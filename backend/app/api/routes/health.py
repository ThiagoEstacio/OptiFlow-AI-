"""
Health Check Endpoints
======================

Provides /health and /readiness endpoints for Kubernetes/Docker health checks.
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", summary="Basic health check")
async def health_check() -> JSONResponse:
    """
    Basic health check endpoint
    
    Returns HTTP 200 if the service is alive.
    This is used for liveness probes in Kubernetes.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "timestamp": time.time()
        }
    )


@router.get("/readiness", summary="Readiness check with dependencies")
async def readiness_check() -> JSONResponse:
    """
    Readiness check endpoint
    
    Checks if the service is ready to handle requests by verifying:
    - Database connection
    - Kafka connection
    - InfluxDB connection
    - Gateway service status
    - Consumer service status
    
    Returns HTTP 200 if all dependencies are healthy, HTTP 503 otherwise.
    This is used for readiness probes in Kubernetes.
    """
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }
    
    all_healthy = True
    
    # Check Database (PostgreSQL)
    try:
        from app.db.session import check_db_health
        db_healthy = await check_db_health()
        health_status["checks"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "type": "postgresql"
        }
        if not db_healthy:
            all_healthy = False
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "type": "postgresql"
        }
        all_healthy = False
    
    # Check InfluxDB
    try:
        from app.services.influxdb import influxdb_service
        influx_healthy = influxdb_service.health_check()
        health_status["checks"]["influxdb"] = {
            "status": "healthy" if influx_healthy else "unhealthy"
        }
        if not influx_healthy:
            all_healthy = False
    except Exception as e:
        logger.error(f"InfluxDB health check failed: {e}")
        health_status["checks"]["influxdb"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        all_healthy = False
    
    # Check Kafka Producer
    try:
        from app.services.kafka_producer import get_kafka_producer
        kafka_producer = get_kafka_producer()
        kafka_healthy = kafka_producer and kafka_producer.enabled
        health_status["checks"]["kafka"] = {
            "status": "healthy" if kafka_healthy else "unhealthy",
            "enabled": kafka_healthy
        }
        if not kafka_healthy:
            all_healthy = False
    except Exception as e:
        logger.error(f"Kafka health check failed: {e}")
        health_status["checks"]["kafka"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        all_healthy = False
    
    # Check Gateway Service
    try:
        from app.services.gateway_service import gateway_service
        gateway_status = gateway_service.get_status()
        gateway_healthy = gateway_status.get("running", False)
        
        health_status["checks"]["gateway"] = {
            "status": "healthy" if gateway_healthy else "unhealthy",
            "running": gateway_healthy,
            "messages_published": gateway_status.get("statistics", {}).get("messages_published", 0),
            "errors": gateway_status.get("statistics", {}).get("errors_count", 0),
            "circuit_breaker": gateway_status.get("circuit_breaker", {}).get("state", "unknown")
        }
        
        # Gateway is not critical for readiness (can start even if gateway has issues)
        # So we don't set all_healthy = False here
        
    except Exception as e:
        logger.error(f"Gateway health check failed: {e}")
        health_status["checks"]["gateway"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Consumer Service
    try:
        from app.services.timeseries_consumer import get_consumer_status
        consumer_status = get_consumer_status()
        consumer_healthy = consumer_status.get("running", False)
        
        health_status["checks"]["consumer"] = {
            "status": "healthy" if consumer_healthy else "unhealthy",
            "running": consumer_healthy,
            "messages_processed": consumer_status.get("messages_processed", 0),
            "errors": consumer_status.get("errors", 0),
            "batch_size": consumer_status.get("current_batch_size", 0)
        }
        
        # Consumer is not critical for readiness (can start even if consumer has issues)
        
    except Exception as e:
        logger.error(f"Consumer health check failed: {e}")
        health_status["checks"]["consumer"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Set overall status
    health_status["status"] = "healthy" if all_healthy else "degraded"
    
    # Return appropriate HTTP status code
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content=health_status
    )
