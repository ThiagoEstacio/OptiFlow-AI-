"""
Endpoints REST para ML Insights

Permite ao Autonomous Agent e ao frontend consumir insights ML/DS
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import logging

from app.db.session import get_db
from app.services.ml_insights_service import ml_insights_service
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/insights/all")
async def get_all_insights(
    time_range: str = Query(
        default='last_7_days',
        description="Período de análise: last_24h, last_7_days, last_30_days"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Gera todos os insights ML para a organização do usuário

    Retorna:
    - Insights de confiabilidade (MTBF/MTTR)
    - Previsão de energia (LSTM)
    - Análise de eficiência (Gradient Boosting)
    - Detecção de anomalias (Isolation Forest)
    - Análise de correlações
    - Otimização de custos
    """
    try:
        insights = await ml_insights_service.generate_all_insights(
            db=db,
            organization_id=str(current_user.organization_id),
            time_range=time_range
        )
        return insights
    except Exception as e:
        logger.error(f"Error generating ML insights: {e}", exc_info=True)
        # Return empty structure instead of failing
        return {
            "status": "error",
            "error": "internal_error",
            "detail": "ML insights service unavailable. Try again later.",
            "insights": {
                "reliability": [],
                "energy_prediction": [],
                "efficiency": [],
                "anomalies": [],
                "correlations": [],
                "cost_optimization": []
            }
        }


@router.get("/insights/reliability")
async def get_reliability_insights(
    time_range: str = Query(default='last_7_days'),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Análise de Confiabilidade (MTBF/MTTR)

    Retorna:
    - Estatísticas de MTBF/MTTR por equipamento
    - Equipamentos críticos
    - Previsão de próximas manutenções
    - Alertas e recomendações
    """
    try:
        insights = await ml_insights_service.generate_all_insights(
            db=db,
            organization_id=str(current_user.organization_id),
            time_range=time_range
        )
        return insights['insights']['reliability']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar insights de confiabilidade: {str(e)}")


@router.get("/insights/energy-prediction")
async def get_energy_prediction_insights(
    time_range: str = Query(default='last_7_days'),
    hours_ahead: int = Query(default=24, ge=1, le=168, description="Horas para prever (1-168)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Previsão de Consumo Energético (LSTM)

    Retorna:
    - Consumo atual
    - Previsão para próximas N horas
    - Tendências
    - Alertas de consumo anormal
    - Recomendações
    """
    try:
        insights = await ml_insights_service.generate_all_insights(
            db=db,
            organization_id=str(current_user.organization_id),
            time_range=time_range
        )
        return insights['insights']['energy_prediction']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar previsão de energia: {str(e)}")


@router.get("/insights/efficiency")
async def get_efficiency_insights(
    time_range: str = Query(default='last_7_days'),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Análise de Eficiência Energética (Gradient Boosting)

    Retorna:
    - Eficiência atual vs esperada
    - Fatores que impactam eficiência
    - Horários de melhor/pior eficiência
    - Recomendações de melhoria
    """
    try:
        insights = await ml_insights_service.generate_all_insights(
            db=db,
            organization_id=str(current_user.organization_id),
            time_range=time_range
        )
        return insights['insights']['efficiency']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar insights de eficiência: {str(e)}")


@router.get("/insights/anomalies")
async def get_anomaly_insights(
    time_range: str = Query(default='last_7_days'),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Detecção de Anomalias (Isolation Forest)

    Retorna:
    - Anomalias detectadas recentemente
    - Padrões de anomalias
    - Equipamentos com mais anomalias
    - Alertas e recomendações
    """
    try:
        insights = await ml_insights_service.generate_all_insights(
            db=db,
            organization_id=str(current_user.organization_id),
            time_range=time_range
        )
        return insights['insights']['anomalies']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar insights de anomalias: {str(e)}")


@router.get("/insights/correlations")
async def get_correlation_insights(
    time_range: str = Query(default='last_7_days'),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Análise de Correlações

    Retorna:
    - Correlações fortes identificadas
    - Variáveis que impactam o sistema
    - Insights de causa-efeito
    - Recomendações
    """
    try:
        insights = await ml_insights_service.generate_all_insights(
            db=db,
            organization_id=str(current_user.organization_id),
            time_range=time_range
        )
        return insights['insights']['correlations']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar insights de correlação: {str(e)}")


@router.get("/insights/cost-optimization")
async def get_cost_optimization_insights(
    time_range: str = Query(default='last_7_days'),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Otimização de Custos de Energia

    Retorna:
    - Custo atual
    - Potencial de economia
    - Estratégias de otimização
    - ROI estimado
    - Recomendações
    """
    try:
        insights = await ml_insights_service.generate_all_insights(
            db=db,
            organization_id=str(current_user.organization_id),
            time_range=time_range
        )
        return insights['insights']['cost_optimization']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar insights de custos: {str(e)}")


@router.get("/insights/summary")
async def get_insights_summary(
    time_range: str = Query(default='last_7_days'),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sumário Executivo de Todos os Insights

    Retorna:
    - Total de insights gerados
    - Total de alertas
    - Severidade geral
    - Top recomendações
    - Status geral
    """
    try:
        insights = await ml_insights_service.generate_all_insights(
            db=db,
            organization_id=str(current_user.organization_id),
            time_range=time_range
        )
        return {
            'generated_at': insights['generated_at'],
            'time_range': insights['time_range'],
            'summary': insights['summary']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar sumário de insights: {str(e)}")


@router.post("/insights/refresh")
async def refresh_insights(
    time_range: str = Query(default='last_7_days'),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Força atualização dos insights (bypass cache)

    Útil quando novos dados foram inseridos e insights precisam ser atualizados imediatamente
    """
    try:
        # Invalidar cache primeiro
        from app.services.redis_cache import redis_cache_service

        invalidated = redis_cache_service.invalidate_insights(
            organization_id=str(current_user.organization_id),
            time_range=time_range
        )

        # Gerar novos insights
        insights = await ml_insights_service.generate_all_insights(
            db=db,
            organization_id=str(current_user.organization_id),
            time_range=time_range
        )

        return {
            'status': 'success',
            'message': 'Insights atualizados com sucesso',
            'cache_invalidated': invalidated > 0,
            'generated_at': insights['generated_at'],
            'summary': insights['summary']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar insights: {str(e)}")


@router.get("/insights/health")
async def check_ml_insights_health():
    """
    Health check do serviço de ML Insights

    Retorna status dos modelos e serviços ML
    """
    try:
        # Verificar se TensorFlow está disponível
        from app.services.ml_insights_service import TENSORFLOW_AVAILABLE

        return {
            'status': 'healthy',
            'tensorflow_available': TENSORFLOW_AVAILABLE,
            'models_loaded': len(ml_insights_service.models),
            'service': 'ml_insights',
            'version': '1.0.0'
        }
    except Exception as e:
        return {
            'status': 'degraded',
            'error': str(e)
        }
