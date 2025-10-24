"""
Tests for EtherNet/IP Protocol Handler

Tests include:
- Client connection and disconnection
- Tag reading (single and batch)
- Tag writing
- Device info retrieval
- Error handling
- Async operations
- Connection pooling
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import List

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.protocols.ethernet_ip import (
    EtherNetIPClient,
    TagValue,
    DeviceInfo,
    ConnectionStatus,
    EtherNetIPConnectionPool,
    EtherNetIPDataType
)


@pytest.fixture
def mock_plc():
    """Create a mock PLC driver."""
    with patch('app.protocols.ethernet_ip.LogixDriver') as mock:
        plc_instance = MagicMock()
        plc_instance.connected = True
        plc_instance.open = MagicMock()
        plc_instance.close = MagicMock()
        mock.return_value = plc_instance
        yield plc_instance


class TestEtherNetIPClient:
    """Test cases for EtherNetIPClient."""

    def test_client_initialization(self):
        """Test client initializes with correct parameters."""
        client = EtherNetIPClient(
            ip_address="192.168.1.100",
            slot=0,
            timeout=5.0
        )

        assert client.ip_address == "192.168.1.100"
        assert client.slot == 0
        assert client.timeout == 5.0
        assert client._connected is False

    def test_connect_success(self, mock_plc):
        """Test successful connection to PLC."""
        client = EtherNetIPClient("192.168.1.100")

        result = client.connect()

        assert result is True
        assert client.is_connected() is True
        mock_plc.open.assert_called_once()

    def test_connect_failure(self):
        """Test connection failure handling."""
        with patch('app.protocols.ethernet_ip.LogixDriver') as mock:
            plc_instance = MagicMock()
            plc_instance.connected = False
            plc_instance.open = MagicMock(side_effect=Exception("Connection failed"))
            mock.return_value = plc_instance

            client = EtherNetIPClient("192.168.1.100")
            result = client.connect()

            assert result is False
            assert client.is_connected() is False

    def test_disconnect(self, mock_plc):
        """Test disconnection from PLC."""
        client = EtherNetIPClient("192.168.1.100")
        client.connect()

        client.disconnect()

        assert client.is_connected() is False
        mock_plc.close.assert_called()

    def test_read_tag_success(self, mock_plc):
        """Test successful tag read."""
        # Setup mock tag response
        mock_tag = MagicMock()
        mock_tag.tag = "Temperature"
        mock_tag.value = 25.5
        mock_tag.type = "REAL"
        mock_tag.error = None

        mock_plc.read = MagicMock(return_value=mock_tag)

        client = EtherNetIPClient("192.168.1.100")
        client.connect()

        result = client.read_tag("Temperature")

        assert isinstance(result, TagValue)
        assert result.tag_name == "Temperature"
        assert result.value == 25.5
        assert result.data_type == "REAL"
        assert result.quality == "Good"
        assert result.error is None

    def test_read_tag_error(self, mock_plc):
        """Test tag read with error."""
        mock_tag = MagicMock()
        mock_tag.tag = "InvalidTag"
        mock_tag.value = None
        mock_tag.error = "Tag not found"

        mock_plc.read = MagicMock(return_value=mock_tag)

        client = EtherNetIPClient("192.168.1.100")
        client.connect()

        result = client.read_tag("InvalidTag")

        assert result.quality == "Bad"
        assert result.error == "Tag not found"
        assert result.value is None

    def test_read_tag_not_connected(self):
        """Test reading tag when not connected."""
        client = EtherNetIPClient("192.168.1.100")

        result = client.read_tag("Temperature")

        assert result.quality == "Bad"
        assert "Not connected" in result.error

    def test_read_tags_batch(self, mock_plc):
        """Test batch tag reading."""
        mock_tags = [
            MagicMock(tag="Tag1", value=10, type="INT", error=None),
            MagicMock(tag="Tag2", value=20.5, type="REAL", error=None),
            MagicMock(tag="Tag3", value=True, type="BOOL", error=None)
        ]

        mock_plc.read = MagicMock(return_value=mock_tags)

        client = EtherNetIPClient("192.168.1.100")
        client.connect()

        results = client.read_tags(["Tag1", "Tag2", "Tag3"])

        assert len(results) == 3
        assert all(r.quality == "Good" for r in results)
        assert results[0].value == 10
        assert results[1].value == 20.5
        assert results[2].value is True

    def test_write_tag_success(self, mock_plc):
        """Test successful tag write."""
        mock_result = MagicMock()
        mock_result.error = None

        mock_plc.write = MagicMock(return_value=mock_result)

        client = EtherNetIPClient("192.168.1.100")
        client.connect()

        result = client.write_tag("Setpoint", 50.0)

        assert result is True
        mock_plc.write.assert_called_once()

    def test_write_tag_error(self, mock_plc):
        """Test tag write with error."""
        mock_result = MagicMock()
        mock_result.error = "Access denied"

        mock_plc.write = MagicMock(return_value=mock_result)

        client = EtherNetIPClient("192.168.1.100")
        client.connect()

        result = client.write_tag("Setpoint", 50.0)

        assert result is False

    def test_write_tags_batch(self, mock_plc):
        """Test batch tag writing."""
        mock_results = [
            MagicMock(tag="Tag1", error=None),
            MagicMock(tag="Tag2", error=None),
            MagicMock(tag="Tag3", error="Access denied")
        ]

        mock_plc.write = MagicMock(return_value=mock_results)

        client = EtherNetIPClient("192.168.1.100")
        client.connect()

        tag_values = {
            "Tag1": 10,
            "Tag2": 20.5,
            "Tag3": True
        }

        results = client.write_tags(tag_values)

        assert results["Tag1"] is True
        assert results["Tag2"] is True
        assert results["Tag3"] is False

    def test_get_device_info(self, mock_plc):
        """Test getting device information."""
        mock_info = {
            'vendor': 'Rockwell Automation',
            'name': 'CompactLogix',
            'serial': 123456,
            'revision_major': 20,
            'revision_minor': 11,
            'product_type': 'Programmable Logic Controller'
        }

        mock_plc.get_plc_info = MagicMock(return_value=mock_info)

        client = EtherNetIPClient("192.168.1.100")
        client.connect()

        info = client.get_device_info()

        assert isinstance(info, DeviceInfo)
        assert info.ip_address == "192.168.1.100"
        assert info.vendor == "Rockwell Automation"
        assert info.product_name == "CompactLogix"
        assert info.serial_number == "123456"
        assert info.revision == "20.11"

    @pytest.mark.asyncio
    async def test_async_connect(self, mock_plc):
        """Test async connection."""
        client = EtherNetIPClient("192.168.1.100")

        result = await client.connect_async()

        assert result is True
        assert client.is_connected()

    @pytest.mark.asyncio
    async def test_async_read_tag(self, mock_plc):
        """Test async tag read."""
        mock_tag = MagicMock()
        mock_tag.tag = "Temperature"
        mock_tag.value = 25.5
        mock_tag.type = "REAL"
        mock_tag.error = None

        mock_plc.read = MagicMock(return_value=mock_tag)

        client = EtherNetIPClient("192.168.1.100")
        await client.connect_async()

        result = await client.read_tag_async("Temperature")

        assert result.value == 25.5
        assert result.quality == "Good"

    @pytest.mark.asyncio
    async def test_async_write_tag(self, mock_plc):
        """Test async tag write."""
        mock_result = MagicMock()
        mock_result.error = None

        mock_plc.write = MagicMock(return_value=mock_result)

        client = EtherNetIPClient("192.168.1.100")
        await client.connect_async()

        result = await client.write_tag_async("Setpoint", 50.0)

        assert result is True

    def test_context_manager(self, mock_plc):
        """Test client as context manager."""
        with EtherNetIPClient("192.168.1.100") as client:
            assert client.is_connected()

        mock_plc.close.assert_called()


class TestEtherNetIPConnectionPool:
    """Test cases for connection pool."""

    @pytest.mark.asyncio
    async def test_pool_get_client(self, mock_plc):
        """Test getting client from pool."""
        pool = EtherNetIPConnectionPool(max_connections_per_device=3)

        client = await pool.get_client("192.168.1.100", slot=0)

        assert client is not None
        assert client.ip_address == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_pool_reuse_connection(self, mock_plc):
        """Test connection reuse in pool."""
        pool = EtherNetIPConnectionPool(max_connections_per_device=1)

        client1 = await pool.get_client("192.168.1.100")
        client2 = await pool.get_client("192.168.1.100")

        # Should return the same client
        assert client1 is client2

    @pytest.mark.asyncio
    async def test_pool_close_all(self, mock_plc):
        """Test closing all connections in pool."""
        pool = EtherNetIPConnectionPool()

        await pool.get_client("192.168.1.100")
        await pool.get_client("192.168.1.101")

        await pool.close_all()

        assert len(pool._pools) == 0


# Integration test (requires real PLC or simulator)
@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("INTEGRATION_TESTS") != "1",
    reason="Integration tests disabled"
)
class TestEtherNetIPIntegration:
    """Integration tests with real PLC."""

    PLC_IP = os.getenv("TEST_PLC_IP", "192.168.1.100")

    def test_real_connection(self):
        """Test connection to real PLC."""
        client = EtherNetIPClient(self.PLC_IP)

        try:
            result = client.connect()
            assert result is True

            info = client.get_device_info()
            assert info is not None
            assert info.ip_address == self.PLC_IP

        finally:
            client.disconnect()

    def test_real_tag_read(self):
        """Test reading from real PLC."""
        client = EtherNetIPClient(self.PLC_IP)

        try:
            client.connect()

            # Read a known tag (adjust to your PLC)
            # result = client.read_tag("YourTagName")
            # assert result.quality == "Good"

        finally:
            client.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
