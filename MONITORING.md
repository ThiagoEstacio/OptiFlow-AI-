# SmartPort - Guia de Monitoramento e Observabilidade

Documentação completa do sistema de monitoramento SmartPort com Prometheus, Grafana e Alertmanager.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Instalação](#instalação)
4. [Métricas](#métricas)
5. [Alertas](#alertas)
6. [Dashboards](#dashboards)
7. [Troubleshooting](#troubleshooting)

---

## 🔍 Visão Geral

O SmartPort utiliza uma stack completa de observabilidade:

- **Prometheus**: Coleta e armazenamento de métricas
- **Grafana**: Visualização e dashboards
- **Alertmanager**: Gerenciamento de alertas
- **Exporters**: Coletores especializados

### Métricas Coletadas

| Componente | Métricas | Intervalo |
|------------|----------|-----------|
| Backend API | Requests, latência, erros | 10s |
| Gateway | Devices conectados, tags lidas, erros | 10s |
| PostgreSQL | Conexões, queries, locks | 15s |
| InfluxDB | Writes, reads, series | 15s |
| Redis | Memória, comandos, hits/misses | 15s |
| Host | CPU, memória, disco, rede | 15s |
| Containers | CPU, memória, I/O por container | 10s |
| Nginx | Requests, conexões ativas, bytes | 15s |

---

## 🏗️ Arquitetura

```
┌─────────────────┐
│   Application   │
│   (Backend,     │◄─── Métricas HTTP /metrics
│    Gateway)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│   Prometheus    │────►│ Alertmanager │──► Email/Slack/PagerDuty
│                 │     └──────────────┘
│  • Scraping     │
│  • Storage      │
│  • Alerting     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│    Grafana      │────►│    InfluxDB     │
│                 │     │   PostgreSQL    │
│  • Dashboards   │     │                 │
│  • Alerts       │     └─────────────────┘
│  • Visualization│
└─────────────────┘
         ▲
         │
    ┌────┴────┐
    │ Exporters│
    │ (Node,   │
    │  cAdvisor│
    │  Postgres│
    │  Redis)  │
    └─────────┘
```

---

## 🚀 Instalação

### 1. Iniciar Stack de Monitoramento

```bash
# Criar network (se não existir)
docker network create smartport-network

# Iniciar aplicação + monitoring
docker-compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d
```

### 2. Verificar Serviços

```bash
# Verificar se todos os containers estão rodando
docker-compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml ps

# Ver logs
docker-compose -f docker-compose.monitoring.yml logs -f prometheus
docker-compose -f docker-compose.monitoring.yml logs -f grafana
```

### 3. Acessar Interfaces

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3001 | admin/admin |
| Alertmanager | http://localhost:9093 | - |

---

## 📊 Métricas

### Backend API

**Endpoint**: `http://backend:8000/metrics`

```python
# Adicionar ao backend/app/main.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Métricas
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'active_connections',
    'Active database connections'
)

@app.get("/metrics")
async def metrics():
    return Response(
        generate_latest(),
        media_type="text/plain"
    )
```

### Gateway

**Endpoint**: `http://gateway:8080/metrics`

Métricas principais:
- `gateway_devices_total`: Total de devices configurados
- `gateway_devices_connected`: Devices atualmente conectados
- `gateway_tags_read_total`: Total de tags lidas
- `gateway_tag_read_errors_total`: Erros de leitura de tags
- `gateway_tag_read_duration_seconds`: Tempo de leitura de tags

### Queries Úteis

```promql
# Taxa de requests por segundo
rate(http_requests_total[5m])

# Latência P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Taxa de erros (%)
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100

# Uso de CPU
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Uso de memória
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Uso de disco
(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100

# Devices conectados
gateway_devices_connected / gateway_devices_total * 100
```

---

## 🚨 Alertas

### Alertas Configurados

#### Infraestrutura
- **HighCPUUsage**: CPU > 80% por 5 minutos
- **CriticalCPUUsage**: CPU > 95% por 2 minutos
- **HighMemoryUsage**: Memória > 85% por 5 minutos
- **CriticalMemoryUsage**: Memória > 95% por 2 minutos
- **HighDiskUsage**: Disco > 85% por 10 minutos
- **CriticalDiskUsage**: Disco > 95% por 5 minutos

#### Aplicação
- **BackendDown**: Backend offline por 1 minuto
- **HighErrorRate**: Taxa de erro > 5% por 5 minutos
- **CriticalErrorRate**: Taxa de erro > 10% por 2 minutos
- **HighRequestLatency**: Latência P95 > 2s por 5 minutos

#### Database
- **PostgreSQLDown**: PostgreSQL offline por 1 minuto
- **PostgreSQLHighConnections**: Uso de conexões > 80% por 5 minutos
- **PostgreSQLLongRunningQueries**: Queries > 5 minutos
- **InfluxDBDown**: InfluxDB offline por 1 minuto
- **RedisDown**: Redis offline por 1 minuto
- **RedisHighMemoryUsage**: Uso de memória Redis > 90%

#### Gateway
- **GatewayDown**: Gateway offline por 2 minutos
- **HighDeviceConnectionErrors**: Alta taxa de erros de conexão
- **HighTagReadErrors**: Alta taxa de erros de leitura

#### Containers
- **ContainerRestarting**: Container reiniciando repetidamente
- **ContainerHighCPU**: Container usando > 80% CPU
- **ContainerHighMemory**: Container usando > 90% memória

### Configurar Notificações

Editar `monitoring/prometheus/alertmanager.yml`:

```yaml
receivers:
  - name: 'critical-alerts'
    email_configs:
      - to: 'oncall@company.com'
        send_resolved: true

    # Slack
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#smartport-alerts'
        title: '[SmartPort] {{ .GroupLabels.alertname }}'

    # PagerDuty
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
```

### Testar Alertas

```bash
# Forçar alerta de CPU
stress --cpu 8 --timeout 300s

# Forçar alerta de memória
stress --vm 4 --vm-bytes 2G --timeout 300s

# Forçar alerta de disco
dd if=/dev/zero of=/tmp/test.img bs=1G count=80
```

---

## 📈 Dashboards

### SmartPort Overview

**UID**: `smartport-overview`

Painéis principais:
1. **Status dos Serviços**: Backend, Gateway, Databases
2. **Uso de Recursos**: CPU, Memória, Disco
3. **API Metrics**: Request rate, latência
4. **Errors**: Taxa de erros por endpoint

### Como Criar Dashboard Customizado

1. Acessar Grafana (http://localhost:3001)
2. Login: admin/admin
3. Click em "+" → "Dashboard"
4. Click em "Add new panel"
5. Selecionar datasource: "Prometheus"
6. Escrever query PromQL
7. Configurar visualização
8. Salvar

### Dashboards Recomendados da Comunidade

```bash
# Importar dashboard pelo ID
# Grafana → Dashboards → Import

# Node Exporter Full
ID: 1860

# Docker Container & Host Metrics
ID: 893

# PostgreSQL Database
ID: 9628

# Redis Dashboard
ID: 763

# Nginx Dashboard
ID: 12708
```

---

## 🔧 Troubleshooting

### Prometheus não está coletando métricas

**Problema**: Targets aparecem como "DOWN" no Prometheus

**Verificar**:
```bash
# Ver targets no Prometheus
curl http://localhost:9090/api/v1/targets

# Testar métricas do backend
curl http://backend:8000/metrics

# Ver logs do Prometheus
docker logs smartport-prometheus
```

**Solução**:
```bash
# Verificar network
docker network inspect smartport-network

# Restart Prometheus
docker-compose -f docker-compose.monitoring.yml restart prometheus
```

### Grafana não conecta ao Prometheus

**Problema**: Erro "Failed to query Prometheus"

**Verificar**:
```bash
# Testar conexão Grafana → Prometheus
docker exec -it smartport-grafana curl http://prometheus:9090/api/v1/query?query=up

# Ver logs
docker logs smartport-grafana
```

**Solução**:
1. Grafana → Configuration → Data Sources
2. Verificar URL: `http://prometheus:9090`
3. Click em "Test" → deve retornar "OK"

### Alertas não estão sendo enviados

**Problema**: Alertas disparam mas não chegam

**Verificar**:
```bash
# Ver alertas ativos
curl http://localhost:9090/api/v1/alerts

# Ver configuração do Alertmanager
curl http://localhost:9093/api/v1/status

# Ver logs
docker logs smartport-alertmanager
```

**Solução**:
```bash
# Verificar SMTP no .env.prod
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Restart Alertmanager
docker-compose -f docker-compose.monitoring.yml restart alertmanager
```

### High cardinality no Prometheus

**Problema**: Prometheus usando muita memória

**Verificar**:
```bash
# Ver número de series
curl http://localhost:9090/api/v1/status/tsdb

# Ver top metrics
curl 'http://localhost:9090/api/v1/label/__name__/values'
```

**Solução**:
```yaml
# Adicionar ao prometheus.yml
global:
  external_labels:
    cluster: 'smartport'  # Reduz duplicação

# Reduzir retention
command:
  - '--storage.tsdb.retention.time=15d'  # Default: 30d
```

### Exporters não estão funcionando

**Problema**: Node exporter, cAdvisor, etc não coletam métricas

**Verificar**:
```bash
# Testar node-exporter
curl http://localhost:9100/metrics

# Testar postgres-exporter
curl http://localhost:9187/metrics

# Ver logs
docker logs smartport-node-exporter
docker logs smartport-postgres-exporter
```

**Solução**:
```bash
# Verificar permissões (node-exporter precisa acesso ao host)
# Ver docker-compose.monitoring.yml volumes

# Restart exporters
docker-compose -f docker-compose.monitoring.yml restart node-exporter
```

---

## 📚 Recursos Adicionais

### Documentação Oficial

- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)
- [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)

### PromQL Cheat Sheet

```promql
# Selectors
http_requests_total{method="GET"}

# Range vector
rate(http_requests_total[5m])

# Aggregation
sum(rate(http_requests_total[5m])) by (endpoint)

# Binary operators
(node_memory_MemFree_bytes / node_memory_MemTotal_bytes) * 100

# Functions
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Melhores Práticas

1. **Use labels consistentes**: `service`, `component`, `environment`
2. **Não use high cardinality labels**: user_id, request_id
3. **Prefixe métricas**: `smartport_gateway_*`, `smartport_backend_*`
4. **Use unidades no nome**: `_seconds`, `_bytes`, `_total`
5. **Documente métricas**: Use `HELP` text
6. **Teste alertas regularmente**
7. **Mantenha dashboards simples**
8. **Use folders para organizar no Grafana**

---

## 🔐 Segurança

### Proteger Prometheus/Grafana em Produção

```yaml
# Adicionar autenticação básica no Nginx
location /prometheus/ {
    auth_basic "Prometheus";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://prometheus:9090/;
}

location /grafana/ {
    proxy_pass http://grafana:3000/;
}
```

### Criar usuário Grafana via API

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monitor User",
    "email": "monitor@company.com",
    "login": "monitor",
    "password": "securepassword",
    "role": "Viewer"
  }' \
  http://admin:admin@localhost:3001/api/admin/users
```

---

## 📊 Métricas de Negócio

Além de métricas técnicas, monitore:

- **Devices ativos vs configurados**
- **Taxa de sucesso de leitura de tags**
- **Latência média por device**
- **Alarmes ativos por severidade**
- **Usuários ativos concorrentes**
- **Taxa de crescimento de dados (InfluxDB)**

---

**Status**: Pronto para Produção ✅
**Versão**: 1.0.0
**Data**: Outubro 2024
