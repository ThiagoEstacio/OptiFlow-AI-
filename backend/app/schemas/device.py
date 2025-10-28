"""
Device schemas for request/response validation
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


class DeviceBase(BaseModel):
    """Base schema for Device"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    device_type: str = Field(..., description="Type of device: PLC, Sensor, Gateway, etc")
    protocol: str = Field(..., description="Communication protocol")

    # Connection
    ip_address: Optional[str] = Field(None, description="IP address or hostname")
    port: Optional[int] = Field(None, ge=1, le=65535)

    # Configuration (protocol-specific)
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Protocol-specific configuration")

    # Performance
    scan_rate: Optional[int] = Field(1000, ge=100, description="Scan rate in milliseconds")
    timeout: Optional[int] = Field(5000, ge=1000, description="Connection timeout in milliseconds")

    # Metadata
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None

    # Status
    enabled: bool = True

    @validator('protocol')
    def validate_protocol(cls, v):
        allowed_protocols = ['opcua', 'modbus_tcp', 'modbus_rtu', 'mqtt', 's7', 'ethernetip', 'http']
        if v not in allowed_protocols:
            raise ValueError(f'protocol must be one of: {", ".join(allowed_protocols)}')
        return v


class DeviceCreate(DeviceBase):
    """Schema for creating a new Device"""
    site_id: UUID


class DeviceUpdate(BaseModel):
    """Schema for updating a Device"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    device_type: Optional[str] = None
    protocol: Optional[str] = None

    # Connection
    ip_address: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)

    # Configuration
    config: Optional[Dict[str, Any]] = None

    # Performance
    scan_rate: Optional[int] = Field(None, ge=100)
    timeout: Optional[int] = Field(None, ge=1000)

    # Metadata
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None

    # Status
    enabled: Optional[bool] = None

    @validator('protocol')
    def validate_protocol(cls, v):
        if v is not None:
            allowed_protocols = ['opcua', 'modbus_tcp', 'modbus_rtu', 'mqtt', 's7', 'ethernetip', 'http']
            if v not in allowed_protocols:
                raise ValueError(f'protocol must be one of: {", ".join(allowed_protocols)}')
        return v


class DeviceResponse(DeviceBase):
    """Schema for Device response"""
    id: UUID
    site_id: UUID
    status: str  # from DeviceStatus enum
    last_seen: Optional[datetime] = None
    total_tags: int = 0
    data_points_collected: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
