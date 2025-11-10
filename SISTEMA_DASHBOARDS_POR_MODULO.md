# 📊 Sistema de Dashboards Customizados por Módulo ISA-95

## 🎯 Visão Geral

Cada módulo funcional (Operações, Manutenção, Engenharia, Executivo) poderá criar e gerenciar seus próprios dashboards customizados, com widgets específicos para suas necessidades.

---

## 🏗️ Arquitetura do Sistema

### **Conceito: Dashboards Contextuais**

```
OptiFlow AI Platform
│
├── 🏠 Principal
│   └── Dashboard Global (visão geral de tudo)
│
├── ⚙️ Operações
│   ├── Hub de Operações (overview do módulo)
│   ├── SCADA Monitor (real-time)
│   └── 📊 Meus Dashboards          ← NOVO!
│       ├── Dashboard: Turno A
│       ├── Dashboard: Turno B
│       ├── Dashboard: Noturno
│       └── Dashboard: Final de Semana
│
├── 🔧 Manutenção
│   ├── Hub de Manutenção
│   └── 📊 Meus Dashboards          ← NOVO!
│       ├── Dashboard: KPIs MTBF/MTTR
│       ├── Dashboard: Ordens Críticas
│       └── Dashboard: Planejamento Semanal
│
├── 🛠️ Engenharia
│   ├── Hub de Engenharia
│   └── 📊 Meus Dashboards          ← NOVO!
│       ├── Dashboard: Otimização
│       ├── Dashboard: Performance
│       └── Dashboard: Análise Mensal
│
└── 👔 Executivo
    ├── Dashboard Executivo (principal)
    └── 📊 Meus Dashboards          ← NOVO!
        ├── Dashboard: Board Meeting
        ├── Dashboard: KPIs Estratégicos
        └── Dashboard: ROI & Custos
```

---

## 📐 Estrutura de Dados

### **1. Dashboard Model (Backend)**

```python
# backend/app/models/dashboard.py

from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum

class DashboardModule(str, enum.Enum):
    """ISA-95 Modules"""
    OPERATIONS = "operations"
    MAINTENANCE = "maintenance"
    ENGINEERING = "engineering"
    EXECUTIVE = "executive"
    ANALYTICS = "analytics"
    GLOBAL = "global"

class Dashboard(Base):
    __tablename__ = "dashboards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # ISA-95 Module assignment
    module = Column(Enum(DashboardModule), nullable=False, index=True)

    # Who can see this dashboard
    is_public = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"))

    # Dashboard configuration
    layout = Column(JSON)  # Grid layout configuration
    widgets = Column(JSON)  # Widget configurations
    filters = Column(JSON)  # Default filters
    refresh_interval = Column(Integer, default=30)  # seconds

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    creator = relationship("User", back_populates="dashboards")
    shares = relationship("DashboardShare", back_populates="dashboard")

class DashboardShare(Base):
    """Share dashboards with specific users or roles"""
    __tablename__ = "dashboard_shares"

    id = Column(Integer, primary_key=True)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role = Column(String, nullable=True)  # 'operator', 'engineer', 'manager'

    dashboard = relationship("Dashboard", back_populates="shares")
    user = relationship("User")
```

### **2. Dashboard Schema (TypeScript)**

```typescript
// frontend/src/types/dashboard.ts

export type DashboardModule =
  | 'operations'
  | 'maintenance'
  | 'engineering'
  | 'executive'
  | 'analytics'
  | 'global';

export interface Dashboard {
  id: number;
  name: string;
  description?: string;
  module: DashboardModule;
  isPublic: boolean;
  createdBy: number;
  layout: GridLayout;
  widgets: Widget[];
  filters: DashboardFilters;
  refreshInterval: number;
  createdAt: string;
  updatedAt?: string;
}

export interface GridLayout {
  cols: number;
  rows: number;
  gap: number;
  items: GridItem[];
}

export interface GridItem {
  id: string;
  x: number;
  y: number;
  w: number;  // width in grid units
  h: number;  // height in grid units
  minW?: number;
  minH?: number;
  maxW?: number;
  maxH?: number;
}

export interface Widget {
  id: string;
  type: WidgetType;
  title: string;
  config: WidgetConfig;
  dataSource: DataSource;
}

export type WidgetType =
  | 'line_chart'
  | 'bar_chart'
  | 'pie_chart'
  | 'gauge'
  | 'kpi_card'
  | 'table'
  | 'heatmap'
  | 'alarm_list'
  | 'work_order_list'
  | 'process_diagram';

export interface DashboardFilters {
  timeRange?: TimeRange;
  tags?: string[];
  equipment?: string[];
  severity?: string[];
}
```

---

## 🎨 Interface de Usuário

### **1. Navegação na Sidebar**

```typescript
// Adicionar em cada módulo:

{
  title: 'Operações',
  items: [
    { path: '/operations', label: 'Hub de Operações', icon: <OperationsIcon /> },
    { path: '/operations/scada', label: 'SCADA Monitor', icon: <MonitorIcon /> },
    { path: '/operations/dashboards', label: 'Meus Dashboards', icon: <DashboardIcon /> }, // ← NOVO!
    // ... outros items
  ],
}
```

### **2. Página: Meus Dashboards**

**Rota**: `/operations/dashboards` (e similar para outros módulos)

**Wireframe**:
```
┌────────────────────────────────────────────────────────────┐
│ [Breadcrumb] Home > Operações > Meus Dashboards            │
├────────────────────────────────────────────────────────────┤
│ 📊 Dashboards de Operações              [+ Novo Dashboard] │
│                                                             │
│ 🔍 Filtros:                                                │
│ [Todos] [Meus] [Compartilhados] [Públicos]                │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ 📊 Turno A - Recebimento                            │   │
│ │ Criado por: João Silva                              │   │
│ │ Atualizado: há 2 horas                              │   │
│ │ 4 widgets • Atualização: 30s                        │   │
│ │                                                      │   │
│ │ [Abrir] [Editar] [Duplicar] [Compartilhar] [🗑️]     │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ 📊 Turno B - Expedição                              │   │
│ │ Criado por: Maria Santos                            │   │
│ │ Atualizado: há 5 minutos                            │   │
│ │ 6 widgets • Atualização: 15s                        │   │
│ │                                                      │   │
│ │ [Abrir] [Editar] [Duplicar] [Compartilhar] [🗑️]     │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ 📊 Dashboard Noturno (Público)                      │   │
│ │ Criado por: Sistema                                 │   │
│ │ Compartilhado com: Todos operadores                 │   │
│ │ 8 widgets • Atualização: 60s                        │   │
│ │                                                      │   │
│ │ [Abrir] [Duplicar]                                  │   │
│ └─────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

### **3. Dashboard Builder Modal**

**Ao clicar em "+ Novo Dashboard"**:

```
┌───────────────────────────────────────────────────────┐
│ 📊 Criar Novo Dashboard                          [✕] │
├───────────────────────────────────────────────────────┤
│                                                       │
│ Nome do Dashboard:                                    │
│ [Dashboard Turno A___________________________]       │
│                                                       │
│ Descrição (opcional):                                │
│ [Monitoramento do turno A - Recebimento_______]     │
│ [_____________________________________________]     │
│                                                       │
│ Módulo:                                              │
│ ⚙️ Operações (selecionado automaticamente)          │
│                                                       │
│ Visibilidade:                                        │
│ ⚪ Privado (somente eu)                              │
│ ⚪ Compartilhado (selecionar usuários)               │
│ ⚪ Público (todos do módulo Operações)               │
│                                                       │
│ Layout Inicial:                                      │
│ ┌────┐ ┌────┐ ┌────┐                                │
│ │2x2 │ │3x2 │ │4x3 │                                │
│ └────┘ └────┘ └────┘                                │
│   4      6      12                                    │
│ widgets widgets widgets                               │
│                                                       │
│ Template (opcional):                                 │
│ [Em branco ▼]                                        │
│  • Em branco                                         │
│  • Template: SCADA Overview                          │
│  • Template: KPIs Operacionais                       │
│  • Template: Alarmes e Eventos                       │
│                                                       │
│              [Cancelar] [Criar Dashboard]            │
└───────────────────────────────────────────────────────┘
```

### **4. Dashboard Viewer**

**Rota**: `/operations/dashboards/:id`

```
┌────────────────────────────────────────────────────────────────┐
│ [Breadcrumb] Home > Operações > Meus Dashboards > Turno A     │
├────────────────────────────────────────────────────────────────┤
│ 📊 Turno A - Recebimento                                      │
│ [●Live - 30s] [⏸️ Pausar] [🔄 Atualizar] [⚙️ Editar] [⋮ Menu] │
│                                                                │
│ 🔍 Filtros: [Últimas 24h ▼] [Todos equipamentos ▼]           │
│                                                                │
│ ┌────────────────────────┬────────────────────────┐          │
│ │  📈 Taxa de Recebimento│  📊 Nível Armazém      │          │
│ │                        │                        │          │
│ │  1,250 t/h            │    85.3%               │          │
│ │  ▲ +5.2% vs ontem     │    ▲ +2.1% vs ontem    │          │
│ │                        │                        │          │
│ │  [Gráfico de linha]    │  [Gauge circular]      │          │
│ └────────────────────────┴────────────────────────┘          │
│                                                                │
│ ┌────────────────────────────────────────────────┐           │
│ │  🚨 Alarmes Ativos (5)                         │           │
│ │  ┌──────────────────────────────────────────┐ │           │
│ │  │ 🔴 Warehouse Level Critical - 5min atrás  │ │           │
│ │  │ 🟠 Moega 1 Temp High - 12min atrás        │ │           │
│ │  │ 🟡 Silo 5 Level Elevated - 30min atrás    │ │           │
│ │  └──────────────────────────────────────────┘ │           │
│ └────────────────────────────────────────────────┘           │
│                                                                │
│ ┌─────────────────────┬─────────────────────┐                │
│ │  ⚡ Equipamentos     │  📋 Eventos Recentes│                │
│ │                     │                     │                │
│ │  🟢 Moega 1: Running│  14:32 START Moega 1│                │
│ │  🟢 Moega 2: Running│  14:28 ACK Alarm    │                │
│ │  🔴 Moega 3: Stopped│  14:15 STOP Moega 3 │                │
│ │  🟢 Transport.: Run │  14:05 Manual Mode  │                │
│ └─────────────────────┴─────────────────────┘                │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Widgets Específicos por Módulo

### **Operações** (Real-Time Focus)

| Widget | Descrição | Dados |
|--------|-----------|-------|
| **Live Tag Value** | Valor de tag em tempo real | Tag específica |
| **Equipment Status** | Grid de status de equipamentos | Equipamentos do módulo |
| **Alarm List** | Lista de alarmes ativos | Alarmes filtrados |
| **Process Flow** | Diagrama de fluxo animado | Tags do processo |
| **Trend Chart** | Gráfico de tendência (últimas 24h) | Múltiplas tags |
| **Command History** | Histórico de comandos | Logs de comandos |
| **Production Counter** | Contador de produção | Totalização |

### **Manutenção** (Planning & Analysis)

| Widget | Descrição | Dados |
|--------|-----------|-------|
| **Work Order List** | Lista de ordens abertas | Ordens de trabalho |
| **MTBF/MTTR Chart** | Gráfico de confiabilidade | Histórico de falhas |
| **Failure Pareto** | Pareto de falhas | Top 10 falhas |
| **Calendar View** | Calendário de manutenções | Agendamentos |
| **Equipment Health** | Gauge de saúde de equipamentos | Score de ML |
| **Parts Inventory** | Estoque de peças | Inventário |
| **Technician Load** | Carga de trabalho por técnico | Alocações |

### **Engenharia** (Optimization & Performance)

| Widget | Descrição | Dados |
|--------|-----------|-------|
| **OEE Gauge** | Overall Equipment Effectiveness | Cálculo OEE |
| **Performance Trend** | Tendência de performance | Histórico 30 dias |
| **Optimization Chart** | Comparação antes/depois | Simulações |
| **Mass Balance** | Balanço de massa | Tags de fluxo |
| **Energy Dashboard** | Consumo energético | Tags de energia |
| **Correlation Matrix** | Matriz de correlação | Múltiplas tags |
| **Statistical Chart** | Histograma, boxplot, etc | Análise estatística |

### **Executivo** (KPIs & Strategic)

| Widget | Descrição | Dados |
|--------|-----------|-------|
| **KPI Card** | Card de KPI com meta | KPI específico |
| **Financial Chart** | Custos, receitas, ROI | Dados financeiros |
| **Production Summary** | Resumo de produção | Totalizações |
| **Risk Matrix** | Matriz de riscos | Análise de riscos |
| **Alerts Summary** | Resumo de alertas | Agregação de alarmes |
| **Trend Comparison** | Comparação mês a mês | Histórico mensal |
| **Health Score** | Score geral de saúde | Agregação ML |

---

## 🛠️ Implementação Técnica

### **1. API Endpoints**

```python
# backend/app/api/v1/endpoints/dashboards.py

from fastapi import APIRouter, Depends
from app.models.dashboard import Dashboard, DashboardModule

router = APIRouter()

@router.get("/modules/{module}/dashboards")
async def list_module_dashboards(
    module: DashboardModule,
    user: User = Depends(get_current_user)
):
    """List all dashboards for a specific module"""
    # Return user's dashboards + public dashboards for this module
    pass

@router.post("/modules/{module}/dashboards")
async def create_module_dashboard(
    module: DashboardModule,
    dashboard: DashboardCreate,
    user: User = Depends(get_current_user)
):
    """Create a new dashboard in a specific module"""
    pass

@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(dashboard_id: int):
    """Get dashboard configuration"""
    pass

@router.put("/dashboards/{dashboard_id}")
async def update_dashboard(dashboard_id: int, dashboard: DashboardUpdate):
    """Update dashboard configuration"""
    pass

@router.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(dashboard_id: int):
    """Delete dashboard"""
    pass

@router.post("/dashboards/{dashboard_id}/share")
async def share_dashboard(dashboard_id: int, share: DashboardShareCreate):
    """Share dashboard with users or roles"""
    pass

@router.get("/dashboards/{dashboard_id}/data")
async def get_dashboard_data(
    dashboard_id: int,
    time_range: Optional[str] = None
):
    """Get real-time data for all widgets in dashboard"""
    # Fetch data for all widgets in one request
    pass
```

### **2. Frontend Components**

```typescript
// frontend/src/pages/ModuleDashboards.tsx

interface ModuleDashboardsPageProps {
  module: DashboardModule;
}

export const ModuleDashboardsPage: React.FC<ModuleDashboardsPageProps> = ({ module }) => {
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [filter, setFilter] = useState<'all' | 'mine' | 'shared' | 'public'>('all');

  useEffect(() => {
    fetchModuleDashboards(module, filter);
  }, [module, filter]);

  return (
    <div>
      <PageHeader
        title={`Dashboards de ${getModuleLabel(module)}`}
        actions={
          <Button onClick={() => openCreateModal()}>
            + Novo Dashboard
          </Button>
        }
      />

      <DashboardFilters value={filter} onChange={setFilter} />

      <DashboardGrid dashboards={dashboards} module={module} />

      <CreateDashboardModal
        module={module}
        open={modalOpen}
        onClose={closeModal}
      />
    </div>
  );
};
```

```typescript
// frontend/src/components/DashboardViewer.tsx

interface DashboardViewerProps {
  dashboardId: number;
  editable?: boolean;
}

export const DashboardViewer: React.FC<DashboardViewerProps> = ({
  dashboardId,
  editable = false
}) => {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [data, setData] = useState<Record<string, any>>({});
  const [isPaused, setIsPaused] = useState(false);

  // Fetch dashboard config
  useEffect(() => {
    fetchDashboard(dashboardId);
  }, [dashboardId]);

  // Auto-refresh data
  useEffect(() => {
    if (!isPaused && dashboard) {
      const interval = setInterval(() => {
        fetchDashboardData(dashboardId);
      }, dashboard.refreshInterval * 1000);

      return () => clearInterval(interval);
    }
  }, [dashboardId, dashboard, isPaused]);

  return (
    <div>
      <DashboardHeader
        dashboard={dashboard}
        isPaused={isPaused}
        onPauseToggle={() => setIsPaused(!isPaused)}
        onRefresh={() => fetchDashboardData(dashboardId)}
        editable={editable}
      />

      <DashboardFilters
        filters={dashboard?.filters}
        onFilterChange={handleFilterChange}
      />

      <GridLayout layout={dashboard?.layout}>
        {dashboard?.widgets.map(widget => (
          <WidgetComponent
            key={widget.id}
            widget={widget}
            data={data[widget.id]}
            editable={editable}
          />
        ))}
      </GridLayout>
    </div>
  );
};
```

---

## 📋 Templates Pré-Configurados

### **Operações**

1. **SCADA Overview**
   - Live tag values (6 widgets)
   - Equipment status grid
   - Alarm list
   - Process flow diagram

2. **KPIs Operacionais**
   - Production rate
   - Efficiency gauge
   - Quality metrics
   - Downtime tracker

3. **Alarmes e Eventos**
   - Active alarms list
   - Alarm history chart
   - Event timeline
   - Top alarm sources

### **Manutenção**

1. **Gestão de Ordens**
   - Open work orders
   - Overdue orders
   - Completion rate
   - Technician load

2. **Análise de Confiabilidade**
   - MTBF trend
   - MTTR trend
   - Failure pareto
   - Equipment health scores

3. **Planejamento**
   - Maintenance calendar
   - Parts inventory
   - Scheduled vs unscheduled
   - Cost tracking

### **Engenharia**

1. **Performance Analysis**
   - OEE gauge
   - Availability/Performance/Quality
   - Trend charts (30 days)
   - Benchmark comparison

2. **Otimização de Processo**
   - Mass balance
   - Energy consumption
   - Process parameters
   - Optimization opportunities

3. **Análise Estatística**
   - Histograms
   - Control charts
   - Correlation matrix
   - Statistical summaries

### **Executivo**

1. **Board Meeting**
   - Key KPIs (4-6 cards)
   - Production summary
   - Financial overview
   - Risk highlights

2. **KPIs Estratégicos**
   - Strategic metrics
   - Month-over-month trends
   - Target vs actual
   - Health score

3. **ROI & Custos**
   - Cost breakdown
   - Revenue tracking
   - ROI calculation
   - Budget vs actual

---

## 🚀 Roadmap de Implementação

### **Fase 1: Infraestrutura Base** (1 semana)
- [ ] Criar model Dashboard no backend
- [ ] Criar API endpoints básicos
- [ ] Criar schemas TypeScript
- [ ] Setup de rotas no frontend

### **Fase 2: UI Básica** (1 semana)
- [ ] Página "Meus Dashboards" por módulo
- [ ] Modal de criação de dashboard
- [ ] Dashboard viewer básico
- [ ] Grid layout component

### **Fase 3: Widgets Core** (2 semanas)
- [ ] 5 widgets de Operações
- [ ] 5 widgets de Manutenção
- [ ] 5 widgets de Engenharia
- [ ] 5 widgets de Executivo

### **Fase 4: Features Avançadas** (1 semana)
- [ ] Compartilhamento de dashboards
- [ ] Templates pré-configurados
- [ ] Drag & drop builder
- [ ] Export/import de dashboards

### **Fase 5: Integração Sidebar** (2 dias)
- [ ] Adicionar "Meus Dashboards" em cada módulo
- [ ] Navegação rápida para dashboards favoritos
- [ ] Badge de contadores (ex: "5 dashboards")

---

## 📊 Exemplo de Uso

### **Cenário: Supervisor de Operações cria dashboard para seu turno**

1. **Navegação**:
   - Acessa: `Operações > Meus Dashboards`
   - Clica em: `+ Novo Dashboard`

2. **Configuração**:
   - Nome: "Turno A - Recebimento"
   - Descrição: "Monitoramento do turno A focado em recebimento"
   - Visibilidade: Público (todos operadores)
   - Template: "SCADA Overview"

3. **Customização**:
   - Adiciona widget: "Taxa de Recebimento" (KPI Card)
   - Adiciona widget: "Nível Armazém" (Gauge)
   - Adiciona widget: "Alarmes Críticos" (Alarm List)
   - Adiciona widget: "Status Moegas" (Equipment Grid)
   - Ajusta layout: Grid 2x2

4. **Compartilhamento**:
   - Dashboard fica visível para todos operadores
   - Aparece na lista de "Dashboards Públicos"
   - Outros podem duplicar e customizar

5. **Uso Diário**:
   - Operadores do turno A abrem dashboard
   - Visualização em tempo real (refresh 30s)
   - Podem pausar para analisar
   - Podem criar suas próprias versões

---

## 🎯 Benefícios

### **Para Operadores**
- ✅ Dashboards focados no contexto do turno
- ✅ Visualização de dados relevantes
- ✅ Sem poluição de informações de outros módulos

### **Para Engenheiros**
- ✅ Análises técnicas específicas
- ✅ Widgets de otimização e performance
- ✅ Dados históricos e estatísticos

### **Para Gestores**
- ✅ KPIs estratégicos consolidados
- ✅ Visão executiva sem detalhes operacionais
- ✅ Comparações e tendências

### **Para a Organização**
- ✅ Cada área com suas próprias ferramentas
- ✅ Reutilização de dashboards (templates)
- ✅ Compartilhamento de melhores práticas
- ✅ ISA-95 compliant

---

**Status**: 📋 Planejamento completo
**Próximo Passo**: Escolher fase para implementar
