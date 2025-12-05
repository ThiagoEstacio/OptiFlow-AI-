"""
Quality Gate Service - CORR-004
===============================

Implements quality gates in the Kafka pipeline to ensure data integrity.

Quality gates can:
1. BLOCK: Reject bad quality data (prevent it from being stored)
2. FLAG: Allow data through but mark it with quality warnings
3. ALERT: Generate alarms when quality thresholds are exceeded

Sprint 1 Task: CORR-004 - Quality gates in Kafka pipeline

Quality Levels (ISA-95 compatible):
- GOOD: Value passes all quality checks
- UNCERTAIN: Value is suspicious but may be valid
- BAD: Value failed critical checks
- COMMUNICATION_LOSS: Value may be invalid due to comm loss
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class QualityGateAction(Enum):
    """Actions quality gates can take"""
    PASS = "pass"           # Allow data through unchanged
    FLAG = "flag"           # Allow but add warning flag
    BLOCK = "block"         # Reject the data point
    ALERT = "alert"         # Allow but generate alert


class QualityGateReason(Enum):
    """Reasons for quality gate decisions"""
    QUALITY_GOOD = "quality_good"
    QUALITY_BAD = "quality_bad"
    QUALITY_UNCERTAIN = "quality_uncertain"
    COMMUNICATION_LOSS = "communication_loss"
    VALUE_STALE = "value_stale"
    VALUE_OUT_OF_RANGE = "value_out_of_range"
    VALUE_FROZEN = "value_frozen"
    TIMESTAMP_INVALID = "timestamp_invalid"


@dataclass
class QualityGateConfig:
    """Configuration for quality gates"""
    # Enable/disable gates
    enabled: bool = True

    # Action for each quality level
    action_on_bad: QualityGateAction = QualityGateAction.FLAG
    action_on_uncertain: QualityGateAction = QualityGateAction.PASS
    action_on_comm_loss: QualityGateAction = QualityGateAction.FLAG
    action_on_stale: QualityGateAction = QualityGateAction.PASS

    # Thresholds
    stale_threshold_seconds: float = 300.0  # 5 minutes

    # Alert generation
    generate_alerts: bool = True
    alert_threshold_consecutive: int = 3  # Generate alert after N consecutive issues

    # Block mode (strict) vs Flag mode (permissive)
    strict_mode: bool = False  # If True, BLOCK bad quality; if False, FLAG only


@dataclass
class QualityGateResult:
    """Result from quality gate evaluation"""
    action: QualityGateAction
    reason: QualityGateReason
    passed: bool
    message: str
    original_quality: str
    annotated_quality: str
    should_alert: bool = False
    alert_message: Optional[str] = None


class QualityGateService:
    """
    Quality Gate Service - Evaluates data points against quality rules.

    CORR-004: This service ensures data integrity by:
    1. Evaluating quality annotations from Gateway
    2. Applying configurable rules (block/flag/alert)
    3. Tracking quality trends for alerting
    4. Providing quality statistics
    """

    def __init__(self, config: Optional[QualityGateConfig] = None):
        """
        Initialize quality gate service.

        Args:
            config: Quality gate configuration (uses defaults if not provided)
        """
        self.config = config or QualityGateConfig()

        # Statistics tracking
        self._stats = {
            "total_evaluated": 0,
            "passed": 0,
            "flagged": 0,
            "blocked": 0,
            "alerts_generated": 0
        }

        # Track consecutive issues per tag for alerting
        self._consecutive_issues: Dict[str, int] = defaultdict(int)

        # Quality distribution
        self._quality_counts: Dict[str, int] = defaultdict(int)

        logger.info("📊 QualityGateService initialized")
        logger.info(f"   Mode: {'STRICT' if self.config.strict_mode else 'PERMISSIVE'}")
        logger.info(f"   Action on BAD: {self.config.action_on_bad.value}")
        logger.info(f"   Action on COMM_LOSS: {self.config.action_on_comm_loss.value}")

    def evaluate(self, data_point: Dict[str, Any]) -> Tuple[QualityGateResult, Dict[str, Any]]:
        """
        Evaluate a data point against quality gates.

        Args:
            data_point: Dictionary containing tag data with quality annotations

        Returns:
            Tuple of (QualityGateResult, annotated_data_point)
        """
        if not self.config.enabled:
            return QualityGateResult(
                action=QualityGateAction.PASS,
                reason=QualityGateReason.QUALITY_GOOD,
                passed=True,
                message="Quality gates disabled",
                original_quality="unknown",
                annotated_quality="unknown"
            ), data_point

        self._stats["total_evaluated"] += 1

        tag_id = data_point.get("tag_id") or data_point.get("tag_name") or "unknown"

        # Extract quality information from data point
        quality = str(data_point.get("quality", "good")).lower()
        quality_issues = data_point.get("quality_issues", [])
        is_comm_loss = data_point.get("is_comm_loss", False)
        is_stale = data_point.get("is_stale", False)
        value_source = data_point.get("value_source", "real")

        # Track quality distribution
        self._quality_counts[quality] += 1

        # Determine action based on quality
        action = QualityGateAction.PASS
        reason = QualityGateReason.QUALITY_GOOD
        message = "Quality check passed"

        # === Check 1: Communication Loss ===
        if is_comm_loss or value_source == "comm_loss":
            action = self.config.action_on_comm_loss
            reason = QualityGateReason.COMMUNICATION_LOSS
            message = f"Communication loss detected for tag {tag_id}"

            if self.config.strict_mode:
                action = QualityGateAction.BLOCK

        # === Check 2: Bad Quality ===
        elif quality == "bad":
            action = self.config.action_on_bad
            reason = QualityGateReason.QUALITY_BAD
            message = f"Bad quality detected for tag {tag_id}: {quality_issues}"

            if self.config.strict_mode:
                action = QualityGateAction.BLOCK

        # === Check 3: Uncertain Quality ===
        elif quality == "uncertain":
            action = self.config.action_on_uncertain
            reason = QualityGateReason.QUALITY_UNCERTAIN
            message = f"Uncertain quality for tag {tag_id}: {quality_issues}"

        # === Check 4: Stale Data ===
        elif is_stale or value_source == "stale":
            action = self.config.action_on_stale
            reason = QualityGateReason.VALUE_STALE
            message = f"Stale value detected for tag {tag_id}"

        # Update statistics
        if action == QualityGateAction.PASS:
            self._stats["passed"] += 1
            self._consecutive_issues[tag_id] = 0
        elif action == QualityGateAction.FLAG:
            self._stats["flagged"] += 1
            self._consecutive_issues[tag_id] += 1
        elif action == QualityGateAction.BLOCK:
            self._stats["blocked"] += 1
            self._consecutive_issues[tag_id] += 1

        # Check if we should generate an alert
        should_alert = False
        alert_message = None

        if self.config.generate_alerts:
            consecutive = self._consecutive_issues[tag_id]
            if consecutive >= self.config.alert_threshold_consecutive:
                should_alert = True
                alert_message = (
                    f"Quality alert: Tag '{tag_id}' has had {consecutive} "
                    f"consecutive quality issues ({reason.value})"
                )
                self._stats["alerts_generated"] += 1
                logger.warning(f"🚨 {alert_message}")

        # Create result
        result = QualityGateResult(
            action=action,
            reason=reason,
            passed=(action != QualityGateAction.BLOCK),
            message=message,
            original_quality=quality,
            annotated_quality=self._get_annotated_quality(action, quality),
            should_alert=should_alert,
            alert_message=alert_message
        )

        # Annotate data point with quality gate results
        annotated = {
            **data_point,
            "quality_gate": {
                "action": action.value,
                "reason": reason.value,
                "passed": result.passed,
                "evaluated_at": datetime.now(timezone.utc).isoformat()
            }
        }

        # Log blocked data
        if action == QualityGateAction.BLOCK:
            logger.warning(f"🚫 BLOCKED: {message}")

        return result, annotated

    def evaluate_batch(
        self,
        data_points: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
        """
        Evaluate a batch of data points.

        Args:
            data_points: List of data point dictionaries

        Returns:
            Tuple of (passed_points, blocked_points, summary)
        """
        passed = []
        blocked = []
        summary = {
            "total": len(data_points),
            "passed": 0,
            "flagged": 0,
            "blocked": 0,
            "alerts": 0
        }

        for point in data_points:
            result, annotated = self.evaluate(point)

            if result.passed:
                passed.append(annotated)
                if result.action == QualityGateAction.FLAG:
                    summary["flagged"] += 1
                else:
                    summary["passed"] += 1
            else:
                blocked.append(annotated)
                summary["blocked"] += 1

            if result.should_alert:
                summary["alerts"] += 1

        # Log summary for batch
        if summary["blocked"] > 0 or summary["flagged"] > 0:
            logger.info(
                f"📊 Quality gate batch: {summary['total']} total, "
                f"✅ {summary['passed']} passed, "
                f"⚠️ {summary['flagged']} flagged, "
                f"🚫 {summary['blocked']} blocked"
            )

        return passed, blocked, summary

    def _get_annotated_quality(self, action: QualityGateAction, original: str) -> str:
        """Get annotated quality based on action"""
        if action == QualityGateAction.BLOCK:
            return "blocked"
        elif action == QualityGateAction.FLAG:
            return f"{original}_flagged"
        elif action == QualityGateAction.ALERT:
            return f"{original}_alerted"
        return original

    def get_statistics(self) -> Dict[str, Any]:
        """Get quality gate statistics"""
        total = self._stats["total_evaluated"] or 1

        return {
            "total_evaluated": self._stats["total_evaluated"],
            "passed": self._stats["passed"],
            "flagged": self._stats["flagged"],
            "blocked": self._stats["blocked"],
            "alerts_generated": self._stats["alerts_generated"],
            "pass_rate": round(self._stats["passed"] / total * 100, 2),
            "block_rate": round(self._stats["blocked"] / total * 100, 2),
            "quality_distribution": dict(self._quality_counts),
            "tags_with_issues": len([
                tag for tag, count in self._consecutive_issues.items()
                if count > 0
            ]),
            "config": {
                "strict_mode": self.config.strict_mode,
                "enabled": self.config.enabled
            }
        }

    def reset_statistics(self):
        """Reset statistics counters"""
        self._stats = {
            "total_evaluated": 0,
            "passed": 0,
            "flagged": 0,
            "blocked": 0,
            "alerts_generated": 0
        }
        self._consecutive_issues.clear()
        self._quality_counts.clear()
        logger.info("📊 Quality gate statistics reset")

    def set_strict_mode(self, enabled: bool):
        """Enable or disable strict mode"""
        self.config.strict_mode = enabled
        logger.info(f"📊 Quality gate mode: {'STRICT' if enabled else 'PERMISSIVE'}")

    def configure(self, **kwargs):
        """Update configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"📊 Quality gate config updated: {key}={value}")


# Global singleton
_quality_gate_instance: Optional[QualityGateService] = None


def get_quality_gate() -> QualityGateService:
    """Get global quality gate service instance"""
    global _quality_gate_instance
    if _quality_gate_instance is None:
        _quality_gate_instance = QualityGateService()
    return _quality_gate_instance


def evaluate_data_quality(data_point: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Convenience function to evaluate a data point's quality.

    CORR-004: Use this function in the Kafka consumer pipeline.

    Args:
        data_point: Dictionary with tag data and quality annotations

    Returns:
        Tuple of (should_process, annotated_data_point)
    """
    gate = get_quality_gate()
    result, annotated = gate.evaluate(data_point)
    return result.passed, annotated


def evaluate_batch_quality(
    data_points: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Convenience function to evaluate a batch of data points.

    Args:
        data_points: List of data point dictionaries

    Returns:
        Tuple of (points_to_process, blocked_points)
    """
    gate = get_quality_gate()
    passed, blocked, _ = gate.evaluate_batch(data_points)
    return passed, blocked
