"""
Device schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from app.models.device import DeviceProtocol, DeviceStatus


class DeviceConnectionConfig(BaseModel):
    """Base connection configuration"""
    pass


class OPCUAConnectionConfig(DeviceConnectionConfig):
    """OPC UA connection configuration"""
    endpoint: str = Field(..., description="OPC UA endpoint URL (e.g., opc.tcp://localhost:4840)")
    username: Optional[str] = Field(None, description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")
    security_mode: Optional[str] = Field("None", description="Security mode: None, Sign, SignAndEncrypt")
    security_policy: Optional[str] = Field("None", description="Security policy")
    certificate_path: Optional[str] = Field(None, description="Path to client certificate")
    private_key_path: Optional[str] = Field(None, description="Path to private key")


class ModbusTCPConnectionConfig(DeviceConnectionConfig):
    """Modbus TCP connection configuration"""
    host: str = Field(..., description="Modbus server IP address")
    port: int = Field(502, description="Modbus server port")
    slave_id: int = Field(1, description="Modbus slave/unit ID")
    timeout: int = Field(3, description="Connection timeout in seconds")


class MQTTConnectionConfig(DeviceConnectionConfig):
    """MQTT connection configuration"""
    broker: str = Field(..., description="MQTT broker address")
    port: int = Field(1883, description="MQTT broker port")
    username: Optional[str] = Field(None, description="Username")
    password: Optional[str] = Field(None, description="Password")
    client_id: Optional[str] = Field(None, description="MQTT client ID")
    topics: List[str] = Field(default_factory=list, description="Topics to subscribe")


class DeviceBase(BaseModel):
    """Base device schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Device name")
    description: Optional[str] = Field(None, description="Device description")
    protocol: DeviceProtocol = Field(..., description="Communication protocol")
    connection_config: Dict[str, Any] = Field(..., description="Protocol-specific connection configuration")
    is_active: bool = Field(True, description="Is device active")
    manufacturer: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    firmware_version: Optional[str] = Field(None, max_length=50)
    settings: Dict[str, Any] = Field(default_factory=dict, description="Additional settings")


class DeviceCreate(DeviceBase):
    """Schema for creating a device"""
    site_id: UUID = Field(..., description="Site ID where device belongs")


class DeviceUpdate(BaseModel):
    """Schema for updating a device"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    connection_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    manufacturer: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    firmware_version: Optional[str] = Field(None, max_length=50)
    settings: Optional[Dict[str, Any]] = None


class DeviceResponse(DeviceBase):
    """Schema for device response"""
    id: UUID
    site_id: UUID
    status: DeviceStatus
    last_seen: Optional[datetime] = None
    error_message: Optional[str] = None
    total_tags: int = 0
    data_points_collected: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """Schema for device list response"""
    devices: List[DeviceResponse]
    total: int
    page: int
    page_size: int


class DeviceTestConnectionRequest(BaseModel):
    """Schema for testing device connection"""
    protocol: DeviceProtocol
    connection_config: Dict[str, Any]


class DeviceTestConnectionResponse(BaseModel):
    """Schema for device connection test result"""
    success: bool
    message: Optional[str] = None
    server_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DeviceBrowseTagsRequest(BaseModel):
    """Schema for browsing device tags"""
    device_id: Optional[UUID] = Field(None, description="Device ID (if already created)")
    protocol: DeviceProtocol = Field(..., description="Protocol type")
    connection_config: Dict[str, Any] = Field(..., description="Connection configuration")
    max_depth: int = Field(10, ge=1, le=20, description="Maximum depth to browse")


class BrowsedTag(BaseModel):
    """Schema for a browsed tag"""
    name: str
    display_name: str
    browse_name: str
    node_id: str
    address: str
    data_type: str
    full_path: str
    description: str
    namespace_index: int
    current_value: Optional[str] = None
    quality: Optional[str] = None
    timestamp: Optional[str] = None


class DeviceBrowseTagsResponse(BaseModel):
    """Schema for browse tags response"""
    success: bool
    tags: List[BrowsedTag] = []
    total: int = 0
    error: Optional[str] = None


class DeviceImportTagsRequest(BaseModel):
    """Schema for importing tags to device"""
    device_id: UUID = Field(..., description="Device ID")
    tags: List[Dict[str, Any]] = Field(..., description="Tags to import")
    auto_activate: bool = Field(True, description="Automatically activate imported tags")
    category: Optional[str] = Field("process", description="Default category for tags")
