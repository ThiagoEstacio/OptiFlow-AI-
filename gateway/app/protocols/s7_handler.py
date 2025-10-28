"""
Siemens S7 Protocol Handler
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import struct
import snap7
from snap7.util import *
from snap7.types import *

from ..core.base_protocol import BaseProtocolHandler, TagValue
from ..core.logger import logger


class S7Handler(BaseProtocolHandler):
    """
    Siemens S7 protocol handler using python-snap7 library
    Supports S7-300, S7-400, S7-1200, S7-1500
    """

    def __init__(self, device_id: str, config: Dict[str, Any]):
        """
        Initialize S7 handler

        Config keys:
            - host: PLC IP address
            - rack: Rack number (default: 0)
            - slot: Slot number (default: 1 for S7-300/400, 0 for S7-1200/1500)
            - tcp_port: TCP port (default: 102)
            - timeout: Connection timeout (default: 10)
        """
        super().__init__(device_id, config)

        self.host = config.get("host")
        self.rack = config.get("rack", 0)
        self.slot = config.get("slot", 1)
        self.tcp_port = config.get("tcp_port", 102)
        self.timeout = config.get("timeout", 10)

        self.client: Optional[snap7.client.Client] = None

    async def connect(self) -> bool:
        """Connect to S7 PLC"""
        async with self._lock:
            try:
                logger.info(f"Connecting to Siemens S7 PLC: {self.host} (Rack {self.rack}, Slot {self.slot})")

                # Create client
                self.client = snap7.client.Client()

                # Set connection parameters
                self.client.set_connection_params(self.host, self.tcp_port, self.tcp_port)

                # Connect
                self.client.connect(self.host, self.rack, self.slot)

                # Verify connection
                if self.client.get_connected():
                    self.update_status(connected=True)

                    # Get PLC info
                    cpu_info = self.client.get_cpu_info()
                    logger.info(f"✓ Connected to S7 PLC: {self.host}")
                    logger.info(f"  Module: {cpu_info.ModuleName.decode('utf-8').strip()}")
                    logger.info(f"  Serial: {cpu_info.SerialNumber.decode('utf-8').strip()}")

                    return True
                else:
                    error_msg = "S7 connection failed"
                    logger.error(error_msg)
                    self.update_status(connected=False, error=error_msg)
                    return False

            except Exception as e:
                error_msg = f"S7 connection error: {str(e)}"
                logger.error(error_msg)
                self.update_status(connected=False, error=error_msg)
                return False

    async def disconnect(self) -> bool:
        """Disconnect from S7 PLC"""
        async with self._lock:
            try:
                if self.client:
                    self.client.disconnect()
                    self.client.destroy()
                    self.client = None

                self.update_status(connected=False)
                logger.info("Disconnected from S7 PLC")
                return True

            except Exception as e:
                logger.error(f"S7 disconnect error: {str(e)}")
                return False

    def _parse_address(self, address: str) -> tuple:
        """
        Parse S7 address string

        Formats:
            - "DB1.DBD0" = Data Block 1, Double Word at byte 0
            - "DB1.DBW10" = Data Block 1, Word at byte 10
            - "DB1.DBB20" = Data Block 1, Byte at byte 20
            - "DB1.DBX0.0" = Data Block 1, Bit at byte 0, bit 0
            - "M0.0" = Memory bit 0.0
            - "I0.0" = Input bit 0.0
            - "Q0.0" = Output bit 0.0

        Returns:
            (area, db_number, start_byte, bit_offset, data_type, size)
        """
        address = address.upper()

        # Data Block addresses
        if address.startswith("DB"):
            parts = address.split(".")
            db_number = int(parts[0][2:])  # Extract DB number

            addr_part = parts[1]

            # Bit access (DBX)
            if addr_part.startswith("DBX"):
                byte_addr = int(addr_part[3:])
                bit_offset = int(parts[2]) if len(parts) > 2 else 0
                return (Areas.DB, db_number, byte_addr, bit_offset, "BOOL", 1)

            # Byte access (DBB)
            elif addr_part.startswith("DBB"):
                byte_addr = int(addr_part[3:])
                return (Areas.DB, db_number, byte_addr, 0, "BYTE", 1)

            # Word access (DBW)
            elif addr_part.startswith("DBW"):
                byte_addr = int(addr_part[3:])
                return (Areas.DB, db_number, byte_addr, 0, "WORD", 2)

            # Double Word access (DBD)
            elif addr_part.startswith("DBD"):
                byte_addr = int(addr_part[3:])
                return (Areas.DB, db_number, byte_addr, 0, "DWORD", 4)

            # Real (Float) access (DBD but as REAL)
            elif addr_part.startswith("DBR"):
                byte_addr = int(addr_part[3:])
                return (Areas.DB, db_number, byte_addr, 0, "REAL", 4)

        # Memory area (M)
        elif address.startswith("M"):
            if "." in address:
                # Bit access
                parts = address[1:].split(".")
                byte_addr = int(parts[0])
                bit_offset = int(parts[1])
                return (Areas.MK, 0, byte_addr, bit_offset, "BOOL", 1)
            else:
                # Byte access
                byte_addr = int(address[1:])
                return (Areas.MK, 0, byte_addr, 0, "BYTE", 1)

        # Input area (I)
        elif address.startswith("I"):
            if "." in address:
                parts = address[1:].split(".")
                byte_addr = int(parts[0])
                bit_offset = int(parts[1])
                return (Areas.PE, 0, byte_addr, bit_offset, "BOOL", 1)
            else:
                byte_addr = int(address[1:])
                return (Areas.PE, 0, byte_addr, 0, "BYTE", 1)

        # Output area (Q)
        elif address.startswith("Q"):
            if "." in address:
                parts = address[1:].split(".")
                byte_addr = int(parts[0])
                bit_offset = int(parts[1])
                return (Areas.PA, 0, byte_addr, bit_offset, "BOOL", 1)
            else:
                byte_addr = int(address[1:])
                return (Areas.PA, 0, byte_addr, 0, "BYTE", 1)

        # Default
        return (Areas.DB, 1, 0, 0, "BYTE", 1)

    async def read_tag(self, tag_address: str) -> Optional[TagValue]:
        """
        Read single S7 tag

        Args:
            tag_address: S7 address (e.g., "DB1.DBD0", "M0.0", "I0.1")

        Returns:
            TagValue or None if error
        """
        try:
            if not self.is_connected:
                await self.connect()

            if not self.client:
                return None

            area, db_number, byte_addr, bit_offset, data_type, size = self._parse_address(tag_address)

            # Read data
            if area == Areas.DB:
                data = self.client.db_read(db_number, byte_addr, size)
            elif area == Areas.MK:
                data = self.client.read_area(Areas.MK, 0, byte_addr, size)
            elif area == Areas.PE:
                data = self.client.read_area(Areas.PE, 0, byte_addr, size)
            elif area == Areas.PA:
                data = self.client.read_area(Areas.PA, 0, byte_addr, size)
            else:
                logger.error(f"Unsupported S7 area: {area}")
                return None

            # Decode value
            value = self._decode_value(data, byte_addr, bit_offset, data_type)

            tag_value = TagValue(
                tag_id=tag_address,
                tag_name=tag_address,
                value=value,
                quality="good",
                timestamp=datetime.now()
            )

            return tag_value

        except Exception as e:
            logger.error(f"Failed to read S7 tag {tag_address}: {str(e)}")
            self.update_status(connected=False, error=str(e))
            return None

    def _decode_value(self, data: bytearray, byte_offset: int, bit_offset: int, data_type: str) -> Any:
        """Decode S7 data based on type"""
        try:
            if data_type == "BOOL":
                return get_bool(data, 0, bit_offset)
            elif data_type == "BYTE":
                return data[0]
            elif data_type == "WORD":
                return get_int(data, 0)
            elif data_type == "DWORD":
                return get_dword(data, 0)
            elif data_type == "REAL":
                return get_real(data, 0)
            else:
                return data[0]

        except Exception as e:
            logger.error(f"Failed to decode S7 value: {str(e)}")
            return None

    async def read_tags(self, tag_addresses: List[str]) -> List[TagValue]:
        """Read multiple S7 tags"""
        results = []

        for address in tag_addresses:
            tag_value = await self.read_tag(address)
            if tag_value:
                results.append(tag_value)

        return results

    async def write_tag(self, tag_address: str, value: Any) -> bool:
        """Write to S7 tag"""
        try:
            if not self.is_connected:
                await self.connect()

            if not self.client:
                return False

            area, db_number, byte_addr, bit_offset, data_type, size = self._parse_address(tag_address)

            # Encode value
            data = bytearray(size)
            if data_type == "BOOL":
                set_bool(data, 0, bit_offset, bool(value))
            elif data_type == "BYTE":
                data[0] = int(value)
            elif data_type == "WORD":
                set_int(data, 0, int(value))
            elif data_type == "DWORD":
                set_dword(data, 0, int(value))
            elif data_type == "REAL":
                set_real(data, 0, float(value))

            # Write data
            if area == Areas.DB:
                self.client.db_write(db_number, byte_addr, data)
            elif area == Areas.MK:
                self.client.write_area(Areas.MK, 0, byte_addr, data)
            elif area == Areas.PA:
                self.client.write_area(Areas.PA, 0, byte_addr, data)
            else:
                logger.error(f"Cannot write to S7 area: {area}")
                return False

            logger.info(f"✓ Wrote value {value} to S7 tag {tag_address}")
            return True

        except Exception as e:
            logger.error(f"Failed to write S7 tag {tag_address}: {str(e)}")
            self.update_status(connected=False, error=str(e))
            return False

    async def health_check(self) -> bool:
        """Check S7 PLC health"""
        try:
            if not self.client:
                return False

            # Check connection and get CPU state
            state = self.client.get_cpu_state()

            if state:
                self.update_status(connected=True)
                return True
            else:
                self.update_status(connected=False, error="Health check failed")
                return False

        except Exception as e:
            logger.error(f"S7 health check failed: {str(e)}")
            self.update_status(connected=False, error=str(e))
            return False

    async def read_db(self, db_number: int, start: int, size: int) -> Optional[bytearray]:
        """
        Read entire data block

        Args:
            db_number: Data block number
            start: Start byte
            size: Number of bytes to read

        Returns:
            Bytearray of data or None
        """
        try:
            if not self.is_connected:
                await self.connect()

            if not self.client:
                return None

            data = self.client.db_read(db_number, start, size)
            return data

        except Exception as e:
            logger.error(f"Failed to read S7 DB{db_number}: {str(e)}")
            return None
