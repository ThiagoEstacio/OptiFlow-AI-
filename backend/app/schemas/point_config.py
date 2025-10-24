"""
Pydantic schemas for Point Configuration API

Schemas for request/response models for Point Templates and Configurations.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID

from app.models.point_config import CompressionType, HistorianType


# ============================================================================
# Point Template Schemas
# ============================================================================

class PointTemplateBase(BaseModel):
    """Base schema for Point Template"""
    name: str = Field(..., min_length=2, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    is_active: bool = Field(True, description="Whether template is active")

    # Category and data type defaults
    category: Optional[str] = Field(None, description="Default tag category")
    data_type: Optional[str] = Field(None, description="Default data type")

    # Engineering settings
    unit: Optional[str] = Field(None, max_length=50, description="Engineering unit")
    min_value: Optional[float] = Field(None, description="Minimum value")
    max_value: Optional[float] = Field(None, description="Maximum value")
    engineering_min: Optional[float] = Field(None, description="Engineering minimum")
    engineering_max: Optional[float] = Field(None, description="Engineering maximum")
    scale: Optional[float] = Field(1.0, description="Scaling factor")
    offset: Optional[float] = Field(0.0, description="Offset value")

    # Sampling configuration
    scan_rate_ms: Optional[int] = Field(1000, ge=10, le=3600000, description="Scan rate in milliseconds")
    deadband: Optional[float] = Field(None, ge=0, description="Deadband value")

    # Compression settings
    compression_enabled: bool = Field(False, description="Enable compression")
    compression_type: CompressionType = Field(CompressionType.NONE, description="Compression algorithm")
    compression_config: Dict[str, Any] = Field(default_factory=dict, description="Compression configuration")

    # Historian settings
    historian_enabled: bool = Field(True, description="Enable historian")
    historian_type: HistorianType = Field(HistorianType.INFLUXDB, description="Historian type")
    historian_config: Dict[str, Any] = Field(default_factory=dict, description="Historian configuration")

    # Alarm settings
    enable_alarms: bool = Field(False, description="Enable alarms")
    alarm_config: Dict[str, Any] = Field(default_factory=dict, description="Alarm configuration")

    # Additional settings
    settings: Dict[str, Any] = Field(default_factory=dict, description="Additional settings")

    @validator('max_value')
    def validate_max_value(cls, v, values):
        """Validate max_value is greater than min_value"""
        if v is not None and 'min_value' in values and values['min_value'] is not None:
            if v <= values['min_value']:
                raise ValueError('max_value must be greater than min_value')
        return v

    @validator('engineering_max')
    def validate_engineering_max(cls, v, values):
        """Validate engineering_max is greater than engineering_min"""
        if v is not None and 'engineering_min' in values and values['engineering_min'] is not None:
            if v <= values['engineering_min']:
                raise ValueError('engineering_max must be greater than engineering_min')
        return v

    @validator('scale')
    def validate_scale(cls, v):
        """Validate scale is not zero"""
        if v == 0:
            raise ValueError('scale cannot be zero')
        return v


class PointTemplateCreate(PointTemplateBase):
    """Schema for creating a Point Template"""
    organization_id: UUID = Field(..., description="Organization ID")


class PointTemplateUpdate(BaseModel):
    """Schema for updating a Point Template"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None

    category: Optional[str] = None
    data_type: Optional[str] = None

    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    engineering_min: Optional[float] = None
    engineering_max: Optional[float] = None
    scale: Optional[float] = None
    offset: Optional[float] = None

    scan_rate_ms: Optional[int] = Field(None, ge=10, le=3600000)
    deadband: Optional[float] = Field(None, ge=0)

    compression_enabled: Optional[bool] = None
    compression_type: Optional[CompressionType] = None
    compression_config: Optional[Dict[str, Any]] = None

    historian_enabled: Optional[bool] = None
    historian_type: Optional[HistorianType] = None
    historian_config: Optional[Dict[str, Any]] = None

    enable_alarms: Optional[bool] = None
    alarm_config: Optional[Dict[str, Any]] = None

    settings: Optional[Dict[str, Any]] = None


class PointTemplateResponse(PointTemplateBase):
    """Schema for Point Template response"""
    id: UUID
    organization_id: UUID
    usage_count: int = Field(0, description="Number of points using this template")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Point Configuration Schemas
# ============================================================================

class PointConfigurationBase(BaseModel):
    """Base schema for Point Configuration"""
    template_id: Optional[UUID] = Field(None, description="Template ID (if using template)")

    # Compression settings
    compression_enabled: bool = Field(False, description="Enable compression")
    compression_type: CompressionType = Field(CompressionType.NONE, description="Compression algorithm")
    compression_config: Dict[str, Any] = Field(default_factory=dict, description="Compression configuration")

    # Historian settings
    historian_enabled: bool = Field(True, description="Enable historian")
    historian_type: HistorianType = Field(HistorianType.INFLUXDB, description="Historian type")
    historian_config: Dict[str, Any] = Field(default_factory=dict, description="Historian configuration")

    # Validation rules
    validation_rules: Dict[str, Any] = Field(default_factory=dict, description="Validation rules")

    # Additional settings
    settings: Dict[str, Any] = Field(default_factory=dict, description="Additional settings")


class PointConfigurationCreate(PointConfigurationBase):
    """Schema for creating a Point Configuration"""
    tag_id: UUID = Field(..., description="Tag ID")


class PointConfigurationUpdate(BaseModel):
    """Schema for updating a Point Configuration"""
    template_id: Optional[UUID] = None

    compression_enabled: Optional[bool] = None
    compression_type: Optional[CompressionType] = None
    compression_config: Optional[Dict[str, Any]] = None

    historian_enabled: Optional[bool] = None
    historian_type: Optional[HistorianType] = None
    historian_config: Optional[Dict[str, Any]] = None

    validation_rules: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None


class PointConfigurationResponse(PointConfigurationBase):
    """Schema for Point Configuration response"""
    id: UUID
    tag_id: UUID

    # Statistics
    total_samples_received: int = 0
    total_samples_stored: int = 0
    compression_ratio: float = 1.0

    total_writes: int = 0
    write_errors: int = 0

    avg_processing_time_ms: float = 0.0

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PointConfigurationWithStats(PointConfigurationResponse):
    """Point Configuration with additional statistics"""
    compression_ratio_percent: float = Field(0.0, description="Compression ratio as percentage")
    write_success_rate: float = Field(100.0, description="Write success rate as percentage")


# ============================================================================
# Batch Operations Schemas
# ============================================================================

class ApplyTemplateRequest(BaseModel):
    """Request to apply template to tags"""
    template_id: UUID = Field(..., description="Template ID to apply")
    tag_ids: List[UUID] = Field(..., min_items=1, description="List of tag IDs")
    override_existing: bool = Field(False, description="Override existing configurations")


class ApplyTemplateResponse(BaseModel):
    """Response from applying template"""
    success: bool
    applied_count: int
    skipped_count: int
    errors: List[Dict[str, str]] = []


class BulkCreatePointConfigRequest(BaseModel):
    """Request to create multiple point configurations"""
    configurations: List[PointConfigurationCreate] = Field(..., min_items=1)


class BulkCreatePointConfigResponse(BaseModel):
    """Response from bulk create"""
    success: bool
    created_count: int
    failed_count: int
    created_ids: List[UUID] = []
    errors: List[Dict[str, str]] = []


class PointValidationRequest(BaseModel):
    """Request to validate point configuration"""
    tag_id: UUID
    configuration: Optional[PointConfigurationBase] = None


class PointValidationResponse(BaseModel):
    """Response from point validation"""
    is_valid: bool
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []


# ============================================================================
# Query/Filter Schemas
# ============================================================================

class PointTemplateFilter(BaseModel):
    """Filter parameters for Point Templates"""
    organization_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    category: Optional[str] = None
    data_type: Optional[str] = None
    search: Optional[str] = Field(None, description="Search in name and description")


class PointConfigurationFilter(BaseModel):
    """Filter parameters for Point Configurations"""
    tag_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    compression_enabled: Optional[bool] = None
    historian_enabled: Optional[bool] = None


# ============================================================================
# Statistics Schemas
# ============================================================================

class CompressionStats(BaseModel):
    """Compression statistics"""
    algorithm: str
    samples_received: int
    samples_stored: int
    compression_ratio_percent: float
    config: Dict[str, Any]


class HistorianStats(BaseModel):
    """Historian statistics"""
    historian_type: str
    total_writes: int
    write_errors: int
    write_success_rate: float
    last_write_timestamp: Optional[datetime]


class PointConfigurationStats(BaseModel):
    """Complete point configuration statistics"""
    point_config_id: UUID
    tag_id: UUID
    compression_stats: Optional[CompressionStats]
    historian_stats: Optional[HistorianStats]
    avg_processing_time_ms: float
