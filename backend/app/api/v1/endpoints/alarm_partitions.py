"""
Alarm Event Partition Management API (PDCA #17)

Endpoints for managing alarm_events table partitions.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
import logging

from app.db.session import get_db
from app.models.user import User
from app.core.deps import get_current_user
from app.services.alarm_partition_manager import get_partition_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_partition_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get alarm_events partition statistics.

    **Returns**:
    ```json
    {
        "total_partitions": 15,
        "total_size": "2.5 GB",
        "total_rows": 1234567,
        "oldest_partition": "alarm_events_2024_01",
        "newest_partition": "alarm_events_2025_03",
        "partitions": [
            {
                "partition_name": "alarm_events_2025_01",
                "size": "150 MB",
                "live_rows": 125000,
                "dead_rows": 50
            }
        ]
    }
    ```

    **Use Cases**:
    - Monitor partition sizes
    - Plan partition maintenance
    - Capacity planning
    - Performance troubleshooting
    """
    manager = await get_partition_manager(db)
    summary = await manager.get_summary()

    return summary


@router.post("/create")
async def create_partition(
    year: int = Query(..., ge=2024, le=2030, description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Manually create a partition for specific year/month.

    **Parameters**:
    - year: Year (2024-2030)
    - month: Month (1-12)

    **Returns**:
    ```json
    {
        "status": "created",
        "partition_name": "alarm_events_2025_06",
        "message": "Partition created successfully"
    }
    ```

    **Use Cases**:
    - Pre-create partitions for future months
    - Recreate partition after manual drop
    - Initial partition setup
    """
    manager = await get_partition_manager(db)

    created = await manager.create_partition(year, month)

    if created:
        return {
            "status": "created",
            "partition_name": f"alarm_events_{year}_{month:02d}",
            "message": "Partition created successfully"
        }
    else:
        return {
            "status": "exists",
            "partition_name": f"alarm_events_{year}_{month:02d}",
            "message": "Partition already exists"
        }


@router.post("/create-future")
async def create_future_partitions(
    months_ahead: int = Query(3, ge=1, le=12, description="Number of months ahead"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create partitions for next N months.

    **Parameters**:
    - months_ahead: Number of months to create partitions for (1-12)

    **Returns**:
    ```json
    {
        "status": "success",
        "partitions_created": 3,
        "message": "Created 3 future partition(s)"
    }
    ```

    **Use Cases**:
    - Proactive partition management
    - Scheduled maintenance tasks
    - Prevent insert failures on month rollover
    """
    manager = await get_partition_manager(db)

    created_count = await manager.create_future_partitions(months_ahead)

    return {
        "status": "success",
        "partitions_created": created_count,
        "months_ahead": months_ahead,
        "message": f"Created {created_count} future partition(s)"
    }


@router.delete("/drop")
async def drop_partition(
    year: int = Query(..., ge=2024, le=2030, description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    confirm: bool = Query(False, description="Confirm deletion"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Drop a specific partition.

    **WARNING**: This permanently deletes data!

    **Parameters**:
    - year: Year (2024-2030)
    - month: Month (1-12)
    - confirm: Must be true to actually delete

    **Returns**:
    ```json
    {
        "status": "dropped",
        "partition_name": "alarm_events_2024_01",
        "message": "Partition dropped successfully"
    }
    ```

    **Use Cases**:
    - Archive old data
    - Free up disk space
    - Data retention compliance
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to drop partition. This action is irreversible!"
        )

    manager = await get_partition_manager(db)

    dropped = await manager.drop_old_partition(year, month)

    if dropped:
        return {
            "status": "dropped",
            "partition_name": f"alarm_events_{year}_{month:02d}",
            "message": "Partition dropped successfully"
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Partition alarm_events_{year}_{month:02d} not found"
        )


@router.post("/cleanup")
async def cleanup_old_partitions(
    retention_months: int = Query(12, ge=1, le=120, description="Keep data for N months"),
    confirm: bool = Query(False, description="Confirm cleanup"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Drop partitions older than retention period.

    **WARNING**: This permanently deletes data!

    **Parameters**:
    - retention_months: Keep data for this many months (default: 12)
    - confirm: Must be true to actually delete

    **Returns**:
    ```json
    {
        "status": "success",
        "partitions_dropped": 5,
        "retention_months": 12,
        "message": "Cleaned up 5 old partition(s)"
    }
    ```

    **Use Cases**:
    - Automated data retention
    - Disk space management
    - Compliance with data retention policies
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to cleanup partitions. This action is irreversible!"
        )

    manager = await get_partition_manager(db)

    dropped_count = await manager.cleanup_old_partitions(retention_months)

    return {
        "status": "success",
        "partitions_dropped": dropped_count,
        "retention_months": retention_months,
        "message": f"Cleaned up {dropped_count} old partition(s)"
    }
