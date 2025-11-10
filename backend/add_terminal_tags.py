"""
Add all discovered OPC-UA tags to Terminal Gateway
This script connects directly to the database to add tags
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.gateway_config import GatewayConfig, GatewayTag

# Import all models to ensure relationships are properly initialized
from app.models import organization, user, device, tag, alarm, ml_model, chat


async def add_terminal_tags():
    """Add all terminal tags based on discovery pattern"""

    # Tag patterns discovered from Terminal (CORR filter gave 217 tags)
    # Tags follow pattern: TERM_CORR_01, TERM_CORR_02, etc. up to TERM_CORR_217

    gateway_id = 1  # Terminal OPC-UA Gateway

    async with AsyncSessionLocal() as db:
        # Verify gateway exists
        result = await db.execute(
            select(GatewayConfig).where(GatewayConfig.id == gateway_id)
        )
        gateway = result.scalar_one_or_none()

        if not gateway:
            print(f"✗ Gateway {gateway_id} not found")
            return

        print(f"✓ Found gateway: {gateway.name}")

        # Get existing tags to avoid duplicates
        result = await db.execute(
            select(GatewayTag).where(GatewayTag.gateway_id == gateway_id)
        )
        existing_tags = result.scalars().all()
        existing_tag_names = {tag.tag_name for tag in existing_tags}

        print(f"  Existing tags: {len(existing_tag_names)}")

        # Generate all 217 CORR tags
        tags_to_add = []
        namespace = 2  # Based on previous discovery

        for i in range(1, 218):  # 1 to 217
            tag_name = f"TERM_CORR_{i:02d}"

            # Skip if already exists
            if tag_name in existing_tag_names:
                continue

            # OPC-UA node ID pattern: ns=2;s=Terminal.TERM_CORR_01
            node_id = f"ns={namespace};s=Terminal.{tag_name}"

            tag = GatewayTag(
                gateway_id=gateway_id,
                tag_name=tag_name,
                enabled=True,
                address_config={"node_id": node_id},
                data_type="float",
                scale_factor=1.0,
                offset=0.0,
                unit="",
                description=f"Terminal conveyor tag {i}"
            )

            tags_to_add.append(tag)

        if not tags_to_add:
            print("✓ All tags already exist!")
            return

        print(f"  Adding {len(tags_to_add)} new tags...")

        # Add tags in batches
        batch_size = 50
        for i in range(0, len(tags_to_add), batch_size):
            batch = tags_to_add[i:i+batch_size]
            db.add_all(batch)
            await db.flush()
            print(f"    Progress: {min(i+batch_size, len(tags_to_add))}/{len(tags_to_add)}")

        await db.commit()

        print(f"\n✓ Successfully added {len(tags_to_add)} tags!")
        print(f"  Total tags in gateway: {len(existing_tag_names) + len(tags_to_add)}")


async def main():
    """Main function"""
    print("=" * 60)
    print("Adding Terminal OPC-UA Tags")
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
