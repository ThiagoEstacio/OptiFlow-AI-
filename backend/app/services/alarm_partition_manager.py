"""
Alarm Event Partition Manager (PDCA #17)

Manages monthly partitions for alarm_events table.

Features:
- Automatic partition creation
- Partition maintenance (cleanup old partitions)
- Partition statistics and monitoring
- Archive old partitions
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


class AlarmPartitionManager:
    """
    Manages partitions for alarm_events table.

    Responsibilities:
    - Create future partitions proactively
    - Monitor partition sizes
    - Archive/drop old partitions
    - Provide partition statistics
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_partition(self, year: int, month: int) -> bool:
        """
        Create a single partition for given year/month.

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)

        Returns:
            True if partition was created, False if already exists
        """
        partition_date = datetime(year, month, 1)
        partition_name = f"alarm_events_{year}_{month:02d}"

        start_date = partition_date
        end_date = partition_date.replace(day=28) + timedelta(days=4)
        end_date = end_date.replace(day=1)

        try:
            # Check if partition exists
            check_query = text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_class WHERE relname = :partition_name
                )
            """)

            result = await self.db.execute(check_query, {"partition_name": partition_name})
            exists = result.scalar()

            if exists:
                logger.info(f"Partition {partition_name} already exists")
                return False

            # Create partition
            create_query = text(f"""
                CREATE TABLE {partition_name} PARTITION OF alarm_events
                FOR VALUES FROM ('{start_date}') TO ('{end_date}')
            """)

            await self.db.execute(create_query)

            # Create indexes
            idx_def_ts = text(f"""
                CREATE INDEX {partition_name}_def_ts_idx
                ON {partition_name} (definition_id, timestamp DESC)
            """)

            idx_state_ts = text(f"""
                CREATE INDEX {partition_name}_state_ts_idx
                ON {partition_name} (state, timestamp DESC)
            """)

            await self.db.execute(idx_def_ts)
            await self.db.execute(idx_state_ts)
            await self.db.commit()

            logger.info(f"✅ Created partition {partition_name} with indexes")
            return True

        except Exception as e:
            logger.error(f"Error creating partition {partition_name}: {e}")
            await self.db.rollback()
            return False

    async def create_future_partitions(self, months_ahead: int = 3) -> int:
        """
        Create partitions for next N months.

        Args:
            months_ahead: Number of months to create partitions for

        Returns:
            Number of partitions created
        """
        created_count = 0
        current_date = datetime.utcnow()

        for i in range(1, months_ahead + 1):
            future_date = current_date + timedelta(days=30 * i)
            created = await self.create_partition(future_date.year, future_date.month)
            if created:
                created_count += 1

        logger.info(f"Created {created_count} future partition(s)")
        return created_count

    async def get_partition_stats(self) -> List[Dict[str, Any]]:
        """
        Get statistics for all alarm_events partitions.

        Returns:
            List of partition stats with size, row count, etc.
        """
        query = text("""
            SELECT
                c.relname AS partition_name,
                pg_size_pretty(pg_total_relation_size(c.oid)) AS size,
                pg_total_relation_size(c.oid) AS size_bytes,
                n_tup_ins AS rows_inserted,
                n_tup_upd AS rows_updated,
                n_tup_del AS rows_deleted,
                n_live_tup AS live_rows,
                n_dead_tup AS dead_rows,
                last_vacuum,
                last_autovacuum
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_stat_user_tables s ON s.relid = c.oid
            WHERE c.relname LIKE 'alarm_events_%'
                AND c.relkind = 'r'
                AND n.nspname = 'public'
            ORDER BY c.relname DESC
        """)

        result = await self.db.execute(query)
        rows = result.fetchall()

        partitions = []
        for row in rows:
            partitions.append({
                "partition_name": row.partition_name,
                "size": row.size,
                "size_bytes": row.size_bytes,
                "live_rows": row.live_rows,
                "dead_rows": row.dead_rows,
                "rows_inserted": row.rows_inserted,
                "rows_updated": row.rows_updated,
                "rows_deleted": row.rows_deleted,
                "last_vacuum": row.last_vacuum,
                "last_autovacuum": row.last_autovacuum
            })

        return partitions

    async def drop_old_partition(self, year: int, month: int) -> bool:
        """
        Drop partition for given year/month.

        WARNING: This permanently deletes data!

        Args:
            year: Year
            month: Month (1-12)

        Returns:
            True if dropped successfully
        """
        partition_name = f"alarm_events_{year}_{month:02d}"

        try:
            # Confirm partition exists
            check_query = text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_class WHERE relname = :partition_name
                )
            """)

            result = await self.db.execute(check_query, {"partition_name": partition_name})
            exists = result.scalar()

            if not exists:
                logger.warning(f"Partition {partition_name} does not exist")
                return False

            # Drop partition
            drop_query = text(f"DROP TABLE {partition_name}")
            await self.db.execute(drop_query)
            await self.db.commit()

            logger.info(f"✅ Dropped partition {partition_name}")
            return True

        except Exception as e:
            logger.error(f"Error dropping partition {partition_name}: {e}")
            await self.db.rollback()
            return False

    async def cleanup_old_partitions(self, retention_months: int = 12) -> int:
        """
        Drop partitions older than retention period.

        Args:
            retention_months: Keep data for this many months

        Returns:
            Number of partitions dropped
        """
        cutoff_date = datetime.utcnow() - timedelta(days=30 * retention_months)
        dropped_count = 0

        # Get all partitions
        query = text("""
            SELECT relname
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname LIKE 'alarm_events_%'
                AND c.relkind = 'r'
                AND n.nspname = 'public'
            ORDER BY c.relname
        """)

        result = await self.db.execute(query)
        partitions = result.fetchall()

        for partition_row in partitions:
            partition_name = partition_row.relname

            # Extract year/month from name (alarm_events_YYYY_MM)
            try:
                parts = partition_name.split('_')
                year = int(parts[2])
                month = int(parts[3])

                partition_date = datetime(year, month, 1)

                if partition_date < cutoff_date:
                    dropped = await self.drop_old_partition(year, month)
                    if dropped:
                        dropped_count += 1

            except (IndexError, ValueError) as e:
                logger.warning(f"Could not parse partition name {partition_name}: {e}")
                continue

        logger.info(f"Cleaned up {dropped_count} old partition(s)")
        return dropped_count

    async def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of partition status.

        Returns:
            {
                "total_partitions": 15,
                "total_size": "2.5 GB",
                "total_rows": 1234567,
                "oldest_partition": "alarm_events_2024_01",
                "newest_partition": "alarm_events_2025_03",
                "partitions": [...]
            }
        """
        partitions = await self.get_partition_stats()

        if not partitions:
            return {
                "total_partitions": 0,
                "total_size": "0 bytes",
                "total_rows": 0,
                "oldest_partition": None,
                "newest_partition": None,
                "partitions": []
            }

        total_size_bytes = sum(p["size_bytes"] for p in partitions)
        total_rows = sum(p["live_rows"] for p in partitions)

        # Convert bytes to human readable
        if total_size_bytes < 1024:
            size_str = f"{total_size_bytes} bytes"
        elif total_size_bytes < 1024**2:
            size_str = f"{total_size_bytes / 1024:.2f} KB"
        elif total_size_bytes < 1024**3:
            size_str = f"{total_size_bytes / 1024**2:.2f} MB"
        else:
            size_str = f"{total_size_bytes / 1024**3:.2f} GB"

        return {
            "total_partitions": len(partitions),
            "total_size": size_str,
            "total_size_bytes": total_size_bytes,
            "total_rows": total_rows,
            "oldest_partition": partitions[-1]["partition_name"] if partitions else None,
            "newest_partition": partitions[0]["partition_name"] if partitions else None,
            "partitions": partitions
        }


# Singleton instance
_partition_manager: AlarmPartitionManager = None


async def get_partition_manager(db: AsyncSession) -> AlarmPartitionManager:
    """Get partition manager instance."""
    return AlarmPartitionManager(db)
