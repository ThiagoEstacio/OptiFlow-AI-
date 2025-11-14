"""
Backup Management Endpoints (PDCA #23)

Endpoints for triggering and monitoring backups.
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from typing import Dict, Any, List
import logging

from app.core.deps import get_current_active_superuser
from app.models.user import User
from app.services.backup_service import get_backup_service, BackupResult
from app.services.restore_tester import get_restore_tester
from app.services.s3_uploader import get_s3_uploader

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/trigger")
async def trigger_backup(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_superuser)
) -> Dict[str, str]:
    """
    Trigger manual backup of all services (admin only).

    **Requires**: Superuser role

    **Backs up**:
    - PostgreSQL database
    - InfluxDB time-series data
    - Redis cache
    - Vault secrets (if configured)

    **Response**:
    ```json
    {
        "message": "Backup started in background",
        "estimated_time": "5-10 minutes"
    }
    ```
    """
    backup_service = get_backup_service()

    # Run backup in background
    background_tasks.add_task(backup_service.backup_all)

    logger.info(f"Manual backup triggered by {current_user.email}")

    return {
        "message": "Backup started in background",
        "estimated_time": "5-10 minutes"
    }


@router.get("/stats")
async def get_backup_stats(
    current_user: User = Depends(get_current_active_superuser)
) -> Dict[str, Any]:
    """
    Get backup service statistics (admin only).

    **Returns**:
    ```json
    {
        "total_backups": 150,
        "failed_backups": 2,
        "success_rate": 98.7,
        "last_backup_time": "2025-01-14T02:00:00",
        "retention_policy": {
            "daily_days": 7,
            "weekly_weeks": 4,
            "monthly_months": 12
        }
    }
    ```
    """
    backup_service = get_backup_service()
    return backup_service.get_stats()


@router.post("/cleanup")
async def cleanup_old_backups(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_superuser)
) -> Dict[str, str]:
    """
    Manually trigger cleanup of old backups (admin only).

    Enforces retention policy:
    - Daily backups: keep 7 days
    - Weekly backups: keep 4 weeks
    - Monthly backups: keep 12 months

    **Response**:
    ```json
    {
        "message": "Cleanup started in background"
    }
    ```
    """
    backup_service = get_backup_service()

    # Run cleanup in background
    background_tasks.add_task(backup_service.cleanup_old_backups)

    logger.info(f"Manual cleanup triggered by {current_user.email}")

    return {
        "message": "Cleanup started in background"
    }


@router.post("/test-restore")
async def test_restore(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_superuser)
) -> Dict[str, str]:
    """
    Trigger restore testing (admin only).

    Tests latest backups by performing automated restores.

    **Response**:
    ```json
    {
        "message": "Restore tests started in background"
    }
    ```
    """
    restore_tester = get_restore_tester()

    # Run restore tests in background
    background_tasks.add_task(restore_tester.test_all_restores)

    logger.info(f"Restore tests triggered by {current_user.email}")

    return {
        "message": "Restore tests started in background"
    }


@router.get("/test-results")
async def get_restore_test_results(
    current_user: User = Depends(get_current_active_superuser)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get latest restore test results (admin only).

    **Returns**:
    ```json
    {
        "results": [
            {
                "service": "postgresql",
                "status": "success",
                "checksum_valid": true,
                "restore_successful": true
            }
        ]
    }
    ```
    """
    restore_tester = get_restore_tester()
    results = restore_tester.get_latest_test_results(limit=20)

    return {
        "results": results
    }


@router.get("/s3/stats")
async def get_s3_stats(
    current_user: User = Depends(get_current_active_superuser)
) -> Dict[str, Any]:
    """
    Get S3/MinIO storage statistics (admin only).

    **Returns**:
    ```json
    {
        "bucket_name": "optiflow-backups",
        "total_objects": 150,
        "total_size_gb": 25.3
    }
    ```
    """
    s3_uploader = get_s3_uploader()
    return s3_uploader.get_stats()


@router.get("/s3/list")
async def list_s3_backups(
    service: str = None,
    current_user: User = Depends(get_current_active_superuser)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List backups in S3/MinIO (admin only).

    **Parameters**:
    - service: Filter by service (postgresql, influxdb, redis)

    **Returns**:
    ```json
    {
        "backups": [
            {
                "key": "postgresql/2025/01/14/postgresql_20250114_020000.sql.gz",
                "size": 1048576,
                "last_modified": "2025-01-14T02:00:00"
            }
        ]
    }
    ```
    """
    s3_uploader = get_s3_uploader()
    backups = await s3_uploader.list_backups(service=service)

    return {
        "backups": backups
    }


@router.get("/health")
async def backup_health() -> Dict[str, str]:
    """
    Health check for backup service.

    **Returns**:
    ```json
    {
        "status": "ok",
        "service": "backup-service"
    }
    ```
    """
    return {
        "status": "ok",
        "service": "backup-service"
    }
