"""
Gateway Manager

Unified manager for all industrial protocol gateways.
Handles gateway lifecycle, health monitoring, and data collection.
"""

from typing import Dict, List, Optional, Any
import logging
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .base_gateway import BaseGateway, GatewayStatus
from .opcua_gateway import OPCUAGateway
from .modbus_gateway import ModbusGateway
from .siemens_gateway import SiemensGateway
from .rockwell_gateway import RockwellGateway
from app.models.gateway_config import GatewayConfig, GatewayType, GatewayHealthLog

logger = logging.getLogger(__name__)


class GatewayManager:
    """
    Manages multiple industrial protocol gateways.

    Responsibilities:
    - Load gateway configurations from database
    - Create and manage gateway instances
    - Start/stop polling for all gateways
    - Collect health metrics
    - Handle gateway failures and reconnections
    """

    GATEWAY_CLASSES = {
        GatewayType.OPCUA: OPCUAGateway,
        GatewayType.MODBUS_TCP: ModbusGateway,
        GatewayType.SIEMENS_S7: SiemensGateway,
        GatewayType.ROCKWELL_EIP: RockwellGateway,
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.gateways: Dict[str, BaseGateway] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False

    async def load_gateways(self) -> None:
        """Load all enabled gateway configurations from database."""
        try:
            # Query enabled gateway configurations
            result = await self.db.execute(
                select(GatewayConfig).where(GatewayConfig.enabled == True)
            )
            configs = result.scalars().all()

            logger.info(f"Loading {len(configs)} gateway configurations")

            for config in configs:
                try:
                    await self._create_gateway(config)
                except Exception as e:
                    logger.error(f"Failed to create gateway {config.name}: {e}")

            logger.info(f"Successfully loaded {len(self.gateways)} gateways")

        except Exception as e:
            logger.error(f"Error loading gateway configurations: {e}")

    async def _create_gateway(self, config: GatewayConfig) -> None:
        """
        Create a gateway instance from configuration.

        Args:
            config: Gateway configuration from database
        """
        gateway_class = self.GATEWAY_CLASSES.get(config.gateway_type)

        if not gateway_class:
            logger.error(f"Unknown gateway type: {config.gateway_type}")
            return

        # Prepare configuration dict
        gateway_config = {
            'connection_config': config.connection_config,
            'polling_interval_ms': config.polling_interval_ms,
            'max_retries': config.max_retries,
            'base_retry_delay': config.base_retry_delay,
            'max_buffer_size': config.max_buffer_size,
            'tags': [tag.to_dict() for tag in config.tags if tag.enabled],
        }

        # Create gateway instance
        gateway = gateway_class(
            name=config.name,
            config=gateway_config,
            max_buffer_size=config.max_buffer_size
        )

        self.gateways[config.name] = gateway
        logger.info(f"Created gateway: {config.name} ({config.gateway_type.value})")

    async def start_all(self) -> None:
        """Start all gateways and begin polling."""
        if self._running:
            logger.warning("Gateway manager already running")
            return

        logger.info(f"Starting {len(self.gateways)} gateways...")

        # Connect all gateways in parallel
        connect_tasks = []
        for name, gateway in self.gateways.items():
            connect_tasks.append(self._connect_gateway(name, gateway))

        await asyncio.gather(*connect_tasks, return_exceptions=True)

        # Start polling for connected gateways
        for name, gateway in self.gateways.items():
            if gateway.status == GatewayStatus.CONNECTED:
                polling_interval = gateway.config.get('polling_interval_ms', 1000)
                await gateway.start_polling(polling_interval)

        # Start health monitoring
        self._running = True
        self._monitoring_task = asyncio.create_task(self._health_monitoring_loop())

        logger.info("All gateways started")

    async def _connect_gateway(self, name: str, gateway: BaseGateway) -> None:
        """Connect a single gateway with retry logic."""
        try:
            success = await gateway.connect_with_retry()
            if success:
                logger.info(f"Gateway {name} connected successfully")
            else:
                logger.error(f"Gateway {name} failed to connect")
        except Exception as e:
            logger.error(f"Error connecting gateway {name}: {e}")

    async def stop_all(self) -> None:
        """Stop all gateways and cleanup."""
        if not self._running:
            return

        logger.info("Stopping all gateways...")

        self._running = False

        # Stop health monitoring
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        # Stop all gateways in parallel
        stop_tasks = []
        for name, gateway in self.gateways.items():
            stop_tasks.append(self._stop_gateway(name, gateway))

        await asyncio.gather(*stop_tasks, return_exceptions=True)

        logger.info("All gateways stopped")

    async def _stop_gateway(self, name: str, gateway: BaseGateway) -> None:
        """Stop a single gateway."""
        try:
            await gateway.stop_polling()
            await gateway.disconnect()
            logger.info(f"Gateway {name} stopped")
        except Exception as e:
            logger.error(f"Error stopping gateway {name}: {e}")

    async def _health_monitoring_loop(self) -> None:
        """Background task to monitor gateway health."""
        logger.info("Started gateway health monitoring")

        while self._running:
            try:
                # Collect health metrics from all gateways
                for name, gateway in self.gateways.items():
                    try:
                        metrics = gateway.get_health_metrics()

                        # Log health metrics to database
                        health_log = GatewayHealthLog(
                            gateway_name=name,
                            status=metrics['status'],
                            successful_reads=metrics['successful_reads'],
                            failed_reads=metrics['failed_reads'],
                            buffer_size=metrics['buffer_size'],
                            uptime_seconds=metrics['uptime_seconds'],
                            last_error=metrics['last_error'],
                        )

                        self.db.add(health_log)

                        # Check for unhealthy gateways
                        if metrics['status'] in [GatewayStatus.ERROR.value, GatewayStatus.DISCONNECTED.value]:
                            logger.warning(f"Gateway {name} is unhealthy: {metrics['status']}")

                            # Attempt reconnection
                            logger.info(f"Attempting to reconnect gateway {name}...")
                            await gateway.connect_with_retry()

                    except Exception as e:
                        logger.error(f"Error monitoring gateway {name}: {e}")

                # Commit health logs
                await self.db.commit()

            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")

            # Wait before next health check (every 60 seconds)
            await asyncio.sleep(60)

    def get_gateway(self, name: str) -> Optional[BaseGateway]:
        """
        Get gateway instance by name.

        Args:
            name: Gateway name

        Returns:
            Gateway instance or None if not found
        """
        return self.gateways.get(name)

    def get_all_health_metrics(self) -> List[Dict[str, Any]]:
        """
        Get health metrics for all gateways.

        Returns:
            List of health metric dictionaries
        """
        metrics = []
        for name, gateway in self.gateways.items():
            try:
                metrics.append(gateway.get_health_metrics())
            except Exception as e:
                logger.error(f"Error getting metrics for gateway {name}: {e}")

        return metrics

    async def reload_gateway(self, gateway_name: str) -> bool:
        """
        Reload a specific gateway (useful after configuration changes).

        Args:
            gateway_name: Name of gateway to reload

        Returns:
            bool: True if reload successful
        """
        try:
            # Stop existing gateway if running
            if gateway_name in self.gateways:
                gateway = self.gateways[gateway_name]
                await gateway.stop_polling()
                await gateway.disconnect()
                del self.gateways[gateway_name]

            # Load new configuration
            result = await self.db.execute(
                select(GatewayConfig).where(
                    GatewayConfig.name == gateway_name,
                    GatewayConfig.enabled == True
                )
            )
            config = result.scalar_one_or_none()

            if not config:
                logger.error(f"Gateway {gateway_name} not found or disabled")
                return False

            # Create new gateway instance
            await self._create_gateway(config)

            # Connect and start polling
            gateway = self.gateways.get(gateway_name)
            if gateway:
                await gateway.connect_with_retry()
                if gateway.status == GatewayStatus.CONNECTED:
                    polling_interval = gateway.config.get('polling_interval_ms', 1000)
                    await gateway.start_polling(polling_interval)

            logger.info(f"Successfully reloaded gateway {gateway_name}")
            return True

        except Exception as e:
            logger.error(f"Error reloading gateway {gateway_name}: {e}")
            return False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.load_gateways()
        await self.start_all()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_all()
