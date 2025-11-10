# ⚙️ Especificação Detalhada - Módulo de Operações

## 📋 Visão Geral

O **Módulo de Operações** é responsável pelo monitoramento e controle em tempo real do terminal graneleiro, atendendo às necessidades do dia-a-dia operacional.

**Usuários-alvo**: Operadores de turno, supervisores de operação, despachantes

**Funcionalidades principais**:
- ✅ Monitoramento SCADA em tempo real
- ⚠️ Controle de processos e equipamentos
- ⚠️ Gestão de alarmes ativos
- ⚠️ Logs de operação e eventos

---

## 🎯 Telas do Módulo

### 1. ✅ **SCADA Monitor** (Já Existe)
**Rota**: `/operations/scada`
**Arquivo**: `SCADAPage.tsx`
**Status**: Implementado

**Descrição**: Visão geral SCADA do terminal com monitoramento em tempo real.

---

### 2. ⚠️ **Controle de Processo** (A Criar)
**Rota**: `/operations/process-control`
**Arquivo**: `ProcessControlPage.tsx`
**Status**: **NÃO EXISTE**

#### **Objetivo**
Permitir que operadores controlem manualmente equipamentos e processos, alterando setpoints e comandando equipamentos.

#### **Funcionalidades**

**A. Seletor de Área/Processo**
```
┌──────────────────────────────────────┐
│ Selecionar Processo:                 │
│ [Recebimento ▼] [Armazenagem ▼]     │
│                 [Expedição ▼]        │
└──────────────────────────────────────┘
```

**B. Grid de Equipamentos Controláveis**
```
┌─────────────────────────────────────────────────────┐
│ Equipamento       │ Status  │ Modo  │ Valor │ Ações │
├───────────────────┼─────────┼───────┼───────┼───────┤
│ 🔵 Moega 1        │ Running │ Auto  │ 75%   │ [⚙️]  │
│ 🔴 Comporta A1    │ Stopped │ Manual│  0%   │ [⚙️]  │
│ 🟢 Transportador 1│ Running │ Auto  │ 850t/h│ [⚙️]  │
│ 🟡 Silo 5         │ Warning │ Auto  │ 92%   │ [⚙️]  │
└─────────────────────────────────────────────────────┘
```

**C. Painel de Controle (ao clicar em ⚙️)**
```
┌─────────────────────────────────────┐
│ Controle: Moega 1                   │
├─────────────────────────────────────┤
│ Status Atual: Running               │
│ Modo: ⚫ Auto  ⚪ Manual            │
│                                     │
│ Capacidade Atual: 75%               │
│ [━━━━━━━━━━━━━━━━━━━━━━━] 75%     │
│                                     │
│ Setpoint: [80____] %                │
│                                     │
│ Comandos:                           │
│ [START] [STOP] [RESET]              │
│                                     │
│ Última Atualização: há 2s           │
│           [Aplicar] [Cancelar]      │
└─────────────────────────────────────┘
```

**D. Histórico de Comandos (Últimas 24h)**
```
┌────────────────────────────────────────────┐
│ 14:32:15 - Operador João: START Moega 1   │
│ 14:25:03 - Operador Maria: STOP Comporta  │
│ 13:58:42 - AUTO → MANUAL Transportador    │
└────────────────────────────────────────────┘
```

#### **Componentes a Criar**

1. **`<ProcessSelector />`**
   ```typescript
   interface ProcessSelectorProps {
     processes: Process[];
     selectedProcess: string;
     onSelect: (processId: string) => void;
   }
   ```

2. **`<EquipmentControlGrid />`**
   ```typescript
   interface EquipmentControlGridProps {
     equipments: Equipment[];
     onControlClick: (equipmentId: string) => void;
   }

   interface Equipment {
     id: string;
     name: string;
     status: 'running' | 'stopped' | 'warning' | 'error';
     mode: 'auto' | 'manual';
     currentValue: number;
     unit: string;
     tags: string[];
   }
   ```

3. **`<ControlPanel />`**
   ```typescript
   interface ControlPanelProps {
     equipment: Equipment;
     onCommand: (command: Command) => void;
     onSetpointChange: (value: number) => void;
     onModeChange: (mode: 'auto' | 'manual') => void;
   }

   interface Command {
     type: 'START' | 'STOP' | 'RESET' | 'EMERGENCY_STOP';
     timestamp: string;
     operator: string;
   }
   ```

4. **`<CommandHistory />`**
   ```typescript
   interface CommandHistoryProps {
     commands: CommandLog[];
     limit?: number;
   }

   interface CommandLog {
     timestamp: string;
     operator: string;
     equipment: string;
     command: string;
     success: boolean;
   }
   ```

#### **API Endpoints Necessários**

```typescript
// GET /api/v1/operations/equipments
// Retorna lista de equipamentos controláveis

// GET /api/v1/operations/equipments/:id
// Retorna detalhes de um equipamento

// POST /api/v1/operations/equipments/:id/command
// Body: { command: 'START' | 'STOP' | 'RESET', operator: string }

// POST /api/v1/operations/equipments/:id/setpoint
// Body: { value: number, operator: string }

// POST /api/v1/operations/equipments/:id/mode
// Body: { mode: 'auto' | 'manual', operator: string }

// GET /api/v1/operations/command-history
// Query: ?equipment_id=&start_time=&end_time=
```

#### **Wireframe Completo**

```
┌──────────────────────────────────────────────────────────────┐
│ [Breadcrumb] Home > Operações > Controle de Processo         │
├──────────────────────────────────────────────────────────────┤
│ ⚙️ Controle de Processo              [●Live] 14:32:15       │
│                                                               │
│ 🔧 Selecionar Processo:                                      │
│ ┌────────┐ ┌────────┐ ┌────────┐                            │
│ │Recebim.│ │Armazen.│ │Expediç.│                            │
│ └────────┘ └────────┘ └────────┘                            │
│                                                               │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                            │
│ │ 12  │ │  5  │ │  3  │ │  0  │                            │
│ │ Run │ │Stop │ │Warn │ │Error│                            │
│ └─────┘ └─────┘ └─────┘ └─────┘                            │
│                                                               │
│ 📊 Equipamentos Controláveis:                                │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Equip.          │ Status  │ Modo   │ Valor  │ Ações   │  │
│ ├─────────────────┼─────────┼────────┼────────┼─────────┤  │
│ │ 🔵 Moega 1      │ Running │ Auto   │ 75%    │ [⚙️][📊] │  │
│ │ 🔴 Comporta A1  │ Stopped │ Manual │  0%    │ [⚙️][📊] │  │
│ │ 🟢 Transport. 1 │ Running │ Auto   │ 850t/h │ [⚙️][📊] │  │
│ │ 🟡 Silo 5       │ Warning │ Auto   │ 92%    │ [⚙️][📊] │  │
│ └────────────────────────────────────────────────────────┘  │
│                                       [← Anterior] [Next →]  │
│                                                               │
│ 📜 Histórico de Comandos (Últimas 24h):                      │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ 14:32:15 - João Silva: START Moega 1                   │  │
│ │ 14:25:03 - Maria Santos: STOP Comporta A1              │  │
│ │ 13:58:42 - Sistema: AUTO → MANUAL Transportador 1      │  │
│ │ 13:45:20 - João Silva: SETPOINT 80% Moega 1            │  │
│ └────────────────────────────────────────────────────────┘  │
│                                          [Ver Tudo]          │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────┐ ← MODAL ao clicar [⚙️]
│ ⚙️ Controle: Moega 1            [✕]  │
├──────────────────────────────────────┤
│ 📊 Status Atual: Running             │
│                                      │
│ Modo de Operação:                    │
│ ⚫ Automático  ⚪ Manual             │
│                                      │
│ 📈 Capacidade Atual: 75.3%           │
│ ┌──────────────────────────────┐    │
│ │ [━━━━━━━━━━━━━━━━━━━━] 75%  │    │
│ └──────────────────────────────┘    │
│                                      │
│ Setpoint:                            │
│ [80________] % (min: 0, max: 100)   │
│                                      │
│ ⚡ Comandos Disponíveis:             │
│ ┌────────┐ ┌────────┐ ┌────────┐   │
│ │ START  │ │  STOP  │ │ RESET  │   │
│ └────────┘ └────────┘ └────────┘   │
│                                      │
│ ⚠️ [PARADA DE EMERGÊNCIA]           │
│                                      │
│ Tags Associadas:                     │
│ • ARZ_MOEGA_1_SPEED_PV               │
│ • ARZ_MOEGA_1_STATUS                 │
│ • ARZ_MOEGA_1_SETPOINT_SP            │
│                                      │
│ Última Atualização: há 2 segundos    │
│                                      │
│        [Aplicar] [Cancelar]          │
└──────────────────────────────────────┘
```

#### **Segurança e Validações**

1. **Confirmação de Comandos Críticos**
   ```
   ┌─────────────────────────────────┐
   │ ⚠️ Confirmação Necessária       │
   ├─────────────────────────────────┤
   │ Você está prestes a PARAR       │
   │ o equipamento: Moega 1          │
   │                                 │
   │ Esta ação pode afetar o         │
   │ processo de recebimento.        │
   │                                 │
   │ Deseja continuar?               │
   │                                 │
   │      [Sim, Parar] [Cancelar]    │
   └─────────────────────────────────┘
   ```

2. **Registro de Audit Trail**
   - Todo comando salvo no banco com timestamp, usuário, equipamento
   - Log enviado ao backend para auditoria

3. **Permissões por Usuário**
   - Operador: START, STOP, SETPOINT
   - Supervisor: + EMERGENCY_STOP, MODE_CHANGE
   - Engenheiro: Full access

---

### 3. ⚠️ **Alarmes Ativos** (A Criar)
**Rota**: `/operations/active-alarms`
**Arquivo**: `ActiveAlarmsPage.tsx`
**Status**: **NÃO EXISTE**

#### **Objetivo**
Exibir todos os alarmes ativos em tempo real, permitindo acknowledge, dismiss e análise.

#### **Funcionalidades**

**A. Contador de Alarmes por Severidade**
```
┌─────────────────────────────────────────────────────┐
│ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ │
│ │  🔴   │ │  🟠   │ │  🟡   │ │  🔵   │ │  ⚪   │ │
│ │   3   │ │   8   │ │  15   │ │  22   │ │  41   │ │
│ │Crítico│ │  Alto │ │ Médio │ │ Baixo │ │ Info  │ │
│ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘ │
└─────────────────────────────────────────────────────┘
```

**B. Filtros e Busca**
```
┌──────────────────────────────────────────────────────┐
│ 🔍 [Buscar alarmes...]                               │
│                                                       │
│ Severidade: [Todas ▼]  Categoria: [Todas ▼]         │
│ Estado: [Ativos ▼]     Área: [Todas ▼]              │
│                                                       │
│ [Limpar Filtros] [Aplicar]                           │
└──────────────────────────────────────────────────────┘
```

**C. Lista de Alarmes**
```
┌────────────────────────────────────────────────────────────────────┐
│ Sev │ Timestamp   │ Tag               │ Mensagem        │ Ações   │
├─────┼─────────────┼───────────────────┼─────────────────┼─────────┤
│ 🔴  │ 14:32:15    │ WAREHOUSE_LEVEL   │ Nível crítico   │ [ACK][✕]│
│ 🟠  │ 14:28:03    │ MOEGA_1_TEMP      │ Temperatura alta│ [ACK][✕]│
│ 🟡  │ 14:15:42    │ SILO_5_LEVEL      │ Nível elevado   │ [ACK][✕]│
│ 🔵  │ 13:58:20    │ GATE_A1_POS       │ Posição inválida│ [ACK][✕]│
└────────────────────────────────────────────────────────────────────┘
```

**D. Detalhes do Alarme (ao clicar)**
```
┌─────────────────────────────────────────┐
│ 🔴 Alarme Crítico                  [✕] │
├─────────────────────────────────────────┤
│ Tag: WAREHOUSE_LEVEL_PCT_PV             │
│ Mensagem: Nível crítico no armazém      │
│                                         │
│ Timestamp: 2025-11-05 14:32:15 UTC      │
│ Duração: 5 minutos 23 segundos          │
│                                         │
│ Valor Atual: 95.8%                      │
│ Limite: > 90%                           │
│                                         │
│ 📊 Gráfico de Tendência (últimas 2h):  │
│ ┌─────────────────────────────────────┐ │
│ │       /‾‾‾‾‾\                       │ │
│ │      /       \    ← ALARME          │ │
│ │     /         ‾‾‾‾‾                 │ │
│ │ ───┘                                │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Recomendações da IA:                    │
│ • Reduzir taxa de recebimento           │
│ • Iniciar expedição para Silo 3         │
│ • Verificar comportas de saída          │
│                                         │
│ Estado: ⚪ Não reconhecido              │
│                                         │
│ [Acknowledge] [Dismiss] [Ver Histórico] │
└─────────────────────────────────────────┘
```

**E. Ações em Massa**
```
┌──────────────────────────────────────┐
│ ☑️ 3 alarmes selecionados            │
│                                      │
│ [ACK Selecionados] [Dismiss Todos]  │
└──────────────────────────────────────┘
```

#### **Componentes a Criar**

1. **`<AlarmCounters />`**
   ```typescript
   interface AlarmCountersProps {
     alarms: Alarm[];
     onSeverityClick?: (severity: AlarmSeverity) => void;
   }

   type AlarmSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';
   ```

2. **`<AlarmFilters />`**
   ```typescript
   interface AlarmFiltersProps {
     onFilterChange: (filters: AlarmFilters) => void;
     initialFilters?: AlarmFilters;
   }

   interface AlarmFilters {
     severity?: AlarmSeverity[];
     category?: string[];
     state?: 'active' | 'acknowledged' | 'dismissed';
     area?: string[];
     searchTerm?: string;
   }
   ```

3. **`<AlarmTable />`**
   ```typescript
   interface AlarmTableProps {
     alarms: Alarm[];
     onAcknowledge: (alarmId: string) => void;
     onDismiss: (alarmId: string) => void;
     onRowClick: (alarm: Alarm) => void;
     selectable?: boolean;
     onSelectionChange?: (selectedIds: string[]) => void;
   }

   interface Alarm {
     id: string;
     severity: AlarmSeverity;
     timestamp: string;
     tag: string;
     message: string;
     value: number;
     limit: number;
     state: 'active' | 'acknowledged' | 'dismissed';
     acknowledgedBy?: string;
     acknowledgedAt?: string;
     dismissedBy?: string;
     dismissedAt?: string;
   }
   ```

4. **`<AlarmDetailModal />`**
   ```typescript
   interface AlarmDetailModalProps {
     alarm: Alarm;
     onClose: () => void;
     onAcknowledge: () => void;
     onDismiss: () => void;
   }
   ```

5. **`<AlarmTrendChart />`**
   ```typescript
   interface AlarmTrendChartProps {
     tagName: string;
     alarmTimestamp: string;
     timeRange?: number; // minutos antes/depois
   }
   ```

#### **API Endpoints Necessários**

```typescript
// GET /api/v1/operations/alarms/active
// Query: ?severity=&category=&state=&area=

// GET /api/v1/operations/alarms/:id

// POST /api/v1/operations/alarms/:id/acknowledge
// Body: { operator: string, notes?: string }

// POST /api/v1/operations/alarms/:id/dismiss
// Body: { operator: string, reason: string }

// POST /api/v1/operations/alarms/bulk-acknowledge
// Body: { alarmIds: string[], operator: string }

// GET /api/v1/operations/alarms/:id/trend
// Query: ?time_range_minutes=120
```

#### **WebSocket Events**

```typescript
// Cliente escuta:
socket.on('alarm:new', (alarm: Alarm) => {
  // Adicionar alarme à lista
  // Tocar som de alerta
  // Mostrar notificação
});

socket.on('alarm:updated', (alarm: Alarm) => {
  // Atualizar alarme existente
});

socket.on('alarm:cleared', (alarmId: string) => {
  // Remover alarme da lista
});
```

#### **Wireframe Completo**

```
┌──────────────────────────────────────────────────────────────┐
│ [Breadcrumb] Home > Operações > Alarmes Ativos               │
├──────────────────────────────────────────────────────────────┤
│ 🚨 Alarmes Ativos                    [●Live] 14:32:15       │
│                                                               │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                    │
│ │ 🔴  │ │ 🟠  │ │ 🟡  │ │ 🔵  │ │ ⚪  │                    │
│ │  3  │ │  8  │ │ 15  │ │ 22  │ │ 41  │                    │
│ │Crít.│ │Alto │ │Médio│ │Baixo│ │Info │                    │
│ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘                    │
│                                                               │
│ 🔍 Filtros:                                                  │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ [Buscar...]                                            │  │
│ │ Severidade: [Todas ▼]  Estado: [Ativos ▼]            │  │
│ │ Categoria: [Todas ▼]   Área: [Todas ▼]               │  │
│ │                         [Limpar] [Aplicar]            │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                               │
│ ☑️ Ações em Massa:                                           │
│ [ACK Selecionados] [Dismiss Selecionados]                   │
│                                                               │
│ 📊 Lista de Alarmes (89 ativos):                             │
│ ┌────────────────────────────────────────────────────────┐  │
│ │☑│Sev│ Time    │ Tag              │ Msg        │ Ações │  │
│ ├─┼───┼─────────┼──────────────────┼────────────┼───────┤  │
│ │☑│🔴 │ 14:32:15│ WAREHOUSE_LEVEL  │ Nível crít.│[ACK][✕│  │
│ │☑│🟠 │ 14:28:03│ MOEGA_1_TEMP     │ Temp. alta │[ACK][✕│  │
│ │☐│🟡 │ 14:15:42│ SILO_5_LEVEL     │ Nível elev.│[ACK][✕│  │
│ │☐│🔵 │ 13:58:20│ GATE_A1_POS      │ Pos. inval.│[ACK][✕│  │
│ └────────────────────────────────────────────────────────┘  │
│                                       [← Anterior] [Next →]  │
│                                                               │
│ 🔔 Som de Alerta: [🔊 ON]  Auto-refresh: [✅ 5s]            │
└──────────────────────────────────────────────────────────────┘
```

---

### 4. ⚠️ **Logs de Operação** (A Criar)
**Rota**: `/operations/logs`
**Arquivo**: `OperationLogsPage.tsx`
**Status**: **NÃO EXISTE**

#### **Objetivo**
Registrar e exibir todos os eventos operacionais para auditoria e análise.

#### **Funcionalidades**

**A. Filtros de Log**
```
┌──────────────────────────────────────────────────────┐
│ 📅 Período:                                          │
│ [Início: 2025-11-01] [Fim: 2025-11-05]              │
│                                                       │
│ Tipo de Evento: [Todos ▼]                           │
│ • Comandos de operador                               │
│ • Mudanças de modo (Auto/Manual)                     │
│ • Alarmes                                            │
│ • Mudanças de setpoint                               │
│ • START/STOP de equipamentos                         │
│                                                       │
│ Operador: [Todos ▼]  Equipamento: [Todos ▼]         │
│                                                       │
│ [Buscar Logs] [Exportar CSV]                         │
└──────────────────────────────────────────────────────┘
```

**B. Tabela de Logs**
```
┌──────────────────────────────────────────────────────────────┐
│ Timestamp        │ Tipo     │ Operador │ Equip.  │ Detalhes │
├──────────────────┼──────────┼──────────┼─────────┼──────────┤
│ 2025-11-05 14:32 │ Command  │ João     │ Moega 1 │ START    │
│ 2025-11-05 14:28 │ Setpoint │ Maria    │ Silo 5  │ 80% → 75%│
│ 2025-11-05 14:15 │ Mode     │ Sistema  │ Trans.1 │ A → M    │
│ 2025-11-05 13:58 │ Alarm    │ -        │ Comp. A1│ ACK      │
└──────────────────────────────────────────────────────────────┘
```

**C. Timeline Visual**
```
┌─────────────────────────────────────────────┐
│ 📊 Timeline de Eventos (últimas 24h)        │
├─────────────────────────────────────────────┤
│ 14:00                                       │
│   │                                         │
│   ├─ 🔴 ALARM: Warehouse Level              │
│   │                                         │
│ 13:00                                       │
│   │                                         │
│   ├─ ⚙️ COMMAND: START Moega 1              │
│   │                                         │
│   ├─ 🔄 MODE CHANGE: Auto → Manual          │
│   │                                         │
│ 12:00                                       │
│   │                                         │
│   ├─ 📊 SETPOINT: 75% → 80%                 │
└─────────────────────────────────────────────┘
```

#### **Componentes a Criar**

1. **`<LogFilters />`**
   ```typescript
   interface LogFiltersProps {
     onFilterChange: (filters: LogFilters) => void;
   }

   interface LogFilters {
     startDate: string;
     endDate: string;
     eventType?: string[];
     operator?: string;
     equipment?: string;
   }
   ```

2. **`<LogTable />`**
   ```typescript
   interface LogTableProps {
     logs: OperationLog[];
     onRowClick?: (log: OperationLog) => void;
   }

   interface OperationLog {
     id: string;
     timestamp: string;
     eventType: 'command' | 'setpoint' | 'mode_change' | 'alarm' | 'start' | 'stop';
     operator?: string;
     equipment: string;
     details: string;
     before?: any;
     after?: any;
   }
   ```

3. **`<LogTimeline />`**
   ```typescript
   interface LogTimelineProps {
     logs: OperationLog[];
     timeRange: number; // horas
   }
   ```

4. **`<LogExport />`**
   ```typescript
   interface LogExportProps {
     filters: LogFilters;
     onExport: (format: 'csv' | 'pdf' | 'excel') => void;
   }
   ```

#### **API Endpoints Necessários**

```typescript
// GET /api/v1/operations/logs
// Query: ?start_date=&end_date=&event_type=&operator=&equipment=

// GET /api/v1/operations/logs/:id

// GET /api/v1/operations/logs/export
// Query: ?format=csv&filters=...
// Retorna arquivo para download
```

#### **Wireframe Completo**

```
┌──────────────────────────────────────────────────────────────┐
│ [Breadcrumb] Home > Operações > Logs de Operação             │
├──────────────────────────────────────────────────────────────┤
│ 📜 Logs de Operação                                          │
│                                                               │
│ 🔍 Filtros:                                                  │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ 📅 Período:                                            │  │
│ │ [Início: 2025-11-01 00:00] [Fim: 2025-11-05 23:59]    │  │
│ │                                                         │  │
│ │ Tipo de Evento: [Todos ▼]                             │  │
│ │ Operador: [Todos ▼]  Equipamento: [Todos ▼]          │  │
│ │                                                         │  │
│ │            [Buscar] [Limpar] [Exportar CSV]           │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                               │
│ 📊 Resumo:                                                   │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                            │
│ │ 156 │ │  43 │ │  28 │ │  12 │                            │
│ │Comds│ │Alrms│ │Modes│ │Stpts│                            │
│ └─────┘ └─────┘ └─────┘ └─────┘                            │
│                                                               │
│ 📋 Logs Encontrados (239):                                   │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Timestamp        │ Tipo  │ Oper. │ Equip.│ Detalhes   │  │
│ ├──────────────────┼───────┼───────┼───────┼────────────┤  │
│ │ 2025-11-05 14:32 │ CMD   │ João  │Moega 1│ START      │  │
│ │ 2025-11-05 14:28 │ STPT  │ Maria │Silo 5 │ 80% → 75%  │  │
│ │ 2025-11-05 14:15 │ MODE  │ Sist. │Trans.1│ Auto → Man │  │
│ │ 2025-11-05 13:58 │ ALARM │ -     │Comp.A1│ ACK        │  │
│ └────────────────────────────────────────────────────────┘  │
│                                       [← Anterior] [Next →]  │
│                                                               │
│ 📊 Timeline Visual:                                          │
│ [Ver Timeline] [Ver Estatísticas]                            │
└──────────────────────────────────────────────────────────────┘
```

---

## 📦 Componentes Core Compartilhados

### 1. **`<RealtimeValue />`**
Exibe valor de tag em tempo real com auto-refresh.

```typescript
interface RealtimeValueProps {
  tagName: string;
  label?: string;
  unit?: string;
  decimals?: number;
  showTimestamp?: boolean;
  showQuality?: boolean;
  thresholds?: {
    critical?: { min?: number; max?: number };
    warning?: { min?: number; max?: number };
  };
}
```

**Exemplo**:
```tsx
<RealtimeValue
  tagName="WAREHOUSE_LEVEL_PCT_PV"
  label="Nível do Armazém"
  unit="%"
  decimals={1}
  showTimestamp={true}
  thresholds={{
    critical: { max: 95 },
    warning: { max: 85 }
  }}
/>
```

### 2. **`<EquipmentStatusBadge />`**
Badge colorido de status de equipamento.

```typescript
interface EquipmentStatusBadgeProps {
  status: 'running' | 'stopped' | 'warning' | 'error' | 'maintenance';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}
```

### 3. **`<OperatorInfo />`**
Mostra informações do operador logado.

```typescript
interface OperatorInfoProps {
  showShift?: boolean;
  showTurno?: boolean;
}
```

### 4. **`<LiveIndicator />`**
Indicador de conexão em tempo real.

```typescript
interface LiveIndicatorProps {
  connected: boolean;
  lastUpdate?: string;
}
```

---

## 🎨 Paleta de Cores - Módulo Operações

```css
/* Status Colors */
--color-running: #10B981;    /* Verde */
--color-stopped: #EF4444;    /* Vermelho */
--color-warning: #F59E0B;    /* Amarelo */
--color-error: #DC2626;      /* Vermelho escuro */
--color-maintenance: #6B7280;/* Cinza */

/* Alarm Severities */
--color-critical: #DC2626;   /* Vermelho */
--color-high: #F97316;       /* Laranja */
--color-medium: #F59E0B;     /* Amarelo */
--color-low: #3B82F6;        /* Azul */
--color-info: #D1D5DB;       /* Cinza claro */

/* Mode Colors */
--color-auto: #10B981;       /* Verde */
--color-manual: #F59E0B;     /* Amarelo */
```

---

## 🚀 Roadmap de Implementação - Módulo Operações

### **Fase 1: Controle de Processo** (1 semana)
- [ ] Criar ProcessControlPage
- [ ] Componentes: ProcessSelector, EquipmentControlGrid
- [ ] Componente: ControlPanel
- [ ] Componente: CommandHistory
- [ ] API endpoints: equipments, commands, setpoints
- [ ] Validações e confirmações
- [ ] Testes

### **Fase 2: Alarmes Ativos** (1 semana)
- [ ] Criar ActiveAlarmsPage
- [ ] Componentes: AlarmCounters, AlarmFilters
- [ ] Componente: AlarmTable, AlarmDetailModal
- [ ] Componente: AlarmTrendChart
- [ ] API endpoints: alarms, acknowledge, dismiss
- [ ] WebSocket integration
- [ ] Som de alerta
- [ ] Testes

### **Fase 3: Logs de Operação** (3-4 dias)
- [ ] Criar OperationLogsPage
- [ ] Componentes: LogFilters, LogTable
- [ ] Componente: LogTimeline
- [ ] Componente: LogExport
- [ ] API endpoints: logs, export
- [ ] Filtros e busca
- [ ] Testes

### **Fase 4: Componentes Core** (2 dias)
- [ ] RealtimeValue
- [ ] EquipmentStatusBadge
- [ ] OperatorInfo
- [ ] LiveIndicator

### **Fase 5: Integração e Testes** (2 dias)
- [ ] Navegação entre telas
- [ ] Testes de integração
- [ ] Ajustes de UX
- [ ] Documentação

**Total**: ~3 semanas

---

## 📊 Métricas de Sucesso

### **Funcionalidades**
- ✅ SCADA Monitor (existente)
- ⚠️ Controle de Processo → 100%
- ⚠️ Alarmes Ativos → 100%
- ⚠️ Logs de Operação → 100%

### **Componentes Reutilizáveis**
- 0 → **8+ componentes core**

### **Cobertura do Módulo**
- 25% → **100%**

---

**Status**: 📋 Especificação completa do Módulo de Operações
**Próximo**: Especificação Módulo de Manutenção
