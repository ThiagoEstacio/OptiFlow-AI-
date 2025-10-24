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


async def handle_smartport(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for SmartPort real-time updates

    Usage:
    ws://localhost:8000/api/v1/ws/smartport?token=<jwt_token>

    Message types:
    - subscribe_berth: Subscribe to berth status updates
    - subscribe_vessel: Subscribe to vessel position/status updates
    - subscribe_operation: Subscribe to operation progress updates
    - subscribe_port: Subscribe to all port events
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
        await manager.connect(websocket, user_id=user_id, metadata={"type": "smartport"})

        # Send welcome message
        await manager.send_personal_message({
            "type": "connection",
            "status": "connected",
            "message": "Connected to SmartPort WebSocket",
            "user_id": user_id
        }, websocket)

        # Handle incoming messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_json()

                # Handle different message types
                message_type = data.get("type")

                if message_type == "subscribe_berth":
                    berth_id = data.get("berth_id")
                    if berth_id:
                        room_id = f"smartport:berth:{berth_id}"
                        await manager.join_room(websocket, room_id)
                        await manager.send_personal_message({
                            "type": "subscription",
                            "status": "subscribed",
                            "resource": "berth",
                            "resource_id": berth_id,
                            "room_id": room_id
                        }, websocket)

                elif message_type == "unsubscribe_berth":
                    berth_id = data.get("berth_id")
                    if berth_id:
                        room_id = f"smartport:berth:{berth_id}"
                        await manager.leave_room(websocket, room_id)
                        await manager.send_personal_message({
                            "type": "subscription",
                            "status": "unsubscribed",
                            "resource": "berth",
                            "resource_id": berth_id
                        }, websocket)

                elif message_type == "subscribe_vessel":
                    vessel_id = data.get("vessel_id")
                    if vessel_id:
                        room_id = f"smartport:vessel:{vessel_id}"
                        await manager.join_room(websocket, room_id)
                        await manager.send_personal_message({
                            "type": "subscription",
                            "status": "subscribed",
                            "resource": "vessel",
                            "resource_id": vessel_id,
                            "room_id": room_id
                        }, websocket)

                elif message_type == "unsubscribe_vessel":
                    vessel_id = data.get("vessel_id")
                    if vessel_id:
                        room_id = f"smartport:vessel:{vessel_id}"
                        await manager.leave_room(websocket, room_id)
                        await manager.send_personal_message({
                            "type": "subscription",
                            "status": "unsubscribed",
                            "resource": "vessel",
                            "resource_id": vessel_id
                        }, websocket)

                elif message_type == "subscribe_operation":
                    operation_id = data.get("operation_id")
                    if operation_id:
                        room_id = f"smartport:operation:{operation_id}"
                        await manager.join_room(websocket, room_id)
                        await manager.send_personal_message({
                            "type": "subscription",
                            "status": "subscribed",
                            "resource": "operation",
                            "resource_id": operation_id,
                            "room_id": room_id
                        }, websocket)

                elif message_type == "unsubscribe_operation":
                    operation_id = data.get("operation_id")
                    if operation_id:
                        room_id = f"smartport:operation:{operation_id}"
                        await manager.leave_room(websocket, room_id)
                        await manager.send_personal_message({
                            "type": "subscription",
                            "status": "unsubscribed",
                            "resource": "operation",
                            "resource_id": operation_id
                        }, websocket)

                elif message_type == "subscribe_port":
                    # Subscribe to all port events
                    room_id = "smartport:port:all"
                    await manager.join_room(websocket, room_id)
                    await manager.send_personal_message({
                        "type": "subscription",
                        "status": "subscribed",
                        "resource": "port",
                        "room_id": room_id
                    }, websocket)

                elif message_type == "unsubscribe_port":
                    room_id = "smartport:port:all"
                    await manager.leave_room(websocket, room_id)
                    await manager.send_personal_message({
                        "type": "subscription",
                        "status": "unsubscribed",
                        "resource": "port"
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
                logger.error(f"Error handling SmartPort WebSocket message: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Internal server error"
                }, websocket)

    except WebSocketDisconnect:
        logger.info(f"SmartPort WebSocket disconnected: user_id={user_id}")
    except Exception as e:
        logger.error(f"SmartPort WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)


async def handle_plc_streaming(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for PLC real-time streaming

    Usage:
    ws://localhost:8000/api/v1/ws/plc?token=<jwt_token>

    Message types:
    - subscribe_tag: Subscribe to a specific PLC tag
    - unsubscribe_tag: Unsubscribe from a tag
    - subscribe_all: Subscribe to all tags
    - read_tag: Read current value of a tag
    """
    from app.services.plc_service import plc_service
    from app.services.timeseries_service import timeseries_service
    import asyncio

    current_user = None
    subscribed_tags = set()
    streaming_task = None

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
        await manager.connect(websocket, user_id=user_id, metadata={"type": "plc"})

        # Send welcome message with available tags
        await manager.send_personal_message({
            "type": "connection",
            "status": "connected",
            "message": "Connected to PLC Streaming",
            "available_tags": list(plc_service.tags.keys())
        }, websocket)

        # Streaming loop task
        async def stream_tags():
            while True:
                if subscribed_tags:
                    # Read subscribed tags
                    data = {}
                    for tag_name in subscribed_tags:
                        value = await plc_service.read_tag_opcua(tag_name)
                        tag = plc_service.tags.get(tag_name)
                        if tag:
                            data[tag_name] = {
                                "value": value,
                                "timestamp": tag.timestamp.isoformat() if tag.timestamp else None,
                                "quality": tag.quality,
                                "unit": tag.unit,
                                "description": tag.description
                            }

                            # Write to time series
                            if value is not None:
                                timeseries_service.write_tag_value(
                                    tag_name=tag_name,
                                    value=value,
                                    timestamp=tag.timestamp
                                )

                    # Send update
                    if data:
                        await manager.send_personal_message({
                            "type": "plc_update",
                            "data": data
                        }, websocket)

                await asyncio.sleep(1.0)  # Update every 1 second

        # Handle incoming messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_json()

                # Handle different message types
                message_type = data.get("type")

                if message_type == "subscribe_tag":
                    tag_name = data.get("tag_name")
                    if tag_name and tag_name in plc_service.tags:
                        subscribed_tags.add(tag_name)

                        # Start streaming if not already started
                        if streaming_task is None or streaming_task.done():
                            streaming_task = asyncio.create_task(stream_tags())

                        await manager.send_personal_message({
                            "type": "subscription",
                            "status": "subscribed",
                            "tag_name": tag_name
                        }, websocket)

                elif message_type == "unsubscribe_tag":
                    tag_name = data.get("tag_name")
                    if tag_name in subscribed_tags:
                        subscribed_tags.remove(tag_name)
                        await manager.send_personal_message({
                            "type": "subscription",
                            "status": "unsubscribed",
                            "tag_name": tag_name
                        }, websocket)

                elif message_type == "subscribe_all":
                    subscribed_tags = set(plc_service.tags.keys())

                    # Start streaming
                    if streaming_task is None or streaming_task.done():
                        streaming_task = asyncio.create_task(stream_tags())

                    await manager.send_personal_message({
                        "type": "subscription",
                        "status": "subscribed_all",
                        "tags": list(subscribed_tags)
                    }, websocket)

                elif message_type == "unsubscribe_all":
                    subscribed_tags.clear()
                    await manager.send_personal_message({
                        "type": "subscription",
                        "status": "unsubscribed_all"
                    }, websocket)

                elif message_type == "read_tag":
                    tag_name = data.get("tag_name")
                    if tag_name and tag_name in plc_service.tags:
                        value = await plc_service.read_tag_opcua(tag_name)
                        tag = plc_service.tags.get(tag_name)

                        await manager.send_personal_message({
                            "type": "tag_value",
                            "tag_name": tag_name,
                            "value": value,
                            "timestamp": tag.timestamp.isoformat() if tag.timestamp else None,
                            "quality": tag.quality,
                            "unit": tag.unit
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
                logger.error(f"Error handling PLC WebSocket message: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Internal server error"
                }, websocket)

    except WebSocketDisconnect:
        logger.info(f"PLC WebSocket disconnected: user_id={user_id}")
    except Exception as e:
        logger.error(f"PLC WebSocket error: {e}")
    finally:
        # Stop streaming
        if streaming_task and not streaming_task.done():
            streaming_task.cancel()

        await manager.disconnect(websocket)
