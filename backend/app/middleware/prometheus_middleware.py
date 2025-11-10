"""
Prometheus Middleware for FastAPI
==================================

Middleware para instrumentação automática de requests HTTP
Registra métricas de latência, throughput e erros

Autor: OptiFlow AI Team
Data: 2025-11-10
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
from typing import Callable

from app.services.prometheus_metrics import get_metrics

logger = logging.getLogger(__name__)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware para coleta automática de métricas HTTP
    
    Registra para cada request:
    - Total de requests (contador)
    - Duração do request (histograma)
    - Requests em progresso (gauge)
    - Status code da response
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.metrics = get_metrics()
        if self.metrics is None:
            logger.error("Failed to get metrics instance - metrics will not be collected!")
        else:
            logger.info(f"Prometheus middleware initialized with metrics: {type(self.metrics)}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Intercepta request e registra métricas
        
        Args:
            request: Request HTTP recebido
            call_next: Próximo handler na cadeia
        
        Returns:
            Response do handler
        """
        # Extrair informações do request
        method = request.method
        endpoint = self._get_endpoint_path(request)
        
        # Marcar início
        start_time = time.time()
        
        # Incrementar gauge de requests em progresso
        with self.metrics.request_in_progress(method, endpoint):
            try:
                # Processar request
                response = await call_next(request)
                
                # Calcular duração
                duration = time.time() - start_time
                
                # Registrar métricas
                self.metrics.track_request(method, endpoint, response.status_code)
                self.metrics.track_request_duration(method, endpoint, duration)
                
                logger.info(
                    f"✓ Metrics tracked: {method} {endpoint} - {response.status_code} "
                    f"({duration:.3f}s)"
                )
                
                return response
            
            except Exception as e:
                # Em caso de erro, registrar como 500
                duration = time.time() - start_time
                self.metrics.track_request(method, endpoint, 500)
                self.metrics.track_request_duration(method, endpoint, duration)
                
                logger.error(
                    f"{method} {endpoint} - ERROR ({duration:.3f}s): {e}"
                )
                raise
    
    def _get_endpoint_path(self, request: Request) -> str:
        """
        Extrai path do endpoint (sem query params)
        
        Args:
            request: Request HTTP
        
        Returns:
            Path do endpoint (ex: /api/v1/devices)
        """
        # Tentar pegar rota matched do FastAPI
        if hasattr(request, "url"):
            path = request.url.path
            
            # Normalizar path para evitar cardinalidade alta
            # Ex: /api/v1/devices/123 -> /api/v1/devices/{id}
            if request.path_params:
                for param_name, param_value in request.path_params.items():
                    path = path.replace(str(param_value), f"{{{param_name}}}")
            
            return path
        
        return "unknown"


def setup_prometheus_middleware(app):
    """
    Adiciona Prometheus middleware à aplicação FastAPI
    
    Args:
        app: Instância do FastAPI
    """
    app.add_middleware(PrometheusMiddleware)
    logger.info("Prometheus middleware added to FastAPI")
