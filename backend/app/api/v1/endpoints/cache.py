"""
Cache monitoring endpoint
"""

from fastapi import APIRouter, HTTPException
from app.services.cache_service import cache_service

router = APIRouter(tags=["Cache Monitoring"])


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
