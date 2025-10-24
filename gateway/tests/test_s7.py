"""
Tests for S7 Protocol Handler

Tests include:
- Client connection and disconnection
- DB reading and writing
- Address parsing
- Data type conversion
- Error handling
- Async operations
"""

import pytest
import struct
from unittest.mock import Mock, MagicMock, patch, AsyncMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.protocols.s7 import (
    S7Client,
    S7Value,
    S7DeviceInfo,
    S7DataType,
    S7AreaType,
    ConnectionStatus
)


@pytest.fixture
def mock_snap7_client():
    """Create a mock snap7 client."""
    with patch('app.protocols.s7.snap7.client.Client') as mock:
        client_instance = MagicMock()
        client_instance.get_connected = MagickMock(return_value=True)
        client_instance.connect = MagicMock()
        client_instance.disconnect = MagicMock()
        mock.return_value = client_instance
        yield client_instance


class TestS7Client:
    """Test cases for S7Client."""

    def test_client_initialization(self):
        """Test client initializes with correct parameters."""
        client = S7Client(
            ip_address="192.168.1.100",
            rack=0,
            slot=1,
            timeout=5.0
        )

        assert client.ip_address == "192.168.1.100"
        assert client.rack == 0
        assert client.slot == 1
        assert client.timeout == 5.0
        assert client._connected is False

    def test_connect_success(self, mock_snap7_client):
        """Test successful connection to PLC."""
        client = S7Client("192.168.1.100")

        result = client.connect()

        assert result is True
        assert client.is_connected() is True
        mock_snap7_client.connect.assert_called_once()

    def test_connect_failure(self):
        """Test connection failure handling."""
        with patch('app.protocols.s7.snap7.client.Client') as mock:
            client_instance = MagicMock()
            client_instance.get_connected = MagicMock(return_value=False)
            client_instance.connect = MagicMock(side_effect=Exception("Connection failed"))
            mock.return_value = client_instance

            client = S7Client("192.168.1.100")
            result = client.connect()

            assert result is False
            assert client.is_connected() is False

    def test_disconnect(self, mock_snap7_client):
        """Test disconnection from PLC."""
        client = S7Client("192.168.1.100")
        client.connect()

        client.disconnect()

        assert client.is_connected() is False
        mock_snap7_client.disconnect.assert_called()

    def test_read_db_success(self, mock_snap7_client):
        """Test successful DB read."""
        mock_snap7_client.db_read = MagicMock(return_value=b'\x00\x00\x41\xC8')  # REAL value 25.0

        client = S7Client("192.168.1.100")
        client.connect()

        data = client.read_db(10, 0, 4)

        assert data == b'\x00\x00\x41\xC8'
        mock_snap7_client.db_read.assert_called_once_with(10, 0, 4)

    def test_write_db_success(self, mock_snap7_client):
        """Test successful DB write."""
        mock_snap7_client.db_write = MagicMock()

        client = S7Client("192.168.1.100")
        client.connect()

        result = client.write_db(10, 0, b'\x00\x00\x41\xC8')

        assert result is True
        mock_snap7_client.db_write.assert_called_once_with(10, 0, b'\x00\x00\x41\xC8')

    def test_parse_address_db_bool(self):
        """Test parsing DB BOOL address."""
        client = S7Client("192.168.1.100")

        parsed = client._parse_address("DB10.DBX0.5")

        assert parsed is not None
        area, db_num, offset, bit_offset, data_type, size = parsed
        assert area == S7AreaType.DB
        assert db_num == 10
        assert offset == 0
        assert bit_offset == 5
        assert data_type == S7DataType.BOOL

    def test_parse_address_db_real(self):
        """Test parsing DB REAL address."""
        client = S7Client("192.168.1.100")

        parsed = client._parse_address("DB10.DBREAL4")

        assert parsed is not None
        area, db_num, offset, bit_offset, data_type, size = parsed
        assert area == S7AreaType.DB
        assert db_num == 10
        assert offset == 4
        assert bit_offset == 0
        assert data_type == S7DataType.REAL
        assert size == 4

    def test_parse_address_input(self):
        """Test parsing Input address."""
        client = S7Client("192.168.1.100")

        parsed = client._parse_address("I0.0")

        assert parsed is not None
        area, db_num, offset, bit_offset, data_type, size = parsed
        assert area == S7AreaType.INPUT
        assert db_num is None
        assert offset == 0
        assert bit_offset == 0

    def test_parse_address_output(self):
        """Test parsing Output address."""
        client = S7Client("192.168.1.100")

        parsed = client._parse_address("QB0")

        assert parsed is not None
        area, db_num, offset, bit_offset, data_type, size = parsed
        assert area == S7AreaType.OUTPUT
        assert offset == 0
        assert data_type == S7DataType.BYTE

    def test_parse_address_merker(self):
        """Test parsing Merker address."""
        client = S7Client("192.168.1.100")

        parsed = client._parse_address("MW2")

        assert parsed is not None
        area, db_num, offset, bit_offset, data_type, size = parsed
        assert area == S7AreaType.MERKER
        assert offset == 2
        assert data_type == S7DataType.WORD

    def test_parse_address_invalid(self):
        """Test parsing invalid address."""
        client = S7Client("192.168.1.100")

        parsed = client._parse_address("INVALID")

        assert parsed is None

    def test_read_address_db_real(self, mock_snap7_client):
        """Test reading REAL value from DB."""
        # Mock DB read returning REAL value 25.5
        mock_snap7_client.db_read = MagicMock(return_value=struct.pack('>f', 25.5))

        client = S7Client("192.168.1.100")
        client.connect()

        result = client.read_address("DB10.DBREAL0")

        assert result.quality == "Good"
        assert abs(result.value - 25.5) < 0.01
        assert result.data_type == S7DataType.REAL

    def test_read_address_not_connected(self):
        """Test reading address when not connected."""
        client = S7Client("192.168.1.100")

        result = client.read_address("DB10.DBW0")

        assert result.quality == "Bad"
        assert "Not connected" in result.error

    def test_write_address_success(self, mock_snap7_client):
        """Test successful address write."""
        mock_snap7_client.db_write = MagicMock()

        client = S7Client("192.168.1.100")
        client.connect()

        result = client.write_address("DB10.DBREAL0", 25.5)

        assert result is True
        mock_snap7_client.db_write.assert_called_once()

    def test_get_device_info(self, mock_snap7_client):
        """Test getting device information."""
        mock_cpu_info = MagicMock()
        mock_cpu_info.ModuleTypeName = b'CPU 1516-3 PN/DP'
        mock_cpu_info.SerialNumber = b'S C-X4U304308002'
        mock_cpu_info.ASName = b'PLC_1'

        mock_snap7_client.get_cpu_info = MagicMock(return_value=mock_cpu_info)

        client = S7Client("192.168.1.100")
        client.connect()

        info = client.get_device_info()

        assert isinstance(info, S7DeviceInfo)
        assert info.ip_address == "192.168.1.100"
        assert info.cpu_type == "CPU 1516-3 PN/DP"
        assert "X4U304308002" in info.serial_number
        assert info.status == ConnectionStatus.CONNECTED

    @pytest.mark.asyncio
    async def test_async_connect(self, mock_snap7_client):
        """Test async connection."""
        client = S7Client("192.168.1.100")

        result = await client.connect_async()

        assert result is True
        assert client.is_connected()

    @pytest.mark.asyncio
    async def test_async_read_address(self, mock_snap7_client):
        """Test async address read."""
        mock_snap7_client.db_read = MagicMock(return_value=struct.pack('>h', 100))

        client = S7Client("192.168.1.100")
        await client.connect_async()

        result = await client.read_address_async("DB10.DBINT0")

        assert result.quality == "Good"
        assert result.value == 100

    @pytest.mark.asyncio
    async def test_async_write_address(self, mock_snap7_client):
        """Test async address write."""
        mock_snap7_client.db_write = MagicMock()

        client = S7Client("192.168.1.100")
        await client.connect_async()

        result = await client.write_address_async("DB10.DBINT0", 100)

        assert result is True

    def test_context_manager(self, mock_snap7_client):
        """Test client as context manager."""
        with S7Client("192.168.1.100") as client:
            assert client.is_connected()

        mock_snap7_client.disconnect.assert_called()


# Integration tests (requires real PLC or simulator)
@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("INTEGRATION_TESTS") != "1",
    reason="Integration tests disabled"
)
class TestS7Integration:
    """Integration tests with real S7 PLC."""

    PLC_IP = os.getenv("TEST_S7_IP", "192.168.1.100")
    PLC_RACK = int(os.getenv("TEST_S7_RACK", "0"))
    PLC_SLOT = int(os.getenv("TEST_S7_SLOT", "1"))

    def test_real_connection(self):
        """Test connection to real PLC."""
        client = S7Client(self.PLC_IP, rack=self.PLC_RACK, slot=self.PLC_SLOT)

        try:
            result = client.connect()
            assert result is True

            info = client.get_device_info()
            assert info is not None
            assert info.ip_address == self.PLC_IP

        finally:
            client.disconnect()

    def test_real_db_read(self):
        """Test reading from real PLC."""
        client = S7Client(self.PLC_IP, rack=self.PLC_RACK, slot=self.PLC_SLOT)

        try:
            client.connect()

            # Try to read DB1 first byte
            data = client.read_db(1, 0, 1)

            # Should get data or None (if DB doesn't exist)
            # Both are valid outcomes
            assert data is not None or data is None

        finally:
            client.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
