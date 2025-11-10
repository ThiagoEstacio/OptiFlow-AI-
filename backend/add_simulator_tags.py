"""
Script to add simulator tags to database for Autonomous Agent monitoring
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.tag import Tag, TagCategory, TagDataType
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Simulator tags to create
SIMULATOR_TAGS = [
    {
        "name": "SYSTEM_RUNNING_PV",
        "tag_address": "SYSTEM_RUNNING_PV",
        "description": "System running status (1=running, 0=stopped)",
        "data_type": TagDataType.BOOLEAN,
        "category": TagCategory.STATUS,
        "unit": "",
        "min_value": 0,
        "max_value": 1,
    },
    {
        "name": "WAREHOUSE_LEVEL_PCT_PV",
        "tag_address": "WAREHOUSE_LEVEL_PCT_PV",
        "description": "Warehouse inventory level percentage",
        "data_type": TagDataType.FLOAT,
        "category": TagCategory.PROCESS,
        "unit": "%",
        "min_value": 0,
        "max_value": 100,
    },
    {
        "name": "TOTAL_MASS_T_PV",
        "tag_address": "TOTAL_MASS_T_PV",
        "description": "Total mass loaded in tonnes",
        "data_type": TagDataType.FLOAT,
        "category": TagCategory.PROCESS,
        "unit": "t",
        "min_value": 0,
        "max_value": 100000,
    },
    {
        "name": "TOTAL_KWH_PV",
        "tag_address": "TOTAL_KWH_PV",
        "description": "Total energy consumed",
        "data_type": TagDataType.FLOAT,
        "category": TagCategory.ENERGY,
        "unit": "kWh",
        "min_value": 0,
        "max_value": 1000000,
    },
    {
        "name": "TEST_COUNTER_PV",
        "tag_address": "TEST_COUNTER_PV",
        "description": "Test counter for validation (0-10)",
        "data_type": TagDataType.INTEGER,
        "category": TagCategory.STATUS,
        "unit": "",
        "min_value": 0,
        "max_value": 10,
    },
]

# Add gate tags
for gate_num in range(1, 5):
    gate_str = str(gate_num).zfill(2)
    SIMULATOR_TAGS.extend([
        {
            "name": f"ARZ_GATES_GATE{gate_str}_POSICAO_PV",
            "tag_address": f"ARZ_GATES_GATE{gate_str}_POSICAO_PV",
            "description": f"Gate {gate_num} position/opening percentage",
            "data_type": TagDataType.FLOAT,
            "category": TagCategory.SETPOINT,
            "unit": "%",
            "min_value": 0,
            "max_value": 100,
        },
        {
            "name": f"ARZ_GATES_GATE{gate_str}_VAZAO_TPH_PV",
            "tag_address": f"ARZ_GATES_GATE{gate_str}_VAZAO_TPH_PV",
            "description": f"Gate {gate_num} flow rate",
            "data_type": TagDataType.FLOAT,
            "category": TagCategory.PROCESS,
            "unit": "t/h",
            "min_value": 0,
            "max_value": 500,
        },
    ])


async def add_simulator_tags():
    """Add simulator tags to database"""
    async with AsyncSessionLocal() as db:
        try:
            created_count = 0
            updated_count = 0

            for tag_data in SIMULATOR_TAGS:
                # Check if tag already exists
                stmt = select(Tag).where(Tag.name == tag_data["name"])
                result = await db.execute(stmt)
                existing_tag = result.scalar_one_or_none()

                if existing_tag:
                    # Update to make sure it's active
                    existing_tag.is_active = True
                    existing_tag.description = tag_data["description"]
                    existing_tag.category = tag_data["category"]
                    existing_tag.data_type = tag_data["data_type"]
                    existing_tag.unit = tag_data["unit"]
                    existing_tag.min_value = tag_data["min_value"]
                    existing_tag.max_value = tag_data["max_value"]
                    updated_count += 1
                    logger.info(f"✓ Updated tag: {tag_data['name']}")
                else:
                    # Create new tag
                    tag = Tag(
                        id=uuid.uuid4(),
                        name=tag_data["name"],
                        tag_address=tag_data["tag_address"],
                        description=tag_data["description"],
                        data_type=tag_data["data_type"],
                        category=tag_data["category"],
                        unit=tag_data["unit"],
                        min_value=tag_data["min_value"],
                        max_value=tag_data["max_value"],
                        is_active=True,
                        enable_alarm=True,
                        enable_logging=True,
                    )
                    db.add(tag)
                    created_count += 1
                    logger.info(f"✓ Created tag: {tag_data['name']}")

            await db.commit()

            logger.info(f"\n{'='*60}")
            logger.info(f"✅ Tags setup complete!")
            logger.info(f"   Created: {created_count} new tags")
            logger.info(f"   Updated: {updated_count} existing tags")
            logger.info(f"   Total active tags: {created_count + updated_count}")
            logger.info(f"{'='*60}\n")

            # Show summary
            stmt = select(Tag).where(Tag.is_active == True)
            result = await db.execute(stmt)
            active_tags = result.scalars().all()
            logger.info(f"📊 Active tags in database: {len(active_tags)}")
            logger.info(f"🤖 Autonomous Agent can now monitor these tags!")

        except Exception as e:
            logger.error(f"Error adding tags: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(add_simulator_tags())
