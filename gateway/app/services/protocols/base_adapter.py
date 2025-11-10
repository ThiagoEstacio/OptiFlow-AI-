"""
Base Protocol Adapter
=====================

Abstract base class for all industrial protocol adapters.

All adapters follow the same pattern:
1. Connect to device/server
2. Read tag values at configured scan rate
3. Publish to Kafka topic 'raw_tags'
4. Handle disconnections and retries gracefully

This ensures consistent behavior across all protocols.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import logging
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class ProtocolConfig:
    """Configuration for protocol adapter"""

    # Basic configuration
    adapter_id: str
    protocol_type: str  # 'opcua', 'modbus', 'mqtt', 'ethernet_ip', 's7'
    enabled: bool = True

    # Connection settings
    host: str = 'localhost'
    port: int = 502
    timeout: float = 5.0
    retry_interval: float = 10.0
    max_retries: int = 5

    # Scan settings
    scan_rate_ms: int = 1000  # How often to read tags
    batch_size: int = 100     # Max tags to publish in one batch

    # Protocol-specific settings (override in subclasses)
    extra_config: Dict[str, Any] = field(default_factory=dict)

    # Tags to monitor
    tags: List[Dict[str, str]] = field(default_factory=list)
    # Format: [{'name': 'tag1', 'address': '40001', 'type': 'float32'}, ...]


@dataclass
class TagData:
    """Standard format for tag data across all protocols"""

    tag_name: str
    value: Any
    quality: str = 'good'  # good, bad, uncertain
    timestamp: Optional[str] = None
    source: Optional[str] = None  # Protocol adapter ID
    address: Optional[str] = None  # Original address (for debugging)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Kafka publishing"""
        return {
            'tag_name': self.tag_name,
            'value': self.value,
            'quality': self.quality,
            'timestamp': self.timestamp or datetime.utcnow().isoformat(),
            'source': self.source,
            'address': self.address
        }


class BaseProtocolAdapter(ABC):
    """
    Abstract base class for industrial protocol adapters

    All protocol adapters must:
    1. Implement connect() - establish connection to device
    2. Implement disconnect() - cleanup connection
    3. Implement read_tags() - read current values from device
    4. Implement health_check() - verify connection is alive

    The base class handles:
    - Kafka publishing
    - Scan loop management
    - Retry logic
    - Error handling
    """

    def __init__(self, config: ProtocolConfig):
        self.config = config
        self.adapter_id = config.adapter_id
        self.protocol_type = config.protocol_type

        # State management
        self.connected = False
        self.running = False
        self._scan_task: Optional[asyncio.Task] = None

        # Statistics
        self._read_count = 0
        self._error_count = 0
        self._last_read_time: Optional[datetime] = None

        # Kafka producer (lazy initialization)
        self.kafka_producer = None
        self._kafka_init_attempted = False

        logger.info(f"🔧 Initialized {self.protocol_type.upper()} adapter: {self.adapter_id}")

    async def _ensure_kafka_producer(self):
        """Initialize Kafka producer if not already initialized"""
        if self.kafka_producer is None and not self._kafka_init_attempted:
            self._kafka_init_attempted = True

            try:
                # Import here to avoid circular dependency
                import sys
                sys.path.insert(0, '/app')  # Ensure backend modules are accessible

                from app.services.kafka_producer import get_kafka_producer

                self.kafka_producer = get_kafka_producer()

                if self.kafka_producer and not self.kafka_producer.producer:
                    await self.kafka_producer.start()

                if self.kafka_producer and self.kafka_producer.enabled:
                    logger.info(f"✅ Kafka producer connected to {self.adapter_id}")
                else:
                    logger.warning(f"⚠️  Kafka producer not available for {self.adapter_id}")
                    self.kafka_producer = None

            except Exception as e:
                logger.warning(f"⚠️  Could not initialize Kafka for {self.adapter_id}: {e}")
                self.kafka_producer = None

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to device/server

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def disconnect(self):
        """Cleanup and close connection"""
        pass

    @abstractmethod
    async def read_tags(self) -> List[TagData]:
        """
        Read all configured tags from device

        Returns:
            List of TagData objects with current values
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if connection is still alive

        Returns:
            True if connection is healthy, False otherwise
        """
        pass

    async def start(self):
        """Start the adapter (connect + start scan loop)"""
        if self.running:
            logger.warning(f"⚠️  {self.adapter_id} already running")
            return

        logger.info(f"🚀 Starting {self.adapter_id} ({self.protocol_type})...")

        # Connect to device
        connected = await self.connect()

        if not connected:
            logger.error(f"❌ Failed to start {self.adapter_id} - connection failed")
            return

        # Start Kafka producer
        await self._ensure_kafka_producer()

        # Start scan loop
        self.running = True
        self._scan_task = asyncio.create_task(self._scan_loop())

        logger.info(f"✅ {self.adapter_id} started successfully")

    async def stop(self):
        """Stop the adapter (stop scan + disconnect)"""
        if not self.running:
            return

        logger.info(f"🛑 Stopping {self.adapter_id}...")

        self.running = False

        # Cancel scan loop
        if self._scan_task:
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass

        # Disconnect from device
        await self.disconnect()

        logger.info(f"✅ {self.adapter_id} stopped - Reads: {self._read_count}, Errors: {self._error_count}")

    async def _scan_loop(self):
        """Main scan loop - read tags and publish to Kafka"""
        scan_interval = self.config.scan_rate_ms / 1000.0  # Convert to seconds

        logger.info(f"🔄 Starting scan loop for {self.adapter_id} (interval: {scan_interval}s)")

        while self.running:
            try:
                # Check connection health
                if not await self.health_check():
                    logger.warning(f"⚠️  {self.adapter_id} connection unhealthy - attempting reconnect...")

                    await self.disconnect()
                    await asyncio.sleep(self.config.retry_interval)

                    if await self.connect():
                        logger.info(f"✅ {self.adapter_id} reconnected successfully")
                    else:
                        logger.error(f"❌ {self.adapter_id} reconnection failed")
                        await asyncio.sleep(self.config.retry_interval)
                        continue

                # Read tags from device
                tags = await self.read_tags()

                if tags:
                    self._read_count += len(tags)
                    self._last_read_time = datetime.utcnow()

                    # Publish to Kafka
                    await self._publish_to_kafka(tags)

                # Wait for next scan
                await asyncio.sleep(scan_interval)

            except asyncio.CancelledError:
                logger.info(f"Scan loop cancelled for {self.adapter_id}")
                break
            except Exception as e:
                self._error_count += 1
                logger.error(f"❌ Error in scan loop for {self.adapter_id}: {e}", exc_info=True)
                await asyncio.sleep(self.config.retry_interval)

    async def _publish_to_kafka(self, tags: List[TagData]):
        """Publish tag data to Kafka"""
        if not self.kafka_producer or not self.kafka_producer.enabled:
            logger.debug(f"⚠️  Kafka not available for {self.adapter_id} - skipping publish")
            return

        try:
            # Convert TagData to dict format
            tag_dicts = [tag.to_dict() for tag in tags]

            # Ensure source is set
            for tag_dict in tag_dicts:
                tag_dict['source'] = self.adapter_id

            # Publish to Kafka in bulk
            success_count = await self.kafka_producer.publish_bulk(tag_dicts)

            if success_count > 0:
                logger.debug(f"📤 {self.adapter_id} published {success_count} tags to Kafka")
            else:
                logger.warning(f"⚠️  {self.adapter_id} failed to publish tags to Kafka")

        except Exception as e:
            logger.error(f"❌ Error publishing to Kafka from {self.adapter_id}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics"""
        return {
            'adapter_id': self.adapter_id,
            'protocol_type': self.protocol_type,
            'connected': self.connected,
            'running': self.running,
            'read_count': self._read_count,
            'error_count': self._error_count,
            'last_read_time': self._last_read_time.isoformat() if self._last_read_time else None
        }
