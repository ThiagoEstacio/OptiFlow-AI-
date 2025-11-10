"""
Kafka Producer Service for Real-Time Tag Streaming

This service publishes tag updates to Kafka topics for real-time consumption
by frontend clients and other services.
"""
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

try:
    from aiokafka import AIOKafkaProducer
    from aiokafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logging.warning("aiokafka not installed - Kafka streaming disabled")

from app.core.config import settings

logger = logging.getLogger(__name__)


class KafkaTagProducer:
    """
    Kafka producer for publishing tag updates in real-time

    Features:
    - Automatic batching for efficiency
    - LZ4 compression to reduce network bandwidth
    - Async/await for non-blocking operations
    - Graceful degradation if Kafka unavailable
    """

    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.enabled = KAFKA_AVAILABLE
        self.topic = 'raw_tags'
        self._start_task: Optional[asyncio.Task] = None

    async def start(self, max_retries: int = 5, initial_delay: float = 2.0):
        """
        Initialize and start Kafka producer with retry logic

        Args:
            max_retries: Maximum number of connection attempts (default: 5)
            initial_delay: Initial delay in seconds before first retry (default: 2.0)
        """
        if not self.enabled:
            logger.warning("⚠️  Kafka producer disabled - aiokafka not available")
            return

        bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')

        for attempt in range(max_retries):
            try:
                logger.info(f"🔌 Kafka connection attempt {attempt + 1}/{max_retries} to {bootstrap_servers}")

                self.producer = AIOKafkaProducer(
                    bootstrap_servers=bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                    compression_type='lz4',  # Fast compression
                    linger_ms=10,  # Wait up to 10ms to batch messages
                    max_batch_size=16384,  # 16KB batch size (changed parameter name in v0.10.0)
                    acks=1,  # Wait for leader acknowledgment only (balance between speed and reliability)
                    max_request_size=1048576,  # 1MB max request size
                )

                # Start producer in background
                await self.producer.start()
                logger.info(f"✅ Kafka producer started successfully - Topic: {self.topic}")
                return  # Success! Exit method

            except Exception as e:
                # Calculate exponential backoff delay
                delay = initial_delay * (2 ** attempt)

                if attempt < max_retries - 1:
                    logger.warning(f"⚠️  Kafka connection attempt {attempt + 1}/{max_retries} failed: {e}")
                    logger.info(f"⏳ Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ Failed to start Kafka producer after {max_retries} attempts: {e}")
                    self.enabled = False

    async def stop(self):
        """Cleanup and stop producer"""
        if self.producer:
            try:
                await self.producer.stop()
                logger.info("🛑 Kafka producer stopped")
            except Exception as e:
                logger.error(f"Error stopping Kafka producer: {e}")

    async def publish_tag(self, tag_data: Dict[str, Any]) -> bool:
        """
        Publish single tag update to Kafka

        Args:
            tag_data: Dictionary with tag information
                - tag_id: Unique identifier
                - name: Tag name
                - value: Current value
                - quality: Data quality indicator
                - timestamp: ISO format timestamp
                - source: Data source (e.g., 'simulator', 'opcua')

        Returns:
            True if published successfully, False otherwise
        """
        if not self.enabled or not self.producer:
            return False

        try:
            # Ensure timestamp is present
            if 'timestamp' not in tag_data:
                tag_data['timestamp'] = datetime.utcnow().isoformat()

            # Send to Kafka (fire and forget for performance)
            await self.producer.send(
                topic=self.topic,
                value=tag_data,
                key=str(tag_data.get('tag_id', '')).encode('utf-8')  # Partition by tag_id
            )

            return True

        except KafkaError as e:
            logger.error(f"Kafka error publishing tag {tag_data.get('tag_id')}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing tag: {e}")
            return False

    async def publish_bulk(self, tags: List[Dict[str, Any]]) -> int:
        """
        Publish multiple tags efficiently

        Args:
            tags: List of tag dictionaries

        Returns:
            Number of tags successfully published
        """
        if not self.enabled or not self.producer:
            logger.warning(f"⚠️  Cannot publish {len(tags)} tags - producer not enabled")
            return 0

        success_count = 0

        try:
            logger.info(f"📨 Starting to publish {len(tags)} tags to Kafka...")

            # Send all tags asynchronously
            for tag in tags:
                if await self.publish_tag(tag):
                    success_count += 1

            # Ensure all pending messages are sent
            await self.producer.flush()

            logger.info(f"✅ Published {success_count}/{len(tags)} tags to Kafka successfully")

        except Exception as e:
            logger.error(f"❌ Error in bulk publish: {e}", exc_info=True)

        return success_count

    async def publish_simulator_state(self, simulator_data: Dict[str, Any]) -> bool:
        """
        Publish complete simulator state to Kafka

        This is useful for frontend to get full state updates periodically
        """
        if not self.enabled or not self.producer:
            return False

        try:
            await self.producer.send(
                topic='simulator_state',
                value={
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': simulator_data
                },
                key=b'simulator'
            )
            return True
        except Exception as e:
            logger.error(f"Error publishing simulator state: {e}")
            return False


# Global singleton instance
_kafka_producer: Optional[KafkaTagProducer] = None


def get_kafka_producer() -> KafkaTagProducer:
    """Get global Kafka producer instance"""
    global _kafka_producer
    if _kafka_producer is None:
        _kafka_producer = KafkaTagProducer()
    return _kafka_producer


async def init_kafka_producer():
    """Initialize Kafka producer on application startup"""
    producer = get_kafka_producer()
    await producer.start()
    return producer


async def cleanup_kafka_producer():
    """Cleanup Kafka producer on application shutdown"""
    global _kafka_producer
    if _kafka_producer:
        await _kafka_producer.stop()
        _kafka_producer = None
