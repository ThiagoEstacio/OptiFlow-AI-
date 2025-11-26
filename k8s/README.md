# OptiFlow Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the OptiFlow platform.

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3 (optional, for some components)
- Storage class configured (for PVCs)

## Quick Start

```bash
# Create namespaces
kubectl apply -f k8s/base/namespace.yaml

# Create secrets (edit first with your values)
kubectl apply -f k8s/base/secrets.yaml

# Deploy infrastructure
kubectl apply -f k8s/redis/
kubectl apply -f k8s/kafka/
kubectl apply -f k8s/influxdb/

# Wait for infrastructure to be ready
kubectl wait --for=condition=ready pod -l app=redis -n optiflow --timeout=120s
kubectl wait --for=condition=ready pod -l app=kafka -n optiflow --timeout=180s
kubectl wait --for=condition=ready pod -l app=influxdb -n optiflow --timeout=120s

# Deploy applications
kubectl apply -f k8s/backend/
kubectl apply -f k8s/gateway/

# Deploy monitoring (optional)
kubectl apply -f k8s/monitoring/

# Check status
kubectl get pods -n optiflow
```

## Directory Structure

```
k8s/
├── base/                 # Namespaces, common configs
│   ├── namespace.yaml
│   └── secrets.yaml      # (create from template)
├── backend/              # OptiFlow Backend API
│   ├── deployment.yaml
│   ├── configmap.yaml
│   └── secrets.yaml.template
├── gateway/              # Gateway (edge device)
│   ├── deployment.yaml
│   ├── configmap.yaml
│   └── service.yaml
├── kafka/                # Kafka cluster
│   └── statefulset.yaml
├── influxdb/             # InfluxDB time-series DB
│   └── statefulset.yaml
├── redis/                # Redis cache
│   └── deployment.yaml
└── monitoring/           # Prometheus + Grafana
    ├── prometheus/
    └── grafana/
```

## Components

### Backend (optiflow-backend)
- FastAPI application
- 2 replicas with HPA (auto-scaling)
- Health checks at `/api/health`
- Prometheus metrics at `/api/v1/metrics`

### Gateway (optiflow-gateway)
- Industrial protocol adapter (OPC-UA, Modbus)
- Single replica per edge location
- Publishes to Kafka

### Kafka
- 3-node KRaft cluster (no Zookeeper)
- Persistent storage (10Gi per node)
- Topics: raw_tags, raw_tags_dlq

### InfluxDB
- Time-series database
- Persistent storage (50Gi)
- Buckets: timeseries, aggregations

### Redis
- Cache for realtime values
- Persistent storage (5Gi)

## Configuration

### Environment Variables

Copy the secrets template and edit:
```bash
cp k8s/base/secrets.yaml.template k8s/base/secrets.yaml
# Edit with your values
kubectl apply -f k8s/base/secrets.yaml
```

### ConfigMaps

Edit `k8s/backend/configmap.yaml` for:
- Kafka bootstrap servers
- InfluxDB URL
- Gateway URL
- Consumer settings

## Scaling

### Backend HPA
```bash
# View current HPA status
kubectl get hpa -n optiflow

# Manual scale
kubectl scale deployment optiflow-backend --replicas=3 -n optiflow
```

### Kafka
```bash
# Scale Kafka brokers
kubectl scale statefulset kafka --replicas=5 -n optiflow
```

## Monitoring

### Prometheus Metrics

Backend: `http://optiflow-backend:8000/api/v1/metrics`
Gateway: `http://optiflow-gateway:8080/metrics`

### Grafana Dashboards

Access Grafana:
```bash
kubectl port-forward svc/grafana 3000:3000 -n optiflow-monitoring
# Open http://localhost:3000
```

## Troubleshooting

### Check pod logs
```bash
kubectl logs -f deployment/optiflow-backend -n optiflow
kubectl logs -f deployment/optiflow-gateway -n optiflow
```

### Check events
```bash
kubectl get events -n optiflow --sort-by='.lastTimestamp'
```

### Debug pod
```bash
kubectl exec -it deployment/optiflow-backend -n optiflow -- /bin/bash
```

### Pipeline health
```bash
kubectl exec -it deployment/optiflow-backend -n optiflow -- \
  curl -s http://localhost:8000/api/v1/metrics/pipeline | jq
```

## Production Considerations

1. **Secrets Management**: Use external secrets (Vault, AWS Secrets Manager)
2. **Ingress**: Configure TLS with cert-manager
3. **Network Policies**: Restrict pod-to-pod communication
4. **Resource Quotas**: Set namespace limits
5. **Backup**: Configure InfluxDB and Kafka backups
6. **Monitoring**: Set up alerts in Prometheus/Grafana
