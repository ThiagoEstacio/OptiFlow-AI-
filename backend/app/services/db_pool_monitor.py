"""
Database Connection Pool Monitor

Monitors PostgreSQL connection pool health and prevents exhaustion.

Features:
- Real-time pool usage tracking
- Automatic alerts on high usage
- Pool exhaustion prevention
- Connection leak detection
- Performance metrics
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.pool import Pool
from sqlalchemy.engine import Engine
import asyncio

logger = logging.getLogger(__name__)


class DatabasePoolMonitor:
    """
    Monitor for SQLAlchemy connection pool.

    Tracks:
    - Pool size and usage
    - Connection leaks
    - High usage patterns
    - Performance metrics
    """

    def __init__(
        self,
        engine: Optional[Engine] = None,
        warning_threshold: float = 0.8,  # Warn at 80% pool usage
        critical_threshold: float = 0.95  # Critical at 95% pool usage
    ):
        self.engine = engine
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

        # Metrics
        self.total_checkouts = 0
        self.total_checkins = 0
        self.peak_usage = 0
        self.peak_usage_time: Optional[datetime] = None
        self.warning_count = 0
        self.critical_count = 0

        # Leak detection
        self.checkout_times: Dict[int, datetime] = {}
        self.leak_threshold_seconds = 300  # 5 minutes

    def set_engine(self, engine: Engine):
        """Set the database engine to monitor."""
        self.engine = engine

    def get_pool_status(self) -> Dict[str, Any]:
        """
        Get current connection pool status.

        Returns:
            {
                "pool_size": int,
                "connections_in_use": int,
                "connections_available": int,
                "usage_percent": float,
                "overflow": int,
                "status": "healthy" | "warning" | "critical",
                "potential_leaks": int
            }
        """
        if not self.engine:
            return {
                "status": "unknown",
                "error": "No engine configured"
            }

        pool: Pool = self.engine.pool

        # Get pool metrics
        pool_size = pool.size()
        checked_out = pool.checkedout()
        available = pool_size - checked_out
        overflow = pool.overflow() if hasattr(pool, 'overflow') else 0

        # Calculate usage
        usage_percent = (checked_out / pool_size * 100) if pool_size > 0 else 0

        # Track peak usage
        if checked_out > self.peak_usage:
            self.peak_usage = checked_out
            self.peak_usage_time = datetime.utcnow()

        # Determine status
        if usage_percent >= self.critical_threshold * 100:
            status = "critical"
            self.critical_count += 1
            logger.error(
                f"⚠️  DATABASE POOL CRITICAL: {checked_out}/{pool_size} connections in use "
                f"({usage_percent:.1f}%)"
            )
        elif usage_percent >= self.warning_threshold * 100:
            status = "warning"
            self.warning_count += 1
            logger.warning(
                f"⚠️  DATABASE POOL WARNING: {checked_out}/{pool_size} connections in use "
                f"({usage_percent:.1f}%)"
            )
        else:
            status = "healthy"

        # Detect potential leaks
        potential_leaks = self._detect_leaks()

        return {
            "pool_size": pool_size,
            "connections_in_use": checked_out,
            "connections_available": available,
            "usage_percent": round(usage_percent, 2),
            "overflow": overflow,
            "status": status,
            "potential_leaks": potential_leaks,
            "peak_usage": {
                "connections": self.peak_usage,
                "timestamp": self.peak_usage_time.isoformat() if self.peak_usage_time else None
            },
            "metrics": {
                "total_checkouts": self.total_checkouts,
                "total_checkins": self.total_checkins,
                "warning_count": self.warning_count,
                "critical_count": self.critical_count
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    def _detect_leaks(self) -> int:
        """
        Detect potential connection leaks.

        Returns:
            Number of connections checked out for longer than threshold
        """
        now = datetime.utcnow()
        leak_count = 0

        for conn_id, checkout_time in list(self.checkout_times.items()):
            elapsed = (now - checkout_time).total_seconds()

            if elapsed > self.leak_threshold_seconds:
                leak_count += 1
                logger.warning(
                    f"Potential connection leak detected: "
                    f"Connection {conn_id} checked out for {elapsed:.0f}s"
                )

        return leak_count

    def on_checkout(self, connection_id: int):
        """Track when a connection is checked out."""
        self.total_checkouts += 1
        self.checkout_times[connection_id] = datetime.utcnow()

    def on_checkin(self, connection_id: int):
        """Track when a connection is checked in."""
        self.total_checkins += 1
        if connection_id in self.checkout_times:
            del self.checkout_times[connection_id]

    def get_health_check(self) -> Dict[str, Any]:
        """
        Get health check status for monitoring systems.

        Returns:
            {
                "healthy": bool,
                "status": str,
                "usage_percent": float,
                "message": str
            }
        """
        status = self.get_pool_status()

        return {
            "healthy": status["status"] == "healthy",
            "status": status["status"],
            "usage_percent": status["usage_percent"],
            "connections_in_use": status["connections_in_use"],
            "connections_available": status["connections_available"],
            "message": self._get_status_message(status)
        }

    def _get_status_message(self, status: Dict[str, Any]) -> str:
        """Generate human-readable status message."""
        usage = status["usage_percent"]
        in_use = status["connections_in_use"]
        total = status["pool_size"]

        if status["status"] == "critical":
            return f"CRITICAL: Connection pool near exhaustion ({in_use}/{total} used, {usage:.1f}%)"
        elif status["status"] == "warning":
            return f"WARNING: High connection pool usage ({in_use}/{total} used, {usage:.1f}%)"
        else:
            return f"Healthy: Connection pool normal ({in_use}/{total} used, {usage:.1f}%)"

    async def monitor_loop(self, interval_seconds: int = 30):
        """
        Continuous monitoring loop (for background task).

        Args:
            interval_seconds: How often to check pool status
        """
        logger.info(f"Starting database pool monitor (interval: {interval_seconds}s)")

        while True:
            try:
                status = self.get_pool_status()

                # Log critical issues
                if status["status"] == "critical":
                    logger.error(f"DATABASE POOL CRITICAL: {status}")
                elif status["status"] == "warning":
                    logger.warning(f"DATABASE POOL WARNING: {status}")

                # Check for leaks
                if status["potential_leaks"] > 0:
                    logger.error(
                        f"⚠️  {status['potential_leaks']} potential connection leak(s) detected"
                    )

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Error in pool monitor loop: {e}", exc_info=True)
                await asyncio.sleep(interval_seconds)


# Global monitor instance
_pool_monitor: Optional[DatabasePoolMonitor] = None


def get_pool_monitor() -> DatabasePoolMonitor:
    """Get or create global pool monitor instance."""
    global _pool_monitor

    if _pool_monitor is None:
        _pool_monitor = DatabasePoolMonitor()

    return _pool_monitor


def init_pool_monitor(engine: Engine) -> DatabasePoolMonitor:
    """
    Initialize pool monitor with database engine.

    Args:
        engine: SQLAlchemy engine to monitor

    Returns:
        DatabasePoolMonitor instance
    """
    monitor = get_pool_monitor()
    monitor.set_engine(engine)

    logger.info("Database pool monitor initialized")

    return monitor
