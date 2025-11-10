"""
Add all discovered OPC-UA tags to Terminal Gateway using raw SQL
This avoids ORM circular dependency issues
"""
import asyncio
import asyncpg
import sys


async def add_terminal_tags():
    """Add all terminal tags using raw SQL"""

    # Database connection details (from docker-compose.yml)
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='optiflow',
        password='optiflow_password',
        database='optiflow'
    )

    try:
        # Check if gateway exists
        gateway = await conn.fetchrow(
            'SELECT id, name FROM gateway_configs WHERE id = $1',
            1
        )

        if not gateway:
            print("✗ Gateway 1 not found")
            return

        print(f"✓ Found gateway: {gateway['name']}")

        # Get existing tags
        existing_tags = await conn.fetch(
            'SELECT tag_name FROM gateway_tags WHERE gateway_id = $1',
            1
        )
        existing_tag_names = {tag['tag_name'] for tag in existing_tags}

        print(f"  Existing tags: {len(existing_tag_names)}")

        # Generate all 217 CORR tags
        namespace = 2
        tags_to_add = []

        for i in range(1, 218):  # 1 to 217
            tag_name = f"TERM_CORR_{i:02d}"

            if tag_name in existing_tag_names:
                continue

            node_id = f"ns={namespace};s=Terminal.{tag_name}"

            tags_to_add.append((
                1,  # gateway_id
                tag_name,
                True,  # enabled
                f'{{"node_id": "{node_id}"}}',  # address_config as JSON string
                'float',  # data_type
                1.0,  # scale_factor
                0.0,  # offset
                '',  # unit
                f'Terminal conveyor tag {i}'  # description
            ))

        if not tags_to_add:
            print("✓ All tags already exist!")
            return

        print(f"  Adding {len(tags_to_add)} new tags...")

        # Insert tags in batches
        batch_size = 50
        added = 0

        for i in range(0, len(tags_to_add), batch_size):
            batch = tags_to_add[i:i+batch_size]

            await conn.executemany('''
                INSERT INTO gateway_tags
                (gateway_id, tag_name, enabled, address_config, data_type, scale_factor, "offset", unit, description)
                VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7, $8, $9)
            ''', batch)

            added += len(batch)
            print(f"    Progress: {added}/{len(tags_to_add)}")

        print(f"\n✓ Successfully added {len(tags_to_add)} tags!")
        print(f"  Total tags in gateway: {len(existing_tag_names) + len(tags_to_add)}")

    finally:
        await conn.close()


async def main():
    """Main function"""
    print("=" * 60)
    print("Adding Terminal OPC-UA Tags (Raw SQL)")
    print("=" * 60)
    print()

    try:
        await add_terminal_tags()
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    print()
    print("=" * 60)
    print("Complete!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
