# 🚀 OptiFlow AI - Início Rápido

**Status**: 🟢 **TOTALMENTE OPERACIONAL**

---

## ⚡ TL;DR - Início Super Rápido

```bash
# 1. Iniciar tudo de uma vez
./start-all.sh

# 2. Acessar
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000/docs

# 3. Parar tudo
./stop-all.sh
```

---

## 📋 Pré-requisitos

### Serviços Necessários

Certifique-se de que estes serviços estão rodando:

```bash
# PostgreSQL
sudo systemctl start postgresql
sudo systemctl status postgresql

# Redis
sudo systemctl start redis
sudo systemctl status redis

# InfluxDB (opcional)
sudo systemctl start influxdb
sudo systemctl status influxdb

# RabbitMQ (opcional)
sudo systemctl start rabbitmq-server
sudo systemctl status rabbitmq-server
```

---

## 🎯 Opções de Inicialização

### Opção 1: Tudo de Uma Vez (Recomendado)

```bash
cd /home/thiestacio/OptiFlow-AI-
./start-all.sh
```

**O que faz**:
- ✅ Verifica serviços (PostgreSQL, Redis, InfluxDB)
- ✅ Ativa ambiente conda
- ✅ Inicia backend em background
- ✅ Inicia frontend em background
- ✅ Mostra URLs de acesso
- ✅ Salva logs em `logs/`

**Para parar**:
```bash
./stop-all.sh
```

---

### Opção 2: Separado (2 Terminais)

**Terminal 1 - Backend**:
```bash
conda activate optiflow
cd backend
./run.sh
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

---

### Opção 3: Manual Completo

**Backend**:
```bash
conda activate optiflow
cd /home/thiestacio/OptiFlow-AI-/backend
python app/main.py
```

**Frontend**:
```bash
cd /home/thiestacio/OptiFlow-AI-/frontend
npm run dev
```

---

## 🌐 URLs de Acesso

### 🎨 Frontend
- **Local**: http://localhost:3000
- **Rede**: http://192.168.1.10:3000

### 🔧 Backend
- **API Base**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 📊 Status Atual

### ✅ Backend
```
✅ Python 3.11.14
✅ FastAPI 0.104.1
✅ 50+ dependências instaladas
✅ 171 testes disponíveis
✅ Zero erros de importação
✅ Database: PostgreSQL + AsyncPG
✅ Time Series: InfluxDB
✅ Cache: Redis
✅ Queue: Celery + RabbitMQ
```

### ✅ Frontend
```
✅ React 18.2
✅ TypeScript 5.0
✅ Vite 5.4.21
✅ Material-UI v7.3.4
✅ Dev server rodando
✅ Hot reload funcionando
⚠️ 216 avisos TypeScript (não bloqueiam)
```

---

## 🛠️ Comandos Úteis

### Backend

```bash
# Ativar ambiente
conda activate optiflow

# Verificar imports
cd backend
python -c "from app.main import app; print('✅ OK')"

# Rodar testes
pytest

# Rodar com coverage
pytest --cov=app --cov-report=html

# Verificar tipos
mypy app/

# Formatar código
black app/
isort app/
```

### Frontend

```bash
cd frontend

# Dev server
npm run dev

# Build de produção
npm run build

# Preview do build
npm run preview

# Testes
npm run test

# Type check
npm run type-check

# Lint
npm run lint
npm run lint:fix

# Format
npm run format
```

---

## 📂 Estrutura do Projeto

```
OptiFlow-AI-/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # REST endpoints
│   │   ├── core/        # Config, deps, security
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   └── main.py      # App entry point
│   ├── tests/           # Pytest tests
│   ├── requirements.txt
│   └── run.sh           # Startup script
│
├── frontend/            # React frontend
│   ├── src/
│   │   ├── api/        # API clients
│   │   ├── components/ # React components
│   │   ├── pages/      # Page components
│   │   ├── services/   # API services
│   │   ├── store/      # Redux store
│   │   └── App.tsx
│   └── package.json
│
├── start-all.sh        # Inicia backend + frontend
├── stop-all.sh         # Para backend + frontend
├── logs/               # Logs da aplicação
│
└── Documentação:
    ├── README.md
    ├── README_INICIO_RAPIDO.md (este arquivo)
    ├── CORREÇÕES_REALIZADAS.md
    ├── STATUS_CORRECOES.md
    └── frontend/STATUS_FRONTEND.md
```

---

## 🔍 Verificação de Saúde

### Backend Health Check

```bash
curl http://localhost:8000/health
```

**Resposta esperada**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

### Frontend Check

```bash
curl http://localhost:3000
```

**Deve retornar**: HTML da aplicação React

---

## 🎓 Primeiros Passos

### 1. Acessar a Aplicação

1. Abra http://localhost:3000
2. Você verá a tela de login
3. Use credenciais padrão (se configuradas) ou crie um usuário

### 2. Explorar API

1. Abra http://localhost:8000/docs
2. Explore os endpoints disponíveis
3. Teste chamadas diretamente no Swagger

### 3. Dashboard Builder

1. Acesse Dashboard Builder
2. Use IA para criar dashboards automaticamente
3. Customize widgets e visualizações

### 4. Análise de Dados

1. Importe dados (Excel/CSV)
2. Configure tags e dispositivos
3. Visualize em tempo real

---

## 📊 Principais Funcionalidades

### 🎯 Dashboards
- Executive Dashboard
- Asset Health Dashboard
- Analytics Hub
- GBM Insights
- Historical Trends
- Real-time Monitor

### 🤖 IA e ML
- Dashboard Builder com IA
- Manutenção Preditiva
- Detecção de Anomalias
- Análise de Falhas
- ROI Calculator
- Insights Automáticos

### 📈 Analytics
- Time Series Analysis
- Pareto Analysis
- Trend Detection
- Month-over-Month Comparisons
- Custom Query Builder

### 🔧 Configuração
- Device Management (OPC UA, Modbus, MQTT, S7)
- Tag Configuration
- Alarm Management
- User Administration

---

## 🐛 Troubleshooting

### Backend não inicia

```bash
# Verificar ambiente
conda env list
conda activate optiflow

# Verificar imports
cd backend
python -c "from app.main import app"

# Verificar banco de dados
psql -U optiflow -d optiflow -h localhost
```

### Frontend não carrega

```bash
# Reinstalar dependências
cd frontend
rm -rf node_modules package-lock.json
npm install

# Limpar cache
rm -rf node_modules/.vite
npm run dev
```

### Porta já em uso

```bash
# Backend (porta 8000)
lsof -i :8000
kill -9 <PID>

# Frontend (porta 3000)
lsof -i :3000
kill -9 <PID>
```

### Database connection failed

```bash
# Verificar PostgreSQL
sudo systemctl status postgresql
sudo systemctl start postgresql

# Testar conexão
psql -U optiflow -h localhost -d optiflow
```

### Redis connection failed

```bash
# Verificar Redis
sudo systemctl status redis
sudo systemctl start redis

# Testar conexão
redis-cli ping
```

---

## 📝 Logs

### Ver logs em tempo real

```bash
# Backend
tail -f logs/backend.log

# Frontend
tail -f logs/frontend.log

# Ambos
tail -f logs/*.log
```

### Limpar logs

```bash
rm logs/*.log
```

---

## 🔐 Segurança

### ⚠️ IMPORTANTE para Produção

1. **Rotacionar chaves**:
   - OpenAI API Key em `backend/.env`
   - JWT Secret Key
   - Database passwords

2. **Configurar CORS**:
   ```python
   # backend/app/main.py
   CORS_ORIGINS = ["https://seu-dominio.com"]
   ```

3. **HTTPS**:
   - Configurar certificados SSL
   - Reverse proxy (Nginx/Caddy)

4. **Environment Variables**:
   ```bash
   export OPENAI_API_KEY="..."
   export DATABASE_URL="..."
   ```

---

## 📚 Documentação Completa

- **README.md**: Visão geral do projeto
- **CORREÇÕES_REALIZADAS.md**: Detalhes de todas correções
- **STATUS_CORRECOES.md**: Status do backend
- **frontend/STATUS_FRONTEND.md**: Status do frontend
- **Backend API Docs**: http://localhost:8000/docs

---

## 🆘 Suporte

### Problemas Comuns

1. **"ModuleNotFoundError"** → Ativar ambiente: `conda activate optiflow`
2. **"Port already in use"** → Matar processo ou usar outra porta
3. **"Database connection failed"** → Iniciar PostgreSQL
4. **TypeScript errors** → Ignorar (não bloqueiam frontend)

### Comandos de Diagnóstico

```bash
# Verificar tudo
./start-all.sh  # Já faz verificações

# Backend
conda activate optiflow
cd backend
python -c "from app.main import app; print('✅')"

# Frontend
cd frontend
npm run type-check
npm run dev
```

---

## 🎉 Resumo

### ✅ O que está funcionando

```
✅ Backend: Totalmente operacional
✅ Frontend: Rodando perfeitamente
✅ Database: PostgreSQL configurado
✅ Time Series: InfluxDB integrado
✅ Cache: Redis configurado
✅ API: 171 testes disponíveis
✅ UI: 15+ páginas funcionais
✅ Charts: Recharts, D3, Plotly
✅ Forms: React Hook Form + Validation
✅ State: Redux Toolkit
✅ Real-time: WebSocket
✅ AI: OpenAI integration
```

### 🚀 Pronto para

- ✅ Desenvolvimento
- ✅ Testes
- ✅ Demonstrações
- ✅ Staging
- ⚠️ Produção (após ajustes de segurança)

---

## 🎯 Quick Commands

```bash
# Iniciar
./start-all.sh

# Parar
./stop-all.sh

# Logs
tail -f logs/*.log

# Status
curl http://localhost:8000/health
curl http://localhost:3000
```

---

**🟢 Aplicação 100% operacional e pronta para uso!**

**Data**: 03 de Novembro de 2025
**Ambiente**: Development
**Status**: Ready 🚀
