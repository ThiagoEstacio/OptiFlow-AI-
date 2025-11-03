# 🧪 OptiFlow AI - Guia de Testes Manuais Completo

**Branch**: `claude/fix-autonomous-agent-sessions-011CUm8WUduocmLfq3bJpCxf`
**Data**: 03 de Novembro de 2025
**Versão**: 1.0

---

## 📋 Índice

1. [Preparação do Ambiente](#preparação-do-ambiente)
2. [Testes de Autonomous Agent](#testes-de-autonomous-agent)
3. [Testes de AI Assistant](#testes-de-ai-assistant)
4. [Testes de Dashboard Builder](#testes-de-dashboard-builder)
5. [Testes de Machine Learning](#testes-de-machine-learning)
6. [Testes de Múltiplos Dashboards](#testes-de-múltiplos-dashboards)
7. [Testes de Analytics](#testes-de-analytics)
8. [Checklist Final](#checklist-final)

---

## 🔧 Preparação do Ambiente

### 1.1 Iniciar Sistema

```bash
# Certificar-se de estar na branch correta
git checkout claude/fix-autonomous-agent-sessions-011CUm8WUduocmLfq3bJpCxf

# Iniciar todos os serviços
docker compose up -d

# Aguardar serviços estarem prontos (30-60 segundos)
docker compose ps

# Verificar logs
docker compose logs -f backend | grep "🤖\|✅"
```

### 1.2 Verificação de Saúde

**URL**: http://localhost:8000/health

**Verificar**:
- ✅ `status: "healthy"`
- ✅ `database: "connected"`
- ✅ `influxdb: "connected"`

**Screenshot**: Salvar para documentação

---

## 🤖 Testes de Autonomous Agent

### 2.1 Verificar Inicialização do Agent

**Logs esperados**:
```
🤖 Autonomous AI Agent initialized and started successfully
✅ Monitoring cycle complete. Total insights: X
```

**Como verificar**:
```bash
docker compose logs backend | grep -i "autonomous\|agent\|🤖"
```

**Resultado esperado**:
- ✅ Agent iniciado sem erros
- ✅ Ciclos de monitoramento executando a cada 60 segundos
- ✅ Nenhum erro de `greenlet_spawn` ou `coroutine`

---

### 2.2 Testar Endpoint de Insights

**URL**: http://localhost:8000/api/v1/agent/insights

**Teste 1: Listar Todos os Insights**
```bash
curl http://localhost:8000/api/v1/agent/insights?limit=20 | jq .
```

**Verificar**:
- ✅ Retorna array de insights
- ✅ Cada insight tem: `id`, `title`, `description`, `category`, `severity`, `timestamp`
- ✅ Categorias válidas: `anomaly`, `optimization`, `alert`, `prediction`, `trend`

**Teste 2: Filtrar por Categoria**
```bash
curl "http://localhost:8000/api/v1/agent/insights?category=anomaly&limit=10" | jq .
```

**Teste 3: Filtrar por Severidade**
```bash
curl "http://localhost:8000/api/v1/agent/insights?severity=high&limit=10" | jq .
```

---

### 2.3 Testar Dashboard Summary

**URL**: http://localhost:8000/api/v1/agent/dashboard-summary

```bash
curl http://localhost:8000/api/v1/agent/dashboard-summary | jq .
```

**Verificar**:
```json
{
  "total_insights": 50,
  "by_category": {
    "anomaly": 15,
    "optimization": 10,
    "alert": 12,
    "prediction": 8,
    "trend": 5
  },
  "by_severity": {
    "critical": 2,
    "high": 8,
    "medium": 20,
    "low": 15,
    "info": 5
  },
  "latest_insight": { ... },
  "monitoring_active": true,
  "monitoring_interval": 60
}
```

---

### 2.4 Verificar Estratégias de Monitoramento

**As 5 estratégias devem executar**:

1. ✅ **Detect Anomalies**: Detecta anomalias em tags críticas
2. ✅ **Analyze Performance**: Analisa performance de equipamentos
3. ✅ **Check Alarm Conditions**: Verifica padrões de alarmes
4. ✅ **Identify Optimization Opportunities**: Identifica oportunidades de otimização
5. ✅ **Predict Future States**: Predição de estados futuros

**Verificar nos logs**:
```bash
docker compose logs backend | grep -E "detect_anomalies|analyze_performance|check_alarm|identify_optimization|predict_future"
```

---

## 💬 Testes de AI Assistant (Chatbot)

### 3.1 Query Simples

**URL**: http://localhost:8000/api/v1/chat/message

**Teste**:
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, what can you help me with?"
  }' | jq .
```

**Verificar**:
- ✅ Resposta em português ou inglês (dependendo da query)
- ✅ Resposta relevante e contextual
- ✅ Sem erros

---

### 3.2 Buscar Tags

**Teste**:
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Find all conveyor belt speed tags"
  }' | jq .
```

**Verificar**:
- ✅ Retorna lista de tags relacionadas a correias
- ✅ Tool calling funcionou (search_tags foi chamado)

---

### 3.3 Query Analítica Complexa

**Teste**:
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Calculate the average speed of CORREIA_01_VELOCIDADE over the last 24 hours and tell me if there are any anomalies"
  }' | jq .
```

**Verificar**:
- ✅ Cálculo de estatísticas (média, desvio padrão)
- ✅ Detecção de anomalias
- ✅ Resposta estruturada e clara

---

### 3.4 Obter Valor Real-Time

**Teste**:
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the current value of CORREIA_01_VELOCIDADE?"
  }' | jq .
```

**Verificar**:
- ✅ Retorna valor atual
- ✅ Timestamp recente
- ✅ Qualidade do dado (good/bad)

---

### 3.5 Comparação de Tags

**Teste**:
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Compare the performance of CORREIA_01_VELOCIDADE and CORREIA_02_VELOCIDADE over the last week"
  }' | jq .
```

**Verificar**:
- ✅ Comparação estatística
- ✅ Correlação (se aplicável)
- ✅ Insights sobre diferenças

---

## 📊 Testes de Dashboard Builder

### 4.1 Criar Dashboard com AI Assistant

**Interface**: http://localhost:3000/dashboard-builder

**Passos**:

1. **Abrir AI Assistant Panel**
   - Clicar no ícone ✨ (Sparkles) no canto superior direito
   - ✅ Panel do AI Assistant abre

2. **Request Dashboard Creation**
   - Digitar: `"Create a dashboard to monitor conveyor belt performance"`
   - Clicar em Send
   - ✅ AI responde com sugestões

3. **Verificar Widgets Sugeridos**
   - ✅ AI sugere widgets apropriados (gauge, timeseries, kpi)
   - ✅ Tags corretas são associadas
   - ✅ Configurações fazem sentido (min, max, units)

4. **Aplicar Sugestões**
   - Clicar em "Add Widgets" (se disponível)
   - ✅ Widgets aparecem no canvas
   - ✅ Dados começam a carregar

---

### 4.2 Adicionar Widget Manualmente

**Passos**:

1. **Arrastar Tag para Canvas**
   - Do painel esquerdo (Tags Panel)
   - Arrastar tag `CORREIA_01_VELOCIDADE`
   - Soltar no canvas
   - ✅ Widget criado automaticamente

2. **Configurar Widget**
   - Clicar no widget
   - Abrir Property Panel (direita)
   - Alterar:
     - Título: "Conveyor 01 Speed"
     - Min: 0
     - Max: 1500
     - Cor: #3b82f6
   - ✅ Mudanças aplicadas em tempo real

3. **Mudar Tipo de Widget**
   - Property Panel → Widget Type
   - Selecionar diferentes tipos:
     - Gauge → ✅ Aparece como gauge
     - Timeseries → ✅ Mostra gráfico de tendência
     - Value → ✅ Mostra valor numérico
     - KPI → ✅ Mostra KPI com tendência

---

### 4.3 Usar Templates Pré-configurados

**Passos**:

1. **Abrir Template Selector**
   - Clicar no ícone 📁 (Template)
   - ✅ Modal com templates abre

2. **Selecionar Template**
   - Escolher: "Port Grain Terminal Overview"
   - Clicar em "Load Template"
   - ✅ Dashboard completo carrega

3. **Verificar Conteúdo**
   - ✅ Múltiplos widgets criados
   - ✅ Layout organizado
   - ✅ Tags conectadas corretamente

---

### 4.4 Salvar e Carregar Dashboard

**Passos**:

1. **Salvar Dashboard**
   - Clicar em 💾 (Save)
   - Nome: "My Production Dashboard"
   - ✅ Dashboard salvo no localStorage

2. **Criar Novo Dashboard**
   - Limpar canvas
   - Criar widgets diferentes

3. **Carregar Dashboard Anterior**
   - Clicar em 📂 (Open/Manager)
   - Selecionar "My Production Dashboard"
   - Clicar em "Load"
   - ✅ Dashboard anterior restaurado

---

## 🧠 Testes de Machine Learning

### 5.1 Anomaly Detection

**Endpoint**: `/api/v1/ai-insights/detect-anomalies`

**Teste**:
```bash
curl -X POST http://localhost:8000/api/v1/ai-insights/detect-anomalies \
  -H "Content-Type: application/json" \
  -d '{
    "tag_id": "CORREIA_01_VELOCIDADE",
    "duration": "24h",
    "sensitivity": "medium"
  }' | jq .
```

**Verificar Resposta**:
```json
{
  "tag_id": "CORREIA_01_VELOCIDADE",
  "duration": "24h",
  "anomalies": [
    {
      "timestamp": "2024-11-03T10:30:00Z",
      "value": 1450.5,
      "anomaly_score": 0.85,
      "severity": "high",
      "z_score": 3.2
    }
  ],
  "anomaly_count": 5,
  "severity_distribution": {
    "critical": 1,
    "high": 2,
    "medium": 2
  },
  "statistics": {
    "mean": 1200,
    "stddev": 75
  }
}
```

---

### 5.2 Time Series Forecasting

**Endpoint**: `/api/v1/ai-insights/forecast`

**Teste 1: ARIMA**
```bash
curl -X POST http://localhost:8000/api/v1/ai-insights/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "tag_id": "SILO_01_NIVEL",
    "horizon": "24h",
    "model": "arima",
    "confidence_interval": 0.95
  }' | jq .
```

**Teste 2: Exponential Smoothing**
```bash
curl -X POST http://localhost:8000/api/v1/ai-insights/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "tag_id": "SILO_01_NIVEL",
    "horizon": "24h",
    "model": "exponential_smoothing"
  }' | jq .
```

**Verificar**:
- ✅ Previsões geradas para próximas 24h
- ✅ Intervalos de confiança (upper, lower bounds)
- ✅ Métricas de qualidade (MAE, RMSE, R²)

---

### 5.3 Pattern Recognition

**Endpoint**: `/api/v1/ai-insights/find-patterns`

**Teste**:
```bash
curl -X POST http://localhost:8000/api/v1/ai-insights/find-patterns \
  -H "Content-Type: application/json" \
  -d '{
    "tag_ids": ["CORREIA_01_VELOCIDADE", "CORREIA_01_CORRENTE"],
    "duration": "7d",
    "pattern_type": "correlation"
  }' | jq .
```

**Verificar**:
- ✅ Correlation coefficient calculado
- ✅ Padrões identificados
- ✅ Insights sobre relacionamentos

---

### 5.4 Predictive Maintenance

**Endpoint**: `/api/v1/ai-insights/maintenance-score`

**Teste**:
```bash
curl -X POST http://localhost:8000/api/v1/ai-insights/maintenance-score \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": "CORREIA_01",
    "features": ["velocidade", "corrente", "temperatura", "vibracao"],
    "duration": "30d"
  }' | jq .
```

**Verificar Resposta**:
```json
{
  "equipment_id": "CORREIA_01",
  "health_score": 78.5,
  "risk_level": "medium",
  "predicted_issues": [
    "Belt tension degradation expected in 14 days",
    "Motor bearing wear detected - inspect in 7 days"
  ],
  "recommendations": [
    "Schedule preventive maintenance",
    "Monitor vibration closely",
    "Check belt alignment"
  ],
  "feature_importance": {
    "temperatura": 0.35,
    "vibracao": 0.30,
    "corrente": 0.20,
    "velocidade": 0.15
  }
}
```

---

## 📈 Testes de Múltiplos Dashboards

### 6.1 Criar Dashboard 1: Production Overview

**Passos**:
1. Abrir Dashboard Builder
2. Nome: "Production Overview"
3. Adicionar widgets:
   - Throughput gauge
   - Speed trends (3x conveyors)
   - Status indicators
   - Alarm count
4. Salvar

---

### 6.2 Criar Dashboard 2: Quality Monitoring

**Passos**:
1. Novo dashboard
2. Nome: "Quality Monitoring"
3. Adicionar widgets:
   - Temperature heatmap
   - Moisture levels
   - Contamination alerts
   - Quality KPIs
4. Salvar

---

### 6.3 Criar Dashboard 3: Energy Management

**Passos**:
1. Novo dashboard
2. Nome: "Energy Management"
3. Adicionar widgets:
   - Power consumption trends
   - Energy efficiency KPIs
   - Cost analysis
   - Peak demand alerts
4. Salvar

---

### 6.4 Organizar Dashboards

**Teste Dashboard Manager**:

1. **Abrir Dashboard Manager**
   - Clicar no ícone 📂
   - ✅ Lista de dashboards aparece

2. **Verificar Dashboards Salvos**
   - ✅ "Production Overview" está na lista
   - ✅ "Quality Monitoring" está na lista
   - ✅ "Energy Management" está na lista

3. **Alternar Entre Dashboards**
   - Clicar em "Production Overview" → Load
   - ✅ Dashboard carrega corretamente
   - Clicar em "Quality Monitoring" → Load
   - ✅ Dashboard diferente carrega

4. **Exportar Dashboard**
   - Selecionar dashboard
   - Clicar em "Export" (📥)
   - ✅ Arquivo JSON é baixado

5. **Importar Dashboard**
   - Clicar em "Import" (📤)
   - Selecionar arquivo JSON
   - ✅ Dashboard é restaurado

6. **Deletar Dashboard**
   - Selecionar dashboard de teste
   - Clicar em "Delete" (🗑️)
   - Confirmar
   - ✅ Dashboard removido da lista

---

## 📊 Testes de Analytics

### 7.1 Estatísticas Básicas

**Endpoint**: `/api/v1/analytics/calculate`

**Teste**:
```bash
curl -X POST http://localhost:8000/api/v1/analytics/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "tag_id": "CORREIA_01_VELOCIDADE",
    "duration": "24h",
    "metrics": ["mean", "min", "max", "stddev", "p95", "p99"]
  }' | jq .
```

**Verificar**:
- ✅ Todas as métricas calculadas
- ✅ Valores fazem sentido
- ✅ Timestamp range correto

---

### 7.2 Agregações por Tempo

**Endpoint**: `/api/v1/analytics/aggregate`

**Teste**:
```bash
curl -X POST http://localhost:8000/api/v1/analytics/aggregate \
  -H "Content-Type: application/json" \
  -d '{
    "tag_id": "CORREIA_01_VELOCIDADE",
    "start_time": "2024-11-02T00:00:00Z",
    "end_time": "2024-11-03T00:00:00Z",
    "interval": "1h",
    "aggregation": "mean"
  }' | jq .
```

**Verificar**:
- ✅ 24 pontos de dados (1 por hora)
- ✅ Agregação correta aplicada

---

### 7.3 Comparação Multi-Tag

**Endpoint**: `/api/v1/analytics/compare`

**Teste**:
```bash
curl -X POST http://localhost:8000/api/v1/analytics/compare \
  -H "Content-Type: application/json" \
  -d '{
    "tag_ids": [
      "CORREIA_01_VELOCIDADE",
      "CORREIA_02_VELOCIDADE",
      "CORREIA_03_VELOCIDADE"
    ],
    "duration": "24h",
    "metrics": ["mean", "correlation"]
  }' | jq .
```

**Verificar**:
- ✅ Estatísticas para cada tag
- ✅ Matriz de correlação
- ✅ Insights sobre diferenças

---

### 7.4 OEE Calculation

**Endpoint**: `/api/v1/analytics/oee`

**Teste**:
```bash
curl -X POST http://localhost:8000/api/v1/analytics/oee \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": "CORREIA_01",
    "duration": "24h",
    "tags": {
      "status": "CORREIA_01_STATUS",
      "speed_actual": "CORREIA_01_VELOCIDADE",
      "speed_design": 1200,
      "production": "CORREIA_01_THROUGHPUT"
    }
  }' | jq .
```

**Verificar Resposta**:
```json
{
  "equipment_id": "CORREIA_01",
  "duration": "24h",
  "oee": 72.5,
  "availability": 85.0,
  "performance": 90.0,
  "quality": 95.0,
  "classification": "Good",
  "target_oee": 85.0,
  "gap_to_target": 12.5
}
```

---

## ✅ Checklist Final

### Sistema
- [ ] Backend API respondendo em http://localhost:8000
- [ ] Frontend respondendo em http://localhost:3000
- [ ] InfluxDB conectado e operacional
- [ ] PostgreSQL conectado e operacional
- [ ] Redis (se aplicável) conectado

### Autonomous Agent
- [ ] Agent inicializado sem erros
- [ ] Ciclos de monitoramento executando
- [ ] Insights sendo gerados
- [ ] 5 estratégias funcionando
- [ ] Dashboard summary disponível
- [ ] Filtragem por categoria/severity funciona

### AI Assistant
- [ ] Responde a queries simples
- [ ] Busca de tags funciona
- [ ] Tool calling operacional
- [ ] Queries analíticas complexas funcionam
- [ ] Valores real-time retornados corretamente

### Dashboard Builder
- [ ] Interface carrega sem erros
- [ ] AI Assistant Panel funciona
- [ ] Criação de dashboard via AI
- [ ] Drag & drop de tags
- [ ] Property Panel configurável
- [ ] Templates carregam
- [ ] Save/Load funciona

### Múltiplos Dashboards
- [ ] Criação de 3+ dashboards
- [ ] Dashboard Manager lista corretamente
- [ ] Alternância entre dashboards
- [ ] Export/Import funciona
- [ ] Delete funciona

### Machine Learning
- [ ] Anomaly Detection funciona
- [ ] Forecasting (ARIMA) funciona
- [ ] Pattern Recognition funciona
- [ ] Predictive Maintenance Score calculado
- [ ] Métricas de qualidade presentes

### Analytics
- [ ] Estatísticas básicas calculadas
- [ ] Agregações por tempo funcionam
- [ ] Comparação multi-tag funciona
- [ ] OEE calculado corretamente

---

## 📸 Screenshots Recomendados

Capturar para documentação:

1. **Dashboard Builder Interface**
   - Canvas vazio
   - Canvas com widgets
   - AI Assistant Panel aberto
   - Property Panel configurando widget

2. **Autonomous Agent**
   - Dashboard summary JSON
   - Lista de insights
   - Logs mostrando monitoramento

3. **AI Assistant**
   - Conversação com query complexa
   - Tool calling em ação
   - Resposta com dados

4. **Multiple Dashboards**
   - Dashboard Manager com lista
   - 3 dashboards diferentes lado a lado
   - Export/Import em ação

5. **Machine Learning**
   - Anomaly detection results
   - Forecast chart
   - Predictive maintenance score

---

## 🎯 Critérios de Sucesso

**Todos os testes devem passar com**:
- ✅ Taxa de sucesso > 90%
- ✅ Nenhum erro crítico
- ✅ Tempo de resposta < 2s para queries simples
- ✅ Interface responsiva e sem bugs visuais

---

**🎉 Se todos os checkboxes estiverem marcados: PLATAFORMA PRONTA PARA PRODUÇÃO!**
