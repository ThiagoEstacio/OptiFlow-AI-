"""
Monitoring API Endpoints

Provides health monitoring APIs for:
- System resources
- Docker containers
- Databases
- Tags
- Overall system health
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.monitoring.system_monitor import SystemMonitor
from app.monitoring.docker_monitor import DockerMonitor
from app.monitoring.database_monitor import DatabaseMonitor
from app.monitoring.tag_monitor import TagMonitor

router = APIRouter()
logger = logging.getLogger(__name__)


# System Monitoring Endpoints


@router.get("/system", response_model=Dict[str, Any])
async def get_system_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive system metrics (CPU, RAM, disk, network, processes).

    Requires authentication.
    """
    try:
        return SystemMonitor.get_all_metrics()
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/cpu", response_model=Dict[str, Any])
async def get_cpu_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get CPU metrics only."""
    try:
        return SystemMonitor.get_cpu_metrics()
    except Exception as e:
        logger.error(f"Error getting CPU metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/memory", response_model=Dict[str, Any])
async def get_memory_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get memory (RAM) metrics."""
    try:
        return SystemMonitor.get_memory_metrics()
    except Exception as e:
        logger.error(f"Error getting memory metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/disk", response_model=Dict[str, Any])
async def get_disk_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get disk usage metrics."""
    try:
        return SystemMonitor.get_disk_metrics()
    except Exception as e:
        logger.error(f"Error getting disk metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/network", response_model=Dict[str, Any])
async def get_network_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get network I/O metrics."""
    try:
        return SystemMonitor.get_network_metrics()
    except Exception as e:
        logger.error(f"Error getting network metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/processes", response_model=Dict[str, Any])
async def get_process_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get process metrics and top processes."""
    try:
        return SystemMonitor.get_process_metrics()
    except Exception as e:
        logger.error(f"Error getting process metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/info", response_model=Dict[str, Any])
async def get_system_info(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get system information (OS, platform, uptime)."""
    try:
        return SystemMonitor.get_system_info()
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Docker Monitoring Endpoints


@router.get("/docker/containers", response_model=Dict[str, Any])
async def get_docker_containers(
    all_containers: bool = False,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get list of Docker containers.

    Args:
        all_containers: Include stopped containers if True
    """
    try:
        monitor = DockerMonitor()
        if not monitor.is_available():
            raise HTTPException(status_code=503, detail="Docker is not available")

        containers = monitor.get_container_list(all_containers=all_containers)
        return {
            "status": "success",
            "container_count": len(containers),
            "containers": containers,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Docker containers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/docker/stats", response_model=Dict[str, Any])
async def get_docker_stats(
    container_name: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get detailed Docker container statistics.

    Args:
        container_name: Specific container name (optional, returns all if not provided)
    """
    try:
        monitor = DockerMonitor()
        if not monitor.is_available():
            raise HTTPException(status_code=503, detail="Docker is not available")

        return monitor.get_container_stats(container_name=container_name)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Docker stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/docker/health/{container_name}", response_model=Dict[str, Any])
async def get_container_health(
    container_name: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get health status for a specific container."""
    try:
        monitor = DockerMonitor()
        if not monitor.is_available():
            raise HTTPException(status_code=503, detail="Docker is not available")

        return monitor.get_container_health(container_name)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting container health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/docker/logs/{container_name}", response_model=Dict[str, Any])
async def get_container_logs(
    container_name: str,
    tail: int = 100,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get logs for a specific container.

    Args:
        container_name: Container name
        tail: Number of lines to return (default 100)
    """
    try:
        monitor = DockerMonitor()
        if not monitor.is_available():
            raise HTTPException(status_code=503, detail="Docker is not available")

        logs = monitor.get_container_logs(container_name, tail=tail)
        return {
            "status": "success",
            "container_name": container_name,
            "line_count": len(logs),
            "logs": logs,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting container logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Database Monitoring Endpoints


@router.get("/database/postgres", response_model=Dict[str, Any])
async def get_postgres_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get PostgreSQL health metrics."""
    try:
        monitor = DatabaseMonitor(pg_session=db)
        return await monitor.get_postgres_health()
    except Exception as e:
        logger.error(f"Error getting PostgreSQL health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/influxdb", response_model=Dict[str, Any])
async def get_influxdb_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get InfluxDB health metrics."""
    try:
        # TODO: Get InfluxDB client from app state or config
        monitor = DatabaseMonitor(pg_session=db, influx_client=None)
        return await monitor.get_influxdb_health()
    except Exception as e:
        logger.error(f"Error getting InfluxDB health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/tables", response_model=Dict[str, Any])
async def get_postgres_table_sizes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get PostgreSQL table sizes."""
    try:
        monitor = DatabaseMonitor(pg_session=db)
        return await monitor.get_postgres_table_sizes()
    except Exception as e:
        logger.error(f"Error getting table sizes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Tag Monitoring Endpoints


@router.get("/tags/count", response_model=Dict[str, Any])
async def get_tag_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get tag count statistics."""
    try:
        monitor = TagMonitor(pg_session=db)
        return await monitor.get_tag_count()
    except Exception as e:
        logger.error(f"Error getting tag count: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/stale", response_model=Dict[str, Any])
async def get_stale_tags(
    hours: int = 24,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get stale tags (tags without recent data).

    Args:
        hours: Hours threshold for stale tags (default 24)
    """
    try:
        monitor = TagMonitor(pg_session=db)
        return await monitor.get_stale_tags(hours=hours)
    except Exception as e:
        logger.error(f"Error getting stale tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/influxdb-stats", response_model=Dict[str, Any])
async def get_influxdb_tag_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get InfluxDB storage and data rate statistics."""
    try:
        # TODO: Get InfluxDB client from app state or config
        monitor = TagMonitor(pg_session=db, influx_client=None)
        return await monitor.get_influxdb_stats()
    except Exception as e:
        logger.error(f"Error getting InfluxDB stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Overall Health Check Endpoint


@router.get("/health", response_model=Dict[str, Any])
async def get_overall_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive system health status.

    Checks:
    - System resources (CPU, RAM, disk)
    - Docker containers
    - Databases (PostgreSQL, InfluxDB)
    - Tags
    """
    try:
        # Gather all health checks
        system_health = SystemMonitor.check_health()

        docker_monitor = DockerMonitor()
        docker_health = docker_monitor.check_health() if docker_monitor.is_available() else {
            "status": "unavailable"
        }

        db_monitor = DatabaseMonitor(pg_session=db)
        database_health = await db_monitor.check_health()

        tag_monitor = TagMonitor(pg_session=db)
        tag_health = await tag_monitor.check_health()

        # Aggregate alerts
        all_alerts = []
        all_alerts.extend(system_health.get("alerts", []))
        all_alerts.extend(docker_health.get("alerts", []))
        all_alerts.extend(database_health.get("alerts", []))
        all_alerts.extend(tag_health.get("alerts", []))

        # Determine overall status
        statuses = [
            system_health.get("status"),
            docker_health.get("status"),
            database_health.get("status"),
            tag_health.get("status"),
        ]

        # Filter out unavailable status
        statuses = [s for s in statuses if s != "unavailable"]

        if "error" in statuses:
            overall_status = "error"
        elif "warning" in statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"

        return {
            "status": overall_status,
            "timestamp": system_health.get("timestamp"),
            "alerts": all_alerts,
            "components": {
                "system": system_health,
                "docker": docker_health,
                "database": database_health,
                "tags": tag_health,
            }
        }

    except Exception as e:
        logger.error(f"Error getting overall health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=Dict[str, Any])
async def get_monitoring_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get high-level monitoring summary for dashboard display.

    Returns key metrics without detailed data.
    """
    try:
        # System metrics
        cpu = SystemMonitor.get_cpu_metrics()
        memory = SystemMonitor.get_memory_metrics()
        disk = SystemMonitor.get_disk_metrics()

        # Docker
        docker_monitor = DockerMonitor()
        docker_stats = docker_monitor.get_container_stats() if docker_monitor.is_available() else None

        # Database
        db_monitor = DatabaseMonitor(pg_session=db)
        pg_health = await db_monitor.get_postgres_health()

        # Tags
        tag_monitor = TagMonitor(pg_session=db)
        tag_count = await tag_monitor.get_tag_count()
        stale_tags = await tag_monitor.get_stale_tags()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "system": {
                    "cpu_percent": cpu.get("percent"),
                    "memory_percent": memory.get("percent"),
                    "disk_percent": disk.get("root", {}).get("percent"),
                    "status": cpu.get("status"),
                },
                "docker": {
                    "running_containers": docker_stats.get("container_count", 0) if docker_stats else 0,
                    "status": docker_stats.get("status", "unavailable") if docker_stats else "unavailable",
                },
                "database": {
                    "postgres_size_gb": pg_health.get("database_size_gb"),
                    "postgres_connections": pg_health.get("total_connections"),
                    "status": pg_health.get("status"),
                },
                "tags": {
                    "total_tags": tag_count.get("total_tags", 0),
                    "stale_tags": stale_tags.get("stale_count", 0),
                    "stale_percent": stale_tags.get("stale_percent", 0),
                }
            }
        }

    except Exception as e:
        logger.error(f"Error getting monitoring summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
