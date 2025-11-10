"""
Extended Tags Schemas - PI Asset Framework style

Pydantic schemas for API requests/responses for:
- Extended gateway tags (with formulas, archive config)
- Tag formulas
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID


class TagTypeEnum(str, Enum):
    """Tag calculation types"""
    PHYSICAL = "physical"
    CALCULATED = "calculated"
    LOGICAL = "logical"
    AGGREGATED = "aggregated"


# ============================================================================
# Extended Gateway Tag Schemas
# ============================================================================

class GatewayTagExtendedBase(BaseModel):
    """Base schema for Extended Gateway Tag"""
    gateway_id: Optional[int] = None
    tag_name: str = Field(..., min_length=1, max_length=200)
    enabled: bool = True

    # Hierarchy
    asset_id: Optional[UUID] = None
    tag_group: Optional[str] = Field(None, max_length=200)

    # Tag type
    tag_type: TagTypeEnum = TagTypeEnum.PHYSICAL

    # Physical tag fields
    address_config: Optional[Dict[str, Any]] = None
    data_type: str = Field(default="float", max_length=50)
    scale_factor: float = 1.0
    tag_offset: float = 0.0

    # Calculated/logical tag fields
    formula: Optional[str] = None
    formula_tags: Optional[List[Any]] = None  # List of tag IDs
    condition: Optional[str] = None

    # Units and limits
    unit: Optional[str] = Field(None, max_length=50)
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    # Historical archiving (PI-style)
    archive_enabled: bool = True
    archive_type: str = Field(default="on_change", max_length=50)
    archive_deadband: Optional[float] = None
    archive_interval_seconds: Optional[int] = None
    compression_deviation: Optional[float] = None

    # Quality and alarms
    quality_enabled: bool = True
    alarm_enabled: bool = False
    alarm_config: Optional[Dict[str, Any]] = None

    # Metadata
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    properties: Optional[Dict[str, Any]] = None

    @field_validator('archive_type')
    @classmethod
    def validate_archive_type(cls, v):
        allowed = ['on_change', 'periodic', 'compressed']
        if v not in allowed:
            raise ValueError(f'archive_type must be one of: {allowed}')
        return v

    @field_validator('tag_type')
    @classmethod
    def validate_calculated_fields(cls, v, info):
        """Ensure calculated/logical tags have required fields"""
        # Note: This validator runs before all fields are set,
        # so we check in the application logic instead
        return v


class GatewayTagExtendedCreate(GatewayTagExtendedBase):
    """Schema for creating an extended tag"""
    pass


class GatewayTagExtendedUpdate(BaseModel):
    """Schema for updating an extended tag"""
    gateway_id: Optional[int] = None
    tag_name: Optional[str] = Field(None, min_length=1, max_length=200)
    enabled: Optional[bool] = None

    # Hierarchy
    asset_id: Optional[UUID] = None
    tag_group: Optional[str] = Field(None, max_length=200)

    # Tag type
    tag_type: Optional[TagTypeEnum] = None

    # Physical tag fields
    address_config: Optional[Dict[str, Any]] = None
    data_type: Optional[str] = Field(None, max_length=50)
    scale_factor: Optional[float] = None
    tag_offset: Optional[float] = None

    # Calculated/logical tag fields
    formula: Optional[str] = None
    formula_tags: Optional[List[Any]] = None
    condition: Optional[str] = None

    # Units and limits
    unit: Optional[str] = Field(None, max_length=50)
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    # Historical archiving
    archive_enabled: Optional[bool] = None
    archive_type: Optional[str] = Field(None, max_length=50)
    archive_deadband: Optional[float] = None
    archive_interval_seconds: Optional[int] = None
    compression_deviation: Optional[float] = None

    # Quality and alarms
    quality_enabled: Optional[bool] = None
    alarm_enabled: Optional[bool] = None
    alarm_config: Optional[Dict[str, Any]] = None

    # Metadata
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    properties: Optional[Dict[str, Any]] = None


class GatewayTagExtendedResponse(GatewayTagExtendedBase):
    """Schema for extended tag response"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Tag Formula Schemas
# ============================================================================

class TagFormulaBase(BaseModel):
    """Base schema for Tag Formula"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)

    # Formula definition
    formula_type: str = Field(..., max_length=50)
    expression: str = Field(..., min_length=1)

    # Input/Output
    input_tags: Optional[List[Any]] = None
    output_unit: Optional[str] = Field(None, max_length=50)
    output_type: Optional[str] = Field(None, max_length=50)

    # Execution
    execution_interval_seconds: Optional[int] = None
    is_active: bool = True

    # Metadata
    category: Optional[str] = Field(None, max_length=100)
    tags_metadata: Optional[Dict[str, Any]] = None

    @field_validator('formula_type')
    @classmethod
    def validate_formula_type(cls, v):
        allowed = ['expression', 'script', 'sql', 'aggregation']
        if v not in allowed:
            raise ValueError(f'formula_type must be one of: {allowed}')
        return v


class TagFormulaCreate(TagFormulaBase):
    """Schema for creating a formula"""
    pass


class TagFormulaUpdate(BaseModel):
    """Schema for updating a formula"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    formula_type: Optional[str] = Field(None, max_length=50)
    expression: Optional[str] = Field(None, min_length=1)
    input_tags: Optional[List[Any]] = None
    output_unit: Optional[str] = Field(None, max_length=50)
    output_type: Optional[str] = Field(None, max_length=50)
    execution_interval_seconds: Optional[int] = None
    is_active: Optional[bool] = None
    category: Optional[str] = Field(None, max_length=100)
    tags_metadata: Optional[Dict[str, Any]] = None


class TagFormulaResponse(TagFormulaBase):
    """Schema for formula response"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Bulk Operations
# ============================================================================

class BulkTagOperation(BaseModel):
    """Schema for bulk tag operations"""
    tag_ids: List[int] = Field(..., min_items=1)
    operation: str = Field(..., pattern="^(enable|disable|delete|move)$")
    target_asset_id: Optional[UUID] = None  # For move operation


class TagImportItem(BaseModel):
    """Schema for importing tags from CSV/Excel"""
    tag_name: str
    asset_path: str  # e.g., "/OptiFlow Plant/Area 1/Equipment 5"
    tag_type: TagTypeEnum = TagTypeEnum.PHYSICAL
    address_config: Dict[str, Any]
    data_type: str = "float"
    unit: Optional[str] = None
    description: Optional[str] = None
    archive_enabled: bool = True


class TagImportRequest(BaseModel):
    """Schema for bulk tag import"""
    gateway_id: int
    tags: List[TagImportItem] = Field(..., min_items=1)
    overwrite_existing: bool = False
