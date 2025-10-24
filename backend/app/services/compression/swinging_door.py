"""
Swinging Door Compression Algorithm

The Swinging Door algorithm is a popular lossy compression technique for time-series data.
It works by keeping a "door" that "swings" based on deviation from a linear trend.

How it works:
1. Store the first point
2. For each new point, check if it falls within the acceptable deviation from
   the trend line formed by the stored point and current point
3. If within deviation, continue (compress out the sample)
4. If outside deviation, store the previous point and start a new trend

This maintains data fidelity within the specified deviation while significantly
reducing storage requirements for slowly changing values.

Reference:
- Bristol, E. H. (1990). "Swinging door trending: Adaptive trend recording"
"""
from typing import Optional, List
import math

from app.services.compression.base import CompressionAlgorithm, DataPoint


class SwingingDoorCompression(CompressionAlgorithm):
    """
    Swinging Door compression algorithm.

    Configuration parameters:
        deviation (float): Maximum allowed deviation from trend line (engineering units)
        time_deadband_ms (int): Minimum time between stored samples in milliseconds
            Default: 0 (no time restriction)
    """

    def reset(self) -> None:
        """Reset algorithm state"""
        self.deviation = self.config.get("deviation", 1.0)
        self.time_deadband_ms = self.config.get("time_deadband_ms", 0)

        # Stored points
        self.archived_point: Optional[DataPoint] = None
        self.snapshot_point: Optional[DataPoint] = None

        # Swinging door boundaries (slopes)
        self.max_slope: Optional[float] = None
        self.min_slope: Optional[float] = None

        # Statistics
        self.samples_received = 0
        self.samples_stored = 0

    def add_sample(self, point: DataPoint) -> Optional[DataPoint]:
        """
        Add a new sample to the compression buffer.

        Args:
            point: New data point to process

        Returns:
            DataPoint to store, or None if sample is compressed out
        """
        self.samples_received += 1

        # First point - always archive
        if self.archived_point is None:
            self.archived_point = point
            self.samples_stored += 1
            return point

        # Second point - initialize snapshot and slopes
        if self.snapshot_point is None:
            self.snapshot_point = point
            self._calculate_slopes(point)
            return None

        # Check time deadband
        time_since_last = (point.timestamp - self.archived_point.timestamp) * 1000
        if self.time_deadband_ms > 0 and time_since_last < self.time_deadband_ms:
            # Update snapshot to latest point within deadband
            self.snapshot_point = point
            self._calculate_slopes(point)
            return None

        # Check if point is within swinging door boundaries
        if self._is_within_door(point):
            # Point is within door - update snapshot and compress
            self.snapshot_point = point
            self._calculate_slopes(point)
            return None
        else:
            # Point is outside door - archive snapshot and start new trend
            point_to_store = self.snapshot_point
            self.archived_point = self.snapshot_point
            self.snapshot_point = point
            self._calculate_slopes(point)

            self.samples_stored += 1
            return point_to_store

    def _calculate_slopes(self, point: DataPoint) -> None:
        """
        Calculate the max and min slopes (swinging door boundaries).

        Args:
            point: Current point to calculate slopes from
        """
        if self.archived_point is None:
            return

        time_diff = point.timestamp - self.archived_point.timestamp

        if time_diff == 0:
            # Avoid division by zero
            self.max_slope = float('inf')
            self.min_slope = float('-inf')
            return

        # Calculate slopes with deviation
        upper_value = point.value + self.deviation
        lower_value = point.value - self.deviation

        upper_slope = (upper_value - self.archived_point.value) / time_diff
        lower_slope = (lower_value - self.archived_point.value) / time_diff

        # Initialize or narrow the door
        if self.max_slope is None or self.min_slope is None:
            self.max_slope = upper_slope
            self.min_slope = lower_slope
        else:
            # Narrow the door (intersection of slopes)
            self.max_slope = min(self.max_slope, upper_slope)
            self.min_slope = max(self.min_slope, lower_slope)

    def _is_within_door(self, point: DataPoint) -> bool:
        """
        Check if point is within the swinging door boundaries.

        Args:
            point: Point to check

        Returns:
            True if within boundaries, False otherwise
        """
        if self.archived_point is None:
            return True

        if self.max_slope is None or self.min_slope is None:
            return True

        # Check if slopes have crossed (door closed)
        if self.max_slope < self.min_slope:
            return False

        time_diff = point.timestamp - self.archived_point.timestamp

        if time_diff == 0:
            # Same timestamp - check value deviation
            return abs(point.value - self.archived_point.value) <= self.deviation

        # Calculate expected value range based on slopes
        expected_max = self.archived_point.value + (self.max_slope * time_diff)
        expected_min = self.archived_point.value + (self.min_slope * time_diff)

        # Check if point value is within the door
        return (point.value >= (expected_min - self.deviation) and
                point.value <= (expected_max + self.deviation))

    def flush(self) -> List[DataPoint]:
        """
        Flush any buffered data points.

        Returns:
            List of buffered points (snapshot point if exists)
        """
        points = []

        if self.snapshot_point is not None:
            points.append(self.snapshot_point)
            self.samples_stored += 1
            self.archived_point = self.snapshot_point
            self.snapshot_point = None
            self.max_slope = None
            self.min_slope = None

        return points

    def get_statistics(self) -> dict:
        """Get compression statistics"""
        compression_ratio = 0.0
        if self.samples_received > 0:
            compression_ratio = (self.samples_received - self.samples_stored) / self.samples_received * 100

        return {
            "algorithm": "swinging_door",
            "samples_received": self.samples_received,
            "samples_stored": self.samples_stored,
            "samples_compressed": self.samples_received - self.samples_stored,
            "compression_ratio_percent": round(compression_ratio, 2),
            "config": {
                "deviation": self.deviation,
                "time_deadband_ms": self.time_deadband_ms
            }
        }

    def __repr__(self):
        stats = self.get_statistics()
        return (f"<SwingingDoorCompression "
                f"deviation={self.deviation} "
                f"compression={stats['compression_ratio_percent']}%>")
