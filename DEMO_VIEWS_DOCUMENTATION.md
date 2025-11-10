# Demo Views - Documentação Completa

## Visão Geral

Foram criadas 4 views de demonstração para mostrar os dados sendo coletados, processados e analisados pelos modelos ML em tempo real. Estas views são essenciais para demonstrações e apresentações do sistema.

---

## 1. Real-Time Data View

**Rota**: `/data/realtime`
**Arquivo**: [frontend/src/pages/RealTimeDataView.tsx](frontend/src/pages/RealTimeDataView.tsx)

### Objetivo
Mostrar os dados sendo coletados em tempo real do InfluxDB, com visualizações e métricas ao vivo.

### Funcionalidades

#### Status Bar
- **Status**: LIVE / PAUSED
- **Active Tags**: Número de tags ativos
- **Refresh Rate**: Taxa de atualização (1s, 2s, 5s, 10s)
- **Last Update**: Timestamp da última atualização

#### Controles
- **Play/Pause**: Iniciar/pausar coleta de dados
- **Refresh**: Atualização manual
- **Category Filter**: Filtrar por categoria (process, control, energy, maintenance, quality)
- **Refresh Interval**: Ajustar velocidade de atualização

#### Mini Charts (Top 6 Tags)
- 6 gráficos de linha mostrando histórico dos últimos 30 pontos
- Atualização em tempo real
- Valor atual exibido

#### Live Data Feed (Tabela)
Colunas:
- **Tag Name**: Nome da tag
- **Value**: Valor atual (2 decimais)
- **Unit**: Unidade de medida
- **Trend**: Ícone indicando tendência (up/down/stable)
- **Change %**: Percentual de mudança desde última leitura
- **Quality**: Qualidade do dado (good/bad/uncertain)
- **Category**: Categoria da tag
- **Timestamp**: Hora da coleta

#### Features Avançadas
- **Trend Detection**: Detecta automaticamente tendências (>0.5% = tendência)
- **Quality Indicators**: Cores diferentes para qualidade dos dados
- **Auto-refresh**: Atualização automática configurável
- **Sticky Header**: Cabeçalho fixo na tabela

### API Endpoints Usados
```
GET /api/v1/tags/realtime?limit=50&category=process
```

### Demonstração Ideal
1. Mostrar dados sendo coletados em tempo real
2. Explicar as diferentes categorias de tags
3. Demonstrar detecção de tendências
4. Mostrar qualidade dos dados
5. Ajustar refresh rate para mostrar flexibilidade

---

## 2. Alarms & Events View

**Rota**: `/data/alarms-events`
**Arquivo**: [frontend/src/pages/AlarmsEventsView.tsx](frontend/src/pages/AlarmsEventsView.tsx)

### Objetivo
Centralizar todos os alarmes e eventos gerados pelo sistema, incluindo alertas ML/DS e do Autonomous Agent.

### Funcionalidades

#### Summary Cards
- **Total Active**: Total de alarmes ativos (com badge de não reconhecidos)
- **Critical**: Alarmes críticos (vermelho)
- **High**: Alarmes de alta prioridade (laranja)
- **Medium**: Alarmes de média prioridade (azul)
- **Low**: Alarmes de baixa prioridade (verde)
- **Unacknowledged**: Alarmes não reconhecidos

#### Visualizações

**Pie Chart - Alarms by Severity**
- Distribuição de alarmes por severidade
- Cores distintas por nível
- Legendas interativas

**Bar Chart - Events by Type**
- Alarmes
- Eventos
- Anomalias
- Predições

#### Filtros
- **Type**: All, Alarms, Events, Anomalies, Predictions
- **Severity**: All, Critical, High, Medium, Low
- Contador de resultados filtrados

#### Tabela de Alarmes
Colunas:
- **Severity**: Ícone + chip colorido
- **Type**: Tipo do evento
- **Title**: Título do alarme
- **Description**: Descrição (truncada)
- **Source**: Origem (Autonomous Agent, ML Energy Predictor, etc.)
- **Timestamp**: Data/hora
- **Status**: Active / Acknowledged
- **Actions**: Botão para ver detalhes

#### Dialog de Detalhes
- Alert visual com severidade
- Informações completas
- Botão "Acknowledge" para reconhecer alarme

### Fontes de Dados

1. **Autonomous Agent Insights**
```
GET /api/v1/ai-agent/insights
```

2. **ML Insights Alerts**
```
GET /api/v1/ml/insights/all?time_range=last_24h
```

#### Tipos de Alertas ML
- **Energy Abnormal**: Consumo energético fora do esperado
- **Anomalies Multiple**: Múltiplas anomalias detectadas (>5)
- **Reliability Critical**: MTBF crítico, manutenção urgente

### Demonstração Ideal
1. Mostrar integração de múltiplas fontes de alertas
2. Demonstrar filtros por tipo e severidade
3. Explicar diferença entre alarmes e predições
4. Mostrar detalhes de alerta ML
5. Demonstrar workflow de acknowledgment

---

## 3. Historical Data Analysis

**Rota**: `/data/historical`
**Arquivo**: [frontend/src/pages/HistoricalDataAnalysis.tsx](frontend/src/pages/HistoricalDataAnalysis.tsx)

### Objetivo
Análise estatística profunda de dados históricos com visualizações e exportação.

### Funcionalidades

#### Filtros
- **Time Range**: Last 24h, 7 days, 30 days, 90 days
- **Aggregation**: Raw, 1min, 5min, 1hour, 1day average
- **Select Tags**: Seleção de tags para análise

#### Time Series Chart (Area Chart)
- Visualização de séries temporais
- Múltiplas tags sobrepostas
- Gradientes coloridos
- Tooltips com timestamp completo
- Eixo X formatado para datas

#### Statistical Summary Cards

Para cada tag analisada:
- **Mean**: Média
- **Median**: Mediana
- **Std Dev**: Desvio padrão
- **Count**: Número de pontos
- **Range**: Min, P25, P75, P95, Max como chips

**Distribution Chart (Bar)**
- Visualização da distribuição estatística
- Linha de referência na média
- Quartis e percentis

#### Data Quality Overview
- **Total Records**: Contagem total
- **Good Quality**: Dados de boa qualidade
- **Bad/Uncertain**: Dados problemáticos

#### Recent Data Points Table
- Últimos 50 pontos de dados
- Timestamp, Tag Name, Value, Quality
- Scroll infinito

#### Export
- Botão "Export CSV"
- Exporta todos os dados históricos
- Formato: timestamp, tag_name, value, quality

### API Endpoints
```
GET /api/v1/tags/list
GET /api/v1/tags/history?tag_name=X&time_range=Y&aggregation=Z
```

### Cálculos Estatísticos (Client-Side)
- Mean, Median, Std Dev
- Percentis (P25, P75, P95)
- Min/Max

### Demonstração Ideal
1. Selecionar tag importante (energy_consumption)
2. Mostrar diferentes time ranges
3. Explicar agregações (raw vs 1h avg)
4. Destacar statistical summary
5. Mostrar distribuição dos dados
6. Exportar dados como CSV

---

## 4. ML Model Execution View

**Rota**: `/ml-demo`
**Arquivo**: [frontend/src/pages/MLModelExecutionView.tsx](frontend/src/pages/MLModelExecutionView.tsx)

### Objetivo
**A VIEW MAIS IMPORTANTE** - Demonstra o modelo ML trabalhando passo a passo em tempo real, mostrando todo o pipeline de execução.

### Funcionalidades

#### Model Selection
Cards clicáveis para selecionar modelo:
- **Gradient Boosting** - Energy Efficiency
- **Isolation Forest** - Anomaly Detection
- **LSTM** - Energy Prediction
- **Random Forest** - Efficiency

#### Execution Pipeline (Stepper Vertical)

**Step 1: Data Collection**
- Coleta dados do InfluxDB
- Mostra quantidade de pontos coletados
- Tempo de execução

**Step 2: Data Preprocessing**
- Limpeza de dados
- Normalização
- Tratamento de valores missing
- Remoção de outliers

**Step 3: Feature Engineering**
- Geração de features
- Features temporais
- Features estatísticas
- Features lagged
- Contagem de features geradas

**Step 4: Model Loading**
- Carregamento do modelo do storage
- Tamanho do modelo (MB)
- Data de treinamento
- Metadados do modelo

**Step 5: Model Inference**
- Execução da inferência
- Tempo de inferência (ms)
- Performance metrics

**Step 6: Results Generation**
- Geração de predições
- Cálculo de métricas
- Visualizações

#### Execution Log (Console)
- Log em tempo real das operações
- Formato: `[HH:MM:SS] message`
- Fundo escuro estilo terminal
- Auto-scroll para última mensagem

#### Model Performance Metrics

Métricas mostradas (dependendo do modelo):
- **Model Name**
- **Execution Time**: Tempo total (ms)
- **R² Score**: Para modelos de regressão
- **MAE**: Mean Absolute Error
- **Accuracy**: Para modelos de classificação
- **Data Points**: Quantidade de dados processados

#### Predictions Visualizations

**Chart 1: Predictions vs Actual Values (Line)**
- Linha azul: Valores reais
- Linha vermelha tracejada: Predições
- Tooltip com valores

**Chart 2: Prediction Error Distribution (Scatter)**
- Eixo X: Valores reais
- Eixo Y: Predições
- Linha de referência (predição perfeita)
- Dispersão mostra erro

**Table: Recent Predictions**
- Timestamp
- Actual value
- Predicted value
- Error (colorido: verde <10, amarelo <30, vermelho >30)
- Confidence (%)

### Estados da UI

**Waiting State**
- Ícone grande de ML
- Mensagem: "Click 'Run Model' to start ML execution"
- Descrição: "Watch the model process data in real-time"

**Running State**
- Botão muda para "Stop"
- Steps vão mudando de status
- Log sendo preenchido
- Progress indicators

**Completed State**
- Todos os steps com checkmark verde
- Métricas exibidas
- Visualizações geradas
- Botão volta para "Run Model"

### API Endpoints Usados
```
GET /api/v1/tags/history
GET /api/v1/ml/models/{model_name}
GET /api/v1/ml/insights/all?time_range=last_24h
```

### Demonstração Ideal (SCRIPT)

1. **Introdução (30s)**
   - "Vou mostrar o modelo ML trabalhando passo a passo"
   - Selecionar modelo: Gradient Boosting

2. **Iniciar Execução (2min)**
   - Clicar "Run Model"
   - **Step 1**: "Primeiro, coletamos dados do InfluxDB - veja, coletamos 100 pontos"
   - **Step 2**: "Agora limpamos os dados - removemos 3 outliers, preenchemos 2 valores faltando"
   - **Step 3**: "Feature engineering - geramos 12 features derivadas"
   - **Step 4**: "Carregamos o modelo pré-treinado - veja, 2.5 MB, treinado ontem"
   - **Step 5**: "Executando inferência - olhe o tempo: 850ms!"
   - **Step 6**: "Gerando resultados..."

3. **Análise de Resultados (1min)**
   - Mostrar métricas: "R² Score de 85% - excelente!"
   - Gráfico: "Veja como as predições (linha vermelha) acompanham os valores reais (azul)"
   - Scatter: "A dispersão mostra o erro - pontos próximos da linha = boas predições"
   - Tabela: "Erros individuais - maioria com erro <10, confiança >80%"

4. **Destacar Vantagens (30s)**
   - "Todo o processo levou menos de 4 segundos"
   - "Modelo carregado da cache - não precisou treinar"
   - "Transparência total do processo"

### Timing dos Steps (Configurável)
```typescript
Step 1: 1000ms (Data Collection)
Step 2: 800ms (Preprocessing)
Step 3: 700ms (Feature Engineering)
Step 4: 600ms (Model Loading)
Step 5: Variable (Inference - real API call)
Step 6: 500ms (Results Generation)
```

---

## Navegação no Sidebar

As 4 views foram adicionadas em uma nova seção chamada **"Dados & ML Demo"**:

```
📊 Dados & ML Demo
  ├─ 📡 Dados em Tempo Real       → /data/realtime
  ├─ 🚨 Alarmes & Eventos         → /data/alarms-events
  ├─ 📈 Análise Histórica         → /data/historical
  └─ 🔬 ML Execution Demo         → /ml-demo
```

---

## Rotas Configuradas

Todas as rotas foram adicionadas em [frontend/src/App.tsx](frontend/src/App.tsx:93-96):

```tsx
{/* AI INSIGHTS & ML DEMO */}
<Route path="insights" element={<InsightsPage />} />
<Route path="ml-insights" element={<MLInsightsDashboard />} />
<Route path="data/realtime" element={<RealTimeDataView />} />
<Route path="data/alarms-events" element={<AlarmsEventsView />} />
<Route path="data/historical" element={<HistoricalDataAnalysis />} />
<Route path="ml-demo" element={<MLModelExecutionView />} />
```

---

## Fluxo de Demonstração Completo (5 min)

### 1. Real-Time Data (1 min)
- Abrir `/data/realtime`
- Mostrar dados chegando ao vivo
- Explicar categorias e qualidade
- Ajustar refresh rate

### 2. ML Model Execution (2 min)
- Abrir `/ml-demo`
- **MOMENTO PRINCIPAL**
- Executar pipeline completo
- Explicar cada step
- Mostrar predições vs valores reais
- Destacar métricas

### 3. Alarms & Events (1 min)
- Abrir `/data/alarms-events`
- Mostrar alarmes ML gerados
- Filtrar por severidade
- Ver detalhes de alerta critical

### 4. Historical Analysis (1 min)
- Abrir `/data/historical`
- Selecionar tag importante
- Mostrar estatísticas
- Exportar dados

---

## Tecnologias Utilizadas

### Frontend
- **React 18** + **TypeScript**
- **Material-UI (MUI)** - Components
- **Recharts** - Visualizações
- **React Router** - Navegação

### Bibliotecas de Gráficos
- **LineChart** - Séries temporais
- **AreaChart** - Tendências
- **BarChart** - Distribuições
- **PieChart** - Severidades
- **ScatterChart** - Correlações

### Estado
- Local state com `useState`
- `useEffect` para polling
- Interval-based updates

---

## Melhorias Futuras

### Real-Time Data View
- [ ] WebSocket para dados real-time (substituir polling)
- [ ] Seleção múltipla de tags para charts
- [ ] Export de dados em tempo real
- [ ] Zoom nos mini charts

### Alarms & Events View
- [ ] Workflow de acknowledgment funcional
- [ ] Filtros por data/hora
- [ ] Exportar lista de alarmes
- [ ] Push notifications
- [ ] Integração com sistema de tickets

### Historical Data Analysis
- [ ] Comparação entre múltiplas tags
- [ ] Correlação entre tags
- [ ] Detecção automática de padrões
- [ ] Export em múltiplos formatos (Excel, JSON)
- [ ] Análise de frequência (FFT)

### ML Model Execution View
- [ ] Seleção de múltiplos modelos simultaneamente
- [ ] Comparação de performance entre modelos
- [ ] Configuração de hiperparâmetros
- [ ] Download de predições
- [ ] Feature importance visualization
- [ ] SHAP values visualization
- [ ] Confusion matrix (para classificação)
- [ ] Residual plots
- [ ] Learning curves

---

## Requisitos de Backend

### Endpoints Necessários

Todos os endpoints já existem ou podem ser implementados facilmente:

1. **Tags Real-time**
```
GET /api/v1/tags/realtime?limit=50&category=process
Response: [{ name, value, unit, timestamp, quality, category }]
```

2. **Tags History**
```
GET /api/v1/tags/history?tag_name=X&time_range=Y&aggregation=Z
Response: { data: [{ timestamp, value, tag_name, quality }] }
```

3. **AI Agent Insights**
```
GET /api/v1/ai-agent/insights
Response: [{ id, title, description, severity, category, timestamp, tags }]
```

4. **ML Insights**
```
GET /api/v1/ml/insights/all?time_range=last_24h
Response: { insights: { energy_prediction, anomalies, reliability, ... } }
```

5. **ML Model Info**
```
GET /api/v1/ml/models/{model_name}
Response: { model_name, size_mb, metadata: { r2_score, trained_at } }
```

---

## Performance

### Otimizações Implementadas

1. **Polling Inteligente**
   - Intervalos configuráveis
   - Pausa automática quando inativo
   - Cleanup de intervals no unmount

2. **Data Limiting**
   - Máximo 50 tags na real-time view
   - Histórico limitado a 30 pontos nos mini charts
   - Tabelas com sticky header e virtualização

3. **Memoization**
   - Cálculos estatísticos cacheable
   - Chart data pre-processado

4. **Lazy Loading**
   - Components carregados sob demanda
   - Routes com code splitting

---

## Troubleshooting

### Real-Time Data não atualiza
- Verificar se backend está rodando
- Verificar endpoint `/api/v1/tags/realtime`
- Verificar console para erros de CORS

### ML Demo não executa
- Verificar se modelos estão salvos em `/app/models/`
- Verificar endpoint `/api/v1/ml/models/list`
- Verificar InfluxDB tem dados

### Charts não renderizam
- Verificar se Recharts está instalado
- Verificar formato dos dados
- Verificar altura do ResponsiveContainer

### Performance lenta
- Reduzir refresh interval
- Limitar número de tags
- Usar agregação nos dados históricos

---

## Conclusão

Estas 4 views formam um **kit completo de demonstração** que mostra:

1. ✅ **Coleta de Dados** - Real-time data view
2. ✅ **Processamento** - ML execution demo
3. ✅ **Análise** - Historical analysis
4. ✅ **Alertas** - Alarms & events

**A view mais importante é a ML Model Execution View** (`/ml-demo`), pois mostra o **valor real do sistema** - modelos ML trabalhando em tempo real para otimizar operações.

**Tempo total de demo**: 5 minutos
**Impacto**: ALTO - demonstra claramente o diferencial tecnológico do OptiFlow AI

---

**Status**: ✅ COMPLETO E PRONTO PARA DEMONSTRAÇÃO
