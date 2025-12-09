"""
Tool Parsing and Formatting for AI Agent
=========================================

Functions to parse tool calls from LLM responses and format
tool definitions/results for the LLM.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import re
import logging

logger = logging.getLogger(__name__)


class ToolCall(BaseModel):
    """A tool call request from the LLM"""
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    """Result of a tool execution"""
    tool_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None


def format_tools_for_prompt(tools: List[Dict[str, Any]]) -> str:
    """
    Format tool definitions for inclusion in the system prompt.

    Args:
        tools: List of tool definitions

    Returns:
        Formatted string describing available tools
    """
    tool_descriptions = []

    for tool in tools:
        params = tool["parameters"]["properties"]
        required = tool["parameters"].get("required", [])

        param_str = ", ".join([
            f"{name}{'*' if name in required else ''}: {info['description']}"
            for name, info in params.items()
        ])

        tool_descriptions.append(
            f"- **{tool['name']}**({param_str}): {tool['description']}"
        )

    return "\n".join(tool_descriptions)


def extract_tool_calls_with_fallback(
    response_text: str,
    available_tags: Optional[List[Dict]] = None
) -> List[ToolCall]:
    """
    Extract tool calls with intelligent fallback for models that don't follow ```tool format.

    Two-phase extraction:
    1. Try native ```tool block extraction (preferred)
    2. Fallback to heuristic detection if no blocks found

    Args:
        response_text: Raw response from LLM
        available_tags: List of available tags for context-aware detection

    Returns:
        List of ToolCall objects
    """
    # PHASE 1: Try native tool block extraction
    tool_calls = _extract_native_tool_blocks(response_text)

    if tool_calls:
        logger.info(f"✅ Native tool extraction: Found {len(tool_calls)} tool(s)")
        return tool_calls

    # PHASE 2: Heuristic fallback
    logger.info("🔄 No ```tool blocks found, trying heuristic detection...")
    tool_calls = _extract_heuristic_tool_calls(response_text, available_tags)

    if tool_calls:
        logger.info(f"✅ Heuristic detection: Found {len(tool_calls)} tool(s)")
    else:
        logger.info("⚠️  No tools detected (native or heuristic)")

    return tool_calls


def _extract_native_tool_blocks(response_text: str) -> List[ToolCall]:
    """Extract tool calls from ```tool code blocks."""
    tool_calls = []
    pattern = r'```tool\s*\n(.*?)\n```'
    matches = re.findall(pattern, response_text, re.DOTALL)

    for match in matches:
        try:
            tool_data = json.loads(match.strip())
            tool_calls.append(ToolCall(
                name=tool_data["name"],
                arguments=tool_data.get("arguments", {})
            ))
        except Exception as e:
            logger.warning(f"Failed to parse tool call: {e}")

    return tool_calls


def _extract_heuristic_tool_calls(
    response_text: str,
    available_tags: Optional[List[Dict]] = None
) -> List[ToolCall]:
    """Heuristic-based tool call detection for non-compliant models."""
    tool_calls = []
    response_lower = response_text.lower()

    # Heuristic 1: Detect real-time value queries
    realtime_call = _detect_realtime_value_call(response_text, response_lower, available_tags)
    if realtime_call:
        return [realtime_call]  # Early return

    # Heuristic 2: Detect tag search queries
    search_call = _detect_search_tags_call(response_text, response_lower)
    if search_call:
        tool_calls.append(search_call)
        return tool_calls

    # Heuristic 3: Detect statistics calculation queries
    stats_call = _detect_statistics_call(response_text, response_lower, available_tags)
    if stats_call:
        tool_calls.append(stats_call)

    return tool_calls


def _detect_realtime_value_call(
    response_text: str,
    response_lower: str,
    available_tags: Optional[List[Dict]]
) -> Optional[ToolCall]:
    """Detect get_realtime_value tool calls."""
    # Check for direct function call format: get_realtime_value("TAG_NAME")
    function_call_pattern = r'get_realtime_value\s*\(\s*["\']([^"\']+)["\']\s*\)'
    function_match = re.search(function_call_pattern, response_text)
    if function_match:
        tag_id = function_match.group(1)
        logger.info(f"🎯 Heuristic detected (function format): get_realtime_value(tag_id={tag_id})")
        return ToolCall(name="get_realtime_value", arguments={"tag_id": tag_id})

    # Pattern-based detection
    realtime_patterns = [
        r'(?:temperatura|temp|pressão|press|velocidade|vel|corrente|potência|power).*?(?:atual|corrente|agora|em tempo real)',
        r'(?:qual|quais|me mostre|buscar|obter).*?(?:valor|dado|medição).*?(?:atual|corrente)',
        r'get_realtime_value\s*\(\s*["\']?tag_id["\']?\s*[:=]\s*["\']([^"\']+)["\']',
    ]

    for pattern in realtime_patterns:
        match = re.search(pattern, response_lower)
        if match:
            tag_id = None

            # Check if explicit tag_id in response
            explicit_tag = re.search(r'tag_id["\']?\s*[:=]\s*["\']([^"\']+)["\']', response_text)
            if explicit_tag:
                tag_id = explicit_tag.group(1)
            elif available_tags and len(available_tags) > 0:
                tag_id = available_tags[0].get('id')

            if tag_id:
                logger.info(f"🎯 Heuristic detected: get_realtime_value(tag_id={tag_id})")
                return ToolCall(name="get_realtime_value", arguments={"tag_id": tag_id})

    return None


def _detect_search_tags_call(response_text: str, response_lower: str) -> Optional[ToolCall]:
    """Detect search_tags tool calls."""
    search_patterns = [
        r'(?:liste|listar|buscar|procurar|encontrar|pesquisar).*?(?:tags|sensores|medições)',
        r'(?:quais|todas).*?(?:tags|sensores).*?(?:disponíveis|existentes)',
        r'search_tags\s*\(\s*["\']?query["\']?\s*[:=]\s*["\']([^"\']+)["\']',
    ]

    for pattern in search_patterns:
        match = re.search(pattern, response_lower)
        if match:
            query = None

            # Check for explicit query parameter
            explicit_query = re.search(r'query["\']?\s*[:=]\s*["\']([^"\']+)["\']', response_text)
            if explicit_query:
                query = explicit_query.group(1)
            else:
                # Extract keywords from user message
                keywords = re.findall(
                    r'(?:temperatura|pressão|velocidade|corrente|potência|nivel|fluxo)',
                    response_lower
                )
                if keywords:
                    query = keywords[0]
                else:
                    query = ""  # List all tags

            logger.info(f"🎯 Heuristic detected: search_tags(query={query})")
            return ToolCall(name="search_tags", arguments={"query": query, "limit": 20})

    return None


def _detect_statistics_call(
    response_text: str,
    response_lower: str,
    available_tags: Optional[List[Dict]]
) -> Optional[ToolCall]:
    """Detect calculate_statistics tool calls."""
    stats_patterns = [
        r'(?:média|mínimo|máximo|estatística|stats|calcular).*?(?:últimas|ultimos|nas|dos)',
        r'calculate_statistics\s*\(',
    ]

    for pattern in stats_patterns:
        match = re.search(pattern, response_lower)
        if match:
            tag_id = None
            period = "24h"

            # Extract tag_id
            explicit_tag = re.search(r'tag_id["\']?\s*[:=]\s*["\']([^"\']+)["\']', response_text)
            if explicit_tag:
                tag_id = explicit_tag.group(1)
            elif available_tags and len(available_tags) > 0:
                tag_id = available_tags[0].get('id')

            # Extract period
            period_match = re.search(r'(\d+)\s*(h|hora|horas|day|dia|dias)', response_lower)
            if period_match:
                value = period_match.group(1)
                unit = period_match.group(2)
                if 'h' in unit or 'hora' in unit:
                    period = f"{value}h"
                elif 'd' in unit or 'dia' in unit:
                    period = f"{int(value)*24}h"

            if tag_id:
                logger.info(f"🎯 Heuristic detected: calculate_statistics(tag_id={tag_id}, duration={period})")
                return ToolCall(name="calculate_statistics", arguments={"tag_id": tag_id, "duration": period})

    return None


def extract_tool_calls_from_response(response_text: str) -> List[ToolCall]:
    """
    DEPRECATED: Use extract_tool_calls_with_fallback() instead.

    Extract tool calls from LLM response (native ```tool blocks only)
    """
    return _extract_native_tool_blocks(response_text)


def format_tool_results_for_llm(results: List[ToolResult]) -> str:
    """
    Format tool execution results for sending back to the LLM.

    Args:
        results: List of tool execution results

    Returns:
        Formatted string
    """
    formatted = []

    for result in results:
        if result.success:
            formatted.append(
                f"Tool '{result.tool_name}' returned:\n```json\n{json.dumps(result.data, indent=2)}\n```"
            )
        else:
            formatted.append(
                f"Tool '{result.tool_name}' failed: {result.error}"
            )

    return "\n\n".join(formatted)
