"""
OPC UA Client Service for SmartPort
Handles connection, tag browsing, and data collection from OPC UA servers
"""
from typing import List, Dict, Optional, Any
from asyncua import Client, ua
from asyncua.common.node import Node
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class OPCUAClient:
    """
    OPC UA Client for connecting to PLCs and industrial devices
    """

    def __init__(self, endpoint_url: str, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize OPC UA client

        Args:
            endpoint_url: OPC UA server endpoint (e.g., "opc.tcp://localhost:4840")
            username: Optional username for authentication
            password: Optional password for authentication
        """
        self.endpoint_url = endpoint_url
        self.username = username
        self.password = password
        self.client = Client(url=endpoint_url)
        self._connected = False

    async def connect(self) -> bool:
        """
        Connect to OPC UA server

        Returns:
            bool: True if connection successful
        """
        try:
            if self.username and self.password:
                self.client.set_user(self.username)
                self.client.set_password(self.password)

            await self.client.connect()
            self._connected = True
            logger.info(f"Connected to OPC UA server: {self.endpoint_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OPC UA server {self.endpoint_url}: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """Disconnect from OPC UA server"""
        try:
            if self._connected:
                await self.client.disconnect()
                self._connected = False
                logger.info(f"Disconnected from OPC UA server: {self.endpoint_url}")
        except Exception as e:
            logger.error(f"Error disconnecting from OPC UA server: {e}")

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to OPC UA server and get server info

        Returns:
            Dict with connection status and server information
        """
        try:
            connected = await self.connect()
            if not connected:
                return {
                    "success": False,
                    "error": "Failed to connect to OPC UA server"
                }

            # Get server information
            server_info = {
                "success": True,
                "endpoint": self.endpoint_url,
                "namespace_array": await self.client.get_namespace_array(),
                "server_state": str(await self.client.get_node("ns=0;i=2259").read_value()),
            }

            # Try to get server status
            try:
                server_status = await self.client.get_node("ns=0;i=2256").read_value()
                server_info["build_info"] = {
                    "product_name": server_status.ProductName,
                    "product_uri": server_status.ProductUri,
                    "manufacturer_name": server_status.ManufacturerName,
                    "software_version": server_status.SoftwareVersion,
                }
            except:
                pass

            await self.disconnect()
            return server_info

        except Exception as e:
            logger.error(f"Error testing connection: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def browse_tags(self, node_id: str = "ns=0;i=85", max_depth: int = 10) -> List[Dict[str, Any]]:
        """
        Browse OPC UA server to discover all available tags

        Args:
            node_id: Starting node ID (default: Objects folder)
            max_depth: Maximum depth to browse

        Returns:
            List of discovered tags with metadata
        """
        if not self._connected:
            await self.connect()

        tags = []
        try:
            root_node = self.client.get_node(node_id)
            await self._browse_node_recursive(root_node, tags, current_depth=0, max_depth=max_depth)
            logger.info(f"Discovered {len(tags)} tags from OPC UA server")
        except Exception as e:
            logger.error(f"Error browsing tags: {e}")

        return tags

    async def _browse_node_recursive(
        self,
        node: Node,
        tags: List[Dict[str, Any]],
        current_depth: int,
        max_depth: int,
        parent_path: str = ""
    ):
        """
        Recursively browse OPC UA node tree

        Args:
            node: Current node to browse
            tags: List to append discovered tags
            current_depth: Current recursion depth
            max_depth: Maximum recursion depth
            parent_path: Path of parent nodes
        """
        if current_depth >= max_depth:
            return

        try:
            # Get node information
            node_class = await node.read_node_class()
            browse_name = await node.read_browse_name()
            display_name = await node.read_display_name()

            # Build full path
            current_name = display_name.Text
            full_path = f"{parent_path}/{current_name}" if parent_path else current_name

            # If it's a Variable node (actual tag), extract its information
            if node_class == ua.NodeClass.Variable:
                try:
                    node_id = node.nodeid.to_string()
                    data_value = await node.read_data_value()
                    data_type = await node.read_data_type()
                    data_type_name = (await self.client.get_node(data_type).read_browse_name()).Name

                    # Map OPC UA data types to our TagDataType
                    type_mapping = {
                        "Boolean": "boolean",
                        "SByte": "integer",
                        "Byte": "integer",
                        "Int16": "integer",
                        "UInt16": "integer",
                        "Int32": "integer",
                        "UInt32": "integer",
                        "Int64": "integer",
                        "UInt64": "integer",
                        "Float": "float",
                        "Double": "double",
                        "String": "string",
                    }

                    tag_data_type = type_mapping.get(data_type_name, "float")

                    # Try to get description
                    description = ""
                    try:
                        desc_node = await node.read_description()
                        if desc_node:
                            description = desc_node.Text
                    except:
                        pass

                    # Build tag metadata
                    tag_info = {
                        "name": current_name,
                        "display_name": display_name.Text,
                        "browse_name": browse_name.Name,
                        "node_id": node_id,
                        "address": node_id,  # For our system, address = node_id
                        "data_type": tag_data_type,
                        "full_path": full_path,
                        "description": description or f"OPC UA tag: {full_path}",
                        "namespace_index": node.nodeid.NamespaceIndex,
                        "current_value": str(data_value.Value.Value) if data_value.Value else None,
                        "quality": str(data_value.StatusCode),
                        "timestamp": data_value.SourceTimestamp.isoformat() if data_value.SourceTimestamp else None,
                    }

                    tags.append(tag_info)

                except Exception as e:
                    logger.debug(f"Could not read variable {current_name}: {e}")

            # Browse children
            children = await node.get_children()
            for child in children:
                await self._browse_node_recursive(
                    child,
                    tags,
                    current_depth + 1,
                    max_depth,
                    full_path
                )

        except Exception as e:
            logger.debug(f"Error browsing node: {e}")

    async def read_tag(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Read value from a specific tag

        Args:
            node_id: OPC UA node ID

        Returns:
            Dict with value, quality, and timestamp
        """
        if not self._connected:
            await self.connect()

        try:
            node = self.client.get_node(node_id)
            data_value = await node.read_data_value()

            return {
                "value": data_value.Value.Value,
                "quality": str(data_value.StatusCode),
                "timestamp": data_value.SourceTimestamp.isoformat() if data_value.SourceTimestamp else None,
            }
        except Exception as e:
            logger.error(f"Error reading tag {node_id}: {e}")
            return None

    async def read_multiple_tags(self, node_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Read values from multiple tags (batch read)

        Args:
            node_ids: List of OPC UA node IDs

        Returns:
            Dict mapping node_id to value data
        """
        if not self._connected:
            await self.connect()

        results = {}
        try:
            nodes = [self.client.get_node(node_id) for node_id in node_ids]
            data_values = await self.client.read_values(nodes)

            for node_id, data_value in zip(node_ids, data_values):
                try:
                    results[node_id] = {
                        "value": data_value.Value.Value if hasattr(data_value, 'Value') else data_value,
                        "quality": str(data_value.StatusCode) if hasattr(data_value, 'StatusCode') else "Good",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                except Exception as e:
                    logger.error(f"Error processing tag {node_id}: {e}")
                    results[node_id] = None

        except Exception as e:
            logger.error(f"Error reading multiple tags: {e}")

        return results

    async def subscribe_to_tags(self, node_ids: List[str], callback):
        """
        Subscribe to tag changes (for real-time monitoring)

        Args:
            node_ids: List of OPC UA node IDs to subscribe
            callback: Callback function to handle value changes
        """
        if not self._connected:
            await self.connect()

        try:
            subscription = await self.client.create_subscription(500, callback)
            nodes = [self.client.get_node(node_id) for node_id in node_ids]
            await subscription.subscribe_data_change(nodes)
            logger.info(f"Subscribed to {len(node_ids)} tags")
            return subscription
        except Exception as e:
            logger.error(f"Error subscribing to tags: {e}")
            return None
