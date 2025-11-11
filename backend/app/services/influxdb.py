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
            skipped = 0

            for p in points:
                try:
                    # Validate value is numeric
                    value = p["value"]
                    if isinstance(value, str):
                        # Try to convert string to float
                        try:
                            value = float(value)
                        except (ValueError, TypeError):
                            logger.warning(f"Skipping non-numeric value '{value}' for tag {p.get('tag_id')}")
                            skipped += 1
                            continue

                    point = Point("tag_data") \
                        .tag("tag_id", str(p["tag_id"])) \
                        .tag("quality", p.get("quality", "good")) \
                        .field("value", float(value))

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

                except Exception as e:
                    logger.warning(f"Error processing point for tag {p.get('tag_id')}: {e}")
                    skipped += 1
                    continue

            if influx_points:
                self.write_api.write(bucket=self.bucket, org=self.org, record=influx_points)
                logger.info(f"Wrote {len(influx_points)} points to InfluxDB (skipped {skipped})")
            else:
                logger.warning(f"No valid points to write (skipped {skipped})")

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

    def get_latest_value_by_name(self, tag_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest value for a tag by tag name

        Args:
            tag_name: Name of the tag (e.g., 'TEST_COUNTER_PV')

        Returns:
            Latest data point or None
        """
        try:
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -24h)
                |> filter(fn: (r) => r["_measurement"] == "tag_data")
                |> filter(fn: (r) => r["tag_id"] == "{tag_name}")
                |> filter(fn: (r) => r["_field"] == "value")
                |> last()
            '''

            tables = self.query_api.query(query, org=self.org)

            for table in tables:
                for record in table.records:
                    return {
                        "tag_name": tag_name,
                        "timestamp": record.get_time().isoformat(),
                        "value": record.get_value(),
                        "quality": record.values.get("quality", "unknown"),
                        "source": record.values.get("source", "unknown")
                    }

            return None

        except Exception as e:
            logger.error(f"Error getting latest value for tag {tag_name}: {e}")
            return None

    def get_latest_values_by_names(self, tag_names: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get the latest values for multiple tags by name (optimized batch query)

        Args:
            tag_names: List of tag names (e.g., ['TEST_COUNTER_PV', 'WAREHOUSE_LEVEL_PCT_PV'])

        Returns:
            Dictionary mapping tag_name to latest data point or None
        """
        try:
            # Build filter for multiple tags
            tag_filter = ' or '.join([f'r["tag_id"] == "{name}"' for name in tag_names])

            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -24h)
                |> filter(fn: (r) => r["_measurement"] == "tag_data")
                |> filter(fn: (r) => {tag_filter})
                |> filter(fn: (r) => r["_field"] == "value")
                |> group(columns: ["tag_id"])
                |> last()
            '''

            tables = self.query_api.query(query, org=self.org)

            results = {}
            for table in tables:
                for record in table.records:
                    tag_name = record.values.get("tag_id")
                    results[tag_name] = {
                        "tag_name": tag_name,
                        "timestamp": record.get_time().isoformat(),
                        "value": record.get_value(),
                        "quality": record.values.get("quality", "unknown"),
                        "source": record.values.get("source", "unknown")
                    }

            # Fill in None for tags that weren't found
            for tag_name in tag_names:
                if tag_name not in results:
                    results[tag_name] = None

            return results

        except Exception as e:
            logger.error(f"Error getting latest values for multiple tags: {e}")
            return {tag_name: None for tag_name in tag_names}

    def list_all_measurements(self) -> List[str]:
        """
        Lista todas as 'measurements' (tags) disponíveis no InfluxDB

        Usa auto-discovery para encontrar todas as tags que estão recebendo dados.
        Esta é a fonte de verdade para quais tags existem no sistema.

        Returns:
            Lista de nomes de tags que existem no bucket
        """
        try:
            # Usa schema.measurements() do InfluxDB para listar todas as measurements
            query = f'''
                import "influxdata/influxdb/schema"
                schema.measurements(bucket: "{self.bucket}")
            '''

            tables = self.query_api.query(query, org=self.org)

            measurements = []
            for table in tables:
                for record in table.records:
                    measurement_name = record.get_value()
                    # Filtra apenas tag_data (ignora outros measurements como system metrics)
                    if measurement_name == "tag_data":
                        # Para tag_data, precisamos listar os tag_ids únicos
                        continue
                    measurements.append(measurement_name)

            # Se estamos usando tag_data como measurement, precisamos listar tag_ids
            if not measurements or "tag_data" in measurements:
                tag_query = f'''
                    from(bucket: "{self.bucket}")
                    |> range(start: -24h)
                    |> filter(fn: (r) => r["_measurement"] == "tag_data")
                    |> keep(columns: ["tag_id"])
                    |> distinct(column: "tag_id")
                '''

                tag_tables = self.query_api.query(tag_query, org=self.org)
                tag_ids = []

                for table in tag_tables:
                    for record in table.records:
                        tag_id = record.values.get("tag_id")
                        if tag_id and tag_id not in tag_ids:
                            tag_ids.append(tag_id)

                return tag_ids if tag_ids else measurements

            return measurements

        except Exception as e:
            logger.error(f"Error listing measurements from InfluxDB: {e}")
            return []

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

    # ==================== GBM LOGISTICS METHODS ====================

    def write_gbm_operation(
        self,
        site_id: int,
        operation_data: Dict[str, Any],
        operation_date: datetime
    ) -> bool:
        """
        Write a single GBM operation to InfluxDB.

        Args:
            site_id: Site ID
            operation_data: Operation data dict
            operation_date: Operation timestamp

        Returns:
            Success status
        """
        try:
            point = Point("gbm_operations") \
                .tag("site_id", str(site_id)) \
                .tag("operation_type", operation_data.get("operation_type", "unknown")) \
                .tag("product_type", operation_data.get("product_type", "unknown")) \
                .tag("vehicle_type", operation_data.get("vehicle_type", "unknown")) \
                .tag("status", operation_data.get("status", "completed")) \
                .time(operation_date)

            # Add all numeric fields
            if operation_data.get("net_weight_kg"):
                point.field("net_weight_kg", float(operation_data["net_weight_kg"]))
            if operation_data.get("loading_time_minutes"):
                point.field("loading_time_minutes", float(operation_data["loading_time_minutes"]))
            if operation_data.get("waiting_time_minutes"):
                point.field("waiting_time_minutes", float(operation_data["waiting_time_minutes"]))
            if operation_data.get("total_value"):
                point.field("total_value", float(operation_data["total_value"]))

            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True

        except Exception as e:
            logger.error(f"Error writing GBM operation to InfluxDB: {e}")
            return False

    def write_gbm_operations_batch(
        self,
        site_id: int,
        operations: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Write multiple GBM operations in batch.

        Args:
            site_id: Site ID
            operations: List of operation dicts

        Returns:
            Stats dict with success/failure counts
        """
        success = 0
        failed = 0
        points = []

        for op in operations:
            try:
                operation_date = op.get("operation_date")
                if isinstance(operation_date, str):
                    operation_date = datetime.fromisoformat(operation_date)

                point = Point("gbm_operations") \
                    .tag("site_id", str(site_id)) \
                    .tag("operation_type", op.get("operation_type", "unknown")) \
                    .tag("product_type", op.get("product_type", "unknown")) \
                    .tag("vehicle_type", op.get("vehicle_type", "unknown")) \
                    .tag("status", op.get("status", "completed")) \
                    .time(operation_date)

                # Add fields
                if op.get("net_weight_kg"):
                    point.field("net_weight_kg", float(op["net_weight_kg"]))
                if op.get("loading_time_minutes"):
                    point.field("loading_time_minutes", float(op["loading_time_minutes"]))
                if op.get("waiting_time_minutes"):
                    point.field("waiting_time_minutes", float(op["waiting_time_minutes"]))
                if op.get("total_value"):
                    point.field("total_value", float(op["total_value"]))

                points.append(point)
                success += 1

            except Exception as e:
                logger.error(f"Error creating GBM point: {e}")
                failed += 1

        # Batch write
        if points:
            try:
                self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            except Exception as e:
                logger.error(f"Error batch writing GBM to InfluxDB: {e}")
                failed += len(points)
                success = 0

        return {"success": success, "failed": failed}

    def query_monthly_aggregates(
        self,
        site_id: int,
        start_date,
        end_date
    ) -> List[Dict[str, Any]]:
        """
        Query comprehensive monthly aggregates from InfluxDB for GBM operations.
        """
        try:
            # Convert date to string for Flux query
            start_str = f"{start_date}T00:00:00Z"
            end_str = f"{end_date}T23:59:59Z"

            # Query for counts, sums, and averages
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: {start_str}, stop: {end_str})
              |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
              |> filter(fn: (r) => r["site_id"] == "{site_id}")
              |> aggregateWindow(every: 1mo, fn: mean, createEmpty: false)
            '''

            tables = self.query_api.query(query, org=self.org)
            monthly_data = {}

            for table in tables:
                for record in table.records:
                    month_key = record.get_time().strftime("%Y-%m")
                    if month_key not in monthly_data:
                        monthly_data[month_key] = {
                            "month": record.get_time(),
                            "operations": 0,
                            "total_weight": 0,
                            "total_revenue": 0,
                            "avg_loading_time": 0,
                            "avg_waiting_time": 0
                        }

                    field = record.get_field()
                    value = record.get_value()
                    if field == "net_weight_kg":
                        monthly_data[month_key]["total_weight"] = float(value) if value else 0
                    elif field == "loading_time_minutes":
                        monthly_data[month_key]["avg_loading_time"] = float(value) if value else 0
                    elif field == "waiting_time_minutes":
                        monthly_data[month_key]["avg_waiting_time"] = float(value) if value else 0
                    elif field == "total_value":
                        monthly_data[month_key]["total_revenue"] = float(value) if value else 0

            return sorted(monthly_data.values(), key=lambda x: x["month"])

        except Exception as e:
            logger.error(f"Error querying monthly aggregates: {e}")
            return []

    def query_daily_stats(
        self,
        site_id: int,
        start_date,
        end_date,
        metric: str = "net_weight_kg"
    ) -> List[Dict[str, Any]]:
        """Query daily statistics for a specific GBM metric."""
        try:
            start_str = f"{start_date}T00:00:00Z"
            end_str = f"{end_date}T23:59:59Z"

            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: {start_str}, stop: {end_str})
              |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
              |> filter(fn: (r) => r["site_id"] == "{site_id}")
              |> filter(fn: (r) => r["_field"] == "{metric}")
              |> aggregateWindow(every: 1d, fn: sum, createEmpty: false)
            '''

            tables = self.query_api.query(query, org=self.org)
            daily_data = []

            for table in tables:
                for record in table.records:
                    daily_data.append({
                        "date": record.get_time().date().isoformat(),
                        "operations": 1,
                        "value": float(record.get_value()) if record.get_value() else 0
                    })

            return sorted(daily_data, key=lambda x: x["date"])

        except Exception as e:
            logger.error(f"Error querying daily stats: {e}")
            return []

    def query_aggregated_metrics(
        self,
        site_id: int,
        start_date,
        end_date
    ) -> Dict[str, Any]:
        """Query aggregated metrics for a period (GBM operations)."""
        try:
            start_str = f"{start_date}T00:00:00Z"
            end_str = f"{end_date}T23:59:59Z"

            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: {start_str}, stop: {end_str})
              |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
              |> filter(fn: (r) => r["site_id"] == "{site_id}")
              |> mean()
            '''

            tables = self.query_api.query(query, org=self.org)
            metrics = {}

            for table in tables:
                for record in table.records:
                    field = record.get_field()
                    value = float(record.get_value()) if record.get_value() else 0
                    metrics[field] = value

            return {
                "operations": int(metrics.get("net_weight_kg", 0)),
                "tonnage": metrics.get("net_weight_kg", 0) / 1000,
                "revenue": metrics.get("total_value", 0),
                "avg_loading_time": metrics.get("loading_time_minutes", 0),
                "avg_waiting_time": metrics.get("waiting_time_minutes", 0)
            }

        except Exception as e:
            logger.error(f"Error querying aggregated metrics: {e}")
            return {
                "operations": 0,
                "tonnage": 0,
                "revenue": 0,
                "avg_loading_time": 0,
                "avg_waiting_time": 0
            }

    def query_seasonal_data(
        self,
        site_id: int,
        start_date,
        end_date
    ) -> List[Dict[str, Any]]:
        """Query data grouped by year and month for seasonal analysis."""
        try:
            start_str = f"{start_date}T00:00:00Z"
            end_str = f"{end_date}T23:59:59Z"

            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: {start_str}, stop: {end_str})
              |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
              |> filter(fn: (r) => r["site_id"] == "{site_id}")
              |> filter(fn: (r) => r["_field"] == "net_weight_kg")
              |> aggregateWindow(every: 1mo, fn: sum, createEmpty: false)
            '''

            tables = self.query_api.query(query, org=self.org)
            seasonal_data = []

            for table in tables:
                for record in table.records:
                    time = record.get_time()
                    seasonal_data.append({
                        "year": time.year,
                        "month": time.month,
                        "operations": 1,
                        "total_weight": float(record.get_value()) if record.get_value() else 0
                    })

            return sorted(seasonal_data, key=lambda x: (x["year"], x["month"]))

        except Exception as e:
            logger.error(f"Error querying seasonal data: {e}")
            return []

    def health_check(self) -> bool:
        """
        Check InfluxDB health by pinging the client
        
        Returns:
            True if InfluxDB is healthy, False otherwise
        """
        try:
            # Try to ping the InfluxDB service
            health = self.client.ping()
            return health is True
        except Exception as e:
            logger.error(f"InfluxDB health check failed: {e}")
            return False

    def close(self):
        """Close InfluxDB client"""
        self.client.close()


# Global instance
influxdb_service = InfluxDBService()
