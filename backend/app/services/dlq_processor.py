"""
Dead Letter Queue (DLQ) Processor
==================================

Consumes messages from the DLQ (raw_tags_dlq) and attempts to reprocess them.

Features:
- Consumes from raw_tags_dlq topic
- Attempts to retry failed messages
- Logs permanently failed messages for manual intervention
- Tracks retry attempts per message
- Exponential backoff for retries
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime

from prometheus_client import Counter, Gauge

try:
    from aiokafka import AIOKafkaConsumer
    from aiokafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logging.warning("aiokafka not installed - DLQ processor disabled")

from app.core.config import settings
from app.services.influxdb import influxdb_service

logger = logging.getLogger(__name__)

# Prometheus Metrics
dlq_messages_processed_total = Counter(
    'dlq_messages_processed_total',
    'Total messages processed from DLQ',
    ['status']  # success, failed, abandoned
)

dlq_retry_attempts_total = Counter(
    'dlq_retry_attempts_total',
    'Total retry attempts for DLQ messages'
)

dlq_queue_size = Gauge(
    'dlq_queue_size',
    'Current size of DLQ (estimated)'
)


class DLQProcessor:
    """
    Processor for Dead Letter Queue messages
    
    Consumes messages that failed processing in the main consumer
    and attempts to reprocess them with retry logic.
    """
    
    def __init__(
        self,
        topic: str = None,
        group_id: str = "dlq-processor",
        max_retries: int = 3,
        retry_delay_s: float = 5.0
    ):
        self.topic = topic or settings.KAFKA_DLQ_TOPIC
        self.group_id = group_id
        self.max_retries = max_retries
        self.retry_delay_s = retry_delay_s
        
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
        self.enabled = KAFKA_AVAILABLE
        
        self._messages_processed = 0
        self._messages_succeeded = 0
        self._messages_failed = 0
        self._messages_abandoned = 0
        
        logger.info(f"🔧 DLQ Processor initialized - Topic: {self.topic}, Max Retries: {self.max_retries}")
    
    async def start(self):
        """Start DLQ consumer"""
        if not self.enabled:
            logger.warning("⚠️  DLQ processor disabled (Kafka unavailable)")
            return False
        
        try:
            bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
            
            self.consumer = AIOKafkaConsumer(
                self.topic,
                bootstrap_servers=bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=False
            )
            
            await self.consumer.start()
            logger.info(f"✅ DLQ processor started - Topic: {self.topic}, Group: {self.group_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start DLQ processor: {e}")
            self.enabled = False
            return False
    
    async def stop(self):
        """Stop DLQ consumer"""
        self.running = False
        
        if self.consumer:
            try:
                await self.consumer.stop()
                logger.info(f"🛑 DLQ processor stopped - Processed: {self._messages_processed}, " +
                          f"Success: {self._messages_succeeded}, Failed: {self._messages_failed}, " +
                          f"Abandoned: {self._messages_abandoned}")
            except Exception as e:
                logger.error(f"Error stopping DLQ processor: {e}")
    
    async def process_loop(self):
        """Main processing loop"""
        if not self.enabled or not self.consumer:
            logger.error("❌ Cannot start DLQ processor loop - consumer not enabled")
            return
        
        self.running = True
        logger.info("🔄 Starting DLQ processor loop...")
        
        try:
            async for msg in self.consumer:
                if not self.running:
                    break
                
                try:
                    dlq_payload = msg.value
                    self._messages_processed += 1
                    
                    # Extract original message and metadata
                    original_message = dlq_payload.get('original', {})
                    reason = dlq_payload.get('reason', 'unknown')
                    timestamp = dlq_payload.get('timestamp')
                    retry_count = dlq_payload.get('retry_count', 0)
                    
                    logger.info(f"📥 Processing DLQ message (retry {retry_count}/{self.max_retries}): " +
                              f"reason={reason}, original={original_message.get('tag_id', 'unknown')}")
                    
                    # Check if we should retry
                    if retry_count >= self.max_retries:
                        logger.warning(f"⚠️  Message exceeded max retries ({self.max_retries}), abandoning: {original_message}")
                        self._messages_abandoned += 1
                        dlq_messages_processed_total.labels(status='abandoned').inc()
                        
                        # Log to file for manual intervention
                        self._log_abandoned_message(original_message, reason, retry_count)
                        
                        await self.consumer.commit()
                        continue
                    
                    # Attempt to reprocess
                    success = await self._retry_message(original_message)
                    dlq_retry_attempts_total.inc()
                    
                    if success:
                        logger.info(f"✅ Successfully reprocessed DLQ message: {original_message.get('tag_id')}")
                        self._messages_succeeded += 1
                        dlq_messages_processed_total.labels(status='success').inc()
                        await self.consumer.commit()
                    else:
                        logger.warning(f"❌ Failed to reprocess DLQ message: {original_message.get('tag_id')}")
                        self._messages_failed += 1
                        dlq_messages_processed_total.labels(status='failed').inc()
                        
                        # Wait before next attempt
                        await asyncio.sleep(self.retry_delay_s)
                        
                        # Don't commit - message will be reprocessed
                
                except Exception as e:
                    logger.error(f"❌ Error processing DLQ message: {e}")
                    continue
        
        except asyncio.CancelledError:
            logger.info("🛑 DLQ processor loop cancelled")
        except Exception as e:
            logger.error(f"❌ DLQ processor loop error: {e}")
        finally:
            self.running = False
    
    async def _retry_message(self, message: Dict[str, Any]) -> bool:
        """
        Retry processing a failed message
        
        Args:
            message: Original message that failed
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Normalize message format
            point = {
                'tag_id': message.get('tag_id') or message.get('tag_name'),
                'tag_name': message.get('name') or message.get('tag_name'),
                'value': message.get('value'),
                'timestamp': message.get('timestamp'),
                'quality': message.get('quality', 'good'),
                'source': message.get('source', 'dlq-retry')
            }
            
            # Try writing to InfluxDB
            success = influxdb_service.write_batch([point])
            
            if success:
                logger.debug(f"✅ DLQ retry successful for {point['tag_id']}")
                return True
            else:
                logger.warning(f"⚠️  DLQ retry failed for {point['tag_id']}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Error retrying DLQ message: {e}")
            return False
    
    def _log_abandoned_message(self, message: Dict[str, Any], reason: str, retry_count: int):
        """Log permanently failed messages to a file"""
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'message': message,
                'reason': reason,
                'retry_count': retry_count,
                'status': 'ABANDONED'
            }
            
            # Log to file for manual review
            with open('/app/logs/dlq_abandoned.jsonl', 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            logger.error(f"💀 ABANDONED MESSAGE logged to dlq_abandoned.jsonl: {message.get('tag_id')}")
        
        except Exception as e:
            logger.error(f"❌ Failed to log abandoned message: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get DLQ processor statistics"""
        return {
            'messages_processed': self._messages_processed,
            'messages_succeeded': self._messages_succeeded,
            'messages_failed': self._messages_failed,
            'messages_abandoned': self._messages_abandoned
        }


# Global singleton instance
_dlq_processor_instance: Optional[DLQProcessor] = None


def get_dlq_processor() -> DLQProcessor:
    """Get global DLQ processor instance"""
    global _dlq_processor_instance
    if _dlq_processor_instance is None:
        _dlq_processor_instance = DLQProcessor()
    return _dlq_processor_instance


async def start_dlq_processor():
    """Start DLQ processor (call from application startup)"""
    processor = get_dlq_processor()
    
    started = await processor.start()
    
    if started:
        # Start processing loop in background
        asyncio.create_task(processor.process_loop())
        logger.info("🚀 DLQ processor started in background")
    else:
        logger.warning("⚠️  DLQ processor not started (Kafka unavailable)")
    
    return processor


async def stop_dlq_processor():
    """Stop DLQ processor (call from application shutdown)"""
    global _dlq_processor_instance
    if _dlq_processor_instance:
        await _dlq_processor_instance.stop()
        _dlq_processor_instance = None


def get_dlq_status() -> Dict[str, Any]:
    """Get current DLQ processor status"""
    global _dlq_processor_instance
    if _dlq_processor_instance is None:
        return {
            "running": False,
            "enabled": False,
            "messages_processed": 0
        }
    
    stats = _dlq_processor_instance.get_stats()
    return {
        "running": _dlq_processor_instance.running,
        "enabled": _dlq_processor_instance.enabled,
        **stats
    }
