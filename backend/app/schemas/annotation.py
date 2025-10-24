"""
Annotation schemas for API validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.annotation import AnnotationType, AnnotationPriority


# ===== Annotation Schemas =====

class AnnotationBase(BaseModel):
    """Base annotation schema"""
    type: AnnotationType = AnnotationType.COMMENT
    priority: Optional[AnnotationPriority] = AnnotationPriority.MEDIUM
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    device_id: Optional[UUID] = None
    tag_id: Optional[UUID] = None
    site_id: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_public: bool = True


class AnnotationCreate(AnnotationBase):
    """Schema for creating an annotation"""
    pass


class AnnotationUpdate(BaseModel):
    """Schema for updating an annotation"""
    type: Optional[AnnotationType] = None
    priority: Optional[AnnotationPriority] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    is_resolved: Optional[bool] = None


class AnnotationInDB(AnnotationBase):
    """Schema for annotation from database"""
    id: UUID
    created_by: Optional[UUID]
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolved_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnotationResponse(AnnotationInDB):
    """Schema for annotation API response"""
    comments_count: Optional[int] = 0


# ===== Annotation Comment Schemas =====

class AnnotationCommentBase(BaseModel):
    """Base annotation comment schema"""
    comment: str = Field(..., min_length=1)
    parent_comment_id: Optional[UUID] = None


class AnnotationCommentCreate(AnnotationCommentBase):
    """Schema for creating a comment"""
    pass


class AnnotationCommentUpdate(BaseModel):
    """Schema for updating a comment"""
    comment: str = Field(..., min_length=1)


class AnnotationCommentInDB(AnnotationCommentBase):
    """Schema for comment from database"""
    id: UUID
    annotation_id: UUID
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    is_edited: bool

    class Config:
        from_attributes = True


class AnnotationCommentResponse(AnnotationCommentInDB):
    """Schema for comment API response"""
    replies: Optional[List["AnnotationCommentResponse"]] = []


# Update forward references
AnnotationCommentResponse.model_rebuild()


# ===== Query Schemas =====

class AnnotationQuery(BaseModel):
    """Schema for querying annotations"""
    type: Optional[AnnotationType] = None
    priority: Optional[AnnotationPriority] = None
    device_id: Optional[UUID] = None
    tag_id: Optional[UUID] = None
    site_id: Optional[UUID] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_resolved: Optional[bool] = None
    created_by: Optional[UUID] = None
    tags: Optional[List[str]] = None
    skip: int = 0
    limit: int = 100


class AnnotationListResponse(BaseModel):
    """Schema for paginated annotation list"""
    annotations: List[AnnotationResponse]
    total: int
    skip: int
    limit: int
