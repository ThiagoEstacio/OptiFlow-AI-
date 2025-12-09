"""
AI Services Package
==================

Provides modular AI components for the OptiFlow platform:
- prompts: System prompts and personas
- tag_matching: Intelligent tag discovery
- ollama: LLM integration (planned)
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
]
