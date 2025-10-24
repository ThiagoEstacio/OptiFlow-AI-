"""
Time Series Data Service

Service for querying historical time-series data from InfluxDB.
Supports:
- Single and multi-tag queries
- Time range filtering
- Data aggregation (avg, min, max, sum, count)
- Downsampling for performance
- Statistical calculations
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from loguru import logger


class AggregationFunction(str, Enum):
    """Aggregation functions for time-series data"""
    MEAN = "mean"
    MIN = "min"
    MAX = "max"
    SUM = "sum"
    COUNT = "count"
    FIRST = "first"
    LAST = "last"
    STDDEV = "stddev"


@dataclass
class TimeSeriesQuery:
    """Parameters for time-series query"""
    tag_ids: List[str]
    start_time: datetime
    end_time: datetime
    aggregation: Optional[AggregationFunction] = None
    interval: Optional[str] = None  # e.g., "1m", "5m", "1h"
    fill: Optional[str] = "null"  # null, previous, linear, 0
    limit: Optional[int] = None


@dataclass
class DataPoint:
    """Single data point in time series"""
    timestamp: datetime
    value: float
    quality: Optional[str] = "Good"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "quality": self.quality
        }


@dataclass
class TagSeries:
    """Time series data for a single tag"""
    tag_id: str
    tag_name: Optional[str] = None
    data_points: List[DataPoint] = None
    statistics: Optional[Dict[str, float]] = None

    def __post_init__(self):
        if self.data_points is None:
            self.data_points = []

    def to_dict(self) -> dict:
        return {
            "tag_id": self.tag_id,
            "tag_name": self.tag_name,
            "data_points": [dp.to_dict() for dp in self.data_points],
            "statistics": self.statistics or {},
            "count": len(self.data_points)
        }


class TimeSeriesService:
    """
    Service for querying and analyzing time-series data.

    This is a mock implementation. In production, this would connect to
    InfluxDB or TimescaleDB.
    """

    def __init__(self, influxdb_client=None):
        """
        Initialize time series service.

        Args:
            influxdb_client: Optional InfluxDB client (for production)
        """
        self.influxdb_client = influxdb_client
        logger.info("TimeSeriesService initialized")

    async def query_tag_data(
        self,
        tag_id: str,
        start_time: datetime,
        end_time: datetime,
        aggregation: Optional[AggregationFunction] = None,
        interval: Optional[str] = None,
        limit: Optional[int] = None
    ) -> TagSeries:
        """
        Query time-series data for a single tag.

        Args:
            tag_id: Tag identifier
            start_time: Start of time range
            end_time: End of time range
            aggregation: Optional aggregation function
            interval: Optional aggregation interval
            limit: Maximum number of points to return

        Returns:
            TagSeries with data points
        """
        # TODO: Implement InfluxDB query
        # For now, return mock data
        logger.info(f"Querying tag {tag_id} from {start_time} to {end_time}")

        data_points = self._generate_mock_data(start_time, end_time, limit or 1000)

        # Calculate statistics
        if data_points:
            values = [dp.value for dp in data_points]
            statistics = {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "count": len(values)
            }
        else:
            statistics = {}

        return TagSeries(
            tag_id=tag_id,
            data_points=data_points,
            statistics=statistics
        )

    async def query_multiple_tags(
        self,
        query: TimeSeriesQuery
    ) -> List[TagSeries]:
        """
        Query time-series data for multiple tags.

        Args:
            query: TimeSeriesQuery parameters

        Returns:
            List of TagSeries, one per tag
        """
        results = []

        for tag_id in query.tag_ids:
            tag_series = await self.query_tag_data(
                tag_id=tag_id,
                start_time=query.start_time,
                end_time=query.end_time,
                aggregation=query.aggregation,
                interval=query.interval,
                limit=query.limit
            )
            results.append(tag_series)

        return results

    async def query_latest_values(
        self,
        tag_ids: List[str]
    ) -> Dict[str, DataPoint]:
        """
        Get latest value for each tag.

        Args:
            tag_ids: List of tag IDs

        Returns:
            Dictionary mapping tag_id to latest DataPoint
        """
        results = {}

        for tag_id in tag_ids:
            # TODO: Query actual latest value from database
            # Mock data for now
            results[tag_id] = DataPoint(
                timestamp=datetime.now(),
                value=0.0,
                quality="Good"
            )

        return results

    async def downsample_data(
        self,
        tag_id: str,
        start_time: datetime,
        end_time: datetime,
        max_points: int = 1000
    ) -> TagSeries:
        """
        Downsample data to reduce number of points.

        Automatically calculates appropriate interval based on time range
        and desired max_points.

        Args:
            tag_id: Tag identifier
            start_time: Start of time range
            end_time: End of time range
            max_points: Maximum number of points to return

        Returns:
            TagSeries with downsampled data
        """
        # Calculate appropriate interval
        time_range = (end_time - start_time).total_seconds()
        interval_seconds = max(1, int(time_range / max_points))

        # Convert to InfluxDB interval format
        if interval_seconds < 60:
            interval = f"{interval_seconds}s"
        elif interval_seconds < 3600:
            interval = f"{interval_seconds // 60}m"
        else:
            interval = f"{interval_seconds // 3600}h"

        return await self.query_tag_data(
            tag_id=tag_id,
            start_time=start_time,
            end_time=end_time,
            aggregation=AggregationFunction.MEAN,
            interval=interval,
            limit=max_points
        )

    async def calculate_statistics(
        self,
        tag_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """
        Calculate statistical metrics for a tag over time range.

        Args:
            tag_id: Tag identifier
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Dictionary with statistical metrics
        """
        tag_series = await self.query_tag_data(
            tag_id=tag_id,
            start_time=start_time,
            end_time=end_time
        )

        if not tag_series.data_points:
            return {}

        values = [dp.value for dp in tag_series.data_points]

        # Calculate statistics
        count = len(values)
        total = sum(values)
        mean = total / count
        sorted_values = sorted(values)

        # Median
        if count % 2 == 0:
            median = (sorted_values[count // 2 - 1] + sorted_values[count // 2]) / 2
        else:
            median = sorted_values[count // 2]

        # Standard deviation
        variance = sum((x - mean) ** 2 for x in values) / count
        stddev = variance ** 0.5

        return {
            "count": count,
            "min": min(values),
            "max": max(values),
            "mean": mean,
            "median": median,
            "stddev": stddev,
            "sum": total,
            "range": max(values) - min(values)
        }

    def _generate_mock_data(
        self,
        start_time: datetime,
        end_time: datetime,
        num_points: int
    ) -> List[DataPoint]:
        """
        Generate mock time-series data for testing.

        Args:
            start_time: Start timestamp
            end_time: End timestamp
            num_points: Number of points to generate

        Returns:
            List of DataPoints
        """
        import math
        import random

        data_points = []
        time_delta = (end_time - start_time) / (num_points - 1) if num_points > 1 else timedelta(seconds=0)

        for i in range(num_points):
            timestamp = start_time + (time_delta * i)

            # Generate sinusoidal pattern with noise
            t = i / num_points * 4 * math.pi  # 2 cycles
            base_value = 50 + 30 * math.sin(t)
            noise = random.uniform(-2, 2)
            value = base_value + noise

            data_points.append(DataPoint(
                timestamp=timestamp,
                value=round(value, 2),
                quality="Good"
            ))

        return data_points

    async def export_to_csv(
        self,
        tag_series: TagSeries,
        include_quality: bool = True
    ) -> str:
        """
        Export tag series to CSV format.

        Args:
            tag_series: TagSeries to export
            include_quality: Include quality column

        Returns:
            CSV string
        """
        lines = []

        # Header
        if include_quality:
            lines.append("timestamp,value,quality")
        else:
            lines.append("timestamp,value")

        # Data rows
        for dp in tag_series.data_points:
            if include_quality:
                lines.append(f"{dp.timestamp.isoformat()},{dp.value},{dp.quality}")
            else:
                lines.append(f"{dp.timestamp.isoformat()},{dp.value}")

        return "\n".join(lines)

    async def export_multiple_to_csv(
        self,
        tag_series_list: List[TagSeries]
    ) -> str:
        """
        Export multiple tag series to CSV format (wide format).

        Args:
            tag_series_list: List of TagSeries to export

        Returns:
            CSV string with columns for each tag
        """
        if not tag_series_list:
            return ""

        # Get all unique timestamps
        all_timestamps = set()
        for series in tag_series_list:
            for dp in series.data_points:
                all_timestamps.add(dp.timestamp)

        sorted_timestamps = sorted(all_timestamps)

        # Build header
        header = ["timestamp"]
        for series in tag_series_list:
            header.append(series.tag_name or series.tag_id)

        lines = [",".join(header)]

        # Build data rows
        for timestamp in sorted_timestamps:
            row = [timestamp.isoformat()]

            for series in tag_series_list:
                # Find value for this timestamp
                value = ""
                for dp in series.data_points:
                    if dp.timestamp == timestamp:
                        value = str(dp.value)
                        break

                row.append(value)

            lines.append(",".join(row))

        return "\n".join(lines)


# Global time series service instance
timeseries_service = TimeSeriesService()
