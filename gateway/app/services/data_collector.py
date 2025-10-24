"""
Data Collector Service
Collects data from industrial devices and sends to backend
"""
import asyncio
import logging
from typing import Dict, List
from datetime import datetime

from gateway.app.protocols import OPCUAHandler, ModbusTCPHandler, MQTTHandler

logger = logging.getLogger(__name__)


class DataCollector:
    """
    Manages data collection from multiple devices
    """

    def __init__(self):
        self.devices: Dict[str, Dict] = {}
        self.running = False

    async def add_device(self, device_id: str, protocol: str, config: Dict):
        """
        Add a device to collect data from

        Args:
            device_id: Unique device identifier
            protocol: Protocol type (opcua, modbus_tcp, mqtt)
            config: Protocol-specific configuration
        """
        try:
            handler = None

            if protocol == "opcua":
                handler = OPCUAHandler(
                    endpoint=config.get("endpoint"),
                    security_mode=config.get("security_mode", "None"),
                    username=config.get("username"),
                    password=config.get("password")
                )

            elif protocol == "modbus_tcp":
                handler = ModbusTCPHandler(
                    host=config.get("host"),
                    port=config.get("port", 502),
                    unit_id=config.get("unit_id", 1)
                )

            elif protocol == "mqtt":
                handler = MQTTHandler(
                    broker=config.get("broker"),
                    port=config.get("port", 1883),
                    username=config.get("username"),
                    password=config.get("password")
                )

            if handler:
                connected = await handler.connect()
                if connected:
                    self.devices[device_id] = {
                        "handler": handler,
                        "protocol": protocol,
                        "config": config,
                        "tags": config.get("tags", [])
                    }
                    logger.info(f"Added device {device_id} with protocol {protocol}")
                    return True

        except Exception as e:
            logger.error(f"Error adding device {device_id}: {e}")

        return False

    async def start_collection(self, interval_seconds: int = 5):
        """
        Start collecting data from all devices

        Args:
            interval_seconds: Collection interval in seconds
        """
        self.running = True
        logger.info(f"Starting data collection (interval: {interval_seconds}s)")

        while self.running:
            try:
                # Collect data from all devices
                for device_id, device_info in self.devices.items():
                    await self._collect_device_data(device_id, device_info)

                # Wait for next collection cycle
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                await asyncio.sleep(interval_seconds)

    async def _collect_device_data(self, device_id: str, device_info: Dict):
        """Collect data from a single device"""
        try:
            handler = device_info["handler"]
            protocol = device_info["protocol"]
            tags = device_info["tags"]

            if protocol == "opcua" and handler.is_connected():
                node_ids = [tag["node_id"] for tag in tags]
                data = await handler.read_multiple_nodes(node_ids)

                # Send data to backend (in production, use HTTP client to backend API)
                logger.debug(f"Collected OPC UA data from {device_id}: {data}")

            elif protocol == "modbus_tcp" and handler.is_connected():
                for tag in tags:
                    address = tag.get("address")
                    register_type = tag.get("type", "holding")

                    if register_type == "holding":
                        values = await handler.read_holding_registers(address, 1)
                    elif register_type == "input":
                        values = await handler.read_input_registers(address, 1)

                    if values:
                        logger.debug(f"Collected Modbus data from {device_id} register {address}: {values[0]}")

            elif protocol == "mqtt":
                # MQTT works differently - data comes via subscriptions
                pass

        except Exception as e:
            logger.error(f"Error collecting data from device {device_id}: {e}")

    async def stop_collection(self):
        """Stop data collection"""
        self.running = False
        logger.info("Stopping data collection")

        # Disconnect all devices
        for device_id, device_info in self.devices.items():
            handler = device_info["handler"]
            await handler.disconnect()


# Global data collector instance
collector = DataCollector()
