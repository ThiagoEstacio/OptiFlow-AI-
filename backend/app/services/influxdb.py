"""
InfluxDB service for time series data operations
"""
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class InfluxDBService:
    """
    Service for interacting with InfluxDB
    """

    def __init__(self):
        self.client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG,
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        self.bucket = settings.INFLUXDB_BUCKET
        self.org = settings.INFLUXDB_ORG

    def write_point(
        self,
        tag_id: str,
        value: float,
        timestamp: Optional[datetime] = None,
        quality: str = "good",
        additional_tags: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Write a single data point to InfluxDB

        Args:
            tag_id: UUID of the tag
            value: Measurement value
            timestamp: Timestamp (defaults to now)
            quality: Data quality indicator
            additional_tags: Additional tags to add to the point

        Returns:
            True if successful, False otherwise
        """
        try:
            point = Point("tag_data") \
                .tag("tag_id", str(tag_id)) \
                .tag("quality", quality) \
                .field("value", float(value))

            if additional_tags:
                for key, val in additional_tags.items():
                    point.tag(key, str(val))

            if timestamp:
                point.time(timestamp)

            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True

        except Exception as e:
            logger.error(f"Error writing point to InfluxDB: {e}")
            return False

    def write_batch(
        self,
        points: List[Dict[str, Any]]
    ) -> bool:
        """
        Write multiple data points in batch

        Args:
            points: List of point dictionaries
                [
                    {
                        "tag_id": "uuid",
                        "value": 42.5,
                        "timestamp": datetime,
                        "quality": "good",
                        "device_id": "device_uuid",
                        "site_id": "site_uuid"
                    },
                    ...
                ]

        Returns:
            True if successful, False otherwise
        """
        try:
            influx_points = []

            for p in points:
                point = Point("tag_data") \
                    .tag("tag_id", str(p["tag_id"])) \
                    .tag("quality", p.get("quality", "good")) \
                    .field("value", float(p["value"]))

                # Add optional tags
                if "device_id" in p:
                    point.tag("device_id", str(p["device_id"]))
                if "site_id" in p:
                    point.tag("site_id", str(p["site_id"]))
                if "category" in p:
                    point.tag("category", p["category"])

                # Set timestamp
                if "timestamp" in p:
                    point.time(p["timestamp"])

                influx_points.append(point)

            self.write_api.write(bucket=self.bucket, org=self.org, record=influx_points)
            logger.info(f"Wrote {len(influx_points)} points to InfluxDB")
            return True

        except Exception as e:
            logger.error(f"Error writing batch to InfluxDB: {e}")
            return False

    def query_tag_data(
        self,
        tag_id: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        aggregation: Optional[str] = None,
        interval: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query historical data for a tag

        Args:
            tag_id: UUID of the tag
            start_time: Start time for query
            end_time: End time (defaults to now)
            aggregation: Aggregation function (mean, min, max, sum, count)
            interval: Aggregation interval (e.g., "1m", "5m", "1h")

        Returns:
            List of data points
        """
        try:
            if end_time is None:
                end_time = datetime.utcnow()

            # Format timestamps in RFC3339 format (required by InfluxDB)
            start_str = start_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            end_str = end_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

            # Build Flux query
            query = f'''from(bucket: "{self.bucket}")
  |> range(start: {start_str}, stop: {end_str})
  |> filter(fn: (r) => r["_measurement"] == "tag_data")
  |> filter(fn: (r) => r["tag_id"] == "{tag_id}")
  |> filter(fn: (r) => r["_field"] == "value")'''

            # Add aggregation if specified
            if aggregation and interval:
                agg_func = aggregation.lower()
                query += f'''
  |> aggregateWindow(every: {interval}, fn: {agg_func}, createEmpty: false)'''

            query += '''
  |> yield(name: "result")'''

            logger.debug(f"InfluxDB query for tag {tag_id}: {query}")

            # Execute query
            tables = self.query_api.query(query, org=self.org)

            # Parse results
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "timestamp": record.get_time().isoformat() + "Z",
                        "value": record.get_value(),
                        "quality": record.values.get("quality", "good")
                    })

            logger.info(f"InfluxDB query returned {len(results)} points for tag {tag_id}")
            return results

        except Exception as e:
            logger.error(f"Error querying InfluxDB for tag {tag_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def query_multiple_tags(
        self,
        tag_ids: List[str],
        start_time: datetime,
        end_time: Optional[datetime] = None,
        aggregation: Optional[str] = None,
        interval: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Query data for multiple tags

        Args:
            tag_ids: List of tag UUIDs
            start_time: Start time
            end_time: End time
            aggregation: Aggregation function
            interval: Aggregation interval

        Returns:
            Dictionary mapping tag_id to list of data points
        """
        results = {}
        for tag_id in tag_ids:
            results[tag_id] = self.query_tag_data(
                tag_id, start_time, end_time, aggregation, interval
            )
        return results

    def get_latest_value(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest value for a tag

        Args:
            tag_id: UUID of the tag

        Returns:
            Latest data point or None
        """
        try:
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -24h)
                |> filter(fn: (r) => r["_measurement"] == "tag_data")
                |> filter(fn: (r) => r["tag_id"] == "{tag_id}")
                |> filter(fn: (r) => r["_field"] == "value")
                |> last()
            '''

            tables = self.query_api.query(query, org=self.org)

            for table in tables:
                for record in table.records:
                    return {
                        "timestamp": record.get_time().isoformat(),
                        "value": record.get_value(),
                        "quality": record.values.get("quality", "unknown"),
                    }

            return None

        except Exception as e:
            logger.error(f"Error getting latest value: {e}")
            return None

    def get_statistics(
        self,
        tag_id: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, float]:
        """
        Get statistical summary for a tag

        Args:
            tag_id: UUID of the tag
            start_time: Start time
            end_time: End time

        Returns:
            Dictionary with statistics (min, max, mean, count)
        """
        try:
            if end_time is None:
                end_time = datetime.utcnow()

            stats = {}

            # Query for each statistic
            for stat in ["min", "max", "mean", "count"]:
                query = f'''
                    from(bucket: "{self.bucket}")
                    |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
                    |> filter(fn: (r) => r["_measurement"] == "tag_data")
                    |> filter(fn: (r) => r["tag_id"] == "{tag_id}")
                    |> filter(fn: (r) => r["_field"] == "value")
                    |> {stat}()
                '''

                tables = self.query_api.query(query, org=self.org)

                for table in tables:
                    for record in table.records:
                        stats[stat] = record.get_value()

            return stats

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

    def close(self):
        """Close InfluxDB client"""
        self.client.close()


# Global instance
influxdb_service = InfluxDBService()
