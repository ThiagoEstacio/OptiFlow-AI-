"""
Alarm Evaluator Service for Gateway Edge
=========================================

Evaluates alarm conditions for managed tags and publishes alarm events to Kafka.
This is the ONLY source of alarms in the architecture - Backend does NOT evaluate alarms.

Architecture:
  Gateway Tags → Alarm Evaluator → Kafka (topic: alarm_events) → Backend Consumer → Database

Alarm Types Supported:
- HIGH_HIGH_LIMIT: Critical high threshold
- HIGH_LIMIT: Warning high threshold
- LOW_LIMIT: Warning low threshold
- LOW_LOW_LIMIT: Critical low threshold
- DEVIATION: Deviation from setpoint
- RATE_OF_CHANGE: Value changing too fast
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Set
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)


class AlarmSeverity(str, Enum):
    """Alarm severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlarmType(str, Enum):
    """Alarm types"""
    HIGH_HIGH_LIMIT = "high_high_limit"
    HIGH_LIMIT = "high_limit"
    LOW_LIMIT = "low_limit"
    LOW_LOW_LIMIT = "low_low_limit"
    DEVIATION = "deviation"
    RATE_OF_CHANGE = "rate_of_change"


class AlarmState(str, Enum):
    """Alarm states"""
    ACTIVE = "active"
    CLEARED = "cleared"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class AlarmEvent:
    """Alarm event data structure"""
    event_id: str
    tag_id: str
    tag_name: str
    alarm_type: str
    severity: str
    state: str
    message: str
    trigger_value: float
    threshold_value: float
    timestamp: str
    gateway_id: str
    adapter_id: str

    # Optional fields
    acknowledged_at: Optional[str] = None
    acknowledged_by: Optional[str] = None
    cleared_at: Optional[str] = None
    clear_value: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Kafka serialization"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AlarmConfig:
    """Alarm configuration from tags_config.json"""
    enabled: bool = False
    hi_hi: Optional[float] = None
    hi_hi_severity: str = "critical"
    hi: Optional[float] = None
    hi_severity: str = "high"
    lo: Optional[float] = None
    lo_severity: str = "high"
    lo_lo: Optional[float] = None
    lo_lo_severity: str = "critical"
    deadband: float = 0.0
    delay_seconds: int = 0
    message_template: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlarmConfig':
        """Create from dictionary"""
        if not data:
            return cls()
        return cls(
            enabled=data.get('enabled', False),
            hi_hi=data.get('hi_hi') or data.get('high_high_limit'),
            hi_hi_severity=data.get('hi_hi_severity', 'critical'),
            hi=data.get('hi') or data.get('high_limit'),
            hi_severity=data.get('hi_severity', 'high'),
            lo=data.get('lo') or data.get('low_limit'),
            lo_severity=data.get('lo_severity', 'high'),
            lo_lo=data.get('lo_lo') or data.get('low_low_limit'),
            lo_lo_severity=data.get('lo_lo_severity', 'critical'),
            deadband=data.get('deadband', 0.0),
            delay_seconds=data.get('delay_seconds', 0),
            message_template=data.get('message_template')
        )


class AlarmEvaluatorService:
    """
    Service that evaluates alarm conditions for Gateway tags

    Features:
    - Evaluates alarm thresholds from tags_config.json
    - Supports deadband to prevent alarm chatter
    - Supports delay before triggering alarm
    - Publishes alarm events to Kafka
    - Tracks active alarms to detect state changes
    """

    def __init__(
        self,
        gateway_id: str,
        kafka_producer=None,
        config_path: str = "/app/config/tags_config.json"
    ):
        self.gateway_id = gateway_id
        self.kafka_producer = kafka_producer
        self.config_path = Path(config_path)

        # Active alarms: {tag_id_alarm_type: AlarmEvent}
        self.active_alarms: Dict[str, AlarmEvent] = {}

        # Pending alarms waiting for delay: {tag_id_alarm_type: (timestamp, value)}
        self.pending_alarms: Dict[str, tuple] = {}

        # Previous values for rate of change: {tag_id: (timestamp, value)}
        self.previous_values: Dict[str, tuple] = {}

        # Statistics
        self.stats = {
            'evaluations': 0,
            'alarms_triggered': 0,
            'alarms_cleared': 0,
            'last_evaluation': None
        }

        self._running = False
        self._task: Optional[asyncio.Task] = None

        logger.info(f"🚨 AlarmEvaluatorService initialized for gateway {gateway_id}")

    def load_tag_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load tag configurations from tags_config.json"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Tags config not found: {self.config_path}")
                return {}

            with open(self.config_path, 'r') as f:
                config = json.load(f)

            tags = {}
            for tag in config.get('tags', []):
                if tag.get('enabled', True):
                    tags[tag.get('tag_id')] = tag

            return tags

        except Exception as e:
            logger.error(f"Error loading tag configs: {e}")
            return {}

    def evaluate_tag(
        self,
        tag_id: str,
        tag_name: str,
        value: float,
        adapter_id: str,
        alarm_config: AlarmConfig,
        advanced_alarms: List[Dict] = None
    ) -> List[AlarmEvent]:
        """
        Evaluate alarm conditions for a single tag

        Returns list of new alarm events (triggered or cleared)
        """
        events = []
        now = datetime.now(timezone.utc)
        timestamp = now.isoformat()

        # Check basic alarm config
        if alarm_config.enabled:
            events.extend(self._check_basic_alarms(
                tag_id, tag_name, value, adapter_id, alarm_config, timestamp
            ))

        # Check advanced alarms
        if advanced_alarms:
            for adv_alarm in advanced_alarms:
                if adv_alarm.get('enabled', False):
                    events.extend(self._check_advanced_alarm(
                        tag_id, tag_name, value, adapter_id, adv_alarm, timestamp
                    ))

        return events

    def _check_basic_alarms(
        self,
        tag_id: str,
        tag_name: str,
        value: float,
        adapter_id: str,
        config: AlarmConfig,
        timestamp: str
    ) -> List[AlarmEvent]:
        """Check basic HI/LO alarm thresholds"""
        events = []
        deadband = config.deadband or 0.0

        # Check HIGH_HIGH
        if config.hi_hi is not None:
            events.extend(self._check_threshold(
                tag_id, tag_name, value, adapter_id,
                AlarmType.HIGH_HIGH_LIMIT, config.hi_hi,
                config.hi_hi_severity, deadband, timestamp,
                is_high=True
            ))

        # Check HIGH
        if config.hi is not None:
            events.extend(self._check_threshold(
                tag_id, tag_name, value, adapter_id,
                AlarmType.HIGH_LIMIT, config.hi,
                config.hi_severity, deadband, timestamp,
                is_high=True
            ))

        # Check LOW
        if config.lo is not None:
            events.extend(self._check_threshold(
                tag_id, tag_name, value, adapter_id,
                AlarmType.LOW_LIMIT, config.lo,
                config.lo_severity, deadband, timestamp,
                is_high=False
            ))

        # Check LOW_LOW
        if config.lo_lo is not None:
            events.extend(self._check_threshold(
                tag_id, tag_name, value, adapter_id,
                AlarmType.LOW_LOW_LIMIT, config.lo_lo,
                config.lo_lo_severity, deadband, timestamp,
                is_high=False
            ))

        return events

    def _check_threshold(
        self,
        tag_id: str,
        tag_name: str,
        value: float,
        adapter_id: str,
        alarm_type: AlarmType,
        threshold: float,
        severity: str,
        deadband: float,
        timestamp: str,
        is_high: bool
    ) -> List[AlarmEvent]:
        """Check a single threshold and generate events"""
        events = []
        alarm_key = f"{tag_id}_{alarm_type.value}"

        # Determine if threshold is violated
        if is_high:
            is_violated = value > threshold
            is_cleared = value < (threshold - deadband)
        else:
            is_violated = value < threshold
            is_cleared = value > (threshold + deadband)

        # Check if alarm should trigger
        if is_violated and alarm_key not in self.active_alarms:
            # Create new alarm event
            event = AlarmEvent(
                event_id=str(uuid.uuid4()),
                tag_id=tag_id,
                tag_name=tag_name,
                alarm_type=alarm_type.value,
                severity=severity,
                state=AlarmState.ACTIVE.value,
                message=self._generate_message(tag_name, alarm_type, value, threshold),
                trigger_value=value,
                threshold_value=threshold,
                timestamp=timestamp,
                gateway_id=self.gateway_id,
                adapter_id=adapter_id
            )

            self.active_alarms[alarm_key] = event
            self.stats['alarms_triggered'] += 1
            events.append(event)

            logger.warning(
                f"🚨 ALARM TRIGGERED: {tag_name} - {alarm_type.value} "
                f"(value={value:.2f}, threshold={threshold:.2f})"
            )

        # Check if alarm should clear
        elif is_cleared and alarm_key in self.active_alarms:
            active_event = self.active_alarms[alarm_key]

            # Create cleared event
            cleared_event = AlarmEvent(
                event_id=active_event.event_id,
                tag_id=tag_id,
                tag_name=tag_name,
                alarm_type=alarm_type.value,
                severity=severity,
                state=AlarmState.CLEARED.value,
                message=f"{tag_name}: {alarm_type.value} alarm cleared",
                trigger_value=active_event.trigger_value,
                threshold_value=threshold,
                timestamp=active_event.timestamp,
                gateway_id=self.gateway_id,
                adapter_id=adapter_id,
                cleared_at=timestamp,
                clear_value=value
            )

            del self.active_alarms[alarm_key]
            self.stats['alarms_cleared'] += 1
            events.append(cleared_event)

            logger.info(
                f"✅ ALARM CLEARED: {tag_name} - {alarm_type.value} "
                f"(value={value:.2f})"
            )

        return events

    def _check_advanced_alarm(
        self,
        tag_id: str,
        tag_name: str,
        value: float,
        adapter_id: str,
        alarm_config: Dict,
        timestamp: str
    ) -> List[AlarmEvent]:
        """Check advanced alarm types (deviation, rate of change, etc.)"""
        events = []
        alarm_type = alarm_config.get('type', '').lower()

        if alarm_type == 'deviation':
            setpoint = alarm_config.get('setpoint', 0)
            limit = alarm_config.get('deviation_limit', 10)
            deviation = abs(value - setpoint)

            if deviation > limit:
                alarm_key = f"{tag_id}_deviation"
                if alarm_key not in self.active_alarms:
                    event = AlarmEvent(
                        event_id=str(uuid.uuid4()),
                        tag_id=tag_id,
                        tag_name=tag_name,
                        alarm_type=AlarmType.DEVIATION.value,
                        severity=alarm_config.get('severity', 'medium'),
                        state=AlarmState.ACTIVE.value,
                        message=f"{tag_name}: Deviation {deviation:.2f} exceeds limit {limit:.2f}",
                        trigger_value=value,
                        threshold_value=setpoint,
                        timestamp=timestamp,
                        gateway_id=self.gateway_id,
                        adapter_id=adapter_id
                    )
                    self.active_alarms[alarm_key] = event
                    events.append(event)

        elif alarm_type == 'rate_of_change':
            rate_limit = alarm_config.get('rate_limit', 10)  # units per second

            prev = self.previous_values.get(tag_id)
            if prev:
                prev_time, prev_value = prev
                time_diff = (datetime.fromisoformat(timestamp.replace('Z', '+00:00')) -
                            datetime.fromisoformat(prev_time.replace('Z', '+00:00'))).total_seconds()

                if time_diff > 0:
                    rate = abs(value - prev_value) / time_diff
                    if rate > rate_limit:
                        alarm_key = f"{tag_id}_rate_of_change"
                        if alarm_key not in self.active_alarms:
                            event = AlarmEvent(
                                event_id=str(uuid.uuid4()),
                                tag_id=tag_id,
                                tag_name=tag_name,
                                alarm_type=AlarmType.RATE_OF_CHANGE.value,
                                severity=alarm_config.get('severity', 'medium'),
                                state=AlarmState.ACTIVE.value,
                                message=f"{tag_name}: Rate of change {rate:.2f}/s exceeds {rate_limit:.2f}/s",
                                trigger_value=value,
                                threshold_value=rate_limit,
                                timestamp=timestamp,
                                gateway_id=self.gateway_id,
                                adapter_id=adapter_id
                            )
                            self.active_alarms[alarm_key] = event
                            events.append(event)

            self.previous_values[tag_id] = (timestamp, value)

        return events

    def _generate_message(
        self,
        tag_name: str,
        alarm_type: AlarmType,
        value: float,
        threshold: float
    ) -> str:
        """Generate alarm message"""
        type_labels = {
            AlarmType.HIGH_HIGH_LIMIT: "Critical high",
            AlarmType.HIGH_LIMIT: "High",
            AlarmType.LOW_LIMIT: "Low",
            AlarmType.LOW_LOW_LIMIT: "Critical low"
        }

        label = type_labels.get(alarm_type, alarm_type.value)
        return f"{tag_name}: {label} alarm - Value {value:.2f} {'>' if 'high' in alarm_type.value else '<'} {threshold:.2f}"

    async def publish_alarm_events(self, events: List[AlarmEvent]) -> bool:
        """Publish alarm events to Kafka"""
        if not events:
            return True

        if not self.kafka_producer:
            logger.warning("⚠️ Kafka producer not available - alarm events will be logged only")
            for event in events:
                logger.info(f"ALARM EVENT: {event.to_dict()}")
            return False

        try:
            messages = [
                {
                    'event_type': 'alarm',
                    'gateway_id': self.gateway_id,
                    **event.to_dict()
                }
                for event in events
            ]

            # Producer should already be configured for alarm_events topic
            result = await self.kafka_producer.publish(messages)

            if result:
                logger.info(f"✅ Published {len(events)} alarm events to Kafka (topic: {self.kafka_producer.topic})")

            return result

        except Exception as e:
            logger.error(f"❌ Failed to publish alarm events: {e}")
            return False

    async def evaluate_all_tags(self, protocol_manager) -> List[AlarmEvent]:
        """
        Evaluate all managed tags and return alarm events

        Args:
            protocol_manager: ProtocolManager instance with adapter values

        Returns:
            List of alarm events
        """
        all_events = []
        tag_configs = self.load_tag_configs()

        self.stats['evaluations'] += 1
        self.stats['last_evaluation'] = datetime.now(timezone.utc).isoformat()

        for tag_id, tag_config in tag_configs.items():
            tag_name = tag_config.get('tag_name', tag_id)
            adapter_id = tag_config.get('adapter_id')
            address = tag_config.get('address')

            # Get current value from adapter
            value = None
            if protocol_manager and adapter_id:
                adapter = protocol_manager.adapters.get(adapter_id)
                if adapter and hasattr(adapter, 'last_values'):
                    cached = adapter.last_values.get(address)
                    if cached:
                        value = cached.get('value')

            if value is None:
                continue

            # Skip non-numeric values
            if not isinstance(value, (int, float)):
                continue

            # Parse alarm configuration
            alarm_config = AlarmConfig.from_dict(tag_config.get('alarm') or {})
            advanced_alarms = tag_config.get('advanced_alarms', [])

            # Evaluate alarms
            events = self.evaluate_tag(
                tag_id=tag_id,
                tag_name=tag_name,
                value=float(value),
                adapter_id=adapter_id,
                alarm_config=alarm_config,
                advanced_alarms=advanced_alarms
            )

            all_events.extend(events)

        return all_events

    async def start(self, protocol_manager, interval_seconds: float = 2.0):
        """Start alarm evaluation loop"""
        if self._running:
            logger.warning("Alarm evaluator already running")
            return

        self._running = True
        self._task = asyncio.create_task(
            self._evaluation_loop(protocol_manager, interval_seconds)
        )
        logger.info(f"🚨 Alarm evaluator started (interval: {interval_seconds}s)")

    async def stop(self):
        """Stop alarm evaluation loop"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("🛑 Alarm evaluator stopped")

    async def _evaluation_loop(self, protocol_manager, interval_seconds: float):
        """Main evaluation loop"""
        try:
            while self._running:
                try:
                    events = await self.evaluate_all_tags(protocol_manager)

                    if events:
                        await self.publish_alarm_events(events)

                except Exception as e:
                    logger.error(f"Error in alarm evaluation: {e}", exc_info=True)

                await asyncio.sleep(interval_seconds)

        except asyncio.CancelledError:
            logger.info("Alarm evaluation loop cancelled")

    def get_active_alarms(self) -> List[Dict[str, Any]]:
        """Get list of currently active alarms"""
        return [alarm.to_dict() for alarm in self.active_alarms.values()]

    def get_statistics(self) -> Dict[str, Any]:
        """Get alarm evaluation statistics"""
        return {
            **self.stats,
            'active_count': len(self.active_alarms)
        }


# Singleton instance
_alarm_evaluator: Optional[AlarmEvaluatorService] = None


def get_alarm_evaluator(
    gateway_id: str = None,
    kafka_producer=None,
    config_path: str = "/app/config/tags_config.json"
) -> AlarmEvaluatorService:
    """Get or create alarm evaluator singleton"""
    global _alarm_evaluator

    if _alarm_evaluator is None:
        from app.core.config import settings
        gw_id = gateway_id or getattr(settings, 'GATEWAY_ID', 'gateway-001')
        _alarm_evaluator = AlarmEvaluatorService(
            gateway_id=gw_id,
            kafka_producer=kafka_producer,
            config_path=config_path
        )

    return _alarm_evaluator
