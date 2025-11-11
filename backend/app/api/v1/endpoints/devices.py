"""
Device endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel

from app.db.session import get_db
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.services.cache_service import cached

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# Simple device creation schema for OPC UA
class SimpleDeviceCreate(BaseModel):
    name: str
    endpoint_url: str
    description: Optional[str] = None
    enabled: bool = True


@router.post("/simple", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_simple_device(
    request: Request,
    device_in: SimpleDeviceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a simple OPC UA device with just name and endpoint"""
    # Get the first site or use a default UUID
    stmt = select(Device).limit(1)
    result = await db.execute(select(Device))
    
    # Try to get first site
    from app.models.site import Site
    site_stmt = select(Site).limit(1)
    site_result = await db.execute(site_stmt)
    site = site_result.scalar_one_or_none()
    site_id = site.id if site else UUID('4562d673-75c3-4238-9c69-69abc98eadc7')
    
    # Extract connection details from endpoint URL
    try:
        endpoint_parts = device_in.endpoint_url.replace('opc.tcp://', '').split(':')
        host = endpoint_parts[0]
        port_and_path = endpoint_parts[1].split('/') if len(endpoint_parts) > 1 else ['4840', '']
        port = int(port_and_path[0])
    except:
        host = 'localhost'
        port = 4840
    
    connection_config = {
        'endpoint_url': device_in.endpoint_url,
        'ip_address': host,
        'port': port,
        'scan_rate': 1000,
        'timeout': 5000,
    }
    
    device = Device(
        name=device_in.name,
        description=device_in.description,
        protocol='opcua',
        site_id=site_id,
        is_active=device_in.enabled,
        connection_config=connection_config,
    )
    
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


@router.get("/")
async def list_devices(
    skip: int = 0,
    limit: int = 100,
    site_id: UUID = None,
    db: AsyncSession = Depends(get_db)
):
    """List all devices (simplified to fix serialization issues)"""
    try:
        stmt = select(Device)

        if site_id:
            stmt = stmt.where(Device.site_id == site_id)

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        devices = result.scalars().all()
        
        # Manual serialization to avoid Pydantic issues
        return [{
            "id": str(d.id),
            "site_id": str(d.site_id) if d.site_id else None,
            "name": d.name,
            "description": d.description,
            "protocol": d.protocol,
            "enabled": d.is_active,  # Model uses is_active
            "status": d.status,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            "total_tags": d.total_tags,
            "data_points_collected": d.data_points_collected,
            "created_at": d.created_at.isoformat(),
            "updated_at": d.updated_at.isoformat()
        } for d in devices]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error listing devices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")  # 🔒 Limit device creation
async def create_device(
    request: Request,
    device_in: DeviceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new device"""
    # Build connection_config from all fields
    connection_config = {
        'endpoint_url': device_in.config.get('endpoint_url') if device_in.config else None,
        'ip_address': device_in.ip_address,
        'port': device_in.port,
        'scan_rate': device_in.scan_rate or 1000,
        'timeout': device_in.timeout or 5000,
    }
    
    # Add device_type if provided
    if device_in.device_type:
        connection_config['device_type'] = device_in.device_type
    
    # Add any additional config
    if device_in.config:
        connection_config.update(device_in.config)
    
    # Create device with only valid model fields
    device = Device(
        name=device_in.name,
        description=device_in.description,
        protocol=device_in.protocol,
        site_id=device_in.site_id,
        is_active=device_in.enabled if hasattr(device_in, 'enabled') else True,
        connection_config=connection_config,
        manufacturer=device_in.manufacturer,
        model=device_in.model,
        serial_number=device_in.serial_number,
        firmware_version=device_in.firmware_version,
    )
    
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


@router.get("/{device_id}", response_model=DeviceResponse)
@cached(ttl=180, key_prefix="device_detail")
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
