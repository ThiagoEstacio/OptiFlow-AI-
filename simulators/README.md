# 🚢 SmartPort - Simuladores

Simuladores de terminal portuário de grãos e açúcar para detecção de anomalias.

**📋 Ver documentação completa**: [SMARTPORT_README.md](../SMARTPORT_README.md)

---

## 🎯 Simuladores Disponíveis

### ⭐ 1. SmartPort Bulk Terminal Simulator (RECOMENDADO)

**Arquivo**: `smartport_bulk_terminal_simulator.py`

**Simulador completo de Terminal de Grãos/Açúcar** com 35+ tags para anomalia detection tipo **PI Vision/Power BI**.

#### 📦 Equipamentos Simulados

- **Correia Transportadora 1** (Recebimento)
- **Correia Transportadora 2** (Transferência)
- **Elevador de Caneca** (Transporte vertical)
- **Shiploader** (Carregador de navio) ⭐ Principal
- **2 Silos** de armazenamento

#### 🏷️ Tags para Anomalia Detection

**Por motor/equipamento**:
- 🔌 Corrente elétrica (A) - detecta sobrecarga
- ⚙️ Velocidade (RPM) - detecta variações
- 🌡️ Temperatura (motor + rolamento) - manutenção preditiva
- 📳 Vibração (mm/s) - desbalanceamento

**Processo**:
- 📊 Fluxo de produto (t/h)
- 📏 Nível de silo (%)
- 🌡️ Temperatura produto (°C)
- 💧 Umidade produto (%)

**KPIs**:
- 📦 Toneladas carregadas (acumulado)
- 📈 Progresso navio (0-100%)
- ⚡ Consumo energia (kWh)

#### 🔍 Anomalias Simuladas

1. **Rolamento degradando** (Correia 1)
   - Após 5 minutos
   - Vibração + temperatura crescentes
   - Para manutenção preditiva

2. **Sobrecarga periódica** (Elevador)
   - A cada 10 minutos
   - Corrente +80A
   - Simula bloqueio

3. **Spikes de vibração** (Shiploader)
   - Aleatoriamente (0.2%/s)
   - Até 12+ mm/s
   - Simula desbalanceamento

#### ⚡ Instalação e Uso

```bash
# 1. Configurar tags no banco (uma vez)
./setup_smartport.sh

# 2. Iniciar simulador
cd simulators
pip install -r requirements.txt
python smartport_bulk_terminal_simulator.py
```

**Opções**:
```bash
# Porta customizada
python smartport_bulk_terminal_simulator.py --port 5030

# Intervalo mais rápido
python smartport_bulk_terminal_simulator.py --interval 0.5
```

---

### 2. Industrial Tags Simulator (Genérico)

**Arquivo**: `industrial_tags_simulator.py`

Simulador genérico com 26 tags industriais para uso geral.

Ver [SIMULADOR_E_TAGS.md](../SIMULADOR_E_TAGS.md) para detalhes.

---

### 3. Modbus TCP Device Simulator (Básico)

**Arquivo**: `modbus_device_simulator.py`

Simulador básico com 6 registros analógicos e 4 coils.

#### Uso

```bash
python modbus_device_simulator.py --port 5020
```

---

## 📊 Comparação de Simuladores

| Feature | SmartPort Bulk | Industrial Tags | Modbus Basic |
|---------|----------------|-----------------|--------------|
| **Tags** | 35 tags | 26 tags | 10 tags |
| **Anomalias** | ✅ 3 tipos | ❌ Não | ❌ Não |
| **Foco** | Terminal portuário | Indústria geral | Teste básico |
| **ML Ready** | ✅ Sim | ⚠️ Parcial | ❌ Não |
| **Realismo** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

---

## 🚀 Quick Start

### Opção 1: SmartPort Completo (Recomendado)

```bash
# Passo 1: Backend
docker compose up -d backend postgres influxdb

# Passo 2: Configurar tags
./setup_smartport.sh

# Passo 3: Simulador
cd simulators
python smartport_bulk_terminal_simulator.py

# Passo 4: Frontend
# Abrir http://localhost:3000
```

### Opção 2: Teste Rápido

```bash
cd simulators
pip install -r requirements.txt
python modbus_device_simulator.py --port 5020
```

---

## 📈 Dashboards Recomendados

### Para SmartPort Bulk Terminal:

1. **Motor Health Monitoring**
   - Tags: `CONV1_MOTOR_CURRENT`, `CONV1_MOTOR_TEMP`, `CONV1_VIBRATION`
   - Tipo: Gauges + Time Series

2. **Manutenção Preditiva**
   - Tags: `CONV1_BEARING_TEMP`, `CONV1_VIBRATION`
   - Tipo: Multi-axis Chart + ML prediction

3. **Throughput Analysis**
   - Tags: `SHIP_FLOW_RATE`, `LOADING_RATE_TOTAL`, `VESSEL_PROGRESS`
   - Tipo: Gauge + Progress bar

4. **Energy Efficiency**
   - Tags: `ENERGY_TOTAL`, todas correntes de motores
   - Tipo: Pie Chart + Dual-axis

Ver [SMARTPORT_README.md](../SMARTPORT_README.md) para exemplos visuais completos.

---

## 🔧 Troubleshooting

### Problema: Porta 5020 em uso

```bash
# Verificar o que está usando a porta
netstat -an | grep 5020

# Usar outra porta
python smartport_bulk_terminal_simulator.py --port 5030
```

### Problema: Tags não aparecem no frontend

```bash
# Reconfigurar tags
./setup_smartport.sh

# Verificar logs do backend
docker logs optiflow-ai--backend
```

### Problema: Permissão negada

```bash
chmod +x setup_smartport.sh
```

---

## 📚 Documentação

- **SmartPort completo**: [SMARTPORT_README.md](../SMARTPORT_README.md)
- **Simuladores genéricos**: [SIMULADOR_E_TAGS.md](../SIMULADOR_E_TAGS.md)
- **API Backend**: [/docs/API.md](../docs/API.md)

---

## 🎯 Roadmap

- [x] SmartPort Bulk Terminal Simulator
- [x] Anomalia detection (3 tipos)
- [ ] RTG Crane Simulator (pátio)
- [ ] Gate Operations Simulator
- [ ] STS Crane Simulator (ship-to-shore)
- [ ] ML models pré-treinados
- [ ] Digital Twin integration

---

**Desenvolvido por**: OptiFlow AI Team
**Versão**: 1.0.0
**Data**: 2025-01-29
