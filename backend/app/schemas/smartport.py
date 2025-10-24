"""
SmartPort - Pydantic Schemas

Request and response schemas for SmartPort API endpoints.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator

from app.models.berth import BerthType, BerthStatus
from app.models.vessel import VesselType, VesselStatus
from app.models.port_operation import OperationType, OperationStatus, CargoType


# ============================================================================
# Berth Schemas
# ============================================================================

class BerthBase(BaseModel):
    """Base berth schema with common fields"""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    berth_type: BerthType
    status: BerthStatus = BerthStatus.AVAILABLE
    max_loa: float = Field(..., gt=0, description="Maximum Length Overall in meters")
    max_beam: float = Field(..., gt=0, description="Maximum beam width in meters")
    max_draft: float = Field(..., gt=0, description="Maximum draft depth in meters")
    max_displacement: Optional[float] = Field(None, gt=0)
    max_crane_capacity: Optional[float] = Field(None, gt=0)
    number_of_cranes: int = Field(0, ge=0)
    has_shore_power: bool = False
    has_fresh_water: bool = False
    has_bunker_facility: bool = False
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    description: Optional[str] = Field(None, max_length=500)


class BerthCreate(BerthBase):
    """Schema for creating a new berth"""
    pass


class BerthUpdate(BaseModel):
    """Schema for updating a berth"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    berth_type: Optional[BerthType] = None
    status: Optional[BerthStatus] = None
    max_loa: Optional[float] = Field(None, gt=0)
    max_beam: Optional[float] = Field(None, gt=0)
    max_draft: Optional[float] = Field(None, gt=0)
    max_displacement: Optional[float] = Field(None, gt=0)
    max_crane_capacity: Optional[float] = Field(None, gt=0)
    number_of_cranes: Optional[int] = Field(None, ge=0)
    has_shore_power: Optional[bool] = None
    has_fresh_water: Optional[bool] = None
    has_bunker_facility: Optional[bool] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class BerthResponse(BerthBase):
    """Schema for berth response"""
    id: UUID
    current_vessel_id: Optional[UUID] = None
    occupation_start: Optional[datetime] = None
    estimated_departure: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BerthDetailResponse(BerthResponse):
    """Detailed berth response with relationships"""
    current_vessel: Optional['VesselResponse'] = None
    occupancy_duration_hours: Optional[float] = None
    is_available: bool

    class Config:
        from_attributes = True


# ============================================================================
# Vessel Schemas
# ============================================================================

class VesselBase(BaseModel):
    """Base vessel schema with common fields"""
    name: str = Field(..., min_length=1, max_length=200)
    imo: str = Field(..., min_length=7, max_length=20, description="IMO number")
    mmsi: Optional[str] = Field(None, max_length=20)
    call_sign: Optional[str] = Field(None, max_length=20)
    flag: Optional[str] = Field(None, max_length=100)
    vessel_type: VesselType
    status: VesselStatus = VesselStatus.APPROACHING
    loa: float = Field(..., gt=0, description="Length Overall in meters")
    beam: float = Field(..., gt=0, description="Beam width in meters")
    draft: float = Field(..., gt=0, description="Draft depth in meters")
    max_draft: Optional[float] = Field(None, gt=0)
    gross_tonnage: Optional[float] = Field(None, gt=0)
    deadweight_tonnage: Optional[float] = Field(None, gt=0)
    capacity_teu: Optional[int] = Field(None, gt=0)
    capacity_passengers: Optional[int] = Field(None, gt=0)
    capacity_vehicles: Optional[int] = Field(None, gt=0)
    capacity_cubic_meters: Optional[float] = Field(None, gt=0)
    eta: Optional[datetime] = None
    etd: Optional[datetime] = None
    origin_port: Optional[str] = Field(None, max_length=200)
    destination_port: Optional[str] = Field(None, max_length=200)
    voyage_number: Optional[str] = Field(None, max_length=50)
    owner: Optional[str] = Field(None, max_length=200)
    operator: Optional[str] = Field(None, max_length=200)
    agent: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=1000)

    @validator('imo')
    def validate_imo(cls, v):
        """Validate IMO number format"""
        if v and not v.startswith('IMO'):
            return f'IMO{v}'
        return v


class VesselCreate(VesselBase):
    """Schema for creating a new vessel"""
    pass


class VesselUpdate(BaseModel):
    """Schema for updating a vessel"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    imo: Optional[str] = Field(None, min_length=7, max_length=20)
    mmsi: Optional[str] = Field(None, max_length=20)
    call_sign: Optional[str] = Field(None, max_length=20)
    flag: Optional[str] = Field(None, max_length=100)
    vessel_type: Optional[VesselType] = None
    status: Optional[VesselStatus] = None
    loa: Optional[float] = Field(None, gt=0)
    beam: Optional[float] = Field(None, gt=0)
    draft: Optional[float] = Field(None, gt=0)
    max_draft: Optional[float] = Field(None, gt=0)
    gross_tonnage: Optional[float] = Field(None, gt=0)
    deadweight_tonnage: Optional[float] = Field(None, gt=0)
    capacity_teu: Optional[int] = Field(None, gt=0)
    capacity_passengers: Optional[int] = Field(None, gt=0)
    capacity_vehicles: Optional[int] = Field(None, gt=0)
    capacity_cubic_meters: Optional[float] = Field(None, gt=0)
    eta: Optional[datetime] = None
    ata: Optional[datetime] = None
    etd: Optional[datetime] = None
    atd: Optional[datetime] = None
    last_latitude: Optional[float] = Field(None, ge=-90, le=90)
    last_longitude: Optional[float] = Field(None, ge=-180, le=180)
    heading: Optional[float] = Field(None, ge=0, le=360)
    speed_knots: Optional[float] = Field(None, ge=0)
    origin_port: Optional[str] = Field(None, max_length=200)
    destination_port: Optional[str] = Field(None, max_length=200)
    voyage_number: Optional[str] = Field(None, max_length=50)
    owner: Optional[str] = Field(None, max_length=200)
    operator: Optional[str] = Field(None, max_length=200)
    agent: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=1000)


class VesselPositionUpdate(BaseModel):
    """Schema for updating vessel position"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    heading: Optional[float] = Field(None, ge=0, le=360)
    speed_knots: Optional[float] = Field(None, ge=0)


class VesselResponse(VesselBase):
    """Schema for vessel response"""
    id: UUID
    ata: Optional[datetime] = None
    atd: Optional[datetime] = None
    last_latitude: Optional[float] = None
    last_longitude: Optional[float] = None
    last_position_update: Optional[datetime] = None
    heading: Optional[float] = None
    speed_knots: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VesselDetailResponse(VesselResponse):
    """Detailed vessel response with calculated fields"""
    is_berthed: bool
    port_time_hours: Optional[float] = None
    is_delayed: bool

    class Config:
        from_attributes = True


# ============================================================================
# Port Operation Schemas
# ============================================================================

class PortOperationBase(BaseModel):
    """Base port operation schema"""
    vessel_id: UUID
    berth_id: UUID
    operation_type: OperationType
    status: OperationStatus = OperationStatus.SCHEDULED
    cargo_type: Optional[CargoType] = None
    containers_planned: Optional[int] = Field(None, ge=0)
    tonnage_planned: Optional[float] = Field(None, ge=0)
    cubic_meters_planned: Optional[float] = Field(None, ge=0)
    scheduled_start: datetime
    estimated_end: datetime
    cranes_assigned: int = Field(0, ge=0)
    workforce_assigned: int = Field(0, ge=0)
    equipment_used: Optional[Dict[str, Any]] = None
    estimated_cost: Optional[float] = Field(None, ge=0)
    currency: str = Field("USD", max_length=3)
    priority: int = Field(3, ge=1, le=5)
    cargo_description: Optional[str] = Field(None, max_length=500)
    special_requirements: Optional[str] = None
    notes: Optional[str] = None

    @validator('estimated_end')
    def validate_end_after_start(cls, v, values):
        """Ensure estimated_end is after scheduled_start"""
        if 'scheduled_start' in values and v <= values['scheduled_start']:
            raise ValueError('estimated_end must be after scheduled_start')
        return v


class PortOperationCreate(PortOperationBase):
    """Schema for creating a new port operation"""
    pass


class PortOperationUpdate(BaseModel):
    """Schema for updating a port operation"""
    vessel_id: Optional[UUID] = None
    berth_id: Optional[UUID] = None
    operation_type: Optional[OperationType] = None
    status: Optional[OperationStatus] = None
    cargo_type: Optional[CargoType] = None
    containers_planned: Optional[int] = Field(None, ge=0)
    containers_completed: Optional[int] = Field(None, ge=0)
    tonnage_planned: Optional[float] = Field(None, ge=0)
    tonnage_completed: Optional[float] = Field(None, ge=0)
    cubic_meters_planned: Optional[float] = Field(None, ge=0)
    cubic_meters_completed: Optional[float] = Field(None, ge=0)
    scheduled_start: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    estimated_end: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    cranes_assigned: Optional[int] = Field(None, ge=0)
    workforce_assigned: Optional[int] = Field(None, ge=0)
    equipment_used: Optional[Dict[str, Any]] = None
    productivity_rate: Optional[float] = Field(None, ge=0)
    downtime_hours: Optional[float] = Field(None, ge=0)
    efficiency_percentage: Optional[float] = Field(None, ge=0, le=100)
    estimated_cost: Optional[float] = Field(None, ge=0)
    actual_cost: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    priority: Optional[int] = Field(None, ge=1, le=5)
    weather_delay: Optional[bool] = None
    equipment_delay: Optional[bool] = None
    labor_delay: Optional[bool] = None
    cargo_description: Optional[str] = Field(None, max_length=500)
    special_requirements: Optional[str] = None
    notes: Optional[str] = None


class PortOperationProgressUpdate(BaseModel):
    """Schema for updating operation progress"""
    containers_completed: Optional[int] = Field(None, ge=0)
    tonnage_completed: Optional[float] = Field(None, ge=0)
    cubic_meters_completed: Optional[float] = Field(None, ge=0)


class PortOperationResponse(PortOperationBase):
    """Schema for port operation response"""
    id: UUID
    containers_completed: int
    tonnage_completed: float
    cubic_meters_completed: float
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    productivity_rate: Optional[float] = None
    downtime_hours: float
    efficiency_percentage: Optional[float] = None
    actual_cost: Optional[float] = None
    weather_delay: bool
    equipment_delay: bool
    labor_delay: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class PortOperationDetailResponse(PortOperationResponse):
    """Detailed port operation response with calculations"""
    vessel: Optional[VesselResponse] = None
    berth: Optional[BerthResponse] = None
    is_active: bool
    completion_percentage: float
    duration_hours: Optional[float] = None
    estimated_duration_hours: float
    is_delayed: bool
    delay_hours: Optional[float] = None

    class Config:
        from_attributes = True


# ============================================================================
# Dashboard & Analytics Schemas
# ============================================================================

class PortKPIs(BaseModel):
    """Port-wide KPIs"""
    total_berths: int
    available_berths: int
    occupied_berths: int
    berth_occupancy_rate: float = Field(..., ge=0, le=100)
    total_vessels: int
    berthed_vessels: int
    approaching_vessels: int
    active_operations: int
    completed_operations_today: int
    containers_handled_today: int
    average_berthing_time_hours: float
    operational_efficiency: float = Field(..., ge=0, le=100)


class BerthOccupancyStats(BaseModel):
    """Berth occupancy statistics"""
    berth_id: UUID
    berth_name: str
    berth_code: str
    total_hours: float
    occupied_hours: float
    occupancy_rate: float = Field(..., ge=0, le=100)
    vessel_count: int


class OperationPerformanceStats(BaseModel):
    """Operation performance statistics"""
    total_operations: int
    completed_operations: int
    in_progress_operations: int
    delayed_operations: int
    average_duration_hours: float
    average_efficiency: float = Field(..., ge=0, le=100)
    total_containers: int
    total_tonnage: float


# Update forward references
BerthDetailResponse.model_rebuild()
VesselDetailResponse.model_rebuild()
PortOperationDetailResponse.model_rebuild()
