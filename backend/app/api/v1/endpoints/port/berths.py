"""
Berth endpoints for SmartPort
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.models.port.berth import Berth, BerthStatus, BerthType
from app.models.port.vessel import Vessel
from app.models.port.loading_operation import LoadingOperation
from app.models.port.equipment import PortEquipment
from app.schemas.port.berth import (
    BerthCreate,
    BerthUpdate,
    BerthResponse,
    BerthDetailResponse,
    BerthOccupancyResponse,
    BerthCapacityResponse,
    BerthListResponse,
)

router = APIRouter()


@router.get("/", response_model=List[BerthResponse])
async def list_berths(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, le=1000, description="Maximum number of records to return"),
    site_id: Optional[UUID] = Query(None, description="Filter by site ID"),
    status: Optional[BerthStatus] = Query(None, description="Filter by status"),
    berth_type: Optional[BerthType] = Query(None, description="Filter by berth type"),
    available: Optional[bool] = Query(None, description="Filter by availability"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all berths with optional filtering
    """
    stmt = select(Berth)

    # Apply filters
    filters = []
    if site_id:
        filters.append(Berth.site_id == site_id)
    if status:
        filters.append(Berth.status == status)
    if berth_type:
        filters.append(Berth.berth_type == berth_type)
    if available is not None:
        if available:
            filters.append(Berth.status == BerthStatus.AVAILABLE)
        else:
            filters.append(Berth.status != BerthStatus.AVAILABLE)

    if filters:
        stmt = stmt.where(and_(*filters))

    stmt = stmt.offset(skip).limit(limit).order_by(Berth.code)

    result = await db.execute(stmt)
    berths = result.scalars().all()

    return berths


@router.post("/", response_model=BerthResponse, status_code=status.HTTP_201_CREATED)
async def create_berth(
    berth_in: BerthCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new berth
    """
    # Check if berth with same code exists
    stmt = select(Berth).where(Berth.code == berth_in.code)
    result = await db.execute(stmt)
    existing_berth = result.scalar_one_or_none()

    if existing_berth:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Berth with code {berth_in.code} already exists"
        )

    # Create berth
    berth = Berth(**berth_in.model_dump())
    db.add(berth)
    await db.commit()
    await db.refresh(berth)

    return berth


@router.get("/{berth_id}", response_model=BerthDetailResponse)
async def get_berth(
    berth_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get berth details by ID
    """
    stmt = select(Berth).where(Berth.id == berth_id)
    result = await db.execute(stmt)
    berth = result.scalar_one_or_none()

    if not berth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Berth not found"
        )

    # Build detailed response
    response_data = BerthResponse.model_validate(berth).model_dump()

    # Get current vessel if occupied
    if berth.current_vessel_id:
        stmt = select(Vessel).where(Vessel.id == berth.current_vessel_id)
        result = await db.execute(stmt)
        vessel = result.scalar_one_or_none()

        if vessel:
            response_data["current_vessel_name"] = vessel.name
            response_data["current_vessel_imo"] = vessel.imo_number

    # Get current operation
    stmt = select(LoadingOperation).where(
        and_(
            LoadingOperation.berth_id == berth_id,
            LoadingOperation.status.in_(["in_progress", "paused", "ready"])
        )
    ).order_by(LoadingOperation.created_at.desc()).limit(1)

    result = await db.execute(stmt)
    current_operation = result.scalar_one_or_none()

    if current_operation:
        response_data["current_operation_id"] = current_operation.id

    # Calculate utilization rate (simplified - last 30 days)
    # This would be better calculated from actual time series data
    response_data["utilization_rate"] = None  # To be implemented with time series data

    # Get total operations count
    stmt = select(func.count(LoadingOperation.id)).where(LoadingOperation.berth_id == berth_id)
    result = await db.execute(stmt)
    total_operations = result.scalar()

    response_data["total_operations"] = total_operations

    return BerthDetailResponse(**response_data)


@router.put("/{berth_id}", response_model=BerthResponse)
async def update_berth(
    berth_id: UUID,
    berth_in: BerthUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update berth information
    """
    stmt = select(Berth).where(Berth.id == berth_id)
    result = await db.execute(stmt)
    berth = result.scalar_one_or_none()

    if not berth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Berth not found"
        )

    # Check if code is being changed and if new code already exists
    if berth_in.code and berth_in.code != berth.code:
        stmt = select(Berth).where(Berth.code == berth_in.code)
        result = await db.execute(stmt)
        existing_berth = result.scalar_one_or_none()

        if existing_berth:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Berth with code {berth_in.code} already exists"
            )

    # Update berth
    update_data = berth_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(berth, field, value)

    await db.commit()
    await db.refresh(berth)

    return berth


@router.delete("/{berth_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_berth(
    berth_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a berth
    """
    stmt = select(Berth).where(Berth.id == berth_id)
    result = await db.execute(stmt)
    berth = result.scalar_one_or_none()

    if not berth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Berth not found"
        )

    # Check if berth has active operations
    stmt = select(LoadingOperation).where(
        and_(
            LoadingOperation.berth_id == berth_id,
            LoadingOperation.status.in_(["in_progress", "paused", "ready"])
        )
    )
    result = await db.execute(stmt)
    active_operations = result.scalars().all()

    if active_operations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete berth with active operations"
        )

    await db.delete(berth)
    await db.commit()

    return None


@router.get("/{berth_id}/status", response_model=dict)
async def get_berth_status(
    berth_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current berth status with operational details
    """
    stmt = select(Berth).where(Berth.id == berth_id)
    result = await db.execute(stmt)
    berth = result.scalar_one_or_none()

    if not berth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Berth not found"
        )

    status_data = {
        "berth_id": str(berth.id),
        "berth_code": berth.code,
        "berth_name": berth.name,
        "status": berth.status.value,
        "current_vessel_id": str(berth.current_vessel_id) if berth.current_vessel_id else None,
        "current_vessel_name": None,
        "current_operation_id": None,
        "operation_progress": None,
        "equipment_status": [],
    }

    # Get current vessel
    if berth.current_vessel_id:
        stmt = select(Vessel).where(Vessel.id == berth.current_vessel_id)
        result = await db.execute(stmt)
        vessel = result.scalar_one_or_none()

        if vessel:
            status_data["current_vessel_name"] = vessel.name

    # Get current operation
    stmt = select(LoadingOperation).where(
        and_(
            LoadingOperation.berth_id == berth_id,
            LoadingOperation.status.in_(["in_progress", "paused", "ready"])
        )
    ).order_by(LoadingOperation.created_at.desc()).limit(1)

    result = await db.execute(stmt)
    current_operation = result.scalar_one_or_none()

    if current_operation:
        status_data["current_operation_id"] = str(current_operation.id)

        # Calculate progress
        if current_operation.total_planned_quantity > 0:
            progress = (current_operation.total_actual_quantity / current_operation.total_planned_quantity) * 100
            status_data["operation_progress"] = round(progress, 2)

    # Get equipment status
    stmt = select(PortEquipment).where(PortEquipment.berth_id == berth_id)
    result = await db.execute(stmt)
    equipment_list = result.scalars().all()

    status_data["equipment_status"] = [
        {
            "equipment_id": str(eq.id),
            "equipment_code": eq.code,
            "equipment_type": eq.equipment_type.value,
            "status": eq.status.value,
            "health_score": eq.health_score,
        }
        for eq in equipment_list
    ]

    return status_data


@router.get("/{berth_id}/occupancy", response_model=BerthOccupancyResponse)
async def get_berth_occupancy(
    berth_id: UUID,
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get berth occupancy timeline
    """
    stmt = select(Berth).where(Berth.id == berth_id)
    result = await db.execute(stmt)
    berth = result.scalar_one_or_none()

    if not berth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Berth not found"
        )

    # Get operations for this berth
    stmt = select(LoadingOperation).where(LoadingOperation.berth_id == berth_id)

    # Apply date filters
    if from_date:
        stmt = stmt.where(LoadingOperation.planned_start >= from_date)
    if to_date:
        stmt = stmt.where(LoadingOperation.planned_end <= to_date)

    stmt = stmt.order_by(LoadingOperation.planned_start)

    result = await db.execute(stmt)
    operations = result.scalars().all()

    # Build occupancy periods
    occupancy_periods = []

    for op in operations:
        # Get vessel name
        stmt = select(Vessel).where(Vessel.id == op.vessel_id)
        result = await db.execute(stmt)
        vessel = result.scalar_one_or_none()

        # Get main cargo commodity
        commodity = None
        total_quantity = 0
        if op.cargos:
            commodity = op.cargos[0].commodity.value if op.cargos else None
            total_quantity = sum(c.planned_quantity for c in op.cargos)

        occupancy_periods.append({
            "vessel_id": str(op.vessel_id),
            "vessel_name": vessel.name if vessel else "Unknown",
            "operation_id": str(op.id),
            "start": op.actual_start.isoformat() if op.actual_start else op.planned_start.isoformat(),
            "end": op.actual_end.isoformat() if op.actual_end else op.planned_end.isoformat(),
            "commodity": commodity,
            "quantity": total_quantity,
            "status": op.status.value,
        })

    return BerthOccupancyResponse(
        berth_id=berth.id,
        berth_name=berth.name,
        berth_code=berth.code,
        occupancy_periods=occupancy_periods,
    )


@router.get("/{berth_id}/capacity", response_model=BerthCapacityResponse)
async def get_berth_capacity(
    berth_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get berth capacity information
    """
    stmt = select(Berth).where(Berth.id == berth_id)
    result = await db.execute(stmt)
    berth = result.scalar_one_or_none()

    if not berth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Berth not found"
        )

    # Calculate current utilization (simplified)
    # In a real implementation, this would come from time series data
    current_utilization = 0.0
    available_capacity = berth.storage_capacity or 0.0

    # Check if berth is occupied
    if berth.status == BerthStatus.OCCUPIED and berth.current_vessel_id:
        # Get current operation
        stmt = select(LoadingOperation).where(
            and_(
                LoadingOperation.berth_id == berth_id,
                LoadingOperation.status.in_(["in_progress", "paused", "ready"])
            )
        ).order_by(LoadingOperation.created_at.desc()).limit(1)

        result = await db.execute(stmt)
        current_operation = result.scalar_one_or_none()

        if current_operation and berth.storage_capacity:
            current_utilization = (current_operation.total_actual_quantity / berth.storage_capacity) * 100
            available_capacity = berth.storage_capacity - current_operation.total_actual_quantity

    # Get equipment count
    stmt = select(PortEquipment).where(PortEquipment.berth_id == berth_id)
    result = await db.execute(stmt)
    all_equipment = result.scalars().all()

    equipment_total = len(all_equipment)
    equipment_available = len([eq for eq in all_equipment if eq.status in ["operating", "idle"]])

    # Determine next available time
    next_available = None
    if berth.status != BerthStatus.AVAILABLE:
        # Get the next operation's end time
        stmt = select(LoadingOperation).where(
            and_(
                LoadingOperation.berth_id == berth_id,
                LoadingOperation.status.in_(["in_progress", "paused", "ready"])
            )
        ).order_by(LoadingOperation.planned_end).limit(1)

        result = await db.execute(stmt)
        next_operation = result.scalar_one_or_none()

        if next_operation:
            next_available = next_operation.planned_end

    return BerthCapacityResponse(
        berth_id=berth.id,
        berth_name=berth.name,
        berth_code=berth.code,
        loading_rate=berth.loading_rate,
        unloading_rate=berth.unloading_rate,
        storage_capacity=berth.storage_capacity,
        current_utilization=round(current_utilization, 2),
        available_capacity=round(available_capacity, 2),
        equipment_available=equipment_available,
        equipment_total=equipment_total,
        next_available=next_available,
    )


@router.patch("/{berth_id}/status", response_model=BerthResponse)
async def update_berth_status(
    berth_id: UUID,
    new_status: BerthStatus,
    db: AsyncSession = Depends(get_db)
):
    """
    Update berth status
    """
    stmt = select(Berth).where(Berth.id == berth_id)
    result = await db.execute(stmt)
    berth = result.scalar_one_or_none()

    if not berth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Berth not found"
        )

    berth.status = new_status
    await db.commit()
    await db.refresh(berth)

    return berth
