# ✅ Fix: Real-time Monitoring "Disconnected"

**Data**: 2025-11-14 21:45
**Status**: ✅ **RESOLVIDO**

---

## 🎯 Problema Identificado

O frontend mostrava "**Disconnected**" na página Real-time Monitoring porque estava tentando buscar dados de um endpoint inexistente:

```typescript
// ❌ ENDPOINT ANTIGO (não existe)
const response = await apiClient.get('/api/v1/demo/tags/realtime');
```

**Erro**: `404 Not Found`

---

## ✅ Solução Implementada

### 1. Novo Endpoint Criado

Criado `/api/v1/demo/tags/realtime` que:
- Busca todas as tags do PostgreSQL
- Obtém valores em tempo real do InfluxDB
- Retorna dados formatados para o frontend
- Suporta filtros por categoria e limite

**Arquivo**: `backend/app/api/v1/endpoints/demo.py`

### 2. Endpoints Disponíveis

#### GET `/api/v1/demo/tags/realtime`

Retorna todas as tags com seus valores em tempo real.

**Query Parameters**:
- `limit` (int, default=50): Máximo de tags a retornar
- `category` (str, opcional): Filtrar por categoria (ENERGY, PROCESS, MAINTENANCE, QUALITY)

**Exemplo**:
```bash
curl "http://localhost:8000/api/v1/demo/tags/realtime?limit=10&category=energy"
```

**Resposta**:
```json
[
  {
    "tag_name": "energy_consumption",
    "name": "energy_consumption",
    "value": 1137.77,
    "unit": "kWh",
    "timestamp": "2025-11-14T21:26:53.284823+00:00",
    "quality": "good",
    "category": "energy",
    "description": "Total Energy Consumption",
    "address": "ns=2;s=energy_consumption"
  },
  {
    "tag_name": "production_rate",
    "name": "production_rate",
    "value": 98.5,
    "unit": "tons/h",
    "timestamp": "2025-11-14T21:26:53.284823+00:00",
    "quality": "good",
    "category": "process",
    "description": "Production Rate",
    "address": "ns=2;s=production_rate"
  }
]
```

#### GET `/api/v1/demo/system/status`

Retorna o status geral do sistema.

**Resposta**:
```json
{
  "simulator": {
    "running": true,
    "status": "connected"
  },
  "database": {
    "status": "connected"
  },
  "influxdb": {
    "status": "connected"
  },
  "overall_status": "connected"
}
```

#### GET `/api/v1/demo/tags/{tag_name}/history`

Retorna dados históricos de uma tag específica.

**Query Parameters**:
- `minutes` (int, default=60): Minutos de histórico

**Exemplo**:
```bash
curl "http://localhost:8000/api/v1/demo/tags/energy_consumption/history?minutes=120"
```

---

## 🔧 Como Usar no Frontend

### Opção 1: Usar o Endpoint Demo (Recomendado para MVP)

```typescript
// RealTimeDataView.tsx
const fetchRealtimeData = async () => {
  try {
    const response = await apiClient.get('/api/v1/demo/tags/realtime', {
      params: {
        limit: 50,
        category: selectedCategory !== 'all' ? selectedCategory : undefined,
      },
    });

    const newReadings: TagReading[] = response.data.map((item: any) => ({
      tag_name: item.tag_name,
      value: item.value,
      unit: item.unit,
      timestamp: item.timestamp,
      quality: item.quality,
      category: item.category,
      trend: calculateTrend(item),  // Sua lógica de tendência
      change_percent: calculateChange(item),
    }));

    setReadings(newReadings);
    setConnectionStatus('connected');  // ✅ Agora mostra "Connected"
  } catch (error) {
    console.error('Error fetching realtime data:', error);
    setConnectionStatus('disconnected');
  }
};
```

### Opção 2: Usar Endpoints Individuais

```typescript
// Para tags específicas
const tags = ['energy_consumption', 'production_rate', 'conveyor_speed'];

const fetchBatchRealtime = async () => {
  const promises = tags.map(tag =>
    apiClient.get(`/api/v1/tags/realtime/${tag}`)
  );

  const results = await Promise.all(promises);
  // Process results...
};
```

---

## 📊 Validação

### Teste 1: Endpoint Funcional ✅

```bash
$ curl "http://localhost:8000/api/v1/demo/tags/realtime?limit=3"
[
  {
    "tag_name": "energy_consumption",
    "value": 1137.77,
    "unit": "kWh",
    "quality": "good"
  },
  ...
]
```

### Teste 2: Simulador Rodando ✅

```bash
$ curl "http://localhost:8000/api/v1/simulator/status"
{
  "system": {
    "running": true,
    "time_s": 27.0,
    "total_mass_t": 0.0
  }
}
```

### Teste 3: Sistema Status ✅

```bash
$ curl "http://localhost:8000/api/v1/demo/system/status"
{
  "overall_status": "connected",
  "simulator": { "status": "connected" }
}
```

---

## 🎨 Update do Frontend (Próximo Passo)

### Adicionar Indicador de Status

```typescript
// RealTimeDataView.tsx
const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected'>('disconnected');

// Fetch system status periodically
useEffect(() => {
  const fetchStatus = async () => {
    try {
      const response = await apiClient.get('/api/v1/demo/system/status');
      setConnectionStatus(response.data.overall_status === 'connected' ? 'connected' : 'disconnected');
    } catch {
      setConnectionStatus('disconnected');
    }
  };

  fetchStatus();
  const interval = setInterval(fetchStatus, 5000);  // Check every 5s
  return () => clearInterval(interval);
}, []);

// Display status
<Chip
  label={connectionStatus === 'connected' ? 'Connected' : 'Disconnected'}
  color={connectionStatus === 'connected' ? 'success' : 'error'}
  icon={connectionStatus === 'connected' ? <CheckCircle /> : <Error />}
/>
```

### Adicionar Controles do Simulador

```typescript
// Botões de controle
const startSimulator = async () => {
  await apiClient.post('/api/v1/simulator/start');
};

const stopSimulator = async () => {
  await apiClient.post('/api/v1/simulator/stop');
};

// UI
<ButtonGroup>
  <Button
    startIcon={<PlayArrow />}
    onClick={startSimulator}
    disabled={connectionStatus === 'connected'}
  >
    Start
  </Button>
  <Button
    startIcon={<Stop />}
    onClick={stopSimulator}
    disabled={connectionStatus === 'disconnected'}
  >
    Stop
  </Button>
</ButtonGroup>
```

---

## 📝 Arquivos Modificados

```
✅ backend/app/api/v1/endpoints/demo.py (NOVO)
   - GET /demo/tags/realtime
   - GET /demo/system/status
   - GET /demo/tags/{tag_name}/history

✅ backend/app/api/v1/api.py
   - Adicionado import demo
   - Registrado router demo

✅ Ambos copiados para container e backend reiniciado
```

---

## 🚀 Próximas Melhorias

### 1. WebSocket para Real-time

Atualmente usando polling (HTTP requests a cada 2s). Para verdadeiro real-time:

```python
# backend/app/api/v1/endpoints/demo.py
@router.websocket("/ws/realtime")
async def realtime_websocket(websocket: WebSocket):
    await websocket.accept()

    while True:
        # Fetch latest data
        data = await get_realtime_tags_data()

        # Send to client
        await websocket.send_json(data)

        # Wait 1 second
        await asyncio.sleep(1)
```

```typescript
// Frontend
const ws = new WebSocket('ws://localhost:8000/api/v1/demo/ws/realtime');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  setReadings(data);
};
```

### 2. Adicionar Gráficos Sparkline

Pequenos gráficos inline para cada tag mostrando tendência:

```typescript
import { Sparklines, SparklinesLine } from 'react-sparklines';

<Sparklines data={tag.history.map(h => h.value)} width={100} height={30}>
  <SparklinesLine color="blue" />
</Sparklines>
```

### 3. Alarmes em Tempo Real

```typescript
// Highlight tags with alarms
const getTagColor = (tag: TagReading) => {
  if (tag.quality === 'bad') return 'error';
  if (tag.value > tag.max_value) return 'warning';
  return 'default';
};
```

---

## ✅ Status Final

| Item | Status |
|------|--------|
| Endpoint criado | ✅ |
| Dados retornando | ✅ |
| Simulador rodando | ✅ |
| Tags com valores | ✅ |
| Sistema conectado | ✅ |

**Frontend agora deve mostrar "Connected" em vez de "Disconnected"!**

Basta o frontend começar a usar:
```
GET /api/v1/demo/tags/realtime?limit=50
```

Em vez de:
```
GET /api/v1/tags/  # (retorna apenas metadados, sem valores)
```

---

**Documento gerado**: 2025-11-14 21:45 UTC
**Backend reiniciado**: ✅
**Endpoints testados**: ✅
**Pronto para uso no frontend**: ✅
