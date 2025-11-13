"""
ML Training Tasks - Celery tasks for automatic model retraining

Provides scheduled and on-demand retraining of ML models
"""

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="ml.retrain_models")
def retrain_models_task(self, organization_id: str = None, models_to_train: str = "all"):
    """
    Task Celery para retreinar modelos ML periodicamente

    Args:
        organization_id: ID da organização (opcional)
        models_to_train: Quais modelos treinar ('all', 'isolation_forest', 'lstm', etc.)

    Returns:
        dict: Status do treino
    """
    logger.info(f"🔄 Iniciando retreino automático de modelos ML")
    logger.info(f"   Organization: {organization_id or 'all'}")
    logger.info(f"   Models: {models_to_train}")

    try:
        from app.services.ml_model_storage import ml_model_storage
        from app.services.ml_insights_service import ml_insights_service

        # 1. Verificar performance atual dos modelos
        current_models = ml_model_storage.list_available_models()
        logger.info(f"   Modelos atuais: {current_models['total']}")

        # 2. Verificar se precisa retreinar (degradação de performance)
        needs_retraining = []

        for model_name in current_models['sklearn']:
            info = ml_model_storage.get_model_info(model_name)
            if info and info.get('metadata'):
                trained_at = datetime.fromisoformat(info['metadata'].get('trained_at', ''))
                days_since_training = (datetime.now() - trained_at).days

                # Retreinar se:
                # - Mais de 7 dias desde último treino
                # - R² score < 0.7 (se disponível)
                # - Anomaly rate fora do esperado (se Isolation Forest)

                if days_since_training > 7:
                    needs_retraining.append(model_name)
                    logger.info(f"   ⚠️  {model_name}: {days_since_training} dias desde treino")

                if 'r2_score' in info['metadata']:
                    r2 = info['metadata']['r2_score']
                    if r2 is not None and r2 < 0.7:
                        if model_name not in needs_retraining:
                            needs_retraining.append(model_name)
                        logger.info(f"   ⚠️  {model_name}: R² baixo ({r2:.4f})")

        # TensorFlow models
        for model_name in current_models['tensorflow']:
            info = ml_model_storage.get_model_info(model_name)
            if info and info.get('metadata'):
                trained_at = datetime.fromisoformat(info['metadata'].get('trained_at', ''))
                days_since_training = (datetime.now() - trained_at).days

                if days_since_training > 7:
                    needs_retraining.append(model_name)
                    logger.info(f"   ⚠️  {model_name}: {days_since_training} dias desde treino")

        if not needs_retraining:
            logger.info("   ✅ Todos os modelos estão atualizados")
            return {
                'status': 'success',
                'message': 'No retraining needed',
                'models_checked': current_models['total']
            }

        logger.info(f"   🔄 Retreinando {len(needs_retraining)} modelos...")

        # 3. Executar retreino (sícrono nesta task)
        # Nota: Para treino assíncrono real, usar asyncio.run() com db async

        import sys
        sys.path.insert(0, '/home/thiestacio/OptiFlow-AI-/backend')

        # Import training scripts
        from pathlib import Path
        import subprocess

        training_script = Path("/tmp/train_ml_models_direct.py")
        if training_script.exists():
            logger.info("   Executando script de treino...")
            result = subprocess.run(
                ["/home/thiestacio/anaconda3/envs/optiflow/bin/python", str(training_script)],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutos max
            )

            if result.returncode == 0:
                logger.info("   ✅ Treino concluído com sucesso")
                return {
                    'status': 'success',
                    'models_retrained': needs_retraining,
                    'total': len(needs_retraining)
                }
            else:
                logger.error(f"   ❌ Erro no treino: {result.stderr}")
                return {
                    'status': 'error',
                    'error': result.stderr,
                    'models_attempted': needs_retraining
                }
        else:
            logger.warning("   ⚠️  Script de treino não encontrado")
            return {
                'status': 'warning',
                'message': 'Training script not found',
                'models_to_retrain': needs_retraining
            }

    except Exception as e:
        logger.error(f"   ❌ Erro no retreino: {e}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task(bind=True, name="ml.validate_models")
def validate_models_task(self):
    """
    Task para validar todos os modelos ML

    Verifica se modelos podem ser carregados e fazem predições válidas
    """
    logger.info("🔍 Validando modelos ML...")

    try:
        from app.services.ml_model_storage import ml_model_storage

        models = ml_model_storage.list_available_models()
        validation_results = {
            'sklearn': {},
            'tensorflow': {}
        }

        # Validar sklearn models
        for model_name in models['sklearn']:
            is_valid = ml_model_storage.validate_model(model_name, 'sklearn')
            validation_results['sklearn'][model_name] = is_valid

            if is_valid:
                logger.info(f"   ✅ {model_name}: válido")
            else:
                logger.error(f"   ❌ {model_name}: inválido")

        # Validar tensorflow models
        for model_name in models['tensorflow']:
            is_valid = ml_model_storage.validate_model(model_name, 'tensorflow')
            validation_results['tensorflow'][model_name] = is_valid

            if is_valid:
                logger.info(f"   ✅ {model_name}: válido")
            else:
                logger.error(f"   ❌ {model_name}: inválido")

        total_valid = sum(1 for v in validation_results['sklearn'].values() if v) + \
                     sum(1 for v in validation_results['tensorflow'].values() if v)
        total_models = models['total']

        logger.info(f"✅ Validação completa: {total_valid}/{total_models} modelos válidos")

        return {
            'status': 'success',
            'valid_models': total_valid,
            'total_models': total_models,
            'details': validation_results
        }

    except Exception as e:
        logger.error(f"❌ Erro na validação: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task(bind=True, name="ml.cleanup_old_models")
def cleanup_old_models_task(self, days_to_keep: int = 30):
    """
    Task para limpar modelos antigos (mais de X dias)

    Args:
        days_to_keep: Número de dias para manter modelos
    """
    logger.info(f"🧹 Limpando modelos com mais de {days_to_keep} dias...")

    try:
        from app.services.ml_model_storage import ml_model_storage
        from pathlib import Path

        models = ml_model_storage.list_available_models()
        deleted_models = []

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        # Check sklearn models
        for model_name in models['sklearn']:
            info = ml_model_storage.get_model_info(model_name)
            if info and info.get('metadata'):
                trained_at = datetime.fromisoformat(info['metadata'].get('trained_at', ''))

                if trained_at < cutoff_date:
                    logger.info(f"   🗑️  Deletando {model_name} (treinado em {trained_at.date()})")
                    success = ml_model_storage.delete_model(model_name, 'sklearn')
                    if success:
                        deleted_models.append(model_name)

        # Check tensorflow models
        for model_name in models['tensorflow']:
            info = ml_model_storage.get_model_info(model_name)
            if info and info.get('metadata'):
                trained_at = datetime.fromisoformat(info['metadata'].get('trained_at', ''))

                if trained_at < cutoff_date:
                    logger.info(f"   🗑️  Deletando {model_name} (treinado em {trained_at.date()})")
                    success = ml_model_storage.delete_model(model_name, 'tensorflow')
                    if success:
                        deleted_models.append(model_name)

        logger.info(f"✅ Limpeza completa: {len(deleted_models)} modelos deletados")

        return {
            'status': 'success',
            'deleted_models': deleted_models,
            'total_deleted': len(deleted_models)
        }

    except Exception as e:
        logger.error(f"❌ Erro na limpeza: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
