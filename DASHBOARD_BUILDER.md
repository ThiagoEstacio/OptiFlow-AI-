# 🎨 SmartPort Dashboard Builder

**Drag-and-Drop Dashboard Creation** - PI Vision / Power BI style

Build custom dashboards by dragging tags onto visual components and watch live data flow in real-time!

---

## 🎯 Features

✅ **Drag-and-Drop Interface** - Intuitive like PI Vision/Power BI
✅ **Live Data Binding** - Drop a tag → Instant live data
✅ **Multiple Widget Types** - Gauges, time series, values, charts
✅ **Real-time Updates** - WebSocket streaming
✅ **Historical Data** - Query time series from InfluxDB
✅ **Save/Load Dashboards** - Persist your configurations
✅ **Resize & Reposition** - Fully customizable layout

---

## 🚀 Quick Start

### 1. Access Dashboard Builder

```
http://localhost:3000/dashboard-builder
```

Or click **🎨 Builder** in the sidebar.

### 2. Add a Widget

Click one of the widget buttons in the toolbar:
- 🎯 **Gauge** - Dial/speedometer style
- 🔢 **Value** - Large number display
- 📈 **Time Series** - Historical trend chart
- 📊 **Chart** - Bar/pie charts

### 3. Bind Data to Widget

**Method 1: Drag-and-Drop** (Recommended)
1. Find your tag in the left panel
2. Click and drag the tag
3. Drop it onto a widget
4. ✨ Watch live data appear!

**Method 2: Configuration** (Coming soon)
- Click widget to select
- Use properties panel to configure

### 4. Customize Widget

- **Move**: Drag the widget header
- **Resize**: Drag corners/edges
- **Rename**: Double-click title to edit
- **Delete**: Click ✕ button

### 5. Save Dashboard

Click **💾 Save** to persist your dashboard.
Click **📂 Load** to restore it later.

---

## 📊 Widget Types

### 1. Gauge (🎯)

**Best for**: Real-time KPIs, motor speed, temperature, pressure

**Features**:
- Auto-scaled to tag's min/max
- Color zones (green/yellow/red)
- Current value + unit display
- Threshold visualization

**Example Use Cases**:
- Motor current (0-300A)
- Temperature (20-120°C)
- Vibration (0-15 mm/s)
- Flow rate (0-3000 t/h)

---

### 2. Value Display (🔢)

**Best for**: Simple numeric displays, status indicators

**Features**:
- Large, readable font
- Unit display
- Timestamp
- Updates in real-time

**Example Use Cases**:
- Current production count
- Latest measurement
- OEE percentage
- Energy consumption

---

### 3. Time Series Chart (📈)

**Best for**: Historical trends, anomaly detection, pattern analysis

**Features**:
- Historical data from InfluxDB
- Zoom/pan capabilities
- Time range selector
- Multiple series

**Example Use Cases**:
- Temperature over 24 hours
- Vibration trends for predictive maintenance
- Production rate over time
- Energy consumption patterns

---

### 4. Chart (📊)

**Best for**: Aggregations, comparisons, distributions

**Features**:
- Bar charts
- Pie charts
- Scatter plots
- Histograms

**Example Use Cases**:
- Energy by equipment
- Production by shift
- Quality distribution

---

## 🏷️ Tags Panel

The left panel shows all available tags from your SmartPort system.

### Features

**Search**: Filter tags by name or description
**Category Filter**: Show only specific tag categories
**Drag Source**: Click and drag any tag to bind it

### Tag Categories

- **energy**: Motor current, power, voltage
- **process**: Flow, level, pressure, temperature
- **maintenance**: Vibration, bearing temp
- **production**: OEE, throughput, quality
- **quality**: Moisture, product temperature
- **status**: Equipment on/off
- **alarm**: Active alarms

---

## 🔴 Live Data

### How it Works

1. **WebSocket Connection**: Automatic connection to backend
2. **Subscribe to Tags**: When you bind a tag, auto-subscribe
3. **Real-time Updates**: Data updates every 1-2 seconds
4. **Fallback to Polling**: If WebSocket fails, uses HTTP polling

### Data Quality Indicators

- **green**: Good quality data
- **yellow**: Simulated/interpolated
- **red**: Connection lost
- **gray**: No data

---

## 📈 Example Dashboards

### Dashboard 1: Motor Health Monitoring

```
┌─────────────┬─────────────┬─────────────┐
│  CORRENTE   │  TEMPERATURA│   VIBRAÇÃO  │
│    125A     │     68°C    │   3.2mm/s   │
│   [Gauge]   │   [Gauge]   │   [Gauge]   │
└─────────────┴─────────────┴─────────────┘

┌───────────────────────────────────────────┐
│      Historical Trend (24 hours)          │
│  [Time Series: Current, Temp, Vibration]  │
│                                           │
└───────────────────────────────────────────┘
```

**Tags Used**:
- `CONV1_MOTOR_CURRENT`
- `CONV1_MOTOR_TEMP`
- `CONV1_VIBRATION`

---

### Dashboard 2: Production KPIs

```
┌─────────────┬─────────────┬─────────────┐
│  THROUGHPUT │   PROGRESS  │     OEE     │
│   2150 t/h  │    45.3%    │    87.5%    │
│   [Value]   │   [Gauge]   │   [Gauge]   │
└─────────────┴─────────────┴─────────────┘

┌───────────────────────────────────────────┐
│      Flow Rate Trend                      │
│  [Time Series: SHIP_FLOW_RATE]            │
│                                           │
└───────────────────────────────────────────┘
```

**Tags Used**:
- `SHIP_FLOW_RATE`
- `VESSEL_PROGRESS`
- `OEE_LINE_01`

---

### Dashboard 3: Predictive Maintenance

```
┌─────────────┬─────────────┬─────────────┐
│  ROLAMENTO  │  VIBRAÇÃO   │  CORRENTE   │
│    72°C     │   5.8mm/s   │    145A     │
│   [Gauge]   │   [Gauge]   │   [Gauge]   │
│   ⚠️ ALERTA │  ⚠️ ALERTA  │   Normal    │
└─────────────┴─────────────┴─────────────┘

┌───────────────────────────────────────────┐
│   Degradation Trend (7 days)              │
│  [Multi-axis: Temperature + Vibration]    │
│   → Trend shows increasing degradation    │
└───────────────────────────────────────────┘
```

**Tags Used**:
- `CONV1_BEARING_TEMP`
- `CONV1_VIBRATION`
- `CONV1_MOTOR_CURRENT`

---

## 🎨 Tips & Tricks

### 1. Organize by Category

Group related widgets together:
- Top row: Main KPIs
- Second row: Supporting metrics
- Bottom: Historical trends

### 2. Use Color Coding

Configure gauge thresholds to match your process:
- Green: Normal operation
- Yellow: Warning zone
- Red: Critical/alarm

### 3. Save Multiple Dashboards

Create specialized dashboards for different purposes:
- **Overview Dashboard**: High-level KPIs for management
- **Operations Dashboard**: Real-time monitoring for operators
- **Maintenance Dashboard**: Predictive signals for maintenance team
- **Quality Dashboard**: Product quality metrics

### 4. Naming Convention

Use clear, descriptive names:
- ❌ Bad: "Widget 1", "Chart"
- ✅ Good: "Shiploader Current", "24h Temperature Trend"

### 5. Refresh Rates

- **Critical tags**: Use WebSocket for 1-second updates
- **Slow-changing**: Polling every 5-10 seconds is fine
- **Historical**: Only query on dashboard load

---

## 🔧 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Delete` | Delete selected widget |
| `Ctrl+S` | Save dashboard |
| `Ctrl+Z` | Undo (coming soon) |
| `Esc` | Deselect widget |

---

## 🐛 Troubleshooting

### Tags not showing in panel

**Solution**: Make sure tags are configured in the system:
```bash
./setup_smartport.sh
```

### Widget shows "No data"

**Possible causes**:
1. Tag not bound yet → Drag a tag onto it
2. Simulator not running → Start `smartport_bulk_terminal_simulator.py`
3. Backend not running → Check `docker ps`

### Live data not updating

**Check**:
1. WebSocket connection (see browser console)
2. Backend is running
3. Gateway is collecting data
4. InfluxDB is accessible

### Dashboard not saving

**Solution**: Check browser localStorage is enabled. In production, this will use API.

---

## 📚 Technical Details

### Architecture

```
TAG (FIELD) → GATEWAY → BACKEND → INFLUXDB
                           ↓
                      WEBSOCKET
                           ↓
                   DASHBOARD BUILDER
                           ↓
                     WIDGET (GAUGE)
```

### Data Flow

1. **Simulator** generates tag values via Modbus TCP
2. **Gateway** reads via Modbus, sends to backend
3. **Backend** writes to InfluxDB
4. **WebSocket** streams to frontend
5. **Widget** displays live value

### WebSocket Protocol

```json
// Subscribe
{
  "query": {
    "tag_ids": ["uuid"],
    "range": "1m"
  },
  "refresh_interval": 1,
  "mode": "continuous"
}

// Response
{
  "type": "data",
  "data": {
    "data": [
      {"timestamp": "...", "value": 125.3, "quality": "good"}
    ]
  },
  "timestamp": "...",
  "sequence": 123
}
```

---

## 🚀 Roadmap

- [ ] Properties panel for widget configuration
- [ ] More widget types (radar, sankey, treemap)
- [ ] Dashboard templates
- [ ] Multi-page dashboards
- [ ] Sharing/collaboration
- [ ] Export to PDF/image
- [ ] Alarm overlays
- [ ] Annotations
- [ ] Calculated tags
- [ ] Custom thresholds per widget

---

## 📦 Dependencies

Required npm packages (already in package.json):
- `react-dnd` - Drag-and-drop
- `react-dnd-html5-backend` - HTML5 backend for DnD
- `react-draggable` - Widget positioning
- `react-resizable` - Widget resizing

To install:
```bash
cd frontend
npm install react-dnd react-dnd-html5-backend react-draggable react-resizable
```

---

## 💡 Need Help?

- **Documentation**: See `/docs/`
- **Examples**: Check `SMARTPORT_README.md`
- **Support**: Open an issue on GitHub

---

**Built with** ❤️ **by OptiFlow AI Team**

**Version**: 1.0.0
**Date**: 2025-01-29
