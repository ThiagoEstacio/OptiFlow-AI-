# 🚢 SmartPort - Terminal de Grãos e Açúcar

**Plataforma IIoT com IA para monitoramento e otimização de terminais portuários**

Powered by **OptiFlow AI Platform**

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Equipamentos Monitorados](#equipamentos-monitorados)
3. [Tags e Sensores](#tags-e-sensores)
4. [Configuração Rápida](#configuração-rápida)
5. [Anomalias Detectadas](#anomalias-detectadas)
6. [Dashboards](#dashboards)
7. [Casos de Uso](#casos-de-uso)

---

## 🎯 Visão Geral

SmartPort é uma solução de **monitoramento inteligente** para terminais de exportação de grãos e açúcar, integrando dados de múltiplos equipamentos via protocolo **Modbus TCP**.

### **Benefícios**

- ✅ **Manutenção Preditiva** - Detecta falhas antes que aconteçam
- ✅ **Otimização de Throughput** - Maximiza taxa de carregamento (t/h)
- ✅ **Eficiência Energética** - Monitora consumo e otimiza operação
- ✅ **Redução de Downtime** - Alertas em tempo real de anomalias
- ✅ **Análise de Qualidade** - Controle de umidade e temperatura do produto

### **Tecnologias**

- **Gateway**: Coleta via Modbus TCP
- **Armazenamento**: InfluxDB (time series) + PostgreSQL
- **Backend**: FastAPI (Python)
- **Frontend**: React + TypeScript
- **Analytics**: Plotly.js (12+ tipos de gráficos)
- **ML**: Detecção de anomalias (scikit-learn)

---

## 🏭 Equipamentos Monitorados

### **1. Correia Transportadora 1** (Recebimento)
**Função**: Recebe grãos/açúcar do silo e transfere para o elevador

**Monitoramento**:
- Corrente motor (A)
- Velocidade (RPM)
- Temperatura motor + rolamento (°C)
- Vibração (mm/s)
- Fluxo de produto (t/h)

**Anomalias detectadas**:
- Sobrecarga (corrente > 250A)
- Rolamento degradando (temperatura + vibração crescentes)
- Bloqueio (fluxo < 400 t/h)

---

### **2. Correia Transportadora 2** (Transferência)
**Função**: Transfere produto do elevador para o shiploader

**Monitoramento**:
- Corrente motor (A)
- Velocidade (RPM)
- Temperatura motor (°C)
- Vibração (mm/s)

**Anomalias detectadas**:
- Sobrecarga
- Desbalanceamento (vibração > 7.5 mm/s)

---

### **3. Elevador de Caneca**
**Função**: Transporte vertical do produto

**Monitoramento**:
- Corrente motor (A) - até 400A
- Velocidade (RPM)
- Temperatura motor (°C) - até 130°C
- Vibração (mm/s)

**Anomalias detectadas**:
- Sobrecarga periódica (bloqueio de canecas)
- Desalinhamento (vibração > 10 mm/s)
- Temperatura excessiva (> 105°C)

---

### **4. Shiploader** (Carregador de Navio) ⭐ **EQUIPAMENTO CRÍTICO**
**Função**: Carrega navio com taxa de até 3000 t/h

**Monitoramento**:
- Corrente motor (A) - até 500A
- Velocidade (RPM)
- **Fluxo de carregamento** (t/h) - **KPI PRINCIPAL**
- Vibração (mm/s)
- Ângulo da lança (°)

**Anomalias detectadas**:
- Fluxo baixo (< 1000 t/h)
- Spikes de vibração (desbalanceamento)
- Sobrecarga

---

### **5. Silos de Armazenamento** (2 unidades)
**Função**: Armazenamento do produto antes do carregamento

**Monitoramento**:
- Nível (%)
- Temperatura do produto (°C)
- Pressão pneumática (bar)

**Anomalias detectadas**:
- Nível crítico (< 10%)
- Temperatura elevada (risco de combustão espontânea)

---

## 🏷️ Tags e Sensores

### **Total: 35 tags**

#### **Por Categoria**:

| Categoria | Quantidade | Descrição |
|-----------|------------|-----------|
| **Energy** | 7 tags | Corrente de motores (anomalia: sobrecarga) |
| **Process** | 8 tags | Velocidade motores, fluxo, níveis |
| **Maintenance** | 8 tags | Temperatura, vibração (manutenção preditiva) |
| **Production** | 4 tags | Fluxo, toneladas acumuladas, progresso navio |
| **Quality** | 2 tags | Umidade e temperatura do produto |
| **Status** | 4 tags | Equipamentos ligados/desligados |
| **Alarm** | 4 tags | Alarmes de anomalias |

---

### **Tags Principais para Anomalia Detection**

#### **Correia 1** (6 tags):
```
CONV1_MOTOR_CURRENT    - Corrente (A) - Sobrecarga
CONV1_MOTOR_SPEED      - Velocidade (RPM) - Variação
CONV1_MOTOR_TEMP       - Temp motor (°C)
CONV1_BEARING_TEMP     - Temp rolamento (°C) - ⭐ PREDITIVA
CONV1_VIBRATION        - Vibração (mm/s) - ⭐ PREDITIVA
CONV1_FLOW_RATE        - Fluxo (t/h) - Throughput
```

#### **Elevador** (4 tags):
```
ELEV1_MOTOR_CURRENT    - Corrente (A) - Bloqueio
ELEV1_MOTOR_SPEED      - Velocidade (RPM)
ELEV1_MOTOR_TEMP       - Temperatura (°C) - até 130°C
ELEV1_VIBRATION        - Vibração (mm/s) - Desalinhamento
```

#### **Shiploader** (5 tags):
```
SHIP_MOTOR_CURRENT     - Corrente (A)
SHIP_MOTOR_SPEED       - Velocidade (RPM)
SHIP_FLOW_RATE         - Fluxo (t/h) - ⭐ KPI PRINCIPAL
SHIP_VIBRATION         - Vibração (mm/s) - Spikes aleatórios
SHIP_BOOM_ANGLE        - Ângulo lança (°)
```

#### **Qualidade** (2 tags):
```
PRODUCT_MOISTURE       - Umidade (%) - Limite: 14%
PRODUCT_TEMP           - Temperatura (°C) - Limite: 40°C
```

#### **KPIs** (3 tags):
```
LOADING_RATE_TOTAL     - Toneladas acumuladas
VESSEL_PROGRESS        - % Carregamento do navio (0-100%)
ENERGY_TOTAL           - kWh consumido total
```

---

## ⚡ Configuração Rápida

### **Passo 1: Iniciar Backend**
```bash
docker compose up -d backend postgres influxdb redis
```

### **Passo 2: Configurar Tags** (1 comando!)
```bash
./setup_smartport.sh
```

Este script irá:
- ✅ Criar site "Terminal Santos - Grãos e Açúcar"
- ✅ Criar device "Bulk Terminal PLC"
- ✅ Criar 35 tags com metadata completo
- ✅ Configurar endereços Modbus, limites, scaling

### **Passo 3: Iniciar Simulador**
```bash
cd simulators
pip install -r requirements.txt
python smartport_bulk_terminal_simulator.py
```

### **Passo 4: Acessar Frontend**
```
http://localhost:3000
```

---

## 🔍 Anomalias Detectadas

O simulador gera **3 tipos de anomalias realistas**:

### **1. Rolamento Degradando** (Correia 1) 🔧

**Quando**: Inicia após 5 minutos de operação

**Sinais**:
- Vibração aumenta gradualmente: 2.8 → 6.0+ mm/s
- Temperatura rolamento sobe: 55°C → 80°C
- Corrente motor aumenta: 120A → 150A (atrito)

**Detecção**:
```python
if vibration > 7.5 and bearing_temp > 85:
    ALARM_HIGH_VIBRATION = True
    ALARM_HIGH_TEMP = True
```

**Dashboard recomendado**: Manutenção Preditiva

---

### **2. Sobrecarga Periódica** (Elevador) ⚠️

**Quando**: A cada 10 minutos, dura 1 minuto

**Sinais**:
- Corrente sobe: 180A → 260A (+80A)
- Temperatura motor: 72°C → 92°C
- Velocidade pode cair ligeiramente

**Causas simuladas**:
- Bloqueio de canecas
- Material úmido/empedrado
- Sobrecarga de produto

**Detecção**:
```python
if motor_current > 350:
    ALARM_HIGH_CURRENT = True
```

**Dashboard recomendado**: Motor Health Monitoring

---

### **3. Spikes de Vibração** (Shiploader) 📈

**Quando**: Aleatoriamente (0.2% chance por segundo)

**Sinais**:
- Vibração sobe abruptamente: 4.2 → 12+ mm/s
- Duração: ~50 segundos (decai gradualmente)

**Causas simuladas**:
- Desbalanceamento da lança
- Bloqueio momentâneo
- Impacto de material

**Detecção**:
```python
if ship_vibration > 12:
    ALARM_HIGH_VIBRATION = True
```

**Dashboard recomendado**: Equipment Health Dashboard

---

## 📊 Dashboards

### **1. Motor Health Monitoring** (PI Vision Style)

```
┌────────────────────────────────────────────────────────────────┐
│  🏭 MOTOR HEALTH - CORREIA 1                                   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  CORRENTE    │  │  TEMPERATURA │  │   VIBRAÇÃO   │        │
│  │   125.3 A    │  │    68.2 °C   │  │   3.2 mm/s   │        │
│  │ [Gauge 0-300]│  │ [Gauge 20-120]│ │ [Gauge 0-15] │        │
│  │   Normal     │  │    Normal    │  │   Normal     │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                │
│  📈 TENDÊNCIAS (Últimas 24 horas)                              │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ [Time Series: Corrente + Temperatura + Vibração]      │   │
│  │  - Linha azul: Corrente                                │   │
│  │  - Linha vermelha: Temperatura                         │   │
│  │  - Linha verde: Vibração                               │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ⚠️ ALERTAS ATIVOS: 0                                          │
└────────────────────────────────────────────────────────────────┘
```

**Tags utilizadas**:
- `CONV1_MOTOR_CURRENT`
- `CONV1_MOTOR_TEMP`
- `CONV1_BEARING_TEMP`
- `CONV1_VIBRATION`

---

### **2. Manutenção Preditiva** (Rolamentos)

```
┌────────────────────────────────────────────────────────────────┐
│  🔧 MANUTENÇÃO PREDITIVA - ANÁLISE DE ROLAMENTOS               │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  CORREIA 1 - Rolamento                                         │
│  ┌──────────────┐  ┌──────────────┐                           │
│  │  TEMPERATURA │  │   VIBRAÇÃO   │                           │
│  │    82.1 °C   │  │   6.8 mm/s   │                           │
│  │ [Gauge]      │  │ [Gauge]      │                           │
│  │  ⚠️ ALERTA   │  │  ⚠️ ALERTA   │                           │
│  └──────────────┘  └──────────────┘                           │
│                                                                │
│  📈 EVOLUÇÃO (7 dias)                                          │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ [Multi-axis Chart]                                     │   │
│  │  Eixo Y1 (esq): Temperatura °C                        │   │
│  │  Eixo Y2 (dir): Vibração mm/s                         │   │
│  │  → Tendência crescente detectada!                     │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  🤖 PREDIÇÃO ML:                                               │
│     • Probabilidade de falha: 78%                              │
│     • Tempo estimado até falha: 48-72 horas                    │
│     • Ação recomendada: Agendar manutenção                     │
│                                                                │
│  📋 MANUTENÇÃO SUGERIDA:                                       │
│     [X] Inspeção visual                                        │
│     [X] Medição de vibração no local                           │
│     [X] Substituição preventiva do rolamento                   │
└────────────────────────────────────────────────────────────────┘
```

**Tags utilizadas**:
- `CONV1_BEARING_TEMP` (principal)
- `CONV1_VIBRATION` (principal)
- `CONV1_MOTOR_CURRENT`

---

### **3. Throughput Dashboard** (Produção)

```
┌────────────────────────────────────────────────────────────────┐
│  📦 THROUGHPUT - CARREGAMENTO DE NAVIO                         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  SHIPLOADER - Taxa Atual                                       │
│  ┌────────────────────────────────────────────┐               │
│  │          2,150 t/h                         │               │
│  │     [Gauge 0-3000 t/h]                     │               │
│  │         ✅ NORMAL                           │               │
│  │  (Alvo: 2000 t/h | Máx: 3000 t/h)         │               │
│  └────────────────────────────────────────────┘               │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  CARREGADO   │  │  PROGRESSO   │  │ TEMPO REST.  │        │
│  │  15,250 t    │  │    25.4 %    │  │   21 horas   │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                │
│  📈 FLUXO POR EQUIPAMENTO (Tempo Real)                         │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ [Multi-series Chart]                                   │   │
│  │  - Correia 1:  850 t/h                                 │   │
│  │  - Correia 2:  835 t/h                                 │   │
│  │  - Elevador:   830 t/h                                 │   │
│  │  - Shiploader: 2150 t/h (múltiplas linhas)            │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ⏱️ DOWNTIME ACUMULADO: 0.5 horas (98% uptime)                │
└────────────────────────────────────────────────────────────────┘
```

**Tags utilizadas**:
- `SHIP_FLOW_RATE` (⭐ principal)
- `CONV1_FLOW_RATE`
- `CONV2_FLOW_RATE`
- `ELEV1_FLOW_RATE`
- `LOADING_RATE_TOTAL`
- `VESSEL_PROGRESS`

---

### **4. Energy Efficiency**

```
┌────────────────────────────────────────────────────────────────┐
│  ⚡ EFICIÊNCIA ENERGÉTICA - TERMINAL                           │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  CONSUMO     │  │  kWh/TONELADA│  │  CUSTO       │        │
│  │  1,250 kW    │  │    0.82      │  │  R$ 875      │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                │
│  📊 CONSUMO POR EQUIPAMENTO                                    │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ [Pie Chart]                                            │   │
│  │  - Shiploader: 45%                                     │   │
│  │  - Elevador:   30%                                     │   │
│  │  - Correia 1:  15%                                     │   │
│  │  - Correia 2:  10%                                     │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  📈 CONSUMO vs PRODUÇÃO (Última Semana)                        │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ [Dual-axis Chart]                                      │   │
│  │  Eixo Y1: kWh total                                    │   │
│  │  Eixo Y2: Toneladas carregadas                         │   │
│  │  → Eficiência melhorou 12% vs semana anterior         │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

**Tags utilizadas**:
- `ENERGY_TOTAL`
- `CONV1_MOTOR_CURRENT`
- `CONV2_MOTOR_CURRENT`
- `ELEV1_MOTOR_CURRENT`
- `SHIP_MOTOR_CURRENT`
- `LOADING_RATE_TOTAL`

---

## 🎯 Casos de Uso

### **Caso 1: Detecção Precoce de Falha de Rolamento**

**Problema**: Rolamento da Correia 1 falhou, causando 8 horas de parada não programada.

**Solução SmartPort**:
1. Monitor contínuo de `CONV1_BEARING_TEMP` e `CONV1_VIBRATION`
2. Algoritmo ML detecta padrão anormal 48-72h antes
3. Alerta gerado automaticamente
4. Manutenção preventiva agendada no próximo turno
5. **Resultado**: Falha evitada, downtime zero

**ROI**: R$ 150.000 (custo parada evitada)

---

### **Caso 2: Otimização de Throughput**

**Problema**: Taxa de carregamento abaixo do esperado (1600 t/h vs 2000 t/h alvo)

**Solução SmartPort**:
1. Dashboard mostra `SHIP_FLOW_RATE` consistentemente baixo
2. Análise de correlação: `ELEV1_MOTOR_CURRENT` elevado
3. Diagnóstico: Sobrecarga no elevador limitando fluxo
4. Ajuste: Reduzir velocidade Correia 1, balancear carga
5. **Resultado**: Throughput aumentou para 2100 t/h (+25%)

**ROI**: R$ 80.000/mês (aumento produtividade)

---

### **Caso 3: Redução de Consumo Energético**

**Problema**: Fatura de energia 15% acima do orçado

**Solução SmartPort**:
1. Dashboard Energy Efficiency identifica picos
2. Correlação: `CONV2_MOTOR_CURRENT` 20% acima do normal
3. Inspeção: Roletes desgastados causando atrito
4. Manutenção corretiva
5. **Resultado**: Consumo normalizado, economia de 15%

**ROI**: R$ 45.000/ano

---

### **Caso 4: Controle de Qualidade do Produto**

**Problema**: Lote rejeitado por umidade acima de 14%

**Solução SmartPort**:
1. Monitor em tempo real de `PRODUCT_MOISTURE`
2. Alerta quando umidade > 13.5%
3. Operador desvia produto para secagem
4. **Resultado**: Zero lotes rejeitados

**ROI**: R$ 120.000/ano (redução perdas)

---

## 📈 KPIs Monitorados

### **Operacionais**
- Taxa de carregamento (t/h)
- Tempo de ciclo de carregamento
- Uptime dos equipamentos (%)
- Downtime acumulado (horas)

### **Manutenção**
- MTBF (Mean Time Between Failures)
- MTTR (Mean Time To Repair)
- Número de falhas evitadas (preditiva)
- Custo de manutenção

### **Qualidade**
- Umidade do produto (%)
- Temperatura do produto (°C)
- Lotes rejeitados (quantidade)

### **Energia**
- Consumo total (kWh)
- Consumo específico (kWh/ton)
- Custo energético (R$)
- Fator de potência médio

---

## 🔧 Arquitetura Técnica

```
┌─────────────┐
│  CAMPO (OT) │  Equipamentos no Terminal
└──────┬──────┘
       │ Modbus TCP (porta 5020)
       ↓
┌──────────────┐
│   GATEWAY    │  Coleta dados via protocolo industrial
└──────┬───────┘
       │ MQTT / HTTP
       ↓
┌──────────────┐
│   BACKEND    │  FastAPI + Celery
│              │  - Validação de dados
│              │  - Detecção de anomalias (ML)
│              │  - Geração de alertas
└──────┬───────┘
       │
       ├─→ PostgreSQL (sites, devices, tags, alarmes)
       ├─→ InfluxDB (time series - high frequency)
       └─→ Redis (cache, pub/sub, rate limiting)
       │
       ↓
┌──────────────┐
│   FRONTEND   │  React + TypeScript
│              │  - Dashboards em tempo real
│              │  - Analytics (query builder)
│              │  - 12+ tipos de visualização
└──────────────┘
```

---

## 🚀 Roadmap

### **Fase 1** ✅ (Atual)
- Monitoramento básico via Modbus
- Dashboards em tempo real
- Detecção de anomalias simples (thresholds)

### **Fase 2** (Q2 2025)
- Machine Learning avançado (LSTM, Isolation Forest)
- Predição de falhas com 7 dias antecedência
- Otimização automática de throughput
- Mobile app (iOS/Android)

### **Fase 3** (Q3 2025)
- Integração com ERP/WMS
- Visão computacional (câmeras)
- Digital Twin do terminal
- Simulações "what-if"

### **Fase 4** (Q4 2025)
- Controle autônomo (closed-loop)
- Otimização multi-objetivo (throughput + energia + qualidade)
- Expansão para outros tipos de carga

---

## 📞 Suporte

**Documentação técnica**: Ver [`/docs`](./docs/)

**Issues/Bugs**: https://github.com/seu-repo/smartport/issues

**Email**: suporte@smartport.com

---

**Desenvolvido por**: OptiFlow AI Team
**Versão**: 1.0.0
**Data**: 2025-01-29
**Licença**: Proprietária
