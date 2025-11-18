"""
Rate Limiter Service (PDCA #21)

Per-user and per-IP rate limiting for API endpoints.

Features:
- Sliding window rate limiting
- Per-user and per-IP limits
- Multiple time windows (second, minute, hour, day)
- Redis-based distributed rate limiting
- In-memory fallback when Redis unavailable
- Rate limit headers (X-RateLimit-*)
- Automatic cleanup of expired entries

Algorithm: Sliding Window Log
- Tracks individual request timestamps
- Accurate rate limiting
- No request bursts at window boundaries
"""

import logging
import time
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration for a specific limit."""
    requests: int  # Number of requests allowed
    window: int  # Time window in seconds
    name: str  # Name of the limit (e.g., "per_second", "per_minute")


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    remaining: int
    reset_at: float  # Unix timestamp when limit resets
    retry_after: Optional[int] = None  # Seconds until retry (if blocked)
    limit: int = 0  # Total requests allowed
    window: int = 0  # Window size in seconds


class InMemoryRateLimiter:
    """
    In-memory rate limiter using sliding window log algorithm.

    Used as fallback when Redis is unavailable.
    """

    def __init__(self):
        # Format: {key: [timestamp1, timestamp2, ...]}
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> RateLimitResult:
        """
        Check if request is within rate limit.

        Args:
            key: Unique identifier (user_id, IP, etc.)
            limit: Number of requests allowed
            window: Time window in seconds

        Returns:
            RateLimitResult with allow/deny decision
        """
        async with self._lock:
            now = time.time()
            cutoff = now - window

            # Get existing requests
            requests = self._requests.get(key, [])

            # Remove expired requests
            requests = [ts for ts in requests if ts > cutoff]

            # Check if limit exceeded
            allowed = len(requests) < limit

            if allowed:
                # Add current request
                requests.append(now)
                self._requests[key] = requests

            # Calculate remaining and reset time
            remaining = max(0, limit - len(requests))

            # Reset time is when the oldest request expires
            if requests:
                reset_at = requests[0] + window
            else:
                reset_at = now + window

            retry_after = None
            if not allowed and requests:
                # Retry after the oldest request expires
                retry_after = int(reset_at - now) + 1

            return RateLimitResult(
                allowed=allowed,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=retry_after,
                limit=limit,
                window=window
            )

    async def reset(self, key: str):
        """Reset rate limit for a key."""
        async with self._lock:
            if key in self._requests:
                del self._requests[key]

    async def cleanup_expired(self):
        """Remove expired entries to prevent memory leak."""
        async with self._lock:
            now = time.time()

            # Find keys with all expired requests
            keys_to_remove = []
            for key, requests in self._requests.items():
                # Keep only requests from last 24 hours (max window we support)
                recent_requests = [ts for ts in requests if ts > now - 86400]

                if not recent_requests:
                    keys_to_remove.append(key)
                else:
                    self._requests[key] = recent_requests

            # Remove expired keys
            for key in keys_to_remove:
                del self._requests[key]

            if keys_to_remove:
                logger.debug(f"Cleaned up {len(keys_to_remove)} expired rate limit entries")

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about rate limiter."""
        return {
            "total_keys": len(self._requests),
            "total_requests_tracked": sum(len(reqs) for reqs in self._requests.values())
        }


class RateLimiter:
    """
    Main rate limiter service.

    Supports multiple rate limit tiers:
    - Per-second limits (prevent DoS)
    - Per-minute limits (standard API throttling)
    - Per-hour limits (prevent abuse)
    - Per-day limits (quota management)

    Uses Redis for distributed rate limiting when available,
    falls back to in-memory for single-instance deployments.
    """

    # Default rate limits (can be overridden per endpoint)
    DEFAULT_LIMITS = [
        RateLimitConfig(requests=10, window=1, name="per_second"),     # 10/sec
        RateLimitConfig(requests=100, window=60, name="per_minute"),   # 100/min
        RateLimitConfig(requests=1000, window=3600, name="per_hour"),  # 1000/hour
        RateLimitConfig(requests=10000, window=86400, name="per_day"), # 10k/day
    ]

    # Stricter limits for unauthenticated requests
    ANONYMOUS_LIMITS = [
        RateLimitConfig(requests=5, window=1, name="per_second"),
        RateLimitConfig(requests=20, window=60, name="per_minute"),
        RateLimitConfig(requests=100, window=3600, name="per_hour"),
        RateLimitConfig(requests=500, window=86400, name="per_day"),
    ]

    def __init__(self, redis_client=None):
        """
        Initialize rate limiter.

        Args:
            redis_client: Optional Redis client for distributed rate limiting
        """
        self.redis = redis_client
        self.memory_limiter = InMemoryRateLimiter()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._use_redis = redis_client is not None

        if self._use_redis:
            logger.info("Rate limiter initialized with Redis backend")
        else:
            logger.info("Rate limiter initialized with in-memory backend")

    async def start(self):
        """Start background cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Rate limiter background tasks started")

    async def stop(self):
        """Stop background tasks."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        logger.info("Rate limiter stopped")

    async def check_rate_limit(
        self,
        identifier: str,
        limits: Optional[List[RateLimitConfig]] = None,
        is_authenticated: bool = True
    ) -> Tuple[bool, RateLimitResult]:
        """
        Check if request is within all configured rate limits.

        Args:
            identifier: Unique identifier (user_id, IP address, etc.)
            limits: Custom rate limits (uses defaults if None)
            is_authenticated: Whether request is from authenticated user

        Returns:
            Tuple of (allowed: bool, result: RateLimitResult)
            If any limit is exceeded, returns the most restrictive result
        """
        if limits is None:
            limits = self.DEFAULT_LIMITS if is_authenticated else self.ANONYMOUS_LIMITS

        # Check all limits
        results = []
        for limit_config in limits:
            key = f"ratelimit:{identifier}:{limit_config.name}"

            if self._use_redis:
                result = await self._check_redis(key, limit_config.requests, limit_config.window)
            else:
                result = await self.memory_limiter.check_rate_limit(
                    key,
                    limit_config.requests,
                    limit_config.window
                )

            results.append(result)

            # If any limit is exceeded, deny immediately
            if not result.allowed:
                logger.warning(
                    f"Rate limit exceeded for {identifier}: "
                    f"{limit_config.name} ({limit_config.requests}/{limit_config.window}s)"
                )
                return False, result

        # All limits passed, return the most restrictive result
        # (the one with least remaining requests)
        most_restrictive = min(results, key=lambda r: r.remaining)
        return True, most_restrictive

    async def _check_redis(
        self,
        key: str,
        limit: int,
        window: int
    ) -> RateLimitResult:
        """
        Check rate limit using Redis.

        Uses sorted sets to implement sliding window log.
        """
        try:
            now = time.time()
            cutoff = now - window

            pipe = self.redis.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(key, 0, cutoff)

            # Count current requests
            pipe.zcard(key)

            # Add current request (optimistically)
            pipe.zadd(key, {str(now): now})

            # Set expiration
            pipe.expire(key, window)

            results = await pipe.execute()

            current_count = results[1]  # Count before adding new request

            allowed = current_count < limit

            if not allowed:
                # Remove the optimistic request we added
                await self.redis.zrem(key, str(now))

            remaining = max(0, limit - current_count - (1 if allowed else 0))

            # Get oldest request timestamp for reset calculation
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                reset_at = oldest[0][1] + window
            else:
                reset_at = now + window

            retry_after = None
            if not allowed:
                retry_after = int(reset_at - now) + 1

            return RateLimitResult(
                allowed=allowed,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=retry_after,
                limit=limit,
                window=window
            )

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}, falling back to memory")
            return await self.memory_limiter.check_rate_limit(key, limit, window)

    async def reset(self, identifier: str, limit_name: Optional[str] = None):
        """
        Reset rate limit for an identifier.

        Args:
            identifier: User ID, IP, etc.
            limit_name: Specific limit to reset (None = reset all)
        """
        if limit_name:
            key = f"ratelimit:{identifier}:{limit_name}"
            if self._use_redis:
                await self.redis.delete(key)
            else:
                await self.memory_limiter.reset(key)
        else:
            # Reset all limits for this identifier
            for limit_config in self.DEFAULT_LIMITS:
                key = f"ratelimit:{identifier}:{limit_config.name}"
                if self._use_redis:
                    await self.redis.delete(key)
                else:
                    await self.memory_limiter.reset(key)

        logger.info(f"Rate limit reset for {identifier} ({limit_name or 'all'})")

    async def get_status(self, identifier: str) -> Dict[str, Dict]:
        """
        Get current rate limit status for an identifier.

        Returns status for all configured limits.
        """
        status = {}

        for limit_config in self.DEFAULT_LIMITS:
            key = f"ratelimit:{identifier}:{limit_config.name}"

            if self._use_redis:
                result = await self._get_redis_status(key, limit_config.requests, limit_config.window)
            else:
                # Check without incrementing
                now = time.time()
                cutoff = now - limit_config.window
                requests = self.memory_limiter._requests.get(key, [])
                requests = [ts for ts in requests if ts > cutoff]

                remaining = max(0, limit_config.requests - len(requests))
                reset_at = requests[0] + limit_config.window if requests else now + limit_config.window

                result = {
                    "remaining": remaining,
                    "limit": limit_config.requests,
                    "window": limit_config.window,
                    "reset_at": datetime.fromtimestamp(reset_at).isoformat()
                }

            status[limit_config.name] = result

        return status

    async def _get_redis_status(self, key: str, limit: int, window: int) -> Dict:
        """Get rate limit status from Redis without incrementing."""
        try:
            now = time.time()
            cutoff = now - window

            # Remove old entries
            await self.redis.zremrangebyscore(key, 0, cutoff)

            # Count current requests
            count = await self.redis.zcard(key)

            remaining = max(0, limit - count)

            # Get oldest request
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                reset_at = oldest[0][1] + window
            else:
                reset_at = now + window

            return {
                "remaining": remaining,
                "limit": limit,
                "window": window,
                "reset_at": datetime.fromtimestamp(reset_at).isoformat()
            }
        except Exception as e:
            logger.error(f"Redis status check failed: {e}")
            return {
                "remaining": limit,
                "limit": limit,
                "window": window,
                "reset_at": datetime.fromtimestamp(now + window).isoformat()
            }

    async def _cleanup_loop(self):
        """Background task to cleanup expired entries."""
        while True:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes

                if not self._use_redis:
                    await self.memory_limiter.cleanup_expired()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in rate limiter cleanup loop: {e}", exc_info=True)

    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        stats = {
            "backend": "redis" if self._use_redis else "memory",
            "default_limits": [
                {
                    "name": lc.name,
                    "requests": lc.requests,
                    "window": lc.window
                }
                for lc in self.DEFAULT_LIMITS
            ],
            "anonymous_limits": [
                {
                    "name": lc.name,
                    "requests": lc.requests,
                    "window": lc.window
                }
                for lc in self.ANONYMOUS_LIMITS
            ]
        }

        if not self._use_redis:
            stats["memory_stats"] = self.memory_limiter.get_stats()

        return stats


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter

    if _rate_limiter is None:
        # Try to get Redis client
        try:
            from app.core.redis import get_redis_client
            redis_client = get_redis_client()
            _rate_limiter = RateLimiter(redis_client=redis_client)
        except Exception as e:
            logger.warning(f"Could not initialize Redis for rate limiting: {e}")
            logger.warning("Using in-memory rate limiting (not suitable for multi-instance)")
            _rate_limiter = RateLimiter(redis_client=None)

    return _rate_limiter


async def init_rate_limiter():
    """Initialize rate limiter."""
    limiter = get_rate_limiter()
    await limiter.start()
    logger.info("Rate limiter initialized")


async def shutdown_rate_limiter():
    """Shutdown rate limiter."""
    limiter = get_rate_limiter()
    await limiter.stop()
    logger.info("Rate limiter shutdown")
