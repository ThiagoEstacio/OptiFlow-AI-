"""
Discovery API Endpoints

Provides endpoints for discovering industrial devices and browsing their tags.
Supports:
- EtherNet/IP (Rockwell PLCs)
- S7 Protocol (Siemens PLCs)
- OPC UA

Endpoints:
- POST /ethernet-ip/scan - Scan network for EtherNet/IP devices
- GET /ethernet-ip/devices - List discovered devices
- POST /ethernet-ip/browse-tags - Browse tags from a device
- POST /ethernet-ip/import-tags - Import tags as points
- POST /s7/scan - Scan for S7 devices
- POST /s7/import-symbols - Import S7 symbols
- POST /opcua/browse - Browse OPC UA address space
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, IPvAnyAddress
import asyncio
from datetime import datetime

from ....db.session import get_db
from ....models.device import Device, DeviceProtocol
from ....models.tag import Tag, TagDataType, TagCategory
from ....core.security import get_current_user
from ....models.user import User

router = APIRouter()


# ========== Request/Response Models ==========

class EtherNetIPScanRequest(BaseModel):
    """Request to scan network for EtherNet/IP devices"""
    subnet: str = Field(..., example="192.168.1.0/24", description="Subnet in CIDR notation")
    timeout: Optional[float] = Field(2.0, ge=0.5, le=10.0, description="Scan timeout in seconds")


class DeviceInfo(BaseModel):
    """Discovered device information"""
    ip_address: str
    vendor_id: Optional[int] = None
    vendor_name: Optional[str] = None
    device_type: Optional[int] = None
    product_code: Optional[int] = None
    product_name: Optional[str] = None
    serial_number: Optional[str] = None
    revision: Optional[str] = None
    protocol: str
    discovered_at: Optional[float] = None


class EtherNetIPScanResponse(BaseModel):
    """Response from EtherNet/IP scan"""
    devices: List[DeviceInfo]
    scan_duration: float
    subnet_scanned: str


class BrowseTagsRequest(BaseModel):
    """Request to browse tags from a device"""
    device_ip: str = Field(..., description="Device IP address")
    slot: Optional[int] = Field(0, description="Slot number (EtherNet/IP)")
    include_values: Optional[bool] = Field(False, description="Include current values (slower)")
    filter_pattern: Optional[str] = Field(None, description="Filter by name pattern")
    exclude_system: Optional[bool] = Field(True, description="Exclude system tags")


class TagInfo(BaseModel):
    """Tag information from device"""
    tag_name: str
    full_path: str
    data_type: str
    category: Optional[str] = None
    is_array: bool = False
    is_struct: bool = False
    value: Optional[Any] = None
    description: Optional[str] = None


class BrowseTagsResponse(BaseModel):
    """Response from tag browsing"""
    device_ip: str
    tag_count: int
    tags: List[TagInfo]


class ImportTagRequest(BaseModel):
    """Single tag to import"""
    tag_name: str
    source_address: str
    data_type: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    scan_rate: Optional[int] = 1000  # milliseconds


class ImportTagsRequest(BaseModel):
    """Request to import tags as points"""
    device_ip: str
    slot: Optional[int] = 0
    protocol: str = "EtherNet/IP"
    site_id: int
    organization_id: int
    tags: List[ImportTagRequest]
    create_device: Optional[bool] = True  # Create device if doesn't exist


class ImportTagsResponse(BaseModel):
    """Response from tag import"""
    device_id: Optional[int] = None
    tags_imported: int
    tags_failed: int
    errors: List[str] = []


class S7ImportSymbolsRequest(BaseModel):
    """Request to import S7 symbols from file"""
    device_ip: str
    site_id: int
    organization_id: int
    symbols_csv: str  # CSV content
    create_device: Optional[bool] = True


# ========== Helper Functions ==========

async def create_device_from_discovery(
    db: AsyncSession,
    device_info: DeviceInfo,
    site_id: int,
    organization_id: int,
    slot: int = 0
) -> Device:
    """
    Create a device record from discovered device info.

    Args:
        db: Database session
        device_info: Discovered device information
        site_id: Site ID
        organization_id: Organization ID
        slot: Slot number

    Returns:
        Created Device object
    """
    # Map protocol string to enum
    protocol_map = {
        "EtherNet/IP": DeviceProtocol.ETHERNET_IP,
        "S7": DeviceProtocol.SIEMENS_S7,
        "OPC UA": DeviceProtocol.OPC_UA
    }

    protocol = protocol_map.get(device_info.protocol, DeviceProtocol.ETHERNET_IP)

    # Create device
    device = Device(
        name=f"{device_info.product_name or 'PLC'}_{device_info.ip_address}",
        description=f"Auto-discovered {device_info.vendor_name or 'device'}",
        protocol=protocol,
        connection_string=device_info.ip_address,
        configuration={
            "ip_address": device_info.ip_address,
            "slot": slot,
            "vendor_id": device_info.vendor_id,
            "product_code": device_info.product_code,
            "serial_number": device_info.serial_number,
            "revision": device_info.revision
        },
        manufacturer=device_info.vendor_name,
        model=device_info.product_name,
        site_id=site_id,
        organization_id=organization_id
    )

    db.add(device)
    await db.commit()
    await db.refresh(device)

    return device


async def create_tag_from_import(
    db: AsyncSession,
    device: Device,
    tag_request: ImportTagRequest,
    organization_id: int
) -> Tag:
    """
    Create a tag record from import request.

    Args:
        db: Database session
        device: Device object
        tag_request: Tag import request
        organization_id: Organization ID

    Returns:
        Created Tag object
    """
    # Map string data type to enum
    data_type_map = {
        "BOOL": TagDataType.BOOLEAN,
        "BOOLEAN": TagDataType.BOOLEAN,
        "SINT": TagDataType.INTEGER,
        "INT": TagDataType.INTEGER,
        "DINT": TagDataType.INTEGER,
        "LINT": TagDataType.INTEGER,
        "REAL": TagDataType.FLOAT,
        "LREAL": TagDataType.DOUBLE,
        "STRING": TagDataType.STRING
    }

    data_type = data_type_map.get(tag_request.data_type.upper(), TagDataType.FLOAT)

    # Map category
    category_map = {
        "process": TagCategory.PROCESS,
        "energy": TagCategory.ENERGY,
        "quality": TagCategory.QUALITY,
        "production": TagCategory.PRODUCTION,
        "maintenance": TagCategory.MAINTENANCE,
        "alarm": TagCategory.ALARM,
        "setpoint": TagCategory.SETPOINT,
        "status": TagCategory.STATUS
    }

    category = TagCategory.PROCESS
    if tag_request.category:
        category = category_map.get(tag_request.category.lower(), TagCategory.PROCESS)

    # Create tag
    tag = Tag(
        name=tag_request.tag_name,
        description=tag_request.description or f"Imported from {device.name}",
        address=tag_request.source_address,
        data_type=data_type,
        unit=tag_request.unit,
        category=category,
        scan_rate=tag_request.scan_rate,
        device_id=device.id,
        organization_id=organization_id
    )

    db.add(tag)
    return tag


# ========== EtherNet/IP Endpoints ==========

@router.post("/ethernet-ip/scan", response_model=EtherNetIPScanResponse)
async def scan_ethernet_ip_network(
    request: EtherNetIPScanRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Scan network for EtherNet/IP devices.

    This endpoint triggers a network scan using List Identity broadcast.
    Discovered devices are returned but not automatically saved to database.
    """
    try:
        # Import here to avoid circular imports
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../gateway'))

        from gateway.app.services.discovery.ethernet_ip_discovery import (
            EtherNetIPDiscoveryService
        )

        # Create discovery service
        discovery = EtherNetIPDiscoveryService(timeout=request.timeout)

        # Run scan
        start_time = asyncio.get_event_loop().time()
        devices = await discovery.scan_network(request.subnet)
        end_time = asyncio.get_event_loop().time()

        # Convert to response model
        device_infos = []
        for device in devices:
            device_infos.append(DeviceInfo(
                ip_address=device.ip_address,
                vendor_id=device.vendor_id,
                vendor_name=device.vendor_name,
                device_type=device.device_type,
                product_code=device.product_code,
                product_name=device.product_name,
                serial_number=device.serial_number,
                revision=f"{device.revision_major}.{device.revision_minor}" if device.revision_major else None,
                protocol="EtherNet/IP",
                discovered_at=device.discovered_at
            ))

        return EtherNetIPScanResponse(
            devices=device_infos,
            scan_duration=end_time - start_time,
            subnet_scanned=request.subnet
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.post("/ethernet-ip/browse-tags", response_model=BrowseTagsResponse)
async def browse_ethernet_ip_tags(
    request: BrowseTagsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Browse tags from an EtherNet/IP device.

    Connects to the device and retrieves all available tags with their metadata.
    """
    try:
        # Import here to avoid circular imports
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../gateway'))

        from gateway.app.services.discovery.ethernet_ip_tag_browser import (
            EtherNetIPTagBrowser,
            TagFilter
        )

        # Create tag browser
        browser = EtherNetIPTagBrowser(request.device_ip, slot=request.slot or 0)

        # Browse tags
        tags = await browser.browse_tags_async(include_values=request.include_values)

        # Apply filters if requested
        if request.filter_pattern or request.exclude_system:
            tag_filter = TagFilter(
                name_pattern=request.filter_pattern,
                exclude_system=request.exclude_system
            )
            tags = browser.filter_tags(tags, tag_filter)

        # Convert to response model
        tag_infos = []
        for tag in tags:
            tag_infos.append(TagInfo(
                tag_name=tag.tag_name,
                full_path=tag.full_path,
                data_type=tag.data_type,
                category=tag.category,
                is_array=tag.is_array,
                is_struct=tag.is_struct,
                value=tag.value,
                description=tag.description
            ))

        # Cleanup
        browser.disconnect()

        return BrowseTagsResponse(
            device_ip=request.device_ip,
            tag_count=len(tag_infos),
            tags=tag_infos
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tag browsing failed: {str(e)}")


@router.post("/ethernet-ip/import-tags", response_model=ImportTagsResponse)
async def import_ethernet_ip_tags(
    request: ImportTagsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import tags from an EtherNet/IP device as points.

    Creates device record (if needed) and tag records in the database.
    """
    try:
        device = None
        tags_imported = 0
        tags_failed = 0
        errors = []

        # Check if device exists
        from sqlalchemy import select
        result = await db.execute(
            select(Device).where(
                Device.connection_string == request.device_ip,
                Device.organization_id == request.organization_id
            )
        )
        device = result.scalar_one_or_none()

        # Create device if doesn't exist and requested
        if not device and request.create_device:
            # Create minimal device info for import
            device_info = DeviceInfo(
                ip_address=request.device_ip,
                protocol=request.protocol,
                product_name="Imported Device"
            )

            device = await create_device_from_discovery(
                db=db,
                device_info=device_info,
                site_id=request.site_id,
                organization_id=request.organization_id,
                slot=request.slot or 0
            )

        if not device:
            raise HTTPException(
                status_code=404,
                detail="Device not found and create_device is False"
            )

        # Import tags
        for tag_request in request.tags:
            try:
                tag = await create_tag_from_import(
                    db=db,
                    device=device,
                    tag_request=tag_request,
                    organization_id=request.organization_id
                )
                tags_imported += 1

            except Exception as e:
                tags_failed += 1
                errors.append(f"{tag_request.tag_name}: {str(e)}")

        # Commit all tags
        await db.commit()

        return ImportTagsResponse(
            device_id=device.id,
            tags_imported=tags_imported,
            tags_failed=tags_failed,
            errors=errors
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# ========== S7 Protocol Endpoints ==========

class S7ScanRequest(BaseModel):
    """Request to scan network for S7 devices"""
    start_ip: str = Field(..., example="192.168.1.1", description="Starting IP address")
    end_ip: str = Field(..., example="192.168.1.254", description="Ending IP address")
    rack: Optional[int] = Field(0, description="Rack number (usually 0)")
    slot: Optional[int] = Field(1, description="Slot number (usually 1 for CPU)")
    timeout: Optional[float] = Field(2.0, ge=0.5, le=10.0, description="Probe timeout")


class S7ListDBsRequest(BaseModel):
    """Request to list Data Blocks"""
    device_ip: str = Field(..., description="Device IP address")
    rack: Optional[int] = Field(0, description="Rack number")
    slot: Optional[int] = Field(1, description="Slot number")
    start_db: Optional[int] = Field(1, description="Starting DB number")
    end_db: Optional[int] = Field(1000, description="Ending DB number")
    max_dbs: Optional[int] = Field(100, description="Maximum DBs to find")


class DBInfo(BaseModel):
    """Data Block information"""
    db_number: int
    size: int
    accessible: bool = True
    error: Optional[str] = None


class S7ListDBsResponse(BaseModel):
    """Response from DB listing"""
    device_ip: str
    db_count: int
    total_size: int
    dbs: List[DBInfo]


@router.post("/s7/scan")
async def scan_s7_network(
    request: S7ScanRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Scan IP range for S7 devices.

    Note: S7 devices don't respond to broadcast, so this performs
    unicast probes on each IP in the range.
    """
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../gateway'))

        from gateway.app.protocols.s7 import S7Client
        import ipaddress

        devices = []
        start = ipaddress.ip_address(request.start_ip)
        end = ipaddress.ip_address(request.end_ip)

        current = start
        scan_count = 0

        logger.info(f"Scanning S7 devices from {request.start_ip} to {request.end_ip}...")

        while current <= end and scan_count < 254:  # Limit to prevent excessive scanning
            ip_str = str(current)
            scan_count += 1

            try:
                # Probe this IP
                client = S7Client(ip_str, rack=request.rack, slot=request.slot, timeout=request.timeout)

                if client.connect():
                    # Get device info
                    info = client.get_device_info()

                    if info:
                        devices.append(DeviceInfo(
                            ip_address=ip_str,
                            product_name=info.cpu_type,
                            serial_number=info.serial_number,
                            vendor_name="Siemens",
                            protocol="S7"
                        ))
                        logger.info(f"Found S7 device at {ip_str}")

                    client.disconnect()

            except Exception as e:
                logger.debug(f"No S7 device at {ip_str}: {e}")

            current += 1

        return {
            "devices": devices,
            "scanned_ips": scan_count,
            "devices_found": len(devices)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S7 scan failed: {str(e)}")


@router.post("/s7/list-dbs", response_model=S7ListDBsResponse)
async def list_s7_data_blocks(
    request: S7ListDBsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    List all accessible Data Blocks in an S7 PLC.

    This endpoint probes DB numbers from start_db to end_db to find
    which DBs are accessible.
    """
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../gateway'))

        from gateway.app.services.discovery.s7_db_browser import S7DBBrowser

        # Create DB browser
        browser = S7DBBrowser(
            request.device_ip,
            rack=request.rack,
            slot=request.slot
        )

        # List DBs
        dbs = await browser.list_dbs_async(
            start_db=request.start_db,
            end_db=request.end_db,
            max_dbs=request.max_dbs
        )

        # Cleanup
        browser.disconnect()

        # Convert to response
        db_infos = [
            DBInfo(
                db_number=db.db_number,
                size=db.size,
                accessible=db.accessible,
                error=db.error
            )
            for db in dbs
        ]

        total_size = sum(db.size for db in dbs)

        return S7ListDBsResponse(
            device_ip=request.device_ip,
            db_count=len(db_infos),
            total_size=total_size,
            dbs=db_infos
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB listing failed: {str(e)}")


@router.post("/s7/import-symbols")
async def import_s7_symbols(
    request: S7ImportSymbolsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import S7 symbols from CSV file exported from TIA Portal.

    CSV format (flexible, must have Name and Address columns):
    Name,Address,Type,Comment
    MotorSpeed,DB10.DBREAL0,Real,Motor speed in RPM
    MotorTemp,DB10.DBREAL4,Real,Motor temperature

    or:

    Symbol,Tag Address,Data Type,Description
    Temperature_1,DB1.DBW0,INT,Temperature sensor 1
    """
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../gateway'))

        from gateway.app.services.discovery.s7_symbol_importer import S7SymbolImporter

        # Create importer
        importer = S7SymbolImporter()

        # Import symbols from CSV
        symbols = importer.import_from_csv(request.symbols_csv)

        if not symbols:
            raise HTTPException(
                status_code=400,
                detail="No symbols found in CSV. Check format."
            )

        # Validate symbols
        validation = importer.validate_symbols(symbols)

        if validation['invalid'] > 0:
            logger.warning(f"Symbol validation found {validation['invalid']} invalid symbols")

        # Check if device exists
        from sqlalchemy import select
        result = await db.execute(
            select(Device).where(
                Device.connection_string == request.device_ip,
                Device.organization_id == request.organization_id
            )
        )
        device = result.scalar_one_or_none()

        # Create device if needed
        if not device and request.create_device:
            device_info = DeviceInfo(
                ip_address=request.device_ip,
                protocol="S7",
                product_name="S7 PLC",
                vendor_name="Siemens"
            )

            device = await create_device_from_discovery(
                db=db,
                device_info=device_info,
                site_id=request.site_id,
                organization_id=request.organization_id,
                slot=0
            )

        if not device:
            raise HTTPException(
                status_code=404,
                detail="Device not found and create_device is False"
            )

        # Import symbols as tags
        tags_imported = 0
        tags_failed = 0
        errors = []

        for symbol in symbols:
            try:
                # Create tag from symbol
                tag_request = ImportTagRequest(
                    tag_name=symbol.name,
                    source_address=symbol.address,
                    data_type=symbol.data_type,
                    description=symbol.comment,
                    unit=symbol.unit
                )

                tag = await create_tag_from_import(
                    db=db,
                    device=device,
                    tag_request=tag_request,
                    organization_id=request.organization_id
                )

                tags_imported += 1

            except Exception as e:
                tags_failed += 1
                errors.append(f"{symbol.name}: {str(e)}")

        # Commit
        await db.commit()

        return {
            "device_id": device.id,
            "symbols_processed": len(symbols),
            "tags_imported": tags_imported,
            "tags_failed": tags_failed,
            "validation": validation,
            "errors": errors[:10]  # Limit error list
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Symbol import failed: {str(e)}")


# ========== OPC UA Endpoints ==========

@router.post("/opcua/browse")
async def browse_opcua_address_space(
    request: BrowseTagsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Browse OPC UA address space.

    Connects to OPC UA server and recursively browses the address space.
    """
    # TODO: Implement OPC UA browsing in Week 3
    raise HTTPException(
        status_code=501,
        detail="OPC UA browsing will be implemented in Phase 0 Week 3"
    )


# ========== Utility Endpoints ==========

@router.get("/devices")
async def list_discovered_devices(
    organization_id: Optional[int] = None,
    protocol: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all discovered/configured devices.

    This returns devices from the database, not a live scan.
    """
    try:
        from sqlalchemy import select

        query = select(Device)

        if organization_id:
            query = query.where(Device.organization_id == organization_id)

        if protocol:
            protocol_map = {
                "ethernet-ip": DeviceProtocol.ETHERNET_IP,
                "s7": DeviceProtocol.SIEMENS_S7,
                "opcua": DeviceProtocol.OPC_UA,
                "modbus": DeviceProtocol.MODBUS_TCP,
                "mqtt": DeviceProtocol.MQTT
            }
            if protocol.lower() in protocol_map:
                query = query.where(Device.protocol == protocol_map[protocol.lower()])

        result = await db.execute(query)
        devices = result.scalars().all()

        return {"devices": devices, "count": len(devices)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
