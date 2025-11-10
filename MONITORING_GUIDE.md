# 📊 OptiFlow AI - Monitoring System

Sistema completo de monitoramento com **Prometheus** e **Grafana** para observabilidade em tempo real.

## 🎯 Objetivo

Fornecer visibilidade total sobre:
- **Performance** da API (latência, throughput, erros)
- **Saúde** dos devices IoT (conexões, leituras, erros)
- **Recursos** do sistema (CPU, RAM, Disk)
- **Dados** (Kafka, InfluxDB, PostgreSQL)
- **Alarmes** ativos e histórico

---

## 📁 Estrutura

```
monitoring/
├── prometheus/
│   ├── prometheus.yml                    # Configuração principal
│   ├── alerts/
│   │   └── optiflow_alerts.yml          # Regras de alerta
│   └── alertmanager.yml                  # Notificações
├── grafana/
│   ├── dashboards/
│   │   ├── optiflow_system_overview.json     # Dashboard principal
│   │   ├── optiflow_api_metrics.json         # API performance
│   │   └── optiflow_devices_monitoring.json  # Devices IoT
│   └── provisioning/
│       ├── datasources/
│       │   └── prometheus.yml            # Datasource Prometheus
│       └── dashboards/
│           └── dashboards.yml            # Auto-load dashboards
```

---

## 🚀 Quick Start

### 1. Iniciar Monitoramento

```bash
# Iniciar Prometheus + Grafana
docker-compose -f docker-compose.monitoring.yml up -d

# Verificar serviços
docker-compose -f docker-compose.monitoring.yml ps
```

### 2. Acessar Interfaces

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **Alertmanager** | http://localhost:9093 | - |

### 3. Validar Métricas

```bash
# Testar endpoint de métricas
curl http://localhost:8000/metrics

# Ver targets no Prometheus
# Acessar: http://localhost:9090/targets

# Health check de métricas
curl http://localhost:8000/health/metrics
```

---

## 📊 Dashboards Disponíveis

### 1. **System Overview** (`optiflow_system_overview`)
Dashboard principal com visão geral do sistema.

**Painéis:**
- CPU, Memory, Disk usage (gauges)
- HTTP requests/s por método (time series)
- Latência HTTP p95/p50 (time series)
- Devices conectados (stat)
- Tags lidos/s por device (time series)
- InfluxDB points escritos/s (time series)
- Alarmes críticos e totais (stats)

**Uso:**
- Monitoramento em tempo real (refresh: 10s)
- Identificar gargalos de performance
- Detectar problemas de devices

### 2. **API Metrics** (`optiflow_api_metrics`)
Performance detalhada da API.

**Painéis:**
- Requests por endpoint (top 10)
- Taxa de erro 4xx/5xx
- Latência por endpoint
- Requests em progresso
- Throughput total

**Uso:**
- Otimizar endpoints lentos
- Detectar erros recorrentes
- Analisar carga por endpoint

### 3. **Devices Monitoring** (`optiflow_devices_monitoring`)
Monitoramento de devices IoT.

**Painéis:**
- Devices conectados por protocolo (OPC-UA, Modbus, MQTT)
- Tags lidos/s com qualidade (Good, Bad)
- Erros de leitura por device
- Taxa de sucesso de leitura
- Histórico de conexões

**Uso:**
- Identificar devices com problemas
- Monitorar qualidade de dados
- Alertar sobre desconexões

---

## 🔔 Alertas Configurados

### Criticidade: CRITICAL

| Alerta | Condição | For | Ação |
|--------|----------|-----|------|
| **APIDown** | Backend não responde | 1min | Reiniciar serviço |
| **GatewayDown** | Gateway não responde | 1min | Verificar rede |
| **HighAPIErrorRate** | >5% de erros 5xx | 2min | Checar logs |
| **NoTagsBeingRead** | 0 tags lidos | 3min | Verificar devices |
| **CriticalCPUUsage** | CPU >95% | 2min | Escalar recursos |
| **CriticalDiskUsage** | Disk >95% | 1min | Liberar espaço |
| **MultipleCriticalAlarms** | >5 alarmes críticos | 1min | Ação urgente |

### Criticidade: WARNING

| Alerta | Condição | For | Ação |
|--------|----------|-----|------|
| **HighAPILatency** | p95 >2s | 5min | Otimizar código |
| **HighRequestRate** | >1000 req/s | 5min | Verificar DDoS |
| **MultipleDevicesDisconnected** | <5 devices | 5min | Verificar rede |
| **HighTagReadErrorRate** | >10% erros leitura | 3min | Verificar conexões |
| **HighDatabaseErrorRate** | >10 erros/s | 2min | Verificar DB |
| **HighCPUUsage** | CPU >80% | 5min | Otimizar |
| **HighMemoryUsage** | RAM >85% | 5min | Verificar leaks |
| **HighDiskUsage** | Disk >85% | 5min | Planejar limpeza |

---

## 📈 Métricas Disponíveis

### HTTP Metrics

```promql
# Total de requests
optiflow_http_requests_total{method="GET", endpoint="/api/v1/devices", status="200"}

# Duração de requests (histogram)
optiflow_http_request_duration_seconds_bucket{method="GET", endpoint="/api/v1/devices", le="0.05"}

# Requests em progresso
optiflow_http_requests_in_progress{method="GET", endpoint="/api/v1/devices"}
```

### Device/Tag Metrics

```promql
# Devices conectados por protocolo
optiflow_devices_connected{protocol="opc_ua"}

# Total de tags configurados
optiflow_tags_total{device="Device001"}

# Tags lidos (contador)
optiflow_tags_read_total{device="Device001", quality="Good"}

# Erros de leitura
optiflow_tag_read_errors_total{device="Device001", error_type="timeout"}
```

### Database Metrics

```promql
# Conexões ativas
optiflow_db_connections_active{database="postgres"}

# Queries executadas
optiflow_db_queries_total{database="postgres", operation="SELECT"}

# Duração de queries (histogram)
optiflow_db_query_duration_seconds_bucket{database="postgres", operation="SELECT", le="0.1"}

# Erros de database
optiflow_db_errors_total{database="postgres", error_type="connection_timeout"}
```

### Kafka Metrics

```promql
# Mensagens enviadas
optiflow_kafka_messages_sent_total{topic="tag-readings"}

# Mensagens falhadas
optiflow_kafka_messages_failed_total{topic="tag-readings", error_type="timeout"}

# Tamanho da fila do producer
optiflow_kafka_producer_queue_size
```

### InfluxDB Metrics

```promql
# Pontos escritos
optiflow_influxdb_points_written_total{bucket="optiflow"}

# Erros de escrita
optiflow_influxdb_write_errors_total{bucket="optiflow", error_type="timeout"}

# Duração de escrita (histogram)
optiflow_influxdb_write_duration_seconds_bucket{bucket="optiflow", le="0.1"}
```

### System Metrics

```promql
# CPU usage
optiflow_system_cpu_usage_percent

# Memória usage
optiflow_system_memory_usage_bytes

# Memória disponível
optiflow_system_memory_available_bytes

# Disk usage
optiflow_system_disk_usage_percent{mount_point="/"}
```

### Alarm Metrics

```promql
# Alarmes ativos por severidade
optiflow_alarms_active{severity="CRITICAL"}

# Total de alarmes disparados
optiflow_alarms_total{severity="HIGH", equipment="Pump-01"}
```

---

## 🔍 Queries Úteis

### Performance da API

```promql
# Taxa de requests/s nos últimos 5min
rate(optiflow_http_requests_total[5m])

# Latência p95 por endpoint
histogram_quantile(0.95, rate(optiflow_http_request_duration_seconds_bucket[5m]))

# Taxa de erro (5xx)
sum(rate(optiflow_http_requests_total{status=~"5.."}[5m])) 
/ 
sum(rate(optiflow_http_requests_total[5m]))

# Endpoints mais lentos (top 5)
topk(5, histogram_quantile(0.95, rate(optiflow_http_request_duration_seconds_bucket[5m])))
```

### Monitoramento de Devices

```promql
# Taxa de leitura de tags/s
rate(optiflow_tags_read_total[1m])

# Taxa de erro de leitura
sum(rate(optiflow_tag_read_errors_total[5m])) 
/ 
sum(rate(optiflow_tags_read_total[5m]))

# Devices com mais erros (top 5)
topk(5, rate(optiflow_tag_read_errors_total[5m]))

# Total de devices conectados
sum(optiflow_devices_connected)
```

### Database Performance

```promql
# Queries/s por tipo
sum(rate(optiflow_db_queries_total[5m])) by (operation)

# Latência p95 de queries
histogram_quantile(0.95, rate(optiflow_db_query_duration_seconds_bucket[5m]))

# Taxa de erro de database
rate(optiflow_db_errors_total[5m])
```

### Sistema

```promql
# CPU usage médio (últimos 5min)
avg_over_time(optiflow_system_cpu_usage_percent[5m])

# Memória usage em %
100 * (optiflow_system_memory_usage_bytes / (optiflow_system_memory_usage_bytes + optiflow_system_memory_available_bytes))

# Previsão de disk cheio (linear regression)
predict_linear(optiflow_system_disk_usage_percent[1h], 7*24*3600)
```

---

## 🔧 Configuração Avançada

### Ajustar Scrape Interval

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s     # Padrão: 15s
  evaluation_interval: 15s  # Avaliar regras a cada 15s

scrape_configs:
  - job_name: 'optiflow-backend'
    scrape_interval: 10s    # Override: mais frequente para API
```

### Adicionar Novo Alerta

```yaml
# monitoring/prometheus/alerts/optiflow_alerts.yml
- alert: MyCustomAlert
  expr: my_metric > 100
  for: 5m
  labels:
    severity: warning
    component: my-service
  annotations:
    summary: "My custom alert"
    description: "Value is {{ $value }}"
```

### Criar Dashboard Customizado

1. Acessar Grafana (http://localhost:3000)
2. Criar novo dashboard
3. Adicionar painéis com queries Prometheus
4. Exportar JSON
5. Salvar em `monitoring/grafana/dashboards/`

---

## 📊 Recording Rules

Regras pré-calculadas para otimizar queries frequentes:

```promql
# Taxa de requests/s (agregado 1min)
job:optiflow_http_requests:rate1m

# Latência p95 (agregado)
job:optiflow_http_request_duration:p95

# Taxa de erro (agregado)
job:optiflow_http_errors:rate1m

# Taxa de sucesso
job:optiflow_http_success_rate

# Tags lidos/s
job:optiflow_tags_read:rate1m

# Queries DB/s
job:optiflow_db_queries:rate1m
```

**Uso em Grafana:**
```promql
# Usar recording rule ao invés de query complexa
job:optiflow_http_request_duration:p95
```

---

## 🐛 Troubleshooting

### Métricas não aparecem no Prometheus

```bash
# 1. Verificar se endpoint /metrics está funcionando
curl http://localhost:8000/metrics

# 2. Verificar targets no Prometheus
# http://localhost:9090/targets
# Status deve ser "UP"

# 3. Verificar logs do Prometheus
docker-compose -f docker-compose.monitoring.yml logs prometheus

# 4. Testar conectividade
docker exec -it prometheus wget -O- http://backend:8000/metrics
```

### Grafana não mostra dados

```bash
# 1. Verificar datasource
# Grafana > Configuration > Data Sources > Prometheus
# URL deve ser: http://prometheus:9090

# 2. Testar query no Prometheus primeiro
# http://localhost:9090/graph
# Executar query: optiflow_http_requests_total

# 3. Verificar timerange no Grafana
# Ajustar para "Last 15 minutes"

# 4. Verificar logs do Grafana
docker-compose -f docker-compose.monitoring.yml logs grafana
```

### Alertas não disparam

```bash
# 1. Verificar regras de alerta carregadas
# http://localhost:9090/alerts

# 2. Verificar Alertmanager
# http://localhost:9093

# 3. Testar expressão do alerta
# Executar no Prometheus: optiflow_system_cpu_usage_percent > 80

# 4. Verificar "for" clause
# Alerta só dispara após condição persistir por tempo definido
```

---

## 📚 Referências

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
- [Alerting Best Practices](https://prometheus.io/docs/practices/alerting/)

---

## ✅ Checklist de Implementação

- [x] Adicionar `prometheus-client` ao requirements.txt
- [x] Criar `PrometheusMetrics` service
- [x] Criar `PrometheusMiddleware` para FastAPI
- [x] Criar endpoint `/metrics`
- [x] Configurar `prometheus.yml` (scraping)
- [x] Criar alertas (`optiflow_alerts.yml`)
- [x] Criar dashboard Grafana
- [ ] Integrar com `docker-compose.yml`
- [ ] Testar localmente
- [ ] Documentar métricas customizadas

---

**Próximos Passos:**
1. Integrar Prometheus/Grafana ao `docker-compose.yml`
2. Adicionar middleware ao FastAPI (`main.py`)
3. Testar com `docker-compose up`
4. Validar dashboards no Grafana
5. Configurar notificações (Slack, Email)
