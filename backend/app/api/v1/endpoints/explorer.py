"""
Tag Explorer API Endpoints

Provides hierarchical browsing and search of tags across the organization structure.

Hierarchy: Organization -> Sites -> Devices -> Tags

Features:
- Tree-based navigation
- Search and filtering
- Tag statistics and health
- Batch operations
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from uuid import UUID

from app.api.deps import get_db
from app.models.organization import Organization, Site
from app.models.device import Device, DeviceStatus
from app.models.tag import Tag, TagCategory, TagDataType
from loguru import logger

router = APIRouter()


# ==================== Pydantic Schemas ====================

from pydantic import BaseModel, Field


class TagSummary(BaseModel):
    """Summary of a tag"""
    id: UUID
    name: str
    description: Optional[str]
    address: str
    data_type: TagDataType
    unit: Optional[str]
    category: TagCategory
    is_active: bool
    last_value: Optional[str]
    last_quality: Optional[str]
    last_timestamp: Optional[str]

    class Config:
        from_attributes = True


class DeviceSummary(BaseModel):
    """Summary of a device with tag count"""
    id: UUID
    name: str
    description: Optional[str]
    protocol_type: str
    connection_string: str
    status: DeviceStatus
    is_active: bool
    tag_count: int = 0
    active_tag_count: int = 0

    class Config:
        from_attributes = True


class SiteSummary(BaseModel):
    """Summary of a site with device and tag counts"""
    id: UUID
    name: str
    description: Optional[str]
    location: Optional[str]
    is_active: bool
    device_count: int = 0
    tag_count: int = 0

    class Config:
        from_attributes = True


class OrganizationSummary(BaseModel):
    """Summary of an organization with site, device, and tag counts"""
    id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    site_count: int = 0
    device_count: int = 0
    tag_count: int = 0

    class Config:
        from_attributes = True


class ExplorerTreeNode(BaseModel):
    """Tree node for explorer"""
    id: str
    name: str
    type: str  # "organization", "site", "device", "tag"
    description: Optional[str] = None
    is_active: bool = True
    children_count: int = 0
    metadata: dict = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Production Site",
                "type": "site",
                "description": "Main production facility",
                "is_active": True,
                "children_count": 15,
                "metadata": {"location": "Building A"}
            }
        }


class SearchResult(BaseModel):
    """Search result item"""
    id: UUID
    name: str
    type: str  # "tag", "device", "site", "organization"
    description: Optional[str]
    path: str  # Full hierarchical path
    metadata: dict = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Temperature Sensor 1",
                "type": "tag",
                "description": "Motor temperature",
                "path": "Acme Corp / Production Site / PLC-1 / Temperature Sensor 1",
                "metadata": {"unit": "°C", "category": "process"}
            }
        }


class SearchResponse(BaseModel):
    """Search response"""
    results: List[SearchResult]
    total: int
    query: str

    class Config:
        schema_extra = {
            "example": {
                "results": [],
                "total": 0,
                "query": "temperature"
            }
        }


# ==================== Organization Level ====================

@router.get("/organizations", response_model=List[OrganizationSummary])
async def list_organizations(
    include_inactive: bool = Query(False, description="Include inactive organizations"),
    db: Session = Depends(get_db)
):
    """
    List all organizations with counts.

    Returns organizations with site, device, and tag counts.
    """
    logger.info("Listing organizations")

    query = db.query(Organization)

    if not include_inactive:
        query = query.filter(Organization.is_active == True)

    organizations = query.all()

    results = []
    for org in organizations:
        # Count sites
        site_count = db.query(Site).filter(Site.organization_id == org.id).count()

        # Count devices
        device_count = db.query(Device).join(Site).filter(
            Site.organization_id == org.id
        ).count()

        # Count tags
        tag_count = db.query(Tag).join(Device).join(Site).filter(
            Site.organization_id == org.id
        ).count()

        results.append(OrganizationSummary(
            id=org.id,
            name=org.name,
            description=org.description,
            is_active=org.is_active,
            site_count=site_count,
            device_count=device_count,
            tag_count=tag_count
        ))

    return results


@router.get("/organizations/{org_id}/tree", response_model=List[ExplorerTreeNode])
async def get_organization_tree(
    org_id: UUID,
    include_inactive: bool = Query(False, description="Include inactive items"),
    db: Session = Depends(get_db)
):
    """
    Get organization tree structure (sites under organization).

    Returns first level children (sites).
    """
    logger.info(f"Getting tree for organization {org_id}")

    # Verify organization exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {org_id} not found"
        )

    # Get sites
    site_query = db.query(Site).filter(Site.organization_id == org_id)

    if not include_inactive:
        site_query = site_query.filter(Site.is_active == True)

    sites = site_query.all()

    results = []
    for site in sites:
        # Count devices under this site
        device_count = db.query(Device).filter(Device.site_id == site.id).count()

        results.append(ExplorerTreeNode(
            id=str(site.id),
            name=site.name,
            type="site",
            description=site.description,
            is_active=site.is_active,
            children_count=device_count,
            metadata={
                "location": site.location,
                "timezone": site.timezone
            }
        ))

    return results


# ==================== Site Level ====================

@router.get("/sites/{site_id}/tree", response_model=List[ExplorerTreeNode])
async def get_site_tree(
    site_id: UUID,
    include_inactive: bool = Query(False, description="Include inactive items"),
    db: Session = Depends(get_db)
):
    """
    Get site tree structure (devices under site).

    Returns first level children (devices).
    """
    logger.info(f"Getting tree for site {site_id}")

    # Verify site exists
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site {site_id} not found"
        )

    # Get devices
    device_query = db.query(Device).filter(Device.site_id == site_id)

    if not include_inactive:
        device_query = device_query.filter(Device.is_active == True)

    devices = device_query.all()

    results = []
    for device in devices:
        # Count tags under this device
        tag_count = db.query(Tag).filter(Tag.device_id == device.id).count()

        results.append(ExplorerTreeNode(
            id=str(device.id),
            name=device.name,
            type="device",
            description=device.description,
            is_active=device.is_active,
            children_count=tag_count,
            metadata={
                "protocol_type": device.protocol_type,
                "status": device.status.value,
                "model": device.model,
                "ip_address": device.ip_address
            }
        ))

    return results


# ==================== Device Level ====================

@router.get("/devices/{device_id}/tags", response_model=List[TagSummary])
async def get_device_tags(
    device_id: UUID,
    include_inactive: bool = Query(False, description="Include inactive tags"),
    category: Optional[TagCategory] = Query(None, description="Filter by category"),
    data_type: Optional[TagDataType] = Query(None, description="Filter by data type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get all tags for a device with filtering and pagination.
    """
    logger.info(f"Getting tags for device {device_id}")

    # Verify device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found"
        )

    # Build query
    query = db.query(Tag).filter(Tag.device_id == device_id)

    if not include_inactive:
        query = query.filter(Tag.is_active == True)

    if category:
        query = query.filter(Tag.category == category)

    if data_type:
        query = query.filter(Tag.data_type == data_type)

    # Pagination
    offset = (page - 1) * page_size
    tags = query.order_by(Tag.name).offset(offset).limit(page_size).all()

    return tags


# ==================== Search ====================

@router.get("/search", response_model=SearchResponse)
async def search_tags(
    query: str = Query(..., min_length=2, max_length=255, description="Search query"),
    search_type: Optional[str] = Query(None, description="Filter by type (tag, device, site, organization)"),
    org_id: Optional[UUID] = Query(None, description="Filter by organization"),
    site_id: Optional[UUID] = Query(None, description="Filter by site"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db)
):
    """
    Search across tags, devices, sites, and organizations.

    Returns results with full hierarchical path for context.
    """
    logger.info(f"Searching for '{query}' (type: {search_type})")

    results = []
    search_term = f"%{query}%"

    # Search tags
    if not search_type or search_type == "tag":
        tag_query = db.query(Tag).join(Device).join(Site).join(Organization)

        # Apply filters
        if org_id:
            tag_query = tag_query.filter(Site.organization_id == org_id)
        if site_id:
            tag_query = tag_query.filter(Device.site_id == site_id)

        # Search in name, description, address
        tag_query = tag_query.filter(
            or_(
                Tag.name.ilike(search_term),
                Tag.description.ilike(search_term),
                Tag.address.ilike(search_term)
            )
        ).filter(Tag.is_active == True)

        tags = tag_query.limit(limit).all()

        for tag in tags:
            device = tag.device
            site = device.site
            org = site.organization

            path = f"{org.name} / {site.name} / {device.name} / {tag.name}"

            results.append(SearchResult(
                id=tag.id,
                name=tag.name,
                type="tag",
                description=tag.description,
                path=path,
                metadata={
                    "unit": tag.unit,
                    "category": tag.category.value,
                    "data_type": tag.data_type.value,
                    "device_id": str(device.id),
                    "site_id": str(site.id),
                    "organization_id": str(org.id)
                }
            ))

    # Search devices
    if not search_type or search_type == "device":
        device_query = db.query(Device).join(Site).join(Organization)

        # Apply filters
        if org_id:
            device_query = device_query.filter(Site.organization_id == org_id)
        if site_id:
            device_query = device_query.filter(Device.site_id == site_id)

        # Search in name, description
        device_query = device_query.filter(
            or_(
                Device.name.ilike(search_term),
                Device.description.ilike(search_term)
            )
        ).filter(Device.is_active == True)

        devices = device_query.limit(limit).all()

        for device in devices:
            site = device.site
            org = site.organization

            path = f"{org.name} / {site.name} / {device.name}"

            # Count tags
            tag_count = db.query(Tag).filter(Tag.device_id == device.id).count()

            results.append(SearchResult(
                id=device.id,
                name=device.name,
                type="device",
                description=device.description,
                path=path,
                metadata={
                    "protocol_type": device.protocol_type,
                    "status": device.status.value,
                    "tag_count": tag_count,
                    "site_id": str(site.id),
                    "organization_id": str(org.id)
                }
            ))

    # Search sites
    if not search_type or search_type == "site":
        site_query = db.query(Site).join(Organization)

        # Apply filters
        if org_id:
            site_query = site_query.filter(Site.organization_id == org_id)

        # Search in name, description, location
        site_query = site_query.filter(
            or_(
                Site.name.ilike(search_term),
                Site.description.ilike(search_term),
                Site.location.ilike(search_term)
            )
        ).filter(Site.is_active == True)

        sites = site_query.limit(limit).all()

        for site in sites:
            org = site.organization
            path = f"{org.name} / {site.name}"

            # Count devices
            device_count = db.query(Device).filter(Device.site_id == site.id).count()

            results.append(SearchResult(
                id=site.id,
                name=site.name,
                type="site",
                description=site.description,
                path=path,
                metadata={
                    "location": site.location,
                    "device_count": device_count,
                    "organization_id": str(org.id)
                }
            ))

    # Search organizations
    if not search_type or search_type == "organization":
        org_query = db.query(Organization)

        # Apply filter
        if org_id:
            org_query = org_query.filter(Organization.id == org_id)

        # Search in name, description
        org_query = org_query.filter(
            or_(
                Organization.name.ilike(search_term),
                Organization.description.ilike(search_term)
            )
        ).filter(Organization.is_active == True)

        orgs = org_query.limit(limit).all()

        for org in orgs:
            path = org.name

            # Count sites
            site_count = db.query(Site).filter(Site.organization_id == org.id).count()

            results.append(SearchResult(
                id=org.id,
                name=org.name,
                type="organization",
                description=org.description,
                path=path,
                metadata={
                    "site_count": site_count
                }
            ))

    # Sort results by relevance (exact matches first, then alphabetically)
    results.sort(key=lambda x: (not x.name.lower().startswith(query.lower()), x.name.lower()))

    # Limit total results
    results = results[:limit]

    return SearchResponse(
        results=results,
        total=len(results),
        query=query
    )


# ==================== Quick Stats ====================

@router.get("/stats/summary")
async def get_explorer_stats(
    org_id: Optional[UUID] = Query(None, description="Filter by organization"),
    site_id: Optional[UUID] = Query(None, description="Filter by site"),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for the explorer.

    Returns counts and health metrics.
    """
    logger.info("Getting explorer statistics")

    # Build base queries
    tag_query = db.query(Tag).join(Device).join(Site)
    device_query = db.query(Device).join(Site)
    site_query = db.query(Site)

    # Apply filters
    if org_id:
        tag_query = tag_query.filter(Site.organization_id == org_id)
        device_query = device_query.filter(Site.organization_id == org_id)
        site_query = site_query.filter(Site.organization_id == org_id)

    if site_id:
        tag_query = tag_query.filter(Device.site_id == site_id)
        device_query = device_query.filter(Device.site_id == site_id)
        site_query = site_query.filter(Site.id == site_id)

    # Count totals
    total_tags = tag_query.count()
    active_tags = tag_query.filter(Tag.is_active == True).count()

    total_devices = device_query.count()
    active_devices = device_query.filter(Device.is_active == True).count()
    connected_devices = device_query.filter(Device.status == DeviceStatus.CONNECTED).count()

    total_sites = site_query.count()
    active_sites = site_query.filter(Site.is_active == True).count()

    # Count by category
    tags_by_category = {}
    for category in TagCategory:
        count = tag_query.filter(Tag.category == category).count()
        tags_by_category[category.value] = count

    # Count by data type
    tags_by_type = {}
    for data_type in TagDataType:
        count = tag_query.filter(Tag.data_type == data_type).count()
        tags_by_type[data_type.value] = count

    return {
        "tags": {
            "total": total_tags,
            "active": active_tags,
            "inactive": total_tags - active_tags,
            "by_category": tags_by_category,
            "by_type": tags_by_type
        },
        "devices": {
            "total": total_devices,
            "active": active_devices,
            "connected": connected_devices,
            "disconnected": total_devices - connected_devices
        },
        "sites": {
            "total": total_sites,
            "active": active_sites,
            "inactive": total_sites - active_sites
        }
    }


# ==================== Favorites (Future Enhancement) ====================

@router.get("/favorites")
async def get_favorite_tags(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Get user's favorite tags.

    Note: This is a placeholder for future user preferences implementation.
    """
    # TODO: Implement user favorites
    return {
        "user_id": user_id,
        "favorites": [],
        "message": "Favorites feature coming soon"
    }
