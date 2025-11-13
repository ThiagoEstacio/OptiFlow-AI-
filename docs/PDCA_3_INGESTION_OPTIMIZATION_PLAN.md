# 📊 PDCA #3: Otimização de Ingestão de Dados OPC-UA

## Status: **EM ANDAMENTO** ⚙️

**Objetivo**: Otimizar performance de coleta de dados para 1000+ tags OPC-UA
**Prioridade**: Alta
**Estimativa**: 4-6 horas

---

## 🔍 PLAN - Análise da Situação Atual

### Arquitetura Atual

```
┌─────────────────┐
│ GatewayManager  │
│  (Backend)      │
└────────┬────────┘
         │
         │ Cria e gerencia
         ▼
┌─────────────────┐
│  OPCUAGateway   │
│  (BaseGateway)  │
└────────┬────────┘
         │
         │ Polling Loop (interval_ms)
         ▼
┌─────────────────────────────────┐
│  read_multiple_tags()           │
│  - Batch read com asyncio       │
│  - Fallback para reads unitários│
└─────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  OPC-UA Server  │
│  (1000+ tags)   │
└─────────────────┘
```

### Implementação Atual

#### 1. Polling Loop (`base_gateway.py:225`)

```python
async def _polling_loop(self, interval_ms: int) -> None:
    interval_sec = interval_ms / 1000.0
    tag_configs = self.config.get('tags', [])

    while True:
        # Read all configured tags
        data_points = await self.read_multiple_tags(tag_configs)

        await asyncio.sleep(interval_sec)
```

**Características**:
- ✅ Loop assíncrono
- ✅ Intervalo configurável
- ⚠️ Lê TODAS as tags em cada ciclo
- ⚠️ Sem otimização por prioridade
- ⚠️ Sem batching inteligente

#### 2. Batch Reading (`opcua_gateway.py:193`)

```python
async def read_multiple_tags(self, tag_configs: List[Dict]) -> List[DataPoint]:
    # Get all nodes
    nodes = []
    for tag_config in enabled_tags:
        node_id_str = tag_config.get('address_config', {}).get('node_id')
        node = await self._get_node(node_id_str)  # ⚠️ SEQUENTIAL
        nodes.append((node, tag_config))

    # Batch read
    values = await self.client.read_values([node for node, _ in nodes])
```

**Problemas Identificados**:
1. ⚠️ **Get nodes é sequencial** - loop `for` com `await`
2. ⚠️ **Cache de nodes não é otimizado** - cada tag faz lookup
3. ⚠️ **Sem chunking** - lê todas as tags de uma vez
4. ⚠️ **Fallback ineficiente** - se batch falha, lê tudo unitário

#### 3. OPC-UA Handler (`gateway/app/protocols/opcua_handler.py:156`)

```python
async def read_tags(self, tag_addresses: List[str]) -> List[TagValue]:
    # Get all nodes
    nodes = []
    for address in tag_addresses:
        node = await self._get_node(address)  # ⚠️ SEQUENTIAL
        if node:
            nodes.append((address, node))

    # Read all in parallel
    read_tasks = [node.read_data_value() for _, node in nodes]
    data_values = await asyncio.gather(*read_tasks, return_exceptions=True)
```

**Melhor que backend**, mas ainda sequencial no get_node

---

## 📊 Métricas Atuais (Estimadas)

### Performance com 1000 Tags

| Métrica | Valor Estimado | Problema |
|---------|----------------|----------|
| Get nodes (sequencial) | ~2-3s | ❌ CRÍTICO |
| Batch read OPC-UA | ~0.5-1s | ✅ OK |
| Processing + storage | ~0.5s | ✅ OK |
| **Total por ciclo** | **~3-4.5s** | ❌ ALTO |
| Polling interval | 1000ms | ❌ Violado! |
| **Real interval** | **~4-5s** | ❌ 4-5x mais lento |

### Gargalos Identificados

1. **🔴 CRÍTICO: Get nodes sequencial**
   - 1000 tags × 2-3ms cada = 2-3 segundos
   - Loop `for` com `await` bloqueia execução
   - **Impacto**: 60-75% do tempo total

2. **🟡 MÉDIO: Sem chunking de batches**
   - 1000 tags em 1 batch read
   - OPC-UA servers têm limites (tipicamente 100-500 itens)
   - Pode causar timeouts ou rejeitções

3. **🟡 MÉDIO: Fallback ineficiente**
   - Se batch falha, lê 1000 tags unitariamente
   - Pode levar 10-30 segundos
   - Sem retry parcial

4. **🟢 BAIXO: Cache não é pré-aquecido**
   - Primeiro ciclo sempre lento
   - Cache é lazy (só carrega quando precisa)

---

## 🎯 DO - Plano de Otimização

### Estratégia: Otimização em 3 Níveis

#### Nível 1: Get Nodes Paralelo (High Impact - 1h)

**Problema**: Get nodes é sequencial
**Solução**: Paralelizar com `asyncio.gather`

**Implementação**:

```python
# ANTES (opcua_gateway.py:219)
nodes = []
for tag_config in enabled_tags:
    node_id_str = tag_config.get('address_config', {}).get('node_id')
    if node_id_str:
        node = await self._get_node(node_id_str)  # ⚠️ SEQUENTIAL
        nodes.append((node, tag_config))

# DEPOIS (OTIMIZADO)
async def _get_node_with_config(self, tag_config):
    node_id_str = tag_config.get('address_config', {}).get('node_id')
    if node_id_str:
        node = await self._get_node(node_id_str)
        return (node, tag_config)
    return None

# Get all nodes in parallel
node_tasks = [self._get_node_with_config(tag) for tag in enabled_tags]
nodes_with_config = await asyncio.gather(*node_tasks, return_exceptions=True)
nodes = [n for n in nodes_with_config if n and not isinstance(n, Exception)]
```

**Impacto Esperado**:
- ⏱️ Get nodes: 2-3s → **0.1-0.2s** (15x mais rápido!)
- 📊 Total por ciclo: 3-4.5s → **1.5-2s**
- ✅ Polling interval respeitado (1s)

#### Nível 2: Chunking Inteligente (Medium Impact - 1.5h)

**Problema**: Batch read de 1000 tags pode falhar
**Solução**: Dividir em chunks de 100-200 tags

**Implementação**:

```python
async def read_multiple_tags(self, tag_configs: List[Dict], chunk_size: int = 100) -> List[DataPoint]:
    """Read tags in chunks for better reliability."""
    data_points = []

    # Get all nodes in parallel (Nível 1)
    nodes_with_config = await self._get_nodes_parallel(tag_configs)

    # Split into chunks
    chunks = [nodes_with_config[i:i + chunk_size]
              for i in range(0, len(nodes_with_config), chunk_size)]

    # Read each chunk
    for chunk in chunks:
        try:
            nodes = [node for node, _ in chunk]
            values = await self.client.read_values(nodes)

            # Process chunk results
            for (node, tag_config), value in zip(chunk, values):
                data_point = self._create_data_point(tag_config, value)
                data_points.append(data_point)

        except Exception as e:
            logger.warning(f"Chunk failed, falling back: {e}")
            # Fallback para este chunk apenas
            for node, tag_config in chunk:
                try:
                    data_point = await self.read_tag(tag_config)
                    if data_point:
                        data_points.append(data_point)
                except Exception:
                    pass  # Skip failed tag

    return data_points
```

**Impacto Esperado**:
- 🛡️ Maior resiliência (chunk failure não afeta outros)
- 📊 Compatibilidade com mais servidores OPC-UA
- ⏱️ Tempo similar ou melhor (chunks em paralelo)

#### Nível 3: Pre-warming e Otimizações Avançadas (Low Impact - 1.5h)

**a) Pre-warm Node Cache**

```python
async def _prewarm_node_cache(self, tag_configs: List[Dict]) -> None:
    """Pre-load all nodes into cache on connection."""
    logger.info(f"Pre-warming node cache for {len(tag_configs)} tags...")

    node_tasks = [self._get_node(tag.get('address_config', {}).get('node_id'))
                  for tag in tag_configs
                  if tag.get('address_config', {}).get('node_id')]

    await asyncio.gather(*node_tasks, return_exceptions=True)

    logger.info(f"Node cache pre-warmed: {len(self._nodes_cache)} nodes")

# Chamar em connect()
async def connect(self) -> bool:
    success = await super().connect()
    if success:
        await self._prewarm_node_cache(self.config.get('tags', []))
    return success
```

**b) Prioritização de Tags**

```python
# Adicionar priority field nas tags
class TagPriority(str, Enum):
    HIGH = "high"      # Ler sempre (crítico)
    MEDIUM = "medium"  # Ler normal
    LOW = "low"        # Ler menos frequente (logs, histórico)

# Polling loop com prioridades
async def _polling_loop(self, interval_ms: int) -> None:
    cycle_count = 0

    while True:
        # High priority: todo ciclo
        high_priority_tags = [t for t in tags if t.get('priority') == 'high']
        data_points = await self.read_multiple_tags(high_priority_tags)

        # Medium priority: todo ciclo
        medium_priority_tags = [t for t in tags if t.get('priority') == 'medium']
        data_points += await self.read_multiple_tags(medium_priority_tags)

        # Low priority: a cada 10 ciclos
        if cycle_count % 10 == 0:
            low_priority_tags = [t for t in tags if t.get('priority') == 'low']
            data_points += await self.read_multiple_tags(low_priority_tags)

        cycle_count += 1
        await asyncio.sleep(interval_sec)
```

**c) Adaptive Chunking**

```python
class AdaptiveChunker:
    def __init__(self):
        self.current_chunk_size = 200
        self.success_count = 0
        self.failure_count = 0

    def adjust_chunk_size(self, success: bool):
        if success:
            self.success_count += 1
            # Aumenta chunk se estável
            if self.success_count > 10:
                self.current_chunk_size = min(500, self.current_chunk_size + 50)
                self.success_count = 0
        else:
            self.failure_count += 1
            # Diminui chunk se instável
            if self.failure_count > 2:
                self.current_chunk_size = max(50, self.current_chunk_size - 50)
                self.failure_count = 0
```

---

## ✅ CHECK - Métricas de Sucesso

### Performance Targets

| Métrica | Antes | Meta | Melhoria |
|---------|-------|------|----------|
| Get nodes (1000 tags) | 2-3s | <0.2s | 15x |
| Total por ciclo | 3-4.5s | <2s | 2x |
| Polling interval real | 4-5s | ~1s | 4-5x |
| Success rate | ~60% | >95% | 1.5x |
| Max tags por segundo | ~250 | >1000 | 4x |

### Testes Necessários

1. **Load Test: 1000 Tags**
   ```bash
   # Simular 1000 tags
   python test_opcua_load.py --tags 1000 --interval 1000
   ```

2. **Stress Test: Failure Scenarios**
   - Timeout de rede
   - Tag inválida
   - Server disconnection

3. **Latency Test: Response Times**
   - P50, P95, P99 latencies
   - Ciclos consecutivos

### Monitoramento

```python
# Adicionar métricas ao gateway
class PerformanceMetrics:
    get_nodes_time: float
    batch_read_time: float
    total_cycle_time: float
    tags_per_second: float
    chunk_size_used: int
    cache_hit_rate: float
```

---

## 🎯 ACT - Implementação Priorizada

### Fase 1: Quick Wins (2h)

1. ✅ **Paralelizar get_nodes** (1h)
   - Maior impacto (15x speedup)
   - Baixo risco
   - Backward compatible

2. ✅ **Implementar chunking** (1h)
   - Melhora resiliência
   - Compatibilidade servers

### Fase 2: Optimizations (2h)

3. ✅ **Pre-warm cache** (30min)
   - Melhora primeiro ciclo
   - Zero overhead depois

4. ✅ **Adaptive chunking** (1h)
   - Auto-ajusta performance
   - Adapta a condições de rede

5. ✅ **Métricas e monitoring** (30min)
   - Visibilidade de performance
   - Alertas de degradação

### Fase 3: Advanced (2h - Opcional)

6. ⚠️ **Prioritização de tags** (1h)
   - Reduz carga média
   - Requer mudanças no schema

7. ⚠️ **Subscriptions OPC-UA** (1h)
   - Push-based em vez de polling
   - Requer suporte do servidor

---

## 📋 Arquivos a Modificar

### Backend

1. **`backend/app/gateways/opcua_gateway.py`**
   - ✏️ `read_multiple_tags()` - paralelizar get_nodes
   - ✏️ `read_multiple_tags()` - adicionar chunking
   - ➕ `_get_nodes_parallel()` - novo método
   - ➕ `_prewarm_node_cache()` - novo método
   - ➕ `AdaptiveChunker` - nova classe

2. **`backend/app/gateways/base_gateway.py`**
   - ✏️ `_polling_loop()` - adicionar métricas
   - ➕ `PerformanceMetrics` - nova classe
   - ✏️ `get_health_metrics()` - incluir perf metrics

3. **`backend/app/models/gateway_config.py`**
   - ➕ `chunk_size: int` - configurável
   - ➕ `enable_chunking: bool`
   - ➕ `enable_cache_prewarm: bool`

### Gateway Service

4. **`gateway/app/protocols/opcua_handler.py`**
   - ✏️ `read_tags()` - paralelizar get_nodes
   - Aplicar mesmas otimizações

### Tests

5. **`tests/test_opcua_performance.py`** (NEW)
   - Load tests
   - Stress tests
   - Latency tests

---

## 🚀 Resumo Executivo

### Problema
- Sistema atual lê 1000 tags em ~4-5 segundos
- Polling interval configurado (1s) não é respeitado
- Gargalo: get_nodes sequencial (60-75% do tempo)

### Solução
- **Nível 1**: Paralelizar get_nodes → 15x speedup
- **Nível 2**: Chunking inteligente → maior resiliência
- **Nível 3**: Otimizações avançadas → adaptive tuning

### Impacto
- ⏱️ Ciclo: 4-5s → ~1-2s (2-4x mais rápido)
- 📊 Tags/s: 250 → >1000 (4x throughput)
- ✅ Success rate: 60% → >95%
- 💰 ROI: Alto (implementação simples, impacto grande)

### Next Steps
1. Implementar Fase 1 (2h) - Quick wins
2. Testar com carga real
3. Medir resultados
4. Iterar com Fase 2 se necessário

---

**Data**: 2025-11-13
**Status**: 🟡 PLAN COMPLETO - Pronto para implementação
**Estimativa**: 4-6 horas total
**Prioridade**: 🔥 ALTA (Impacto direto na performance do sistema)
