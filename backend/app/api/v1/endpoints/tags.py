"""
Tag endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import logging

from app.db.session import get_db
from app.models.tag import Tag, TagCategory, TagDataType
from app.models.device import Device
from app.schemas.tag import (
    TagCreate,
    TagUpdate,
    TagResponse,
    TagWithDeviceResponse,
    TagListResponse,
    TagValueResponse,
)
from app.services.influxdb import InfluxDBService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=TagListResponse)
async def list_tags(
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[UUID] = None,
    site_id: Optional[UUID] = None,
    category: Optional[TagCategory] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all tags with pagination and filters
    This is the main endpoint that /tags page will consume
    """
    stmt = select(Tag).options(joinedload(Tag.device))

    # Apply filters
    if device_id:
        stmt = stmt.where(Tag.device_id == device_id)

    if site_id:
        # Join with Device to filter by site_id
        stmt = stmt.join(Device).where(Device.site_id == site_id)

    if category:
        stmt = stmt.where(Tag.category == category)

    if is_active is not None:
        stmt = stmt.where(Tag.is_active == is_active)

    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            (Tag.name.ilike(search_pattern)) |
            (Tag.description.ilike(search_pattern))
        )

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Get paginated results
    stmt = stmt.offset(skip).limit(limit).order_by(Tag.name)
    result = await db.execute(stmt)
    tags = result.unique().scalars().all()

    return TagListResponse(
        tags=[TagResponse.model_validate(t) for t in tags],
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.get("/with-devices")
async def list_tags_with_devices(
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[UUID] = None,
    site_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List tags with device information
    Useful for dashboard-builder to know which device each tag belongs to
    """
    stmt = select(Tag, Device).join(Device, Tag.device_id == Device.id)

    if device_id:
        stmt = stmt.where(Tag.device_id == device_id)

    if site_id:
        stmt = stmt.where(Device.site_id == site_id)

    stmt = stmt.offset(skip).limit(limit).order_by(Tag.name)
    result = await db.execute(stmt)
    rows = result.all()

    tags_with_devices = []
    for tag, device in rows:
        tag_dict = TagResponse.model_validate(tag).model_dump()
        tag_dict["device_name"] = device.name
        tag_dict["device_protocol"] = device.protocol.value
        tag_dict["site_id"] = str(device.site_id)
        tags_with_devices.append(tag_dict)

    return {
        "tags": tags_with_devices,
        "total": len(tags_with_devices)
    }


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new tag"""
    try:
        # Verify device exists
        device_stmt = select(Device).where(Device.id == tag_data.device_id)
        device_result = await db.execute(device_stmt)
        device = device_result.scalar_one_or_none()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {tag_data.device_id} not found"
            )

        # Check if tag with same address already exists for this device
        check_stmt = select(Tag).where(
            Tag.device_id == tag_data.device_id,
            Tag.address == tag_data.address
        )
        check_result = await db.execute(check_stmt)
        existing_tag = check_result.scalar_one_or_none()

        if existing_tag:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag with address '{tag_data.address}' already exists for this device"
            )

        # Create tag
        tag = Tag(**tag_data.model_dump())
        db.add(tag)

        # Update device total_tags count
        device.total_tags += 1

        await db.commit()
        await db.refresh(tag)

        logger.info(f"Created tag {tag.name} ({tag.id}) for device {device.name}")
        return TagResponse.model_validate(tag)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating tag: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating tag: {str(e)}"
        )


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get tag by ID"""
    stmt = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag {tag_id} not found"
        )

    return TagResponse.model_validate(tag)


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: UUID,
    tag_data: TagUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update tag"""
    stmt = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag {tag_id} not found"
        )

    # Update fields
    update_data = tag_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)

    try:
        await db.commit()
        await db.refresh(tag)
        logger.info(f"Updated tag {tag.name} ({tag.id})")
        return TagResponse.model_validate(tag)
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating tag: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating tag: {str(e)}"
        )


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete tag"""
    stmt = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag {tag_id} not found"
        )

    try:
        # Update device total_tags count
        device_stmt = select(Device).where(Device.id == tag.device_id)
        device_result = await db.execute(device_stmt)
        device = device_result.scalar_one_or_none()
        if device and device.total_tags > 0:
            device.total_tags -= 1

        await db.delete(tag)
        await db.commit()
        logger.info(f"Deleted tag {tag.name} ({tag.id})")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting tag: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting tag: {str(e)}"
        )


@router.get("/{tag_id}/latest", response_model=TagValueResponse)
async def get_tag_latest(tag_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get latest cached value for a tag
    This is fast as it reads from PostgreSQL cache
    """
    stmt = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag {tag_id} not found"
        )

    if not tag.last_value or not tag.last_timestamp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached value available for tag {tag_id}"
        )

    # Parse value based on data type
    value = tag.last_value
    if tag.data_type == TagDataType.BOOLEAN:
        value = value.lower() in ('true', '1', 'yes')
    elif tag.data_type in (TagDataType.INTEGER, TagDataType.FLOAT, TagDataType.DOUBLE):
        try:
            value = float(value) if tag.data_type in (TagDataType.FLOAT, TagDataType.DOUBLE) else int(value)
        except:
            pass

    return TagValueResponse(
        tag_id=tag.id,
        value=value,
        quality=tag.last_quality or "Unknown",
        timestamp=tag.last_timestamp
    )


@router.get("/{tag_id}/history")
async def get_tag_history(
    tag_id: UUID,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical values for a tag from InfluxDB
    """
    stmt = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag {tag_id} not found"
        )

    # Default time range: last 24 hours
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=24)

    try:
        influx_service = InfluxDBService()
        data_points = await influx_service.query_tag_data(
            tag_id=str(tag_id),
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

        return {
            "tag_id": str(tag_id),
            "tag_name": tag.name,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "data_points": data_points,
            "count": len(data_points)
        }

    except Exception as e:
        logger.error(f"Error querying historical data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying historical data: {str(e)}"
        )
