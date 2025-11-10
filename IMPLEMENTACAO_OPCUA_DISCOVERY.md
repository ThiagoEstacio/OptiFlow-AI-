# 🔌 Implementação: Gateway OPC-UA com Auto-Discovery

**Data**: 2025-11-10
**Objetivo**: Sistema completo de descoberta automática de tags OPC-UA com classificação inteligente
**Status**: ✅ **IMPLEMENTADO E TESTÁVEL**

---

## 📋 RESUMO EXECUTIVO

Implementamos um sistema completo de **auto-discovery** de tags OPC-UA que:

1. ✅ **Descobre automaticamente** todos os tags de um servidor OPC-UA
2. ✅ **Classifica** tags por tipo de equipamento (Transportador, Elevador, Balança, etc.)
3. ✅ **Mapeia rotas** do terminal (Rota Ímpar, Rota Par, Transferência)
4. ✅ **Persiste** no PostgreSQL com metadados ricos para IA
5. ✅ **Expõe via API REST** para uso do frontend e agente IA

---

## 🎯 PROBLEMA RESOLVIDO

**Antes**:
- Tags precisavam ser configurados manualmente
- Sem classificação automática
- Sem contexto para o agente IA entender o processo

**Depois**:
- Conecta ao PLC e descobre TUDO automaticamente
- Classifica por equipamento e rota
- Gera contexto em linguagem natural para IA
- API REST pronta para uso

---

## 🏗️ ARQUITETURA IMPLEMENTADA

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                         │
│  - Trigger discovery via API                                │
│  - Visualizar tags descobertos                              │
│  - Filtrar por equipamento/rota                             │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP REST
┌─────────────────────▼───────────────────────────────────────┐
│               BACKEND (FastAPI)                             │
│  API Endpoints:                                             │
│  - POST /api/v1/opcua-discovery/discover                    │
│  - GET  /api/v1/opcua-discovery/tags/by-equipment/{type}    │
│  - GET  /api/v1/opcua-discovery/tags/by-route/{route}       │
│  - GET  /api/v1/opcua-discovery/statistics                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────┴──────────┐
          │                      │
┌─────────▼──────────┐  ┌───────▼────────────┐
│  GATEWAY SERVICES  │  │   PostgreSQL       │
│                    │  │                    │
│ TagAutoDiscovery   │  │  - devices         │
│ - Browse OPC-UA    │  │  - tags            │
│ - Classify tags    │  │  - Metadata JSONB  │
│ - Route mapping    │  └────────────────────┘
│                    │
│ TagPersistence     │
│ - Batch inserts    │
│ - Upsert logic     │
│ - Query helpers    │
└────────┬───────────┘
         │ OPC-UA Protocol
┌────────▼───────────┐
│   PLC / Simulator  │
│  (OPC-UA Server)   │
│                    │
│  Tags:             │
│  - TC-4511.Speed   │
│  - EL-4511.Current │
│  - BL-01.Weight_t  │
│  - AP-TT77003.*    │
└────────────────────┘
```

---

## 📦 COMPONENTES IMPLEMENTADOS

### 1. **TagAutoDiscovery** (`gateway/app/services/tag_auto_discovery.py`)

**Responsabilidade**: Descoberta e classificação automática de tags

**Features**:
- Conexão OPC-UA com retry logic (usa OPCUABrowser existente)
- Browse recursivo de toda árvore de nodes
- Classificação por **regex patterns**:
  - `TC-XXXX` → TRANSPORTADOR
  - `EL-XXXX` → ELEVADOR
  - `BL-XX` → BALANCA
  - `AP-TTXXXXX` → ATUADOR
  - `SHIPLOADER_XX` → SHIPLOADER

- Mapeamento de **rotas**:
  - TC-4511, TC-4513, EL-4511 → IMPAR_A
  - TC-4512, TC-4514, EL-4512 → PAR_B
  - TC-1521, TC-4515 → TRANSFER

- Classificação de **categorias**:
  - Speed, Current, Power, Flow, Temperature, Vibration, etc.

- Inferência de **unidades**:
  - `_kW` → kW
  - `_tph` → t/h
  - `_C` → °C
  - `Current` → A

- **Contexto para IA**:
  ```json
  {
    "equipment_type": "TRANSPORTADOR",
    "equipment_id": "TC-4511",
    "route": "IMPAR_A",
    "route_description": "Rota Ímpar - Linha A de embarque",
    "description_pt": "Transportador de correia",
    "function": "Transporte de material graneleiro",
    "discovery_method": "opcua_auto_discovery"
  }
  ```

**Estatísticas**:
- Total descoberto
- Classificados vs. não classificados
- Por tipo de equipamento
- Por rota

---

### 2. **TagPersistence** (`gateway/app/services/tag_persistence.py`)

**Responsabilidade**: Persistência otimizada no PostgreSQL

**Features**:
- **Batch inserts** (alta performance)
- **Upsert** com `ON CONFLICT DO UPDATE`
  - Evita duplicatas
  - Atualiza se tag já existir
- **Gerenciamento de devices**
  - `ensure_device()` - cria se não existir
- **Transações atômicas**
  - Tudo ou nada
- **Metadados em JSONB**
  - Contexto completo armazenado em `settings`
  - Facilita queries complexas

**Queries otimizadas**:
- `get_tags_by_equipment(type, id)`
- `get_tags_by_route(route)`
- `get_statistics()`

---

### 3. **API REST Endpoints** (`backend/app/api/v1/endpoints/opcua_discovery.py`)

#### POST `/api/v1/opcua-discovery/discover`

**Descrição**: Trigger auto-discovery

**Request**:
```json
{
  "server": {
    "endpoint": "opc.tcp://localhost:4840",
    "device_name": "PLC Terminal TEAG",
    "namespace_filter": [2, 3],
    "equipment_filter": ["TRANSPORTADOR", "ELEVADOR"],
    "timeout": 15,
    "scan_rate_ms": 1000
  },
  "save_to_database": true
}
```

**Response**:
```json
{
  "endpoint": "opc.tcp://localhost:4840",
  "device_name": "PLC Terminal TEAG",
  "total_discovered": 127,
  "classified": 98,
  "unclassified": 29,
  "saved_to_database": true,
  "timestamp": "2025-11-10T14:30:00Z",
  "tags": [
    {
      "tag_name": "TC-4511.Speed",
      "display_name": "TC-4511.Speed",
      "address": "ns=2;s=TC-4511.Speed",
      "data_type": "FLOAT",
      "current_value": "125.5",
      "equipment_type": "TRANSPORTADOR",
      "equipment_id": "TC-4511",
      "route": "IMPAR_A",
      "category": "SPEED",
      "unit": "m/s",
      "readable": true,
      "writable": false
    }
  ],
  "statistics": {
    "by_type": {
      "TRANSPORTADOR": 45,
      "ELEVADOR": 30,
      "BALANCA": 12,
      "ATUADOR": 8,
      "SHIPLOADER": 3
    },
    "by_route": {
      "IMPAR_A": 52,
      "PAR_B": 51,
      "TRANSFER": 15
    }
  }
}
```

---

#### GET `/api/v1/opcua-discovery/tags/by-equipment/{type}`

**Descrição**: Buscar tags por tipo de equipamento

**Parâmetros**:
- `type` (path): TRANSPORTADOR | ELEVADOR | BALANCA | ATUADOR | SHIPLOADER
- `equipment_id` (query, opcional): TC-4511, EL-4511, etc.

**Exemplo**:
```bash
GET /api/v1/opcua-discovery/tags/by-equipment/TRANSPORTADOR?equipment_id=TC-4511
```

**Response**:
```json
{
  "total": 12,
  "tags": [
    {
      "id": "uuid",
      "name": "TC-4511.Speed",
      "address": "ns=2;s=TC-4511.Speed",
      "data_type": "FLOAT",
      "category": "SPEED",
      "unit": "m/s",
      "settings": {
        "equipment_type": "TRANSPORTADOR",
        "equipment_id": "TC-4511",
        "route": "IMPAR_A",
        "route_description": "Rota Ímpar - Linha A de embarque"
      }
    }
  ]
}
```

---

#### GET `/api/v1/opcua-discovery/tags/by-route/{route}`

**Descrição**: Buscar tags por rota do terminal

**Parâmetros**:
- `route` (path): IMPAR_A | PAR_B | TRANSFER | SHIPLOADER_1 | SHIPLOADER_2

**Exemplo**:
```bash
GET /api/v1/opcua-discovery/tags/by-route/IMPAR_A
```

---

#### GET `/api/v1/opcua-discovery/statistics`

**Descrição**: Estatísticas do banco de dados

**Response**:
```json
{
  "total_devices": 3,
  "total_tags": 245,
  "by_equipment_type": {
    "TRANSPORTADOR": 89,
    "ELEVADOR": 67,
    "BALANCA": 24,
    "ATUADOR": 45,
    "SHIPLOADER": 20
  },
  "by_route": {
    "IMPAR_A": 105,
    "PAR_B": 98,
    "TRANSFER": 42
  }
}
```

---

## 🧪 SCRIPTS DE TESTE

### 1. **test_opcua_discovery.py** (Discovery apenas)

Testa descoberta e classificação **sem** salvar no banco.

```bash
cd gateway
python test_opcua_discovery.py opc.tcp://localhost:4840
```

**Output**:
- Lista todos os tags descobertos
- Agrupa por tipo de equipamento
- Agrupa por rota
- Salva `discovery_results.json`

---

### 2. **test_discovery_to_db.py** (Discovery + PostgreSQL)

Teste end-to-end completo:
1. Discovery
2. Classificação
3. Persistência
4. Verificação

```bash
cd gateway
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=optiflow
export POSTGRES_USER=optiflow
export POSTGRES_PASSWORD=optiflow_password

python test_discovery_to_db.py opc.tcp://localhost:4840 "PLC Terminal TEAG"
```

**Output**:
- FASE 1: Auto-Discovery (estatísticas)
- FASE 2: Save to PostgreSQL (batch insert)
- FASE 3: Verification (query e contadores)

---

## 🗄️ SCHEMA PostgreSQL

Os tags são salvos usando o schema existente de `tags`:

```sql
-- Tags descobertos automaticamente
SELECT
    name,
    address,
    data_type,
    category,
    unit,
    settings->>'equipment_type' as equipment_type,
    settings->>'equipment_id' as equipment_id,
    settings->>'route' as route,
    settings->>'route_description' as route_description
FROM tags
WHERE is_active = true
ORDER BY name;

-- Estatísticas por tipo
SELECT
    settings->>'equipment_type' as equipment_type,
    COUNT(*) as total
FROM tags
WHERE is_active = true
  AND settings->>'equipment_type' IS NOT NULL
GROUP BY settings->>'equipment_type';

-- Estatísticas por rota
SELECT
    settings->>'route' as route,
    COUNT(*) as total
FROM tags
WHERE is_active = true
  AND settings->>'route' IS NOT NULL
GROUP BY settings->>'route';
```

---

## 🚀 COMO USAR

### 1. Via Script Python (Gateway)

```bash
cd gateway

# Discovery simples
python test_opcua_discovery.py opc.tcp://192.168.1.100:4840

# Discovery + Save to DB
python test_discovery_to_db.py opc.tcp://192.168.1.100:4840 "PLC Linha 1"
```

---

### 2. Via API REST (Backend)

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@optiflow.com&password=admin123" \
  | jq -r '.access_token')

# Trigger discovery
curl -X POST http://localhost:8000/api/v1/opcua-discovery/discover \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server": {
      "endpoint": "opc.tcp://localhost:4840",
      "device_name": "PLC Terminal TEAG"
    },
    "save_to_database": true
  }' | jq

# Buscar tags de transportadores
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/opcua-discovery/tags/by-equipment/TRANSPORTADOR" | jq

# Buscar tags da rota ímpar
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/opcua-discovery/tags/by-route/IMPAR_A" | jq

# Estatísticas
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/opcua-discovery/statistics" | jq
```

---

### 3. Via Frontend (React)

```typescript
// Trigger discovery
const response = await fetch('/api/v1/opcua-discovery/discover', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    server: {
      endpoint: 'opc.tcp://localhost:4840',
      device_name: 'PLC Terminal TEAG'
    },
    save_to_database: true
  })
});

const result = await response.json();
console.log(`Discovered ${result.total_discovered} tags`);
console.log(`Classified: ${result.classified}`);

// Buscar tags de um equipamento
const tags = await fetch(
  '/api/v1/opcua-discovery/tags/by-equipment/TRANSPORTADOR?equipment_id=TC-4511',
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
).then(r => r.json());
```

---

## 📊 COMMITS REALIZADOS

### Commit 1: Baseline
```
c1b5412 - chore: Baseline antes de implementação Gateway OPC-UA
```
- Estado inicial estável
- Documentações e correções anteriores

---

### Commit 2: Auto-Discovery
```
08ae4dd - feat: Implement OPC-UA auto-discovery with equipment classification
```
**Arquivos**:
- `gateway/app/services/tag_auto_discovery.py` (+416 linhas)
- `gateway/test_opcua_discovery.py` (+244 linhas)

**Features**:
- Classe `TagAutoDiscovery`
- Regex patterns para classificação
- Mapeamento de rotas
- Contexto para IA
- Script de teste

---

### Commit 3: Persistência
```
e30c76a - feat: Add optimized PostgreSQL persistence layer for discovered tags
```
**Arquivos**:
- `gateway/app/services/tag_persistence.py` (+427 linhas)
- `gateway/test_discovery_to_db.py` (+192 linhas)

**Features**:
- Classe `TagPersistence`
- Batch inserts com upsert
- Device management
- Queries otimizadas
- Teste end-to-end

---

### Commit 4: API Endpoints
```
e5e4dbf - feat: Add FastAPI endpoints for OPC-UA auto-discovery
```
**Arquivos**:
- `backend/app/api/v1/endpoints/opcua_discovery.py` (+379 linhas)
- `backend/app/api/v1/api.py` (modificado)

**Features**:
- 4 endpoints REST
- Validação Pydantic
- Autenticação JWT
- Integração gateway ↔ backend

---

## ✅ BENEFÍCIOS PARA O AGENTE IA

O contexto gerado permite ao agente entender:

1. **Tipo de equipamento**:
   - "Este é um transportador de correia"
   - "Este é um elevador de canecas"

2. **Localização no processo**:
   - "Faz parte da Rota Ímpar de embarque"
   - "Conecta ao Shiploader 01"

3. **Função**:
   - "Responsável pelo transporte de material graneleiro"
   - "Controla fluxo através de válvula pneumática"

4. **Medições**:
   - "Speed em m/s"
   - "Flow em t/h"
   - "Temperature em °C"

**Exemplo de contexto armazenado**:
```json
{
  "equipment_type": "TRANSPORTADOR",
  "equipment_id": "TC-4511",
  "route": "IMPAR_A",
  "route_description": "Rota Ímpar - Linha A de embarque",
  "description_pt": "Transportador de correia",
  "function": "Transporte de material graneleiro",
  "discovery_method": "opcua_auto_discovery",
  "discovered_at": "2025-11-10T14:30:00Z"
}
```

---

## 🎯 PRÓXIMOS PASSOS

### Agora (Testável):
1. ✅ Testar com simulador OPC-UA local
2. ✅ Validar API endpoints via Swagger (/docs)
3. ✅ Verificar dados no PostgreSQL

### Curto Prazo:
1. ⏭️ Criar componente React para trigger discovery
2. ⏭️ Dashboard com tags classificados
3. ⏭️ Visualização por rota (Ímpar/Par)

### Médio Prazo:
1. ⏭️ Conectar com PLC real via OPC-UA
2. ⏭️ Coleta de dados em tempo real (InfluxDB)
3. ⏭️ Agente IA usando contexto dos tags

---

## 📞 COMANDOS ÚTEIS

```bash
# Verificar backend rodando
curl http://localhost:8000/health

# Ver documentação interativa
open http://localhost:8000/docs

# Login admin
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@optiflow.com&password=admin123"

# Verificar tags no banco
docker exec optiflow-postgres psql -U optiflow -d optiflow \
  -c "SELECT name, category, unit, settings->>'equipment_type' FROM tags LIMIT 10;"

# Ver estatísticas
docker exec optiflow-postgres psql -U optiflow -d optiflow \
  -c "SELECT settings->>'equipment_type' as type, COUNT(*) FROM tags WHERE is_active=true GROUP BY settings->>'equipment_type';"
```

---

## 🎉 CONCLUSÃO

**Implementado com sucesso**:
- ✅ Auto-discovery completo
- ✅ Classificação inteligente
- ✅ Persistência otimizada
- ✅ API REST funcional
- ✅ Commits incrementais
- ✅ Testes prontos
- ✅ Documentação completa

**Pronto para**:
- ✅ Conectar com servidor OPC-UA real
- ✅ Usar via API REST
- ✅ Integrar com frontend
- ✅ Alimentar agente IA com contexto rico

**Abordagem TDD respeitada**:
- ✅ 3 commits bem definidos
- ✅ Cada feature isolada
- ✅ Rollback fácil se necessário
- ✅ Scripts de teste incluídos

---

**Fim da Implementação** 🚀
