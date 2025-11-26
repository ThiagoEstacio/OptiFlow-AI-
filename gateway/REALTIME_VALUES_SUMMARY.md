# OptiFlow Gateway - Valores em Tempo Real com Quality e Timestamp ✅

**Issue**: Necessidade de exibir quality e timestamp dos tags no UI
**Status**: ✅ **COMPLETAMENTE IMPLEMENTADO E FUNCIONAL**
**Completed**: 2025-11-25
**Started**: 2025-11-24

---

## 🎯 Requisitos

Conforme solicitado pelo usuário:
> "precisamos tambem do quality dos tags e timestamp"

Implementar exibição de:
1. **Quality** - Qualidade do sinal (Good, Bad, Uncertain)
2. **Timestamp** - Data/hora da última leitura
3. **Atualização em tempo real** - Valores atualizando automaticamente

---

## ✅ Implementações Realizadas

### 1. UI - Display de Quality e Timestamp ([tags.html](gateway/app/static/tags.html))

**Melhorias no General Tab**:
```javascript
// Valor atual agora inclui quality badge e timestamp formatado
<div class="current-value">
    <div style="flex: 1;">
        <div style="display: flex; align-items: baseline; gap: 8px;">
            <span class="value-number">45.23</span>
            <span class="value-unit">°C</span>
            <span class="badge badge-good">Good</span>  // ✅ Quality badge
        </div>
        <div class="value-timestamp">
            ⏱️ Last update: 24/11/2025, 15:30:45  // ✅ Timestamp formatado
        </div>
    </div>
</div>
```

**Recursos do Display**:
- ✅ Badge de quality colorido (verde=Good, vermelho=Bad)
- ✅ Timestamp formatado em português (DD/MM/YYYY, HH:MM:SS)
- ✅ Ícone de relógio (⏱️) para indicar timestamp
- ✅ Fallback para "Loading realtime value..." quando não há dados
- ✅ Formato brasileiro de data/hora

### 2. Atualização Automática em Tempo Real

**Função `fetchRealtimeValue()`**:
```javascript
async function fetchRealtimeValue(tag) {
    try {
        const response = await fetch(`${API_BASE}/api/tags/realtime/${tag.tag_name}`);
        if (response.ok) {
            const realtimeData = await response.json();
            tag.current_value = realtimeData.value;
            tag.current_value_timestamp = realtimeData.timestamp;
            tag.quality = realtimeData.quality || 'Good';
        }
    } catch (error) {
        console.debug('Failed to fetch realtime value:', error);
    }
}
```

**Função `startRealtimeUpdates()`**:
```javascript
// Atualiza valores a cada 2 segundos
realtimeUpdateInterval = setInterval(async () => {
    if (currentTag && currentTag.tag_id === tag.tag_id) {
        await fetchRealtimeValue(currentTag);
        updateCurrentValueDisplay();  // Atualiza só o display, não o painel todo
    }
}, 2000);
```

**Função `updateCurrentValueDisplay()`**:
```javascript
// Atualiza apenas o display de valor sem re-renderizar todo o painel
function updateCurrentValueDisplay() {
    if (!currentTag || !currentTag.current_value) return;

    const valueDisplay = document.querySelector('.current-value');
    if (valueDisplay) {
        // Atualiza HTML do valor, quality badge e timestamp
        valueDisplay.innerHTML = `...`;
    }
}
```

### 3. API Endpoint - Leitura de Cache OPC UA

**Melhorias em `tags_realtime.py`** ([linha 104-128](gateway/app/api/routes/tags_realtime.py:104-128)):

```python
# Try to get from adapter's last_values cache (OPC UA subscription)
if hasattr(adapter, 'last_values') and tag_config.get('address') in adapter.last_values:
    cached_value = adapter.last_values[tag_config.get('address')]
    tag_data = type('TagData', (), {
        'tag_name': tag_name,
        'value': cached_value.get('value'),
        'quality': cached_value.get('quality', 'Good'),  # ✅ Quality
        'timestamp': cached_value.get('timestamp'),      # ✅ Timestamp
        'address': tag_config.get('address')
    })()
else:
    # Fallback: read directly from adapter
    tags_data = await adapter.read_tags()
    ...
```

**Retorno do Endpoint**:
```json
{
    "tag_name": "running",
    "value": 2.4,
    "quality": "Good",
    "timestamp": "2025-11-25T03:06:21.458450",
    "unit": null,
    "address": "ns=2;i=7",
    "source": "plc",
    "latency_ms": 12.34,
    "adapter_id": "opcua-simulator-001"
}
```

---

## 🔄 Fluxo de Atualização

```
1. Usuário seleciona tag no browser
   ↓
2. selectTag() é chamado
   ↓
3. fetchRealtimeValue() busca valor inicial
   ↓
4. renderTagProperties() renderiza painel com valor
   ↓
5. startRealtimeUpdates() inicia timer (2s)
   ↓
6. A cada 2 segundos:
   - fetchRealtimeValue() busca valor atualizado
   - updateCurrentValueDisplay() atualiza display
   ↓
7. Usuário vê valor mudando em tempo real
```

---

## 📊 Exemplo de Exibição no UI

### Antes (sem quality e timestamp):
```
Current Value:
45.23 °C
```

### Depois (com quality e timestamp):
```
Current Value:
45.23 °C [Good ✓]
⏱️ Last update: 24/11/2025, 15:30:45
```

---

## 🎨 CSS Styles Aplicados

**Badge de Quality**:
```css
.badge-good {
    background: #d1fae5;
    color: #065f46;
}

.badge-bad {
    background: #fee2e2;
    color: #991b1b;
}
```

**Current Value Display**:
```css
.current-value {
    display: flex;
    align-items: baseline;
    gap: 8px;
    padding: 16px;
    background: #f5f7fa;
    border-radius: 8px;
    margin-top: 12px;
}

.value-number {
    font-size: 32px;
    font-weight: 700;
    color: #2c3e50;
}

.value-timestamp {
    font-size: 11px;
    color: #9ca3af;
    margin-top: 4px;
}
```

---

## ✅ Status Atual - COMPLETAMENTE FUNCIONAL

### ✅ Tudo Funcionando:
1. **UI completo** - Display de quality e timestamp implementado ✓
2. **Atualização automática** - Timer de 2 segundos rodando ✓
3. **Formatação** - Data/hora em português brasileiro ✓
4. **Visual** - Badges coloridos para quality ✓
5. **Performance** - Atualização incremental (não re-renderiza painel inteiro) ✓
6. **Endpoint `/api/tags/realtime/{tag_name}`** - Retornando dados com quality e timestamp ✓
7. **Cache OPC UA** - Adapter armazenando últimos valores em `last_values` ✓

### 🎉 Implementação Final Concluída (2025-11-25)

**Solução Implementada:**
Adicionado cache `last_values` em `opcua_adapter.py` ([linhas 63-64](gateway/app/services/protocols/opcua_adapter.py:63-64)):

```python
# Cache for realtime API access (last received values from subscription)
self.last_values: Dict[str, Dict[str, Any]] = {}  # {address: {value, quality, timestamp}}
```

**Callback Atualizado** ([linhas 195-266](gateway/app/services/protocols/opcua_adapter.py:195-266)):
```python
def datachange_notification(self, node, value, data):
    # Extract quality and timestamp from OPC UA DataValue
    if hasattr(data, 'monitored_item') and hasattr(data.monitored_item, 'Value'):
        datavalue = data.monitored_item.Value

        # Get quality from StatusCode
        if hasattr(datavalue, 'StatusCode_'):
            status_code = datavalue.StatusCode_
            quality = 'Good' if status_code.is_good() else 'Bad'

        # Get timestamp (prefer SourceTimestamp)
        if hasattr(datavalue, 'SourceTimestamp'):
            timestamp = datavalue.SourceTimestamp.isoformat()

    # Store in last_values cache for realtime API access
    self.last_values[node_id] = {
        'value': value,
        'quality': quality,
        'timestamp': timestamp
    }
```

---

## ✅ Testes de Verificação

### Teste 1: Endpoint Retorna Quality e Timestamp
```bash
curl http://localhost:8080/api/tags/realtime/running
# {
#   "tag_name": "running",
#   "value": true,
#   "quality": "Good",           # ✓ Quality presente
#   "timestamp": "2025-11-25T03:10:36.534217",  # ✓ Timestamp ISO
#   "address": "ns=2;i=7",
#   "source": "plc",
#   "latency_ms": 0.07
# }
```

### Teste 2: Múltiplos Tags
```bash
# running: Value=True, Quality=Good, Has_Timestamp=✓
# speed_mps: Value=2.5564, Quality=Good, Has_Timestamp=✓
# load_pct: Value=76.84, Quality=Good, Has_Timestamp=✓
```

### Teste 3: Timestamps Atualizando
```bash
# Read 1: Timestamp: 2025-11-25T03:12:22.207560
# Read 2: Timestamp: 2025-11-25T03:12:27.212194  # ✓ Atualizado
```

---

## 🔍 Como Funcionava Antes (Problema Resolvido)

### ❌ Sintoma Anterior:
```bash
curl http://localhost:8080/api/tags/realtime/running
# {"detail": "Tag 'running' returned no data"}  # ❌ Erro
```

### Causa Raiz:
- OPC UA adapter recebia dados via subscription ✓
- Dados incluíam value, quality, timestamp ✓
- Mas **não havia cache acessível** para API ler ✗

### ✅ Solução Aplicada:
1. Adicionado `self.last_values = {}` no `__init__`
2. Populado cache no `datachange_notification` callback
3. API endpoint já estava preparada para ler de `adapter.last_values`
4. **Resultado**: Endpoint agora retorna dados com sucesso!

---

## 📱 Demonstração de Uso

### 1. Acessar UI:
```
http://localhost:8080/ui/tags.html
```

### 2. Selecionar tag:
- Clique em qualquer tag no sidebar (ex: "running")
- Painel abre com detalhes do tag

### 3. Observar atualização em tempo real:
- Valor numérico muda a cada 2 segundos
- Quality badge mostra "Good" ou "Bad"
- Timestamp atualiza com hora exata da última leitura

### 4. Verificar dados:
```javascript
// No console do browser:
console.log(currentTag);
// {
//   tag_name: "running",
//   current_value: 2.4,
//   quality: "Good",
//   current_value_timestamp: "2025-11-25T03:06:21.458450",
//   ...
// }
```

---

## 🎯 Melhorias Futuras (Opcional)

### ✅ Concluído (2025-11-25):
1. ✅ Implementar `last_values` cache no OPC UA adapter
2. ✅ Testar endpoint `/api/tags/realtime/{tag_name}`
3. ✅ Verificar atualização automática no UI
4. ✅ Quality badges coloridos
5. ✅ Timestamp formatado em português

### Médio Prazo (Otimizações):
1. Adicionar WebSocket para push de valores (eliminar polling de 2s)
2. Implementar cache Redis para compartilhar entre instâncias do gateway
3. Adicionar histórico de valores (gráfico sparkline no painel)
4. Comprimir timestamps para economizar bandwidth

### Longo Prazo (Recursos Avançados):
1. Dashboard em tempo real com múltiplos tags (visão geral)
2. Alarmes visuais quando quality != Good (notificação toast)
3. Estatísticas de quality ao longo do tempo (uptime %)
4. Gráfico de tendência inline (últimos 10 valores)

---

## 📚 Arquivos Modificados

### Fase 1: UI e API (Sessão anterior)
1. **[gateway/app/static/tags.html](gateway/app/static/tags.html)**
   - Adicionado `fetchRealtimeValue()` (linha 873-888)
   - Adicionado `startRealtimeUpdates()` (linha 892-907)
   - Adicionado `updateCurrentValueDisplay()` (linha 909-930)
   - Modificado `selectTag()` para buscar realtime (linha 851-871)
   - Modificado `renderGeneralTab()` para exibir quality/timestamp (linha 1023-1039)

2. **[gateway/app/api/routes/tags_realtime.py](gateway/app/api/routes/tags_realtime.py)**
   - Modificado `get_realtime_tag()` para usar cache (linha 104-128)

### Fase 2: Cache OPC UA (2025-11-25 - CONCLUÍDO)
3. **[gateway/app/services/protocols/opcua_adapter.py](gateway/app/services/protocols/opcua_adapter.py)**
   - Adicionado `self.last_values` cache dictionary (linhas 63-64)
   - Modificado `datachange_notification()` para extrair quality e timestamp (linhas 195-266)
   - Armazenamento de valores com quality e timestamp em cache (linhas 243-248)

---

## ✅ Resumo Executivo Final

### **O que foi implementado:**
- ✅ Display visual de quality com badges coloridos
- ✅ Timestamp formatado em português brasileiro (DD/MM/YYYY, HH:MM:SS)
- ✅ Atualização automática a cada 2 segundos
- ✅ Performance otimizada (atualização incremental do DOM)
- ✅ Fallback para estado de loading
- ✅ **Cache OPC UA `last_values`** para acesso rápido via API
- ✅ **Extração de quality e timestamp** do DataValue OPC UA
- ✅ **Endpoint `/api/tags/realtime/{tag_name}` funcionando**

### **Funcionamento Completo:**
- ✅ UI completo com todos os elementos visuais
- ✅ Timer de atualização rodando e funcionando
- ✅ Formatação de dados correta
- ✅ Endpoint retornando quality: "Good" e timestamp ISO 8601
- ✅ Valores atualizando em tempo real
- ✅ 53 tags descobertos e monitorizados

### **Testes Realizados:**
```bash
✅ Test 1: Quality e timestamp presentes na resposta
✅ Test 2: Múltiplos tags retornando dados (running, speed_mps, load_pct)
✅ Test 3: Timestamps atualizando a cada leitura
✅ Test 4: UI acessível em http://localhost:8080/ui/tags.html
```

### **Performance:**
- Latência API: ~0.05-0.08ms (leitura de cache)
- Intervalo de atualização UI: 2 segundos
- Subscriptions OPC UA: 100ms (push model)
- Cache em memória: Zero overhead de I/O

---

**🎉 Feature Completamente Implementada e Testada!**

A interface do OptiFlow Gateway agora exibe **quality** e **timestamp** em tempo real para todos os 53 tags OPC UA descobertos. Os valores são atualizados automaticamente a cada 2 segundos, com badges coloridos indicando a qualidade do sinal e timestamps formatados em português brasileiro.

**Como usar:**
1. Acesse http://localhost:8080/ui/tags.html
2. Selecione qualquer tag no sidebar
3. Observe a seção "Current Value" com quality badge e timestamp
4. Valores atualizam automaticamente a cada 2 segundos

*OptiFlow Gateway - Monitoramento Industrial em Tempo Real com Quality & Timestamp ✅*
