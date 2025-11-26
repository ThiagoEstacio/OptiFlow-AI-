# OptiFlow - Arquitetura de Microserviços

## 📋 Visão Geral

OptiFlow utiliza uma arquitetura de microserviços com 4 serviços principais:

| Serviço | Função | Tecnologia | Porta |
|---------|--------|------------|-------|
| **Simulator** | Simulador OPC UA Server | asyncua (python-opcua) | 4840 |
| **Gateway** | Coleta de dados industrial | asyncio + FastAPI | 8080 |
| **Backend** | Lógica de negócio e APIs | FastAPI | 8000 |
| **Frontend** | Interface web | React + Vite | 3000 |

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA OT (Operational Technology)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────────┐                                         │
│   │  OPC UA Simulator │  (Simula PLCs/Sensores)                │
│   │  Port: 4840      │                                         │
│   └────────┬──────────┘                                         │
│            │ OPC UA Protocol                                    │
│            ▼                                                     │
│   ┌──────────────────┐                                         │
│   │  Gateway Service │  (Coleta dados industriais)            │
│   │  Port: 8080      │  • OPC UA Client                       │
│   │                  │  • Kafka Producer                       │
│   └────────┬──────────┘                                         │
│            │                                                     │
└────────────┼─────────────────────────────────────────────────────┘
             │
             │ Kafka Topic: raw_tags
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  MESSAGE BROKER (Desacoplamento)                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │  Apache Kafka Cluster (3 brokers)                       │ │
│   │  • kafka-1:9092, kafka-2:9093, kafka-3:9096             │ │
│   │  • Topic: raw_tags (dados de sensores)                  │ │
│   │  • Topic: raw_tags_dlq (dead letter queue)              │ │
│   └────────────────────┬─────────────────────────────────────┘ │
│                        │                                         │
└────────────────────────┼─────────────────────────────────────────┘
                         │
                         │ Kafka Consumer
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA IT (Information Technology)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │  Backend Service (FastAPI)                               │ │
│   │  Port: 8000                                              │ │
│   │                                                          │ │
│   │  ┌─────────────────────────────────────────────────────┐│ │
│   │  │ Kafka Consumer (timeseries_consumer.py)            ││ │
│   │  │ • Consome mensagens de raw_tags                    ││ │
│   │  │ • Escreve em InfluxDB                              ││ │
│   │  │ • Deduplicação via Redis                           ││ │
│   │  └─────────────────────────────────────────────────────┘│ │
│   │                                                          │ │
│   │  ┌─────────────────────────────────────────────────────┐│ │
│   │  │ REST API                                            ││ │
│   │  │ • /api/v1/... (CRUD operations)                    ││ │
│   │  │ • /api/health (health checks)                      ││ │
│   │  │ • /metrics (Prometheus metrics)                    ││ │
│   │  └─────────────────────────────────────────────────────┘│ │
│   │                                                          │ │
│   │  ┌─────────────────────────────────────────────────────┐│ │
│   │  │ WebSocket Server                                    ││ │
│   │  │ • Envia dados em tempo real para Frontend          ││ │
│   │  └─────────────────────────────────────────────────────┘│ │
│   └────────────────────┬─────────────────────────────────────┘ │
│                        │ HTTP/WebSocket                          │
│                        ▼                                         │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │  Frontend (React + TypeScript)                           │ │
│   │  Port: 3000                                              │ │
│   │  • Dashboards                                            │ │
│   │  • Gráficos em tempo real (WebSocket)                   │ │
│   │  • Configuração de alarmes                              │ │
│   └──────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  INFRAESTRUTURA                                                 │
├─────────────────────────────────────────────────────────────────┤
│  • PostgreSQL (dados relacionais)                               │
│  • InfluxDB (séries temporais)                                  │
│  • Redis (cache + deduplicação)                                 │
│  • RabbitMQ (tarefas assíncronas - Celery)                     │
│  • Prometheus (métricas)                                        │
│  • Grafana (dashboards de monitoramento)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Fluxo de Dados

### 1. Coleta de Dados (OT → IT)

```
Simulator (OPC UA) → Gateway (OPC UA Client) → Kafka (raw_tags)
```

**Detalhes**:
- Simulator publica dados em OPC UA (4840)
- Gateway conecta como cliente OPC UA
- Gateway transforma dados em mensagens JSON
- Gateway publica no Kafka topic `raw_tags`

### 2. Processamento de Dados (Kafka → Backend)

```
Kafka (raw_tags) → Backend (timeseries_consumer) → InfluxDB
```

**Detalhes**:
- Backend consome mensagens do Kafka via `timeseries_consumer.py`
- Deduplicação via Redis (evita dados duplicados)
- Batch writing (escreve em lotes para otimizar performance)
- Circuit breaker (protege InfluxDB de sobrecarga)
- Dados persistidos em InfluxDB para consultas

### 3. Visualização (Backend → Frontend)

```
InfluxDB → Backend (REST API) → Frontend (HTTP/WebSocket)
```

**Detalhes**:
- Frontend consulta Backend via REST API
- Backend lê dados do InfluxDB
- WebSocket envia dados em tempo real
- Frontend renderiza dashboards e gráficos

---

## 🚀 Componentes Principais

### 1. Simulator (OPC UA Server)

**Arquivo**: `opcua-simulator/server.py`

**Função**: Simula um terminal graneleiro com:
- 5 silos (sensores de temperatura, nível, umidade)
- 3 correias transportadoras (velocidade, status)
- 2 moegas (peso, status)

**Protocolo**: OPC UA (não HTTP!)

**Quando usar**:
- Desenvolvimento local (sem acesso a PLCs reais)
- Testes de integração
- Demonstrações

### 2. Gateway Service (Microserviço Standalone)

**Arquivo**: `gateway/app/main.py`

**Função**:
- Conecta em servidores OPC UA
- Coleta dados de tags configuradas
- Publica dados no Kafka

**APIs**:
- `GET /health` - Health check
- `GET /api/tags` - Lista tags disponíveis no OPC UA
- `GET /api/devices` - Lista dispositivos configurados

**Configuração via Environment**:
```bash
GATEWAY_ENABLED=true
GATEWAY_POLL_INTERVAL_S=1.0
KAFKA_BOOTSTRAP_SERVERS=kafka-1:9092,kafka-2:9093,kafka-3:9096
```

**⚠️ IMPORTANTE**: Gateway NÃO está mais dentro do Backend! É um microserviço independente.

### 3. Backend Service (FastAPI)

**Arquivo**: `backend/app/main.py`

**Função**:
- API REST para CRUD de assets, alarmes, dashboards
- Kafka Consumer (consome dados do Gateway)
- WebSocket Server (envia dados em tempo real)
- ML/AI Agent (análise preditiva)

**Componentes**:

#### a) Kafka Consumer (`timeseries_consumer.py`)

```python
# Auto-start no startup do Backend
@app.on_event("startup")
async def startup_event():
    await start_timeseries_consumer()
```

**Configuração**:
```bash
CONSUMER_ENABLED=true
CONSUMER_TOPIC=raw_tags
CONSUMER_GROUP_ID=timeseries-writers
CONSUMER_MIN_BATCH_SIZE=50
CONSUMER_MAX_BATCH_SIZE=500
```

#### b) REST API

Endpoints principais:
- `/api/v1/assets` - Gerenciamento de assets
- `/api/v1/alarms` - Configuração de alarmes
- `/api/v1/dashboards` - Dashboards personalizados
- `/api/v1/timeseries` - Consulta de séries temporais
- `/api/health` - Health check
- `/metrics` - Métricas Prometheus

#### c) WebSocket Server

```python
# Frontend conecta via WebSocket
ws = new WebSocket("ws://localhost:8000/api/v1/ws")
```

### 4. Frontend (React + TypeScript)

**Arquivo**: `frontend/src/`

**Função**:
- Interface web para visualização e configuração
- Dashboards interativos
- Gráficos em tempo real (WebSocket)
- Configuração de alarmes e assets

**Tecnologias**:
- React 18
- TypeScript
- Material-UI
- Recharts / Plotly.js
- WebSocket client

---

## 🔐 Separação OT/IT

OptiFlow implementa separação de redes OT/IT por segurança:

```yaml
# docker-compose.yml

networks:
  ot-network:   # Operational Technology (PLCs, sensores)
    driver: bridge

  it-network:   # Information Technology (Backend, Frontend, DBs)
    driver: bridge

services:
  # Gateway tem acesso a AMBAS as redes (funciona como diodo de dados)
  gateway:
    networks:
      - ot-network  # Comunica com OPC UA Simulator
      - it-network  # Publica no Kafka

  # Simulator só acessa rede OT
  simulator:
    networks:
      - ot-network

  # Backend, Frontend, DBs só acessam rede IT
  backend:
    networks:
      - it-network
```

**Por quê?**
- Segurança: PLCs não têm acesso direto à internet
- Isolamento: Problemas na rede IT não afetam rede OT
- Conformidade: Atende normas IEC 62443

---

## 📊 Fluxo de Mensagens Kafka

### Topic: `raw_tags`

**Formato da mensagem**:
```json
{
  "tag_id": "Silo_1_Temperature",
  "tag_name": "Silo 1 - Temperatura",
  "value": 25.3,
  "unit": "°C",
  "timestamp": "2025-11-19T10:30:45.123Z",
  "quality": "good",
  "source": "optiflow-gateway",
  "device_id": "opcua-simulator"
}
```

**Produtores**:
- Gateway Service (principal)
- Simulador (em modo teste)

**Consumidores**:
- Backend (`timeseries_consumer.py`) - escreve em InfluxDB
- Outros serviços futuros (analytics, ML pipeline, etc.)

### Topic: `raw_tags_dlq` (Dead Letter Queue)

**Função**: Armazena mensagens que falhar  ao processar

**Quando usar**:
- Erros de parse JSON
- InfluxDB indisponível por muito tempo
- Dados malformados

**Reprocessamento**: Via `dlq_processor.py` (manual ou automático)

---

## 🔧 Configuração

### Backend

Arquivo: `backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # Kafka Consumer
    CONSUMER_ENABLED: bool = True
    CONSUMER_TOPIC: str = "raw_tags"
    CONSUMER_GROUP_ID: str = "timeseries-writers"
    CONSUMER_MIN_BATCH_SIZE: int = 50
    CONSUMER_MAX_BATCH_SIZE: int = 500
    CONSUMER_BATCH_TIMEOUT_S: float = 5.0

    # Kafka Cluster
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka-1:9092,kafka-2:9093,kafka-3:9096"
    KAFKA_DLQ_TOPIC: str = "raw_tags_dlq"
```

### Gateway

Arquivo: `gateway/app/config.py`

```python
# Gateway Configuration
GATEWAY_ENABLED: bool = True
GATEWAY_POLL_INTERVAL_S: float = 1.0
GATEWAY_SOURCE_NAME: str = "optiflow-gateway"
GATEWAY_MAX_BUFFER_SIZE: int = 10000

# Kafka
KAFKA_BOOTSTRAP_SERVERS: str = "kafka-1:9092,kafka-2:9093,kafka-3:9096"
```

---

## 🐛 Debug e Troubleshooting

### Verificar se Gateway está publicando no Kafka

```bash
# Ver logs do Gateway
docker-compose logs -f gateway

# Procurar por:
# "✅ Published 1 messages to Kafka"
```

### Verificar se Backend está consumindo do Kafka

```bash
# Ver logs do Backend
docker-compose logs -f backend

# Procurar por:
# "✅ Kafka consumer started"
# "✅ Wrote batch of 50 points to InfluxDB"
```

### Verificar mensagens no Kafka

```bash
# Acessar Kafka UI
http://localhost:8090

# Ou via CLI
docker exec -it kafka-1 kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic raw_tags \
  --from-beginning \
  --max-messages 10
```

### Verificar dados no InfluxDB

```bash
# Acessar InfluxDB UI
http://localhost:8086

# Ou via CLI
docker exec -it optiflow-influxdb influx query \
  --org optiflow \
  --token my-super-secret-influxdb-token \
  'from(bucket:"timeseries") |> range(start: -1h) |> limit(n:10)'
```

### Health Checks

```bash
# Gateway
curl http://localhost:8080/health

# Backend
curl http://localhost:8000/api/health

# Resposta esperada do Backend:
{
  "status": "healthy",
  "checks": {
    "database": {"status": "healthy"},
    "influxdb": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "gateway": {
      "status": "external",
      "note": "Gateway is now a standalone microservice (port 8080)",
      "health_endpoint": "http://gateway:8080/health"
    }
  }
}
```

---

## 📈 Métricas (Prometheus)

### Backend Metrics

```bash
# Ver métricas
curl http://localhost:8000/metrics
```

**Métricas do Consumer**:
- `consumer_messages_consumed_total` - Total de mensagens consumidas
- `consumer_messages_written_total` - Total de mensagens escritas no InfluxDB
- `consumer_batch_size_current` - Tamanho atual do batch
- `consumer_write_latency_seconds` - Latência de escrita
- `consumer_dedup_hits_total` - Total de duplicatas detectadas
- `consumer_dlq_messages_total` - Total de mensagens enviadas para DLQ

### Gateway Metrics

```bash
# Ver métricas do Gateway
curl http://localhost:8080/metrics
```

**Métricas do Gateway**:
- `gateway_messages_published_total` - Total de mensagens publicadas
- `gateway_publish_latency_seconds` - Latência de publicação
- `gateway_buffer_size` - Tamanho do buffer
- `gateway_circuit_breaker_state` - Estado do circuit breaker

---

## 🚀 Próximos Passos

### Para Desenvolvedores

1. **Subir ambiente local**:
   ```bash
   cd /home/thiestacio/OptiFlow-AI-
   ./dev.sh start
   ```

2. **Verificar serviços**:
   ```bash
   ./dev.sh status
   ```

3. **Ver logs**:
   ```bash
   ./dev.sh logs gateway
   ./dev.sh logs backend
   ```

4. **Testar fluxo completo**:
   - Simulator publica dados → Gateway coleta → Kafka → Backend consome → InfluxDB
   - Verificar em: http://localhost:3000 (Frontend)

### Para DevOps

1. **Monitoramento**: Configure Grafana com dashboards de Kafka e InfluxDB
2. **Alertas**: Configure AlertManager para métricas críticas
3. **Scaling**: Configure HPA (Horizontal Pod Autoscaler) para Gateway e Backend
4. **Backup**: Configure backup automático de InfluxDB e PostgreSQL

---

## 📚 Documentação Relacionada

- [QUICK_START.md](QUICK_START.md) - Como iniciar o projeto em 3 comandos
- [DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md) - Guia completo Docker Compose
- [ENVIRONMENT_GUIDE.md](ENVIRONMENT_GUIDE.md) - Ambientes (Dev/Staging/Prod)
- [INFRASTRUCTURE_GUIDE.md](INFRASTRUCTURE_GUIDE.md) - Infraestrutura Kubernetes

---

**Última atualização**: 2025-11-19
**Versão da arquitetura**: Microserviços v2 (Gateway standalone)
