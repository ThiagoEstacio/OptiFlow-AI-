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

    ESTRATÉGIA DE RETENÇÃO PERMANENTE:
    ====================================
    - timeseries: Raw data, 7 days retention, full resolution
    - downsampled_1m: 1-minute aggregations, 90 days retention
    - downsampled_1h: 1-hour aggregations, 2 years retention
    - downsampled_1d: 1-day aggregations, INFINITE retention (permanent storage)

    Uso de espaço estimado (10 tags @ 1s):
    - Raw (7d):      ~6M points  = ~150 MB
    - 1min (90d):    ~1.3M points = ~30 MB
    - 1hour (2y):    ~175k points = ~5 MB
    - 1day (∞):      ~3.6k/year  = ~1 MB/year

    Total para 10 anos: ~195 MB (excelente compressão!)
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

        # Bucket definitions - Multi-tier retention strategy
        self.buckets = {
            "raw": "timeseries",            # 7 days, full resolution (queries recentes)
            "1m": "downsampled_1m",         # 90 days, 1-min aggregations (queries médio prazo)
            "1h": "downsampled_1h",         # 2 years, 1-hour aggregations (queries longo prazo)
            "1d": "downsampled_1d",         # INFINITE, 1-day aggregations (storage permanente)
        }

        logger.info("✅ OptimizedInfluxDBService initialized with permanent retention strategy")
    
    def _select_optimal_bucket(
        self,
        time_range: timedelta,
        force_bucket: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Auto-select best bucket based on time range

        NOVA ESTRATÉGIA - 4 CAMADAS:
        =============================
        - 0-7 days:    RAW data (resolução completa, ultra-rápido)
        - 7-90 days:   1-minute aggregations (boa precisão, rápido)
        - 90-730 days: 1-hour aggregations (precisão aceitável, muito rápido)
        - 730+ days:   1-day aggregations (trends/reports, extremamente rápido)

        Benefícios:
        - Queries de 10 anos: ~3600 pontos (1 dia cada) = instantâneo!
        - Queries de 1 ano: ~8760 pontos (1 hora cada) = muito rápido
        - Queries de 1 mês: ~43k pontos (1 min cada) = rápido
        - Queries de 1 dia: ~86k pontos (raw) = ultra-rápido

        Args:
            time_range: Query time range
            force_bucket: Force specific bucket (for testing)

        Returns:
            Tuple of (bucket_name, resolution)
        """
        if force_bucket:
            return self.buckets.get(force_bucket, self.buckets["raw"]), force_bucket

        if time_range <= timedelta(days=7):
            bucket = self.buckets["raw"]
            resolution = "raw (1s)"
            logger.debug(f"✅ Selected RAW bucket for {time_range} - full resolution")
        elif time_range <= timedelta(days=90):
            bucket = self.buckets["1m"]
            resolution = "1min"
            logger.debug(f"✅ Selected 1MIN bucket for {time_range} - 60x compression")
        elif time_range <= timedelta(days=730):  # 2 years
            bucket = self.buckets["1h"]
            resolution = "1hour"
            logger.debug(f"✅ Selected 1HOUR bucket for {time_range} - 3600x compression")
        else:
            bucket = self.buckets["1d"]
            resolution = "1day"
            logger.debug(f"✅ Selected 1DAY bucket for {time_range} - 86400x compression")
        
        return bucket, resolution
    
    async def query_tag_data(
        self,
        tag_id: str,
        start: datetime,
        end: datetime,
        measurement: str = "tag_data",
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

        # Format timestamps properly for InfluxDB (RFC3339 without duplicate timezone)
        start_str = start.replace(tzinfo=None).isoformat() + "Z" if start.tzinfo else start.isoformat() + "Z"
        end_str = end.replace(tzinfo=None).isoformat() + "Z" if end.tzinfo else end.isoformat() + "Z"

        query = f'''
            from(bucket: "{bucket}")
              |> range(start: {start_str}, stop: {end_str})
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

    def write_batch(self, points: List[Dict[str, Any]]) -> bool:
        """
        Write batch of data points to InfluxDB

        Args:
            points: List of data points in format:
                [
                    {
                        "tag_id": "uuid",
                        "value": 42.5,
                        "timestamp": "2024-01-01T00:00:00Z",
                        "quality": "good"
                    }
                ]

        Returns:
            True if successful, False otherwise
        """
        if not points:
            logger.warning("Empty batch provided")
            return False

        try:
            batch_points = []

            for point_data in points:
                tag_id = point_data.get("tag_id")
                value = point_data.get("value")
                timestamp_str = point_data.get("timestamp")
                quality = point_data.get("quality", "good")

                if not tag_id or value is None:
                    logger.warning(f"Skipping invalid point: {point_data}")
                    continue

                # Parse timestamp
                if isinstance(timestamp_str, str):
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                elif isinstance(timestamp_str, datetime):
                    timestamp = timestamp_str
                else:
                    timestamp = datetime.utcnow()

                # Create InfluxDB point
                # Handle both numeric and string values
                try:
                    # Try to convert to float for numeric values
                    numeric_value = float(value)
                    field_value = {"value": numeric_value}
                except (ValueError, TypeError):
                    # If conversion fails, store as string in a separate field
                    field_value = {"value_str": str(value)}
                
                influx_point = {
                    "measurement": "tag_data",
                    "tags": {
                        "tag_id": str(tag_id),
                        "quality": quality
                    },
                    "fields": field_value,
                    "time": timestamp
                }

                batch_points.append(influx_point)

            if not batch_points:
                logger.warning("No valid points to write")
                return False

            # Write batch to InfluxDB
            self.write_api.write(
                bucket=self.buckets["raw"],
                org=settings.INFLUXDB_ORG,
                record=batch_points
            )

            # Force flush to ensure data is written
            try:
                self.write_api.flush()
            except Exception as flush_error:
                logger.warning(f"Flush warning (may be expected for SYNCHRONOUS mode): {flush_error}")

            logger.info(f"✅ Wrote batch of {len(batch_points)} points to InfluxDB")
            return True

        except Exception as e:
            logger.error(f"❌ Batch write error: {e}")
            return False

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
    
    def get_active_tags(self, lookback_hours: int = 1) -> List[Dict[str, Any]]:
        """
        Get list of all active tags with data in the specified lookback period.
        
        Args:
            lookback_hours: Hours to look back for active tags (default: 1)
            
        Returns:
            List of dictionaries with tag information including last value
        """
        try:
            # Use the primary bucket (timeseries/optiflow)
            bucket = settings.INFLUXDB_BUCKET
            
            query = f'''
                from(bucket: "{bucket}")
                    |> range(start: -{lookback_hours}h)
                    |> filter(fn: (r) => r._measurement == "tag_data")
                    |> group(columns: ["tag_id"])
                    |> last()
                    |> yield(name: "last")
            '''
            
            tables = self.query_api.query(query, org=settings.INFLUXDB_ORG)
            
            tags = []
            seen_tags = set()
            
            for table in tables:
                for record in table.records:
                    tag_id = record.values.get("tag_id") or record.values.get("tag_name")
                    
                    if not tag_id:
                        continue
                        
                    # Skip duplicates
                    if tag_id in seen_tags:
                        continue
                    seen_tags.add(tag_id)
                    
                    tags.append({
                        "id": tag_id,
                        "name": tag_id,
                        "address": tag_id,
                        "data_type": "FLOAT",
                        "last_value": record.get_value(),
                        "last_quality": record.values.get("quality", "Good"),
                        "last_timestamp": record.get_time().isoformat() if record.get_time() else None,
                        "enabled": True,
                        "source": "influxdb",
                        "unit": record.values.get("unit", ""),
                        "description": f"Active tag from InfluxDB (last {lookback_hours}h)",
                        "device_id": record.values.get("device_id", "unknown")
                    })
            
            logger.info(f"✅ Found {len(tags)} active tags in last {lookback_hours}h from bucket '{bucket}'")
            return tags
            
        except Exception as e:
            logger.error(f"❌ Error getting active tags: {e}", exc_info=True)
            return []
    
    def close(self):
        """Close InfluxDB client"""
        self.client.close()
        logger.info("✅ InfluxDB client closed")


# Singleton instance
optimized_influxdb_service = OptimizedInfluxDBService()
