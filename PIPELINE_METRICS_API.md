# Pipeline Metrics API Documentation

## Overview

The OptiFlow Pipeline Metrics API provides comprehensive monitoring endpoints for the entire data pipeline:

```
Gateway → Kafka → Consumer → InfluxDB
```

**Base URL**: `http://localhost:8000/api/v1`

---

## Quick Status Check

```bash
# Check overall pipeline status
curl http://localhost:8000/api/v1/metrics/pipeline

# Response:
{
  "pipeline_status": "operational",  # operational | degraded | critical
  "components": {
    "kafka": { "status": "healthy" },
    "influxdb": { "status": "pass" },
    "redis": { "status": "healthy" },
    "consumer": { "status": "running" }
  }
}
```

---

## Endpoints

### Pipeline Health

#### `GET /api/v1/metrics/pipeline`

Returns comprehensive pipeline health status with all components.

**Response:**
```json
{
  "pipeline_status": "operational",
  "checked_at": "2025-11-25T13:00:00.000000",
  "components": {
    "kafka": {
      "status": "healthy",
      "brokers": "kafka-1:9092,kafka-2:9093,kafka-3:9096",
      "topics_count": 3,
      "topics": ["raw_tags", "raw_tags_dlq", "__consumer_offsets"]
    },
    "influxdb": {
      "status": "pass",
      "url": "http://influxdb:8086",
      "org": "optiflow",
      "buckets": ["timeseries", "aggregations", "downsampled_1h"],
      "points_last_hour": 50000
    },
    "redis": {
      "status": "healthy",
      "host": "redis:6379",
      "memory_used": "1.5M",
      "keys_count": 10
    },
    "consumer": {
      "status": "running",
      "enabled": true,
      "messages_processed": 10000,
      "errors": 0,
      "topic": "raw_tags",
      "group_id": "optiflow-consumer"
    }
  },
  "data_flow": {
    "description": "Gateway → Kafka → Consumer → InfluxDB",
    "gateway": "Publishing to Kafka",
    "kafka_to_influxdb": "running"
  }
}
```

**Pipeline Status Values:**
- `operational`: All components healthy
- `degraded`: Some components unhealthy but data flowing
- `critical`: Kafka down, no data flow

---

### Kafka Metrics

#### `GET /api/v1/metrics/kafka`

Returns Kafka cluster health and topic information.

**Response:**
```json
{
  "status": "healthy",
  "brokers": "kafka-1:9092,kafka-2:9093,kafka-3:9096",
  "topics_count": 3,
  "topics": ["raw_tags", "raw_tags_dlq", "__consumer_offsets"],
  "checked_at": "2025-11-25T13:00:00.000000"
}
```

**Status Values:**
- `healthy`: Kafka cluster reachable and responsive
- `timeout`: Connection timed out (5s default)
- `error`: Connection failed

---

### InfluxDB Metrics

#### `GET /api/v1/metrics/influxdb`

Returns InfluxDB health and data statistics.

**Response:**
```json
{
  "status": "pass",
  "url": "http://influxdb:8086",
  "org": "optiflow",
  "buckets": [
    "timeseries",
    "aggregations",
    "downsampled_1h",
    "downsampled_1d",
    "raw_data"
  ],
  "points_last_hour": 125000,
  "checked_at": "2025-11-25T13:00:00.000000"
}
```

**Status Values:**
- `pass`: InfluxDB healthy (from InfluxDB health check)
- `error`: Connection failed

---

### Redis Metrics

#### `GET /api/v1/metrics/redis`

Returns Redis cache health and statistics.

**Response:**
```json
{
  "status": "healthy",
  "host": "redis:6379",
  "memory_used": "2.5M",
  "keys_count": 150,
  "checked_at": "2025-11-25T13:00:00.000000"
}
```

---

### Consumer Metrics

#### `GET /api/v1/metrics/consumer`

Returns Kafka consumer status and processing metrics.

**Response:**
```json
{
  "status": "healthy",
  "running": true,
  "messages_processed": 15000,
  "errors_count": 0,
  "batch_size_current": 100,
  "consumer_enabled": true,
  "topic": "raw_tags",
  "group_id": "optiflow-consumer"
}
```

**Status Values:**
- `healthy`: Consumer running and processing
- `stopped`: Consumer not running
- `error`: Error occurred

---

### Gateway Metrics

#### `GET /api/v1/metrics/gateway`

Returns Gateway health and adapter status (calls gateway API).

**Response:**
```json
{
  "status": "healthy",
  "url": "http://optiflow-gateway:8080",
  "health": {
    "status": "healthy"
  },
  "adapters_count": 2,
  "adapters": [
    {
      "adapter_id": "opcua-simulator-001",
      "protocol_type": "opcua",
      "connected": true,
      "running": true,
      "tags_count": 53
    },
    {
      "adapter_id": "modbus-pump-station-001",
      "protocol_type": "modbus",
      "connected": true,
      "running": true,
      "tags_count": 25
    }
  ],
  "tags_count": 78,
  "checked_at": "2025-11-25T13:00:00.000000"
}
```

---

## Prometheus Metrics

### Backend Metrics

#### `GET /api/v1/metrics`

Returns Prometheus-formatted metrics from the backend.

```bash
curl http://localhost:8000/api/v1/metrics
```

**Sample Output:**
```
# HELP optiflow_http_requests_total Total HTTP requests
# TYPE optiflow_http_requests_total counter
optiflow_http_requests_total{endpoint="/api/v1/tags",method="GET",status="200"} 150

# HELP optiflow_http_request_duration_seconds HTTP request latency
# TYPE optiflow_http_request_duration_seconds histogram
optiflow_http_request_duration_seconds_bucket{le="0.01"} 50
```

### Gateway Metrics

#### `GET /metrics` (Gateway - port 8080)

Returns Prometheus-formatted metrics from the gateway.

```bash
curl http://localhost:8080/metrics
```

**Sample Output:**
```
# HELP gateway_devices_connected Number of connected devices
# TYPE gateway_devices_connected gauge
gateway_devices_connected{protocol="opcua",gateway_id="gateway-01"} 1

# HELP gateway_tags_read_total Total tags read
# TYPE gateway_tags_read_total counter
gateway_tags_read_total{protocol="opcua",quality="GOOD"} 50000

# HELP gateway_tags_read_duration_seconds Tag read operation latency
# TYPE gateway_tags_read_duration_seconds histogram
gateway_tags_read_duration_seconds_bucket{le="0.001"} 45000
```

---

## Grafana Dashboards

Pre-configured dashboards are available at: `http://localhost:3001`

**Dashboards:**
- OptiFlow System Overview
- OptiFlow Pipeline Monitoring
- OptiFlow API Metrics
- OptiFlow Devices Monitoring
- OptiFlow ML Metrics

**Default Login:**
- Username: `admin`
- Password: `admin`

---

## Usage Examples

### Bash Health Check Script

```bash
#!/bin/bash
# Quick pipeline health check

BACKEND="http://localhost:8000"

echo "Checking pipeline health..."
status=$(curl -s "$BACKEND/api/v1/metrics/pipeline" | jq -r '.pipeline_status')

case $status in
  "operational")
    echo "✅ Pipeline operational"
    exit 0
    ;;
  "degraded")
    echo "⚠️  Pipeline degraded"
    exit 1
    ;;
  "critical")
    echo "❌ Pipeline critical"
    exit 2
    ;;
  *)
    echo "❓ Unknown status: $status"
    exit 3
    ;;
esac
```

### Python Monitoring Script

```python
import httpx
import asyncio

async def check_pipeline():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Check pipeline
        resp = await client.get("http://localhost:8000/api/v1/metrics/pipeline")
        data = resp.json()

        print(f"Pipeline Status: {data['pipeline_status']}")

        for component, info in data['components'].items():
            status = info.get('status', 'unknown')
            print(f"  - {component}: {status}")

        return data['pipeline_status'] == 'operational'

asyncio.run(check_pipeline())
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka-1:9092,kafka-2:9093,kafka-3:9096` | Kafka brokers |
| `INFLUXDB_URL` | `http://influxdb:8086` | InfluxDB URL |
| `INFLUXDB_TOKEN` | - | InfluxDB access token |
| `INFLUXDB_ORG` | `optiflow` | InfluxDB organization |
| `REDIS_URL` | `redis://:password@redis:6379/0` | Redis connection URL |
| `GATEWAY_URL` | `http://optiflow-gateway:8080` | Gateway URL |

---

## Troubleshooting

### Pipeline Status "critical"

1. Check Kafka is running:
```bash
docker ps | grep kafka
curl http://localhost:8000/api/v1/metrics/kafka
```

2. Check consumer logs:
```bash
docker logs optiflow-backend | grep -i consumer
```

### Pipeline Status "degraded"

1. Check individual components:
```bash
curl http://localhost:8000/api/v1/metrics/influxdb
curl http://localhost:8000/api/v1/metrics/redis
curl http://localhost:8000/api/v1/metrics/gateway
```

2. Restart unhealthy component:
```bash
docker restart optiflow-influxdb
docker restart optiflow-redis
```

### No Data in InfluxDB

1. Verify consumer is processing:
```bash
curl http://localhost:8000/api/v1/metrics/consumer
# Should show messages_processed increasing
```

2. Check gateway is publishing:
```bash
docker logs optiflow-gateway | grep "Published"
```

3. Verify Kafka has messages:
```bash
docker exec kafka-1 kafka-console-consumer --bootstrap-server localhost:9092 --topic raw_tags --max-messages 5
```
