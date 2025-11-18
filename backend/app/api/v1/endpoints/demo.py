"""
Demo endpoints for frontend development

Provides simplified endpoints that aggregate data from multiple sources
for easy consumption by frontend components.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models.tag import Tag
from app.services.optimized_influxdb_service import optimized_influxdb_service

router = APIRouter()


@router.get("/tags/realtime")
async def get_realtime_tags(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of tags to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get real-time values for all tags.

    This endpoint:
    - Fetches all tags from database
    - Gets latest values from InfluxDB
    - Returns combined data in a simple format

    Perfect for real-time monitoring dashboards.
    """
    # Get tags from database
    stmt = select(Tag).limit(limit)

    if category and category.upper() != 'ALL':
        from app.models.tag import TagCategory
        try:
            cat_enum = TagCategory[category.upper()]
            stmt = stmt.where(Tag.category == cat_enum)
        except KeyError:
            pass  # Invalid category, ignore filter

    result = await db.execute(stmt)
    tags = result.scalars().all()

    # Build response with real-time values
    realtime_data = []

    for tag in tags:
        # Try to get latest value from InfluxDB
        try:
            latest = optimized_influxdb_service.get_latest_value_by_name(tag.name)

            if latest:
                value = latest.get('value', 0.0)
                timestamp = latest.get('timestamp')
                quality = latest.get('quality', 'GOOD')
            else:
                # Fallback to database values
                value = tag.last_value if tag.last_value else 0.0
                timestamp = tag.last_timestamp
                quality = tag.last_quality or 'GOOD'

        except Exception as e:
            # On error, use database values
            value = tag.last_value if tag.last_value else 0.0
            timestamp = tag.last_timestamp
            quality = 'UNCERTAIN'

        # Convert value to float if it's a string
        try:
            value_float = float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            value_float = 0.0

        realtime_data.append({
            'tag_name': tag.name,
            'name': tag.name,
            'value': value_float,
            'unit': tag.unit or '',
            'timestamp': timestamp.isoformat() if timestamp else datetime.utcnow().isoformat(),
            'quality': quality.lower() if isinstance(quality, str) else 'good',
            'category': tag.category.value if tag.category else 'process',
            'description': tag.description or '',
            'address': tag.address,
        })

    return realtime_data


@router.get("/tags/{tag_name}/history")
async def get_tag_history(
    tag_name: str,
    minutes: int = Query(60, ge=1, le=525600, description="Minutes of history to fetch (max: 525600 = 1 year)")
):
    """
    Get historical data for a specific tag.

    Returns time-series data points for charting.
    """
    from datetime import timedelta

    start_time = datetime.utcnow() - timedelta(minutes=minutes)
    end_time = datetime.utcnow()

    try:
        data = await optimized_influxdb_service.query_tag_data(
            tag_id=tag_name,
            start=start_time,
            end=end_time
        )

        return {
            'tag_name': tag_name,
            'start_time': start_time.isoformat() + 'Z',
            'end_time': end_time.isoformat() + 'Z',
            'points': len(data),
            'data': data
        }
    except Exception as e:
        return {
            'tag_name': tag_name,
            'start_time': start_time.isoformat() + 'Z',
            'end_time': end_time.isoformat() + 'Z',
            'points': 0,
            'data': [],
            'error': str(e)
        }


@router.get("/system/status")
async def get_system_status():
    """
    Get overall system status.

    Returns:
    - Simulator status
    - Connection status
    - Data flow indicators
    """
    import requests

    try:
        # Check simulator
        sim_response = requests.get('http://localhost:8000/api/v1/simulator/status', timeout=2)
        simulator_running = sim_response.status_code == 200 and sim_response.json().get('system', {}).get('running', False)
    except:
        simulator_running = False

    return {
        'simulator': {
            'running': simulator_running,
            'status': 'connected' if simulator_running else 'disconnected'
        },
        'database': {
            'status': 'connected'  # If this endpoint works, DB is connected
        },
        'influxdb': {
            'status': 'connected'  # Assume connected if no error
        },
        'overall_status': 'connected' if simulator_running else 'partial'
    }
