"""
Tests for Compression Algorithms

Tests SwingingDoor, BoxCar, and Deadband compression algorithms.
"""
import pytest
from datetime import datetime, timedelta

from app.services.compression import (
    DataPoint,
    SwingingDoorCompression,
    BoxCarCompression,
    DeadbandCompression
)


class TestDataPoint:
    """Test DataPoint class"""

    def test_create_datapoint(self):
        """Test creating a DataPoint"""
        point = DataPoint(timestamp=1000.0, value=25.5, quality="Good")

        assert point.timestamp == 1000.0
        assert point.value == 25.5
        assert point.quality == "Good"
        assert point.metadata is None

    def test_create_from_datetime(self):
        """Test creating DataPoint from datetime"""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        point = DataPoint.from_datetime(dt, 30.0)

        assert isinstance(point.timestamp, float)
        assert point.value == 30.0
        assert point.quality == "Good"

    def test_to_datetime(self):
        """Test converting timestamp to datetime"""
        point = DataPoint(timestamp=1704110400.0, value=25.0)  # 2024-01-01 12:00:00 UTC
        dt = point.to_datetime()

        assert isinstance(dt, datetime)

    def test_comparison(self):
        """Test DataPoint comparison by timestamp"""
        p1 = DataPoint(timestamp=1000.0, value=10.0)
        p2 = DataPoint(timestamp=2000.0, value=20.0)

        assert p1 < p2
        assert not p2 < p1


class TestDeadbandCompression:
    """Test Deadband compression algorithm"""

    def test_initialization(self):
        """Test algorithm initialization"""
        config = {"deadband": 1.0, "mode": "absolute"}
        algo = DeadbandCompression(config)

        assert algo.deadband == 1.0
        assert algo.mode == "absolute"
        assert algo.samples_received == 0
        assert algo.samples_stored == 0

    def test_first_point_stored(self):
        """Test that first point is always stored"""
        algo = DeadbandCompression({"deadband": 1.0})
        point = DataPoint(timestamp=1000.0, value=10.0)

        result = algo.add_sample(point)

        assert result is not None
        assert result.value == 10.0
        stats = algo.get_statistics()
        assert stats["samples_received"] == 1
        assert stats["samples_stored"] == 1

    def test_absolute_deadband_compression(self):
        """Test absolute deadband compression"""
        algo = DeadbandCompression({"deadband": 1.0, "mode": "absolute"})

        # First point - stored
        p1 = DataPoint(timestamp=1000.0, value=10.0)
        assert algo.add_sample(p1) is not None

        # Change < deadband - compressed
        p2 = DataPoint(timestamp=2000.0, value=10.5)
        assert algo.add_sample(p2) is None

        # Change >= deadband - stored
        p3 = DataPoint(timestamp=3000.0, value=11.0)
        assert algo.add_sample(p3) is not None

        # Change < deadband - compressed
        p4 = DataPoint(timestamp=4000.0, value=11.8)
        assert algo.add_sample(p4) is None

        # Change >= deadband - stored
        p5 = DataPoint(timestamp=5000.0, value=12.0)
        assert algo.add_sample(p5) is not None

        stats = algo.get_statistics()
        assert stats["samples_received"] == 5
        assert stats["samples_stored"] == 3
        assert stats["samples_compressed_value"] == 2
        assert stats["compression_ratio_percent"] == 40.0

    def test_percent_deadband(self):
        """Test percentage deadband compression"""
        algo = DeadbandCompression({"deadband_percent": 10.0, "mode": "percent"})

        # First point
        p1 = DataPoint(timestamp=1000.0, value=100.0)
        assert algo.add_sample(p1) is not None

        # 5% change - compressed
        p2 = DataPoint(timestamp=2000.0, value=105.0)
        assert algo.add_sample(p2) is None

        # 15% change - stored
        p3 = DataPoint(timestamp=3000.0, value=115.0)
        assert algo.add_sample(p3) is not None

        stats = algo.get_statistics()
        assert stats["samples_stored"] == 2

    def test_time_deadband(self):
        """Test time deadband compression"""
        algo = DeadbandCompression({
            "deadband": 0.1,
            "time_deadband_ms": 1000  # 1 second minimum
        })

        # First point
        p1 = DataPoint(timestamp=1000.0, value=10.0)
        assert algo.add_sample(p1) is not None

        # Large value change but too soon - compressed
        p2 = DataPoint(timestamp=1000.5, value=20.0)  # 0.5s later
        assert algo.add_sample(p2) is None

        # After time deadband - stored
        p3 = DataPoint(timestamp=2001.0, value=20.0)  # 1.001s later
        assert algo.add_sample(p3) is not None

        stats = algo.get_statistics()
        assert stats["samples_compressed_time"] == 1

    def test_flush_returns_empty(self):
        """Test that flush returns empty for deadband"""
        algo = DeadbandCompression({"deadband": 1.0})

        p1 = DataPoint(timestamp=1000.0, value=10.0)
        algo.add_sample(p1)

        flushed = algo.flush()
        assert len(flushed) == 0


class TestSwingingDoorCompression:
    """Test SwingingDoor compression algorithm"""

    def test_initialization(self):
        """Test algorithm initialization"""
        config = {"deviation": 2.0, "time_deadband_ms": 1000}
        algo = SwingingDoorCompression(config)

        assert algo.deviation == 2.0
        assert algo.time_deadband_ms == 1000
        assert algo.samples_received == 0
        assert algo.samples_stored == 0

    def test_first_point_stored(self):
        """Test that first point is always stored"""
        algo = SwingingDoorCompression({"deviation": 1.0})
        point = DataPoint(timestamp=1000.0, value=10.0)

        result = algo.add_sample(point)

        assert result is not None
        assert result.value == 10.0

    def test_linear_trend_compression(self):
        """Test compression of linear trend within deviation"""
        algo = SwingingDoorCompression({"deviation": 1.0})

        # Create linear trend: y = 10 + 0.001*t
        points = []
        for i in range(10):
            t = 1000.0 + i * 1000.0  # 1 second intervals
            v = 10.0 + 0.001 * (i * 1000.0)  # Linear increase
            points.append(DataPoint(timestamp=t, value=v))

        results = [algo.add_sample(p) for p in points]

        # First point should be stored
        assert results[0] is not None

        # Most intermediate points should be compressed (within deviation)
        compressed_count = sum(1 for r in results if r is None)
        assert compressed_count > 0

        stats = algo.get_statistics()
        assert stats["compression_ratio_percent"] > 0

    def test_non_linear_trend_stores_points(self):
        """Test that non-linear trends store more points"""
        algo = SwingingDoorCompression({"deviation": 1.0})

        # Create non-linear data (sine wave)
        import math
        points = []
        for i in range(20):
            t = 1000.0 + i * 100.0
            v = 10.0 + 5.0 * math.sin(i / 3.0)
            points.append(DataPoint(timestamp=t, value=v))

        results = [algo.add_sample(p) for p in points]

        # With sine wave, should store more points than linear
        stored_count = sum(1 for r in results if r is not None)
        assert stored_count > 2  # More than just first point

    def test_sudden_change_stores_point(self):
        """Test that sudden changes store points"""
        algo = SwingingDoorCompression({"deviation": 1.0})

        # Flat then sudden jump
        p1 = DataPoint(timestamp=1000.0, value=10.0)
        p2 = DataPoint(timestamp=2000.0, value=10.0)
        p3 = DataPoint(timestamp=3000.0, value=10.0)
        p4 = DataPoint(timestamp=4000.0, value=20.0)  # Sudden jump

        assert algo.add_sample(p1) is not None  # First
        assert algo.add_sample(p2) is None  # Compressed
        assert algo.add_sample(p3) is None  # Compressed
        result = algo.add_sample(p4)
        # Should store p3 (previous point before deviation)
        assert result is not None

    def test_flush_stores_pending(self):
        """Test that flush stores pending snapshot"""
        algo = SwingingDoorCompression({"deviation": 1.0})

        p1 = DataPoint(timestamp=1000.0, value=10.0)
        p2 = DataPoint(timestamp=2000.0, value=10.5)
        p3 = DataPoint(timestamp=3000.0, value=11.0)

        algo.add_sample(p1)  # Stored
        algo.add_sample(p2)  # Snapshot
        algo.add_sample(p3)  # New snapshot

        flushed = algo.flush()

        assert len(flushed) == 1
        assert flushed[0].value == 11.0

    def test_time_deadband(self):
        """Test time deadband in swinging door"""
        algo = SwingingDoorCompression({
            "deviation": 1.0,
            "time_deadband_ms": 5000  # 5 seconds
        })

        p1 = DataPoint(timestamp=1000.0, value=10.0)
        p2 = DataPoint(timestamp=2000.0, value=15.0)  # 1s later, large change
        p3 = DataPoint(timestamp=6001.0, value=15.0)  # >5s later

        assert algo.add_sample(p1) is not None  # Stored
        assert algo.add_sample(p2) is None  # Within time deadband
        # p3 should trigger storage due to time deadband

    def test_statistics(self):
        """Test compression statistics"""
        algo = SwingingDoorCompression({"deviation": 1.0})

        for i in range(10):
            p = DataPoint(timestamp=1000.0 + i * 1000.0, value=10.0)
            algo.add_sample(p)

        stats = algo.get_statistics()

        assert stats["algorithm"] == "swinging_door"
        assert stats["samples_received"] == 10
        assert "compression_ratio_percent" in stats
        assert "config" in stats


class TestBoxCarCompression:
    """Test BoxCar compression algorithm"""

    def test_initialization(self):
        """Test algorithm initialization"""
        config = {"time_window_ms": 60000, "store_method": "average"}
        algo = BoxCarCompression(config)

        assert algo.time_window_ms == 60000
        assert algo.store_method == "average"

    def test_last_value_method(self):
        """Test storing last value in window"""
        algo = BoxCarCompression({"time_window_ms": 1000, "store_method": "last"})

        # First point
        p1 = DataPoint(timestamp=1000.0, value=10.0)
        assert algo.add_sample(p1) is not None  # First always stored

        # Add points within window
        p2 = DataPoint(timestamp=1000.2, value=11.0)
        p3 = DataPoint(timestamp=1000.5, value=12.0)
        assert algo.add_sample(p2) is None
        assert algo.add_sample(p3) is None

        # Close window with next point
        p4 = DataPoint(timestamp=2000.5, value=13.0)
        result = algo.add_sample(p4)

        # Should store last value from previous window (p3)
        assert result is not None
        assert result.value == 12.0

    def test_average_method(self):
        """Test storing average value in window"""
        algo = BoxCarCompression({"time_window_ms": 1000, "store_method": "average"})

        p1 = DataPoint(timestamp=1000.0, value=10.0)
        algo.add_sample(p1)  # First

        p2 = DataPoint(timestamp=1000.3, value=12.0)
        p3 = DataPoint(timestamp=1000.6, value=14.0)
        algo.add_sample(p2)
        algo.add_sample(p3)

        # Close window
        p4 = DataPoint(timestamp=2000.5, value=16.0)
        result = algo.add_sample(p4)

        # Average of p2 and p3 in window = (12 + 14) / 2 = 13
        # But p1 was stored immediately, so average is of samples in window (p2, p3)
        # Wait, actually all samples in the window including p1: (10 + 12 + 14) / 3 = 12
        assert result is not None
        assert result.value == 12.0
        assert result.metadata["method"] == "average"
        assert result.metadata["samples_in_window"] == 3

    def test_min_method(self):
        """Test storing minimum value in window"""
        algo = BoxCarCompression({"time_window_ms": 1000, "store_method": "min"})

        p1 = DataPoint(timestamp=1000.0, value=10.0)
        algo.add_sample(p1)

        p2 = DataPoint(timestamp=1000.3, value=12.0)
        p3 = DataPoint(timestamp=1000.6, value=8.0)  # Min
        p4 = DataPoint(timestamp=1000.9, value=14.0)
        algo.add_sample(p2)
        algo.add_sample(p3)
        algo.add_sample(p4)

        # Close window
        p5 = DataPoint(timestamp=2000.5, value=16.0)
        result = algo.add_sample(p5)

        assert result is not None
        assert result.value == 8.0

    def test_max_method(self):
        """Test storing maximum value in window"""
        algo = BoxCarCompression({"time_window_ms": 1000, "store_method": "max"})

        p1 = DataPoint(timestamp=1000.0, value=10.0)
        algo.add_sample(p1)

        p2 = DataPoint(timestamp=1000.3, value=12.0)
        p3 = DataPoint(timestamp=1000.6, value=18.0)  # Max
        p4 = DataPoint(timestamp=1000.9, value=14.0)
        algo.add_sample(p2)
        algo.add_sample(p3)
        algo.add_sample(p4)

        # Close window
        p5 = DataPoint(timestamp=2000.5, value=16.0)
        result = algo.add_sample(p5)

        assert result is not None
        assert result.value == 18.0

    def test_change_threshold_trigger(self):
        """Test immediate storage on large change"""
        algo = BoxCarCompression({
            "time_window_ms": 10000,  # Long window
            "change_threshold": 5.0,
            "store_method": "last"
        })

        p1 = DataPoint(timestamp=1000.0, value=10.0)
        algo.add_sample(p1)  # First

        # Small change - not triggered
        p2 = DataPoint(timestamp=1001.0, value=12.0)
        assert algo.add_sample(p2) is None

        # Large change - should trigger immediate storage
        p3 = DataPoint(timestamp=1002.0, value=18.0)  # Change of 6 from p2
        result = algo.add_sample(p3)
        assert result is not None
        assert result.value == 18.0

        stats = algo.get_statistics()
        assert stats["change_triggered_stores"] == 1

    def test_flush(self):
        """Test flushing pending window"""
        algo = BoxCarCompression({"time_window_ms": 1000, "store_method": "last"})

        p1 = DataPoint(timestamp=1000.0, value=10.0)
        p2 = DataPoint(timestamp=1000.5, value=12.0)

        algo.add_sample(p1)
        algo.add_sample(p2)

        # Flush without closing window
        flushed = algo.flush()

        assert len(flushed) == 1
        assert flushed[0].value == 12.0

    def test_statistics(self):
        """Test compression statistics"""
        algo = BoxCarCompression({"time_window_ms": 1000, "store_method": "average"})

        for i in range(20):
            p = DataPoint(timestamp=1000.0 + i * 100.0, value=10.0 + i)
            algo.add_sample(p)

        stats = algo.get_statistics()

        assert stats["algorithm"] == "boxcar"
        assert stats["samples_received"] == 20
        assert "windows_completed" in stats
        assert "compression_ratio_percent" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
