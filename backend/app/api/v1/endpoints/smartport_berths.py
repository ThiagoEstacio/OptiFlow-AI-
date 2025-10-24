"""
SmartPort - Berths API Endpoints

CRUD operations and queries for port berths.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models.berth import Berth, BerthType, BerthStatus
from app.models.user import User
from app.schemas.smartport import (
    BerthCreate,
    BerthUpdate,
    BerthResponse,
    BerthDetailResponse,
    BerthOccupancyStats,
)

router = APIRouter()


@router.get("/", response_model=List[BerthResponse])
async def list_berths(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    berth_type: Optional[BerthType] = None,
    status: Optional[BerthStatus] = None,
    is_active: Optional[bool] = True,
):
    """
    List all berths with optional filtering.

    Filters:
    - berth_type: Filter by berth type
    - status: Filter by berth status
    - is_active: Filter by active status
    """
    query = select(Berth)

    # Apply filters
    if berth_type:
        query = query.where(Berth.berth_type == berth_type)
    if status:
        query = query.where(Berth.status == status)
    if is_active is not None:
        query = query.where(Berth.is_active == is_active)

    # Order by name and apply pagination
    query = query.order_by(Berth.name).offset(skip).limit(limit)

    result = await db.execute(query)
    berths = result.scalars().all()

    return berths


@router.get("/available", response_model=List[BerthResponse])
async def list_available_berths(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    berth_type: Optional[BerthType] = None,
    min_loa: Optional[float] = None,
    min_beam: Optional[float] = None,
    min_draft: Optional[float] = None,
):
    """
    List available berths that can accommodate vessels with specified dimensions.

    Parameters:
    - berth_type: Filter by berth type
    - min_loa: Minimum length overall required
    - min_beam: Minimum beam width required
    - min_draft: Minimum draft depth required
    """
    query = select(Berth).where(
        Berth.status == BerthStatus.AVAILABLE,
        Berth.is_active == True,
        Berth.current_vessel_id.is_(None)
    )

    # Apply dimension filters
    if min_loa:
        query = query.where(Berth.max_loa >= min_loa)
    if min_beam:
        query = query.where(Berth.max_beam >= min_beam)
    if min_draft:
        query = query.where(Berth.max_draft >= min_draft)
    if berth_type:
        query = query.where(Berth.berth_type == berth_type)

    query = query.order_by(Berth.max_loa.desc())

    result = await db.execute(query)
    berths = result.scalars().all()

    return berths


@router.get("/{berth_id}", response_model=BerthDetailResponse)
async def get_berth(
    berth_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed berth information including current vessel."""
    query = select(Berth).where(Berth.id == berth_id).options(
        selectinload(Berth.current_vessel)
    )

    result = await db.execute(query)
    berth = result.scalar_one_or_none()

    if not berth:
        raise HTTPException(status_code=404, detail="Berth not found")

    return berth


@router.post("/", response_model=BerthResponse, status_code=201)
async def create_berth(
    berth_in: BerthCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new berth."""
    # Check if berth with same code already exists
    query = select(Berth).where(Berth.code == berth_in.code)
    result = await db.execute(query)
    existing_berth = result.scalar_one_or_none()

    if existing_berth:
        raise HTTPException(
            status_code=400,
            detail=f"Berth with code {berth_in.code} already exists"
        )

    # Create new berth
    berth = Berth(**berth_in.model_dump())
    db.add(berth)
    await db.commit()
    await db.refresh(berth)

    return berth


@router.put("/{berth_id}", response_model=BerthResponse)
async def update_berth(
    berth_id: UUID,
    berth_in: BerthUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update berth information."""
    query = select(Berth).where(Berth.id == berth_id)
    result = await db.execute(query)
    berth = result.scalar_one_or_none()

    if not berth:
        raise HTTPException(status_code=404, detail="Berth not found")

    # Update berth fields
    update_data = berth_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(berth, field, value)

    await db.commit()
    await db.refresh(berth)

    return berth


@router.delete("/{berth_id}", status_code=204)
async def delete_berth(
    berth_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a berth (soft delete by setting is_active=False)."""
    query = select(Berth).where(Berth.id == berth_id)
    result = await db.execute(query)
    berth = result.scalar_one_or_none()

    if not berth:
        raise HTTPException(status_code=404, detail="Berth not found")

    # Soft delete
    berth.is_active = False
    await db.commit()

    return None


@router.get("/{berth_id}/occupancy", response_model=BerthOccupancyStats)
async def get_berth_occupancy(
    berth_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get berth occupancy statistics.

    Returns historical occupancy data including:
    - Total hours in period
    - Occupied hours
    - Occupancy rate
    - Number of vessels served
    """
    from datetime import datetime, timedelta
    from app.models.port_operation import PortOperation, OperationStatus

    query = select(Berth).where(Berth.id == berth_id)
    result = await db.execute(query)
    berth = result.scalar_one_or_none()

    if not berth:
        raise HTTPException(status_code=404, detail="Berth not found")

    # Calculate occupancy for last 30 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    total_hours = (end_date - start_date).total_seconds() / 3600

    # Get completed operations for this berth in the period
    ops_query = select(PortOperation).where(
        PortOperation.berth_id == berth_id,
        PortOperation.status == OperationStatus.COMPLETED,
        PortOperation.actual_end >= start_date,
        PortOperation.actual_end <= end_date
    )
    ops_result = await db.execute(ops_query)
    operations = ops_result.scalars().all()

    # Calculate occupied hours
    occupied_hours = sum(
        (op.actual_end - op.actual_start).total_seconds() / 3600
        for op in operations
        if op.actual_start and op.actual_end
    )

    # Add current occupation if berth is occupied
    if berth.occupation_start and berth.status == BerthStatus.OCCUPIED:
        current_occupation = (end_date - berth.occupation_start).total_seconds() / 3600
        occupied_hours += current_occupation

    occupancy_rate = (occupied_hours / total_hours * 100) if total_hours > 0 else 0

    return BerthOccupancyStats(
        berth_id=berth.id,
        berth_name=berth.name,
        berth_code=berth.code,
        total_hours=total_hours,
        occupied_hours=occupied_hours,
        occupancy_rate=min(100, occupancy_rate),
        vessel_count=len(operations)
    )


@router.get("/stats/summary")
async def get_berths_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get summary statistics for all berths."""
    # Total berths
    total_query = select(func.count(Berth.id)).where(Berth.is_active == True)
    total_result = await db.execute(total_query)
    total_berths = total_result.scalar()

    # Count by status
    status_counts = {}
    for status in BerthStatus:
        count_query = select(func.count(Berth.id)).where(
            Berth.is_active == True,
            Berth.status == status
        )
        count_result = await db.execute(count_query)
        status_counts[status.value] = count_result.scalar()

    # Count by type
    type_counts = {}
    for berth_type in BerthType:
        count_query = select(func.count(Berth.id)).where(
            Berth.is_active == True,
            Berth.berth_type == berth_type
        )
        count_result = await db.execute(count_query)
        type_counts[berth_type.value] = count_result.scalar()

    return {
        "total_berths": total_berths,
        "by_status": status_counts,
        "by_type": type_counts,
        "occupancy_rate": (
            status_counts.get("occupied", 0) / total_berths * 100
            if total_berths > 0 else 0
        )
    }
