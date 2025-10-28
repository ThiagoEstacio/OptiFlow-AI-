"""
Tag endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate, TagResponse

router = APIRouter()


@router.get("/", response_model=List[TagResponse])
async def list_tags(
    skip: int = 0,
    limit: int = 100,
    device_id: UUID = None,
    db: AsyncSession = Depends(get_db)
):
    """List all tags"""
    stmt = select(Tag)

    if device_id:
        stmt = stmt.where(Tag.device_id == device_id)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    tags = result.scalars().all()
    return tags


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_in: TagCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new tag"""
    tag = Tag(**tag_in.model_dump())
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get tag by ID"""
    stmt = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    return tag


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: UUID,
    tag_in: TagUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a tag"""
    stmt = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    # Update only provided fields
    update_data = tag_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)

    await db.commit()
    await db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a tag"""
    stmt = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    await db.delete(tag)
    await db.commit()
    return None


@router.get("/{tag_id}/latest")
async def get_latest_tag_value(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get latest tag value"""
    stmt = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    return {
        "tag_id": str(tag.id),
        "value": tag.last_value,
        "quality": tag.last_quality,
        "timestamp": tag.last_timestamp
    }
