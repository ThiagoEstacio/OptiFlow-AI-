"""
Ethernet/IP Protocol Handler (Allen-Bradley/Rockwell)
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pycomm3 import LogixDriver, Tag

from ..core.base_protocol import BaseProtocolHandler, TagValue
from ..core.logger import logger


class EthernetIPHandler(BaseProtocolHandler):
    """
    Ethernet/IP protocol handler using pycomm3 library
    Primarily for Allen-Bradley/Rockwell PLCs (CompactLogix, ControlLogix)
    """

    def __init__(self, device_id: str, config: Dict[str, Any]):
        """
        Initialize Ethernet/IP handler

        Config keys:
            - host: PLC IP address
            - port: CIP port (default: 44818)
            - slot: PLC slot number (default: 0)
            - timeout: Connection timeout (default: 10)
            - micro800: Set True for Micro800 series (default: False)
        """
        super().__init__(device_id, config)

        self.host = config.get("host")
        self.port = config.get("port", 44818)
        self.slot = config.get("slot", 0)
        self.timeout = config.get("timeout", 10)
        self.micro800 = config.get("micro800", False)

        self.driver: Optional[LogixDriver] = None

    async def connect(self) -> bool:
        """Connect to Ethernet/IP device"""
        async with self._lock:
            try:
                logger.info(f"Connecting to Ethernet/IP PLC: {self.host}")

                # Create driver
                self.driver = LogixDriver(
                    path=self.host,
                    init_tags=False,  # Don't auto-read all tags
                    init_info=True,   # Read PLC info
                    micro800=self.micro800
                )

                # Open connection
                success = self.driver.open()

                if success and not self.driver.error:
                    self.update_status(connected=True)
                    logger.info(f"✓ Connected to Ethernet/IP PLC: {self.host}")
                    logger.info(f"  Name: {self.driver.name}")
                    logger.info(f"  Revision: {self.driver.revision}")
                    return True
                else:
                    error_msg = f"Ethernet/IP connection failed: {self.driver.error}"
                    logger.error(error_msg)
                    self.update_status(connected=False, error=error_msg)
                    return False

            except Exception as e:
                error_msg = f"Ethernet/IP connection error: {str(e)}"
                logger.error(error_msg)
                self.update_status(connected=False, error=error_msg)
                return False

    async def disconnect(self) -> bool:
        """Disconnect from Ethernet/IP device"""
        async with self._lock:
            try:
                if self.driver:
                    self.driver.close()
                    self.driver = None

                self.update_status(connected=False)
                logger.info("Disconnected from Ethernet/IP PLC")
                return True

            except Exception as e:
                logger.error(f"Ethernet/IP disconnect error: {str(e)}")
                return False

    async def read_tag(self, tag_address: str) -> Optional[TagValue]:
        """
        Read single Ethernet/IP tag

        Args:
            tag_address: Tag name (e.g., "MyTag", "Program:MainProgram.MyTag")

        Returns:
            TagValue or None if error
        """
        try:
            if not self.is_connected:
                await self.connect()

            if not self.driver:
                return None

            # Read tag
            result = self.driver.read(tag_address)

            if result.error:
                logger.error(f"Failed to read tag {tag_address}: {result.error}")
                quality = "bad"
                value = None
            else:
                quality = "good"
                value = result.value

            tag_value = TagValue(
                tag_id=tag_address,
                tag_name=tag_address,
                value=value,
                quality=quality,
                timestamp=datetime.now()
            )

            return tag_value

        except Exception as e:
            logger.error(f"Failed to read Ethernet/IP tag {tag_address}: {str(e)}")
            self.update_status(connected=False, error=str(e))
            return None

    async def read_tags(self, tag_addresses: List[str]) -> List[TagValue]:
        """
        Read multiple Ethernet/IP tags

        Args:
            tag_addresses: List of tag names

        Returns:
            List of TagValue objects
        """
        results = []

        try:
            if not self.is_connected:
                await self.connect()

            if not self.driver:
                return results

            # Read multiple tags at once (more efficient)
            read_results = self.driver.read(*tag_addresses)

            # Handle single tag result
            if not isinstance(read_results, list):
                read_results = [read_results]

            # Process results
            for address, result in zip(tag_addresses, read_results):
                if result.error:
                    logger.error(f"Failed to read tag {address}: {result.error}")
                    quality = "bad"
                    value = None
                else:
                    quality = "good"
                    value = result.value

                tag_value = TagValue(
                    tag_id=address,
                    tag_name=address,
                    value=value,
                    quality=quality,
                    timestamp=datetime.now()
                )
                results.append(tag_value)

        except Exception as e:
            logger.error(f"Failed to read Ethernet/IP tags: {str(e)}")
            self.update_status(connected=False, error=str(e))

        return results

    async def write_tag(self, tag_address: str, value: Any) -> bool:
        """
        Write to Ethernet/IP tag

        Args:
            tag_address: Tag name
            value: Value to write

        Returns:
            True if write successful
        """
        try:
            if not self.is_connected:
                await self.connect()

            if not self.driver:
                return False

            # Write tag
            result = self.driver.write(tag_address, value)

            if result.error:
                logger.error(f"Failed to write tag {tag_address}: {result.error}")
                return False

            logger.info(f"✓ Wrote value {value} to Ethernet/IP tag {tag_address}")
            return True

        except Exception as e:
            logger.error(f"Failed to write Ethernet/IP tag {tag_address}: {str(e)}")
            self.update_status(connected=False, error=str(e))
            return False

    async def health_check(self) -> bool:
        """Check Ethernet/IP PLC health"""
        try:
            if not self.driver:
                return False

            # Try to get PLC info
            info = self.driver.get_plc_info()

            if info and not self.driver.error:
                self.update_status(connected=True)
                return True
            else:
                self.update_status(connected=False, error="Health check failed")
                return False

        except Exception as e:
            logger.error(f"Ethernet/IP health check failed: {str(e)}")
            self.update_status(connected=False, error=str(e))
            return False

    async def get_tag_list(self, program: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of available tags from PLC

        Args:
            program: Optional program name to filter tags

        Returns:
            List of tag information dictionaries
        """
        results = []

        try:
            if not self.is_connected:
                await self.connect()

            if not self.driver:
                return results

            # Get all tags
            tags = self.driver.get_tag_list(program=program)

            for tag in tags:
                tag_info = {
                    "tag_name": tag.get('tag_name', ''),
                    "tag_type": tag.get('tag_type', ''),
                    "dim": tag.get('dim', 0),
                    "alias": tag.get('alias', False)
                }
                results.append(tag_info)

            logger.info(f"Retrieved {len(results)} tags from PLC")

        except Exception as e:
            logger.error(f"Failed to get tag list: {str(e)}")

        return results

    async def discover_tags(self) -> List[str]:
        """
        Discover all tag names in the PLC

        Returns:
            List of tag names
        """
        tags = await self.get_tag_list()
        return [tag['tag_name'] for tag in tags]
