"""
Tag endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.session import get_db
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate, TagResponse
from app.services.opcua_tag_reader import update_tag_values_from_opcua

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


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
@limiter.limit("200/minute")  # 🔒 Limit tag creation (increased for batch imports)
async def create_tag(
    request: Request,
    tag_in: TagCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new tag"""
    # Map schema fields to model fields
    tag_data = tag_in.model_dump()
    
    # Rename fields to match database column names
    if 'scale_factor' in tag_data:
        tag_data['scale'] = tag_data.pop('scale_factor')
    if 'enabled' in tag_data:
        tag_data['is_active'] = tag_data.pop('enabled')
    if 'log_enabled' in tag_data:
        tag_data['enable_quality_check'] = tag_data.pop('log_enabled')
    
    tag = Tag(**tag_data)
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
@limiter.limit("50/minute")  # 🔒 Limit tag updates (higher for batch operations)
async def update_tag(
    request: Request,
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
@limiter.limit("50/minute")  # 🔒 Limit tag deletions (higher for batch operations)
async def delete_tag(
    request: Request,
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


@router.post("/sync-values", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")  # Rate limit for sync operations
async def sync_tag_values_from_opcua(
    request: Request,
    device_id: Optional[UUID] = Query(None, description="Device ID to filter tags"),
    opcua_endpoint: str = Query("opc.tcp://opcua-server:4840/optiflow/terminal", description="OPC UA server endpoint"),
    limit: int = Query(200, ge=1, le=500, description="Maximum number of tags to sync"),
    db: AsyncSession = Depends(get_db)
):
    """
    Read current values from OPC UA server and update tags in database
    
    This endpoint:
    - Connects to the OPC UA server
    - Reads current values for all tags
    - Updates last_value, last_quality, and last_timestamp in database
    
    Use this to synchronize tag values before displaying them in the UI
    """
    result = await update_tag_values_from_opcua(
        db=db,
        opcua_endpoint=opcua_endpoint,
        device_id=str(device_id) if device_id else None,
        limit=limit
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )
    
    return result
