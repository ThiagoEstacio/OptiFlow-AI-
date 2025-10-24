"""
Cache utilities using Redis
"""
import json
from typing import Optional, Any
from functools import wraps
import redis.asyncio as redis

from app.core.config import settings

# Redis clients for different purposes
_redis_cache_client: Optional[redis.Redis] = None
_redis_session_client: Optional[redis.Redis] = None
_redis_realtime_client: Optional[redis.Redis] = None


async def get_cache_client() -> redis.Redis:
    """Get Redis cache client"""
    global _redis_cache_client
    if _redis_cache_client is None:
        _redis_cache_client = await redis.from_url(
            settings.REDIS_URL,
            db=settings.REDIS_CACHE_DB,
            decode_responses=True
        )
    return _redis_cache_client


async def get_session_client() -> redis.Redis:
    """Get Redis session client"""
    global _redis_session_client
    if _redis_session_client is None:
        _redis_session_client = await redis.from_url(
            settings.REDIS_URL,
            db=settings.REDIS_SESSION_DB,
            decode_responses=True
        )
    return _redis_session_client


async def get_realtime_client() -> redis.Redis:
    """Get Redis realtime client (for pub/sub)"""
    global _redis_realtime_client
    if _redis_realtime_client is None:
        _redis_realtime_client = await redis.from_url(
            settings.REDIS_URL,
            db=settings.REDIS_REALTIME_DB,
            decode_responses=True
        )
    return _redis_realtime_client


async def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """
    Set a value in cache

    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        ttl: Time to live in seconds (default: 1 hour)

    Returns:
        True if successful
    """
    try:
        client = await get_cache_client()
        serialized = json.dumps(value)
        await client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        print(f"Cache set error: {e}")
        return False


async def cache_get(key: str) -> Optional[Any]:
    """
    Get a value from cache

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found
    """
    try:
        client = await get_cache_client()
        value = await client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        print(f"Cache get error: {e}")
        return None


async def cache_delete(key: str) -> bool:
    """
    Delete a value from cache

    Args:
        key: Cache key

    Returns:
        True if successful
    """
    try:
        client = await get_cache_client()
        await client.delete(key)
        return True
    except Exception as e:
        print(f"Cache delete error: {e}")
        return False


async def cache_clear_pattern(pattern: str) -> int:
    """
    Clear all keys matching a pattern

    Args:
        pattern: Key pattern (e.g., "device:*")

    Returns:
        Number of keys deleted
    """
    try:
        client = await get_cache_client()
        keys = await client.keys(pattern)
        if keys:
            return await client.delete(*keys)
        return 0
    except Exception as e:
        print(f"Cache clear pattern error: {e}")
        return 0


def cache_decorator(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator for caching function results

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_value = await cache_get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache_set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


async def close_redis_connections():
    """Close all Redis connections"""
    global _redis_cache_client, _redis_session_client, _redis_realtime_client

    if _redis_cache_client:
        await _redis_cache_client.close()
        _redis_cache_client = None

    if _redis_session_client:
        await _redis_session_client.close()
        _redis_session_client = None

    if _redis_realtime_client:
        await _redis_realtime_client.close()
        _redis_realtime_client = None
