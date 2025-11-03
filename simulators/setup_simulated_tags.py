#!/usr/bin/env python3
"""
Setup Simulated Tags in OptiFlow AI Database
Creates device and tags for the Industrial Tags Simulator

This script configures all simulated tags in the OptiFlow database
Compatible with PI Vision and Power BI visualization workflows
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime
import os
import uuid

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://optiflow:optiflow_password@localhost:5432/optiflow"
)


class TagConfigurator:
    """Configure simulated tags in OptiFlow database"""

    def __init__(self):
        self.engine = None
        self.async_session = None

        # Tag definitions (matching industrial_tags_simulator.py)
        self.tag_definitions = {
            # PROCESS TAGS - Analog
            "TEMP_REACTOR_01": {
                "address": "40001", "data_type": "float", "unit": "°C", "category": "process",
                "min_value": 20.0, "max_value": 100.0, "scaling_factor": 0.1,
                "description": "Reactor temperature sensor", "scan_rate": 1000
            },
            "PRES_VESSEL_01": {
                "address": "40003", "data_type": "float", "unit": "bar", "category": "process",
                "min_value": 0.0, "max_value": 10.0, "scaling_factor": 0.01,
                "description": "Pressure vessel gauge", "scan_rate": 1000
            },
            "FLOW_INLET_01": {
                "address": "40005", "data_type": "float", "unit": "L/min", "category": "process",
                "min_value": 0.0, "max_value": 1000.0, "scaling_factor": 1.0,
                "description": "Inlet flow meter", "scan_rate": 1000
            },
            "LEVEL_TANK_01": {
                "address": "40007", "data_type": "float", "unit": "%", "category": "process",
                "min_value": 0.0, "max_value": 100.0, "scaling_factor": 0.1,
                "description": "Tank level transmitter", "scan_rate": 1000
            },
            "PH_ANALYZER_01": {
                "address": "40009", "data_type": "float", "unit": "pH", "category": "quality",
                "min_value": 0.0, "max_value": 14.0, "scaling_factor": 0.01,
                "description": "pH analyzer", "scan_rate": 2000
            },
            "COND_ANALYZER_01": {
                "address": "40011", "data_type": "float", "unit": "µS/cm", "category": "quality",
                "min_value": 0.0, "max_value": 5000.0, "scaling_factor": 1.0,
                "description": "Conductivity analyzer", "scan_rate": 2000
            },

            # ENERGY TAGS
            "POWER_MOTOR_01": {
                "address": "40013", "data_type": "float", "unit": "kW", "category": "energy",
                "min_value": 0.0, "max_value": 10000.0, "scaling_factor": 1.0,
                "description": "Motor power consumption", "scan_rate": 1000
            },
            "CURRENT_MOTOR_01": {
                "address": "40015", "data_type": "float", "unit": "A", "category": "energy",
                "min_value": 0.0, "max_value": 200.0, "scaling_factor": 0.1,
                "description": "Motor current", "scan_rate": 1000
            },
            "VOLTAGE_LINE_01": {
                "address": "40017", "data_type": "float", "unit": "V", "category": "energy",
                "min_value": 0.0, "max_value": 500.0, "scaling_factor": 1.0,
                "description": "Line voltage", "scan_rate": 1000
            },
            "PF_MOTOR_01": {
                "address": "40019", "data_type": "float", "unit": "", "category": "energy",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 0.001,
                "description": "Power factor", "scan_rate": 1000
            },

            # PRODUCTION TAGS
            "RATE_PRODUCTION": {
                "address": "40021", "data_type": "float", "unit": "units/h", "category": "production",
                "min_value": 0.0, "max_value": 200.0, "scaling_factor": 1.0,
                "description": "Production rate", "scan_rate": 5000
            },
            "COUNT_PRODUCTION": {
                "address": "40023", "data_type": "integer", "unit": "units", "category": "production",
                "min_value": 0.0, "max_value": 999999.0, "scaling_factor": 1.0,
                "description": "Production counter", "scan_rate": 5000
            },
            "OEE_LINE_01": {
                "address": "40025", "data_type": "float", "unit": "%", "category": "production",
                "min_value": 0.0, "max_value": 100.0, "scaling_factor": 0.1,
                "description": "Overall Equipment Effectiveness", "scan_rate": 10000
            },
            "QUALITY_RATE": {
                "address": "40027", "data_type": "float", "unit": "%", "category": "quality",
                "min_value": 0.0, "max_value": 100.0, "scaling_factor": 0.1,
                "description": "Quality rate", "scan_rate": 10000
            },

            # EQUIPMENT/MAINTENANCE TAGS
            "SPEED_MOTOR_01": {
                "address": "40029", "data_type": "float", "unit": "RPM", "category": "process",
                "min_value": 0.0, "max_value": 3000.0, "scaling_factor": 1.0,
                "description": "Motor speed", "scan_rate": 1000
            },
            "TEMP_BEARING_01": {
                "address": "40031", "data_type": "float", "unit": "°C", "category": "maintenance",
                "min_value": 20.0, "max_value": 100.0, "scaling_factor": 0.1,
                "description": "Bearing temperature", "scan_rate": 2000
            },
            "VIB_X_MOTOR_01": {
                "address": "40033", "data_type": "float", "unit": "mm/s", "category": "maintenance",
                "min_value": 0.0, "max_value": 10.0, "scaling_factor": 0.01,
                "description": "Vibration X-axis", "scan_rate": 500
            },
            "VIB_Y_MOTOR_01": {
                "address": "40035", "data_type": "float", "unit": "mm/s", "category": "maintenance",
                "min_value": 0.0, "max_value": 10.0, "scaling_factor": 0.01,
                "description": "Vibration Y-axis", "scan_rate": 500
            },

            # DIGITAL/STATUS TAGS (Coils)
            "STATUS_MOTOR_RUNNING": {
                "address": "00001", "data_type": "boolean", "unit": "", "category": "status",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 1.0,
                "description": "Motor running status", "scan_rate": 1000
            },
            "STATUS_VALVE_OPEN": {
                "address": "00002", "data_type": "boolean", "unit": "", "category": "status",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 1.0,
                "description": "Valve open status", "scan_rate": 1000
            },
            "STATUS_PUMP_RUNNING": {
                "address": "00003", "data_type": "boolean", "unit": "", "category": "status",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 1.0,
                "description": "Pump running status", "scan_rate": 1000
            },
            "ALARM_HIGH_TEMP": {
                "address": "00004", "data_type": "boolean", "unit": "", "category": "alarm",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 1.0,
                "description": "High temperature alarm", "scan_rate": 1000
            },
            "ALARM_HIGH_PRES": {
                "address": "00005", "data_type": "boolean", "unit": "", "category": "alarm",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 1.0,
                "description": "High pressure alarm", "scan_rate": 1000
            },
            "ALARM_EMERGENCY": {
                "address": "00006", "data_type": "boolean", "unit": "", "category": "alarm",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 1.0,
                "description": "Emergency stop", "scan_rate": 500
            },
            "MODE_MAINTENANCE": {
                "address": "00007", "data_type": "boolean", "unit": "", "category": "status",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 1.0,
                "description": "Maintenance mode", "scan_rate": 2000
            },
            "MODE_AUTO": {
                "address": "00008", "data_type": "boolean", "unit": "", "category": "status",
                "min_value": 0.0, "max_value": 1.0, "scaling_factor": 1.0,
                "description": "Automatic mode", "scan_rate": 2000
            },
        }

    async def connect(self):
        """Connect to database"""
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def disconnect(self):
        """Disconnect from database"""
        if self.engine:
            await self.engine.dispose()

    async def get_or_create_site(self, session: AsyncSession) -> str:
        """Get or create demo site"""
        # Check if site exists
        result = await session.execute(
            text("SELECT id FROM sites WHERE name = 'Demo Industrial Plant' LIMIT 1")
        )
        site = result.fetchone()

        if site:
            print(f"✓ Site found: Demo Industrial Plant (ID: {site[0]})")
            return site[0]

        # Create site
        site_id = str(uuid.uuid4())
        await session.execute(
            text("""
                INSERT INTO sites (id, name, site_type, address, city, state, country,
                                   latitude, longitude, is_active, created_at, updated_at)
                VALUES (:id, :name, :site_type, :address, :city, :state, :country,
                        :latitude, :longitude, :is_active, :created_at, :updated_at)
            """),
            {
                "id": site_id,
                "name": "Demo Industrial Plant",
                "site_type": "smartport",
                "address": "Industrial District",
                "city": "São Paulo",
                "state": "SP",
                "country": "Brazil",
                "latitude": -23.5505,
                "longitude": -46.6333,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
        await session.commit()
        print(f"✓ Created site: Demo Industrial Plant (ID: {site_id})")
        return site_id

    async def get_or_create_device(self, session: AsyncSession, site_id: str) -> str:
        """Get or create simulator device"""
        # Check if device exists
        result = await session.execute(
            text("SELECT id FROM devices WHERE name = 'Industrial Simulator' LIMIT 1")
        )
        device = result.fetchone()

        if device:
            print(f"✓ Device found: Industrial Simulator (ID: {device[0]})")
            return device[0]

        # Create device
        device_id = str(uuid.uuid4())
        await session.execute(
            text("""
                INSERT INTO devices (id, site_id, name, protocol, ip_address, port,
                                     device_type, manufacturer, model, enabled, status,
                                     created_at, updated_at)
                VALUES (:id, :site_id, :name, :protocol, :ip_address, :port,
                        :device_type, :manufacturer, :model, :enabled, :status,
                        :created_at, :updated_at)
            """),
            {
                "id": device_id,
                "site_id": site_id,
                "name": "Industrial Simulator",
                "protocol": "modbus_tcp",
                "ip_address": "localhost",
                "port": 5020,
                "device_type": "PLC",
                "manufacturer": "OptiFlow AI",
                "model": "ITS-1000",
                "enabled": True,
                "status": "connected",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
        await session.commit()
        print(f"✓ Created device: Industrial Simulator (ID: {device_id})")
        return device_id

    async def create_tag(self, session: AsyncSession, device_id: str, tag_name: str, tag_def: dict):
        """Create a single tag"""
        tag_id = str(uuid.uuid4())

        await session.execute(
            text("""
                INSERT INTO tags (id, device_id, name, address, data_type, unit, category,
                                  description, min_value, max_value, scaling_factor, scan_rate,
                                  enabled, log_enabled, created_at, updated_at)
                VALUES (:id, :device_id, :name, :address, :data_type, :unit, :category,
                        :description, :min_value, :max_value, :scaling_factor, :scan_rate,
                        :enabled, :log_enabled, :created_at, :updated_at)
                ON CONFLICT (device_id, name) DO UPDATE SET
                    address = EXCLUDED.address,
                    data_type = EXCLUDED.data_type,
                    unit = EXCLUDED.unit,
                    category = EXCLUDED.category,
                    description = EXCLUDED.description,
                    min_value = EXCLUDED.min_value,
                    max_value = EXCLUDED.max_value,
                    scaling_factor = EXCLUDED.scaling_factor,
                    scan_rate = EXCLUDED.scan_rate,
                    updated_at = EXCLUDED.updated_at
            """),
            {
                "id": tag_id,
                "device_id": device_id,
                "name": tag_name,
                "address": tag_def["address"],
                "data_type": tag_def["data_type"],
                "unit": tag_def["unit"] or None,
                "category": tag_def["category"],
                "description": tag_def["description"],
                "min_value": tag_def["min_value"],
                "max_value": tag_def["max_value"],
                "scaling_factor": tag_def["scaling_factor"],
                "scan_rate": tag_def["scan_rate"],
                "enabled": True,
                "log_enabled": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

    async def setup_all_tags(self):
        """Setup all tags in database"""
        try:
            print("\n" + "=" * 80)
            print("🏭 OptiFlow AI - Industrial Tags Setup")
            print("=" * 80 + "\n")

            await self.connect()

            async with self.async_session() as session:
                # Get or create site
                print("📍 Step 1: Site Configuration")
                site_id = await self.get_or_create_site(session)

                # Get or create device
                print("\n📡 Step 2: Device Configuration")
                device_id = await self.get_or_create_device(session, site_id)

                # Create tags
                print(f"\n🏷️  Step 3: Creating {len(self.tag_definitions)} Tags")
                print("-" * 80)

                category_counts = {}
                for tag_name, tag_def in sorted(self.tag_definitions.items()):
                    await self.create_tag(session, device_id, tag_name, tag_def)
                    category = tag_def["category"]
                    category_counts[category] = category_counts.get(category, 0) + 1
                    print(f"  ✓ {tag_name:<25} ({tag_def['category']:<12}) - {tag_def['description']}")

                await session.commit()

                print("-" * 80)
                print("\n📊 Tags Created by Category:")
                for category, count in sorted(category_counts.items()):
                    print(f"   • {category:<15}: {count} tags")

                print("\n" + "=" * 80)
                print("✅ SUCCESS! All tags configured")
                print("=" * 80)
                print("\n📋 Next Steps:")
                print("   1. Start the simulator:")
                print("      python simulators/industrial_tags_simulator.py")
                print("\n   2. Start OptiFlow backend (if not running):")
                print("      docker compose up -d backend")
                print("\n   3. View tags in frontend:")
                print("      http://localhost:3000/tags")
                print("\n   4. Create visualizations:")
                print("      http://localhost:3000/analytics")
                print("\n" + "=" * 80 + "\n")

                return True

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.disconnect()


async def main():
    """Main function"""
    configurator = TagConfigurator()
    success = await configurator.setup_all_tags()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
