# OptiFlow AI - Monitoring Stack

## Overview

OptiFlow AI now has a **complete monitoring stack** integrated with Prometheus and Grafana, providing real-time visibility into application performance, infrastructure health, and business metrics.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Grafana Dashboards                        │
│                    http://localhost:3001                     │
│                    (admin/admin)                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Prometheus                                 │
│                    http://localhost:9090                     │
│                    (Metrics Collection & Alerting)           │
└───┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬──────────────┘
    │     │     │     │     │     │     │     │
    ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼
┌────┐ ┌───┐ ┌───┐ ┌───┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐
│Back│ │PG │ │Red│ │Inf│ │Node│ │Gtwy│ │cAdv│ │Back│
│end │ │Exp│ │Exp│ │DB │ │Exp │ │    │ │isor│ │end │
└────┘ └───┘ └───┘ └───┘ └────┘ └────┘ └────┘ └────┘
:8000  :9187 :9121 :8086 :9100  :8080  :8081  /metrics
```

## Components

### 1. Backend Metrics Endpoint
- **URL:** http://localhost:8000/metrics
- **Implementation:** `backend/app/main.py` using `prometheus_client`
- **Metrics Exposed:**
  - **HTTP Metrics:** Request count, duration, error rate, in-progress requests
  - **Database:** Active connections, query counts, query duration
  - **Extended Tags (PI AF):** Total tags by type/gateway, archived tags, formulas count
  - **Gateway:** Tag count per gateway, connection status
  - **AI Agent:** Interaction counts, response duration, success/failure rates
  - **System:** CPU usage, memory usage, file descriptors
  - **Application Info:** Version, environment, platform name

### 2. Exporters

#### PostgreSQL Exporter
- **Port:** 9187
- **Image:** `prometheuscommunity/postgres-exporter`
- **Metrics:** Database size, connections, queries, transactions, replication lag

#### Redis Exporter
- **Port:** 9121
- **Image:** `oliver006/redis_exporter`
- **Metrics:** Memory usage, connected clients, commands processed, keyspace stats

#### Node Exporter
- **Port:** 9100
- **Image:** `prom/node-exporter`
- **Metrics:** CPU, memory, disk, network, filesystem usage (host-level)

#### cAdvisor
- **Port:** 8081
- **Image:** `gcr.io/cadvisor/cadvisor`
- **Metrics:** Container CPU, memory, network, disk I/O

### 3. Prometheus
- **URL:** http://localhost:9090
- **Config:** `monitoring/prometheus/prometheus.yml`
- **Scrape Interval:** 15s (10s for backend, gateway, cadvisor)
- **Storage:** `prometheus_data` volume
- **Alert Rules:** `monitoring/prometheus/alerts/optiflow_alerts.yml`

**Configured Jobs:**
- `prometheus` - Self-monitoring
- `backend` - FastAPI application (10s interval)
- `postgres` - PostgreSQL exporter
- `redis` - Redis exporter
- `influxdb` - InfluxDB metrics
- `gateway` - Data collection gateway (10s interval)
- `node` - Host system metrics
- `cadvisor` - Container metrics (10s interval)

### 4. Grafana
- **URL:** http://localhost:3001
- **Credentials:** admin/admin
- **Datasources:**
  - **Prometheus** (default) - Infrastructure and application metrics
  - **InfluxDB** - Time-series tag data (Flux query language)
  - **PostgreSQL** - Relational data queries

**Dashboards:**
- **OptiFlow AI - Overview** - Main dashboard with 14 panels
  - Application status
  - HTTP request metrics (rate, duration, errors)
  - Extended tags breakdown
  - Database connections and queries
  - Gateway connection status
  - System resource usage
  - Container metrics

## Alert Rules

Located in `monitoring/prometheus/alerts/optiflow_alerts.yml`

### Application Alerts
- **OptiFlowBackendDown** (critical) - Backend API unreachable for >1min
- **HighRequestLatency** (warning) - p95 latency >1s for >5min
- **HighErrorRate** (critical) - Error rate >5% for >5min

### Database Alerts
- **PostgreSQLDown** (critical) - Database unreachable for >1min
- **HighDatabaseConnections** (warning) - >50 active connections for >5min
- **RedisDown** (warning) - Cache unreachable for >1min
- **InfluxDBDown** (critical) - Time-series DB unreachable for >1min

### Gateway Alerts
- **GatewayDown** (critical) - Gateway unreachable for >2min
- **GatewayDisconnected** (warning) - Gateway disconnected for >5min

### Extended Tags Alerts
- **NoTagsConfigured** (info) - No extended tags for >10min
- **HighTagCalculationFailures** (warning) - >10% calculation failures for >5min

### System Alerts
- **HighCPUUsage** (warning) - CPU >80% for >5min
- **HighMemoryUsage** (warning) - Memory >1GB for >5min
- **TooManyOpenFiles** (warning) - File descriptors >80% of max for >5min

### AI Agent Alerts
- **HighAIAgentFailureRate** (warning) - >20% failures for >5min
- **SlowAIAgentResponse** (warning) - p95 response time >30s for >5min

## Quick Start

### 1. Start All Services
```bash
docker compose up -d
```

### 2. Access Interfaces

**Grafana Dashboards:**
```
http://localhost:3001
User: admin
Pass: admin
```

**Prometheus:**
```
http://localhost:9090
```

**Backend Metrics:**
```
curl http://localhost:8000/metrics
```

### 3. View Specific Metrics

**Extended Tags by Type:**
```promql
sum by (tag_type) (extended_tags_total)
```

**HTTP Request Rate:**
```promql
rate(http_requests_total[5m])
```

**Database Connections:**
```promql
db_connections_active
```

**p95 Request Latency:**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

## Custom Metrics Usage

### In Backend Code

```python
from app.main import (
    extended_tags_total,
    tag_calculations_total,
    ai_agent_interactions_total
)

# Update tag count
extended_tags_total.labels(
    tag_type='calculated',
    gateway_id='1'
).set(42)

# Track formula calculation
tag_calculations_total.labels(
    formula_id='123',
    success='true'
).inc()

# Track AI interaction
ai_agent_interactions_total.labels(
    agent_type='dashboard_builder',
    success='true'
).inc()
```

### Query Examples

**Error rate per endpoint:**
```promql
rate(http_requests_total{status=~"5.."}[5m]) 
/ 
rate(http_requests_total[5m])
```

**Top 5 slowest endpoints:**
```promql
topk(5, 
  histogram_quantile(0.95, 
    rate(http_request_duration_seconds_bucket[5m])
  )
)
```

**Gateway health:**
```promql
gateway_connection_status{gateway_id="1"}
```

## Maintenance

### View Prometheus Targets
```bash
curl http://localhost:9090/api/v1/targets | jq .
```

### Reload Prometheus Config
```bash
docker exec optiflow-prometheus kill -HUP 1
```

### View Grafana Logs
```bash
docker logs optiflow-grafana -f
```

### Restart Monitoring Stack
```bash
docker compose restart prometheus grafana postgres-exporter redis-exporter node-exporter cadvisor
```

## Ports Summary

| Service              | Port  | Purpose                        |
|----------------------|-------|--------------------------------|
| Backend              | 8000  | API + /metrics endpoint        |
| Grafana              | 3001  | Dashboards UI                  |
| Prometheus           | 9090  | Metrics collection & queries   |
| PostgreSQL Exporter  | 9187  | Database metrics               |
| Redis Exporter       | 9121  | Cache metrics                  |
| Node Exporter        | 9100  | Host system metrics            |
| cAdvisor             | 8081  | Container metrics              |
| InfluxDB             | 8086  | Time-series metrics            |

## Files Structure

```
monitoring/
├── prometheus/
│   ├── prometheus.yml          # Scrape configuration
│   └── alerts/
│       └── optiflow_alerts.yml # Alert rules
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── datasources.yml # Auto-configured data sources
        └── dashboards/
            ├── dashboards.yml  # Dashboard provider config
            └── optiflow-overview.json # Main dashboard
```

## Next Steps

1. **Configure Alertmanager** - Set up email/Slack notifications for alerts
2. **Add More Dashboards** - Create specialized dashboards for:
   - Extended Tags detailed view
   - Gateway performance
   - AI Agent analytics
3. **Set Up Log Aggregation** - Integrate Loki for log management
4. **Enable HTTPS** - Secure Grafana and Prometheus with TLS
5. **Backup Configurations** - Automate backup of Grafana dashboards

## Troubleshooting

### Backend metrics not showing
```bash
# Check backend is running
curl http://localhost:8000/health

# Check metrics endpoint
curl http://localhost:8000/metrics | head -20
```

### Prometheus not scraping
```bash
# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

### Grafana dashboard empty
```bash
# Check datasource connection
docker exec optiflow-grafana grafana-cli admin data-sources ls

# Restart Grafana
docker restart optiflow-grafana
```

---

**Status:** ✅ 100% Functional
**Last Updated:** 2025-11-04
**Maintained By:** OptiFlow AI Team
