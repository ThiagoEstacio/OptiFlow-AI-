#!/usr/bin/env python3
"""
OptiFlow OPC UA Simulator - Grain Terminal + Eletrocentro
=========================================================

Simulates a complete grain terminal with:
- Conveyors (CORR01-03)
- Silos (SILO01-03)
- Elevators (ELEV01-02)
- Shiploader (SLD01)
- Complete Eletrocentro (electrical power center):
  - Transformer (TR01) - 1000 kVA, 13.8kV/480V
  - CCM (Centro de Controle de Motores) with 8 drawers
  - Multi-Meters (PM_GERAL, PM_CCM01, PM_ILUM)
  - Capacitor Bank (BC01)
  - Protection Relays

Behaves exactly like a real industrial OPC UA server
"""

import asyncio
import logging
import sys
import time
import random
import math
from datetime import datetime
from asyncua import Server, ua

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EletrocentroSimulator:
    """
    Simulates complete electrical power center (Eletrocentro)

    Equipment:
    - TR01: Power Transformer 1000 kVA, 13.8kV/480V
    - CCM01: Motor Control Center with 8 drawers
    - PM_GERAL, PM_CCM01, PM_ILUM: Sector power meters
    - BC01: Capacitor bank for PF correction
    - REL_GERAL: Main protection relay
    """

    def __init__(self):
        self.start_time = time.time()
        self.total_energy_kwh = 0.0
        self.total_kvarh = 0.0
        self.peak_demand_kw = 0.0

        # Equipment definitions
        self.ccm_equipment = ["CORR01", "CORR02", "CORR03", "SLD01", "SLD02", "ELV01", "VNT01", "VNT02"]

        # Initialize states
        self._init_transformer()
        self._init_ccm_drawers()
        self._init_power_meters()
        self._init_capacitor_bank()
        self._init_main_relay()

    def _init_transformer(self):
        """Initialize transformer TR01"""
        self.transformer = {
            "load_pct": 45.0,
            "power_kw": 450.0,
            "power_kvar": 150.0,
            "power_kva": 474.0,
            "pf": 0.95,
            "current_pri_a": 20.0,
            "current_sec_a": 570.0,
            "temp_winding_c": 65.0,
            "temp_oil_c": 55.0,
            "alarm_overtemp": False,
            "alarm_overload": False,
        }

    def _init_ccm_drawers(self):
        """Initialize CCM drawers for each motor"""
        self.ccm = {}

        # Motor ratings (kW)
        motor_ratings = {
            "CORR01": 55, "CORR02": 55, "CORR03": 75,
            "SLD01": 90, "SLD02": 45,
            "ELV01": 45, "VNT01": 22, "VNT02": 22
        }

        # Starter types
        starter_types = {
            "CORR01": "softstart", "CORR02": "softstart", "CORR03": "softstart",
            "SLD01": "vfd", "SLD02": "vfd",
            "ELV01": "softstart", "VNT01": "dol", "VNT02": "dol"
        }

        for equip in self.ccm_equipment:
            rating = motor_ratings[equip]
            starter = starter_types[equip]

            self.ccm[equip] = {
                # Basic drawer
                "running": True,
                "breaker": True,
                "contactor": True,
                "current_a": rating * 1.5 * 0.7,  # ~70% load
                "power_kw": rating * 0.7,
                "power_kvar": rating * 0.25,
                "starter_type": starter,

                # Softstart data
                "ss_state": 3 if starter == "softstart" else 0,  # 3=Running
                "ss_voltage_pct": 100.0 if starter == "softstart" else 0,
                "ss_motor_temp_pct": 45.0 if starter == "softstart" else 0,
                "ss_fault": False,

                # VFD data
                "vfd_state": 2 if starter == "vfd" else 0,  # 2=Running
                "vfd_freq_hz": 60.0 if starter == "vfd" else 0,
                "vfd_voltage_v": 460.0 if starter == "vfd" else 0,
                "vfd_speed_rpm": 1750.0 if starter == "vfd" else 0,
                "vfd_torque_pct": 70.0 if starter == "vfd" else 0,
                "vfd_dc_bus_v": 650.0 if starter == "vfd" else 0,
                "vfd_temp_c": 45.0 if starter == "vfd" else 0,
                "vfd_energy_kwh": 0.0,
                "vfd_fault": False,

                # Protection relay
                "rel_state": 1,  # Normal
                "rel_thermal_pct": 55.0,
                "rel_fn50": False,  # Instantaneous overcurrent
                "rel_fn51": False,  # Time overcurrent
                "rel_fn49": False,  # Thermal
                "rel_trip": False,

                # Power meter
                "pm_v_ab": 480.0 + random.uniform(-5, 5),
                "pm_v_bc": 480.0 + random.uniform(-5, 5),
                "pm_v_ca": 480.0 + random.uniform(-5, 5),
                "pm_i_a": rating * 1.5 * 0.7 + random.uniform(-2, 2),
                "pm_i_b": rating * 1.5 * 0.7 + random.uniform(-2, 2),
                "pm_i_c": rating * 1.5 * 0.7 + random.uniform(-2, 2),
                "pm_freq_hz": 60.0,
                "pm_pf": 0.85,
                "pm_kwh": 0.0,
            }

    def _init_power_meters(self):
        """Initialize sector power meters"""
        self.power_meters = {
            "PM_GERAL": self._create_meter(450, 0.92),
            "PM_CCM01": self._create_meter(380, 0.88),
            "PM_ILUM": self._create_meter(25, 0.98),
        }

    def _create_meter(self, base_kw: float, base_pf: float) -> dict:
        """Create a power meter with all variables"""
        kvar = base_kw * math.tan(math.acos(base_pf))
        kva = math.sqrt(base_kw**2 + kvar**2)
        current = kva * 1000 / (480 * math.sqrt(3))

        return {
            "v_ab": 480.0, "v_bc": 480.0, "v_ca": 480.0,
            "v_an": 277.0, "v_bn": 277.0, "v_cn": 277.0,
            "i_a": current, "i_b": current, "i_c": current, "i_n": current * 0.1,
            "kw": base_kw, "kvar": kvar, "kva": kva, "pf": base_pf,
            "freq_hz": 60.0,
            "kwh": 0.0, "kvarh": 0.0,
            "thd_v_pct": 2.5, "thd_i_pct": 8.0,
            "demand_kw": base_kw * 0.8, "demand_max_kw": base_kw * 1.1,
        }

    def _init_capacitor_bank(self):
        """Initialize capacitor bank BC01"""
        self.capacitor_bank = {
            "stages_on": 4,
            "stages_total": 6,
            "kvar": 200.0,
            "current_a": 240.0,
            "temp_c": 35.0,
        }

    def _init_main_relay(self):
        """Initialize main protection relay"""
        self.main_relay = {
            "state": 1,  # Normal
            "thermal_pct": 45.0,
            "trip": False,
            "trip_count": 0,
        }

    def update(self, motor_loads: dict, dt_s: float = 1.0):
        """
        Update all electrical simulation

        Args:
            motor_loads: Dict of motor name -> load percentage (0-100)
            dt_s: Time step in seconds
        """
        elapsed = time.time() - self.start_time

        # Update each CCM drawer based on motor loads
        total_kw = 0.0
        total_kvar = 0.0

        for equip in self.ccm_equipment:
            drawer = self.ccm[equip]
            load_pct = motor_loads.get(equip, 70.0)  # Default 70% load

            # Update drawer based on load
            if drawer["running"]:
                # Power calculations
                nominal_kw = {"CORR01": 55, "CORR02": 55, "CORR03": 75,
                             "SLD01": 90, "SLD02": 45, "ELV01": 45,
                             "VNT01": 22, "VNT02": 22}[equip]

                drawer["power_kw"] = nominal_kw * (load_pct / 100) + random.uniform(-1, 1)
                drawer["power_kvar"] = drawer["power_kw"] * 0.35 + random.uniform(-0.5, 0.5)
                drawer["current_a"] = drawer["power_kw"] * 1000 / (480 * math.sqrt(3) * 0.85)
                drawer["current_a"] += random.uniform(-1, 1)

                # Update starter-specific values
                if drawer["starter_type"] == "softstart":
                    drawer["ss_motor_temp_pct"] = 40 + load_pct * 0.3 + random.uniform(-2, 2)
                    drawer["ss_motor_temp_pct"] = min(95, drawer["ss_motor_temp_pct"])

                elif drawer["starter_type"] == "vfd":
                    # VFD adjusts frequency based on load
                    drawer["vfd_freq_hz"] = 50 + load_pct * 0.1 + random.uniform(-0.5, 0.5)
                    drawer["vfd_speed_rpm"] = drawer["vfd_freq_hz"] / 60 * 1750
                    drawer["vfd_torque_pct"] = load_pct + random.uniform(-3, 3)
                    drawer["vfd_temp_c"] = 35 + load_pct * 0.25 + random.uniform(-1, 1)
                    drawer["vfd_dc_bus_v"] = 650 + random.uniform(-10, 10)
                    drawer["vfd_energy_kwh"] += drawer["power_kw"] * dt_s / 3600

                # Relay thermal image
                drawer["rel_thermal_pct"] = 30 + load_pct * 0.5 + random.uniform(-2, 2)
                drawer["rel_thermal_pct"] = min(100, drawer["rel_thermal_pct"])

                # Power meter update
                drawer["pm_v_ab"] = 480 + random.uniform(-3, 3)
                drawer["pm_v_bc"] = 480 + random.uniform(-3, 3)
                drawer["pm_v_ca"] = 480 + random.uniform(-3, 3)
                drawer["pm_i_a"] = drawer["current_a"] + random.uniform(-1, 1)
                drawer["pm_i_b"] = drawer["current_a"] + random.uniform(-1, 1)
                drawer["pm_i_c"] = drawer["current_a"] + random.uniform(-1, 1)
                drawer["pm_pf"] = 0.80 + load_pct * 0.001
                drawer["pm_kwh"] += drawer["power_kw"] * dt_s / 3600

                total_kw += drawer["power_kw"]
                total_kvar += drawer["power_kvar"]
            else:
                drawer["power_kw"] = 0
                drawer["power_kvar"] = 0
                drawer["current_a"] = 0

        # Update transformer
        self.transformer["power_kw"] = total_kw + 25  # +25kW for losses/lighting
        self.transformer["power_kvar"] = total_kvar + 10
        self.transformer["power_kva"] = math.sqrt(
            self.transformer["power_kw"]**2 + self.transformer["power_kvar"]**2
        )
        self.transformer["load_pct"] = (self.transformer["power_kva"] / 1000) * 100
        self.transformer["pf"] = self.transformer["power_kw"] / max(1, self.transformer["power_kva"])

        # Transformer currents
        self.transformer["current_pri_a"] = self.transformer["power_kva"] / (13.8 * math.sqrt(3))
        self.transformer["current_sec_a"] = self.transformer["power_kva"] * 1000 / (480 * math.sqrt(3))

        # Transformer temperatures (thermal model)
        target_winding = 50 + self.transformer["load_pct"] * 0.4
        self.transformer["temp_winding_c"] += (target_winding - self.transformer["temp_winding_c"]) * 0.02
        self.transformer["temp_winding_c"] += random.uniform(-0.3, 0.3)

        target_oil = 40 + self.transformer["load_pct"] * 0.25
        self.transformer["temp_oil_c"] += (target_oil - self.transformer["temp_oil_c"]) * 0.01
        self.transformer["temp_oil_c"] += random.uniform(-0.2, 0.2)

        # Alarms
        self.transformer["alarm_overtemp"] = self.transformer["temp_winding_c"] > 95
        self.transformer["alarm_overload"] = self.transformer["load_pct"] > 100

        # Update power meters
        for meter_name, meter in self.power_meters.items():
            if meter_name == "PM_GERAL":
                meter["kw"] = self.transformer["power_kw"]
                meter["kvar"] = self.transformer["power_kvar"]
            elif meter_name == "PM_CCM01":
                meter["kw"] = total_kw
                meter["kvar"] = total_kvar
            # PM_ILUM stays relatively constant

            meter["kva"] = math.sqrt(meter["kw"]**2 + meter["kvar"]**2)
            meter["pf"] = meter["kw"] / max(1, meter["kva"])

            # Currents
            meter["i_a"] = meter["kva"] * 1000 / (480 * math.sqrt(3)) + random.uniform(-1, 1)
            meter["i_b"] = meter["i_a"] + random.uniform(-0.5, 0.5)
            meter["i_c"] = meter["i_a"] + random.uniform(-0.5, 0.5)

            # Voltages with variation
            meter["v_ab"] = 480 + random.uniform(-3, 3)
            meter["v_bc"] = 480 + random.uniform(-3, 3)
            meter["v_ca"] = 480 + random.uniform(-3, 3)
            meter["v_an"] = meter["v_ab"] / math.sqrt(3)
            meter["v_bn"] = meter["v_bc"] / math.sqrt(3)
            meter["v_cn"] = meter["v_ca"] / math.sqrt(3)

            # Energy accumulation
            meter["kwh"] += meter["kw"] * dt_s / 3600
            meter["kvarh"] += meter["kvar"] * dt_s / 3600

            # Demand (15-min rolling average simulation)
            meter["demand_kw"] = meter["demand_kw"] * 0.99 + meter["kw"] * 0.01
            meter["demand_max_kw"] = max(meter["demand_max_kw"], meter["demand_kw"])

            # THD varies slightly
            meter["thd_v_pct"] = 2.0 + random.uniform(0, 1.5)
            meter["thd_i_pct"] = 5.0 + random.uniform(0, 6.0)

        # Update capacitor bank (automatic PF correction)
        target_pf = 0.92
        current_pf = self.transformer["pf"]

        if current_pf < target_pf - 0.02:
            # Need more kVAR
            if self.capacitor_bank["stages_on"] < self.capacitor_bank["stages_total"]:
                self.capacitor_bank["stages_on"] += 1
        elif current_pf > target_pf + 0.02:
            # Too much kVAR
            if self.capacitor_bank["stages_on"] > 0:
                self.capacitor_bank["stages_on"] -= 1

        self.capacitor_bank["kvar"] = self.capacitor_bank["stages_on"] * 50  # 50 kVAR per stage
        self.capacitor_bank["current_a"] = self.capacitor_bank["kvar"] * 1000 / (480 * math.sqrt(3))
        self.capacitor_bank["temp_c"] = 30 + self.capacitor_bank["stages_on"] * 2 + random.uniform(-1, 1)

        # Update main relay
        self.main_relay["thermal_pct"] = self.transformer["load_pct"] * 0.8
        self.main_relay["trip"] = self.main_relay["thermal_pct"] > 100

        # Update totals
        self.total_energy_kwh += self.transformer["power_kw"] * dt_s / 3600
        self.total_kvarh += self.transformer["power_kvar"] * dt_s / 3600
        self.peak_demand_kw = max(self.peak_demand_kw, self.transformer["power_kw"])

    def get_all_tags(self) -> dict:
        """Get all electrical tags as flat dictionary"""
        tags = {}

        # Transformer tags
        tags["TR01_LOAD_PCT_PV"] = self.transformer["load_pct"]
        tags["TR01_POWER_KW_PV"] = self.transformer["power_kw"]
        tags["TR01_POWER_KVAR_PV"] = self.transformer["power_kvar"]
        tags["TR01_POWER_KVA_PV"] = self.transformer["power_kva"]
        tags["TR01_PF_PV"] = self.transformer["pf"]
        tags["TR01_CURRENT_PRI_A_PV"] = self.transformer["current_pri_a"]
        tags["TR01_CURRENT_SEC_A_PV"] = self.transformer["current_sec_a"]
        tags["TR01_TEMP_WINDING_C_PV"] = self.transformer["temp_winding_c"]
        tags["TR01_TEMP_OIL_C_PV"] = self.transformer["temp_oil_c"]
        tags["TR01_ALARM_OVERTEMP_PV"] = self.transformer["alarm_overtemp"]
        tags["TR01_ALARM_OVERLOAD_PV"] = self.transformer["alarm_overload"]

        # CCM drawer tags
        for equip in self.ccm_equipment:
            d = self.ccm[equip]
            prefix = f"CCM01_{equip}"

            # Basic
            tags[f"{prefix}_RUNNING_PV"] = d["running"]
            tags[f"{prefix}_BREAKER_PV"] = d["breaker"]
            tags[f"{prefix}_CONTACTOR_PV"] = d["contactor"]
            tags[f"{prefix}_CURRENT_A_PV"] = d["current_a"]
            tags[f"{prefix}_POWER_KW_PV"] = d["power_kw"]
            tags[f"{prefix}_POWER_KVAR_PV"] = d["power_kvar"]

            # Softstart
            tags[f"{prefix}_SS_STATE_PV"] = d["ss_state"]
            tags[f"{prefix}_SS_VOLTAGE_PCT_PV"] = d["ss_voltage_pct"]
            tags[f"{prefix}_SS_MOTOR_TEMP_PCT_PV"] = d["ss_motor_temp_pct"]
            tags[f"{prefix}_SS_FAULT_PV"] = d["ss_fault"]

            # VFD
            tags[f"{prefix}_VFD_STATE_PV"] = d["vfd_state"]
            tags[f"{prefix}_VFD_FREQ_HZ_PV"] = d["vfd_freq_hz"]
            tags[f"{prefix}_VFD_VOLTAGE_V_PV"] = d["vfd_voltage_v"]
            tags[f"{prefix}_VFD_SPEED_RPM_PV"] = d["vfd_speed_rpm"]
            tags[f"{prefix}_VFD_TORQUE_PCT_PV"] = d["vfd_torque_pct"]
            tags[f"{prefix}_VFD_DC_BUS_V_PV"] = d["vfd_dc_bus_v"]
            tags[f"{prefix}_VFD_TEMP_C_PV"] = d["vfd_temp_c"]
            tags[f"{prefix}_VFD_ENERGY_KWH_PV"] = d["vfd_energy_kwh"]
            tags[f"{prefix}_VFD_FAULT_PV"] = d["vfd_fault"]

            # Relay
            tags[f"{prefix}_REL_STATE_PV"] = d["rel_state"]
            tags[f"{prefix}_REL_THERMAL_PCT_PV"] = d["rel_thermal_pct"]
            tags[f"{prefix}_REL_FN50_PV"] = d["rel_fn50"]
            tags[f"{prefix}_REL_FN51_PV"] = d["rel_fn51"]
            tags[f"{prefix}_REL_FN49_PV"] = d["rel_fn49"]
            tags[f"{prefix}_REL_TRIP_PV"] = d["rel_trip"]

            # Power meter
            tags[f"{prefix}_PM_V_AB_PV"] = d["pm_v_ab"]
            tags[f"{prefix}_PM_V_BC_PV"] = d["pm_v_bc"]
            tags[f"{prefix}_PM_V_CA_PV"] = d["pm_v_ca"]
            tags[f"{prefix}_PM_I_A_PV"] = d["pm_i_a"]
            tags[f"{prefix}_PM_I_B_PV"] = d["pm_i_b"]
            tags[f"{prefix}_PM_I_C_PV"] = d["pm_i_c"]
            tags[f"{prefix}_PM_FREQ_HZ_PV"] = d["pm_freq_hz"]
            tags[f"{prefix}_PM_PF_PV"] = d["pm_pf"]
            tags[f"{prefix}_PM_KWH_PV"] = d["pm_kwh"]

        # Sector power meters
        for meter_name, m in self.power_meters.items():
            tags[f"{meter_name}_V_AB_PV"] = m["v_ab"]
            tags[f"{meter_name}_V_BC_PV"] = m["v_bc"]
            tags[f"{meter_name}_V_CA_PV"] = m["v_ca"]
            tags[f"{meter_name}_V_AN_PV"] = m["v_an"]
            tags[f"{meter_name}_V_BN_PV"] = m["v_bn"]
            tags[f"{meter_name}_V_CN_PV"] = m["v_cn"]
            tags[f"{meter_name}_I_A_PV"] = m["i_a"]
            tags[f"{meter_name}_I_B_PV"] = m["i_b"]
            tags[f"{meter_name}_I_C_PV"] = m["i_c"]
            tags[f"{meter_name}_I_N_PV"] = m["i_n"]
            tags[f"{meter_name}_KW_PV"] = m["kw"]
            tags[f"{meter_name}_KVAR_PV"] = m["kvar"]
            tags[f"{meter_name}_KVA_PV"] = m["kva"]
            tags[f"{meter_name}_PF_PV"] = m["pf"]
            tags[f"{meter_name}_FREQ_HZ_PV"] = m["freq_hz"]
            tags[f"{meter_name}_KWH_PV"] = m["kwh"]
            tags[f"{meter_name}_KVARH_PV"] = m["kvarh"]
            tags[f"{meter_name}_THD_V_PCT_PV"] = m["thd_v_pct"]
            tags[f"{meter_name}_THD_I_PCT_PV"] = m["thd_i_pct"]
            tags[f"{meter_name}_DEMAND_KW_PV"] = m["demand_kw"]
            tags[f"{meter_name}_DEMAND_MAX_KW_PV"] = m["demand_max_kw"]

        # Capacitor bank
        tags["BC01_STAGES_ON_PV"] = self.capacitor_bank["stages_on"]
        tags["BC01_STAGES_TOTAL_PV"] = self.capacitor_bank["stages_total"]
        tags["BC01_KVAR_PV"] = self.capacitor_bank["kvar"]
        tags["BC01_CURRENT_A_PV"] = self.capacitor_bank["current_a"]
        tags["BC01_TEMP_C_PV"] = self.capacitor_bank["temp_c"]

        # Main relay
        tags["REL_GERAL_STATE_PV"] = self.main_relay["state"]
        tags["REL_GERAL_THERMAL_PCT_PV"] = self.main_relay["thermal_pct"]
        tags["REL_GERAL_TRIP_PV"] = self.main_relay["trip"]
        tags["REL_GERAL_TRIP_COUNT_PV"] = self.main_relay["trip_count"]

        # Totals
        tags["ELETRO_TOTAL_KWH_PV"] = self.total_energy_kwh
        tags["ELETRO_TOTAL_KVARH_PV"] = self.total_kvarh
        tags["ELETRO_PEAK_DEMAND_KW_PV"] = self.peak_demand_kw
        tags["ELETRO_TIME_S_PV"] = time.time() - self.start_time

        return tags


class GrainTerminalSimulator:
    """Simulates a grain terminal with realistic dynamic behavior"""

    def __init__(self):
        self.start_time = time.time()
        self.running = True

        # Equipment state
        self.conveyors = {}
        self.silos = {}
        self.elevators = {}
        self.shiploader = {}
        self.energy = {}

        # Eletrocentro
        self.eletrocentro = EletrocentroSimulator()

    def initialize_equipment(self):
        """Initialize equipment with default values"""
        # 3 Conveyors (CORR01-03)
        for i in range(1, 4):
            name = f"CORR{i:02d}"
            self.conveyors[name] = {
                "running": True,
                "speed_mps": 2.5 + random.uniform(-0.2, 0.2),
                "load_pct": random.uniform(50, 80),
                "current_a": random.uniform(30, 50),
                "power_kw": random.uniform(35, 55),
                "temp_c": random.uniform(35, 45),
                "vibration_mms": random.uniform(1.5, 3.5),
                "misalignment": random.uniform(0, 2),
            }

        # 3 Silos (SILO01-03)
        for i in range(1, 4):
            name = f"SILO{i:02d}"
            self.silos[name] = {
                "level_pct": random.uniform(40, 90),
                "temp_grain_c": random.uniform(15, 25),
                "humidity_pct": random.uniform(12, 16),
                "weight_t": random.uniform(500, 2000),
                "pressure_pa": random.uniform(100, 500),
            }

        # 2 Elevators (ELEV01-02)
        for i in range(1, 3):
            name = f"ELEV{i:02d}"
            self.elevators[name] = {
                "running": True,
                "bucket_speed_mps": 1.5 + random.uniform(-0.1, 0.1),
                "current_a": random.uniform(20.0, 35.0),
                "power_kw": random.uniform(25.0, 40.0),
                "temp_c": random.uniform(40.0, 50.0),
            }

        # Shiploader
        self.shiploader = {
            "setpoint_tph": 1200.0,
            "flow_tph": 1150.0,
            "power_kw": 85.0,
            "current_a": 120.0,
        }

        # Energy monitoring (will be updated from eletrocentro)
        self.energy = {
            "grid_power_kw": 150.0,
            "total_energy_kwh": 0.0,
            "power_factor": 0.92,
            "grid_voltage_v": 480.0,
        }

    def update_simulation(self):
        """Update all equipment values with realistic dynamics"""
        elapsed = time.time() - self.start_time

        # Update conveyors with sine wave variations
        for name, conv in self.conveyors.items():
            if conv["running"]:
                conv["speed_mps"] += random.uniform(-0.05, 0.05)
                conv["speed_mps"] = max(2.0, min(3.0, conv["speed_mps"]))

                base_load = 65 + 15 * math.sin(elapsed * 0.1)
                conv["load_pct"] = base_load + random.uniform(-5, 5)
                conv["load_pct"] = max(0, min(100, conv["load_pct"]))

                conv["current_a"] = 30 + (conv["load_pct"] / 100) * 25 + random.uniform(-2, 2)
                conv["power_kw"] = conv["current_a"] * 0.95 + random.uniform(-1, 1)

                target_temp = 35 + (conv["load_pct"] / 100) * 15
                conv["temp_c"] += (target_temp - conv["temp_c"]) * 0.1
                conv["temp_c"] += random.uniform(-0.5, 0.5)

                conv["vibration_mms"] = 2.0 + (conv["speed_mps"] / 3.0) * 2.0 + random.uniform(-0.3, 0.3)
                conv["misalignment"] += random.uniform(-0.1, 0.1)
                conv["misalignment"] = max(0, min(5, conv["misalignment"]))

        # Update silos
        for name, silo in self.silos.items():
            silo["level_pct"] += random.uniform(-0.5, 0.5)
            silo["level_pct"] = max(10, min(95, silo["level_pct"]))
            silo["weight_t"] = (silo["level_pct"] / 100) * 2500 + random.uniform(-10, 10)
            silo["temp_grain_c"] += random.uniform(-0.2, 0.2)
            silo["temp_grain_c"] = max(10, min(30, silo["temp_grain_c"]))
            silo["humidity_pct"] += random.uniform(-0.1, 0.1)
            silo["humidity_pct"] = max(11, min(17, silo["humidity_pct"]))
            silo["pressure_pa"] = 100 + (silo["level_pct"] / 100) * 400 + random.uniform(-10, 10)

        # Update elevators
        for name, elev in self.elevators.items():
            if elev["running"]:
                elev["bucket_speed_mps"] += random.uniform(-0.02, 0.02)
                elev["bucket_speed_mps"] = max(1.2, min(1.8, elev["bucket_speed_mps"]))
                elev["current_a"] = 25 + random.uniform(-3, 3)
                elev["power_kw"] = elev["current_a"] * 1.05 + random.uniform(-1, 1)
                elev["temp_c"] += random.uniform(-0.5, 0.5)
                elev["temp_c"] = max(40, min(60, elev["temp_c"]))

        # Update shiploader
        self.shiploader["flow_tph"] = self.shiploader["setpoint_tph"] * 0.95 + random.uniform(-50, 50)
        self.shiploader["power_kw"] = 70 + (self.shiploader["flow_tph"] / 1500) * 30 + random.uniform(-2, 2)
        self.shiploader["current_a"] = self.shiploader["power_kw"] * 1.4 + random.uniform(-3, 3)

        # Build motor loads for eletrocentro
        motor_loads = {
            "CORR01": self.conveyors["CORR01"]["load_pct"],
            "CORR02": self.conveyors["CORR02"]["load_pct"],
            "CORR03": self.conveyors["CORR03"]["load_pct"],
            "SLD01": (self.shiploader["flow_tph"] / 1500) * 100,
            "SLD02": 40 + (self.shiploader["flow_tph"] / 1500) * 30,
            "ELV01": 60 if self.running else 0,
            "VNT01": 80 if self.running else 0,
            "VNT02": 75 if self.running else 0,
        }

        # Update eletrocentro
        self.eletrocentro.update(motor_loads, 1.0)

        # Update energy from eletrocentro
        self.energy["grid_power_kw"] = self.eletrocentro.transformer["power_kw"]
        self.energy["total_energy_kwh"] = self.eletrocentro.total_energy_kwh
        self.energy["power_factor"] = self.eletrocentro.transformer["pf"]
        self.energy["grid_voltage_v"] = 480 + random.uniform(-3, 3)



# Boolean tags that need special handling
BOOLEAN_TAGS = {
    "RUNNING", "BREAKER", "CONTACTOR", "FAULT", "TRIP",
    "FN50", "FN51", "FN49", "ALARM_OVERTEMP", "ALARM_OVERLOAD"
}

def is_boolean_tag(tag_name: str) -> bool:
    """Check if a tag should be boolean type"""
    return any(bt in tag_name for bt in BOOLEAN_TAGS)


async def main():
    """Main OPC UA server"""
    logger.info("=" * 70)
    logger.info("  🚀 OptiFlow OPC UA Simulator - Grain Terminal + Eletrocentro")
    logger.info("=" * 70)

    # Create simulator
    simulator = GrainTerminalSimulator()
    simulator.initialize_equipment()

    # Create OPC UA server
    server = Server()
    await server.init()

    # Configure server
    server.set_endpoint("opc.tcp://0.0.0.0:4840/optiflow/terminal")
    server.set_server_name("OptiFlow Grain Terminal Simulator")
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    # Setup namespace
    uri = "http://optiflow.ai/grain-terminal"
    idx = await server.register_namespace(uri)

    logger.info(f"  Namespace: {uri}")
    logger.info(f"  Namespace Index: {idx}")
    logger.info(f"  Endpoint: opc.tcp://0.0.0.0:4840/optiflow/terminal")
    logger.info("=" * 70)

    objects = server.nodes.objects
    terminal = await objects.add_folder(idx, "GrainTerminal")

    # =========================================================================
    # PROCESS EQUIPMENT
    # =========================================================================

    # Conveyors folder
    conveyors_folder = await terminal.add_folder(idx, "Conveyors")
    conveyor_nodes = {}
    for name, data in simulator.conveyors.items():
        conv_folder = await conveyors_folder.add_folder(idx, name)
        conveyor_nodes[name] = {
            "running": await conv_folder.add_variable(idx, "running", data["running"]),
            "speed_mps": await conv_folder.add_variable(idx, "speed_mps", data["speed_mps"]),
            "load_pct": await conv_folder.add_variable(idx, "load_pct", data["load_pct"]),
            "current_a": await conv_folder.add_variable(idx, "current_a", data["current_a"]),
            "power_kw": await conv_folder.add_variable(idx, "power_kw", data["power_kw"]),
            "temp_c": await conv_folder.add_variable(idx, "temp_c", data["temp_c"]),
            "vibration_mms": await conv_folder.add_variable(idx, "vibration_mms", data["vibration_mms"]),
            "misalignment": await conv_folder.add_variable(idx, "misalignment", data["misalignment"]),
        }
        for var in conveyor_nodes[name].values():
            await var.set_writable()

    # Silos folder
    silos_folder = await terminal.add_folder(idx, "Silos")
    silo_nodes = {}
    for name, data in simulator.silos.items():
        silo_folder = await silos_folder.add_folder(idx, name)
        silo_nodes[name] = {
            "level_pct": await silo_folder.add_variable(idx, "level_pct", data["level_pct"]),
            "temp_grain_c": await silo_folder.add_variable(idx, "temp_grain_c", data["temp_grain_c"]),
            "humidity_pct": await silo_folder.add_variable(idx, "humidity_pct", data["humidity_pct"]),
            "weight_t": await silo_folder.add_variable(idx, "weight_t", data["weight_t"]),
            "pressure_pa": await silo_folder.add_variable(idx, "pressure_pa", data["pressure_pa"]),
        }
        for var in silo_nodes[name].values():
            await var.set_writable()

    # Elevators folder
    elevators_folder = await terminal.add_folder(idx, "Elevators")
    elevator_nodes = {}
    for name, data in simulator.elevators.items():
        elev_folder = await elevators_folder.add_folder(idx, name)
        elevator_nodes[name] = {
            "running": await elev_folder.add_variable(idx, "running", data["running"]),
            "bucket_speed_mps": await elev_folder.add_variable(idx, "bucket_speed_mps", data["bucket_speed_mps"]),
            "current_a": await elev_folder.add_variable(idx, "current_a", data["current_a"]),
            "power_kw": await elev_folder.add_variable(idx, "power_kw", data["power_kw"]),
            "temp_c": await elev_folder.add_variable(idx, "temp_c", data["temp_c"]),
        }
        for var in elevator_nodes[name].values():
            await var.set_writable()

    # Energy folder (basic - will be supplemented by Eletrocentro)
    energy_folder = await terminal.add_folder(idx, "Energy")
    energy_nodes = {
        "grid_power_kw": await energy_folder.add_variable(idx, "grid_power_kw", 0.0),
        "total_energy_kwh": await energy_folder.add_variable(idx, "total_energy_kwh", 0.0),
        "power_factor": await energy_folder.add_variable(idx, "power_factor", 0.0),
        "grid_voltage_v": await energy_folder.add_variable(idx, "grid_voltage_v", 0.0),
    }
    for var in energy_nodes.values():
        await var.set_writable()

    # =========================================================================
    # ELETROCENTRO - Complete Electrical System
    # =========================================================================
    eletro_folder = await terminal.add_folder(idx, "Eletrocentro")
    eletro_nodes = {}

    async def add_typed_variable(folder, idx, tag_name: str, prefix: str = ""):
        """Add variable with correct type based on tag name"""
        full_name = f"{prefix}_{tag_name}_PV" if prefix else f"{tag_name}_PV"
        if is_boolean_tag(tag_name):
            var = await folder.add_variable(idx, tag_name, False)
        else:
            var = await folder.add_variable(idx, tag_name, 0.0)
        await var.set_writable()
        return var, full_name

    # --- Transformer TR01 ---
    tr_folder = await eletro_folder.add_folder(idx, "TR01")
    tr_tags = ["LOAD_PCT", "POWER_KW", "POWER_KVAR", "POWER_KVA", "PF",
               "CURRENT_PRI_A", "CURRENT_SEC_A", "TEMP_WINDING_C", "TEMP_OIL_C",
               "ALARM_OVERTEMP", "ALARM_OVERLOAD"]
    for tag in tr_tags:
        var, full_name = await add_typed_variable(tr_folder, idx, tag, "TR01")
        eletro_nodes[full_name] = var

    # --- CCM01 ---
    ccm_folder = await eletro_folder.add_folder(idx, "CCM01")

    for equip in simulator.eletrocentro.ccm_equipment:
        eq_folder = await ccm_folder.add_folder(idx, equip)
        prefix = f"CCM01_{equip}"

        # Basic tags
        basic_tags = ["RUNNING", "BREAKER", "CONTACTOR", "CURRENT_A", "POWER_KW", "POWER_KVAR"]
        for tag in basic_tags:
            var, full_name = await add_typed_variable(eq_folder, idx, tag, prefix)
            eletro_nodes[full_name] = var

        # Softstart subfolder
        ss_folder = await eq_folder.add_folder(idx, "Softstart")
        ss_tags = ["STATE", "VOLTAGE_PCT", "MOTOR_TEMP_PCT", "FAULT"]
        for tag in ss_tags:
            var, full_name = await add_typed_variable(ss_folder, idx, tag, f"{prefix}_SS")
            eletro_nodes[full_name] = var

        # VFD subfolder
        vfd_folder = await eq_folder.add_folder(idx, "VFD")
        vfd_tags = ["STATE", "FREQ_HZ", "VOLTAGE_V", "SPEED_RPM", "TORQUE_PCT",
                   "DC_BUS_V", "TEMP_C", "ENERGY_KWH", "FAULT"]
        for tag in vfd_tags:
            var, full_name = await add_typed_variable(vfd_folder, idx, tag, f"{prefix}_VFD")
            eletro_nodes[full_name] = var

        # Relay subfolder
        rel_folder = await eq_folder.add_folder(idx, "Relay")
        rel_tags = ["STATE", "THERMAL_PCT", "FN50", "FN51", "FN49", "TRIP"]
        for tag in rel_tags:
            var, full_name = await add_typed_variable(rel_folder, idx, tag, f"{prefix}_REL")
            eletro_nodes[full_name] = var

        # PowerMeter subfolder
        pm_folder = await eq_folder.add_folder(idx, "PowerMeter")
        pm_tags = ["V_AB", "V_BC", "V_CA", "I_A", "I_B", "I_C", "FREQ_HZ", "PF", "KWH"]
        for tag in pm_tags:
            var, full_name = await add_typed_variable(pm_folder, idx, tag, f"{prefix}_PM")
            eletro_nodes[full_name] = var

    # --- Sector Power Meters ---
    meters_folder = await eletro_folder.add_folder(idx, "PowerMeters")

    for meter_name in ["PM_GERAL", "PM_CCM01", "PM_ILUM"]:
        m_folder = await meters_folder.add_folder(idx, meter_name)
        meter_tags = ["V_AB", "V_BC", "V_CA", "V_AN", "V_BN", "V_CN",
                     "I_A", "I_B", "I_C", "I_N",
                     "KW", "KVAR", "KVA", "PF", "FREQ_HZ",
                     "KWH", "KVARH",
                     "THD_V_PCT", "THD_I_PCT",
                     "DEMAND_KW", "DEMAND_MAX_KW"]
        for tag in meter_tags:
            var, full_name = await add_typed_variable(m_folder, idx, tag, meter_name)
            eletro_nodes[full_name] = var

    # --- Capacitor Bank BC01 ---
    bc_folder = await eletro_folder.add_folder(idx, "BC01")
    bc_tags = ["STAGES_ON", "STAGES_TOTAL", "KVAR", "CURRENT_A", "TEMP_C"]
    for tag in bc_tags:
        var, full_name = await add_typed_variable(bc_folder, idx, tag, "BC01")
        eletro_nodes[full_name] = var

    # --- Main Relay ---
    rel_geral_folder = await eletro_folder.add_folder(idx, "REL_GERAL")
    rel_geral_tags = ["STATE", "THERMAL_PCT", "TRIP", "TRIP_COUNT"]
    for tag in rel_geral_tags:
        var, full_name = await add_typed_variable(rel_geral_folder, idx, tag, "REL_GERAL")
        eletro_nodes[full_name] = var

    # --- Totals ---
    totals_folder = await eletro_folder.add_folder(idx, "Totals")
    total_tags = ["TOTAL_KWH", "TOTAL_KVARH", "PEAK_DEMAND_KW", "TIME_S"]
    for tag in total_tags:
        var, full_name = await add_typed_variable(totals_folder, idx, tag, "ELETRO")
        eletro_nodes[full_name] = var

    # Count total tags
    process_tags = sum(len(n) for n in [conveyor_nodes, silo_nodes, elevator_nodes]) * 8 + len(energy_nodes)
    eletro_tag_count = len(eletro_nodes)

    logger.info("\n📊 Equipment Summary:")
    logger.info(f"  Conveyors: {len(simulator.conveyors)}")
    logger.info(f"  Silos: {len(simulator.silos)}")
    logger.info(f"  Elevators: {len(simulator.elevators)}")
    logger.info(f"  Process Tags: ~{process_tags}")
    logger.info(f"  ⚡ Eletrocentro Tags: {eletro_tag_count}")
    logger.info(f"  Total Tags: ~{process_tags + eletro_tag_count}")

    # Start server
    async with server:
        logger.info("\n" + "=" * 70)
        logger.info("  ✅ OPC UA Server Started Successfully")
        logger.info("  📡 Clients can connect to:")
        logger.info("     opc.tcp://opcua-server:4840/optiflow/terminal")
        logger.info("  Press Ctrl+C to stop")
        logger.info("=" * 70 + "\n")

        update_count = 0
        while True:
            try:
                # Update simulation
                simulator.update_simulation()

                # Update process OPC UA nodes
                for name, data in simulator.conveyors.items():
                    for key, val in data.items():
                        if key == "running":
                            await conveyor_nodes[name][key].write_value(bool(val))
                        else:
                            await conveyor_nodes[name][key].write_value(float(val))

                for name, data in simulator.silos.items():
                    for key, val in data.items():
                        await silo_nodes[name][key].write_value(float(val))

                for name, data in simulator.elevators.items():
                    for key, val in data.items():
                        if key == "running":
                            await elevator_nodes[name][key].write_value(bool(val))
                        else:
                            await elevator_nodes[name][key].write_value(float(val))

                # Update energy nodes
                await energy_nodes["grid_power_kw"].write_value(float(simulator.energy["grid_power_kw"]))
                await energy_nodes["total_energy_kwh"].write_value(float(simulator.energy["total_energy_kwh"]))
                await energy_nodes["power_factor"].write_value(float(simulator.energy["power_factor"]))
                await energy_nodes["grid_voltage_v"].write_value(float(simulator.energy["grid_voltage_v"]))

                # Update Eletrocentro nodes
                eletro_tags = simulator.eletrocentro.get_all_tags()
                for tag_name, value in eletro_tags.items():
                    if tag_name in eletro_nodes:
                        # Check if tag should be boolean based on its name
                        if is_boolean_tag(tag_name):
                            await eletro_nodes[tag_name].write_value(bool(value))
                        else:
                            await eletro_nodes[tag_name].write_value(float(value))

                update_count += 1
                if update_count % 10 == 0:
                    tr = simulator.eletrocentro.transformer
                    logger.info(
                        f"📊 Update #{update_count} | "
                        f"TR01: {tr['power_kw']:.0f}kW @ {tr['load_pct']:.0f}% | "
                        f"PF: {tr['pf']:.2f} | "
                        f"Energy: {simulator.eletrocentro.total_energy_kwh:.1f}kWh"
                    )

                await asyncio.sleep(1)

            except KeyboardInterrupt:
                logger.info("\n🛑 Shutting down server...")
                break
            except Exception as e:
                logger.error(f"❌ Error in simulation loop: {e}", exc_info=True)
                await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
