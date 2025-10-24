"""
SmartPort - Dashboard API Endpoints

Consolidated KPIs and statistics for port dashboard.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.berth import Berth, BerthStatus
from app.models.vessel import Vessel, VesselStatus
from app.models.port_operation import PortOperation, OperationStatus
from app.models.user import User
from app.schemas.smartport import PortKPIs

router = APIRouter()


@router.get("/kpis", response_model=PortKPIs)
async def get_port_kpis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive port KPIs including:
    - Berth statistics (total, available, occupied, occupancy rate)
    - Vessel statistics (total, berthed, approaching)
    - Operation statistics (active, completed today)
    - Performance metrics (avg berthing time, efficiency)
    """
    # Berth statistics
    total_berths_query = select(func.count(Berth.id)).where(Berth.is_active == True)
    total_berths_result = await db.execute(total_berths_query)
    total_berths = total_berths_result.scalar() or 0

    available_berths_query = select(func.count(Berth.id)).where(
        Berth.is_active == True,
        Berth.status == BerthStatus.AVAILABLE
    )
    available_berths_result = await db.execute(available_berths_query)
    available_berths = available_berths_result.scalar() or 0

    occupied_berths_query = select(func.count(Berth.id)).where(
        Berth.is_active == True,
        Berth.status == BerthStatus.OCCUPIED
    )
    occupied_berths_result = await db.execute(occupied_berths_query)
    occupied_berths = occupied_berths_result.scalar() or 0

    # Vessel statistics
    total_vessels_query = select(func.count(Vessel.id))
    total_vessels_result = await db.execute(total_vessels_query)
    total_vessels = total_vessels_result.scalar() or 0

    berthed_vessels_query = select(func.count(Vessel.id)).where(
        Vessel.status.in_([
            VesselStatus.BERTHED,
            VesselStatus.LOADING,
            VesselStatus.UNLOADING
        ])
    )
    berthed_vessels_result = await db.execute(berthed_vessels_query)
    berthed_vessels = berthed_vessels_result.scalar() or 0

    approaching_vessels_query = select(func.count(Vessel.id)).where(
        Vessel.status.in_([
            VesselStatus.APPROACHING,
            VesselStatus.ANCHORED
        ])
    )
    approaching_vessels_result = await db.execute(approaching_vessels_query)
    approaching_vessels = approaching_vessels_result.scalar() or 0

    # Operation statistics
    active_operations_query = select(func.count(PortOperation.id)).where(
        PortOperation.status.in_([
            OperationStatus.IN_PROGRESS,
            OperationStatus.PAUSED
        ])
    )
    active_operations_result = await db.execute(active_operations_query)
    active_operations = active_operations_result.scalar() or 0

    # Completed operations today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    completed_today_query = select(func.count(PortOperation.id)).where(
        PortOperation.status == OperationStatus.COMPLETED,
        PortOperation.actual_end >= today_start
    )
    completed_today_result = await db.execute(completed_today_query)
    completed_operations_today = completed_today_result.scalar() or 0

    # Containers handled today
    containers_query = select(func.sum(PortOperation.containers_completed)).where(
        PortOperation.actual_end >= today_start
    )
    containers_result = await db.execute(containers_query)
    containers_handled_today = containers_result.scalar() or 0

    # Average berthing time (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    completed_ops_query = select(PortOperation).where(
        PortOperation.status == OperationStatus.COMPLETED,
        PortOperation.actual_end >= thirty_days_ago,
        PortOperation.actual_start.isnot(None),
        PortOperation.actual_end.isnot(None)
    )
    completed_ops_result = await db.execute(completed_ops_query)
    completed_ops = completed_ops_result.scalars().all()

    avg_berthing_time = 0
    operational_efficiency = 0

    if completed_ops:
        # Calculate average berthing time
        berthing_times = [
            (op.actual_end - op.actual_start).total_seconds() / 3600
            for op in completed_ops
        ]
        avg_berthing_time = sum(berthing_times) / len(berthing_times)

        # Calculate operational efficiency
        efficiencies = [
            op.efficiency_percentage
            for op in completed_ops
            if op.efficiency_percentage is not None
        ]
        if efficiencies:
            operational_efficiency = sum(efficiencies) / len(efficiencies)

    # Calculate berth occupancy rate
    berth_occupancy_rate = (
        (occupied_berths / total_berths * 100)
        if total_berths > 0 else 0
    )

    return PortKPIs(
        total_berths=total_berths,
        available_berths=available_berths,
        occupied_berths=occupied_berths,
        berth_occupancy_rate=round(berth_occupancy_rate, 2),
        total_vessels=total_vessels,
        berthed_vessels=berthed_vessels,
        approaching_vessels=approaching_vessels,
        active_operations=active_operations,
        completed_operations_today=completed_operations_today,
        containers_handled_today=containers_handled_today,
        average_berthing_time_hours=round(avg_berthing_time, 2),
        operational_efficiency=round(operational_efficiency, 2)
    )


@router.get("/timeline")
async def get_timeline_events(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    hours: int = Query(24, ge=1, le=168, description="Look ahead/back hours"),
):
    """
    Get timeline of port events (arrivals, departures, operation start/end).

    Returns events for the next N hours.
    """
    now = datetime.utcnow()
    start_time = now - timedelta(hours=hours)
    end_time = now + timedelta(hours=hours)

    events: List[Dict[str, Any]] = []

    # Vessel arrivals (ETA)
    arrivals_query = select(Vessel).where(
        Vessel.eta >= start_time,
        Vessel.eta <= end_time,
        Vessel.eta.isnot(None)
    )
    arrivals_result = await db.execute(arrivals_query)
    arrivals = arrivals_result.scalars().all()

    for vessel in arrivals:
        events.append({
            "type": "vessel_arrival",
            "timestamp": vessel.eta.isoformat(),
            "vessel_id": str(vessel.id),
            "vessel_name": vessel.name,
            "vessel_imo": vessel.imo,
            "description": f"ETA: {vessel.name} ({vessel.vessel_type.value})"
        })

    # Vessel departures (ETD)
    departures_query = select(Vessel).where(
        Vessel.etd >= start_time,
        Vessel.etd <= end_time,
        Vessel.etd.isnot(None),
        Vessel.status.in_([
            VesselStatus.BERTHED,
            VesselStatus.LOADING,
            VesselStatus.UNLOADING
        ])
    )
    departures_result = await db.execute(departures_query)
    departures = departures_result.scalars().all()

    for vessel in departures:
        events.append({
            "type": "vessel_departure",
            "timestamp": vessel.etd.isoformat(),
            "vessel_id": str(vessel.id),
            "vessel_name": vessel.name,
            "vessel_imo": vessel.imo,
            "description": f"ETD: {vessel.name} ({vessel.vessel_type.value})"
        })

    # Operation starts
    op_starts_query = select(PortOperation).where(
        PortOperation.scheduled_start >= start_time,
        PortOperation.scheduled_start <= end_time,
        PortOperation.status == OperationStatus.SCHEDULED
    )
    op_starts_result = await db.execute(op_starts_query)
    op_starts = op_starts_result.scalars().all()

    for operation in op_starts:
        events.append({
            "type": "operation_start",
            "timestamp": operation.scheduled_start.isoformat(),
            "operation_id": str(operation.id),
            "operation_type": operation.operation_type.value,
            "description": f"Operation start: {operation.operation_type.value}"
        })

    # Operation ends
    op_ends_query = select(PortOperation).where(
        PortOperation.estimated_end >= start_time,
        PortOperation.estimated_end <= end_time,
        PortOperation.status.in_([
            OperationStatus.IN_PROGRESS,
            OperationStatus.SCHEDULED
        ])
    )
    op_ends_result = await db.execute(op_ends_query)
    op_ends = op_ends_result.scalars().all()

    for operation in op_ends:
        events.append({
            "type": "operation_end",
            "timestamp": operation.estimated_end.isoformat(),
            "operation_id": str(operation.id),
            "operation_type": operation.operation_type.value,
            "description": f"Operation end: {operation.operation_type.value}"
        })

    # Sort events by timestamp
    events.sort(key=lambda x: x["timestamp"])

    return {
        "period_start": start_time.isoformat(),
        "period_end": end_time.isoformat(),
        "total_events": len(events),
        "events": events
    }


@router.get("/alerts")
async def get_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current alerts and warnings for port operations.

    Includes:
    - Delayed operations
    - Delayed vessel arrivals
    - Berth conflicts
    - Operations at risk
    """
    alerts: List[Dict[str, Any]] = []
    now = datetime.utcnow()

    # Delayed operations
    delayed_ops_query = select(PortOperation).where(
        PortOperation.status.in_([
            OperationStatus.IN_PROGRESS,
            OperationStatus.SCHEDULED
        ])
    )
    delayed_ops_result = await db.execute(delayed_ops_query)
    all_ops = delayed_ops_result.scalars().all()

    delayed_ops = [op for op in all_ops if op.is_delayed]

    for operation in delayed_ops:
        delay_hours = operation.delay_hours or 0
        alerts.append({
            "type": "operation_delayed",
            "severity": "high" if delay_hours > 4 else "medium",
            "operation_id": str(operation.id),
            "delay_hours": round(delay_hours, 2),
            "message": f"Operation delayed by {delay_hours:.1f} hours"
        })

    # Delayed vessel arrivals
    delayed_vessels_query = select(Vessel).where(
        Vessel.eta < now,
        Vessel.ata.is_(None),
        Vessel.status.in_([
            VesselStatus.APPROACHING,
            VesselStatus.ANCHORED
        ])
    )
    delayed_vessels_result = await db.execute(delayed_vessels_query)
    delayed_vessels = delayed_vessels_result.scalars().all()

    for vessel in delayed_vessels:
        delay_hours = (now - vessel.eta).total_seconds() / 3600
        alerts.append({
            "type": "vessel_arrival_delayed",
            "severity": "medium",
            "vessel_id": str(vessel.id),
            "vessel_name": vessel.name,
            "delay_hours": round(delay_hours, 2),
            "message": f"Vessel {vessel.name} arrival delayed by {delay_hours:.1f} hours"
        })

    # Operations with equipment/weather/labor delays
    problem_ops_query = select(PortOperation).where(
        PortOperation.status == OperationStatus.IN_PROGRESS,
        (PortOperation.weather_delay == True) |
        (PortOperation.equipment_delay == True) |
        (PortOperation.labor_delay == True)
    )
    problem_ops_result = await db.execute(problem_ops_query)
    problem_ops = problem_ops_result.scalars().all()

    for operation in problem_ops:
        reasons = []
        if operation.weather_delay:
            reasons.append("weather")
        if operation.equipment_delay:
            reasons.append("equipment")
        if operation.labor_delay:
            reasons.append("labor")

        alerts.append({
            "type": "operation_issues",
            "severity": "medium",
            "operation_id": str(operation.id),
            "issues": reasons,
            "message": f"Operation has issues: {', '.join(reasons)}"
        })

    # Sort alerts by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda x: severity_order.get(x["severity"], 3))

    return {
        "total_alerts": len(alerts),
        "high_severity": len([a for a in alerts if a["severity"] == "high"]),
        "medium_severity": len([a for a in alerts if a["severity"] == "medium"]),
        "low_severity": len([a for a in alerts if a["severity"] == "low"]),
        "alerts": alerts
    }
