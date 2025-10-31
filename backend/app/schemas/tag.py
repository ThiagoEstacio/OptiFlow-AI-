"""
Tag schemas for request/response validation
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator


class TagBase(BaseModel):
    """Base schema for Tag"""
    name: str = Field(..., min_length=1, max_length=255)
    address: str = Field(..., description="Protocol-specific address")
    data_type: str = Field(..., description="Data type: BOOL, INT, FLOAT, DOUBLE, STRING, etc")
    description: Optional[str] = None

    # Engineering units
    unit: Optional[str] = Field(None, max_length=50, description="Engineering unit, e.g., °C, m/s, kW")

    # Scaling
    scale_factor: Optional[float] = Field(1.0, description="Multiplier for raw value")
    offset: Optional[float] = Field(0.0, description="Offset added after scaling")

    # Limits
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    engineering_min: Optional[float] = None
    engineering_max: Optional[float] = None

    # Sampling
    scan_rate_ms: Optional[int] = Field(1000, ge=100, description="Scan rate in milliseconds")
    deadband: Optional[float] = Field(None, description="Change threshold to trigger update")

    # Category
    category: Optional[str] = Field(None, description="Category: PROCESS, ENERGY, QUALITY, etc")

    # Status
    enabled: bool = True
    log_enabled: bool = True

    @validator('data_type')
    def validate_data_type(cls, v):
        allowed_types = ['BOOL', 'BOOLEAN', 'INT', 'INTEGER', 'FLOAT', 'DOUBLE', 'STRING', 'BYTE', 'WORD', 'DWORD', 'REAL']
        if v not in allowed_types:
            raise ValueError(f'data_type must be one of: {", ".join(allowed_types)}')
        return v

    @validator('category')
    def validate_category(cls, v):
        if v is not None:
            allowed_categories = ['PROCESS', 'ENERGY', 'QUALITY', 'PRODUCTION', 'MAINTENANCE', 'ALARM', 'SETPOINT', 'STATUS']
            if v not in allowed_categories:
                raise ValueError(f'category must be one of: {", ".join(allowed_categories)}')
        return v


class TagCreate(TagBase):
    """Schema for creating a new Tag"""
    device_id: UUID


class TagUpdate(BaseModel):
    """Schema for updating a Tag"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = None
    data_type: Optional[str] = None
    description: Optional[str] = None

    # Engineering units
    unit: Optional[str] = Field(None, max_length=50)

    # Scaling
    scale_factor: Optional[float] = None
    offset: Optional[float] = None

    # Limits
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    engineering_min: Optional[float] = None
    engineering_max: Optional[float] = None

    # Sampling
    scan_rate_ms: Optional[int] = Field(None, ge=100)
    deadband: Optional[float] = None

    # Category
    category: Optional[str] = None

    # Status
    enabled: Optional[bool] = None
    log_enabled: Optional[bool] = None

    @validator('data_type')
    def validate_data_type(cls, v):
        if v is not None:
            allowed_types = ['BOOL', 'BOOLEAN', 'INT', 'INTEGER', 'FLOAT', 'DOUBLE', 'STRING', 'BYTE', 'WORD', 'DWORD', 'REAL']
            if v not in allowed_types:
                raise ValueError(f'data_type must be one of: {", ".join(allowed_types)}')
        return v

    @validator('category')
    def validate_category(cls, v):
        if v is not None:
            allowed_categories = ['PROCESS', 'ENERGY', 'QUALITY', 'PRODUCTION', 'MAINTENANCE', 'ALARM', 'SETPOINT', 'STATUS']
            if v not in allowed_categories:
                raise ValueError(f'category must be one of: {", ".join(allowed_categories)}')
        return v


class TagResponse(TagBase):
    """Schema for Tag response"""
    id: UUID
    device_id: UUID
    last_value: Optional[str] = None  # Changed from float to str to support all data types
    last_quality: Optional[str] = None
    last_timestamp: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @validator('data_type', pre=True)
    def convert_data_type(cls, v):
        """Convert enum to string uppercase"""
        if hasattr(v, 'value'):
            return v.value.upper()
        return v.upper() if isinstance(v, str) else v

    @validator('category', pre=True)
    def convert_category(cls, v):
        """Convert enum to string uppercase"""
        if v is None:
            return None
        if hasattr(v, 'value'):
            return v.value.upper()
        return v.upper() if isinstance(v, str) else v

    class Config:
        from_attributes = True
