"""
SmartPort - Vessels API Endpoints

CRUD operations and queries for vessels/ships.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.vessel import Vessel, VesselType, VesselStatus
from app.models.user import User
from app.schemas.smartport import (
    VesselCreate,
    VesselUpdate,
    VesselPositionUpdate,
    VesselResponse,
    VesselDetailResponse,
)

router = APIRouter()


@router.get("/", response_model=List[VesselResponse])
async def list_vessels(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    vessel_type: Optional[VesselType] = None,
    status: Optional[VesselStatus] = None,
    search: Optional[str] = None,
):
    """
    List all vessels with optional filtering.

    Filters:
    - vessel_type: Filter by vessel type
    - status: Filter by vessel status
    - search: Search by name or IMO number
    """
    query = select(Vessel)

    # Apply filters
    if vessel_type:
        query = query.where(Vessel.vessel_type == vessel_type)
    if status:
        query = query.where(Vessel.status == status)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Vessel.name.ilike(search_pattern),
                Vessel.imo.ilike(search_pattern)
            )
        )

    # Order by ETA (upcoming arrivals first) and apply pagination
    query = query.order_by(Vessel.eta.asc().nullslast()).offset(skip).limit(limit)

    result = await db.execute(query)
    vessels = result.scalars().all()

    return vessels


@router.get("/in-port", response_model=List[VesselResponse])
async def list_vessels_in_port(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all vessels currently in port (berthed, loading, or unloading)."""
    query = select(Vessel).where(
        Vessel.status.in_([
            VesselStatus.BERTHED,
            VesselStatus.LOADING,
            VesselStatus.UNLOADING
        ])
    ).order_by(Vessel.ata.desc())

    result = await db.execute(query)
    vessels = result.scalars().all()

    return vessels


@router.get("/expected-arrivals", response_model=List[VesselResponse])
async def list_expected_arrivals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    hours: int = Query(24, ge=1, le=168, description="Look ahead hours"),
):
    """
    List vessels expected to arrive within specified hours.

    Default: 24 hours
    """
    from datetime import timedelta

    cutoff_time = datetime.utcnow() + timedelta(hours=hours)

    query = select(Vessel).where(
        Vessel.status.in_([VesselStatus.APPROACHING, VesselStatus.ANCHORED]),
        Vessel.eta <= cutoff_time,
        Vessel.eta.isnot(None)
    ).order_by(Vessel.eta.asc())

    result = await db.execute(query)
    vessels = result.scalars().all()

    return vessels


@router.get("/{vessel_id}", response_model=VesselDetailResponse)
async def get_vessel(
    vessel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed vessel information."""
    query = select(Vessel).where(Vessel.id == vessel_id)
    result = await db.execute(query)
    vessel = result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")

    return vessel


@router.get("/imo/{imo}", response_model=VesselDetailResponse)
async def get_vessel_by_imo(
    imo: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get vessel by IMO number."""
    # Ensure IMO format
    if not imo.startswith("IMO"):
        imo = f"IMO{imo}"

    query = select(Vessel).where(Vessel.imo == imo)
    result = await db.execute(query)
    vessel = result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")

    return vessel


@router.post("/", response_model=VesselResponse, status_code=201)
async def create_vessel(
    vessel_in: VesselCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new vessel."""
    # Check if vessel with same IMO already exists
    imo = vessel_in.imo
    if not imo.startswith("IMO"):
        imo = f"IMO{imo}"

    query = select(Vessel).where(Vessel.imo == imo)
    result = await db.execute(query)
    existing_vessel = result.scalar_one_or_none()

    if existing_vessel:
        raise HTTPException(
            status_code=400,
            detail=f"Vessel with IMO {imo} already exists"
        )

    # Create new vessel
    vessel_data = vessel_in.model_dump()
    vessel = Vessel(**vessel_data)
    db.add(vessel)
    await db.commit()
    await db.refresh(vessel)

    return vessel


@router.put("/{vessel_id}", response_model=VesselResponse)
async def update_vessel(
    vessel_id: UUID,
    vessel_in: VesselUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update vessel information."""
    query = select(Vessel).where(Vessel.id == vessel_id)
    result = await db.execute(query)
    vessel = result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")

    # Update vessel fields
    update_data = vessel_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vessel, field, value)

    await db.commit()
    await db.refresh(vessel)

    return vessel


@router.put("/{vessel_id}/position", response_model=VesselResponse)
async def update_vessel_position(
    vessel_id: UUID,
    position: VesselPositionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update vessel GPS position (AIS data)."""
    query = select(Vessel).where(Vessel.id == vessel_id)
    result = await db.execute(query)
    vessel = result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")

    # Update position using method
    vessel.update_position(
        latitude=position.latitude,
        longitude=position.longitude,
        heading=position.heading,
        speed=position.speed_knots
    )

    await db.commit()
    await db.refresh(vessel)

    return vessel


@router.delete("/{vessel_id}", status_code=204)
async def delete_vessel(
    vessel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a vessel."""
    query = select(Vessel).where(Vessel.id == vessel_id)
    result = await db.execute(query)
    vessel = result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")

    # Check if vessel has active operations
    from app.models.port_operation import PortOperation, OperationStatus
    ops_query = select(func.count(PortOperation.id)).where(
        PortOperation.vessel_id == vessel_id,
        PortOperation.status.in_([
            OperationStatus.SCHEDULED,
            OperationStatus.IN_PROGRESS
        ])
    )
    ops_result = await db.execute(ops_query)
    active_ops = ops_result.scalar()

    if active_ops > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete vessel with {active_ops} active operations"
        )

    await db.delete(vessel)
    await db.commit()

    return None


@router.get("/stats/summary")
async def get_vessels_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get summary statistics for all vessels."""
    # Total vessels
    total_query = select(func.count(Vessel.id))
    total_result = await db.execute(total_query)
    total_vessels = total_result.scalar()

    # Count by status
    status_counts = {}
    for status in VesselStatus:
        count_query = select(func.count(Vessel.id)).where(
            Vessel.status == status
        )
        count_result = await db.execute(count_query)
        status_counts[status.value] = count_result.scalar()

    # Count by type
    type_counts = {}
    for vessel_type in VesselType:
        count_query = select(func.count(Vessel.id)).where(
            Vessel.vessel_type == vessel_type
        )
        count_result = await db.execute(count_query)
        type_counts[vessel_type.value] = count_result.scalar()

    # Count delayed vessels
    delayed_query = select(func.count(Vessel.id)).where(
        or_(
            Vessel.eta < datetime.utcnow(),
            Vessel.etd < datetime.utcnow()
        )
    )
    delayed_result = await db.execute(delayed_query)
    delayed_vessels = delayed_result.scalar()

    return {
        "total_vessels": total_vessels,
        "by_status": status_counts,
        "by_type": type_counts,
        "delayed_vessels": delayed_vessels,
        "in_port": status_counts.get("berthed", 0) +
                   status_counts.get("loading", 0) +
                   status_counts.get("unloading", 0),
    }
