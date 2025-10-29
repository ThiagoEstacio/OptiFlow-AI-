# 🏭 Simulador Industrial e Tags - OptiFlow AI

Documentação completa para usar simuladores industriais e tags no OptiFlow AI Platform.

**Similar a PI Vision e Power BI** - Tags industriais simuladas para criar dashboards profissionais.

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Simuladores Disponíveis](#simuladores-disponíveis)
3. [Tags Industriais](#tags-industriais)
4. [Configuração Rápida (1 comando)](#configuração-rápida)
5. [Configuração Manual](#configuração-manual)
6. [Criando Dashboards](#criando-dashboards)
7. [Componentes de Visualização](#componentes-de-visualização)

---

## 🎯 Visão Geral

O OptiFlow AI possui um sistema completo de simulação de dados industriais, permitindo:

- ✅ **26 tags industriais simuladas** (processo, energia, produção, qualidade, manutenção)
- ✅ **Dados realistas** com padrões senoidais, ruído e correlações
- ✅ **Compatível com PI Vision, Power BI e Grafana**
- ✅ **12+ tipos de visualizações** (gauges, gráficos, heatmaps, etc)
- ✅ **Protocolo Modbus TCP** padrão industrial
- ✅ **Configuração automática** no banco de dados

---

## 🔧 Simuladores Disponíveis

### 1. **Industrial Tags Simulator** ⭐ NOVO!
**Arquivo**: `simulators/industrial_tags_simulator.py`

Simulador completo com 26 tags industriais categorizadas:

#### 📊 **PROCESS TAGS** (6 tags)
| Tag | Descrição | Unidade | Faixa |
|-----|-----------|---------|-------|
| TEMP_REACTOR_01 | Temperatura do reator | °C | 20-100 |
| PRES_VESSEL_01 | Pressão do vaso | bar | 0-10 |
| FLOW_INLET_01 | Vazão de entrada | L/min | 0-1000 |
| LEVEL_TANK_01 | Nível do tanque | % | 0-100 |
| PH_ANALYZER_01 | Analisador de pH | pH | 0-14 |
| COND_ANALYZER_01 | Condutividade | µS/cm | 0-5000 |

#### ⚡ **ENERGY TAGS** (4 tags)
| Tag | Descrição | Unidade | Faixa |
|-----|-----------|---------|-------|
| POWER_MOTOR_01 | Consumo de potência | kW | 0-10000 |
| CURRENT_MOTOR_01 | Corrente elétrica | A | 0-200 |
| VOLTAGE_LINE_01 | Tensão da linha | V | 0-500 |
| PF_MOTOR_01 | Fator de potência | - | 0-1 |

#### 🏭 **PRODUCTION TAGS** (4 tags)
| Tag | Descrição | Unidade | Faixa |
|-----|-----------|---------|-------|
| RATE_PRODUCTION | Taxa de produção | units/h | 0-200 |
| COUNT_PRODUCTION | Contador de produção | units | 0-999999 |
| OEE_LINE_01 | Eficiência geral (OEE) | % | 0-100 |
| QUALITY_RATE | Taxa de qualidade | % | 0-100 |

#### 🔧 **MAINTENANCE TAGS** (4 tags)
| Tag | Descrição | Unidade | Faixa |
|-----|-----------|---------|-------|
| SPEED_MOTOR_01 | Velocidade do motor | RPM | 0-3000 |
| TEMP_BEARING_01 | Temperatura do rolamento | °C | 20-100 |
| VIB_X_MOTOR_01 | Vibração eixo X | mm/s | 0-10 |
| VIB_Y_MOTOR_01 | Vibração eixo Y | mm/s | 0-10 |

#### 🚨 **STATUS & ALARM TAGS** (8 tags)
| Tag | Descrição | Tipo |
|-----|-----------|------|
| STATUS_MOTOR_RUNNING | Motor em operação | Boolean |
| STATUS_VALVE_OPEN | Válvula aberta | Boolean |
| STATUS_PUMP_RUNNING | Bomba em operação | Boolean |
| ALARM_HIGH_TEMP | Alarme temperatura alta | Boolean |
| ALARM_HIGH_PRES | Alarme pressão alta | Boolean |
| ALARM_EMERGENCY | Parada de emergência | Boolean |
| MODE_MAINTENANCE | Modo manutenção | Boolean |
| MODE_AUTO | Modo automático | Boolean |

---

### 2. **Modbus Device Simulator**
**Arquivo**: `simulators/modbus_device_simulator.py`

Simulador básico com 6 registros analógicos e 4 coils digitais.

---

### 3. **SmartPort Crane Simulator**
**Arquivo**: `scripts/smartport_simulate.py`

Simula operação completa de guindaste portuário (7 fases de operação).

---

## ⚡ Configuração Rápida

### Passo 1: Iniciar Backend
```bash
docker compose up -d backend postgres
```

### Passo 2: Configurar Tags Automaticamente
```bash
./configurar_tags_simuladas.sh
```

Este script irá:
- ✅ Criar site "Demo Industrial Plant"
- ✅ Criar device "Industrial Simulator"
- ✅ Criar 26 tags industriais no banco de dados
- ✅ Configurar endereços Modbus, unidades, limites, etc.

### Passo 3: Iniciar Simulador
```bash
cd simulators
pip install -r requirements.txt
python industrial_tags_simulator.py
```

**Pronto!** 🎉 Acesse http://localhost:3000/tags para ver as tags.

---

## 🔨 Configuração Manual

Se preferir configurar manualmente:

### 1. Instalar dependências do simulador
```bash
cd simulators
pip install -r requirements.txt
```

### 2. Configurar tags no banco de dados
```bash
# Copiar script para container
docker cp simulators/setup_simulated_tags.py optiflow-ai--backend:/app/

# Executar script
docker exec -it optiflow-ai--backend python /app/setup_simulated_tags.py
```

### 3. Iniciar simulador
```bash
# Porta padrão 5020
python industrial_tags_simulator.py

# Porta personalizada
python industrial_tags_simulator.py --port 5030

# Intervalo de atualização mais rápido
python industrial_tags_simulator.py --interval 0.5

# Listar todas as tags disponíveis
python industrial_tags_simulator.py --list-tags
```

---

## 📊 Criando Dashboards

### Acessar Frontend
```
http://localhost:3000
```

### Ver Tags Configuradas
```
http://localhost:3000/tags
```

### Página de Analytics (Query Builder)
```
http://localhost:3000/analytics
```

A página Analytics possui:
- 🔍 Query Builder visual com autocomplete
- 📈 12+ tipos de visualização
- ⏱️ Seletor de time range
- 🔧 Agregações (mean, median, sum, etc)
- 📥 Export CSV

---

## 🎨 Componentes de Visualização

### Disponíveis no Frontend

1. **TimeSeriesChart** - Gráficos de linha/área temporais
   ```typescript
   import { TimeSeriesChart } from '@/components/Charts/TimeSeriesChart';
   ```

2. **GaugeChart** - Indicadores tipo velocímetro
   ```typescript
   import { GaugeChart } from '@/components/Visualizations/GaugeChart';
   ```

3. **MultiAxisChart** - Múltiplos eixos Y
4. **HeatmapChart** - Mapas de calor
5. **BarChart** - Gráficos de barras
6. **ScatterPlot** - Gráficos de dispersão
7. **BoxPlot** - Box plots estatísticos
8. **PieChart** - Gráficos pizza
9. **RadarChart** - Gráficos radar
10. **SankeyDiagram** - Diagramas Sankey
11. **TreemapChart** - Treemaps hierárquicos
12. **WaterfallChart** - Gráficos cascata
13. **GeoMap** - Mapas geográficos

### Exemplo: Dashboard com Gauge

```typescript
import { GaugeChart } from '@/components/Visualizations/GaugeChart';

function MyDashboard() {
  return (
    <GaugeChart
      value={65.5}
      min={20}
      max={100}
      unit="°C"
      title="Temperatura do Reator"
      thresholds={[
        { value: 20, color: '#22c55e', label: 'Normal' },
        { value: 70, color: '#eab308', label: 'Alerta' },
        { value: 85, color: '#ef4444', label: 'Crítico' }
      ]}
    />
  );
}
```

### Exemplo: Time Series

```typescript
import { TimeSeriesChart } from '@/components/Charts/TimeSeriesChart';

function MyChart() {
  const data = [
    { timestamp: '2025-01-01T12:00:00Z', value: 65.5 },
    { timestamp: '2025-01-01T12:01:00Z', value: 66.2 },
    // ...
  ];

  return (
    <TimeSeriesChart
      data={data}
      title="Temperatura ao longo do tempo"
      unit="°C"
      color="#3B82F6"
    />
  );
}
```

---

## 🔌 Protocolo Modbus TCP

### Endereçamento

#### Holding Registers (Valores Analógicos)
- **Formato**: `40001` a `40099`
- **Tipo**: Float/Integer de 16 ou 32 bits
- **Exemplo**: TEMP_REACTOR_01 = endereço 40001

#### Coils (Valores Digitais)
- **Formato**: `00001` a `00099`
- **Tipo**: Boolean (ON/OFF)
- **Exemplo**: STATUS_MOTOR_RUNNING = endereço 00001

### Configuração do Gateway OptiFlow

O OptiFlow Gateway irá automaticamente:
1. Conectar no simulador via Modbus TCP (localhost:5020)
2. Ler os valores das tags configuradas
3. Aplicar scaling factors (temperatura × 0.1, pressão × 0.01, etc)
4. Armazenar no InfluxDB
5. Disponibilizar via API REST

---

## 📈 Padrões de Dados Simulados

### Temperatura
- **Padrão**: Onda senoidal lenta + ruído gaussiano
- **Fórmula**: `65 + 15 * sin(t/100) + random(0, 0.5)`
- **Uso**: Simular aquecimento/resfriamento cíclico

### Pressão
- **Padrão**: Correlacionado com temperatura
- **Fórmula**: `5 + 2 * sin(t/120 + 0.5) + random(0, 0.1)`

### Vazão
- **Padrão**: Variações periódicas
- **Fórmula**: `500 + 200 * sin(t/80) + random(0, 5)`

### Consumo de Energia
- **Padrão**: Proporcional ao quadrado da velocidade do motor
- **Fórmula**: `5000 * (speed/1500)² + random(0, 100)`

### OEE (Overall Equipment Effectiveness)
- **Padrão**: Produto de disponibilidade × qualidade × performance
- **Fórmula**: `availability * quality_rate * performance_rate / 100`

### Alarmes
- **Padrão**: Baseado em condições
- **Exemplo**: `alarm_high_temp = 1 if temp > 85 else 0`

---

## 🎯 Casos de Uso

### 1. Dashboard de Processo (PI Vision style)
```
┌─────────────────────────────────────────────────────┐
│  🌡️ Temperatura    💨 Pressão     💧 Vazão          │
│     65.5°C           5.2 bar       520 L/min       │
│  [Gauge Chart]    [Gauge Chart]  [Gauge Chart]     │
│                                                     │
│  📈 Tendências (últimas 24h)                        │
│  [Time Series Chart: Temp, Pressão, Vazão]         │
│                                                     │
│  ⚠️ Alarmes Ativos                                  │
│  • Nenhum alarme ativo                              │
└─────────────────────────────────────────────────────┘
```

### 2. Dashboard de Energia
```
┌─────────────────────────────────────────────────────┐
│  ⚡ Potência        🔌 Corrente     📊 Tensão        │
│    5.2 kW           102 A          380 V           │
│                                                     │
│  📈 Consumo Acumulado                               │
│  [Area Chart: kWh ao longo do tempo]               │
│                                                     │
│  📊 Fator de Potência: 0.85                         │
│  [Gauge Chart com zonas: <0.7 red, >0.85 green]    │
└─────────────────────────────────────────────────────┘
```

### 3. Dashboard de Produção (OEE)
```
┌─────────────────────────────────────────────────────┐
│  🏭 OEE Global: 85.3%                               │
│  [Gauge Chart com target 85%]                      │
│                                                     │
│  Disponibilidade: 95%  │  Qualidade: 98.5%         │
│  Performance: 95%      │  Taxa: 105 units/h        │
│                                                     │
│  📈 Produção (últimas 8h)                           │
│  [Multi-axis: Taxa + Contador acumulado]           │
└─────────────────────────────────────────────────────┘
```

### 4. Dashboard de Manutenção Preditiva
```
┌─────────────────────────────────────────────────────┐
│  🔧 Saúde do Equipamento                            │
│                                                     │
│  Temperatura Rolamento: 45.2°C                      │
│  [Gauge: Normal <60, Alerta 60-80, Crítico >80]    │
│                                                     │
│  Vibração (mm/s)                                    │
│  X: 2.5  Y: 2.3  Z: 1.8                            │
│  [Radar Chart: 3 eixos]                            │
│                                                     │
│  📈 Tendência Vibração (7 dias)                     │
│  [Time Series: VIB_X, VIB_Y, VIB_Z]                │
└─────────────────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### Problema: Simulador não inicia
```bash
# Verificar se a porta 5020 está livre
netstat -an | grep 5020

# Se estiver em uso, escolher outra porta
python industrial_tags_simulator.py --port 5030
```

### Problema: Tags não aparecem no frontend
```bash
# Verificar se o backend está rodando
docker ps | grep backend

# Verificar logs do backend
docker logs optiflow-ai--backend

# Reconfigurar tags
./configurar_tags_simuladas.sh
```

### Problema: Dados não atualizam
```bash
# Verificar se o simulador está rodando
ps aux | grep industrial_tags_simulator

# Verificar se o Gateway OptiFlow está habilitado
docker logs optiflow-ai--backend | grep "Gateway"

# Reiniciar serviços
docker compose restart backend gateway
```

### Problema: Permissão negada ao executar script
```bash
chmod +x configurar_tags_simuladas.sh
```

---

## 📚 Referências

### Documentação OptiFlow
- [API REST](./docs/API.md)
- [InfluxDB Schema](./docs/INFLUXDB.md)
- [Frontend Components](./frontend/src/components/)

### Padrões Industriais
- **Modbus TCP**: [modbus.org](https://modbus.org)
- **OEE Calculation**: ISO 22400-2
- **PI Vision**: OSIsoft PI System
- **Power BI**: Microsoft Power BI

---

## 🎉 Conclusão

Agora você tem:
- ✅ **26 tags industriais simuladas** rodando
- ✅ **Dados realistas** com padrões industriais
- ✅ **Dashboards tipo PI Vision** no OptiFlow
- ✅ **12+ visualizações** disponíveis
- ✅ **Configuração automática** com 1 comando

**Divirta-se criando dashboards incríveis!** 🚀

---

**Criado por**: OptiFlow AI Team
**Versão**: 1.0.0
**Data**: 2025-01-29
