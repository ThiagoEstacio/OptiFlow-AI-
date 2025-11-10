"""
Gateway Prometheus Metrics Service
===================================

Serviço de métricas específico para o Gateway IoT
Monitora devices, protocolos, tags e comunicação

Autor: OptiFlow AI Team
Data: 2025-11-10
"""

from prometheus_client import Counter, Gauge, Histogram, Info, CollectorRegistry
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class GatewayMetrics:
    """
    Gerenciador de métricas Prometheus para Gateway IoT
    
    Métricas específicas:
    - Devices: conectados por protocolo, status de conexão
    - Tags: leituras/s, qualidade, erros
    - Protocolos: OPC-UA, Modbus, MQTT performance
    - Buffer: tamanho, operações
    - Comunicação: latência, timeouts, reconexões
    """
    
    def __init__(self, gateway_id: str = "gateway-01"):
        """
        Inicializa métricas do Gateway
        
        Args:
            gateway_id: Identificador único do gateway
        """
        self.gateway_id = gateway_id
        self.registry = CollectorRegistry()
        
        # ====================================================================
        # GATEWAY INFO
        # ====================================================================
        self.gateway_info = Info(
            'gateway_info',
            'Gateway information',
            registry=self.registry
        )
        
        # ====================================================================
        # DEVICE METRICS
        # ====================================================================
        self.devices_connected = Gauge(
            'gateway_devices_connected',
            'Number of connected devices',
            ['protocol', 'gateway_id'],
            registry=self.registry
        )
        
        self.device_connection_status = Gauge(
            'gateway_device_connection_status',
            'Device connection status (1=connected, 0=disconnected)',
            ['device_id', 'protocol', 'gateway_id'],
            registry=self.registry
        )
        
        self.device_connection_attempts_total = Counter(
            'gateway_device_connection_attempts_total',
            'Total device connection attempts',
            ['device_id', 'protocol', 'success', 'gateway_id'],
            registry=self.registry
        )
        
        self.device_reconnections_total = Counter(
            'gateway_device_reconnections_total',
            'Total device reconnections',
            ['device_id', 'protocol', 'gateway_id'],
            registry=self.registry
        )
        
        # ====================================================================
        # TAG METRICS
        # ====================================================================
        self.tags_total = Gauge(
            'gateway_tags_total',
            'Total number of configured tags',
            ['device_id', 'gateway_id'],
            registry=self.registry
        )
        
        self.tags_read_total = Counter(
            'gateway_tags_read_total',
            'Total tags read',
            ['device_id', 'protocol', 'quality', 'gateway_id'],
            registry=self.registry
        )
        
        self.tags_read_duration_seconds = Histogram(
            'gateway_tags_read_duration_seconds',
            'Tag read operation latency',
            ['device_id', 'protocol', 'gateway_id'],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
            registry=self.registry
        )
        
        self.tag_read_errors_total = Counter(
            'gateway_tag_read_errors_total',
            'Tag read errors',
            ['device_id', 'protocol', 'error_type', 'gateway_id'],
            registry=self.registry
        )
        
        self.tag_value_changes_total = Counter(
            'gateway_tag_value_changes_total',
            'Total tag value changes detected',
            ['device_id', 'tag_name', 'gateway_id'],
            registry=self.registry
        )
        
        # ====================================================================
        # PROTOCOL SPECIFIC METRICS
        # ====================================================================
        
        # OPC-UA
        self.opcua_sessions_active = Gauge(
            'gateway_opcua_sessions_active',
            'Active OPC-UA sessions',
            ['gateway_id'],
            registry=self.registry
        )
        
        self.opcua_subscriptions_active = Gauge(
            'gateway_opcua_subscriptions_active',
            'Active OPC-UA subscriptions',
            ['device_id', 'gateway_id'],
            registry=self.registry
        )
        
        self.opcua_notifications_received_total = Counter(
            'gateway_opcua_notifications_received_total',
            'OPC-UA data change notifications',
            ['device_id', 'gateway_id'],
            registry=self.registry
        )
        
        # Modbus
        self.modbus_requests_total = Counter(
            'gateway_modbus_requests_total',
            'Total Modbus requests',
            ['device_id', 'function_code', 'success', 'gateway_id'],
            registry=self.registry
        )
        
        self.modbus_response_duration_seconds = Histogram(
            'gateway_modbus_response_duration_seconds',
            'Modbus response time',
            ['device_id', 'function_code', 'gateway_id'],
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
            registry=self.registry
        )
        
        # MQTT
        self.mqtt_messages_received_total = Counter(
            'gateway_mqtt_messages_received_total',
            'MQTT messages received',
            ['topic', 'gateway_id'],
            registry=self.registry
        )
        
        self.mqtt_connection_status = Gauge(
            'gateway_mqtt_connection_status',
            'MQTT broker connection status',
            ['broker', 'gateway_id'],
            registry=self.registry
        )
        
        # ====================================================================
        # BUFFER METRICS
        # ====================================================================
        self.buffer_size = Gauge(
            'gateway_buffer_size',
            'Current buffer size (pending messages)',
            ['gateway_id'],
            registry=self.registry
        )
        
        self.buffer_capacity = Gauge(
            'gateway_buffer_capacity',
            'Buffer capacity (max messages)',
            ['gateway_id'],
            registry=self.registry
        )
        
        self.buffer_writes_total = Counter(
            'gateway_buffer_writes_total',
            'Total buffer write operations',
            ['gateway_id'],
            registry=self.registry
        )
        
        self.buffer_reads_total = Counter(
            'gateway_buffer_reads_total',
            'Total buffer read operations',
            ['gateway_id'],
            registry=self.registry
        )
        
        self.buffer_overflows_total = Counter(
            'gateway_buffer_overflows_total',
            'Buffer overflow events',
            ['gateway_id'],
            registry=self.registry
        )
        
        # ====================================================================
        # BACKEND COMMUNICATION METRICS
        # ====================================================================
        self.backend_requests_total = Counter(
            'gateway_backend_requests_total',
            'Total requests to backend API',
            ['method', 'endpoint', 'status', 'gateway_id'],
            registry=self.registry
        )
        
        self.backend_request_duration_seconds = Histogram(
            'gateway_backend_request_duration_seconds',
            'Backend API request latency',
            ['method', 'endpoint', 'gateway_id'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0),
            registry=self.registry
        )
        
        self.backend_connection_status = Gauge(
            'gateway_backend_connection_status',
            'Backend API connection status (1=connected, 0=disconnected)',
            ['gateway_id'],
            registry=self.registry
        )
        
        self.backend_timeouts_total = Counter(
            'gateway_backend_timeouts_total',
            'Backend API timeout errors',
            ['endpoint', 'gateway_id'],
            registry=self.registry
        )
        
        # ====================================================================
        # DATA FLOW METRICS
        # ====================================================================
        self.data_points_collected_total = Counter(
            'gateway_data_points_collected_total',
            'Total data points collected from devices',
            ['device_id', 'gateway_id'],
            registry=self.registry
        )
        
        self.data_points_sent_total = Counter(
            'gateway_data_points_sent_total',
            'Total data points sent to backend',
            ['gateway_id'],
            registry=self.registry
        )
        
        self.data_points_failed_total = Counter(
            'gateway_data_points_failed_total',
            'Failed data point transmissions',
            ['error_type', 'gateway_id'],
            registry=self.registry
        )
        
        logger.info(f"Gateway metrics initialized for {gateway_id}")
    
    def set_gateway_info(self, version: str, protocols: list):
        """Define informações do gateway"""
        self.gateway_info.info({
            'gateway_id': self.gateway_id,
            'version': version,
            'protocols': ','.join(protocols)
        })
    
    # ========================================================================
    # DEVICE METHODS
    # ========================================================================
    
    def set_devices_connected(self, protocol: str, count: int):
        """Atualiza número de devices conectados por protocolo"""
        self.devices_connected.labels(
            protocol=protocol,
            gateway_id=self.gateway_id
        ).set(count)
    
    def set_device_status(self, device_id: str, protocol: str, connected: bool):
        """Atualiza status de conexão de um device"""
        status = 1 if connected else 0
        self.device_connection_status.labels(
            device_id=device_id,
            protocol=protocol,
            gateway_id=self.gateway_id
        ).set(status)
    
    def track_connection_attempt(self, device_id: str, protocol: str, success: bool):
        """Registra tentativa de conexão"""
        self.device_connection_attempts_total.labels(
            device_id=device_id,
            protocol=protocol,
            success=str(success),
            gateway_id=self.gateway_id
        ).inc()
    
    def track_reconnection(self, device_id: str, protocol: str):
        """Registra reconexão de device"""
        self.device_reconnections_total.labels(
            device_id=device_id,
            protocol=protocol,
            gateway_id=self.gateway_id
        ).inc()
    
    # ========================================================================
    # TAG METHODS
    # ========================================================================
    
    def set_tags_total(self, device_id: str, count: int):
        """Atualiza número total de tags de um device"""
        self.tags_total.labels(
            device_id=device_id,
            gateway_id=self.gateway_id
        ).set(count)
    
    def track_tag_read(self, device_id: str, protocol: str, quality: str, duration: float):
        """Registra leitura de tag"""
        # Incrementar contador
        self.tags_read_total.labels(
            device_id=device_id,
            protocol=protocol,
            quality=quality,
            gateway_id=self.gateway_id
        ).inc()
        
        # Registrar latência
        self.tags_read_duration_seconds.labels(
            device_id=device_id,
            protocol=protocol,
            gateway_id=self.gateway_id
        ).observe(duration)
    
    def track_tag_error(self, device_id: str, protocol: str, error_type: str):
        """Registra erro de leitura de tag"""
        self.tag_read_errors_total.labels(
            device_id=device_id,
            protocol=protocol,
            error_type=error_type,
            gateway_id=self.gateway_id
        ).inc()
    
    def track_tag_value_change(self, device_id: str, tag_name: str):
        """Registra mudança de valor de tag"""
        self.tag_value_changes_total.labels(
            device_id=device_id,
            tag_name=tag_name,
            gateway_id=self.gateway_id
        ).inc()
    
    # ========================================================================
    # OPC-UA METHODS
    # ========================================================================
    
    def set_opcua_sessions(self, count: int):
        """Atualiza número de sessões OPC-UA ativas"""
        self.opcua_sessions_active.labels(gateway_id=self.gateway_id).set(count)
    
    def set_opcua_subscriptions(self, device_id: str, count: int):
        """Atualiza número de subscriptions OPC-UA"""
        self.opcua_subscriptions_active.labels(
            device_id=device_id,
            gateway_id=self.gateway_id
        ).set(count)
    
    def track_opcua_notification(self, device_id: str):
        """Registra notificação OPC-UA recebida"""
        self.opcua_notifications_received_total.labels(
            device_id=device_id,
            gateway_id=self.gateway_id
        ).inc()
    
    # ========================================================================
    # MODBUS METHODS
    # ========================================================================
    
    def track_modbus_request(self, device_id: str, function_code: int, 
                            success: bool, duration: float):
        """Registra request Modbus"""
        self.modbus_requests_total.labels(
            device_id=device_id,
            function_code=str(function_code),
            success=str(success),
            gateway_id=self.gateway_id
        ).inc()
        
        self.modbus_response_duration_seconds.labels(
            device_id=device_id,
            function_code=str(function_code),
            gateway_id=self.gateway_id
        ).observe(duration)
    
    # ========================================================================
    # MQTT METHODS
    # ========================================================================
    
    def track_mqtt_message(self, topic: str):
        """Registra mensagem MQTT recebida"""
        self.mqtt_messages_received_total.labels(
            topic=topic,
            gateway_id=self.gateway_id
        ).inc()
    
    def set_mqtt_status(self, broker: str, connected: bool):
        """Atualiza status de conexão MQTT"""
        status = 1 if connected else 0
        self.mqtt_connection_status.labels(
            broker=broker,
            gateway_id=self.gateway_id
        ).set(status)
    
    # ========================================================================
    # BUFFER METHODS
    # ========================================================================
    
    def set_buffer_size(self, size: int):
        """Atualiza tamanho atual do buffer"""
        self.buffer_size.labels(gateway_id=self.gateway_id).set(size)
    
    def set_buffer_capacity(self, capacity: int):
        """Define capacidade do buffer"""
        self.buffer_capacity.labels(gateway_id=self.gateway_id).set(capacity)
    
    def track_buffer_write(self):
        """Registra escrita no buffer"""
        self.buffer_writes_total.labels(gateway_id=self.gateway_id).inc()
    
    def track_buffer_read(self):
        """Registra leitura do buffer"""
        self.buffer_reads_total.labels(gateway_id=self.gateway_id).inc()
    
    def track_buffer_overflow(self):
        """Registra overflow do buffer"""
        self.buffer_overflows_total.labels(gateway_id=self.gateway_id).inc()
    
    # ========================================================================
    # BACKEND COMMUNICATION METHODS
    # ========================================================================
    
    def track_backend_request(self, method: str, endpoint: str, 
                              status_code: int, duration: float):
        """Registra request ao backend"""
        self.backend_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code),
            gateway_id=self.gateway_id
        ).inc()
        
        self.backend_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
            gateway_id=self.gateway_id
        ).observe(duration)
    
    def set_backend_status(self, connected: bool):
        """Atualiza status de conexão com backend"""
        status = 1 if connected else 0
        self.backend_connection_status.labels(gateway_id=self.gateway_id).set(status)
    
    def track_backend_timeout(self, endpoint: str):
        """Registra timeout de backend"""
        self.backend_timeouts_total.labels(
            endpoint=endpoint,
            gateway_id=self.gateway_id
        ).inc()
    
    # ========================================================================
    # DATA FLOW METHODS
    # ========================================================================
    
    def track_data_collected(self, device_id: str, count: int = 1):
        """Registra dados coletados de device"""
        self.data_points_collected_total.labels(
            device_id=device_id,
            gateway_id=self.gateway_id
        ).inc(count)
    
    def track_data_sent(self, count: int = 1):
        """Registra dados enviados ao backend"""
        self.data_points_sent_total.labels(gateway_id=self.gateway_id).inc(count)
    
    def track_data_failed(self, error_type: str, count: int = 1):
        """Registra falha no envio de dados"""
        self.data_points_failed_total.labels(
            error_type=error_type,
            gateway_id=self.gateway_id
        ).inc(count)
    
    # ========================================================================
    # EXPORT
    # ========================================================================
    
    def export_metrics(self) -> bytes:
        """
        Exporta métricas no formato Prometheus
        
        Returns:
            Métricas serializadas em formato texto
        """
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """Retorna content type para response HTTP"""
        return CONTENT_TYPE_LATEST


# Singleton global
_gateway_metrics_instance: Optional[GatewayMetrics] = None


def get_gateway_metrics() -> GatewayMetrics:
    """
    Retorna instância singleton de GatewayMetrics
    
    Returns:
        Instância de GatewayMetrics
    """
    global _gateway_metrics_instance
    if _gateway_metrics_instance is None:
        _gateway_metrics_instance = GatewayMetrics()
    return _gateway_metrics_instance


def init_gateway_metrics(gateway_id: str = "gateway-01", 
                        version: str = "1.0.0",
                        protocols: list = None):
    """
    Inicializa sistema de métricas do gateway
    
    Args:
        gateway_id: ID do gateway
        version: Versão do gateway
        protocols: Lista de protocolos suportados
    """
    global _gateway_metrics_instance
    _gateway_metrics_instance = GatewayMetrics(gateway_id)
    
    if protocols is None:
        protocols = ["opc_ua", "modbus", "mqtt"]
    
    _gateway_metrics_instance.set_gateway_info(version, protocols)
    logger.info(f"Gateway metrics initialized: {gateway_id} v{version}")
    return _gateway_metrics_instance
