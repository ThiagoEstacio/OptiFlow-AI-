"""
Communication Monitor Service - CORR-003
=========================================

Detects communication loss vs actual zero values.
This is critical for distinguishing between:
- Tag value = 0 (valid sensor reading)
- Tag value = 0 because communication was lost (invalid!)

The distinction is crucial for operators to make correct decisions.

Features:
1. Track last successful communication per adapter
2. Detect stale/frozen values
3. Mark tags with communication issues
4. Distinguish zero value from communication loss
5. Report communication health metrics

Sprint 1 Task: CORR-003 - No detection of communication loss vs zero value
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class CommunicationState(Enum):
    """State of communication with a device/adapter"""
    HEALTHY = "healthy"           # Normal operation
    DEGRADED = "degraded"         # Some tags not responding
    STALE = "stale"               # No updates for a while
    LOST = "lost"                 # Communication completely lost
    UNKNOWN = "unknown"           # Initial state


class ValueSource(Enum):
    """Indicates the source/validity of a value"""
    REAL = "real"                 # Fresh value from device
    CACHED = "cached"             # Valid but from cache
    STALE = "stale"               # Old value, may not reflect reality
    COMMUNICATION_LOSS = "comm_loss"  # Value is 0/null due to comm loss
    UNKNOWN = "unknown"           # Cannot determine


@dataclass
class TagCommunicationState:
    """Tracks communication state for a single tag"""
    tag_id: str
    adapter_id: str
    last_successful_read: Optional[datetime] = None
    last_value: Optional[Any] = None
    consecutive_failures: int = 0
    consecutive_same_values: int = 0
    quality: str = "Unknown"
    source: ValueSource = ValueSource.UNKNOWN

    def update_success(self, value: Any, timestamp: datetime):
        """Record a successful read"""
        # Check if value changed
        if self.last_value is not None and value == self.last_value:
            self.consecutive_same_values += 1
        else:
            self.consecutive_same_values = 0

        self.last_successful_read = timestamp
        self.last_value = value
        self.consecutive_failures = 0
        self.quality = "Good"
        self.source = ValueSource.REAL

    def update_failure(self):
        """Record a failed read"""
        self.consecutive_failures += 1
        self.quality = "Bad"
        self.source = ValueSource.COMMUNICATION_LOSS

    def is_stale(self, threshold_seconds: float = 30.0) -> bool:
        """Check if value is stale (no updates for threshold)"""
        if self.last_successful_read is None:
            return True

        age = (datetime.now(timezone.utc) - self.last_successful_read).total_seconds()
        return age > threshold_seconds

    def is_frozen(self, threshold_count: int = 10) -> bool:
        """Check if value appears frozen (same value too many times)"""
        return self.consecutive_same_values >= threshold_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tag_id": self.tag_id,
            "adapter_id": self.adapter_id,
            "last_successful_read": self.last_successful_read.isoformat() if self.last_successful_read else None,
            "last_value": self.last_value,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_same_values": self.consecutive_same_values,
            "quality": self.quality,
            "source": self.source.value,
            "is_stale": self.is_stale(),
            "is_frozen": self.is_frozen()
        }


@dataclass
class AdapterCommunicationState:
    """Tracks communication state for an adapter"""
    adapter_id: str
    state: CommunicationState = CommunicationState.UNKNOWN
    last_successful_connection: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    consecutive_failures: int = 0
    total_tags: int = 0
    responsive_tags: int = 0
    stale_tags: int = 0
    error_message: Optional[str] = None

    def update_heartbeat(self):
        """Record a heartbeat"""
        self.last_heartbeat = datetime.now(timezone.utc)

    def calculate_state(self) -> CommunicationState:
        """Calculate overall state based on metrics"""
        if self.total_tags == 0:
            return CommunicationState.UNKNOWN

        responsive_ratio = self.responsive_tags / self.total_tags if self.total_tags > 0 else 0

        if responsive_ratio >= 0.95:
            return CommunicationState.HEALTHY
        elif responsive_ratio >= 0.5:
            return CommunicationState.DEGRADED
        elif responsive_ratio > 0:
            return CommunicationState.STALE
        else:
            return CommunicationState.LOST

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "state": self.state.value,
            "last_successful_connection": self.last_successful_connection.isoformat() if self.last_successful_connection else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "consecutive_failures": self.consecutive_failures,
            "total_tags": self.total_tags,
            "responsive_tags": self.responsive_tags,
            "stale_tags": self.stale_tags,
            "health_percentage": round((self.responsive_tags / self.total_tags * 100) if self.total_tags > 0 else 0, 1),
            "error_message": self.error_message
        }


class CommunicationMonitor:
    """
    Monitors communication health and distinguishes between
    zero values and communication loss.

    CORR-003: Critical for data integrity - operators need to know
    if a "0" means the sensor reads 0 or if communication is lost!
    """

    def __init__(
        self,
        stale_threshold_seconds: float = 30.0,
        frozen_threshold_count: int = 10,
        heartbeat_interval_seconds: float = 5.0
    ):
        """
        Initialize communication monitor.

        Args:
            stale_threshold_seconds: Time without update before marking stale
            frozen_threshold_count: Consecutive same values before marking frozen
            heartbeat_interval_seconds: Expected interval between heartbeats
        """
        self.stale_threshold = stale_threshold_seconds
        self.frozen_threshold = frozen_threshold_count
        self.heartbeat_interval = heartbeat_interval_seconds

        # State tracking
        self._tag_states: Dict[str, TagCommunicationState] = {}
        self._adapter_states: Dict[str, AdapterCommunicationState] = {}

        # Statistics
        self._stats = {
            "total_updates": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "comm_loss_detected": 0,
            "stale_values_detected": 0
        }

        logger.info("📡 CommunicationMonitor initialized")
        logger.info(f"   Stale threshold: {stale_threshold_seconds}s")
        logger.info(f"   Frozen threshold: {frozen_threshold_count} samples")

    def record_successful_read(
        self,
        tag_id: str,
        adapter_id: str,
        value: Any,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Record a successful tag read.

        Returns annotation dict to be added to data point.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Ensure timestamp is timezone-aware
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        # Get or create tag state
        if tag_id not in self._tag_states:
            self._tag_states[tag_id] = TagCommunicationState(
                tag_id=tag_id,
                adapter_id=adapter_id
            )

        tag_state = self._tag_states[tag_id]
        tag_state.update_success(value, timestamp)

        # Update adapter state
        self._update_adapter_state(adapter_id, success=True)

        # Update stats
        self._stats["total_updates"] += 1
        self._stats["successful_updates"] += 1

        # Return annotations
        return {
            "comm_state": "healthy",
            "value_source": ValueSource.REAL.value,
            "comm_quality": "Good",
            "is_stale": False,
            "is_comm_loss": False
        }

    def record_failed_read(
        self,
        tag_id: str,
        adapter_id: str,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record a failed tag read.

        Returns annotation dict indicating communication loss.
        """
        # Get or create tag state
        if tag_id not in self._tag_states:
            self._tag_states[tag_id] = TagCommunicationState(
                tag_id=tag_id,
                adapter_id=adapter_id
            )

        tag_state = self._tag_states[tag_id]
        tag_state.update_failure()

        # Update adapter state
        self._update_adapter_state(adapter_id, success=False, error=error)

        # Update stats
        self._stats["total_updates"] += 1
        self._stats["failed_updates"] += 1
        self._stats["comm_loss_detected"] += 1

        # Return annotations
        return {
            "comm_state": "lost",
            "value_source": ValueSource.COMMUNICATION_LOSS.value,
            "comm_quality": "Bad",
            "is_stale": True,
            "is_comm_loss": True,
            "comm_error": error
        }

    def annotate_value(
        self,
        tag_id: str,
        adapter_id: str,
        value: Any,
        timestamp: Optional[datetime] = None,
        raw_quality: str = "Good"
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Annotate a value with communication status.

        This is the main method for distinguishing zero values from comm loss.

        Args:
            tag_id: Tag identifier
            adapter_id: Adapter identifier
            value: The value to annotate
            timestamp: When the value was read
            raw_quality: Quality from the device

        Returns:
            Tuple of (annotations_dict, is_valid)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Ensure timestamp is timezone-aware
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        # Check if this looks like communication loss
        is_comm_loss = False
        value_source = ValueSource.REAL

        # Case 1: Quality is bad from device
        if raw_quality.lower() in ['bad', 'error', 'comm_loss', 'uncertain']:
            is_comm_loss = raw_quality.lower() in ['bad', 'comm_loss']
            value_source = ValueSource.COMMUNICATION_LOSS if is_comm_loss else ValueSource.CACHED

        # Case 2: Check if value is stale
        tag_state = self._tag_states.get(tag_id)
        if tag_state and tag_state.is_stale(self.stale_threshold):
            value_source = ValueSource.STALE
            self._stats["stale_values_detected"] += 1

        # Case 3: Value is None/null
        if value is None:
            is_comm_loss = True
            value_source = ValueSource.COMMUNICATION_LOSS

        # Case 4: Check for suspicious zero pattern
        # If value suddenly went to 0 and quality degraded, might be comm loss
        if value == 0 and tag_state and tag_state.last_value is not None:
            if tag_state.last_value != 0 and raw_quality.lower() != 'good':
                # Suspicious - value dropped to 0 with non-good quality
                value_source = ValueSource.CACHED
                logger.warning(
                    f"⚠️  Tag {tag_id}: Value dropped to 0 with quality '{raw_quality}' "
                    f"(previous: {tag_state.last_value}) - possible comm issue"
                )

        # Record the read
        if is_comm_loss:
            annotations = self.record_failed_read(tag_id, adapter_id)
        else:
            annotations = self.record_successful_read(tag_id, adapter_id, value, timestamp)

        # Override value_source if we detected something specific
        annotations["value_source"] = value_source.value
        annotations["is_comm_loss"] = is_comm_loss

        # Add helper fields
        annotations["value_is_zero"] = value == 0
        annotations["zero_is_real"] = value == 0 and not is_comm_loss

        return annotations, not is_comm_loss

    def _update_adapter_state(
        self,
        adapter_id: str,
        success: bool,
        error: Optional[str] = None
    ):
        """Update adapter-level state"""
        if adapter_id not in self._adapter_states:
            self._adapter_states[adapter_id] = AdapterCommunicationState(
                adapter_id=adapter_id
            )

        state = self._adapter_states[adapter_id]

        if success:
            state.last_successful_connection = datetime.now(timezone.utc)
            state.consecutive_failures = 0
            state.error_message = None
        else:
            state.consecutive_failures += 1
            state.error_message = error

        # Recalculate state
        self._recalculate_adapter_metrics(adapter_id)

    def _recalculate_adapter_metrics(self, adapter_id: str):
        """Recalculate adapter metrics from tag states"""
        state = self._adapter_states.get(adapter_id)
        if not state:
            return

        # Count tags for this adapter
        adapter_tags = [
            t for t in self._tag_states.values()
            if t.adapter_id == adapter_id
        ]

        state.total_tags = len(adapter_tags)
        state.responsive_tags = sum(1 for t in adapter_tags if not t.is_stale())
        state.stale_tags = sum(1 for t in adapter_tags if t.is_stale())
        state.state = state.calculate_state()

    def get_tag_state(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of a tag"""
        state = self._tag_states.get(tag_id)
        return state.to_dict() if state else None

    def get_adapter_state(self, adapter_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of an adapter"""
        state = self._adapter_states.get(adapter_id)
        return state.to_dict() if state else None

    def get_all_stale_tags(self) -> List[Dict[str, Any]]:
        """Get all tags with stale values"""
        return [
            t.to_dict() for t in self._tag_states.values()
            if t.is_stale()
        ]

    def get_all_comm_loss_tags(self) -> List[Dict[str, Any]]:
        """Get all tags with communication loss"""
        return [
            t.to_dict() for t in self._tag_states.values()
            if t.source == ValueSource.COMMUNICATION_LOSS
        ]

    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall communication health summary"""
        total_tags = len(self._tag_states)
        healthy_tags = sum(1 for t in self._tag_states.values() if t.source == ValueSource.REAL)
        stale_tags = sum(1 for t in self._tag_states.values() if t.is_stale())
        comm_loss_tags = sum(1 for t in self._tag_states.values() if t.source == ValueSource.COMMUNICATION_LOSS)

        # Adapter summary
        adapter_summary = {
            adapter_id: state.to_dict()
            for adapter_id, state in self._adapter_states.items()
        }

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_tags_monitored": total_tags,
            "healthy_tags": healthy_tags,
            "stale_tags": stale_tags,
            "comm_loss_tags": comm_loss_tags,
            "health_percentage": round((healthy_tags / total_tags * 100) if total_tags > 0 else 0, 1),
            "statistics": self._stats,
            "adapters": adapter_summary,
            "configuration": {
                "stale_threshold_seconds": self.stale_threshold,
                "frozen_threshold_count": self.frozen_threshold,
                "heartbeat_interval_seconds": self.heartbeat_interval
            }
        }

    def reset_statistics(self):
        """Reset statistics counters"""
        self._stats = {
            "total_updates": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "comm_loss_detected": 0,
            "stale_values_detected": 0
        }
        logger.info("📡 Communication statistics reset")


# Global singleton
_monitor_instance: Optional[CommunicationMonitor] = None


def get_communication_monitor() -> CommunicationMonitor:
    """Get global communication monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = CommunicationMonitor()
    return _monitor_instance


def annotate_data_point(
    tag_id: str,
    adapter_id: str,
    value: Any,
    timestamp: Optional[datetime] = None,
    quality: str = "Good"
) -> Dict[str, Any]:
    """
    Convenience function to annotate a data point with communication status.

    CORR-003: Use this function in the data pipeline to annotate all values.

    Args:
        tag_id: Tag identifier
        adapter_id: Adapter identifier
        value: The value
        timestamp: When the value was read
        quality: Quality from device

    Returns:
        Dict with annotations including:
        - comm_state: healthy/degraded/lost
        - value_source: real/cached/stale/comm_loss
        - is_comm_loss: bool
        - zero_is_real: bool (True if value is 0 and communication is good)
    """
    monitor = get_communication_monitor()
    annotations, is_valid = monitor.annotate_value(
        tag_id=tag_id,
        adapter_id=adapter_id,
        value=value,
        timestamp=timestamp,
        raw_quality=quality
    )
    return annotations
