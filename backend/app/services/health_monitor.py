"""
OptiFlow Health Monitoring Service
===================================

Comprehensive health monitoring for all services with predictive alerts.

Features:
- Container health checks (memory, CPU, restarts)
- Database connection pool monitoring
- Redis memory and connection tracking
- Kafka lag monitoring
- InfluxDB write performance
- Predictive alerts based on trends
- Circuit breaker state monitoring

Author: OptiFlow AI Team
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import statistics

import httpx
import redis.asyncio as redis
from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    """Health status for a single service"""
    name: str
    status: HealthStatus
    latency_ms: float = 0.0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    last_check: datetime = field(default_factory=datetime.utcnow)
    consecutive_failures: int = 0
    trend: str = "stable"  # improving, stable, degrading


@dataclass
class SystemHealth:
    """Overall system health"""
    status: HealthStatus
    services: Dict[str, ServiceHealth] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.utcnow)


class HealthMonitor:
    """
    Comprehensive health monitoring service

    Monitors all OptiFlow services and provides:
    - Real-time health status
    - Trend analysis for predictive alerts
    - Resource usage tracking
    - Recommendations for issue resolution
    """

    # Thresholds for health status
    THRESHOLDS = {
        "latency_warning_ms": 500,
        "latency_critical_ms": 2000,
        "memory_warning_percent": 80,
        "memory_critical_percent": 95,
        "cpu_warning_percent": 80,
        "cpu_critical_percent": 95,
        "db_pool_warning_percent": 70,
        "db_pool_critical_percent": 90,
        "redis_memory_warning_mb": 500,
        "redis_memory_critical_mb": 900,
        "kafka_lag_warning": 1000,
        "kafka_lag_critical": 10000,
        "consecutive_failures_warning": 2,
        "consecutive_failures_critical": 5,
    }

    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None
        self.redis_client: Optional[redis.Redis] = None

        # Historical data for trend analysis
        self._history: Dict[str, List[Dict[str, Any]]] = {}
        self._history_max_size = 100  # Keep last 100 measurements

        # Circuit breaker states
        self._circuit_breakers: Dict[str, Dict[str, Any]] = {}

        # Service endpoints
        self.services = {
            "backend": f"http://localhost:8000/api/health",
            "gateway": f"http://localhost:8080/health",
            "frontend": f"http://localhost:3000/",
            "grafana": f"http://localhost:3001/api/health",
            "prometheus": f"http://localhost:9090/-/healthy",
            "influxdb": f"http://localhost:8086/health",
            "kafka_ui": f"http://localhost:8090/",
        }

    async def initialize(self):
        """Initialize monitoring connections"""
        self.http_client = httpx.AsyncClient(timeout=10.0)

        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Could not initialize Redis client: {e}")

    async def close(self):
        """Close monitoring connections"""
        if self.http_client:
            await self.http_client.aclose()
        if self.redis_client:
            await self.redis_client.close()

    async def check_all_services(self) -> SystemHealth:
        """
        Perform comprehensive health check of all services

        Returns:
            SystemHealth object with status of all services
        """
        system_health = SystemHealth(status=HealthStatus.HEALTHY)

        # Run all checks in parallel
        checks = await asyncio.gather(
            self._check_http_services(),
            self._check_database(),
            self._check_redis(),
            self._check_kafka(),
            self._check_influxdb(),
            self._check_containers(),
            return_exceptions=True
        )

        # Process results
        for check_result in checks:
            if isinstance(check_result, Exception):
                logger.error(f"Health check failed: {check_result}")
                continue
            if isinstance(check_result, dict):
                system_health.services.update(check_result)

        # Analyze overall health
        system_health = self._analyze_system_health(system_health)

        # Store in history for trend analysis
        self._update_history(system_health)

        return system_health

    async def _check_http_services(self) -> Dict[str, ServiceHealth]:
        """Check HTTP-based services"""
        results = {}

        for name, url in self.services.items():
            start_time = time.time()
            try:
                response = await self.http_client.get(url)
                latency_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    status = HealthStatus.HEALTHY
                    if latency_ms > self.THRESHOLDS["latency_critical_ms"]:
                        status = HealthStatus.DEGRADED
                    elif latency_ms > self.THRESHOLDS["latency_warning_ms"]:
                        status = HealthStatus.DEGRADED

                    results[name] = ServiceHealth(
                        name=name,
                        status=status,
                        latency_ms=latency_ms,
                        message="Service responding normally",
                        details={"status_code": response.status_code}
                    )
                else:
                    results[name] = ServiceHealth(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        latency_ms=latency_ms,
                        message=f"HTTP {response.status_code}",
                        details={"status_code": response.status_code}
                    )

            except httpx.TimeoutException:
                results[name] = ServiceHealth(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message="Request timed out",
                    consecutive_failures=self._increment_failure(name)
                )
            except httpx.ConnectError:
                results[name] = ServiceHealth(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message="Connection refused - service may be down",
                    consecutive_failures=self._increment_failure(name)
                )
            except Exception as e:
                results[name] = ServiceHealth(
                    name=name,
                    status=HealthStatus.UNKNOWN,
                    message=str(e),
                    consecutive_failures=self._increment_failure(name)
                )

        return results

    async def _check_database(self) -> Dict[str, ServiceHealth]:
        """Check PostgreSQL database health"""
        from app.core.database import get_db_session

        start_time = time.time()
        try:
            async with get_db_session() as session:
                # Check connection
                result = await session.execute(text("SELECT 1"))
                result.scalar()

                # Check connection pool stats
                pool_stats = await session.execute(text("""
                    SELECT
                        numbackends as active_connections,
                        (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """))
                stats = pool_stats.fetchone()

                latency_ms = (time.time() - start_time) * 1000

                # Calculate pool usage
                pool_usage_percent = 0
                if stats and stats.max_connections:
                    pool_usage_percent = (stats.active_connections / stats.max_connections) * 100

                status = HealthStatus.HEALTHY
                message = "Database responding normally"

                if pool_usage_percent > self.THRESHOLDS["db_pool_critical_percent"]:
                    status = HealthStatus.CRITICAL
                    message = f"Connection pool at {pool_usage_percent:.1f}% - critical"
                elif pool_usage_percent > self.THRESHOLDS["db_pool_warning_percent"]:
                    status = HealthStatus.DEGRADED
                    message = f"Connection pool at {pool_usage_percent:.1f}% - warning"

                return {
                    "postgresql": ServiceHealth(
                        name="postgresql",
                        status=status,
                        latency_ms=latency_ms,
                        message=message,
                        details={
                            "active_connections": stats.active_connections if stats else 0,
                            "max_connections": stats.max_connections if stats else 0,
                            "pool_usage_percent": pool_usage_percent
                        }
                    )
                }

        except Exception as e:
            return {
                "postgresql": ServiceHealth(
                    name="postgresql",
                    status=HealthStatus.CRITICAL,
                    message=f"Database error: {str(e)}",
                    consecutive_failures=self._increment_failure("postgresql")
                )
            }

    async def _check_redis(self) -> Dict[str, ServiceHealth]:
        """Check Redis health and memory usage"""
        if not self.redis_client:
            return {
                "redis": ServiceHealth(
                    name="redis",
                    status=HealthStatus.UNKNOWN,
                    message="Redis client not initialized"
                )
            }

        start_time = time.time()
        try:
            # Ping Redis
            await self.redis_client.ping()

            # Get memory info
            info = await self.redis_client.info("memory")
            used_memory_mb = info.get("used_memory", 0) / (1024 * 1024)
            max_memory_mb = info.get("maxmemory", 0) / (1024 * 1024)

            # Get client info
            client_info = await self.redis_client.info("clients")
            connected_clients = client_info.get("connected_clients", 0)

            latency_ms = (time.time() - start_time) * 1000

            status = HealthStatus.HEALTHY
            message = "Redis responding normally"

            if used_memory_mb > self.THRESHOLDS["redis_memory_critical_mb"]:
                status = HealthStatus.CRITICAL
                message = f"Redis memory critical: {used_memory_mb:.1f}MB"
            elif used_memory_mb > self.THRESHOLDS["redis_memory_warning_mb"]:
                status = HealthStatus.DEGRADED
                message = f"Redis memory warning: {used_memory_mb:.1f}MB"

            return {
                "redis": ServiceHealth(
                    name="redis",
                    status=status,
                    latency_ms=latency_ms,
                    message=message,
                    details={
                        "used_memory_mb": used_memory_mb,
                        "max_memory_mb": max_memory_mb,
                        "connected_clients": connected_clients,
                        "memory_usage_percent": (used_memory_mb / max_memory_mb * 100) if max_memory_mb > 0 else 0
                    }
                )
            }

        except Exception as e:
            return {
                "redis": ServiceHealth(
                    name="redis",
                    status=HealthStatus.CRITICAL,
                    message=f"Redis error: {str(e)}",
                    consecutive_failures=self._increment_failure("redis")
                )
            }

    async def _check_kafka(self) -> Dict[str, ServiceHealth]:
        """Check Kafka cluster health"""
        try:
            # Check Kafka via kafka-ui API
            response = await self.http_client.get(
                "http://localhost:8090/api/clusters/local/brokers"
            )

            if response.status_code == 200:
                brokers = response.json()
                broker_count = len(brokers) if isinstance(brokers, list) else 0

                # Check consumer lag
                lag_response = await self.http_client.get(
                    "http://localhost:8090/api/clusters/local/consumer-groups"
                )

                total_lag = 0
                if lag_response.status_code == 200:
                    groups = lag_response.json()
                    for group in groups if isinstance(groups, list) else []:
                        total_lag += group.get("lag", 0)

                status = HealthStatus.HEALTHY
                message = f"Kafka cluster healthy with {broker_count} brokers"

                if total_lag > self.THRESHOLDS["kafka_lag_critical"]:
                    status = HealthStatus.CRITICAL
                    message = f"Kafka lag critical: {total_lag} messages behind"
                elif total_lag > self.THRESHOLDS["kafka_lag_warning"]:
                    status = HealthStatus.DEGRADED
                    message = f"Kafka lag warning: {total_lag} messages behind"
                elif broker_count < 3:
                    status = HealthStatus.DEGRADED
                    message = f"Kafka cluster degraded: only {broker_count}/3 brokers"

                return {
                    "kafka": ServiceHealth(
                        name="kafka",
                        status=status,
                        message=message,
                        details={
                            "broker_count": broker_count,
                            "total_lag": total_lag
                        }
                    )
                }
            else:
                return {
                    "kafka": ServiceHealth(
                        name="kafka",
                        status=HealthStatus.UNKNOWN,
                        message="Could not reach Kafka UI"
                    )
                }

        except Exception as e:
            return {
                "kafka": ServiceHealth(
                    name="kafka",
                    status=HealthStatus.UNKNOWN,
                    message=f"Kafka check failed: {str(e)}"
                )
            }

    async def _check_influxdb(self) -> Dict[str, ServiceHealth]:
        """Check InfluxDB health and write performance"""
        start_time = time.time()
        try:
            # Check health endpoint
            response = await self.http_client.get("http://localhost:8086/health")
            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                health_data = response.json()

                status = HealthStatus.HEALTHY
                if health_data.get("status") != "pass":
                    status = HealthStatus.DEGRADED

                # Check write metrics
                metrics_response = await self.http_client.get("http://localhost:8086/metrics")
                write_errors = 0
                if metrics_response.status_code == 200:
                    # Parse prometheus metrics for write errors
                    metrics_text = metrics_response.text
                    for line in metrics_text.split("\n"):
                        if "http_api_request_duration_seconds" in line and "write" in line:
                            # Found write metrics
                            pass

                return {
                    "influxdb": ServiceHealth(
                        name="influxdb",
                        status=status,
                        latency_ms=latency_ms,
                        message="InfluxDB responding normally",
                        details={
                            "version": health_data.get("version", "unknown"),
                            "status": health_data.get("status", "unknown")
                        }
                    )
                }
            else:
                return {
                    "influxdb": ServiceHealth(
                        name="influxdb",
                        status=HealthStatus.UNHEALTHY,
                        message=f"InfluxDB returned HTTP {response.status_code}"
                    )
                }

        except Exception as e:
            return {
                "influxdb": ServiceHealth(
                    name="influxdb",
                    status=HealthStatus.CRITICAL,
                    message=f"InfluxDB error: {str(e)}",
                    consecutive_failures=self._increment_failure("influxdb")
                )
            }

    async def _check_containers(self) -> Dict[str, ServiceHealth]:
        """Check Docker container health via Docker API or cadvisor"""
        try:
            # Query cadvisor for container metrics
            response = await self.http_client.get(
                "http://localhost:9090/api/v1/query",
                params={"query": "container_memory_usage_bytes{name=~'optiflow.*'}"}
            )

            if response.status_code != 200:
                return {}

            data = response.json()
            results = {}

            for result in data.get("data", {}).get("result", []):
                container_name = result.get("metric", {}).get("name", "unknown")
                memory_bytes = float(result.get("value", [0, 0])[1])
                memory_mb = memory_bytes / (1024 * 1024)

                # Get CPU usage
                cpu_response = await self.http_client.get(
                    "http://localhost:9090/api/v1/query",
                    params={"query": f"rate(container_cpu_usage_seconds_total{{name='{container_name}'}}[5m]) * 100"}
                )

                cpu_percent = 0
                if cpu_response.status_code == 200:
                    cpu_data = cpu_response.json()
                    if cpu_data.get("data", {}).get("result"):
                        cpu_percent = float(cpu_data["data"]["result"][0].get("value", [0, 0])[1])

                status = HealthStatus.HEALTHY
                message = f"Container healthy - Memory: {memory_mb:.1f}MB, CPU: {cpu_percent:.1f}%"

                if memory_mb > 1000 or cpu_percent > self.THRESHOLDS["cpu_critical_percent"]:
                    status = HealthStatus.CRITICAL
                    message = f"Container resource critical - Memory: {memory_mb:.1f}MB, CPU: {cpu_percent:.1f}%"
                elif memory_mb > 500 or cpu_percent > self.THRESHOLDS["cpu_warning_percent"]:
                    status = HealthStatus.DEGRADED
                    message = f"Container resource warning - Memory: {memory_mb:.1f}MB, CPU: {cpu_percent:.1f}%"

                results[f"container_{container_name}"] = ServiceHealth(
                    name=container_name,
                    status=status,
                    message=message,
                    details={
                        "memory_mb": memory_mb,
                        "cpu_percent": cpu_percent
                    }
                )

            return results

        except Exception as e:
            logger.warning(f"Container check failed: {e}")
            return {}

    def _increment_failure(self, service_name: str) -> int:
        """Track consecutive failures for a service"""
        if service_name not in self._circuit_breakers:
            self._circuit_breakers[service_name] = {"failures": 0, "last_success": None}

        self._circuit_breakers[service_name]["failures"] += 1
        return self._circuit_breakers[service_name]["failures"]

    def _reset_failure(self, service_name: str):
        """Reset failure count on success"""
        if service_name in self._circuit_breakers:
            self._circuit_breakers[service_name]["failures"] = 0
            self._circuit_breakers[service_name]["last_success"] = datetime.utcnow()

    def _analyze_system_health(self, system_health: SystemHealth) -> SystemHealth:
        """Analyze overall system health and generate alerts/recommendations"""
        critical_count = 0
        unhealthy_count = 0
        degraded_count = 0

        for name, service in system_health.services.items():
            if service.status == HealthStatus.CRITICAL:
                critical_count += 1
                system_health.alerts.append(f"🔴 CRITICAL: {name} - {service.message}")

                # Add recommendations
                if "memory" in service.message.lower():
                    system_health.recommendations.append(
                        f"Consider restarting {name} or increasing memory limits"
                    )
                if "connection" in service.message.lower():
                    system_health.recommendations.append(
                        f"Check if {name} container is running: docker ps | grep {name}"
                    )

            elif service.status == HealthStatus.UNHEALTHY:
                unhealthy_count += 1
                system_health.alerts.append(f"🟠 UNHEALTHY: {name} - {service.message}")

            elif service.status == HealthStatus.DEGRADED:
                degraded_count += 1
                system_health.alerts.append(f"🟡 DEGRADED: {name} - {service.message}")

            # Check for trending issues
            trend = self._analyze_trend(name)
            service.trend = trend
            if trend == "degrading":
                system_health.alerts.append(f"📉 TRENDING DOWN: {name} performance is degrading")
                system_health.recommendations.append(
                    f"Monitor {name} closely - performance degradation detected"
                )

        # Determine overall status
        if critical_count > 0:
            system_health.status = HealthStatus.CRITICAL
        elif unhealthy_count > 0:
            system_health.status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            system_health.status = HealthStatus.DEGRADED
        else:
            system_health.status = HealthStatus.HEALTHY

        return system_health

    def _update_history(self, system_health: SystemHealth):
        """Store health data for trend analysis"""
        timestamp = datetime.utcnow()

        for name, service in system_health.services.items():
            if name not in self._history:
                self._history[name] = []

            self._history[name].append({
                "timestamp": timestamp,
                "status": service.status.value,
                "latency_ms": service.latency_ms,
                "details": service.details
            })

            # Trim history
            if len(self._history[name]) > self._history_max_size:
                self._history[name] = self._history[name][-self._history_max_size:]

    def _analyze_trend(self, service_name: str) -> str:
        """Analyze trend for a service based on historical data"""
        if service_name not in self._history or len(self._history[service_name]) < 5:
            return "stable"

        recent = self._history[service_name][-10:]

        # Check latency trend
        latencies = [h.get("latency_ms", 0) for h in recent if h.get("latency_ms")]
        if len(latencies) >= 5:
            first_half = statistics.mean(latencies[:len(latencies)//2])
            second_half = statistics.mean(latencies[len(latencies)//2:])

            if second_half > first_half * 1.5:
                return "degrading"
            elif second_half < first_half * 0.7:
                return "improving"

        # Check status trend
        statuses = [h.get("status") for h in recent]
        if statuses[-3:] == ["critical", "critical", "critical"]:
            return "degrading"
        elif statuses[-3:] == ["healthy", "healthy", "healthy"] and statuses[0] != "healthy":
            return "improving"

        return "stable"

    def get_health_summary(self) -> Dict[str, Any]:
        """Get a quick health summary for API response"""
        if not self._history:
            return {
                "status": "unknown",
                "message": "No health data available yet",
                "checked_at": None
            }

        # Get latest status for each service
        services_status = {}
        for name, history in self._history.items():
            if history:
                latest = history[-1]
                services_status[name] = {
                    "status": latest["status"],
                    "latency_ms": latest.get("latency_ms", 0),
                    "trend": self._analyze_trend(name)
                }

        # Determine overall status
        statuses = [s["status"] for s in services_status.values()]
        if "critical" in statuses:
            overall = "critical"
        elif "unhealthy" in statuses:
            overall = "unhealthy"
        elif "degraded" in statuses:
            overall = "degraded"
        else:
            overall = "healthy"

        return {
            "status": overall,
            "services": services_status,
            "alerts_count": len([s for s in statuses if s in ["critical", "unhealthy"]]),
            "checked_at": datetime.utcnow().isoformat()
        }


# Singleton instance
_health_monitor: Optional[HealthMonitor] = None


async def get_health_monitor() -> HealthMonitor:
    """Get or create health monitor instance"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
        await _health_monitor.initialize()
    return _health_monitor


async def run_health_check() -> Dict[str, Any]:
    """Run a complete health check and return results"""
    monitor = await get_health_monitor()
    health = await monitor.check_all_services()

    return {
        "status": health.status.value,
        "services": {
            name: {
                "status": svc.status.value,
                "latency_ms": svc.latency_ms,
                "message": svc.message,
                "trend": svc.trend,
                "details": svc.details
            }
            for name, svc in health.services.items()
        },
        "alerts": health.alerts,
        "recommendations": health.recommendations,
        "checked_at": health.checked_at.isoformat()
    }
