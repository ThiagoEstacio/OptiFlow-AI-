"""
Base Gateway Abstract Class

Defines the interface and common functionality for all industrial gateways.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
import asyncio
import logging
from collections import deque

logger = logging.getLogger(__name__)


class GatewayStatus(str, Enum):
    """Gateway connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    BUFFERING = "buffering"


class DataPoint:
    """Represents a single data point read from a gateway"""
    def __init__(
        self,
        tag_name: str,
        value: Any,
        quality: str = "good",
        timestamp: Optional[datetime] = None
    ):
        self.tag_name = tag_name
        self.value = value
        self.quality = quality
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict:
        return {
            "tag_name": self.tag_name,
            "value": self.value,
            "quality": self.quality,
            "timestamp": self.timestamp.isoformat()
        }


class BaseGateway(ABC):
    """
    Abstract base class for all industrial protocol gateways.

    Provides:
    - Connection management with auto-reconnect
    - Offline data buffering
    - Health monitoring
    - Error handling and logging
    """

    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        max_buffer_size: int = 10000
    ):
        self.name = name
        self.config = config
        self.status = GatewayStatus.DISCONNECTED
        self.max_buffer_size = max_buffer_size

        # Offline buffer for data when connection is lost
        self.buffer: deque[DataPoint] = deque(maxlen=max_buffer_size)

        # Health metrics
        self.connection_attempts = 0
        self.successful_reads = 0
        self.failed_reads = 0
        self.last_error: Optional[str] = None
        self.last_successful_read: Optional[datetime] = None
        self.connected_since: Optional[datetime] = None

        # Retry configuration
        self.max_retries = config.get('max_retries', 5)
        self.base_retry_delay = config.get('base_retry_delay', 5)  # seconds

        # Background tasks
        self._polling_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None

        logger.info(f"Initialized {self.__class__.__name__}: {name}")

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the industrial device.

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the industrial device."""
        pass

    @abstractmethod
    async def read_tag(self, tag_config: Dict[str, Any]) -> Optional[DataPoint]:
        """
        Read a single tag from the device.

        Args:
            tag_config: Tag configuration (address, type, etc.)

        Returns:
            DataPoint if successful, None if error
        """
        pass

    @abstractmethod
    async def read_multiple_tags(self, tag_configs: List[Dict[str, Any]]) -> List[DataPoint]:
        """
        Read multiple tags in a single request (if protocol supports it).

        Args:
            tag_configs: List of tag configurations

        Returns:
            List of DataPoints
        """
        pass

    async def connect_with_retry(self) -> bool:
        """
        Attempt connection with exponential backoff retry logic.

        Returns:
            bool: True if connection successful
        """
        retry_count = 0
        self.status = GatewayStatus.CONNECTING

        while retry_count < self.max_retries:
            try:
                self.connection_attempts += 1
                logger.info(f"{self.name}: Connection attempt {retry_count + 1}/{self.max_retries}")

                success = await self.connect()

                if success:
                    self.status = GatewayStatus.CONNECTED
                    self.connected_since = datetime.utcnow()
                    logger.info(f"{self.name}: Connected successfully")

                    # Flush buffered data
                    await self._flush_buffer()
                    return True

            except Exception as e:
                self.last_error = str(e)
                logger.error(f"{self.name}: Connection attempt failed: {e}")

            retry_count += 1
            if retry_count < self.max_retries:
                delay = self.base_retry_delay * (2 ** (retry_count - 1))  # Exponential backoff
                logger.info(f"{self.name}: Retrying in {delay} seconds...")
                await asyncio.sleep(delay)

        self.status = GatewayStatus.ERROR
        logger.error(f"{self.name}: Failed to connect after {self.max_retries} attempts")
        return False

    async def _flush_buffer(self) -> None:
        """Send all buffered data points after reconnection."""
        if not self.buffer:
            return

        logger.info(f"{self.name}: Flushing {len(self.buffer)} buffered data points")

        # TODO: Implement actual data storage logic
        # For now, just log the count
        flushed_count = len(self.buffer)
        self.buffer.clear()

        logger.info(f"{self.name}: Flushed {flushed_count} data points")

    def add_to_buffer(self, data_point: DataPoint) -> None:
        """
        Add data point to offline buffer when connection is lost.

        Args:
            data_point: Data point to buffer
        """
        if len(self.buffer) >= self.max_buffer_size:
            logger.warning(f"{self.name}: Buffer full, oldest data will be discarded")

        self.buffer.append(data_point)
        self.status = GatewayStatus.BUFFERING

    async def start_polling(self, interval_ms: int = 1000) -> None:
        """
        Start polling loop to continuously read tags.

        Args:
            interval_ms: Polling interval in milliseconds
        """
        if self._polling_task and not self._polling_task.done():
            logger.warning(f"{self.name}: Polling already running")
            return

        self._polling_task = asyncio.create_task(self._polling_loop(interval_ms))
        logger.info(f"{self.name}: Started polling with {interval_ms}ms interval")

    async def stop_polling(self) -> None:
        """Stop the polling loop."""
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
            logger.info(f"{self.name}: Stopped polling")

    async def _polling_loop(self, interval_ms: int) -> None:
        """
        Internal polling loop.

        Args:
            interval_ms: Polling interval in milliseconds
        """
        interval_sec = interval_ms / 1000.0
        tag_configs = self.config.get('tags', [])

        while True:
            try:
                if self.status != GatewayStatus.CONNECTED:
                    # Attempt reconnection
                    logger.info(f"{self.name}: Not connected, attempting reconnection...")
                    await self.connect_with_retry()

                if self.status == GatewayStatus.CONNECTED:
                    # Read all configured tags
                    data_points = await self.read_multiple_tags(tag_configs)

                    if data_points:
                        self.successful_reads += 1
                        self.last_successful_read = datetime.utcnow()

                        # TODO: Store data points in database
                        # For now, just log
                        logger.debug(f"{self.name}: Read {len(data_points)} data points")
                    else:
                        self.failed_reads += 1

            except Exception as e:
                self.failed_reads += 1
                self.last_error = str(e)
                logger.error(f"{self.name}: Polling error: {e}")
                self.status = GatewayStatus.ERROR

            await asyncio.sleep(interval_sec)

    def get_health_metrics(self) -> Dict[str, Any]:
        """
        Get gateway health metrics.

        Returns:
            Dictionary with health metrics
        """
        uptime_seconds = None
        if self.connected_since:
            uptime_seconds = (datetime.utcnow() - self.connected_since).total_seconds()

        success_rate = 0.0
        total_reads = self.successful_reads + self.failed_reads
        if total_reads > 0:
            success_rate = (self.successful_reads / total_reads) * 100

        return {
            "name": self.name,
            "status": self.status.value,
            "connection_attempts": self.connection_attempts,
            "successful_reads": self.successful_reads,
            "failed_reads": self.failed_reads,
            "success_rate": round(success_rate, 2),
            "buffer_size": len(self.buffer),
            "max_buffer_size": self.max_buffer_size,
            "last_error": self.last_error,
            "last_successful_read": self.last_successful_read.isoformat() if self.last_successful_read else None,
            "connected_since": self.connected_since.isoformat() if self.connected_since else None,
            "uptime_seconds": round(uptime_seconds, 2) if uptime_seconds else None,
        }

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect_with_retry()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_polling()
        await self.disconnect()
