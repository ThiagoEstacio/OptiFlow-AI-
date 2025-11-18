"""
Comprehensive Health Check Service

Consolidates health checks for all critical services:
- PostgreSQL database
- Redis cache
- InfluxDB timeseries
- RabbitMQ message broker
- Kafka streaming
- Vault secrets manager
- Gateway OPC-UA service

Provides unified health status endpoint for monitoring and orchestration.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class HealthCheckService:
    """
    Centralized health check service for all OptiFlow dependencies.

    Provides:
    - Individual service health checks
    - Aggregate system health status
    - Detailed diagnostic information
    - Performance metrics (response times)
    """

    def __init__(self):
        self.service_checks = {
            'postgres': self._check_postgres,
            'redis': self._check_redis,
            'influxdb': self._check_influxdb,
            'rabbitmq': self._check_rabbitmq,
            'kafka': self._check_kafka,
            'vault': self._check_vault,
            'gateway': self._check_gateway,
        }

    async def check_all_services(self) -> Dict[str, Any]:
        """
        Run health checks for all services in parallel.

        Returns:
            {
                "status": "healthy" | "degraded" | "unhealthy",
                "timestamp": "2025-01-13T12:00:00Z",
                "services": {
                    "postgres": {"status": "healthy", "response_time_ms": 5, ...},
                    "redis": {...},
                    ...
                },
                "summary": {
                    "total": 7,
                    "healthy": 7,
                    "degraded": 0,
                    "unhealthy": 0
                }
            }
        """
        timestamp = datetime.utcnow().isoformat() + 'Z'

        # Run all checks in parallel
        check_tasks = {
            service_name: self._run_check_with_timing(service_name, check_func)
            for service_name, check_func in self.service_checks.items()
        }

        results = await asyncio.gather(
            *check_tasks.values(),
            return_exceptions=True
        )

        # Build service results
        services = {}
        for (service_name, _), result in zip(check_tasks.items(), results):
            if isinstance(result, Exception):
                services[service_name] = {
                    'status': 'unhealthy',
                    'error': str(result),
                    'response_time_ms': None
                }
            else:
                services[service_name] = result

        # Calculate summary
        summary = {
            'total': len(services),
            'healthy': sum(1 for s in services.values() if s['status'] == 'healthy'),
            'degraded': sum(1 for s in services.values() if s['status'] == 'degraded'),
            'unhealthy': sum(1 for s in services.values() if s['status'] == 'unhealthy')
        }

        # Determine overall status
        if summary['unhealthy'] > 0:
            overall_status = 'unhealthy'
        elif summary['degraded'] > 0:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'

        return {
            'status': overall_status,
            'timestamp': timestamp,
            'services': services,
            'summary': summary
        }

    async def _run_check_with_timing(
        self,
        service_name: str,
        check_func
    ) -> Dict[str, Any]:
        """Run a health check function and measure response time."""
        start_time = asyncio.get_event_loop().time()

        try:
            result = await check_func()
            elapsed_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
            result['response_time_ms'] = elapsed_ms
            return result
        except Exception as e:
            elapsed_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
            logger.error(f"Health check failed for {service_name}: {e}", exc_info=True)
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time_ms': elapsed_ms
            }

    # ==================== Individual Service Checks ====================

    async def _check_postgres(self) -> Dict[str, Any]:
        """Check PostgreSQL database health."""
        try:
            from app.db.session import AsyncSessionLocal
            from sqlalchemy import text

            async with AsyncSessionLocal() as session:
                # Test query
                result = await session.execute(text("SELECT 1"))
                result.scalar()

                # Get database info
                version_result = await session.execute(text("SELECT version()"))
                version = version_result.scalar()

                # Check connection pool
                pool_size = session.get_bind().pool.size()
                pool_checked_out = session.get_bind().pool.checkedout()

                return {
                    'status': 'healthy',
                    'version': version.split(',')[0] if version else 'unknown',
                    'pool_size': pool_size,
                    'connections_in_use': pool_checked_out,
                    'connections_available': pool_size - pool_checked_out
                }

        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis cache health."""
        try:
            from app.core.cache import get_redis_client

            redis = await get_redis_client()

            # Test ping
            pong = await redis.ping()
            if not pong:
                raise Exception("Redis ping failed")

            # Get info
            info = await redis.info()

            return {
                'status': 'healthy',
                'version': info.get('redis_version', 'unknown'),
                'used_memory_mb': int(info.get('used_memory', 0)) // (1024 * 1024),
                'connected_clients': info.get('connected_clients', 0),
                'uptime_days': int(info.get('uptime_in_seconds', 0)) // 86400
            }

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    async def _check_influxdb(self) -> Dict[str, Any]:
        """Check InfluxDB timeseries database health."""
        try:
            from app.db.influxdb import get_influxdb_client

            client = get_influxdb_client()

            # Test health endpoint
            health = client.health()

            if health.status != 'pass':
                return {
                    'status': 'degraded',
                    'influxdb_status': health.status,
                    'message': health.message or 'InfluxDB not fully healthy'
                }

            # Get buckets
            buckets_api = client.buckets_api()
            buckets = buckets_api.find_buckets().buckets

            return {
                'status': 'healthy',
                'version': health.version or 'unknown',
                'influxdb_status': health.status,
                'buckets_count': len(buckets) if buckets else 0
            }

        except Exception as e:
            logger.error(f"InfluxDB health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    async def _check_rabbitmq(self) -> Dict[str, Any]:
        """Check RabbitMQ message broker health."""
        try:
            import aio_pika
            from app.core.config import settings

            # Test connection
            connection = await aio_pika.connect_robust(
                f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@"
                f"{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
            )

            async with connection:
                channel = await connection.channel()

                # Get queue info (if available)
                try:
                    queue = await channel.declare_queue('celery', passive=True)
                    message_count = queue.declaration_result.message_count
                except Exception:
                    message_count = None

                return {
                    'status': 'healthy',
                    'connection': 'established',
                    'celery_queue_messages': message_count
                }

        except Exception as e:
            logger.error(f"RabbitMQ health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    async def _check_kafka(self) -> Dict[str, Any]:
        """Check Kafka streaming platform health."""
        try:
            from aiokafka import AIOKafkaProducer
            from app.core.config import settings

            # Test connection with short timeout
            producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                request_timeout_ms=5000
            )

            await producer.start()

            # Get cluster metadata
            metadata = await producer.client.fetch_all_metadata()
            brokers_count = len(metadata.brokers)
            topics_count = len(metadata.topics)

            await producer.stop()

            return {
                'status': 'healthy',
                'brokers_count': brokers_count,
                'topics_count': topics_count,
                'connection': 'established'
            }

        except Exception as e:
            logger.warning(f"Kafka health check failed: {e}")
            # Kafka is optional in some deployments
            return {
                'status': 'degraded',
                'error': str(e),
                'message': 'Kafka not available (optional service)'
            }

    async def _check_vault(self) -> Dict[str, Any]:
        """Check HashiCorp Vault secrets manager health."""
        try:
            from app.core.vault import vault_client

            # Check if Vault is initialized and unsealed
            if not vault_client.sys.is_initialized():
                return {
                    'status': 'unhealthy',
                    'error': 'Vault not initialized'
                }

            if vault_client.sys.is_sealed():
                return {
                    'status': 'unhealthy',
                    'error': 'Vault is sealed'
                }

            # Test read access
            health = vault_client.sys.read_health_status(method='GET')

            return {
                'status': 'healthy',
                'initialized': True,
                'sealed': False,
                'cluster_name': health.get('cluster_name', 'unknown'),
                'version': health.get('version', 'unknown')
            }

        except Exception as e:
            logger.error(f"Vault health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    async def _check_gateway(self) -> Dict[str, Any]:
        """Check OPC-UA Gateway service health."""
        try:
            import httpx

            # Test gateway health endpoint
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get('http://gateway:5001/health')

                if response.status_code != 200:
                    return {
                        'status': 'degraded',
                        'http_status': response.status_code,
                        'error': 'Gateway returned non-200 status'
                    }

                data = response.json()

                return {
                    'status': 'healthy',
                    'gateway_status': data.get('status', 'unknown'),
                    'opcua_connected': data.get('opcua_connected', False),
                    'kafka_connected': data.get('kafka_connected', False)
                }

        except Exception as e:
            logger.warning(f"Gateway health check failed: {e}")
            # Gateway might not be deployed in all environments
            return {
                'status': 'degraded',
                'error': str(e),
                'message': 'Gateway not available (optional service)'
            }


# Singleton instance
_health_check_service: Optional[HealthCheckService] = None


def get_health_check_service() -> HealthCheckService:
    """Get or create global health check service instance."""
    global _health_check_service

    if _health_check_service is None:
        _health_check_service = HealthCheckService()

    return _health_check_service
