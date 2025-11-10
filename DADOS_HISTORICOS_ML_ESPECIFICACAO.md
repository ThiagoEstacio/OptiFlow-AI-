# 📊 Especificação de Dados Históricos para ML/Data Science

**Data**: 2025-11-06
**Objetivo**: Gerar dados históricos ricos para treinar modelos ML e gerar insights valiosos

---

## 🎯 Visão Geral

O Autonomous Agent do OptiFlow AI precisa de dados históricos robustos para:
- Calcular **MTBF/MTTR** (confiabilidade de equipamentos)
- Prever **consumo energético** (regressão linear e LSTM)
- Detectar **correlações** entre variáveis operacionais
- Identificar **anomalias** e padrões em alarmes
- Otimizar **custos de energia** baseado em tarifas
- Gerar **insights acionáveis** para operadores

---

## 📋 Dados Necessários

### **1. Alarmes Históricos** (1.207 alarmes/ano)

**Objetivo**: Análise de padrões, detecção de anomalias, análise de confiabilidade

**Estrutura**:
```python
{
    "id": UUID,
    "equipment_id": "motor_1",
    "equipment_name": "Motor 1",
    "equipment_type": "motor",  # gate, motor, conveyor, loader
    "alarm_type": "overheating",  # 20+ tipos diferentes
    "severity": "critical",  # critical, high, medium, low
    "start_time": datetime,
    "end_time": datetime,
    "duration_minutes": 120,
    "acknowledged": True,
    "acknowledged_by": "operator_name",
    "resolved": True,
    "resolution_notes": "Motor cooled down after...",
    "days_since_maintenance": 45
}
```

**Padrões Incluídos**:
- ✅ **Horário de Pico**: 70% dos alarmes entre 8h-18h (horário de operação)
- ✅ **Sazonalidade**: 50% mais alarmes no verão (sobrecarga térmica)
- ✅ **Degradação**: Probabilidade aumenta com tempo desde manutenção
- ✅ **Correlação**: Falhas em cascata entre equipamentos relacionados
- ✅ **Severidade Realista**: Distribuição baseada em tipo de alarme

**Tipos de Alarme por Equipamento**:

**Gates** (12 unidades):
- high_temperature (30% × degradação)
- position_error (20%)
- motor_overload (15% × degradação)
- communication_error (10%)
- sensor_failure (15%)
- vibration_high (10% × degradação)

**Motors** (6 unidades):
- overheating (35% × degradação)
- overcurrent (25% × degradação)
- bearing_failure (20% × degradação)
- phase_imbalance (10%)
- insulation_fault (10%)

**Conveyors** (3 unidades):
- belt_misalignment (30%)
- motor_overload (25% × degradação)
- bearing_noise (20% × degradação)
- speed_deviation (15%)
- emergency_stop (10%)

**Ship Loaders** (2 unidades):
- hydraulic_pressure_low (30%)
- overload (25%)
- positioning_error (20%)
- mechanical_wear (15% × degradação)
- control_system_fault (10%)

---

### **2. Eventos de Manutenção** (140 eventos/ano)

**Objetivo**: Cálculo de MTBF/MTTR, análise de custos, planejamento preditivo

**Estrutura**:
```python
{
    "id": UUID,
    "equipment_id": "motor_1",
    "equipment_name": "Motor 1",
    "equipment_type": "motor",
    "alarm_id": UUID,  # Alarme que gerou a manutenção
    "maintenance_type": "corrective",  # corrective, preventive, predictive
    "start_time": datetime,
    "end_time": datetime,
    "mttr_hours": 3.5,  # Mean Time To Repair
    "mtbf_hours": 720.0,  # Mean Time Between Failures
    "cost_brl": 4500.00,  # Custo da manutenção
    "technician": "Tech-05",
    "parts_replaced": "bearing",  # bearing, motor, sensor, etc.
    "notes": "Corrective maintenance performed..."
}
```

**Distribuição de Tipos**:
- 60% Corretiva (após falha)
- 30% Preventiva (planejada)
- 10% Preditiva (baseada em análise)

**Custos Base** (R$):
- Gate: R$ 1.500 × variação (0.7-1.5)
- Motor: R$ 3.000 × variação
- Conveyor: R$ 2.500 × variação
- Loader: R$ 5.000 × variação

**Métricas Esperadas**:
- MTBF médio: 500-800 horas
- MTTR médio: 2-4 horas
- Custo total/ano: R$ 350.000 - R$ 450.000

---

### **3. Consumo Energético Histórico** (8.760 registros/ano - hora a hora)

**Objetivo**: Previsão com LSTM, otimização de custos, análise de eficiência

**Estrutura**:
```python
{
    "timestamp": datetime,
    "hour": 14,  # 0-23
    "day_of_week": 2,  # 0=Monday, 6=Sunday
    "day_of_year": 125,
    "month": 5,

    # Consumo por equipamento (kWh)
    "total_consumption_kwh": 450.75,
    "gates_consumption_kwh": 60.0,  # 12 gates × 5 kW
    "motors_consumption_kwh": 270.0,  # 6 motors × 45 kW
    "conveyors_consumption_kwh": 90.0,  # 3 conveyors × 30 kW
    "loaders_consumption_kwh": 30.75,  # 2 loaders × 150 kW (parcial)

    # Produção
    "production_tons": 720.5,  # Toneladas processadas

    # Eficiência
    "efficiency_kwh_per_ton": 0.6254,  # kWh por tonelada

    # Custo
    "tariff_period": "peak",  # peak, intermediate, off_peak
    "tariff_rate_brl": 0.85,  # R$/kWh
    "cost_brl": 383.14,

    # Fatores aplicados
    "operation_factor": 0.85,  # 0-1 (percentual de operação)
    "seasonal_factor": 1.25,  # Verão
    "weekly_factor": 1.0,  # Dia útil
    "efficiency_trend": 0.985  # Melhoria de 1.5% desde início
}
```

**Padrões Incluídos**:
- ✅ **Ciclo Diário**: Mais consumo 6h-20h (operação), menos 22h-6h (stand-by)
- ✅ **Ciclo Semanal**: 40% consumo em fins de semana (manutenção apenas)
- ✅ **Sazonalidade Anual**: +25% verão (refrigeração), -15% inverno
- ✅ **Correlação com Produção**: Consumo proporcional a tonelagem processada
- ✅ **Tendência de Eficiência**: Melhoria de 6% ao ano (0.5%/mês)
- ✅ **Ruído Realista**: ±5% variação aleatória

**Tarifas de Energia** (Bandeira Verde):
- **Ponta** (18h-21h): R$ 0,85/kWh
- **Intermediário** (17h-18h, 21h-22h): R$ 0,65/kWh
- **Fora Ponta** (demais): R$ 0,45/kWh

**Economia Potencial**:
- Deslocar operações de ponta → fora ponta: **~30-40% redução custo**
- Melhorar eficiência 10%: **R$ 50.000-80.000/ano**

---

### **4. Eventos Operacionais** (887 eventos/ano)

**Objetivo**: Análise de correlação, contexto operacional

**Tipos de Eventos**:

#### **A. Operações de Navios** (500-700/ano)
```python
{
    "id": UUID,
    "event_type": "ship_operation",
    "ship_name": "MV-5421",
    "arrival_time": datetime,
    "departure_time": datetime,
    "duration_hours": 18.5,
    "tonnage": 45000,  # Toneladas
    "cargo_type": "grain",  # grain, soy, corn, fertilizer
    "operation_type": "loading"  # loading, unloading
}
```

**Padrões**:
- 1-3 navios/dia útil
- Duração: 6-24 horas
- Tonelagem: 20.000-80.000 ton

#### **B. Condições Climáticas** (365/ano - diário)
```python
{
    "id": UUID,
    "event_type": "weather",
    "date": datetime,
    "temperature_c": 28.5,  # 15-35°C
    "humidity_percent": 75,  # 40-90%
    "wind_speed_kmh": 15,  # 0-40 km/h
    "rainfall_mm": 5.2,  # 0-50 mm
    "conditions": "cloudy"  # clear, cloudy, rainy, windy
}
```

**Correlações Esperadas**:
- Alta temperatura → Mais alarmes de overheating
- Vento forte → Paradas de operação loader
- Chuva → Redução de eficiência

---

## 🤖 Modelos ML/DS a Treinar

### **1. Análise de Confiabilidade (MTBF/MTTR)**

**Técnicas**:
- Estatística descritiva (médias, desvios)
- Análise de Weibull (distribuição de falhas)
- Curvas de confiabilidade

**Insights Gerados**:
- "Motor 3 está com MTBF 40% abaixo da média → Manutenção urgente"
- "MTTR do Gate 5 está aumentando → Necessita upgrade"
- "Custo de manutenção aumentou 25% em 3 meses → Investigar"

---

### **2. Previsão de Consumo Energético (LSTM)**

**Arquitetura**:
```python
# Input: Últimas 168 horas (1 semana)
# Features:
#   - Consumo total
#   - Produção
#   - Hora do dia
#   - Dia da semana
#   - Mês
#   - Fatores operacionais
# Output: Próximas 24 horas

model = Sequential([
    LSTM(64, return_sequences=True, input_shape=(168, 10)),
    Dropout(0.2),
    LSTM(32),
    Dropout(0.2),
    Dense(24)  # 24 horas
])
```

**Insights Gerados**:
- "Consumo previsto amanhã: 10.500 kWh (±5%)"
- "Pico de consumo esperado às 14h → Evitar operações não-essenciais"
- "Custo previsto: R$ 6.800 → R$ 1.200 acima do normal"

---

### **3. Regressão Linear (Eficiência Energética)**

**Modelo**:
```python
# Y = β0 + β1×Produção + β2×Temperatura + β3×Operação + ε

Efficiency = f(
    production_tons,
    temperature_c,
    operation_factor,
    equipment_age,
    maintenance_recent
)
```

**Insights Gerados**:
- "Eficiência atual: 0.68 kWh/ton (baseline: 0.62) → 9.6% pior"
- "Correlação forte entre temperatura > 30°C e perda de eficiência"
- "Manutenção recente melhorou eficiência em 12%"

---

### **4. Detecção de Anomalias (Isolation Forest)**

**Técnicas**:
- Isolation Forest (unsupervised)
- Z-score (estatístico)
- Autoencoders (deep learning)

**Insights Gerados**:
- "Padrão anormal detectado: 5 alarmes em 2 horas no setor A"
- "Consumo energético fora do padrão: +45% sem aumento de produção"
- "Motor 2 apresentando vibração atípica → Investigar"

---

### **5. Análise de Correlação (Pearson/Spearman)**

**Variáveis**:
```python
correlations = {
    ("temperature", "alarms"): 0.72,  # Forte correlação
    ("humidity", "efficiency"): -0.45,  # Correlação negativa
    ("production", "energy"): 0.89,  # Fortíssima correlação
    ("wind_speed", "loader_stops"): 0.65,
    ("days_since_maintenance", "alarm_rate"): 0.58
}
```

**Insights Gerados**:
- "Temperatura > 32°C aumenta alarmes em 70%"
- "Umidade alta reduz eficiência em 15%"
- "Vento > 30 km/h → Parar operação loader"

---

### **6. Otimização de Custos (Linear Programming)**

**Problema**:
```python
# Minimizar:
Cost = Σ(Energy[t] × Tariff[t])

# Sujeito a:
Production[t] >= Target[t]  # Cumprir meta
Equipment[t] <= Capacity    # Respeitar capacidade
Peak_load[t] <= Contract    # Não exceder contrato
```

**Insights Gerados**:
- "Deslocar 20% da carga das 19h para 22h → Economia de R$ 12.000/mês"
- "Operando fora de ponta pode economizar R$ 150.000/ano"
- "Contrato de demanda está 15% sub-utilizado → Renegociar"

---

## 💾 Estrutura de Armazenamento

### **PostgreSQL** (Dados Estruturados)
```sql
historical_alarms                  -- 1.207 registros
historical_maintenance             -- 140 registros
historical_operational_events      -- 887 registros
```

### **InfluxDB** (Séries Temporais)
```
energy_consumption                 -- 8.760 registros
  tags: tariff_period, equipment_type
  fields: consumption, production, efficiency, cost
```

---

## 🚀 Script de Geração

**Arquivo**: `backend/generate_ml_training_data.py`

**Comando**:
```bash
# Dentro do container backend
python /app/generate_ml_training_data.py
```

**Tempo de Execução**: ~30-60 segundos

**Saída**:
```
✅ Gerados 1.207 alarmes
✅ Gerados 140 eventos de manutenção
✅ Gerados 8.760 registros de energia
✅ Gerados 887 eventos operacionais

📈 Métricas:
  • MTBF médio: 650.5 horas
  • MTTR médio: 3.2 horas
  • Custo total de manutenção: R$ 385.420,00
  • Custo total de energia: R$ 2.847.563,00
  • Eficiência média: 0.6254 kWh/ton
```

---

## 📊 Validação dos Dados

### **Checklist de Qualidade**

**Alarmes**:
- [ ] Distribuição horária realista (70% em 8h-18h)
- [ ] Sazonalidade presente (mais alarmes no verão)
- [ ] Degradação correlacionada com manutenção
- [ ] Severidades corretas por tipo
- [ ] Duração proporcional à severidade

**Manutenção**:
- [ ] MTBF > 0 e < 2.000 horas
- [ ] MTTR > 0 e < 24 horas
- [ ] Custos dentro da faixa esperada
- [ ] Proporção 60/30/10 (corretiva/preventiva/preditiva)

**Energia**:
- [ ] Ciclo diário evidente
- [ ] Ciclo semanal evidente (40% fim de semana)
- [ ] Sazonalidade anual presente
- [ ] Eficiência melhorando ao longo do tempo (-6%/ano)
- [ ] Correlação forte com produção (>0.85)

**Eventos**:
- [ ] 1-3 navios por dia útil
- [ ] Registro climático diário completo
- [ ] Dados sem duplicatas

---

## 🎯 Próximos Passos

1. **Executar Script**
   ```bash
   docker exec optiflow-backend python /app/generate_ml_training_data.py
   ```

2. **Validar Dados**
   ```sql
   SELECT COUNT(*) FROM historical_alarms;
   SELECT COUNT(*) FROM historical_maintenance;
   ```

3. **Treinar Modelos**
   - LSTM para energia
   - Regressão para eficiência
   - Detecção de anomalias

4. **Integrar no Autonomous Agent**
   - Adicionar queries no `autonomous_agent.py`
   - Gerar insights com modelos treinados
   - Exibir no dashboard

5. **Criar Dashboards**
   - Gráfico de MTBF/MTTR por equipamento
   - Previsão de consumo energético
   - Análise de custos de energia
   - Mapa de calor de alarmes

---

## 📈 Métricas de Sucesso

**Dados Gerados**:
- ✅ 1 ano de histórico completo
- ✅ 10.994 registros totais
- ✅ Padrões realistas implementados
- ✅ Correlações estatísticas corretas

**Insights Esperados**:
- ✅ 5-10 insights por dia do Autonomous Agent
- ✅ Previsões com erro < 10%
- ✅ Identificação de 80%+ dos problemas reais
- ✅ ROI comprovado (economia > R$ 200k/ano)

---

## 🤖 Exemplo de Insights Gerados

**MTBF/MTTR**:
> "⚠️ Motor 3 apresenta MTBF de 420h, 35% abaixo da média de 650h. Recomenda-se manutenção preventiva urgente para evitar falha catastrófica. Custo estimado da falha: R$ 15.000."

**Energia**:
> "💡 Análise LSTM prevê consumo de 11.200 kWh amanhã (+15% vs média). Pico às 14h coincide com tarifa de ponta. Recomenda-se deslocar 20% da carga para 22h → Economia de R$ 850."

**Correlação**:
> "🔥 Forte correlação (r=0.78) entre temperatura > 32°C e alarmes de overheating. Com previsão de 34°C amanhã, risco 80% de 3-5 alarmes. Recomenda-se: ativar refrigeração preventiva, reduzir carga em 10%."

**Anomalia**:
> "🚨 Anomalia detectada: Conveyor 2 com 8 alarmes em 4 horas (normal: 1 por dia). Padrão indica provável falha iminente do motor. Ação: Parar equipamento e realizar inspeção técnica."

---

**Status**: ✅ Especificação Completa
**Próximo**: Executar script e treinar modelos
**Estimativa**: 2-3 horas para implementação completa
