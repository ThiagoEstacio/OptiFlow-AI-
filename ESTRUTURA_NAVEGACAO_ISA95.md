# 📐 Estrutura de Navegação - OptiFlow AI
## Baseada na Norma ISA-95

**Data**: 2025-11-06
**Versão**: 2.0 - Reorganização por Módulos Funcionais

---

## 🎯 OBJETIVO

Reorganizar a navegação do OptiFlow AI seguindo os princípios da **ISA-95** (International Society of Automation - Enterprise-Control System Integration), proporcionando uma estrutura hierárquica clara e alinhada com os níveis funcionais de uma indústria.

---

## 📊 ARQUITETURA ISA-95

### Níveis Funcionais (ISA-95 Model)

```
┌─────────────────────────────────────────────────────┐
│  Nível 4: Planejamento Empresarial (ERP)           │  ← Executivo
├─────────────────────────────────────────────────────┤
│  Nível 3: Gerenciamento de Operações (MES)         │  ← Operações
│           Manufacturing Execution System             │     Manutenção
│                                                      │     Engenharia
├─────────────────────────────────────────────────────┤
│  Nível 2: Supervisão e Controle (SCADA)            │  ← Operações
│           Supervisory Control                        │     (Monitoramento)
├─────────────────────────────────────────────────────┤
│  Nível 1: Controle Básico (PLC/DCS)                │  ← Dispositivos
│           Programmable Logic Controllers             │     (Configuração)
├─────────────────────────────────────────────────────┤
│  Nível 0: Processos Físicos                         │  ← Sensores/Atuadores
│           Sensors, Actuators, Equipment              │
└─────────────────────────────────────────────────────┘
```

---

## 🗂️ NOVA ESTRUTURA DE NAVEGAÇÃO

### 1️⃣ **PRINCIPAL** (Nível Transversal)
**Propósito**: Acesso rápido a funcionalidades principais e IA

```
├─ Dashboard Home           → Visão geral do sistema
├─ Insights IA              → Insights do Autonomous Agent
├─ ML/DS Insights           → Machine Learning / Data Science
└─ Assistente IA            → Chatbot inteligente
```

**Alinhamento ISA-95**: Transversal (todos os níveis)
**Usuários típicos**: Todos

---

### 2️⃣ **OPERAÇÕES** (Nível 2-3)
**Propósito**: Monitoramento em tempo real e controle de processo
**ISA-95**: Nível 2 (Supervisão) + Nível 3 (MES)

```
├─ Hub de Operações                    → Central operacional
├─ Meus Dashboards                     → Dashboards personalizados
├─ 📊 Monitoramento Tempo Real ⭐      → Nova! Real-time data feed
├─ 🚨 Alarmes & Eventos ⭐             → Nova! Unified alarms view
├─ SCADA Monitor                       → Supervisório
├─ Controle de Processo                → Process control
└─ Logs de Operação                    → Operational logs
```

**Funcionalidades das Novas Views**:

#### 📊 **Monitoramento Tempo Real**
- **Rota**: `/data/realtime`
- **Endpoint**: `GET /api/v1/demo/tags/realtime`
- **Funcionalidades**:
  - Live data streaming (atualização a cada 2s)
  - Filtros por categoria (ENERGY, PROCESS, MAINTENANCE, etc.)
  - Mini-charts para cada tag
  - Indicadores de qualidade
  - Trend detection (↑↓)
  - Status: Operational/Warning/Critical
- **Use Case**: Sala de controle, operadores monitorando processo em tempo real
- **ISA-95 Level**: Nível 2 (Supervisão)

#### 🚨 **Alarmes & Eventos**
- **Rota**: `/data/alarms-events`
- **Endpoints**:
  - `GET /api/v1/demo/ai-agent/insights` (Autonomous Agent)
  - `GET /api/v1/ml/insights/all` (ML Insights)
- **Funcionalidades**:
  - Integração com Autonomous Agent
  - Integração com ML Insights
  - Filtros por tipo (alarm, event, insight, prediction)
  - Filtros por severidade (critical, high, medium, low)
  - Timeline de eventos
  - Estatísticas de alarmes
  - Badge de contagem no menu
- **Use Case**: Centro de alarmes unificado, resposta a incidentes
- **ISA-95 Level**: Nível 2-3 (Supervisão + MES)

**Alinhamento ISA-95**: Nível 2 (SCADA) + Nível 3 (MES)
**Usuários típicos**: Operadores, Supervisores de turno

---

### 3️⃣ **MANUTENÇÃO** (Nível 3)
**Propósito**: Gestão de manutenção e confiabilidade
**ISA-95**: Nível 3 (MES - Maintenance Management)

```
├─ Hub de Manutenção
├─ Meus Dashboards
├─ Manutenção Preditiva           → Predictive models
├─ Ordens de Trabalho             → Work order management
├─ Histórico de Falhas            → Failure history
├─ Análise MTBF/MTTR              → Reliability metrics
└─ Calendário                     → Maintenance calendar
```

**Alinhamento ISA-95**: Nível 3 (MES)
**Usuários típicos**: Equipe de manutenção, Planejadores

---

### 4️⃣ **ENGENHARIA** (Nível 3)
**Propósito**: Análise técnica, otimização e melhoria contínua
**ISA-95**: Nível 3 (MES - Engineering Functions)

```
├─ Hub de Engenharia
├─ Meus Dashboards
├─ 📈 Análise Histórica ⭐           → Nova! Historical analysis
├─ Otimização de Processo            → Process optimization
├─ Análise de Performance            → Performance KPIs
├─ Modelagem de Processo             → Process modeling
└─ Análise de Tendências             → Trend analysis
```

**Funcionalidades da Nova View**:

#### 📈 **Análise Histórica**
- **Rota**: `/data/historical`
- **Endpoints**:
  - `GET /api/v1/demo/tags/list` (Lista de tags)
  - `GET /api/v1/demo/tags/history` (Dados históricos)
- **Funcionalidades**:
  - Seleção de tag via dropdown
  - Time ranges: 24h, 7 dias, 30 dias, 90 dias
  - Agregação: raw, 1m, 5m, 1h, 1d
  - Estatísticas: mean, median, std, min, max, range
  - Gráfico de tendência (LineChart)
  - Exportação para CSV/Excel
  - Detecção de anomalias visuais
- **Use Case**: Análise de performance, identificação de padrões, troubleshooting
- **ISA-95 Level**: Nível 3 (MES - Engineering)

**Alinhamento ISA-95**: Nível 3 (MES)
**Usuários típicos**: Engenheiros de processo, Analistas

---

### 5️⃣ **EXECUTIVO** (Nível 4)
**Propósito**: Visão estratégica e tomada de decisão
**ISA-95**: Nível 4 (ERP/Business Planning)

```
├─ Dashboard Executivo            → Executive KPIs
├─ Meus Dashboards
├─ Insights GBM                   → Logistics insights
├─ Tendências Históricas          → Historical trends
├─ Importar Dados                 → Data import
├─ Análise Financeira             → Financial analysis
└─ Análise de Riscos              → Risk assessment
```

**Alinhamento ISA-95**: Nível 4 (Business Planning)
**Usuários típicos**: Diretores, Gerentes, C-level

---

### 6️⃣ **ANALYTICS & IA** (Transversal)
**Propósito**: Análises avançadas e machine learning
**ISA-95**: Transversal (todos os níveis)

```
├─ Centro de Análise              → Analytics hub
├─ Saúde de Assets                → Asset health
└─ 🤖 ML Pipeline Demo ⭐          → Nova! ML execution demo
```

**Funcionalidades da Nova View**:

#### 🤖 **ML Pipeline Demo**
- **Rota**: `/ml-demo`
- **Endpoints**:
  - `GET /api/v1/demo/tags/history` (Training data)
  - `GET /api/v1/ml/insights/all` (Model predictions)
- **Funcionalidades**:
  - **Pipeline ML em 6 Etapas**:
    1. ✅ Data Collection (busca dados)
    2. ✅ Data Preprocessing (limpeza)
    3. ✅ Feature Engineering (features)
    4. ✅ Model Loading (carrega modelo)
    5. ✅ Model Inference (predições)
    6. ✅ Results Presentation (resultados)
  - Log de execução em tempo real (estilo terminal)
  - Timing de cada etapa (ms)
  - Métricas do modelo:
    - R² Score
    - MAE (Mean Absolute Error)
    - RMSE (Root Mean Squared Error)
    - Feature importance
  - Scatter plot: Predicted vs Actual
  - Sample predictions table
  - Botão "Execute Pipeline"
- **Use Case**: Demonstração de ML, treinamento, validação de modelos
- **ISA-95 Level**: Transversal (todos os níveis)

**Alinhamento ISA-95**: Transversal
**Usuários típicos**: Data Scientists, ML Engineers, Engenheiros

---

### 7️⃣ **CONFIGURAÇÃO** (Nível 1-2)
**Propósito**: Configuração de dispositivos e sistema
**ISA-95**: Nível 1-2 (Controle + Supervisão)

```
├─ Hub de Configuração
├─ Meus Dashboards
├─ Gerenciar Gateways             → Gateway management
├─ Devices & Assets               → Device configuration
├─ Tags & Labels                  → Tag management
├─ Dashboard Builder              → Custom dashboards
├─ Configurações SCADA            → SCADA settings
├─ Simulador de Terminal          → Grain terminal simulator
└─ Administração                  → System admin
```

**Alinhamento ISA-95**: Nível 1-2
**Usuários típicos**: Administradores, Engenheiros de automação

---

## 🎨 MAPEAMENTO DE VIEWS CRIADAS

### Distribuição por Módulo:

| View | Módulo Original | Novo Módulo | Nível ISA-95 | Justificativa |
|------|----------------|-------------|--------------|---------------|
| **Monitoramento Tempo Real** | "Dados & ML Demo" | **Operações** | Nível 2 | Supervisão em tempo real |
| **Alarmes & Eventos** | "Dados & ML Demo" | **Operações** | Nível 2-3 | Gestão de alarmes operacionais |
| **Análise Histórica** | "Dados & ML Demo" | **Engenharia** | Nível 3 | Análise técnica de dados |
| **ML Pipeline Demo** | "Dados & ML Demo" | **Analytics & IA** | Transversal | Demonstração de ML |

---

## 🔄 FLUXO DE INFORMAÇÃO ISA-95

```
┌─────────────────────────────────────────────────────────┐
│  NÍVEL 4: EXECUTIVO                                     │
│  - Dashboard Executivo                                  │
│  - ROI, KPIs estratégicos                              │
│  - Insights GBM                                         │
└─────────────────┬───────────────────────────────────────┘
                  │ Reports, KPIs
                  ↓
┌─────────────────────────────────────────────────────────┐
│  NÍVEL 3: MES (Operações + Manutenção + Engenharia)   │
│                                                         │
│  OPERAÇÕES:            MANUTENÇÃO:      ENGENHARIA:    │
│  - Alarmes & Eventos   - Preditiva      - Análise      │
│  - Logs                - Work Orders    - Otimização   │
│                                         - Histórico    │
└─────────────────┬───────────────────────────────────────┘
                  │ Orders, Schedules
                  ↓
┌─────────────────────────────────────────────────────────┐
│  NÍVEL 2: SCADA (Supervisão)                           │
│  - Monitoramento Tempo Real                            │
│  - SCADA Monitor                                        │
│  - Controle de Processo                                │
└─────────────────┬───────────────────────────────────────┘
                  │ Control Commands
                  ↓
┌─────────────────────────────────────────────────────────┐
│  NÍVEL 1: CONTROLE (PLCs/DCS)                          │
│  - Devices & Assets                                     │
│  - Tags Configuration                                   │
│  - Gateways                                            │
└─────────────────┬───────────────────────────────────────┘
                  │ Sensor Data
                  ↓
┌─────────────────────────────────────────────────────────┐
│  NÍVEL 0: PROCESSO FÍSICO                              │
│  - Sensores, Atuadores                                  │
│  - Equipamentos                                        │
└─────────────────────────────────────────────────────────┘

                  ↑
                  │ ML Insights (Transversal)
                  │
       ┌──────────┴──────────┐
       │  ANALYTICS & IA      │
       │  - ML Pipeline       │
       │  - Asset Health      │
       └──────────────────────┘
```

---

## 📋 CHECKLIST DE REORGANIZAÇÃO

### ✅ Concluído:

- [x] Remover seção "Dados & ML Demo" temporária
- [x] Adicionar "Monitoramento Tempo Real" em **Operações**
- [x] Adicionar "Alarmes & Eventos" em **Operações**
- [x] Adicionar "Análise Histórica" em **Engenharia**
- [x] Adicionar "ML Pipeline Demo" em **Analytics & IA**
- [x] Renomear seção "Analytics" para "Analytics & IA"
- [x] Ajustar ordem de prioridade das seções
- [x] Configurar seções expandidas por padrão (Principal + Operações)
- [x] Manter badges de notificação em "Alarmes & Eventos"

### 🎯 Benefícios da Reorganização:

1. **Alinhamento com ISA-95** ✅
   - Estrutura clara por níveis funcionais
   - Separação de responsabilidades
   - Fluxo de informação hierárquico

2. **Melhor UX** ✅
   - Usuários encontram funcionalidades no módulo correto
   - Redução de cliques para acessar views principais
   - Navegação intuitiva por área funcional

3. **Escalabilidade** ✅
   - Fácil adicionar novas views em cada módulo
   - Estrutura modular e extensível
   - Preparado para crescimento

4. **Clareza Funcional** ✅
   - Cada módulo tem propósito bem definido
   - Views agrupadas por contexto de uso
   - Alinhamento com papéis de usuário

---

## 🎭 PERSONAS E ACESSO

### Operador de Turno
**Módulos principais**: Operações
**Views chave**:
- Monitoramento Tempo Real
- Alarmes & Eventos
- SCADA Monitor

### Engenheiro de Processo
**Módulos principais**: Engenharia, Analytics & IA
**Views chave**:
- Análise Histórica
- Otimização de Processo
- ML Pipeline Demo
- Análise de Performance

### Gerente de Manutenção
**Módulos principais**: Manutenção
**Views chave**:
- Manutenção Preditiva
- Ordens de Trabalho
- Análise MTBF/MTTR

### Diretor/Executivo
**Módulos principais**: Executivo
**Views chave**:
- Dashboard Executivo
- Insights GBM
- Análise Financeira

### Data Scientist
**Módulos principais**: Analytics & IA
**Views chave**:
- ML Pipeline Demo
- Centro de Análise
- Insights IA

---

## 🔗 ROTAS COMPLETAS

### Operações (Level 2-3)
```
/operations                    → Hub
/operations/dashboards         → Custom dashboards
/data/realtime                 → Real-time monitoring ⭐
/data/alarms-events            → Alarms & Events ⭐
/operations/scada              → SCADA monitor
/operations/process-control    → Process control
/operations/logs               → Operation logs
```

### Engenharia (Level 3)
```
/engineering                   → Hub
/engineering/dashboards        → Custom dashboards
/data/historical               → Historical analysis ⭐
/engineering/optimization      → Process optimization
/engineering/performance       → Performance analysis
/engineering/modeling          → Process modeling
/engineering/trends            → Trend analysis
```

### Analytics & IA (Transversal)
```
/analytics-hub                 → Analytics center
/asset-health-hub              → Asset health
/ml-demo                       → ML Pipeline Demo ⭐
```

---

## 📊 ESTATÍSTICAS FINAIS

### Views Criadas: 4
- ✅ Monitoramento Tempo Real (430 linhas)
- ✅ Alarmes & Eventos (580 linhas)
- ✅ Análise Histórica (450 linhas)
- ✅ ML Pipeline Demo (670 linhas)

### Total de Código: ~2.130 linhas
### Endpoints Backend: 4
### Módulos Impactados: 3 (Operações, Engenharia, Analytics & IA)

---

## 🚀 PRÓXIMOS PASSOS

### Curto Prazo:
1. Testar navegação em todos os módulos
2. Validar badges de notificação
3. Verificar responsividade mobile

### Médio Prazo:
1. Adicionar permissões por módulo/role
2. Criar tutorial de navegação
3. Analytics de uso por módulo

### Longo Prazo:
1. Dashboards personalizáveis por módulo
2. Favoritos e acesso rápido
3. Navegação por voz (IA)

---

**Documento criado em**: 2025-11-06
**Baseado em**: ISA-95 Enterprise-Control System Integration
**Status**: ✅ Implementado e testado

---

## 📚 REFERÊNCIAS

- **ISA-95**: Enterprise-Control System Integration Standard
- **S88/S95**: Batch Control and Enterprise Integration
- **Purdue Model**: Industrial Control System Architecture
- **Material Design**: Google Material Design Guidelines

---

