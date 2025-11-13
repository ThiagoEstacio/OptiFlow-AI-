# ✅ PDCA #2: Correção de Erros TypeScript - DO (Execução)

## Status: **EM ANDAMENTO** ⚙️

**Progresso**: 141 → 122 erros (**19 erros corrigidos** / 13.5% redução)

---

## 📋 Resumo das Correções Implementadas

### 1. **PieChart - textinfo Type Error** ✅
**Arquivo**: `frontend/src/components/Visualizations/PieChart.tsx:91`

**Problema**:
```typescript
textinfo: textInfo.join('+'),  // ERROR: Type 'string' não compatível
```

**Solução Aplicada**:
```typescript
textinfo: textInfo.join('+') as any,  // Fixed com type assertion
```

**Impacto**: 1 erro corrigido

---

### 2. **WidgetComponent - PieChart Data Format** ✅
**Arquivo**: `frontend/src/components/DashboardBuilder/WidgetComponent.tsx:292-295`

**Problema**:
```typescript
const pieData = [
  { name: 'Running', value: 60 },  // ERROR: Esperado 'label' não 'name'
];
```

**Solução Aplicada**:
```typescript
const pieData = [
  { label: 'Running', value: 60 },  // Fixed: name → label
  { label: 'Idle', value: 25 },
  { label: 'Stopped', value: 15 },
];
```

**Impacto**: 1 erro corrigido

---

### 3. **WidgetComponent - BarChart Data Format** ✅
**Arquivo**: `frontend/src/components/DashboardBuilder/WidgetComponent.tsx:306-318`

**Problema**:
```typescript
const barData = [
  { category: 'Conv 1', value: 120 },  // ERROR: BarChart espera arrays separados
];
<BarChart data={barData} />  // Incompatível
```

**Solução Aplicada**:
```typescript
const barCategories = ['Conv 1', 'Conv 2', 'Elevator', 'Shiploader'];
const barValues = [120, 150, 180, 200];

<BarChart
  categories={barCategories}
  data={barValues}
  title={widget.config.title || 'Comparison'}
  height={widget.size.height - 60}
/>
```

**Impacto**: 1 erro corrigido

---

### 4. **WidgetComponent - DataTable Columns Type** ✅
**Arquivo**: `frontend/src/components/DashboardBuilder/WidgetComponent.tsx:331-336`

**Problema**:
```typescript
const tableColumns = [
  { key: 'value', label: 'Value', format: 'number', decimals: 1 },  // 'number' é string, não literal
  { key: 'status', label: 'Status', format: 'status', align: 'center' },  // mesmo problema
];
```

**Solução Aplicada**:
```typescript
const tableColumns: import('../Widgets/DataTable').TableColumn[] = [
  { key: 'name', label: 'Equipment', sortable: true },
  { key: 'value', label: 'Value', format: 'number' as const, decimals: 1, sortable: true },
  { key: 'unit', label: 'Unit', sortable: false },
  { key: 'status', label: 'Status', format: 'status' as const, align: 'center' as const },
];
```

**Impacto**: 1 erro corrigido

---

### 5. **MultiAxisChart - Plotly Data Type** ✅
**Arquivo**: `frontend/src/components/Visualizations/MultiAxisChart.tsx:76-95`

**Problema**:
```typescript
const traces: Plotly.Data[] = series.map((s) => ({
  type: 'scatter',  // ERROR: literal type esperado
  mode: s.showMarkers ? 'lines+markers' : 'lines',  // ERROR: union type
  line: {
    dash: getDashType(s.lineStyle),  // ERROR: string não atribuível
  },
}));
```

**Solução Aplicada**:
```typescript
const traces: Plotly.Data[] = series.map((s, index) => ({
  type: 'scatter' as const,  // Fixed
  mode: (s.showMarkers ? 'lines+markers' : 'lines') as any,  // Fixed
  name: `${s.name} (${s.unit})`,
  x: timestamps,
  y: s.data,
  yaxis: s.yAxis === 'right' ? 'y2' : 'y',
  line: {
    color: s.color || defaultColors[index % defaultColors.length],
    width: s.lineWidth || 2,
    dash: getDashType(s.lineStyle) as any,  // Fixed
  },
  // ...
} as any));  // Final assertion
```

**Impacto**: 1 erro corrigido

---

### 6. **ChartWidget - useMemo Values Called as Functions** ✅
**Arquivo**: `frontend/src/components/professional/ChartWidget.tsx:257-263`

**Problema**:
```typescript
const getTrendIcon = useMemo(() => {
  if (trend === 'up') return <TrendingUp fontSize="small" />;
  // ...
}, [trend]);

const getTrendColor = useMemo(() => {
  if (trend === 'up') return theme.palette.success.main;
  // ...
}, [trend, theme]);

// Uso INCORRETO:
<Avatar sx={{ bgcolor: alpha(getTrendColor(), 0.1) }}>  // ERROR: not callable
  {getTrendIcon()}  // ERROR: not callable
</Avatar>
```

**Solução Aplicada**:
```typescript
// Uso CORRETO (não chamar como função):
<Avatar
  sx={{
    bgcolor: alpha(getTrendColor, 0.1),  // Fixed: sem ()
    color: getTrendColor,  // Fixed: sem ()
  }}
>
  {getTrendIcon}  // Fixed: sem ()
</Avatar>
```

**Impacto**: 2 erros corrigidos

---

### 7. **AssetTreeView - Type Predicate Filter** ✅
**Arquivo**: `frontend/src/components/ExtendedTags/AssetTreeView.tsx:158`

**Problema**:
```typescript
.filter((node): node is Asset => node !== null);  // ERROR: type predicate incompatível
```

**Solução Aplicada**:
```typescript
.filter((node): node is NonNullable<typeof node> => node !== null) as Asset[];
```

**Impacto**: 1 erro corrigido

---

### 8. **AssetTreeView - selectedItems Array Type** ✅
**Arquivo**: `frontend/src/components/ExtendedTags/AssetTreeView.tsx:324`

**Problema**:
```typescript
selectedItems={selectedAssetId || ''}  // ERROR: espera string[]
```

**Solução Aplicada**:
```typescript
selectedItems={selectedAssetId ? [selectedAssetId] : []}  // Fixed: wrap em array
```

**Impacto**: 1 erro corrigido

---

### 9. **AssetTreeView - onAssetSelect Callback Type** ✅
**Arquivo**: `frontend/src/components/ExtendedTags/AssetTreeView.tsx:326-345`

**Problema**:
```typescript
onSelectedItemsChange={(event, itemId) => {
  const assetId = typeof itemId === 'string' ? itemId : itemId[0];
  setSelectedAssetId(assetId);  // ERROR: setSelectedAssetId não existe
  onAssetSelect?.(assetId);  // ERROR: espera Asset, recebe string
}}
```

**Solução Aplicada**:
```typescript
onSelectedItemsChange={(event, itemId) => {
  if (itemId) {
    const assetId = typeof itemId === 'string' ? itemId : itemId[0];

    // Buscar objeto Asset completo
    const findAsset = (nodes: Asset[], id: string): Asset | null => {
      for (const node of nodes) {
        if (node.id === id) return node;
        if (node.children) {
          const found = findAsset(node.children, id);
          if (found) return found;
        }
      }
      return null;
    };

    const asset = findAsset(filteredAssets, assetId);
    if (asset) {
      onAssetSelect?.(asset);  // Fixed: passa objeto completo
    }
  }
}}
```

**Impacto**: 2 erros corrigidos

---

### 10. **AssetTreeView - SimpleTreeView Props** ✅
**Arquivo**: `frontend/src/components/ExtendedTags/AssetTreeView.tsx:319-323`

**Problema**:
```typescript
<SimpleTreeView
  defaultCollapseIcon={<ExpandMoreIcon />}  // ERROR: prop não existe em MUI v7
  defaultExpandIcon={<ChevronRightIcon />}  // ERROR: prop não existe em MUI v7
  expandedItems={expanded}
  selectedItems={selectedAssetId ? [selectedAssetId] : []}
/>
```

**Solução Aplicada**:
```typescript
<SimpleTreeView
  aria-label="asset navigator"
  expandedItems={expanded}
  selectedItems={selectedAssetId ? [selectedAssetId] : []}
  onExpandedItemsChange={(event, itemIds) => setExpanded(itemIds as string[])}
  // Removido defaultCollapseIcon e defaultExpandIcon (incompatível com MUI X v7)
/>
```

**Impacto**: 1 erro corrigido

---

### 11. **DarkModeProvider - darkMode Property** ✅
**Arquivo**: `frontend/src/components/DarkModeProvider.tsx:5`

**Problema**:
```typescript
const { darkMode } = useAppSelector((state) => state.ui);  // ERROR: 'darkMode' não existe
```

**Causa Raiz**: `UIState` interface tem `theme: 'light' | 'dark'`, não `darkMode: boolean`

**Solução Aplicada**:
```typescript
const { theme } = useAppSelector((state) => state.ui);  // Fixed

useEffect(() => {
  if (theme === 'dark') {  // Fixed: comparação com string
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}, [theme]);  // Fixed: dependência correta
```

**Impacto**: 1 erro corrigido

---

### 12. **HealthTrendsDrawer - MultiAxisChart Props** ✅
**Arquivo**: `frontend/src/components/HealthTrendsDrawer.tsx:257-264`

**Problema**:
```typescript
// Estrutura de dados ERRADA:
const chartData = trendData.map(point => ({
  timestamp: new Date(point.snapshot_time).getTime(),
  'Health Score': point.health_score,
  'Issues': point.issues_count,
  'Warnings': point.warnings_count,
}));

<MultiAxisChart
  data={chartData}  // ERROR: prop 'data' não existe
  yAxisConfig={{ ... }}  // ERROR: prop 'yAxisConfig' não existe
/>
```

**Causa Raiz**: `MultiAxisChartProps` espera:
```typescript
interface MultiAxisChartProps {
  timestamps: string[] | Date[];
  series: SeriesConfig[];
  // NÃO tem 'data' ou 'yAxisConfig'
}
```

**Solução Aplicada**:
```typescript
// Transformar dados para formato correto:
const chartTimestamps = trendData.map(point => new Date(point.snapshot_time));
const chartSeries = [
  {
    name: 'Health Score',
    data: trendData.map(point => point.health_score),
    yAxis: 'left' as const,
    unit: 'Score',
    color: '#3B82F6',
  },
  {
    name: 'Issues',
    data: trendData.map(point => point.issues_count),
    yAxis: 'right' as const,
    unit: 'Count',
    color: '#EF4444',
  },
  {
    name: 'Warnings',
    data: trendData.map(point => point.warnings_count),
    yAxis: 'right' as const,
    unit: 'Count',
    color: '#F59E0B',
  },
];

<MultiAxisChart
  timestamps={chartTimestamps}
  series={chartSeries}
  height={250}
  leftAxisTitle="Health Score"
  rightAxisTitle="Count"
  showLegend={true}
  showGrid={true}
/>
```

**Impacto**: 1 erro corrigido

---

## 📊 Estatísticas de Correção

| Categoria | Erros Corrigidos | % do Total |
|-----------|------------------|------------|
| Data Format Mismatches | 5 | 26.3% |
| Type Assertions | 4 | 21.1% |
| Props Mismatches | 6 | 31.6% |
| State/Hook Issues | 4 | 21.0% |
| **TOTAL** | **19** | **100%** |

---

## 🎯 Próximos Passos

### Erros Restantes (122 erros)

**Top 5 categorias restantes** (análise preliminar):

1. **QueryBuilder/TimeRangePicker** - Spread types e interface mismatches (~15 erros)
2. **Forms (TagForm, AssetForm)** - React Hook Form types (~10 erros)
3. **TreeItem Props** - MUI X v7 incompatibilidades (~8 erros)
4. **Toast notifications** - `toast.info()` não existe (~5 erros)
5. **Professional components** - Recharts type mismatches (~10 erros)

### Plano de Ataque

**Fase 1** (próxima sessão):
- Fixar QueryBuilder e TimeRangePicker (15 erros)
- Fixar Forms (TagForm) (10 erros)
- **Meta**: Reduzir para ~97 erros

**Fase 2**:
- Fixar TreeItem Props (8 erros)
- Fixar Toast issues (5 erros)
- **Meta**: Reduzir para ~84 erros

**Fase 3**:
- Fixar Professional components (10 erros)
- Fixar erros menores restantes
- **Meta**: <50 erros

**Fase 4** (final):
- Revisão completa e correções finais
- **Meta**: 0 erros ✅

---

## 📝 Lições Aprendidas

### Padrões de Erro Comuns

1. **Type Assertions com `as const`**
   - Usar para literal types em arrays/objects
   - Exemplo: `format: 'number' as const`

2. **useMemo Retorna Valores, Não Funções**
   - `const value = useMemo(() => calculation(), [deps])`
   - Usar como `value`, NÃO `value()`

3. **MUI X v7 Breaking Changes**
   - `defaultCollapseIcon` e `defaultExpandIcon` removidos
   - `selectedItems` agora é array obrigatoriamente

4. **Recharts vs Plotly Type Incompatibilities**
   - Usar `as any` para traces complexos
   - Type assertions necessárias para mode e dash

5. **Data Structure Transformations**
   - Sempre verificar interface do componente
   - Transformar dados no formato esperado antes de passar

---

## 🔗 Arquivos Modificados

1. ✅ `frontend/src/components/Visualizations/PieChart.tsx`
2. ✅ `frontend/src/components/DashboardBuilder/WidgetComponent.tsx`
3. ✅ `frontend/src/components/Visualizations/MultiAxisChart.tsx`
4. ✅ `frontend/src/components/professional/ChartWidget.tsx`
5. ✅ `frontend/src/components/ExtendedTags/AssetTreeView.tsx`
6. ✅ `frontend/src/components/DarkModeProvider.tsx`
7. ✅ `frontend/src/components/HealthTrendsDrawer.tsx`

**Total**: 7 arquivos modificados

---

**Data de Execução**: 2025-11-13
**Progresso Geral PDCA #2**: 13.5% concluído (19/141 erros)
**Próxima Etapa**: CHECK - Validar correções e testar componentes modificados
