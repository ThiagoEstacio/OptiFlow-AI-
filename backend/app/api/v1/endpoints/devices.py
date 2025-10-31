"""
Device endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
import logging

from app.db.session import get_db
from app.models.device import Device, DeviceProtocol, DeviceStatus
from app.models.tag import Tag, TagDataType, TagCategory
from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceListResponse,
    DeviceTestConnectionRequest,
    DeviceTestConnectionResponse,
    DeviceBrowseTagsRequest,
    DeviceBrowseTagsResponse,
    BrowsedTag,
    DeviceImportTagsRequest,
)
from app.services.opcua_client import OPCUAClient

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=DeviceListResponse)
async def list_devices(
    skip: int = 0,
    limit: int = 100,
    site_id: Optional[UUID] = None,
    protocol: Optional[DeviceProtocol] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all devices with pagination and filters"""
    stmt = select(Device)

    if site_id:
        stmt = stmt.where(Device.site_id == site_id)
    if protocol:
        stmt = stmt.where(Device.protocol == protocol)
    if is_active is not None:
        stmt = stmt.where(Device.is_active == is_active)

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Get paginated results
    stmt = stmt.offset(skip).limit(limit).order_by(Device.created_at.desc())
    result = await db.execute(stmt)
    devices = result.scalars().all()

    return DeviceListResponse(
        devices=[DeviceResponse.model_validate(d) for d in devices],
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new device"""
    try:
        # Create device instance
        device = Device(
            site_id=device_data.site_id,
            name=device_data.name,
            description=device_data.description,
            protocol=device_data.protocol,
            connection_config=device_data.connection_config,
            is_active=device_data.is_active,
            manufacturer=device_data.manufacturer,
            model=device_data.model,
            serial_number=device_data.serial_number,
            firmware_version=device_data.firmware_version,
            settings=device_data.settings,
            status=DeviceStatus.UNKNOWN
        )

        db.add(device)
        await db.commit()
        await db.refresh(device)

        logger.info(f"Created device {device.name} ({device.id})")
        return DeviceResponse.model_validate(device)

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating device: {str(e)}"
        )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get device by ID"""
    stmt = select(Device).where(Device.id == device_id)
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found"
        )

    return DeviceResponse.model_validate(device)


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: UUID,
    device_data: DeviceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update device"""
    stmt = select(Device).where(Device.id == device_id)
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found"
        )

    # Update fields
    update_data = device_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)

    try:
        await db.commit()
        await db.refresh(device)
        logger.info(f"Updated device {device.name} ({device.id})")
        return DeviceResponse.model_validate(device)
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating device: {str(e)}"
        )


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete device"""
    stmt = select(Device).where(Device.id == device_id)
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found"
        )

    try:
        await db.delete(device)
        await db.commit()
        logger.info(f"Deleted device {device.name} ({device.id})")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting device: {str(e)}"
        )


@router.post("/test-connection", response_model=DeviceTestConnectionResponse)
async def test_connection(request: DeviceTestConnectionRequest):
    """Test connection to a device before creating it"""
    try:
        if request.protocol == DeviceProtocol.OPC_UA:
            endpoint = request.connection_config.get("endpoint")
            username = request.connection_config.get("username")
            password = request.connection_config.get("password")

            if not endpoint:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="endpoint is required for OPC UA"
                )

            client = OPCUAClient(endpoint, username, password)
            result = await client.test_connection()

            if result["success"]:
                return DeviceTestConnectionResponse(
                    success=True,
                    message="Successfully connected to OPC UA server",
                    server_info=result
                )
            else:
                return DeviceTestConnectionResponse(
                    success=False,
                    error=result.get("error", "Unknown error")
                )

        else:
            return DeviceTestConnectionResponse(
                success=False,
                error=f"Protocol {request.protocol} not yet implemented"
            )

    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return DeviceTestConnectionResponse(
            success=False,
            error=str(e)
        )


@router.post("/browse-tags", response_model=DeviceBrowseTagsResponse)
async def browse_tags(request: DeviceBrowseTagsRequest):
    """Browse/discover tags from a device"""
    try:
        if request.protocol == DeviceProtocol.OPC_UA:
            endpoint = request.connection_config.get("endpoint")
            username = request.connection_config.get("username")
            password = request.connection_config.get("password")

            if not endpoint:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="endpoint is required for OPC UA"
                )

            client = OPCUAClient(endpoint, username, password)
            await client.connect()

            tags = await client.browse_tags(max_depth=request.max_depth)
            await client.disconnect()

            return DeviceBrowseTagsResponse(
                success=True,
                tags=[BrowsedTag(**tag) for tag in tags],
                total=len(tags)
            )

        else:
            return DeviceBrowseTagsResponse(
                success=False,
                error=f"Protocol {request.protocol} not yet implemented"
            )

    except Exception as e:
        logger.error(f"Error browsing tags: {e}")
        return DeviceBrowseTagsResponse(
            success=False,
            error=str(e)
        )


@router.post("/import-tags")
async def import_tags(
    request: DeviceImportTagsRequest,
    db: AsyncSession = Depends(get_db)
):
    """Import discovered tags to a device"""
    try:
        # Verify device exists
        stmt = select(Device).where(Device.id == request.device_id)
        result = await db.execute(stmt)
        device = result.scalar_one_or_none()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {request.device_id} not found"
            )

        imported_count = 0
        skipped_count = 0

        for tag_data in request.tags:
            # Check if tag already exists
            check_stmt = select(Tag).where(
                Tag.device_id == request.device_id,
                Tag.address == tag_data.get("address")
            )
            check_result = await db.execute(check_stmt)
            existing_tag = check_result.scalar_one_or_none()

            if existing_tag:
                skipped_count += 1
                continue

            # Create new tag
            tag = Tag(
                device_id=request.device_id,
                name=tag_data.get("name"),
                description=tag_data.get("description", ""),
                address=tag_data.get("address"),
                data_type=TagDataType(tag_data.get("data_type", "float")),
                category=TagCategory(request.category),
                is_active=request.auto_activate,
            )

            db.add(tag)
            imported_count += 1

        # Update device total_tags count
        count_stmt = select(func.count()).select_from(Tag).where(Tag.device_id == request.device_id)
        count_result = await db.execute(count_stmt)
        device.total_tags = count_result.scalar() + imported_count

        await db.commit()

        logger.info(f"Imported {imported_count} tags to device {device.name}, skipped {skipped_count}")

        return {
            "success": True,
            "imported": imported_count,
            "skipped": skipped_count,
            "total": imported_count + skipped_count
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Error importing tags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing tags: {str(e)}"
        )
