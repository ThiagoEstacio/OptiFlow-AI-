#!/usr/bin/env python3
"""
Test OPC-UA Discovery Endpoints
Standalone test of the OPC-UA tag discovery functionality
"""
import asyncio
from asyncua import Client, ua
from typing import Dict, Any, List
import json

class OPCUADiscoveryTest:
    """Test OPC-UA discovery endpoints functionality"""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    async def test_connection(self) -> Dict[str, Any]:
        """Test OPC-UA connection"""
        print(f"\n{'='*70}")
        print("🔍 TEST 1: Connection Test")
        print(f"   Endpoint: {self.endpoint}")
        print('='*70)

        try:
            client = Client(url=self.endpoint, timeout=10)
            await client.connect()

            namespaces = await client.get_namespace_array()
            server_state = await client.get_node("i=2259").read_value()

            await client.disconnect()

            result = {
                "success": True,
                "message": "Connection successful",
                "server_info": {
                    "endpoint": self.endpoint,
                    "namespaces": namespaces,
                    "server_state": str(server_state),
                    "namespace_count": len(namespaces)
                }
            }

            print(f"\n✅ Connection successful!")
            print(f"   Namespaces: {len(namespaces)}")
            for i, ns in enumerate(namespaces):
                print(f"     [{i}] {ns}")
            print(f"   Server state: {server_state}")

            return result

        except Exception as e:
            print(f"\n❌ Connection failed: {e}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "error": str(e)
            }

    async def browse_tags(self, start_node: str = "i=85", max_depth: int = 4) -> Dict[str, Any]:
        """Browse OPC-UA tags"""
        print(f"\n{'='*70}")
        print("🔍 TEST 2: Tag Discovery / Browsing")
        print(f"   Start node: {start_node}")
        print(f"   Max depth: {max_depth}")
        print('='*70)

        try:
            client = Client(url=self.endpoint, timeout=10)
            await client.connect()

            start_node_obj = client.get_node(start_node)
            discovered_tags = []

            async def browse_node(node, current_path="", current_depth=0):
                """Recursively browse node tree"""
                if current_depth > max_depth:
                    return

                try:
                    browse_name = await node.read_browse_name()
                    node_class = await node.read_node_class()
                    node_id = node.nodeid.to_string()

                    node_path = f"{current_path}/{browse_name.Name}" if current_path else browse_name.Name

                    value = None
                    data_type = None

                    if node_class == ua.NodeClass.Variable:
                        try:
                            value_variant = await node.read_value()
                            value = str(value_variant) if value_variant is not None else None

                            data_type_node = await node.read_data_type()
                            data_type = data_type_node.to_string()
                        except:
                            pass

                    tag_info = {
                        "node_id": node_id,
                        "browse_name": browse_name.Name,
                        "display_name": browse_name.Name,
                        "node_class": node_class.name,
                        "path": node_path,
                        "depth": current_depth,
                        "data_type": data_type,
                        "value": value
                    }

                    discovered_tags.append(tag_info)

                    if current_depth < max_depth:
                        try:
                            children = await node.get_children()
                            for child in children:
                                await browse_node(child, node_path, current_depth + 1)
                        except:
                            pass

                except Exception:
                    pass

            await browse_node(start_node_obj)
            await client.disconnect()

            result = {
                "success": True,
                "endpoint": self.endpoint,
                "tags_discovered": len(discovered_tags),
                "tags": discovered_tags
            }

            print(f"\n✅ Tag discovery successful!")
            print(f"   Total tags discovered: {len(discovered_tags)}")

            # Show sample tags
            print(f"\n📋 Sample tags (first 10):")
            for i, tag in enumerate(discovered_tags[:10]):
                value_str = f" = {tag['value']}" if tag['value'] else ""
                print(f"   [{i+1}] {tag['path']}")
                print(f"        NodeID: {tag['node_id']}")
                print(f"        Type: {tag['node_class']}{value_str}")

            # Summary by type
            variables = [t for t in discovered_tags if t['node_class'] == 'Variable']
            objects = [t for t in discovered_tags if t['node_class'] == 'Object']
            print(f"\n📊 Summary:")
            print(f"   Variables: {len(variables)}")
            print(f"   Objects: {len(objects)}")
            print(f"   Other: {len(discovered_tags) - len(variables) - len(objects)}")

            return result

        except Exception as e:
            print(f"\n❌ Tag discovery failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

async def main():
    """Main test function"""
    endpoint = "opc.tcp://127.0.0.1:4840/optiflow/terminal"

    print("="*70)
    print("🧪 OPC-UA Discovery Endpoints - Functionality Test")
    print("="*70)
    print(f"Endpoint: {endpoint}")
    print("="*70)

    tester = OPCUADiscoveryTest(endpoint)

    # Test 1: Connection
    connection_result = await tester.test_connection()

    # Test 2: Tag Discovery
    if connection_result.get("success"):
        browse_result = await tester.browse_tags(max_depth=4)

        # Save results to file
        results = {
            "connection_test": connection_result,
            "browse_test": browse_result
        }

        output_file = "/tmp/opcua_test_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Full results saved to: {output_file}")

    print("\n" + "="*70)
    print("✅ OPC-UA Discovery Tests Complete!")
    print("="*70)

    print("\n📝 Summary:")
    print("   These functions replicate the backend API endpoints:")
    print("   • POST /api/v1/devices/test-opcua-connection")
    print("   • POST /api/v1/devices/browse-opcua-tags")
    print("\n   The SmartPort frontend can use these endpoints to:")
    print("   1. Test connection before adding a device")
    print("   2. Discover all available tags automatically")
    print("   3. Let users select which tags to monitor")

if __name__ == "__main__":
    asyncio.run(main())
