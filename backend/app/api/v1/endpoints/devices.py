"""
Device endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.session import get_db
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/", response_model=List[DeviceResponse])
async def list_devices(
    skip: int = 0,
    limit: int = 100,
    site_id: UUID = None,
    db: AsyncSession = Depends(get_db)
):
    """List all devices"""
    stmt = select(Device)

    if site_id:
        stmt = stmt.where(Device.site_id == site_id)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    devices = result.scalars().all()
    return devices


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")  # 🔒 Limit device creation
async def create_device(
    request: Request,
    device_in: DeviceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new device"""
    device = Device(**device_in.model_dump())
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get device by ID"""
    stmt = select(Device).where(Device.id == device_id)
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    return device


@router.put("/{device_id}", response_model=DeviceResponse)
@limiter.limit("30/minute")  # 🔒 Limit device updates
async def update_device(
    request: Request,
    device_id: UUID,
    device_in: DeviceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a device"""
    stmt = select(Device).where(Device.id == device_id)
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # Update only provided fields
    update_data = device_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)

    await db.commit()
    await db.refresh(device)
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")  # 🔒 Limit device deletions
async def delete_device(
    request: Request,
    device_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a device"""
    stmt = select(Device).where(Device.id == device_id)
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    await db.delete(device)
    await db.commit()
    return None
