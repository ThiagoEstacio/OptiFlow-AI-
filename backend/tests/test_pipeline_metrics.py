"""
Test Pipeline Metrics Endpoints
================================

Tests for the consumer metrics API endpoints that provide
pipeline health monitoring for Kafka, InfluxDB, Redis, and Gateway.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime


class TestConsumerMetricsEndpoints:
    """Test suite for consumer metrics API endpoints"""

    @pytest.fixture
    def mock_consumer_status(self):
        """Mock consumer status response"""
        return {
            "running": True,
            "enabled": True,
            "messages_processed": 1000,
            "errors": 0,
            "batch_size": 50,
            "topic": "raw_tags",
            "group_id": "optiflow-consumer"
        }

    @pytest.fixture
    def mock_kafka_health(self):
        """Mock Kafka health response"""
        return {
            "status": "healthy",
            "brokers": "kafka-1:9092,kafka-2:9093,kafka-3:9096",
            "topics_count": 3,
            "topics": ["raw_tags", "raw_tags_dlq", "__consumer_offsets"],
            "checked_at": datetime.utcnow().isoformat()
        }

    @pytest.fixture
    def mock_influxdb_health(self):
        """Mock InfluxDB health response"""
        return {
            "status": "pass",
            "url": "http://influxdb:8086",
            "org": "optiflow",
            "buckets": ["timeseries", "raw_data", "aggregations"],
            "points_last_hour": 50000,
            "checked_at": datetime.utcnow().isoformat()
        }

    @pytest.fixture
    def mock_redis_health(self):
        """Mock Redis health response"""
        return {
            "status": "healthy",
            "host": "redis:6379",
            "memory_used": "1.5M",
            "keys_count": 10,
            "checked_at": datetime.utcnow().isoformat()
        }

    @pytest.fixture
    def mock_gateway_health(self):
        """Mock Gateway health response"""
        return {
            "status": "healthy",
            "url": "http://optiflow-gateway:8080",
            "health": {"status": "healthy"},
            "adapters_count": 2,
            "adapters": [
                {
                    "adapter_id": "opcua-001",
                    "protocol_type": "opcua",
                    "connected": True,
                    "tags_count": 53
                },
                {
                    "adapter_id": "modbus-001",
                    "protocol_type": "modbus",
                    "connected": True,
                    "tags_count": 25
                }
            ],
            "tags_count": 78,
            "checked_at": datetime.utcnow().isoformat()
        }


class TestConsumerEndpoint:
    """Tests for /api/v1/metrics/consumer endpoint"""

    def test_consumer_metrics_healthy(self, client, mock_consumer_status):
        """Test consumer metrics when consumer is running"""
        with patch(
            'app.api.routes.consumer_metrics.get_consumer_status',
            return_value=mock_consumer_status
        ):
            response = client.get("/api/v1/metrics/consumer")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "healthy"
            assert data["running"] == True
            assert data["messages_processed"] == 1000
            assert data["errors_count"] == 0
            assert data["consumer_enabled"] == True
            assert data["topic"] == "raw_tags"

    def test_consumer_metrics_stopped(self, client):
        """Test consumer metrics when consumer is stopped"""
        with patch(
            'app.api.routes.consumer_metrics.get_consumer_status',
            return_value={"running": False, "enabled": False}
        ):
            response = client.get("/api/v1/metrics/consumer")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "stopped"
            assert data["running"] == False


class TestKafkaEndpoint:
    """Tests for /api/v1/metrics/kafka endpoint"""

    def test_kafka_healthy(self, client, mock_kafka_health):
        """Test Kafka metrics when cluster is healthy"""
        with patch(
            'app.api.routes.consumer_metrics.check_kafka_health',
            new_callable=AsyncMock,
            return_value=mock_kafka_health
        ):
            response = client.get("/api/v1/metrics/kafka")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "healthy"
            assert data["topics_count"] == 3
            assert "raw_tags" in data["topics"]

    def test_kafka_timeout(self, client):
        """Test Kafka metrics when connection times out"""
        with patch(
            'app.api.routes.consumer_metrics.check_kafka_health',
            new_callable=AsyncMock,
            return_value={
                "status": "timeout",
                "error": "Connection to Kafka timed out"
            }
        ):
            response = client.get("/api/v1/metrics/kafka")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "timeout"
            assert "error" in data


class TestInfluxDBEndpoint:
    """Tests for /api/v1/metrics/influxdb endpoint"""

    def test_influxdb_healthy(self, client, mock_influxdb_health):
        """Test InfluxDB metrics when database is healthy"""
        with patch(
            'app.api.routes.consumer_metrics.check_influxdb_health',
            new_callable=AsyncMock,
            return_value=mock_influxdb_health
        ):
            response = client.get("/api/v1/metrics/influxdb")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "pass"
            assert data["org"] == "optiflow"
            assert "timeseries" in data["buckets"]

    def test_influxdb_error(self, client):
        """Test InfluxDB metrics when database has error"""
        with patch(
            'app.api.routes.consumer_metrics.check_influxdb_health',
            new_callable=AsyncMock,
            return_value={
                "status": "error",
                "error": "Connection refused"
            }
        ):
            response = client.get("/api/v1/metrics/influxdb")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "error"


class TestRedisEndpoint:
    """Tests for /api/v1/metrics/redis endpoint"""

    def test_redis_healthy(self, client, mock_redis_health):
        """Test Redis metrics when cache is healthy"""
        with patch(
            'app.api.routes.consumer_metrics.check_redis_health',
            new_callable=AsyncMock,
            return_value=mock_redis_health
        ):
            response = client.get("/api/v1/metrics/redis")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "healthy"
            assert "memory_used" in data
            assert data["keys_count"] == 10


class TestGatewayEndpoint:
    """Tests for /api/v1/metrics/gateway endpoint"""

    def test_gateway_healthy(self, client, mock_gateway_health):
        """Test Gateway metrics when gateway is healthy"""
        with patch(
            'app.api.routes.consumer_metrics.get_gateway_metrics',
            new_callable=AsyncMock,
            return_value=mock_gateway_health
        ):
            response = client.get("/api/v1/metrics/gateway")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "healthy"
            assert data["adapters_count"] == 2
            assert data["tags_count"] == 78


class TestPipelineEndpoint:
    """Tests for /api/v1/metrics/pipeline endpoint"""

    def test_pipeline_operational(
        self, client, mock_consumer_status, mock_kafka_health,
        mock_influxdb_health, mock_redis_health
    ):
        """Test pipeline metrics when all components are healthy"""
        with patch(
            'app.api.routes.consumer_metrics.get_consumer_status',
            return_value=mock_consumer_status
        ), patch(
            'app.api.routes.consumer_metrics.check_kafka_health',
            new_callable=AsyncMock,
            return_value=mock_kafka_health
        ), patch(
            'app.api.routes.consumer_metrics.check_influxdb_health',
            new_callable=AsyncMock,
            return_value=mock_influxdb_health
        ), patch(
            'app.api.routes.consumer_metrics.check_redis_health',
            new_callable=AsyncMock,
            return_value=mock_redis_health
        ):
            response = client.get("/api/v1/metrics/pipeline")

            assert response.status_code == 200
            data = response.json()

            assert data["pipeline_status"] == "operational"
            assert "components" in data
            assert "data_flow" in data

            # Verify all components are present
            components = data["components"]
            assert "kafka" in components
            assert "influxdb" in components
            assert "redis" in components
            assert "consumer" in components

    def test_pipeline_degraded_kafka_unhealthy(self, client, mock_consumer_status):
        """Test pipeline status is degraded when Kafka is unhealthy"""
        with patch(
            'app.api.routes.consumer_metrics.get_consumer_status',
            return_value=mock_consumer_status
        ), patch(
            'app.api.routes.consumer_metrics.check_kafka_health',
            new_callable=AsyncMock,
            return_value={"status": "error", "error": "Connection failed"}
        ), patch(
            'app.api.routes.consumer_metrics.check_influxdb_health',
            new_callable=AsyncMock,
            return_value={"status": "pass"}
        ), patch(
            'app.api.routes.consumer_metrics.check_redis_health',
            new_callable=AsyncMock,
            return_value={"status": "healthy"}
        ):
            response = client.get("/api/v1/metrics/pipeline")

            assert response.status_code == 200
            data = response.json()

            # Should be critical when Kafka is down
            assert data["pipeline_status"] == "critical"


# Fixtures for test client
@pytest.fixture
def client():
    """Create test client"""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def mock_consumer_status():
    """Mock consumer status response"""
    return {
        "running": True,
        "enabled": True,
        "messages_processed": 1000,
        "errors": 0,
        "batch_size": 50,
        "topic": "raw_tags",
        "group_id": "optiflow-consumer"
    }


@pytest.fixture
def mock_kafka_health():
    """Mock Kafka health response"""
    return {
        "status": "healthy",
        "brokers": "kafka-1:9092,kafka-2:9093,kafka-3:9096",
        "topics_count": 3,
        "topics": ["raw_tags", "raw_tags_dlq", "__consumer_offsets"],
        "checked_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def mock_influxdb_health():
    """Mock InfluxDB health response"""
    return {
        "status": "pass",
        "url": "http://influxdb:8086",
        "org": "optiflow",
        "buckets": ["timeseries", "raw_data", "aggregations"],
        "points_last_hour": 50000,
        "checked_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def mock_redis_health():
    """Mock Redis health response"""
    return {
        "status": "healthy",
        "host": "redis:6379",
        "memory_used": "1.5M",
        "keys_count": 10,
        "checked_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def mock_gateway_health():
    """Mock Gateway health response"""
    return {
        "status": "healthy",
        "url": "http://optiflow-gateway:8080",
        "health": {"status": "healthy"},
        "adapters_count": 2,
        "adapters": [],
        "tags_count": 78,
        "checked_at": datetime.utcnow().isoformat()
    }
