"""
Alarm endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.models.alarm import AlarmEvent, AlarmDefinition, AlarmState
from app.schemas.alarm import (
    AlarmDefinitionCreate,
    AlarmDefinitionUpdate,
    AlarmDefinitionResponse,
    AlarmEventResponse,
    AlarmAcknowledgeRequest
)

router = APIRouter()


@router.get("/events", response_model=List[AlarmEventResponse])
async def list_alarm_events(
    skip: int = 0,
    limit: int = 100,
    active: bool = None,
    db: AsyncSession = Depends(get_db)
):
    """List alarm events (alias endpoint for frontend compatibility)"""
    stmt = select(AlarmEvent)

    if active is not None:
        if active:
            stmt = stmt.where(AlarmEvent.state == AlarmState.ACTIVE)
        else:
            stmt = stmt.where(AlarmEvent.state.in_([AlarmState.ACKNOWLEDGED, AlarmState.CLEARED]))

    stmt = stmt.offset(skip).limit(limit).order_by(AlarmEvent.trigger_timestamp.desc())
    result = await db.execute(stmt)
    alarms = result.scalars().all()
    return alarms


@router.get("/", response_model=List[AlarmEventResponse])
async def list_alarms(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,  # active, acknowledged, cleared
    db: AsyncSession = Depends(get_db)
):
    """List all alarm events"""
    stmt = select(AlarmEvent)

    if status_filter:
        if status_filter.upper() in ['ACTIVE', 'ACKNOWLEDGED', 'CLEARED']:
            stmt = stmt.where(AlarmEvent.state == AlarmState[status_filter.upper()])

    stmt = stmt.offset(skip).limit(limit).order_by(AlarmEvent.trigger_timestamp.desc())
    result = await db.execute(stmt)
    alarms = result.scalars().all()
    return alarms


@router.post("/definitions", response_model=AlarmDefinitionResponse, status_code=status.HTTP_201_CREATED)
async def create_alarm_definition(
    alarm_def_in: AlarmDefinitionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new alarm definition"""
    alarm_def = AlarmDefinition(**alarm_def_in.model_dump())
    db.add(alarm_def)
    await db.commit()
    await db.refresh(alarm_def)
    return alarm_def


@router.get("/definitions", response_model=List[AlarmDefinitionResponse])
async def list_alarm_definitions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all alarm definitions"""
    stmt = select(AlarmDefinition).offset(skip).limit(limit)
    result = await db.execute(stmt)
    alarm_defs = result.scalars().all()
    return alarm_defs


@router.get("/definitions/{alarm_def_id}", response_model=AlarmDefinitionResponse)
async def get_alarm_definition(
    alarm_def_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get alarm definition by ID"""
    stmt = select(AlarmDefinition).where(AlarmDefinition.id == alarm_def_id)
    result = await db.execute(stmt)
    alarm_def = result.scalar_one_or_none()

    if not alarm_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm definition not found"
        )

    return alarm_def


@router.put("/definitions/{alarm_def_id}", response_model=AlarmDefinitionResponse)
async def update_alarm_definition(
    alarm_def_id: UUID,
    alarm_def_in: AlarmDefinitionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an alarm definition"""
    stmt = select(AlarmDefinition).where(AlarmDefinition.id == alarm_def_id)
    result = await db.execute(stmt)
    alarm_def = result.scalar_one_or_none()

    if not alarm_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm definition not found"
        )

    # Update only provided fields
    update_data = alarm_def_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(alarm_def, field, value)

    await db.commit()
    await db.refresh(alarm_def)
    return alarm_def


@router.delete("/definitions/{alarm_def_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alarm_definition(
    alarm_def_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete an alarm definition"""
    stmt = select(AlarmDefinition).where(AlarmDefinition.id == alarm_def_id)
    result = await db.execute(stmt)
    alarm_def = result.scalar_one_or_none()

    if not alarm_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm definition not found"
        )

    await db.delete(alarm_def)
    await db.commit()
    return None


@router.post("/{alarm_id}/acknowledge", response_model=AlarmEventResponse)
async def acknowledge_alarm(
    alarm_id: UUID,
    ack_request: AlarmAcknowledgeRequest,
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge an alarm event"""
    stmt = select(AlarmEvent).where(AlarmEvent.id == alarm_id)
    result = await db.execute(stmt)
    alarm = result.scalar_one_or_none()

    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm event not found"
        )

    if alarm.status != 'ACTIVE':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alarm is not in ACTIVE state"
        )

    # Update alarm status
    alarm.status = 'ACKNOWLEDGED'
    alarm.acknowledged_at = datetime.utcnow()
    alarm.acknowledgment_comment = ack_request.comment

    await db.commit()
    await db.refresh(alarm)
    return alarm


@router.get("/{alarm_id}", response_model=AlarmEventResponse)
async def get_alarm(
    alarm_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get alarm event by ID"""
    stmt = select(AlarmEvent).where(AlarmEvent.id == alarm_id)
    result = await db.execute(stmt)
    alarm = result.scalar_one_or_none()

    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm event not found"
        )

    return alarm
