"""
OptiFlow Gateway - Event-Driven Data Collection Service
========================================================

Main entry point for gateway with Kafka-based architecture.

This version uses Protocol Adapters that publish directly to Kafka,
replacing the HTTP-based polling approach.

Architecture:
  PLCs/Devices → Protocol Adapters → Kafka → InfluxDB Consumer → InfluxDB
                                   ↓
                         Alarm Evaluator → Kafka (alarm_events) → Backend
"""

import asyncio
import signal
import logging
from typing import Optional
from pathlib import Path

from app.core.logger import logger
from app.core.config import settings
from app.services.protocol_manager import ProtocolManager
from app.services.config_sync import init_config_sync, get_config_sync
from app.services.alarm_evaluator import get_alarm_evaluator, AlarmEvaluatorService
from app.services.kafka_producer import get_kafka_producer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class KafkaGateway:
    """
    Kafka-based gateway application

    Uses Protocol Manager to handle multiple protocol adapters
    that publish directly to Kafka.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize gateway

        Args:
            config_path: Path to adapter configuration JSON file
        """
        self.running = False
        self.config_path = config_path or "/app/config/adapters_config.json"

        # Protocol Manager
        self.protocol_manager: Optional[ProtocolManager] = None

        # Config Sync Service
        self.config_sync = None

        # Alarm Evaluator
        self.alarm_evaluator: Optional[AlarmEvaluatorService] = None

        # Kafka Producer (for alarms - separate from raw_tags producer)
        self.alarm_kafka_producer = None

        # Health monitoring
        self._stats_task: Optional[asyncio.Task] = None
        self._stats_interval = 60  # seconds

    async def initialize(self):
        """Initialize gateway components"""
        global protocol_manager

        try:
            logger.info("=" * 70)
            logger.info("  🚀 OptiFlow Gateway Starting (Kafka Event-Driven Architecture)")
            logger.info("=" * 70)
            logger.info(f"  Gateway ID: {settings.GATEWAY_ID}")
            logger.info(f"  Gateway Name: {settings.GATEWAY_NAME}")
            logger.info(f"  Config Path: {self.config_path}")
            logger.info(f"  Kafka Servers: {getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')}")
            logger.info("=" * 70)

            # Initialize Config Sync Service (Backend → Gateway)
            backend_url = getattr(settings, 'BACKEND_URL', 'http://optiflow-backend:8000')
            backend_api_key = getattr(settings, 'BACKEND_API_KEY', None)
            sync_interval = getattr(settings, 'CONFIG_SYNC_INTERVAL', 60)

            logger.info("🔄 Initializing Config Sync Service...")
            logger.info(f"   Backend URL: {backend_url}")
            logger.info(f"   Sync Interval: {sync_interval}s")

            self.config_sync = init_config_sync(
                backend_url=backend_url,
                api_key=backend_api_key,
                sync_interval_seconds=sync_interval
            )
            logger.info("✅ Config Sync Service initialized")

            # Initialize Protocol Manager
            logger.info("🔧 Initializing Protocol Manager...")
            self.protocol_manager = ProtocolManager(config_path=self.config_path)
            protocol_manager = self.protocol_manager  # Export for API access

            # Load adapter configurations
            config_file = Path(self.config_path)
            if config_file.exists():
                logger.info(f"📖 Loading adapter configuration from: {self.config_path}")
                loaded_count = await self.protocol_manager.load_config()
                logger.info(f"✅ Loaded {loaded_count} protocol adapters from configuration")
            else:
                logger.warning(f"⚠️  Configuration file not found: {self.config_path}")
                logger.warning("⚠️  Gateway will start with no adapters")
                logger.info("💡 You can add adapters programmatically or create a config file")

            # Initialize separate Kafka Producer for alarm events
            # NOTE: This is a separate producer from the one used for raw_tags
            kafka_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'kafka-1:9092,kafka-2:9093,kafka-3:9096')
            logger.info("📡 Initializing Kafka Producer for alarm events...")
            from app.services.kafka_producer import KafkaProducerService
            self.alarm_kafka_producer = KafkaProducerService(
                bootstrap_servers=kafka_servers,
                topic='alarm_events'
            )
            await self.alarm_kafka_producer.start()
            logger.info("✅ Kafka Producer for alarms initialized (topic: alarm_events)")

            # Initialize Alarm Evaluator with its own producer
            logger.info("🚨 Initializing Alarm Evaluator...")
            self.alarm_evaluator = get_alarm_evaluator(
                gateway_id=settings.GATEWAY_ID,
                kafka_producer=self.alarm_kafka_producer,
                config_path="/app/config/tags_config.json"
            )
            logger.info("✅ Alarm Evaluator initialized")

            logger.info("=" * 70)
            logger.info("  ✅ Gateway initialized successfully")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"❌ Failed to initialize gateway: {str(e)}", exc_info=True)
            raise

    async def stats_loop(self):
        """Periodic statistics logging"""
        logger.info(f"📊 Starting statistics loop (interval: {self._stats_interval}s)")

        while self.running:
            try:
                await asyncio.sleep(self._stats_interval)

                # Get statistics from all adapters
                stats = self.protocol_manager.get_statistics()

                logger.info("")
                logger.info("=" * 70)
                logger.info("  📊 Gateway Statistics")
                logger.info("=" * 70)
                logger.info(f"  Total Adapters: {stats['total_adapters']}")
                logger.info(f"  Running: {stats['running_adapters']}")
                logger.info(f"  Connected: {stats['connected_adapters']}")
                logger.info("")

                # Show per-adapter stats
                for adapter_id, adapter_stats in stats['adapters'].items():
                    status_icon = "✅" if adapter_stats['running'] else "❌"
                    conn_icon = "🔌" if adapter_stats['connected'] else "⚠️ "

                    logger.info(f"  {status_icon} {adapter_id} ({adapter_stats['protocol_type']})")
                    logger.info(f"     {conn_icon} Connected: {adapter_stats['connected']}")
                    logger.info(f"     📖 Reads: {adapter_stats['read_count']}")
                    logger.info(f"     ❌ Errors: {adapter_stats['error_count']}")

                    if adapter_stats['last_read_time']:
                        logger.info(f"     🕐 Last Read: {adapter_stats['last_read_time']}")
                    logger.info("")

                # Show alarm evaluator stats
                if self.alarm_evaluator:
                    alarm_stats = self.alarm_evaluator.get_statistics()
                    logger.info("  🚨 Alarm Evaluator:")
                    logger.info(f"     Evaluations: {alarm_stats['evaluations']}")
                    logger.info(f"     Active Alarms: {alarm_stats['active_count']}")
                    logger.info(f"     Triggered: {alarm_stats['alarms_triggered']}")
                    logger.info(f"     Cleared: {alarm_stats['alarms_cleared']}")
                    logger.info("")

                logger.info("=" * 70)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in stats loop: {e}", exc_info=True)

    async def start(self):
        """Start gateway operation"""
        try:
            self.running = True

            # Initialize components
            await self.initialize()

            # Start config sync service
            if self.config_sync:
                logger.info("🔄 Starting Config Sync Service...")
                await self.config_sync.start()
                logger.info("✅ Config Sync Service started")

            # Start protocol manager (starts all adapters)
            logger.info("🚀 Starting all protocol adapters...")
            await self.protocol_manager.start_all()

            # Start Alarm Evaluator
            if self.alarm_evaluator:
                logger.info("🚨 Starting Alarm Evaluator...")
                await self.alarm_evaluator.start(
                    protocol_manager=self.protocol_manager,
                    interval_seconds=2.0  # Evaluate every 2 seconds
                )
                logger.info("✅ Alarm Evaluator started")

            # Get initial status
            status = self.protocol_manager.get_status()

            logger.info("")
            logger.info("=" * 70)
            logger.info("  ✅ Gateway is Running")
            logger.info("=" * 70)
            logger.info(f"  Adapters Running: {status['running_adapters']}/{status['total_adapters']}")
            logger.info(f"  Adapters Connected: {status['connected_adapters']}/{status['total_adapters']}")
            logger.info(f"  Health Monitor: {'Active' if status['health_monitor_active'] else 'Inactive'}")
            logger.info(f"  Alarm Evaluator: {'Active' if self.alarm_evaluator else 'Inactive'}")
            logger.info("")
            logger.info("  📡 Architecture:")
            logger.info("     PLCs/Devices → Protocol Adapters → Kafka → InfluxDB Consumer → InfluxDB")
            logger.info("                                      ↓")
            logger.info("                            Alarm Evaluator → Kafka (alarm_events) → Backend")
            logger.info("")
            logger.info("  Press Ctrl+C to stop")
            logger.info("=" * 70)
            logger.info("")

            # Start background tasks
            self._stats_task = asyncio.create_task(self.stats_loop())

            # Wait for tasks
            await asyncio.gather(
                self._stats_task,
                return_exceptions=True
            )

        except Exception as e:
            logger.error(f"❌ Gateway error: {str(e)}", exc_info=True)
            raise

    async def stop(self):
        """Stop gateway operation"""
        logger.info("")
        logger.info("=" * 70)
        logger.info("  🛑 Gateway Shutting Down...")
        logger.info("=" * 70)

        self.running = False

        # Cancel stats task
        if self._stats_task:
            self._stats_task.cancel()
            try:
                await self._stats_task
            except asyncio.CancelledError:
                pass

        # Stop alarm evaluator
        if self.alarm_evaluator:
            logger.info("🛑 Stopping Alarm Evaluator...")
            await self.alarm_evaluator.stop()

        # Stop Kafka producer for alarms
        if self.alarm_kafka_producer:
            logger.info("🛑 Stopping Kafka Producer for alarms...")
            await self.alarm_kafka_producer.stop()

        # Stop config sync service
        if self.config_sync:
            logger.info("🛑 Stopping Config Sync Service...")
            await self.config_sync.stop()

        # Stop protocol manager (stops all adapters)
        if self.protocol_manager:
            logger.info("🛑 Stopping all protocol adapters...")
            await self.protocol_manager.stop_all()

        # Final statistics
        if self.protocol_manager:
            final_stats = self.protocol_manager.get_statistics()

            logger.info("")
            logger.info("  📊 Final Statistics:")
            for adapter_id, stats in final_stats['adapters'].items():
                logger.info(f"     {adapter_id}: {stats['read_count']} reads, {stats['error_count']} errors")

        logger.info("")
        logger.info("=" * 70)
        logger.info("  ✅ Gateway Shutdown Complete")
        logger.info("=" * 70)


# Global gateway instance and protocol manager (for API access)
gateway: Optional[KafkaGateway] = None
protocol_manager: Optional['ProtocolManager'] = None


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    if gateway:
        asyncio.create_task(gateway.stop())


async def main():
    """Main entry point"""
    global gateway

    # Get config path from environment or use default
    import os
    config_path = os.getenv('GATEWAY_CONFIG_PATH', '/app/config/adapters_config.json')

    # Create gateway instance
    gateway = KafkaGateway(config_path=config_path)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await gateway.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        await gateway.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
