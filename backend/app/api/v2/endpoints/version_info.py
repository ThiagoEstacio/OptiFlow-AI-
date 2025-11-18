"""
API Version Information Endpoint (PDCA #22)

Provides information about API versions, deprecation, and migration paths.
"""

from fastapi import APIRouter, Request
from typing import Dict, List, Any
from datetime import datetime

from app.core.versioning import (
    APIVersion,
    APIVersionRegistry,
    VersionNegotiator,
    VersionStatus
)

router = APIRouter()


@router.get("/info")
async def get_version_info(request: Request) -> Dict[str, Any]:
    """
    Get information about current API version.

    **Returns**:
    ```json
    {
        "version": "v2",
        "status": "current",
        "released": "2025-01-15T00:00:00",
        "description": "Enhanced API with versioning and rate limiting"
    }
    ```
    """
    version = VersionNegotiator.get_version_from_request(request)
    info = APIVersionRegistry.get_version_info(version)

    return {
        "version": info.version.value,
        "status": info.status.value,
        "released": info.released.isoformat(),
        "deprecated_on": info.deprecated_on.isoformat() if info.deprecated_on else None,
        "sunset_on": info.sunset_on.isoformat() if info.sunset_on else None,
        "description": info.description
    }


@router.get("/all")
async def get_all_versions() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get information about all API versions.

    **Returns**:
    ```json
    {
        "versions": [
            {
                "version": "v1",
                "status": "supported",
                "released": "2025-01-01T00:00:00",
                "deprecated_on": "2025-06-01T00:00:00",
                "sunset_on": "2025-12-01T00:00:00",
                "description": "Original API version"
            },
            {
                "version": "v2",
                "status": "current",
                "released": "2025-01-15T00:00:00",
                "description": "Enhanced API version"
            }
        ],
        "current": "v2"
    }
    ```
    """
    versions = []

    for version in APIVersion:
        info = APIVersionRegistry.get_version_info(version)
        versions.append({
            "version": info.version.value,
            "status": info.status.value,
            "released": info.released.isoformat(),
            "deprecated_on": info.deprecated_on.isoformat() if info.deprecated_on else None,
            "sunset_on": info.sunset_on.isoformat() if info.sunset_on else None,
            "description": info.description
        })

    return {
        "versions": versions,
        "current": APIVersionRegistry.get_current_version().value
    }


@router.get("/deprecation")
async def get_deprecation_info(request: Request) -> Dict[str, Any]:
    """
    Get deprecation information for current API version.

    **Returns**:
    ```json
    {
        "version": "v1",
        "is_deprecated": true,
        "warning": "API version v1 is deprecated...",
        "sunset_on": "2025-12-01T00:00:00",
        "days_until_sunset": 180,
        "recommended_version": "v2",
        "migration_guide": "/docs/migration/v1-to-v2"
    }
    ```
    """
    version = VersionNegotiator.get_version_from_request(request)
    info = APIVersionRegistry.get_version_info(version)

    is_deprecated = APIVersionRegistry.is_deprecated(version)
    warning = APIVersionRegistry.get_deprecation_warning(version)

    days_until_sunset = None
    if info.sunset_on:
        days_until_sunset = (info.sunset_on - datetime.now()).days

    return {
        "version": version.value,
        "is_deprecated": is_deprecated,
        "warning": warning,
        "sunset_on": info.sunset_on.isoformat() if info.sunset_on else None,
        "days_until_sunset": days_until_sunset,
        "recommended_version": APIVersionRegistry.get_current_version().value,
        "migration_guide": f"/docs/migration/{version}-to-{APIVersionRegistry.get_current_version()}"
    }


@router.get("/changelog")
async def get_changelog() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get changelog between API versions.

    **Returns**:
    ```json
    {
        "changes": [
            {
                "version": "v2",
                "released": "2025-01-15T00:00:00",
                "changes": [
                    "Added rate limiting support",
                    "Added API versioning",
                    "Improved error responses",
                    "Enhanced monitoring"
                ],
                "breaking_changes": [],
                "deprecations": []
            }
        ]
    }
    ```
    """
    return {
        "changes": [
            {
                "version": "v2",
                "released": "2025-01-15T00:00:00",
                "changes": [
                    "Added rate limiting per user/IP",
                    "Added API versioning with deprecation warnings",
                    "Added Prometheus metrics export",
                    "Added WebSocket connection pooling",
                    "Improved frontend bundle optimization",
                    "Enhanced circuit breaker patterns",
                    "Improved error responses with detailed messages"
                ],
                "breaking_changes": [],
                "deprecations": [],
                "migrations": [
                    {
                        "description": "No breaking changes - V2 is fully backward compatible with V1",
                        "action_required": False
                    }
                ]
            },
            {
                "version": "v1",
                "released": "2025-01-01T00:00:00",
                "changes": [
                    "Initial API release",
                    "Authentication and authorization",
                    "Asset management",
                    "Time-series data collection",
                    "Alarm management",
                    "Analytics and insights"
                ],
                "breaking_changes": [],
                "deprecations": [
                    {
                        "endpoint": "All V1 endpoints",
                        "deprecated_on": "2025-06-01",
                        "sunset_on": "2025-12-01",
                        "reason": "V2 provides enhanced features and better performance",
                        "replacement": "Migrate to /api/v2"
                    }
                ]
            }
        ]
    }


@router.get("/health")
async def version_health() -> Dict[str, str]:
    """
    Health check for versioning system.

    **Returns**:
    ```json
    {
        "status": "ok",
        "service": "api-versioning"
    }
    ```
    """
    return {
        "status": "ok",
        "service": "api-versioning"
    }
