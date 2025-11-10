#!/usr/bin/env python3
"""
Teste de Auto-Discovery OPC-UA
================================

Script para testar a descoberta automática de tags OPC-UA.

Uso:
    python test_opcua_discovery.py [ENDPOINT]

Exemplo:
    python test_opcua_discovery.py opc.tcp://localhost:4840
"""
import asyncio
import sys
import json
from pathlib import Path

# Adicionar path do gateway
sys.path.insert(0, str(Path(__file__).parent / 'app'))

from app.services.tag_auto_discovery import TagAutoDiscovery


async def test_discovery(endpoint: str):
    """
    Testa descoberta de tags

    Args:
        endpoint: URL do servidor OPC-UA
    """
    print("=" * 70)
    print("🔍 OPC-UA Auto-Discovery Test")
    print("=" * 70)
    print(f"Endpoint: {endpoint}")
    print()

    # Criar serviço de discovery
    discovery = TagAutoDiscovery(opcua_endpoint=endpoint, timeout=15)

    # Executar discovery
    print("🚀 Starting discovery...")
    print()

    discovered_tags = await discovery.discover_all()

    # Resultados
    print()
    print("=" * 70)
    print("✅ DISCOVERY COMPLETE")
    print("=" * 70)
    print()

    if not discovered_tags:
        print("❌ No tags discovered!")
        return

    # Resumo
    print(f"📊 Total discovered: {len(discovered_tags)}")
    print()

    # Agrupamento por tipo de equipamento
    by_equipment = {}
    by_route = {}
    unclassified = []

    for tag in discovered_tags:
        if tag.equipment_type:
            by_equipment.setdefault(tag.equipment_type, []).append(tag)
        else:
            unclassified.append(tag)

        if tag.route:
            by_route.setdefault(tag.route, []).append(tag)

    # Exibir por tipo
    print("📋 Tags by Equipment Type:")
    print("-" * 70)
    for eq_type, tags in sorted(by_equipment.items()):
        print(f"\n{eq_type}: {len(tags)} tags")

        # Agrupar por equipment_id
        by_id = {}
        for tag in tags:
            by_id.setdefault(tag.equipment_id, []).append(tag)

        for eq_id, eq_tags in sorted(by_id.items()):
            print(f"  {eq_id} ({len(eq_tags)} tags):")
            for tag in sorted(eq_tags, key=lambda t: t.tag_name)[:5]:  # Primeiros 5
                value_str = str(tag.current_value) if tag.current_value is not None else 'N/A'
                unit_str = f" {tag.unit}" if tag.unit else ""
                print(f"    - {tag.tag_name}: {value_str}{unit_str} [{tag.category or 'N/A'}]")
            if len(eq_tags) > 5:
                print(f"    ... and {len(eq_tags) - 5} more tags")

    # Exibir por rota
    if by_route:
        print()
        print("🛤️  Tags by Route:")
        print("-" * 70)
        for route, tags in sorted(by_route.items()):
            print(f"{route}: {len(tags)} tags")

    # Tags não classificados
    if unclassified:
        print()
        print(f"⚠️  Unclassified tags: {len(unclassified)}")
        print("-" * 70)
        for tag in unclassified[:10]:  # Primeiros 10
            print(f"  - {tag.tag_name}")
        if len(unclassified) > 10:
            print(f"  ... and {len(unclassified) - 10} more")

    # Salvar resultados em JSON
    output_file = Path(__file__).parent / "discovery_results.json"

    results = {
        'endpoint': endpoint,
        'total_tags': len(discovered_tags),
        'timestamp': discovery.stats.get('timestamp', 'N/A'),
        'statistics': {
            'total_discovered': len(discovered_tags),
            'classified': len(discovered_tags) - len(unclassified),
            'unclassified': len(unclassified),
            'by_type': {k: len(v) for k, v in by_equipment.items()},
            'by_route': {k: len(v) for k, v in by_route.items()},
        },
        'tags': [tag.to_dict() for tag in discovered_tags]
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print()
    print(f"💾 Results saved to: {output_file}")
    print()

    # Exemplo de tags para copy-paste
    print("=" * 70)
    print("📝 SAMPLE TAGS (for testing)")
    print("=" * 70)

    # Pegar alguns tags exemplo de cada tipo
    samples = {}
    for eq_type, tags in by_equipment.items():
        if tags:
            samples[eq_type] = tags[0]  # Primeiro de cada tipo

    for eq_type, tag in samples.items():
        print(f"\n{eq_type}: {tag.tag_name}")
        print(f"  Address: {tag.address}")
        print(f"  Type: {tag.data_type}")
        print(f"  Value: {tag.current_value}")
        print(f"  Category: {tag.category}")
        print(f"  Route: {tag.route}")

    print()
    print("=" * 70)


def main():
    """Entry point"""
    # Endpoint padrão ou via argumento
    default_endpoint = "opc.tcp://localhost:4840"
    endpoint = sys.argv[1] if len(sys.argv) > 1 else default_endpoint

    # Executar teste
    try:
        asyncio.run(test_discovery(endpoint))
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
