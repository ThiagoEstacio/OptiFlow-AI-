"""
S7 Protocol Handler for Siemens PLCs

Supports:
- S7-300, S7-400, S7-1200, S7-1500
- Data types: BOOL, BYTE, WORD, DWORD, INT, DINT, REAL, STRING
- DB (Data Block) reading and writing
- Input, Output, and Merker (Flag) access
- Asynchronous operations with asyncio wrapper
- Comprehensive error handling and retries

Uses python-snap7 library which wraps the Snap7 C library.
"""

import asyncio
import logging
import struct
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import time

from loguru import logger
import snap7
from snap7.snap7types import S7AreaDB, S7AreaPE, S7AreaPA, S7AreaMK, S7AreaTM, S7AreaCT
from snap7.util import *


class S7DataType(str, Enum):
    """Supported S7 data types"""
    BOOL = "BOOL"
    BYTE = "BYTE"
    WORD = "WORD"
    DWORD = "DWORD"
    INT = "INT"  # 16-bit signed integer
    DINT = "DINT"  # 32-bit signed integer
    REAL = "REAL"  # 32-bit floating point
    STRING = "STRING"
    CHAR = "CHAR"
    TIME = "TIME"
    DATE = "DATE"


class S7AreaType(str, Enum):
    """S7 memory areas"""
    DB = "DB"  # Data Block
    INPUT = "I"  # Process Input
    OUTPUT = "Q"  # Process Output
    MERKER = "M"  # Flag/Marker
    TIMER = "T"  # Timer
    COUNTER = "C"  # Counter


class ConnectionStatus(str, Enum):
    """Connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CONNECTING = "connecting"


@dataclass
class S7Value:
    """Represents an S7 value with metadata"""
    address: str
    value: Any
    data_type: Optional[str] = None
    quality: str = "Good"
    timestamp: Optional[float] = None
    error: Optional[str] = None


@dataclass
class S7DeviceInfo:
    """S7 PLC device information"""
    ip_address: str
    rack: int = 0
    slot: int = 1
    cpu_type: Optional[str] = None
    serial_number: Optional[str] = None
    module_type: Optional[str] = None
    status: str = ConnectionStatus.DISCONNECTED


class S7Client:
    """
    S7 Protocol client for Siemens PLCs using python-snap7.

    Features:
    - Connection management with auto-reconnect
    - DB, Input, Output, Merker access
    - Multiple data type support
    - Bit-level operations
    - Error handling with retries
    - Quality codes (Good/Bad)
    """

    # Area type mapping for snap7
    AREA_MAP = {
        S7AreaType.DB: S7AreaDB,
        S7AreaType.INPUT: S7AreaPE,
        S7AreaType.OUTPUT: S7AreaPA,
        S7AreaType.MERKER: S7AreaMK,
        S7AreaType.TIMER: S7AreaTM,
        S7AreaType.COUNTER: S7AreaCT
    }

    def __init__(
        self,
        ip_address: str,
        rack: int = 0,
        slot: int = 1,
        timeout: float = 5.0,
        max_retries: int = 3
    ):
        """
        Initialize S7 client.

        Args:
            ip_address: PLC IP address
            rack: Rack number (usually 0)
            slot: Slot number (usually 1 for CPU, 2 for some models)
            timeout: Connection timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.ip_address = ip_address
        self.rack = rack
        self.slot = slot
        self.timeout = timeout
        self.max_retries = max_retries

        self._client: Optional[snap7.client.Client] = None
        self._connected = False
        self._connection_lock = asyncio.Lock()

        logger.info(f"S7 client initialized for {ip_address}:{rack}/{slot}")

    def connect(self) -> bool:
        """
        Establish connection to PLC.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self._client is not None:
                self._client.disconnect()

            self._client = snap7.client.Client()

            # Set connection parameters
            self._client.set_connection_params(self.ip_address, 102, self.rack, self.slot)
            self._client.set_connection_type(3)  # PG (Programming Console)

            # Connect
            self._client.connect(self.ip_address, self.rack, self.slot)

            if not self._client.get_connected():
                raise Exception("Failed to connect to PLC")

            self._connected = True
            logger.info(f"Connected to S7 PLC at {self.ip_address}")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to {self.ip_address}: {e}")
            self._connected = False
            return False

    def disconnect(self) -> None:
        """Close connection to PLC."""
        try:
            if self._client is not None:
                self._client.disconnect()
                logger.info(f"Disconnected from {self.ip_address}")
        except Exception as e:
            logger.error(f"Error disconnecting from {self.ip_address}: {e}")
        finally:
            self._connected = False
            self._client = None

    def is_connected(self) -> bool:
        """Check if connected to PLC."""
        return (
            self._connected and
            self._client is not None and
            self._client.get_connected()
        )

    def read_db(self, db_number: int, start: int, size: int) -> Optional[bytes]:
        """
        Read data from a Data Block.

        Args:
            db_number: DB number
            start: Start byte offset
            size: Number of bytes to read

        Returns:
            Bytes read or None on error
        """
        if not self.is_connected():
            logger.error("Cannot read DB: Not connected")
            return None

        try:
            data = self._client.db_read(db_number, start, size)
            return data

        except Exception as e:
            logger.error(f"Error reading DB{db_number}.{start}: {e}")
            return None

    def write_db(self, db_number: int, start: int, data: bytes) -> bool:
        """
        Write data to a Data Block.

        Args:
            db_number: DB number
            start: Start byte offset
            data: Bytes to write

        Returns:
            True if write successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot write DB: Not connected")
            return False

        try:
            self._client.db_write(db_number, start, data)
            return True

        except Exception as e:
            logger.error(f"Error writing DB{db_number}.{start}: {e}")
            return False

    def read_inputs(self, start: int, size: int) -> Optional[bytes]:
        """
        Read process inputs (I area).

        Args:
            start: Start byte offset
            size: Number of bytes to read

        Returns:
            Bytes read or None on error
        """
        if not self.is_connected():
            return None

        try:
            data = self._client.read_area(S7AreaPE, 0, start, size)
            return data

        except Exception as e:
            logger.error(f"Error reading inputs at I{start}: {e}")
            return None

    def read_outputs(self, start: int, size: int) -> Optional[bytes]:
        """
        Read process outputs (Q area).

        Args:
            start: Start byte offset
            size: Number of bytes to read

        Returns:
            Bytes read or None on error
        """
        if not self.is_connected():
            return None

        try:
            data = self._client.read_area(S7AreaPA, 0, start, size)
            return data

        except Exception as e:
            logger.error(f"Error reading outputs at Q{start}: {e}")
            return None

    def read_merkers(self, start: int, size: int) -> Optional[bytes]:
        """
        Read merkers/flags (M area).

        Args:
            start: Start byte offset
            size: Number of bytes to read

        Returns:
            Bytes read or None on error
        """
        if not self.is_connected():
            return None

        try:
            data = self._client.read_area(S7AreaMK, 0, start, size)
            return data

        except Exception as e:
            logger.error(f"Error reading merkers at M{start}: {e}")
            return None

    def read_address(self, address: str) -> S7Value:
        """
        Read value from an S7 address.

        Address formats:
        - DB10.DBX0.0 - BOOL at DB10, byte 0, bit 0
        - DB10.DBB0 - BYTE at DB10, byte 0
        - DB10.DBW0 - WORD at DB10, byte 0
        - DB10.DBD0 - DWORD at DB10, byte 0
        - DB10.DBREAL0 - REAL at DB10, byte 0
        - I0.0 - Input bit 0.0
        - Q0.0 - Output bit 0.0
        - M0.0 - Merker bit 0.0

        Args:
            address: S7 address string

        Returns:
            S7Value object with value and metadata
        """
        if not self.is_connected():
            return S7Value(
                address=address,
                value=None,
                quality="Bad",
                error="Not connected to PLC"
            )

        try:
            # Parse address
            parsed = self._parse_address(address)
            if not parsed:
                return S7Value(
                    address=address,
                    value=None,
                    quality="Bad",
                    error="Invalid address format"
                )

            area_type, db_number, byte_offset, bit_offset, data_type, size = parsed

            # Read raw bytes
            if area_type == S7AreaType.DB:
                raw_data = self.read_db(db_number, byte_offset, size)
            elif area_type == S7AreaType.INPUT:
                raw_data = self.read_inputs(byte_offset, size)
            elif area_type == S7AreaType.OUTPUT:
                raw_data = self.read_outputs(byte_offset, size)
            elif area_type == S7AreaType.MERKER:
                raw_data = self.read_merkers(byte_offset, size)
            else:
                return S7Value(
                    address=address,
                    value=None,
                    quality="Bad",
                    error=f"Unsupported area type: {area_type}"
                )

            if raw_data is None:
                return S7Value(
                    address=address,
                    value=None,
                    quality="Bad",
                    error="Read failed"
                )

            # Convert bytes to value based on data type
            value = self._bytes_to_value(raw_data, data_type, bit_offset)

            return S7Value(
                address=address,
                value=value,
                data_type=data_type,
                quality="Good",
                timestamp=time.time()
            )

        except Exception as e:
            logger.error(f"Error reading address {address}: {e}")
            return S7Value(
                address=address,
                value=None,
                quality="Bad",
                error=str(e)
            )

    def write_address(self, address: str, value: Any) -> bool:
        """
        Write value to an S7 address.

        Args:
            address: S7 address string
            value: Value to write

        Returns:
            True if write successful, False otherwise
        """
        if not self.is_connected():
            logger.error(f"Cannot write to {address}: Not connected")
            return False

        try:
            # Parse address
            parsed = self._parse_address(address)
            if not parsed:
                logger.error(f"Invalid address format: {address}")
                return False

            area_type, db_number, byte_offset, bit_offset, data_type, size = parsed

            # Convert value to bytes
            data = self._value_to_bytes(value, data_type, bit_offset)

            # Write bytes
            if area_type == S7AreaType.DB:
                return self.write_db(db_number, byte_offset, data)
            else:
                # TODO: Implement write for I/Q/M areas
                logger.error(f"Write not implemented for area type: {area_type}")
                return False

        except Exception as e:
            logger.error(f"Error writing to {address}: {e}")
            return False

    def _parse_address(self, address: str) -> Optional[Tuple]:
        """
        Parse S7 address string.

        Returns:
            Tuple of (area_type, db_number, byte_offset, bit_offset, data_type, size)
            or None if parsing fails
        """
        try:
            address = address.upper().strip()

            # DB addresses
            if address.startswith("DB"):
                parts = address.split(".")
                db_number = int(parts[0][2:])

                if len(parts) < 2:
                    return None

                type_part = parts[1]

                # BOOL: DB10.DBX0.0
                if type_part.startswith("DBX") and len(parts) == 3:
                    byte_offset = int(type_part[3:])
                    bit_offset = int(parts[2])
                    return (S7AreaType.DB, db_number, byte_offset, bit_offset, S7DataType.BOOL, 1)

                # BYTE: DB10.DBB0
                elif type_part.startswith("DBB"):
                    byte_offset = int(type_part[3:])
                    return (S7AreaType.DB, db_number, byte_offset, 0, S7DataType.BYTE, 1)

                # WORD: DB10.DBW0
                elif type_part.startswith("DBW"):
                    byte_offset = int(type_part[3:])
                    return (S7AreaType.DB, db_number, byte_offset, 0, S7DataType.WORD, 2)

                # DWORD: DB10.DBD0
                elif type_part.startswith("DBD"):
                    byte_offset = int(type_part[3:])
                    return (S7AreaType.DB, db_number, byte_offset, 0, S7DataType.DWORD, 4)

                # INT: DB10.DBINT0 or infer from size
                elif type_part.startswith("DBINT"):
                    byte_offset = int(type_part[5:])
                    return (S7AreaType.DB, db_number, byte_offset, 0, S7DataType.INT, 2)

                # DINT: DB10.DBDINT0
                elif type_part.startswith("DBDINT"):
                    byte_offset = int(type_part[6:])
                    return (S7AreaType.DB, db_number, byte_offset, 0, S7DataType.DINT, 4)

                # REAL: DB10.DBREAL0
                elif type_part.startswith("DBREAL"):
                    byte_offset = int(type_part[6:])
                    return (S7AreaType.DB, db_number, byte_offset, 0, S7DataType.REAL, 4)

            # Input: I0.0 or IB0, IW0, ID0
            elif address.startswith("I"):
                if "." in address:
                    # Bit: I0.0
                    parts = address[1:].split(".")
                    byte_offset = int(parts[0])
                    bit_offset = int(parts[1])
                    return (S7AreaType.INPUT, 0, byte_offset, bit_offset, S7DataType.BOOL, 1)
                elif address[1] == "B":
                    # Byte: IB0
                    byte_offset = int(address[2:])
                    return (S7AreaType.INPUT, 0, byte_offset, 0, S7DataType.BYTE, 1)
                elif address[1] == "W":
                    # Word: IW0
                    byte_offset = int(address[2:])
                    return (S7AreaType.INPUT, 0, byte_offset, 0, S7DataType.WORD, 2)
                elif address[1] == "D":
                    # DWord: ID0
                    byte_offset = int(address[2:])
                    return (S7AreaType.INPUT, 0, byte_offset, 0, S7DataType.DWORD, 4)

            # Output: Q0.0 or QB0, QW0, QD0
            elif address.startswith("Q"):
                if "." in address:
                    parts = address[1:].split(".")
                    byte_offset = int(parts[0])
                    bit_offset = int(parts[1])
                    return (S7AreaType.OUTPUT, 0, byte_offset, bit_offset, S7DataType.BOOL, 1)
                elif address[1] == "B":
                    byte_offset = int(address[2:])
                    return (S7AreaType.OUTPUT, 0, byte_offset, 0, S7DataType.BYTE, 1)
                elif address[1] == "W":
                    byte_offset = int(address[2:])
                    return (S7AreaType.OUTPUT, 0, byte_offset, 0, S7DataType.WORD, 2)
                elif address[1] == "D":
                    byte_offset = int(address[2:])
                    return (S7AreaType.OUTPUT, 0, byte_offset, 0, S7DataType.DWORD, 4)

            # Merker: M0.0 or MB0, MW0, MD0
            elif address.startswith("M"):
                if "." in address:
                    parts = address[1:].split(".")
                    byte_offset = int(parts[0])
                    bit_offset = int(parts[1])
                    return (S7AreaType.MERKER, 0, byte_offset, bit_offset, S7DataType.BOOL, 1)
                elif address[1] == "B":
                    byte_offset = int(address[2:])
                    return (S7AreaType.MERKER, 0, byte_offset, 0, S7DataType.BYTE, 1)
                elif address[1] == "W":
                    byte_offset = int(address[2:])
                    return (S7AreaType.MERKER, 0, byte_offset, 0, S7DataType.WORD, 2)
                elif address[1] == "D":
                    byte_offset = int(address[2:])
                    return (S7AreaType.MERKER, 0, byte_offset, 0, S7DataType.DWORD, 4)

            return None

        except Exception as e:
            logger.error(f"Error parsing address {address}: {e}")
            return None

    def _bytes_to_value(self, data: bytes, data_type: str, bit_offset: int = 0) -> Any:
        """Convert bytes to value based on data type."""
        try:
            if data_type == S7DataType.BOOL:
                return get_bool(data, 0, bit_offset)
            elif data_type == S7DataType.BYTE:
                return data[0]
            elif data_type == S7DataType.WORD:
                return get_word(data, 0)
            elif data_type == S7DataType.DWORD:
                return get_dword(data, 0)
            elif data_type == S7DataType.INT:
                return get_int(data, 0)
            elif data_type == S7DataType.DINT:
                return get_dint(data, 0)
            elif data_type == S7DataType.REAL:
                return get_real(data, 0)
            else:
                return data

        except Exception as e:
            logger.error(f"Error converting bytes to {data_type}: {e}")
            return None

    def _value_to_bytes(self, value: Any, data_type: str, bit_offset: int = 0) -> bytes:
        """Convert value to bytes based on data type."""
        try:
            if data_type == S7DataType.BOOL:
                data = bytearray(1)
                set_bool(data, 0, bit_offset, value)
                return bytes(data)
            elif data_type == S7DataType.BYTE:
                return bytes([value])
            elif data_type == S7DataType.WORD:
                data = bytearray(2)
                set_word(data, 0, value)
                return bytes(data)
            elif data_type == S7DataType.DWORD:
                data = bytearray(4)
                set_dword(data, 0, value)
                return bytes(data)
            elif data_type == S7DataType.INT:
                data = bytearray(2)
                set_int(data, 0, value)
                return bytes(data)
            elif data_type == S7DataType.DINT:
                data = bytearray(4)
                set_dint(data, 0, value)
                return bytes(data)
            elif data_type == S7DataType.REAL:
                data = bytearray(4)
                set_real(data, 0, value)
                return bytes(data)
            else:
                return bytes(value)

        except Exception as e:
            logger.error(f"Error converting {value} to {data_type}: {e}")
            return b''

    def get_device_info(self) -> Optional[S7DeviceInfo]:
        """
        Get PLC device information.

        Returns:
            S7DeviceInfo object or None if failed
        """
        if not self.is_connected():
            if not self.connect():
                return None

        try:
            cpu_info = self._client.get_cpu_info()

            return S7DeviceInfo(
                ip_address=self.ip_address,
                rack=self.rack,
                slot=self.slot,
                cpu_type=cpu_info.ModuleTypeName.decode('utf-8'),
                serial_number=cpu_info.SerialNumber.decode('utf-8'),
                module_type=cpu_info.ASName.decode('utf-8'),
                status=ConnectionStatus.CONNECTED
            )

        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return S7DeviceInfo(
                ip_address=self.ip_address,
                rack=self.rack,
                slot=self.slot,
                status=ConnectionStatus.ERROR
            )

    # Async wrappers
    async def connect_async(self) -> bool:
        """Async wrapper for connect."""
        async with self._connection_lock:
            return await asyncio.to_thread(self.connect)

    async def disconnect_async(self) -> None:
        """Async wrapper for disconnect."""
        async with self._connection_lock:
            await asyncio.to_thread(self.disconnect)

    async def read_address_async(self, address: str) -> S7Value:
        """Async wrapper for read_address."""
        return await asyncio.to_thread(self.read_address, address)

    async def write_address_async(self, address: str, value: Any) -> bool:
        """Async wrapper for write_address."""
        return await asyncio.to_thread(self.write_address, address, value)

    async def get_device_info_async(self) -> Optional[S7DeviceInfo]:
        """Async wrapper for get_device_info."""
        return await asyncio.to_thread(self.get_device_info)

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def __del__(self):
        """Cleanup on deletion."""
        self.disconnect()
