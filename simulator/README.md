# OptiFlow Simulator - Virtual PLC

**Version**: 1.0.0
**Type**: Microserviço independente

---

## 🎯 Propósito

Simula um **PLC real** (Siemens, Allen-Bradley, etc.) para:
- ✅ **Desenvolvimento**: Testar Gateway sem PLCs físicos
- ✅ **Demos**: Demonstrações da plataforma
- ✅ **Testes**: Validar IA, ML, análises de energia
- ✅ **Treinamento**: Treinar operadores

**IMPORTANTE**: Este simulador **NÃO** publica diretamente no Kafka.
O Gateway conecta via OPC-UA e publica as tags no Kafka, igual produção.

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│          Simulator Microservice                         │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Grain Terminal Simulator                        │  │
│  │  - 7 Gates (comportas)                           │  │
│  │  - 3 Conveyor Belts (correias)                   │  │
│  │  - 1 Shiploader (carregador)                     │  │
│  │  - Física simplificada (< 100ms/step)            │  │
│  │  - Falhas programadas (ML training)              │  │
│  └──────────────┬───────────────────────────────────┘  │
│                 │                                       │
│                 ▼                                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │  OPC-UA Server (port 4840)                       │  │
│  │  - Expõe tags como PLC real                      │  │
│  │  - Namespace: ns=2 (industrial)                  │  │
│  │  - Read-only (sem write methods)                 │  │
│  │  - Atualiza tags a cada 1s                       │  │
│  └──────────────┬───────────────────────────────────┘  │
│                 │                                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │  REST API (port 4850)                            │  │
│  │  - /start, /stop, /reset                         │  │
│  │  - /status, /tags                                │  │
│  │  - /gates/*/setpoint                             │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │                          │
         ▼                          ▼
   Gateway (OPC-UA)          Frontend (REST API)
   Lê tags → Kafka          Controla simulação
```

---

## 🚀 Quick Start

### Local (Python)

```bash
cd simulator

# Instala dependências
pip install -r requirements.txt

# Roda simulador
python -m app.main

# Acessa
# - OPC-UA: opc.tcp://localhost:4840
# - REST API: http://localhost:4850
# - Docs: http://localhost:4850/docs
```

### Docker

```bash
# Build
docker build -t optiflow-simulator:latest ./simulator

# Run
docker run -p 4840:4840 -p 4850:4850 optiflow-simulator:latest

# Logs
docker logs -f optiflow-simulator
```

### Docker Compose (Standalone)

```bash
docker-compose -f simulator/docker-compose.yml up

# Para
docker-compose -f simulator/docker-compose.yml down
```

---

## 📡 API Endpoints

### System Control

```bash
# Iniciar simulação
curl -X POST http://localhost:4850/simulator/start

# Parar simulação
curl -X POST http://localhost:4850/simulator/stop

# Reset simulador
curl -X POST http://localhost:4850/simulator/reset

# Status completo
curl http://localhost:4850/simulator/status
```

### Gate Control

```bash
# Setpoint de gate específica (0-6)
curl -X POST http://localhost:4850/simulator/gates/0/setpoint \
  -H "Content-Type: application/json" \
  -d '{"value": 50.0}'

# Setpoint de TODAS as gates
curl -X POST http://localhost:4850/simulator/gates/all/setpoint \
  -H "Content-Type: application/json" \
  -d '{"value": 60.0}'
```

### Tags

```bash
# Listar todas as tags disponíveis
curl http://localhost:4850/simulator/tags
```

**Response**:
```json
{
  "count": 50,
  "tags": {
    "SYSTEM_RUNNING_PV": 1.0,
    "SYSTEM_TIME_S_PV": 123.4,
    "CORR01_TEMP_C_PV": 45.2,
    "ARZ_GATES_GATE01_POSICAO_PV": 50.0,
    ...
  }
}
```

---

## 🔌 OPC-UA Server

### Conexão

```python
from asyncua import Client

async def connect():
    client = Client("opc.tcp://localhost:4840")
    await client.connect()

    # Browse namespace
    root = client.nodes.objects
    children = await root.get_children()

    # Lê tag
    temp_node = client.get_node("ns=2;s=CORR01/TEMP_C_PV")
    value = await temp_node.read_value()
    print(f"Temperature: {value}°C")

    await client.disconnect()
```

### Gateway Config

Para o Gateway conectar, adicione em `config/adapters_config.yaml`:

```yaml
adapters:
  - adapter_id: simulator_opcua
    protocol_type: opcua
    enabled: true
    host: simulator  # Docker service name
    port: 4840
    timeout: 5.0
    scan_rate_ms: 1000

    extra_config:
      security_mode: None
      security_policy: None

    tags:
      - name: CORR01_TEMP_C
        address: ns=2;s=CORR01/TEMP_C_PV
        type: float
        unit: °C

      - name: CORR01_POWER_KW
        address: ns=2;s=CORR01/POWER_KW_PV
        type: float
        unit: kW

      # ... adicione outras tags
```

---

## 📊 Tags Disponíveis

### System Tags

| Tag Name | Type | Unit | Description |
|----------|------|------|-------------|
| SYSTEM_RUNNING_PV | Boolean | - | Sistema rodando |
| SYSTEM_TIME_S_PV | Float | s | Tempo simulação |
| TOTAL_MASS_T_PV | Float | t | Massa total carregada |
| TOTAL_KWH_PV | Float | kWh | Energia total consumida |
| WAREHOUSE_LEVEL_PCT_PV | Float | % | Nível armazém |

### Gate Tags (01-07)

| Tag Name | Type | Unit | Description |
|----------|------|------|-------------|
| ARZ_GATES_GATE{N}_POSICAO_PV | Float | % | Abertura comporta |
| ARZ_GATES_GATE{N}_VAZAO_TPH_PV | Float | t/h | Vazão comporta |

### Belt Tags (CORR01, CORR02, CORR03)

| Tag Name | Type | Unit | Description |
|----------|------|------|-------------|
| {BELT}_RUNNING_PV | Boolean | - | Correia ligada |
| {BELT}_SPEED_MPS_PV | Float | m/s | Velocidade correia |
| {BELT}_FLOW_TPH_PV | Float | t/h | Vazão correia |
| {BELT}_LOAD_PCT_PV | Float | % | Carregamento |
| {BELT}_POWER_KW_PV | Float | kW | Potência motor |
| {BELT}_CURRENT_A_PV | Float | A | Corrente motor |
| {BELT}_TEMP_C_PV | Float | °C | Temperatura motor |
| {BELT}_MISALIGNMENT_PV | Float | 0-1 | Desalinhamento |

### Shiploader Tags

| Tag Name | Type | Unit | Description |
|----------|------|------|-------------|
| SLD01_SETPOINT_TPH_PV | Float | t/h | Setpoint vazão |
| SLD01_FLOW_TPH_PV | Float | t/h | Vazão atual |
| SLD01_POWER_KW_PV | Float | kW | Potência |
| SLD01_CURRENT_A_PV | Float | A | Corrente |

---

## 🧪 Falhas Programadas

O simulador injeta falhas automaticamente para treinar ML:

| Tempo (s) | Falha | Descrição |
|-----------|-------|-----------|
| 300 | Gate Stuck | Gate 02 trava em 45% |
| 600 | Belt Misalignment | CORR01 desalinhamento 30% |

**Observável via**:
- Tag: `ARZ_GATES_GATE02_POSICAO_PV` (não responde a setpoint)
- Tag: `CORR01_MISALIGNMENT_PV` (aumenta de 0 para 0.3)
- Consequência: `CORR01_POWER_KW_PV` aumenta (mais consumo)
- Consequência: `CORR01_TEMP_C_PV` aumenta (aquecimento)

---

## 🔄 Workflow Completo

### 1. Iniciar Simulador

```bash
docker-compose -f simulator/docker-compose.yml up -d
```

### 2. Verificar Status

```bash
curl http://localhost:4850/health
```

**Response**:
```json
{
  "status": "healthy",
  "simulator_running": false,
  "opcua_server": "running"
}
```

### 3. Iniciar Simulação

```bash
curl -X POST http://localhost:4850/simulator/start
```

**Resultado**:
- ✅ Correias ligam
- ✅ Tags OPC-UA começam a variar
- ✅ Loop automático (1 step/segundo)

### 4. Conectar Gateway

Gateway lê tags via OPC-UA e publica no Kafka:

```bash
# Gateway lê CORR01_TEMP_C_PV a cada 1s
# Gateway publica no Kafka topic "raw_tags"
# Backend consome Kafka → InfluxDB
```

### 5. Visualizar no Frontend

Frontend consulta backend → mostra dashboards em tempo real

---

## 📈 Performance

| Métrica | Target | Atual |
|---------|--------|-------|
| Simulation step | < 100ms | ~10-20ms |
| OPC-UA update rate | 1 Hz | 1 Hz |
| Tags count | 50+ | 50 |
| Memory usage | < 200MB | ~150MB |
| CPU usage | < 10% | ~5% |

---

## 🐛 Troubleshooting

### OPC-UA server não inicia

```bash
# Erro: "Address already in use"
# Solução: Matar processo na porta 4840
sudo lsof -i :4840
sudo kill -9 <PID>
```

### Gateway não conecta

```bash
# 1. Verificar se simulador está rodando
curl http://localhost:4850/health

# 2. Verificar se OPC-UA está acessível
telnet localhost 4840

# 3. Verificar logs do simulador
docker logs -f optiflow-simulator

# 4. Verificar configuração do gateway
# host: "simulator" (Docker service name)
# port: 4840
# endpoint: "opc.tcp://simulator:4840"
```

### Tags não variam

```bash
# Verificar se simulação está rodando
curl http://localhost:4850/simulator/status

# Se "running": false, iniciar
curl -X POST http://localhost:4850/simulator/start

# Verificar valores direto da API
curl http://localhost:4850/simulator/tags
```

---

## 📚 References

- [OPC-UA Specification](https://opcfoundation.org/)
- [asyncua Documentation](https://github.com/FreeOpcUa/opcua-asyncio)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Developed by**: OptiFlow Team
**License**: Proprietary
