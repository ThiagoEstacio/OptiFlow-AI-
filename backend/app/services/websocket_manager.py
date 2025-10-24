"""
WebSocket Manager for Real-Time Data Streaming

Manages WebSocket connections for live data updates to dashboards.
Supports:
- Tag subscription (subscribe to specific tags)
- Broadcast updates to subscribers
- Connection management
- Room-based subscriptions (by organization, site, device)
"""
from typing import Dict, Set, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import asyncio
import json
from datetime import datetime
from fastapi import WebSocket
from uuid import UUID

from loguru import logger


@dataclass
class Subscription:
    """Represents a subscription to tag updates"""
    connection_id: str
    websocket: WebSocket
    tag_ids: Set[str] = field(default_factory=set)
    rooms: Set[str] = field(default_factory=set)  # organization_id, site_id, device_id
    last_activity: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for logging"""
        return {
            "connection_id": self.connection_id,
            "tag_count": len(self.tag_ids),
            "rooms": list(self.rooms),
            "last_activity": self.last_activity.isoformat()
        }


@dataclass
class TagUpdate:
    """Represents a tag value update"""
    tag_id: str
    value: Any
    quality: str
    timestamp: float
    device_id: Optional[str] = None
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "tag_id": self.tag_id,
            "value": self.value,
            "quality": self.quality,
            "timestamp": self.timestamp,
            "device_id": self.device_id,
            "metadata": self.metadata or {}
        }


class WebSocketManager:
    """
    Manages WebSocket connections and real-time data subscriptions.

    Features:
    - Connection lifecycle management
    - Tag-based subscriptions
    - Room-based broadcasting
    - Connection cleanup
    - Health monitoring
    """

    def __init__(self):
        # Active connections: connection_id -> Subscription
        self.active_connections: Dict[str, Subscription] = {}

        # Tag subscriptions: tag_id -> set of connection_ids
        self.tag_subscriptions: Dict[str, Set[str]] = defaultdict(set)

        # Room subscriptions: room_id -> set of connection_ids
        self.room_subscriptions: Dict[str, Set[str]] = defaultdict(set)

        # Statistics
        self.total_connections = 0
        self.total_messages_sent = 0
        self.total_messages_received = 0

        logger.info("WebSocketManager initialized")

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str
    ) -> None:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            connection_id: Unique connection identifier
        """
        await websocket.accept()

        subscription = Subscription(
            connection_id=connection_id,
            websocket=websocket
        )

        self.active_connections[connection_id] = subscription
        self.total_connections += 1

        logger.info(f"WebSocket connected: {connection_id} (total: {len(self.active_connections)})")

        # Send welcome message
        await self.send_personal_message({
            "type": "connected",
            "connection_id": connection_id,
            "timestamp": datetime.now().timestamp()
        }, connection_id)

    async def disconnect(self, connection_id: str) -> None:
        """
        Disconnect and cleanup a WebSocket connection.

        Args:
            connection_id: Connection to disconnect
        """
        if connection_id not in self.active_connections:
            return

        subscription = self.active_connections[connection_id]

        # Remove from tag subscriptions
        for tag_id in subscription.tag_ids:
            if tag_id in self.tag_subscriptions:
                self.tag_subscriptions[tag_id].discard(connection_id)
                if not self.tag_subscriptions[tag_id]:
                    del self.tag_subscriptions[tag_id]

        # Remove from room subscriptions
        for room in subscription.rooms:
            if room in self.room_subscriptions:
                self.room_subscriptions[room].discard(connection_id)
                if not self.room_subscriptions[room]:
                    del self.room_subscriptions[room]

        # Remove connection
        del self.active_connections[connection_id]

        logger.info(f"WebSocket disconnected: {connection_id} (total: {len(self.active_connections)})")

    async def subscribe_to_tags(
        self,
        connection_id: str,
        tag_ids: List[str]
    ) -> None:
        """
        Subscribe connection to specific tags.

        Args:
            connection_id: Connection identifier
            tag_ids: List of tag IDs to subscribe to
        """
        if connection_id not in self.active_connections:
            logger.warning(f"Cannot subscribe: connection {connection_id} not found")
            return

        subscription = self.active_connections[connection_id]

        for tag_id in tag_ids:
            subscription.tag_ids.add(tag_id)
            self.tag_subscriptions[tag_id].add(connection_id)

        logger.info(f"Connection {connection_id} subscribed to {len(tag_ids)} tags")

        # Send acknowledgment
        await self.send_personal_message({
            "type": "subscribed",
            "tag_ids": tag_ids,
            "timestamp": datetime.now().timestamp()
        }, connection_id)

    async def unsubscribe_from_tags(
        self,
        connection_id: str,
        tag_ids: List[str]
    ) -> None:
        """
        Unsubscribe connection from specific tags.

        Args:
            connection_id: Connection identifier
            tag_ids: List of tag IDs to unsubscribe from
        """
        if connection_id not in self.active_connections:
            return

        subscription = self.active_connections[connection_id]

        for tag_id in tag_ids:
            subscription.tag_ids.discard(tag_id)
            if tag_id in self.tag_subscriptions:
                self.tag_subscriptions[tag_id].discard(connection_id)
                if not self.tag_subscriptions[tag_id]:
                    del self.tag_subscriptions[tag_id]

        logger.info(f"Connection {connection_id} unsubscribed from {len(tag_ids)} tags")

    async def join_room(
        self,
        connection_id: str,
        room_id: str
    ) -> None:
        """
        Join a room for group subscriptions.

        Rooms can be organization_id, site_id, or device_id.

        Args:
            connection_id: Connection identifier
            room_id: Room identifier
        """
        if connection_id not in self.active_connections:
            return

        subscription = self.active_connections[connection_id]
        subscription.rooms.add(room_id)
        self.room_subscriptions[room_id].add(connection_id)

        logger.info(f"Connection {connection_id} joined room {room_id}")

    async def leave_room(
        self,
        connection_id: str,
        room_id: str
    ) -> None:
        """
        Leave a room.

        Args:
            connection_id: Connection identifier
            room_id: Room identifier
        """
        if connection_id not in self.active_connections:
            return

        subscription = self.active_connections[connection_id]
        subscription.rooms.discard(room_id)

        if room_id in self.room_subscriptions:
            self.room_subscriptions[room_id].discard(connection_id)
            if not self.room_subscriptions[room_id]:
                del self.room_subscriptions[room_id]

        logger.info(f"Connection {connection_id} left room {room_id}")

    async def send_personal_message(
        self,
        message: dict,
        connection_id: str
    ) -> bool:
        """
        Send message to a specific connection.

        Args:
            message: Message dictionary to send
            connection_id: Target connection

        Returns:
            True if sent successfully, False otherwise
        """
        if connection_id not in self.active_connections:
            return False

        subscription = self.active_connections[connection_id]

        try:
            await subscription.websocket.send_json(message)
            subscription.last_activity = datetime.now()
            self.total_messages_sent += 1
            return True
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False

    async def broadcast_tag_update(
        self,
        tag_update: TagUpdate
    ) -> int:
        """
        Broadcast tag update to all subscribers.

        Args:
            tag_update: Tag update to broadcast

        Returns:
            Number of connections notified
        """
        tag_id = tag_update.tag_id

        if tag_id not in self.tag_subscriptions:
            return 0

        subscribers = self.tag_subscriptions[tag_id].copy()

        message = {
            "type": "tag_update",
            "data": tag_update.to_dict()
        }

        sent_count = 0
        failed_connections = []

        for connection_id in subscribers:
            success = await self.send_personal_message(message, connection_id)
            if success:
                sent_count += 1
            else:
                failed_connections.append(connection_id)

        # Cleanup failed connections
        for connection_id in failed_connections:
            await self.disconnect(connection_id)

        return sent_count

    async def broadcast_to_room(
        self,
        room_id: str,
        message: dict
    ) -> int:
        """
        Broadcast message to all connections in a room.

        Args:
            room_id: Room identifier
            message: Message to broadcast

        Returns:
            Number of connections notified
        """
        if room_id not in self.room_subscriptions:
            return 0

        subscribers = self.room_subscriptions[room_id].copy()

        sent_count = 0
        for connection_id in subscribers:
            success = await self.send_personal_message(message, connection_id)
            if success:
                sent_count += 1

        return sent_count

    async def broadcast_to_all(
        self,
        message: dict
    ) -> int:
        """
        Broadcast message to all active connections.

        Args:
            message: Message to broadcast

        Returns:
            Number of connections notified
        """
        connections = list(self.active_connections.keys())

        sent_count = 0
        for connection_id in connections:
            success = await self.send_personal_message(message, connection_id)
            if success:
                sent_count += 1

        return sent_count

    async def handle_message(
        self,
        connection_id: str,
        message: dict
    ) -> None:
        """
        Handle incoming WebSocket message.

        Args:
            connection_id: Connection identifier
            message: Received message
        """
        self.total_messages_received += 1

        message_type = message.get("type")

        if message_type == "subscribe":
            tag_ids = message.get("tag_ids", [])
            await self.subscribe_to_tags(connection_id, tag_ids)

        elif message_type == "unsubscribe":
            tag_ids = message.get("tag_ids", [])
            await self.unsubscribe_from_tags(connection_id, tag_ids)

        elif message_type == "join_room":
            room_id = message.get("room_id")
            if room_id:
                await self.join_room(connection_id, room_id)

        elif message_type == "leave_room":
            room_id = message.get("room_id")
            if room_id:
                await self.leave_room(connection_id, room_id)

        elif message_type == "ping":
            await self.send_personal_message({
                "type": "pong",
                "timestamp": datetime.now().timestamp()
            }, connection_id)

        else:
            logger.warning(f"Unknown message type: {message_type}")

    def get_statistics(self) -> dict:
        """
        Get WebSocket manager statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "active_connections": len(self.active_connections),
            "total_connections": self.total_connections,
            "tag_subscriptions": len(self.tag_subscriptions),
            "room_subscriptions": len(self.room_subscriptions),
            "total_messages_sent": self.total_messages_sent,
            "total_messages_received": self.total_messages_received
        }

    def get_connection_info(self, connection_id: str) -> Optional[dict]:
        """
        Get information about a specific connection.

        Args:
            connection_id: Connection identifier

        Returns:
            Connection info dict or None
        """
        if connection_id not in self.active_connections:
            return None

        return self.active_connections[connection_id].to_dict()

    async def cleanup_inactive_connections(self, timeout_seconds: int = 300) -> int:
        """
        Cleanup connections inactive for longer than timeout.

        Args:
            timeout_seconds: Inactivity timeout in seconds

        Returns:
            Number of connections cleaned up
        """
        now = datetime.now()
        inactive_connections = []

        for connection_id, subscription in self.active_connections.items():
            inactive_time = (now - subscription.last_activity).total_seconds()
            if inactive_time > timeout_seconds:
                inactive_connections.append(connection_id)

        for connection_id in inactive_connections:
            logger.info(f"Cleaning up inactive connection: {connection_id}")
            await self.disconnect(connection_id)

        return len(inactive_connections)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
