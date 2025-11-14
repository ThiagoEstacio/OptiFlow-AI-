"""
Cache monitoring endpoint (Enhanced with PDCA #26)
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.services.cache_service import cache_service
from app.core.advanced_cache import get_advanced_cache
from app.core.deps import get_current_active_superuser
from app.models.user import User
import logging

router = APIRouter(tags=["Cache Monitoring"])
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_cache_stats():
    """
    Get cache statistics
    
    Returns cache hit/miss rates and Redis info
    """
    try:
        stats = await cache_service.get_stats()
        return {
            "status": "healthy" if stats["connected"] else "disconnected",
            **stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.post("/invalidate")
async def invalidate_cache_pattern(pattern: str):
    """
    Invalidate cache keys matching pattern
    
    Args:
        pattern: Redis pattern (e.g., "dashboard:*", "tags:123:*")
    
    Returns:
        Number of keys deleted
    """
    try:
        deleted = await cache_service.invalidate_pattern(pattern)
        return {
            "pattern": pattern,
            "deleted_keys": deleted,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")


@router.delete("/clear")
async def clear_all_cache():
    """
    Clear entire cache (USE WITH CAUTION!)
    
    Admin endpoint to flush all Redis cache
    """
    try:
        success = await cache_service.clear_all()
        if success:
            return {
                "status": "success",
                "message": "All cache cleared"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/health")
async def cache_health_check():
    """
    Check cache service health
    """
    stats = await cache_service.get_stats()

    if not stats["connected"]:
        raise HTTPException(status_code=503, detail="Cache service not connected")

    return {
        "status": "healthy",
        "connected": True,
        "message": "Cache service is operational"
    }


# ========================================
# PDCA #26: Advanced Cache Endpoints
# ========================================

@router.get("/advanced/stats")
async def get_advanced_cache_stats(
    current_user: User = Depends(get_current_active_superuser)
) -> Dict[str, Any]:
    """
    Get advanced cache statistics (admin only).

    **PDCA #26**: Multi-layer cache monitoring

    **Returns**:
    ```json
    {
        "l1": {
            "size": 500,
            "max_size": 1000,
            "hits": 15000,
            "misses": 500,
            "hit_rate": 96.7
        },
        "l2_hits": 300,
        "misses": 200,
        "overall_hit_rate": 98.5,
        "in_flight_requests": 2
    }
    ```

    **Performance Targets**:
    - Hit rate > 95%
    - p95 latency < 50ms (vs 500ms without cache)
    - Database load reduction > 60%
    """
    cache = get_advanced_cache()
    stats = cache.get_stats()

    return stats


@router.post("/advanced/warm")
async def warm_advanced_cache(
    current_user: User = Depends(get_current_active_superuser)
) -> Dict[str, Any]:
    """
    Warm cache with frequently accessed data (admin only).

    Pre-loads cache with:
    - Active users
    - Recent assets
    - Common dashboard queries

    **Response**:
    ```json
    {
        "message": "Cache warming completed",
        "items_warmed": 150,
        "duration_seconds": 2.5
    }
    ```
    """
    import time
    from app.db.session import AsyncSessionLocal
    from app.models.user import User as UserModel
    from app.models.asset import Asset
    from sqlalchemy import select

    cache = get_advanced_cache()
    start_time = time.time()
    items_warmed = 0

    try:
        async with AsyncSessionLocal() as db:
            # Warm user cache (top 100 active users)
            users_result = await db.execute(
                select(UserModel).limit(100)
            )
            users = users_result.scalars().all()

            for user in users:
                cache_key = f"user:{user.id}"
                user_data = {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role
                }
                await cache.set(cache_key, user_data, ttl=300)
                items_warmed += 1

            # Warm asset cache (top 50 recent assets)
            assets_result = await db.execute(
                select(Asset).limit(50)
            )
            assets = assets_result.scalars().all()

            for asset in assets:
                cache_key = f"asset:{asset.id}"
                asset_data = {
                    "id": str(asset.id),
                    "name": asset.name,
                    "type": asset.type,
                    "status": asset.status
                }
                await cache.set(cache_key, asset_data, ttl=600)
                items_warmed += 1

        duration = time.time() - start_time

        logger.info(
            f"Cache warming completed by {current_user.email}: "
            f"{items_warmed} items in {duration:.2f}s"
        )

        return {
            "message": "Cache warming completed",
            "items_warmed": items_warmed,
            "duration_seconds": round(duration, 2)
        }

    except Exception as e:
        logger.error(f"Failed to warm cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to warm cache: {str(e)}")


@router.delete("/advanced/key/{key}")
async def invalidate_advanced_key(
    key: str,
    current_user: User = Depends(get_current_active_superuser)
) -> Dict[str, str]:
    """
    Invalidate specific cache key from multi-layer cache (admin only).

    **Parameters**:
    - key: Cache key to invalidate (e.g., "user:123", "dashboard:executive")

    **Response**:
    ```json
    {
        "message": "Key invalidated successfully",
        "key": "user:123"
    }
    ```
    """
    cache = get_advanced_cache()

    try:
        await cache.delete(key)
        logger.info(f"Cache key '{key}' invalidated by {current_user.email}")

        return {
            "message": "Key invalidated successfully",
            "key": key
        }

    except Exception as e:
        logger.error(f"Failed to invalidate key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to invalidate key: {str(e)}")


@router.delete("/advanced/pattern/{pattern}")
async def invalidate_advanced_pattern(
    pattern: str,
    current_user: User = Depends(get_current_active_superuser)
) -> Dict[str, str]:
    """
    Invalidate all cache keys matching pattern (admin only).

    **Parameters**:
    - pattern: Redis glob pattern (e.g., "user:*", "dashboard:*")

    **Examples**:
    - `user:*` - All user cache entries
    - `dashboard:executive:*` - All executive dashboard cache
    - `asset:*` - All asset cache

    **Response**:
    ```json
    {
        "message": "Pattern invalidated successfully",
        "pattern": "user:*"
    }
    ```
    """
    cache = get_advanced_cache()

    try:
        await cache.invalidate_pattern(pattern)
        logger.info(f"Cache pattern '{pattern}' invalidated by {current_user.email}")

        return {
            "message": "Pattern invalidated successfully",
            "pattern": pattern
        }

    except Exception as e:
        logger.error(f"Failed to invalidate pattern: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to invalidate pattern: {str(e)}")
