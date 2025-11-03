# SmartPort - Advanced Analytics & Visualization Roadmap

**Versão**: 1.0
**Data**: 2025-10-28
**Objetivo**: Transformar SmartPort em plataforma industrial analytics completa (Power BI + PI Vision)

---

## 🎯 Visão Estratégica

Elevar o SmartPort de uma **plataforma de monitoramento básica** para uma **plataforma de analytics e visualização industrial de nível enterprise**, combinando:

- **Power BI**: Queries dinâmicas, filtros avançados, análise multi-dimensional
- **PI Vision**: Visualizações industriais, trending avançado, símbolos animados

### Diferencial Competitivo

| Funcionalidade | Atual (v1.0) | Futuro (v2.0) | Competidores |
|----------------|--------------|---------------|--------------|
| **Query Dinâmico** | Agregações básicas | Query builder visual + DAX-like | Power BI, Tableau |
| **Visualizações** | 2 tipos de gráfico | 15+ tipos industriais | PI Vision, Ignition |
| **Real-time** | Parcial | Streaming completo | SCADA systems |
| **Analytics** | Nenhum | ML/AI integrado | ThingWorx, AWS IoT |
| **Dashboard Builder** | Nenhum | Drag-and-drop | Grafana, Kibana |

---

## 📋 Estado Atual (Baseline)

### Frontend Existente

**Bibliotecas Disponíveis**:
- ✅ Recharts 2.15.4 (em uso)
- ✅ Plotly.js 2.27.1 (instalado, não usado)
- ✅ D3 7.8.5 (instalado, não usado)
- ✅ React 18 + TypeScript
- ✅ Redux Toolkit

**Componentes Atuais**:
- TimeSeriesChart (linha/área simples)
- MultiSeriesChart (múltiplas séries)
- StatCard (KPI básico)
- Dashboards hardcoded

**Capacidades de Query**:
- Agregações: mean, min, max, sum, count
- Filtros: Por tempo (1h, 6h, 24h, 7d)
- Limitações: Sem cross-tag, sem custom measures

### Gap Analysis

| Categoria | Score Atual | Target | Gap |
|-----------|-------------|--------|-----|
| Query Engine | 2/10 | 9/10 | **Crítico** |
| Visualizações | 3/10 | 9/10 | **Crítico** |
| Real-time | 4/10 | 10/10 | Alto |
| Dashboard Builder | 0/10 | 9/10 | **Crítico** |
| Analytics/ML | 0/10 | 8/10 | Alto |
| Mobile UX | 5/10 | 8/10 | Médio |

---

## 🗺️ Roadmap de Implementação

### Fase 1: Fundação Analytics (8-10 semanas)
**Objetivo**: Query engine + Biblioteca de visualizações core

### Fase 2: Dashboard Builder (6-8 semanas)
**Objetivo**: Interface drag-and-drop para criação de dashboards

### Fase 3: Analytics Avançado (8-10 semanas)
**Objetivo**: ML/AI integration, predictive analytics

### Fase 4: Enterprise Features (6-8 semanas)
**Objetivo**: Multi-tenancy, row-level security, mobile app

---

## 📦 FASE 1: Fundação Analytics (8-10 semanas)

**Meta**: Criar a base para queries dinâmicas e visualizações avançadas

---

### 1.1 Query Engine Backend (3 semanas)

#### Objetivo
Implementar query engine flexível no backend que suporte agregações complexas, filtros multi-dimensionais e cross-tag queries.

#### Tecnologias
- **InfluxDB Flux Language** - Queries time-series avançadas
- **Pandas** - Manipulação de dados (correlação, estatísticas)
- **FastAPI Depends** - Query parameter validation

#### Implementação

**Novo endpoint: `/api/v1/analytics/query`**

```python
# backend/app/api/v1/endpoints/analytics.py

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class QueryFilter(BaseModel):
    field: str
    operator: str  # "eq", "ne", "gt", "lt", "gte", "lte", "in", "between"
    value: Any

class QueryAggregation(BaseModel):
    function: str  # "mean", "median", "stddev", "percentile", "correlation"
    field: str
    window: Optional[str] = "1m"
    params: Optional[Dict[str, Any]] = None  # Ex: {"percentile": 95}

class AnalyticsQuery(BaseModel):
    tags: List[str]  # Tag IDs
    start: datetime
    end: datetime
    filters: Optional[List[QueryFilter]] = []
    aggregations: List[QueryAggregation]
    group_by: Optional[List[str]] = []  # Ex: ["device_id", "site_id"]
    limit: Optional[int] = 1000

@router.post("/query", response_model=QueryResult)
async def execute_query(
    query: AnalyticsQuery,
    db: AsyncSession = Depends(get_db),
    influx: InfluxDBClient = Depends(get_influxdb)
):
    """
    Execute advanced analytics query

    Suporta:
    - Cross-tag comparisons
    - Multi-dimensional aggregations
    - Statistical functions (percentile, stddev, correlation)
    - Custom time windows
    """
    # Build Flux query
    flux_query = build_flux_query(query)

    # Execute in InfluxDB
    result = await influx.query(flux_query)

    # Post-process (correlations, custom calculations)
    if requires_pandas(query):
        df = to_pandas(result)
        df = apply_analytics(df, query)
        result = from_pandas(df)

    return QueryResult(
        data=result,
        metadata={
            "query_time_ms": elapsed,
            "rows": len(result),
            "tags_analyzed": len(query.tags)
        }
    )
```

**Novas agregações suportadas**:
- `mean`, `median`, `mode`
- `min`, `max`, `stddev`, `variance`
- `percentile` (P50, P95, P99)
- `correlation` (entre tags)
- `rate_of_change`
- `moving_average` (SMA, EMA, WMA)
- `cumulative_sum`
- `outlier_detection` (Z-score, IQR)

**Exemplo de query complexa**:
```json
{
  "tags": ["temp_sensor_01", "pressure_sensor_01"],
  "start": "2025-10-27T00:00:00Z",
  "end": "2025-10-28T00:00:00Z",
  "filters": [
    {"field": "quality", "operator": "eq", "value": "good"},
    {"field": "value", "operator": "between", "value": [20, 80]}
  ],
  "aggregations": [
    {
      "function": "percentile",
      "field": "value",
      "window": "1h",
      "params": {"percentile": 95}
    },
    {
      "function": "correlation",
      "field": "value",
      "params": {"target_tag": "pressure_sensor_01"}
    }
  ],
  "group_by": ["device_id"]
}
```

**Entregáveis**:
- [ ] Novo endpoint `/api/v1/analytics/query`
- [ ] Query builder (Flux + Pandas integration)
- [ ] 12 agregações avançadas implementadas
- [ ] Testes de performance (1000 tags, 7 dias)
- [ ] Documentação OpenAPI atualizada

---

### 1.2 Query Builder Frontend (2 semanas)

#### Objetivo
Interface visual para construção de queries sem código.

#### Componente: `<QueryBuilder>`

```tsx
// frontend/src/components/Analytics/QueryBuilder.tsx

interface QueryBuilderProps {
  onQueryChange: (query: AnalyticsQuery) => void;
  initialQuery?: AnalyticsQuery;
}

export function QueryBuilder({ onQueryChange, initialQuery }: QueryBuilderProps) {
  return (
    <div className="query-builder">
      {/* Tag Selection */}
      <TagSelector
        multiple
        onChange={handleTagsChange}
      />

      {/* Time Range */}
      <TimeRangePicker
        presets={['1h', '6h', '24h', '7d', '30d', 'custom']}
        onChange={handleTimeRangeChange}
      />

      {/* Filters */}
      <FilterBuilder
        fields={availableFields}
        onFiltersChange={handleFiltersChange}
      />

      {/* Aggregations */}
      <AggregationBuilder
        functions={aggregationFunctions}
        onAggregationsChange={handleAggregationsChange}
      />

      {/* Group By */}
      <GroupBySelector
        dimensions={['device_id', 'site_id', 'organization_id']}
        onChange={handleGroupByChange}
      />

      {/* Preview */}
      <QueryPreview query={currentQuery} />

      {/* Actions */}
      <Button onClick={executeQuery}>Run Query</Button>
      <Button onClick={saveQuery}>Save as Template</Button>
    </div>
  );
}
```

**Funcionalidades**:
- Multi-select de tags (com autocomplete)
- Time range picker (presets + custom)
- Filter builder visual (field + operator + value)
- Aggregation builder (função + janela + parâmetros)
- Query preview (JSON)
- Save/load query templates
- Query history (últimas 10 queries)

**Entregáveis**:
- [ ] Componente QueryBuilder completo
- [ ] 5 sub-componentes (TagSelector, TimeRangePicker, etc)
- [ ] Query templates (salvar/carregar)
- [ ] Query history persistente
- [ ] Testes E2E com Playwright

---

### 1.3 Biblioteca de Visualizações (3 semanas)

#### Objetivo
Implementar 15+ tipos de visualizações industriais usando Plotly.js e D3.

#### Novos Componentes

##### 1. **Gauge Chart** (Indicador Industrial)

```tsx
// frontend/src/components/Visualizations/GaugeChart.tsx

interface GaugeChartProps {
  value: number;
  min: number;
  max: number;
  unit: string;
  thresholds?: { value: number; color: string; label: string }[];
  title?: string;
}

export function GaugeChart({ value, min, max, unit, thresholds }: GaugeChartProps) {
  // Usando Plotly.js indicator gauge
  const data = [{
    type: "indicator",
    mode: "gauge+number+delta",
    value: value,
    title: { text: title },
    delta: { reference: previousValue },
    gauge: {
      axis: { range: [min, max] },
      bar: { color: getColorByThreshold(value, thresholds) },
      steps: thresholds.map(t => ({
        range: [t.value, t.value + 10],
        color: t.color
      })),
      threshold: {
        line: { color: "red", width: 4 },
        thickness: 0.75,
        value: max * 0.9
      }
    }
  }];

  return <Plot data={data} layout={layout} />;
}
```

**Uso**:
```tsx
<GaugeChart
  value={75.5}
  min={0}
  max={100}
  unit="°C"
  thresholds={[
    { value: 0, color: "green", label: "Normal" },
    { value: 70, color: "yellow", label: "Warning" },
    { value: 90, color: "red", label: "Critical" }
  ]}
  title="Temperature"
/>
```

---

##### 2. **Heatmap Chart** (Mapa de Calor)

```tsx
// frontend/src/components/Visualizations/HeatmapChart.tsx

interface HeatmapChartProps {
  data: number[][];  // Matrix de valores
  xLabels: string[];  // Labels do eixo X (ex: horas)
  yLabels: string[];  // Labels do eixo Y (ex: tags)
  colorScale?: string;  // "Viridis", "Jet", "Hot", etc
  title?: string;
}

export function HeatmapChart({ data, xLabels, yLabels, colorScale = "Viridis" }: HeatmapChartProps) {
  const plotlyData = [{
    z: data,
    x: xLabels,
    y: yLabels,
    type: 'heatmap',
    colorscale: colorScale,
    hovertemplate: '<b>%{y}</b><br>%{x}<br>Value: %{z}<extra></extra>'
  }];

  return <Plot data={plotlyData} layout={layout} />;
}
```

**Uso**:
```tsx
<HeatmapChart
  data={performanceMatrix}  // 24x7 (hours x days)
  xLabels={hours}
  yLabels={['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}
  colorScale="Viridis"
  title="Production Performance (Last Week)"
/>
```

---

##### 3. **Scatter Plot** (Correlação)

```tsx
// frontend/src/components/Visualizations/ScatterPlot.tsx

interface ScatterPlotProps {
  xData: number[];
  yData: number[];
  xLabel: string;
  yLabel: string;
  showTrendline?: boolean;
  showCorrelation?: boolean;
  groups?: string[];  // Para múltiplos grupos com cores
}

export function ScatterPlot({ xData, yData, xLabel, yLabel, showTrendline, showCorrelation }: ScatterPlotProps) {
  const correlation = showCorrelation ? calculateCorrelation(xData, yData) : null;

  const trace = {
    x: xData,
    y: yData,
    mode: 'markers',
    type: 'scatter',
    marker: { size: 8, color: 'rgba(31, 119, 180, 0.6)' }
  };

  const traces = [trace];

  if (showTrendline) {
    traces.push(calculateTrendline(xData, yData));
  }

  return (
    <div>
      <Plot data={traces} layout={layout} />
      {showCorrelation && (
        <div className="correlation-info">
          Correlation: <strong>{correlation.toFixed(3)}</strong>
          {correlation > 0.7 ? ' (Strong Positive)' : ''}
          {correlation < -0.7 ? ' (Strong Negative)' : ''}
        </div>
      )}
    </div>
  );
}
```

---

##### 4. **Multi-Axis Chart** (Trending Industrial)

```tsx
// frontend/src/components/Visualizations/MultiAxisChart.tsx

interface SeriesConfig {
  tagId: string;
  name: string;
  color: string;
  yAxis: 'left' | 'right';  // Eixo Y esquerdo ou direito
  unit: string;
  lineStyle?: 'solid' | 'dashed' | 'dotted';
}

interface MultiAxisChartProps {
  series: SeriesConfig[];
  data: TimeSeriesData[];
  showLegend?: boolean;
  showCrosshair?: boolean;
}

export function MultiAxisChart({ series, data, showLegend, showCrosshair }: MultiAxisChartProps) {
  // Suporta múltiplos eixos Y com diferentes unidades
  // Exemplo: Temperatura (°C) + Pressão (bar) no mesmo gráfico

  const traces = series.map(s => ({
    x: data.map(d => d.timestamp),
    y: data.map(d => d[s.tagId]),
    name: s.name,
    type: 'scatter',
    mode: 'lines',
    line: {
      color: s.color,
      dash: s.lineStyle === 'dashed' ? 'dash' : 'solid'
    },
    yaxis: s.yAxis === 'right' ? 'y2' : 'y'
  }));

  const layout = {
    xaxis: { title: 'Time' },
    yaxis: {
      title: series.filter(s => s.yAxis === 'left')[0]?.unit,
      side: 'left'
    },
    yaxis2: {
      title: series.filter(s => s.yAxis === 'right')[0]?.unit,
      overlaying: 'y',
      side: 'right'
    }
  };

  return <Plot data={traces} layout={layout} />;
}
```

---

##### 5. **Bar/Column Chart** (Comparações)

```tsx
// frontend/src/components/Visualizations/BarChart.tsx

interface BarChartProps {
  data: { label: string; value: number; color?: string }[];
  orientation?: 'horizontal' | 'vertical';
  stacked?: boolean;
  grouped?: boolean;
  showValues?: boolean;
}

export function BarChart({ data, orientation = 'vertical', showValues }: BarChartProps) {
  const trace = {
    x: orientation === 'vertical' ? data.map(d => d.label) : data.map(d => d.value),
    y: orientation === 'vertical' ? data.map(d => d.value) : data.map(d => d.label),
    type: 'bar',
    orientation: orientation === 'horizontal' ? 'h' : 'v',
    marker: { color: data.map(d => d.color || 'blue') },
    text: showValues ? data.map(d => d.value) : [],
    textposition: 'auto'
  };

  return <Plot data={[trace]} layout={layout} />;
}
```

---

##### 6. **Waterfall Chart** (Análise de Contribuição)

```tsx
// frontend/src/components/Visualizations/WaterfallChart.tsx

interface WaterfallItem {
  label: string;
  value: number;
  type: 'initial' | 'increase' | 'decrease' | 'total';
}

export function WaterfallChart({ data }: { data: WaterfallItem[] }) {
  // Mostra contribuições positivas/negativas
  // Útil para análise de eficiência (perdas em processo)

  const trace = {
    name: "Process Analysis",
    type: "waterfall",
    orientation: "v",
    measure: data.map(d => d.type === 'total' ? 'total' : 'relative'),
    x: data.map(d => d.label),
    y: data.map(d => d.value),
    connector: { line: { color: "rgb(63, 63, 63)" } }
  };

  return <Plot data={[trace]} layout={layout} />;
}
```

---

##### 7. **Geo-Spatial Map** (Sites/Assets)

```tsx
// frontend/src/components/Visualizations/GeoMap.tsx

interface MapMarker {
  lat: number;
  lon: number;
  name: string;
  status: 'online' | 'offline' | 'warning';
  value?: number;
}

export function GeoMap({ markers }: { markers: MapMarker[] }) {
  const data = [{
    type: 'scattermapbox',
    lat: markers.map(m => m.lat),
    lon: markers.map(m => m.lon),
    mode: 'markers',
    marker: {
      size: 14,
      color: markers.map(m => getColorByStatus(m.status))
    },
    text: markers.map(m => m.name),
    hovertemplate: '<b>%{text}</b><br>Status: %{marker.color}<extra></extra>'
  }];

  const layout = {
    mapbox: {
      style: 'open-street-map',
      center: { lat: -23.5505, lon: -46.6333 },  // São Paulo
      zoom: 10
    }
  };

  return <Plot data={data} layout={layout} />;
}
```

---

#### Lista Completa de Visualizações

| # | Componente | Tipo | Biblioteca | Use Case |
|---|-----------|------|------------|----------|
| 1 | GaugeChart | Gauge | Plotly | KPI real-time (temperatura, pressão) |
| 2 | HeatmapChart | Heatmap | Plotly | Performance matrix, correlação |
| 3 | ScatterPlot | Scatter | Plotly | Correlação entre variáveis |
| 4 | MultiAxisChart | Line (multi-Y) | Plotly | Trending com unidades diferentes |
| 5 | BarChart | Bar/Column | Plotly | Comparações categóricas |
| 6 | WaterfallChart | Waterfall | Plotly | Análise de contribuição/perdas |
| 7 | GeoMap | Geo-spatial | Plotly | Sites/assets em mapa |
| 8 | PieChart | Pie/Donut | Plotly | Distribuição percentual |
| 9 | BoxPlot | Box & Whisker | Plotly | Distribuição estatística |
| 10 | ViolinPlot | Violin | Plotly | Densidade de distribuição |
| 11 | RadarChart | Radar | Plotly | Comparação multi-dimensional |
| 12 | SankeyDiagram | Sankey | Plotly | Fluxo de energia/material |
| 13 | TreemapChart | Treemap | Plotly | Hierarquia de dados |
| 14 | SunburstChart | Sunburst | Plotly | Hierarquia circular |
| 15 | ThreeDSurface | 3D Surface | Plotly | Superfícies 3D (temperatura) |

**Entregáveis**:
- [ ] 15 componentes de visualização
- [ ] Storybook para cada componente
- [ ] Documentação de uso
- [ ] Testes visuais (screenshot testing)
- [ ] Performance benchmarks

---

### 1.4 Real-time WebSocket Integration (2 semanas)

#### Objetivo
Completar integração WebSocket para streaming real-time de dados.

#### Arquitetura

```
Industrial Device
    ↓
Gateway (coleta cada 5s)
    ↓
Backend API (processa)
    ↓
WebSocket Server (broadcast)
    ↓
Frontend (Socket.io client)
    ↓
Redux Store (atualização)
    ↓
React Components (re-render)
```

#### Backend: WebSocket Server

```python
# backend/app/websocket/manager.py

from fastapi import WebSocket
from typing import Dict, Set
import asyncio

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, tag_id: str):
        await websocket.accept()
        if tag_id not in self.active_connections:
            self.active_connections[tag_id] = set()
        self.active_connections[tag_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, tag_id: str):
        self.active_connections[tag_id].remove(websocket)

    async def broadcast_tag_update(self, tag_id: str, data: dict):
        """Broadcast to all clients subscribed to this tag"""
        if tag_id in self.active_connections:
            for connection in self.active_connections[tag_id]:
                await connection.send_json({
                    "type": "tag_update",
                    "tag_id": tag_id,
                    "timestamp": data["timestamp"],
                    "value": data["value"],
                    "quality": data["quality"]
                })

# backend/app/main.py

@app.websocket("/ws/tags/{tag_id}")
async def websocket_endpoint(websocket: WebSocket, tag_id: str):
    await ws_manager.connect(websocket, tag_id)
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, tag_id)
```

#### Frontend: WebSocket Client

```tsx
// frontend/src/services/websocket.ts

import { io, Socket } from 'socket.io-client';
import { store } from '../store';
import { updateTagValue } from '../store/slices/tagsSlice';

class WebSocketService {
  private socket: Socket | null = null;
  private subscribedTags: Set<string> = new Set();

  connect() {
    this.socket = io(process.env.VITE_WS_URL || 'ws://localhost:8000');

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      // Re-subscribe to all tags
      this.subscribedTags.forEach(tagId => this.subscribe(tagId));
    });

    this.socket.on('tag_update', (data) => {
      // Update Redux store
      store.dispatch(updateTagValue({
        tagId: data.tag_id,
        timestamp: data.timestamp,
        value: data.value,
        quality: data.quality
      }));
    });
  }

  subscribe(tagId: string) {
    if (this.socket && !this.subscribedTags.has(tagId)) {
      this.socket.emit('subscribe', { tag_id: tagId });
      this.subscribedTags.add(tagId);
    }
  }

  unsubscribe(tagId: string) {
    if (this.socket && this.subscribedTags.has(tagId)) {
      this.socket.emit('unsubscribe', { tag_id: tagId });
      this.subscribedTags.delete(tagId);
    }
  }
}

export const wsService = new WebSocketService();
```

#### React Hook

```tsx
// frontend/src/hooks/useRealtimeTag.ts

import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../hooks';
import { wsService } from '../services/websocket';

export function useRealtimeTag(tagId: string) {
  const dispatch = useAppDispatch();
  const tagData = useAppSelector(state => state.tags.data[tagId]);

  useEffect(() => {
    // Subscribe to real-time updates
    wsService.subscribe(tagId);

    return () => {
      // Unsubscribe on unmount
      wsService.unsubscribe(tagId);
    };
  }, [tagId]);

  return {
    value: tagData?.value,
    timestamp: tagData?.timestamp,
    quality: tagData?.quality,
    isConnected: wsService.isConnected()
  };
}
```

**Uso em componente**:
```tsx
function TemperatureGauge({ tagId }: { tagId: string }) {
  const { value, timestamp, quality, isConnected } = useRealtimeTag(tagId);

  return (
    <div>
      <ConnectionIndicator connected={isConnected} />
      <GaugeChart
        value={value}
        min={0}
        max={100}
        unit="°C"
        quality={quality}
      />
      <div className="timestamp">
        Last update: {formatTimestamp(timestamp)}
      </div>
    </div>
  );
}
```

**Entregáveis**:
- [ ] WebSocket server (FastAPI)
- [ ] WebSocket client (Socket.io)
- [ ] Connection manager (auto-reconnect)
- [ ] Redux integration
- [ ] useRealtimeTag hook
- [ ] Connection status indicator
- [ ] Performance test (1000 concurrent connections)

---

## 📦 FASE 2: Dashboard Builder (6-8 semanas)

**Meta**: Interface drag-and-drop para criação de dashboards customizados

---

### 2.1 Grid Layout Engine (2 semanas)

#### Tecnologia
- **react-grid-layout** - Drag-and-drop grid system

#### Componente: `<DashboardBuilder>`

```tsx
// frontend/src/components/DashboardBuilder/DashboardBuilder.tsx

import GridLayout from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';

interface Widget {
  id: string;
  type: 'gauge' | 'timeseries' | 'heatmap' | 'scatter' | 'bar' | 'stat';
  config: any;
  layout: { x: number; y: number; w: number; h: number };
}

interface DashboardConfig {
  id: string;
  name: string;
  widgets: Widget[];
  layout: 'fluid' | 'fixed';
  refreshInterval: number;  // seconds
}

export function DashboardBuilder({ dashboardId }: { dashboardId?: string }) {
  const [widgets, setWidgets] = useState<Widget[]>([]);
  const [layout, setLayout] = useState([]);

  const addWidget = (type: string) => {
    const newWidget: Widget = {
      id: generateId(),
      type,
      config: getDefaultConfig(type),
      layout: { x: 0, y: Infinity, w: 4, h: 4 }  // Append to bottom
    };
    setWidgets([...widgets, newWidget]);
  };

  const renderWidget = (widget: Widget) => {
    switch (widget.type) {
      case 'gauge':
        return <GaugeChart {...widget.config} />;
      case 'timeseries':
        return <TimeSeriesChart {...widget.config} />;
      case 'heatmap':
        return <HeatmapChart {...widget.config} />;
      // ... outros tipos
    }
  };

  return (
    <div className="dashboard-builder">
      <WidgetPalette onAddWidget={addWidget} />

      <GridLayout
        className="layout"
        layout={layout}
        cols={12}
        rowHeight={30}
        width={1200}
        onLayoutChange={setLayout}
        isDraggable={true}
        isResizable={true}
      >
        {widgets.map(widget => (
          <div key={widget.id} data-grid={widget.layout}>
            <WidgetContainer
              widget={widget}
              onEdit={() => openWidgetEditor(widget)}
              onDelete={() => deleteWidget(widget.id)}
            >
              {renderWidget(widget)}
            </WidgetContainer>
          </div>
        ))}
      </GridLayout>

      <DashboardActions
        onSave={saveDashboard}
        onExport={exportDashboard}
        onShare={shareDashboard}
      />
    </div>
  );
}
```

**Entregáveis**:
- [ ] Grid layout com drag-and-drop
- [ ] Widget palette (15+ widgets)
- [ ] Widget container (edit/delete/resize)
- [ ] Dashboard save/load
- [ ] Layout responsivo (mobile)

---

### 2.2 Widget Configuration Editor (2 semanas)

#### Objetivo
Editor visual para configurar cada widget sem código.

```tsx
// frontend/src/components/DashboardBuilder/WidgetEditor.tsx

interface WidgetEditorProps {
  widget: Widget;
  onSave: (config: any) => void;
  onCancel: () => void;
}

export function WidgetEditor({ widget, onSave, onCancel }: WidgetEditorProps) {
  return (
    <Dialog>
      <DialogTitle>Configure {widget.type} Widget</DialogTitle>
      <DialogContent>
        {/* Data Source */}
        <Section title="Data Source">
          <QueryBuilder
            initialQuery={widget.config.query}
            onChange={handleQueryChange}
          />
        </Section>

        {/* Visualization Settings */}
        <Section title="Visualization">
          {widget.type === 'gauge' && (
            <GaugeSettings
              min={widget.config.min}
              max={widget.config.max}
              thresholds={widget.config.thresholds}
              onChange={handleVisualizationChange}
            />
          )}

          {widget.type === 'timeseries' && (
            <TimeSeriesSettings
              chartType={widget.config.chartType}
              showLegend={widget.config.showLegend}
              yAxisRange={widget.config.yAxisRange}
              onChange={handleVisualizationChange}
            />
          )}
        </Section>

        {/* Display Settings */}
        <Section title="Display">
          <Input label="Title" value={widget.config.title} />
          <ColorPicker label="Color" value={widget.config.color} />
          <Select label="Refresh Rate" options={refreshRates} />
        </Section>

        {/* Preview */}
        <Section title="Preview">
          {renderWidget(widget)}
        </Section>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>Cancel</Button>
        <Button onClick={() => onSave(widget.config)}>Save</Button>
      </DialogActions>
    </Dialog>
  );
}
```

**Entregáveis**:
- [ ] Widget editor modal
- [ ] Type-specific configuration forms
- [ ] Live preview
- [ ] Validation (required fields)
- [ ] Default templates

---

### 2.3 Dashboard Templates (1 semana)

#### Objetivo
Dashboards pré-construídos para acelerar implementação.

**Templates Industriais**:

1. **Production Overview**
   - 4 gauges (temperatura, pressão, flow, level)
   - 1 timeseries (produção last 24h)
   - 1 bar chart (produção por turno)
   - 1 stat card (OEE)

2. **Energy Management**
   - 1 heatmap (consumo por hora/dia)
   - 2 timeseries (demanda vs. contrato)
   - 1 pie chart (distribuição por área)
   - 3 stat cards (kWh, custo, pico)

3. **Maintenance Dashboard**
   - 1 geo map (equipamentos)
   - 1 scatter plot (MTBF vs. MTTR)
   - 1 waterfall (downtime contributors)
   - 1 bar chart (top 10 failures)

4. **Quality Control**
   - 3 gauges (Cpk, defect rate, yield)
   - 1 control chart (X-bar & R)
   - 1 pareto chart (defect types)
   - 1 histogram (measurement distribution)

**Implementação**:
```tsx
// frontend/src/templates/dashboardTemplates.ts

export const templates: DashboardTemplate[] = [
  {
    id: 'production-overview',
    name: 'Production Overview',
    description: 'Monitor real-time production metrics',
    category: 'Operations',
    widgets: [
      {
        type: 'gauge',
        layout: { x: 0, y: 0, w: 3, h: 4 },
        config: {
          title: 'Temperature',
          query: { tags: ['temp_sensor'], aggregation: 'mean' },
          min: 0,
          max: 100,
          unit: '°C',
          thresholds: [
            { value: 80, color: 'yellow' },
            { value: 90, color: 'red' }
          ]
        }
      },
      // ... mais 7 widgets
    ]
  },
  // ... mais templates
];
```

**Entregáveis**:
- [ ] 10 dashboard templates
- [ ] Template gallery
- [ ] Template preview
- [ ] "Use Template" button
- [ ] Template customization

---

### 2.4 Dashboard Sharing & Permissions (1-2 semanas)

#### Objetivo
Compartilhar dashboards entre usuários/equipes com controle de acesso.

**Features**:
- Public link (read-only, com token)
- Share with users (read/write permissions)
- Share with organization (everyone can view)
- Embed code (iframe para sistemas externos)

```tsx
// frontend/src/components/DashboardBuilder/ShareDialog.tsx

export function ShareDialog({ dashboard }: { dashboard: Dashboard }) {
  const [shareMode, setShareMode] = useState<'private' | 'users' | 'public'>('private');
  const [publicLink, setPublicLink] = useState('');

  const generatePublicLink = async () => {
    const response = await api.post(`/dashboards/${dashboard.id}/share`, {
      mode: 'public',
      expiresIn: '30d'
    });
    setPublicLink(response.data.link);
  };

  return (
    <Dialog>
      <Select value={shareMode} onChange={setShareMode}>
        <option value="private">Private (only me)</option>
        <option value="users">Specific users</option>
        <option value="public">Public link</option>
      </Select>

      {shareMode === 'users' && (
        <UserSelector
          multiple
          onUsersChange={handleUsersChange}
        />
      )}

      {shareMode === 'public' && (
        <div>
          <Button onClick={generatePublicLink}>Generate Link</Button>
          {publicLink && (
            <Input value={publicLink} readOnly />
          )}
        </div>
      )}

      <EmbedCode dashboard={dashboard} />
    </Dialog>
  );
}
```

**Backend**:
```python
# backend/app/api/v1/endpoints/dashboards.py

@router.post("/{dashboard_id}/share")
async def share_dashboard(
    dashboard_id: UUID,
    share_request: ShareRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Share dashboard com controle de acesso
    """
    if share_request.mode == "public":
        # Gerar token único
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=30)

        # Salvar no banco
        shared_link = SharedDashboard(
            dashboard_id=dashboard_id,
            token=token,
            expires_at=expires_at,
            created_by=current_user.id
        )
        db.add(shared_link)
        await db.commit()

        return {
            "link": f"{settings.FRONTEND_URL}/public/dashboards/{token}"
        }
    elif share_request.mode == "users":
        # Adicionar permissões por usuário
        for user_id in share_request.user_ids:
            permission = DashboardPermission(
                dashboard_id=dashboard_id,
                user_id=user_id,
                role=share_request.role  # "viewer" ou "editor"
            )
            db.add(permission)
        await db.commit()

        return {"shared_with": len(share_request.user_ids)}
```

**Entregáveis**:
- [ ] Share dialog
- [ ] Public link generation
- [ ] User permissions (viewer/editor)
- [ ] Embed code generator
- [ ] Access control middleware

---

## 🧠 FASE 3: Analytics Avançado (8-10 semanas)

**Meta**: Machine Learning, predictive analytics, e automação

---

### 3.1 Predictive Maintenance (3 semanas)

#### Objetivo
Prever falhas de equipamento antes que ocorram.

#### Tecnologias
- **scikit-learn** - ML models (Random Forest, XGBoost)
- **Prophet** - Time series forecasting (Facebook)
- **Optuna** - Hyperparameter tuning

#### Modelo: Failure Prediction

```python
# backend/app/ml/predictive_maintenance.py

from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import joblib

class FailurePredictionModel:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100)
        self.feature_columns = [
            'temperature_mean', 'temperature_std',
            'vibration_mean', 'vibration_std',
            'pressure_mean', 'pressure_std',
            'runtime_hours',
            'cycles_count'
        ]

    async def train(self, device_id: str):
        """
        Treinar modelo com histórico de falhas do device
        """
        # Obter histórico
        historical_data = await get_device_history(device_id)
        failures = await get_device_failures(device_id)

        # Feature engineering
        X = self.extract_features(historical_data)
        y = self.create_labels(historical_data, failures)

        # Train
        self.model.fit(X, y)

        # Save
        model_path = f"models/device_{device_id}_failure.pkl"
        joblib.dump(self.model, model_path)

        # Evaluate
        metrics = self.evaluate(X, y)
        return metrics

    async def predict(self, device_id: str):
        """
        Prever probabilidade de falha nas próximas 24h
        """
        # Load model
        model_path = f"models/device_{device_id}_failure.pkl"
        self.model = joblib.load(model_path)

        # Get current features
        current_data = await get_device_current_data(device_id)
        X = self.extract_features(current_data)

        # Predict
        probability = self.model.predict_proba(X)[0][1]

        return {
            "device_id": device_id,
            "failure_probability": probability,
            "risk_level": "high" if probability > 0.7 else "medium" if probability > 0.4 else "low",
            "predicted_failure_in_hours": int(24 * (1 - probability)),
            "top_features": self.get_feature_importance()
        }

    def extract_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Feature engineering: agregações estatísticas
        """
        features = pd.DataFrame()

        # Temperature features
        features['temperature_mean'] = data['temperature'].mean()
        features['temperature_std'] = data['temperature'].std()
        features['temperature_max'] = data['temperature'].max()

        # Vibration features
        features['vibration_mean'] = data['vibration'].mean()
        features['vibration_std'] = data['vibration'].std()

        # Pressure features
        features['pressure_mean'] = data['pressure'].mean()
        features['pressure_std'] = data['pressure'].std()

        # Runtime
        features['runtime_hours'] = (data['timestamp'].max() - data['timestamp'].min()).total_seconds() / 3600

        return features
```

#### Frontend: Predictive Maintenance Dashboard

```tsx
// frontend/src/pages/PredictiveMaintenancePage.tsx

export function PredictiveMaintenancePage() {
  const [predictions, setPredictions] = useState([]);

  useEffect(() => {
    // Load predictions for all devices
    loadPredictions();
  }, []);

  return (
    <div className="predictive-maintenance">
      <Header title="Predictive Maintenance" />

      {/* Risk Summary */}
      <RiskSummaryCards predictions={predictions} />

      {/* High Risk Devices */}
      <Section title="High Risk Devices (Next 24h)">
        <DeviceRiskTable
          devices={predictions.filter(p => p.risk_level === 'high')}
        />
      </Section>

      {/* Failure Probability Chart */}
      <Section title="Failure Probability Trends">
        <FailureProbabilityChart data={predictions} />
      </Section>

      {/* Feature Importance */}
      <Section title="Contributing Factors">
        <FeatureImportanceChart features={selectedDevice?.top_features} />
      </Section>

      {/* Maintenance Recommendations */}
      <Section title="Recommended Actions">
        <MaintenanceRecommendations predictions={predictions} />
      </Section>
    </div>
  );
}
```

**Entregáveis**:
- [ ] ML model training pipeline
- [ ] Feature engineering (15+ features)
- [ ] Model evaluation (precision, recall, F1)
- [ ] Prediction API endpoint
- [ ] Predictive maintenance dashboard
- [ ] Alert integration (high risk → alarm)
- [ ] Model retraining scheduler (weekly)

---

### 3.2 Anomaly Detection (2 semanas)

#### Objetivo
Detectar comportamentos anômalos automaticamente.

#### Tecnologias
- **Isolation Forest** - Unsupervised anomaly detection
- **LSTM Autoencoders** - Deep learning para séries temporais

#### Modelo: Real-time Anomaly Detection

```python
# backend/app/ml/anomaly_detection.py

from sklearn.ensemble import IsolationForest
import numpy as np

class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.05)  # 5% anomalies expected

    async def detect(self, tag_id: str, window_minutes: int = 60):
        """
        Detectar anomalias nas últimas N minutos
        """
        # Get recent data
        data = await get_tag_data(
            tag_id=tag_id,
            start=datetime.utcnow() - timedelta(minutes=window_minutes)
        )

        # Extract features
        X = self.extract_features(data)

        # Predict anomalies
        predictions = self.model.predict(X)  # -1 = anomaly, 1 = normal
        anomaly_scores = self.model.score_samples(X)

        # Find anomalies
        anomalies = []
        for i, pred in enumerate(predictions):
            if pred == -1:
                anomalies.append({
                    "timestamp": data[i]['timestamp'],
                    "value": data[i]['value'],
                    "anomaly_score": float(anomaly_scores[i]),
                    "severity": self.calculate_severity(anomaly_scores[i])
                })

        return anomalies
```

**Entregáveis**:
- [ ] Anomaly detection model
- [ ] Real-time detection (streaming)
- [ ] Anomaly visualization
- [ ] Automatic alarm creation
- [ ] False positive feedback loop

---

### 3.3 Forecasting (2 semanas)

#### Objetivo
Prever valores futuros de tags (demand forecasting, capacity planning).

#### Tecnologia
- **Prophet** (Facebook) - Time series forecasting

```python
# backend/app/ml/forecasting.py

from prophet import Prophet
import pandas as pd

class Forecaster:
    async def forecast(
        self,
        tag_id: str,
        horizon_hours: int = 24,
        confidence_interval: float = 0.95
    ):
        """
        Prever valores futuros com intervalo de confiança
        """
        # Get historical data (last 30 days)
        data = await get_tag_data(
            tag_id=tag_id,
            start=datetime.utcnow() - timedelta(days=30)
        )

        # Prepare data for Prophet
        df = pd.DataFrame({
            'ds': [d['timestamp'] for d in data],
            'y': [d['value'] for d in data]
        })

        # Train model
        model = Prophet(
            interval_width=confidence_interval,
            daily_seasonality=True,
            weekly_seasonality=True
        )
        model.fit(df)

        # Create future dataframe
        future = model.make_future_dataframe(periods=horizon_hours, freq='H')

        # Predict
        forecast = model.predict(future)

        return {
            "tag_id": tag_id,
            "forecast_horizon_hours": horizon_hours,
            "predictions": [
                {
                    "timestamp": row['ds'],
                    "predicted_value": row['yhat'],
                    "lower_bound": row['yhat_lower'],
                    "upper_bound": row['yhat_upper']
                }
                for _, row in forecast.tail(horizon_hours).iterrows()
            ]
        }
```

**Entregáveis**:
- [ ] Forecasting model (Prophet)
- [ ] API endpoint
- [ ] Forecast visualization (with confidence bands)
- [ ] Capacity planning dashboard
- [ ] Demand forecasting reports

---

### 3.4 Root Cause Analysis (1-2 semanas)

#### Objetivo
Identificar causa raiz de problemas automaticamente.

#### Técnica
- **Correlation Analysis** - Identificar tags correlacionados com alarme
- **Causal Discovery** - DAG (Directed Acyclic Graph) de causalidade

```python
# backend/app/ml/root_cause_analysis.py

async def analyze_root_cause(alarm_id: UUID):
    """
    Analisar causa raiz de um alarme
    """
    # Get alarm details
    alarm = await get_alarm(alarm_id)

    # Get all tags in same device/site
    related_tags = await get_related_tags(alarm.tag_id)

    # Get data window around alarm
    window_before = timedelta(hours=1)
    data = await get_multi_tag_data(
        tag_ids=related_tags,
        start=alarm.triggered_at - window_before,
        end=alarm.triggered_at
    )

    # Calculate correlations
    correlations = calculate_correlations(data, alarm.tag_id)

    # Find high correlations (potential causes)
    suspects = [
        tag for tag, corr in correlations.items()
        if abs(corr) > 0.7  # Strong correlation
    ]

    # Time-lagged correlation (which happened first?)
    causal_chain = analyze_time_lags(data, suspects, alarm.tag_id)

    return {
        "alarm_id": alarm_id,
        "root_causes": [
            {
                "tag_id": tag,
                "tag_name": tag_names[tag],
                "correlation": correlations[tag],
                "time_lag_minutes": causal_chain[tag]['lag'],
                "confidence": causal_chain[tag]['confidence']
            }
            for tag in suspects
        ],
        "recommendation": generate_recommendation(suspects, causal_chain)
    }
```

**Entregáveis**:
- [ ] Root cause analysis algorithm
- [ ] Correlation heatmap
- [ ] Causal chain visualization
- [ ] Automatic recommendations
- [ ] Integration with alarm page

---

## 🏢 FASE 4: Enterprise Features (6-8 semanas)

**Meta**: Recursos para uso enterprise (multi-tenancy, mobile, compliance)

---

### 4.1 Row-Level Security (2 semanas)

#### Objetivo
Controle fino de acesso a dados (por site, device, tag).

```python
# backend/app/core/security.py

class RowLevelSecurity:
    @staticmethod
    async def filter_query_by_user_permissions(
        query: Any,
        model: Type[Base],
        user: User,
        db: AsyncSession
    ):
        """
        Aplica filtros de segurança baseado em permissões do usuário
        """
        # Admin vê tudo
        if user.role == "admin":
            return query

        # Site manager vê apenas seus sites
        if user.role == "site_manager":
            user_sites = await get_user_sites(user.id, db)
            if model == Site:
                query = query.filter(Site.id.in_(user_sites))
            elif model == Device:
                query = query.filter(Device.site_id.in_(user_sites))
            elif model == Tag:
                device_ids = await get_devices_from_sites(user_sites, db)
                query = query.filter(Tag.device_id.in_(device_ids))

        # Operator vê apenas devices atribuídos
        elif user.role == "operator":
            user_devices = await get_user_devices(user.id, db)
            if model == Device:
                query = query.filter(Device.id.in_(user_devices))
            elif model == Tag:
                query = query.filter(Tag.device_id.in_(user_devices))

        return query
```

**Entregáveis**:
- [ ] RLS middleware
- [ ] Permission system (role-based + resource-based)
- [ ] User assignment UI (assign sites/devices)
- [ ] Audit log (who accessed what)
- [ ] Performance optimization (permission caching)

---

### 4.2 Mobile App (React Native) (4 semanas)

#### Objetivo
App mobile para monitoramento em campo.

**Features Principais**:
- Real-time dashboards (otimizado para mobile)
- Alarm notifications (push)
- Offline mode (last known values)
- Camera integration (photos de equipamentos)
- Geolocation (check-in em sites)

```tsx
// mobile/src/screens/DashboardScreen.tsx

import { View, ScrollView, RefreshControl } from 'react-native';
import { GaugeWidget, ChartWidget } from '../components/Widgets';

export function DashboardScreen() {
  const [refreshing, setRefreshing] = useState(false);
  const { dashboards } = useDashboards();

  const onRefresh = async () => {
    setRefreshing(true);
    await refetchData();
    setRefreshing(false);
  };

  return (
    <ScrollView
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* KPI Cards */}
      <View style={styles.kpiContainer}>
        <GaugeWidget tagId="temp_01" />
        <GaugeWidget tagId="pressure_01" />
      </View>

      {/* Main Chart */}
      <ChartWidget
        tagIds={['temp_01', 'pressure_01']}
        range="24h"
      />

      {/* Alarms */}
      <AlarmsList filter={{ status: 'active' }} />
    </ScrollView>
  );
}
```

**Entregáveis**:
- [ ] React Native app (iOS + Android)
- [ ] 5 telas principais (Dashboard, Alarms, Sites, Devices, Settings)
- [ ] Push notifications (Firebase Cloud Messaging)
- [ ] Offline mode (AsyncStorage)
- [ ] Camera integration
- [ ] App store deployment

---

### 4.3 Compliance & Audit Trail (1-2 semanas)

#### Objetivo
Compliance com regulamentações (FDA 21 CFR Part 11, ISO 27001, LGPD).

**Features**:
- Audit trail completo (quem/quando/o quê)
- Electronic signatures (aprovações)
- Data retention policies
- LGPD compliance (direito ao esquecimento)

```python
# backend/app/models/audit.py

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    action = Column(String)  # "create", "update", "delete", "read"
    resource_type = Column(String)  # "device", "tag", "alarm"
    resource_id = Column(UUID)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    ip_address = Column(String)
    user_agent = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Compliance
    reason = Column(String, nullable=True)  # Reason for change (FDA requirement)
    reviewed_by = Column(UUID, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
```

**Entregáveis**:
- [ ] Audit log model + API
- [ ] Audit log viewer (filtros avançados)
- [ ] Electronic signature workflow
- [ ] Data retention automation
- [ ] LGPD compliance endpoints (export/delete user data)
- [ ] Compliance reports (PDF)

---

## 📊 Resumo Executivo do Roadmap

### Timeline Completo

| Fase | Duração | Esforço (person-weeks) | Prioridade |
|------|---------|------------------------|------------|
| **Fase 1: Fundação** | 8-10 semanas | 20-24 weeks | **Crítica** |
| **Fase 2: Dashboard Builder** | 6-8 semanas | 12-16 weeks | **Alta** |
| **Fase 3: Analytics Avançado** | 8-10 semanas | 16-20 weeks | Média |
| **Fase 4: Enterprise** | 6-8 semanas | 12-16 weeks | Média |
| **TOTAL** | **28-36 semanas** | **60-76 weeks** | |

### Equipe Recomendada

Para implementar em **7-9 meses** (paralelo):
- 2 Backend developers (Python/FastAPI)
- 2 Frontend developers (React/TypeScript)
- 1 ML engineer (Python/scikit-learn)
- 1 UX/UI designer
- 1 QA engineer
- 1 DevOps (CI/CD, infraestrutura)

### Investimento Estimado

| Categoria | Custo (USD) |
|-----------|-------------|
| Desenvolvimento | $300k - $450k |
| Infraestrutura (Cloud) | $24k/ano |
| Licenças (se necessário) | $10k/ano |
| QA/Testing | $50k |
| **TOTAL (ano 1)** | **$384k - $534k** |

### ROI Esperado

**Diferenciais Competitivos**:
- Queries dinâmicas → **+40% produtividade analistas**
- Visualizações avançadas → **+30% identificação problemas**
- Predictive maintenance → **-25% downtime não planejado**
- Dashboard builder → **-60% tempo criação dashboards**

**Valor de Mercado**:
- Software similar: **$50k-$200k/ano por site**
- Nosso preço competitivo: **$30k-$100k/ano**
- Margem: **60-70%**

---

## 🎯 Recomendação Estratégica

### Abordagem Phased Release

**Versão 2.0 (Fase 1 + 2.1)**: *3-4 meses*
- Query engine completo
- 15 tipos de visualização
- Real-time WebSocket
- Grid layout básico (sem full builder)

**Lançamento**: Q2 2026

**Versão 2.5 (Fase 2 completa)**: *2-3 meses*
- Dashboard builder completo
- Templates library
- Sharing & permissions

**Lançamento**: Q3 2026

**Versão 3.0 (Fase 3)**: *3-4 meses*
- Predictive maintenance
- Anomaly detection
- Forecasting
- Root cause analysis

**Lançamento**: Q4 2026

**Versão 3.5 (Fase 4)**: *2-3 meses*
- Mobile app
- RLS completo
- Compliance features

**Lançamento**: Q1 2027

---

## 📈 Métricas de Sucesso

### KPIs Técnicos
- Query response time < 500ms (P95)
- Dashboard load time < 2s
- Real-time latency < 100ms
- Mobile app rating > 4.5 stars
- ML model accuracy > 90%

### KPIs de Negócio
- Redução 60% no tempo de criação de dashboards
- Aumento 40% no uso da plataforma
- NPS > 50
- Customer acquisition cost -30%
- Churn rate < 5%

---

## 🚀 Próximos Passos Imediatos

1. **Aprovação Executiva** (1 semana)
   - Apresentar roadmap para stakeholders
   - Aprovar budget
   - Definir prioridades

2. **Hiring** (4-6 semanas)
   - Contratar equipe (7 pessoas)
   - Onboarding

3. **Sprint 0** (2 semanas)
   - Setup ambiente de desenvolvimento
   - Definir arquitetura detalhada
   - Criar backlog detalhado

4. **Fase 1 Sprint 1** (2 semanas)
   - Implementar query engine backend (agregações básicas)
   - Implementar 3 primeiros componentes de visualização

---

**Documento criado por**: Claude Code (SmartPort Development Team)
**Data**: 2025-10-28
**Versão**: 1.0
