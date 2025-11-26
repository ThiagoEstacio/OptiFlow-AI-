"""
Test Gateway API Endpoints
===========================

Tests for the gateway HTTP API endpoints including:
- Health checks
- Adapter management
- Tag operations
- Metrics endpoints
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime


class TestHealthEndpoints:
    """Tests for gateway health endpoints"""

    def test_health_endpoint(self, client):
        """Test basic health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_ready_endpoint_healthy(self, client, mock_protocol_manager):
        """Test readiness endpoint when adapters are connected"""
        mock_protocol_manager.get_status.return_value = {
            "total_adapters": 2,
            "running_adapters": 2,
            "connected_adapters": 2
        }

        with patch(
            'app.api_app.protocol_manager',
            mock_protocol_manager
        ):
            response = client.get("/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["ready"] == True


class TestAdapterEndpoints:
    """Tests for adapter management endpoints"""

    def test_list_adapters(self, client, mock_protocol_manager, sample_adapters):
        """Test listing all adapters"""
        mock_protocol_manager.get_all_adapters.return_value = sample_adapters

        with patch(
            'app.api.routes.adapters.protocol_manager',
            mock_protocol_manager
        ):
            response = client.get("/api/adapters/")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

    def test_get_adapter_status(self, client, mock_protocol_manager, sample_adapter):
        """Test getting single adapter status"""
        mock_protocol_manager.get_adapter.return_value = sample_adapter

        with patch(
            'app.api.routes.adapters.protocol_manager',
            mock_protocol_manager
        ):
            response = client.get("/api/adapters/opcua-001")
            assert response.status_code == 200
            data = response.json()
            assert data["adapter_id"] == "opcua-001"
            assert data["connected"] == True

    def test_get_adapter_not_found(self, client, mock_protocol_manager):
        """Test getting non-existent adapter"""
        mock_protocol_manager.get_adapter.return_value = None

        with patch(
            'app.api.routes.adapters.protocol_manager',
            mock_protocol_manager
        ):
            response = client.get("/api/adapters/nonexistent")
            assert response.status_code == 404


class TestTagEndpoints:
    """Tests for tag operations endpoints"""

    def test_list_tags(self, client, mock_protocol_manager, sample_tags):
        """Test listing all tags"""
        mock_protocol_manager.get_all_tags.return_value = sample_tags

        with patch(
            'app.api.routes.tags_realtime.protocol_manager',
            mock_protocol_manager
        ):
            response = client.get("/api/tags/list")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] > 0

    def test_get_tag_value(self, client, mock_protocol_manager):
        """Test getting single tag value"""
        mock_value = {
            "value": 25.5,
            "quality": "GOOD",
            "timestamp": datetime.utcnow().isoformat()
        }

        mock_adapter = MagicMock()
        mock_adapter.last_values = {
            "ns=2;s=Silo1.Temperature": {
                "value": 25.5,
                "quality": "GOOD",
                "timestamp": datetime.utcnow()
            }
        }
        mock_protocol_manager.get_all_adapters.return_value = {
            "opcua-001": mock_adapter
        }

        with patch(
            'app.api.routes.tags_realtime.protocol_manager',
            mock_protocol_manager
        ):
            response = client.get(
                "/api/tags/realtime/value",
                params={"tag_id": "ns=2;s=Silo1.Temperature"}
            )
            assert response.status_code == 200

    def test_get_bulk_values(self, client, mock_protocol_manager):
        """Test getting multiple tag values at once"""
        mock_adapter = MagicMock()
        mock_adapter.last_values = {
            "tag1": {"value": 10, "quality": "GOOD"},
            "tag2": {"value": 20, "quality": "GOOD"}
        }
        mock_protocol_manager.get_all_adapters.return_value = {
            "opcua-001": mock_adapter
        }

        with patch(
            'app.api.routes.tags_realtime.protocol_manager',
            mock_protocol_manager
        ):
            response = client.post(
                "/api/tags/realtime/values",
                json={"tag_ids": ["tag1", "tag2"]}
            )
            assert response.status_code == 200


class TestMetricsEndpoints:
    """Tests for Prometheus metrics endpoints"""

    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint"""
        with patch(
            'app.api_app.get_gateway_metrics'
        ) as mock_get_metrics:
            mock_metrics = MagicMock()
            mock_metrics.export_metrics.return_value = b"# HELP gateway_info\n"
            mock_metrics.get_content_type.return_value = "text/plain"
            mock_get_metrics.return_value = mock_metrics

            response = client.get("/metrics")
            assert response.status_code == 200
            assert "gateway" in response.text or "HELP" in response.text

    def test_metrics_health_endpoint(self, client):
        """Test metrics health check endpoint"""
        with patch(
            'app.api_app.get_gateway_metrics'
        ) as mock_get_metrics:
            mock_metrics = MagicMock()
            mock_metrics.export_metrics.return_value = b"metrics_data"
            mock_get_metrics.return_value = mock_metrics

            response = client.get("/health/metrics")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"


# Fixtures

@pytest.fixture
def client():
    """Create test client for gateway API"""
    from app.api_app import app
    return TestClient(app)


@pytest.fixture
def mock_protocol_manager():
    """Create mock protocol manager"""
    mock = MagicMock()
    mock.get_status.return_value = {
        "total_adapters": 2,
        "running_adapters": 2,
        "connected_adapters": 2
    }
    return mock


@pytest.fixture
def sample_adapter():
    """Sample adapter object"""
    adapter = MagicMock()
    adapter.adapter_id = "opcua-001"
    adapter.protocol_type = "opcua"
    adapter.connected = True
    adapter.running = True
    adapter.tags_count = 53
    adapter.host = "opcua-server"
    adapter.port = 4840
    return adapter


@pytest.fixture
def sample_adapters(sample_adapter):
    """Sample adapters dictionary"""
    modbus_adapter = MagicMock()
    modbus_adapter.adapter_id = "modbus-001"
    modbus_adapter.protocol_type = "modbus"
    modbus_adapter.connected = True
    modbus_adapter.running = True
    modbus_adapter.tags_count = 25
    modbus_adapter.host = "modbus-server"
    modbus_adapter.port = 502

    return {
        "opcua-001": sample_adapter,
        "modbus-001": modbus_adapter
    }


@pytest.fixture
def sample_tags():
    """Sample tags list"""
    return [
        {
            "tag_id": "ns=2;s=Silo1.Temperature",
            "name": "Silo 1 Temperature",
            "adapter_id": "opcua-001",
            "data_type": "Double",
            "unit": "°C"
        },
        {
            "tag_id": "ns=2;s=Silo1.Level",
            "name": "Silo 1 Level",
            "adapter_id": "opcua-001",
            "data_type": "Double",
            "unit": "%"
        },
        {
            "tag_id": "40001",
            "name": "Pump 1 Speed",
            "adapter_id": "modbus-001",
            "data_type": "Float",
            "unit": "RPM"
        }
    ]
