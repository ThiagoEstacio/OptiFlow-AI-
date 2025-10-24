"""
OPC UA Protocol Handler

Unified Architecture (OPC UA) is a machine-to-machine communication protocol
for industrial automation. It's platform-independent and provides a service-oriented
architecture.

Features:
- Connection management with security modes
- Address space browsing (recursive node discovery)
- Read/Write operations for nodes
- Subscription support for real-time data
- Multiple data type support
- Discovery of OPC UA servers on network

Uses asyncua (python-opcua-asyncio) library for async operations.
"""

import asyncio
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import time

from loguru import logger
from asyncua import Client, ua
from asyncua.common.node import Node
from asyncua.common.subscription import Subscription


class OPCUASecurityMode(str, Enum):
    """OPC UA security modes"""
    NONE = "None"
    SIGN = "Sign"
    SIGN_AND_ENCRYPT = "SignAndEncrypt"


class NodeClass(str, Enum):
    """OPC UA node classes"""
    OBJECT = "Object"
    VARIABLE = "Variable"
    METHOD = "Method"
    OBJECT_TYPE = "ObjectType"
    VARIABLE_TYPE = "VariableType"
    REFERENCE_TYPE = "ReferenceType"
    DATA_TYPE = "DataType"
    VIEW = "View"


@dataclass
class OPCUANodeInfo:
    """Information about an OPC UA node"""
    node_id: str
    browse_name: str
    display_name: str
    node_class: str
    parent_node_id: Optional[str] = None
    data_type: Optional[str] = None
    value: Optional[Any] = None
    access_level: Optional[int] = None
    description: Optional[str] = None
    namespace: Optional[int] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class OPCUAValue:
    """Represents an OPC UA value with metadata"""
    node_id: str
    value: Any
    data_type: Optional[str] = None
    quality: str = "Good"
    timestamp: Optional[float] = None
    server_timestamp: Optional[float] = None
    source_timestamp: Optional[float] = None
    error: Optional[str] = None


@dataclass
class OPCUAServerInfo:
    """OPC UA server information"""
    server_url: str
    server_name: Optional[str] = None
    server_state: Optional[str] = None
    namespaces: Optional[List[str]] = None
    connected: bool = False


class OPCUAClient:
    """
    OPC UA client with address space browsing capabilities.

    Features:
    - Connection management with security
    - Address space browsing (recursive)
    - Read/Write operations
    - Subscription support
    - Discovery services
    - Quality codes (Good/Bad/Uncertain)
    """

    def __init__(
        self,
        server_url: str,
        timeout: float = 10.0,
        security_mode: OPCUASecurityMode = OPCUASecurityMode.NONE
    ):
        """
        Initialize OPC UA client.

        Args:
            server_url: OPC UA server URL (e.g., "opc.tcp://192.168.1.100:4840")
            timeout: Connection timeout in seconds
            security_mode: Security mode (None, Sign, SignAndEncrypt)
        """
        self.server_url = server_url
        self.timeout = timeout
        self.security_mode = security_mode

        self._client: Optional[Client] = None
        self._connected = False
        self._subscription: Optional[Subscription] = None

        logger.info(f"OPC UA client initialized for {server_url}")

    async def connect(self) -> bool:
        """
        Connect to OPC UA server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self._client is not None:
                await self.disconnect()

            self._client = Client(url=self.server_url, timeout=self.timeout)

            # Set security mode
            if self.security_mode == OPCUASecurityMode.NONE:
                self._client.set_security_string("None")

            # Connect
            await self._client.connect()

            self._connected = True
            logger.info(f"Connected to OPC UA server at {self.server_url}")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to {self.server_url}: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from OPC UA server."""
        try:
            if self._subscription:
                await self._subscription.delete()
                self._subscription = None

            if self._client is not None:
                await self._client.disconnect()
                logger.info(f"Disconnected from {self.server_url}")

        except Exception as e:
            logger.error(f"Error disconnecting from {self.server_url}: {e}")

        finally:
            self._connected = False
            self._client = None

    def is_connected(self) -> bool:
        """Check if connected to OPC UA server."""
        return self._connected and self._client is not None

    async def get_server_info(self) -> Optional[OPCUAServerInfo]:
        """
        Get server information.

        Returns:
            OPCUAServerInfo object or None if failed
        """
        if not self.is_connected():
            return None

        try:
            # Get server name
            server_status_node = self._client.get_node("i=2256")  # ServerStatus
            server_state_node = self._client.get_node("i=2259")  # State

            server_state = await server_state_node.read_value()

            # Get namespaces
            namespaces = await self._client.get_namespace_array()

            return OPCUAServerInfo(
                server_url=self.server_url,
                server_name=self.server_url.split("//")[1].split(":")[0],
                server_state=str(server_state),
                namespaces=namespaces,
                connected=True
            )

        except Exception as e:
            logger.error(f"Failed to get server info: {e}")
            return OPCUAServerInfo(
                server_url=self.server_url,
                connected=False
            )

    async def read_node(self, node_id: str) -> OPCUAValue:
        """
        Read value from a node.

        Args:
            node_id: Node identifier (e.g., "ns=2;i=10" or "ns=2;s=Temperature")

        Returns:
            OPCUAValue object with value and metadata
        """
        if not self.is_connected():
            return OPCUAValue(
                node_id=node_id,
                value=None,
                quality="Bad",
                error="Not connected to server"
            )

        try:
            node = self._client.get_node(node_id)

            # Read data value
            data_value = await node.read_data_value()

            # Get data type
            try:
                data_type_node = await node.read_data_type()
                data_type = await data_type_node.read_browse_name()
                data_type_str = str(data_type)
            except:
                data_type_str = "Unknown"

            # Check quality
            quality = "Good"
            if data_value.StatusCode.is_bad():
                quality = "Bad"
            elif not data_value.StatusCode.is_good():
                quality = "Uncertain"

            return OPCUAValue(
                node_id=node_id,
                value=data_value.Value.Value if data_value.Value else None,
                data_type=data_type_str,
                quality=quality,
                timestamp=time.time(),
                server_timestamp=data_value.ServerTimestamp.timestamp() if data_value.ServerTimestamp else None,
                source_timestamp=data_value.SourceTimestamp.timestamp() if data_value.SourceTimestamp else None
            )

        except Exception as e:
            logger.error(f"Error reading node {node_id}: {e}")
            return OPCUAValue(
                node_id=node_id,
                value=None,
                quality="Bad",
                error=str(e)
            )

    async def write_node(self, node_id: str, value: Any) -> bool:
        """
        Write value to a node.

        Args:
            node_id: Node identifier
            value: Value to write

        Returns:
            True if write successful, False otherwise
        """
        if not self.is_connected():
            logger.error(f"Cannot write to {node_id}: Not connected")
            return False

        try:
            node = self._client.get_node(node_id)

            # Get data type to ensure correct value type
            data_type = await node.read_data_type_as_variant_type()

            # Create variant with correct type
            variant = ua.Variant(value, data_type)

            # Write value
            await node.write_value(variant)

            logger.debug(f"Successfully wrote {value} to {node_id}")
            return True

        except Exception as e:
            logger.error(f"Error writing to {node_id}: {e}")
            return False

    async def browse_address_space(
        self,
        root_node_id: str = "i=85",  # Objects folder
        max_depth: int = 10,
        filter_node_classes: Optional[List[str]] = None
    ) -> List[OPCUANodeInfo]:
        """
        Recursively browse the OPC UA address space.

        Args:
            root_node_id: Starting node ID (default: Objects folder)
            max_depth: Maximum recursion depth
            filter_node_classes: Filter by node classes (e.g., ["Variable"])

        Returns:
            List of OPCUANodeInfo objects
        """
        if not self.is_connected():
            if not await self.connect():
                return []

        nodes = []
        visited: Set[str] = set()

        try:
            root_node = self._client.get_node(root_node_id)
            await self._browse_recursive(
                root_node,
                nodes,
                visited,
                max_depth=max_depth,
                current_depth=0,
                filter_node_classes=filter_node_classes
            )

        except Exception as e:
            logger.error(f"Error browsing address space: {e}")

        logger.info(f"Found {len(nodes)} nodes in address space")
        return nodes

    async def _browse_recursive(
        self,
        node: Node,
        nodes: List[OPCUANodeInfo],
        visited: Set[str],
        max_depth: int,
        current_depth: int,
        filter_node_classes: Optional[List[str]] = None,
        parent_node_id: Optional[str] = None
    ) -> None:
        """
        Recursive helper for browsing address space.

        Args:
            node: Current node to browse
            nodes: List to accumulate found nodes
            visited: Set of visited node IDs
            max_depth: Maximum recursion depth
            current_depth: Current recursion depth
            filter_node_classes: Filter by node classes
            parent_node_id: Parent node ID
        """
        if current_depth >= max_depth:
            return

        try:
            node_id_str = node.nodeid.to_string()

            # Avoid cycles
            if node_id_str in visited:
                return

            visited.add(node_id_str)

            # Get node attributes
            node_class = await node.read_node_class()
            node_class_name = str(node_class).split(".")[-1]

            # Apply filter
            if filter_node_classes and node_class_name not in filter_node_classes:
                # Still browse children
                children = await node.get_children()
                for child in children:
                    await self._browse_recursive(
                        child,
                        nodes,
                        visited,
                        max_depth,
                        current_depth + 1,
                        filter_node_classes,
                        node_id_str
                    )
                return

            # Get node info
            browse_name = await node.read_browse_name()
            display_name = await node.read_display_name()

            node_info = OPCUANodeInfo(
                node_id=node_id_str,
                browse_name=str(browse_name),
                display_name=str(display_name),
                node_class=node_class_name,
                parent_node_id=parent_node_id,
                namespace=node.nodeid.NamespaceIndex
            )

            # If it's a variable, get additional info
            if node_class == ua.NodeClass.Variable:
                try:
                    # Get data type
                    data_type = await node.read_data_type()
                    data_type_name = await data_type.read_browse_name()
                    node_info.data_type = str(data_type_name)

                    # Get access level
                    access_level = await node.read_attribute(ua.AttributeIds.AccessLevel)
                    node_info.access_level = access_level.Value.Value

                    # Optionally read value (can be slow)
                    # value = await node.read_value()
                    # node_info.value = value

                except Exception as e:
                    logger.debug(f"Could not get variable attributes for {node_id_str}: {e}")

            nodes.append(node_info)

            # Browse children
            children = await node.get_children()
            for child in children:
                await self._browse_recursive(
                    child,
                    nodes,
                    visited,
                    max_depth,
                    current_depth + 1,
                    filter_node_classes,
                    node_id_str
                )

        except Exception as e:
            logger.debug(f"Error browsing node: {e}")

    async def get_node_hierarchy(self, node_id: str) -> str:
        """
        Get hierarchical path for a node.

        Args:
            node_id: Node identifier

        Returns:
            Hierarchical path (e.g., "Objects/DeviceSet/Device1/Temperature")
        """
        if not self.is_connected():
            return node_id

        try:
            node = self._client.get_node(node_id)
            path_parts = []

            current = node

            # Traverse up to root
            while True:
                display_name = await current.read_display_name()
                path_parts.insert(0, str(display_name))

                # Get parent
                parents = await current.get_parents()
                if not parents or len(path_parts) > 20:  # Prevent infinite loop
                    break

                current = parents[0]

                # Stop at Objects or Root
                if current.nodeid.Identifier in [84, 85, 86]:  # Root, Objects, Types
                    break

            return "/".join(path_parts)

        except Exception as e:
            logger.error(f"Error getting node hierarchy: {e}")
            return node_id

    async def filter_industrial_tags(
        self,
        nodes: List[OPCUANodeInfo]
    ) -> List[OPCUANodeInfo]:
        """
        Filter nodes to get industrial process tags.

        Removes system nodes and keeps only variables with numeric/boolean types.

        Args:
            nodes: List of nodes

        Returns:
            Filtered list of industrial tags
        """
        industrial_tags = []

        for node in nodes:
            # Only variables
            if node.node_class != "Variable":
                continue

            # Skip system variables
            if node.browse_name.startswith("Server") or \
               node.browse_name.startswith("System"):
                continue

            # Skip if no data type
            if not node.data_type:
                continue

            # Filter by data type (numeric, boolean, string)
            data_type_lower = node.data_type.lower()
            if any(t in data_type_lower for t in [
                "int", "uint", "float", "double", "bool", "byte",
                "real", "number", "string"
            ]):
                industrial_tags.append(node)

        return industrial_tags

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


# Network discovery of OPC UA servers
async def discover_opcua_servers(
    discovery_url: str = "opc.tcp://localhost:4840"
) -> List[str]:
    """
    Discover OPC UA servers on the network.

    Args:
        discovery_url: Discovery server URL

    Returns:
        List of discovered server URLs
    """
    try:
        client = Client(discovery_url)
        await client.connect()

        # Find servers
        servers = await client.find_servers()

        # Get URLs
        server_urls = []
        for server in servers:
            if server.DiscoveryUrls:
                server_urls.extend(server.DiscoveryUrls)

        await client.disconnect()

        return list(set(server_urls))  # Remove duplicates

    except Exception as e:
        logger.error(f"Error discovering OPC UA servers: {e}")
        return []
