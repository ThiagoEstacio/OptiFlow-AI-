"""
Prometheus Metrics Endpoint (PDCA #20)

Exports metrics in Prometheus format for monitoring.
"""

from fastapi import APIRouter, Response
from typing import Dict, Any
import logging

from app.services.prometheus_exporter import get_prometheus_exporter

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/metrics", response_class=Response)
async def prometheus_metrics():
    """
    Export metrics in Prometheus format.

    **No authentication required** - Prometheus scrapers need public access.

    **Returns**: Metrics in Prometheus exposition format (text/plain)

    **Metrics Categories**:
    - System: CPU, memory, disk, uptime
    - Application: Requests, errors, latency
    - Database: Connection pool, circuit breakers
    - WebSocket: Active connections, messages
    - Business: Alarms, assets, users

    **Example Prometheus Config**:
    ```yaml
    scrape_configs:
      - job_name: 'optiflow'
        scrape_interval: 15s
        static_configs:
          - targets: ['localhost:8000']
        metrics_path: '/api/v1/prometheus/metrics'
    ```

    **Example Grafana Queries**:
    ```promql
    # CPU usage
    optiflow_system_cpu_percent

    # Memory usage
    optiflow_system_memory_percent

    # Connection pool usage
    optiflow_db_pool_usage_percent

    # Active WebSocket connections
    optiflow_websocket_connections

    # Circuit breaker open count
    count(optiflow_circuit_breaker_state == 1)
    ```

    **Use Cases**:
    - Prometheus monitoring
    - Grafana dashboards
    - Alerting rules
    - Capacity planning
    """
    exporter = get_prometheus_exporter()
    metrics = exporter.export_metrics()

    return Response(
        content=metrics,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@router.get("/health")
async def prometheus_health() -> Dict[str, str]:
    """
    Health check for Prometheus scraper.

    **Returns**:
    ```json
    {
        "status": "ok",
        "service": "optiflow-prometheus-exporter"
    }
    ```
    """
    return {
        "status": "ok",
        "service": "optiflow-prometheus-exporter"
    }
