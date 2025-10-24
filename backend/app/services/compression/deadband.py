"""
Deadband Compression Algorithm

The Deadband algorithm is the simplest compression technique. It only stores
a new value if the change from the last stored value exceeds a threshold.

How it works:
1. Store the first value
2. For each new sample, calculate change from last stored value
3. If abs(change) >= deadband, store the new value
4. Otherwise, discard the sample

This is very effective for slowly changing values or when you only care about
significant changes. It's the most common compression used in industrial systems.

Variants:
- Absolute deadband: abs(new - last) >= deadband
- Percentage deadband: abs(new - last) / last >= deadband_percent
- Combined: Either condition triggers storage
"""
from typing import Optional, List

from app.services.compression.base import CompressionAlgorithm, DataPoint


class DeadbandCompression(CompressionAlgorithm):
    """
    Deadband compression algorithm.

    Configuration parameters:
        deadband (float): Absolute deadband value (engineering units)
            Default: 0.0 (no compression)
        deadband_percent (float): Percentage deadband (0-100)
            Default: None (not used)
        mode (str): "absolute", "percent", or "either"
            Default: "absolute"
        time_deadband_ms (int): Minimum time between stored samples
            Default: 0 (no time restriction)
    """

    def reset(self) -> None:
        """Reset algorithm state"""
        self.deadband = self.config.get("deadband", 0.0)
        self.deadband_percent = self.config.get("deadband_percent", None)
        self.mode = self.config.get("mode", "absolute")
        self.time_deadband_ms = self.config.get("time_deadband_ms", 0)

        # Last stored point
        self.last_stored_point: Optional[DataPoint] = None

        # Statistics
        self.samples_received = 0
        self.samples_stored = 0
        self.samples_compressed_value = 0
        self.samples_compressed_time = 0

    def add_sample(self, point: DataPoint) -> Optional[DataPoint]:
        """
        Add a new sample to the compression buffer.

        Args:
            point: New data point to process

        Returns:
            DataPoint to store, or None if sample is compressed out
        """
        self.samples_received += 1

        # First point - always store
        if self.last_stored_point is None:
            self.last_stored_point = point
            self.samples_stored += 1
            return point

        # Check time deadband
        time_since_last = (point.timestamp - self.last_stored_point.timestamp) * 1000
        if self.time_deadband_ms > 0 and time_since_last < self.time_deadband_ms:
            self.samples_compressed_time += 1
            return None

        # Calculate value change
        value_change = abs(point.value - self.last_stored_point.value)

        # Check if change exceeds deadband
        should_store = False

        if self.mode == "absolute":
            should_store = value_change >= self.deadband

        elif self.mode == "percent":
            if self.deadband_percent is not None and self.last_stored_point.value != 0:
                percent_change = (value_change / abs(self.last_stored_point.value)) * 100
                should_store = percent_change >= self.deadband_percent
            else:
                # Fallback to absolute if percent not configured or zero value
                should_store = value_change >= self.deadband

        elif self.mode == "either":
            # Store if either absolute or percent deadband is exceeded
            absolute_exceeded = value_change >= self.deadband

            percent_exceeded = False
            if self.deadband_percent is not None and self.last_stored_point.value != 0:
                percent_change = (value_change / abs(self.last_stored_point.value)) * 100
                percent_exceeded = percent_change >= self.deadband_percent

            should_store = absolute_exceeded or percent_exceeded

        if should_store:
            self.last_stored_point = point
            self.samples_stored += 1
            return point
        else:
            self.samples_compressed_value += 1
            return None

    def flush(self) -> List[DataPoint]:
        """
        Flush any buffered data points.

        For deadband, there's no buffering, so this returns empty list.

        Returns:
            Empty list
        """
        return []

    def get_statistics(self) -> dict:
        """Get compression statistics"""
        compression_ratio = 0.0
        if self.samples_received > 0:
            compression_ratio = (self.samples_received - self.samples_stored) / self.samples_received * 100

        return {
            "algorithm": "deadband",
            "samples_received": self.samples_received,
            "samples_stored": self.samples_stored,
            "samples_compressed_value": self.samples_compressed_value,
            "samples_compressed_time": self.samples_compressed_time,
            "samples_compressed_total": self.samples_received - self.samples_stored,
            "compression_ratio_percent": round(compression_ratio, 2),
            "config": {
                "deadband": self.deadband,
                "deadband_percent": self.deadband_percent,
                "mode": self.mode,
                "time_deadband_ms": self.time_deadband_ms
            }
        }

    def __repr__(self):
        stats = self.get_statistics()
        return (f"<DeadbandCompression "
                f"deadband={self.deadband} "
                f"mode={self.mode} "
                f"compression={stats['compression_ratio_percent']}%>")
