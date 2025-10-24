"""PLC Tags API"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.api.deps import get_current_user
from app.models.user import User
from app.services.plc_service import plc_service, PLCService
from app.services.timeseries_service import timeseries_service

router = APIRouter()


# Request/Response Models
class ConnectionTestRequest(BaseModel):
    url: str


class DiscoverTagsRequest(BaseModel):
    url: str
    node_id: Optional[str] = "i=85"  # Objects folder
    max_depth: Optional[int] = 10
    include_properties: Optional[bool] = False


class ImportTagsRequest(BaseModel):
    tags: List[Dict[str, Any]]
    device_id: Optional[str] = None

@router.get("/tags")
async def list_tags(current_user: User = Depends(get_current_user)):
    """List all available PLC tags"""
    return {
        "tags": [
            {
                "name": tag.name,
                "address": tag.address,
                "data_type": tag.data_type,
                "description": tag.description,
                "unit": tag.unit,
                "min_value": tag.min_value,
                "max_value": tag.max_value,
            }
            for tag in plc_service.tags.values()
        ]
    }

@router.get("/tags/{tag_name}")
async def read_tag(tag_name: str, current_user: User = Depends(get_current_user)):
    """Read current value of a PLC tag"""
    value = await plc_service.read_tag_opcua(tag_name)
    tag = plc_service.tags.get(tag_name)
    if not tag:
        return {"error": "Tag not found"}
    return {
        "name": tag_name,
        "value": value,
        "timestamp": tag.timestamp.isoformat() if tag.timestamp else None,
        "quality": tag.quality,
        "unit": tag.unit
    }

@router.get("/tags/{tag_name}/history")
async def get_tag_history(
    tag_name: str,
    hours: int = 24,
    aggregate: str = None,
    window: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get historical data for a tag"""
    start = datetime.utcnow() - timedelta(hours=hours)
    history = timeseries_service.query_tag_history(
        tag_name=tag_name,
        start=start,
        aggregate=aggregate,
        window=window
    )
    return {"tag_name": tag_name, "data": history}

@router.get("/tags/{tag_name}/stats")
async def get_tag_statistics(
    tag_name: str,
    hours: int = 24,
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a tag"""
    start = datetime.utcnow() - timedelta(hours=hours)
    stats = timeseries_service.query_statistics(tag_name, start)
    return {"tag_name": tag_name, "statistics": stats}


@router.post("/connection/test")
async def test_connection(
    request: ConnectionTestRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Test connection to OPC UA server

    This endpoint tests the connection to an OPC UA server (like KEPServerEX)
    and returns basic server information.
    """
    temp_service = PLCService()
    result = await temp_service.test_connection(request.url)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/discover")
async def discover_tags(
    request: DiscoverTagsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Discover all tags from OPC UA server

    This endpoint connects to an OPC UA server (like KEPServerEX) and browses
    the entire tag tree to discover all available variables/tags.

    Example for KEPServerEX:
    - url: "opc.tcp://localhost:49320"
    - node_id: "i=85" (Objects folder - default)
    - max_depth: 10 (maximum tree depth)
    """
    # Create temporary service for discovery
    temp_service = PLCService()

    try:
        # Connect to server
        connected = await temp_service.connect_opcua(request.url)
        if not connected:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to connect to OPC UA server at {request.url}"
            )

        # Browse and discover tags
        discovered_tags = await temp_service.browse_opcua(
            node_id=request.node_id,
            max_depth=request.max_depth,
            include_properties=request.include_properties
        )

        # Disconnect
        await temp_service.disconnect()

        return {
            "success": True,
            "url": request.url,
            "tags_found": len(discovered_tags),
            "tags": discovered_tags
        }

    except Exception as e:
        # Ensure disconnect on error
        try:
            await temp_service.disconnect()
        except:
            pass

        raise HTTPException(
            status_code=500,
            detail=f"Error during tag discovery: {str(e)}"
        )


@router.post("/tags/import")
async def import_tags(
    request: ImportTagsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Import discovered tags to the system

    This endpoint takes a list of discovered tags and registers them
    in the PLC service for monitoring.

    In the future, this will also save tags to PostgreSQL database.
    """
    from app.services.plc_service import PLCTag

    imported_count = 0
    errors = []

    for tag_data in request.tags:
        try:
            # Create PLCTag from discovered data
            tag = PLCTag(
                name=tag_data.get("name"),
                address=tag_data.get("node_id"),  # Use node_id as address
                data_type=tag_data.get("data_type", "Unknown"),
                description=tag_data.get("description", ""),
                unit=tag_data.get("unit", ""),
                min_value=tag_data.get("min_value"),
                max_value=tag_data.get("max_value")
            )

            # Register tag in PLC service
            plc_service.register_tag(tag)
            imported_count += 1

        except Exception as e:
            errors.append({
                "tag_name": tag_data.get("name"),
                "error": str(e)
            })

    return {
        "success": True,
        "imported_count": imported_count,
        "total_tags": len(request.tags),
        "errors": errors if errors else None
    }
