"""
Health Check Endpoints
======================

Provides /health and /readiness endpoints for Kubernetes/Docker health checks.
Enhanced with predictive health monitoring and trend analysis.
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging
import time
import asyncio
import httpx
import psutil

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["health"])

# Health history for trend analysis
_health_history: Dict[str, list] = {
    "memory": [],
    "cpu": [],
    "db_connections": [],
    "latency": []
}
_history_max_size = 60  # Keep 60 measurements (10 minutes at 10s intervals)


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
    
    # Gateway Service now runs as standalone microservice
    # Its health is available at http://gateway:8080/health
    health_status["checks"]["gateway"] = {
        "status": "external",
        "note": "Gateway is now a standalone microservice (port 8080)",
        "health_endpoint": "http://gateway:8080/health"
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


@router.get("/health/detailed", summary="Detailed health check with trends")
async def detailed_health_check() -> JSONResponse:
    """
    Comprehensive health check with:
    - All service statuses
    - Resource usage (memory, CPU, disk)
    - Trend analysis
    - Predictive alerts
    - Recommendations
    """
    health_result = {
        "status": "healthy",
        "timestamp": time.time(),
        "resources": {},
        "services": {},
        "trends": {},
        "alerts": [],
        "recommendations": []
    }

    # Get system resources
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        disk = psutil.disk_usage('/')

        health_result["resources"] = {
            "memory": {
                "used_percent": memory.percent,
                "used_gb": memory.used / (1024**3),
                "available_gb": memory.available / (1024**3),
                "total_gb": memory.total / (1024**3)
            },
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "disk": {
                "used_percent": disk.percent,
                "used_gb": disk.used / (1024**3),
                "free_gb": disk.free / (1024**3),
                "total_gb": disk.total / (1024**3)
            }
        }

        # Store in history for trend analysis
        _update_history("memory", memory.percent)
        _update_history("cpu", cpu_percent)

        # Generate alerts based on thresholds
        if memory.percent > 85:
            health_result["alerts"].append({
                "level": "warning",
                "message": f"Memory usage is high: {memory.percent:.1f}%"
            })
            health_result["recommendations"].append(
                "Consider restarting heavy services or increasing memory"
            )

        if memory.percent > 95:
            health_result["alerts"].append({
                "level": "critical",
                "message": f"Memory usage is critical: {memory.percent:.1f}%"
            })
            health_result["status"] = "critical"

        if disk.percent > 85:
            health_result["alerts"].append({
                "level": "warning",
                "message": f"Disk usage is high: {disk.percent:.1f}%"
            })
            health_result["recommendations"].append(
                "Clean up logs and docker images: docker system prune"
            )

        if disk.percent > 95:
            health_result["alerts"].append({
                "level": "critical",
                "message": f"Disk usage is critical: {disk.percent:.1f}%"
            })
            health_result["status"] = "critical"

    except Exception as e:
        logger.error(f"Resource check failed: {e}")
        health_result["resources"]["error"] = str(e)

    # Check all services
    services_to_check = {
        "gateway": "http://gateway:8080/health",
        "grafana": "http://grafana:3000/api/health",
        "prometheus": "http://prometheus:9090/-/healthy",
        "influxdb": "http://influxdb:8086/health"
    }

    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in services_to_check.items():
            try:
                start = time.time()
                response = await client.get(url)
                latency = (time.time() - start) * 1000

                health_result["services"][name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "latency_ms": latency,
                    "status_code": response.status_code
                }

                if latency > 1000:
                    health_result["alerts"].append({
                        "level": "warning",
                        "message": f"{name} response time is slow: {latency:.0f}ms"
                    })

            except httpx.TimeoutException:
                health_result["services"][name] = {
                    "status": "timeout",
                    "error": "Request timed out"
                }
                health_result["alerts"].append({
                    "level": "critical",
                    "message": f"{name} is not responding"
                })
            except httpx.ConnectError:
                health_result["services"][name] = {
                    "status": "down",
                    "error": "Connection refused"
                }
                health_result["alerts"].append({
                    "level": "critical",
                    "message": f"{name} is down"
                })
            except Exception as e:
                health_result["services"][name] = {
                    "status": "error",
                    "error": str(e)
                }

    # Analyze trends
    health_result["trends"] = {
        "memory": _analyze_trend("memory"),
        "cpu": _analyze_trend("cpu")
    }

    # Add trend-based alerts
    if health_result["trends"]["memory"] == "increasing":
        health_result["alerts"].append({
            "level": "warning",
            "message": "Memory usage is trending upward - possible memory leak"
        })
        health_result["recommendations"].append(
            "Monitor for memory leaks in application services"
        )

    # Set overall status based on alerts
    critical_alerts = [a for a in health_result["alerts"] if a["level"] == "critical"]
    warning_alerts = [a for a in health_result["alerts"] if a["level"] == "warning"]

    if critical_alerts:
        health_result["status"] = "critical"
    elif warning_alerts:
        health_result["status"] = "degraded"

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=health_result
    )


def _update_history(metric: str, value: float):
    """Update history for trend analysis"""
    global _health_history
    if metric in _health_history:
        _health_history[metric].append({"time": time.time(), "value": value})
        if len(_health_history[metric]) > _history_max_size:
            _health_history[metric] = _health_history[metric][-_history_max_size:]


def _analyze_trend(metric: str) -> str:
    """Analyze trend for a metric"""
    global _health_history
    if metric not in _health_history or len(_health_history[metric]) < 10:
        return "stable"

    values = [h["value"] for h in _health_history[metric]]
    first_half = sum(values[:len(values)//2]) / (len(values)//2)
    second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)

    if second_half > first_half * 1.2:
        return "increasing"
    elif second_half < first_half * 0.8:
        return "decreasing"
    return "stable"


@router.get("/health/metrics", summary="Prometheus-format health metrics")
async def health_metrics() -> JSONResponse:
    """
    Export health metrics in Prometheus format for scraping
    """
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        disk = psutil.disk_usage('/')

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "optiflow_health_status": 1,
                "optiflow_memory_used_percent": memory.percent,
                "optiflow_memory_available_bytes": memory.available,
                "optiflow_cpu_percent": cpu_percent,
                "optiflow_disk_used_percent": disk.percent,
                "optiflow_disk_free_bytes": disk.free
            }
        )
    except Exception as e:
        logger.error(f"Health metrics failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )
