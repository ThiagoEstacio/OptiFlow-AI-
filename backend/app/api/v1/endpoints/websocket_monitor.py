"""
WebSocket Connection Pool Monitoring API (PDCA #18)

Endpoints for monitoring WebSocket connections.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
import logging

from app.core.websocket_pool import get_websocket_pool
from app.models.user import User
from app.core.deps import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_websocket_stats(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get WebSocket connection pool statistics.

    **Returns**:
    ```json
    {
        "active_connections": 245,
        "max_connections": 1000,
        "max_per_user": 10,
        "total_users": 52,
        "endpoints": {
            "/analytics/ws/stream": 120,
            "/ws/tags": 85,
            "/ws/simulator": 40
        },
        "metrics": {
            "total_connections_ever": 1523,
            "total_disconnections": 1278,
            "total_messages_sent": 452389
        },
        "top_users": [
            {"user_id": "user-123", "connections": 5},
            {"user_id": "user-456", "connections": 4}
        ]
    }
    ```

    **Use Cases**:
    - Monitor WebSocket pool health
    - Capacity planning
    - Identify users with many connections
    - Debug connection issues
    """
    pool = get_websocket_pool()
    return pool.get_stats()


@router.get("/connections/{connection_id}")
async def get_connection_info(
    connection_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get information about a specific WebSocket connection.

    **Parameters**:
    - connection_id: WebSocket connection ID

    **Returns**:
    ```json
    {
        "connection_id": "conn-abc123",
        "user_id": "user-456",
        "endpoint": "/analytics/ws/stream",
        "connected_at": "2025-01-13T10:30:00Z",
        "uptime_seconds": 1523,
        "message_count": 3456,
        "messages_per_minute": 136.2,
        "last_ping": "2025-01-13T10:55:00Z",
        "is_alive": true
    }
    ```

    **Use Cases**:
    - Debug specific connection
    - Monitor connection health
    - Audit user activity
    """
    pool = get_websocket_pool()
    stats = pool.get_connection_stats(connection_id)

    if stats is None:
        raise HTTPException(
            status_code=404,
            detail=f"Connection {connection_id} not found"
        )

    return stats


@router.get("/user/{user_id}/connections")
async def get_user_connections(
    user_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all WebSocket connections for a specific user.

    **Parameters**:
    - user_id: User ID

    **Returns**:
    ```json
    {
        "user_id": "user-456",
        "connection_count": 3,
        "connections": [
            {
                "connection_id": "conn-abc",
                "endpoint": "/analytics/ws/stream",
                "uptime_seconds": 1200
            },
            {
                "connection_id": "conn-def",
                "endpoint": "/ws/tags",
                "uptime_seconds": 800
            }
        ]
    }
    ```

    **Use Cases**:
    - See all connections for a user
    - Debug multi-connection issues
    - Enforce connection limits
    """
    pool = get_websocket_pool()
    connection_ids = pool.get_user_connections(user_id)

    connections = []
    for conn_id in connection_ids:
        stats = pool.get_connection_stats(conn_id)
        if stats:
            connections.append({
                "connection_id": conn_id,
                "endpoint": stats["endpoint"],
                "uptime_seconds": stats["uptime_seconds"],
                "message_count": stats["message_count"],
                "is_alive": stats["is_alive"]
            })

    return {
        "user_id": user_id,
        "connection_count": len(connections),
        "max_per_user": pool.max_per_user,
        "connections": connections
    }


@router.post("/broadcast")
async def broadcast_message(
    message: Dict[str, Any],
    endpoint: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Broadcast message to WebSocket connections.

    **Parameters**:
    - message: JSON message to broadcast
    - endpoint: Optional endpoint filter (broadcast only to this endpoint)

    **Returns**:
    ```json
    {
        "status": "success",
        "recipients": 245,
        "message": "Broadcast sent successfully"
    }
    ```

    **Use Cases**:
    - System-wide announcements
    - Emergency notifications
    - Maintenance warnings
    - Feature updates

    **Example**:
    ```bash
    curl -X POST -H "Authorization: Bearer $TOKEN" \\
         -H "Content-Type: application/json" \\
         -d '{"type":"announcement","text":"System maintenance in 10 minutes"}' \\
         http://localhost:8000/api/v1/websocket-monitor/broadcast
    ```
    """
    pool = get_websocket_pool()

    if endpoint:
        recipients = await pool.broadcast_to_endpoint(endpoint, message)
    else:
        recipients = await pool.broadcast_to_all(message)

    return {
        "status": "success",
        "recipients": recipients,
        "endpoint": endpoint,
        "message": "Broadcast sent successfully"
    }


@router.delete("/connections/{connection_id}")
async def close_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Forcefully close a WebSocket connection.

    **Parameters**:
    - connection_id: Connection ID to close

    **Returns**:
    ```json
    {
        "status": "closed",
        "connection_id": "conn-abc123",
        "message": "Connection closed successfully"
    }
    ```

    **Use Cases**:
    - Close stuck connections
    - Enforce policies
    - Emergency disconnect
    """
    pool = get_websocket_pool()

    # Check if connection exists
    stats = pool.get_connection_stats(connection_id)
    if stats is None:
        raise HTTPException(
            status_code=404,
            detail=f"Connection {connection_id} not found"
        )

    # Close connection
    await pool.disconnect(connection_id)

    return {
        "status": "closed",
        "connection_id": connection_id,
        "message": "Connection closed successfully"
    }
