# 🔌 Guia de Conexão WebSocket - Real-time Monitoring

**Status**: ⚠️ **FRONTEND USANDO ENDPOINT INCORRETO**

---

## 🎯 Problema

O frontend está tentando conectar ao WebSocket no endpoint **genérico**:
```
ws://localhost:8000/ws
```

Mas o endpoint correto para streaming do simulador é:
```
ws://localhost:8000/api/v1/ws/simulator/stream
```

---

## ✅ Solução: Atualizar Frontend

### Opção 1: Atualizar useRealtimeData Hook (Recomendado)

**Arquivo**: `frontend/src/hooks/useRealtimeData.ts`

**Linha 74** - Alterar URL padrão:

```typescript
// ❌ ANTES (errado)
const { autoConnect = true, url = 'ws://localhost:8000/ws' } = options;

// ✅ DEPOIS (correto)
const { autoConnect = true, url = 'ws://localhost:8000/api/v1/ws/simulator/stream' } = options;
```

### Opção 2: Passar URL Correta no Component

**Arquivo**: `frontend/src/pages/ProfessionalRealtime.tsx`

**Linha 59** - Adicionar URL ao hook:

```typescript
// ❌ ANTES
const { data: simulatorData } = useRealtimeData<SimulatorUpdate>('simulator_update');

// ✅ DEPOIS
const { data: simulatorData } = useRealtimeData<SimulatorUpdate>('simulator_update', {
  url: 'ws://localhost:8000/api/v1/ws/simulator/stream'
});
```

---

## 📡 Endpoints WebSocket Disponíveis

| Endpoint | Propósito | Mensagem |
|----------|-----------|----------|
| `/api/v1/ws/simulator/stream` | ✅ Stream do simulador em tempo real | `simulator_update` |
| `/api/v1/ws/tags` | Stream de tags individuais | `tag_update` |
| `/api/v1/ws/analytics` | Stream de analytics | `analytics_update` |
| `/api/v1/websocket-monitor/ws` | Monitor de conexões | `monitor_update` |

---

## 🔍 Como o WebSocket Funciona

### 1. Conexão

```typescript
// Frontend conecta em:
ws://localhost:8000/api/v1/ws/simulator/stream

// Backend aceita conexão:
await websocket.accept()
```

### 2. Streaming Automático

O backend inicia automaticamente o streaming quando o **primeiro cliente** conecta:

```python
# backend/app/api/v1/endpoints/websocket_simulator.py

async def connect(self, websocket: WebSocket):
    await websocket.accept()
    self.active_connections.add(websocket)

    # Inicia streaming se não estiver rodando
    if not self.is_streaming:
        await self.start_streaming()  # ✅ Automático!
```

### 3. Mensagens a Cada 1 Segundo

```python
async def _stream_loop(self):
    while self.is_streaming:
        # Busca dados do simulador
        all_tags = sim.get_all_tags()
        status = sim.get_status()

        # Envia para todos os clientes
        message = {
            "type": "simulator_update",
            "timestamp": "2025-11-14T21:50:00Z",
            "tags": {
                "SYSTEM.running": 1.0,
                "CORR01_POWER_KW_PV": 34.7,
                ...
            },
            "status": {
                "system": {"running": true, ...},
                "belts": [...],
                "gates": [...]
            }
        }

        await self.broadcast(json.dumps(message))
        await asyncio.sleep(1.0)  # 1 Hz
```

### 4. Frontend Recebe Dados

```typescript
// useRealtimeData hook recebe automaticamente
const { data: simulatorData, isConnected } = useRealtimeData<SimulatorUpdate>('simulator_update');

// simulatorData agora contém:
{
  type: "simulator_update",
  timestamp: "2025-11-14T21:50:00Z",
  tags: {
    "CORR01_POWER_KW_PV": 34.7,
    "CORR01_TEMP_C_PV": 56.4,
    ...
  },
  status: {
    system: {
      running: true,
      time_s: 145.0,
      ...
    }
  }
}

// isConnected ✅ true (mostra "Live" no frontend)
```

---

## 🧪 Teste de Conexão

### 1. Via curl (HTTP - apenas para teste)

```bash
# Verificar se endpoint existe
curl -I http://localhost:8000/api/v1/ws/simulator/stream

# Resposta esperada: 426 Upgrade Required (correto para WebSocket)
```

### 2. Via wscat (WebSocket direto)

```bash
# Instalar wscat
npm install -g wscat

# Conectar ao WebSocket
wscat -c ws://localhost:8000/api/v1/ws/simulator/stream

# Você deve receber mensagens a cada 1 segundo:
< {"type":"simulator_update","timestamp":"2025-11-14T21:50:00Z","tags":{...}}
< {"type":"simulator_update","timestamp":"2025-11-14T21:50:01Z","tags":{...}}
```

### 3. Via Browser DevTools

```javascript
// Abra o console do navegador em http://localhost:3000
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/simulator/stream');

ws.onopen = () => console.log('✅ Connected!');
ws.onmessage = (event) => console.log('📥 Data:', JSON.parse(event.data));
ws.onerror = (error) => console.error('❌ Error:', error);
ws.onclose = () => console.log('⏹️ Disconnected');

// Deve imprimir dados a cada 1 segundo
```

---

## 🛠️ Implementação Correta no Frontend

### Atualização Completa do Hook

```typescript
// frontend/src/hooks/useRealtimeData.ts

export function useRealtimeData<T = any>(
  messageType: string,
  options: UseRealtimeDataOptions = {}
): RealtimeData<T> & {
  send: (data: any) => void;
  connect: () => void;
  disconnect: () => void;
} {
  // ✅ URL CORRETA DO SIMULADOR
  const {
    autoConnect = true,
    url = 'ws://localhost:8000/api/v1/ws/simulator/stream'  // MUDANÇA AQUI!
  } = options;

  // ... resto do código permanece igual
}
```

### Uso no Componente

```typescript
// frontend/src/pages/ProfessionalRealtime.tsx

export const ProfessionalRealtime: React.FC = () => {
  // WebSocket connection status
  const isConnected = useWebSocketStatus();  // ✅ Agora retorna TRUE

  // Real-time simulator updates from WebSocket
  const { data: simulatorData } = useRealtimeData<SimulatorUpdate>('simulator_update');

  // ✅ isConnected agora será TRUE quando conectar corretamente
  // ✅ simulatorData receberá atualizações a cada 1 segundo

  return (
    <Chip
      label={isConnected ? 'Live' : 'Disconnected'}  // ✅ Mostrará "Live"
      sx={{
        bgcolor: isConnected ? 'rgba(76, 175, 80, 0.2)' : 'rgba(255, 255, 255, 0.2)',
        color: 'white'
      }}
    />
  );
};
```

---

## 📊 Formato das Mensagens WebSocket

### Mensagem Completa do Simulador

```json
{
  "type": "simulator_update",
  "timestamp": "2025-11-14T21:50:15.284823Z",
  "tags": {
    "SYSTEM.running": 1.0,
    "SYSTEM.time_s": 145.0,
    "SYSTEM.total_mass_t": 5.8,
    "SYSTEM.total_kWh": 8.2,
    "SYSTEM.warehouse_level_pct": 68.5,
    "CORR01_POWER_KW_PV": 34.7,
    "CORR01_SPEED_MPS_PV": 1.59,
    "CORR01_TEMP_C_PV": 56.4,
    "CORR01_FLOW_TPH_PV": 115.4,
    "GATE_03_OPENING_PCT_PV": 45.0,
    "GATE_03_FLOW_TPH_PV": 115.4,
    "SLD01_FLOW_TPH_PV": 114.0,
    "SLD01_POWER_KW_PV": 31.4
  },
  "status": {
    "system": {
      "running": true,
      "time_s": 145.0,
      "total_mass_t": 5.8,
      "total_kWh": 8.2,
      "warehouse_level_pct": 68.5,
      "kWh_per_ton": 1.414,
      "cost_BRL": 5.33
    },
    "gates": [
      {
        "name": "GATE_01",
        "setpoint_pct": 0.0,
        "opening_pct": 0,
        "flow_tph": 0,
        "failure": false
      },
      ...
    ],
    "belts": [
      {
        "name": "CORR01",
        "running": true,
        "speed_mps": 1.59,
        "flow_tph": 115.4,
        "load_pct": 23.1,
        "power_kw": 34.7,
        "current_a": 53.6,
        "temp_c": 56.4,
        "misalignment": 0.3
      },
      ...
    ],
    "shiploader": {
      "name": "SHIPLOADER_01",
      "setpoint_tph": 1500.0,
      "flow_tph": 114.0,
      "power_kw": 31.4,
      "current_a": 48.5
    }
  }
}
```

---

## ✅ Checklist de Validação

### Backend
- [x] WebSocket endpoint existe em `/api/v1/ws/simulator/stream`
- [x] Simulador rodando (`curl http://localhost:8000/api/v1/simulator/status`)
- [x] Streaming inicia automaticamente ao conectar
- [x] Mensagens enviadas a cada 1 segundo (1 Hz)

### Frontend (Precisa Atualizar)
- [ ] Hook `useRealtimeData` usando URL correta
- [ ] Componente `ProfessionalRealtime` recebendo dados
- [ ] Status mudando de "Disconnected" para "Live"
- [ ] Tags atualizando em tempo real

---

## 🚀 Próximos Passos

1. **Atualizar `useRealtimeData.ts`**:
   - Mudar URL padrão de `/ws` para `/api/v1/ws/simulator/stream`

2. **Testar no Browser**:
   - Abrir DevTools → Network → WS
   - Ver conexão WebSocket ativa
   - Ver mensagens chegando a cada 1s

3. **Verificar Status**:
   - Chip deve mostrar "Live" (verde)
   - Tags devem atualizar valores
   - Gráficos devem receber dados

---

## 📝 Arquivos para Modificar

```
✅ frontend/src/hooks/useRealtimeData.ts
   Linha 74: url = 'ws://localhost:8000/api/v1/ws/simulator/stream'

⚠️ Alternativa (se não quiser mudar o hook):
   frontend/src/pages/ProfessionalRealtime.tsx
   Linha 59: Adicionar { url: 'ws://...' } nas options
```

---

**Depois dessa mudança, o status mudará de "Disconnected" para "Live"! ✅**

