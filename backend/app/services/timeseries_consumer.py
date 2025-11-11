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
import time
from typing import List, Dict, Any
import json
from datetime import datetime

from prometheus_client import Counter, Gauge, Histogram

try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
    from aiokafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logging.warning("aiokafka not installed - Kafka consumer disabled")

from app.core.config import settings
from app.services.influxdb import influxdb_service

# Redis for deduplication
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("redis not installed - using in-memory deduplication")

logger = logging.getLogger(__name__)

# Prometheus Metrics
consumer_messages_consumed_total = Counter(
    'consumer_messages_consumed_total',
    'Total number of messages consumed from Kafka'
)

consumer_messages_written_total = Counter(
    'consumer_messages_written_total',
    'Total number of messages successfully written to InfluxDB',
    ['status']  # success, failed
)

consumer_batch_size = Gauge(
    'consumer_batch_size_current',
    'Current adaptive batch size'
)

consumer_write_latency_seconds = Histogram(
    'consumer_write_latency_seconds',
    'Latency of writing batches to InfluxDB',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

consumer_dedup_hits_total = Counter(
    'consumer_dedup_hits_total',
    'Total number of duplicate messages detected'
)

consumer_dlq_messages_total = Counter(
    'consumer_dlq_messages_total',
    'Total number of messages sent to DLQ',
    ['reason']  # write_failed, processing_error
)


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
        topic: str = None,
        group_id: str = None,
        min_batch_size: int = None,
        max_batch_size: int = None,
        batch_timeout_s: float = None
    ):
        # Load from settings if not provided
        self.topic = topic or settings.CONSUMER_TOPIC
        self.group_id = group_id or settings.CONSUMER_GROUP_ID
        self.min_batch_size = min_batch_size or settings.CONSUMER_MIN_BATCH_SIZE
        self.max_batch_size = max_batch_size or settings.CONSUMER_MAX_BATCH_SIZE
        self.batch_timeout_s = batch_timeout_s or settings.CONSUMER_BATCH_TIMEOUT_S
        self.current_batch_size = self.min_batch_size

        self.consumer = None
        self.dlq_producer = None
        self.running = False
        self.enabled = KAFKA_AVAILABLE and settings.CONSUMER_ENABLED

        self._messages_processed = 0
        self._batches_written = 0
        self._errors = 0

        # Deduplication cache (Redis preferred, fallback to in-memory)
        self._redis_client = None
        self._use_redis = REDIS_AVAILABLE
        self._processed_message_ids = set()  # Fallback in-memory cache
        self._message_id_cache_size = settings.CONSUMER_DEDUP_CACHE_SIZE
        self._redis_key = "consumer:dedup:message_ids"
        self._redis_ttl = 3600  # 1 hour TTL for dedup entries

        # Performance metrics
        self._write_latencies_ms = []

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
                    max_poll_records=self.current_batch_size
                )

                await self.consumer.start()
                # DLQ producer (optional) for failed messages
                self.dlq_producer = AIOKafkaProducer(
                    bootstrap_servers=bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
                )
                await self.dlq_producer.start()
                
                # Initialize Redis connection for deduplication
                if self._use_redis:
                    try:
                        self._redis_client = await aioredis.from_url(
                            settings.REDIS_URL,
                            encoding="utf-8",
                            decode_responses=True
                        )
                        await self._redis_client.ping()
                        logger.info("✅ Redis connected for deduplication cache")
                    except Exception as e:
                        logger.warning(f"⚠️  Redis connection failed: {e}, using in-memory dedup")
                        self._use_redis = False
                        self._redis_client = None

                logger.info(f"✅ Kafka consumer started - Topic: {self.topic}, Group: {self.group_id}, DLQ: {settings.KAFKA_DLQ_TOPIC}, batch: {self.min_batch_size}-{self.max_batch_size}, dedup: {'Redis' if self._use_redis else 'in-memory'}")
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
        
        # Close Redis connection
        if self._redis_client:
            try:
                await self._redis_client.close()
                logger.info("✅ Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis: {e}")

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
        batch_start = time.time()

        try:
            async for msg in self.consumer:
                if not self.running:
                    break

                try:
                    tag_data = msg.value
                    
                    # Prometheus metric
                    consumer_messages_consumed_total.inc()

                    # Deduplicate by message_id if present
                    message_id = tag_data.get('message_id')
                    if message_id:
                        is_duplicate = await self._is_duplicate(message_id)
                        if is_duplicate:
                            logger.debug(f"⏭️  Skipping duplicate message {message_id}")
                            consumer_dedup_hits_total.inc()
                            continue

                    # Normalize fields
                    entry = {
                        'tag_id': tag_data.get('tag_id') or tag_data.get('tag_name'),
                        'tag_name': tag_data.get('name') or tag_data.get('tag_name'),
                        'value': tag_data.get('value'),
                        'timestamp': tag_data.get('timestamp'),
                        'quality': tag_data.get('quality', 'good'),
                        'source': tag_data.get('source', 'unknown'),
                        'message_id': message_id
                    }

                    batch.append(entry)

                    # Record processed id (Redis or in-memory)
                    if message_id:
                        await self._mark_as_processed(message_id)

                    # Determine if we should flush
                    batch_age = time.time() - batch_start
                    should_flush = (
                        len(batch) >= self.current_batch_size or
                        (len(batch) >= self.min_batch_size and batch_age >= self.batch_timeout_s)
                    )

                    if should_flush:
                        ok = await self._write_batch(batch)
                        if ok:
                            await self.consumer.commit()
                            consumer_messages_written_total.labels(status='success').inc(len(batch))
                            batch = []
                            batch_start = time.time()
                            self._adjust_batch_size(success=True)
                        else:
                            # write failed -> send to DLQ and do not commit offsets
                            await self._send_to_dlq(batch, reason="influx_write_failed")
                            consumer_messages_written_total.labels(status='failed').inc(len(batch))
                            self._errors += len(batch)
                            batch = []
                            batch_start = time.time()
                            self._adjust_batch_size(success=False)

                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    self._errors += 1
                    # Try to send problematic message to DLQ
                    try:
                        await self._send_to_dlq([msg.value], reason=str(e))
                    except Exception:
                        pass
                    continue

            # Flush remaining
            if batch:
                ok = await self._write_batch(batch)
                if ok:
                    await self.consumer.commit()

        except asyncio.CancelledError:
            logger.info("Consumer loop cancelled")
        except Exception as e:
            logger.error(f"❌ Fatal error in consume loop: {e}", exc_info=True)
        finally:
            if batch:
                await self._write_batch(batch)

    async def _write_batch(self, batch: List[Dict[str, Any]]):
        """
        Write batch of messages to InfluxDB

        Args:
            batch: List of tag data dictionaries
        """
        try:
            start = time.time()
            success = influxdb_service.write_batch(batch)
            latency_ms = (time.time() - start) * 1000
            
            # Prometheus metrics
            consumer_write_latency_seconds.observe(latency_ms / 1000.0)
            
            # record latency
            self._write_latencies_ms.append(latency_ms)
            if len(self._write_latencies_ms) > 1000:
                self._write_latencies_ms = self._write_latencies_ms[-1000:]

            if success:
                self._messages_processed += len(batch)
                self._batches_written += 1
                logger.info(f"✅ Wrote {len(batch)} points to InfluxDB (total: {self._messages_processed}) - {latency_ms:.1f}ms")
                return True
            else:
                logger.error(f"❌ Failed to write batch of {len(batch)} points to InfluxDB")
                self._errors += 1
                return False

        except Exception as e:
            logger.error(f"❌ Error writing batch to InfluxDB: {e}")
            self._errors += 1
            return False

    async def _send_to_dlq(self, batch: List[Dict[str, Any]], reason: str = ""):
        """Send failed batch to Dead Letter Queue"""
        if not self.dlq_producer:
            logger.warning("⚠️  DLQ producer not available, dropping batch")
            return

        try:
            for msg in batch:
                payload = {
                    'original': msg,
                    'reason': reason,
                    'timestamp': datetime.utcnow().isoformat()
                }
                await self.dlq_producer.send_and_wait(topic=settings.KAFKA_DLQ_TOPIC, value=payload)
            
            # Prometheus metrics
            consumer_dlq_messages_total.labels(reason=reason).inc(len(batch))
            logger.info(f"📥 Sent {len(batch)} messages to DLQ ({settings.KAFKA_DLQ_TOPIC})")
        except Exception as e:
            logger.error(f"❌ Failed to send to DLQ: {e}")

    def _adjust_batch_size(self, success: bool):
        """Adjust current_batch_size based on recent latencies and success/failure"""
        if not self._write_latencies_ms:
            return
        
        avg = sum(self._write_latencies_ms[-10:]) / min(len(self._write_latencies_ms), 10)
        
        # If writes are fast, slowly increase batch size
        if avg < 200 and success:
            new_size = min(int(self.current_batch_size * 1.1), self.max_batch_size)
            if new_size != self.current_batch_size:
                logger.info(f"🔺 Increasing batch size {self.current_batch_size} -> {new_size} (avg {avg:.1f}ms)")
                self.current_batch_size = new_size
        else:
            new_size = max(int(self.current_batch_size * 0.8), self.min_batch_size)
            if new_size != self.current_batch_size:
                logger.info(f"🔻 Decreasing batch size {self.current_batch_size} -> {new_size} (avg {avg:.1f}ms)")
                self.current_batch_size = new_size
        
        # Update Prometheus metric
        consumer_batch_size.set(self.current_batch_size)
    
    async def _is_duplicate(self, message_id: str) -> bool:
        """Check if message_id has been processed (Redis or in-memory)"""
        try:
            if self._use_redis and self._redis_client:
                # Use Redis SET with SISMEMBER
                exists = await self._redis_client.sismember(self._redis_key, message_id)
                return bool(exists)
            else:
                # Fallback to in-memory set
                return message_id in self._processed_message_ids
        except Exception as e:
            logger.error(f"Error checking duplicate: {e}, using in-memory fallback")
            return message_id in self._processed_message_ids
    
    async def _mark_as_processed(self, message_id: str):
        """Mark message_id as processed (Redis or in-memory)"""
        try:
            if self._use_redis and self._redis_client:
                # Use Redis SET with TTL
                await self._redis_client.sadd(self._redis_key, message_id)
                await self._redis_client.expire(self._redis_key, self._redis_ttl)
            else:
                # Fallback to in-memory set with naive eviction
                self._processed_message_ids.add(message_id)
                if len(self._processed_message_ids) > self._message_id_cache_size:
                    to_remove = len(self._processed_message_ids) // 2
                    for _ in range(to_remove):
                        self._processed_message_ids.pop()
        except Exception as e:
            logger.error(f"Error marking as processed: {e}, using in-memory fallback")
            self._processed_message_ids.add(message_id)

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


def get_consumer_status() -> Dict[str, Any]:
    """Get current consumer status for health checks"""
    global _consumer_instance
    if _consumer_instance is None:
        return {
            "running": False,
            "enabled": False,
            "messages_processed": 0,
            "errors": 0,
            "current_batch_size": 0
        }
    
    stats = _consumer_instance.get_stats()
    return {
        "running": _consumer_instance.running,
        "enabled": _consumer_instance.enabled,
        "messages_processed": stats.get("messages_processed", 0),
        "batches_written": stats.get("batches_written", 0),
        "errors": stats.get("errors", 0),
        "current_batch_size": _consumer_instance.current_batch_size,
        "min_batch_size": _consumer_instance.min_batch_size,
        "max_batch_size": _consumer_instance.max_batch_size
    }

