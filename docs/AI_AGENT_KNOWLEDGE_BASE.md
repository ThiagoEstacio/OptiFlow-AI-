# AI Agent Knowledge Base
## Industrial IoT Expert Assistant - Complete Training Manual

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Process Knowledge](#process-knowledge)
3. [Statistical Analysis](#statistical-analysis)
4. [Data Visualization](#data-visualization)
5. [Insights Generation](#insights-generation)
6. [Industrial KPIs](#industrial-kpis)
7. [Best Practices](#best-practices)

---

## 1. System Overview

### OptiFlow-AI Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OptiFlow-AI Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend (React + TypeScript)                               │
│  ├── Dashboard Builder (AI-Assisted)                         │
│  ├── Real-time Monitoring                                    │
│  ├── Historical Analysis                                     │
│  └── Alarm Management                                        │
│                                                               │
│  Backend (FastAPI + Python)                                  │
│  ├── REST API (v1)                                           │
│  ├── AI Agent (Ollama + LLaMA 3.1)                          │
│  ├── Data Services                                           │
│  └── Agent Toolkit (10+ tools)                              │
│                                                               │
│  Data Layer                                                  │
│  ├── PostgreSQL (Relational data, tags, metadata)           │
│  ├── InfluxDB (Time-series data, 242k points/hour)          │
│  └── Tag Labels (User-friendly names)                       │
│                                                               │
│  Gateway                                                     │
│  ├── Modbus TCP/RTU                                          │
│  ├── SmartPort Protocol                                     │
│  └── Real-time Data Collection                              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### System Capabilities

- **Real-time Monitoring**: 736 tags, ~73 points/second
- **Historical Storage**: InfluxDB with 27.7MB storage (efficient!)
- **AI Assistant**: LLaMA 3.1 (8B) for intelligent analysis
- **Tag Labels**: User-friendly names (e.g., "Posição do Portão 1" instead of "ARZ_GATES_GATE01_POSICAO_PV")
- **Tool Support**: 10 advanced tools for data analysis

---

## 2. Process Knowledge

### 2.1 Industrial Equipment Types

#### Conveyor Belts (Correias Transportadoras)

**Purpose**: Material transport in warehouses and production lines

**Key Parameters**:
- **Velocidade (Speed)**: RPM or m/s
  - Typical range: 800-1500 RPM
  - Design speed: ~1200 RPM
  - Alarm if > 1500 RPM or < 500 RPM
  
- **Temperatura (Temperature)**: °C
  - Normal: 40-80°C
  - Warning: 80-100°C
  - Critical: > 100°C (motor overheating)
  
- **Corrente do Motor (Motor Current)**: A
  - Indicates load and efficiency
  - High current = overload or mechanical issue
  - Low current = empty belt or slippage

**Common Issues**:
- Belt slippage (speed drops, current increases)
- Overload (current high, speed low)
- Motor overheating (temperature high)
- Bearing failure (vibration increase, temperature rise)

**Monitoring Strategy**:
- Continuous speed monitoring
- Temperature trending
- Current vs. speed correlation
- Anomaly detection for sudden changes

#### Gates/Doors (Portões)

**Purpose**: Access control, material flow, security

**Key Parameters**:
- **Posição (Position)**: 0-100%
  - 0% = Fully closed
  - 100% = Fully open
  - Intermediate = Moving or partially open
  
- **Estado (Status)**: Open, Closed, Moving, Alarm
  
- **Ciclos (Cycle Count)**: Number of open/close cycles
  - Track for maintenance scheduling
  - High cycles = wear, need inspection

**Common Issues**:
- Stuck position (not fully open/closed)
- Slow response time (mechanical issue)
- Frequent cycling (control logic problem)
- Position sensor drift

**Monitoring Strategy**:
- Position vs. command verification
- Cycle time tracking
- Anomaly detection on cycle count
- Alarm on position mismatch

#### Inventory/Silos (Inventário)

**Purpose**: Material storage and level monitoring

**Key Parameters**:
- **Nível (Level)**: Percentage or absolute (m³, kg)
  - 0-20%: Low level, reorder needed
  - 20-80%: Normal operating range
  - 80-100%: High level, stop filling
  
- **Taxa de Enchimento/Esvaziamento (Fill/Drain Rate)**: kg/h, m³/h
  - Indicates throughput
  - Helps predict empty/full time

**Common Issues**:
- Level sensor malfunction (stuck reading)
- Overfill/overflow risk
- Material bridging or ratholing
- Slow filling (supply issue)

**Monitoring Strategy**:
- Level trending over time
- Fill/drain rate calculation
- Predicted time to empty/full
- Min/max level alarms

#### Alarms (Alarmes)

**Purpose**: Alert operators to abnormal conditions

**Categories**:
1. **Critical** (Crítico): Safety or production stop
   - Immediate action required
   - SMS/call notification
   - Example: Equipment failure, safety interlock
   
2. **High** (Alto): Significant issue
   - Action within 15-30 minutes
   - Process deviation
   - Example: Temperature high, pressure out of range
   
3. **Medium** (Médio): Warning condition
   - Action within 1-2 hours
   - Preventive maintenance needed
   - Example: High vibration, low efficiency
   
4. **Low** (Baixo): Informational
   - Monitoring only
   - Example: Set point change, mode change

**Alarm Management Best Practices**:
- **Target alarm rate**: < 1 alarm per 10 minutes per operator
- **Alarm flood**: > 10 alarms/10 minutes = problem
- **Chattering alarm**: Same alarm on/off repeatedly
- **Standing alarm**: Alarm permanently active (should be fixed or threshold adjusted)
- **Stale alarm**: Alarm not acknowledged for long time

**Analysis Techniques**:
- Pareto analysis (80/20 rule - 20% of tags cause 80% of alarms)
- Time-of-day patterns (shift changes, production cycles)
- Alarm correlation (which alarms occur together)
- Alarm consequence analysis (which alarms indicate real problems)

---

## 3. Statistical Analysis

### 3.1 Descriptive Statistics

#### Central Tendency
- **Mean (Média)**: Average value
  - Use for: Overall performance, typical operation
  - Sensitive to outliers
  
- **Median**: Middle value (50th percentile)
  - Use for: Robust average when outliers present
  - Better for skewed distributions
  
- **Mode**: Most frequent value
  - Use for: Discrete data, status values

#### Variability
- **Standard Deviation (Desvio Padrão)**: Spread of data
  - Low σ = Stable process
  - High σ = Variable process
  - Use for: Process stability assessment
  
- **Coefficient of Variation (CV)**: σ / mean × 100%
  - < 5%: Very stable
  - 5-15%: Moderate variability
  - > 15%: High variability
  - Use for: Comparing variability across different scales

- **Range**: Max - Min
  - Quick variability indicator
  - Sensitive to outliers

#### Distribution
- **Quartiles**: Q1 (25%), Q2 (50%), Q3 (75%)
- **Interquartile Range (IQR)**: Q3 - Q1
  - Use for: Outlier detection (values outside Q1-1.5×IQR to Q3+1.5×IQR)

### 3.2 Time-Series Analysis

#### Trend Analysis
- **Linear Trend**: Steady increase/decrease
  - y = mx + b
  - Use for: Drift detection, degradation

- **Moving Average**: Smooth short-term fluctuations
  - Simple: Average of last N points
  - Exponential: Weighted average (recent data weighted more)
  - Use for: Noise reduction, trend identification

#### Seasonality
- **Daily cycles**: Production shifts, temperature changes
- **Weekly cycles**: Weekend shutdowns, batch processes
- **Monthly cycles**: Planned maintenance, seasonal demand

#### Autocorrelation
- Correlation of signal with itself at different time lags
- Use for: Detect cycles, repetitive patterns

### 3.3 Process Control Statistics

#### Control Charts
- **X-bar chart**: Monitor process mean
  - Center line: Mean
  - Control limits: Mean ± 3σ
  - Out of control: Point outside limits or 7+ points on one side

- **R chart**: Monitor process variation
  - Track range between samples

#### Process Capability
- **Cp**: (USL - LSL) / (6σ)
  - Cp > 1.33: Capable process
  - Cp = 1.0: Just capable
  - Cp < 1.0: Incapable
  
- **Cpk**: Min[(USL - μ)/(3σ), (μ - LSL)/(3σ)]
  - Accounts for process centering
  - Cpk > 1.33: Good
  - Cpk < 1.0: Poor

### 3.4 Correlation Analysis

#### Pearson Correlation
- Measures linear relationship
- Range: -1 to +1
  - +1: Perfect positive correlation
  - 0: No correlation
  - -1: Perfect negative correlation

**Interpretation**:
- |r| > 0.8: Strong correlation
- |r| = 0.5-0.8: Moderate correlation
- |r| < 0.5: Weak correlation

**Use Cases**:
- Motor current vs. conveyor speed
- Temperature vs. ambient temperature
- Production rate vs. energy consumption

#### Cross-Correlation
- Correlation with time lag
- Use for: Identify cause-effect relationships with time delay

### 3.5 Anomaly Detection

#### Z-Score Method
- Z = (x - μ) / σ
- Outlier if |Z| > 2 (95% confidence) or > 3 (99.7% confidence)

#### IQR Method
- Outlier if x < Q1 - 1.5×IQR or x > Q3 + 1.5×IQR
- More robust to non-normal distributions

#### Time-Series Anomalies
- Point anomalies: Single unusual value
- Contextual anomalies: Unusual in context (e.g., high value at night)
- Collective anomalies: Sequence of unusual values

---

## 4. Data Visualization

### 4.1 Widget Selection Guide

| Data Type | Question | Widget Type | Use Case |
|-----------|----------|-------------|----------|
| Single value | What is it now? | **Gauge** | Current temperature, pressure |
| Single value | How much? | **Value** | KPI, total count, current status |
| Time-series | How does it change? | **Timeseries** | Trends, history, patterns |
| Comparison | Which is higher? | **Bar Chart** | Compare equipment, shifts |
| Composition | What are the parts? | **Pie Chart** | Alarm distribution, categories |
| Distribution | What's the spread? | **Histogram** | Value distribution, quality |
| Relationship | Are they related? | **Scatter Plot** | Correlation analysis |
| Performance | Are we meeting goals? | **KPI** | OEE, efficiency, targets |
| Status | Is it OK? | **Status** | Equipment state, health |
| Multi-variable | Show many values | **Table** | Tag list, alarm list |
| Progress | How far along? | **Progress Bar** | Completion %, capacity |
| Intensity | Where is it hot? | **Heatmap** | Geographic, time-based |

### 4.2 Color Psychology

#### Status Colors
- **🟢 Green (#10b981)**: Normal, OK, running, good
- **🟡 Yellow (#f59e0b)**: Warning, caution, moderate
- **🔴 Red (#ef4444)**: Critical, alarm, stopped, bad
- **🔵 Blue (#3b82f6)**: Information, cold, low
- **⚫ Gray (#6b7280)**: Inactive, disabled, unknown

#### Performance Colors
- **Green**: > 90% (excellent)
- **Yellow**: 70-90% (acceptable)
- **Red**: < 70% (poor)

### 4.3 Dashboard Design Principles

#### Layout
- **F-Pattern**: Most important info top-left
- **Z-Pattern**: Guide eye with diagonal flow
- **Grid**: Align widgets for clean look

#### Hierarchy
1. **Critical alarms** (top, red)
2. **Key KPIs** (prominent, large)
3. **Real-time values** (gauges, values)
4. **Trends** (timeseries, charts)
5. **Details** (tables, supplementary info)

#### Density
- **Executive dashboard**: 4-6 widgets (high-level)
- **Operator dashboard**: 8-12 widgets (actionable)
- **Engineer dashboard**: 12-20 widgets (detailed)

### 4.4 Threshold Configuration

#### Temperature
```javascript
thresholds: [
  {value: 0, color: "#3b82f6"},    // Cold: Blue
  {value: 60, color: "#10b981"},   // Normal: Green
  {value: 80, color: "#f59e0b"},   // Warm: Yellow
  {value: 100, color: "#ef4444"}   // Hot: Red
]
```

#### Speed/Performance
```javascript
thresholds: [
  {value: 0, color: "#ef4444"},    // Stopped: Red
  {value: 50, color: "#f59e0b"},   // Low: Yellow
  {value: 80, color: "#10b981"},   // Normal: Green
  {value: 120, color: "#ef4444"}   // Overspeed: Red
]
```

#### Level
```javascript
thresholds: [
  {value: 0, color: "#ef4444"},    // Empty: Red
  {value: 20, color: "#f59e0b"},   // Low: Yellow
  {value: 80, color: "#10b981"},   // Normal: Green
  {value: 95, color: "#ef4444"}    // Overflow risk: Red
]
```

---

## 5. Insights Generation

### 5.1 Insight Categories

#### 1. **Performance Insights**
- Is equipment running at design capacity?
- Are we meeting production targets?
- What's the efficiency trend?

**Example**:
> "Conveyor 01 is running at 104% of design speed (1250 RPM vs 1200 RPM design). Performance is good, but monitor motor temperature and bearing wear at sustained high speeds."

#### 2. **Anomaly Insights**
- Are there unusual patterns?
- Did something unexpected happen?
- Are values out of normal range?

**Example**:
> "Temperature sensor showed 3 anomalies in the last 24 hours (values > 2.5 standard deviations from mean). Investigate sensor calibration or actual process upsets."

#### 3. **Correlation Insights**
- Do parameters move together?
- What causes what?
- Are there hidden relationships?

**Example**:
> "Strong correlation (r=0.87) between motor current and conveyor speed. When speed drops 10%, current increases 15%, suggesting increased mechanical resistance or load."

#### 4. **Predictive Insights**
- What will happen next?
- When will it reach limit?
- How long until maintenance?

**Example**:
> "At current fill rate (450 kg/h), silo will reach capacity in 8.5 hours. Plan production accordingly to avoid overflow."

#### 5. **Optimization Insights**
- Can we do better?
- Where are bottlenecks?
- What's the improvement potential?

**Example**:
> "OEE is 72% (target: 85%). Main loss is Availability (78% vs 95% target). Reducing downtime by 1 hour/day would improve OEE to 78%."

### 5.2 Root Cause Analysis Framework

```
1. Define the Problem
   ├── What happened?
   ├── When did it happen?
   ├── Where did it happen?
   └── What's the impact?

2. Gather Data
   ├── Get real-time values
   ├── Fetch historical data
   ├── Calculate statistics
   └── Search for related tags

3. Identify Patterns
   ├── Trends (increasing, decreasing, stable)
   ├── Anomalies (outliers, spikes)
   ├── Correlations (related parameters)
   └── Timing (shift, day, time of day)

4. Generate Hypotheses
   ├── What could cause this?
   ├── Have we seen this before?
   ├── What changed recently?
   └── What are similar cases?

5. Test Hypotheses
   ├── Check correlated parameters
   ├── Compare to baseline
   ├── Look for confirmatory evidence
   └── Rule out alternatives

6. Recommend Actions
   ├── Immediate actions (stop, adjust, alert)
   ├── Short-term fixes (workarounds)
   ├── Long-term solutions (prevent recurrence)
   └── Monitoring (track effectiveness)
```

### 5.3 Insight Quality Checklist

✅ **Specific**: Use actual numbers and units
✅ **Contextual**: Compare to baseline, target, or design
✅ **Actionable**: Suggest what to do
✅ **Timely**: Consider urgency and priority
✅ **Evidence-based**: Use real data, not assumptions

❌ **Avoid**:
- Vague statements ("seems high", "looks unusual")
- Opinions without data
- Recommendations without justification
- Ignoring context and history

---

## 6. Industrial KPIs

### 6.1 Overall Equipment Effectiveness (OEE)

**Formula**: OEE = Availability × Performance × Quality

#### Availability
```
Availability = (Operating Time / Planned Production Time) × 100%

Where:
- Operating Time = Planned Production Time - Downtime
- Downtime = Planned stops + Unplanned stops

Target: > 90% (World Class: > 95%)
```

**Example**:
- Planned: 24 hours (1440 min)
- Downtime: 3 hours (180 min)
- Operating: 21 hours (1260 min)
- **Availability = 1260/1440 × 100% = 87.5%**

#### Performance
```
Performance = (Actual Output / Theoretical Maximum Output) × 100%

Where:
- Actual Output = Units produced
- Theoretical Maximum = Design speed × Operating time

Target: > 95% (World Class: > 98%)
```

**Example**:
- Design speed: 100 units/hour
- Operating time: 21 hours
- Theoretical: 2100 units
- Actual: 1890 units
- **Performance = 1890/2100 × 100% = 90%**

#### Quality
```
Quality = (Good Units / Total Units Produced) × 100%

Where:
- Good Units = Total - Defects - Rework

Target: > 99% (World Class: > 99.5%)
```

**Example**:
- Total produced: 1890 units
- Defects: 38 units
- Good: 1852 units
- **Quality = 1852/1890 × 100% = 98%**

#### OEE Calculation
```
OEE = 87.5% × 90% × 98% = 77.2%
```

**Classification**:
- < 40%: Unacceptable - Systematic losses
- 40-60%: Fair - Moderate losses
- 60-85%: Good - Minor losses
- > 85%: World Class - Optimized

### 6.2 Other Key Metrics

#### Mean Time Between Failures (MTBF)
```
MTBF = Total Operating Time / Number of Failures

Target: > 2000 hours (depends on equipment)
```

**Use**: Reliability indicator, maintenance planning

#### Mean Time To Repair (MTTR)
```
MTTR = Total Downtime / Number of Repairs

Target: < 2 hours (depends on equipment)
```

**Use**: Maintenance efficiency, spare parts strategy

#### Throughput
```
Throughput = Units Produced / Time Period

Units: tons/hour, m³/hour, units/shift
```

**Use**: Production planning, capacity analysis

#### Cycle Time
```
Cycle Time = Time to Complete One Unit/Cycle

Target: ≤ Design cycle time
```

**Use**: Bottleneck identification, process optimization

#### Yield
```
Yield = (Good Units / Total Input) × 100%

First Pass Yield = Good units on first attempt

Target: > 95%
```

**Use**: Quality management, waste reduction

---

## 7. Best Practices

### 7.1 Data Quality

#### Check Data Validity
```python
# Example validation
if value > max_range or value < min_range:
    flag = "Out of range - possible sensor error"
if stddev == 0:
    flag = "Stuck sensor - constant reading"
if missing_data_pct > 10:
    flag = "High data loss - connectivity issue"
```

#### Handle Missing Data
- Small gaps (< 5 minutes): Interpolate
- Medium gaps (5-30 minutes): Mark as missing
- Large gaps (> 30 minutes): Investigate root cause

### 7.2 Analysis Workflow

```
1. Understand the Question
   └── What does the user really want to know?

2. Identify Required Data
   └── Which tags? What time period?

3. Fetch Data
   └── Use appropriate tools (realtime, historical, stats)

4. Validate Data
   └── Check for quality issues

5. Analyze
   └── Calculate metrics, identify patterns

6. Generate Insights
   └── What does it mean? Why does it matter?

7. Recommend Actions
   └── What should be done?

8. Create Visualizations
   └── Show it clearly and actionably
```

### 7.3 Communication Guidelines

#### Structure Responses
```
1. Summary (1-2 sentences)
   └── What's the answer?

2. Details (bullet points)
   └── Key findings with numbers

3. Insights (why it matters)
   └── Interpretation and context

4. Recommendations (what to do)
   └── Actionable next steps

5. Visualizations
   └── Widget configurations
```

#### Use Numbers Effectively
- ✅ "1,250 RPM (104% of 1,200 RPM design)"
- ❌ "Pretty fast"

- ✅ "3 anomalies detected (2.5σ threshold)"
- ❌ "Some unusual values"

- ✅ "OEE improved from 72% to 78% (+6 points)"
- ❌ "OEE got better"

### 7.4 Tool Usage Strategy

| Scenario | Tools to Use |
|----------|-------------|
| "What is X now?" | `get_realtime_value` |
| "Show me multiple sensors" | `get_multiple_realtime_values` |
| "What happened over time?" | `get_historical_data` |
| "What's the average?" | `calculate_statistics` |
| "Find temperature tags" | `search_tags` |
| "Are X and Y related?" | `compare_tags` |
| "Find problems" | `detect_anomalies` |
| "Calculate OEE" | `calculate_oee` |
| "Why so many alarms?" | `analyze_alarm_patterns` |
| "What's the range?" | `get_tag_metadata` |

### 7.5 Error Handling

#### Common Issues
- **Tag not found**: Search for similar tags, suggest alternatives
- **No data available**: Check time range, sensor status
- **Data quality issues**: Flag and explain to user
- **Calculation errors**: Use fallback methods, explain limitations

#### Graceful Degradation
```
If calculate_oee fails:
  ├── Calculate individual components (availability, performance, quality)
  ├── Explain what's missing
  └── Provide partial results with caveats
```

---

## 8. Quick Reference

### Common Tag Patterns

| Tag Pattern | Meaning | Typical Range |
|-------------|---------|---------------|
| `*_VELOCIDADE_PV` | Speed | 0-2000 RPM |
| `*_TEMPERATURA_PV` | Temperature | 0-150°C |
| `*_CORRENTE_PV` | Current | 0-100 A |
| `*_POSICAO_PV` | Position | 0-100% |
| `*_NIVEL_PV` | Level | 0-100% |
| `*_PRESSAO_PV` | Pressure | 0-10 bar |
| `ALARMES_*_COUNT` | Alarm count | 0-999 |
| `SYSTEM_RUNNING_PV` | System status | 0/1 |

### Widget Quick Config

```javascript
// Gauge
{
  type: "gauge",
  title: "Temperature",
  tagId: "temp_01",
  config: {
    min: 0, max: 150, unit: "°C",
    thresholds: [{value: 0, color: "blue"}, {value: 100, color: "yellow"}, {value: 120, color: "red"}]
  }
}

// KPI
{
  type: "kpi",
  title: "OEE",
  config: {
    current: 77.2, target: 85, unit: "%",
    trend: "up", status: "warning"
  }
}

// Timeseries
{
  type: "timeseries",
  title: "Speed Trend",
  tagId: "speed_01",
  config: {
    timeRange: "24h",
    aggregation: "mean",
    showStats: true
  }
}
```

---

## 9. Training Exercises

### Exercise 1: Basic Analysis
**User asks**: "Show me the current temperature"

**Your workflow**:
1. Call `get_realtime_value("ARZ_CORR01_TEMPERATURA_PV")`
2. Get result: 75.5°C
3. Call `get_tag_metadata` to get range
4. Create gauge widget with appropriate thresholds
5. Respond with friendly message

### Exercise 2: Performance Analysis
**User asks**: "How is the conveyor performing today?"

**Your workflow**:
1. Call `calculate_statistics("ARZ_CORR01_VELOCIDADE_PV", "24h")`
2. Call `get_historical_data` for trend
3. Compare to design speed
4. Calculate performance ratio
5. Detect any anomalies
6. Generate insights and recommendations
7. Create KPI + timeseries widgets

### Exercise 3: Root Cause Analysis
**User asks**: "Why are there so many alarms?"

**Your workflow**:
1. Call `search_tags("alarm")` to find alarm tags
2. Call `get_multiple_realtime_values` for current counts
3. Call `analyze_alarm_patterns` with alarm tags
4. Identify critical vs. nuisance alarms
5. Look for correlations (are process parameters abnormal?)
6. Generate insights on root causes
7. Recommend immediate and long-term actions
8. Create alarm dashboard (pie chart + trend + table)

---

## 10. Success Metrics

Your performance will be evaluated on:

✅ **Accuracy**: Correct calculations and interpretations
✅ **Insight Quality**: Meaningful, actionable insights
✅ **Response Time**: Use tools efficiently
✅ **Clarity**: Clear, well-structured communication
✅ **Visualization**: Appropriate widget selection
✅ **Context**: Consider process knowledge and best practices

---

## Appendix: Glossary

- **PV**: Process Variable (actual measured value)
- **SP**: Set Point (desired value)
- **CV**: Controlled Variable
- **MV**: Manipulated Variable
- **OEE**: Overall Equipment Effectiveness
- **MTBF**: Mean Time Between Failures
- **MTTR**: Mean Time To Repair
- **KPI**: Key Performance Indicator
- **SPC**: Statistical Process Control
- **Cpk**: Process Capability Index
- **RTU**: Remote Terminal Unit
- **HMI**: Human-Machine Interface
- **SCADA**: Supervisory Control and Data Acquisition

---

**Last Updated**: November 2025
**Version**: 1.0
**Maintained By**: OptiFlow-AI Team
