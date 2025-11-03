"""
OPC UA Tag Value Reader Service

Reads current values from OPC UA server and updates tags in database
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from asyncua import Client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import logging

from app.models.tag import Tag

logger = logging.getLogger(__name__)


class OPCUATagReader:
    """Service to read tag values from OPC UA server"""
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.client: Optional[Client] = None
        self.connected = False
    
    async def connect(self) -> bool:
        """Connect to OPC UA server"""
        try:
            self.client = Client(url=self.endpoint)
            await self.client.connect()
            self.connected = True
            logger.info(f"Connected to OPC UA server: {self.endpoint}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OPC UA server: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from OPC UA server"""
        if self.client and self.connected:
            await self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from OPC UA server")
    
    async def read_tag_value(self, node_address: str) -> Optional[Dict]:
        """
        Read a single tag value from OPC UA server
        
        Args:
            node_address: OPC UA node address (e.g., "ns=2;s=TEAG.ARZ.GATES.GATE01.POSICAO.PV")
        
        Returns:
            Dict with value, quality, timestamp or None if error
        """
        if not self.connected or not self.client:
            return None
        
        try:
            node = self.client.get_node(node_address)
            data_value = await node.read_data_value()
            
            # Extract value
            value = data_value.Value.Value
            
            # Convert value to string for storage (max 100 chars)
            if isinstance(value, bool):
                value_str = "1" if value else "0"
            elif isinstance(value, (int, float)):
                value_str = str(value)
            elif isinstance(value, str):
                value_str = value[:100]  # Truncate long strings
            elif isinstance(value, list):
                # For arrays, show first few elements
                value_str = str(value[:3])[:100] if len(value) > 3 else str(value)[:100]
            elif value is None:
                value_str = "NULL"
            else:
                # For complex objects, try to get a meaningful representation
                try:
                    # Try to get numeric value if it has one
                    if hasattr(value, 'Value'):
                        value_str = str(value.Value)[:100]
                    elif hasattr(value, '__str__'):
                        value_str = str(value)[:100]
                    else:
                        value_str = str(type(value).__name__)[:100]
                except:
                    value_str = "N/A"
            
            # Get quality
            quality = data_value.StatusCode.name if data_value.StatusCode else "Good"
            
            # Get timestamp
            timestamp = data_value.SourceTimestamp or datetime.utcnow()
            
            return {
                "value": value_str,
                "quality": quality,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Error reading tag {node_address}: {e}")
            return None
    
    async def read_multiple_tags(self, node_addresses: List[str]) -> Dict[str, Dict]:
        """
        Read multiple tag values from OPC UA server
        
        Args:
            node_addresses: List of OPC UA node addresses
        
        Returns:
            Dict mapping address to value data
        """
        results = {}
        
        for address in node_addresses:
            result = await self.read_tag_value(address)
            if result:
                results[address] = result
        
        return results


async def update_tag_values_from_opcua(
    db: AsyncSession,
    opcua_endpoint: str,
    device_id: Optional[str] = None,
    limit: int = 100
) -> Dict:
    """
    Read tag values from OPC UA server and update database
    
    Args:
        db: Database session
        opcua_endpoint: OPC UA server endpoint
        device_id: Optional device ID to filter tags
        limit: Maximum number of tags to update
    
    Returns:
        Dict with update statistics
    """
    # Get tags from database
    query = select(Tag).limit(limit)
    if device_id:
        query = query.where(Tag.device_id == device_id)
    
    result = await db.execute(query)
    tags = result.scalars().all()
    
    if not tags:
        return {"success": False, "message": "No tags found", "updated": 0}
    
    # Connect to OPC UA server
    reader = OPCUATagReader(opcua_endpoint)
    if not await reader.connect():
        return {"success": False, "message": "Failed to connect to OPC UA server", "updated": 0}
    
    try:
        # Read all tag values
        addresses = [tag.address for tag in tags]
        values = await reader.read_multiple_tags(addresses)
        
        # Update tags in database
        updated_count = 0
        for tag in tags:
            if tag.address in values:
                value_data = values[tag.address]
                
                # Update tag with new value
                tag.last_value = value_data["value"]
                tag.last_quality = value_data["quality"]
                tag.last_timestamp = value_data["timestamp"]
                
                updated_count += 1
        
        # Commit changes
        await db.commit()
        
        logger.info(f"Updated {updated_count} tag values from OPC UA server")
        
        return {
            "success": True,
            "message": f"Updated {updated_count} tags",
            "updated": updated_count,
            "total": len(tags)
        }
        
    except Exception as e:
        logger.error(f"Error updating tag values: {e}")
        await db.rollback()
        return {"success": False, "message": str(e), "updated": 0}
    
    finally:
        await reader.disconnect()
