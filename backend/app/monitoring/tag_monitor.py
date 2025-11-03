"""
Tag Monitor

Monitors tag statistics: total count, data rates, storage, stale tags.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from app.models.tag import Tag

try:
    from influxdb_client import InfluxDBClient
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    InfluxDBClient = None

logger = logging.getLogger(__name__)


class TagMonitor:
    """
    Tag statistics monitoring.

    Provides metrics for:
    - Total tag count
    - Active vs stale tags
    - Data points per minute
    - Storage usage
    - Tag distribution by device/site
    """

    # Alert thresholds
    STALE_TAG_THRESHOLD = 20  # %
    STALE_TAG_HOURS = 24  # Hours without data

    def __init__(self, pg_session: AsyncSession, influx_client: Optional[InfluxDBClient] = None):
        self.pg_session = pg_session
        self.influx_client = influx_client

    async def get_tag_count(self) -> Dict[str, Any]:
        """
        Get total tag count from PostgreSQL.

        Returns:
            Dictionary with tag count metrics
        """
        try:
            # Total tags
            result = await self.pg_session.execute(
                select(func.count(Tag.id))
            )
            total_tags = result.scalar() or 0

            # Tags by type
            result = await self.pg_session.execute(
                select(Tag.tag_type, func.count(Tag.id))
                .group_by(Tag.tag_type)
            )
            tags_by_type = {row[0]: row[1] for row in result}

            # Tags by device
            result = await self.pg_session.execute(text(
                """
                SELECT d.name as device_name, COUNT(t.id) as tag_count
                FROM tags t
                JOIN devices d ON t.device_id = d.id
                GROUP BY d.name
                ORDER BY tag_count DESC
                LIMIT 10
                """
            ))
            tags_by_device = [
                {"device": row.device_name, "count": row.tag_count}
                for row in result
            ]

            return {
                "status": "success",
                "total_tags": total_tags,
                "tags_by_type": tags_by_type,
                "top_devices": tags_by_device,
            }

        except Exception as e:
            logger.error(f"Error getting tag count: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    async def get_stale_tags(self, hours: int = 24) -> Dict[str, Any]:
        """
        Identify tags that haven't received data recently.

        Args:
            hours: Hours threshold for stale tags

        Returns:
            Dictionary with stale tag information
        """
        try:
            # Get tags with last_value_at older than threshold
            threshold = datetime.utcnow() - timedelta(hours=hours)

            result = await self.pg_session.execute(
                select(Tag)
                .where(
                    (Tag.last_value_at < threshold) |
                    (Tag.last_value_at.is_(None))
                )
            )
            stale_tags = result.scalars().all()

            # Total tags for percentage
            result = await self.pg_session.execute(
                select(func.count(Tag.id))
            )
            total_tags = result.scalar() or 1

            stale_count = len(stale_tags)
            stale_percent = (stale_count / total_tags) * 100

            status = "healthy"
            if stale_percent > self.STALE_TAG_THRESHOLD:
                status = "warning"
                logger.warning(f"High percentage of stale tags: {stale_percent:.1f}%")

            return {
                "status": status,
                "stale_count": stale_count,
                "total_count": total_tags,
                "stale_percent": round(stale_percent, 2),
                "threshold_hours": hours,
                "stale_tags": [
                    {
                        "id": tag.id,
                        "name": tag.name,
                        "device_id": tag.device_id,
                        "last_value_at": tag.last_value_at.isoformat() if tag.last_value_at else None,
                    }
                    for tag in stale_tags[:20]  # Limit to 20 examples
                ],
            }

        except Exception as e:
            logger.error(f"Error getting stale tags: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    async def get_influxdb_stats(self) -> Dict[str, Any]:
        """
        Get InfluxDB storage and data rate statistics.

        Returns:
            Dictionary with InfluxDB statistics
        """
        if not self.influx_client or not INFLUXDB_AVAILABLE:
            return {
                "status": "unavailable",
                "error": "InfluxDB client not configured",
            }

        try:
            query_api = self.influx_client.query_api()

            # Get data point count for last 24 hours
            query = '''
            from(bucket: "optiflow")
                |> range(start: -24h)
                |> count()
            '''

            tables = query_api.query(query)

            total_points = 0
            for table in tables:
                for record in table.records:
                    total_points += record.get_value()

            # Calculate data rate (points per minute)
            data_rate = total_points / (24 * 60) if total_points > 0 else 0

            # Get measurement count
            query = '''
            import "influxdata/influxdb/schema"
            schema.measurements(bucket: "optiflow")
            '''

            tables = query_api.query(query)
            measurement_count = sum(len(table.records) for table in tables)

            return {
                "status": "healthy",
                "data_points_24h": total_points,
                "data_rate_per_minute": round(data_rate, 2),
                "data_rate_per_second": round(data_rate / 60, 2),
                "measurement_count": measurement_count,
            }

        except Exception as e:
            logger.error(f"Error getting InfluxDB stats: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    async def get_tag_value_distribution(self) -> Dict[str, Any]:
        """
        Get distribution of tag values (min, max, avg) for recent data.

        Returns:
            Dictionary with value distribution statistics
        """
        try:
            # Get aggregate statistics for numeric tags
            result = await self.pg_session.execute(text(
                """
                SELECT
                    COUNT(*) as total_tags,
                    COUNT(CASE WHEN last_value IS NOT NULL THEN 1 END) as tags_with_values,
                    AVG(CASE WHEN last_value ~ '^[0-9.]+$' THEN last_value::numeric END) as avg_value,
                    MIN(CASE WHEN last_value ~ '^[0-9.]+$' THEN last_value::numeric END) as min_value,
                    MAX(CASE WHEN last_value ~ '^[0-9.]+$' THEN last_value::numeric END) as max_value
                FROM tags
                WHERE tag_type IN ('analog', 'counter', 'sensor')
                """
            ))

            row = result.first()

            return {
                "status": "success",
                "total_tags": row.total_tags,
                "tags_with_values": row.tags_with_values,
                "avg_value": round(float(row.avg_value), 2) if row.avg_value else None,
                "min_value": round(float(row.min_value), 2) if row.min_value else None,
                "max_value": round(float(row.max_value), 2) if row.max_value else None,
            }

        except Exception as e:
            logger.error(f"Error getting tag value distribution: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    async def check_health(self) -> Dict[str, Any]:
        """
        Check overall tag health.

        Returns:
            Dictionary with health status and alerts
        """
        alerts = []
        overall_status = "healthy"

        # Check stale tags
        stale_tags = await self.get_stale_tags(hours=self.STALE_TAG_HOURS)
        if stale_tags.get("status") == "warning":
            alerts.append(
                f"{stale_tags.get('stale_count')} tags ({stale_tags.get('stale_percent'):.1f}%) are stale"
            )
            overall_status = "warning"

        # Get tag count
        tag_count = await self.get_tag_count()
        total_tags = tag_count.get("total_tags", 0)

        if total_tags == 0:
            alerts.append("No tags configured")
            overall_status = "warning"

        # Check InfluxDB stats
        influx_stats = await self.get_influxdb_stats()
        data_rate = influx_stats.get("data_rate_per_minute", 0)

        if data_rate == 0:
            alerts.append("No data being written to InfluxDB")
            overall_status = "warning"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "alerts": alerts,
            "summary": {
                "total_tags": total_tags,
                "stale_tags": stale_tags.get("stale_count", 0),
                "stale_percent": stale_tags.get("stale_percent", 0),
                "data_rate_per_minute": data_rate,
            }
        }
