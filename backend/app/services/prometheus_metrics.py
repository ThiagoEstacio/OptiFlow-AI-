"""
Prometheus Metrics Service
===========================

Serviço centralizado para coleta e exposição de métricas do sistema
Integrado com FastAPI e Prometheus

Autor: OptiFlow AI Team
Data: 2025-11-10
"""

from prometheus_client import Counter, Gauge, Histogram, Info, CollectorRegistry
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Optional
import time
import psutil
import logging

logger = logging.getLogger(__name__)


class PrometheusMetrics:
    """
    Gerenciador centralizado de métricas Prometheus
    
    Métricas disponíveis:
    - HTTP: requests, latency, errors
    - Application: active users, API calls
    - Database: connections, queries, errors
    - Kafka: messages sent, errors
    - InfluxDB: points written, errors
    - System: CPU, memory, disk
    """
    
    def __init__(self, app_name: str = "optiflow"):
        """
        Inicializa métricas Prometheus
        
        Args:
            app_name: Nome da aplicação para prefixo de métricas
        """
        self.app_name = app_name
        self.registry = CollectorRegistry()
        
        # ====================================================================
        # APPLICATION INFO
        # ====================================================================
        self.app_info = Info(
            f'{app_name}_application',
            'Application information',
            registry=self.registry
        )
        
        # ====================================================================
        # HTTP METRICS
        # ====================================================================
        self.http_requests_total = Counter(
            f'{app_name}_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration_seconds = Histogram(
            f'{app_name}_http_request_duration_seconds',
            'HTTP request latency',
            ['method', 'endpoint'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry
        )
        
        self.http_requests_in_progress = Gauge(
            f'{app_name}_http_requests_in_progress',
            'HTTP requests currently in progress',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # ====================================================================
        # APPLICATION METRICS
        # ====================================================================
        self.active_users = Gauge(
            f'{app_name}_active_users',
            'Number of active users',
            registry=self.registry
        )
        
        self.websocket_connections = Gauge(
            f'{app_name}_websocket_connections',
            'Active WebSocket connections',
            registry=self.registry
        )
        
        # ====================================================================
        # DATABASE METRICS
        # ====================================================================
        self.db_connections_active = Gauge(
            f'{app_name}_db_connections_active',
            'Active database connections',
            ['database'],
            registry=self.registry
        )
        
        self.db_queries_total = Counter(
            f'{app_name}_db_queries_total',
            'Total database queries',
            ['database', 'operation'],
            registry=self.registry
        )
        
        self.db_query_duration_seconds = Histogram(
            f'{app_name}_db_query_duration_seconds',
            'Database query latency',
            ['database', 'operation'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0),
            registry=self.registry
        )
        
        self.db_errors_total = Counter(
            f'{app_name}_db_errors_total',
            'Database errors',
            ['database', 'error_type'],
            registry=self.registry
        )
        
        # ====================================================================
        # KAFKA METRICS
        # ====================================================================
        self.kafka_messages_sent_total = Counter(
            f'{app_name}_kafka_messages_sent_total',
            'Total Kafka messages sent',
            ['topic'],
            registry=self.registry
        )
        
        self.kafka_messages_failed_total = Counter(
            f'{app_name}_kafka_messages_failed_total',
            'Failed Kafka messages',
            ['topic', 'error_type'],
            registry=self.registry
        )
        
        self.kafka_producer_queue_size = Gauge(
            f'{app_name}_kafka_producer_queue_size',
            'Kafka producer queue size',
            registry=self.registry
        )
        
        # ====================================================================
        # INFLUXDB METRICS
        # ====================================================================
        self.influxdb_points_written_total = Counter(
            f'{app_name}_influxdb_points_written_total',
            'Total InfluxDB points written',
            ['bucket'],
            registry=self.registry
        )
        
        self.influxdb_write_errors_total = Counter(
            f'{app_name}_influxdb_write_errors_total',
            'InfluxDB write errors',
            ['bucket', 'error_type'],
            registry=self.registry
        )
        
        self.influxdb_write_duration_seconds = Histogram(
            f'{app_name}_influxdb_write_duration_seconds',
            'InfluxDB write latency',
            ['bucket'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5),
            registry=self.registry
        )
        
        # ====================================================================
        # OPC-UA / DEVICE METRICS
        # ====================================================================
        self.devices_connected = Gauge(
            f'{app_name}_devices_connected',
            'Number of connected devices',
            ['protocol'],
            registry=self.registry
        )
        
        self.tags_total = Gauge(
            f'{app_name}_tags_total',
            'Total number of tags configured',
            ['device'],
            registry=self.registry
        )
        
        self.tags_read_total = Counter(
            f'{app_name}_tags_read_total',
            'Total tags read',
            ['device', 'quality'],
            registry=self.registry
        )
        
        self.tag_read_errors_total = Counter(
            f'{app_name}_tag_read_errors_total',
            'Tag read errors',
            ['device', 'error_type'],
            registry=self.registry
        )
        
        # ====================================================================
        # ALARM METRICS
        # ====================================================================
        self.alarms_active = Gauge(
            f'{app_name}_alarms_active',
            'Active alarms',
            ['severity'],
            registry=self.registry
        )
        
        self.alarms_total = Counter(
            f'{app_name}_alarms_total',
            'Total alarms triggered',
            ['severity', 'equipment'],
            registry=self.registry
        )
        
        # ====================================================================
        # SYSTEM METRICS
        # ====================================================================
        self.system_cpu_usage = Gauge(
            f'{app_name}_system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            f'{app_name}_system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )
        
        self.system_memory_available = Gauge(
            f'{app_name}_system_memory_available_bytes',
            'System memory available in bytes',
            registry=self.registry
        )
        
        self.system_disk_usage = Gauge(
            f'{app_name}_system_disk_usage_percent',
            'System disk usage percentage',
            ['mount_point'],
            registry=self.registry
        )
        
        logger.info(f"Prometheus metrics initialized for {app_name}")
    
    def set_app_info(self, version: str, environment: str):
        """Define informações da aplicação"""
        self.app_info.info({
            'version': version,
            'environment': environment,
            'app': self.app_name
        })
    
    # ========================================================================
    # HTTP METHODS
    # ========================================================================
    
    def track_request(self, method: str, endpoint: str, status_code: int):
        """Registra request HTTP"""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()
    
    def track_request_duration(self, method: str, endpoint: str, duration: float):
        """Registra duração de request"""
        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def request_in_progress(self, method: str, endpoint: str):
        """Context manager para tracking de requests em progresso"""
        class RequestTracker:
            def __init__(self, gauge, method, endpoint):
                self.gauge = gauge
                self.method = method
                self.endpoint = endpoint
                self.start_time = None
            
            def __enter__(self):
                self.gauge.labels(method=self.method, endpoint=self.endpoint).inc()
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.gauge.labels(method=self.method, endpoint=self.endpoint).dec()
                return False
        
        return RequestTracker(self.http_requests_in_progress, method, endpoint)
    
    # ========================================================================
    # DATABASE METHODS
    # ========================================================================
    
    def track_db_query(self, database: str, operation: str, duration: float):
        """Registra query de database"""
        self.db_queries_total.labels(database=database, operation=operation).inc()
        self.db_query_duration_seconds.labels(
            database=database,
            operation=operation
        ).observe(duration)
    
    def track_db_error(self, database: str, error_type: str):
        """Registra erro de database"""
        self.db_errors_total.labels(database=database, error_type=error_type).inc()
    
    def set_db_connections(self, database: str, count: int):
        """Atualiza número de conexões ativas"""
        self.db_connections_active.labels(database=database).set(count)
    
    # ========================================================================
    # KAFKA METHODS
    # ========================================================================
    
    def track_kafka_message_sent(self, topic: str):
        """Registra mensagem enviada ao Kafka"""
        self.kafka_messages_sent_total.labels(topic=topic).inc()
    
    def track_kafka_message_failed(self, topic: str, error_type: str):
        """Registra falha ao enviar mensagem"""
        self.kafka_messages_failed_total.labels(
            topic=topic,
            error_type=error_type
        ).inc()
    
    def set_kafka_queue_size(self, size: int):
        """Atualiza tamanho da fila do producer"""
        self.kafka_producer_queue_size.set(size)
    
    # ========================================================================
    # INFLUXDB METHODS
    # ========================================================================
    
    def track_influxdb_write(self, bucket: str, points_count: int, duration: float):
        """Registra escrita no InfluxDB"""
        self.influxdb_points_written_total.labels(bucket=bucket).inc(points_count)
        self.influxdb_write_duration_seconds.labels(bucket=bucket).observe(duration)
    
    def track_influxdb_error(self, bucket: str, error_type: str):
        """Registra erro de escrita"""
        self.influxdb_write_errors_total.labels(
            bucket=bucket,
            error_type=error_type
        ).inc()
    
    # ========================================================================
    # DEVICE/TAG METHODS
    # ========================================================================
    
    def set_devices_connected(self, protocol: str, count: int):
        """Atualiza número de devices conectados"""
        self.devices_connected.labels(protocol=protocol).set(count)
    
    def set_tags_total(self, device: str, count: int):
        """Atualiza número total de tags"""
        self.tags_total.labels(device=device).set(count)
    
    def track_tag_read(self, device: str, quality: str):
        """Registra leitura de tag"""
        self.tags_read_total.labels(device=device, quality=quality).inc()
    
    def track_tag_error(self, device: str, error_type: str):
        """Registra erro de leitura de tag"""
        self.tag_read_errors_total.labels(device=device, error_type=error_type).inc()
    
    # ========================================================================
    # ALARM METHODS
    # ========================================================================
    
    def set_active_alarms(self, severity: str, count: int):
        """Atualiza número de alarmes ativos"""
        self.alarms_active.labels(severity=severity).set(count)
    
    def track_alarm_triggered(self, severity: str, equipment: str):
        """Registra alarme disparado"""
        self.alarms_total.labels(severity=severity, equipment=equipment).inc()
    
    # ========================================================================
    # SYSTEM METHODS
    # ========================================================================
    
    def update_system_metrics(self):
        """Atualiza métricas de sistema (CPU, RAM, Disk)"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.system_cpu_usage.set(cpu_percent)
            
            # Memory
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.used)
            self.system_memory_available.set(memory.available)
            
            # Disk
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    self.system_disk_usage.labels(
                        mount_point=partition.mountpoint
                    ).set(usage.percent)
                except (PermissionError, OSError):
                    pass
        
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    # ========================================================================
    # EXPORT
    # ========================================================================
    
    def export_metrics(self) -> bytes:
        """
        Exporta métricas no formato Prometheus
        
        Returns:
            Métricas serializadas em formato texto
        """
        # Atualizar métricas de sistema antes de exportar
        self.update_system_metrics()
        
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """Retorna content type para response HTTP"""
        return CONTENT_TYPE_LATEST


# Singleton global
_metrics_instance: Optional[PrometheusMetrics] = None


def get_metrics() -> PrometheusMetrics:
    """
    Retorna instância singleton de PrometheusMetrics
    
    Returns:
        Instância de PrometheusMetrics
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = PrometheusMetrics()
    return _metrics_instance


def init_metrics(app_name: str = "optiflow", version: str = "1.0.0", environment: str = "development"):
    """
    Inicializa sistema de métricas
    
    Args:
        app_name: Nome da aplicação
        version: Versão da aplicação
        environment: Ambiente (development, staging, production)
    """
    global _metrics_instance
    _metrics_instance = PrometheusMetrics(app_name)
    _metrics_instance.set_app_info(version, environment)
    logger.info(f"Metrics initialized: {app_name} v{version} ({environment})")
    return _metrics_instance
