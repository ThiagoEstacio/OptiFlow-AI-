"""
WebSocket endpoint handlers
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import json
import logging

from app.websocket.manager import manager
from app.core.security import get_current_user_ws
from app.models.user import User

logger = logging.getLogger(__name__)


async def handle_realtime_data(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time data streaming

    Usage:
    ws://localhost:8000/api/v1/ws/realtime?token=<jwt_token>
    """
    current_user = None

    try:
        # Authenticate user if token provided
        if token:
            try:
                current_user = await get_current_user_ws(token)
            except Exception as e:
                await websocket.close(code=4001, reason="Authentication failed")
                return

        # Accept connection
        user_id = str(current_user.id) if current_user else None
        await manager.connect(websocket, user_id=user_id)

        # Send welcome message
        await manager.send_personal_message({
            "type": "connection",
            "status": "connected",
            "message": "Connected to OptiFlow AI Platform",
            "user_id": user_id
        }, websocket)

        # Handle incoming messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_json()

                # Handle different message types
                message_type = data.get("type")

                if message_type == "subscribe_tag":
                    tag_id = data.get("tag_id")
                    if tag_id:
                        await manager.subscribe_to_tag(websocket, tag_id)
                        await manager.send_personal_message({
                            "type": "subscription",
                            "status": "subscribed",
                            "resource": "tag",
                            "resource_id": tag_id
                        }, websocket)

                elif message_type == "unsubscribe_tag":
                    tag_id = data.get("tag_id")
                    if tag_id:
                        await manager.unsubscribe_from_tag(websocket, tag_id)
                        await manager.send_personal_message({
                            "type": "subscription",
                            "status": "unsubscribed",
                            "resource": "tag",
                            "resource_id": tag_id
                        }, websocket)

                elif message_type == "subscribe_device":
                    device_id = data.get("device_id")
                    if device_id:
                        await manager.subscribe_to_device(websocket, device_id)
                        await manager.send_personal_message({
                            "type": "subscription",
                            "status": "subscribed",
                            "resource": "device",
                            "resource_id": device_id
                        }, websocket)

                elif message_type == "join_room":
                    room_id = data.get("room_id")
                    if room_id:
                        await manager.join_room(websocket, room_id)
                        await manager.send_personal_message({
                            "type": "room",
                            "status": "joined",
                            "room_id": room_id
                        }, websocket)

                elif message_type == "leave_room":
                    room_id = data.get("room_id")
                    if room_id:
                        await manager.leave_room(websocket, room_id)
                        await manager.send_personal_message({
                            "type": "room",
                            "status": "left",
                            "room_id": room_id
                        }, websocket)

                elif message_type == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": data.get("timestamp")
                    }, websocket)

                else:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    }, websocket)

            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, websocket)
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Internal server error"
                }, websocket)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user_id={user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)


async def handle_dashboard(
    websocket: WebSocket,
    dashboard_id: str,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for dashboard real-time updates

    Usage:
    ws://localhost:8000/api/v1/ws/dashboard/{dashboard_id}?token=<jwt_token>
    """
    current_user = None

    try:
        # Authenticate user if token provided
        if token:
            try:
                current_user = await get_current_user_ws(token)
            except Exception as e:
                await websocket.close(code=4001, reason="Authentication failed")
                return

        # Accept connection
        user_id = str(current_user.id) if current_user else None
        await manager.connect(websocket, user_id=user_id, metadata={"dashboard_id": dashboard_id})

        # Join dashboard room
        room_id = f"dashboard:{dashboard_id}"
        await manager.join_room(websocket, room_id)

        # Send welcome message
        await manager.send_personal_message({
            "type": "connection",
            "status": "connected",
            "dashboard_id": dashboard_id,
            "room_id": room_id
        }, websocket)

        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                message_type = data.get("type")

                # Handle dashboard-specific messages
                if message_type == "subscribe_tags":
                    tag_ids = data.get("tag_ids", [])
                    for tag_id in tag_ids:
                        await manager.subscribe_to_tag(websocket, tag_id)

                    await manager.send_personal_message({
                        "type": "subscription",
                        "status": "subscribed",
                        "tag_ids": tag_ids
                    }, websocket)

                elif message_type == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": data.get("timestamp")
                    }, websocket)

            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, websocket)

    except WebSocketDisconnect:
        logger.info(f"Dashboard WebSocket disconnected: dashboard_id={dashboard_id}, user_id={user_id}")
    except Exception as e:
        logger.error(f"Dashboard WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)
