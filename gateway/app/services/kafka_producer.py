"""
Kafka Producer Service for Gateway
===================================

Publishes tag data to Kafka topic 'raw_tags'.

=== SPRINT 1: Data Quality Validation ===
Data is now validated and annotated with quality information
before being published to Kafka. This is the first line of
defense for data quality in the OptiFlow pipeline.
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

# Import metrics
try:
    from app.services.gateway_metrics import get_gateway_metrics
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

# === SPRINT 1: Data Quality Validation ===
try:
    from app.services.data_quality import get_data_quality_validator, validate_data_quality
    DATA_QUALITY_AVAILABLE = True
except ImportError:
    DATA_QUALITY_AVAILABLE = False
    logging.warning("Data quality validation not available")

# === SPRINT 1: Communication Monitor (CORR-003) ===
try:
    from app.services.communication_monitor import get_communication_monitor, annotate_data_point
    COMM_MONITOR_AVAILABLE = True
except ImportError:
    COMM_MONITOR_AVAILABLE = False
    logging.warning("Communication monitor not available")

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

            # Update metrics - Kafka is our backend
            if METRICS_AVAILABLE:
                metrics = get_gateway_metrics()
                metrics.set_backend_status(True)
                metrics.set_buffer_capacity(10000)  # Default capacity

        except Exception as e:
            logger.error(f"❌ Failed to start Kafka producer: {e}", exc_info=True)
            self._started = False

            # Update metrics on failure
            if METRICS_AVAILABLE:
                metrics = get_gateway_metrics()
                metrics.set_backend_status(False)

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

    async def publish_bulk(self, messages: List[Dict[str, Any]], validate_quality: bool = True) -> int:
        """
        Publish multiple messages to Kafka (bulk operation)

        === SPRINT 1: Data Quality Validation ===
        Messages are now validated and annotated with quality info
        before publishing to Kafka. Quality levels:
        - GOOD: Value passes all checks
        - UNCERTAIN: Suspicious but may be valid
        - BAD: Failed critical checks

        Args:
            messages: List of tag data dictionaries
            validate_quality: Whether to run quality validation (default True)

        Returns:
            Number of messages successfully published
        """
        logger.info(f"📤 publish_bulk called with {len(messages)} messages")

        if not self._started or not self.producer:
            logger.warning(f"⚠️  Kafka not available - dropping {len(messages)} messages (started={self._started}, producer={self.producer is not None})")
            return 0

        import time
        start_time = time.time()

        try:
            # === SPRINT 1: Communication monitoring (CORR-003) ===
            # Annotate each message with communication status to distinguish
            # between real zero values and communication loss
            if COMM_MONITOR_AVAILABLE:
                comm_annotated = []
                for msg in messages:
                    tag_id = msg.get("tag_id") or msg.get("tag_name") or msg.get("name")
                    adapter_id = msg.get("adapter_id") or msg.get("source") or "unknown"
                    value = msg.get("value")
                    quality = msg.get("quality", "Good")

                    # Get communication annotations
                    comm_info = annotate_data_point(
                        tag_id=tag_id,
                        adapter_id=adapter_id,
                        value=value,
                        quality=quality
                    )

                    # Merge communication info into message
                    annotated_msg = {**msg, **comm_info}
                    comm_annotated.append(annotated_msg)

                messages = comm_annotated
                logger.debug(f"📡 Communication annotated {len(messages)} messages")

            # === SPRINT 1: Validate data quality ===
            if validate_quality and DATA_QUALITY_AVAILABLE:
                validated_messages = validate_data_quality(messages)
                logger.debug(f"📊 Quality validated {len(validated_messages)} messages")
            else:
                # Add default quality annotation if validation not available
                validated_messages = [
                    {**msg, "quality": "good", "quality_issues": []}
                    for msg in messages
                ]

            # Track buffer before sending
            if METRICS_AVAILABLE:
                metrics = get_gateway_metrics()
                metrics.set_buffer_size(len(validated_messages))
                metrics.track_buffer_write()

            # Send all validated messages
            for msg in validated_messages:
                await self.producer.send(self.topic, value=msg)

            # Flush to ensure delivery
            await self.producer.flush()

            duration = time.time() - start_time

            # Update metrics after successful send
            if METRICS_AVAILABLE:
                metrics = get_gateway_metrics()
                metrics.set_buffer_size(0)  # Buffer cleared
                metrics.track_buffer_read()
                metrics.track_data_sent(len(validated_messages))
                metrics.track_backend_request("POST", "/raw_tags", 200, duration)

            # Log quality summary
            good_count = sum(1 for m in validated_messages if m.get("quality") == "good")
            uncertain_count = sum(1 for m in validated_messages if m.get("quality") == "uncertain")
            bad_count = sum(1 for m in validated_messages if m.get("quality") == "bad")

            quality_summary = f"(quality: ✅{good_count}"
            if uncertain_count > 0:
                quality_summary += f" ⚠️{uncertain_count}"
            if bad_count > 0:
                quality_summary += f" ❌{bad_count}"
            quality_summary += ")"

            logger.info(f"✅ Published {len(validated_messages)} messages to Kafka topic '{self.topic}' {quality_summary}")
            return len(messages)

        except Exception as e:
            logger.error(f"❌ Failed to publish to Kafka: {e}", exc_info=True)

            duration = time.time() - start_time

            # Track failure in metrics
            if METRICS_AVAILABLE:
                metrics = get_gateway_metrics()
                metrics.track_data_failed("kafka_error")
                metrics.track_backend_request("POST", "/raw_tags", 500, duration)

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
