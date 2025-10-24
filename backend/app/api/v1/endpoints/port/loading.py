"""
Loading Operation endpoints for SmartPort
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.port.loading_operation import (
    LoadingOperation,
    Cargo,
    OperationEvent,
    OperationStatus,
    OperationType,
    CommodityType,
)
from app.models.port.vessel import Vessel
from app.models.port.berth import Berth, BerthStatus
from app.schemas.port.loading_operation import (
    LoadingOperationCreate,
    LoadingOperationUpdate,
    LoadingOperationResponse,
    LoadingOperationDetailResponse,
    LoadingOperationProgressResponse,
    LoadingOperationListResponse,
    OperationStartRequest,
    OperationPauseRequest,
    OperationCompleteRequest,
    OperationDelayRequest,
    CargoResponse,
    OperationEventResponse,
)

router = APIRouter()


@router.get("/", response_model=List[LoadingOperationResponse])
async def list_loading_operations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000),
    site_id: Optional[UUID] = Query(None),
    vessel_id: Optional[UUID] = Query(None),
    berth_id: Optional[UUID] = Query(None),
    status: Optional[OperationStatus] = Query(None),
    operation_type: Optional[OperationType] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    delayed_only: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    List all loading operations with filtering
    """
    stmt = select(LoadingOperation)

    # Apply filters
    filters = []
    if site_id:
        filters.append(LoadingOperation.site_id == site_id)
    if vessel_id:
        filters.append(LoadingOperation.vessel_id == vessel_id)
    if berth_id:
        filters.append(LoadingOperation.berth_id == berth_id)
    if status:
        filters.append(LoadingOperation.status == status)
    if operation_type:
        filters.append(LoadingOperation.operation_type == operation_type)
    if from_date:
        filters.append(LoadingOperation.planned_start >= from_date)
    if to_date:
        filters.append(LoadingOperation.planned_end <= to_date)
    if delayed_only:
        filters.append(LoadingOperation.is_delayed == True)

    if filters:
        stmt = stmt.where(and_(*filters))

    stmt = stmt.offset(skip).limit(limit).order_by(LoadingOperation.created_at.desc())

    result = await db.execute(stmt)
    operations = result.scalars().all()

    return operations


@router.post("/", response_model=LoadingOperationResponse, status_code=status.HTTP_201_CREATED)
async def create_loading_operation(
    operation_in: LoadingOperationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new loading operation
    """
    # Check if operation number already exists
    stmt = select(LoadingOperation).where(LoadingOperation.operation_number == operation_in.operation_number)
    result = await db.execute(stmt)
    existing_operation = result.scalar_one_or_none()

    if existing_operation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Operation with number {operation_in.operation_number} already exists"
        )

    # Verify vessel exists
    stmt = select(Vessel).where(Vessel.id == operation_in.vessel_id)
    result = await db.execute(stmt)
    vessel = result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vessel not found"
        )

    # Verify berth exists and is available
    stmt = select(Berth).where(Berth.id == operation_in.berth_id)
    result = await db.execute(stmt)
    berth = result.scalar_one_or_none()

    if not berth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Berth not found"
        )

    # Create operation
    operation_data = operation_in.model_dump(exclude={"cargos"})
    operation = LoadingOperation(**operation_data)

    db.add(operation)
    await db.flush()  # Flush to get operation ID

    # Create cargos
    if operation_in.cargos:
        for cargo_data in operation_in.cargos:
            cargo = Cargo(
                **cargo_data.model_dump(),
                loading_operation_id=operation.id
            )
            db.add(cargo)

    # Create initial event
    event = OperationEvent(
        loading_operation_id=operation.id,
        event_type="created",
        event_time=datetime.utcnow(),
        description=f"Loading operation {operation.operation_number} created",
        event_data={"status": operation.status.value}
    )
    db.add(event)

    await db.commit()
    await db.refresh(operation)

    return operation


@router.get("/{operation_id}", response_model=LoadingOperationDetailResponse)
async def get_loading_operation(
    operation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get loading operation details
    """
    stmt = select(LoadingOperation).where(LoadingOperation.id == operation_id)
    result = await db.execute(stmt)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loading operation not found"
        )

    # Build detailed response
    response_data = LoadingOperationResponse.model_validate(operation).model_dump()

    # Get vessel info
    stmt = select(Vessel).where(Vessel.id == operation.vessel_id)
    result = await db.execute(stmt)
    vessel = result.scalar_one_or_none()

    if vessel:
        response_data["vessel_name"] = vessel.name
        response_data["vessel_imo"] = vessel.imo_number

    # Get berth info
    stmt = select(Berth).where(Berth.id == operation.berth_id)
    result = await db.execute(stmt)
    berth = result.scalar_one_or_none()

    if berth:
        response_data["berth_name"] = berth.name
        response_data["berth_code"] = berth.code

    # Get cargos
    stmt = select(Cargo).where(Cargo.loading_operation_id == operation_id)
    result = await db.execute(stmt)
    cargos = result.scalars().all()
    response_data["cargos"] = [CargoResponse.model_validate(c) for c in cargos]

    # Get events
    stmt = select(OperationEvent).where(OperationEvent.loading_operation_id == operation_id).order_by(OperationEvent.event_time.desc())
    result = await db.execute(stmt)
    events = result.scalars().all()
    response_data["events"] = [OperationEventResponse.model_validate(e) for e in events]

    # Calculate progress percentage
    if operation.total_planned_quantity > 0:
        progress_percentage = (operation.total_actual_quantity / operation.total_planned_quantity) * 100
        response_data["progress_percentage"] = round(progress_percentage, 2)
    else:
        response_data["progress_percentage"] = 0.0

    # Calculate estimated completion
    if operation.status == OperationStatus.IN_PROGRESS and operation.current_rate and operation.current_rate > 0:
        remaining_quantity = operation.total_planned_quantity - operation.total_actual_quantity
        hours_remaining = remaining_quantity / operation.current_rate
        response_data["time_remaining_hours"] = round(hours_remaining, 2)
        response_data["estimated_completion"] = datetime.utcnow() + timedelta(hours=hours_remaining)
    else:
        response_data["time_remaining_hours"] = None
        response_data["estimated_completion"] = None

    return LoadingOperationDetailResponse(**response_data)


@router.put("/{operation_id}", response_model=LoadingOperationResponse)
async def update_loading_operation(
    operation_id: UUID,
    operation_in: LoadingOperationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update loading operation
    """
    stmt = select(LoadingOperation).where(LoadingOperation.id == operation_id)
    result = await db.execute(stmt)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loading operation not found"
        )

    # Update operation
    update_data = operation_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(operation, field, value)

    await db.commit()
    await db.refresh(operation)

    return operation


@router.delete("/{operation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_loading_operation(
    operation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a loading operation (only if not started)
    """
    stmt = select(LoadingOperation).where(LoadingOperation.id == operation_id)
    result = await db.execute(stmt)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loading operation not found"
        )

    # Can only delete operations that haven't started
    if operation.status not in [OperationStatus.PLANNED, OperationStatus.READY]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete operation that has started. Use cancel instead."
        )

    await db.delete(operation)
    await db.commit()

    return None


# ===== CONTROL ENDPOINTS =====

@router.post("/{operation_id}/start", response_model=LoadingOperationResponse)
async def start_loading_operation(
    operation_id: UUID,
    request: OperationStartRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a loading operation
    """
    stmt = select(LoadingOperation).where(LoadingOperation.id == operation_id)
    result = await db.execute(stmt)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loading operation not found"
        )

    # Check if operation can be started
    if operation.status not in [OperationStatus.PLANNED, OperationStatus.READY, OperationStatus.PAUSED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start operation with status {operation.status.value}"
        )

    # Update operation status
    operation.status = OperationStatus.IN_PROGRESS
    operation.actual_start = request.actual_start or datetime.utcnow()

    # Update berth status
    stmt = select(Berth).where(Berth.id == operation.berth_id)
    result = await db.execute(stmt)
    berth = result.scalar_one_or_none()

    if berth:
        berth.status = BerthStatus.OCCUPIED
        berth.current_vessel_id = operation.vessel_id

    # Update vessel status
    stmt = select(Vessel).where(Vessel.id == operation.vessel_id)
    result = await db.execute(stmt)
    vessel = result.scalar_one_or_none()

    if vessel:
        vessel.status = "loading" if operation.operation_type == OperationType.LOADING else "unloading"
        vessel.current_berth_id = operation.berth_id
        vessel.atb = operation.actual_start  # Actual time of berthing

    # Create event
    event = OperationEvent(
        loading_operation_id=operation.id,
        event_type="start",
        event_time=operation.actual_start,
        description=f"Operation started{': ' + request.notes if request.notes else ''}",
        event_data={"notes": request.notes}
    )
    db.add(event)

    await db.commit()
    await db.refresh(operation)

    return operation


@router.post("/{operation_id}/pause", response_model=LoadingOperationResponse)
async def pause_loading_operation(
    operation_id: UUID,
    request: OperationPauseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Pause a loading operation
    """
    stmt = select(LoadingOperation).where(LoadingOperation.id == operation_id)
    result = await db.execute(stmt)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loading operation not found"
        )

    # Check if operation can be paused
    if operation.status != OperationStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pause operation with status {operation.status.value}"
        )

    # Update operation status
    operation.status = OperationStatus.PAUSED

    # Create event
    event = OperationEvent(
        loading_operation_id=operation.id,
        event_type="pause",
        event_time=datetime.utcnow(),
        description=f"Operation paused: {request.reason}",
        event_data={"reason": request.reason, "notes": request.notes}
    )
    db.add(event)

    await db.commit()
    await db.refresh(operation)

    return operation


@router.post("/{operation_id}/resume", response_model=LoadingOperationResponse)
async def resume_loading_operation(
    operation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Resume a paused loading operation
    """
    stmt = select(LoadingOperation).where(LoadingOperation.id == operation_id)
    result = await db.execute(stmt)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loading operation not found"
        )

    # Check if operation can be resumed
    if operation.status != OperationStatus.PAUSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot resume operation with status {operation.status.value}"
        )

    # Update operation status
    operation.status = OperationStatus.IN_PROGRESS

    # Create event
    event = OperationEvent(
        loading_operation_id=operation.id,
        event_type="resume",
        event_time=datetime.utcnow(),
        description="Operation resumed",
        event_data={}
    )
    db.add(event)

    await db.commit()
    await db.refresh(operation)

    return operation


@router.post("/{operation_id}/complete", response_model=LoadingOperationResponse)
async def complete_loading_operation(
    operation_id: UUID,
    request: OperationCompleteRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Complete a loading operation
    """
    stmt = select(LoadingOperation).where(LoadingOperation.id == operation_id)
    result = await db.execute(stmt)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loading operation not found"
        )

    # Check if operation can be completed
    if operation.status not in [OperationStatus.IN_PROGRESS, OperationStatus.PAUSED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete operation with status {operation.status.value}"
        )

    # Update operation
    operation.status = OperationStatus.COMPLETED
    operation.actual_end = request.actual_end or datetime.utcnow()

    if request.total_actual_quantity:
        operation.total_actual_quantity = request.total_actual_quantity

    # Calculate actual duration and rate
    if operation.actual_start and operation.actual_end:
        duration = operation.actual_end - operation.actual_start
        operation.working_hours = duration.total_seconds() / 3600

        if operation.working_hours > 0 and operation.total_actual_quantity > 0:
            operation.actual_rate = operation.total_actual_quantity / operation.working_hours

        # Calculate efficiency
        if operation.planned_rate and operation.actual_rate:
            operation.efficiency = (operation.actual_rate / operation.planned_rate) * 100

    # Update berth status to available
    stmt = select(Berth).where(Berth.id == operation.berth_id)
    result = await db.execute(stmt)
    berth = result.scalar_one_or_none()

    if berth:
        berth.status = BerthStatus.AVAILABLE
        berth.current_vessel_id = None

    # Update vessel status
    stmt = select(Vessel).where(Vessel.id == operation.vessel_id)
    result = await db.execute(stmt)
    vessel = result.scalar_one_or_none()

    if vessel:
        vessel.status = "completed"
        vessel.atc = operation.actual_end  # Actual time of completion

    # Create event
    event = OperationEvent(
        loading_operation_id=operation.id,
        event_type="complete",
        event_time=operation.actual_end,
        description=f"Operation completed{': ' + request.notes if request.notes else ''}",
        event_data={
            "total_actual_quantity": operation.total_actual_quantity,
            "actual_rate": operation.actual_rate,
            "efficiency": operation.efficiency,
            "notes": request.notes
        }
    )
    db.add(event)

    await db.commit()
    await db.refresh(operation)

    return operation


@router.post("/{operation_id}/delay", response_model=LoadingOperationResponse)
async def report_operation_delay(
    operation_id: UUID,
    request: OperationDelayRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Report a delay in operation
    """
    stmt = select(LoadingOperation).where(LoadingOperation.id == operation_id)
    result = await db.execute(stmt)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loading operation not found"
        )

    # Update operation delay info
    operation.is_delayed = True
    operation.delay_reason = request.delay_reason
    operation.delay_minutes += request.delay_minutes
    operation.status = OperationStatus.DELAYED

    # Create event
    event = OperationEvent(
        loading_operation_id=operation.id,
        event_type="delay",
        event_time=datetime.utcnow(),
        description=f"Delay reported: {request.delay_reason}",
        event_data={
            "reason": request.delay_reason,
            "delay_minutes": request.delay_minutes,
            "notes": request.notes
        }
    )
    db.add(event)

    await db.commit()
    await db.refresh(operation)

    return operation


@router.get("/{operation_id}/progress", response_model=LoadingOperationProgressResponse)
async def get_operation_progress(
    operation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get real-time operation progress
    """
    stmt = select(LoadingOperation).where(LoadingOperation.id == operation_id)
    result = await db.execute(stmt)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loading operation not found"
        )

    # Calculate progress
    progress_percentage = 0.0
    if operation.total_planned_quantity > 0:
        progress_percentage = (operation.total_actual_quantity / operation.total_planned_quantity) * 100

    remaining_quantity = operation.total_planned_quantity - operation.total_actual_quantity

    # Calculate time estimates
    time_elapsed_hours = None
    time_remaining_hours = None
    estimated_completion = None

    if operation.actual_start:
        time_elapsed = datetime.utcnow() - operation.actual_start
        time_elapsed_hours = time_elapsed.total_seconds() / 3600

        if operation.current_rate and operation.current_rate > 0:
            time_remaining_hours = remaining_quantity / operation.current_rate
            estimated_completion = datetime.utcnow() + timedelta(hours=time_remaining_hours)

    # Calculate average rate
    average_rate = None
    if time_elapsed_hours and time_elapsed_hours > 0:
        average_rate = operation.total_actual_quantity / time_elapsed_hours

    # Equipment status would come from TimeSeries/Device data in a real implementation
    equipment_status = {
        "equipment_count": len(operation.equipment_used),
        "equipment_codes": operation.equipment_used,
        # Real-time status would be fetched from devices/tags
    }

    return LoadingOperationProgressResponse(
        operation_id=operation.id,
        operation_number=operation.operation_number,
        status=operation.status,
        progress_percentage=round(progress_percentage, 2),
        total_planned_quantity=operation.total_planned_quantity,
        total_actual_quantity=operation.total_actual_quantity,
        remaining_quantity=remaining_quantity,
        current_rate=operation.current_rate,
        average_rate=average_rate,
        planned_rate=operation.planned_rate,
        actual_start=operation.actual_start,
        estimated_completion=estimated_completion,
        time_elapsed_hours=round(time_elapsed_hours, 2) if time_elapsed_hours else None,
        time_remaining_hours=round(time_remaining_hours, 2) if time_remaining_hours else None,
        efficiency=operation.efficiency,
        downtime_hours=operation.downtime_hours,
        is_delayed=operation.is_delayed,
        delay_minutes=operation.delay_minutes,
        equipment_status=equipment_status,
    )
