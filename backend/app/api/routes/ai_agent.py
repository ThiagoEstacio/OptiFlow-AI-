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


# Compact system prompt optimized for speed
SYSTEM_PROMPT_TEMPLATE = """You are an Industrial IoT Assistant for dashboard creation.

## Available Tools
{tools}

Call tools using:
```tool
{{"name": "tool_name", "arguments": {{"param": "value"}}}}
```

## Widget Types
- **gauge**: Real-time value with thresholds (temp, pressure, speed)
- **timeseries**: Historical trend chart (timeRange: 1h-30d)
- **value**: Large numeric KPI display
- **kpi**: Performance metric with target/trend
- **status**: Equipment state indicator
- **table**: Multi-tag data table
- **bar/pie**: Comparison/distribution charts

## Workflow
1. If data needed → call tool
2. Wait for result
3. Create widget with actual data
4. Respond with brief message + JSON

## Response Format
Brief explanation, then:
```json
{{"type": "gauge", "title": "Title", "tagId": "TAG_ID", "config": {{...}}}}
```

For multiple widgets, use array: [{...}, {...}]

Be concise. Use real data from tools."""


async def call_ollama(messages: List[Dict[str, str]], max_iterations: int = 3) -> str:
    """
    Call Ollama API for chat completion with tool support.
    Optimized for fast responses.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": MODEL_NAME,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower = more focused, faster
                        "top_p": 0.8,
                        "num_predict": 300,  # Max tokens to generate (reduced from default 2048)
                        "num_ctx": 2048,     # Context window (reduced from default 4096)
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
