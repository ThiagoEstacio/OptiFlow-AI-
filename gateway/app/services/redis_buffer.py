"""
Redis-based High-Performance Data Buffer

This buffer uses Redis for high-throughput, persistent data buffering
when the Kafka producer is unavailable or overloaded.

Advantages over SQLite:
- Much higher write throughput (100k+ writes/sec vs ~1k/sec)
- Atomic operations for concurrent access
- Built-in TTL for automatic cleanup
- Can be shared across multiple gateway instances
- Lower latency (in-memory with persistence)

Usage:
    buffer = RedisBuffer(redis_url="redis://localhost:6379")
    await buffer.connect()

    # Add data point
    await buffer.add(device_id="plc-1", tag_id="temp1", value=25.5, ...)

    # Get unsent data
    batch = await buffer.get_unsent(limit=1000)

    # Mark as sent
    await buffer.mark_sent([msg['id'] for msg in batch])
"""
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ..core.logger import logger


class RedisBuffer:
    """
    High-performance Redis-based data buffer for tag data

    Data Structure:
    - Queue: optiflow:buffer:queue (LIST) - Message IDs in FIFO order
    - Messages: optiflow:buffer:msg:{id} (HASH) - Individual message data
    - Sent Set: optiflow:buffer:sent (SET) - IDs of sent messages
    - Stats: optiflow:buffer:stats (HASH) - Buffer statistics

    Example message structure:
    {
        'id': 'uuid',
        'device_id': 'plc-1',
        'tag_id': 'temp1',
        'tag_name': 'Temperature 1',
        'value': 25.5,
        'quality': 'good',
        'timestamp': '2025-01-15T10:30:00Z',
        'buffered_at': '2025-01-15T10:30:01Z'
    }
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        max_buffer_size: int = 100000,
        message_ttl: int = 86400,  # 24 hours
        key_prefix: str = "optiflow:buffer"
    ):
        """
        Initialize Redis buffer

        Args:
            redis_url: Redis connection URL
            max_buffer_size: Maximum number of buffered messages
            message_ttl: TTL for messages in seconds (default: 24h)
            key_prefix: Redis key prefix for namespace isolation
        """
        self.redis_url = redis_url
        self.max_buffer_size = max_buffer_size
        self.message_ttl = message_ttl
        self.key_prefix = key_prefix

        # Redis keys
        self.queue_key = f"{key_prefix}:queue"
        self.msg_key_prefix = f"{key_prefix}:msg:"
        self.sent_key = f"{key_prefix}:sent"
        self.stats_key = f"{key_prefix}:stats"

        self.redis: Optional[aioredis.Redis] = None
        self.connected = False

        if not REDIS_AVAILABLE:
            logger.warning("⚠️  redis package not installed - RedisBuffer disabled")

    async def connect(self) -> bool:
        """
        Connect to Redis

        Returns:
            True if connected successfully
        """
        if not REDIS_AVAILABLE:
            logger.error("❌ Cannot connect to Redis - redis package not installed")
            return False

        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5
            )

            # Test connection
            await self.redis.ping()

            self.connected = True
            logger.info(f"✅ RedisBuffer connected to {self.redis_url}")

            # Initialize stats if not exists
            await self._init_stats()

            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            try:
                await self.redis.close()
                self.connected = False
                logger.info("Redis buffer connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")

    async def _init_stats(self):
        """Initialize statistics counters"""
        try:
            exists = await self.redis.exists(self.stats_key)
            if not exists:
                await self.redis.hset(
                    self.stats_key,
                    mapping={
                        'total_added': 0,
                        'total_sent': 0,
                        'total_dropped': 0
                    }
                )
        except Exception as e:
            logger.error(f"Failed to initialize stats: {e}")

    async def add(
        self,
        device_id: str,
        tag_id: str,
        tag_name: str,
        value: Any,
        quality: str,
        timestamp: datetime,
        source: str = "gateway"
    ) -> bool:
        """
        Add data point to buffer

        Args:
            device_id: Device identifier
            tag_id: Tag identifier
            tag_name: Tag name
            value: Tag value
            quality: Data quality (good, bad, uncertain)
            timestamp: Data timestamp
            source: Data source identifier

        Returns:
            True if added successfully
        """
        if not self.connected:
            logger.warning("⚠️  Redis not connected - cannot buffer data")
            return False

        try:
            # Check buffer size limit
            queue_size = await self.redis.llen(self.queue_key)
            if queue_size >= self.max_buffer_size:
                logger.warning(
                    f"⚠️  Buffer full ({queue_size}/{self.max_buffer_size}) - "
                    f"dropping oldest message"
                )
                # Remove oldest message
                oldest_id = await self.redis.lpop(self.queue_key)
                if oldest_id:
                    await self.redis.delete(f"{self.msg_key_prefix}{oldest_id}")
                    await self.redis.hincrby(self.stats_key, 'total_dropped', 1)

            # Generate unique message ID
            msg_id = str(uuid.uuid4())

            # Create message
            message = {
                'id': msg_id,
                'device_id': device_id,
                'tag_id': tag_id,
                'tag_name': tag_name,
                'value': json.dumps(value),
                'quality': quality,
                'timestamp': timestamp.isoformat(),
                'buffered_at': datetime.utcnow().isoformat(),
                'source': source
            }

            # Store message with TTL
            msg_key = f"{self.msg_key_prefix}{msg_id}"
            await self.redis.hset(msg_key, mapping=message)
            await self.redis.expire(msg_key, self.message_ttl)

            # Add to queue (right push = FIFO)
            await self.redis.rpush(self.queue_key, msg_id)

            # Update stats
            await self.redis.hincrby(self.stats_key, 'total_added', 1)

            logger.debug(f"✅ Buffered {tag_name} = {value} (id: {msg_id})")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to add data to Redis buffer: {e}")
            return False

    async def get_unsent(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get unsent buffered data

        Args:
            limit: Maximum number of records to retrieve

        Returns:
            List of buffered data dictionaries
        """
        if not self.connected:
            return []

        try:
            # Get message IDs from queue (peek, don't remove)
            msg_ids = await self.redis.lrange(self.queue_key, 0, limit - 1)

            if not msg_ids:
                return []

            # Fetch messages
            results = []
            for msg_id in msg_ids:
                # Skip if already marked as sent
                is_sent = await self.redis.sismember(self.sent_key, msg_id)
                if is_sent:
                    continue

                msg_key = f"{self.msg_key_prefix}{msg_id}"
                msg_data = await self.redis.hgetall(msg_key)

                if msg_data:
                    # Parse value from JSON
                    msg_data['value'] = json.loads(msg_data['value'])
                    results.append(msg_data)

            logger.debug(f"📤 Retrieved {len(results)} unsent messages from buffer")
            return results

        except Exception as e:
            logger.error(f"❌ Failed to get unsent buffer data: {e}")
            return []

    async def mark_sent(self, message_ids: List[str]) -> bool:
        """
        Mark messages as sent

        Args:
            message_ids: List of message IDs to mark as sent

        Returns:
            True if marked successfully
        """
        if not self.connected or not message_ids:
            return False

        try:
            # Add to sent set with TTL
            await self.redis.sadd(self.sent_key, *message_ids)
            await self.redis.expire(self.sent_key, self.message_ttl)

            # Remove from queue
            for msg_id in message_ids:
                await self.redis.lrem(self.queue_key, 1, msg_id)

            # Update stats
            await self.redis.hincrby(self.stats_key, 'total_sent', len(message_ids))

            logger.debug(f"✅ Marked {len(message_ids)} messages as sent")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to mark messages as sent: {e}")
            return False

    async def delete_sent(self, older_than_hours: int = 24):
        """
        Delete old sent messages

        Note: Redis TTL handles this automatically, but this method
        provides manual cleanup if needed.

        Args:
            older_than_hours: Delete messages older than this many hours
        """
        if not self.connected:
            return

        try:
            # Get all sent message IDs
            sent_ids = await self.redis.smembers(self.sent_key)

            cutoff_time = datetime.utcnow().timestamp() - (older_than_hours * 3600)
            deleted_count = 0

            for msg_id in sent_ids:
                msg_key = f"{self.msg_key_prefix}{msg_id}"
                msg_data = await self.redis.hgetall(msg_key)

                if msg_data:
                    buffered_at = datetime.fromisoformat(msg_data['buffered_at']).timestamp()
                    if buffered_at < cutoff_time:
                        await self.redis.delete(msg_key)
                        await self.redis.srem(self.sent_key, msg_id)
                        deleted_count += 1

            if deleted_count > 0:
                logger.info(f"🗑️  Deleted {deleted_count} old sent messages from buffer")

        except Exception as e:
            logger.error(f"❌ Failed to delete old messages: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get buffer statistics

        Returns:
            Dictionary with buffer stats
        """
        if not self.connected:
            return {
                'connected': False,
                'unsent': 0,
                'sent': 0,
                'total_added': 0,
                'total_sent': 0,
                'total_dropped': 0
            }

        try:
            # Get queue size
            unsent_count = await self.redis.llen(self.queue_key)

            # Get sent count
            sent_count = await self.redis.scard(self.sent_key)

            # Get lifetime stats
            stats_data = await self.redis.hgetall(self.stats_key)

            return {
                'connected': True,
                'unsent': unsent_count,
                'sent': sent_count,
                'total_added': int(stats_data.get('total_added', 0)),
                'total_sent': int(stats_data.get('total_sent', 0)),
                'total_dropped': int(stats_data.get('total_dropped', 0)),
                'max_buffer_size': self.max_buffer_size,
                'message_ttl': self.message_ttl
            }

        except Exception as e:
            logger.error(f"❌ Failed to get buffer stats: {e}")
            return {
                'connected': False,
                'error': str(e)
            }

    async def clear_all(self):
        """Clear all buffer data (use with caution!)"""
        if not self.connected:
            return

        try:
            # Get all message IDs
            msg_ids = await self.redis.lrange(self.queue_key, 0, -1)

            # Delete all messages
            for msg_id in msg_ids:
                msg_key = f"{self.msg_key_prefix}{msg_id}"
                await self.redis.delete(msg_key)

            # Clear queue and sent set
            await self.redis.delete(self.queue_key)
            await self.redis.delete(self.sent_key)

            # Reset stats
            await self.redis.hset(
                self.stats_key,
                mapping={
                    'total_added': 0,
                    'total_sent': 0,
                    'total_dropped': 0
                }
            )

            logger.warning("⚠️  Redis buffer cleared completely")

        except Exception as e:
            logger.error(f"❌ Failed to clear buffer: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Redis buffer

        Returns:
            Health status dictionary
        """
        try:
            if not self.connected or not self.redis:
                return {
                    'status': 'unhealthy',
                    'connected': False,
                    'error': 'Not connected to Redis'
                }

            # Test Redis connection
            start_time = time.time()
            await self.redis.ping()
            latency_ms = (time.time() - start_time) * 1000

            # Get stats
            stats = await self.get_stats()

            return {
                'status': 'healthy',
                'connected': True,
                'latency_ms': round(latency_ms, 2),
                'unsent_count': stats['unsent'],
                'buffer_usage_pct': round(stats['unsent'] / self.max_buffer_size * 100, 1),
                'total_added': stats['total_added'],
                'total_sent': stats['total_sent'],
                'total_dropped': stats['total_dropped']
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e)
            }
