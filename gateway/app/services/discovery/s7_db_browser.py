"""
S7 Data Block Browser

Browses and lists available Data Blocks in a Siemens PLC.
Provides DB structure and size information.

Note: Unlike Rockwell PLCs, S7 PLCs don't provide symbolic names
natively. Symbol information must be imported from TIA Portal exports.
"""

import asyncio
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import struct

from loguru import logger


@dataclass
class DBInfo:
    """Information about a Data Block"""
    db_number: int
    size: int  # Size in bytes
    accessible: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class DBStructure:
    """Structure information for a Data Block"""
    db_number: int
    size: int
    offset_map: Dict[int, str]  # offset -> inferred type
    raw_data: Optional[bytes] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        if data.get('raw_data'):
            data['raw_data'] = f"<{len(data['raw_data'])} bytes>"
        return data


class S7DBBrowser:
    """
    Browser for S7 Data Blocks.

    Features:
    - List all accessible DBs
    - Get DB size information
    - Read DB structure (raw bytes)
    - Infer basic type information from data patterns

    Limitations:
    - Cannot retrieve symbolic names (use Symbol Importer for that)
    - Type inference is basic (exact types need symbol file)
    """

    def __init__(self, ip_address: str, rack: int = 0, slot: int = 1):
        """
        Initialize DB browser.

        Args:
            ip_address: PLC IP address
            rack: Rack number
            slot: Slot number
        """
        self.ip_address = ip_address
        self.rack = rack
        self.slot = slot
        self._client = None

    def connect(self) -> bool:
        """Connect to PLC."""
        try:
            from ..protocols.s7 import S7Client

            self._client = S7Client(self.ip_address, self.rack, self.slot)
            return self._client.connect()

        except Exception as e:
            logger.error(f"Failed to connect to S7 PLC: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from PLC."""
        if self._client:
            self._client.disconnect()
            self._client = None

    def list_dbs(
        self,
        start_db: int = 1,
        end_db: int = 1000,
        max_dbs: int = 100
    ) -> List[DBInfo]:
        """
        List all accessible Data Blocks by probing.

        Since S7 PLCs don't provide a DB list natively, we probe each DB
        number to see if it's accessible.

        Args:
            start_db: Starting DB number to probe
            end_db: Ending DB number to probe
            max_dbs: Maximum number of DBs to find

        Returns:
            List of DBInfo objects for accessible DBs
        """
        if not self._client or not self._client.is_connected():
            if not self.connect():
                return []

        dbs = []
        found_count = 0

        logger.info(f"Scanning for DBs from DB{start_db} to DB{end_db}...")

        for db_num in range(start_db, end_db + 1):
            if found_count >= max_dbs:
                break

            try:
                # Try to read 1 byte to check if DB exists
                data = self._client.read_db(db_num, 0, 1)

                if data is not None:
                    # DB exists, now get its size
                    size = self._get_db_size(db_num)

                    db_info = DBInfo(
                        db_number=db_num,
                        size=size,
                        accessible=True
                    )

                    dbs.append(db_info)
                    found_count += 1

                    logger.debug(f"Found DB{db_num} (size: {size} bytes)")

            except Exception as e:
                # DB doesn't exist or not accessible
                logger.debug(f"DB{db_num} not accessible: {e}")
                continue

        logger.info(f"Found {len(dbs)} accessible Data Blocks")
        return dbs

    def _get_db_size(self, db_number: int) -> int:
        """
        Determine the size of a Data Block by binary search.

        Args:
            db_number: DB number

        Returns:
            Size in bytes
        """
        # Binary search for DB size
        # Start with reasonable bounds
        min_size = 0
        max_size = 65536  # 64KB max for most DBs

        # Try to read at different offsets to find the boundary
        last_successful = 0

        # Quick probe at common sizes
        test_sizes = [10, 100, 1000, 10000, 65536]

        for test_size in test_sizes:
            try:
                data = self._client.read_db(db_number, test_size - 1, 1)
                if data is not None:
                    last_successful = test_size
                else:
                    # Failed, so size is less than this
                    max_size = test_size
                    break
            except:
                max_size = test_size
                break

        # If we successfully read at max test size, do a more thorough search
        if last_successful > 0:
            # Binary search between last successful and max
            while min_size < max_size - 1:
                mid = (min_size + max_size) // 2

                try:
                    data = self._client.read_db(db_number, mid, 1)
                    if data is not None:
                        min_size = mid
                        last_successful = mid + 1
                    else:
                        max_size = mid
                except:
                    max_size = mid

            return last_successful

        return 0

    def get_db_structure(
        self,
        db_number: int,
        read_data: bool = False
    ) -> Optional[DBStructure]:
        """
        Get structure information for a Data Block.

        Args:
            db_number: DB number
            read_data: Whether to read the actual data

        Returns:
            DBStructure object or None if failed
        """
        if not self._client or not self._client.is_connected():
            if not self.connect():
                return None

        try:
            # Get DB size
            size = self._get_db_size(db_number)

            if size == 0:
                logger.error(f"DB{db_number} has size 0 or is not accessible")
                return None

            # Read data if requested
            raw_data = None
            if read_data:
                raw_data = self._client.read_db(db_number, 0, size)

            # Infer basic structure from size
            offset_map = self._infer_structure(size, raw_data)

            return DBStructure(
                db_number=db_number,
                size=size,
                offset_map=offset_map,
                raw_data=raw_data
            )

        except Exception as e:
            logger.error(f"Error getting structure for DB{db_number}: {e}")
            return None

    def _infer_structure(
        self,
        size: int,
        data: Optional[bytes] = None
    ) -> Dict[int, str]:
        """
        Infer basic structure from DB size and data.

        This is a simple heuristic-based approach. For accurate structure,
        use symbol files from TIA Portal.

        Args:
            size: DB size in bytes
            data: Raw DB data (optional)

        Returns:
            Dictionary mapping offset to inferred type
        """
        offset_map = {}

        if data is None:
            # Without data, we can only provide generic offsets
            offset = 0
            while offset < size:
                # Assume 4-byte (DWORD/REAL) alignment
                offset_map[offset] = "UNKNOWN"
                offset += 4

            return offset_map

        # With data, try to infer types based on patterns
        offset = 0

        while offset < len(data) - 1:
            # Check if this could be a BOOL (single bit usage)
            if offset < len(data):
                byte_val = data[offset]

                # If only bit 0 or 1 is set, likely BOOL
                if byte_val in [0, 1]:
                    offset_map[offset] = "BOOL (inferred)"
                    offset += 1
                    continue

            # Check if this could be an INT (2 bytes)
            if offset < len(data) - 1:
                int_val = struct.unpack('>h', data[offset:offset+2])[0]

                # Reasonable INT range
                if -32768 <= int_val <= 32767:
                    offset_map[offset] = "INT (inferred)"
                    offset += 2
                    continue

            # Check if this could be a REAL (4 bytes)
            if offset < len(data) - 3:
                try:
                    real_val = struct.unpack('>f', data[offset:offset+4])[0]

                    # Check if it's a reasonable float
                    if not (real_val != real_val):  # Not NaN
                        offset_map[offset] = "REAL (inferred)"
                        offset += 4
                        continue
                except:
                    pass

            # Default: treat as BYTE
            offset_map[offset] = "BYTE"
            offset += 1

        return offset_map

    def read_db_value(
        self,
        db_number: int,
        offset: int,
        data_type: str
    ) -> Optional[any]:
        """
        Read a specific value from a DB.

        Args:
            db_number: DB number
            offset: Byte offset
            data_type: Data type (BOOL, BYTE, INT, DINT, REAL, etc.)

        Returns:
            Value or None if read failed
        """
        if not self._client or not self._client.is_connected():
            if not self.connect():
                return None

        try:
            # Build address string
            address = self._build_address(db_number, offset, data_type)

            # Read using S7Client
            result = self._client.read_address(address)

            if result.quality == "Good":
                return result.value
            else:
                logger.error(f"Failed to read {address}: {result.error}")
                return None

        except Exception as e:
            logger.error(f"Error reading DB{db_number}.{offset}: {e}")
            return None

    def _build_address(
        self,
        db_number: int,
        offset: int,
        data_type: str
    ) -> str:
        """
        Build S7 address string from DB number, offset, and type.

        Args:
            db_number: DB number
            offset: Byte offset
            data_type: Data type

        Returns:
            Address string (e.g., "DB10.DBW0")
        """
        data_type = data_type.upper()

        if data_type == "BOOL":
            # BOOL needs bit offset (assume .0)
            return f"DB{db_number}.DBX{offset}.0"
        elif data_type == "BYTE":
            return f"DB{db_number}.DBB{offset}"
        elif data_type == "WORD" or data_type == "INT":
            return f"DB{db_number}.DBW{offset}"
        elif data_type == "DWORD" or data_type == "DINT":
            return f"DB{db_number}.DBD{offset}"
        elif data_type == "REAL":
            return f"DB{db_number}.DBREAL{offset}"
        else:
            # Default to DWORD
            return f"DB{db_number}.DBD{offset}"

    def export_db_list_to_dict(self, dbs: List[DBInfo]) -> Dict:
        """
        Export DB list to dictionary format.

        Args:
            dbs: List of DBInfo objects

        Returns:
            Dictionary with DB information
        """
        return {
            "device": {
                "ip_address": self.ip_address,
                "rack": self.rack,
                "slot": self.slot
            },
            "db_count": len(dbs),
            "total_size": sum(db.size for db in dbs),
            "dbs": [db.to_dict() for db in dbs]
        }

    async def list_dbs_async(
        self,
        start_db: int = 1,
        end_db: int = 1000,
        max_dbs: int = 100
    ) -> List[DBInfo]:
        """Async wrapper for list_dbs."""
        return await asyncio.to_thread(self.list_dbs, start_db, end_db, max_dbs)

    async def get_db_structure_async(
        self,
        db_number: int,
        read_data: bool = False
    ) -> Optional[DBStructure]:
        """Async wrapper for get_db_structure."""
        return await asyncio.to_thread(self.get_db_structure, db_number, read_data)

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
