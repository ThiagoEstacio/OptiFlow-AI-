"""
Eletrocentro Simulator - Electrical Power Center
=================================================

Simula um Eletrocentro industrial completo com:
- Transformador de entrada (SE - Subestação)
- CCM (Centro de Controle de Motores) com múltiplos alimentadores
- Multi-Medidores de energia por setor
- Relés de Proteção (50/51, 49, 27/59)
- Softstarters para partida suave de motores
- Inversores de Frequência (VFDs)
- Banco de Capacitores para correção de FP

Grandezas Elétricas Simuladas:
- Tensão (V) - trifásica L-L e L-N
- Corrente (A) - por fase e neutro
- Potência Ativa (kW), Reativa (kVAR), Aparente (kVA)
- Fator de Potência (PF)
- Frequência (Hz)
- Energia (kWh, kVARh)
- THD (Distorção Harmônica Total)
- Temperatura de equipamentos

Baseado em equipamentos reais:
- Transformador: 1000 kVA, 13.8kV/480V
- CCM: 6 gavetas com softstarters
- Multi-Medidores: Schneider PM5xxx ou similar
- Relés: SEL, ABB, Siemens
"""

import logging
import random
import math
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTES ELÉTRICAS
# ============================================================================

SQRT3 = math.sqrt(3)
NOMINAL_FREQUENCY_HZ = 60.0  # Brasil = 60Hz


class MotorState(Enum):
    """Estados do motor"""
    STOPPED = "stopped"
    STARTING = "starting"  # Partida (softstart/VFD ramping)
    RUNNING = "running"
    STOPPING = "stopping"
    FAULT = "fault"


class RelayState(Enum):
    """Estados do relé de proteção"""
    NORMAL = "normal"
    ALARM = "alarm"
    TRIP = "trip"
    BLOCKED = "blocked"


# ============================================================================
# CLASSES AUXILIARES
# ============================================================================

@dataclass
class FirstOrderLag:
    """Modelo de primeira ordem para resposta dinâmica realista"""
    value: float = 0.0
    tau: float = 5.0  # Constante de tempo (segundos)

    def update(self, setpoint: float, dt: float) -> float:
        """Atualiza valor com dinâmica de primeira ordem"""
        alpha = dt / (self.tau + dt)
        self.value += alpha * (setpoint - self.value)
        return self.value


@dataclass
class ThreePhaseVoltage:
    """Tensões trifásicas"""
    v_ab: float = 480.0  # Linha A-B
    v_bc: float = 480.0  # Linha B-C
    v_ca: float = 480.0  # Linha C-A
    v_an: float = 277.0  # Fase A-Neutro
    v_bn: float = 277.0  # Fase B-Neutro
    v_cn: float = 277.0  # Fase C-Neutro

    @property
    def v_ll_avg(self) -> float:
        """Tensão linha-linha média"""
        return (self.v_ab + self.v_bc + self.v_ca) / 3

    @property
    def v_ln_avg(self) -> float:
        """Tensão linha-neutro média"""
        return (self.v_an + self.v_bn + self.v_cn) / 3

    @property
    def voltage_imbalance_pct(self) -> float:
        """Desequilíbrio de tensão (%)"""
        avg = self.v_ll_avg
        if avg == 0:
            return 0
        max_dev = max(abs(self.v_ab - avg), abs(self.v_bc - avg), abs(self.v_ca - avg))
        return (max_dev / avg) * 100


@dataclass
class ThreePhaseCurrent:
    """Correntes trifásicas"""
    i_a: float = 0.0  # Fase A
    i_b: float = 0.0  # Fase B
    i_c: float = 0.0  # Fase C
    i_n: float = 0.0  # Neutro

    @property
    def i_avg(self) -> float:
        """Corrente média das fases"""
        return (self.i_a + self.i_b + self.i_c) / 3

    @property
    def current_imbalance_pct(self) -> float:
        """Desequilíbrio de corrente (%)"""
        avg = self.i_avg
        if avg == 0:
            return 0
        max_dev = max(abs(self.i_a - avg), abs(self.i_b - avg), abs(self.i_c - avg))
        return (max_dev / avg) * 100


# ============================================================================
# TRANSFORMADOR DE POTÊNCIA
# ============================================================================

@dataclass
class PowerTransformer:
    """
    Transformador de Potência da Subestação
    Modelo: Transformador a óleo, 3 fases, 60Hz
    """
    name: str = "TR01"
    capacity_kva: float = 1000.0  # Potência nominal

    # Tensões nominais
    primary_voltage_v: float = 13800.0   # Primário (Alta Tensão)
    secondary_voltage_v: float = 480.0   # Secundário (Baixa Tensão)

    # Medições em tempo real
    load_pct: float = 0.0
    power_kw: float = 0.0
    power_kvar: float = 0.0
    power_kva: float = 0.0
    power_factor: float = 1.0

    # Correntes
    primary_current_a: float = 0.0
    secondary_current_a: float = 0.0

    # Temperaturas
    winding_temp_c: float = 45.0
    oil_temp_c: float = 40.0
    ambient_temp_c: float = 25.0

    # Perdas
    no_load_loss_kw: float = 2.5     # Perdas em vazio (núcleo)
    full_load_loss_kw: float = 12.0  # Perdas em carga (cobre) @ 100%

    # Alarmes
    overtemp_alarm: bool = False
    overload_alarm: bool = False

    # Dinâmica térmica
    _lag_winding: FirstOrderLag = field(default_factory=lambda: FirstOrderLag(tau=1800.0))  # 30 min
    _lag_oil: FirstOrderLag = field(default_factory=lambda: FirstOrderLag(tau=3600.0))      # 60 min

    def step(self, total_load_kw: float, total_load_kvar: float, dt: float):
        """Atualiza estado do transformador"""
        # Potência aparente
        self.power_kw = total_load_kw + self.no_load_loss_kw
        self.power_kvar = total_load_kvar
        self.power_kva = math.sqrt(self.power_kw**2 + self.power_kvar**2)

        # Fator de potência
        if self.power_kva > 0:
            self.power_factor = self.power_kw / self.power_kva
        else:
            self.power_factor = 1.0

        # Carregamento
        self.load_pct = (self.power_kva / self.capacity_kva) * 100.0

        # Correntes
        self.secondary_current_a = (self.power_kva * 1000) / (SQRT3 * self.secondary_voltage_v)
        self.primary_current_a = (self.power_kva * 1000) / (SQRT3 * self.primary_voltage_v)

        # Perdas totais (vazio + carga proporcional ao quadrado da corrente)
        load_factor = self.load_pct / 100.0
        copper_loss = self.full_load_loss_kw * (load_factor ** 2)
        total_loss = self.no_load_loss_kw + copper_loss

        # Temperatura do enrolamento (elevação proporcional às perdas)
        temp_rise = 55.0 * (total_loss / (self.no_load_loss_kw + self.full_load_loss_kw))
        target_winding = self.ambient_temp_c + temp_rise
        self.winding_temp_c = self._lag_winding.update(target_winding, dt)

        # Temperatura do óleo (segue enrolamento com atraso)
        target_oil = self.ambient_temp_c + temp_rise * 0.7
        self.oil_temp_c = self._lag_oil.update(target_oil, dt)

        # Alarmes
        self.overtemp_alarm = self.winding_temp_c > 95.0 or self.oil_temp_c > 85.0
        self.overload_alarm = self.load_pct > 100.0


# ============================================================================
# MULTI-MEDIDOR DE ENERGIA
# ============================================================================

@dataclass
class MultiMeter:
    """
    Multi-Medidor de Energia (tipo Schneider PM5xxx)
    Mede todas as grandezas elétricas de um alimentador
    """
    name: str
    nominal_voltage_v: float = 480.0
    nominal_current_a: float = 100.0

    # Tensões
    voltage: ThreePhaseVoltage = field(default_factory=ThreePhaseVoltage)

    # Correntes
    current: ThreePhaseCurrent = field(default_factory=ThreePhaseCurrent)

    # Potências
    power_kw: float = 0.0       # Ativa
    power_kvar: float = 0.0     # Reativa
    power_kva: float = 0.0      # Aparente
    power_factor: float = 1.0   # FP

    # Frequência
    frequency_hz: float = 60.0

    # Energia acumulada
    energy_kwh: float = 0.0
    energy_kvarh: float = 0.0

    # Qualidade de energia
    thd_v_pct: float = 2.0   # THD de tensão
    thd_i_pct: float = 5.0   # THD de corrente

    # Demanda (15 min)
    demand_kw: float = 0.0
    demand_max_kw: float = 0.0
    _demand_accumulator: float = 0.0
    _demand_time: float = 0.0

    def update_from_load(self, load_kw: float, load_kvar: float, pf: float, dt: float):
        """Atualiza medições baseado na carga"""
        # Potências
        self.power_kw = load_kw
        self.power_kvar = load_kvar
        self.power_kva = math.sqrt(load_kw**2 + load_kvar**2)
        self.power_factor = pf if pf > 0 else 0.85

        # Corrente (assumindo sistema balanceado)
        if self.voltage.v_ll_avg > 0:
            i_total = (self.power_kva * 1000) / (SQRT3 * self.voltage.v_ll_avg)
            # Adiciona pequeno desequilíbrio realista (±2%)
            self.current.i_a = i_total * (1.0 + random.uniform(-0.02, 0.02))
            self.current.i_b = i_total * (1.0 + random.uniform(-0.02, 0.02))
            self.current.i_c = i_total * (1.0 + random.uniform(-0.02, 0.02))
            self.current.i_n = abs(self.current.i_a - self.current.i_b) * 0.1  # Neutro residual

        # Frequência com pequena variação
        self.frequency_hz = 60.0 + random.uniform(-0.05, 0.05)

        # Tensão com pequena variação
        v_variation = random.uniform(-0.02, 0.02)
        self.voltage.v_ab = self.nominal_voltage_v * (1.0 + v_variation)
        self.voltage.v_bc = self.nominal_voltage_v * (1.0 + v_variation + random.uniform(-0.01, 0.01))
        self.voltage.v_ca = self.nominal_voltage_v * (1.0 + v_variation + random.uniform(-0.01, 0.01))
        self.voltage.v_an = self.voltage.v_ab / SQRT3
        self.voltage.v_bn = self.voltage.v_bc / SQRT3
        self.voltage.v_cn = self.voltage.v_ca / SQRT3

        # Energia acumulada
        self.energy_kwh += (load_kw * dt) / 3600.0
        self.energy_kvarh += (abs(load_kvar) * dt) / 3600.0

        # Demanda (média de 15 minutos)
        self._demand_accumulator += load_kw * dt
        self._demand_time += dt
        if self._demand_time >= 900:  # 15 minutos
            self.demand_kw = self._demand_accumulator / self._demand_time
            self.demand_max_kw = max(self.demand_max_kw, self.demand_kw)
            self._demand_accumulator = 0.0
            self._demand_time = 0.0

        # THD varia com a carga (mais carga = mais harmônicos)
        load_factor = self.power_kva / (self.nominal_current_a * self.nominal_voltage_v * SQRT3 / 1000)
        self.thd_v_pct = 2.0 + load_factor * 3.0
        self.thd_i_pct = 5.0 + load_factor * 10.0


# ============================================================================
# SOFTSTART
# ============================================================================

@dataclass
class Softstart:
    """
    Softstart para partida suave de motores
    Modelo típico: ABB PST, Siemens 3RW, WEG SSW
    """
    name: str
    motor_power_kw: float = 75.0      # Potência nominal do motor
    motor_voltage_v: float = 480.0    # Tensão nominal
    motor_current_a: float = 100.0    # Corrente nominal

    # Estado
    state: MotorState = MotorState.STOPPED
    command_run: bool = False

    # Parâmetros de partida
    ramp_time_s: float = 15.0         # Tempo de rampa (segundos)
    initial_voltage_pct: float = 40.0  # Tensão inicial (%)
    current_limit_pct: float = 350.0   # Limite de corrente (% da nominal)

    # Medições
    output_voltage_pct: float = 0.0   # Tensão de saída (%)
    output_current_a: float = 0.0     # Corrente de saída
    output_power_kw: float = 0.0      # Potência de saída
    motor_temp_pct: float = 0.0       # Temperatura do motor (% do limite)

    # Tempo de partida
    _start_time: float = 0.0
    _ramp_progress: float = 0.0

    # Falhas
    fault_overload: bool = False
    fault_phase_loss: bool = False
    fault_motor_temp: bool = False

    # Dinâmica
    _lag_current: FirstOrderLag = field(default_factory=lambda: FirstOrderLag(tau=0.5))
    _lag_temp: FirstOrderLag = field(default_factory=lambda: FirstOrderLag(tau=120.0))

    def step(self, load_pct: float, dt: float):
        """Atualiza estado do softstart"""
        # Verifica comando
        if self.command_run and self.state == MotorState.STOPPED:
            self.state = MotorState.STARTING
            self._start_time = 0.0
            self._ramp_progress = 0.0
        elif not self.command_run and self.state in [MotorState.RUNNING, MotorState.STARTING]:
            self.state = MotorState.STOPPING

        # Máquina de estados
        if self.state == MotorState.STOPPED:
            self.output_voltage_pct = 0.0
            self.output_current_a = 0.0
            self.output_power_kw = 0.0
            # Resfria
            target_temp = 0.0

        elif self.state == MotorState.STARTING:
            self._start_time += dt
            self._ramp_progress = min(1.0, self._start_time / self.ramp_time_s)

            # Tensão aumenta de initial_voltage até 100%
            self.output_voltage_pct = self.initial_voltage_pct + \
                (100.0 - self.initial_voltage_pct) * self._ramp_progress

            # Corrente de partida (pico no início, diminui conforme tensão aumenta)
            # I_start tipicamente 3-6x nominal, limitado pelo softstart
            start_current_mult = min(self.current_limit_pct / 100.0,
                                     4.0 - 2.5 * self._ramp_progress)
            target_current = self.motor_current_a * start_current_mult * (self.output_voltage_pct / 100.0)
            self.output_current_a = self._lag_current.update(target_current, dt)

            # Potência durante partida
            self.output_power_kw = (self.output_voltage_pct / 100.0) * self.motor_power_kw * 0.3

            # Temperatura sobe durante partida
            target_temp = 30.0 + 50.0 * self._ramp_progress

            # Transição para running quando rampa completa
            if self._ramp_progress >= 1.0:
                self.state = MotorState.RUNNING

        elif self.state == MotorState.RUNNING:
            self.output_voltage_pct = 100.0

            # Corrente proporcional à carga
            target_current = self.motor_current_a * (0.3 + 0.7 * load_pct / 100.0)
            self.output_current_a = self._lag_current.update(target_current, dt)

            # Potência proporcional à carga
            self.output_power_kw = self.motor_power_kw * (0.2 + 0.8 * load_pct / 100.0)

            # Temperatura estabiliza baseada na carga
            target_temp = 20.0 + 60.0 * (load_pct / 100.0)

        elif self.state == MotorState.STOPPING:
            # Rampa de descida rápida
            self.output_voltage_pct = max(0, self.output_voltage_pct - dt * 20.0)
            self.output_current_a = self._lag_current.update(0, dt)
            self.output_power_kw = 0.0
            target_temp = 0.0

            if self.output_voltage_pct <= 0:
                self.state = MotorState.STOPPED

        elif self.state == MotorState.FAULT:
            self.output_voltage_pct = 0.0
            self.output_current_a = 0.0
            self.output_power_kw = 0.0
            target_temp = self.motor_temp_pct  # Mantém temperatura

        # Atualiza temperatura
        self.motor_temp_pct = self._lag_temp.update(target_temp, dt)

        # Verifica falhas
        if self.output_current_a > self.motor_current_a * (self.current_limit_pct / 100.0) * 1.1:
            self.fault_overload = True
            self.state = MotorState.FAULT

        if self.motor_temp_pct > 100.0:
            self.fault_motor_temp = True
            self.state = MotorState.FAULT


# ============================================================================
# INVERSOR DE FREQUÊNCIA (VFD)
# ============================================================================

@dataclass
class VFD:
    """
    Inversor de Frequência (Variable Frequency Drive)
    Modelo típico: ABB ACS580, Siemens G120, WEG CFW11
    """
    name: str
    motor_power_kw: float = 90.0      # Potência nominal do motor
    motor_voltage_v: float = 480.0    # Tensão nominal
    motor_current_a: float = 120.0    # Corrente nominal
    motor_rpm_nominal: float = 1750.0 # RPM nominal (4 polos, 60Hz)

    # Estado
    state: MotorState = MotorState.STOPPED
    command_run: bool = False

    # Setpoints
    speed_setpoint_pct: float = 0.0   # Velocidade desejada (%)
    frequency_setpoint_hz: float = 0.0 # Frequência de saída

    # Medições de saída
    output_frequency_hz: float = 0.0
    output_voltage_v: float = 0.0
    output_current_a: float = 0.0
    output_power_kw: float = 0.0
    output_torque_pct: float = 0.0
    motor_speed_rpm: float = 0.0

    # Barramento DC
    dc_bus_voltage_v: float = 650.0

    # Temperatura
    heatsink_temp_c: float = 35.0
    motor_temp_pct: float = 0.0

    # Energia
    energy_kwh: float = 0.0

    # Parâmetros
    accel_time_s: float = 10.0        # Tempo de aceleração 0-100%
    decel_time_s: float = 8.0         # Tempo de desaceleração 100-0%

    # Falhas
    fault_overcurrent: bool = False
    fault_overvoltage: bool = False
    fault_overtemp: bool = False

    # Dinâmica
    _lag_freq: FirstOrderLag = field(default_factory=lambda: FirstOrderLag(tau=2.0))
    _lag_current: FirstOrderLag = field(default_factory=lambda: FirstOrderLag(tau=0.3))
    _lag_temp: FirstOrderLag = field(default_factory=lambda: FirstOrderLag(tau=180.0))

    def step(self, load_torque_pct: float, dt: float):
        """Atualiza estado do VFD"""
        # Verifica comando
        if self.command_run and self.state == MotorState.STOPPED:
            self.state = MotorState.STARTING
        elif not self.command_run and self.state in [MotorState.RUNNING, MotorState.STARTING]:
            self.state = MotorState.STOPPING

        # Frequência setpoint baseada na velocidade
        self.frequency_setpoint_hz = (self.speed_setpoint_pct / 100.0) * 60.0

        # Máquina de estados
        if self.state == MotorState.STOPPED:
            target_freq = 0.0
            target_current = 0.0
            self.output_power_kw = 0.0
            self.output_torque_pct = 0.0

        elif self.state == MotorState.STARTING:
            # Rampa de aceleração
            freq_rate = 60.0 / self.accel_time_s  # Hz/s
            target_freq = min(self.frequency_setpoint_hz,
                            self.output_frequency_hz + freq_rate * dt)

            # Corrente de partida (boost em baixa frequência)
            boost_factor = 1.0 + 0.5 * (1.0 - target_freq / 60.0) if target_freq < 60 else 1.0
            target_current = self.motor_current_a * boost_factor * (target_freq / 60.0 + 0.3)

            # Potência e torque
            self.output_power_kw = self.motor_power_kw * (target_freq / 60.0) * (load_torque_pct / 100.0 + 0.2)
            self.output_torque_pct = load_torque_pct + 20.0

            if abs(self.output_frequency_hz - self.frequency_setpoint_hz) < 0.5:
                self.state = MotorState.RUNNING

        elif self.state == MotorState.RUNNING:
            target_freq = self.frequency_setpoint_hz

            # Corrente baseada na carga
            target_current = self.motor_current_a * (0.25 + 0.75 * load_torque_pct / 100.0)

            # Potência proporcional a freq × torque
            freq_ratio = target_freq / 60.0 if target_freq > 0 else 0
            self.output_power_kw = self.motor_power_kw * freq_ratio * (load_torque_pct / 100.0 + 0.15)
            self.output_torque_pct = load_torque_pct

        elif self.state == MotorState.STOPPING:
            # Rampa de desaceleração
            freq_rate = 60.0 / self.decel_time_s
            target_freq = max(0, self.output_frequency_hz - freq_rate * dt)
            target_current = self.motor_current_a * 0.3 * (target_freq / 60.0)
            self.output_power_kw = 0.0
            self.output_torque_pct = 0.0

            if target_freq <= 0.5:
                self.state = MotorState.STOPPED
                target_freq = 0.0

        elif self.state == MotorState.FAULT:
            target_freq = 0.0
            target_current = 0.0
            self.output_power_kw = 0.0

        # Atualiza valores com dinâmica
        self.output_frequency_hz = self._lag_freq.update(target_freq, dt)
        self.output_current_a = self._lag_current.update(target_current, dt)

        # Tensão V/f (proporcional à frequência)
        self.output_voltage_v = self.motor_voltage_v * min(1.0, self.output_frequency_hz / 60.0)

        # Velocidade do motor (RPM = 120 × f / polos)
        # Assumindo 4 polos: RPM = 30 × f
        slip = 0.03 if self.state == MotorState.RUNNING else 0.05
        sync_rpm = 30.0 * self.output_frequency_hz
        self.motor_speed_rpm = sync_rpm * (1.0 - slip * load_torque_pct / 100.0)

        # Barramento DC (varia com regeneração)
        self.dc_bus_voltage_v = 650.0 + random.uniform(-5, 5)
        if self.state == MotorState.STOPPING:
            self.dc_bus_voltage_v += 20.0  # Regeneração aumenta tensão DC

        # Temperatura
        power_loss = self.output_power_kw * 0.03  # ~3% de perdas
        target_temp = 35.0 + power_loss * 2.0
        self.heatsink_temp_c = self._lag_temp.update(target_temp, dt)
        self.motor_temp_pct = 20.0 + 60.0 * (load_torque_pct / 100.0)

        # Energia acumulada
        self.energy_kwh += (self.output_power_kw * dt) / 3600.0

        # Verifica falhas
        if self.output_current_a > self.motor_current_a * 1.5:
            self.fault_overcurrent = True
            self.state = MotorState.FAULT
        if self.dc_bus_voltage_v > 750:
            self.fault_overvoltage = True
            self.state = MotorState.FAULT
        if self.heatsink_temp_c > 85:
            self.fault_overtemp = True
            self.state = MotorState.FAULT


# ============================================================================
# RELÉ DE PROTEÇÃO
# ============================================================================

@dataclass
class ProtectionRelay:
    """
    Relé de Proteção Digital (tipo SEL, ABB, Siemens)
    Funções: 50/51 (sobrecorrente), 49 (térmica), 27/59 (sub/sobretensão)
    """
    name: str

    # Ajustes de proteção
    pickup_50_a: float = 800.0        # Pickup instantâneo (50) em A
    pickup_51_a: float = 120.0        # Pickup temporizado (51) em A
    curve_51: str = "IEC_C"           # Curva de tempo (IEC_C = muito inversa)
    dial_51: float = 0.5              # Dial de tempo

    pickup_49_pct: float = 105.0      # Pickup térmico (% da FLC)

    pickup_27_v: float = 420.0        # Subtensão (V)
    pickup_59_v: float = 528.0        # Sobretensão (V)

    # Estado
    state: RelayState = RelayState.NORMAL

    # Medições de entrada
    current_a: float = 0.0
    voltage_v: float = 480.0

    # Status das funções
    fn_50_active: bool = False        # Instantâneo ativo
    fn_51_active: bool = False        # Temporizado ativo
    fn_49_active: bool = False        # Térmica ativo
    fn_27_active: bool = False        # Subtensão ativo
    fn_59_active: bool = False        # Sobretensão ativo

    # Acumulador térmico (modelo I²t)
    thermal_pct: float = 0.0

    # Contadores de eventos
    trip_count: int = 0
    alarm_count: int = 0

    # Timer para funções temporizadas
    _timer_51: float = 0.0
    _timer_27: float = 0.0
    _timer_59: float = 0.0

    def step(self, current_a: float, voltage_v: float, dt: float):
        """Atualiza estado do relé"""
        self.current_a = current_a
        self.voltage_v = voltage_v

        # Reset de flags
        self.fn_50_active = False
        self.fn_51_active = False
        self.fn_27_active = False
        self.fn_59_active = False

        # Se em trip, mantém
        if self.state == RelayState.TRIP:
            return

        # Função 50 - Sobrecorrente instantânea
        if current_a >= self.pickup_50_a:
            self.fn_50_active = True
            self.state = RelayState.TRIP
            self.trip_count += 1
            logger.warning(f"⚡ TRIP 50: {self.name} - Instantaneous overcurrent {current_a:.1f}A")
            return

        # Função 51 - Sobrecorrente temporizada
        if current_a >= self.pickup_51_a:
            self.fn_51_active = True
            # Cálculo simplificado do tempo de trip (curva IEC muito inversa)
            multiple = current_a / self.pickup_51_a
            if multiple > 1:
                trip_time = (13.5 * self.dial_51) / (multiple - 1)
                self._timer_51 += dt
                if self._timer_51 >= trip_time:
                    self.state = RelayState.TRIP
                    self.trip_count += 1
                    logger.warning(f"⚡ TRIP 51: {self.name} - Timed overcurrent {current_a:.1f}A")
                    return
                elif self._timer_51 > trip_time * 0.8:
                    self.state = RelayState.ALARM
                    self.alarm_count += 1
        else:
            self._timer_51 = max(0, self._timer_51 - dt * 2)  # Reset com histerese

        # Função 49 - Proteção térmica (modelo I²t simplificado)
        if current_a > 0:
            i_ratio = current_a / (self.pickup_51_a * self.pickup_49_pct / 100.0)
            if i_ratio > 1:
                # Aquecimento
                self.thermal_pct += (i_ratio ** 2) * dt / 60.0 * 5.0  # Escala para simulação
            else:
                # Resfriamento
                self.thermal_pct = max(0, self.thermal_pct - dt / 60.0 * 2.0)

            self.fn_49_active = self.thermal_pct > 80.0

            if self.thermal_pct >= 100.0:
                self.state = RelayState.TRIP
                self.trip_count += 1
                logger.warning(f"⚡ TRIP 49: {self.name} - Thermal overload {self.thermal_pct:.1f}%")
                return
            elif self.thermal_pct > 80.0 and self.state == RelayState.NORMAL:
                self.state = RelayState.ALARM

        # Função 27 - Subtensão
        if voltage_v < self.pickup_27_v:
            self.fn_27_active = True
            self._timer_27 += dt
            if self._timer_27 >= 3.0:  # 3 segundos de delay
                self.state = RelayState.TRIP
                self.trip_count += 1
                logger.warning(f"⚡ TRIP 27: {self.name} - Undervoltage {voltage_v:.1f}V")
                return
        else:
            self._timer_27 = 0

        # Função 59 - Sobretensão
        if voltage_v > self.pickup_59_v:
            self.fn_59_active = True
            self._timer_59 += dt
            if self._timer_59 >= 1.0:  # 1 segundo de delay
                self.state = RelayState.TRIP
                self.trip_count += 1
                logger.warning(f"⚡ TRIP 59: {self.name} - Overvoltage {voltage_v:.1f}V")
                return
        else:
            self._timer_59 = 0

        # Se nenhuma condição de alarme, volta ao normal
        if self.state == RelayState.ALARM and not self.fn_51_active and not self.fn_49_active:
            self.state = RelayState.NORMAL

    def reset(self):
        """Reset manual do relé"""
        self.state = RelayState.NORMAL
        self._timer_51 = 0
        self._timer_27 = 0
        self._timer_59 = 0
        self.thermal_pct = max(0, self.thermal_pct - 20)  # Não reseta completamente


# ============================================================================
# BANCO DE CAPACITORES
# ============================================================================

@dataclass
class CapacitorBank:
    """
    Banco de Capacitores para correção de fator de potência
    Controle automático por estágios
    """
    name: str
    total_kvar: float = 300.0         # Capacidade total
    num_stages: int = 6               # Número de estágios

    # Estado
    stages_on: int = 0                # Estágios ligados

    # Parâmetros de controle
    target_pf: float = 0.92           # FP alvo
    hysteresis: float = 0.02          # Histerese

    # Medições
    reactive_power_kvar: float = 0.0
    current_a: float = 0.0
    voltage_v: float = 480.0
    temperature_c: float = 35.0

    # Timer para evitar chaveamento rápido
    _switch_timer: float = 0.0
    _switch_delay: float = 30.0       # Delay mínimo entre chaveamentos

    def step(self, system_kw: float, system_kvar: float, voltage_v: float, dt: float):
        """Atualiza estado do banco de capacitores"""
        self.voltage_v = voltage_v

        # Calcula FP atual do sistema
        kva = math.sqrt(system_kw**2 + system_kvar**2)
        current_pf = system_kw / kva if kva > 0 else 1.0

        # Atualiza timer
        self._switch_timer += dt

        # Controle automático de estágios
        if self._switch_timer >= self._switch_delay:
            kvar_per_stage = self.total_kvar / self.num_stages

            if current_pf < self.target_pf - self.hysteresis and self.stages_on < self.num_stages:
                # Liga mais um estágio
                self.stages_on += 1
                self._switch_timer = 0
                logger.info(f"🔌 {self.name}: Stage ON ({self.stages_on}/{self.num_stages})")

            elif current_pf > self.target_pf + self.hysteresis and self.stages_on > 0:
                # Desliga um estágio
                self.stages_on -= 1
                self._switch_timer = 0
                logger.info(f"🔌 {self.name}: Stage OFF ({self.stages_on}/{self.num_stages})")

        # Calcula potência reativa fornecida
        kvar_per_stage = self.total_kvar / self.num_stages
        self.reactive_power_kvar = self.stages_on * kvar_per_stage * (voltage_v / 480.0) ** 2

        # Corrente do banco
        if voltage_v > 0:
            self.current_a = (self.reactive_power_kvar * 1000) / (SQRT3 * voltage_v)

        # Temperatura (capacitores aquecem com a corrente)
        target_temp = 35.0 + self.current_a * 0.05
        self.temperature_c += (target_temp - self.temperature_c) * dt / 300.0


# ============================================================================
# CCM - CENTRO DE CONTROLE DE MOTORES
# ============================================================================

@dataclass
class CCMDrawer:
    """
    Gaveta do CCM (Motor Control Center Drawer)
    Contém: Disjuntor, Contator, Relé térmico/eletrônico, Softstart ou VFD
    """
    name: str
    motor_name: str
    motor_power_kw: float
    motor_voltage_v: float = 480.0

    # Tipo de partida
    starter_type: str = "DOL"  # DOL, Softstart, VFD

    # Estado
    breaker_closed: bool = True
    contactor_on: bool = False
    running: bool = False

    # Equipamentos
    softstart: Optional[Softstart] = None
    vfd: Optional[VFD] = None
    relay: Optional[ProtectionRelay] = None
    meter: Optional[MultiMeter] = None

    # Medições
    current_a: float = 0.0
    power_kw: float = 0.0
    power_kvar: float = 0.0

    def __post_init__(self):
        """Inicializa equipamentos da gaveta"""
        nominal_current = (self.motor_power_kw * 1000) / (SQRT3 * self.motor_voltage_v * 0.85)

        if self.starter_type == "Softstart":
            self.softstart = Softstart(
                name=f"{self.name}_SS",
                motor_power_kw=self.motor_power_kw,
                motor_voltage_v=self.motor_voltage_v,
                motor_current_a=nominal_current
            )
        elif self.starter_type == "VFD":
            self.vfd = VFD(
                name=f"{self.name}_VFD",
                motor_power_kw=self.motor_power_kw,
                motor_voltage_v=self.motor_voltage_v,
                motor_current_a=nominal_current
            )

        # Relé de proteção
        self.relay = ProtectionRelay(
            name=f"{self.name}_REL",
            pickup_50_a=nominal_current * 8,   # 800% para instantâneo
            pickup_51_a=nominal_current * 1.2  # 120% para temporizado
        )

        # Multi-medidor
        self.meter = MultiMeter(
            name=f"{self.name}_PM",
            nominal_voltage_v=self.motor_voltage_v,
            nominal_current_a=nominal_current
        )

    def step(self, load_pct: float, dt: float):
        """Atualiza estado da gaveta"""
        if not self.breaker_closed:
            self.current_a = 0
            self.power_kw = 0
            self.power_kvar = 0
            self.running = False
            return

        # Atualiza starter baseado no tipo
        if self.starter_type == "Softstart" and self.softstart:
            self.softstart.command_run = self.contactor_on
            self.softstart.step(load_pct, dt)
            self.current_a = self.softstart.output_current_a
            self.power_kw = self.softstart.output_power_kw
            self.running = self.softstart.state == MotorState.RUNNING

        elif self.starter_type == "VFD" and self.vfd:
            self.vfd.command_run = self.contactor_on
            self.vfd.speed_setpoint_pct = 100.0 if self.contactor_on else 0.0
            self.vfd.step(load_pct, dt)
            self.current_a = self.vfd.output_current_a
            self.power_kw = self.vfd.output_power_kw
            self.running = self.vfd.state == MotorState.RUNNING

        else:  # DOL
            if self.contactor_on:
                nominal_current = (self.motor_power_kw * 1000) / (SQRT3 * self.motor_voltage_v * 0.85)
                self.current_a = nominal_current * (0.3 + 0.7 * load_pct / 100.0)
                self.power_kw = self.motor_power_kw * (0.2 + 0.8 * load_pct / 100.0)
                self.running = True
            else:
                self.current_a = 0
                self.power_kw = 0
                self.running = False

        # Calcula potência reativa (assumindo FP 0.85)
        pf = 0.85
        self.power_kvar = self.power_kw * math.tan(math.acos(pf))

        # Atualiza relé de proteção
        if self.relay:
            self.relay.step(self.current_a, self.motor_voltage_v, dt)
            # Se relé tripar, abre contator
            if self.relay.state == RelayState.TRIP:
                self.contactor_on = False

        # Atualiza medidor
        if self.meter:
            self.meter.update_from_load(self.power_kw, self.power_kvar, pf, dt)


# ============================================================================
# ELETROCENTRO COMPLETO
# ============================================================================

class EletrocentroSimulator:
    """
    Simulador completo do Eletrocentro

    Equipamentos:
    - 1 Transformador 1000 kVA, 13.8kV/480V
    - 1 CCM com 8 gavetas (motores com diferentes tipos de partida)
    - 3 Multi-medidores de setor
    - 1 Banco de capacitores 300 kVAR
    - Relés de proteção em cada alimentador
    """

    def __init__(self):
        self.time_s = 0.0

        # Transformador principal
        self.transformer = PowerTransformer(
            name="TR01_PRINCIPAL",
            capacity_kva=1000.0,
            primary_voltage_v=13800.0,
            secondary_voltage_v=480.0
        )

        # CCM - Gavetas de motores
        self.ccm_drawers: Dict[str, CCMDrawer] = {
            # Correias transportadoras (Softstart)
            "CCM01_CORR01": CCMDrawer(
                name="CCM01_CORR01",
                motor_name="Motor Correia 01",
                motor_power_kw=75.0,
                starter_type="Softstart"
            ),
            "CCM01_CORR02": CCMDrawer(
                name="CCM01_CORR02",
                motor_name="Motor Correia 02",
                motor_power_kw=90.0,
                starter_type="Softstart"
            ),
            "CCM01_CORR03": CCMDrawer(
                name="CCM01_CORR03",
                motor_name="Motor Correia 03",
                motor_power_kw=90.0,
                starter_type="Softstart"
            ),
            # Shiploader (VFD para controle de velocidade)
            "CCM01_SLD01": CCMDrawer(
                name="CCM01_SLD01",
                motor_name="Motor Shiploader Lança",
                motor_power_kw=110.0,
                starter_type="VFD"
            ),
            "CCM01_SLD02": CCMDrawer(
                name="CCM01_SLD02",
                motor_name="Motor Shiploader Giro",
                motor_power_kw=55.0,
                starter_type="VFD"
            ),
            # Elevadores (Softstart)
            "CCM01_ELV01": CCMDrawer(
                name="CCM01_ELV01",
                motor_name="Motor Elevador 01",
                motor_power_kw=45.0,
                starter_type="Softstart"
            ),
            # Ventiladores (DOL - partida direta)
            "CCM01_VNT01": CCMDrawer(
                name="CCM01_VNT01",
                motor_name="Ventilador Exaustão 01",
                motor_power_kw=15.0,
                starter_type="DOL"
            ),
            "CCM01_VNT02": CCMDrawer(
                name="CCM01_VNT02",
                motor_name="Ventilador Exaustão 02",
                motor_power_kw=15.0,
                starter_type="DOL"
            ),
        }

        # Multi-medidores de setor
        self.sector_meters: Dict[str, MultiMeter] = {
            "PM_GERAL": MultiMeter(name="PM_GERAL", nominal_voltage_v=480.0, nominal_current_a=1200.0),
            "PM_CCM01": MultiMeter(name="PM_CCM01", nominal_voltage_v=480.0, nominal_current_a=600.0),
            "PM_ILUM": MultiMeter(name="PM_ILUM", nominal_voltage_v=480.0, nominal_current_a=100.0),
        }

        # Banco de capacitores
        self.capacitor_bank = CapacitorBank(
            name="BC01",
            total_kvar=300.0,
            num_stages=6,
            target_pf=0.92
        )

        # Relé de proteção geral
        self.main_relay = ProtectionRelay(
            name="REL_GERAL",
            pickup_50_a=2000.0,
            pickup_51_a=1200.0
        )

        # Acumuladores
        self.total_energy_kwh = 0.0
        self.total_reactive_kvarh = 0.0
        self.peak_demand_kw = 0.0

        # Cargas auxiliares (iluminação, ar condicionado, etc.)
        self.aux_load_kw = 25.0
        self.aux_load_kvar = 10.0

        logger.info("✅ Eletrocentro Simulator initialized")

    def reset(self):
        """Reset do simulador"""
        self.time_s = 0.0
        self.total_energy_kwh = 0.0
        self.total_reactive_kvarh = 0.0
        self.peak_demand_kw = 0.0

        for drawer in self.ccm_drawers.values():
            drawer.contactor_on = False
            drawer.breaker_closed = True
            if drawer.relay:
                drawer.relay.reset()

        self.capacitor_bank.stages_on = 0
        self.main_relay.reset()

        logger.info("🔄 Eletrocentro reset")

    def start_all_motors(self):
        """Liga todos os motores"""
        for drawer in self.ccm_drawers.values():
            drawer.contactor_on = True
        logger.info("▶️ All motors started")

    def stop_all_motors(self):
        """Desliga todos os motores"""
        for drawer in self.ccm_drawers.values():
            drawer.contactor_on = False
        logger.info("⏹️ All motors stopped")

    def step(self, motor_loads: Dict[str, float], dt: float = 1.0):
        """
        Executa um passo de simulação

        Args:
            motor_loads: Dict com cargas dos motores (0-100%)
                Ex: {"CCM01_CORR01": 75.0, "CCM01_CORR02": 80.0, ...}
            dt: Intervalo de tempo em segundos
        """
        self.time_s += dt

        # Atualiza cada gaveta do CCM
        total_kw = self.aux_load_kw
        total_kvar = self.aux_load_kvar

        for name, drawer in self.ccm_drawers.items():
            load_pct = motor_loads.get(name, 50.0)  # Default 50% se não especificado
            drawer.step(load_pct, dt)
            total_kw += drawer.power_kw
            total_kvar += drawer.power_kvar

        # Banco de capacitores compensa reativo
        self.capacitor_bank.step(total_kw, total_kvar, 480.0, dt)
        compensated_kvar = total_kvar - self.capacitor_bank.reactive_power_kvar

        # Atualiza transformador com carga total
        self.transformer.step(total_kw, compensated_kvar, dt)

        # Atualiza medidores de setor
        ccm_kw = sum(d.power_kw for d in self.ccm_drawers.values())
        ccm_kvar = sum(d.power_kvar for d in self.ccm_drawers.values())

        self.sector_meters["PM_GERAL"].update_from_load(
            total_kw, compensated_kvar, self.transformer.power_factor, dt
        )
        self.sector_meters["PM_CCM01"].update_from_load(
            ccm_kw, ccm_kvar, 0.85, dt
        )
        self.sector_meters["PM_ILUM"].update_from_load(
            self.aux_load_kw, self.aux_load_kvar, 0.9, dt
        )

        # Atualiza relé geral
        total_current = self.transformer.secondary_current_a
        self.main_relay.step(total_current, 480.0, dt)

        # Acumuladores
        self.total_energy_kwh += (total_kw * dt) / 3600.0
        self.total_reactive_kvarh += (abs(compensated_kvar) * dt) / 3600.0
        self.peak_demand_kw = max(self.peak_demand_kw, total_kw)

    def get_all_tags(self) -> Dict[str, Any]:
        """
        Retorna todas as tags do Eletrocentro para o OPC-UA server
        """
        tags = {}

        # ===== TRANSFORMADOR =====
        tags['TR01_LOAD_PCT_PV'] = self.transformer.load_pct
        tags['TR01_POWER_KW_PV'] = self.transformer.power_kw
        tags['TR01_POWER_KVAR_PV'] = self.transformer.power_kvar
        tags['TR01_POWER_KVA_PV'] = self.transformer.power_kva
        tags['TR01_PF_PV'] = self.transformer.power_factor
        tags['TR01_CURRENT_PRI_A_PV'] = self.transformer.primary_current_a
        tags['TR01_CURRENT_SEC_A_PV'] = self.transformer.secondary_current_a
        tags['TR01_TEMP_WINDING_C_PV'] = self.transformer.winding_temp_c
        tags['TR01_TEMP_OIL_C_PV'] = self.transformer.oil_temp_c
        tags['TR01_ALARM_OVERTEMP_PV'] = 1.0 if self.transformer.overtemp_alarm else 0.0
        tags['TR01_ALARM_OVERLOAD_PV'] = 1.0 if self.transformer.overload_alarm else 0.0

        # ===== CCM GAVETAS =====
        for name, drawer in self.ccm_drawers.items():
            prefix = name.replace("CCM01_", "")

            # Estado geral
            tags[f'{prefix}_RUNNING_PV'] = 1.0 if drawer.running else 0.0
            tags[f'{prefix}_BREAKER_PV'] = 1.0 if drawer.breaker_closed else 0.0
            tags[f'{prefix}_CONTACTOR_PV'] = 1.0 if drawer.contactor_on else 0.0

            # Medições
            tags[f'{prefix}_CURRENT_A_PV'] = drawer.current_a
            tags[f'{prefix}_POWER_KW_PV'] = drawer.power_kw
            tags[f'{prefix}_POWER_KVAR_PV'] = drawer.power_kvar

            # Softstart específico
            if drawer.softstart:
                ss = drawer.softstart
                tags[f'{prefix}_SS_STATE_PV'] = float(list(MotorState).index(ss.state))
                tags[f'{prefix}_SS_VOLTAGE_PCT_PV'] = ss.output_voltage_pct
                tags[f'{prefix}_SS_MOTOR_TEMP_PCT_PV'] = ss.motor_temp_pct
                tags[f'{prefix}_SS_FAULT_PV'] = 1.0 if ss.state == MotorState.FAULT else 0.0

            # VFD específico
            if drawer.vfd:
                vfd = drawer.vfd
                tags[f'{prefix}_VFD_STATE_PV'] = float(list(MotorState).index(vfd.state))
                tags[f'{prefix}_VFD_FREQ_HZ_PV'] = vfd.output_frequency_hz
                tags[f'{prefix}_VFD_VOLTAGE_V_PV'] = vfd.output_voltage_v
                tags[f'{prefix}_VFD_SPEED_RPM_PV'] = vfd.motor_speed_rpm
                tags[f'{prefix}_VFD_TORQUE_PCT_PV'] = vfd.output_torque_pct
                tags[f'{prefix}_VFD_DC_BUS_V_PV'] = vfd.dc_bus_voltage_v
                tags[f'{prefix}_VFD_TEMP_C_PV'] = vfd.heatsink_temp_c
                tags[f'{prefix}_VFD_ENERGY_KWH_PV'] = vfd.energy_kwh
                tags[f'{prefix}_VFD_FAULT_PV'] = 1.0 if vfd.state == MotorState.FAULT else 0.0

            # Relé de proteção
            if drawer.relay:
                rel = drawer.relay
                tags[f'{prefix}_REL_STATE_PV'] = float(list(RelayState).index(rel.state))
                tags[f'{prefix}_REL_THERMAL_PCT_PV'] = rel.thermal_pct
                tags[f'{prefix}_REL_FN50_PV'] = 1.0 if rel.fn_50_active else 0.0
                tags[f'{prefix}_REL_FN51_PV'] = 1.0 if rel.fn_51_active else 0.0
                tags[f'{prefix}_REL_FN49_PV'] = 1.0 if rel.fn_49_active else 0.0
                tags[f'{prefix}_REL_TRIP_PV'] = 1.0 if rel.state == RelayState.TRIP else 0.0

            # Medidor da gaveta
            if drawer.meter:
                m = drawer.meter
                tags[f'{prefix}_PM_V_AB_PV'] = m.voltage.v_ab
                tags[f'{prefix}_PM_V_BC_PV'] = m.voltage.v_bc
                tags[f'{prefix}_PM_V_CA_PV'] = m.voltage.v_ca
                tags[f'{prefix}_PM_I_A_PV'] = m.current.i_a
                tags[f'{prefix}_PM_I_B_PV'] = m.current.i_b
                tags[f'{prefix}_PM_I_C_PV'] = m.current.i_c
                tags[f'{prefix}_PM_FREQ_HZ_PV'] = m.frequency_hz
                tags[f'{prefix}_PM_PF_PV'] = m.power_factor
                tags[f'{prefix}_PM_KWH_PV'] = m.energy_kwh

        # ===== MEDIDORES DE SETOR =====
        for name, meter in self.sector_meters.items():
            prefix = name
            tags[f'{prefix}_V_AB_PV'] = meter.voltage.v_ab
            tags[f'{prefix}_V_BC_PV'] = meter.voltage.v_bc
            tags[f'{prefix}_V_CA_PV'] = meter.voltage.v_ca
            tags[f'{prefix}_V_AN_PV'] = meter.voltage.v_an
            tags[f'{prefix}_V_BN_PV'] = meter.voltage.v_bn
            tags[f'{prefix}_V_CN_PV'] = meter.voltage.v_cn
            tags[f'{prefix}_I_A_PV'] = meter.current.i_a
            tags[f'{prefix}_I_B_PV'] = meter.current.i_b
            tags[f'{prefix}_I_C_PV'] = meter.current.i_c
            tags[f'{prefix}_I_N_PV'] = meter.current.i_n
            tags[f'{prefix}_KW_PV'] = meter.power_kw
            tags[f'{prefix}_KVAR_PV'] = meter.power_kvar
            tags[f'{prefix}_KVA_PV'] = meter.power_kva
            tags[f'{prefix}_PF_PV'] = meter.power_factor
            tags[f'{prefix}_FREQ_HZ_PV'] = meter.frequency_hz
            tags[f'{prefix}_KWH_PV'] = meter.energy_kwh
            tags[f'{prefix}_KVARH_PV'] = meter.energy_kvarh
            tags[f'{prefix}_THD_V_PCT_PV'] = meter.thd_v_pct
            tags[f'{prefix}_THD_I_PCT_PV'] = meter.thd_i_pct
            tags[f'{prefix}_DEMAND_KW_PV'] = meter.demand_kw
            tags[f'{prefix}_DEMAND_MAX_KW_PV'] = meter.demand_max_kw

        # ===== BANCO DE CAPACITORES =====
        tags['BC01_STAGES_ON_PV'] = float(self.capacitor_bank.stages_on)
        tags['BC01_STAGES_TOTAL_PV'] = float(self.capacitor_bank.num_stages)
        tags['BC01_KVAR_PV'] = self.capacitor_bank.reactive_power_kvar
        tags['BC01_CURRENT_A_PV'] = self.capacitor_bank.current_a
        tags['BC01_TEMP_C_PV'] = self.capacitor_bank.temperature_c

        # ===== RELÉ GERAL =====
        tags['REL_GERAL_STATE_PV'] = float(list(RelayState).index(self.main_relay.state))
        tags['REL_GERAL_THERMAL_PCT_PV'] = self.main_relay.thermal_pct
        tags['REL_GERAL_TRIP_PV'] = 1.0 if self.main_relay.state == RelayState.TRIP else 0.0
        tags['REL_GERAL_TRIP_COUNT_PV'] = float(self.main_relay.trip_count)

        # ===== TOTALIZADORES =====
        tags['ELETRO_TOTAL_KWH_PV'] = self.total_energy_kwh
        tags['ELETRO_TOTAL_KVARH_PV'] = self.total_reactive_kvarh
        tags['ELETRO_PEAK_DEMAND_KW_PV'] = self.peak_demand_kw
        tags['ELETRO_TIME_S_PV'] = self.time_s

        return tags

    def get_status(self) -> Dict:
        """Retorna status completo para API REST"""
        return {
            "time_s": self.time_s,
            "transformer": {
                "name": self.transformer.name,
                "load_pct": round(self.transformer.load_pct, 1),
                "power_kw": round(self.transformer.power_kw, 1),
                "power_kvar": round(self.transformer.power_kvar, 1),
                "power_factor": round(self.transformer.power_factor, 3),
                "winding_temp_c": round(self.transformer.winding_temp_c, 1),
                "oil_temp_c": round(self.transformer.oil_temp_c, 1),
                "alarms": {
                    "overtemp": self.transformer.overtemp_alarm,
                    "overload": self.transformer.overload_alarm
                }
            },
            "ccm_drawers": [
                {
                    "name": name,
                    "motor": drawer.motor_name,
                    "type": drawer.starter_type,
                    "running": drawer.running,
                    "current_a": round(drawer.current_a, 1),
                    "power_kw": round(drawer.power_kw, 1),
                    "relay_state": drawer.relay.state.value if drawer.relay else "N/A",
                    "thermal_pct": round(drawer.relay.thermal_pct, 1) if drawer.relay else 0
                }
                for name, drawer in self.ccm_drawers.items()
            ],
            "sector_meters": [
                {
                    "name": name,
                    "power_kw": round(meter.power_kw, 1),
                    "power_factor": round(meter.power_factor, 3),
                    "energy_kwh": round(meter.energy_kwh, 1),
                    "demand_kw": round(meter.demand_kw, 1)
                }
                for name, meter in self.sector_meters.items()
            ],
            "capacitor_bank": {
                "name": self.capacitor_bank.name,
                "stages_on": self.capacitor_bank.stages_on,
                "stages_total": self.capacitor_bank.num_stages,
                "kvar": round(self.capacitor_bank.reactive_power_kvar, 1)
            },
            "totals": {
                "energy_kwh": round(self.total_energy_kwh, 1),
                "reactive_kvarh": round(self.total_reactive_kvarh, 1),
                "peak_demand_kw": round(self.peak_demand_kw, 1)
            }
        }


# ============================================================================
# SINGLETON
# ============================================================================

_eletrocentro_instance: Optional[EletrocentroSimulator] = None


def get_eletrocentro() -> EletrocentroSimulator:
    """Retorna instância global do simulador de eletrocentro"""
    global _eletrocentro_instance
    if _eletrocentro_instance is None:
        _eletrocentro_instance = EletrocentroSimulator()
    return _eletrocentro_instance
