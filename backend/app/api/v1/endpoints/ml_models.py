"""
Endpoints para gerenciamento de modelos ML

Permite treinar, salvar, carregar e gerenciar modelos ML
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.services.ml_insights_service import ml_insights_service
from app.services.ml_model_storage import ml_model_storage, get_model_description
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/models/list")
async def list_models(
    current_user: User = Depends(get_current_user)
):
    """
    Lista todos os modelos ML disponíveis
    """
    try:
        models = ml_model_storage.list_available_models()

        # Adicionar informações detalhadas
        detailed_models = {
            'sklearn': [],
            'tensorflow': [],
            'total': models['total']
        }

        for model_name in models['sklearn']:
            info = ml_model_storage.get_model_info(model_name)
            if info:
                info['description'] = get_model_description(model_name)
                detailed_models['sklearn'].append(info)

        for model_name in models['tensorflow']:
            info = ml_model_storage.get_model_info(model_name)
            if info:
                info['description'] = get_model_description(model_name)
                detailed_models['tensorflow'].append(info)

        return detailed_models

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar modelos: {str(e)}")


@router.get("/models/{model_name}")
async def get_model_info(
    model_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Obtém informações detalhadas sobre um modelo específico
    """
    try:
        info = ml_model_storage.get_model_info(model_name)

        if not info:
            raise HTTPException(status_code=404, detail=f"Modelo '{model_name}' não encontrado")

        # Adicionar descrição
        info['description'] = get_model_description(model_name)

        return info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter info do modelo: {str(e)}")


@router.post("/models/train")
async def train_models(
    background_tasks: BackgroundTasks,
    time_range: str = 'last_30_days',
    models_to_train: Optional[str] = None,  # 'all', 'lstm', 'gradient_boosting', etc.
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Treina modelos ML com dados históricos e salva em disco

    Args:
        time_range: Período de dados para treino (last_30_days recomendado)
        models_to_train: Quais modelos treinar ('all', 'lstm', 'gradient_boosting', etc.)

    Returns:
        Status do treino e informações dos modelos
    """
    try:
        models_list = models_to_train.split(',') if models_to_train and models_to_train != 'all' else ['all']

        # Adicionar task em background (treino pode demorar)
        background_tasks.add_task(
            _train_and_save_models,
            db=db,
            organization_id=str(current_user.organization_id),
            time_range=time_range,
            models_list=models_list
        )

        return {
            'status': 'training_started',
            'message': 'Treino de modelos iniciado em background',
            'models': models_list,
            'time_range': time_range,
            'estimated_time': '5-10 minutes'
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar treino: {str(e)}")


async def _train_and_save_models(
    db: AsyncSession,
    organization_id: str,
    time_range: str,
    models_list: list
):
    """
    Task background para treinar e salvar modelos

    Args:
        db: Database session
        organization_id: ID da organização
        time_range: Período de dados
        models_list: Lista de modelos para treinar
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Iniciando treino de modelos: {models_list}")

        # Gerar insights (treina os modelos)
        insights = await ml_insights_service.generate_all_insights(
            db=db,
            organization_id=organization_id,
            time_range=time_range
        )

        # Salvar modelos treinados
        saved_models = []

        # Verificar quais modelos foram treinados e salvá-los
        if 'all' in models_list or 'gradient_boosting' in models_list:
            if 'gradient_boosting' in ml_insights_service.models:
                success = ml_model_storage.save_sklearn_model(
                    model_name='gradient_boosting_efficiency',
                    model=ml_insights_service.models['gradient_boosting'],
                    metadata={
                        'r2_score': insights['insights']['efficiency'].get('r2_score'),
                        'mape': insights['insights']['efficiency'].get('mape'),
                        'trained_at': datetime.now().isoformat(),
                        'training_data_period': time_range
                    }
                )
                if success:
                    saved_models.append('gradient_boosting_efficiency')

        if 'all' in models_list or 'isolation_forest' in models_list:
            if 'isolation_forest' in ml_insights_service.models:
                success = ml_model_storage.save_sklearn_model(
                    model_name='isolation_forest_anomalies',
                    model=ml_insights_service.models['isolation_forest'],
                    metadata={
                        'anomaly_rate': insights['insights']['anomalies'].get('anomaly_rate'),
                        'trained_at': datetime.now().isoformat(),
                        'training_data_period': time_range
                    }
                )
                if success:
                    saved_models.append('isolation_forest_anomalies')

        if 'all' in models_list or 'lstm' in models_list:
            if 'lstm' in ml_insights_service.models:
                success = ml_model_storage.save_tensorflow_model(
                    model_name='lstm_energy',
                    model=ml_insights_service.models['lstm'],
                    metadata={
                        'r2_score': insights['insights']['energy_prediction'].get('r2_score'),
                        'mape': insights['insights']['energy_prediction'].get('mape'),
                        'trained_at': datetime.now().isoformat(),
                        'training_data_period': time_range
                    }
                )
                if success:
                    saved_models.append('lstm_energy')

        logger.info(f"✅ Modelos treinados e salvos com sucesso: {saved_models}")

        return {
            'status': 'success',
            'saved_models': saved_models,
            'total': len(saved_models)
        }

    except Exception as e:
        logger.error(f"Erro no treino de modelos: {e}")
        return {'status': 'error', 'error': str(e)}


@router.delete("/models/{model_name}")
async def delete_model(
    model_name: str,
    model_type: str = 'sklearn',  # 'sklearn' ou 'tensorflow'
    current_user: User = Depends(get_current_user)
):
    """
    Deleta um modelo salvo

    Args:
        model_name: Nome do modelo
        model_type: Tipo do modelo ('sklearn' ou 'tensorflow')
    """
    try:
        success = ml_model_storage.delete_model(model_name, model_type)

        if not success:
            raise HTTPException(status_code=404, detail=f"Modelo '{model_name}' não encontrado")

        return {
            'status': 'success',
            'message': f"Modelo '{model_name}' deletado com sucesso"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar modelo: {str(e)}")


@router.post("/models/{model_name}/validate")
async def validate_model(
    model_name: str,
    model_type: str = 'sklearn',
    current_user: User = Depends(get_current_user)
):
    """
    Valida se um modelo pode ser carregado corretamente

    Args:
        model_name: Nome do modelo
        model_type: Tipo do modelo
    """
    try:
        is_valid = ml_model_storage.validate_model(model_name, model_type)

        return {
            'model_name': model_name,
            'model_type': model_type,
            'is_valid': is_valid,
            'message': 'Modelo válido' if is_valid else 'Modelo inválido ou corrompido'
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao validar modelo: {str(e)}")


@router.get("/models/storage/stats")
async def get_storage_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Obtém estatísticas do armazenamento de modelos
    """
    try:
        models = ml_model_storage.list_available_models()

        # Calcular tamanho total
        total_size_bytes = 0
        for model_name in models['sklearn']:
            info = ml_model_storage.get_model_info(model_name)
            if info:
                total_size_bytes += info['size_bytes']

        for model_name in models['tensorflow']:
            info = ml_model_storage.get_model_info(model_name)
            if info:
                total_size_bytes += info['size_bytes']

        return {
            'total_models': models['total'],
            'sklearn_models': len(models['sklearn']),
            'tensorflow_models': len(models['tensorflow']),
            'total_size_bytes': total_size_bytes,
            'total_size_mb': round(total_size_bytes / (1024 * 1024), 2),
            'storage_path': str(ml_model_storage.models_dir)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter stats: {str(e)}")
