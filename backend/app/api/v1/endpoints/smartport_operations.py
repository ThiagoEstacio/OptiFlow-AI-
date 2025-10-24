"""
SmartPort - Port Operations API Endpoints

CRUD operations and queries for port operations (loading/unloading).
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models.port_operation import PortOperation, OperationType, OperationStatus
from app.models.user import User
from app.schemas.smartport import (
    PortOperationCreate,
    PortOperationUpdate,
    PortOperationProgressUpdate,
    PortOperationResponse,
    PortOperationDetailResponse,
    OperationPerformanceStats,
)

router = APIRouter()


@router.get("/", response_model=List[PortOperationResponse])
async def list_operations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    operation_type: Optional[OperationType] = None,
    status: Optional[OperationStatus] = None,
    vessel_id: Optional[UUID] = None,
    berth_id: Optional[UUID] = None,
):
    """
    List all port operations with optional filtering.

    Filters:
    - operation_type: Filter by operation type
    - status: Filter by operation status
    - vessel_id: Filter by vessel
    - berth_id: Filter by berth
    """
    query = select(PortOperation)

    # Apply filters
    if operation_type:
        query = query.where(PortOperation.operation_type == operation_type)
    if status:
        query = query.where(PortOperation.status == status)
    if vessel_id:
        query = query.where(PortOperation.vessel_id == vessel_id)
    if berth_id:
        query = query.where(PortOperation.berth_id == berth_id)

    # Order by scheduled start and apply pagination
    query = query.order_by(PortOperation.scheduled_start.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    operations = result.scalars().all()

    return operations


@router.get("/active", response_model=List[PortOperationDetailResponse])
async def list_active_operations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all currently active operations (in progress or paused)."""
    query = select(PortOperation).where(
        PortOperation.status.in_([
            OperationStatus.IN_PROGRESS,
            OperationStatus.PAUSED
        ])
    ).options(
        selectinload(PortOperation.vessel),
        selectinload(PortOperation.berth)
    ).order_by(PortOperation.scheduled_start.asc())

    result = await db.execute(query)
    operations = result.scalars().all()

    return operations


@router.get("/today", response_model=List[PortOperationResponse])
async def list_todays_operations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all operations scheduled for today."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    query = select(PortOperation).where(
        PortOperation.scheduled_start >= today_start,
        PortOperation.scheduled_start < today_end
    ).order_by(PortOperation.scheduled_start.asc())

    result = await db.execute(query)
    operations = result.scalars().all()

    return operations


@router.get("/delayed", response_model=List[PortOperationDetailResponse])
async def list_delayed_operations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all delayed operations."""
    now = datetime.utcnow()

    query = select(PortOperation).where(
        PortOperation.status.in_([
            OperationStatus.DELAYED,
            OperationStatus.SCHEDULED,
            OperationStatus.IN_PROGRESS
        ])
    ).options(
        selectinload(PortOperation.vessel),
        selectinload(PortOperation.berth)
    )

    result = await db.execute(query)
    all_operations = result.scalars().all()

    # Filter delayed operations
    delayed_operations = [op for op in all_operations if op.is_delayed]

    return delayed_operations


@router.get("/{operation_id}", response_model=PortOperationDetailResponse)
async def get_operation(
    operation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed operation information including vessel and berth."""
    query = select(PortOperation).where(
        PortOperation.id == operation_id
    ).options(
        selectinload(PortOperation.vessel),
        selectinload(PortOperation.berth)
    )

    result = await db.execute(query)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")

    return operation


@router.post("/", response_model=PortOperationResponse, status_code=201)
async def create_operation(
    operation_in: PortOperationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new port operation."""
    from app.models.vessel import Vessel
    from app.models.berth import Berth, BerthStatus

    # Verify vessel exists
    vessel_query = select(Vessel).where(Vessel.id == operation_in.vessel_id)
    vessel_result = await db.execute(vessel_query)
    vessel = vessel_result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")

    # Verify berth exists and is available
    berth_query = select(Berth).where(Berth.id == operation_in.berth_id)
    berth_result = await db.execute(berth_query)
    berth = berth_result.scalar_one_or_none()

    if not berth:
        raise HTTPException(status_code=404, detail="Berth not found")

    # Check if berth can accommodate vessel
    if not berth.can_accommodate_vessel(vessel.loa, vessel.beam, vessel.draft):
        raise HTTPException(
            status_code=400,
            detail=f"Berth {berth.code} cannot accommodate vessel {vessel.name}"
        )

    # Create new operation
    operation_data = operation_in.model_dump()
    operation_data["created_by"] = current_user.email
    operation = PortOperation(**operation_data)

    db.add(operation)
    await db.commit()
    await db.refresh(operation)

    # Update berth status if operation starts immediately
    if operation.status == OperationStatus.IN_PROGRESS:
        berth.status = BerthStatus.OCCUPIED
        berth.current_vessel_id = vessel.id
        berth.occupation_start = operation.actual_start
        berth.estimated_departure = operation.estimated_end
        await db.commit()

    return operation


@router.put("/{operation_id}", response_model=PortOperationResponse)
async def update_operation(
    operation_id: UUID,
    operation_in: PortOperationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update operation information."""
    query = select(PortOperation).where(PortOperation.id == operation_id)
    result = await db.execute(query)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")

    # Update operation fields
    update_data = operation_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(operation, field, value)

    # Recalculate metrics if operation is active
    if operation.is_active:
        operation.calculate_productivity()
        operation.calculate_efficiency()

    await db.commit()
    await db.refresh(operation)

    return operation


@router.put("/{operation_id}/progress", response_model=PortOperationResponse)
async def update_operation_progress(
    operation_id: UUID,
    progress: PortOperationProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update operation progress (containers/tonnage completed)."""
    query = select(PortOperation).where(PortOperation.id == operation_id)
    result = await db.execute(query)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")

    # Update progress using method
    operation.update_progress(
        containers=progress.containers_completed,
        tonnage=progress.tonnage_completed,
        cubic_meters=progress.cubic_meters_completed
    )

    # Recalculate metrics
    operation.calculate_productivity()
    operation.calculate_efficiency()

    await db.commit()
    await db.refresh(operation)

    return operation


@router.post("/{operation_id}/start", response_model=PortOperationResponse)
async def start_operation(
    operation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a scheduled operation."""
    from app.models.berth import Berth, BerthStatus
    from app.models.vessel import Vessel, VesselStatus

    query = select(PortOperation).where(PortOperation.id == operation_id)
    result = await db.execute(query)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")

    if operation.status != OperationStatus.SCHEDULED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start operation with status {operation.status.value}"
        )

    # Update operation
    operation.status = OperationStatus.IN_PROGRESS
    operation.actual_start = datetime.utcnow()

    # Update berth
    berth_query = select(Berth).where(Berth.id == operation.berth_id)
    berth_result = await db.execute(berth_query)
    berth = berth_result.scalar_one_or_none()

    if berth:
        berth.status = BerthStatus.OCCUPIED
        berth.current_vessel_id = operation.vessel_id
        berth.occupation_start = operation.actual_start
        berth.estimated_departure = operation.estimated_end

    # Update vessel status
    vessel_query = select(Vessel).where(Vessel.id == operation.vessel_id)
    vessel_result = await db.execute(vessel_query)
    vessel = vessel_result.scalar_one_or_none()

    if vessel:
        if operation.operation_type == OperationType.LOADING:
            vessel.status = VesselStatus.LOADING
        elif operation.operation_type == OperationType.UNLOADING:
            vessel.status = VesselStatus.UNLOADING
        else:
            vessel.status = VesselStatus.BERTHED

    await db.commit()
    await db.refresh(operation)

    return operation


@router.post("/{operation_id}/complete", response_model=PortOperationResponse)
async def complete_operation(
    operation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark an operation as completed."""
    from app.models.berth import Berth, BerthStatus
    from app.models.vessel import Vessel, VesselStatus

    query = select(PortOperation).where(PortOperation.id == operation_id)
    result = await db.execute(query)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")

    if operation.status not in [OperationStatus.IN_PROGRESS, OperationStatus.PAUSED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot complete operation with status {operation.status.value}"
        )

    # Update operation
    operation.status = OperationStatus.COMPLETED
    operation.actual_end = datetime.utcnow()

    # Calculate final metrics
    operation.calculate_productivity()
    operation.calculate_efficiency()

    # Free up berth
    berth_query = select(Berth).where(Berth.id == operation.berth_id)
    berth_result = await db.execute(berth_query)
    berth = berth_result.scalar_one_or_none()

    if berth and berth.current_vessel_id == operation.vessel_id:
        berth.status = BerthStatus.AVAILABLE
        berth.current_vessel_id = None
        berth.occupation_start = None
        berth.estimated_departure = None

    # Update vessel to ready to depart
    vessel_query = select(Vessel).where(Vessel.id == operation.vessel_id)
    vessel_result = await db.execute(vessel_query)
    vessel = vessel_result.scalar_one_or_none()

    if vessel:
        vessel.status = VesselStatus.BERTHED

    await db.commit()
    await db.refresh(operation)

    return operation


@router.delete("/{operation_id}", status_code=204)
async def delete_operation(
    operation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete (cancel) a port operation."""
    query = select(PortOperation).where(PortOperation.id == operation_id)
    result = await db.execute(query)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")

    # Only allow deletion of scheduled or cancelled operations
    if operation.status in [OperationStatus.IN_PROGRESS, OperationStatus.COMPLETED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete operation with status {operation.status.value}"
        )

    # Mark as cancelled instead of deleting
    operation.status = OperationStatus.CANCELLED
    await db.commit()

    return None


@router.get("/stats/performance", response_model=OperationPerformanceStats)
async def get_operations_performance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365, description="Look back days"),
):
    """
    Get operations performance statistics for specified period.

    Default: Last 30 days
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    query = select(PortOperation).where(
        PortOperation.created_at >= cutoff_date
    )

    result = await db.execute(query)
    operations = result.scalars().all()

    # Calculate statistics
    total_operations = len(operations)
    completed_ops = [op for op in operations if op.status == OperationStatus.COMPLETED]
    in_progress_ops = [op for op in operations if op.status == OperationStatus.IN_PROGRESS]
    delayed_ops = [op for op in operations if op.is_delayed]

    # Calculate averages
    avg_duration = 0
    avg_efficiency = 0
    total_containers = 0
    total_tonnage = 0

    if completed_ops:
        durations = [op.duration_hours for op in completed_ops if op.duration_hours]
        avg_duration = sum(durations) / len(durations) if durations else 0

        efficiencies = [op.efficiency_percentage for op in completed_ops if op.efficiency_percentage]
        avg_efficiency = sum(efficiencies) / len(efficiencies) if efficiencies else 0

        total_containers = sum(op.containers_completed for op in completed_ops)
        total_tonnage = sum(op.tonnage_completed for op in completed_ops)

    return OperationPerformanceStats(
        total_operations=total_operations,
        completed_operations=len(completed_ops),
        in_progress_operations=len(in_progress_ops),
        delayed_operations=len(delayed_ops),
        average_duration_hours=avg_duration,
        average_efficiency=avg_efficiency,
        total_containers=total_containers,
        total_tonnage=total_tonnage
    )
