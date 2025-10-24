# OptiFlow AI + KEPServerEX - Guia de Integração Rápida

**Objetivo**: Conectar OptiFlow AI ao KEPServerEX e descobrir tags automaticamente

**Tempo estimado**: 10-15 minutos

---

## 📋 Pré-requisitos

### 1. KEPServerEX Instalado
- ✅ KEPServerEX 6.x instalado e rodando
- ✅ Porta OPC UA configurada (padrão: 49320)
- ✅ Servidor OPC UA habilitado

### 2. OptiFlow AI Rodando
```bash
# Backend
cd backend
python -m uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev
```

### 3. Tags Configurados no KEPServer
- Pelo menos 1 canal configurado
- Pelo menos 1 device configurado
- Alguns tags criados para teste

---

## 🚀 Passo a Passo

### Passo 1: Verificar KEPServerEX está rodando

**Abra o KEPServerEX Configuration**:
- Verifique se o servidor está "Connected"
- Anote a porta OPC UA (Administration → Server Settings → OPC UA)
- Porta padrão: **49320**

**URL do servidor será**: `opc.tcp://localhost:49320`

---

### Passo 2: Testar Conexão via API

**Método 1: Swagger UI (Recomendado)**

1. Abra http://localhost:8000/docs
2. Faça login (se necessário)
3. Expanda `POST /api/v1/plc/connection/test`
4. Clique em "Try it out"
5. Cole no body:
```json
{
  "url": "opc.tcp://localhost:49320"
}
```
6. Clique em "Execute"

**Resposta esperada**:
```json
{
  "success": true,
  "url": "opc.tcp://localhost:49320",
  "server_info": {
    "application_uri": "urn:localhost:Kepware.KEPServerEX.V6",
    "product_uri": "urn:Kepware.KEPServerEX",
    "server_name": "KEPServerEX",
    "namespaces": [
      "http://opcfoundation.org/UA/",
      "urn:localhost:Kepware.KEPServerEX.V6"
    ]
  }
}
```

**Método 2: cURL**
```bash
curl -X POST "http://localhost:8000/api/v1/plc/connection/test" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "url": "opc.tcp://localhost:49320"
  }'
```

**Método 3: Python**
```python
import requests

url = "http://localhost:8000/api/v1/plc/connection/test"
headers = {"Authorization": "Bearer YOUR_TOKEN"}
data = {"url": "opc.tcp://localhost:49320"}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

---

### Passo 3: Descobrir Todos os Tags Automaticamente

**Via Swagger UI**:

1. Expanda `POST /api/v1/plc/discover`
2. Clique em "Try it out"
3. Cole no body:
```json
{
  "url": "opc.tcp://localhost:49320",
  "node_id": "i=85",
  "max_depth": 10,
  "include_properties": false
}
```
4. Clique em "Execute"
5. **Aguarde** (pode levar 5-30 segundos dependendo do número de tags)

**Resposta esperada**:
```json
{
  "success": true,
  "url": "opc.tcp://localhost:49320",
  "tags_found": 47,
  "tags": [
    {
      "name": "Temperature",
      "path": "Channel1/Device1/Temperature",
      "node_id": "ns=2;s=Channel1.Device1.Temperature",
      "data_type": "Float",
      "value_type": "float",
      "description": "Temperature sensor",
      "current_value": 25.5,
      "writable": true
    },
    {
      "name": "Pressure",
      "path": "Channel1/Device1/Pressure",
      "node_id": "ns=2;s=Channel1.Device1.Pressure",
      "data_type": "Float",
      "value_type": "float",
      "description": "Pressure sensor",
      "current_value": 101.3,
      "writable": true
    },
    // ... mais 45 tags
  ]
}
```

**Via cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/plc/discover" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "url": "opc.tcp://localhost:49320",
    "node_id": "i=85",
    "max_depth": 10
  }'
```

**Via Python**:
```python
import requests

url = "http://localhost:8000/api/v1/plc/discover"
headers = {"Authorization": "Bearer YOUR_TOKEN"}
data = {
    "url": "opc.tcp://localhost:49320",
    "node_id": "i=85",
    "max_depth": 10
}

response = requests.post(url, json=data, headers=headers)
result = response.json()

print(f"Tags encontrados: {result['tags_found']}")
for tag in result['tags']:
    print(f"  - {tag['path']}: {tag['data_type']}")
```

---

### Passo 4: Importar Tags para o OptiFlow

**Selecionar tags** que você quer monitorar e importar:

**Via Swagger UI**:

1. Expanda `POST /api/v1/plc/tags/import`
2. Clique em "Try it out"
3. Cole no body (exemplo com 3 tags):
```json
{
  "tags": [
    {
      "name": "Temperature",
      "node_id": "ns=2;s=Channel1.Device1.Temperature",
      "data_type": "Float",
      "description": "Temperature sensor",
      "unit": "°C",
      "min_value": 0,
      "max_value": 100
    },
    {
      "name": "Pressure",
      "node_id": "ns=2;s=Channel1.Device1.Pressure",
      "data_type": "Float",
      "description": "Pressure sensor",
      "unit": "kPa",
      "min_value": 0,
      "max_value": 200
    },
    {
      "name": "Motor_Speed",
      "node_id": "ns=2;s=Channel1.Device1.Motor_Speed",
      "data_type": "Int32",
      "description": "Motor RPM",
      "unit": "RPM",
      "min_value": 0,
      "max_value": 3000
    }
  ]
}
```
4. Clique em "Execute"

**Resposta esperada**:
```json
{
  "success": true,
  "imported_count": 3,
  "total_tags": 3,
  "errors": null
}
```

---

### Passo 5: Verificar Tags Importados

**Listar todos os tags**:

1. Expanda `GET /api/v1/plc/tags`
2. Clique em "Try it out"
3. Clique em "Execute"

**Resposta esperada**:
```json
{
  "tags": [
    {
      "name": "Temperature",
      "address": "ns=2;s=Channel1.Device1.Temperature",
      "data_type": "Float",
      "description": "Temperature sensor",
      "unit": "°C",
      "min_value": 0,
      "max_value": 100
    },
    {
      "name": "Pressure",
      "address": "ns=2;s=Channel1.Device1.Pressure",
      "data_type": "Float",
      "description": "Pressure sensor",
      "unit": "kPa",
      "min_value": 0,
      "max_value": 200
    },
    {
      "name": "Motor_Speed",
      "address": "ns=2;s=Channel1.Device1.Motor_Speed",
      "data_type": "Int32",
      "description": "Motor RPM",
      "unit": "RPM",
      "min_value": 0,
      "max_value": 3000
    }
  ]
}
```

---

### Passo 6: Conectar ao KEPServer para Monitoramento em Tempo Real

**IMPORTANTE**: Atualmente o código está usando **DemoPLCService**. Para conectar ao KEPServer real:

**Edite**: `backend/app/services/plc_service.py`

**Linha 413** (final do arquivo):
```python
# ANTES (Demo mode)
plc_service = DemoPLCService()

# DEPOIS (Production mode com KEPServer)
plc_service = PLCService()
```

**Reinicie o backend**:
```bash
# Pare o servidor (Ctrl+C)
# Inicie novamente
python -m uvicorn app.main:app --reload
```

**Configure a conexão via environment variable** (melhor prática):

1. Crie arquivo `backend/.env`:
```bash
# OPC UA Configuration
OPC_UA_URL=opc.tcp://localhost:49320
PLC_MODE=production
```

2. Modifique `plc_service.py` para ler do .env:
```python
import os

# No final do arquivo
if os.getenv("PLC_MODE") == "production":
    plc_service = PLCService()
    # Auto-connect
    import asyncio
    asyncio.create_task(
        plc_service.connect_opcua(os.getenv("OPC_UA_URL"))
    )
else:
    plc_service = DemoPLCService()
```

---

### Passo 7: Visualizar no Frontend

1. Abra http://localhost:5173
2. Faça login
3. Navegue até **SmartPort**
4. Clique na tab **"PLC Monitor"**

Você verá:
- **Real-time Viewer**: Todos os tags atualizando a cada 1 segundo
- **Historical Chart**: Gráfico de tendência
- **AI ChatBot**: Assistente para insights

---

## 🎯 Fluxo Completo Resumido

```
┌─────────────────────────────────────────────────────────────┐
│                    KEPServerEX                              │
│   Tags: Temperature, Pressure, Motor_Speed, etc.            │
└────────────────────┬────────────────────────────────────────┘
                     │ OPC UA (opc.tcp://localhost:49320)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              OptiFlow AI Backend                            │
│                                                              │
│  1. POST /plc/connection/test → Testa conexão               │
│  2. POST /plc/discover → Descobre todos os tags             │
│  3. POST /plc/tags/import → Importa tags selecionados       │
│  4. WebSocket /ws/plc → Stream em tempo real                │
│  5. InfluxDB → Armazena histórico                           │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/WebSocket
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              OptiFlow AI Frontend                           │
│                                                              │
│  SmartPort → PLC Monitor Tab:                               │
│    - Real-time PLC Viewer (1s updates)                      │
│    - Historical Trend Chart                                 │
│    - AI ChatBot                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Erro: "Failed to connect to OPC UA server"

**Causa**: KEPServerEX não está rodando ou porta incorreta

**Solução**:
1. Abra KEPServerEX Configuration
2. Verifique se servidor está "Connected"
3. Vá em Administration → Server Settings → OPC UA
4. Verifique a porta (padrão: 49320)
5. Certifique-se que OPC UA está habilitado

---

### Erro: "asyncua not installed"

**Causa**: Biblioteca asyncua não instalada

**Solução**:
```bash
cd backend
pip install asyncua
```

---

### Discovery retorna 0 tags

**Causa**: node_id incorreto ou sem permissão

**Solução**:
1. Tente com node_id diferentes:
   - `"i=85"` (Objects folder)
   - `"ns=2;s=Channel1"` (seu canal específico)
2. Aumente max_depth: `"max_depth": 15`
3. Verifique permissões no KEPServer

---

### Tags não aparecem no Frontend

**Causa**: plc_service ainda está em Demo mode

**Solução**:
1. Edite `backend/app/services/plc_service.py` linha 413
2. Troque `DemoPLCService()` por `PLCService()`
3. Adicione chamada de conexão
4. Reinicie backend

---

## 📝 Exemplo de Código Python Completo

```python
import requests
import json

# Configuração
BASE_URL = "http://localhost:8000"
TOKEN = "your_access_token_here"
KEPSERVER_URL = "opc.tcp://localhost:49320"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 1. Testar conexão
print("1. Testando conexão...")
response = requests.post(
    f"{BASE_URL}/api/v1/plc/connection/test",
    json={"url": KEPSERVER_URL},
    headers=headers
)
print(f"   Conexão: {'OK' if response.json()['success'] else 'FALHOU'}")
print(f"   Servidor: {response.json()['server_info']['server_name']}")

# 2. Descobrir tags
print("\n2. Descobrindo tags...")
response = requests.post(
    f"{BASE_URL}/api/v1/plc/discover",
    json={
        "url": KEPSERVER_URL,
        "node_id": "i=85",
        "max_depth": 10
    },
    headers=headers
)
result = response.json()
print(f"   Tags encontrados: {result['tags_found']}")

# 3. Selecionar e importar tags
print("\n3. Importando tags...")
tags_to_import = []
for tag in result['tags'][:5]:  # Importa primeiros 5 tags
    tags_to_import.append({
        "name": tag['name'],
        "node_id": tag['node_id'],
        "data_type": tag['data_type'],
        "description": tag['description'],
        "unit": ""
    })

response = requests.post(
    f"{BASE_URL}/api/v1/plc/tags/import",
    json={"tags": tags_to_import},
    headers=headers
)
print(f"   Importados: {response.json()['imported_count']}")

# 4. Listar tags importados
print("\n4. Listando tags importados...")
response = requests.get(
    f"{BASE_URL}/api/v1/plc/tags",
    headers=headers
)
for tag in response.json()['tags']:
    print(f"   - {tag['name']}: {tag['data_type']}")

print("\n✅ Integração completa!")
print("Acesse http://localhost:5173 → SmartPort → PLC Monitor")
```

---

## 🎉 Próximos Passos

Após a integração básica:

1. **Configurar Archives** - Políticas de retenção no InfluxDB
2. **Alarmes** - Configurar thresholds e notificações
3. **Dashboards Customizados** - Criar visualizações específicas
4. **Reports Automáticos** - Relatórios PDF agendados
5. **Machine Learning** - Previsões e detecção de anomalias

---

## 📞 Suporte

Problemas? Abra uma issue no GitHub ou consulte:
- Documentação OptiFlow: `/docs`
- Documentação KEPServerEX: https://www.kepware.com/support
- asyncua library: https://github.com/FreeOpcUa/opcua-asyncio

---

**Última atualização**: 2025-10-24
**Versão**: 1.0
