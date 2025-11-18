"""
Automated Restore Testing (PDCA #23 - Enhancement)

Tests backup integrity by performing automated restores.

Features:
- Weekly restore tests
- Test database restoration
- Validation of backup integrity
- SHA-256 checksum verification
- Test results tracking
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RestoreTestStatus(str, Enum):
    """Restore test status."""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    SKIPPED = "skipped"


@dataclass
class RestoreTestResult:
    """Result of a restore test."""
    service: str
    status: RestoreTestStatus
    started_at: datetime
    completed_at: Optional[datetime]
    backup_file: str
    test_db_name: Optional[str]
    checksum_valid: bool
    restore_successful: bool
    error: Optional[str] = None


class RestoreTester:
    """
    Automated restore testing service.

    Periodically tests backup restoration to ensure backups are valid.
    """

    def __init__(self, backup_dir: str = "/var/backups/optiflow"):
        self.backup_dir = Path(backup_dir)
        self.test_results: List[RestoreTestResult] = []

    async def test_all_restores(self) -> List[RestoreTestResult]:
        """
        Test restoration of all latest backups.

        Returns:
            List of test results
        """
        logger.info("Starting automated restore tests")

        results = await asyncio.gather(
            self.test_postgresql_restore(),
            self.test_redis_restore(),
            # InfluxDB and Vault tests can be added here
            return_exceptions=True
        )

        # Process results
        test_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Restore test failed with exception: {result}")
            else:
                test_results.append(result)
                self.test_results.append(result)

        # Log summary
        success_count = sum(1 for r in test_results if r.status == RestoreTestStatus.SUCCESS)
        logger.info(f"Restore tests completed: {success_count}/{len(test_results)} successful")

        return test_results

    async def test_postgresql_restore(self) -> RestoreTestResult:
        """
        Test PostgreSQL backup restoration.

        Creates a test database and restores latest backup.
        """
        service = "postgresql"
        started_at = datetime.utcnow()

        try:
            logger.info(f"Testing {service} restore")

            # Find latest PostgreSQL backup
            backup_files = sorted(
                self.backup_dir.glob("postgresql_*.sql.gz"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            if not backup_files:
                logger.warning("No PostgreSQL backups found for testing")
                return RestoreTestResult(
                    service=service,
                    status=RestoreTestStatus.SKIPPED,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                    backup_file="",
                    test_db_name=None,
                    checksum_valid=False,
                    restore_successful=False,
                    error="No backups found"
                )

            latest_backup = backup_files[0]
            logger.info(f"Testing restore of: {latest_backup.name}")

            # Verify checksum (if checksum file exists)
            checksum_valid = await self._verify_checksum(latest_backup)

            # Create test database
            test_db_name = f"optiflow_test_restore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            create_db_cmd = [
                "psql",
                "-h", "postgres",
                "-U", "optiflow_user",
                "-d", "postgres",
                "-c", f"CREATE DATABASE {test_db_name};"
            ]

            process = await asyncio.create_subprocess_exec(
                *create_db_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={"PGPASSWORD": "optiflow_password"}
            )

            await process.communicate()

            if process.returncode != 0:
                return RestoreTestResult(
                    service=service,
                    status=RestoreTestStatus.FAILED,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                    backup_file=str(latest_backup),
                    test_db_name=test_db_name,
                    checksum_valid=checksum_valid,
                    restore_successful=False,
                    error="Failed to create test database"
                )

            # Restore backup to test database
            restore_cmd = [
                "pg_restore",
                "-h", "postgres",
                "-U", "optiflow_user",
                "-d", test_db_name,
                str(latest_backup)
            ]

            process = await asyncio.create_subprocess_exec(
                *restore_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={"PGPASSWORD": "optiflow_password"}
            )

            stdout, stderr = await process.communicate()

            restore_successful = process.returncode == 0

            # Cleanup test database
            drop_db_cmd = [
                "psql",
                "-h", "postgres",
                "-U", "optiflow_user",
                "-d", "postgres",
                "-c", f"DROP DATABASE IF EXISTS {test_db_name};"
            ]

            cleanup_process = await asyncio.create_subprocess_exec(
                *drop_db_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={"PGPASSWORD": "optiflow_password"}
            )

            await cleanup_process.communicate()

            completed_at = datetime.utcnow()
            duration = (completed_at - started_at).total_seconds()

            if restore_successful:
                logger.info(f"PostgreSQL restore test successful ({duration:.1f}s)")
                status = RestoreTestStatus.SUCCESS
                error = None
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"PostgreSQL restore test failed: {error_msg}")
                status = RestoreTestStatus.FAILED
                error = error_msg

            return RestoreTestResult(
                service=service,
                status=status,
                started_at=started_at,
                completed_at=completed_at,
                backup_file=str(latest_backup),
                test_db_name=test_db_name,
                checksum_valid=checksum_valid,
                restore_successful=restore_successful,
                error=error
            )

        except Exception as e:
            logger.error(f"PostgreSQL restore test exception: {e}", exc_info=True)
            return RestoreTestResult(
                service=service,
                status=RestoreTestStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                backup_file="",
                test_db_name=None,
                checksum_valid=False,
                restore_successful=False,
                error=str(e)
            )

    async def test_redis_restore(self) -> RestoreTestResult:
        """
        Test Redis backup restoration.

        Validates RDB file integrity.
        """
        service = "redis"
        started_at = datetime.utcnow()

        try:
            logger.info(f"Testing {service} restore")

            # Find latest Redis backup
            backup_files = sorted(
                self.backup_dir.glob("redis_*.rdb"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            if not backup_files:
                logger.warning("No Redis backups found for testing")
                return RestoreTestResult(
                    service=service,
                    status=RestoreTestStatus.SKIPPED,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                    backup_file="",
                    test_db_name=None,
                    checksum_valid=False,
                    restore_successful=False,
                    error="No backups found"
                )

            latest_backup = backup_files[0]
            logger.info(f"Testing restore of: {latest_backup.name}")

            # Verify checksum
            checksum_valid = await self._verify_checksum(latest_backup)

            # Validate RDB file using redis-check-rdb
            validate_cmd = [
                "redis-check-rdb",
                str(latest_backup)
            ]

            process = await asyncio.create_subprocess_exec(
                *validate_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            restore_successful = process.returncode == 0

            completed_at = datetime.utcnow()
            duration = (completed_at - started_at).total_seconds()

            if restore_successful:
                logger.info(f"Redis restore test successful ({duration:.1f}s)")
                status = RestoreTestStatus.SUCCESS
                error = None
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Redis restore test failed: {error_msg}")
                status = RestoreTestStatus.FAILED
                error = error_msg

            return RestoreTestResult(
                service=service,
                status=status,
                started_at=started_at,
                completed_at=completed_at,
                backup_file=str(latest_backup),
                test_db_name=None,
                checksum_valid=checksum_valid,
                restore_successful=restore_successful,
                error=error
            )

        except Exception as e:
            logger.error(f"Redis restore test exception: {e}", exc_info=True)
            return RestoreTestResult(
                service=service,
                status=RestoreTestStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                backup_file="",
                test_db_name=None,
                checksum_valid=False,
                restore_successful=False,
                error=str(e)
            )

    async def _verify_checksum(self, backup_file: Path) -> bool:
        """
        Verify backup file checksum.

        Looks for .sha256 file alongside backup.
        """
        checksum_file = backup_file.with_suffix(backup_file.suffix + '.sha256')

        if not checksum_file.exists():
            logger.warning(f"No checksum file found for {backup_file.name}")
            return False

        try:
            # Read expected checksum
            with open(checksum_file, 'r') as f:
                expected_checksum = f.read().strip()

            # Calculate actual checksum
            import hashlib
            sha256 = hashlib.sha256()

            with open(backup_file, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)

            actual_checksum = sha256.hexdigest()

            if expected_checksum == actual_checksum:
                logger.info(f"Checksum valid for {backup_file.name}")
                return True
            else:
                logger.error(f"Checksum mismatch for {backup_file.name}")
                return False

        except Exception as e:
            logger.error(f"Error verifying checksum: {e}")
            return False

    def get_latest_test_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest restore test results."""
        return [
            {
                "service": r.service,
                "status": r.status.value,
                "started_at": r.started_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "backup_file": r.backup_file,
                "checksum_valid": r.checksum_valid,
                "restore_successful": r.restore_successful,
                "error": r.error
            }
            for r in self.test_results[-limit:]
        ]


# Global instance
_restore_tester: Optional[RestoreTester] = None


def get_restore_tester() -> RestoreTester:
    """Get global restore tester instance."""
    global _restore_tester

    if _restore_tester is None:
        _restore_tester = RestoreTester()

    return _restore_tester
