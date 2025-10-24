"""
Loading Operation schemas
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from app.port.models.loading_operation import LoadingStatus


class LoadingOperationBase(BaseModel):
    """Base loading operation schema"""
    vessel_id: UUID
    berth_id: Optional[UUID] = None
    commodity_id: Optional[UUID] = None
    route_id: Optional[UUID] = None
    target_quantity: float
    target_loading_rate: Optional[float] = None
    estimated_duration_hours: Optional[float] = None


class LoadingOperationCreate(LoadingOperationBase):
    """Loading operation creation schema"""
    site_id: UUID
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None


class LoadingOperationUpdate(BaseModel):
    """Loading operation update schema"""
    status: Optional[LoadingStatus] = None
    actual_quantity: Optional[float] = None
    actual_loading_rate: Optional[float] = None
    progress_percentage: Optional[float] = None
    current_hold_number: Optional[int] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    cargo_quality_parameters: Optional[Dict[str, Any]] = None
    total_downtime_minutes: Optional[int] = None
    total_energy_kwh: Optional[float] = None
    notes: Optional[str] = None


class LoadingOperationResponse(LoadingOperationBase):
    """Loading operation response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    site_id: UUID
    operation_number: str
    status: LoadingStatus
    actual_quantity: float = 0.0
    actual_loading_rate: Optional[float] = None
    actual_duration_minutes: Optional[int] = None
    progress_percentage: float = 0.0
    current_hold_number: Optional[int] = None
    total_holds: Optional[int] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    shiploader_ids: List[str] = []
    conveyor_ids: List[str] = []
    cargo_quality_parameters: Dict[str, Any] = {}
    total_downtime_minutes: int = 0
    weather_delay_minutes: int = 0
    equipment_failure_minutes: int = 0
    efficiency_percentage: Optional[float] = None
    productivity_tons_per_hour: Optional[float] = None
    total_energy_kwh: Optional[float] = None
    energy_per_ton: Optional[float] = None
    created_at: datetime
    updated_at: datetime
