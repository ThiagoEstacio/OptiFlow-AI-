"""
Dashboard API endpoints
Provides CRUD operations for dashboards, widgets, templates, and sharing
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.models.user import User
from app.models.dashboard import Dashboard, Widget, DashboardShare, DashboardTemplate, DashboardModule, WidgetType
from app.schemas.dashboard import (
    DashboardCreate, DashboardUpdate, DashboardResponse, DashboardListResponse,
    WidgetCreate, WidgetUpdate, WidgetResponse,
    DashboardShareCreate, DashboardShareResponse,
    DashboardTemplateCreate, DashboardTemplateUpdate, DashboardTemplateResponse,
    WidgetBulkUpdateRequest, DashboardCloneRequest
)
from app.core.deps import get_current_user

router = APIRouter(tags=["dashboards"])


# ============================================================================
# Dashboard CRUD
# ============================================================================

@router.post("", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new dashboard with optional widgets
    """
    # Create dashboard
    dashboard = Dashboard(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        name=dashboard_data.name,
        description=dashboard_data.description,
        module=dashboard_data.module,
        is_public=dashboard_data.is_public,
        is_template=dashboard_data.is_template,
        layout_config=dashboard_data.layout_config,
        default_filters=dashboard_data.default_filters,
        refresh_interval=dashboard_data.refresh_interval,
        auto_refresh=dashboard_data.auto_refresh,
        theme=dashboard_data.theme,
        show_legend=dashboard_data.show_legend,
        show_grid=dashboard_data.show_grid
    )
    
    db.add(dashboard)
    await db.flush()
    
    # Create widgets if provided
    if dashboard_data.widgets:
        for widget_data in dashboard_data.widgets:
            widget = Widget(
                dashboard_id=dashboard.id,
                title=widget_data.title,
                description=widget_data.description,
                type=widget_data.type,
                position=widget_data.position,
                grid_position=widget_data.grid_position,
                config=widget_data.config,
                data_config=widget_data.data_config,
                display_config=widget_data.display_config,
                refresh_interval=widget_data.refresh_interval
            )
            db.add(widget)
    
    await db.commit()
    await db.refresh(dashboard)
    
    return dashboard


@router.get("", response_model=List[DashboardListResponse])
async def list_dashboards(
    module: Optional[DashboardModule] = None,
    is_public: Optional[bool] = None,
    is_template: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all dashboards accessible by the current user
    """
    # Build query
    query = select(Dashboard).where(
        or_(
            Dashboard.user_id == current_user.id,
            Dashboard.is_public == True,
            Dashboard.id.in_(
                select(DashboardShare.dashboard_id).where(
                    DashboardShare.user_id == current_user.id
                )
            )
        )
    ).where(Dashboard.organization_id == current_user.organization_id)
    
    # Apply filters
    if module:
        query = query.where(Dashboard.module == module)
    if is_public is not None:
        query = query.where(Dashboard.is_public == is_public)
    if is_template is not None:
        query = query.where(Dashboard.is_template == is_template)
    
    # Order and paginate
    query = query.order_by(Dashboard.updated_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    dashboards = result.scalars().all()
    
    # Add widget count
    response = []
    for dashboard in dashboards:
        widget_count_query = select(func.count(Widget.id)).where(Widget.dashboard_id == dashboard.id)
        widget_count_result = await db.execute(widget_count_query)
        widget_count = widget_count_result.scalar()
        
        dashboard_dict = {
            "id": dashboard.id,
            "name": dashboard.name,
            "description": dashboard.description,
            "module": dashboard.module,
            "is_public": dashboard.is_public,
            "is_template": dashboard.is_template,
            "view_count": dashboard.view_count,
            "last_viewed_at": dashboard.last_viewed_at,
            "created_at": dashboard.created_at,
            "updated_at": dashboard.updated_at,
            "widget_count": widget_count
        }
        response.append(DashboardListResponse(**dashboard_dict))
    
    return response


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific dashboard with all widgets
    """
    # Check access
    query = select(Dashboard).where(
        Dashboard.id == dashboard_id,
        Dashboard.organization_id == current_user.organization_id,
        or_(
            Dashboard.user_id == current_user.id,
            Dashboard.is_public == True,
            Dashboard.id.in_(
                select(DashboardShare.dashboard_id).where(
                    DashboardShare.user_id == current_user.id
                )
            )
        )
    )
    
    result = await db.execute(query)
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    # Update view count
    dashboard.view_count += 1
    dashboard.last_viewed_at = func.now()
    await db.commit()
    await db.refresh(dashboard)
    
    return dashboard


@router.put("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: UUID,
    dashboard_data: DashboardUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a dashboard
    """
    # Check ownership or edit permission
    query = select(Dashboard).where(
        Dashboard.id == dashboard_id,
        Dashboard.organization_id == current_user.organization_id,
        or_(
            Dashboard.user_id == current_user.id,
            Dashboard.id.in_(
                select(DashboardShare.dashboard_id).where(
                    and_(
                        DashboardShare.user_id == current_user.id,
                        DashboardShare.can_edit == True
                    )
                )
            )
        )
    )
    
    result = await db.execute(query)
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found or no edit permission")
    
    # Update fields
    update_data = dashboard_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dashboard, field, value)
    
    await db.commit()
    await db.refresh(dashboard)
    
    return dashboard


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a dashboard
    """
    # Check ownership or delete permission
    query = select(Dashboard).where(
        Dashboard.id == dashboard_id,
        Dashboard.organization_id == current_user.organization_id,
        or_(
            Dashboard.user_id == current_user.id,
            Dashboard.id.in_(
                select(DashboardShare.dashboard_id).where(
                    and_(
                        DashboardShare.user_id == current_user.id,
                        DashboardShare.can_delete == True
                    )
                )
            )
        )
    )
    
    result = await db.execute(query)
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found or no delete permission")
    
    await db.delete(dashboard)
    await db.commit()


@router.post("/{dashboard_id}/clone", response_model=DashboardResponse)
async def clone_dashboard(
    dashboard_id: UUID,
    clone_data: DashboardCloneRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Clone an existing dashboard
    """
    # Get source dashboard
    query = select(Dashboard).where(
        Dashboard.id == dashboard_id,
        Dashboard.organization_id == current_user.organization_id,
        or_(
            Dashboard.user_id == current_user.id,
            Dashboard.is_public == True,
            Dashboard.id.in_(
                select(DashboardShare.dashboard_id).where(
                    DashboardShare.user_id == current_user.id
                )
            )
        )
    )
    
    result = await db.execute(query)
    source_dashboard = result.scalar_one_or_none()
    
    if not source_dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    # Create new dashboard
    new_dashboard = Dashboard(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        name=clone_data.name,
        description=clone_data.description or source_dashboard.description,
        module=source_dashboard.module,
        is_public=False,  # Clones are private by default
        is_template=False,
        layout_config=source_dashboard.layout_config,
        default_filters=source_dashboard.default_filters,
        refresh_interval=source_dashboard.refresh_interval,
        auto_refresh=source_dashboard.auto_refresh,
        theme=source_dashboard.theme,
        show_legend=source_dashboard.show_legend,
        show_grid=source_dashboard.show_grid
    )
    
    db.add(new_dashboard)
    await db.flush()
    
    # Clone widgets if requested
    if clone_data.include_widgets:
        widgets_query = select(Widget).where(Widget.dashboard_id == dashboard_id)
        widgets_result = await db.execute(widgets_query)
        widgets = widgets_result.scalars().all()
        
        for widget in widgets:
            new_widget = Widget(
                dashboard_id=new_dashboard.id,
                title=widget.title,
                description=widget.description,
                type=widget.type,
                position=widget.position,
                grid_position=widget.grid_position,
                config=widget.config,
                data_config=widget.data_config,
                display_config=widget.display_config,
                refresh_interval=widget.refresh_interval
            )
            db.add(new_widget)
    
    await db.commit()
    await db.refresh(new_dashboard)
    
    return new_dashboard


# ============================================================================
# Widget CRUD
# ============================================================================

@router.post("/{dashboard_id}/widgets", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED)
async def create_widget(
    dashboard_id: UUID,
    widget_data: WidgetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a widget to a dashboard
    """
    # Check dashboard access and edit permission
    query = select(Dashboard).where(
        Dashboard.id == dashboard_id,
        Dashboard.organization_id == current_user.organization_id,
        or_(
            Dashboard.user_id == current_user.id,
            Dashboard.id.in_(
                select(DashboardShare.dashboard_id).where(
                    and_(
                        DashboardShare.user_id == current_user.id,
                        DashboardShare.can_edit == True
                    )
                )
            )
        )
    )
    
    result = await db.execute(query)
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found or no edit permission")
    
    # Create widget
    widget = Widget(
        dashboard_id=dashboard_id,
        title=widget_data.title,
        description=widget_data.description,
        type=widget_data.type,
        position=widget_data.position,
        grid_position=widget_data.grid_position,
        config=widget_data.config,
        data_config=widget_data.data_config,
        display_config=widget_data.display_config,
        refresh_interval=widget_data.refresh_interval
    )
    
    db.add(widget)
    await db.commit()
    await db.refresh(widget)
    
    return widget


@router.put("/{dashboard_id}/widgets/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    dashboard_id: UUID,
    widget_id: UUID,
    widget_data: WidgetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a widget
    """
    # Check dashboard access
    dashboard_query = select(Dashboard).where(
        Dashboard.id == dashboard_id,
        Dashboard.organization_id == current_user.organization_id,
        or_(
            Dashboard.user_id == current_user.id,
            Dashboard.id.in_(
                select(DashboardShare.dashboard_id).where(
                    and_(
                        DashboardShare.user_id == current_user.id,
                        DashboardShare.can_edit == True
                    )
                )
            )
        )
    )
    
    dashboard_result = await db.execute(dashboard_query)
    dashboard = dashboard_result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found or no edit permission")
    
    # Get widget
    widget_query = select(Widget).where(
        Widget.id == widget_id,
        Widget.dashboard_id == dashboard_id
    )
    
    widget_result = await db.execute(widget_query)
    widget = widget_result.scalar_one_or_none()
    
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    # Update fields
    update_data = widget_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(widget, field, value)
    
    await db.commit()
    await db.refresh(widget)
    
    return widget


@router.delete("/{dashboard_id}/widgets/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    dashboard_id: UUID,
    widget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a widget from a dashboard
    """
    # Check dashboard access
    dashboard_query = select(Dashboard).where(
        Dashboard.id == dashboard_id,
        Dashboard.organization_id == current_user.organization_id,
        or_(
            Dashboard.user_id == current_user.id,
            Dashboard.id.in_(
                select(DashboardShare.dashboard_id).where(
                    and_(
                        DashboardShare.user_id == current_user.id,
                        DashboardShare.can_edit == True
                    )
                )
            )
        )
    )
    
    dashboard_result = await db.execute(dashboard_query)
    dashboard = dashboard_result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found or no edit permission")
    
    # Get and delete widget
    widget_query = select(Widget).where(
        Widget.id == widget_id,
        Widget.dashboard_id == dashboard_id
    )
    
    widget_result = await db.execute(widget_query)
    widget = widget_result.scalar_one_or_none()
    
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    await db.delete(widget)
    await db.commit()


@router.post("/{dashboard_id}/widgets/bulk-update", response_model=List[WidgetResponse])
async def bulk_update_widgets(
    dashboard_id: UUID,
    bulk_data: WidgetBulkUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk update widgets (useful for drag & drop layout changes)
    """
    # Check dashboard access
    dashboard_query = select(Dashboard).where(
        Dashboard.id == dashboard_id,
        Dashboard.organization_id == current_user.organization_id,
        or_(
            Dashboard.user_id == current_user.id,
            Dashboard.id.in_(
                select(DashboardShare.dashboard_id).where(
                    and_(
                        DashboardShare.user_id == current_user.id,
                        DashboardShare.can_edit == True
                    )
                )
            )
        )
    )
    
    dashboard_result = await db.execute(dashboard_query)
    dashboard = dashboard_result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found or no edit permission")
    
    # Update widgets
    updated_widgets = []
    for update_data in bulk_data.updates:
        widget_id = UUID(update_data["id"])
        
        widget_query = select(Widget).where(
            Widget.id == widget_id,
            Widget.dashboard_id == dashboard_id
        )
        
        widget_result = await db.execute(widget_query)
        widget = widget_result.scalar_one_or_none()
        
        if widget:
            for field, value in update_data.items():
                if field != "id" and hasattr(widget, field):
                    setattr(widget, field, value)
            updated_widgets.append(widget)
    
    await db.commit()
    
    for widget in updated_widgets:
        await db.refresh(widget)
    
    return updated_widgets


# ============================================================================
# Dashboard Templates
# ============================================================================

@router.get("/templates", response_model=List[DashboardTemplateResponse], tags=["dashboard-templates"])
async def list_templates(
    module: Optional[DashboardModule] = None,
    is_active: Optional[bool] = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    List all dashboard templates
    """
    query = select(DashboardTemplate)
    
    if module:
        query = query.where(DashboardTemplate.module == module)
    if is_active is not None:
        query = query.where(DashboardTemplate.is_active == is_active)
    
    query = query.order_by(DashboardTemplate.usage_count.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return templates


@router.post("/templates/{template_id}/use", response_model=DashboardResponse, tags=["dashboard-templates"])
async def use_template(
    template_id: UUID,
    name: str = Query(..., min_length=1, max_length=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a dashboard from a template
    """
    # Get template
    template_query = select(DashboardTemplate).where(
        DashboardTemplate.id == template_id,
        DashboardTemplate.is_active == True
    )
    
    template_result = await db.execute(template_query)
    template = template_result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Create dashboard from template
    config = template.config
    
    dashboard = Dashboard(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        name=name,
        description=config.get("description", ""),
        module=template.module,
        is_public=False,
        is_template=False,
        layout_config=config.get("layout_config", {}),
        default_filters=config.get("default_filters", {}),
        refresh_interval=config.get("refresh_interval", 30),
        auto_refresh=config.get("auto_refresh", True),
        theme=config.get("theme", "light"),
        show_legend=config.get("show_legend", True),
        show_grid=config.get("show_grid", True)
    )
    
    db.add(dashboard)
    await db.flush()
    
    # Create widgets from template
    for widget_config in config.get("widgets", []):
        widget = Widget(
            dashboard_id=dashboard.id,
            title=widget_config["title"],
            description=widget_config.get("description"),
            type=WidgetType(widget_config["type"]),
            position=widget_config.get("position", 0),
            grid_position=widget_config["grid_position"],
            config=widget_config.get("config", {}),
            data_config=widget_config.get("data_config", {}),
            display_config=widget_config.get("display_config", {}),
            refresh_interval=widget_config.get("refresh_interval")
        )
        db.add(widget)
    
    # Update usage count
    template.usage_count += 1
    
    await db.commit()
    await db.refresh(dashboard)
    
    return dashboard


# ============================================================================
# Dashboard Sharing
# ============================================================================

@router.post("/{dashboard_id}/share", response_model=DashboardShareResponse, tags=["dashboard-sharing"])
async def share_dashboard(
    dashboard_id: UUID,
    share_data: DashboardShareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Share a dashboard with another user
    """
    # Check ownership
    dashboard_query = select(Dashboard).where(
        Dashboard.id == dashboard_id,
        Dashboard.user_id == current_user.id,
        Dashboard.organization_id == current_user.organization_id
    )
    
    dashboard_result = await db.execute(dashboard_query)
    dashboard = dashboard_result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found or not owned by you")
    
    # Check if already shared
    existing_query = select(DashboardShare).where(
        DashboardShare.dashboard_id == dashboard_id,
        DashboardShare.user_id == share_data.user_id
    )
    
    existing_result = await db.execute(existing_query)
    existing_share = existing_result.scalar_one_or_none()
    
    if existing_share:
        raise HTTPException(status_code=400, detail="Dashboard already shared with this user")
    
    # Create share
    share = DashboardShare(
        dashboard_id=dashboard_id,
        user_id=share_data.user_id,
        can_edit=share_data.can_edit,
        can_delete=share_data.can_delete,
        shared_by=current_user.id
    )
    
    db.add(share)
    await db.commit()
    await db.refresh(share)
    
    return share


@router.delete("/{dashboard_id}/share/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["dashboard-sharing"])
async def unshare_dashboard(
    dashboard_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Unshare a dashboard
    """
    # Check ownership
    dashboard_query = select(Dashboard).where(
        Dashboard.id == dashboard_id,
        Dashboard.user_id == current_user.id
    )
    
    dashboard_result = await db.execute(dashboard_query)
    dashboard = dashboard_result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found or not owned by you")
    
    # Delete share
    share_query = select(DashboardShare).where(
        DashboardShare.dashboard_id == dashboard_id,
        DashboardShare.user_id == user_id
    )
    
    share_result = await db.execute(share_query)
    share = share_result.scalar_one_or_none()
    
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    await db.delete(share)
    await db.commit()
