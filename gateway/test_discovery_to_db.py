#!/usr/bin/env python3
"""
Teste End-to-End: Discovery → PostgreSQL
==========================================

Script completo que:
1. Descobre tags via OPC-UA
2. Classifica automaticamente
3. Salva no PostgreSQL
4. Mostra estatísticas

Uso:
    python test_discovery_to_db.py [OPCUA_ENDPOINT]

Exemplo:
    python test_discovery_to_db.py opc.tcp://localhost:4840
"""
import asyncio
import sys
import os
from pathlib import Path

# Adicionar path do gateway
sys.path.insert(0, str(Path(__file__).parent / 'app'))

from app.services.tag_auto_discovery import TagAutoDiscovery
from app.services.tag_persistence import TagPersistence


# Configuração do PostgreSQL
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'database': os.getenv('POSTGRES_DB', 'optiflow'),
    'user': os.getenv('POSTGRES_USER', 'optiflow'),
    'password': os.getenv('POSTGRES_PASSWORD', 'optiflow_password'),
}


async def test_discovery_to_db(opcua_endpoint: str, device_name: str):
    """
    Teste completo de discovery → database

    Args:
        opcua_endpoint: URL do servidor OPC-UA
        device_name: Nome do device a criar/atualizar
    """
    print("=" * 70)
    print("🔄 END-TO-END TEST: OPC-UA Discovery → PostgreSQL")
    print("=" * 70)
    print(f"OPC-UA Endpoint: {opcua_endpoint}")
    print(f"Device Name: {device_name}")
    print(f"Database: {DB_CONFIG['database']}@{DB_CONFIG['host']}")
    print()

    # ======================================
    # FASE 1: Auto-Discovery
    # ======================================
    print("📡 PHASE 1: Auto-Discovery")
    print("-" * 70)

    discovery = TagAutoDiscovery(opcua_endpoint=opcua_endpoint, timeout=15)

    print("🔍 Discovering tags...")
    tags = await discovery.discover_all()

    if not tags:
        print("❌ No tags discovered! Check if OPC-UA server is running.")
        return

    print(f"✓ Discovered {len(tags)} tags")

    # Resumo
    classified = sum(1 for t in tags if t.equipment_type)
    unclassified = len(tags) - classified

    print(f"  - Classified: {classified}")
    print(f"  - Unclassified: {unclassified}")

    # Por tipo
    by_type = {}
    for tag in tags:
        if tag.equipment_type:
            by_type[tag.equipment_type] = by_type.get(tag.equipment_type, 0) + 1

    if by_type:
        print("\n  Equipment types found:")
        for eq_type, count in sorted(by_type.items()):
            print(f"    - {eq_type}: {count}")

    print()

    # ======================================
    # FASE 2: Persistence
    # ======================================
    print("💾 PHASE 2: Save to PostgreSQL")
    print("-" * 70)

    persistence = TagPersistence(db_config=DB_CONFIG)

    try:
        # Garantir que device existe
        print(f"🔧 Ensuring device '{device_name}' exists...")
        device_id = await persistence.ensure_device(
            device_name=device_name,
            protocol='OPC_UA',
            connection_config={'endpoint': opcua_endpoint}
        )
        print(f"✓ Device ID: {device_id}")

        # Salvar tags em batch
        print(f"\n💾 Saving {len(tags)} tags in batch...")
        save_stats = await persistence.save_tags_batch(
            tags=tags,
            device_id=device_id,
            scan_rate_ms=1000
        )

        print(f"✓ Save completed:")
        print(f"  - Total: {save_stats['total']}")
        print(f"  - Inserted/Updated: {save_stats['inserted']}")
        print(f"  - Errors: {save_stats['errors']}")

        # ======================================
        # FASE 3: Verification
        # ======================================
        print()
        print("✅ PHASE 3: Verification")
        print("-" * 70)

        # Estatísticas do banco
        db_stats = await persistence.get_statistics()

        print(f"📊 Database Statistics:")
        print(f"  - Total Devices: {db_stats['total_devices']}")
        print(f"  - Total Tags: {db_stats['total_tags']}")

        if db_stats['by_equipment_type']:
            print(f"\n  Tags by Equipment Type:")
            for eq_type, count in db_stats['by_equipment_type'].items():
                print(f"    - {eq_type}: {count}")

        if db_stats['by_route']:
            print(f"\n  Tags by Route:")
            for route, count in db_stats['by_route'].items():
                print(f"    - {route}: {count}")

        # Verificar alguns tags específicos
        print()
        print("🔍 Sample Tags (from database):")
        print("-" * 70)

        # Buscar tags de um equipamento específico
        if tags:
            first_tag = next((t for t in tags if t.equipment_type), None)

            if first_tag and first_tag.equipment_type:
                sample_tags = await persistence.get_tags_by_equipment(
                    equipment_type=first_tag.equipment_type,
                    equipment_id=first_tag.equipment_id
                )

                if sample_tags:
                    print(f"\nTags for {first_tag.equipment_id} ({first_tag.equipment_type}):")
                    for tag in sample_tags[:5]:  # Primeiros 5
                        unit_str = f" [{tag['unit']}]" if tag.get('unit') else ""
                        print(f"  - {tag['name']}: {tag['data_type']}{unit_str}")
                        print(f"    Address: {tag['address']}")
                        print(f"    Category: {tag.get('category', 'N/A')}")

        print()
        print("=" * 70)
        print("✅ TEST COMPLETE!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Check database: SELECT * FROM devices;")
        print("  2. Check tags: SELECT name, category, unit FROM tags LIMIT 10;")
        print("  3. Use these tags in your API endpoints")
        print()

    finally:
        await persistence.disconnect()


def main():
    """Entry point"""
    # Configuração
    default_endpoint = "opc.tcp://localhost:4840"
    default_device = "PLC Terminal TEAG"

    opcua_endpoint = sys.argv[1] if len(sys.argv) > 1 else default_endpoint
    device_name = sys.argv[2] if len(sys.argv) > 2 else default_device

    # Executar teste
    try:
        asyncio.run(test_discovery_to_db(opcua_endpoint, device_name))
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
