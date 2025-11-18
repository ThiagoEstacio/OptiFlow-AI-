"""
Prometheus Metrics Exporter (PDCA #20)

Exports OptiFlow metrics in Prometheus format.

Metrics Categories:
- System metrics (CPU, memory, disk)
- Application metrics (requests, errors, latency)
- Database metrics (pool, queries, circuit breakers)
- WebSocket metrics (connections, messages)
- Kafka metrics (messages, lag)
- Business metrics (alarms, assets, users)
"""

import logging
from typing import Dict, Any, List
import psutil
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class PrometheusExporter:
    """
    Exports metrics in Prometheus format.

    Format:
    # HELP metric_name Description
    # TYPE metric_name gauge|counter|histogram
    metric_name{label="value"} value timestamp
    """

    def __init__(self):
        self.start_time = time.time()

    def export_metrics(self) -> str:
        """
        Export all metrics in Prometheus format.

        Returns:
            String with all metrics in Prometheus exposition format
        """
        metrics = []

        # System metrics
        metrics.extend(self._system_metrics())

        # Application metrics
        metrics.extend(self._app_metrics())

        # Database metrics
        metrics.extend(self._database_metrics())

        # WebSocket metrics
        metrics.extend(self._websocket_metrics())

        # Business metrics
        metrics.extend(self._business_metrics())

        return "\n".join(metrics)

    def _system_metrics(self) -> List[str]:
        """Export system-level metrics."""
        metrics = []

        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        metrics.append('# HELP optiflow_system_cpu_percent CPU usage percentage')
        metrics.append('# TYPE optiflow_system_cpu_percent gauge')
        metrics.append(f'optiflow_system_cpu_percent {cpu_percent}')

        # Memory
        memory = psutil.virtual_memory()
        metrics.append('# HELP optiflow_system_memory_used_bytes Memory used in bytes')
        metrics.append('# TYPE optiflow_system_memory_used_bytes gauge')
        metrics.append(f'optiflow_system_memory_used_bytes {memory.used}')

        metrics.append('# HELP optiflow_system_memory_percent Memory usage percentage')
        metrics.append('# TYPE optiflow_system_memory_percent gauge')
        metrics.append(f'optiflow_system_memory_percent {memory.percent}')

        # Disk
        disk = psutil.disk_usage('/')
        metrics.append('# HELP optiflow_system_disk_used_bytes Disk used in bytes')
        metrics.append('# TYPE optiflow_system_disk_used_bytes gauge')
        metrics.append(f'optiflow_system_disk_used_bytes {disk.used}')

        metrics.append('# HELP optiflow_system_disk_percent Disk usage percentage')
        metrics.append('# TYPE optiflow_system_disk_percent gauge')
        metrics.append(f'optiflow_system_disk_percent {disk.percent}')

        # Uptime
        uptime = time.time() - self.start_time
        metrics.append('# HELP optiflow_system_uptime_seconds System uptime in seconds')
        metrics.append('# TYPE optiflow_system_uptime_seconds counter')
        metrics.append(f'optiflow_system_uptime_seconds {uptime}')

        return metrics

    def _app_metrics(self) -> List[str]:
        """Export application-level metrics."""
        metrics = []

        # These would come from actual request counters
        # For now, returning structure
        metrics.append('# HELP optiflow_http_requests_total Total HTTP requests')
        metrics.append('# TYPE optiflow_http_requests_total counter')
        metrics.append('optiflow_http_requests_total{method="GET",status="200"} 0')

        metrics.append('# HELP optiflow_http_request_duration_seconds HTTP request duration')
        metrics.append('# TYPE optiflow_http_request_duration_seconds histogram')
        metrics.append('optiflow_http_request_duration_seconds_sum 0')
        metrics.append('optiflow_http_request_duration_seconds_count 0')

        return metrics

    def _database_metrics(self) -> List[str]:
        """Export database metrics."""
        metrics = []

        try:
            from app.services.db_pool_monitor import get_pool_monitor

            monitor = get_pool_monitor()
            status = monitor.get_pool_status()

            # Connection pool
            metrics.append('# HELP optiflow_db_pool_size Database connection pool size')
            metrics.append('# TYPE optiflow_db_pool_size gauge')
            metrics.append(f'optiflow_db_pool_size {status["pool_size"]}')

            metrics.append('# HELP optiflow_db_pool_in_use Connections in use')
            metrics.append('# TYPE optiflow_db_pool_in_use gauge')
            metrics.append(f'optiflow_db_pool_in_use {status["connections_in_use"]}')

            metrics.append('# HELP optiflow_db_pool_usage_percent Pool usage percentage')
            metrics.append('# TYPE optiflow_db_pool_usage_percent gauge')
            metrics.append(f'optiflow_db_pool_usage_percent {status["usage_percent"]}')

        except Exception as e:
            logger.debug(f"Could not get DB metrics: {e}")

        try:
            from app.core.circuit_breaker import get_all_circuit_breakers

            breakers = get_all_circuit_breakers()

            # Circuit breakers
            for name, breaker in breakers.items():
                state_map = {"closed": 0, "open": 1, "half_open": 2}
                state_value = state_map.get(breaker.state, -1)

                metrics.append(f'# HELP optiflow_circuit_breaker_state Circuit breaker state')
                metrics.append(f'# TYPE optiflow_circuit_breaker_state gauge')
                metrics.append(f'optiflow_circuit_breaker_state{{name="{name}"}} {state_value}')

                metrics.append(f'# HELP optiflow_circuit_breaker_failures Circuit breaker failures')
                metrics.append(f'# TYPE optiflow_circuit_breaker_failures counter')
                metrics.append(f'optiflow_circuit_breaker_failures{{name="{name}"}} {breaker.total_failures}')

        except Exception as e:
            logger.debug(f"Could not get circuit breaker metrics: {e}")

        return metrics

    def _websocket_metrics(self) -> List[str]:
        """Export WebSocket metrics."""
        metrics = []

        try:
            from app.core.websocket_pool import get_websocket_pool

            pool = get_websocket_pool()
            stats = pool.get_stats()

            metrics.append('# HELP optiflow_websocket_connections Active WebSocket connections')
            metrics.append('# TYPE optiflow_websocket_connections gauge')
            metrics.append(f'optiflow_websocket_connections {stats["active_connections"]}')

            metrics.append('# HELP optiflow_websocket_users Total users with connections')
            metrics.append('# TYPE optiflow_websocket_users gauge')
            metrics.append(f'optiflow_websocket_users {stats["total_users"]}')

            metrics.append('# HELP optiflow_websocket_messages_sent_total Total messages sent')
            metrics.append('# TYPE optiflow_websocket_messages_sent_total counter')
            metrics.append(f'optiflow_websocket_messages_sent_total {stats["metrics"]["total_messages_sent"]}')

        except Exception as e:
            logger.debug(f"Could not get WebSocket metrics: {e}")

        return metrics

    def _business_metrics(self) -> List[str]:
        """Export business-level metrics."""
        metrics = []

        # These would come from database queries
        # For now, returning structure
        metrics.append('# HELP optiflow_active_alarms Active alarms count')
        metrics.append('# TYPE optiflow_active_alarms gauge')
        metrics.append('optiflow_active_alarms{severity="critical"} 0')
        metrics.append('optiflow_active_alarms{severity="high"} 0')
        metrics.append('optiflow_active_alarms{severity="medium"} 0')

        metrics.append('# HELP optiflow_total_assets Total assets in system')
        metrics.append('# TYPE optiflow_total_assets gauge')
        metrics.append('optiflow_total_assets 0')

        metrics.append('# HELP optiflow_active_users Active users in last hour')
        metrics.append('# TYPE optiflow_active_users gauge')
        metrics.append('optiflow_active_users 0')

        return metrics


# Singleton instance
_exporter: PrometheusExporter = None


def get_prometheus_exporter() -> PrometheusExporter:
    """Get Prometheus exporter instance."""
    global _exporter

    if _exporter is None:
        _exporter = PrometheusExporter()

    return _exporter
