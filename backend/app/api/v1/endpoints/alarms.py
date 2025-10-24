"""
Alarm endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models.alarm import AlarmEvent, AlarmState

router = APIRouter()


@router.get("/")
async def list_alarms(
    skip: int = 0,
    limit: int = 100,
    state: AlarmState = None,
    db: AsyncSession = Depends(get_db)
):
    """List all alarms"""
    stmt = select(AlarmEvent)

    if state:
        stmt = stmt.where(AlarmEvent.state == state)

    stmt = stmt.offset(skip).limit(limit).order_by(AlarmEvent.trigger_timestamp.desc())
    result = await db.execute(stmt)
    alarms = result.scalars().all()

    return [
        {
            "id": str(a.id),
            "state": a.state.value,
            "trigger_value": a.trigger_value,
            "trigger_timestamp": a.trigger_timestamp.isoformat() if a.trigger_timestamp else None,
            "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
        }
        for a in alarms
    ]


@router.post("/")
async def create_alarm(db: AsyncSession = Depends(get_db)):
    """Create alarm definition (placeholder)"""
    return {"message": "Alarm creation endpoint - to be implemented"}


@router.post("/{alarm_id}/ack")
async def acknowledge_alarm(alarm_id: str, db: AsyncSession = Depends(get_db)):
    """Acknowledge an alarm (placeholder)"""
    return {"message": f"Acknowledge alarm {alarm_id} - to be implemented"}
