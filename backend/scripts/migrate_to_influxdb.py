"""
Data Migration Script: PostgreSQL → InfluxDB

Migrates existing GBM Logistics data from PostgreSQL to InfluxDB
for improved time-series performance.

Usage:
    python -m scripts.migrate_to_influxdb [--site-id SITE_ID] [--batch-size BATCH_SIZE]
"""

import asyncio
import argparse
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models.external_data import GBMLogisticsData
from app.services.influxdb_service import influxdb_service
from app.core.logging import get_logger

logger = get_logger(__name__)


async def migrate_site_data(
    site_id: int,
    batch_size: int = 1000,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Migrate GBM data for a specific site from PostgreSQL to InfluxDB.

    Args:
        site_id: Site ID to migrate
        batch_size: Number of records per batch
        dry_run: If True, only count records without writing

    Returns:
        Migration statistics
    """
    async with async_session_maker() as db:
        # Count total records
        count_result = await db.execute(
            select(GBMLogisticsData).where(GBMLogisticsData.site_id == site_id)
        )
        all_records = count_result.scalars().all()
        total_records = len(all_records)

        logger.info(f"Found {total_records} records for site {site_id}")

        if dry_run:
            return {
                "site_id": site_id,
                "total_records": total_records,
                "migrated": 0,
                "failed": 0,
                "dry_run": True
            }

        if total_records == 0:
            logger.warning(f"No records found for site {site_id}")
            return {
                "site_id": site_id,
                "total_records": 0,
                "migrated": 0,
                "failed": 0
            }

        # Migrate in batches
        migrated = 0
        failed = 0

        for i in range(0, total_records, batch_size):
            batch = all_records[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(total_records + batch_size - 1)//batch_size} ({len(batch)} records)")

            # Convert to InfluxDB format
            influx_operations = []
            for record in batch:
                try:
                    influx_operations.append({
                        "operation_date": record.operation_date,
                        "operation_type": record.operation_type or "unknown",
                        "product_type": record.product_type or "unknown",
                        "vehicle_type": record.vehicle_type or "unknown",
                        "status": record.status or "completed",
                        "net_weight_kg": float(record.net_weight_kg) if record.net_weight_kg else None,
                        "gross_weight_kg": float(record.gross_weight_kg) if record.gross_weight_kg else None,
                        "tare_weight_kg": float(record.tare_weight_kg) if record.tare_weight_kg else None,
                        "loading_time_minutes": float(record.loading_time_minutes) if record.loading_time_minutes else None,
                        "waiting_time_minutes": float(record.waiting_time_minutes) if record.waiting_time_minutes else None,
                        "total_time_minutes": float(record.total_time_minutes) if record.total_time_minutes else None,
                        "moisture_percent": float(record.moisture_percent) if record.moisture_percent else None,
                        "impurity_percent": float(record.impurity_percent) if record.impurity_percent else None,
                        "total_value": float(record.total_value) if record.total_value else None,
                        "freight_value": float(record.freight_value) if record.freight_value else None
                    })
                except Exception as e:
                    logger.error(f"Error converting record {record.id}: {str(e)}")
                    failed += 1

            # Write batch to InfluxDB
            if influx_operations:
                try:
                    result = influxdb_service.write_gbm_operations_batch(
                        site_id=site_id,
                        operations=influx_operations
                    )
                    migrated += result["success"]
                    failed += result["failed"]
                    logger.info(f"Batch result: {result['success']} success, {result['failed']} failed")
                except Exception as e:
                    logger.error(f"Error writing batch to InfluxDB: {str(e)}")
                    failed += len(influx_operations)

        logger.info(f"Migration complete for site {site_id}: {migrated} migrated, {failed} failed")

        return {
            "site_id": site_id,
            "total_records": total_records,
            "migrated": migrated,
            "failed": failed
        }


async def migrate_all_sites(
    batch_size: int = 1000,
    dry_run: bool = False
) -> List[Dict[str, Any]]:
    """
    Migrate data for all sites.

    Args:
        batch_size: Number of records per batch
        dry_run: If True, only count records without writing

    Returns:
        List of migration statistics per site
    """
    async with async_session_maker() as db:
        # Get all unique site IDs
        result = await db.execute(
            select(GBMLogisticsData.site_id).distinct()
        )
        site_ids = [row[0] for row in result.all()]

        logger.info(f"Found {len(site_ids)} sites to migrate")

        results = []
        for site_id in site_ids:
            logger.info(f"\n{'='*60}")
            logger.info(f"Migrating site {site_id}")
            logger.info(f"{'='*60}")

            result = await migrate_site_data(
                site_id=site_id,
                batch_size=batch_size,
                dry_run=dry_run
            )
            results.append(result)

        return results


def print_summary(results: List[Dict[str, Any]]):
    """Print migration summary."""
    print("\n" + "="*60)
    print("MIGRATION SUMMARY")
    print("="*60)

    total_records = sum(r["total_records"] for r in results)
    total_migrated = sum(r["migrated"] for r in results)
    total_failed = sum(r["failed"] for r in results)

    print(f"\nSites processed: {len(results)}")
    print(f"Total records:   {total_records:,}")
    print(f"Migrated:        {total_migrated:,}")
    print(f"Failed:          {total_failed:,}")
    print(f"Success rate:    {(total_migrated/total_records*100):.2f}%" if total_records > 0 else "N/A")

    print("\nPer-site results:")
    print(f"{'Site ID':<10} {'Total':<10} {'Migrated':<10} {'Failed':<10} {'Rate':<10}")
    print("-"*60)

    for r in results:
        rate = f"{(r['migrated']/r['total_records']*100):.1f}%" if r['total_records'] > 0 else "N/A"
        print(f"{r['site_id']:<10} {r['total_records']:<10} {r['migrated']:<10} {r['failed']:<10} {rate:<10}")

    print("="*60 + "\n")


async def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description="Migrate GBM data from PostgreSQL to InfluxDB")
    parser.add_argument("--site-id", type=int, help="Migrate specific site only")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size (default 1000)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (count only, don't write)")

    args = parser.parse_args()

    start_time = datetime.now()
    logger.info(f"Starting migration at {start_time}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Dry run: {args.dry_run}")

    if args.site_id:
        logger.info(f"Migrating single site: {args.site_id}")
        result = await migrate_site_data(
            site_id=args.site_id,
            batch_size=args.batch_size,
            dry_run=args.dry_run
        )
        results = [result]
    else:
        logger.info("Migrating all sites")
        results = await migrate_all_sites(
            batch_size=args.batch_size,
            dry_run=args.dry_run
        )

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print_summary(results)

    logger.info(f"Migration completed in {duration:.2f} seconds")

    if args.dry_run:
        logger.info("DRY RUN - No data was written to InfluxDB")


if __name__ == "__main__":
    asyncio.run(main())
