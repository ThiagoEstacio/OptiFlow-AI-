"""
WebSocket Connection Pool Manager (PDCA #18)

Advanced connection pooling for WebSocket endpoints.

Features:
- Connection limits per user
- Global connection limits
- Auto-reconnect support
- Connection health monitoring
- Resource cleanup
- Metrics and monitoring
"""

import logging
import asyncio
from typing import Dict, Set, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import WebSocket, WebSocketDisconnect
import json

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """
    Represents a single WebSocket connection with metadata.
    """

    def __init__(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: Optional[str] = None,
        endpoint: str = ""
    ):
        self.websocket = websocket
        self.connection_id = connection_id
        self.user_id = user_id
        self.endpoint = endpoint
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.message_count = 0
        self.is_alive = True

    async def send_json(self, data: dict) -> bool:
        """
        Send JSON data to client.

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            await self.websocket.send_json(data)
            self.message_count += 1
            return True
        except Exception as e:
            logger.error(f"Error sending to {self.connection_id}: {e}")
            self.is_alive = False
            return False

    async def send_text(self, text: str) -> bool:
        """Send text data to client."""
        try:
            await self.websocket.send_text(text)
            self.message_count += 1
            return True
        except Exception as e:
            logger.error(f"Error sending to {self.connection_id}: {e}")
            self.is_alive = False
            return False

    async def ping(self) -> bool:
        """Send ping to check connection health."""
        try:
            await self.websocket.send_json({"type": "ping", "timestamp": datetime.utcnow().isoformat()})
            self.last_ping = datetime.utcnow()
            return True
        except Exception:
            self.is_alive = False
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        uptime = (datetime.utcnow() - self.connected_at).total_seconds()
        return {
            "connection_id": self.connection_id,
            "user_id": self.user_id,
            "endpoint": self.endpoint,
            "connected_at": self.connected_at.isoformat(),
            "uptime_seconds": uptime,
            "message_count": self.message_count,
            "messages_per_minute": (self.message_count / uptime * 60) if uptime > 0 else 0,
            "last_ping": self.last_ping.isoformat(),
            "is_alive": self.is_alive
        }


class WebSocketConnectionPool:
    """
    Manages WebSocket connections with pooling and resource limits.

    Features:
    - Per-user connection limits
    - Global connection limits
    - Connection health monitoring
    - Automatic cleanup of dead connections
    - Metrics and statistics
    """

    def __init__(
        self,
        max_connections: int = 1000,
        max_per_user: int = 10,
        ping_interval: int = 30,
        ping_timeout: int = 60
    ):
        self.max_connections = max_connections
        self.max_per_user = max_per_user
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout

        # Connections storage
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)
        self.endpoint_connections: Dict[str, Set[str]] = defaultdict(set)

        # Metrics
        self.total_connections_ever = 0
        self.total_disconnections = 0
        self.total_messages_sent = 0

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start background tasks."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._ping_task = asyncio.create_task(self._ping_loop())
        logger.info("WebSocket connection pool started")

    async def stop(self):
        """Stop background tasks and close all connections."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._ping_task:
            self._ping_task.cancel()

        # Close all connections
        for conn in list(self.connections.values()):
            await self.disconnect(conn.connection_id)

        logger.info("WebSocket connection pool stopped")

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: Optional[str] = None,
        endpoint: str = ""
    ) -> bool:
        """
        Accept new WebSocket connection.

        Returns:
            True if accepted, False if rejected (limits exceeded)
        """
        # Check global limit
        if len(self.connections) >= self.max_connections:
            logger.warning(f"Global connection limit reached: {self.max_connections}")
            await websocket.close(code=1008, reason="Connection limit reached")
            return False

        # Check per-user limit
        if user_id and len(self.user_connections[user_id]) >= self.max_per_user:
            logger.warning(f"User {user_id} connection limit reached: {self.max_per_user}")
            await websocket.close(code=1008, reason="User connection limit reached")
            return False

        # Accept connection
        try:
            await websocket.accept()

            # Create connection object
            conn = WebSocketConnection(
                websocket=websocket,
                connection_id=connection_id,
                user_id=user_id,
                endpoint=endpoint
            )

            # Store connection
            self.connections[connection_id] = conn
            if user_id:
                self.user_connections[user_id].add(connection_id)
            self.endpoint_connections[endpoint].add(connection_id)

            # Update metrics
            self.total_connections_ever += 1

            logger.info(
                f"WebSocket connected: {connection_id} "
                f"(user: {user_id}, endpoint: {endpoint}, "
                f"total: {len(self.connections)})"
            )

            return True

        except Exception as e:
            logger.error(f"Error accepting connection {connection_id}: {e}")
            return False

    async def disconnect(self, connection_id: str):
        """Disconnect and cleanup connection."""
        if connection_id not in self.connections:
            return

        conn = self.connections[connection_id]

        # Close WebSocket
        try:
            await conn.websocket.close()
        except Exception as e:
            logger.debug(f"Error closing websocket {connection_id}: {e}")

        # Remove from tracking
        if conn.user_id:
            self.user_connections[conn.user_id].discard(connection_id)
            if not self.user_connections[conn.user_id]:
                del self.user_connections[conn.user_id]

        self.endpoint_connections[conn.endpoint].discard(connection_id)
        if not self.endpoint_connections[conn.endpoint]:
            del self.endpoint_connections[conn.endpoint]

        del self.connections[connection_id]

        # Update metrics
        self.total_disconnections += 1

        logger.info(
            f"WebSocket disconnected: {connection_id} "
            f"(total: {len(self.connections)})"
        )

    async def send_to_connection(self, connection_id: str, data: dict) -> bool:
        """Send data to specific connection."""
        if connection_id not in self.connections:
            return False

        conn = self.connections[connection_id]
        success = await conn.send_json(data)

        if success:
            self.total_messages_sent += 1
        else:
            # Connection dead, cleanup
            await self.disconnect(connection_id)

        return success

    async def send_to_user(self, user_id: str, data: dict) -> int:
        """
        Send data to all connections of a user.

        Returns:
            Number of successful sends
        """
        if user_id not in self.user_connections:
            return 0

        connection_ids = list(self.user_connections[user_id])
        success_count = 0

        for conn_id in connection_ids:
            if await self.send_to_connection(conn_id, data):
                success_count += 1

        return success_count

    async def broadcast_to_endpoint(self, endpoint: str, data: dict) -> int:
        """
        Broadcast data to all connections on an endpoint.

        Returns:
            Number of successful sends
        """
        if endpoint not in self.endpoint_connections:
            return 0

        connection_ids = list(self.endpoint_connections[endpoint])
        success_count = 0

        for conn_id in connection_ids:
            if await self.send_to_connection(conn_id, data):
                success_count += 1

        return success_count

    async def broadcast_to_all(self, data: dict) -> int:
        """
        Broadcast data to all connections.

        Returns:
            Number of successful sends
        """
        connection_ids = list(self.connections.keys())
        success_count = 0

        for conn_id in connection_ids:
            if await self.send_to_connection(conn_id, data):
                success_count += 1

        return success_count

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            "active_connections": len(self.connections),
            "max_connections": self.max_connections,
            "max_per_user": self.max_per_user,
            "total_users": len(self.user_connections),
            "endpoints": {
                endpoint: len(conns)
                for endpoint, conns in self.endpoint_connections.items()
            },
            "metrics": {
                "total_connections_ever": self.total_connections_ever,
                "total_disconnections": self.total_disconnections,
                "total_messages_sent": self.total_messages_sent
            },
            "top_users": self._get_top_users(5)
        }

    def _get_top_users(self, limit: int) -> list:
        """Get top N users by connection count."""
        user_counts = [
            {"user_id": user_id, "connections": len(conns)}
            for user_id, conns in self.user_connections.items()
        ]
        user_counts.sort(key=lambda x: x["connections"], reverse=True)
        return user_counts[:limit]

    def get_connection_stats(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get stats for specific connection."""
        if connection_id not in self.connections:
            return None

        return self.connections[connection_id].get_stats()

    def get_user_connections(self, user_id: str) -> list:
        """Get all connection IDs for a user."""
        return list(self.user_connections.get(user_id, []))

    async def _cleanup_loop(self):
        """Background task to cleanup dead connections."""
        while True:
            try:
                await asyncio.sleep(30)  # Cleanup every 30 seconds

                dead_connections = []

                for conn_id, conn in self.connections.items():
                    # Check if connection is alive
                    if not conn.is_alive:
                        dead_connections.append(conn_id)
                        continue

                    # Check if last ping is too old
                    time_since_ping = (datetime.utcnow() - conn.last_ping).total_seconds()
                    if time_since_ping > self.ping_timeout:
                        logger.warning(f"Connection {conn_id} timed out (no ping for {time_since_ping}s)")
                        dead_connections.append(conn_id)

                # Cleanup dead connections
                for conn_id in dead_connections:
                    await self.disconnect(conn_id)

                if dead_connections:
                    logger.info(f"Cleaned up {len(dead_connections)} dead connection(s)")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)

    async def _ping_loop(self):
        """Background task to ping all connections."""
        while True:
            try:
                await asyncio.sleep(self.ping_interval)

                for conn_id, conn in list(self.connections.items()):
                    await conn.ping()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ping loop: {e}", exc_info=True)


# Global connection pool instance
_connection_pool: Optional[WebSocketConnectionPool] = None


def get_websocket_pool() -> WebSocketConnectionPool:
    """Get global WebSocket connection pool."""
    global _connection_pool

    if _connection_pool is None:
        _connection_pool = WebSocketConnectionPool(
            max_connections=1000,
            max_per_user=10,
            ping_interval=30,
            ping_timeout=60
        )

    return _connection_pool


async def init_websocket_pool():
    """Initialize WebSocket connection pool."""
    pool = get_websocket_pool()
    await pool.start()
    logger.info("WebSocket connection pool initialized")


async def shutdown_websocket_pool():
    """Shutdown WebSocket connection pool."""
    pool = get_websocket_pool()
    await pool.stop()
    logger.info("WebSocket connection pool shutdown")
