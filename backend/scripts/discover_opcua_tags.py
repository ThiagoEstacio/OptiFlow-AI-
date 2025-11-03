#!/usr/bin/env python3
"""
Discover and import all tags from OPC UA server
"""
import asyncio
import sys
import time
import requests
from asyncua import Client
from typing import List, Dict

# API Configuration
API_URL = "http://localhost:8000/api/v1/tags/"
DEVICE_ID = "9bf20d02-35c0-4dc2-9e65-64ffd36a2e12"

# OPC UA Configuration
OPCUA_ENDPOINT = "opc.tcp://localhost:4840/optiflow/terminal"
NAMESPACE_URI = "http://optiflow.com/terminal"


async def discover_tags(client: Client, namespace_idx: int) -> List[Dict]:
    """Discover all variable nodes in the OPC UA server"""
    tags = []
    
    # Get Objects node (standard root)
    objects = client.get_objects_node()
    
    # Find TEAG node under Objects
    try:
        children = await objects.get_children()
        root = None
        for child in children:
            browse_name = await child.read_browse_name()
            if browse_name.Name == "TEAG":
                root = child
                break
        
        if root is None:
            print("❌ Nó 'TEAG' não encontrado sob Objects")
            return []
            
    except Exception as e:
        print(f"❌ Erro ao buscar nó TEAG: {e}")
        return []
    
    print(f"\n🔍 Descobrindo tags a partir de: {await root.read_browse_name()}")
    
    async def browse_recursive(node, path=""):
        """Recursively browse all nodes"""
        try:
            children = await node.get_children()
            
            for child in children:
                try:
                    # Get node info
                    browse_name = await child.read_browse_name()
                    node_class = await child.read_node_class()
                    
                    # Build full path
                    current_path = f"{path}.{browse_name.Name}" if path else browse_name.Name
                    
                    # If it's a Variable node, add to tags list
                    if node_class.value == 2:  # Variable
                        node_id = child.nodeid.to_string()
                        
                        # Try to get data type
                        try:
                            data_type_node = await child.read_data_type()
                            variant = await child.read_data_value()
                            value = variant.Value.Value
                            
                            # Determine data type
                            if isinstance(value, bool):
                                data_type = "BOOLEAN"
                            elif isinstance(value, int):
                                data_type = "INTEGER"
                            elif isinstance(value, float):
                                data_type = "FLOAT"
                            elif isinstance(value, str):
                                data_type = "STRING"
                            else:
                                data_type = "FLOAT"  # Default
                            
                        except:
                            data_type = "FLOAT"  # Default
                        
                        # Try to get description
                        try:
                            description = await child.read_description()
                            desc_text = description.Text if description else current_path
                        except:
                            desc_text = current_path
                        
                        # Determine unit and category based on tag name
                        unit = None
                        category = "PROCESS"
                        
                        if "POSICAO" in current_path or "POSITION" in current_path:
                            unit = "%"
                        elif "VAZAO" in current_path or "FLOW" in current_path:
                            unit = "t/h"
                        elif "TEMP" in current_path:
                            unit = "°C"
                            category = "ENERGY"
                        elif "ENERGIA" in current_path or "ENERGY" in current_path or "KWH" in current_path:
                            unit = "kWh"
                            category = "ENERGY"
                        elif "MASSA" in current_path or "MASS" in current_path:
                            unit = "t"
                        elif "CUSTO" in current_path or "COST" in current_path:
                            unit = "R$"
                        elif "POTENCIA" in current_path or "POWER" in current_path:
                            unit = "kW"
                            category = "ENERGY"
                        elif "CORRENTE" in current_path or "CURRENT" in current_path:
                            unit = "A"
                            category = "ENERGY"
                        elif "TENSAO" in current_path or "VOLTAGE" in current_path:
                            unit = "V"
                            category = "ENERGY"
                        elif "FATOR_POTENCIA" in current_path or "PF" in current_path:
                            unit = ""
                            category = "ENERGY"
                        elif "VIBRACAO" in current_path or "VIBRATION" in current_path:
                            unit = "mm/s"
                            category = "PROCESS"
                        elif "HEALTH" in current_path or "SAUDE" in current_path:
                            unit = "%"
                            category = "PROCESS"
                        elif "HORIMETRO" in current_path or "HOURS" in current_path:
                            unit = "h"
                            category = "PROCESS"
                        elif "MANUTENCAO" in current_path:
                            category = "PROCESS"
                        elif "INTERLOCKS" in current_path or "INTERLOCK" in current_path:
                            category = "ALARM"
                        elif "ALARMES" in current_path:
                            category = "ALARM"
                        elif ".SP" in current_path:
                            category = "SETPOINT"
                        elif "ALARM" in current_path or ".AL" in current_path:
                            category = "ALARM"
                            data_type = "BOOLEAN"
                        
                        tags.append({
                            "name": current_path.replace(".", "_").upper(),
                            "address": node_id,
                            "data_type": data_type,
                            "unit": unit,
                            "category": category,
                            "description": desc_text,
                            "path": current_path
                        })
                        
                        # Log detalhado para tags importantes
                        if any(x in current_path.upper() for x in ["INTERLOCKS", "ALARMES", "MANUTENCAO", "ENERGIA"]):
                            print(f"  ✓ {current_path} ({data_type}, {unit or 'no unit'}, cat={category})")
                        else:
                            print(f"  ✓ {current_path} ({data_type}, {unit or 'no unit'})")
                    
                    # Continue browsing recursively
                    await browse_recursive(child, current_path)
                    
                except Exception as e:
                    # Skip nodes that can't be accessed
                    pass
                    
        except Exception as e:
            # Skip if can't browse children
            pass
    
    await browse_recursive(root)
    return tags


async def discover_opcua_tags():
    """Connect to OPC UA server and discover all tags"""
    print(f"\n🔌 Conectando ao servidor OPC UA: {OPCUA_ENDPOINT}")
    
    client = Client(url=OPCUA_ENDPOINT)
    
    try:
        await client.connect()
        print("✅ Conectado com sucesso!")
        
        # Get namespace index
        namespaces = await client.get_namespace_array()
        namespace_idx = None
        
        for idx, ns in enumerate(namespaces):
            if ns == NAMESPACE_URI:
                namespace_idx = idx
                break
        
        if namespace_idx is None:
            print(f"❌ Namespace '{NAMESPACE_URI}' não encontrado")
            return []
        
        print(f"📦 Namespace encontrado: index={namespace_idx}")
        
        # Discover all tags
        tags = await discover_tags(client, namespace_idx)
        
        print(f"\n✅ Descobertas {len(tags)} tags!")
        return tags
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return []
    
    finally:
        await client.disconnect()
        print("🔌 Desconectado do servidor OPC UA")


def create_tag_in_db(tag_data: Dict) -> bool:
    """Create a single tag via API"""
    payload = {
        "name": tag_data["name"],
        "address": tag_data["address"],
        "device_id": DEVICE_ID,
        "data_type": tag_data["data_type"],
        "unit": tag_data.get("unit"),
        "category": tag_data.get("category", "PROCESS"),
        "description": tag_data["description"],
        "enabled": True
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=5)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        if "422" in str(e):
            # Tag might already exist
            return False
        if "429" in str(e):
            # Rate limit - wait and retry
            print(f"  ⏳ Rate limit atingido, aguardando 2s...")
            time.sleep(2)
            try:
                response = requests.post(API_URL, json=payload, timeout=5)
                response.raise_for_status()
                return True
            except:
                print(f"  ❌ Erro após retry '{tag_data['name']}': {e}")
                return False
        print(f"  ❌ Erro ao criar '{tag_data['name']}': {e}")
        return False


def import_tags_to_db(tags: List[Dict]):
    """Import discovered tags to database"""
    print(f"\n📥 Importando {len(tags)} tags para o banco de dados...")
    print(f"   Device ID: {DEVICE_ID}\n")
    
    # Get existing tags first
    try:
        response = requests.get(API_URL, timeout=10)
        existing_tags = response.json()
        existing_names = {t['name'] for t in existing_tags}
        print(f"📊 Tags existentes no banco: {len(existing_names)}\n")
    except Exception as e:
        print(f"⚠️  Erro ao buscar tags existentes: {e}")
        existing_names = set()
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    # Separate tags by category for better reporting
    category_counts = {"INTERLOCKS": 0, "ALARMES": 0, "MANUTENCAO": 0, "ENERGIA": 0, "OTHER": 0}
    
    for i, tag in enumerate(tags):
        tag_name = tag['name']
        
        # Skip if already exists
        if tag_name in existing_names:
            skip_count += 1
            continue
        
        # Add delay every 10 requests to avoid rate limiting
        if i > 0 and i % 10 == 0:
            time.sleep(0.5)
            
        if create_tag_in_db(tag):
            success_count += 1
            print(f"  ✅ {tag_name}")
            
            # Count by category
            if "INTERLOCKS" in tag_name:
                category_counts["INTERLOCKS"] += 1
            elif "ALARMES" in tag_name:
                category_counts["ALARMES"] += 1
            elif "MANUTENCAO" in tag_name:
                category_counts["MANUTENCAO"] += 1
            elif "ENERGIA" in tag_name:
                category_counts["ENERGIA"] += 1
            else:
                category_counts["OTHER"] += 1
        else:
            error_count += 1
            print(f"  ❌ {tag_name} (erro)")
    
    print(f"\n" + "="*60)
    print(f"✅ Importação concluída!")
    print(f"   Criadas: {success_count}")
    print(f"   Já existiam: {skip_count}")
    print(f"   Erros: {error_count}")
    print(f"   Total descoberto: {len(tags)}")
    print(f"\n📊 Por categoria:")
    for cat, count in category_counts.items():
        if count > 0:
            print(f"   {cat}: {count} tags")
    print("="*60 + "\n")
    
    # Verify final count
    try:
        response = requests.get(API_URL, timeout=10)
        total = len(response.json())
        unique = len({t['name'] for t in response.json()})
        print(f"📊 Total de tags no banco: {total} ({unique} únicas)\n")
        
        # Count special tags
        all_tags = response.json()
        interlocks = len([t for t in all_tags if "INTERLOCKS" in t['name']])
        alarmes = len([t for t in all_tags if "ALARMES" in t['name']])
        manutencao = len([t for t in all_tags if "MANUTENCAO" in t['name']])
        energia = len([t for t in all_tags if "ENERGIA" in t['name']])
        
        print(f"📋 Tags dos sistemas avançados no banco:")
        print(f"   Interlocks: {interlocks}")
        print(f"   Alarmes: {alarmes}")
        print(f"   Manutenção: {manutencao}")
        print(f"   Energia: {energia}")
        print(f"   Total sistemas avançados: {interlocks + alarmes + manutencao + energia}\n")
    except:
        pass


async def main():
    """Main function"""
    print("\n" + "="*60)
    print("  🔍 Descoberta Automática de Tags OPC UA")
    print("="*60)
    
    # Step 1: Discover tags from OPC UA server
    tags = await discover_opcua_tags()
    
    if not tags:
        print("\n❌ Nenhuma tag foi descoberta. Verifique se o servidor OPC UA está rodando.")
        sys.exit(1)
    
    # Step 2: Import tags to database
    import_tags_to_db(tags)
    
    print("✅ Processo concluído com sucesso!\n")


if __name__ == "__main__":
    asyncio.run(main())
