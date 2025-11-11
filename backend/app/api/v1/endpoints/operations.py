"""
Operational Data API Endpoints

Provides APIs for port terminal operations:
- Truck entries (weighbridge)
- Ship loading operations
- Daily operational summaries
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field
import logging

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.operational_data import TruckEntry, ShipLoading, DailyOperations
from app.services.cache_service import cached

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic models for request/response


class TruckEntryCreate(BaseModel):
    truck_id: str = Field(..., max_length=50, description="License plate")
    driver_name: Optional[str] = Field(None, max_length=200)
    company: Optional[str] = Field(None, max_length=200)
    gross_weight: float = Field(..., gt=0, description="Gross weight in kg")
    tare_weight: float = Field(..., gt=0, description="Tare weight in kg")
    product_type: str = Field(..., max_length=100, description="Product type (corn, soy, wheat)")
    product_quality: Optional[str] = Field(None, max_length=50)
    moisture_percent: Optional[float] = Field(None, ge=0, le=100)
    impurity_percent: Optional[float] = Field(None, ge=0, le=100)
    origin_farm: Optional[str] = Field(None, max_length=200)
    origin_city: Optional[str] = Field(None, max_length=200)
    origin_state: Optional[str] = Field(None, max_length=50)
    entry_time: datetime
    site_id: int
    notes: Optional[str] = None


class TruckEntryUpdate(BaseModel):
    status: Optional[str] = None
    gross_weight_time: Optional[datetime] = None
    tare_weight_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    notes: Optional[str] = None


class ShipLoadingCreate(BaseModel):
    ship_name: str = Field(..., max_length=200)
    ship_imo: Optional[str] = Field(None, max_length=20)
    ship_flag: Optional[str] = Field(None, max_length=50)
    ship_dwt: Optional[float] = Field(None, gt=0)
    berth_number: int = Field(..., ge=1)
    product_type: str = Field(..., max_length=100)
    target_tonnage: float = Field(..., gt=0)
    arrival_time: Optional[datetime] = None
    buyer_company: Optional[str] = Field(None, max_length=200)
    destination_port: Optional[str] = Field(None, max_length=200)
    destination_country: Optional[str] = Field(None, max_length=100)
    contract_number: Optional[str] = Field(None, max_length=100)
    site_id: int
    notes: Optional[str] = None


class ShipLoadingUpdate(BaseModel):
    status: Optional[str] = None
    loaded_tonnage: Optional[float] = None
    loading_rate_avg: Optional[float] = None
    loading_rate_peak: Optional[float] = None
    downtime_hours: Optional[float] = None
    berthing_time: Optional[datetime] = None
    loading_start_time: Optional[datetime] = None
    loading_end_time: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    average_moisture: Optional[float] = None
    average_impurity: Optional[float] = None
    quality_approved: Optional[bool] = None
    quality_notes: Optional[str] = None
    weather_conditions: Optional[str] = None
    incidents: Optional[str] = None
    notes: Optional[str] = None


class DailyOperationsCreate(BaseModel):
    operation_date: date
    trucks_received: int = 0
    trucks_total_tonnage: float = 0.0
    trucks_avg_wait_time: Optional[float] = None
    ships_in_port: int = 0
    ships_loading: int = 0
    ships_departed: int = 0
    ships_total_tonnage: float = 0.0
    total_tonnage_loaded: float = 0.0
    avg_loading_rate: Optional[float] = None
    operating_hours: float = 0.0
    downtime_hours: float = 0.0
    shiploaders_available: Optional[int] = None
    shiploaders_operating: Optional[int] = None
    conveyors_available: Optional[int] = None
    conveyors_operating: Optional[int] = None
    corn_tonnage: float = 0.0
    soy_tonnage: float = 0.0
    wheat_tonnage: float = 0.0
    other_tonnage: float = 0.0
    weather_condition: Optional[str] = None
    avg_temperature: Optional[float] = None
    rainfall_mm: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    weather_delays_hours: float = 0.0
    incidents_count: int = 0
    incidents_description: Optional[str] = None
    maintenance_hours: float = 0.0
    operational_efficiency: Optional[float] = None
    equipment_utilization: Optional[float] = None
    site_id: int
    notes: Optional[str] = None


# Truck Entry Endpoints


@router.post("/trucks", response_model=Dict[str, Any])
async def create_truck_entry(
    truck_data: TruckEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new truck entry."""
    try:
        # Calculate net weight
        net_weight = truck_data.gross_weight - truck_data.tare_weight

        # Create truck entry
        truck_entry = TruckEntry(
            **truck_data.dict(),
            net_weight=net_weight,
            created_by=current_user.id
        )

        db.add(truck_entry)
        await db.commit()
        await db.refresh(truck_entry)

        logger.info(f"Created truck entry {truck_entry.id} for truck {truck_entry.truck_id}")

        return truck_entry.to_dict()

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating truck entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trucks", response_model=Dict[str, Any])
async def get_truck_entries(
    site_id: Optional[int] = None,
    status: Optional[str] = None,
    product_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get list of truck entries with filtering."""
    try:
        query = select(TruckEntry)

        # Apply filters
        if site_id:
            query = query.where(TruckEntry.site_id == site_id)
        if status:
            query = query.where(TruckEntry.status == status)
        if product_type:
            query = query.where(TruckEntry.product_type == product_type)
        if start_date:
            query = query.where(TruckEntry.entry_time >= start_date)
        if end_date:
            query = query.where(TruckEntry.entry_time <= end_date)

        # Order by entry time descending
        query = query.order_by(TruckEntry.entry_time.desc())

        # Count total
        count_query = select(func.count()).select_from(query.alias())
        total = (await db.execute(count_query)).scalar()

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        entries = result.scalars().all()

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "entries": [entry.to_dict() for entry in entries]
        }

    except Exception as e:
        logger.error(f"Error getting truck entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trucks/{truck_entry_id}", response_model=Dict[str, Any])
async def get_truck_entry(
    truck_entry_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get a specific truck entry."""
    result = await db.execute(
        select(TruckEntry).where(TruckEntry.id == truck_entry_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Truck entry not found")

    return entry.to_dict()


@router.put("/trucks/{truck_entry_id}", response_model=Dict[str, Any])
async def update_truck_entry(
    truck_entry_id: int,
    update_data: TruckEntryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update a truck entry."""
    try:
        result = await db.execute(
            select(TruckEntry).where(TruckEntry.id == truck_entry_id)
        )
        entry = result.scalar_one_or_none()

        if not entry:
            raise HTTPException(status_code=404, detail="Truck entry not found")

        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(entry, field, value)

        await db.commit()
        await db.refresh(entry)

        logger.info(f"Updated truck entry {truck_entry_id}")

        return entry.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating truck entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Ship Loading Endpoints


@router.post("/ships", response_model=Dict[str, Any])
async def create_ship_loading(
    ship_data: ShipLoadingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new ship loading operation."""
    try:
        ship_loading = ShipLoading(
            **ship_data.dict(),
            created_by=current_user.id
        )

        db.add(ship_loading)
        await db.commit()
        await db.refresh(ship_loading)

        logger.info(f"Created ship loading {ship_loading.id} for {ship_loading.ship_name}")

        return ship_loading.to_dict()

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating ship loading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ships", response_model=Dict[str, Any])
async def get_ship_loadings(
    site_id: Optional[int] = None,
    status: Optional[str] = None,
    berth_number: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get list of ship loading operations with filtering."""
    try:
        query = select(ShipLoading)

        # Apply filters
        if site_id:
            query = query.where(ShipLoading.site_id == site_id)
        if status:
            query = query.where(ShipLoading.status == status)
        if berth_number:
            query = query.where(ShipLoading.berth_number == berth_number)
        if start_date:
            query = query.where(ShipLoading.arrival_time >= start_date)
        if end_date:
            query = query.where(ShipLoading.arrival_time <= end_date)

        # Order by arrival time descending
        query = query.order_by(ShipLoading.arrival_time.desc())

        # Count total
        count_query = select(func.count()).select_from(query.alias())
        total = (await db.execute(count_query)).scalar()

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        loadings = result.scalars().all()

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "loadings": [loading.to_dict() for loading in loadings]
        }

    except Exception as e:
        logger.error(f"Error getting ship loadings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ships/{ship_loading_id}", response_model=Dict[str, Any])
async def get_ship_loading(
    ship_loading_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get a specific ship loading operation."""
    result = await db.execute(
        select(ShipLoading).where(ShipLoading.id == ship_loading_id)
    )
    loading = result.scalar_one_or_none()

    if not loading:
        raise HTTPException(status_code=404, detail="Ship loading not found")

    return loading.to_dict()


@router.put("/ships/{ship_loading_id}", response_model=Dict[str, Any])
async def update_ship_loading(
    ship_loading_id: int,
    update_data: ShipLoadingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update a ship loading operation."""
    try:
        result = await db.execute(
            select(ShipLoading).where(ShipLoading.id == ship_loading_id)
        )
        loading = result.scalar_one_or_none()

        if not loading:
            raise HTTPException(status_code=404, detail="Ship loading not found")

        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(loading, field, value)

        await db.commit()
        await db.refresh(loading)

        logger.info(f"Updated ship loading {ship_loading_id}")

        return loading.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating ship loading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Daily Operations Endpoints


@router.post("/daily", response_model=Dict[str, Any])
async def create_daily_operations(
    daily_data: DailyOperationsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create or update daily operations summary."""
    try:
        # Check if entry already exists for this date and site
        result = await db.execute(
            select(DailyOperations).where(
                and_(
                    DailyOperations.operation_date == daily_data.operation_date,
                    DailyOperations.site_id == daily_data.site_id
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            for field, value in daily_data.dict(exclude_unset=True).items():
                setattr(existing, field, value)
            await db.commit()
            await db.refresh(existing)
            logger.info(f"Updated daily operations for {daily_data.operation_date}")
            return existing.to_dict()
        else:
            # Create new
            daily_ops = DailyOperations(
                **daily_data.dict(),
                created_by=current_user.id
            )
            db.add(daily_ops)
            await db.commit()
            await db.refresh(daily_ops)
            logger.info(f"Created daily operations for {daily_data.operation_date}")
            return daily_ops.to_dict()

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating daily operations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily", response_model=Dict[str, Any])
@cached(ttl=300, key_prefix="operations_daily")
async def get_daily_operations(
    site_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get daily operations summaries with filtering."""
    try:
        query = select(DailyOperations)

        # Apply filters
        if site_id:
            query = query.where(DailyOperations.site_id == site_id)
        if start_date:
            query = query.where(DailyOperations.operation_date >= start_date)
        if end_date:
            query = query.where(DailyOperations.operation_date <= end_date)

        # Order by date descending
        query = query.order_by(DailyOperations.operation_date.desc())

        # Count total
        count_query = select(func.count()).select_from(query.alias())
        total = (await db.execute(count_query)).scalar()

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        daily_ops = result.scalars().all()

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "operations": [ops.to_dict() for ops in daily_ops]
        }

    except Exception as e:
        logger.error(f"Error getting daily operations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily/{operation_date}", response_model=Dict[str, Any])
async def get_daily_operation(
    operation_date: date,
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get daily operations for a specific date."""
    result = await db.execute(
        select(DailyOperations).where(
            and_(
                DailyOperations.operation_date == operation_date,
                DailyOperations.site_id == site_id
            )
        )
    )
    daily_ops = result.scalar_one_or_none()

    if not daily_ops:
        raise HTTPException(status_code=404, detail="Daily operations not found")

    return daily_ops.to_dict()


# Statistics Endpoints


@router.get("/statistics/trucks", response_model=Dict[str, Any])
async def get_truck_statistics(
    site_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get truck statistics for a time period."""
    try:
        query = select(
            func.count(TruckEntry.id).label('total_trucks'),
            func.sum(TruckEntry.net_weight).label('total_tonnage'),
            func.avg(TruckEntry.net_weight).label('avg_tonnage'),
            TruckEntry.product_type,
        ).where(TruckEntry.site_id == site_id)

        if start_date:
            query = query.where(TruckEntry.entry_time >= start_date)
        if end_date:
            query = query.where(TruckEntry.entry_time <= end_date)

        query = query.group_by(TruckEntry.product_type)

        result = await db.execute(query)
        stats = result.all()

        return {
            "by_product": [
                {
                    "product_type": row.product_type,
                    "total_trucks": row.total_trucks,
                    "total_tonnage": float(row.total_tonnage) if row.total_tonnage else 0,
                    "avg_tonnage": float(row.avg_tonnage) if row.avg_tonnage else 0,
                }
                for row in stats
            ]
        }

    except Exception as e:
        logger.error(f"Error getting truck statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/ships", response_model=Dict[str, Any])
async def get_ship_statistics(
    site_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get ship loading statistics for a time period."""
    try:
        query = select(
            func.count(ShipLoading.id).label('total_ships'),
            func.sum(ShipLoading.loaded_tonnage).label('total_tonnage'),
            func.avg(ShipLoading.loading_rate_avg).label('avg_loading_rate'),
            func.avg(ShipLoading.downtime_hours).label('avg_downtime'),
        ).where(ShipLoading.site_id == site_id)

        if start_date:
            query = query.where(ShipLoading.arrival_time >= start_date)
        if end_date:
            query = query.where(ShipLoading.arrival_time <= end_date)

        result = await db.execute(query)
        row = result.first()

        return {
            "total_ships": row.total_ships or 0,
            "total_tonnage": float(row.total_tonnage) if row.total_tonnage else 0,
            "avg_loading_rate": float(row.avg_loading_rate) if row.avg_loading_rate else 0,
            "avg_downtime": float(row.avg_downtime) if row.avg_downtime else 0,
        }

    except Exception as e:
        logger.error(f"Error getting ship statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
