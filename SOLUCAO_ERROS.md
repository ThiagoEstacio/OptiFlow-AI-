# Solução para Erros do Console

## 🔍 Erros Identificados

### 1. ✅ RESOLVIDO - Avisos do React Router

**Erro original:**
```
⚠️ React Router Future Flag Warning: React Router will begin wrapping state updates in `React.startTransition` in v7
⚠️ React Router Future Flag Warning: Relative route resolution within Splat routes is changing in v7
```

**Solução aplicada:**

Editado `frontend/src/App.tsx` para incluir as flags de futuro:

```tsx
<BrowserRouter
  future={{
    v7_startTransition: true,
    v7_relativeSplatPath: true
  }}
>
```

✅ Esses avisos não aparecerão mais após reiniciar o frontend.

---

### 2. ⚠️ ERRO CORS - Precisa Atenção

**Erro:**
```
Access to XMLHttpRequest at 'http://localhost:8000/api/v1/devices/'
from origin 'http://localhost:3002' has been blocked by CORS policy
```

**Causa:**
Você está tentando acessar rotas que **NÃO existem no servidor standalone**.

O servidor standalone (`simulator_standalone.py`) tem APENAS estas rotas:
- ✅ `/api/v1/simulator/*` - Rotas do simulador
- ❌ `/api/v1/devices/` - NÃO EXISTE
- ❌ `/api/v1/sites/` - NÃO EXISTE
- ❌ `/api/v1/auth/` - NÃO EXISTE

**Soluções:**

#### Solução A: Use o Servidor Completo (Recomendado se precisa de devices, sites, auth, etc)

```bash
# Terminal 1 - Backend COMPLETO
cd /home/user/OptiFlow-AI-/backend

# Primeiro, instalar dependências que faltam
pip3 install email-validator

# Iniciar servidor completo
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Este servidor tem TODAS as rotas:
- ✅ `/api/v1/simulator/*`
- ✅ `/api/v1/devices/`
- ✅ `/api/v1/sites/`
- ✅ `/api/v1/auth/`
- ✅ Todas as outras

#### Solução B: Use Apenas o Simulador (Recomendado se só quer testar o simulador)

```bash
# Terminal 1 - Backend STANDALONE (apenas simulador)
cd /home/user/OptiFlow-AI-/backend
python3 -m uvicorn simulator_standalone:app --host 0.0.0.0 --port 8000 --reload
```

**E acesse DIRETO a página do simulador:**
```
http://localhost:3002/simulator
```

**NÃO acesse:**
- ❌ `http://localhost:3002/devices` - vai dar erro
- ❌ `http://localhost:3002/sites` - vai dar erro
- ❌ `http://localhost:3002/` (home) - pode dar erro

---

### 3. 🔧 Erros "Uncaught (in promise) Object"

**Causa:**
Esses erros aparecem quando o frontend tenta carregar dados de rotas que não existem ou que dão erro 401 (não autenticado).

**Solução:**

Se estiver usando servidor STANDALONE:
- Acesse APENAS `/simulator`
- Não tente acessar outras páginas

Se estiver usando servidor COMPLETO:
- Faça login primeiro em `/login`
- Depois acesse as outras páginas

---

## 🚀 Comandos Passo a Passo

### Para TESTAR APENAS O SIMULADOR:

```bash
# 1. Parar tudo que está rodando
pkill -9 -f uvicorn
pkill -9 -f "npm.*dev"

# 2. Terminal 1 - Backend Standalone
cd /home/user/OptiFlow-AI-/backend
python3 -m uvicorn simulator_standalone:app --host 0.0.0.0 --port 8000 --reload

# Aguarde ver:
# INFO:     Uvicorn running on http://0.0.0.0:8000

# 3. Terminal 2 - Frontend
cd /home/user/OptiFlow-AI-/frontend
npm run dev

# 4. Navegador - Acesse DIRETO:
http://localhost:5173/simulator
# OU (se estiver na porta 3002)
http://localhost:3002/simulator
```

✅ **Deve funcionar sem erros CORS**

---

### Para USAR O SISTEMA COMPLETO:

```bash
# 1. Parar tudo que está rodando
pkill -9 -f uvicorn
pkill -9 -f "npm.*dev"

# 2. Instalar dependências que faltam
cd /home/user/OptiFlow-AI-/backend
pip3 install email-validator

# 3. Terminal 1 - Backend Completo
cd /home/user/OptiFlow-AI-/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Terminal 2 - Frontend
cd /home/user/OptiFlow-AI-/frontend
npm run dev

# 5. Navegador - Faça login primeiro:
http://localhost:5173/login
# OU
http://localhost:3002/login

# 6. Depois de logar, pode acessar:
http://localhost:5173/simulator
http://localhost:5173/devices
http://localhost:5173/sites
# etc
```

---

## ✅ Checklist de Verificação

Após iniciar tudo, verifique no console do navegador (F12):

- [ ] **Sem avisos** do React Router v7 (resolvido com as flags)
- [ ] **Sem erros CORS** (verifique se está acessando a rota certa)
- [ ] **Sem "Uncaught (in promise)"** (faça login se necessário)

---

## 📝 Arquivos Modificados

1. ✅ `frontend/src/App.tsx` - Adicionadas flags v7 do React Router
2. ✅ `frontend/.env` - Criado arquivo de configuração com `VITE_API_URL`

---

## 🔄 Próximos Passos

1. **Reinicie o frontend** para aplicar as mudanças do React Router
   ```bash
   cd /home/user/OptiFlow-AI-/frontend
   # Ctrl+C para parar o servidor atual
   npm run dev
   ```

2. **Escolha qual servidor usar** (standalone ou completo)

3. **Acesse a rota correta** no navegador

4. **Verifique o console** (F12) - deve estar limpo agora!

---

## ❓ Ainda tem erros?

**Me diga:**
1. Qual servidor você está usando? (standalone ou completo)
2. Qual URL você está acessando? (copie da barra de endereço)
3. Qual erro aparece no console? (copie e cole aqui)

Vou te ajudar a resolver!
