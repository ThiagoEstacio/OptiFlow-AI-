"""
PLC Integration Service

Support for multiple protocols:
- OPC UA (recommended for modern PLCs)
- Modbus TCP (for legacy equipment)
- S7 (Siemens)
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# OPC UA
try:
    from asyncua import Client as OPCClient, ua
    HAS_OPCUA = True
except ImportError:
    HAS_OPCUA = False

# Modbus
try:
    from pymodbus.client import AsyncModbusTcpClient
    HAS_MODBUS = True
except ImportError:
    HAS_MODBUS = False

logger = logging.getLogger(__name__)


class PLCTag:
    """Represents a PLC tag/variable"""
    def __init__(
        self,
        name: str,
        address: str,
        data_type: str,
        description: str = "",
        unit: str = "",
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ):
        self.name = name
        self.address = address
        self.data_type = data_type
        self.description = description
        self.unit = unit
        self.min_value = min_value
        self.max_value = max_value
        self.value: Any = None
        self.timestamp: Optional[datetime] = None
        self.quality: str = "GOOD"


class PLCService:
    """Service for PLC communication"""

    def __init__(self):
        self.opcua_client: Optional[OPCClient] = None
        self.modbus_client: Optional[AsyncModbusTcpClient] = None
        self.connected = False
        self.tags: Dict[str, PLCTag] = {}
        self._monitoring_task: Optional[asyncio.Task] = None

    async def connect_opcua(self, url: str) -> bool:
        """
        Connect to OPC UA server

        Args:
            url: OPC UA server URL (e.g., "opc.tcp://localhost:4840")
        """
        if not HAS_OPCUA:
            logger.error("asyncua not installed. Install: pip install asyncua")
            return False

        try:
            self.opcua_client = OPCClient(url=url)
            await self.opcua_client.connect()
            self.connected = True
            logger.info(f"Connected to OPC UA server: {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OPC UA: {e}")
            return False

    async def connect_modbus(self, host: str, port: int = 502) -> bool:
        """
        Connect to Modbus TCP server

        Args:
            host: Modbus server IP
            port: Modbus server port (default 502)
        """
        if not HAS_MODBUS:
            logger.error("pymodbus not installed. Install: pip install pymodbus")
            return False

        try:
            self.modbus_client = AsyncModbusTcpClient(host=host, port=port)
            await self.modbus_client.connect()
            self.connected = True
            logger.info(f"Connected to Modbus server: {host}:{port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Modbus: {e}")
            return False

    async def disconnect(self):
        """Disconnect from PLC"""
        if self._monitoring_task:
            self._monitoring_task.cancel()

        if self.opcua_client:
            await self.opcua_client.disconnect()

        if self.modbus_client:
            self.modbus_client.close()

        self.connected = False
        logger.info("Disconnected from PLC")

    def register_tag(self, tag: PLCTag):
        """Register a tag for monitoring"""
        self.tags[tag.name] = tag
        logger.info(f"Registered tag: {tag.name} ({tag.address})")

    async def read_tag_opcua(self, tag_name: str) -> Optional[Any]:
        """Read tag value from OPC UA"""
        if not self.opcua_client or not self.connected:
            return None

        tag = self.tags.get(tag_name)
        if not tag:
            return None

        try:
            # Get node by address
            node = self.opcua_client.get_node(tag.address)
            value = await node.read_value()

            # Update tag
            tag.value = value
            tag.timestamp = datetime.utcnow()
            tag.quality = "GOOD"

            return value
        except Exception as e:
            logger.error(f"Error reading OPC UA tag {tag_name}: {e}")
            tag.quality = "BAD"
            return None

    async def read_tag_modbus(self, tag_name: str) -> Optional[Any]:
        """Read tag value from Modbus"""
        if not self.modbus_client or not self.connected:
            return None

        tag = self.tags.get(tag_name)
        if not tag:
            return None

        try:
            # Parse address (format: "holding:1000" or "input:2000")
            addr_type, address = tag.address.split(":")
            address = int(address)

            if addr_type == "holding":
                result = await self.modbus_client.read_holding_registers(address, 1)
            elif addr_type == "input":
                result = await self.modbus_client.read_input_registers(address, 1)
            elif addr_type == "coil":
                result = await self.modbus_client.read_coils(address, 1)
            elif addr_type == "discrete":
                result = await self.modbus_client.read_discrete_inputs(address, 1)
            else:
                return None

            if result.isError():
                tag.quality = "BAD"
                return None

            value = result.registers[0] if hasattr(result, 'registers') else result.bits[0]

            # Update tag
            tag.value = value
            tag.timestamp = datetime.utcnow()
            tag.quality = "GOOD"

            return value
        except Exception as e:
            logger.error(f"Error reading Modbus tag {tag_name}: {e}")
            tag.quality = "BAD"
            return None

    async def write_tag_opcua(self, tag_name: str, value: Any) -> bool:
        """Write value to OPC UA tag"""
        if not self.opcua_client or not self.connected:
            return False

        tag = self.tags.get(tag_name)
        if not tag:
            return False

        try:
            node = self.opcua_client.get_node(tag.address)

            # Convert to appropriate UA type
            if tag.data_type == "Int32":
                ua_value = ua.Variant(int(value), ua.VariantType.Int32)
            elif tag.data_type == "Float":
                ua_value = ua.Variant(float(value), ua.VariantType.Float)
            elif tag.data_type == "Boolean":
                ua_value = ua.Variant(bool(value), ua.VariantType.Boolean)
            else:
                ua_value = ua.Variant(value, ua.VariantType.String)

            await node.write_value(ua_value)
            logger.info(f"Wrote value {value} to tag {tag_name}")
            return True
        except Exception as e:
            logger.error(f"Error writing OPC UA tag {tag_name}: {e}")
            return False

    async def write_tag_modbus(self, tag_name: str, value: Any) -> bool:
        """Write value to Modbus tag"""
        if not self.modbus_client or not self.connected:
            return False

        tag = self.tags.get(tag_name)
        if not tag:
            return False

        try:
            addr_type, address = tag.address.split(":")
            address = int(address)

            if addr_type == "holding":
                result = await self.modbus_client.write_register(address, int(value))
            elif addr_type == "coil":
                result = await self.modbus_client.write_coil(address, bool(value))
            else:
                return False

            if result.isError():
                return False

            logger.info(f"Wrote value {value} to tag {tag_name}")
            return True
        except Exception as e:
            logger.error(f"Error writing Modbus tag {tag_name}: {e}")
            return False

    async def read_all_tags(self) -> Dict[str, Any]:
        """Read all registered tags"""
        results = {}

        for tag_name, tag in self.tags.items():
            if self.opcua_client:
                value = await self.read_tag_opcua(tag_name)
            elif self.modbus_client:
                value = await self.read_tag_modbus(tag_name)
            else:
                value = None

            results[tag_name] = {
                "name": tag_name,
                "value": value,
                "timestamp": tag.timestamp.isoformat() if tag.timestamp else None,
                "quality": tag.quality,
                "unit": tag.unit,
                "description": tag.description,
            }

        return results

    async def start_monitoring(self, interval: float = 1.0, callback=None):
        """
        Start continuous monitoring of all tags

        Args:
            interval: Polling interval in seconds
            callback: Async function to call with tag updates
        """
        async def monitor_loop():
            while True:
                try:
                    results = await self.read_all_tags()

                    if callback:
                        await callback(results)

                    await asyncio.sleep(interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(interval)

        self._monitoring_task = asyncio.create_task(monitor_loop())
        logger.info(f"Started tag monitoring (interval: {interval}s)")

    async def stop_monitoring(self):
        """Stop continuous monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped tag monitoring")

    async def browse_opcua(
        self,
        node_id: str = "i=85",  # Objects folder
        max_depth: int = 10,
        include_properties: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Browse OPC UA server tree and discover all variables/tags

        Args:
            node_id: Starting node ID (default: Objects folder)
            max_depth: Maximum depth to browse (prevents infinite recursion)
            include_properties: Include property nodes (usually not needed)

        Returns:
            List of discovered tags with metadata
        """
        if not self.opcua_client or not self.connected:
            logger.error("OPC UA client not connected")
            return []

        discovered_tags = []

        async def browse_node(node, current_path: str = "", depth: int = 0):
            """Recursively browse nodes"""
            if depth > max_depth:
                return

            try:
                # Get node class (Object, Variable, Method, etc)
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

                        # Get current value to infer more info
                        try:
                            value = await node.read_value()
                            value_type = type(value).__name__
                        except:
                            value = None
                            value_type = "Unknown"

                        # Get access level
                        try:
                            access_level = await node.read_attribute(ua.AttributeIds.AccessLevel)
                            writable = bool(access_level.Value.Value & 0x02)  # Check write bit
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
                        logger.debug(f"Discovered tag: {path} ({data_type})")

                    except Exception as e:
                        logger.warning(f"Error reading variable {path}: {e}")

                # Browse children
                try:
                    children = await node.get_children()
                    for child in children:
                        # Skip properties unless explicitly requested
                        if not include_properties:
                            child_browse_name = await child.read_browse_name()
                            # Properties typically have namespace 0 and are in Properties folder
                            if child_browse_name.NamespaceIndex == 0:
                                continue

                        await browse_node(child, path, depth + 1)
                except Exception as e:
                    logger.debug(f"No children for node {path}: {e}")

            except Exception as e:
                logger.warning(f"Error browsing node {current_path}: {e}")

        # Start browsing from root node
        try:
            root_node = self.opcua_client.get_node(node_id)
            logger.info(f"Starting OPC UA browse from node: {node_id}")
            await browse_node(root_node)
            logger.info(f"Browse complete. Found {len(discovered_tags)} tags")
        except Exception as e:
            logger.error(f"Error starting browse: {e}")

        return discovered_tags

    async def _get_data_type_name(self, data_type_node) -> str:
        """Convert OPC UA data type node to readable name"""
        try:
            # Map common OPC UA data types
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
                "i=15": "Guid",
                "i=17": "ByteString",
            }

            node_id_str = data_type_node.to_string()
            return type_map.get(node_id_str, node_id_str)
        except:
            return "Unknown"

    async def test_connection(self, url: str) -> Dict[str, Any]:
        """
        Test connection to OPC UA server and get basic info

        Args:
            url: OPC UA server URL

        Returns:
            Connection test results
        """
        result = {
            "success": False,
            "url": url,
            "server_info": None,
            "error": None
        }

        temp_client = None
        try:
            temp_client = OPCClient(url=url, timeout=5)
            await temp_client.connect()

            # Get server info
            server_info = {
                "application_uri": str(temp_client.application_uri),
                "product_uri": str(temp_client.product_uri),
                "server_name": str(temp_client.name),
            }

            # Try to get namespace array
            try:
                ns_node = temp_client.get_node("i=2255")  # NamespaceArray node
                namespaces = await ns_node.read_value()
                server_info["namespaces"] = namespaces
            except:
                pass

            result["success"] = True
            result["server_info"] = server_info
            logger.info(f"Successfully tested connection to {url}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Connection test failed for {url}: {e}")
        finally:
            if temp_client:
                try:
                    await temp_client.disconnect()
                except:
                    pass

        return result


# Demo PLC simulator for testing
class DemoPLCService(PLCService):
    """Demo PLC service with simulated data"""

    def __init__(self):
        super().__init__()
        self.connected = True
        self._setup_demo_tags()

    def _setup_demo_tags(self):
        """Setup demo tags for SmartPort"""
        import random

        # Container crane tags
        self.register_tag(PLCTag(
            name="crane_1_position",
            address="ns=2;i=1000",
            data_type="Float",
            description="Crane 1 trolley position",
            unit="meters",
            min_value=0,
            max_value=50
        ))

        self.register_tag(PLCTag(
            name="crane_1_load",
            address="ns=2;i=1001",
            data_type="Float",
            description="Crane 1 load weight",
            unit="tonnes",
            min_value=0,
            max_value=70
        ))

        self.register_tag(PLCTag(
            name="crane_1_speed",
            address="ns=2;i=1002",
            data_type="Float",
            description="Crane 1 speed",
            unit="m/min",
            min_value=0,
            max_value=120
        ))

        # Berth sensors
        self.register_tag(PLCTag(
            name="berth_t1a_occupied",
            address="ns=2;i=2000",
            data_type="Boolean",
            description="Berth T1-A occupation sensor"
        ))

        self.register_tag(PLCTag(
            name="berth_t1a_containers",
            address="ns=2;i=2001",
            data_type="Int32",
            description="Containers on T1-A",
            unit="TEU"
        ))

        # Port metrics
        self.register_tag(PLCTag(
            name="port_throughput",
            address="ns=2;i=3000",
            data_type="Int32",
            description="Port hourly throughput",
            unit="containers/hour"
        ))

    async def read_tag_opcua(self, tag_name: str) -> Optional[Any]:
        """Simulate reading tag"""
        import random

        tag = self.tags.get(tag_name)
        if not tag:
            return None

        # Generate realistic demo values
        if tag.data_type == "Float":
            if tag.min_value is not None and tag.max_value is not None:
                value = random.uniform(tag.min_value, tag.max_value)
            else:
                value = random.uniform(0, 100)
        elif tag.data_type == "Int32":
            if tag.min_value is not None and tag.max_value is not None:
                value = random.randint(int(tag.min_value), int(tag.max_value))
            else:
                value = random.randint(0, 1000)
        elif tag.data_type == "Boolean":
            value = random.choice([True, False])
        else:
            value = "OK"

        tag.value = value
        tag.timestamp = datetime.utcnow()
        tag.quality = "GOOD"

        return value


# Global PLC service instance
plc_service = DemoPLCService()  # Use DemoPLCService for demo, replace with PLCService for real PLC
