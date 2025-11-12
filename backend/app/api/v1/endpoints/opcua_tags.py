"""
OPC UA Tag Browser API
Browse OPC UA server nodes and configure tags for gateway collection
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import asyncio
from asyncua import Client
import logging

from ....db.session import get_db
from ....models.device import Device
from ....models.tag import Tag

logger = logging.getLogger(__name__)
router = APIRouter()


class OPCUANode(BaseModel):
    """OPC UA node representation"""
    node_id: str
    browse_name: str
    display_name: str
    node_class: str  # Variable, Object, Method
    data_type: Optional[str] = None
    value: Optional[Any] = None
    children: Optional[List['OPCUANode']] = None
    has_children: bool = False


class TagConfiguration(BaseModel):
    """Tag configuration for gateway collection"""
    tag_name: str
    description: Optional[str] = None
    node_id: str
    data_type: str
    unit: Optional[str] = None
    sample_interval_ms: int = 1000
    enabled: bool = True


class BulkTagConfigRequest(BaseModel):
    """Request to configure multiple tags"""
    device_id: int
    tags: List[TagConfiguration]


async def browse_opcua_node(client: Client, node, level: int = 0, max_level: int = 3) -> Optional[OPCUANode]:
    """
    Browse OPC UA node and return structured data
    """
    try:
        browse_name = await node.read_browse_name()
        node_id = node.nodeid.to_string()
        node_class = await node.read_node_class()
        
        # Get display name
        try:
            display_name_obj = await node.read_display_name()
            display_name = display_name_obj.Text if hasattr(display_name_obj, 'Text') else browse_name.Name
        except:
            display_name = browse_name.Name
        
        node_data = OPCUANode(
            node_id=node_id,
            browse_name=browse_name.Name,
            display_name=display_name,
            node_class=node_class.name,
            children=[]
        )
        
        # If it's a variable, get data type and current value
        if node_class.name == "Variable":
            try:
                # Get data type
                data_type_node = await node.read_data_type()
                node_data.data_type = data_type_node.to_string()
                
                # Try to read current value
                value = await node.read_value()
                # Convert to serializable format
                if isinstance(value, (int, float, str, bool)):
                    node_data.value = value
                else:
                    node_data.value = str(value)
            except Exception as e:
                logger.debug(f"Could not read variable details: {e}")
                node_data.data_type = "Unknown"
        
        # Check if has children and browse them if not at max level
        if level < max_level:
            try:
                children = await node.get_children()
                node_data.has_children = len(children) > 0
                
                if node_data.has_children:
                    for child in children:
                        child_data = await browse_opcua_node(client, child, level + 1, max_level)
                        if child_data:
                            node_data.children.append(child_data)
            except Exception as e:
                logger.debug(f"Could not browse children: {e}")
        
        return node_data
        
    except Exception as e:
        logger.error(f"Error browsing node: {e}")
        return None


@router.get("/devices/{device_id}/opcua/browse", response_model=List[OPCUANode])
async def browse_opcua_tags(
    device_id: int,
    max_depth: int = 3,
    db: AsyncSession = Depends(get_db)
):
    """
    Browse OPC UA server tag tree for a device
    
    Returns hierarchical structure of OPC UA nodes that can be configured as tags
    """
    try:
        # Get device from database
        result = await db.execute(
            select(Device).where(Device.id == device_id)
        )
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        if device.protocol != "opcua":
            raise HTTPException(
                status_code=400, 
                detail=f"Device protocol is {device.protocol}, not OPC UA"
            )
        
        # Get OPC UA endpoint from device config
        config = device.config or {}
        endpoint = config.get("endpoint") or config.get("connection_string")
        
        if not endpoint:
            raise HTTPException(
                status_code=400,
                detail="Device does not have OPC UA endpoint configured"
            )
        
        logger.info(f"Browsing OPC UA server: {endpoint}")
        
        # Connect to OPC UA server
        client = Client(url=endpoint, timeout=10)
        await client.connect()
        
        try:
            # Get Objects node (root of custom nodes)
            objects = client.get_objects_node()
            
            # Browse from Objects node
            children = await objects.get_children()
            nodes = []
            
            for child in children:
                browse_name = await child.read_browse_name()
                # Filter for custom namespace (ns=2 in our case) or include all
                if browse_name.NamespaceIndex >= 2 or browse_name.Name == "TEAG":
                    node_data = await browse_opcua_node(client, child, level=0, max_level=max_depth)
                    if node_data:
                        nodes.append(node_data)
            
            return nodes
            
        finally:
            await client.disconnect()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error browsing OPC UA tags: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to browse OPC UA server: {str(e)}"
        )


@router.post("/devices/{device_id}/opcua/configure-tags")
async def configure_opcua_tags(
    device_id: int,
    request: BulkTagConfigRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Configure multiple tags for OPC UA data collection
    
    Creates Tag records in database that the gateway will use for data collection
    """
    try:
        # Verify device exists and is OPC UA
        result = await db.execute(
            select(Device).where(Device.id == device_id)
        )
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        if device.protocol != "opcua":
            raise HTTPException(
                status_code=400,
                detail=f"Device protocol is {device.protocol}, not OPC UA"
            )
        
        created_tags = []
        skipped_tags = []
        errors = []
        
        for tag_config in request.tags:
            try:
                # Check if tag already exists
                existing = await db.execute(
                    select(Tag).where(
                        and_(
                            Tag.device_id == device_id,
                            Tag.name == tag_config.tag_name
                        )
                    )
                )
                
                if existing.scalar_one_or_none():
                    skipped_tags.append(tag_config.tag_name)
                    continue
                
                # Determine SQLAlchemy data type from OPC UA data type
                data_type_map = {
                    "boolean": "bool",
                    "float": "float",
                    "double": "float",
                    "int": "int",
                    "integer": "int",
                    "string": "str",
                }
                
                sql_data_type = data_type_map.get(
                    tag_config.data_type.lower(), 
                    "float"
                )
                
                # Create new tag
                new_tag = Tag(
                    device_id=device_id,
                    name=tag_config.tag_name,
                    description=tag_config.description or tag_config.tag_name,
                    data_type=sql_data_type,
                    unit=tag_config.unit or "",
                    config={
                        "node_id": tag_config.node_id,
                        "opcua_data_type": tag_config.data_type,
                        "sample_interval_ms": tag_config.sample_interval_ms,
                    },
                    enabled=tag_config.enabled,
                )
                
                db.add(new_tag)
                created_tags.append(tag_config.tag_name)
                
            except Exception as e:
                logger.error(f"Error creating tag {tag_config.tag_name}: {e}")
                errors.append({
                    "tag_name": tag_config.tag_name,
                    "error": str(e)
                })
        
        # Commit all changes
        await db.commit()
        
        return {
            "success": True,
            "created_count": len(created_tags),
            "skipped_count": len(skipped_tags),
            "error_count": len(errors),
            "created_tags": created_tags,
            "skipped_tags": skipped_tags,
            "errors": errors,
            "message": f"Successfully configured {len(created_tags)} tags. "
                      f"{len(skipped_tags)} already existed. "
                      f"{len(errors)} errors."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring OPC UA tags: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure tags: {str(e)}"
        )


@router.get("/devices/{device_id}/tags")
async def get_device_tags(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all configured tags for a device
    """
    try:
        result = await db.execute(
            select(Tag).where(Tag.device_id == device_id).order_by(Tag.name)
        )
        tags = result.scalars().all()
        
        return {
            "device_id": device_id,
            "tag_count": len(tags),
            "tags": [
                {
                    "id": tag.id,
                    "name": tag.name,
                    "description": tag.description,
                    "data_type": tag.data_type,
                    "unit": tag.unit,
                    "enabled": tag.enabled,
                    "node_id": tag.config.get("node_id") if tag.config else None,
                    "sample_interval_ms": tag.config.get("sample_interval_ms", 1000) if tag.config else 1000,
                }
                for tag in tags
            ]
        }
    except Exception as e:
        logger.error(f"Error getting device tags: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get device tags: {str(e)}"
        )


@router.delete("/devices/{device_id}/tags/{tag_id}")
async def delete_tag(
    device_id: int,
    tag_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a configured tag
    """
    try:
        result = await db.execute(
            select(Tag).where(
                and_(Tag.id == tag_id, Tag.device_id == device_id)
            )
        )
        tag = result.scalar_one_or_none()
        
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")
        
        await db.delete(tag)
        await db.commit()
        
        return {
            "success": True,
            "message": f"Tag '{tag.name}' deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tag: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete tag: {str(e)}"
        )
