"""
WebSocket routes and handlers
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from typing import Optional
import uuid
import logging
import json

from app.websocket.manager import manager
from app.core.security import decode_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """
    Main WebSocket endpoint for real-time data streaming

    Connection flow:
    1. Client connects with optional auth token
    2. Server assigns connection_id
    3. Client can send subscription messages
    4. Server broadcasts relevant data updates

    Message format from client:
    {
        "action": "subscribe_tag" | "subscribe_site" | "subscribe_device" | "unsubscribe_tag" | ...,
        "id": "uuid-string"
    }

    Message format from server:
    {
        "type": "tag_data" | "alarm" | "device_status" | "info" | "error",
        "data": {...}
    }
    """
    connection_id = str(uuid.uuid4())

    # Optional: Verify authentication token
    user_id = None
    if token:
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
        except Exception as e:
            logger.warning(f"Invalid WebSocket token: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    # Accept connection
    await manager.connect(websocket, connection_id)

    # Send welcome message
    await manager.send_personal_message(
        {
            "type": "info",
            "message": "Connected to OptiFlow AI Platform",
            "connection_id": connection_id,
            "user_id": user_id
        },
        connection_id
    )

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                action = message.get("action")
                target_id = message.get("id")

                if not action:
                    await manager.send_personal_message(
                        {"type": "error", "message": "Missing 'action' field"},
                        connection_id
                    )
                    continue

                # Handle subscription actions
                if action == "subscribe_tag":
                    manager.subscribe_to_tag(connection_id, target_id)
                    await manager.send_personal_message(
                        {"type": "info", "message": f"Subscribed to tag {target_id}"},
                        connection_id
                    )

                elif action == "subscribe_site":
                    manager.subscribe_to_site(connection_id, target_id)
                    await manager.send_personal_message(
                        {"type": "info", "message": f"Subscribed to site {target_id}"},
                        connection_id
                    )

                elif action == "subscribe_device":
                    manager.subscribe_to_device(connection_id, target_id)
                    await manager.send_personal_message(
                        {"type": "info", "message": f"Subscribed to device {target_id}"},
                        connection_id
                    )

                elif action == "ping":
                    await manager.send_personal_message(
                        {"type": "pong", "timestamp": message.get("timestamp")},
                        connection_id
                    )

                elif action == "get_stats":
                    stats = manager.get_stats()
                    await manager.send_personal_message(
                        {"type": "stats", "data": stats},
                        connection_id
                    )

                else:
                    await manager.send_personal_message(
                        {"type": "error", "message": f"Unknown action: {action}"},
                        connection_id
                    )

            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON"},
                    connection_id
                )
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await manager.send_personal_message(
                    {"type": "error", "message": "Internal server error"},
                    connection_id
                )

    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"Client {connection_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        manager.disconnect(connection_id)


# Helper function to broadcast data (used by other services)
async def broadcast_tag_data(tag_id: str, value: float, timestamp: str, quality: str = "good"):
    """Broadcast tag data to subscribed clients"""
    await manager.broadcast_to_tag(
        tag_id,
        {
            "type": "tag_data",
            "data": {
                "tag_id": tag_id,
                "value": value,
                "timestamp": timestamp,
                "quality": quality
            }
        }
    )


async def broadcast_alarm(alarm_id: str, severity: str, message: str):
    """Broadcast alarm to all clients"""
    await manager.broadcast_all(
        {
            "type": "alarm",
            "data": {
                "alarm_id": alarm_id,
                "severity": severity,
                "message": message
            }
        }
    )


async def broadcast_device_status(device_id: str, status: str, site_id: Optional[str] = None):
    """Broadcast device status change"""
    message = {
        "type": "device_status",
        "data": {
            "device_id": device_id,
            "status": status
        }
    }

    # Broadcast to device subscribers
    await manager.broadcast_to_device(device_id, message)

    # Also broadcast to site subscribers if applicable
    if site_id:
        await manager.broadcast_to_site(site_id, message)
