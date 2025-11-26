"""
Gateway Security Module
=======================

Provides authentication and authorization for Gateway APIs.

Supported methods:
1. API Key (for server-to-server communication)
2. JWT (for user/UI access)
3. mTLS (for production deployments)

All methods are optional and can be enabled via environment variables.
"""

import os
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
from functools import wraps

from fastapi import HTTPException, Depends, Request, Security
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ============================================
# Configuration
# ============================================

class SecurityConfig:
    """Security configuration from environment variables"""

    # API Key authentication
    API_KEY_ENABLED: bool = os.getenv("GATEWAY_API_KEY_ENABLED", "false").lower() == "true"
    API_KEY: str = os.getenv("GATEWAY_API_KEY", "")
    API_KEY_HEADER: str = "X-API-Key"

    # JWT authentication
    JWT_ENABLED: bool = os.getenv("GATEWAY_JWT_ENABLED", "false").lower() == "true"
    JWT_SECRET: str = os.getenv("GATEWAY_JWT_SECRET", secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = int(os.getenv("GATEWAY_JWT_EXPIRY_HOURS", "24"))

    # Read-only mode (block write operations)
    READ_ONLY_MODE: bool = os.getenv("GATEWAY_READ_ONLY_MODE", "false").lower() == "true"

    # IP whitelist
    IP_WHITELIST_ENABLED: bool = os.getenv("GATEWAY_IP_WHITELIST_ENABLED", "false").lower() == "true"
    IP_WHITELIST: list = os.getenv("GATEWAY_IP_WHITELIST", "").split(",") if os.getenv("GATEWAY_IP_WHITELIST") else []

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("GATEWAY_RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("GATEWAY_RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("GATEWAY_RATE_LIMIT_WINDOW", "60"))  # seconds


config = SecurityConfig()


# ============================================
# Security Schemes
# ============================================

api_key_header = APIKeyHeader(name=config.API_KEY_HEADER, auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


# ============================================
# Authentication Models
# ============================================

class AuthUser(BaseModel):
    """Authenticated user/client information"""
    id: str
    type: str  # "api_key", "jwt", "anonymous"
    roles: list = []
    ip: Optional[str] = None


# ============================================
# JWT Functions
# ============================================

def create_jwt_token(subject: str, roles: list = None, expires_delta: timedelta = None) -> str:
    """Create a JWT token"""
    try:
        import jwt
    except ImportError:
        logger.error("PyJWT not installed. Run: pip install pyjwt")
        raise HTTPException(status_code=500, detail="JWT not available")

    if expires_delta is None:
        expires_delta = timedelta(hours=config.JWT_EXPIRY_HOURS)

    expire = datetime.utcnow() + expires_delta

    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        "roles": roles or [],
    }

    token = jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return token


def verify_jwt_token(token: str) -> Tuple[bool, Optional[dict]]:
    """Verify a JWT token"""
    try:
        import jwt
    except ImportError:
        return False, None

    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET,
            algorithms=[config.JWT_ALGORITHM]
        )
        return True, payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return False, None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return False, None


# ============================================
# Authentication Dependencies
# ============================================

async def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    # Check for X-Forwarded-For header (if behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # Check for X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct client
    if request.client:
        return request.client.host

    return "unknown"


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """Verify API key if provided"""
    if not config.API_KEY_ENABLED:
        return None

    if not api_key:
        return None

    if secrets.compare_digest(api_key, config.API_KEY):
        return api_key

    return None


async def verify_bearer_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> Optional[dict]:
    """Verify Bearer token (JWT) if provided"""
    if not config.JWT_ENABLED:
        return None

    if not credentials:
        return None

    valid, payload = verify_jwt_token(credentials.credentials)
    if valid:
        return payload

    return None


async def get_current_user(
    request: Request,
    api_key: Optional[str] = Depends(verify_api_key),
    jwt_payload: Optional[dict] = Depends(verify_bearer_token),
) -> AuthUser:
    """
    Get current authenticated user.

    Authentication is checked in order:
    1. API Key
    2. JWT Bearer token
    3. Anonymous (if security is disabled)
    """
    client_ip = await get_client_ip(request)

    # Check IP whitelist
    if config.IP_WHITELIST_ENABLED:
        if client_ip not in config.IP_WHITELIST and "127.0.0.1" not in config.IP_WHITELIST:
            logger.warning(f"Request from non-whitelisted IP: {client_ip}")
            raise HTTPException(
                status_code=403,
                detail="Access denied: IP not in whitelist"
            )

    # Check API Key authentication
    if api_key:
        return AuthUser(
            id="api_key_client",
            type="api_key",
            roles=["read", "write"],
            ip=client_ip
        )

    # Check JWT authentication
    if jwt_payload:
        return AuthUser(
            id=jwt_payload.get("sub", "unknown"),
            type="jwt",
            roles=jwt_payload.get("roles", []),
            ip=client_ip
        )

    # If security is enabled but no auth provided
    if config.API_KEY_ENABLED or config.JWT_ENABLED:
        # Allow read-only access without auth for certain endpoints
        return AuthUser(
            id="anonymous",
            type="anonymous",
            roles=["read"],
            ip=client_ip
        )

    # Security disabled - allow full access
    return AuthUser(
        id="anonymous",
        type="anonymous",
        roles=["read", "write", "admin"],
        ip=client_ip
    )


def require_auth(roles: list = None):
    """
    Decorator/dependency to require authentication with specific roles.

    Usage:
        @router.get("/protected")
        async def protected(user: AuthUser = Depends(require_auth(["admin"]))):
            ...
    """
    async def auth_dependency(user: AuthUser = Depends(get_current_user)):
        # Check if authentication is required
        if (config.API_KEY_ENABLED or config.JWT_ENABLED) and user.type == "anonymous":
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Check roles
        if roles:
            if not any(role in user.roles for role in roles):
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required roles: {roles}"
                )

        return user

    return auth_dependency


def require_write_permission(user: AuthUser = Depends(get_current_user)):
    """Dependency to require write permission"""
    if config.READ_ONLY_MODE:
        raise HTTPException(
            status_code=403,
            detail="Gateway is in read-only mode. Write operations are disabled."
        )

    if "write" not in user.roles and "admin" not in user.roles:
        raise HTTPException(
            status_code=403,
            detail="Write permission required"
        )

    return user


# ============================================
# Rate Limiting (Simple in-memory)
# ============================================

_rate_limit_store: dict = {}


async def check_rate_limit(request: Request, user: AuthUser = Depends(get_current_user)):
    """Simple rate limiting based on IP"""
    if not config.RATE_LIMIT_ENABLED:
        return

    client_ip = await get_client_ip(request)
    key = f"rate_limit:{client_ip}"
    now = datetime.utcnow()

    # Clean old entries
    if key in _rate_limit_store:
        entries = _rate_limit_store[key]
        cutoff = now - timedelta(seconds=config.RATE_LIMIT_WINDOW)
        _rate_limit_store[key] = [ts for ts in entries if ts > cutoff]
    else:
        _rate_limit_store[key] = []

    # Check limit
    if len(_rate_limit_store[key]) >= config.RATE_LIMIT_REQUESTS:
        logger.warning(f"Rate limit exceeded for {client_ip}")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {config.RATE_LIMIT_REQUESTS} requests per {config.RATE_LIMIT_WINDOW}s"
        )

    # Record request
    _rate_limit_store[key].append(now)


# ============================================
# Utility Functions
# ============================================

def get_security_status() -> dict:
    """Get current security configuration status"""
    return {
        "api_key_enabled": config.API_KEY_ENABLED,
        "api_key_configured": bool(config.API_KEY),
        "jwt_enabled": config.JWT_ENABLED,
        "read_only_mode": config.READ_ONLY_MODE,
        "ip_whitelist_enabled": config.IP_WHITELIST_ENABLED,
        "ip_whitelist_count": len(config.IP_WHITELIST),
        "rate_limit_enabled": config.RATE_LIMIT_ENABLED,
        "rate_limit_requests": config.RATE_LIMIT_REQUESTS,
        "rate_limit_window_seconds": config.RATE_LIMIT_WINDOW,
    }


def generate_api_key() -> str:
    """Generate a new random API key"""
    return secrets.token_urlsafe(32)
