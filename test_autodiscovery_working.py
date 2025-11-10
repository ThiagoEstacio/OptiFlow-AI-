#!/usr/bin/env python3
"""
Teste de Auto-Discovery OPC-UA - Versão Simplificada
Testa descoberta de tags do servidor OPC-UA sem dependências complexas
"""
import asyncio
import sys
from asyncua import Client
import json

async def test_auto_discovery():
    """Testa auto-discovery básico"""
    endpoint = "opc.tcp://localhost:4840/optiflow/terminal"

    print("=" * 70)
    print("🔍 TESTE DE AUTO-DISCOVERY - OPTIFLOW")
    print("=" * 70)
    print(f"Endpoint: {endpoint}")
    print()

    client = Client(url=endpoint, timeout=10)

    try:
        # Conectar
        print("🔌 Conectando ao servidor OPC-UA...")
        await client.connect()
        print("✓ Conectado!")
        print()

        # Namespaces
        print("📋 Namespaces:")
        namespaces = await client.get_namespace_array()
        for idx, ns in enumerate(namespaces):
            print(f"  {idx}: {ns}")
        print()

        # Namespace OptiFlow (índice 2)
        optiflow_ns_idx = 2

        # Browse TEAG node
        print("🏭 Descobrindo estrutura TEAG...")
        objects = client.get_objects_node()

        # Encontrar TEAG
        teag_node = None
        for child in await objects.get_children():
            name = await child.read_browse_name()
            if name.Name == "TEAG":
                teag_node = child
                break

        if not teag_node:
            print("❌ TEAG não encontrado!")
            return

        print("✓ TEAG encontrado!")
        print()

        # Descobrir tags
        print("🔍 Descobrindo tags...")
        discovered_tags = []

        async def browse_recursive(node, prefix="", level=0):
            """Browse recursivo de nodes"""
            if level > 5:  # Limite de profundidade
                return

            try:
                children = await node.get_children()
                for child in children:
                    try:
                        # Nome e tipo
                        browse_name = await child.read_browse_name()
                        node_class = await child.read_node_class()

                        tag_name = f"{prefix}.{browse_name.Name}" if prefix else browse_name.Name

                        # Se for variável, ler valor
                        if node_class.name == "Variable":
                            try:
                                value = await child.read_value()
                                data_type = await child.read_data_type_as_variant_type()

                                tag_info = {
                                    "name": tag_name,
                                    "node_id": str(child.nodeid),
                                    "value": str(value) if value is not None else "N/A",
                                    "data_type": str(data_type)
                                }
                                discovered_tags.append(tag_info)

                            except Exception as e:
                                # Valor não legível, adicionar sem valor
                                tag_info = {
                                    "name": tag_name,
                                    "node_id": str(child.nodeid),
                                    "value": "N/A",
                                    "data_type": "Unknown"
                                }
                                discovered_tags.append(tag_info)

                        # Se for objeto, continuar browse
                        elif node_class.name == "Object":
                            await browse_recursive(child, tag_name, level + 1)

                    except Exception as e:
                        continue

            except Exception as e:
                pass

        # Iniciar descoberta
        await browse_recursive(teag_node, "TEAG")

        print(f"✅ Descobertos {len(discovered_tags)} tags!")
        print()

        # Classificar por prefixo
        prefixes = {}
        for tag in discovered_tags:
            parts = tag['name'].split('.')
            if len(parts) >= 2:
                prefix = parts[1]  # Pega depois de TEAG.
                prefixes[prefix] = prefixes.get(prefix, 0) + 1

        print("📊 Tags por área:")
        for prefix, count in sorted(prefixes.items()):
            print(f"  {prefix}: {count} tags")
        print()

        # Exemplos
        print("📝 Exemplos de tags descobertos:")
        for i, tag in enumerate(discovered_tags[:15]):
            print(f"  {i+1}. {tag['name']}")
            print(f"      Valor: {tag['value']}")
        print()

        # Salvar resultado
        result = {
            "endpoint": endpoint,
            "total_tags": len(discovered_tags),
            "by_area": prefixes,
            "tags": discovered_tags
        }

        with open("autodiscovery_results.json", "w") as f:
            json.dump(result, f, indent=2)

        print("💾 Resultados salvos em: autodiscovery_results.json")
        print()

        # Resumo final
        print("=" * 70)
        print("✅ AUTO-DISCOVERY CONCLUÍDO COM SUCESSO!")
        print("=" * 70)
        print(f"Total de tags: {len(discovered_tags)}")
        print(f"Áreas cobertas: {len(prefixes)}")
        print()

        return True

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await client.disconnect()
        print("🔌 Desconectado")

if __name__ == "__main__":
    try:
        success = asyncio.run(test_auto_discovery())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1)
