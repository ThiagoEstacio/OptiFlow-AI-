# SmartPort - Data Visualization Enhancement Plan

## Current Visualizations ✅

1. **Port Map** - SVG-based berth visualization
2. **KPI Cards** - 8 metric cards with progress bars
3. **Operation Progress** - Individual operation cards with progress
4. **Vessel Table** - List view of vessels
5. **Berth Grid** - Card grid of berths

## Missing Visualizations ❌

### 1. Time Series Charts (MISSING)

#### A. Berth Occupancy Over Time
```typescript
// frontend/src/components/smartport/charts/BerthOccupancyChart.tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export const BerthOccupancyChart: React.FC = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    // Fetch occupancy history
    fetch('/api/v1/smartport/analytics/berth-occupancy?days=7')
      .then(res => res.json())
      .then(data => setData(data));
  }, []);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="occupancy_rate" stroke="#3b82f6" name="Occupancy %" />
        <Line type="monotone" dataKey="available" stroke="#10b981" name="Available" />
        <Line type="monotone" dataKey="occupied" stroke="#ef4444" name="Occupied" />
      </LineChart>
    </ResponsiveContainer>
  );
};
```

#### B. Container Throughput Chart
```typescript
// frontend/src/components/smartport/charts/ThroughputChart.tsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

export const ThroughputChart: React.FC = () => {
  return (
    <BarChart width={600} height={300} data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="date" />
      <YAxis />
      <Tooltip />
      <Legend />
      <Bar dataKey="containers_loaded" fill="#10b981" name="Loaded" />
      <Bar dataKey="containers_unloaded" fill="#3b82f6" name="Unloaded" />
    </BarChart>
  );
};
```

#### C. Vessel Timeline (Gantt Chart)
```typescript
// frontend/src/components/smartport/charts/VesselTimeline.tsx
import { Chart } from 'react-google-charts';

export const VesselTimeline: React.FC = () => {
  const columns = [
    { type: 'string', label: 'Vessel' },
    { type: 'string', label: 'Berth' },
    { type: 'date', label: 'Start' },
    { type: 'date', label: 'End' },
  ];

  const rows = [
    ['MSC Gülsün', 'T1-A', new Date(2024, 0, 1, 8, 0), new Date(2024, 0, 1, 20, 0)],
    ['EVER GIVEN', 'T1-B', new Date(2024, 0, 1, 10, 0), new Date(2024, 0, 2, 6, 0)],
    // ...
  ];

  return (
    <Chart
      chartType="Timeline"
      data={[columns, ...rows]}
      width="100%"
      height="400px"
    />
  );
};
```

### 2. Real-time Process Monitoring (MISSING)

#### A. Live Operation Dashboard
```typescript
// frontend/src/components/smartport/LiveOperationMonitor.tsx
export const LiveOperationMonitor: React.FC = () => {
  const { operations, connected } = useSmartPort();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Live crane movements */}
      <div className="bg-white rounded-lg p-6">
        <h3>Crane Activity</h3>
        <CraneActivityChart operations={operations} />
      </div>

      {/* Container flow rate */}
      <div className="bg-white rounded-lg p-6">
        <h3>Container Flow (per hour)</h3>
        <LineChart data={containerFlowData}>
          <Line dataKey="rate" stroke="#3b82f6" strokeWidth={3} />
        </LineChart>
      </div>

      {/* Productivity heatmap */}
      <div className="col-span-2">
        <ProductivityHeatmap />
      </div>
    </div>
  );
};
```

#### B. Vessel Tracking Map (with Leaflet)
```typescript
// frontend/src/components/smartport/VesselTrackingMap.tsx
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';

export const VesselTrackingMap: React.FC = () => {
  const { vessels } = useSmartPort();

  // Custom vessel icon
  const vesselIcon = new L.Icon({
    iconUrl: '/icons/vessel.png',
    iconSize: [30, 30],
  });

  return (
    <MapContainer center={[-23.9618, -46.3322]} zoom={13} style={{ height: '600px' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap contributors'
      />

      {/* Vessels */}
      {vessels.map((vessel) => (
        vessel.last_latitude && vessel.last_longitude && (
          <Marker
            key={vessel.id}
            position={[vessel.last_latitude, vessel.last_longitude]}
            icon={vesselIcon}
          >
            <Popup>
              <div>
                <h4 className="font-bold">{vessel.name}</h4>
                <p>IMO: {vessel.imo}</p>
                <p>Speed: {vessel.speed_knots} knots</p>
                <p>Heading: {vessel.heading}°</p>
              </div>
            </Popup>
          </Marker>
        )
      ))}

      {/* Vessel trajectories */}
      {vessels.map((vessel) =>
        vessel.trajectory && (
          <Polyline
            key={`trajectory-${vessel.id}`}
            positions={vessel.trajectory}
            color="blue"
            weight={2}
          />
        )
      )}
    </MapContainer>
  );
};
```

### 3. Analytics Dashboard (MISSING)

#### A. Performance Analytics
```typescript
// frontend/src/pages/AnalyticsPage.tsx
export const AnalyticsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* KPI comparison */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KPICard
          title="This Week"
          value={kpis.thisWeek}
          change="+12%"
          trend="up"
        />
        <KPICard
          title="Last Week"
          value={kpis.lastWeek}
          change="+8%"
          trend="up"
        />
        <KPICard
          title="Monthly Avg"
          value={kpis.monthlyAvg}
          change="-2%"
          trend="down"
        />
      </div>

      {/* Trend charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ThroughputTrendChart />
        <EfficiencyTrendChart />
        <BerthUtilizationChart />
        <VesselWaitTimeChart />
      </div>

      {/* Detailed analytics table */}
      <OperationAnalyticsTable />
    </div>
  );
};
```

#### B. Berth Utilization Heatmap
```typescript
// frontend/src/components/smartport/BerthUtilizationHeatmap.tsx
import { HeatMapGrid } from 'react-grid-heatmap';

export const BerthUtilizationHeatmap: React.FC = () => {
  // Data: [hour][berth] = utilization %
  const data = [
    [100, 80, 60, 90, 100, 70, 85, 95, 100, 80],  // 00:00
    [100, 85, 65, 90, 100, 75, 85, 95, 100, 85],  // 01:00
    // ... 24 hours
  ];

  const berths = ['T1-A', 'T1-B', 'T2-A', 'T2-B', ...];
  const hours = ['00:00', '01:00', '02:00', ...];

  return (
    <div className="bg-white rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Berth Utilization (24h)</h3>
      <HeatMapGrid
        data={data}
        xLabels={berths}
        yLabels={hours}
        cellStyle={(x, y, ratio) => ({
          background: `rgba(59, 130, 246, ${ratio})`,
          fontSize: '11px',
          color: ratio > 0.5 ? 'white' : 'black',
        })}
        cellRender={(x, y, value) => `${value}%`}
      />
    </div>
  );
};
```

### 4. Predictive Analytics Visualizations (MISSING)

#### A. Berth Allocation Prediction
```typescript
// frontend/src/components/smartport/BerthAllocationPredictor.tsx
export const BerthAllocationPredictor: React.FC = () => {
  const [prediction, setPrediction] = useState(null);

  const predictBerth = async (vesselData) => {
    const response = await fetch('/api/v1/smartport/ml/predict-berth', {
      method: 'POST',
      body: JSON.stringify(vesselData),
    });
    const data = await response.json();
    setPrediction(data);
  };

  return (
    <div className="bg-white rounded-lg p-6">
      <h3>AI Berth Recommendation</h3>

      {prediction && (
        <div className="space-y-4">
          <div className="border-l-4 border-green-500 pl-4">
            <p className="font-semibold">Recommended: {prediction.berth_name}</p>
            <p className="text-sm text-gray-600">
              Confidence: {(prediction.confidence * 100).toFixed(1)}%
            </p>
          </div>

          {/* Alternative berths */}
          <div>
            <p className="font-medium mb-2">Alternatives:</p>
            {prediction.alternatives.map((alt, i) => (
              <div key={i} className="flex justify-between text-sm">
                <span>{alt.berth_name}</span>
                <span className="text-gray-600">{(alt.score * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>

          {/* Reasoning */}
          <div className="bg-blue-50 p-3 rounded">
            <p className="text-sm font-medium">Why this berth?</p>
            <ul className="text-xs text-gray-700 mt-2 space-y-1">
              <li>✓ Optimal crane capacity match</li>
              <li>✓ Minimal vessel repositioning</li>
              <li>✓ Available during ETA window</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};
```

#### B. Operation Time Prediction
```typescript
// frontend/src/components/smartport/OperationTimePrediction.tsx
import { GaugeChart } from 'react-gauge-chart';

export const OperationTimePrediction: React.FC = () => {
  const [prediction, setPrediction] = useState(null);

  return (
    <div className="bg-white rounded-lg p-6">
      <h3>Estimated Operation Time</h3>

      <div className="grid grid-cols-2 gap-4 mt-4">
        <div>
          <GaugeChart
            id="predicted-time-gauge"
            percent={prediction?.confidence || 0}
            textColor="#000"
            formatTextValue={() => `${prediction?.predicted_hours || 0}h`}
          />
        </div>

        <div className="space-y-2">
          <div>
            <p className="text-sm text-gray-600">Predicted Time</p>
            <p className="text-2xl font-bold">{prediction?.predicted_hours}h</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Confidence Range</p>
            <p className="text-sm">
              {prediction?.min_hours}h - {prediction?.max_hours}h
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Historical Average</p>
            <p className="text-sm">{prediction?.historical_avg}h</p>
          </div>
        </div>
      </div>

      {/* Factors affecting prediction */}
      <div className="mt-4 border-t pt-4">
        <p className="font-medium text-sm mb-2">Key Factors:</p>
        <div className="space-y-2">
          {prediction?.factors.map((factor, i) => (
            <div key={i} className="flex justify-between text-sm">
              <span>{factor.name}</span>
              <span className={factor.impact > 0 ? 'text-red-600' : 'text-green-600'}>
                {factor.impact > 0 ? '+' : ''}{factor.impact}h
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
```

### 5. Reporting & Export (MISSING)

#### A. PDF Report Generation
```typescript
// frontend/src/components/smartport/ReportGenerator.tsx
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

export const ReportGenerator: React.FC = () => {
  const generatePDFReport = async () => {
    const doc = new jsPDF();

    // Add header
    doc.setFontSize(20);
    doc.text('SmartPort Daily Report', 20, 20);

    // Add KPIs
    doc.setFontSize(12);
    doc.text(`Date: ${new Date().toLocaleDateString()}`, 20, 40);
    doc.text(`Total Operations: ${kpis.total_operations}`, 20, 50);
    doc.text(`Containers Handled: ${kpis.containers}`, 20, 60);

    // Capture charts as images
    const chartElement = document.getElementById('throughput-chart');
    const canvas = await html2canvas(chartElement);
    const imgData = canvas.toDataURL('image/png');
    doc.addImage(imgData, 'PNG', 20, 80, 170, 100);

    // Save PDF
    doc.save(`smartport-report-${new Date().toISOString().split('T')[0]}.pdf`);
  };

  return (
    <button onClick={generatePDFReport} className="btn btn-primary">
      Generate PDF Report
    </button>
  );
};
```

#### B. Excel Export with Charts
```typescript
// frontend/src/components/smartport/ExcelExporter.tsx
import * as XLSX from 'xlsx';

export const exportToExcel = async () => {
  const workbook = XLSX.utils.book_new();

  // Berths sheet
  const berthsData = berths.map(b => ({
    'Berth Code': b.code,
    'Name': b.name,
    'Type': b.berth_type,
    'Status': b.status,
    'Max LOA': b.max_loa,
  }));
  const berthsSheet = XLSX.utils.json_to_sheet(berthsData);
  XLSX.utils.book_append_sheet(workbook, berthsSheet, 'Berths');

  // Operations sheet
  const opsData = operations.map(op => ({
    'Date': op.scheduled_start,
    'Vessel': op.vessel_name,
    'Type': op.operation_type,
    'Containers': op.containers_completed,
    'Efficiency': `${op.efficiency_percentage}%`,
  }));
  const opsSheet = XLSX.utils.json_to_sheet(opsData);
  XLSX.utils.book_append_sheet(workbook, opsSheet, 'Operations');

  // KPIs sheet
  const kpisSheet = XLSX.utils.json_to_sheet([kpis]);
  XLSX.utils.book_append_sheet(workbook, kpisSheet, 'KPIs');

  // Download
  XLSX.writeFile(workbook, `smartport-data-${Date.now()}.xlsx`);
};
```

### 6. Alert & Notification Visualizations (MISSING)

#### A. Alert Timeline
```typescript
// frontend/src/components/smartport/AlertTimeline.tsx
import { Timeline } from 'antd';

export const AlertTimeline: React.FC = () => {
  const { alerts } = useSmartPort();

  return (
    <Timeline mode="left">
      {alerts.map((alert, i) => (
        <Timeline.Item
          key={i}
          color={alert.severity === 'high' ? 'red' : alert.severity === 'medium' ? 'yellow' : 'blue'}
          label={new Date(alert.timestamp).toLocaleTimeString()}
        >
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-4 w-4" />
            <div>
              <p className="font-medium">{alert.message}</p>
              <p className="text-xs text-gray-500">{alert.type}</p>
            </div>
          </div>
        </Timeline.Item>
      ))}
    </Timeline>
  );
};
```

## Implementation Priority

1. **Week 1 (Urgent):**
   - Time series charts (berth occupancy, throughput)
   - Vessel tracking map with Leaflet
   - Real-time operation monitoring

2. **Week 2 (Important):**
   - Analytics dashboard with trends
   - Heatmaps for utilization
   - PDF/Excel reporting

3. **Week 3 (Nice to have):**
   - Predictive analytics visualizations
   - Gantt chart for vessel timeline
   - Alert timeline

4. **Week 4 (Advanced):**
   - 3D port visualization
   - AR/VR support
   - Mobile app with visualizations

## Dependencies to Install

```bash
# Frontend
npm install recharts
npm install react-leaflet leaflet
npm install react-google-charts
npm install react-gauge-chart
npm install react-grid-heatmap
npm install jspdf html2canvas
npm install xlsx
npm install antd
```

## Performance Considerations

- Use **virtualization** for large lists (react-window)
- **Lazy load** charts on tab switch
- **Debounce** real-time updates (max 1 update/second)
- **Memoize** expensive calculations
- Use **Web Workers** for heavy computations
