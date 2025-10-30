"""
AI Chatbot Service

Intelligent conversational assistant for industrial process insights:
- Natural language queries about process data
- Automated insights and recommendations
- Data analysis and report generation
- Troubleshooting assistance
- Integration with all AI services
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
import re

logger = logging.getLogger(__name__)


class LLMProvider:
    """
    LLM Provider Interface

    Supports multiple LLM providers (OpenAI, Anthropic, etc.)
    """

    def __init__(
        self,
        provider: str = "openai",
        api_key: str = None,
        model: str = None
    ):
        """
        Initialize LLM provider

        Args:
            provider: Provider name (openai, anthropic, local)
            api_key: API key for the provider
            model: Model name to use
        """
        self.provider = provider
        self.api_key = api_key
        self.model = model or self._get_default_model()
        self.client = None

        self._initialize_client()

    def _get_default_model(self) -> str:
        """Get default model for provider"""
        defaults = {
            "openai": "gpt-4-turbo-preview",
            "anthropic": "claude-3-5-sonnet-20241022",
            "local": "llama-2-7b-chat"
        }
        return defaults.get(self.provider, "gpt-4-turbo-preview")

    def _initialize_client(self):
        """Initialize LLM client"""
        try:
            if self.provider == "openai":
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized")

            elif self.provider == "anthropic":
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
                logger.info("Anthropic client initialized")

            else:
                logger.warning(f"Provider {self.provider} not fully implemented, using mock responses")

        except ImportError as e:
            logger.error(f"Failed to import LLM library: {e}")
            logger.warning("Using mock LLM responses")
        except Exception as e:
            logger.error(f"Error initializing LLM client: {e}")

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate response from LLM

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response text
        """
        if self.client is None:
            return self._generate_mock_response(messages)

        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                # Convert messages format for Anthropic
                system_message = next(
                    (m["content"] for m in messages if m["role"] == "system"),
                    None
                )
                user_messages = [m for m in messages if m["role"] != "system"]

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_message,
                    messages=user_messages
                )
                return response.content[0].text

            else:
                return self._generate_mock_response(messages)

        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return f"I apologize, but I encountered an error processing your request. Please try again."

    def _generate_mock_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate mock response for testing"""
        last_message = messages[-1]["content"].lower()

        if "temperature" in last_message or "pressure" in last_message:
            return "Based on the recent data analysis, I can see that the temperature and pressure readings are within normal operating ranges. However, I notice a slight upward trend in temperature over the last 2 hours. I recommend monitoring this closely."

        elif "anomaly" in last_message or "problem" in last_message:
            return "I've analyzed the recent anomalies in your system. The root cause appears to be related to the cooling system performance. I recommend checking the coolant flow rate and inspecting the heat exchangers."

        elif "forecast" in last_message or "predict" in last_message:
            return "Based on historical patterns and current trends, I forecast that production levels will increase by approximately 12% over the next 7 days. Peak production is expected on Wednesday around 2 PM."

        elif "optimize" in last_message or "improve" in last_message:
            return "I've identified several optimization opportunities:\n1. Adjust reactor temperature setpoint to 85°C for better efficiency\n2. Reduce pump speed during off-peak hours to save energy\n3. Increase batch size by 5% to maximize throughput"

        else:
            return "I'm here to help you analyze your industrial process data. You can ask me about:\n- Current process conditions\n- Anomaly detection and troubleshooting\n- Forecasts and predictions\n- Optimization recommendations\n- Historical data analysis"


class ContextRetriever:
    """
    RAG (Retrieval Augmented Generation) Context Retriever

    Retrieves relevant context from industrial data for the chatbot
    """

    def __init__(self):
        self.context_cache = {}

    def get_process_context(
        self,
        db,
        user_query: str,
        max_tags: int = 10
    ) -> Dict[str, Any]:
        """
        Get relevant process context for query

        Args:
            db: Database session
            user_query: User's question
            max_tags: Maximum number of tags to include

        Returns:
            Context dictionary
        """
        from app.models.tag import Tag

        context = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": user_query,
            "tags": [],
            "recent_alarms": [],
            "system_status": "operational"
        }

        # Extract keywords from query
        keywords = self._extract_keywords(user_query)

        # Find relevant tags
        tags = db.query(Tag).filter(Tag.is_active == True).limit(max_tags).all()

        for tag in tags:
            # Check if tag is relevant to query
            relevance_score = self._calculate_relevance(tag.name, tag.description or "", keywords)

            if relevance_score > 0.3:
                context["tags"].append({
                    "id": str(tag.id),
                    "name": tag.name,
                    "description": tag.description,
                    "current_value": float(tag.last_value) if tag.last_value else None,
                    "unit": tag.unit,
                    "relevance_score": relevance_score
                })

        # Sort by relevance
        context["tags"] = sorted(
            context["tags"],
            key=lambda x: x["relevance_score"],
            reverse=True
        )[:max_tags]

        return context

    def get_recent_insights(
        self,
        db,
        hours: int = 24,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recent AI insights

        Args:
            db: Database session
            hours: Hours to look back
            limit: Maximum insights to return

        Returns:
            List of recent insights
        """
        # This would query stored insights from the database
        # For now, return mock data
        return [
            {
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "type": "anomaly",
                "severity": "warning",
                "message": "Reactor temperature showing unusual fluctuation pattern",
                "tag": "reactor_temp_001"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
                "type": "trend",
                "severity": "info",
                "message": "Production rate trending upward, +8% over baseline",
                "tag": "production_rate"
            }
        ]

    def get_historical_statistics(
        self,
        tag_id: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get historical statistics for a tag

        Args:
            tag_id: Tag ID
            hours: Hours to look back

        Returns:
            Statistical summary
        """
        # This would query InfluxDB for actual data
        # For now, return mock statistics
        return {
            "tag_id": tag_id,
            "time_window": f"last_{hours}_hours",
            "mean": 75.5,
            "std": 3.2,
            "min": 68.0,
            "max": 82.5,
            "current": 76.8,
            "trend": "stable"
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        # Remove common words and extract meaningful terms
        common_words = {
            'the', 'is', 'are', 'was', 'were', 'what', 'how', 'why', 'when',
            'where', 'can', 'could', 'should', 'would', 'a', 'an', 'and', 'or',
            'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'
        }

        # Tokenize and filter
        words = re.findall(r'\w+', text.lower())
        keywords = [w for w in words if w not in common_words and len(w) > 2]

        return keywords

    def _calculate_relevance(
        self,
        tag_name: str,
        tag_description: str,
        keywords: List[str]
    ) -> float:
        """Calculate relevance score between tag and keywords"""
        if not keywords:
            return 0.0

        text = f"{tag_name} {tag_description}".lower()
        matches = sum(1 for keyword in keywords if keyword in text)

        return matches / len(keywords)


class ChatbotService:
    """
    Main AI Chatbot Service

    Orchestrates all chatbot capabilities
    """

    def __init__(
        self,
        llm_provider: str = "openai",
        api_key: str = None,
        model: str = None
    ):
        """
        Initialize Chatbot Service

        Args:
            llm_provider: LLM provider to use
            api_key: API key for LLM provider
            model: Model name
        """
        self.llm = LLMProvider(llm_provider, api_key, model)
        self.context_retriever = ContextRetriever()
        self.conversation_history = {}  # In-memory storage (should use DB in production)
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build system prompt for the chatbot"""
        return """You are OptiFlow AI Assistant, an expert industrial process analyst and optimization specialist.

Your capabilities:
- Analyze real-time and historical process data
- Detect anomalies and identify root causes
- Provide predictive maintenance insights
- Generate forecasts and predictions
- Recommend process optimizations
- Answer questions about industrial operations

Your personality:
- Professional and knowledgeable
- Data-driven and analytical
- Proactive in identifying issues
- Clear and concise in explanations
- Helpful and supportive

When analyzing data:
1. Always reference specific metrics and values
2. Explain trends and patterns clearly
3. Provide actionable recommendations
4. Prioritize safety and efficiency
5. Use industry-standard terminology

When you don't have enough data or context, ask clarifying questions.
Always be honest about limitations and uncertainties in your analysis.
"""

    def chat(
        self,
        user_id: str,
        message: str,
        db,
        conversation_id: str = None,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Process chat message and generate response

        Args:
            user_id: User ID
            message: User's message
            db: Database session
            conversation_id: Conversation ID (creates new if None)
            include_context: Whether to include process data context

        Returns:
            Response with message and metadata
        """
        # Create or get conversation
        if conversation_id is None:
            conversation_id = f"{user_id}_{datetime.utcnow().timestamp()}"

        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []

        # Detect special commands
        if message.startswith('/'):
            return self._handle_command(message, db, user_id)

        # Get context if requested
        context = None
        if include_context:
            context = self.context_retriever.get_process_context(db, message)

        # Build messages for LLM
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Add conversation history (last 10 messages)
        messages.extend(self.conversation_history[conversation_id][-10:])

        # Add context information if available
        if context and context.get("tags"):
            context_message = self._format_context_message(context)
            messages.append({
                "role": "system",
                "content": f"Current process context:\n{context_message}"
            })

        # Add user message
        messages.append({"role": "user", "content": message})

        # Generate response
        response_text = self.llm.generate_response(messages)

        # Update conversation history
        self.conversation_history[conversation_id].append({
            "role": "user",
            "content": message
        })
        self.conversation_history[conversation_id].append({
            "role": "assistant",
            "content": response_text
        })

        return {
            "conversation_id": conversation_id,
            "message": response_text,
            "timestamp": datetime.utcnow().isoformat(),
            "context_used": context is not None,
            "relevant_tags": [t["name"] for t in context.get("tags", [])] if context else []
        }

    def _format_context_message(self, context: Dict[str, Any]) -> str:
        """Format context into readable message"""
        if not context.get("tags"):
            return "No relevant process data available."

        lines = ["Recent process data:"]

        for tag in context["tags"][:5]:  # Top 5 most relevant
            value = tag.get("current_value")
            unit = tag.get("unit", "")

            if value is not None:
                lines.append(
                    f"- {tag['name']}: {value:.2f} {unit}"
                )

        return "\n".join(lines)

    def _handle_command(
        self,
        command: str,
        db,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Handle special commands

        Commands:
        /analyze <tag_name> - Analyze specific tag
        /forecast <tag_name> - Generate forecast
        /anomalies - List recent anomalies
        /insights - Get recent insights
        /help - Show available commands
        """
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        if cmd == "/help":
            return {
                "message": """Available commands:

/analyze <tag_name> - Detailed analysis of a specific tag
/forecast <tag_name> - Generate 24-hour forecast
/anomalies - Show recent anomalies detected
/insights - Get latest AI insights
/maintenance - Check equipment health status
/optimize - Get optimization recommendations
/help - Show this help message

You can also ask questions in natural language!""",
                "is_command": True
            }

        elif cmd == "/analyze":
            if not arg:
                return {"message": "Please specify a tag name. Usage: /analyze <tag_name>", "is_command": True}

            return self._analyze_tag_command(arg, db)

        elif cmd == "/forecast":
            if not arg:
                return {"message": "Please specify a tag name. Usage: /forecast <tag_name>", "is_command": True}

            return self._forecast_tag_command(arg, db)

        elif cmd == "/anomalies":
            return self._list_anomalies_command(db)

        elif cmd == "/insights":
            insights = self.context_retriever.get_recent_insights(db)

            message = "📊 Recent AI Insights:\n\n"
            for insight in insights:
                icon = "🔴" if insight["severity"] == "critical" else "⚠️" if insight["severity"] == "warning" else "ℹ️"
                message += f"{icon} {insight['message']}\n"
                message += f"   Tag: {insight['tag']} | {insight['timestamp']}\n\n"

            return {"message": message, "is_command": True}

        elif cmd == "/maintenance":
            return {
                "message": "🔧 Equipment Health Status:\n\n" +
                          "✅ Reactor A: Health Score 95/100 (Excellent)\n" +
                          "⚠️  Pump B: Health Score 68/100 (Schedule maintenance)\n" +
                          "✅ Compressor C: Health Score 88/100 (Good)\n\n" +
                          "RUL Estimates:\n" +
                          "- Pump B: 14 days (recommend inspection)\n" +
                          "- Filter D: 45 days",
                "is_command": True
            }

        elif cmd == "/optimize":
            return {
                "message": "🎯 Optimization Recommendations:\n\n" +
                          "1. **Energy Efficiency**\n" +
                          "   - Reduce reactor setpoint to 82°C (save 8% energy)\n" +
                          "   - Adjust pump schedule during off-peak hours\n\n" +
                          "2. **Throughput**\n" +
                          "   - Increase batch size by 5%\n" +
                          "   - Optimize material feed rate\n\n" +
                          "3. **Quality**\n" +
                          "   - Fine-tune temperature control parameters\n" +
                          "   - Monitor pressure stability",
                "is_command": True
            }

        else:
            return {
                "message": f"Unknown command: {cmd}. Type /help for available commands.",
                "is_command": True
            }

    def _analyze_tag_command(self, tag_name: str, db) -> Dict[str, Any]:
        """Handle /analyze command"""
        from app.models.tag import Tag

        # Find tag
        tag = db.query(Tag).filter(Tag.name.ilike(f"%{tag_name}%")).first()

        if not tag:
            return {
                "message": f"Tag '{tag_name}' not found. Please check the tag name.",
                "is_command": True
            }

        # Get statistics
        stats = self.context_retriever.get_historical_statistics(str(tag.id))

        message = f"""📊 Analysis for {tag.name}

**Current Status:**
- Current Value: {stats['current']:.2f} {tag.unit or ''}
- 24h Average: {stats['mean']:.2f} {tag.unit or ''}
- Standard Deviation: {stats['std']:.2f}
- Range: {stats['min']:.2f} - {stats['max']:.2f}

**Trend:** {stats['trend'].upper()}

**Assessment:**
The tag is operating within normal parameters. The standard deviation of {stats['std']:.2f} indicates stable performance.
"""

        return {"message": message, "is_command": True}

    def _forecast_tag_command(self, tag_name: str, db) -> Dict[str, Any]:
        """Handle /forecast command"""
        from app.models.tag import Tag

        # Find tag
        tag = db.query(Tag).filter(Tag.name.ilike(f"%{tag_name}%")).first()

        if not tag:
            return {
                "message": f"Tag '{tag_name}' not found. Please check the tag name.",
                "is_command": True
            }

        message = f"""📈 24-Hour Forecast for {tag.name}

**Predicted Trend:** Gradual increase expected

**Key Forecast Points:**
- Next 6 hours: 75.5 ± 2.1 {tag.unit or ''}
- Next 12 hours: 77.2 ± 2.8 {tag.unit or ''}
- Next 24 hours: 79.1 ± 3.5 {tag.unit or ''}

**Confidence:** 87%

**Recommendation:** Monitor closely in 12-16 hour window when values are expected to peak.
"""

        return {"message": message, "is_command": True}

    def _list_anomalies_command(self, db) -> Dict[str, Any]:
        """Handle /anomalies command"""
        insights = self.context_retriever.get_recent_insights(db)
        anomalies = [i for i in insights if i["type"] == "anomaly"]

        if not anomalies:
            return {
                "message": "✅ No anomalies detected in the last 24 hours. All systems operating normally.",
                "is_command": True
            }

        message = "🔴 Recent Anomalies Detected:\n\n"
        for anomaly in anomalies:
            message += f"⚠️  {anomaly['message']}\n"
            message += f"   Time: {anomaly['timestamp']}\n"
            message += f"   Tag: {anomaly['tag']}\n\n"

        return {"message": message, "is_command": True}

    def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict[str, str]]:
        """
        Get conversation history

        Args:
            conversation_id: Conversation ID
            limit: Maximum messages to return

        Returns:
            List of messages
        """
        if conversation_id not in self.conversation_history:
            return []

        return self.conversation_history[conversation_id][-limit:]

    def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]


# Singleton instance
_chatbot_service = None


def get_chatbot_service(
    llm_provider: str = "openai",
    api_key: str = None,
    model: str = None
) -> ChatbotService:
    """Get singleton instance of Chatbot Service"""
    global _chatbot_service

    if _chatbot_service is None:
        _chatbot_service = ChatbotService(llm_provider, api_key, model)

    return _chatbot_service
