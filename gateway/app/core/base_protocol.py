"""
Base protocol handler class
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio


@dataclass
class TagValue:
    """Data class for tag values"""
    tag_id: str
    tag_name: str
    value: Any
    quality: str  # "good", "bad", "uncertain"
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tag_id": self.tag_id,
            "tag_name": self.tag_name,
            "value": self.value,
            "quality": self.quality,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class DeviceStatus:
    """Device connection status"""
    connected: bool
    last_success: Optional[datetime]
    last_error: Optional[str]
    error_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "connected": self.connected,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_error": self.last_error,
            "error_count": self.error_count
        }


class BaseProtocolHandler(ABC):
    """
    Base class for all protocol handlers
    """

    def __init__(self, device_id: str, config: Dict[str, Any]):
        """
        Initialize protocol handler

        Args:
            device_id: Unique device identifier
            config: Device configuration dictionary
        """
        self.device_id = device_id
        self.config = config
        self.status = DeviceStatus(
            connected=False,
            last_success=None,
            last_error=None,
            error_count=0
        )
        self._lock = asyncio.Lock()

    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to device

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from device

        Returns:
            True if disconnection successful
        """
        pass

    @abstractmethod
    async def read_tag(self, tag_address: str) -> Optional[TagValue]:
        """
        Read single tag

        Args:
            tag_address: Tag address in protocol-specific format

        Returns:
            TagValue or None if error
        """
        pass

    @abstractmethod
    async def read_tags(self, tag_addresses: List[str]) -> List[TagValue]:
        """
        Read multiple tags

        Args:
            tag_addresses: List of tag addresses

        Returns:
            List of TagValue objects
        """
        pass

    @abstractmethod
    async def write_tag(self, tag_address: str, value: Any) -> bool:
        """
        Write single tag

        Args:
            tag_address: Tag address
            value: Value to write

        Returns:
            True if write successful
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check device health

        Returns:
            True if device is healthy
        """
        pass

    def update_status(self, connected: bool, error: Optional[str] = None):
        """Update device status"""
        self.status.connected = connected
        if connected:
            self.status.last_success = datetime.now()
            self.status.error_count = 0
        else:
            self.status.error_count += 1
            if error:
                self.status.last_error = error

    def get_status(self) -> DeviceStatus:
        """Get current device status"""
        return self.status

    @property
    def is_connected(self) -> bool:
        """Check if device is connected"""
        return self.status.connected
