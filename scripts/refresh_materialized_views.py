#!/usr/bin/env python3
"""
Auto-Refresh Materialized Views - Background Service
OptiFlow AI - Alternative to pg_cron

Runs as a background service refreshing materialized views on schedule.
"""

import asyncio
import asyncpg
import logging
from datetime import datetime
from typing import Optional
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://optiflow:optiflow@postgres:5432/optiflow'
)

# Refresh schedules (in seconds)
SCHEDULES = {
    'mv_alarm_statistics': 3600,              # 1 hour
    'mv_tag_performance': 120,                # 2 minutes
    'mv_asset_health_overview': 300,          # 5 minutes
    'mv_daily_operations_summary': 3600,      # 1 hour
}

class MaterializedViewRefresher:
    """Background service to refresh materialized views"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.tasks = []
        self.running = False
        
    async def connect(self):
        """Connect to database"""
        try:
            self.pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=1,
                max_size=3,
                command_timeout=60
            )
            logger.info("✅ Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from database"""
        if self.pool:
            await self.pool.close()
            logger.info("👋 Disconnected from PostgreSQL")
    
    async def refresh_view(self, view_name: str):
        """Refresh a single materialized view"""
        try:
            start_time = datetime.now()
            
            async with self.pool.acquire() as conn:
                # Use CONCURRENTLY to avoid locking
                await conn.execute(
                    f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}"
                )
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Refreshed {view_name} in {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Failed to refresh {view_name}: {e}")
    
    async def refresh_loop(self, view_name: str, interval: int):
        """Continuous refresh loop for a view"""
        logger.info(f"🔄 Starting refresh loop for {view_name} (every {interval}s)")
        
        while self.running:
            try:
                await self.refresh_view(view_name)
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger.info(f"⏹️  Stopping refresh loop for {view_name}")
                break
            except Exception as e:
                logger.error(f"❌ Error in refresh loop for {view_name}: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def start(self):
        """Start all refresh loops"""
        await self.connect()
        
        self.running = True
        
        # Create a task for each view
        for view_name, interval in SCHEDULES.items():
            task = asyncio.create_task(
                self.refresh_loop(view_name, interval)
            )
            self.tasks.append(task)
        
        logger.info(f"🚀 Started {len(self.tasks)} refresh loops")
        
        # Initial refresh of all views
        logger.info("🔄 Performing initial refresh of all views...")
        for view_name in SCHEDULES.keys():
            await self.refresh_view(view_name)
        
        logger.info("✅ All views refreshed. Running scheduled refreshes...")
    
    async def stop(self):
        """Stop all refresh loops"""
        logger.info("⏹️  Stopping materialized view refresher...")
        
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for all tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        await self.disconnect()
        
        logger.info("✅ Materialized view refresher stopped")


async def main():
    """Main entry point"""
    refresher = MaterializedViewRefresher()
    
    try:
        await refresher.start()
        
        # Run forever
        while True:
            await asyncio.sleep(3600)
            
    except KeyboardInterrupt:
        logger.info("⌨️  Keyboard interrupt received")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        await refresher.stop()


if __name__ == "__main__":
    asyncio.run(main())
