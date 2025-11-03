"""
InfluxDB Service for Time-Series Data

Handles all time-series operational data in InfluxDB for:
- High performance queries
- Automatic compression (10-100x vs PostgreSQL)
- Fast aggregations
- Low disk usage
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class InfluxDBService:
    """
    Service for InfluxDB time-series operations.
    """

    def __init__(self):
        self.client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        self.bucket = settings.INFLUXDB_BUCKET

    # ==================== WRITE OPERATIONS ====================

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
                .time(operation_date, WritePrecision.S)

            # Add all numeric fields
            if operation_data.get("net_weight_kg"):
                point.field("net_weight_kg", float(operation_data["net_weight_kg"]))

            if operation_data.get("gross_weight_kg"):
                point.field("gross_weight_kg", float(operation_data["gross_weight_kg"]))

            if operation_data.get("tare_weight_kg"):
                point.field("tare_weight_kg", float(operation_data["tare_weight_kg"]))

            if operation_data.get("loading_time_minutes"):
                point.field("loading_time_minutes", float(operation_data["loading_time_minutes"]))

            if operation_data.get("waiting_time_minutes"):
                point.field("waiting_time_minutes", float(operation_data["waiting_time_minutes"]))

            if operation_data.get("total_time_minutes"):
                point.field("total_time_minutes", float(operation_data["total_time_minutes"]))

            if operation_data.get("moisture_percent"):
                point.field("moisture_percent", float(operation_data["moisture_percent"]))

            if operation_data.get("impurity_percent"):
                point.field("impurity_percent", float(operation_data["impurity_percent"]))

            if operation_data.get("total_value"):
                point.field("total_value", float(operation_data["total_value"]))

            if operation_data.get("freight_value"):
                point.field("freight_value", float(operation_data["freight_value"]))

            # Write to InfluxDB
            self.write_api.write(bucket=self.bucket, record=point)
            return True

        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {str(e)}")
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
                    .time(operation_date, WritePrecision.S)

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
                logger.error(f"Error creating point: {str(e)}")
                failed += 1

        # Batch write
        if points:
            try:
                self.write_api.write(bucket=self.bucket, record=points)
            except Exception as e:
                logger.error(f"Error batch writing to InfluxDB: {str(e)}")
                failed += len(points)
                success = 0

        return {"success": success, "failed": failed}

    # ==================== QUERY OPERATIONS ====================

    def query_monthly_aggregates(
        self,
        site_id: int,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Query comprehensive monthly aggregates from InfluxDB.

        Returns aggregated data grouped by month with counts, sums, and averages.
        """
        # Query for counts (operations per month)
        count_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start_date.isoformat()}T00:00:00Z, stop: {end_date.isoformat()}T23:59:59Z)
          |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
          |> filter(fn: (r) => r["site_id"] == "{site_id}")
          |> filter(fn: (r) => r["_field"] == "net_weight_kg")
          |> aggregateWindow(every: 1mo, fn: count, createEmpty: false)
        '''

        # Query for sum of weights and revenues
        sum_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start_date.isoformat()}T00:00:00Z, stop: {end_date.isoformat()}T23:59:59Z)
          |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
          |> filter(fn: (r) => r["site_id"] == "{site_id}")
          |> filter(fn: (r) => r["_field"] == "net_weight_kg" or r["_field"] == "total_value")
          |> aggregateWindow(every: 1mo, fn: sum, createEmpty: false)
        '''

        # Query for average times
        avg_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start_date.isoformat()}T00:00:00Z, stop: {end_date.isoformat()}T23:59:59Z)
          |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
          |> filter(fn: (r) => r["site_id"] == "{site_id}")
          |> filter(fn: (r) => r["_field"] == "loading_time_minutes" or r["_field"] == "waiting_time_minutes")
          |> aggregateWindow(every: 1mo, fn: mean, createEmpty: false)
        '''

        try:
            # Execute all queries
            count_tables = self.query_api.query(count_query)
            sum_tables = self.query_api.query(sum_query)
            avg_tables = self.query_api.query(avg_query)

            # Process results
            monthly_data = {}

            # Process counts
            for table in count_tables:
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
                    monthly_data[month_key]["operations"] = int(record.get_value()) if record.get_value() else 0

            # Process sums
            for table in sum_tables:
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
                    if field == "net_weight_kg":
                        monthly_data[month_key]["total_weight"] = float(record.get_value()) if record.get_value() else 0
                    elif field == "total_value":
                        monthly_data[month_key]["total_revenue"] = float(record.get_value()) if record.get_value() else 0

            # Process averages
            for table in avg_tables:
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
                    if field == "loading_time_minutes":
                        monthly_data[month_key]["avg_loading_time"] = float(record.get_value()) if record.get_value() else 0
                    elif field == "waiting_time_minutes":
                        monthly_data[month_key]["avg_waiting_time"] = float(record.get_value()) if record.get_value() else 0

            # Convert to sorted list
            return sorted(monthly_data.values(), key=lambda x: x["month"])

        except Exception as e:
            logger.error(f"Error querying InfluxDB monthly aggregates: {str(e)}")
            return []

    def query_daily_stats(
        self,
        site_id: int,
        start_date: date,
        end_date: date,
        metric: str = "net_weight_kg"
    ) -> List[Dict[str, Any]]:
        """
        Query daily statistics for a specific metric.

        Args:
            site_id: Site ID
            start_date: Start date
            end_date: End date
            metric: Field to query (net_weight_kg, loading_time_minutes, etc.)

        Returns:
            List of daily data points with operations count and value
        """
        # Determine aggregation function based on metric
        if metric in ["loading_time_minutes", "waiting_time_minutes"]:
            agg_fn = "mean"
        else:
            agg_fn = "sum"

        # Query for counts (operations per day)
        count_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start_date.isoformat()}T00:00:00Z, stop: {end_date.isoformat()}T23:59:59Z)
          |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
          |> filter(fn: (r) => r["site_id"] == "{site_id}")
          |> filter(fn: (r) => r["_field"] == "net_weight_kg")
          |> aggregateWindow(every: 1d, fn: count, createEmpty: false)
        '''

        # Query for metric values
        value_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start_date.isoformat()}T00:00:00Z, stop: {end_date.isoformat()}T23:59:59Z)
          |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
          |> filter(fn: (r) => r["site_id"] == "{site_id}")
          |> filter(fn: (r) => r["_field"] == "{metric}")
          |> aggregateWindow(every: 1d, fn: {agg_fn}, createEmpty: false)
        '''

        try:
            count_tables = self.query_api.query(count_query)
            value_tables = self.query_api.query(value_query)

            daily_data = {}

            # Process counts
            for table in count_tables:
                for record in table.records:
                    date_key = record.get_time().date().isoformat()
                    if date_key not in daily_data:
                        daily_data[date_key] = {
                            "date": date_key,
                            "operations": 0,
                            "value": 0
                        }
                    daily_data[date_key]["operations"] = int(record.get_value()) if record.get_value() else 0

            # Process values
            for table in value_tables:
                for record in table.records:
                    date_key = record.get_time().date().isoformat()
                    if date_key not in daily_data:
                        daily_data[date_key] = {
                            "date": date_key,
                            "operations": 0,
                            "value": 0
                        }
                    daily_data[date_key]["value"] = float(record.get_value()) if record.get_value() else 0

            # Convert to sorted list
            return sorted(daily_data.values(), key=lambda x: x["date"])

        except Exception as e:
            logger.error(f"Error querying daily stats: {str(e)}")
            return []

    def query_operation_counts(
        self,
        site_id: int,
        start_date: date,
        end_date: date,
        group_by: str = "1mo"  # 1d, 1w, 1mo
    ) -> List[Dict[str, Any]]:
        """
        Query operation counts grouped by time period.

        Args:
            site_id: Site ID
            start_date: Start date
            end_date: End date
            group_by: Aggregation window (1d, 1w, 1mo)

        Returns:
            List of aggregated counts
        """
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start_date.isoformat()}T00:00:00Z, stop: {end_date.isoformat()}T23:59:59Z)
          |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
          |> filter(fn: (r) => r["site_id"] == "{site_id}")
          |> filter(fn: (r) => r["_field"] == "net_weight_kg")
          |> aggregateWindow(every: {group_by}, fn: count, createEmpty: false)
        '''

        try:
            tables = self.query_api.query(query)
            results = []

            for table in tables:
                for record in table.records:
                    results.append({
                        "time": record.get_time().isoformat(),
                        "count": int(record.get_value()) if record.get_value() else 0
                    })

            return results

        except Exception as e:
            logger.error(f"Error querying operation counts: {str(e)}")
            return []

    def query_aggregated_metrics(
        self,
        site_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Query aggregated metrics for a period.

        Returns total operations, tonnage, revenue, and average times.
        """
        # Query for count
        count_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start_date.isoformat()}T00:00:00Z, stop: {end_date.isoformat()}T23:59:59Z)
          |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
          |> filter(fn: (r) => r["site_id"] == "{site_id}")
          |> filter(fn: (r) => r["_field"] == "net_weight_kg")
          |> count()
        '''

        # Query for sums (weight and revenue)
        sum_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start_date.isoformat()}T00:00:00Z, stop: {end_date.isoformat()}T23:59:59Z)
          |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
          |> filter(fn: (r) => r["site_id"] == "{site_id}")
          |> filter(fn: (r) => r["_field"] == "net_weight_kg" or r["_field"] == "total_value")
          |> group(columns: ["_field"])
          |> sum()
        '''

        # Query for averages (times)
        avg_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start_date.isoformat()}T00:00:00Z, stop: {end_date.isoformat()}T23:59:59Z)
          |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
          |> filter(fn: (r) => r["site_id"] == "{site_id}")
          |> filter(fn: (r) => r["_field"] == "loading_time_minutes" or r["_field"] == "waiting_time_minutes")
          |> group(columns: ["_field"])
          |> mean()
        '''

        try:
            # Execute queries
            count_tables = self.query_api.query(count_query)
            sum_tables = self.query_api.query(sum_query)
            avg_tables = self.query_api.query(avg_query)

            operations = 0
            for table in count_tables:
                for record in table.records:
                    operations = int(record.get_value()) if record.get_value() else 0

            sums = {}
            for table in sum_tables:
                for record in table.records:
                    field = record.get_field()
                    value = float(record.get_value()) if record.get_value() else 0
                    sums[field] = value

            avgs = {}
            for table in avg_tables:
                for record in table.records:
                    field = record.get_field()
                    value = float(record.get_value()) if record.get_value() else 0
                    avgs[field] = value

            return {
                "operations": operations,
                "tonnage": sums.get("net_weight_kg", 0) / 1000,  # Convert to tons
                "revenue": sums.get("total_value", 0),
                "avg_loading_time": avgs.get("loading_time_minutes", 0),
                "avg_waiting_time": avgs.get("waiting_time_minutes", 0)
            }

        except Exception as e:
            logger.error(f"Error querying aggregated metrics: {str(e)}")
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
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Query data grouped by year and month for seasonal analysis.

        Returns data with year, month, operations count, and tonnage.
        """
        # Query for operations count by month
        count_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start_date.isoformat()}T00:00:00Z, stop: {end_date.isoformat()}T23:59:59Z)
          |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
          |> filter(fn: (r) => r["site_id"] == "{site_id}")
          |> filter(fn: (r) => r["_field"] == "net_weight_kg")
          |> aggregateWindow(every: 1mo, fn: count, createEmpty: false)
        '''

        # Query for tonnage sum by month
        tonnage_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start_date.isoformat()}T00:00:00Z, stop: {end_date.isoformat()}T23:59:59Z)
          |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
          |> filter(fn: (r) => r["site_id"] == "{site_id}")
          |> filter(fn: (r) => r["_field"] == "net_weight_kg")
          |> aggregateWindow(every: 1mo, fn: sum, createEmpty: false)
        '''

        try:
            count_tables = self.query_api.query(count_query)
            tonnage_tables = self.query_api.query(tonnage_query)

            seasonal_data = {}

            # Process counts
            for table in count_tables:
                for record in table.records:
                    time = record.get_time()
                    year = time.year
                    month = time.month
                    key = f"{year}-{month:02d}"

                    if key not in seasonal_data:
                        seasonal_data[key] = {
                            "year": year,
                            "month": month,
                            "operations": 0,
                            "total_weight": 0
                        }

                    seasonal_data[key]["operations"] = int(record.get_value()) if record.get_value() else 0

            # Process tonnage
            for table in tonnage_tables:
                for record in table.records:
                    time = record.get_time()
                    year = time.year
                    month = time.month
                    key = f"{year}-{month:02d}"

                    if key not in seasonal_data:
                        seasonal_data[key] = {
                            "year": year,
                            "month": month,
                            "operations": 0,
                            "total_weight": 0
                        }

                    seasonal_data[key]["total_weight"] = float(record.get_value()) if record.get_value() else 0

            return sorted(seasonal_data.values(), key=lambda x: (x["year"], x["month"]))

        except Exception as e:
            logger.error(f"Error querying seasonal data: {str(e)}")
            return []

    # ==================== HELPER METHODS ====================

    def _process_monthly_results(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Process raw monthly query results into structured data."""
        # Group by month
        monthly_data = {}

        for record in results:
            month_key = record["time"].strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "month": month_key,
                    "month_name": record["time"].strftime("%B %Y")
                }

            field = record["field"]
            monthly_data[month_key][field] = record["value"]

        return list(monthly_data.values())

    # ==================== RETENTION & DOWNSAMPLING ====================

    def setup_continuous_queries(self):
        """
        Setup continuous queries for automatic aggregations.

        Creates tasks to pre-aggregate data at different intervals.
        """
        # Daily aggregation task
        daily_task = f'''
        option task = {{name: "daily_gbm_aggregation", every: 1h}}

        from(bucket: "{self.bucket}")
          |> range(start: -2d)
          |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
          |> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
          |> to(bucket: "{self.bucket}_daily", org: "{settings.INFLUXDB_ORG}")
        '''

        # Monthly aggregation task
        monthly_task = f'''
        option task = {{name: "monthly_gbm_aggregation", every: 1d}}

        from(bucket: "{self.bucket}")
          |> range(start: -60d)
          |> filter(fn: (r) => r["_measurement"] == "gbm_operations")
          |> aggregateWindow(every: 1mo, fn: mean, createEmpty: false)
          |> to(bucket: "{self.bucket}_monthly", org: "{settings.INFLUXDB_ORG}")
        '''

        logger.info("Continuous queries configuration ready")
        # Note: These would be created via InfluxDB UI or API

    def close(self):
        """Close InfluxDB client connection."""
        self.client.close()


# Global instance
influxdb_service = InfluxDBService()
