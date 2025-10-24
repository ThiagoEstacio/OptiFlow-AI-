"""
Analytics endpoints for SmartPort
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.port.loading_operation import LoadingOperation, OperationStatus, CommodityType
from app.models.port.vessel import Vessel, VesselStatus
from app.models.port.berth import Berth, BerthStatus
from app.models.port.equipment import PortEquipment
from app.schemas.port.analytics import (
    PortKPIResponse,
    PerformanceMetricsResponse,
    EquipmentPerformanceResponse,
    TrendResponse,
    CommodityBreakdownResponse,
    CommodityAnalyticsResponse,
)

router = APIRouter()


@router.get("/kpis", response_model=PortKPIResponse)
async def get_port_kpis(
    site_id: Optional[UUID] = Query(None),
    from_date: datetime = Query(..., description="Start date"),
    to_date: datetime = Query(..., description="End date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get port operational KPIs for a period
    """
    # Build query filters
    filters = [
        LoadingOperation.planned_start >= from_date,
        LoadingOperation.planned_end <= to_date,
    ]
    if site_id:
        filters.append(LoadingOperation.site_id == site_id)

    # Get all operations in period
    stmt = select(LoadingOperation).where(and_(*filters))
    result = await db.execute(stmt)
    operations = result.scalars().all()

    # Calculate KPIs
    total_operations = len(operations)
    completed_operations = len([op for op in operations if op.status == OperationStatus.COMPLETED])
    active_operations = len([op for op in operations if op.status == OperationStatus.IN_PROGRESS])
    delayed_operations = len([op for op in operations if op.is_delayed])

    # Throughput
    total_throughput = sum(op.total_actual_quantity for op in operations if op.total_actual_quantity)
    days_in_period = (to_date - from_date).days or 1
    daily_average_throughput = total_throughput / days_in_period if days_in_period > 0 else 0

    # Calculate average loading rate from completed operations
    completed_ops_with_rate = [op for op in operations if op.status == OperationStatus.COMPLETED and op.actual_rate]
    average_loading_rate = sum(op.actual_rate for op in completed_ops_with_rate) / len(completed_ops_with_rate) if completed_ops_with_rate else 0

    # Calculate average efficiency
    ops_with_efficiency = [op for op in operations if op.efficiency]
    average_efficiency = sum(op.efficiency for op in ops_with_efficiency) / len(ops_with_efficiency) if ops_with_efficiency else 0

    # Total downtime
    total_downtime_hours = sum(op.downtime_hours for op in operations)
    average_downtime_per_operation = total_downtime_hours / total_operations if total_operations > 0 else 0

    # Vessel counts
    vessel_filters = []
    if site_id:
        vessel_filters.append(Vessel.site_id == site_id)

    stmt = select(Vessel).where(and_(*vessel_filters)) if vessel_filters else select(Vessel)
    result = await db.execute(stmt)
    all_vessels = result.scalars().all()

    total_vessels = len(all_vessels)
    vessels_in_port = len([v for v in all_vessels if v.status in [VesselStatus.BERTHED, VesselStatus.LOADING, VesselStatus.UNLOADING]])
    vessels_berthed = len([v for v in all_vessels if v.status in [VesselStatus.BERTHED, VesselStatus.LOADING, VesselStatus.UNLOADING]])
    vessels_waiting = len([v for v in all_vessels if v.status in [VesselStatus.ANCHORED, VesselStatus.APPROACHING]])

    # Berth utilization (simplified)
    berth_filters = []
    if site_id:
        berth_filters.append(Berth.site_id == site_id)

    stmt = select(Berth).where(and_(*berth_filters)) if berth_filters else select(Berth)
    result = await db.execute(stmt)
    all_berths = result.scalars().all()

    occupied_berths = len([b for b in all_berths if b.status == BerthStatus.OCCUPIED])
    total_berths = len(all_berths)
    average_berth_utilization = (occupied_berths / total_berths * 100) if total_berths > 0 else 0

    return PortKPIResponse(
        total_throughput=round(total_throughput, 2),
        daily_average_throughput=round(daily_average_throughput, 2),
        monthly_throughput=round(total_throughput, 2),  # Simplified
        average_loading_rate=round(average_loading_rate, 2),
        average_efficiency=round(average_efficiency, 2),
        average_berth_utilization=round(average_berth_utilization, 2),
        total_operations=total_operations,
        completed_operations=completed_operations,
        active_operations=active_operations,
        delayed_operations=delayed_operations,
        total_vessels=total_vessels,
        vessels_in_port=vessels_in_port,
        vessels_berthed=vessels_berthed,
        vessels_waiting=vessels_waiting,
        total_downtime_hours=round(total_downtime_hours, 2),
        average_downtime_per_operation=round(average_downtime_per_operation, 2),
        period_start=from_date,
        period_end=to_date,
    )


@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    site_id: Optional[UUID] = Query(None),
    from_date: datetime = Query(...),
    to_date: datetime = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Get general performance metrics
    """
    # Build query filters
    filters = [
        LoadingOperation.planned_start >= from_date,
        LoadingOperation.planned_end <= to_date,
        LoadingOperation.status == OperationStatus.COMPLETED,
    ]
    if site_id:
        filters.append(LoadingOperation.site_id == site_id)

    # Get completed operations in period
    stmt = select(LoadingOperation).where(and_(*filters))
    result = await db.execute(stmt)
    operations = result.scalars().all()

    if not operations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed operations found in the specified period"
        )

    # Calculate operational efficiency
    ops_with_efficiency = [op for op in operations if op.efficiency]
    operational_efficiency = sum(op.efficiency for op in ops_with_efficiency) / len(ops_with_efficiency) if ops_with_efficiency else 0

    # Equipment availability (simplified - would come from equipment status tracking)
    equipment_availability = 95.0  # Placeholder

    # Berth utilization
    berth_filters = []
    if site_id:
        berth_filters.append(Berth.site_id == site_id)

    stmt = select(Berth).where(and_(*berth_filters)) if berth_filters else select(Berth)
    result = await db.execute(stmt)
    all_berths = result.scalars().all()

    occupied_berths = len([b for b in all_berths if b.status == BerthStatus.OCCUPIED])
    total_berths = len(all_berths)
    berth_utilization = (occupied_berths / total_berths * 100) if total_berths > 0 else 0

    # Time metrics (simplified)
    turnaround_times = []
    for op in operations:
        if op.actual_start and op.actual_end:
            duration = (op.actual_end - op.actual_start).total_seconds() / 3600
            turnaround_times.append(duration)

    average_turnaround_time = sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0
    average_waiting_time = 2.5  # Placeholder
    average_berthing_time = average_turnaround_time

    # Throughput
    current_throughput_rate = None
    peak_throughput_rate = max([op.actual_rate for op in operations if op.actual_rate], default=0)
    design_throughput_rate = None  # Would come from berth specifications

    # On-time completion
    on_time_ops = len([op for op in operations if not op.is_delayed])
    on_time_completion_rate = (on_time_ops / len(operations) * 100) if operations else 0

    return PerformanceMetricsResponse(
        operational_efficiency=round(operational_efficiency, 2),
        equipment_availability=equipment_availability,
        berth_utilization=round(berth_utilization, 2),
        average_turnaround_time=round(average_turnaround_time, 2),
        average_waiting_time=round(average_waiting_time, 2),
        average_berthing_time=round(average_berthing_time, 2),
        current_throughput_rate=current_throughput_rate,
        peak_throughput_rate=round(peak_throughput_rate, 2),
        design_throughput_rate=design_throughput_rate,
        on_time_completion_rate=round(on_time_completion_rate, 2),
        safety_incidents=0,  # Placeholder
        period_start=from_date,
        period_end=to_date,
        last_updated=datetime.utcnow(),
    )


@router.get("/equipment/{equipment_id}", response_model=EquipmentPerformanceResponse)
async def get_equipment_performance(
    equipment_id: UUID,
    from_date: datetime = Query(...),
    to_date: datetime = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Get performance metrics for specific equipment
    """
    # Get equipment
    stmt = select(PortEquipment).where(PortEquipment.id == equipment_id)
    result = await db.execute(stmt)
    equipment = result.scalar_one_or_none()

    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found"
        )

    # Get operations that used this equipment
    # Note: This is simplified - in production you'd track equipment usage more precisely
    stmt = select(LoadingOperation).where(
        and_(
            LoadingOperation.planned_start >= from_date,
            LoadingOperation.planned_end <= to_date,
            LoadingOperation.status == OperationStatus.COMPLETED,
        )
    )
    result = await db.execute(stmt)
    all_operations = result.scalars().all()

    # Filter operations that used this equipment
    operations = [op for op in all_operations if equipment.code in op.equipment_used]

    # Calculate metrics
    total_throughput = sum(op.total_actual_quantity for op in operations if op.total_actual_quantity)

    total_hours = sum(op.working_hours for op in operations if op.working_hours)
    average_throughput_rate = total_throughput / total_hours if total_hours > 0 else 0

    total_operating_hours = equipment.total_operating_hours
    total_downtime_hours = equipment.total_downtime_hours

    utilization_rate = (total_operating_hours / (total_operating_hours + total_downtime_hours) * 100) if (total_operating_hours + total_downtime_hours) > 0 else 0
    availability = (total_operating_hours / (total_operating_hours + total_downtime_hours) * 100) if (total_operating_hours + total_downtime_hours) > 0 else 0

    # Efficiency
    efficiency = 90.0  # Placeholder - would be calculated from actual vs design performance

    # MTBF and MTTR placeholders
    mtbf = None
    mttr = None

    # Days until maintenance
    days_until_maintenance = None
    if equipment.next_maintenance_date:
        days_until_maintenance = (equipment.next_maintenance_date - datetime.utcnow()).days

    return EquipmentPerformanceResponse(
        equipment_id=equipment.id,
        equipment_code=equipment.code,
        equipment_name=equipment.name,
        equipment_type=equipment.equipment_type.value,
        current_status=equipment.status.value,
        health_score=equipment.health_score,
        failure_probability=equipment.failure_probability,
        utilization_rate=round(utilization_rate, 2),
        efficiency=efficiency,
        availability=round(availability, 2),
        total_throughput=round(total_throughput, 2),
        average_throughput_rate=round(average_throughput_rate, 2),
        current_throughput_rate=equipment.current_throughput,
        total_operating_hours=total_operating_hours,
        total_downtime_hours=total_downtime_hours,
        mtbf=mtbf,
        mttr=mttr,
        last_maintenance_date=equipment.last_maintenance_date,
        next_maintenance_date=equipment.next_maintenance_date,
        days_until_maintenance=days_until_maintenance,
        period_start=from_date,
        period_end=to_date,
    )


@router.get("/commodity-breakdown", response_model=CommodityAnalyticsResponse)
async def get_commodity_breakdown(
    site_id: Optional[UUID] = Query(None),
    from_date: datetime = Query(...),
    to_date: datetime = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Get commodity breakdown analytics
    """
    # Build query filters
    filters = [
        LoadingOperation.planned_start >= from_date,
        LoadingOperation.planned_end <= to_date,
        LoadingOperation.status == OperationStatus.COMPLETED,
    ]
    if site_id:
        filters.append(LoadingOperation.site_id == site_id)

    # Get completed operations
    stmt = select(LoadingOperation).where(and_(*filters))
    result = await db.execute(stmt)
    operations = result.scalars().all()

    # Group by commodity
    commodity_stats = {}

    for op in operations:
        # Get cargos for this operation
        for cargo in op.cargos:
            commodity = cargo.commodity

            if commodity not in commodity_stats:
                commodity_stats[commodity] = {
                    "total_quantity": 0,
                    "total_operations": 0,
                    "rates": []
                }

            commodity_stats[commodity]["total_quantity"] += cargo.actual_quantity or cargo.planned_quantity
            commodity_stats[commodity]["total_operations"] += 1

            if op.actual_rate:
                commodity_stats[commodity]["rates"].append(op.actual_rate)

    # Calculate total for percentages
    total_quantity_all = sum(stats["total_quantity"] for stats in commodity_stats.values())

    # Build breakdown
    breakdown = []
    for commodity, stats in commodity_stats.items():
        average_rate = sum(stats["rates"]) / len(stats["rates"]) if stats["rates"] else 0
        percentage = (stats["total_quantity"] / total_quantity_all * 100) if total_quantity_all > 0 else 0

        breakdown.append(CommodityBreakdownResponse(
            commodity=commodity,
            total_quantity=round(stats["total_quantity"], 2),
            total_operations=stats["total_operations"],
            average_rate=round(average_rate, 2),
            percentage_of_total=round(percentage, 2),
        ))

    # Sort by quantity descending
    breakdown.sort(key=lambda x: x.total_quantity, reverse=True)

    return CommodityAnalyticsResponse(
        total_commodities=len(breakdown),
        breakdown=breakdown,
        period_start=from_date,
        period_end=to_date,
    )


@router.get("/trends", response_model=List[TrendResponse])
async def get_trends(
    site_id: Optional[UUID] = Query(None),
    from_date: datetime = Query(...),
    to_date: datetime = Query(...),
    metrics: str = Query("throughput,efficiency", description="Comma-separated list of metrics"),
    granularity: str = Query("day", description="hour, day, week"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trend data for specified metrics

    Note: This is a simplified implementation for MVP.
    In production, this would query TimeSeries data from InfluxDB.
    """
    # This is a placeholder implementation
    # In production, you would query actual time series data

    metric_list = metrics.split(",")
    trends = []

    for metric_name in metric_list:
        # Generate placeholder trend data
        # In production, fetch from InfluxDB based on granularity

        data_points = []
        current_date = from_date

        while current_date <= to_date:
            # Placeholder values - would come from actual time series data
            value = 1500.0 if metric_name == "throughput" else 85.0

            data_points.append({
                "timestamp": current_date,
                "value": value,
                "label": current_date.strftime("%Y-%m-%d")
            })

            # Increment based on granularity
            if granularity == "hour":
                current_date += timedelta(hours=1)
            elif granularity == "day":
                current_date += timedelta(days=1)
            elif granularity == "week":
                current_date += timedelta(weeks=1)

        values = [dp["value"] for dp in data_points]

        trends.append(TrendResponse(
            metric_name=metric_name,
            metric_unit="tons/hour" if metric_name == "throughput" else "%",
            data_points=data_points,
            min_value=min(values) if values else 0,
            max_value=max(values) if values else 0,
            average_value=sum(values) / len(values) if values else 0,
            current_value=values[-1] if values else None,
            period_start=from_date,
            period_end=to_date,
        ))

    return trends
