# OptiFlow Monitoring Stack

Complete observability stack for OptiFlow platform with metrics, logs, alerts, and dashboards.

## 📊 Stack Components

| Component | Purpose | Access | Storage |
|-----------|---------|--------|---------|
| **Prometheus** | Metrics collection & querying | http://prometheus.optiflow.local | 50Gi (30 days retention) |
| **Grafana** | Visualization & dashboards | http://grafana.optiflow.local | 10Gi |
| **Loki** | Log aggregation | http://loki:3100 (internal) | 30Gi (7 days retention) |
| **Promtail** | Log collection agent | - (DaemonSet) | - |
| **AlertManager** | Alert routing & notifications | http://alertmanager.optiflow.local | 5Gi |

**Total Storage Required**: ~95Gi

---

## 🚀 Quick Start

### 1. Deploy Monitoring Stack

```bash
# Create monitoring namespace
kubectl create namespace monitoring

# Deploy Prometheus (metrics)
kubectl apply -f prometheus/prometheus.yaml
kubectl apply -f prometheus/rules/optiflow-alerts.yaml

# Deploy Grafana (dashboards)
kubectl apply -f grafana/grafana.yaml
kubectl apply -f grafana/grafana-dashboards.yaml

# Deploy Loki (logs)
kubectl apply -f loki/loki.yaml

# Deploy AlertManager (alerting)
kubectl apply -f alertmanager/alertmanager.yaml

# Verify deployment
kubectl get pods -n monitoring
```

### 2. Wait for Pods to be Ready

```bash
kubectl wait --for=condition=ready pod \
  --all \
  --timeout=300s \
  -n monitoring
```

### 3. Access Services

#### Option A: Port-forward (Development)

```bash
# Grafana (main UI)
kubectl port-forward -n monitoring svc/grafana 3000:3000
# Access: http://localhost:3000
# Default credentials: admin / optiflow123

# Prometheus (metrics explorer)
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Access: http://localhost:9090

# AlertManager (alert management)
kubectl port-forward -n monitoring svc/alertmanager 9093:9093
# Access: http://localhost:9093
```

#### Option B: Ingress (Production)

```bash
# Add to /etc/hosts
echo "127.0.0.1 grafana.optiflow.local" | sudo tee -a /etc/hosts
echo "127.0.0.1 prometheus.optiflow.local" | sudo tee -a /etc/hosts
echo "127.0.0.1 alertmanager.optiflow.local" | sudo tee -a /etc/hosts

# Access via browser
http://grafana.optiflow.local
http://prometheus.optiflow.local
http://alertmanager.optiflow.local
```

---

## 📈 Pre-configured Dashboards

Grafana includes 4 pre-configured dashboards:

### 1. Platform Overview
**URL**: Grafana → Dashboards → OptiFlow - Platform Overview

**Metrics**:
- ✅ Service health status (all OptiFlow services)
- 📊 Request rate across services
- ❌ Error rate (5xx responses)
- ⏱️ Response time (p95 latency)

**Use case**: Executive dashboard, high-level system health

---

### 2. Gateway Metrics
**URL**: Grafana → Dashboards → OptiFlow - Gateway Metrics

**Metrics**:
- 🔌 PLC connection status (per adapter)
- 📡 Tags published rate
- ⏱️ Gateway API latency (p95, p99)
- 💾 Buffer utilization (with alert at 90%)
- ✅ Kafka publish success rate
- 🌐 Network traffic (bytes sent/received)

**Use case**: Gateway operations, edge monitoring, PLC connectivity troubleshooting

**Alerts configured**:
- ⚠️ Buffer >90% (warning)
- 🚨 PLC disconnected (critical)

---

### 3. Backend Metrics
**URL**: Grafana → Dashboards → OptiFlow - Backend Metrics

**Metrics**:
- 📊 API requests/sec (by method & endpoint)
- 📨 Kafka consumer lag (with alert at 10k)
- 🗄️ Database connection pool usage
- 💾 InfluxDB write rate & failures
- 🧠 Memory usage
- ⚙️ CPU usage

**Use case**: Backend performance, database bottlenecks, Kafka monitoring

**Alerts configured**:
- ⚠️ Kafka lag >10,000 messages
- 🚨 Connection pool >90%

---

### 4. Kubernetes Cluster
**URL**: Grafana → Dashboards → OptiFlow - Kubernetes Cluster

**Metrics**:
- ⚙️ Node CPU usage
- 🧠 Node memory usage
- 📦 Pod count by namespace
- 💾 Disk usage
- 🌐 Network traffic

**Use case**: Cluster capacity planning, resource optimization

---

## 🚨 Alert Rules

### Service Health Alerts

| Alert | Condition | Severity | Receiver |
|-------|-----------|----------|----------|
| **ServiceDown** | Service unavailable for 2m | 🚨 Critical | PagerDuty + Slack |
| **HighErrorRate** | >5% 5xx errors for 5m | ⚠️ Warning | Slack |

### Gateway Alerts

| Alert | Condition | Severity | Receiver |
|-------|-----------|----------|----------|
| **GatewayPLCDisconnected** | PLC connection lost for 1m | 🚨 Critical | PagerDuty (ops) |
| **GatewayHighLatency** | p95 latency >100ms for 5m | ⚠️ Warning | Slack (ops) |
| **GatewayBufferFull** | Buffer >90% for 5m | ⚠️ Warning | Slack (ops) |

### Backend Alerts

| Alert | Condition | Severity | Receiver |
|-------|-----------|----------|----------|
| **KafkaConsumerLag** | Lag >10,000 messages for 5m | ⚠️ Warning | Slack (platform) |
| **DatabaseConnectionPoolExhausted** | Pool >90% for 2m | 🚨 Critical | PagerDuty + Slack |
| **InfluxDBWriteFailures** | Write failures >0.01/s for 5m | ⚠️ Warning | Slack (platform) |

### Resource Alerts

| Alert | Condition | Severity | Receiver |
|-------|-----------|----------|----------|
| **HighCPUUsage** | CPU >80% for 10m | ⚠️ Warning | Slack (platform) |
| **HighMemoryUsage** | Memory >90% for 5m | ⚠️ Warning | Slack (platform) |
| **DiskSpaceLow** | Disk <10% free for 5m | 🚨 Critical | PagerDuty + Email |

### Business Metrics Alerts

| Alert | Condition | Severity | Receiver |
|-------|-----------|----------|----------|
| **NoDataIngestion** | No tags published for 10m | 🚨 Critical | PagerDuty (ops) + Slack (business) |
| **AnomalousTagValue** | Tag value changes >50% in 1h | ⚠️ Warning | Slack (business) |

---

## 🔔 Alert Routing

AlertManager routes alerts to different channels based on severity and team:

```
┌─────────────┐
│   CRITICAL  │ ──▶ PagerDuty (24/7 on-call) + Slack
└─────────────┘

┌─────────────┐
│   WARNING   │ ──▶ Slack (#alerts, #ops-alerts, #platform-alerts)
└─────────────┘

┌─────────────┐
│    INFO     │ ──▶ Email (ops@optiflow.com)
└─────────────┘
```

### Notification Channels

| Channel | Purpose | Alerts |
|---------|---------|--------|
| **PagerDuty** | 24/7 on-call escalation | Critical alerts only |
| **Slack #alerts** | General warnings | All warning-level alerts |
| **Slack #ops-alerts** | Operations team | Gateway, PLC, business metrics |
| **Slack #platform-alerts** | Platform team | Backend, Kafka, database |
| **Slack #business-metrics** | Business team | Data ingestion, anomalies |
| **Email** | Low-priority notifications | Info-level alerts |

---

## ⚙️ Configuration

### 1. Configure Alert Notifications

Edit `alertmanager/alertmanager.yaml` to add your credentials:

```yaml
# SMTP (Email)
smtp_auth_username: 'alerts@your-company.com'
smtp_auth_password: 'YOUR_SMTP_PASSWORD'

# Slack
SLACK_WEBHOOK_URL: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

# PagerDuty
PAGERDUTY_SERVICE_KEY_CRITICAL: 'YOUR_PAGERDUTY_KEY'
```

**🔒 Security Best Practice**: Use Sealed Secrets or External Secrets Operator instead of plain secrets in Git!

```bash
# Example with Sealed Secrets
kubeseal --format yaml < alertmanager-secrets.yaml > alertmanager-secrets-sealed.yaml
kubectl apply -f alertmanager-secrets-sealed.yaml
```

### 2. Customize Alert Rules

Edit `prometheus/rules/optiflow-alerts.yaml`:

```yaml
# Example: Add custom alert
- alert: CustomMetric
  expr: my_custom_metric > 100
  for: 5m
  labels:
    severity: warning
    team: ops
  annotations:
    summary: "Custom metric exceeded threshold"
    description: "Value is {{ $value }}"
```

Reload Prometheus config:
```bash
kubectl rollout restart deployment/prometheus -n monitoring
```

### 3. Add Custom Dashboards

Edit `grafana/grafana-dashboards.yaml` or import via Grafana UI:

```bash
# Access Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Go to http://localhost:3000
# Login: admin / optiflow123
# Click "+" → "Import" → Upload JSON
```

---

## 🔍 Querying Metrics

### Prometheus Query Examples

```promql
# Service uptime
up{job=~"optiflow-.*"}

# Request rate (requests/second)
rate(http_requests_total{job="optiflow-backend"}[5m])

# Error rate (%)
sum(rate(http_requests_total{status=~"5.."}[5m]))
/
sum(rate(http_requests_total[5m])) * 100

# p95 latency
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket[5m])
)

# Kafka consumer lag
kafka_consumer_lag

# Gateway PLC connections
count(gateway_plc_connected == 1)

# Memory usage
process_resident_memory_bytes{job="optiflow-backend"}

# CPU usage (%)
rate(process_cpu_seconds_total{job="optiflow-backend"}[5m]) * 100
```

### Loki Query Examples (LogQL)

Access via Grafana → Explore → Loki datasource

```logql
# All logs from backend
{namespace="optiflow-prod", app="backend"}

# Error logs only
{namespace="optiflow-prod"} |= "ERROR"

# Gateway PLC disconnection logs
{app="gateway"} |= "PLC disconnected"

# API request logs with status 500
{app="backend"} | json | status="500"

# Count error logs per minute
sum(rate({namespace="optiflow-prod"} |= "ERROR" [1m]))
```

---

## 📊 Custom Metrics for OptiFlow Services

### Required Annotations

Add to your service's Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service
spec:
  template:
    metadata:
      annotations:
        prometheus.io/scrape: "true"     # Enable scraping
        prometheus.io/port: "8000"       # Metrics port
        prometheus.io/path: "/metrics"   # Metrics endpoint
```

### Metrics Endpoints

Each OptiFlow service exposes metrics at:

| Service | Endpoint | Port |
|---------|----------|------|
| Simulator | `/metrics` | 4850 |
| Gateway | `/api/metrics` | 8080 |
| Backend | `/api/metrics` | 8000 |
| Frontend | `/metrics` | 80 |

### Example: Adding Custom Metric (Python)

```python
from prometheus_client import Counter, Histogram, Gauge

# Counter: Incrementing value (e.g., total requests)
requests_total = Counter(
    'my_service_requests_total',
    'Total requests',
    ['method', 'endpoint']
)

# Histogram: Distribution of values (e.g., latency)
request_duration = Histogram(
    'my_service_request_duration_seconds',
    'Request duration',
    ['endpoint']
)

# Gauge: Current value (e.g., queue size)
queue_size = Gauge(
    'my_service_queue_size',
    'Current queue size'
)

# Usage
requests_total.labels(method='GET', endpoint='/api/data').inc()
request_duration.labels(endpoint='/api/data').observe(0.25)
queue_size.set(42)
```

---

## 🛠️ Troubleshooting

### Prometheus not scraping services

```bash
# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Go to http://localhost:9090/targets

# Check service annotations
kubectl get deployment my-service -o yaml | grep prometheus.io

# Check service discovery
kubectl get pods -n optiflow-prod -l app=backend -o yaml | grep -A5 annotations
```

### Grafana shows "No data"

```bash
# Check datasource
# Grafana → Configuration → Data Sources → Prometheus
# Test connection should show "Data source is working"

# Check Prometheus has data
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Run query: up{job="optiflow-backend"}
# Should return results

# Check time range in Grafana dashboard
# Make sure time range includes recent data
```

### Alerts not firing

```bash
# Check AlertManager is running
kubectl get pods -n monitoring -l app=alertmanager

# Check alert rules loaded in Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Go to http://localhost:9090/rules

# Check AlertManager config
kubectl logs -n monitoring -l app=alertmanager

# Test alert manually
# Prometheus → Alerts → Click alert → "Firing" state
```

### Loki not receiving logs

```bash
# Check Promtail DaemonSet is running on all nodes
kubectl get ds -n monitoring promtail
kubectl get pods -n monitoring -l app=promtail

# Check Promtail logs
kubectl logs -n monitoring -l app=promtail

# Check Loki is running
kubectl get pods -n monitoring -l app=loki
kubectl logs -n monitoring -l app=loki

# Test query in Grafana
# Explore → Loki → {namespace="monitoring"}
```

---

## 📝 Maintenance

### Daily

- ✅ Check Grafana dashboards for anomalies
- ✅ Review alert notifications
- ✅ Verify all services are up (Prometheus targets)

### Weekly

- 📊 Review dashboard metrics trends
- 🔍 Check for unused alerts (too noisy or never fire)
- 💾 Verify storage usage (PVCs)
  ```bash
  kubectl get pvc -n monitoring
  ```

### Monthly

- 🔄 Update monitoring stack images
  ```bash
  # Update Prometheus
  kubectl set image deployment/prometheus \
    prometheus=prom/prometheus:v2.XX.0 -n monitoring

  # Update Grafana
  kubectl set image deployment/grafana \
    grafana=grafana/grafana:XX.X.0 -n monitoring
  ```
- 📈 Review retention policies (adjust if storage is full)
- 🧹 Clean up old dashboards

### Quarterly

- 📊 Review and optimize alert thresholds based on historical data
- 🎯 Add new business metrics and dashboards as needed
- 📚 Update documentation

---

## 🔒 Security Considerations

### 1. Change Default Passwords

```bash
# Grafana admin password
kubectl create secret generic grafana-secrets \
  --from-literal=admin-password='STRONG_PASSWORD' \
  -n monitoring --dry-run=client -o yaml | kubectl apply -f -

kubectl rollout restart deployment/grafana -n monitoring
```

### 2. Enable Authentication

All monitoring services are protected:
- Grafana: Built-in auth (admin user)
- Prometheus: Basic auth via Ingress (optional)
- AlertManager: Basic auth via Ingress

### 3. Use Sealed Secrets

```bash
# Install Sealed Secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Seal your secrets
kubeseal --format yaml < alertmanager-secrets.yaml > alertmanager-secrets-sealed.yaml

# Commit sealed secrets to Git (safe!)
git add alertmanager-secrets-sealed.yaml
```

### 4. Network Policies

Restrict pod-to-pod communication:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: monitoring-network-policy
  namespace: monitoring
spec:
  podSelector:
    matchLabels:
      app: prometheus
  ingress:
    # Only allow Grafana to query Prometheus
    - from:
      - podSelector:
          matchLabels:
            app: grafana
      ports:
        - port: 9090
```

---

## 📚 Additional Resources

- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/
- **Loki Docs**: https://grafana.com/docs/loki/
- **AlertManager Docs**: https://prometheus.io/docs/alerting/latest/alertmanager/
- **PromQL Cheat Sheet**: https://promlabs.com/promql-cheat-sheet/
- **LogQL Cheat Sheet**: https://grafana.com/docs/loki/latest/logql/

---

## 🆘 Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review logs: `kubectl logs -n monitoring -l app=<component>`
3. Contact platform team: platform@optiflow.com
4. Emergency (production down): PagerDuty escalation

---

**Last Updated**: 2025-11-19
**Version**: 1.0.0
**Maintained by**: OptiFlow Platform Team
