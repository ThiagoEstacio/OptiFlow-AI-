"""
Unit tests for database models
"""
import pytest
from uuid import uuid4
from app.models import Organization, Site, User, Device, Tag


class TestOrganizationModel:
    """Test Organization model"""

    def test_organization_creation(self):
        """Test creating an organization instance"""
        org = Organization(
            name="Test Org",
            slug="test-org",
            description="Test description",
            is_active=True
        )
        assert org.name == "Test Org"
        assert org.slug == "test-org"
        assert org.is_active is True

    def test_organization_repr(self):
        """Test organization string representation"""
        org = Organization(name="Test Org", slug="test-org")
        assert repr(org) == "<Organization Test Org>"


class TestSiteModel:
    """Test Site model"""

    def test_site_creation(self):
        """Test creating a site instance"""
        site = Site(
            organization_id=uuid4(),
            name="Test Site",
            slug="test-site",
            site_type="port",
            city="Test City",
            country="Test Country"
        )
        assert site.name == "Test Site"
        assert site.site_type == "port"
        assert site.city == "Test City"

    def test_site_repr(self):
        """Test site string representation"""
        site = Site(organization_id=uuid4(), name="Test Site", slug="test-site")
        assert repr(site) == "<Site Test Site>"


class TestDeviceModel:
    """Test Device model"""

    def test_device_creation(self):
        """Test creating a device instance"""
        device = Device(
            site_id=uuid4(),
            name="Test PLC",
            protocol="opcua",
            connection_config={"endpoint": "opc.tcp://localhost:4840"},
            status="unknown"
        )
        assert device.name == "Test PLC"
        assert device.protocol.value == "opcua"
        assert device.status.value == "unknown"

    def test_device_repr(self):
        """Test device string representation"""
        device = Device(
            site_id=uuid4(),
            name="Test PLC",
            protocol="opcua",
            connection_config={}
        )
        assert repr(device) == "<Device Test PLC (opcua)>"
