"""
MELH-004: Cross-Equipment Correlation Analysis

Identifies correlations between equipment to predict propagation of:
- Failures
- Performance degradation
- Quality issues
- Production bottlenecks

Uses statistical correlation analysis and pattern mining to discover
relationships between equipment that may not be obvious from process diagrams.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

# Try to import scipy for advanced correlation
try:
    from scipy import stats
    from scipy.signal import correlate
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not available - using basic correlation methods")


class CorrelationType(str, Enum):
    """Types of correlation between equipment"""
    POSITIVE = "positive"  # Equipment move together
    NEGATIVE = "negative"  # Equipment move inversely
    LAGGED = "lagged"  # One follows the other with delay
    CAUSAL = "causal"  # One causes changes in another


class CorrelationStrength(str, Enum):
    """Strength of correlation"""
    STRONG = "strong"  # |r| > 0.7
    MODERATE = "moderate"  # 0.4 < |r| <= 0.7
    WEAK = "weak"  # 0.2 < |r| <= 0.4
    NONE = "none"  # |r| <= 0.2


@dataclass
class EquipmentCorrelation:
    """Correlation between two equipment/tags"""
    source_id: str
    source_name: str
    target_id: str
    target_name: str
    correlation_coefficient: float
    correlation_type: CorrelationType
    strength: CorrelationStrength
    lag_seconds: int = 0  # Time delay if lagged
    p_value: float = 0.0  # Statistical significance
    sample_size: int = 0
    description: str = ""
    recommendations: List[str] = field(default_factory=list)


@dataclass
class CorrelationMatrix:
    """Complete correlation analysis result"""
    generated_at: datetime
    analysis_period_hours: int
    equipment_count: int
    correlations: List[EquipmentCorrelation]
    strong_correlations: List[EquipmentCorrelation]
    potential_cascading_failures: List[Dict[str, Any]]
    recommendations: List[str]


class CrossEquipmentCorrelationService:
    """
    Cross-Equipment Correlation Analysis Service

    Analyzes relationships between multiple equipment to:
    1. Identify strongly correlated equipment
    2. Detect lagged correlations (cause-effect chains)
    3. Predict failure propagation paths
    4. Optimize maintenance scheduling
    """

    # Correlation thresholds
    STRONG_THRESHOLD = 0.7
    MODERATE_THRESHOLD = 0.4
    WEAK_THRESHOLD = 0.2

    # Maximum lag to check (in data points)
    MAX_LAG = 60  # e.g., 60 minutes if data is per-minute

    def __init__(self):
        """Initialize correlation service"""
        self.correlation_cache: Dict[str, CorrelationMatrix] = {}
        logger.info("CrossEquipmentCorrelationService initialized")

    async def analyze_correlations(
        self,
        equipment_data: Dict[str, List[Dict[str, Any]]],
        hours: int = 24,
        min_correlation: float = 0.3
    ) -> CorrelationMatrix:
        """
        Analyze correlations between multiple equipment.

        Args:
            equipment_data: Dict mapping equipment_id to list of readings
                           Each reading: {timestamp, value, quality}
            hours: Analysis period
            min_correlation: Minimum |r| to report

        Returns:
            CorrelationMatrix with all discovered correlations
        """
        logger.info(f"Analyzing correlations for {len(equipment_data)} equipment")

        correlations = []
        equipment_ids = list(equipment_data.keys())

        # Prepare time series data
        time_series = {}
        for eq_id, readings in equipment_data.items():
            # Extract values and align to timestamps
            values = [r.get("value", 0) for r in readings if r.get("value") is not None]
            if len(values) >= 10:  # Need minimum data points
                time_series[eq_id] = np.array(values, dtype=float)

        # Calculate pairwise correlations
        for i, eq1_id in enumerate(equipment_ids):
            if eq1_id not in time_series:
                continue

            for eq2_id in equipment_ids[i+1:]:
                if eq2_id not in time_series:
                    continue

                # Get correlation
                correlation = self._calculate_correlation(
                    time_series[eq1_id],
                    time_series[eq2_id],
                    eq1_id,
                    eq2_id,
                    equipment_data
                )

                if correlation and abs(correlation.correlation_coefficient) >= min_correlation:
                    correlations.append(correlation)

        # Sort by absolute correlation strength
        correlations.sort(key=lambda c: abs(c.correlation_coefficient), reverse=True)

        # Identify strong correlations
        strong = [c for c in correlations if c.strength == CorrelationStrength.STRONG]

        # Identify potential cascading failure paths
        cascading = self._identify_cascading_paths(correlations, equipment_data)

        # Generate recommendations
        recommendations = self._generate_recommendations(correlations, cascading)

        result = CorrelationMatrix(
            generated_at=datetime.utcnow(),
            analysis_period_hours=hours,
            equipment_count=len(equipment_ids),
            correlations=correlations,
            strong_correlations=strong,
            potential_cascading_failures=cascading,
            recommendations=recommendations
        )

        # Cache result
        cache_key = f"corr_{hours}h_{len(equipment_ids)}"
        self.correlation_cache[cache_key] = result

        logger.info(f"Correlation analysis complete: {len(correlations)} correlations found")
        return result

    def _calculate_correlation(
        self,
        series1: np.ndarray,
        series2: np.ndarray,
        eq1_id: str,
        eq2_id: str,
        equipment_data: Dict[str, List[Dict]]
    ) -> Optional[EquipmentCorrelation]:
        """Calculate correlation between two time series"""

        # Align series lengths
        min_len = min(len(series1), len(series2))
        if min_len < 10:
            return None

        s1 = series1[:min_len]
        s2 = series2[:min_len]

        # Handle constant series
        if np.std(s1) == 0 or np.std(s2) == 0:
            return None

        # Calculate Pearson correlation
        if SCIPY_AVAILABLE:
            r, p_value = stats.pearsonr(s1, s2)
        else:
            r = np.corrcoef(s1, s2)[0, 1]
            p_value = 0.05  # Assume significant if scipy not available

        # Check for lagged correlation if direct correlation is weak
        lag = 0
        if abs(r) < self.MODERATE_THRESHOLD:
            lag_r, lag = self._find_best_lag(s1, s2)
            if abs(lag_r) > abs(r):
                r = lag_r

        # Determine correlation type and strength
        if lag > 0:
            corr_type = CorrelationType.LAGGED
        elif r > 0:
            corr_type = CorrelationType.POSITIVE
        else:
            corr_type = CorrelationType.NEGATIVE

        strength = self._get_correlation_strength(r)

        # Get equipment names
        eq1_data = equipment_data.get(eq1_id, [{}])
        eq2_data = equipment_data.get(eq2_id, [{}])
        eq1_name = eq1_data[0].get("name", eq1_id) if eq1_data else eq1_id
        eq2_name = eq2_data[0].get("name", eq2_id) if eq2_data else eq2_id

        # Generate description
        description = self._generate_correlation_description(
            eq1_name, eq2_name, r, lag, corr_type
        )

        # Generate recommendations
        recommendations = self._get_correlation_recommendations(
            corr_type, strength, lag
        )

        return EquipmentCorrelation(
            source_id=eq1_id,
            source_name=eq1_name,
            target_id=eq2_id,
            target_name=eq2_name,
            correlation_coefficient=round(r, 4),
            correlation_type=corr_type,
            strength=strength,
            lag_seconds=lag * 60,  # Assuming minute-level data
            p_value=round(p_value, 6),
            sample_size=min_len,
            description=description,
            recommendations=recommendations
        )

    def _find_best_lag(
        self,
        series1: np.ndarray,
        series2: np.ndarray
    ) -> Tuple[float, int]:
        """Find the lag that maximizes correlation"""

        best_r = 0.0
        best_lag = 0

        for lag in range(1, min(self.MAX_LAG, len(series1) // 4)):
            # Series2 lagging series1
            if lag < len(series1):
                s1 = series1[lag:]
                s2 = series2[:-lag]
                if len(s1) >= 10 and np.std(s1) > 0 and np.std(s2) > 0:
                    r = np.corrcoef(s1, s2)[0, 1]
                    if abs(r) > abs(best_r):
                        best_r = r
                        best_lag = lag

            # Series1 lagging series2
            if lag < len(series2):
                s1 = series1[:-lag]
                s2 = series2[lag:]
                if len(s1) >= 10 and np.std(s1) > 0 and np.std(s2) > 0:
                    r = np.corrcoef(s1, s2)[0, 1]
                    if abs(r) > abs(best_r):
                        best_r = r
                        best_lag = -lag  # Negative indicates series2 leads

        return best_r, best_lag

    def _get_correlation_strength(self, r: float) -> CorrelationStrength:
        """Determine correlation strength from coefficient"""
        abs_r = abs(r)
        if abs_r > self.STRONG_THRESHOLD:
            return CorrelationStrength.STRONG
        elif abs_r > self.MODERATE_THRESHOLD:
            return CorrelationStrength.MODERATE
        elif abs_r > self.WEAK_THRESHOLD:
            return CorrelationStrength.WEAK
        else:
            return CorrelationStrength.NONE

    def _generate_correlation_description(
        self,
        eq1_name: str,
        eq2_name: str,
        r: float,
        lag: int,
        corr_type: CorrelationType
    ) -> str:
        """Generate human-readable description of correlation"""

        strength = self._get_correlation_strength(r)
        strength_text = strength.value

        if corr_type == CorrelationType.LAGGED:
            if lag > 0:
                return f"{strength_text.capitalize()} correlation: {eq1_name} changes follow {eq2_name} by ~{abs(lag)} minutes"
            else:
                return f"{strength_text.capitalize()} correlation: {eq2_name} changes follow {eq1_name} by ~{abs(lag)} minutes"
        elif corr_type == CorrelationType.POSITIVE:
            return f"{strength_text.capitalize()} positive correlation: {eq1_name} and {eq2_name} increase/decrease together"
        else:
            return f"{strength_text.capitalize()} negative correlation: When {eq1_name} increases, {eq2_name} decreases"

    def _get_correlation_recommendations(
        self,
        corr_type: CorrelationType,
        strength: CorrelationStrength,
        lag: int
    ) -> List[str]:
        """Generate recommendations based on correlation"""

        recommendations = []

        if strength == CorrelationStrength.STRONG:
            if corr_type == CorrelationType.LAGGED:
                recommendations.append(
                    f"Consider predictive monitoring - leading equipment can warn of issues in lagging equipment"
                )
                recommendations.append(
                    f"Schedule maintenance for both equipment together, with {abs(lag)}-minute offset"
                )
            else:
                recommendations.append(
                    "These equipment should be monitored together for anomalies"
                )
                recommendations.append(
                    "Coordinate maintenance windows to minimize production impact"
                )

        elif strength == CorrelationStrength.MODERATE:
            recommendations.append(
                "Monitor for correlation changes - may indicate developing issues"
            )

        return recommendations

    def _identify_cascading_paths(
        self,
        correlations: List[EquipmentCorrelation],
        equipment_data: Dict[str, List[Dict]]
    ) -> List[Dict[str, Any]]:
        """Identify potential cascading failure paths"""

        cascading_paths = []

        # Find chains of lagged correlations
        lagged = [c for c in correlations if c.correlation_type == CorrelationType.LAGGED and c.lag_seconds > 0]

        # Build graph of dependencies
        graph: Dict[str, List[Tuple[str, int]]] = {}
        for corr in lagged:
            if corr.source_id not in graph:
                graph[corr.source_id] = []
            graph[corr.source_id].append((corr.target_id, corr.lag_seconds))

        # Find paths
        for start_node in graph:
            paths = self._find_paths(graph, start_node, max_length=4)
            for path in paths:
                if len(path) >= 2:
                    total_delay = sum(lag for _, lag in path[1:])
                    cascading_paths.append({
                        "path": [node for node, _ in path],
                        "total_delay_seconds": total_delay,
                        "warning": f"Failure in {path[0][0]} may propagate to {path[-1][0]} in ~{total_delay//60} minutes",
                        "risk_level": "high" if len(path) >= 3 else "medium"
                    })

        return cascading_paths[:10]  # Top 10 paths

    def _find_paths(
        self,
        graph: Dict[str, List[Tuple[str, int]]],
        start: str,
        max_length: int
    ) -> List[List[Tuple[str, int]]]:
        """Find all paths from start node using DFS"""

        paths = []
        stack = [[(start, 0)]]

        while stack:
            path = stack.pop()
            node = path[-1][0]

            if len(path) > 1:
                paths.append(path)

            if len(path) < max_length and node in graph:
                for next_node, lag in graph[node]:
                    if not any(n == next_node for n, _ in path):  # Avoid cycles
                        stack.append(path + [(next_node, lag)])

        return paths

    def _generate_recommendations(
        self,
        correlations: List[EquipmentCorrelation],
        cascading: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate overall recommendations from analysis"""

        recommendations = []

        # Strong correlations
        strong_count = sum(1 for c in correlations if c.strength == CorrelationStrength.STRONG)
        if strong_count > 0:
            recommendations.append(
                f"Found {strong_count} strongly correlated equipment pairs - coordinate maintenance schedules"
            )

        # Cascading risks
        high_risk = sum(1 for c in cascading if c.get("risk_level") == "high")
        if high_risk > 0:
            recommendations.append(
                f"Identified {high_risk} high-risk cascading failure paths - prioritize upstream equipment monitoring"
            )

        # Lagged correlations
        lagged_count = sum(1 for c in correlations if c.correlation_type == CorrelationType.LAGGED)
        if lagged_count > 0:
            recommendations.append(
                f"Found {lagged_count} time-delayed correlations - implement predictive alerts based on leading indicators"
            )

        return recommendations

    async def get_equipment_impact(
        self,
        equipment_id: str,
        correlations: List[EquipmentCorrelation]
    ) -> Dict[str, Any]:
        """Get impact analysis for specific equipment"""

        # Find all correlations involving this equipment
        related = [
            c for c in correlations
            if c.source_id == equipment_id or c.target_id == equipment_id
        ]

        if not related:
            return {
                "equipment_id": equipment_id,
                "impact_score": 0,
                "affected_equipment": [],
                "message": "No significant correlations found"
            }

        # Calculate impact score (how many other equipment would be affected)
        affected = set()
        for c in related:
            if c.strength in [CorrelationStrength.STRONG, CorrelationStrength.MODERATE]:
                if c.source_id == equipment_id:
                    affected.add(c.target_id)
                else:
                    affected.add(c.source_id)

        impact_score = len(affected) / len(set(c.source_id for c in correlations) | set(c.target_id for c in correlations))

        return {
            "equipment_id": equipment_id,
            "impact_score": round(impact_score, 2),
            "affected_equipment": list(affected),
            "correlation_count": len(related),
            "strong_correlations": sum(1 for c in related if c.strength == CorrelationStrength.STRONG)
        }

    def to_dict(self, matrix: CorrelationMatrix) -> Dict[str, Any]:
        """Convert CorrelationMatrix to dictionary for JSON serialization"""
        return {
            "generated_at": matrix.generated_at.isoformat(),
            "analysis_period_hours": matrix.analysis_period_hours,
            "equipment_count": matrix.equipment_count,
            "total_correlations": len(matrix.correlations),
            "strong_correlation_count": len(matrix.strong_correlations),
            "correlations": [
                {
                    "source_id": c.source_id,
                    "source_name": c.source_name,
                    "target_id": c.target_id,
                    "target_name": c.target_name,
                    "coefficient": c.correlation_coefficient,
                    "type": c.correlation_type.value,
                    "strength": c.strength.value,
                    "lag_seconds": c.lag_seconds,
                    "p_value": c.p_value,
                    "sample_size": c.sample_size,
                    "description": c.description,
                    "recommendations": c.recommendations
                }
                for c in matrix.correlations
            ],
            "cascading_failures": matrix.potential_cascading_failures,
            "recommendations": matrix.recommendations
        }


# Singleton instance
_correlation_service: Optional[CrossEquipmentCorrelationService] = None


def get_correlation_service() -> CrossEquipmentCorrelationService:
    """Get or create correlation service instance"""
    global _correlation_service
    if _correlation_service is None:
        _correlation_service = CrossEquipmentCorrelationService()
    return _correlation_service
