"""
OPC UA Protocol Adapter
=======================

Connects to OPC UA servers and publishes tag data to Kafka.

Features:
- Automatic reconnection on connection loss
- Subscription-based monitoring (efficient push model)
- Batch publishing to Kafka
- Graceful degradation on errors

Based on asyncua library and existing OPC UA browser code.
"""

from typing import List, Dict, Any, Optional
import asyncio
import hashlib
import logging

try:
    from asyncua import Client, ua
    from asyncua.common.subscription import Subscription
    OPCUA_AVAILABLE = True
except ImportError:
    OPCUA_AVAILABLE = False
    logging.warning("asyncua not installed - OPC UA adapter disabled")

from .base_adapter import BaseProtocolAdapter, ProtocolConfig, TagData

# Import metrics
try:
    from app.services.gateway_metrics import get_gateway_metrics
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

logger = logging.getLogger(__name__)


class OPCUAAdapter(BaseProtocolAdapter):
    """
    OPC UA protocol adapter

    Connects to OPC UA server and monitors tags via subscriptions.
    Much more efficient than polling - server pushes changes.

    Configuration (extra_config):
    - security_policy: Security policy (None, Basic256Sha256, etc.)
    - security_mode: Security mode (None, Sign, SignAndEncrypt)
    - username: Optional username for authentication
    - password: Optional password for authentication
    - subscription_interval: Subscription publishing interval in ms (default: 100)
    """

    def __init__(self, config: ProtocolConfig):
        if not OPCUA_AVAILABLE:
            raise ImportError("asyncua library not available - cannot create OPC UA adapter")

        super().__init__(config)

        # OPC UA specific state
        self.client: Optional[Client] = None
        self.subscription: Optional[Subscription] = None
        self._monitored_items: Dict[str, Any] = {}  # {node_id: monitored_item}

        # Tag values buffer (for batch publishing)
        self._tag_buffer: List[TagData] = []
        self._buffer_lock = asyncio.Lock()

        # Cache for realtime API access (last received values from subscription)
        self.last_values: Dict[str, Dict[str, Any]] = {}  # {address: {value, quality, timestamp}}

        # Connection settings
        self.endpoint = f"opc.tcp://{config.host}:{config.port}"
        self.username = config.extra_config.get('username')
        self.password = config.extra_config.get('password')
        self.subscription_interval = config.extra_config.get('subscription_interval', 100)

        logger.info(f"🔧 OPC UA adapter initialized - Endpoint: {self.endpoint}")

    async def connect(self) -> bool:
        """Connect to OPC UA server and setup subscriptions"""
        if self.connected:
            logger.warning(f"⚠️  {self.adapter_id} already connected")
            return True

        try:
            logger.info(f"🔌 Connecting to OPC UA server: {self.endpoint}")

            # Create client
            self.client = Client(url=self.endpoint, timeout=self.config.timeout)

            # Set authentication if provided
            if self.username and self.password:
                self.client.set_user(self.username)
                self.client.set_password(self.password)
                logger.info(f"🔐 Using authentication for user: {self.username}")

            # Connect to server
            await self.client.connect()

            # Get namespace array for logging
            namespaces = await self.client.get_namespace_array()
            logger.info(f"✅ Connected to OPC UA server - Namespaces: {len(namespaces)}")

            # Load tags from tags_config.json (Point Builder concept)
            # Only tags in config will be historized
            await self._load_managed_tags()

            # If still no tags, fall back to auto-discovery
            if not self.config.tags:
                logger.info("🔍 No managed tags found - starting auto-discovery...")
                await self._discover_tags()

            # Create subscription
            await self._create_subscription()

            self.connected = True

            # Update metrics
            if METRICS_AVAILABLE:
                metrics = get_gateway_metrics()
                metrics.set_devices_connected("opc_ua", 1)
                metrics.set_device_status(self.adapter_id, "opc_ua", True)
                metrics.track_connection_attempt(self.adapter_id, "opc_ua", True)
                metrics.set_opcua_sessions(1)
                metrics.set_tags_total(self.adapter_id, len(self.config.tags))

            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to OPC UA server: {e}", exc_info=True)
            self.connected = False

            # Update metrics on failure
            if METRICS_AVAILABLE:
                metrics = get_gateway_metrics()
                metrics.track_connection_attempt(self.adapter_id, "opc_ua", False)
                metrics.set_device_status(self.adapter_id, "opc_ua", False)

            return False

    async def disconnect(self):
        """Disconnect from OPC UA server"""
        if not self.connected:
            return

        try:
            logger.info(f"🔌 Disconnecting from {self.endpoint}...")

            # Delete subscription
            if self.subscription and self.client:
                try:
                    await self.subscription.delete()
                    logger.info("✅ Subscription deleted")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to delete subscription: {e}")

            # Disconnect client
            if self.client:
                try:
                    await self.client.disconnect()
                    logger.info("✅ Client disconnected")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to disconnect client: {e}")

            self.client = None
            self.subscription = None
            self._monitored_items.clear()
            self.connected = False

            # Update metrics
            if METRICS_AVAILABLE:
                metrics = get_gateway_metrics()
                metrics.set_devices_connected("opc_ua", 0)
                metrics.set_device_status(self.adapter_id, "opc_ua", False)
                metrics.set_opcua_sessions(0)

        except Exception as e:
            logger.error(f"❌ Error during disconnect: {e}")

    async def _create_subscription(self):
        """Create OPC UA subscription for monitoring tags"""
        if not self.client:
            raise RuntimeError("Client not connected")

        try:
            logger.info(f"📡 Creating OPC UA subscription (interval: {self.subscription_interval}ms)...")

            # Create subscription
            # The handler should be the adapter object itself (which has datachange_notification method)
            self.subscription = await self.client.create_subscription(
                period=self.subscription_interval,
                handler=self
            )

            # Subscribe to all configured tags
            for tag_config in self.config.tags:
                try:
                    node_id = tag_config.get('address')  # OPC UA node ID
                    tag_name = tag_config.get('name') or tag_config.get('tag_name')
                    tag_id = tag_config.get('tag_id')  # Unique ID for InfluxDB persistence

                    if not node_id or not tag_name:
                        logger.warning(f"⚠️  Skipping tag with missing node_id or name: {tag_config}")
                        continue

                    # Get node from client
                    node = self.client.get_node(node_id)

                    # Create monitored item
                    handle = await self.subscription.subscribe_data_change(node)

                    self._monitored_items[node_id] = {
                        'handle': handle,
                        'tag_name': tag_name,
                        'tag_id': tag_id,  # Store tag_id for Kafka publishing
                        'node': node
                    }

                    logger.debug(f"✅ Subscribed to {tag_name} (id={tag_id}, node={node_id})")

                except Exception as e:
                    logger.error(f"❌ Failed to subscribe to tag {tag_config}: {e}")

            logger.info(f"✅ Subscription created - Monitoring {len(self._monitored_items)} tags")

            # Update metrics
            if METRICS_AVAILABLE:
                metrics = get_gateway_metrics()
                metrics.set_opcua_subscriptions(self.adapter_id, 1)

        except Exception as e:
            logger.error(f"❌ Failed to create subscription: {e}", exc_info=True)
            raise

    def datachange_notification(self, node, value, data):
        """
        Callback for subscription data changes (asyncua standard method name)

        This is called by asyncua when a monitored value changes.
        We buffer the change and publish in batches.
        """
        try:
            # Find tag name for this node
            node_id = node.nodeid.to_string()

            tag_info = self._monitored_items.get(node_id)
            if not tag_info:
                logger.warning(f"⚠️  Received update for unknown node: {node_id}")
                return

            tag_name = tag_info['tag_name']
            tag_id = tag_info.get('tag_id')  # Get tag_id for InfluxDB persistence

            # Determine quality
            quality = 'good'
            timestamp = None

            # Extract quality and timestamp from OPC UA DataValue
            if hasattr(data, 'monitored_item') and hasattr(data.monitored_item, 'Value'):
                datavalue = data.monitored_item.Value

                # Get quality from StatusCode
                if hasattr(datavalue, 'StatusCode_'):
                    status_code = datavalue.StatusCode_
                    if hasattr(status_code, 'is_good') and callable(status_code.is_good):
                        quality = 'Good' if status_code.is_good() else 'Bad'
                    elif status_code.value == 0:
                        quality = 'Good'
                    else:
                        quality = 'Bad'

                # Get timestamp (prefer SourceTimestamp)
                if hasattr(datavalue, 'SourceTimestamp') and datavalue.SourceTimestamp:
                    timestamp = datavalue.SourceTimestamp.isoformat()
                elif hasattr(datavalue, 'ServerTimestamp') and datavalue.ServerTimestamp:
                    timestamp = datavalue.ServerTimestamp.isoformat()
            elif hasattr(data, 'StatusCode'):
                # Fallback for older format
                if not data.StatusCode.is_good():
                    quality = 'Bad'
                elif data.StatusCode.name == 'Uncertain':
                    quality = 'Uncertain'

            # Store in last_values cache for realtime API access
            self.last_values[node_id] = {
                'value': value,
                'quality': quality,
                'timestamp': timestamp
            }

            # Create TagData (for Kafka publishing)
            tag_data = TagData(
                tag_name=tag_name,
                value=value,
                quality=quality.lower(),  # Keep lowercase for backward compatibility
                source=self.adapter_id,
                address=node_id,
                tag_id=tag_id  # Include tag_id for InfluxDB persistence
            )

            # Add to buffer (will be published in scan loop)
            # Using asyncio.create_task to not block the callback
            asyncio.create_task(self._add_to_buffer(tag_data))

            # Update metrics
            if METRICS_AVAILABLE:
                try:
                    metrics = get_gateway_metrics()
                    metrics.track_tag_read(self.adapter_id, "opc_ua", quality.lower(), 0.001)  # Subscription is nearly instant
                    metrics.track_opcua_notification(self.adapter_id)
                    metrics.track_data_collected(self.adapter_id, 1)
                except Exception:
                    pass  # Don't let metrics fail the data flow

            logger.debug(f"📊 {tag_name}: {value} (quality={quality}, ts={timestamp})")

        except Exception as e:
            logger.error(f"❌ Error in subscription handler: {e}", exc_info=True)

            # Track error in metrics
            if METRICS_AVAILABLE:
                try:
                    metrics = get_gateway_metrics()
                    metrics.track_tag_error(self.adapter_id, "opc_ua", "subscription_error")
                except Exception:
                    pass

    async def _add_to_buffer(self, tag_data: TagData):
        """Add tag data to buffer (thread-safe)"""
        async with self._buffer_lock:
            self._tag_buffer.append(tag_data)

    async def read_tags(self) -> List[TagData]:
        """
        Read current tag values from buffer

        This is called by the scan loop. We return buffered values
        from subscription updates.
        """
        async with self._buffer_lock:
            # Return and clear buffer
            tags = self._tag_buffer.copy()
            self._tag_buffer.clear()

        return tags

    async def _load_managed_tags(self):
        """
        Load tags from tags_config.json (Point Builder concept)

        Only tags explicitly configured in tags_config.json will be historized.
        This follows the PI System pattern where tags must be created in Point Builder
        before they can be archived.
        """
        import json
        from pathlib import Path

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
                if t.get("adapter_id") == self.adapter_id or t.get("protocol_type") == "opcua"
            ]

            if not adapter_tags:
                logger.info(f"📋 No managed tags found for adapter {self.adapter_id}")
                return

            # Convert to adapter config format
            managed_tags = []
            for tag in adapter_tags:
                managed_tags.append({
                    'tag_id': tag.get('tag_id'),  # Use the configured tag_id!
                    'name': tag.get('tag_name') or tag.get('name'),
                    'tag_name': tag.get('tag_name') or tag.get('name'),
                    'address': tag.get('address'),
                    'data_type': tag.get('data_type', 'double')
                })

            if managed_tags:
                self.config.tags = managed_tags
                logger.info(f"✅ Loaded {len(managed_tags)} managed tags from tags_config.json")
                for tag in managed_tags:
                    logger.debug(f"   📌 {tag['tag_id']}: {tag['name']} @ {tag['address']}")
            else:
                logger.info("📋 No managed tags found in tags_config.json")

        except Exception as e:
            logger.error(f"❌ Error loading managed tags: {e}", exc_info=True)

    async def _discover_tags(self):
        """
        Auto-discover tags from OPC UA server

        Browses the server namespace and finds all readable variables
        """
        try:
            from asyncua import ua

            logger.info("🔍 Starting OPC UA tag discovery...")

            # Get namespace array
            namespaces = await self.client.get_namespace_array()
            logger.info(f"📋 Found {len(namespaces)} namespaces")

            # Browse from Objects node (standard starting point)
            objects_node = self.client.get_node("ns=0;i=85")  # Objects folder

            discovered_tags = []

            async def browse_node(node, depth=0, max_depth=10):
                """Recursively browse nodes"""
                if depth > max_depth:
                    return

                try:
                    # Get node class
                    node_class = await node.read_node_class()

                    # If it's a variable, check if readable
                    if node_class == ua.NodeClass.Variable:
                        try:
                            # Check access level
                            access_level = await node.read_attribute(ua.AttributeIds.AccessLevel)
                            readable = (access_level.Value.Value & 0x01) != 0

                            if readable:
                                # Get node ID and browse name
                                node_id = node.nodeid.to_string()
                                browse_name = await node.read_browse_name()
                                display_name = await node.read_display_name()

                                # Only add tags from namespace 2 (application namespace)
                                if node_id.startswith('ns=2;'):
                                    tag_name = display_name.Text or browse_name.Name

                                    # Try to get data type
                                    data_type = 'variant'
                                    try:
                                        data_type_node = await node.read_data_type()
                                        if data_type_node:
                                            dt_str = str(data_type_node)
                                            # Map OPC UA types to common names
                                            if 'Double' in dt_str:
                                                data_type = 'double'
                                            elif 'Float' in dt_str:
                                                data_type = 'float'
                                            elif 'Int32' in dt_str or 'Int16' in dt_str:
                                                data_type = 'int32'
                                            elif 'Int64' in dt_str:
                                                data_type = 'int64'
                                            elif 'Boolean' in dt_str:
                                                data_type = 'boolean'
                                            elif 'String' in dt_str:
                                                data_type = 'string'
                                            elif 'Byte' in dt_str or 'UInt' in dt_str:
                                                data_type = 'uint32'
                                    except Exception:
                                        pass  # Keep default 'variant'

                                    # Generate tag_id from node_id hash for consistency
                                    tag_id = f"tag_{hashlib.md5(node_id.encode()).hexdigest()[:8]}"

                                    discovered_tags.append({
                                        'name': tag_name,
                                        'tag_name': tag_name,
                                        'tag_id': tag_id,
                                        'address': node_id,
                                        'data_type': data_type
                                    })
                                    logger.debug(f"  ✓ Found tag: {tag_name} (id={tag_id}, node={node_id}) type={data_type}")
                        except Exception:
                            pass  # Skip nodes we can't read

                    # Browse children
                    children = await node.get_children()
                    for child in children:
                        await browse_node(child, depth + 1, max_depth)

                except Exception as e:
                    logger.debug(f"  ⚠️  Error browsing node at depth {depth}: {e}")

            # Start browsing
            await browse_node(objects_node)

            logger.info(f"✅ Discovery complete - Found {len(discovered_tags)} readable tags")

            # Update config with discovered tags
            if discovered_tags:
                self.config.tags = discovered_tags
                logger.info(f"📊 Configured {len(discovered_tags)} tags for monitoring")
            else:
                logger.warning("⚠️  No tags discovered - check OPC UA server configuration")

        except Exception as e:
            logger.error(f"❌ Tag discovery failed: {e}", exc_info=True)

    async def health_check(self) -> bool:
        """Check if connection is still alive"""
        if not self.connected or not self.client:
            return False

        try:
            # Try to read server status
            server_state = await self.client.get_node("ns=0;i=2259").read_value()  # ServerState
            return True
        except Exception as e:
            logger.warning(f"⚠️  Health check failed: {e}")
            return False

    async def read_all_discovered_tags(self) -> List[Dict[str, Any]]:
        """
        Read current values for ALL discovered tags directly from OPC-UA server

        This bypasses the subscription cache and reads values directly.
        Used by the Gateway UI to show real-time values for all tags.

        Returns:
            List of dicts with tag info and current values
        """
        if not self.connected or not self.client:
            logger.warning("Cannot read tags - not connected to OPC-UA server")
            return []

        results = []

        # Use tags from config (which includes discovered tags)
        tags_to_read = self.config.tags if hasattr(self.config, 'tags') else []

        if not tags_to_read:
            logger.warning("No tags configured/discovered to read")
            return []

        logger.info(f"📖 Reading {len(tags_to_read)} tags directly from OPC-UA server...")

        for tag in tags_to_read:
            tag_addr = tag.get('address', '')
            tag_name = tag.get('name') or tag.get('tag_name', tag_addr)

            try:
                # Get node and read value directly
                node = self.client.get_node(tag_addr)
                data_value = await node.read_data_value()

                # Extract value
                value = data_value.Value.Value if data_value.Value else None

                # Extract quality
                quality = 'Good'
                if hasattr(data_value, 'StatusCode') and data_value.StatusCode:
                    if hasattr(data_value.StatusCode, 'is_good'):
                        quality = 'Good' if data_value.StatusCode.is_good() else 'Bad'
                    elif hasattr(data_value.StatusCode, 'value'):
                        quality = 'Good' if data_value.StatusCode.value == 0 else 'Bad'

                # Extract timestamp
                timestamp = None
                if hasattr(data_value, 'SourceTimestamp') and data_value.SourceTimestamp:
                    timestamp = data_value.SourceTimestamp.isoformat()
                elif hasattr(data_value, 'ServerTimestamp') and data_value.ServerTimestamp:
                    timestamp = data_value.ServerTimestamp.isoformat()

                # Also update last_values cache
                self.last_values[tag_addr] = {
                    'value': value,
                    'quality': quality,
                    'timestamp': timestamp
                }

                results.append({
                    "name": tag_name,
                    "address": tag_addr,
                    "current_value": value,
                    "quality": quality,
                    "data_type": tag.get('data_type', tag.get('type', 'variant')),
                    "unit": tag.get('unit'),
                    "last_update": timestamp,
                    "connected": True
                })

            except Exception as e:
                logger.debug(f"⚠️  Failed to read tag {tag_name} ({tag_addr}): {e}")
                results.append({
                    "name": tag_name,
                    "address": tag_addr,
                    "current_value": None,
                    "quality": "Bad",
                    "data_type": tag.get('data_type', tag.get('type', 'variant')),
                    "unit": tag.get('unit'),
                    "last_update": None,
                    "connected": False,
                    "error": str(e)
                })

        logger.info(f"✅ Read {len([r for r in results if r['connected']])} tags successfully")
        return results


def create_opcua_adapter(
    adapter_id: str,
    host: str,
    port: int = 4840,
    tags: List[Dict[str, str]] = None,
    scan_rate_ms: int = 1000,
    username: Optional[str] = None,
    password: Optional[str] = None,
    **kwargs
) -> OPCUAAdapter:
    """
    Convenience function to create OPC UA adapter

    Args:
        adapter_id: Unique adapter identifier
        host: OPC UA server host
        port: OPC UA server port (default: 4840)
        tags: List of tags to monitor [{'name': 'tag1', 'address': 'ns=2;i=1'}]
        scan_rate_ms: How often to publish buffered tags (default: 1000ms)
        username: Optional username for authentication
        password: Optional password for authentication
        **kwargs: Additional configuration options

    Returns:
        Configured OPC UA adapter instance
    """
    config = ProtocolConfig(
        adapter_id=adapter_id,
        protocol_type='opcua',
        host=host,
        port=port,
        scan_rate_ms=scan_rate_ms,
        tags=tags or [],
        extra_config={
            'username': username,
            'password': password,
            'subscription_interval': kwargs.get('subscription_interval', 100),
            **kwargs
        }
    )

    return OPCUAAdapter(config)
