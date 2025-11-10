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
import logging

try:
    from asyncua import Client, ua
    from asyncua.common.subscription import Subscription
    OPCUA_AVAILABLE = True
except ImportError:
    OPCUA_AVAILABLE = False
    logging.warning("asyncua not installed - OPC UA adapter disabled")

from .base_adapter import BaseProtocolAdapter, ProtocolConfig, TagData

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

            # Create subscription
            await self._create_subscription()

            self.connected = True
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to OPC UA server: {e}", exc_info=True)
            self.connected = False
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

        except Exception as e:
            logger.error(f"❌ Error during disconnect: {e}")

    async def _create_subscription(self):
        """Create OPC UA subscription for monitoring tags"""
        if not self.client:
            raise RuntimeError("Client not connected")

        try:
            logger.info(f"📡 Creating OPC UA subscription (interval: {self.subscription_interval}ms)...")

            # Create subscription
            self.subscription = await self.client.create_subscription(
                period=self.subscription_interval,
                handler=self._subscription_handler
            )

            # Subscribe to all configured tags
            for tag_config in self.config.tags:
                try:
                    node_id = tag_config.get('address')  # OPC UA node ID
                    tag_name = tag_config.get('name')

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
                        'node': node
                    }

                    logger.debug(f"✅ Subscribed to {tag_name} ({node_id})")

                except Exception as e:
                    logger.error(f"❌ Failed to subscribe to tag {tag_config}: {e}")

            logger.info(f"✅ Subscription created - Monitoring {len(self._monitored_items)} tags")

        except Exception as e:
            logger.error(f"❌ Failed to create subscription: {e}", exc_info=True)
            raise

    def _subscription_handler(self, node, value, data):
        """
        Callback for subscription data changes

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

            # Determine quality
            quality = 'good'
            if hasattr(data, 'StatusCode'):
                if not data.StatusCode.is_good():
                    quality = 'bad'
                elif data.StatusCode.name == 'Uncertain':
                    quality = 'uncertain'

            # Create TagData
            tag_data = TagData(
                tag_name=tag_name,
                value=value,
                quality=quality,
                source=self.adapter_id,
                address=node_id
            )

            # Add to buffer (will be published in scan loop)
            # Using asyncio.create_task to not block the callback
            asyncio.create_task(self._add_to_buffer(tag_data))

        except Exception as e:
            logger.error(f"❌ Error in subscription handler: {e}", exc_info=True)

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
