"""
Database Monitoring API Endpoints

Provides endpoints for:
- Circuit breaker status and control
- Connection pool monitoring
- Database health metrics
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
import logging

from app.core.circuit_breaker import get_all_circuit_breakers, get_circuit_breaker
from app.services.db_pool_monitor import get_pool_monitor
from app.models.user import User
from app.core.deps import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/circuit-breakers")
async def list_circuit_breakers(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List all circuit breakers and their states.

    **Returns**:
    ```json
    {
        "circuit_breakers": [
            {
                "name": "executive_dashboard",
                "state": "closed",
                "failure_count": 0,
                "metrics": {
                    "total_calls": 1523,
                    "success_rate": 99.8,
                    "failure_rate": 0.2
                }
            }
        ],
        "summary": {
            "total": 5,
            "open": 0,
            "half_open": 0,
            "closed": 5
        }
    }
    ```

    **Use Cases**:
    - Monitor circuit breaker health
    - Identify problematic database operations
    - Track failure patterns
    """
    breakers = get_all_circuit_breakers()

    breaker_states = [breaker.get_state() for breaker in breakers.values()]

    # Calculate summary
    summary = {
        "total": len(breaker_states),
        "open": sum(1 for b in breaker_states if b["state"] == "open"),
        "half_open": sum(1 for b in breaker_states if b["state"] == "half_open"),
        "closed": sum(1 for b in breaker_states if b["state"] == "closed")
    }

    return {
        "circuit_breakers": breaker_states,
        "summary": summary,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }


@router.get("/circuit-breakers/{name}")
async def get_circuit_breaker_status(
    name: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get status of specific circuit breaker.

    **Parameters**:
    - name: Circuit breaker name (e.g., "executive_dashboard", "user_query")

    **Returns**:
    Detailed state and metrics for the circuit breaker.

    **Example**:
    ```bash
    curl -H "Authorization: Bearer $TOKEN" \\
         http://localhost:8000/api/v1/database/circuit-breakers/executive_dashboard
    ```
    """
    breakers = get_all_circuit_breakers()

    if name not in breakers:
        raise HTTPException(
            status_code=404,
            detail=f"Circuit breaker '{name}' not found. Available: {list(breakers.keys())}"
        )

    breaker = breakers[name]
    return breaker.get_state()


@router.post("/circuit-breakers/{name}/reset")
async def reset_circuit_breaker(
    name: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Manually reset a circuit breaker to CLOSED state.

    **Use Cases**:
    - Recover from temporary database issues after fixing root cause
    - Force retry after manual intervention
    - Testing circuit breaker behavior

    **Warning**: Only reset after confirming the underlying issue is resolved.

    **Returns**:
    ```json
    {
        "status": "reset",
        "circuit_breaker": "executive_dashboard",
        "new_state": "closed",
        "message": "Circuit breaker reset successfully"
    }
    ```
    """
    breakers = get_all_circuit_breakers()

    if name not in breakers:
        raise HTTPException(
            status_code=404,
            detail=f"Circuit breaker '{name}' not found"
        )

    breaker = breakers[name]
    old_state = breaker.state

    breaker.reset()

    logger.info(
        f"Circuit breaker '{name}' manually reset by user {current_user.email} "
        f"(old state: {old_state})"
    )

    return {
        "status": "reset",
        "circuit_breaker": name,
        "old_state": old_state,
        "new_state": breaker.state,
        "message": "Circuit breaker reset successfully",
        "reset_by": current_user.email
    }


@router.get("/connection-pool")
async def get_connection_pool_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get PostgreSQL connection pool status.

    **Returns**:
    ```json
    {
        "pool_size": 20,
        "connections_in_use": 3,
        "connections_available": 17,
        "usage_percent": 15.0,
        "status": "healthy",
        "potential_leaks": 0,
        "peak_usage": {
            "connections": 12,
            "timestamp": "2025-01-13T10:30:00Z"
        },
        "metrics": {
            "total_checkouts": 5421,
            "total_checkins": 5418,
            "warning_count": 2,
            "critical_count": 0
        }
    }
    ```

    **Status Values**:
    - `healthy`: Usage < 80%
    - `warning`: Usage 80-95%
    - `critical`: Usage > 95%

    **Use Cases**:
    - Monitor connection pool health
    - Detect connection leaks
    - Plan pool size adjustments
    - Alert on high usage
    """
    monitor = get_pool_monitor()
    return monitor.get_pool_status()


@router.get("/connection-pool/health")
async def get_connection_pool_health() -> Dict[str, Any]:
    """
    Simple health check for connection pool.

    **No authentication required** - For monitoring systems.

    **Returns**:
    ```json
    {
        "healthy": true,
        "status": "healthy",
        "usage_percent": 15.0,
        "message": "Healthy: Connection pool normal (3/20 used, 15.0%)"
    }
    ```

    **Use Cases**:
    - Kubernetes health checks
    - Prometheus monitoring
    - Alerting systems
    """
    monitor = get_pool_monitor()
    return monitor.get_health_check()


@router.get("/metrics")
async def get_database_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive database metrics.

    Combines:
    - Circuit breaker statistics
    - Connection pool metrics
    - Overall database health

    **Returns**:
    ```json
    {
        "circuit_breakers": {
            "total": 5,
            "open": 0,
            "total_calls": 10532,
            "total_failures": 23,
            "overall_success_rate": 99.78
        },
        "connection_pool": {
            "status": "healthy",
            "usage_percent": 15.0,
            "potential_leaks": 0
        },
        "overall_health": "healthy",
        "timestamp": "2025-01-13T12:00:00Z"
    }
    ```

    **Use Cases**:
    - Dashboard widgets
    - Executive reporting
    - Capacity planning
    - SLA monitoring
    """
    # Circuit breaker metrics
    breakers = get_all_circuit_breakers()
    breaker_states = [b.get_state() for b in breakers.values()]

    total_calls = sum(b["metrics"]["total_calls"] for b in breaker_states)
    total_failures = sum(b["metrics"]["total_failures"] for b in breaker_states)
    overall_success_rate = (
        ((total_calls - total_failures) / total_calls * 100)
        if total_calls > 0 else 100.0
    )

    circuit_breaker_metrics = {
        "total": len(breaker_states),
        "open": sum(1 for b in breaker_states if b["state"] == "open"),
        "half_open": sum(1 for b in breaker_states if b["state"] == "half_open"),
        "closed": sum(1 for b in breaker_states if b["state"] == "closed"),
        "total_calls": total_calls,
        "total_failures": total_failures,
        "overall_success_rate": round(overall_success_rate, 2)
    }

    # Connection pool metrics
    monitor = get_pool_monitor()
    pool_status = monitor.get_pool_status()

    pool_metrics = {
        "status": pool_status["status"],
        "usage_percent": pool_status["usage_percent"],
        "connections_in_use": pool_status["connections_in_use"],
        "connections_available": pool_status["connections_available"],
        "potential_leaks": pool_status["potential_leaks"]
    }

    # Overall health
    if pool_status["status"] == "critical" or circuit_breaker_metrics["open"] > 0:
        overall_health = "unhealthy"
    elif pool_status["status"] == "warning" or circuit_breaker_metrics["half_open"] > 0:
        overall_health = "degraded"
    else:
        overall_health = "healthy"

    return {
        "circuit_breakers": circuit_breaker_metrics,
        "connection_pool": pool_metrics,
        "overall_health": overall_health,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }
