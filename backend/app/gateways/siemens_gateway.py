"""
Siemens S7 Gateway Implementation

Provides connectivity to Siemens S7 PLCs using the python-snap7 library.
Supports S7-300, S7-400, S7-1200, and S7-1500 series.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import struct

try:
    import snap7
    from snap7.util import get_real, get_int, get_dint, get_bool, get_string
    SNAP7_AVAILABLE = True
except ImportError:
    SNAP7_AVAILABLE = False
    snap7 = None

from .base_gateway import BaseGateway, DataPoint, GatewayStatus

logger = logging.getLogger(__name__)


class SiemensGateway(BaseGateway):
    """
    Siemens S7 PLC Gateway implementation.

    Connects to Siemens S7 PLCs and reads data from DB blocks, inputs, outputs, and merkers.

    Configuration example:
    {
        "host": "192.168.1.102",
        "port": 102,
        "rack": 0,
        "slot": 1,
        "tags": [
            {
                "tag_name": "conveyor_speed",
                "address_config": {
                    "area": "DB",
                    "db_number": 1,
                    "start": 0,
                    "size": 4,
                    "data_type": "real"
                },
                "data_type": "float",
                "unit": "m/s"
            }
        ]
    }

    Supported areas:
    - DB: Data blocks
    - I: Inputs (process image)
    - Q: Outputs (process image)
    - M: Merker (flags)
    - TM: Timers
    - CT: Counters

    Supported data types:
    - bool: Boolean (1 bit)
    - byte: Byte (8 bits)
    - int: Integer (16 bits)
    - dint: Double integer (32 bits)
    - real: Real number (32-bit float)
    - string: String
    """

    AREA_MAP = {
        'I': snap7.types.Areas.PE if SNAP7_AVAILABLE else None,  # Process inputs
        'Q': snap7.types.Areas.PA if SNAP7_AVAILABLE else None,  # Process outputs
        'M': snap7.types.Areas.MK if SNAP7_AVAILABLE else None,  # Merkers
        'DB': snap7.types.Areas.DB if SNAP7_AVAILABLE else None,  # Data blocks
        'TM': snap7.types.Areas.TM if SNAP7_AVAILABLE else None,  # Timers
        'CT': snap7.types.Areas.CT if SNAP7_AVAILABLE else None,  # Counters
    }

    def __init__(self, name: str, config: Dict[str, Any], max_buffer_size: int = 10000):
        if not SNAP7_AVAILABLE:
            raise ImportError(
                "python-snap7 library is not installed. "
                "Install it with: pip install python-snap7\n"
                "Note: Also requires snap7 library (libsnap7.so on Linux)"
            )

        super().__init__(name, config, max_buffer_size)

        conn_config = config.get('connection_config', {})
        self.host = conn_config.get('host')
        if not self.host:
            raise ValueError("Siemens host is required in connection_config")

        self.port = conn_config.get('port', 102)
        self.rack = conn_config.get('rack', 0)
        self.slot = conn_config.get('slot', 1)

        self.client: Optional[snap7.client.Client] = None

    async def connect(self) -> bool:
        """
        Connect to Siemens S7 PLC.

        Returns:
            bool: True if connection successful
        """
        try:
            logger.info(f"{self.name}: Connecting to Siemens PLC at {self.host}:{self.port} (Rack {self.rack}, Slot {self.slot})")

            # Create client (snap7 is synchronous, but we wrap in async)
            self.client = snap7.client.Client()

            # Connect to PLC
            self.client.connect(self.host, self.rack, self.slot, self.port)

            if self.client.get_connected():
                # Get CPU info for verification
                cpu_info = self.client.get_cpu_info()
                logger.info(f"{self.name}: Connected successfully. CPU: {cpu_info.ModuleTypeName.decode()}")
                return True
            else:
                logger.error(f"{self.name}: Connection failed")
                return False

        except Exception as e:
            logger.error(f"{self.name}: Connection error: {e}")
            self.client = None
            raise

    async def disconnect(self) -> None:
        """Disconnect from Siemens PLC."""
        if self.client:
            try:
                self.client.disconnect()
                logger.info(f"{self.name}: Disconnected")
            except Exception as e:
                logger.error(f"{self.name}: Error during disconnect: {e}")
            finally:
                self.client = None
                self.status = GatewayStatus.DISCONNECTED

    def _parse_s7_data(
        self,
        data: bytes,
        data_type: str,
        bit_offset: int = 0,
        string_length: int = 254
    ) -> Optional[Any]:
        """
        Parse S7 data bytes into Python value.

        Args:
            data: Raw bytes from PLC
            data_type: Data type (bool, byte, int, dint, real, string)
            bit_offset: Bit offset for boolean values
            string_length: Maximum string length

        Returns:
            Parsed value or None if error
        """
        try:
            if data_type == 'bool':
                return get_bool(data, 0, bit_offset)
            elif data_type == 'byte':
                return data[0]
            elif data_type == 'int':
                return get_int(data, 0)
            elif data_type == 'dint':
                return get_dint(data, 0)
            elif data_type == 'real':
                return get_real(data, 0)
            elif data_type == 'string':
                return get_string(data, 0, string_length)
            else:
                logger.error(f"Unknown data type: {data_type}")
                return None

        except Exception as e:
            logger.error(f"Error parsing S7 data: {e}")
            return None

    async def read_tag(self, tag_config: Dict[str, Any]) -> Optional[DataPoint]:
        """
        Read a single tag from Siemens PLC.

        Args:
            tag_config: Tag configuration with address_config

        Returns:
            DataPoint if successful, None if error
        """
        if not self.client or not self.client.get_connected() or self.status != GatewayStatus.CONNECTED:
            return None

        try:
            tag_name = tag_config.get('tag_name')
            addr_config = tag_config.get('address_config', {})

            area = addr_config.get('area', 'DB')
            db_number = addr_config.get('db_number', 0)
            start = addr_config.get('start', 0)
            size = addr_config.get('size', 4)
            data_type = addr_config.get('data_type', 'real')
            bit_offset = addr_config.get('bit_offset', 0)

            # Get area code
            area_code = self.AREA_MAP.get(area)
            if area_code is None:
                logger.error(f"{self.name}: Unknown area: {area}")
                return None

            # Read data from PLC
            if area == 'DB':
                data = self.client.db_read(db_number, start, size)
            else:
                data = self.client.read_area(area_code, 0, start, size)

            # Parse data
            value = self._parse_s7_data(data, data_type, bit_offset)

            if value is None:
                return None

            # Apply scaling for numeric values
            if isinstance(value, (int, float)):
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
        Read multiple tags from Siemens PLC.

        Args:
            tag_configs: List of tag configurations

        Returns:
            List of DataPoints
        """
        if not self.client or not self.client.get_connected() or self.status != GatewayStatus.CONNECTED:
            return []

        # Filter only enabled tags
        enabled_tags = [tag for tag in tag_configs if tag.get('enabled', True)]

        if not enabled_tags:
            return []

        data_points = []

        # Read tags individually (S7 doesn't have a multi-read API like OPC-UA)
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
        area: str,
        db_number: int,
        start: int,
        value: Any,
        data_type: str = 'real'
    ) -> bool:
        """
        Write a value to Siemens PLC (optional, for future use).

        Args:
            area: Memory area (DB, M, Q, etc.)
            db_number: DB number (if area is DB)
            start: Start address
            value: Value to write
            data_type: Data type

        Returns:
            bool: True if write successful
        """
        if not self.client or not self.client.get_connected():
            return False

        try:
            # Convert value to bytes based on data type
            if data_type == 'bool':
                data = bytearray(1)
                data[0] = 1 if value else 0
            elif data_type == 'int':
                data = struct.pack('>h', int(value))  # 16-bit signed
            elif data_type == 'dint':
                data = struct.pack('>i', int(value))  # 32-bit signed
            elif data_type == 'real':
                data = struct.pack('>f', float(value))  # 32-bit float
            else:
                logger.error(f"{self.name}: Write not implemented for data type: {data_type}")
                return False

            # Write to PLC
            area_code = self.AREA_MAP.get(area)
            if area_code is None:
                logger.error(f"{self.name}: Unknown area: {area}")
                return False

            if area == 'DB':
                self.client.db_write(db_number, start, data)
            else:
                self.client.write_area(area_code, 0, start, data)

            logger.info(f"{self.name}: Successfully wrote {value} to {area} {start}")
            return True

        except Exception as e:
            logger.error(f"{self.name}: Write exception: {e}")
            return False
