"""
Materialized View Auto-Refresh Service
OptiFlow AI - Background task to keep mat views fresh
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy import text
from prometheus_client import Gauge, Counter, Histogram, REGISTRY
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Prometheus Metrics (using default REGISTRY)
mat_view_last_refresh = Gauge(
    'optiflow_mat_view_last_refresh_timestamp',
    'Last successful refresh timestamp',
    ['view_name'],
    registry=REGISTRY
)

mat_view_refresh_duration = Histogram(
    'optiflow_mat_view_refresh_duration_seconds',
    'Time taken to refresh materialized view',
    ['view_name'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
    registry=REGISTRY
)

mat_view_refresh_errors = Counter(
    'optiflow_mat_view_refresh_errors_total',
    'Total number of failed refreshes',
    ['view_name'],
    registry=REGISTRY
)

mat_view_refresh_success = Counter(
    'optiflow_mat_view_refresh_success_total',
    'Total number of successful refreshes',
    ['view_name'],
    registry=REGISTRY
)

# Refresh schedules (in seconds)
REFRESH_SCHEDULES = {
    'mv_alarm_statistics': 3600,              # 1 hour
    'mv_tag_performance': 120,                # 2 minutes  
    'mv_asset_health_overview': 300,          # 5 minutes
    'mv_daily_operations_summary': 3600,      # 1 hour
}

class MatViewRefresher:
    """Auto-refresh materialized views in background"""
    
    def __init__(self):
        self.running = False
        self.tasks = []
    
    async def refresh_view(self, view_name: str):
        """Refresh a single materialized view"""
        start_time = datetime.now()
        
        try:
            async with AsyncSessionLocal() as session:
                # Use CONCURRENTLY to avoid locking (requires unique index)
                await session.execute(
                    text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}")
                )
                await session.commit()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Update Prometheus metrics
            mat_view_refresh_duration.labels(view_name=view_name).observe(duration)
            mat_view_last_refresh.labels(view_name=view_name).set(datetime.now().timestamp())
            mat_view_refresh_success.labels(view_name=view_name).inc()
            
            logger.info(f"✅ Refreshed {view_name} in {duration:.2f}s")
            
        except Exception as e:
            # Update error metrics
            mat_view_refresh_errors.labels(view_name=view_name).inc()
            
            # Non-critical - log but don't crash
            logger.warning(f"⚠️  Failed to refresh {view_name}: {e}")
    
    async def refresh_loop(self, view_name: str, interval: int):
        """Continuous refresh loop"""
        logger.info(f"🔄 Mat view refresh loop: {view_name} (every {interval}s)")
        
        while self.running:
            try:
                await self.refresh_view(view_name)
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger.info(f"⏹️  Stopped refresh loop: {view_name}")
                break
            except Exception as e:
                logger.error(f"❌ Error in refresh loop {view_name}: {e}")
                await asyncio.sleep(60)  # Wait 1 min on error
    
    async def start(self):
        """Start all refresh loops"""
        self.running = True
        
        # Initial refresh
        logger.info("🔄 Initial refresh of all materialized views...")
        for view_name in REFRESH_SCHEDULES.keys():
            await self.refresh_view(view_name)
        
        # Start background tasks
        for view_name, interval in REFRESH_SCHEDULES.items():
            task = asyncio.create_task(
                self.refresh_loop(view_name, interval)
            )
            self.tasks.append(task)
        
        logger.info(f"✅ Started {len(self.tasks)} mat view refresh loops")
    
    async def stop(self):
        """Stop all refresh loops"""
        logger.info("⏹️  Stopping mat view refresher...")
        self.running = False
        
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("✅ Mat view refresher stopped")


# Global instance
mat_view_refresher = MatViewRefresher()


async def start_mat_view_refresher():
    """Start the refresher (called from main.py)"""
    await mat_view_refresher.start()


async def stop_mat_view_refresher():
    """Stop the refresher (called from main.py shutdown)"""
    await mat_view_refresher.stop()
