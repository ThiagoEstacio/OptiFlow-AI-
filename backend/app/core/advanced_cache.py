"""
Advanced Multi-Layer Caching Strategy (PDCA #26)

Implements sophisticated caching with:
- L1: In-memory cache (LRU)
- L2: Redis distributed cache
- Cache warming
- Smart invalidation
- Stampede prevention
- TTL optimization

Performance targets:
- p95 latency < 50ms (vs 500ms without cache)
- Cache hit rate > 95%
- Database load reduction > 60%
"""

import logging
import asyncio
import hashlib
import pickle
from typing import Optional, Any, Callable, Dict
from datetime import datetime, timedelta
from functools import wraps
from collections import OrderedDict

logger = logging.getLogger(__name__)


class LRUCache:
    """
    Thread-safe LRU (Least Recently Used) cache.

    L1 cache stored in application memory.
    """

    def __init__(self, max_size: int = 1000):
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                value, expiry = self.cache[key]

                # Check if expired
                if expiry and datetime.utcnow() > expiry:
                    del self.cache[key]
                    self.misses += 1
                    return None

                return value
            else:
                self.misses += 1
                return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with optional TTL."""
        async with self._lock:
            # Calculate expiry
            expiry = None
            if ttl:
                expiry = datetime.utcnow() + timedelta(seconds=ttl)

            # Add to cache
            self.cache[key] = (value, expiry)
            self.cache.move_to_end(key)

            # Evict oldest if over max size
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    async def delete(self, key: str):
        """Delete key from cache."""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]

    async def clear(self):
        """Clear all cache."""
        async with self._lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }


class MultiLayerCache:
    """
    Multi-layer cache with L1 (memory) and L2 (Redis).

    Features:
    - Automatic fallback: L1 → L2 → Source
    - Write-through strategy
    - Cache warming
    - Stampede prevention (single-flight)
    - TTL optimization per key pattern
    """

    def __init__(
        self,
        l1_max_size: int = 1000,
        l2_client=None  # Redis client
    ):
        self.l1 = LRUCache(max_size=l1_max_size)
        self.l2 = l2_client

        # Stampede prevention: track in-flight requests
        self._in_flight: Dict[str, asyncio.Future] = {}
        self._in_flight_lock = asyncio.Lock()

        # Statistics
        self.l1_hits = 0
        self.l2_hits = 0
        self.misses = 0

    async def get(
        self,
        key: str,
        fetch_fn: Optional[Callable] = None,
        ttl: int = 300
    ) -> Optional[Any]:
        """
        Get value from cache with automatic fallback.

        Args:
            key: Cache key
            fetch_fn: Function to fetch value on cache miss
            ttl: Time to live in seconds

        Returns:
            Cached or fetched value
        """
        # Try L1 (memory)
        value = await self.l1.get(key)
        if value is not None:
            self.l1_hits += 1
            logger.debug(f"L1 cache hit: {key}")
            return value

        # Try L2 (Redis)
        if self.l2:
            try:
                value = await self._get_from_redis(key)
                if value is not None:
                    self.l2_hits += 1
                    logger.debug(f"L2 cache hit: {key}")

                    # Populate L1
                    await self.l1.set(key, value, ttl=min(ttl, 60))

                    return value

            except Exception as e:
                logger.warning(f"Redis error: {e}")

        # Cache miss - fetch from source
        if fetch_fn:
            self.misses += 1

            # Stampede prevention: check if already fetching
            async with self._in_flight_lock:
                if key in self._in_flight:
                    # Wait for in-flight request
                    logger.debug(f"Waiting for in-flight fetch: {key}")
                    return await self._in_flight[key]

                # Create future for this fetch
                future = asyncio.Future()
                self._in_flight[key] = future

            try:
                # Fetch value
                logger.debug(f"Cache miss, fetching: {key}")
                value = await fetch_fn() if asyncio.iscoroutinefunction(fetch_fn) else fetch_fn()

                # Set in both caches
                await self.set(key, value, ttl=ttl)

                # Resolve future
                future.set_result(value)

                return value

            except Exception as e:
                logger.error(f"Fetch failed for {key}: {e}")
                future.set_exception(e)
                raise

            finally:
                # Remove from in-flight
                async with self._in_flight_lock:
                    if key in self._in_flight:
                        del self._in_flight[key]

        return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """
        Set value in both L1 and L2 caches.

        Write-through strategy.
        """
        # Set in L1 (shorter TTL for memory efficiency)
        await self.l1.set(key, value, ttl=min(ttl, 60))

        # Set in L2 (Redis)
        if self.l2:
            try:
                await self._set_in_redis(key, value, ttl=ttl)
            except Exception as e:
                logger.warning(f"Failed to set in Redis: {e}")

    async def delete(self, key: str):
        """Delete key from both caches."""
        await self.l1.delete(key)

        if self.l2:
            try:
                await self.l2.delete(key)
            except Exception as e:
                logger.warning(f"Failed to delete from Redis: {e}")

    async def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching pattern.

        Example: invalidate_pattern("user:*")
        """
        if self.l2:
            try:
                # Get all keys matching pattern
                keys = await self.l2.keys(pattern)

                if keys:
                    # Delete from Redis
                    await self.l2.delete(*keys)

                    # Delete from L1 (check each key)
                    for key in keys:
                        await self.l1.delete(key.decode() if isinstance(key, bytes) else key)

                    logger.info(f"Invalidated {len(keys)} keys matching {pattern}")

            except Exception as e:
                logger.warning(f"Failed to invalidate pattern: {e}")

    async def warm(self, keys: list, fetch_fn: Callable):
        """
        Warm cache with pre-fetched data.

        Usage:
            await cache.warm(
                keys=["user:1", "user:2"],
                fetch_fn=lambda key: fetch_user(key.split(":")[1])
            )
        """
        logger.info(f"Warming cache with {len(keys)} keys")

        for key in keys:
            try:
                value = await fetch_fn(key)
                await self.set(key, value)
            except Exception as e:
                logger.warning(f"Failed to warm key {key}: {e}")

    async def _get_from_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis and deserialize."""
        try:
            value = await self.l2.get(key)

            if value:
                # Deserialize
                return pickle.loads(value)

            return None

        except Exception as e:
            logger.warning(f"Redis get error: {e}")
            return None

    async def _set_in_redis(self, key: str, value: Any, ttl: int):
        """Serialize and set value in Redis."""
        try:
            # Serialize
            serialized = pickle.dumps(value)

            # Set with TTL
            await self.l2.setex(key, ttl, serialized)

        except Exception as e:
            logger.warning(f"Redis set error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.l1_hits + self.l2_hits + self.misses
        overall_hit_rate = ((self.l1_hits + self.l2_hits) / total * 100) if total > 0 else 0

        return {
            "l1": self.l1.get_stats(),
            "l2_hits": self.l2_hits,
            "misses": self.misses,
            "overall_hit_rate": overall_hit_rate,
            "in_flight_requests": len(self._in_flight)
        }


# Global cache instance
_cache: Optional[MultiLayerCache] = None


def get_advanced_cache() -> MultiLayerCache:
    """Get global advanced cache instance."""
    global _cache

    if _cache is None:
        # Try to get Redis client
        try:
            from app.core.redis import get_redis_client
            redis_client = get_redis_client()
            _cache = MultiLayerCache(l2_client=redis_client)
            logger.info("Advanced cache initialized with Redis L2")
        except Exception as e:
            logger.warning(f"Could not initialize Redis for L2 cache: {e}")
            _cache = MultiLayerCache(l2_client=None)
            logger.info("Advanced cache initialized without L2 (memory only)")

    return _cache


# Decorators for easy caching

def cached_function(
    ttl: int = 300,
    key_prefix: str = "",
    key_builder: Optional[Callable] = None
):
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        key_builder: Custom function to build cache key from args

    Usage:
        @cached_function(ttl=300, key_prefix="user")
        async def get_user(user_id: str):
            return await db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default: hash of function name + args
                key_parts = [key_prefix or func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # Get from cache
            cache = get_advanced_cache()

            # Define fetch function
            async def fetch():
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            return await cache.get(cache_key, fetch_fn=fetch, ttl=ttl)

        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    Invalidate cache matching pattern.

    Usage:
        # After updating user
        await invalidate_cache("user:123:*")
    """
    cache = get_advanced_cache()
    return cache.invalidate_pattern(pattern)
