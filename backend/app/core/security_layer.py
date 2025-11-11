"""
API Rate Limiting & Security Layer
OptiFlow AI - Quick Security Implementation
"""

from fastapi import Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime, timedelta
from typing import Dict, Optional
import hashlib
import secrets
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# RATE LIMITER SETUP
# ============================================================================

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute", "1000/hour"],
    storage_uri="redis://redis:6379/1"
)

# ============================================================================
# API KEY MANAGEMENT (In-Memory for Quick Implementation)
# ============================================================================

class APIKeyManager:
    """Simple API key management with rotation"""
    
    def __init__(self):
        self.keys: Dict[str, dict] = {}
        self.key_usage: Dict[str, int] = {}
        
    def generate_key(self, user_id: str, expiry_days: int = 90) -> str:
        """Generate a new API key"""
        key = f"opti_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        self.keys[key_hash] = {
            'user_id': user_id,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(days=expiry_days),
            'is_active': True,
            'rate_limit': "200/minute"
        }
        
        logger.info(f"✅ API key generated for user: {user_id}")
        return key
    
    def validate_key(self, key: str) -> Optional[dict]:
        """Validate API key"""
        if not key or not key.startswith('opti_'):
            return None
            
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash not in self.keys:
            return None
            
        key_data = self.keys[key_hash]
        
        # Check expiry
        if datetime.now() > key_data['expires_at']:
            logger.warning(f"⚠️  Expired API key used by user: {key_data['user_id']}")
            return None
            
        # Check active status
        if not key_data['is_active']:
            return None
            
        # Track usage
        self.key_usage[key_hash] = self.key_usage.get(key_hash, 0) + 1
        
        return key_data
    
    def rotate_key(self, old_key: str, expiry_days: int = 90) -> Optional[str]:
        """Rotate an existing API key"""
        old_hash = hashlib.sha256(old_key.encode()).hexdigest()
        
        if old_hash not in self.keys:
            return None
            
        old_data = self.keys[old_hash]
        
        # Deactivate old key
        self.keys[old_hash]['is_active'] = False
        
        # Generate new key
        new_key = self.generate_key(old_data['user_id'], expiry_days)
        
        logger.info(f"🔄 API key rotated for user: {old_data['user_id']}")
        return new_key
    
    def revoke_key(self, key: str) -> bool:
        """Revoke an API key"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash in self.keys:
            self.keys[key_hash]['is_active'] = False
            logger.info(f"🚫 API key revoked")
            return True
            
        return False
    
    def get_usage_stats(self, key: str) -> Optional[dict]:
        """Get usage statistics for a key"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash not in self.keys:
            return None
            
        key_data = self.keys[key_hash]
        usage_count = self.key_usage.get(key_hash, 0)
        
        return {
            'user_id': key_data['user_id'],
            'created_at': key_data['created_at'],
            'expires_at': key_data['expires_at'],
            'is_active': key_data['is_active'],
            'usage_count': usage_count,
            'days_until_expiry': (key_data['expires_at'] - datetime.now()).days
        }

# Global instance
api_key_manager = APIKeyManager()

# ============================================================================
# SECURITY MIDDLEWARE
# ============================================================================

async def verify_api_key(request: Request) -> dict:
    """Verify API key from request header"""
    api_key = request.headers.get('X-API-Key')
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include X-API-Key header."
        )
    
    key_data = api_key_manager.validate_key(api_key)
    
    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired API key"
        )
    
    return key_data

# ============================================================================
# ENDPOINT-SPECIFIC RATE LIMITS
# ============================================================================

RATE_LIMITS = {
    # High-cost operations
    'ml_training': "5/hour",
    'data_export': "20/hour",
    'bulk_operations': "30/hour",
    
    # Medium-cost operations
    'ml_prediction': "100/minute",
    'analytics': "100/minute",
    'reports': "50/minute",
    
    # Low-cost operations
    'read_only': "200/minute",
    'dashboard': "300/minute",
}

def get_rate_limit(operation: str) -> str:
    """Get rate limit for specific operation"""
    return RATE_LIMITS.get(operation, "100/minute")

# ============================================================================
# AUDIT LOGGING
# ============================================================================

class AuditLogger:
    """Simple audit logger"""
    
    @staticmethod
    def log_access(user_id: str, endpoint: str, method: str, status_code: int):
        """Log API access"""
        logger.info(
            f"AUDIT: user={user_id} endpoint={endpoint} method={method} "
            f"status={status_code} timestamp={datetime.now().isoformat()}"
        )
    
    @staticmethod
    def log_security_event(event_type: str, details: str):
        """Log security events"""
        logger.warning(
            f"SECURITY: type={event_type} details={details} "
            f"timestamp={datetime.now().isoformat()}"
        )

audit_logger = AuditLogger()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded"""
    audit_logger.log_security_event(
        'rate_limit_exceeded',
        f"IP: {get_remote_address(request)} Path: {request.url.path}"
    )
    
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Rate limit exceeded: {exc.detail}"
    )

# ============================================================================
# INITIALIZATION
# ============================================================================

def init_security():
    """Initialize security system"""
    # Generate default admin key
    admin_key = api_key_manager.generate_key('admin', expiry_days=365)
    logger.info(f"🔑 Admin API Key: {admin_key}")
    logger.info("⚠️  Store this key securely! It will not be shown again.")
    
    return admin_key
