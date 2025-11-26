"""
Kafka Consumer for Alarm Events from Gateway
=============================================

Consumes alarm events from Kafka 'alarm_events' topic and stores them in PostgreSQL.

Architecture:
  Gateway → Kafka (alarm_events) → This Consumer → PostgreSQL (alarm_events table)

The Gateway is the ONLY source of alarms:
- Gateway evaluates alarm conditions locally
- Publishes alarm events to Kafka
- This consumer stores them in the database
- Frontend reads from Backend API

This replaces the old alarm_monitor_service that read from the simulator.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import json

try:
    from aiokafka import AIOKafkaConsumer
    from aiokafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logging.warning("aiokafka not installed - Kafka consumer disabled")

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.alarm import AlarmDefinition, AlarmEvent, AlarmSeverity, AlarmType, AlarmState
from app.models.tag import Tag, TagDataType, TagCategory
from app.models.device import Device, DeviceProtocol, DeviceStatus

logger = logging.getLogger(__name__)


class AlarmEventConsumer:
    """
    Kafka consumer for alarm events from Gateway

    Receives alarm events and stores them in PostgreSQL for:
    - Historical record
    - Frontend display
    - Analytics and reporting
    """

    def __init__(
        self,
        topic: str = "alarm_events",
        group_id: str = "alarm-consumer-group",
        bootstrap_servers: str = None
    ):
        self.topic = topic
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers or getattr(
            settings, 'KAFKA_BOOTSTRAP_SERVERS', 'kafka-1:9092,kafka-2:9093,kafka-3:9096'
        )

        self.consumer: Optional[AIOKafkaConsumer] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Statistics
        self.stats = {
            'messages_received': 0,
            'alarms_stored': 0,
            'alarms_updated': 0,
            'errors': 0,
            'last_message_time': None
        }

        # Cache for alarm definitions (tag_id -> definition_id)
        self._definition_cache: Dict[str, str] = {}

        logger.info(f"🚨 AlarmEventConsumer initialized")
        logger.info(f"   Topic: {self.topic}")
        logger.info(f"   Group: {self.group_id}")
        logger.info(f"   Servers: {self.bootstrap_servers}")

    async def start(self):
        """Start consuming alarm events"""
        if not KAFKA_AVAILABLE:
            logger.warning("⚠️ Kafka not available - alarm consumer disabled")
            return

        if self._running:
            logger.warning("⚠️ Alarm consumer already running")
            return

        try:
            logger.info("🚀 Starting Alarm Event Consumer...")

            self.consumer = AIOKafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                auto_commit_interval_ms=5000
            )

            await self.consumer.start()
            self._running = True

            logger.info(f"✅ Alarm consumer started - listening to topic '{self.topic}'")

            # Start consume loop
            self._task = asyncio.create_task(self._consume_loop())

        except Exception as e:
            logger.error(f"❌ Failed to start alarm consumer: {e}", exc_info=True)
            self._running = False

    async def stop(self):
        """Stop consuming"""
        if not self._running:
            return

        logger.info("🛑 Stopping Alarm Event Consumer...")
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self.consumer:
            await self.consumer.stop()

        logger.info("✅ Alarm consumer stopped")
        logger.info(f"   Total received: {self.stats['messages_received']}")
        logger.info(f"   Stored: {self.stats['alarms_stored']}")
        logger.info(f"   Updated: {self.stats['alarms_updated']}")
        logger.info(f"   Errors: {self.stats['errors']}")

    async def _consume_loop(self):
        """Main consume loop"""
        try:
            async for message in self.consumer:
                if not self._running:
                    break

                try:
                    await self._process_message(message.value)
                except Exception as e:
                    logger.error(f"Error processing alarm message: {e}", exc_info=True)
                    self.stats['errors'] += 1

        except asyncio.CancelledError:
            logger.info("Consume loop cancelled")
        except Exception as e:
            logger.error(f"Error in consume loop: {e}", exc_info=True)

    async def _process_message(self, message: Dict[str, Any]):
        """Process a single alarm event message"""
        self.stats['messages_received'] += 1
        self.stats['last_message_time'] = datetime.now(timezone.utc).isoformat()

        event_type = message.get('event_type')
        if event_type != 'alarm':
            logger.debug(f"Ignoring non-alarm event type: {event_type}")
            return

        # Extract alarm data
        event_id = message.get('event_id')
        tag_id = message.get('tag_id')
        tag_name = message.get('tag_name')
        alarm_type = message.get('alarm_type')
        severity = message.get('severity')
        state = message.get('state')
        trigger_value = message.get('trigger_value')
        threshold_value = message.get('threshold_value')
        timestamp = message.get('timestamp')
        gateway_id = message.get('gateway_id')
        alarm_message = message.get('message', '')

        # Cleared info
        cleared_at = message.get('cleared_at')
        clear_value = message.get('clear_value')

        logger.info(
            f"📥 Received alarm event: {tag_name} - {alarm_type} ({state}) "
            f"from gateway {gateway_id}"
        )

        async with AsyncSessionLocal() as db:
            try:
                # Find or create the tag in the database
                db_tag = await self._get_or_create_tag(db, tag_id, tag_name, gateway_id)

                if not db_tag:
                    logger.warning(f"Could not find/create tag for alarm: {tag_name}")
                    return

                # Find or create alarm definition
                definition = await self._get_or_create_definition(
                    db, db_tag.id, tag_name, alarm_type, severity, threshold_value, alarm_message
                )

                if state == 'active':
                    # Create new alarm event
                    await self._create_alarm_event(
                        db, event_id, definition.id, trigger_value, timestamp, severity, alarm_message
                    )
                    self.stats['alarms_stored'] += 1

                elif state == 'cleared':
                    # Update existing alarm event as cleared
                    await self._clear_alarm_event(
                        db, event_id, cleared_at, clear_value
                    )
                    self.stats['alarms_updated'] += 1

                await db.commit()

            except Exception as e:
                logger.error(f"Error storing alarm event: {e}", exc_info=True)
                await db.rollback()
                self.stats['errors'] += 1

    async def _get_or_create_tag(
        self,
        db: AsyncSession,
        gateway_tag_id: str,
        tag_name: str,
        gateway_id: str
    ) -> Optional[Tag]:
        """Get or create tag in database"""
        # First try to find by name
        result = await db.execute(
            select(Tag).where(Tag.name == tag_name)
        )
        tag = result.scalar_one_or_none()

        if tag:
            return tag

        # Try to find by gateway tag ID stored in metadata
        result = await db.execute(
            select(Tag).where(Tag.description.contains(gateway_tag_id))
        )
        tag = result.scalar_one_or_none()

        if tag:
            return tag

        # Auto-create tag with Gateway device
        logger.info(f"Tag '{tag_name}' not found, creating automatically from Gateway alarm")

        # Find or create a Gateway device
        gateway_device = await self._get_or_create_gateway_device(db, gateway_id)

        if not gateway_device:
            logger.error(f"Could not create gateway device for {gateway_id}")
            return None

        # Create the tag
        new_tag = Tag(
            device_id=gateway_device.id,
            name=tag_name,
            description=f"Auto-created from Gateway alarm. Gateway tag ID: {gateway_tag_id}",
            is_active=True,
            address=f"gateway:{gateway_tag_id}",
            data_type=TagDataType.DOUBLE,
            category=TagCategory.ALARM,
            unit="%",  # Default unit
            scale=1.0,
            offset=0.0,
            scan_rate_ms=1000
        )

        db.add(new_tag)
        await db.flush()

        logger.info(f"✅ Created tag '{tag_name}' (id: {new_tag.id}) from Gateway alarm")
        return new_tag

    async def _get_or_create_gateway_device(
        self,
        db: AsyncSession,
        gateway_id: str
    ) -> Optional[Device]:
        """Get or create a device representing the Gateway"""
        device_name = f"Gateway-{gateway_id}"

        # Try to find existing Gateway device
        result = await db.execute(
            select(Device).where(Device.name == device_name)
        )
        device = result.scalar_one_or_none()

        if device:
            return device

        # Create new Gateway device
        logger.info(f"Creating Gateway device: {device_name}")

        new_device = Device(
            name=device_name,
            description=f"Gateway device for edge data collection (ID: {gateway_id})",
            protocol=DeviceProtocol.HTTP,  # Gateway uses HTTP API
            connection_config={
                "type": "gateway",
                "gateway_id": gateway_id,
                "endpoint": f"http://optiflow-gateway:8080",
                "description": "Edge gateway for industrial data collection"
            },
            is_active=True,
            status=DeviceStatus.CONNECTED
        )

        db.add(new_device)
        await db.flush()

        logger.info(f"✅ Created Gateway device: {device_name} (id: {new_device.id})")
        return new_device

    async def _get_or_create_definition(
        self,
        db: AsyncSession,
        tag_id: UUID,
        tag_name: str,
        alarm_type: str,
        severity: str,
        threshold_value: float,
        message: str
    ) -> AlarmDefinition:
        """Get or create alarm definition"""
        cache_key = f"{tag_id}_{alarm_type}"

        # Check cache
        if cache_key in self._definition_cache:
            result = await db.execute(
                select(AlarmDefinition).where(
                    AlarmDefinition.id == self._definition_cache[cache_key]
                )
            )
            definition = result.scalar_one_or_none()
            if definition:
                return definition

        # Try to find existing definition
        result = await db.execute(
            select(AlarmDefinition).where(
                AlarmDefinition.tag_id == tag_id,
                AlarmDefinition.alarm_type == self._map_alarm_type(alarm_type)
            )
        )
        definition = result.scalar_one_or_none()

        if definition:
            self._definition_cache[cache_key] = str(definition.id)
            return definition

        # Create new definition
        logger.info(f"Creating alarm definition for {tag_name}: {alarm_type}")

        new_definition = AlarmDefinition(
            tag_id=tag_id,
            name=f"{tag_name} - {alarm_type.replace('_', ' ').title()}",
            description=message or f"Auto-created from Gateway alarm",
            alarm_type=self._map_alarm_type(alarm_type),
            severity=self._map_severity(severity),
            high_limit=threshold_value if 'high' in alarm_type else None,
            low_limit=threshold_value if 'low' in alarm_type else None,
            deadband=0.0,
            delay_seconds=0,
            is_active=True
        )

        db.add(new_definition)
        await db.flush()

        self._definition_cache[cache_key] = str(new_definition.id)
        return new_definition

    async def _create_alarm_event(
        self,
        db: AsyncSession,
        event_id: str,
        definition_id: UUID,
        trigger_value: float,
        timestamp: str,
        severity: str,
        message: str
    ):
        """Create new alarm event in database"""
        # Parse timestamp
        try:
            trigger_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            trigger_time = datetime.now(timezone.utc)

        # Check if event already exists
        result = await db.execute(
            select(AlarmEvent).where(AlarmEvent.id == event_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.debug(f"Alarm event {event_id} already exists, skipping")
            return

        new_event = AlarmEvent(
            id=event_id,
            definition_id=definition_id,
            state=AlarmState.ACTIVE,
            trigger_value=trigger_value,
            trigger_timestamp=trigger_time
        )

        db.add(new_event)
        logger.info(f"✅ Stored alarm event: {event_id[:8]}...")

    async def _clear_alarm_event(
        self,
        db: AsyncSession,
        event_id: str,
        cleared_at: str,
        clear_value: float
    ):
        """Update alarm event as cleared"""
        result = await db.execute(
            select(AlarmEvent).where(AlarmEvent.id == event_id)
        )
        event = result.scalar_one_or_none()

        if not event:
            logger.warning(f"Alarm event {event_id} not found for clearing")
            return

        # Parse cleared timestamp
        try:
            clear_time = datetime.fromisoformat(cleared_at.replace('Z', '+00:00'))
        except:
            clear_time = datetime.now(timezone.utc)

        # Calculate duration
        if event.trigger_timestamp:
            duration = (clear_time - event.trigger_timestamp).total_seconds()
        else:
            duration = None

        event.state = AlarmState.CLEARED
        event.cleared_at = clear_time
        event.clear_value = clear_value
        event.duration_seconds = duration

        logger.info(f"✅ Cleared alarm event: {event_id[:8]}... (duration: {duration}s)")

    def _map_alarm_type(self, gateway_type: str) -> AlarmType:
        """Map Gateway alarm type to Backend enum"""
        type_map = {
            'high_high_limit': AlarmType.HIGH_HIGH_LIMIT,
            'high_limit': AlarmType.HIGH_LIMIT,
            'low_limit': AlarmType.LOW_LIMIT,
            'low_low_limit': AlarmType.LOW_LOW_LIMIT,
            'deviation': AlarmType.DEVIATION,
            'rate_of_change': AlarmType.RATE_OF_CHANGE
        }
        return type_map.get(gateway_type, AlarmType.HIGH_LIMIT)

    def _map_severity(self, gateway_severity: str) -> AlarmSeverity:
        """Map Gateway severity to Backend enum"""
        severity_map = {
            'critical': AlarmSeverity.CRITICAL,
            'high': AlarmSeverity.HIGH,
            'medium': AlarmSeverity.MEDIUM,
            'low': AlarmSeverity.LOW
        }
        return severity_map.get(gateway_severity, AlarmSeverity.MEDIUM)

    def get_statistics(self) -> Dict[str, Any]:
        """Get consumer statistics"""
        return {
            **self.stats,
            'running': self._running,
            'topic': self.topic,
            'group_id': self.group_id
        }


# Singleton instance
_alarm_consumer: Optional[AlarmEventConsumer] = None


def get_alarm_consumer() -> AlarmEventConsumer:
    """Get or create alarm consumer singleton"""
    global _alarm_consumer

    if _alarm_consumer is None:
        _alarm_consumer = AlarmEventConsumer()

    return _alarm_consumer


async def start_alarm_consumer():
    """Start the alarm consumer"""
    consumer = get_alarm_consumer()
    await consumer.start()


async def stop_alarm_consumer():
    """Stop the alarm consumer"""
    consumer = get_alarm_consumer()
    await consumer.stop()
