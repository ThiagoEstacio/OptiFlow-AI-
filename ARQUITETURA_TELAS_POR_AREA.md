# 🎨 Arquitetura de Telas por Área - OptiFlow AI

## 📊 Status Atual (Mapeamento Completo)

### Estrutura Hierárquica ISA-95

```
OptiFlow AI Platform
├── 🏠 Principal (Cross-Functional)
├── ⚙️ Operações (Operations)
├── 🔧 Manutenção (Maintenance)
├── 🛠️ Engenharia (Engineering)
├── 👔 Executivo (Executive)
└── ⚙️ Configuração (Configuration)
```

---

## 📋 MAPEAMENTO ATUAL DE TELAS

### 🏠 **MÓDULO PRINCIPAL** (Cross-Functional)

| Tela | Rota | Arquivo | Status | Descrição |
|------|------|---------|--------|-----------|
| Dashboard Home | `/` | ModernDashboard.tsx | ✅ Existe | Dashboard principal com visão geral |
| Insights IA | `/insights` | InsightsPage.tsx | ✅ Existe | Insights do Autonomous Agent |
| Centro de Análise | `/analytics-hub` | AnalyticsHub.tsx | ✅ Existe | Hub central de analytics |
| Saúde de Assets | `/asset-health-hub` | AssetHealthHub.tsx | ✅ Existe | Hub de saúde de equipamentos |
| Assistente IA | `/chat` | ChatPage.tsx | ✅ Existe | Chat com IA |

---

### ⚙️ **MÓDULO DE OPERAÇÕES**

| Tela | Rota | Arquivo | Status | Descrição |
|------|------|---------|--------|-----------|
| Hub de Operações | `/operations` | OperationsHub.tsx | ✅ Existe | Landing page do módulo |
| SCADA Monitor | `/operations/scada` | SCADAPage.tsx | ✅ Existe | Monitoramento SCADA em tempo real |
| Visão Geral | `/operations/overview` | ModernDashboard.tsx | ✅ Existe | Overview operacional |
| **Controle de Processo** | `/operations/process-control` | ❌ Não Existe | ⚠️ Falta | Controle de processos industriais |
| **Alarmes Ativos** | `/operations/active-alarms` | ❌ Não Existe | ⚠️ Falta | Lista de alarmes em tempo real |
| **Logs de Operação** | `/operations/logs` | ❌ Não Existe | ⚠️ Falta | Histórico de operações |

**Funcionalidades Esperadas**:
- ✅ Monitoramento em tempo real (SCADA)
- ⚠️ Controle de equipamentos (falta)
- ⚠️ Gerenciamento de alarmes (falta)
- ⚠️ Logs de eventos (falta)

---

### 🔧 **MÓDULO DE MANUTENÇÃO**

| Tela | Rota | Arquivo | Status | Descrição |
|------|------|---------|--------|-----------|
| Hub de Manutenção | `/maintenance` | MaintenanceHub.tsx | ✅ Existe | Landing page do módulo |
| Manutenção Preditiva | `/maintenance/predictive` | AssetHealthHub.tsx | ✅ Existe | Análise preditiva de falhas |
| **Ordens de Trabalho** | `/maintenance/work-orders` | ❌ Não Existe | ⚠️ Falta | Gestão de ordens de serviço |
| **Histórico de Falhas** | `/maintenance/failure-history` | ❌ Não Existe | ⚠️ Falta | Histórico de falhas e reparos |
| **Calendário de Manutenção** | `/maintenance/calendar` | ❌ Não Existe | ⚠️ Falta | Agendamento de manutenções |
| **Análise de MTBF/MTTR** | `/maintenance/reliability` | ❌ Não Existe | ⚠️ Falta | Métricas de confiabilidade |

**Funcionalidades Esperadas**:
- ✅ Predição de falhas (existe)
- ⚠️ Gestão de ordens de trabalho (falta)
- ⚠️ Histórico e análise de falhas (falta)
- ⚠️ Planejamento de manutenção (falta)

---

### 🛠️ **MÓDULO DE ENGENHARIA**

| Tela | Rota | Arquivo | Status | Descrição |
|------|------|---------|--------|-----------|
| Hub de Engenharia | `/engineering` | EngineeringHub.tsx | ✅ Existe | Landing page do módulo |
| **Otimização de Processo** | `/engineering/optimization` | ❌ Não Existe | ⚠️ Falta | Simulações e otimizações |
| **Análise de Performance** | `/engineering/performance` | ❌ Não Existe | ⚠️ Falta | KPIs de performance |
| **Modelagem de Processo** | `/engineering/modeling` | ❌ Não Existe | ⚠️ Falta | Modelos e simulações |
| **Balanço de Massa/Energia** | `/engineering/balance` | ❌ Não Existe | ⚠️ Falta | Balanços de massa e energia |
| **Análise de Tendências** | `/engineering/trends` | ❌ Não Existe | ⚠️ Falta | Análise estatística de tendências |

**Funcionalidades Esperadas**:
- ⚠️ Simulação e otimização (falta)
- ⚠️ Análise de performance (falta)
- ⚠️ Modelagem de processos (falta)
- ⚠️ Balanços e tendências (falta)

---

### 👔 **MÓDULO EXECUTIVO / GBM**

| Tela | Rota | Arquivo | Status | Descrição |
|------|------|---------|--------|-----------|
| Dashboard Executivo | `/executive/:siteId` | ExecutiveDashboard.tsx | ✅ Existe | KPIs executivos |
| Importar Dados GBM | `/gbm-import/:siteId` | GBMDataImport.tsx | ✅ Existe | Importação de dados |
| Insights GBM | `/gbm-insights/:siteId` | GBMInsights.tsx | ✅ Existe | Análises de dados GBM |
| Tendências Históricas | `/historical-trends/:siteId` | HistoricalTrends.tsx | ✅ Existe | Análise histórica |
| **Relatórios Financeiros** | `/executive/financial` | ❌ Não Existe | ⚠️ Falta | ROI, custos, receitas |
| **Análise de Riscos** | `/executive/risks` | ❌ Não Existe | ⚠️ Falta | Matriz de riscos |

**Funcionalidades Esperadas**:
- ✅ KPIs e dashboards (existe)
- ✅ Importação de dados (existe)
- ✅ Análise histórica (existe)
- ⚠️ Análise financeira (falta)
- ⚠️ Gestão de riscos (falta)

---

### ⚙️ **MÓDULO DE CONFIGURAÇÃO**

| Tela | Rota | Arquivo | Status | Descrição |
|------|------|---------|--------|-----------|
| Hub de Configuração | `/config` | ConfigurationHub.tsx | ✅ Existe | Landing page do módulo |
| Configuração Simulador | `/config/simulator` | SimulatorConfigPage.tsx | ✅ Existe | Config do simulador |
| Fontes de Dados | `/config/data-sources` | GatewayManagementPage.tsx | ✅ Existe | Gestão de gateways |
| Gerenciar Tags | `/config/tags` | TagsPage.tsx | ✅ Existe | CRUD de tags |
| Configurar Alarmes | `/config/alarms` | AlarmsPage.tsx | ✅ Existe | Config de alarmes |
| Usuários | `/config/users` | SettingsPage.tsx | ✅ Existe | Gestão de usuários |
| Admin | `/admin` | AdminPage.tsx | ✅ Existe | Painel administrativo |

**Funcionalidades Esperadas**:
- ✅ Configuração de simulador (existe)
- ✅ Gestão de gateways (existe)
- ✅ Gestão de tags (existe)
- ✅ Configuração de alarmes (existe)
- ✅ Gestão de usuários (existe)

---

## 📊 RESUMO POR MÓDULO

| Módulo | Telas Existentes | Telas Faltando | Completude |
|--------|------------------|----------------|------------|
| Principal | 5 | 0 | ✅ 100% |
| Operações | 3 | 3 | ⚠️ 50% |
| Manutenção | 2 | 4 | ⚠️ 33% |
| Engenharia | 1 | 5 | ⚠️ 17% |
| Executivo/GBM | 4 | 2 | ✅ 67% |
| Configuração | 7 | 0 | ✅ 100% |

**TOTAL**: 22 telas existentes / 14 telas faltando = **61% de completude**

---

## 🎯 TELAS PRIORITÁRIAS A CRIAR

### **Alta Prioridade** (Funcionalidades Core)

1. **Operações - Controle de Processo** (`/operations/process-control`)
   - Controle manual/automático de equipamentos
   - Setpoints e comandos
   - Estados de equipamentos

2. **Operações - Alarmes Ativos** (`/operations/active-alarms`)
   - Lista em tempo real de alarmes
   - Ações de acknowledge e dismiss
   - Filtros por severidade

3. **Manutenção - Ordens de Trabalho** (`/maintenance/work-orders`)
   - CRUD de ordens de serviço
   - Status tracking
   - Atribuição de técnicos

4. **Manutenção - Histórico de Falhas** (`/maintenance/failure-history`)
   - Timeline de falhas
   - Análise de causas raiz
   - Pareto de falhas

### **Média Prioridade** (Análise e Otimização)

5. **Engenharia - Otimização de Processo** (`/engineering/optimization`)
   - Simulação de cenários
   - Recomendações de IA
   - Comparação de resultados

6. **Engenharia - Análise de Performance** (`/engineering/performance`)
   - OEE (Overall Equipment Effectiveness)
   - Disponibilidade, Performance, Qualidade
   - Benchmarking

7. **Manutenção - Análise MTBF/MTTR** (`/maintenance/reliability`)
   - Métricas de confiabilidade
   - Gráficos de Weibull
   - Previsão de vida útil

### **Baixa Prioridade** (Nice to Have)

8. **Operações - Logs de Operação** (`/operations/logs`)
9. **Manutenção - Calendário** (`/maintenance/calendar`)
10. **Engenharia - Modelagem** (`/engineering/modeling`)
11. **Engenharia - Balanço M/E** (`/engineering/balance`)
12. **Executivo - Análise Financeira** (`/executive/financial`)
13. **Executivo - Análise de Riscos** (`/executive/risks`)

---

## 🗺️ ARQUITETURA DE NAVEGAÇÃO PROPOSTA

### **Sidebar Reorganizada por ISA-95**

```
┌─────────────────────────────────────┐
│ OptiFlow AI                         │
├─────────────────────────────────────┤
│ 🏠 Principal                        │
│   ├─ Dashboard                      │
│   ├─ Insights IA                    │
│   ├─ Centro de Análise              │
│   ├─ Saúde de Assets                │
│   └─ Assistente IA                  │
├─────────────────────────────────────┤
│ ⚙️ Operações                        │
│   ├─ SCADA Monitor                  │
│   ├─ Controle de Processo     [NEW] │
│   ├─ Alarmes Ativos           [NEW] │
│   └─ Logs de Operação         [NEW] │
├─────────────────────────────────────┤
│ 🔧 Manutenção                       │
│   ├─ Manutenção Preditiva           │
│   ├─ Ordens de Trabalho       [NEW] │
│   ├─ Histórico de Falhas      [NEW] │
│   ├─ Análise de Confiabilidade[NEW] │
│   └─ Calendário               [NEW] │
├─────────────────────────────────────┤
│ 🛠️ Engenharia                       │
│   ├─ Otimização de Processo   [NEW] │
│   ├─ Análise de Performance   [NEW] │
│   ├─ Modelagem de Processo    [NEW] │
│   ├─ Balanço de Massa/Energia [NEW] │
│   └─ Análise de Tendências    [NEW] │
├─────────────────────────────────────┤
│ 👔 Executivo                        │
│   ├─ Dashboard Executivo            │
│   ├─ Insights GBM                   │
│   ├─ Tendências Históricas          │
│   ├─ Importar Dados                 │
│   ├─ Análise Financeira       [NEW] │
│   └─ Análise de Riscos        [NEW] │
├─────────────────────────────────────┤
│ ⚙️ Configuração                     │
│   ├─ Simulador                      │
│   ├─ Fontes de Dados                │
│   ├─ Tags                           │
│   ├─ Alarmes                        │
│   └─ Usuários                       │
├─────────────────────────────────────┤
│ 🔧 Sistema                          │
│   ├─ Admin                          │
│   └─ Configurações                  │
└─────────────────────────────────────┘
```

---

## 📐 DESIGN PATTERNS POR TIPO DE TELA

### **1. Telas de Monitoramento (Real-Time)**
**Exemplos**: SCADA, Alarmes Ativos, Controle de Processo

**Componentes**:
- Header com timestamp e status de conexão
- Grid de cards com valores em tempo real
- Gráficos de tendência (últimas 24h)
- Indicadores visuais (semáforos, barras)
- WebSocket para atualizações live

**Layout**:
```
┌────────────────────────────────────────┐
│ [Breadcrumb] SCADA Monitor    [●Live] │
├────────────────────────────────────────┤
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐      │
│ │ KPI │ │ KPI │ │ KPI │ │ KPI │      │
│ └─────┘ └─────┘ └─────┘ └─────┘      │
│ ┌────────────────────┐ ┌────────────┐ │
│ │  Gráfico Tempo    │ │  Alarmes   │ │
│ │  Real             │ │  Recentes  │ │
│ └────────────────────┘ └────────────┘ │
│ ┌──────────────────────────────────┐  │
│ │  Equipamentos (Grid de Cards)    │  │
│ └──────────────────────────────────┘  │
└────────────────────────────────────────┘
```

### **2. Telas de Análise (Historical)**
**Exemplos**: Histórico de Falhas, Análise de Performance, Tendências

**Componentes**:
- Filtros de data/período
- Gráficos históricos (line, bar, scatter)
- Tabelas com paginação
- Exportação de dados (CSV, PDF)
- Comparação de períodos

**Layout**:
```
┌────────────────────────────────────────┐
│ [Breadcrumb] Análise de Performance    │
├────────────────────────────────────────┤
│ 📅 [Data Início] [Data Fim] [Aplicar] │
│ ┌─────┐ ┌─────┐ ┌─────┐              │
│ │ Avg │ │ Max │ │ Min │              │
│ └─────┘ └─────┘ └─────┘              │
│ ┌──────────────────────────────────┐  │
│ │  Gráfico Histórico (Line Chart)  │  │
│ └──────────────────────────────────┘  │
│ ┌──────────────────────────────────┐  │
│ │  Tabela de Dados (Paginated)     │  │
│ └──────────────────────────────────┘  │
│          [Exportar CSV] [Exportar PDF]│
└────────────────────────────────────────┘
```

### **3. Telas de Gestão (CRUD)**
**Exemplos**: Ordens de Trabalho, Tags, Usuários

**Componentes**:
- Botão "Criar Novo"
- Tabela com ações (editar, deletar)
- Modal/drawer de edição
- Filtros e busca
- Paginação

**Layout**:
```
┌────────────────────────────────────────┐
│ [Breadcrumb] Ordens de Trabalho        │
├────────────────────────────────────────┤
│ 🔍 [Buscar...] [Filtros▼] [+Novo]    │
│ ┌──────────────────────────────────┐  │
│ │ ID │ Descrição │ Status │ Ações  │  │
│ ├────┼───────────┼────────┼────────┤  │
│ │ 01 │ Manutenção│ Aberta │ [✏️][🗑️]│  │
│ │ 02 │ Reparo... │ Fechada│ [✏️][🗑️]│  │
│ └──────────────────────────────────┘  │
│            [← Anterior] [Próxima →]   │
└────────────────────────────────────────┘
```

### **4. Telas de Dashboard (Executive)**
**Exemplos**: Dashboard Executivo, Hub de Módulo

**Componentes**:
- Cards de KPIs principais
- Gráficos executivos (pizza, bar, gauge)
- Alerts e notificações
- Navegação rápida para detalhes

**Layout**:
```
┌────────────────────────────────────────┐
│ [Breadcrumb] Dashboard Executivo       │
├────────────────────────────────────────┤
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐      │
│ │ OEE │ │Prod.│ │Custo│ │ ROI │      │
│ └─────┘ └─────┘ └─────┘ └─────┘      │
│ ┌────────────┐ ┌────────────────────┐ │
│ │ Produção   │ │ Custos Mensais     │ │
│ │ (Bar Chart)│ │ (Line Chart)       │ │
│ └────────────┘ └────────────────────┘ │
│ ┌──────────────────────────────────┐  │
│ │  Alertas e Recomendações         │  │
│ └──────────────────────────────────┘  │
└────────────────────────────────────────┘
```

---

## 🎨 COMPONENTES REUTILIZÁVEIS A CRIAR

### **Core Components**

1. **`<RealtimeCard />`** - Card com valor em tempo real
   - Props: `tagName`, `unit`, `thresholds`, `showTrend`
   - Auto-refresh via WebSocket

2. **`<TrendChart />`** - Gráfico de tendência
   - Props: `tagName`, `timeRange`, `showPrediction`
   - Suporta zoom e pan

3. **`<AlarmList />`** - Lista de alarmes
   - Props: `severity`, `limit`, `showActions`
   - Actions: acknowledge, dismiss, details

4. **`<KPICard />`** - Card de KPI
   - Props: `value`, `target`, `label`, `trend`
   - Visual: gauge, number, percentage

5. **`<DataTable />`** - Tabela com filtros
   - Props: `columns`, `data`, `actions`, `pagination`
   - Sorting, filtering, export

6. **`<DateRangePicker />`** - Seletor de período
   - Props: `onChange`, `presets`
   - Presets: Hoje, Ontem, Última semana, Último mês

7. **`<EquipmentCard />`** - Card de equipamento
   - Props: `equipment`, `showStatus`, `showControls`
   - Visual: status, valores, comandos

8. **`<WorkOrderForm />`** - Formulário de ordem
   - Props: `onSubmit`, `initialData`
   - Validação e auto-complete

---

## 🚀 ROADMAP DE IMPLEMENTAÇÃO

### **Fase 1: Operações** (2-3 semanas)
- [ ] Controle de Processo
- [ ] Alarmes Ativos
- [ ] Logs de Operação
- [ ] Componentes: RealtimeCard, AlarmList

### **Fase 2: Manutenção** (3-4 semanas)
- [ ] Ordens de Trabalho
- [ ] Histórico de Falhas
- [ ] Análise MTBF/MTTR
- [ ] Calendário
- [ ] Componentes: WorkOrderForm, DataTable

### **Fase 3: Engenharia** (4-5 semanas)
- [ ] Otimização de Processo
- [ ] Análise de Performance
- [ ] Modelagem
- [ ] Balanço M/E
- [ ] Análise de Tendências
- [ ] Componentes: TrendChart, KPICard

### **Fase 4: Executivo** (2 semanas)
- [ ] Análise Financeira
- [ ] Análise de Riscos
- [ ] Componentes: Executive charts

### **Fase 5: Reorganização Sidebar** (1 semana)
- [ ] Implementar nova estrutura ISA-95
- [ ] Adicionar badges de notificação
- [ ] Melhorar navegação

---

## 📊 MÉTRICAS DE SUCESSO

### **Completude por Módulo**
- Operações: 50% → **100%**
- Manutenção: 33% → **100%**
- Engenharia: 17% → **100%**
- Executivo: 67% → **100%**

### **Componentes Reutilizáveis**
- 0 → **8 componentes core**

### **Cobertura de Funcionalidades**
- 61% → **100%**

---

**Status**: 📋 Arquitetura mapeada e pronta para implementação
**Próximo Passo**: Escolher módulo para começar (recomendado: Operações - Fase 1)
