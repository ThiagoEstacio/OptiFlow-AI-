"""
Fix tag addresses - Map string identifiers to correct numeric identifiers
"""
import asyncio
import requests
from asyncua import Client, ua

OPCUA_ENDPOINT = "opc.tcp://localhost:4840/optiflow/terminal"
API_URL = "http://localhost:8000/api/v1/tags"


async def discover_all_nodes():
    """Discover all nodes from OPC UA server with their numeric IDs"""
    client = Client(url=OPCUA_ENDPOINT)
    
    nodes_map = {}
    
    try:
        await client.connect()
        print(f"✅ Conectado ao OPC UA: {OPCUA_ENDPOINT}\n")
        
        # Start from TEAG root
        root = client.get_node('ns=2;i=1')  # TEAG
        
        async def browse_recursive(node, path='TEAG'):
            try:
                children = await node.get_children()
                for child in children:
                    try:
                        browse_name = await child.read_browse_name()
                        node_id = child.nodeid.to_string()
                        node_class = await child.read_node_class()
                        
                        current_path = f"{path}.{browse_name.Name}"
                        
                        # Store mapping
                        nodes_map[current_path] = node_id
                        
                        # If it's not a variable, browse recursively
                        if node_class != ua.NodeClass.Variable:
                            await browse_recursive(child, current_path)
                            
                    except Exception as e:
                        pass
            except Exception as e:
                pass
        
        await browse_recursive(root)
        await client.disconnect()
        
        print(f"📦 Descobertos {len(nodes_map)} nodes")
        return nodes_map
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return {}


def get_all_tags():
    """Get all tags from database"""
    try:
        response = requests.get(f"{API_URL}?limit=500")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Erro ao buscar tags: {e}")
        return []


def update_tag_address(tag_id: str, new_address: str, tag_data: dict):
    """Update tag address in database"""
    try:
        # Use PUT with all required fields
        payload = {
            "name": tag_data['name'],
            "address": new_address,  # New address
            "device_id": tag_data['device_id'],
            "data_type": tag_data['data_type'],
            "unit": tag_data.get('unit'),
            "category": tag_data.get('category'),
            "description": tag_data.get('description'),
            "enabled": tag_data.get('enabled', True),
            "log_enabled": tag_data.get('log_enabled', True)
        }
        
        response = requests.put(
            f"{API_URL}/{tag_id}",
            json=payload
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


async def main():
    print("\n" + "="*70)
    print("🔧 Corrigindo Endereços das Tags")
    print("="*70 + "\n")
    
    # Step 1: Discover all nodes
    print("📡 Passo 1: Descobrindo nodes do servidor OPC UA...")
    nodes_map = await discover_all_nodes()
    
    if not nodes_map:
        print("❌ Nenhum node descoberto. Verifique a conexão com o servidor OPC UA.")
        return
    
    # Print some examples
    print("\n📋 Exemplos de mapeamento:")
    for path, node_id in list(nodes_map.items())[:10]:
        print(f"  {path:<60} -> {node_id}")
    
    # Step 2: Get all tags from database
    print("\n\n📥 Passo 2: Buscando tags do banco de dados...")
    tags = get_all_tags()
    print(f"   Encontradas {len(tags)} tags\n")
    
    # Step 3: Fix addresses
    print("🔧 Passo 3: Corrigindo endereços...\n")
    
    updated = 0
    already_correct = 0
    not_found = 0
    
    for tag in tags:
        tag_name = tag['name']
        current_address = tag.get('address', '')
        
        # Skip if already has numeric identifier
        if current_address.startswith('ns=2;i='):
            already_correct += 1
            continue
        
        # Try to find correct address
        # Current address might be like: ns=2;s=TEAG.ARZ.GATES.GATE01.POSICAO.PV
        # Extract the path part
        if 'ns=2;s=' in current_address:
            path = current_address.replace('ns=2;s=', '')
            
            if path in nodes_map:
                new_address = nodes_map[path]
                print(f"  🔄 {tag_name}")
                print(f"     OLD: {current_address}")
                print(f"     NEW: {new_address}")
                
                if update_tag_address(tag['id'], new_address, tag):
                    updated += 1
                    print(f"     ✅ Atualizado!\n")
                else:
                    print(f"     ❌ Falhou\n")
            else:
                print(f"  ⚠️  {tag_name}: Path '{path}' não encontrado no servidor OPC UA")
                not_found += 1
    
    # Summary
    print("\n" + "="*70)
    print("📊 Resumo:")
    print(f"   ✅ Atualizados: {updated}")
    print(f"   ✔️  Já corretos: {already_correct}")
    print(f"   ⚠️  Não encontrados: {not_found}")
    print(f"   📦 Total: {len(tags)}")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
