"""
Gateway Service - Industrial Protocol Bridge
============================================

Responsável por:
1. Descobrir tags do PLC (Simulator) via get_all_tags()
2. Ler valores periodicamente (polling)
3. Publicar dados no Kafka (raw_tags topic)
4. Simular protocolo OPC UA / Modbus behavior

Melhorias Implementadas:
- Retry exponencial com circuit breaker
- Buffer local para mensagens falhadas
- Polling adaptativo baseado em tempo de execução
- Métricas Prometheus
- Backpressure para Kafka
- Tag discovery dinâmico
- Transformações de dados (scaling, deadband, validation)

Arquitetura:
    PLC Virtual (Simulator) → Gateway → Kafka → Consumer → InfluxDB
"""

import asyncio
import hashlib
import logging
import time
from collections import deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, Any, List, Deque
from dataclasses import dataclass, field

from prometheus_client import Counter, Gauge, Histogram

from app.services.lightweight_simulator import get_simulator
from app.services.kafka_producer import get_kafka_producer

logger = logging.getLogger(__name__)

# Prometheus Metrics
gateway_messages_published_total = Counter(
    'gateway_messages_published_total',
    'Total number of messages published to Kafka',
    ['status']  # success, failed, buffered
)

gateway_publish_latency_seconds = Histogram(
    'gateway_publish_latency_seconds',
    'Latency of publishing messages to Kafka',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

gateway_buffer_size = Gauge(
    'gateway_buffer_size',
    'Current number of messages in local buffer'
)

gateway_circuit_breaker_state = Gauge(
    'gateway_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=half_open, 2=open)'
)

gateway_circuit_breaker_failures = Counter(
    'gateway_circuit_breaker_failures_total',
    'Total number of circuit breaker failures'
)

gateway_tags_discovered = Gauge(
    'gateway_tags_discovered',
    'Number of tags currently discovered from PLC'
)

gateway_transformations_applied = Counter(
    'gateway_transformations_applied_total',
    'Number of transformations applied to tag values',
    ['type']  # deadband, scaling, unit_conversion, range_validation
)


class CircuitState(Enum):
    """Estados do Circuit Breaker"""
    CLOSED = "closed"  # Funcionando normalmente
    OPEN = "open"      # Muitos erros, não tenta publicar
    HALF_OPEN = "half_open"  # Testando recuperação


@dataclass
class TagConfig:
    """Configuração individual de tag para transformações"""
    name: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    deadband: float = 0.0  # Mudança mínima para publicar
    scaling_factor: float = 1.0
    unit_conversion: Optional[str] = None  # Ex: "F_to_C"
    last_published_value: Optional[float] = None


@dataclass
class GatewayConfig:
    """Configuração do Gateway"""
    poll_interval_s: float = 1.0  # Intervalo de polling (segundos)
    quality_good_threshold: float = 0.0  # Threshold para qualidade "Good"
    source_name: str = "simulator"  # Nome da fonte de dados
    enabled: bool = True  # Gateway ativo
    
    # Retry & Circuit Breaker
    max_retry_attempts: int = 3
    retry_backoff_factor: float = 2.0  # Exponencial: 1s, 2s, 4s
    circuit_breaker_threshold: int = 5  # Erros consecutivos para abrir
    circuit_breaker_timeout_s: float = 30.0  # Tempo em OPEN antes de HALF_OPEN
    
    # Buffer local
    max_buffer_size: int = 10000  # Máximo de mensagens no buffer local
    buffer_flush_interval_s: float = 5.0  # Tenta flush do buffer a cada 5s
    
    # Backpressure
    kafka_buffer_threshold: float = 0.8  # 80% do buffer Kafka = slow down
    rate_limit_msgs_per_sec: Optional[int] = None  # None = sem limite
    
    # Tag discovery
    tag_discovery_interval_s: float = 60.0  # Re-scan tags a cada 60s
    
    # Tags individuais
    tag_configs: Dict[str, TagConfig] = field(default_factory=dict)


class GatewayService:
    """
    Gateway Service - Ponte entre PLC e Kafka
    
    Simula comportamento de gateway industrial (OPC UA / Modbus)
    com melhorias de resiliência e performance
    """
    
    def __init__(self, config: Optional[GatewayConfig] = None):
        # Use provided config or create from settings
        if config is None:
            from app.core.config import settings
            config = GatewayConfig(
                enabled=settings.GATEWAY_ENABLED,
                poll_interval_s=settings.GATEWAY_POLL_INTERVAL_S,
                source_name=settings.GATEWAY_SOURCE_NAME,
                max_buffer_size=settings.GATEWAY_MAX_BUFFER_SIZE,
                circuit_breaker_threshold=settings.GATEWAY_CIRCUIT_BREAKER_THRESHOLD,
                circuit_breaker_timeout_s=settings.GATEWAY_CIRCUIT_BREAKER_TIMEOUT_S,
                max_retry_attempts=settings.GATEWAY_MAX_RETRY_ATTEMPTS,
                retry_backoff_factor=settings.GATEWAY_RETRY_BACKOFF_FACTOR,
                rate_limit_msgs_per_sec=settings.GATEWAY_RATE_LIMIT_MSGS_PER_SEC,
                tag_discovery_interval_s=settings.GATEWAY_TAG_DISCOVERY_INTERVAL_S,
                buffer_flush_interval_s=settings.GATEWAY_BUFFER_FLUSH_INTERVAL_S
            )
        
        self.config = config
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._buffer_flush_task: Optional[asyncio.Task] = None
        self._tag_discovery_task: Optional[asyncio.Task] = None
        self._simulator = get_simulator()
        self._kafka_producer = None
        
        # Buffer local para mensagens falhadas
        self._message_buffer: Deque[Dict[str, Any]] = deque(maxlen=self.config.max_buffer_size)
        
        # Circuit Breaker state
        self._circuit_state = CircuitState.CLOSED
        self._circuit_failures = 0
        self._circuit_opened_at: Optional[datetime] = None
        
        # Estatísticas básicas
        self.tags_discovered = 0
        self.messages_published = 0
        self.last_poll_time: Optional[datetime] = None
        self.errors_count = 0
        
        # Métricas avançadas
        self.publish_latencies_ms: List[float] = []
        self.kafka_connection_status = "unknown"
        self.last_error: Optional[str] = None
        self.buffer_size_current = 0
        self.messages_buffered = 0
        self.messages_from_buffer = 0
        self.circuit_breaker_opens = 0
        self.tags_metadata: Dict[str, TagConfig] = {}
        
        # Rate limiting
        self._last_publish_time = time.time()
        self._publish_count_in_window = 0
        
        logger.info(f"🔌 Gateway Service initialized (poll_interval={self.config.poll_interval_s}s, circuit_breaker=enabled)")
    
    async def start(self):
        """Inicia o Gateway Service"""
        if self.running:
            logger.warning("⚠️  Gateway already running")
            return
        
        self.running = True
        
        # Obtém Kafka producer
        self._kafka_producer = get_kafka_producer()
        
        # Inicia tasks
        self._task = asyncio.create_task(self._polling_loop())
        self._buffer_flush_task = asyncio.create_task(self._buffer_flush_loop())
        self._tag_discovery_task = asyncio.create_task(self._tag_discovery_loop())
        
        logger.info("▶️  Gateway Service started (polling + buffer flush + tag discovery)")
    
    async def stop(self):
        """Para o Gateway Service"""
        if not self.running:
            return
        
        self.running = False
        
        # Cancela tasks
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._buffer_flush_task:
            self._buffer_flush_task.cancel()
            try:
                await self._buffer_flush_task
            except asyncio.CancelledError:
                pass
        
        if self._tag_discovery_task:
            self._tag_discovery_task.cancel()
            try:
                await self._tag_discovery_task
            except asyncio.CancelledError:
                pass
        
        logger.info("⏹️  Gateway Service stopped")
    
    async def _polling_loop(self):
        """Loop principal de polling com timing adaptativo"""
        logger.info("🔄 Gateway polling loop started")
        
        try:
            while self.running:
                loop_start = time.time()
                
                try:
                    # Polling e publicação
                    await self._poll_and_publish()
                    
                    # Calcula sleep adaptativo
                    loop_duration = time.time() - loop_start
                    sleep_time = max(0, self.config.poll_interval_s - loop_duration)
                    
                    if loop_duration > self.config.poll_interval_s:
                        logger.warning(f"⚠️  Polling took {loop_duration:.2f}s, exceeds interval {self.config.poll_interval_s}s")
                    
                    await asyncio.sleep(sleep_time)
                
                except asyncio.CancelledError:
                    break
                
                except Exception as e:
                    self.errors_count += 1
                    logger.error(f"❌ Error in polling loop: {e}", exc_info=True)
                    await asyncio.sleep(1)  # Backoff em caso de erro
        
        finally:
            logger.info("🔄 Gateway polling loop stopped")
    
    async def _poll_and_publish(self):
        """Poll tags do PLC e publica no Kafka com retry e circuit breaker"""
        
        # 1. Verifica circuit breaker
        if not self._check_circuit_breaker():
            return
        
        # 2. Descobre/lê todas as tags do PLC
        tags_data = self._simulator.get_all_tags()
        
        if not tags_data:
            logger.warning("⚠️  No tags discovered from PLC")
            return
        
        self.tags_discovered = len(tags_data)
        self.last_poll_time = datetime.utcnow()
        
        # 3. Publica cada tag no Kafka com transformações
        timestamp = self.last_poll_time.isoformat()
        
        for tag_name, raw_value in tags_data.items():
            # Aplica transformações (deadband, scaling, validation)
            processed_value = self._apply_transformations(tag_name, raw_value)
            
            if processed_value is None:
                continue  # Skip por deadband ou validação
            
            # Constrói mensagem Kafka
            tag_data = {
                "tag_id": tag_name,
                "name": tag_name,
                "value": processed_value,
                "quality": "Good",
                "timestamp": timestamp,
                "source": self.config.source_name,
                "message_id": self._generate_message_id(tag_name, timestamp)  # Para deduplicação
            }
            
            # Tenta publicar com retry
            await self._publish_with_retry(tag_data)
    
    async def _publish_with_retry(self, tag_data: Dict[str, Any], retry_count: int = 0):
        """Publica mensagem com retry exponencial"""
        if not self._kafka_producer or not self._kafka_producer.enabled:
            self._add_to_buffer(tag_data)
            return
        
        # Backpressure: verifica rate limiting
        if not self._check_rate_limit():
            self._add_to_buffer(tag_data)
            return
        
        try:
            publish_start = time.time()
            
            # Tenta publicar
            success = await self._kafka_producer.publish_tag(tag_data)
            
            if success:
                # Sucesso: registra latência e reseta circuit breaker
                latency_ms = (time.time() - publish_start) * 1000
                self.publish_latencies_ms.append(latency_ms)
                if len(self.publish_latencies_ms) > 1000:
                    self.publish_latencies_ms = self.publish_latencies_ms[-1000:]
                
                self.messages_published += 1
                self._circuit_failures = 0
                self.kafka_connection_status = "connected"
                
                # Prometheus metrics
                gateway_messages_published_total.labels(status='success').inc()
                gateway_publish_latency_seconds.observe(latency_ms / 1000.0)
                
                if self._circuit_state == CircuitState.HALF_OPEN:
                    logger.info("✅ Circuit breaker recovered: HALF_OPEN → CLOSED")
                    self._circuit_state = CircuitState.CLOSED
                    gateway_circuit_breaker_state.set(0)  # CLOSED
            else:
                raise Exception("Kafka publish returned False")
        
        except Exception as e:
            self.errors_count += 1
            self._circuit_failures += 1
            self.last_error = str(e)
            
            # Prometheus metrics
            gateway_messages_published_total.labels(status='failed').inc()
            gateway_circuit_breaker_failures.inc()
            
            # Retry com backoff exponencial
            if retry_count < self.config.max_retry_attempts:
                backoff = self.config.retry_backoff_factor ** retry_count
                logger.warning(f"⚠️  Retry {retry_count + 1}/{self.config.max_retry_attempts} in {backoff}s for {tag_data['tag_id']}")
                await asyncio.sleep(backoff)
                await self._publish_with_retry(tag_data, retry_count + 1)
            else:
                # Falhou todas as tentativas: adiciona ao buffer local
                logger.error(f"❌ Failed to publish {tag_data['tag_id']} after {self.config.max_retry_attempts} retries, buffering")
                self._add_to_buffer(tag_data)
                
                # Atualiza circuit breaker
                if self._circuit_failures >= self.config.circuit_breaker_threshold:
                    self._open_circuit_breaker()
    
    def _check_circuit_breaker(self) -> bool:
        """Verifica estado do circuit breaker"""
        if self._circuit_state == CircuitState.CLOSED:
            return True
        
        if self._circuit_state == CircuitState.OPEN:
            # Verifica se já passou o timeout
            if self._circuit_opened_at:
                elapsed = (datetime.utcnow() - self._circuit_opened_at).total_seconds()
                if elapsed >= self.config.circuit_breaker_timeout_s:
                    logger.info("🔄 Circuit breaker timeout: OPEN → HALF_OPEN")
                    self._circuit_state = CircuitState.HALF_OPEN
                    gateway_circuit_breaker_state.set(1)  # HALF_OPEN
                    return True
            return False
        
        # HALF_OPEN: permite uma tentativa
        return True
    
    def _open_circuit_breaker(self):
        """Abre o circuit breaker"""
        if self._circuit_state != CircuitState.OPEN:
            logger.error(f"⚠️  Circuit breaker OPENED after {self._circuit_failures} failures")
            self._circuit_state = CircuitState.OPEN
            self._circuit_opened_at = datetime.utcnow()
            self.circuit_breaker_total_opens += 1
            gateway_circuit_breaker_state.set(2)  # OPEN
            self.kafka_connection_status = "disconnected"
    
    def _add_to_buffer(self, message: Dict[str, Any]):
        """Adiciona mensagem ao buffer local"""
        if len(self._message_buffer) >= self.config.max_buffer_size:
            logger.warning(f"⚠️  Buffer full ({self.config.max_buffer_size}), dropping oldest message")
        
        self._message_buffer.append(message)
        self.messages_buffered += 1
        self.buffer_size_current = len(self._message_buffer)
        
        # Prometheus metrics
        gateway_buffer_size.set(self.buffer_size_current)
        gateway_messages_published_total.labels(status='buffered').inc()
    
    def _check_rate_limit(self) -> bool:
        """Verifica rate limiting"""
        if self.config.rate_limit_msgs_per_sec is None:
            return True
        
        now = time.time()
        window_elapsed = now - self._last_publish_time
        
        if window_elapsed >= 1.0:
            # Nova janela de 1 segundo
            self._last_publish_time = now
            self._publish_count_in_window = 0
            return True
        
        if self._publish_count_in_window >= self.config.rate_limit_msgs_per_sec:
            return False  # Rate limit atingido
        
        self._publish_count_in_window += 1
        return True
    
    async def _buffer_flush_loop(self):
        """Loop para tentar flush do buffer local"""
        logger.info("🔄 Buffer flush loop started")
        
        try:
            while self.running:
                await asyncio.sleep(self.config.buffer_flush_interval_s)
                
                if len(self._message_buffer) > 0 and self._circuit_state != CircuitState.OPEN:
                    await self._flush_buffer()
        
        except asyncio.CancelledError:
            pass
        finally:
            logger.info("🔄 Buffer flush loop stopped")
    
    async def _flush_buffer(self):
        """Tenta publicar mensagens do buffer"""
        if not self._kafka_producer or not self._kafka_producer.enabled:
            return
        
        buffer_size = len(self._message_buffer)
        if buffer_size == 0:
            return
        
        logger.info(f"📤 Flushing buffer ({buffer_size} messages)...")
        flushed = 0
        
        while len(self._message_buffer) > 0 and flushed < 100:  # Max 100 por flush
            message = self._message_buffer.popleft()
            
            try:
                success = await self._kafka_producer.publish_tag(message)
                if success:
                    flushed += 1
                    self.messages_from_buffer += 1
                else:
                    # Falhou: recoloca no buffer
                    self._message_buffer.appendleft(message)
                    break
            except Exception as e:
                logger.error(f"❌ Error flushing buffer: {e}")
                self._message_buffer.appendleft(message)
                break
        
        self.buffer_size_current = len(self._message_buffer)
        
        # Prometheus metrics
        gateway_buffer_size.set(self.buffer_size_current)
        
        if flushed > 0:
            logger.info(f"✅ Flushed {flushed} messages from buffer ({len(self._message_buffer)} remaining)")
    
    async def _tag_discovery_loop(self):
        """Loop para re-scan de tags"""
        logger.info("🔄 Tag discovery loop started")
        
        try:
            while self.running:
                await asyncio.sleep(self.config.tag_discovery_interval_s)
                await self._discover_tags()
        
        except asyncio.CancelledError:
            pass
        finally:
            logger.info("🔄 Tag discovery loop stopped")
    
    async def _discover_tags(self):
        """Descobre tags e atualiza metadata"""
        try:
            tags_data = self._simulator.get_all_tags()
            
            # Atualiza metadata para novas tags
            for tag_name in tags_data.keys():
                if tag_name not in self.tags_metadata:
                    # Cria configuração padrão
                    self.tags_metadata[tag_name] = TagConfig(
                        name=tag_name,
                        deadband=0.1,  # 0.1 unidades de mudança mínima
                        scaling_factor=1.0
                    )
                    logger.info(f"🆕 New tag discovered: {tag_name}")
            
            # Prometheus metric
            gateway_tags_discovered.set(len(self.tags_metadata))
        
        except Exception as e:
            logger.error(f"❌ Error discovering tags: {e}")
    
    def _apply_transformations(self, tag_name: str, raw_value: float) -> Optional[float]:
        """Aplica transformações: deadband, scaling, validation"""
        tag_config = self.tags_metadata.get(tag_name)
        
        if tag_config is None:
            # Sem config: retorna valor bruto
            return raw_value
        
        # 1. Deadband: verifica se mudança é significativa
        if tag_config.last_published_value is not None:
            change = abs(raw_value - tag_config.last_published_value)
            if change < tag_config.deadband:
                gateway_transformations_applied.labels(type='deadband').inc()
                return None  # Skip: mudança menor que deadband
        
        # 2. Scaling
        value = raw_value * tag_config.scaling_factor
        if tag_config.scaling_factor != 1.0:
            gateway_transformations_applied.labels(type='scaling').inc()
        
        # 3. Unit conversion (exemplo: °F → °C)
        if tag_config.unit_conversion == "F_to_C":
            value = (value - 32) * 5/9
            gateway_transformations_applied.labels(type='unit_conversion').inc()
        
        # 4. Validação de range
        if tag_config.min_value is not None and value < tag_config.min_value:
            logger.warning(f"⚠️  Value {value} below min {tag_config.min_value} for {tag_name}")
            value = tag_config.min_value
            gateway_transformations_applied.labels(type='range_validation').inc()
        
        if tag_config.max_value is not None and value > tag_config.max_value:
            logger.warning(f"⚠️  Value {value} above max {tag_config.max_value} for {tag_name}")
            value = tag_config.max_value
            gateway_transformations_applied.labels(type='range_validation').inc()
        
        # Atualiza último valor publicado
        tag_config.last_published_value = value
        
        return value
    
    def _generate_message_id(self, tag_name: str, timestamp: str) -> str:
        """Gera ID único para mensagem (para deduplicação no consumer)"""
        unique_str = f"{tag_name}:{timestamp}:{self.config.source_name}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status completo do Gateway com métricas avançadas"""
        avg_latency = sum(self.publish_latencies_ms) / len(self.publish_latencies_ms) if self.publish_latencies_ms else 0
        
        return {
            "running": self.running,
            "config": {
                "poll_interval_s": self.config.poll_interval_s,
                "source_name": self.config.source_name,
                "enabled": self.config.enabled,
                "max_buffer_size": self.config.max_buffer_size,
                "circuit_breaker_threshold": self.config.circuit_breaker_threshold
            },
            "statistics": {
                "tags_discovered": self.tags_discovered,
                "messages_published": self.messages_published,
                "messages_buffered": self.messages_buffered,
                "messages_from_buffer": self.messages_from_buffer,
                "errors_count": self.errors_count,
                "last_poll_time": self.last_poll_time.isoformat() if self.last_poll_time else None
            },
            "performance": {
                "avg_publish_latency_ms": round(avg_latency, 2),
                "buffer_size_current": self.buffer_size_current,
                "kafka_connection_status": self.kafka_connection_status
            },
            "circuit_breaker": {
                "state": self._circuit_state.value,
                "failures_count": self._circuit_failures,
                "total_opens": self.circuit_breaker_opens,
                "opened_at": self._circuit_opened_at.isoformat() if self._circuit_opened_at else None
            },
            "last_error": self.last_error,
            "simulator_running": self._simulator.running if self._simulator else False
        }


# Singleton global
_gateway_instance: Optional[GatewayService] = None


def get_gateway() -> GatewayService:
    """Retorna instância global do Gateway Service"""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = GatewayService()
    return _gateway_instance


# Export singleton instance
gateway_service = get_gateway()
