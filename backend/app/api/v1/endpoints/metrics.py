"""
Prometheus Metrics Endpoint
============================

Endpoint para exposição de métricas Prometheus
Formato: texto plano compatível com Prometheus scraping

Autor: OptiFlow AI Team
Data: 2025-11-10
"""

from fastapi import APIRouter, Response
from app.services.prometheus_metrics import get_metrics
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["monitoring"])


@router.get(
    "/metrics",
    summary="Prometheus Metrics",
    description="Expõe métricas da aplicação no formato Prometheus",
    response_class=Response,
    responses={
        200: {
            "description": "Métricas no formato Prometheus",
            "content": {
                "text/plain; version=0.0.4; charset=utf-8": {
                    "example": """
# HELP optiflow_http_requests_total Total HTTP requests
# TYPE optiflow_http_requests_total counter
optiflow_http_requests_total{endpoint="/api/v1/devices",method="GET",status="200"} 150.0

# HELP optiflow_http_request_duration_seconds HTTP request latency
# TYPE optiflow_http_request_duration_seconds histogram
optiflow_http_request_duration_seconds_bucket{endpoint="/api/v1/devices",method="GET",le="0.01"} 50.0
optiflow_http_request_duration_seconds_bucket{endpoint="/api/v1/devices",method="GET",le="0.05"} 120.0
optiflow_http_request_duration_seconds_sum{endpoint="/api/v1/devices",method="GET"} 5.25
optiflow_http_request_duration_seconds_count{endpoint="/api/v1/devices",method="GET"} 150.0

# HELP optiflow_system_cpu_usage_percent System CPU usage percentage
# TYPE optiflow_system_cpu_usage_percent gauge
optiflow_system_cpu_usage_percent 25.3
                    """
                }
            }
        }
    }
)
async def metrics_endpoint():
    """
    Endpoint de métricas Prometheus
    
    Retorna todas as métricas coletadas em formato texto compatível com Prometheus.
    Este endpoint é acessado periodicamente pelo servidor Prometheus (scraping).
    
    **Métricas Disponíveis:**
    
    - **HTTP**: requests totais, latência, requests em progresso
    - **Aplicação**: usuários ativos, conexões WebSocket
    - **Database**: conexões, queries, erros
    - **Kafka**: mensagens enviadas, erros, tamanho da fila
    - **InfluxDB**: pontos escritos, erros, latência
    - **Devices**: devices conectados, tags lidas, erros
    - **Alarmes**: alarmes ativos, alarmes disparados
    - **Sistema**: CPU, memória, disco
    - **Simulador**: status do processo, inventário, fluxo
    - **Negócio**: KPIs de energia (kWh/ton), custo operacional
    
    **Exemplo de Configuração Prometheus:**
    
    ```yaml
    scrape_configs:
      - job_name: 'optiflow-backend'
        scrape_interval: 15s
        static_configs:
          - targets: ['backend:8000']
    ```
    
    Returns:
        Response: Métricas em formato texto Prometheus
    """
    try:
        metrics_service = get_metrics()
        metrics_data = metrics_service.export_metrics()
        content_type = metrics_service.get_content_type()
        
        logger.debug(f"Metrics exported: {len(metrics_data)} bytes")
        
        return Response(
            content=metrics_data,
            media_type=content_type
        )
    
    except Exception as e:
        logger.error(f"Error exporting metrics: {e}", exc_info=True)
        return Response(
            content=f"# Error exporting metrics: {str(e)}\n",
            media_type="text/plain",
            status_code=500
        )


@router.get(
    "/health/metrics",
    summary="Metrics Health Check",
    description="Verifica se o sistema de métricas está funcionando",
    response_model=dict
)
async def metrics_health():
    """
    Health check do sistema de métricas
    
    Verifica se o PrometheusMetrics está inicializado e funcionando.
    
    Returns:
        dict: Status do sistema de métricas
        
    **Exemplo de Response:**
    
    ```json
    {
        "status": "healthy",
        "metrics_service": "running",
        "registry": "initialized",
        "message": "Metrics system operational"
    }
    ```
    """
    try:
        metrics_service = get_metrics()
        
        # Tentar exportar métricas como teste
        metrics_data = metrics_service.export_metrics()
        
        return {
            "status": "healthy",
            "metrics_service": "running",
            "registry": "initialized",
            "metrics_size_bytes": len(metrics_data),
            "message": "Metrics system operational"
        }
    
    except Exception as e:
        logger.error(f"Metrics health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "metrics_service": "error",
            "error": str(e),
            "message": "Metrics system not operational"
        }
