"""
Data Quality Validation Service
===============================

Validates and annotates data quality at the Gateway edge before publishing to Kafka.

This is the first line of defense for data quality in the OptiFlow pipeline.
Invalid or suspicious data is flagged with quality indicators, not discarded,
so downstream systems can decide how to handle it.

Quality Checks:
1. Range Validation - Value within defined min/max limits
2. Rate of Change - Detect sudden spikes/drops (potential sensor issues)
3. Frozen Value - Detect values that haven't changed (stuck sensor)
4. Null/Invalid - Missing or malformed values
5. Timestamp - Future timestamps or too old data

Quality Levels (ISA-95 compatible):
- GOOD: Value passes all quality checks
- UNCERTAIN: Value is suspicious but may be valid
- BAD: Value failed critical checks
- INTERPOLATED: Value was interpolated/estimated

Sprint 1 Task: Add basic data quality validation at the Gateway
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# Import metrics
try:
    from prometheus_client import Counter, Gauge, Histogram
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """ISA-95 compatible quality levels"""
    GOOD = "good"
    UNCERTAIN = "uncertain"
    BAD = "bad"
    INTERPOLATED = "interpolated"


class QualityIssue(Enum):
    """Types of quality issues detected"""
    NONE = "none"
    OUT_OF_RANGE = "out_of_range"
    RATE_OF_CHANGE = "rate_of_change"
    FROZEN_VALUE = "frozen_value"
    NULL_VALUE = "null_value"
    INVALID_TYPE = "invalid_type"
    FUTURE_TIMESTAMP = "future_timestamp"
    STALE_TIMESTAMP = "stale_timestamp"


@dataclass
class TagQualityConfig:
    """Configuration for tag-specific quality validation"""
    tag_id: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    max_rate_of_change: Optional[float] = None  # Max change per second
    frozen_timeout_s: float = 300.0  # 5 minutes default
    max_age_s: float = 3600.0  # 1 hour default
    enabled: bool = True


@dataclass
class TagState:
    """State tracking for a single tag (for rate of change and frozen detection)"""
    last_value: Optional[float] = None
    last_timestamp: Optional[datetime] = None
    last_change_timestamp: Optional[datetime] = None
    consecutive_same_count: int = 0


# Prometheus Metrics (if available)
if PROMETHEUS_AVAILABLE:
    data_quality_checks_total = Counter(
        'gateway_data_quality_checks_total',
        'Total data quality checks performed',
        ['tag_id', 'result']  # good, uncertain, bad
    )

    data_quality_issues_total = Counter(
        'gateway_data_quality_issues_total',
        'Total data quality issues detected by type',
        ['issue_type']  # out_of_range, rate_of_change, frozen_value, etc.
    )

    data_quality_rate = Gauge(
        'gateway_data_quality_rate',
        'Current data quality rate (0-1)',
        ['tag_id']
    )

    data_quality_frozen_tags = Gauge(
        'gateway_data_quality_frozen_tags',
        'Number of tags currently detected as frozen'
    )


class DataQualityValidator:
    """
    Validates data quality at the Gateway edge.

    Features:
    - Range validation (configurable per tag)
    - Rate of change detection (spike detection)
    - Frozen value detection (stuck sensors)
    - Timestamp validation
    - Quality annotation (doesn't discard data)
    """

    def __init__(
        self,
        default_min: float = -1e10,
        default_max: float = 1e10,
        default_max_roc: float = 1000.0,  # Max 1000 units per second
        default_frozen_timeout_s: float = 300.0,
        default_max_age_s: float = 3600.0,
        enable_metrics: bool = True
    ):
        """
        Initialize data quality validator.

        Args:
            default_min: Default minimum value if not configured per tag
            default_max: Default maximum value if not configured per tag
            default_max_roc: Default max rate of change per second
            default_frozen_timeout_s: Default time before considering value frozen
            default_max_age_s: Default max age for timestamps
            enable_metrics: Enable Prometheus metrics
        """
        self.default_min = default_min
        self.default_max = default_max
        self.default_max_roc = default_max_roc
        self.default_frozen_timeout_s = default_frozen_timeout_s
        self.default_max_age_s = default_max_age_s
        self.enable_metrics = enable_metrics and PROMETHEUS_AVAILABLE

        # Tag-specific configurations
        self._tag_configs: Dict[str, TagQualityConfig] = {}

        # State tracking per tag
        self._tag_states: Dict[str, TagState] = defaultdict(TagState)

        # Statistics
        self._total_checked = 0
        self._total_good = 0
        self._total_uncertain = 0
        self._total_bad = 0
        self._issues_by_type: Dict[str, int] = defaultdict(int)

        logger.info("📊 DataQualityValidator initialized")
        logger.info(f"   Default range: [{default_min}, {default_max}]")
        logger.info(f"   Max rate of change: {default_max_roc}/s")
        logger.info(f"   Frozen timeout: {default_frozen_timeout_s}s")

    def configure_tag(self, config: TagQualityConfig):
        """Configure quality validation for a specific tag."""
        self._tag_configs[config.tag_id] = config
        logger.debug(f"Configured quality validation for tag: {config.tag_id}")

    def configure_tags_from_list(self, tags: List[Dict[str, Any]]):
        """
        Configure tags from a list of tag definitions.

        Expected format:
        [
            {
                "tag_id": "temp_001",
                "min_value": 0,
                "max_value": 100,
                "engineering_units": "°C"
            },
            ...
        ]
        """
        for tag in tags:
            tag_id = tag.get("tag_id") or tag.get("id") or tag.get("name")
            if not tag_id:
                continue

            config = TagQualityConfig(
                tag_id=tag_id,
                min_value=tag.get("min_value") or tag.get("low_limit"),
                max_value=tag.get("max_value") or tag.get("high_limit"),
                max_rate_of_change=tag.get("max_rate_of_change"),
                frozen_timeout_s=tag.get("frozen_timeout_s", self.default_frozen_timeout_s),
                max_age_s=tag.get("max_age_s", self.default_max_age_s),
                enabled=tag.get("quality_check_enabled", True)
            )
            self._tag_configs[tag_id] = config

        logger.info(f"✅ Configured quality validation for {len(tags)} tags")

    def validate(self, data_point: Dict[str, Any]) -> Tuple[QualityLevel, List[QualityIssue], Dict[str, Any]]:
        """
        Validate a single data point.

        Args:
            data_point: Dictionary with tag_id, value, timestamp

        Returns:
            Tuple of (quality_level, issues_list, annotated_data_point)
        """
        tag_id = data_point.get("tag_id") or data_point.get("tag_name") or data_point.get("name")
        value = data_point.get("value")
        timestamp_str = data_point.get("timestamp")

        issues: List[QualityIssue] = []
        self._total_checked += 1

        # Get tag config (or use defaults)
        config = self._tag_configs.get(tag_id)

        # Get/create tag state
        state = self._tag_states[tag_id]

        # Parse timestamp - ensure it's always timezone-aware (UTC)
        try:
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            elif isinstance(timestamp_str, datetime):
                timestamp = timestamp_str
            else:
                timestamp = datetime.now(timezone.utc)

            # Ensure timestamp is timezone-aware (convert naive to UTC)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            timestamp = datetime.now(timezone.utc)

        # === Check 1: Null/Invalid Value ===
        if value is None:
            issues.append(QualityIssue.NULL_VALUE)
            self._issues_by_type["null_value"] += 1
        elif not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                issues.append(QualityIssue.INVALID_TYPE)
                self._issues_by_type["invalid_type"] += 1

        # === Check 2: Range Validation ===
        if isinstance(value, (int, float)):
            min_val = config.min_value if config and config.min_value is not None else self.default_min
            max_val = config.max_value if config and config.max_value is not None else self.default_max

            if value < min_val or value > max_val:
                issues.append(QualityIssue.OUT_OF_RANGE)
                self._issues_by_type["out_of_range"] += 1
                logger.debug(f"⚠️ Out of range: {tag_id}={value} (limits: [{min_val}, {max_val}])")

        # === Check 3: Rate of Change ===
        if isinstance(value, (int, float)) and state.last_value is not None and state.last_timestamp:
            time_delta = (timestamp - state.last_timestamp).total_seconds()
            if time_delta > 0:
                rate = abs(value - state.last_value) / time_delta
                max_roc = config.max_rate_of_change if config and config.max_rate_of_change else self.default_max_roc

                if rate > max_roc:
                    issues.append(QualityIssue.RATE_OF_CHANGE)
                    self._issues_by_type["rate_of_change"] += 1
                    logger.debug(f"⚠️ High rate of change: {tag_id} rate={rate:.2f}/s (max: {max_roc})")

        # === Check 4: Frozen Value Detection ===
        if isinstance(value, (int, float)):
            if state.last_value is not None and abs(value - state.last_value) < 0.0001:
                state.consecutive_same_count += 1

                # Check if frozen
                frozen_timeout = config.frozen_timeout_s if config else self.default_frozen_timeout_s
                if state.last_change_timestamp:
                    time_since_change = (timestamp - state.last_change_timestamp).total_seconds()
                    if time_since_change > frozen_timeout:
                        issues.append(QualityIssue.FROZEN_VALUE)
                        self._issues_by_type["frozen_value"] += 1
                        logger.debug(f"⚠️ Frozen value: {tag_id}={value} (unchanged for {time_since_change:.0f}s)")
            else:
                state.consecutive_same_count = 0
                state.last_change_timestamp = timestamp

        # === Check 5: Timestamp Validation ===
        now = datetime.now(timezone.utc)

        # Future timestamp
        if timestamp > now + timedelta(seconds=60):
            issues.append(QualityIssue.FUTURE_TIMESTAMP)
            self._issues_by_type["future_timestamp"] += 1
            logger.debug(f"⚠️ Future timestamp: {tag_id} timestamp={timestamp}")

        # Stale timestamp
        max_age = config.max_age_s if config else self.default_max_age_s
        if (now - timestamp).total_seconds() > max_age:
            issues.append(QualityIssue.STALE_TIMESTAMP)
            self._issues_by_type["stale_timestamp"] += 1
            logger.debug(f"⚠️ Stale timestamp: {tag_id} age={(now - timestamp).total_seconds():.0f}s")

        # Update state
        if isinstance(value, (int, float)):
            state.last_value = value
        state.last_timestamp = timestamp

        # Determine quality level
        quality_level = self._determine_quality_level(issues)

        # Update statistics
        if quality_level == QualityLevel.GOOD:
            self._total_good += 1
        elif quality_level == QualityLevel.UNCERTAIN:
            self._total_uncertain += 1
        else:
            self._total_bad += 1

        # Update Prometheus metrics
        if self.enable_metrics:
            data_quality_checks_total.labels(tag_id=tag_id, result=quality_level.value).inc()
            for issue in issues:
                data_quality_issues_total.labels(issue_type=issue.value).inc()

        # Annotate data point with quality info
        annotated = {
            **data_point,
            "quality": quality_level.value,
            "quality_issues": [i.value for i in issues] if issues else [],
            "quality_timestamp": datetime.now(timezone.utc).isoformat()
        }

        return quality_level, issues, annotated

    def validate_batch(self, data_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate a batch of data points.

        Args:
            data_points: List of data point dictionaries

        Returns:
            List of annotated data points with quality information
        """
        annotated_points = []

        for point in data_points:
            _, _, annotated = self.validate(point)
            annotated_points.append(annotated)

        # Log summary
        good_count = sum(1 for p in annotated_points if p.get("quality") == "good")
        uncertain_count = sum(1 for p in annotated_points if p.get("quality") == "uncertain")
        bad_count = sum(1 for p in annotated_points if p.get("quality") == "bad")

        if uncertain_count > 0 or bad_count > 0:
            logger.info(
                f"📊 Quality check: {len(data_points)} points - "
                f"✅ {good_count} good, ⚠️ {uncertain_count} uncertain, ❌ {bad_count} bad"
            )

        return annotated_points

    def _determine_quality_level(self, issues: List[QualityIssue]) -> QualityLevel:
        """Determine overall quality level from issues list."""
        if not issues:
            return QualityLevel.GOOD

        # Critical issues -> BAD
        critical = {QualityIssue.NULL_VALUE, QualityIssue.INVALID_TYPE, QualityIssue.FUTURE_TIMESTAMP}
        if any(i in critical for i in issues):
            return QualityLevel.BAD

        # Suspicious issues -> UNCERTAIN
        suspicious = {QualityIssue.OUT_OF_RANGE, QualityIssue.RATE_OF_CHANGE, QualityIssue.FROZEN_VALUE, QualityIssue.STALE_TIMESTAMP}
        if any(i in suspicious for i in issues):
            return QualityLevel.UNCERTAIN

        return QualityLevel.GOOD

    def get_frozen_tags(self) -> List[str]:
        """Get list of currently frozen tags."""
        frozen = []
        now = datetime.now(timezone.utc)

        for tag_id, state in self._tag_states.items():
            if state.last_change_timestamp:
                config = self._tag_configs.get(tag_id)
                frozen_timeout = config.frozen_timeout_s if config else self.default_frozen_timeout_s

                if (now - state.last_change_timestamp).total_seconds() > frozen_timeout:
                    frozen.append(tag_id)

        # Update Prometheus metric
        if self.enable_metrics:
            data_quality_frozen_tags.set(len(frozen))

        return frozen

    def get_statistics(self) -> Dict[str, Any]:
        """Get quality validation statistics."""
        total = self._total_checked or 1  # Avoid division by zero

        return {
            "total_checked": self._total_checked,
            "total_good": self._total_good,
            "total_uncertain": self._total_uncertain,
            "total_bad": self._total_bad,
            "good_rate": round(self._total_good / total * 100, 2),
            "uncertain_rate": round(self._total_uncertain / total * 100, 2),
            "bad_rate": round(self._total_bad / total * 100, 2),
            "issues_by_type": dict(self._issues_by_type),
            "frozen_tags": self.get_frozen_tags(),
            "configured_tags": len(self._tag_configs)
        }

    def reset_statistics(self):
        """Reset validation statistics."""
        self._total_checked = 0
        self._total_good = 0
        self._total_uncertain = 0
        self._total_bad = 0
        self._issues_by_type.clear()
        logger.info("📊 Quality statistics reset")


# Global singleton instance
_validator_instance: Optional[DataQualityValidator] = None


def get_data_quality_validator() -> DataQualityValidator:
    """Get global data quality validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = DataQualityValidator()
    return _validator_instance


def validate_data_quality(data_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convenience function to validate a batch of data points.

    Args:
        data_points: List of data point dictionaries

    Returns:
        List of annotated data points with quality information
    """
    validator = get_data_quality_validator()
    return validator.validate_batch(data_points)
