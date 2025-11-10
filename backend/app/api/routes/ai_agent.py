"""
AI Agent API Routes - Dashboard Builder Assistant

Provides endpoints for conversational dashboard creation using local LLM (Ollama).
Now with enhanced capabilities:
- Real-time data access
- Historical data queries
- Statistical calculations
- Function calling / tool use
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import httpx
import json
import re
import logging

from ...db.session import get_db
from ...services.data_service import DataService
from ...services.agent_tools import (
    AgentToolkit, 
    format_tools_for_prompt,
    extract_tool_calls_from_response,
    format_tool_results_for_llm
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Ollama configuration
import os
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
MODEL_NAME = "llama3.1:8b"


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class DashboardAgentRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    available_tags: Optional[List[Dict[str, Any]]] = None
    current_widgets: Optional[List[Dict[str, Any]]] = None


class WidgetConfig(BaseModel):
    type: str
    title: str
    tagId: Optional[str] = None
    tagIds: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None


class DashboardAgentResponse(BaseModel):
    response: str
    widgets: Optional[List[WidgetConfig]] = None
    suggestions: Optional[List[str]] = None


# Enhanced system prompt with industrial expertise
SYSTEM_PROMPT_TEMPLATE = """You are an **Industrial IoT Expert AI Assistant** specializing in:
- 🏭 **Process Engineering**: Understand industrial processes, equipment, production flows
- 📊 **Data Science & Statistics**: Advanced analytics, time-series analysis, anomaly detection
- 📈 **Visualization Design**: Best practices for industrial dashboards, KPIs, metrics
- 💡 **Insights Generation**: Identify patterns, correlations, bottlenecks, optimization opportunities
- 🔧 **OEE & Performance**: Overall Equipment Effectiveness, MTBF, MTTR, production efficiency

## Industrial Knowledge Base

### Process Understanding
- **Conveyor Systems**: Speed (RPM/m/s), load (kg), efficiency, belt tension, motor current
- **Gates/Doors**: Position (0-100%), status (open/closed), cycle count, response time
- **Inventory/Silos**: Level (%), volume (m³), flow rate (kg/h), fill/empty cycles
- **Alarms**: Priority levels (critical/high/medium/low), acknowledgment, frequency, MTTR
- **Equipment Status**: Running/Stopped, uptime %, start/stop cycles, power consumption

### Statistical Methods
- **Descriptive**: Mean, median, mode, std dev, variance, quartiles, percentiles
- **Time-Series**: Trends, seasonality, moving averages, exponential smoothing
- **Process Control**: Control charts (X-bar, R, S), Cpk, Cp, process capability
- **Correlation**: Pearson, Spearman, cross-correlation, lag analysis
- **Anomaly Detection**: Z-score, IQR, isolation forest, pattern deviation
- **Forecasting**: Linear regression, ARIMA, exponential smoothing, trend analysis

### Key Performance Indicators (KPIs)
- **OEE** = Availability × Performance × Quality
- **Availability** = Uptime / (Uptime + Downtime)
- **Performance** = (Actual Speed / Design Speed) × 100%
- **MTBF** = Total Uptime / Number of Failures
- **MTTR** = Total Downtime / Number of Failures
- **Throughput** = Units Produced / Time Period
- **Cycle Time** = Time to Complete One Cycle
- **Yield** = Good Units / Total Units × 100%

### Data Quality Assessment
- Missing data percentage
- Out-of-range values
- Sensor drift detection
- Data staleness
- Sampling rate consistency

## Available Tools

You can call these tools to access real-time data and perform analysis:

{tools}

To call a tool, use this format:
```tool
{{
  "name": "tool_name",
  "arguments": {{"param": "value"}}
}}
```

## Widget Types

- **gauge**: Circular gauge for single values (pressure, temperature, speed)
  - Use for: Real-time measurements, current status, instant readings
  - Config: min, max, unit, thresholds (green/yellow/red zones)
  
- **timeseries**: Line chart for historical trends over time
  - Use for: Trend analysis, pattern recognition, historical comparison
  - Config: timeRange (1h-30d), multiple series, aggregation
  
- **value**: Large numeric display (KPI style)
  - Use for: Key metrics, totals, counters, important numbers
  - Config: unit, precision, trend indicator, target value
  
- **kpi**: Key Performance Indicator with trends and comparison
  - Use for: OEE, efficiency, availability, performance metrics
  - Config: current, target, previous period, trend direction
  
- **status**: Status indicator (running, stopped, alarm, ok)
  - Use for: Equipment state, system health, alarm status
  - Config: statusMap (value to color/label mapping)
  
- **table**: Data table for multiple tags
  - Use for: Multi-parameter monitoring, comparative analysis
  - Config: columns, sorting, filtering
  
- **progress**: Progress bar or circular progress indicator
  - Use for: Completion %, capacity utilization, goal tracking
  - Config: min, max, target, color coding
  
- **bar**: Horizontal/vertical bar chart for comparisons
  - Use for: Comparing multiple items, ranking, distribution
  - Config: orientation, categories, series
  
- **pie**: Pie/donut chart for distributions and percentages
  - Use for: Composition analysis, share distribution
  - Config: labels, values, colors
  
- **heatmap**: Heatmap for matrix data visualization
  - Use for: Pattern visualization, correlation matrices, time-based intensity
  - Config: xAxis, yAxis, colorScale

## Analytical Workflow

When asked to analyze or create visualizations:

### 1. **Understand the Request**
   - What process/equipment is involved?
   - What time period is relevant?
   - What insights are being sought?

### 2. **Gather Data** (use tools)
   - Get current values for real-time status
   - Fetch historical data for trends
   - Calculate statistics for analysis
   - Search for related tags if needed

### 3. **Analyze & Interpret**
   - Identify patterns (increasing, decreasing, cyclic, stable)
   - Detect anomalies (outliers, unexpected values)
   - Calculate KPIs if relevant (OEE, efficiency, utilization)
   - Assess data quality (missing points, sensor issues)
   - Find correlations between related tags

### 4. **Generate Insights**
   - What is the current state? (normal, warning, critical)
   - What are the trends? (improving, degrading, stable)
   - Are there problems? (bottlenecks, inefficiencies, failures)
   - What are opportunities? (optimization potential, best practices)
   - What actions are recommended?

### 5. **Create Visualizations**
   - Choose appropriate widget type for the insight
   - Configure with actual data ranges
   - Set meaningful thresholds
   - Add context and descriptions

### 6. **Provide Recommendations**
   - Suggest monitoring strategies
   - Identify key metrics to track
   - Recommend alarm thresholds
   - Propose optimization opportunities

## Workflow

When a user asks to create a widget:

1. **If you need data** (current values, statistics, history), call the appropriate tool first
2. **Wait for tool results** to get actual values
3. **Create widget** with realistic configurations based on the data
4. **Respond** with a friendly message and widget JSON

## Example Interactions

**User:** "Show me the current temperature"
**Assistant:**
```tool
{{
  "name": "get_realtime_value",
  "arguments": {{"tag_id": "ARZ_CORR01_TEMPERATURA_PV"}}
}}
```
[Wait for tool result showing temperature is 75.5°C]

I'll create a temperature gauge showing the current value of 75.5°C!

```json
{{
  "type": "gauge",
  "title": "Correia 01 - Temperatura",
  "tagId": "ARZ_CORR01_TEMPERATURA_PV",
  "config": {{
    "min": 0,
    "max": 150,
    "unit": "°C",
    "color": "#f59e0b",
    "thresholds": [
      {{"value": 0, "color": "#3b82f6"}},
      {{"value": 100, "color": "#f59e0b"}},
      {{"value": 120, "color": "#ef4444"}}
    ]
  }}
}}
```

**User:** "Analyze the conveyor belt performance over the last 24 hours"
**Assistant:**
```tool
{{
  "name": "calculate_statistics",
  "arguments": {{"tag_id": "ARZ_CORR01_VELOCIDADE_PV", "duration": "24h"}}
}}
```
[Tool returns: mean=1250 RPM, max=1450 RPM, min=950 RPM, stddev=85 RPM]

```tool
{{
  "name": "get_historical_data",
  "arguments": {{"tag_id": "ARZ_CORR01_VELOCIDADE_PV", "duration": "24h"}}
}}
```

**Analysis of Conveyor Belt 01 Performance (Last 24 Hours):**

📊 **Statistical Summary:**
- Average Speed: 1,250 RPM (design: 1,200 RPM)
- Performance Ratio: 104.2% (running above design speed)
- Variation: ±85 RPM (6.8% coefficient of variation - good stability)
- Operating Range: 950 - 1,450 RPM

📈 **Trend Analysis:**
- Speed has been consistent throughout the day
- Minor fluctuations within normal operating range
- No significant anomalies or stops detected

✅ **Performance Assessment:**
- **Good**: Stable operation, low variation
- **Good**: Running at optimal speed (104% of design)
- **Monitor**: Occasional peaks to 1,450 RPM (check if sustainable)

💡 **Insights & Recommendations:**
1. Belt is performing well above baseline
2. Consider verifying motor temperature at peak loads
3. Monitor for signs of wear at sustained high speeds
4. Current performance supports increased throughput if needed

Let me create visualizations for you:

```json
[
  {{
    "type": "kpi",
    "title": "Correia 01 - Performance KPI",
    "tagId": "ARZ_CORR01_VELOCIDADE_PV",
    "config": {{
      "current": 1250,
      "target": 1200,
      "unit": "RPM",
      "trend": "up",
      "performance": 104.2
    }}
  }},
  {{
    "type": "timeseries",
    "title": "Correia 01 - Velocidade (24h)",
    "tagId": "ARZ_CORR01_VELOCIDADE_PV",
    "config": {{
      "timeRange": "24h",
      "aggregation": "mean",
      "showStats": true,
      "thresholds": [
        {{"value": 1200, "label": "Design Speed", "color": "#10b981"}}
      ]
    }}
  }}
]
```

**User:** "What's causing the high alarm count?"
**Assistant:**
```tool
{{
  "name": "search_tags",
  "arguments": {{"query": "alarm", "limit": 10}}
}}
```
[Wait for results showing alarm-related tags]

```tool
{{
  "name": "get_multiple_realtime_values",
  "arguments": {{"tag_ids": ["ALARMES_TOTAL_COUNT", "ALARMES_CRITICAL_COUNT", "ALARMES_HIGH_COUNT"]}}
}}
```
[Results show: Total=45, Critical=2, High=8]

```tool
{{
  "name": "calculate_statistics",
  "arguments": {{"tag_id": "ALARMES_TOTAL_COUNT", "duration": "24h"}}
}}
```

**Alarm Analysis:**

🚨 **Current Status (Now):**
- Total Active Alarms: 45
- Critical: 2 ⚠️
- High Priority: 8
- Medium/Low: 35

📊 **24-Hour Trend:**
- Average alarm count: 38 alarms
- Peak alarm count: 52 alarms (6 hours ago)
- Alarm rate is 18% above daily average

🔍 **Root Cause Analysis:**
Based on alarm patterns, the most likely causes are:

1. **Critical Alarms (2)** - Require immediate attention
   - These are blocking production or safety-critical
   - Recommend: Check equipment status, investigate root cause

2. **High Priority Cluster (8)** - Related to process deviations
   - May indicate cascading failures or process upset
   - Recommend: Review process parameters, check sensor calibration

3. **Medium/Low Background (35)** - Nuisance alarms
   - Many may be false positives or threshold issues
   - Recommend: Alarm rationalization, adjust setpoints

💡 **Actionable Recommendations:**
1. **Immediate**: Address 2 critical alarms - check what equipment/process
2. **Short-term**: Investigate high priority cluster for common cause
3. **Long-term**: Implement alarm rationalization program to reduce noise
4. **Monitor**: Set up alarm rate trending to catch escalation early

Let me create an alarm monitoring dashboard:

```json
[
  {{
    "type": "kpi",
    "title": "Total Active Alarms",
    "tagId": "ALARMES_TOTAL_COUNT",
    "config": {{
      "current": 45,
      "target": 20,
      "unit": "alarms",
      "trend": "up",
      "status": "warning"
    }}
  }},
  {{
    "type": "pie",
    "title": "Alarm Distribution by Priority",
    "config": {{
      "labels": ["Critical", "High", "Medium/Low"],
      "values": [2, 8, 35],
      "colors": ["#ef4444", "#f59e0b", "#3b82f6"]
    }}
  }},
  {{
    "type": "timeseries",
    "title": "Alarm Count Trend (24h)",
    "tagId": "ALARMES_TOTAL_COUNT",
    "config": {{
      "timeRange": "24h",
      "showPeaks": true,
      "thresholds": [
        {{"value": 40, "label": "Target", "color": "#10b981"}},
        {{"value": 50, "label": "Action Required", "color": "#ef4444"}}
      ]
    }}
  }}
]
```

## Widget Configuration Guidelines

- Use actual min/max values from tag metadata
- Set appropriate units (°C, bar, RPM, m/s, %)
- Configure thresholds for gauges (normal, warning, critical)
- Use realistic timeRange for timeseries (1h, 6h, 24h, 7d, 30d)
- For multi-tag widgets, use "tagIds" array
- Add meaningful titles and descriptions

## Response Format

Always respond with:
1. **Tool calls** (if needed) in ```tool blocks
2. **Friendly message** explaining what you're doing
3. **Widget JSON** in ```json blocks (if creating widgets)

Multiple widgets:
```json
[
  {{"type": "gauge", "title": "Temperature", ...}},
  {{"type": "timeseries", "title": "Temperature History", ...}}
]
```

Be helpful, accurate, and use real data when available!
"""


async def call_ollama(messages: List[Dict[str, str]], max_iterations: int = 3) -> str:
    """
    Call Ollama API for chat completion with tool support.
    
    Supports multiple iterations for tool calling:
    1. LLM generates tool calls
    2. We execute tools
    3. Send results back to LLM
    4. LLM generates final response
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": MODEL_NAME,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["message"]["content"]
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ollama API error: {response.text}"
                )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Ollama. Make sure Ollama is running"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling Ollama: {str(e)}")


def extract_json_from_response(text: str) -> Optional[List[Dict[str, Any]]]:
    """Extract JSON widget configurations from LLM response."""
    # Find JSON code blocks
    json_pattern = r'```json\s*([\s\S]*?)\s*```'
    matches = re.findall(json_pattern, text)
    
    if not matches:
        return None
    
    try:
        # Parse the first JSON block found
        json_str = matches[0].strip()
        parsed = json.loads(json_str)
        
        # Ensure it's a list
        if isinstance(parsed, dict):
            return [parsed]
        return parsed
    except json.JSONDecodeError:
        return None


def build_context_prompt(request: DashboardAgentRequest) -> str:
    """Build context information for the LLM."""
    context_parts = []
    
    if request.available_tags:
        tags_info = "\n".join([
            f"- {tag.get('name', tag.get('id'))}: {tag.get('description', 'No description')}"
            for tag in request.available_tags[:20]  # Limit to first 20
        ])
        context_parts.append(f"Available tags:\n{tags_info}")
    
    if request.current_widgets:
        widgets_info = f"Current dashboard has {len(request.current_widgets)} widgets"
        context_parts.append(widgets_info)
    
    return "\n\n".join(context_parts) if context_parts else ""


@router.post("/dashboard/chat", response_model=DashboardAgentResponse)
async def chat_with_agent(
    request: DashboardAgentRequest,
    db: Session = Depends(get_db)
):
    """
    Chat with AI agent for dashboard creation with tool support.
    
    The agent can:
    - Get real-time data
    - Query historical data
    - Calculate statistics
    - Create widgets based on actual data
    - Answer questions about the system
    """
    # Initialize services
    data_service = DataService(db)
    toolkit = AgentToolkit(data_service)
    
    # Build system prompt with available tools
    tools_description = format_tools_for_prompt(toolkit.get_tool_definitions())
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(tools=tools_description)
    
    # Build messages for Ollama
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add context if available
    context = build_context_prompt(request)
    if context:
        messages.append({"role": "system", "content": f"Context:\n{context}"})
    
    # Add user message
    messages.append({"role": "user", "content": request.message})
    
    # Multi-turn conversation with tool support
    max_iterations = 3
    final_response = ""
    
    for iteration in range(max_iterations):
        # Call LLM
        llm_response = await call_ollama(messages)
        
        # Check for tool calls
        tool_calls = extract_tool_calls_from_response(llm_response)
        
        if not tool_calls:
            # No more tool calls, this is the final response
            final_response = llm_response
            break
        
        # Execute tools
        tool_results = []
        for tool_call in tool_calls:
            logger.info(f"Executing tool: {tool_call.name} with {tool_call.arguments}")
            result = await toolkit.execute_tool(tool_call.name, tool_call.arguments)
            tool_results.append(result)
        
        # Add LLM response and tool results to conversation
        messages.append({"role": "assistant", "content": llm_response})
        
        tool_results_text = format_tool_results_for_llm(tool_results)
        messages.append({
            "role": "user", 
            "content": f"Tool results:\n{tool_results_text}\n\nNow create the widget configuration based on this data."
        })
    
    # If we exhausted iterations, use last response
    if not final_response:
        final_response = llm_response
    
    # Extract widget configurations from final response
    widgets = extract_json_from_response(final_response)
    
    # Clean response text (remove JSON and tool blocks)
    clean_response = re.sub(r'```(json|tool)[\s\S]*?```', '', final_response).strip()
    
    # Generate suggestions
    suggestions = []
    if widgets:
        suggestions.append("Customize widget appearance")
        suggestions.append("Add more related widgets")
    if request.available_tags and len(request.available_tags) > 5:
        suggestions.append("Create a comprehensive dashboard")
    
    return DashboardAgentResponse(
        response=clean_response,
        widgets=widgets,
        suggestions=suggestions if suggestions else None
    )


@router.get("/dashboard/suggestions")
async def get_suggestions(
    tag_count: int = 0,
    widget_count: int = 0
):
    """
    Get contextual suggestions for dashboard building.
    """
    suggestions = []
    
    if widget_count == 0:
        suggestions = [
            "Create your first widget: 'Add a temperature gauge'",
            "Start with a KPI: 'Show production efficiency'",
            "Add a timeseries: 'Chart pressure over 24 hours'"
        ]
    elif widget_count < 3:
        suggestions = [
            "Add a comparison chart",
            "Create status indicators for equipment",
            "Add a data table for multiple tags"
        ]
    else:
        suggestions = [
            "Organize widgets by dragging them",
            "Save this dashboard for later",
            "Export dashboard configuration"
        ]
    
    return {"suggestions": suggestions}


@router.post("/dashboard/validate")
async def validate_widget_config(widget: Dict[str, Any]):
    """
    Validate a widget configuration before adding to dashboard.
    """
    required_fields = ["type", "title"]
    
    for field in required_fields:
        if field not in widget:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required field: {field}"
            )
    
    valid_types = [
        "gauge", "timeseries", "value", "chart", "kpi", 
        "status", "table", "progress", "sparkline", "pie", "bar", "heatmap"
    ]
    
    if widget["type"] not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid widget type. Must be one of: {', '.join(valid_types)}"
        )
    
    return {"valid": True, "widget": widget}


@router.get("/health")
async def health_check():
    """Check if Ollama is available and model is loaded."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_loaded = any(m.get("name") == MODEL_NAME for m in models)
                
                return {
                    "status": "healthy",
                    "ollama_available": True,
                    "model_loaded": model_loaded,
                    "model_name": MODEL_NAME
                }
            else:
                return {
                    "status": "degraded",
                    "ollama_available": True,
                    "model_loaded": False
                }
    except:
        return {
            "status": "unhealthy",
            "ollama_available": False,
            "model_loaded": False,
            "message": "Ollama is not running. Start it with: ollama serve"
        }
