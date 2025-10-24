"""
S7 Symbol Importer

Imports symbolic tag names from TIA Portal exports (CSV or SDF format).

Siemens PLCs don't provide symbolic names via S7 protocol. Names must be
exported from the engineering environment (TIA Portal, Step7).

Supported formats:
- CSV: Exported from TIA Portal tag table
- SDF: Symbol Definition File from Step7 Classic (binary format)
"""

import csv
import io
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import re

from loguru import logger


@dataclass
class S7Symbol:
    """Represents a symbolic tag from S7 PLC"""
    name: str
    address: str  # S7 address (e.g., DB10.DBW0)
    data_type: str
    comment: Optional[str] = None

    # Parsed components
    db_number: Optional[int] = None
    offset: Optional[int] = None
    bit_offset: Optional[int] = None
    area: Optional[str] = None  # DB, I, Q, M

    # Additional metadata
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    initial_value: Optional[Any] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        # Remove None values for cleaner output
        return {k: v for k, v in data.items() if v is not None}


class S7SymbolImporter:
    """
    Importer for S7 symbolic tags.

    Features:
    - Parse CSV exports from TIA Portal
    - Parse SDF files from Step7 Classic
    - Validate symbol definitions
    - Extract address components (DB, offset, type)
    """

    # Common data type mappings
    TYPE_MAPPINGS = {
        # TIA Portal types
        "Bool": "BOOL",
        "Byte": "BYTE",
        "Word": "WORD",
        "DWord": "DWORD",
        "Int": "INT",
        "DInt": "DINT",
        "Real": "REAL",
        "LReal": "LREAL",
        "String": "STRING",
        "Char": "CHAR",
        "Time": "TIME",
        "Date": "DATE",

        # Step7 Classic types (German)
        "BOOL": "BOOL",
        "BYTE": "BYTE",
        "WORD": "WORD",
        "DWORD": "DWORD",
        "INT": "INT",
        "DINT": "DINT",
        "REAL": "REAL",
        "S5TIME": "TIME",
        "DATE": "DATE",
        "TOD": "TIME_OF_DAY",
        "CHAR": "CHAR",
        "STRING": "STRING"
    }

    def __init__(self):
        """Initialize symbol importer."""
        self._symbols: List[S7Symbol] = []

    def import_from_csv(
        self,
        csv_content: str,
        delimiter: str = ","
    ) -> List[S7Symbol]:
        """
        Import symbols from CSV content.

        Expected CSV format (flexible):
        - Must have columns: Name, Address (or Symbol/Address pair)
        - Optional columns: Type, Comment, Description, Unit, Min, Max

        Common TIA Portal export formats:
        1. Name,Address,Type,Comment
        2. Symbol,Address,Data Type,Comment
        3. Tag Name,Tag Address,Data Type,Description

        Args:
            csv_content: CSV file content as string
            delimiter: CSV delimiter (default: comma)

        Returns:
            List of S7Symbol objects
        """
        self._symbols.clear()

        try:
            # Parse CSV
            reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)

            # Detect column names (case-insensitive)
            if not reader.fieldnames:
                logger.error("CSV has no header row")
                return []

            # Map column names to standard names
            col_map = self._detect_csv_columns(reader.fieldnames)

            if not col_map.get('name') or not col_map.get('address'):
                logger.error(
                    f"CSV must have 'Name' and 'Address' columns. "
                    f"Found: {reader.fieldnames}"
                )
                return []

            logger.info(f"Detected CSV columns: {col_map}")

            # Parse rows
            for row_num, row in enumerate(reader, start=2):
                try:
                    symbol = self._parse_csv_row(row, col_map)
                    if symbol:
                        self._symbols.append(symbol)

                except Exception as e:
                    logger.warning(f"Error parsing row {row_num}: {e}")
                    continue

            logger.info(f"Imported {len(self._symbols)} symbols from CSV")

        except Exception as e:
            logger.error(f"Error importing CSV: {e}")

        return self._symbols

    def _detect_csv_columns(self, fieldnames: List[str]) -> Dict[str, str]:
        """
        Detect column mapping from CSV headers.

        Args:
            fieldnames: CSV column names

        Returns:
            Dictionary mapping standard names to actual column names
        """
        col_map = {}

        # Normalize field names for comparison
        normalized = {name.lower().strip(): name for name in fieldnames}

        # Detect name column
        for variant in ['name', 'symbol', 'tag name', 'tag_name', 'tagname']:
            if variant in normalized:
                col_map['name'] = normalized[variant]
                break

        # Detect address column
        for variant in ['address', 'tag address', 'tag_address', 'addr']:
            if variant in normalized:
                col_map['address'] = normalized[variant]
                break

        # Detect type column
        for variant in ['type', 'data type', 'data_type', 'datatype', 'dtype']:
            if variant in normalized:
                col_map['type'] = normalized[variant]
                break

        # Detect comment/description column
        for variant in ['comment', 'description', 'desc', 'remarks']:
            if variant in normalized:
                col_map['comment'] = normalized[variant]
                break

        # Detect optional columns
        for variant in ['unit', 'units', 'engineering unit']:
            if variant in normalized:
                col_map['unit'] = normalized[variant]
                break

        for variant in ['min', 'minimum', 'min_value']:
            if variant in normalized:
                col_map['min'] = normalized[variant]
                break

        for variant in ['max', 'maximum', 'max_value']:
            if variant in normalized:
                col_map['max'] = normalized[variant]
                break

        return col_map

    def _parse_csv_row(
        self,
        row: Dict[str, str],
        col_map: Dict[str, str]
    ) -> Optional[S7Symbol]:
        """
        Parse a single CSV row into S7Symbol.

        Args:
            row: CSV row as dictionary
            col_map: Column mapping

        Returns:
            S7Symbol object or None if parsing fails
        """
        try:
            # Get required fields
            name = row.get(col_map['name'], '').strip()
            address = row.get(col_map['address'], '').strip()

            if not name or not address:
                return None

            # Get optional fields
            data_type = row.get(col_map.get('type', ''), 'UNKNOWN').strip()
            comment = row.get(col_map.get('comment', ''), '').strip() or None
            unit = row.get(col_map.get('unit', ''), '').strip() or None

            # Parse min/max if present
            min_value = None
            max_value = None

            if col_map.get('min'):
                try:
                    min_value = float(row.get(col_map['min'], ''))
                except (ValueError, TypeError):
                    pass

            if col_map.get('max'):
                try:
                    max_value = float(row.get(col_map['max'], ''))
                except (ValueError, TypeError):
                    pass

            # Normalize data type
            data_type = self.TYPE_MAPPINGS.get(data_type, data_type.upper())

            # Parse address components
            parsed = self._parse_address(address)

            if not parsed:
                logger.warning(f"Could not parse address: {address}")
                return None

            db_number, area, offset, bit_offset = parsed

            return S7Symbol(
                name=name,
                address=address,
                data_type=data_type,
                comment=comment,
                db_number=db_number,
                offset=offset,
                bit_offset=bit_offset,
                area=area,
                unit=unit,
                min_value=min_value,
                max_value=max_value
            )

        except Exception as e:
            logger.error(f"Error parsing CSV row: {e}")
            return None

    def _parse_address(self, address: str) -> Optional[tuple]:
        """
        Parse S7 address string into components.

        Supports formats:
        - DB10.DBX0.0 -> (10, 'DB', 0, 0)
        - DB10.DBW0 -> (10, 'DB', 0, None)
        - I0.0 -> (None, 'I', 0, 0)
        - Q0.0 -> (None, 'Q', 0, 0)
        - M0.0 -> (None, 'M', 0, 0)

        Args:
            address: S7 address string

        Returns:
            Tuple of (db_number, area, offset, bit_offset) or None
        """
        try:
            address = address.upper().strip()

            # DB address
            if address.startswith('DB'):
                # Extract DB number
                match = re.match(r'DB(\d+)\.(.+)', address)
                if not match:
                    return None

                db_number = int(match.group(1))
                rest = match.group(2)

                # Parse offset and type
                if rest.startswith('DBX'):
                    # BOOL: DBX0.0
                    parts = rest[3:].split('.')
                    offset = int(parts[0])
                    bit_offset = int(parts[1]) if len(parts) > 1 else 0
                    return (db_number, 'DB', offset, bit_offset)

                elif rest.startswith('DBB'):
                    # BYTE: DBB0
                    offset = int(rest[3:])
                    return (db_number, 'DB', offset, None)

                elif rest.startswith('DBW') or rest.startswith('DBINT'):
                    # WORD/INT: DBW0
                    if rest.startswith('DBINT'):
                        offset = int(rest[5:])
                    else:
                        offset = int(rest[3:])
                    return (db_number, 'DB', offset, None)

                elif rest.startswith('DBD') or rest.startswith('DBDINT'):
                    # DWORD/DINT: DBD0
                    if rest.startswith('DBDINT'):
                        offset = int(rest[6:])
                    else:
                        offset = int(rest[3:])
                    return (db_number, 'DB', offset, None)

                elif rest.startswith('DBREAL'):
                    # REAL: DBREAL0
                    offset = int(rest[6:])
                    return (db_number, 'DB', offset, None)

            # Input address
            elif address.startswith('I'):
                if '.' in address:
                    # Bit: I0.0
                    parts = address[1:].split('.')
                    offset = int(parts[0])
                    bit_offset = int(parts[1])
                    return (None, 'I', offset, bit_offset)
                elif address[1] in ['B', 'W', 'D']:
                    # IB, IW, ID
                    offset = int(address[2:])
                    return (None, 'I', offset, None)

            # Output address
            elif address.startswith('Q'):
                if '.' in address:
                    parts = address[1:].split('.')
                    offset = int(parts[0])
                    bit_offset = int(parts[1])
                    return (None, 'Q', offset, bit_offset)
                elif address[1] in ['B', 'W', 'D']:
                    offset = int(address[2:])
                    return (None, 'Q', offset, None)

            # Merker address
            elif address.startswith('M'):
                if '.' in address:
                    parts = address[1:].split('.')
                    offset = int(parts[0])
                    bit_offset = int(parts[1])
                    return (None, 'M', offset, bit_offset)
                elif address[1] in ['B', 'W', 'D']:
                    offset = int(address[2:])
                    return (None, 'M', offset, None)

            return None

        except Exception as e:
            logger.debug(f"Error parsing address {address}: {e}")
            return None

    def import_from_sdf(self, sdf_path: str) -> List[S7Symbol]:
        """
        Import symbols from SDF (Symbol Definition File).

        SDF is a binary format used by Step7 Classic.
        This is a placeholder - full implementation requires
        binary format specification.

        Args:
            sdf_path: Path to SDF file

        Returns:
            List of S7Symbol objects
        """
        # TODO: Implement SDF parsing
        # SDF format is proprietary and complex
        # For now, recommend using CSV export from Step7

        logger.warning("SDF import not yet implemented. Please export to CSV from Step7.")
        return []

    def validate_symbols(self, symbols: Optional[List[S7Symbol]] = None) -> Dict:
        """
        Validate symbol definitions.

        Args:
            symbols: List of symbols to validate (uses imported if None)

        Returns:
            Dictionary with validation results
        """
        if symbols is None:
            symbols = self._symbols

        results = {
            "total": len(symbols),
            "valid": 0,
            "invalid": 0,
            "warnings": [],
            "errors": []
        }

        seen_names = set()
        seen_addresses = set()

        for symbol in symbols:
            is_valid = True

            # Check for duplicate names
            if symbol.name in seen_names:
                results["errors"].append(
                    f"Duplicate symbol name: {symbol.name}"
                )
                is_valid = False
            seen_names.add(symbol.name)

            # Check for duplicate addresses
            addr_key = (symbol.db_number, symbol.offset, symbol.bit_offset)
            if addr_key in seen_addresses:
                results["warnings"].append(
                    f"Duplicate address: {symbol.address} (used by multiple symbols)"
                )
            seen_addresses.add(addr_key)

            # Validate data type
            if symbol.data_type == "UNKNOWN":
                results["warnings"].append(
                    f"Unknown data type for {symbol.name}"
                )

            # Validate address components
            if symbol.db_number is None and symbol.area == 'DB':
                results["errors"].append(
                    f"DB symbol {symbol.name} has no DB number"
                )
                is_valid = False

            if symbol.offset is None:
                results["errors"].append(
                    f"Symbol {symbol.name} has no offset"
                )
                is_valid = False

            if is_valid:
                results["valid"] += 1
            else:
                results["invalid"] += 1

        return results

    def get_symbols(self) -> List[S7Symbol]:
        """Get imported symbols."""
        return self._symbols

    def get_symbols_by_db(self, db_number: int) -> List[S7Symbol]:
        """Get symbols for a specific DB."""
        return [s for s in self._symbols if s.db_number == db_number]

    def get_symbols_by_area(self, area: str) -> List[S7Symbol]:
        """Get symbols for a specific memory area (DB, I, Q, M)."""
        return [s for s in self._symbols if s.area == area.upper()]

    def export_to_dict(self) -> Dict:
        """Export symbols to dictionary format."""
        return {
            "symbol_count": len(self._symbols),
            "symbols": [s.to_dict() for s in self._symbols]
        }

    def clear(self) -> None:
        """Clear all imported symbols."""
        self._symbols.clear()


# Example CSV formats for reference
EXAMPLE_CSV_TIA_PORTAL = """
Name,Address,Type,Comment
MotorSpeed,DB10.DBREAL0,Real,Motor speed in RPM
MotorTemp,DB10.DBREAL4,Real,Motor temperature in Celsius
MotorRunning,DB10.DBX8.0,Bool,Motor running status
AlarmLevel,DB10.DBINT10,Int,Alarm level (0-3)
"""

EXAMPLE_CSV_STEP7 = """
Symbol,Tag Address,Data Type,Description
Temperature_1,DB1.DBW0,INT,Temperature sensor 1
Pressure_1,DB1.DBD2,REAL,Pressure sensor 1
Valve_Open,DB1.DBX6.0,BOOL,Valve open command
"""
