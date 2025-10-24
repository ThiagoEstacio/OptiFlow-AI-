# OptiFlow Gateway - Auto-Discovery Implementation Plan

**Date**: 2025-10-24
**Objective**: Implementar auto-discovery de devices/nodes no Gateway, similar ao KEPServerEX

---

## 🎯 Problema Identificado

O usuário está correto: **nosso Gateway precisa descobrir devices automaticamente**, assim como o KEPServerEX faz.

**Situação Atual**:
- ❌ Gateway vazio (apenas estrutura básica)
- ❌ Sem discovery de devices
- ❌ Configuração 100% manual necessária
- ❌ Sem scan de redes industriais

**Situação Desejada** (como KEPServerEX):
- ✅ Scan automático de rede para devices Modbus
- ✅ Discovery de servidores OPC UA na rede
- ✅ Detecção automática de ranges de endereços
- ✅ Identificação de tipos de devices
- ✅ Leitura automática de estrutura de dados
- ✅ Configuração zero-touch

---

## 📊 Funcionalidades do KEPServerEX que Precisamos Replicar

### 1. **Network Scanning**
KEPServerEX faz:
- Scan de range IP (ex: 192.168.1.1-254)
- Tenta conectar em portas conhecidas (502 Modbus, 4840 OPC UA)
- Identifica devices respondendo

### 2. **Modbus Device Discovery**
KEPServerEX faz:
- Scan de Unit IDs (1-247)
- Tenta ler registradores padrão
- Identifica vendor/model se possível
- Mapeia estrutura de memória

### 3. **OPC UA Server Discovery**
KEPServerEX faz:
- Multicast discovery (LDS - Local Discovery Server)
- Browse de endpoints
- Browse de estrutura completa de tags
- Detecção de namespaces

### 4. **Tag Structure Discovery**
KEPServerEX faz:
- Leitura de blocos de memória
- Detecção de tipos de dados
- Criação automática de tags
- Agrupamento lógico

### 5. **Auto-Configuration**
KEPServerEX faz:
- Salva configuração descoberta
- Permite edição posterior
- Export/Import de config
- Templates de devices conhecidos

---

## 🏗️ Arquitetura Proposta para OptiFlow Gateway

```
OptiFlow Gateway
├── Discovery Engine
│   ├── Network Scanner
│   │   ├── IP Range Scanner
│   │   ├── Port Scanner
│   │   └── Protocol Detector
│   │
│   ├── Modbus Discovery
│   │   ├── Unit ID Scanner (1-247)
│   │   ├── Register Mapper
│   │   └── Vendor Detection
│   │
│   ├── OPC UA Discovery
│   │   ├── LDS Client
│   │   ├── Server Browser
│   │   └── Tag Tree Walker
│   │
│   └── S7 Discovery (Siemens)
│       ├── TSAP Scanner
│       ├── Block Lister
│       └── Symbol Table Reader
│
├── Configuration Manager
│   ├── Device Registry
│   ├── Tag Mapper
│   ├── Config Validator
│   └── Config Exporter
│
├── Data Collector
│   ├── Protocol Clients
│   ├── Polling Engine
│   ├── Buffer Manager
│   └── Backend Uploader
│
└── API Server
    ├── Discovery Endpoints
    ├── Configuration Endpoints
    ├── Status Endpoints
    └── WebSocket Streaming
```

---

## 🚀 Implementação por Fases

### **Fase 1: Network Scanner** (1-2 horas)

**Objetivo**: Descobrir devices na rede

**Implementar**:
```python
# gateway/app/services/network_scanner.py

class NetworkScanner:
    async def scan_ip_range(self, start_ip, end_ip, ports):
        """Scan IP range for devices"""

    async def scan_port(self, ip, port):
        """Check if port is open"""

    async def identify_protocol(self, ip, port):
        """Identify which protocol (Modbus, OPC UA, S7)"""
```

**Endpoints**:
- `POST /api/discovery/network/scan`
- Body: `{"start_ip": "192.168.1.1", "end_ip": "192.168.1.254", "ports": [502, 4840]}`

---

### **Fase 2: Modbus Discovery** (2-3 horas)

**Objetivo**: Descobrir devices Modbus e seus registradores

**Implementar**:
```python
# gateway/app/services/modbus_discovery.py

class ModbusDiscovery:
    async def scan_unit_ids(self, ip, port, unit_id_range):
        """Scan for active Modbus unit IDs"""
        # Tenta ler holding register 0 para cada unit ID

    async def map_registers(self, ip, port, unit_id):
        """Map available registers for a unit"""
        # Tenta ler blocos de holding/input registers
        # Identifica ranges válidos

    async def detect_vendor(self, ip, port, unit_id):
        """Try to detect device vendor/model"""
        # Lê registradores padrão de identificação
```

**Endpoints**:
- `POST /api/discovery/modbus/scan`
- `POST /api/discovery/modbus/map-registers`

---

### **Fase 3: OPC UA Discovery** (2-3 horas)

**Objetivo**: Descobrir servidores OPC UA e seus tags

**Implementar**:
```python
# gateway/app/services/opcua_discovery.py

class OPCUADiscovery:
    async def discover_servers(self, network_range):
        """Use LDS to find OPC UA servers"""

    async def browse_server(self, url):
        """Browse complete tag tree"""
        # Reutilizar código do plc_service.browse_opcua()

    async def get_server_info(self, url):
        """Get server metadata"""
```

**Endpoints**:
- `POST /api/discovery/opcua/find-servers`
- `POST /api/discovery/opcua/browse`

---

### **Fase 4: Auto-Configuration** (2-3 horas)

**Objetivo**: Criar configuração automaticamente

**Implementar**:
```python
# gateway/app/services/config_manager.py

class ConfigManager:
    async def create_device_config(self, discovery_result):
        """Create device configuration from discovery"""

    async def create_tag_config(self, device_id, tags):
        """Create tag configurations"""

    async def save_config(self, config):
        """Save to file/database"""

    async def sync_to_backend(self, config):
        """Upload config to OptiFlow backend"""
```

**Endpoints**:
- `POST /api/config/create-from-discovery`
- `GET /api/config/export`
- `POST /api/config/sync-backend`

---

### **Fase 5: Integration with Backend** (1-2 horas)

**Objetivo**: Sincronizar descobertas com backend OptiFlow

**Fluxo**:
```
Gateway Discovery
    ↓
Cria Devices no Gateway
    ↓
Envia para Backend via API
    ↓
Backend cria:
  - Device record
  - Tag records
  - Associates with Organization/Site
    ↓
Gateway inicia coleta de dados
```

---

## 📋 API Completa do Gateway

### **Discovery APIs**

```yaml
# Network Scanning
POST /api/discovery/network/scan
POST /api/discovery/network/scan-ports

# Modbus Discovery
POST /api/discovery/modbus/scan-units
POST /api/discovery/modbus/map-registers
POST /api/discovery/modbus/detect-vendor

# OPC UA Discovery
POST /api/discovery/opcua/find-servers
POST /api/discovery/opcua/browse-server
POST /api/discovery/opcua/get-endpoints

# S7 Discovery (future)
POST /api/discovery/s7/scan-racks
POST /api/discovery/s7/read-symbols

# Auto Configuration
POST /api/config/create-from-discovery
POST /api/config/validate
POST /api/config/apply
GET /api/config/export
POST /api/config/import
```

### **Data Collection APIs**

```yaml
# Device Management
GET /api/devices
POST /api/devices
PUT /api/devices/{id}
DELETE /api/devices/{id}

# Tag Management
GET /api/tags
POST /api/tags
PUT /api/tags/{id}

# Status & Health
GET /api/health
GET /api/status
GET /api/metrics
```

---

## 🎯 Exemplo de Uso Completo

### **Cenário: Descobrir PLCs Modbus numa fábrica**

**1. Scan da Rede**:
```bash
POST /api/discovery/network/scan
{
  "start_ip": "192.168.1.1",
  "end_ip": "192.168.1.254",
  "ports": [502]
}

# Resposta:
{
  "devices_found": 3,
  "devices": [
    {"ip": "192.168.1.10", "port": 502, "protocol": "modbus"},
    {"ip": "192.168.1.20", "port": 502, "protocol": "modbus"},
    {"ip": "192.168.1.30", "port": 502, "protocol": "modbus"}
  ]
}
```

**2. Descobrir Unit IDs de cada device**:
```bash
POST /api/discovery/modbus/scan-units
{
  "ip": "192.168.1.10",
  "port": 502,
  "unit_id_range": [1, 10]
}

# Resposta:
{
  "active_units": [1, 2],
  "units": [
    {"unit_id": 1, "responsive": true},
    {"unit_id": 2, "responsive": true}
  ]
}
```

**3. Mapear Registradores**:
```bash
POST /api/discovery/modbus/map-registers
{
  "ip": "192.168.1.10",
  "port": 502,
  "unit_id": 1
}

# Resposta:
{
  "holding_registers": {
    "0-99": "readable",
    "100-199": "readable",
    "1000-1050": "readable"
  },
  "input_registers": {
    "0-49": "readable"
  },
  "suggested_tags": [
    {"name": "HR_0", "address": "holding:0", "type": "Int16"},
    {"name": "HR_1", "address": "holding:1", "type": "Int16"},
    // ...
  ]
}
```

**4. Criar Configuração Automaticamente**:
```bash
POST /api/config/create-from-discovery
{
  "device": {
    "ip": "192.168.1.10",
    "port": 502,
    "unit_id": 1,
    "protocol": "modbus"
  },
  "tags": [
    {"name": "Temperature", "address": "holding:0", "type": "Int16", "unit": "°C"},
    {"name": "Pressure", "address": "holding:1", "type": "Int16", "unit": "kPa"},
    {"name": "Motor_RPM", "address": "holding:10", "type": "Int16", "unit": "RPM"}
  ]
}

# Resposta:
{
  "device_id": "abc-123",
  "tags_created": 3,
  "config_saved": true,
  "ready_to_collect": true
}
```

**5. Sincronizar com Backend**:
```bash
POST /api/config/sync-backend
{
  "device_id": "abc-123"
}

# Gateway cria no Backend:
# - Device record (IP, porta, protocolo)
# - 3 Tag records
# - Associação com Site/Organization
```

**6. Iniciar Coleta Automática**:
- Gateway automaticamente inicia polling
- Dados enviados para InfluxDB
- Visível no frontend em tempo real

---

## 📊 Comparação: KEPServerEX vs OptiFlow Gateway

| Feature | KEPServerEX | OptiFlow Gateway (Proposto) |
|---------|-------------|------------------------------|
| Network Scan | ✅ | ✅ Implementar |
| Modbus Discovery | ✅ | ✅ Implementar |
| OPC UA Discovery | ✅ | ✅ Usar código já feito |
| S7 Discovery | ✅ | 🔜 Fase futura |
| Auto Config | ✅ | ✅ Implementar |
| Backend Sync | ❌ | ✅ Vantagem nossa! |
| Zero Config | ✅ | ✅ Implementar |
| Web UI | ✅ | ✅ Já temos no OptiFlow |

---

## ⏱️ Estimativa de Tempo

| Fase | Tempo Estimado | Prioridade |
|------|----------------|------------|
| Fase 1: Network Scanner | 1-2 horas | 🔴 Alta |
| Fase 2: Modbus Discovery | 2-3 horas | 🔴 Alta |
| Fase 3: OPC UA Discovery | 1-2 horas | 🟡 Média (já temos parte) |
| Fase 4: Auto Configuration | 2-3 horas | 🔴 Alta |
| Fase 5: Backend Integration | 1-2 horas | 🟡 Média |
| **TOTAL** | **7-12 horas** | |

---

## 🚀 Posso Implementar Agora?

Posso começar a implementar:

**Opção 1: Implementação Completa (8-10 horas)**
- Todas as 5 fases
- Gateway totalmente funcional
- Discovery automático completo

**Opção 2: MVP Rápido (3-4 horas)**
- Fase 1: Network Scanner
- Fase 2: Modbus Discovery básico
- Fase 4: Auto Config mínimo
- **Resultado**: Já consegue descobrir devices Modbus automaticamente

**Opção 3: Documentação + Roadmap Detalhado (1 hora)**
- Criar especificação técnica completa
- Diagramas de sequência
- Exemplos de código
- Você ou equipe implementa depois

---

## 💡 Recomendação

**Recomendo Opção 2 (MVP Rápido)** porque:
- ✅ Você já tem KEPServerEX funcionando (pode usar enquanto isso)
- ✅ 3-4 horas para ter discovery básico funcionando
- ✅ Modbus é o protocolo mais comum em indústria
- ✅ Valida a arquitetura antes de investir mais tempo
- ✅ Depois expande para OPC UA (reutiliza código já feito)

---

**Qual opção prefere?** 🎯

1. ✅ Implementação Completa agora (8-10h)
2. ✅ MVP Rápido agora (3-4h)
3. ✅ Documentação detalhada + você implementa depois

---

**Última atualização**: 2025-10-24
