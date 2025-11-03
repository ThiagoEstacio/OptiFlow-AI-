#!/usr/bin/env python3
"""
Seed script for Asset Framework - Creates sample hierarchical asset structure
Similar to PI Vision Asset Framework example

Creates structure:
└── Terminal Portuário (Enterprise)
    └── Planta de Grãos (Site)
        ├── Área de Recepção (Area)
        │   ├── Moega 01 (Equipment)
        │   │   ├── Sensor de Nível (Component)
        │   │   └── Sensor de Temperatura (Component)
        │   └── Correia 01 (Equipment)
        │       ├── Motor Principal (Component)
        │       └── Sensor de Velocidade (Component)
        └── Área de Armazenamento (Area)
            ├── Silo 01 (Equipment)
            │   ├── Sensor de Nível (Component)
            │   └── Sensor de Temperatura (Component)
            └── Silo 02 (Equipment)
                ├── Sensor de Nível (Component)
                └── Sensor de Temperatura (Component)
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.asset import Asset, AssetAttribute, AssetTemplate, AssetType
from app.models.tag import Tag
from sqlalchemy import select
import uuid


async def get_tag_by_name(db: AsyncSession, tag_name: str):
    """Helper to find tag by name"""
    stmt = select(Tag).where(Tag.name == tag_name)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def seed_assets():
    """Seed the database with sample asset structure"""
    print("🌱 Starting Asset Framework seed...")

    async with AsyncSessionLocal() as db:
        try:
            # ============================================================
            # 1. CREATE ENTERPRISE (Top Level)
            # ============================================================
            print("\n📦 Creating Enterprise...")
            enterprise = Asset(
                name="Terminal Portuário OptiFlow",
                description="Terminal Portuário de Grãos - Sistema de Gestão Industrial",
                asset_type=AssetType.ENTERPRISE,
                metadata={
                    "location": "Porto de Santos, SP",
                    "capacity": "1.000.000 ton/year",
                    "established": "2020",
                    "contact": "operacao@optiflow.com.br"
                }
            )
            db.add(enterprise)
            await db.flush()
            print(f"✓ Enterprise created: {enterprise.name} ({enterprise.id})")

            # ============================================================
            # 2. CREATE SITE
            # ============================================================
            print("\n🏭 Creating Site...")
            site = Asset(
                name="Planta de Grãos Principal",
                description="Planta principal de recepção e armazenamento de grãos",
                asset_type=AssetType.SITE,
                parent_id=enterprise.id,
                metadata={
                    "area": "50.000 m²",
                    "silos_count": 10,
                    "conveyor_length": "2 km",
                    "port_capacity": "5.000 ton/day"
                }
            )
            db.add(site)
            await db.flush()
            print(f"✓ Site created: {site.name} ({site.id})")

            # ============================================================
            # 3. CREATE AREAS
            # ============================================================
            print("\n📍 Creating Areas...")

            # Area 1: Recepção
            area_recepcao = Asset(
                name="Área de Recepção",
                description="Área responsável pela recepção de grãos dos caminhões",
                asset_type=AssetType.AREA,
                parent_id=site.id,
                metadata={
                    "moegas_count": 2,
                    "capacity": "200 ton/hour",
                    "operating_hours": "24/7"
                }
            )
            db.add(area_recepcao)

            # Area 2: Armazenamento
            area_armazenamento = Asset(
                name="Área de Armazenamento",
                description="Área de armazenamento em silos verticais",
                asset_type=AssetType.AREA,
                parent_id=site.id,
                metadata={
                    "silos_count": 4,
                    "total_capacity": "40.000 ton",
                    "temperature_control": "Yes"
                }
            )
            db.add(area_armazenamento)

            await db.flush()
            print(f"✓ Area created: {area_recepcao.name}")
            print(f"✓ Area created: {area_armazenamento.name}")

            # ============================================================
            # 4. CREATE EQUIPMENT (Recepção)
            # ============================================================
            print("\n⚙️  Creating Equipment (Recepção)...")

            # Moega 01
            moega_01 = Asset(
                name="Moega 01",
                description="Moega de recepção com capacidade de 50 toneladas",
                asset_type=AssetType.EQUIPMENT,
                parent_id=area_recepcao.id,
                metadata={
                    "capacity": "50 ton",
                    "manufacturer": "Acme Industries",
                    "model": "MRG-50",
                    "installation_date": "2020-01-15",
                    "maintenance_interval": "6 months"
                }
            )
            db.add(moega_01)

            # Correia 01
            correia_01 = Asset(
                name="Correia Transportadora 01",
                description="Correia transportadora com velocidade variável",
                asset_type=AssetType.EQUIPMENT,
                parent_id=area_recepcao.id,
                metadata={
                    "length": "150 m",
                    "speed_max": "2.5 m/s",
                    "manufacturer": "BeltTech",
                    "model": "CT-150",
                    "power": "30 kW"
                }
            )
            db.add(correia_01)

            await db.flush()
            print(f"✓ Equipment created: {moega_01.name}")
            print(f"✓ Equipment created: {correia_01.name}")

            # ============================================================
            # 5. CREATE EQUIPMENT (Armazenamento)
            # ============================================================
            print("\n⚙️  Creating Equipment (Armazenamento)...")

            # Silo 01
            silo_01 = Asset(
                name="Silo 01",
                description="Silo de armazenamento vertical com 10.000 ton de capacidade",
                asset_type=AssetType.EQUIPMENT,
                parent_id=area_armazenamento.id,
                metadata={
                    "capacity": "10.000 ton",
                    "height": "40 m",
                    "diameter": "12 m",
                    "material": "Aço carbono",
                    "ventilation": "Forced air system"
                }
            )
            db.add(silo_01)

            # Silo 02
            silo_02 = Asset(
                name="Silo 02",
                description="Silo de armazenamento vertical com 10.000 ton de capacidade",
                asset_type=AssetType.EQUIPMENT,
                parent_id=area_armazenamento.id,
                metadata={
                    "capacity": "10.000 ton",
                    "height": "40 m",
                    "diameter": "12 m",
                    "material": "Aço carbono",
                    "ventilation": "Forced air system"
                }
            )
            db.add(silo_02)

            await db.flush()
            print(f"✓ Equipment created: {silo_01.name}")
            print(f"✓ Equipment created: {silo_02.name}")

            # ============================================================
            # 6. CREATE COMPONENTS
            # ============================================================
            print("\n🔧 Creating Components...")

            # Moega 01 - Components
            moega_01_nivel = Asset(
                name="Sensor de Nível Moega 01",
                description="Sensor ultrassônico de nível",
                asset_type=AssetType.COMPONENT,
                parent_id=moega_01.id,
                metadata={"sensor_type": "Ultrasonic", "range": "0-10m"}
            )
            db.add(moega_01_nivel)

            # Correia 01 - Components
            correia_01_motor = Asset(
                name="Motor Principal Correia 01",
                description="Motor elétrico 30kW",
                asset_type=AssetType.COMPONENT,
                parent_id=correia_01.id,
                metadata={"power": "30 kW", "voltage": "380V", "rpm": "1750"}
            )
            db.add(correia_01_motor)

            # Silo 01 - Components
            silo_01_nivel = Asset(
                name="Sensor de Nível Silo 01",
                description="Sensor radar de nível",
                asset_type=AssetType.COMPONENT,
                parent_id=silo_01.id,
                metadata={"sensor_type": "Radar", "range": "0-40m"}
            )
            db.add(silo_01_nivel)

            silo_01_temp = Asset(
                name="Sensor de Temperatura Silo 01",
                description="Sensor de temperatura PT100",
                asset_type=AssetType.COMPONENT,
                parent_id=silo_01.id,
                metadata={"sensor_type": "PT100", "range": "-50 to 200°C"}
            )
            db.add(silo_01_temp)

            await db.flush()
            print(f"✓ Component created: {moega_01_nivel.name}")
            print(f"✓ Component created: {correia_01_motor.name}")
            print(f"✓ Component created: {silo_01_nivel.name}")
            print(f"✓ Component created: {silo_01_temp.name}")

            # ============================================================
            # 7. CREATE ASSET ATTRIBUTES (Link to Tags)
            # ============================================================
            print("\n🏷️  Creating Asset Attributes (linking to Tags)...")

            # Try to find some tags to link
            correia_vel_tag = await get_tag_by_name(db, "CORREIA_01_VELOCIDADE")
            correia_corrente_tag = await get_tag_by_name(db, "CORREIA_01_CORRENTE")
            silo_nivel_tag = await get_tag_by_name(db, "SILO_01_NIVEL")
            silo_temp_tag = await get_tag_by_name(db, "SILO_01_TEMPERATURA")

            attributes_created = 0

            # Correia 01 Attributes
            if correia_vel_tag:
                attr_vel = AssetAttribute(
                    asset_id=correia_01.id,
                    name="Velocidade",
                    description="Velocidade atual da correia",
                    attribute_type="tag_reference",
                    tag_id=correia_vel_tag.id,
                    unit="m/s",
                    display_order=1,
                    settings={"min": 0, "max": 2.5, "warning": 2.3}
                )
                db.add(attr_vel)
                attributes_created += 1
                print(f"✓ Attribute created: {correia_01.name} -> {attr_vel.name}")

            if correia_corrente_tag:
                attr_corrente = AssetAttribute(
                    asset_id=correia_01.id,
                    name="Corrente do Motor",
                    description="Corrente elétrica do motor",
                    attribute_type="tag_reference",
                    tag_id=correia_corrente_tag.id,
                    unit="A",
                    display_order=2,
                    settings={"min": 0, "max": 60, "critical": 55}
                )
                db.add(attr_corrente)
                attributes_created += 1
                print(f"✓ Attribute created: {correia_01.name} -> {attr_corrente.name}")

            # Silo 01 Attributes
            if silo_nivel_tag:
                attr_nivel = AssetAttribute(
                    asset_id=silo_01.id,
                    name="Nível",
                    description="Nível de grãos no silo",
                    attribute_type="tag_reference",
                    tag_id=silo_nivel_tag.id,
                    unit="%",
                    display_order=1,
                    settings={"min": 0, "max": 100, "target": 80}
                )
                db.add(attr_nivel)
                attributes_created += 1
                print(f"✓ Attribute created: {silo_01.name} -> {attr_nivel.name}")

            if silo_temp_tag:
                attr_temp = AssetAttribute(
                    asset_id=silo_01.id,
                    name="Temperatura",
                    description="Temperatura dos grãos",
                    attribute_type="tag_reference",
                    tag_id=silo_temp_tag.id,
                    unit="°C",
                    display_order=2,
                    settings={"min": 0, "max": 60, "warning": 40, "critical": 50}
                )
                db.add(attr_temp)
                attributes_created += 1
                print(f"✓ Attribute created: {silo_01.name} -> {attr_temp.name}")

            # Add some static and calculated attributes
            attr_static = AssetAttribute(
                asset_id=correia_01.id,
                name="Velocidade Nominal",
                description="Velocidade nominal de projeto",
                attribute_type="static",
                static_value="2.0",
                unit="m/s",
                display_order=10
            )
            db.add(attr_static)
            attributes_created += 1
            print(f"✓ Static attribute created: {correia_01.name} -> {attr_static.name}")

            # ============================================================
            # 8. COMMIT ALL
            # ============================================================
            await db.commit()

            print("\n" + "="*60)
            print("✅ Asset Framework seed completed successfully!")
            print("="*60)
            print(f"\n📊 Summary:")
            print(f"   - 1 Enterprise")
            print(f"   - 1 Site")
            print(f"   - 2 Areas")
            print(f"   - 4 Equipment")
            print(f"   - 4 Components")
            print(f"   - {attributes_created} Attributes")
            print(f"\n   Total Assets: {1 + 1 + 2 + 4 + 4} = 12 assets")
            print(f"\n🌳 Asset Tree:")
            print(f"   {enterprise.name}")
            print(f"   └── {site.name}")
            print(f"       ├── {area_recepcao.name}")
            print(f"       │   ├── {moega_01.name}")
            print(f"       │   └── {correia_01.name}")
            print(f"       └── {area_armazenamento.name}")
            print(f"           ├── {silo_01.name}")
            print(f"           └── {silo_02.name}")
            print("\n✓ Ready to use Asset Framework in Dashboard Builder!")

        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error seeding assets: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    asyncio.run(seed_assets())
