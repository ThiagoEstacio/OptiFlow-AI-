"""
Redis Cache Service - Distributed caching for AI responses and data
Provides persistent, scalable caching across multiple backend instances
"""

import json
import hashlib
import logging
from typing import Optional, Dict, Any, List, Union
from datetime import timedelta
import os

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis-based cache for:
    - AI response caching (reduces LLM calls)
    - Tag data caching (reduces DB queries)
    - Session data
    - Rate limiting state
    """

    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._connected = False

        # Configuration from environment
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.cache_db = int(os.getenv("REDIS_CACHE_DB", "1"))

        # Cache settings
        self.default_ttl = 300  # 5 minutes
        self.ai_cache_ttl = 600  # 10 minutes for AI responses
        self.tag_cache_ttl = 60  # 1 minute for real-time tag data
        self.stats_cache_ttl = 300  # 5 minutes for statistics

    async def connect(self):
        """Initialize Redis connection pool"""
        if self._connected:
            return

        try:
            self._pool = ConnectionPool.from_url(
                self.redis_url,
                db=self.cache_db,
                max_connections=50,
                decode_responses=True
            )
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            await self._client.ping()
            self._connected = True
            logger.info(f"✅ Redis cache connected: {self.redis_url}")

        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self._connected = False

    async def disconnect(self):
        """Close Redis connections"""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Redis cache disconnected")

    async def _ensure_connected(self):
        """Ensure Redis is connected before operations"""
        if not self._connected:
            await self.connect()
        return self._connected

    # ==========================================
    # AI RESPONSE CACHING
    # ==========================================

    def _generate_ai_key(self, message: str, context: Optional[Dict] = None) -> str:
        """Generate cache key for AI responses"""
        normalized = message.lower().strip()
        normalized = ''.join(c for c in normalized if c.isalnum() or c.isspace())
        normalized = ' '.join(normalized.split())

        context_str = json.dumps(context, sort_keys=True) if context else ""
        cache_str = f"ai:{normalized}:{context_str}"

        return f"ai_cache:{hashlib.md5(cache_str.encode()).hexdigest()}"

    async def get_ai_response(
        self,
        message: str,
        context: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached AI response"""
        if not await self._ensure_connected():
            return None

        try:
            key = self._generate_ai_key(message, context)
            cached = await self._client.get(key)

            if cached:
                logger.info(f"⚡ Redis AI cache HIT: {key[:20]}...")
                return json.loads(cached)

            return None

        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set_ai_response(
        self,
        message: str,
        response: Dict[str, Any],
        context: Optional[Dict] = None,
        ttl: Optional[int] = None
    ):
        """Cache AI response"""
        if not await self._ensure_connected():
            return

        try:
            key = self._generate_ai_key(message, context)
            ttl = ttl or self.ai_cache_ttl

            await self._client.setex(
                key,
                ttl,
                json.dumps(response)
            )
            logger.info(f"💾 Redis AI cache SET: {key[:20]}... (TTL: {ttl}s)")

        except Exception as e:
            logger.error(f"Redis set error: {e}")

    # ==========================================
    # TAG DATA CACHING
    # ==========================================

    async def get_tag_value(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """Get cached tag value"""
        if not await self._ensure_connected():
            return None

        try:
            key = f"tag:{tag_id}:value"
            cached = await self._client.get(key)

            if cached:
                return json.loads(cached)
            return None

        except Exception as e:
            logger.error(f"Redis tag get error: {e}")
            return None

    async def set_tag_value(
        self,
        tag_id: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """Cache tag value"""
        if not await self._ensure_connected():
            return

        try:
            key = f"tag:{tag_id}:value"
            ttl = ttl or self.tag_cache_ttl

            await self._client.setex(key, ttl, json.dumps(value))

        except Exception as e:
            logger.error(f"Redis tag set error: {e}")

    async def get_multiple_tag_values(
        self,
        tag_ids: List[str]
    ) -> Dict[str, Optional[Dict]]:
        """Get multiple cached tag values"""
        if not await self._ensure_connected():
            return {tid: None for tid in tag_ids}

        try:
            keys = [f"tag:{tid}:value" for tid in tag_ids]
            values = await self._client.mget(keys)

            result = {}
            for tag_id, value in zip(tag_ids, values):
                result[tag_id] = json.loads(value) if value else None

            return result

        except Exception as e:
            logger.error(f"Redis mget error: {e}")
            return {tid: None for tid in tag_ids}

    async def set_multiple_tag_values(
        self,
        values: Dict[str, Dict[str, Any]],
        ttl: Optional[int] = None
    ):
        """Cache multiple tag values"""
        if not await self._ensure_connected():
            return

        try:
            ttl = ttl or self.tag_cache_ttl
            pipe = self._client.pipeline()

            for tag_id, value in values.items():
                key = f"tag:{tag_id}:value"
                pipe.setex(key, ttl, json.dumps(value))

            await pipe.execute()

        except Exception as e:
            logger.error(f"Redis mset error: {e}")

    # ==========================================
    # STATISTICS CACHING
    # ==========================================

    async def get_statistics(
        self,
        tag_id: str,
        duration: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached statistics"""
        if not await self._ensure_connected():
            return None

        try:
            key = f"stats:{tag_id}:{duration}"
            cached = await self._client.get(key)

            if cached:
                logger.info(f"⚡ Redis stats cache HIT: {key}")
                return json.loads(cached)
            return None

        except Exception as e:
            logger.error(f"Redis stats get error: {e}")
            return None

    async def set_statistics(
        self,
        tag_id: str,
        duration: str,
        stats: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """Cache statistics"""
        if not await self._ensure_connected():
            return

        try:
            key = f"stats:{tag_id}:{duration}"
            ttl = ttl or self.stats_cache_ttl

            await self._client.setex(key, ttl, json.dumps(stats))
            logger.info(f"💾 Redis stats cache SET: {key} (TTL: {ttl}s)")

        except Exception as e:
            logger.error(f"Redis stats set error: {e}")

    # ==========================================
    # CACHE MANAGEMENT
    # ==========================================

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        if not await self._ensure_connected():
            return 0

        try:
            cursor = 0
            deleted = 0

            while True:
                cursor, keys = await self._client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )

                if keys:
                    deleted += await self._client.delete(*keys)

                if cursor == 0:
                    break

            logger.info(f"🗑️ Invalidated {deleted} keys matching: {pattern}")
            return deleted

        except Exception as e:
            logger.error(f"Redis invalidate error: {e}")
            return 0

    async def clear_ai_cache(self) -> int:
        """Clear all AI response cache"""
        return await self.invalidate_pattern("ai_cache:*")

    async def clear_tag_cache(self) -> int:
        """Clear all tag value cache"""
        return await self.invalidate_pattern("tag:*:value")

    async def clear_all(self) -> bool:
        """Clear entire cache database"""
        if not await self._ensure_connected():
            return False

        try:
            await self._client.flushdb()
            logger.info("🗑️ Redis cache cleared completely")
            return True

        except Exception as e:
            logger.error(f"Redis flush error: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not await self._ensure_connected():
            return {"connected": False}

        try:
            info = await self._client.info("stats")
            memory = await self._client.info("memory")
            dbsize = await self._client.dbsize()

            return {
                "connected": True,
                "keys": dbsize,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) /
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100,
                    2
                ),
                "memory_used": memory.get("used_memory_human", "0B"),
                "memory_peak": memory.get("used_memory_peak_human", "0B"),
            }

        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {"connected": True, "error": str(e)}

    async def health_check(self) -> bool:
        """Check Redis health"""
        if not await self._ensure_connected():
            return False

        try:
            await self._client.ping()
            return True
        except Exception:
            return False


# Global instance
_redis_cache: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """Get global Redis cache instance"""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache


async def init_redis_cache():
    """Initialize Redis cache on startup"""
    cache = get_redis_cache()
    await cache.connect()
    logger.info("✅ Redis cache initialized")


async def close_redis_cache():
    """Close Redis cache on shutdown"""
    cache = get_redis_cache()
    await cache.disconnect()
