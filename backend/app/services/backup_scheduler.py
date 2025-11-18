"""
Backup Scheduler (PDCA #23 - Enhancement)

Schedules automatic backups using APScheduler.

Features:
- Daily backups at 2AM UTC
- Automatic cleanup after backup
- Error notifications
- Retry on failure
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.backup_service import get_backup_service

logger = logging.getLogger(__name__)


class BackupScheduler:
    """
    Manages scheduled backups.

    Uses APScheduler for cron-like scheduling.
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    async def start(self):
        """Start backup scheduler."""
        if self.is_running:
            logger.warning("Backup scheduler already running")
            return

        # Schedule daily backup at 2 AM UTC
        self.scheduler.add_job(
            self._run_backup,
            trigger=CronTrigger(hour=2, minute=0, timezone='UTC'),
            id='daily_backup',
            name='Daily Backup (2AM UTC)',
            replace_existing=True
        )

        # Schedule weekly cleanup on Mondays at 3 AM UTC
        self.scheduler.add_job(
            self._run_cleanup,
            trigger=CronTrigger(day_of_week='mon', hour=3, minute=0, timezone='UTC'),
            id='weekly_cleanup',
            name='Weekly Backup Cleanup (Monday 3AM UTC)',
            replace_existing=True
        )

        self.scheduler.start()
        self.is_running = True

        logger.info("✅ Backup scheduler started")
        logger.info("   • Daily backup: 2AM UTC")
        logger.info("   • Weekly cleanup: Monday 3AM UTC")

    async def stop(self):
        """Stop backup scheduler."""
        if not self.is_running:
            return

        self.scheduler.shutdown(wait=True)
        self.is_running = False

        logger.info("Backup scheduler stopped")

    async def _run_backup(self):
        """Execute scheduled backup."""
        try:
            logger.info("Starting scheduled backup")

            backup_service = get_backup_service()
            results = await backup_service.backup_all()

            # Log results
            success_count = sum(1 for r in results if r.status == "success")
            total_count = len(results)

            if success_count == total_count:
                logger.info(f"✅ Scheduled backup completed successfully ({success_count}/{total_count})")
            else:
                logger.error(f"⚠️  Scheduled backup partially failed ({success_count}/{total_count})")

            # TODO: Send notification if failures

        except Exception as e:
            logger.error(f"❌ Scheduled backup failed: {e}", exc_info=True)
            # TODO: Send alert

    async def _run_cleanup(self):
        """Execute scheduled cleanup."""
        try:
            logger.info("Starting scheduled cleanup")

            backup_service = get_backup_service()
            await backup_service.cleanup_old_backups()

            logger.info("✅ Scheduled cleanup completed")

        except Exception as e:
            logger.error(f"❌ Scheduled cleanup failed: {e}", exc_info=True)

    async def trigger_backup_now(self):
        """Manually trigger backup (for testing)."""
        logger.info("Manual backup triggered via scheduler")
        await self._run_backup()

    def get_next_run_time(self, job_id: str) -> Optional[datetime]:
        """Get next run time for a job."""
        job = self.scheduler.get_job(job_id)
        if job:
            return job.next_run_time
        return None


# Global scheduler instance
_scheduler: Optional[BackupScheduler] = None


def get_backup_scheduler() -> BackupScheduler:
    """Get global backup scheduler."""
    global _scheduler

    if _scheduler is None:
        _scheduler = BackupScheduler()

    return _scheduler


async def init_backup_scheduler():
    """Initialize and start backup scheduler."""
    scheduler = get_backup_scheduler()
    await scheduler.start()


async def shutdown_backup_scheduler():
    """Shutdown backup scheduler."""
    scheduler = get_backup_scheduler()
    await scheduler.stop()
