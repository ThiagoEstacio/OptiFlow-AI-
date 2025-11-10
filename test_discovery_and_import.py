#!/usr/bin/env python3
"""
Script to discover OPC-UA tags and add them to an existing gateway configuration
"""
import asyncio
import httpx
import json
from typing import List, Dict, Any


async def discover_tags() -> List[Dict[str, Any]]:
    """Discover tags from OPC-UA server via gateway browse API"""
    gateway_url = "http://localhost:8080/api/browse"  # Note: goes through Docker network from backend

    request_data = {
        "endpoint": "opc.tcp://opcua-server:4840/optiflow/terminal",
        "namespace_index": 2,
        "tag_filter": "CORR"
    }

    print(f"Discovering tags from OPC-UA server...")
    print(f"Request: {json.dumps(request_data, indent=2)}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Call from the backend container's perspective
            response = await client.post(
                "http://gateway:8080/api/browse",
                json=request_data
            )

            print(f"Response status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"✓ Discovery successful!")
                print(f"  Found {result['tag_count']} tags")
                print(f"  Namespaces: {len(result['namespaces'])}")
                return result['tags']
            else:
                print(f"✗ Discovery failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return []

        except Exception as e:
            print(f"✗ Error during discovery: {str(e)}")
            return []


async def add_tags_to_gateway(gateway_id: int, tags: List[Dict[str, Any]]):
    """Add discovered tags to an existing gateway configuration"""
    backend_url = "http://localhost:8000"

    print(f"\nAdding {len(tags)} tags to gateway {gateway_id}...")

    async with httpx.AsyncClient(timeout=60.0) as client:
        added = 0
        failed = 0

        for i, tag in enumerate(tags, 1):
            try:
                # Convert discovered tag to GatewayTagCreate format
                tag_data = {
                    "tag_name": tag["tag_name"],
                    "enabled": True,
                    "address_config": {"node_id": tag["address"]},
                    "data_type": tag.get("data_type", "float"),
                    "scale_factor": 1.0,
                    "offset": 0.0,
                    "unit": None,
                    "description": tag.get("description", tag.get("display_name", ""))
                }

                response = await client.post(
                    f"{backend_url}/api/v1/gateway-config/{gateway_id}/tags",
                    json=tag_data
                )

                if response.status_code == 201:
                    added += 1
                    if i % 50 == 0:
                        print(f"  Progress: {i}/{len(tags)} tags processed...")
                else:
                    failed += 1
                    print(f"  ✗ Failed to add tag {tag['tag_name']}: {response.status_code}")

            except Exception as e:
                failed += 1
                print(f"  ✗ Error adding tag {tag['tag_name']}: {str(e)}")

        print(f"\n✓ Tag import complete:")
        print(f"  Added: {added}")
        print(f"  Failed: {failed}")
        print(f"  Total: {len(tags)}")


async def main():
    """Main function"""
    print("=" * 60)
    print("OPC-UA Tag Discovery and Import")
    print("=" * 60)

    # Step 1: Discover tags
    tags = await discover_tags()

    if not tags:
        print("\n✗ No tags discovered. Exiting.")
        return

    print(f"\nSample discovered tags (first 3):")
    for tag in tags[:3]:
        print(f"  - {tag['tag_name']} ({tag['address']})")

    # Step 2: Add tags to Gateway ID 1 (Terminal OPC-UA Gateway)
    gateway_id = 1
    await add_tags_to_gateway(gateway_id, tags)

    print("\n" + "=" * 60)
    print("Import complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
