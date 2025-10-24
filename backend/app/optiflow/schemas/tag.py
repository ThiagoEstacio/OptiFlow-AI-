"""
Tag schemas
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from app.optiflow.models.tag import TagDataType


class TagBase(BaseModel):
    """Base tag schema"""
    name: str
    description: Optional[str] = None
    data_type: TagDataType
    unit: Optional[str] = None
    address: str
    scaling_factor: float = 1.0
    scaling_offset: float = 0.0
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    deadband: float = 0.0
    sample_rate: int = 1000
    is_enabled: bool = True
    metadata: Dict[str, Any] = {}


class TagCreate(TagBase):
    """Tag creation schema"""
    device_id: UUID


class TagUpdate(BaseModel):
    """Tag update schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    data_type: Optional[TagDataType] = None
    unit: Optional[str] = None
    address: Optional[str] = None
    scaling_factor: Optional[float] = None
    scaling_offset: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    deadband: Optional[float] = None
    sample_rate: Optional[int] = None
    is_enabled: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class TagResponse(TagBase):
    """Tag response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: UUID
    last_value: Optional[float] = None
    last_value_timestamp: Optional[datetime] = None
    quality: Optional[str] = None
    created_at: datetime
    updated_at: datetime
