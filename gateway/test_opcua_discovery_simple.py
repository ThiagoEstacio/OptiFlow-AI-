#!/usr/bin/env python3
"""
Teste Simples de Auto-Discovery OPC-UA
Evita imports complexos que requerem dependências extras
"""
import asyncio
import sys
from pathlib import Path

# Adicionar path do gateway
sys.path.insert(0, str(Path(__file__).parent / 'app'))

# Import direto do que precisamos
from services.opcua_browser import OPCUABrowser


async def simple_discovery(endpoint: str):
    """Teste simples de discovery"""
    print("=" * 70)
    print("🔍 OPC-UA Simple Discovery Test")
    print("=" * 70)
    print(f"Endpoint: {endpoint}")
    print()

    browser = OPCUABrowser(endpoint, timeout=15)

    try:
        # Conectar
        print("🔌 Connecting to OPC-UA server...")
        connected = await browser.connect()

        if not connected:
            print("❌ Failed to connect!")
            return

        print("✓ Connected successfully!")
        print()

        # Listar namespaces
        print("📋 Namespaces:")
        namespaces = await browser.get_namespaces()
        for ns in namespaces:
            print(f"  {ns['index']}: {ns['uri']}")
        print()

        # Descobrir tags
        print("🔍 Discovering tags...")
        tags = await browser.discover_all_tags(namespace_filter=[2])  # Namespace OptiFlow

        print(f"\n✅ Found {len(tags)} tags!")
        print()

        # Agrupar por prefixo
        prefixes = {}
        for tag in tags:
            # Pegar prefixo (primeira parte antes do .)
            parts = tag['tag_name'].split('.')
            if len(parts) > 0:
                prefix = parts[0]
                prefixes[prefix] = prefixes.get(prefix, 0) + 1

        print("📊 Tags by prefix:")
        for prefix, count in sorted(prefixes.items()):
            print(f"  {prefix}: {count} tags")

        print()
        print("📝 Sample tags (first 20):")
        for i, tag in enumerate(tags[:20]):
            value_str = tag.get('current_value', 'N/A')
            print(f"  {i+1}. {tag['tag_name']}: {value_str}")

        print()
        print(f"✅ Discovery complete! Found {len(tags)} total tags")

        return tags

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await browser.disconnect()


if __name__ == '__main__':
    endpoint = sys.argv[1] if len(sys.argv) > 1 else "opc.tcp://localhost:4840/optiflow/terminal"

    try:
        asyncio.run(simple_discovery(endpoint))
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
