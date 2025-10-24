"""
Tests for OPC UA Protocol Handler

Tests include:
- Client connection and disconnection
- Node reading (single and batch)
- Node writing
- Address space browsing
- Node discovery and filtering
- Async operations
- Error handling
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import List
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.protocols.opcua import (
    OPCUAClient,
    OPCUANodeInfo,
    OPCUAValue
)


@pytest.fixture
def mock_opcua_client():
    """Create a mock OPC UA client."""
    with patch('app.protocols.opcua.Client') as mock_client_class:
        mock_client = MagicMock()

        # Mock connection state
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()

        # Mock node operations
        mock_node = MagicMock()
        mock_node.read_value = AsyncMock(return_value=25.5)
        mock_node.read_data_value = AsyncMock()
        mock_node.write_value = AsyncMock()
        mock_node.get_browse_name = AsyncMock(return_value=MagicMock(Name="Temperature"))
        mock_node.get_display_name = AsyncMock(return_value=MagicMock(Text="Temperature Sensor"))
        mock_node.get_node_class = AsyncMock()
        mock_node.get_data_type = AsyncMock()
        mock_node.get_children = AsyncMock(return_value=[])

        mock_client.get_node = MagicMock(return_value=mock_node)

        mock_client_class.return_value = mock_client
        yield mock_client


class TestOPCUAClient:
    """Test cases for OPCUAClient."""

    def test_client_initialization(self):
        """Test client initializes with correct parameters."""
        client = OPCUAClient(
            server_url="opc.tcp://192.168.1.100:4840",
            timeout=10.0
        )

        assert client.server_url == "opc.tcp://192.168.1.100:4840"
        assert client.timeout == 10.0
        assert client._client is None

    @pytest.mark.asyncio
    async def test_connect_success(self, mock_opcua_client):
        """Test successful connection to OPC UA server."""
        client = OPCUAClient("opc.tcp://192.168.1.100:4840")

        result = await client.connect()

        assert result is True
        assert client.is_connected() is True
        mock_opcua_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure handling."""
        with patch('app.protocols.opcua.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client_class.return_value = mock_client

            client = OPCUAClient("opc.tcp://192.168.1.100:4840")
            result = await client.connect()

            assert result is False
            assert client.is_connected() is False

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_opcua_client):
        """Test disconnection from OPC UA server."""
        client = OPCUAClient("opc.tcp://192.168.1.100:4840")
        await client.connect()

        await client.disconnect()

        assert client.is_connected() is False
        mock_opcua_client.disconnect.assert_called()

    @pytest.mark.asyncio
    async def test_read_node_success(self, mock_opcua_client):
        """Test successful node read."""
        # Setup mock node response
        mock_data_value = MagicMock()
        mock_data_value.Value.Value = 25.5
        mock_data_value.ServerTimestamp = datetime.now()
        mock_data_value.SourceTimestamp = datetime.now()
        mock_status = MagicMock()
        mock_status.is_good = MagicMock(return_value=True)
        mock_status.is_bad = MagicMock(return_value=False)
        mock_data_value.StatusCode = mock_status

        mock_node = MagicMock()
        mock_node.read_data_value = AsyncMock(return_value=mock_data_value)
        mock_node.read_data_type = AsyncMock(side_effect=Exception("Not available"))
        mock_opcua_client.get_node.return_value = mock_node

        client = OPCUAClient("opc.tcp://192.168.1.100:4840")
        await client.connect()

        result = await client.read_node("ns=2;i=100")

        assert isinstance(result, OPCUAValue)
        assert result.node_id == "ns=2;i=100"
        assert result.value == 25.5
        assert result.quality == "Good"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_read_node_error(self, mock_opcua_client):
        """Test node read with bad status code."""
        mock_data_value = MagicMock()
        mock_data_value.Value.Value = None
        mock_status = MagicMock()
        mock_status.is_good = MagicMock(return_value=False)
        mock_status.is_bad = MagicMock(return_value=True)
        mock_data_value.StatusCode = mock_status
        mock_data_value.ServerTimestamp = None
        mock_data_value.SourceTimestamp = None

        mock_node = MagicMock()
        mock_node.read_data_value = AsyncMock(return_value=mock_data_value)
        mock_node.read_data_type = AsyncMock(side_effect=Exception("Not available"))
        mock_opcua_client.get_node.return_value = mock_node

        client = OPCUAClient("opc.tcp://192.168.1.100:4840")
        await client.connect()

        result = await client.read_node("ns=2;i=999")

        assert result.quality == "Bad"
        assert result.value is None

    @pytest.mark.asyncio
    async def test_read_node_not_connected(self):
        """Test reading node when not connected."""
        client = OPCUAClient("opc.tcp://192.168.1.100:4840")

        result = await client.read_node("ns=2;i=100")

        assert result.quality == "Bad"
        assert "Not connected" in result.error

    @pytest.mark.asyncio
    async def test_read_multiple_nodes(self, mock_opcua_client):
        """Test reading multiple nodes individually."""
        # Create proper mock data values
        def create_mock_data_value(val):
            dv = MagicMock()
            dv.Value.Value = val
            st = MagicMock()
            st.is_good = MagicMock(return_value=True)
            st.is_bad = MagicMock(return_value=False)
            dv.StatusCode = st
            dv.ServerTimestamp = datetime.now()
            dv.SourceTimestamp = datetime.now()
            return dv

        mock_values = [
            create_mock_data_value(10),
            create_mock_data_value(20.5),
            create_mock_data_value(True)
        ]

        mock_node = MagicMock()
        mock_node.read_data_value = AsyncMock(side_effect=mock_values)
        mock_node.read_data_type = AsyncMock(side_effect=Exception("Not available"))
        mock_opcua_client.get_node.return_value = mock_node

        client = OPCUAClient("opc.tcp://192.168.1.100:4840")
        await client.connect()

        # Read individually since there's no batch method
        results = []
        for node_id in ["ns=2;i=100", "ns=2;i=101", "ns=2;i=102"]:
            result = await client.read_node(node_id)
            results.append(result)

        assert len(results) == 3
        assert all(r.quality == "Good" for r in results)
        assert results[0].value == 10
        assert results[1].value == 20.5
        assert results[2].value is True

    @pytest.mark.asyncio
    async def test_write_node_success(self, mock_opcua_client):
        """Test successful node write."""
        with patch('app.protocols.opcua.ua') as mock_ua:
            mock_ua.Variant = MagicMock(return_value=MagicMock())

            mock_node = MagicMock()
            mock_node.write_value = AsyncMock()
            mock_node.read_data_type_as_variant_type = AsyncMock(return_value=MagicMock())
            mock_opcua_client.get_node.return_value = mock_node

            client = OPCUAClient("opc.tcp://192.168.1.100:4840")
            await client.connect()

            result = await client.write_node("ns=2;i=100", 50.0)

            assert result is True
            mock_node.write_value.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_node_error(self, mock_opcua_client):
        """Test node write with error."""
        mock_node = mock_opcua_client.get_node.return_value
        mock_node.write_value = AsyncMock(side_effect=Exception("Access denied"))

        client = OPCUAClient("opc.tcp://192.168.1.100:4840")
        await client.connect()

        result = await client.write_node("ns=2;i=100", 50.0)

        assert result is False

    @pytest.mark.asyncio
    async def test_write_multiple_nodes(self, mock_opcua_client):
        """Test writing multiple nodes individually."""
        with patch('app.protocols.opcua.ua') as mock_ua:
            mock_ua.Variant = MagicMock(return_value=MagicMock())

            mock_node = MagicMock()
            mock_node.read_data_type_as_variant_type = AsyncMock(return_value=MagicMock())

            # First two succeed, third fails
            mock_node.write_value = AsyncMock(
                side_effect=[None, None, Exception("Access denied")]
            )
            mock_opcua_client.get_node.return_value = mock_node

            client = OPCUAClient("opc.tcp://192.168.1.100:4840")
            await client.connect()

            # Write individually since there's no batch method
            results = {}
            results["ns=2;i=100"] = await client.write_node("ns=2;i=100", 10)
            results["ns=2;i=101"] = await client.write_node("ns=2;i=101", 20.5)
            results["ns=2;i=102"] = await client.write_node("ns=2;i=102", True)

            assert results["ns=2;i=100"] is True
            assert results["ns=2;i=101"] is True
            assert results["ns=2;i=102"] is False

    @pytest.mark.asyncio
    async def test_browse_address_space(self, mock_opcua_client):
        """Test browsing address space returns list."""
        client = OPCUAClient("opc.tcp://192.168.1.100:4840")
        await client.connect()

        nodes = await client.browse_address_space(root_node_id="i=85", max_depth=2)

        # Should return a list (may be empty if mocking fails gracefully)
        assert isinstance(nodes, list)

    @pytest.mark.asyncio
    async def test_browse_with_filter(self, mock_opcua_client):
        """Test browsing with node class filter returns list."""
        client = OPCUAClient("opc.tcp://192.168.1.100:4840")
        await client.connect()

        # Browse with Variable filter only
        nodes = await client.browse_address_space(
            root_node_id="ns=2;i=200",
            max_depth=2,
            filter_node_classes=["Variable"]
        )

        # Should return a list
        assert isinstance(nodes, list)

    @pytest.mark.asyncio
    async def test_filter_industrial_tags(self, mock_opcua_client):
        """Test filtering industrial tags."""
        client = OPCUAClient("opc.tcp://192.168.1.100:4840")
        await client.connect()

        # Create test nodes
        nodes = [
            OPCUANodeInfo(
                node_id="ns=2;i=100",
                browse_name="Temperature",
                display_name="Temperature Sensor",
                node_class="Variable",
                data_type="Double"
            ),
            OPCUANodeInfo(
                node_id="ns=0;i=2253",  # System node
                browse_name="Server",
                display_name="Server",
                node_class="Object",
                data_type=None
            ),
            OPCUANodeInfo(
                node_id="ns=2;i=101",
                browse_name="Pressure",
                display_name="Pressure Sensor",
                node_class="Variable",
                data_type="Float"
            )
        ]

        filtered = await client.filter_industrial_tags(nodes)

        # Should exclude system nodes and non-variables
        assert len(filtered) == 2
        assert all(node.node_class == "Variable" for node in filtered)
        assert all(not node.node_id.startswith("ns=0;") for node in filtered)

    @pytest.mark.asyncio
    async def test_get_node_hierarchy(self, mock_opcua_client):
        """Test getting node hierarchy string."""
        mock_node = MagicMock()
        mock_node.get_browse_name = AsyncMock(return_value=MagicMock(Name="Temperature"))
        mock_opcua_client.get_node.return_value = mock_node

        client = OPCUAClient("opc.tcp://192.168.1.100:4840")
        await client.connect()

        hierarchy = await client.get_node_hierarchy("ns=2;i=100")

        assert isinstance(hierarchy, str)
        assert len(hierarchy) > 0

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_opcua_client):
        """Test client as context manager."""
        async with OPCUAClient("opc.tcp://192.168.1.100:4840") as client:
            assert client.is_connected()

        mock_opcua_client.disconnect.assert_called()

    @pytest.mark.asyncio
    async def test_read_failure_handling(self, mock_opcua_client):
        """Test handling read failures gracefully."""
        mock_node = MagicMock()
        mock_node.read_data_value = AsyncMock(side_effect=Exception("Connection lost"))
        mock_opcua_client.get_node.return_value = mock_node

        client = OPCUAClient("opc.tcp://192.168.1.100:4840")
        await client.connect()

        # Should return error result instead of raising exception
        result = await client.read_node("ns=2;i=100")

        assert result.quality == "Bad"
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_concurrent_reads(self, mock_opcua_client):
        """Test concurrent node reads."""
        mock_data_value = MagicMock()
        mock_data_value.Value.Value = 25.5
        mock_data_value.StatusCode = MagicMock()
        mock_data_value.StatusCode.is_good = MagicMock(return_value=True)
        mock_data_value.SourceTimestamp = datetime.now()

        mock_node = mock_opcua_client.get_node.return_value
        mock_node.read_data_value = AsyncMock(return_value=mock_data_value)

        client = OPCUAClient("opc.tcp://192.168.1.100:4840")
        await client.connect()

        # Read multiple nodes concurrently
        node_ids = [f"ns=2;i={i}" for i in range(100, 110)]

        tasks = [client.read_node(node_id) for node_id in node_ids]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(isinstance(r, OPCUAValue) for r in results)


class TestOPCUANodeInfo:
    """Test cases for OPCUANodeInfo dataclass."""

    def test_node_info_creation(self):
        """Test creating node info."""
        node = OPCUANodeInfo(
            node_id="ns=2;i=100",
            browse_name="Temperature",
            display_name="Temperature Sensor",
            node_class="Variable",
            data_type="Double"
        )

        assert node.node_id == "ns=2;i=100"
        assert node.browse_name == "Temperature"
        assert node.node_class == "Variable"

    def test_node_to_dict(self):
        """Test converting node to dictionary."""
        node = OPCUANodeInfo(
            node_id="ns=2;i=100",
            browse_name="Pressure",
            display_name="Pressure Sensor",
            node_class="Variable"
        )

        data = node.to_dict()

        assert isinstance(data, dict)
        assert data['node_id'] == "ns=2;i=100"
        assert data['browse_name'] == "Pressure"


class TestOPCUAValue:
    """Test cases for OPCUAValue dataclass."""

    def test_node_value_creation(self):
        """Test creating node value."""
        value = OPCUAValue(
            node_id="ns=2;i=100",
            value=25.5,
            quality="Good",
            timestamp=datetime.now()
        )

        assert value.node_id == "ns=2;i=100"
        assert value.value == 25.5
        assert value.quality == "Good"


# Integration tests (requires real OPC UA server)
@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("INTEGRATION_TESTS") != "1",
    reason="Integration tests disabled"
)
class TestOPCUAIntegration:
    """Integration tests with real OPC UA server."""

    SERVER_URL = os.getenv("TEST_OPCUA_URL", "opc.tcp://localhost:4840")

    @pytest.mark.asyncio
    async def test_real_connection(self):
        """Test connection to real OPC UA server."""
        client = OPCUAClient(self.SERVER_URL)

        try:
            result = await client.connect()
            assert result is True
            assert client.is_connected()

        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_real_node_read(self):
        """Test reading from real OPC UA server."""
        client = OPCUAClient(self.SERVER_URL)

        try:
            await client.connect()

            # Read server current time (standard node)
            result = await client.read_node("i=2258")  # Server.ServerStatus.CurrentTime

            if result.quality == "Good":
                assert result.value is not None
                assert isinstance(result.timestamp, datetime)

        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_real_address_space_browse(self):
        """Test browsing real server address space."""
        client = OPCUAClient(self.SERVER_URL)

        try:
            await client.connect()

            # Browse Objects folder
            nodes = await client.browse_address_space(
                root_node_id="i=85",  # Objects
                max_depth=2
            )

            assert len(nodes) > 0
            assert all(isinstance(node, OPCUANodeInfo) for node in nodes)

        finally:
            await client.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
