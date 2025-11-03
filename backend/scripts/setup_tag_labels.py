#!/usr/bin/env python3
"""
Setup Tag Labels System

Creates the tag_labels table and populates with initial examples
Converts technical tag names into user-friendly labels organized by area and equipment
"""
import asyncio
import sys
import logging
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, "/app")

from app.db.session import get_db
from app.models.tag_label import TagLabel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_table():
    """Create tag_labels table"""
    logger.info("Creating tag_labels table...")
    
    create_sql = """
    CREATE TABLE IF NOT EXISTS tag_labels (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tag_id UUID NOT NULL UNIQUE REFERENCES tags(id) ON DELETE CASCADE,
        
        -- User-friendly identifiers
        display_name VARCHAR(255) NOT NULL,
        short_name VARCHAR(100),
        
        -- Organization
        equipment_name VARCHAR(255),
        area_name VARCHAR(255),
        system_name VARCHAR(255),
        
        -- Custom description
        custom_description TEXT,
        notes TEXT,
        
        -- Visibility
        is_visible BOOLEAN NOT NULL DEFAULT true,
        is_favorite BOOLEAN NOT NULL DEFAULT false,
        
        -- Audit
        created_by VARCHAR(255),
        updated_by VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );
    
    -- Create indexes
    CREATE INDEX IF NOT EXISTS ix_tag_labels_tag_id ON tag_labels(tag_id);
    CREATE INDEX IF NOT EXISTS ix_tag_labels_display_name ON tag_labels(display_name);
    CREATE INDEX IF NOT EXISTS ix_tag_labels_equipment_name ON tag_labels(equipment_name);
    CREATE INDEX IF NOT EXISTS ix_tag_labels_area_name ON tag_labels(area_name);
    CREATE INDEX IF NOT EXISTS ix_tag_labels_system_name ON tag_labels(system_name);
    """
    
    async for db in get_db():
        try:
            await db.execute(text(create_sql))
            await db.commit()
            logger.info("✅ Table created successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating table: {e}")
            await db.rollback()
            return False


async def populate_labels():
    """Populate with initial label examples"""
    logger.info("Populating tag labels...")
    
    # Read SQL file
    with open("/app/scripts/populate_tag_labels.sql", "r") as f:
        populate_sql = f.read()
    
    async for db in get_db():
        try:
            # Execute population script
            await db.execute(text(populate_sql))
            await db.commit()
            
            # Get statistics
            result = await db.execute(text("""
                SELECT 
                    COUNT(*) as total_labels,
                    COUNT(DISTINCT area_name) as total_areas,
                    COUNT(DISTINCT equipment_name) as total_equipments,
                    COUNT(DISTINCT system_name) as total_systems,
                    SUM(CASE WHEN is_favorite THEN 1 ELSE 0 END) as favorites
                FROM tag_labels
            """))
            
            stats = result.fetchone()
            
            logger.info("✅ Labels populated successfully!")
            logger.info(f"   Total Labels: {stats[0]}")
            logger.info(f"   Areas: {stats[1]}")
            logger.info(f"   Equipments: {stats[2]}")
            logger.info(f"   Systems: {stats[3]}")
            logger.info(f"   Favorites: {stats[4]}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error populating labels: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await db.rollback()
            return False


async def main():
    """Main setup function"""
    logger.info("="*80)
    logger.info("🏷️  Tag Labels System Setup")
    logger.info("="*80)
    
    # Step 1: Create table
    if not await create_table():
        logger.error("Failed to create table. Exiting.")
        return 1
    
    # Step 2: Populate with examples
    if not await populate_labels():
        logger.error("Failed to populate labels. Table created but empty.")
        return 1
    
    logger.info("\n" + "="*80)
    logger.info("✅ Setup completed successfully!")
    logger.info("="*80)
    logger.info("\nYou can now:")
    logger.info("1. Access labels via API: GET /api/v1/tag-labels/")
    logger.info("2. Search by area: GET /api/v1/tag-labels/?area_name=Armazém 01")
    logger.info("3. View favorites: GET /api/v1/tag-labels/?is_favorite=true")
    logger.info("4. Get tag with label: GET /api/v1/tag-labels/tags/with-labels")
    logger.info("5. View stats: GET /api/v1/tag-labels/stats/overview")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
