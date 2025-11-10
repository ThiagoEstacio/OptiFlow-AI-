"""
Grain Terminal Process Simulator - Python Backend
Real physics-based simulation of 1500 t/h export line

This is the Python port of the TypeScript simulator for backend OPC-UA server
Extended with InterlockManager, AlarmManager, MaintenanceManager, EnergyManager
Integrated with InfluxDB for real-time data persistence
"""

import math
import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

# Import new managers
from app.services.interlock_manager import InterlockManager
from app.services.alarm_manager import AlarmManager
from app.services.maintenance_energy import MaintenanceManager, EnergyManager

# Import DEM Physics Engine
from app.services.dem_physics import DEMEngine

# Import Operational Events Manager
from app.services.operational_events import OperationalEventsManager

# Import Failure System
try:
    from app.services.failures import (
        FailureGenerator,
        BeltFailureModel,
        BearingFailureModel,
        MotorFailureModel,
        SensorFailureModel,
        EnvironmentalFactors
    )
    from app.services.failures.failure_models import (
        BeltFailureState,
        BearingFailureState,
        MotorFailureState,
        SensorFailureState,
        BeltFailureType,
        BearingFailureType,
        MotorFailureType,
        SensorFailureType
    )
    from app.services.failures.environmental_factors import EnvironmentalConditions, WeatherCondition
    FAILURES_AVAILABLE = True
except Exception as e:
    FAILURES_AVAILABLE = False

# Import InfluxDB service
try:
    from app.services.influxdb import influxdb_service
    INFLUXDB_AVAILABLE = True
except Exception as e:
    influxdb_service = None
    INFLUXDB_AVAILABLE = False

# Import Kafka Producer service
try:
    from app.services.kafka_producer import get_kafka_producer
    KAFKA_AVAILABLE = True
except Exception as e:
    get_kafka_producer = None
    KAFKA_AVAILABLE = False

logger = logging.getLogger(__name__)

# Log availability after logger is initialized
if FAILURES_AVAILABLE:
    logger.info("✅ Failure system imported successfully")
else:
    logger.warning("⚠️  Failure system not available - will run without failures")

# Log InfluxDB availability after logger is initialized
if not INFLUXDB_AVAILABLE:
    logger.warning("InfluxDB service not available - data will not be persisted")

# Log Kafka availability after logger is initialized
if KAFKA_AVAILABLE:
    logger.info("✅ Kafka producer imported successfully - real-time streaming enabled")
else:
    logger.warning("⚠️ Kafka producer not available - streaming disabled")


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

        # Energy (legacy - mantido para compatibilidade)
        self.total_kWh = 0.0
        self.total_mass_t = 0.0
        self.kWh_per_ton = 0.0
        self.cost_BRL = 0.0

        # Alarms (legacy - mantido para compatibilidade)
        self.alarms: List[AlarmState] = []
        self.trips: List[AlarmState] = []

        # Health (legacy - mantido para compatibilidade)
        self.health: Dict[str, float] = {}
        for gate in self.gates:
            self.health[f'GATE{gate.id:02d}'] = 100.0
        for belt_id in self.belts.keys():
            self.health[belt_id] = 100.0
        self.health['ELV01'] = 100.0
        self.health['BAL01'] = 100.0
        self.health['SLD01'] = 100.0
        
        # ========================================================================
        # NEW: Advanced Systems
        # ========================================================================
        
        # Interlock Manager
        self.interlock_manager = InterlockManager()
        logger.info("✅ InterlockManager initialized")
        
        # Alarm Manager
        self.alarm_manager = AlarmManager()
        logger.info("✅ AlarmManager initialized")
        
        # Maintenance Manager
        self.maintenance_manager = MaintenanceManager()
        for belt_id in self.belts.keys():
            self.maintenance_manager.register_equipment(belt_id)
        self.maintenance_manager.register_equipment('ELV01')
        self.maintenance_manager.register_equipment('BAL01')
        self.maintenance_manager.register_equipment('SLD01')
        logger.info("✅ MaintenanceManager initialized")
        
        # Energy Manager
        self.energy_manager = EnergyManager()
        for belt_id, belt in self.belts.items():
            self.energy_manager.register_equipment(belt_id, belt.motor_kW)
        self.energy_manager.register_equipment('ELV01', 225.0)
        self.energy_manager.register_equipment('BAL01', 50.0)
        self.energy_manager.register_equipment('SLD01', 320.0)
        logger.info("✅ EnergyManager initialized")

        # ========================================================================
        # Failure System - Realistic equipment failures
        # ========================================================================

        if FAILURES_AVAILABLE:
            # Failure Generator
            from app.services.failures.failure_generator import FailureConfig
            failure_config = FailureConfig(
                base_mtbf_hours=10000.0,  # 10,000 hours base MTBF
                min_mtbf_hours=100.0,      # Minimum 100 hours at 0% health
                enabled=True,              # Enable failure generation
                verbose=False              # Set to True for debug logging
            )
            self.failure_generator = FailureGenerator(failure_config)

            # Failure Models
            self.belt_failure_model = BeltFailureModel()
            self.bearing_failure_model = BearingFailureModel()
            self.motor_failure_model = MotorFailureModel()
            self.sensor_failure_model = SensorFailureModel()

            # Environmental Factors
            self.environmental_factors = EnvironmentalFactors()
            self.environmental_conditions = EnvironmentalConditions(
                ambient_temp_C=25.0,
                equipment_temp_C=40.0,
                humidity_pct=60.0,
                weather=WeatherCondition.CLEAR,
                dust_level_ppm=50.0,
                hours_continuous_operation=0.0,
                starts_today=0,
                overload_events_today=0
            )

            # Failure States for Equipment
            self.failure_states = {}

            # Initialize failure states for belts
            for belt_id in self.belts.keys():
                self.failure_states[belt_id] = {
                    'belt': BeltFailureState(),
                    'bearing': BearingFailureState(),
                    'motor': MotorFailureState(),
                    'sensor_temp': SensorFailureState(),
                    'sensor_current': SensorFailureState()
                }

            # Initialize for elevator
            self.failure_states['ELV01'] = {
                'belt': BeltFailureState(),
                'bearing': BearingFailureState(),
                'motor': MotorFailureState(),
                'sensor_temp': SensorFailureState()
            }

            logger.info("✅ Failure System initialized - Realistic failures enabled")
        else:
            self.failure_generator = None
            logger.warning("⚠️  Failure System disabled - module not available")

        # ========================================================================
        # DEM Physics Engine
        # ========================================================================
        
        self.dem_engine = DEMEngine(gravity=9.81)
        self.dem_enabled = True  # Flag para habilitar/desabilitar DEM
        self.dem_particle_scale = 100  # Fator de escala (1 partícula DEM = 100 kg reais) - ALTA RESOLUÇÃO
        
        # Define volumes de contenção DEM (coordenadas em metros)
        # Armazém (50x50x30m - grande silo)
        self.dem_engine.add_box(
            'warehouse',
            min_bounds=[0, 0, 0],
            max_bounds=[50, 50, 30],
            friction=0.5,
            restitution=0.2
        )
        
        # Chutes das comportas (um para cada gate ativa)
        for i in range(Config.PI_INITIAL_GATES):
            self.dem_engine.add_box(
                f'gate_chute_{i+1}',
                min_bounds=[10 + i*2, 20, -2],
                max_bounds=[11 + i*2, 21, 0],
                friction=0.4,
                restitution=0.25
            )
        
        # CORR01 (correia receptora - 30m de comprimento)
        self.dem_engine.add_box(
            'belt_corr01',
            min_bounds=[10, 15, -2.5],
            max_bounds=[40, 16.5, -2],
            friction=0.35,
            restitution=0.3
        )
        
        # CORR02 (correia intermediária - 25m)
        self.dem_engine.add_box(
            'belt_corr02',
            min_bounds=[38, 16, -2.5],
            max_bounds=[38.5, 41, -2],
            friction=0.35,
            restitution=0.3
        )
        
        # ELV01 (elevador - 40m altura)
        self.dem_engine.add_box(
            'elevator',
            min_bounds=[38, 40, -2],
            max_bounds=[40, 42, 38],
            friction=0.3,
            restitution=0.35
        )
        
        # CORR03 (correia de embarque - 50m)
        self.dem_engine.add_box(
            'belt_corr03',
            min_bounds=[40, 40, 36],
            max_bounds=[90, 41.6, 36.5],
            friction=0.35,
            restitution=0.3
        )
        
        # Balança (região de pesagem)
        self.dem_engine.add_box(
            'balance',
            min_bounds=[65, 39, 36],
            max_bounds=[68, 43, 37],
            friction=0.4,
            restitution=0.2
        )
        
        # Shiploader (carregador de navio - grande volume)
        self.dem_engine.add_box(
            'shiploader',
            min_bounds=[88, 38, 35],
            max_bounds=[92, 44, 38],
            friction=0.3,
            restitution=0.25
        )
        
        # Inicializa partículas no armazém (simulando grãos já armazenados)
        if self.dem_enabled and self.warehouse_inventory_t > 0:
            # Calcula número de partículas baseado no inventário (alta resolução para demo)
            particle_count = min(8000, int(self.warehouse_inventory_t / self.dem_particle_scale))
            spawned = self.dem_engine.spawn_particles(
                count=particle_count,
                box_name='warehouse',
                material='soja',
                velocity=[0, 0, 0]
            )
            logger.info(f"✅ DEM Engine initialized with {spawned} particles in warehouse")
        else:
            logger.info("✅ DEM Engine initialized (empty)")
        
        # ========================================================================
        # Operational Events Manager (para demonstração comercial realística)
        # ========================================================================
        
        self.events_manager = OperationalEventsManager()
        logger.info("✅ Operational Events Manager initialized")
        logger.info(f"   - Navios na fila: {len(self.events_manager.ships_queue)}")
        logger.info(f"   - Clima atual: {self.events_manager.current_weather.value}")
        logger.info(f"   - Produto atual: {self.events_manager.current_product.value}")

    # ------------------------------------------------------------------------
    # HELPER METHODS: Realistic Sensor Modeling
    # ------------------------------------------------------------------------
    
    def _add_sensor_noise(self, value: float, sensor_type: str = 'default') -> float:
        """
        Adiciona ruído realístico a leituras de sensores (para demo comercial)
        Simula imperfeições de sensores reais
        """
        return self.events_manager.add_sensor_noise(value, sensor_type)
    
    def _add_sensor_drift(self, value: float, sensor_type: str = 'default') -> float:
        """
        Adiciona drift temporal (descalibração ao longo do tempo)
        """
        return self.events_manager.add_sensor_drift(value, self.time_s, drift_rate=0.00005)

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

    def write_to_influxdb(self, tag_mapping: Dict[str, str]):
        """
        Write current simulator values to InfluxDB
        
        Args:
            tag_mapping: Dict mapping tag names to tag UUIDs
                        e.g., {'CORR01_FLOW_TPH_PV': 'uuid-1234-...'}
        """
        if not INFLUXDB_AVAILABLE or not influxdb_service:
            return
        
        try:
            points = []
            timestamp = datetime.utcnow()
            
            # Collect all current values
            for tag_name, tag_id in tag_mapping.items():
                value = self.get_tag_value(tag_name)
                
                if value is not None:
                    points.append({
                        'tag_id': tag_id,
                        'value': float(value),
                        'timestamp': timestamp,
                        'quality': 'good'
                    })
            
            # Write batch to InfluxDB
            if points:
                success = influxdb_service.write_batch(points)
                if success:
                    logger.debug(f"✅ Wrote {len(points)} points to InfluxDB")
                else:
                    logger.warning(f"⚠️ Failed to write {len(points)} points to InfluxDB")
                    
        except Exception as e:
            logger.error(f"❌ Error writing to InfluxDB: {e}")

    def step(self, dt_s: float = None):
        """Execute one simulation step"""
        if dt_s is None:
            dt_s = Config.DT_S

        if not self.running or self.emergency_stop:
            self._step_dynamics(dt_s)
            return

        self.time_s += dt_s

        # 0. Operational Events (novos eventos operacionais realísticos)
        event_modifiers = self.events_manager.step(dt_s)
        
        # Aplicar modificadores climáticos
        weather_flow_factor = event_modifiers.get('weather_flow_factor', 1.0)
        weather_speed_factor = event_modifiers.get('weather_speed_factor', 1.0)

        # 1. DEM Physics (executa múltiplos sub-steps para estabilidade)
        if self.dem_enabled:
            self._step_dem(dt_s, weather_flow_factor)

        # 2. PI Controller
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

        # 9. Energy (legacy + new system)
        self._step_energy(dt_s)

        # 10. Alarms (old system + new AlarmManager)
        self._step_alarms()
        self._step_alarm_manager(dt_s)

        # 11. Interlocks (NEW)
        self._step_interlocks()

        # 12. Maintenance (old system + new MaintenanceManager)
        self._step_maintenance(dt_s)
        self._step_maintenance_manager(dt_s)

        # 13. Warehouse
        self._step_warehouse(dt_s)
        
        # 14. Ship Loading Management (NEW - gerencia carregamento de navios)
        self._step_ship_loading(dt_s)

        # 15. Update legacy values from new managers
        self._sync_legacy_values()

        # 16. Publish to Kafka for real-time streaming (NEW)
        # DISABLED_FOR_TESTING:         logger.info(f"🚀 About to call _publish_to_kafka() - time: {self.time_s}s")
        # DISABLED_FOR_TESTING:         try:
        # DISABLED_FOR_TESTING:             with open('/tmp/kafka_debug.txt', 'a') as f:
        # DISABLED_FOR_TESTING:                 f.write(f"Step called at time: {self.time_s}s\n")
        # DISABLED_FOR_TESTING:         except:
        # DISABLED_FOR_TESTING:             pass
        # DISABLED_FOR_TESTING:         # DISABLED_FOR_TESTING:         self._publish_to_kafka()

    # ------------------------------------------------------------------------
    # PRIVATE: SHIP LOADING MANAGEMENT
    # ------------------------------------------------------------------------
    
    def _step_ship_loading(self, dt_s: float):
        """
        Gerencia carregamento automático de navios
        """
        # Se há um navio carregando, atualiza quantidade
        current_ship = self.events_manager.get_loading_ship()
        
        if current_ship:
            # Quantidade carregada é baseada no throughput real do shiploader
            loaded_this_step_kg = self.shiploader.flow_pv_tph * 1000 * (dt_s / 3600)
            self.events_manager.update_ship_loading(loaded_this_step_kg / 1000)  # converter para toneladas
        else:
            # Se não há navio carregando, tenta iniciar próximo da fila
            waiting_ships = [s for s in self.events_manager.ships_queue if s.status == "waiting"]
            if waiting_ships:
                # Pega navio com maior prioridade
                next_ship = sorted(waiting_ships, key=lambda s: s.priority, reverse=True)[0]
                self.events_manager.start_loading_ship(next_ship)
                logger.info(f"🚢 Iniciando carregamento do navio {next_ship.name}")

    # ------------------------------------------------------------------------
    # PRIVATE: DEM PHYSICS (NEW)
    # ------------------------------------------------------------------------

    def _step_dem(self, dt_s: float, weather_flow_factor: float = 1.0):
        """
        Executa simulação DEM (Discrete Element Method) para modelagem granular realista
        
        Args:
            dt_s: Tempo de simulação (segundos)
            weather_flow_factor: Fator de redução de fluxo por clima (0.7-1.0)
        """
        # Número de sub-steps para estabilidade (DEM requer passos menores)
        sub_steps = max(1, int(dt_s / self.dem_engine.time_step))
        
        for _ in range(sub_steps):
            # 1. Spawn novas partículas nas comportas abertas (afetado por clima)
            self._dem_spawn_from_gates(weather_flow_factor)
            
            # 2. Aplica velocidade das correias às partículas
            self._dem_apply_belt_motion()
            
            # 3. Step do motor de física
            dem_stats = self.dem_engine.step()
            
            # 4. Atualiza taxas de fluxo baseadas no DEM
            self._dem_update_flow_rates()
            
            # 5. Coleta partículas que chegaram ao destino
            self._dem_collect_particles()
        
        # Log stats periodicamente
        if int(self.time_s * 10) % 100 == 0:  # a cada 10s
            logger.debug(f"DEM: {dem_stats['particle_count']} particles, "
                        f"{dem_stats['collision_count']} collisions, "
                        f"KE={dem_stats['total_kinetic_energy']:.1f}J")
    
    def _dem_spawn_from_gates(self, weather_flow_factor: float = 1.0):
        """
        Spawna partículas nas comportas abertas baseado no fluxo
        
        Args:
            weather_flow_factor: Fator de redução por clima (0.7-1.0)
        """
        for gate in self.gates:
            if gate.open_pct > 5 and gate.flow_tph > 1:
                # Calcula quantas partículas spawnar baseado no fluxo (afetado por clima)
                # flow_tph é toneladas por hora, queremos kg por segundo
                kg_per_second = (gate.flow_tph * 1000) / 3600
                kg_per_second *= weather_flow_factor  # Reduz em chuva/vento
                
                # Cada partícula DEM representa N kg de material real
                particles_per_second = kg_per_second / self.dem_particle_scale
                
                # Probabilidade de spawn neste sub-step
                spawn_probability = particles_per_second * self.dem_engine.time_step
                
                if np.random.random() < spawn_probability:
                    # Spawn 1-3 partículas
                    count = np.random.randint(1, 4)
                    
                    # Velocidade inicial baseada na abertura da comporta
                    # Maior abertura = maior velocidade de saída
                    exit_velocity_z = -1.0 * (gate.open_pct / 100.0) * 2.0  # até -2 m/s
                    exit_velocity_z *= weather_flow_factor  # Reduz velocidade em chuva
                    
                    # Material baseado no produto atual do events_manager
                    material = self.events_manager.current_product.value
                    
                    self.dem_engine.spawn_particles(
                        count=count,
                        box_name=f'gate_chute_{gate.id}',
                        material=material,
                        velocity=[0.0, 0.0, exit_velocity_z]
                    )
    
    def _dem_apply_belt_motion(self):
        """Aplica movimento das correias às partículas em contato"""
        belts_boxes = {
            'CORR01': 'belt_corr01',
            'CORR02': 'belt_corr02',
            'CORR03': 'belt_corr03'
        }
        
        for belt_id, box_name in belts_boxes.items():
            belt = self.belts[belt_id]
            if not belt.running:
                continue
            
            box = self.dem_engine.boxes.get(box_name)
            if not box:
                continue
            
            # Direção do movimento da correia
            if belt_id == 'CORR01':
                direction = np.array([1, 0, 0])  # movimento em +X
            elif belt_id == 'CORR02':
                direction = np.array([0, 1, 0])  # movimento em +Y
            else:  # CORR03
                direction = np.array([1, 0, 0])  # movimento em +X
            
            # Aplica velocidade às partículas próximas da superfície da correia
            for particle in self.dem_engine.particles:
                if box.contains(particle.position):
                    # Distância do fundo da correia
                    dist_from_bottom = particle.position[2] - box.min_bounds[2]
                    
                    # Partículas próximas do fundo (< 5cm) são arrastadas
                    if dist_from_bottom < 0.05 + particle.radius:
                        # Aplica velocidade da correia com atrito
                        target_velocity = direction * belt.speed_mps
                        
                        # Interpolação suave (fator de acoplamento)
                        coupling = 0.3  # 30% de acoplamento por step
                        particle.velocity += (target_velocity - particle.velocity) * coupling
    
    def _dem_update_flow_rates(self):
        """Atualiza taxas de fluxo dos equipamentos baseado no DEM"""
        # CORR01 - taxa de fluxo baseada em partículas na correia
        corr01_flow_kg_s = self.dem_engine.get_flow_rate('belt_corr01', 'x')
        self.belts['CORR01'].flow_tph = (corr01_flow_kg_s * 3.6 * self.dem_particle_scale)
        
        # CORR02
        corr02_flow_kg_s = self.dem_engine.get_flow_rate('belt_corr02', 'y')
        self.belts['CORR02'].flow_tph = (corr02_flow_kg_s * 3.6 * self.dem_particle_scale)
        
        # Elevador
        elv_flow_kg_s = self.dem_engine.get_flow_rate('elevator', 'z')
        self.elevator.flow_tph = (elv_flow_kg_s * 3.6 * self.dem_particle_scale)
        
        # CORR03
        corr03_flow_kg_s = self.dem_engine.get_flow_rate('belt_corr03', 'x')
        self.belts['CORR03'].flow_tph = (corr03_flow_kg_s * 3.6 * self.dem_particle_scale)
        
        # Balança - massa instantânea
        balance_mass_kg = self.dem_engine.get_mass_in_box('balance') * self.dem_particle_scale
        self.balance.weight_kg = balance_mass_kg
        
        # Shiploader
        shiploader_flow_kg_s = self.dem_engine.get_flow_rate('shiploader', 'z')
        self.shiploader.flow_pv_tph = (shiploader_flow_kg_s * 3.6 * self.dem_particle_scale)
    
    def _dem_collect_particles(self):
        """Remove partículas que chegaram ao destino final"""
        # Partículas que saíram do shiploader vão para o navio
        shiploader_box = self.dem_engine.boxes['shiploader']
        particles_to_remove = []
        
        for i, particle in enumerate(self.dem_engine.particles):
            # Se partícula está no shiploader e caindo (velocidade -Z)
            if shiploader_box.contains(particle.position):
                if particle.velocity[2] < -0.5:  # caindo rápido
                    # Atingiu o fundo do shiploader
                    if particle.position[2] <= shiploader_box.min_bounds[2] + particle.radius:
                        particles_to_remove.append(i)
        
        # Remove partículas (reverso para não afetar índices)
        for i in reversed(particles_to_remove):
            mass_kg = self.dem_engine.particles[i].mass * self.dem_particle_scale
            self.total_mass_t += mass_kg / 1000
            del self.dem_engine.particles[i]

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
# DISABLED_KAFKA:             self._set_trip('TRIP_ELV01_MOTOR_SOBRETEMP')
# DISABLED_KAFKA:         elif self.elevator.temp_motor_C >= Config.TEMP_MOTOR_ALARM:
# DISABLED_KAFKA:             self._set_alarm('AL_ELV01_MOTOR_TEMP_ALTA')
# DISABLED_KAFKA: 
# DISABLED_KAFKA:         # Underspeed
# DISABLED_KAFKA:         for belt_id, belt in self.belts.items():
# DISABLED_KAFKA:             if belt.underspeed_alarm:
# DISABLED_KAFKA:                 self._set_alarm(f'AL_{belt_id}_SUBVELOCIDADE')
# DISABLED_KAFKA: 
# DISABLED_KAFKA:         # Elevator slip
# DISABLED_KAFKA:         if self.elevator.slip:
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
    # NEW SYSTEMS INTEGRATION
    # ------------------------------------------------------------------------
    
    def _step_alarm_manager(self, dt_s: float):
        """Avalia todos os alarmes via AlarmManager"""
        
        # Alarmes térmicos
        for belt_id, belt in self.belts.items():
            self.alarm_manager.evaluate(
                f'AL_{belt_id}_BEARING_TEMP_ALTA',
                belt.temp_bearing_C >= Config.TEMP_BEARING_ALARM,
                self.time_s, dt_s
            )
            self.alarm_manager.evaluate(
                f'TRIP_{belt_id}_BEARING_SOBRETEMP',
                belt.temp_bearing_C >= Config.TEMP_BEARING_TRIP,
                self.time_s, dt_s
            )
            
            # Alarmes mecânicos
            self.alarm_manager.evaluate(
                f'AL_{belt_id}_DESALINHAMENTO',
                belt.misaligned,
                self.time_s, dt_s
            )
            self.alarm_manager.evaluate(
                f'AL_{belt_id}_SUBVELOCIDADE',
                belt.underspeed_alarm,
                self.time_s, dt_s
            )
            self.alarm_manager.evaluate(
                f'TRIP_{belt_id}_RASGO',
                belt.torn,
                self.time_s, dt_s
            )
            
            # Alarmes de chute
            self.alarm_manager.evaluate(
                f'AL_CHT{["01","02","03"][list(self.belts.keys()).index(belt_id)]}_ACUMULO',
                belt.chute_level_pct >= 80,
                self.time_s, dt_s
            )
            self.alarm_manager.evaluate(
                f'TRIP_CHT{["01","02","03"][list(self.belts.keys()).index(belt_id)]}_ENTALO',
                belt.chute_plugged,
                self.time_s, dt_s
            )
        
        # Alarmes do elevador
        self.alarm_manager.evaluate(
            'AL_ELV01_MOTOR_TEMP_ALTA',
            self.elevator.temp_motor_C >= Config.TEMP_MOTOR_ALARM,
            self.time_s, dt_s
        )
        self.alarm_manager.evaluate(
            'TRIP_ELV01_MOTOR_SOBRETEMP',
            self.elevator.temp_motor_C >= Config.TEMP_MOTOR_TRIP,
            self.time_s, dt_s
        )
        self.alarm_manager.evaluate(
            'AL_ELV01_ESCORREGAMENTO',
            self.elevator.slip,
            self.time_s, dt_s
        )
        
        # Alarmes elétricos
        for belt_id in self.belts.keys():
            if belt_id in self.energy_manager.electrical_states:
                elec = self.energy_manager.electrical_states[belt_id]
                self.alarm_manager.evaluate(
                    'AL_FP_BAIXO',
                    elec.power_kW > 0.1 * elec.motor_kW and elec.power_factor < 0.85,
                    self.time_s, dt_s
                )
        
        # Alarmes de manutenção
        for eq_id in self.maintenance_manager.maintenance_states.keys():
            maint = self.maintenance_manager.maintenance_states[eq_id]
            alarm_tag = maint.get_alarm_tag()
            if alarm_tag:
                self.alarm_manager.evaluate(
                    alarm_tag,
                    True,
                    self.time_s, dt_s
                )
    
    def _step_interlocks(self):
        """Avalia matriz de intertravamentos"""
        executed = self.interlock_manager.evaluate(self, self.time_s)
        
        if executed:
            logger.warning(f"⚠️  Interlocks executed: {len(executed)} actions")
    
    def _step_maintenance_manager(self, dt_s: float):
        """Atualiza MaintenanceManager para todos equipamentos"""
        
        # Belts
        for belt_id, belt in self.belts.items():
            # Conta eventos (alarmes ativos)
            events = len([a for a in self.alarm_manager.get_active_alarms() 
                         if belt_id in a['tag']])
            
            self.maintenance_manager.update_equipment(
                belt_id, dt_s, belt.load_pct, events, belt.running
            )
            
            # Atualiza energia também
            if belt_id in self.energy_manager.electrical_states:
                self.energy_manager.electrical_states[belt_id].update(
                    dt_s, belt.load_pct, belt.running
                )
        
        # Elevator
        events_elv = len([a for a in self.alarm_manager.get_active_alarms() 
                         if 'ELV' in a['tag']])
        load_elv = (self.elevator.flow_tph / 1650) * 100 if self.elevator.running else 0
        self.maintenance_manager.update_equipment(
            'ELV01', dt_s, load_elv, events_elv, self.elevator.running
        )
        
        if 'ELV01' in self.energy_manager.electrical_states:
            self.energy_manager.electrical_states['ELV01'].update(
                dt_s, load_elv, self.elevator.running
            )
        
        # Balance
        load_bal = 50 if self.balance.running else 0
        self.maintenance_manager.update_equipment(
            'BAL01', dt_s, load_bal, 0, self.balance.running
        )
        
        # Shiploader
        load_sld = (self.shiploader.flow_pv_tph / 1500) * 100 if self.shiploader.running else 0
        self.maintenance_manager.update_equipment(
            'SLD01', dt_s, load_sld, 0, self.shiploader.running
        )
        
        if 'SLD01' in self.energy_manager.electrical_states:
            self.energy_manager.electrical_states['SLD01'].update(
                dt_s, load_sld, self.shiploader.running
            )
        
        # Atualiza Energy Manager global
        import datetime
        hour_of_day = datetime.datetime.now().hour
        self.energy_manager.update(dt_s, hour_of_day)
        
        # Atualiza produção
        flow_tph = self.shiploader.flow_pv_tph
        mass_t_step = (flow_tph * dt_s) / 3600
        self.energy_manager.update_production(mass_t_step)
    
    def _sync_legacy_values(self):
        """Sincroniza valores legacy com novos sistemas"""
        
        # Energia
        energy_summary = self.energy_manager.get_electrical_summary()
        self.total_kWh = energy_summary['total_kWh']
        self.kWh_per_ton = energy_summary['kWh_per_ton']
        self.total_mass_t = self.energy_manager.total_mass_t
        self.cost_BRL = energy_summary['cost_total_BRL']
        
        # Health (média dos novos estados de manutenção)
        for eq_id in self.maintenance_manager.maintenance_states.keys():
            if eq_id in self.health:
                self.health[eq_id] = self.maintenance_manager.maintenance_states[eq_id].health_pct

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

    # ------------------------------------------------------------------------
    # PRIVATE: KAFKA STREAMING (NEW)
    # ------------------------------------------------------------------------

    def _publish_to_kafka(self):
        """
        Publish key simulator tags to Kafka for real-time streaming

        This method is called at the end of each simulation step to push
        real-time data to frontend via WebSocket.
        """
        logger.info(f"🔍 _publish_to_kafka() called - time: {self.time_s}s")

        # Dynamic check for Kafka availability
        try:
            from app.services.kafka_producer import get_kafka_producer
        except ImportError:
            logger.warning("Import Error - Kafka producer not available")
            return  # Kafka not available

        try:
            import asyncio
            kafka_producer = get_kafka_producer()

            # Check if producer is actually enabled
            if not kafka_producer.enabled:
                logger.warning(f"⚠️  Kafka producer not enabled - skipping publish (time: {self.time_s}s)")
                return

            # Check if producer is initialized (lazy initialization)
            if kafka_producer.producer is None:
                logger.info(f"⚙️  Kafka producer not started yet - initializing now...")
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If event loop is running, schedule as task
                    asyncio.ensure_future(kafka_producer.start())
                    # Wait briefly for initialization
                    import time
                    time.sleep(0.1)
                else:
                    # If no event loop, run in new loop
                    asyncio.run(kafka_producer.start())

                # Check again after initialization attempt
                if kafka_producer.producer is None:
                    logger.warning(f"⚠️  Failed to initialize Kafka producer")
                    return

            logger.info(f"📤 Publishing tags to Kafka - Time: {self.time_s}s")

            # Build tag updates for critical process variables
            tags = []

            # Gate flow tags
            for i, gate in enumerate(self.gates):
                tags.append({
                    'tag_id': f'GATE_{i+1:02d}_FLOW',
                    'name': f'Gate {i+1} Flow',
                    'value': round(gate.flow_tph, 2),
                    'quality': 'good' if not gate.failure else 'bad',
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'simulator'
                })
                tags.append({
                    'tag_id': f'GATE_{i+1:02d}_OPEN_PCT',
                    'name': f'Gate {i+1} Opening',
                    'value': round(gate.open_pct, 1),
                    'quality': 'good' if not gate.failure else 'bad',
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'simulator'
                })

            # Belt tags
            for belt_name in ['CORR01', 'CORR02', 'CORR03']:
                belt = self.belts[belt_name]
                tags.extend([
                    {
                        'tag_id': f'{belt_name}_FLOW',
                        'name': f'Belt {belt_name} Flow',
                        'value': round(belt.flow_tph, 2),
                        'quality': 'good',
                        'timestamp': datetime.utcnow().isoformat(),
                        'source': 'simulator'
                    },
                    {
                        'tag_id': f'{belt_name}_SPEED',
                        'name': f'Belt {belt_name} Speed',
                        'value': round(belt.speed_mps, 2),
                        'quality': 'good',
                        'timestamp': datetime.utcnow().isoformat(),
                        'source': 'simulator'
                    },
                    {
                        'tag_id': f'{belt_name}_LOAD_PCT',
                        'name': f'Belt {belt_name} Load',
                        'value': round(belt.load_pct, 1),
                        'quality': 'good',
                        'timestamp': datetime.utcnow().isoformat(),
                        'source': 'simulator'
                    },
                    {
                        'tag_id': f'{belt_name}_POWER_KW',
                        'name': f'Belt {belt_name} Power',
                        'value': round(belt.power_kW, 2),
                        'quality': 'good',
                        'timestamp': datetime.utcnow().isoformat(),
                        'source': 'simulator'
                    }
                ])

            # Elevator tags
            tags.extend([
                {
                    'tag_id': 'ELEV_01_FLOW',
                    'name': 'Elevator Flow',
                    'value': round(self.elevator.flow_tph, 2),
                    'quality': 'good',
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'simulator'
                },
                {
                    'tag_id': 'ELEV_01_SPEED',
                    'name': 'Elevator Speed',
                    'value': round(self.elevator.speed_mps, 2),
                    'quality': 'good',
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'simulator'
                },
                {
                    'tag_id': 'ELEV_01_POWER_KW',
                    'name': 'Elevator Power',
                    'value': round(self.elevator.power_kW, 2),
                    'quality': 'good',
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'simulator'
                }
            ])

            # Balance tags
            tags.extend([
                {
                    'tag_id': 'BALANCE_01_WEIGHT',
                    'name': 'Balance Weight',
                    'value': round(self.balance.weight_kg, 1),
                    'quality': 'good',
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'simulator'
                },
                {
                    'tag_id': 'BALANCE_01_STATE',
                    'name': 'Balance State',
                    'value': self.balance.cycle_state.value,
                    'quality': 'good',
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'simulator'
                }
            ])

            # Shiploader tags
            tags.extend([
                {
                    'tag_id': 'SHIPLOADER_01_FLOW_SP',
                    'name': 'Shiploader Setpoint',
                    'value': round(self.shiploader.flow_sp_tph, 2),
                    'quality': 'good',
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'simulator'
                },
                {
                    'tag_id': 'SHIPLOADER_01_FLOW_PV',
                    'name': 'Shiploader Flow',
                    'value': round(self.shiploader.flow_pv_tph, 2),
                    'quality': 'good',
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'simulator'
                },
                {
                    'tag_id': 'SHIPLOADER_01_POWER_KW',
                    'name': 'Shiploader Power',
                    'value': round(self.shiploader.power_kW, 2),
                    'quality': 'good',
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'simulator'
                }
            ])

            # System tags
            tags.extend([
                {
                    'tag_id': 'SYSTEM_RUNNING',
                    'name': 'System Running',
                    'value': 1.0 if self.running else 0.0,
                    'quality': 'good',
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'simulator'
                },
                {
                    'tag_id': 'WAREHOUSE_LEVEL_PCT',
                    'name': 'Warehouse Level',
                    'value': round(self.warehouse_level_pct, 1),
                    'quality': 'good',
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'simulator'
                },
                {
                    'tag_id': 'SYSTEM_TOTAL_POWER_KW',
                    'name': 'Total Power',
                    'value': round(
                        sum(b.power_kW for b in self.belts.values()) +
                        self.elevator.power_kW +
                        self.shiploader.power_kW,
                        2
                    ),
                    'quality': 'good',
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'simulator'
                }
            ])

            # Publish tags asynchronously (non-blocking)
            # Create task to avoid blocking simulation
            try:
                loop = asyncio.get_running_loop()
                # Schedule the publish task without awaiting
                logger.info(f"🔄 Scheduling publish task in event loop (tags: {len(tags)})")
                asyncio.ensure_future(kafka_producer.publish_bulk(tags), loop=loop)
            except RuntimeError as re:
                # No event loop in current thread, try creating new task in thread pool
                logger.info(f"⚠️  No event loop in current thread - using threading fallback")
                try:
                    import threading
                    def publish_in_thread():
                        try:
                            import asyncio
                            logger.info(f"🧵 Publishing in separate thread (tags: {len(tags)})")
                            asyncio.run(kafka_producer.publish_bulk(tags))
                        except Exception as e:
                            logger.error(f"❌ Thread publish error: {e}", exc_info=True)

                    thread = threading.Thread(target=publish_in_thread, daemon=True)
                    thread.start()
                except Exception as e:
                    logger.debug(f"Failed to publish in thread: {e}")

        except Exception as e:
            # Don't crash simulator if Kafka fails - graceful degradation
            logger.error(f"❌ Kafka publish error (non-critical): {e}", exc_info=True)
