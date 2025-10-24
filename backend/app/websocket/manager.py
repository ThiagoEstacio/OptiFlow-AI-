"""
WebSocket Connection Manager
Handles real-time communication with clients
"""
from typing import Dict, Set, List
from fastapi import WebSocket
from uuid import UUID
import json
import logging
import asyncio

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time data streaming
    """

    def __init__(self):
        # Active connections: {connection_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}

        # Subscriptions: {tag_id: Set[connection_id]}
        self.tag_subscriptions: Dict[str, Set[str]] = {}

        # Subscriptions: {site_id: Set[connection_id]}
        self.site_subscriptions: Dict[str, Set[str]] = {}

        # Subscriptions: {device_id: Set[connection_id]}
        self.device_subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connected: {connection_id}")

    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection and clean up subscriptions"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        # Clean up all subscriptions
        for tag_id in list(self.tag_subscriptions.keys()):
            self.tag_subscriptions[tag_id].discard(connection_id)
            if not self.tag_subscriptions[tag_id]:
                del self.tag_subscriptions[tag_id]

        for site_id in list(self.site_subscriptions.keys()):
            self.site_subscriptions[site_id].discard(connection_id)
            if not self.site_subscriptions[site_id]:
                del self.site_subscriptions[site_id]

        for device_id in list(self.device_subscriptions.keys()):
            self.device_subscriptions[device_id].discard(connection_id)
            if not self.device_subscriptions[device_id]:
                del self.device_subscriptions[device_id]

        logger.info(f"WebSocket disconnected: {connection_id}")

    def subscribe_to_tag(self, connection_id: str, tag_id: str):
        """Subscribe a connection to tag updates"""
        if tag_id not in self.tag_subscriptions:
            self.tag_subscriptions[tag_id] = set()
        self.tag_subscriptions[tag_id].add(connection_id)
        logger.debug(f"Connection {connection_id} subscribed to tag {tag_id}")

    def subscribe_to_site(self, connection_id: str, site_id: str):
        """Subscribe a connection to site updates"""
        if site_id not in self.site_subscriptions:
            self.site_subscriptions[site_id] = set()
        self.site_subscriptions[site_id].add(connection_id)
        logger.debug(f"Connection {connection_id} subscribed to site {site_id}")

    def subscribe_to_device(self, connection_id: str, device_id: str):
        """Subscribe a connection to device updates"""
        if device_id not in self.device_subscriptions:
            self.device_subscriptions[device_id] = set()
        self.device_subscriptions[device_id].add(connection_id)
        logger.debug(f"Connection {connection_id} subscribed to device {device_id}")

    async def send_personal_message(self, message: dict, connection_id: str):
        """Send a message to a specific connection"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)

    async def broadcast_to_tag(self, tag_id: str, message: dict):
        """Broadcast a message to all connections subscribed to a tag"""
        if tag_id in self.tag_subscriptions:
            connection_ids = list(self.tag_subscriptions[tag_id])
            await self._broadcast_to_connections(connection_ids, message)

    async def broadcast_to_site(self, site_id: str, message: dict):
        """Broadcast a message to all connections subscribed to a site"""
        if site_id in self.site_subscriptions:
            connection_ids = list(self.site_subscriptions[site_id])
            await self._broadcast_to_connections(connection_ids, message)

    async def broadcast_to_device(self, device_id: str, message: dict):
        """Broadcast a message to all connections subscribed to a device"""
        if device_id in self.device_subscriptions:
            connection_ids = list(self.device_subscriptions[device_id])
            await self._broadcast_to_connections(connection_ids, message)

    async def broadcast_all(self, message: dict):
        """Broadcast a message to all active connections"""
        connection_ids = list(self.active_connections.keys())
        await self._broadcast_to_connections(connection_ids, message)

    async def _broadcast_to_connections(self, connection_ids: List[str], message: dict):
        """Helper method to broadcast to a list of connections"""
        disconnected = []

        for connection_id in connection_ids:
            if connection_id in self.active_connections:
                try:
                    websocket = self.active_connections[connection_id]
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {connection_id}: {e}")
                    disconnected.append(connection_id)

        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)

    def get_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "active_connections": len(self.active_connections),
            "tag_subscriptions": len(self.tag_subscriptions),
            "site_subscriptions": len(self.site_subscriptions),
            "device_subscriptions": len(self.device_subscriptions),
        }


# Global connection manager instance
manager = ConnectionManager()
