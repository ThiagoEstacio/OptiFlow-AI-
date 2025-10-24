"""
Time series data endpoints
"""
from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from datetime import datetime
from uuid import UUID

from app.db.session import get_db
from app.optiflow.services.influxdb import influxdb_service

router = APIRouter()


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


@router.get("/tags/{tag_id}")
async def query_tag_data(
    tag_id: UUID,
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
