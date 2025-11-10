"""
OptiFlow Gateway - Event-Driven Data Collection Service
========================================================

Main entry point for gateway with Kafka-based architecture.

This version uses Protocol Adapters that publish directly to Kafka,
replacing the HTTP-based polling approach.

Architecture:
  PLCs/Devices → Protocol Adapters → Kafka → InfluxDB Consumer → InfluxDB
"""

import asyncio
import signal
import logging
from typing import Optional
from pathlib import Path

from app.core.logger import logger
from app.core.config import settings
from app.services.protocol_manager import ProtocolManager

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

        # Health monitoring
        self._stats_task: Optional[asyncio.Task] = None
        self._stats_interval = 60  # seconds

    async def initialize(self):
        """Initialize gateway components"""
        try:
            logger.info("=" * 70)
            logger.info("  🚀 OptiFlow Gateway Starting (Kafka Event-Driven Architecture)")
            logger.info("=" * 70)
            logger.info(f"  Gateway ID: {settings.GATEWAY_ID}")
            logger.info(f"  Gateway Name: {settings.GATEWAY_NAME}")
            logger.info(f"  Config Path: {self.config_path}")
            logger.info(f"  Kafka Servers: {getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')}")
            logger.info("=" * 70)

            # Initialize Protocol Manager
            logger.info("🔧 Initializing Protocol Manager...")
            self.protocol_manager = ProtocolManager(config_path=self.config_path)

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

            # Start protocol manager (starts all adapters)
            logger.info("🚀 Starting all protocol adapters...")
            await self.protocol_manager.start_all()

            # Get initial status
            status = self.protocol_manager.get_status()

            logger.info("")
            logger.info("=" * 70)
            logger.info("  ✅ Gateway is Running")
            logger.info("=" * 70)
            logger.info(f"  Adapters Running: {status['running_adapters']}/{status['total_adapters']}")
            logger.info(f"  Adapters Connected: {status['connected_adapters']}/{status['total_adapters']}")
            logger.info(f"  Health Monitor: {'Active' if status['health_monitor_active'] else 'Inactive'}")
            logger.info("")
            logger.info("  📡 Architecture:")
            logger.info("     PLCs/Devices → Protocol Adapters → Kafka → InfluxDB Consumer → InfluxDB")
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


# Global gateway instance
gateway: Optional[KafkaGateway] = None


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
