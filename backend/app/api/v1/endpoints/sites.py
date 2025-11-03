"""
Site endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.session import get_db
from app.models.organization import Site
from app.schemas.site import SiteCreate, SiteUpdate, SiteResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/", response_model=List[SiteResponse])
async def list_sites(
    skip: int = 0,
    limit: int = 100,
    organization_id: UUID = None,
    db: AsyncSession = Depends(get_db)
):
    """List all sites"""
    stmt = select(Site)

    if organization_id:
        stmt = stmt.where(Site.organization_id == organization_id)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    sites = result.scalars().all()
    return sites


@router.post("/", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")  # 🔒 Limit site creation
async def create_site(
    request: Request,
    site_in: SiteCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new site"""
    site = Site(**site_in.model_dump())
    db.add(site)
    await db.commit()
    await db.refresh(site)
    return site


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(
    site_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get site by ID"""
    stmt = select(Site).where(Site.id == site_id)
    result = await db.execute(stmt)
    site = result.scalar_one_or_none()

    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )

    return site


@router.put("/{site_id}", response_model=SiteResponse)
@limiter.limit("30/minute")  # 🔒 Limit site updates
async def update_site(
    request: Request,
    site_id: UUID,
    site_in: SiteUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a site"""
    stmt = select(Site).where(Site.id == site_id)
    result = await db.execute(stmt)
    site = result.scalar_one_or_none()

    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )

    # Update only provided fields
    update_data = site_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(site, field, value)

    await db.commit()
    await db.refresh(site)
    return site


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")  # 🔒 Limit site deletions
async def delete_site(
    request: Request,
    site_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a site"""
    stmt = select(Site).where(Site.id == site_id)
    result = await db.execute(stmt)
    site = result.scalar_one_or_none()

    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )

    await db.delete(site)
    await db.commit()
    return None
