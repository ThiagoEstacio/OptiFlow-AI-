"""
Tests for EtherNet/IP Discovery Service

Tests include:
- Network scanning
- Device discovery
- IP range scanning
- Device probing
- Response parsing
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch
import struct

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.discovery.ethernet_ip_discovery import (
    EtherNetIPDiscoveryService,
    DiscoveredDevice
)


class TestEtherNetIPDiscoveryService:
    """Test cases for EtherNet/IP discovery."""

    def test_service_initialization(self):
        """Test service initializes correctly."""
        service = EtherNetIPDiscoveryService(timeout=3.0, max_devices=50)

        assert service.timeout == 3.0
        assert service.max_devices == 50

    def test_create_list_identity_request(self):
        """Test creation of List Identity request packet."""
        service = EtherNetIPDiscoveryService()

        packet = service._create_list_identity_request()

        assert len(packet) > 0
        assert isinstance(packet, bytes)

        # Verify command code (List Identity = 0x0063)
        command = struct.unpack('<H', packet[:2])[0]
        assert command == 0x0063

    def test_parse_identity_response_minimal(self):
        """Test parsing minimal identity response."""
        service = EtherNetIPDiscoveryService()

        # Create minimal response (just encapsulation header)
        command = 0x0063
        length = 0
        session = 0
        status = 0

        response = struct.pack(
            '<HHIIQII',
            command,
            length,
            session,
            status,
            0,  # sender context
            0   # options
        )

        device = service._parse_identity_response(response, "192.168.1.100")

        assert device is not None
        assert device.ip_address == "192.168.1.100"
        assert device.protocol == "EtherNet/IP"

    def test_parse_identity_response_invalid(self):
        """Test parsing invalid response."""
        service = EtherNetIPDiscoveryService()

        # Invalid data (too short)
        response = b'short'

        device = service._parse_identity_response(response, "192.168.1.100")

        assert device is None

    @pytest.mark.asyncio
    async def test_scan_network_mock(self):
        """Test network scanning with mocked socket."""
        service = EtherNetIPDiscoveryService(timeout=1.0)

        with patch('socket.socket') as mock_socket_class:
            mock_sock = MagicMock()

            # Mock socket operations
            mock_sock.sendto = MagicMock()
            mock_sock.recvfrom = MagicMock(
                side_effect=TimeoutError("Timeout")
            )
            mock_sock.close = MagicMock()

            mock_socket_class.return_value = mock_sock

            devices = await service.scan_network("192.168.1.0/24")

            # Should return empty list on timeout (no devices found)
            assert isinstance(devices, list)
            mock_sock.sendto.assert_called_once()
            mock_sock.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_probe_device_success(self):
        """Test probing a specific device."""
        service = EtherNetIPDiscoveryService()

        with patch('app.services.discovery.ethernet_ip_discovery.LogixDriver') as mock_driver:
            mock_plc = MagicMock()
            mock_plc.connected = True
            mock_plc.get_plc_info = MagicMock(return_value={
                'name': 'CompactLogix',
                'serial': '123456',
                'revision_major': 20,
                'revision_minor': 11
            })
            mock_plc.open = MagicMock()
            mock_plc.close = MagicMock()

            mock_driver.return_value = mock_plc

            device = await service._probe_device("192.168.1.100")

            assert device is not None
            assert device.ip_address == "192.168.1.100"
            assert device.product_name == "CompactLogix"
            assert device.vendor_name == "Rockwell Automation"

    @pytest.mark.asyncio
    async def test_probe_device_failure(self):
        """Test probing non-existent device."""
        service = EtherNetIPDiscoveryService()

        with patch('app.services.discovery.ethernet_ip_discovery.LogixDriver') as mock_driver:
            mock_driver.side_effect = Exception("Connection failed")

            device = await service._probe_device("192.168.1.200")

            assert device is None

    @pytest.mark.asyncio
    async def test_get_device_details(self):
        """Test getting detailed device information."""
        service = EtherNetIPDiscoveryService()

        with patch('app.services.discovery.ethernet_ip_discovery.LogixDriver') as mock_driver:
            mock_plc = MagicMock()
            mock_plc.connected = True
            mock_plc.get_plc_info = MagicMock(return_value={
                'vendor': 'Rockwell Automation',
                'name': 'CompactLogix',
                'serial': '123456'
            })
            mock_plc.get_module_info = MagicMock(return_value={
                'product_name': 'Test Module'
            })
            mock_plc.open = MagicMock()
            mock_plc.close = MagicMock()

            mock_driver.return_value = mock_plc

            details = await service.get_device_details("192.168.1.100", slot=0)

            assert details is not None
            assert details['ip_address'] == "192.168.1.100"
            assert details['protocol'] == "EtherNet/IP"
            assert 'info' in details


class TestDiscoveredDevice:
    """Test cases for DiscoveredDevice dataclass."""

    def test_device_creation(self):
        """Test creating discovered device."""
        device = DiscoveredDevice(
            ip_address="192.168.1.100",
            vendor_id=1,
            vendor_name="Rockwell Automation",
            product_name="CompactLogix"
        )

        assert device.ip_address == "192.168.1.100"
        assert device.vendor_id == 1
        assert device.protocol == "EtherNet/IP"

    def test_device_to_dict(self):
        """Test converting device to dictionary."""
        device = DiscoveredDevice(
            ip_address="192.168.1.100",
            vendor_name="Rockwell Automation",
            product_name="CompactLogix"
        )

        data = device.to_dict()

        assert isinstance(data, dict)
        assert data['ip_address'] == "192.168.1.100"
        assert data['protocol'] == "EtherNet/IP"


# Integration tests
@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("INTEGRATION_TESTS") != "1",
    reason="Integration tests disabled"
)
class TestEtherNetIPDiscoveryIntegration:
    """Integration tests for real network discovery."""

    @pytest.mark.asyncio
    async def test_real_network_scan(self):
        """Test scanning real network."""
        service = EtherNetIPDiscoveryService(timeout=2.0)

        # Use test network from environment
        subnet = os.getenv("TEST_SUBNET", "192.168.1.0/24")

        devices = await service.scan_network(subnet)

        # Should return list (may be empty if no devices)
        assert isinstance(devices, list)

    @pytest.mark.asyncio
    async def test_real_device_probe(self):
        """Test probing real device."""
        service = EtherNetIPDiscoveryService()

        plc_ip = os.getenv("TEST_PLC_IP", "192.168.1.100")

        device = await service._probe_device(plc_ip)

        # May be None if device not available
        if device:
            assert device.ip_address == plc_ip


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
