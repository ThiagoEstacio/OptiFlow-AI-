"""
Vessel endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.port.models.vessel import Vessel, VesselStatus
from app.port.schemas.vessel import VesselCreate, VesselUpdate, VesselResponse

router = APIRouter()


@router.get("/", response_model=List[VesselResponse])
async def list_vessels(
    skip: int = 0,
    limit: int = 100,
    site_id: UUID = None,
    status: VesselStatus = None,
    db: AsyncSession = Depends(get_db)
):
    """List all vessels"""
    stmt = select(Vessel)

    if site_id:
        stmt = stmt.where(Vessel.site_id == site_id)

    if status:
        stmt = stmt.where(Vessel.status == status)

    stmt = stmt.offset(skip).limit(limit).order_by(Vessel.eta.desc())
    result = await db.execute(stmt)
    vessels = result.scalars().all()
    return vessels


@router.post("/", response_model=VesselResponse, status_code=status.HTTP_201_CREATED)
async def create_vessel(
    vessel_in: VesselCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new vessel"""
    vessel = Vessel(**vessel_in.model_dump())
    db.add(vessel)
    await db.commit()
    await db.refresh(vessel)
    return vessel


@router.get("/{vessel_id}", response_model=VesselResponse)
async def get_vessel(
    vessel_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get vessel by ID"""
    stmt = select(Vessel).where(Vessel.id == vessel_id)
    result = await db.execute(stmt)
    vessel = result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vessel not found"
        )

    return vessel


@router.put("/{vessel_id}", response_model=VesselResponse)
async def update_vessel(
    vessel_id: UUID,
    vessel_in: VesselUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update vessel"""
    stmt = select(Vessel).where(Vessel.id == vessel_id)
    result = await db.execute(stmt)
    vessel = result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vessel not found"
        )

    # Update fields
    for field, value in vessel_in.model_dump(exclude_unset=True).items():
        setattr(vessel, field, value)

    await db.commit()
    await db.refresh(vessel)
    return vessel


@router.delete("/{vessel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vessel(
    vessel_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete vessel"""
    stmt = select(Vessel).where(Vessel.id == vessel_id)
    result = await db.execute(stmt)
    vessel = result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vessel not found"
        )

    await db.delete(vessel)
    await db.commit()


@router.get("/{vessel_id}/performance")
async def get_vessel_performance(
    vessel_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get vessel performance metrics"""
    stmt = select(Vessel).where(Vessel.id == vessel_id)
    result = await db.execute(stmt)
    vessel = result.scalar_one_or_none()

    if not vessel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vessel not found"
        )

    return {
        "vessel_id": str(vessel.id),
        "vessel_name": vessel.name,
        "status": vessel.status.value,
        "cargo": {
            "planned": vessel.cargo_quantity_planned,
            "actual": vessel.cargo_quantity_actual,
            "completion_percentage": (
                (vessel.cargo_quantity_actual / vessel.cargo_quantity_planned * 100)
                if vessel.cargo_quantity_planned and vessel.cargo_quantity_actual
                else 0
            )
        },
        "loading_rate": {
            "average": vessel.average_loading_rate,
            "peak": vessel.peak_loading_rate
        },
        "delays": {
            "demurrage_hours": vessel.demurrage_hours,
            "weather_delay_hours": vessel.weather_delay_hours,
            "equipment_delay_hours": vessel.equipment_delay_hours,
            "other_delay_hours": vessel.other_delay_hours,
            "total_delay_hours": (
                vessel.demurrage_hours + vessel.weather_delay_hours +
                vessel.equipment_delay_hours + vessel.other_delay_hours
            )
        },
        "timeline": {
            "eta": vessel.eta.isoformat() if vessel.eta else None,
            "ata": vessel.ata.isoformat() if vessel.ata else None,
            "etd": vessel.etd.isoformat() if vessel.etd else None,
            "atd": vessel.atd.isoformat() if vessel.atd else None,
            "loading_start": vessel.loading_start_time.isoformat() if vessel.loading_start_time else None,
            "loading_end": vessel.loading_end_time.isoformat() if vessel.loading_end_time else None,
            "duration_minutes": vessel.loading_duration_minutes
        }
    }
