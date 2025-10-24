"""
Loading Operation endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
import uuid as uuid_lib

from app.db.session import get_db
from app.port.models.loading_operation import LoadingOperation, LoadingStatus
from app.port.schemas.loading import LoadingOperationCreate, LoadingOperationUpdate, LoadingOperationResponse

router = APIRouter()


@router.get("/", response_model=List[LoadingOperationResponse])
async def list_loading_operations(
    skip: int = 0,
    limit: int = 100,
    vessel_id: UUID = None,
    status: LoadingStatus = None,
    db: AsyncSession = Depends(get_db)
):
    """List all loading operations"""
    stmt = select(LoadingOperation)

    if vessel_id:
        stmt = stmt.where(LoadingOperation.vessel_id == vessel_id)

    if status:
        stmt = stmt.where(LoadingOperation.status == status)

    stmt = stmt.offset(skip).limit(limit).order_by(LoadingOperation.created_at.desc())
    result = await db.execute(stmt)
    operations = result.scalars().all()
    return operations


@router.post("/", response_model=LoadingOperationResponse, status_code=status.HTTP_201_CREATED)
async def create_loading_operation(
    operation_in: LoadingOperationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new loading operation"""
    # Generate operation number
    operation_number = f"LO-{uuid_lib.uuid4().hex[:8].upper()}"

    operation = LoadingOperation(
        **operation_in.model_dump(),
        operation_number=operation_number
    )

    db.add(operation)
    await db.commit()
    await db.refresh(operation)
    return operation


@router.get("/{operation_id}", response_model=LoadingOperationResponse)
async def get_loading_operation(
    operation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get loading operation by ID"""
    stmt = select(LoadingOperation).where(LoadingOperation.id == operation_id)
    result = await db.execute(stmt)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loading operation not found"
        )

    return operation


@router.put("/{operation_id}", response_model=LoadingOperationResponse)
async def update_loading_operation(
    operation_id: UUID,
    operation_in: LoadingOperationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update loading operation"""
    stmt = select(LoadingOperation).where(LoadingOperation.id == operation_id)
    result = await db.execute(stmt)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loading operation not found"
        )

    # Update fields
    for field, value in operation_in.model_dump(exclude_unset=True).items():
        setattr(operation, field, value)

    # Calculate metrics if operation is completed
    if operation.status == LoadingStatus.COMPLETED and operation.actual_start and operation.actual_end:
        duration = (operation.actual_end - operation.actual_start).total_seconds() / 60
        operation.actual_duration_minutes = int(duration)

        if duration > 0:
            operation.actual_loading_rate = (operation.actual_quantity / duration) * 60  # tons/hour

        if operation.target_quantity > 0:
            operation.efficiency_percentage = (operation.actual_quantity / operation.target_quantity) * 100

    await db.commit()
    await db.refresh(operation)
    return operation


@router.delete("/{operation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_loading_operation(
    operation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete loading operation"""
    stmt = select(LoadingOperation).where(LoadingOperation.id == operation_id)
    result = await db.execute(stmt)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loading operation not found"
        )

    await db.delete(operation)
    await db.commit()


@router.post("/{operation_id}/start")
async def start_loading_operation(
    operation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Start a loading operation"""
    from datetime import datetime

    stmt = select(LoadingOperation).where(LoadingOperation.id == operation_id)
    result = await db.execute(stmt)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loading operation not found"
        )

    if operation.status != LoadingStatus.PLANNED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Operation must be in PLANNED status to start"
        )

    operation.status = LoadingStatus.IN_PROGRESS
    operation.actual_start = datetime.utcnow()

    await db.commit()
    await db.refresh(operation)
    return operation


@router.post("/{operation_id}/complete")
async def complete_loading_operation(
    operation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Complete a loading operation"""
    from datetime import datetime

    stmt = select(LoadingOperation).where(LoadingOperation.id == operation_id)
    result = await db.execute(stmt)
    operation = result.scalar_one_or_none()

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loading operation not found"
        )

    if operation.status != LoadingStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Operation must be IN_PROGRESS to complete"
        )

    operation.status = LoadingStatus.COMPLETED
    operation.actual_end = datetime.utcnow()
    operation.progress_percentage = 100.0

    # Calculate metrics
    if operation.actual_start:
        duration = (operation.actual_end - operation.actual_start).total_seconds() / 60
        operation.actual_duration_minutes = int(duration)

        if duration > 0:
            operation.actual_loading_rate = (operation.actual_quantity / duration) * 60  # tons/hour
            operation.productivity_tons_per_hour = operation.actual_loading_rate

    if operation.target_quantity > 0:
        operation.efficiency_percentage = (operation.actual_quantity / operation.target_quantity) * 100

    await db.commit()
    await db.refresh(operation)
    return operation
