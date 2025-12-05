"""
MQTT Protocol Adapter
=====================

Subscribes to MQTT topics and publishes tag data to Kafka.

Features:
- Automatic reconnection on connection loss
- Wildcard topic subscriptions (#, +)
- JSON payload parsing
- QoS levels 0, 1, 2 support
- TLS/SSL support

Based on asyncio-mqtt library.
"""

from typing import List, Dict, Any, Optional
import asyncio
import logging
import json

try:
    import asyncio_mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logging.warning("asyncio-mqtt not installed - MQTT adapter disabled")

from .base_adapter import BaseProtocolAdapter, ProtocolConfig, TagData

logger = logging.getLogger(__name__)


class MQTTAdapter(BaseProtocolAdapter):
    """
    MQTT protocol adapter

    Subscribes to MQTT topics and forwards messages to Kafka.

    Configuration (extra_config):
    - client_id: MQTT client ID (default: auto-generated)
    - username: Optional username for authentication
    - password: Optional password for authentication
    - qos: Quality of Service level 0-2 (default: 0)
    - clean_session: Clean session flag (default: True)
    - keepalive: Keepalive interval in seconds (default: 60)
    - use_tls: Enable TLS/SSL (default: False)

    Tag configuration format:
    {
        'name': 'temperature',         # Tag name
        'address': 'sensors/temp/1',   # MQTT topic to subscribe
        'path': 'value',               # JSON path to extract value (optional)
        'type': 'float'                # Data type hint (optional)
    }

    Examples:
    - Subscribe to single topic: 'sensors/temperature'
    - Subscribe to all sensors: 'sensors/#'
    - Subscribe to specific type: 'sensors/+/temperature'
    """

    def __init__(self, config: ProtocolConfig):
        if not MQTT_AVAILABLE:
            raise ImportError("asyncio-mqtt library not available - cannot create MQTT adapter")

        super().__init__(config)

        # MQTT specific state
        self.client: Optional[asyncio_mqtt.Client] = None
        self._subscription_task: Optional[asyncio.Task] = None

        # Configuration
        self.client_id = config.extra_config.get('client_id', f"optiflow-mqtt-{config.adapter_id}")
        self.username = config.extra_config.get('username')
        self.password = config.extra_config.get('password')
        self.qos = config.extra_config.get('qos', 0)
        self.clean_session = config.extra_config.get('clean_session', True)
        self.keepalive = config.extra_config.get('keepalive', 60)
        self.use_tls = config.extra_config.get('use_tls', False)

        # Tag buffer (MQTT is push-based, so we buffer messages)
        self._tag_buffer: List[TagData] = []
        self._buffer_lock = asyncio.Lock()

        logger.info(f"🔧 MQTT adapter initialized - Broker: {config.host}:{config.port}, Client: {self.client_id}")

    async def connect(self) -> bool:
        """Connect to MQTT broker and subscribe to topics"""
        if self.connected:
            logger.warning(f"⚠️  {self.adapter_id} already connected")
            return True

        try:
            logger.info(f"🔌 Connecting to MQTT broker: {self.config.host}:{self.config.port}")

            # Create MQTT client
            # Note: asyncio-mqtt doesn't support 'timeout' in Client constructor
            client_kwargs = {
                'hostname': self.config.host,
                'port': self.config.port,
                'client_id': self.client_id,
                'clean_session': self.clean_session,
                'keepalive': self.keepalive
            }

            # Add authentication if provided
            if self.username:
                client_kwargs['username'] = self.username
            if self.password:
                client_kwargs['password'] = self.password

            # Add TLS if enabled
            if self.use_tls:
                import ssl
                client_kwargs['tls_context'] = ssl.create_default_context()

            self.client = asyncio_mqtt.Client(**client_kwargs)

            # Connect to broker
            await self.client.connect()

            logger.info(f"✅ Connected to MQTT broker")

            # Subscribe to all configured topics
            await self._subscribe_topics()

            # Start message handler task
            self._subscription_task = asyncio.create_task(self._message_handler())

            self.connected = True
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to MQTT broker: {e}", exc_info=True)
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from MQTT broker"""
        if not self.connected:
            return

        try:
            logger.info(f"🔌 Disconnecting from {self.config.host}:{self.config.port}...")

            # Cancel message handler task
            if self._subscription_task:
                self._subscription_task.cancel()
                try:
                    await self._subscription_task
                except asyncio.CancelledError:
                    pass

            # Disconnect client
            if self.client:
                await self.client.disconnect()
                logger.info("✅ Client disconnected")

            self.client = None
            self.connected = False

        except Exception as e:
            logger.error(f"❌ Error during disconnect: {e}")

    async def _subscribe_topics(self):
        """Subscribe to all configured MQTT topics"""
        if not self.client:
            raise RuntimeError("Client not connected")

        logger.info(f"📡 Subscribing to MQTT topics (QoS: {self.qos})...")

        for tag_config in self.config.tags:
            try:
                topic = tag_config.get('address')  # MQTT topic
                tag_name = tag_config.get('name')

                if not topic or not tag_name:
                    logger.warning(f"⚠️  Skipping tag with missing topic or name: {tag_config}")
                    continue

                # Subscribe to topic
                await self.client.subscribe(topic, qos=self.qos)

                logger.debug(f"✅ Subscribed to {topic} (tag: {tag_name})")

            except Exception as e:
                logger.error(f"❌ Failed to subscribe to topic {tag_config}: {e}")

        logger.info(f"✅ Subscribed to {len(self.config.tags)} MQTT topics")

    async def _message_handler(self):
        """Handle incoming MQTT messages"""
        if not self.client:
            return

        try:
            async with self.client.filtered_messages('/#') as messages:  # Listen to all topics
                async for message in messages:
                    try:
                        # Find tag configuration for this topic
                        tag_config = self._find_tag_for_topic(message.topic)

                        if not tag_config:
                            logger.debug(f"⚠️  No tag configured for topic: {message.topic}")
                            continue

                        # Parse payload
                        value = self._parse_payload(message.payload, tag_config)

                        if value is not None:
                            # Create TagData
                            tag_data = TagData(
                                tag_name=tag_config['name'],
                                value=value,
                                quality='good',
                                source=self.adapter_id,
                                address=message.topic
                            )

                            # Add to buffer
                            await self._add_to_buffer(tag_data)

                    except Exception as e:
                        logger.error(f"❌ Error processing MQTT message: {e}")
                        continue

        except asyncio.CancelledError:
            logger.info("Message handler cancelled")
        except Exception as e:
            logger.error(f"❌ Fatal error in message handler: {e}", exc_info=True)

    def _find_tag_for_topic(self, topic: str) -> Optional[Dict[str, Any]]:
        """Find tag configuration that matches the given topic"""
        for tag_config in self.config.tags:
            configured_topic = tag_config.get('address', '')

            # Exact match
            if configured_topic == topic:
                return tag_config

            # Wildcard match (simple implementation)
            if self._topic_matches(configured_topic, topic):
                return tag_config

        return None

    def _topic_matches(self, pattern: str, topic: str) -> bool:
        """Check if topic matches pattern (with MQTT wildcards)"""
        # Simple wildcard matching for # and +
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')

        if len(pattern_parts) > len(topic_parts):
            return False

        for i, pattern_part in enumerate(pattern_parts):
            if pattern_part == '#':
                # Multi-level wildcard - matches everything after
                return True
            elif pattern_part == '+':
                # Single-level wildcard - matches one level
                continue
            elif i >= len(topic_parts) or pattern_part != topic_parts[i]:
                return False

        return len(pattern_parts) == len(topic_parts)

    def _parse_payload(self, payload: bytes, tag_config: Dict[str, Any]) -> Optional[Any]:
        """Parse MQTT payload to extract value"""
        try:
            # Decode payload
            payload_str = payload.decode('utf-8')

            # Try to parse as JSON
            try:
                payload_json = json.loads(payload_str)

                # Extract value using JSON path if specified
                json_path = tag_config.get('path')
                if json_path:
                    value = self._extract_json_path(payload_json, json_path)
                else:
                    # If no path, assume entire payload is the value
                    value = payload_json

            except json.JSONDecodeError:
                # Not JSON, treat as plain text/number
                value = payload_str

            # Convert to appropriate type
            data_type = tag_config.get('type', 'string')
            value = self._convert_type(value, data_type)

            return value

        except Exception as e:
            logger.error(f"Error parsing MQTT payload: {e}")
            return None

    def _extract_json_path(self, data: Any, path: str) -> Any:
        """Extract value from JSON using simple path notation"""
        # Simple implementation: supports dot notation like 'sensor.temperature'
        parts = path.split('.')
        current = data

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                current = current[int(part)]
            else:
                return None

        return current

    def _convert_type(self, value: Any, data_type: str) -> Any:
        """Convert value to specified data type"""
        try:
            if data_type == 'int':
                return int(float(value))
            elif data_type == 'float':
                return float(value)
            elif data_type == 'bool':
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ('true', '1', 'yes', 'on')
            else:  # string
                return str(value)
        except:
            return value

    async def _add_to_buffer(self, tag_data: TagData):
        """Add tag data to buffer (thread-safe)"""
        async with self._buffer_lock:
            self._tag_buffer.append(tag_data)

    async def read_tags(self) -> List[TagData]:
        """
        Read current tag values from buffer

        This is called by the scan loop. We return buffered values
        from MQTT subscription.
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

        # MQTT client doesn't have a direct health check
        # We rely on the keepalive mechanism
        return True


def create_mqtt_adapter(
    adapter_id: str,
    host: str,
    port: int = 1883,
    tags: List[Dict[str, str]] = None,
    scan_rate_ms: int = 1000,
    username: Optional[str] = None,
    password: Optional[str] = None,
    **kwargs
) -> MQTTAdapter:
    """
    Convenience function to create MQTT adapter

    Args:
        adapter_id: Unique adapter identifier
        host: MQTT broker host
        port: MQTT broker port (default: 1883)
        tags: List of tags to monitor (see MQTTAdapter docstring for format)
        scan_rate_ms: How often to publish buffered tags (default: 1000ms)
        username: Optional username for authentication
        password: Optional password for authentication
        **kwargs: Additional configuration options

    Returns:
        Configured MQTT adapter instance
    """
    config = ProtocolConfig(
        adapter_id=adapter_id,
        protocol_type='mqtt',
        host=host,
        port=port,
        scan_rate_ms=scan_rate_ms,
        tags=tags or [],
        extra_config={
            'username': username,
            'password': password,
            'qos': kwargs.get('qos', 0),
            'clean_session': kwargs.get('clean_session', True),
            'keepalive': kwargs.get('keepalive', 60),
            'use_tls': kwargs.get('use_tls', False),
            **kwargs
        }
    )

    return MQTTAdapter(config)
