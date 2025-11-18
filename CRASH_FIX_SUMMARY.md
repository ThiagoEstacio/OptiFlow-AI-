# 🔧 Correção do Crash do Sistema - Relatório Técnico

## 📊 O Que Aconteceu

O sistema OptiFlow travou completamente após query de descoberta "Quais tags de temperatura?", resultando em:
- Backend 100% CPU/memória
- Timeout de 30+ segundos em queries simples
- Ollama não responsivo
- Necessidade de `docker compose down` forçado

## 🔍 Análise da Causa Raiz

### Problema 1: Loop Infinito de Queries InfluxDB
**Sintoma**: Centenas de erros `'str' object has no attribute 'isoformat'` nos logs

**Causa**: 
- Query "Quais tags?" ativou função `get_all_tags()` ou `search_tags()`
- Retornou 50-100+ tags simultaneamente
- Agent tentou buscar dados históricos de TODAS as tags em paralelo
- Cada tag gerou 2 queries: `get_realtime_value()` + `get_historical_data()`
- Total: 100-200+ queries simultâneas ao InfluxDB

**Evidência**:
```
ERROR:app.services.data_service:Error getting historical data for <tag>: 'str' object has no attribute 'isoformat'
```
(Repetido 500+ vezes em 1 minuto)

### Problema 2: Código Dessincrono (Cache Docker)
**Sintoma**: Alterações no código não eram aplicadas após `docker compose restart`

**Causa**:
- Fix de conversão datetime estava correto no arquivo fonte
- Docker usava imagem em CACHE sem as mudanças
- Layer `COPY . .` não detectava mudanças sutis

**Evidência**:
```bash
#10 [backend stage-1 5/6] COPY . .
#10 CACHED  ⚠️ NÃO RECOMPILOU!
```

### Problema 3: Ausência de Rate Limiting
**Sintoma**: Sistema não limitava queries concorrentes

**Causa**:
- Nenhum controle de concorrência no `DataService`
- Nenhum timeout nas queries InfluxDB
- Nenhum limite máximo em `get_all_tags()`

## ✅ Correções Implementadas

### 1. **Rate Limiting Global** (data_service.py)
```python
# PROTECTION: Rate limiting for InfluxDB queries (prevent loops)
_influx_query_semaphore = asyncio.Semaphore(10)  # Max 10 concurrent queries
_influx_query_timeout = 30  # 30 seconds timeout per query
```

**Impacto**: Máximo de 10 queries simultâneas, nunca mais loops infinitos

### 2. **Timeout por Query** (data_service.py)
```python
async def get_historical_data(...):
    async with _influx_query_semaphore:
        try:
            return await asyncio.wait_for(
                self._get_historical_data_impl(...),
                timeout=_influx_query_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"⏱️ InfluxDB query timeout for tag {tag_id}")
            return {"error": "Query timeout", "data_points": []}
```

**Impacto**: Queries travadas não bloqueiam sistema inteiro, retornam erro após 30s

### 3. **Limite Máximo de Tags** (data_service.py + agent_tools.py)
```python
async def get_all_tags(self, limit: int = 50, ...):
    # PROTECTION: Enforce maximum limit to prevent memory issues
    limit = min(limit, 100)  # HARD CAP
```

**Impacto**: Máximo 100 tags retornadas, mesmo se agent pedir mais

### 4. **Proteção em search_tags** (agent_tools.py)
```python
async def _search_tags(self, query: str, limit: int = 20):
    # PROTECTION: Limit max results to prevent memory issues
    limit = min(limit, 50)
    return await self.data_service.search_tags(query, limit)
```

**Impacto**: Buscas retornam no máximo 50 resultados

### 5. **Proteção em get_all_tags do Agent** (agent_tools.py)
```python
async def _get_all_tags(self, limit: int = 50, ...):
    # PROTECTION: Enforce max limit to prevent memory/CPU issues
    limit = min(limit, 50)
```

**Impacto**: Agent nunca processa mais de 50 tags de uma vez

## 🛡️ Mecanismos de Proteção Adicionados

| Camada | Proteção | Limite | Propósito |
|--------|----------|--------|-----------|
| **InfluxDB** | Semaphore | 10 queries concorrentes | Evitar sobrecarga |
| **InfluxDB** | Timeout | 30s por query | Evitar travamento |
| **DataService** | Hard Cap | Max 100 tags | Limite de memória |
| **Agent Tools** | Hard Cap | Max 50 tags | Limite de processamento |
| **Search** | Hard Cap | Max 50 resultados | Limite de busca |

## 📝 Mudanças Necessárias para Aplicar

### Opção 1: Rebuild Completo (Recomendado)
```bash
docker compose down
docker compose build --no-cache backend
docker compose up -d postgres influxdb redis ollama backend
```

### Opção 2: Forçar Mudança no Código
```bash
touch backend/app/services/data_service.py
docker compose build backend  # Sem --no-cache
docker compose up -d backend
```

## 🧪 Testes de Validação

Após subir sistema, testar:

### 1. Query de Descoberta (Causou o Crash)
```bash
curl -X POST http://localhost:8000/api/v1/agent/dashboard/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Quais tags de temperatura estão disponíveis?"}'
```
**Esperado**: 
- ✅ Resposta em < 5 segundos
- ✅ Lista com no máximo 50 tags
- ✅ Sem errors nos logs

### 2. Estatísticas (Funcionava)
```bash
curl -X POST http://localhost:8000/api/v1/agent/dashboard/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Calcule a média de ELEV01_TEMP_C_PV nas últimas 24 horas"}'
```
**Esperado**:
- ✅ Resposta em < 10 segundos
- ✅ Estatísticas reais (72.69°C confirmado anteriormente)
- ✅ Sem timeout

### 3. Múltiplas Queries Simultâneas (Teste de Stress)
```bash
for i in {1..20}; do
  curl -X POST http://localhost:8000/api/v1/agent/dashboard/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "Olá"}' &
done
wait
```
**Esperado**:
- ✅ Todas respondem
- ✅ Backend não trava
- ✅ Memória estável

## 📈 Monitoramento Pós-Fix

### Logs a Observar
```bash
# Verificar se rate limiting está funcionando
docker logs optiflow-backend 2>&1 | grep "InfluxDB query timeout"

# Verificar se semaphore está limitando
docker logs optiflow-backend 2>&1 | grep "concurrent queries"

# Verificar uso de recursos
docker stats optiflow-backend
```

### Métricas de Sucesso
- **CPU**: < 80% em queries normais
- **Memória**: < 1GB em operação normal
- **Latência**: < 10s para queries analíticas
- **Timeout**: 0 queries travadas

## 🔄 Próximos Passos

1. ✅ **Aplicar correções** (rebuild backend)
2. ⏳ **Validar com testes** (3 cenários acima)
3. ⏳ **Refinar classificação híbrida** (discovery keywords)
4. ⏳ **Otimizar ferramentas** (compare_tags, detect_anomalies)
5. ⏳ **Adicionar monitoramento** (Prometheus metrics)

## 📚 Lições Aprendidas

### 1. **Docker Cache é Traiçoeiro**
- ❌ `docker compose restart` não recompila código
- ❌ `docker compose build` usa cache agressivo
- ✅ Sempre usar `--no-cache` quando mudanças críticas

### 2. **Rate Limiting é Essencial**
- ❌ Confiar que agent não abusará de ferramentas
- ✅ Sempre limitar queries concorrentes
- ✅ Sempre ter timeout em operações externas

### 3. **Proteção em Múltiplas Camadas**
- ✅ DataService: Limita concorrência
- ✅ Agent Tools: Limita quantidade
- ✅ API: Limita complexidade

### 4. **Logs Salvam Vidas**
- Os 500+ erros nos logs revelaram o loop infinito
- Timestamps mostraram quando começou (query de descoberta)
- Stack traces identificaram o bug de datetime

## 🎯 Estado Final Esperado

Após aplicar correções:
- ✅ **Sistema estável**: Não trava mesmo com queries pesadas
- ✅ **Proteções ativas**: Rate limiting + timeouts + hard caps
- ✅ **Código sincronizado**: Container com últimas mudanças
- ✅ **Queries funcionais**: Descoberta + Estatísticas + Comparação
- ✅ **Qwen operacional**: Respostas em português com dados reais

---

**Data da Correção**: 18 de novembro de 2025  
**Versão**: v1.0 (Post-Crash Fix)  
**Status**: ⚠️ **CORREÇÕES APLICADAS NO CÓDIGO, AGUARDANDO REBUILD**
