"""
Redis service for caching, sessions, and pub/sub
"""
import redis
import json
from typing import Any, Optional, List
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """
    Service for interacting with Redis
    """

    def __init__(self):
        self.client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf-8"
        )

    def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        Set a value in Redis

        Args:
            key: Redis key
            value: Value (will be JSON serialized if dict/list)
            expire: Expiration time in seconds

        Returns:
            True if successful
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            if expire:
                return self.client.setex(key, expire, value)
            else:
                return self.client.set(key, value)

        except Exception as e:
            logger.error(f"Error setting Redis key {key}: {e}")
            return False

    def get(
        self,
        key: str,
        as_json: bool = False
    ) -> Optional[Any]:
        """
        Get a value from Redis

        Args:
            key: Redis key
            as_json: Parse value as JSON

        Returns:
            Value or None if not found
        """
        try:
            value = self.client.get(key)

            if value is None:
                return None

            if as_json:
                return json.loads(value)

            return value

        except Exception as e:
            logger.error(f"Error getting Redis key {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """
        Delete a key from Redis

        Args:
            key: Redis key

        Returns:
            True if deleted
        """
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting Redis key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if a key exists

        Args:
            key: Redis key

        Returns:
            True if exists
        """
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Error checking Redis key {key}: {e}")
            return False

    def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter

        Args:
            key: Redis key
            amount: Amount to increment

        Returns:
            New value
        """
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing Redis key {key}: {e}")
            return 0

    def cache_tag_value(
        self,
        tag_id: str,
        value: Any,
        quality: str = "good",
        expire: int = 300
    ) -> bool:
        """
        Cache latest tag value in Redis

        Args:
            tag_id: Tag UUID
            value: Tag value
            quality: Data quality
            expire: Cache expiration (seconds)

        Returns:
            True if successful
        """
        key = f"realtime:{tag_id}"
        data = {
            "value": value,
            "quality": quality,
            "timestamp": datetime.utcnow().isoformat()
        }
        return self.set(key, data, expire=expire)

    def get_cached_tag_value(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached tag value

        Args:
            tag_id: Tag UUID

        Returns:
            Cached value dict or None
        """
        key = f"realtime:{tag_id}"
        return self.get(key, as_json=True)

    def publish(self, channel: str, message: Any) -> int:
        """
        Publish a message to a channel

        Args:
            channel: Channel name
            message: Message (will be JSON serialized if dict/list)

        Returns:
            Number of subscribers that received the message
        """
        try:
            if isinstance(message, (dict, list)):
                message = json.dumps(message)

            return self.client.publish(channel, message)

        except Exception as e:
            logger.error(f"Error publishing to channel {channel}: {e}")
            return 0

    def publish_tag_update(
        self,
        tag_id: str,
        value: Any,
        quality: str = "good"
    ) -> int:
        """
        Publish tag update to subscribers

        Args:
            tag_id: Tag UUID
            value: Tag value
            quality: Data quality

        Returns:
            Number of subscribers
        """
        channel = "pubsub:updates"
        message = {
            "tag_id": str(tag_id),
            "value": value,
            "quality": quality,
            "timestamp": datetime.utcnow().isoformat()
        }
        return self.publish(channel, message)

    def cache_query_result(
        self,
        query_key: str,
        result: Any,
        expire: int = 300
    ) -> bool:
        """
        Cache query result

        Args:
            query_key: Unique query identifier
            result: Query result
            expire: Cache expiration (seconds)

        Returns:
            True if successful
        """
        key = f"cache:query:{query_key}"
        return self.set(key, result, expire=expire)

    def get_cached_query(self, query_key: str) -> Optional[Any]:
        """
        Get cached query result

        Args:
            query_key: Unique query identifier

        Returns:
            Cached result or None
        """
        key = f"cache:query:{query_key}"
        return self.get(key, as_json=True)

    def close(self):
        """Close Redis connection"""
        self.client.close()


# Global instance
from datetime import datetime

redis_service = RedisService()
