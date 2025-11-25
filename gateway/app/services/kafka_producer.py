"""
Kafka Producer Service for Gateway
===================================

Publishes tag data to Kafka topic 'raw_tags'.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from aiokafka import AIOKafkaProducer
    from aiokafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logging.warning("aiokafka not installed - Kafka publishing disabled")

logger = logging.getLogger(__name__)


class KafkaProducerService:
    """
    Kafka producer singleton for Gateway

    Publishes tag data to Kafka topic.
    """

    def __init__(
        self,
        bootstrap_servers: str = "kafka-1:9092,kafka-2:9093,kafka-3:9096",
        topic: str = "raw_tags"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer: Optional[AIOKafkaProducer] = None
        self._started = False
        self.enabled = KAFKA_AVAILABLE  # Enable if aiokafka is installed

    async def start(self):
        """Start Kafka producer"""
        if not KAFKA_AVAILABLE:
            logger.warning("⚠️  Kafka not available - messages will be dropped")
            return

        if self._started:
            logger.warning("⚠️  Kafka producer already started")
            return

        try:
            logger.info(f"🚀 Starting Kafka producer: {self.bootstrap_servers}")

            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                compression_type='gzip',  # Changed from lz4 to gzip (built-in)
                linger_ms=100,
                acks=1
            )

            await self.producer.start()
            self._started = True
            logger.info(f"✅ Kafka producer started - Publishing to topic '{self.topic}'")

        except Exception as e:
            logger.error(f"❌ Failed to start Kafka producer: {e}", exc_info=True)
            self._started = False

    async def stop(self):
        """Stop Kafka producer"""
        if self.producer and self._started:
            try:
                logger.info("🛑 Stopping Kafka producer...")
                await self.producer.stop()
                self._started = False
                logger.info("✅ Kafka producer stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping Kafka producer: {e}")

    async def publish(self, messages: List[Dict[str, Any]]) -> bool:
        """
        Publish messages to Kafka

        Args:
            messages: List of tag data dictionaries

        Returns:
            True if published successfully
        """
        if not self._started or not self.producer:
            logger.warning(f"⚠️  Kafka not available - dropping {len(messages)} messages")
            return False

        try:
            # Send all messages
            for msg in messages:
                await self.producer.send(self.topic, value=msg)

            # Flush to ensure delivery
            await self.producer.flush()

            logger.debug(f"✅ Published {len(messages)} messages to Kafka topic '{self.topic}'")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to publish to Kafka: {e}")
            return False

    async def publish_bulk(self, messages: List[Dict[str, Any]]) -> int:
        """
        Publish multiple messages to Kafka (bulk operation)

        Args:
            messages: List of tag data dictionaries

        Returns:
            Number of messages successfully published
        """
        logger.info(f"📤 publish_bulk called with {len(messages)} messages")

        if not self._started or not self.producer:
            logger.warning(f"⚠️  Kafka not available - dropping {len(messages)} messages (started={self._started}, producer={self.producer is not None})")
            return 0

        try:
            # Send all messages
            for msg in messages:
                await self.producer.send(self.topic, value=msg)

            # Flush to ensure delivery
            await self.producer.flush()

            logger.info(f"✅ Published {len(messages)} messages to Kafka topic '{self.topic}'")
            return len(messages)

        except Exception as e:
            logger.error(f"❌ Failed to publish to Kafka: {e}", exc_info=True)
            return 0


# Singleton instance
_kafka_producer: Optional[KafkaProducerService] = None


def get_kafka_producer(
    bootstrap_servers: str = "kafka-1:9092,kafka-2:9093,kafka-3:9096",
    topic: str = "raw_tags"
) -> KafkaProducerService:
    """
    Get or create Kafka producer singleton

    Args:
        bootstrap_servers: Kafka bootstrap servers
        topic: Topic to publish to

    Returns:
        KafkaProducerService instance
    """
    global _kafka_producer

    if _kafka_producer is None:
        _kafka_producer = KafkaProducerService(
            bootstrap_servers=bootstrap_servers,
            topic=topic
        )

    return _kafka_producer
