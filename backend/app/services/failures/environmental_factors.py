"""
Environmental Factors - How environment affects equipment degradation

Models the impact of:
- Temperature (ambient and equipment)
- Humidity and precipitation
- Dust and particulate matter
- Operating hours and duty cycle

These factors multiply the base failure rate and degradation rate.
"""

import numpy as np
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class WeatherCondition(Enum):
    """Weather conditions"""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"
    STRONG_WIND = "strong_wind"


@dataclass
class EnvironmentalConditions:
    """Current environmental conditions"""
    # Temperature
    ambient_temp_C: float = 25.0  # Ambient temperature
    equipment_temp_C: float = 40.0  # Equipment operating temperature

    # Humidity
    humidity_pct: float = 60.0  # Relative humidity 0-100%
    weather: WeatherCondition = WeatherCondition.CLEAR

    # Air quality
    dust_level_ppm: float = 50.0  # Particulate matter concentration

    # Operating conditions
    hours_continuous_operation: float = 0.0  # Hours running without stop
    starts_today: int = 0  # Number of start/stop cycles today
    overload_events_today: int = 0  # Number of overload events


class EnvironmentalFactors:
    """
    Calculate stress multipliers based on environmental conditions

    Higher multiplier = faster degradation / higher failure probability
    Normal conditions = 1.0x
    Harsh conditions = 1.5x - 3.0x
    """

    def __init__(self):
        self.rng = np.random.default_rng()

        # Thresholds for environmental severity
        self.TEMP_NOMINAL_C = 25.0
        self.TEMP_HIGH_C = 35.0
        self.TEMP_EXTREME_C = 45.0

        self.HUMIDITY_HIGH = 80.0
        self.HUMIDITY_EXTREME = 95.0

        self.DUST_NORMAL = 100.0  # ppm
        self.DUST_HIGH = 300.0
        self.DUST_EXTREME = 500.0

    def calculate_temperature_factor(self, temp_C: float, equipment_type: str = "general") -> float:
        """
        Temperature stress multiplier

        High temperatures accelerate:
        - Chemical reactions (oxidation, corrosion)
        - Material fatigue
        - Lubrication breakdown
        - Electrical insulation degradation

        Arrhenius equation approximation:
        For every 10°C increase, degradation rate roughly doubles

        Args:
            temp_C: Temperature in Celsius
            equipment_type: "electrical", "mechanical", "general"

        Returns:
            Stress multiplier (>1.0 means faster degradation)
        """
        if temp_C <= self.TEMP_NOMINAL_C:
            return 1.0  # No additional stress

        # Calculate excess temperature
        delta_T = temp_C - self.TEMP_NOMINAL_C

        # Arrhenius-like: factor = 2^(delta_T / 10)
        # So +10°C → 2x, +20°C → 4x, +30°C → 8x
        base_factor = 2.0 ** (delta_T / 10.0)

        # Equipment-specific multipliers
        if equipment_type == "electrical":
            # Electrical insulation very sensitive to temp
            factor = base_factor * 1.2
        elif equipment_type == "mechanical":
            # Mechanical wear also temperature sensitive
            factor = base_factor * 1.0
        else:
            factor = base_factor

        # Cap at 5x to avoid unrealistic values
        return min(factor, 5.0)

    def calculate_humidity_factor(self,
                                   humidity_pct: float,
                                   weather: WeatherCondition) -> float:
        """
        Humidity and precipitation stress multiplier

        High humidity causes:
        - Corrosion of metal parts
        - Mold growth in electrical components
        - Reduced electrical insulation
        - Accelerated chemical reactions

        Rain adds:
        - Direct water ingress risk
        - Increased corrosion rate
        - Electrical short-circuit risk

        Args:
            humidity_pct: Relative humidity 0-100%
            weather: Current weather condition

        Returns:
            Stress multiplier
        """
        factor = 1.0

        # Base humidity factor
        if humidity_pct < 60.0:
            # Low humidity is good
            factor = 1.0
        elif humidity_pct < self.HUMIDITY_HIGH:
            # Moderate humidity - slight increase
            factor = 1.0 + 0.01 * (humidity_pct - 60.0)  # Up to 1.2x at 80%
        elif humidity_pct < self.HUMIDITY_EXTREME:
            # High humidity - significant increase
            factor = 1.2 + 0.02 * (humidity_pct - 80.0)  # Up to 1.5x at 95%
        else:
            # Extreme humidity
            factor = 1.5 + 0.01 * (humidity_pct - 95.0)  # 1.5x+

        # Weather modifiers
        if weather == WeatherCondition.LIGHT_RAIN:
            factor *= 1.2  # 20% worse with light rain
        elif weather == WeatherCondition.HEAVY_RAIN:
            factor *= 1.5  # 50% worse with heavy rain
        elif weather == WeatherCondition.STRONG_WIND:
            factor *= 1.1  # Dust and debris

        return min(factor, 3.0)

    def calculate_dust_factor(self, dust_ppm: float, equipment_type: str = "general") -> float:
        """
        Dust and particulate matter stress multiplier

        Dust causes:
        - Abrasive wear on moving parts
        - Filter clogging (reduced cooling)
        - Electrical contact contamination
        - Bearing contamination
        - Sensor fouling

        Args:
            dust_ppm: Particulate matter concentration (ppm)
            equipment_type: "mechanical", "electrical", "sensors"

        Returns:
            Stress multiplier
        """
        if dust_ppm < self.DUST_NORMAL:
            return 1.0

        # Base dust factor
        if dust_ppm < self.DUST_HIGH:
            # Moderate dust
            factor = 1.0 + 0.002 * (dust_ppm - self.DUST_NORMAL)  # Up to 1.4x at 300ppm
        elif dust_ppm < self.DUST_EXTREME:
            # High dust
            factor = 1.4 + 0.003 * (dust_ppm - self.DUST_HIGH)  # Up to 2.0x at 500ppm
        else:
            # Extreme dust
            factor = 2.0 + 0.001 * (dust_ppm - self.DUST_EXTREME)  # 2.0x+

        # Equipment-specific sensitivity
        if equipment_type == "mechanical":
            # Bearings, gearboxes very sensitive
            factor *= 1.3
        elif equipment_type == "sensors":
            # Sensors get fouled easily
            factor *= 1.5
        elif equipment_type == "electrical":
            # Electrical less sensitive
            factor *= 0.9

        return min(factor, 4.0)

    def calculate_duty_cycle_factor(self,
                                     hours_continuous: float,
                                     starts_today: int,
                                     overload_events: int) -> float:
        """
        Operating duty cycle stress multiplier

        Harsh operating conditions:
        - Long continuous operation without rest → thermal fatigue
        - Frequent starts/stops → thermal cycling, mechanical shock
        - Overload events → stress concentration

        Args:
            hours_continuous: Hours of continuous operation
            starts_today: Number of start/stop cycles today
            overload_events: Number of overload events today

        Returns:
            Stress multiplier
        """
        factor = 1.0

        # Continuous operation stress
        # Equipment needs periodic stops for cooling
        if hours_continuous > 8.0:
            # After 8h, fatigue starts accumulating
            factor += 0.02 * (hours_continuous - 8.0)  # +2% per hour over 8h

        # Start/stop cycles
        # Each cycle causes thermal shock and mechanical transients
        if starts_today > 10:
            factor += 0.01 * (starts_today - 10)  # +1% per start over 10

        # Overload events
        # Each overload causes stress concentration
        if overload_events > 0:
            factor += 0.05 * overload_events  # +5% per overload

        return min(factor, 2.5)

    def calculate_combined_stress(self,
                                   conditions: EnvironmentalConditions,
                                   equipment_type: str = "general") -> Dict[str, float]:
        """
        Calculate all stress factors and combine them

        Args:
            conditions: Current environmental conditions
            equipment_type: Type of equipment

        Returns:
            Dictionary with individual and combined stress factors
        """
        # Individual factors
        temp_factor = self.calculate_temperature_factor(
            conditions.equipment_temp_C, equipment_type
        )

        humidity_factor = self.calculate_humidity_factor(
            conditions.humidity_pct, conditions.weather
        )

        dust_factor = self.calculate_dust_factor(
            conditions.dust_level_ppm, equipment_type
        )

        duty_factor = self.calculate_duty_cycle_factor(
            conditions.hours_continuous_operation,
            conditions.starts_today,
            conditions.overload_events_today
        )

        # Combined stress (multiplicative)
        # If all factors are 1.5x, combined = 1.5^4 = 5.06x
        # This can get very high, so we cap it
        combined = temp_factor * humidity_factor * dust_factor * duty_factor
        combined = min(combined, 10.0)  # Cap at 10x

        return {
            'temperature_factor': temp_factor,
            'humidity_factor': humidity_factor,
            'dust_factor': dust_factor,
            'duty_cycle_factor': duty_factor,
            'combined_stress': combined
        }

    def apply_corrosion(self,
                       health_pct: float,
                       conditions: EnvironmentalConditions,
                       dt_seconds: float) -> float:
        """
        Apply corrosion damage from humidity

        Corrosion is a chemical process that permanently damages equipment.
        It's most severe in high humidity + salt environments (coastal terminals).

        Args:
            health_pct: Current health percentage
            conditions: Environmental conditions
            dt_seconds: Time step

        Returns:
            Health degradation amount (positive value to subtract from health)
        """
        # Only corrode in high humidity or rain
        if conditions.humidity_pct < 70.0 and conditions.weather == WeatherCondition.CLEAR:
            return 0.0

        # Base corrosion rate (%/day)
        base_rate = 0.01  # 0.01% per day in ideal conditions

        # Humidity effect
        if conditions.humidity_pct >= self.HUMIDITY_EXTREME:
            humidity_multiplier = 3.0
        elif conditions.humidity_pct >= self.HUMIDITY_HIGH:
            humidity_multiplier = 2.0
        else:
            humidity_multiplier = 1.0

        # Weather effect
        if conditions.weather == WeatherCondition.HEAVY_RAIN:
            weather_multiplier = 2.0
        elif conditions.weather == WeatherCondition.LIGHT_RAIN:
            weather_multiplier = 1.5
        else:
            weather_multiplier = 1.0

        # Combined corrosion rate
        corrosion_rate_per_day = base_rate * humidity_multiplier * weather_multiplier

        # Convert to per second
        dt_days = dt_seconds / 86400.0
        degradation = corrosion_rate_per_day * dt_days

        return degradation

    def get_severity_description(self, combined_stress: float) -> str:
        """Get human-readable severity description"""
        if combined_stress < 1.2:
            return "🟢 Normal - Low stress"
        elif combined_stress < 1.5:
            return "🟡 Elevated - Moderate stress"
        elif combined_stress < 2.0:
            return "🟠 High - Significant stress"
        elif combined_stress < 3.0:
            return "🔴 Severe - Major stress"
        else:
            return "💀 Critical - Extreme stress"


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    env = EnvironmentalFactors()

    print("=== Environmental Stress Testing ===\n")

    # Test 1: Normal conditions
    print("TEST 1: Normal operating conditions")
    conditions = EnvironmentalConditions(
        ambient_temp_C=25.0,
        equipment_temp_C=40.0,
        humidity_pct=60.0,
        weather=WeatherCondition.CLEAR,
        dust_level_ppm=50.0,
        hours_continuous_operation=4.0,
        starts_today=3,
        overload_events_today=0
    )

    stress = env.calculate_combined_stress(conditions, "mechanical")
    print(f"  Temperature factor: {stress['temperature_factor']:.2f}x")
    print(f"  Humidity factor: {stress['humidity_factor']:.2f}x")
    print(f"  Dust factor: {stress['dust_factor']:.2f}x")
    print(f"  Duty cycle factor: {stress['duty_cycle_factor']:.2f}x")
    print(f"  COMBINED: {stress['combined_stress']:.2f}x")
    print(f"  {env.get_severity_description(stress['combined_stress'])}\n")

    # Test 2: Hot day
    print("TEST 2: Hot day (40°C ambient)")
    conditions.ambient_temp_C = 40.0
    conditions.equipment_temp_C = 65.0
    stress = env.calculate_combined_stress(conditions, "electrical")
    print(f"  COMBINED: {stress['combined_stress']:.2f}x")
    print(f"  {env.get_severity_description(stress['combined_stress'])}\n")

    # Test 3: Rainy + dusty
    print("TEST 3: Heavy rain + high dust")
    conditions.weather = WeatherCondition.HEAVY_RAIN
    conditions.humidity_pct = 95.0
    conditions.dust_level_ppm = 400.0
    stress = env.calculate_combined_stress(conditions, "mechanical")
    print(f"  COMBINED: {stress['combined_stress']:.2f}x")
    print(f"  {env.get_severity_description(stress['combined_stress'])}\n")

    # Test 4: Extreme - long run + multiple overloads
    print("TEST 4: Extreme - 16h run + 5 overloads")
    conditions.hours_continuous_operation = 16.0
    conditions.overload_events_today = 5
    conditions.starts_today = 20
    stress = env.calculate_combined_stress(conditions, "mechanical")
    print(f"  COMBINED: {stress['combined_stress']:.2f}x")
    print(f"  {env.get_severity_description(stress['combined_stress'])}\n")

    # Test 5: Corrosion over time
    print("TEST 5: Corrosion simulation (30 days)")
    conditions = EnvironmentalConditions(
        humidity_pct=90.0,
        weather=WeatherCondition.HEAVY_RAIN
    )
    health = 100.0
    for day in range(30):
        degradation = env.apply_corrosion(health, conditions, 86400.0)  # 1 day
        health -= degradation
        if day % 5 == 0:
            print(f"  Day {day:2d}: health = {health:.2f}% (corroded {degradation:.4f}%)")
