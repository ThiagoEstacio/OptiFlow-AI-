"""
Consumer Metrics API
====================

Expõe métricas do consumer Kafka e pipeline para monitoramento.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any, Optional
import logging
import asyncio
import os
from datetime import datetime

from app.services.timeseries_consumer import get_consumer_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


# === HELPER FUNCTIONS FOR INFRASTRUCTURE CHECKS ===

async def check_kafka_health() -> Dict[str, Any]:
    """Check Kafka cluster health using aiokafka"""
    try:
        from aiokafka import AIOKafkaConsumer
        from aiokafka.admin import AIOKafkaAdminClient

        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-1:9092,kafka-2:9093,kafka-3:9096")

        # Try to connect and list topics
        admin = AIOKafkaAdminClient(bootstrap_servers=bootstrap_servers)
        await asyncio.wait_for(admin.start(), timeout=5.0)

        # Get cluster metadata
        topics = await admin.list_topics()
        await admin.close()

        return {
            "status": "healthy",
            "brokers": bootstrap_servers,
            "topics_count": len(topics),
            "topics": list(topics)[:10],  # First 10 topics
            "checked_at": datetime.utcnow().isoformat()
        }
    except asyncio.TimeoutError:
        return {
            "status": "timeout",
            "error": "Connection to Kafka timed out",
            "brokers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "unknown")
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "brokers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "unknown")
        }


async def check_influxdb_health() -> Dict[str, Any]:
    """Check InfluxDB health and get basic stats"""
    try:
        from influxdb_client import InfluxDBClient
        from influxdb_client.client.exceptions import InfluxDBError

        url = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
        token = os.getenv("INFLUXDB_TOKEN", "")
        org = os.getenv("INFLUXDB_ORG", "optiflow")

        client = InfluxDBClient(url=url, token=token, org=org)

        # Check health
        health = client.health()

        # Get bucket info
        buckets_api = client.buckets_api()
        buckets = buckets_api.find_buckets().buckets
        bucket_names = [b.name for b in buckets]

        # Try to get some stats from raw_data bucket
        query_api = client.query_api()
        query = '''
        from(bucket: "raw_data")
          |> range(start: -1h)
          |> count()
          |> sum(column: "_value")
        '''

        points_1h = 0
        try:
            result = query_api.query(query)
            for table in result:
                for record in table.records:
                    points_1h += record.get_value() or 0
        except Exception:
            pass  # Query might fail if no data

        client.close()

        return {
            "status": health.status if health else "unknown",
            "url": url,
            "org": org,
            "buckets": bucket_names,
            "points_last_hour": points_1h,
            "checked_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "url": os.getenv("INFLUXDB_URL", "unknown")
        }


async def check_redis_health() -> Dict[str, Any]:
    """Check Redis health"""
    try:
        import redis.asyncio as aioredis

        # Try REDIS_URL first, fallback to individual settings
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            client = aioredis.from_url(redis_url)
            host_info = redis_url.split("@")[-1].split("/")[0] if "@" in redis_url else redis_url
        else:
            host = os.getenv("REDIS_HOST", "redis")
            port = int(os.getenv("REDIS_PORT", "6379"))
            password = os.getenv("REDIS_PASSWORD", "")
            client = aioredis.Redis(host=host, port=port, password=password or None)
            host_info = f"{host}:{port}"

        # Ping and get info
        await client.ping()
        info = await client.info("memory")
        keys = await client.dbsize()

        await client.close()

        return {
            "status": "healthy",
            "host": host_info,
            "memory_used": info.get("used_memory_human", "unknown"),
            "keys_count": keys,
            "checked_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/consumer")
async def get_consumer_metrics() -> Dict[str, Any]:
    """
    Get current consumer metrics

    Returns:
        - running: bool - Consumer is active
        - lag: int - Number of messages behind
        - throughput: float - Messages/second
        - error_rate: float - Errors/second
        - last_offset: int - Last committed offset
        - batch_size: int - Current adaptive batch size
    """
    try:
        status = get_consumer_status()

        return {
            "status": "healthy" if status.get("running") else "stopped",
            "running": status.get("running", False),
            "messages_processed": status.get("messages_processed", 0),
            "errors_count": status.get("errors", 0),
            "batch_size_current": status.get("batch_size", 0),
            "consumer_enabled": status.get("enabled", False),
            "topic": status.get("topic", "unknown"),
            "group_id": status.get("group_id", "unknown")
        }
    except Exception as e:
        logger.error(f"Failed to get consumer metrics: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/pipeline")
async def get_pipeline_metrics() -> Dict[str, Any]:
    """
    Get overall pipeline health metrics

    Checks:
    - Gateway publishing status
    - Kafka cluster health
    - Consumer processing status
    - InfluxDB writing status
    - Redis cache status

    Returns comprehensive pipeline health status.
    """
    # Run all health checks concurrently
    kafka_task = asyncio.create_task(check_kafka_health())
    influxdb_task = asyncio.create_task(check_influxdb_health())
    redis_task = asyncio.create_task(check_redis_health())

    consumer_status = get_consumer_status()

    # Wait for all checks
    kafka_health = await kafka_task
    influxdb_health = await influxdb_task
    redis_health = await redis_task

    # Determine overall pipeline status
    all_healthy = (
        kafka_health.get("status") == "healthy" and
        influxdb_health.get("status") == "pass" and
        redis_health.get("status") == "healthy"
    )

    consumer_running = consumer_status.get("running", False)

    if all_healthy and consumer_running:
        pipeline_status = "operational"
    elif kafka_health.get("status") == "healthy":
        pipeline_status = "degraded"
    else:
        pipeline_status = "critical"

    return {
        "pipeline_status": pipeline_status,
        "checked_at": datetime.utcnow().isoformat(),
        "components": {
            "kafka": kafka_health,
            "influxdb": influxdb_health,
            "redis": redis_health,
            "consumer": {
                "status": "running" if consumer_running else "stopped",
                "enabled": consumer_status.get("enabled", False),
                "messages_processed": consumer_status.get("messages_processed", 0),
                "errors": consumer_status.get("errors", 0),
                "topic": consumer_status.get("topic", "unknown"),
                "group_id": consumer_status.get("group_id", "unknown")
            }
        },
        "data_flow": {
            "description": "Gateway → Kafka → Consumer → InfluxDB",
            "gateway": "Publishing to Kafka (check /api/v1/gateway/status)",
            "kafka_to_influxdb": "running" if consumer_running else "stopped"
        }
    }


@router.get("/kafka")
async def get_kafka_metrics() -> Dict[str, Any]:
    """
    Get detailed Kafka cluster metrics

    Returns:
    - Cluster health status
    - List of topics
    - Broker information
    """
    return await check_kafka_health()


@router.get("/influxdb")
async def get_influxdb_metrics() -> Dict[str, Any]:
    """
    Get detailed InfluxDB metrics

    Returns:
    - Health status
    - List of buckets
    - Points written in last hour
    """
    return await check_influxdb_health()


@router.get("/redis")
async def get_redis_metrics() -> Dict[str, Any]:
    """
    Get Redis cache metrics

    Returns:
    - Health status
    - Memory usage
    - Keys count
    """
    return await check_redis_health()


@router.get("/gateway")
async def get_gateway_metrics() -> Dict[str, Any]:
    """
    Get gateway status by calling gateway API

    Returns adapter status and tag counts.
    """
    import httpx

    gateway_url = os.getenv("GATEWAY_URL", "http://optiflow-gateway:8080")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Get health
            health_resp = await client.get(f"{gateway_url}/health")
            health = health_resp.json() if health_resp.status_code == 200 else {"status": "unreachable"}

            # Get adapters
            adapters_resp = await client.get(f"{gateway_url}/api/adapters/")
            adapters = adapters_resp.json() if adapters_resp.status_code == 200 else []

            # Get tags count
            tags_resp = await client.get(f"{gateway_url}/api/tags/list")
            tags_data = tags_resp.json() if tags_resp.status_code == 200 else {}
            tags_count = tags_data.get("count", 0)

        return {
            "status": "healthy" if health.get("status") == "healthy" else "degraded",
            "url": gateway_url,
            "health": health,
            "adapters_count": len(adapters) if isinstance(adapters, list) else 0,
            "adapters": adapters if isinstance(adapters, list) else [],
            "tags_count": tags_count,
            "checked_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "url": gateway_url
        }
