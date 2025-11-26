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
import httpx
from influxdb_client import InfluxDBClient
from app.core.config import settings
from app.services.influxdb import influxdb_service
from app.core.advanced_cache import get_advanced_cache

logger = logging.getLogger(__name__)

# Gateway Edge URL for realtime fallback
GATEWAY_EDGE_URL = settings.GATEWAY_URL if hasattr(settings, 'GATEWAY_URL') else "http://optiflow-gateway:8080"

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
        Get current REAL-TIME value with multi-source fallback:
        1. Redis Cache (L1/L2) - fastest
        2. InfluxDB - historical source
        3. Gateway Edge API - authoritative real-time source

        QUALITY FILTERING: Returns None for non-"good" quality data to prevent
        analytics from processing communication failures as real values.

        CACHING: 5-second TTL to reduce load for frequent AI Agent queries.

        Args:
            tag_id: Tag identifier (name, id, or address)

        Returns:
            Dict with metadata + realtime value, or None if not found OR bad quality
        """
        cache = get_advanced_cache()
        cache_key = f"realtime_value:{tag_id}"

        async def _fetch_from_gateway_edge(search_id: str) -> Optional[Dict[str, Any]]:
            """Fetch realtime value directly from Gateway Edge API"""
            try:
                logger.info(f"🌐 Fetching realtime value from Gateway Edge for: {search_id}")
                async with httpx.AsyncClient(timeout=5.0) as client:
                    # First try to get all tags to find the matching one
                    response = await client.get(f"{GATEWAY_EDGE_URL}/api/tags/")
                    if response.status_code == 200:
                        tags = response.json()
                        # Search for tag by name, tag_id, or partial match
                        search_lower = search_id.lower()
                        matching_tag = None
                        for tag in tags:
                            tag_name = tag.get("tag_name", "").lower()
                            tag_id_val = tag.get("tag_id", "").lower()
                            if search_lower in tag_name or search_lower in tag_id_val or tag_name in search_lower:
                                matching_tag = tag
                                break

                        if matching_tag and matching_tag.get("current_value") is not None:
                            quality = matching_tag.get("current_quality", "Good")
                            logger.info(f"✅ Gateway Edge returned: {matching_tag.get('current_value')} for {search_id}")
                            return {
                                "tag_id": matching_tag.get("tag_id", search_id),
                                "name": matching_tag.get("tag_name", search_id),
                                "unit": matching_tag.get("metadata", {}).get("engineering_units", ""),
                                "data_type": matching_tag.get("data_type", "double"),
                                "description": matching_tag.get("metadata", {}).get("description", ""),
                                "value": matching_tag.get("current_value"),
                                "timestamp": matching_tag.get("current_timestamp"),
                                "quality": quality.upper() if quality else "GOOD",
                                "min_value": matching_tag.get("scaling", {}).get("eng_min") if matching_tag.get("scaling") else None,
                                "max_value": matching_tag.get("scaling", {}).get("eng_max") if matching_tag.get("scaling") else None,
                                "source": "gateway_edge"
                            }
                logger.warning(f"⚠️ Tag {search_id} not found in Gateway Edge")
                return None
            except Exception as e:
                logger.error(f"❌ Gateway Edge fetch error for {search_id}: {e}")
                return None

        async def _fetch_from_influxdb():
            """Fetch function for cache miss - tries InfluxDB first, then Gateway Edge"""
            try:
                logger.info(f"📋 Cache MISS - Getting realtime value for {tag_id}")

                # Try InfluxDB first (historical data source)
                result = await asyncio.to_thread(influxdb_service.get_latest_value_by_name, tag_id)

                if result is not None:
                    # QUALITY FILTER: Only return data with "good" quality
                    quality = result.get("quality", "GOOD").lower()
                    if quality != "good":
                        logger.warning(
                            f"⚠️ Ignoring {tag_id} from InfluxDB due to bad quality: {quality}"
                        )
                    else:
                        logger.info(f"✅ InfluxDB returned: {result.get('value')} for {tag_id}")
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
                            "max_value": None,
                            "source": "influxdb"
                        }

                # Fallback to Gateway Edge (authoritative realtime source)
                logger.info(f"🔄 InfluxDB has no data for {tag_id}, trying Gateway Edge...")
                gateway_result = await _fetch_from_gateway_edge(tag_id)
                if gateway_result:
                    return gateway_result

                logger.warning(f"⚠️ No realtime data found for tag: {tag_id} (checked InfluxDB and Gateway Edge)")
                return None

            except Exception as e:
                logger.error(f"❌ Error getting realtime value for {tag_id}: {e}")
                # Last resort: try Gateway Edge
                return await _fetch_from_gateway_edge(tag_id)

        try:
            # Get value with caching (5-second TTL for realtime data)
            value = await cache.get(cache_key, fetch_fn=_fetch_from_influxdb, ttl=5)

            if value is not None:
                logger.debug(f"✅ Realtime value retrieved for {tag_id}")

            return value

        except Exception as e:
            logger.error(f"❌ Cache error for {tag_id}, falling back to direct fetch: {e}")
            return await _fetch_from_influxdb()
    
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
    
    async def _resolve_tag_id(self, tag_id: str) -> Tuple[str, str]:
        """
        Resolve tag name to UUID for InfluxDB queries.

        Args:
            tag_id: Tag name (e.g., "SILO01_NIVEL") or UUID

        Returns:
            Tuple of (uuid, name) - returns original tag_id if already UUID or not found
        """
        import re

        # Check if already a UUID
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
        if uuid_pattern.match(tag_id):
            return (tag_id, tag_id)

        # Look up in PostgreSQL
        try:
            result = await self.db.execute(
                text("SELECT id, name FROM tags WHERE name = :name OR name ILIKE :pattern LIMIT 1"),
                {"name": tag_id, "pattern": f"%{tag_id}%"}
            )
            row = result.fetchone()
            if row:
                logger.info(f"🔍 Resolved tag '{tag_id}' to UUID: {row[0]}")
                return (str(row[0]), row[1])
        except Exception as e:
            logger.warning(f"⚠️ Could not resolve tag name {tag_id}: {e}")

        # Return original if not found
        return (tag_id, tag_id)

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
            # Resolve tag name to UUID for InfluxDB
            resolved_tag_id, tag_name = await self._resolve_tag_id(tag_id)

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
            # Data is stored as: measurement="tag_data", tag="tag_id" (UUID), field="value"
            # Use resolved_tag_id (UUID) for the query, not the original tag name
            # QUALITY FILTERING: Only include "good" quality data to prevent false positives
            flux_query = f'''
from(bucket: "{settings.INFLUXDB_BUCKET}")
  |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
  |> filter(fn: (r) => r["_measurement"] == "tag_data")
  |> filter(fn: (r) => r["tag_id"] == "{resolved_tag_id}")
  |> filter(fn: (r) => r["_field"] == "value")
  |> filter(fn: (r) => r["quality"] == "good")
  |> sort(columns: ["_time"])
            '''

            if aggregation and interval:
                # Apply aggregation if requested (e.g., mean over 5m windows)
                flux_query += f'''
  |> aggregateWindow(every: {interval}, fn: {aggregation}, createEmpty: false)
                '''

            logger.info(f"🔍 Querying InfluxDB for {tag_id} (UUID: {resolved_tag_id}) from {start_time} to {end_time}")
            
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
            
            logger.info(f"✅ Retrieved {len(data_points)} points for {tag_id} (UUID: {resolved_tag_id})")

            return {
                "tag_id": tag_id,
                "tag_uuid": resolved_tag_id,
                "tag_name": tag_name,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "data_points": data_points,
                "points": data_points,  # Alias for compatibility with agent_tools
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
