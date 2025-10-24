"""
Vessel schemas
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.port.models.vessel import VesselType, VesselStatus


class VesselBase(BaseModel):
    """Base vessel schema"""
    name: str
    imo_number: Optional[str] = None
    mmsi_number: Optional[str] = None
    call_sign: Optional[str] = None
    flag_country: Optional[str] = None
    vessel_type: VesselType
    length_overall: Optional[float] = None
    beam: Optional[float] = None
    draft: Optional[float] = None
    deadweight_tonnage: Optional[int] = None
    gross_tonnage: Optional[int] = None
    cargo_type: Optional[str] = None
    cargo_quantity_planned: Optional[float] = None


class VesselCreate(VesselBase):
    """Vessel creation schema"""
    site_id: UUID
    eta: Optional[datetime] = None


class VesselUpdate(BaseModel):
    """Vessel update schema"""
    name: Optional[str] = None
    status: Optional[VesselStatus] = None
    current_berth_id: Optional[UUID] = None
    cargo_quantity_actual: Optional[float] = None
    ata: Optional[datetime] = None
    atd: Optional[datetime] = None
    berthing_time: Optional[datetime] = None
    unberthing_time: Optional[datetime] = None
    loading_start_time: Optional[datetime] = None
    loading_end_time: Optional[datetime] = None
    notes: Optional[str] = None


class VesselResponse(VesselBase):
    """Vessel response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    site_id: UUID
    status: VesselStatus
    current_berth_id: Optional[UUID] = None
    cargo_quantity_actual: Optional[float] = None
    eta: Optional[datetime] = None
    ata: Optional[datetime] = None
    etd: Optional[datetime] = None
    atd: Optional[datetime] = None
    berthing_time: Optional[datetime] = None
    unberthing_time: Optional[datetime] = None
    loading_start_time: Optional[datetime] = None
    loading_end_time: Optional[datetime] = None
    loading_duration_minutes: Optional[int] = None
    average_loading_rate: Optional[float] = None
    demurrage_hours: float = 0.0
    weather_delay_hours: float = 0.0
    equipment_delay_hours: float = 0.0
    created_at: datetime
    updated_at: datetime
