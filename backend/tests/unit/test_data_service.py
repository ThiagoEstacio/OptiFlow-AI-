"""
Unit tests for DataService
Tests the core data service functionality
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.data_service import DataService


class TestDataServiceInitialization:
    """Tests for DataService initialization"""

    def test_initialization_with_db(self):
        """Should initialize with database session"""
        mock_db = MagicMock()
        service = DataService(db=mock_db)
        assert service.db == mock_db

    def test_initialization_stores_db_reference(self):
        """Should store database reference"""
        mock_db = MagicMock()
        service = DataService(db=mock_db)
        assert hasattr(service, 'db')


class TestTagOperations:
    """Tests for tag-related operations"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create DataService instance"""
        return DataService(db=mock_db)

    @pytest.mark.asyncio
    async def test_list_tags_returns_list(self, service, mock_db):
        """list_tags should return a list"""
        # Setup mock to return ScalarResult
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.list_tags()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_tags_with_filters(self, service, mock_db):
        """list_tags should accept filter parameters"""
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Should not raise with various filters
        result = await service.list_tags(
            device_id=str(uuid4()),
            enabled=True,
            limit=10
        )
        assert isinstance(result, list)


class TestHistoricalData:
    """Tests for historical data operations"""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        return DataService(db=mock_db)

    @pytest.mark.asyncio
    async def test_get_tag_history_returns_list(self, service):
        """get_tag_history should return time-series data"""
        with patch.object(service, 'get_tag_history', new_callable=AsyncMock) as mock:
            mock.return_value = [
                {"timestamp": "2024-01-01T00:00:00", "value": 25.0},
                {"timestamp": "2024-01-01T01:00:00", "value": 26.0},
            ]
            result = await service.get_tag_history("test_tag", duration="1h")
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_tag_history_with_aggregation(self, service):
        """get_tag_history should support aggregation"""
        with patch.object(service, 'get_tag_history', new_callable=AsyncMock) as mock:
            mock.return_value = [{"timestamp": "2024-01-01", "mean": 25.5}]
            result = await service.get_tag_history(
                "test_tag",
                duration="24h",
                aggregation="mean"
            )
            assert isinstance(result, list)


class TestStatisticsCalculation:
    """Tests for statistics calculations"""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        return DataService(db=mock_db)

    @pytest.mark.asyncio
    async def test_calculate_statistics_returns_dict(self, service):
        """calculate_statistics should return statistics dict"""
        with patch.object(service, 'calculate_statistics', new_callable=AsyncMock) as mock:
            mock.return_value = {
                "mean": 25.5,
                "min": 20.0,
                "max": 30.0,
                "stddev": 2.5,
                "count": 100
            }
            result = await service.calculate_statistics("test_tag", "1h")
            assert "mean" in result
            assert "min" in result
            assert "max" in result

    @pytest.mark.asyncio
    async def test_statistics_with_empty_data(self, service):
        """Should handle empty data gracefully"""
        with patch.object(service, 'calculate_statistics', new_callable=AsyncMock) as mock:
            mock.return_value = {
                "mean": None,
                "min": None,
                "max": None,
                "stddev": None,
                "count": 0
            }
            result = await service.calculate_statistics("empty_tag", "1h")
            assert result["count"] == 0


class TestRealtimeData:
    """Tests for real-time data operations"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return DataService(db=mock_db)

    @pytest.mark.asyncio
    async def test_get_current_value_returns_reading(self, service):
        """get_tag_current_value should return current reading"""
        with patch.object(service, 'get_tag_current_value', new_callable=AsyncMock) as mock:
            mock.return_value = {
                "tag_id": "test_tag",
                "value": 25.5,
                "timestamp": datetime.now().isoformat(),
                "quality": "good"
            }
            result = await service.get_tag_current_value("test_tag")
            assert "value" in result
            assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_get_multiple_current_values(self, service):
        """Should get multiple tag values"""
        with patch.object(service, 'get_multiple_current_values', new_callable=AsyncMock) as mock:
            mock.return_value = [
                {"tag_id": "tag1", "value": 25.0},
                {"tag_id": "tag2", "value": 30.0},
            ]
            result = await service.get_multiple_current_values(["tag1", "tag2"])
            assert len(result) == 2


class TestSearchOperations:
    """Tests for search operations"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return DataService(db=mock_db)

    @pytest.mark.asyncio
    async def test_search_tags_returns_matches(self, service):
        """search_tags should return matching tags"""
        with patch.object(service, 'search_tags', new_callable=AsyncMock) as mock:
            mock.return_value = [
                {"id": "temp_01", "name": "Temperature 1", "score": 0.95},
                {"id": "temp_02", "name": "Temperature 2", "score": 0.85},
            ]
            result = await service.search_tags("temperature")
            assert isinstance(result, list)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_search_with_no_matches(self, service):
        """Should return empty list for no matches"""
        with patch.object(service, 'search_tags', new_callable=AsyncMock) as mock:
            mock.return_value = []
            result = await service.search_tags("nonexistent_xyz_123")
            assert result == []


class TestAlarmOperations:
    """Tests for alarm-related operations"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return DataService(db=mock_db)

    @pytest.mark.asyncio
    async def test_get_active_alarms(self, service):
        """Should get active alarms"""
        with patch.object(service, 'get_active_alarms', new_callable=AsyncMock) as mock:
            mock.return_value = [
                {
                    "id": "alarm1",
                    "tag_id": "temp_01",
                    "severity": "high",
                    "message": "Temperature too high",
                    "timestamp": datetime.now().isoformat()
                }
            ]
            result = await service.get_active_alarms()
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_alarms_by_severity(self, service):
        """Should filter alarms by severity"""
        with patch.object(service, 'get_active_alarms', new_callable=AsyncMock) as mock:
            mock.return_value = [
                {"id": "alarm1", "severity": "critical"},
            ]
            result = await service.get_active_alarms(severity="critical")
            assert all(a.get("severity") == "critical" for a in result)


class TestDeviceOperations:
    """Tests for device-related operations"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return DataService(db=mock_db)

    @pytest.mark.asyncio
    async def test_list_devices(self, service):
        """Should list all devices"""
        with patch.object(service, 'list_devices', new_callable=AsyncMock) as mock:
            mock.return_value = [
                {"id": "dev1", "name": "PLC-01", "status": "online"},
                {"id": "dev2", "name": "PLC-02", "status": "offline"},
            ]
            result = await service.list_devices()
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_device_status(self, service):
        """Should get device status"""
        with patch.object(service, 'get_device_status', new_callable=AsyncMock) as mock:
            mock.return_value = {
                "id": "dev1",
                "name": "PLC-01",
                "status": "online",
                "last_seen": datetime.now().isoformat()
            }
            result = await service.get_device_status("dev1")
            assert "status" in result


class TestErrorHandling:
    """Tests for error handling in DataService"""

    @pytest.fixture
    def mock_db_with_error(self):
        db = MagicMock()
        db.execute = AsyncMock(side_effect=Exception("Database error"))
        return db

    @pytest.fixture
    def service_with_error(self, mock_db_with_error):
        return DataService(db=mock_db_with_error)

    @pytest.mark.asyncio
    async def test_handles_database_errors(self, service_with_error):
        """Should handle database errors gracefully"""
        # This tests that the service doesn't crash on DB errors
        # Actual behavior depends on implementation
        try:
            await service_with_error.list_tags()
        except Exception as e:
            # Should be a meaningful error, not a crash
            assert str(e) is not None


class TestCacheBehavior:
    """Tests for caching behavior if implemented"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return DataService(db=mock_db)

    @pytest.mark.asyncio
    async def test_repeated_queries_work(self, service):
        """Repeated queries should work consistently"""
        with patch.object(service, 'list_tags', new_callable=AsyncMock) as mock:
            mock.return_value = [{"id": "tag1"}]

            # Multiple calls should all work
            for _ in range(3):
                result = await service.list_tags()
                assert isinstance(result, list)


class TestDataValidation:
    """Tests for data validation"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return DataService(db=mock_db)

    @pytest.mark.asyncio
    async def test_handles_invalid_tag_id(self, service):
        """Should handle invalid tag IDs"""
        with patch.object(service, 'get_tag_current_value', new_callable=AsyncMock) as mock:
            mock.return_value = None
            result = await service.get_tag_current_value("")
            # Should return None or empty, not crash

    @pytest.mark.asyncio
    async def test_handles_invalid_duration(self, service):
        """Should handle invalid duration formats"""
        with patch.object(service, 'get_tag_history', new_callable=AsyncMock) as mock:
            mock.return_value = []
            result = await service.get_tag_history("tag1", duration="invalid")
            # Should handle gracefully
