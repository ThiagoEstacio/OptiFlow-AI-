"""
Persistent Buffer for Circuit Breaker Recovery
===============================================

Provides Redis-backed buffering for data points when InfluxDB is unavailable.
When the circuit breaker opens (InfluxDB down), data is stored in Redis.
When the circuit closes (InfluxDB recovered), data is automatically flushed.

This prevents data loss during InfluxDB outages instead of just sending to DLQ.

Architecture:
    Consumer -> Circuit Breaker (OPEN) -> Persistent Buffer (Redis)
                                     |
                                     v
              Circuit Breaker (CLOSED) -> Flush to InfluxDB

Features:
- Redis LIST for FIFO queue (reliable and fast)
- Configurable max buffer size (prevents memory exhaustion)
- TTL on buffered data (discard very old data)
- Automatic flush when circuit closes
- Prometheus metrics for monitoring
"""

import logging
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)

# Prometheus Metrics
buffer_size_current = Gauge(
    'circuit_breaker_buffer_size',
    'Current number of data points in the persistent buffer',
    ['buffer_name']
)

buffer_writes_total = Counter(
    'circuit_breaker_buffer_writes_total',
    'Total data points written to persistent buffer',
    ['buffer_name', 'status']  # success, failed, dropped
)

buffer_flushes_total = Counter(
    'circuit_breaker_buffer_flushes_total',
    'Total flush operations from persistent buffer',
    ['buffer_name', 'status']  # success, partial, failed
)

buffer_data_recovered_total = Counter(
    'circuit_breaker_buffer_data_recovered_total',
    'Total data points recovered from buffer to InfluxDB',
    ['buffer_name']
)


class PersistentBuffer:
    """
    Redis-backed buffer for storing data during circuit breaker outages.

    Uses Redis LIST as a FIFO queue:
    - RPUSH to add new data to end of queue
    - LPOP to remove data from front (oldest first)

    This ensures data is processed in order when recovered.
    """

    def __init__(
        self,
        name: str = "influxdb_buffer",
        redis_key_prefix: str = "optiflow:buffer",
        max_size: int = 100000,      # Max 100k points (prevents memory exhaustion)
        ttl_seconds: int = 3600,     # 1 hour TTL for buffered data
        flush_batch_size: int = 500  # Points per flush batch
    ):
        """
        Initialize persistent buffer.

        Args:
            name: Buffer identifier (for metrics and logging)
            redis_key_prefix: Redis key prefix for the buffer
            max_size: Maximum number of points to buffer
            ttl_seconds: TTL for buffered data (discard if too old)
            flush_batch_size: Number of points to flush per batch
        """
        self.name = name
        self.redis_key = f"{redis_key_prefix}:{name}"
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.flush_batch_size = flush_batch_size

        self._redis_client = None
        self._enabled = False
        self._is_flushing = False

        # Statistics
        self._total_buffered = 0
        self._total_recovered = 0
        self._total_dropped = 0

        logger.info(f"📦 PersistentBuffer '{name}' initialized")
        logger.info(f"   Redis key: {self.redis_key}")
        logger.info(f"   Max size: {max_size}, TTL: {ttl_seconds}s")

    async def connect(self, redis_client) -> bool:
        """
        Connect to Redis.

        Args:
            redis_client: Async Redis client instance

        Returns:
            True if connected successfully
        """
        try:
            self._redis_client = redis_client
            await self._redis_client.ping()
            self._enabled = True

            # Get current buffer size
            current_size = await self.size()
            logger.info(f"✅ PersistentBuffer '{self.name}' connected to Redis")
            logger.info(f"   Current buffer size: {current_size}")

            buffer_size_current.labels(buffer_name=self.name).set(current_size)
            return True

        except Exception as e:
            logger.error(f"❌ PersistentBuffer '{self.name}' failed to connect: {e}")
            self._enabled = False
            return False

    async def disconnect(self):
        """Disconnect from Redis."""
        self._enabled = False
        self._redis_client = None
        logger.info(f"🔌 PersistentBuffer '{self.name}' disconnected")

    async def buffer(self, data_points: List[Dict[str, Any]]) -> int:
        """
        Buffer data points to Redis.

        Args:
            data_points: List of data point dictionaries

        Returns:
            Number of points successfully buffered
        """
        if not self._enabled or not self._redis_client:
            logger.warning(f"⚠️ Buffer '{self.name}' not enabled, dropping {len(data_points)} points")
            buffer_writes_total.labels(buffer_name=self.name, status='dropped').inc(len(data_points))
            self._total_dropped += len(data_points)
            return 0

        try:
            # Check current size
            current_size = await self.size()

            # Calculate how many we can buffer
            available_space = self.max_size - current_size
            if available_space <= 0:
                logger.warning(
                    f"⚠️ Buffer '{self.name}' is full ({current_size}/{self.max_size}), "
                    f"dropping {len(data_points)} oldest points"
                )
                # Remove oldest points to make room
                points_to_remove = len(data_points)
                for _ in range(min(points_to_remove, current_size)):
                    await self._redis_client.lpop(self.redis_key)
                available_space = len(data_points)

            # Buffer data points
            points_to_buffer = data_points[:available_space]
            buffered_count = 0

            for point in points_to_buffer:
                # Add timestamp for TTL tracking
                buffered_point = {
                    'data': point,
                    'buffered_at': datetime.utcnow().isoformat()
                }

                await self._redis_client.rpush(
                    self.redis_key,
                    json.dumps(buffered_point, default=str)
                )
                buffered_count += 1

            # Set TTL on the key
            await self._redis_client.expire(self.redis_key, self.ttl_seconds)

            self._total_buffered += buffered_count

            # Update metrics
            new_size = await self.size()
            buffer_size_current.labels(buffer_name=self.name).set(new_size)
            buffer_writes_total.labels(buffer_name=self.name, status='success').inc(buffered_count)

            if len(data_points) > available_space:
                dropped = len(data_points) - buffered_count
                buffer_writes_total.labels(buffer_name=self.name, status='dropped').inc(dropped)
                self._total_dropped += dropped

            logger.info(
                f"📦 Buffered {buffered_count}/{len(data_points)} points in '{self.name}' "
                f"(total: {new_size}/{self.max_size})"
            )

            return buffered_count

        except Exception as e:
            logger.error(f"❌ Failed to buffer data in '{self.name}': {e}")
            buffer_writes_total.labels(buffer_name=self.name, status='failed').inc(len(data_points))
            return 0

    async def flush(self, write_func) -> tuple:
        """
        Flush buffered data to InfluxDB.

        Args:
            write_func: Function to write data points to InfluxDB
                       Signature: write_func(List[Dict]) -> bool

        Returns:
            Tuple of (success_count, failed_count)
        """
        if not self._enabled or not self._redis_client:
            return (0, 0)

        if self._is_flushing:
            logger.warning(f"⚠️ Buffer '{self.name}' flush already in progress")
            return (0, 0)

        self._is_flushing = True
        success_count = 0
        failed_count = 0

        try:
            current_size = await self.size()
            if current_size == 0:
                logger.debug(f"Buffer '{self.name}' is empty, nothing to flush")
                return (0, 0)

            logger.info(f"🔄 Starting flush of {current_size} points from '{self.name}'")

            batch = []
            while True:
                # Get a point from the front of the queue
                raw_point = await self._redis_client.lpop(self.redis_key)
                if raw_point is None:
                    break

                try:
                    buffered_point = json.loads(raw_point)
                    data_point = buffered_point.get('data', buffered_point)

                    # Check if data is too old (beyond TTL)
                    buffered_at = buffered_point.get('buffered_at')
                    if buffered_at:
                        try:
                            buffered_time = datetime.fromisoformat(buffered_at)
                            age_seconds = (datetime.utcnow() - buffered_time).total_seconds()
                            if age_seconds > self.ttl_seconds:
                                logger.debug(f"Skipping stale point (age: {age_seconds:.0f}s)")
                                continue
                        except (ValueError, TypeError):
                            pass

                    batch.append(data_point)

                    # Flush batch when full
                    if len(batch) >= self.flush_batch_size:
                        try:
                            if write_func(batch):
                                success_count += len(batch)
                                buffer_data_recovered_total.labels(buffer_name=self.name).inc(len(batch))
                                logger.debug(f"✅ Flushed batch of {len(batch)} points")
                            else:
                                # Write failed - re-buffer the data
                                await self._rebuffer(batch)
                                failed_count += len(batch)
                                logger.warning(f"⚠️ Flush failed, re-buffered {len(batch)} points")
                                break  # Stop flushing if write fails
                        except Exception as e:
                            logger.error(f"❌ Error flushing batch: {e}")
                            await self._rebuffer(batch)
                            failed_count += len(batch)
                            break

                        batch = []

                except json.JSONDecodeError as e:
                    logger.error(f"❌ Invalid JSON in buffer: {e}")
                    continue

            # Flush remaining batch
            if batch:
                try:
                    if write_func(batch):
                        success_count += len(batch)
                        buffer_data_recovered_total.labels(buffer_name=self.name).inc(len(batch))
                    else:
                        await self._rebuffer(batch)
                        failed_count += len(batch)
                except Exception as e:
                    logger.error(f"❌ Error flushing final batch: {e}")
                    await self._rebuffer(batch)
                    failed_count += len(batch)

            self._total_recovered += success_count

            # Update metrics
            remaining_size = await self.size()
            buffer_size_current.labels(buffer_name=self.name).set(remaining_size)

            if success_count > 0:
                buffer_flushes_total.labels(buffer_name=self.name, status='success').inc()
            if failed_count > 0:
                buffer_flushes_total.labels(buffer_name=self.name, status='partial').inc()

            logger.info(
                f"✅ Flush complete: {success_count} recovered, {failed_count} failed, "
                f"{remaining_size} remaining in buffer"
            )

            return (success_count, failed_count)

        except Exception as e:
            logger.error(f"❌ Flush error in '{self.name}': {e}")
            buffer_flushes_total.labels(buffer_name=self.name, status='failed').inc()
            return (success_count, failed_count)

        finally:
            self._is_flushing = False

    async def _rebuffer(self, data_points: List[Dict[str, Any]]):
        """Re-buffer failed points at the front of the queue."""
        try:
            for point in reversed(data_points):
                buffered_point = {
                    'data': point,
                    'buffered_at': datetime.utcnow().isoformat()
                }
                await self._redis_client.lpush(
                    self.redis_key,
                    json.dumps(buffered_point, default=str)
                )
        except Exception as e:
            logger.error(f"❌ Failed to re-buffer data: {e}")

    async def size(self) -> int:
        """Get current buffer size."""
        if not self._enabled or not self._redis_client:
            return 0

        try:
            return await self._redis_client.llen(self.redis_key)
        except Exception:
            return 0

    async def clear(self):
        """Clear all buffered data."""
        if not self._enabled or not self._redis_client:
            return

        try:
            await self._redis_client.delete(self.redis_key)
            buffer_size_current.labels(buffer_name=self.name).set(0)
            logger.info(f"🗑️ Buffer '{self.name}' cleared")
        except Exception as e:
            logger.error(f"❌ Failed to clear buffer '{self.name}': {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics."""
        return {
            'name': self.name,
            'enabled': self._enabled,
            'is_flushing': self._is_flushing,
            'total_buffered': self._total_buffered,
            'total_recovered': self._total_recovered,
            'total_dropped': self._total_dropped,
            'max_size': self.max_size,
            'ttl_seconds': self.ttl_seconds
        }


# Global singleton instance
_buffer_instance: Optional[PersistentBuffer] = None


def get_persistent_buffer() -> PersistentBuffer:
    """Get global persistent buffer instance."""
    global _buffer_instance
    if _buffer_instance is None:
        _buffer_instance = PersistentBuffer()
    return _buffer_instance


async def init_persistent_buffer(redis_client) -> PersistentBuffer:
    """Initialize and connect the persistent buffer."""
    buffer = get_persistent_buffer()
    await buffer.connect(redis_client)
    return buffer
