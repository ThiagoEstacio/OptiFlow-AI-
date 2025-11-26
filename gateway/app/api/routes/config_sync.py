"""
Config Sync API Routes
======================

API endpoints to manage configuration synchronization
between Gateway and Backend.

Gateway is read-only - Backend is the source of truth.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.config_sync import get_config_sync

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/config", tags=["Config Sync"])


# ==================== Response Models ====================

class SyncStatusResponse(BaseModel):
    """Config sync status"""
    backend_url: str
    sync_interval_seconds: int
    is_running: bool
    is_syncing: bool
    last_sync: Optional[str]
    last_error: Optional[str]
    cached_configs: dict


class SyncTriggerResponse(BaseModel):
    """Sync trigger result"""
    success: bool
    message: str
    tags_count: int
    alarms_count: int
    formulas_count: int


# ==================== Endpoints ====================

@router.get("/sync/status", response_model=SyncStatusResponse)
async def get_sync_status():
    """
    Get current config sync status.

    Returns information about:
    - Backend connection
    - Last sync time
    - Cached config counts
    - Any errors
    """
    sync_service = get_config_sync()

    if not sync_service:
        raise HTTPException(
            status_code=503,
            detail="Config sync service not initialized"
        )

    return sync_service.get_status()


@router.post("/sync/trigger", response_model=SyncTriggerResponse)
async def trigger_sync():
    """
    Manually trigger a full config sync.

    Fetches all configurations from Backend:
    - Tags
    - Alarms
    - Formulas

    Use this after making changes in Backend that
    should be immediately reflected in Gateway.
    """
    sync_service = get_config_sync()

    if not sync_service:
        raise HTTPException(
            status_code=503,
            detail="Config sync service not initialized"
        )

    if sync_service.status.is_syncing:
        raise HTTPException(
            status_code=409,
            detail="Sync already in progress"
        )

    try:
        success = await sync_service.sync_all()
        status = sync_service.status

        return SyncTriggerResponse(
            success=success,
            message="Sync completed" if success else "Sync completed with errors",
            tags_count=status.tags_count,
            alarms_count=status.alarms_count,
            formulas_count=status.formulas_count
        )

    except Exception as e:
        logger.error(f"Manual sync failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/tags")
async def get_cached_tags():
    """
    Get cached tag configurations.

    Returns tags fetched from Backend.
    These are read-only in Gateway.

    To modify tags, use Backend API: POST/PUT/DELETE /api/v1/tags
    """
    sync_service = get_config_sync()

    if not sync_service:
        raise HTTPException(
            status_code=503,
            detail="Config sync service not initialized"
        )

    tags = sync_service.tags

    return {
        "count": len(tags),
        "source": "backend_cache",
        "tags": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "data_type": t.data_type,
                "unit": t.unit,
                "deadband": t.deadband,
                "historize": t.historize,
                "adapter_id": t.adapter_id,
                "source_address": t.source_address,
            }
            for t in tags.values()
        ],
        "note": "Tags are managed via Backend API. Gateway cache is read-only."
    }


@router.get("/alarms")
async def get_cached_alarms():
    """
    Get cached alarm configurations.

    Returns alarms fetched from Backend.
    These are read-only in Gateway.

    To modify alarms, use Backend API: POST/PUT/DELETE /api/v1/alarms
    """
    sync_service = get_config_sync()

    if not sync_service:
        raise HTTPException(
            status_code=503,
            detail="Config sync service not initialized"
        )

    alarms = sync_service.alarms

    return {
        "count": len(alarms),
        "source": "backend_cache",
        "alarms": [
            {
                "id": a.id,
                "tag_id": a.tag_id,
                "name": a.name,
                "alarm_type": a.alarm_type,
                "setpoint": a.setpoint,
                "priority": a.priority,
                "enabled": a.enabled,
            }
            for a in alarms.values()
        ],
        "note": "Alarms are managed via Backend API. Gateway cache is read-only."
    }


@router.get("/formulas")
async def get_cached_formulas():
    """
    Get cached formula configurations.

    Returns formulas fetched from Backend.
    These are read-only in Gateway.

    To modify formulas, use Backend API: POST/PUT/DELETE /api/v1/formulas
    """
    sync_service = get_config_sync()

    if not sync_service:
        raise HTTPException(
            status_code=503,
            detail="Config sync service not initialized"
        )

    formulas = sync_service.formulas

    return {
        "count": len(formulas),
        "source": "backend_cache",
        "formulas": [
            {
                "id": f.id,
                "name": f.name,
                "expression": f.expression,
                "output_tag_id": f.output_tag_id,
                "input_tags": f.input_tags,
                "enabled": f.enabled,
            }
            for f in formulas.values()
        ],
        "note": "Formulas are managed via Backend API. Gateway cache is read-only."
    }


@router.get("/health")
async def config_sync_health():
    """
    Config sync health check.

    Verifies:
    - Service is running
    - Can connect to Backend
    - Has recent sync
    """
    sync_service = get_config_sync()

    if not sync_service:
        return {
            "status": "not_initialized",
            "message": "Config sync service not initialized"
        }

    status = sync_service.status

    # Determine health
    if not sync_service._running:
        health = "stopped"
    elif status.last_error:
        health = "degraded"
    elif status.last_sync is None:
        health = "initializing"
    else:
        health = "healthy"

    return {
        "status": health,
        "is_running": sync_service._running,
        "last_sync": status.last_sync.isoformat() if status.last_sync else None,
        "last_error": status.last_error,
        "cached_items": {
            "tags": status.tags_count,
            "alarms": status.alarms_count,
            "formulas": status.formulas_count
        },
        "backend_url": sync_service.backend_url
    }
