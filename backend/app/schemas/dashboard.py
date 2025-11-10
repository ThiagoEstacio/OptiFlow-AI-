"""
Dashboard schemas for request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.dashboard import DashboardModule, WidgetType


# ==================== Grid Position ====================

class GridPosition(BaseModel):
    """Grid position for widget layout"""
    x: int = Field(..., ge=0, description="X position in grid")
    y: int = Field(..., ge=0, description="Y position in grid")
    w: int = Field(..., ge=1, le=12, description="Width in grid columns (1-12)")
    h: int = Field(..., ge=1, description="Height in grid rows")
    minW: Optional[int] = Field(None, ge=1, le=12, description="Minimum width")
    minH: Optional[int] = Field(None, ge=1, description="Minimum height")
    maxW: Optional[int] = Field(None, ge=1, le=12, description="Maximum width")
    maxH: Optional[int] = Field(None, ge=1, description="Maximum height")


# ==================== Widget Schemas ====================

class WidgetBase(BaseModel):
    """Base widget schema"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    type: WidgetType
    position: int = Field(default=0, ge=0)
    grid_position: GridPosition
    config: Dict[str, Any] = Field(default_factory=dict)
    data_config: Dict[str, Any] = Field(default_factory=dict)
    display_config: Dict[str, Any] = Field(default_factory=dict)
    refresh_interval: Optional[int] = Field(None, ge=5, le=3600, description="Refresh interval in seconds (5-3600)")


class WidgetCreate(WidgetBase):
    """Schema for creating a widget"""
    pass


class WidgetUpdate(BaseModel):
    """Schema for updating a widget"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    type: Optional[WidgetType] = None
    position: Optional[int] = Field(None, ge=0)
    grid_position: Optional[GridPosition] = None
    config: Optional[Dict[str, Any]] = None
    data_config: Optional[Dict[str, Any]] = None
    display_config: Optional[Dict[str, Any]] = None
    refresh_interval: Optional[int] = Field(None, ge=5, le=3600)


class WidgetResponse(WidgetBase):
    """Schema for widget response"""
    id: UUID
    dashboard_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Dashboard Schemas ====================

class DashboardBase(BaseModel):
    """Base dashboard schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    module: DashboardModule
    is_public: bool = Field(default=False, description="Public dashboards visible to all users")
    is_template: bool = Field(default=False, description="Template dashboards for quick creation")
    layout_config: Dict[str, Any] = Field(default_factory=dict)
    default_filters: Dict[str, Any] = Field(default_factory=dict)
    refresh_interval: int = Field(default=30, ge=5, le=300, description="Refresh interval in seconds (5-300)")
    auto_refresh: bool = True
    theme: str = Field(default="light", description="Theme: light or dark")
    show_legend: bool = True
    show_grid: bool = True


class DashboardCreate(DashboardBase):
    """Schema for creating a dashboard"""
    widgets: Optional[List[WidgetCreate]] = Field(default_factory=list, description="Initial widgets")


class DashboardUpdate(BaseModel):
    """Schema for updating a dashboard"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    module: Optional[DashboardModule] = None
    is_public: Optional[bool] = None
    is_template: Optional[bool] = None
    layout_config: Optional[Dict[str, Any]] = None
    default_filters: Optional[Dict[str, Any]] = None
    refresh_interval: Optional[int] = Field(None, ge=5, le=300)
    auto_refresh: Optional[bool] = None
    theme: Optional[str] = None
    show_legend: Optional[bool] = None
    show_grid: Optional[bool] = None


class DashboardResponse(DashboardBase):
    """Schema for dashboard response"""
    id: UUID
    user_id: UUID
    organization_id: UUID
    view_count: int
    last_viewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    widgets: List[WidgetResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DashboardListResponse(BaseModel):
    """Schema for dashboard list response (without widgets)"""
    id: UUID
    name: str
    description: Optional[str] = None
    module: DashboardModule
    is_public: bool
    is_template: bool
    view_count: int
    last_viewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    widget_count: int = Field(default=0, description="Number of widgets in dashboard")

    model_config = ConfigDict(from_attributes=True)


# ==================== Dashboard Share Schemas ====================

class DashboardShareBase(BaseModel):
    """Base dashboard share schema"""
    can_edit: bool = False
    can_delete: bool = False


class DashboardShareCreate(DashboardShareBase):
    """Schema for creating a dashboard share"""
    user_id: UUID


class DashboardShareUpdate(BaseModel):
    """Schema for updating a dashboard share"""
    can_edit: Optional[bool] = None
    can_delete: Optional[bool] = None


class DashboardShareResponse(DashboardShareBase):
    """Schema for dashboard share response"""
    id: UUID
    dashboard_id: UUID
    user_id: UUID
    created_at: datetime
    shared_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== Dashboard Template Schemas ====================

class DashboardTemplateBase(BaseModel):
    """Base dashboard template schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    module: DashboardModule
    config: Dict[str, Any] = Field(..., description="Full dashboard + widgets configuration")
    thumbnail_url: Optional[str] = None
    is_active: bool = True


class DashboardTemplateCreate(DashboardTemplateBase):
    """Schema for creating a dashboard template"""
    is_system: bool = Field(default=False, description="System templates can't be deleted")


class DashboardTemplateUpdate(BaseModel):
    """Schema for updating a dashboard template"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    module: Optional[DashboardModule] = None
    config: Optional[Dict[str, Any]] = None
    thumbnail_url: Optional[str] = None
    is_active: Optional[bool] = None


class DashboardTemplateResponse(DashboardTemplateBase):
    """Schema for dashboard template response"""
    id: UUID
    is_system: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Bulk Operations ====================

class DashboardCloneRequest(BaseModel):
    """Schema for cloning a dashboard"""
    name: Optional[str] = Field(None, description="New dashboard name, defaults to 'Copy of {original}'")
    module: Optional[DashboardModule] = Field(None, description="Module for new dashboard, defaults to original")


class DashboardFromTemplateRequest(BaseModel):
    """Schema for creating dashboard from template"""
    template_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    module: Optional[DashboardModule] = Field(None, description="Override template module")
    filters: Optional[Dict[str, Any]] = Field(None, description="Override default filters")


class WidgetBulkUpdateRequest(BaseModel):
    """Schema for bulk updating widget positions"""
    updates: List[Dict[str, Any]] = Field(..., description="List of {id, position, grid_position}")


# ==================== Query Filters ====================

class DashboardListFilters(BaseModel):
    """Schema for filtering dashboard list"""
    module: Optional[DashboardModule] = None
    is_public: Optional[bool] = None
    is_template: Optional[bool] = None
    search: Optional[str] = Field(None, description="Search in name and description")
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=100)


# ==================== Statistics ====================

class DashboardStats(BaseModel):
    """Dashboard usage statistics"""
    total_dashboards: int
    by_module: Dict[str, int]
    public_dashboards: int
    template_dashboards: int
    total_widgets: int
    by_widget_type: Dict[str, int]
    most_viewed: List[DashboardListResponse]
    recently_updated: List[DashboardListResponse]
