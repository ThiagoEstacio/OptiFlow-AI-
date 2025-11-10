"""
Failure Models - Specific failure types per equipment

Each model implements realistic failure modes:
- Progressive failures (grow over time)
- Sudden failures (catastrophic)
- Conditional failures (triggered by specific conditions)

Equipment types:
- Belts: tear, misalignment, splice failure
- Bearings: wear, seizure, lubrication failure
- Motors: winding burnout, fan failure, starter failure
- Sensors: drift, noise, total failure
"""

import numpy as np
import logging
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# FAILURE TYPES
# ============================================================================

class BeltFailureType(Enum):
    """Types of belt failures"""
    NONE = "none"
    TEAR = "tear"  # Progressive tearing
    MISALIGNMENT = "misalignment"  # Lateral drift
    SPLICE_FAILURE = "splice_failure"  # Belt splice coming apart
    ROLLER_SEIZED = "roller_seized"  # Idler roller stuck


class BearingFailureType(Enum):
    """Types of bearing failures"""
    NONE = "none"
    WEAR = "wear"  # Progressive wear
    SEIZURE = "seizure"  # Sudden lock-up
    LUBRICATION = "lubrication"  # Oil degradation
    CONTAMINATION = "contamination"  # Particles in bearing


class MotorFailureType(Enum):
    """Types of motor failures"""
    NONE = "none"
    WINDING_BURNOUT = "winding_burnout"  # Coil overheating
    FAN_FAILURE = "fan_failure"  # Cooling fan broken
    STARTER_FAILURE = "starter_failure"  # Won't start
    INSULATION = "insulation"  # Insulation breakdown


class SensorFailureType(Enum):
    """Types of sensor failures"""
    NONE = "none"
    DRIFT = "drift"  # Gradual calibration drift
    NOISE = "noise"  # High electrical noise
    TOTAL_FAILURE = "total_failure"  # Sensor dead
    STUCK = "stuck"  # Reading frozen


# ============================================================================
# BELT FAILURE MODEL
# ============================================================================

@dataclass
class BeltFailureState:
    """State of belt failures"""
    failure_type: BeltFailureType = BeltFailureType.NONE

    # Tear parameters
    tear_severity_pct: float = 0.0  # 0-100%, 100% = complete tear
    tear_growth_rate: float = 0.5  # %/minute when active

    # Misalignment parameters
    misalignment_mm: float = 0.0  # Lateral offset in mm
    misalignment_rate: float = 0.3  # mm/minute when active
    max_misalignment_mm: float = 50.0  # Maximum before trip

    # Splice parameters
    splice_integrity_pct: float = 100.0  # 100% = perfect
    splice_degradation_rate: float = 0.1  # %/hour of operation

    # Roller seized flag
    roller_seized: bool = False
    seized_roller_index: int = -1  # Which roller (0-N)


class BeltFailureModel:
    """
    Belt conveyor failure model

    Failures:
    1. TEAR - Progressive tearing starting small and growing
    2. MISALIGNMENT - Belt drifts laterally causing edge damage
    3. SPLICE_FAILURE - Belt splice deteriorates over cycles
    4. ROLLER_SEIZED - Idler roller bearing locks up
    """

    def __init__(self):
        self.rng = np.random.default_rng()

    def initialize_failure(self,
                          failure_type: BeltFailureType,
                          state: BeltFailureState) -> None:
        """
        Initialize a new failure with random parameters

        Args:
            failure_type: Type of failure to initialize
            state: Belt failure state to modify
        """
        state.failure_type = failure_type

        if failure_type == BeltFailureType.TEAR:
            # Tear starts small (5-15%)
            state.tear_severity_pct = self.rng.uniform(5.0, 15.0)
            state.tear_growth_rate = self.rng.uniform(0.3, 0.8)  # %/min
            logger.warning(
                f"🔴 BELT TEAR initiated: {state.tear_severity_pct:.1f}% "
                f"(growth: {state.tear_growth_rate:.2f}%/min)"
            )

        elif failure_type == BeltFailureType.MISALIGNMENT:
            # Misalignment starts at 5-10mm
            state.misalignment_mm = self.rng.uniform(5.0, 10.0)
            state.misalignment_rate = self.rng.uniform(0.2, 0.5)  # mm/min
            logger.warning(
                f"🔴 BELT MISALIGNMENT initiated: {state.misalignment_mm:.1f}mm "
                f"(rate: {state.misalignment_rate:.2f}mm/min)"
            )

        elif failure_type == BeltFailureType.SPLICE_FAILURE:
            # Splice starts degraded (70-90%)
            state.splice_integrity_pct = self.rng.uniform(70.0, 90.0)
            state.splice_degradation_rate = self.rng.uniform(0.05, 0.2)  # %/hour
            logger.warning(
                f"🔴 SPLICE FAILURE initiated: {state.splice_integrity_pct:.1f}% integrity "
                f"(degradation: {state.splice_degradation_rate:.2f}%/h)"
            )

        elif failure_type == BeltFailureType.ROLLER_SEIZED:
            state.roller_seized = True
            state.seized_roller_index = self.rng.integers(0, 20)  # Assume 20 rollers
            logger.warning(
                f"🔴 ROLLER SEIZED: roller #{state.seized_roller_index}"
            )

    def update_failure(self,
                       state: BeltFailureState,
                       dt_seconds: float,
                       running: bool) -> Dict:
        """
        Update failure progression over time

        Args:
            state: Current failure state
            dt_seconds: Time step
            running: Is belt running?

        Returns:
            Dict with effects on belt operation
        """
        effects = {
            'friction_multiplier': 1.0,  # Increased resistance
            'efficiency_multiplier': 1.0,  # Reduced throughput
            'vibration_increase': 0.0,  # mm/s added
            'should_trip': False  # Emergency stop
        }

        if state.failure_type == BeltFailureType.NONE:
            return effects

        # Only progress failures when running
        if not running:
            return effects

        dt_minutes = dt_seconds / 60.0
        dt_hours = dt_seconds / 3600.0

        # === TEAR PROGRESSION ===
        if state.failure_type == BeltFailureType.TEAR:
            # Tear grows over time
            state.tear_severity_pct += state.tear_growth_rate * dt_minutes

            # Effects of tearing
            severity_factor = state.tear_severity_pct / 100.0
            effects['efficiency_multiplier'] = 1.0 - (0.5 * severity_factor)  # Up to 50% loss
            effects['vibration_increase'] = 2.0 * severity_factor  # Up to +2 mm/s

            # Trip if tear > 80%
            if state.tear_severity_pct >= 80.0:
                effects['should_trip'] = True
                logger.error(
                    f"💥 BELT TORN: {state.tear_severity_pct:.1f}% - EMERGENCY STOP"
                )

        # === MISALIGNMENT PROGRESSION ===
        elif state.failure_type == BeltFailureType.MISALIGNMENT:
            # Misalignment increases
            state.misalignment_mm += state.misalignment_rate * dt_minutes

            # Effects
            misalign_factor = state.misalignment_mm / state.max_misalignment_mm
            effects['friction_multiplier'] = 1.0 + (0.5 * misalign_factor)  # Up to +50% friction
            effects['vibration_increase'] = 1.5 * misalign_factor

            # Trip if beyond limit
            if state.misalignment_mm >= state.max_misalignment_mm:
                effects['should_trip'] = True
                logger.error(
                    f"💥 BELT MISALIGNED: {state.misalignment_mm:.1f}mm - EMERGENCY STOP"
                )

        # === SPLICE DEGRADATION ===
        elif state.failure_type == BeltFailureType.SPLICE_FAILURE:
            # Splice weakens
            state.splice_integrity_pct -= state.splice_degradation_rate * dt_hours

            # Effects
            integrity_factor = state.splice_integrity_pct / 100.0
            effects['efficiency_multiplier'] = integrity_factor  # Direct correlation
            effects['vibration_increase'] = (1.0 - integrity_factor) * 3.0  # Up to +3 mm/s

            # Trip if splice < 30%
            if state.splice_integrity_pct <= 30.0:
                effects['should_trip'] = True
                logger.error(
                    f"💥 SPLICE FAILED: {state.splice_integrity_pct:.1f}% - EMERGENCY STOP"
                )

        # === ROLLER SEIZED ===
        elif state.failure_type == BeltFailureType.ROLLER_SEIZED:
            # Immediate effects
            effects['friction_multiplier'] = 1.8  # 80% more friction
            effects['vibration_increase'] = 4.0  # Significant vibration

            # Should trip immediately
            effects['should_trip'] = True
            logger.error(
                f"💥 ROLLER SEIZED: #{state.seized_roller_index} - EMERGENCY STOP"
            )

        return effects


# ============================================================================
# BEARING FAILURE MODEL
# ============================================================================

@dataclass
class BearingFailureState:
    """State of bearing failures"""
    failure_type: BearingFailureType = BearingFailureType.NONE

    # Wear parameters
    wear_pct: float = 0.0  # 0-100%
    wear_rate: float = 0.05  # %/hour

    # Seizure flag
    seized: bool = False

    # Lubrication
    oil_quality_pct: float = 100.0
    oil_degradation_rate: float = 0.02  # %/hour

    # Contamination
    contamination_ppm: float = 0.0  # Parts per million
    contamination_rate: float = 1.0  # ppm/hour


class BearingFailureModel:
    """
    Bearing failure model

    Failures:
    1. WEAR - Progressive surface damage
    2. SEIZURE - Sudden lock-up (often from lubrication loss)
    3. LUBRICATION - Oil quality degrades
    4. CONTAMINATION - Particles damage surfaces
    """

    def __init__(self):
        self.rng = np.random.default_rng()

    def initialize_failure(self,
                          failure_type: BearingFailureType,
                          state: BearingFailureState) -> None:
        """Initialize bearing failure"""
        state.failure_type = failure_type

        if failure_type == BearingFailureType.WEAR:
            state.wear_pct = self.rng.uniform(30.0, 50.0)
            state.wear_rate = self.rng.uniform(0.03, 0.08)
            logger.warning(
                f"🔴 BEARING WEAR initiated: {state.wear_pct:.1f}% "
                f"(rate: {state.wear_rate:.3f}%/h)"
            )

        elif failure_type == BearingFailureType.SEIZURE:
            state.seized = True
            logger.warning("🔴 BEARING SEIZURE - IMMEDIATE FAILURE")

        elif failure_type == BearingFailureType.LUBRICATION:
            state.oil_quality_pct = self.rng.uniform(40.0, 60.0)
            state.oil_degradation_rate = self.rng.uniform(0.01, 0.05)
            logger.warning(
                f"🔴 LUBRICATION FAILURE: {state.oil_quality_pct:.1f}% quality"
            )

        elif failure_type == BearingFailureType.CONTAMINATION:
            state.contamination_ppm = self.rng.uniform(100.0, 300.0)
            state.contamination_rate = self.rng.uniform(0.5, 2.0)
            logger.warning(
                f"🔴 BEARING CONTAMINATION: {state.contamination_ppm:.1f} ppm"
            )

    def update_failure(self,
                       state: BearingFailureState,
                       dt_seconds: float,
                       running: bool,
                       load_factor: float = 1.0) -> Dict:
        """Update bearing failure progression"""
        effects = {
            'temperature_increase_C': 0.0,
            'vibration_multiplier': 1.0,
            'friction_increase': 0.0,
            'should_trip': False
        }

        if state.failure_type == BearingFailureType.NONE:
            return effects

        if not running:
            return effects

        dt_hours = dt_seconds / 3600.0

        # === WEAR ===
        if state.failure_type == BearingFailureType.WEAR:
            # Wear accelerates with load
            state.wear_pct += state.wear_rate * dt_hours * load_factor

            # Effects
            wear_factor = state.wear_pct / 100.0
            effects['vibration_multiplier'] = 1.0 + (4.0 * wear_factor)  # Up to 5x vibration
            effects['temperature_increase_C'] = 20.0 * wear_factor  # Up to +20°C

            # Trip if > 90% worn
            if state.wear_pct >= 90.0:
                effects['should_trip'] = True
                logger.error(f"💥 BEARING WORN OUT: {state.wear_pct:.1f}%")

        # === SEIZURE ===
        elif state.failure_type == BearingFailureType.SEIZURE:
            effects['should_trip'] = True
            effects['temperature_increase_C'] = 50.0  # Immediate overheating
            effects['vibration_multiplier'] = 10.0  # Massive vibration
            logger.error("💥 BEARING SEIZED")

        # === LUBRICATION ===
        elif state.failure_type == BearingFailureType.LUBRICATION:
            # Oil degrades faster at high load
            state.oil_quality_pct -= state.oil_degradation_rate * dt_hours * (1.0 + load_factor * 0.5)

            # Effects worsen as oil quality drops
            oil_factor = 1.0 - (state.oil_quality_pct / 100.0)
            effects['temperature_increase_C'] = 15.0 * oil_factor
            effects['friction_increase'] = 0.3 * oil_factor

            # If oil very poor, risk seizure
            if state.oil_quality_pct <= 10.0:
                effects['should_trip'] = True
                logger.error(f"💥 LUBRICATION CRITICAL: {state.oil_quality_pct:.1f}%")

        # === CONTAMINATION ===
        elif state.failure_type == BearingFailureType.CONTAMINATION:
            # Contamination increases
            state.contamination_ppm += state.contamination_rate * dt_hours

            # Effects
            contam_factor = min(state.contamination_ppm / 1000.0, 1.0)  # Cap at 1000ppm
            effects['wear_rate_multiplier'] = 1.0 + (2.0 * contam_factor)  # Accelerates wear
            effects['vibration_multiplier'] = 1.0 + (1.5 * contam_factor)

            if state.contamination_ppm >= 800.0:
                effects['should_trip'] = True
                logger.error(f"💥 CONTAMINATION CRITICAL: {state.contamination_ppm:.0f} ppm")

        return effects


# ============================================================================
# MOTOR FAILURE MODEL
# ============================================================================

@dataclass
class MotorFailureState:
    """State of motor failures"""
    failure_type: MotorFailureType = MotorFailureType.NONE

    # Winding burnout
    insulation_pct: float = 100.0
    insulation_degradation_rate: float = 0.01  # %/hour at rated temp

    # Fan failure
    fan_broken: bool = False
    cooling_efficiency_pct: float = 100.0

    # Starter failure
    starter_failed: bool = False
    start_success_probability: float = 1.0  # 0-1


class MotorFailureModel:
    """
    Motor failure model

    Failures:
    1. WINDING_BURNOUT - Insulation breaks down from overheating
    2. FAN_FAILURE - Cooling fan stops working
    3. STARTER_FAILURE - Motor won't start reliably
    4. INSULATION - Electrical insulation degradation
    """

    def __init__(self):
        self.rng = np.random.default_rng()

    def initialize_failure(self,
                          failure_type: MotorFailureType,
                          state: MotorFailureState) -> None:
        """Initialize motor failure"""
        state.failure_type = failure_type

        if failure_type == MotorFailureType.WINDING_BURNOUT:
            state.insulation_pct = self.rng.uniform(40.0, 70.0)
            logger.warning(f"🔴 WINDING BURNOUT initiated: {state.insulation_pct:.1f}% insulation")

        elif failure_type == MotorFailureType.FAN_FAILURE:
            state.fan_broken = True
            state.cooling_efficiency_pct = self.rng.uniform(10.0, 30.0)  # Reduced cooling
            logger.warning(f"🔴 FAN FAILURE: {state.cooling_efficiency_pct:.1f}% cooling")

        elif failure_type == MotorFailureType.STARTER_FAILURE:
            state.starter_failed = True
            state.start_success_probability = self.rng.uniform(0.3, 0.7)
            logger.warning(f"🔴 STARTER FAILURE: {state.start_success_probability*100:.0f}% success rate")

        elif failure_type == MotorFailureType.INSULATION:
            state.insulation_pct = self.rng.uniform(50.0, 80.0)
            state.insulation_degradation_rate = self.rng.uniform(0.02, 0.05)
            logger.warning(f"🔴 INSULATION DEGRADATION: {state.insulation_pct:.1f}%")

    def update_failure(self,
                       state: MotorFailureState,
                       dt_seconds: float,
                       running: bool,
                       temperature_C: float) -> Dict:
        """Update motor failure progression"""
        effects = {
            'cooling_multiplier': 1.0,
            'current_multiplier': 1.0,
            'can_start': True,
            'should_trip': False
        }

        if state.failure_type == MotorFailureType.NONE:
            return effects

        dt_hours = dt_seconds / 3600.0

        # === FAN FAILURE ===
        if state.failure_type == MotorFailureType.FAN_FAILURE:
            effects['cooling_multiplier'] = state.cooling_efficiency_pct / 100.0
            # Temperature rises faster without cooling

        # === WINDING BURNOUT / INSULATION ===
        if state.failure_type in [MotorFailureType.WINDING_BURNOUT, MotorFailureType.INSULATION]:
            # Insulation degrades faster at high temperature
            temp_factor = max(0, (temperature_C - 85.0) / 20.0)  # Accelerates above 85°C
            state.insulation_pct -= state.insulation_degradation_rate * dt_hours * (1.0 + temp_factor)

            # Effects
            insulation_factor = state.insulation_pct / 100.0
            effects['current_multiplier'] = 1.0 + (0.3 * (1.0 - insulation_factor))  # Higher current draw

            # Trip if insulation < 20%
            if state.insulation_pct <= 20.0:
                effects['should_trip'] = True
                logger.error(f"💥 MOTOR BURNOUT: insulation {state.insulation_pct:.1f}%")

        # === STARTER FAILURE ===
        if state.failure_type == MotorFailureType.STARTER_FAILURE:
            # Check if start attempt succeeds
            if not running:
                roll = self.rng.random()
                effects['can_start'] = roll < state.start_success_probability
                if not effects['can_start']:
                    logger.warning("⚠️ MOTOR START FAILED")

        return effects


# ============================================================================
# SENSOR FAILURE MODEL
# ============================================================================

@dataclass
class SensorFailureState:
    """State of sensor failures"""
    failure_type: SensorFailureType = SensorFailureType.NONE

    # Drift
    drift_offset: float = 0.0  # Calibration offset
    drift_rate: float = 0.01  # Units/hour

    # Noise
    noise_amplitude: float = 0.0  # Sigma of Gaussian noise

    # Total failure
    failed: bool = False
    stuck_value: Optional[float] = None


class SensorFailureModel:
    """
    Sensor failure model

    Failures:
    1. DRIFT - Gradual calibration error
    2. NOISE - High electrical noise
    3. TOTAL_FAILURE - Sensor stops responding
    4. STUCK - Reading freezes at one value
    """

    def __init__(self):
        self.rng = np.random.default_rng()

    def initialize_failure(self,
                          failure_type: SensorFailureType,
                          state: SensorFailureState,
                          current_value: float) -> None:
        """Initialize sensor failure"""
        state.failure_type = failure_type

        if failure_type == SensorFailureType.DRIFT:
            state.drift_offset = self.rng.uniform(-2.0, 2.0)
            state.drift_rate = self.rng.uniform(0.005, 0.02)
            logger.warning(f"🔴 SENSOR DRIFT: offset={state.drift_offset:.2f}, rate={state.drift_rate:.3f}")

        elif failure_type == SensorFailureType.NOISE:
            state.noise_amplitude = self.rng.uniform(0.5, 3.0)
            logger.warning(f"🔴 SENSOR NOISE: amplitude={state.noise_amplitude:.2f}")

        elif failure_type == SensorFailureType.TOTAL_FAILURE:
            state.failed = True
            logger.warning("🔴 SENSOR FAILED - NO READING")

        elif failure_type == SensorFailureType.STUCK:
            state.failed = True
            state.stuck_value = current_value
            logger.warning(f"🔴 SENSOR STUCK at {current_value:.2f}")

    def apply_failure(self,
                      state: SensorFailureState,
                      true_value: float,
                      dt_seconds: float) -> float:
        """
        Apply sensor failure to reading

        Args:
            state: Sensor failure state
            true_value: Actual physical value
            dt_seconds: Time step

        Returns:
            Corrupted sensor reading
        """
        if state.failure_type == SensorFailureType.NONE:
            return true_value

        # === DRIFT ===
        if state.failure_type == SensorFailureType.DRIFT:
            # Drift grows over time
            dt_hours = dt_seconds / 3600.0
            state.drift_offset += state.drift_rate * dt_hours
            return true_value + state.drift_offset

        # === NOISE ===
        elif state.failure_type == SensorFailureType.NOISE:
            noise = self.rng.normal(0, state.noise_amplitude)
            return true_value + noise

        # === TOTAL FAILURE ===
        elif state.failure_type == SensorFailureType.TOTAL_FAILURE:
            return 0.0  # Sensor reads zero

        # === STUCK ===
        elif state.failure_type == SensorFailureType.STUCK:
            return state.stuck_value

        return true_value


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Testing Belt Failure Model ===")
    belt_model = BeltFailureModel()
    belt_state = BeltFailureState()

    # Initialize a tear
    belt_model.initialize_failure(BeltFailureType.TEAR, belt_state)

    # Simulate 60 minutes
    for minute in range(60):
        effects = belt_model.update_failure(belt_state, 60.0, running=True)
        if minute % 10 == 0:
            print(f"Minute {minute}: tear={belt_state.tear_severity_pct:.1f}%, "
                  f"efficiency={effects['efficiency_multiplier']:.2f}")
        if effects['should_trip']:
            print("TRIP!")
            break
