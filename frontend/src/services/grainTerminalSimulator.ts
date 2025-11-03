/**
 * Grain Terminal Process Simulator
 * Real physics-based simulation of 1500 t/h export line
 *
 * Features:
 * - 10 gates with flow curves and saturation
 * - PI controller with anti-windup
 * - Belt mechanics (load, friction, underspeed)
 * - Elevator slip and jamming
 * - Batch scale cycles
 * - Thermal model (bearings, motors, belts)
 * - Electrical model (current, power, PF, kWh)
 * - Alarms and interlocks matrix
 * - Health/maintenance model
 */

import { GRAIN_TERMINAL_CONFIG } from './grainTerminalConfig';

const CONFIG = GRAIN_TERMINAL_CONFIG;

// ============================================================================
// TYPES
// ============================================================================

export interface GateState {
  id: number;
  open_pct: number;        // 0-100
  open_pct_sp: number;     // Setpoint
  position_fb: number;     // Feedback with dynamics
  flow_tph: number;        // Actual flow from this gate
  plugged: boolean;
  failure: boolean;
}

export interface BeltState {
  id: string;
  running: boolean;
  speed_mps: number;
  speed_sp_mps: number;
  rpm: number;
  rpm_nom: number;
  flow_tph: number;
  load_pct: number;
  current_A: number;
  current_nom_A: number;
  power_kW: number;
  temp_bearing_C: number;
  temp_belt_C: number;
  temp_drum_C: number;
  misaligned: boolean;
  torn: boolean;
  underspeed_warn: boolean;
  underspeed_alarm: boolean;
  chute_level_pct: number;
  chute_plugged: boolean;
}

export interface ElevatorState {
  id: string;
  running: boolean;
  speed_mps: number;
  flow_tph: number;
  current_A: number;
  power_kW: number;
  temp_motor_C: number;
  temp_gearbox_C: number;
  temp_bearing_sup_C: number;
  temp_bearing_inf_C: number;
  belt_loose: boolean;
  slip: boolean;
  jammed: boolean;
  spark_detected: boolean;
}

export interface BalanceState {
  id: string;
  running: boolean;
  cycle_state: 'idle' | 'filling' | 'stabilizing' | 'discharging';
  weight_kg: number;
  target_kg: number;
  cycle_count: number;
  total_mass_t: number;
  avg_flow_tph: number;
  failure: boolean;
}

export interface ShipLoaderState {
  id: string;
  running: boolean;
  flow_sp_tph: number;
  flow_pv_tph: number;
  position_deg: number;
  dust_level: number;
  current_A: number;
  power_kW: number;
}

export interface PIControllerState {
  error: number;
  integral: number;
  output: number;
  A_tot: number;           // Total equivalent gate opening area
  active_gates: number[];  // List of gate IDs currently open
}

export interface AlarmState {
  tag: string;
  active: boolean;
  latched: boolean;
  timestamp: number;
  count: number;
}

export interface SimulatorState {
  time_s: number;
  running: boolean;

  // Plant states
  warehouse_inventory_t: number;
  warehouse_level_pct: number;
  gates: GateState[];
  belts: { [id: string]: BeltState };
  elevator: ElevatorState;
  balance: BalanceState;
  shiploader: ShipLoaderState;

  // Control
  pi_controller: PIControllerState;

  // Energy
  total_kWh: number;
  total_mass_t: number;
  kWh_per_ton: number;
  cost_R$: number;

  // Alarms & Trips
  alarms: AlarmState[];
  trips: AlarmState[];

  // Maintenance
  health: { [equipId: string]: number }; // 0-100%

  // Emergency
  emergency_stop: boolean;
}

// ============================================================================
// SIMULATOR CLASS
// ============================================================================

export class GrainTerminalSimulator {
  private state: SimulatorState;
  private dt_s: number;
  private time_s: number = 0;

  constructor() {
    this.dt_s = CONFIG.simulation.dt_s;
    this.state = this.createInitialState();
  }

  // --------------------------------------------------------------------------
  // INITIALIZATION
  // --------------------------------------------------------------------------

  private createInitialState(): SimulatorState {
    const gates: GateState[] = [];
    for (let i = 0; i < CONFIG.plant.warehouse.gates.count; i++) {
      gates.push({
        id: i + 1,
        open_pct: 0,
        open_pct_sp: 0,
        position_fb: 0,
        flow_tph: 0,
        plugged: false,
        failure: false
      });
    }

    // Initialize first 4 gates as per start strategy
    const startGates = CONFIG.control.gates_pi.start_strategy.initial_gates;
    const startOpen = CONFIG.control.gates_pi.start_strategy.initial_open_pct;
    for (let i = 0; i < startGates; i++) {
      gates[i].open_pct_sp = startOpen;
      gates[i].open_pct = startOpen;
      gates[i].position_fb = startOpen;
    }

    const belts: { [id: string]: BeltState } = {};

    // Create belt states from config
    const beltSegments = CONFIG.plant.route.segments.filter(s => s.id.startsWith('CORR'));
    beltSegments.forEach(seg => {
      const nominalRPM = (seg.speed_mps! * 60) / (Math.PI * CONFIG.mechanics.belts.drive_pulley_diameter_mm / 1000);
      const nominalCurrent = (seg.motor_kW * 1000) / (440 * Math.sqrt(3) * 0.92); // V=440, PF=0.92

      belts[seg.id] = {
        id: seg.id,
        running: false,
        speed_mps: 0,
        speed_sp_mps: seg.speed_mps!,
        rpm: 0,
        rpm_nom: nominalRPM,
        flow_tph: 0,
        load_pct: 0,
        current_A: 0,
        current_nom_A: nominalCurrent,
        power_kW: 0,
        temp_bearing_C: 25,
        temp_belt_C: 25,
        temp_drum_C: 25,
        misaligned: false,
        torn: false,
        underspeed_warn: false,
        underspeed_alarm: false,
        chute_level_pct: 0,
        chute_plugged: false
      };
    });

    const elevatorSeg = CONFIG.plant.route.segments.find(s => s.id === 'ELV01')!;
    const elevator: ElevatorState = {
      id: 'ELV01',
      running: false,
      speed_mps: 0,
      flow_tph: 0,
      current_A: 0,
      power_kW: 0,
      temp_motor_C: 25,
      temp_gearbox_C: 25,
      temp_bearing_sup_C: 25,
      temp_bearing_inf_C: 25,
      belt_loose: false,
      slip: false,
      jammed: false,
      spark_detected: false
    };

    const balanceSeg = CONFIG.plant.route.segments.find(s => s.id === 'BAL01')!;
    const balance: BalanceState = {
      id: 'BAL01',
      running: false,
      cycle_state: 'idle',
      weight_kg: 0,
      target_kg: balanceSeg.batch_target_kg!,
      cycle_count: 0,
      total_mass_t: 0,
      avg_flow_tph: 0,
      failure: false
    };

    const shiploader: ShipLoaderState = {
      id: 'SLD01',
      running: false,
      flow_sp_tph: CONFIG.assumptions.shiploader_master_tph,
      flow_pv_tph: 0,
      position_deg: 0,
      dust_level: 0,
      current_A: 0,
      power_kW: 0
    };

    const pi_controller: PIControllerState = {
      error: 0,
      integral: 0,
      output: 0,
      A_tot: 0,
      active_gates: [1, 2, 3, 4] // Start with first 4 gates
    };

    // Health: 100% for all equipment
    const health: { [id: string]: number } = {};
    ['CORR01', 'ELV01', 'CORR02', 'BAL01', 'CORR03', 'SLD01'].forEach(id => {
      health[id] = 100;
    });
    gates.forEach(g => {
      health[`GATE${String(g.id).padStart(2, '0')}`] = 100;
    });

    return {
      time_s: 0,
      running: false,
      warehouse_inventory_t: CONFIG.plant.warehouse.initial_inventory_t,
      warehouse_level_pct: (CONFIG.plant.warehouse.initial_inventory_t /
                           (CONFIG.plant.warehouse.geometry.volume_m3 * CONFIG.product.bulk_density_t_m3)) * 100,
      gates,
      belts,
      elevator,
      balance,
      shiploader,
      pi_controller,
      total_kWh: 0,
      total_mass_t: 0,
      kWh_per_ton: 0,
      cost_R$: 0,
      alarms: [],
      trips: [],
      health,
      emergency_stop: false
    };
  }

  // --------------------------------------------------------------------------
  // PUBLIC API
  // --------------------------------------------------------------------------

  public start(): void {
    this.state.running = true;
    this.state.shiploader.running = true;
    this.startBelts();
    this.state.elevator.running = true;
    this.state.balance.running = true;
  }

  public stop(): void {
    this.state.running = false;
    this.state.shiploader.running = false;
    this.stopBelts();
    this.state.elevator.running = false;
    this.state.balance.running = false;

    // Close all gates
    this.state.gates.forEach(g => {
      g.open_pct_sp = 0;
    });
  }

  public emergencyStop(): void {
    this.state.emergency_stop = true;
    this.stop();

    // Immediate closure of all gates
    this.state.gates.forEach(g => {
      g.open_pct = 0;
      g.open_pct_sp = 0;
      g.position_fb = 0;
    });
  }

  public reset(): void {
    this.state.emergency_stop = false;
    // Clear latched alarms/trips (in real system would need manual confirmation)
    this.state.alarms = [];
    this.state.trips = [];
  }

  public setShipLoaderSetpoint(tph: number): void {
    this.state.shiploader.flow_sp_tph = Math.max(0, Math.min(1650, tph));
  }

  public setGateManual(gateId: number, open_pct: number): void {
    const gate = this.state.gates.find(g => g.id === gateId);
    if (gate) {
      gate.open_pct_sp = Math.max(0, Math.min(100, open_pct));
    }
  }

  public getState(): SimulatorState {
    return { ...this.state };
  }

  public getTagValue(tagId: string): number | boolean | null {
    // Map tag IDs to state values
    // This will be expanded to cover all OPC-UA tags

    // Gates
    const gateMatch = tagId.match(/GATE(\d{2})_(.+)/);
    if (gateMatch) {
      const gateNum = parseInt(gateMatch[1]);
      const param = gateMatch[2];
      const gate = this.state.gates.find(g => g.id === gateNum);
      if (!gate) return null;

      switch (param) {
        case 'POSITION': return gate.position_fb;
        case 'FLOW': return gate.flow_tph;
        case 'PLUGGED': return gate.plugged;
        default: return null;
      }
    }

    // Belts
    const beltKeys = Object.keys(this.state.belts);
    for (const beltId of beltKeys) {
      if (tagId.startsWith(beltId + '_')) {
        const belt = this.state.belts[beltId];
        const param = tagId.substring(beltId.length + 1);

        switch (param) {
          case 'RPM': return belt.rpm;
          case 'SPEED': return belt.speed_mps;
          case 'FLOW': return belt.flow_tph;
          case 'LOAD': return belt.load_pct;
          case 'CURRENT': return belt.current_A;
          case 'POWER': return belt.power_kW;
          case 'TEMP_BEARING': return belt.temp_bearing_C;
          case 'TEMP_BELT': return belt.temp_belt_C;
          case 'RUNNING': return belt.running;
          case 'MISALIGNED': return belt.misaligned;
          case 'UNDERSPEED_WARN': return belt.underspeed_warn;
          default: return null;
        }
      }
    }

    // Elevator
    if (tagId.startsWith('ELV01_')) {
      const param = tagId.substring(6);
      switch (param) {
        case 'SPEED': return this.state.elevator.speed_mps;
        case 'FLOW': return this.state.elevator.flow_tph;
        case 'CURRENT': return this.state.elevator.current_A;
        case 'POWER': return this.state.elevator.power_kW;
        case 'TEMP_MOTOR': return this.state.elevator.temp_motor_C;
        case 'RUNNING': return this.state.elevator.running;
        case 'SLIP': return this.state.elevator.slip;
        default: return null;
      }
    }

    // Balance
    if (tagId.startsWith('BAL01_')) {
      const param = tagId.substring(6);
      switch (param) {
        case 'WEIGHT': return this.state.balance.weight_kg;
        case 'TOTAL': return this.state.balance.total_mass_t;
        case 'FLOW': return this.state.balance.avg_flow_tph;
        case 'CYCLES': return this.state.balance.cycle_count;
        case 'STATE': return this.state.balance.cycle_state === 'filling' ? 1 : 0;
        default: return null;
      }
    }

    // Shiploader
    if (tagId.startsWith('SLD01_')) {
      const param = tagId.substring(6);
      switch (param) {
        case 'FLOW_SP': return this.state.shiploader.flow_sp_tph;
        case 'FLOW_PV': return this.state.shiploader.flow_pv_tph;
        case 'POWER': return this.state.shiploader.power_kW;
        case 'RUNNING': return this.state.shiploader.running;
        default: return null;
      }
    }

    // Global
    switch (tagId) {
      case 'WAREHOUSE_INVENTORY': return this.state.warehouse_inventory_t;
      case 'WAREHOUSE_LEVEL': return this.state.warehouse_level_pct;
      case 'TOTAL_KWH': return this.state.total_kWh;
      case 'TOTAL_MASS': return this.state.total_mass_t;
      case 'KWH_PER_TON': return this.state.kWh_per_ton;
      case 'SYSTEM_RUNNING': return this.state.running;
      default: return null;
    }
  }

  // --------------------------------------------------------------------------
  // SIMULATION STEP
  // --------------------------------------------------------------------------

  public step(): void {
    if (!this.state.running || this.state.emergency_stop) {
      this.stepDynamics(); // Still update positions/temperatures in standby
      return;
    }

    this.time_s += this.dt_s;
    this.state.time_s = this.time_s;

    // 1. PI Controller updates gate setpoints
    this.stepPIController();

    // 2. Gates dynamics and flow calculation
    this.stepGates();

    // 3. Belt CORR01 receives total gate flow
    this.stepBelt('CORR01');

    // 4. Elevator
    this.stepElevator();

    // 5. Belt CORR02
    this.stepBelt('CORR02');

    // 6. Balance (batch cycles)
    this.stepBalance();

    // 7. Belt CORR03 (final flow measurement - PV for controller)
    this.stepBelt('CORR03');

    // 8. Shiploader
    this.stepShipLoader();

    // 9. Energy accounting
    this.stepEnergy();

    // 10. Alarms and Interlocks
    this.stepAlarmsAndInterlocks();

    // 11. Maintenance/Health
    this.stepMaintenance();

    // 12. Warehouse inventory
    this.stepWarehouse();
  }

  // --------------------------------------------------------------------------
  // PRIVATE: CONTROL
  // --------------------------------------------------------------------------

  private stepPIController(): void {
    const pi = this.state.pi_controller;
    const cfg = CONFIG.control.gates_pi;

    // PV = flow measured at CORR03 (final belt before shiploader)
    const PV = this.state.belts['CORR03']?.flow_tph || 0;

    // SP = shiploader setpoint
    const SP = this.state.shiploader.flow_sp_tph;

    // Error
    const error = SP - PV;
    pi.error = error;

    // PI calculation
    const P_term = cfg.Kp * error;
    pi.integral += cfg.Ki * error * this.dt_s;

    // Anti-windup: clamp integral
    const [A_min, A_max] = cfg.A_tot_limits;
    const output_raw = P_term + pi.integral;

    if (output_raw > A_max) {
      pi.integral = A_max - P_term;
    } else if (output_raw < A_min) {
      pi.integral = A_min - P_term;
    }

    pi.output = P_term + pi.integral;
    pi.A_tot = Math.max(A_min, Math.min(A_max, pi.output));

    // Distribute A_tot among active gates equally
    const n_gates = pi.active_gates.length;
    if (n_gates > 0) {
      const open_per_gate = (pi.A_tot / n_gates);

      pi.active_gates.forEach(gateId => {
        const gate = this.state.gates.find(g => g.id === gateId);
        if (gate) {
          const [open_min, open_max] = cfg.gate_open_limits_pct;
          gate.open_pct_sp = Math.max(open_min, Math.min(open_max, open_per_gate));
        }
      });
    }
  }

  // --------------------------------------------------------------------------
  // PRIVATE: GATES
  // --------------------------------------------------------------------------

  private stepGates(): void {
    const cfg = CONFIG.plant.warehouse.gates;
    const ramp_rate = CONFIG.control.gates_pi.ramp_pct_per_s;

    // Warehouse level normalized (0-1)
    const h_norm = this.state.warehouse_level_pct / 100;

    let total_flow = 0;

    this.state.gates.forEach(gate => {
      if (gate.failure || gate.plugged) {
        gate.flow_tph = 0;
        return;
      }

      // Position dynamics (first order with rate limit)
      const delta = gate.open_pct_sp - gate.open_pct;
      const max_delta = ramp_rate * this.dt_s;
      const actual_delta = Math.max(-max_delta, Math.min(max_delta, delta));
      gate.open_pct += actual_delta;
      gate.position_fb = gate.open_pct; // Instantaneous feedback

      // Flow from curve (interpolate)
      const flow_ideal = this.interpolateFlowCurve(gate.open_pct, h_norm);

      gate.flow_tph = flow_ideal;
      total_flow += flow_ideal;
    });

    // Apply saturation penalty if multiple gates open
    const n_open = this.state.gates.filter(g => g.open_pct > 5).length;
    if (n_open > 1) {
      const penalty = 1 - (cfg.alpha_saturation * (n_open - 1) / cfg.count);
      this.state.gates.forEach(g => {
        g.flow_tph *= penalty;
      });
    }
  }

  private interpolateFlowCurve(open_pct: number, h_norm: number): number {
    const curve = CONFIG.plant.warehouse.gates.flow_curve;

    // Find bounding points
    let lower = curve[0];
    let upper = curve[curve.length - 1];

    for (let i = 0; i < curve.length - 1; i++) {
      if (open_pct >= curve[i].open_pct && open_pct <= curve[i + 1].open_pct) {
        lower = curve[i];
        upper = curve[i + 1];
        break;
      }
    }

    // Linear interpolation
    const t = (open_pct - lower.open_pct) / (upper.open_pct - lower.open_pct + 0.001);
    const q_base = lower.q_tph + t * (upper.q_tph - lower.q_tph);

    // Level penalty
    const h_required = lower.h_norm_min + t * (upper.h_norm_min - lower.h_norm_min);
    const level_factor = h_norm < h_required ? (h_norm / h_required) : 1.0;

    return q_base * level_factor;
  }

  // --------------------------------------------------------------------------
  // PRIVATE: BELTS
  // --------------------------------------------------------------------------

  private stepBelt(beltId: string): void {
    const belt = this.state.belts[beltId];
    if (!belt) return;

    const seg = CONFIG.plant.route.segments.find(s => s.id === beltId)!;

    if (!belt.running) {
      belt.speed_mps = 0;
      belt.rpm = 0;
      belt.flow_tph = 0;
      belt.current_A = belt.current_nom_A * 0.2; // No-load current
      belt.power_kW = 0;
      this.coolDown(belt);
      return;
    }

    // Input flow
    let input_flow = 0;
    if (beltId === 'CORR01') {
      input_flow = this.state.gates.reduce((sum, g) => sum + g.flow_tph, 0);
    } else if (beltId === 'CORR02') {
      input_flow = this.state.elevator.flow_tph;
    } else if (beltId === 'CORR03') {
      input_flow = this.state.balance.avg_flow_tph;
    }

    // Chute losses
    input_flow *= (1 - CONFIG.mechanics.belts.chute_losses_pct / 100);

    belt.flow_tph = input_flow;

    // Load calculation
    const capacity = seg.practical_capacity_tph;
    belt.load_pct = (input_flow / capacity) * 100;

    // Mechanical model
    const k_load = CONFIG.mechanics.coefficients.k_load;
    const k_fric = CONFIG.mechanics.coefficients.k_fric;

    // Torque proportional to load
    const torque_factor = 1 + k_load * (belt.load_pct / 100);

    // Speed reduction under heavy load
    const speed_factor = 1 / (1 + 0.1 * Math.max(0, belt.load_pct - 100));
    belt.speed_mps = belt.speed_sp_mps * speed_factor;
    belt.rpm = (belt.speed_mps * 60) / (Math.PI * CONFIG.mechanics.belts.drive_pulley_diameter_mm / 1000);

    // Current and power
    belt.current_A = belt.current_nom_A * torque_factor;
    belt.power_kW = seg.motor_kW * torque_factor;

    // Thermal model
    const ambient_C = 25;
    const heating_rate = 0.005 * belt.load_pct;
    const cooling_rate = 0.02 * (belt.temp_bearing_C - ambient_C);
    belt.temp_bearing_C += (heating_rate - cooling_rate) * this.dt_s;
    belt.temp_belt_C += (heating_rate * 0.7 - cooling_rate * 0.8) * this.dt_s;
    belt.temp_drum_C += (heating_rate * 0.8 - cooling_rate * 0.9) * this.dt_s;

    // Underspeed detection
    const rpm_pct = (belt.rpm / belt.rpm_nom) * 100;
    belt.underspeed_warn = rpm_pct < CONFIG.mechanics.underspeed.warn_pct_nominal;
    belt.underspeed_alarm = rpm_pct < CONFIG.mechanics.underspeed.alarm_pct_nominal;

    // Random faults (very low probability)
    if (Math.random() < 0.00001) belt.misaligned = true;
    if (Math.random() < 0.000001) belt.torn = true;

    // Chute level (simple accumulator)
    const chute_in_rate = input_flow / 3600; // t/s
    const chute_out_rate = belt.flow_tph / 3600;
    const delta_chute = (chute_in_rate - chute_out_rate) * this.dt_s * 10; // Simplified
    belt.chute_level_pct = Math.max(0, Math.min(100, belt.chute_level_pct + delta_chute));

    belt.chute_plugged = belt.chute_level_pct > CONFIG.mechanics.belts.plugging.trip_pct;
  }

  private coolDown(belt: BeltState): void {
    const ambient_C = 25;
    const cool_rate = 0.05;
    belt.temp_bearing_C += (ambient_C - belt.temp_bearing_C) * cool_rate * this.dt_s;
    belt.temp_belt_C += (ambient_C - belt.temp_belt_C) * cool_rate * this.dt_s;
    belt.temp_drum_C += (ambient_C - belt.temp_drum_C) * cool_rate * this.dt_s;
  }

  private startBelts(): void {
    Object.values(this.state.belts).forEach(belt => {
      belt.running = true;
    });
  }

  private stopBelts(): void {
    Object.values(this.state.belts).forEach(belt => {
      belt.running = false;
    });
  }

  // --------------------------------------------------------------------------
  // PRIVATE: ELEVATOR
  // --------------------------------------------------------------------------

  private stepElevator(): void {
    const elv = this.state.elevator;
    const seg = CONFIG.plant.route.segments.find(s => s.id === 'ELV01')!;

    if (!elv.running) {
      elv.speed_mps = 0;
      elv.flow_tph = 0;
      elv.current_A = 0;
      elv.power_kW = 0;
      this.coolDownElevator();
      return;
    }

    // Input from CORR01
    const input_flow = this.state.belts['CORR01']?.flow_tph || 0;

    // Capacity check
    const buckets_per_s = seg.belt_speed_mps! * seg.buckets_per_m!;
    const capacity_tph = buckets_per_s * (seg.bucket_vol_L! / 1000) * CONFIG.product.bulk_density_t_m3 * 3600;

    elv.flow_tph = Math.min(input_flow, capacity_tph);
    elv.speed_mps = seg.belt_speed_mps!;

    // Load and slip
    const load_ratio = input_flow / capacity_tph;
    if (load_ratio > 1.05) {
      elv.slip = true;
    } else {
      elv.slip = false;
    }

    // Power
    const torque_factor = 1 + 0.5 * load_ratio;
    elv.current_A = (seg.motor_kW * 1000 / (440 * Math.sqrt(3) * 0.9)) * torque_factor;
    elv.power_kW = seg.motor_kW * torque_factor;

    // Thermal
    const ambient = 25;
    const heat_motor = 0.01 * load_ratio * 100;
    const cool_motor = 0.03 * (elv.temp_motor_C - ambient);
    elv.temp_motor_C += (heat_motor - cool_motor) * this.dt_s;

    elv.temp_gearbox_C += (heat_motor * 0.8 - 0.025 * (elv.temp_gearbox_C - ambient)) * this.dt_s;
    elv.temp_bearing_sup_C += (heat_motor * 0.6 - 0.02 * (elv.temp_bearing_sup_C - ambient)) * this.dt_s;
    elv.temp_bearing_inf_C += (heat_motor * 0.6 - 0.02 * (elv.temp_bearing_inf_C - ambient)) * this.dt_s;

    // Random faults
    if (Math.random() < 0.00001) elv.belt_loose = true;
    if (Math.random() < 0.000005) elv.jammed = true;
  }

  private coolDownElevator(): void {
    const ambient = 25;
    const rate = 0.05;
    this.state.elevator.temp_motor_C += (ambient - this.state.elevator.temp_motor_C) * rate * this.dt_s;
    this.state.elevator.temp_gearbox_C += (ambient - this.state.elevator.temp_gearbox_C) * rate * this.dt_s;
    this.state.elevator.temp_bearing_sup_C += (ambient - this.state.elevator.temp_bearing_sup_C) * rate * this.dt_s;
    this.state.elevator.temp_bearing_inf_C += (ambient - this.state.elevator.temp_bearing_inf_C) * rate * this.dt_s;
  }

  // --------------------------------------------------------------------------
  // PRIVATE: BALANCE
  // --------------------------------------------------------------------------

  private stepBalance(): void {
    const bal = this.state.balance;
    const seg = CONFIG.plant.route.segments.find(s => s.id === 'BAL01')!;

    if (!bal.running) {
      bal.cycle_state = 'idle';
      bal.weight_kg = 0;
      bal.avg_flow_tph = 0;
      return;
    }

    const fill_time_s = seg.fill_s!;
    const discharge_time_s = seg.discharge_s!;
    const cycle_time_s = fill_time_s + discharge_time_s;

    // Input from CORR02
    const input_flow_tph = this.state.belts['CORR02']?.flow_tph || 0;
    const input_rate_kg_s = (input_flow_tph * 1000) / 3600;

    // State machine
    if (bal.cycle_state === 'idle') {
      bal.cycle_state = 'filling';
      bal.weight_kg = 0;
    }

    if (bal.cycle_state === 'filling') {
      bal.weight_kg += input_rate_kg_s * this.dt_s;

      if (bal.weight_kg >= bal.target_kg) {
        bal.cycle_state = 'discharging';
        bal.cycle_count++;
        bal.total_mass_t += bal.weight_kg / 1000;
      }
    } else if (bal.cycle_state === 'discharging') {
      // Discharge in fixed time
      const discharge_rate_kg_s = bal.target_kg / discharge_time_s;
      bal.weight_kg = Math.max(0, bal.weight_kg - discharge_rate_kg_s * this.dt_s);

      if (bal.weight_kg < 1) {
        bal.cycle_state = 'filling';
        bal.weight_kg = 0;
      }
    }

    // Average flow
    const cycles_per_hour = 3600 / cycle_time_s;
    bal.avg_flow_tph = (bal.target_kg / 1000) * cycles_per_hour;
  }

  // --------------------------------------------------------------------------
  // PRIVATE: SHIPLOADER
  // --------------------------------------------------------------------------

  private stepShipLoader(): void {
    const sld = this.state.shiploader;

    if (!sld.running) {
      sld.flow_pv_tph = 0;
      sld.power_kW = 0;
      return;
    }

    // Receives flow from CORR03
    sld.flow_pv_tph = this.state.belts['CORR03']?.flow_tph || 0;

    // Power
    const seg = CONFIG.plant.route.segments.find(s => s.id === 'SLD01')!;
    const load_ratio = sld.flow_pv_tph / seg.master_capacity_tph!;
    sld.power_kW = seg.motor_kW * (0.3 + 0.7 * load_ratio);
    sld.current_A = (sld.power_kW * 1000) / (440 * Math.sqrt(3) * 0.92);

    // Dust (proportional to flow)
    sld.dust_level = load_ratio * 80;
  }

  // --------------------------------------------------------------------------
  // PRIVATE: ENERGY
  // --------------------------------------------------------------------------

  private stepEnergy(): void {
    let total_power_kW = 0;

    Object.values(this.state.belts).forEach(belt => {
      total_power_kW += belt.power_kW;
    });
    total_power_kW += this.state.elevator.power_kW;
    total_power_kW += this.state.shiploader.power_kW;

    const energy_kWh_step = (total_power_kW * this.dt_s) / 3600;
    this.state.total_kWh += energy_kWh_step;

    // Mass accumulation
    const flow_tph = this.state.shiploader.flow_pv_tph;
    const mass_t_step = (flow_tph * this.dt_s) / 3600;
    this.state.total_mass_t += mass_t_step;

    // KPIs
    if (this.state.total_mass_t > 0.1) {
      this.state.kWh_per_ton = this.state.total_kWh / this.state.total_mass_t;
    }

    // Cost (simplified - assumes peak hours)
    const tariff = CONFIG.electrical.tariffs.peak_R$_kWh;
    this.state.cost_R$ += energy_kWh_step * tariff;
  }

  // --------------------------------------------------------------------------
  // PRIVATE: ALARMS & INTERLOCKS
  // --------------------------------------------------------------------------

  private stepAlarmsAndInterlocks(): void {
    this.checkAlarms();
    this.applyInterlocks();
  }

  private checkAlarms(): void {
    // Temperature alarms
    Object.values(this.state.belts).forEach(belt => {
      this.checkThermalAlarm(`${belt.id}_BEARING`, belt.temp_bearing_C, 'bearing');
      this.checkThermalAlarm(`${belt.id}_BELT`, belt.temp_belt_C, 'belt');
      this.checkThermalAlarm(`${belt.id}_DRUM`, belt.temp_drum_C, 'drum');
    });

    this.checkThermalAlarm('ELV01_MOTOR', this.state.elevator.temp_motor_C, 'motor');

    // Underspeed
    Object.values(this.state.belts).forEach(belt => {
      if (belt.underspeed_alarm) {
        this.setAlarm(`AL_${belt.id}_SUBVELOCIDADE`, true);
      } else {
        this.setAlarm(`AL_${belt.id}_SUBVELOCIDADE`, false);
      }
    });

    // Torn belt
    Object.values(this.state.belts).forEach(belt => {
      if (belt.torn) {
        this.setTrip(`TRIP_${belt.id}_RASGO`, true);
      }
    });

    // Elevator slip
    if (this.state.elevator.slip) {
      this.setAlarm('AL_ELV01_ESCORREGAMENTO', true);
    }
  }

  private checkThermalAlarm(equipId: string, temp_C: number, zone: string): void {
    const limits = CONFIG.thermal_limits[zone];
    if (!limits) return;

    if (temp_C >= limits.trip_C) {
      this.setTrip(`TRIP_${equipId}_SOBRETEMP`, true);
    } else if (temp_C >= limits.alarm_C) {
      this.setAlarm(`AL_${equipId}_TEMP_ALTA`, true);
    } else if (temp_C >= limits.warn_C) {
      this.setAlarm(`AL_${equipId}_TEMP_WARN`, true);
    }
  }

  private setAlarm(tag: string, active: boolean): void {
    let alarm = this.state.alarms.find(a => a.tag === tag);
    if (!alarm) {
      alarm = { tag, active: false, latched: false, timestamp: 0, count: 0 };
      this.state.alarms.push(alarm);
    }

    if (active && !alarm.active) {
      alarm.active = true;
      alarm.latched = true;
      alarm.timestamp = this.time_s;
      alarm.count++;
    } else if (!active) {
      alarm.active = false;
      // Latched alarms stay true until manual reset
    }
  }

  private setTrip(tag: string, active: boolean): void {
    let trip = this.state.trips.find(t => t.tag === tag);
    if (!trip) {
      trip = { tag, active: false, latched: false, timestamp: 0, count: 0 };
      this.state.trips.push(trip);
    }

    if (active && !trip.active) {
      trip.active = true;
      trip.latched = true;
      trip.timestamp = this.time_s;
      trip.count++;
    }
  }

  private applyInterlocks(): void {
    // Check interlock matrix
    CONFIG.interlocks.matrix.forEach(il => {
      const causeActive = this.isCauseActive(il.cause);

      if (causeActive) {
        il.effect.forEach(eff => {
          this.executeEffect(eff);
        });
      }
    });
  }

  private isCauseActive(cause: string): boolean {
    // Check if alarm/trip is active
    const alarm = this.state.alarms.find(a => a.tag === cause && a.active);
    const trip = this.state.trips.find(t => t.tag === cause && t.active);
    return !!(alarm || trip);
  }

  private executeEffect(effect: string): void {
    if (effect === 'CMD_ALL_STOP') {
      this.stop();
    } else if (effect === 'GATES_CLOSE_ALL') {
      this.state.gates.forEach(g => g.open_pct_sp = 0);
    } else if (effect === 'GATE_CLOSE_ONE') {
      // Close one gate (highest numbered open gate)
      const openGates = this.state.gates.filter(g => g.open_pct > 10).sort((a, b) => b.id - a.id);
      if (openGates.length > 0) {
        openGates[0].open_pct_sp = 0;
      }
    } else if (effect.startsWith('CMD_') && effect.includes('_PARAR')) {
      // Stop specific equipment
      const eqId = effect.replace('CMD_', '').replace('_PARAR', '');
      if (this.state.belts[eqId]) {
        this.state.belts[eqId].running = false;
      }
    }
  }

  // --------------------------------------------------------------------------
  // PRIVATE: MAINTENANCE
  // --------------------------------------------------------------------------

  private stepMaintenance(): void {
    const k_uso = CONFIG.maintenance.health_model.k.k_uso;

    // Degrade health based on load
    Object.values(this.state.belts).forEach(belt => {
      const load_rel = belt.load_pct / 100;
      this.state.health[belt.id] -= k_uso * load_rel * this.dt_s;
      this.state.health[belt.id] = Math.max(0, this.state.health[belt.id]);
    });

    // Health alarms
    Object.keys(this.state.health).forEach(eqId => {
      const h = this.state.health[eqId];
      if (h < CONFIG.maintenance.health_model.thresholds_pct.trip) {
        this.setAlarm(`AL_${eqId}_SAUDE_CRITICA`, true);
      } else if (h < CONFIG.maintenance.health_model.thresholds_pct.plan) {
        this.setAlarm(`AL_${eqId}_MANUTENCAO_PROGRAMAR`, true);
      } else if (h < CONFIG.maintenance.health_model.thresholds_pct.warn) {
        this.setAlarm(`AL_${eqId}_MANUTENCAO_PREVENTIVA`, true);
      }
    });
  }

  // --------------------------------------------------------------------------
  // PRIVATE: WAREHOUSE
  // --------------------------------------------------------------------------

  private stepWarehouse(): void {
    // Mass balance
    const total_gate_flow_tph = this.state.gates.reduce((sum, g) => sum + g.flow_tph, 0);
    const mass_out_t = (total_gate_flow_tph * this.dt_s) / 3600;

    this.state.warehouse_inventory_t -= mass_out_t;
    this.state.warehouse_inventory_t = Math.max(0, this.state.warehouse_inventory_t);

    // Level
    const max_inventory_t = CONFIG.plant.warehouse.geometry.volume_m3 * CONFIG.product.bulk_density_t_m3;
    this.state.warehouse_level_pct = (this.state.warehouse_inventory_t / max_inventory_t) * 100;
  }

  // --------------------------------------------------------------------------
  // PRIVATE: DYNAMICS
  // --------------------------------------------------------------------------

  private stepDynamics(): void {
    // Update positions, temperatures even when stopped
    this.state.gates.forEach(gate => {
      const delta = gate.open_pct_sp - gate.open_pct;
      const rate = CONFIG.control.gates_pi.ramp_pct_per_s;
      const max_d = rate * this.dt_s;
      gate.open_pct += Math.max(-max_d, Math.min(max_d, delta));
      gate.position_fb = gate.open_pct;
    });

    // Cool down all equipment
    Object.values(this.state.belts).forEach(belt => this.coolDown(belt));
    this.coolDownElevator();
  }
}

// Singleton instance
export const grainTerminalSimulator = new GrainTerminalSimulator();
