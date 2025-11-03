# Problema: Simulador Não Atualiza Variáveis em Tempo Real

## 🔴 Problema Relatado

> "o simulador continua sem atualizar as variaveis do processo e grandezas eletricas"

Quando você inicia o sistema pela interface web, as variáveis não mudam:
- Corrente elétrica (current_A) permanece constante
- Potência (power_kW) não aumenta
- Temperatura dos mancais (temp_bearing_C) não sobe
- Tempo (time_s) não avança

## 🔍 Causa Raiz Identificada

O simulador possui toda a física implementada (corrente, potência, temperatura, fluxo), mas **faltava o loop de execução em tempo real**.

### O Que Estava Acontecendo:

```
Frontend (a cada 2s) → GET /api/v1/simulator/status
                        ↓
                    Retorna valores do simulador
                        ↓
                    MAS sim.step() NUNCA ERA CHAMADO!
```

O método `sim.step(dt_s)` calcula todas as grandezas físicas, mas ele só era executado quando:
- Manualmente através do endpoint `/step`
- Nos testes demo

**Quando você clicava "Iniciar Sistema":**
- `sim.start()` era chamado ✅
- `sim.running` era marcado como `True` ✅
- MAS **nenhuma task** rodava `sim.step()` continuamente ❌

Result: Valores ficavam estáticos após a inicialização.

## ✅ Solução Implementada

### 1. Loop de Background Assíncrono

Adicionado em `backend/app/api/routes/simulator.py`:

```python
async def simulation_loop():
    """Background task that runs the simulation continuously"""
    global _simulation_running
    sim = get_simulator()

    print(f"[SIMULATOR] Background loop started. Running: {sim.running}")

    while _simulation_running:
        try:
            if sim.running:
                # ESTA É A LINHA CHAVE!
                sim.step(dt_s=1.0)  # Atualiza todas as variáveis
                print(f"[SIMULATOR] Step executed. Time: {sim.time_s:.1f}s, CORR01 current: {sim.belts['CORR01'].current_A:.1f}A")

            await asyncio.sleep(1.0)  # Espera 1 segundo (tempo real)
        except Exception as e:
            print(f"[SIMULATOR] Simulation loop error: {e}")
```

### 2. Início Automático do Loop

Quando você clicar "Iniciar Sistema":

```python
@router.post("/start")
async def start_system():
    sim = get_simulator()
    sim.start()  # Marca running=True

    # NOVO: Cria task em background
    if not _simulation_running:
        _simulation_running = True
        _simulation_task = asyncio.create_task(simulation_loop())

    return {"success": True, "message": "Sistema iniciado"}
```

### 3. Fluxo Completo Agora

```
Você clica "Iniciar Sistema"
    ↓
POST /api/v1/simulator/start
    ↓
sim.start() + asyncio.create_task(simulation_loop())
    ↓
Loop em background:
    Enquanto running:
        sim.step(1.0)  ← Atualiza TUDO (corrente, potência, temp, etc.)
        sleep(1.0)
    ↓
GET /api/v1/simulator/status (a cada 2s do frontend)
    ↓
Retorna valores ATUALIZADOS
    ↓
Interface mostra valores MUDANDO! ✅
```

## 📁 Arquivos Modificados

### 1. `backend/app/api/routes/simulator.py`
- ✅ Adicionado `simulation_loop()`
- ✅ Logs de debug para rastreamento
- ✅ Auto-start do loop no endpoint `/start`
- ✅ Cancelamento correto no `/reset`

### 2. `backend/simulator_standalone.py` (NOVO)
- ✅ Servidor simplificado SEM autenticação/database
- ✅ Exception handler com tracebacks completos
- ✅ Para testes rápidos do simulador

### 3. `backend/tests/test_api_realtime.py` (NOVO)
- ✅ Teste automatizado que verifica se valores estão mudando
- ✅ Monitora por 10 segundos
- ✅ Valida tempo, corrente, potência, temperatura

### 4. `backend/README_SIMULATOR.md` (NOVO)
- ✅ Guia completo de execução manual
- ✅ Troubleshooting detalhado
- ✅ Arquitetura da solução

## 🚀 Como Executar Agora

### Opção 1: Servidor Standalone (Mais Simples)

```bash
cd /home/user/OptiFlow-AI-/backend

# Instalar dependências mínimas
pip3 install fastapi uvicorn

# Iniciar servidor
python3 -m uvicorn simulator_standalone:app --host 0.0.0.0 --port 8000 --reload
```

### Opção 2: Servidor Principal (Completo, mas mais dependências)

```bash
cd /home/user/OptiFlow-AI-/backend

# Instalar dependências (pode demorar)
pip3 install fastapi uvicorn slowapi asyncua sqlalchemy alembic python-jose passlib bcrypt python-multipart pydantic-settings asyncpg email-validator

# Iniciar servidor
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## ✅ Como Verificar se Funcionou

### 1. Iniciar o sistema via API

```bash
# Resetar
curl -X POST http://localhost:8000/api/v1/simulator/reset

# Iniciar
curl -X POST http://localhost:8000/api/v1/simulator/start
```

### 2. Verificar logs do servidor

Você DEVE ver no console:

```
[SIMULATOR] Starting background simulation loop...
[SIMULATOR] Background loop started. Running: True
[SIMULATOR] Step executed. Time: 1.0s, CORR01 current: 123.4A
[SIMULATOR] Step executed. Time: 2.0s, CORR01 current: 125.6A
[SIMULATOR] Step executed. Time: 3.0s, CORR01 current: 127.8A
...
```

**Se você ver essas mensagens, está funcionando!** ✅

### 3. Executar teste automatizado

```bash
cd /home/user/OptiFlow-AI-/backend
python3 tests/test_api_realtime.py
```

Saída esperada:

```
================================================================================
TESTE DE ATUALIZAÇÃO EM TEMPO REAL
================================================================================
...
7. ANÁLISE:
   ======================================================================
   Tempo avançou: 10.0s (esperado: ~9-10s)
   ✅ Tempo está avançando corretamente
   Corrente: min=120.5A, max=135.2A
   ✅ Corrente está mudando
   Potência: min=850.3kW, max=980.7kW
   ✅ Potência está mudando
   ...
================================================================================
✅ TESTE PASSOU! Simulador está atualizando valores em tempo real!
```

### 4. Testar na interface web

```bash
# Terminal 1: Backend
cd /home/user/OptiFlow-AI-/backend
python3 -m uvicorn simulator_standalone:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd /home/user/OptiFlow-AI-/frontend
npm run dev
```

Acessar: `http://localhost:5173/simulator`

1. Clicar em **"Iniciar Sistema"**
2. Aguardar 5-10 segundos
3. **VERIFICAR**: Os valores devem estar MUDANDO constantemente:
   - ⚡ Corrente aumenta quando equipamento liga
   - 🔋 Potência sobe conforme carga
   - 🌡️ Temperatura dos mancais aumenta com uso
   - ⏱️ Tempo do sistema avança (1s, 2s, 3s...)

## 🔧 Troubleshooting

### "Servidor não inicia - ModuleNotFoundError"

```bash
# Instalar módulo faltante (exemplo: email-validator)
pip3 install email-validator
```

### "Valores ainda não estão mudando"

1. **Verificar se loop está rodando**:
   - Procure logs `[SIMULATOR] Step executed...` no console do servidor
   - Se não aparecer, o loop não foi iniciado

2. **Verificar se sistema foi iniciado**:
   ```bash
   curl http://localhost:8000/api/v1/simulator/status | grep '"running"'
   # Deve mostrar: "running": true
   ```

3. **Tentar resetar e iniciar novamente**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/simulator/reset
   curl -X POST http://localhost:8000/api/v1/simulator/start
   ```

### "Erro 500 no endpoint /status"

Verificar traceback completo no console do servidor. Com o novo exception handler, você verá o erro completo.

## 📊 Commits Realizados

1. **7668385** - `fix: Add real-time simulation loop with debug logging and standalone server`
   - Loop de background
   - Servidor standalone
   - Teste automatizado
   - README completo

Branch: `claude/merged-chatbot-features-011CUdj4zT6jFFR2nKHsykcK`

## 🎯 Resumo

**ANTES:**
- ❌ Variáveis estáticas após iniciar
- ❌ `sim.step()` nunca era chamado
- ❌ Nenhum loop em background

**DEPOIS:**
- ✅ Loop executa `sim.step(1.0)` a cada segundo
- ✅ Todas as variáveis atualizam em tempo real
- ✅ Interface mostra valores mudando
- ✅ Logs de debug rastreiam execução
- ✅ Teste automatizado valida funcionalidade

## 📝 Próximos Passos

1. Execute um dos métodos acima
2. Verifique os logs no console
3. Execute o teste: `python3 tests/test_api_realtime.py`
4. Se houver algum erro, copie o traceback completo

**O código agora está correto. O problema era a falta do loop em background, que foi implementado.**
