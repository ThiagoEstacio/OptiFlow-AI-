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
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...db.session import get_db
from ...services.data_service import DataService
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


# System prompt for DATA-DRIVEN analysis (with pre-fetched data)
SYSTEM_PROMPT_WITH_DATA = """Você é um Analista de Manutenção Preditiva (PCM/PCO) especializado em análise de dados industriais.

## DADOS DISPONÍVEIS:
{data_context}

## SUA MISSÃO:
Analise os dados acima e forneça:
1. 📊 **Situação Atual**: Resumo dos valores/status
2. 🔍 **Análise Técnica**: Identificar padrões, anomalias, tendências
3. 💡 **Recomendações**: Ações concretas baseadas nos dados

## FORMATO DE RESPOSTA:
- Use Markdown com emojis
- Seja conciso e objetivo
- Foque em insights acionáveis
- Cite valores específicos dos dados

## CONTEXTO DO USUÁRIO:
Pergunta: {user_query}

Analise os dados e responda de forma técnica e precisa."""

# Fallback prompt (when no tools available)
SYSTEM_PROMPT_TEMPLATE = """OptiFlow AI - Analista Industrial

{tools}

REGRAS:
1) SEMPRE busque dados reais usando ferramentas
2) Use blocos ```tool para chamar ferramentas
3) Português, conciso, Markdown+emojis

FORMATO: 📊 Dados → 🔍 Análise → 💡 Ações"""


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
    logger.error(f"🔍 find_best_matching_tag called with query: {query}")

    # Identify measurement type from query
    measurement_type = None
    if 'temperatura' in query_lower or 'temp' in query_lower:
        measurement_type = 'temp'
    elif 'pressão' in query_lower or 'pressure' in query_lower:
        measurement_type = 'press'
    elif 'corrente' in query_lower or 'current' in query_lower:
        measurement_type = 'current'
    elif 'potência' in query_lower or 'power' in query_lower:
        measurement_type = 'power'
    elif 'velocidade' in query_lower or 'speed' in query_lower:
        measurement_type = 'speed'

    logger.error(f"🎯 Detected measurement_type: {measurement_type}")

    # Extract keywords from query (remove common words AND measurement type words)
    measurement_words = ['temperatura', 'temp', 'pressão', 'pressure', 'corrente', 'current', 'potência', 'power', 'velocidade', 'speed']
    keywords = []
    for word in query_lower.split():
        # Remove punctuation from word
        clean_word = word.strip('.,?!;:')
        # Remove common words AND measurement type words (we handle those separately)
        if clean_word and clean_word not in ['qual', 'a', 'o', 'do', 'da', 'de', 'valor', 'atual', 'é', 'está'] and clean_word not in measurement_words:
            keywords.append(clean_word)

    logger.error(f"🔑 Extracted keywords: {keywords}")

    # Try exact match first
    for tag in available_tags:
        tag_name = tag.get('name', '').lower()
        tag_id = tag.get('id', '').lower()

        # Check if query mentions the exact tag name or ID
        if tag_name in query_lower or tag_id in query_lower:
            return tag

    # PRIORITY: If measurement type identified, find tag with matching type
    if measurement_type:
        logger.error(f"🔍 Searching for tags with measurement_type={measurement_type}")
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
                    logger.error(f"  ➕ Tag matched keyword '{keyword}' (exact): {tag.get('name')}")
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
                        logger.error(f"  ➕ Tag matched keyword '{keyword}' (fuzzy): {tag.get('name')}")
                        break

        logger.error(f"📋 Found {len(matching_tags)} tags matching keywords")

        # Then, filter by measurement type
        for tag in matching_tags:
            tag_name = tag.get('name', '').lower()
            logger.error(f"  🔎 Checking tag '{tag.get('name')}': Does '{tag_name}' contain '{measurement_type}'? {measurement_type in tag_name}")
            if measurement_type in tag_name:
                logger.error(f"✅ MATCHED TAG with measurement_type={measurement_type}: {tag.get('name')}")
                return tag

        logger.error(f"⚠️ No tags found with measurement_type={measurement_type} in {len(matching_tags)} candidates")

    # Try partial match (e.g., "el01" matches "ELEV01_TEMP_C_PV")
    for keyword in keywords:
        for tag in available_tags:
            tag_name = tag.get('name', '').lower()
            tag_id = tag.get('id', '').lower()

            # Check if keyword is part of tag name
            if keyword in tag_name or keyword in tag_id:
                return tag

    # Fallback: return first tag
    return available_tags[0]


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
    realtime_patterns = [
        'temperatura atual', 'pressão atual', 'valor atual', 'velocidade atual',
        'qual a temperatura', 'qual a pressão', 'qual o valor',
        'quanto está', 'quanto é', 'mostre'
    ]

    if any(pattern in query_lower for pattern in realtime_patterns):
        # Try to find a tag via props first, then fall back to regex in the user text
        matched_tag = None
        tag_id = None
        tag_name = None
        unit = ''

        logger.error(f"🔍 PRE-EXECUTE: Query='{query}', available_tags count={len(available_tags) if available_tags else 0}")

        if available_tags:
            logger.error("🔍 Calling find_best_matching_tag...")
            matched_tag = find_best_matching_tag(query, available_tags)
            logger.error(f"🔍 PRE-EXECUTE: Matched tag={matched_tag}")

        if matched_tag:
            tag_id = matched_tag.get('id')
            tag_name = matched_tag.get('name', tag_id)
            unit = matched_tag.get('unit', '')
            logger.info(f"🔍 PRE-EXECUTE: Using matched tag - id={tag_id}, name={tag_name}, unit={unit}")
            # IMPORTANT: Use tag NAME for InfluxDB lookup, not UUID!
            tag_lookup = tag_name if tag_name else tag_id
        else:
            # Heuristic: capture something like "ELEV01_TEMP_C_PV" directly from the prompt
            tag_candidates = re.findall(r'[A-Za-z0-9]+(?:[_\-\.][A-Za-z0-9]+)+', query)
            if tag_candidates:
                tag_lookup = tag_candidates[0]
                tag_name = tag_lookup
                tag_id = tag_lookup
            else:
                tag_lookup = None

        if tag_lookup:
            logger.info(f"🎯 PRE-EXECUTING: get_realtime_value(tag_id={tag_lookup}) [matched from query]")
            result = await toolkit.execute_tool("get_realtime_value", {"tag_id": tag_lookup})

            if result.success and result.data:
                value = result.data.get('value')
                timestamp = result.data.get('timestamp', 'N/A')
                data_results.append(f"**{tag_name}**: {value} {unit} (em {timestamp})")
            else:
                data_results.append(f"**{tag_name or tag_id}**: Sem dados disponíveis")

    # Pattern 2: Statistics queries
    stats_patterns = ['média', 'máximo', 'mínimo', 'estatística', 'últimas', 'últimos']

    if any(pattern in query_lower for pattern in stats_patterns):
        if available_tags and len(available_tags) > 0:
            tag_id = available_tags[0].get('id')
            tag_name = available_tags[0].get('name', tag_id)

            # Extract time period
            duration = "24h"
            if "24 horas" in query_lower or "24h" in query_lower:
                duration = "24h"
            elif "12 horas" in query_lower or "12h" in query_lower:
                duration = "12h"
            elif "semana" in query_lower:
                duration = "168h"

            logger.info(f"🎯 PRE-EXECUTING: calculate_statistics(tag_id={tag_id}, duration={duration})")
            result = await toolkit.execute_tool("calculate_statistics", {"tag_id": tag_id, "duration": duration})

            if result.success and result.data:
                stats = result.data
                data_results.append(f"**Estatísticas de {tag_name} ({duration})**:")
                data_results.append(f"  - Média: {stats.get('mean', 'N/A')}")
                data_results.append(f"  - Mínimo: {stats.get('min', 'N/A')}")
                data_results.append(f"  - Máximo: {stats.get('max', 'N/A')}")
                data_results.append(f"  - Desvio padrão: {stats.get('std_dev', 'N/A')}")
                data_results.append(f"  - Total de leituras: {stats.get('count', 'N/A')}")

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
            tags = result.data.get('tags', [])
            if tags:
                data_results.append(f"**Tags encontradas** ({len(tags)} resultados):")
                for tag in tags[:10]:
                    tag_name = tag.get('name', tag.get('id'))
                    unit = tag.get('unit', '')
                    data_results.append(f"  - {tag_name} ({unit})")
            else:
                data_results.append("**Nenhuma tag encontrada**")

    if data_results:
        return "\n".join(data_results)

    return None


async def call_ollama(messages: List[Dict[str, str]], max_iterations: int = 3) -> str:
    """
    Call Ollama API for chat completion with tool support.
    Optimized for MAXIMUM SPEED with GPU - Target: 3-8 seconds.
    """
    try:
        logger.error(f"🔍 DEBUG: Calling Ollama at {OLLAMA_BASE_URL}")
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
                        "num_predict": 300,  # Shorter responses (was 400)
                        "num_ctx": 1536,     # Smaller context window (was 2048)
                        "num_gpu": 99,       # Force full GPU usage
                        "num_thread": 4,     # Optimize CPU threads
                        "repeat_penalty": 1.1,  # Reduce repetition
                        "stop": ["</response>", "\n\n\n"],  # Early stopping
                    }
                }
            )
            logger.error(f"🔍 DEBUG: Ollama response received - Status: {response.status_code}")
            
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
                        "num_predict": 300,
                        "num_ctx": 1536,
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
            alarms_result = await toolkit.execute_tool("get_active_alarms", {"limit": 50})
            
            if alarms_result.success and alarms_result.data:
                data = alarms_result.data
                alarms = data.get("alarms", [])
                total = data.get("total_alarms", 0)
                
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
    # Check cache first (5-minute TTL, ~8s → <100ms for cached queries)
    from app.core.ai_cache import get_ai_cache
    cache = get_ai_cache()

    cached_response = cache.get(
        message=chat_request.message,
        available_tags=chat_request.available_tags
    )

    if cached_response:
        logger.info(f"⚡ Returning cached response for: '{chat_request.message[:50]}...'")
        return DashboardAgentResponse(**cached_response)

    # DEBUG: Log entrada do endpoint
    logger.error(f"🔍 DEBUG: Starting chat request: '{chat_request.message}'")
    logger.error(f"🔍 DEBUG: Available tags: {len(chat_request.available_tags or [])}")

    # Initialize services
    data_service = DataService(db)
    toolkit = AgentToolkit(data_service)
    
    message_lower = chat_request.message.lower()
    
    # === HYBRID DECISION: Fallback vs Qwen ===
    # Use FALLBACK for simple, direct queries (fast + Portuguese + specialized)
    simple_keywords = [
        'alarme', 'alarm', 'alerta', 'principal', 'crítico', 'urgente',
        'dispositivo', 'device', 'status', 'online', 'offline',
        'olá', 'oi', 'hello', 'help', 'ajuda'
    ]

    # REALTIME VALUE queries - Use fallback for instant response
    realtime_value_keywords = [
        'temperatura atual', 'pressão atual', 'valor atual', 'velocidade atual',
        'qual a temperatura', 'qual a pressão', 'qual o valor', 'qual a velocidade',
        'quanto está', 'quanto é', 'qual está', 'qual é',
        'me mostre o valor', 'mostre a temperatura', 'mostre a pressão'
    ]

    use_fallback = any(keyword in message_lower for keyword in simple_keywords)
    use_fallback_realtime = any(keyword in message_lower for keyword in realtime_value_keywords)
    
    # Use QWEN for complex queries requiring math, logic, or multi-step analysis
    complex_keywords = [
        'média', 'average', 'mean', 'máximo', 'maximum', 'mínimo', 'minimum',
        'comparar', 'compare', 'correlação', 'correlation', 'tendência', 'trend',
        'anomalia', 'anomaly', 'estatística', 'statistic', 'análise', 'analysis',
        'calcul', 'desvio', 'variação', 'predict'
    ]
    
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
    logger.error(f"🔍 DEBUG: Query classification - fallback_realtime={use_fallback_realtime}, complex={use_qwen}, discovery={use_qwen_discovery}")

    # PRIORITY 1: Realtime value queries → Use QWEN with PRE-EXECUTE for data-driven analysis
    # Changed: Realtime queries now use Qwen to ensure 2-step architecture (PostgreSQL → InfluxDB)
    if use_fallback_realtime:
        use_fallback = False
        use_qwen = True
        logger.error("⚡ DEBUG: REALTIME QUERY detected → Using Qwen with PRE-EXECUTE for data fetching")

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

    logger.error(f"🔍 DEBUG: Final classification: fallback={use_fallback}, qwen={use_qwen}, realtime={use_fallback_realtime}")

    if use_fallback:
        logger.error("⚡ DEBUG: Using specialized fallback mode (fast response)")
        return await chat_fallback_mode(chat_request, data_service, toolkit, db)

    # Check if Ollama is available
    logger.error(f"🔍 DEBUG: Checking Ollama availability at {OLLAMA_BASE_URL}")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            logger.error(f"✅ DEBUG: Ollama available - Status {response.status_code}")
    except Exception as e:
        logger.error(f"⚠️ DEBUG: Ollama not available, using fallback mode: {e}")
        return await chat_fallback_mode(chat_request, data_service, toolkit, db)

    # === NEW APPROACH: PRE-EXECUTE TOOLS FIRST ===
    logger.error("🔍 DEBUG: Starting PRE-EXECUTE tools...")
    pre_fetched_data = await pre_execute_tools_from_query(
        query=chat_request.message,
        available_tags=chat_request.available_tags,
        toolkit=toolkit
    )
    logger.error(f"🔍 DEBUG: PRE-EXECUTE complete. Has data: {bool(pre_fetched_data)}")

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

            use_fallback_realtime = any(keyword in message_lower for keyword in realtime_value_keywords)

            # PRIORITY: Realtime queries use PRE-EXECUTE with data-driven prompts
            if use_fallback_realtime:
                use_fallback = False
                use_qwen = True
                logger.info("⚡ STREAMING REALTIME QUERY detected → Using PRE-EXECUTE for data fetching")

            logger.info(f"🌊 Streaming query: fallback={use_fallback}, qwen={use_qwen}, realtime={use_fallback_realtime}")

            # === FALLBACK MODE (Fast, non-streaming) ===
            if use_fallback:
                response = await chat_fallback_mode(chat_request, data_service, toolkit, db)
                # Send as single chunk
                metadata = {"model": "fallback", "mode": "fast"}
                yield f"data: {json.dumps({'chunk': response.response, 'done': True, 'metadata': metadata})}\n\n"
                return

            # === PRE-EXECUTE MODE (for realtime queries) ===
            if use_fallback_realtime:
                logger.error(f"🔍 PRE-EXECUTING tools for streaming realtime query... Query={chat_request.message}, Tags count={len(chat_request.available_tags) if chat_request.available_tags else 0}")
                pre_fetched_data = await pre_execute_tools_from_query(
                    query=chat_request.message,
                    available_tags=chat_request.available_tags,
                    toolkit=toolkit
                )
                logger.error(f"✅ pre_fetched_data result: {pre_fetched_data}")

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
