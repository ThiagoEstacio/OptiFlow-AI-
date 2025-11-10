"""
Kafka Consumer for Time-Series Data
====================================

Consumes tag data from Kafka 'raw_tags' topic and writes to InfluxDB.

This consumer is part of the event-driven architecture where:
- Simulator/Gateways publish to Kafka
- This consumer reads from Kafka and writes to InfluxDB
- Other consumers can read the same data for different purposes

Benefits:
- Decouples data sources from storage
- Allows horizontal scaling
- Enables multiple consumers for same data
- Built-in retry and backpressure management
"""

import logging
import asyncio
from typing import List, Dict, Any
import json
from datetime import datetime

try:
    from aiokafka import AIOKafkaConsumer
    from aiokafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logging.warning("aiokafka not installed - Kafka consumer disabled")

from app.core.config import settings
from app.services.influxdb import influxdb_service

logger = logging.getLogger(__name__)


class TimeSeriesConsumer:
    """
    Kafka consumer that writes time-series data to InfluxDB

    Features:
    - Consumes from 'raw_tags' topic
    - Batches writes to InfluxDB for efficiency
    - Automatic commit after successful write
    - Graceful error handling
    """

    def __init__(
        self,
        topic: str = 'raw_tags',
        group_id: str = 'timeseries-influxdb-writer',
        batch_size: int = 100
    ):
        self.topic = topic
        self.group_id = group_id
        self.batch_size = batch_size

        self.consumer = None
        self.running = False
        self.enabled = KAFKA_AVAILABLE

        self._messages_processed = 0
        self._batches_written = 0
        self._errors = 0

    async def start(self, max_retries: int = 5, initial_delay: float = 2.0):
        """
        Start Kafka consumer with retry logic

        Args:
            max_retries: Maximum number of connection attempts
            initial_delay: Initial delay before first retry
        """
        if not self.enabled:
            logger.warning("⚠️  Kafka consumer disabled - aiokafka not available")
            return False

        bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')

        for attempt in range(max_retries):
            try:
                logger.info(f"🔌 Kafka consumer connection attempt {attempt + 1}/{max_retries} to {bootstrap_servers}")

                self.consumer = AIOKafkaConsumer(
                    self.topic,
                    bootstrap_servers=bootstrap_servers,
                    group_id=self.group_id,
                    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                    auto_offset_reset='earliest',  # Start from beginning if no offset
                    enable_auto_commit=False,  # Manual commit after successful write
                    max_poll_records=self.batch_size
                )

                await self.consumer.start()
                logger.info(f"✅ Kafka consumer started - Topic: {self.topic}, Group: {self.group_id}")
                return True

            except Exception as e:
                delay = initial_delay * (2 ** attempt)

                if attempt < max_retries - 1:
                    logger.warning(f"⚠️  Kafka consumer connection attempt {attempt + 1}/{max_retries} failed: {e}")
                    logger.info(f"⏳ Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ Failed to start Kafka consumer after {max_retries} attempts: {e}")
                    self.enabled = False
                    return False

    async def stop(self):
        """Stop consumer and cleanup"""
        self.running = False

        if self.consumer:
            try:
                await self.consumer.stop()
                logger.info(f"🛑 Kafka consumer stopped - Processed: {self._messages_processed}, Batches: {self._batches_written}, Errors: {self._errors}")
            except Exception as e:
                logger.error(f"Error stopping Kafka consumer: {e}")

    async def consume_loop(self):
        """
        Main consume loop - reads from Kafka and writes to InfluxDB
        """
        if not self.enabled or not self.consumer:
            logger.error("❌ Cannot start consume loop - consumer not enabled")
            return

        self.running = True
        logger.info("🔄 Starting time-series consumer loop...")

        batch: List[Dict[str, Any]] = []

        try:
            async for msg in self.consumer:
                if not self.running:
                    break

                try:
                    # Extract tag data from message
                    tag_data = msg.value

                    # Add to batch
                    batch.append({
                        'tag_id': tag_data.get('tag_name'),  # Use tag_name as tag_id for now
                        'value': tag_data.get('value'),
                        'timestamp': tag_data.get('timestamp'),
                        'quality': tag_data.get('quality', 'good'),
                        'source': tag_data.get('source', 'unknown')
                    })

                    # Write batch when full
                    if len(batch) >= self.batch_size:
                        await self._write_batch(batch)
                        await self.consumer.commit()
                        batch = []

                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    self._errors += 1
                    continue

            # Write remaining messages in batch
            if batch:
                await self._write_batch(batch)
                await self.consumer.commit()

        except asyncio.CancelledError:
            logger.info("Consumer loop cancelled")
        except Exception as e:
            logger.error(f"❌ Fatal error in consume loop: {e}", exc_info=True)
        finally:
            # Write any remaining messages
            if batch:
                await self._write_batch(batch)

    async def _write_batch(self, batch: List[Dict[str, Any]]):
        """
        Write batch of messages to InfluxDB

        Args:
            batch: List of tag data dictionaries
        """
        try:
            success = influxdb_service.write_batch(batch)

            if success:
                self._messages_processed += len(batch)
                self._batches_written += 1
                logger.info(f"✅ Wrote {len(batch)} points to InfluxDB (total: {self._messages_processed})")
            else:
                logger.error(f"❌ Failed to write batch of {len(batch)} points to InfluxDB")
                self._errors += 1

        except Exception as e:
            logger.error(f"❌ Error writing batch to InfluxDB: {e}")
            self._errors += 1

    def get_stats(self) -> Dict[str, int]:
        """Get consumer statistics"""
        return {
            'messages_processed': self._messages_processed,
            'batches_written': self._batches_written,
            'errors': self._errors
        }


# Global singleton instance
_consumer_instance = None


def get_timeseries_consumer() -> TimeSeriesConsumer:
    """Get global time-series consumer instance"""
    global _consumer_instance
    if _consumer_instance is None:
        _consumer_instance = TimeSeriesConsumer()
    return _consumer_instance


async def start_timeseries_consumer():
    """Start time-series consumer (call from application startup)"""
    consumer = get_timeseries_consumer()

    # Start consumer
    started = await consumer.start()

    if started:
        # Start consume loop in background
        asyncio.create_task(consumer.consume_loop())
        logger.info("🚀 Time-series consumer started in background")
    else:
        logger.warning("⚠️  Time-series consumer not started (Kafka unavailable)")

    return consumer


async def stop_timeseries_consumer():
    """Stop time-series consumer (call from application shutdown)"""
    global _consumer_instance
    if _consumer_instance:
        await _consumer_instance.stop()
        _consumer_instance = None
