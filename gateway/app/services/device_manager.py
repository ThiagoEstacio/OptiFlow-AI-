"""
Device Manager - Manages multiple device connections and data collection
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..core.logger import logger
from ..core.base_protocol import BaseProtocolHandler, TagValue
from ..protocols.opcua_handler import OPCUAHandler
from ..protocols.modbus_handler import ModbusHandler
from ..protocols.mqtt_handler import MQTTHandler
from ..protocols.ethernetip_handler import EthernetIPHandler
from ..protocols.s7_handler import S7Handler
from .buffer import DataBuffer
from .backend_client import BackendClient
from .opcua_browser import OPCUABrowser


class DeviceManager:
    """
    Manages multiple industrial devices and their data collection
    """

    def __init__(self, backend_client: BackendClient, buffer: DataBuffer):
        """
        Initialize device manager

        Args:
            backend_client: Backend API client
            buffer: Data buffer for offline storage
        """
        self.backend = backend_client
        self.buffer = buffer

        # Active devices
        self.devices: Dict[str, BaseProtocolHandler] = {}

        # Collection tasks
        self._collection_tasks: Dict[str, asyncio.Task] = {}

        # Protocol handler mapping
        self.protocol_handlers = {
            "opc_ua": OPCUAHandler,
            "modbus": ModbusHandler,
            "mqtt": MQTTHandler,
            "ethernet_ip": EthernetIPHandler,
            "s7": S7Handler,
        }

    async def add_device(self, device_id: str, protocol: str, config: Dict[str, Any]) -> bool:
        """
        Add and connect to a device

        Args:
            device_id: Unique device identifier
            protocol: Protocol type (opc_ua, modbus, mqtt, ethernet_ip, s7)
            config: Device-specific configuration

        Returns:
            True if device added successfully
        """
        try:
            # Check if already exists
            if device_id in self.devices:
                logger.warning(f"Device {device_id} already exists")
                return False

            # Get protocol handler class
            handler_class = self.protocol_handlers.get(protocol.lower())
            if not handler_class:
                logger.error(f"Unknown protocol: {protocol}")
                return False

            # Create handler
            handler = handler_class(device_id=device_id, config=config)

            # Try to connect
            connected = await handler.connect()

            if connected:
                self.devices[device_id] = handler
                logger.info(f"✓ Device {device_id} ({protocol}) added and connected")
                return True
            else:
                logger.error(f"Failed to connect to device {device_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to add device {device_id}: {str(e)}")
            return False

    async def remove_device(self, device_id: str) -> bool:
        """
        Remove and disconnect a device

        Args:
            device_id: Device identifier

        Returns:
            True if removed successfully
        """
        try:
            if device_id not in self.devices:
                logger.warning(f"Device {device_id} not found")
                return False

            # Stop collection task if running
            if device_id in self._collection_tasks:
                task = self._collection_tasks[device_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self._collection_tasks[device_id]

            # Disconnect device
            handler = self.devices[device_id]
            await handler.disconnect()

            # Remove from devices
            del self.devices[device_id]

            logger.info(f"Device {device_id} removed")
            return True

        except Exception as e:
            logger.error(f"Failed to remove device {device_id}: {str(e)}")
            return False

    async def start_collection(self, device_id: str, tags: List[Dict[str, Any]], scan_rate: int = 1000):
        """
        Start data collection for a device

        Args:
            device_id: Device identifier
            tags: List of tag configurations with keys:
                - tag_id: Tag identifier
                - tag_name: Tag name
                - address: Protocol-specific address
                - scan_rate: Optional override scan rate
            scan_rate: Default scan rate in milliseconds
        """
        try:
            if device_id not in self.devices:
                logger.error(f"Device {device_id} not found")
                return

            # Stop existing collection if any
            if device_id in self._collection_tasks:
                await self.stop_collection(device_id)

            # Create and start collection task
            task = asyncio.create_task(
                self._collection_loop(device_id, tags, scan_rate)
            )
            self._collection_tasks[device_id] = task

            logger.info(f"✓ Started data collection for device {device_id} ({len(tags)} tags)")

        except Exception as e:
            logger.error(f"Failed to start collection for {device_id}: {str(e)}")

    async def stop_collection(self, device_id: str):
        """Stop data collection for a device"""
        if device_id in self._collection_tasks:
            task = self._collection_tasks[device_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._collection_tasks[device_id]
            logger.info(f"Stopped data collection for device {device_id}")

    async def _collection_loop(self, device_id: str, tags: List[Dict[str, Any]], scan_rate: int):
        """
        Main collection loop for a device

        Args:
            device_id: Device identifier
            tags: List of tag configurations
            scan_rate: Scan rate in milliseconds
        """
        handler = self.devices[device_id]
        scan_interval = scan_rate / 1000.0  # Convert to seconds

        logger.info(f"Collection loop started for {device_id} (scan rate: {scan_rate}ms)")

        while True:
            try:
                start_time = asyncio.get_event_loop().time()

                # Read all tags
                tag_addresses = [tag["address"] for tag in tags]
                tag_values = await handler.read_tags(tag_addresses)

                # Process results
                data_points = []
                for tag, tag_value in zip(tags, tag_values):
                    if tag_value:
                        # Prepare data point
                        data_point = {
                            "tag_id": tag["tag_id"],
                            "value": tag_value.value,
                            "timestamp": tag_value.timestamp.isoformat(),
                            "quality": tag_value.quality
                        }
                        data_points.append(data_point)

                        # Also buffer the data
                        self.buffer.add(
                            device_id=device_id,
                            tag_id=tag["tag_id"],
                            tag_name=tag.get("tag_name", tag["address"]),
                            value=tag_value.value,
                            quality=tag_value.quality,
                            timestamp=tag_value.timestamp
                        )

                # Send to backend
                if data_points:
                    if self.backend.is_connected:
                        success = await self.backend.send_timeseries_batch(data_points)
                        if success:
                            logger.debug(f"Sent {len(data_points)} points from {device_id}")
                    else:
                        logger.debug(f"Backend offline, {len(data_points)} points buffered")

                # Calculate sleep time to maintain scan rate
                elapsed = asyncio.get_event_loop().time() - start_time
                sleep_time = max(0, scan_interval - elapsed)

                await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                logger.info(f"Collection loop cancelled for {device_id}")
                raise

            except Exception as e:
                logger.error(f"Error in collection loop for {device_id}: {str(e)}")
                await asyncio.sleep(scan_interval)

    async def flush_buffer(self):
        """
        Flush buffered data to backend

        Returns:
            Number of records sent
        """
        try:
            # Get unsent data
            unsent_data = self.buffer.get_unsent(limit=1000)

            if not unsent_data:
                return 0

            # Convert to data points format
            data_points = []
            record_ids = []

            for record in unsent_data:
                data_points.append({
                    "tag_id": record["tag_id"],
                    "value": record["value"],
                    "timestamp": record["timestamp"],
                    "quality": record["quality"]
                })
                record_ids.append(record["id"])

            # Send to backend
            success = await self.backend.send_timeseries_batch(data_points)

            if success:
                # Mark as sent
                self.buffer.mark_sent(record_ids)
                logger.info(f"✓ Flushed {len(data_points)} buffered points to backend")
                return len(data_points)
            else:
                logger.warning("Failed to flush buffer to backend")
                return 0

        except Exception as e:
            logger.error(f"Failed to flush buffer: {str(e)}")
            return 0

    async def health_check_all(self) -> Dict[str, bool]:
        """
        Check health of all devices

        Returns:
            Dictionary of device_id -> health status
        """
        results = {}

        for device_id, handler in self.devices.items():
            try:
                healthy = await handler.health_check()
                results[device_id] = healthy
            except Exception as e:
                logger.error(f"Health check failed for {device_id}: {str(e)}")
                results[device_id] = False

        return results

    def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific device"""
        if device_id not in self.devices:
            return None

        handler = self.devices[device_id]
        status = handler.get_status()

        return {
            "device_id": device_id,
            "connected": status.connected,
            "last_success": status.last_success.isoformat() if status.last_success else None,
            "last_error": status.last_error,
            "error_count": status.error_count,
            "collecting": device_id in self._collection_tasks
        }

    def get_all_statuses(self) -> List[Dict[str, Any]]:
        """Get status of all devices"""
        return [
            self.get_device_status(device_id)
            for device_id in self.devices.keys()
        ]

    async def discover_opcua_tags(
        self,
        endpoint: str,
        namespace_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Discover available tags from an OPC-UA server
        Similar to KEPServerEX tag discovery

        Args:
            endpoint: OPC-UA server endpoint
            namespace_index: Optional namespace index to filter by

        Returns:
            Dictionary with discovered tags and namespaces
        """
        browser = OPCUABrowser(endpoint)

        try:
            logger.info(f"Starting OPC-UA discovery for {endpoint}")

            # Connect to server
            connected = await browser.connect()
            if not connected:
                return {
                    "success": False,
                    "error": "Failed to connect to OPC-UA server"
                }

            # Get namespaces
            namespaces = await browser.get_namespaces()
            logger.info(f"Found {len(namespaces)} namespaces")

            # Discover tags
            namespace_filter = [namespace_index] if namespace_index is not None else None
            tags = await browser.discover_all_tags(namespace_filter=namespace_filter)

            logger.info(f"✓ Discovered {len(tags)} tags from {endpoint}")

            return {
                "success": True,
                "endpoint": endpoint,
                "namespaces": namespaces,
                "tags": tags,
                "tag_count": len(tags)
            }

        except Exception as e:
            logger.error(f"OPC-UA discovery failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

        finally:
            await browser.disconnect()

    async def add_opcua_device_with_discovery(
        self,
        device_id: str,
        endpoint: str,
        namespace_index: Optional[int] = None,
        tag_filter: Optional[str] = None,
        scan_rate: int = 1000
    ) -> Dict[str, Any]:
        """
        Add OPC-UA device with automatic tag discovery

        Args:
            device_id: Unique device identifier
            endpoint: OPC-UA server endpoint
            namespace_index: Optional namespace to filter tags
            tag_filter: Optional search term to filter tags by name
            scan_rate: Data collection scan rate in milliseconds

        Returns:
            Dictionary with results
        """
        try:
            logger.info(f"Adding OPC-UA device {device_id} with discovery...")

            # Discover tags
            discovery_result = await self.discover_opcua_tags(endpoint, namespace_index)

            if not discovery_result["success"]:
                return discovery_result

            # Filter tags if requested
            tags = discovery_result["tags"]
            if tag_filter:
                search_lower = tag_filter.lower()
                tags = [
                    tag for tag in tags
                    if search_lower in tag["tag_name"].lower() or
                       search_lower in tag["display_name"].lower()
                ]
                logger.info(f"Filtered to {len(tags)} tags matching '{tag_filter}'")

            if not tags:
                return {
                    "success": False,
                    "error": "No tags found after filtering"
                }

            # Create device configuration
            config = {
                "endpoint": endpoint,
                "security_mode": "None"
            }

            # Add device
            device_added = await self.add_device(device_id, "opc_ua", config)

            if not device_added:
                return {
                    "success": False,
                    "error": "Failed to add device"
                }

            # Prepare tags for collection
            collection_tags = []
            for idx, tag in enumerate(tags):
                collection_tags.append({
                    "tag_id": f"{device_id}-tag-{idx}",
                    "tag_name": tag["tag_name"],
                    "address": tag["address"]
                })

            # Start collection
            await self.start_collection(device_id, collection_tags, scan_rate)

            logger.info(f"✓ OPC-UA device {device_id} added with {len(collection_tags)} tags")

            return {
                "success": True,
                "device_id": device_id,
                "endpoint": endpoint,
                "tag_count": len(collection_tags),
                "tags": collection_tags,
                "namespaces": discovery_result["namespaces"]
            }

        except Exception as e:
            logger.error(f"Failed to add OPC-UA device with discovery: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def shutdown(self):
        """Shutdown device manager and disconnect all devices"""
        logger.info("Shutting down device manager...")

        # Stop all collection tasks
        for device_id in list(self._collection_tasks.keys()):
            await self.stop_collection(device_id)

        # Disconnect all devices
        for device_id in list(self.devices.keys()):
            await self.remove_device(device_id)

        logger.info("Device manager shutdown complete")
