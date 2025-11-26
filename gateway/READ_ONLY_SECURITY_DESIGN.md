# OptiFlow Gateway - Read-Only Security Design 🔒

**Princípio Fundamental**: O OptiFlow Gateway é **READ-ONLY por design**

---

## 🛡️ Premissa de Segurança

### **Gateway NÃO Escreve em Tags**

O OptiFlow Gateway foi projetado com segurança em mente, seguindo o princípio de **menor privilégio**:

✅ **O QUE O GATEWAY FAZ**:
- Lê valores de tags OPC UA, Modbus, MQTT
- Processa e transforma dados (scaling, fórmulas)
- Envia dados para sistemas externos (Kafka, TimeSeries DB)
- Gera alarmes e notificações
- Executa ações de monitoramento

❌ **O QUE O GATEWAY NÃO FAZ**:
- **NÃO escreve valores em PLCs**
- **NÃO modifica setpoints**
- **NÃO controla equipamentos**
- **NÃO executa comandos nos dispositivos**

---

## 🎯 Razões para Read-Only

### 1. **Segurança Industrial (Safety)**
- Evita modificações acidentais em processos críticos
- Previne comandos não autorizados
- Elimina risco de interferência no controle
- Compatível com IEC 61508 (SIL)

### 2. **Conformidade ISA-99 / IEC 62443**
```
Enterprise (IT) ──[Firewall]──> DMZ (Gateway) ──[Firewall]──> OT (PLCs)
   Read/Write                    READ-ONLY ✅              Read/Write
```

**Zonas de Segurança**:
- **IT Zone**: Sistemas corporativos (SCADA, MES, ERP)
- **DMZ Zone**: Gateway (READ-ONLY)
- **OT Zone**: PLCs, sensores, atuadores

### 3. **Auditoria e Compliance**
- Todas as escritas rastreadas no sistema de controle
- Gateway não interfere na cadeia de comando
- Logs de auditoria simplificados
- Compliance com FDA 21 CFR Part 11

### 4. **Arquitetura de Controle**
```
┌─────────────────────────────────────────┐
│         SCADA / DCS (Controle)          │
│         ├─ Leitura de tags              │
│         └─ ESCRITA de setpoints ✓       │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│           PLCs / RTUs                   │
│         ├─ Controle local               │
│         ├─ Lógica de segurança          │
│         └─ I/O físico                   │
└─────────────────────────────────────────┘
                    ↕ (read-only)
┌─────────────────────────────────────────┐
│      OptiFlow Gateway (READ-ONLY) ✅    │
│         ├─ Coleta de dados              │
│         ├─ Processamento edge           │
│         ├─ Alarmes e notificações       │
│         └─ Histórico e analytics        │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│     Cloud Platform / Data Lake          │
│         ├─ Armazenamento                │
│         ├─ Analytics                    │
│         └─ Dashboards                   │
└─────────────────────────────────────────┘
```

---

## 🔐 Implementação de Segurança

### 1. **Código - BaseProtocolAdapter**

```python
class BaseProtocolAdapter:
    """Base adapter - READ-ONLY"""

    def read_tag(self, address: str):
        """✅ Permitido - Lê valor"""
        pass

    # ❌ Método write_tag() NÃO EXISTE
    # def write_tag(self, address: str, value: Any):
    #     """❌ REMOVIDO - Gateway é read-only"""
    #     raise NotImplementedError("Gateway is READ-ONLY by design")
```

### 2. **OPC UA Adapter - Somente Read Methods**

```python
class OPCUAAdapter:
    """OPC UA Adapter - READ-ONLY"""

    async def read_tag(self, node_id: str):
        """✅ Usa ua.Client.read_values()"""
        return await self.client.read_values([node_id])

    # ❌ Métodos de escrita NÃO implementados:
    # - write_value()
    # - call_method()
    # - write_attribute()
```

### 3. **Modbus Adapter - Read Functions Only**

```python
class ModbusAdapter:
    """Modbus Adapter - READ-ONLY"""

    def read_holding_registers(self, address: int, count: int):
        """✅ Function Code 0x03 - Read"""
        pass

    def read_input_registers(self, address: int, count: int):
        """✅ Function Code 0x04 - Read"""
        pass

    # ❌ Funções de escrita NÃO implementadas:
    # - write_single_coil() - Function 0x05
    # - write_single_register() - Function 0x06
    # - write_multiple_coils() - Function 0x0F
    # - write_multiple_registers() - Function 0x10
```

---

## 🚫 Ações Removidas

### **ActionType Enum - WRITE_TAG Removido**

**ANTES** (INSEGURO):
```python
class ActionType(str, Enum):
    WEBHOOK = "webhook"
    EMAIL = "email"
    WRITE_TAG = "write_tag"  # ❌ REMOVIDO
    EXECUTE_SCRIPT = "execute_script"
```

**DEPOIS** (SEGURO):
```python
class ActionType(str, Enum):
    """Types of actions (READ-ONLY Gateway)"""
    WEBHOOK = "webhook"
    EMAIL = "email"
    MQTT_PUBLISH = "mqtt_publish"
    EXECUTE_SCRIPT = "execute_script"  # Read-only context
    LOG_MESSAGE = "log_message"
    DASHBOARD_NOTIFICATION = "dashboard_notification"
    # NOTE: WRITE_TAG removed - Gateway is READ-ONLY by design
```

### **AutomatedAction Model - Campos de Escrita Removidos**

**ANTES**:
```python
class AutomatedAction:
    # Write tag action ❌
    target_tag_id: Optional[str] = None
    write_value_expression: Optional[str] = None
```

**DEPOIS**:
```python
class AutomatedAction:
    # Execute script action (READ-ONLY - no write access to tags)
    script_code: Optional[str] = None  # Read-only context
    script_timeout_seconds: float = 5.0
```

---

## ✅ Ações Permitidas (Read-Only)

### 1. **Notificações Externas**

#### **Webhook**
```json
{
  "action_type": "webhook",
  "webhook_url": "https://api.controle.com/notify",
  "webhook_method": "POST",
  "webhook_body_template": "{\"tag\": \"{tag_name}\", \"value\": {value}, \"alarm\": true}"
}
```
**Uso**: Notificar sistema de controle externo (que pode tomar ação)

#### **Email**
```json
{
  "action_type": "email",
  "email_to": ["operador@empresa.com"],
  "email_subject_template": "Alarme: {tag_name}",
  "email_body_template": "Temperatura {value}°C excede limite"
}
```
**Uso**: Alertar equipe para ação manual

#### **MQTT Publish**
```json
{
  "action_type": "mqtt_publish",
  "mqtt_topic": "plant/alarms/{tag_name}",
  "mqtt_payload_template": "{\"value\": {value}, \"quality\": \"{quality}\"}"
}
```
**Uso**: Publicar em sistema de mensageria para consumo por outros sistemas

### 2. **Scripts Read-Only**

```python
# ✅ PERMITIDO - Leitura de múltiplas tags
script_code = """
import requests
temp = tags['TEMP_01']
pressure = tags['PRESSURE_01']

if temp > 80 and pressure > 100:
    requests.post('https://scada.local/api/alerts',
                  json={'status': 'critical', 'temp': temp, 'pressure': pressure})
"""
```

```python
# ❌ BLOQUEADO - Tentativa de escrita
script_code = """
tags['VALVE_CLOSE'] = True  # ❌ Erro: tags é read-only
"""
```

---

## 🔥 Firewall Rules (Deep Packet Inspection)

### **OPC UA - Permitir Apenas Read Operations**

```bash
# ✅ ALLOW - Read operations
- ua.ReadRequest
- ua.BrowseRequest
- ua.SubscribeRequest
- ua.CreateMonitoredItemsRequest

# ❌ BLOCK - Write operations
- ua.WriteRequest
- ua.CallMethodRequest
- ua.HistoryUpdateRequest
```

### **Modbus TCP - Permitir Apenas Read Functions**

```bash
# ✅ ALLOW - Read function codes
0x01 - Read Coils
0x02 - Read Discrete Inputs
0x03 - Read Holding Registers
0x04 - Read Input Registers

# ❌ BLOCK - Write function codes
0x05 - Write Single Coil
0x06 - Write Single Register
0x0F - Write Multiple Coils
0x10 - Write Multiple Registers
```

---

## 📋 Audit Trail

### **Log de Operações**

```json
{
  "timestamp": "2025-11-25T10:30:00Z",
  "event": "tag_read",
  "operation": "READ",  // ✅ Sempre READ
  "tag_name": "TEMP_FORNO_01",
  "value": 125.4,
  "quality": "Good",
  "adapter_id": "opcua-001",
  "gateway_id": "gateway-01"
}
```

**Verificação de Compliance**:
```bash
# Verificar se há tentativas de escrita (deve retornar 0)
grep -c "operation.*WRITE" /var/log/gateway/audit.log
# Output: 0 ✅
```

---

## 🎯 Como Implementar Controle

### **Opção 1: SCADA/DCS Tradicional**

```
┌──────────────────────────────────────┐
│         SCADA System                 │
│  ├─ Supervisory Control              │
│  ├─ HMI (Operador)                   │
│  └─ Escrita de setpoints ✓           │
└──────────────────────────────────────┘
            ↕ (read/write)
┌──────────────────────────────────────┐
│         PLCs (Controle Local)        │
└──────────────────────────────────────┘
            ↕ (read-only)
┌──────────────────────────────────────┐
│    OptiFlow Gateway (Monitoring)     │
└──────────────────────────────────────┘
```

### **Opção 2: Webhook para Sistema de Controle**

```python
# Gateway detecta condição crítica
{
  "action_type": "webhook",
  "webhook_url": "https://scada.local/api/emergency-shutdown",
  "webhook_body_template": "{
    \"action\": \"emergency_shutdown\",
    \"reason\": \"Temperature {value}°C > 95°C\",
    \"tag\": \"{tag_name}\",
    \"timestamp\": \"{timestamp}\"
  }"
}
```

**Sistema de Controle (separado)** recebe webhook e **executa ação de controle**.

### **Opção 3: MQTT + Node-RED**

```
OptiFlow Gateway
    ↓ (publish alarm via MQTT)
MQTT Broker
    ↓ (subscribe)
Node-RED (Control Logic)
    ↓ (write to PLC)
PLC/SCADA
```

---

## ✅ Benefícios do Design Read-Only

### **Segurança**
- ✅ Zero risco de comandos acidentais
- ✅ Impossível interferir no controle
- ✅ Firewall pode bloquear 100% de escritas
- ✅ Audit trail simplificado

### **Compliance**
- ✅ ISA-99 / IEC 62443 compliant
- ✅ FDA 21 CFR Part 11 ready
- ✅ HIPAA compatible
- ✅ Separação clara de responsabilidades

### **Operacional**
- ✅ Monitoramento sem risco
- ✅ Analytics sem interferência
- ✅ Deploy simplificado
- ✅ Menor superfície de ataque

---

## 📚 Referências e Standards

### **ISA-99 / IEC 62443**
- **Zones and Conduits**: Gateway em DMZ (read-only)
- **Defense in Depth**: Múltiplas camadas de proteção
- **Least Privilege**: Apenas leitura necessária

### **NIST Cybersecurity Framework**
- **Identify**: Classificação de ativos
- **Protect**: Controles de acesso (read-only)
- **Detect**: Monitoramento de anomalias
- **Respond**: Notificações automáticas
- **Recover**: Logs de auditoria

### **OWASP Top 10 Industrial**
- **Injection Prevention**: Sem comandos de escrita
- **Access Control**: Operações limitadas a leitura
- **Security Misconfiguration**: Default read-only

---

## 🎓 Casos de Uso Read-Only

### **Caso 1: Monitoramento de Temperatura**
```
✅ Gateway lê temperatura
✅ Gateway detecta > 95°C
✅ Gateway envia webhook para SCADA
✅ SCADA executa shutdown (separadamente)
```

### **Caso 2: Dashboard de Produção**
```
✅ Gateway lê OEE, performance, qualidade
✅ Gateway calcula KPIs
✅ Gateway envia para cloud
✅ Dashboard exibe dados em tempo real
```

### **Caso 3: Manutenção Preditiva**
```
✅ Gateway lê vibração, temperatura, corrente
✅ Gateway detecta anomalia estatística
✅ Gateway envia email para manutenção
✅ Manutenção agenda intervenção
```

---

## 🚀 Conclusão

**OptiFlow Gateway = Monitoring & Analytics, NÃO Controle**

O OptiFlow Gateway foi projetado para:
- ✅ **Monitorar** processos com segurança
- ✅ **Analisar** dados em tempo real
- ✅ **Alertar** equipes sobre condições anormais
- ✅ **Integrar** dados OT → IT

**NÃO** foi projetado para:
- ❌ Controlar equipamentos
- ❌ Modificar setpoints
- ❌ Executar comandos em PLCs
- ❌ Substituir SCADA/DCS

---

**🔒 Segurança em Primeiro Lugar - Read-Only by Design**

*OptiFlow Gateway: Monitor com Confiança, Controle com Sistemas Dedicados*
