"""
Tests for Time Series Service

Tests time-series data querying, aggregation, downsampling, and statistics.
"""
import pytest
from datetime import datetime, timedelta

from app.services.timeseries_service import (
    TimeSeriesService,
    TimeSeriesQuery,
    AggregationFunction,
    DataPoint,
    TagSeries
)


@pytest.fixture
def timeseries_service():
    """Create time series service instance"""
    return TimeSeriesService()


class TestDataPoint:
    """Test DataPoint model"""

    def test_datapoint_creation(self):
        """Test creating a data point"""
        timestamp = datetime.now()
        dp = DataPoint(timestamp=timestamp, value=42.5, quality="Good")

        assert dp.timestamp == timestamp
        assert dp.value == 42.5
        assert dp.quality == "Good"

    def test_datapoint_to_dict(self):
        """Test converting data point to dictionary"""
        timestamp = datetime.now()
        dp = DataPoint(timestamp=timestamp, value=42.5, quality="Good")

        result = dp.to_dict()

        assert result["timestamp"] == timestamp.isoformat()
        assert result["value"] == 42.5
        assert result["quality"] == "Good"


class TestTagSeries:
    """Test TagSeries model"""

    def test_tagseries_creation(self):
        """Test creating a tag series"""
        series = TagSeries(tag_id="tag1", tag_name="Temperature")

        assert series.tag_id == "tag1"
        assert series.tag_name == "Temperature"
        assert series.data_points == []
        assert series.statistics is None

    def test_tagseries_to_dict(self):
        """Test converting tag series to dictionary"""
        timestamp = datetime.now()
        dp = DataPoint(timestamp=timestamp, value=42.5, quality="Good")

        series = TagSeries(
            tag_id="tag1",
            tag_name="Temperature",
            data_points=[dp],
            statistics={"min": 40.0, "max": 45.0, "avg": 42.5}
        )

        result = series.to_dict()

        assert result["tag_id"] == "tag1"
        assert result["tag_name"] == "Temperature"
        assert result["count"] == 1
        assert len(result["data_points"]) == 1
        assert result["statistics"]["min"] == 40.0


class TestTimeSeriesService:
    """Test Time Series Service"""

    @pytest.mark.asyncio
    async def test_query_tag_data(self, timeseries_service):
        """Test querying tag data"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        result = await timeseries_service.query_tag_data(
            tag_id="tag1",
            start_time=start_time,
            end_time=end_time
        )

        assert isinstance(result, TagSeries)
        assert result.tag_id == "tag1"
        assert len(result.data_points) > 0
        assert result.statistics is not None

    @pytest.mark.asyncio
    async def test_query_tag_data_with_aggregation(self, timeseries_service):
        """Test querying tag data with aggregation"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        result = await timeseries_service.query_tag_data(
            tag_id="tag1",
            start_time=start_time,
            end_time=end_time,
            aggregation=AggregationFunction.MEAN,
            interval="5m"
        )

        assert isinstance(result, TagSeries)
        assert result.tag_id == "tag1"

    @pytest.mark.asyncio
    async def test_query_tag_data_with_limit(self, timeseries_service):
        """Test querying tag data with limit"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        result = await timeseries_service.query_tag_data(
            tag_id="tag1",
            start_time=start_time,
            end_time=end_time,
            limit=100
        )

        assert isinstance(result, TagSeries)
        assert len(result.data_points) <= 100

    @pytest.mark.asyncio
    async def test_query_multiple_tags(self, timeseries_service):
        """Test querying multiple tags"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        query = TimeSeriesQuery(
            tag_ids=["tag1", "tag2", "tag3"],
            start_time=start_time,
            end_time=end_time
        )

        results = await timeseries_service.query_multiple_tags(query)

        assert len(results) == 3
        assert all(isinstance(r, TagSeries) for r in results)

    @pytest.mark.asyncio
    async def test_query_latest_values(self, timeseries_service):
        """Test querying latest values"""
        result = await timeseries_service.query_latest_values(
            tag_ids=["tag1", "tag2"]
        )

        assert len(result) == 2
        assert "tag1" in result
        assert "tag2" in result
        assert isinstance(result["tag1"], DataPoint)

    @pytest.mark.asyncio
    async def test_downsample_data(self, timeseries_service):
        """Test downsampling data"""
        start_time = datetime.now() - timedelta(days=1)
        end_time = datetime.now()

        result = await timeseries_service.downsample_data(
            tag_id="tag1",
            start_time=start_time,
            end_time=end_time,
            max_points=100
        )

        assert isinstance(result, TagSeries)
        assert len(result.data_points) <= 100

    @pytest.mark.asyncio
    async def test_calculate_statistics(self, timeseries_service):
        """Test calculating statistics"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        result = await timeseries_service.calculate_statistics(
            tag_id="tag1",
            start_time=start_time,
            end_time=end_time
        )

        assert isinstance(result, dict)
        assert "min" in result
        assert "max" in result
        assert "mean" in result
        assert "median" in result
        assert "stddev" in result
        assert "count" in result

    @pytest.mark.asyncio
    async def test_export_to_csv(self, timeseries_service):
        """Test exporting tag series to CSV"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        tag_series = await timeseries_service.query_tag_data(
            tag_id="tag1",
            start_time=start_time,
            end_time=end_time,
            limit=10
        )

        csv_output = await timeseries_service.export_to_csv(
            tag_series=tag_series,
            include_quality=True
        )

        assert isinstance(csv_output, str)
        assert "timestamp,value,quality" in csv_output
        assert len(csv_output.split("\n")) > 1

    @pytest.mark.asyncio
    async def test_export_multiple_to_csv(self, timeseries_service):
        """Test exporting multiple tag series to CSV"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        query = TimeSeriesQuery(
            tag_ids=["tag1", "tag2"],
            start_time=start_time,
            end_time=end_time,
            limit=10
        )

        tag_series_list = await timeseries_service.query_multiple_tags(query)

        csv_output = await timeseries_service.export_multiple_to_csv(
            tag_series_list=tag_series_list
        )

        assert isinstance(csv_output, str)
        assert "timestamp" in csv_output
        assert len(csv_output.split("\n")) > 1


class TestMockDataGeneration:
    """Test mock data generation"""

    def test_generate_mock_data(self, timeseries_service):
        """Test generating mock data"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        data_points = timeseries_service._generate_mock_data(
            start_time=start_time,
            end_time=end_time,
            num_points=100
        )

        assert len(data_points) == 100
        assert all(isinstance(dp, DataPoint) for dp in data_points)
        assert data_points[0].timestamp == start_time

    def test_mock_data_values(self, timeseries_service):
        """Test mock data value ranges"""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        data_points = timeseries_service._generate_mock_data(
            start_time=start_time,
            end_time=end_time,
            num_points=100
        )

        values = [dp.value for dp in data_points]

        # Check values are in reasonable range (sinusoidal pattern)
        assert min(values) >= 10  # Base of 50 +/- 30 +/- 2
        assert max(values) <= 90

    def test_mock_data_timestamps(self, timeseries_service):
        """Test mock data timestamp spacing"""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        data_points = timeseries_service._generate_mock_data(
            start_time=start_time,
            end_time=end_time,
            num_points=10
        )

        # Check timestamps are evenly spaced
        timestamps = [dp.timestamp for dp in data_points]
        assert timestamps[0] == start_time
        assert timestamps[-1] == end_time

        # Check spacing is consistent
        deltas = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        if len(deltas) > 1:
            # All deltas should be approximately equal
            avg_delta = sum((d.total_seconds() for d in deltas), 0) / len(deltas)
            for delta in deltas:
                assert abs(delta.total_seconds() - avg_delta) < 1  # Within 1 second


class TestAggregationFunction:
    """Test aggregation function enum"""

    def test_aggregation_functions(self):
        """Test aggregation function values"""
        assert AggregationFunction.MEAN == "mean"
        assert AggregationFunction.MIN == "min"
        assert AggregationFunction.MAX == "max"
        assert AggregationFunction.SUM == "sum"
        assert AggregationFunction.COUNT == "count"
        assert AggregationFunction.FIRST == "first"
        assert AggregationFunction.LAST == "last"
        assert AggregationFunction.STDDEV == "stddev"
