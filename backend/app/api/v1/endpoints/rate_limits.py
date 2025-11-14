"""
Rate Limit Management Endpoints (PDCA #21)

Endpoints for monitoring and managing rate limits.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from app.core.deps import get_current_user, get_current_active_superuser
from app.models.user import User
from app.services.rate_limiter import get_rate_limiter

router = APIRouter()
logger = logging.getLogger(__name__)


class RateLimitStatus(BaseModel):
    """Rate limit status response."""
    identifier: str
    is_authenticated: bool
    limits: Dict[str, Dict[str, Any]]


class RateLimitReset(BaseModel):
    """Rate limit reset request."""
    identifier: str = Field(..., description="User ID or IP address to reset")
    limit_name: Optional[str] = Field(None, description="Specific limit to reset (None = all)")


class RateLimitStats(BaseModel):
    """Rate limiter statistics."""
    backend: str
    default_limits: list
    anonymous_limits: list
    memory_stats: Optional[Dict[str, int]] = None


@router.get("/status", response_model=RateLimitStatus)
async def get_my_rate_limit_status(
    current_user: User = Depends(get_current_user)
) -> RateLimitStatus:
    """
    Get current user's rate limit status.

    Shows remaining requests for all configured limits.

    **Returns**:
    ```json
    {
        "identifier": "user:abc-123",
        "is_authenticated": true,
        "limits": {
            "per_second": {
                "remaining": 8,
                "limit": 10,
                "window": 1,
                "reset_at": "2025-01-15T10:30:00"
            },
            "per_minute": {
                "remaining": 95,
                "limit": 100,
                "window": 60,
                "reset_at": "2025-01-15T10:31:00"
            }
        }
    }
    ```
    """
    limiter = get_rate_limiter()
    identifier = f"user:{current_user.id}"

    status_data = await limiter.get_status(identifier)

    return RateLimitStatus(
        identifier=identifier,
        is_authenticated=True,
        limits=status_data
    )


@router.get("/status/{identifier}", response_model=RateLimitStatus)
async def get_rate_limit_status(
    identifier: str,
    current_user: User = Depends(get_current_active_superuser)
) -> RateLimitStatus:
    """
    Get rate limit status for any identifier (admin only).

    **Requires**: Superuser role

    **Parameters**:
    - `identifier`: User ID (with "user:" prefix) or IP address (with "ip:" prefix)

    **Example**: `/api/v1/rate-limits/status/user:abc-123`

    **Returns**: Same format as `/status` endpoint
    """
    limiter = get_rate_limiter()

    # Validate identifier format
    if not (identifier.startswith("user:") or identifier.startswith("ip:")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identifier must start with 'user:' or 'ip:'"
        )

    status_data = await limiter.get_status(identifier)
    is_authenticated = identifier.startswith("user:")

    return RateLimitStatus(
        identifier=identifier,
        is_authenticated=is_authenticated,
        limits=status_data
    )


@router.post("/reset")
async def reset_rate_limit(
    reset_data: RateLimitReset,
    current_user: User = Depends(get_current_active_superuser)
) -> Dict[str, str]:
    """
    Reset rate limit for a user or IP address (admin only).

    **Requires**: Superuser role

    **Use Cases**:
    - Unblock a user who hit rate limits
    - Clear limits after fixing an issue
    - Testing rate limiting behavior

    **Request Body**:
    ```json
    {
        "identifier": "user:abc-123",
        "limit_name": "per_minute"  // Optional - resets specific limit
    }
    ```

    **Response**:
    ```json
    {
        "message": "Rate limit reset for user:abc-123 (per_minute)"
    }
    ```
    """
    limiter = get_rate_limiter()

    # Validate identifier format
    if not (reset_data.identifier.startswith("user:") or reset_data.identifier.startswith("ip:")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identifier must start with 'user:' or 'ip:'"
        )

    await limiter.reset(reset_data.identifier, reset_data.limit_name)

    logger.info(
        f"Rate limit reset by {current_user.email} for "
        f"{reset_data.identifier} ({reset_data.limit_name or 'all'})"
    )

    return {
        "message": f"Rate limit reset for {reset_data.identifier} "
                   f"({reset_data.limit_name or 'all'})"
    }


@router.post("/reset-my-limits")
async def reset_my_rate_limits(
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Reset current user's rate limits.

    Allows users to reset their own rate limits.
    Useful for testing or if user believes limits are incorrect.

    **Note**: This endpoint itself has rate limiting to prevent abuse.

    **Response**:
    ```json
    {
        "message": "Your rate limits have been reset"
    }
    ```
    """
    limiter = get_rate_limiter()
    identifier = f"user:{current_user.id}"

    await limiter.reset(identifier)

    logger.info(f"User {current_user.email} reset their own rate limits")

    return {
        "message": "Your rate limits have been reset"
    }


@router.get("/stats", response_model=RateLimitStats)
async def get_rate_limiter_stats(
    current_user: User = Depends(get_current_active_superuser)
) -> RateLimitStats:
    """
    Get rate limiter statistics (admin only).

    **Requires**: Superuser role

    **Returns**:
    ```json
    {
        "backend": "redis",  // or "memory"
        "default_limits": [
            {
                "name": "per_second",
                "requests": 10,
                "window": 1
            },
            ...
        ],
        "anonymous_limits": [...],
        "memory_stats": {  // Only if using in-memory backend
            "total_keys": 1234,
            "total_requests_tracked": 5678
        }
    }
    ```

    **Use Cases**:
    - Monitor rate limiter performance
    - Check which backend is being used (Redis vs memory)
    - See configured limits
    - Debug rate limiting issues
    """
    limiter = get_rate_limiter()
    stats = limiter.get_stats()

    return RateLimitStats(**stats)


@router.get("/config")
async def get_rate_limit_config(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get rate limit configuration.

    Shows configured rate limits that apply to the current user.

    **Returns**:
    ```json
    {
        "user_type": "authenticated",
        "limits": [
            {
                "name": "per_second",
                "requests": 10,
                "window": 1,
                "description": "10 requests per second"
            },
            {
                "name": "per_minute",
                "requests": 100,
                "window": 60,
                "description": "100 requests per minute"
            },
            {
                "name": "per_hour",
                "requests": 1000,
                "window": 3600,
                "description": "1000 requests per hour"
            },
            {
                "name": "per_day",
                "requests": 10000,
                "window": 86400,
                "description": "10000 requests per day"
            }
        ],
        "headers": {
            "X-RateLimit-Limit": "Total requests allowed in window",
            "X-RateLimit-Remaining": "Requests remaining in current window",
            "X-RateLimit-Reset": "Unix timestamp when limit resets",
            "Retry-After": "Seconds until retry (only when rate limited)"
        }
    }
    ```
    """
    from app.services.rate_limiter import RateLimiter

    limits_info = []
    for limit in RateLimiter.DEFAULT_LIMITS:
        limits_info.append({
            "name": limit.name,
            "requests": limit.requests,
            "window": limit.window,
            "description": f"{limit.requests} requests per {limit.window} seconds"
        })

    return {
        "user_type": "authenticated",
        "limits": limits_info,
        "headers": {
            "X-RateLimit-Limit": "Total requests allowed in window",
            "X-RateLimit-Remaining": "Requests remaining in current window",
            "X-RateLimit-Reset": "Unix timestamp when limit resets",
            "Retry-After": "Seconds until retry (only when rate limited)"
        }
    }


@router.get("/health")
async def rate_limiter_health() -> Dict[str, str]:
    """
    Health check for rate limiter.

    **Returns**:
    ```json
    {
        "status": "ok",
        "service": "optiflow-rate-limiter"
    }
    ```
    """
    return {
        "status": "ok",
        "service": "optiflow-rate-limiter"
    }
