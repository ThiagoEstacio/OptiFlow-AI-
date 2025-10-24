"""
Device schemas
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from app.optiflow.models.device import DeviceProtocol, DeviceStatus


class DeviceBase(BaseModel):
    """Base device schema"""
    name: str
    description: Optional[str] = None
    protocol: DeviceProtocol
    connection_config: Dict[str, Any]
    is_active: bool = True
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    settings: Dict[str, Any] = {}


class DeviceCreate(DeviceBase):
    """Device creation schema"""
    site_id: UUID


class DeviceUpdate(BaseModel):
    """Device update schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    connection_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class DeviceResponse(DeviceBase):
    """Device response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    site_id: UUID
    status: DeviceStatus
    last_seen: Optional[datetime] = None
    error_message: Optional[str] = None
    total_tags: int = 0
    data_points_collected: int = 0
    created_at: datetime
    updated_at: datetime
