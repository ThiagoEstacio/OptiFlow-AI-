# 🚀 Guia de Teste Local - OptiFlow AI

## Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Node.js** (v18 ou superior) - [Download](https://nodejs.org/)
- **Python** (v3.11 ou superior) - [Download](https://www.python.org/)
- **Docker Desktop** (opcional, para banco de dados) - [Download](https://www.docker.com/products/docker-desktop/)

---

## 🎯 Opção 1: Frontend Standalone (Mais Rápido)

Esta é a forma mais rápida de testar o Dashboard Builder com a simulação!

### Passo 1: Instalar Dependências do Frontend

```bash
cd frontend
npm install
```

### Passo 2: Iniciar o Frontend

```bash
npm run dev
```

Você verá algo como:
```
VITE v5.0.0  ready in 500 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### Passo 3: Acessar a Aplicação

Abra seu navegador e acesse:

```
http://localhost:5173
```

### Passo 4: Testar o Dashboard Builder com Simulação

1. **Fazer Login** (ou pular se não houver autenticação)

2. **Ir para Dashboard Builder**
   ```
   http://localhost:5173/dashboard-builder
   ```

3. **Abrir Painel de Simulação**
   - Clique no botão laranja **"Simulation"** no header (canto superior direito)
   - Um modal aparecerá

4. **Iniciar Simulação**
   - Clique em **"▶ Start"**
   - Você verá as tags começarem a atualizar em tempo real

5. **Explorar Tags**
   - No painel esquerdo, você verá **80+ tags** organizadas por categoria:
     * Reception (9 tags)
     * Conveyor (9 tags)
     * Elevator (5 tags)
     * Storage (17 tags)
     * Shiploader (10 tags)
     * Quality (5 tags)
     * Utilities (5 tags)
     * Environmental (5 tags)
     * Production (4 tags)

6. **Criar Widgets**
   - Na barra de ferramentas (logo abaixo do header), clique nos ícones para adicionar widgets:
     * 🎯 Gauge
     * 📈 Time Series
     * 🔢 Value
     * 📊 KPI
     * ⚡ Status
     * 📉 Progress
     * ✨ Sparkline

7. **Arrastar Tags para Widgets**
   - Arraste uma tag do painel esquerdo
   - Solte sobre um widget no canvas
   - O widget se conectará automaticamente à tag

8. **Testar Controles da Simulação**
   - **Velocidade**: Ajuste o slider (0.5x a 5.0x)
   - **Ship Loading**: Toggle para ativar/desativar carregamento de navio
   - **Truck Reception**: Toggle para ativar/desativar recepção de caminhões
   - **Alarmes**: Enable/Disable alarmes

9. **Disparar Alarmes de Teste**
   - Clique em **"High Temp"** - dispara alarme de temperatura alta
   - Clique em **"Low Pressure"** - dispara alarme de pressão baixa
   - Clique em **"High Vib"** - dispara alarme de vibração alta
   - Veja os alarmes aparecerem na lista

10. **Observar Correlações**
    - Ative "Ship Loading" e observe:
      * SHIP_LOADER_FLOW_RATE aumenta
      * SHIP_TOTAL_LOADED acumula
      * SHIP_LOADING_PROGRESS aumenta
      * SILO_01_LEVEL diminui
      * UTIL_POWER_CONSUMPTION aumenta

---

## 🎯 Opção 2: Sistema Completo (Backend + Frontend)

Para testar com o backend completo (API, banco de dados, etc.)

### Passo 1: Iniciar Serviços com Docker

```bash
# Na raiz do projeto
docker-compose up -d postgres influxdb redis
```

Isso iniciará:
- PostgreSQL na porta 5432
- InfluxDB na porta 8086
- Redis na porta 6379

### Passo 2: Configurar Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### Passo 3: Configurar Variáveis de Ambiente

Crie um arquivo `.env` na pasta `backend/`:

```bash
cd backend
cp .env.example .env
```

Edite o `.env` se necessário (valores padrão já funcionam para desenvolvimento local)

### Passo 4: Iniciar Backend

```bash
# Dentro da pasta backend com venv ativado
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Você verá:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Passo 5: Verificar API

Abra em seu navegador:

```
http://localhost:8000/docs
```

Você verá o **Swagger UI** com todos os endpoints da API.

### Passo 6: Iniciar Frontend

Em outro terminal:

```bash
cd frontend
npm install  # Se ainda não instalou
npm run dev
```

### Passo 7: Acessar Aplicação Completa

```
http://localhost:5173
```

Agora você tem:
- ✅ Frontend: http://localhost:5173
- ✅ Backend API: http://localhost:8000
- ✅ API Docs: http://localhost:8000/docs
- ✅ Banco PostgreSQL: localhost:5432
- ✅ InfluxDB: http://localhost:8086
- ✅ Redis: localhost:6379

---

## 🧪 Testes Específicos

### Teste 1: Dashboard Builder com Simulação

```bash
# 1. Acesse
http://localhost:5173/dashboard-builder

# 2. Abra Console do Browser (F12)
# 3. Execute no console:
import { tagDataSimulator } from './services/tagDataSimulator';
tagDataSimulator.setSimulationSpeed(2.0);  // 2x speed
```

### Teste 2: AI Chatbot

```bash
# 1. Configure OpenAI API Key (opcional)
# No backend/.env:
OPENAI_API_KEY=sk-sua-chave-aqui

# 2. Acesse
http://localhost:5173/chat

# 3. Faça perguntas:
"Quais dispositivos estão offline?"
"Mostre-me os alarmes ativos"
"Como está a performance do sistema?"
```

### Teste 3: Analytics

```bash
# Acesse
http://localhost:5173/analytics

# Crie queries complexas com o visual query builder
```

### Teste 4: AI Insights

```bash
# Acesse
http://localhost:5173/ai-insights

# Explore insights de ML sobre seus dados
```

---

## 🎨 Cenários de Teste Completos

### Cenário 1: Criar Dashboard de Recepção

1. **Acesse Dashboard Builder**
   ```
   http://localhost:5173/dashboard-builder
   ```

2. **Abra Simulação e Start**

3. **Adicione Widgets:**
   - **Gauge Widget**: Arraste `RCV_HOPPER_01_LEVEL`
   - **Value Widget**: Arraste `RCV_QUEUE_COUNT`
   - **KPI Widget**: Arraste `PROD_TOTAL_RECEIVED_TODAY`
   - **Progress Widget**: Arraste `RCV_HOPPER_01_LEVEL`

4. **Configure Alarmes:**
   - No painel de simulação, clique em "High Temp"
   - Veja o alarme aparecer

5. **Salve o Dashboard:**
   - Clique em "Save" no header
   - Nome: "Reception Overview"

### Cenário 2: Teste de Performance

1. **Inicie Simulação a 5x**

2. **Ative Ship Loading e Truck Reception**

3. **Observe em Tempo Real:**
   - Tags atualizando a cada segundo
   - Correlações funcionando
   - Alarmes sendo disparados

### Cenário 3: Demo para Cliente

1. **Prepare Dashboard com Template:**
   - Clique em "Templates"
   - Selecione template (se houver)

2. **Inicie Simulação Normal (1x)**

3. **Ative Ship Loading:**
   - Observe progresso de 0% a 100%
   - Calado do navio aumentando
   - Silos sendo esvaziados

4. **Dispare Alarme de Demonstração:**
   - High Temperature
   - Mostre como é detectado

---

## 🐛 Troubleshooting

### Problema: Frontend não inicia

```bash
# Limpar cache e reinstalar
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Problema: Porta 5173 em uso

```bash
# Matar processo na porta
# Windows:
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:5173 | xargs kill -9

# Ou use outra porta:
npm run dev -- --port 3000
```

### Problema: Backend não conecta ao banco

```bash
# Verificar se Docker está rodando
docker ps

# Reiniciar containers
docker-compose restart postgres influxdb redis

# Ver logs
docker-compose logs postgres
```

### Problema: Tags não aparecem no Dashboard Builder

1. **Verifique Console do Browser (F12)**
2. **Procure por erros de import**
3. **Recarregue a página (Ctrl+R)**

### Problema: Simulação não atualiza

1. **Abra painel de simulação**
2. **Clique em "▶ Start"**
3. **Verifique se speed > 0**
4. **Veja console para erros**

---

## 📊 Verificação de Funcionamento

### Checklist Frontend:

- [ ] Página inicial carrega sem erros
- [ ] Dashboard Builder acessível
- [ ] Painel de tags mostra 80+ tags
- [ ] Botão "Simulation" aparece no header
- [ ] Modal de simulação abre/fecha
- [ ] Widgets podem ser adicionados
- [ ] Tags podem ser arrastadas
- [ ] Chat acessível em /chat
- [ ] Analytics acessível em /analytics

### Checklist Simulação:

- [ ] Botão Start/Pause funciona
- [ ] Slider de velocidade ajusta
- [ ] Toggle Ship Loading funciona
- [ ] Toggle Truck Reception funciona
- [ ] Botões de teste de alarme funcionam
- [ ] Lista de alarmes atualiza
- [ ] Reset limpa tudo

### Checklist Backend (se rodando):

- [ ] API responde em http://localhost:8000
- [ ] /docs mostra Swagger UI
- [ ] Endpoints de chat listados
- [ ] PostgreSQL conectado
- [ ] InfluxDB conectado
- [ ] Redis conectado

---

## 🎥 Gravação de Demo

Para fazer um vídeo demo:

1. **Preparação:**
   ```bash
   # Terminal 1 (Backend)
   cd backend && uvicorn app.main:app --reload

   # Terminal 2 (Frontend)
   cd frontend && npm run dev
   ```

2. **Roteiro:**
   - Abrir Dashboard Builder
   - Mostrar 80+ tags por categoria
   - Abrir painel de simulação
   - Iniciar simulação
   - Criar 3-4 widgets
   - Arrastar tags
   - Ativar Ship Loading
   - Mostrar correlações funcionando
   - Disparar alarme de teste
   - Ajustar velocidade para 3x
   - Salvar dashboard

3. **Ferramentas de Gravação:**
   - OBS Studio (grátis)
   - Loom
   - QuickTime (Mac)

---

## 📚 URLs Importantes

| Serviço | URL Local |
|---------|-----------|
| Frontend | http://localhost:5173 |
| Dashboard Builder | http://localhost:5173/dashboard-builder |
| AI Chatbot | http://localhost:5173/chat |
| Analytics | http://localhost:5173/analytics |
| AI Insights | http://localhost:5173/ai-insights |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

---

## ✅ Resultado Esperado

Após seguir os passos, você deve ter:

1. ✅ Frontend rodando em http://localhost:5173
2. ✅ 80+ tags visíveis no Dashboard Builder
3. ✅ Painel de simulação funcional
4. ✅ Widgets criáveis e configuráveis
5. ✅ Tags arrastáveis para widgets
6. ✅ Simulação em tempo real
7. ✅ Alarmes funcionando
8. ✅ Correlações visíveis
9. ✅ Dark mode disponível
10. ✅ Todas as páginas acessíveis

**Divirta-se testando!** 🎉
