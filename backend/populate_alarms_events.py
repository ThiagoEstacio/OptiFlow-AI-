"""
Populate Alarm Definitions and Events with 1 Month of Historical Data

This script creates realistic alarm definitions and events based on the
grain terminal simulator, including equipment failures, operational events,
and threshold violations.
"""

import asyncio
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
import random
from uuid import UUID, uuid4
from typing import List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import all models to avoid lazy loading issues
from app.models import *  # This imports all models including relationships
from app.models.tag import Tag
from app.models.alarm import AlarmDefinition, AlarmEvent, AlarmType, AlarmSeverity, AlarmState
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Alarm definitions for different equipment and scenarios
ALARM_TEMPLATES = [
    # Temperature alarms
    {
        "name": "Motor Temperature High",
        "description": "Motor temperature exceeded safe operating limit",
        "alarm_type": AlarmType.HIGH_LIMIT,
        "severity": AlarmSeverity.HIGH,
        "high_limit": 85.0,
        "tag_pattern": "MOTOR_TEMP",
        "probability": 0.15,  # 15% chance per day
    },
    {
        "name": "Bearing Temperature Critical",
        "description": "Bearing temperature reached critical threshold",
        "alarm_type": AlarmType.HIGH_LIMIT,
        "severity": AlarmSeverity.CRITICAL,
        "high_limit": 95.0,
        "tag_pattern": "BEARING_TEMP",
        "probability": 0.08,  # 8% chance per day
    },
    {
        "name": "Belt Temperature Warning",
        "description": "Conveyor belt temperature above normal",
        "alarm_type": AlarmType.HIGH_LIMIT,
        "severity": AlarmSeverity.MEDIUM,
        "high_limit": 75.0,
        "tag_pattern": "BELT_TEMP",
        "probability": 0.20,  # 20% chance per day
    },

    # Vibration alarms
    {
        "name": "Motor Vibration High",
        "description": "Motor vibration exceeded acceptable threshold",
        "alarm_type": AlarmType.HIGH_LIMIT,
        "severity": AlarmSeverity.HIGH,
        "high_limit": 7.5,
        "tag_pattern": "MOTOR_VIB",
        "probability": 0.12,
    },
    {
        "name": "Bearing Vibration Critical",
        "description": "Bearing vibration indicates potential failure",
        "alarm_type": AlarmType.HIGH_LIMIT,
        "severity": AlarmSeverity.CRITICAL,
        "high_limit": 8.5,
        "tag_pattern": "BEARING_VIB",
        "probability": 0.06,
    },

    # Power and current alarms
    {
        "name": "Motor Current High",
        "description": "Motor drawing excessive current - possible overload",
        "alarm_type": AlarmType.HIGH_LIMIT,
        "severity": AlarmSeverity.HIGH,
        "high_limit": 250.0,
        "tag_pattern": "MOTOR_CURRENT",
        "probability": 0.18,
    },
    {
        "name": "Power Consumption Spike",
        "description": "Unusual spike in power consumption detected",
        "alarm_type": AlarmType.HIGH_LIMIT,
        "severity": AlarmSeverity.MEDIUM,
        "high_limit": 500.0,
        "tag_pattern": "POWER_KW",
        "probability": 0.25,
    },

    # Flow and throughput alarms
    {
        "name": "Conveyor Flow Rate Low",
        "description": "Belt conveyor flow rate below expected",
        "alarm_type": AlarmType.LOW_LIMIT,
        "severity": AlarmSeverity.MEDIUM,
        "low_limit": 300.0,
        "tag_pattern": "BELT_FLOW",
        "probability": 0.22,
    },
    {
        "name": "Shiploader Rate Critical Low",
        "description": "Ship loading rate critically below target",
        "alarm_type": AlarmType.LOW_LIMIT,
        "severity": AlarmSeverity.HIGH,
        "low_limit": 1000.0,
        "tag_pattern": "SHIPLOADER_RATE",
        "probability": 0.10,
    },

    # Equipment status alarms
    {
        "name": "Belt Misalignment Detected",
        "description": "Belt tracking sensor detected misalignment",
        "alarm_type": AlarmType.CUSTOM,
        "severity": AlarmSeverity.MEDIUM,
        "tag_pattern": "BELT_ALIGNED",
        "probability": 0.15,
    },
    {
        "name": "Emergency Stop Activated",
        "description": "Emergency stop button was activated",
        "alarm_type": AlarmType.CUSTOM,
        "severity": AlarmSeverity.CRITICAL,
        "tag_pattern": "E_STOP",
        "probability": 0.03,  # Rare but critical
    },
    {
        "name": "Belt Slip Detected",
        "description": "Belt slippage detected on conveyor",
        "alarm_type": AlarmType.CUSTOM,
        "severity": AlarmSeverity.HIGH,
        "tag_pattern": "BELT_SLIP",
        "probability": 0.08,
    },

    # Environmental alarms
    {
        "name": "Dust Level High",
        "description": "Dust concentration exceeded environmental limit",
        "alarm_type": AlarmType.HIGH_LIMIT,
        "severity": AlarmSeverity.MEDIUM,
        "high_limit": 50.0,
        "tag_pattern": "DUST_LEVEL",
        "probability": 0.30,  # Common in grain terminals
    },
    {
        "name": "Noise Level Excessive",
        "description": "Noise level exceeded safety threshold",
        "alarm_type": AlarmType.HIGH_LIMIT,
        "severity": AlarmSeverity.LOW,
        "high_limit": 90.0,
        "tag_pattern": "NOISE_DB",
        "probability": 0.20,
    },
]

# Event scenarios for realistic event generation
EVENT_SCENARIOS = [
    {
        "description": "Scheduled maintenance performed",
        "duration_hours": (2, 8),
        "severity": AlarmSeverity.LOW,
    },
    {
        "description": "Belt cleaning required due to material buildup",
        "duration_hours": (0.5, 2),
        "severity": AlarmSeverity.MEDIUM,
    },
    {
        "description": "Motor overheating - equipment shutdown for cooling",
        "duration_hours": (1, 4),
        "severity": AlarmSeverity.HIGH,
    },
    {
        "description": "Bearing failure detected - emergency maintenance",
        "duration_hours": (4, 24),
        "severity": AlarmSeverity.CRITICAL,
    },
    {
        "description": "Rain delay - operations suspended",
        "duration_hours": (1, 6),
        "severity": AlarmSeverity.MEDIUM,
    },
    {
        "description": "Power quality issue - voltage fluctuation",
        "duration_hours": (0.1, 0.5),
        "severity": AlarmSeverity.MEDIUM,
    },
    {
        "description": "Operator intervention required",
        "duration_hours": (0.2, 1),
        "severity": AlarmSeverity.LOW,
    },
]


async def get_or_create_tags(session: AsyncSession) -> List[Tag]:
    """Get existing tags or create demo tags if needed"""
    result = await session.execute(select(Tag).limit(100))
    tags = result.scalars().all()

    if not tags:
        logger.warning("No tags found in database. Please run the simulator or create tags first.")
        return []

    logger.info(f"Found {len(tags)} tags in database")
    return list(tags)


async def create_alarm_definitions(
    session: AsyncSession,
    tags: List[Tag]
) -> List[AlarmDefinition]:
    """Create alarm definitions based on available tags"""

    alarm_defs = []

    for template in ALARM_TEMPLATES:
        # Find matching tags
        matching_tags = [
            tag for tag in tags
            if template["tag_pattern"] in tag.name.upper()
        ]

        if not matching_tags:
            logger.warning(f"No tags found for pattern: {template['tag_pattern']}")
            continue

        # Create alarm definition for first matching tag
        tag = matching_tags[0]

        alarm_def = AlarmDefinition(
            id=uuid4(),
            tag_id=tag.id,
            name=template["name"],
            description=template["description"],
            is_active=True,
            alarm_type=template["alarm_type"],
            severity=template["severity"],
            high_limit=template.get("high_limit"),
            low_limit=template.get("low_limit"),
            deadband=2.0 if template.get("high_limit") or template.get("low_limit") else None,
            delay_seconds=5.0,
            enable_email=template["severity"] in [AlarmSeverity.HIGH, AlarmSeverity.CRITICAL],
            enable_sms=template["severity"] == AlarmSeverity.CRITICAL,
            notification_recipients=[],
            settings={"probability": template["probability"]}
        )

        session.add(alarm_def)
        alarm_defs.append(alarm_def)
        logger.info(f"Created alarm definition: {alarm_def.name}")

    await session.commit()
    return alarm_defs


async def generate_historical_events(
    session: AsyncSession,
    alarm_defs: List[AlarmDefinition],
    days: int = 30
) -> List[AlarmEvent]:
    """Generate realistic historical alarm events for the past N days"""

    events = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Get admin user for acknowledgments
    result = await session.execute(
        select(User).where(User.email == "admin@optiflow.com")
    )
    admin_user = result.scalar_one_or_none()

    logger.info(f"Generating events from {start_date.date()} to {end_date.date()}")

    # Generate events day by day
    current_date = start_date

    while current_date < end_date:
        # For each day, check each alarm definition
        for alarm_def in alarm_defs:
            probability = alarm_def.settings.get("probability", 0.1)

            # Random chance of alarm occurring on this day
            if random.random() < probability:
                # Generate alarm event
                trigger_time = current_date + timedelta(
                    hours=random.uniform(6, 22),  # During operational hours
                    minutes=random.uniform(0, 59)
                )

                # Generate trigger value based on alarm type
                if alarm_def.high_limit:
                    trigger_value = alarm_def.high_limit + random.uniform(1, 10)
                elif alarm_def.low_limit:
                    trigger_value = alarm_def.low_limit - random.uniform(1, 50)
                else:
                    trigger_value = 1.0  # Digital alarm

                # Random duration (most alarms are short, some are long)
                if random.random() < 0.7:  # 70% are resolved quickly
                    duration_minutes = random.uniform(5, 60)
                else:  # 30% take longer
                    duration_minutes = random.uniform(60, 480)

                cleared_time = trigger_time + timedelta(minutes=duration_minutes)

                # Most critical alarms are acknowledged
                is_acknowledged = (
                    alarm_def.severity in [AlarmSeverity.HIGH, AlarmSeverity.CRITICAL]
                    and random.random() < 0.85
                )

                acknowledged_at = None
                acknowledged_by = None
                comment = None

                if is_acknowledged and admin_user:
                    ack_delay = random.uniform(2, 30)  # Acknowledged within 2-30 min
                    acknowledged_at = trigger_time + timedelta(minutes=ack_delay)
                    acknowledged_by = admin_user.id

                    comments = [
                        "Acknowledged - maintenance dispatched",
                        "Operator investigating",
                        "Normal operating conditions resumed",
                        "Equipment inspected - no issues found",
                        "Scheduled maintenance required",
                        "Corrective action taken",
                    ]
                    comment = random.choice(comments)

                # Clear value
                if alarm_def.high_limit:
                    clear_value = alarm_def.high_limit - random.uniform(5, 15)
                elif alarm_def.low_limit:
                    clear_value = alarm_def.low_limit + random.uniform(10, 100)
                else:
                    clear_value = 0.0

                # Create event
                event = AlarmEvent(
                    id=uuid4(),
                    definition_id=alarm_def.id,
                    state=AlarmState.CLEARED,
                    trigger_value=trigger_value,
                    trigger_timestamp=trigger_time,
                    acknowledged_at=acknowledged_at,
                    acknowledged_by=acknowledged_by,
                    acknowledgment_comment=comment,
                    cleared_at=cleared_time,
                    clear_value=clear_value,
                    duration_seconds=duration_minutes * 60,
                    event_metadata={
                        "equipment": alarm_def.name.split()[0],
                        "shift": "day" if 6 <= trigger_time.hour < 18 else "night",
                        "simulated": True
                    }
                )

                session.add(event)
                events.append(event)

        # Move to next day
        current_date += timedelta(days=1)

        # Commit every 7 days to avoid memory issues
        if (current_date - start_date).days % 7 == 0:
            await session.commit()
            logger.info(f"Progress: {(current_date - start_date).days}/{days} days")

    # Final commit
    await session.commit()
    logger.info(f"Generated {len(events)} alarm events over {days} days")

    return events


async def create_active_alarms(
    session: AsyncSession,
    alarm_defs: List[AlarmDefinition]
) -> List[AlarmEvent]:
    """Create some currently active alarms for real-time monitoring"""

    events = []
    now = datetime.now()

    # Get admin user
    result = await session.execute(
        select(User).where(User.email == "admin@optiflow.com")
    )
    admin_user = result.scalar_one_or_none()

    # Create 3-5 active alarms
    num_active = random.randint(3, 5)
    selected_alarms = random.sample(alarm_defs, min(num_active, len(alarm_defs)))

    for alarm_def in selected_alarms:
        # Triggered within last hour
        trigger_time = now - timedelta(minutes=random.uniform(5, 60))

        # Generate trigger value
        if alarm_def.high_limit:
            trigger_value = alarm_def.high_limit + random.uniform(1, 10)
        elif alarm_def.low_limit:
            trigger_value = alarm_def.low_limit - random.uniform(1, 50)
        else:
            trigger_value = 1.0

        # Some are acknowledged, some not
        is_acknowledged = random.random() < 0.6

        state = AlarmState.ACKNOWLEDGED if is_acknowledged else AlarmState.ACTIVE
        acknowledged_at = None
        acknowledged_by = None
        comment = None

        if is_acknowledged and admin_user:
            ack_delay = random.uniform(2, 20)
            acknowledged_at = trigger_time + timedelta(minutes=ack_delay)
            acknowledged_by = admin_user.id
            comment = "Investigating - operator on site"

        event = AlarmEvent(
            id=uuid4(),
            definition_id=alarm_def.id,
            state=state,
            trigger_value=trigger_value,
            trigger_timestamp=trigger_time,
            acknowledged_at=acknowledged_at,
            acknowledged_by=acknowledged_by,
            acknowledgment_comment=comment,
            event_metadata={
                "equipment": alarm_def.name.split()[0],
                "shift": "day" if 6 <= trigger_time.hour < 18 else "night",
                "active": True
            }
        )

        session.add(event)
        events.append(event)
        logger.info(f"Created active alarm: {alarm_def.name} - {state.value}")

    await session.commit()
    return events


async def print_statistics(session: AsyncSession):
    """Print statistics about generated data"""

    # Count alarm definitions
    result = await session.execute(select(AlarmDefinition))
    alarm_defs = result.scalars().all()

    # Count events by severity
    result = await session.execute(select(AlarmEvent))
    events = result.scalars().all()

    severity_counts = {}
    state_counts = {}

    for event in events:
        # Get alarm definition to get severity
        result = await session.execute(
            select(AlarmDefinition).where(AlarmDefinition.id == event.definition_id)
        )
        alarm_def = result.scalar_one_or_none()

        if alarm_def:
            severity = alarm_def.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        state = event.state.value
        state_counts[state] = state_counts.get(state, 0) + 1

    logger.info("\n" + "="*60)
    logger.info("ALARM AND EVENT STATISTICS")
    logger.info("="*60)
    logger.info(f"Total Alarm Definitions: {len(alarm_defs)}")
    logger.info(f"Total Alarm Events: {len(events)}")
    logger.info("\nEvents by Severity:")
    for severity, count in sorted(severity_counts.items()):
        logger.info(f"  {severity}: {count}")
    logger.info("\nEvents by State:")
    for state, count in sorted(state_counts.items()):
        logger.info(f"  {state}: {count}")
    logger.info("="*60 + "\n")


async def main():
    """Main execution function"""
    logger.info("Starting alarm and event population...")

    async with AsyncSessionLocal() as session:
        # Get tags
        tags = await get_or_create_tags(session)

        if not tags:
            logger.error("No tags available. Please run simulator first.")
            return

        # Create alarm definitions
        logger.info("\nCreating alarm definitions...")
        alarm_defs = await create_alarm_definitions(session, tags)

        if not alarm_defs:
            logger.error("Failed to create alarm definitions")
            return

        # Generate historical events (30 days)
        logger.info("\nGenerating 30 days of historical events...")
        historical_events = await generate_historical_events(session, alarm_defs, days=30)

        # Create some active alarms
        logger.info("\nCreating active alarms...")
        active_events = await create_active_alarms(session, alarm_defs)

        # Print statistics
        await print_statistics(session)

        logger.info("✅ Alarm and event population completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
