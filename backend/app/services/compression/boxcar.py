"""
BoxCar Compression Algorithm

The BoxCar algorithm is a simple time-based compression technique that stores
representative values over fixed time windows.

How it works:
1. Define a time window (e.g., 1 minute)
2. Collect all samples within that window
3. When the window closes, store a representative value (min, max, average, or last)
4. Also store if value change exceeds threshold

This is useful for high-frequency data where you want periodic snapshots
while also capturing significant changes.

Variations:
- Simple BoxCar: Store last value in window
- Min/Max BoxCar: Store min and max in window
- Average BoxCar: Store average of all values in window
- Change-based: Also store if change exceeds threshold
"""
from typing import Optional, List
from datetime import datetime

from app.services.compression.base import CompressionAlgorithm, DataPoint


class BoxCarCompression(CompressionAlgorithm):
    """
    BoxCar compression algorithm.

    Configuration parameters:
        time_window_ms (int): Time window in milliseconds
            Default: 60000 (1 minute)
        change_threshold (float): Minimum change to trigger immediate storage
            Default: None (no change-based trigger)
        store_method (str): Method for storing value
            Options: "last", "average", "min", "max", "min_max"
            Default: "last"
    """

    def reset(self) -> None:
        """Reset algorithm state"""
        self.time_window_ms = self.config.get("time_window_ms", 60000)
        self.change_threshold = self.config.get("change_threshold", None)
        self.store_method = self.config.get("store_method", "last")

        # Window tracking
        self.window_start_time: Optional[float] = None
        self.window_samples: List[DataPoint] = []

        # Last stored value for change detection
        self.last_stored_value: Optional[float] = None
        self.last_stored_point: Optional[DataPoint] = None

        # Statistics
        self.samples_received = 0
        self.samples_stored = 0
        self.windows_completed = 0
        self.change_triggered_stores = 0

    def add_sample(self, point: DataPoint) -> Optional[DataPoint]:
        """
        Add a new sample to the compression buffer.

        Args:
            point: New data point to process

        Returns:
            DataPoint to store, or None if sample is buffered
        """
        self.samples_received += 1

        # Initialize window on first sample
        if self.window_start_time is None:
            self.window_start_time = point.timestamp
            self.window_samples.append(point)

            # First point is always stored
            self.last_stored_value = point.value
            self.last_stored_point = point
            self.samples_stored += 1
            return point

        # Check if we need to close current window
        window_elapsed_ms = (point.timestamp - self.window_start_time) * 1000

        if window_elapsed_ms >= self.time_window_ms:
            # Close current window and store representative value
            stored_point = self._close_window()

            # Start new window
            self.window_start_time = point.timestamp
            self.window_samples = [point]

            return stored_point

        # Add to current window
        self.window_samples.append(point)

        # Check for change threshold trigger
        if self.change_threshold is not None and self.last_stored_value is not None:
            change = abs(point.value - self.last_stored_value)
            if change >= self.change_threshold:
                # Significant change detected - store immediately
                self.last_stored_value = point.value
                self.last_stored_point = point
                self.samples_stored += 1
                self.change_triggered_stores += 1
                return point

        return None

    def _close_window(self) -> Optional[DataPoint]:
        """
        Close current window and return representative point.

        Returns:
            Representative DataPoint for the window
        """
        if not self.window_samples:
            return None

        self.windows_completed += 1

        # Calculate representative value based on method
        if self.store_method == "last":
            result_point = self.window_samples[-1]

        elif self.store_method == "average":
            avg_value = sum(p.value for p in self.window_samples) / len(self.window_samples)
            # Use timestamp of last sample
            result_point = DataPoint(
                timestamp=self.window_samples[-1].timestamp,
                value=avg_value,
                quality=self.window_samples[-1].quality,
                metadata={"method": "average", "samples_in_window": len(self.window_samples)}
            )

        elif self.store_method == "min":
            min_point = min(self.window_samples, key=lambda p: p.value)
            result_point = DataPoint(
                timestamp=min_point.timestamp,
                value=min_point.value,
                quality=min_point.quality,
                metadata={"method": "min", "samples_in_window": len(self.window_samples)}
            )

        elif self.store_method == "max":
            max_point = max(self.window_samples, key=lambda p: p.value)
            result_point = DataPoint(
                timestamp=max_point.timestamp,
                value=max_point.value,
                quality=max_point.quality,
                metadata={"method": "max", "samples_in_window": len(self.window_samples)}
            )

        elif self.store_method == "min_max":
            # This mode returns two points - we'll return the max
            # In a real implementation, you might want to handle this differently
            min_point = min(self.window_samples, key=lambda p: p.value)
            max_point = max(self.window_samples, key=lambda p: p.value)
            # For now, return the point with greater deviation from last stored
            if self.last_stored_value is not None:
                if abs(min_point.value - self.last_stored_value) > abs(max_point.value - self.last_stored_value):
                    result_point = min_point
                else:
                    result_point = max_point
            else:
                result_point = max_point

        else:
            # Default to last
            result_point = self.window_samples[-1]

        # Update last stored tracking
        self.last_stored_value = result_point.value
        self.last_stored_point = result_point
        self.samples_stored += 1

        return result_point

    def flush(self) -> List[DataPoint]:
        """
        Flush any buffered data points.

        Returns:
            List containing the representative point for current window
        """
        points = []

        if self.window_samples:
            closed_point = self._close_window()
            if closed_point:
                points.append(closed_point)

            # Reset window
            self.window_start_time = None
            self.window_samples = []

        return points

    def get_statistics(self) -> dict:
        """Get compression statistics"""
        compression_ratio = 0.0
        if self.samples_received > 0:
            compression_ratio = (self.samples_received - self.samples_stored) / self.samples_received * 100

        avg_samples_per_window = 0.0
        if self.windows_completed > 0:
            avg_samples_per_window = self.samples_received / self.windows_completed

        return {
            "algorithm": "boxcar",
            "samples_received": self.samples_received,
            "samples_stored": self.samples_stored,
            "samples_compressed": self.samples_received - self.samples_stored,
            "compression_ratio_percent": round(compression_ratio, 2),
            "windows_completed": self.windows_completed,
            "change_triggered_stores": self.change_triggered_stores,
            "avg_samples_per_window": round(avg_samples_per_window, 2),
            "config": {
                "time_window_ms": self.time_window_ms,
                "change_threshold": self.change_threshold,
                "store_method": self.store_method
            }
        }

    def __repr__(self):
        stats = self.get_statistics()
        return (f"<BoxCarCompression "
                f"window={self.time_window_ms}ms "
                f"method={self.store_method} "
                f"compression={stats['compression_ratio_percent']}%>")
