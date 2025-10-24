"""
Time Series Service

Store and query historical PLC data using InfluxDB
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    HAS_INFLUXDB = True
except ImportError:
    HAS_INFLUXDB = False

logger = logging.getLogger(__name__)


class TimeSeriesService:
    """Service for time series data storage and retrieval"""

    def __init__(
        self,
        url: str = "http://localhost:8086",
        token: str = "my-token",
        org: str = "smartport",
        bucket: str = "plc_data"
    ):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client: Optional[InfluxDBClient] = None
        self.write_api = None
        self.query_api = None

        if HAS_INFLUXDB:
            try:
                self.client = InfluxDBClient(url=url, token=token, org=org)
                self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
                self.query_api = self.client.query_api()
                logger.info(f"Connected to InfluxDB: {url}")
            except Exception as e:
                logger.error(f"Failed to connect to InfluxDB: {e}")
        else:
            logger.warning("influxdb-client not installed. Install: pip install influxdb-client")

    def write_tag_value(
        self,
        tag_name: str,
        value: Any,
        timestamp: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Write a tag value to time series database

        Args:
            tag_name: Tag name
            value: Tag value
            timestamp: Timestamp (default: now)
            tags: Additional tags (e.g., {"location": "berth_1", "equipment": "crane"})
        """
        if not self.write_api:
            return

        try:
            point = Point("plc_tag") \
                .tag("tag_name", tag_name)

            # Add additional tags
            if tags:
                for key, val in tags.items():
                    point = point.tag(key, val)

            # Add value as field
            if isinstance(value, bool):
                point = point.field("value", int(value))
            elif isinstance(value, (int, float)):
                point = point.field("value", float(value))
            else:
                point = point.field("value", str(value))

            # Set timestamp
            if timestamp:
                point = point.time(timestamp, WritePrecision.NS)

            self.write_api.write(bucket=self.bucket, record=point)

        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")

    def write_batch(self, data_points: List[Dict[str, Any]]):
        """
        Write multiple data points in batch

        Args:
            data_points: List of dicts with keys: tag_name, value, timestamp, tags
        """
        if not self.write_api:
            return

        try:
            points = []
            for dp in data_points:
                point = Point("plc_tag") \
                    .tag("tag_name", dp["tag_name"]) \
                    .field("value", float(dp["value"]))

                if "tags" in dp:
                    for key, val in dp["tags"].items():
                        point = point.tag(key, val)

                if "timestamp" in dp:
                    point = point.time(dp["timestamp"], WritePrecision.NS)

                points.append(point)

            self.write_api.write(bucket=self.bucket, record=points)

        except Exception as e:
            logger.error(f"Error writing batch to InfluxDB: {e}")

    def query_tag_history(
        self,
        tag_name: str,
        start: datetime,
        end: Optional[datetime] = None,
        aggregate: Optional[str] = None,
        window: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query historical data for a tag

        Args:
            tag_name: Tag name to query
            start: Start time
            end: End time (default: now)
            aggregate: Aggregation function (mean, min, max, sum)
            window: Aggregation window (e.g., "1m", "5m", "1h")

        Returns:
            List of {time, value} dicts
        """
        if not self.query_api:
            return []

        try:
            end = end or datetime.utcnow()

            # Build Flux query
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
                |> filter(fn: (r) => r["_measurement"] == "plc_tag")
                |> filter(fn: (r) => r["tag_name"] == "{tag_name}")
                |> filter(fn: (r) => r["_field"] == "value")
            '''

            # Add aggregation if specified
            if aggregate and window:
                query += f'''
                |> aggregateWindow(every: {window}, fn: {aggregate}, createEmpty: false)
                '''

            query += '|> yield(name: "result")'

            # Execute query
            result = self.query_api.query(query=query)

            # Parse results
            data = []
            for table in result:
                for record in table.records:
                    data.append({
                        "time": record.get_time().isoformat(),
                        "value": record.get_value(),
                    })

            return data

        except Exception as e:
            logger.error(f"Error querying InfluxDB: {e}")
            return []

    def query_multiple_tags(
        self,
        tag_names: List[str],
        start: datetime,
        end: Optional[datetime] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Query multiple tags at once"""
        results = {}

        for tag_name in tag_names:
            results[tag_name] = self.query_tag_history(tag_name, start, end)

        return results

    def query_statistics(
        self,
        tag_name: str,
        start: datetime,
        end: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Calculate statistics for a tag over a period

        Returns:
            Dict with mean, min, max, stddev
        """
        if not self.query_api:
            return {}

        try:
            end = end or datetime.utcnow()

            queries = {
                "mean": f'''
                from(bucket: "{self.bucket}")
                    |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
                    |> filter(fn: (r) => r["tag_name"] == "{tag_name}")
                    |> mean()
                ''',
                "min": f'''
                from(bucket: "{self.bucket}")
                    |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
                    |> filter(fn: (r) => r["tag_name"] == "{tag_name}")
                    |> min()
                ''',
                "max": f'''
                from(bucket: "{self.bucket}")
                    |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
                    |> filter(fn: (r) => r["tag_name"] == "{tag_name}")
                    |> max()
                ''',
                "stddev": f'''
                from(bucket: "{self.bucket}")
                    |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
                    |> filter(fn: (r) => r["tag_name"] == "{tag_name}")
                    |> stddev()
                '''
            }

            stats = {}
            for stat_name, query in queries.items():
                result = self.query_api.query(query=query)
                if result and len(result) > 0 and len(result[0].records) > 0:
                    stats[stat_name] = result[0].records[0].get_value()

            return stats

        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}

    def close(self):
        """Close InfluxDB connection"""
        if self.client:
            self.client.close()


# Demo time series service with in-memory storage
class DemoTimeSeriesService(TimeSeriesService):
    """Demo time series service for testing without InfluxDB"""

    def __init__(self):
        self.data: Dict[str, List[Dict[str, Any]]] = {}
        logger.info("Using demo time series service (in-memory)")

    def write_tag_value(
        self,
        tag_name: str,
        value: Any,
        timestamp: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """Store in memory"""
        if tag_name not in self.data:
            self.data[tag_name] = []

        self.data[tag_name].append({
            "time": (timestamp or datetime.utcnow()).isoformat(),
            "value": value,
            "tags": tags or {}
        })

        # Keep only last 10000 points per tag
        if len(self.data[tag_name]) > 10000:
            self.data[tag_name] = self.data[tag_name][-10000:]

    def query_tag_history(
        self,
        tag_name: str,
        start: datetime,
        end: Optional[datetime] = None,
        aggregate: Optional[str] = None,
        window: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query from memory"""
        if tag_name not in self.data:
            return []

        end = end or datetime.utcnow()

        # Filter by time range
        filtered = [
            point for point in self.data[tag_name]
            if start <= datetime.fromisoformat(point["time"]) <= end
        ]

        # Simple aggregation (if requested)
        if aggregate and window and filtered:
            # Just return sampled data for demo
            step = max(1, len(filtered) // 100)
            filtered = filtered[::step]

        return [{"time": p["time"], "value": p["value"]} for p in filtered]

    def query_statistics(
        self,
        tag_name: str,
        start: datetime,
        end: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Calculate simple statistics"""
        history = self.query_tag_history(tag_name, start, end)

        if not history:
            return {}

        values = [p["value"] for p in history if isinstance(p["value"], (int, float))]

        if not values:
            return {}

        import statistics

        return {
            "mean": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "stddev": statistics.stdev(values) if len(values) > 1 else 0
        }


# Global time series service
# Use DemoTimeSeriesService for demo, TimeSeriesService for production with InfluxDB
timeseries_service = DemoTimeSeriesService()
