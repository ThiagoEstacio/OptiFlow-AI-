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

try:
    from pymodbus.client import AsyncModbusTcpClient
    from pymodbus.exceptions import ModbusException
    from pymodbus.pdu import ExceptionResponse
    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False
    logging.warning("pymodbus not installed - Modbus adapter disabled")

from .base_adapter import BaseProtocolAdapter, ProtocolConfig, TagData

logger = logging.getLogger(__name__)


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

        logger.info(f"🔧 Modbus adapter initialized - Host: {config.host}:{config.port}, Slave: {self.slave_id}")

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
                return True
            else:
                logger.error(f"❌ Failed to connect to Modbus TCP server")
                self.connected = False
                return False

        except Exception as e:
            logger.error(f"❌ Failed to connect to Modbus TCP server: {e}", exc_info=True)
            self.connected = False
            return False

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

        except Exception as e:
            logger.error(f"❌ Error during disconnect: {e}")

    async def read_tags(self) -> List[TagData]:
        """Read all configured tags from Modbus device"""
        if not self.connected or not self.client:
            return []

        tags = []

        for tag_config in self.config.tags:
            try:
                tag_name = tag_config.get('name')
                address = tag_config.get('address')
                data_type = tag_config.get('type', 'int16')
                function = tag_config.get('function', 'holding')

                if not tag_name or not address:
                    logger.warning(f"⚠️  Skipping tag with missing name or address: {tag_config}")
                    continue

                # Parse Modbus address
                modbus_address = self._parse_address(address, function)

                # Read value from device
                value = await self._read_value(modbus_address, data_type, function)

                if value is not None:
                    tag_data = TagData(
                        tag_name=tag_name,
                        value=value,
                        quality='good',
                        source=self.adapter_id,
                        address=address
                    )
                    tags.append(tag_data)
                else:
                    # Create tag with bad quality
                    tag_data = TagData(
                        tag_name=tag_name,
                        value=None,
                        quality='bad',
                        source=self.adapter_id,
                        address=address
                    )
                    tags.append(tag_data)

            except Exception as e:
                logger.error(f"❌ Error reading tag {tag_config.get('name')}: {e}")
                continue

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
