"""
Vessel endpoints for SmartPort
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.models.port.vessel import Vessel, VesselStatus, VesselType
from app.models.port.loading_operation import LoadingOperation
from app.schemas.port.vessel import (
    VesselCreate,
    VesselUpdate,
    VesselResponse,
    VesselDetailResponse,
    VesselListResponse,
)

router = APIRouter()


@router.get("/", response_model=List[VesselResponse])
async def list_vessels(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, le=1000, description="Maximum number of records to return"),
    site_id: Optional[UUID] = Query(None, description="Filter by site ID"),
    status: Optional[VesselStatus] = Query(None, description="Filter by status"),
    vessel_type: Optional[VesselType] = Query(None, description="Filter by vessel type"),
    name: Optional[str] = Query(None, description="Search by vessel name"),
    imo_number: Optional[str] = Query(None, description="Search by IMO number"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all vessels with optional filtering
    """
    # Build query with filters
    stmt = select(Vessel)

    # Apply filters
    filters = []
    if site_id:
        filters.append(Vessel.site_id == site_id)
    if status:
        filters.append(Vessel.status == status)
    if vessel_type:
        filters.append(Vessel.vessel_type == vessel_type)
    if name:
        filters.append(Vessel.name.ilike(f"%{name}%"))
    if imo_number:
        filters.append(Vessel.imo_number == imo_number)

    if filters:
        stmt = stmt.where(and_(*filters))

    stmt = stmt.offset(skip).limit(limit).order_by(Vessel.created_at.desc())

    result = await db.execute(stmt)
    vessels = result.scalars().all()

    return vessels


@router.post("/", response_model=VesselResponse, status_code=status.HTTP_201_CREATED)
async def create_vessel(
    vessel_in: VesselCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new vessel record
    """
    # Check if vessel with same IMO number exists
    stmt = select(Vessel).where(Vessel.imo_number == vessel_in.imo_number)
    result = await db.execute(stmt)
    existing_vessel = result.scalar_one_or_none()

    if existing_vessel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vessel with IMO number {vessel_in.imo_number} already exists"
        )

    # Create vessel
    vessel = Vessel(**vessel_in.model_dump())
    db.add(vessel)
    await db.commit()
    await db.refresh(vessel)

    return vessel


@router.get("/{vessel_id}", response_model=VesselDetailResponse)
async def get_vessel(
    vessel_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get vessel details by ID
    """
    stmt = select(Vessel).where(Vessel.id == vessel_id)
    result = await db.execute(stmt)
    vessel = result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vessel not found"
        )

    # Build detailed response
    response_data = VesselResponse.model_validate(vessel).model_dump()

    # Get current berth name if available
    if vessel.current_berth_id:
        response_data["current_berth_name"] = vessel.current_berth.name if vessel.current_berth else None

    # Get current operation
    stmt = select(LoadingOperation).where(
        and_(
            LoadingOperation.vessel_id == vessel_id,
            LoadingOperation.status.in_([
                "in_progress",
                "paused",
                "ready"
            ])
        )
    ).order_by(LoadingOperation.created_at.desc()).limit(1)

    result = await db.execute(stmt)
    current_operation = result.scalar_one_or_none()

    if current_operation:
        response_data["current_operation_id"] = current_operation.id

    # Get total operations count
    stmt = select(LoadingOperation).where(LoadingOperation.vessel_id == vessel_id)
    result = await db.execute(stmt)
    total_operations = len(result.scalars().all())

    response_data["total_operations"] = total_operations

    return VesselDetailResponse(**response_data)


@router.put("/{vessel_id}", response_model=VesselResponse)
async def update_vessel(
    vessel_id: UUID,
    vessel_in: VesselUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update vessel information
    """
    # Get vessel
    stmt = select(Vessel).where(Vessel.id == vessel_id)
    result = await db.execute(stmt)
    vessel = result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vessel not found"
        )

    # Update vessel
    update_data = vessel_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(vessel, field, value)

    await db.commit()
    await db.refresh(vessel)

    return vessel


@router.delete("/{vessel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vessel(
    vessel_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a vessel record
    """
    stmt = select(Vessel).where(Vessel.id == vessel_id)
    result = await db.execute(stmt)
    vessel = result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vessel not found"
        )

    # Check if vessel has active operations
    stmt = select(LoadingOperation).where(
        and_(
            LoadingOperation.vessel_id == vessel_id,
            LoadingOperation.status.in_([
                "in_progress",
                "paused",
                "ready"
            ])
        )
    )
    result = await db.execute(stmt)
    active_operations = result.scalars().all()

    if active_operations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete vessel with active operations. Complete or cancel operations first."
        )

    await db.delete(vessel)
    await db.commit()

    return None


@router.get("/{vessel_id}/operations", response_model=List[dict])
async def get_vessel_operations(
    vessel_id: UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all operations for a specific vessel
    """
    # Check if vessel exists
    stmt = select(Vessel).where(Vessel.id == vessel_id)
    result = await db.execute(stmt)
    vessel = result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vessel not found"
        )

    # Get operations
    stmt = select(LoadingOperation).where(
        LoadingOperation.vessel_id == vessel_id
    ).offset(skip).limit(limit).order_by(LoadingOperation.created_at.desc())

    result = await db.execute(stmt)
    operations = result.scalars().all()

    # Convert to dict (will be replaced with proper schema later)
    return [
        {
            "id": str(op.id),
            "operation_number": op.operation_number,
            "operation_type": op.operation_type.value,
            "status": op.status.value,
            "planned_start": op.planned_start.isoformat() if op.planned_start else None,
            "planned_end": op.planned_end.isoformat() if op.planned_end else None,
            "actual_start": op.actual_start.isoformat() if op.actual_start else None,
            "actual_end": op.actual_end.isoformat() if op.actual_end else None,
            "total_planned_quantity": op.total_planned_quantity,
            "total_actual_quantity": op.total_actual_quantity,
        }
        for op in operations
    ]


@router.get("/search/by-imo/{imo_number}", response_model=VesselResponse)
async def search_vessel_by_imo(
    imo_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Search vessel by IMO number
    """
    stmt = select(Vessel).where(Vessel.imo_number == imo_number)
    result = await db.execute(stmt)
    vessel = result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vessel with IMO {imo_number} not found"
        )

    return vessel


@router.patch("/{vessel_id}/status", response_model=VesselResponse)
async def update_vessel_status(
    vessel_id: UUID,
    new_status: VesselStatus,
    db: AsyncSession = Depends(get_db)
):
    """
    Update vessel status
    """
    stmt = select(Vessel).where(Vessel.id == vessel_id)
    result = await db.execute(stmt)
    vessel = result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vessel not found"
        )

    vessel.status = new_status
    await db.commit()
    await db.refresh(vessel)

    return vessel
