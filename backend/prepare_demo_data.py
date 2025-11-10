"""
Prepare Demo Data

Popula o sistema com dados de demonstração para as views:
- Tags no PostgreSQL
- Dados históricos no InfluxDB
- Dados em tempo real simulados
"""
import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import AsyncSessionLocal
from app.models.tag import Tag, TagCategory, TagDataType
from app.models.organization import Organization
from app.services.influxdb import influxdb_service


# Demo tags configuration
DEMO_TAGS = [
    {
        'name': 'energy_consumption',
        'description': 'Total Energy Consumption',
        'unit': 'kWh',
        'category': TagCategory.ENERGY,
        'data_type': TagDataType.FLOAT,
        'min_value': 800.0,
        'max_value': 1500.0,
    },
    {
        'name': 'production_rate',
        'description': 'Production Rate',
        'unit': 'tons/h',
        'category': TagCategory.PROCESS,
        'data_type': TagDataType.FLOAT,
        'min_value': 50.0,
        'max_value': 150.0,
    },
    {
        'name': 'conveyor_speed',
        'description': 'Conveyor Belt Speed',
        'unit': 'm/s',
        'category': TagCategory.PROCESS,
        'data_type': TagDataType.FLOAT,
        'min_value': 0.5,
        'max_value': 3.0,
    },
    {
        'name': 'motor_temperature',
        'description': 'Motor Temperature',
        'unit': '°C',
        'category': TagCategory.MAINTENANCE,
        'data_type': TagDataType.FLOAT,
        'min_value': 40.0,
        'max_value': 85.0,
    },
    {
        'name': 'vibration_level',
        'description': 'Vibration Level',
        'unit': 'mm/s',
        'category': TagCategory.MAINTENANCE,
        'data_type': TagDataType.FLOAT,
        'min_value': 0.5,
        'max_value': 5.0,
    },
    {
        'name': 'pressure_sensor_1',
        'description': 'Pressure Sensor 1',
        'unit': 'bar',
        'category': TagCategory.PROCESS,
        'data_type': TagDataType.FLOAT,
        'min_value': 1.0,
        'max_value': 8.0,
    },
    {
        'name': 'flow_rate_01',
        'description': 'Flow Rate 01',
        'unit': 'm3/h',
        'category': TagCategory.PROCESS,
        'data_type': TagDataType.FLOAT,
        'min_value': 10.0,
        'max_value': 50.0,
    },
    {
        'name': 'quality_index',
        'description': 'Product Quality Index',
        'unit': '%',
        'category': TagCategory.QUALITY,
        'data_type': TagDataType.FLOAT,
        'min_value': 85.0,
        'max_value': 100.0,
    },
    {
        'name': 'ambient_temperature',
        'description': 'Ambient Temperature',
        'unit': '°C',
        'category': TagCategory.PROCESS,
        'data_type': TagDataType.FLOAT,
        'min_value': 15.0,
        'max_value': 35.0,
    },
    {
        'name': 'humidity_level',
        'description': 'Humidity Level',
        'unit': '%',
        'category': TagCategory.PROCESS,
        'data_type': TagDataType.FLOAT,
        'min_value': 30.0,
        'max_value': 80.0,
    },
]


async def create_demo_tags(db: AsyncSession):
    """Create demo tags in PostgreSQL"""
    print("Creating demo tags in PostgreSQL...")

    # Get first organization
    result = await db.execute(select(Organization).limit(1))
    organization = result.scalar_one_or_none()

    if not organization:
        print("ERROR: No organization found. Please create an organization first.")
        return []

    created_tags = []

    for tag_config in DEMO_TAGS:
        # Check if tag already exists
        result = await db.execute(
            select(Tag).where(Tag.name == tag_config['name'])
        )
        existing_tag = result.scalar_one_or_none()

        if existing_tag:
            print(f"  ✓ Tag '{tag_config['name']}' already exists")
            created_tags.append(existing_tag)
            continue

        # Create new tag
        tag = Tag(
            name=tag_config['name'],
            tag_address=tag_config['name'],
            description=tag_config['description'],
            unit=tag_config['unit'],
            category=tag_config['category'],
            data_type=tag_config['data_type'],
            min_value=tag_config['min_value'],
            max_value=tag_config['max_value'],
            is_active=True,
            organization_id=organization.id
        )

        db.add(tag)
        created_tags.append(tag)
        print(f"  + Created tag '{tag_config['name']}'")

    await db.commit()
    print(f"✅ Created/verified {len(created_tags)} demo tags")
    return created_tags


def generate_historical_data(tag_config, days=7):
    """Generate historical data for a tag"""
    data_points = []
    now = datetime.now()

    # Generate data points every 5 minutes
    interval = timedelta(minutes=5)
    num_points = int((days * 24 * 60) / 5)  # Total 5-minute intervals

    base_value = (tag_config['min_value'] + tag_config['max_value']) / 2
    value_range = tag_config['max_value'] - tag_config['min_value']

    for i in range(num_points):
        timestamp = now - (timedelta(days=days) - (interval * i))

        # Add realistic patterns
        hour = timestamp.hour
        day_of_week = timestamp.weekday()

        # Working hours pattern (higher values during day)
        time_factor = 1.0
        if 6 <= hour <= 18:  # Day shift
            time_factor = 1.2
        elif hour < 6 or hour > 22:  # Night
            time_factor = 0.8

        # Weekend pattern (lower values)
        if day_of_week >= 5:  # Weekend
            time_factor *= 0.7

        # Base value with pattern
        value = base_value * time_factor

        # Add noise
        noise = random.uniform(-0.1, 0.1) * value_range
        value += noise

        # Add occasional anomalies (5% chance)
        if random.random() < 0.05:
            anomaly = random.choice([-1, 1]) * random.uniform(0.2, 0.4) * value_range
            value += anomaly

        # Clamp to min/max
        value = max(tag_config['min_value'], min(tag_config['max_value'], value))

        data_points.append({
            'measurement': tag_config['name'],
            'timestamp': timestamp,
            'value': round(value, 2),
            'quality': 'good' if random.random() > 0.02 else 'uncertain'
        })

    return data_points


def populate_influxdb(tags_config):
    """Populate InfluxDB with historical data"""
    print("\nPopulating InfluxDB with historical data...")

    for tag_config in tags_config:
        print(f"  Generating data for '{tag_config['name']}'...")

        # Generate 7 days of data
        data_points = generate_historical_data(tag_config, days=7)

        # Write to InfluxDB in batches
        batch_size = 1000
        for i in range(0, len(data_points), batch_size):
            batch = data_points[i:i+batch_size]

            try:
                for point in batch:
                    influxdb_service.write_value(
                        tag_name=point['measurement'],
                        value=point['value'],
                        timestamp=point['timestamp'],
                        quality=point['quality']
                    )
            except Exception as e:
                print(f"    Warning: Error writing batch: {e}")

        print(f"  ✓ Written {len(data_points)} points for '{tag_config['name']}'")

    print(f"✅ InfluxDB populated with {len(tags_config)} tags")


async def main():
    """Main function"""
    print("=" * 60)
    print("PREPARING DEMO DATA")
    print("=" * 60)

    # Create PostgreSQL session
    async with AsyncSessionLocal() as db:
        # Step 1: Create demo tags
        tags = await create_demo_tags(db)

    # Step 2: Populate InfluxDB
    populate_influxdb(DEMO_TAGS)

    print("\n" + "=" * 60)
    print("✅ DEMO DATA PREPARATION COMPLETE!")
    print("=" * 60)
    print("\nYou can now:")
    print("  1. Open /data/realtime to see real-time data")
    print("  2. Open /data/historical to analyze historical trends")
    print("  3. Open /data/alarms-events to see alarms")
    print("  4. Open /ml-demo to run ML models")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
