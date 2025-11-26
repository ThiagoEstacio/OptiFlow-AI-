# 🏗️ OptiFlow - Guia de Infraestrutura e Manutenção

**Versão**: 1.0.0
**Data**: 2025-01-19

---

## 📁 Estrutura de Diretórios

```
optiflow-platform/
├── services/                  # Microserviços
│   ├── simulator/
│   ├── gateway/
│   ├── backend/
│   └── frontend/
│
├── infrastructure/            # Infraestrutura como código
│   ├── kubernetes/           # K8s manifests
│   ├── terraform/            # Provisioning
│   ├── helm/                 # Helm charts
│   └── argocd/               # GitOps
│
├── shared/                    # Código compartilhado
├── scripts/                   # Automação
├── tests/                     # Testes integração
└── docs/                      # Documentação
```

---

## 🎯 Decisões de Arquitetura

### 1. Repositório

**Decisão**: **Monorepo** (inicialmente)

**Justificativa**:
- ✅ Refactoring cross-service fácil
- ✅ CI/CD centralizado
- ✅ Versionamento sincronizado
- ✅ Ideal para time < 10 devs

**Migração para Multirepo**:
- Quando time > 10 devs
- Quando deploy frequency > 10x/dia
- Quando serviços tem owners diferentes

### 2. Orquestração

| Ambiente | Solução | Justificativa |
|----------|---------|---------------|
| **Dev Local** | Docker Compose | Simplicidade, setup rápido |
| **Staging** | Kubernetes (K3s) | Paridade com produção |
| **Production** | Kubernetes (EKS/AKS/GKE) | Escalabilidade, auto-healing |
| **Edge (Gateway)** | K3s ou Docker | Lightweight, edge devices |

### 3. Frontend/Backend

**Decisão**: **Completamente separados**

```
Frontend (SPA)                Backend (API)
├── React + TypeScript        ├── FastAPI + Python
├── NGINX container           ├── Gunicorn + Uvicorn
├── K8s Deployment            ├── K8s Deployment
├── HPA (CPU-based)           ├── HPA (Request-based)
└── CDN (CloudFront)          └── Internal only
```

**Comunicação**:
- Frontend → Backend: HTTP REST API
- Frontend → Gateway: WebSocket (alarmes)
- Backend → Gateway: Kafka (ingestão)

---

## 🚀 Deployment Strategy

### Ambientes

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Development  │──▶│   Staging    │──▶│  Production  │
│ (Local)      │   │  (Cloud K8s) │   │  (Cloud K8s) │
└──────────────┘   └──────────────┘   └──────────────┘
Docker Compose     K3s/Minikube       EKS/AKS/GKE

Auto-deploy:       Auto-deploy:       Manual approval
✅ On commit       ✅ On merge main   ❌ (GitOps)
```

### GitOps com ArgoCD

```
┌─────────────────────────────────────────────────────┐
│                   Git Repository                    │
│  infrastructure/kubernetes/*.yaml                   │
└──────────────────┬──────────────────────────────────┘
                   │ Git push
                   ▼
┌─────────────────────────────────────────────────────┐
│                    ArgoCD                           │
│  - Monitors Git repo                                │
│  - Detects changes                                  │
│  - Auto-applies to K8s                              │
└──────────────────┬──────────────────────────────────┘
                   │ kubectl apply
                   ▼
┌─────────────────────────────────────────────────────┐
│              Kubernetes Cluster                     │
│  - Simulator, Gateway, Backend, Frontend            │
│  - Auto-healing, Auto-scaling                       │
└─────────────────────────────────────────────────────┘
```

**Benefícios**:
- ✅ **Single source of truth**: Git é a fonte da verdade
- ✅ **Auditability**: Todo deploy é um commit Git
- ✅ **Rollback fácil**: git revert + ArgoCD sync
- ✅ **Self-healing**: ArgoCD detecta drift e corrige

### Deployment Patterns

| Serviço | Strategy | Reason |
|---------|----------|--------|
| **Simulator** | Recreate | Stateless, dev only |
| **Gateway** | Rolling Update | Stateful (buffer), zero downtime |
| **Backend** | Blue-Green | Database migrations, zero downtime |
| **Frontend** | Rolling Update | Stateless, fast rollout |

---

## 📊 Monitoramento

### Stack Completo

```
┌────────────────────────────────────────────────────────┐
│                  OBSERVABILITY                         │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Metrics (Prometheus)                                 │
│  ├─ gateway_api_latency_seconds                       │
│  ├─ backend_kafka_consumer_lag                        │
│  ├─ gateway_plc_connected                             │
│  └─ http_requests_total                               │
│                                                        │
│  Logs (Loki)                                          │
│  ├─ Structured JSON logs                              │
│  ├─ Label extraction                                  │
│  └─ Retention: 30 days                                │
│                                                        │
│  Traces (Jaeger)                                      │
│  ├─ Request → Gateway → Kafka → Backend              │
│  ├─ Latency breakdown                                 │
│  └─ Error tracing                                     │
│                                                        │
│  Visualization (Grafana)                              │
│  ├─ Platform Overview dashboard                       │
│  ├─ Service-specific dashboards                       │
│  └─ Business metrics dashboards                       │
│                                                        │
│  Alerting (AlertManager)                              │
│  ├─ PagerDuty (critical)                              │
│  ├─ Slack (warnings)                                  │
│  └─ Email (info)                                      │
└────────────────────────────────────────────────────────┘
```

### Dashboards Principais

#### 1. Platform Overview

```
┌─────────────────────────────────────────────────────┐
│ OptiFlow Platform - Overview                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Service Health                                      │
│ ├─ Simulator:  ✅ UP    (1/1 pods)                 │
│ ├─ Gateway:    ✅ UP    (3/3 pods)                 │
│ ├─ Backend:    ✅ UP    (5/5 pods)                 │
│ └─ Frontend:   ✅ UP    (2/2 pods)                 │
│                                                     │
│ Key Metrics (Last 5 min)                            │
│ ├─ Requests:   12.5k req/s                         │
│ ├─ Latency:    24ms (p95)                          │
│ ├─ Errors:     0.02%                               │
│ └─ Data:       150 MB/s ingested                   │
│                                                     │
│ Infrastructure                                      │
│ ├─ CPU:        45% (12/20 cores)                   │
│ ├─ Memory:     60% (24/40 GB)                      │
│ ├─ Disk:       30% (300/1000 GB)                   │
│ └─ Network:    2.5 Gbps                            │
│                                                     │
│ Active Alerts                                       │
│ ⚠️  Gateway buffer high (gateway-002) - WARNING    │
└─────────────────────────────────────────────────────┘
```

#### 2. Gateway Dashboard

```
┌─────────────────────────────────────────────────────┐
│ Gateway Metrics                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│ PLC Connections                                     │
│ ├─ Connected:   5/5 PLCs ✅                        │
│ ├─ Uptime:      99.98%                             │
│ └─ Last disconnect: 2h ago (plc-003)               │
│                                                     │
│ API Performance                                     │
│ ├─ Latency p50: 8ms                                │
│ ├─ Latency p95: 24ms                               │
│ ├─ Latency p99: 45ms                               │
│ └─ Requests:    5k req/s                           │
│                                                     │
│ Data Ingestion                                      │
│ ├─ Tags/sec:    5,000 tags/s                       │
│ ├─ Kafka pub:   4,980 msg/s (99.6% success)        │
│ └─ Buffer:      120 MB (12% full)                  │
│                                                     │
│ Alarms                                              │
│ ├─ Active:      3 alarms                           │
│ ├─ Quality:     2 bad quality                      │
│ └─ WebSocket:   15 clients connected               │
└─────────────────────────────────────────────────────┘
```

### Alerting Rules

| Alert | Severity | Threshold | Action |
|-------|----------|-----------|--------|
| ServiceDown | Critical | > 2 min | PagerDuty |
| GatewayPLCDisconnected | Critical | > 1 min | PagerDuty |
| HighErrorRate | Warning | > 5% | Slack |
| HighCPUUsage | Warning | > 80% | Slack |
| KafkaConsumerLag | Warning | > 10k | Slack |
| DiskSpaceLow | Critical | < 10% | PagerDuty |
| NoDataIngestion | Critical | > 10 min | PagerDuty |

---

## 🔧 Manutenção

### Rotinas Diárias

```bash
# 1. Verificar health de todos os serviços
kubectl get pods -n optiflow-prod

# 2. Verificar alertas ativos
curl http://alertmanager:9093/api/v2/alerts

# 3. Verificar métricas chave
curl http://prometheus:9090/api/v1/query?query=up

# 4. Verificar logs de erro (últimas 1h)
kubectl logs -n optiflow-prod -l app=backend --since=1h | grep ERROR
```

### Rotinas Semanais

```bash
# 1. Backup databases
./scripts/maintenance/backup-db.sh

# 2. Cleanup old images
./scripts/maintenance/cleanup-old-images.sh

# 3. Review Grafana dashboards
open http://grafana.optiflow.local

# 4. Review capacidade e scaling
kubectl top nodes
kubectl top pods -n optiflow-prod
```

### Rotinas Mensais

```bash
# 1. Update dependencies
./scripts/maintenance/update-dependencies.sh

# 2. Review security vulnerabilities
trivy image optiflow-backend:latest

# 3. Review costs (cloud bill)
# AWS: CloudWatch + Cost Explorer
# Azure: Cost Management
# GCP: Billing Reports

# 4. Review SLA metrics
# Uptime, Latency, Error rate
```

---

## 🚨 Incident Response

### Runbook: Service Down

```bash
# 1. Identificar serviço afetado
kubectl get pods -n optiflow-prod
# Exemplo: backend-5d7f8c9b4-xyz → CrashLoopBackOff

# 2. Verificar logs
kubectl logs -n optiflow-prod backend-5d7f8c9b4-xyz --tail=100

# 3. Verificar events
kubectl describe pod -n optiflow-prod backend-5d7f8c9b4-xyz

# 4. Verificar recursos
kubectl top pod -n optiflow-prod backend-5d7f8c9b4-xyz

# 5. Restart pod (quick fix)
kubectl delete pod -n optiflow-prod backend-5d7f8c9b4-xyz

# 6. Rollback deploy (se novo deploy causou)
kubectl rollout undo deployment/backend -n optiflow-prod

# 7. Escalar horizontalmente (se sobrecarga)
kubectl scale deployment backend --replicas=10 -n optiflow-prod
```

### Runbook: Gateway PLC Disconnected

```bash
# 1. Verificar logs do Gateway
kubectl logs -n optiflow-prod -l app=gateway --tail=100 | grep "plc-003"

# 2. Verificar configuração do adapter
kubectl get configmap gateway-config -n optiflow-prod -o yaml

# 3. Testar conectividade PLC
kubectl exec -n optiflow-prod gateway-xxx -- telnet 192.168.1.10 4840

# 4. Verificar se PLC está online (ping)
kubectl exec -n optiflow-prod gateway-xxx -- ping -c 3 192.168.1.10

# 5. Verificar logs do PLC (se acesso disponível)
# ssh plc-003
# tail -f /var/log/opcua.log

# 6. Restart Gateway pod (reconectar)
kubectl delete pod -n optiflow-prod gateway-xxx
```

### Runbook: High Kafka Consumer Lag

```bash
# 1. Verificar lag atual
kubectl exec -n optiflow-prod kafka-0 -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group backend-consumer

# 2. Verificar se Backend consumer está rodando
kubectl logs -n optiflow-prod -l app=backend | grep "Kafka consumer"

# 3. Escalar Backend horizontalmente
kubectl scale deployment backend --replicas=10 -n optiflow-prod

# 4. Verificar InfluxDB (pode ser gargalo)
kubectl exec -n optiflow-prod influxdb-0 -- influx ping

# 5. Aumentar partitions Kafka (se necessário)
kubectl exec -n optiflow-prod kafka-0 -- kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --alter --topic raw_tags --partitions 10
```

---

## 🔐 Security

### Secrets Management

**Opção 1: Kubernetes Secrets** (básico)

```bash
# Create secret
kubectl create secret generic backend-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=influxdb-token="..." \
  -n optiflow-prod

# Use in deployment
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: backend-secrets
        key: database-url
```

**Opção 2: Sealed Secrets** (GitOps-friendly)

```bash
# Install Sealed Secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Create sealed secret (pode commitar no Git!)
echo -n "my-secret-value" | kubectl create secret generic my-secret \
  --dry-run=client --from-file=key=/dev/stdin -o yaml | \
  kubeseal -o yaml > sealed-secret.yaml

# Apply
kubectl apply -f sealed-secret.yaml
```

**Opção 3: External Secrets Operator** (produção recomendado)

```yaml
# Integra com AWS Secrets Manager, Azure Key Vault, etc.
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: backend-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: backend-secrets
  data:
    - secretKey: database-url
      remoteRef:
        key: optiflow/backend/database-url
```

### Network Policies

```yaml
# Restringe comunicação entre pods
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
  namespace: optiflow-prod
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # Allow from Frontend only
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 8000
  egress:
    # Allow to PostgreSQL
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
    # Allow to InfluxDB
    - to:
        - podSelector:
            matchLabels:
              app: influxdb
      ports:
        - protocol: TCP
          port: 8086
```

---

## 📈 Scaling

### Horizontal Pod Autoscaler (HPA)

```yaml
# Gateway HPA (based on custom metric: Kafka lag)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gateway-hpa
  namespace: optiflow-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gateway
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: gateway_kafka_publish_lag
        target:
          type: AverageValue
          averageValue: "1000"

---
# Backend HPA (based on requests)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: optiflow-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"
```

### Vertical Pod Autoscaler (VPA)

```yaml
# Ajusta CPU/Memory automaticamente
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: backend-vpa
  namespace: optiflow-prod
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  updatePolicy:
    updateMode: "Auto"  # Recreate|Initial|Off
  resourcePolicy:
    containerPolicies:
      - containerName: backend
        minAllowed:
          cpu: 500m
          memory: 1Gi
        maxAllowed:
          cpu: 4000m
          memory: 8Gi
```

---

## 💰 Cost Optimization

### Kubernetes Resources

```yaml
# Define requests/limits para todos os pods
resources:
  requests:     # Minimum guaranteed
    cpu: 500m
    memory: 1Gi
  limits:       # Maximum allowed
    cpu: 2000m
    memory: 4Gi
```

**Cálculo de custos** (AWS EKS exemplo):

| Componente | Qty | vCPU | RAM | Cost/month |
|------------|-----|------|-----|------------|
| EKS Control Plane | 1 | - | - | $73 |
| Worker Nodes (t3.large) | 5 | 2 | 8GB | $370 |
| RDS PostgreSQL (db.t3.medium) | 1 | 2 | 4GB | $70 |
| ElastiCache Redis (cache.t3.medium) | 1 | 2 | 3.2GB | $50 |
| MSK Kafka (kafka.m5.large) | 3 | 2 | 8GB | $450 |
| InfluxDB (t3.xlarge) | 1 | 4 | 16GB | $150 |
| **TOTAL** | | | | **$1,163/mês** |

**Economia com Spot Instances**:
- Worker Nodes (Spot): -70% = $111
- **Total com Spot**: $904/mês (**-22%**)

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/backend-ci.yml
name: Backend CI/CD

on:
  push:
    branches: [main, staging]
    paths:
      - 'services/backend/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd services/backend
          pip install -r requirements.txt
          pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: |
          docker build -t optiflow-backend:${{ github.sha }} services/backend
      - name: Push to registry
        run: |
          docker push optiflow-backend:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Update Kubernetes manifest
        run: |
          sed -i "s|image:.*|image: optiflow-backend:${{ github.sha }}|" \
            infrastructure/kubernetes/backend/deployment.yaml
      - name: Commit and push
        run: |
          git add .
          git commit -m "chore: update backend image to ${{ github.sha }}"
          git push
      # ArgoCD detecta mudança e faz deploy automaticamente
```

---

**Próximos passos**: Implementar estrutura proposta? 🚀
