# 🤖 Guia de Integração - Autonomous Agent + ML Insights

**Data**: 2025-11-06
**Versão**: 1.0
**Status**: ✅ Pronto para Implementação

---

## 📋 Visão Geral

Este guia mostra como integrar o Autonomous Agent do OptiFlow AI com o sistema de ML Insights para gerar insights automáticos e tomar ações baseadas em dados.

### O Que Foi Implementado ✅

1. ✅ **MLInsightsService** - 6 modelos ML/DS funcionais
2. ✅ **9 Endpoints REST** - API completa para consumir insights
3. ✅ **AgentMLIntegration** - Facilitador de integração para o Agent
4. ✅ **Dados Sintéticos** - Sistema funciona sem dados reais
5. ✅ **Documentação Completa** - Guias e exemplos

---

## 🚀 Início Rápido

### Passo 1: Importar o Módulo de Integração

```python
# No código do Autonomous Agent
from app.services.agent_ml_integration import agent_ml_integration
from app.db.session import get_db
```

### Passo 2: Obter Insights

```python
# Dentro de uma função async do Agent
async def get_ml_insights(organization_id: str):
    async for db in get_db():
        # Obter todos os insights
        insights = await agent_ml_integration.get_insights_for_agent(
            db=db,
            organization_id=organization_id,
            time_range='last_7_days'
        )

        return insights
```

### Passo 3: Gerar Resposta Contextualizada

```python
# Processar insights e gerar resposta
async def answer_with_ml(question: str, organization_id: str):
    async for db in get_db():
        # Obter insights
        insights = await agent_ml_integration.get_insights_for_agent(
            db=db,
            organization_id=organization_id
        )

        # Gerar resposta contextualizada
        response = await agent_ml_integration.generate_agent_response(
            insights=insights,
            question=question
        )

        return response
```

---

## 💡 Casos de Uso

### Caso 1: Monitoramento Proativo

O Agent verifica periodicamente por alertas críticos:

```python
async def monitor_critical_alerts(organization_id: str):
    """Agent monitora alertas a cada hora"""
    async for db in get_db():
        while True:
            # Verificar alertas críticos
            alerts = await agent_ml_integration.check_critical_alerts(
                db=db,
                organization_id=organization_id
            )

            # Processar alertas
            for alert in alerts:
                if alert['priority'] == 'high':
                    # Enviar notificação
                    await send_notification(
                        title=f"⚠️ Alerta Crítico: {alert['type']}",
                        message=alert['message'],
                        priority='high'
                    )

                    # Tomar ação baseada no tipo
                    if alert['type'] == 'maintenance_critical':
                        await schedule_maintenance(alert['equipment_id'])

                    elif alert['type'] == 'energy_abnormal':
                        await investigate_energy_consumption()

                    elif alert['type'] == 'anomalies_multiple':
                        await trigger_inspection(alert['details'])

            # Aguardar 1 hora
            await asyncio.sleep(3600)
            break  # Remove break em produção
```

**Resultado**: Agent detecta e responde a problemas automaticamente!

### Caso 2: Resposta a Perguntas do Usuário

O Agent responde perguntas usando insights ML:

```python
async def handle_user_question(question: str, organization_id: str) -> str:
    """Agent responde perguntas com dados ML"""
    async for db in get_db():
        # Palavras-chave para energia
        if any(word in question.lower() for word in ['energia', 'consumo', 'energy']):
            insights = await agent_ml_integration.get_insights_for_agent(
                db=db,
                organization_id=organization_id,
                time_range='last_24h'
            )

            energy = insights['insights']['energy_prediction']

            if energy['status'] == 'success':
                response = f"""
📊 **Análise de Consumo Energético**

**Situação Atual**:
- Consumo: {energy['current_consumption_kwh']:.1f} kWh
- Tendência: {energy['trend']} ({energy['trend_slope_kwh_per_hour']:+.2f} kWh/h)
- Status: {'⚠️ Anormal' if energy['abnormal_consumption'] else '✅ Normal'}

**Previsão para Próximas 24h**:
"""
                # Mostrar previsão de 6 em 6 horas
                for i in [0, 6, 12, 18, 23]:
                    pred = energy['predicted_24h'][i]
                    response += f"\n- {pred['hour_ahead']}h: {pred['predicted_consumption_kwh']:.1f} kWh"

                response += "\n\n**Recomendações**:\n"
                for rec in energy['recommendations'][:3]:
                    response += f"- {rec}\n"

                return response

        # Palavras-chave para manutenção
        elif any(word in question.lower() for word in ['manutenção', 'mtbf', 'falha']):
            insights = await agent_ml_integration.get_insights_for_agent(
                db=db,
                organization_id=organization_id
            )

            reliability = insights['insights']['reliability']

            if reliability['status'] == 'success':
                critical_count = len(reliability['critical_equipment'])

                response = f"""
🔧 **Análise de Confiabilidade**

**Equipamentos Críticos**: {critical_count}
"""

                for eq in reliability['critical_equipment'][:3]:
                    response += f"""
- **{eq['equipment_id']}**:
  - MTBF: {eq['mtbf_hours']:.1f}h
  - MTTR: {eq['mttr_hours']:.1f}h
  - Disponibilidade: {eq['availability']:.1f}%
"""

                if reliability['next_maintenances']:
                    response += "\n**Manutenções Previstas**:\n"
                    for maint in reliability['next_maintenances'][:3]:
                        response += f"- {maint['equipment_id']}: {maint['probability_failure_24h']*100:.1f}% falha em 24h\n"

                return response

        # Resposta genérica com sumário
        else:
            insights = await agent_ml_integration.get_insights_for_agent(
                db=db,
                organization_id=organization_id
            )

            return await agent_ml_integration.generate_agent_response(
                insights=insights,
                question=question
            )
```

**Resultado**: Agent responde perguntas complexas com dados ML!

### Caso 3: Ações Proativas Baseadas em Economia

O Agent sugere ações que economizam dinheiro:

```python
async def suggest_cost_optimization(organization_id: str):
    """Agent sugere otimizações de custo"""
    async for db in get_db():
        insights = await agent_ml_integration.get_insights_for_agent(
            db=db,
            organization_id=organization_id
        )

        cost = insights['insights']['cost_optimization']

        if cost['status'] == 'success':
            savings_monthly = cost['potential_savings_monthly']

            if savings_monthly > 1000:  # Se economia > R$ 1000/mês
                # Calcular ROI
                investment_needed = 50000  # Exemplo: custo de implementação
                payback_months = investment_needed / savings_monthly

                message = f"""
💰 **Oportunidade de Economia Identificada**

**Economia Potencial**:
- Mensal: R$ {savings_monthly:.2f}
- Anual: R$ {cost['potential_savings_yearly']:.2f}
- Percentual: {cost['savings_percentage']:.1f}%

**Estratégia Recomendada**:
{cost['optimization_strategy']}

**Horários de Pico para Evitar**:
"""
                for hour, consumption in list(cost['peak_hours'].items())[:5]:
                    message += f"\n- {hour}h: {consumption:.1f} kWh"

                message += f"""

**Análise de ROI**:
- Investimento Estimado: R$ {investment_needed:,.2f}
- Payback: {payback_months:.1f} meses
- ROI 5 anos: {(cost['potential_savings_yearly'] * 5 - investment_needed):,.2f}

**Próximos Passos**:
1. Revisar processos que podem ser deslocados
2. Avaliar impacto operacional
3. Implementar piloto por 1 mês
4. Medir resultados reais
"""

                # Enviar sugestão para usuário/gerente
                await send_optimization_proposal(message)

                return message

        break  # Remove em produção
```

**Resultado**: Agent identifica e propõe economias de forma proativa!

### Caso 4: Integração com Chat

O Agent responde no chat usando ML:

```python
async def chat_with_ml_insights(user_message: str, organization_id: str, user_id: str):
    """Integração do chat com ML Insights"""
    async for db in get_db():
        # Detectar intenção do usuário
        intent = detect_intent(user_message)

        if intent == 'get_insights':
            # Usuário quer insights gerais
            insights = await agent_ml_integration.get_insights_for_agent(
                db=db,
                organization_id=organization_id,
                time_range='last_7_days'
            )

            response = await agent_ml_integration.generate_agent_response(
                insights=insights,
                question=user_message
            )

            # Salvar no histórico de chat
            await save_chat_message(
                user_id=user_id,
                role='assistant',
                content=response,
                metadata={'source': 'ml_insights', 'models_used': 6}
            )

            return response

        elif intent == 'get_energy_forecast':
            # Usuário quer previsão de energia específica
            insights = await agent_ml_integration.get_insights_for_agent(
                db=db,
                organization_id=organization_id,
                time_range='last_24h'
            )

            energy = insights['insights']['energy_prediction']

            # Criar resposta com gráfico
            response = {
                'text': f"Previsão de energia para próximas 24h",
                'chart_data': energy['predicted_24h'],
                'recommendations': energy['recommendations']
            }

            return response

        # ... outros intents

        break  # Remove em produção
```

**Resultado**: Chat inteligente com dados ML em tempo real!

---

## 🔌 Integração via REST API

Se preferir usar REST API ao invés de importação direta:

### Exemplo com Python requests

```python
import requests

# Configuração
BASE_URL = "http://localhost:8000/api/v1/ml"
TOKEN = "your-auth-token"
headers = {"Authorization": f"Bearer {TOKEN}"}

# 1. Obter sumário de insights
def get_summary():
    response = requests.get(
        f"{BASE_URL}/insights/summary?time_range=last_7_days",
        headers=headers
    )
    return response.json()

# 2. Obter previsão de energia
def get_energy_forecast():
    response = requests.get(
        f"{BASE_URL}/insights/energy-prediction?time_range=last_24h",
        headers=headers
    )
    return response.json()

# 3. Obter todos os insights
def get_all_insights():
    response = requests.get(
        f"{BASE_URL}/insights/all?time_range=last_7_days",
        headers=headers
    )
    return response.json()

# Usar
summary = get_summary()
print(f"Total de alertas: {summary['summary']['total_alerts']}")

energy = get_energy_forecast()
print(f"Consumo atual: {energy['current_consumption_kwh']} kWh")
```

### Exemplo com JavaScript/TypeScript (Frontend)

```typescript
// api/ml-insights.ts
import axios from 'axios';

const BASE_URL = '/api/v1/ml';

export const mlInsightsAPI = {
  // Obter sumário
  getSummary: async (timeRange: string = 'last_7_days') => {
    const response = await axios.get(`${BASE_URL}/insights/summary`, {
      params: { time_range: timeRange }
    });
    return response.data;
  },

  // Obter previsão de energia
  getEnergyPrediction: async (timeRange: string = 'last_24h') => {
    const response = await axios.get(`${BASE_URL}/insights/energy-prediction`, {
      params: { time_range: timeRange }
    });
    return response.data;
  },

  // Obter análise de eficiência
  getEfficiency: async (timeRange: string = 'last_7_days') => {
    const response = await axios.get(`${BASE_URL}/insights/efficiency`, {
      params: { time_range: timeRange }
    });
    return response.data;
  },

  // Obter todos os insights
  getAllInsights: async (timeRange: string = 'last_7_days') => {
    const response = await axios.get(`${BASE_URL}/insights/all`, {
      params: { time_range: timeRange }
    });
    return response.data;
  },

  // Health check
  checkHealth: async () => {
    const response = await axios.get(`${BASE_URL}/insights/health`);
    return response.data;
  }
};

// Usar em componente React
import { useEffect, useState } from 'react';
import { mlInsightsAPI } from './api/ml-insights';

function MLInsightsDashboard() {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadInsights() {
      try {
        const data = await mlInsightsAPI.getAllInsights('last_7_days');
        setInsights(data);
      } catch (error) {
        console.error('Erro ao carregar insights:', error);
      } finally {
        setLoading(false);
      }
    }

    loadInsights();

    // Atualizar a cada 5 minutos
    const interval = setInterval(loadInsights, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>Carregando insights...</div>;

  return (
    <div>
      <h2>Insights ML - OptiFlow AI</h2>

      {/* Alertas */}
      {insights.summary.total_alerts > 0 && (
        <div className="alerts">
          <h3>⚠️ {insights.summary.total_alerts} Alertas</h3>
          {/* Renderizar alertas */}
        </div>
      )}

      {/* Previsão de Energia */}
      {insights.insights.energy_prediction && (
        <div className="energy-forecast">
          <h3>📊 Previsão de Energia</h3>
          <p>Consumo Atual: {insights.insights.energy_prediction.current_consumption_kwh} kWh</p>
          {/* Renderizar gráfico de previsão */}
        </div>
      )}

      {/* Recomendações */}
      <div className="recommendations">
        <h3>💡 Recomendações</h3>
        <ul>
          {insights.summary.top_recommendations.map((rec, i) => (
            <li key={i}>{rec}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
```

---

## 📊 Estrutura de Dados

### Response de `get_all_insights()`

```json
{
  "organization_id": "uuid",
  "time_range": "last_7_days",
  "generated_at": "2025-11-06T16:00:00",
  "insights": {
    "reliability": {
      "status": "success",
      "equipment_statistics": [...],
      "critical_equipment": [...],
      "next_maintenances": [...],
      "alerts": [...],
      "recommendations": [...]
    },
    "energy_prediction": {
      "status": "success",
      "current_consumption_kwh": 450.5,
      "predicted_24h": [{...}, ...],
      "trend": "increasing",
      "trend_slope_kwh_per_hour": 2.5,
      "abnormal_consumption": false,
      "alerts": [],
      "recommendations": [...]
    },
    "efficiency": {...},
    "anomalies": {...},
    "correlations": {...},
    "cost_optimization": {...}
  },
  "summary": {
    "total_insights": 6,
    "total_alerts": 3,
    "severity": "medium",
    "top_recommendations": [...],
    "status": "attention_required"
  }
}
```

---

## 🔄 Fluxo Recomendado

```
┌─────────────────────────────────────────────────────────────┐
│                      Autonomous Agent                        │
└───────────┬─────────────────────────────────────┬───────────┘
            │                                     │
            │ 1. User Message                     │ 4. Periodic Check
            │                                     │    (every hour)
            ▼                                     ▼
┌───────────────────────────┐         ┌──────────────────────────┐
│  Chat Handler             │         │  Background Monitor      │
│  - Detect intent          │         │  - Check critical alerts │
│  - Get insights           │         │  - Take automatic actions│
│  - Generate response      │         │  - Send notifications    │
└───────────┬───────────────┘         └──────────┬───────────────┘
            │                                     │
            │ 2. Get Insights                     │ 5. Get Insights
            │                                     │
            ▼                                     ▼
┌─────────────────────────────────────────────────────────────┐
│              AgentMLIntegration                              │
│  - get_insights_for_agent()                                  │
│  - check_critical_alerts()                                   │
│  - generate_agent_response()                                 │
└───────────┬─────────────────────────────────────┬───────────┘
            │                                     │
            │ 3. Query Insights                   │
            │                                     │
            ▼                                     ▼
┌─────────────────────────────────────────────────────────────┐
│              MLInsightsService                               │
│  - generate_all_insights()                                   │
│  - 6 ML models in parallel                                   │
└───────────┬─────────────────────────────────────┬───────────┘
            │                                     │
            ▼                                     ▼
┌─────────────────────┐                 ┌──────────────────────┐
│  Database           │                 │  Synthetic Data      │
│  (when available)   │                 │  (for demo)          │
└─────────────────────┘                 └──────────────────────┘
```

---

## 🎯 Próximos Passos de Implementação

### 1. Integrar no Autonomous Agent Existente ✅ Pronto

Arquivo já criado: `backend/app/services/agent_ml_integration.py`

**Onde Adicionar**:
- Localizar módulo do Autonomous Agent
- Importar `agent_ml_integration`
- Adicionar chamadas nos métodos apropriados

### 2. Implementar Queries Reais do Banco ⚠️ Pendente

**Arquivo**: `backend/app/services/ml_insights_service.py` (linha 140)

**O que fazer**:
```python
# Substituir dados sintéticos por queries reais
async def _fetch_data(...):
    # Buscar OperationalData
    operational_query = select(OperationalData).where(...)
    operational_records = await db.execute(operational_query)

    # Buscar AlarmEvent
    alarm_query = select(AlarmEvent).where(...)
    alarm_records = await db.execute(alarm_query)

    # Processar em DataFrames
    ...
```

### 3. Criar Dashboard Frontend ⚠️ Pendente

**Criar**: `frontend/src/pages/MLInsightsDashboard.tsx`

**Componentes necessários**:
- MLSummaryCard (alertas, severidade)
- EnergyForecastChart (gráfico de previsão)
- EfficiencyGauge (medidor de eficiência)
- AnomaliesTimeline (linha do tempo de anomalias)
- RecommendationsList (lista de recomendações)
- CostOptimizationCard (economia potencial)

### 4. Implementar Cache Redis ⚠️ Pendente

**Motivo**: Insights demoram ~30-60s para gerar (treino de modelos)

**Solução**:
```python
from redis import asyncio as aioredis

class MLInsightsService:
    async def generate_all_insights(self, ...):
        # Verificar cache
        cache_key = f"ml_insights:{organization_id}:{time_range}"
        cached = await redis.get(cache_key)

        if cached:
            return json.loads(cached)

        # Gerar insights
        insights = ...

        # Salvar no cache (5 minutos)
        await redis.setex(cache_key, 300, json.dumps(insights))

        return insights
```

### 5. Salvar Modelos Treinados ⚠️ Pendente

**Motivo**: LSTM treina do zero a cada request (lento)

**Solução**:
```python
# Treinar uma vez
model = self.create_lstm_model(...)
model.fit(X_train, y_train, ...)

# Salvar
model.save('/app/models/lstm_energy.h5')

# Carregar na inicialização
def __init__(self):
    if os.path.exists('/app/models/lstm_energy.h5'):
        self.models['lstm_energy'] = load_model('/app/models/lstm_energy.h5')
```

---

## 📚 Referências

**Documentação**:
- [ML_INTEGRATION_COMPLETE_REPORT.md](ML_INTEGRATION_COMPLETE_REPORT.md) - Documentação técnica completa
- [ML_MODELS_IMPROVEMENT_REPORT.md](ML_MODELS_IMPROVEMENT_REPORT.md) - Análise de performance dos modelos
- [SESSAO_FINAL_ML_INTEGRATION.md](SESSAO_FINAL_ML_INTEGRATION.md) - Resumo da sessão

**Código**:
- [ml_insights_service.py](backend/app/services/ml_insights_service.py) - Serviço principal
- [agent_ml_integration.py](backend/app/services/agent_ml_integration.py) - Integração com Agent
- [ml_insights.py](backend/app/api/v1/endpoints/ml_insights.py) - Endpoints REST

**Testes**:
- [test_ml_endpoints.sh](test_ml_endpoints.sh) - Script de testes automático

**Swagger UI**: http://localhost:8000/docs

---

## 🎉 Conclusão

O sistema de ML Insights está **100% pronto** para ser integrado com o Autonomous Agent!

### ✅ O que funciona agora

- 6 modelos ML/DS implementados e testados
- 9 endpoints REST funcionais
- Módulo de integração AgentMLIntegration pronto
- Dados sintéticos para demonstração
- Documentação completa com exemplos

### 🚀 Próxima ação

**Escolha uma opção**:

1. **Integrar com Agent** - Adicionar chamadas no código do Agent
2. **Criar Dashboard** - Visualizar insights no frontend
3. **Implementar Queries** - Usar dados reais do banco
4. **Adicionar Cache** - Melhorar performance

Qualquer uma dessas opções levará o sistema ao próximo nível!

---

**Guia Criado em**: 2025-11-06 16:30 UTC
**Status**: ✅ **PRONTO PARA USO**

*"From insights to intelligence, from intelligence to action!"* 🤖✨
