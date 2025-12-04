"""
Virtual Protocol Adapter
========================

Base class for virtual adapters that read data from the Node-RED
ingestion buffer instead of real industrial devices.

This enables realistic simulation of multiple industrial protocols
(OPC-UA, MODBUS, PROFINET, ETHERNET/IP) using a single data source
from Node-RED.

Architecture:
  Node-RED Simulator -> HTTP Ingest API -> Buffer -> Virtual Adapters -> Kafka

Each virtual adapter:
1. Filters tags by protocol type from the buffer
2. Publishes filtered tags to Kafka with proper metadata
3. Simulates protocol-specific behavior (timing, quality, etc.)

IMPORTANT: Virtual adapters have the SAME behavior as real adapters.
The only difference is the data source (Node-RED buffer vs real PLC).
"""

import asyncio
import hashlib
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from .base_adapter import BaseProtocolAdapter, ProtocolConfig, TagData

# Import metrics
try:
    from app.services.gateway_metrics import get_gateway_metrics
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

logger = logging.getLogger(__name__)


class VirtualAdapter(BaseProtocolAdapter):
    """
    Virtual adapter that reads from Node-RED ingestion buffer

    This adapter doesn't connect to real devices - instead it:
    1. Reads from the in-memory buffer populated by Node-RED
    2. Filters tags based on protocol_filter
    3. Publishes to Kafka just like a real adapter

    BEHAVIOR IS IDENTICAL TO REAL ADAPTERS:
    - last_values cache for fast API access
    - read_all_discovered_tags() for UI
    - _load_managed_tags() from tags_config.json
    - Metrics and monitoring
    """

    def __init__(
        self,
        config: ProtocolConfig,
        protocol_filter: str,
        tag_prefix_filters: Optional[List[str]] = None
    ):
        """
        Initialize virtual adapter

        Args:
            config: Standard protocol configuration
            protocol_filter: Protocol to filter for (e.g., 'OPC-UA', 'MODBUS')
            tag_prefix_filters: Optional list of tag name prefixes to include
        """
        super().__init__(config)

        self.protocol_filter = protocol_filter.upper()
        self.tag_prefix_filters = tag_prefix_filters or []

        # Virtual adapter specific stats
        self._tags_filtered = 0
        self._last_buffer_read = None

        # Simulated connection state
        self._virtual_connected = False

        # Cache for realtime API access (same as real OPC-UA adapter)
        self.last_values: Dict[str, Dict[str, Any]] = {}  # {address: {value, quality, timestamp}}

        # Tag buffer for batch publishing (same as real adapter)
        self._tag_buffer: List[TagData] = []
        self._buffer_lock = asyncio.Lock()

        logger.info(
            f"🔌 Virtual {self.protocol_filter} adapter initialized: {self.adapter_id} "
            f"(filters: {self.tag_prefix_filters or 'all'})"
        )

    async def connect(self) -> bool:
        """
        Simulate connection to virtual device

        For virtual adapters, we verify the buffer is accessible
        and load managed tags (same as real adapter).
        """
        try:
            # Import buffer access
            from app.api.routes.data_ingest import get_data_buffer, get_ingest_stats

            # Verify buffer is accessible
            buffer = get_data_buffer()
            stats = get_ingest_stats()

            logger.info(
                f"✅ Virtual {self.protocol_filter} adapter connected: "
                f"Buffer has {len(buffer)} tags, "
                f"{stats['total_received']} total received"
            )

            # Load managed tags from tags_config.json (same as real adapter)
            await self._load_managed_tags()

            # Discover tags from buffer if no managed tags
            if not self.config.tags:
                logger.info("🔍 No managed tags found - discovering from buffer...")
                await self._discover_tags()

            self._virtual_connected = True
            self.connected = True

            # Update metrics (same as real adapter)
            if METRICS_AVAILABLE:
                metrics = get_gateway_metrics()
                metrics.set_devices_connected(self.protocol_filter.lower().replace('/', '_'), 1)
                metrics.set_device_status(self.adapter_id, self.protocol_filter.lower(), True)
                metrics.track_connection_attempt(self.adapter_id, self.protocol_filter.lower(), True)
                metrics.set_tags_total(self.adapter_id, self._tags_filtered)

            return True

        except Exception as e:
            logger.error(f"❌ Virtual adapter connection failed: {e}")
            self.connected = False

            # Update metrics on failure
            if METRICS_AVAILABLE:
                metrics = get_gateway_metrics()
                metrics.track_connection_attempt(self.adapter_id, self.protocol_filter.lower(), False)
                metrics.set_device_status(self.adapter_id, self.protocol_filter.lower(), False)

            return False

    async def disconnect(self):
        """Cleanup virtual connection"""
        self._virtual_connected = False
        self.connected = False

        # Update metrics
        if METRICS_AVAILABLE:
            metrics = get_gateway_metrics()
            metrics.set_devices_connected(self.protocol_filter.lower().replace('/', '_'), 0)
            metrics.set_device_status(self.adapter_id, self.protocol_filter.lower(), False)

        logger.info(f"🔌 Virtual {self.protocol_filter} adapter disconnected")

    async def _load_managed_tags(self):
        """
        Load tags from tags_config.json (Point Builder concept)

        Only tags explicitly configured in tags_config.json will be historized.
        This follows the PI System pattern where tags must be created in Point Builder
        before they can be archived.

        SAME BEHAVIOR AS REAL ADAPTERS.
        """
        try:
            config_path = Path("/app/config/tags_config.json")

            if not config_path.exists():
                logger.warning("⚠️  tags_config.json not found - no managed tags to load")
                return

            with open(config_path, 'r') as f:
                config_data = json.load(f)

            all_tags = config_data.get("tags", [])

            # Filter tags for this adapter
            adapter_tags = [
                t for t in all_tags
                if t.get("adapter_id") == self.adapter_id
            ]

            if not adapter_tags:
                logger.info(f"📋 No managed tags found for adapter {self.adapter_id}")
                return

            # Convert to adapter config format
            managed_tags = []
            for tag in adapter_tags:
                managed_tags.append({
                    'tag_id': tag.get('tag_id'),
                    'name': tag.get('tag_name') or tag.get('name'),
                    'tag_name': tag.get('tag_name') or tag.get('name'),
                    'address': tag.get('address'),
                    'data_type': tag.get('data_type', 'double')
                })

            if managed_tags:
                self.config.tags = managed_tags
                logger.info(f"✅ Loaded {len(managed_tags)} managed tags from tags_config.json")
                for tag in managed_tags:
                    logger.debug(f"   📌 {tag.get('tag_id')}: {tag.get('name')} @ {tag.get('address')}")
            else:
                logger.info("📋 No managed tags found in tags_config.json")

        except Exception as e:
            logger.error(f"❌ Error loading managed tags: {e}", exc_info=True)

    async def discover_tags(self) -> List[Dict[str, Any]]:
        """
        Public API for tag discovery - similar to OPC-UA browse/KEPServerEX discovery

        Scans the Node-RED buffer and returns all tags matching this adapter's protocol.
        This method can be called via the /api/adapters/{id}/discover endpoint.

        Returns:
            List of discovered tag definitions
        """
        await self._discover_tags()
        return self.config.tags

    async def _discover_tags(self):
        """
        Auto-discover tags from Node-RED buffer

        Reads current buffer and identifies available tags.
        SAME PATTERN AS REAL ADAPTER DISCOVERY (OPC-UA browse, KEPServerEX scan).
        """
        try:
            from app.api.routes.data_ingest import get_data_buffer

            buffer = get_data_buffer()

            if not buffer:
                logger.warning("⚠️  Buffer empty - no tags to discover")
                return

            logger.info(f"🔍 Discovering tags from buffer ({len(buffer)} total)...")

            discovered_tags = []

            for tag_name, tag_data in buffer.items():
                # Get protocol from metadata
                metadata = tag_data.get('metadata', {}) or {}
                tag_protocol = metadata.get('protocol', 'UNKNOWN').upper()

                # Filter by protocol
                if tag_protocol != self.protocol_filter:
                    continue

                # Filter by tag prefix if specified
                if self.tag_prefix_filters:
                    if not any(tag_name.startswith(prefix) for prefix in self.tag_prefix_filters):
                        continue

                # Generate consistent tag_id from tag_name hash
                address = f"virtual:{self.protocol_filter}:{tag_name}"
                tag_id = f"tag_{hashlib.md5(address.encode()).hexdigest()[:8]}"

                # Detect data type from value
                value = tag_data.get('value')
                data_type = 'variant'
                if isinstance(value, bool):
                    data_type = 'boolean'
                elif isinstance(value, int):
                    data_type = 'int32'
                elif isinstance(value, float):
                    data_type = 'double'
                elif isinstance(value, str):
                    data_type = 'string'

                discovered_tags.append({
                    'tag_id': tag_id,
                    'name': tag_name,
                    'tag_name': tag_name,
                    'address': address,
                    'data_type': data_type
                })

                logger.debug(f"  ✓ Discovered: {tag_name} (id={tag_id}) type={data_type}")

            if discovered_tags:
                self.config.tags = discovered_tags
                self._tags_filtered = len(discovered_tags)
                logger.info(f"✅ Discovery complete - Found {len(discovered_tags)} tags for {self.protocol_filter}")
            else:
                logger.warning(f"⚠️  No tags discovered for protocol {self.protocol_filter}")

        except Exception as e:
            logger.error(f"❌ Tag discovery failed: {e}", exc_info=True)

    async def read_tags(self) -> List[TagData]:
        """
        Read tags from ingestion buffer filtered by protocol

        Returns:
            List of TagData matching this adapter's protocol filter
        """
        try:
            from app.api.routes.data_ingest import get_data_buffer

            buffer = get_data_buffer()
            self._last_buffer_read = datetime.utcnow()

            tags = []

            for tag_name, tag_data in buffer.items():
                # Get protocol from metadata
                metadata = tag_data.get('metadata', {}) or {}
                tag_protocol = metadata.get('protocol', 'UNKNOWN').upper()

                # Filter by protocol
                if tag_protocol != self.protocol_filter:
                    continue

                # Filter by tag prefix if specified
                if self.tag_prefix_filters:
                    if not any(tag_name.startswith(prefix) for prefix in self.tag_prefix_filters):
                        continue

                # Build address
                address = f"virtual:{self.protocol_filter}:{tag_name}"

                # Get quality and timestamp
                quality = tag_data.get('quality', 'good').lower()
                timestamp = tag_data.get('timestamp')
                value = tag_data.get('value')

                # Update last_values cache (same as real OPC-UA adapter)
                self.last_values[address] = {
                    'value': value,
                    'quality': quality,
                    'timestamp': timestamp
                }

                # Find tag_id from config if available
                tag_id = None
                for cfg_tag in self.config.tags:
                    if cfg_tag.get('name') == tag_name or cfg_tag.get('tag_name') == tag_name:
                        tag_id = cfg_tag.get('tag_id')
                        break

                # Create TagData
                tag = TagData(
                    tag_name=tag_name,
                    value=value,
                    quality=quality,
                    timestamp=timestamp,
                    source=self.adapter_id,
                    address=address,
                    tag_id=tag_id
                )

                tags.append(tag)

            self._tags_filtered = len(tags)

            # Update metrics
            if METRICS_AVAILABLE and tags:
                try:
                    metrics = get_gateway_metrics()
                    for tag in tags:
                        metrics.track_tag_read(self.adapter_id, self.protocol_filter.lower(), tag.quality, 0.001)
                    metrics.track_data_collected(self.adapter_id, len(tags))
                except Exception:
                    pass

            if tags:
                logger.debug(
                    f"📖 Virtual {self.protocol_filter} adapter read {len(tags)} tags "
                    f"from buffer ({len(buffer)} total)"
                )

            return tags

        except Exception as e:
            logger.error(f"❌ Error reading from buffer: {e}")
            self._error_count += 1

            # Track error in metrics
            if METRICS_AVAILABLE:
                try:
                    metrics = get_gateway_metrics()
                    metrics.track_tag_error(self.adapter_id, self.protocol_filter.lower(), "buffer_read_error")
                except Exception:
                    pass

            return []

    async def read_all_discovered_tags(self) -> List[Dict[str, Any]]:
        """
        Read current values for ALL discovered tags

        This method is used by the Gateway UI to show real-time values.
        SAME INTERFACE AS REAL OPC-UA ADAPTER.

        Returns:
            List of dicts with tag info and current values
        """
        if not self.connected:
            logger.warning("Cannot read tags - adapter not connected")
            return []

        results = []

        try:
            from app.api.routes.data_ingest import get_data_buffer

            buffer = get_data_buffer()
            tags_read = 0

            for tag_name, tag_data in buffer.items():
                # Get protocol from metadata
                metadata = tag_data.get('metadata', {}) or {}
                tag_protocol = metadata.get('protocol', 'UNKNOWN').upper()

                # Filter by protocol
                if tag_protocol != self.protocol_filter:
                    continue

                # Filter by tag prefix if specified
                if self.tag_prefix_filters:
                    if not any(tag_name.startswith(prefix) for prefix in self.tag_prefix_filters):
                        continue

                # Build address
                address = f"virtual:{self.protocol_filter}:{tag_name}"

                # Get values
                value = tag_data.get('value')
                quality = tag_data.get('quality', 'good')
                timestamp = tag_data.get('timestamp')

                # Update cache
                self.last_values[address] = {
                    'value': value,
                    'quality': quality,
                    'timestamp': timestamp
                }

                # Detect data type
                data_type = 'variant'
                if isinstance(value, bool):
                    data_type = 'boolean'
                elif isinstance(value, int):
                    data_type = 'int32'
                elif isinstance(value, float):
                    data_type = 'double'
                elif isinstance(value, str):
                    data_type = 'string'

                results.append({
                    "name": tag_name,
                    "address": address,
                    "current_value": value,
                    "quality": quality,
                    "data_type": data_type,
                    "unit": metadata.get('unit'),
                    "last_update": timestamp,
                    "connected": quality.lower() == 'good'
                })

                tags_read += 1

            logger.debug(f"📖 Read {tags_read} tags for {self.protocol_filter}")

        except Exception as e:
            logger.error(f"❌ Error reading all tags: {e}", exc_info=True)

        return results

    async def health_check(self) -> bool:
        """Check if buffer is accessible"""
        try:
            from app.api.routes.data_ingest import get_data_buffer
            buffer = get_data_buffer()
            return self._virtual_connected and buffer is not None
        except Exception:
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get extended stats for virtual adapter"""
        base_stats = super().get_stats()
        base_stats.update({
            'protocol_filter': self.protocol_filter,
            'tag_prefix_filters': self.tag_prefix_filters,
            'tags_filtered': self._tags_filtered,
            'tags_in_cache': len(self.last_values),
            'last_buffer_read': self._last_buffer_read.isoformat() if self._last_buffer_read else None,
            'virtual': True
        })
        return base_stats


class OPCUAVirtualAdapter(VirtualAdapter):
    """
    Virtual OPC-UA adapter for simulated PLCs (Gates)

    Simulates:
    - Siemens S7 series (OPC-UA interface)
    - Gate control systems
    - ARZ (Armazém/Warehouse) equipment

    Auto-discovery: Will discover ALL tags with protocol='OPC-UA' from Node-RED buffer.
    No prefix filtering - matches real KEPServerEX/OPC-UA discovery behavior.
    """

    def __init__(self, config: ProtocolConfig):
        super().__init__(
            config=config,
            protocol_filter='OPC-UA',
            # Empty list = no prefix filtering = discover ALL OPC-UA tags (like real OPC-UA)
            tag_prefix_filters=[]
        )

        # OPC-UA specific simulation
        self.namespace_index = 2
        self.subscription_interval_ms = config.extra_config.get('subscription_interval', 100)

    async def connect(self) -> bool:
        """Simulate OPC-UA connection with namespace info"""
        if await super().connect():
            logger.info(
                f"🔵 OPC-UA Virtual connected: ns={self.namespace_index}, "
                f"subscription={self.subscription_interval_ms}ms"
            )
            return True
        return False


class ModbusVirtualAdapter(VirtualAdapter):
    """
    Virtual Modbus adapter for simulated conveyor belts

    Simulates:
    - Modbus TCP/RTU communication
    - Conveyor belt controllers
    - Motor drive systems (VFDs)

    Auto-discovery: Will discover ALL tags with protocol='MODBUS' from Node-RED buffer.
    No prefix filtering - matches real Modbus scanner discovery behavior.
    """

    def __init__(self, config: ProtocolConfig):
        super().__init__(
            config=config,
            protocol_filter='MODBUS',
            # Empty list = no prefix filtering = discover ALL MODBUS tags
            tag_prefix_filters=[]
        )

        # Modbus specific simulation
        self.unit_id = config.extra_config.get('unit_id', 1)
        self.byte_order = config.extra_config.get('byte_order', 'big')

    async def connect(self) -> bool:
        """Simulate Modbus connection"""
        if await super().connect():
            logger.info(
                f"🟢 Modbus Virtual connected: unit_id={self.unit_id}, "
                f"byte_order={self.byte_order}"
            )
            return True
        return False


class ProfinetVirtualAdapter(VirtualAdapter):
    """
    Virtual PROFINET adapter for simulated elevator and scale

    Simulates:
    - PROFINET IO communication
    - Siemens PROFINET devices
    - Elevator/bucket elevator systems (ELV01)
    - Flow scale systems (BLC01 - Balança de Fluxo)

    Auto-discovery: Will discover ALL tags with protocol='PROFINET' from Node-RED buffer.
    No prefix filtering - matches real PROFINET discovery behavior.
    """

    def __init__(self, config: ProtocolConfig):
        super().__init__(
            config=config,
            protocol_filter='PROFINET',
            # Empty list = no prefix filtering = discover ALL PROFINET tags
            tag_prefix_filters=[]
        )

        # PROFINET specific simulation
        self.device_name = config.extra_config.get('device_name', 'elevator-01')
        self.cycle_time_ms = config.extra_config.get('cycle_time', 4)  # PROFINET IRT

    async def connect(self) -> bool:
        """Simulate PROFINET connection"""
        if await super().connect():
            logger.info(
                f"🟣 PROFINET Virtual connected: device={self.device_name}, "
                f"cycle={self.cycle_time_ms}ms"
            )
            return True
        return False


class EthernetIPVirtualAdapter(VirtualAdapter):
    """
    Virtual EtherNet/IP adapter for simulated shiploader and tripper

    Simulates:
    - EtherNet/IP (CIP) communication
    - Allen-Bradley/Rockwell PLCs
    - Shiploader control systems (SLD01)
    - Tripper car systems (TRP01)

    Auto-discovery: Will discover ALL tags with protocol='ETHERNET/IP' from Node-RED buffer.
    No prefix filtering - matches real EtherNet/IP discovery behavior.
    """

    def __init__(self, config: ProtocolConfig):
        super().__init__(
            config=config,
            protocol_filter='ETHERNET/IP',
            # Empty list = no prefix filtering = discover ALL ETHERNET/IP tags
            tag_prefix_filters=[]
        )

        # EtherNet/IP specific simulation
        self.slot = config.extra_config.get('slot', 0)
        self.rpi_ms = config.extra_config.get('rpi', 100)  # Requested Packet Interval

    async def connect(self) -> bool:
        """Simulate EtherNet/IP connection"""
        if await super().connect():
            logger.info(
                f"🟠 EtherNet/IP Virtual connected: slot={self.slot}, "
                f"RPI={self.rpi_ms}ms"
            )
            return True
        return False
