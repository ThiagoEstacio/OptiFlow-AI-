"""PLC Tags API"""
from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.api.deps import get_current_user
from app.models.user import User
from app.services.plc_service import plc_service
from app.services.timeseries_service import timeseries_service

router = APIRouter()

@router.get("/tags")
async def list_tags(current_user: User = Depends(get_current_user)):
    """List all available PLC tags"""
    return {
        "tags": [
            {
                "name": tag.name,
                "address": tag.address,
                "data_type": tag.data_type,
                "description": tag.description,
                "unit": tag.unit,
                "min_value": tag.min_value,
                "max_value": tag.max_value,
            }
            for tag in plc_service.tags.values()
        ]
    }

@router.get("/tags/{tag_name}")
async def read_tag(tag_name: str, current_user: User = Depends(get_current_user)):
    """Read current value of a PLC tag"""
    value = await plc_service.read_tag_opcua(tag_name)
    tag = plc_service.tags.get(tag_name)
    if not tag:
        return {"error": "Tag not found"}
    return {
        "name": tag_name,
        "value": value,
        "timestamp": tag.timestamp.isoformat() if tag.timestamp else None,
        "quality": tag.quality,
        "unit": tag.unit
    }

@router.get("/tags/{tag_name}/history")
async def get_tag_history(
    tag_name: str,
    hours: int = 24,
    aggregate: str = None,
    window: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get historical data for a tag"""
    start = datetime.utcnow() - timedelta(hours=hours)
    history = timeseries_service.query_tag_history(
        tag_name=tag_name,
        start=start,
        aggregate=aggregate,
        window=window
    )
    return {"tag_name": tag_name, "data": history}

@router.get("/tags/{tag_name}/stats")
async def get_tag_statistics(
    tag_name: str,
    hours: int = 24,
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a tag"""
    start = datetime.utcnow() - timedelta(hours=hours)
    stats = timeseries_service.query_statistics(tag_name, start)
    return {"tag_name": tag_name, "statistics": stats}
