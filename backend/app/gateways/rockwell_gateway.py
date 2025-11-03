"""
Rockwell EtherNet/IP Gateway Implementation

Provides connectivity to Rockwell/Allen-Bradley PLCs using the pycomm3 library.
Supports ControlLogix, CompactLogix, and Micro800 series.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

try:
    from pycomm3 import LogixDriver
    PYCOMM3_AVAILABLE = True
except ImportError:
    PYCOMM3_AVAILABLE = False
    LogixDriver = None

from .base_gateway import BaseGateway, DataPoint, GatewayStatus

logger = logging.getLogger(__name__)


class RockwellGateway(BaseGateway):
    """
    Rockwell/Allen-Bradley EtherNet/IP Gateway implementation.

    Connects to Rockwell PLCs and reads tags using EtherNet/IP protocol.

    Configuration example:
    {
        "host": "192.168.1.103",
        "port": 44818,
        "slot": 0,
        "tags": [
            {
                "tag_name": "motor_speed",
                "address_config": {
                    "tag_path": "Program:MainProgram.MotorSpeed"
                },
                "data_type": "float",
                "unit": "RPM"
            }
        ]
    }

    Supported tag types:
    - DINT: 32-bit integer
    - INT: 16-bit integer
    - REAL: 32-bit float
    - BOOL: Boolean
    - STRING: String
    - Arrays and structures (using bracket notation)
    """

    def __init__(self, name: str, config: Dict[str, Any], max_buffer_size: int = 10000):
        if not PYCOMM3_AVAILABLE:
            raise ImportError(
                "pycomm3 library is not installed. "
                "Install it with: pip install pycomm3"
            )

        super().__init__(name, config, max_buffer_size)

        conn_config = config.get('connection_config', {})
        self.host = conn_config.get('host')
        if not self.host:
            raise ValueError("Rockwell host is required in connection_config")

        self.port = conn_config.get('port', 44818)
        self.slot = conn_config.get('slot', 0)
        self.micro800 = conn_config.get('micro800', False)  # Micro800 series flag

        self.client: Optional[LogixDriver] = None

    async def connect(self) -> bool:
        """
        Connect to Rockwell PLC.

        Returns:
            bool: True if connection successful
        """
        try:
            logger.info(f"{self.name}: Connecting to Rockwell PLC at {self.host}:{self.port}")

            # Create driver (pycomm3 is synchronous, but we wrap in async)
            self.client = LogixDriver(
                path=f"{self.host}:{self.port}/{self.slot}",
                init_tags=False,  # Don't read all tags on connect
                micro800=self.micro800
            )

            # Open connection
            self.client.open()

            if self.client.connected:
                # Get controller info
                controller_name = self.client.info.get('name', 'Unknown')
                vendor = self.client.info.get('vendor', 'Unknown')
                product_name = self.client.info.get('product_name', 'Unknown')

                logger.info(
                    f"{self.name}: Connected successfully. "
                    f"Controller: {controller_name}, "
                    f"Vendor: {vendor}, "
                    f"Product: {product_name}"
                )
                return True
            else:
                logger.error(f"{self.name}: Connection failed")
                return False

        except Exception as e:
            logger.error(f"{self.name}: Connection error: {e}")
            self.client = None
            raise

    async def disconnect(self) -> None:
        """Disconnect from Rockwell PLC."""
        if self.client:
            try:
                self.client.close()
                logger.info(f"{self.name}: Disconnected")
            except Exception as e:
                logger.error(f"{self.name}: Error during disconnect: {e}")
            finally:
                self.client = None
                self.status = GatewayStatus.DISCONNECTED

    async def read_tag(self, tag_config: Dict[str, Any]) -> Optional[DataPoint]:
        """
        Read a single tag from Rockwell PLC.

        Args:
            tag_config: Tag configuration with address_config containing tag_path

        Returns:
            DataPoint if successful, None if error
        """
        if not self.client or not self.client.connected or self.status != GatewayStatus.CONNECTED:
            return None

        try:
            tag_name = tag_config.get('tag_name')
            tag_path = tag_config.get('address_config', {}).get('tag_path')

            if not tag_path:
                logger.error(f"{self.name}: No tag_path in config for {tag_name}")
                return None

            # Read tag value
            result = self.client.read(tag_path)

            if result.error:
                logger.error(f"{self.name}: Error reading {tag_name}: {result.error}")
                return None

            value = result.value

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
        Read multiple tags from Rockwell PLC.

        Uses batch reading for better performance.

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

        try:
            # Build list of tag paths
            tag_paths = []
            tag_map = {}  # Map tag_path to tag_config

            for tag_config in enabled_tags:
                tag_path = tag_config.get('address_config', {}).get('tag_path')
                if tag_path:
                    tag_paths.append(tag_path)
                    tag_map[tag_path] = tag_config

            if not tag_paths:
                return []

            # Batch read all tags
            results = self.client.read(*tag_paths)

            # Process results
            for result in results:
                if result.error:
                    logger.error(f"{self.name}: Error reading {result.tag}: {result.error}")
                    continue

                tag_config = tag_map.get(result.tag)
                if not tag_config:
                    continue

                tag_name = tag_config.get('tag_name')
                value = result.value

                # Apply scaling
                if isinstance(value, (int, float)):
                    scale_factor = tag_config.get('scale_factor', 1.0)
                    offset = tag_config.get('offset', 0.0)
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

    async def write_tag(self, tag_path: str, value: Any) -> bool:
        """
        Write a value to Rockwell PLC (optional, for future use).

        Args:
            tag_path: Tag path (e.g., "Program:MainProgram.SetPoint")
            value: Value to write

        Returns:
            bool: True if write successful
        """
        if not self.client or not self.client.connected:
            return False

        try:
            result = self.client.write(tag_path, value)

            if result.error:
                logger.error(f"{self.name}: Write error: {result.error}")
                return False

            logger.info(f"{self.name}: Successfully wrote {value} to {tag_path}")
            return True

        except Exception as e:
            logger.error(f"{self.name}: Write exception: {e}")
            return False

    async def get_tag_list(self) -> List[Dict[str, Any]]:
        """
        Get list of all tags from PLC (useful for discovery).

        Returns:
            List of tag information dictionaries
        """
        if not self.client or not self.client.connected:
            return []

        try:
            # Get tag list from PLC
            tags = self.client.get_tag_list()

            tag_list = []
            for tag in tags:
                tag_list.append({
                    'tag_name': tag.get('tag_name', ''),
                    'tag_type': tag.get('tag_type', ''),
                    'dim': tag.get('dim', 0),
                    'data_type': tag.get('data_type', ''),
                })

            return tag_list

        except Exception as e:
            logger.error(f"{self.name}: Error getting tag list: {e}")
            return []
