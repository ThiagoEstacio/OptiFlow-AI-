"""
Lightweight Industrial Simulator - Grain Terminal
==================================================

Simulador simplificado SEM DEM physics para:
- Gerar tags OPC-UA realistas de processo e elétricos
- Testar Gateway, IA/ML, análises de energia e falhas
- Performance < 100ms por step

Grandezas Simuladas:
- PROCESSO: Vazão (t/h), Velocidade (m/s), Nível (%), Pressão (bar)
- ELÉTRICO: Corrente (A), Tensão (V), Potência (kW), Energia (kWh), FP
- FALHAS: Sobrecarga, desalinhamento, aquecimento, vibração
"""

import logging
import random
import math
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class FirstOrderLag:
    """Modelo de primeira ordem para resposta dinâmica realista"""
    value: float = 0.0
    tau: float = 5.0  # Constante de tempo (segundos)

    def update(self, setpoint: float, dt: float) -> float:
        """Atualiza valor com dinâmica de primeira ordem"""
        alpha = dt / (self.tau + dt)
        self.value += alpha * (setpoint - self.value)
        # Adiciona ruído realista (±2%)
        noise = random.gauss(0, 0.02 * abs(setpoint)) if setpoint > 0 else 0
        return max(0, self.value + noise)


@dataclass
class Gate:
    """Comporta de dosagem (Feeding Gate)"""
    name: str
    setpoint_pct: float = 0.0  # Abertura setpoint (0-100%)
    opening_pct: float = 0.0   # Abertura real (0-100%)
    flow_tph: float = 0.0      # Vazão (ton/h)

    # Dinâmica
    lag_opening: FirstOrderLag = field(default_factory=lambda: FirstOrderLag(tau=3.0))
    lag_flow: FirstOrderLag = field(default_factory=lambda: FirstOrderLag(tau=2.0))

    # Falhas
    failure: bool = False
    stuck_position: Optional[float] = None

    def step(self, dt: float):
        """Simula step de tempo"""
        # Se falhou, trava na posição
        if self.failure and self.stuck_position is not None:
            self.opening_pct = self.stuck_position
        else:
            # Abertura segue setpoint com lag
            self.opening_pct = self.lag_opening.update(self.setpoint_pct, dt)

        # Vazão é proporcional à abertura (modelo simples)
        # Capacidade máxima: 250 t/h por comporta
        target_flow = (self.opening_pct / 100.0) * 250.0
        self.flow_tph = self.lag_flow.update(target_flow, dt)


@dataclass
class ConveyorBelt:
    """Correia transportadora"""
    name: str
    capacity_tph: float = 1500.0  # Capacidade nominal (t/h)

    # Estados
    running: bool = False
    speed_mps: float = 0.0  # Velocidade (m/s)
    flow_tph: float = 0.0   # Vazão atual (t/h)
    load_pct: float = 0.0   # Carregamento (%)

    # Motor elétrico
    motor_power_kw: float = 0.0     # Potência ativa
    motor_current_a: float = 0.0    # Corrente
    motor_voltage_v: float = 440.0  # Tensão (fixa)
    motor_pf: float = 0.85          # Fator de potência
    motor_temp_c: float = 25.0      # Temperatura

    # Dinâmica
    lag_speed: FirstOrderLag = field(default_factory=lambda: FirstOrderLag(tau=4.0))
    lag_power: FirstOrderLag = field(default_factory=lambda: FirstOrderLag(tau=1.5))

    # Falhas
    misalignment: float = 0.0  # Desalinhamento (0-1)
    bearing_wear: float = 0.0  # Desgaste rolamento (0-1)

    def step(self, input_flow_tph: float, dt: float):
        """Simula step de tempo"""
        if not self.running:
            self.speed_mps = 0.0
            self.flow_tph = 0.0
            self.load_pct = 0.0
            self.motor_power_kw = 0.0
            self.motor_current_a = 0.0
            self.motor_temp_c = max(25.0, self.motor_temp_c - dt * 0.5)  # Resfria
            return

        # Vazão = input limitado pela capacidade
        self.flow_tph = min(input_flow_tph, self.capacity_tph)

        # Carregamento
        self.load_pct = (self.flow_tph / self.capacity_tph) * 100.0

        # Velocidade proporcional à carga (3.5 m/s nominal)
        target_speed = 1.0 + (self.load_pct / 100.0) * 2.5
        self.speed_mps = self.lag_speed.update(target_speed, dt)

        # Potência = potência base + carga + perdas por falhas
        base_power = 15.0  # kW (motor vazio)
        load_power = (self.load_pct / 100.0) * 75.0  # kW (carga)
        failure_power = self.misalignment * 10.0 + self.bearing_wear * 15.0
        target_power = base_power + load_power + failure_power
        self.motor_power_kw = self.lag_power.update(target_power, dt)

        # Corrente (P = √3 * V * I * PF)
        self.motor_current_a = self.motor_power_kw * 1000 / (math.sqrt(3) * self.motor_voltage_v * self.motor_pf)

        # Temperatura sobe com carga e falhas
        heat_rate = (self.load_pct / 100.0) * 0.3 + failure_power * 0.5
        cooling_rate = max(0, self.motor_temp_c - 25.0) * 0.05
        self.motor_temp_c += (heat_rate - cooling_rate) * dt
        self.motor_temp_c = min(self.motor_temp_c, 120.0)  # Limite físico


@dataclass
class Shiploader:
    """Carregador de navios (Shiploader)"""
    name: str
    setpoint_tph: float = 0.0
    flow_tph: float = 0.0
    boom_angle_deg: float = 45.0
    slewing_deg: float = 0.0

    # Motores
    power_kw: float = 0.0
    current_a: float = 0.0

    lag_flow: FirstOrderLag = field(default_factory=lambda: FirstOrderLag(tau=3.0))

    def step(self, input_flow_tph: float, dt: float):
        """Simula step"""
        # Vazão segue entrada limitada por setpoint
        target_flow = min(input_flow_tph, self.setpoint_tph)
        self.flow_tph = self.lag_flow.update(target_flow, dt)

        # Potência proporcional à vazão
        self.power_kw = 20.0 + (self.flow_tph / 1500.0) * 150.0
        self.current_a = self.power_kw * 1000 / (math.sqrt(3) * 440 * 0.85)


class LightweightGrainTerminalSimulator:
    """
    Simulador lightweight de terminal graneleiro 1500 t/h

    Equipamentos:
    - 7 Gates (comportas de dosagem)
    - 3 Correias (CORR01, CORR02, CORR03)
    - 1 Shiploader (carregador de navios)
    """

    def __init__(self):
        self.time_s = 0.0
        self.running = False
        self._simulation_task = None  # Task para loop automático

        # Equipamentos
        self.gates = [Gate(name=f"GATE_{i+1:02d}") for i in range(7)]

        self.belts = {
            "CORR01": ConveyorBelt(name="CORR01", capacity_tph=500),
            "CORR02": ConveyorBelt(name="CORR02", capacity_tph=1500),
            "CORR03": ConveyorBelt(name="CORR03", capacity_tph=1500),
        }

        self.shiploader = Shiploader(name="SHIPLOADER_01")

        # Acumuladores
        self.total_mass_t = 0.0
        self.total_kwh = 0.0
        self.warehouse_level_pct = 75.0  # Nível inicial do armazém

        # Falhas programadas
        self.failure_events = []
        self._schedule_random_failures()

        # Test counter for frontend real-time visualization (0-10, auto-reset)
        self.test_counter = 0

        logger.info("✅ Lightweight simulator initialized (PLC Virtual)")

    def _schedule_random_failures(self):
        """Agenda falhas aleatórias para treinar ML"""
        # Falha de gate travado aos 300s
        self.failure_events.append({
            "time": 300,
            "type": "gate_stuck",
            "gate_id": 2,
            "position": 45.0
        })

        # Desalinhamento de correia aos 600s
        self.failure_events.append({
            "time": 600,
            "type": "belt_misalignment",
            "belt": "CORR01",
            "severity": 0.3
        })

    def reset(self):
        """Reset simulador"""
        self.time_s = 0.0
        self.running = False
        self.total_mass_t = 0.0
        self.total_kwh = 0.0
        self.warehouse_level_pct = 75.0
        self.test_counter = 0

        for gate in self.gates:
            gate.setpoint_pct = 0.0
            gate.opening_pct = 0.0
            gate.flow_tph = 0.0
            gate.failure = False

        for belt in self.belts.values():
            belt.running = False
            belt.flow_tph = 0.0
            belt.misalignment = 0.0
            belt.bearing_wear = 0.0

        self.shiploader.setpoint_tph = 0.0
        self.shiploader.flow_tph = 0.0

        logger.info("🔄 Simulator reset")

    def start(self):
        """Inicia simulação com loop automático"""
        self.running = True

        # Liga correias
        for belt in self.belts.values():
            belt.running = True

        # Define setpoints iniciais
        self.shiploader.setpoint_tph = 1500.0

        # Inicia loop automático se ainda não está rodando
        if self._simulation_task is None or self._simulation_task.done():
            import asyncio
            self._simulation_task = asyncio.create_task(self._auto_simulation_loop())
            logger.info("▶️  Simulator started with auto-update loop")
        else:
            logger.info("▶️  Simulator started")

    def stop(self):
        """Para simulação e cancela loop automático"""
        self.running = False

        # Cancela task de simulação automática
        if self._simulation_task and not self._simulation_task.done():
            self._simulation_task.cancel()
            logger.info("⏹️  Auto-simulation loop cancelled")

        for gate in self.gates:
            gate.setpoint_pct = 0.0

        for belt in self.belts.values():
            belt.running = False

        self.shiploader.setpoint_tph = 0.0

        logger.info("⏹️  Simulator stopped")
    
    async def _auto_simulation_loop(self):
        """Loop automático que avança a simulação a cada segundo"""
        import asyncio
        logger.info("🔄 Auto-simulation loop started (1 step/second)")
        
        try:
            while self.running:
                # Avança simulação em 1 segundo
                await self.step_async(1.0)
                
                # Aguarda 1 segundo antes do próximo step
                await asyncio.sleep(1.0)
        
        except asyncio.CancelledError:
            logger.info("🔄 Auto-simulation loop cancelled")
        
        except Exception as e:
            logger.error(f"❌ Error in auto-simulation loop: {e}", exc_info=True)
        
        finally:
            logger.info("🔄 Auto-simulation loop stopped")

    async def step_async(self, dt_s: float = 1.0):
        """
        Executa step de simulação (async version for Kafka publishing)

        PERFORMANCE TARGET: < 100ms
        """
        if not self.running:
            return

        self.time_s += dt_s

        # Processa falhas programadas
        self._process_failures()

        # 1. Gates → vazão total
        total_gate_flow = sum(gate.flow_tph for gate in self.gates)

        for gate in self.gates:
            gate.step(dt_s)

        # 2. CORR01 (recebe de gates 1-3)
        corr01_input = sum(self.gates[i].flow_tph for i in range(3))
        self.belts["CORR01"].step(corr01_input, dt_s)

        # 3. CORR02 (recebe de gates 4-7 + CORR01)
        corr02_input = sum(self.gates[i].flow_tph for i in range(3, 7)) + self.belts["CORR01"].flow_tph
        self.belts["CORR02"].step(corr02_input, dt_s)

        # 4. CORR03 (recebe de CORR02)
        self.belts["CORR03"].step(self.belts["CORR02"].flow_tph, dt_s)

        # 5. Shiploader (recebe de CORR03)
        self.shiploader.step(self.belts["CORR03"].flow_tph, dt_s)

        # 6. Acumuladores
        mass_loaded_t = (self.shiploader.flow_tph / 3600.0) * dt_s  # t
        self.total_mass_t += mass_loaded_t

        # Energia total (soma de todos motores)
        total_power_kw = sum(belt.motor_power_kw for belt in self.belts.values()) + self.shiploader.power_kw
        energy_kwh = (total_power_kw / 3600.0) * dt_s
        self.total_kwh += energy_kwh

        # Nível do armazém diminui conforme carrega
        self.warehouse_level_pct -= (mass_loaded_t / 5000.0) * 100.0  # Armazém de 5000t
        self.warehouse_level_pct = max(0, self.warehouse_level_pct)

        # Incrementa test_counter (0-10, reset automático para visualização em tempo real)
        self.test_counter += 1
        if self.test_counter > 10:
            self.test_counter = 0

        # Simulador atualiza estado interno apenas
        # Gateway é responsável por ler os valores e publicar no Kafka



    def step(self, dt_s: float = 1.0):
        """
        Executa step de simulação (sync wrapper)

        PERFORMANCE TARGET: < 100ms
        """
        if not self.running:
            return

        self.time_s += dt_s

        # Processa falhas programadas
        self._process_failures()

        # 1. Gates → vazão total
        total_gate_flow = sum(gate.flow_tph for gate in self.gates)

        for gate in self.gates:
            gate.step(dt_s)

        # 2. CORR01 (recebe de gates 1-3)
        corr01_input = sum(self.gates[i].flow_tph for i in range(3))
        self.belts["CORR01"].step(corr01_input, dt_s)

        # 3. CORR02 (recebe de gates 4-7 + CORR01)
        corr02_input = sum(self.gates[i].flow_tph for i in range(3, 7)) + self.belts["CORR01"].flow_tph
        self.belts["CORR02"].step(corr02_input, dt_s)

        # 4. CORR03 (recebe de CORR02)
        self.belts["CORR03"].step(self.belts["CORR02"].flow_tph, dt_s)

        # 5. Shiploader (recebe de CORR03)
        self.shiploader.step(self.belts["CORR03"].flow_tph, dt_s)

        # 6. Acumuladores
        mass_loaded_t = (self.shiploader.flow_tph / 3600.0) * dt_s  # t
        self.total_mass_t += mass_loaded_t

        # Energia total (soma de todos motores)
        total_power_kw = sum(belt.motor_power_kw for belt in self.belts.values()) + self.shiploader.power_kw
        energy_kwh = (total_power_kw / 3600.0) * dt_s
        self.total_kwh += energy_kwh

        # Nível do armazém diminui conforme carrega
        self.warehouse_level_pct -= (mass_loaded_t / 5000.0) * 100.0  # Armazém de 5000t
        self.warehouse_level_pct = max(0, self.warehouse_level_pct)

        # Incrementa test_counter (0-10, reset automático para visualização em tempo real)
        self.test_counter += 1
        if self.test_counter > 10:
            self.test_counter = 0

    def _process_failures(self):
        """Processa falhas programadas"""
        for event in list(self.failure_events):
            if self.time_s >= event["time"]:
                if event["type"] == "gate_stuck":
                    gate = self.gates[event["gate_id"]]
                    gate.failure = True
                    gate.stuck_position = event["position"]
                    logger.warning(f"⚠️  FAILURE: {gate.name} stuck at {event['position']}%")

                elif event["type"] == "belt_misalignment":
                    belt = self.belts[event["belt"]]
                    belt.misalignment = event["severity"]
                    logger.warning(f"⚠️  FAILURE: {belt.name} misalignment {event['severity']*100}%")

                self.failure_events.remove(event)

    def get_status(self) -> Dict:
        """Retorna status completo para API"""
        return {
            "system": {
                "running": self.running,
                "time_s": self.time_s,
                "total_mass_t": round(self.total_mass_t, 2),
                "total_kWh": round(self.total_kwh, 2),
                "warehouse_level_pct": round(self.warehouse_level_pct, 1),
                "kWh_per_ton": round(self.total_kwh / self.total_mass_t, 3) if self.total_mass_t > 0 else 0,
                "cost_BRL": round(self.total_kwh * 0.65, 2),  # R$ 0.65/kWh
            },
            "gates": [
                {
                    "name": g.name,
                    "setpoint_pct": round(g.setpoint_pct, 1),
                    "opening_pct": round(g.opening_pct, 1),
                    "flow_tph": round(g.flow_tph, 1),
                    "failure": g.failure,
                }
                for g in self.gates
            ],
            "belts": [
                {
                    "name": b.name,
                    "running": b.running,
                    "speed_mps": round(b.speed_mps, 2),
                    "flow_tph": round(b.flow_tph, 1),
                    "load_pct": round(b.load_pct, 1),
                    "power_kw": round(b.motor_power_kw, 1),
                    "current_a": round(b.motor_current_a, 1),
                    "temp_c": round(b.motor_temp_c, 1),
                    "misalignment": round(b.misalignment, 2),
                }
                for b in self.belts.values()
            ],
            "shiploader": {
                "name": self.shiploader.name,
                "setpoint_tph": round(self.shiploader.setpoint_tph, 1),
                "flow_tph": round(self.shiploader.flow_tph, 1),
                "power_kw": round(self.shiploader.power_kw, 1),
                "current_a": round(self.shiploader.current_a, 1),
            }
        }

    def set_gate_setpoint(self, gate_id: int, setpoint_pct: float):
        """Define setpoint de uma comporta"""
        if 0 <= gate_id < len(self.gates):
            self.gates[gate_id].setpoint_pct = max(0, min(100, setpoint_pct))

    def set_all_gates_setpoint(self, setpoint_pct: float):
        """Define setpoint de todas as comportas"""
        for gate in self.gates:
            gate.setpoint_pct = max(0, min(100, setpoint_pct))

    def get_all_tags(self) -> Dict[str, Any]:
        """
        Retorna todas as tags do PLC virtual para leitura pelo Gateway.
        
        O Gateway deve chamar este método periodicamente e publicar no Kafka.
        Simula descoberta de tags OPC UA / Modbus.
        """
        tags = {}
        
        # System tags
        tags['SYSTEM_RUNNING_PV'] = 1.0 if self.running else 0.0
        tags['SYSTEM_TIME_S_PV'] = self.time_s
        tags['TOTAL_MASS_T_PV'] = self.total_mass_t
        tags['TOTAL_KWH_PV'] = self.total_kwh
        tags['WAREHOUSE_LEVEL_PCT_PV'] = self.warehouse_level_pct
        tags['TEST_COUNTER_PV'] = float(self.test_counter)
        
        # Gates tags
        for gate in self.gates:
            gate_num = gate.name.split('_')[-1]
            tags[f'ARZ_GATES_GATE{gate_num}_POSICAO_PV'] = gate.opening_pct
            tags[f'ARZ_GATES_GATE{gate_num}_VAZAO_TPH_PV'] = gate.flow_tph
        
        # Belts tags
        for belt in self.belts.values():
            tags[f'{belt.name}_RUNNING_PV'] = 1.0 if belt.running else 0.0
            tags[f'{belt.name}_SPEED_MPS_PV'] = belt.speed_mps
            tags[f'{belt.name}_FLOW_TPH_PV'] = belt.flow_tph
            tags[f'{belt.name}_LOAD_PCT_PV'] = belt.load_pct
            tags[f'{belt.name}_POWER_KW_PV'] = belt.motor_power_kw
            tags[f'{belt.name}_CURRENT_A_PV'] = belt.motor_current_a
            tags[f'{belt.name}_TEMP_C_PV'] = belt.motor_temp_c
            tags[f'{belt.name}_MISALIGNMENT_PV'] = belt.misalignment
        
        # Shiploader tags
        tags['SLD01_SETPOINT_TPH_PV'] = self.shiploader.setpoint_tph
        tags['SLD01_FLOW_TPH_PV'] = self.shiploader.flow_tph
        tags['SLD01_POWER_KW_PV'] = self.shiploader.power_kw
        tags['SLD01_CURRENT_A_PV'] = self.shiploader.current_a
        
        return tags


# Singleton global
_simulator_instance: Optional[LightweightGrainTerminalSimulator] = None


def get_simulator() -> LightweightGrainTerminalSimulator:
    """Retorna instância global do simulador"""
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = LightweightGrainTerminalSimulator()
    return _simulator_instance

