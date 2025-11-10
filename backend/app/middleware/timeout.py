"""
Request timeout middleware to prevent indefinite hangs
"""
import asyncio
import async_timeout
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

logger = logging.getLogger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce request timeouts and prevent indefinite hangs.

    If a request takes longer than REQUEST_TIMEOUT_SECONDS, it will be
    cancelled and return a 504 Gateway Timeout response.
    """

    def __init__(self, app, timeout_seconds: int = None):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds or settings.REQUEST_TIMEOUT_SECONDS

    async def dispatch(self, request: Request, call_next):
        """
        Process request with timeout protection
        """
        # Skip timeout for certain endpoints
        skip_timeout_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]

        # Skip WebSocket connections
        if request.url.path.startswith("/ws"):
            return await call_next(request)

        # Skip health check and metrics endpoints
        if any(request.url.path.startswith(path) for path in skip_timeout_paths):
            return await call_next(request)

        try:
            # Execute request with timeout
            async with async_timeout.timeout(self.timeout_seconds):
                response = await call_next(request)
                return response

        except asyncio.TimeoutError:
            # Request exceeded timeout
            logger.error(
                f"Request timeout: {request.method} {request.url.path} "
                f"exceeded {self.timeout_seconds} seconds"
            )

            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "detail": f"Request processing exceeded timeout of {self.timeout_seconds} seconds",
                    "error": "gateway_timeout",
                    "path": str(request.url.path),
                    "method": request.method,
                },
            )

        except Exception as e:
            # Catch any other errors
            logger.error(f"Unexpected error in timeout middleware: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal server error",
                    "error": "internal_error",
                },
            )
