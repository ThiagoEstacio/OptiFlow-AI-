"""
MELH-003: Dynamic Ishikawa (Fishbone) Diagram Analysis

Generates root cause analysis using the 6M methodology:
- Man (Personnel)
- Machine (Equipment)
- Method (Process)
- Material (Materials/Inputs)
- Measurement (Instrumentation)
- Mother Nature (Environment)

This replaces static diagrams with dynamic, data-driven analysis.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class IshikawaCategory(str, Enum):
    """6M Categories for Ishikawa Diagram"""
    MAN = "man"  # Personnel/Human factors
    MACHINE = "machine"  # Equipment issues
    METHOD = "method"  # Process/procedures
    MATERIAL = "material"  # Raw materials/inputs
    MEASUREMENT = "measurement"  # Instrumentation/sensors
    MOTHER_NATURE = "mother_nature"  # Environmental factors


class CauseSeverity(str, Enum):
    """Severity levels for root causes"""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Address within 24h
    MEDIUM = "medium"  # Address within 1 week
    LOW = "low"  # Monitor and plan


@dataclass
class RootCause:
    """Individual root cause identified"""
    category: IshikawaCategory
    cause: str
    description: str
    severity: CauseSeverity
    confidence: float  # 0.0 - 1.0
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    related_tags: List[str] = field(default_factory=list)
    frequency: int = 1  # How often this cause appears


@dataclass
class IshikawaDiagram:
    """Complete Ishikawa analysis result"""
    problem_statement: str
    generated_at: datetime
    analysis_period_hours: int
    categories: Dict[str, List[RootCause]]
    primary_cause: Optional[RootCause]
    total_causes_identified: int
    data_quality_score: float
    recommendations: List[str]


class IshikawaAnalysisService:
    """
    Dynamic Ishikawa Diagram Generator

    Uses real-time data to identify root causes of quality issues,
    equipment failures, or production problems.
    """

    # Cause patterns mapped to categories
    CAUSE_PATTERNS = {
        IshikawaCategory.MAN: {
            "patterns": [
                "operator_error", "training_gap", "fatigue", "communication",
                "shift_change", "human_error", "supervision"
            ],
            "tag_keywords": ["operator", "manual", "human", "user"],
            "alarm_keywords": ["operator", "manual", "interlock_bypass", "override"]
        },
        IshikawaCategory.MACHINE: {
            "patterns": [
                "equipment_failure", "wear", "calibration", "maintenance",
                "breakdown", "mechanical", "electrical"
            ],
            "tag_keywords": ["motor", "pump", "valve", "conveyor", "crusher", "feeder"],
            "alarm_keywords": ["fault", "failure", "trip", "overload", "breakdown"]
        },
        IshikawaCategory.METHOD: {
            "patterns": [
                "procedure_violation", "wrong_sequence", "timing", "sop",
                "process_deviation", "recipe", "batch"
            ],
            "tag_keywords": ["setpoint", "recipe", "batch", "sequence", "step"],
            "alarm_keywords": ["sequence", "step", "procedure", "deviation", "limit"]
        },
        IshikawaCategory.MATERIAL: {
            "patterns": [
                "contamination", "moisture", "grade_change", "supplier",
                "specification", "quality", "variation"
            ],
            "tag_keywords": ["material", "feed", "input", "grade", "moisture", "iron"],
            "alarm_keywords": ["quality", "contamination", "specification", "grade"]
        },
        IshikawaCategory.MEASUREMENT: {
            "patterns": [
                "sensor_drift", "calibration_error", "instrument_failure",
                "accuracy", "precision", "range"
            ],
            "tag_keywords": ["sensor", "transmitter", "analyzer", "scale", "flowmeter"],
            "alarm_keywords": ["sensor", "signal", "communication", "offline", "bad_quality"]
        },
        IshikawaCategory.MOTHER_NATURE: {
            "patterns": [
                "temperature_ambient", "humidity", "weather", "seasonal",
                "dust", "wind", "rain"
            ],
            "tag_keywords": ["ambient", "weather", "environment", "temperature_ext", "humidity"],
            "alarm_keywords": ["weather", "ambient", "environmental", "extreme"]
        }
    }

    def __init__(self):
        """Initialize Ishikawa analysis service"""
        self.analysis_cache: Dict[str, IshikawaDiagram] = {}
        logger.info("IshikawaAnalysisService initialized")

    async def analyze(
        self,
        problem_statement: str,
        alarms: List[Dict[str, Any]],
        tag_data: List[Dict[str, Any]],
        events: Optional[List[Dict[str, Any]]] = None,
        hours: int = 24
    ) -> IshikawaDiagram:
        """
        Generate dynamic Ishikawa diagram from operational data.

        Args:
            problem_statement: Description of the problem to analyze
            alarms: Recent alarm events
            tag_data: Tag value snapshots with anomalies
            events: Optional additional events (shift changes, maintenance, etc.)
            hours: Analysis period in hours

        Returns:
            IshikawaDiagram with categorized root causes
        """
        logger.info(f"Generating Ishikawa analysis for: {problem_statement}")

        categories: Dict[str, List[RootCause]] = {
            cat.value: [] for cat in IshikawaCategory
        }

        # Analyze alarms for root causes
        alarm_causes = self._analyze_alarms(alarms, hours)
        for cause in alarm_causes:
            categories[cause.category.value].append(cause)

        # Analyze tag data for patterns
        tag_causes = self._analyze_tags(tag_data, hours)
        for cause in tag_causes:
            categories[cause.category.value].append(cause)

        # Analyze events if provided
        if events:
            event_causes = self._analyze_events(events, hours)
            for cause in event_causes:
                categories[cause.category.value].append(cause)

        # Deduplicate and rank causes within each category
        for cat_name in categories:
            categories[cat_name] = self._deduplicate_causes(categories[cat_name])
            categories[cat_name] = sorted(
                categories[cat_name],
                key=lambda c: (c.severity.value, -c.confidence),
                reverse=False  # Critical first
            )

        # Find primary cause
        all_causes = [c for causes in categories.values() for c in causes]
        primary_cause = self._identify_primary_cause(all_causes)

        # Generate recommendations
        recommendations = self._generate_recommendations(categories, primary_cause)

        # Calculate data quality score
        data_quality = self._calculate_data_quality(alarms, tag_data, events)

        diagram = IshikawaDiagram(
            problem_statement=problem_statement,
            generated_at=datetime.utcnow(),
            analysis_period_hours=hours,
            categories=categories,
            primary_cause=primary_cause,
            total_causes_identified=len(all_causes),
            data_quality_score=data_quality,
            recommendations=recommendations
        )

        # Cache result
        cache_key = f"{problem_statement[:50]}_{hours}h"
        self.analysis_cache[cache_key] = diagram

        logger.info(f"Ishikawa analysis complete: {len(all_causes)} causes identified")
        return diagram

    def _analyze_alarms(self, alarms: List[Dict], hours: int) -> List[RootCause]:
        """Extract root causes from alarm data"""
        causes = []

        for alarm in alarms:
            alarm_type = alarm.get("alarm_type", "").lower()
            tag_id = alarm.get("tag_id", "")
            message = alarm.get("message", "").lower()
            count = alarm.get("count", 1)

            category = self._classify_alarm(alarm_type, tag_id, message)
            severity = self._determine_severity(alarm)

            cause = RootCause(
                category=category,
                cause=alarm.get("alarm_type", "Unknown Alarm"),
                description=alarm.get("message", f"Alarm on {tag_id}"),
                severity=severity,
                confidence=min(0.5 + (count * 0.1), 0.95),  # Higher count = higher confidence
                evidence=[f"Alarm occurred {count} times in {hours}h"],
                recommendations=self._get_alarm_recommendations(category, alarm_type),
                related_tags=[tag_id] if tag_id else [],
                frequency=count
            )
            causes.append(cause)

        return causes

    def _analyze_tags(self, tag_data: List[Dict], hours: int) -> List[RootCause]:
        """Extract root causes from tag value anomalies"""
        causes = []

        for tag in tag_data:
            tag_id = tag.get("tag_id", "")
            tag_name = tag.get("name", tag_id).lower()
            value = tag.get("value")
            quality = tag.get("quality", "GOOD")
            has_anomaly = tag.get("is_anomaly", False)
            cv = tag.get("coefficient_of_variation", 0)

            # Skip good quality, stable tags
            if quality == "GOOD" and not has_anomaly and cv < 15:
                continue

            category = self._classify_tag(tag_id, tag_name)

            # Bad quality indicates measurement issues
            if quality in ["BAD", "UNCERTAIN", "COMM_LOSS"]:
                cause = RootCause(
                    category=IshikawaCategory.MEASUREMENT,
                    cause=f"Signal Quality Issue: {quality}",
                    description=f"Tag {tag_name} showing {quality} quality",
                    severity=CauseSeverity.HIGH if quality == "COMM_LOSS" else CauseSeverity.MEDIUM,
                    confidence=0.85,
                    evidence=[f"Quality status: {quality}"],
                    recommendations=[
                        "Check sensor wiring and connections",
                        "Verify transmitter power supply",
                        "Check for electromagnetic interference"
                    ],
                    related_tags=[tag_id]
                )
                causes.append(cause)

            # High variability indicates process instability
            if cv > 25:
                cause = RootCause(
                    category=category,
                    cause=f"High Process Variability",
                    description=f"Tag {tag_name} showing {cv:.1f}% CV (threshold: 25%)",
                    severity=CauseSeverity.MEDIUM if cv < 50 else CauseSeverity.HIGH,
                    confidence=0.7,
                    evidence=[f"Coefficient of Variation: {cv:.1f}%"],
                    recommendations=[
                        "Review control loop tuning",
                        "Check for upstream disturbances",
                        "Verify setpoint stability"
                    ],
                    related_tags=[tag_id]
                )
                causes.append(cause)

            # Anomaly detected
            if has_anomaly:
                cause = RootCause(
                    category=category,
                    cause=f"Anomaly Detected",
                    description=f"ML model detected anomaly in {tag_name}",
                    severity=CauseSeverity.HIGH,
                    confidence=tag.get("anomaly_confidence", 0.75),
                    evidence=[
                        f"Current value: {value}",
                        f"Expected range: {tag.get('expected_min')} - {tag.get('expected_max')}"
                    ],
                    recommendations=[
                        "Investigate recent changes",
                        "Check related equipment",
                        "Review maintenance history"
                    ],
                    related_tags=[tag_id]
                )
                causes.append(cause)

        return causes

    def _analyze_events(self, events: List[Dict], hours: int) -> List[RootCause]:
        """Extract root causes from operational events"""
        causes = []

        for event in events:
            event_type = event.get("type", "").lower()
            description = event.get("description", "")

            if "shift" in event_type or "handover" in event_type:
                cause = RootCause(
                    category=IshikawaCategory.MAN,
                    cause="Shift Change",
                    description=f"Shift change occurred: {description}",
                    severity=CauseSeverity.LOW,
                    confidence=0.4,
                    evidence=[f"Event: {description}"],
                    recommendations=[
                        "Review shift handover procedures",
                        "Check for incomplete tasks at shift change"
                    ]
                )
                causes.append(cause)

            elif "maintenance" in event_type:
                cause = RootCause(
                    category=IshikawaCategory.MACHINE,
                    cause="Recent Maintenance",
                    description=f"Maintenance activity: {description}",
                    severity=CauseSeverity.MEDIUM,
                    confidence=0.6,
                    evidence=[f"Maintenance event: {description}"],
                    recommendations=[
                        "Verify maintenance was completed correctly",
                        "Check post-maintenance test results"
                    ]
                )
                causes.append(cause)

            elif "material" in event_type or "grade" in event_type:
                cause = RootCause(
                    category=IshikawaCategory.MATERIAL,
                    cause="Material Change",
                    description=f"Material/grade change: {description}",
                    severity=CauseSeverity.MEDIUM,
                    confidence=0.65,
                    evidence=[f"Material event: {description}"],
                    recommendations=[
                        "Verify material specifications",
                        "Check process adjustments for new material"
                    ]
                )
                causes.append(cause)

        return causes

    def _classify_alarm(self, alarm_type: str, tag_id: str, message: str) -> IshikawaCategory:
        """Classify alarm into Ishikawa category"""
        combined_text = f"{alarm_type} {tag_id} {message}".lower()

        for category, patterns in self.CAUSE_PATTERNS.items():
            for keyword in patterns["alarm_keywords"]:
                if keyword in combined_text:
                    return category

        # Default to machine for most alarms
        return IshikawaCategory.MACHINE

    def _classify_tag(self, tag_id: str, tag_name: str) -> IshikawaCategory:
        """Classify tag into Ishikawa category"""
        combined_text = f"{tag_id} {tag_name}".lower()

        for category, patterns in self.CAUSE_PATTERNS.items():
            for keyword in patterns["tag_keywords"]:
                if keyword in combined_text:
                    return category

        # Default to method for process tags
        return IshikawaCategory.METHOD

    def _determine_severity(self, alarm: Dict) -> CauseSeverity:
        """Determine severity based on alarm properties"""
        priority = alarm.get("priority", "").upper()
        count = alarm.get("count", 1)

        if priority == "CRITICAL" or count > 10:
            return CauseSeverity.CRITICAL
        elif priority == "HIGH" or count > 5:
            return CauseSeverity.HIGH
        elif priority == "MEDIUM" or count > 2:
            return CauseSeverity.MEDIUM
        else:
            return CauseSeverity.LOW

    def _get_alarm_recommendations(self, category: IshikawaCategory, alarm_type: str) -> List[str]:
        """Get recommendations based on category and alarm type"""
        recommendations = {
            IshikawaCategory.MAN: [
                "Review operator actions leading to alarm",
                "Check if refresher training is needed",
                "Verify procedures are being followed"
            ],
            IshikawaCategory.MACHINE: [
                "Check equipment maintenance history",
                "Verify mechanical condition",
                "Review spare parts availability"
            ],
            IshikawaCategory.METHOD: [
                "Review operating procedures",
                "Check sequence logic",
                "Verify recipe parameters"
            ],
            IshikawaCategory.MATERIAL: [
                "Check material quality certificates",
                "Verify supplier compliance",
                "Review incoming inspection results"
            ],
            IshikawaCategory.MEASUREMENT: [
                "Calibrate sensors",
                "Check signal integrity",
                "Verify transmitter configuration"
            ],
            IshikawaCategory.MOTHER_NATURE: [
                "Check environmental conditions",
                "Review weather impact on operations",
                "Verify climate control systems"
            ]
        }
        return recommendations.get(category, ["Investigate root cause"])

    def _deduplicate_causes(self, causes: List[RootCause]) -> List[RootCause]:
        """Remove duplicate causes, keeping highest confidence"""
        seen = {}
        for cause in causes:
            key = f"{cause.category.value}_{cause.cause}"
            if key not in seen or cause.confidence > seen[key].confidence:
                if key in seen:
                    # Merge evidence
                    cause.evidence.extend(seen[key].evidence)
                    cause.frequency += seen[key].frequency
                seen[key] = cause

        return list(seen.values())

    def _identify_primary_cause(self, causes: List[RootCause]) -> Optional[RootCause]:
        """Identify the most likely primary root cause"""
        if not causes:
            return None

        # Score each cause
        scored_causes = []
        for cause in causes:
            score = 0

            # Severity weight
            severity_weights = {
                CauseSeverity.CRITICAL: 100,
                CauseSeverity.HIGH: 75,
                CauseSeverity.MEDIUM: 50,
                CauseSeverity.LOW: 25
            }
            score += severity_weights[cause.severity]

            # Confidence weight
            score += cause.confidence * 50

            # Frequency weight
            score += min(cause.frequency * 5, 25)

            scored_causes.append((score, cause))

        # Return highest scoring cause
        scored_causes.sort(key=lambda x: x[0], reverse=True)
        return scored_causes[0][1] if scored_causes else None

    def _generate_recommendations(
        self,
        categories: Dict[str, List[RootCause]],
        primary_cause: Optional[RootCause]
    ) -> List[str]:
        """Generate prioritized recommendations"""
        recommendations = []

        if primary_cause:
            recommendations.append(
                f"PRIORITY: Address {primary_cause.cause} ({primary_cause.category.value})"
            )
            recommendations.extend(primary_cause.recommendations[:2])

        # Add recommendations from critical causes
        for cat_name, causes in categories.items():
            for cause in causes:
                if cause.severity == CauseSeverity.CRITICAL and cause != primary_cause:
                    recommendations.append(
                        f"CRITICAL: {cause.cause} - {cause.recommendations[0] if cause.recommendations else 'Investigate'}"
                    )

        # Limit to top 5 recommendations
        return recommendations[:5]

    def _calculate_data_quality(
        self,
        alarms: List[Dict],
        tag_data: List[Dict],
        events: Optional[List[Dict]]
    ) -> float:
        """Calculate quality score of input data"""
        score = 0.0
        factors = 0

        # Alarms data quality
        if alarms:
            score += 0.3 * min(len(alarms) / 10, 1.0)
            factors += 1

        # Tag data quality
        if tag_data:
            good_quality = sum(1 for t in tag_data if t.get("quality") == "GOOD")
            score += 0.4 * (good_quality / len(tag_data)) if tag_data else 0
            factors += 1

        # Events data quality
        if events:
            score += 0.3 * min(len(events) / 5, 1.0)
            factors += 1

        return score / factors if factors > 0 else 0.5

    def to_dict(self, diagram: IshikawaDiagram) -> Dict[str, Any]:
        """Convert IshikawaDiagram to dictionary for JSON serialization"""
        return {
            "problem_statement": diagram.problem_statement,
            "generated_at": diagram.generated_at.isoformat(),
            "analysis_period_hours": diagram.analysis_period_hours,
            "categories": {
                cat_name: [
                    {
                        "category": cause.category.value,
                        "cause": cause.cause,
                        "description": cause.description,
                        "severity": cause.severity.value,
                        "confidence": cause.confidence,
                        "evidence": cause.evidence,
                        "recommendations": cause.recommendations,
                        "related_tags": cause.related_tags,
                        "frequency": cause.frequency
                    }
                    for cause in causes
                ]
                for cat_name, causes in diagram.categories.items()
            },
            "primary_cause": {
                "category": diagram.primary_cause.category.value,
                "cause": diagram.primary_cause.cause,
                "description": diagram.primary_cause.description,
                "severity": diagram.primary_cause.severity.value,
                "confidence": diagram.primary_cause.confidence
            } if diagram.primary_cause else None,
            "total_causes_identified": diagram.total_causes_identified,
            "data_quality_score": diagram.data_quality_score,
            "recommendations": diagram.recommendations
        }


# Singleton instance
_ishikawa_service: Optional[IshikawaAnalysisService] = None


def get_ishikawa_service() -> IshikawaAnalysisService:
    """Get or create Ishikawa analysis service instance"""
    global _ishikawa_service
    if _ishikawa_service is None:
        _ishikawa_service = IshikawaAnalysisService()
    return _ishikawa_service
