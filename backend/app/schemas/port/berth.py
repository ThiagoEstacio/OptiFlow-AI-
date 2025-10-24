"""
Berth schemas for API request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from app.models.port.berth import BerthType, BerthStatus


class BerthBase(BaseModel):
    """Base berth schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Berth name")
    code: str = Field(..., min_length=1, max_length=50, description="Unique berth code")
    description: Optional[str] = Field(None, description="Berth description")
    berth_type: BerthType = Field(..., description="Type of berth/terminal")

    # Physical specifications
    length: Optional[float] = Field(None, ge=0, description="Berth length (meters)")
    depth: Optional[float] = Field(None, ge=0, description="Water depth (meters)")
    max_draft: Optional[float] = Field(None, ge=0, description="Maximum vessel draft (meters)")
    max_dwt: Optional[float] = Field(None, ge=0, description="Maximum deadweight tonnage")
    max_loa: Optional[float] = Field(None, ge=0, description="Maximum length overall (meters)")

    # Capacity & equipment
    loading_rate: Optional[float] = Field(None, ge=0, description="Design loading rate (tons/hour)")
    unloading_rate: Optional[float] = Field(None, ge=0, description="Design unloading rate (tons/hour)")
    storage_capacity: Optional[float] = Field(None, ge=0, description="Associated storage capacity (tons)")
    num_shiploaders: int = Field(default=0, ge=0, description="Number of shiploaders")
    num_conveyors: int = Field(default=0, ge=0, description="Number of conveyors")
    num_cranes: int = Field(default=0, ge=0, description="Number of cranes")

    # Location
    latitude: Optional[str] = Field(None, max_length=50)
    longitude: Optional[str] = Field(None, max_length=50)

    # Commodities handled
    commodities: List[str] = Field(default_factory=list, description="List of commodities handled")

    # Additional information
    notes: Optional[str] = None
    restrictions: Optional[str] = Field(None, description="Operational restrictions")

    is_active: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)


class BerthCreate(BerthBase):
    """Schema for creating a berth"""
    site_id: UUID = Field(..., description="Site/port ID where berth is located")
    status: BerthStatus = Field(default=BerthStatus.AVAILABLE, description="Initial berth status")


class BerthUpdate(BaseModel):
    """Schema for updating a berth"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    berth_type: Optional[BerthType] = None

    # Physical specifications
    length: Optional[float] = Field(None, ge=0)
    depth: Optional[float] = Field(None, ge=0)
    max_draft: Optional[float] = Field(None, ge=0)
    max_dwt: Optional[float] = Field(None, ge=0)
    max_loa: Optional[float] = Field(None, ge=0)

    # Capacity & equipment
    loading_rate: Optional[float] = Field(None, ge=0)
    unloading_rate: Optional[float] = Field(None, ge=0)
    storage_capacity: Optional[float] = Field(None, ge=0)
    num_shiploaders: Optional[int] = Field(None, ge=0)
    num_conveyors: Optional[int] = Field(None, ge=0)
    num_cranes: Optional[int] = Field(None, ge=0)

    # Location
    latitude: Optional[str] = Field(None, max_length=50)
    longitude: Optional[str] = Field(None, max_length=50)

    # Status
    status: Optional[BerthStatus] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None

    # Commodities handled
    commodities: Optional[List[str]] = None

    # Additional information
    notes: Optional[str] = None
    restrictions: Optional[str] = None

    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class BerthResponse(BerthBase):
    """Schema for berth response"""
    id: UUID
    site_id: UUID
    status: BerthStatus
    current_vessel_id: Optional[UUID] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BerthDetailResponse(BerthResponse):
    """Detailed berth response with current occupancy"""
    current_vessel_name: Optional[str] = None
    current_vessel_imo: Optional[str] = None
    current_operation_id: Optional[UUID] = None
    utilization_rate: Optional[float] = Field(None, description="Utilization rate (%)")
    total_operations: int = 0


class BerthOccupancyResponse(BaseModel):
    """Berth occupancy timeline"""
    berth_id: UUID
    berth_name: str
    berth_code: str
    occupancy_periods: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of occupancy periods with vessel and operation details"
    )
    # Example:
    # [
    #   {
    #     "vessel_id": "...",
    #     "vessel_name": "MV Carrier",
    #     "operation_id": "...",
    #     "start": "2025-01-15T08:00:00Z",
    #     "end": "2025-01-16T18:00:00Z",
    #     "commodity": "soybean",
    #     "quantity": 75000
    #   }
    # ]


class BerthCapacityResponse(BaseModel):
    """Berth capacity information"""
    berth_id: UUID
    berth_name: str
    berth_code: str

    # Design capacity
    loading_rate: Optional[float]
    unloading_rate: Optional[float]
    storage_capacity: Optional[float]

    # Current utilization
    current_utilization: float = Field(..., description="Current utilization (%)")
    available_capacity: float = Field(..., description="Available capacity (tons)")

    # Equipment status
    equipment_available: int = Field(..., description="Number of available equipment")
    equipment_total: int = Field(..., description="Total equipment count")

    # Next available
    next_available: Optional[datetime] = Field(None, description="Next available datetime")


class BerthListResponse(BaseModel):
    """Response for listing berths with pagination"""
    total: int
    page: int
    page_size: int
    berths: List[BerthResponse]


class BerthSearchParams(BaseModel):
    """Search parameters for berths"""
    name: Optional[str] = Field(None, description="Search by berth name")
    code: Optional[str] = Field(None, description="Search by berth code")
    status: Optional[BerthStatus] = Field(None, description="Filter by status")
    berth_type: Optional[BerthType] = Field(None, description="Filter by berth type")
    commodity: Optional[str] = Field(None, description="Filter by commodity handled")
    available: Optional[bool] = Field(None, description="Filter by availability")
