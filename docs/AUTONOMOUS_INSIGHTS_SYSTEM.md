# Sistema de Insights Autônomos - OptiFlow AI

## 🤖 Visão Geral

O OptiFlow AI agora possui um **Agente Autônomo** que monitora continuamente o processo industrial e gera insights proativos sem intervenção humana.

## 🎯 Capacidades do Agente Autônomo

### 1. **Monitoramento Contínuo 24/7**
- Executa ciclos de análise a cada 60 segundos
- Monitora todos os tags ativos do sistema
- Nunca para de analisar o processo

### 2. **Detecção Automática de Anomalias**
- Identifica valores fora do padrão usando Z-score
- Detecta desvios de até 2.5 desvios padrão
- Classifica anomalias por severidade (critical, high, medium, low)
- **Output**: "Anomalia detectada: ARZ_CORR01_TEMPERATURA_PV - 3 anomalias na última hora"

### 3. **Análise de Performance**
- Calcula performance vs. design speed
- Identifica equipamentos sub-performando (< 80%)
- Alerta sobre equipamentos em sobrecarga (> 110%)
- **Output**: "Performance baixa: Correia 01 - 75% do design (900 RPM vs 1200 RPM)"

### 4. **Gestão Inteligente de Alarmes**
- Analisa padrões de alarmes
- Detecta alarm floods (> 50 alarmes/24h)
- Identifica chattering alarms (liga/desliga repetidamente)
- **Output**: "Alto volume de alarmes: 87 alarmes nas últimas 24h - Rationalization recomendada"

### 5. **Identificação de Oportunidades de Otimização**
- Compara múltiplos parâmetros
- Encontra correlações entre variáveis
- Sugere ajustes de processo
- **Output**: "Oportunidade de otimização: ARZ equipments - Alta variabilidade em 3 parâmetros"

### 6. **Previsões Preditivas**
- Calcula tendências lineares
- Prevê quando níveis atingirão limites
- Alerta com antecedência
- **Output**: "Previsão: Inventário atingirá capacidade máxima em 6.5 horas - Planejar esvaziamento"

## 📊 Categorias de Insights

| Categoria | Descrição | Exemplo |
|-----------|-----------|---------|
| **anomaly** | Valores anormais ou outliers | Temperatura fora da faixa esperada |
| **optimization** | Oportunidades de melhoria | Performance abaixo do ideal |
| **alert** | Condições críticas | Alarm flood detectado |
| **trend** | Mudanças de padrão | Tendência de aumento contínuo |
| **prediction** | Projeções futuras | Nível atingirá limite em X horas |

## 🚨 Níveis de Severidade

| Severidade | Cor | Ação Requerida | Tempo de Resposta |
|------------|-----|----------------|-------------------|
| **critical** | 🔴 | Ação imediata | < 15 minutos |
| **high** | 🟠 | Ação urgente | < 1 hora |
| **medium** | 🟡 | Ação necessária | < 4 horas |
| **low** | 🟢 | Monitorar | < 24 horas |
| **info** | 🔵 | Informativo | Quando conveniente |

## 🔌 API Endpoints

### 1. Obter Insights Autônomos
```http
GET /api/v1/ai/insights/autonomous
Query Parameters:
  - category: anomaly|optimization|alert|trend|prediction
  - severity: critical|high|medium|low|info
  - limit: 1-100 (default: 20)
```

**Response**:
```json
{
  "total": 15,
  "insights": [
    {
      "id": "anomaly_tag123_1698876543.123",
      "title": "Anomalia detectada: Correia 01 Temperatura",
      "description": "Detectadas 3 anomalias na última hora. Valores além de 2.5 desvios padrão",
      "category": "anomaly",
      "severity": "high",
      "tags": ["tag-uuid-123"],
      "metrics": {
        "anomaly_count": 3,
        "mean": 75.5,
        "stddev": 8.2
      },
      "recommendations": [
        "Verificar sensor ou equipamento",
        "Analisar condições de processo"
      ],
      "timestamp": "2025-11-02T21:00:00Z"
    }
  ]
}
```

### 2. Sumário do Monitoramento
```http
GET /api/v1/ai/insights/autonomous/summary
```

**Response**:
```json
{
  "total_insights": 45,
  "by_category": {
    "anomaly": 12,
    "optimization": 8,
    "alert": 5,
    "prediction": 10,
    "trend": 10
  },
  "by_severity": {
    "critical": 2,
    "high": 8,
    "medium": 15,
    "low": 20
  },
  "latest_insight": { ... },
  "monitoring_active": true,
  "monitoring_interval": 60
}
```

### 3. Forçar Ciclo de Monitoramento
```http
POST /api/v1/ai/insights/autonomous/trigger
```

**Response**:
```json
{
  "status": "completed",
  "message": "Monitoring cycle completed successfully",
  "insights_generated": 48
}
```

### 4. Insight em Tempo Real (Tag Específico)
```http
GET /api/v1/ai/insights/realtime/{tag_id}
```

**Response**:
```json
{
  "tag_id": "uuid",
  "tag_name": "ARZ_CORR01_VELOCIDADE_PV",
  "timestamp": "2025-11-02T21:00:00Z",
  "current_value": {
    "value": 1245.5,
    "unit": "RPM",
    "quality": "good"
  },
  "statistics": {
    "mean": 1250.0,
    "stddev": 85.0,
    "min": 950.0,
    "max": 1450.0
  },
  "anomalies": {
    "anomaly_count": 0,
    "insight": "No significant anomalies detected"
  },
  "recommendations": [
    "✅ Processo muito estável - Bom desempenho"
  ]
}
```

### 5. Análise Completa do Processo
```http
POST /api/v1/ai/insights/analyze-process?duration=24h
```

**Response**:
```json
{
  "timestamp": "2025-11-02T21:00:00Z",
  "duration": "24h",
  "tags_analyzed": 20,
  "process_health": {
    "score": 85,
    "status": "good",
    "factors": [
      "Anomalias detectadas: -10 pontos",
      "Performance abaixo do esperado: -5 pontos"
    ]
  },
  "anomalies": [
    {
      "tag": "ARZ_CORR01_TEMPERATURA_PV",
      "count": 3,
      "insight": "Detected 3 anomalies"
    }
  ],
  "performance": [
    {
      "tag": "ARZ_CORR01_VELOCIDADE_PV",
      "value": 1250.0,
      "performance": 104.2,
      "status": "good"
    }
  ],
  "predictions": [],
  "recommendations": [
    "✅ Processo operando de forma excelente - Manter monitoramento"
  ]
}
```

## 🎨 Integração com Frontend

### Aba de Insights - Componentes

#### 1. **Feed de Insights em Tempo Real**
```typescript
// Buscar insights a cada 30 segundos
const { data: insights } = useQuery({
  queryKey: ['autonomous-insights'],
  queryFn: () => api.get('/ai/insights/autonomous?limit=20'),
  refetchInterval: 30000
});
```

#### 2. **Filtros por Categoria**
```typescript
const categories = [
  { value: 'anomaly', label: 'Anomalias', icon: '🔍', color: 'red' },
  { value: 'optimization', label: 'Otimização', icon: '⚙️', color: 'blue' },
  { value: 'alert', label: 'Alertas', icon: '🚨', color: 'orange' },
  { value: 'trend', label: 'Tendências', icon: '📈', color: 'green' },
  { value: 'prediction', label: 'Previsões', icon: '🔮', color: 'purple' }
];
```

#### 3. **Cards de Insights**
```jsx
<InsightCard
  title={insight.title}
  description={insight.description}
  severity={insight.severity}
  category={insight.category}
  metrics={insight.metrics}
  recommendations={insight.recommendations}
  timestamp={insight.timestamp}
  onAction={() => handleInsightAction(insight)}
/>
```

#### 4. **Dashboard de Saúde do Processo**
```typescript
const { data: summary } = useQuery({
  queryKey: ['process-health'],
  queryFn: () => api.get('/ai/insights/autonomous/summary'),
  refetchInterval: 60000
});

// Exibir:
// - Score de saúde (0-100)
// - Total de insights por categoria
// - Alertas críticos em destaque
```

## 📈 Métricas de Performance do Agente

| Métrica | Valor | Descrição |
|---------|-------|-----------|
| **Ciclo de Monitoramento** | 60s | Frequência de análise |
| **Tags Monitorados** | 50 | Máximo por ciclo |
| **Ferramentas Usadas** | 10 | Tools do AgentToolkit |
| **Insights Armazenados** | 100 | Últimos insights mantidos |
| **Latência Média** | < 5s | Tempo por ciclo |

## 🔧 Configuração

### Ajustar Intervalo de Monitoramento
```python
# Em autonomous_agent.py
self.monitoring_interval = 30  # 30 segundos (mais frequente)
```

### Ajustar Sensibilidade de Anomalias
```python
# No método detect_anomalies
sensitivity = "high"  # low, medium, high
```

### Limitar Tags Analisados
```python
# No método monitor_cycle
.limit(100)  # Aumentar limite
```

## 🎯 Casos de Uso

### 1. **Monitoramento Proativo**
- Operador abre aba de Insights
- Vê lista de insights gerados automaticamente
- Filtra por "critical" e "high"
- Age nos alertas prioritários

### 2. **Análise de Turno**
- Supervisor acessa sumário
- Vê score de saúde: 82/100
- Identifica 3 anomalias no turno
- Investiga causas raiz

### 3. **Planejamento Preditivo**
- Gerente vê previsões
- "Silo atingirá capacidade em 8h"
- Planeja logística com antecedência
- Evita paradas não planejadas

### 4. **Otimização Contínua**
- Engenheiro revisa insights de otimização
- Identifica oportunidades de melhoria
- Implementa ajustes
- Monitora resultados

## 🚀 Roadmap Futuro

- [ ] Machine Learning para detecção de padrões complexos
- [ ] Integração com sistema de ordens de trabalho
- [ ] Relatórios automáticos por email
- [ ] Análise de causa raiz automática
- [ ] Recomendações de ações corretivas
- [ ] Simulação de cenários "what-if"
- [ ] Aprendizado com feedback do usuário
- [ ] Integração com sistema de manutenção preditiva

## 📝 Logs e Debugging

### Ver Logs do Agente
```bash
docker logs optiflow-backend | grep "Autonomous Agent"
```

### Logs Importantes
```
🤖 Autonomous Agent started - Continuous monitoring enabled
🔍 Executing monitoring cycle...
📝 New insight: [high] Anomalia detectada: Correia 01
✅ Monitoring cycle complete. Total insights: 45
```

## ✅ Checklist de Implementação Frontend

- [ ] Criar página `/insights` com layout responsivo
- [ ] Implementar filtros por categoria e severidade
- [ ] Criar componente `InsightCard` com badges de categoria
- [ ] Adicionar widget de "Process Health Score"
- [ ] Implementar auto-refresh (30s)
- [ ] Adicionar notificações para insights críticos
- [ ] Criar modal de detalhes do insight
- [ ] Implementar ações rápidas (marcar como lido, arquivar)
- [ ] Adicionar gráfico de tendência de insights
- [ ] Criar dashboard de métricas do agente

---

**Status**: ✅ PRODUCTION READY  
**Versão**: 1.0  
**Data**: Novembro 2025  
**Autor**: OptiFlow AI Team
