# OptiFlow Monitoring - Quick Reference Card

## 🚀 One-Command Setup

```bash
# Deploy entire monitoring stack
./scripts/setup/setup-monitoring.sh

# Access Grafana (main UI)
kubectl port-forward -n monitoring svc/grafana 3000:3000
# → http://localhost:3000 (admin / optiflow123)
```

---

## 📊 Stack Overview

| Component | Purpose | Port | Storage |
|-----------|---------|------|---------|
| **Prometheus** | Metrics (30d) | 9090 | 50Gi |
| **Grafana** | Dashboards | 3000 | 10Gi |
| **Loki** | Logs (7d) | 3100 | 30Gi |
| **Promtail** | Log collector | - | - |
| **AlertManager** | Alerting | 9093 | 5Gi |

---

## 🔍 Most Useful Commands

```bash
# === ACCESS ===
kubectl port-forward -n monitoring svc/grafana 3000:3000        # Grafana
kubectl port-forward -n monitoring svc/prometheus 9090:9090     # Prometheus
kubectl port-forward -n monitoring svc/alertmanager 9093:9093   # AlertManager

# === STATUS ===
kubectl get pods -n monitoring                                  # All pods
kubectl get pvc -n monitoring                                   # Storage usage
kubectl top pods -n monitoring                                  # Resource usage

# === LOGS ===
kubectl logs -n monitoring -l app=prometheus --tail=100         # Prometheus logs
kubectl logs -n monitoring -l app=grafana --tail=100            # Grafana logs
kubectl logs -n monitoring -l app=loki --tail=100               # Loki logs
kubectl logs -n monitoring -l app=alertmanager --tail=100       # AlertManager logs
kubectl logs -n monitoring -l app=promtail --tail=100           # Promtail logs

# === RESTART ===
kubectl rollout restart deployment/prometheus -n monitoring
kubectl rollout restart deployment/grafana -n monitoring
kubectl rollout restart deployment/loki -n monitoring
kubectl rollout restart deployment/alertmanager -n monitoring
kubectl rollout restart daemonset/promtail -n monitoring

# === UNINSTALL ===
kubectl delete namespace monitoring                             # Remove everything
```

---

## 📈 Pre-configured Dashboards

Access via Grafana → Dashboards

1. **Platform Overview** - Service health, request rate, errors, latency
2. **Gateway Metrics** - PLC status, buffer usage, Kafka publish rate
3. **Backend Metrics** - API requests, Kafka lag, DB connections, InfluxDB
4. **Kubernetes Cluster** - Node CPU/memory, pods, disk, network

---

## 🚨 Critical Alerts

| Alert | Threshold | Action |
|-------|-----------|--------|
| **ServiceDown** | 2 minutes down | 🚨 PagerDuty + Slack |
| **GatewayPLCDisconnected** | PLC offline 1m | 🚨 PagerDuty (ops) |
| **DatabaseConnectionPoolExhausted** | >90% for 2m | 🚨 PagerDuty + Slack |
| **DiskSpaceLow** | <10% for 5m | 🚨 PagerDuty + Email |
| **NoDataIngestion** | No data 10m | 🚨 PagerDuty (ops) |
| **GatewayBufferFull** | >90% for 5m | ⚠️ Slack (ops) |
| **KafkaConsumerLag** | >10k msgs 5m | ⚠️ Slack (platform) |
| **HighCPUUsage** | >80% for 10m | ⚠️ Slack (platform) |

---

## 🔍 Useful Queries

### PromQL (Prometheus)

```promql
# Service uptime
up{job=~"optiflow-.*"}

# Request rate
rate(http_requests_total{job="optiflow-backend"}[5m])

# Error rate (%)
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100

# p95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Gateway PLC connections
count(gateway_plc_connected == 1)

# Kafka consumer lag
kafka_consumer_lag

# Memory usage
process_resident_memory_bytes{job="optiflow-backend"}
```

### LogQL (Loki via Grafana)

```logql
# All logs from backend
{namespace="optiflow-prod", app="backend"}

# Error logs only
{namespace="optiflow-prod"} |= "ERROR"

# Gateway PLC disconnection
{app="gateway"} |= "PLC disconnected"

# API 500 errors
{app="backend"} | json | status="500"

# Error rate per minute
sum(rate({namespace="optiflow-prod"} |= "ERROR" [1m]))
```

---

## 🔧 Enable Metrics in Your Service

### 1. Add Kubernetes Annotations

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service
spec:
  template:
    metadata:
      annotations:
        prometheus.io/scrape: "true"     # ← Enable Prometheus scraping
        prometheus.io/port: "8000"       # ← Metrics port
        prometheus.io/path: "/metrics"   # ← Metrics endpoint
```

### 2. Expose Metrics Endpoint (Python Example)

```python
from prometheus_client import Counter, Histogram, make_asgi_app
from fastapi import FastAPI

app = FastAPI()

# Add Prometheus middleware
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Define metrics
requests_total = Counter('http_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'Request duration')

# Use in your code
@app.get("/api/data")
async def get_data():
    requests_total.labels(method='GET', endpoint='/api/data').inc()
    with request_duration.time():
        # Your logic here
        return {"data": "..."}
```

### 3. Verify Metrics

```bash
# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# → http://localhost:9090/targets
# Your service should appear in the list

# Test metrics endpoint
kubectl port-forward -n optiflow-prod svc/my-service 8000:8000
curl http://localhost:8000/metrics
```

---

## 🔔 Configure Alerting

### 1. Edit AlertManager Secrets

```bash
kubectl edit secret alertmanager-secrets -n monitoring
```

Add your credentials (base64 encoded):
- `SMTP_PASSWORD` - Email alerts
- `SLACK_WEBHOOK_URL` - Slack notifications
- `PAGERDUTY_SERVICE_KEY_*` - PagerDuty integration

### 2. Restart AlertManager

```bash
kubectl rollout restart deployment/alertmanager -n monitoring
```

### 3. Test Alert

```bash
# Send test alert via Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# → http://localhost:9090/alerts
# Click any alert → manually set to "Firing"
```

---

## 🔒 Security Checklist

- [ ] Change Grafana admin password
  ```bash
  kubectl create secret generic grafana-secrets \
    --from-literal=admin-password='STRONG_PASSWORD' \
    -n monitoring --dry-run=client -o yaml | kubectl apply -f -
  kubectl rollout restart deployment/grafana -n monitoring
  ```

- [ ] Configure AlertManager credentials (SMTP, Slack, PagerDuty)

- [ ] Enable TLS for Ingress (cert-manager + Let's Encrypt)

- [ ] Use Sealed Secrets for GitOps
  ```bash
  kubeseal --format yaml < secrets.yaml > secrets-sealed.yaml
  ```

- [ ] Add basic auth to Prometheus/AlertManager Ingress

- [ ] Configure Network Policies to restrict pod-to-pod traffic

---

## 🐛 Common Issues

### Grafana shows "No data"

```bash
# 1. Check datasource connection
# Grafana → Configuration → Data Sources → Prometheus → Test
# Should show "Data source is working"

# 2. Check Prometheus has data
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Query: up{job="optiflow-backend"}

# 3. Check service annotations
kubectl get deployment my-service -o yaml | grep prometheus.io
```

### Alerts not firing

```bash
# 1. Check alert rules loaded
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# → http://localhost:9090/rules

# 2. Check AlertManager config
kubectl logs -n monitoring -l app=alertmanager | grep -i error

# 3. Verify metric threshold crossed
# Prometheus → Graph → Run alert query
# E.g., up{job="optiflow-backend"} == 0
```

### Loki not receiving logs

```bash
# 1. Check Promtail pods running on all nodes
kubectl get pods -n monitoring -l app=promtail -o wide

# 2. Check Promtail logs
kubectl logs -n monitoring -l app=promtail | grep -i error

# 3. Test Loki query in Grafana
# Explore → Loki → {namespace="monitoring"}
```

### High storage usage

```bash
# 1. Check PVC usage
kubectl get pvc -n monitoring
kubectl exec -n monitoring -it <prometheus-pod> -- df -h /prometheus

# 2. Reduce retention period (if needed)
# Edit prometheus.yaml → --storage.tsdb.retention.time=15d
# Default is 30d

# 3. For Loki, edit retention in loki.yaml
# retention_period: 168h (7 days → adjust as needed)
```

---

## 📊 Storage Requirements

| Component | Size | Retention | Can Reduce? |
|-----------|------|-----------|-------------|
| Prometheus | 50Gi | 30 days | ✅ Yes (15d = ~25Gi) |
| Loki | 30Gi | 7 days | ✅ Yes (3d = ~15Gi) |
| Grafana | 10Gi | Permanent | ⚠️ Dashboards only |
| AlertManager | 5Gi | 5 days | ⚠️ Alert history |

**Total**: ~95Gi (can reduce to ~55Gi with shorter retention)

---

## 🎯 Performance Tips

1. **Scrape intervals** (Prometheus): 15s default, increase to 30s for less critical metrics
2. **Evaluation intervals** (Alerts): 15s default, increase to 30s if alert volume is high
3. **Log sampling** (Promtail): Sample logs at 50% for high-volume services
4. **Dashboard refresh**: Use 30s-60s refresh instead of 5s
5. **Query optimization**: Use `rate()` over `irate()`, avoid regex when possible

---

## 📚 Resources

- **Full Documentation**: [monitoring/README.md](README.md)
- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/
- **PromQL Cheat Sheet**: https://promlabs.com/promql-cheat-sheet/
- **LogQL Cheat Sheet**: https://grafana.com/docs/loki/latest/logql/

---

**Last Updated**: 2025-11-19
**Quick Help**: `kubectl get pods -n monitoring` or check [README.md](README.md)
