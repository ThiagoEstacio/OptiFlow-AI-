"""
Alarm Monitoring Service - Automatic Threshold Detection
Monitors simulator data and creates alarm events automatically
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.alarm import AlarmDefinition, AlarmEvent, AlarmSeverity, AlarmType, AlarmState
from app.models.tag import Tag
from app.services.lightweight_simulator import get_simulator

logger = logging.getLogger(__name__)


class AlarmMonitorService:
    """
    Service that monitors simulator values and triggers alarms
    based on defined thresholds
    """

    def __init__(self):
        self.is_running = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.check_interval = 2.0  # Check every 2 seconds
        self.active_alarms: Dict[str, str] = {}  # tag_id -> alarm_event_id

    async def start(self, db: AsyncSession):
        """Start the alarm monitoring service"""
        if self.is_running:
            logger.warning("Alarm monitor already running")
            return

        # Recover active alarms from database before starting
        await self._recover_active_alarms(db)

        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop(db))
        logger.info("🚨 Alarm monitoring service started")

    async def stop(self):
        """Stop the alarm monitoring service"""
        if not self.is_running:
            return

        self.is_running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️  Alarm monitoring service stopped")

    async def _recover_active_alarms(self, db: AsyncSession):
        """
        Recover active alarms from database on startup.
        This ensures alarm state is preserved across restarts.
        """
        try:
            # Query all active and acknowledged alarms from database
            result = await db.execute(
                select(AlarmEvent, AlarmDefinition)
                .join(AlarmDefinition, AlarmEvent.definition_id == AlarmDefinition.id)
                .where(
                    AlarmEvent.state.in_([AlarmState.ACTIVE, AlarmState.ACKNOWLEDGED])
                )
            )
            active_events = result.all()

            # Rebuild active_alarms dictionary
            recovered_count = 0
            for alarm_event, alarm_def in active_events:
                alarm_key = f"{alarm_def.tag_id}_{alarm_def.id}"
                self.active_alarms[alarm_key] = str(alarm_event.id)
                recovered_count += 1

            if recovered_count > 0:
                logger.info(
                    f"✅ Recovered {recovered_count} active alarm(s) from database"
                )
            else:
                logger.info("ℹ️  No active alarms to recover")

        except Exception as e:
            logger.error(f"❌ Error recovering active alarms: {e}", exc_info=True)

    async def _monitor_loop(self, db: AsyncSession):
        """Main monitoring loop"""
        try:
            while self.is_running:
                await self._check_alarms(db)
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            logger.info("Alarm monitor loop cancelled")
        except Exception as e:
            logger.error(f"Error in alarm monitor loop: {e}", exc_info=True)
            self.is_running = False

    async def _check_alarms(self, db: AsyncSession):
        """Check all alarm definitions against current simulator values"""
        try:
            # Get simulator instance
            sim = get_simulator()
            if not sim or not sim.running:
                return

            # Get all tags
            all_tags = sim.get_all_tags()

            # Get all enabled alarm definitions
            result = await db.execute(
                select(AlarmDefinition)
                .where(AlarmDefinition.is_active == True)
            )
            alarm_defs = result.scalars().all()

            for alarm_def in alarm_defs:
                await self._check_single_alarm(db, alarm_def, all_tags)

            await db.commit()

        except Exception as e:
            logger.error(f"Error checking alarms: {e}", exc_info=True)
            await db.rollback()

    async def _check_single_alarm(
        self,
        db: AsyncSession,
        alarm_def: AlarmDefinition,
        all_tags: Dict[str, float]
    ):
        """Check a single alarm definition"""
        try:
            # Get tag from alarm definition
            tag_result = await db.execute(
                select(Tag).where(Tag.id == alarm_def.tag_id)
            )
            tag = tag_result.scalar_one_or_none()

            if not tag:
                return

            # Get current value from simulator
            tag_value = all_tags.get(tag.name)
            if tag_value is None:
                return

            # Check if alarm should be triggered
            is_alarmed = self._evaluate_alarm(alarm_def, tag_value)
            alarm_key = f"{tag.id}_{alarm_def.id}"

            if is_alarmed and alarm_key not in self.active_alarms:
                # Create new alarm event
                alarm_event = await self._create_alarm_event(
                    db, alarm_def, tag, tag_value
                )
                self.active_alarms[alarm_key] = str(alarm_event.id)
                logger.warning(
                    f"🚨 ALARM TRIGGERED: {alarm_def.name} - {tag.name} = {tag_value}"
                )

            elif not is_alarmed and alarm_key in self.active_alarms:
                # Clear alarm event
                alarm_event_id = self.active_alarms[alarm_key]
                await self._clear_alarm_event(db, alarm_event_id)
                del self.active_alarms[alarm_key]
                logger.info(
                    f"✅ ALARM CLEARED: {alarm_def.name} - {tag.name} = {tag_value}"
                )

        except Exception as e:
            logger.error(f"Error checking alarm {alarm_def.name}: {e}")

    def _evaluate_alarm(self, alarm_def: AlarmDefinition, value: float) -> bool:
        """Evaluate if alarm condition is met"""
        alarm_type = alarm_def.alarm_type

        if alarm_type == AlarmType.HIGH_LIMIT:
            return value > alarm_def.high_limit

        elif alarm_type == AlarmType.LOW_LIMIT:
            return value < alarm_def.low_limit

        elif alarm_type == AlarmType.HIGH_HIGH_LIMIT:
            return value > alarm_def.high_high_limit

        elif alarm_type == AlarmType.LOW_LOW_LIMIT:
            return value < alarm_def.low_low_limit

        elif alarm_type == AlarmType.RATE_OF_CHANGE:
            # TODO: Implement rate of change detection
            return False

        elif alarm_type == AlarmType.DEVIATION:
            # Check deviation from setpoint
            if alarm_def.setpoint is not None and alarm_def.deviation_limit is not None:
                deviation = abs(value - alarm_def.setpoint)
                return deviation > alarm_def.deviation_limit
            return False

        return False

    async def _create_alarm_event(
        self,
        db: AsyncSession,
        alarm_def: AlarmDefinition,
        tag: Tag,
        value: float
    ) -> AlarmEvent:
        """Create a new alarm event"""

        # Determine limit that was exceeded
        limit = 0.0
        if alarm_def.alarm_type == AlarmType.HIGH_LIMIT:
            limit = alarm_def.high_limit
        elif alarm_def.alarm_type == AlarmType.LOW_LIMIT:
            limit = alarm_def.low_limit
        elif alarm_def.alarm_type == AlarmType.HIGH_HIGH_LIMIT:
            limit = alarm_def.high_high_limit
        elif alarm_def.alarm_type == AlarmType.LOW_LOW_LIMIT:
            limit = alarm_def.low_low_limit

        # Create message
        message = (
            f"{alarm_def.name}: {tag.name} = {value:.2f} "
            f"(limit: {limit:.2f})"
        )

        # Create alarm event
        alarm_event = AlarmEvent(
            definition_id=alarm_def.id,
            state=AlarmState.ACTIVE,
            trigger_value=value,
            trigger_timestamp=datetime.utcnow(),
            event_metadata={
                "tag_name": tag.name,
                "severity": alarm_def.severity.value,
                "alarm_type": alarm_def.alarm_type.value,
                "limit": limit,
                "message": message
            }
        )

        db.add(alarm_event)
        await db.flush()

        return alarm_event

    async def _clear_alarm_event(self, db: AsyncSession, alarm_event_id: str):
        """Clear an active alarm event"""
        result = await db.execute(
            select(AlarmEvent).where(AlarmEvent.id == alarm_event_id)
        )
        alarm_event = result.scalar_one_or_none()

        if alarm_event and alarm_event.state == AlarmState.ACTIVE:
            alarm_event.state = AlarmState.CLEARED
            alarm_event.cleared_at = datetime.utcnow()
            alarm_event.clear_value = alarm_event.trigger_value  # Store clear value
            db.add(alarm_event)
            await db.flush()


# Global instance
_alarm_monitor_service: Optional[AlarmMonitorService] = None


def get_alarm_monitor_service() -> AlarmMonitorService:
    """Get the global alarm monitor service instance"""
    global _alarm_monitor_service
    if _alarm_monitor_service is None:
        _alarm_monitor_service = AlarmMonitorService()
    return _alarm_monitor_service
