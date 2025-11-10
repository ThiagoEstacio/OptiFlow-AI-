"""
OPC-UA Browser Service - Dynamic node discovery similar to KEPServerEX
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from asyncua import Client, ua
from asyncua.common.node import Node

from app.core.logger import logger


class OPCUANodeInfo:
    """Information about an OPC-UA node"""

    def __init__(
        self,
        node_id: str,
        browse_name: str,
        display_name: str,
        node_class: str,
        data_type: Optional[str] = None,
        value: Any = None,
        description: Optional[str] = None,
        access_level: Optional[int] = None,
        parent_node_id: Optional[str] = None
    ):
        self.node_id = node_id
        self.browse_name = browse_name
        self.display_name = display_name
        self.node_class = node_class
        self.data_type = data_type
        self.value = value
        self.description = description
        self.access_level = access_level
        self.parent_node_id = parent_node_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "node_id": self.node_id,
            "browse_name": self.browse_name,
            "display_name": self.display_name,
            "node_class": self.node_class,
            "data_type": self.data_type,
            "value": self.value,
            "description": self.description,
            "access_level": self.access_level,
            "parent_node_id": self.parent_node_id,
            "readable": self.access_level and (self.access_level & 1) > 0 if self.access_level else False,
            "writable": self.access_level and (self.access_level & 2) > 0 if self.access_level else False,
        }


class OPCUABrowser:
    """
    OPC-UA browsing service for dynamic discovery
    Similar to KEPServerEX functionality
    """

    def __init__(self, endpoint: str, timeout: int = 10):
        """
        Initialize OPC-UA browser

        Args:
            endpoint: OPC-UA server endpoint URL
            timeout: Connection timeout in seconds
        """
        self.endpoint = endpoint
        self.timeout = timeout
        self.client: Optional[Client] = None
        self.namespaces: List[str] = []
        self._connected = False

    async def connect(self, max_retries: int = 3, retry_delay: float = 2.0) -> bool:
        """
        Connect to OPC-UA server with retry logic

        Args:
            max_retries: Maximum number of connection attempts
            retry_delay: Initial delay between retries in seconds (exponential backoff)
        """
        import asyncio

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {delay}s delay...")
                    await asyncio.sleep(delay)

                logger.info(f"Browser connecting to OPC-UA server: {self.endpoint}")

                self.client = Client(url=self.endpoint, timeout=self.timeout)
                await self.client.connect()

                # Get namespace array
                self.namespaces = await self.client.get_namespace_array()
                logger.info(f"✓ Browser connected. Found {len(self.namespaces)} namespaces")

                self._connected = True
                return True

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                logger.error(f"Browser connection failed (attempt {attempt + 1}/{max_retries}): {type(e).__name__}: {str(e)}")
                logger.error(f"Full traceback:\n{error_details}")
                self._connected = False

                if attempt < max_retries - 1:
                    continue
                else:
                    logger.error(f"Failed to connect after {max_retries} attempts")
                    return False

        return False

    async def disconnect(self):
        """Disconnect from OPC-UA server"""
        try:
            if self.client:
                await self.client.disconnect()
                self.client = None
            self._connected = False
            logger.info("Browser disconnected")
        except Exception as e:
            logger.error(f"Browser disconnect error: {str(e)}")

    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self._connected and self.client is not None

    async def get_namespaces(self) -> List[Dict[str, Any]]:
        """
        Get all available namespaces

        Returns:
            List of namespace information
        """
        if not self.is_connected:
            await self.connect()

        result = []
        for idx, ns in enumerate(self.namespaces):
            result.append({
                "index": idx,
                "uri": ns
            })

        return result

    async def browse_node(
        self,
        node_id: str = "i=85",
        recursive: bool = False,
        max_depth: int = 5,
        variable_only: bool = False
    ) -> List[OPCUANodeInfo]:
        """
        Browse OPC-UA node structure

        Args:
            node_id: Starting node ID (default: Objects folder "i=85")
            recursive: Browse recursively
            max_depth: Maximum recursion depth
            variable_only: Only return Variable nodes (readable tags)

        Returns:
            List of node information
        """
        if not self.is_connected:
            await self.connect()

        if not self.client:
            return []

        return await self._browse_recursive(
            node_id,
            recursive=recursive,
            max_depth=max_depth,
            current_depth=0,
            variable_only=variable_only,
            parent_node_id=None
        )

    async def _browse_recursive(
        self,
        node_id: str,
        recursive: bool,
        max_depth: int,
        current_depth: int,
        variable_only: bool,
        parent_node_id: Optional[str]
    ) -> List[OPCUANodeInfo]:
        """Recursive browsing implementation"""
        results = []

        try:
            node = self.client.get_node(node_id)
            children = await node.get_children()

            if current_depth == 0:
                logger.info(f"Browsing root node {node_id}, found {len(children)} children at depth 0")

            for child in children:
                try:
                    # Get basic node information
                    browse_name = await child.read_browse_name()
                    display_name = await child.read_display_name()
                    node_class = await child.read_node_class()

                    node_info = None

                    # Process Variable nodes (tags)
                    if node_class == ua.NodeClass.Variable:
                        try:
                            # Get data type
                            data_type_node = await child.read_data_type()
                            data_type = data_type_node.to_string()

                            # Get value
                            try:
                                value = await child.read_value()
                            except:
                                value = None

                            # Get description
                            try:
                                desc_variant = await child.read_attribute(ua.AttributeIds.Description)
                                description = desc_variant.Value.Text if desc_variant.Value else None
                            except:
                                description = None

                            # Get access level
                            try:
                                access_level = await child.read_attribute(ua.AttributeIds.AccessLevel)
                                access_level_value = access_level.Value.Value if access_level.Value else None
                            except:
                                access_level_value = None

                            node_info = OPCUANodeInfo(
                                node_id=child.nodeid.to_string(),
                                browse_name=browse_name.Name,
                                display_name=display_name.Text,
                                node_class=node_class.name,
                                data_type=data_type,
                                value=str(value) if value is not None else None,
                                description=description,
                                access_level=access_level_value,
                                parent_node_id=parent_node_id
                            )

                        except Exception as e:
                            logger.debug(f"Failed to get variable details: {str(e)}")

                    # Process Object nodes (folders)
                    elif node_class == ua.NodeClass.Object:
                        # Create node_info only if we want to include objects in results
                        if not variable_only:
                            node_info = OPCUANodeInfo(
                                node_id=child.nodeid.to_string(),
                                browse_name=browse_name.Name,
                                display_name=display_name.Text,
                                node_class=node_class.name,
                                parent_node_id=parent_node_id
                            )

                        # Always recurse into objects to find variables inside
                        # regardless of variable_only flag
                        if recursive and current_depth < max_depth:
                            child_results = await self._browse_recursive(
                                child.nodeid.to_string(),
                                recursive=True,
                                max_depth=max_depth,
                                current_depth=current_depth + 1,
                                variable_only=variable_only,
                                parent_node_id=node_id
                            )
                            results.extend(child_results)

                    # Add the node info if it was created
                    if node_info:
                        results.append(node_info)

                except Exception as e:
                    logger.debug(f"Failed to read child node: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Failed to browse node {node_id}: {str(e)}")

        return results

    async def discover_all_tags(self, namespace_filter: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Discover all readable tags (variables) in the server
        Similar to KEPServerEX tag discovery

        Args:
            namespace_filter: Only include tags from these namespace indexes

        Returns:
            List of tag dictionaries suitable for configuration
        """
        logger.info("Starting tag discovery...")

        # Browse from Objects folder recursively
        all_nodes = await self.browse_node(
            node_id="i=85",  # Objects folder
            recursive=True,
            max_depth=10,
            variable_only=True
        )

        logger.info(f"Browse completed. Found {len(all_nodes)} variable nodes total")

        tags = []
        filtered_out_namespace = 0
        filtered_out_access = 0

        for node in all_nodes:
            # Apply namespace filter if specified
            if namespace_filter:
                # Extract namespace index from node_id (format: ns=X;...)
                try:
                    ns_part = node.node_id.split(';')[0]
                    ns_index = int(ns_part.split('=')[1])
                    if ns_index not in namespace_filter:
                        filtered_out_namespace += 1
                        continue
                except:
                    filtered_out_namespace += 1
                    continue

            # Only include readable variables (or all if access_level is None)
            is_readable = node.access_level is None or (node.access_level & 1) > 0

            if is_readable:
                tag = {
                    "tag_name": node.browse_name,
                    "display_name": node.display_name,
                    "address": node.node_id,
                    "data_type": node.data_type,
                    "description": node.description,
                    "readable": True,
                    "writable": node.access_level and (node.access_level & 2) > 0,
                    "current_value": node.value
                }
                tags.append(tag)
            else:
                filtered_out_access += 1

        logger.info(f"Filtered out: {filtered_out_namespace} by namespace, {filtered_out_access} by access level")
        logger.info(f"✓ Discovered {len(tags)} readable tags")
        return tags

    async def search_tags(self, search_term: str, namespace_filter: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Search for tags by name

        Args:
            search_term: Search term (case-insensitive)
            namespace_filter: Only search in these namespaces

        Returns:
            List of matching tags
        """
        all_tags = await self.discover_all_tags(namespace_filter=namespace_filter)

        search_lower = search_term.lower()
        matches = [
            tag for tag in all_tags
            if search_lower in tag["tag_name"].lower() or
               search_lower in tag["display_name"].lower()
        ]

        logger.info(f"Found {len(matches)} tags matching '{search_term}'")
        return matches

    async def get_node_details(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific node

        Args:
            node_id: Node ID to query

        Returns:
            Detailed node information
        """
        if not self.is_connected:
            await self.connect()

        if not self.client:
            return None

        try:
            node = self.client.get_node(node_id)

            # Get all available attributes
            browse_name = await node.read_browse_name()
            display_name = await node.read_display_name()
            node_class = await node.read_node_class()

            details = {
                "node_id": node_id,
                "browse_name": browse_name.Name,
                "display_name": display_name.Text,
                "node_class": node_class.name
            }

            # Variable-specific attributes
            if node_class == ua.NodeClass.Variable:
                try:
                    data_type = await node.read_data_type()
                    details["data_type"] = data_type.to_string()
                except:
                    pass

                try:
                    value = await node.read_value()
                    details["value"] = str(value)
                except:
                    pass

                try:
                    access_level = await node.read_attribute(ua.AttributeIds.AccessLevel)
                    details["access_level"] = access_level.Value.Value
                except:
                    pass

            return details

        except Exception as e:
            logger.error(f"Failed to get node details for {node_id}: {str(e)}")
            return None


async def browse_opcua_server(endpoint: str, namespace_index: Optional[int] = None) -> Dict[str, Any]:
    """
    Convenience function to browse an OPC-UA server

    Args:
        endpoint: OPC-UA server endpoint
        namespace_index: Optional namespace to filter by

    Returns:
        Dictionary with namespaces and discovered tags
    """
    browser = OPCUABrowser(endpoint)

    try:
        connected = await browser.connect()
        if not connected:
            return {
                "success": False,
                "error": "Failed to connect to OPC-UA server"
            }

        # Get namespaces
        namespaces = await browser.get_namespaces()

        # Discover tags
        namespace_filter = [namespace_index] if namespace_index is not None else None
        tags = await browser.discover_all_tags(namespace_filter=namespace_filter)

        return {
            "success": True,
            "endpoint": endpoint,
            "namespaces": namespaces,
            "tags": tags,
            "tag_count": len(tags)
        }

    finally:
        await browser.disconnect()
