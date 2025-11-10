#!/usr/bin/env python3
"""
Teste Mínimo de Conexão OPC-UA
Usa apenas asyncua, sem dependências do gateway
"""
import asyncio
from asyncua import Client

async def main():
    endpoint = "opc.tcp://localhost:4840/optiflow/terminal"

    print(f"🔌 Conectando a {endpoint}...")

    client = Client(url=endpoint, timeout=10)

    try:
        await client.connect()
        print("✅ Conectado com sucesso!")

        # Listar namespaces
        namespaces = await client.get_namespace_array()
        print(f"\n📋 Namespaces ({len(namespaces)}):")
        for i, ns in enumerate(namespaces):
            print(f"  {i}: {ns}")

        # Browse Objects folder
        print("\n🔍 Browsing Objects folder...")
        objects = client.get_objects_node()
        children = await objects.get_children()

        print(f"✓ Found {len(children)} objects:")
        for child in children[:10]:  # Primeiros 10
            browse_name = await child.read_browse_name()
            print(f"  - {browse_name.Name}")

        # Tentar navegar até TEAG
        print("\n🏭 Looking for TEAG node...")
        try:
            teag = await objects.get_child(["2:TEAG"])
            print("✅ Found TEAG!")

            teag_children = await teag.get_children()
            print(f"\nTEAG has {len(teag_children)} children:")
            for child in teag_children:
                name = await child.read_browse_name()
                print(f"  - {name.Name}")

        except Exception as e:
            print(f"⚠️  Could not find TEAG: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.disconnect()
        print("\n🔌 Disconnected")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
