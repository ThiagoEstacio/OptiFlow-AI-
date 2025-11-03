"""
MQTT Protocol Handler
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import json
import asyncio
from asyncio_mqtt import Client as AsyncMQTTClient, MqttError

from ..core.base_protocol import BaseProtocolHandler, TagValue
from ..core.logger import logger


class MQTTHandler(BaseProtocolHandler):
    """
    MQTT protocol handler using asyncio-mqtt library
    """

    def __init__(self, device_id: str, config: Dict[str, Any]):
        """
        Initialize MQTT handler

        Config keys:
            - host: MQTT broker host
            - port: MQTT broker port (default: 1883)
            - username: Optional username
            - password: Optional password
            - client_id: MQTT client ID (default: gateway-{device_id})
            - keepalive: Keepalive interval in seconds (default: 60)
            - qos: Quality of Service (0, 1, 2) (default: 1)
            - topic_prefix: Topic prefix (e.g., "plant/area1")
        """
        super().__init__(device_id, config)

        self.host = config.get("host")
        self.port = config.get("port", 1883)
        self.username = config.get("username")
        self.password = config.get("password")
        self.client_id = config.get("client_id", f"gateway-{device_id}")
        self.keepalive = config.get("keepalive", 60)
        self.qos = config.get("qos", 1)
        self.topic_prefix = config.get("topic_prefix", "")

        self.client: Optional[AsyncMQTTClient] = None
        self._subscriptions: Dict[str, TagValue] = {}  # topic -> latest value
        self._callbacks: Dict[str, List[Callable]] = {}  # topic -> callbacks
        self._listen_task: Optional[asyncio.Task] = None

    async def connect(self) -> bool:
        """Connect to MQTT broker"""
        async with self._lock:
            try:
                logger.info(f"Connecting to MQTT broker: {self.host}:{self.port}")

                # Create client
                self.client = AsyncMQTTClient(
                    hostname=self.host,
                    port=self.port,
                    username=self.username if self.username else None,
                    password=self.password if self.password else None,
                    client_id=self.client_id,
                    keepalive=self.keepalive
                )

                # Connect
                await self.client.__aenter__()

                self.update_status(connected=True)
                logger.info(f"✓ Connected to MQTT broker: {self.host}:{self.port}")

                # Start listening task
                self._listen_task = asyncio.create_task(self._listen_loop())

                return True

            except Exception as e:
                error_msg = f"MQTT connection failed: {str(e)}"
                logger.error(error_msg)
                self.update_status(connected=False, error=error_msg)
                return False

    async def disconnect(self) -> bool:
        """Disconnect from MQTT broker"""
        async with self._lock:
            try:
                # Cancel listening task
                if self._listen_task:
                    self._listen_task.cancel()
                    try:
                        await self._listen_task
                    except asyncio.CancelledError:
                        pass

                # Disconnect client
                if self.client:
                    await self.client.__aexit__(None, None, None)
                    self.client = None

                self._subscriptions.clear()
                self.update_status(connected=False)
                logger.info("Disconnected from MQTT broker")
                return True

            except Exception as e:
                logger.error(f"MQTT disconnect error: {str(e)}")
                return False

    def _build_topic(self, tag_address: str) -> str:
        """Build full topic from address"""
        if self.topic_prefix:
            return f"{self.topic_prefix}/{tag_address}"
        return tag_address

    async def subscribe(self, topic: str, callback: Optional[Callable] = None) -> bool:
        """
        Subscribe to MQTT topic

        Args:
            topic: Topic to subscribe
            callback: Optional callback function for messages

        Returns:
            True if subscription successful
        """
        try:
            if not self.is_connected:
                await self.connect()

            if not self.client:
                return False

            full_topic = self._build_topic(topic)

            await self.client.subscribe(full_topic, qos=self.qos)

            if callback:
                if full_topic not in self._callbacks:
                    self._callbacks[full_topic] = []
                self._callbacks[full_topic].append(callback)

            logger.info(f"✓ Subscribed to MQTT topic: {full_topic}")
            return True

        except Exception as e:
            logger.error(f"Failed to subscribe to {topic}: {str(e)}")
            return False

    async def _listen_loop(self):
        """Background task to listen for MQTT messages"""
        try:
            if not self.client:
                return

            async with self.client.messages() as messages:
                async for message in messages:
                    await self._handle_message(message)

        except asyncio.CancelledError:
            logger.info("MQTT listening task cancelled")
            raise
        except Exception as e:
            logger.error(f"MQTT listening error: {str(e)}")
            self.update_status(connected=False, error=str(e))

    async def _handle_message(self, message):
        """Handle received MQTT message"""
        try:
            topic = message.topic
            payload = message.payload.decode()

            # Try to parse as JSON
            try:
                value = json.loads(payload)
            except json.JSONDecodeError:
                # If not JSON, use raw string
                value = payload

            # Store latest value
            tag_value = TagValue(
                tag_id=topic,
                tag_name=topic,
                value=value,
                quality="good",
                timestamp=datetime.now()
            )

            self._subscriptions[topic] = tag_value

            # Call callbacks
            if topic in self._callbacks:
                for callback in self._callbacks[topic]:
                    try:
                        await callback(tag_value)
                    except Exception as e:
                        logger.error(f"Callback error for {topic}: {str(e)}")

        except Exception as e:
            logger.error(f"Error handling MQTT message: {str(e)}")

    async def read_tag(self, tag_address: str) -> Optional[TagValue]:
        """
        Read latest value from subscribed topic

        Note: MQTT is publish/subscribe, so you need to subscribe first
        """
        full_topic = self._build_topic(tag_address)

        # Return cached value if available
        if full_topic in self._subscriptions:
            return self._subscriptions[full_topic]

        # If not subscribed, subscribe and wait for first message
        await self.subscribe(tag_address)

        # Wait up to 5 seconds for a message
        for _ in range(50):
            await asyncio.sleep(0.1)
            if full_topic in self._subscriptions:
                return self._subscriptions[full_topic]

        logger.warning(f"No MQTT message received for {tag_address}")
        return None

    async def read_tags(self, tag_addresses: List[str]) -> List[TagValue]:
        """Read multiple MQTT topics"""
        results = []

        # Subscribe to all topics first
        for address in tag_addresses:
            await self.subscribe(address)

        # Wait a bit for messages
        await asyncio.sleep(1)

        # Collect values
        for address in tag_addresses:
            full_topic = self._build_topic(address)
            if full_topic in self._subscriptions:
                results.append(self._subscriptions[full_topic])

        return results

    async def write_tag(self, tag_address: str, value: Any) -> bool:
        """
        Publish value to MQTT topic

        Args:
            tag_address: Topic to publish to
            value: Value to publish (will be JSON-encoded if dict/list)

        Returns:
            True if publish successful
        """
        try:
            if not self.is_connected:
                await self.connect()

            if not self.client:
                return False

            full_topic = self._build_topic(tag_address)

            # Encode value
            if isinstance(value, (dict, list)):
                payload = json.dumps(value)
            else:
                payload = str(value)

            # Publish
            await self.client.publish(full_topic, payload.encode(), qos=self.qos)

            logger.info(f"✓ Published to MQTT topic {full_topic}: {payload}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish to {tag_address}: {str(e)}")
            self.update_status(connected=False, error=str(e))
            return False

    async def health_check(self) -> bool:
        """Check MQTT broker connection"""
        try:
            if not self.client:
                return False

            # MQTT doesn't have a direct ping, but we can try to subscribe to a test topic
            test_topic = f"{self.topic_prefix}/$SYS/broker/uptime" if self.topic_prefix else "$SYS/broker/uptime"

            try:
                await asyncio.wait_for(
                    self.client.subscribe(test_topic, qos=0),
                    timeout=5
                )
                await self.client.unsubscribe(test_topic)

                self.update_status(connected=True)
                return True

            except asyncio.TimeoutError:
                self.update_status(connected=False, error="Health check timeout")
                return False

        except Exception as e:
            logger.error(f"MQTT health check failed: {str(e)}")
            self.update_status(connected=False, error=str(e))
            return False
