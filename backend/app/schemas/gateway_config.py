"""
Gateway Configuration Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class GatewayTypeEnum(str, Enum):
    """Supported gateway protocols"""
    OPCUA = "opcua"
    MODBUS_TCP = "modbus_tcp"
    SIEMENS_S7 = "siemens_s7"
    ROCKWELL_EIP = "rockwell_eip"


# Gateway Tag Schemas
class GatewayTagBase(BaseModel):
    """Base gateway tag schema"""
    tag_name: str = Field(..., min_length=1, max_length=200)
    enabled: bool = True
    address_config: Dict[str, Any] = Field(..., description="Protocol-specific address configuration")
    data_type: str = "float"
    scale_factor: float = 1.0
    offset: float = 0.0
    unit: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)


class GatewayTagCreate(GatewayTagBase):
    """Schema for creating a gateway tag"""
    pass


class GatewayTagUpdate(BaseModel):
    """Schema for updating a gateway tag"""
    tag_name: Optional[str] = Field(None, min_length=1, max_length=200)
    enabled: Optional[bool] = None
    address_config: Optional[Dict[str, Any]] = None
    data_type: Optional[str] = None
    scale_factor: Optional[float] = None
    offset: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)


class GatewayTag(GatewayTagBase):
    """Schema for gateway tag response"""
    id: int
    gateway_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Gateway Config Schemas
class GatewayConfigBase(BaseModel):
    """Base gateway configuration schema"""
    name: str = Field(..., min_length=1, max_length=200)
    gateway_type: GatewayTypeEnum
    enabled: bool = True
    connection_config: Dict[str, Any] = Field(..., description="Connection settings (JSON)")
    polling_interval_ms: int = Field(1000, ge=100, le=60000)
    max_retries: int = Field(5, ge=1, le=20)
    base_retry_delay: int = Field(5, ge=1, le=300)
    max_buffer_size: int = Field(10000, ge=100, le=100000)
    description: Optional[str] = Field(None, max_length=500)


class GatewayConfigCreate(GatewayConfigBase):
    """Schema for creating a gateway configuration"""
    tags: Optional[List[GatewayTagCreate]] = Field(default_factory=list)


class GatewayConfigUpdate(BaseModel):
    """Schema for updating a gateway configuration"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    gateway_type: Optional[GatewayTypeEnum] = None
    enabled: Optional[bool] = None
    connection_config: Optional[Dict[str, Any]] = None
    polling_interval_ms: Optional[int] = Field(None, ge=100, le=60000)
    max_retries: Optional[int] = Field(None, ge=1, le=20)
    base_retry_delay: Optional[int] = Field(None, ge=1, le=300)
    max_buffer_size: Optional[int] = Field(None, ge=100, le=100000)
    description: Optional[str] = Field(None, max_length=500)


class GatewayConfig(GatewayConfigBase):
    """Schema for gateway configuration response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[GatewayTag] = Field(default_factory=list)

    class Config:
        from_attributes = True


class GatewayConfigList(BaseModel):
    """Schema for gateway configuration list response"""
    id: int
    name: str
    gateway_type: GatewayTypeEnum
    enabled: bool
    description: Optional[str] = None
    tags_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# OPC-UA Discovery Schemas
class OPCUADiscoveryRequest(BaseModel):
    """Request schema for OPC-UA tag discovery"""
    endpoint: str = Field(..., description="OPC-UA server endpoint URL")
    namespace_index: Optional[int] = Field(None, description="Namespace index to filter tags")
    tag_filter: Optional[str] = Field(None, description="Search term to filter tag names")


class OPCUANamespace(BaseModel):
    """OPC-UA namespace information"""
    index: int
    uri: str


class OPCUADiscoveredTag(BaseModel):
    """Discovered OPC-UA tag"""
    tag_name: str
    display_name: str
    address: str
    data_type: Optional[str] = None
    description: Optional[str] = None
    readable: bool = True
    writable: bool = False
    current_value: Optional[str] = None


class OPCUADiscoveryResponse(BaseModel):
    """Response schema for OPC-UA tag discovery"""
    success: bool
    endpoint: str
    namespaces: List[OPCUANamespace]
    tags: List[OPCUADiscoveredTag]
    tag_count: int
    error: Optional[str] = None


class OPCUADiscoveryImportRequest(BaseModel):
    """Request to import discovered tags into a gateway configuration"""
    gateway_name: str = Field(..., description="Name for the new gateway configuration")
    endpoint: str
    namespace_index: Optional[int] = None
    tag_filter: Optional[str] = None
    polling_interval_ms: int = Field(1000, ge=100, le=60000)
    description: Optional[str] = None


# Gateway Health Schemas
class GatewayHealthLog(BaseModel):
    """Gateway health log entry"""
    id: int
    gateway_name: str
    timestamp: datetime
    status: str
    successful_reads: int = 0
    failed_reads: int = 0
    buffer_size: int = 0
    uptime_seconds: Optional[float] = None
    last_error: Optional[str] = None

    class Config:
        from_attributes = True


# Bulk Operations
class BulkGatewayImport(BaseModel):
    """Schema for bulk import of gateway configurations"""
    gateways: List[GatewayConfigCreate]


class BulkImportResponse(BaseModel):
    """Response for bulk import operation"""
    success: bool
    imported_count: int
    failed_count: int
    errors: List[str] = Field(default_factory=list)
