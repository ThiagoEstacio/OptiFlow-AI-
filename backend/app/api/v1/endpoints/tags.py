"""
Tag endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.session import get_db
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate, TagResponse
from app.services.opcua_tag_reader import update_tag_values_from_opcua
from app.services.optimized_influxdb_service import optimized_influxdb_service as influxdb_service
from app.services.cache_service import cached

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/", response_model=List[TagResponse])
@cached(ttl=120, key_prefix="tags_list")
async def list_tags(
    skip: int = 0,
    limit: int = 100,
    device_id: UUID = None,
    db: AsyncSession = Depends(get_db)
):
    """List all tags"""
    stmt = select(Tag)

    if device_id:
        stmt = stmt.where(Tag.device_id == device_id)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    tags = result.scalars().all()
    return tags


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("200/minute")  # 🔒 Limit tag creation (increased for batch imports)
async def create_tag(
    request: Request,
    tag_in: TagCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new tag"""
    # Map schema fields to model fields
    tag_data = tag_in.model_dump()
    
    # Rename fields to match database column names
    if 'scale_factor' in tag_data:
        tag_data['scale'] = tag_data.pop('scale_factor')
    if 'enabled' in tag_data:
        tag_data['is_active'] = tag_data.pop('enabled')
    if 'log_enabled' in tag_data:
        tag_data['enable_quality_check'] = tag_data.pop('log_enabled')
    
    tag = Tag(**tag_data)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get tag by ID"""
    stmt = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    return tag


@router.put("/{tag_id}", response_model=TagResponse)
@limiter.limit("50/minute")  # 🔒 Limit tag updates (higher for batch operations)
async def update_tag(
    request: Request,
    tag_id: UUID,
    tag_in: TagUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a tag"""
    stmt = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    # Update only provided fields
    update_data = tag_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)

    await db.commit()
    await db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("50/minute")  # 🔒 Limit tag deletions (higher for batch operations)
async def delete_tag(
    request: Request,
    tag_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a tag"""
    stmt = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    await db.delete(tag)
    await db.commit()
    return None


@router.get("/{tag_id}/latest")
async def get_latest_tag_value(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get latest tag value"""
    stmt = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    return {
        "tag_id": str(tag.id),
        "value": tag.last_value,
        "quality": tag.last_quality,
        "timestamp": tag.last_timestamp
    }


@router.post("/sync-values", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")  # Rate limit for sync operations
async def sync_tag_values_from_opcua(
    request: Request,
    device_id: Optional[UUID] = Query(None, description="Device ID to filter tags"),
    opcua_endpoint: str = Query("opc.tcp://opcua-server:4840/optiflow/terminal", description="OPC UA server endpoint"),
    limit: int = Query(200, ge=1, le=500, description="Maximum number of tags to sync"),
    db: AsyncSession = Depends(get_db)
):
    """
    Read current values from OPC UA server and update tags in database
    
    This endpoint:
    - Connects to the OPC UA server
    - Reads current values for all tags
    - Updates last_value, last_quality, and last_timestamp in database
    
    Use this to synchronize tag values before displaying them in the UI
    """
    result = await update_tag_values_from_opcua(
        db=db,
        opcua_endpoint=opcua_endpoint,
        device_id=str(device_id) if device_id else None,
        limit=limit
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )

    return result


@router.get("/realtime/{tag_name}")
async def get_realtime_tag_value(tag_name: str):
    """
    Get real-time value for a tag from InfluxDB

    This endpoint:
    - Queries InfluxDB for the latest value of a tag by name
    - Returns the current value, timestamp, quality, and source
    - Useful for real-time dashboards and monitoring

    Example: GET /api/v1/tags/realtime/TEST_COUNTER_PV
    """
    try:
        result = influxdb_service.get_latest_value_by_name(tag_name)

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for tag '{tag_name}' in the last 24 hours"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving realtime value for tag '{tag_name}': {str(e)}"
        )


@router.post("/realtime/batch")
async def get_realtime_tag_values_batch(tag_names: List[str]):
    """
    Get real-time values for multiple tags from InfluxDB (batch query)

    This endpoint:
    - Accepts a list of tag names in request body
    - Returns latest values for all tags in a single optimized query
    - More efficient than multiple individual requests
    - Useful for SCADA dashboards monitoring many tags

    Example POST body: ["TEST_COUNTER_PV", "WAREHOUSE_LEVEL_PCT_PV", "TOTAL_MASS_T_PV"]
    """
    try:
        if not tag_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag names list cannot be empty"
            )

        if len(tag_names) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 tags per request"
            )

        results = influxdb_service.get_latest_values_by_names(tag_names)
        return results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving batch realtime values: {str(e)}"
        )


@router.get("/timeseries/{tag_name}")
async def get_tag_timeseries(
    tag_name: str,
    start_minutes_ago: int = Query(default=60, ge=1, le=1440, description="Minutes ago to start query"),
    aggregation: Optional[str] = Query(default=None, description="Aggregation function: mean, min, max, sum, count"),
    interval: Optional[str] = Query(default=None, description="Aggregation interval (e.g., '1m', '5m', '1h')"),
):
    """
    Get time-series data for a tag by name

    Perfect for real-time charts and historical analysis.

    Parameters:
    - tag_name: Name of the tag (e.g., 'TEST_COUNTER_PV')
    - start_minutes_ago: How many minutes back to query (default: 60, max: 1440 = 24h)
    - aggregation: Optional aggregation function (mean, min, max, sum, count)
    - interval: Aggregation interval (e.g., '1m' for 1 minute, '5m', '1h')

    Example:
    - GET /api/v1/tags/timeseries/TEST_COUNTER_PV?start_minutes_ago=10
    - GET /api/v1/tags/timeseries/WAREHOUSE_LEVEL_PCT_PV?start_minutes_ago=60&aggregation=mean&interval=5m
    """
    try:
        from datetime import datetime, timedelta

        # Calculate start time
        start_time = datetime.utcnow() - timedelta(minutes=start_minutes_ago)
        end_time = datetime.utcnow()

        # Query InfluxDB using the tag name as tag_id (since simulator uses tag names)
        data = await influxdb_service.query_tag_data(
            tag_id=tag_name,
            start=start_time,
            end=end_time
        )

        return {
            "tag_name": tag_name,
            "start_time": start_time.isoformat() + "Z",
            "end_time": end_time.isoformat() + "Z",
            "aggregation": aggregation,
            "interval": interval,
            "data_points": len(data),
            "data": data
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving time-series data: {str(e)}"
        )


@router.post("/timeseries/batch")
async def get_multiple_tags_timeseries(
    tag_names: List[str],
    start_minutes_ago: int = Query(default=60, ge=1, le=1440),
    aggregation: Optional[str] = Query(default=None),
    interval: Optional[str] = Query(default=None),
):
    """
    Get time-series data for multiple tags at once

    Perfect for synchronized charts with multiple series.

    Example POST body:
    ```json
    ["TEST_COUNTER_PV", "WAREHOUSE_LEVEL_PCT_PV", "CORR01_POWER_KW_PV"]
    ```
    """
    try:
        from datetime import datetime, timedelta

        if not tag_names or len(tag_names) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide 1-20 tag names"
            )

        start_time = datetime.utcnow() - timedelta(minutes=start_minutes_ago)
        end_time = datetime.utcnow()

        results = {}
        for tag_name in tag_names:
            data = await influxdb_service.query_tag_data(
                tag_id=tag_name,
                start=start_time,
                end=end_time
            )
            results[tag_name] = {
                "data_points": len(data),
                "data": data
            }

        return {
            "start_time": start_time.isoformat() + "Z",
            "end_time": end_time.isoformat() + "Z",
            "aggregation": aggregation,
            "interval": interval,
            "tags": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving batch time-series: {str(e)}"
        )
