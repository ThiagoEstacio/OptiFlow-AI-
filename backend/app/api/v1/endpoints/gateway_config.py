"""
Gateway Configuration API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import httpx

from app.db.session import get_db
from app.models.gateway_config import GatewayConfig as GatewayConfigModel, GatewayTag as GatewayTagModel
from app.schemas import gateway_config as schemas

router = APIRouter()


# ============================================================================
# Gateway Configuration CRUD
# ============================================================================

@router.get("/", response_model=List[schemas.GatewayConfigList])
async def list_gateway_configs(
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = False,
    gateway_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all gateway configurations

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        enabled_only: Filter only enabled gateways
        gateway_type: Filter by gateway type (opcua, modbus_tcp, etc.)
    """
    query = select(GatewayConfigModel).options(selectinload(GatewayConfigModel.tags))

    if enabled_only:
        query = query.where(GatewayConfigModel.enabled == True)

    if gateway_type:
        query = query.where(GatewayConfigModel.gateway_type == gateway_type)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    configs = result.scalars().all()

    # Convert to list schema with tags count
    return [
        schemas.GatewayConfigList(
            id=config.id,
            name=config.name,
            gateway_type=config.gateway_type,
            enabled=config.enabled,
            description=config.description,
            tags_count=len(config.tags) if config.tags else 0,
            created_at=config.created_at
        )
        for config in configs
    ]


@router.post("/", response_model=schemas.GatewayConfig, status_code=status.HTTP_201_CREATED)
async def create_gateway_config(
    gateway: schemas.GatewayConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new gateway configuration

    Args:
        gateway: Gateway configuration data including optional tags
    """
    # Check if name already exists
    result = await db.execute(
        select(GatewayConfigModel).where(GatewayConfigModel.name == gateway.name)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gateway with name '{gateway.name}' already exists"
        )

    # Create gateway config
    db_gateway = GatewayConfigModel(
        name=gateway.name,
        gateway_type=gateway.gateway_type,
        enabled=gateway.enabled,
        connection_config=gateway.connection_config,
        polling_interval_ms=gateway.polling_interval_ms,
        max_retries=gateway.max_retries,
        base_retry_delay=gateway.base_retry_delay,
        max_buffer_size=gateway.max_buffer_size,
        description=gateway.description
    )

    db.add(db_gateway)
    await db.flush()

    # Create tags if provided
    if gateway.tags:
        for tag in gateway.tags:
            db_tag = GatewayTagModel(
                gateway_id=db_gateway.id,
                tag_name=tag.tag_name,
                enabled=tag.enabled,
                address_config=tag.address_config,
                data_type=tag.data_type,
                scale_factor=tag.scale_factor,
                offset=tag.offset,
                unit=tag.unit,
                description=tag.description
            )
            db.add(db_tag)

    await db.commit()

    # Refresh and eagerly load tags
    await db.refresh(db_gateway)
    result = await db.execute(
        select(GatewayConfigModel)
        .options(selectinload(GatewayConfigModel.tags))
        .where(GatewayConfigModel.id == db_gateway.id)
    )
    db_gateway = result.scalar_one()

    return db_gateway


@router.get("/all-tags", response_model=List[schemas.GatewayTag])
async def list_all_tags(
    enabled_only: bool = False,
    skip: int = 0,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    """
    List all tags from all gateways

    Args:
        enabled_only: Filter only enabled tags
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
    """
    query = select(GatewayTagModel)

    if enabled_only:
        query = query.where(GatewayTagModel.enabled == True)

    query = query.offset(skip).limit(limit).order_by(GatewayTagModel.gateway_id, GatewayTagModel.tag_name)

    result = await db.execute(query)
    tags = result.scalars().all()

    return tags


@router.get("/{gateway_id}", response_model=schemas.GatewayConfig)
async def get_gateway_config(
    gateway_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get gateway configuration by ID including all tags
    """
    result = await db.execute(
        select(GatewayConfigModel)
        .options(selectinload(GatewayConfigModel.tags))
        .where(GatewayConfigModel.id == gateway_id)
    )
    gateway = result.scalar_one_or_none()

    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gateway with id {gateway_id} not found"
        )

    return gateway


@router.put("/{gateway_id}", response_model=schemas.GatewayConfig)
async def update_gateway_config(
    gateway_id: int,
    gateway_update: schemas.GatewayConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update gateway configuration
    """
    result = await db.execute(
        select(GatewayConfigModel).where(GatewayConfigModel.id == gateway_id)
    )
    gateway = result.scalar_one_or_none()

    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gateway with id {gateway_id} not found"
        )

    # Update fields
    update_data = gateway_update.model_dump(exclude_unset=True)

    # Check name uniqueness if changing name
    if "name" in update_data and update_data["name"] != gateway.name:
        result = await db.execute(
            select(GatewayConfigModel).where(GatewayConfigModel.name == update_data["name"])
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Gateway with name '{update_data['name']}' already exists"
            )

    for field, value in update_data.items():
        setattr(gateway, field, value)

    await db.commit()
    await db.refresh(gateway)

    return gateway


@router.delete("/{gateway_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gateway_config(
    gateway_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete gateway configuration (cascades to tags)
    """
    result = await db.execute(
        select(GatewayConfigModel).where(GatewayConfigModel.id == gateway_id)
    )
    gateway = result.scalar_one_or_none()

    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gateway with id {gateway_id} not found"
        )

    await db.delete(gateway)
    await db.commit()


# ============================================================================
# Gateway Service Proxy for Tags (must be before {gateway_id} routes)
# ============================================================================

GATEWAY_SERVICE_URL_TAGS = "http://gateway:8080"


@router.get("/proxy/tags")
async def proxy_gateway_all_tags():
    """
    Proxy endpoint to get all tags managed by the gateway service.
    Returns all 235+ tags with their current values and metadata.
    Must be defined before /{gateway_id}/tags to avoid route conflict.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{GATEWAY_SERVICE_URL_TAGS}/api/tags/")
            if response.status_code == 200:
                return response.json()
            return []
    except httpx.RequestError as e:
        return {"error": str(e), "tags": []}
    except Exception as e:
        return {"error": str(e), "tags": []}


# ============================================================================
# Gateway Tags CRUD
# ============================================================================

@router.get("/{gateway_id}/tags", response_model=List[schemas.GatewayTag])
async def list_gateway_tags(
    gateway_id: int,
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    List all tags for a gateway
    """
    # Check gateway exists
    result = await db.execute(
        select(GatewayConfigModel).where(GatewayConfigModel.id == gateway_id)
    )
    gateway = result.scalar_one_or_none()

    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gateway with id {gateway_id} not found"
        )

    # Get tags
    query = select(GatewayTagModel).where(GatewayTagModel.gateway_id == gateway_id)

    if enabled_only:
        query = query.where(GatewayTagModel.enabled == True)

    result = await db.execute(query)
    tags = result.scalars().all()

    return tags


@router.post("/{gateway_id}/tags", response_model=schemas.GatewayTag, status_code=status.HTTP_201_CREATED)
async def create_gateway_tag(
    gateway_id: int,
    tag: schemas.GatewayTagCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Add a new tag to a gateway
    """
    # Check gateway exists
    result = await db.execute(
        select(GatewayConfigModel).where(GatewayConfigModel.id == gateway_id)
    )
    gateway = result.scalar_one_or_none()

    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gateway with id {gateway_id} not found"
        )

    # Create tag
    db_tag = GatewayTagModel(
        gateway_id=gateway_id,
        tag_name=tag.tag_name,
        enabled=tag.enabled,
        address_config=tag.address_config,
        data_type=tag.data_type,
        scale_factor=tag.scale_factor,
        offset=tag.offset,
        unit=tag.unit,
        description=tag.description
    )

    db.add(db_tag)
    await db.commit()
    await db.refresh(db_tag)

    return db_tag


@router.put("/{gateway_id}/tags/{tag_id}", response_model=schemas.GatewayTag)
async def update_gateway_tag(
    gateway_id: int,
    tag_id: int,
    tag_update: schemas.GatewayTagUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a gateway tag
    """
    result = await db.execute(
        select(GatewayTagModel).where(
            GatewayTagModel.id == tag_id,
            GatewayTagModel.gateway_id == gateway_id
        )
    )
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id {tag_id} not found for gateway {gateway_id}"
        )

    # Update fields
    update_data = tag_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)

    await db.commit()
    await db.refresh(tag)

    return tag


@router.delete("/{gateway_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gateway_tag(
    gateway_id: int,
    tag_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a gateway tag
    """
    result = await db.execute(
        select(GatewayTagModel).where(
            GatewayTagModel.id == tag_id,
            GatewayTagModel.gateway_id == gateway_id
        )
    )
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id {tag_id} not found for gateway {gateway_id}"
        )

    await db.delete(tag)
    await db.commit()


# ============================================================================
# OPC-UA Discovery
# ============================================================================

@router.post("/discover/opcua", response_model=schemas.OPCUADiscoveryResponse)
async def discover_opcua_tags(
    request: schemas.OPCUADiscoveryRequest
):
    """
    Discover tags from an OPC-UA server

    Connects to the gateway service to perform OPC-UA browsing
    """
    try:
        # Call gateway API for OPC-UA browsing
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://gateway:8080/api/browse",
                json={
                    "endpoint": request.endpoint,
                    "namespace_index": request.namespace_index,
                    "tag_filter": request.tag_filter
                }
            )

            if response.status_code != 200:
                return schemas.OPCUADiscoveryResponse(
                    success=False,
                    endpoint=request.endpoint,
                    namespaces=[],
                    tags=[],
                    tag_count=0,
                    error=f"Gateway API error: {response.status_code}"
                )

            data = response.json()

            # Convert to schema
            return schemas.OPCUADiscoveryResponse(
                success=data["success"],
                endpoint=data["endpoint"],
                namespaces=[
                    schemas.OPCUANamespace(index=ns["index"], uri=ns["uri"])
                    for ns in data["namespaces"]
                ],
                tags=[
                    schemas.OPCUADiscoveredTag(**tag)
                    for tag in data["tags"]
                ],
                tag_count=data["tag_count"],
                error=data.get("error")
            )

    except httpx.RequestError as e:
        return schemas.OPCUADiscoveryResponse(
            success=False,
            endpoint=request.endpoint,
            namespaces=[],
            tags=[],
            tag_count=0,
            error=f"Failed to connect to gateway service: {str(e)}"
        )
    except Exception as e:
        return schemas.OPCUADiscoveryResponse(
            success=False,
            endpoint=request.endpoint,
            namespaces=[],
            tags=[],
            tag_count=0,
            error=f"Discovery failed: {str(e)}"
        )


@router.post("/discover/opcua/import", response_model=schemas.GatewayConfig, status_code=status.HTTP_201_CREATED)
async def import_opcua_discovery(
    request: schemas.OPCUADiscoveryImportRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Discover OPC-UA tags and create a gateway configuration with all discovered tags

    This is a convenience endpoint that combines discovery and import in one step
    """
    # First, discover tags
    discovery_request = schemas.OPCUADiscoveryRequest(
        endpoint=request.endpoint,
        namespace_index=request.namespace_index,
        tag_filter=request.tag_filter
    )

    discovery_result = await discover_opcua_tags(discovery_request)

    if not discovery_result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OPC-UA discovery failed: {discovery_result.error}"
        )

    if discovery_result.tag_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tags discovered with the specified filters"
        )

    # Create gateway configuration
    connection_config = {
        "endpoint": request.endpoint,
        "namespace": f"namespace_{request.namespace_index}" if request.namespace_index else "all",
        "security_policy": "None"
    }

    # Convert discovered tags to GatewayTagCreate
    tags = []
    for discovered_tag in discovery_result.tags:
        tags.append(schemas.GatewayTagCreate(
            tag_name=discovered_tag.tag_name,
            enabled=True,
            address_config={"node_id": discovered_tag.address},
            data_type=discovered_tag.data_type or "float",
            scale_factor=1.0,
            offset=0.0,
            unit=None,
            description=discovered_tag.description
        ))

    gateway_create = schemas.GatewayConfigCreate(
        name=request.gateway_name,
        gateway_type=schemas.GatewayTypeEnum.OPCUA,
        enabled=True,
        connection_config=connection_config,
        polling_interval_ms=request.polling_interval_ms,
        max_retries=5,
        base_retry_delay=5,
        max_buffer_size=10000,
        description=request.description,
        tags=tags
    )

    # Create gateway using existing endpoint
    return await create_gateway_config(gateway_create, db)


# ============================================================================
# Bulk Operations
# ============================================================================

@router.post("/bulk/import", response_model=schemas.BulkImportResponse)
async def bulk_import_gateways(
    bulk_request: schemas.BulkGatewayImport,
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk import multiple gateway configurations
    """
    imported_count = 0
    failed_count = 0
    errors = []

    for gateway in bulk_request.gateways:
        try:
            await create_gateway_config(gateway, db)
            imported_count += 1
        except Exception as e:
            failed_count += 1
            errors.append(f"Gateway '{gateway.name}': {str(e)}")

    return schemas.BulkImportResponse(
        success=failed_count == 0,
        imported_count=imported_count,
        failed_count=failed_count,
        errors=errors
    )


# ============================================================================
# Gateway Service Proxy (for frontend connectivity status)
# ============================================================================

GATEWAY_SERVICE_URL = "http://gateway:8080"


@router.get("/proxy/health")
async def proxy_gateway_health():
    """
    Proxy endpoint to get gateway service health status.
    This allows the frontend to check gateway health without CORS issues.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{GATEWAY_SERVICE_URL}/health")
            return response.json()
    except httpx.RequestError as e:
        return {"status": "disconnected", "error": str(e)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/proxy/adapters")
async def proxy_gateway_adapters():
    """
    Proxy endpoint to get list of adapters from the gateway service.
    Returns adapter status, connection info, and tag counts.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{GATEWAY_SERVICE_URL}/api/adapters/")
            if response.status_code == 200:
                return response.json()
            return []
    except httpx.RequestError as e:
        return {"error": str(e), "adapters": []}
    except Exception as e:
        return {"error": str(e), "adapters": []}


