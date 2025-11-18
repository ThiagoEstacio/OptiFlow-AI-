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
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import json
import re
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address

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


# Ultra-compact system prompt optimized for SPEED with GPU
SYSTEM_PROMPT_TEMPLATE = """OptiFlow AI - Analista PCM/PCO Industrial

{tools}

## REGRAS
1. SEMPRE chame ferramentas para dados reais
2. Use Markdown com emojis (🔴🟠🟡🟢)
3. Responda em PORTUGUÊS
4. Seja conciso e técnico

## FORMATO
- 📊 Situação (dados + unidades)
- 🔍 Análise (o que significa)
- ⚡ Impacto (risco, OEE)
- 💡 Ações (específicas)

Ferramentas:
```tool
{{"name": "ferramenta", "arguments": {{"param": "valor"}}}}
```

Exemplos de chamadas:
- Alarmes: get_active_alarms
- Tags: search_tags({"query": "temperatura"})
- Valor atual: get_realtime_value({"tag_id": "uuid"})
- Estatísticas: calculate_statistics({"tag_id": "uuid", "period": "24h"})"""


async def call_ollama(messages: List[Dict[str, str]], max_iterations: int = 3) -> str:
    """
    Call Ollama API for chat completion with tool support.
    Optimized for MAXIMUM SPEED with GPU.
    """
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": MODEL_NAME,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Maximum focus, fastest inference
                        "top_p": 0.85,      # Slightly more deterministic
                        "num_predict": 400,  # Shorter responses = faster (was 800)
                        "num_ctx": 2048,     # Reduced context window = faster (was 3072)
                        "num_gpu": 99,       # Force full GPU usage
                        "num_thread": 4,     # Optimize CPU threads
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
    
    use_fallback = any(keyword in message_lower for keyword in simple_keywords)
    
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
    
    # Discovery queries ALWAYS use Qwen (need tools)
    if use_qwen_discovery:
        use_qwen = True
        use_fallback = False
    
    # If both or neither match, default based on message complexity
    if not use_fallback and not use_qwen:
        # Short messages (<20 words) → fallback
        # Long/complex messages → Qwen
        word_count = len(request.message.split())
        use_fallback = word_count < 20
        use_qwen = not use_fallback
    
    # Override: If specifically needs calculation/analysis, always use Qwen
    if use_qwen and use_fallback:
        use_qwen = True
        use_fallback = False
    
    logger.info(f"🤖 Query classification: fallback={use_fallback}, qwen={use_qwen}, message='{request.message[:50]}'")
    
    if use_fallback:
        logger.info("⚡ Using specialized fallback mode (fast response)")
        return await chat_fallback_mode(request, data_service, toolkit, db)
    
    # Check if Ollama is available
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        logger.info("✅ Ollama available - Using QWEN 2.5:7B with full tool-calling")
    except Exception as e:
        logger.warning(f"⚠️ Ollama not available, using fallback mode: {e}")
        return await chat_fallback_mode(request, data_service, toolkit, db)
    
    # Build system prompt with available tools
    tools_description = format_tools_for_prompt(toolkit.get_tool_definitions())
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(tools=tools_description)
    
    # Build messages for Ollama - MINIMAL context for speed
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Skip context to reduce tokens and speed up inference
    # (context adds ~200-500 tokens, slows down GPU processing)
    
    # Add user message
    messages.append({"role": "user", "content": request.message})
    
    # Multi-turn conversation with tool support - REDUCED for speed
    max_iterations = 2  # Was 3, now 2 for faster response
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
