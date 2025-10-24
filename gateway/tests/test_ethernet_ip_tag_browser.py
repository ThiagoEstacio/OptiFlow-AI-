"""
Tests for EtherNet/IP Tag Browser

Tests include:
- Tag browsing
- Tag filtering
- Tag searching
- Hierarchical structure building
- Export functionality
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, MagicMock, patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.discovery.ethernet_ip_tag_browser import (
    EtherNetIPTagBrowser,
    TagInfo,
    TagFilter,
    TagCategory
)


class TestTagInfo:
    """Test cases for TagInfo dataclass."""

    def test_tag_info_creation(self):
        """Test creating tag info."""
        tag = TagInfo(
            tag_name="Temperature",
            full_path="Program:MainRoutine.Temperature",
            data_type="REAL",
            is_array=False
        )

        assert tag.tag_name == "Temperature"
        assert tag.data_type == "REAL"
        assert tag.is_array is False

    def test_tag_to_dict(self):
        """Test converting tag to dictionary."""
        tag = TagInfo(
            tag_name="Pressure",
            full_path="Pressure",
            data_type="REAL",
            value=25.5
        )

        data = tag.to_dict()

        assert isinstance(data, dict)
        assert data['tag_name'] == "Pressure"
        assert data['value'] == 25.5


class TestTagFilter:
    """Test cases for TagFilter."""

    def test_filter_by_name_pattern(self):
        """Test filtering by name pattern."""
        tag_filter = TagFilter(name_pattern="Temp.*")

        tag1 = TagInfo(tag_name="Temperature", full_path="Temperature", data_type="REAL")
        tag2 = TagInfo(tag_name="Pressure", full_path="Pressure", data_type="REAL")

        assert tag_filter.matches(tag1) is True
        assert tag_filter.matches(tag2) is False

    def test_filter_by_data_type(self):
        """Test filtering by data type."""
        tag_filter = TagFilter(data_types=["REAL", "DINT"])

        tag1 = TagInfo(tag_name="Tag1", full_path="Tag1", data_type="REAL")
        tag2 = TagInfo(tag_name="Tag2", full_path="Tag2", data_type="BOOL")

        assert tag_filter.matches(tag1) is True
        assert tag_filter.matches(tag2) is False

    def test_filter_exclude_system(self):
        """Test excluding system tags."""
        tag_filter = TagFilter(exclude_system=True)

        tag1 = TagInfo(
            tag_name="UserTag",
            full_path="UserTag",
            data_type="REAL",
            category=TagCategory.USER_DEFINED
        )
        tag2 = TagInfo(
            tag_name="SystemTag",
            full_path="SystemTag",
            data_type="REAL",
            category=TagCategory.SYSTEM
        )

        assert tag_filter.matches(tag1) is True
        assert tag_filter.matches(tag2) is False

    def test_filter_arrays(self):
        """Test filtering arrays."""
        tag_filter = TagFilter(include_arrays=False)

        tag1 = TagInfo(tag_name="Single", full_path="Single", data_type="REAL", is_array=False)
        tag2 = TagInfo(tag_name="Array", full_path="Array", data_type="REAL", is_array=True)

        assert tag_filter.matches(tag1) is True
        assert tag_filter.matches(tag2) is False


class TestEtherNetIPTagBrowser:
    """Test cases for tag browser."""

    @pytest.fixture
    def mock_plc(self):
        """Create mock PLC with tags."""
        with patch('app.services.discovery.ethernet_ip_tag_browser.LogixDriver') as mock:
            plc_instance = MagicMock()
            plc_instance.connected = True

            # Mock tag database
            plc_instance.tags = {
                'Temperature': {
                    'data_type': 'REAL',
                    'dim': 0,
                    'dimensions': None
                },
                'Pressure': {
                    'data_type': 'REAL',
                    'dim': 0,
                    'dimensions': None
                },
                'Program:MainRoutine.Status': {
                    'data_type': 'DINT',
                    'dim': 0,
                    'dimensions': None
                },
                'MotorArray': {
                    'data_type': 'REAL',
                    'dim': 1,
                    'dimensions': [10]
                }
            }

            plc_instance.open = MagicMock()
            plc_instance.close = MagicMock()

            mock.return_value = plc_instance
            yield plc_instance

    def test_browser_initialization(self):
        """Test browser initializes correctly."""
        browser = EtherNetIPTagBrowser("192.168.1.100", slot=0)

        assert browser.ip_address == "192.168.1.100"
        assert browser.slot == 0

    def test_connect_success(self, mock_plc):
        """Test successful connection."""
        browser = EtherNetIPTagBrowser("192.168.1.100")

        result = browser.connect()

        assert result is True
        mock_plc.open.assert_called_once()

    def test_browse_tags(self, mock_plc):
        """Test browsing tags."""
        browser = EtherNetIPTagBrowser("192.168.1.100")
        browser.connect()

        tags = browser.browse_tags(include_values=False)

        assert len(tags) > 0
        assert all(isinstance(tag, TagInfo) for tag in tags)

        # Check specific tags
        tag_names = [tag.tag_name for tag in tags]
        assert 'Temperature' in tag_names
        assert 'Pressure' in tag_names

    def test_browse_tags_with_values(self, mock_plc):
        """Test browsing tags with values."""
        # Mock read method
        mock_tag_result = MagicMock()
        mock_tag_result.value = 25.5
        mock_tag_result.error = None

        mock_plc.read = MagicMock(return_value=mock_tag_result)

        browser = EtherNetIPTagBrowser("192.168.1.100")
        browser.connect()

        tags = browser.browse_tags(include_values=True)

        # Values should be populated
        assert any(tag.value is not None for tag in tags)

    def test_get_tag_details(self, mock_plc):
        """Test getting details for specific tag."""
        mock_tag_result = MagicMock()
        mock_tag_result.value = 25.5
        mock_tag_result.error = None

        mock_plc.read = MagicMock(return_value=mock_tag_result)

        browser = EtherNetIPTagBrowser("192.168.1.100")
        browser.connect()

        tag = browser.get_tag_details("Temperature", read_value=True)

        assert tag is not None
        assert tag.tag_name == "Temperature"
        assert tag.value == 25.5

    def test_filter_tags(self, mock_plc):
        """Test filtering tags."""
        browser = EtherNetIPTagBrowser("192.168.1.100")
        browser.connect()

        # Browse all tags
        all_tags = browser.browse_tags()

        # Filter by pattern
        tag_filter = TagFilter(name_pattern="Temp.*")
        filtered = browser.filter_tags(all_tags, tag_filter)

        assert len(filtered) < len(all_tags)
        assert all("Temp" in tag.tag_name for tag in filtered)

    def test_search_tags(self, mock_plc):
        """Test searching tags."""
        browser = EtherNetIPTagBrowser("192.168.1.100")
        browser.connect()

        all_tags = browser.browse_tags()

        # Search with wildcard
        results = browser.search_tags("Temp*", all_tags)

        assert len(results) > 0
        assert all("Temp" in tag.tag_name for tag in results)

    def test_hierarchical_structure(self, mock_plc):
        """Test building hierarchical structure."""
        browser = EtherNetIPTagBrowser("192.168.1.100")
        browser.connect()

        tags = browser.browse_tags()
        hierarchy = browser.get_hierarchical_structure(tags)

        assert isinstance(hierarchy, dict)
        # Should have nested structure for Program:MainRoutine.Status
        assert 'Program:MainRoutine' in hierarchy or 'Temperature' in hierarchy

    def test_export_to_json(self, mock_plc):
        """Test exporting tags to JSON."""
        browser = EtherNetIPTagBrowser("192.168.1.100")
        browser.connect()

        tags = browser.browse_tags()

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filepath = f.name

        try:
            result = browser.export_to_json(filepath, tags)

            assert result is True
            assert os.path.exists(filepath)

            # Verify JSON content
            with open(filepath, 'r') as f:
                data = json.load(f)

            assert 'device' in data
            assert 'tags' in data
            assert data['device']['ip_address'] == "192.168.1.100"

        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_export_to_csv(self, mock_plc):
        """Test exporting tags to CSV."""
        browser = EtherNetIPTagBrowser("192.168.1.100")
        browser.connect()

        tags = browser.browse_tags()

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            filepath = f.name

        try:
            result = browser.export_to_csv(filepath, tags)

            assert result is True
            assert os.path.exists(filepath)

            # Verify CSV content
            with open(filepath, 'r') as f:
                content = f.read()

            assert 'tag_name' in content
            assert 'data_type' in content

        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    @pytest.mark.asyncio
    async def test_async_browse_tags(self, mock_plc):
        """Test async tag browsing."""
        browser = EtherNetIPTagBrowser("192.168.1.100")
        browser.connect()

        tags = await browser.browse_tags_async(include_values=False)

        assert len(tags) > 0

    def test_context_manager(self, mock_plc):
        """Test browser as context manager."""
        with EtherNetIPTagBrowser("192.168.1.100") as browser:
            tags = browser.browse_tags()
            assert len(tags) > 0

        mock_plc.close.assert_called()


# Integration tests
@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("INTEGRATION_TESTS") != "1",
    reason="Integration tests disabled"
)
class TestTagBrowserIntegration:
    """Integration tests with real PLC."""

    PLC_IP = os.getenv("TEST_PLC_IP", "192.168.1.100")

    def test_real_tag_browsing(self):
        """Test browsing tags from real PLC."""
        browser = EtherNetIPTagBrowser(self.PLC_IP)

        try:
            result = browser.connect()
            assert result is True

            tags = browser.browse_tags()
            assert len(tags) > 0

            # Verify tag structure
            assert all(isinstance(tag, TagInfo) for tag in tags)

        finally:
            browser.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
