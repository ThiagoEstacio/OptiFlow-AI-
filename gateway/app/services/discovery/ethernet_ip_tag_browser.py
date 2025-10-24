"""
EtherNet/IP Tag Browser

Browses and lists all tags available in a Rockwell PLC.
Provides hierarchical tag structure and filtering capabilities.
"""

import asyncio
import json
from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum
import re

from loguru import logger
from pycomm3 import LogixDriver
from pycomm3.tag import Tag


class TagCategory(str, Enum):
    """Tag categories"""
    CONTROLLER = "controller"
    PROGRAM = "program"
    USER_DEFINED = "user_defined"
    SYSTEM = "system"
    IO = "io"


@dataclass
class TagInfo:
    """Detailed information about a tag"""
    tag_name: str
    full_path: str
    data_type: str
    dim: int = 0  # Array dimension (0 = not array)
    dimensions: Optional[List[int]] = None
    value: Optional[Any] = None
    description: Optional[str] = None
    category: Optional[str] = None
    alias: Optional[str] = None
    external_access: Optional[str] = None
    is_array: bool = False
    is_struct: bool = False
    members: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        # Remove None values for cleaner output
        return {k: v for k, v in data.items() if v is not None}


class TagFilter:
    """Filter for tag browsing"""

    def __init__(
        self,
        name_pattern: Optional[str] = None,
        data_types: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        exclude_system: bool = True,
        exclude_io: bool = False,
        include_arrays: bool = True,
        include_structs: bool = True
    ):
        self.name_pattern = name_pattern
        self.data_types = data_types or []
        self.categories = categories or []
        self.exclude_system = exclude_system
        self.exclude_io = exclude_io
        self.include_arrays = include_arrays
        self.include_structs = include_structs

    def matches(self, tag: TagInfo) -> bool:
        """Check if tag matches filter criteria."""
        # Name pattern
        if self.name_pattern:
            if not re.search(self.name_pattern, tag.tag_name, re.IGNORECASE):
                return False

        # Data type
        if self.data_types and tag.data_type not in self.data_types:
            return False

        # Category
        if self.categories and tag.category not in self.categories:
            return False

        # System tags
        if self.exclude_system and tag.category == TagCategory.SYSTEM:
            return False

        # IO tags
        if self.exclude_io and tag.category == TagCategory.IO:
            return False

        # Arrays
        if not self.include_arrays and tag.is_array:
            return False

        # Structs
        if not self.include_structs and tag.is_struct:
            return False

        return True


class EtherNetIPTagBrowser:
    """
    Browser for PLC tags via EtherNet/IP.

    Provides:
    - Complete tag listing
    - Hierarchical tag structure
    - Tag metadata (type, dimensions, description)
    - Filtering capabilities
    - Current value reading
    """

    # System tag prefixes to identify
    SYSTEM_PREFIXES = [
        'Program:',
        'Task:',
        'Module:',
        'Controller',
        'CST',
        'SST',
        'FBD',
        'SFC'
    ]

    def __init__(self, ip_address: str, slot: int = 0):
        """
        Initialize tag browser.

        Args:
            ip_address: PLC IP address
            slot: Slot number
        """
        self.ip_address = ip_address
        self.slot = slot
        self._plc: Optional[LogixDriver] = None
        self._all_tags: List[TagInfo] = []

    def connect(self) -> bool:
        """Connect to PLC."""
        try:
            if self._plc is not None:
                self._plc.close()

            self._plc = LogixDriver(
                self.ip_address,
                slot=self.slot,
                init_tags=True,  # Load tag database
                init_program_tags=True
            )

            self._plc.open()

            if not self._plc.connected:
                logger.error(f"Failed to connect to PLC at {self.ip_address}")
                return False

            logger.info(f"Connected to PLC at {self.ip_address} for tag browsing")
            return True

        except Exception as e:
            logger.error(f"Error connecting to PLC: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from PLC."""
        if self._plc is not None:
            self._plc.close()
            self._plc = None

    def browse_tags(self, include_values: bool = False) -> List[TagInfo]:
        """
        Browse all tags in the PLC.

        Args:
            include_values: Whether to read current values (slower)

        Returns:
            List of TagInfo objects
        """
        if not self._plc or not self._plc.connected:
            if not self.connect():
                return []

        tags = []

        try:
            # Get tags from pycomm3's tag database
            tag_list = self._plc.tags

            logger.info(f"Found {len(tag_list)} tags in PLC")

            for tag_name, tag_info in tag_list.items():
                try:
                    tag_data = self._parse_tag_info(tag_name, tag_info)

                    # Read value if requested
                    if include_values and tag_data:
                        value = self._read_tag_value(tag_name)
                        tag_data.value = value

                    if tag_data:
                        tags.append(tag_data)

                except Exception as e:
                    logger.debug(f"Error parsing tag {tag_name}: {e}")
                    continue

            self._all_tags = tags

        except Exception as e:
            logger.error(f"Error browsing tags: {e}")

        return tags

    def _parse_tag_info(self, tag_name: str, tag_info: Dict) -> Optional[TagInfo]:
        """
        Parse tag information from pycomm3 tag data.

        Args:
            tag_name: Tag name
            tag_info: Tag information dictionary

        Returns:
            TagInfo object or None
        """
        try:
            data_type = tag_info.get('data_type', 'UNKNOWN')
            dim = tag_info.get('dim', 0)
            dimensions = tag_info.get('dimensions', None)

            # Determine category
            category = self._categorize_tag(tag_name)

            # Check if array
            is_array = dim > 0 or (dimensions is not None and len(dimensions) > 0)

            # Check if struct (UDT)
            is_struct = ':' not in data_type and data_type not in [
                'BOOL', 'SINT', 'INT', 'DINT', 'LINT',
                'REAL', 'LREAL', 'STRING'
            ]

            return TagInfo(
                tag_name=tag_name,
                full_path=tag_name,
                data_type=data_type,
                dim=dim,
                dimensions=dimensions,
                category=category,
                is_array=is_array,
                is_struct=is_struct,
                alias=tag_info.get('alias'),
                external_access=tag_info.get('external_access')
            )

        except Exception as e:
            logger.error(f"Error parsing tag info for {tag_name}: {e}")
            return None

    def _categorize_tag(self, tag_name: str) -> str:
        """Categorize a tag based on its name."""
        # Check for program tags
        if tag_name.startswith('Program:'):
            return TagCategory.PROGRAM

        # Check for IO tags
        if tag_name.startswith('Local:') or tag_name.startswith('Remote:'):
            return TagCategory.IO

        # Check for controller tags
        if tag_name.startswith('Controller'):
            return TagCategory.CONTROLLER

        # Check for system tags
        for prefix in self.SYSTEM_PREFIXES:
            if tag_name.startswith(prefix):
                return TagCategory.SYSTEM

        return TagCategory.USER_DEFINED

    def _read_tag_value(self, tag_name: str) -> Optional[Any]:
        """Read current value of a tag."""
        try:
            result = self._plc.read(tag_name)
            if result.error:
                return None
            return result.value
        except:
            return None

    def get_tag_details(self, tag_name: str, read_value: bool = True) -> Optional[TagInfo]:
        """
        Get detailed information about a specific tag.

        Args:
            tag_name: Tag name
            read_value: Whether to read current value

        Returns:
            TagInfo object or None
        """
        if not self._plc or not self._plc.connected:
            if not self.connect():
                return None

        try:
            # Get tag from database
            if tag_name in self._plc.tags:
                tag_info = self._plc.tags[tag_name]
                tag_data = self._parse_tag_info(tag_name, tag_info)

                # Read value
                if read_value and tag_data:
                    tag_data.value = self._read_tag_value(tag_name)

                return tag_data

        except Exception as e:
            logger.error(f"Error getting tag details for {tag_name}: {e}")

        return None

    def filter_tags(
        self,
        tags: Optional[List[TagInfo]] = None,
        tag_filter: Optional[TagFilter] = None
    ) -> List[TagInfo]:
        """
        Filter tags based on criteria.

        Args:
            tags: List of tags to filter (uses cached if None)
            tag_filter: Filter criteria

        Returns:
            Filtered list of tags
        """
        if tags is None:
            tags = self._all_tags

        if tag_filter is None:
            return tags

        return [tag for tag in tags if tag_filter.matches(tag)]

    def get_hierarchical_structure(
        self,
        tags: Optional[List[TagInfo]] = None
    ) -> Dict[str, Any]:
        """
        Build hierarchical structure of tags.

        Args:
            tags: List of tags (uses cached if None)

        Returns:
            Nested dictionary representing tag hierarchy
        """
        if tags is None:
            tags = self._all_tags

        hierarchy = {}

        for tag in tags:
            # Split tag path
            parts = tag.tag_name.split('.')

            # Build hierarchy
            current = hierarchy
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    # Leaf node - store tag info
                    current[part] = tag.to_dict()
                else:
                    # Branch node
                    if part not in current:
                        current[part] = {}
                    current = current[part]

        return hierarchy

    def search_tags(
        self,
        search_term: str,
        tags: Optional[List[TagInfo]] = None,
        case_sensitive: bool = False
    ) -> List[TagInfo]:
        """
        Search for tags by name.

        Args:
            search_term: Search term (supports wildcards)
            tags: List of tags to search (uses cached if None)
            case_sensitive: Whether search is case-sensitive

        Returns:
            List of matching tags
        """
        if tags is None:
            tags = self._all_tags

        # Convert wildcards to regex
        pattern = search_term.replace('*', '.*').replace('?', '.')
        flags = 0 if case_sensitive else re.IGNORECASE

        try:
            regex = re.compile(pattern, flags)
            return [tag for tag in tags if regex.search(tag.tag_name)]
        except re.error:
            # If regex fails, do simple substring match
            if case_sensitive:
                return [tag for tag in tags if search_term in tag.tag_name]
            else:
                search_lower = search_term.lower()
                return [tag for tag in tags if search_lower in tag.tag_name.lower()]

    def export_to_json(
        self,
        filepath: str,
        tags: Optional[List[TagInfo]] = None,
        indent: int = 2
    ) -> bool:
        """
        Export tags to JSON file.

        Args:
            filepath: Output file path
            tags: List of tags to export (uses cached if None)
            indent: JSON indentation

        Returns:
            True if successful
        """
        if tags is None:
            tags = self._all_tags

        try:
            data = {
                "device": {
                    "ip_address": self.ip_address,
                    "slot": self.slot
                },
                "tag_count": len(tags),
                "tags": [tag.to_dict() for tag in tags]
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=indent, default=str)

            logger.info(f"Exported {len(tags)} tags to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error exporting tags to JSON: {e}")
            return False

    def export_to_csv(
        self,
        filepath: str,
        tags: Optional[List[TagInfo]] = None
    ) -> bool:
        """
        Export tags to CSV file.

        Args:
            filepath: Output file path
            tags: List of tags to export (uses cached if None)

        Returns:
            True if successful
        """
        if tags is None:
            tags = self._all_tags

        try:
            import csv

            with open(filepath, 'w', newline='') as f:
                if not tags:
                    return True

                # Get all possible fields
                fieldnames = [
                    'tag_name', 'full_path', 'data_type', 'dim',
                    'category', 'is_array', 'is_struct', 'value', 'description'
                ]

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for tag in tags:
                    row = tag.to_dict()
                    # Only include fields that exist in fieldnames
                    row = {k: v for k, v in row.items() if k in fieldnames}
                    writer.writerow(row)

            logger.info(f"Exported {len(tags)} tags to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error exporting tags to CSV: {e}")
            return False

    async def browse_tags_async(self, include_values: bool = False) -> List[TagInfo]:
        """Async wrapper for browse_tags."""
        return await asyncio.to_thread(self.browse_tags, include_values)

    async def get_tag_details_async(
        self,
        tag_name: str,
        read_value: bool = True
    ) -> Optional[TagInfo]:
        """Async wrapper for get_tag_details."""
        return await asyncio.to_thread(self.get_tag_details, tag_name, read_value)

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
