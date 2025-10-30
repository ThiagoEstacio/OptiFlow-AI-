"""
AI Service for chatbot functionality using OpenAI API.
Provides intelligent insights and assistance for OptiFlow platform.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.device import Device, DeviceStatus
from app.models.tag import Tag
from app.models.alarm import AlarmEvent, AlarmState
from app.models.chat import Message, MessageRole
from app.core.config import settings


class AIService:
    """
    Service for AI-powered chatbot functionality.
    Uses OpenAI API to provide intelligent responses and insights.
    """

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> str:
        """
        Generate AI response using OpenAI API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            context: Additional context for the AI
            stream: Whether to stream the response

        Returns:
            Generated response text
        """
        try:
            # If OpenAI API key is not configured, return a helpful default response
            if not self.api_key:
                return self._get_fallback_response(messages, context)

            # Import openai only when needed
            import openai
            openai.api_key = self.api_key

            # Prepare system message with context
            system_message = self._build_system_message(context)

            # Combine system message with conversation messages
            full_messages = [
                {"role": "system", "content": system_message}
            ] + messages

            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=full_messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=stream
            )

            if stream:
                return response
            else:
                return response.choices[0].message.content

        except Exception as e:
            print(f"Error generating AI response: {str(e)}")
            return self._get_fallback_response(messages, context)

    def _build_system_message(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Build system message with OptiFlow platform context.
        """
        base_message = """You are OptiFlow AI Assistant, an intelligent helper for the OptiFlow Industrial IoT Platform.

Your capabilities:
- Analyze industrial device data, alarms, and time-series metrics
- Provide insights on device performance and health
- Help troubleshoot issues with PLCs, sensors, and industrial equipment
- Suggest optimizations for industrial processes
- Answer questions about the platform and its features
- Generate actionable recommendations based on data trends

Guidelines:
- Be concise but informative
- Focus on actionable insights
- Use technical terminology appropriately
- When discussing data, provide specific numbers and trends
- Always prioritize safety and operational efficiency
- If you're not certain about something, say so clearly
"""

        if context:
            context_info = "\n\nCurrent Context:\n"

            if "devices_summary" in context:
                context_info += f"\nDevices: {context['devices_summary']}"

            if "alarms_summary" in context:
                context_info += f"\nActive Alarms: {context['alarms_summary']}"

            if "organization" in context:
                context_info += f"\nOrganization: {context['organization']['name']}"

            if "site" in context:
                context_info += f"\nSite: {context['site']['name']}"

            if "time_range" in context:
                context_info += f"\nTime Range: {context['time_range']}"

            base_message += context_info

        return base_message

    def _get_fallback_response(
        self,
        messages: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Provide fallback response when OpenAI API is not available.
        """
        last_message = messages[-1]["content"].lower() if messages else ""

        # Simple pattern matching for common queries
        if any(word in last_message for word in ["hello", "hi", "hey", "olá"]):
            return "Olá! Sou o OptiFlow AI Assistant. Como posso ajudá-lo com seus dispositivos industriais e dados hoje?"

        if any(word in last_message for word in ["device", "dispositivo", "plc", "sensor"]):
            if context and "devices_summary" in context:
                return f"Baseado nos dados atuais: {context['devices_summary']}. Configure a variável de ambiente OPENAI_API_KEY para análises mais detalhadas."
            return "Para análises detalhadas de dispositivos, configure a variável de ambiente OPENAI_API_KEY com sua chave da API OpenAI."

        if any(word in last_message for word in ["alarm", "alarme", "alert"]):
            if context and "alarms_summary" in context:
                return f"Status de alarmes: {context['alarms_summary']}. Para insights mais profundos, configure a integração com OpenAI."
            return "Para análise de alarmes em tempo real, configure a variável de ambiente OPENAI_API_KEY."

        return """OptiFlow AI Assistant está disponível!

Para ativar todas as funcionalidades de IA, configure as seguintes variáveis de ambiente:
- OPENAI_API_KEY: Sua chave da API OpenAI
- OPENAI_MODEL (opcional): Modelo a usar (padrão: gpt-4-turbo-preview)

Enquanto isso, posso ajudá-lo com:
- Visualização de status de dispositivos
- Consulta de dados históricos
- Gerenciamento de alarmes
- Navegação na plataforma

Como posso ajudá-lo?"""

    async def get_platform_context(
        self,
        db: AsyncSession,
        organization_id: str,
        include_devices: bool = True,
        include_alarms: bool = True,
        site_id: Optional[str] = None,
        time_range: str = "24h"
    ) -> Dict[str, Any]:
        """
        Gather platform context for AI responses.

        Args:
            db: Database session
            organization_id: Organization ID
            include_devices: Include device summary
            include_alarms: Include alarm summary
            site_id: Optional site ID to filter
            time_range: Time range for data (e.g., "24h", "7d")

        Returns:
            Context dictionary
        """
        context = {
            "organization_id": organization_id,
            "time_range": time_range
        }

        try:
            # Get device summary
            if include_devices:
                query = select(
                    Device.status,
                    func.count(Device.id).label("count")
                ).where(Device.organization_id == organization_id)

                if site_id:
                    query = query.where(Device.site_id == site_id)

                query = query.group_by(Device.status)
                result = await db.execute(query)
                device_stats = result.all()

                devices_summary = {str(status): count for status, count in device_stats}
                total_devices = sum(devices_summary.values())

                context["devices_summary"] = {
                    "total": total_devices,
                    "by_status": devices_summary,
                    "connected": devices_summary.get("CONNECTED", 0),
                    "disconnected": devices_summary.get("DISCONNECTED", 0),
                    "error": devices_summary.get("ERROR", 0)
                }

            # Get alarm summary
            if include_alarms:
                # Get active alarms
                query = select(
                    func.count(AlarmEvent.id)
                ).where(
                    AlarmEvent.state == AlarmState.ACTIVE
                )

                result = await db.execute(query)
                active_alarms = result.scalar() or 0

                context["alarms_summary"] = {
                    "active": active_alarms
                }

        except Exception as e:
            print(f"Error gathering platform context: {str(e)}")

        return context

    async def generate_insights(
        self,
        db: AsyncSession,
        organization_id: str,
        query: str,
        scope: str = "organization",
        entity_id: Optional[str] = None,
        time_range: str = "24h"
    ) -> Dict[str, Any]:
        """
        Generate AI insights based on platform data.

        Args:
            db: Database session
            organization_id: Organization ID
            query: Natural language query
            scope: Scope of analysis (organization, site, device)
            entity_id: ID of specific entity (site or device)
            time_range: Time range for analysis

        Returns:
            Insights dictionary
        """
        # Gather context
        context = await self.get_platform_context(
            db,
            organization_id,
            include_devices=True,
            include_alarms=True,
            site_id=entity_id if scope == "site" else None,
            time_range=time_range
        )

        # Build message for AI
        messages = [
            {
                "role": "user",
                "content": f"Analyze the following and provide insights: {query}"
            }
        ]

        # Generate response
        response = await self.generate_response(messages, context)

        # Parse insights
        insights = {
            "insights": [response],
            "data_summary": context,
            "recommendations": [],
            "visualizations": []
        }

        return insights

    def generate_suggestions(
        self,
        conversation_messages: List[Message]
    ) -> List[str]:
        """
        Generate suggested follow-up questions based on conversation history.

        Args:
            conversation_messages: List of messages in the conversation

        Returns:
            List of suggested questions
        """
        # Default suggestions
        default_suggestions = [
            "Quais dispositivos estão offline?",
            "Mostre-me os alarmes ativos",
            "Como está a performance do sistema?",
            "Quais são as tendências de dados nas últimas 24 horas?"
        ]

        if not conversation_messages or len(conversation_messages) < 2:
            return default_suggestions

        # Context-aware suggestions based on last message
        last_message = conversation_messages[-1].content.lower()

        if any(word in last_message for word in ["device", "dispositivo", "plc"]):
            return [
                "Quais são os dispositivos com mais erros?",
                "Mostre detalhes de conexão dos dispositivos",
                "Há dispositivos que precisam de manutenção?",
                "Qual é a taxa de disponibilidade dos dispositivos?"
            ]

        if any(word in last_message for word in ["alarm", "alarme", "alert"]):
            return [
                "Quais são os alarmes mais críticos?",
                "Mostre o histórico de alarmes",
                "Há padrões nos alarmes recentes?",
                "Como posso reduzir alarmes falsos?"
            ]

        if any(word in last_message for word in ["performance", "desempenho", "otimizar"]):
            return [
                "Quais processos podem ser otimizados?",
                "Mostre gargalos de produção",
                "Como melhorar a eficiência?",
                "Há oportunidades de economia de energia?"
            ]

        return default_suggestions
