"""
OPC-UA Gateway Implementation

Provides connectivity to OPC-UA servers using the asyncua library.
OPC-UA is the universal standard for industrial communication.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

try:
    from asyncua import Client
    from asyncua.ua import NodeId
    ASYNCUA_AVAILABLE = True
except ImportError:
    ASYNCUA_AVAILABLE = False
    Client = None
    NodeId = None

from .base_gateway import BaseGateway, DataPoint, GatewayStatus

logger = logging.getLogger(__name__)


class OPCUAGateway(BaseGateway):
    """
    OPC-UA Gateway implementation.

    Connects to OPC-UA servers and reads data from configured nodes.

    Configuration example:
    {
        "endpoint": "opc.tcp://192.168.1.100:4840",
        "namespace": "urn:shiploader:server",
        "security_policy": "None",  # or "Basic256Sha256"
        "username": null,
        "password": null,
        "tags": [
            {
                "tag_name": "shiploader_belt_speed",
                "address_config": {
                    "node_id": "ns=2;s=Belt.Speed"
                },
                "data_type": "float",
                "unit": "m/s"
            }
        ]
    }
    """

    def __init__(self, name: str, config: Dict[str, Any], max_buffer_size: int = 10000):
        if not ASYNCUA_AVAILABLE:
            raise ImportError(
                "asyncua library is not installed. "
                "Install it with: pip install asyncua"
            )

        super().__init__(name, config, max_buffer_size)

        self.endpoint = config.get('connection_config', {}).get('endpoint')
        if not self.endpoint:
            raise ValueError("OPC-UA endpoint is required in connection_config")

        self.namespace = config.get('connection_config', {}).get('namespace', '')
        self.security_policy = config.get('connection_config', {}).get('security_policy', 'None')
        self.username = config.get('connection_config', {}).get('username')
        self.password = config.get('connection_config', {}).get('password')

        self.client: Optional[Client] = None
        self._node_cache: Dict[str, Any] = {}  # Cache node objects

    async def connect(self) -> bool:
        """
        Connect to OPC-UA server.

        Returns:
            bool: True if connection successful
        """
        try:
            logger.info(f"{self.name}: Connecting to OPC-UA server at {self.endpoint}")

            # Create client
            self.client = Client(url=self.endpoint)

            # Set security policy
            if self.security_policy != "None":
                await self.client.set_security_string(
                    f"{self.security_policy},SignAndEncrypt,certificate.der,private_key.pem"
                )

            # Set user authentication if provided
            if self.username and self.password:
                self.client.set_user(self.username)
                self.client.set_password(self.password)

            # Connect
            await self.client.connect()

            # Test connection by reading server state
            server_state = await self.client.get_node("ns=0;i=2259").read_value()
            logger.info(f"{self.name}: Connected successfully. Server state: {server_state}")

            return True

        except Exception as e:
            logger.error(f"{self.name}: Connection failed: {e}")
            self.client = None
            raise

    async def disconnect(self) -> None:
        """Disconnect from OPC-UA server."""
        if self.client:
            try:
                await self.client.disconnect()
                logger.info(f"{self.name}: Disconnected")
            except Exception as e:
                logger.error(f"{self.name}: Error during disconnect: {e}")
            finally:
                self.client = None
                self._node_cache.clear()
                self.status = GatewayStatus.DISCONNECTED

    async def _get_node(self, node_id_str: str):
        """
        Get node object (with caching).

        Args:
            node_id_str: Node ID string (e.g., "ns=2;s=Belt.Speed")

        Returns:
            Node object
        """
        if node_id_str not in self._node_cache:
            node = self.client.get_node(node_id_str)
            self._node_cache[node_id_str] = node

        return self._node_cache[node_id_str]

    async def read_tag(self, tag_config: Dict[str, Any]) -> Optional[DataPoint]:
        """
        Read a single tag from OPC-UA server.

        Args:
            tag_config: Tag configuration with address_config containing node_id

        Returns:
            DataPoint if successful, None if error
        """
        if not self.client or self.status != GatewayStatus.CONNECTED:
            return None

        try:
            tag_name = tag_config.get('tag_name')
            node_id_str = tag_config.get('address_config', {}).get('node_id')

            if not node_id_str:
                logger.error(f"{self.name}: No node_id in tag config for {tag_name}")
                return None

            # Get node
            node = await self._get_node(node_id_str)

            # Read value and status
            data_value = await node.read_data_value()
            value = data_value.Value.Value
            status_code = data_value.StatusCode

            # Apply scaling if configured
            scale_factor = tag_config.get('scale_factor', 1.0)
            offset = tag_config.get('offset', 0.0)

            if isinstance(value, (int, float)):
                value = (value * scale_factor) + offset

            # Determine quality based on status code
            quality = "good" if status_code.is_good() else "bad"

            # Create data point
            data_point = DataPoint(
                tag_name=tag_name,
                value=value,
                quality=quality,
                timestamp=data_value.SourceTimestamp or datetime.utcnow()
            )

            return data_point

        except Exception as e:
            logger.error(f"{self.name}: Error reading tag {tag_name}: {e}")
            return None

    async def read_multiple_tags(self, tag_configs: List[Dict[str, Any]]) -> List[DataPoint]:
        """
        Read multiple tags from OPC-UA server.

        Uses batch reading for better performance when available.

        Args:
            tag_configs: List of tag configurations

        Returns:
            List of DataPoints
        """
        if not self.client or self.status != GatewayStatus.CONNECTED:
            return []

        # Filter only enabled tags
        enabled_tags = [tag for tag in tag_configs if tag.get('enabled', True)]

        if not enabled_tags:
            return []

        data_points = []

        try:
            # Batch read all nodes
            nodes = []
            for tag_config in enabled_tags:
                node_id_str = tag_config.get('address_config', {}).get('node_id')
                if node_id_str:
                    node = await self._get_node(node_id_str)
                    nodes.append((node, tag_config))

            # Read all values
            values = await self.client.read_values([node for node, _ in nodes])

            # Create data points
            for (node, tag_config), value in zip(nodes, values):
                tag_name = tag_config.get('tag_name')

                # Apply scaling
                scale_factor = tag_config.get('scale_factor', 1.0)
                offset = tag_config.get('offset', 0.0)

                if isinstance(value, (int, float)):
                    value = (value * scale_factor) + offset

                data_point = DataPoint(
                    tag_name=tag_name,
                    value=value,
                    quality="good",
                    timestamp=datetime.utcnow()
                )
                data_points.append(data_point)

        except Exception as e:
            logger.error(f"{self.name}: Error in batch read: {e}")

            # Fallback to individual reads
            for tag_config in enabled_tags:
                try:
                    data_point = await self.read_tag(tag_config)
                    if data_point:
                        data_points.append(data_point)
                except Exception as tag_error:
                    logger.error(f"{self.name}: Failed to read {tag_config.get('tag_name')}: {tag_error}")

        return data_points

    async def browse_nodes(self, parent_node_id: str = "ns=0;i=85") -> List[Dict[str, Any]]:
        """
        Browse OPC-UA server nodes (useful for discovery).

        Args:
            parent_node_id: Parent node to start browsing from (default: Objects folder)

        Returns:
            List of node information dictionaries
        """
        if not self.client or self.status != GatewayStatus.CONNECTED:
            return []

        try:
            parent_node = await self._get_node(parent_node_id)
            children = await parent_node.get_children()

            nodes_info = []
            for child in children:
                try:
                    browse_name = await child.read_browse_name()
                    display_name = await child.read_display_name()
                    node_class = await child.read_node_class()
                    node_id = child.nodeid.to_string()

                    nodes_info.append({
                        "node_id": node_id,
                        "browse_name": browse_name.Name,
                        "display_name": display_name.Text,
                        "node_class": node_class.name,
                    })
                except Exception as e:
                    logger.warning(f"{self.name}: Error browsing child node: {e}")

            return nodes_info

        except Exception as e:
            logger.error(f"{self.name}: Error browsing nodes: {e}")
            return []
