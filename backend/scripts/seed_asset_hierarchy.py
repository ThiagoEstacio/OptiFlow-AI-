"""
Seed Asset Hierarchy for ML-based Anomaly Detection
====================================================

Creates:
1. Asset Templates for each equipment type with ML-relevant attributes
2. Hierarchical asset structure (Enterprise > Site > Area > Unit > Equipment > Component)
3. Asset attributes with physical correlations for ML training

Run with: docker compose exec backend python -m scripts.seed_asset_hierarchy
"""

import asyncio
import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path
import sys
sys.path.insert(0, '/app')

from app.db.session import AsyncSessionLocal
from app.models.asset import Asset, AssetType, AssetTemplate, AssetAttribute


# =============================================================================
# ASSET TEMPLATES - Define ML-relevant attributes for each equipment type
# =============================================================================

ASSET_TEMPLATES = [
    {
        "name": "Motor Elétrico",
        "description": "Template para motores elétricos com monitoramento de vibração, temperatura e corrente",
        "asset_type": AssetType.EQUIPMENT,
        "attribute_definitions": [
            # Raw sensor readings
            {"name": "vibration_mms", "attribute_type": "tag_reference", "unit": "mm/s",
             "description": "Vibração do motor", "settings": {"min": 0, "max": 10, "warning": 4, "alarm": 7}},
            {"name": "temperature_c", "attribute_type": "tag_reference", "unit": "°C",
             "description": "Temperatura do motor", "settings": {"min": 20, "max": 100, "warning": 70, "alarm": 85}},
            {"name": "current_a", "attribute_type": "tag_reference", "unit": "A",
             "description": "Corrente do motor", "settings": {"min": 0, "max": 150, "warning": 100, "alarm": 130}},
            {"name": "power_kw", "attribute_type": "tag_reference", "unit": "kW",
             "description": "Potência consumida", "settings": {"min": 0, "max": 100}},
            {"name": "speed_rpm", "attribute_type": "tag_reference", "unit": "RPM",
             "description": "Velocidade do motor", "settings": {"min": 0, "max": 1800}},
            # Static design values
            {"name": "rated_power_kw", "attribute_type": "static", "static_value": "75", "unit": "kW",
             "description": "Potência nominal do motor"},
            {"name": "rated_current_a", "attribute_type": "static", "static_value": "100", "unit": "A",
             "description": "Corrente nominal"},
            {"name": "rated_speed_rpm", "attribute_type": "static", "static_value": "1750", "unit": "RPM",
             "description": "Velocidade nominal"},
            # Calculated ML features
            {"name": "load_pct", "attribute_type": "calculated", "unit": "%",
             "formula": "{power_kw} / {rated_power_kw} * 100", "description": "Percentual de carga"},
            {"name": "current_ratio", "attribute_type": "calculated", "unit": "%",
             "formula": "{current_a} / {rated_current_a} * 100", "description": "Razão de corrente"},
            {"name": "speed_deviation", "attribute_type": "calculated", "unit": "%",
             "formula": "({speed_rpm} - {rated_speed_rpm}) / {rated_speed_rpm} * 100", "description": "Desvio de velocidade"},
            {"name": "vibration_per_load", "attribute_type": "calculated", "unit": "mm/s/%",
             "formula": "{vibration_mms} / max({load_pct}, 1)", "description": "Vibração normalizada pela carga"},
        ]
    },
    {
        "name": "Bomba Centrífuga",
        "description": "Template para bombas centrífugas com monitoramento de vazão, pressão e eficiência",
        "asset_type": AssetType.EQUIPMENT,
        "attribute_definitions": [
            # Raw sensor readings
            {"name": "flow_m3h", "attribute_type": "tag_reference", "unit": "m³/h",
             "description": "Vazão da bomba", "settings": {"min": 0, "max": 500, "warning": 450, "alarm": 480}},
            {"name": "discharge_pressure_bar", "attribute_type": "tag_reference", "unit": "bar",
             "description": "Pressão de descarga", "settings": {"min": 0, "max": 15, "warning": 12, "alarm": 14}},
            {"name": "suction_pressure_bar", "attribute_type": "tag_reference", "unit": "bar",
             "description": "Pressão de sucção", "settings": {"min": -1, "max": 5}},
            {"name": "vibration_mms", "attribute_type": "tag_reference", "unit": "mm/s",
             "description": "Vibração da bomba", "settings": {"min": 0, "max": 10, "warning": 5, "alarm": 8}},
            {"name": "temperature_c", "attribute_type": "tag_reference", "unit": "°C",
             "description": "Temperatura do mancal", "settings": {"min": 20, "max": 90, "warning": 70, "alarm": 80}},
            {"name": "current_a", "attribute_type": "tag_reference", "unit": "A",
             "description": "Corrente do motor", "settings": {"min": 0, "max": 200}},
            {"name": "power_kw", "attribute_type": "tag_reference", "unit": "kW",
             "description": "Potência consumida", "settings": {"min": 0, "max": 150}},
            # Static design values
            {"name": "rated_flow_m3h", "attribute_type": "static", "static_value": "400", "unit": "m³/h",
             "description": "Vazão nominal"},
            {"name": "rated_head_m", "attribute_type": "static", "static_value": "50", "unit": "m",
             "description": "Head nominal"},
            {"name": "rated_power_kw", "attribute_type": "static", "static_value": "110", "unit": "kW",
             "description": "Potência nominal"},
            # Calculated ML features
            {"name": "differential_pressure", "attribute_type": "calculated", "unit": "bar",
             "formula": "{discharge_pressure_bar} - {suction_pressure_bar}", "description": "Pressão diferencial"},
            {"name": "hydraulic_power_kw", "attribute_type": "calculated", "unit": "kW",
             "formula": "{flow_m3h} * {differential_pressure} * 0.0272", "description": "Potência hidráulica"},
            {"name": "pump_efficiency", "attribute_type": "calculated", "unit": "%",
             "formula": "{hydraulic_power_kw} / max({power_kw}, 1) * 100", "description": "Eficiência da bomba"},
            {"name": "flow_ratio", "attribute_type": "calculated", "unit": "%",
             "formula": "{flow_m3h} / {rated_flow_m3h} * 100", "description": "Razão de vazão"},
        ]
    },
    {
        "name": "Correia Transportadora",
        "description": "Template para correias transportadoras com monitoramento de velocidade, carga e alinhamento",
        "asset_type": AssetType.EQUIPMENT,
        "attribute_definitions": [
            # Raw sensor readings
            {"name": "speed_ms", "attribute_type": "tag_reference", "unit": "m/s",
             "description": "Velocidade da correia", "settings": {"min": 0, "max": 5, "warning": 0.5, "alarm": 0.2}},
            {"name": "belt_load_tph", "attribute_type": "tag_reference", "unit": "t/h",
             "description": "Carga da correia", "settings": {"min": 0, "max": 2000, "warning": 1800, "alarm": 1950}},
            {"name": "motor_current_a", "attribute_type": "tag_reference", "unit": "A",
             "description": "Corrente do motor", "settings": {"min": 0, "max": 300}},
            {"name": "motor_power_kw", "attribute_type": "tag_reference", "unit": "kW",
             "description": "Potência do motor", "settings": {"min": 0, "max": 200}},
            {"name": "belt_tension_kn", "attribute_type": "tag_reference", "unit": "kN",
             "description": "Tensão da correia", "settings": {"min": 0, "max": 100, "warning": 80, "alarm": 90}},
            {"name": "pulley_temp_c", "attribute_type": "tag_reference", "unit": "°C",
             "description": "Temperatura do tambor", "settings": {"min": 20, "max": 80, "warning": 60, "alarm": 70}},
            {"name": "misalignment_mm", "attribute_type": "tag_reference", "unit": "mm",
             "description": "Desalinhamento", "settings": {"min": 0, "max": 50, "warning": 20, "alarm": 35}},
            # Static design values
            {"name": "rated_speed_ms", "attribute_type": "static", "static_value": "3.5", "unit": "m/s",
             "description": "Velocidade nominal"},
            {"name": "rated_capacity_tph", "attribute_type": "static", "static_value": "1500", "unit": "t/h",
             "description": "Capacidade nominal"},
            {"name": "belt_width_mm", "attribute_type": "static", "static_value": "1200", "unit": "mm",
             "description": "Largura da correia"},
            # Calculated ML features
            {"name": "speed_ratio", "attribute_type": "calculated", "unit": "%",
             "formula": "{speed_ms} / {rated_speed_ms} * 100", "description": "Razão de velocidade"},
            {"name": "load_ratio", "attribute_type": "calculated", "unit": "%",
             "formula": "{belt_load_tph} / {rated_capacity_tph} * 100", "description": "Razão de carga"},
            {"name": "specific_power", "attribute_type": "calculated", "unit": "kW/(t/h)",
             "formula": "{motor_power_kw} / max({belt_load_tph}, 1)", "description": "Potência específica"},
        ]
    },
    {
        "name": "Britador de Mandíbulas",
        "description": "Template para britadores com monitoramento de vibração, potência e produção",
        "asset_type": AssetType.EQUIPMENT,
        "attribute_definitions": [
            # Raw sensor readings
            {"name": "vibration_mms", "attribute_type": "tag_reference", "unit": "mm/s",
             "description": "Vibração do britador", "settings": {"min": 0, "max": 20, "warning": 12, "alarm": 16}},
            {"name": "motor_current_a", "attribute_type": "tag_reference", "unit": "A",
             "description": "Corrente do motor", "settings": {"min": 0, "max": 500}},
            {"name": "motor_power_kw", "attribute_type": "tag_reference", "unit": "kW",
             "description": "Potência do motor", "settings": {"min": 0, "max": 350}},
            {"name": "oil_pressure_bar", "attribute_type": "tag_reference", "unit": "bar",
             "description": "Pressão do óleo", "settings": {"min": 0, "max": 10, "warning": 2, "alarm": 1}},
            {"name": "oil_temp_c", "attribute_type": "tag_reference", "unit": "°C",
             "description": "Temperatura do óleo", "settings": {"min": 20, "max": 80, "warning": 65, "alarm": 75}},
            {"name": "css_mm", "attribute_type": "tag_reference", "unit": "mm",
             "description": "Abertura de saída (CSS)", "settings": {"min": 50, "max": 200}},
            {"name": "throughput_tph", "attribute_type": "tag_reference", "unit": "t/h",
             "description": "Produção", "settings": {"min": 0, "max": 800}},
            # Static design values
            {"name": "rated_power_kw", "attribute_type": "static", "static_value": "300", "unit": "kW",
             "description": "Potência nominal"},
            {"name": "rated_capacity_tph", "attribute_type": "static", "static_value": "600", "unit": "t/h",
             "description": "Capacidade nominal"},
            {"name": "max_feed_size_mm", "attribute_type": "static", "static_value": "750", "unit": "mm",
             "description": "Tamanho máximo de alimentação"},
            # Calculated ML features
            {"name": "load_pct", "attribute_type": "calculated", "unit": "%",
             "formula": "{motor_power_kw} / {rated_power_kw} * 100", "description": "Percentual de carga"},
            {"name": "throughput_ratio", "attribute_type": "calculated", "unit": "%",
             "formula": "{throughput_tph} / {rated_capacity_tph} * 100", "description": "Razão de produção"},
            {"name": "specific_energy", "attribute_type": "calculated", "unit": "kWh/t",
             "formula": "{motor_power_kw} / max({throughput_tph}, 1)", "description": "Energia específica"},
            {"name": "vibration_per_power", "attribute_type": "calculated", "unit": "mm/s/kW",
             "formula": "{vibration_mms} / max({motor_power_kw}, 1) * 100", "description": "Vibração por potência"},
        ]
    },
    {
        "name": "Elevador de Canecas",
        "description": "Template para elevadores de canecas com monitoramento de velocidade e carga",
        "asset_type": AssetType.EQUIPMENT,
        "attribute_definitions": [
            # Raw sensor readings
            {"name": "speed_ms", "attribute_type": "tag_reference", "unit": "m/s",
             "description": "Velocidade do elevador", "settings": {"min": 0, "max": 3, "warning": 0.5, "alarm": 0.3}},
            {"name": "motor_current_a", "attribute_type": "tag_reference", "unit": "A",
             "description": "Corrente do motor", "settings": {"min": 0, "max": 200}},
            {"name": "motor_power_kw", "attribute_type": "tag_reference", "unit": "kW",
             "description": "Potência do motor", "settings": {"min": 0, "max": 150}},
            {"name": "belt_slip_pct", "attribute_type": "tag_reference", "unit": "%",
             "description": "Escorregamento da correia", "settings": {"min": 0, "max": 10, "warning": 3, "alarm": 5}},
            {"name": "head_vibration_mms", "attribute_type": "tag_reference", "unit": "mm/s",
             "description": "Vibração do cabeçote", "settings": {"min": 0, "max": 15, "warning": 8, "alarm": 12}},
            {"name": "boot_vibration_mms", "attribute_type": "tag_reference", "unit": "mm/s",
             "description": "Vibração do pé", "settings": {"min": 0, "max": 15, "warning": 8, "alarm": 12}},
            {"name": "throughput_tph", "attribute_type": "tag_reference", "unit": "t/h",
             "description": "Produção", "settings": {"min": 0, "max": 500}},
            # Static design values
            {"name": "rated_speed_ms", "attribute_type": "static", "static_value": "2.0", "unit": "m/s",
             "description": "Velocidade nominal"},
            {"name": "rated_capacity_tph", "attribute_type": "static", "static_value": "400", "unit": "t/h",
             "description": "Capacidade nominal"},
            {"name": "lift_height_m", "attribute_type": "static", "static_value": "30", "unit": "m",
             "description": "Altura de elevação"},
            # Calculated ML features
            {"name": "speed_ratio", "attribute_type": "calculated", "unit": "%",
             "formula": "{speed_ms} / {rated_speed_ms} * 100", "description": "Razão de velocidade"},
            {"name": "load_ratio", "attribute_type": "calculated", "unit": "%",
             "formula": "{throughput_tph} / {rated_capacity_tph} * 100", "description": "Razão de carga"},
            {"name": "total_vibration", "attribute_type": "calculated", "unit": "mm/s",
             "formula": "({head_vibration_mms} + {boot_vibration_mms}) / 2", "description": "Vibração média"},
        ]
    }
]


# =============================================================================
# ASSET HIERARCHY - Process flow structure
# =============================================================================

ASSET_HIERARCHY = {
    "name": "OptiFlow Mining",
    "asset_type": AssetType.ENTERPRISE,
    "description": "Empresa de mineração OptiFlow",
    "children": [
        {
            "name": "Mina Serra Azul",
            "asset_type": AssetType.SITE,
            "description": "Planta de beneficiamento Serra Azul",
            "children": [
                {
                    "name": "Área de Britagem",
                    "asset_type": AssetType.AREA,
                    "description": "Área de britagem primária e secundária",
                    "children": [
                        {
                            "name": "Britagem Primária",
                            "asset_type": AssetType.UNIT,
                            "description": "Unidade de britagem primária",
                            "children": [
                                {
                                    "name": "Britador Primário 01",
                                    "asset_type": AssetType.EQUIPMENT,
                                    "template_name": "Britador de Mandíbulas",
                                    "equipment_id": "CRUSH01",
                                    "description": "Britador de mandíbulas primário",
                                    "process_flow": {"upstream": [], "downstream": ["CORR01"]}
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "Área de Transporte",
                    "asset_type": AssetType.AREA,
                    "description": "Sistema de correias transportadoras",
                    "children": [
                        {
                            "name": "Transporte Primário",
                            "asset_type": AssetType.UNIT,
                            "description": "Correias da britagem primária",
                            "children": [
                                {
                                    "name": "Correia Transportadora 01",
                                    "asset_type": AssetType.EQUIPMENT,
                                    "template_name": "Correia Transportadora",
                                    "equipment_id": "CORR01",
                                    "description": "Correia do britador para elevador",
                                    "process_flow": {"upstream": ["CRUSH01"], "downstream": ["ELEV01"]}
                                },
                                {
                                    "name": "Correia Transportadora 02",
                                    "asset_type": AssetType.EQUIPMENT,
                                    "template_name": "Correia Transportadora",
                                    "equipment_id": "CORR02",
                                    "description": "Correia do elevador para estoque",
                                    "process_flow": {"upstream": ["ELEV01"], "downstream": []}
                                }
                            ]
                        },
                        {
                            "name": "Elevação",
                            "asset_type": AssetType.UNIT,
                            "description": "Elevadores de canecas",
                            "children": [
                                {
                                    "name": "Elevador de Canecas 01",
                                    "asset_type": AssetType.EQUIPMENT,
                                    "template_name": "Elevador de Canecas",
                                    "equipment_id": "ELEV01",
                                    "description": "Elevador principal",
                                    "process_flow": {"upstream": ["CORR01"], "downstream": ["CORR02"]}
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "Área de Bombeamento",
                    "asset_type": AssetType.AREA,
                    "description": "Sistema de bombeamento de água e polpa",
                    "children": [
                        {
                            "name": "Casa de Bombas",
                            "asset_type": AssetType.UNIT,
                            "description": "Estação de bombeamento principal",
                            "children": [
                                {
                                    "name": "Bomba Centrífuga 01",
                                    "asset_type": AssetType.EQUIPMENT,
                                    "template_name": "Bomba Centrífuga",
                                    "equipment_id": "PUMP01",
                                    "description": "Bomba de água de processo",
                                    "process_flow": {"upstream": [], "downstream": []}
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}


async def create_templates(db: AsyncSession) -> dict:
    """Create asset templates and return mapping of name -> template"""
    templates = {}

    for template_def in ASSET_TEMPLATES:
        # Check if template already exists
        result = await db.execute(
            select(AssetTemplate).where(AssetTemplate.name == template_def["name"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  Template '{template_def['name']}' already exists, skipping...")
            templates[template_def["name"]] = existing
            continue

        template = AssetTemplate(
            id=uuid.uuid4(),
            name=template_def["name"],
            description=template_def["description"],
            asset_type=template_def["asset_type"],
            attribute_definitions=template_def["attribute_definitions"],
            is_active=True
        )
        db.add(template)
        templates[template_def["name"]] = template
        print(f"  Created template: {template_def['name']}")

    await db.commit()
    return templates


async def create_asset_hierarchy(
    db: AsyncSession,
    node: dict,
    templates: dict,
    parent_id: uuid.UUID = None
) -> Asset:
    """Recursively create asset hierarchy"""

    # Check if asset already exists
    result = await db.execute(
        select(Asset).where(Asset.name == node["name"])
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"  Asset '{node['name']}' already exists, processing children...")
        asset = existing
    else:
        # Get template if specified
        template = None
        if "template_name" in node:
            template = templates.get(node["template_name"])

        # Create asset metadata
        metadata = {}
        if "equipment_id" in node:
            metadata["equipment_id"] = node["equipment_id"]
        if "process_flow" in node:
            metadata["process_flow"] = node["process_flow"]

        asset = Asset(
            id=uuid.uuid4(),
            name=node["name"],
            description=node.get("description", ""),
            asset_type=node["asset_type"],
            parent_id=parent_id,
            template_id=template.id if template else None,
            is_active=True,
            health_score=100.0,
            status="operational",
            asset_metadata=metadata if metadata else None
        )
        db.add(asset)
        await db.flush()  # Get the ID

        print(f"  Created asset: {node['name']} ({node['asset_type'].value})")

        # Create attributes from template if equipment
        if template and node["asset_type"] == AssetType.EQUIPMENT:
            for attr_def in template.attribute_definitions:
                attr = AssetAttribute(
                    id=uuid.uuid4(),
                    asset_id=asset.id,
                    name=attr_def["name"],
                    description=attr_def.get("description", ""),
                    attribute_type=attr_def["attribute_type"],  # String: 'tag_reference', 'static', 'calculated'
                    static_value=attr_def.get("static_value"),
                    formula=attr_def.get("formula"),
                    unit=attr_def.get("unit", ""),
                    settings=attr_def.get("settings", {})
                )
                db.add(attr)
            print(f"    Added {len(template.attribute_definitions)} attributes from template")

    # Process children
    for child_node in node.get("children", []):
        await create_asset_hierarchy(db, child_node, templates, asset.id)

    return asset


async def main():
    """Main function to seed asset hierarchy"""
    print("\n" + "="*60)
    print("SEEDING ASSET HIERARCHY FOR ML ANOMALY DETECTION")
    print("="*60 + "\n")

    async with AsyncSessionLocal() as db:
        try:
            # Step 1: Create templates
            print("Step 1: Creating Asset Templates...")
            templates = await create_templates(db)
            print(f"  Total templates: {len(templates)}\n")

            # Step 2: Create hierarchy
            print("Step 2: Creating Asset Hierarchy...")
            root_asset = await create_asset_hierarchy(db, ASSET_HIERARCHY, templates)
            await db.commit()

            # Step 3: Summary
            print("\n" + "="*60)
            print("SUMMARY")
            print("="*60)

            # Count assets by type
            for asset_type in AssetType:
                result = await db.execute(
                    select(Asset).where(Asset.asset_type == asset_type)
                )
                count = len(result.scalars().all())
                if count > 0:
                    print(f"  {asset_type.value}: {count}")

            # Count attributes
            result = await db.execute(select(AssetAttribute))
            attr_count = len(result.scalars().all())
            print(f"  Total Attributes: {attr_count}")

            print("\n✅ Asset hierarchy seeded successfully!")
            print("="*60 + "\n")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
