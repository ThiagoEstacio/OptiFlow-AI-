"""
Data Collector Service

Unified data collection service for all industrial protocols.
Supports:
- EtherNet/IP (Rockwell PLCs)
- S7 Protocol (Siemens PLCs)
- OPC UA
- Modbus TCP/RTU
- MQTT

Features:
- Multi-protocol support
- Batch reads for efficiency
- Connection pooling
- Rate limiting
- Health monitoring
- Auto-reconnect
- Quality codes
"""

import asyncio
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time

from loguru import logger

# Import protocol handlers
from ..protocols.ethernet_ip import EtherNetIPClient, TagValue, ConnectionStatus


class CollectionMode(str, Enum):
    """Data collection modes"""
    POLLING = "polling"  # Regular interval polling
    EXCEPTION = "exception"  # Report by exception (on change)
    BOTH = "both"  # Both polling and exception


class DataQuality(str, Enum):
    """Data quality codes"""
    GOOD = "Good"
    BAD = "Bad"
    UNCERTAIN = "Uncertain"


@dataclass
class PointConfig:
    """Configuration for a single point (tag)"""
    point_id: int
    point_name: str
    device_id: int
    device_ip: str
    protocol: str
    source_address: str  # Tag name or address
    data_type: str
    collection_mode: CollectionMode = CollectionMode.POLLING
    scan_rate: int = 1000  # milliseconds
    deadband: Optional[float] = None  # For exception reporting
    enabled: bool = True
    slot: int = 0  # For EtherNet/IP and S7

    # Scaling
    raw_min: Optional[float] = None
    raw_max: Optional[float] = None
    eng_min: Optional[float] = None
    eng_max: Optional[float] = None

    # Last values for deadband/exception
    last_value: Optional[Any] = None
    last_collection: Optional[float] = None


@dataclass
class DataPoint:
    """Collected data point"""
    point_id: int
    point_name: str
    value: Any
    quality: str
    timestamp: float
    device_id: int


@dataclass
class DeviceStatus:
    """Device connection status"""
    device_id: int
    device_ip: str
    protocol: str
    status: str
    last_connected: Optional[float] = None
    error_count: int = 0
    total_reads: int = 0
    failed_reads: int = 0


class DataCollector:
    """
    Main data collection service.

    Manages:
    - Multiple device connections
    - Point configuration
    - Data collection loops
    - Health monitoring
    """

    def __init__(
        self,
        data_callback: Optional[callable] = None,
        status_callback: Optional[callable] = None
    ):
        """
        Initialize data collector.

        Args:
            data_callback: Callback for collected data (async function)
            status_callback: Callback for status updates (async function)
        """
        self.data_callback = data_callback
        self.status_callback = status_callback

        # Point configurations
        self._points: Dict[int, PointConfig] = {}
        self._points_by_device: Dict[int, List[PointConfig]] = {}

        # Protocol clients
        self._ethernetip_clients: Dict[str, EtherNetIPClient] = {}
        self._s7_clients: Dict[str, Any] = {}  # S7Client instances
        self._opcua_clients: Dict[str, Any] = {}  # OPCUAClient instances

        # Device status
        self._device_status: Dict[int, DeviceStatus] = {}

        # Collection tasks
        self._collection_tasks: Dict[int, asyncio.Task] = {}

        # Control flags
        self._running = False
        self._shutdown_event = asyncio.Event()

        logger.info("Data Collector initialized")

    def add_point(self, point: PointConfig) -> None:
        """
        Add a point to collection.

        Args:
            point: Point configuration
        """
        self._points[point.point_id] = point

        # Group by device
        if point.device_id not in self._points_by_device:
            self._points_by_device[point.device_id] = []

        self._points_by_device[point.device_id].append(point)

        logger.info(f"Added point {point.point_name} (ID: {point.point_id})")

    def remove_point(self, point_id: int) -> bool:
        """
        Remove a point from collection.

        Args:
            point_id: Point ID

        Returns:
            True if removed, False if not found
        """
        if point_id not in self._points:
            return False

        point = self._points[point_id]
        device_points = self._points_by_device.get(point.device_id, [])
        device_points = [p for p in device_points if p.point_id != point_id]

        if device_points:
            self._points_by_device[point.device_id] = device_points
        else:
            del self._points_by_device[point.device_id]

        del self._points[point_id]

        logger.info(f"Removed point {point.point_name} (ID: {point_id})")
        return True

    def update_point(self, point_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update point configuration.

        Args:
            point_id: Point ID
            updates: Dictionary of fields to update

        Returns:
            True if updated
        """
        if point_id not in self._points:
            return False

        point = self._points[point_id]

        for key, value in updates.items():
            if hasattr(point, key):
                setattr(point, key, value)

        logger.info(f"Updated point {point.point_name} (ID: {point_id})")
        return True

    async def start(self) -> None:
        """Start data collection for all configured points."""
        if self._running:
            logger.warning("Data collector already running")
            return

        self._running = True
        self._shutdown_event.clear()

        logger.info("Starting data collector...")

        # Group points by device and create collection tasks
        for device_id, points in self._points_by_device.items():
            # Filter enabled points
            enabled_points = [p for p in points if p.enabled]

            if not enabled_points:
                continue

            # Determine protocol
            protocol = enabled_points[0].protocol

            # Create collection task for this device
            task = asyncio.create_task(
                self._collect_device_data(device_id, enabled_points)
            )
            self._collection_tasks[device_id] = task

            logger.info(
                f"Started collection for device {device_id} "
                f"({protocol}, {len(enabled_points)} points)"
            )

        logger.info(f"Data collector started with {len(self._collection_tasks)} devices")

    async def stop(self) -> None:
        """Stop data collection."""
        if not self._running:
            return

        logger.info("Stopping data collector...")

        self._running = False
        self._shutdown_event.set()

        # Cancel all collection tasks
        for device_id, task in self._collection_tasks.items():
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._collection_tasks.values(), return_exceptions=True)

        self._collection_tasks.clear()

        # Disconnect all clients
        await self._disconnect_all()

        logger.info("Data collector stopped")

    async def _collect_device_data(self, device_id: int, points: List[PointConfig]) -> None:
        """
        Collection loop for a specific device.

        Args:
            device_id: Device ID
            points: List of points to collect
        """
        protocol = points[0].protocol
        device_ip = points[0].device_ip

        logger.info(f"Collection loop started for device {device_id} ({device_ip})")

        # Initialize device status
        self._device_status[device_id] = DeviceStatus(
            device_id=device_id,
            device_ip=device_ip,
            protocol=protocol,
            status=ConnectionStatus.DISCONNECTED
        )

        while self._running and not self._shutdown_event.is_set():
            try:
                if protocol == "EtherNet/IP":
                    await self._collect_ethernetip(device_id, device_ip, points)
                elif protocol == "S7":
                    await self._collect_s7(device_id, device_ip, points)
                elif protocol == "OPC UA":
                    await self._collect_opcua(device_id, device_ip, points)
                else:
                    logger.warning(f"Unsupported protocol: {protocol}")
                    await asyncio.sleep(5)

            except asyncio.CancelledError:
                logger.info(f"Collection cancelled for device {device_id}")
                break
            except Exception as e:
                logger.error(f"Error in collection loop for device {device_id}: {e}")
                await asyncio.sleep(5)  # Back off on error

    async def _collect_ethernetip(
        self,
        device_id: int,
        device_ip: str,
        points: List[PointConfig]
    ) -> None:
        """
        Collect data from EtherNet/IP device.

        Args:
            device_id: Device ID
            device_ip: Device IP address
            points: Points to collect
        """
        # Get or create client
        slot = points[0].slot if points else 0
        client_key = f"{device_ip}:{slot}"

        if client_key not in self._ethernetip_clients:
            client = EtherNetIPClient(device_ip, slot=slot)
            if not await client.connect_async():
                logger.error(f"Failed to connect to {device_ip}")
                self._device_status[device_id].status = ConnectionStatus.ERROR
                await asyncio.sleep(5)
                return

            self._ethernetip_clients[client_key] = client
            self._device_status[device_id].status = ConnectionStatus.CONNECTED
            self._device_status[device_id].last_connected = time.time()

            if self.status_callback:
                await self.status_callback(self._device_status[device_id])

        client = self._ethernetip_clients[client_key]

        # Check connection
        if not client.is_connected():
            logger.warning(f"Client disconnected, reconnecting to {device_ip}")
            if not await client.connect_async():
                logger.error(f"Reconnection failed for {device_ip}")
                self._device_status[device_id].status = ConnectionStatus.ERROR
                await asyncio.sleep(5)
                return

        # Group points by scan rate for efficient batch reads
        scan_groups = {}
        for point in points:
            rate = point.scan_rate
            if rate not in scan_groups:
                scan_groups[rate] = []
            scan_groups[rate].append(point)

        # Collect data for each scan rate group
        current_time = time.time()

        for scan_rate, group_points in scan_groups.items():
            # Check if it's time to collect
            needs_collection = []

            for point in group_points:
                if point.last_collection is None:
                    needs_collection.append(point)
                else:
                    elapsed = (current_time - point.last_collection) * 1000
                    if elapsed >= scan_rate:
                        needs_collection.append(point)

            if not needs_collection:
                continue

            # Batch read
            tag_names = [p.source_address for p in needs_collection]

            try:
                results = await client.read_tags_async(tag_names)

                # Process results
                data_points = []

                for point, tag_value in zip(needs_collection, results):
                    # Apply scaling if configured
                    scaled_value = self._apply_scaling(tag_value.value, point)

                    # Check deadband for exception reporting
                    should_report = self._check_deadband(scaled_value, point)

                    if should_report:
                        data_points.append(DataPoint(
                            point_id=point.point_id,
                            point_name=point.point_name,
                            value=scaled_value,
                            quality=tag_value.quality,
                            timestamp=time.time(),
                            device_id=device_id
                        ))

                    # Update last values
                    point.last_value = scaled_value
                    point.last_collection = current_time

                # Send data via callback
                if data_points and self.data_callback:
                    await self.data_callback(data_points)

                # Update statistics
                self._device_status[device_id].total_reads += len(tag_names)

            except Exception as e:
                logger.error(f"Error reading tags from {device_ip}: {e}")
                self._device_status[device_id].failed_reads += len(tag_names)
                self._device_status[device_id].error_count += 1

        # Sleep until next collection cycle
        # Use minimum scan rate
        min_scan_rate = min(scan_groups.keys()) if scan_groups else 1000
        await asyncio.sleep(min_scan_rate / 1000.0)

    async def _collect_s7(
        self,
        device_id: int,
        device_ip: str,
        points: List[PointConfig]
    ) -> None:
        """
        Collect data from S7 device.

        Args:
            device_id: Device ID
            device_ip: Device IP address
            points: Points to collect
        """
        from ..protocols.s7 import S7Client

        # Get or create client
        rack = points[0].slot if hasattr(points[0], 'rack') else 0
        slot = points[0].slot if points else 1
        client_key = f"{device_ip}:{rack}:{slot}"

        if client_key not in self._s7_clients:
            client = S7Client(device_ip, rack=rack, slot=slot)
            if not await client.connect_async():
                logger.error(f"Failed to connect to S7 PLC at {device_ip}")
                self._device_status[device_id].status = ConnectionStatus.ERROR
                await asyncio.sleep(5)
                return

            self._s7_clients[client_key] = client
            self._device_status[device_id].status = ConnectionStatus.CONNECTED
            self._device_status[device_id].last_connected = time.time()

            if self.status_callback:
                await self.status_callback(self._device_status[device_id])

        client = self._s7_clients[client_key]

        # Check connection
        if not client.is_connected():
            logger.warning(f"S7 client disconnected, reconnecting to {device_ip}")
            if not await client.connect_async():
                logger.error(f"Reconnection failed for {device_ip}")
                self._device_status[device_id].status = ConnectionStatus.ERROR
                await asyncio.sleep(5)
                return

        # Group points by scan rate
        scan_groups = {}
        for point in points:
            rate = point.scan_rate
            if rate not in scan_groups:
                scan_groups[rate] = []
            scan_groups[rate].append(point)

        # Collect data for each scan rate group
        current_time = time.time()

        for scan_rate, group_points in scan_groups.items():
            # Check if it's time to collect
            needs_collection = []

            for point in group_points:
                if point.last_collection is None:
                    needs_collection.append(point)
                else:
                    elapsed = (current_time - point.last_collection) * 1000
                    if elapsed >= scan_rate:
                        needs_collection.append(point)

            if not needs_collection:
                continue

            # Read each address individually (S7 doesn't have batch read like EtherNet/IP)
            data_points = []

            for point in needs_collection:
                try:
                    # Read using S7 address
                    result = await client.read_address_async(point.source_address)

                    if result.quality == "Good":
                        # Apply scaling
                        scaled_value = self._apply_scaling(result.value, point)

                        # Check deadband
                        should_report = self._check_deadband(scaled_value, point)

                        if should_report:
                            data_points.append(DataPoint(
                                point_id=point.point_id,
                                point_name=point.point_name,
                                value=scaled_value,
                                quality=result.quality,
                                timestamp=time.time(),
                                device_id=device_id
                            ))

                        # Update last values
                        point.last_value = scaled_value
                        point.last_collection = current_time

                        # Update statistics
                        self._device_status[device_id].total_reads += 1

                    else:
                        logger.warning(
                            f"Bad quality reading {point.source_address}: {result.error}"
                        )
                        self._device_status[device_id].failed_reads += 1

                except Exception as e:
                    logger.error(f"Error reading {point.source_address} from {device_ip}: {e}")
                    self._device_status[device_id].failed_reads += 1
                    self._device_status[device_id].error_count += 1

            # Send data via callback
            if data_points and self.data_callback:
                await self.data_callback(data_points)

        # Sleep until next collection cycle
        min_scan_rate = min(scan_groups.keys()) if scan_groups else 1000
        await asyncio.sleep(min_scan_rate / 1000.0)

    async def _collect_opcua(
        self,
        device_id: int,
        device_ip: str,
        points: List[PointConfig]
    ) -> None:
        """
        Collect data from OPC UA device.

        Args:
            device_id: Device ID
            device_ip: Device IP/URL (e.g., opc.tcp://192.168.1.100:4840)
            points: Points to collect
        """
        from ..protocols.opcua import OPCUAClient

        # Get or create client
        client_key = device_ip

        if client_key not in self._opcua_clients:
            client = OPCUAClient(device_ip)
            if not await client.connect():
                logger.error(f"Failed to connect to OPC UA server at {device_ip}")
                self._device_status[device_id].status = ConnectionStatus.ERROR
                await asyncio.sleep(5)
                return

            self._opcua_clients[client_key] = client
            self._device_status[device_id].status = ConnectionStatus.CONNECTED
            self._device_status[device_id].last_connected = time.time()

            if self.status_callback:
                await self.status_callback(self._device_status[device_id])

        client = self._opcua_clients[client_key]

        # Check connection
        if not client.is_connected():
            logger.warning(f"OPC UA client disconnected, reconnecting to {device_ip}")
            if not await client.connect():
                logger.error(f"Reconnection failed for {device_ip}")
                self._device_status[device_id].status = ConnectionStatus.ERROR
                await asyncio.sleep(5)
                return

        # Group points by scan rate
        scan_groups = {}
        for point in points:
            rate = point.scan_rate
            if rate not in scan_groups:
                scan_groups[rate] = []
            scan_groups[rate].append(point)

        # Collect data for each scan rate group
        current_time = time.time()

        for scan_rate, group_points in scan_groups.items():
            # Check if it's time to collect
            needs_collection = []

            for point in group_points:
                if point.last_collection is None:
                    needs_collection.append(point)
                else:
                    elapsed = (current_time - point.last_collection) * 1000
                    if elapsed >= scan_rate:
                        needs_collection.append(point)

            if not needs_collection:
                continue

            # Read each node
            data_points = []

            for point in needs_collection:
                try:
                    # Read using OPC UA node ID
                    result = await client.read_node(point.source_address)

                    if result.quality == "Good":
                        # Apply scaling
                        scaled_value = self._apply_scaling(result.value, point)

                        # Check deadband
                        should_report = self._check_deadband(scaled_value, point)

                        if should_report:
                            data_points.append(DataPoint(
                                point_id=point.point_id,
                                point_name=point.point_name,
                                value=scaled_value,
                                quality=result.quality,
                                timestamp=time.time(),
                                device_id=device_id
                            ))

                        # Update last values
                        point.last_value = scaled_value
                        point.last_collection = current_time

                        # Update statistics
                        self._device_status[device_id].total_reads += 1

                    else:
                        logger.warning(
                            f"Bad quality reading {point.source_address}: {result.error}"
                        )
                        self._device_status[device_id].failed_reads += 1

                except Exception as e:
                    logger.error(f"Error reading {point.source_address} from {device_ip}: {e}")
                    self._device_status[device_id].failed_reads += 1
                    self._device_status[device_id].error_count += 1

            # Send data via callback
            if data_points and self.data_callback:
                await self.data_callback(data_points)

        # Sleep until next collection cycle
        min_scan_rate = min(scan_groups.keys()) if scan_groups else 1000
        await asyncio.sleep(min_scan_rate / 1000.0)

    def _apply_scaling(self, value: Any, point: PointConfig) -> Any:
        """
        Apply scaling to raw value.

        Args:
            value: Raw value
            point: Point configuration

        Returns:
            Scaled value
        """
        if value is None:
            return None

        # Only scale numeric values
        if not isinstance(value, (int, float)):
            return value

        # Check if scaling is configured
        if (point.raw_min is None or point.raw_max is None or
            point.eng_min is None or point.eng_max is None):
            return value

        # Linear scaling
        raw_range = point.raw_max - point.raw_min
        eng_range = point.eng_max - point.eng_min

        if raw_range == 0:
            return value

        scaled = point.eng_min + ((value - point.raw_min) / raw_range) * eng_range

        return scaled

    def _check_deadband(self, value: Any, point: PointConfig) -> bool:
        """
        Check if value should be reported based on deadband.

        Args:
            value: Current value
            point: Point configuration

        Returns:
            True if should report
        """
        # Always report if no previous value
        if point.last_value is None:
            return True

        # Always report if polling mode
        if point.collection_mode == CollectionMode.POLLING:
            return True

        # Check deadband for exception/both modes
        if point.deadband is None:
            # No deadband configured, report on any change
            return value != point.last_value

        # Only check deadband for numeric values
        if not isinstance(value, (int, float)) or not isinstance(point.last_value, (int, float)):
            return value != point.last_value

        # Check if change exceeds deadband
        change = abs(value - point.last_value)
        return change >= point.deadband

    async def _disconnect_all(self) -> None:
        """Disconnect all protocol clients."""
        # Disconnect EtherNet/IP clients
        for client_key, client in self._ethernetip_clients.items():
            await client.disconnect_async()

        self._ethernetip_clients.clear()

        # Disconnect S7 clients
        for client_key, client in self._s7_clients.items():
            await client.disconnect_async()

        self._s7_clients.clear()

        # Disconnect OPC UA clients
        for client_key, client in self._opcua_clients.items():
            await client.disconnect()

        self._opcua_clients.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get collection statistics.

        Returns:
            Dictionary with statistics
        """
        total_points = len(self._points)
        enabled_points = sum(1 for p in self._points.values() if p.enabled)

        device_stats = []
        for device_id, status in self._device_status.items():
            success_rate = 0
            if status.total_reads > 0:
                success_rate = (status.total_reads - status.failed_reads) / status.total_reads * 100

            device_stats.append({
                "device_id": device_id,
                "device_ip": status.device_ip,
                "protocol": status.protocol,
                "status": status.status,
                "total_reads": status.total_reads,
                "failed_reads": status.failed_reads,
                "success_rate": round(success_rate, 2),
                "error_count": status.error_count
            })

        return {
            "total_points": total_points,
            "enabled_points": enabled_points,
            "active_devices": len(self._collection_tasks),
            "devices": device_stats,
            "running": self._running
        }
