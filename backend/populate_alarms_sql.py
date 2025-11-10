"""
Populate Alarm Events with 1 Month of Historical Data using Direct SQL

This script generates realistic alarm events without needing to import
all models, avoiding circular dependency issues.
"""

import asyncio
import asyncpg
from datetime import datetime, timedelta
import random
from uuid import uuid4
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Database connection settings
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'optiflow',
    'user': 'optiflow',
    'password': 'optiflow_password'
}

# Alarm templates with realistic industrial scenarios
ALARM_SCENARIOS = [
    # Motor alarms
    {
        "name": "Motor Temperature High",
        "description": "Motor temperature exceeded safe operating limit",
        "alarm_type": "HIGH_LIMIT",
        "severity": "HIGH",
        "high_limit": 85.0,
        "probability_per_day": 0.15,
        "avg_duration_min": 45,
    },
    {
        "name": "Motor Current Overload",
        "description": "Motor drawing excessive current",
        "alarm_type": "HIGH_LIMIT",
        "severity": "HIGH",
        "high_limit": 250.0,
        "probability_per_day": 0.18,
        "avg_duration_min": 30,
    },
    {
        "name": "Motor Vibration High",
        "description": "Motor vibration exceeded acceptable threshold",
        "alarm_type": "HIGH_LIMIT",
        "severity": "HIGH",
        "high_limit": 7.5,
        "probability_per_day": 0.12,
        "avg_duration_min": 60,
    },

    # Bearing alarms
    {
        "name": "Bearing Temperature Critical",
        "description": "Bearing temperature reached critical threshold - potential failure",
        "alarm_type": "HIGH_LIMIT",
        "severity": "CRITICAL",
        "high_limit": 95.0,
        "probability_per_day": 0.08,
        "avg_duration_min": 120,
    },
    {
        "name": "Bearing Vibration Critical",
        "description": "Bearing vibration indicates imminent failure",
        "alarm_type": "HIGH_LIMIT",
        "severity": "CRITICAL",
        "high_limit": 8.5,
        "probability_per_day": 0.06,
        "avg_duration_min": 180,
    },

    # Belt alarms
    {
        "name": "Belt Temperature Warning",
        "description": "Conveyor belt temperature above normal",
        "alarm_type": "HIGH_LIMIT",
        "severity": "MEDIUM",
        "high_limit": 75.0,
        "probability_per_day": 0.20,
        "avg_duration_min": 25,
    },
    {
        "name": "Belt Misalignment Detected",
        "description": "Belt tracking sensor detected misalignment",
        "alarm_type": "CUSTOM",
        "severity": "MEDIUM",
        "high_limit": 1.0,
        "probability_per_day": 0.15,
        "avg_duration_min": 45,
    },
    {
        "name": "Belt Slip Detected",
        "description": "Belt slippage detected on conveyor",
        "alarm_type": "CUSTOM",
        "severity": "HIGH",
        "high_limit": 1.0,
        "probability_per_day": 0.08,
        "avg_duration_min": 90,
    },

    # Flow/throughput alarms
    {
        "name": "Conveyor Flow Rate Low",
        "description": "Belt conveyor flow rate below expected",
        "alarm_type": "LOW_LIMIT",
        "severity": "MEDIUM",
        "low_limit": 300.0,
        "probability_per_day": 0.22,
        "avg_duration_min": 40,
    },
    {
        "name": "Shiploader Rate Critical Low",
        "description": "Ship loading rate critically below target",
        "alarm_type": "LOW_LIMIT",
        "severity": "HIGH",
        "low_limit": 1000.0,
        "probability_per_day": 0.10,
        "avg_duration_min": 75,
    },

    # Environmental alarms
    {
        "name": "Dust Level High",
        "description": "Dust concentration exceeded environmental limit",
        "alarm_type": "HIGH_LIMIT",
        "severity": "MEDIUM",
        "high_limit": 50.0,
        "probability_per_day": 0.30,
        "avg_duration_min": 20,
    },
    {
        "name": "Noise Level Excessive",
        "description": "Noise level exceeded safety threshold",
        "alarm_type": "HIGH_LIMIT",
        "severity": "LOW",
        "high_limit": 90.0,
        "probability_per_day": 0.20,
        "avg_duration_min": 15,
    },

    # Critical equipment alarms
    {
        "name": "Emergency Stop Activated",
        "description": "Emergency stop button was activated",
        "alarm_type": "CUSTOM",
        "severity": "CRITICAL",
        "high_limit": 1.0,
        "probability_per_day": 0.03,
        "avg_duration_min": 300,
    },
    {
        "name": "Power Supply Voltage Fluctuation",
        "description": "Power quality issue detected",
        "alarm_type": "DEVIATION",
        "severity": "MEDIUM",
        "high_limit": 5.0,
        "probability_per_day": 0.25,
        "avg_duration_min": 10,
    },
]

# Acknowledgment comments
ACK_COMMENTS = [
    "Acknowledged - maintenance team dispatched",
    "Operator investigating root cause",
    "Equipment inspected - minor adjustment made",
    "Normal operating conditions resumed",
    "Scheduled for next maintenance window",
    "Corrective action completed",
    "False alarm - sensor calibration needed",
    "Equipment shutdown for safety",
    "Monitoring - no immediate action required",
    "Resolved - awaiting confirmation",
]


async def create_alarm_definitions(conn, tags):
    """Create alarm definitions if they don't exist"""

    created_count = 0

    # If no tags, create dummy tags
    if not tags:
        logger.info("No tags found, creating dummy tags for alarm definitions...")

        # First ensure we have a device
        device_count = await conn.fetchval("SELECT COUNT(*) FROM devices")
        if device_count == 0:
            logger.info("  Creating dummy device...")
            dummy_device_id = uuid4()
            await conn.execute("""
                INSERT INTO devices (
                    id, name, description, is_active, protocol,
                    connection_config, status, total_tags, data_points_collected, settings
                ) VALUES (
                    $1, 'Alarm System Device', 'Virtual device for alarms', true,
                    'OPC_UA', '{}'::jsonb, 'CONNECTED', 0, 0, '{}'::jsonb
                )
            """, dummy_device_id)
        else:
            dummy_device_id = await conn.fetchval("SELECT id FROM devices LIMIT 1")

        # Create dummy tag
        dummy_tag_id = uuid4()
        await conn.execute("""
            INSERT INTO tags (
                id, device_id, name, description, is_active,
                address, data_type, category, scale, "offset",
                scan_rate_ms, enable_quality_check, data_points_count, settings
            ) VALUES (
                $1, $2, 'DUMMY_TAG', 'Dummy tag for alarm system', true,
                'ns=2;s=dummy', 'FLOAT', 'PROCESS', 1.0, 0.0,
                1000, false, 0, '{}'::jsonb
            ) ON CONFLICT DO NOTHING
        """, dummy_tag_id, dummy_device_id)
        tags = [{'id': dummy_tag_id, 'name': 'DUMMY_TAG'}]
        logger.info(f"  Created dummy tag with id: {dummy_tag_id}")

    for scenario in ALARM_SCENARIOS:
        # Check if alarm definition already exists
        existing = await conn.fetchval(
            "SELECT id FROM alarm_definitions WHERE name = $1",
            scenario["name"]
        )

        if existing:
            logger.info(f"  Alarm definition already exists: {scenario['name']}")
            continue

        # Use first available tag
        tag_id = tags[0]['id']

        # Create alarm definition
        alarm_id = uuid4()

        await conn.execute("""
            INSERT INTO alarm_definitions (
                id, tag_id, name, description, is_active, alarm_type,
                severity, high_limit, low_limit, deadband, delay_seconds,
                enable_email, enable_sms, notification_recipients, settings
            ) VALUES (
                $1, $2, $3, $4, $5, $6::alarmtype,
                $7::alarmseverity, $8, $9, $10, $11,
                $12, $13, $14, $15
            )
        """,
            alarm_id,
            tag_id,
            scenario["name"],
            scenario["description"],
            True,  # is_active
            scenario["alarm_type"],
            scenario["severity"],
            scenario.get("high_limit"),
            scenario.get("low_limit"),
            2.0,  # deadband
            5.0,  # delay_seconds
            scenario["severity"] in ["HIGH", "CRITICAL"],  # enable_email
            scenario["severity"] == "CRITICAL",  # enable_sms
            '[]',  # notification_recipients
            f'{{"probability": {scenario["probability_per_day"]}, "avg_duration": {scenario["avg_duration_min"]}}}'
        )

        created_count += 1
        logger.info(f"  ✓ Created alarm definition: {scenario['name']}")

    return created_count


async def generate_historical_events(conn, alarm_defs, admin_user_id, days=30):
    """Generate realistic historical alarm events"""

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    logger.info(f"\nGenerating events from {start_date.date()} to {end_date.date()}")
    logger.info("="*60)

    events_created = 0
    current_date = start_date

    while current_date < end_date:
        day_events = 0

        for alarm_def in alarm_defs:
            # Get probability from settings
            probability = alarm_def.get('probability_per_day', 0.1)
            avg_duration = alarm_def.get('avg_duration_min', 30)

            # Random chance of alarm occurring
            if random.random() < probability:
                # Generate trigger time during operational hours (6 AM to 10 PM)
                trigger_time = current_date + timedelta(
                    hours=random.uniform(6, 22),
                    minutes=random.uniform(0, 59),
                    seconds=random.uniform(0, 59)
                )

                # Generate trigger value
                if alarm_def['high_limit']:
                    trigger_value = alarm_def['high_limit'] + random.uniform(1, 10)
                elif alarm_def['low_limit']:
                    trigger_value = alarm_def['low_limit'] - random.uniform(1, 50)
                else:
                    trigger_value = 1.0

                # Random duration (with variation)
                if random.random() < 0.7:  # 70% resolve quickly
                    duration_minutes = avg_duration * random.uniform(0.5, 1.5)
                else:  # 30% take longer
                    duration_minutes = avg_duration * random.uniform(2, 6)

                cleared_time = trigger_time + timedelta(minutes=duration_minutes)

                # Determine if acknowledged
                is_critical = alarm_def['severity'] in ['HIGH', 'CRITICAL']
                is_acknowledged = is_critical and random.random() < 0.85

                acknowledged_at = None
                acknowledged_by = None
                ack_comment = None

                if is_acknowledged and admin_user_id:
                    ack_delay = random.uniform(2, 30)
                    acknowledged_at = trigger_time + timedelta(minutes=ack_delay)
                    acknowledged_by = admin_user_id
                    ack_comment = random.choice(ACK_COMMENTS)

                # Clear value
                if alarm_def['high_limit']:
                    clear_value = alarm_def['high_limit'] - random.uniform(5, 15)
                elif alarm_def['low_limit']:
                    clear_value = alarm_def['low_limit'] + random.uniform(10, 100)
                else:
                    clear_value = 0.0

                # Insert event
                event_id = uuid4()

                await conn.execute("""
                    INSERT INTO alarm_events (
                        id, definition_id, state, trigger_value, trigger_timestamp,
                        acknowledged_at, acknowledged_by, acknowledgment_comment,
                        cleared_at, clear_value, duration_seconds, event_metadata
                    ) VALUES (
                        $1, $2, $3::alarmstate, $4, $5,
                        $6, $7, $8,
                        $9, $10, $11, $12
                    )
                """,
                    event_id,
                    alarm_def['id'],
                    'CLEARED',
                    trigger_value,
                    trigger_time,
                    acknowledged_at,
                    acknowledged_by,
                    ack_comment,
                    cleared_time,
                    clear_value,
                    duration_minutes * 60,
                    f'{{"equipment": "{alarm_def["name"].split()[0]}", "shift": "{"day" if 6 <= trigger_time.hour < 18 else "night"}", "simulated": true}}'
                )

                events_created += 1
                day_events += 1

        # Progress update
        if day_events > 0:
            logger.info(f"  Day {(current_date - start_date).days + 1}/{days}: {day_events} events")

        current_date += timedelta(days=1)

    logger.info("="*60)
    logger.info(f"Total events created: {events_created}\n")

    return events_created


async def create_active_alarms(conn, alarm_defs, admin_user_id):
    """Create some currently active alarms"""

    logger.info("Creating active alarms for real-time monitoring...")

    now = datetime.now()
    num_active = random.randint(3, 5)
    selected_alarms = random.sample(alarm_defs, min(num_active, len(alarm_defs)))

    events_created = 0

    for alarm_def in selected_alarms:
        trigger_time = now - timedelta(minutes=random.uniform(5, 60))

        # Generate trigger value
        if alarm_def['high_limit']:
            trigger_value = alarm_def['high_limit'] + random.uniform(1, 10)
        elif alarm_def['low_limit']:
            trigger_value = alarm_def['low_limit'] - random.uniform(1, 50)
        else:
            trigger_value = 1.0

        # Some acknowledged, some not
        is_acknowledged = random.random() < 0.6
        state = 'ACKNOWLEDGED' if is_acknowledged else 'ACTIVE'

        acknowledged_at = None
        acknowledged_by = None
        ack_comment = None

        if is_acknowledged and admin_user_id:
            ack_delay = random.uniform(2, 20)
            acknowledged_at = trigger_time + timedelta(minutes=ack_delay)
            acknowledged_by = admin_user_id
            ack_comment = "Investigating - operator on site"

        event_id = uuid4()

        await conn.execute("""
            INSERT INTO alarm_events (
                id, definition_id, state, trigger_value, trigger_timestamp,
                acknowledged_at, acknowledged_by, acknowledgment_comment,
                event_metadata
            ) VALUES (
                $1, $2, $3::alarmstate, $4, $5,
                $6, $7, $8, $9
            )
        """,
            event_id,
            alarm_def['id'],
            state,
            trigger_value,
            trigger_time,
            acknowledged_at,
            acknowledged_by,
            ack_comment,
            f'{{"equipment": "{alarm_def["name"].split()[0]}", "active": true, "shift": "{"day" if 6 <= trigger_time.hour < 18 else "night"}"}}'
        )

        events_created += 1
        logger.info(f"  ✓ Active alarm: {alarm_def['name']} ({state})")

    return events_created


async def print_statistics(conn):
    """Print statistics about generated data"""

    total_defs = await conn.fetchval("SELECT COUNT(*) FROM alarm_definitions")
    total_events = await conn.fetchval("SELECT COUNT(*) FROM alarm_events")

    severity_stats = await conn.fetch("""
        SELECT ad.severity, COUNT(ae.id) as count
        FROM alarm_events ae
        JOIN alarm_definitions ad ON ae.definition_id = ad.id
        GROUP BY ad.severity
        ORDER BY ad.severity
    """)

    state_stats = await conn.fetch("""
        SELECT state, COUNT(*) as count
        FROM alarm_events
        GROUP BY state
        ORDER BY state
    """)

    logger.info("\n" + "="*60)
    logger.info("ALARM AND EVENT STATISTICS")
    logger.info("="*60)
    logger.info(f"Total Alarm Definitions: {total_defs}")
    logger.info(f"Total Alarm Events: {total_events}")
    logger.info("\nEvents by Severity:")
    for row in severity_stats:
        logger.info(f"  {row['severity']}: {row['count']}")
    logger.info("\nEvents by State:")
    for row in state_stats:
        logger.info(f"  {row['state']}: {row['count']}")
    logger.info("="*60 + "\n")


async def main():
    """Main execution function"""

    logger.info("\n" + "="*60)
    logger.info("OPTIFLOW - ALARM AND EVENT POPULATION")
    logger.info("="*60 + "\n")

    logger.info("Connecting to database...")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        # Get available tags
        tags = await conn.fetch("SELECT id, name FROM tags LIMIT 100")
        logger.info(f"Found {len(tags)} tags in database")

        # Get admin user
        admin_user = await conn.fetchrow(
            "SELECT id FROM users WHERE email = 'admin@optiflow.com'"
        )
        admin_user_id = admin_user['id'] if admin_user else None

        # Create alarm definitions
        logger.info("Creating alarm definitions...")
        created_defs = await create_alarm_definitions(conn, tags)
        logger.info(f"Created {created_defs} new alarm definitions\n")

        # Get all alarm definitions with their settings
        alarm_defs = await conn.fetch("""
            SELECT id, name, severity, high_limit, low_limit,
                   COALESCE((settings->>'probability')::float, 0.1) as probability_per_day,
                   COALESCE((settings->>'avg_duration')::float, 30) as avg_duration_min
            FROM alarm_definitions
        """)

        alarm_defs = [dict(row) for row in alarm_defs]

        # Generate historical events
        historical_count = await generate_historical_events(
            conn, alarm_defs, admin_user_id, days=30
        )

        # Create active alarms
        active_count = await create_active_alarms(conn, alarm_defs, admin_user_id)
        logger.info(f"Created {active_count} active alarms\n")

        # Print statistics
        await print_statistics(conn)

        logger.info("✅ Alarm and event population completed successfully!\n")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
