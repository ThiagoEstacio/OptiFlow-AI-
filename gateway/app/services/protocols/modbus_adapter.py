"""
Modbus TCP Protocol Adapter
============================

Connects to Modbus TCP servers/PLCs and publishes tag data to Kafka.

Features:
- Supports all Modbus function codes (FC01-04)
- Automatic data type conversion (INT16, UINT16, INT32, UINT32, FLOAT32, FLOAT64)
- Efficient batch reading of consecutive registers
- Automatic reconnection on connection loss

Based on pymodbus library.
"""

from typing import List, Dict, Any, Optional
import asyncio
import logging
import struct

from dataclasses import dataclass, field

try:
    from pymodbus.client import AsyncModbusTcpClient
    from pymodbus.exceptions import ModbusException
    from pymodbus.pdu import ExceptionResponse
    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False
    logging.warning("pymodbus not installed - Modbus adapter disabled")

from .base_adapter import BaseProtocolAdapter, ProtocolConfig, TagData

# Import metrics
try:
    from app.services.gateway_metrics import get_gateway_metrics
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class TagReadSpec:
    """Metadata describing how to extract a tag value from a batch read"""

    name: str
    data_type: str
    function: str
    address: str
    raw_address: int
    register_count: int
    offset: int  # Offset in registers (or bits for coils/discrete)
    config: Dict[str, Any]
    tag_id: Optional[str] = None  # Unique tag ID for InfluxDB persistence


@dataclass
class ReadGroup:
    """Represents a contiguous block of registers/bits to read in a single Modbus request"""

    function: str
    start_address: int
    count: int
    tags: List[TagReadSpec] = field(default_factory=list)


class ModbusAdapter(BaseProtocolAdapter):
    """
    Modbus TCP protocol adapter

    Reads registers from Modbus TCP devices and publishes to Kafka.

    Configuration (extra_config):
    - slave_id: Modbus slave/unit ID (default: 1)
    - byte_order: Byte order for multi-register values (default: 'big')
    - word_order: Word order for 32/64-bit values (default: 'big')

    Tag configuration format:
    {
        'name': 'Temperature',
        'address': '40001',     # Modbus address (40001 = holding register 0)
        'type': 'float32',      # int16, uint16, int32, uint32, float32, float64
        'function': 'holding'   # holding, input, coil, discrete
    }

    Address formats supported:
    - 40001-49999: Holding Registers (FC03)
    - 30001-39999: Input Registers (FC04)
    - 10001-19999: Digital Inputs (FC02)
    - 00001-09999: Coils (FC01)
    """

    # Data type sizes (in 16-bit registers)
    TYPE_SIZES = {
        'int16': 1,
        'uint16': 1,
        'int32': 2,
        'uint32': 2,
        'float32': 2,
        'float64': 4,
        'bool': 1
    }

    def __init__(self, config: ProtocolConfig):
        if not MODBUS_AVAILABLE:
            raise ImportError("pymodbus library not available - cannot create Modbus adapter")

        super().__init__(config)

        # Modbus specific state
        self.client: Optional[AsyncModbusTcpClient] = None
        self.slave_id = config.extra_config.get('slave_id', 1)
        self.byte_order = config.extra_config.get('byte_order', 'big')
        self.word_order = config.extra_config.get('word_order', 'big')

        # Batch/concurrency configuration for high tag counts
        self.max_registers_per_batch = int(
            config.extra_config.get(
                'max_registers_per_batch',
                max(10, min(120, config.batch_size or 120))
            )
        )
        self.max_bits_per_batch = int(config.extra_config.get('max_bits_per_batch', 2000))
        self.max_concurrent_reads = int(config.extra_config.get('max_concurrent_reads', 10))

        # Pre-compute optimal read plan for all tags (to avoid 1 request per tag)
        self._read_plan: List[ReadGroup] = self._build_read_plan()

        # Cache for realtime API access (last received values)
        self.last_values: Dict[str, Dict[str, Any]] = {}  # {address: {value, quality, timestamp}}

        logger.info(f"🔧 Modbus adapter initialized - Host: {config.host}:{config.port}, Slave: {self.slave_id}")
        if self._read_plan:
            total_groups = len(self._read_plan)
            total_tags = sum(len(group.tags) for group in self._read_plan)
            logger.info(
                f"📦 Modbus read plan created - {total_tags} tags in {total_groups} batch groups "
                f"(max {self.max_registers_per_batch} registers per group)"
            )
        else:
            logger.warning("⚠️  Modbus read plan empty - falling back to sequential reads (less efficient)")

    async def connect(self) -> bool:
        """Connect to Modbus TCP server"""
        if self.connected:
            logger.warning(f"⚠️  {self.adapter_id} already connected")
            return True

        try:
            logger.info(f"🔌 Connecting to Modbus TCP server: {self.config.host}:{self.config.port}")

            # Create Modbus TCP client
            self.client = AsyncModbusTcpClient(
                host=self.config.host,
                port=self.config.port,
                timeout=self.config.timeout
            )

            # Connect to server
            await self.client.connect()

            if self.client.connected:
                logger.info(f"✅ Connected to Modbus TCP server")
                self.connected = True

                # Update metrics
                if METRICS_AVAILABLE:
                    metrics = get_gateway_metrics()
                    metrics.set_devices_connected("modbus", 1)
                    metrics.set_device_status(self.adapter_id, "modbus", True)
                    metrics.track_connection_attempt(self.adapter_id, "modbus", True)
                    metrics.set_tags_total(self.adapter_id, len(self.config.tags))

                return True
            else:
                logger.error(f"❌ Failed to connect to Modbus TCP server")
                self.connected = False

                # Update metrics on failure
                if METRICS_AVAILABLE:
                    metrics = get_gateway_metrics()
                    metrics.track_connection_attempt(self.adapter_id, "modbus", False)
                    metrics.set_device_status(self.adapter_id, "modbus", False)

                return False

        except Exception as e:
            logger.error(f"❌ Failed to connect to Modbus TCP server: {e}", exc_info=True)
            self.connected = False

            # Update metrics on failure
            if METRICS_AVAILABLE:
                metrics = get_gateway_metrics()
                metrics.track_connection_attempt(self.adapter_id, "modbus", False)
                metrics.set_device_status(self.adapter_id, "modbus", False)

            return False

    def _build_read_plan(self) -> List[ReadGroup]:
        """
        Build an optimized plan grouping tags into contiguous blocks for batch reads.

        This drastically reduces the number of Modbus round-trips, enabling
        10k+ tags to be read under tight scan intervals.
        """
        if not self.config.tags:
            return []

        tags_by_function: Dict[str, List[Dict[str, Any]]] = {
            'holding': [],
            'input': [],
            'coil': [],
            'discrete': []
        }

        for tag_config in self.config.tags:
            function = tag_config.get('function', 'holding').lower()
            if function not in tags_by_function:
                logger.warning(f"⚠️  Unsupported Modbus function '{function}' for tag {tag_config.get('name')}")
                continue

            address = tag_config.get('address')
            if not address:
                logger.warning(f"⚠️  Tag {tag_config.get('name')} missing address")
                continue

            parsed_address = self._parse_address(address, function)
            data_type = tag_config.get('type', 'int16').lower()
            register_count = self.TYPE_SIZES.get(data_type, 1)

            tags_by_function[function].append({
                'config': tag_config,
                'address': parsed_address,
                'register_count': register_count
            })

        plan: List[ReadGroup] = []
        for function, tag_list in tags_by_function.items():
            if not tag_list:
                continue

            tag_list.sort(key=lambda t: t['address'])
            max_span = self.max_registers_per_batch if function in ('holding', 'input') else self.max_bits_per_batch

            current_group: Optional[ReadGroup] = None
            for tag_info in tag_list:
                tag_conf = tag_info['config']
                address = tag_info['address']
                register_count = tag_info['register_count']
                span_unit = register_count if function in ('holding', 'input') else 1

                if current_group is None:
                    current_group = ReadGroup(
                        function=function,
                        start_address=address,
                        count=0,
                        tags=[]
                    )

                # Determine if tag fits in current group
                relative_offset = address - current_group.start_address
                required_span = relative_offset + span_unit

                if required_span > max_span:
                    plan.append(current_group)
                    current_group = ReadGroup(
                        function=function,
                        start_address=address,
                        count=0,
                        tags=[]
                    )
                    relative_offset = 0
                    required_span = span_unit

                spec = TagReadSpec(
                    name=tag_conf.get('name'),
                    data_type=tag_conf.get('type', 'int16'),
                    function=function,
                    address=tag_conf.get('address'),
                    raw_address=address,
                    register_count=register_count,
                    offset=relative_offset,
                    config=tag_conf,
                    tag_id=tag_conf.get('tag_id')  # Include tag_id for InfluxDB persistence
                )
                current_group.tags.append(spec)
                current_group.count = max(current_group.count, required_span)

            if current_group and current_group.tags:
                plan.append(current_group)

        return plan

    async def disconnect(self):
        """Disconnect from Modbus TCP server"""
        if not self.connected:
            return

        try:
            logger.info(f"🔌 Disconnecting from {self.config.host}:{self.config.port}...")

            if self.client:
                self.client.close()
                logger.info("✅ Client disconnected")

            self.client = None
            self.connected = False

            # Update metrics
            if METRICS_AVAILABLE:
                metrics = get_gateway_metrics()
                metrics.set_devices_connected("modbus", 0)
                metrics.set_device_status(self.adapter_id, "modbus", False)

        except Exception as e:
            logger.error(f"❌ Error during disconnect: {e}")

    async def read_tags(self) -> List[TagData]:
        """Read all configured tags from Modbus device using optimized batch plan"""
        if not self.connected or not self.client:
            return []

        # Fallback to sequential reads if no plan could be built
        if not self._read_plan:
            return await self._read_tags_sequential()

        results: List[TagData] = []
        semaphore = asyncio.Semaphore(self.max_concurrent_reads)

        async def read_group(group: ReadGroup):
            async with semaphore:
                return await self._read_group(group)

        tasks = [read_group(group) for group in self._read_plan]
        group_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in group_results:
            if isinstance(result, Exception):
                logger.error(f"❌ Error reading Modbus group: {result}")
                continue
            results.extend(result)

        return results

    async def _read_tags_sequential(self) -> List[TagData]:
        """Fallback for environments where batch plan isn't available"""
        tags: List[TagData] = []

        for tag_config in self.config.tags:
            try:
                tag_name = tag_config.get('name')
                tag_id = tag_config.get('tag_id')  # Get tag_id for InfluxDB persistence
                address = tag_config.get('address')
                data_type = tag_config.get('type', 'int16')
                function = tag_config.get('function', 'holding')

                if not tag_name or not address:
                    logger.warning(f"⚠️  Skipping tag with missing name or address: {tag_config}")
                    continue

                modbus_address = self._parse_address(address, function)
                value = await self._read_value(modbus_address, data_type, function)
                quality = 'good' if value is not None else 'bad'

                tags.append(TagData(
                    tag_name=tag_name,
                    value=value,
                    quality=quality,
                    source=self.adapter_id,
                    address=address,
                    tag_id=tag_id  # Include tag_id for InfluxDB persistence
                ))

            except Exception as e:
                logger.error(f"❌ Error reading tag {tag_config.get('name')}: {e}")
                tags.append(TagData(
                    tag_name=tag_config.get('name', 'unknown'),
                    value=None,
                    quality='bad',
                    source=self.adapter_id,
                    address=tag_config.get('address'),
                    tag_id=tag_config.get('tag_id')  # Include tag_id even for errors
                ))

        return tags

    def _parse_address(self, address: str, function: str) -> int:
        """
        Parse Modbus address from string

        Supports both numeric addresses and Modbus addressing conventions:
        - 40001-49999: Holding Registers (subtract 40001 to get 0-based)
        - 30001-39999: Input Registers (subtract 30001)
        - 10001-19999: Discrete Inputs (subtract 10001)
        - 00001-09999: Coils (subtract 1)
        """
        try:
            addr = int(address)

            # Convert from Modbus addressing to 0-based
            if 40000 <= addr <= 49999:
                return addr - 40001
            elif 30000 <= addr <= 39999:
                return addr - 30001
            elif 10000 <= addr <= 19999:
                return addr - 10001
            elif 1 <= addr <= 9999:
                return addr - 1
            else:
                # Already 0-based
                return addr

        except ValueError:
            logger.error(f"Invalid Modbus address: {address}")
            return 0

    async def _read_value(self, address: int, data_type: str, function: str) -> Optional[Any]:
        """Read value from Modbus device"""
        try:
            # Determine register count needed
            count = self.TYPE_SIZES.get(data_type, 1)

            # Read registers based on function type
            if function == 'holding':
                response = await self.client.read_holding_registers(
                    address=address,
                    count=count,
                    slave=self.slave_id
                )
            elif function == 'input':
                response = await self.client.read_input_registers(
                    address=address,
                    count=count,
                    slave=self.slave_id
                )
            elif function == 'coil':
                response = await self.client.read_coils(
                    address=address,
                    count=1,
                    slave=self.slave_id
                )
                if not response.isError():
                    return bool(response.bits[0])
                else:
                    return None
            elif function == 'discrete':
                response = await self.client.read_discrete_inputs(
                    address=address,
                    count=1,
                    slave=self.slave_id
                )
                if not response.isError():
                    return bool(response.bits[0])
                else:
                    return None
            else:
                logger.error(f"Unknown function type: {function}")
                return None

            # Check for errors
            if response.isError():
                logger.warning(f"Modbus error reading address {address}: {response}")
                return None

            # Convert registers to value
            if function in ['holding', 'input']:
                return self._convert_registers(response.registers, data_type)
            else:
                return None

        except Exception as e:
            logger.error(f"Error reading Modbus value at {address}: {e}")
            return None

    def _convert_registers(self, registers: List[int], data_type: str) -> Optional[Any]:
        """Convert Modbus registers to Python value"""
        try:
            if data_type == 'int16':
                # Single register, signed
                value = registers[0]
                if value >= 32768:
                    value -= 65536
                return value

            elif data_type == 'uint16':
                # Single register, unsigned
                return registers[0]

            elif data_type == 'int32':
                # Two registers, signed
                if self.word_order == 'big':
                    raw = (registers[0] << 16) | registers[1]
                else:
                    raw = (registers[1] << 16) | registers[0]

                if raw >= 2147483648:
                    raw -= 4294967296
                return raw

            elif data_type == 'uint32':
                # Two registers, unsigned
                if self.word_order == 'big':
                    return (registers[0] << 16) | registers[1]
                else:
                    return (registers[1] << 16) | registers[0]

            elif data_type == 'float32':
                # Two registers, IEEE 754 float
                if self.word_order == 'big':
                    raw = (registers[0] << 16) | registers[1]
                else:
                    raw = (registers[1] << 16) | registers[0]

                # Convert to bytes then to float
                byte_order = '>' if self.byte_order == 'big' else '<'
                bytes_val = raw.to_bytes(4, byteorder='big')
                return struct.unpack(f'{byte_order}f', bytes_val)[0]

            elif data_type == 'float64':
                # Four registers, IEEE 754 double
                if self.word_order == 'big':
                    raw = (registers[0] << 48) | (registers[1] << 32) | (registers[2] << 16) | registers[3]
                else:
                    raw = (registers[3] << 48) | (registers[2] << 32) | (registers[1] << 16) | registers[0]

                byte_order = '>' if self.byte_order == 'big' else '<'
                bytes_val = raw.to_bytes(8, byteorder='big')
                return struct.unpack(f'{byte_order}d', bytes_val)[0]

            else:
                logger.error(f"Unknown data type: {data_type}")
                return None

        except Exception as e:
            logger.error(f"Error converting registers to {data_type}: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if connection is still alive"""
        if not self.connected or not self.client:
            return False

        try:
            # Try to read a single register as health check
            response = await self.client.read_holding_registers(
                address=0,
                count=1,
                slave=self.slave_id
            )
            return not response.isError()
        except Exception as e:
            logger.warning(f"⚠️  Health check failed: {e}")
            return False

    async def read_all_discovered_tags(self) -> List[Dict[str, Any]]:
        """
        Read current values for ALL configured tags directly from Modbus device

        This reads values directly and updates the last_values cache.
        Used by the Gateway UI to show real-time values for all tags.

        Returns:
            List of dicts with tag info and current values
        """
        from datetime import datetime

        if not self.connected or not self.client:
            logger.warning("Cannot read tags - not connected to Modbus server")
            return []

        results = []

        # Use tags from config
        tags_to_read = self.config.tags if hasattr(self.config, 'tags') else []

        if not tags_to_read:
            logger.warning("No tags configured to read")
            return []

        logger.info(f"📖 Reading {len(tags_to_read)} tags directly from Modbus device...")

        # Read all tags using the optimized batch plan
        tag_data_list = await self.read_tags()

        # Build results and update cache
        now = datetime.now().isoformat()

        for tag_data in tag_data_list:
            # Find original tag config for additional info
            tag_config = next(
                (t for t in tags_to_read if t.get('name') == tag_data.tag_name),
                {}
            )

            address = tag_data.address or tag_config.get('address', '')
            quality = tag_data.quality.capitalize() if tag_data.quality else 'Bad'

            # Update last_values cache
            self.last_values[address] = {
                'value': tag_data.value,
                'quality': quality,
                'timestamp': now
            }

            results.append({
                "name": tag_data.tag_name,
                "address": address,
                "current_value": tag_data.value,
                "quality": quality,
                "data_type": tag_config.get('type', tag_config.get('data_type', 'int16')),
                "unit": tag_config.get('unit'),
                "last_update": now,
                "connected": tag_data.value is not None
            })

        good_count = len([r for r in results if r['connected']])
        logger.info(f"✅ Read {good_count}/{len(results)} tags successfully from Modbus")
        return results

    async def _read_group(self, group: ReadGroup) -> List[TagData]:
        """Read a single batch group and return TagData entries"""
        if group.function in ('holding', 'input'):
            registers = await self._read_register_block(group.function, group.start_address, group.count)
            return self._build_tag_data_from_registers(group, registers)
        else:
            bits = await self._read_bit_block(group.function, group.start_address, group.count)
            return self._build_tag_data_from_bits(group, bits)

    async def _read_register_block(self, function: str, start: int, count: int) -> Optional[List[int]]:
        """Read a contiguous block of registers"""
        try:
            if function == 'holding':
                response = await self.client.read_holding_registers(
                    address=start,
                    count=count,
                    slave=self.slave_id
                )
            else:
                response = await self.client.read_input_registers(
                    address=start,
                    count=count,
                    slave=self.slave_id
                )

            if response.isError():
                logger.warning(f"⚠️  Modbus error reading block {function}@{start}+{count}: {response}")
                return None

            return response.registers

        except Exception as e:
            logger.error(f"❌ Error reading register block {function}@{start}+{count}: {e}")
            return None

    async def _read_bit_block(self, function: str, start: int, count: int) -> Optional[List[bool]]:
        """Read a contiguous block of coils/discrete inputs"""
        try:
            if function == 'coil':
                response = await self.client.read_coils(
                    address=start,
                    count=count,
                    slave=self.slave_id
                )
            else:
                response = await self.client.read_discrete_inputs(
                    address=start,
                    count=count,
                    slave=self.slave_id
                )

            if response.isError():
                logger.warning(f"⚠️  Modbus error reading bit block {function}@{start}+{count}: {response}")
                return None

            return list(response.bits)

        except Exception as e:
            logger.error(f"❌ Error reading bit block {function}@{start}+{count}: {e}")
            return None

    def _build_tag_data_from_registers(
        self,
        group: ReadGroup,
        registers: Optional[List[int]]
    ) -> List[TagData]:
        """Convert register block into TagData entries and update last_values cache"""
        from datetime import datetime
        results: List[TagData] = []
        now = datetime.now().isoformat()

        for spec in group.tags:
            value = None
            quality = 'bad'

            if registers is not None:
                slice_start = spec.offset
                slice_end = slice_start + spec.register_count
                registers_slice = registers[slice_start:slice_end]

                if len(registers_slice) == spec.register_count:
                    value = self._convert_registers(registers_slice, spec.data_type)
                    quality = 'good' if value is not None else 'bad'

            # Update last_values cache for realtime API access (same as OPC-UA)
            self.last_values[spec.address] = {
                'value': value,
                'quality': quality.capitalize(),
                'timestamp': now
            }

            results.append(TagData(
                tag_name=spec.name,
                value=value,
                quality=quality,
                source=self.adapter_id,
                address=spec.address,
                tag_id=spec.tag_id  # Include tag_id for InfluxDB persistence
            ))

            # Update metrics
            if METRICS_AVAILABLE:
                try:
                    metrics = get_gateway_metrics()
                    metrics.track_tag_read(self.adapter_id, "modbus", quality, 0.001)
                    metrics.track_data_collected(self.adapter_id, 1)
                except Exception:
                    pass  # Don't let metrics fail the data flow

        return results

    def _build_tag_data_from_bits(
        self,
        group: ReadGroup,
        bits: Optional[List[bool]]
    ) -> List[TagData]:
        """Convert coil/discrete block into TagData entries and update last_values cache"""
        from datetime import datetime
        results: List[TagData] = []
        now = datetime.now().isoformat()

        for spec in group.tags:
            value = None
            quality = 'bad'

            if bits is not None:
                bit_index = spec.offset
                if bit_index < len(bits):
                    value = bool(bits[bit_index])
                    quality = 'good'

            # Update last_values cache for realtime API access (same as OPC-UA)
            self.last_values[spec.address] = {
                'value': value,
                'quality': quality.capitalize(),
                'timestamp': now
            }

            results.append(TagData(
                tag_name=spec.name,
                value=value,
                quality=quality,
                source=self.adapter_id,
                address=spec.address,
                tag_id=spec.tag_id  # Include tag_id for InfluxDB persistence
            ))

            # Update metrics
            if METRICS_AVAILABLE:
                try:
                    metrics = get_gateway_metrics()
                    metrics.track_tag_read(self.adapter_id, "modbus", quality, 0.001)
                    metrics.track_data_collected(self.adapter_id, 1)
                except Exception:
                    pass  # Don't let metrics fail the data flow

        return results


def create_modbus_adapter(
    adapter_id: str,
    host: str,
    port: int = 502,
    tags: List[Dict[str, str]] = None,
    scan_rate_ms: int = 1000,
    slave_id: int = 1,
    **kwargs
) -> ModbusAdapter:
    """
    Convenience function to create Modbus TCP adapter

    Args:
        adapter_id: Unique adapter identifier
        host: Modbus TCP server host
        port: Modbus TCP server port (default: 502)
        tags: List of tags to monitor (see ModbusAdapter docstring for format)
        scan_rate_ms: How often to read tags (default: 1000ms)
        slave_id: Modbus slave/unit ID (default: 1)
        **kwargs: Additional configuration options

    Returns:
        Configured Modbus adapter instance
    """
    config = ProtocolConfig(
        adapter_id=adapter_id,
        protocol_type='modbus',
        host=host,
        port=port,
        scan_rate_ms=scan_rate_ms,
        tags=tags or [],
        extra_config={
            'slave_id': slave_id,
            'byte_order': kwargs.get('byte_order', 'big'),
            'word_order': kwargs.get('word_order', 'big'),
            **kwargs
        }
    )

    return ModbusAdapter(config)
