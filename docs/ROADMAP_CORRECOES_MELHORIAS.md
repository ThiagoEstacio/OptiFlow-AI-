# OptiFlow AI - Roadmap de Correções e Melhorias

**Data:** 2025-12-04
**Versão:** 1.0
**Status:** Aprovado para Execução

---

## Visão Geral do Roadmap

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ROADMAP OPTIFLOW AI                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  SPRINT 1 (URGENTE)     │  SPRINT 2-3           │  SPRINT 4-6              │
│  Integridade de Dados   │  ML & Predição        │  Experiência PCM         │
│  ━━━━━━━━━━━━━━━━━━━━   │  ━━━━━━━━━━━━━━━━━    │  ━━━━━━━━━━━━━━━━━━━    │
│  ■ Remover fallbacks    │  ■ Modelo preditivo   │  ■ Dashboard PCM         │
│  ■ Validar configs      │  ■ Detecção anomalia  │  ■ MTBF/MTTR real        │
│  ■ Detectar comm loss   │  ■ Ishikawa dinâmico  │  ■ Integração OS         │
│  ■ Quality gates        │  ■ Cross-correlation  │  ■ Sugestão de peças     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Sprint 1: Integridade de Dados (CRÍTICO)

**Duração:** 1 semana
**Prioridade:** P0 - Bloqueante
**Responsável:** Engenheiro Frontend + Backend

### 1.1 Remover Dados Fictícios do Frontend

| Campo | Valor |
|-------|-------|
| **ID** | CORR-001 |
| **Severidade** | CRÍTICA |
| **Esforço** | 4h |
| **Arquivos** | `TremorExecutive.tsx`, `TremorEnergy.tsx` |

**Problema:**
- Fallback com dados hardcoded quando API retorna vazio
- `Math.random()` usado para simular previsões ML

**Solução:**
```typescript
// REMOVER este padrão:
const displayRootCause = rootCauseAnalysis.length > 0 ? rootCauseAnalysis : fallbackRootCauseData;

// SUBSTITUIR por:
const displayRootCause = rootCauseAnalysis;
// + Componente EmptyState quando não há dados
```

**Critério de Aceite:**
- [ ] Zero instâncias de `Math.random()` em dashboards
- [ ] Zero dados hardcoded apresentados como reais
- [ ] Componente `<NoDataAvailable />` implementado
- [ ] Usuário consegue distinguir "sem dados" de "dados reais"

---

### 1.2 Validação de Configuração de Tags

| Campo | Valor |
|-------|-------|
| **ID** | CORR-002 |
| **Severidade** | ALTA |
| **Esforço** | 8h |
| **Arquivos** | `gateway/app/services/tag_manager.py`, `gateway/app/api/routes/tags.py` |

**Problema:**
- Tags podem ser criados apontando para adapters inexistentes
- Sem validação de compatibilidade protocol_type vs adapter

**Solução:**
```python
# tag_manager.py
def create_tag(self, tag_config: dict) -> dict:
    adapter_id = tag_config.get("adapter_id")

    # Validação 1: Adapter existe
    if adapter_id not in self._active_adapters:
        raise ValidationError(
            f"Adapter '{adapter_id}' não encontrado. "
            f"Adapters disponíveis: {list(self._active_adapters.keys())}"
        )

    # Validação 2: Protocolo compatível
    adapter = self._active_adapters[adapter_id]
    if tag_config.get("protocol_type") != adapter.protocol_type:
        raise ValidationError(
            f"Protocolo '{tag_config.get('protocol_type')}' incompatível "
            f"com adapter '{adapter_id}' (tipo: {adapter.protocol_type})"
        )

    # Prosseguir...
```

**Critério de Aceite:**
- [ ] API retorna 400 ao criar tag para adapter inexistente
- [ ] API retorna 400 para protocolo incompatível
- [ ] Job de housekeeping detecta tags órfãos
- [ ] Alerta disparado para tags em estado inválido

---

### 1.3 Detecção de Perda de Comunicação

| Campo | Valor |
|-------|-------|
| **ID** | CORR-003 |
| **Severidade** | ALTA |
| **Esforço** | 12h |
| **Arquivos** | `gateway/app/services/protocols/base_adapter.py`, `gateway/app/services/data_quality.py` |

**Problema:**
- Sistema não distingue "PLC enviou zero" de "comunicação perdida"
- Último valor bom é sobrescrito quando comunicação cai

**Solução:**
```python
# base_adapter.py
class BaseAdapter:
    def __init__(self):
        self.last_successful_read: datetime = None
        self.communication_timeout_s: float = 30.0
        self.last_good_values: Dict[str, Any] = {}

    def get_communication_status(self) -> CommunicationStatus:
        if self.last_successful_read is None:
            return CommunicationStatus.NEVER_CONNECTED

        age = (datetime.now(timezone.utc) - self.last_successful_read).total_seconds()

        if age > self.communication_timeout_s:
            return CommunicationStatus.LOST
        elif age > self.communication_timeout_s * 0.8:
            return CommunicationStatus.DEGRADED
        return CommunicationStatus.OK

    def on_communication_lost(self):
        """Chamado quando timeout é atingido"""
        for tag_name in self.configured_tags:
            self.publish_quality_change(
                tag_name=tag_name,
                quality="BAD_COMM_FAILURE",
                last_good_value=self.last_good_values.get(tag_name),
                last_good_timestamp=self.last_successful_read
            )
```

**Critério de Aceite:**
- [ ] Alarme "COMM_FAILURE" disparado em < 30s após queda
- [ ] Último valor bom preservado durante perda de comunicação
- [ ] Dashboard mostra status de comunicação por adapter
- [ ] Diferenciação visual entre "zero real" e "sem comunicação"

---

### 1.4 Quality Gates no Pipeline

| Campo | Valor |
|-------|-------|
| **ID** | CORR-004 |
| **Severidade** | MÉDIA |
| **Esforço** | 6h |
| **Arquivos** | `backend/app/services/kafka_consumer.py`, `gateway/app/services/kafka_producer.py` |

**Problema:**
- Dados com qualidade ruim fluem sem bloqueio pelo pipeline
- Não há métricas de qualidade agregadas

**Solução:**
```python
# kafka_consumer.py
class TagDataConsumer:
    def __init__(self):
        self.quality_metrics = QualityMetrics()

    async def process_message(self, message: dict):
        quality = message.get("quality", "unknown")

        # Registrar métricas
        self.quality_metrics.record(
            tag_id=message.get("tag_id"),
            quality=quality,
            timestamp=message.get("timestamp")
        )

        # Quality gate: não processar BAD para historian
        if quality == "bad":
            logger.warning(f"Dropping BAD quality data: {message.get('tag_id')}")
            return

        # Processar normalmente
        await self._store_to_historian(message)
```

**Critério de Aceite:**
- [ ] Dados BAD não são armazenados no historian
- [ ] Métricas de qualidade expostas em `/api/v1/metrics/quality`
- [ ] Dashboard mostra taxa de qualidade por adapter
- [ ] Alerta quando taxa de BAD > 5%

---

## Sprint 2-3: Machine Learning & Predição

**Duração:** 2-3 semanas
**Prioridade:** P1 - Alta
**Responsável:** Data Scientist + Engenheiro ML

### 2.1 Modelo de Detecção de Anomalias

| Campo | Valor |
|-------|-------|
| **ID** | MELH-001 |
| **Esforço** | 40h |
| **Arquivos** | `backend/app/services/ml/anomaly_detection.py` (novo) |

**Objetivo:**
Implementar modelo Isolation Forest para detectar comportamento anômalo em equipamentos usando dados de vibração, temperatura e corrente.

**Implementação:**
```python
# backend/app/services/ml/anomaly_detection.py
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np
import joblib

class AnomalyDetectionService:
    FEATURE_COLUMNS = ['vibration_mms', 'temp_c', 'current_a', 'power_kw', 'load_pct']

    def __init__(self):
        self.models: Dict[str, IsolationForest] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.model_path = Path("models/anomaly")

    async def train_model(self, equipment_id: str, days: int = 30):
        """Treina modelo para um equipamento específico"""
        # Buscar dados históricos
        history = await self._fetch_historical_data(equipment_id, days)

        if len(history) < 1000:
            raise InsufficientDataError(f"Necessário mínimo 1000 amostras, encontrado {len(history)}")

        # Preparar features
        X = history[self.FEATURE_COLUMNS].values

        # Escalar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Treinar Isolation Forest
        model = IsolationForest(
            contamination=0.05,  # 5% de anomalias esperadas
            n_estimators=100,
            max_samples='auto',
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_scaled)

        # Salvar
        self.models[equipment_id] = model
        self.scalers[equipment_id] = scaler

        # Persistir
        joblib.dump(model, self.model_path / f"{equipment_id}_model.joblib")
        joblib.dump(scaler, self.model_path / f"{equipment_id}_scaler.joblib")

        return {
            "equipment_id": equipment_id,
            "samples_trained": len(history),
            "contamination": 0.05,
            "status": "trained"
        }

    async def predict(self, equipment_id: str, current_readings: dict) -> AnomalyPrediction:
        """Prediz se leitura atual é anômala"""
        model = self.models.get(equipment_id)
        scaler = self.scalers.get(equipment_id)

        if not model:
            return AnomalyPrediction(
                status="NO_MODEL",
                message=f"Modelo não treinado para {equipment_id}"
            )

        # Preparar input
        X = np.array([[
            current_readings.get('vibration_mms', 0),
            current_readings.get('temp_c', 0),
            current_readings.get('current_a', 0),
            current_readings.get('power_kw', 0),
            current_readings.get('load_pct', 0)
        ]])

        X_scaled = scaler.transform(X)

        # Predição
        score = model.decision_function(X_scaled)[0]
        is_anomaly = model.predict(X_scaled)[0] == -1

        # Identificar feature contribuinte
        contributing_feature = self._identify_contributing_feature(
            current_readings, equipment_id
        )

        return AnomalyPrediction(
            status="ANOMALY" if is_anomaly else "NORMAL",
            score=float(score),
            confidence=min(abs(score) * 50, 99),
            contributing_feature=contributing_feature,
            recommendation=self._generate_recommendation(contributing_feature, score)
        )
```

**Endpoints:**
```python
# backend/app/api/v1/endpoints/ml_anomaly.py
@router.post("/train/{equipment_id}")
async def train_anomaly_model(equipment_id: str, days: int = 30):
    """Treina modelo de detecção de anomalia para equipamento"""

@router.get("/predict/{equipment_id}")
async def predict_anomaly(equipment_id: str):
    """Retorna predição de anomalia para leituras atuais"""

@router.get("/status")
async def get_models_status():
    """Lista status de todos os modelos treinados"""
```

**Critério de Aceite:**
- [ ] Modelo treinado para cada equipamento com > 1000 amostras
- [ ] Precisão > 85% em conjunto de validação
- [ ] Latência de predição < 50ms
- [ ] Retreinamento automático mensal

---

### 2.2 Previsão de Consumo de Energia (LSTM)

| Campo | Valor |
|-------|-------|
| **ID** | MELH-002 |
| **Esforço** | 32h |
| **Arquivos** | `backend/app/services/ml/energy_forecast.py` (novo) |

**Objetivo:**
Substituir o `Math.random()` por modelo LSTM real para previsão de consumo energético.

**Implementação:**
```python
# backend/app/services/ml/energy_forecast.py
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

class EnergyForecastService:
    SEQUENCE_LENGTH = 24  # 24 horas de histórico
    FORECAST_HORIZON = 24  # Prever próximas 24 horas

    def __init__(self):
        self.model = None
        self.scaler = MinMaxScaler()

    def build_model(self):
        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=(self.SEQUENCE_LENGTH, 1)),
            Dropout(0.2),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(self.FORECAST_HORIZON)
        ])
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model

    async def train(self, days: int = 90):
        """Treina modelo com histórico de consumo"""
        # Buscar dados
        history = await self._fetch_energy_history(days)

        # Preparar sequências
        X, y = self._create_sequences(history['consumption'].values)

        # Escalar
        X_scaled = self.scaler.fit_transform(X.reshape(-1, 1)).reshape(X.shape)

        # Treinar
        self.model = self.build_model()
        self.model.fit(
            X_scaled, y,
            epochs=50,
            batch_size=32,
            validation_split=0.2,
            callbacks=[
                tf.keras.callbacks.EarlyStopping(patience=10),
                tf.keras.callbacks.ReduceLROnPlateau()
            ]
        )

        # Salvar
        self.model.save("models/energy_lstm.h5")
        joblib.dump(self.scaler, "models/energy_scaler.joblib")

    async def predict(self) -> EnergyForecast:
        """Gera previsão para próximas 24 horas"""
        # Buscar últimas 24 horas
        recent = await self._fetch_recent_consumption(hours=24)

        # Preparar input
        X = np.array(recent['consumption'].values).reshape(1, -1, 1)
        X_scaled = self.scaler.transform(X.reshape(-1, 1)).reshape(X.shape)

        # Predição
        predictions = self.model.predict(X_scaled)[0]

        # Calcular métricas
        return EnergyForecast(
            predictions=[
                {"hour": i, "predicted": float(p), "confidence": self._calculate_confidence(i)}
                for i, p in enumerate(predictions)
            ],
            mape=self._calculate_mape(recent, predictions[:len(recent)]),
            model="LSTM",
            trained_at=self.last_training_date
        )
```

**Critério de Aceite:**
- [ ] MAPE < 10% em conjunto de teste
- [ ] Previsão gerada em < 200ms
- [ ] Confiança diminui para horizontes mais distantes
- [ ] Retreinamento semanal automático

---

### 2.3 Diagrama de Ishikawa Dinâmico

| Campo | Valor |
|-------|-------|
| **ID** | MELH-003 |
| **Esforço** | 24h |
| **Arquivos** | `backend/app/api/v1/endpoints/quality_analytics.py`, `frontend/src/pages/tremor/TremorQuality.tsx` |

**Objetivo:**
Alimentar automaticamente o diagrama Ishikawa com correlações ML entre causas (6M) e efeitos.

**Implementação Backend:**
```python
# quality_analytics.py - Adicionar endpoint
@router.get("/ishikawa/dynamic/{effect}")
async def get_dynamic_ishikawa(
    effect: str,  # Ex: "parada_nao_planejada", "defeito_qualidade"
    time_range: str = "7d",
    db: AsyncSession = Depends(get_db)
):
    """
    Gera diagrama Ishikawa baseado em análise de correlação de dados históricos.
    Categorias 6M: Máquina, Método, Mão de obra, Material, Medição, Meio ambiente
    """

    # Buscar eventos do efeito
    effect_events = await _get_effect_events(db, effect, time_range)

    # Para cada categoria, buscar causas correlacionadas
    causes = {}

    # MÁQUINA: Correlacionar com alarmes de equipamento
    machine_causes = await _correlate_machine_causes(db, effect_events)
    causes["machine"] = [
        {
            "cause": c.description,
            "correlation": c.correlation_score,
            "occurrences": c.count,
            "equipment": c.equipment_id
        }
        for c in machine_causes
    ]

    # MÉTODO: Correlacionar com mudanças de receita/setpoint
    method_causes = await _correlate_method_causes(db, effect_events)
    causes["method"] = method_causes

    # MATERIAL: Correlacionar com lotes de matéria-prima
    material_causes = await _correlate_material_causes(db, effect_events)
    causes["material"] = material_causes

    # MEDIÇÃO: Correlacionar com descalibração de sensores
    measurement_causes = await _correlate_measurement_causes(db, effect_events)
    causes["measurement"] = measurement_causes

    # MÃO DE OBRA: Correlacionar com turnos/operadores
    manpower_causes = await _correlate_manpower_causes(db, effect_events)
    causes["manpower"] = manpower_causes

    # MEIO AMBIENTE: Correlacionar com condições ambientais
    environment_causes = await _correlate_environment_causes(db, effect_events)
    causes["environment"] = environment_causes

    return {
        "effect": effect,
        "time_range": time_range,
        "total_events": len(effect_events),
        "causes": causes,
        "top_cause": _identify_top_cause(causes),
        "confidence": _calculate_overall_confidence(causes)
    }
```

**Critério de Aceite:**
- [ ] Causas ordenadas por correlação
- [ ] Mínimo 3 causas por categoria M
- [ ] Score de correlação calculado (Pearson/Spearman)
- [ ] Drill-down para detalhes de cada causa

---

### 2.4 Correlação Cross-Equipment

| Campo | Valor |
|-------|-------|
| **ID** | MELH-004 |
| **Esforço** | 20h |
| **Arquivos** | `backend/app/services/ml/correlation_analysis.py` (novo) |

**Objetivo:**
Detectar cascatas de falha entre equipamentos usando análise de grafos.

**Implementação:**
```python
# correlation_analysis.py
import networkx as nx
from scipy.stats import spearmanr

class EquipmentCorrelationService:
    def __init__(self):
        self.dependency_graph = nx.DiGraph()

    async def build_dependency_graph(self, days: int = 30):
        """Constrói grafo de dependência baseado em correlação temporal de falhas"""

        # Buscar todos os eventos de falha
        failures = await self._get_all_failures(days)

        # Agrupar por equipamento
        equipment_failures = self._group_by_equipment(failures)

        # Calcular correlação temporal entre cada par
        equipments = list(equipment_failures.keys())

        for i, eq1 in enumerate(equipments):
            for eq2 in equipments[i+1:]:
                # Criar série temporal binária (1 = falha, 0 = ok)
                ts1 = self._create_failure_timeseries(equipment_failures[eq1])
                ts2 = self._create_failure_timeseries(equipment_failures[eq2])

                # Calcular correlação com lag
                for lag in range(-5, 6):  # -5 a +5 minutos
                    corr, pvalue = spearmanr(
                        ts1[max(0, lag):],
                        ts2[max(0, -lag):len(ts1)-abs(lag)]
                    )

                    if abs(corr) > 0.7 and pvalue < 0.05:
                        # Adicionar aresta ao grafo
                        if lag > 0:  # eq1 causa eq2
                            self.dependency_graph.add_edge(
                                eq1, eq2,
                                correlation=corr,
                                lag_minutes=lag,
                                confidence=1 - pvalue
                            )
                        else:  # eq2 causa eq1
                            self.dependency_graph.add_edge(
                                eq2, eq1,
                                correlation=corr,
                                lag_minutes=-lag,
                                confidence=1 - pvalue
                            )

        return self._serialize_graph()

    async def predict_cascade(self, failed_equipment: str) -> List[CascadeRisk]:
        """Dado um equipamento em falha, prediz quais outros podem ser afetados"""

        if failed_equipment not in self.dependency_graph:
            return []

        # BFS a partir do equipamento falho
        affected = []
        for successor in nx.bfs_tree(self.dependency_graph, failed_equipment):
            if successor == failed_equipment:
                continue

            edge = self.dependency_graph[failed_equipment][successor]
            affected.append(CascadeRisk(
                equipment=successor,
                estimated_time_minutes=edge['lag_minutes'],
                probability=edge['correlation'],
                recommendation=f"Monitorar {successor} nos próximos {edge['lag_minutes']} minutos"
            ))

        return sorted(affected, key=lambda x: x.estimated_time_minutes)
```

**Critério de Aceite:**
- [ ] Grafo de dependência visualizável
- [ ] Predição de cascata em < 100ms
- [ ] Alerta proativo quando equipamento "raiz" falha
- [ ] Acurácia > 70% em validação histórica

---

## Sprint 4-6: Experiência PCM

**Duração:** 3 semanas
**Prioridade:** P2 - Média
**Responsável:** Engenheiro Frontend + Analista PCM

### 3.1 Dashboard Dedicado de Manutenção

| Campo | Valor |
|-------|-------|
| **ID** | MELH-005 |
| **Esforço** | 60h |
| **Arquivos** | `frontend/src/pages/tremor/TremorMaintenance.tsx` (novo) |

**Estrutura de Tabs:**

```
┌─────────────────────────────────────────────────────────────────┐
│  🔧 Central de Manutenção                                       │
├─────────────────────────────────────────────────────────────────┤
│  [Saúde dos Ativos] [Indicadores] [Backlog] [Análise de Falhas] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Tab 1: Saúde dos Ativos                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ ELEV01   │ │ CORR01   │ │ CORR02   │ │ SILO01   │           │
│  │ ██████   │ │ ████░░   │ │ ███████  │ │ █████░   │           │
│  │ 95%      │ │ 72%      │ │ 98%      │ │ 85%      │           │
│  │ ✓ Normal │ │ ⚠ Alerta │ │ ✓ Normal │ │ ✓ Normal │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                 │
│  Tab 2: Indicadores KPI                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ MTBF por Equipamento        MTTR por Tipo de Falha      │   │
│  │ [████████████████████]      [████████]                  │   │
│  │ ELEV01: 720h                Mecânica: 2.5h              │   │
│  │ CORR01: 480h                Elétrica: 1.2h              │   │
│  │ CORR02: 890h                Instrumentação: 0.8h        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Tab 3: Backlog e Planejamento                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Ordens Preventivas Pendentes: 12                        │   │
│  │ ┌────────────────────────────────────────────────────┐  │   │
│  │ │ OS-2024-1234 │ ELEV01 │ Troca rolamento │ 15/12   │  │   │
│  │ │ OS-2024-1235 │ CORR02 │ Lubrificação    │ 18/12   │  │   │
│  │ └────────────────────────────────────────────────────┘  │   │
│  │                                                          │   │
│  │ Previsões ML (Próximos 7 dias):                         │   │
│  │ ⚠ CORR01: Probabilidade de falha 78% (vibração alta)    │   │
│  │ ⚠ SILO02: Sensor de nível degradando (calibrar)         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Tab 4: Análise de Falhas                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Pareto de Falhas         │ Custo Corretiva vs Preventiva│   │
│  │ [Gráfico de Barras]      │ [Gráfico de Pizza]           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Critério de Aceite:**
- [ ] Score de saúde calculado em tempo real
- [ ] MTBF/MTTR calculados corretamente
- [ ] Integração com backlog de OS
- [ ] Previsões ML exibidas com confiança

---

### 3.2 Cálculo Real de MTBF/MTTR

| Campo | Valor |
|-------|-------|
| **ID** | MELH-006 |
| **Esforço** | 16h |
| **Arquivos** | `backend/app/api/v1/endpoints/maintenance_kpis.py` (novo) |

**Implementação:**
```python
@router.get("/kpis/{equipment_id}")
async def get_maintenance_kpis(
    equipment_id: str,
    time_range: str = "90d",
    db: AsyncSession = Depends(get_db)
):
    """Calcula KPIs de manutenção para equipamento"""

    # Buscar eventos de falha e reparo
    failures = await _get_failure_events(db, equipment_id, time_range)
    repairs = await _get_repair_events(db, equipment_id, time_range)

    # MTBF = Tempo total operação / Número de falhas
    total_operation_time = await _calculate_operation_time(db, equipment_id, time_range)
    mtbf = total_operation_time / len(failures) if failures else None

    # MTTR = Soma dos tempos de reparo / Número de reparos
    total_repair_time = sum(r.duration_hours for r in repairs)
    mttr = total_repair_time / len(repairs) if repairs else None

    # Disponibilidade = MTBF / (MTBF + MTTR)
    availability = mtbf / (mtbf + mttr) if mtbf and mttr else None

    return {
        "equipment_id": equipment_id,
        "mtbf_hours": mtbf,
        "mttr_hours": mttr,
        "availability_percent": availability * 100 if availability else None,
        "failure_count": len(failures),
        "repair_count": len(repairs),
        "time_range": time_range
    }
```

---

### 3.3 Sugestão Automática de Peças

| Campo | Valor |
|-------|-------|
| **ID** | MELH-007 |
| **Esforço** | 24h |
| **Arquivos** | `backend/app/services/maintenance/spare_parts.py` (novo) |

**Objetivo:**
Baseado no histórico de manutenção, sugerir peças necessárias quando uma falha é predita.

**Implementação:**
```python
class SparePartsRecommender:
    async def recommend(self, equipment_id: str, failure_type: str) -> List[SparePart]:
        """
        Recomenda peças baseado em:
        1. Histórico de peças usadas para este tipo de falha
        2. Frequência de uso
        3. Estoque atual
        """

        # Buscar histórico
        history = await self._get_parts_history(equipment_id, failure_type)

        # Rankear por frequência
        parts_frequency = Counter(h.part_code for h in history)

        recommendations = []
        for part_code, frequency in parts_frequency.most_common(5):
            part_info = await self._get_part_info(part_code)
            stock = await self._get_current_stock(part_code)

            recommendations.append(SparePart(
                code=part_code,
                description=part_info.description,
                probability_needed=frequency / len(history),
                current_stock=stock.quantity,
                reorder_point=stock.reorder_point,
                needs_order=stock.quantity < stock.reorder_point,
                estimated_cost=part_info.unit_cost
            ))

        return recommendations
```

---

### 3.4 Fechamento Automático de PDCA

| Campo | Valor |
|-------|-------|
| **ID** | MELH-008 |
| **Esforço** | 20h |
| **Arquivos** | `backend/app/api/v1/endpoints/quality_analytics.py` |

**Objetivo:**
Integrar PDCA com sistema de OS para fechar ciclo automaticamente.

**Implementação:**
```python
@router.post("/pdca/{pdca_id}/link-os")
async def link_pdca_to_os(
    pdca_id: str,
    os_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Vincula PDCA a uma Ordem de Serviço"""

    pdca = await _get_pdca(db, pdca_id)

    # Atualizar PDCA com referência à OS
    pdca.linked_os_id = os_id
    pdca.status = "DO"  # Mover para fase DO

    # Agendar verificação automática
    await schedule_pdca_check(pdca_id, check_after_hours=72)

    return pdca


@router.post("/pdca/{pdca_id}/auto-check")
async def auto_check_pdca(pdca_id: str, db: AsyncSession = Depends(get_db)):
    """Verificação automática: OS foi concluída? Problema resolvido?"""

    pdca = await _get_pdca(db, pdca_id)
    os = await _get_os(db, pdca.linked_os_id)

    if os.status != "CLOSED":
        return {"status": "WAITING", "message": "OS ainda não concluída"}

    # Verificar se problema foi resolvido (não recorreu)
    recurrence = await _check_recurrence(
        db,
        equipment_id=pdca.equipment_id,
        problem_type=pdca.problem_type,
        since=os.closed_at,
        hours=168  # 7 dias
    )

    if recurrence:
        pdca.status = "FAILED"
        pdca.notes = f"Problema recorreu em {recurrence.occurred_at}"
    else:
        pdca.status = "ACT"  # Sucesso, padronizar
        pdca.effectiveness = "EFFECTIVE"

    return pdca
```

---

## Cronograma Visual

```
Semana  1    2    3    4    5    6    7    8    9
        |====|====|====|====|====|====|====|====|====|
SPRINT 1 ████████
  CORR-001 ██
  CORR-002 ████
  CORR-003   ██████
  CORR-004     ████

SPRINT 2-3        ████████████████
  MELH-001        ████████████
  MELH-002            ████████████
  MELH-003              ████████
  MELH-004                ████████

SPRINT 4-6                        ████████████████████████
  MELH-005                        ████████████████
  MELH-006                            ████████
  MELH-007                              ████████████
  MELH-008                                  ████████████
```

---

## Métricas de Sucesso

| Métrica | Baseline Atual | Meta Sprint 1 | Meta Sprint 3 | Meta Sprint 6 |
|---------|----------------|---------------|---------------|---------------|
| Dados fictícios em produção | Presente | 0 | 0 | 0 |
| Taxa de qualidade Good | 100%* | > 95% | > 95% | > 98% |
| Detecção de falha antecipada | N/A | 4h | 8h | 24h |
| MAPE previsão energia | N/A | - | < 15% | < 10% |
| Tempo análise diária PCM | 2h | - | - | 30min |
| Cobertura modelo anomalia | 0% | - | 50% | 100% |

*Após remoção de tags órfãos

---

## Dependências e Riscos

### Dependências

| Item | Depende de | Impacto se Atrasado |
|------|------------|---------------------|
| MELH-001 (Anomalia) | Histórico de 30 dias | Modelo impreciso |
| MELH-002 (LSTM) | TensorFlow instalado | Previsão não funciona |
| MELH-005 (Dashboard PCM) | MELH-006 (KPIs) | Dados faltantes |
| MELH-008 (PDCA Auto) | Sistema de OS externo | Integração manual |

### Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Dados históricos insuficientes | Média | Alto | Começar coleta intensiva agora |
| Resistência do PCM a novo dashboard | Média | Médio | Envolver usuários desde Sprint 2 |
| Performance do modelo em prod | Baixa | Alto | Stress test antes de deploy |
| Integração com sistema OS legado | Alta | Médio | Fallback para input manual |

---

## Aprovações

| Papel | Nome | Data | Assinatura |
|-------|------|------|------------|
| Product Owner | | | |
| Tech Lead | | | |
| PCO Lead | | | |
| PCM Lead | | | |
| Data Science Lead | | | |

---

*Documento gerado automaticamente pelo Comitê Multidisciplinar de Indústria 4.0*
