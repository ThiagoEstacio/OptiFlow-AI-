"""
SmartPort API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.smartport import Berth, VesselVisit, PortKPI, BerthStatus, VesselType

router = APIRouter()


# Berths
@router.get("/berths/")
async def list_berths(
    site_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all berths"""
    stmt = select(Berth)

    if site_id:
        stmt = stmt.where(Berth.site_id == site_id)

    if status:
        stmt = stmt.where(Berth.status == status)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    berths = result.scalars().all()

    return [
        {
            "id": str(b.id),
            "name": b.name,
            "berth_number": b.berth_number,
            "status": b.status.value,
            "site_id": str(b.site_id),
            "max_vessel_length_m": b.max_vessel_length_m,
            "has_crane": b.has_crane,
            "number_of_cranes": b.number_of_cranes
        }
        for b in berths
    ]


@router.get("/berths/{berth_id}")
async def get_berth(berth_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get berth details"""
    stmt = select(Berth).where(Berth.id == berth_id)
    result = await db.execute(stmt)
    berth = result.scalar_one_or_none()

    if not berth:
        raise HTTPException(status_code=404, detail="Berth not found")

    return {
        "id": str(berth.id),
        "name": berth.name,
        "berth_number": berth.berth_number,
        "status": berth.status.value,
        "site_id": str(berth.site_id),
        "specifications": {
            "max_vessel_length_m": berth.max_vessel_length_m,
            "max_vessel_width_m": berth.max_vessel_width_m,
            "max_draft_m": berth.max_draft_m,
            "max_tonnage": berth.max_tonnage
        },
        "equipment": {
            "has_crane": berth.has_crane,
            "crane_capacity_tons": berth.crane_capacity_tons,
            "number_of_cranes": berth.number_of_cranes
        },
        "utilities": {
            "has_power_supply": berth.has_power_supply,
            "has_water_supply": berth.has_water_supply,
            "has_fuel_supply": berth.has_fuel_supply
        }
    }


# Vessel Visits
@router.get("/vessel-visits/")
async def list_vessel_visits(
    site_id: Optional[UUID] = None,
    berth_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List vessel visits"""
    stmt = select(VesselVisit).order_by(VesselVisit.arrival_time.desc())

    if site_id:
        stmt = stmt.where(VesselVisit.site_id == site_id)

    if berth_id:
        stmt = stmt.where(VesselVisit.berth_id == berth_id)

    if start_date:
        stmt = stmt.where(VesselVisit.arrival_time >= start_date)

    if end_date:
        stmt = stmt.where(VesselVisit.arrival_time <= end_date)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    visits = result.scalars().all()

    return [
        {
            "id": str(v.id),
            "vessel_name": v.vessel_name,
            "vessel_type": v.vessel_type.value,
            "imo_number": v.imo_number,
            "berth_id": str(v.berth_id) if v.berth_id else None,
            "arrival_time": v.arrival_time.isoformat(),
            "departure_time": v.departure_time.isoformat() if v.departure_time else None,
            "cargo_type": v.cargo_type,
            "turnaround_time_hours": v.turnaround_time_hours,
            "containers_loaded": v.containers_loaded,
            "containers_unloaded": v.containers_unloaded
        }
        for v in visits
    ]


@router.get("/vessel-visits/{visit_id}")
async def get_vessel_visit(visit_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get vessel visit details"""
    stmt = select(VesselVisit).where(VesselVisit.id == visit_id)
    result = await db.execute(stmt)
    visit = result.scalar_one_or_none()

    if not visit:
        raise HTTPException(status_code=404, detail="Vessel visit not found")

    return {
        "id": str(visit.id),
        "vessel_name": visit.vessel_name,
        "vessel_type": visit.vessel_type.value,
        "imo_number": visit.imo_number,
        "vessel_specs": {
            "gross_tonnage": visit.gross_tonnage,
            "length_m": visit.length_m,
            "width_m": visit.width_m,
            "draft_m": visit.draft_m,
            "flag": visit.flag
        },
        "visit_details": {
            "berth_id": str(visit.berth_id) if visit.berth_id else None,
            "arrival_time": visit.arrival_time.isoformat(),
            "departure_time": visit.departure_time.isoformat() if visit.departure_time else None,
            "estimated_departure": visit.estimated_departure.isoformat() if visit.estimated_departure else None
        },
        "cargo": {
            "cargo_type": visit.cargo_type,
            "cargo_weight_tons": visit.cargo_weight_tons,
            "containers_loaded": visit.containers_loaded,
            "containers_unloaded": visit.containers_unloaded
        },
        "performance": {
            "turnaround_time_hours": visit.turnaround_time_hours,
            "berthing_time_hours": visit.berthing_time_hours,
            "cargo_handling_time_hours": visit.cargo_handling_time_hours
        },
        "notes": visit.notes
    }


# KPIs
@router.get("/kpis/")
async def list_kpis(
    site_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    period_type: Optional[str] = "daily",
    db: AsyncSession = Depends(get_db)
):
    """List port KPIs"""
    stmt = select(PortKPI).where(PortKPI.site_id == site_id)

    if start_date:
        stmt = stmt.where(PortKPI.period_start >= start_date)

    if end_date:
        stmt = stmt.where(PortKPI.period_end <= end_date)

    if period_type:
        stmt = stmt.where(PortKPI.period_type == period_type)

    stmt = stmt.order_by(PortKPI.period_start.desc())
    result = await db.execute(stmt)
    kpis = result.scalars().all()

    return [
        {
            "id": str(k.id),
            "period_start": k.period_start.isoformat(),
            "period_end": k.period_end.isoformat(),
            "period_type": k.period_type,
            "vessel_metrics": {
                "total_vessel_visits": k.total_vessel_visits,
                "average_turnaround_time_hours": k.average_turnaround_time_hours,
                "average_waiting_time_hours": k.average_waiting_time_hours,
                "berth_occupancy_rate": k.berth_occupancy_rate
            },
            "cargo_metrics": {
                "total_cargo_handled_tons": k.total_cargo_handled_tons,
                "total_containers_handled": k.total_containers_handled,
                "average_cargo_handling_rate": k.average_cargo_handling_rate_tons_per_hour
            },
            "operational_metrics": {
                "crane_utilization_rate": k.crane_utilization_rate,
                "equipment_availability": k.equipment_availability,
                "labor_productivity": k.labor_productivity
            },
            "environmental_metrics": {
                "energy_consumption_kwh": k.energy_consumption_kwh,
                "carbon_emissions_tons": k.carbon_emissions_tons
            }
        }
        for k in kpis
    ]


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    site_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get SmartPort dashboard summary"""
    # Get current berth status
    berths_stmt = select(Berth).where(Berth.site_id == site_id)
    berths_result = await db.execute(berths_stmt)
    berths = berths_result.scalars().all()

    total_berths = len(berths)
    available_berths = len([b for b in berths if b.status == BerthStatus.AVAILABLE])
    occupied_berths = len([b for b in berths if b.status == BerthStatus.OCCUPIED])

    # Get today's vessel visits
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    visits_stmt = select(VesselVisit).where(
        VesselVisit.site_id == site_id,
        VesselVisit.arrival_time >= today_start
    )
    visits_result = await db.execute(visits_stmt)
    today_visits = visits_result.scalars().all()

    # Get active vessels (not yet departed)
    active_stmt = select(VesselVisit).where(
        VesselVisit.site_id == site_id,
        VesselVisit.departure_time == None
    )
    active_result = await db.execute(active_stmt)
    active_vessels = active_result.scalars().all()

    return {
        "berths": {
            "total": total_berths,
            "available": available_berths,
            "occupied": occupied_berths,
            "occupancy_rate": (occupied_berths / total_berths * 100) if total_berths > 0 else 0
        },
        "vessels": {
            "today_arrivals": len(today_visits),
            "active_vessels": len(active_vessels),
            "average_turnaround_hours": sum(v.turnaround_time_hours or 0 for v in active_vessels) / len(active_vessels) if active_vessels else 0
        },
        "cargo": {
            "total_containers_today": sum(v.containers_loaded + v.containers_unloaded for v in today_visits),
            "total_cargo_tons_today": sum(v.cargo_weight_tons or 0 for v in today_visits)
        }
    }
