"""
OptiFlow Gateway with HTTP API
================================

Combined entry point that runs:
1. Kafka-based Gateway (protocol adapters publishing to Kafka)
2. HTTP API for configuration and monitoring (port 8080)

This allows edge device configuration through REST API while
maintaining event-driven architecture for data collection.
"""

import asyncio
import signal
import logging
from typing import Optional
import uvicorn
from pathlib import Path

from app.core.logger import logger
from app.main_kafka import KafkaGateway, protocol_manager
from app.api_app import app as fastapi_app


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class GatewayWithAPI:
    """
    Gateway that runs both Kafka adapters and HTTP API server
    """

    def __init__(self, config_path: Optional[str] = None, api_port: int = 8080):
        """
        Initialize gateway with API

        Args:
            config_path: Path to adapter configuration JSON file
            api_port: Port for HTTP API server
        """
        self.config_path = config_path or "/app/config/adapters_config.json"
        self.api_port = api_port

        # Gateway instance
        self.gateway: Optional[KafkaGateway] = None

        # API server
        self.api_server: Optional[uvicorn.Server] = None
        self.api_task: Optional[asyncio.Task] = None

        self.running = False

    async def start_api_server(self):
        """Start FastAPI HTTP server"""
        try:
            logger.info(f"🌐 Starting HTTP API server on port {self.api_port}...")

            # Create uvicorn config
            config = uvicorn.Config(
                app=fastapi_app,
                host="0.0.0.0",
                port=self.api_port,
                log_level="info",
                access_log=True
            )

            # Create server
            self.api_server = uvicorn.Server(config)

            # Start server
            await self.api_server.serve()

        except Exception as e:
            logger.error(f"❌ Failed to start API server: {e}", exc_info=True)
            raise

    async def start(self):
        """Start gateway with API"""
        try:
            self.running = True

            logger.info("")
            logger.info("=" * 70)
            logger.info("  🚀 OptiFlow Gateway with Configuration API")
            logger.info("=" * 70)
            logger.info(f"  Config Path: {self.config_path}")
            logger.info(f"  API Port: {self.api_port}")
            logger.info("=" * 70)
            logger.info("")

            # Create gateway instance
            self.gateway = KafkaGateway(config_path=self.config_path)

            # Initialize gateway (loads config, initializes protocol manager)
            await self.gateway.initialize()

            # Start protocol adapters
            logger.info("🚀 Starting protocol adapters...")
            await self.gateway.protocol_manager.start_all()

            # Get status
            status = self.gateway.protocol_manager.get_status()

            logger.info("")
            logger.info("=" * 70)
            logger.info("  ✅ Gateway Core Running")
            logger.info("=" * 70)
            logger.info(f"  Adapters Running: {status['running_adapters']}/{status['total_adapters']}")
            logger.info(f"  Adapters Connected: {status['connected_adapters']}/{status['total_adapters']}")
            logger.info("=" * 70)
            logger.info("")

            # Start API server in background
            self.api_task = asyncio.create_task(self.start_api_server())

            # Start gateway stats loop
            stats_task = asyncio.create_task(self.gateway.stats_loop())

            logger.info("")
            logger.info("=" * 70)
            logger.info("  ✅ Gateway with API is Running")
            logger.info("=" * 70)
            logger.info(f"  HTTP API: http://0.0.0.0:{self.api_port}")
            logger.info(f"  API Docs: http://0.0.0.0:{self.api_port}/docs")
            logger.info("")
            logger.info("  📡 Architecture:")
            logger.info("     PLCs/Devices → Protocol Adapters → Kafka → InfluxDB")
            logger.info("     Configuration UI → HTTP API → Protocol Manager")
            logger.info("")
            logger.info("  Press Ctrl+C to stop")
            logger.info("=" * 70)
            logger.info("")

            # Wait for tasks
            await asyncio.gather(
                self.api_task,
                stats_task,
                return_exceptions=True
            )

        except Exception as e:
            logger.error(f"❌ Gateway error: {str(e)}", exc_info=True)
            raise

    async def stop(self):
        """Stop gateway and API"""
        logger.info("")
        logger.info("=" * 70)
        logger.info("  🛑 Gateway Shutting Down...")
        logger.info("=" * 70)

        self.running = False

        # Stop API server
        if self.api_server:
            logger.info("  Stopping HTTP API server...")
            self.api_server.should_exit = True

        if self.api_task:
            self.api_task.cancel()
            try:
                await self.api_task
            except asyncio.CancelledError:
                pass

        # Stop gateway
        if self.gateway:
            logger.info("  Stopping protocol adapters...")
            await self.gateway.stop()

        logger.info("")
        logger.info("=" * 70)
        logger.info("  ✅ Gateway Shutdown Complete")
        logger.info("=" * 70)


# Global instance
gateway_with_api: Optional[GatewayWithAPI] = None


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    if gateway_with_api:
        asyncio.create_task(gateway_with_api.stop())


async def main():
    """Main entry point"""
    global gateway_with_api

    # Get config from environment
    import os
    config_path = os.getenv('GATEWAY_CONFIG_PATH', '/app/config/adapters_config.json')
    api_port = int(os.getenv('GATEWAY_API_PORT', '8080'))

    # Create gateway instance
    gateway_with_api = GatewayWithAPI(config_path=config_path, api_port=api_port)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await gateway_with_api.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        await gateway_with_api.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Gateway stopped")
