# 🔌 Plano de Implementação: Gateway OPC-UA com Auto-Discovery

**Projeto**: OptiFlow AI - Terminal Portuário TEAG
**Objetivo**: Implementar coleta automática de tags via OPC-UA
**Prioridade**: ALTA - Base para toda plataforma

---

## 🎯 OBJETIVO

Implementar Gateway OPC-UA capaz de:
1. **Conectar** ao servidor OPC-UA (PLC/Simulador)
2. **Descobrir automaticamente** todos os tags disponíveis
3. **Mapear** tags para estrutura do terminal (Rota Ímpar/Par)
4. **Coletar** dados em tempo real
5. **Gravar** no InfluxDB e PostgreSQL
6. **Disponibilizar** para frontend via API

---

## 🏗️ ARQUITETURA DO TERMINAL TEAG

### Rota Ímpar (A)
```
TC-4511 → TC-4513 → EL-4511 → BL-01 → AP-TT77003-01A/B
                                          ↓
                                     TC-1521
                                     ↙     ↘
                              TC-2512      TC-2522
                                ↓            ↓
                          Shiploader 01  Shiploader 02
```

### Rota Par (B)
```
TC-4512 → TC-4514 → EL-4512 → BL-02 → AP-TT77003-02A/B
                                          ↓
                                   TC-1521/TC-1511
                                     ↙         ↘
                              TC-2512          TC-2522
                                ↓                ↓
                          Shiploader 01    Shiploader 02
```

### Rota de Transferência
```
TC-1521 / TC-4515 ← → AP-TT77002-01/02 → BL-01/BL-02
```

---

## 📋 TAGS ESPERADAS POR EQUIPAMENTO

### Transportador de Correia (TC)
```
TC-XXXX.Speed          // Velocidade (m/s)
TC-XXXX.Current        // Corrente (A)
TC-XXXX.Running        // Estado Running (BOOL)
TC-XXXX.Stop           // Estado Stop (BOOL)
TC-XXXX.Alarm          // Alarme ativo (BOOL)
TC-XXXX.Fault          // Falha (BOOL)
TC-XXXX.Power_kW       // Potência (kW)
TC-XXXX.Flow_tph       // Vazão (t/h)
TC-XXXX.Load_pct       // Carga (%)
TC-XXXX.Temp_C         // Temperatura (°C)
TC-XXXX.Misalignment   // Desalinhamento (mm)
```

### Elevador de Canecas (EL)
```
EL-XXXX.Speed
EL-XXXX.Current
EL-XXXX.Running
EL-XXXX.Stop
EL-XXXX.Alarm
EL-XXXX.Fault
EL-XXXX.Power_kW
EL-XXXX.Bucket_Speed   // Velocidade das canecas
EL-XXXX.Vibration      // Vibração
```

### Balança (BL)
```
BL-XX.Weight_t         // Peso atual (t)
BL-XX.Flow_tph         // Vazão (t/h)
BL-XX.Total_t          // Total acumulado (t)
BL-XX.Running
BL-XX.Alarm
BL-XX.Fault
```

### Atuador Pneumático (AP)
```
AP-TTXXXXX-XXX.Position_Open   // Aberto (BOOL)
AP-TTXXXXX-XXX.Position_Closed // Fechado (BOOL)
AP-TTXXXXX-XXX.Fault           // Falha
AP-TTXXXXX-XXX.Command_Open    // Comando Abrir
AP-TTXXXXX-XXX.Command_Close   // Comando Fechar
```

### Shiploader
```
SHIPLOADER_XX.Flow_tph         // Vazão (t/h)
SHIPLOADER_XX.Total_Loaded_t   // Total embarcado (t)
SHIPLOADER_XX.Running
SHIPLOADER_XX.Setpoint_tph     // Setpoint de vazão
SHIPLOADER_XX.Power_kW
```

---

## 🔧 COMPONENTES A IMPLEMENTAR

### 1. Gateway Service (Python)
**Arquivo**: `/gateway/app/services/opcua_browser.py`

**Funcionalidades**:
- [ ] Conectar ao servidor OPC-UA
- [ ] Browse automático da árvore de nodes
- [ ] Identificar todos os tags
- [ ] Classificar tags por equipamento
- [ ] Manter conexão persistente
- [ ] Reconexão automática em caso de falha

### 2. Auto-Discovery Engine
**Arquivo**: `/gateway/app/services/auto_discovery.py`

**Funcionalidades**:
- [ ] Escanear servidor OPC-UA
- [ ] Extrair metadados (nome, tipo, unidade)
- [ ] Criar estrutura hierárquica
- [ ] Mapear para modelo OptiFlow
- [ ] Gerar configuração automática
- [ ] Detectar novos tags

### 3. Tag Mapper
**Arquivo**: `/gateway/app/services/tag_mapper.py`

**Funcionalidades**:
- [ ] Regex patterns para identificar equipamentos
- [ ] Mapeamento TC-XXXX → Transportador
- [ ] Mapeamento EL-XXXX → Elevador
- [ ] Mapeamento BL-XX → Balança
- [ ] Mapeamento AP-TTXXXXX → Atuador
- [ ] Categorização automática

### 4. Data Collector
**Arquivo**: `/gateway/app/services/data_collector.py`

**Funcionalidades**:
- [ ] Polling otimizado
- [ ] Batch reading (múltiplos tags)
- [ ] Change detection (só grava mudanças)
- [ ] Buffer local (em caso de desconexão)
- [ ] Priorização de tags críticos

### 5. Data Persistence
**Arquivo**: `/gateway/app/services/data_persistence.py`

**Funcionalidades**:
- [ ] Gravar time-series no InfluxDB
- [ ] Gravar metadados no PostgreSQL
- [ ] Batch writes para performance
- [ ] Retry logic
- [ ] Health monitoring

---

## 📊 MODELO DE DADOS

### PostgreSQL - Devices
```sql
CREATE TABLE devices (
    id UUID PRIMARY KEY,
    name VARCHAR(255),          -- "PLC Terminal TEAG"
    protocol VARCHAR(50),       -- "OPC_UA"
    connection_config JSONB,    -- {url, security, etc}
    status VARCHAR(50),         -- CONNECTED, DISCONNECTED
    last_seen TIMESTAMP,
    total_tags INTEGER,
    discovered_at TIMESTAMP
);
```

### PostgreSQL - Tags
```sql
CREATE TABLE tags (
    id UUID PRIMARY KEY,
    device_id UUID REFERENCES devices(id),
    name VARCHAR(255),          -- "TC-4511.Speed"
    address VARCHAR(500),       -- "ns=2;s=TC-4511.Speed"
    data_type VARCHAR(50),      -- "FLOAT", "BOOL", etc
    unit VARCHAR(50),           -- "m/s", "A", "kW"
    category VARCHAR(50),       -- "SPEED", "CURRENT", etc
    equipment_type VARCHAR(50), -- "TRANSPORTADOR", "ELEVADOR"
    equipment_id VARCHAR(50),   -- "TC-4511"
    route VARCHAR(50),          -- "IMPAR_A", "PAR_B", "TRANSFER"
    scan_rate_ms INTEGER,       -- 1000 (1 segundo)
    min_value FLOAT,
    max_value FLOAT,
    is_active BOOLEAN,
    discovered_at TIMESTAMP
);
```

### InfluxDB - Measurements
```
measurement: equipment_data
tags:
  - equipment_id (TC-4511)
  - equipment_type (TRANSPORTADOR)
  - route (IMPAR_A)
  - tag_name (Speed)
fields:
  - value (FLOAT)
  - quality (GOOD/BAD)
timestamp: RFC3339
```

---

## 🚀 IMPLEMENTAÇÃO EM FASES

### FASE 1: Gateway Básico (2-3 dias)

#### Dia 1: Estrutura e Conexão
- [ ] Criar estrutura de pastas do gateway
- [ ] Implementar `opcua_client.py` básico
- [ ] Conectar ao servidor OPC-UA
- [ ] Listar nodes raiz
- [ ] Teste de ping/pong

**Entregável**: Gateway conecta e lista nodes raiz

#### Dia 2: Auto-Discovery
- [ ] Implementar browse recursivo
- [ ] Extrair todos os tags
- [ ] Identificar tipos de dados
- [ ] Salvar em JSON temporário
- [ ] Log de descoberta

**Entregável**: Lista completa de tags descobertos

#### Dia 3: Mapeamento e Persistência
- [ ] Implementar regex para classificação
- [ ] Mapear equipamentos
- [ ] Gravar em PostgreSQL
- [ ] Validar estrutura

**Entregável**: Tags classificados e salvos no banco

---

### FASE 2: Coleta de Dados (2-3 dias)

#### Dia 4: Polling e Leitura
- [ ] Implementar polling loop
- [ ] Batch reading otimizado
- [ ] Change detection
- [ ] Buffer local

**Entregável**: Gateway lendo valores em tempo real

#### Dia 5: InfluxDB Integration
- [ ] Gravar time-series
- [ ] Batch writes
- [ ] Validar performance
- [ ] Monitorar latência

**Entregável**: Dados fluindo para InfluxDB

#### Dia 6: API Backend
- [ ] Endpoint `GET /tags`
- [ ] Endpoint `GET /tags/realtime`
- [ ] Endpoint `GET /tags/history`
- [ ] Endpoint `POST /discovery/scan`

**Entregável**: API retornando dados reais

---

### FASE 3: Frontend e Visualização (2-3 dias)

#### Dia 7: Componentes React
- [ ] Lista de equipamentos
- [ ] Card por equipamento
- [ ] Indicadores visuais (Running/Stop)
- [ ] Valores em tempo real

**Entregável**: Frontend mostrando equipamentos

#### Dia 8: Gráficos
- [ ] Gráfico de velocidade
- [ ] Gráfico de corrente
- [ ] Gráfico de vazão
- [ ] Histórico temporal

**Entregável**: Gráficos atualizando em tempo real

#### Dia 9: Dashboard Consolidado
- [ ] Vista Rota Ímpar
- [ ] Vista Rota Par
- [ ] Vista Consolidada
- [ ] Alarmes ativos

**Entregável**: Dashboard completo do terminal

---

## 🧪 TESTES E VALIDAÇÃO

### Teste 1: Conexão OPC-UA
```python
# Script de teste
python test_opcua_connection.py --url opc.tcp://localhost:4840
```
**Esperado**: Conexão estabelecida, nodes listados

### Teste 2: Auto-Discovery
```python
# Script de teste
python test_auto_discovery.py --scan-depth 5
```
**Esperado**: 100+ tags descobertos e classificados

### Teste 3: Coleta em Tempo Real
```bash
# Verificar dados no InfluxDB
curl http://localhost:8086/api/v2/query \
  -H "Authorization: Token TOKEN" \
  --data-urlencode 'org=optiflow' \
  --data-urlencode 'query=from(bucket:"timeseries") |> range(start: -5m)'
```
**Esperado**: Dados recentes dos últimos 5 minutos

### Teste 4: Performance
- [ ] Latência < 100ms por tag
- [ ] Throughput > 1000 tags/segundo
- [ ] CPU < 10% em idle
- [ ] Memória < 500MB

---

## 📈 MÉTRICAS DE SUCESSO

### Curto Prazo (1 semana)
- ✅ Gateway conectado ao OPC-UA
- ✅ 100+ tags descobertos automaticamente
- ✅ Dados gravados no InfluxDB
- ✅ API retornando dados reais
- ✅ Frontend com 1 gráfico funcionando

### Médio Prazo (2 semanas)
- ✅ Coleta de 500+ tags
- ✅ Dashboard com Rotas Ímpar e Par
- ✅ Alarmes baseados em dados reais
- ✅ WebSocket para updates em tempo real
- ✅ 99% uptime do gateway

### Longo Prazo (1 mês)
- ✅ Múltiplos servidores OPC-UA
- ✅ 1000+ tags coletados
- ✅ ML treinando com dados reais
- ✅ Agente IA analisando padrões
- ✅ Sistema em produção

---

## 🔧 CONFIGURAÇÃO INICIAL

### 1. Configurar Servidor OPC-UA

Se usar simulador:
```python
# Iniciar servidor OPC-UA simulado
python backend/scripts/run_opcua_server.py
```

Se usar PLC real:
```yaml
# gateway/config/devices.yaml
devices:
  - name: "PLC Terminal TEAG"
    protocol: "OPC_UA"
    url: "opc.tcp://192.168.1.100:4840"
    security_mode: "None"  # ou "Sign", "SignAndEncrypt"
    security_policy: "None"
    username: ""  # se necessário
    password: ""  # se necessário
```

### 2. Estrutura de Tags Esperada

O gateway procurará tags seguindo padrões:
```
TC-XXXX.*      → Transportadores
EL-XXXX.*      → Elevadores
BL-XX.*        → Balanças
AP-TTXXXXX.*   → Atuadores
SHIPLOADER_*   → Shiploaders
```

### 3. Mapeamento Automático

```python
# Regex patterns para identificação
PATTERNS = {
    'TRANSPORTADOR': r'^TC-\d{4}',
    'ELEVADOR': r'^EL-\d{4}',
    'BALANCA': r'^BL-\d{2}',
    'ATUADOR': r'^AP-TT\d{5}',
    'SHIPLOADER': r'^SHIPLOADER_\d{2}'
}

# Classificação de rota
ROUTE_MAPPING = {
    'TC-4511': 'IMPAR_A',
    'TC-4513': 'IMPAR_A',
    'TC-4512': 'PAR_B',
    'TC-4514': 'PAR_B',
    'TC-1521': 'TRANSFER',
    'TC-4515': 'TRANSFER'
}
```

---

## 📝 PRÓXIMOS PASSOS IMEDIATOS

### Hoje (Dia 1)
1. ✅ Criar este plano detalhado ← **COMPLETO!**
2. ⏭️ Verificar se gateway service existe
3. ⏭️ Implementar conexão OPC-UA básica
4. ⏭️ Testar browse de nodes
5. ⏭️ Listar tags disponíveis

### Amanhã (Dia 2)
1. Implementar auto-discovery completo
2. Extrair metadados dos tags
3. Salvar estrutura em JSON
4. Validar classificação

### Depois de Amanhã (Dia 3)
1. Gravar tags no PostgreSQL
2. Iniciar coleta de dados
3. Gravar no InfluxDB
4. Criar endpoint de API

---

## 🎯 ENTREGÁVEL FINAL (1 Semana)

**Dashboard Funcional** mostrando:

```
┌─────────────────────────────────────────────────────────┐
│            TERMINAL TEAG - EMBARQUE                     │
├─────────────────────────────────────────────────────────┤
│  ROTA ÍMPAR (A)                  ROTA PAR (B)           │
│  ┌─────────┐                     ┌─────────┐            │
│  │ TC-4511 │ ▶ [dados reais]    │ TC-4512 │            │
│  │ Speed   │   125.5 m/s        │ Speed   │            │
│  │ Current │   245 A            │ Current │            │
│  └─────────┘                     └─────────┘            │
│                                                          │
│  [Gráfico velocidade em tempo real]                     │
│  [Gráfico corrente em tempo real]                       │
│  [Gráfico vazão em tempo real]                          │
│                                                          │
│  SHIPLOADERS                                             │
│  Shiploader 01: 1450 t/h  |  Total: 12,450 t           │
│  Shiploader 02: OFFLINE                                  │
└─────────────────────────────────────────────────────────┘
```

---

**Quer que eu comece implementando o Gateway OPC-UA agora?**

Vou verificar o que já existe e começar pela conexão básica e auto-discovery! 🚀