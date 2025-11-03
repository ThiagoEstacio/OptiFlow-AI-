# Simulador de Terminal Graneleiro - Guia de Execução

## Problema Identificado

O simulador **NÃO está atualizando as variáveis em tempo real** porque:

1. **O loop de background não está executando automaticamente**
2. **Dependências do projeto principal (auth, database) estão causando problemas**

## Solução Implementada

### Arquivos Modificados

#### 1. `backend/app/api/routes/simulator.py`
Adicionado:
- **Loop de simulação em background**: `simulation_loop()` que executa `sim.step(1.0)` a cada segundo
- **Logs de debug** para rastrear execução
- **Inicialização automática** do loop quando `/start` é chamado

```python
async def simulation_loop():
    """Background task that runs the simulation continuously"""
    global _simulation_running
    sim = get_simulator()

    print(f"[SIMULATOR] Background loop started. Running: {sim.running}")

    while _simulation_running:
        try:
            if sim.running:
                # Run simulation step (1 second)
                sim.step(dt_s=1.0)
                print(f"[SIMULATOR] Step executed. Time: {sim.time_s:.1f}s, CORR01 current: {sim.belts['CORR01'].current_A:.1f}A")
            # Sleep for 1 second (real-time simulation)
            await asyncio.sleep(1.0)
        except Exception as e:
            print(f"[SIMULATOR] Simulation loop error: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(1.0)
```

#### 2. `backend/simulator_standalone.py`
Criado servidor **standalone** sem dependências de auth/database:
- Apenas FastAPI + simulador
- Middleware CORS configurado
- Exception handler com traceback completo

## Como Executar (MANUALMENTE)

### Opção 1: Servidor Standalone (Recomendado)

```bash
cd /home/user/OptiFlow-AI-/backend

# Instalar dependências mínimas
pip3 install fastapi uvicorn

# Iniciar servidor
python3 -m uvicorn simulator_standalone:app --host 0.0.0.0 --port 8000 --reload
```

### Opção 2: Servidor Principal (Requer mais dependências)

```bash
cd /home/user/OptiFlow-AI-/backend

# Instalar todas as dependências
pip3 install -r requirements.txt

# OU instalar manualmente as essenciais:
pip3 install fastapi uvicorn slowapi asyncua sqlalchemy alembic python-jose passlib bcrypt python-multipart pydantic-settings asyncpg email-validator

# Iniciar servidor
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Testar se Está Funcionando

### 1. Verificar se servidor está rodando
```bash
curl http://localhost:8000/health
# Deve retornar: {"status":"healthy"}
```

### 2. Resetar simulador
```bash
curl -X POST http://localhost:8000/api/v1/simulator/reset
# Deve retornar: {"success":true,"message":"Sistema resetado com sucesso"}
```

### 3. Iniciar sistema
```bash
curl -X POST http://localhost:8000/api/v1/simulator/start
# Deve retornar: {"success":true,"message":"Sistema iniciado com sucesso"}
```

**IMPORTANTE**: Aguarde 2-3 segundos e verifique o log do servidor. Você deve ver:
```
[SIMULATOR] Background loop started. Running: True
[SIMULATOR] Step executed. Time: 1.0s, CORR01 current: 123.4A
[SIMULATOR] Step executed. Time: 2.0s, CORR01 current: 125.6A
...
```

### 4. Verificar status (deve mostrar valores mudando)
```bash
# Primeira leitura
curl http://localhost:8000/api/v1/simulator/status | python3 -m json.tool > status1.json

# Aguardar 5 segundos
sleep 5

# Segunda leitura
curl http://localhost:8000/api/v1/simulator/status | python3 -m json.tool > status2.json

# Comparar
diff status1.json status2.json
```

Se os valores estiverem mudando (time_s, current_A, power_kW, temp_bearing_C), o simulador está funcionando!

### 5. Testar interface web

```bash
cd /home/user/OptiFlow-AI-/frontend

# Instalar dependências
npm install

# Iniciar frontend
npm run dev
```

Acessar: `http://localhost:5173/simulator`

1. Clicar em **"Iniciar Sistema"**
2. Aguardar 5-10 segundos
3. Verificar se os valores de corrente, potência e temperatura estão mudando

## Script de Teste Automático

```bash
cd /home/user/OptiFlow-AI-/backend
python3 tests/test_api_realtime.py
```

Este script:
- Reseta o sistema
- Inicia o sistema
- Monitora por 10 segundos
- Verifica se tempo, corrente, potência e temperatura estão mudando
- Mostra resultado: ✅ PASSOU ou ❌ FALHOU

## Troubleshooting

### Problema: Servidor não inicia

**Erro**: `ModuleNotFoundError: No module named 'X'`

**Solução**: Instalar módulo faltante
```bash
pip3 install X
```

### Problema: Valores não estão mudando

**Verificar**:
1. Se o servidor está mostrando os logs `[SIMULATOR] Step executed...`
2. Se o sistema foi iniciado com `/start`
3. Se `sim.running` é `True`

**Debug**:
```bash
# Ver logs do servidor em tempo real
tail -f nohup.out  # se rodou com nohup
# OU ver saída do terminal onde executou uvicorn
```

### Problema: Erro 500 no /status

**Possíveis causas**:
1. Simulador não foi inicializado corretamente
2. Falta alguma dependência

**Debug**:
Verificar traceback completo no log do servidor

## Arquitetura da Solução

```
┌─────────────────────────────────────────────────────┐
│ Frontend (React)                                     │
│  - Auto-refresh a cada 2s                           │
│  - Chama /api/v1/simulator/status                   │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP GET (2s interval)
┌──────────────────▼──────────────────────────────────┐
│ Backend (FastAPI)                                    │
│  ┌────────────────────────────────────────────────┐ │
│  │ /start endpoint                                │ │
│  │  - Chama sim.start()                           │ │
│  │  - Cria asyncio.Task(simulation_loop())        │ │
│  └────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────┐ │
│  │ simulation_loop() [BACKGROUND]                 │ │
│  │  while _simulation_running:                    │ │
│  │    if sim.running:                             │ │
│  │      sim.step(dt_s=1.0)  ← CHAVE!             │ │
│  │    await asyncio.sleep(1.0)                    │ │
│  └────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────┐ │
│  │ /status endpoint                               │ │
│  │  - Retorna sim.belts, sim.gates, etc.          │ │
│  │  - Valores são atualizados pelo step()         │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## Próximos Passos

Se ainda não estiver funcionando:

1. **Executar manualmente** conforme este guia
2. **Copiar todos os logs** do servidor
3. **Executar** o script de teste: `python3 tests/test_api_realtime.py`
4. **Reportar** qual etapa falhou

## Commits Realizados

1. **feat: Add background simulation loop to simulator API** - Implementação do loop
2. **feat: Complete simulator interface with real-time updates** - Expansão da interface
3. **feat: Add standalone simulator server** - Servidor simplificado

Todos os commits estão no branch: `claude/add-chatbot-ai-011CUdj4zT6jFFR2nKHsykcK`
