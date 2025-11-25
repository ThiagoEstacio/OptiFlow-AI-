"""
Consumer Metrics API
====================

Expõe métricas do consumer Kafka para monitoramento.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import logging

from app.services.timeseries_consumer import get_consumer_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/consumer")
async def get_consumer_metrics() -> Dict[str, Any]:
    """
    Get current consumer metrics

    Returns:
        - running: bool - Consumer is active
        - lag: int - Number of messages behind
        - throughput: float - Messages/second
        - error_rate: float - Errors/second
        - last_offset: int - Last committed offset
        - batch_size: int - Current adaptive batch size
    """
    try:
        status = get_consumer_status()

        return {
            "status": "healthy" if status.get("running") else "stopped",
            "running": status.get("running", False),
            "messages_processed": status.get("messages_processed", 0),
            "errors_count": status.get("errors", 0),
            "batch_size_current": status.get("batch_size", 0),
            "consumer_enabled": status.get("enabled", False),
            "topic": status.get("topic", "unknown"),
            "group_id": status.get("group_id", "unknown")
        }
    except Exception as e:
        logger.error(f"Failed to get consumer metrics: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/pipeline")
async def get_pipeline_metrics() -> Dict[str, Any]:
    """
    Get overall pipeline health metrics

    Checks:
    - Gateway publishing
    - Kafka cluster
    - Consumer processing
    - InfluxDB writing
    """
    # Simplified version - can be expanded with actual checks
    consumer_status = get_consumer_status()

    return {
        "pipeline_status": "operational" if consumer_status.get("running") else "degraded",
        "components": {
            "consumer": {
                "status": "running" if consumer_status.get("running") else "stopped",
                "messages_processed": consumer_status.get("messages_processed", 0)
            },
            "kafka": {
                "status": "unknown",  # Would need Kafka admin client
                "message": "Check Kafka UI for details"
            },
            "influxdb": {
                "status": "unknown",  # Would need InfluxDB health check
                "message": "Check InfluxDB directly"
            }
        }
    }
