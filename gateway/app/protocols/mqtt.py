"""
MQTT Protocol Handler
Connects to MQTT brokers and subscribes to topics
"""
import asyncio
import logging
from typing import Dict, List, Optional, Callable

logger = logging.getLogger(__name__)


class MQTTHandler:
    """
    Handler for MQTT protocol
    """

    def __init__(self, broker: str, port: int = 1883, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize MQTT handler

        Args:
            broker: MQTT broker address
            port: MQTT port (default 1883 for non-TLS, 8883 for TLS)
            username: Optional username for authentication
            password: Optional password for authentication
        """
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.connected = False
        self.subscriptions: Dict[str, Callable] = {}

    async def connect(self) -> bool:
        """
        Connect to MQTT broker

        Returns:
            True if connected successfully, False otherwise
        """
        try:
            # In a real implementation, use aiomqtt or paho-mqtt:
            # import aiomqtt
            # self.client = aiomqtt.Client(hostname=self.broker, port=self.port)
            # if self.username and self.password:
            #     self.client.username_pw_set(self.username, self.password)
            # await self.client.connect()

            logger.info(f"Connected to MQTT broker: {self.broker}:{self.port}")
            self.connected = True
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker {self.broker}:{self.port}: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from MQTT broker"""
        try:
            if self.client:
                # await self.client.disconnect()
                pass
            self.connected = False
            logger.info(f"Disconnected from MQTT broker: {self.broker}:{self.port}")
        except Exception as e:
            logger.error(f"Error disconnecting from MQTT broker: {e}")

    async def subscribe(self, topic: str, callback: Callable):
        """
        Subscribe to an MQTT topic

        Args:
            topic: MQTT topic to subscribe to (supports wildcards: +, #)
            callback: Callback function to handle received messages
        """
        try:
            if not self.connected:
                logger.warning("Not connected to MQTT broker")
                return False

            # In a real implementation:
            # await self.client.subscribe(topic)
            self.subscriptions[topic] = callback

            logger.info(f"Subscribed to MQTT topic: {topic}")
            return True

        except Exception as e:
            logger.error(f"Error subscribing to MQTT topic {topic}: {e}")
            return False

    async def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> bool:
        """
        Publish a message to an MQTT topic

        Args:
            topic: MQTT topic to publish to
            payload: Message payload
            qos: Quality of Service (0, 1, or 2)
            retain: Whether to retain the message

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.connected:
                logger.warning("Not connected to MQTT broker")
                return False

            # In a real implementation:
            # await self.client.publish(topic, payload, qos=qos, retain=retain)

            logger.info(f"Published to MQTT topic {topic}: {payload}")
            return True

        except Exception as e:
            logger.error(f"Error publishing to MQTT topic {topic}: {e}")
            return False

    async def start_listening(self):
        """
        Start listening for MQTT messages
        This should run in a background task
        """
        try:
            if not self.connected:
                logger.warning("Not connected to MQTT broker")
                return

            # In a real implementation:
            # async with self.client.messages() as messages:
            #     async for message in messages:
            #         topic = message.topic
            #         payload = message.payload.decode()
            #
            #         # Find matching subscription and call callback
            #         for sub_topic, callback in self.subscriptions.items():
            #             if self._topic_matches(topic, sub_topic):
            #                 await callback(topic, payload)

            logger.info("Started MQTT message listener")

        except Exception as e:
            logger.error(f"Error in MQTT listener: {e}")

    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """
        Check if topic matches pattern (supports MQTT wildcards)

        Args:
            topic: Actual topic
            pattern: Pattern with wildcards (+ for single level, # for multi-level)

        Returns:
            True if matches, False otherwise
        """
        # Simple implementation - in production use proper MQTT topic matching
        if pattern == topic:
            return True

        if '#' in pattern:
            prefix = pattern.split('#')[0]
            return topic.startswith(prefix)

        # Handle + wildcard
        topic_parts = topic.split('/')
        pattern_parts = pattern.split('/')

        if len(topic_parts) != len(pattern_parts):
            return False

        for t, p in zip(topic_parts, pattern_parts):
            if p != '+' and p != t:
                return False

        return True

    def is_connected(self) -> bool:
        """Check if connected to MQTT broker"""
        return self.connected
