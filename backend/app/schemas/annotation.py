"""
Annotation Schemas

Pydantic schemas for annotation validation and serialization.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.models.annotation import AnnotationType, AnnotationSeverity


# ==================== Base Schemas ====================

class AnnotationBase(BaseModel):
    """Base schema for annotation"""
    annotation_type: AnnotationType = Field(AnnotationType.COMMENT, description="Type of annotation")
    severity: AnnotationSeverity = Field(AnnotationSeverity.INFO, description="Severity level")
    title: str = Field(..., min_length=1, max_length=255, description="Annotation title")
    content: Optional[str] = Field(None, description="Annotation content (supports Markdown)")
    start_time: datetime = Field(..., description="Start timestamp")
    end_time: Optional[datetime] = Field(None, description="End timestamp (for range annotations)")
    tag_id: Optional[UUID] = Field(None, description="Associated tag ID")
    device_id: Optional[UUID] = Field(None, description="Associated device ID")
    site_id: Optional[UUID] = Field(None, description="Associated site ID")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    color: Optional[str] = Field(None, description="Color for visualization (hex code)")
    is_public: bool = Field(True, description="Public or private visibility")
    pinned: bool = Field(False, description="Pinned to top")

    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Ensure end_time is after start_time"""
        if v is not None and 'start_time' in values:
            if v <= values['start_time']:
                raise ValueError('end_time must be after start_time')
        return v

    @validator('color')
    def validate_color(cls, v):
        """Validate hex color code"""
        if v is not None:
            if not v.startswith('#') or len(v) != 7:
                raise ValueError('color must be a valid hex code (e.g., #FF5733)')
            # Check if valid hex
            try:
                int(v[1:], 16)
            except ValueError:
                raise ValueError('color must be a valid hex code')
        return v

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not just whitespace"""
        if not v or not v.strip():
            raise ValueError('title cannot be empty or whitespace')
        return v.strip()


# ==================== Create Schemas ====================

class AnnotationCreate(AnnotationBase):
    """Schema for creating a new annotation"""
    created_by: str = Field(..., min_length=1, max_length=255, description="User ID or username")
    created_by_name: Optional[str] = Field(None, max_length=255, description="Display name")

    class Config:
        schema_extra = {
            "example": {
                "annotation_type": "event",
                "severity": "warning",
                "title": "Motor vibration detected",
                "content": "Unusual vibration detected on Motor #3. Maintenance scheduled.",
                "start_time": "2025-01-20T14:30:00Z",
                "end_time": None,
                "tag_id": "123e4567-e89b-12d3-a456-426614174000",
                "device_id": None,
                "site_id": None,
                "created_by": "operator1",
                "created_by_name": "John Operator",
                "metadata": {"maintenance_ticket": "MT-2025-001"},
                "color": "#FFA500",
                "is_public": True,
                "pinned": False
            }
        }


class AnnotationBulkCreate(BaseModel):
    """Schema for bulk creating annotations"""
    annotations: List[AnnotationCreate] = Field(..., min_items=1, max_items=100)


# ==================== Update Schemas ====================

class AnnotationUpdate(BaseModel):
    """Schema for updating an annotation"""
    annotation_type: Optional[AnnotationType] = None
    severity: Optional[AnnotationSeverity] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    tag_id: Optional[UUID] = None
    device_id: Optional[UUID] = None
    site_id: Optional[UUID] = None
    metadata: Optional[dict] = None
    color: Optional[str] = None
    is_public: Optional[bool] = None
    pinned: Optional[bool] = None

    @validator('color')
    def validate_color(cls, v):
        """Validate hex color code"""
        if v is not None:
            if not v.startswith('#') or len(v) != 7:
                raise ValueError('color must be a valid hex code (e.g., #FF5733)')
            try:
                int(v[1:], 16)
            except ValueError:
                raise ValueError('color must be a valid hex code')
        return v

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not just whitespace"""
        if v is not None and (not v or not v.strip()):
            raise ValueError('title cannot be empty or whitespace')
        return v.strip() if v else None

    class Config:
        schema_extra = {
            "example": {
                "title": "Updated title",
                "content": "Updated content with additional details",
                "severity": "error",
                "pinned": True
            }
        }


# ==================== Response Schemas ====================

class AnnotationResponse(AnnotationBase):
    """Schema for annotation response"""
    id: UUID
    created_by: str
    created_by_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    duration_seconds: float = Field(0.0, description="Duration in seconds (for range annotations)")
    is_range: bool = Field(False, description="Whether this is a range annotation")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "annotation_type": "event",
                "severity": "warning",
                "title": "Motor vibration detected",
                "content": "Unusual vibration detected on Motor #3. Maintenance scheduled.",
                "start_time": "2025-01-20T14:30:00Z",
                "end_time": None,
                "tag_id": "123e4567-e89b-12d3-a456-426614174001",
                "device_id": None,
                "site_id": None,
                "created_by": "operator1",
                "created_by_name": "John Operator",
                "metadata": {"maintenance_ticket": "MT-2025-001"},
                "color": "#FFA500",
                "is_public": True,
                "pinned": False,
                "created_at": "2025-01-20T14:30:00Z",
                "updated_at": "2025-01-20T14:30:00Z",
                "is_deleted": False,
                "duration_seconds": 0.0,
                "is_range": False
            }
        }


class AnnotationListResponse(BaseModel):
    """Schema for paginated annotation list"""
    total: int = Field(..., description="Total number of annotations")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    annotations: List[AnnotationResponse] = Field(..., description="List of annotations")

    class Config:
        schema_extra = {
            "example": {
                "total": 150,
                "page": 1,
                "page_size": 20,
                "annotations": []
            }
        }


# ==================== Query Schemas ====================

class AnnotationQuery(BaseModel):
    """Schema for querying annotations"""
    tag_ids: Optional[List[UUID]] = Field(None, description="Filter by tag IDs")
    device_ids: Optional[List[UUID]] = Field(None, description="Filter by device IDs")
    site_ids: Optional[List[UUID]] = Field(None, description="Filter by site IDs")
    annotation_types: Optional[List[AnnotationType]] = Field(None, description="Filter by types")
    severities: Optional[List[AnnotationSeverity]] = Field(None, description="Filter by severities")
    start_time: Optional[datetime] = Field(None, description="Start of time range")
    end_time: Optional[datetime] = Field(None, description="End of time range")
    created_by: Optional[str] = Field(None, description="Filter by creator")
    is_public: Optional[bool] = Field(None, description="Filter by visibility")
    pinned_only: bool = Field(False, description="Return only pinned annotations")
    include_deleted: bool = Field(False, description="Include deleted annotations")
    search: Optional[str] = Field(None, max_length=255, description="Search in title and content")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    order_by: str = Field("start_time", description="Order by field")
    order_direction: str = Field("desc", description="Order direction (asc/desc)")

    @validator('order_direction')
    def validate_order_direction(cls, v):
        """Validate order direction"""
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('order_direction must be "asc" or "desc"')
        return v.lower()

    @validator('order_by')
    def validate_order_by(cls, v):
        """Validate order by field"""
        allowed_fields = ['start_time', 'created_at', 'updated_at', 'title', 'severity']
        if v not in allowed_fields:
            raise ValueError(f'order_by must be one of: {", ".join(allowed_fields)}')
        return v

    class Config:
        schema_extra = {
            "example": {
                "tag_ids": ["123e4567-e89b-12d3-a456-426614174000"],
                "annotation_types": ["event", "alarm"],
                "severities": ["warning", "error"],
                "start_time": "2025-01-01T00:00:00Z",
                "end_time": "2025-01-31T23:59:59Z",
                "page": 1,
                "page_size": 20,
                "order_by": "start_time",
                "order_direction": "desc"
            }
        }


# ==================== Statistics Schemas ====================

class AnnotationStatistics(BaseModel):
    """Schema for annotation statistics"""
    total_annotations: int = Field(0, description="Total number of annotations")
    by_type: dict = Field(default_factory=dict, description="Count by annotation type")
    by_severity: dict = Field(default_factory=dict, description="Count by severity")
    recent_count_24h: int = Field(0, description="Annotations created in last 24 hours")
    recent_count_7d: int = Field(0, description="Annotations created in last 7 days")
    pinned_count: int = Field(0, description="Number of pinned annotations")
    range_annotations: int = Field(0, description="Number of range annotations")
    point_annotations: int = Field(0, description="Number of point annotations")

    class Config:
        schema_extra = {
            "example": {
                "total_annotations": 150,
                "by_type": {
                    "comment": 50,
                    "event": 40,
                    "alarm": 30,
                    "maintenance": 20,
                    "note": 10
                },
                "by_severity": {
                    "info": 80,
                    "warning": 40,
                    "error": 20,
                    "critical": 10
                },
                "recent_count_24h": 5,
                "recent_count_7d": 25,
                "pinned_count": 3,
                "range_annotations": 30,
                "point_annotations": 120
            }
        }
