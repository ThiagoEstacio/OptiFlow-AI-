"""
Vessel schemas for API request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from app.models.port.vessel import VesselType, VesselStatus


class VesselBase(BaseModel):
    """Base vessel schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Vessel name")
    imo_number: str = Field(..., min_length=7, max_length=20, description="IMO ship identification number")
    call_sign: Optional[str] = Field(None, max_length=20, description="Call sign")
    mmsi: Optional[str] = Field(None, max_length=20, description="Maritime Mobile Service Identity")
    vessel_type: VesselType = Field(..., description="Type of vessel")
    flag: Optional[str] = Field(None, max_length=100, description="Country of registration")
    classification: Optional[str] = Field(None, max_length=100, description="Classification society")

    # Specifications
    dwt: Optional[float] = Field(None, ge=0, description="Deadweight tonnage (tons)")
    grt: Optional[float] = Field(None, ge=0, description="Gross registered tonnage")
    nrt: Optional[float] = Field(None, ge=0, description="Net registered tonnage")
    length: Optional[float] = Field(None, ge=0, description="Length overall (meters)")
    beam: Optional[float] = Field(None, ge=0, description="Beam/width (meters)")
    draft: Optional[float] = Field(None, ge=0, description="Draft (meters)")
    capacity: Optional[float] = Field(None, ge=0, description="Cargo capacity")

    # Ownership
    owner: Optional[str] = Field(None, max_length=255)
    operator: Optional[str] = Field(None, max_length=255)
    agent: Optional[str] = Field(None, max_length=255, description="Port agent")

    # Schedule
    eta: Optional[datetime] = Field(None, description="Estimated time of arrival")
    etb: Optional[datetime] = Field(None, description="Estimated time of berthing")
    etc: Optional[datetime] = Field(None, description="Estimated time of completion")
    etd: Optional[datetime] = Field(None, description="Estimated time of departure")

    # Additional info
    voyage_number: Optional[str] = Field(None, max_length=50)
    previous_port: Optional[str] = Field(None, max_length=100)
    next_port: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

    is_active: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)


class VesselCreate(VesselBase):
    """Schema for creating a vessel"""
    site_id: UUID = Field(..., description="Site/port ID where vessel is visiting")
    status: VesselStatus = Field(default=VesselStatus.SCHEDULED, description="Initial vessel status")


class VesselUpdate(BaseModel):
    """Schema for updating a vessel"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    call_sign: Optional[str] = Field(None, max_length=20)
    mmsi: Optional[str] = Field(None, max_length=20)
    vessel_type: Optional[VesselType] = None
    flag: Optional[str] = Field(None, max_length=100)
    classification: Optional[str] = Field(None, max_length=100)

    # Specifications
    dwt: Optional[float] = Field(None, ge=0)
    grt: Optional[float] = Field(None, ge=0)
    nrt: Optional[float] = Field(None, ge=0)
    length: Optional[float] = Field(None, ge=0)
    beam: Optional[float] = Field(None, ge=0)
    draft: Optional[float] = Field(None, ge=0)
    capacity: Optional[float] = Field(None, ge=0)

    # Ownership
    owner: Optional[str] = Field(None, max_length=255)
    operator: Optional[str] = Field(None, max_length=255)
    agent: Optional[str] = Field(None, max_length=255)

    # Status
    status: Optional[VesselStatus] = None
    current_berth_id: Optional[UUID] = None

    # Schedule
    eta: Optional[datetime] = None
    ata: Optional[datetime] = None
    etb: Optional[datetime] = None
    atb: Optional[datetime] = None
    etc: Optional[datetime] = None
    atc: Optional[datetime] = None
    etd: Optional[datetime] = None
    atd: Optional[datetime] = None

    # Additional info
    voyage_number: Optional[str] = Field(None, max_length=50)
    previous_port: Optional[str] = Field(None, max_length=100)
    next_port: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class VesselResponse(VesselBase):
    """Schema for vessel response"""
    id: UUID
    site_id: UUID
    status: VesselStatus
    current_berth_id: Optional[UUID] = None

    # Actual times
    ata: Optional[datetime] = None
    atb: Optional[datetime] = None
    atc: Optional[datetime] = None
    atd: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VesselDetailResponse(VesselResponse):
    """Detailed vessel response with related data"""
    # This will be populated in the API endpoint
    current_berth_name: Optional[str] = None
    current_operation_id: Optional[UUID] = None
    total_operations: int = 0


class VesselListResponse(BaseModel):
    """Response for listing vessels with pagination"""
    total: int
    page: int
    page_size: int
    vessels: List[VesselResponse]


class VesselSearchParams(BaseModel):
    """Search parameters for vessels"""
    name: Optional[str] = Field(None, description="Search by vessel name")
    imo_number: Optional[str] = Field(None, description="Search by IMO number")
    status: Optional[VesselStatus] = Field(None, description="Filter by status")
    vessel_type: Optional[VesselType] = Field(None, description="Filter by vessel type")
    berth_id: Optional[UUID] = Field(None, description="Filter by current berth")
    from_date: Optional[datetime] = Field(None, description="Filter by ETA from date")
    to_date: Optional[datetime] = Field(None, description="Filter by ETA to date")
