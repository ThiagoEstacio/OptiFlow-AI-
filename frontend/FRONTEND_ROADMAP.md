# 🎨 SmartPort Frontend Development Roadmap

Este documento contém o plano completo para desenvolver o frontend do SmartPort MVP em 6 semanas (Week 3-8 do plano original).

---

## 📊 Status Atual

```yaml
✅ CONCLUÍDO:
  - Projeto React + TypeScript + Vite configurado
  - TailwindCSS 3.4 com tema SmartPort customizado
  - Dependências instaladas (Recharts, Framer Motion, Radix UI)
  - Estrutura de pastas criada
  - Utilidades básicas (cn, formatNumber, getStatusColor)

⏳ PRÓXIMOS PASSOS:
  - Criar componentes UI base
  - Implementar API client
  - Construir layout (Header, Sidebar)
  - Desenvolver páginas (Dashboard, Vessels, Loading)
```

---

## 🎯 Roadmap Detalhado - 6 Semanas

### **Week 3: Foundation & Dashboard** (5 dias)

#### Dia 1-2: Componentes Base UI
```
frontend/src/components/ui/
├── Button.tsx         # Botões (primary, secondary, danger, ghost)
├── Card.tsx          # Cards com header opcional
├── Badge.tsx         # Status badges
├── Input.tsx         # Input de texto
├── Select.tsx        # Dropdown/Select
├── Skeleton.tsx      # Loading states
├── Tooltip.tsx       # Tooltips (Radix UI)
└── ProgressBar.tsx   # Barra de progresso
```

#### Dia 3-4: API Client & Services
```
frontend/src/services/
├── api.ts            # Axios instance configurado
├── port/
│   ├── vesselService.ts     # CRUD vessels
│   ├── berthService.ts      # CRUD berths
│   ├── operationService.ts  # CRUD operations + control
│   └── analyticsService.ts  # KPIs e metrics
└── types.ts          # TypeScript types
```

#### Dia 5: Layout & Navigation
```
frontend/src/components/layout/
├── Header.tsx        # Header com logo, search, user menu
├── Sidebar.tsx       # Navegação lateral
├── MainLayout.tsx    # Layout wrapper
└── BreadCrumb.tsx    # Navegação breadcrumb
```

---

### **Week 4: Dashboard & Vessel Management** (5 dias)

#### Dia 1-2: Port Dashboard Components
```
frontend/src/components/port/
├── KPICard.tsx           # Card de KPI com ícone e trend
├── BerthCard.tsx         # Card de berço com status
├── EquipmentCard.tsx     # Card de equipamento
└── StatusIndicator.tsx   # Indicador animado de status
```

#### Dia 2-3: Port Dashboard Page
```
frontend/src/pages/port/
└── PortDashboard.tsx

Layout:
┌────────────────────────────────────┐
│ 🚢 SmartPort | Terminal Santos    │
├────────────────────────────────────┤
│  KPIs (4 cards em grid)            │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ │
│  │Vazão│ │Efic.│ │Navios│ │Alert│ │
│  └─────┘ └─────┘ └─────┘ └─────┘ │
│                                     │
│  Gráfico: Vazão + Energia (48h)   │
│  ┌────────────────────────────┐   │
│  │ [Recharts LineChart]       │   │
│  └────────────────────────────┘   │
│                                     │
│  Status de Berços (2 cards)        │
│  Equipamentos Críticos (3 cards)   │
└────────────────────────────────────┘
```

#### Dia 4-5: Vessel Management
```
frontend/src/pages/port/
├── VesselManagement.tsx   # Lista de navios
└── VesselDetail.tsx       # Detalhes do navio

Componentes:
├── VesselTable.tsx        # Tabela (@tanstack/react-table)
├── VesselForm.tsx         # Formulário create/edit
└── VesselTimeline.tsx     # Timeline ETA→ETD
```

---

### **Week 5: Loading Control & Real-Time** (5 dias)

#### Dia 1-3: Loading Control Page
```
frontend/src/pages/port/
└── LoadingControl.tsx

Layout:
┌────────────────────────────────────┐
│ Operação - MV GRAIN CARRIER        │
├────────────────────────────────────┤
│ Status: 🟢 EM ANDAMENTO            │
│                                     │
│ Progresso: ████████░░░ 65%        │
│ 48.750 / 75.000 ton                │
│                                     │
│ ┌────┐ ┌────┐ ┌────┐              │
│ │Vazão│ │Tempo│ │Efic│              │
│ │1850t│ │14h  │ │91.5│              │
│ └────┘ └────┘ └────┘              │
│                                     │
│ Fluxograma de Equipamentos         │
│ [Silo] → [TC] → [EL] → [SL]       │
│                                     │
│ Timeline de Eventos                 │
└────────────────────────────────────┘

Componentes:
├── OperationProgress.tsx    # Barra de progresso animada
├── MetricCard.tsx           # Card de métrica tempo real
├── EquipmentFlow.tsx        # Fluxograma (react-flow)
└── EventTimeline.tsx        # Timeline de eventos
```

#### Dia 4-5: WebSocket Integration
```
frontend/src/hooks/
└── useWebSocket.ts          # Hook para updates real-time

frontend/src/services/
└── websocket.ts             # WebSocket client
```

---

### **Week 6: Predictive Maintenance & AI** (5 dias)

#### Dia 1-3: Predictive Maintenance Page
```
frontend/src/pages/port/
└── PredictiveMaintenance.tsx

Layout:
┌────────────────────────────────────┐
│ Manutenção Preditiva               │
├────────────────────────────────────┤
│ Alertas Ativos: 3                  │
│                                     │
│ ┌────────────────────────────────┐│
│ │🔴 ALTA PRIORIDADE              ││
│ │                                 ││
│ │TC2521 - Correia Transferência  ││
│ │Probabilidade Falha: 82%        ││
│ │Tempo Estimado: 24-48h          ││
│ │                                 ││
│ │Sinais:                          ││
│ │• Corrente: 445A (↑18%)        ││
│ │• Temperatura: 48°C (↑14%)      ││
│ │• Vibração: 4.2mm/s (↑35%)      ││
│ │                                 ││
│ │ROI Preventiva:                  ││
│ │• Custo: R$ 15.000              ││
│ │• Economia: R$ 72.000           ││
│ │                                 ││
│ │[Agendar] [Ver SHAP]            ││
│ └────────────────────────────────┘│
│                                     │
│ Saúde dos Equipamentos             │
│ TC4515:  ████████░░ 95%           │
│ TC2521:  █████░░░░░ 72% ⚠️        │
└────────────────────────────────────┘

Componentes:
├── PredictionAlert.tsx      # Card de alerta preditivo
├── HealthBar.tsx            # Barra de saúde
├── SHAPChart.tsx            # Gráfico SHAP (Plotly)
└── ROIComparison.tsx        # Comparação preventiva vs corretiva
```

#### Dia 4-5: AI Insights Page
```
frontend/src/pages/port/
└── AIInsights.tsx

Componentes:
├── InsightCard.tsx          # Card de insight
├── OpportunityCard.tsx      # Card de oportunidade
├── AnomalyChart.tsx         # Gráfico de anomalias
└── ChatbotWidget.tsx        # Widget de chat (canto direito)
```

---

### **Week 7: Reports & Export** (4 dias)

#### Dia 1-2: Reports Page
```
frontend/src/pages/port/
└── Reports.tsx

frontend/src/components/port/
├── ReportBuilder.tsx        # Construtor de relatórios
├── ReportPreview.tsx        # Preview do relatório
└── ReportExport.tsx         # Opções de export
```

#### Dia 3-4: PDF & Excel Generation
```
frontend/src/utils/
├── pdfGenerator.ts          # jsPDF + html2canvas
└── excelGenerator.ts        # xlsx library

Tipos de Relatórios:
1. Relatório Diário de Operações
2. Relatório de Performance por Navio
3. Relatório de Downtime
4. Relatório de Eficiência Energética
5. Relatório Executivo Mensal
```

---

### **Week 8: Polish & Optimization** (5 dias)

#### Dia 1-2: Responsividade
- Testar em desktop (1920x1080, 1366x768)
- Testar em tablet (iPad, Android)
- Ajustar breakpoints
- Testar gráficos responsivos

#### Dia 3-4: Performance
- Lazy loading de páginas
- Memoização de componentes
- React Query para caching
- Compressão de imagens

#### Dia 5: UX Final
- Loading states
- Error states
- Empty states
- Toasts de notificação
- Confirmações

---

## 📦 Componentes UI Base - Specs

### Button Component
```tsx
// frontend/src/components/ui/Button.tsx

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  icon?: React.ReactNode;
}

Variants:
- primary: bg-primary-600 hover:bg-primary-700
- secondary: bg-dark-700 hover:bg-dark-600
- danger: bg-danger-600 hover:bg-danger-700
- ghost: hover:bg-dark-700
- outline: border-2 border-primary-600
```

### Card Component
```tsx
// frontend/src/components/ui/Card.tsx

interface CardProps {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
}

Estilo:
- Dark mode: bg-dark-800 border border-dark-700
- Hover: hover:bg-dark-750 transition
- Rounded: rounded-lg
- Padding: p-6
```

### Badge Component
```tsx
// frontend/src/components/ui/Badge.tsx

interface BadgeProps {
  children: React.ReactNode;
  variant: 'success' | 'warning' | 'danger' | 'info' | 'default';
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;  // Ponto animado
}

Variants com cores semânticas do tema
```

---

## 🔌 API Service Template

```typescript
// frontend/src/services/port/vesselService.ts

import api from '../api';
import { Vessel, VesselCreate, VesselUpdate } from '@/types/port';

export const vesselService = {
  // List vessels
  list: async (params?: {
    site_id?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }) => {
    const { data } = await api.get<Vessel[]>('/port/vessels', { params });
    return data;
  },

  // Get vessel by ID
  getById: async (id: string) => {
    const { data } = await api.get<Vessel>(`/port/vessels/${id}`);
    return data;
  },

  // Create vessel
  create: async (vessel: VesselCreate) => {
    const { data } = await api.post<Vessel>('/port/vessels', vessel);
    return data;
  },

  // Update vessel
  update: async (id: string, vessel: VesselUpdate) => {
    const { data } = await api.put<Vessel>(`/port/vessels/${id}`, vessel);
    return data;
  },

  // Delete vessel
  delete: async (id: string) => {
    await api.delete(`/port/vessels/${id}`);
  },

  // Get vessel operations
  getOperations: async (id: string) => {
    const { data } = await api.get(`/port/vessels/${id}/operations`);
    return data;
  },

  // Update status
  updateStatus: async (id: string, status: string) => {
    const { data } = await api.patch(`/port/vessels/${id}/status`, { status });
    return data;
  },
};
```

---

## 🎨 Design System - Padrões

### Colors
```
Primary:   #3b82f6 (Blue)
Success:   #22c55e (Green)
Warning:   #f59e0b (Orange)
Danger:    #ef4444 (Red)
Dark:      #0f172a, #1e293b, #334155
```

### Typography
```
Headings:  font-bold text-white
Body:      font-normal text-dark-200
Muted:     text-dark-400
```

### Spacing
```
Card padding:   p-6
Section gap:    space-y-6
Grid gap:       gap-4
```

### Animations
```
fade-in:    animate-fade-in
slide-up:   animate-slide-up
pulse-slow: animate-pulse-slow
```

---

## 🔧 Instalação de Dependências

```bash
cd frontend

# Instalar dependências
npm install

# Dependências já incluídas no package.json:
✅ framer-motion
✅ @radix-ui/react-dialog
✅ @radix-ui/react-dropdown-menu
✅ @radix-ui/react-tabs
✅ @radix-ui/react-tooltip
✅ @radix-ui/react-select
✅ @radix-ui/react-progress
✅ react-hot-toast

# Iniciar dev server
npm run dev
```

---

## 📝 Próximos Passos Imediatos

1. **Criar componentes UI base** (Button, Card, Badge, Input)
2. **Configurar API client** com axios e tipos
3. **Implementar layout** (Header, Sidebar, MainLayout)
4. **Criar Port Dashboard** com KPI cards
5. **Implementar Vessel Management** com tabela
6. **Desenvolver Loading Control** com real-time updates

---

## 🎯 Templates de Código Prontos

### KPI Card Component
```tsx
// frontend/src/components/port/KPICard.tsx

interface KPICardProps {
  title: string;
  value: number;
  unit: string;
  trend?: number;  // Percentual de mudança
  icon?: React.ReactNode;
  format?: 'number' | 'percent' | 'decimal';
}

export function KPICard({ title, value, unit, trend, icon, format }: KPICardProps) {
  const formattedValue = format === 'percent'
    ? formatPercent(value)
    : formatNumber(value, format === 'decimal' ? 1 : 0);

  const trendColor = trend && trend > 0
    ? 'text-success-500'
    : trend && trend < 0
    ? 'text-danger-500'
    : 'text-dark-400';

  return (
    <Card className="relative overflow-hidden">
      {/* Glow effect background */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary-600/10 to-transparent" />

      <div className="relative">
        <div className="flex items-start justify-between mb-2">
          <p className="text-dark-400 text-sm font-medium">{title}</p>
          {icon && <div className="text-primary-500">{icon}</div>}
        </div>

        <div className="flex items-baseline gap-2">
          <h3 className="text-3xl font-bold text-white">
            {formattedValue}
          </h3>
          <span className="text-dark-400 text-lg">{unit}</span>
        </div>

        {trend !== undefined && (
          <div className={cn('flex items-center gap-1 mt-2 text-sm', trendColor)}>
            {trend > 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
            <span>{Math.abs(trend)}%</span>
          </div>
        )}
      </div>
    </Card>
  );
}
```

---

## 📊 Estrutura Completa de Arquivos

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/               # Componentes base
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Tabs.tsx
│   │   │   ├── Table.tsx
│   │   │   ├── Skeleton.tsx
│   │   │   ├── Tooltip.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   └── EmptyState.tsx
│   │   │
│   │   ├── port/             # SmartPort specific
│   │   │   ├── KPICard.tsx
│   │   │   ├── VesselCard.tsx
│   │   │   ├── BerthCard.tsx
│   │   │   ├── EquipmentCard.tsx
│   │   │   ├── OperationProgress.tsx
│   │   │   ├── MetricCard.tsx
│   │   │   ├── StatusIndicator.tsx
│   │   │   ├── VesselTable.tsx
│   │   │   ├── VesselForm.tsx
│   │   │   ├── EventTimeline.tsx
│   │   │   ├── PredictionAlert.tsx
│   │   │   └── HealthBar.tsx
│   │   │
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── MainLayout.tsx
│   │   │   └── Breadcrumb.tsx
│   │   │
│   │   └── charts/
│   │       ├── LineChart.tsx
│   │       ├── BarChart.tsx
│   │       ├── AreaChart.tsx
│   │       └── GaugeChart.tsx
│   │
│   ├── pages/
│   │   └── port/
│   │       ├── PortDashboard.tsx
│   │       ├── VesselManagement.tsx
│   │       ├── VesselDetail.tsx
│   │       ├── LoadingControl.tsx
│   │       ├── PredictiveMaintenance.tsx
│   │       ├── AIInsights.tsx
│   │       └── Reports.tsx
│   │
│   ├── services/
│   │   ├── api.ts
│   │   └── port/
│   │       ├── vesselService.ts
│   │       ├── berthService.ts
│   │       ├── operationService.ts
│   │       ├── analyticsService.ts
│   │       └── equipmentService.ts
│   │
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useVessels.ts
│   │   ├── useOperations.ts
│   │   └── useAnalytics.ts
│   │
│   ├── types/
│   │   ├── port.ts
│   │   ├── api.ts
│   │   └── common.ts
│   │
│   ├── lib/
│   │   └── utils.ts  ✅ CRIADO
│   │
│   └── utils/
│       ├── dateFormatters.ts
│       ├── pdfGenerator.ts
│       └── excelGenerator.ts
│
├── package.json        ✅ ATUALIZADO
├── tailwind.config.js  ✅ CUSTOMIZADO
└── vite.config.ts
```

---

## 🚀 Como Continuar

### Passo 1: Criar Componentes UI Base (2-3 horas)
```bash
# Criar os 10 componentes UI essenciais
# Use os templates deste documento
```

### Passo 2: Configurar API Client (1 hora)
```bash
# Criar axios instance
# Criar services para vessels, berths, operations
```

### Passo 3: Implementar Layout (2 horas)
```bash
# Header + Sidebar + MainLayout
# Routing com react-router-dom
```

### Passo 4: Port Dashboard (1 dia)
```bash
# 4 KPI cards
# Gráfico de tendência (Recharts)
# Status de berços
# Equipamentos críticos
```

---

**🎨 SmartPort Frontend está pronto para ser desenvolvido!**

**Backend completo ✅ + Frontend configurado ✅ = Pronto para Week 3-8!**

---

*Documento gerado com Claude Code*
*https://claude.com/claude-code*
