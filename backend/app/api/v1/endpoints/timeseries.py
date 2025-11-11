"""
Time series data endpoints
"""
from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
import logging
from functools import lru_cache
import hashlib
import json

from app.db.session import get_db
from app.services.optimized_influxdb_service import optimized_influxdb_service as influxdb_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Simple in-memory cache for latest values (TTL: 1 second)
_latest_value_cache: Dict[str, tuple] = {}  # {tag_id: (value, timestamp)}
_cache_ttl = 1.0  # seconds


@router.post("/batch")
async def write_batch(
    points: List[Dict[str, Any]] = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Write batch of time series data points

    Expected format:
    [
        {
            "tag_id": "uuid",
            "value": 42.5,
            "timestamp": "2024-01-01T00:00:00Z",
            "quality": "good",
            "device_id": "uuid",
            "site_id": "uuid"
        }
    ]
    """
    try:
        success = influxdb_service.write_batch(points)

        if success:
            return {
                "status": "success",
                "points_written": len(points)
            }
        else:
            return {
                "status": "error",
                "message": "Failed to write points"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/tags/{tag_id}/latest")
async def get_latest_value(
    tag_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the latest value for a tag from InfluxDB (with caching)
    
    Args:
        tag_id: Can be either UUID or tag name
    """
    from sqlalchemy import select
    from app.models.tag import Tag
    
    try:
        # Check cache first
        now = datetime.utcnow()
        if tag_id in _latest_value_cache:
            cached_value, cached_time = _latest_value_cache[tag_id]
            age = (now - cached_time).total_seconds()
            
            if age < _cache_ttl:
                logger.debug(f"Cache HIT for {tag_id} (age: {age:.2f}s)")
                return cached_value
        
        # Check if tag_id is a UUID or a name
        actual_tag_id = tag_id
        
        # If not a valid UUID format, try to find by name
        try:
            UUID(tag_id)
        except ValueError:
            # It's a name, lookup the UUID
            result = await db.execute(
                select(Tag).where(Tag.name == tag_id)
            )
            tag = result.scalars().first()  # Get first match if duplicates exist
            
            if tag:
                actual_tag_id = str(tag.id)
                logger.debug(f"Resolved tag name '{tag_id}' to UUID '{actual_tag_id}'")
            else:
                logger.warning(f"Tag not found with name: {tag_id}")
                response = {
                    "value": None,
                    "timestamp": now.isoformat() + "Z",
                    "quality": "tag_not_found"
                }
                # Cache negative result briefly
                _latest_value_cache[tag_id] = (response, now)
                return response
        
        # Query last 10 seconds from InfluxDB
        end_time = now
        start_time = end_time - timedelta(seconds=10)
        
        data = influxdb_service.query_tag_data(
            tag_id=actual_tag_id,
            start_time=start_time,
            end_time=end_time
        )
        
        if data and len(data) > 0:
            # Return most recent value
            latest = data[-1]
            logger.debug(f"✅ Returning REAL latest value for tag {tag_id}: {latest.get('value')}")
            response = {
                "value": latest.get("value"),
                "timestamp": latest.get("timestamp"),
                "quality": latest.get("quality", "good")
            }
        else:
            logger.debug(f"⚠️ No InfluxDB data for tag {tag_id}, returning null")
            response = {
                "value": None,
                "timestamp": now.isoformat() + "Z",
                "quality": "no_data"
            }
        
        # Cache the result
        _latest_value_cache[tag_id] = (response, now)
        
        # Clean old cache entries (simple cleanup)
        if len(_latest_value_cache) > 1000:
            old_keys = [k for k, (_, t) in _latest_value_cache.items() 
                       if (now - t).total_seconds() > 60]
            for k in old_keys:
                del _latest_value_cache[k]
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error fetching latest value for tag {tag_id}: {e}")
        return {
            "value": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "quality": "error"
        }


@router.get("/tags/{tag_id}")
async def query_tag_data(
    tag_id: str,
    start_time: datetime,
    end_time: datetime = None,
    aggregation: str = None,
    interval: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Query historical data for a tag
    """
    try:
        data = influxdb_service.query_tag_data(
            str(tag_id),
            start_time,
            end_time,
            aggregation,
            interval
        )

        return {
            "tag_id": str(tag_id),
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        return {
            "error": str(e)
        }


@router.post("/query")
async def query_multiple_tags(
    query: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Query data for multiple tags

    Expected format:
    {
        "tag_ids": ["uuid1", "uuid2"],
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-01-02T00:00:00Z",
        "aggregation": "mean",
        "interval": "5m"
    }
    """
    try:
        tag_ids = query.get("tag_ids", [])
        start_time = datetime.fromisoformat(query.get("start_time").replace("Z", "+00:00"))
        end_time_str = query.get("end_time")
        end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00")) if end_time_str else None
        aggregation = query.get("aggregation")
        interval = query.get("interval")

        data = influxdb_service.query_multiple_tags(
            tag_ids,
            start_time,
            end_time,
            aggregation,
            interval
        )

        return data
    except Exception as e:
        return {
            "error": str(e)
        }
