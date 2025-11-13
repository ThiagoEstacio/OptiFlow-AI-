"""
Alarm Initializer - Creates default alarm definitions for simulator tags
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.alarm import AlarmDefinition, AlarmSeverity, AlarmType
from app.models.tag import Tag
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def initialize_default_alarms():
    """
    Create default alarm definitions for critical simulator tags
    """
    async with AsyncSessionLocal() as db:
        try:
            logger.info("🚨 Initializing default alarm definitions...")

            # Check if alarms already exist
            result = await db.execute(select(AlarmDefinition))
            existing_alarms = result.scalars().all()

            if len(existing_alarms) > 0:
                logger.info(f"Alarms already initialized ({len(existing_alarms)} definitions)")
                return

            # Define alarm configurations for simulator tags
            alarm_configs = [
                # Belt Temperature Alarms
                {
                    "tag_name": "CORR01_TEMP_C_PV",
                    "name": "Belt CORR01 - High Temperature",
                    "description": "Conveyor belt temperature exceeds safe operating limit",
                    "alarm_type": AlarmType.HIGH_LIMIT,
                    "severity": AlarmSeverity.HIGH,
                    "high_limit": 85.0,
                    "deadband": 5.0,
                    "delay_seconds": 10
                },
                {
                    "tag_name": "CORR01_TEMP_C_PV",
                    "name": "Belt CORR01 - Critical Temperature",
                    "description": "Conveyor belt temperature at critical level - immediate action required",
                    "alarm_type": AlarmType.HIGH_HIGH_LIMIT,
                    "severity": AlarmSeverity.CRITICAL,
                    "high_high_limit": 95.0,
                    "deadband": 5.0,
                    "delay_seconds": 5
                },

                # Belt Current Alarms
                {
                    "tag_name": "CORR01_CURRENT_A_PV",
                    "name": "Belt CORR01 - High Current",
                    "description": "Conveyor motor drawing excessive current",
                    "alarm_type": AlarmType.HIGH_LIMIT,
                    "severity": AlarmSeverity.MEDIUM,
                    "high_limit": 90.0,
                    "deadband": 5.0,
                    "delay_seconds": 15
                },

                # Belt Misalignment
                {
                    "tag_name": "CORR01_MISALIGNMENT_PV",
                    "name": "Belt CORR01 - Misalignment Detected",
                    "description": "Belt tracking out of alignment",
                    "alarm_type": AlarmType.HIGH_LIMIT,
                    "severity": AlarmSeverity.HIGH,
                    "high_limit": 0.5,  # 50% misalignment
                    "deadband": 0.1,
                    "delay_seconds": 30
                },

                # Shiploader Power
                {
                    "tag_name": "SLD01_POWER_KW_PV",
                    "name": "Shiploader - High Power Consumption",
                    "description": "Shiploader power consumption above normal",
                    "alarm_type": AlarmType.HIGH_LIMIT,
                    "severity": AlarmSeverity.MEDIUM,
                    "high_limit": 450.0,
                    "deadband": 20.0,
                    "delay_seconds": 20
                },

                # Shiploader Current
                {
                    "tag_name": "SLD01_CURRENT_A_PV",
                    "name": "Shiploader - Overcurrent",
                    "description": "Shiploader motor overcurrent condition",
                    "alarm_type": AlarmType.HIGH_LIMIT,
                    "severity": AlarmSeverity.HIGH,
                    "high_limit": 85.0,
                    "deadband": 5.0,
                    "delay_seconds": 10
                },

                # Warehouse Level Alarms
                {
                    "tag_name": "WAREHOUSE_LEVEL_PCT_PV",
                    "name": "Warehouse - Low Level",
                    "description": "Warehouse inventory below minimum level",
                    "alarm_type": AlarmType.LOW_LIMIT,
                    "severity": AlarmSeverity.MEDIUM,
                    "low_limit": 20.0,
                    "deadband": 5.0,
                    "delay_seconds": 60
                },
                {
                    "tag_name": "WAREHOUSE_LEVEL_PCT_PV",
                    "name": "Warehouse - High Level",
                    "description": "Warehouse inventory near capacity",
                    "alarm_type": AlarmType.HIGH_LIMIT,
                    "severity": AlarmSeverity.LOW,
                    "high_limit": 95.0,
                    "deadband": 5.0,
                    "delay_seconds": 60
                },

                # Production Flow Deviation
                {
                    "tag_name": "SLD01_FLOW_TPH_PV",
                    "name": "Shiploader - Flow Deviation",
                    "description": "Actual flow deviates significantly from setpoint",
                    "alarm_type": AlarmType.DEVIATION,
                    "severity": AlarmSeverity.MEDIUM,
                    "setpoint": 2000.0,  # Will be updated from SLD01_SETPOINT_TPH_PV
                    "deviation_limit": 300.0,  # 15% deviation
                    "deadband": 50.0,
                    "delay_seconds": 30
                },

                # System Running Check
                {
                    "tag_name": "SYSTEM_RUNNING_PV",
                    "name": "System - Not Running",
                    "description": "System stopped unexpectedly",
                    "alarm_type": AlarmType.LOW_LIMIT,
                    "severity": AlarmSeverity.CRITICAL,
                    "low_limit": 0.5,  # Triggers when < 0.5 (i.e., False)
                    "deadband": 0.1,
                    "delay_seconds": 5
                }
            ]

            created_count = 0

            for config in alarm_configs:
                # Find the tag
                tag_result = await db.execute(
                    select(Tag).where(Tag.name == config["tag_name"])
                )
                tag = tag_result.scalar_one_or_none()

                if not tag:
                    logger.warning(f"Tag not found: {config['tag_name']}, skipping alarm creation")
                    continue

                # Create alarm definition
                alarm_def = AlarmDefinition(
                    tag_id=tag.id,
                    name=config["name"],
                    description=config["description"],
                    alarm_type=config["alarm_type"],
                    severity=config["severity"],
                    high_limit=config.get("high_limit"),
                    low_limit=config.get("low_limit"),
                    high_high_limit=config.get("high_high_limit"),
                    low_low_limit=config.get("low_low_limit"),
                    setpoint=config.get("setpoint"),
                    deviation_limit=config.get("deviation_limit"),
                    deadband=config["deadband"],
                    delay_seconds=config["delay_seconds"],
                    is_active=True
                )

                db.add(alarm_def)
                created_count += 1
                logger.info(f"✅ Created alarm: {config['name']}")

            await db.commit()
            logger.info(f"🎉 Successfully created {created_count} alarm definitions")

        except Exception as e:
            logger.error(f"Error initializing alarms: {e}", exc_info=True)
            await db.rollback()


async def cleanup_alarms():
    """Remove all alarm definitions (for testing)"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(AlarmDefinition))
            alarm_defs = result.scalars().all()

            for alarm_def in alarm_defs:
                await db.delete(alarm_def)

            await db.commit()
            logger.info(f"Deleted {len(alarm_defs)} alarm definitions")

        except Exception as e:
            logger.error(f"Error cleaning up alarms: {e}", exc_info=True)
            await db.rollback()


# CLI entry point
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(initialize_default_alarms())
