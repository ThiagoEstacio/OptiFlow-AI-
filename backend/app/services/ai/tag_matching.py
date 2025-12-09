"""
Tag Matching Service
====================

Intelligent tag discovery and matching for the AI Agent.
Supports fuzzy matching, keyword extraction, and measurement type detection.
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def find_best_matching_tag(query: str, available_tags: List[Dict]) -> Optional[Dict]:
    """
    Find the best matching tag from available_tags based on query keywords.

    Matching logic:
    1. Direct mention of tag name in query
    2. Partial match (e.g., "EL01" matches "ELEV01_TEMP_C_PV")
    3. Fuzzy match on tag description/name
    """
    if not available_tags:
        return None

    query_lower = query.lower()
    logger.debug(f"🔍 find_best_matching_tag called with query: {query}")

    # Identify measurement type from query
    measurement_type = _detect_measurement_type(query_lower)
    logger.debug(f"🎯 Detected measurement_type: {measurement_type}")

    # Extract keywords from query
    keywords = _extract_keywords(query_lower)
    logger.debug(f"🔑 Extracted keywords: {keywords}")

    # Try exact match first
    for tag in available_tags:
        tag_name = tag.get('name', '').lower()
        tag_id = tag.get('id', '').lower()

        # Check if query mentions the exact tag name or ID
        if tag_name in query_lower or tag_id in query_lower:
            logger.debug(f"✅ EXACT MATCH: tag_name='{tag_name}' or tag_id='{tag_id}' found in query")
            return tag

        # Also check if any extracted keyword IS the exact tag name
        for keyword in keywords:
            if keyword == tag_name or keyword == tag_id:
                logger.debug(f"✅ KEYWORD EXACT MATCH: keyword='{keyword}' matches tag")
                return tag

    # PRIORITY: If measurement type identified, find tag with matching type
    if measurement_type:
        result = _find_tag_by_measurement_type(
            measurement_type, keywords, available_tags
        )
        if result:
            return result

    # Try partial match with fuzzy logic
    logger.debug(f"⚠️ No measurement type detected, trying fuzzy fallback with keywords: {keywords}")
    for keyword in keywords:
        for tag in available_tags:
            tag_name = tag.get('name', '').lower()
            tag_id = tag.get('id', '').lower()

            # Exact match first
            if keyword in tag_name or keyword in tag_id:
                logger.debug(f"✅ FALLBACK exact match: keyword '{keyword}' in tag '{tag.get('name')}'")
                return tag

            # Fuzzy match as fallback
            if len(keyword) >= 3:
                if _fuzzy_match(keyword, tag_name):
                    logger.debug(f"✅ FALLBACK fuzzy match: keyword '{keyword}' → tag '{tag.get('name')}'")
                    return tag

    # Last resort: return first tag
    logger.debug(f"⚠️ No matches found, returning first tag: {available_tags[0].get('name') if available_tags else 'None'}")
    return available_tags[0]


def find_matching_tags(
    query: str,
    available_tags: List[Dict],
    max_results: int = 5
) -> List[Dict]:
    """
    Find multiple matching tags based on query.

    Args:
        query: User query string
        available_tags: List of available tags
        max_results: Maximum number of tags to return

    Returns:
        List of matching tags, sorted by relevance
    """
    if not available_tags:
        return []

    query_lower = query.lower()
    keywords = _extract_keywords(query_lower)
    measurement_type = _detect_measurement_type(query_lower)

    scored_tags = []
    for tag in available_tags:
        tag_name = tag.get('name', '').lower()
        tag_id = tag.get('id', '').lower()
        score = 0

        # Exact match gets highest score
        if tag_name in query_lower or tag_id in query_lower:
            score += 100

        # Keyword match
        for keyword in keywords:
            if keyword in tag_name or keyword in tag_id:
                score += 50
            elif _fuzzy_match(keyword, tag_name):
                score += 25

        # Measurement type match
        if measurement_type and measurement_type in tag_name:
            score += 40

        if score > 0:
            scored_tags.append((score, tag))

    # Sort by score descending
    scored_tags.sort(key=lambda x: x[0], reverse=True)

    return [tag for _, tag in scored_tags[:max_results]]


def _detect_measurement_type(query_lower: str) -> Optional[str]:
    """Detect measurement type from query."""
    measurement_patterns = {
        'temp': ['temperatura', 'temp'],
        'press': ['pressão', 'pressure', 'pressao'],
        'current': ['corrente', 'current', 'ampere'],
        'power': ['potência', 'power', 'potencia'],
        'speed': ['velocidade', 'speed'],
        'level': ['nível', 'nivel', 'level'],
        'flow': ['vazão', 'vazao', 'flow'],
        'vib': ['vibração', 'vibracao', 'vibration', 'vib'],
        'humid': ['umidade', 'humidity', 'humid'],
        'ph': ['ph'],
        'dens': ['densidade', 'density'],
        'torque': ['torque'],
        'rpm': ['rpm', 'rotação', 'rotacao', 'rotation'],
        'force': ['força', 'forca', 'force'],
        'pos': ['posição', 'posicao', 'position'],
        'volt': ['tensão', 'tensao', 'voltage', 'volt'],
        'freq': ['frequência', 'frequencia', 'frequency', 'freq'],
    }

    for measurement_type, patterns in measurement_patterns.items():
        if any(p in query_lower for p in patterns):
            return measurement_type

    return None


def _extract_keywords(query_lower: str) -> List[str]:
    """Extract meaningful keywords from query."""
    # Words to exclude from keyword extraction
    exclude_words = {
        'qual', 'a', 'o', 'do', 'da', 'de', 'valor', 'atual', 'é', 'está',
        # Also exclude measurement type words
        'temperatura', 'temp', 'pressão', 'pressao', 'pressure', 'press',
        'corrente', 'current', 'ampere', 'potência', 'potencia', 'power',
        'velocidade', 'speed', 'nível', 'nivel', 'level',
        'vazão', 'vazao', 'flow', 'vibração', 'vibracao', 'vibration', 'vib',
        'umidade', 'humidity', 'humid', 'ph', 'densidade', 'density', 'dens',
        'torque', 'rpm', 'rotação', 'rotacao', 'rotation',
        'força', 'forca', 'force', 'posição', 'posicao', 'position', 'pos',
        'tensão', 'tensao', 'voltage', 'volt', 'frequência', 'frequencia', 'frequency', 'freq'
    }

    keywords = []
    for word in query_lower.split():
        clean_word = word.strip('.,?!;:')
        if clean_word and clean_word not in exclude_words:
            keywords.append(clean_word)

    return keywords


def _fuzzy_match(keyword: str, tag_name: str) -> bool:
    """Check if keyword fuzzy matches tag name."""
    if len(keyword) < 3:
        return False

    keyword_parts = [c for c in keyword if c.isalnum()]
    tag_name_clean = ''.join([c for c in tag_name if c.isalnum()])

    if not all(char in tag_name_clean for char in keyword_parts):
        return False

    # Check if characters appear in order
    idx = 0
    for char in keyword_parts:
        new_idx = tag_name_clean.find(char, idx)
        if new_idx == -1:
            return False
        idx = new_idx + 1

    return True


def _find_tag_by_measurement_type(
    measurement_type: str,
    keywords: List[str],
    available_tags: List[Dict]
) -> Optional[Dict]:
    """Find tag matching measurement type and keywords."""
    logger.debug(f"🔍 Searching for tags with measurement_type={measurement_type}")

    # First, find all tags that match any keyword
    matching_tags = []
    for tag in available_tags:
        tag_name = tag.get('name', '').lower()
        tag_id = tag.get('id', '').lower()

        for keyword in keywords:
            if keyword in tag_name or keyword in tag_id:
                matching_tags.append(tag)
                logger.debug(f"  ➕ Tag matched keyword '{keyword}' (exact): {tag.get('name')}")
                break
            elif _fuzzy_match(keyword, tag_name):
                matching_tags.append(tag)
                logger.debug(f"  ➕ Tag matched keyword '{keyword}' (fuzzy): {tag.get('name')}")
                break

    logger.debug(f"📋 Found {len(matching_tags)} tags matching keywords")

    # Filter by measurement type
    for tag in matching_tags:
        tag_name = tag.get('name', '').lower()
        if measurement_type in tag_name:
            logger.debug(f"✅ MATCHED TAG with measurement_type={measurement_type}: {tag.get('name')}")
            return tag

    logger.debug(f"⚠️ No tags found with measurement_type={measurement_type} in {len(matching_tags)} candidates")
    return None


def get_trend_icon(trend: str) -> str:
    """Get icon for trend direction."""
    icons = {
        "up": "📈",
        "down": "📉",
        "stable": "➡️",
        "critical": "🔴",
        "warning": "🟡",
        "normal": "🟢",
    }
    return icons.get(trend, "❓")
