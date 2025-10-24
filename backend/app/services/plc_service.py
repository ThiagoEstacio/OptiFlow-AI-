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
