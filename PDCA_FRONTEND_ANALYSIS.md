# PDCA - Análise Completa do Frontend OptiFlow AI

**Data**: 2025-11-17
**Versão**: Frontend v1.0.0
**Framework**: React 18.2.0 + TypeScript 5.3.3 + Vite 5.0.8

---

## 📊 RESUMO EXECUTIVO

### Status Geral

| Categoria | Status | Quantidade |
|-----------|--------|------------|
| **Build** | ⚠️ Funciona com warnings | 27.73s |
| **Bundle Size** | 🔴 CRÍTICO | 6.5 MB (chart-vendor: 5.2 MB) |
| **TypeScript Errors** | 🟡 MÉDIO | 4 erros (Apollo Client não instalado) |
| **ESLint Errors** | 🔴 CRÍTICO | 445 erros |
| **ESLint Warnings** | 🟡 MÉDIO | 269 warnings |
| **MUI Grid v2** | 🟡 MÉDIO | 86 ocorrências de props deprecated |
| **Páginas** | ✅ BOM | 55 páginas funcionais |
| **Componentes** | ✅ BOM | 141 componentes |
| **Hooks Customizados** | ✅ BOM | 12 hooks |

---

## 🔴 PLAN - PROBLEMAS CRÍTICOS IDENTIFICADOS

### 1. BUNDLE SIZE EXCESSIVO (PRIORIDADE: ALTA)

**Problema**: Bundle total de 6.5 MB após build
```
dist/assets/chart-vendor-DZpWpVNw.js   5,190.78 kB (5.2 MB!)
dist/assets/index-B8JgOWVS.js          1,073.81 kB (1 MB)
dist/assets/react-vendor-DufuAMOZ.js     164.52 kB
```

**Impacto**:
- Tempo de carregamento lento (3+ segundos)
- Consumo excessivo de banda
- Performance ruim em dispositivos móveis
- UX degradada

**Causa Raiz**:
- Plotly.js inteiro importado (2.27.1) = ~4 MB
- D3.js completo (7.8.5) = ~600 KB
- Recharts (2.15.4) = ~400 KB
- Três bibliotecas de gráficos diferentes
- Sem tree shaking efetivo
- Sem code splitting por rota

---

### 2. ERROS DE ESLINT (PRIORIDADE: ALTA)

**Total**: 445 erros + 269 warnings = **714 problemas**

**Principais categorias**:

| Tipo de Erro | Quantidade | Descrição |
|--------------|------------|-----------|
| `@typescript-eslint/no-explicit-any` | ~300 | Uso de `any` type |
| `react-hooks/exhaustive-deps` | ~80 | Dependências faltando em hooks |
| `@typescript-eslint/no-unused-vars` | ~50 | Variáveis não utilizadas |
| `@typescript-eslint/ban-ts-comment` | ~30 | @ts-ignore comments |

**Arquivos mais problemáticos**:
- `/api/client.ts` - 12+ erros de `any`
- `/api/chat.ts` - 3 erros
- `/api/insights.ts` - 3 erros
- Vários componentes com hooks mal configurados

---

### 3. TYPESCRIPT ERRORS (PRIORIDADE: MÉDIA)

```bash
src/components/ExecutiveDashboardGraphQL.tsx(11,39): error TS2307:
  Cannot find module '@apollo/client'

src/graphql/apollo-client-example.ts(7,73): error TS2307:
  Cannot find module '@apollo/client'
```

**Problema**: Apollo Client está sendo usado mas não instalado
**Impacto**: Type checking falha, GraphQL não funciona

---

### 4. MUI GRID V2 DEPRECATED PROPS (PRIORIDADE: MÉDIA)

**86 ocorrências** em 11 arquivos:

```tsx
// DEPRECATED (MUI Grid v2):
<Grid item xs={12} sm={6} md={4}>

// CORRETO (MUI Grid v2):
<Grid size={{ xs: 12, sm: 6, md: 4 }}>
```

**Arquivos afetados**:
- `ProfessionalDashboard.tsx` - 14 ocorrências
- `AlarmsEventsView.tsx` - 15 ocorrências
- `HistoricalDataAnalysis.tsx` - 12 ocorrências
- `ProfessionalAnalytics.tsx` - 11 ocorrências
- E mais 7 arquivos

---

### 5. IMPORTS NÃO UTILIZADOS (PRIORIDADE: BAIXA)

**App.tsx**:
```tsx
import SimulatorPage from './pages/SimulatorPage';           // UNUSED
import DashboardBuilderPage from './pages/DashboardBuilderPage'; // UNUSED
import ExecutiveDashboard from './pages/ExecutiveDashboard'; // UNUSED
```

**Impacto**: Bundle size aumentado desnecessariamente

---

### 6. MÓDULOS EXTERNALIZADOS (PRIORIDADE: BAIXA)

```
[plugin:vite:resolve] Module "buffer" has been externalized
[plugin:vite:resolve] Module "stream" has been externalized
[plugin:vite:resolve] Module "assert" has been externalized
```

**Causa**: Bibliotecas Node.js sendo usadas no browser
**Fonte**: `typedarray-pool`, `probe-image-size`, `stream-parser`

---

## 🔧 DO - PLANO DE AÇÃO

### SPRINT 1: CRÍTICOS (1-2 dias)

#### 1.1 Instalar Apollo Client
```bash
npm install @apollo/client graphql
```

**Arquivos**:
- `src/components/ExecutiveDashboardGraphQL.tsx`
- `src/graphql/apollo-client-example.ts`

#### 1.2 Otimizar Bundle Size (Code Splitting)

**A) Lazy Loading de Rotas** (`App.tsx`):
```tsx
// ANTES:
import Dashboard from './pages/Dashboard';

// DEPOIS:
const Dashboard = lazy(() => import('./pages/Dashboard'));
const ExecutiveDashboard = lazy(() => import('./pages/ExecutiveDashboard'));

// Usar com Suspense:
<Suspense fallback={<CircularProgress />}>
  <Route path="/dashboard" element={<Dashboard />} />
</Suspense>
```

**B) Dynamic Import de Chart Libraries**:
```tsx
// ANTES:
import Plot from 'react-plotly.js';

// DEPOIS:
const Plot = lazy(() => import('react-plotly.js'));
```

**C) Tree Shaking para D3**:
```tsx
// ANTES:
import * as d3 from 'd3';

// DEPOIS:
import { scaleLinear, line } from 'd3-scale';
import { axisBottom } from 'd3-axis';
```

#### 1.3 Remover Imports Não Utilizados

**App.tsx**:
```tsx
// REMOVER:
import SimulatorPage from './pages/SimulatorPage';
import DashboardBuilderPage from './pages/DashboardBuilderPage';
import ExecutiveDashboard from './pages/ExecutiveDashboard';
```

---

### SPRINT 2: ALTOS (2-3 dias)

#### 2.1 Corrigir MUI Grid v2

**Script automático** (`scripts/fix-mui-grid.sh`):
```bash
#!/bin/bash
# Substituir props deprecated do MUI Grid v2

for file in src/pages/*.tsx src/components/**/*.tsx; do
  # item prop removal
  sed -i 's/<Grid item /<Grid /g' "$file"

  # xs/sm/md/lg -> size
  sed -i 's/xs={\([^}]*\)}/size={{ xs: \1 }}/g' "$file"
  sed -i 's/xs="\([^"]*\)"/size={{ xs: \1 }}/g' "$file"
done
```

**Exemplo manual**:
```tsx
// ANTES:
<Grid container spacing={3}>
  <Grid item xs={12} sm={6} md={4}>
    <Card>...</Card>
  </Grid>
</Grid>

// DEPOIS:
<Grid container spacing={3}>
  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
    <Card>...</Card>
  </Grid>
</Grid>
```

#### 2.2 Corrigir Hook Dependencies

**Padrão problemático**:
```tsx
// ERRADO:
useEffect(() => {
  fetchActiveAlarms();
}, []); // Missing dependency!

// CORRETO:
const fetchActiveAlarms = useCallback(async () => {
  // fetch logic
}, [dependencies]);

useEffect(() => {
  fetchActiveAlarms();
}, [fetchActiveAlarms]);
```

---

### SPRINT 3: MÉDIOS (3-5 dias)

#### 3.1 Eliminar `any` Types

**Estratégia gradual**:

1. **API Client** (`src/api/client.ts`):
```tsx
// ANTES:
export async function get(url: string): Promise<any> {

// DEPOIS:
export async function get<T>(url: string): Promise<T> {
```

2. **Criar interfaces para respostas**:
```tsx
interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

interface TagData {
  id: string;
  name: string;
  value: number;
  timestamp: string;
  quality: 'GOOD' | 'BAD' | 'UNCERTAIN';
}
```

3. **Usar generics**:
```tsx
// ANTES:
const response: any = await api.get('/tags');

// DEPOIS:
const response = await api.get<TagData[]>('/tags');
```

#### 3.2 Configurar ESLint Progressivamente

**`.eslintrc.cjs`**:
```js
module.exports = {
  rules: {
    // Desativar temporariamente para legacy code
    '@typescript-eslint/no-explicit-any': 'warn', // era 'error'

    // Ativar para novo código
    '@typescript-eslint/no-unused-vars': ['error', {
      argsIgnorePattern: '^_',
      varsIgnorePattern: '^_'
    }],

    'react-hooks/exhaustive-deps': 'warn'
  }
};
```

---

### SPRINT 4: OTIMIZAÇÕES (1 semana)

#### 4.1 Substituir Plotly por Recharts

**Por quê?**
- Plotly: 5.2 MB (bundled)
- Recharts: 400 KB (tree-shakeable)
- Performance 10x melhor

**Exemplo de migração**:
```tsx
// ANTES (Plotly):
import Plot from 'react-plotly.js';

<Plot
  data={[{ x: [1,2,3], y: [2,6,3], type: 'scatter' }]}
  layout={{ width: 600, height: 400 }}
/>

// DEPOIS (Recharts):
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

const data = [
  { x: 1, y: 2 },
  { x: 2, y: 6 },
  { x: 3, y: 3 }
];

<LineChart width={600} height={400} data={data}>
  <Line type="monotone" dataKey="y" stroke="#8884d8" />
  <XAxis dataKey="x" />
  <YAxis />
  <Tooltip />
</LineChart>
```

#### 4.2 Implementar Memoização

```tsx
// Componentes pesados
const HeavyChart = React.memo(({ data }) => {
  return <LineChart data={data} />;
});

// Valores computados
const expensiveValue = useMemo(() => {
  return data.reduce((acc, item) => acc + item.value, 0);
}, [data]);

// Callbacks
const handleClick = useCallback(() => {
  // handler logic
}, [dependency]);
```

#### 4.3 Virtual Scrolling para Listas Grandes

```bash
npm install @tanstack/react-virtual
```

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

function TagsList({ tags }) {
  const virtualizer = useVirtualizer({
    count: tags.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
  });

  return (
    <div ref={parentRef} style={{ height: '400px', overflow: 'auto' }}>
      <div style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div key={virtualItem.key}>{tags[virtualItem.index].name}</div>
        ))}
      </div>
    </div>
  );
}
```

---

## ✅ CHECK - MÉTRICAS DE SUCESSO

### Bundle Size Target

| Chunk | Atual | Meta | Redução |
|-------|-------|------|---------|
| chart-vendor | 5,190 KB | < 1,000 KB | -80% |
| index (main) | 1,073 KB | < 500 KB | -53% |
| Total | 6,500 KB | < 2,000 KB | -69% |

### Performance Targets

| Métrica | Atual | Meta | Melhoria |
|---------|-------|------|----------|
| First Contentful Paint | ~3s | < 1s | -66% |
| Time to Interactive | ~5s | < 2s | -60% |
| Lighthouse Score | ~60 | > 90 | +50% |

### Code Quality Targets

| Métrica | Atual | Meta |
|---------|-------|------|
| ESLint Errors | 445 | 0 |
| ESLint Warnings | 269 | < 50 |
| TypeScript Errors | 4 | 0 |
| MUI Deprecated Props | 86 | 0 |

---

## 🔄 ACT - PRÓXIMAS ITERAÇÕES

### Ciclo 1: Estabilização (Esta semana)
- [ ] Instalar Apollo Client
- [ ] Remover imports não utilizados
- [ ] Corrigir TypeScript errors (4)
- [ ] Implementar lazy loading básico

### Ciclo 2: Code Quality (Próxima semana)
- [ ] Corrigir MUI Grid deprecated props (86)
- [ ] Resolver 50% dos ESLint warnings
- [ ] Adicionar tipos para APIs principais

### Ciclo 3: Performance (Semana 3)
- [ ] Migrar Plotly → Recharts
- [ ] Implementar code splitting por rota
- [ ] Adicionar memoização em componentes pesados

### Ciclo 4: Excelência (Semana 4)
- [ ] Zero ESLint errors
- [ ] < 50 warnings
- [ ] Bundle < 2 MB
- [ ] Lighthouse > 90

---

## 📋 ARQUIVOS PRIORITÁRIOS PARA CORREÇÃO

### Críticos (Bloqueia funcionalidade)
1. `src/graphql/apollo-client-example.ts` - Apollo não instalado
2. `src/components/ExecutiveDashboardGraphQL.tsx` - Apollo não instalado

### Altos (Deprecation warnings)
3. `src/pages/ProfessionalDashboard.tsx` - 14 Grid deprecated
4. `src/pages/AlarmsEventsView.tsx` - 15 Grid deprecated
5. `src/pages/HistoricalDataAnalysis.tsx` - 12 Grid deprecated

### Médios (Code quality)
6. `src/api/client.ts` - 12+ any types
7. `src/App.tsx` - imports não utilizados
8. `src/components/ActiveAlarmsWidget.tsx` - hook dependency

---

## 🚀 COMANDOS ÚTEIS

```bash
# Verificar TypeScript
npm run type-check

# Build com análise
npm run build

# Lint completo
npx eslint src/ --ext .ts,.tsx

# Lint com auto-fix
npx eslint src/ --ext .ts,.tsx --fix

# Contar problemas
npx eslint src/ --ext .ts,.tsx 2>&1 | grep -c "error"

# Analisar bundle
npm i -D rollup-plugin-visualizer
# Adicionar em vite.config.ts e gerar stats.html
```

---

## 📊 DASHBOARD DE PROGRESSO

```
PDCA Frontend Progress:

[Build]          ████████████████████ 100% ✅
[TypeScript]     ██████████░░░░░░░░░░  50% 🟡
[ESLint]         ██░░░░░░░░░░░░░░░░░░  10% 🔴
[Performance]    ████░░░░░░░░░░░░░░░░  20% 🔴
[MUI Migration]  ░░░░░░░░░░░░░░░░░░░░   0% 🔴
[Code Quality]   ████████░░░░░░░░░░░░  40% 🟡

Overall: 37%
```

---

**Próximo PDCA**: Após correção dos itens críticos (Sprint 1)
**Responsável**: Development Team
**Review Date**: 2025-11-24

---

*Este documento deve ser atualizado a cada sprint para refletir o progresso real.*
