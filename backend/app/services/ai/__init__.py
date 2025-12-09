"""
AI Services Package
==================

Provides modular AI components for the OptiFlow platform:
- prompts: System prompts and personas
- tag_matching: Intelligent tag discovery
- tool_definitions: JSON Schema definitions for LLM tools
- tool_parsing: Tool call extraction and formatting
- ollama_client: Async LLM client with streaming support
"""

from .prompts import (
    PERSONA_PROMPTS,
    detect_persona,
    get_system_prompt,
    SYSTEM_PROMPT_WITH_DATA,
    SYSTEM_PROMPT_TEMPLATE,
)
from .tag_matching import (
    find_best_matching_tag,
    find_matching_tags,
    get_trend_icon,
)
from .tool_definitions import (
    AVAILABLE_TOOLS,
    get_tool_by_name,
    get_tool_names,
)
from .tool_parsing import (
    ToolCall,
    ToolResult,
    format_tools_for_prompt,
    extract_tool_calls_with_fallback,
    extract_tool_calls_from_response,
    format_tool_results_for_llm,
)
from .ollama_client import (
    OllamaConfig,
    OllamaError,
    OllamaConnectionError,
    OllamaAPIError,
    call_ollama,
    call_ollama_stream,
    extract_json_from_response,
    DEFAULT_CONFIG as OLLAMA_DEFAULT_CONFIG,
)

__all__ = [
    # Prompts
    "PERSONA_PROMPTS",
    "detect_persona",
    "get_system_prompt",
    "SYSTEM_PROMPT_WITH_DATA",
    "SYSTEM_PROMPT_TEMPLATE",
    # Tag matching
    "find_best_matching_tag",
    "find_matching_tags",
    "get_trend_icon",
    # Tool definitions
    "AVAILABLE_TOOLS",
    "get_tool_by_name",
    "get_tool_names",
    # Tool parsing
    "ToolCall",
    "ToolResult",
    "format_tools_for_prompt",
    "extract_tool_calls_with_fallback",
    "extract_tool_calls_from_response",
    "format_tool_results_for_llm",
    # Ollama client
    "OllamaConfig",
    "OllamaError",
    "OllamaConnectionError",
    "OllamaAPIError",
    "call_ollama",
    "call_ollama_stream",
    "extract_json_from_response",
    "OLLAMA_DEFAULT_CONFIG",
]
