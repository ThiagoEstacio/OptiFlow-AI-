"""
Dashboard Statistics API endpoint
Provides system-wide statistics for the main dashboard
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any
from datetime import datetime, timedelta
import logging

from app.db.session import get_db
from app.models.device import Device
from app.models.tag import Tag
from app.models.alarm import AlarmDefinition, AlarmEvent, AlarmState
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(tags=["dashboard-stats"])
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get dashboard statistics including:
    - Total devices
    - Active devices
    - Total tags
    - Active alarms
    - Data points today (estimated)
    """
    try:
        # Total devices
        total_devices_result = await db.execute(
            select(func.count(Device.id))
        )
        total_devices = total_devices_result.scalar() or 0

        # Active devices (is_active = True)
        active_devices_result = await db.execute(
            select(func.count(Device.id)).where(Device.is_active == True)
        )
        active_devices = active_devices_result.scalar() or 0

        # Total tags
        total_tags_result = await db.execute(
            select(func.count(Tag.id))
        )
        total_tags = total_tags_result.scalar() or 0

        # Active alarms (state = ACTIVE or ACKNOWLEDGED)
        active_alarms_result = await db.execute(
            select(func.count(AlarmEvent.id)).where(
                AlarmEvent.state.in_([AlarmState.ACTIVE, AlarmState.ACKNOWLEDGED])
            )
        )
        active_alarms = active_alarms_result.scalar() or 0

        # Estimate data points today based on tags and scan rate
        # Average scan rate is ~1000ms, so ~86400 points per tag per day
        # But we'll use a reasonable estimate based on total tags
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        hours_elapsed = (datetime.utcnow() - today_start).total_seconds() / 3600

        # Estimate: 60 points per hour per active tag (1 per minute)
        data_points_today = int(total_tags * hours_elapsed * 60)

        return {
            "total_devices": total_devices,
            "active_devices": active_devices,
            "total_tags": total_tags,
            "active_alarms": active_alarms,
            "data_points_today": data_points_today
        }

    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {
            "total_devices": 0,
            "active_devices": 0,
            "total_tags": 0,
            "active_alarms": 0,
            "data_points_today": 0,
            "error": str(e)
        }
