# Guia Rápido - Iniciar Simulador

## ⚠️ Problema Atual

Você está tentando acessar rotas que não existem no servidor standalone:
- ❌ `/api/v1/devices/` - NÃO EXISTE
- ✅ `/api/v1/simulator/` - EXISTE (rotas do simulador)

## 🚀 Solução - Iniciar Corretamente

### Opção 1: Apenas Simulador (Recomendado para teste)

**Terminal 1 - Backend Standalone:**
```bash
cd /home/user/OptiFlow-AI-/backend
python3 -m uvicorn simulator_standalone:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd /home/user/OptiFlow-AI-/frontend
npm run dev
```

**Acessar**: `http://localhost:5173/simulator` (ou `http://localhost:3002/simulator`)

### Opção 2: Sistema Completo (com auth, devices, etc)

**ANTES de iniciar, instale as dependências que faltam:**
```bash
cd /home/user/OptiFlow-AI-/backend
pip3 install email-validator
```

**Terminal 1 - Backend Completo:**
```bash
cd /home/user/OptiFlow-AI-/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd /home/user/OptiFlow-AI-/frontend
npm run dev
```

## 🔧 Corrigindo Avisos do React Router

Edite o arquivo que configura o BrowserRouter e adicione as flags:

**Arquivo**: `frontend/src/main.tsx` ou `frontend/src/App.tsx`

```tsx
<BrowserRouter
  future={{
    v7_startTransition: true,
    v7_relativeSplatPath: true
  }}
>
  {/* suas rotas */}
</BrowserRouter>
```

## ✅ Verificar se Backend Está Rodando

```bash
# Teste 1: Health check
curl http://localhost:8000/health

# Deve retornar: {"status":"healthy"}

# Teste 2: Rotas disponíveis
curl http://localhost:8000/

# Teste 3: Status do simulador
curl http://localhost:8000/api/v1/simulator/status
```

## 🐛 Se o Erro Persistir

### 1. Verifique a porta do frontend

No navegador, você está em:
- `http://localhost:3002` ← porta diferente do padrão Vite (5173)
- Verifique se há outro processo usando a porta

### 2. Limpe o cache do navegador

```
Ctrl + Shift + Delete (ou Cmd + Shift + Delete no Mac)
→ Marque "Cached images and files"
→ Clear data
```

### 3. Verifique se o backend está realmente rodando

```bash
# Verificar processos Python rodando
ps aux | grep uvicorn

# Se não houver nada, o backend não está rodando!
```

## 📋 Checklist Rápido

- [ ] Backend rodando em `http://localhost:8000`
- [ ] Frontend rodando em `http://localhost:5173` ou `http://localhost:3002`
- [ ] Navegador acessando a rota correta: `/simulator`
- [ ] Sem erros CORS no console (F12)
- [ ] Endpoint `/api/v1/simulator/status` retornando 200 OK

## 🎯 Para APENAS testar o simulador

Use esta sequência exata:

```bash
# Terminal 1 - Backend
cd /home/user/OptiFlow-AI-/backend
pkill -9 -f uvicorn  # Mata qualquer processo anterior
python3 -m uvicorn simulator_standalone:app --host 0.0.0.0 --port 8000

# Aguarde ver:
# INFO:     Uvicorn running on http://0.0.0.0:8000

# Terminal 2 - Teste
curl http://localhost:8000/health
# Deve retornar: {"status":"healthy"}

# Terminal 3 - Frontend
cd /home/user/OptiFlow-AI-/frontend
npm run dev

# Navegador - Acesse:
http://localhost:5173/simulator
```

## ❓ Qual erro você está vendo agora?

1. CORS error? → Verifique se backend está rodando
2. 404 Not Found? → Verifique a URL (deve ter `/simulator`)
3. Página em branco? → Verifique console do navegador (F12)
4. Backend não inicia? → Cole o erro aqui
