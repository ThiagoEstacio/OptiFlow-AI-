"""
Modbus TCP Gateway Implementation

Provides connectivity to Modbus TCP devices using the pymodbus library.
Modbus is widely used in grain terminals and industrial automation.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import struct

try:
    from pymodbus.client import AsyncModbusTcpClient
    from pymodbus.exceptions import ModbusException
    PYMODBUS_AVAILABLE = True
except ImportError:
    PYMODBUS_AVAILABLE = False
    AsyncModbusTcpClient = None
    ModbusException = Exception

from .base_gateway import BaseGateway, DataPoint, GatewayStatus

logger = logging.getLogger(__name__)


class ModbusGateway(BaseGateway):
    """
    Modbus TCP Gateway implementation.

    Connects to Modbus TCP devices and reads holding registers or input registers.

    Configuration example:
    {
        "host": "192.168.1.101",
        "port": 502,
        "unit_id": 1,
        "timeout": 3,
        "tags": [
            {
                "tag_name": "weighbridge_gross_weight",
                "address_config": {
                    "register_type": "holding",  # or "input"
                    "address": 0,
                    "count": 2,
                    "data_type": "float32",
                    "byte_order": "big",
                    "word_order": "big"
                },
                "data_type": "float",
                "unit": "kg"
            }
        ]
    }

    Supported data types:
    - uint16: Single register, unsigned 16-bit integer
    - int16: Single register, signed 16-bit integer
    - uint32: Two registers, unsigned 32-bit integer
    - int32: Two registers, signed 32-bit integer
    - float32: Two registers, 32-bit float
    - float64: Four registers, 64-bit double
    """

    REGISTER_COUNTS = {
        'uint16': 1,
        'int16': 1,
        'uint32': 2,
        'int32': 2,
        'float32': 2,
        'float64': 4,
    }

    def __init__(self, name: str, config: Dict[str, Any], max_buffer_size: int = 10000):
        if not PYMODBUS_AVAILABLE:
            raise ImportError(
                "pymodbus library is not installed. "
                "Install it with: pip install pymodbus"
            )

        super().__init__(name, config, max_buffer_size)

        conn_config = config.get('connection_config', {})
        self.host = conn_config.get('host')
        if not self.host:
            raise ValueError("Modbus host is required in connection_config")

        self.port = conn_config.get('port', 502)
        self.unit_id = conn_config.get('unit_id', 1)
        self.timeout = conn_config.get('timeout', 3)

        self.client: Optional[AsyncModbusTcpClient] = None

    async def connect(self) -> bool:
        """
        Connect to Modbus TCP device.

        Returns:
            bool: True if connection successful
        """
        try:
            logger.info(f"{self.name}: Connecting to Modbus device at {self.host}:{self.port}")

            # Create client
            self.client = AsyncModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=self.timeout
            )

            # Connect
            await self.client.connect()

            if self.client.connected:
                logger.info(f"{self.name}: Connected successfully")
                return True
            else:
                logger.error(f"{self.name}: Connection failed")
                return False

        except Exception as e:
            logger.error(f"{self.name}: Connection error: {e}")
            self.client = None
            raise

    async def disconnect(self) -> None:
        """Disconnect from Modbus device."""
        if self.client:
            try:
                self.client.close()
                logger.info(f"{self.name}: Disconnected")
            except Exception as e:
                logger.error(f"{self.name}: Error during disconnect: {e}")
            finally:
                self.client = None
                self.status = GatewayStatus.DISCONNECTED

    def _parse_register_data(
        self,
        registers: List[int],
        data_type: str,
        byte_order: str = 'big',
        word_order: str = 'big'
    ) -> Optional[float]:
        """
        Parse Modbus register data into a Python value.

        Args:
            registers: List of register values (16-bit each)
            data_type: Data type (uint16, int16, uint32, int32, float32, float64)
            byte_order: Byte order ('big' or 'little')
            word_order: Word order ('big' or 'little')

        Returns:
            Parsed value or None if error
        """
        try:
            if data_type == 'uint16':
                return registers[0]
            elif data_type == 'int16':
                # Convert unsigned to signed
                value = registers[0]
                return value if value < 32768 else value - 65536

            # For multi-register types, convert to bytes
            if word_order == 'little':
                registers = registers[::-1]  # Reverse word order

            # Pack registers into bytes
            if byte_order == 'big':
                byte_data = b''.join(reg.to_bytes(2, byteorder='big') for reg in registers)
            else:
                byte_data = b''.join(reg.to_bytes(2, byteorder='little') for reg in registers)

            # Unpack based on data type
            if data_type == 'uint32':
                return struct.unpack('>I' if byte_order == 'big' else '<I', byte_data)[0]
            elif data_type == 'int32':
                return struct.unpack('>i' if byte_order == 'big' else '<i', byte_data)[0]
            elif data_type == 'float32':
                return struct.unpack('>f' if byte_order == 'big' else '<f', byte_data)[0]
            elif data_type == 'float64':
                return struct.unpack('>d' if byte_order == 'big' else '<d', byte_data)[0]

            logger.error(f"Unknown data type: {data_type}")
            return None

        except Exception as e:
            logger.error(f"Error parsing register data: {e}")
            return None

    async def read_tag(self, tag_config: Dict[str, Any]) -> Optional[DataPoint]:
        """
        Read a single tag from Modbus device.

        Args:
            tag_config: Tag configuration with address_config

        Returns:
            DataPoint if successful, None if error
        """
        if not self.client or not self.client.connected or self.status != GatewayStatus.CONNECTED:
            return None

        try:
            tag_name = tag_config.get('tag_name')
            addr_config = tag_config.get('address_config', {})

            register_type = addr_config.get('register_type', 'holding')
            address = addr_config.get('address', 0)
            data_type = addr_config.get('data_type', 'float32')
            byte_order = addr_config.get('byte_order', 'big')
            word_order = addr_config.get('word_order', 'big')

            # Determine register count based on data type
            count = self.REGISTER_COUNTS.get(data_type, 2)

            # Read registers
            if register_type == 'holding':
                response = await self.client.read_holding_registers(
                    address=address,
                    count=count,
                    slave=self.unit_id
                )
            elif register_type == 'input':
                response = await self.client.read_input_registers(
                    address=address,
                    count=count,
                    slave=self.unit_id
                )
            else:
                logger.error(f"{self.name}: Unknown register type: {register_type}")
                return None

            # Check for errors
            if response.isError():
                logger.error(f"{self.name}: Modbus error reading {tag_name}: {response}")
                return None

            # Parse register data
            value = self._parse_register_data(
                response.registers,
                data_type,
                byte_order,
                word_order
            )

            if value is None:
                return None

            # Apply scaling
            scale_factor = tag_config.get('scale_factor', 1.0)
            offset = tag_config.get('offset', 0.0)
            value = (value * scale_factor) + offset

            # Create data point
            data_point = DataPoint(
                tag_name=tag_name,
                value=value,
                quality="good",
                timestamp=datetime.utcnow()
            )

            return data_point

        except Exception as e:
            logger.error(f"{self.name}: Error reading tag {tag_name}: {e}")
            return None

    async def read_multiple_tags(self, tag_configs: List[Dict[str, Any]]) -> List[DataPoint]:
        """
        Read multiple tags from Modbus device.

        Note: Modbus doesn't support true batch reads of non-contiguous addresses,
        so this implementation reads tags individually.

        Args:
            tag_configs: List of tag configurations

        Returns:
            List of DataPoints
        """
        if not self.client or not self.client.connected or self.status != GatewayStatus.CONNECTED:
            return []

        # Filter only enabled tags
        enabled_tags = [tag for tag in tag_configs if tag.get('enabled', True)]

        if not enabled_tags:
            return []

        data_points = []

        # Read tags individually
        for tag_config in enabled_tags:
            try:
                data_point = await self.read_tag(tag_config)
                if data_point:
                    data_points.append(data_point)
            except Exception as e:
                logger.error(f"{self.name}: Failed to read {tag_config.get('tag_name')}: {e}")

        return data_points

    async def write_tag(
        self,
        address: int,
        value: Any,
        data_type: str = 'uint16',
        register_type: str = 'holding'
    ) -> bool:
        """
        Write a value to Modbus device (optional, for future use).

        Args:
            address: Register address
            value: Value to write
            data_type: Data type
            register_type: Register type (only 'holding' supports writes)

        Returns:
            bool: True if write successful
        """
        if not self.client or not self.client.connected:
            return False

        if register_type != 'holding':
            logger.error(f"{self.name}: Only holding registers support writes")
            return False

        try:
            # Convert value to registers based on data type
            if data_type == 'uint16':
                response = await self.client.write_register(
                    address=address,
                    value=int(value),
                    slave=self.unit_id
                )
            else:
                # TODO: Implement multi-register writes for other data types
                logger.error(f"{self.name}: Write not implemented for data type: {data_type}")
                return False

            if response.isError():
                logger.error(f"{self.name}: Write error: {response}")
                return False

            logger.info(f"{self.name}: Successfully wrote {value} to address {address}")
            return True

        except Exception as e:
            logger.error(f"{self.name}: Write exception: {e}")
            return False
