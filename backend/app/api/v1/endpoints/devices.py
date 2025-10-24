"""
Device endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.models.device import Device

router = APIRouter()


@router.get("/")
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
    return [
        {
            "id": str(d.id),
            "name": d.name,
            "protocol": d.protocol.value,
            "status": d.status.value,
            "site_id": str(d.site_id)
        }
        for d in devices
    ]


@router.post("/")
async def create_device(db: AsyncSession = Depends(get_db)):
    """Create a new device (placeholder)"""
    return {"message": "Device creation endpoint - to be implemented"}


@router.get("/{device_id}")
async def get_device(device_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get device by ID (placeholder)"""
    return {"message": f"Get device {device_id} - to be implemented"}
