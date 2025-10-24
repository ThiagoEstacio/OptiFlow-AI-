"""
Organization endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate, OrganizationResponse

router = APIRouter()


@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List all organizations
    """
    stmt = select(Organization).offset(skip).limit(limit)
    result = await db.execute(stmt)
    organizations = result.scalars().all()
    return organizations


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    organization_in: OrganizationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new organization
    """
    # Check if organization with same name exists
    stmt = select(Organization).where(Organization.name == organization_in.name)
    result = await db.execute(stmt)
    existing_org = result.scalar_one_or_none()

    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this name already exists"
        )

    # Create organization
    organization = Organization(**organization_in.model_dump())
    db.add(organization)
    await db.commit()
    await db.refresh(organization)

    return organization


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get organization by ID
    """
    stmt = select(Organization).where(Organization.id == organization_id)
    result = await db.execute(stmt)
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    return organization


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: UUID,
    organization_in: OrganizationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an organization
    """
    stmt = select(Organization).where(Organization.id == organization_id)
    result = await db.execute(stmt)
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Update fields
    update_data = organization_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization, field, value)

    await db.commit()
    await db.refresh(organization)

    return organization


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an organization
    """
    stmt = select(Organization).where(Organization.id == organization_id)
    result = await db.execute(stmt)
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    await db.delete(organization)
    await db.commit()

    return None
