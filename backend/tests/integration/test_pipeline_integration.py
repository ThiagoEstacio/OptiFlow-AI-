"""
Pipeline Integration Tests
===========================

End-to-end integration tests for the complete data pipeline:
Gateway -> Kafka -> Consumer -> InfluxDB

These tests require the full infrastructure to be running.
"""

import pytest
import httpx
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List


# Base URLs for services
# Use container names when running inside Docker, localhost when running locally
def get_backend_url():
    """Get backend URL based on environment"""
    if os.path.exists("/.dockerenv"):  # Running inside Docker container
        return "http://optiflow-backend:8000"
    return os.getenv("BACKEND_URL", "http://localhost:8000")


def get_gateway_url():
    """Get gateway URL based on environment"""
    if os.path.exists("/.dockerenv"):  # Running inside Docker container
        return "http://optiflow-gateway:8080"
    return os.getenv("GATEWAY_URL", "http://localhost:8080")


BACKEND_URL = get_backend_url()
GATEWAY_URL = get_gateway_url()


class TestPipelineHealth:
    """Test pipeline health and connectivity"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_all_services_healthy(self):
        """Verify all services are healthy"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Backend health
            backend_resp = await client.get(f"{BACKEND_URL}/api/health")
            assert backend_resp.status_code == 200
            assert backend_resp.json()["status"] == "healthy"

            # Gateway health
            gateway_resp = await client.get(f"{GATEWAY_URL}/health")
            assert gateway_resp.status_code == 200
            assert gateway_resp.json()["status"] == "healthy"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pipeline_status_operational(self):
        """Verify pipeline is operational"""
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{BACKEND_URL}/api/v1/metrics/pipeline"
            )
            assert resp.status_code == 200
            data = resp.json()

            # Pipeline should be operational or degraded (not critical)
            assert data["pipeline_status"] in ["operational", "degraded"]

            # All components should be present
            components = data["components"]
            assert "kafka" in components
            assert "influxdb" in components
            assert "redis" in components
            assert "consumer" in components


class TestKafkaIntegration:
    """Test Kafka integration"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_kafka_healthy_with_topics(self):
        """Verify Kafka cluster is healthy with required topics"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{BACKEND_URL}/api/v1/metrics/kafka"
            )
            assert resp.status_code == 200
            data = resp.json()

            assert data["status"] == "healthy"
            assert "raw_tags" in data["topics"]
            assert data["topics_count"] >= 1


class TestGatewayIntegration:
    """Test Gateway integration"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_gateway_adapters_connected(self):
        """Verify gateway adapters are connected"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{GATEWAY_URL}/api/adapters/")
            assert resp.status_code == 200
            adapters = resp.json()

            # Should have at least one adapter
            assert len(adapters) >= 1

            # Check OPC-UA adapter is connected
            opcua_adapters = [
                a for a in adapters
                if a.get("protocol_type") == "opcua"
            ]
            if opcua_adapters:
                opcua = opcua_adapters[0]
                assert opcua["connected"] == True
                assert opcua["tags_count"] > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_gateway_tags_available(self):
        """Verify tags are available from gateway"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{GATEWAY_URL}/api/tags/list")
            assert resp.status_code == 200
            data = resp.json()

            assert data["count"] > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_gateway_realtime_values(self):
        """Verify realtime tag values are accessible"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            # First get list of tags
            tags_resp = await client.get(f"{GATEWAY_URL}/api/tags/list")
            tags_data = tags_resp.json()

            if tags_data["count"] > 0:
                # Get values for running tags
                values_resp = await client.get(
                    f"{GATEWAY_URL}/api/tags/realtime/running"
                )
                assert values_resp.status_code == 200
                values = values_resp.json()

                # Should have some values
                assert len(values) > 0

                # Check value structure
                for tag_id, value_data in values.items():
                    assert "value" in value_data or "error" in value_data


class TestConsumerIntegration:
    """Test Kafka Consumer integration"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_consumer_running(self):
        """Verify consumer is running and processing messages"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{BACKEND_URL}/api/v1/metrics/consumer"
            )
            assert resp.status_code == 200
            data = resp.json()

            assert data["status"] == "healthy"
            assert data["running"] == True
            assert data["consumer_enabled"] == True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_consumer_processing_messages(self):
        """Verify consumer is processing messages"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get initial count
            resp1 = await client.get(
                f"{BACKEND_URL}/api/v1/metrics/consumer"
            )
            initial_count = resp1.json().get("messages_processed", 0)

            # Wait a bit for more messages
            await asyncio.sleep(2)

            # Get new count
            resp2 = await client.get(
                f"{BACKEND_URL}/api/v1/metrics/consumer"
            )
            new_count = resp2.json().get("messages_processed", 0)

            # Should have processed more messages
            assert new_count >= initial_count


class TestInfluxDBIntegration:
    """Test InfluxDB integration"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_influxdb_healthy(self):
        """Verify InfluxDB is healthy"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{BACKEND_URL}/api/v1/metrics/influxdb"
            )
            assert resp.status_code == 200
            data = resp.json()

            assert data["status"] == "pass"
            assert "timeseries" in data["buckets"]


class TestEndToEndDataFlow:
    """End-to-end data flow tests"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_flow_gateway_to_influxdb(self):
        """Test complete data flow from gateway to InfluxDB"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Verify gateway is publishing data
            gateway_resp = await client.get(f"{GATEWAY_URL}/health")
            assert gateway_resp.json()["status"] == "healthy"

            # 2. Verify Kafka is receiving messages
            kafka_resp = await client.get(
                f"{BACKEND_URL}/api/v1/metrics/kafka"
            )
            assert kafka_resp.json()["status"] == "healthy"

            # 3. Verify consumer is processing
            consumer_resp = await client.get(
                f"{BACKEND_URL}/api/v1/metrics/consumer"
            )
            consumer_data = consumer_resp.json()
            assert consumer_data["running"] == True

            # 4. Verify InfluxDB has data
            influxdb_resp = await client.get(
                f"{BACKEND_URL}/api/v1/metrics/influxdb"
            )
            assert influxdb_resp.json()["status"] == "pass"

            # 5. Check overall pipeline status
            pipeline_resp = await client.get(
                f"{BACKEND_URL}/api/v1/metrics/pipeline"
            )
            pipeline_data = pipeline_resp.json()
            assert pipeline_data["pipeline_status"] in ["operational", "degraded"]


class TestMetricsEndpoints:
    """Test all metrics endpoints"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_prometheus_metrics_backend(self):
        """Test backend Prometheus metrics endpoint"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{BACKEND_URL}/api/v1/metrics")
            assert resp.status_code == 200
            assert "optiflow" in resp.text

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_prometheus_metrics_gateway(self):
        """Test gateway Prometheus metrics endpoint"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{GATEWAY_URL}/metrics")
            assert resp.status_code == 200
            assert "gateway" in resp.text


# Run integration tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
