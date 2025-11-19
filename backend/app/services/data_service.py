"""
Data Services - Real-time and Historical Data Access

Provides services to query:
- Real-time tag values (PostgreSQL/Redis)
- Historical time-series data (InfluxDB)
- Calculated aggregations (avg, max, min, stddev, sum)
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
import asyncio
import logging
from influxdb_client import InfluxDBClient
from app.core.config import settings
from app.services.influxdb import influxdb_service

logger = logging.getLogger(__name__)

# PROTECTION: Rate limiting for InfluxDB queries (prevent loops)
_influx_query_semaphore = asyncio.Semaphore(10)  # Max 10 concurrent queries
_influx_query_timeout = 30  # 30 seconds timeout per query


class DataService:
    """Service for accessing real-time and historical data"""
    
    def __init__(self, db: AsyncSession):
        """Initialize with async session and InfluxDB client"""
        self.db = db
        
        # Initialize InfluxDB client
        try:
            self.influx_client = InfluxDBClient(
                url=settings.INFLUXDB_URL,
                token=settings.INFLUXDB_TOKEN,
                org=settings.INFLUXDB_ORG,
                timeout=10000
            )
            self.query_api = self.influx_client.query_api()
            logger.info("✅ InfluxDB client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize InfluxDB client: {e}")
            self.influx_client = None
            self.query_api = None
        
    async def get_realtime_value(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current REAL-TIME value using influxdb_service

        QUALITY FILTERING: Returns None for non-"good" quality data to prevent
        analytics from processing communication failures as real values.

        Args:
            tag_id: Tag identifier (name, id, or address)

        Returns:
            Dict with metadata + realtime value, or None if not found OR bad quality
        """
        try:
            logger.info(f"📋 Getting realtime value for {tag_id}")

            # Use the influxdb_service that's working for /api/v1/tags/realtime/{tag_name}
            result = await asyncio.to_thread(influxdb_service.get_latest_value_by_name, tag_id)

            if result is None:
                logger.warning(f"⚠️ No realtime data found for tag: {tag_id}")
                return None

            # QUALITY FILTER: Only return data with "good" quality
            # This prevents communication failures (quality="bad") from being treated as real values
            quality = result.get("quality", "GOOD").lower()
            if quality != "good":
                logger.warning(
                    f"⚠️ Ignoring {tag_id} due to bad quality: {quality} "
                    f"(value={result.get('value')} would be discarded)"
                )
                return None

            logger.info(f"✅ Got realtime value: {result.get('value')} for {tag_id} (quality: {quality})")

            return {
                "tag_id": result.get("tag_id", tag_id),
                "name": result.get("tag_name", tag_id),
                "unit": result.get("unit"),
                "data_type": "float",
                "description": None,
                "value": result.get("value"),
                "timestamp": result.get("timestamp"),
                "quality": quality.upper(),
                "min_value": None,
                "max_value": None
            }

        except Exception as e:
            logger.error(f"❌ Error getting realtime value for {tag_id}: {e}")
            return None
    
    async def get_multiple_realtime_values(self, tag_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get current values for multiple tags
        
        Args:
            tag_ids: List of tag identifiers
            
        Returns:
            List of tag data dictionaries
        """
        results = []
        for tag_id in tag_ids:
            data = await self.get_realtime_value(tag_id)
            if data:
                results.append(data)
        return results
    
    async def get_historical_data(
        self, 
        tag_id: str, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        duration: str = "1h",
        aggregation: Optional[str] = None,
        interval: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get historical data from InfluxDB (REAL DATA)
        
        Args:
            tag_id: Tag identifier (e.g., "ELEV01_TEMP_C_PV")
            start_time: Start of time range
            end_time: End of time range
            duration: Duration string (e.g., "1h", "24h", "7d") if start_time not provided
            aggregation: Aggregation function (mean, max, min, stddev, sum)
            interval: Aggregation interval (e.g., "1m", "5m", "1h")
            
        Returns:
            Dict with data points and metadata from InfluxDB
        """
        # PROTECTION: Acquire semaphore to limit concurrent queries
        async with _influx_query_semaphore:
            try:
                # PROTECTION: Wrap in timeout to prevent hanging
                return await asyncio.wait_for(
                    self._get_historical_data_impl(tag_id, start_time, end_time, duration, aggregation, interval),
                    timeout=_influx_query_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"⏱️ InfluxDB query timeout for tag {tag_id}")
                return {
                    "tag_id": tag_id,
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None,
                    "data_points": [],
                    "count": 0,
                    "error": "Query timeout"
                }
            except Exception as e:
                logger.error(f"❌ Error in get_historical_data: {e}")
                return {
                    "tag_id": tag_id,
                    "data_points": [],
                    "count": 0,
                    "error": str(e)
                }
    
    async def _get_historical_data_impl(
        self, 
        tag_id: str, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        duration: str = "1h",
        aggregation: Optional[str] = None,
        interval: Optional[str] = None
    ) -> Dict[str, Any]:
        """Internal implementation of get_historical_data (with protections above)"""
        try:
            # Parse duration to get start_time if not provided
            if not start_time or (isinstance(start_time, str) and start_time in ["1h", "6h", "12h", "24h", "7d", "30d"]):
                # start_time is either None or a duration string
                end_time = end_time or datetime.now()
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    
                duration_map = {
                    "1h": timedelta(hours=1),
                    "6h": timedelta(hours=6),
                    "12h": timedelta(hours=12),
                    "24h": timedelta(days=1),
                    "7d": timedelta(days=7),
                    "30d": timedelta(days=30)
                }
                # Get duration from start_time if it's a duration string, else use parameter
                duration_str = start_time if isinstance(start_time, str) else duration
                delta = duration_map.get(duration_str, timedelta(hours=1))
                start_time = end_time - delta
            else:
                # start_time is a datetime or ISO string
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            
            if not end_time:
                end_time = datetime.now()
            elif isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # Check if InfluxDB client is available
            if not self.query_api:
                logger.warning("⚠️ InfluxDB not available, returning empty data")
                return {
                    "tag_id": tag_id,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "data_points": [],
                    "count": 0,
                    "error": "InfluxDB not available"
                }
            
            # Build Flux query to get data from InfluxDB
            # Data is stored as: measurement="tag_data", tag="tag_id", field="value"
            # QUALITY FILTERING: Only include "good" quality data to prevent false positives
            flux_query = f'''
from(bucket: "{settings.INFLUXDB_BUCKET}")
  |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
  |> filter(fn: (r) => r["_measurement"] == "tag_data")
  |> filter(fn: (r) => r["tag_id"] == "{tag_id}")
  |> filter(fn: (r) => r["_field"] == "value")
  |> filter(fn: (r) => r["quality"] == "good")
  |> sort(columns: ["_time"])
            '''
            
            if aggregation and interval:
                # Apply aggregation if requested (e.g., mean over 5m windows)
                flux_query += f'''
  |> aggregateWindow(every: {interval}, fn: {aggregation}, createEmpty: false)
                '''
            
            logger.info(f"🔍 Querying InfluxDB for {tag_id} from {start_time} to {end_time}")
            
            # Execute query
            result = self.query_api.query(query=flux_query)
            
            data_points = []
            for table in result:
                for record in table.records:
                    data_points.append({
                        "timestamp": record.get_time().isoformat(),
                        "value": float(record.get_value()),
                        "quality": record.values.get("quality", "good")
                    })
            
            logger.info(f"✅ Retrieved {len(data_points)} points for {tag_id}")
            
            return {
                "tag_id": tag_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "data_points": data_points,
                "count": len(data_points)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting historical data for {tag_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "tag_id": tag_id,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "error": str(e),
                "data_points": [],
                "count": 0
            }
    
    async def calculate_statistics(
        self, 
        tag_id: str, 
        duration: str = "1h"
    ) -> Dict[str, Any]:
        """
        Calculate statistical metrics for a tag over a time period
        
        Args:
            tag_id: Tag identifier
            duration: Duration string (e.g., "1h", "24h", "7d")
            
        Returns:
            Dict with statistical metrics (avg, max, min, stddev, count)
        """
        try:
            # Get historical data
            hist_data = await self.get_historical_data(tag_id, duration=duration)
            
            if not hist_data.get("data_points"):
                return {
                    "tag_id": tag_id,
                    "duration": duration,
                    "error": "No data available"
                }
            
            values = [p["value"] for p in hist_data["data_points"]]
            
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            stddev = variance ** 0.5
            
            return {
                "tag_id": tag_id,
                "tag_name": hist_data.get("tag_name"),
                "duration": duration,
                "count": len(values),
                "mean": round(mean, 2),
                "median": round(sorted(values)[len(values) // 2], 2),
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "stddev": round(stddev, 2),
                "range": round(max(values) - min(values), 2),
                "unit": hist_data.get("unit")
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistics for {tag_id}: {str(e)}")
            return {
                "tag_id": tag_id,
                "duration": duration,
                "error": str(e)
            }
    
    async def search_tags(
        self, 
        query: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for tags by name or description
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching tags
        """
        try:
            sql_query = text("""
                SELECT 
                    t.id,
                    t.name,
                    t.address,
                    t.description,
                    t.unit,
                    t.data_type,
                    t.min_value,
                    t.max_value
                FROM tags t
                WHERE 
                    LOWER(t.name) LIKE LOWER(:query) 
                    OR LOWER(t.description) LIKE LOWER(:query)
                    OR LOWER(t.address) LIKE LOWER(:query)
                ORDER BY 
                    CASE 
                        WHEN LOWER(t.name) = LOWER(:exact_query) THEN 1
                        WHEN LOWER(t.name) LIKE LOWER(:query) THEN 2
                        ELSE 3
                    END,
                    t.name
                LIMIT :limit
            """)
            
            search_pattern = f"%{query}%"
            result = await self.db.execute(
                sql_query,
                {
                    "query": search_pattern,
                    "exact_query": query,
                    "limit": limit
                }
            )
            rows = result.fetchall()

            tags = []
            for row in rows:
                tags.append({
                    "id": row[0],
                    "name": row[1],
                    "tag_address": row[2],
                    "description": row[3],
                    "unit": row[4],
                    "data_type": row[5],
                    "min_value": float(row[6]) if row[6] is not None else 0,
                    "max_value": float(row[7]) if row[7] is not None else 100
                })
            
            return tags
            
        except Exception as e:
            logger.error(f"Error searching tags for '{query}': {str(e)}")
            return []

    async def get_all_tags(self, limit: int = 50, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get list of all available tags in the system

        Args:
            limit: Maximum number of tags to return (max: 100)
            active_only: Return only active tags (default: True)

        Returns:
            List of tag dictionaries
        """
        # PROTECTION: Enforce maximum limit to prevent memory issues
        limit = min(limit, 100)
        
        try:
            sql_query = text("""
                SELECT
                    t.id,
                    t.name,
                    t.address,
                    t.description,
                    t.unit,
                    t.data_type,
                    t.min_value,
                    t.max_value,
                    t.current_value as last_value,
                    t.is_active
                FROM tags t
                WHERE 1=1
                    AND (:active_only = FALSE OR t.is_active = TRUE)
                ORDER BY t.name
                LIMIT :limit
            """)

            result = await self.db.execute(
                sql_query,
                {
                    "active_only": active_only,
                    "limit": limit
                }
            )
            rows = result.fetchall()

            tags = []
            for row in rows:
                tags.append({
                    "id": row[0],
                    "name": row[1],
                    "address": row[2],
                    "description": row[3],
                    "unit": row[4],
                    "data_type": row[5],
                    "min_value": float(row[6]) if row[6] is not None else 0,
                    "max_value": float(row[7]) if row[7] is not None else 100,
                    "last_value": row[8],
                    "is_active": row[9]
                })

            return tags

        except Exception as e:
            logger.error(f"Error getting all tags: {str(e)}")
            return []
