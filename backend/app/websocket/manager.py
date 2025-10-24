"""
WebSocket Connection Manager for Real-time Data Streaming
"""
from typing import Dict, Set, List, Any
from fastapi import WebSocket
from datetime import datetime
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time data streaming"""

    def __init__(self):
        # Active connections: {user_id: Set[WebSocket]}
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # Room-based connections: {room_id: Set[WebSocket]}
        self.rooms: Dict[str, Set[WebSocket]] = {}

        # Tag subscriptions: {tag_id: Set[WebSocket]}
        self.tag_subscriptions: Dict[str, Set[WebSocket]] = {}

        # Device subscriptions: {device_id: Set[WebSocket]}
        self.device_subscriptions: Dict[str, Set[WebSocket]] = {}

        # Connection metadata: {WebSocket: Dict}
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str = None,
        metadata: Dict[str, Any] = None
    ):
        """Accept new WebSocket connection"""
        await websocket.accept()

        # Store connection metadata
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "metadata": metadata or {}
        }

        # Add to user connections
        if user_id:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)

        logger.info(f"WebSocket connected: user_id={user_id}, total_connections={self.get_total_connections()}")

    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection and clean up subscriptions"""
        metadata = self.connection_metadata.get(websocket, {})
        user_id = metadata.get("user_id")

        # Remove from user connections
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        # Remove from rooms
        for room_id, connections in list(self.rooms.items()):
            connections.discard(websocket)
            if not connections:
                del self.rooms[room_id]

        # Remove from tag subscriptions
        for tag_id, connections in list(self.tag_subscriptions.items()):
            connections.discard(websocket)
            if not connections:
                del self.tag_subscriptions[tag_id]

        # Remove from device subscriptions
        for device_id, connections in list(self.device_subscriptions.items()):
            connections.discard(websocket)
            if not connections:
                del self.device_subscriptions[device_id]

        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]

        logger.info(f"WebSocket disconnected: user_id={user_id}, remaining_connections={self.get_total_connections()}")

    async def subscribe_to_tag(self, websocket: WebSocket, tag_id: str):
        """Subscribe WebSocket to tag updates"""
        if tag_id not in self.tag_subscriptions:
            self.tag_subscriptions[tag_id] = set()
        self.tag_subscriptions[tag_id].add(websocket)
        logger.debug(f"WebSocket subscribed to tag: {tag_id}")

    async def unsubscribe_from_tag(self, websocket: WebSocket, tag_id: str):
        """Unsubscribe WebSocket from tag updates"""
        if tag_id in self.tag_subscriptions:
            self.tag_subscriptions[tag_id].discard(websocket)
            if not self.tag_subscriptions[tag_id]:
                del self.tag_subscriptions[tag_id]
        logger.debug(f"WebSocket unsubscribed from tag: {tag_id}")

    async def subscribe_to_device(self, websocket: WebSocket, device_id: str):
        """Subscribe WebSocket to device updates"""
        if device_id not in self.device_subscriptions:
            self.device_subscriptions[device_id] = set()
        self.device_subscriptions[device_id].add(websocket)
        logger.debug(f"WebSocket subscribed to device: {device_id}")

    async def join_room(self, websocket: WebSocket, room_id: str):
        """Add WebSocket to a room"""
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(websocket)
        logger.debug(f"WebSocket joined room: {room_id}")

    async def leave_room(self, websocket: WebSocket, room_id: str):
        """Remove WebSocket from a room"""
        if room_id in self.rooms:
            self.rooms[room_id].discard(websocket)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        logger.debug(f"WebSocket left room: {room_id}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket)

    async def send_to_user(self, message: Dict[str, Any], user_id: str):
        """Send message to all connections of a specific user"""
        if user_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected sockets
            for ws in disconnected:
                await self.disconnect(ws)

    async def broadcast_to_room(self, message: Dict[str, Any], room_id: str):
        """Broadcast message to all connections in a room"""
        if room_id in self.rooms:
            disconnected = []
            for websocket in self.rooms[room_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to room {room_id}: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected sockets
            for ws in disconnected:
                await self.disconnect(ws)

    async def broadcast_tag_update(self, tag_id: str, data: Dict[str, Any]):
        """Broadcast tag data update to all subscribers"""
        if tag_id in self.tag_subscriptions:
            message = {
                "type": "tag_update",
                "tag_id": tag_id,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }

            disconnected = []
            for websocket in self.tag_subscriptions[tag_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting tag update {tag_id}: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected sockets
            for ws in disconnected:
                await self.disconnect(ws)

    async def broadcast_device_update(self, device_id: str, data: Dict[str, Any]):
        """Broadcast device data update to all subscribers"""
        if device_id in self.device_subscriptions:
            message = {
                "type": "device_update",
                "device_id": device_id,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }

            disconnected = []
            for websocket in self.device_subscriptions[device_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting device update {device_id}: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected sockets
            for ws in disconnected:
                await self.disconnect(ws)

    async def broadcast_all(self, message: Dict[str, Any]):
        """Broadcast message to all active connections"""
        all_connections = set()
        for connections in self.active_connections.values():
            all_connections.update(connections)

        disconnected = []
        for websocket in all_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to all: {e}")
                disconnected.append(websocket)

        # Clean up disconnected sockets
        for ws in disconnected:
            await self.disconnect(ws)

    def get_total_connections(self) -> int:
        """Get total number of active connections"""
        return len(self.connection_metadata)

    def get_user_connections(self, user_id: str) -> int:
        """Get number of connections for a specific user"""
        return len(self.active_connections.get(user_id, set()))

    def get_room_size(self, room_id: str) -> int:
        """Get number of connections in a room"""
        return len(self.rooms.get(room_id, set()))

    def get_tag_subscribers(self, tag_id: str) -> int:
        """Get number of subscribers for a tag"""
        return len(self.tag_subscriptions.get(tag_id, set()))

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": self.get_total_connections(),
            "total_users": len(self.active_connections),
            "total_rooms": len(self.rooms),
            "tag_subscriptions": len(self.tag_subscriptions),
            "device_subscriptions": len(self.device_subscriptions)
        }


# Global connection manager instance
manager = ConnectionManager()
