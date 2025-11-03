"""
Asset schemas for request/response validation
Implements hierarchical asset structure similar to PI Vision Asset Framework
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ============================================================================
# Asset Schemas
# ============================================================================

class AssetBase(BaseModel):
    """Base schema for Asset"""
    name: str = Field(..., min_length=1, max_length=255, description="Asset name")
    description: Optional[str] = Field(None, description="Asset description")
    asset_type: str = Field(..., description="Asset type: enterprise, site, area, unit, equipment, component")
    is_active: bool = Field(True, description="Whether asset is active")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata (manufacturer, model, location, etc)")

    @validator('asset_type')
    def validate_asset_type(cls, v):
        allowed_types = ['enterprise', 'site', 'area', 'unit', 'equipment', 'component']
        if v.lower() not in allowed_types:
            raise ValueError(f'asset_type must be one of: {", ".join(allowed_types)}')
        return v.lower()


class AssetCreate(AssetBase):
    """Schema for creating a new Asset"""
    parent_id: Optional[UUID] = Field(None, description="Parent asset ID for hierarchy")
    template_id: Optional[UUID] = Field(None, description="Template to instantiate from")


class AssetUpdate(BaseModel):
    """Schema for updating an Asset"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type: Optional[str] = None
    parent_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator('asset_type')
    def validate_asset_type(cls, v):
        if v is not None:
            allowed_types = ['enterprise', 'site', 'area', 'unit', 'equipment', 'component']
            if v.lower() not in allowed_types:
                raise ValueError(f'asset_type must be one of: {", ".join(allowed_types)}')
            return v.lower()
        return v


class AssetResponse(AssetBase):
    """Schema for Asset response"""
    id: UUID
    parent_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    # Computed properties
    level: Optional[int] = Field(None, description="Hierarchy level (0 = root)")
    full_path: Optional[str] = Field(None, description="Full hierarchical path")

    # Relationships
    children_count: Optional[int] = Field(None, description="Number of direct children")
    attributes_count: Optional[int] = Field(None, description="Number of attributes")

    @validator('asset_type', pre=True)
    def convert_asset_type(cls, v):
        """Convert enum to string"""
        if hasattr(v, 'value'):
            return v.value
        return v

    class Config:
        from_attributes = True


class AssetTreeNode(BaseModel):
    """Schema for hierarchical asset tree representation"""
    id: UUID
    name: str
    asset_type: str
    is_active: bool
    parent_id: Optional[UUID] = None
    level: int
    full_path: str
    children: List['AssetTreeNode'] = Field(default_factory=list)
    attributes_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# ============================================================================
# Asset Attribute Schemas
# ============================================================================

class AssetAttributeBase(BaseModel):
    """Base schema for AssetAttribute"""
    name: str = Field(..., min_length=1, max_length=255, description="Attribute name")
    description: Optional[str] = Field(None, description="Attribute description")
    attribute_type: str = Field(..., description="Attribute type: tag_reference, static, calculated")
    unit: Optional[str] = Field(None, max_length=50, description="Unit of measure")
    display_order: int = Field(0, description="Display order in UI")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Display settings, thresholds, etc")

    @validator('attribute_type')
    def validate_attribute_type(cls, v):
        allowed_types = ['tag_reference', 'static', 'calculated']
        if v.lower() not in allowed_types:
            raise ValueError(f'attribute_type must be one of: {", ".join(allowed_types)}')
        return v.lower()


class AssetAttributeCreate(AssetAttributeBase):
    """Schema for creating a new AssetAttribute"""
    asset_id: UUID = Field(..., description="Asset this attribute belongs to")
    tag_id: Optional[UUID] = Field(None, description="Tag ID for tag_reference type")
    static_value: Optional[str] = Field(None, max_length=500, description="Static value for static type")
    formula: Optional[str] = Field(None, description="Formula for calculated type")

    @validator('tag_id')
    def validate_tag_reference(cls, v, values):
        """Ensure tag_id is provided for tag_reference type"""
        if values.get('attribute_type') == 'tag_reference' and v is None:
            raise ValueError('tag_id is required for tag_reference attribute type')
        return v

    @validator('static_value')
    def validate_static_value(cls, v, values):
        """Ensure static_value is provided for static type"""
        if values.get('attribute_type') == 'static' and not v:
            raise ValueError('static_value is required for static attribute type')
        return v

    @validator('formula')
    def validate_formula(cls, v, values):
        """Ensure formula is provided for calculated type"""
        if values.get('attribute_type') == 'calculated' and not v:
            raise ValueError('formula is required for calculated attribute type')
        return v


class AssetAttributeUpdate(BaseModel):
    """Schema for updating an AssetAttribute"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    attribute_type: Optional[str] = None
    tag_id: Optional[UUID] = None
    static_value: Optional[str] = Field(None, max_length=500)
    formula: Optional[str] = None
    unit: Optional[str] = Field(None, max_length=50)
    display_order: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None

    @validator('attribute_type')
    def validate_attribute_type(cls, v):
        if v is not None:
            allowed_types = ['tag_reference', 'static', 'calculated']
            if v.lower() not in allowed_types:
                raise ValueError(f'attribute_type must be one of: {", ".join(allowed_types)}')
            return v.lower()
        return v


class AssetAttributeResponse(AssetAttributeBase):
    """Schema for AssetAttribute response"""
    id: UUID
    asset_id: UUID
    tag_id: Optional[UUID] = None
    static_value: Optional[str] = None
    formula: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Computed values
    current_value: Optional[Any] = Field(None, description="Current value (from tag or static)")
    calculated_value: Optional[float] = Field(None, description="Calculated value if applicable")

    @validator('attribute_type', pre=True)
    def convert_attribute_type(cls, v):
        """Convert enum to string"""
        if hasattr(v, 'value'):
            return v.value
        return v

    class Config:
        from_attributes = True


# ============================================================================
# Asset Template Schemas
# ============================================================================

class AttributeDefinition(BaseModel):
    """Schema for attribute definition in template"""
    name: str = Field(..., description="Attribute name")
    attribute_type: str = Field(..., description="Attribute type")
    unit: Optional[str] = None
    static_value: Optional[str] = None
    formula: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)

    @validator('attribute_type')
    def validate_attribute_type(cls, v):
        allowed_types = ['tag_reference', 'static', 'calculated']
        if v.lower() not in allowed_types:
            raise ValueError(f'attribute_type must be one of: {", ".join(allowed_types)}')
        return v.lower()


class AssetTemplateBase(BaseModel):
    """Base schema for AssetTemplate"""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    asset_type: str = Field(..., description="Asset type for instances")
    attribute_definitions: List[AttributeDefinition] = Field(default_factory=list, description="Attribute definitions")
    analyses: List[Dict[str, Any]] = Field(default_factory=list, description="Analysis definitions for future use")
    is_active: bool = Field(True, description="Whether template is active")

    @validator('asset_type')
    def validate_asset_type(cls, v):
        allowed_types = ['enterprise', 'site', 'area', 'unit', 'equipment', 'component']
        if v.lower() not in allowed_types:
            raise ValueError(f'asset_type must be one of: {", ".join(allowed_types)}')
        return v.lower()


class AssetTemplateCreate(AssetTemplateBase):
    """Schema for creating a new AssetTemplate"""
    pass


class AssetTemplateUpdate(BaseModel):
    """Schema for updating an AssetTemplate"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type: Optional[str] = None
    attribute_definitions: Optional[List[AttributeDefinition]] = None
    analyses: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None

    @validator('asset_type')
    def validate_asset_type(cls, v):
        if v is not None:
            allowed_types = ['enterprise', 'site', 'area', 'unit', 'equipment', 'component']
            if v.lower() not in allowed_types:
                raise ValueError(f'asset_type must be one of: {", ".join(allowed_types)}')
            return v.lower()
        return v


class AssetTemplateResponse(AssetTemplateBase):
    """Schema for AssetTemplate response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    instances_count: Optional[int] = Field(None, description="Number of asset instances using this template")

    @validator('asset_type', pre=True)
    def convert_asset_type(cls, v):
        """Convert enum to string"""
        if hasattr(v, 'value'):
            return v.value
        return v

    class Config:
        from_attributes = True


class AssetInstantiateRequest(BaseModel):
    """Schema for instantiating an asset from template"""
    template_id: UUID = Field(..., description="Template to instantiate from")
    name: str = Field(..., min_length=1, max_length=255, description="Name for new asset")
    parent_id: Optional[UUID] = Field(None, description="Parent asset ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    attribute_overrides: Dict[str, Any] = Field(default_factory=dict, description="Override template attribute values")


# Enable forward references for recursive types
AssetTreeNode.model_rebuild()
