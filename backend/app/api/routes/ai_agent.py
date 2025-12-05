"""
AI Agent API Routes - Dashboard Builder Assistant

Provides endpoints for conversational dashboard creation using local LLM (Ollama).
Now with enhanced capabilities:
- Real-time data access
- Historical data queries
- Statistical calculations
- Function calling / tool use
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import json
import re
import logging
import asyncio
import time
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...db.session import get_db
from ...services.data_service import DataService
from ...services.circuit_breaker import CircuitBreaker
from ...services.agent_tools import (
    AgentToolkit,
    format_tools_for_prompt,
    extract_tool_calls_from_response,
    extract_tool_calls_with_fallback,  # NEW: Heuristic fallback
    format_tool_results_for_llm
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Rate limiter for AI endpoints (expensive operations)
limiter = Limiter(key_func=get_remote_address)

# Ollama configuration
import os
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
# Qwen2.5:7B - Superior reasoning for industrial applications
# Optimized for 16GB RAM + 8GB VRAM (RTX 4060)
# Alternative: mistral:7b (also excellent)
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# Circuit breaker for Ollama (prevent cascade failures when LLM is overloaded)
ollama_circuit_breaker = CircuitBreaker(
    failure_threshold=3,      # Open circuit after 3 consecutive Ollama failures
    success_threshold=2,      # Close circuit after 2 successful calls
    timeout=30,               # Wait 30s before retrying Ollama
    half_open_max_calls=2,    # Test with max 2 calls in half-open state
    name="ollama_llm"
)


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class ToolCallRequest(BaseModel):
    """Direct tool call request (bypasses LLM)"""
    name: str
    arguments: Dict[str, Any]


class DashboardAgentRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    available_tags: Optional[List[Dict[str, Any]]] = None
    current_widgets: Optional[List[Dict[str, Any]]] = None
    tool_call: Optional[ToolCallRequest] = None  # Direct tool execution


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
    tool_result: Optional[Dict[str, Any]] = None  # Raw tool result data


# =============================================================================
# SYSTEM PROMPTS - Analista Sênior PCO/PCM/Qualidade (Indústria 4.0)
# =============================================================================

# System prompt for DATA-DRIVEN analysis (with pre-fetched data)
SYSTEM_PROMPT_WITH_DATA = """Você é um ANALISTA SÊNIOR de PCO (Planejamento e Controle de Operações), PCM (Planejamento e Controle da Manutenção) e QUALIDADE, atuando 24h em uma PLATAFORMA DE INDÚSTRIA 4.0.

## SEU PAPEL:
- Monitorar continuamente o processo industrial
- Detectar anomalias e desvios de comportamento
- Prever falhas e problemas de qualidade
- Sugerir ações de operação e manutenção
- Apoiar decisões com BASE EM DADOS, não opinião

Você une: Ferramentas de Qualidade (Ishikawa, 5 Porquês, Pareto, CEP), Ciência de Dados, Machine Learning, visão de PCO, PCM e Qualidade.

## DADOS DISPONÍVEIS:
{data_context}

## SUA ANÁLISE DEVE CONTER:

1) 📊 **VISÃO GERAL**
   - Resumo em 2-3 frases do cenário atual

2) 🔍 **PRINCIPAIS INSIGHTS** (3-5 pontos)
   - Desvios, tendências, anomalias detectadas
   - Diferenças entre turnos/máquinas/linhas (se aplicável)
   - Impactos em produção, manutenção, qualidade

3) 🎯 **DIAGNÓSTICO PROVÁVEL**
   - O que está acontecendo e por quê
   - Nível de confiança: alta | média | baixa

4) ⚙️ **RECOMENDAÇÕES PCO** (Operação)
   - Ajuste de ritmo, priorização, gargalos

5) 🔧 **RECOMENDAÇÕES PCM** (Manutenção)
   - Inspeções, verificações, programação

6) ✅ **RECOMENDAÇÕES QUALIDADE**
   - Estabilização do processo, redução de rejeito

## REGRAS:
- NUNCA assuma que o sistema escreve no processo (somente leitura)
- Seja TRANSPARENTE sobre incertezas
- NÃO invente números - use os dados fornecidos
- Pense como quem está na SALA DE CONTROLE: prático e orientado à ação
- Use Markdown com emojis para clareza

## CONTEXTO DO USUÁRIO:
Pergunta: {user_query}

Analise os dados acima e responda como um Analista Sênior, transformando dados em INSIGHTS ACIONÁVEIS."""

# Fallback prompt (when no tools available or for tool-calling mode)
SYSTEM_PROMPT_TEMPLATE = """OptiFlow AI - Analista Sênior PCO/PCM/Qualidade

Você é um ANALISTA SÊNIOR de Indústria 4.0 especializado em:
- PCO: gargalos, capacidade, eficiência, OEE
- PCM: manutenção preditiva, falhas, MTBF/MTTR
- Qualidade: CEP, defeitos, variabilidade, Pareto

{tools}

## COMO AGIR:
1. ENTENDER o cenário e variáveis críticas
2. ANALISAR padrões, tendências, correlações
3. DIAGNOSTICAR causas prováveis
4. RECOMENDAR ações práticas

## FORMATO:
📊 **Situação** → 🔍 **Análise** → 🎯 **Diagnóstico** → 💡 **Ações**

## REGRAS:
- SEMPRE busque dados reais usando ferramentas antes de responder
- Use blocos ```tool para chamar ferramentas
- Português, conciso, Markdown com emojis
- Seja transparente sobre incertezas
- Priorize por criticidade/impacto"""


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

    # Identify measurement type from query - EXPANDED for all industrial variables
    measurement_type = None
    if 'temperatura' in query_lower or 'temp' in query_lower:
        measurement_type = 'temp'
    elif 'pressão' in query_lower or 'pressure' in query_lower or 'pressao' in query_lower:
        measurement_type = 'press'
    elif 'corrente' in query_lower or 'current' in query_lower or 'ampere' in query_lower:
        measurement_type = 'current'
    elif 'potência' in query_lower or 'power' in query_lower or 'potencia' in query_lower:
        measurement_type = 'power'
    elif 'velocidade' in query_lower or 'speed' in query_lower:
        measurement_type = 'speed'
    elif 'nível' in query_lower or 'nivel' in query_lower or 'level' in query_lower:
        measurement_type = 'level'
    elif 'vazão' in query_lower or 'vazao' in query_lower or 'flow' in query_lower:
        measurement_type = 'flow'
    elif 'vibração' in query_lower or 'vibracao' in query_lower or 'vibration' in query_lower or 'vib' in query_lower:
        measurement_type = 'vib'
    elif 'umidade' in query_lower or 'humidity' in query_lower or 'humid' in query_lower:
        measurement_type = 'humid'
    elif 'ph' in query_lower:
        measurement_type = 'ph'
    elif 'densidade' in query_lower or 'density' in query_lower:
        measurement_type = 'dens'
    elif 'torque' in query_lower:
        measurement_type = 'torque'
    elif 'rpm' in query_lower or 'rotação' in query_lower or 'rotacao' in query_lower or 'rotation' in query_lower:
        measurement_type = 'rpm'
    elif 'força' in query_lower or 'forca' in query_lower or 'force' in query_lower:
        measurement_type = 'force'
    elif 'posição' in query_lower or 'posicao' in query_lower or 'position' in query_lower:
        measurement_type = 'pos'
    elif 'tensão' in query_lower or 'tensao' in query_lower or 'voltage' in query_lower or 'volt' in query_lower:
        measurement_type = 'volt'
    elif 'frequência' in query_lower or 'frequencia' in query_lower or 'frequency' in query_lower or 'freq' in query_lower:
        measurement_type = 'freq'

    logger.debug(f"🎯 Detected measurement_type: {measurement_type}")

    # Extract keywords from query (remove common words AND measurement type words)
    measurement_words = [
        'temperatura', 'temp', 'pressão', 'pressao', 'pressure', 'press',
        'corrente', 'current', 'ampere', 'potência', 'potencia', 'power',
        'velocidade', 'speed', 'nível', 'nivel', 'level',
        'vazão', 'vazao', 'flow', 'vibração', 'vibracao', 'vibration', 'vib',
        'umidade', 'humidity', 'humid', 'ph', 'densidade', 'density', 'dens',
        'torque', 'rpm', 'rotação', 'rotacao', 'rotation',
        'força', 'forca', 'force', 'posição', 'posicao', 'position', 'pos',
        'tensão', 'tensao', 'voltage', 'volt', 'frequência', 'frequencia', 'frequency', 'freq'
    ]
    keywords = []
    for word in query_lower.split():
        # Remove punctuation from word
        clean_word = word.strip('.,?!;:')
        # Remove common words AND measurement type words (we handle those separately)
        if clean_word and clean_word not in ['qual', 'a', 'o', 'do', 'da', 'de', 'valor', 'atual', 'é', 'está'] and clean_word not in measurement_words:
            keywords.append(clean_word)

    logger.debug(f"🔑 Extracted keywords: {keywords}")

    # Try exact match first - EXPANDED to also check keywords for exact matches
    for tag in available_tags:
        tag_name = tag.get('name', '').lower()
        tag_id = tag.get('id', '').lower()

        # Check if query mentions the exact tag name or ID
        if tag_name in query_lower or tag_id in query_lower:
            logger.debug(f"✅ EXACT MATCH: tag_name='{tag_name}' or tag_id='{tag_id}' found in query")
            return tag

        # Also check if any extracted keyword IS the exact tag name (e.g., "por_carregamento")
        for keyword in keywords:
            if keyword == tag_name or keyword == tag_id:
                logger.debug(f"✅ KEYWORD EXACT MATCH: keyword='{keyword}' matches tag")
                return tag

    # PRIORITY: If measurement type identified, find tag with matching type
    if measurement_type:
        logger.debug(f"🔍 Searching for tags with measurement_type={measurement_type}")
        # First, find all tags that match any keyword (fuzzy matching)
        matching_tags = []
        for tag in available_tags:
            tag_name = tag.get('name', '').lower()
            tag_id = tag.get('id', '').lower()

            # Check if ANY keyword matches this tag (with fuzzy logic)
            for keyword in keywords:
                # Fuzzy match: keyword in tag OR tag starts with keyword-like pattern
                # Example: "el01" matches "elev01_temp_c_pv" because both contain "el" and "01"
                keyword_parts = [c for c in keyword if c.isalnum()]
                tag_name_clean = ''.join([c for c in tag_name if c.isalnum()])

                # Simple fuzzy: check if most characters of keyword appear in order in tag name
                if keyword in tag_name or keyword in tag_id:
                    matching_tags.append(tag)
                    logger.debug(f"  ➕ Tag matched keyword '{keyword}' (exact): {tag.get('name')}")
                    break
                # Fuzzy match for partial names like "el01" -> "elev01"
                elif len(keyword) >= 3 and all(char in tag_name_clean for char in keyword_parts):
                    # Check if characters appear in roughly the same order
                    idx = 0
                    for char in keyword_parts:
                        new_idx = tag_name_clean.find(char, idx)
                        if new_idx == -1:
                            break
                        idx = new_idx + 1
                    else:
                        matching_tags.append(tag)
                        logger.debug(f"  ➕ Tag matched keyword '{keyword}' (fuzzy): {tag.get('name')}")
                        break

        logger.debug(f"📋 Found {len(matching_tags)} tags matching keywords")

        # Then, filter by measurement type
        for tag in matching_tags:
            tag_name = tag.get('name', '').lower()
            logger.debug(f"  🔎 Checking tag '{tag.get('name')}': Does '{tag_name}' contain '{measurement_type}'? {measurement_type in tag_name}")
            if measurement_type in tag_name:
                logger.debug(f"✅ MATCHED TAG with measurement_type={measurement_type}: {tag.get('name')}")
                return tag

        logger.debug(f"⚠️ No tags found with measurement_type={measurement_type} in {len(matching_tags)} candidates")

    # Try partial match with fuzzy logic (e.g., "el01" matches "ELEV01_TEMP_C_PV")
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
                keyword_parts = [c for c in keyword if c.isalnum()]
                tag_name_clean = ''.join([c for c in tag_name if c.isalnum()])

                if all(char in tag_name_clean for char in keyword_parts):
                    # Check if characters appear in order
                    idx = 0
                    for char in keyword_parts:
                        new_idx = tag_name_clean.find(char, idx)
                        if new_idx == -1:
                            break
                        idx = new_idx + 1
                    else:
                        logger.debug(f"✅ FALLBACK fuzzy match: keyword '{keyword}' → tag '{tag.get('name')}'")
                        return tag

    # Last resort: return first tag
    logger.debug(f"⚠️ No matches found, returning first tag: {available_tags[0].get('name') if available_tags else 'None'}")
    return available_tags[0]


def _get_trend_icon(trend: str) -> str:
    """Get icon for trend direction"""
    if trend == "up":
        return "📈"
    elif trend == "down":
        return "📉"
    elif trend == "stable":
        return "➡️"
    return ""


async def pre_execute_tools_from_query(
    query: str,
    available_tags: Optional[List[Dict]],
    toolkit: AgentToolkit
) -> Optional[str]:
    """
    PRE-EXECUTE tools based on query analysis BEFORE calling LLM.
    This ensures LLM ALWAYS has real data to analyze.

    Returns: Formatted data context string or None
    """
    query_lower = query.lower()
    data_results = []

    # Pattern 1: Realtime value queries
    # EXPANDED: Now includes "valor de {tag}", "qual o valor de {tag}", direct tag names
    # NOTE: Include both accented and non-accented versions for PT-BR compatibility
    realtime_patterns = [
        # With accents
        'temperatura atual', 'pressão atual', 'valor atual', 'velocidade atual',
        'qual a temperatura', 'qual a pressão', 'qual o valor', 'qual o nivel',
        'quanto está', 'quanto é', 'mostre', 'valor de', 'valor do', 'valor da',
        'qual é o valor', 'me mostre o valor', 'leitura de', 'leitura do', 'leitura da',
        # Without accents (PT-BR compatibility)
        'pressao atual', 'qual a pressao', 'qual o nivel', 'qual a nivel',
        'quanto esta', 'corrente atual', 'vazao atual', 'qual a vazao', 'qual a corrente',
        # Direct measurement type queries
        'qual a temperatura', 'qual a pressao', 'qual a velocidade',
        'qual a corrente', 'qual a vazao', 'qual o nivel',
        # Equipment-specific patterns
        'temperatura da', 'temperatura do', 'pressao da', 'pressao do',
        'nivel do', 'nivel da', 'vazao da', 'vazao do', 'corrente da', 'corrente do'
    ]

    # Also detect direct tag name queries (e.g., "por_carregamento" or "ELEV01_TEMP")
    # If the query contains a tag-like name pattern (word with underscore or specific format)
    import re
    tag_name_pattern = re.search(r'\b([a-zA-Z][a-zA-Z0-9_]*(?:_[a-zA-Z0-9]+)+)\b', query)
    has_tag_name_in_query = tag_name_pattern is not None

    if any(pattern in query_lower for pattern in realtime_patterns) or has_tag_name_in_query:
        # Try to find a tag via props first, then fall back to regex in the user text
        matched_tag = None
        tag_id = None
        tag_name = None
        unit = ''

        logger.debug(f"🔍 PRE-EXECUTE: Query='{query}', available_tags count={len(available_tags) if available_tags else 0}")

        if available_tags:
            logger.debug("🔍 Calling find_best_matching_tag...")
            matched_tag = find_best_matching_tag(query, available_tags)
            logger.debug(f"🔍 PRE-EXECUTE: Matched tag={matched_tag}")

        if matched_tag:
            tag_id = matched_tag.get('id')
            tag_name = matched_tag.get('name', tag_id)
            unit = matched_tag.get('unit', '')
            logger.info(f"🔍 PRE-EXECUTE: Using matched tag - id={tag_id}, name={tag_name}, unit={unit}")
            # IMPORTANT: Use tag NAME for InfluxDB lookup, not UUID!
            tag_lookup = tag_name if tag_name else tag_id
        else:
            # AUTO-DISCOVER from Gateway based on query keywords
            # Step 1: Detect measurement type
            measurement_keyword = None
            keyword_map = {
                'temperatura': 'Temperatura', 'temperature': 'Temperatura', 'temp': 'Temperatura',
                'pressão': 'Pressao', 'pressao': 'Pressao', 'pressure': 'Pressao',
                'nível': 'Nivel', 'nivel': 'Nivel', 'level': 'Nivel',
                'vazão': 'Vazao', 'vazao': 'Vazao', 'flow': 'Vazao',
                'corrente': 'Corrente', 'current': 'Corrente',
                'velocidade': 'Velocidade', 'speed': 'Velocidade',
                'rpm': 'RPM', 'rotação': 'RPM', 'rotacao': 'RPM',
                'potência': 'Potencia', 'potencia': 'Potencia', 'power': 'Potencia',
                'umidade': 'Umidade', 'humidity': 'Umidade',
                'peso': 'Peso', 'weight': 'Peso',
            }

            for keyword, gateway_keyword in keyword_map.items():
                if keyword in query_lower:
                    measurement_keyword = gateway_keyword
                    break

            # Step 2: Extract equipment context (silo1, linha1, motor1, etc.)
            equipment_context = None
            equipment_patterns = [
                r'silo\s*(\d+)', r'linha\s*(\d+)', r'motor\s*(\d+)', r'bomba\s*(\d+)',
                r'esteira\s*(\d+)', r'caldeira\s*(\d+)', r'compressor\s*(\d+)',
                r'balanca\s*(\d+)', r'balanc[aç]a\s*(\d+)'
            ]
            for pattern in equipment_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    equip_name = pattern.split(r'\s')[0].replace('\\', '')  # Extract equipment type
                    equip_num = match.group(1)
                    equipment_context = f"{equip_name.title()}{equip_num}"
                    break

            # Step 3: Build search query combining measurement + equipment
            if measurement_keyword:
                if equipment_context:
                    # Search with equipment context first (more specific)
                    search_query = f"{equipment_context}_{measurement_keyword}"
                    logger.info(f"🔍 PRE-EXECUTE: Searching specific tag '{search_query}'")
                    search_result = await toolkit.execute_tool("search_tags", {"query": search_query, "limit": 5})

                    if search_result.success and search_result.data:
                        tags = search_result.data if isinstance(search_result.data, list) else search_result.data.get('tags', [])
                        if tags and len(tags) > 0:
                            tag_lookup = tags[0].get('name') or tags[0].get('tag_name') or tags[0].get('id')
                            tag_name = tag_lookup
                            unit = tags[0].get('unit', '') or tags[0].get('metadata', {}).get('engineering_units', '')
                            logger.info(f"🎯 PRE-EXECUTE: Found specific tag: {tag_name}")

                # If no specific tag found, try generic measurement search
                if not tag_lookup:
                    logger.info(f"🔍 PRE-EXECUTE: Searching generic '{measurement_keyword}'")
                    search_result = await toolkit.execute_tool("search_tags", {"query": measurement_keyword, "limit": 5})
                    if search_result.success and search_result.data:
                        tags = search_result.data if isinstance(search_result.data, list) else search_result.data.get('tags', [])
                        if tags and len(tags) > 0:
                            # If we have equipment context, try to filter by it
                            if equipment_context:
                                for tag in tags:
                                    tname = (tag.get('name') or tag.get('tag_name') or '').lower()
                                    if equipment_context.lower().replace(' ', '') in tname.replace('_', ''):
                                        tag_lookup = tag.get('name') or tag.get('tag_name') or tag.get('id')
                                        tag_name = tag_lookup
                                        unit = tag.get('unit', '') or tag.get('metadata', {}).get('engineering_units', '')
                                        logger.info(f"🎯 PRE-EXECUTE: Matched with context: {tag_name}")
                                        break
                            # Fallback to first tag
                            if not tag_lookup:
                                tag_lookup = tags[0].get('name') or tags[0].get('tag_name') or tags[0].get('id')
                                tag_name = tag_lookup
                                unit = tags[0].get('unit', '') or tags[0].get('metadata', {}).get('engineering_units', '')
                                logger.info(f"🎯 PRE-EXECUTE: Using first match: {tag_name}")

            # Fallback: Heuristic capture from prompt (e.g., "ELEV01_TEMP_C_PV")
            if not tag_lookup:
                tag_candidates = re.findall(r'[A-Za-z0-9]+(?:[_\-\.][A-Za-z0-9]+)+', query)
                if tag_candidates:
                    tag_lookup = tag_candidates[0]
                    tag_name = tag_lookup
                    tag_id = tag_lookup

        if tag_lookup:
            logger.info(f"🎯 PRE-EXECUTING: get_realtime_value(tag_id={tag_lookup}) [matched from query]")
            result = await toolkit.execute_tool("get_realtime_value", {"tag_id": tag_lookup})

            if result.success and result.data:
                value = result.data.get('value')
                timestamp = result.data.get('timestamp', 'N/A')
                source = result.data.get('source', 'influxdb')
                actual_unit = result.data.get('unit', unit)
                actual_name = result.data.get('tag_name', tag_name)

                if value is not None:
                    # Format value nicely
                    if isinstance(value, float):
                        value_str = f"{value:.2f}"
                    else:
                        value_str = str(value)
                    data_results.append(f"**{actual_name}**: {value_str} {actual_unit} (em {timestamp})")
                    if source == 'gateway':
                        data_results.append(f"  _(Fonte: Gateway Edge - Dados em tempo real)_")
                else:
                    data_results.append(f"**{actual_name or tag_lookup}**: Sem dados disponíveis")
            else:
                data_results.append(f"**{tag_name or tag_lookup}**: Sem dados disponíveis")

    # Pattern 2: Statistics queries
    stats_patterns = ['média', 'media', 'máximo', 'maximo', 'mínimo', 'minimo',
                      'estatística', 'estatistica', 'estatísticas', 'estatisticas',
                      'últimas', 'ultimas', 'últimos', 'ultimos', 'calcule', 'calculate']

    if any(pattern in query_lower for pattern in stats_patterns):
        # Extract time period
        duration = "24h"
        if "24 horas" in query_lower or "24h" in query_lower:
            duration = "24h"
        elif "12 horas" in query_lower or "12h" in query_lower:
            duration = "12h"
        elif "semana" in query_lower:
            duration = "168h"

        # Determine which tag to use
        tag_id = None
        tag_name = None

        if available_tags and len(available_tags) > 0:
            tag_id = available_tags[0].get('id')
            tag_name = available_tags[0].get('name', tag_id)
        else:
            # Try to find a tag based on query keywords
            search_keyword = None
            for keyword in ['temperatura', 'temperature', 'pressão', 'pressure', 'velocidade', 'speed',
                           'corrente', 'current', 'potência', 'power', 'umidade', 'humidity', 'vibração', 'vibration']:
                if keyword in query_lower:
                    search_keyword = keyword
                    break

            if search_keyword:
                logger.info(f"🔍 PRE-EXECUTE: Searching tags with keyword '{search_keyword}'")
                search_result = await toolkit.execute_tool("search_tags", {"query": search_keyword, "limit": 1})
                if search_result.success and search_result.data:
                    tags = search_result.data if isinstance(search_result.data, list) else search_result.data.get('tags', [])
                    if tags and len(tags) > 0:
                        tag_id = tags[0].get('id') or tags[0].get('name')
                        tag_name = tags[0].get('name', tag_id)

        if tag_id:
            logger.info(f"🎯 PRE-EXECUTING: calculate_statistics(tag_id={tag_id}, duration={duration})")
            result = await toolkit.execute_tool("calculate_statistics", {"tag_id": tag_id, "duration": duration})

            if result.success and result.data:
                stats = result.data
                actual_name = stats.get('tag_name', tag_name)
                source = stats.get('source', 'influxdb')
                note = stats.get('note', '')

                data_results.append(f"**Estatísticas de {actual_name} ({duration})**:")

                # Format numeric values
                mean_val = stats.get('mean')
                min_val = stats.get('min')
                max_val = stats.get('max')
                std_val = stats.get('std_dev')
                unit = stats.get('unit', '')

                if mean_val is not None:
                    data_results.append(f"  - Média: {mean_val:.2f} {unit}" if isinstance(mean_val, float) else f"  - Média: {mean_val} {unit}")
                if min_val is not None:
                    data_results.append(f"  - Mínimo: {min_val:.2f} {unit}" if isinstance(min_val, float) else f"  - Mínimo: {min_val} {unit}")
                if max_val is not None:
                    data_results.append(f"  - Máximo: {max_val:.2f} {unit}" if isinstance(max_val, float) else f"  - Máximo: {max_val} {unit}")
                if std_val is not None:
                    data_results.append(f"  - Desvio padrão: {std_val:.2f}" if isinstance(std_val, float) else f"  - Desvio padrão: {std_val}")
                data_results.append(f"  - Total de leituras: {stats.get('count', 'N/A')}")

                if note:
                    data_results.append(f"  _{note}_")
                if source == 'gateway':
                    data_results.append(f"  _(Fonte: Gateway Edge)_")
        else:
            data_results.append("**⚠️ Nenhuma tag encontrada para calcular estatísticas.**")
            data_results.append("💡 Especifique uma tag (ex: 'estatísticas de temperatura') ou selecione uma tag na interface.")

    # Pattern 3: List/search tags
    list_patterns = ['liste', 'listar', 'quais', 'mostre', 'disponíveis', 'todas as tags']

    if any(pattern in query_lower for pattern in list_patterns) and 'tags' in query_lower:
        # Extract search keyword
        search_query = ""
        for keyword in ['temperatura', 'pressão', 'velocidade', 'corrente', 'potência']:
            if keyword in query_lower:
                search_query = keyword
                break

        logger.info(f"🎯 PRE-EXECUTING: search_tags(query={search_query})")
        result = await toolkit.execute_tool("search_tags", {"query": search_query, "limit": 10})

        if result.success and result.data:
            # result.data can be a list directly or a dict with 'tags' key
            if isinstance(result.data, list):
                tags = result.data
            else:
                tags = result.data.get('tags', [])
            if tags:
                data_results.append(f"**Tags encontradas** ({len(tags)} resultados):")
                for tag in tags[:10]:
                    if isinstance(tag, dict):
                        tag_name = tag.get('name', tag.get('id', 'unknown'))
                        unit = tag.get('unit', '')
                    else:
                        tag_name = str(tag)
                        unit = ''
                    data_results.append(f"  - {tag_name} ({unit})")
            else:
                data_results.append("**Nenhuma tag encontrada**")

    # Pattern 4: Alarm queries (NEW - Applied to ALL equipment)
    alarm_patterns = [
        'alarme', 'alarm', 'alerta', 'alert',
        'problema', 'problem', 'crítico', 'critical',
        'falha', 'failure', 'erro', 'error',
        'atenção', 'atencao', 'warning', 'aviso'
    ]

    # Frequency patterns - when present, skip Pattern 4 (active alarms) and use Pattern 5 (frequency analysis)
    frequency_patterns = ['frequência', 'frequency', 'chattering', 'flood', 'taxa', 'quantas vezes', 'how often', 'histórico', 'history', 'vezes', 'ocorrências', 'ocorrencias']
    is_frequency_query = any(pattern in query_lower for pattern in frequency_patterns)

    if any(pattern in query_lower for pattern in alarm_patterns) and not is_frequency_query:
        logger.info(f"🚨 PRE-EXECUTE: Alarm query detected: '{query}'")

        # Detect severity filter from query
        severity = None
        if 'crítico' in query_lower or 'critical' in query_lower:
            severity = 'critical'
        elif 'alto' in query_lower or 'high' in query_lower or 'alta' in query_lower:
            severity = 'high'
        elif 'médio' in query_lower or 'medio' in query_lower or 'medium' in query_lower:
            severity = 'medium'
        elif 'baixo' in query_lower or 'low' in query_lower or 'baixa' in query_lower:
            severity = 'low'

        # Detect equipment filter using fuzzy matching
        equipment_filter = None
        if available_tags:
            # Try to extract equipment name from query
            # Common patterns: "alarmes do EL01", "problemas no SILO02", "alertas da correia 1"
            equipment_keywords = []
            for word in query_lower.split():
                clean_word = word.strip('.,?!;:')
                # Skip common words
                if clean_word not in ['qual', 'quais', 'a', 'o', 'do', 'da', 'no', 'na', 'de', 'tem', 'há',
                                       'existe', 'existem', 'mostre', 'liste', 'alarme', 'alarmes',
                                       'alerta', 'alertas', 'problema', 'problemas']:
                    if len(clean_word) >= 3:  # Minimum 3 characters
                        equipment_keywords.append(clean_word)

            logger.debug(f"🔍 Equipment keywords extracted: {equipment_keywords}")

            # Try to match equipment name with tags
            if equipment_keywords:
                # Get unique equipment prefixes from available tags
                equipment_names = set()
                for tag in available_tags:
                    tag_name = tag.get('name', '')
                    prefix = tag_name.split('_')[0] if '_' in tag_name else tag_name
                    equipment_names.add(prefix.lower())

                logger.debug(f"🏭 Available equipment: {sorted(equipment_names)}")

                # Fuzzy match equipment name
                for keyword in equipment_keywords:
                    for eq_name in equipment_names:
                        # Fuzzy match: keyword chars in order in equipment name
                        if len(keyword) >= 2:
                            keyword_chars = [c for c in keyword if c.isalnum()]
                            eq_chars = [c for c in eq_name if c.isalnum()]

                            # Check if characters appear in order
                            idx = 0
                            match = True
                            for char in keyword_chars:
                                found_idx = -1
                                for i in range(idx, len(eq_chars)):
                                    if eq_chars[i] == char:
                                        found_idx = i
                                        break
                                if found_idx == -1:
                                    match = False
                                    break
                                idx = found_idx + 1

                            if match:
                                equipment_filter = eq_name.upper()
                                logger.debug(f"✅ Matched equipment: '{keyword}' → {equipment_filter}")
                                break
                    if equipment_filter:
                        break

        # Execute get_active_alarms tool
        alarm_args = {"limit": 100}
        if severity:
            alarm_args["severity"] = severity
            logger.info(f"🎯 PRE-EXECUTING: get_active_alarms(severity={severity}, limit=100)")
        else:
            logger.info(f"🎯 PRE-EXECUTING: get_active_alarms(limit=100)")

        result = await toolkit.execute_tool("get_active_alarms", alarm_args)

        if result.success and result.data:
            alarms = result.data.get('alarms', [])
            total_active = result.data.get('total_active_alarms', len(alarms))

            # Filter by equipment if detected
            if equipment_filter and alarms:
                logger.debug(f"🔍 Filtering alarms by equipment: {equipment_filter}")
                filtered_alarms = []
                for alarm in alarms:
                    alarm_name = alarm.get('alarm_name', '').upper()
                    tag_id = alarm.get('tag_id', '')
                    # Check if alarm is related to the equipment
                    if equipment_filter in alarm_name or (tag_id and equipment_filter in str(tag_id).upper()):
                        filtered_alarms.append(alarm)

                logger.debug(f"📊 Filtered {len(filtered_alarms)} alarms from {len(alarms)} total")
                alarms = filtered_alarms
                total_active = len(filtered_alarms)  # Update count for filtered results

            if alarms:
                alarm_count = len(alarms)
                severity_filter_text = f" ({severity.upper()})" if severity else ""
                equipment_filter_text = f" do equipamento {equipment_filter}" if equipment_filter else ""

                data_results.append(f"**🚨 Alarmes Ativos{severity_filter_text}{equipment_filter_text}**: {total_active} alarme(s)")
                data_results.append("")

                for i, alarm in enumerate(alarms[:10], 1):  # Show max 10 alarms
                    alarm_name = alarm.get('alarm_name', 'Alarme desconhecido')
                    severity_level = alarm.get('severity', 'N/A')
                    trigger_time = alarm.get('trigger_timestamp', 'N/A')
                    trigger_value = alarm.get('trigger_value', 'N/A')

                    # Format severity with emoji
                    severity_emoji = {
                        'CRITICAL': '🔴',
                        'HIGH': '🟠',
                        'MEDIUM': '🟡',
                        'LOW': '🟢'
                    }.get(severity_level, '⚪')

                    data_results.append(f"{i}. {severity_emoji} **{alarm_name}**")
                    data_results.append(f"   - Severidade: {severity_level}")
                    data_results.append(f"   - Valor: {trigger_value}")
                    data_results.append(f"   - Desde: {trigger_time}")
                    data_results.append("")

                if alarm_count > 10:
                    data_results.append(f"_... e mais {alarm_count - 10} alarme(s)_")
            else:
                filter_desc = ""
                if severity:
                    filter_desc += f" de severidade {severity.upper()}"
                if equipment_filter:
                    filter_desc += f" no equipamento {equipment_filter}"
                data_results.append(f"✅ **Nenhum alarme ativo{filter_desc}**")
        else:
            data_results.append("❌ **Erro ao buscar alarmes ativos**")

    # Pattern 5: Alarm frequency analysis queries (NEW)
    # Uses is_frequency_query already defined above

    logger.debug(f"🔍 DEBUG: is_frequency_query={is_frequency_query}, alarm_pattern_match={any(pattern in query_lower for pattern in alarm_patterns)}")

    if is_frequency_query and any(pattern in query_lower for pattern in alarm_patterns):
        logger.debug(f"📊 PRE-EXECUTE: Alarm frequency analysis detected: '{query}'")

        # Detect specific alarm name filter from query (e.g., "LOAD PCT", "LOAD_PCT")
        alarm_name_filter = None
        # Common alarm name patterns to extract
        import re

        # Multiple patterns to try (in order of specificity)
        alarm_patterns = [
            # "alarme de LOAD PCT aparece/ocorre"
            r'alarme\s+(?:de\s+)?([A-Za-z0-9_\s]+?)(?:\s+aparece|\s+ocorre)',
            # "alarme LOAD PCT" or "alarme de LOAD PCT" followed by various endings
            r'alarme\s+(?:de\s+)?([A-Za-z][A-Za-z0-9_\s]{2,20})(?:\s+nos|\s+nas|\s+no|\s+na|\s+em|\s+durante|\?|$)',
            # "frequência do alarme LOAD_PCT"
            r'frequ[êe]ncia\s+(?:do\s+|da\s+)?alarme\s+([A-Za-z][A-Za-z0-9_\s]{2,20})',
            # Direct alarm name pattern like "LOAD_PCT" or "LOAD PCT"
            r'\b(LOAD[_\s]?PCT[_\s]?[A-Za-z0-9_]*)\b',
            # Any word_word pattern that looks like an alarm name
            r'\b([A-Z][A-Z0-9]*[_][A-Z0-9_]+)\b',
        ]

        for pattern in alarm_patterns:
            alarm_name_match = re.search(pattern, query, re.IGNORECASE)
            if alarm_name_match:
                alarm_name_filter = alarm_name_match.group(1).strip().upper().replace(' ', '_')
                # Clean up trailing words like "NOS" or "NAS"
                alarm_name_filter = re.sub(r'[_]?(NOS|NAS|NO|NA|EM|DURANTE)$', '', alarm_name_filter)
                if len(alarm_name_filter) >= 4:  # Minimum 4 chars for valid alarm name
                    logger.debug(f"🔍 Detected alarm name filter: {alarm_name_filter} (pattern: {pattern[:30]}...)")
                    break
                else:
                    alarm_name_filter = None

        # Detect equipment filter
        equipment_filter = None
        if available_tags:
            equipment_keywords = []
            for word in query_lower.split():
                clean_word = word.strip('.,?!;:')
                if clean_word not in ['qual', 'quais', 'a', 'o', 'do', 'da', 'no', 'na', 'frequência', 'alarme', 'alarmes', 'quantas', 'vezes', 'aparece', 'ocorre']:
                    if len(clean_word) >= 3:
                        equipment_keywords.append(clean_word)

            if equipment_keywords:
                equipment_names = set(tag.get('name', '').split('_')[0] for tag in available_tags if '_' in tag.get('name', ''))
                for keyword in equipment_keywords:
                    for eq_name in equipment_names:
                        if all(c in eq_name.lower() for c in keyword):
                            equipment_filter = eq_name.upper()
                            break
                    if equipment_filter:
                        break

        # Execute frequency analysis
        logger.debug(f"🔧 PRE-EXECUTE: Calling analyze_alarm_frequency with equipment_filter={equipment_filter}, alarm_name_filter={alarm_name_filter}")
        result = await toolkit.execute_tool("analyze_alarm_frequency", {
            "duration": "7d",  # Use 7 days for better frequency analysis
            "equipment_filter": equipment_filter,
            "alarm_name_filter": alarm_name_filter
        })
        logger.debug(f"🔧 PRE-EXECUTE: analyze_alarm_frequency result.success={result.success}, has_data={bool(result.data)}, data_type={type(result.data)}, data_keys={result.data.keys() if isinstance(result.data, dict) else 'N/A'}")

        if result.success and result.data:
            freq_data = result.data
            summary = freq_data.get('summary', {})
            top_alarms = freq_data.get('top_frequent_alarms', [])[:10]
            chattering = freq_data.get('chattering_alarms', [])
            insights = freq_data.get('insights', [])

            # Filter by alarm name if specified
            if alarm_name_filter and top_alarms:
                filtered_alarms = [a for a in top_alarms if alarm_name_filter.replace('_', '') in a.get('alarm_name', '').upper().replace('_', '').replace(' ', '')]
                if filtered_alarms:
                    top_alarms = filtered_alarms
                    # Calculate specific count
                    specific_count = sum(a.get('event_count', 0) for a in filtered_alarms)
                    data_results.append(f"**📊 Frequência do Alarme '{alarm_name_filter}' (últimos 7 dias)**")
                    data_results.append("")
                    data_results.append(f"🔢 **Total de ocorrências: {specific_count} vezes**")
                    data_results.append("")
                else:
                    data_results.append(f"**📊 Análise de Frequência de Alarmes (últimos 7 dias)**")
                    data_results.append("")
                    data_results.append(f"⚠️ Alarme '{alarm_name_filter}' não encontrado no histórico.")
                    data_results.append("")
            else:
                data_results.append(f"**📊 Análise de Frequência de Alarmes (últimos 7 dias)**")
                data_results.append("")
                data_results.append(f"- Total de eventos: {summary.get('total_alarm_events', 0)}")
                data_results.append(f"- Alarmes/hora: {summary.get('alarms_per_hour', 0):.1f}")
                data_results.append(f"- Alarmes únicos: {summary.get('unique_alarms', 0)}")
                data_results.append("")

            if top_alarms:
                data_results.append("**🔝 Alarmes Mais Frequentes:**")
                for alarm in top_alarms:
                    data_results.append(f"  - {alarm['alarm_name']}: {alarm['event_count']} eventos ({alarm.get('percentage', 0)}%)")
                data_results.append("")

            if chattering:
                data_results.append(f"**🔄 Alarmes Chattering Detectados:** {len(chattering)}")
                for alarm in chattering[:3]:
                    data_results.append(f"  - {alarm['alarm_name']}: {alarm['event_count']} eventos, intervalo médio {alarm.get('avg_interval_minutes', 0):.1f} min")
                data_results.append("")

            if insights:
                data_results.append("**💡 Insights:**")
                for insight in insights:
                    data_results.append(f"  {insight}")
        else:
            data_results.append("❌ **Erro ao analisar frequência de alarmes**")

    # Pattern 6: Histogram/distribution queries (NEW)
    histogram_patterns = ['histograma', 'histogram', 'distribuição', 'distribution', 'faixa', 'range']

    if any(pattern in query_lower for pattern in histogram_patterns):
        logger.debug(f"📊 PRE-EXECUTE: Histogram query detected: '{query}'")

        # Try to find tag from query
        matched_tag = find_best_matching_tag(query, available_tags) if available_tags else None

        if matched_tag:
            tag_id = str(matched_tag.get('id'))
            result = await toolkit.execute_tool("generate_data_histogram", {
                "tag_id": tag_id,
                "duration": "24h",
                "bins": 10
            })

            if result.success and result.data:
                hist_data = result.data
                histogram = hist_data.get('histogram', [])
                stats = hist_data.get('statistics', {})
                insights = hist_data.get('insights', [])

                data_results.append(f"**📊 Histograma: {matched_tag.get('name')}**")
                data_results.append("")
                data_results.append(f"- Total de amostras: {hist_data.get('total_samples', 0)}")
                data_results.append(f"- Média: {stats.get('mean', 0):.2f}")
                data_results.append(f"- Desvio padrão: {stats.get('stddev', 0):.2f}")
                data_results.append("")

                data_results.append("**Distribuição:**")
                for bin_data in histogram[:5]:  # Show top 5 bins
                    data_results.append(f"  {bin_data['range_start']:.1f} - {bin_data['range_end']:.1f}: {bin_data['count']} ({bin_data['percentage']}%)")
                data_results.append("")

                if insights:
                    data_results.append("**💡 Insights:**")
                    for insight in insights:
                        data_results.append(f"  {insight}")

    # Pattern 7: Trend detection queries (NEW)
    trend_patterns = ['tendência', 'trend', 'crescendo', 'diminuindo', 'increasing', 'decreasing', 'subindo', 'caindo']

    if any(pattern in query_lower for pattern in trend_patterns):
        logger.debug(f"📈 PRE-EXECUTE: Trend analysis detected: '{query}'")

        matched_tag = find_best_matching_tag(query, available_tags) if available_tags else None

        if matched_tag:
            tag_id = str(matched_tag.get('id'))
            result = await toolkit.execute_tool("detect_trends", {
                "tag_id": tag_id,
                "duration": "24h",
                "sensitivity": "medium"
            })

            if result.success and result.data:
                trend_data = result.data
                insights = trend_data.get('insights', [])

                data_results.append(f"**📈 Análise de Tendência: {matched_tag.get('name')}**")
                data_results.append("")
                data_results.append(f"- {trend_data.get('trend_description', '')}")
                data_results.append(f"- Valor inicial: {trend_data.get('start_value', 0):.2f}")
                data_results.append(f"- Valor final: {trend_data.get('end_value', 0):.2f}")
                data_results.append(f"- Variação: {trend_data.get('change', 0):.2f} ({trend_data.get('change_percentage', 0):.1f}%)")
                data_results.append(f"- Confiança (R²): {trend_data.get('r_squared', 0):.3f}")
                data_results.append("")

                if insights:
                    data_results.append("**💡 Insights:**")
                    for insight in insights:
                        data_results.append(f"  {insight}")

    # Pattern 8: Insights/recommendations queries (NEW)
    insight_patterns = ['insight', 'insights', 'análise', 'analysis', 'recomendação', 'recommendation', 'resumo', 'summary']

    if any(pattern in query_lower for pattern in insight_patterns):
        logger.debug(f"💡 PRE-EXECUTE: Insights generation detected: '{query}'")

        # Determine scope
        scope = "system"
        if 'alarme' in query_lower or 'alarm' in query_lower:
            scope = "alarms"

        result = await toolkit.execute_tool("generate_insights", {
            "scope": scope,
            "duration": "24h"
        })

        if result.success and result.data:
            insight_data = result.data
            insights = insight_data.get('insights', [])
            alerts = insight_data.get('alerts', [])
            recommendations = insight_data.get('recommendations', [])

            data_results.append(f"**💡 Insights do Sistema**")
            data_results.append("")

            if insights:
                data_results.append("**Principais Observações:**")
                for insight in insights:
                    data_results.append(f"  {insight}")
                data_results.append("")

            if alerts:
                data_results.append(f"**⚠️ Alertas ({len(alerts)}):**")
                for alert in alerts[:5]:
                    data_results.append(f"  - [{alert.get('severity', 'info').upper()}] {alert.get('message', '')}")
                    if alert.get('action'):
                        data_results.append(f"    → {alert['action']}")
                data_results.append("")

            if recommendations:
                data_results.append("**📋 Recomendações:**")
                for rec in recommendations:
                    data_results.append(f"  {rec}")

    # Pattern 9: Executive Dashboard queries (NEW)
    # Also includes OEE, eficiência, disponibilidade, performance queries
    executive_patterns = [
        'executivo', 'executive', 'visão geral', 'overview', 'kpi', 'kpis',
        'dashboard', 'gerencial', 'diretoria', 'indicadores', 'resumo executivo',
        'oee', 'eficiência', 'eficiencia', 'disponibilidade', 'availability',
        'performance', 'qualidade', 'quality', 'mtbf', 'mttr'
    ]

    if any(pattern in query_lower for pattern in executive_patterns):
        logger.info(f"📊 PRE-EXECUTE: Executive dashboard query detected: '{query}'")

        # Detect time range from query
        time_range = "24h"
        if "7 dias" in query_lower or "semana" in query_lower or "7d" in query_lower:
            time_range = "7d"
        elif "30 dias" in query_lower or "mês" in query_lower or "30d" in query_lower:
            time_range = "30d"

        result = await toolkit.execute_tool("get_executive_overview", {"time_range": time_range})

        if result.success and result.data:
            exec_data = result.data
            kpis = exec_data.get('kpis', {})
            alarms = exec_data.get('alarms', {})
            financial = exec_data.get('financial_summary', {})

            data_results.append(f"**📊 Dashboard Executivo ({time_range})**")
            data_results.append("")

            # KPIs
            data_results.append("**📈 KPIs Principais:**")
            oee = kpis.get('oee', {})
            avail = kpis.get('availability', {})
            perf = kpis.get('performance', {})
            qual = kpis.get('quality', {})

            data_results.append(f"  - OEE: {oee.get('value', 0):.1f}% (Meta: {oee.get('target', 85)}%) {_get_trend_icon(oee.get('trend'))}")
            data_results.append(f"  - Disponibilidade: {avail.get('value', 0):.1f}% (Meta: {avail.get('target', 95)}%) {_get_trend_icon(avail.get('trend'))}")
            data_results.append(f"  - Performance: {perf.get('value', 0):.1f}% (Meta: {perf.get('target', 90)}%) {_get_trend_icon(perf.get('trend'))}")
            data_results.append(f"  - Qualidade: {qual.get('value', 0):.1f}% (Meta: {qual.get('target', 99)}%) {_get_trend_icon(qual.get('trend'))}")
            data_results.append("")

            # Alarms
            data_results.append("**🚨 Status de Alarmes:**")
            data_results.append(f"  - Total Ativos: {alarms.get('total_active', 0)}")
            by_sev = alarms.get('by_severity', {})
            data_results.append(f"  - Críticos: {by_sev.get('critical', 0)} | Alto: {by_sev.get('high', 0)} | Médio: {by_sev.get('medium', 0)} | Baixo: {by_sev.get('low', 0)}")
            data_results.append(f"  - MTTR: {alarms.get('mttr_hours', 0):.1f} horas")
            data_results.append("")

            # Financial
            if financial:
                data_results.append("**💰 Resumo Financeiro:**")
                data_results.append(f"  - Economia Estimada: R$ {financial.get('estimated_savings_today', 0):,.2f}")
                data_results.append(f"  - Custo Evitado: R$ {financial.get('downtime_cost_avoided', 0):,.2f}")
                data_results.append(f"  - Projeção Mensal: R$ {financial.get('projected_monthly_savings', 0):,.2f}")
                data_results.append("")

            # Insights
            insights = exec_data.get('insights', [])
            if insights:
                data_results.append("**💡 Insights:**")
                for insight in insights[:3]:
                    if isinstance(insight, dict):
                        data_results.append(f"  - [{insight.get('type', 'info').upper()}] {insight.get('title', '')}: {insight.get('description', '')}")
                    else:
                        data_results.append(f"  - {insight}")

    # Pattern 10: Energy metrics queries (NEW)
    energy_patterns = ['energia', 'energy', 'consumo', 'kwh', 'demanda', 'fator de potência', 'conta de luz']

    if any(pattern in query_lower for pattern in energy_patterns):
        logger.info(f"⚡ PRE-EXECUTE: Energy metrics query detected: '{query}'")

        time_range = "24h"
        if "7 dias" in query_lower or "semana" in query_lower:
            time_range = "7d"
        elif "30 dias" in query_lower or "mês" in query_lower:
            time_range = "30d"

        result = await toolkit.execute_tool("get_energy_metrics", {"time_range": time_range})

        if result.success and result.data:
            energy = result.data
            current = energy.get('current', {})
            period = energy.get('period', {})
            forecast = energy.get('forecast', {})
            bill = energy.get('bill_forecast', {})

            data_results.append(f"**⚡ Métricas de Energia ({time_range})**")
            data_results.append("")
            data_results.append("**Consumo Atual:**")
            data_results.append(f"  - Consumo: {current.get('consumption_kwh', 0):,.0f} kWh")
            data_results.append(f"  - Demanda: {current.get('demand_kw', 0):,.0f} kW")
            data_results.append(f"  - Fator de Potência: {current.get('power_factor', 0):.2f}")
            data_results.append("")
            data_results.append("**Previsão de Conta:**")
            data_results.append(f"  - Custo Energia: R$ {bill.get('energy_cost', 0):,.2f}")
            data_results.append(f"  - Custo Demanda: R$ {bill.get('demand_cost', 0):,.2f}")
            data_results.append(f"  - Total Estimado: R$ {bill.get('total_estimate', 0):,.2f}")

    # Pattern 11: Production metrics queries (NEW)
    production_patterns = ['produção', 'production', 'throughput', 'ton/h', 'capacidade', 'meta de produção']

    if any(pattern in query_lower for pattern in production_patterns):
        logger.info(f"🏭 PRE-EXECUTE: Production metrics query detected: '{query}'")

        time_range = "24h"
        if "7 dias" in query_lower or "semana" in query_lower:
            time_range = "7d"

        result = await toolkit.execute_tool("get_production_metrics", {"time_range": time_range})

        if result.success and result.data:
            prod = result.data
            current = prod.get('current', {})
            target = prod.get('target', {})
            capacity = prod.get('capacity', {})

            data_results.append(f"**🏭 Métricas de Produção ({time_range})**")
            data_results.append("")
            data_results.append("**Produção Atual:**")
            data_results.append(f"  - Throughput: {current.get('throughput_ton_hour', 0):.1f} ton/h")
            data_results.append(f"  - Utilização: {current.get('utilization_percent', 0):.1f}%")
            data_results.append(f"  - Tempo de Ciclo: {current.get('cycle_time_minutes', 0):.1f} min")
            data_results.append("")
            data_results.append("**Metas:**")
            data_results.append(f"  - Meta Diária: {target.get('production_target_tons', 0):,.0f} ton")
            data_results.append(f"  - Atingimento: {target.get('achievement_percent', 0):.1f}%")
            data_results.append(f"  - Gap: {target.get('gap_tons', 0):+,.0f} ton")

    # Pattern 12: Pareto analysis queries (NEW)
    pareto_patterns = ['pareto', 'ranking', 'top alarmes', 'principais alarmes', '80/20']

    if any(pattern in query_lower for pattern in pareto_patterns):
        logger.info(f"📊 PRE-EXECUTE: Pareto analysis query detected: '{query}'")

        result = await toolkit.execute_tool("get_alarm_pareto", {"time_range": "24h", "limit": 10})

        if result.success and result.data:
            pareto = result.data
            summary = pareto.get('summary', {})
            pareto_list = pareto.get('pareto', [])

            data_results.append("**📊 Análise de Pareto - Alarmes (24h)**")
            data_results.append("")
            data_results.append(f"- Total de Alarmes: {summary.get('total_alarms', 0)}")
            data_results.append(f"- Tipos Únicos: {summary.get('unique_types', 0)}")
            data_results.append(f"- Custo Estimado Total: R$ {summary.get('total_estimated_cost', 0):,.2f}")
            data_results.append(f"- {summary.get('pareto_efficiency', '')}")
            data_results.append("")
            data_results.append("**Top Alarmes:**")
            for item in pareto_list[:5]:
                data_results.append(f"  {item['rank']}. {item['alarm_type']}: {item['count']}x ({item['cumulative_percent']:.1f}% acum.)")

    # Pattern 13: Financial summary queries (NEW)
    financial_patterns = ['financeiro', 'financial', 'economia', 'savings', 'roi', 'custo evitado']

    if any(pattern in query_lower for pattern in financial_patterns):
        logger.info(f"💰 PRE-EXECUTE: Financial summary query detected: '{query}'")

        result = await toolkit.execute_tool("get_financial_summary", {"time_range": "24h"})

        if result.success and result.data:
            fin = result.data
            roi = fin.get('roi_metrics', {})
            breakdown = fin.get('cost_breakdown', {})

            data_results.append("**💰 Resumo Financeiro (24h)**")
            data_results.append("")
            data_results.append(f"- Economia Estimada: R$ {fin.get('estimated_savings_today', 0):,.2f}")
            data_results.append(f"- Custo Evitado: R$ {fin.get('downtime_cost_avoided', 0):,.2f}")
            data_results.append(f"- Melhoria de Eficiência: {fin.get('efficiency_improvement', 0):.1f}%")
            data_results.append(f"- Projeção Mensal: R$ {fin.get('projected_monthly_savings', 0):,.2f}")
            data_results.append("")
            data_results.append("**Detalhamento:**")
            data_results.append(f"  - Energia: R$ {breakdown.get('energy_savings', 0):,.2f}")
            data_results.append(f"  - Manutenção: R$ {breakdown.get('maintenance_savings', 0):,.2f}")
            data_results.append(f"  - Produtividade: R$ {breakdown.get('productivity_gains', 0):,.2f}")
            data_results.append("")
            data_results.append("**ROI:**")
            data_results.append(f"  - ROI Mensal: {roi.get('monthly_roi_percent', 0):.1f}%")
            data_results.append(f"  - Payback: {roi.get('payback_months', 0):.1f} meses")

    # Pattern 14: Maintenance/Predictive queries (NEW)
    maintenance_patterns = ['manutenção', 'maintenance', 'preditiva', 'predictive', 'health', 'saúde do equipamento', 'falha', 'failure prediction']

    if any(pattern in query_lower for pattern in maintenance_patterns):
        logger.info(f"🔧 PRE-EXECUTE: Maintenance dashboard query detected: '{query}'")

        result = await toolkit.execute_tool("get_maintenance_dashboard", {"include_predictions": True})

        if result.success and result.data:
            maint = result.data
            summary = maint.get('summary', {})
            at_risk = maint.get('at_risk', [])
            roi = maint.get('roi', {})

            data_results.append("**🔧 Dashboard de Manutenção Preditiva**")
            data_results.append("")
            data_results.append(f"- Total de Equipamentos: {summary.get('total_equipment', 0)}")
            data_results.append(f"- Em Risco: {summary.get('at_risk_count', 0)}")
            data_results.append(f"- Health Score Médio: {summary.get('average_health_score', 0):.1f}%")
            data_results.append(f"- Manutenções em 7d: {summary.get('maintenance_scheduled_7d', 0)}")
            data_results.append("")

            if at_risk:
                data_results.append("**⚠️ Equipamentos em Risco:**")
                for eq in at_risk[:3]:
                    data_results.append(f"  - {eq['equipment_name']}: Health {eq['health_score']}%, Prob. Falha {eq['failure_probability']:.1f}%")
                    data_results.append(f"    → {eq['recommended_action']}")
                data_results.append("")

            data_results.append("**💰 ROI da Manutenção Preditiva:**")
            data_results.append(f"  - Falhas Prevenidas/Mês: {roi.get('failures_prevented_month', 0)}")
            data_results.append(f"  - Economia Mensal: R$ {roi.get('monthly_savings', 0):,.2f}")
            data_results.append(f"  - ROI: {roi.get('roi_percent', 0):.1f}%")

    # Pattern 15: Report generation queries (NEW)
    report_patterns = ['relatório', 'report', 'pdf', 'exportar', 'gerar relatório', 'generate report']

    if any(pattern in query_lower for pattern in report_patterns):
        logger.info(f"📄 PRE-EXECUTE: Report generation query detected: '{query}'")

        time_range = "24h"
        if "7 dias" in query_lower or "semana" in query_lower:
            time_range = "7d"
        elif "30 dias" in query_lower or "mês" in query_lower:
            time_range = "30d"

        result = await toolkit.execute_tool("generate_executive_report", {
            "time_range": time_range,
            "include_charts": True
        })

        if result.success and result.data:
            report = result.data
            if report.get('success'):
                info = report.get('report_info', {})
                data_results.append("**📄 Relatório Executivo Gerado**")
                data_results.append("")
                data_results.append(f"- Título: {info.get('title', 'Relatório Executivo')}")
                data_results.append(f"- Período: {info.get('time_range', '24h')}")
                data_results.append(f"- Gerado em: {info.get('generated_at', 'N/A')}")
                data_results.append(f"- Arquivo: {info.get('filename', 'relatorio.pdf')}")
                data_results.append("")
                data_results.append(f"**📥 Download:** {report.get('download_url', '')}")
                data_results.append("")
                data_results.append(report.get('instructions', ''))
            else:
                data_results.append(f"**❌ Erro ao gerar relatório:** {report.get('error', 'Erro desconhecido')}")
                data_results.append(f"💡 {report.get('suggestion', '')}")

    # Pattern 16: Asset Tree queries (NEW)
    asset_patterns = [
        'asset', 'ativo', 'ativos', 'hierarquia', 'hierarchy',
        'equipamento', 'equipamentos', 'planta', 'área', 'áreas',
        'elemento', 'elementos', 'estrutura', 'organização'
    ]

    if any(pattern in query_lower for pattern in asset_patterns):
        logger.debug(f"🏭 PRE-EXECUTE: Asset Tree query detected: '{query}'")

        # Check if asking for statistics/count
        if any(word in query_lower for word in ['quanto', 'quantos', 'total', 'count', 'estatística']):
            result = await toolkit.execute_tool("get_asset_statistics", {})

            if result.success and result.data:
                stats = result.data.get('statistics', result.data)
                summary = result.data.get('summary', '')

                data_results.append("**🏭 Estatísticas do Asset Tree**")
                data_results.append("")
                data_results.append(f"- Total de Elementos: {stats.get('total_elements', 0)}")
                data_results.append(f"- Total de Atributos: {stats.get('total_attributes', 0)}")
                data_results.append(f"- Templates: {stats.get('total_templates', 0)}")
                data_results.append("")

                by_type = stats.get('elements_by_type', {})
                if by_type:
                    data_results.append("**Por Tipo:**")
                    for etype, count in by_type.items():
                        data_results.append(f"  - {etype}: {count}")

        # Check if asking for hierarchy/structure
        elif any(word in query_lower for word in ['hierarquia', 'hierarchy', 'estrutura', 'árvore', 'tree', 'organização']):
            result = await toolkit.execute_tool("get_asset_hierarchy", {})

            if result.success and result.data:
                hierarchy = result.data.get('hierarchy', [])
                summary = result.data.get('summary', '')

                data_results.append("**🏭 Hierarquia de Ativos**")
                data_results.append("")
                data_results.append(f"Total de elementos raiz: {result.data.get('total_root_elements', len(hierarchy))}")
                data_results.append("")
                data_results.append(summary if summary else "Use a interface visual para ver a estrutura completa.")

        # Check if searching for specific equipment
        elif any(word in query_lower for word in ['encontre', 'busque', 'procure', 'find', 'search', 'onde']):
            logger.debug(f"🔍 PRE-EXECUTE: Asset search pattern detected")
            # Extract search query
            search_keywords = []
            for word in query_lower.split():
                if word not in ['encontre', 'busque', 'procure', 'find', 'search', 'onde', 'está', 'fica', 'o', 'a', 'os', 'as', 'equipamento', 'equipamentos', 'de', 'do', 'da']:
                    if len(word) >= 3:
                        search_keywords.append(word)

            search_query = ' '.join(search_keywords[:3]) if search_keywords else 'silo'
            logger.debug(f"🔍 PRE-EXECUTE: Searching assets with query='{search_query}'")

            result = await toolkit.execute_tool("search_assets", {"query": search_query, "limit": 10})
            logger.debug(f"🔍 PRE-EXECUTE: Search result success={result.success}, data={result.data}")

            if result.success and result.data:
                # Handle both list and dict responses
                if isinstance(result.data, list):
                    elements = result.data
                else:
                    elements = result.data.get('elements', [])

                total = len(elements) if isinstance(result.data, list) else result.data.get('total', len(elements))

                data_results.append(f"**🔍 Busca de Ativos: '{search_query}'**")
                data_results.append("")
                data_results.append(f"Encontrados: {total} resultados")

                if elements:
                    data_results.append("")
                    for elem in elements[:5]:
                        name = elem.get('name', 'Unknown') if isinstance(elem, dict) else str(elem)
                        elem_type = elem.get('element_type', '') if isinstance(elem, dict) else ''
                        path = elem.get('path', '') if isinstance(elem, dict) else ''
                        data_results.append(f"- **{name}** ({elem_type}): {path}")
                else:
                    data_results.append("")
                    data_results.append("Nenhum resultado encontrado.")

        # Default: show statistics
        else:
            result = await toolkit.execute_tool("get_asset_statistics", {})

            if result.success and result.data:
                stats = result.data.get('statistics', result.data)

                data_results.append("**🏭 Visão Geral do Asset Tree**")
                data_results.append("")
                data_results.append(f"- Total de Elementos: {stats.get('total_elements', 0)}")
                data_results.append(f"- Total de Atributos: {stats.get('total_attributes', 0)}")
                data_results.append(f"- Templates: {stats.get('total_templates', 0)}")

                by_type = stats.get('elements_by_type', {})
                if by_type:
                    data_results.append("")
                    data_results.append("**Por Tipo:**")
                    for etype, count in by_type.items():
                        data_results.append(f"  - {etype}: {count}")

    if data_results:
        return "\n".join(data_results)

    return None


async def call_ollama(messages: List[Dict[str, str]], max_iterations: int = 3) -> str:
    """
    Call Ollama API for chat completion with tool support.
    Optimized for MAXIMUM SPEED with GPU - Target: 3-8 seconds.
    Protected by circuit breaker to prevent cascade failures.
    """
    # Check circuit breaker BEFORE attempting Ollama call
    if ollama_circuit_breaker.is_open:
        logger.warning(
            f"⚡ Circuit breaker OPEN - Ollama unavailable "
            f"(will retry after {ollama_circuit_breaker.config.timeout}s)"
        )
        raise HTTPException(
            status_code=503,
            detail="AI service temporarily unavailable due to high load. Please try again in a moment."
        )

    async def _ollama_request():
        """Inner function for circuit breaker wrapping"""
        logger.debug(f"🔍 DEBUG: Calling Ollama at {OLLAMA_BASE_URL}")
        # Increased timeout to 120s for first model load
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": MODEL_NAME,
                    "messages": messages,
                    "stream": False,
                    "keep_alive": "30m",  # Keep model in VRAM for 30 minutes (faster subsequent queries)
                    "options": {
                        "temperature": 0.05,  # Even more deterministic = faster
                        "top_p": 0.8,        # More focused sampling
                        "top_k": 20,         # Limit token choices = faster
                        "num_predict": 800,  # Increased for complete responses (was 500)
                        "num_ctx": 4096,     # Increased context for system prompt + data + response
                        "num_gpu": 99,       # Force full GPU usage
                        "num_thread": 4,     # Optimize CPU threads
                        "repeat_penalty": 1.1,  # Reduce repetition
                        "stop": ["</response>", "\n\n\n"],  # Early stopping
                    }
                }
            )
            logger.debug(f"🔍 DEBUG: Ollama response received - Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                return result["message"]["content"]
            else:
                raise Exception(f"Ollama API error: {response.text}")

    try:
        # Execute through circuit breaker (using async version for async function)
        result = await ollama_circuit_breaker.call_async(_ollama_request)
        return result
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Ollama. Make sure Ollama is running"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling Ollama: {str(e)}")


async def call_ollama_stream(messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
    """
    Call Ollama API with streaming enabled.
    Yields chunks of text as they are generated (SSE - Server-Sent Events).

    This provides real-time feedback to users, making 8s queries feel instant!
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": MODEL_NAME,
                    "messages": messages,
                    "stream": True,  # Enable streaming!
                    "keep_alive": "30m",
                    "options": {
                        "temperature": 0.05,
                        "top_p": 0.8,
                        "top_k": 20,
                        "num_predict": 600,  # Increased for complete streaming responses (was 300)
                        "num_ctx": 4096,     # Match non-streaming context (was 1536)
                        "num_gpu": 99,
                        "num_thread": 4,
                        "repeat_penalty": 1.1,
                        "stop": ["</response>", "\n\n\n"],
                    }
                }
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Ollama API error: {error_text.decode()}"
                    )

                # Stream chunks from Ollama
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                content = chunk["message"]["content"]
                                if content:  # Only yield non-empty chunks
                                    yield content

                            # Check if done
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to decode JSON chunk: {line}")
                            continue

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Ollama. Make sure Ollama is running"
        )
    except Exception as e:
        logger.error(f"Streaming error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error streaming from Ollama: {str(e)}")


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


async def chat_fallback_mode(
    request: DashboardAgentRequest,
    data_service: DataService,
    toolkit: AgentToolkit,
    db: AsyncSession
) -> DashboardAgentResponse:
    """
    Chatbot especializado em PCM/PCO e Ciência de Dados Industrial.
    Responde com expertise técnica e recomendações acionáveis.
    """
    message_lower = request.message.lower()
    logger.info(f"🤖 OptiFlow AI - Pergunta: '{request.message}'")
    
    # === CONSULTA DE ALARMES ===
    if any(word in message_lower for word in ['alarme', 'alarm', 'alerta', 'alert', 'principal', 'crítico', 'urgente', 'problema']):
        logger.info("🚨 Detectado: Consulta sobre ALARMES")
        try:
            # Buscar alarmes ativos
            alarms_result = await toolkit.execute_tool("get_active_alarms", {"limit": 100})

            if alarms_result.success and alarms_result.data:
                data = alarms_result.data
                alarms = data.get("alarms", [])
                total = data.get("total_active_alarms", len(alarms))
                
                # Agrupar por severidade
                by_severity = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
                for alarm in alarms:
                    severity = alarm.get("severity", "LOW").upper()  # Converter para maiúscula!
                    by_severity[severity].append(alarm)
                
                # Construir resposta como Analista PCM/PCO
                response = "## 📊 ANÁLISE PCM - Status de Alarmes\n\n"
                response += f"**Total de Alarmes Ativos**: {total}\n\n"
                
                if total == 0:
                    response += "### ✅ SITUAÇÃO NORMAL\n"
                    response += "Não há alarmes ativos no momento. Sistema operando dentro dos parâmetros normais.\n\n"
                    response += "**Recomendação**: Manter rotina de inspeção preventiva.\n"
                else:
                    response += "### 🎯 ANÁLISE POR SEVERIDADE\n\n"
                    
                    # CRÍTICO
                    if by_severity["CRITICAL"]:
                        response += f"#### 🔴 **CRÍTICO** - {len(by_severity['CRITICAL'])} alarmes (AÇÃO IMEDIATA)\n"
                        for i, alarm in enumerate(by_severity["CRITICAL"][:5], 1):
                            name = alarm.get("alarm_name", "Sem nome")
                            value = alarm.get("trigger_value")
                            value_str = f"{value:.2f}" if isinstance(value, (int, float)) else str(value)
                            response += f"{i}. **{name}**: Valor = {value_str}\n"
                        if len(by_severity["CRITICAL"]) > 5:
                            response += f"   ... e mais {len(by_severity['CRITICAL']) - 5} alarmes críticos\n"
                        response += "\n**Impacto**: Risco de parada não programada, perda de produção\n"
                        response += "**Ação PCM**: Intervenção imediata da equipe de manutenção\n\n"
                    
                    # ALTO
                    if by_severity["HIGH"]:
                        response += f"#### 🟠 **ALTO** - {len(by_severity['HIGH'])} alarmes (ATENÇÃO)\n"
                        for i, alarm in enumerate(by_severity["HIGH"][:3], 1):
                            name = alarm.get("alarm_name", "Sem nome")
                            value = alarm.get("trigger_value")
                            value_str = f"{value:.2f}" if isinstance(value, (int, float)) else str(value)
                            response += f"{i}. **{name}**: Valor = {value_str}\n"
                        if len(by_severity["HIGH"]) > 3:
                            response += f"   ... e mais {len(by_severity['HIGH']) - 3} alarmes\n"
                        response += "\n**Ação PCO**: Monitoramento contínuo, preparar intervenção\n\n"
                    
                    # MÉDIO
                    if by_severity["MEDIUM"]:
                        response += f"#### � **MÉDIO** - {len(by_severity['MEDIUM'])} alarmes (PROGRAMAR)\n"
                        response += "**Ação PCM**: Incluir em próxima parada programada\n\n"
                    
                    # BAIXO
                    if by_severity["LOW"]:
                        response += f"#### 🔵 **BAIXO** - {len(by_severity['LOW'])} alarmes (MONITORAR)\n"
                        response += "**Ação**: Acompanhar evolução, sem urgência\n\n"
                    
                    # RECOMENDAÇÕES ESTRATÉGICAS
                    response += "### 💡 RECOMENDAÇÕES ESTRATÉGICAS\n"
                    critical_count = len(by_severity["CRITICAL"])
                    high_count = len(by_severity["HIGH"])
                    
                    if critical_count > 5:
                        response += "1. **URGENTE**: Alarme de processo detectado - convocar equipe de emergência\n"
                        response += "2. Avaliar necessidade de parada controlada\n"
                        response += "3. Acionar procedimento de contingência\n"
                    elif critical_count > 0:
                        response += "1. **ALTA PRIORIDADE**: Investigar alarmes críticos imediatamente\n"
                        response += "2. Preparar recursos para manutenção corretiva\n"
                    
                    if high_count > 10:
                        response += f"3. {high_count} alarmes de severidade ALTA indicam degradação múltipla\n"
                        response += "4. Revisar plano de manutenção preventiva\n"
                    
                    response += f"\n📈 **Métricas**: Taxa de alarmes = {total} ativos | Disponibilidade em risco\n"
                
                response += f"\n🔗 **Dashboard Completo**: http://localhost:3000/alarms\n"
                
                return DashboardAgentResponse(
                    response=response,
                    suggestions=[
                        "Qual a causa raiz dos alarmes críticos?",
                        "Mostrar histórico de alarmes dos últimos 7 dias",
                        "Análise de tendência de falhas",
                        "Calcular MTBF e MTTR dos equipamentos"
                    ]
                )
        except Exception as e:
            logger.error(f"❌ Erro ao consultar alarmes: {e}")
            import traceback
            traceback.print_exc()
            return DashboardAgentResponse(
                response="⚠️ Erro ao acessar sistema de alarmes. Verifique os logs do sistema ou acesse http://localhost:3000/alarms diretamente.",
                suggestions=["Status dos dispositivos", "Consultar tags ativos"]
            )
    
    # Device status queries
    if any(word in message_lower for word in ['dispositivo', 'device', 'online', 'offline', 'conectado']):
        try:
            # Get device count from database directly
            from sqlalchemy import select, func, case
            from ...models.device import Device
            
            result = await db.execute(
                select(
                    func.count(Device.id).label('total'),
                    func.sum(case((Device.status == 'CONNECTED', 1), else_=0)).label('online'),
                    func.sum(case((Device.status != 'CONNECTED', 1), else_=0)).label('offline')
                )
            )
            row = result.first()
            
            total = row.total or 0
            online = row.online or 0
            offline = row.offline or 0
            
            response = f"📊 **Status dos Dispositivos**\n\n"
            response += f"Total: {total} dispositivos\n"
            response += f"🟢 Online: {online}\n"
            response += f"🔴 Offline: {offline}\n\n"
            
            if online > 0:
                response += f"Ótimo! {online} dispositivo(s) estão operando normalmente."
            if offline > 0:
                response += f" {offline} dispositivo(s) precisam de atenção."
            
            return DashboardAgentResponse(
                response=response,
                suggestions=[
                    "Mostre-me os tags ativos",
                    "Quais alarmes estão ativos?",
                    "Crie um gráfico de temperatura"
                ]
            )
        except Exception as e:
            logger.error(f"Error getting device status: {e}")
    
    # Active tags queries
    if any(word in message_lower for word in ['tag', 'dados', 'sensores', 'sensor']):
        try:
            tags_result = await toolkit.execute_tool("get_active_tags", {})
            if tags_result.success and tags_result.data:
                tags_data = tags_result.data
                tags = tags_data.get("tags", [])
                count = tags_data.get("total_tags", len(tags))
                
                response = f"📡 **Tags Ativos**\n\n"
                response += f"Encontrei {count} tags com dados recentes:\n\n"
                
                for i, tag in enumerate(tags[:5], 1):
                    name = tag.get("name", tag.get("tag_id", "Unknown"))
                    value = tag.get("last_value", "N/A")
                    response += f"{i}. **{name}**: {value}\n"
                
                if count > 5:
                    response += f"\n... e mais {count - 5} tags."
                
                return DashboardAgentResponse(
                    response=response,
                    suggestions=[
                        "Crie um gráfico para TEST_COUNTER_PV",
                        "Mostre estatísticas dos sensores",
                        "Quais tags mudaram recentemente?"
                    ]
                )
        except Exception as e:
            logger.error(f"Error getting active tags: {e}")
            import traceback
            traceback.print_exc()
    
    # === SAUDAÇÃO ESPECIALIZADA ===
    if any(word in message_lower for word in ['olá', 'oi', 'hello', 'hi', 'bom dia', 'boa tarde', 'boa noite']):
        logger.info("� Detectado: SAUDAÇÃO")
        return DashboardAgentResponse(
            response="""## 👋 Bem-vindo ao OptiFlow AI Assistant

Sou seu **Analista PCM/PCO** e **Cientista de Dados** especializado em:

### 🔧 Planejamento e Controle de Manutenção (PCM)
- Análise de alarmes e diagnóstico de falhas
- Manutenção preditiva e preventiva
- Cálculo de KPIs: MTBF, MTTR, Disponibilidade

### ⚙️ Planejamento e Controle de Operações (PCO)
- Monitoramento de processo em tempo real
- Otimização operacional e eficiência
- Análise de OEE (Overall Equipment Effectiveness)

### 📊 Ciência de Dados Industrial
- Análise estatística de séries temporais
- Detecção de anomalias e padrões
- Correlação entre variáveis de processo

**Como posso ajudá-lo hoje?**""",
            suggestions=[
                "Quais são os principais alarmes?",
                "Análise de disponibilidade dos equipamentos",
                "Mostrar tendências de falhas",
                "Calcular OEE do último mês"
            ]
        )
    
    # === ANÁLISE DE PERFORMANCE/OEE ===
    if any(word in message_lower for word in ['oee', 'performance', 'eficiência', 'disponibilidade', 'mtbf', 'mttr', 'kpi']):
        logger.info("📊 Detectado: Consulta sobre PERFORMANCE/KPIs")
        return DashboardAgentResponse(
            response="""## 📊 Análise de Performance Industrial

### Indicadores Disponíveis:
- **OEE (Overall Equipment Effectiveness)**: Disponibilidade × Performance × Qualidade
- **MTBF (Mean Time Between Failures)**: Tempo médio entre falhas
- **MTTR (Mean Time To Repair)**: Tempo médio de reparo
- **Disponibilidade**: % tempo operacional vs. tempo total

### Para Cálculo Detalhado:
Preciso de informações sobre o equipamento ou período:
- "Calcular OEE do transportador T01 nos últimos 7 dias"
- "MTBF dos equipamentos críticos este mês"
- "Análise de disponibilidade geral da planta"

**Ou acesse**: http://localhost:3000/analytics para dashboard completo de performance.""",
            suggestions=[
                "Calcular OEE do último mês",
                "MTBF dos equipamentos críticos",
                "Análise de disponibilidade",
                "Principais causas de parada"
            ]
        )
    
    # === MANUTENÇÃO PREDITIVA ===
    if any(word in message_lower for word in ['preditiva', 'predictive', 'tendência', 'trend', 'prever', 'falha']):
        logger.info("🔮 Detectado: Consulta sobre MANUTENÇÃO PREDITIVA")
        return DashboardAgentResponse(
            response="""## 🔮 Manutenção Preditiva - PCM

### Análises Disponíveis:
1. **Detecção de Anomalias**: ML identifica comportamentos anormais
2. **Análise de Tendências**: Degradação gradual de equipamentos
3. **Previsão de Falhas**: Estimativa de tempo até falha
4. **Correlação de Variáveis**: Relação entre parâmetros

### Status do Sistema ML:
- ✅ Modelo Isolation Forest ativo
- ⏸️ Aguardando dados históricos para treino
- 📊 Monitorando: temperatura, vibração, corrente, pressão

**Acesse**: http://localhost:3000/analytics para dashboard de anomalias.""",
            suggestions=[
                "Quais equipamentos têm comportamento anormal?",
                "Análise de vibração dos motores",
                "Tendência de temperatura dos transformadores",
                "Previsão de falhas próximas"
            ]
        )
    
    # === RESPOSTA PADRÃO (Fallback genérico) ===
    logger.info("❓ Nenhuma categoria específica detectada - Resposta genérica")

    # Widget creation commands
    if any(word in message_lower for word in ['crie', 'criar', 'adicione', 'adicionar', 'add', 'create', 'mostre', 'mostrar']):
        widgets = []
        response_text = ""

        # Detect widget type from message
        if any(word in message_lower for word in ['gauge', 'medidor', 'velocímetro']):
            widget_type = 'gauge'
            widget_title = 'Gauge Widget'
        elif any(word in message_lower for word in ['gráfico', 'grafico', 'chart', 'série temporal', 'timeseries', 'histórico', 'historico', 'tendência', 'tendencia']):
            widget_type = 'timeseries'
            widget_title = 'Time Series Chart'
        elif any(word in message_lower for word in ['kpi', 'indicador', 'performance']):
            widget_type = 'kpi'
            widget_title = 'KPI Widget'
        elif any(word in message_lower for word in ['valor', 'value', 'número', 'numero']):
            widget_type = 'value'
            widget_title = 'Value Display'
        elif any(word in message_lower for word in ['status', 'estado']):
            widget_type = 'status'
            widget_title = 'Status Indicator'
        elif any(word in message_lower for word in ['tabela', 'table', 'dados']):
            widget_type = 'table'
            widget_title = 'Data Table'
        elif any(word in message_lower for word in ['barra', 'bar', 'comparação', 'comparacao']):
            widget_type = 'bar'
            widget_title = 'Bar Chart'
        elif any(word in message_lower for word in ['pizza', 'pie', 'distribuição', 'distribuicao']):
            widget_type = 'pie'
            widget_title = 'Pie Chart'
        elif any(word in message_lower for word in ['progresso', 'progress']):
            widget_type = 'progress'
            widget_title = 'Progress Bar'
        elif any(word in message_lower for word in ['sparkline', 'mini']):
            widget_type = 'sparkline'
            widget_title = 'Sparkline'
        else:
            widget_type = 'gauge'  # Default
            widget_title = 'Custom Widget'

        # Find tag mentioned or use available tags
        selected_tag_id = None
        selected_tag_name = None

        # Check for specific measurement keywords
        if any(word in message_lower for word in ['temperatura', 'temperature', 'temp']):
            widget_title = f'{widget_title} - Temperatura'
            # Look for temperature tag in available tags
            if request.available_tags:
                for tag in request.available_tags:
                    tag_name = tag.get('name', '').lower()
                    if 'temp' in tag_name:
                        selected_tag_id = tag.get('id')
                        selected_tag_name = tag.get('name')
                        break
        elif any(word in message_lower for word in ['pressão', 'pressao', 'pressure', 'press']):
            widget_title = f'{widget_title} - Pressão'
            if request.available_tags:
                for tag in request.available_tags:
                    tag_name = tag.get('name', '').lower()
                    if 'press' in tag_name:
                        selected_tag_id = tag.get('id')
                        selected_tag_name = tag.get('name')
                        break
        elif any(word in message_lower for word in ['velocidade', 'speed', 'vel']):
            widget_title = f'{widget_title} - Velocidade'
            if request.available_tags:
                for tag in request.available_tags:
                    tag_name = tag.get('name', '').lower()
                    if 'speed' in tag_name:
                        selected_tag_id = tag.get('id')
                        selected_tag_name = tag.get('name')
                        break
        elif any(word in message_lower for word in ['fluxo', 'flow', 'vazão', 'vazao']):
            widget_title = f'{widget_title} - Fluxo'
            if request.available_tags:
                for tag in request.available_tags:
                    tag_name = tag.get('name', '').lower()
                    if 'flow' in tag_name:
                        selected_tag_id = tag.get('id')
                        selected_tag_name = tag.get('name')
                        break

        # If no specific tag found, use first available
        if not selected_tag_id and request.available_tags and len(request.available_tags) > 0:
            first_tag = request.available_tags[0]
            selected_tag_id = first_tag.get('id')
            selected_tag_name = first_tag.get('name')

        # Create widget configuration
        widget_config = WidgetConfig(
            type=widget_type,
            title=widget_title,
            tagId=selected_tag_id,
            config={
                "unit": "",
                "min": 0,
                "max": 100,
                "timeRange": "1h" if widget_type == 'timeseries' else None
            }
        )
        widgets.append(widget_config)

        if selected_tag_name:
            response_text = f"✅ Criei um widget **{widget_type}** vinculado ao tag **{selected_tag_name}**.\n\n"
        else:
            response_text = f"✅ Criei um widget **{widget_type}**. Arraste uma tag para vinculá-la ao widget.\n\n"

        response_text += f"O widget '{widget_title}' foi adicionado ao seu dashboard."

        return DashboardAgentResponse(
            response=response_text,
            widgets=widgets,
            suggestions=[
                "Adicionar mais widgets",
                "Criar um gráfico de série temporal",
                "Mostrar status dos equipamentos"
            ]
        )

    # === RESPOSTA PADRÃO - Orientação Especializada ===
    return DashboardAgentResponse(
        response="""## 🤔 Como posso ajudar?

Sou especialista em **PCM/PCO e Ciência de Dados Industrial**. Posso ajudá-lo com:

### 🚨 Gestão de Alarmes & Manutenção
- "Quais são os principais alarmes?"
- "Análise de alarmes críticos"
- "Histórico de falhas do último mês"

### 📊 Performance & KPIs
- "Calcular OEE dos equipamentos"
- "MTBF e MTTR dos últimos 30 dias"
- "Análise de disponibilidade da planta"

### 🔮 Manutenção Preditiva
- "Detectar anomalias nos equipamentos"
- "Tendências de degradação"
- "Previsão de falhas"

### 📈 Análise de Dados
- "Status dos dispositivos"
- "Tendências de temperatura/vibração"
- "Correlação entre variáveis"

**Tente ser mais específico na sua pergunta!**""",
        suggestions=[
            "Quais são os principais alarmes?",
            "Análise de performance dos equipamentos",
            "Status dos dispositivos",
            "Detecção de anomalias"
        ]
    )


@router.post("/dashboard/chat", response_model=DashboardAgentResponse)
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute for LLM chat
async def chat_with_agent(
    request: Request,  # Required for rate limiting
    chat_request: DashboardAgentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Intelligent hybrid chat system:
    - Uses specialized fallback for simple queries (fast, Portuguese, accurate)
    - Uses Qwen 2.5:7B LLM for complex analysis (mathematical, multi-variable, correlations)

    Rate Limited: 10 requests/minute per IP to prevent LLM abuse

    The agent can:
    - Get real-time data
    - Query historical data
    - Calculate statistics
    - Detect anomalies
    - Provide PCM/PCO expert analysis
    """
    # Performance tracking
    start_time = time.time()

    # Check cache first (5-minute TTL, ~8s → <100ms for cached queries)
    from app.core.ai_cache import get_ai_cache
    cache = get_ai_cache()

    cached_response = cache.get(
        message=chat_request.message,
        available_tags=chat_request.available_tags
    )

    if cached_response:
        latency_ms = (time.time() - start_time) * 1000
        logger.info(f"⚡ CACHE HIT [{latency_ms:.0f}ms]: '{chat_request.message[:50]}...'")
        return DashboardAgentResponse(**cached_response)

    # DEBUG: Log entrada do endpoint
    logger.debug(f"🔍 DEBUG: Starting chat request: '{chat_request.message}'")
    logger.debug(f"🔍 DEBUG: Available tags: {len(chat_request.available_tags or [])}")

    # Initialize services
    data_service = DataService(db)
    toolkit = AgentToolkit(data_service)

    # ========================================
    # DIRECT TOOL CALL: Bypass LLM for programmatic access
    # ========================================
    if chat_request.tool_call:
        try:
            tool_name = chat_request.tool_call.name
            tool_args = chat_request.tool_call.arguments

            logger.info(f"🔧 Direct tool call: {tool_name} with args: {tool_args}")

            # Execute tool directly
            tool_result = await toolkit.execute_tool(tool_name, tool_args)

            # Handle ToolResult object (has success, data, error attributes)
            if not tool_result.success:
                return DashboardAgentResponse(
                    response=f"Erro ao executar ferramenta {tool_name}: {tool_result.error}",
                    widgets=None,
                    suggestions=None
                )

            # Extract data from ToolResult
            result_data = tool_result.data if hasattr(tool_result, 'data') else {}

            # Check if result_data has error key
            if isinstance(result_data, dict) and result_data.get("error"):
                return DashboardAgentResponse(
                    response=f"Erro ao executar ferramenta {tool_name}: {result_data['error']}",
                    widgets=None,
                    suggestions=None
                )

            # Return tool result with summary AND raw data
            summary = _summarize_tool_result(tool_name, result_data)

            return DashboardAgentResponse(
                response=summary,
                widgets=None,
                suggestions=_generate_tool_suggestions(tool_name, result_data),
                tool_result=result_data  # Include raw data for frontend
            )

        except Exception as e:
            logger.error(f"Error in direct tool call: {e}")
            import traceback
            traceback.print_exc()
            return DashboardAgentResponse(
                response=f"Erro ao executar ferramenta: {str(e)}",
                widgets=None,
                suggestions=None
            )

    message_lower = chat_request.message.lower()
    
    # === HYBRID DECISION: Fallback vs Qwen ===
    # Use FALLBACK for simple, direct queries (fast + Portuguese + specialized)
    simple_keywords = [
        'alarme', 'alarm', 'alerta', 'principal', 'crítico', 'urgente',
        'dispositivo', 'device', 'status', 'online', 'offline',
        'olá', 'oi', 'hello', 'help', 'ajuda'
    ]

    # REALTIME VALUE queries - Use fallback for instant response
    # EXPANDED: Now includes "valor de", "leitura de", and direct tag queries
    realtime_value_keywords = [
        'temperatura atual', 'pressão atual', 'valor atual', 'velocidade atual',
        'qual a temperatura', 'qual a pressão', 'qual o valor', 'qual a velocidade',
        'quanto está', 'quanto é', 'qual está', 'qual é',
        'me mostre o valor', 'mostre a temperatura', 'mostre a pressão',
        'valor de', 'valor do', 'valor da', 'leitura de', 'leitura do', 'leitura da'
    ]

    # DETECT TAG NAME IN QUERY: If query contains a tag-like name (word_word format), treat as realtime query
    import re
    tag_name_pattern = re.search(r'\b([a-zA-Z][a-zA-Z0-9_]*(?:_[a-zA-Z0-9]+)+)\b', chat_request.message)
    has_tag_name_in_query = tag_name_pattern is not None
    if has_tag_name_in_query:
        logger.debug(f"🏷️ Detected tag name pattern in query: {tag_name_pattern.group(1)}")

    use_fallback = any(keyword in message_lower for keyword in simple_keywords)
    use_fallback_realtime = any(keyword in message_lower for keyword in realtime_value_keywords) or has_tag_name_in_query
    
    # Use QWEN for complex queries requiring math, logic, or multi-step analysis
    complex_keywords = [
        'média', 'average', 'mean', 'máximo', 'maximum', 'mínimo', 'minimum',
        'comparar', 'compare', 'correlação', 'correlation', 'tendência', 'trend',
        'anomalia', 'anomaly', 'estatística', 'statistic', 'análise', 'analysis',
        'calcul', 'desvio', 'variação', 'predict',
        # Frequency analysis keywords
        'quantas vezes', 'frequência', 'histórico', 'ocorrências', 'aparece', 'ocorre'
    ]

    # EXECUTIVE DASHBOARD keywords - queries about executive metrics, reports, energy, production
    executive_keywords = [
        'executivo', 'executive', 'kpi', 'kpis', 'dashboard', 'gerencial', 'diretoria',
        'visão geral', 'overview', 'indicadores',
        'energia', 'energy', 'consumo', 'kwh', 'demanda', 'fator de potência', 'conta de luz',
        'produção', 'production', 'throughput', 'capacidade', 'meta',
        'pareto', 'ranking', '80/20',
        'financeiro', 'financial', 'economia', 'savings', 'roi', 'custo',
        'manutenção preditiva', 'predictive maintenance', 'health score',
        'relatório', 'relatorio', 'report', 'pdf', 'exportar', 'gerar'
    ]

    use_qwen_executive = any(keyword in message_lower for keyword in executive_keywords)

    # DISCOVERY keywords - queries asking WHAT/WHICH tags/sensors exist
    # These MUST use Qwen to call search_tags() and get_all_tags() tools
    discovery_keywords = [
        'quais', 'qual', 'which', 'what', 'liste', 'list', 'listar',
        'busque', 'buscar', 'search', 'procure', 'procurar', 'find',
        'disponível', 'disponíveis', 'available', 'existe', 'existem', 'exist',
        'mostre', 'mostrar', 'show', 'tags', 'sensores', 'sensors'
    ]
    
    use_qwen = any(keyword in message_lower for keyword in complex_keywords)
    use_qwen_discovery = any(keyword in message_lower for keyword in discovery_keywords)

    # DEBUG: Log classification
    logger.debug(f"🔍 DEBUG: Query classification - fallback_realtime={use_fallback_realtime}, complex={use_qwen}, discovery={use_qwen_discovery}, executive={use_qwen_executive}")

    # PRIORITY 0: Executive dashboard queries → Always use QWEN with PRE-EXECUTE
    if use_qwen_executive:
        use_fallback = False
        use_qwen = True
        logger.debug("📊 EXECUTIVE QUERY detected → Using Qwen with PRE-EXECUTE for executive data")

    # PRIORITY 1: Realtime value queries → Use QWEN with PRE-EXECUTE for data-driven analysis
    # Changed: Realtime queries now use Qwen to ensure 2-step architecture (PostgreSQL → InfluxDB)
    elif use_fallback_realtime:
        use_fallback = False
        use_qwen = True
        logger.debug("⚡ REALTIME QUERY detected → Using Qwen with PRE-EXECUTE for data fetching")

    # PRIORITY 2: Discovery queries use Qwen (need search tools)
    elif use_qwen_discovery and not use_fallback_realtime:
        use_qwen = True
        use_fallback = False

    # If both or neither match, default based on message complexity
    elif not use_fallback and not use_qwen:
        # Short messages (<20 words) → fallback
        # Long/complex messages → Qwen
        word_count = len(chat_request.message.split())
        use_fallback = word_count < 20
        use_qwen = not use_fallback

    # Override: If specifically needs calculation/analysis, always use Qwen
    if use_qwen and use_fallback and not use_fallback_realtime:
        use_qwen = True
        use_fallback = False

    logger.debug(f"🔍 DEBUG: Final classification: fallback={use_fallback}, qwen={use_qwen}, realtime={use_fallback_realtime}")

    if use_fallback:
        logger.debug("⚡ Using specialized fallback mode (fast response)")
        return await chat_fallback_mode(chat_request, data_service, toolkit, db)

    # Check if Ollama is available
    logger.debug(f"🔍 DEBUG: Checking Ollama availability at {OLLAMA_BASE_URL}")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            logger.debug(f"✅ DEBUG: Ollama available - Status {response.status_code}")
    except Exception as e:
        logger.warning(f"⚠️ Ollama not available, using fallback mode: {e}")
        return await chat_fallback_mode(chat_request, data_service, toolkit, db)

    # === NEW APPROACH: PRE-EXECUTE TOOLS FIRST ===
    logger.debug("🔍 Starting PRE-EXECUTE tools...")
    pre_fetched_data = await pre_execute_tools_from_query(
        query=chat_request.message,
        available_tags=chat_request.available_tags,
        toolkit=toolkit
    )
    logger.info(f"🔍 PRE-EXECUTE complete. Has data: {bool(pre_fetched_data)}, length: {len(pre_fetched_data) if pre_fetched_data else 0}")

    # If we have pre-fetched data, use DATA-DRIVEN prompt
    if pre_fetched_data:
        logger.info("✅ Data pre-fetched successfully, using DATA-DRIVEN analysis mode")
        system_prompt = SYSTEM_PROMPT_WITH_DATA.format(
            data_context=pre_fetched_data,
            user_query=chat_request.message
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": chat_request.message}
        ]

        # Call LLM with pre-fetched data
        final_response = await call_ollama(messages, max_iterations=1)  # No tool calling needed!

        # Cache and return
        # Validate response quality
        response_length = len(final_response) if final_response else 0
        latency_ms = (time.time() - start_time) * 1000

        if response_length < 50:
            logger.warning(f"⚠️ SHORT RESPONSE [{response_length} chars, {latency_ms:.0f}ms]: May be incomplete")

        logger.info(f"✅ PRE-EXECUTE RESPONSE [{response_length} chars, {latency_ms:.0f}ms]: '{chat_request.message[:40]}...'")

        response_data = {
            "response": final_response,
            "widgets": None,
            "suggestions": None
        }

        cache.set(
            message=chat_request.message,
            response=response_data,
            available_tags=chat_request.available_tags
        )

        return DashboardAgentResponse(**response_data)

    # FALLBACK: If no data pre-fetched, use traditional tool-calling approach
    logger.info("⚠️  No data pre-fetched, falling back to traditional tool-calling")

    # Build system prompt with SELECTIVE tools (faster inference)
    # Only include tools relevant to the query to reduce prompt size
    message_lower = chat_request.message.lower()

    # Smart tool selection based on query keywords
    relevant_tools = []
    all_tools = toolkit.get_tool_definitions()

    # Always include these core tools
    core_tool_names = ["get_all_tags", "search_tags", "get_active_alarms"]

    # Add tools based on query content
    if any(word in message_lower for word in ["tempo real", "atual", "agora", "current", "realtime", "valor"]):
        core_tool_names.extend(["get_realtime_value", "get_multiple_realtime_values"])

    if any(word in message_lower for word in ["histórico", "históricos", "tendência", "trend", "históry", "passado"]):
        core_tool_names.append("get_historical_data")

    if any(word in message_lower for word in ["média", "average", "estatística", "statistics", "min", "max", "desvio"]):
        core_tool_names.append("calculate_statistics")

    if any(word in message_lower for word in ["comparar", "compare", "correlação", "correlation"]):
        core_tool_names.append("compare_tags")

    if any(word in message_lower for word in ["anomalia", "anomaly", "outlier", "desvio"]):
        core_tool_names.append("detect_anomalies")

    if any(word in message_lower for word in ["oee", "eficiência", "efficiency", "disponibilidade"]):
        core_tool_names.append("calculate_oee")

    # EXECUTIVE DASHBOARD tools
    if any(word in message_lower for word in ["executivo", "executive", "visão geral", "overview", "kpi", "dashboard", "gerencial", "diretoria"]):
        core_tool_names.extend(["get_executive_overview", "get_executive_trends"])

    if any(word in message_lower for word in ["energia", "energy", "consumo", "kwh", "demanda", "fator de potência", "conta de luz"]):
        core_tool_names.append("get_energy_metrics")

    if any(word in message_lower for word in ["produção", "production", "throughput", "ton/h", "capacidade", "meta", "ciclo"]):
        core_tool_names.append("get_production_metrics")

    if any(word in message_lower for word in ["pareto", "ranking", "top alarmes", "principais alarmes", "80/20"]):
        core_tool_names.append("get_alarm_pareto")

    if any(word in message_lower for word in ["financeiro", "financial", "economia", "savings", "roi", "custo", "cost"]):
        core_tool_names.append("get_financial_summary")

    if any(word in message_lower for word in ["manutenção", "maintenance", "preditiva", "predictive", "health", "saúde", "falha", "failure"]):
        core_tool_names.append("get_maintenance_dashboard")

    if any(word in message_lower for word in ["relatório", "report", "pdf", "exportar", "export", "gerar relatório", "generate report"]):
        core_tool_names.append("generate_executive_report")

    # ASSET TREE tools
    if any(word in message_lower for word in ["asset", "ativo", "ativos", "hierarquia", "hierarchy", "equipamento", "equipamentos", "planta", "área", "elemento", "elementos", "estrutura"]):
        core_tool_names.extend(["get_asset_hierarchy", "get_asset_element", "search_assets", "get_asset_statistics"])

    if any(word in message_lower for word in ["atributo", "atributos", "sensor", "sensores", "tag", "tags"]):
        core_tool_names.extend(["get_element_attributes", "get_tags_by_asset"])

    # Filter tools to only relevant ones (reduces prompt tokens by 60-70%)
    relevant_tools = [t for t in all_tools if t.get("name") in set(core_tool_names)]

    # Fallback: if no tools selected, use top 5 most common
    if not relevant_tools:
        relevant_tools = all_tools[:5]

    tools_description = format_tools_for_prompt(relevant_tools)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(tools=tools_description)
    
    # Build messages for Ollama - MINIMAL context for speed
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Skip context to reduce tokens and speed up inference
    # (context adds ~200-500 tokens, slows down GPU processing)

    # Add user message
    messages.append({"role": "user", "content": chat_request.message})
    
    # Multi-turn conversation with tool support - REDUCED for speed
    max_iterations = 2  # Was 3, now 2 for faster response
    final_response = ""
    
    for iteration in range(max_iterations):
        # Call LLM
        llm_response = await call_ollama(messages)

        # Check for tool calls (with heuristic fallback for Qwen 7B)
        tool_calls = extract_tool_calls_with_fallback(
            llm_response,
            available_tags=chat_request.available_tags
        )
        
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
    if chat_request.available_tags and len(chat_request.available_tags) > 5:
        suggestions.append("Create a comprehensive dashboard")

    # Create response
    response_data = DashboardAgentResponse(
        response=clean_response,
        widgets=widgets,
        suggestions=suggestions if suggestions else None
    )

    # Cache the response (5-minute TTL)
    cache.set(
        message=chat_request.message,
        response=response_data.dict(),
        available_tags=chat_request.available_tags
    )

    return response_data


@router.get("/cache/stats")
async def get_cache_stats():
    """Get AI response cache statistics"""
    from app.core.ai_cache import get_ai_cache
    cache = get_ai_cache()
    return cache.get_stats()


@router.post("/cache/clear")
async def clear_cache():
    """Clear AI response cache (admin only)"""
    from app.core.ai_cache import get_ai_cache
    cache = get_ai_cache()
    cache.clear()
    return {"status": "success", "message": "Cache cleared successfully"}


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


@router.post("/dashboard/chat/stream")
@limiter.limit("10/minute")
async def chat_with_agent_stream(
    request: Request,  # Required for rate limiting
    chat_request: DashboardAgentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    🚀 STREAMING VERSION of chat_with_agent

    Returns SSE (Server-Sent Events) stream for real-time AI responses.
    User sees text appear progressively (like ChatGPT) instead of waiting 8s for full response.

    Benefits:
    - Perceived latency: ~1-2s (first tokens) instead of 8s
    - Better UX for long responses
    - User can see AI "thinking" in real-time

    Format: SSE (text/event-stream)
    - data: {JSON with chunk, done, metadata}
    """

    async def generate_sse_stream():
        """Generator for SSE stream"""
        try:
            # Initialize services
            data_service = DataService(db)
            toolkit = AgentToolkit(data_service)

            message_lower = chat_request.message.lower()

            # === HYBRID DECISION: Fallback vs Qwen (same logic as non-streaming) ===
            simple_keywords = [
                'alarme', 'alarm', 'alerta', 'principal', 'crítico', 'urgente',
                'dispositivo', 'device', 'status', 'online', 'offline',
                'olá', 'oi', 'hello', 'help', 'ajuda'
            ]

            use_fallback = any(keyword in message_lower for keyword in simple_keywords)

            complex_keywords = [
                'média', 'average', 'mean', 'máximo', 'maximum', 'mínimo', 'minimum',
                'comparar', 'compare', 'correlação', 'correlation', 'tendência', 'trend',
                'anomalia', 'anomaly', 'estatística', 'statistic', 'análise', 'analysis',
                'calcul', 'desvio', 'variação', 'predict'
            ]

            discovery_keywords = [
                'quais', 'qual', 'which', 'what', 'liste', 'list', 'listar',
                'busque', 'buscar', 'search', 'procure', 'procurar', 'find',
                'disponível', 'disponíveis', 'available', 'existe', 'existem', 'exist',
                'mostre', 'mostrar', 'show', 'tags', 'sensores', 'sensors'
            ]

            use_qwen = any(keyword in message_lower for keyword in complex_keywords)
            use_qwen_discovery = any(keyword in message_lower for keyword in discovery_keywords)

            if use_qwen_discovery:
                use_qwen = True
                use_fallback = False

            if not use_fallback and not use_qwen:
                word_count = len(chat_request.message.split())
                use_fallback = word_count < 20
                use_qwen = not use_fallback

            if use_qwen and use_fallback:
                use_qwen = True
                use_fallback = False

            # REALTIME VALUE queries - Use PRE-EXECUTE for data-driven analysis
            realtime_value_keywords = [
                'temperatura atual', 'pressão atual', 'valor atual', 'velocidade atual',
                'qual a temperatura', 'qual a pressão', 'qual o valor', 'qual a velocidade',
                'quanto está', 'quanto é', 'qual está', 'qual é',
                'me mostre o valor', 'mostre a temperatura', 'mostre a pressão'
            ]

            # ALARM queries - Use PRE-EXECUTE for alarm data (NEW)
            alarm_keywords = [
                'alarme', 'alarm', 'alerta', 'alert',
                'problema', 'problem', 'crítico', 'critical',
                'falha', 'failure', 'erro', 'error',
                'atenção', 'atencao', 'warning', 'aviso'
            ]

            use_fallback_realtime = any(keyword in message_lower for keyword in realtime_value_keywords)
            use_fallback_alarms = any(keyword in message_lower for keyword in alarm_keywords)

            # PRIORITY: Realtime and Alarm queries use PRE-EXECUTE with data-driven prompts
            if use_fallback_realtime or use_fallback_alarms:
                use_fallback = False
                use_qwen = True
                if use_fallback_realtime:
                    logger.info("⚡ STREAMING REALTIME QUERY detected → Using PRE-EXECUTE for data fetching")
                if use_fallback_alarms:
                    logger.info("🚨 STREAMING ALARM QUERY detected → Using PRE-EXECUTE for alarm data")

            logger.info(f"🌊 Streaming query: fallback={use_fallback}, qwen={use_qwen}, realtime={use_fallback_realtime}")

            # === FALLBACK MODE (Fast, non-streaming) ===
            if use_fallback:
                response = await chat_fallback_mode(chat_request, data_service, toolkit, db)
                # Send as single chunk
                metadata = {"model": "fallback", "mode": "fast"}
                yield f"data: {json.dumps({'chunk': response.response, 'done': True, 'metadata': metadata})}\n\n"
                return

            # === PRE-EXECUTE MODE (for realtime and alarm queries) ===
            if use_fallback_realtime or use_fallback_alarms:
                logger.debug(f"🔍 PRE-EXECUTING tools for streaming realtime query... Query={chat_request.message}, Tags count={len(chat_request.available_tags) if chat_request.available_tags else 0}")
                pre_fetched_data = await pre_execute_tools_from_query(
                    query=chat_request.message,
                    available_tags=chat_request.available_tags,
                    toolkit=toolkit
                )
                logger.debug(f"✅ pre_fetched_data result: {pre_fetched_data}")

                if pre_fetched_data:
                    logger.info("✅ Data pre-fetched, using DATA-DRIVEN streaming mode")
                    # Use data-driven prompt
                    system_prompt = SYSTEM_PROMPT_WITH_DATA.format(
                        data_context=pre_fetched_data,
                        user_query=chat_request.message
                    )

                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": chat_request.message}
                    ]

                    # Stream response from Qwen
                    full_response = ""
                    chunk_count = 0

                    async for chunk in call_ollama_stream(messages):
                        full_response += chunk
                        chunk_count += 1
                        yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"

                    # Send done message
                    metadata = {
                        "model": "qwen2.5:7b",
                        "mode": "pre-execute-data-driven",
                        "chunks_sent": chunk_count
                    }
                    yield f"data: {json.dumps({'done': True, 'metadata': metadata})}\n\n"
                    logger.info(f"✅ PRE-EXECUTE streaming complete: {chunk_count} chunks")
                    return

            # === QWEN MODE with STREAMING (traditional tool-calling) ===
            # Select relevant tools (same smart selection as non-streaming)
            all_tools = toolkit.get_tool_definitions()
            core_tool_names = ["get_all_tags", "search_tags", "get_active_alarms"]

            if any(word in message_lower for word in ["tempo real", "atual", "agora", "current", "now"]):
                core_tool_names.extend(["get_realtime_value", "get_multiple_realtime_values"])

            if any(word in message_lower for word in ["média", "average", "estatística", "statistics", "máx", "mín"]):
                core_tool_names.append("calculate_statistics")

            if any(word in message_lower for word in ["histórico", "history", "tendência", "trend", "passado"]):
                core_tool_names.append("get_historical_data")

            if any(word in message_lower for word in ["comparar", "compare", "versus", "vs", "diferença"]):
                core_tool_names.append("compare_tags")

            if any(word in message_lower for word in ["anomalia", "anomaly", "outlier", "desvio"]):
                core_tool_names.append("detect_anomalies")

            if any(word in message_lower for word in ["oee", "eficiência", "efficiency", "disponibilidade"]):
                core_tool_names.append("calculate_oee")

            if any(word in message_lower for word in ["padrão", "pattern", "frequência", "frequency"]):
                core_tool_names.append("analyze_alarm_patterns")

            # NEW: Advanced analytics tools
            if any(word in message_lower for word in ["frequência", "frequency", "chattering", "flood", "taxa"]):
                core_tool_names.append("analyze_alarm_frequency")

            if any(word in message_lower for word in ["histograma", "histogram", "distribuição", "distribution"]):
                core_tool_names.append("generate_data_histogram")

            if any(word in message_lower for word in ["correlação", "correlation", "relação", "relationship"]):
                core_tool_names.append("calculate_correlation")

            if any(word in message_lower for word in ["tendência", "trend", "crescendo", "diminuindo", "increasing", "decreasing"]):
                core_tool_names.append("detect_trends")

            if any(word in message_lower for word in ["insight", "insights", "análise", "analysis", "recomendação", "recommendation"]):
                core_tool_names.append("generate_insights")

            relevant_tools = [t for t in all_tools if t.get("name") in set(core_tool_names)]

            # Build optimized system prompt
            tools_description = format_tools_for_prompt(relevant_tools)

            # Build available tags list for prompt
            available_tags_list = ""
            logger.info(f"📋 Available tags received: {len(chat_request.available_tags) if chat_request.available_tags else 0}")
            if chat_request.available_tags:
                logger.info(f"📋 First 3 tags: {[t.get('name', t.get('id')) for t in chat_request.available_tags[:3]]}")
                available_tags_list = "\n## TAGS DISPONÍVEIS:\n"
                for tag in chat_request.available_tags[:20]:  # Limit to 20 to avoid prompt bloat
                    tag_name = tag.get('name', tag.get('id'))
                    unit = tag.get('unit', '')
                    available_tags_list += f"- **{tag_name}** ({unit})\n"
            else:
                logger.warning("⚠️ No available_tags provided in request!")

            SYSTEM_PROMPT_TEMPLATE = """OptiFlow AI - Analista Industrial

{tools}
{available_tags}

REGRAS CRÍTICAS:
1) SEMPRE use APENAS os tags da lista "TAGS DISPONÍVEIS" acima
2) NUNCA invente nomes de tags - use EXATAMENTE como listado
3) Use blocos ```tool para chamar ferramentas
4) Português, conciso, Markdown+emojis

COMO CHAMAR FERRAMENTAS:
Para buscar dados, use este formato EXATO:

```tool
{{
  "name": "get_realtime_value",
  "arguments": {{"tag_id": "NOME_EXATO_DO_TAG"}}
}}
```

⚠️ IMPORTANTE: Sempre use o nome COMPLETO e EXATO do tag como aparece na lista "TAGS DISPONÍVEIS".
Exemplo: Se o usuário perguntar sobre "EL01", procure na lista por tags que contenham "EL01" (como "ELEV01_TEMP_C_PV") e use esse nome completo.

FORMATO: 📊 Dados → 🔍 Análise → 💡 Ações"""

            system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
                tools=tools_description,
                available_tags=available_tags_list
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": chat_request.message}
            ]

            # === STREAM FROM QWEN ===
            full_response = ""
            chunk_count = 0

            async for chunk in call_ollama_stream(messages):
                full_response += chunk
                chunk_count += 1

                # Send chunk to frontend via SSE
                yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"

            # Process tool calls after streaming is done (with heuristic fallback)
            tool_calls = extract_tool_calls_with_fallback(
                full_response,
                available_tags=chat_request.available_tags
            )

            if tool_calls:
                # Execute tools and send results
                tool_results = []
                for tool_call in tool_calls:
                    # ToolCall objects have .name and .arguments attributes
                    tc_name = tool_call.name if hasattr(tool_call, 'name') else tool_call["name"]
                    tc_args = tool_call.arguments if hasattr(tool_call, 'arguments') else tool_call["arguments"]

                    result = await toolkit.execute_tool(tc_name, tc_args)
                    tool_results.append({
                        "tool": tc_name,
                        "result": result.data if result.success else f"Error: {result.error}"
                    })

                # Send final analysis with tool results
                yield f"data: {json.dumps({'tools_executed': tool_results, 'done': False})}\n\n"

            # Send final "done" message
            metadata = {
                "model": "qwen2.5:7b",
                "chunks_sent": chunk_count,
                "tools_used": [(tc.name if hasattr(tc, 'name') else tc["name"]) for tc in tool_calls] if tool_calls else []
            }

            yield f"data: {json.dumps({'done': True, 'metadata': metadata})}\n\n"

            logger.info(f"✅ Streaming complete: {chunk_count} chunks, {len(tool_calls or [])} tools")

        except Exception as e:
            logger.error(f"❌ Streaming error: {str(e)}")
            import traceback
            traceback.print_exc()  # Print full stack trace
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    # Return SSE stream
    return StreamingResponse(
        generate_sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


# ========================================
# Helper Functions for Direct Tool Calls
# ========================================

def _summarize_tool_result(tool_name: str, result: Dict[str, Any]) -> str:
    """Generate a human-readable summary of tool result"""

    if tool_name == "calculate_mtbf_mttr":
        mtbf = result.get("mtbf_hours")
        mttr = result.get("mttr_hours")
        availability = result.get("availability_percent")
        classification = result.get("reliability_classification", "N/A")

        summary = f"## 🔧 Análise MTBF/MTTR - {result.get('equipment_id', 'Equipamento')}\n\n"
        summary += f"**Classificação:** {classification}\n\n"
        summary += "### Métricas Principais\n"
        summary += f"- **MTBF:** {mtbf:.1f}h ({mtbf/24:.1f} dias)\n" if mtbf else "- **MTBF:** N/A\n"
        summary += f"- **MTTR:** {mttr:.1f}h\n" if mttr else "- **MTTR:** N/A\n"
        summary += f"- **Disponibilidade:** {availability:.1f}%\n" if availability else "- **Disponibilidade:** N/A\n"
        summary += f"- **Falhas no Período:** {result.get('failure_count', 0)}\n\n"

        if result.get("insights"):
            summary += "### Insights\n"
            for insight in result["insights"]:
                summary += f"- {insight}\n"

        if result.get("recommendations"):
            summary += "\n### Recomendações\n"
            for rec in result["recommendations"]:
                summary += f"- {rec}\n"

        return summary

    elif tool_name == "predict_failure":
        risk_level = result.get("overall_risk_level", "unknown")
        probability = result.get("failure_probability", 0)
        priority = result.get("action_priority", "routine")

        risk_icons = {"low": "✅", "medium": "⚡", "high": "⚠️", "critical": "🚨"}

        summary = f"## 🔮 Predição de Falha - {result.get('equipment_id', 'Equipamento')}\n\n"
        summary += f"**Nível de Risco:** {risk_icons.get(risk_level, '❓')} {risk_level.upper()}\n"
        summary += f"**Probabilidade de Falha:** {probability*100:.1f}%\n"
        summary += f"**Prioridade de Ação:** {priority}\n"
        summary += f"**Confiança:** {result.get('confidence', 0)*100:.0f}%\n\n"

        if result.get("predicted_failure_window"):
            window = result["predicted_failure_window"]
            summary += f"### Janela de Falha Prevista\n"
            summary += f"- **Mais provável:** {window['most_likely_days']} dias\n"
            summary += f"- **Intervalo:** {window['min_days']}-{window['max_days']} dias\n\n"

        if result.get("risk_factors"):
            summary += "### Fatores de Risco\n"
            for factor in result["risk_factors"][:5]:
                summary += f"- **{factor['tag_id']}** ({factor['risk_score']*100:.0f}%): {factor['primary_concern']}\n"

        if result.get("recommendations"):
            summary += "\n### Ações Recomendadas\n"
            for rec in result["recommendations"]:
                summary += f"- {rec}\n"

        return summary

    elif tool_name == "calculate_spc_limits":
        stability = result.get("stability_assessment", {}).get("status", "N/A")
        cpk = result.get("capability_indices", {}).get("cpk")
        ooc_count = result.get("stability_assessment", {}).get("out_of_control_count", 0)

        stability_icons = {"Estável": "✅", "Marginalmente Estável": "⚡", "Instável": "🚨"}

        summary = f"## 📊 Análise CEP/SPC - {result.get('tag_id', 'Tag')}\n\n"
        summary += f"**Status:** {stability_icons.get(stability, '❓')} {stability}\n"
        summary += f"**Pontos Fora de Controle:** {ooc_count}\n\n"

        if result.get("control_limits"):
            limits = result["control_limits"]
            chart = limits.get("x_bar_chart") or limits.get("individuals_chart")
            if chart:
                summary += "### Limites de Controle\n"
                summary += f"- **UCL:** {chart['ucl']:.4f}\n"
                summary += f"- **CL:** {chart['cl']:.4f}\n"
                summary += f"- **LCL:** {chart['lcl']:.4f}\n\n"

        if cpk is not None:
            summary += "### Índices de Capabilidade\n"
            cap = result["capability_indices"]
            summary += f"- **Cp:** {cap.get('cp', 0):.2f}\n"
            summary += f"- **Cpk:** {cpk:.2f}\n"
            summary += f"- **Nível Sigma:** {cap.get('sigma_level', 0):.1f}σ\n"
            summary += f"- **PPM Estimado:** {cap.get('ppm_estimate', 0):.0f}\n\n"

        if result.get("insights"):
            summary += "### Insights\n"
            for insight in result["insights"]:
                summary += f"- {insight}\n"

        if result.get("recommendations"):
            summary += "\n### Recomendações\n"
            for rec in result["recommendations"]:
                summary += f"- {rec}\n"

        return summary

    else:
        # Generic summary for other tools
        return f"## Resultado: {tool_name}\n\n```json\n{json.dumps(result, indent=2, default=str)}\n```"


def _generate_tool_suggestions(tool_name: str, result: Dict[str, Any]) -> List[str]:
    """Generate follow-up suggestions based on tool result"""

    suggestions = []

    if tool_name == "calculate_mtbf_mttr":
        classification = result.get("reliability_classification")
        if classification in ["Crítico", "Regular"]:
            suggestions.append("Analise a predição de falha deste equipamento")
            suggestions.append("Quais são as causas das últimas paradas?")
        suggestions.append("Compare a disponibilidade com outros equipamentos")
        suggestions.append("Qual é a tendência do MTBF nos últimos 3 meses?")

    elif tool_name == "predict_failure":
        risk_level = result.get("overall_risk_level")
        if risk_level in ["high", "critical"]:
            suggestions.append("Quais são os alarmes ativos deste equipamento?")
            suggestions.append("Mostre a tendência das tags de risco")
        suggestions.append("Calcule o MTBF/MTTR deste equipamento")
        suggestions.append("Compare o risco com equipamentos similares")

    elif tool_name == "calculate_spc_limits":
        stability = result.get("stability_assessment", {}).get("status")
        if stability == "Instável":
            suggestions.append("Detecte anomalias nesta tag")
            suggestions.append("Qual é a tendência dos valores?")
        suggestions.append("Compare com os limites de especificação")
        suggestions.append("Analise a correlação com outras tags")

    else:
        suggestions = [
            "Mostre mais detalhes",
            "Analise tendências relacionadas",
            "Compare com dados históricos"
        ]

    return suggestions[:4]  # Limit to 4 suggestions


@router.post("/tools/test")
async def test_agent_tools(
    tool_name: str,
    arguments: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """
    Test agent tools directly

    Available tools:
    - get_all_tags: List all tags
    - get_active_alarms: List active alarms
    - search_tags: Search for tags
    - get_realtime_value: Get current tag value
    - calculate_statistics: Calculate stats for a tag
    """
    try:
        data_service = DataService(db)
        toolkit = AgentToolkit(data_service)

        if arguments is None:
            arguments = {}

        result = await toolkit.execute_tool(tool_name, arguments)

        return {
            "tool": tool_name,
            "success": result.success,
            "data": result.data,
            "error": result.error
        }

    except Exception as e:
        logger.error(f"Error testing tool {tool_name}: {e}")
        return {
            "tool": tool_name,
            "success": False,
            "error": str(e)
        }
