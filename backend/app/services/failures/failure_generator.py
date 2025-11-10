"""
Failure Generator - Core probabilistic failure engine

Generates equipment failures based on:
1. MTBF (Mean Time Between Failures) - decreases with health degradation
2. Operating hours and cycles
3. Environmental stress factors
4. Random events with realistic probabilities

Example:
    generator = FailureGenerator()
    failure_occurred = generator.evaluate_equipment(equipment, dt_s)
    if failure_occurred:
        print(f"Failure type: {equipment.failure_type}")
"""

import numpy as np
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FailureConfig:
    """Configuration for failure generation"""
    # Base MTBF for equipment at 100% health (hours)
    base_mtbf_hours: float = 10000.0  # 10,000 hours = ~1.14 years

    # Minimum MTBF even at 0% health (to avoid divide by zero)
    min_mtbf_hours: float = 100.0  # 100 hours = ~4 days

    # Enable/disable failure generation
    enabled: bool = True

    # Verbosity for debugging
    verbose: bool = False


class FailureGenerator:
    """
    Main failure generation engine

    Calculates failure probability based on equipment health and generates
    random failures using exponential distribution (Poisson process).

    Failure rate λ = 1/MTBF
    Probability of failure in time dt: P(fail) = 1 - exp(-λ * dt)
    """

    def __init__(self, config: Optional[FailureConfig] = None):
        self.config = config or FailureConfig()
        self.failure_history: Dict[str, list] = {}  # Track failures per equipment
        self.rng = np.random.default_rng()  # Random number generator

        logger.info(f"FailureGenerator initialized - Base MTBF: {self.config.base_mtbf_hours}h")

    def calculate_mtbf(self, health_pct: float) -> float:
        """
        Calculate dynamic MTBF based on equipment health

        MTBF decreases non-linearly as health decreases:
        - 100% health → base_mtbf (e.g. 10,000h)
        - 50% health → base_mtbf/4 (e.g. 2,500h)
        - 10% health → min_mtbf (e.g. 100h)

        Uses exponential decay: MTBF = min + (base - min) * (health/100)^2

        Args:
            health_pct: Equipment health percentage (0-100)

        Returns:
            MTBF in hours
        """
        if health_pct < 0:
            health_pct = 0
        if health_pct > 100:
            health_pct = 100

        # Exponential decay (squaring health factor makes degradation accelerate)
        health_factor = (health_pct / 100.0) ** 2

        mtbf = self.config.min_mtbf_hours + \
               (self.config.base_mtbf_hours - self.config.min_mtbf_hours) * health_factor

        return mtbf

    def calculate_failure_probability(self,
                                     health_pct: float,
                                     dt_seconds: float,
                                     stress_multiplier: float = 1.0) -> float:
        """
        Calculate probability of failure in time interval dt

        Uses exponential distribution (Poisson process):
        P(fail in dt) = 1 - exp(-λ * dt)
        where λ = 1/MTBF

        Args:
            health_pct: Equipment health (0-100)
            dt_seconds: Time interval in seconds
            stress_multiplier: Factor to increase failure rate (>1 = more stress)

        Returns:
            Probability of failure (0-1)
        """
        if not self.config.enabled:
            return 0.0

        # Calculate MTBF in hours
        mtbf_hours = self.calculate_mtbf(health_pct)

        # Apply stress multiplier (environmental factors, overload, etc)
        mtbf_hours = mtbf_hours / stress_multiplier

        # Failure rate λ = 1/MTBF (in failures per hour)
        failure_rate_per_hour = 1.0 / mtbf_hours

        # Convert dt to hours
        dt_hours = dt_seconds / 3600.0

        # Probability using exponential distribution
        # P = 1 - exp(-λ * dt)
        probability = 1.0 - np.exp(-failure_rate_per_hour * dt_hours)

        return probability

    def roll_failure(self, probability: float) -> bool:
        """
        Roll dice to determine if failure occurs

        Args:
            probability: Failure probability (0-1)

        Returns:
            True if failure occurs, False otherwise
        """
        if probability <= 0:
            return False
        if probability >= 1:
            return True

        # Generate random number [0, 1)
        roll = self.rng.random()

        return roll < probability

    def evaluate_equipment(self,
                          equipment_id: str,
                          health_pct: float,
                          dt_seconds: float,
                          stress_multiplier: float = 1.0) -> bool:
        """
        Evaluate if equipment fails in this time step

        Args:
            equipment_id: Unique identifier for equipment
            health_pct: Equipment health (0-100)
            dt_seconds: Time step in seconds
            stress_multiplier: Environmental/operational stress factor

        Returns:
            True if failure occurred, False otherwise
        """
        if not self.config.enabled:
            return False

        # Calculate probability
        prob = self.calculate_failure_probability(health_pct, dt_seconds, stress_multiplier)

        # Roll for failure
        failure_occurred = self.roll_failure(prob)

        # Log if failure occurred
        if failure_occurred:
            if equipment_id not in self.failure_history:
                self.failure_history[equipment_id] = []

            self.failure_history[equipment_id].append({
                'probability': prob,
                'health_pct': health_pct,
                'stress_multiplier': stress_multiplier
            })

            logger.warning(
                f"⚠️ FAILURE GENERATED: {equipment_id} "
                f"(health={health_pct:.1f}%, prob={prob*100:.4f}%, stress={stress_multiplier:.2f}x)"
            )
        elif self.config.verbose and prob > 0.001:  # Log high probability even if no failure
            logger.debug(
                f"Failure roll: {equipment_id} health={health_pct:.1f}% "
                f"prob={prob*100:.4f}% - NO FAILURE"
            )

        return failure_occurred

    def get_failure_count(self, equipment_id: str) -> int:
        """Get total number of failures for equipment"""
        return len(self.failure_history.get(equipment_id, []))

    def get_failure_history(self, equipment_id: str) -> list:
        """Get failure history for equipment"""
        return self.failure_history.get(equipment_id, [])

    def reset_history(self, equipment_id: Optional[str] = None):
        """Reset failure history (all equipment or specific one)"""
        if equipment_id:
            self.failure_history[equipment_id] = []
        else:
            self.failure_history = {}

    def get_statistics(self) -> Dict:
        """Get statistics about failures"""
        total_failures = sum(len(hist) for hist in self.failure_history.values())
        equipment_count = len(self.failure_history)

        return {
            'total_failures': total_failures,
            'equipment_with_failures': equipment_count,
            'avg_failures_per_equipment': total_failures / equipment_count if equipment_count > 0 else 0,
            'equipment_list': list(self.failure_history.keys())
        }


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Create generator
    config = FailureConfig(base_mtbf_hours=10000, verbose=True)
    generator = FailureGenerator(config)

    # Test MTBF calculation
    print("\n=== MTBF vs Health ===")
    for health in [100, 80, 60, 40, 20, 10, 5, 0]:
        mtbf = generator.calculate_mtbf(health)
        print(f"Health {health:3d}% → MTBF {mtbf:8.1f} hours ({mtbf/24:.1f} days)")

    # Test failure probability
    print("\n=== Failure Probability (1 hour interval) ===")
    dt_1hour = 3600  # 1 hour in seconds
    for health in [100, 50, 20, 10]:
        prob = generator.calculate_failure_probability(health, dt_1hour)
        print(f"Health {health:3d}% → P(fail in 1h) = {prob*100:.6f}%")

    # Simulate 1000 hours of operation
    print("\n=== Simulating 1000 hours ===")
    health = 30  # Start at 30% health (degraded equipment)
    dt_step = 60  # 1 minute steps
    steps = int(1000 * 3600 / dt_step)  # 1000 hours in 1-minute steps

    failures = 0
    for step in range(steps):
        if generator.evaluate_equipment("TEST_BELT_01", health, dt_step):
            failures += 1

    print(f"Failures occurred: {failures}")
    print(f"Expected failures: ~{1000 / generator.calculate_mtbf(health):.2f}")
    print(f"\nStatistics: {generator.get_statistics()}")
