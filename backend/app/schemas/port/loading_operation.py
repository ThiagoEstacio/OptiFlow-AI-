"""
Loading Operation schemas for API request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from app.models.port.loading_operation import OperationType, OperationStatus, CommodityType


# ===== Cargo Schemas =====

class CargoBase(BaseModel):
    """Base cargo schema"""
    commodity: CommodityType = Field(..., description="Type of commodity")
    commodity_grade: Optional[str] = Field(None, max_length=100, description="Grade/quality")
    description: Optional[str] = None

    planned_quantity: float = Field(..., gt=0, description="Planned quantity (tons)")
    unit: str = Field(default="tons", max_length=20)

    origin: Optional[str] = Field(None, max_length=255)
    destination: Optional[str] = Field(None, max_length=255)
    shipper: Optional[str] = Field(None, max_length=255)
    consignee: Optional[str] = Field(None, max_length=255)

    specifications: Dict[str, Any] = Field(default_factory=dict, description="Cargo specifications")
    bl_number: Optional[str] = Field(None, max_length=100, description="Bill of lading number")
    customs_reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class CargoCreate(CargoBase):
    """Schema for creating cargo"""
    pass


class CargoUpdate(BaseModel):
    """Schema for updating cargo"""
    commodity: Optional[CommodityType] = None
    commodity_grade: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None

    planned_quantity: Optional[float] = Field(None, gt=0)
    actual_quantity: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=20)

    origin: Optional[str] = Field(None, max_length=255)
    destination: Optional[str] = Field(None, max_length=255)
    shipper: Optional[str] = Field(None, max_length=255)
    consignee: Optional[str] = Field(None, max_length=255)

    specifications: Optional[Dict[str, Any]] = None
    bl_number: Optional[str] = Field(None, max_length=100)
    customs_reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class CargoResponse(CargoBase):
    """Schema for cargo response"""
    id: UUID
    loading_operation_id: UUID
    actual_quantity: Optional[float] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== Operation Event Schemas =====

class OperationEventBase(BaseModel):
    """Base operation event schema"""
    event_type: str = Field(..., max_length=100, description="Type of event")
    event_time: datetime = Field(..., description="When the event occurred")
    description: str = Field(..., min_length=1, description="Event description")
    event_data: Dict[str, Any] = Field(default_factory=dict)
    user_name: Optional[str] = Field(None, max_length=255)


class OperationEventCreate(OperationEventBase):
    """Schema for creating an operation event"""
    pass


class OperationEventResponse(OperationEventBase):
    """Schema for operation event response"""
    id: UUID
    loading_operation_id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== Loading Operation Schemas =====

class LoadingOperationBase(BaseModel):
    """Base loading operation schema"""
    operation_type: OperationType = Field(..., description="Type of operation (loading/unloading)")
    operation_number: str = Field(..., min_length=1, max_length=100, description="Unique operation number")

    planned_start: datetime = Field(..., description="Planned start time")
    planned_end: datetime = Field(..., description="Planned end time")
    planned_rate: Optional[float] = Field(None, ge=0, description="Planned loading rate (tons/hour)")
    total_planned_quantity: float = Field(..., gt=0, description="Total planned quantity (tons)")

    equipment_used: List[str] = Field(default_factory=list, description="Equipment codes used")

    notes: Optional[str] = None
    weather_conditions: Optional[str] = Field(None, max_length=255)
    shift_supervisor: Optional[str] = Field(None, max_length=255)

    is_active: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)


class LoadingOperationCreate(LoadingOperationBase):
    """Schema for creating a loading operation"""
    site_id: UUID
    vessel_id: UUID
    berth_id: UUID
    status: OperationStatus = Field(default=OperationStatus.PLANNED, description="Initial status")

    # Cargos to be loaded/unloaded
    cargos: List[CargoCreate] = Field(default_factory=list, description="List of cargos")


class LoadingOperationUpdate(BaseModel):
    """Schema for updating a loading operation"""
    operation_type: Optional[OperationType] = None
    status: Optional[OperationStatus] = None

    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None

    planned_rate: Optional[float] = Field(None, ge=0)
    actual_rate: Optional[float] = Field(None, ge=0)
    current_rate: Optional[float] = Field(None, ge=0)

    total_planned_quantity: Optional[float] = Field(None, gt=0)
    total_actual_quantity: Optional[float] = Field(None, ge=0)

    efficiency: Optional[float] = Field(None, ge=0, le=100)
    downtime_hours: Optional[float] = Field(None, ge=0)
    working_hours: Optional[float] = Field(None, ge=0)

    is_delayed: Optional[bool] = None
    delay_reason: Optional[str] = None
    delay_minutes: Optional[float] = Field(None, ge=0)

    equipment_used: Optional[List[str]] = None

    notes: Optional[str] = None
    weather_conditions: Optional[str] = Field(None, max_length=255)
    shift_supervisor: Optional[str] = Field(None, max_length=255)

    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class LoadingOperationResponse(LoadingOperationBase):
    """Schema for loading operation response"""
    id: UUID
    site_id: UUID
    vessel_id: UUID
    berth_id: UUID
    status: OperationStatus

    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    actual_rate: Optional[float] = None
    current_rate: Optional[float] = None
    total_actual_quantity: float = 0.0

    efficiency: Optional[float] = None
    downtime_hours: float = 0.0
    working_hours: float = 0.0

    is_delayed: bool = False
    delay_reason: Optional[str] = None
    delay_minutes: float = 0.0

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoadingOperationDetailResponse(LoadingOperationResponse):
    """Detailed loading operation response with related data"""
    vessel_name: Optional[str] = None
    vessel_imo: Optional[str] = None
    berth_name: Optional[str] = None
    berth_code: Optional[str] = None

    cargos: List[CargoResponse] = Field(default_factory=list)
    events: List[OperationEventResponse] = Field(default_factory=list)

    # Calculated fields
    progress_percentage: float = Field(default=0.0, ge=0, le=100, description="Progress percentage")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    time_remaining_hours: Optional[float] = Field(None, description="Estimated hours remaining")


class LoadingOperationProgressResponse(BaseModel):
    """Real-time progress response"""
    operation_id: UUID
    operation_number: str
    status: OperationStatus

    # Progress
    progress_percentage: float = Field(..., ge=0, le=100)
    total_planned_quantity: float
    total_actual_quantity: float
    remaining_quantity: float

    # Rates
    current_rate: Optional[float] = Field(None, description="Current rate (tons/hour)")
    average_rate: Optional[float] = Field(None, description="Average rate (tons/hour)")
    planned_rate: Optional[float] = None

    # Time
    actual_start: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    time_elapsed_hours: Optional[float] = None
    time_remaining_hours: Optional[float] = None

    # Performance
    efficiency: Optional[float] = Field(None, ge=0, le=100, description="Efficiency (%)")
    downtime_hours: float = 0.0
    is_delayed: bool = False
    delay_minutes: float = 0.0

    # Real-time metrics (would come from TimeSeries data)
    equipment_status: Dict[str, Any] = Field(default_factory=dict)


class LoadingOperationListResponse(BaseModel):
    """Response for listing loading operations with pagination"""
    total: int
    page: int
    page_size: int
    operations: List[LoadingOperationResponse]


class LoadingOperationSearchParams(BaseModel):
    """Search parameters for loading operations"""
    vessel_id: Optional[UUID] = None
    berth_id: Optional[UUID] = None
    status: Optional[OperationStatus] = None
    operation_type: Optional[OperationType] = None
    from_date: Optional[datetime] = Field(None, description="Filter from planned_start")
    to_date: Optional[datetime] = Field(None, description="Filter to planned_end")
    commodity: Optional[CommodityType] = None
    delayed_only: Optional[bool] = Field(None, description="Show only delayed operations")


# ===== Operation Control Schemas =====

class OperationStartRequest(BaseModel):
    """Request to start an operation"""
    actual_start: Optional[datetime] = Field(None, description="Actual start time (default: now)")
    notes: Optional[str] = None


class OperationPauseRequest(BaseModel):
    """Request to pause an operation"""
    reason: str = Field(..., min_length=1, description="Reason for pause")
    notes: Optional[str] = None


class OperationResumeRequest(BaseModel):
    """Request to resume a paused operation"""
    notes: Optional[str] = None


class OperationCompleteRequest(BaseModel):
    """Request to complete an operation"""
    actual_end: Optional[datetime] = Field(None, description="Actual end time (default: now)")
    total_actual_quantity: Optional[float] = Field(None, gt=0, description="Total quantity loaded/unloaded")
    notes: Optional[str] = None


class OperationDelayRequest(BaseModel):
    """Request to report a delay"""
    delay_reason: str = Field(..., min_length=1, description="Reason for delay")
    delay_minutes: float = Field(..., gt=0, description="Delay duration (minutes)")
    notes: Optional[str] = None
