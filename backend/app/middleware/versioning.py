"""
API Versioning Middleware (PDCA #22)

Automatically handles API version negotiation and headers.
"""

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.versioning import (
    VersionNegotiator,
    APIVersionRegistry,
    APIVersion
)

logger = logging.getLogger(__name__)


class VersioningMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle API versioning.

    Features:
    - Automatic version detection from request
    - Version headers in response
    - Deprecation warnings
    - Sunset notifications
    """

    async def dispatch(self, request: Request, call_next):
        """Process request and add version headers."""

        # Detect API version from request
        try:
            version = VersionNegotiator.get_version_from_request(request)

            # Store version in request state for later use
            request.state.api_version = version

            # Check if version is still supported
            if not APIVersionRegistry.is_supported(version):
                from fastapi.responses import JSONResponse
                from fastapi import status

                return JSONResponse(
                    status_code=status.HTTP_410_GONE,
                    content={
                        "detail": f"API version {version} is no longer supported.",
                        "current_version": APIVersionRegistry.get_current_version().value,
                        "supported_versions": [
                            v.value for v in APIVersion
                            if APIVersionRegistry.is_supported(v)
                        ]
                    },
                    headers={
                        "API-Version": version.value,
                        "API-Current-Version": APIVersionRegistry.get_current_version().value
                    }
                )

            # Process request
            response = await call_next(request)

            # Add version headers to response
            VersionNegotiator.add_version_headers(response, version)

            return response

        except Exception as e:
            logger.error(f"Error in versioning middleware: {e}", exc_info=True)
            # On error, proceed without version handling
            return await call_next(request)
