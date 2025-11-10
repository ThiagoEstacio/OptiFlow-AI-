"""
Failure Analyzer - Root Cause Analysis Engine

Analyzes equipment failures and identifies root causes using:
- Time-series correlation analysis
- Pattern recognition
- Historical failure data
- AI-powered inference
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
import statistics

from app.models.asset import Asset
from app.models.alarm import AlarmDefinition

logger = logging.getLogger(__name__)


class FailureAnalyzer:
    """
    Analyzes equipment failures and performs root cause analysis.

    Techniques used:
    - Time correlation analysis
    - Pattern matching against historical failures
    - Multi-asset correlation
    - Statistical analysis of sensor data
    """

    def __init__(self, db: AsyncSession):
        self.db = db

        # Correlation window (minutes before failure to analyze)
        self.correlation_window = 60  # 1 hour

        # Known failure patterns
        self.failure_patterns = {
            "motor_overload": {
                "symptoms": ["high_current", "high_temperature", "vibration"],
                "causes": ["mechanical_load", "bearing_failure", "misalignment"],
            },
            "bearing_failure": {
                "symptoms": ["vibration", "high_temperature", "noise"],
                "causes": ["wear", "lubrication_failure", "contamination"],
            },
            "belt_slip": {
                "symptoms": ["speed_deviation", "low_torque", "irregular_sound"],
                "causes": ["tension_loss", "pulley_wear", "contamination"],
            },
            "overheating": {
                "symptoms": ["high_temperature", "thermal_shutdown"],
                "causes": ["cooling_failure", "overload", "ambient_temperature"],
            },
            "pump_cavitation": {
                "symptoms": ["vibration", "noise", "flow_reduction"],
                "causes": ["low_suction_pressure", "air_ingestion", "impeller_damage"],
            },
        }

    async def analyze_failure(
        self,
        asset_id: str,
        failure_time: datetime,
        failure_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive failure analysis.

        Args:
            asset_id: Asset that failed
            failure_time: When the failure occurred
            failure_description: Optional description of the failure

        Returns:
            Analysis results with probable causes and recommendations
        """
        try:
            logger.info(f"Analyzing failure for asset {asset_id} at {failure_time}")

            # Get asset information
            result = await self.db.execute(
                select(Asset).where(Asset.id == asset_id)
            )
            asset = result.scalar_one_or_none()

            if not asset:
                raise ValueError(f"Asset {asset_id} not found")

            # Collect data for analysis
            alarms_before = await self._get_alarms_before_failure(asset_id, failure_time)
            sensor_anomalies = await self._detect_sensor_anomalies(asset_id, failure_time)
            historical_failures = await self._get_historical_failures(asset_id)
            correlated_failures = await self._find_correlated_failures(failure_time)

            # Perform analysis
            pattern_match = self._match_failure_pattern(alarms_before, sensor_anomalies)
            probable_causes = self._identify_probable_causes(
                alarms_before,
                sensor_anomalies,
                historical_failures,
                pattern_match
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(probable_causes, asset.asset_type)

            # Calculate confidence score
            confidence = self._calculate_confidence(
                len(alarms_before),
                len(sensor_anomalies),
                len(historical_failures),
                pattern_match
            )

            analysis_result = {
                "asset_id": asset_id,
                "asset_name": asset.name,
                "asset_type": asset.asset_type,
                "failure_time": failure_time.isoformat(),
                "failure_description": failure_description,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "confidence_score": confidence,
                "alarms_before_failure": len(alarms_before),
                "sensor_anomalies_detected": len(sensor_anomalies),
                "historical_failures_count": len(historical_failures),
                "correlated_failures": len(correlated_failures),
                "pattern_match": pattern_match,
                "probable_causes": probable_causes,
                "recommendations": recommendations,
                "detailed_analysis": {
                    "alarms": alarms_before,
                    "anomalies": sensor_anomalies,
                    "historical_patterns": self._analyze_historical_patterns(historical_failures),
                    "correlated_assets": correlated_failures,
                },
            }

            logger.info(f"Failure analysis completed. Confidence: {confidence}%")

            return analysis_result

        except Exception as e:
            logger.error(f"Error analyzing failure: {e}")
            raise

    async def _get_alarms_before_failure(
        self,
        asset_id: str,
        failure_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get all alarms that occurred before the failure."""
        try:
            start_time = failure_time - timedelta(minutes=self.correlation_window)

            result = await self.db.execute(
                select(AlarmDefinition).where(
                    and_(
                        AlarmDefinition.asset_id == asset_id,
                        AlarmDefinition.triggered_at >= start_time,
                        AlarmDefinition.triggered_at <= failure_time
                    )
                ).order_by(AlarmDefinition.triggered_at.desc())
            )

            alarms = result.scalars().all()

            return [
                {
                    "alarm_type": alarm.alarm_type,
                    "severity": alarm.severity,
                    "message": alarm.message,
                    "triggered_at": alarm.triggered_at.isoformat(),
                    "minutes_before_failure": (failure_time - alarm.triggered_at).total_seconds() / 60,
                }
                for alarm in alarms
            ]

        except Exception as e:
            logger.error(f"Error getting alarms: {e}")
            return []

    async def _detect_sensor_anomalies(
        self,
        asset_id: str,
        failure_time: datetime
    ) -> List[Dict[str, Any]]:
        """Detect abnormal sensor readings before failure."""
        try:
            # This is a placeholder - in production, would query InfluxDB
            # for actual sensor data and detect anomalies

            # Simulated anomalies
            anomalies = []

            # In real implementation:
            # 1. Query time-series data from InfluxDB
            # 2. Calculate statistical baselines
            # 3. Detect values beyond 2-3 sigma
            # 4. Detect rapid changes (derivatives)

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    async def _get_historical_failures(self, asset_id: str) -> List[Dict[str, Any]]:
        """Get historical failure records for pattern analysis."""
        try:
            # Query past failures from alarms table
            result = await self.db.execute(
                select(AlarmDefinition).where(
                    and_(
                        AlarmDefinition.asset_id == asset_id,
                        AlarmDefinition.severity.in_(["critical", "high"])
                    )
                ).order_by(AlarmDefinition.triggered_at.desc()).limit(20)
            )

            alarms = result.scalars().all()

            return [
                {
                    "alarm_type": alarm.alarm_type,
                    "severity": alarm.severity,
                    "message": alarm.message,
                    "triggered_at": alarm.triggered_at.isoformat() if alarm.triggered_at else None,
                }
                for alarm in alarms
            ]

        except Exception as e:
            logger.error(f"Error getting historical failures: {e}")
            return []

    async def _find_correlated_failures(
        self,
        failure_time: datetime
    ) -> List[Dict[str, Any]]:
        """Find failures in other assets around the same time."""
        try:
            time_window = 15  # minutes

            start_time = failure_time - timedelta(minutes=time_window)
            end_time = failure_time + timedelta(minutes=time_window)

            result = await self.db.execute(
                select(AlarmDefinition).where(
                    and_(
                        AlarmDefinition.triggered_at >= start_time,
                        AlarmDefinition.triggered_at <= end_time,
                        AlarmDefinition.severity.in_(["critical", "high"])
                    )
                ).order_by(AlarmDefinition.triggered_at)
            )

            alarms = result.scalars().all()

            return [
                {
                    "asset_id": alarm.asset_id,
                    "alarm_type": alarm.alarm_type,
                    "triggered_at": alarm.triggered_at.isoformat() if alarm.triggered_at else None,
                }
                for alarm in alarms
            ]

        except Exception as e:
            logger.error(f"Error finding correlated failures: {e}")
            return []

    def _match_failure_pattern(
        self,
        alarms: List[Dict[str, Any]],
        anomalies: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Match observed symptoms to known failure patterns."""
        if not alarms and not anomalies:
            return None

        # Extract symptoms from alarms
        observed_symptoms = set()
        for alarm in alarms:
            alarm_type = alarm.get('alarm_type', '').lower()

            # Map alarm types to symptoms
            if 'current' in alarm_type or 'overload' in alarm_type:
                observed_symptoms.add('high_current')
            if 'temp' in alarm_type or 'heat' in alarm_type:
                observed_symptoms.add('high_temperature')
            if 'vibration' in alarm_type or 'vib' in alarm_type:
                observed_symptoms.add('vibration')
            if 'speed' in alarm_type:
                observed_symptoms.add('speed_deviation')

        # Match against known patterns
        best_match = None
        best_score = 0

        for pattern_name, pattern in self.failure_patterns.items():
            pattern_symptoms = set(pattern['symptoms'])
            match_score = len(observed_symptoms & pattern_symptoms) / len(pattern_symptoms)

            if match_score > best_score and match_score > 0.5:  # At least 50% match
                best_score = match_score
                best_match = pattern_name

        return best_match

    def _identify_probable_causes(
        self,
        alarms: List[Dict[str, Any]],
        anomalies: List[Dict[str, Any]],
        historical_failures: List[Dict[str, Any]],
        pattern_match: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Identify most probable root causes."""
        causes = []

        # Pattern-based causes
        if pattern_match and pattern_match in self.failure_patterns:
            pattern = self.failure_patterns[pattern_match]
            for cause in pattern['causes']:
                causes.append({
                    "cause": cause.replace('_', ' ').title(),
                    "probability": 0.7,
                    "source": "pattern_matching",
                    "pattern": pattern_match,
                })

        # Frequency-based causes from historical data
        if historical_failures:
            alarm_types = [f.get('alarm_type') for f in historical_failures if f.get('alarm_type')]
            if alarm_types:
                # Find most common alarm type
                alarm_counter = {}
                for alarm_type in alarm_types:
                    alarm_counter[alarm_type] = alarm_counter.get(alarm_type, 0) + 1

                most_common = max(alarm_counter.items(), key=lambda x: x[1])
                frequency = most_common[1] / len(historical_failures)

                if frequency > 0.3:  # If occurs in >30% of failures
                    causes.append({
                        "cause": f"Recurring {most_common[0]} Issue",
                        "probability": min(frequency, 0.9),
                        "source": "historical_pattern",
                        "frequency": f"{frequency * 100:.1f}%",
                    })

        # If no causes identified, provide generic ones
        if not causes:
            causes.append({
                "cause": "Insufficient Data for Analysis",
                "probability": 0.3,
                "source": "default",
                "note": "More historical data needed for accurate analysis",
            })

        # Sort by probability
        causes.sort(key=lambda x: x['probability'], reverse=True)

        return causes

    def _generate_recommendations(
        self,
        probable_causes: List[Dict[str, Any]],
        asset_type: Optional[str]
    ) -> List[str]:
        """Generate actionable recommendations based on probable causes."""
        recommendations = []

        for cause in probable_causes[:3]:  # Top 3 causes
            cause_name = cause.get('cause', '').lower()

            # Cause-specific recommendations
            if 'bearing' in cause_name:
                recommendations.extend([
                    "Inspect bearing condition and lubrication",
                    "Check for contamination or wear",
                    "Verify proper bearing alignment",
                ])
            elif 'overload' in cause_name or 'current' in cause_name:
                recommendations.extend([
                    "Check mechanical load on motor",
                    "Verify setpoint and control parameters",
                    "Inspect for mechanical binding or friction",
                ])
            elif 'vibration' in cause_name:
                recommendations.extend([
                    "Perform vibration analysis",
                    "Check for misalignment or imbalance",
                    "Inspect mounting and foundation",
                ])
            elif 'temperature' in cause_name or 'heat' in cause_name:
                recommendations.extend([
                    "Inspect cooling system operation",
                    "Verify adequate ventilation",
                    "Check for excessive friction or load",
                ])

        # Generic recommendations if no specific ones
        if not recommendations:
            recommendations.extend([
                "Conduct thorough physical inspection",
                "Review maintenance history",
                "Check recent operational changes",
                "Consult equipment manual for troubleshooting",
            ])

        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)

        return unique_recommendations[:5]  # Top 5 recommendations

    def _calculate_confidence(
        self,
        alarm_count: int,
        anomaly_count: int,
        historical_count: int,
        pattern_match: Optional[str]
    ) -> float:
        """Calculate confidence score for the analysis (0-100)."""
        confidence = 0.0

        # Base confidence from data availability
        if alarm_count > 0:
            confidence += min(alarm_count * 15, 40)
        if anomaly_count > 0:
            confidence += min(anomaly_count * 10, 30)
        if historical_count > 5:
            confidence += min(historical_count * 2, 20)

        # Bonus for pattern match
        if pattern_match:
            confidence += 20

        # Cap at 95% (never 100% certain)
        return min(round(confidence, 1), 95.0)

    def _analyze_historical_patterns(
        self,
        historical_failures: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze patterns in historical failure data."""
        if not historical_failures:
            return {"pattern": "insufficient_data"}

        # Extract alarm types
        alarm_types = [f.get('alarm_type') for f in historical_failures if f.get('alarm_type')]

        # Count occurrences
        type_counts = {}
        for alarm_type in alarm_types:
            type_counts[alarm_type] = type_counts.get(alarm_type, 0) + 1

        # Calculate time between failures
        times = [
            datetime.fromisoformat(f['triggered_at'])
            for f in historical_failures
            if f.get('triggered_at')
        ]

        time_between_failures = []
        if len(times) > 1:
            sorted_times = sorted(times, reverse=True)
            for i in range(len(sorted_times) - 1):
                delta = sorted_times[i] - sorted_times[i + 1]
                time_between_failures.append(delta.total_seconds() / 3600)  # hours

        avg_time_between = None
        if time_between_failures:
            avg_time_between = statistics.mean(time_between_failures)

        return {
            "most_common_alarm": max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None,
            "alarm_diversity": len(type_counts),
            "average_time_between_failures_hours": round(avg_time_between, 1) if avg_time_between else None,
            "failure_frequency": "high" if len(historical_failures) > 10 else "normal",
        }
