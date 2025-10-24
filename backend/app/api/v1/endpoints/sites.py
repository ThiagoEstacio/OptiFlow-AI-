"""
Site endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.models.organization import Site
from app.schemas.organization import SiteCreate, SiteUpdate, SiteResponse

router = APIRouter()


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
async def create_site(
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
