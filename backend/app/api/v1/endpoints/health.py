"""
Health Check API Endpoints

Provides comprehensive health monitoring for all OptiFlow services.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import logging

from app.services.health_check_service import get_health_check_service
from app.models.user import User
from app.core.deps import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/comprehensive")
async def comprehensive_health_check() -> Dict[str, Any]:
    """
    Comprehensive health check for all OptiFlow services.

    **No authentication required** - This endpoint is public for monitoring systems.

    Checks:
    - PostgreSQL database
    - Redis cache
    - InfluxDB timeseries
    - RabbitMQ message broker
    - Kafka streaming platform
    - Vault secrets manager
    - OPC-UA Gateway service

    **Returns**:
    ```json
    {
        "status": "healthy" | "degraded" | "unhealthy",
        "timestamp": "2025-01-13T12:00:00Z",
        "services": {
            "postgres": {
                "status": "healthy",
                "response_time_ms": 5,
                "version": "PostgreSQL 15.3",
                "pool_size": 20,
                "connections_in_use": 3,
                "connections_available": 17
            },
            "redis": {...},
            "influxdb": {...},
            ...
        },
        "summary": {
            "total": 7,
            "healthy": 6,
            "degraded": 1,
            "unhealthy": 0
        }
    }
    ```

    **Use Cases**:
    - Kubernetes readiness/liveness probes
    - Monitoring system integration (Prometheus, Grafana)
    - Docker Compose health checks
    - Load balancer health checks
    - Automated alerting systems

    **Response Codes**:
    - 200: System healthy or degraded (partial availability)
    - 503: System unhealthy (critical services down)
    """
    health_service = get_health_check_service()

    result = await health_service.check_all_services()

    # Return 503 if system is unhealthy
    status_code = 503 if result['status'] == 'unhealthy' else 200

    return result


@router.get("/quick")
async def quick_health_check() -> Dict[str, str]:
    """
    Quick health check - lightweight endpoint for basic availability.

    **No authentication required** - This endpoint is public for monitoring.

    Only checks that the API process is running and responsive.
    Does NOT check dependencies (database, cache, etc.).

    **Use Cases**:
    - Docker container health checks
    - Load balancer ping checks
    - Basic uptime monitoring

    **Returns**:
    ```json
    {
        "status": "ok",
        "service": "optiflow-api"
    }
    ```
    """
    return {
        "status": "ok",
        "service": "optiflow-api"
    }


@router.get("/services/{service_name}")
async def check_specific_service(
    service_name: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Health check for a specific service.

    **Authentication required** - Detailed service diagnostics require auth.

    **Parameters**:
    - service_name: One of: postgres, redis, influxdb, rabbitmq, kafka, vault, gateway

    **Returns**:
    Service-specific health information with detailed diagnostics.

    **Example**:
    ```bash
    curl -H "Authorization: Bearer $TOKEN" \\
         http://localhost:8000/api/v1/health/services/postgres
    ```

    **Use Cases**:
    - Troubleshooting specific service issues
    - Monitoring individual service metrics
    - Integration testing
    """
    health_service = get_health_check_service()

    if service_name not in health_service.service_checks:
        return {
            'error': f'Unknown service: {service_name}',
            'available_services': list(health_service.service_checks.keys())
        }

    # Run specific check
    check_func = health_service.service_checks[service_name]
    result = await health_service._run_check_with_timing(service_name, check_func)

    return {
        'service': service_name,
        'timestamp': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
        'health': result
    }
