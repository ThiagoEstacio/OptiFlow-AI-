"""
OPC UA Discovery Service

Discovers OPC UA servers and browses tag structures.
Reuses code from backend PLC service.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

# OPC UA client
try:
    from asyncua import Client as OPCClient, ua
    HAS_OPCUA = True
except ImportError:
    HAS_OPCUA = False
    logger.warning("asyncua not installed. OPC UA discovery will not work.")

logger = logging.getLogger(__name__)


@dataclass
class OPCUAServer:
    """Represents a discovered OPC UA server"""
    url: str
    application_uri: Optional[str] = None
    product_uri: Optional[str] = None
    server_name: Optional[str] = None
    namespaces: List[str] = field(default_factory=list)
    discovered_tags: List[Dict[str, Any]] = field(default_factory=list)
    responsive: bool = False
    discovered_at: datetime = field(default_factory=datetime.utcnow)


class OPCUADiscovery:
    """
    OPC UA server and tag discovery

    Features:
    - Test server connectivity
    - Get server information
    - Browse complete tag tree
    - Generate tag configurations
    """

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.discovered_servers: List[OPCUAServer] = []

    async def test_connection(self, url: str) -> Dict[str, Any]:
        """
        Test connection to OPC UA server

        Args:
            url: OPC UA server URL (e.g., "opc.tcp://localhost:4840")

        Returns:
            Connection test result with server info
        """
        if not HAS_OPCUA:
            return {"success": False, "error": "asyncua not installed"}

        result = {
            "success": False,
            "url": url,
            "server_info": None,
            "error": None
        }

        temp_client = None
        try:
            temp_client = OPCClient(url=url, timeout=self.timeout)
            await temp_client.connect()

            # Get server info
            server_info = {
                "application_uri": str(temp_client.application_uri),
                "product_uri": str(temp_client.product_uri),
                "server_name": str(temp_client.name),
            }

            # Try to get namespaces
            try:
                ns_node = temp_client.get_node("i=2255")  # NamespaceArray node
                namespaces = await ns_node.read_value()
                server_info["namespaces"] = namespaces
            except:
                pass

            result["success"] = True
            result["server_info"] = server_info
            logger.info(f"Successfully connected to OPC UA server: {url}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Failed to connect to OPC UA server {url}: {e}")
        finally:
            if temp_client:
                try:
                    await temp_client.disconnect()
                except:
                    pass

        return result

    async def discover_server(
        self,
        url: str,
        node_id: str = "i=85",
        max_depth: int = 10,
        include_properties: bool = False
    ) -> OPCUAServer:
        """
        Discover an OPC UA server and browse its tags

        Args:
            url: OPC UA server URL
            node_id: Starting node ID for browsing (default: Objects folder)
            max_depth: Maximum browse depth
            include_properties: Include property nodes

        Returns:
            OPCUAServer with discovered tags
        """
        if not HAS_OPCUA:
            logger.error("asyncua not installed")
            return None

        logger.info(f"Discovering OPC UA server: {url}")

        server = OPCUAServer(url=url)

        client = None
        try:
            client = OPCClient(url=url, timeout=self.timeout)
            await client.connect()

            server.responsive = True

            # Get server info
            server.application_uri = str(client.application_uri)
            server.product_uri = str(client.product_uri)
            server.server_name = str(client.name)

            # Get namespaces
            try:
                ns_node = client.get_node("i=2255")
                namespaces = await ns_node.read_value()
                server.namespaces = namespaces
            except:
                pass

            # Browse tags
            discovered_tags = await self._browse_tags(
                client,
                node_id=node_id,
                max_depth=max_depth,
                include_properties=include_properties
            )

            server.discovered_tags = discovered_tags

            logger.info(f"Discovery complete. Found {len(discovered_tags)} tags")

        except Exception as e:
            logger.error(f"Error discovering server {url}: {e}")
        finally:
            if client:
                try:
                    await client.disconnect()
                except:
                    pass

        self.discovered_servers.append(server)
        return server

    async def _browse_tags(
        self,
        client: OPCClient,
        node_id: str = "i=85",
        max_depth: int = 10,
        include_properties: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Browse OPC UA server tree and discover all variables/tags

        This is the same implementation as in backend PLCService
        """
        discovered_tags = []

        async def browse_node(node, current_path: str = "", depth: int = 0):
            """Recursively browse nodes"""
            if depth > max_depth:
                return

            try:
                # Get node class
                node_class = await node.read_node_class()

                # Get browse name
                browse_name = await node.read_browse_name()
                node_name = browse_name.Name

                # Build path
                path = f"{current_path}/{node_name}" if current_path else node_name

                # If it's a Variable node, extract tag information
                if node_class == ua.NodeClass.Variable:
                    try:
                        # Get data type
                        data_type_node = await node.read_data_type()
                        data_type = await self._get_data_type_name(data_type_node)

                        # Get description
                        try:
                            description_attr = await node.read_description()
                            description = description_attr.Text if description_attr else ""
                        except:
                            description = ""

                        # Get current value
                        try:
                            value = await node.read_value()
                            value_type = type(value).__name__
                        except:
                            value = None
                            value_type = "Unknown"

                        # Get access level
                        try:
                            access_level = await node.read_attribute(ua.AttributeIds.AccessLevel)
                            writable = bool(access_level.Value.Value & 0x02)
                        except:
                            writable = False

                        # Get node ID string
                        node_id_str = node.nodeid.to_string()

                        tag_info = {
                            "name": node_name,
                            "path": path,
                            "node_id": node_id_str,
                            "data_type": data_type,
                            "value_type": value_type,
                            "description": description,
                            "current_value": value,
                            "writable": writable,
                        }

                        discovered_tags.append(tag_info)

                    except Exception as e:
                        logger.warning(f"Error reading variable {path}: {e}")

                # Browse children
                try:
                    children = await node.get_children()
                    for child in children:
                        # Skip properties unless explicitly requested
                        if not include_properties:
                            child_browse_name = await child.read_browse_name()
                            if child_browse_name.NamespaceIndex == 0:
                                continue

                        await browse_node(child, path, depth + 1)
                except Exception as e:
                    logger.debug(f"No children for node {path}: {e}")

            except Exception as e:
                logger.warning(f"Error browsing node {current_path}: {e}")

        # Start browsing
        try:
            root_node = client.get_node(node_id)
            await browse_node(root_node)
        except Exception as e:
            logger.error(f"Error starting browse: {e}")

        return discovered_tags

    async def _get_data_type_name(self, data_type_node) -> str:
        """Convert OPC UA data type node to readable name"""
        try:
            type_map = {
                "i=1": "Boolean",
                "i=2": "SByte",
                "i=3": "Byte",
                "i=4": "Int16",
                "i=5": "UInt16",
                "i=6": "Int32",
                "i=7": "UInt32",
                "i=8": "Int64",
                "i=9": "UInt64",
                "i=10": "Float",
                "i=11": "Double",
                "i=12": "String",
                "i=13": "DateTime",
            }
            node_id_str = data_type_node.to_string()
            return type_map.get(node_id_str, node_id_str)
        except:
            return "Unknown"

    def get_discovered_servers(self) -> List[OPCUAServer]:
        """Get list of all discovered OPC UA servers"""
        return self.discovered_servers

    def clear_discovered_servers(self):
        """Clear the list of discovered servers"""
        self.discovered_servers = []
