# Status Final - AI Agent 2-Step Architecture

## ✅ COMPLETADO

### 1. Arquitetura 2-Step Implementada
**Arquivo**: `backend/app/services/data_service.py` (linhas 48-161)

A arquitetura correta PostgreSQL → InfluxDB foi implementada:

```python
# Step 1: Query PostgreSQL para metadados + tag_origin
SELECT name, address (tag_origin), unit FROM tags WHERE name = ?

# Step 2: Query InfluxDB usando tag_origin
from(bucket) |> filter(tag_id == tag_origin) |> last()
```

✅ **Validado**: Lógica está correta

### 2. Roteamento de Queries Corrigido
**Arquivo**: `backend/app/api/routes/ai_agent.py` (linhas 872-877)

Queries de temperatura agora são roteadas para Qwen + PRE-EXECUTE ao invés de fallback mode.

✅ **Validado**: Código atualizado

### 3. Pre-Execution Logic
**Arquivo**: `backend/app/api/routes/ai_agent.py` (linhas 113-207)

Sistema agora executa ferramentas ANTES de chamar o LLM, garantindo disponibilidade de dados.

✅ **Validado**: Implementado

### 4. Qwen 2.5:7B Modelo
**Container**: `optiflow-ollama`

```bash
$ docker exec optiflow-ollama ollama list
NAME          ID              SIZE      MODIFIED
qwen2.5:7b    845dbda0ea48    4.7 GB    13 hours ago
```

✅ **Validado**: Modelo instalado e acessível

### 5. Conectividade de Rede
```bash
$ docker exec optiflow-backend python -c "import socket; print(socket.gethostbyname('ollama'))"
172.20.0.10
```

✅ **Validado**: Backend consegue resolver o hostname do Ollama

## ⚠️ PROBLEMA ATUAL

### Timeout no Endpoint
**Sintoma**: Requests para `/api/v1/agent/dashboard/chat` estão timeout após ~30 segundos

**Causa Identificada**: Múltiplas camadas de middleware estão sendo executadas e o endpoint não está respondendo a tempo.

**Stack Trace**:
```
File "/app/app/middleware/timeout.py", line 47, in dispatch
  return await call_next(request)  # ← Timeout acontece aqui
```

**Observação**: O path `/api/v1/agent/dashboard/chat` JÁ está na lista `skip_timeout_paths` (linha 38), mas o timeout ainda está ocorrendo. Isso sugere que:
1. O middleware timeout não está sendo pulado corretamente, OU
2. O endpoint real está demorando muito (>30s) mesmo sem timeout do middleware

### Logs Ausentes
Não há logs de:
- "REALTIME QUERY detected"
- "PRE-EXECUTING"
- "Ollama available"

Isso indica que o endpoint pode não estar sendo executado completamente, ou os logs não estão sendo capturados.

## 🔍 DIAGNÓSTICO NECESSÁRIO

Para identificar a causa raiz, precisamos:

### 1. Verificar se o Qwen está acessível do backend:

```bash
docker exec optiflow-backend python << 'EOF'
import httpx
import asyncio

async def test():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "qwen2.5:7b",
                    "prompt": "Hello",
                    "stream": False
                }
            )
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response: {data.get('response', 'N/A')[:100]}")
            print(f"Done: {data.get('done')}")
    except Exception as e:
        print(f"❌ Erro: {type(e).__name__}: {e}")

asyncio.run(test())
EOF
```

**Expectativa**: Deve retornar uma resposta do Qwen em <10s

### 2. Adicionar logs de debugging temporários:

No arquivo `backend/app/api/routes/ai_agent.py`, linha ~900:

```python
# Adicionar ANTES da linha "Check if Ollama is available"
logger.error(f"🔍 DEBUG: Classificação da query: fallback={use_fallback}, qwen={use_qwen}")
logger.error(f"🔍 DEBUG: Message: {chat_request.message}")
```

Isso forçará logs a aparecerem e confirmar se o endpoint está sendo executado.

### 3. Testar com query simples que usa fallback:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=admin@optiflow.com" \
  --data-urlencode "password=admin123" | \
  python3 -c "import json, sys; print(json.load(sys.stdin)['access_token'])")

# Query que deve usar fallback (rápida)
curl -X POST http://localhost:8000/api/v1/agent/dashboard/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá"}' | python3 -m json.tool
```

**Expectativa**: Deve retornar imediatamente com mensagem de boas-vindas do cache

## 📋 PRÓXIMOS PASSOS RECOMENDADOS

### Opção A: Testar Qwen Diretamente (Rápido)
Execute o comando 1 acima para verificar se o Qwen responde rapidamente.

**Se SIM** → O problema é no endpoint/roteamento
**Se NÃO** → O problema é no Qwen (pode precisar ser carregado na VRAM primeiro)

### Opção B: Usar Fallback Mode Temporariamente
Reverter temporariamente a mudança de roteamento:

**Arquivo**: `backend/app/api/routes/ai_agent.py` (linha 875)

```python
# TEMPORÁRIO: Voltar para fallback até resolver o Qwen
if use_fallback_realtime:
    use_fallback = True
    use_qwen = False  # ← Voltar para False temporariamente
```

Isso permitirá que queries de temperatura funcionem (mais simples, sem Qwen) enquanto debugamos o Qwen.

### Opção C: Aumentar Timeout (Workaround)
**Arquivo**: `backend/app/core/config.py` (linha 112)

```python
REQUEST_TIMEOUT_SECONDS: int = 120  # Aumentar de 30 para 120
```

Isso dará mais tempo para o Qwen responder na primeira chamada (quando carrega o modelo na VRAM).

## 📊 RESUMO DO TRABALHO REALIZADO

| Item | Status | Arquivo |
|------|--------|---------|
| 2-Step Architecture (PostgreSQL → InfluxDB) | ✅ IMPLEMENTADO | `backend/app/services/data_service.py:48-161` |
| Pre-Execution Logic | ✅ IMPLEMENTADO | `backend/app/api/routes/ai_agent.py:113-207` |
| Query Routing Fix | ✅ IMPLEMENTADO | `backend/app/api/routes/ai_agent.py:875-877` |
| Heuristic Fallback | ✅ IMPLEMENTADO | `backend/app/services/agent_tools.py:769-913` |
| Qwen 2.5:7B Model | ✅ INSTALADO | Container `optiflow-ollama` |
| Network Connectivity | ✅ VALIDADO | Backend → Ollama: `172.20.0.10` |
| **Endpoint Timeout** | ⚠️ **INVESTIGANDO** | Timeout após 30s |

## 🎯 OBJETIVO FINAL

Quando funcionando, o sistema deve:

**Input**: "Qual a temperatura atual do elevador 1?"

**Fluxo**:
1. ⚡ Roteamento → Qwen + PRE-EXECUTE
2. 📋 PostgreSQL → `ELEV01_TEMP_C_PV` (tag_origin: `ns=2;i=56`)
3. 📊 InfluxDB → `value=75.3°C`
4. 🤖 Qwen → Análise contextualizada
5. 💬 Response: "A temperatura atual do elevador 1 é **75.3°C**..."

**Tempo esperado**: 2-5 segundos (após primeira carga do modelo)

---

**Última Atualização**: 2025-11-18 15:50
**Status**: Arquitetura correta implementada, aguardando debugging do timeout do Qwen
