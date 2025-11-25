"""
Redis Client Configuration for OptiFlow

Provides a centralized Redis client for use across the application.
Uses environment variables or default settings for connection configuration.
"""

import os
import redis
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Redis connection settings from environment
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', 'optiflow_redis_password')

# Global Redis client
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get or create a Redis client.

    Returns:
        Redis client instance or None if connection fails
    """
    global _redis_client

    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except Exception:
            _redis_client = None

    try:
        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )

        # Test connection
        _redis_client.ping()
        logger.info(f"Redis client connected to {REDIS_HOST}:{REDIS_PORT}")
        return _redis_client

    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}")
        _redis_client = None
        return None


def close_redis_client():
    """Close the global Redis client connection."""
    global _redis_client

    if _redis_client is not None:
        try:
            _redis_client.close()
            logger.info("Redis client closed")
        except Exception as e:
            logger.warning(f"Error closing Redis client: {e}")
        finally:
            _redis_client = None


# Helper functions for common operations
def redis_get(key: str) -> Optional[str]:
    """Get a value from Redis."""
    client = get_redis_client()
    if client:
        try:
            return client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
    return None


def redis_set(key: str, value: str, ex: Optional[int] = None) -> bool:
    """Set a value in Redis with optional expiration."""
    client = get_redis_client()
    if client:
        try:
            client.set(key, value, ex=ex)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
    return False


def redis_delete(key: str) -> bool:
    """Delete a key from Redis."""
    client = get_redis_client()
    if client:
        try:
            client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
    return False


def redis_exists(key: str) -> bool:
    """Check if a key exists in Redis."""
    client = get_redis_client()
    if client:
        try:
            return client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
    return False


def redis_incr(key: str) -> Optional[int]:
    """Increment a counter in Redis."""
    client = get_redis_client()
    if client:
        try:
            return client.incr(key)
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
    return None


def redis_expire(key: str, seconds: int) -> bool:
    """Set expiration on a key."""
    client = get_redis_client()
    if client:
        try:
            return client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {e}")
    return False
