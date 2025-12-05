"""
Communication Health API Routes - CORR-003
==========================================

Provides endpoints to monitor communication health and distinguish
between real zero values and communication loss.

Sprint 1 Task: CORR-003 - No detection of communication loss vs zero value
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.logger import logger

# Import communication monitor
try:
    from app.services.communication_monitor import (
        get_communication_monitor,
        CommunicationState,
        ValueSource
    )
    COMM_MONITOR_AVAILABLE = True
except ImportError:
    COMM_MONITOR_AVAILABLE = False
    logger.warning("Communication monitor not available")

router = APIRouter()


@router.get("/health")
async def get_communication_health():
    """
    Get overall communication health summary.

    Returns:
    - total_tags_monitored: Number of tags being tracked
    - healthy_tags: Tags with good communication
    - stale_tags: Tags with stale values
    - comm_loss_tags: Tags with communication loss
    - health_percentage: Overall health (0-100%)
    - adapters: Per-adapter health status
    """
    if not COMM_MONITOR_AVAILABLE:
        return {
            "error": "Communication monitor not available",
            "available": False
        }

    monitor = get_communication_monitor()
    return monitor.get_health_summary()


@router.get("/tags/stale")
async def get_stale_tags():
    """
    Get all tags with stale values.

    Stale tags haven't received updates within the threshold period.
    This could indicate communication issues or polling problems.
    """
    if not COMM_MONITOR_AVAILABLE:
        raise HTTPException(503, "Communication monitor not available")

    monitor = get_communication_monitor()
    stale_tags = monitor.get_all_stale_tags()

    return {
        "count": len(stale_tags),
        "tags": stale_tags,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/tags/comm-loss")
async def get_communication_loss_tags():
    """
    Get all tags with communication loss.

    CORR-003: Critical endpoint to identify tags where the value
    may be invalid due to communication loss (not a real zero!).
    """
    if not COMM_MONITOR_AVAILABLE:
        raise HTTPException(503, "Communication monitor not available")

    monitor = get_communication_monitor()
    comm_loss_tags = monitor.get_all_comm_loss_tags()

    return {
        "count": len(comm_loss_tags),
        "tags": comm_loss_tags,
        "timestamp": datetime.utcnow().isoformat(),
        "warning": "Values from these tags should NOT be trusted - communication was lost!"
    }


@router.get("/tags/{tag_id}")
async def get_tag_communication_state(tag_id: str):
    """
    Get communication state for a specific tag.

    Returns detailed information about:
    - Last successful read time
    - Current value source (real, cached, stale, comm_loss)
    - Communication quality
    - Whether the current zero value (if any) is real or from comm loss
    """
    if not COMM_MONITOR_AVAILABLE:
        raise HTTPException(503, "Communication monitor not available")

    monitor = get_communication_monitor()
    state = monitor.get_tag_state(tag_id)

    if not state:
        return {
            "tag_id": tag_id,
            "tracked": False,
            "message": "Tag not yet tracked by communication monitor"
        }

    return {
        "tag_id": tag_id,
        "tracked": True,
        **state
    }


@router.get("/adapters/{adapter_id}")
async def get_adapter_communication_state(adapter_id: str):
    """
    Get communication state for a specific adapter.

    Returns health metrics for all tags under this adapter.
    """
    if not COMM_MONITOR_AVAILABLE:
        raise HTTPException(503, "Communication monitor not available")

    monitor = get_communication_monitor()
    state = monitor.get_adapter_state(adapter_id)

    if not state:
        return {
            "adapter_id": adapter_id,
            "tracked": False,
            "message": "Adapter not yet tracked by communication monitor"
        }

    return {
        "adapter_id": adapter_id,
        "tracked": True,
        **state
    }


@router.post("/reset-stats")
async def reset_communication_statistics():
    """
    Reset communication statistics counters.

    This clears the accumulated statistics but keeps tracking states.
    """
    if not COMM_MONITOR_AVAILABLE:
        raise HTTPException(503, "Communication monitor not available")

    monitor = get_communication_monitor()
    monitor.reset_statistics()

    return {
        "success": True,
        "message": "Communication statistics reset",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/value-sources")
async def get_value_source_info():
    """
    Get information about value sources.

    CORR-003: Explains what each value source means for operators.
    """
    return {
        "value_sources": {
            "real": {
                "description": "Fresh value from device - trustworthy",
                "reliability": "HIGH",
                "action": "Value can be used for decisions"
            },
            "cached": {
                "description": "Valid but from cache - may be slightly old",
                "reliability": "MEDIUM",
                "action": "Value is likely accurate but verify if critical"
            },
            "stale": {
                "description": "Old value - device hasn't sent updates",
                "reliability": "LOW",
                "action": "Investigate why device isn't responding"
            },
            "comm_loss": {
                "description": "Communication lost - value is NOT trustworthy",
                "reliability": "NONE",
                "action": "DO NOT use for decisions - investigate immediately"
            },
            "unknown": {
                "description": "Cannot determine value source",
                "reliability": "UNKNOWN",
                "action": "Treat as suspicious until confirmed"
            }
        },
        "zero_value_guidance": {
            "description": "How to interpret zero values",
            "check_field": "zero_is_real",
            "if_true": "The sensor is reporting 0 - this is a valid measurement",
            "if_false": "The 0 might be due to communication loss - do NOT trust it"
        }
    }
