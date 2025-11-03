#!/usr/bin/env python3
"""
Browse OPC-UA Server Tree
Navigate and display the complete tag tree structure
"""

import asyncio
from asyncua import Client


async def browse_node(node, level=0, max_level=5):
    """Recursively browse OPC-UA node tree"""
    try:
        indent = "  " * level
        browse_name = await node.read_browse_name()
        node_id = node.nodeid.to_string()
        node_class = await node.read_node_class()

        # Try to read value if it's a variable
        value_str = ""
        if node_class.name == "Variable":
            try:
                value = await node.read_value()
                value_str = f" = {value}"
            except:
                value_str = " = [cannot read]"

        print(f"{indent}[{node_class.name}] {browse_name.Name} ({node_id}){value_str}")

        # Recursively browse children
        if level < max_level:
            try:
                children = await node.get_children()
                for child in children:
                    await browse_node(child, level + 1, max_level)
            except:
                pass

    except Exception as e:
        print(f"{indent}Error browsing node: {str(e)}")


async def main():
    """Main entry point"""
    endpoint = "opc.tcp://localhost:4840/optiflow/terminal"

    print("\n" + "="*80)
    print("🔍 NAVEGANDO ÁRVORE OPC-UA - TERMINAL DE GRÃOS")
    print("="*80)
    print(f"\nConectando a: {endpoint}\n")

    try:
        # Connect
        client = Client(url=endpoint, timeout=10)
        await client.connect()
        print("✅ Conectado!\n")

        # Get Objects node
        objects = client.get_objects_node()

        # Browse from TEAG node (our namespace)
        print("📂 ESTRUTURA DE TAGS:\n")
        print("="*80)

        children = await objects.get_children()
        for child in children:
            browse_name = await child.read_browse_name()
            if browse_name.Name == "TEAG":
                print("🏭 TERMINAL EXPORTADOR DE GRÃOS (TEAG):\n")
                await browse_node(child, level=0, max_level=4)

        # Disconnect
        await client.disconnect()
        print("\n" + "="*80)
        print("✅ Navegação concluída")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ Erro: {str(e)}\n")


if __name__ == "__main__":
    asyncio.run(main())
