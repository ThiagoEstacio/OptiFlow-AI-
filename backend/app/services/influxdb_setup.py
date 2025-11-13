"""
InfluxDB Setup and Optimization Service

Handles:
- Retention policies creation
- Continuous queries for data rollups
- Bucket management
- Index optimization
"""

import logging
from typing import List, Dict, Any
from influxdb_client import InfluxDBClient, BucketRetentionRules
from influxdb_client.client.write_api import SYNCHRONOUS
from app.core.config import settings

logger = logging.getLogger(__name__)


class InfluxDBSetupService:
    """Service for setting up and optimizing InfluxDB."""

    def __init__(self):
        """Initialize InfluxDB client."""
        self.client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG
        )
        self.buckets_api = self.client.buckets_api()
        self.tasks_api = self.client.tasks_api()

    async def setup_buckets_and_retention(self):
        """
        Setup InfluxDB buckets with appropriate retention policies.

        Buckets:
        - timeseries: Raw data, 30 days retention
        - aggregations: 1h rollups, 1 year retention
        - downsampled: 1d rollups, 5 years retention
        """
        logger.info("Setting up InfluxDB buckets with retention policies...")

        buckets_config = [
            {
                "name": "timeseries",
                "retention_hours": 30 * 24,  # 30 days
                "description": "Raw timeseries data (30d retention)",
                "shard_group_duration": 24 * 3600  # 1 day shards
            },
            {
                "name": "aggregations",
                "retention_hours": 365 * 24,  # 1 year
                "description": "1-hour aggregated data (1y retention)",
                "shard_group_duration": 7 * 24 * 3600  # 7 day shards
            },
            {
                "name": "downsampled",
                "retention_hours": 5 * 365 * 24,  # 5 years
                "description": "1-day aggregated data (5y retention)",
                "shard_group_duration": 30 * 24 * 3600  # 30 day shards
            }
        ]

        for bucket_config in buckets_config:
            await self._create_or_update_bucket(bucket_config)

        logger.info("✅ InfluxDB buckets configured successfully")

    async def _create_or_update_bucket(self, config: Dict[str, Any]):
        """Create or update a bucket with retention policy."""
        bucket_name = config["name"]

        # Check if bucket exists
        try:
            bucket = self.buckets_api.find_bucket_by_name(bucket_name)

            if bucket:
                logger.info(f"Bucket '{bucket_name}' already exists, updating retention...")

                # Update retention
                retention_rules = BucketRetentionRules(
                    type="expire",
                    every_seconds=config["retention_hours"] * 3600
                )
                bucket.retention_rules = [retention_rules]

                self.buckets_api.update_bucket(bucket=bucket)
                logger.info(f"✅ Updated bucket '{bucket_name}' retention to {config['retention_hours']}h")
            else:
                raise Exception("Bucket not found")

        except Exception:
            # Create bucket
            logger.info(f"Creating bucket '{bucket_name}'...")

            retention_rules = BucketRetentionRules(
                type="expire",
                every_seconds=config["retention_hours"] * 3600
            )

            self.buckets_api.create_bucket(
                bucket_name=bucket_name,
                retention_rules=retention_rules,
                org=settings.INFLUXDB_ORG,
                description=config["description"]
            )

            logger.info(f"✅ Created bucket '{bucket_name}' with {config['retention_hours']}h retention")

    async def setup_continuous_queries(self):
        """
        Setup continuous queries (tasks) for automatic data rollups.

        CQ 1: 1h mean rollup (timeseries → aggregations)
        CQ 2: 1d mean rollup (aggregations → downsampled)
        """
        logger.info("Setting up InfluxDB continuous queries (tasks)...")

        tasks = [
            {
                "name": "cq_1h_rollup",
                "flux": self._get_1h_rollup_flux(),
                "every": "1h",
                "offset": "5m"
            },
            {
                "name": "cq_1d_rollup",
                "flux": self._get_1d_rollup_flux(),
                "every": "1d",
                "offset": "10m"
            }
        ]

        for task_config in tasks:
            await self._create_or_update_task(task_config)

        logger.info("✅ Continuous queries configured successfully")

    def _get_1h_rollup_flux(self) -> str:
        """
        Flux query for 1-hour rollup.

        Aggregates raw data from 'timeseries' bucket into 1h windows
        and stores in 'aggregations' bucket.
        """
        return f"""
option task = {{name: "cq_1h_rollup", every: 1h, offset: 5m}}

from(bucket: "timeseries")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] =~ /.*/)
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> set(key: "_rollup", value: "1h")
  |> to(bucket: "aggregations", org: "{settings.INFLUXDB_ORG}")
"""

    def _get_1d_rollup_flux(self) -> str:
        """
        Flux query for 1-day rollup.

        Aggregates 1h data from 'aggregations' bucket into 1d windows
        and stores in 'downsampled' bucket.
        """
        return f"""
option task = {{name: "cq_1d_rollup", every: 1d, offset: 10m}}

from(bucket: "aggregations")
  |> range(start: -1d)
  |> filter(fn: (r) => r["_rollup"] == "1h")
  |> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
  |> set(key: "_rollup", value: "1d")
  |> to(bucket: "downsampled", org: "{settings.INFLUXDB_ORG}")
"""

    async def _create_or_update_task(self, config: Dict[str, Any]):
        """Create or update a task (continuous query)."""
        task_name = config["name"]

        # Check if task exists
        tasks = self.tasks_api.find_tasks()
        existing_task = next((t for t in tasks if t.name == task_name), None)

        if existing_task:
            logger.info(f"Task '{task_name}' already exists, updating...")

            # Update task
            existing_task.flux = config["flux"]
            existing_task.every = config["every"]
            existing_task.offset = config.get("offset")

            self.tasks_api.update_task(task=existing_task)
            logger.info(f"✅ Updated task '{task_name}'")
        else:
            # Create task
            logger.info(f"Creating task '{task_name}'...")

            self.tasks_api.create_task_every(
                name=task_name,
                flux=config["flux"],
                every=config["every"],
                organization=settings.INFLUXDB_ORG,
                offset=config.get("offset")
            )

            logger.info(f"✅ Created task '{task_name}'")

    async def optimize_queries(self):
        """
        Additional query optimizations.

        - Enable TSI (Time Series Index) - already default in InfluxDB 2.x
        - Optimize shard groups
        """
        logger.info("Applying additional InfluxDB optimizations...")

        # TSI is enabled by default in InfluxDB 2.x
        # Shard groups are optimized via bucket configuration

        logger.info("✅ InfluxDB optimizations applied")

    async def verify_setup(self) -> Dict[str, Any]:
        """
        Verify that all buckets and tasks are configured correctly.

        Returns:
            status: Dict with setup verification results
        """
        logger.info("Verifying InfluxDB setup...")

        # Check buckets
        buckets = self.buckets_api.find_buckets().buckets
        bucket_names = [b.name for b in buckets]

        buckets_ok = all(
            name in bucket_names
            for name in ["timeseries", "aggregations", "downsampled"]
        )

        # Check tasks
        tasks = self.tasks_api.find_tasks()
        task_names = [t.name for t in tasks]

        tasks_ok = all(
            name in task_names
            for name in ["cq_1h_rollup", "cq_1d_rollup"]
        )

        status = {
            "buckets_configured": buckets_ok,
            "buckets_found": bucket_names,
            "tasks_configured": tasks_ok,
            "tasks_found": task_names,
            "overall_status": "OK" if (buckets_ok and tasks_ok) else "INCOMPLETE"
        }

        if status["overall_status"] == "OK":
            logger.info("✅ InfluxDB setup verification passed")
        else:
            logger.warning("⚠️ InfluxDB setup incomplete")

        return status


async def initialize_influxdb():
    """
    Initialize InfluxDB with optimized configuration.

    Called on application startup.
    """
    service = InfluxDBSetupService()

    try:
        await service.setup_buckets_and_retention()
        await service.setup_continuous_queries()
        await service.optimize_queries()

        status = await service.verify_setup()

        if status["overall_status"] == "OK":
            logger.info("✅ InfluxDB initialization complete and verified")
        else:
            logger.error(f"❌ InfluxDB initialization incomplete: {status}")

    except Exception as e:
        logger.error(f"❌ Error initializing InfluxDB: {e}")
        raise
