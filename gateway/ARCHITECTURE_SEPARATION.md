# OptiFlow - Separação de Responsabilidades: Backend vs Gateway

## Princípio Fundamental

```
BACKEND = Plano de Controle (Cloud) - Fonte única de verdade
GATEWAY = Plano de Dados (Edge)     - Execução e cache local
```

---

## 1. Responsabilidades do BACKEND (Cloud)

O Backend é a **fonte única de verdade** para todas as configurações e dados persistentes.

### Funcionalidades EXCLUSIVAS do Backend:

| Categoria | Funcionalidade | Endpoint |
|-----------|---------------|----------|
| **Tags** | CRUD de definições | `POST/PUT/DELETE /api/v1/tags` |
| **Tags** | Metadados (scaling, deadband) | `PUT /api/v1/tags/{id}/config` |
| **Tags** | Histórico (time series) | `GET /api/v1/tags/{id}/history` |
| **Alarmes** | Definições de alarme | `POST/PUT/DELETE /api/v1/alarms` |
| **Alarmes** | Histórico de eventos | `GET /api/v1/alarms/events` |
| **Alarmes** | Acknowledge | `POST /api/v1/alarms/{id}/ack` |
| **Fórmulas** | Registro de fórmulas | `POST /api/v1/formulas` |
| **Segurança** | Emissão de JWT | `POST /api/v1/auth/token` |
| **Segurança** | RBAC/Permissões | `GET /api/v1/users/permissions` |
| **Segurança** | Audit log | Automático |
| **Analytics** | ML/AI | Todos os endpoints de ML |
| **Analytics** | Relatórios | `GET /api/v1/reports` |
| **Gestão** | Usuários | `CRUD /api/v1/users` |
| **Gestão** | Organizações | `CRUD /api/v1/organizations` |
| **Gestão** | Assets | `CRUD /api/v1/assets` |

### O que o Backend NÃO faz:
- ❌ Comunicação direta com PLCs
- ❌ Buffering de dados em tempo real
- ❌ Compressão SDT
- ❌ Avaliação de fórmulas em tempo real

---

## 2. Responsabilidades do GATEWAY (Edge)

O Gateway é o **plano de dados** focado em coleta e execução local.

### Funcionalidades EXCLUSIVAS do Gateway:

| Categoria | Funcionalidade | Endpoint/Serviço |
|-----------|---------------|------------------|
| **Protocolos** | OPC-UA Client | `opcua_adapter.py` |
| **Protocolos** | Modbus TCP | `modbus_adapter.py` |
| **Protocolos** | MQTT Client | `mqtt_adapter.py` |
| **Protocolos** | Descoberta OPC-UA | `GET /api/browse` |
| **Cache** | Valores em tempo real | `GET /api/tags/realtime/*` |
| **Cache** | Buffer para Kafka | `buffer.py`, `redis_buffer.py` |
| **Compressão** | SDT (Swinging Door) | `compression.py` |
| **Execução** | Avaliação de fórmulas | `formula_engine.py` |
| **Execução** | Disparo de alarmes | `alarm_evaluator.py` (a criar) |
| **Adaptadores** | Gestão local | `GET/POST /api/adapters` |

### O que o Gateway NÃO faz:
- ❌ CRUD de tags (apenas leitura/cache)
- ❌ Definição de alarmes (apenas avaliação)
- ❌ Emissão de tokens JWT (apenas validação)
- ❌ Persistência de histórico
- ❌ Analytics/ML

---

## 3. Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND (Cloud)                          │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │   Tags   │  │  Alarms  │  │ Formulas │  │  Authentication  │ │
│  │   CRUD   │  │   CRUD   │  │ Registry │  │   JWT Issuer     │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │
│       │             │             │                  │           │
│       └─────────────┴─────────────┴──────────────────┘           │
│                              │                                    │
│                    REST API (Config Sync)                        │
│                              │                                    │
└──────────────────────────────┼────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────┴────────────────────────────────────┐
│                         GATEWAY (Edge)                            │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                    Config Sync Client                         ││
│  │  - Busca tags do backend no startup                          ││
│  │  - Busca alarmes do backend no startup                       ││
│  │  - Busca fórmulas do backend no startup                      ││
│  │  - Polling periódico para atualizações                       ││
│  └──────────────────────────────────────────────────────────────┘│
│                              │                                    │
│         ┌────────────────────┼────────────────────┐              │
│         ▼                    ▼                    ▼              │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐         │
│  │    Tag     │      │   Alarm    │      │  Formula   │         │
│  │   Cache    │      │  Evaluator │      │   Engine   │         │
│  │ (read-only)│      │  (trigger) │      │  (compute) │         │
│  └─────┬──────┘      └─────┬──────┘      └─────┬──────┘         │
│        │                   │                   │                 │
│        ▼                   ▼                   ▼                 │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                    Protocol Adapters                          ││
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         ││
│  │  │ OPC-UA  │  │ Modbus  │  │  MQTT   │  │ Siemens │         ││
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘         ││
│  └───────┼────────────┼────────────┼────────────┼───────────────┘│
│          │            │            │            │                 │
│          └────────────┴────────────┴────────────┘                │
│                              │                                    │
│                              ▼                                    │
│                    ┌─────────────────┐                           │
│                    │      PLCs       │                           │
│                    │    Devices      │                           │
│                    └─────────────────┘                           │
│                                                                   │
│  ══════════════════════════════════════════════════════════════  │
│                                                                   │
│                    Data Output (Kafka)                           │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │  Topics:                                                      ││
│  │  - raw_tags        → Valores brutos dos PLCs                 ││
│  │  - alarm_events    → Eventos de alarme disparados            ││
│  │  - calculated_tags → Resultados de fórmulas                  ││
│  └──────────────────────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────┴────────────────────────────────────┐
│                      BACKEND (Consumers)                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐      │
│  │ timeseries_    │  │ alarm_event_   │  │ analytics_     │      │
│  │ consumer       │  │ consumer       │  │ consumer       │      │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘      │
│          │                   │                   │                │
│          ▼                   ▼                   ▼                │
│     InfluxDB            PostgreSQL           ML Pipeline         │
└───────────────────────────────────────────────────────────────────┘
```

---

## 4. Arquivos a Manter no Gateway

### ✅ MANTER (funcionalidade core):

```
gateway/app/
├── services/
│   ├── protocols/           # Adaptadores de protocolo
│   │   ├── base_adapter.py
│   │   ├── opcua_adapter.py
│   │   ├── modbus_adapter.py
│   │   └── mqtt_adapter.py
│   ├── protocol_manager.py  # Orquestração de protocolos
│   ├── device_manager.py    # Gestão de dispositivos
│   ├── buffer.py            # Buffer em memória
│   ├── redis_buffer.py      # Buffer Redis
│   ├── compression.py       # Compressão SDT
│   ├── kafka_producer.py    # Publicação Kafka
│   ├── formula_engine.py    # Avaliação de fórmulas
│   ├── opcua_browser.py     # Descoberta OPC-UA
│   ├── gateway_metrics.py   # Métricas Prometheus
│   └── backend_client.py    # Cliente do backend
├── api/routes/
│   ├── adapters.py          # Gestão de adaptadores
│   ├── tags_realtime.py     # Cache de valores (read-only)
│   └── websocket.py         # Streaming WebSocket
└── core/
    ├── config.py            # Configuração
    ├── logger.py            # Logging
    └── security.py          # Validação de tokens (simplificado)
```

### ❌ REMOVER/DEPRECAR (duplicação com backend):

```
gateway/app/
├── api/routes/
│   ├── tags_advanced.py     # ❌ REMOVER - Tag CRUD vai para backend
│   ├── tags_automation.py   # ⚠️ REFATORAR - Remover definições de alarme
│   └── security.py          # ⚠️ SIMPLIFICAR - Apenas validação
└── services/
    └── tag_manager.py       # ❌ REMOVER - Config vem do backend
```

---

## 5. Novo Serviço: Config Sync

Criar `gateway/app/services/config_sync.py`:

```python
"""
Config Sync Service
===================
Sincroniza configurações do Backend para o Gateway.
"""

class ConfigSyncService:
    """
    Responsabilidades:
    1. Buscar tags do backend no startup
    2. Buscar alarmes do backend no startup
    3. Buscar fórmulas do backend no startup
    4. Polling periódico para atualizações
    5. Notificar componentes sobre mudanças
    """

    async def sync_tags(self) -> List[TagConfig]:
        """Busca tags do backend"""
        response = await self.backend_client.get("/api/v1/tags")
        return [TagConfig(**t) for t in response]

    async def sync_alarms(self) -> List[AlarmConfig]:
        """Busca alarmes do backend"""
        response = await self.backend_client.get("/api/v1/alarms")
        return [AlarmConfig(**a) for a in response]

    async def sync_formulas(self) -> List[FormulaConfig]:
        """Busca fórmulas do backend"""
        response = await self.backend_client.get("/api/v1/formulas")
        return [FormulaConfig(**f) for f in response]
```

---

## 6. Endpoints do Gateway (Versão Final)

### API Pública (`:8080`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/api/adapters` | Listar adaptadores |
| `POST` | `/api/adapters/{id}/start` | Iniciar adaptador |
| `POST` | `/api/adapters/{id}/stop` | Parar adaptador |
| `GET` | `/api/tags/realtime/all` | Todos os valores (cache) |
| `GET` | `/api/tags/realtime/{name}` | Valor específico (cache) |
| `GET` | `/api/browse` | Descoberta OPC-UA |
| `WS` | `/ws/tags` | Stream de valores |
| `WS` | `/ws/alarms` | Stream de alarmes |

### Removidos (usar Backend):
- ~~`POST /api/tags`~~ → Backend
- ~~`PUT /api/tags/{id}`~~ → Backend
- ~~`DELETE /api/tags/{id}`~~ → Backend
- ~~`POST /api/alarms`~~ → Backend
- ~~`POST /api/security/token`~~ → Backend

---

## 7. Variáveis de Ambiente

```env
# Backend Connection
BACKEND_URL=http://backend:8000
BACKEND_API_KEY=secure-key

# Config Sync
CONFIG_SYNC_INTERVAL=60  # segundos
CONFIG_SYNC_ON_STARTUP=true

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka-1:9092,kafka-2:9093,kafka-3:9096
KAFKA_TOPIC_RAW_TAGS=raw_tags
KAFKA_TOPIC_ALARM_EVENTS=alarm_events
KAFKA_TOPIC_CALCULATED=calculated_tags

# Security (validação apenas)
JWT_SECRET=same-as-backend  # Mesmo segredo para validar tokens
JWT_ALGORITHM=HS256
```

---

## 8. Migração

### Fase 1: Preparação
1. Adicionar endpoint `/api/v1/gateway/config` no backend
2. Criar `config_sync.py` no gateway
3. Testar sync de tags

### Fase 2: Remoção
1. Deprecar `tags_advanced.py`
2. Remover CRUD de tags do gateway
3. Atualizar documentação

### Fase 3: Alarmes
1. Criar `alarm_evaluator.py` no gateway
2. Publicar eventos em `alarm_events` topic
3. Backend consome e persiste

### Fase 4: Segurança
1. Simplificar `security.py` no gateway
2. Usar mesmo JWT_SECRET do backend
3. Gateway apenas valida, não emite

---

## 9. Checklist de Validação

- [ ] Gateway não cria tags (apenas lê do backend)
- [ ] Gateway não define alarmes (apenas avalia)
- [ ] Gateway não emite tokens JWT
- [ ] Backend é fonte única de verdade
- [ ] Kafka é o canal de dados gateway → backend
- [ ] Config sync funciona no startup
- [ ] Métricas Prometheus separadas mas federadas
