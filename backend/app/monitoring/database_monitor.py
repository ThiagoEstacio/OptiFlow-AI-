"""
Database Monitor

Monitors PostgreSQL and InfluxDB health, performance, and storage.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

try:
    from influxdb_client import InfluxDBClient
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    InfluxDBClient = None

logger = logging.getLogger(__name__)


class DatabaseMonitor:
    """
    Database health monitoring for PostgreSQL and InfluxDB.

    Provides metrics for:
    - Connection status
    - Connection pool usage
    - Database size
    - Active connections
    - Query performance
    - Table/measurement counts
    """

    # Alert thresholds
    CONNECTION_POOL_THRESHOLD = 80  # %
    QUERY_TIME_THRESHOLD = 1000  # ms

    def __init__(self, pg_session: AsyncSession, influx_client: Optional[InfluxDBClient] = None):
        self.pg_session = pg_session
        self.influx_client = influx_client

    async def get_postgres_health(self) -> Dict[str, Any]:
        """
        Get PostgreSQL health metrics.

        Returns:
            Dictionary with PostgreSQL health metrics
        """
        try:
            # Test connection
            start_time = datetime.now()
            await self.pg_session.execute(text("SELECT 1"))
            query_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Database size
            result = await self.pg_session.execute(text(
                "SELECT pg_database_size(current_database()) as size"
            ))
            db_size_bytes = result.scalar()

            # Active connections
            result = await self.pg_session.execute(text(
                """
                SELECT count(*) as active_connections
                FROM pg_stat_activity
                WHERE state = 'active'
                """
            ))
            active_connections = result.scalar()

            # Total connections
            result = await self.pg_session.execute(text(
                """
                SELECT count(*) as total_connections
                FROM pg_stat_activity
                """
            ))
            total_connections = result.scalar()

            # Max connections
            result = await self.pg_session.execute(text(
                "SHOW max_connections"
            ))
            max_connections = int(result.scalar())

            # Connection pool usage percentage
            pool_usage = (total_connections / max_connections) * 100 if max_connections > 0 else 0

            # Database version
            result = await self.pg_session.execute(text("SELECT version()"))
            version = result.scalar()

            # Cache hit ratio
            result = await self.pg_session.execute(text(
                """
                SELECT
                    sum(heap_blks_hit) / nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100 as cache_hit_ratio
                FROM pg_statio_user_tables
                """
            ))
            cache_hit_ratio = result.scalar() or 0

            # Table count
            result = await self.pg_session.execute(text(
                """
                SELECT count(*) as table_count
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            ))
            table_count = result.scalar()

            # Determine status
            status = "healthy"
            if pool_usage > self.CONNECTION_POOL_THRESHOLD:
                status = "warning"
                logger.warning(f"High PostgreSQL connection pool usage: {pool_usage:.1f}%")
            if query_time_ms > self.QUERY_TIME_THRESHOLD:
                status = "warning"
                logger.warning(f"Slow PostgreSQL query response: {query_time_ms:.1f}ms")

            return {
                "status": status,
                "connection": "connected",
                "version": version,
                "query_time_ms": round(query_time_ms, 2),
                "database_size_bytes": db_size_bytes,
                "database_size_mb": round(db_size_bytes / (1024**2), 2),
                "database_size_gb": round(db_size_bytes / (1024**3), 2),
                "active_connections": active_connections,
                "total_connections": total_connections,
                "max_connections": max_connections,
                "pool_usage_percent": round(pool_usage, 2),
                "cache_hit_ratio": round(cache_hit_ratio, 2),
                "table_count": table_count,
            }

        except Exception as e:
            logger.error(f"Error getting PostgreSQL health: {e}")
            return {
                "status": "error",
                "connection": "failed",
                "error": str(e),
            }

    async def get_influxdb_health(self) -> Dict[str, Any]:
        """
        Get InfluxDB health metrics.

        Returns:
            Dictionary with InfluxDB health metrics
        """
        if not self.influx_client or not INFLUXDB_AVAILABLE:
            return {
                "status": "unavailable",
                "error": "InfluxDB client not configured",
            }

        try:
            # Test connection
            start_time = datetime.now()
            health = self.influx_client.health()
            query_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Get organization and bucket info
            org_api = self.influx_client.organizations_api()
            orgs = org_api.find_organizations()

            bucket_api = self.influx_client.buckets_api()
            buckets = bucket_api.find_buckets().buckets

            # Determine status
            status = "healthy" if health.status == "pass" else "warning"

            if query_time_ms > self.QUERY_TIME_THRESHOLD:
                status = "warning"
                logger.warning(f"Slow InfluxDB query response: {query_time_ms:.1f}ms")

            return {
                "status": status,
                "connection": "connected",
                "health_status": health.status,
                "health_message": health.message,
                "version": health.version,
                "query_time_ms": round(query_time_ms, 2),
                "organization_count": len(orgs),
                "bucket_count": len(buckets),
                "buckets": [
                    {
                        "name": bucket.name,
                        "id": bucket.id,
                        "retention_rules": [
                            {
                                "type": rule.type,
                                "every_seconds": rule.every_seconds,
                            }
                            for rule in bucket.retention_rules
                        ] if bucket.retention_rules else [],
                    }
                    for bucket in buckets
                ],
            }

        except Exception as e:
            logger.error(f"Error getting InfluxDB health: {e}")
            return {
                "status": "error",
                "connection": "failed",
                "error": str(e),
            }

    async def get_postgres_table_sizes(self) -> Dict[str, Any]:
        """
        Get sizes of all PostgreSQL tables.

        Returns:
            Dictionary with table size information
        """
        try:
            result = await self.pg_session.execute(text(
                """
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 20
                """
            ))

            tables = []
            for row in result:
                tables.append({
                    "schema": row.schemaname,
                    "table": row.tablename,
                    "size": row.size,
                    "size_bytes": row.size_bytes,
                    "size_mb": round(row.size_bytes / (1024**2), 2),
                })

            return {
                "status": "success",
                "tables": tables,
            }

        except Exception as e:
            logger.error(f"Error getting PostgreSQL table sizes: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    async def check_health(self) -> Dict[str, Any]:
        """
        Check overall database health.

        Returns:
            Dictionary with health status and alerts
        """
        alerts = []
        overall_status = "healthy"

        # Check PostgreSQL
        pg_health = await self.get_postgres_health()
        if pg_health.get("status") != "healthy":
            alerts.append(f"PostgreSQL: {pg_health.get('status')}")
            if pg_health.get("status") == "error":
                overall_status = "error"
            else:
                overall_status = "warning"

        # Check InfluxDB
        influx_health = await self.get_influxdb_health()
        if influx_health.get("status") not in ["healthy", "unavailable"]:
            alerts.append(f"InfluxDB: {influx_health.get('status')}")
            if influx_health.get("status") == "error":
                overall_status = "error"
            else:
                overall_status = "warning"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "alerts": alerts,
            "postgresql": {
                "status": pg_health.get("status"),
                "connection": pg_health.get("connection"),
                "pool_usage_percent": pg_health.get("pool_usage_percent"),
                "database_size_gb": pg_health.get("database_size_gb"),
            },
            "influxdb": {
                "status": influx_health.get("status"),
                "connection": influx_health.get("connection"),
            }
        }
