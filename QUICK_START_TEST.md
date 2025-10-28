# 🚀 Quick Start Testing Guide

Guia rápido para testar a implementação de Analytics em **5-20 minutos** sem precisar de dados reais.

---

## ✅ Passo 1: Validação Completa (FEITO!)

```bash
✓ python test_analytics_validation.py
```

**Resultado**: Todos os arquivos presentes e válidos! ✅

---

## 🔧 Passo 2: Verificar Dependências

### Backend Dependencies:

```bash
cd backend

# Verificar se virtual env existe
ls venv/ 2>/dev/null || echo "Virtual env não encontrado - criando..."

# Se não existir, criar:
python3 -m venv venv
source venv/bin/activate

# Instalar/atualizar dependências
pip install -r requirements.txt

# Voltar ao root
cd ..
```

### Frontend Dependencies:

```bash
cd frontend

# Verificar se node_modules existe
ls node_modules/ 2>/dev/null || echo "node_modules não encontrado - instalando..."

# Instalar dependências
npm install

# Voltar ao root
cd ..
```

---

## 🎯 Passo 3A: Teste RÁPIDO (5 min) - Sem Backend

**O que testar**: Frontend standalone (Showcase Page)

### Iniciar apenas o Frontend:

```bash
cd frontend
npm start
```

**Aguarde**: Compilação completa (~30s)

**Abrir**: http://localhost:3000

### Testes Frontend-Only:

#### 1. Showcase Page (★★★ RECOMENDADO):

```
URL: http://localhost:3000/showcase
(ou navegue para "Visualization Showcase" no menu)
```

**Checklist rápido** (5 min):
- [ ] Página carrega sem erros
- [ ] 12 visualizações renderizam
- [ ] Stats dashboard mostra: 12 componentes, 4 categorias, 40+ use cases
- [ ] Search bar funciona (digite "gauge" ou "map")
- [ ] Category filter funciona (clique em "Basic", "Statistical", etc)
- [ ] Grid/List view toggle funciona
- [ ] Click "Show Code Example" em qualquer viz
- [ ] Visualizações são interativas:
  - [ ] Hover mostra tooltips
  - [ ] Scatter plot tem zoom/pan
  - [ ] Multi-axis chart tem legend toggle
- [ ] Responsive: Redimensione browser window

**Se tudo funciona**: ✅ Frontend está perfeito!

#### 2. Analytics Page (visual apenas):

```
URL: http://localhost:3000/analytics
```

**Checklist visual** (2 min):
- [ ] Página carrega
- [ ] Query Builder aparece
- [ ] TagSelector, TimeRangePicker, FilterBuilder, AggregationBuilder visíveis
- [ ] Mode toggle (Execute Once / Stream Live) funciona
- [ ] JSON Preview funciona
- [ ] UI está bonita e responsiva

**Nota**: Não conseguirá executar queries sem backend, mas pode verificar a UI!

---

## 🎯 Passo 3B: Teste COMPLETO (20 min) - Com Backend

**O que testar**: Sistema completo (Backend + Frontend)

### Pré-requisitos:

**Necessário**:
- PostgreSQL rodando (porta 5432)
- InfluxDB rodando (porta 8086)
- Credenciais configuradas em `backend/.env`

**Como verificar**:
```bash
# PostgreSQL
psql -U postgres -c "SELECT version();"

# InfluxDB
curl http://localhost:8086/health

# Se não estiverem rodando, veja START_SERVICES.md seção "Troubleshooting"
```

### Iniciar Backend:

**Terminal 1**:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Aguarde**:
```
INFO: Application startup complete.
```

**Verificar**: http://localhost:8000/docs (Swagger UI)

### Iniciar Frontend:

**Terminal 2**:
```bash
cd frontend
npm start
```

**Aguarde**:
```
Compiled successfully!
```

**Abrir**: http://localhost:3000

### Testar Endpoints Backend:

**Terminal 3**:
```bash
python test_analytics_endpoints.py
```

**Esperado**: 6/6 testes passam ✅

### Testar Query Builder:

1. **Login** em http://localhost:3000
2. **Navegue** para Analytics page
3. **Execute Once Mode**:
   - Selecione 1-2 tags (se houver dados)
   - Escolha "Last 24 Hours"
   - Adicione aggregation "mean"
   - Click "Execute Query"
   - Verifique resultados

4. **Stream Live Mode**:
   - Toggle para "Stream Live"
   - Set refresh interval: 5s
   - Click "Start Stream"
   - Verifique: Connected, streaming, sequence incrementa
   - Click "Pause" → "Resume" → "Stop"

### Testar Visualizações:

- Após executar query, verifique que visualization auto-seleciona
- Tente mudar tipo de visualization
- Hover para ver tooltips
- Export CSV

---

## 📋 Resultados Esperados:

### ✅ Teste RÁPIDO (Frontend-only):

| Item | Status |
|------|--------|
| Showcase page loads | ✓ |
| 12 visualizations render | ✓ |
| Search works | ✓ |
| Filter works | ✓ |
| Code examples show | ✓ |
| Interactions work | ✓ |
| Responsive | ✓ |

**Tempo**: 5 minutos
**Conclusão**: Frontend está production-ready! 🎉

---

### ✅ Teste COMPLETO (Full stack):

| Item | Status |
|------|--------|
| Backend starts | ✓ |
| Frontend starts | ✓ |
| API tests pass (6/6) | ✓ |
| Query Builder UI | ✓ |
| Execute Once mode | ✓ |
| Stream Live mode | ✓ |
| Visualizations render | ✓ |
| Export CSV works | ✓ |

**Tempo**: 20 minutos
**Conclusão**: Sistema completo está production-ready! 🎉🎉

---

## 🐛 Troubleshooting Rápido:

### Frontend não compila:

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

### Backend não inicia:

```bash
# Verificar .env
cat backend/.env

# Verificar InfluxDB
curl http://localhost:8086/health

# Verificar PostgreSQL
psql -U postgres -c "SELECT 1"

# Ver logs de erro
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Porta 3000 ou 8000 em uso:

```bash
# Matar processo na porta
lsof -ti:3000 | xargs kill -9  # Frontend
lsof -ti:8000 | xargs kill -9  # Backend

# Ou usar portas diferentes
PORT=3001 npm start  # Frontend
uvicorn app.main:app --port 8001  # Backend
```

### Browser não abre automaticamente:

Abrir manualmente:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Showcase: http://localhost:3000/showcase

---

## 📸 Screenshots para Demo:

Tire screenshots de:

1. **Showcase Grid View** - Todas as 12 visualizações
2. **Individual Visualization** - Gauge chart com thresholds
3. **Code Example** - Show code toggle aberto
4. **Search Demo** - Filtrado por "statistical"
5. **Query Builder** - Interface completa
6. **Stream Controls** - Streaming ativo com sequence
7. **Results** - Visualization com dados
8. **Multi-axis Chart** - 3 séries diferentes

---

## ✅ Checklist Final:

### Mínimo (5 min - Frontend only):
- [ ] npm install completo
- [ ] npm start funciona
- [ ] Showcase page carrega
- [ ] 12 visualizações renderizam
- [ ] Interações funcionam

### Completo (20 min - Full stack):
- [ ] Backend dependencies instaladas
- [ ] InfluxDB + PostgreSQL rodando
- [ ] Backend inicia sem erros
- [ ] Frontend inicia sem erros
- [ ] test_analytics_endpoints.py passa (6/6)
- [ ] Query Builder visual funciona
- [ ] Execute Once funciona (se houver dados)
- [ ] Stream Live funciona
- [ ] Visualizações renderizam corretamente
- [ ] Sem erros no console

---

## 🎯 Próximo Passo:

**Se testes passarem**:
→ Você tem um sistema de Analytics de classe mundial! 🏆
→ Pronto para demos, UAT, beta, ou produção
→ Próximo: Fase 2 (Dashboard Builder) ou ML features

**Se houver issues**:
→ Verifique TESTING_CHECKLIST.md para testes detalhados
→ Consulte START_SERVICES.md para troubleshooting
→ Revise console errors no browser (F12)

---

## 📞 Comandos Úteis:

```bash
# Status rápido
python test_analytics_validation.py

# Testar API
python test_analytics_endpoints.py

# Ver processos rodando
ps aux | grep -E "(uvicorn|npm)"

# Ver portas em uso
netstat -tuln | grep -E ":(3000|8000)"

# Logs backend em tempo real
cd backend && tail -f logs/app.log

# Reconstruir tudo do zero
cd frontend && rm -rf node_modules && npm install
cd backend && rm -rf venv && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

---

## 🎉 Sucesso!

Se chegou aqui com tudo funcionando:

**PARABÉNS! 🏆**

Você construiu e validou:
- ✅ ~8,650 linhas de código
- ✅ 35 arquivos novos
- ✅ 12 visualizações interativas
- ✅ Query Builder completo
- ✅ WebSocket streaming
- ✅ Suite de validação
- ✅ Showcase page

**SmartPort Analytics está PRONTO! 🚀**

---

**Dúvidas?** Consulte:
- START_SERVICES.md - Guia completo de inicialização
- TESTING_CHECKLIST.md - 300+ testes detalhados
- VALIDATION_GUIDE.md - Guia mestre
- VISUALIZATION_SHOWCASE.md - Guia do showcase
