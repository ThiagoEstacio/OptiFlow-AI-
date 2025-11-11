"""
Optimized InfluxDB Service with Automatic Bucket Selection
Implements downsampling strategy for 10x-100x query performance
"""

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class OptimizedInfluxDBService:
    """
    InfluxDB service with automatic bucket selection based on time range
    
    Buckets:
    - timeseries: Raw data, 2 days retention
    - downsampled_1m: 1-minute aggregations, 30 days retention
    - downsampled_1h: 1-hour aggregations, 365 days retention
    """
    
    def __init__(self):
        self.client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG,
            timeout=30_000  # 30 seconds timeout
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        
        # Bucket definitions
        self.buckets = {
            "raw": "timeseries",            # 2 days retention, 1-second resolution
            "1m": "downsampled_1m",         # 30 days retention, 1-minute resolution
            "1h": "downsampled_1h",         # 365 days retention, 1-hour resolution
        }
        
        logger.info("✅ OptimizedInfluxDBService initialized with downsampling")
    
    def _select_optimal_bucket(
        self, 
        time_range: timedelta,
        force_bucket: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Auto-select best bucket based on time range
        
        Strategy:
        - 0-2 days: Use raw data (best precision)
        - 2-30 days: Use 1-minute aggregations (good precision, fast)
        - 30+ days: Use 1-hour aggregations (acceptable precision, very fast)
        
        Args:
            time_range: Query time range
            force_bucket: Force specific bucket (for testing)
        
        Returns:
            Tuple of (bucket_name, resolution)
        """
        if force_bucket:
            return self.buckets.get(force_bucket, self.buckets["raw"]), force_bucket
        
        if time_range <= timedelta(days=2):
            bucket = self.buckets["raw"]
            resolution = "raw"
            logger.debug(f"Selected RAW bucket (time_range: {time_range})")
        elif time_range <= timedelta(days=30):
            bucket = self.buckets["1m"]
            resolution = "1m"
            logger.debug(f"Selected 1M bucket (time_range: {time_range})")
        else:
            bucket = self.buckets["1h"]
            resolution = "1h"
            logger.debug(f"Selected 1H bucket (time_range: {time_range})")
        
        return bucket, resolution
    
    async def query_tag_data(
        self,
        tag_id: int,
        start: datetime,
        end: datetime,
        measurement: str = "sensor_data",
        force_bucket: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query tag data with automatic bucket selection
        
        Args:
            tag_id: Tag identifier
            start: Start time
            end: End time
            measurement: Measurement name
            force_bucket: Force specific bucket (optional)
        
        Returns:
            List of data points
        """
        time_range = end - start
        bucket, resolution = self._select_optimal_bucket(time_range, force_bucket)
        
        query = f'''
            from(bucket: "{bucket}")
              |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
              |> filter(fn: (r) => r._measurement == "{measurement}")
              |> filter(fn: (r) => r.tag_id == "{tag_id}")
              |> filter(fn: (r) => r._field == "value")
              |> sort(columns: ["_time"])
        '''
        
        logger.info(
            f"🔍 Querying tag_id={tag_id} from '{bucket}' "
            f"(resolution: {resolution}, range: {time_range})"
        )
        
        try:
            tables = self.query_api.query(query, org=settings.INFLUXDB_ORG)
            
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "time": record.get_time(),
                        "value": record.get_value(),
                        "tag_id": record.values.get("tag_id"),
                        "resolution": resolution
                    })
            
            logger.info(f"✅ Retrieved {len(results)} points (resolution: {resolution})")
            return results
            
        except Exception as e:
            logger.error(f"❌ Query error: {e}")
            raise
    
    async def query_multiple_tags(
        self,
        tag_ids: List[int],
        start: datetime,
        end: datetime,
        measurement: str = "sensor_data"
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Query multiple tags efficiently
        
        Args:
            tag_ids: List of tag identifiers
            start: Start time
            end: End time
            measurement: Measurement name
        
        Returns:
            Dictionary mapping tag_id to data points
        """
        time_range = end - start
        bucket, resolution = self._select_optimal_bucket(time_range)
        
        # Build filter for multiple tags
        tag_filter = " or ".join([f'r.tag_id == "{tid}"' for tid in tag_ids])
        
        query = f'''
            from(bucket: "{bucket}")
              |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
              |> filter(fn: (r) => r._measurement == "{measurement}")
              |> filter(fn: (r) => {tag_filter})
              |> filter(fn: (r) => r._field == "value")
              |> sort(columns: ["_time"])
        '''
        
        logger.info(
            f"🔍 Querying {len(tag_ids)} tags from '{bucket}' "
            f"(resolution: {resolution}, range: {time_range})"
        )
        
        try:
            tables = self.query_api.query(query, org=settings.INFLUXDB_ORG)
            
            results: Dict[int, List[Dict[str, Any]]] = {tid: [] for tid in tag_ids}
            total_points = 0
            
            for table in tables:
                for record in table.records:
                    tag_id = int(record.values.get("tag_id"))
                    results[tag_id].append({
                        "time": record.get_time(),
                        "value": record.get_value(),
                        "resolution": resolution
                    })
                    total_points += 1
            
            logger.info(
                f"✅ Retrieved {total_points} total points across {len(tag_ids)} tags "
                f"(resolution: {resolution})"
            )
            return results
            
        except Exception as e:
            logger.error(f"❌ Query error: {e}")
            raise
    
    async def query_aggregated(
        self,
        tag_id: int,
        start: datetime,
        end: datetime,
        window: str = "5m",
        aggregation: str = "mean"
    ) -> List[Dict[str, Any]]:
        """
        Query with custom aggregation window
        
        Args:
            tag_id: Tag identifier
            start: Start time
            end: End time
            window: Aggregation window (e.g., "5m", "1h", "1d")
            aggregation: Aggregation function (mean, min, max, sum, count)
        
        Returns:
            Aggregated data points
        """
        time_range = end - start
        bucket, resolution = self._select_optimal_bucket(time_range)
        
        query = f'''
            from(bucket: "{bucket}")
              |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
              |> filter(fn: (r) => r._measurement == "sensor_data")
              |> filter(fn: (r) => r.tag_id == "{tag_id}")
              |> filter(fn: (r) => r._field == "value")
              |> aggregateWindow(every: {window}, fn: {aggregation}, createEmpty: false)
              |> sort(columns: ["_time"])
        '''
        
        logger.info(
            f"🔍 Querying aggregated (window={window}, fn={aggregation}) "
            f"from '{bucket}' (resolution: {resolution})"
        )
        
        try:
            tables = self.query_api.query(query, org=settings.INFLUXDB_ORG)
            
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "time": record.get_time(),
                        "value": record.get_value(),
                        "window": window,
                        "aggregation": aggregation,
                        "source_resolution": resolution
                    })
            
            logger.info(
                f"✅ Retrieved {len(results)} aggregated points "
                f"(window={window}, source={resolution})"
            )
            return results
            
        except Exception as e:
            logger.error(f"❌ Aggregation query error: {e}")
            raise
    
    async def get_statistics(
        self,
        tag_id: int,
        start: datetime,
        end: datetime
    ) -> Dict[str, float]:
        """
        Get statistical summary for a tag
        
        Args:
            tag_id: Tag identifier
            start: Start time
            end: End time
        
        Returns:
            Dictionary with min, max, mean, stddev, count
        """
        time_range = end - start
        bucket, resolution = self._select_optimal_bucket(time_range)
        
        query = f'''
            from(bucket: "{bucket}")
              |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
              |> filter(fn: (r) => r._measurement == "sensor_data")
              |> filter(fn: (r) => r.tag_id == "{tag_id}")
              |> filter(fn: (r) => r._field == "value")
        '''
        
        try:
            # Execute multiple aggregations
            stats = {}
            
            for stat_func in ["min", "max", "mean", "stddev", "count"]:
                stat_query = query + f'|> {stat_func}()'
                tables = self.query_api.query(stat_query, org=settings.INFLUXDB_ORG)
                
                for table in tables:
                    for record in table.records:
                        stats[stat_func] = record.get_value()
            
            logger.info(f"✅ Retrieved statistics for tag_id={tag_id}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Statistics query error: {e}")
            raise
    
    def write_data(
        self,
        measurement: str,
        tag_id: int,
        value: float,
        timestamp: Optional[datetime] = None,
        additional_tags: Optional[Dict[str, str]] = None,
        additional_fields: Optional[Dict[str, Any]] = None
    ):
        """
        Write data point to InfluxDB (always to raw bucket)
        
        Args:
            measurement: Measurement name
            tag_id: Tag identifier
            value: Value to write
            timestamp: Timestamp (default: now)
            additional_tags: Additional tags
            additional_fields: Additional fields
        """
        point = {
            "measurement": measurement,
            "tags": {"tag_id": str(tag_id)},
            "fields": {"value": value},
            "time": timestamp or datetime.utcnow()
        }
        
        if additional_tags:
            point["tags"].update(additional_tags)
        
        if additional_fields:
            point["fields"].update(additional_fields)
        
        try:
            self.write_api.write(
                bucket=self.buckets["raw"],  # Always write to raw bucket
                org=settings.INFLUXDB_ORG,
                record=point
            )
            logger.debug(f"✅ Wrote data point for tag_id={tag_id}")
        except Exception as e:
            logger.error(f"❌ Write error: {e}")
            raise
    
    def get_latest_value(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """
        Get latest value for a tag by ID or name.
        Queries raw bucket for most recent data.
        
        Args:
            tag_id: Tag ID or name
            
        Returns:
            Dictionary with value, timestamp, quality or None
        """
        try:
            query = f'''
            from(bucket: "{self.buckets["raw"]}")
                |> range(start: -2d)
                |> filter(fn: (r) => r["_measurement"] == "tag_data")
                |> filter(fn: (r) => r["tag_id"] == "{tag_id}" or r["tag_name"] == "{tag_id}")
                |> last()
            '''
            
            result = self.query_api.query(query, org=settings.INFLUXDB_ORG)
            
            if not result or not result[0].records:
                logger.debug(f"No data found for tag: {tag_id}")
                return None
            
            record = result[0].records[0]
            return {
                "value": record.get_value(),
                "timestamp": record.get_time(),
                "quality": record.values.get("quality", "GOOD"),
                "tag_id": record.values.get("tag_id"),
                "tag_name": record.values.get("tag_name")
            }
            
        except Exception as e:
            logger.error(f"Error getting latest value for {tag_id}: {e}")
            return None
    
    def get_latest_value_by_name(self, tag_name: str) -> Optional[Dict[str, Any]]:
        """
        Get latest value for a tag by name.
        Alias for get_latest_value to maintain API compatibility.
        
        Args:
            tag_name: Tag name
            
        Returns:
            Dictionary with value, timestamp, quality or None
        """
        return self.get_latest_value(tag_name)
    
    def get_latest_values_by_names(self, tag_names: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get latest values for multiple tags by name.
        
        Args:
            tag_names: List of tag names
            
        Returns:
            Dictionary mapping tag names to their latest values
        """
        results = {}
        
        # Query each tag individually (more reliable than complex grouping)
        for tag_name in tag_names:
            try:
                results[tag_name] = self.get_latest_value_by_name(tag_name)
            except Exception as e:
                logger.error(f"Error getting value for {tag_name}: {e}")
                results[tag_name] = None
        
        return results
    
    async def get_bucket_info(self) -> Dict[str, Any]:
        """Get information about configured buckets"""
        return {
            "buckets": self.buckets,
            "strategy": {
                "0-2_days": "raw (best precision)",
                "2-30_days": "1m aggregations (good precision, 60x faster)",
                "30+_days": "1h aggregations (acceptable precision, 3600x faster)"
            },
            "status": "active"
        }
    
    def close(self):
        """Close InfluxDB client"""
        self.client.close()
        logger.info("✅ InfluxDB client closed")


# Singleton instance
optimized_influxdb_service = OptimizedInfluxDBService()
