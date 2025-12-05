# OptiFlow - Premissas Arquiteturais

> **IMPORTANTE**: Este documento DEVE ser consultado antes de iniciar qualquer implementação.
> Última atualização: 2025-12-04

---

## 0. Regras de Ouro

```
┌────────────────────────────────────────────────────────────────────────────┐
│  O NODE-RED É O SIMULADOR DE CAMPO - EXPÕE SERVIDORES DE PROTOCOLO REAL   │
│  OS ADAPTERS DO GATEWAY JÁ EXISTEM - NÃO DEVEM SER MODIFICADOS            │
│  QUANDO USAR EQUIPAMENTO REAL, SÓ MUDA O HOST NO ADAPTER                  │
└────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│  TAGS SÃO DESCOBERTOS E GERENCIADOS PELO GATEWAY                          │
│  SOMENTE TAGS GERENCIADOS VÃO PARA O KAFKA → BACKEND → FRONTEND           │
│  O GATEWAY É A ÚNICA FONTE DE VERDADE PARA TAGS                           │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Fluxo de Dados (IMUTÁVEL)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUXO DE DADOS OPTIFLOW                           │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌───────────┐
  │   CAMPO     │ ───► │   GATEWAY   │ ───► │   BACKEND   │ ───► │ FRONTEND  │
  │  (Node-RED) │      │  (Adapters) │      │  (FastAPI)  │      │  (React)  │
  └─────────────┘      └─────────────┘      └─────────────┘      └───────────┘
        │                    │                    │                    │
   Protocolos            Kafka              InfluxDB              WebSocket
   Industriais         raw_tags            PostgreSQL               REST
        │                    │                 Redis                   │
        ▼                    ▼                    ▼                    ▼
   • OPC-UA             Coleta e           Armazena e            Visualiza
   • Modbus TCP         Normaliza          Processa              e Controla
   • EtherNet/IP
   • MQTT
   • S7
```

---

## 2. Papel de Cada Componente

### 2.1 Node-RED (Simulador de Campo)

**O QUE É:**
- Simulador que se comporta EXATAMENTE como equipamentos reais de campo
- Expõe servidores de protocolo industrial (não clientes!)

**O QUE DEVE FAZER:**
- ✅ Expor servidor OPC-UA na porta 4840 (comporta-se como um PLC Siemens)
- ✅ Expor servidor Modbus TCP na porta 502 (comporta-se como medidores de energia)
- ✅ Publicar em tópicos MQTT (comporta-se como sensores IoT)
- ✅ Simular física realista dos equipamentos
- ✅ Gerar alarmes e eventos

**O QUE NÃO DEVE FAZER:**
- ❌ Enviar dados via HTTP POST diretamente para o Gateway
- ❌ Conectar-se como cliente a outros servidores
- ❌ Conhecer a existência do Backend ou Frontend

### 2.2 Gateway (Coletor e Gerenciador de Tags)

**O QUE É:**
- Microsserviço que conecta ao CAMPO usando protocolos industriais
- Funciona como "diodo de dados" entre rede OT e IT
- **ÚNICA FONTE DE VERDADE para tags** - descobre, gerencia e publica

**O QUE DEVE FAZER:**
- ✅ Conectar como CLIENTE OPC-UA ao Node-RED (ou PLC real)
- ✅ Conectar como CLIENTE Modbus TCP ao Node-RED (ou medidores reais)
- ✅ Subscrever em tópicos MQTT
- ✅ **DESCOBRIR tags automaticamente** via protocolos (auto-discovery)
- ✅ **GERENCIAR tags** - apenas tags gerenciados vão para Kafka
- ✅ Publicar dados normalizados no Kafka (topic: raw_tags)
- ✅ Usar adapters configuráveis (adapters_config.json)
- ✅ Enriquecer tags descobertos com metadados (alarmes, historian) via tags_config.json

**O QUE NÃO DEVE FAZER:**
- ❌ Receber dados via HTTP POST do simulador
- ❌ Ter lógica específica para simulação (deve ser agnóstico)
- ❌ Modificar adapters para "modo simulação"
- ❌ Publicar tags que não estão gerenciados no Gateway

**FLUXO DE TAGS:**
```
Campo (OPC-UA/Modbus/MQTT)
    │
    ▼
Gateway DESCOBRE tags via protocolo
    │
    ▼
Tags são GERENCIADOS no Gateway (tags_config.json para enriquecimento)
    │
    ▼
Apenas tags GERENCIADOS vão para Kafka → Backend → Frontend
```

### 2.3 Backend (Processamento)

**O QUE É:**
- API REST e WebSocket para o Frontend
- Consumidor Kafka que persiste em InfluxDB

**O QUE DEVE FAZER:**
- ✅ Consumir dados do Kafka
- ✅ Persistir em InfluxDB (time series) e PostgreSQL (configurações)
- ✅ Processar alarmes e eventos
- ✅ Expor APIs para o Frontend
- ✅ Executar modelos ML

### 2.4 Frontend (Visualização)

**O QUE É:**
- Interface do usuário (React + TypeScript)

**O QUE DEVE FAZER:**
- ✅ Consumir APIs do Backend
- ✅ Receber dados real-time via WebSocket
- ✅ Visualizar dashboards, trends, alarmes

---

## 3. Protocolos e Portas

| Protocolo     | Porta Simulador | Porta Produção | Equipamento Típico          |
|---------------|-----------------|----------------|-----------------------------|
| OPC-UA        | 4841 (Node-RED) | 4840           | PLCs Siemens, Rockwell      |
| Modbus TCP    | 5020 (Node-RED) | 502            | Medidores, Inversores       |
| MQTT          | 1883            | 1883           | Sensores IoT, Gateways LoRa |
| EtherNet/IP   | 44818           | 44818          | PLCs Allen-Bradley          |
| S7 (Siemens)  | 102             | 102            | PLCs Siemens S7-300/400     |

**Nota sobre portas do simulador:**
- Usamos portas diferentes (4841, 5020) para não conflitar com simuladores standalone
- Em produção, o Gateway conecta nas portas padrão dos equipamentos reais

---

## 4. Configuração dos Adapters

Os adapters no Gateway são configurados em `gateway/config/adapters_config.json`.

**REGRA DE OURO:** Os adapters NÃO devem ser modificados para acomodar o simulador.
O simulador (Node-RED) deve se comportar como o equipamento real.

### Exemplo: Adapter OPC-UA para Gates

```json
{
  "adapter_id": "opcua-gates",
  "adapter_name": "OPC-UA Gates Control",
  "protocol_type": "opcua",
  "enabled": true,
  "host": "nodered",           // Em produção: IP do PLC real
  "port": 4840,                // Porta padrão OPC-UA
  "scan_rate_ms": 1000,
  "extra_config": {
    "security_mode": "None",
    "security_policy": "None",
    "subscription_interval": 100
  },
  "tags": [
    {"name": "ARZ_GATE01_Opening", "address": "ns=2;s=GrainTerminal.ARZ_GATE01.Opening", "type": "double"},
    {"name": "ARZ_GATE01_Setpoint", "address": "ns=2;s=GrainTerminal.ARZ_GATE01.Setpoint", "type": "double"}
  ]
}
```

### Exemplo: Adapter Modbus TCP para Medidores

```json
{
  "adapter_id": "modbus-energy-meters",
  "adapter_name": "Medidores de Energia",
  "protocol_type": "modbus",
  "enabled": true,
  "host": "nodered",           // Em produção: IP do medidor real
  "port": 502,                 // Porta padrão Modbus
  "scan_rate_ms": 1000,
  "extra_config": {
    "unit_id": 1,
    "byte_order": "big"
  },
  "tags": [
    {"name": "PM_GERAL_VoltageL1", "address": "40001", "type": "uint16", "scale": 0.1},
    {"name": "PM_GERAL_CurrentL1", "address": "40004", "type": "uint16", "scale": 0.01}
  ]
}
```

---

## 5. Node-RED - Estrutura dos Flows

O Node-RED deve ter a seguinte estrutura de flows:

```
📁 Node-RED Flows
├── 📄 Grain Terminal Simulator     # Lógica de simulação física
│   ├── Inject (1s) → Função Física → State Global
│   └── Dashboard UI
│
├── 📄 Protocol Servers             # Servidores de protocolo
│   ├── OPC-UA Server (porta 4840)
│   │   └── Address Space com variáveis do simulador
│   │
│   ├── Modbus TCP Server (porta 502)
│   │   └── Holding Registers mapeados
│   │
│   └── MQTT Publisher
│       └── Publica em tópicos por área
│
└── 📄 Command API                  # API para comandos (start/stop/fault)
    └── HTTP endpoints para controle
```

---

## 6. Substituição por Equipamento Real

Quando um equipamento real for instalado, a única mudança necessária é:

1. **Atualizar `adapters_config.json`:**
   - Mudar `host` de "nodered" para o IP do equipamento real
   - Ajustar `port` se necessário
   - Verificar `tags` (addresses podem mudar)

2. **Nenhuma mudança em:**
   - Gateway (código)
   - Backend
   - Frontend
   - Node-RED (pode continuar simulando outros equipamentos)

---

## 7. Checklist Antes de Implementar

Antes de iniciar qualquer implementação, verifique:

- [ ] O fluxo de dados segue: **Campo → Gateway → Backend → Frontend**?
- [ ] O Node-RED está atuando como SERVIDOR de protocolo (não cliente)?
- [ ] O Gateway está atuando como CLIENTE de protocolo?
- [ ] Os adapters estão configurados de forma agnóstica (funcionam igual para simulador e equipamento real)?
- [ ] Não há comunicação HTTP direta entre Node-RED e Gateway/Backend?
- [ ] O simulador se comporta exatamente como o equipamento real se comportaria?

---

## 8. Adapters Existentes no Gateway

Os adapters já estão configurados em `gateway/config/adapters_config.json`.

### Para SIMULAÇÃO (Node-RED como servidor):

| Adapter ID              | Protocolo | Host (Simulação) | Porta |
|-------------------------|-----------|------------------|-------|
| `siemens-s7-line1`      | OPC-UA    | `nodered`        | 4840  |
| `modbus-energy-meters`  | Modbus    | `nodered`        | 502   |
| `mqtt-iot-sensors`      | MQTT      | `rabbitmq`       | 1883  |

### Para PRODUÇÃO (Equipamento Real):

| Adapter ID              | Protocolo | Host (Produção)  | Porta |
|-------------------------|-----------|------------------|-------|
| `siemens-s7-line1`      | OPC-UA    | `192.168.1.10`   | 4840  |
| `modbus-energy-meters`  | Modbus    | `192.168.1.30`   | 502   |
| `mqtt-iot-sensors`      | MQTT      | `broker.local`   | 1883  |

### O que NÃO usar:

| Componente              | Motivo                                           |
|-------------------------|--------------------------------------------------|
| `opcua-simulator/`      | Simulador standalone - usar Node-RED             |
| `simulator/`            | Simulador Modbus standalone - usar Node-RED      |
| HTTP POST para ingestão | Viola arquitetura de protocolos industriais      |
| Virtual Adapters        | Workaround - usar adapters reais com host=nodered|
| `opcua-simulator-dev`   | Aponta para simulador standalone                 |

---

## 9. Node-RED - Servidores de Protocolo

O Node-RED deve expor os seguintes servidores:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     NODE-RED (Simulador de Campo)                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │  OPC-UA Server  │  │ Modbus TCP Srv  │  │  MQTT Publisher │     │
│  │   Porta 4840    │  │   Porta 502     │  │   Via RabbitMQ  │     │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤     │
│  │ • Gates (ARZ)   │  │ • PM_GERAL      │  │ • Sensores IoT  │     │
│  │ • Correias      │  │ • PM_CCM01      │  │ • Vibração      │     │
│  │ • Elevador      │  │ • PM_ILUM       │  │ • Temperatura   │     │
│  │ • Shiploader    │  │ • Inversores    │  │ • Qualidade Ar  │     │
│  │ • Transformador │  │                 │  │                 │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              SIMULADOR FÍSICO (Estado Global)                │   │
│  │   Calcula física realista: fluxo, temperatura, energia...   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 10. Diagrama de Rede

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              REDE OT (Automação)                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   Node-RED   │    │   PLC Real   │    │   Medidor    │                  │
│  │  (Simulador) │    │   (Futuro)   │    │    Real      │                  │
│  │              │    │              │    │   (Futuro)   │                  │
│  │ OPC-UA:4840  │    │ OPC-UA:4840  │    │ Modbus:502   │                  │
│  │ Modbus:502   │    │              │    │              │                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                   │                          │
│         └───────────────────┴───────────────────┘                          │
│                             │                                               │
│                    ┌────────┴────────┐                                      │
│                    │     GATEWAY     │ ◄── Diodo de Dados                  │
│                    │  (OPC-UA Client)│                                      │
│                    │ (Modbus Client) │                                      │
│                    └────────┬────────┘                                      │
└─────────────────────────────┼───────────────────────────────────────────────┘
                              │ Kafka
┌─────────────────────────────┼───────────────────────────────────────────────┐
│                              │ REDE IT (Corporativa)                        │
│                    ┌─────────┴─────────┐                                    │
│                    │      BACKEND      │                                    │
│                    │    (Kafka Consumer)│                                   │
│                    │    (REST API)     │                                    │
│                    └─────────┬─────────┘                                    │
│                              │                                              │
│                    ┌─────────┴─────────┐                                    │
│                    │     FRONTEND      │                                    │
│                    │      (React)      │                                    │
│                    └───────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Histórico de Decisões

| Data       | Decisão                                                    | Motivo                              |
|------------|------------------------------------------------------------|-------------------------------------|
| 2025-12-04 | Node-RED como único simulador                              | Consistência arquitetural           |
| 2025-12-04 | Eliminar HTTP POST entre Node-RED e Gateway               | Seguir padrão de protocolos reais   |
| 2025-12-04 | Gateway agnóstico (funciona igual para simulador e real)  | Facilitar transição para produção   |
| 2025-12-04 | Gateway como única fonte de verdade para tags             | Centralização e controle de dados   |
| 2025-12-04 | Apenas tags gerenciados vão para Kafka                    | Evitar poluição de dados            |

---

**Mantenedor:** Equipe OptiFlow
**Revisão:** Obrigatória antes de qualquer PR que modifique arquitetura
