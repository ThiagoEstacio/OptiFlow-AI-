"""
Integração do Autonomous Agent com ML Insights

Este módulo facilita a integração do Autonomous Agent com o serviço de ML Insights,
permitindo que o agent gere insights automáticos e tome ações baseadas neles.

Uso no Autonomous Agent:
    from app.services.agent_ml_integration import AgentMLIntegration

    # Inicializar
    ml_integration = AgentMLIntegration()

    # Gerar insights
    insights = await ml_integration.get_insights_for_agent(
        db=db,
        organization_id=org_id
    )

    # Processar e responder
    response = await ml_integration.generate_agent_response(insights)
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.services.ml_insights_service import ml_insights_service

logger = logging.getLogger(__name__)


class AgentMLIntegration:
    """
    Facilitador de integração entre Autonomous Agent e ML Insights

    Fornece métodos de alto nível para que o Agent consuma insights ML
    e gere respostas contextualizadas
    """

    def __init__(self):
        self.last_insights = {}
        self.alert_history = []

    async def get_insights_for_agent(
        self,
        db: AsyncSession,
        organization_id: str,
        time_range: str = 'last_7_days',
        include_summary_only: bool = False
    ) -> Dict[str, Any]:
        """
        Obtém insights ML formatados para o Agent

        Args:
            db: Database session
            organization_id: ID da organização
            time_range: Período de análise
            include_summary_only: Se True, retorna apenas sumário

        Returns:
            Dict com insights processados para o Agent
        """
        try:
            # Gerar insights
            insights = await ml_insights_service.generate_all_insights(
                db=db,
                organization_id=organization_id,
                time_range=time_range
            )

            # Armazenar para histórico
            self.last_insights[organization_id] = {
                'timestamp': datetime.now(),
                'insights': insights
            }

            # Se apenas sumário
            if include_summary_only:
                return {
                    'summary': insights['summary'],
                    'generated_at': insights['generated_at'],
                    'time_range': insights['time_range']
                }

            return insights

        except Exception as e:
            logger.error(f"Erro ao obter insights para agent: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }

    async def check_critical_alerts(
        self,
        db: AsyncSession,
        organization_id: str
    ) -> List[Dict[str, Any]]:
        """
        Verifica alertas críticos que requerem ação imediata

        Returns:
            Lista de alertas críticos com prioridade
        """
        insights = await self.get_insights_for_agent(db, organization_id, time_range='last_24h')

        if 'error' in insights:
            return []

        critical_alerts = []

        # 1. Verificar reliability (manutenções urgentes)
        reliability = insights['insights'].get('reliability')
        if reliability and reliability.get('status') == 'success':
            for eq in reliability.get('critical_equipment', []):
                critical_alerts.append({
                    'type': 'maintenance_critical',
                    'priority': 'high',
                    'equipment_id': eq['equipment_id'],
                    'message': f"MTBF crítico: {eq['mtbf_hours']:.1f}h",
                    'action': 'schedule_maintenance',
                    'details': eq
                })

        # 2. Verificar energy (consumo anormal)
        energy = insights['insights'].get('energy_prediction')
        if energy and energy.get('status') == 'success':
            if energy.get('abnormal_consumption'):
                critical_alerts.append({
                    'type': 'energy_abnormal',
                    'priority': 'medium',
                    'message': f"Consumo anormal: {energy['current_consumption_kwh']:.1f} kWh",
                    'action': 'investigate_consumption',
                    'details': energy
                })

        # 3. Verificar anomalies (múltiplas anomalias)
        anomalies = insights['insights'].get('anomalies')
        if anomalies and anomalies.get('status') == 'success':
            if anomalies.get('recent_anomalies', 0) > 5:
                critical_alerts.append({
                    'type': 'anomalies_multiple',
                    'priority': 'high',
                    'message': f"{anomalies['recent_anomalies']} anomalias nas últimas 24h",
                    'action': 'investigate_anomalies',
                    'details': anomalies
                })

        # Ordenar por prioridade
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        critical_alerts.sort(key=lambda x: priority_order.get(x['priority'], 3))

        # Armazenar histórico
        self.alert_history.extend(critical_alerts)

        return critical_alerts

    async def generate_agent_response(
        self,
        insights: Dict[str, Any],
        question: Optional[str] = None
    ) -> str:
        """
        Gera resposta contextualizada do Agent baseada nos insights

        Args:
            insights: Insights ML gerados
            question: Pergunta opcional do usuário

        Returns:
            Resposta formatada em markdown
        """
        if 'error' in insights:
            return f"❌ Não foi possível gerar insights: {insights['error']}"

        summary = insights.get('summary', {})

        # Resposta base
        response = f"""
## 📊 Análise ML/DS - OptiFlow AI

**Gerado em**: {insights.get('generated_at', 'N/A')}
**Período**: {insights.get('time_range', 'N/A')}

### 📈 Sumário Executivo

- **Total de Insights**: {summary.get('total_insights', 0)}
- **Alertas Ativos**: {summary.get('total_alerts', 0)}
- **Severidade**: {summary.get('severity', 'unknown').upper()}
- **Status Geral**: {summary.get('status', 'unknown')}

"""

        # Se há alertas
        if summary.get('total_alerts', 0) > 0:
            response += "### ⚠️ Alertas Requerendo Atenção\n\n"

            for insight_type, insight_data in insights['insights'].items():
                if insight_data and 'alerts' in insight_data and insight_data['alerts']:
                    response += f"\n**{insight_type.replace('_', ' ').title()}**:\n"
                    for alert in insight_data['alerts']:
                        response += f"- {alert}\n"

        # Recomendações principais
        if summary.get('top_recommendations'):
            response += "\n### 💡 Principais Recomendações\n\n"
            for rec in summary['top_recommendations'][:5]:
                response += f"- {rec}\n"

        # Adicionar detalhes específicos baseados na pergunta
        if question:
            response += self._add_contextual_details(insights, question)

        return response

    def _add_contextual_details(self, insights: Dict[str, Any], question: str) -> str:
        """Adiciona detalhes contextuais baseados na pergunta"""
        question_lower = question.lower()
        details = "\n### 🔍 Detalhes Adicionais\n\n"

        # Energia
        if any(word in question_lower for word in ['energia', 'consumo', 'energy']):
            energy = insights['insights'].get('energy_prediction')
            if energy and energy.get('status') == 'success':
                details += f"""
**Previsão de Energia**:
- Consumo Atual: {energy.get('current_consumption_kwh', 0):.1f} kWh
- Tendência: {energy.get('trend', 'N/A')}
- Previsão 24h: {len(energy.get('predicted_24h', []))} horas mapeadas
"""

        # Eficiência
        elif any(word in question_lower for word in ['eficiência', 'efficiency']):
            efficiency = insights['insights'].get('efficiency')
            if efficiency and efficiency.get('status') == 'success':
                details += f"""
**Análise de Eficiência**:
- Eficiência Atual: {efficiency.get('current_efficiency_kwh_per_ton', 0):.2f} kWh/ton
- Média: {efficiency.get('mean_efficiency_kwh_per_ton', 0):.2f} kWh/ton
- Status: {efficiency.get('efficiency_status', 'N/A')}
"""

        # Manutenção
        elif any(word in question_lower for word in ['manutenção', 'maintenance', 'mtbf', 'mttr']):
            reliability = insights['insights'].get('reliability')
            if reliability and reliability.get('status') == 'success':
                critical_count = len(reliability.get('critical_equipment', []))
                details += f"""
**Análise de Confiabilidade**:
- Equipamentos Críticos: {critical_count}
- Manutenções Previstas: {len(reliability.get('next_maintenances', []))}
"""

        # Anomalias
        elif any(word in question_lower for word in ['anomalia', 'anomaly', 'problema', 'falha']):
            anomalies = insights['insights'].get('anomalies')
            if anomalies and anomalies.get('status') == 'success':
                details += f"""
**Detecção de Anomalias**:
- Total de Anomalias: {anomalies.get('total_anomalies', 0)}
- Anomalias Recentes (24h): {anomalies.get('recent_anomalies', 0)}
- Taxa de Anomalia: {anomalies.get('anomaly_rate', 0)*100:.1f}%
"""

        # Custos
        elif any(word in question_lower for word in ['custo', 'economia', 'cost', 'saving']):
            cost = insights['insights'].get('cost_optimization')
            if cost and cost.get('status') == 'success':
                details += f"""
**Otimização de Custos**:
- Economia Potencial (Mensal): R$ {cost.get('potential_savings_monthly', 0):.2f}
- Economia Anual: R$ {cost.get('potential_savings_yearly', 0):.2f}
- Percentual: {cost.get('savings_percentage', 0):.1f}%
"""

        return details if len(details) > 50 else ""

    async def get_recommendations_for_action(
        self,
        db: AsyncSession,
        organization_id: str,
        action_type: str
    ) -> List[str]:
        """
        Obtém recomendações específicas para um tipo de ação

        Args:
            action_type: Tipo de ação ('maintenance', 'energy', 'cost', etc.)

        Returns:
            Lista de recomendações específicas
        """
        insights = await self.get_insights_for_agent(db, organization_id)

        if 'error' in insights:
            return []

        recommendations = []

        # Mapear tipo de ação para insight
        action_to_insight = {
            'maintenance': 'reliability',
            'energy': 'energy_prediction',
            'efficiency': 'efficiency',
            'anomaly': 'anomalies',
            'cost': 'cost_optimization'
        }

        insight_key = action_to_insight.get(action_type)
        if insight_key:
            insight_data = insights['insights'].get(insight_key)
            if insight_data and 'recommendations' in insight_data:
                recommendations = insight_data['recommendations']

        return recommendations

    async def get_insight_trend(
        self,
        organization_id: str,
        metric: str
    ) -> Dict[str, Any]:
        """
        Obtém tendência de uma métrica ao longo do tempo

        Args:
            metric: Métrica a analisar ('energy', 'efficiency', 'anomalies', etc.)

        Returns:
            Dict com dados de tendência
        """
        # TODO: Implementar análise de tendência histórica
        # Por enquanto, retorna último insight
        last = self.last_insights.get(organization_id)

        if not last:
            return {'status': 'no_data'}

        insight_data = last['insights']['insights'].get(metric)

        return {
            'status': 'success',
            'timestamp': last['timestamp'],
            'current_value': insight_data,
            'trend': 'stable'  # TODO: calcular tendência real
        }

    async def schedule_periodic_monitoring(
        self,
        db: AsyncSession,
        organization_id: str,
        interval_minutes: int = 60,
        callback_fn = None
    ):
        """
        Agenda monitoramento periódico de insights

        Args:
            interval_minutes: Intervalo entre checks (default: 60 min)
            callback_fn: Função a chamar quando houver alertas críticos
        """
        logger.info(f"Iniciando monitoramento periódico a cada {interval_minutes} minutos")

        while True:
            try:
                # Verificar alertas críticos
                alerts = await self.check_critical_alerts(db, organization_id)

                if alerts and callback_fn:
                    # Chamar callback com alertas
                    await callback_fn(alerts)

                # Aguardar intervalo
                await asyncio.sleep(interval_minutes * 60)

            except Exception as e:
                logger.error(f"Erro no monitoramento periódico: {e}")
                await asyncio.sleep(60)  # Aguardar 1 min antes de tentar novamente


# Singleton instance
agent_ml_integration = AgentMLIntegration()


# Exemplo de uso no Autonomous Agent
async def example_agent_usage():
    """
    Exemplo de como o Autonomous Agent deve usar esta integração
    """
    from app.db.session import get_db

    async for db in get_db():
        org_id = "your-org-id"

        # 1. Obter insights gerais
        insights = await agent_ml_integration.get_insights_for_agent(
            db=db,
            organization_id=org_id,
            time_range='last_7_days'
        )

        # 2. Gerar resposta para usuário
        response = await agent_ml_integration.generate_agent_response(
            insights=insights,
            question="Como está o consumo de energia?"
        )
        print(response)

        # 3. Verificar alertas críticos
        alerts = await agent_ml_integration.check_critical_alerts(db, org_id)

        for alert in alerts:
            if alert['priority'] == 'high':
                print(f"⚠️ ALERTA CRÍTICO: {alert['message']}")
                # Tomar ação...

        # 4. Obter recomendações específicas
        energy_recs = await agent_ml_integration.get_recommendations_for_action(
            db=db,
            organization_id=org_id,
            action_type='energy'
        )

        print("Recomendações de Energia:")
        for rec in energy_recs:
            print(f"  - {rec}")

        break  # Apenas um exemplo
