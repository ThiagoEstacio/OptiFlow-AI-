"""
Tag schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from app.models.tag import TagDataType, TagCategory


class TagBase(BaseModel):
    """Base tag schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Tag name")
    description: Optional[str] = Field(None, description="Tag description")
    address: str = Field(..., min_length=1, max_length=500, description="Protocol-specific address")
    data_type: TagDataType = Field(..., description="Data type")
    unit: Optional[str] = Field(None, max_length=50, description="Engineering unit")
    category: TagCategory = Field(TagCategory.PROCESS, description="Tag category")
    is_active: bool = Field(True, description="Is tag active")

    # Engineering limits
    min_value: Optional[float] = Field(None, description="Minimum value")
    max_value: Optional[float] = Field(None, description="Maximum value")
    engineering_min: Optional[float] = Field(None, description="Engineering minimum")
    engineering_max: Optional[float] = Field(None, description="Engineering maximum")

    # Scaling
    scale: float = Field(1.0, description="Scale factor")
    offset: float = Field(0.0, description="Offset value")

    # Sampling
    scan_rate_ms: int = Field(1000, ge=100, le=3600000, description="Scan rate in milliseconds")
    deadband: Optional[float] = Field(None, description="Deadband threshold")

    # Quality
    enable_quality_check: bool = Field(True, description="Enable quality checking")

    # Additional settings
    settings: Dict[str, Any] = Field(default_factory=dict, description="Additional settings")


class TagCreate(TagBase):
    """Schema for creating a tag"""
    device_id: UUID = Field(..., description="Device ID")


class TagUpdate(BaseModel):
    """Schema for updating a tag"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    unit: Optional[str] = Field(None, max_length=50)
    category: Optional[TagCategory] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    engineering_min: Optional[float] = None
    engineering_max: Optional[float] = None
    scale: Optional[float] = None
    offset: Optional[float] = None
    scan_rate_ms: Optional[int] = Field(None, ge=100, le=3600000)
    deadband: Optional[float] = None
    enable_quality_check: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class TagResponse(TagBase):
    """Schema for tag response"""
    id: UUID
    device_id: UUID
    last_value: Optional[str] = None
    last_quality: Optional[str] = None
    last_timestamp: Optional[datetime] = None
    data_points_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TagWithDeviceResponse(TagResponse):
    """Schema for tag response with device info"""
    device_name: str
    device_protocol: str
    site_id: UUID


class TagListResponse(BaseModel):
    """Schema for tag list response"""
    tags: List[TagResponse]
    total: int
    page: int
    page_size: int


class TagValueResponse(BaseModel):
    """Schema for tag value response"""
    tag_id: UUID
    value: Any
    quality: str
    timestamp: datetime


class TagValuesResponse(BaseModel):
    """Schema for multiple tag values"""
    values: List[TagValueResponse]
