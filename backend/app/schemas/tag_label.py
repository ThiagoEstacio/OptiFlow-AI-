"""
Tag Label schemas for API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID


class TagLabelBase(BaseModel):
    """Base schema for tag labels"""
    display_name: str = Field(..., description="User-friendly display name", max_length=255)
    short_name: Optional[str] = Field(None, description="Short name for dashboards", max_length=100)
    equipment_name: Optional[str] = Field(None, description="Equipment this tag belongs to", max_length=255)
    area_name: Optional[str] = Field(None, description="Area/location of the equipment", max_length=255)
    system_name: Optional[str] = Field(None, description="System this tag belongs to", max_length=255)
    custom_description: Optional[str] = Field(None, description="Custom description")
    notes: Optional[str] = Field(None, description="Internal notes")
    is_visible: bool = Field(True, description="Show in UI")
    is_favorite: bool = Field(False, description="Quick access favorite")


class TagLabelCreate(TagLabelBase):
    """Schema for creating a tag label"""
    tag_id: UUID = Field(..., description="ID of the tag to label")
    created_by: Optional[str] = Field(None, description="User creating the label")


class TagLabelUpdate(BaseModel):
    """Schema for updating a tag label"""
    display_name: Optional[str] = Field(None, description="User-friendly display name", max_length=255)
    short_name: Optional[str] = Field(None, description="Short name for dashboards", max_length=100)
    equipment_name: Optional[str] = Field(None, description="Equipment this tag belongs to", max_length=255)
    area_name: Optional[str] = Field(None, description="Area/location of the equipment", max_length=255)
    system_name: Optional[str] = Field(None, description="System this tag belongs to", max_length=255)
    custom_description: Optional[str] = Field(None, description="Custom description")
    notes: Optional[str] = Field(None, description="Internal notes")
    is_visible: Optional[bool] = Field(None, description="Show in UI")
    is_favorite: Optional[bool] = Field(None, description="Quick access favorite")
    updated_by: Optional[str] = Field(None, description="User updating the label")


class TagLabelResponse(TagLabelBase):
    """Schema for tag label responses"""
    id: UUID
    tag_id: UUID
    created_by: Optional[str]
    updated_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TagWithLabel(BaseModel):
    """Tag with its label information"""
    # Original tag info
    id: UUID
    name: str  # Original technical name (e.g., ARZ_GATES_GATE01_POSICAO_PV)
    description: Optional[str]
    unit: Optional[str]
    data_type: str
    category: str
    is_active: bool
    
    # Label info (if exists)
    label: Optional[TagLabelResponse] = None
    
    # Display info (prioritizes label over original)
    effective_name: str = Field(..., description="Display name if label exists, otherwise original name")
    effective_description: Optional[str] = Field(None, description="Custom description if exists, otherwise original")

    class Config:
        from_attributes = True


class TagLabelSearchParams(BaseModel):
    """Search parameters for tag labels"""
    query: Optional[str] = Field(None, description="Search in display name, equipment, area")
    area_name: Optional[str] = Field(None, description="Filter by area")
    equipment_name: Optional[str] = Field(None, description="Filter by equipment")
    system_name: Optional[str] = Field(None, description="Filter by system")
    is_favorite: Optional[bool] = Field(None, description="Filter favorites")
    is_visible: Optional[bool] = Field(True, description="Filter visibility")
    limit: int = Field(100, ge=1, le=1000, description="Max results")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class TagLabelBulkCreate(BaseModel):
    """Bulk create tag labels"""
    labels: list[TagLabelCreate] = Field(..., description="List of labels to create")
    
    @validator('labels')
    def validate_labels(cls, v):
        if len(v) > 100:
            raise ValueError('Maximum 100 labels per bulk operation')
        return v


class TagLabelStats(BaseModel):
    """Statistics about tag labels"""
    total_tags: int = Field(..., description="Total number of tags")
    labeled_tags: int = Field(..., description="Tags with labels")
    unlabeled_tags: int = Field(..., description="Tags without labels")
    favorite_tags: int = Field(..., description="Favorite tags")
    areas_count: int = Field(..., description="Number of unique areas")
    equipments_count: int = Field(..., description="Number of unique equipments")
    systems_count: int = Field(..., description="Number of unique systems")
