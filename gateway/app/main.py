"""
OptiFlow Gateway - Data Collection Service
Main entry point for the gateway application
"""
import asyncio
import signal
from typing import Optional

from .core.logger import logger
from .core.config import settings
from .services.backend_client import BackendClient
from .services.buffer import DataBuffer
from .services.device_manager import DeviceManager
from .services.simulator_poller import SimulatorPoller


class Gateway:
    """
    Main gateway application
    """

    def __init__(self):
        """Initialize gateway components"""
        self.running = False
        self.backend_client: Optional[BackendClient] = None
        self.buffer: Optional[DataBuffer] = None
        self.device_manager: Optional[DeviceManager] = None
        self.simulator_poller: Optional[SimulatorPoller] = None

        # Tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._buffer_flush_task: Optional[asyncio.Task] = None
        self._simulator_poll_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize gateway components"""
        try:
            logger.info("=" * 60)
            logger.info("  🚀 OptiFlow Gateway Starting...")
            logger.info("=" * 60)
            logger.info(f"  Gateway ID: {settings.GATEWAY_ID}")
            logger.info(f"  Gateway Name: {settings.GATEWAY_NAME}")
            logger.info(f"  Backend URL: {settings.BACKEND_URL}")
            logger.info("=" * 60)

            # Initialize backend client
            logger.info("Initializing backend client...")
            self.backend_client = BackendClient()
            await self.backend_client.connect()

            # Check backend connectivity
            backend_available = await self.backend_client.health_check()
            if backend_available:
                logger.info("✓ Backend is available")
            else:
                logger.warning("⚠️  Backend is not available (will use buffering)")

            # Initialize buffer
            logger.info("Initializing data buffer...")
            self.buffer = DataBuffer()
            stats = self.buffer.get_stats()
            logger.info(f"  Buffer stats: {stats['unsent']} unsent, {stats['sent']} sent")

            # Initialize device manager
            logger.info("Initializing device manager...")
            self.device_manager = DeviceManager(
                backend_client=self.backend_client,
                buffer=self.buffer
            )

            # Initialize simulator poller
            logger.info("Initializing simulator poller...")
            self.simulator_poller = SimulatorPoller(
                simulator_url=settings.BACKEND_URL,  # Simulator runs on same host as backend
                backend_client=self.backend_client,
                poll_interval_s=1.0  # Poll every second
            )
            await self.simulator_poller.initialize()

            logger.info("=" * 60)
            logger.info("  ✅ Gateway initialized successfully")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Failed to initialize gateway: {str(e)}")
            raise

    async def load_devices(self):
        """
        Load device configurations from backend
        """
        try:
            logger.info("Loading device configurations...")

            # TODO: Implement API endpoint to get gateway devices
            # For now, we'll use a placeholder configuration
            # In production, this would call:
            # devices = await self.backend_client.get_gateway_devices(settings.GATEWAY_ID)

            # Example configuration (replace with backend API call)
            example_devices = [
                # {
                #     "device_id": "plc-001",
                #     "protocol": "opc_ua",
                #     "config": {
                #         "endpoint": "opc.tcp://192.168.1.100:4840",
                #         "security_mode": "None"
                #     },
                #     "tags": [
                #         {
                #             "tag_id": "tag-001",
                #             "tag_name": "Temperature",
                #             "address": "ns=2;s=Temperature"
                #         }
                #     ],
                #     "scan_rate": 1000
                # }
            ]

            # Add devices
            for device_config in example_devices:
                device_id = device_config["device_id"]
                protocol = device_config["protocol"]
                config = device_config["config"]
                tags = device_config.get("tags", [])
                scan_rate = device_config.get("scan_rate", 1000)

                # Add device
                success = await self.device_manager.add_device(device_id, protocol, config)

                if success:
                    # Start collection
                    await self.device_manager.start_collection(device_id, tags, scan_rate)

            logger.info(f"Loaded {len(example_devices)} devices")

        except Exception as e:
            logger.error(f"Failed to load devices: {str(e)}")

    async def health_check_loop(self):
        """Periodic health check loop"""
        interval = settings.HEALTH_CHECK_INTERVAL

        logger.info(f"Starting health check loop (interval: {interval}s)")

        while self.running:
            try:
                # Check backend
                backend_healthy = await self.backend_client.health_check()

                # Check devices
                device_statuses = await self.device_manager.health_check_all()

                # Log results
                healthy_count = sum(1 for healthy in device_statuses.values() if healthy)
                total_count = len(device_statuses)

                logger.info(
                    f"Health check: Backend={'OK' if backend_healthy else 'DOWN'}, "
                    f"Devices={healthy_count}/{total_count}"
                )

                # If backend became available, flush buffer
                if backend_healthy and self.backend_client.is_connected:
                    flushed = await self.device_manager.flush_buffer()
                    if flushed > 0:
                        logger.info(f"Flushed {flushed} buffered points")

                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
                await asyncio.sleep(interval)

    async def buffer_flush_loop(self):
        """Periodic buffer flush loop"""
        interval = 60  # Flush every minute

        logger.info(f"Starting buffer flush loop (interval: {interval}s)")

        while self.running:
            try:
                await asyncio.sleep(interval)

                if self.backend_client.is_connected:
                    flushed = await self.device_manager.flush_buffer()
                    if flushed > 0:
                        logger.info(f"Periodic flush: sent {flushed} buffered points")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Buffer flush error: {str(e)}")

    async def start(self):
        """Start gateway operation"""
        try:
            self.running = True

            # Initialize components
            await self.initialize()

            # Load device configurations
            await self.load_devices()

            # Start background tasks
            self._health_check_task = asyncio.create_task(self.health_check_loop())
            self._buffer_flush_task = asyncio.create_task(self.buffer_flush_loop())
            self._simulator_poll_task = asyncio.create_task(self.simulator_poller.start_polling())

            logger.info("")
            logger.info("=" * 60)
            logger.info("  ✅ Gateway is running")
            logger.info("  📡 Polling simulator → Backend → InfluxDB")
            logger.info("  Press Ctrl+C to stop")
            logger.info("=" * 60)
            logger.info("")

            # Wait for tasks
            await asyncio.gather(
                self._health_check_task,
                self._buffer_flush_task,
                self._simulator_poll_task,
                return_exceptions=True
            )

        except Exception as e:
            logger.error(f"Gateway error: {str(e)}")
            raise

    async def stop(self):
        """Stop gateway operation"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("  🛑 Gateway shutting down...")
        logger.info("=" * 60)

        self.running = False

        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        if self._buffer_flush_task:
            self._buffer_flush_task.cancel()
            try:
                await self._buffer_flush_task
            except asyncio.CancelledError:
                pass

        if self._simulator_poll_task:
            self._simulator_poll_task.cancel()
            try:
                await self._simulator_poll_task
            except asyncio.CancelledError:
                pass

        # Shutdown simulator poller
        if self.simulator_poller:
            await self.simulator_poller.close()

        # Shutdown device manager
        if self.device_manager:
            await self.device_manager.shutdown()

        # Disconnect backend client
        if self.backend_client:
            await self.backend_client.disconnect()

        # Clean up old buffer records
        if self.buffer:
            self.buffer.delete_sent(older_than_days=7)
            stats = self.buffer.get_stats()
            logger.info(f"Final buffer stats: {stats}")

        logger.info("=" * 60)
        logger.info("  ✅ Gateway shutdown complete")
        logger.info("=" * 60)


# Global gateway instance
gateway = Gateway()


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    asyncio.create_task(gateway.stop())


async def main():
    """Main entry point"""
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
