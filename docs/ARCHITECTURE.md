# OptiFlow - Arquitetura e Premissas

## Visao Geral

OptiFlow e uma plataforma de IoT Industrial (IIoT) para monitoramento e analise de dados de processos industriais, similar ao OSIsoft PI System.

## Arquitetura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CAMPO (OT Network)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Siemens S7   │  │ Rockwell CLX │  │ Modbus TCP   │  │ MQTT/IoT     │    │
│  │ (OPC-UA)     │  │ (EtherNet/IP)│  │ (Energia)    │  │ (Sensores)   │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │             │
│         └─────────────────┴─────────────────┴─────────────────┘             │
│                                    │                                         │
│                         ┌──────────▼──────────┐                             │
│                         │   Node-RED          │                             │
│                         │   (Simulador/Edge)  │                             │
│                         └──────────┬──────────┘                             │
│                                    │                                         │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                              GATEWAY (Edge)                                  │
├────────────────────────────────────┼────────────────────────────────────────┤
│                                    │                                         │
│                         ┌──────────▼──────────┐                             │
│                         │   HTTP Ingest API   │                             │
│                         │   (Buffer)          │                             │
│                         └──────────┬──────────┘                             │
│                                    │                                         │
│    ┌───────────────────────────────┼───────────────────────────────┐        │
│    │                               │                               │        │
│    ▼                               ▼                               ▼        │
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│ │ Virtual     │  │ Virtual     │  │ Virtual     │  │ Virtual     │        │
│ │ OPC-UA      │  │ MODBUS      │  │ PROFINET    │  │ EtherNet/IP │        │
│ │ Adapter     │  │ Adapter     │  │ Adapter     │  │ Adapter     │        │
│ └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│        │                │                │                │                 │
│        └────────────────┴────────────────┴────────────────┘                 │
│                                    │                                         │
│                         ┌──────────▼──────────┐                             │
│                         │   Kafka Producer    │                             │
│                         └──────────┬──────────┘                             │
│                                    │                                         │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                              BACKEND (Cloud/Data Center)                     │
├────────────────────────────────────┼────────────────────────────────────────┤
│                                    │                                         │
│                         ┌──────────▼──────────┐                             │
│                         │   Kafka Cluster     │                             │
│                         │   (3 brokers)       │                             │
│                         └──────────┬──────────┘                             │
│                                    │                                         │
│              ┌─────────────────────┼─────────────────────┐                  │
│              │                     │                     │                  │
│              ▼                     ▼                     ▼                  │
│    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐        │
│    │   InfluxDB      │   │   PostgreSQL    │   │   Redis         │        │
│    │   (Time Series) │   │   (Metadata)    │   │   (Cache)       │        │
│    └─────────────────┘   └─────────────────┘   └─────────────────┘        │
│                                    │                                         │
│                         ┌──────────▼──────────┐                             │
│                         │   FastAPI Backend   │                             │
│                         └──────────┬──────────┘                             │
│                                    │                                         │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                              FRONTEND                                        │
├────────────────────────────────────┼────────────────────────────────────────┤
│                                    │                                         │
│                         ┌──────────▼──────────┐                             │
│                         │   React + Tremor    │                             │
│                         │   Dashboard         │                             │
│                         └─────────────────────┘                             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Componentes Principais

### 1. Gateway (Edge Computing)

O Gateway e o componente responsavel pela coleta de dados de campo.

**Responsabilidades:**
- Conexao com dispositivos de campo (PLCs, sensores, etc.)
- Descoberta automatica de tags
- Gerenciamento de tags (Point Builder)
- Publicacao de dados no Kafka
- Cache local de valores em tempo real

**Protocolos Suportados:**
- OPC-UA (Siemens S7, Rockwell via KEPServerEX)
- Modbus TCP/RTU (medidores, inversores)
- MQTT (sensores IoT)
- PROFINET (Siemens)
- EtherNet/IP (Allen-Bradley/Rockwell)

### 2. Backend (Data Center)

O Backend e responsavel pelo processamento e armazenamento de dados.

**Componentes:**
- **Kafka Cluster**: Mensageria para dados em tempo real
- **InfluxDB**: Banco de dados de series temporais
- **PostgreSQL**: Metadata, usuarios, configuracoes
- **Redis**: Cache de sessoes e dados frequentes
- **FastAPI**: API REST para o Frontend

### 3. Frontend (Dashboard)

Interface web para visualizacao e analise.

**Tecnologias:**
- React 18 + TypeScript
- Tremor UI Components
- Recharts para graficos
- WebSocket para dados em tempo real

---

## Premissas de Arquitetura

### 1. Gateway e Source of Truth para Tags

**Premissa:** O Gateway e a fonte de verdade (source of truth) para configuracao de tags.

```
┌─────────────────────────────────────────────────────────────────┐
│                    TAG MANAGEMENT FLOW                           │
│                    (Point Builder Pattern)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. DISCOVERY (Automatico)                                       │
│     - Gateway descobre tags dos dispositivos                     │
│     - Tags ficam disponiveis para selecao                        │
│     - NAO sao automaticamente historizado                       │
│                                                                  │
│  2. MANAGEMENT (Point Builder)                                   │
│     - Usuario seleciona quais tags historizar                    │
│     - Configuracao em tags_config.json                           │
│     - Define metadata: unidade, escala, deadband                 │
│                                                                  │
│  3. HISTORIZATION                                                │
│     - Apenas tags gerenciados vao para Kafka                     │
│     - Dados sao persistidos no InfluxDB                          │
│     - Compressao e deadband aplicados                            │
│                                                                  │
│  4. SYNC (Opcional)                                              │
│     - Gateway pode sincronizar metadata para Backend             │
│     - Backend NAO cria tags automaticamente                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Analogia com PI System:**
- `tags_config.json` = PI Point Builder
- Descoberta = PI Interface tag scan
- Historization = PI Archive

### 2. Separacao OT/IT

**Premissa:** Existe separacao clara entre rede OT (automacao) e IT (corporativa).

```
OT Network (192.168.1.0/24)          IT Network
┌─────────────────────────┐          ┌─────────────────────────┐
│ PLCs, Sensores, RTUs    │          │ Kafka, InfluxDB, API    │
│ Node-RED (Edge)         │◄────────►│ Frontend, Usuarios      │
│ Gateway                 │   DMZ    │                         │
└─────────────────────────┘          └─────────────────────────┘
```

### 3. Dados em Tempo Real vs Historicos

**Premissa:** Existem dois fluxos de dados distintos.

| Fluxo | Fonte | Uso |
|-------|-------|-----|
| **Tempo Real** | Gateway Buffer | Dashboards, Alarmes |
| **Historico** | InfluxDB | Trends, Relatorios |

```
                    ┌─────────────────────┐
                    │   Gateway Buffer    │
                    │   (Tempo Real)      │
                    └─────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
      ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
      │ WebSocket API │ │ REST API      │ │ Kafka         │
      │ (Dashboard)   │ │ (Consultas)   │ │ (Historico)   │
      └───────────────┘ └───────────────┘ └───────┬───────┘
                                                  │
                                                  ▼
                                          ┌───────────────┐
                                          │   InfluxDB    │
                                          │   (Archive)   │
                                          └───────────────┘
```

### 4. Virtual Adapters

**Premissa:** Virtual Adapters simulam protocolos reais usando o buffer Node-RED.

```
┌─────────────────────────────────────────────────────────────────┐
│                     VIRTUAL ADAPTER ARCHITECTURE                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Node-RED Simulator                                             │
│   └── Envia dados com metadata: {protocol: "OPC-UA", ...}        │
│                    │                                             │
│                    ▼                                             │
│   ┌────────────────────────────────┐                            │
│   │   HTTP Ingest Buffer           │                            │
│   │   (97 tags de todos protocolos)│                            │
│   └────────────────────────────────┘                            │
│                    │                                             │
│       ┌────────────┼────────────┬────────────┐                  │
│       │            │            │            │                  │
│       ▼            ▼            ▼            ▼                  │
│   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐               │
│   │OPC-UA  │  │MODBUS  │  │PROFINET│  │ENET/IP │               │
│   │Virtual │  │Virtual │  │Virtual │  │Virtual │               │
│   │Adapter │  │Adapter │  │Adapter │  │Adapter │               │
│   │        │  │        │  │        │  │        │               │
│   │Filtra: │  │Filtra: │  │Filtra: │  │Filtra: │               │
│   │OPC-UA  │  │MODBUS  │  │PROFINET│  │ENET/IP │               │
│   └────────┘  └────────┘  └────────┘  └────────┘               │
│       │            │            │            │                  │
│       └────────────┴────────────┴────────────┘                  │
│                           │                                      │
│                           ▼                                      │
│                    ┌──────────────┐                             │
│                    │    Kafka     │                             │
│                    │  raw_tags    │                             │
│                    └──────────────┘                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Equipamentos Simulados:**
- **OPC-UA**: ARZ_GATE01-04 (Comportas)
- **MODBUS**: CORR01-03 (Correias Transportadoras)
- **PROFINET**: ELV01 (Elevador), BLC01 (Balanca de Fluxo)
- **EtherNet/IP**: SLD01 (Shiploader), TRP01 (Tripper Car)

---

## Fluxo de Dados Detalhado

### 1. Coleta e Ingestao

```
Dispositivo → Protocolo → Adapter → Buffer → Kafka → InfluxDB
     │            │          │         │        │         │
     │            │          │         │        │         └─ Armazenamento permanente
     │            │          │         │        └─ Mensageria
     │            │          │         └─ Cache temporario
     │            │          └─ Normalizacao
     │            └─ Comunicacao
     └─ Origem do dado
```

### 2. Consulta de Dados

```
Frontend → Backend API → Redis (cache) → InfluxDB/PostgreSQL
                │
                └─ ou Gateway API (tempo real)
```

### 3. Alarmes

```
Gateway → Avalia Limites → Kafka (alarms) → Backend → Notificacoes
                                    │
                                    └─ PostgreSQL (historico)
```

---

## Configuracao de Tags (Point Builder)

### Arquivo: `gateway/config/tags_config.json`

```json
{
  "tags": [
    {
      "tag_id": "tag_abc123",
      "tag_name": "CORR01_FLOW_TPH_PV",
      "address": "virtual:MODBUS:CORR01_FLOW_TPH_PV",
      "adapter_id": "virtual-modbus-belts",
      "data_type": "double",
      "unit": "t/h",
      "description": "Correia 01 - Vazao",
      "historize": true,
      "compression_enabled": true,
      "compression_deviation": 0.5
    }
  ]
}
```

### Campos Importantes

| Campo | Descricao |
|-------|-----------|
| `tag_id` | Identificador unico |
| `tag_name` | Nome do tag |
| `address` | Endereco no dispositivo |
| `adapter_id` | Adapter responsavel |
| `data_type` | Tipo de dado (double, int32, boolean) |
| `unit` | Unidade de engenharia |
| `historize` | Se deve ser historizado |
| `compression_enabled` | Compressao ativa |
| `compression_deviation` | Deadband para compressao |

---

## Endpoints Principais

### Gateway API (localhost:8080)

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| `/api/adapters/` | GET | Lista adapters |
| `/api/adapters/{id}/discover` | POST | Descoberta de tags |
| `/api/adapters/{id}/tags` | GET | Tags do adapter |
| `/api/tags/realtime/all` | GET | Valores em tempo real |
| `/api/v1/data/ingest` | POST | Ingestao de dados |

### Backend API (localhost:8000)

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| `/api/v1/tags` | GET/POST | CRUD de tags |
| `/api/v1/timeseries/{tag}` | GET | Dados historicos |
| `/api/v1/alarms/` | GET | Alarmes |
| `/api/v1/dashboard/stats` | GET | Estatisticas |

---

## Tecnologias Utilizadas

### Backend
- **Python 3.11** - Linguagem principal
- **FastAPI** - Framework web
- **SQLAlchemy** - ORM
- **Celery** - Tarefas assincronas
- **asyncua** - Cliente OPC-UA
- **pymodbus** - Cliente Modbus

### Frontend
- **React 18** - UI Framework
- **TypeScript** - Tipagem
- **Vite** - Build tool
- **Tremor** - UI Components
- **Recharts** - Graficos

### Infraestrutura
- **Docker Compose** - Orquestracao
- **Kafka** - Mensageria (3 brokers)
- **InfluxDB 2.x** - Time Series DB
- **PostgreSQL 15** - Metadata DB
- **Redis** - Cache
- **Node-RED** - Simulacao/Edge

---

## Seguranca

### Autenticacao
- JWT tokens para API
- OAuth2 password flow
- Rate limiting por endpoint

### Rede
- Separacao OT/IT
- HTTPS para APIs externas
- Comunicacao interna via Docker network

---

## Escalabilidade

### Horizontal
- Kafka cluster com 3 brokers
- Backend stateless (pode ter multiplas instancias)
- Redis para cache distribuido

### Vertical
- InfluxDB com compressao e retention policies
- PostgreSQL com indices otimizados

---

## Monitoramento

### Metricas
- Prometheus metrics no Gateway
- Health checks em todos servicos
- Logs estruturados (JSON)

### Dashboards
- Grafana para metricas de infraestrutura
- Frontend proprio para dados de processo

---

## Proximos Passos

1. [ ] Implementar UI de Point Builder no Frontend
2. [ ] Adicionar autenticacao OPC-UA (certificates)
3. [ ] Implementar retention policies no InfluxDB
4. [ ] Adicionar suporte a Siemens S7 nativo
5. [ ] Implementar export de dados (CSV, Excel)
