# OptiFlow Monitoring Stack - Architecture

## 📊 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         OPTIFLOW PLATFORM                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│  │Simulator │    │ Gateway  │    │ Backend  │    │ Frontend │        │
│  │  :4850   │    │  :8080   │    │  :8000   │    │   :80    │        │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘        │
│       │               │               │               │                │
│       │ /metrics      │ /api/metrics  │ /api/metrics  │ /metrics       │
│       │               │               │               │                │
│       │               │               │               │                │
│       │               │               │               │                │
└───────┼───────────────┼───────────────┼───────────────┼────────────────┘
        │               │               │               │
        │               │               │               │
        ▼               ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      MONITORING NAMESPACE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                       PROMETHEUS :9090                           │  │
│  │  ┌────────────────────────────────────────────────────────┐     │  │
│  │  │ Service Discovery (Kubernetes API)                     │     │  │
│  │  │ • Auto-discover pods with prometheus.io/scrape=true    │     │  │
│  │  │ • Scrape metrics every 15s                             │     │  │
│  │  └────────────────────────────────────────────────────────┘     │  │
│  │                                                                  │  │
│  │  ┌────────────────────────────────────────────────────────┐     │  │
│  │  │ Time-Series Database (TSDB)                            │     │  │
│  │  │ • 30 days retention                                    │     │  │
│  │  │ • 50Gi storage (PVC)                                   │     │  │
│  │  └────────────────────────────────────────────────────────┘     │  │
│  │                                                                  │  │
│  │  ┌────────────────────────────────────────────────────────┐     │  │
│  │  │ Alert Rules Engine                                     │     │  │
│  │  │ • Evaluate rules every 15s                             │     │  │
│  │  │ • Send alerts to AlertManager                          │     │  │
│  │  └────────────────────────────────────────────────────────┘     │  │
│  └──────────────────┬───────────────────────────────────────────────┘  │
│                     │                                                   │
│                     │ Alerts                                            │
│                     ▼                                                   │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                   ALERTMANAGER :9093                             │  │
│  │  ┌────────────────────────────────────────────────────────┐     │  │
│  │  │ Alert Routing                                          │     │  │
│  │  │ • Group by: cluster, severity, alertname               │     │  │
│  │  │ • Route by: severity, team                             │     │  │
│  │  └────────────────────────────────────────────────────────┘     │  │
│  │                                                                  │  │
│  │  ┌────────────────────────────────────────────────────────┐     │  │
│  │  │ Notification Channels                                  │     │  │
│  │  │ • Critical    → PagerDuty (24/7 on-call)              │     │  │
│  │  │ • Warning     → Slack (#alerts)                        │     │  │
│  │  │ • Info        → Email (ops@optiflow.com)              │     │  │
│  │  └────────────────────────────────────────────────────────┘     │  │
│  │                                                                  │  │
│  │  ┌────────────────────────────────────────────────────────┐     │  │
│  │  │ Inhibition Rules                                       │     │  │
│  │  │ • ServiceDown suppresses HighLatency                   │     │  │
│  │  │ • PLCDisconnected suppresses Gateway alerts            │     │  │
│  │  └────────────────────────────────────────────────────────┘     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                         LOKI :3100                               │  │
│  │  ┌────────────────────────────────────────────────────────┐     │  │
│  │  │ Log Storage                                            │     │  │
│  │  │ • Indexes labels, not content (low resource)           │     │  │
│  │  │ • 7 days retention                                     │     │  │
│  │  │ • 30Gi storage (PVC)                                   │     │  │
│  │  └────────────────────────────────────────────────────────┘     │  │
│  └──────────────────▲───────────────────────────────────────────────┘  │
│                     │                                                   │
│                     │ Logs                                              │
│  ┌──────────────────┴───────────────────────────────────────────────┐  │
│  │               PROMTAIL (DaemonSet on each node)                  │  │
│  │  ┌────────────────────────────────────────────────────────┐     │  │
│  │  │ Log Collection                                         │     │  │
│  │  │ • Scrape logs from /var/log/pods                       │     │  │
│  │  │ • Add labels: namespace, pod, app, container           │     │  │
│  │  │ • Stream to Loki                                       │     │  │
│  │  └────────────────────────────────────────────────────────┘     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                       GRAFANA :3000                              │  │
│  │  ┌────────────────────────────────────────────────────────┐     │  │
│  │  │ Data Sources                                           │     │  │
│  │  │ • Prometheus (metrics)  → http://prometheus:9090       │     │  │
│  │  │ • Loki (logs)           → http://loki:3100             │     │  │
│  │  └────────────────────────────────────────────────────────┘     │  │
│  │                                                                  │  │
│  │  ┌────────────────────────────────────────────────────────┐     │  │
│  │  │ Pre-configured Dashboards                              │     │  │
│  │  │ • Platform Overview                                    │     │  │
│  │  │ • Gateway Metrics                                      │     │  │
│  │  │ • Backend Metrics                                      │     │  │
│  │  │ • Kubernetes Cluster                                   │     │  │
│  │  └────────────────────────────────────────────────────────┘     │  │
│  │                                                                  │  │
│  │  ┌────────────────────────────────────────────────────────┐     │  │
│  │  │ Visualization                                          │     │  │
│  │  │ • Time series graphs                                   │     │  │
│  │  │ • Tables                                               │     │  │
│  │  │ • Stats panels                                         │     │  │
│  │  │ • Alerts (on dashboards)                               │     │  │
│  │  └────────────────────────────────────────────────────────┘     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
        │               │               │               │
        │               │               │               │
        ▼               ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL INTEGRATIONS                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  🚨 PagerDuty        📧 Email            💬 Slack                       │
│  (Critical alerts)  (Info alerts)       (Warning alerts)               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

### 1. Metrics Collection Flow

```
OptiFlow Service                Prometheus                  Grafana
     (Pod)                     (Scraper)                 (Visualization)
       │                           │                          │
       │   /metrics endpoint       │                          │
       │◀──────scrape (15s)────────┤                          │
       │                           │                          │
       │   metric samples          │                          │
       ├──────────────────────────▶│                          │
       │                           │                          │
       │                           │  Store in TSDB           │
       │                           │  (50Gi, 30d retention)   │
       │                           │                          │
       │                           │   PromQL query           │
       │                           │◀─────────────────────────┤
       │                           │                          │
       │                           │   query results          │
       │                           ├─────────────────────────▶│
       │                           │                          │
       │                           │                          │  Display
       │                           │                          │  in dashboard
```

### 2. Alerting Flow

```
Prometheus                  AlertManager                External Systems
  (Rules)                   (Routing)                  (Notifications)
     │                           │                          │
     │  Evaluate rules (15s)     │                          │
     │                           │                          │
     │  Threshold crossed        │                          │
     │  (e.g., service down)     │                          │
     │                           │                          │
     │   Send alert              │                          │
     ├──────────────────────────▶│                          │
     │                           │                          │
     │                           │  Group alerts            │
     │                           │  (by cluster, severity)  │
     │                           │                          │
     │                           │  Route by severity       │
     │                           │                          │
     │                           │  Critical alert          │
     │                           ├─────────────────────────▶│ PagerDuty
     │                           │                          │ (page on-call)
     │                           │                          │
     │                           │  Warning alert           │
     │                           ├─────────────────────────▶│ Slack
     │                           │                          │ (#alerts)
     │                           │                          │
     │                           │  Info alert              │
     │                           ├─────────────────────────▶│ Email
     │                           │                          │ (ops@...)
```

### 3. Log Collection Flow

```
Pod Logs                    Promtail                  Loki                Grafana
(/var/log/pods)           (Collector)             (Storage)          (Visualization)
     │                         │                       │                   │
     │  Write logs             │                       │                   │
     │  to stdout/stderr       │                       │                   │
     │                         │                       │                   │
     │  Kubernetes writes      │                       │                   │
     │  to /var/log/pods       │                       │                   │
     │                         │                       │                   │
     │   Tail log files        │                       │                   │
     │◀────────────────────────┤                       │                   │
     │                         │                       │                   │
     │   Log lines + labels    │                       │                   │
     │   (namespace, pod, app) │                       │                   │
     ├────────────────────────▶│                       │                   │
     │                         │                       │                   │
     │                         │  Stream logs          │                   │
     │                         ├──────────────────────▶│                   │
     │                         │                       │                   │
     │                         │                       │  Store (7d)       │
     │                         │                       │  Index labels     │
     │                         │                       │                   │
     │                         │                       │   LogQL query     │
     │                         │                       │◀──────────────────┤
     │                         │                       │                   │
     │                         │                       │   results         │
     │                         │                       ├──────────────────▶│
     │                         │                       │                   │
     │                         │                       │                   │  Display
     │                         │                       │                   │  in Explore
```

---

## 🎯 Service Discovery

Prometheus automatically discovers OptiFlow services using Kubernetes API:

```yaml
# How Prometheus finds services:
scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod                           # ← Discover all pods

    relabel_configs:
      # 1. Only scrape pods with annotation
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true                         # ← prometheus.io/scrape: "true"

      # 2. Use custom port if specified
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\\d+)?;(\\d+)
        replacement: $1:$2
        target_label: __address__           # ← prometheus.io/port: "8000"

      # 3. Use custom path if specified
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__      # ← prometheus.io/path: "/metrics"

      # 4. Add pod labels as metric labels
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
```

**Result**: Any pod with annotations is automatically scraped!

```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8000"
    prometheus.io/path: "/metrics"
```

---

## 🚨 Alert Lifecycle

```
1. METRIC COLLECTED
   ┌─────────────────────────────────────┐
   │ gateway_plc_connected = 1           │
   │ (Gateway connected to PLC)          │
   └─────────────────────────────────────┘
                  │
                  │ Time passes...
                  ▼
2. THRESHOLD CROSSED
   ┌─────────────────────────────────────┐
   │ gateway_plc_connected = 0           │
   │ (PLC connection lost!)              │
   └─────────────────────────────────────┘
                  │
                  │ Prometheus evaluates rule every 15s
                  ▼
3. PENDING STATE
   ┌─────────────────────────────────────┐
   │ Alert: GatewayPLCDisconnected       │
   │ State: PENDING                      │
   │ For: 1m (waiting to confirm)        │
   └─────────────────────────────────────┘
                  │
                  │ Still down after 1 minute
                  ▼
4. FIRING STATE
   ┌─────────────────────────────────────┐
   │ Alert: GatewayPLCDisconnected       │
   │ State: FIRING                       │
   │ Severity: critical                  │
   │ Team: operations                    │
   └─────────────────────────────────────┘
                  │
                  │ Send to AlertManager
                  ▼
5. ALERTMANAGER GROUPING
   ┌─────────────────────────────────────┐
   │ Group alerts by:                    │
   │ • cluster: optiflow-prod            │
   │ • severity: critical                │
   │ • alertname: GatewayPLCDisconnected │
   │                                     │
   │ Wait 10s to collect similar alerts  │
   └─────────────────────────────────────┘
                  │
                  │ Group wait elapsed
                  ▼
6. ROUTE ALERT
   ┌─────────────────────────────────────┐
   │ Match severity: critical            │
   │ Route to: pagerduty-operations      │
   │ Also continue to: slack-operations  │
   └─────────────────────────────────────┘
                  │
                  │ Send notifications
                  ▼
7. NOTIFY
   ┌─────────────────────────────────────┐
   │ 🚨 PagerDuty                        │
   │ → Page on-call engineer             │
   │                                     │
   │ 💬 Slack #ops-alerts                │
   │ → "Gateway plc-003 disconnected"    │
   └─────────────────────────────────────┘
                  │
                  │ Engineer investigates...
                  │ PLC connection restored
                  ▼
8. RESOLVED
   ┌─────────────────────────────────────┐
   │ gateway_plc_connected = 1           │
   │ Alert state: RESOLVED               │
   │                                     │
   │ Notifications sent:                 │
   │ • PagerDuty: Auto-resolve incident  │
   │ • Slack: "✅ Alert resolved"         │
   └─────────────────────────────────────┘
```

---

## 🔐 Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL ACCESS                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Users (Browser) ──▶ NGINX Ingress Controller                          │
│                           │                                             │
│                           │ TLS (cert-manager + Let's Encrypt)          │
│                           │                                             │
│         ┌─────────────────┼─────────────────┐                          │
│         │                 │                 │                          │
│         ▼                 ▼                 ▼                          │
│  grafana.optiflow  prometheus.optiflow  alertmanager.optiflow          │
│  (Built-in auth)   (Basic auth)        (Basic auth)                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                           │
                           │ Ingress routes to Services
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      MONITORING NAMESPACE (Internal)                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐           │
│  │    Grafana     │  │  Prometheus    │  │ AlertManager   │           │
│  │   Service      │  │   Service      │  │   Service      │           │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘           │
│           │                   │                   │                    │
│           │                   │                   │                    │
│  ┌────────▼───────┐  ┌────────▼───────┐  ┌────────▼───────┐           │
│  │    Grafana     │  │  Prometheus    │  │ AlertManager   │           │
│  │     Pod        │  │     Pod        │  │     Pod        │           │
│  │                │  │                │  │                │           │
│  │  Secrets:      │  │  ServiceAccount│  │  Secrets:      │           │
│  │  - admin pwd   │  │  RBAC for K8s  │  │  - SMTP pwd    │           │
│  │                │  │  API access    │  │  - Slack URL   │           │
│  │                │  │                │  │  - PagerDuty   │           │
│  └────────────────┘  └────────────────┘  └────────────────┘           │
│                                                                         │
│  Network Policies:                                                     │
│  • Prometheus can scrape all pods                                      │
│  • Grafana can query Prometheus + Loki                                 │
│  • AlertManager can send external webhooks                             │
│  • Promtail can read pod logs                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Security Layers

1. **Network Isolation**
   - Monitoring namespace separate from application namespaces
   - Network policies restrict pod-to-pod communication
   - Only necessary ports exposed

2. **Authentication**
   - Grafana: Username/password (admin/optiflow123 - CHANGE IN PROD!)
   - Prometheus: Optional basic auth via Ingress annotations
   - AlertManager: Basic auth via Ingress annotations

3. **TLS/SSL**
   - Ingress with cert-manager for automatic Let's Encrypt certificates
   - All external traffic encrypted

4. **Secrets Management**
   - Kubernetes Secrets for credentials
   - Recommended: Sealed Secrets for GitOps
   - Recommended: External Secrets Operator for cloud integration

5. **RBAC**
   - ServiceAccount for Prometheus with read-only access to K8s API
   - ServiceAccount for Promtail to read pod logs
   - Minimal permissions (principle of least privilege)

---

## 📊 Storage Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PERSISTENT VOLUME CLAIMS (PVCs)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  prometheus-pvc (50Gi)                                         │    │
│  │  ┌──────────────────────────────────────────────────────┐     │    │
│  │  │ Time-Series Database (TSDB)                          │     │    │
│  │  │                                                       │     │    │
│  │  │  /prometheus/chunks/                                 │     │    │
│  │  │  ├── 00001.chunk   (day 1-7)    ~15Gi              │     │    │
│  │  │  ├── 00002.chunk   (day 8-14)   ~15Gi              │     │    │
│  │  │  ├── 00003.chunk   (day 15-21)  ~15Gi              │     │    │
│  │  │  └── 00004.chunk   (day 22-30)  ~5Gi               │     │    │
│  │  │                                                       │     │    │
│  │  │  Retention: 30 days                                  │     │    │
│  │  │  Compaction: 2h blocks → 24h blocks                 │     │    │
│  │  └──────────────────────────────────────────────────────┘     │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  loki-pvc (30Gi)                                               │    │
│  │  ┌──────────────────────────────────────────────────────┐     │    │
│  │  │ Log Storage (BoltDB + Filesystem)                    │     │    │
│  │  │                                                       │     │    │
│  │  │  /loki/chunks/                                       │     │    │
│  │  │  ├── index_YYYYMMDD  (label indexes)    ~2Gi        │     │    │
│  │  │  └── chunks/         (log content)       ~28Gi       │     │    │
│  │  │      └── compressed with gzip                        │     │    │
│  │  │                                                       │     │    │
│  │  │  Retention: 7 days                                   │     │    │
│  │  │  Compression: ~10:1 ratio                            │     │    │
│  │  └──────────────────────────────────────────────────────┘     │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  grafana-pvc (10Gi)                                            │    │
│  │  ┌──────────────────────────────────────────────────────┐     │    │
│  │  │ Dashboard & Configuration Storage                    │     │    │
│  │  │                                                       │     │    │
│  │  │  /var/lib/grafana/                                   │     │    │
│  │  │  ├── dashboards/     (JSON files)        ~500Mi      │     │    │
│  │  │  ├── plugins/        (installed plugins) ~200Mi      │     │    │
│  │  │  ├── grafana.db      (SQLite metadata)   ~100Mi      │     │    │
│  │  │  └── png/            (rendered images)   ~200Mi      │     │    │
│  │  │                                                       │     │    │
│  │  │  Retention: Permanent                                │     │    │
│  │  └──────────────────────────────────────────────────────┘     │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  alertmanager-pvc (5Gi)                                        │    │
│  │  ┌──────────────────────────────────────────────────────┐     │    │
│  │  │ Alert State & Silences                               │     │    │
│  │  │                                                       │     │    │
│  │  │  /alertmanager/                                      │     │    │
│  │  │  ├── nflog          (notification log)   ~1Gi        │     │    │
│  │  │  └── silences       (active silences)    ~100Mi      │     │    │
│  │  │                                                       │     │    │
│  │  │  Retention: 5 days                                   │     │    │
│  │  └──────────────────────────────────────────────────────┘     │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  TOTAL: ~95Gi                                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Scalability

### Current Architecture (Single Instance)

```
Prometheus:  1 replica  →  Can handle ~10-20 services, 5,000 metrics/sec
Grafana:     1 replica  →  Can handle ~100 concurrent users
Loki:        1 replica  →  Can handle ~5 MB/s log ingestion
AlertManager: 1 replica →  Single point of failure (acceptable for dev/staging)
```

### Scaled Architecture (Production)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Prometheus (Federation)                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │ Prometheus      │  │ Prometheus      │  │ Prometheus      │    │
│  │ (cluster 1)     │  │ (cluster 2)     │  │ (cluster 3)     │    │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘    │
│           │                    │                    │              │
│           └────────────────────┼────────────────────┘              │
│                                │                                   │
│                    ┌───────────▼───────────┐                       │
│                    │  Prometheus           │                       │
│                    │  (Global/Federation)  │                       │
│                    │  • Aggregates metrics │                       │
│                    │  • Long-term storage  │                       │
│                    └───────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Loki (Distributed)                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │ Ingester        │  │ Querier         │  │ Compactor       │    │
│  │ (writes)        │  │ (reads)         │  │ (compression)   │    │
│  │ 3 replicas      │  │ 2 replicas      │  │ 1 replica       │    │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘    │
│           │                    │                    │              │
│           └────────────────────┼────────────────────┘              │
│                                │                                   │
│                    ┌───────────▼───────────┐                       │
│                    │  S3 / Object Storage  │                       │
│                    │  (long-term storage)  │                       │
│                    └───────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Grafana (HA)                                                       │
│  ┌─────────────────┐  ┌─────────────────┐                          │
│  │ Grafana         │  │ Grafana         │                          │
│  │ (instance 1)    │  │ (instance 2)    │                          │
│  └────────┬────────┘  └────────┬────────┘                          │
│           │                    │                                   │
│           │    ┌───────────────┴──────────┐                        │
│           └────┤  PostgreSQL (shared DB)  │                        │
│                └──────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📚 Related Documentation

- **[README.md](README.md)** - Full deployment guide, configuration, troubleshooting
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick commands and queries cheat sheet
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - This file (architecture deep dive)

---

**Last Updated**: 2025-11-19
**Architecture Version**: 1.0.0
**Maintained by**: OptiFlow Platform Team
