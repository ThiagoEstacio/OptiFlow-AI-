"""
Grain Terminal Process Simulator - Python Backend
Real physics-based simulation of 1500 t/h export line

This is the Python port of the TypeScript simulator for backend OPC-UA server
"""

import math
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# CONFIGURATION (Based on JSON spec)
# ============================================================================

class Config:
    # Assumptions
    SHIPLOADER_MASTER_TPH = 1500
    PRACTICAL_MARGIN = 1.10
    BELT_FILL_FACTOR = 0.70

    # Product
    BULK_DENSITY_T_M3 = 0.75
    MOISTURE_PCT_RANGE = (12, 14)

    # Warehouse
    WAREHOUSE_VOLUME_M3 = 72000
    WAREHOUSE_INITIAL_INVENTORY_T = 50000

    # Gates
    GATES_COUNT = 10
    GATES_Q_PER_GATE_TPH_100PCT = 170
    GATES_ALPHA_SATURATION = 0.10
    GATES_FLOW_CURVE = [
        (0, 0.0, 0),
        (25, 0.3, 42),
        (50, 0.4, 85),
        (75, 0.5, 136),
        (100, 0.6, 170)
    ]  # (open_pct, h_norm_min, q_tph)

    # PI Controller
    PI_KP = 0.12
    PI_KI = 0.02
    PI_A_TOT_LIMITS = (0, 1000)
    PI_GATE_OPEN_LIMITS_PCT = (10, 90)
    PI_INITIAL_GATES = 4
    PI_INITIAL_OPEN_PCT = 50
    PI_RAMP_PCT_PER_S = 5

    # Mechanics
    BELT_CHUTE_LOSSES_PCT = 3
    K_LOAD = 0.45
    K_FRIC = 0.05
    K_WEAR = 0.01

    # Thermal limits (°C)
    TEMP_BEARING_WARN = 60
    TEMP_BEARING_ALARM = 70
    TEMP_BEARING_TRIP = 80
    TEMP_MOTOR_WARN = 85
    TEMP_MOTOR_ALARM = 95
    TEMP_MOTOR_TRIP = 105

    # Electrical
    VOLTAGE_LL = 440
    PF_NOMINAL = 0.92
    TARIFF_PEAK_R_KWH = 1.50

    # Simulation
    DT_S = 1.0


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class GateState:
    id: int
    open_pct: float = 0.0
    open_pct_sp: float = 0.0
    position_fb: float = 0.0
    flow_tph: float = 0.0
    plugged: bool = False
    failure: bool = False


@dataclass
class BeltState:
    id: str
    width_m: float
    speed_mps_nom: float
    motor_kW: float

    running: bool = False
    speed_mps: float = 0.0
    rpm: float = 0.0
    rpm_nom: float = 0.0
    flow_tph: float = 0.0
    load_pct: float = 0.0
    current_A: float = 0.0
    current_nom_A: float = 0.0
    power_kW: float = 0.0
    temp_bearing_C: float = 25.0
    temp_belt_C: float = 25.0
    temp_drum_C: float = 25.0
    misaligned: bool = False
    torn: bool = False
    underspeed_warn: bool = False
    underspeed_alarm: bool = False
    chute_level_pct: float = 0.0
    chute_plugged: bool = False

    # Internal safety timers
    _underspeed_time_s: float = 0.0
    _overload_time_s: float = 0.0
    _chute_high_time_s: float = 0.0


@dataclass
class ElevatorState:
    id: str = "ELV01"
    running: bool = False
    speed_mps: float = 0.0
    flow_tph: float = 0.0
    current_A: float = 0.0
    power_kW: float = 0.0
    temp_motor_C: float = 25.0
    temp_gearbox_C: float = 25.0
    temp_bearing_sup_C: float = 25.0
    temp_bearing_inf_C: float = 25.0
    belt_loose: bool = False
    slip: bool = False
    jammed: bool = False


class CycleState(str, Enum):
    IDLE = "idle"
    FILLING = "filling"
    DISCHARGING = "discharging"


@dataclass
class BalanceState:
    id: str = "BAL01"
    running: bool = False
    cycle_state: CycleState = CycleState.IDLE
    weight_kg: float = 0.0
    target_kg: float = 4500.0  # 4.5 tons per batch for 1500 t/h system
    cycle_count: int = 0
    total_mass_t: float = 0.0
    avg_flow_tph: float = 0.0
    failure: bool = False

    # Internal timing (8s fill + 2s discharge = 10s cycle, 360 cycles/h, 1620 t/h capacity)
    _fill_time_s: float = 8.0
    _discharge_time_s: float = 2.0
    _cycle_elapsed_s: float = 0.0


@dataclass
class ShipLoaderState:
    id: str = "SLD01"
    running: bool = False
    flow_sp_tph: float = 1500.0
    flow_pv_tph: float = 0.0
    position_deg: float = 0.0
    dust_level: float = 0.0
    current_A: float = 0.0
    power_kW: float = 0.0


@dataclass
class PIControllerState:
    error: float = 0.0
    integral: float = 0.0
    output: float = 0.0
    A_tot: float = 0.0
    active_gates: List[int] = field(default_factory=lambda: [1, 2, 3, 4])


@dataclass
class AlarmState:
    tag: str
    active: bool = False
    latched: bool = False
    timestamp: float = 0.0
    count: int = 0


# ============================================================================
# SIMULATOR CLASS
# ============================================================================

class GrainTerminalSimulator:
    """
    Real-time grain terminal process simulator

    Simulates:
    - 10 gates with PI control
    - 3 belts with mechanical/thermal/electrical models
    - Elevator with slip detection
    - Batch scale
    - Shiploader
    - Alarms and interlocks
    - Energy and maintenance
    """

    def __init__(self):
        self.time_s = 0.0
        self.running = False
        self.emergency_stop = False

        # Initialize states
        self.warehouse_inventory_t = Config.WAREHOUSE_INITIAL_INVENTORY_T
        self.warehouse_level_pct = self._calc_warehouse_level()

        # Gates
        self.gates: List[GateState] = []
        for i in range(Config.GATES_COUNT):
            gate = GateState(id=i+1)
            # Start first 4 gates
            if i < Config.PI_INITIAL_GATES:
                gate.open_pct_sp = Config.PI_INITIAL_OPEN_PCT
                gate.open_pct = Config.PI_INITIAL_OPEN_PCT
                gate.position_fb = Config.PI_INITIAL_OPEN_PCT
            self.gates.append(gate)

        # Belts
        self.belts: Dict[str, BeltState] = {
            'CORR01': BeltState(
                id='CORR01',
                width_m=1.5,
                speed_mps_nom=3.2,
                motor_kW=180,
                rpm_nom=(3.2 * 60) / (math.pi * 0.63),
                current_nom_A=180000 / (440 * math.sqrt(3) * 0.92)
            ),
            'CORR02': BeltState(
                id='CORR02',
                width_m=1.4,
                speed_mps_nom=3.0,
                motor_kW=150,
                rpm_nom=(3.0 * 60) / (math.pi * 0.63),
                current_nom_A=150000 / (440 * math.sqrt(3) * 0.92)
            ),
            'CORR03': BeltState(
                id='CORR03',
                width_m=1.6,
                speed_mps_nom=3.2,
                motor_kW=180,
                rpm_nom=(3.2 * 60) / (math.pi * 0.63),
                current_nom_A=180000 / (440 * math.sqrt(3) * 0.92)
            )
        }

        self.elevator = ElevatorState()
        self.balance = BalanceState()
        self.shiploader = ShipLoaderState()

        # Control
        self.pi_controller = PIControllerState()

        # Energy
        self.total_kWh = 0.0
        self.total_mass_t = 0.0
        self.kWh_per_ton = 0.0
        self.cost_BRL = 0.0

        # Alarms
        self.alarms: List[AlarmState] = []
        self.trips: List[AlarmState] = []

        # Health
        self.health: Dict[str, float] = {}
        for gate in self.gates:
            self.health[f'GATE{gate.id:02d}'] = 100.0
        for belt_id in self.belts.keys():
            self.health[belt_id] = 100.0
        self.health['ELV01'] = 100.0
        self.health['BAL01'] = 100.0
        self.health['SLD01'] = 100.0

    # ------------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------------

    def start(self):
        """Start the simulation"""
        self.running = True
        self.shiploader.running = True
        for belt in self.belts.values():
            belt.running = True
        self.elevator.running = True
        self.balance.running = True

    def stop(self):
        """Stop the simulation"""
        self.running = False
        self.shiploader.running = False
        for belt in self.belts.values():
            belt.running = False
        self.elevator.running = False
        self.balance.running = False

        # Close all gates
        for gate in self.gates:
            gate.open_pct_sp = 0.0

    def emergency_stop_trigger(self):
        """Emergency stop - immediate closure"""
        self.emergency_stop = True
        self.stop()
        for gate in self.gates:
            gate.open_pct = 0.0
            gate.open_pct_sp = 0.0
            gate.position_fb = 0.0

    def reset(self):
        """Reset alarms and emergency"""
        self.emergency_stop = False
        self.alarms.clear()
        self.trips.clear()

    def set_shiploader_setpoint(self, tph: float):
        """Set shiploader flow setpoint"""
        self.shiploader.flow_sp_tph = max(0, min(1650, tph))

    def set_gate_manual(self, gate_id: int, open_pct: float):
        """Manually set gate opening"""
        gate = next((g for g in self.gates if g.id == gate_id), None)
        if gate:
            gate.open_pct_sp = max(0, min(100, open_pct))

    def get_tag_value(self, tag_id: str):
        """Get current value of a tag"""
        # Gates
        for gate in self.gates:
            if tag_id == f'GATE{gate.id:02d}_POSITION':
                return gate.position_fb
            elif tag_id == f'GATE{gate.id:02d}_FLOW':
                return gate.flow_tph

        # Belts
        for belt_id, belt in self.belts.items():
            if tag_id == f'{belt_id}_RPM':
                return belt.rpm
            elif tag_id == f'{belt_id}_SPEED':
                return belt.speed_mps
            elif tag_id == f'{belt_id}_FLOW':
                return belt.flow_tph
            elif tag_id == f'{belt_id}_LOAD':
                return belt.load_pct
            elif tag_id == f'{belt_id}_CURRENT':
                return belt.current_A
            elif tag_id == f'{belt_id}_POWER':
                return belt.power_kW
            elif tag_id == f'{belt_id}_TEMP_BEARING':
                return belt.temp_bearing_C
            elif tag_id == f'{belt_id}_RUNNING':
                return belt.running

        # Elevator
        if tag_id == 'ELV01_SPEED':
            return self.elevator.speed_mps
        elif tag_id == 'ELV01_FLOW':
            return self.elevator.flow_tph
        elif tag_id == 'ELV01_CURRENT':
            return self.elevator.current_A
        elif tag_id == 'ELV01_POWER':
            return self.elevator.power_kW
        elif tag_id == 'ELV01_TEMP_MOTOR':
            return self.elevator.temp_motor_C
        elif tag_id == 'ELV01_RUNNING':
            return self.elevator.running

        # Balance
        if tag_id == 'BAL01_WEIGHT':
            return self.balance.weight_kg
        elif tag_id == 'BAL01_TOTAL':
            return self.balance.total_mass_t
        elif tag_id == 'BAL01_FLOW':
            return self.balance.avg_flow_tph
        elif tag_id == 'BAL01_CYCLES':
            return self.balance.cycle_count

        # Shiploader
        if tag_id == 'SLD01_FLOW_SP':
            return self.shiploader.flow_sp_tph
        elif tag_id == 'SLD01_FLOW_PV':
            return self.shiploader.flow_pv_tph
        elif tag_id == 'SLD01_POWER':
            return self.shiploader.power_kW
        elif tag_id == 'SLD01_RUNNING':
            return self.shiploader.running

        # Global
        if tag_id == 'WAREHOUSE_INVENTORY':
            return self.warehouse_inventory_t
        elif tag_id == 'WAREHOUSE_LEVEL':
            return self.warehouse_level_pct
        elif tag_id == 'TOTAL_KWH':
            return self.total_kWh
        elif tag_id == 'TOTAL_MASS':
            return self.total_mass_t
        elif tag_id == 'KWH_PER_TON':
            return self.kWh_per_ton
        elif tag_id == 'SYSTEM_RUNNING':
            return self.running

        return None

    def step(self, dt_s: float = None):
        """Execute one simulation step"""
        if dt_s is None:
            dt_s = Config.DT_S

        if not self.running or self.emergency_stop:
            self._step_dynamics(dt_s)
            return

        self.time_s += dt_s

        # 1. PI Controller
        self._step_pi_controller(dt_s)

        # 2. Gates
        self._step_gates(dt_s)

        # 3. Belts
        self._step_belt('CORR01', dt_s)

        # 4. Elevator
        self._step_elevator(dt_s)

        # 5. Belt CORR02
        self._step_belt('CORR02', dt_s)

        # 6. Balance
        self._step_balance(dt_s)

        # 7. Belt CORR03
        self._step_belt('CORR03', dt_s)

        # 8. Shiploader
        self._step_shiploader(dt_s)

        # 9. Energy
        self._step_energy(dt_s)

        # 10. Alarms
        self._step_alarms()

        # 11. Maintenance
        self._step_maintenance(dt_s)

        # 12. Warehouse
        self._step_warehouse(dt_s)

    # ------------------------------------------------------------------------
    # PRIVATE: CONTROL
    # ------------------------------------------------------------------------

    def _step_pi_controller(self, dt_s: float):
        pi = self.pi_controller

        # PV = flow at CORR03
        PV = self.belts['CORR03'].flow_tph

        # SP = shiploader setpoint
        SP = self.shiploader.flow_sp_tph

        # Error
        error = SP - PV
        pi.error = error

        # PI
        P_term = Config.PI_KP * error
        pi.integral += Config.PI_KI * error * dt_s

        # Anti-windup
        A_min, A_max = Config.PI_A_TOT_LIMITS
        output_raw = P_term + pi.integral

        if output_raw > A_max:
            pi.integral = A_max - P_term
        elif output_raw < A_min:
            pi.integral = A_min - P_term

        pi.output = P_term + pi.integral
        pi.A_tot = max(A_min, min(A_max, pi.output))

        # Distribute
        n_gates = len(pi.active_gates)
        if n_gates > 0:
            open_per_gate = pi.A_tot / n_gates
            open_min, open_max = Config.PI_GATE_OPEN_LIMITS_PCT

            for gate_id in pi.active_gates:
                gate = next((g for g in self.gates if g.id == gate_id), None)
                if gate:
                    gate.open_pct_sp = max(open_min, min(open_max, open_per_gate))

    # ------------------------------------------------------------------------
    # PRIVATE: GATES
    # ------------------------------------------------------------------------

    def _step_gates(self, dt_s: float):
        h_norm = self.warehouse_level_pct / 100.0
        total_flow = 0.0

        for gate in self.gates:
            if gate.failure or gate.plugged:
                gate.flow_tph = 0.0
                continue

            # Position dynamics
            delta = gate.open_pct_sp - gate.open_pct
            max_delta = Config.PI_RAMP_PCT_PER_S * dt_s
            actual_delta = max(-max_delta, min(max_delta, delta))
            gate.open_pct += actual_delta
            gate.position_fb = gate.open_pct

            # Flow from curve
            flow_ideal = self._interpolate_flow_curve(gate.open_pct, h_norm)
            gate.flow_tph = flow_ideal
            total_flow += flow_ideal

        # Saturation penalty
        n_open = sum(1 for g in self.gates if g.open_pct > 5)
        if n_open > 1:
            penalty = 1 - (Config.GATES_ALPHA_SATURATION * (n_open - 1) / Config.GATES_COUNT)
            for gate in self.gates:
                gate.flow_tph *= penalty

    def _interpolate_flow_curve(self, open_pct: float, h_norm: float) -> float:
        curve = Config.GATES_FLOW_CURVE

        # Find bounding points
        lower = curve[0]
        upper = curve[-1]

        for i in range(len(curve) - 1):
            if open_pct >= curve[i][0] and open_pct <= curve[i+1][0]:
                lower = curve[i]
                upper = curve[i+1]
                break

        # Interpolate
        t = (open_pct - lower[0]) / (upper[0] - lower[0] + 0.001)
        q_base = lower[2] + t * (upper[2] - lower[2])

        # Level penalty
        h_required = lower[1] + t * (upper[1] - lower[1])
        level_factor = min(1.0, h_norm / h_required) if h_required > 0 else 1.0

        return q_base * level_factor

    # ------------------------------------------------------------------------
    # PRIVATE: BELTS
    # ------------------------------------------------------------------------

    def _step_belt(self, belt_id: str, dt_s: float):
        belt = self.belts[belt_id]

        if not belt.running:
            belt.speed_mps = 0.0
            belt.rpm = 0.0
            belt.flow_tph = 0.0
            belt.current_A = belt.current_nom_A * 0.2
            belt.power_kW = 0.0
            self._cool_down_belt(belt, dt_s)
            return

        # Input flow
        if belt_id == 'CORR01':
            input_flow = sum(g.flow_tph for g in self.gates)
        elif belt_id == 'CORR02':
            input_flow = self.elevator.flow_tph
        elif belt_id == 'CORR03':
            input_flow = self.balance.avg_flow_tph
        else:
            input_flow = 0.0

        # Chute losses
        input_flow *= (1 - Config.BELT_CHUTE_LOSSES_PCT / 100)

        belt.flow_tph = input_flow

        # Load
        capacity = 1650  # All belts have this capacity
        belt.load_pct = (input_flow / capacity) * 100

        # Mechanics
        torque_factor = 1 + Config.K_LOAD * (belt.load_pct / 100)
        speed_factor = 1 / (1 + 0.1 * max(0, belt.load_pct - 100))

        belt.speed_mps = belt.speed_mps_nom * speed_factor
        belt.rpm = (belt.speed_mps * 60) / (math.pi * 0.63)

        # Electrical
        belt.current_A = belt.current_nom_A * torque_factor
        belt.power_kW = belt.motor_kW * torque_factor

        # Thermal
        self._update_belt_thermal(belt, dt_s)

        # Underspeed
        rpm_pct = (belt.rpm / belt.rpm_nom) * 100 if belt.rpm_nom > 0 else 100
        belt.underspeed_warn = rpm_pct < 90
        belt.underspeed_alarm = rpm_pct < 80

        # Chute level dynamics and safety
        self._update_chute_and_safety(belt, belt_id, input_flow, dt_s)

    def _update_belt_thermal(self, belt: BeltState, dt_s: float):
        ambient_C = 25
        heating_rate = 0.005 * belt.load_pct
        cooling_rate_bearing = 0.02 * (belt.temp_bearing_C - ambient_C)

        belt.temp_bearing_C += (heating_rate - cooling_rate_bearing) * dt_s
        belt.temp_belt_C += (heating_rate * 0.7 - 0.02 * (belt.temp_belt_C - ambient_C)) * dt_s
        belt.temp_drum_C += (heating_rate * 0.8 - 0.02 * (belt.temp_drum_C - ambient_C)) * dt_s

    def _cool_down_belt(self, belt: BeltState, dt_s: float):
        ambient_C = 25
        cool_rate = 0.05
        belt.temp_bearing_C += (ambient_C - belt.temp_bearing_C) * cool_rate * dt_s
        belt.temp_belt_C += (ambient_C - belt.temp_belt_C) * cool_rate * dt_s
        belt.temp_drum_C += (ambient_C - belt.temp_drum_C) * cool_rate * dt_s

    def _update_chute_and_safety(self, belt: BeltState, belt_id: str, input_flow: float, dt_s: float):
        """
        Models material accumulation in transfer chute and safety trips

        Physics:
        - If input > output → material accumulates in chute
        - If chute level > 95% → plugs automatically
        - If underspeed > 10s → trips belt motor
        - If overload > 120% for > 30s → trips belt motor
        """

        # Output capacity (what actually moves on the belt)
        capacity = 1650  # t/h
        actual_output = min(input_flow, capacity * (belt.speed_mps / belt.speed_mps_nom))

        # Chute level dynamics
        if not belt.chute_plugged:
            # Flow difference affects chute level
            # 1% per second per 100 t/h difference
            flow_diff_tph = input_flow - actual_output
            level_rate_pct_per_s = flow_diff_tph / 100.0

            belt.chute_level_pct += level_rate_pct_per_s * dt_s
            belt.chute_level_pct = max(0, min(100, belt.chute_level_pct))

            # Auto-plugging when level too high
            if belt.chute_level_pct > 95:
                belt.chute_plugged = True
                self._set_trip(f'TRIP_{belt_id}_CHUTE_ENTUPIDO')
                self._set_alarm(f'AL_{belt_id}_CHUTE_NIVEL_ALTO')
        else:
            # When plugged, level stays at 100%
            belt.chute_level_pct = 100.0

            # Can only unplug manually (would require maintenance)
            # In real system, operator would need to clear the chute

        # Chute high level alarm (before plugging)
        if belt.chute_level_pct > 80 and not belt.chute_plugged:
            belt._chute_high_time_s += dt_s
            if belt._chute_high_time_s > 5:  # 5 seconds of high level
                self._set_alarm(f'AL_{belt_id}_CHUTE_NIVEL_ALTO')
        else:
            belt._chute_high_time_s = 0.0

        # Underspeed trip (persistent underspeed > 10s)
        if belt.underspeed_alarm:
            belt._underspeed_time_s += dt_s
            if belt._underspeed_time_s > 10.0:
                # Trip the belt motor
                belt.running = False
                self._set_trip(f'TRIP_{belt_id}_SUBVELOCIDADE')
                # Cascade: stop upstream equipment
                self._cascade_stop_upstream(belt_id)
        else:
            belt._underspeed_time_s = 0.0

        # Overload trip (> 120% for > 30s)
        if belt.load_pct > 120:
            belt._overload_time_s += dt_s
            if belt._overload_time_s > 30.0:
                # Trip the belt motor
                belt.running = False
                self._set_trip(f'TRIP_{belt_id}_SOBRECARGA')
                # Cascade: stop upstream equipment
                self._cascade_stop_upstream(belt_id)
        else:
            belt._overload_time_s = 0.0

    def _cascade_stop_upstream(self, belt_id: str):
        """
        Cascade shutdown: when a belt trips, stop upstream equipment

        Chain: GATES → CORR01 → ELEVATOR → CORR02 → BALANCE → CORR03 → SHIPLOADER
        """
        if belt_id == 'CORR01':
            # Close all gates immediately
            for gate in self.gates:
                gate.open_pct_sp = 0.0
            self._set_alarm('AL_SYSTEM_PARADA_EMERGENCIA_CORR01')

        elif belt_id == 'CORR02':
            # Stop elevator
            self.elevator.running = False
            # Reduce CORR01 flow
            for gate in self.gates:
                gate.open_pct_sp = min(gate.open_pct_sp, 20.0)  # Reduce to 20%
            self._set_alarm('AL_SYSTEM_PARADA_EMERGENCIA_CORR02')

        elif belt_id == 'CORR03':
            # Stop balance
            self.balance.running = False
            # Stop CORR02
            self.belts['CORR02'].running = False
            # Stop elevator
            self.elevator.running = False
            # Reduce gates to minimum
            for gate in self.gates:
                gate.open_pct_sp = min(gate.open_pct_sp, 10.0)
            self._set_alarm('AL_SYSTEM_PARADA_EMERGENCIA_CORR03')

    # ------------------------------------------------------------------------
    # PRIVATE: ELEVATOR
    # ------------------------------------------------------------------------

    def _step_elevator(self, dt_s: float):
        if not self.elevator.running:
            self.elevator.speed_mps = 0.0
            self.elevator.flow_tph = 0.0
            self.elevator.current_A = 0.0
            self.elevator.power_kW = 0.0
            self._cool_down_elevator(dt_s)
            return

        # Input from CORR01
        input_flow = self.belts['CORR01'].flow_tph

        # Capacity (buckets × volume × density × speed)
        # Designed for 1650 t/h (10% margin): 2.5 m/s speed, 4.5 buckets/m, 54L buckets
        buckets_per_s = 2.5 * 4.5  # speed × buckets_per_m
        capacity_tph = buckets_per_s * (54 / 1000) * Config.BULK_DENSITY_T_M3 * 3600

        self.elevator.flow_tph = min(input_flow, capacity_tph)
        self.elevator.speed_mps = 2.5

        # Power
        load_ratio = input_flow / capacity_tph if capacity_tph > 0 else 0
        torque_factor = 1 + 0.5 * load_ratio

        motor_kW = 225
        self.elevator.current_A = (motor_kW * 1000 / (440 * math.sqrt(3) * 0.9)) * torque_factor
        self.elevator.power_kW = motor_kW * torque_factor

        # Thermal
        ambient = 25
        heat_motor = 0.01 * load_ratio * 100
        cool_motor = 0.03 * (self.elevator.temp_motor_C - ambient)

        self.elevator.temp_motor_C += (heat_motor - cool_motor) * dt_s
        self.elevator.temp_gearbox_C += (heat_motor * 0.8 - 0.025 * (self.elevator.temp_gearbox_C - ambient)) * dt_s

        # Slip detection
        self.elevator.slip = load_ratio > 1.05

    def _cool_down_elevator(self, dt_s: float):
        ambient = 25
        rate = 0.05
        self.elevator.temp_motor_C += (ambient - self.elevator.temp_motor_C) * rate * dt_s
        self.elevator.temp_gearbox_C += (ambient - self.elevator.temp_gearbox_C) * rate * dt_s

    # ------------------------------------------------------------------------
    # PRIVATE: BALANCE
    # ------------------------------------------------------------------------

    def _step_balance(self, dt_s: float):
        if not self.balance.running:
            self.balance.cycle_state = CycleState.IDLE
            self.balance.weight_kg = 0.0
            self.balance.avg_flow_tph = 0.0
            return

        input_flow_tph = self.belts['CORR02'].flow_tph
        input_rate_kg_s = (input_flow_tph * 1000) / 3600

        # State machine
        if self.balance.cycle_state == CycleState.IDLE:
            self.balance.cycle_state = CycleState.FILLING
            self.balance.weight_kg = 0.0
            self.balance._cycle_elapsed_s = 0.0

        self.balance._cycle_elapsed_s += dt_s

        if self.balance.cycle_state == CycleState.FILLING:
            self.balance.weight_kg += input_rate_kg_s * dt_s

            if self.balance.weight_kg >= self.balance.target_kg:
                self.balance.cycle_state = CycleState.DISCHARGING
                self.balance.cycle_count += 1
                self.balance.total_mass_t += self.balance.weight_kg / 1000
                self.balance._cycle_elapsed_s = 0.0

        elif self.balance.cycle_state == CycleState.DISCHARGING:
            discharge_rate_kg_s = self.balance.target_kg / self.balance._discharge_time_s
            self.balance.weight_kg = max(0, self.balance.weight_kg - discharge_rate_kg_s * dt_s)

            if self.balance.weight_kg < 1:
                self.balance.cycle_state = CycleState.FILLING
                self.balance.weight_kg = 0.0
                self.balance._cycle_elapsed_s = 0.0

        # Average flow (limited by input - conservation of mass)
        cycle_time_s = self.balance._fill_time_s + self.balance._discharge_time_s
        cycles_per_hour = 3600 / cycle_time_s
        theoretical_capacity_tph = (self.balance.target_kg / 1000) * cycles_per_hour

        # Balance can't output more than what comes in (with 95% efficiency for losses)
        self.balance.avg_flow_tph = min(input_flow_tph * 0.95, theoretical_capacity_tph)

    # ------------------------------------------------------------------------
    # PRIVATE: SHIPLOADER
    # ------------------------------------------------------------------------

    def _step_shiploader(self, dt_s: float):
        if not self.shiploader.running:
            self.shiploader.flow_pv_tph = 0.0
            self.shiploader.power_kW = 0.0
            return

        # Receives from CORR03
        self.shiploader.flow_pv_tph = self.belts['CORR03'].flow_tph

        # Power
        load_ratio = self.shiploader.flow_pv_tph / 1500 if self.shiploader.flow_pv_tph > 0 else 0
        self.shiploader.power_kW = 320 * (0.3 + 0.7 * load_ratio)
        self.shiploader.current_A = (self.shiploader.power_kW * 1000) / (440 * math.sqrt(3) * 0.92)

        # Dust
        self.shiploader.dust_level = load_ratio * 80

    # ------------------------------------------------------------------------
    # PRIVATE: ENERGY
    # ------------------------------------------------------------------------

    def _step_energy(self, dt_s: float):
        total_power_kW = sum(b.power_kW for b in self.belts.values())
        total_power_kW += self.elevator.power_kW
        total_power_kW += self.shiploader.power_kW

        energy_kWh_step = (total_power_kW * dt_s) / 3600
        self.total_kWh += energy_kWh_step

        # Mass
        flow_tph = self.shiploader.flow_pv_tph
        mass_t_step = (flow_tph * dt_s) / 3600
        self.total_mass_t += mass_t_step

        # KPI
        if self.total_mass_t > 0.1:
            self.kWh_per_ton = self.total_kWh / self.total_mass_t

        # Cost
        self.cost_BRL += energy_kWh_step * Config.TARIFF_PEAK_R_KWH

    # ------------------------------------------------------------------------
    # PRIVATE: ALARMS
    # ------------------------------------------------------------------------

    def _step_alarms(self):
        # Temperature alarms
        for belt_id, belt in self.belts.items():
            if belt.temp_bearing_C >= Config.TEMP_BEARING_TRIP:
                self._set_trip(f'TRIP_{belt_id}_BEARING_SOBRETEMP')
            elif belt.temp_bearing_C >= Config.TEMP_BEARING_ALARM:
                self._set_alarm(f'AL_{belt_id}_BEARING_TEMP_ALTA')

        if self.elevator.temp_motor_C >= Config.TEMP_MOTOR_TRIP:
            self._set_trip('TRIP_ELV01_MOTOR_SOBRETEMP')
        elif self.elevator.temp_motor_C >= Config.TEMP_MOTOR_ALARM:
            self._set_alarm('AL_ELV01_MOTOR_TEMP_ALTA')

        # Underspeed
        for belt_id, belt in self.belts.items():
            if belt.underspeed_alarm:
                self._set_alarm(f'AL_{belt_id}_SUBVELOCIDADE')

        # Elevator slip
        if self.elevator.slip:
            self._set_alarm('AL_ELV01_ESCORREGAMENTO')

    def _set_alarm(self, tag: str):
        alarm = next((a for a in self.alarms if a.tag == tag), None)
        if not alarm:
            alarm = AlarmState(tag=tag)
            self.alarms.append(alarm)

        if not alarm.active:
            alarm.active = True
            alarm.latched = True
            alarm.timestamp = self.time_s
            alarm.count += 1

    def _set_trip(self, tag: str):
        trip = next((t for t in self.trips if t.tag == tag), None)
        if not trip:
            trip = AlarmState(tag=tag)
            self.trips.append(trip)

        if not trip.active:
            trip.active = True
            trip.latched = True
            trip.timestamp = self.time_s
            trip.count += 1

    # ------------------------------------------------------------------------
    # PRIVATE: MAINTENANCE
    # ------------------------------------------------------------------------

    def _step_maintenance(self, dt_s: float):
        k_uso = Config.K_WEAR

        # Degrade health
        for belt_id, belt in self.belts.items():
            load_rel = belt.load_pct / 100
            self.health[belt_id] -= k_uso * load_rel * dt_s
            self.health[belt_id] = max(0, self.health[belt_id])

    # ------------------------------------------------------------------------
    # PRIVATE: WAREHOUSE
    # ------------------------------------------------------------------------

    def _step_warehouse(self, dt_s: float):
        total_gate_flow_tph = sum(g.flow_tph for g in self.gates)
        mass_out_t = (total_gate_flow_tph * dt_s) / 3600

        self.warehouse_inventory_t -= mass_out_t
        self.warehouse_inventory_t = max(0, self.warehouse_inventory_t)

        self.warehouse_level_pct = self._calc_warehouse_level()

    def _calc_warehouse_level(self) -> float:
        max_inventory_t = Config.WAREHOUSE_VOLUME_M3 * Config.BULK_DENSITY_T_M3
        return (self.warehouse_inventory_t / max_inventory_t) * 100

    # ------------------------------------------------------------------------
    # PRIVATE: DYNAMICS
    # ------------------------------------------------------------------------

    def _step_dynamics(self, dt_s: float):
        # Update positions even when stopped
        for gate in self.gates:
            delta = gate.open_pct_sp - gate.open_pct
            rate = Config.PI_RAMP_PCT_PER_S
            max_d = rate * dt_s
            gate.open_pct += max(-max_d, min(max_d, delta))
            gate.position_fb = gate.open_pct

        # Cool down
        for belt in self.belts.values():
            self._cool_down_belt(belt, dt_s)
        self._cool_down_elevator(dt_s)

    # ------------------------------------------------------------------------
    # STATE EXPORT
    # ------------------------------------------------------------------------

    def get_state_dict(self) -> dict:
        """Export complete state as dictionary for JSON/WebSocket"""
        return {
            'time_s': self.time_s,
            'running': self.running,
            'warehouse_inventory_t': self.warehouse_inventory_t,
            'warehouse_level_pct': self.warehouse_level_pct,
            'gates': [
                {
                    'id': g.id,
                    'open_pct': g.open_pct,
                    'open_pct_sp': g.open_pct_sp,
                    'flow_tph': g.flow_tph
                }
                for g in self.gates
            ],
            'belts': {
                bid: {
                    'running': b.running,
                    'rpm': b.rpm,
                    'flow_tph': b.flow_tph,
                    'load_pct': b.load_pct,
                    'current_A': b.current_A,
                    'power_kW': b.power_kW,
                    'temp_bearing_C': b.temp_bearing_C
                }
                for bid, b in self.belts.items()
            },
            'elevator': {
                'running': self.elevator.running,
                'flow_tph': self.elevator.flow_tph,
                'temp_motor_C': self.elevator.temp_motor_C,
                'slip': self.elevator.slip
            },
            'balance': {
                'cycle_state': self.balance.cycle_state.value,
                'weight_kg': self.balance.weight_kg,
                'cycle_count': self.balance.cycle_count,
                'total_mass_t': self.balance.total_mass_t
            },
            'shiploader': {
                'running': self.shiploader.running,
                'flow_sp_tph': self.shiploader.flow_sp_tph,
                'flow_pv_tph': self.shiploader.flow_pv_tph,
                'power_kW': self.shiploader.power_kW
            },
            'energy': {
                'total_kWh': self.total_kWh,
                'total_mass_t': self.total_mass_t,
                'kWh_per_ton': self.kWh_per_ton,
                'cost_BRL': self.cost_BRL
            },
            'alarms': [{'tag': a.tag, 'active': a.active, 'count': a.count} for a in self.alarms if a.active],
            'trips': [{'tag': t.tag, 'active': t.active, 'count': t.count} for t in self.trips if t.active]
        }
