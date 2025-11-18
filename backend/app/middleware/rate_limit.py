"""
Rate Limiting Middleware (PDCA #21)

FastAPI middleware for automatic rate limiting on all endpoints.

Features:
- Automatic rate limiting on all requests
- Per-user limits for authenticated requests
- Per-IP limits for anonymous requests
- Standard rate limit headers (X-RateLimit-*)
- Configurable per-endpoint limits via decorators
- Bypass option for internal/health endpoints
"""

import logging
from typing import Optional, List, Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from functools import wraps

from app.services.rate_limiter import get_rate_limiter, RateLimitConfig

logger = logging.getLogger(__name__)


# ========================================
# INTERNAL IPS - Whitelist (No Rate Limiting)
# ========================================
# IPs that bypass rate limiting (internal services, monitoring, health checks)
INTERNAL_IPS = [
    "127.0.0.1",      # Localhost (autonomous agent, health checks)
    "::1",            # IPv6 localhost
    "172.17.0.0/16",  # Docker bridge network (default)
    "172.18.0.0/16",  # Docker custom networks
    "10.0.0.0/8",     # Private network (if used)
]

def is_internal_ip(ip: str) -> bool:
    """Check if IP is in internal whitelist."""
    from ipaddress import ip_address, ip_network
    
    try:
        client_ip = ip_address(ip)
        for allowed in INTERNAL_IPS:
            if "/" in allowed:  # CIDR notation
                if client_ip in ip_network(allowed, strict=False):
                    return True
            else:  # Single IP
                if str(client_ip) == allowed:
                    return True
        return False
    except ValueError:
        # Invalid IP format
        return False


# Endpoints that bypass rate limiting
RATE_LIMIT_BYPASS = [
    "/api/health",  # Health check endpoint
    "/api/v1/health",
    "/api/v1/auth",  # All auth endpoints (login, register, me)
    "/api/v1/simulator",  # Simulator endpoints (dev/test)
    "/api/v1/ml",  # ML models endpoints
    "/api/v1/alarms",  # Alarms endpoints
    "/api/v1/tags",  # Tags and timeseries endpoints
    "/api/v1/devices",  # Devices endpoints
    "/api/v1/executive",  # Executive dashboard endpoints
    "/api/v1/timeseries",  # Timeseries endpoints
    "/api/v1/prometheus/metrics",
    "/api/v1/prometheus/health",
    "/graphql",  # GraphQL endpoint (PDCA #27)
    "/docs",
    "/redoc",
    "/openapi.json",
]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limits on all requests.

    Applies rate limits based on:
    - User ID (for authenticated requests)
    - IP address (for anonymous requests)

    Adds standard rate limit headers to responses:
    - X-RateLimit-Limit: Total requests allowed in window
    - X-RateLimit-Remaining: Requests remaining in current window
    - X-RateLimit-Reset: Unix timestamp when limit resets
    - Retry-After: Seconds until retry (only when rate limited)
    """

    async def dispatch(self, request: Request, call_next):
        """Process request and apply rate limiting."""

        # Skip rate limiting for internal IPs (autonomous agent, health checks, monitoring)
        client_ip = request.client.host if request.client else "unknown"
        if is_internal_ip(client_ip):
            logger.debug(f"⚪ Skipping rate limit for internal IP: {client_ip}")
            return await call_next(request)

        # Skip rate limiting for OPTIONS requests (CORS preflight)
        # Return 200 OK to properly handle CORS preflight
        if request.method == "OPTIONS":
            # Let CORSMiddleware handle the response
            response = await call_next(request)
            # If it's a 405, convert to 200 for proper CORS handling
            if response.status_code == 405:
                from fastapi.responses import Response
                return Response(status_code=200, headers=dict(response.headers))
            return response

        # Check if endpoint should bypass rate limiting
        if self._should_bypass(request.url.path):
            return await call_next(request)

        # Get rate limiter
        limiter = get_rate_limiter()

        # Determine identifier (user_id or IP)
        identifier, is_authenticated = await self._get_identifier(request)

        # Check rate limit
        try:
            allowed, result = await limiter.check_rate_limit(
                identifier=identifier,
                is_authenticated=is_authenticated
            )

            if not allowed:
                # Rate limit exceeded
                logger.warning(
                    f"Rate limit exceeded for {identifier} "
                    f"(authenticated: {is_authenticated}): "
                    f"{result.limit} requests per {result.window}s"
                )

                headers = {
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(result.reset_at)),
                    "Retry-After": str(result.retry_after or 60),
                }

                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded. Please try again later.",
                        "retry_after": result.retry_after,
                        "limit": result.limit,
                        "window": result.window
                    },
                    headers=headers
                )

            # Allowed - process request
            response = await call_next(request)

            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(result.limit)
            response.headers["X-RateLimit-Remaining"] = str(result.remaining)
            response.headers["X-RateLimit-Reset"] = str(int(result.reset_at))

            return response

        except Exception as e:
            logger.error(f"Rate limiting error: {e}", exc_info=True)
            # On error, allow request to proceed (fail open)
            return await call_next(request)

    def _should_bypass(self, path: str) -> bool:
        """Check if path should bypass rate limiting."""
        for bypass_path in RATE_LIMIT_BYPASS:
            if path.startswith(bypass_path):
                return True
        return False

    async def _get_identifier(self, request: Request) -> tuple[str, bool]:
        """
        Get identifier for rate limiting.

        Returns:
            Tuple of (identifier: str, is_authenticated: bool)
        """
        # Try to get user from request state
        user = getattr(request.state, "user", None)

        if user:
            # Authenticated user - use user_id
            user_id = getattr(user, "id", None)
            if user_id:
                return f"user:{user_id}", True

        # Anonymous user - use IP address
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP if multiple
            ip = forwarded_for.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}", False


# Decorator for custom rate limits on specific endpoints
def rate_limit(
    requests: int,
    window: int,
    per_user: bool = True
):
    """
    Decorator to apply custom rate limit to an endpoint.

    Args:
        requests: Number of requests allowed
        window: Time window in seconds
        per_user: If True, limit per user; if False, limit per endpoint globally

    Example:
        @router.post("/expensive-operation")
        @rate_limit(requests=10, window=3600)  # 10 requests per hour
        async def expensive_operation():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                # Try to find in kwargs
                request = kwargs.get("request")

            if request is None:
                logger.warning("Could not find Request object for rate limiting")
                return await func(*args, **kwargs)

            # Get identifier
            middleware = RateLimitMiddleware(app=None)
            identifier, is_authenticated = await middleware._get_identifier(request)

            if not per_user:
                # Global limit for this endpoint
                identifier = f"endpoint:{request.url.path}"

            # Check rate limit
            limiter = get_rate_limiter()
            custom_limits = [RateLimitConfig(
                requests=requests,
                window=window,
                name=f"custom_{window}s"
            )]

            allowed, result = await limiter.check_rate_limit(
                identifier=identifier,
                limits=custom_limits,
                is_authenticated=is_authenticated
            )

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {requests} requests per {window}s",
                    headers={
                        "X-RateLimit-Limit": str(result.limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(result.reset_at)),
                        "Retry-After": str(result.retry_after or 60),
                    }
                )

            # Execute endpoint
            return await func(*args, **kwargs)

        return wrapper
    return decorator


# Convenience decorators for common rate limits
def rate_limit_strict(func: Callable):
    """Very strict rate limit: 5 requests per minute."""
    return rate_limit(requests=5, window=60)(func)


def rate_limit_moderate(func: Callable):
    """Moderate rate limit: 30 requests per minute."""
    return rate_limit(requests=30, window=60)(func)


def rate_limit_relaxed(func: Callable):
    """Relaxed rate limit: 100 requests per minute."""
    return rate_limit(requests=100, window=60)(func)
