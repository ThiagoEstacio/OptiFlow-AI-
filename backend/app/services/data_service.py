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
from sqlalchemy.orm import Session
from sqlalchemy import text, select
import asyncio
import logging

logger = logging.getLogger(__name__)


class DataService:
    """Service for accessing real-time and historical data"""
    
    def __init__(self, db):
        """Initialize with either sync or async session"""
        self.db = db
        self.is_async = isinstance(db, AsyncSession)
        
    async def get_realtime_value(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current value of a tag from the database
        
        Args:
            tag_id: Tag identifier
            
        Returns:
            Dict with value, timestamp, quality, or None if not found
        """
        try:
            query = text("""
                SELECT 
                    t.id,
                    t.name,
                    t.tag_address,
                    t.data_type,
                    t.description,
                    t.unit,
                    t.min_value,
                    t.max_value,
                    t.current_value,
                    t.updated_at
                FROM tags t
                WHERE t.name = :tag_id OR t.tag_address = :tag_id OR CAST(t.id AS TEXT) = :tag_id
                LIMIT 1
            """)
            
            if self.is_async:
                result = await self.db.execute(query, {"tag_id": tag_id})
                row = result.fetchone()
            else:
                result = self.db.execute(query, {"tag_id": tag_id})
                row = result.fetchone()
            
            if not row:
                return None
                
            return {
                "tag_id": row[1],  # name
                "tag_address": row[2],
                "data_type": row[3],
                "description": row[4],
                "unit": row[5],
                "min_value": float(row[6]) if row[6] is not None else 0,
                "max_value": float(row[7]) if row[7] is not None else 100,
                "value": row[8],  # current_value
                "timestamp": row[9].isoformat() if row[9] else datetime.now().isoformat(),
                "quality": "good"
            }
            
        except Exception as e:
            logger.error(f"Error getting realtime value for {tag_id}: {e}")
            # Rollback failed transaction
            if self.is_async:
                await self.db.rollback()
            else:
                self.db.rollback()
            return None
            logger.error(f"Error getting realtime value for {tag_id}: {str(e)}")
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
        Get historical data from InfluxDB (simulated for now)
        
        Args:
            tag_id: Tag identifier
            start_time: Start of time range
            end_time: End of time range
            duration: Duration string (e.g., "1h", "24h", "7d") if start_time not provided
            aggregation: Aggregation function (mean, max, min, stddev, sum)
            interval: Aggregation interval (e.g., "1m", "5m", "1h")
            
        Returns:
            Dict with data points and metadata
        """
        try:
            # Parse duration to get start_time if not provided
            if not start_time:
                end_time = end_time or datetime.now()
                duration_map = {
                    "1h": timedelta(hours=1),
                    "6h": timedelta(hours=6),
                    "12h": timedelta(hours=12),
                    "24h": timedelta(days=1),
                    "7d": timedelta(days=7),
                    "30d": timedelta(days=30)
                }
                delta = duration_map.get(duration, timedelta(hours=1))
                start_time = end_time - delta
            
            # For now, generate simulated historical data
            # TODO: Replace with actual InfluxDB query when available
            data_points = []
            
            # Get tag info for realistic ranges
            tag_info = await self.get_realtime_value(tag_id)
            if not tag_info:
                return {
                    "tag_id": tag_id,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "data_points": [],
                    "count": 0
                }
            
            min_val = tag_info.get("min_value", 0)
            max_val = tag_info.get("max_value", 100)
            
            # Generate sample data points
            import random
            time_diff = end_time - start_time
            num_points = min(100, int(time_diff.total_seconds() / 60))  # 1 point per minute, max 100
            
            for i in range(num_points):
                timestamp = start_time + (time_diff * i / num_points)
                # Simulate realistic industrial data with some noise
                base_value = (min_val + max_val) / 2
                variation = (max_val - min_val) * 0.2
                value = base_value + random.uniform(-variation, variation)
                
                data_points.append({
                    "timestamp": timestamp.isoformat(),
                    "value": round(value, 2),
                    "quality": "good"
                })
            
            result = {
                "tag_id": tag_id,
                "tag_name": tag_info.get("tag_id"),
                "description": tag_info.get("description"),
                "unit": tag_info.get("unit"),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "data_points": data_points,
                "count": len(data_points)
            }
            
            # Apply aggregation if requested
            if aggregation and data_points:
                values = [p["value"] for p in data_points]
                result["aggregation"] = {
                    "function": aggregation,
                    "interval": interval or "raw"
                }
                
                if aggregation == "mean":
                    result["aggregation"]["value"] = round(sum(values) / len(values), 2)
                elif aggregation == "max":
                    result["aggregation"]["value"] = round(max(values), 2)
                elif aggregation == "min":
                    result["aggregation"]["value"] = round(min(values), 2)
                elif aggregation == "sum":
                    result["aggregation"]["value"] = round(sum(values), 2)
                elif aggregation == "stddev":
                    mean = sum(values) / len(values)
                    variance = sum((x - mean) ** 2 for x in values) / len(values)
                    result["aggregation"]["value"] = round(variance ** 0.5, 2)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting historical data for {tag_id}: {str(e)}")
            return {
                "tag_id": tag_id,
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
                    t.tag_address,
                    t.description,
                    t.unit,
                    t.data_type,
                    t.min_value,
                    t.max_value
                FROM tags t
                WHERE 
                    LOWER(t.name) LIKE LOWER(:query) 
                    OR LOWER(t.description) LIKE LOWER(:query)
                    OR LOWER(t.tag_address) LIKE LOWER(:query)
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
            results = self.db.execute(
                sql_query, 
                {
                    "query": search_pattern,
                    "exact_query": query,
                    "limit": limit
                }
            ).fetchall()
            
            tags = []
            for row in results:
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
