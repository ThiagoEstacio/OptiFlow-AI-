"""
Security API Routes (Gateway - Simplified)
==========================================

Gateway security endpoints for token VALIDATION only.
Token GENERATION should be done via Backend API.

Architecture:
- Backend: Issues JWT tokens (/api/v1/auth/token)
- Gateway: Validates tokens (same JWT_SECRET)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import (
    get_current_user,
    get_security_status,
    AuthUser,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/security", tags=["Security"])


# ============================================
# Response Models
# ============================================

class SecurityStatusResponse(BaseModel):
    """Security status response"""
    api_key_enabled: bool
    api_key_configured: bool
    jwt_enabled: bool
    read_only_mode: bool
    ip_whitelist_enabled: bool
    ip_whitelist_count: int
    rate_limit_enabled: bool
    rate_limit_requests: int
    rate_limit_window_seconds: int


class WhoAmIResponse(BaseModel):
    """Current user info response"""
    id: str
    type: str
    roles: list
    ip: Optional[str]


# ============================================
# Endpoints
# ============================================

@router.get("/status", response_model=SecurityStatusResponse)
async def get_status():
    """
    Get security configuration status.

    Returns current security settings without revealing sensitive values.
    """
    return get_security_status()


@router.get("/whoami", response_model=WhoAmIResponse)
async def who_am_i(user: AuthUser = Depends(get_current_user)):
    """
    Get current authenticated user info.

    Returns information about the current request's authentication status.
    Validates the provided token (JWT or API Key).
    """
    return WhoAmIResponse(
        id=user.id,
        type=user.type,
        roles=user.roles,
        ip=user.ip
    )


@router.get("/health")
async def security_health_check(user: AuthUser = Depends(get_current_user)):
    """
    Security health check endpoint.

    Tests if authentication is working correctly.
    """
    return {
        "status": "ok",
        "authenticated": user.type != "anonymous",
        "auth_type": user.type,
        "message": f"Hello {user.id}! Your roles: {user.roles}",
        "note": "Token generation available via Backend API: POST /api/v1/auth/token"
    }


# ============================================
# DEPRECATED ENDPOINTS
# ============================================
# The following endpoints have been moved to Backend:
#
# POST /security/token          -> Backend: POST /api/v1/auth/token
# POST /security/api-key/generate -> Backend: POST /api/v1/auth/api-key
#
# To generate tokens, use the Backend API:
#   curl -X POST http://backend:8000/api/v1/auth/token \
#     -H "Content-Type: application/json" \
#     -d '{"username": "admin", "password": "***"}'
# ============================================
