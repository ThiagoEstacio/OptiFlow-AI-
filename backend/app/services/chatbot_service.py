"""
ChatBot Service with AI

Provides conversational AI for SmartPort process insights using:
- OpenAI GPT-4
- Anthropic Claude
- LangChain for context management
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json

try:
    from langchain.chat_models import ChatOpenAI, ChatAnthropic
    from langchain.schema import HumanMessage, AIMessage, SystemMessage
    from langchain.memory import ConversationBufferMemory
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

logger = logging.getLogger(__name__)


class ChatBotService:
    """
    AI ChatBot for SmartPort process insights

    Capabilities:
    - Answer questions about port operations
    - Analyze PLC data and provide insights
    - Suggest optimizations
    - Explain alarms and anomalies
    """

    def __init__(
        self,
        provider: str = "openai",  # "openai" or "anthropic"
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        temperature: float = 0.7
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.chat_model = None
        self.conversations: Dict[str, List[Dict[str, str]]] = {}

        if HAS_LANGCHAIN and api_key:
            try:
                if provider == "openai":
                    self.chat_model = ChatOpenAI(
                        model_name=model,
                        openai_api_key=api_key,
                        temperature=temperature
                    )
                elif provider == "anthropic":
                    self.chat_model = ChatAnthropic(
                        model=model,
                        anthropic_api_key=api_key,
                        temperature=temperature
                    )

                logger.info(f"Initialized ChatBot with {provider} - {model}")
            except Exception as e:
                logger.error(f"Failed to initialize ChatBot: {e}")
        else:
            if not HAS_LANGCHAIN:
                logger.warning("langchain not installed. Install: pip install langchain openai anthropic")

    def _get_system_prompt(self) -> str:
        """Get system prompt with SmartPort context"""
        return """You are an AI assistant for SmartPort, an intelligent port management system.

Your role is to help port operators by:
1. Analyzing real-time PLC data (cranes, berths, operations)
2. Identifying bottlenecks and inefficiencies
3. Suggesting optimizations for throughput and efficiency
4. Explaining alarms, delays, and anomalies
5. Answering questions about port operations

You have access to:
- Real-time PLC tag values (crane positions, loads, speeds)
- Historical trend data
- Berth occupancy and vessel information
- Operation performance metrics
- Port KPIs (throughput, efficiency, delays)

Always provide:
- Clear, concise explanations
- Data-driven insights
- Actionable recommendations
- Safety considerations when relevant

Format your responses in a professional yet friendly tone."""

    async def chat(
        self,
        user_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a chat message

        Args:
            user_id: User identifier for conversation history
            message: User message
            context: Additional context (PLC data, operations, etc.)

        Returns:
            AI response
        """
        # Initialize conversation for user if not exists
        if user_id not in self.conversations:
            self.conversations[user_id] = []

        # Add user message to history
        self.conversations[user_id].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Use AI model if available
        if self.chat_model:
            try:
                response = await self._chat_with_ai(user_id, message, context)
            except Exception as e:
                logger.error(f"AI chat error: {e}")
                response = self._get_fallback_response(message, context)
        else:
            # Fallback to rule-based responses
            response = self._get_fallback_response(message, context)

        # Add AI response to history
        self.conversations[user_id].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep only last 50 messages
        if len(self.conversations[user_id]) > 50:
            self.conversations[user_id] = self.conversations[user_id][-50:]

        return response

    async def _chat_with_ai(
        self,
        user_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Chat using AI model"""
        messages = [SystemMessage(content=self._get_system_prompt())]

        # Add context if provided
        if context:
            context_msg = self._format_context(context)
            messages.append(SystemMessage(content=f"Current Context:\n{context_msg}"))

        # Add conversation history (last 10 messages)
        history = self.conversations[user_id][-10:]
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        # Get AI response
        response = await self.chat_model.agenerate([messages])
        return response.generations[0][0].text

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context data for AI"""
        formatted = []

        if "plc_data" in context:
            formatted.append("=== Real-time PLC Data ===")
            for tag_name, data in context["plc_data"].items():
                formatted.append(f"{tag_name}: {data['value']} {data.get('unit', '')}")

        if "operations" in context:
            formatted.append("\n=== Active Operations ===")
            for op in context["operations"][:5]:  # Top 5
                formatted.append(
                    f"- {op.get('operation_type')}: "
                    f"{op.get('containers_completed')}/{op.get('containers_planned')} containers, "
                    f"{op.get('efficiency_percentage', 0):.1f}% efficiency"
                )

        if "kpis" in context:
            kpis = context["kpis"]
            formatted.append("\n=== Port KPIs ===")
            formatted.append(f"Berth Occupancy: {kpis.get('berth_occupancy_rate', 0):.1f}%")
            formatted.append(f"Active Operations: {kpis.get('active_operations', 0)}")
            formatted.append(f"Containers Today: {kpis.get('containers_handled_today', 0)}")
            formatted.append(f"Operational Efficiency: {kpis.get('operational_efficiency', 0):.1f}%")

        if "alerts" in context:
            formatted.append("\n=== Current Alerts ===")
            for alert in context["alerts"][:5]:
                formatted.append(f"- [{alert.get('severity')}] {alert.get('message')}")

        return "\n".join(formatted)

    def _get_fallback_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Fallback rule-based responses when AI is unavailable"""
        message_lower = message.lower()

        # Keywords for different topics
        if any(word in message_lower for word in ["crane", "guindaste", "carga"]):
            if context and "plc_data" in context:
                crane_data = {k: v for k, v in context["plc_data"].items() if "crane" in k}
                if crane_data:
                    response = "📊 **Crane Status:**\n\n"
                    for tag, data in crane_data.items():
                        response += f"- **{tag}**: {data['value']} {data.get('unit', '')}\n"
                    return response

            return "I can provide crane status and performance data. Please provide real-time PLC data for analysis."

        elif any(word in message_lower for word in ["berth", "berço", "ocupação"]):
            if context and "kpis" in context:
                kpis = context["kpis"]
                return f"""📍 **Berth Status:**

- Total Berths: {kpis.get('total_berths', 0)}
- Available: {kpis.get('available_berths', 0)}
- Occupied: {kpis.get('occupied_berths', 0)}
- Occupancy Rate: {kpis.get('berth_occupancy_rate', 0):.1f}%

{'⚠️ High occupancy detected!' if kpis.get('berth_occupancy_rate', 0) > 80 else '✅ Occupancy levels are healthy.'}"""

            return "I can analyze berth occupancy and utilization. Please provide current KPI data."

        elif any(word in message_lower for word in ["efficiency", "eficiência", "performance", "desempenho"]):
            if context and "kpis" in context:
                kpis = context["kpis"]
                efficiency = kpis.get('operational_efficiency', 0)
                containers = kpis.get('containers_handled_today', 0)

                return f"""📈 **Performance Metrics:**

- Operational Efficiency: {efficiency:.1f}%
- Containers Handled Today: {containers}
- Average Berthing Time: {kpis.get('average_berthing_time_hours', 0):.1f}h
- Active Operations: {kpis.get('active_operations', 0)}

{'🎯 Excellent performance!' if efficiency > 85 else '💡 Consider optimizing crane assignments to improve efficiency.'}"""

            return "I can analyze operational efficiency and suggest improvements based on current metrics."

        elif any(word in message_lower for word in ["alert", "alerta", "alarm", "alarme", "problem", "problema"]):
            if context and "alerts" in context:
                alerts = context["alerts"]
                if alerts:
                    response = "🚨 **Current Alerts:**\n\n"
                    for alert in alerts[:5]:
                        icon = "🔴" if alert.get('severity') == 'high' else "🟡" if alert.get('severity') == 'medium' else "🔵"
                        response += f"{icon} {alert.get('message')}\n"
                    return response
                else:
                    return "✅ No active alerts. All systems operating normally."

            return "I can help you understand and resolve alerts. Please provide current alert data."

        elif any(word in message_lower for word in ["optimization", "optimize", "otimizar", "improve", "melhorar"]):
            return """💡 **Optimization Suggestions:**

1. **Crane Scheduling**: Analyze crane utilization patterns and adjust assignments dynamically
2. **Berth Allocation**: Use AI to predict optimal berth assignments based on vessel characteristics
3. **Operation Timing**: Identify peak hours and adjust workforce allocation
4. **Preventive Maintenance**: Monitor equipment performance to schedule maintenance proactively

Would you like me to analyze specific data to provide targeted recommendations?"""

        elif any(word in message_lower for word in ["help", "ajuda", "what can you do", "o que você faz"]):
            return """👋 **Hello! I'm your SmartPort AI Assistant.**

I can help you with:

🏭 **Operations**
- Monitor real-time PLC data (cranes, sensors)
- Analyze berth occupancy and vessel status
- Track operation progress and efficiency

📊 **Analytics**
- Identify bottlenecks and inefficiencies
- Provide historical trends and patterns
- Calculate performance metrics

🚨 **Alerts & Issues**
- Explain alarms and anomalies
- Suggest corrective actions
- Predict potential problems

💡 **Optimization**
- Recommend process improvements
- Optimize resource allocation
- Increase throughput and efficiency

Just ask me anything about your port operations!"""

        else:
            return """I'm here to help with SmartPort operations, PLC data analysis, and process optimization.

Try asking me about:
- Crane status and performance
- Berth occupancy
- Operation efficiency
- Current alerts
- Optimization suggestions

How can I assist you today?"""

    def clear_conversation(self, user_id: str):
        """Clear conversation history for a user"""
        if user_id in self.conversations:
            self.conversations[user_id] = []

    def get_conversation(self, user_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a user"""
        return self.conversations.get(user_id, [])


# Global chatbot service instance
# Set api_key from environment variable for production
chatbot_service = ChatBotService(
    provider="openai",  # or "anthropic"
    model="gpt-4",
    api_key=None,  # Will use fallback responses without API key
    temperature=0.7
)
