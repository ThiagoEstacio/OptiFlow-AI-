"""
Redis-based Cache Service for OptiFlow AI
Provides transparent caching with decorator support
"""

from redis import asyncio as aioredis
from typing import Any, Optional, Callable
import pickle
import hashlib
from functools import wraps
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis-based caching service with decorator support
    
    Features:
    - Transparent caching with @cached decorator
    - Pattern-based invalidation
    - Cache statistics
    - TTL support
    - Error resilience (fails open)
    """
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._connected = False
        self._stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0
        }
    
    async def connect(self):
        """Connect to Redis with connection pooling"""
        if not self._connected:
            try:
                # Create connection pool for better performance
                self.redis = await aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=False,
                    socket_keepalive=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    max_connections=20,  # Connection pool size
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # Test connection
                await self.redis.ping()
                self._connected = True
                logger.info("✅ Cache service connected to Redis with connection pool (20 connections)")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Redis: {e}")
                self._connected = False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/error
        """
        try:
            if not self._connected:
                await self.connect()
            
            if not self._connected:
                return None
            
            value = await self.redis.get(key)
            if value:
                self._stats["hits"] += 1
                logger.debug(f"✅ Cache HIT: {key}")
                return pickle.loads(value)
            
            self._stats["misses"] += 1
            logger.debug(f"❌ Cache MISS: {key}")
            return None
            
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Cache get error for key '{key}': {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: int = 300
    ) -> bool:
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 5 minutes)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._connected:
                await self.connect()
            
            if not self._connected:
                return False
            
            await self.redis.setex(
                key,
                ttl,
                pickle.dumps(value)
            )
            logger.debug(f"✅ Cache SET: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Cache set error for key '{key}': {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            if not self._connected:
                await self.connect()
            
            if not self._connected:
                return False
            
            result = await self.redis.delete(key)
            logger.debug(f"✅ Cache DELETE: {key}")
            return result > 0
            
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern
        
        Args:
            pattern: Redis pattern (e.g., "dashboard:*")
        
        Returns:
            Number of keys deleted
        """
        try:
            if not self._connected:
                await self.connect()
            
            if not self._connected:
                return 0
            
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"✅ Cache INVALIDATE: {deleted} keys ({pattern})")
                return deleted
            
            return 0
            
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Cache invalidate error for pattern '{pattern}': {e}")
            return 0
    
    async def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with hits, misses, hit_rate, errors
        """
        try:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
            
            redis_info = {}
            if self._connected and self.redis:
                info = await self.redis.info("stats")
                redis_info = {
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "0B")
                }
            
            return {
                "app_stats": {
                    "hits": self._stats["hits"],
                    "misses": self._stats["misses"],
                    "errors": self._stats["errors"],
                    "hit_rate": f"{hit_rate:.2f}%"
                },
                "redis_stats": redis_info,
                "connected": self._connected
            }
            
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {
                "app_stats": self._stats,
                "redis_stats": {},
                "connected": self._connected,
                "error": str(e)
            }
    
    async def clear_all(self) -> bool:
        """
        Clear all cache (USE WITH CAUTION!)
        
        Returns:
            True if successful
        """
        try:
            if not self._connected:
                await self.connect()
            
            if not self._connected:
                return False
            
            await self.redis.flushdb()
            logger.warning("⚠️  Cache CLEARED (all keys deleted)")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            self._connected = False
            logger.info("✅ Cache service disconnected")


# Singleton instance
cache_service = CacheService()


def cached(
    ttl: int = 300, 
    key_prefix: str = "",
    skip_none: bool = True
):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Prefix for cache key (default: function name)
        skip_none: Don't cache None values (default: True)
    
    Usage:
        @cached(ttl=600, key_prefix="dashboard")
        async def get_dashboard_data(org_id: int):
            # Expensive operation
            return data
    
    Example:
        @cached(ttl=30)
        async def get_recent_tags(org_id: int):
            return await db.query(...)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            prefix = key_prefix or func.__name__
            
            # Create deterministic key from args and kwargs
            key_parts = [prefix]
            
            # Add positional args (skip 'self' or 'cls' if present)
            start_idx = 1 if args and hasattr(args[0], '__class__') else 0
            for arg in args[start_idx:]:
                key_parts.append(str(arg))
            
            # Add keyword args (sorted for consistency)
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = await cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result (if not None or skip_none=False)
            if result is not None or not skip_none:
                await cache_service.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_invalidate(pattern: str):
    """
    Decorator to invalidate cache after function execution
    
    Args:
        pattern: Cache key pattern to invalidate
    
    Usage:
        @cache_invalidate("dashboard:*")
        async def update_dashboard(org_id: int, data: dict):
            # Update operation
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute function first
            result = await func(*args, **kwargs)
            
            # Invalidate cache pattern
            await cache_service.invalidate_pattern(pattern)
            
            return result
        
        return wrapper
    return decorator
