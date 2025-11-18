"""
API Versioning System (PDCA #22)

Manages API version negotiation and deprecation.

Features:
- Multiple API versions (v1, v2, v3...)
- Version negotiation (URL, header, query param)
- Deprecation warnings
- Backward compatibility
- Version-specific routing
"""

import logging
from typing import Optional, Callable, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from fastapi import Request, Response, HTTPException, status
from functools import wraps

logger = logging.getLogger(__name__)


class APIVersion(str, Enum):
    """Supported API versions."""
    V1 = "v1"
    V2 = "v2"
    # V3 = "v3"  # Future versions


class VersionStatus(str, Enum):
    """Version lifecycle status."""
    CURRENT = "current"          # Latest stable version
    SUPPORTED = "supported"      # Older version, still supported
    DEPRECATED = "deprecated"    # Will be removed soon
    SUNSET = "sunset"           # No longer supported


@dataclass
class VersionInfo:
    """Version metadata."""
    version: APIVersion
    status: VersionStatus
    released: datetime
    deprecated_on: Optional[datetime] = None
    sunset_on: Optional[datetime] = None
    description: str = ""


class APIVersionRegistry:
    """
    Registry of API versions with their metadata.

    Tracks version lifecycle and deprecation schedules.
    """

    # Version registry with metadata
    VERSIONS = {
        APIVersion.V1: VersionInfo(
            version=APIVersion.V1,
            status=VersionStatus.SUPPORTED,
            released=datetime(2025, 1, 1),
            deprecated_on=datetime(2025, 6, 1),  # Deprecated in 6 months
            sunset_on=datetime(2025, 12, 1),     # Sunset in 12 months
            description="Original API version with basic features"
        ),
        APIVersion.V2: VersionInfo(
            version=APIVersion.V2,
            status=VersionStatus.CURRENT,
            released=datetime(2025, 1, 15),
            description="Enhanced API with rate limiting, versioning, and improved performance"
        ),
    }

    @classmethod
    def get_version_info(cls, version: APIVersion) -> VersionInfo:
        """Get metadata for a version."""
        if version not in cls.VERSIONS:
            raise ValueError(f"Unknown API version: {version}")
        return cls.VERSIONS[version]

    @classmethod
    def get_current_version(cls) -> APIVersion:
        """Get the current (latest) API version."""
        for version, info in cls.VERSIONS.items():
            if info.status == VersionStatus.CURRENT:
                return version
        # Fallback to V1 if no current version set
        return APIVersion.V1

    @classmethod
    def is_supported(cls, version: APIVersion) -> bool:
        """Check if version is still supported."""
        info = cls.get_version_info(version)
        return info.status in [VersionStatus.CURRENT, VersionStatus.SUPPORTED, VersionStatus.DEPRECATED]

    @classmethod
    def is_deprecated(cls, version: APIVersion) -> bool:
        """Check if version is deprecated."""
        info = cls.get_version_info(version)
        return info.status == VersionStatus.DEPRECATED

    @classmethod
    def get_deprecation_warning(cls, version: APIVersion) -> Optional[str]:
        """Get deprecation warning message for version."""
        info = cls.get_version_info(version)

        if info.status == VersionStatus.DEPRECATED and info.sunset_on:
            days_until_sunset = (info.sunset_on - datetime.now()).days
            return (
                f"API version {version} is deprecated and will be sunset on "
                f"{info.sunset_on.strftime('%Y-%m-%d')} ({days_until_sunset} days remaining). "
                f"Please migrate to version {cls.get_current_version()}."
            )

        return None


class VersionNegotiator:
    """
    Negotiates API version from request.

    Version detection order:
    1. URL path (/api/v2/...)
    2. Header (API-Version: v2)
    3. Query parameter (?version=v2)
    4. Default to current version
    """

    @staticmethod
    def get_version_from_request(request: Request) -> APIVersion:
        """
        Extract API version from request.

        Args:
            request: FastAPI request object

        Returns:
            Detected API version
        """
        # 1. Try URL path (most common)
        path = request.url.path
        for version in APIVersion:
            if f"/api/{version}/" in path or path.endswith(f"/api/{version}"):
                logger.debug(f"Version detected from URL: {version}")
                return version

        # 2. Try custom header
        version_header = request.headers.get("API-Version") or request.headers.get("X-API-Version")
        if version_header:
            try:
                version = APIVersion(version_header.lower())
                logger.debug(f"Version detected from header: {version}")
                return version
            except ValueError:
                logger.warning(f"Invalid API version in header: {version_header}")

        # 3. Try query parameter
        version_param = request.query_params.get("version") or request.query_params.get("api_version")
        if version_param:
            try:
                version = APIVersion(version_param.lower())
                logger.debug(f"Version detected from query param: {version}")
                return version
            except ValueError:
                logger.warning(f"Invalid API version in query param: {version_param}")

        # 4. Default to current version
        current = APIVersionRegistry.get_current_version()
        logger.debug(f"Using default API version: {current}")
        return current

    @staticmethod
    def add_version_headers(response: Response, version: APIVersion):
        """
        Add version information to response headers.

        Headers added:
        - API-Version: Current version used
        - API-Deprecated: Warning if version is deprecated
        - API-Sunset: Date when version will be sunset
        - API-Current-Version: Latest available version
        """
        info = APIVersionRegistry.get_version_info(version)

        # Always add current version
        response.headers["API-Version"] = version.value
        response.headers["API-Current-Version"] = APIVersionRegistry.get_current_version().value

        # Add deprecation warning
        warning = APIVersionRegistry.get_deprecation_warning(version)
        if warning:
            response.headers["API-Deprecated"] = "true"
            response.headers["Warning"] = f'299 - "{warning}"'

            if info.sunset_on:
                # RFC 8594 Sunset header
                response.headers["Sunset"] = info.sunset_on.strftime("%a, %d %b %Y %H:%M:%S GMT")


def require_version(
    min_version: APIVersion,
    max_version: Optional[APIVersion] = None
) -> Callable:
    """
    Decorator to require specific API version for endpoint.

    Args:
        min_version: Minimum API version required
        max_version: Maximum API version (None = no max)

    Example:
        @router.get("/new-feature")
        @require_version(APIVersion.V2)
        async def new_feature():
            # Only available in V2+
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request in args/kwargs
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                request = kwargs.get("request")

            if request is None:
                logger.warning("Could not find Request object for version check")
                return await func(*args, **kwargs)

            # Check version
            version = VersionNegotiator.get_version_from_request(request)

            # Convert to comparable (v1 < v2 < v3)
            version_num = int(version.value[1:])  # "v2" -> 2
            min_num = int(min_version.value[1:])

            if version_num < min_num:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"This endpoint requires API version {min_version} or higher. "
                           f"You are using version {version}.",
                    headers={
                        "API-Version": version.value,
                        "API-Min-Version": min_version.value,
                        "API-Current-Version": APIVersionRegistry.get_current_version().value
                    }
                )

            if max_version:
                max_num = int(max_version.value[1:])
                if version_num > max_num:
                    raise HTTPException(
                        status_code=status.HTTP_410_GONE,
                        detail=f"This endpoint was removed in API version {max_version}. "
                               f"You are using version {version}.",
                        headers={
                            "API-Version": version.value,
                            "API-Max-Version": max_version.value
                        }
                    )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def deprecated_endpoint(
    deprecated_in: APIVersion,
    sunset_in: APIVersion,
    replacement: Optional[str] = None
) -> Callable:
    """
    Mark endpoint as deprecated.

    Args:
        deprecated_in: Version where endpoint was deprecated
        sunset_in: Version where endpoint will be removed
        replacement: Suggested replacement endpoint

    Example:
        @router.get("/old-endpoint")
        @deprecated_endpoint(
            deprecated_in=APIVersion.V2,
            sunset_in=APIVersion.V3,
            replacement="/api/v2/new-endpoint"
        )
        async def old_endpoint():
            # Still works but shows deprecation warning
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request in args/kwargs
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                request = kwargs.get("request")

            # Log deprecation warning
            logger.warning(
                f"Deprecated endpoint called: {func.__name__} "
                f"(deprecated in {deprecated_in}, will be removed in {sunset_in})"
            )

            # Execute function
            result = await func(*args, **kwargs)

            # If result is a Response, add deprecation headers
            if isinstance(result, Response):
                result.headers["Deprecated"] = "true"
                result.headers["Sunset-Version"] = sunset_in.value

                warning_msg = f"This endpoint is deprecated and will be removed in {sunset_in}."
                if replacement:
                    warning_msg += f" Please use {replacement} instead."

                result.headers["Warning"] = f'299 - "{warning_msg}"'

            return result

        return wrapper
    return decorator


class VersionRegistry:
    """
    Global registry for version-specific implementations.

    Allows registering different implementations for different API versions.
    """

    _implementations: dict[str, dict[APIVersion, Callable]] = {}

    @classmethod
    def register(
        cls,
        endpoint: str,
        version: APIVersion,
        implementation: Callable
    ):
        """Register a version-specific implementation."""
        if endpoint not in cls._implementations:
            cls._implementations[endpoint] = {}

        cls._implementations[endpoint][version] = implementation
        logger.info(f"Registered {endpoint} for API version {version}")

    @classmethod
    def get_implementation(
        cls,
        endpoint: str,
        version: APIVersion
    ) -> Optional[Callable]:
        """Get version-specific implementation."""
        if endpoint not in cls._implementations:
            return None

        return cls._implementations[endpoint].get(version)

    @classmethod
    def get_available_versions(cls, endpoint: str) -> list[APIVersion]:
        """Get list of versions that support this endpoint."""
        if endpoint not in cls._implementations:
            return []

        return list(cls._implementations[endpoint].keys())


def versioned_endpoint(endpoint_name: str):
    """
    Decorator to create version-aware endpoint.

    Automatically routes to version-specific implementation.

    Example:
        @router.get("/users")
        @versioned_endpoint("get_users")
        async def get_users_v1():
            # V1 implementation
            pass

        @router.get("/users")
        @versioned_endpoint("get_users")
        @require_version(APIVersion.V2)
        async def get_users_v2():
            # V2 implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        # Detect version from function name or decorator
        # For now, just register the function

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                request = kwargs.get("request")

            if request:
                version = VersionNegotiator.get_version_from_request(request)

                # Try to get version-specific implementation
                impl = VersionRegistry.get_implementation(endpoint_name, version)
                if impl:
                    return await impl(*args, **kwargs)

            # Fallback to current implementation
            return await func(*args, **kwargs)

        return wrapper
    return decorator
