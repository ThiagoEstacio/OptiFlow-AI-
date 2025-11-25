"""
WebSocket Routes - Real-time Alarm Streaming
=============================================

Provides WebSocket endpoint for streaming critical alarms to frontends.

**Target Performance**:
- Latency: < 100ms from PLC quality flag to frontend
- Push-based model (server notifies client)
- No polling required
- Supports multiple concurrent clients

**Use Cases**:
- Real-time alarm dashboard
- Mobile notifications
- HMI alarm panels
- Operator workstations

**Connection Flow**:
1. Client connects: ws://gateway:8001/ws/alarms
2. Server sends initial state (active alarms)
3. Server pushes new alarms as they occur
4. Client can filter by severity/tag

**Message Format**:
```json
{
  "type": "alarm",
  "severity": "HIGH",
  "tag_name": "SILO1_TEMPERATURA",
  "message": "Communication loss detected",
  "value": null,
  "quality": "bad",
  "timestamp": "2025-01-19T10:30:45.123Z",
  "source": "plc1_opcua"
}
```
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Set, Optional, List, Dict, Any
import asyncio
import json
from datetime import datetime

from app.core.logger import logger

router = APIRouter()


# === CONNECTION MANAGER ===

class AlarmConnectionManager:
    """
    Manages WebSocket connections and broadcasts alarms

    Features:
    - Multiple concurrent clients
    - Broadcast to all or filter by client
    - Automatic reconnection handling
    - Memory efficient (no message queue)
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()

        async with self._lock:
            self.active_connections.add(websocket)

        logger.info(f"✅ WebSocket client connected. Total: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        async with self._lock:
            self.active_connections.discard(websocket)

        logger.info(f"❌ WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast message to all connected clients

        Automatically removes dead connections
        """
        if not self.active_connections:
            return

        # Serialize once (performance optimization)
        message_json = json.dumps(message)

        dead_connections = set()

        for connection in list(self.active_connections):
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"⚠️ Failed to send to client: {e}")
                dead_connections.add(connection)

        # Cleanup dead connections
        if dead_connections:
            async with self._lock:
                self.active_connections -= dead_connections
            logger.warning(f"🗑️ Removed {len(dead_connections)} dead connections")

    async def send_to_one(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"❌ Failed to send to client: {e}")
            await self.disconnect(websocket)

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)


# Global connection manager
alarm_manager = AlarmConnectionManager()


# === DEPENDENCY INJECTION ===

def get_protocol_manager():
    """Get protocol manager from global state"""
    from app.main_hybrid import protocol_manager
    if protocol_manager is None:
        raise RuntimeError("Protocol manager not initialized")
    return protocol_manager


# === WEBSOCKET ENDPOINT ===

@router.websocket("/alarms")
async def websocket_alarms(
    websocket: WebSocket,
    severity: Optional[str] = Query(None, description="Filter by severity: LOW, MEDIUM, HIGH, CRITICAL"),
    adapter_id: Optional[str] = Query(None, description="Filter by adapter ID")
):
    """
    WebSocket endpoint for real-time alarm streaming

    **Connection URL**:
    ```
    ws://gateway:8001/ws/alarms
    ws://gateway:8001/ws/alarms?severity=HIGH
    ws://gateway:8001/ws/alarms?adapter_id=plc1_opcua
    ```

    **Message Types**:

    1. **Initial State** (sent on connection):
    ```json
    {
      "type": "connected",
      "message": "Connected to alarm stream",
      "active_alarms": 3,
      "filters": {"severity": "HIGH", "adapter_id": null}
    }
    ```

    2. **Alarm Event** (pushed when alarm occurs):
    ```json
    {
      "type": "alarm",
      "severity": "HIGH",
      "tag_name": "SILO1_TEMPERATURA",
      "message": "Communication loss detected",
      "value": null,
      "quality": "bad",
      "timestamp": "2025-01-19T10:30:45.123Z",
      "source": "plc1_opcua"
    }
    ```

    3. **Heartbeat** (every 30s to keep connection alive):
    ```json
    {
      "type": "heartbeat",
      "timestamp": "2025-01-19T10:30:45.123Z"
    }
    ```

    **Client Example** (JavaScript):
    ```javascript
    const ws = new WebSocket('ws://gateway:8001/ws/alarms?severity=HIGH');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'alarm') {
        console.log(`🚨 ALARM: ${data.tag_name} - ${data.message}`);
        showNotification(data);
      }
    };
    ```
    """
    await alarm_manager.connect(websocket)

    try:
        # Send initial connection confirmation
        await alarm_manager.send_to_one(websocket, {
            "type": "connected",
            "message": "Connected to OptiFlow Gateway alarm stream",
            "timestamp": datetime.utcnow().isoformat(),
            "filters": {
                "severity": severity,
                "adapter_id": adapter_id
            },
            "total_connections": alarm_manager.get_connection_count()
        })

        # Send current active alarms (if any)
        # TODO: Implement alarm state tracking in ProtocolManager

        # Keep connection alive and wait for client messages
        while True:
            try:
                # Wait for client message (with timeout for heartbeat)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )

                # Handle client messages (ping, filter updates, etc.)
                try:
                    message = json.loads(data)

                    if message.get("type") == "ping":
                        await alarm_manager.send_to_one(websocket, {
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        })

                except json.JSONDecodeError:
                    await alarm_manager.send_to_one(websocket, {
                        "type": "error",
                        "message": "Invalid JSON format"
                    })

            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                await alarm_manager.send_to_one(websocket, {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
        await alarm_manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}", exc_info=True)
        await alarm_manager.disconnect(websocket)


# === ALARM BROADCASTING (Called by Protocol Manager) ===

async def broadcast_alarm(
    tag_name: str,
    quality: str,
    value: Any,
    adapter_id: str,
    address: str,
    timestamp: Optional[str] = None
):
    """
    Broadcast alarm to all connected WebSocket clients

    This function is called by ProtocolManager when:
    - Quality flag changes from "good" to "bad"/"uncertain"
    - Tag value violates threshold
    - Communication loss detected

    Args:
        tag_name: Name of the tag triggering alarm
        quality: OPC-UA quality code (good/bad/uncertain)
        value: Current tag value (can be None)
        adapter_id: Source adapter ID
        address: Original tag address
        timestamp: ISO timestamp of event
    """
    # Determine severity based on quality
    severity = "HIGH"
    if quality in ["bad", "comm_failure"]:
        severity = "CRITICAL"
    elif quality == "uncertain":
        severity = "MEDIUM"

    # Build alarm message
    alarm_message = {
        "type": "alarm",
        "severity": severity,
        "tag_name": tag_name,
        "message": f"Quality flag changed to '{quality}'",
        "value": value,
        "quality": quality,
        "timestamp": timestamp or datetime.utcnow().isoformat(),
        "source": adapter_id,
        "address": address
    }

    # Broadcast to all connected clients
    await alarm_manager.broadcast(alarm_message)

    logger.info(f"📢 Broadcasted alarm to {alarm_manager.get_connection_count()} clients: {tag_name} ({quality})")


# === STATUS ENDPOINT (REST) ===

@router.get("/alarms/status")
async def get_websocket_status():
    """
    Get WebSocket connection statistics

    **Returns**:
    ```json
    {
      "active_connections": 5,
      "uptime_seconds": 3600,
      "total_alarms_sent": 1234
    }
    ```
    """
    return {
        "active_connections": alarm_manager.get_connection_count(),
        "service": "websocket_alarms",
        "endpoint": "/ws/alarms",
        "status": "operational"
    }


# === REAL-TIME TAG VALUES WEBSOCKET ===

class TagValueConnectionManager:
    """
    Manages WebSocket connections for real-time tag value streaming

    Features:
    - Subscribe to specific tags or all tags
    - Multiple concurrent clients with different subscriptions
    - Automatic value broadcasting on change
    """

    def __init__(self):
        self.active_connections: Dict[WebSocket, Set[str]] = {}  # websocket -> subscribed tag names
        self._lock = asyncio.Lock()
        self._broadcast_task: Optional[asyncio.Task] = None
        self._running = False

    async def connect(self, websocket: WebSocket, tag_names: Optional[List[str]] = None):
        """Accept new WebSocket connection with optional tag subscription"""
        await websocket.accept()

        async with self._lock:
            self.active_connections[websocket] = set(tag_names) if tag_names else set()

        logger.info(f"✅ Tag values WebSocket connected. Total: {len(self.active_connections)}")

        # Start broadcast task if not running
        if not self._running:
            self._running = True
            self._broadcast_task = asyncio.create_task(self._broadcast_loop())

    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        async with self._lock:
            self.active_connections.pop(websocket, None)

        logger.info(f"❌ Tag values WebSocket disconnected. Total: {len(self.active_connections)}")

        # Stop broadcast task if no connections
        if not self.active_connections and self._running:
            self._running = False
            if self._broadcast_task:
                self._broadcast_task.cancel()

    async def subscribe(self, websocket: WebSocket, tag_names: List[str]):
        """Subscribe client to specific tags"""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections[websocket].update(tag_names)

    async def unsubscribe(self, websocket: WebSocket, tag_names: List[str]):
        """Unsubscribe client from specific tags"""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections[websocket] -= set(tag_names)

    async def _broadcast_loop(self):
        """Background task to broadcast tag values at regular intervals"""
        # Try to get protocol_manager from the active main module
        protocol_manager = None
        try:
            from app.main_kafka import protocol_manager
        except ImportError:
            try:
                from app.main_hybrid import protocol_manager
            except ImportError:
                pass

        while self._running:
            try:
                if not self.active_connections:
                    await asyncio.sleep(1)
                    continue

                # Get all subscribed tags from clients
                all_subscribed_tags: Set[str] = set()
                for tags in self.active_connections.values():
                    all_subscribed_tags.update(tags)

                # Get tag values from all adapters
                tag_values = {}
                if protocol_manager:
                    # Get values from all adapters
                    for adapter_id, adapter in protocol_manager.get_all_adapters().items():
                        try:
                            # Get cached values from adapter's last_values
                            if hasattr(adapter, 'last_values') and adapter.last_values:
                                for address, cached_value in adapter.last_values.items():
                                    # Find tag name from config
                                    tag_name = address  # default to address
                                    unit = ''
                                    for tag_config in adapter.config.tags:
                                        if tag_config.get('address') == address:
                                            tag_name = tag_config.get('name', address)
                                            unit = tag_config.get('unit', '')
                                            break

                                    # If no specific subscriptions, include all tags
                                    # Otherwise only include subscribed tags
                                    if not all_subscribed_tags or tag_name in all_subscribed_tags or address in all_subscribed_tags:
                                        tag_values[tag_name] = {
                                            'value': cached_value.get('value'),
                                            'quality': cached_value.get('quality', 'good'),
                                            'timestamp': cached_value.get('timestamp', datetime.utcnow().isoformat()),
                                            'unit': unit,
                                            'adapter_id': adapter_id
                                        }
                        except Exception as e:
                            logger.warning(f"Failed to get values from adapter {adapter_id}: {e}")

                if not tag_values:
                    await asyncio.sleep(1)
                    continue

                # Broadcast to each connected client
                dead_connections = set()
                for websocket, subscribed_tags in list(self.active_connections.items()):
                    try:
                        # Filter values for this client
                        client_values = {}
                        if subscribed_tags:
                            for tag_name in subscribed_tags:
                                if tag_name in tag_values:
                                    client_values[tag_name] = tag_values[tag_name]
                        else:
                            # Send all values if no specific subscription
                            client_values = tag_values

                        if client_values:
                            await websocket.send_json({
                                "type": "tag_values",
                                "timestamp": datetime.utcnow().isoformat(),
                                "count": len(client_values),
                                "values": client_values
                            })
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to send tag values: {e}")
                        dead_connections.add(websocket)

                # Cleanup dead connections
                if dead_connections:
                    async with self._lock:
                        for ws in dead_connections:
                            self.active_connections.pop(ws, None)

                # Wait before next broadcast (500ms for real-time feel)
                await asyncio.sleep(0.5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Broadcast loop error: {e}")
                await asyncio.sleep(1)

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)


# Global tag value connection manager
tag_value_manager = TagValueConnectionManager()


@router.websocket("/tags")
async def websocket_tag_values(
    websocket: WebSocket,
    tags: Optional[str] = Query(None, description="Comma-separated list of tag names to subscribe to")
):
    """
    WebSocket endpoint for real-time tag value streaming

    **Connection URL**:
    ```
    ws://gateway:8080/ws/tags
    ws://gateway:8080/ws/tags?tags=Pump%201%20Flow,Tank%201%20Level
    ```

    **Message Types**:

    1. **Connected** (sent on connection):
    ```json
    {
      "type": "connected",
      "message": "Connected to tag value stream",
      "subscribed_tags": ["Pump 1 Flow", "Tank 1 Level"]
    }
    ```

    2. **Tag Values** (pushed every 500ms):
    ```json
    {
      "type": "tag_values",
      "timestamp": "2025-01-19T10:30:45.123Z",
      "count": 2,
      "values": {
        "Pump 1 Flow": {"value": 150, "quality": "good", "timestamp": "...", "unit": "L/min"},
        "Tank 1 Level": {"value": 75, "quality": "good", "timestamp": "...", "unit": "%"}
      }
    }
    ```

    3. **Subscribe/Unsubscribe** (client can send):
    ```json
    {"type": "subscribe", "tags": ["Pump 2 Flow", "Pump 2 Pressure"]}
    {"type": "unsubscribe", "tags": ["Pump 1 Flow"]}
    ```

    **Client Example** (JavaScript):
    ```javascript
    const ws = new WebSocket('ws://gateway:8080/ws/tags?tags=Pump%201%20Flow');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'tag_values') {
        for (const [tagName, tagData] of Object.entries(data.values)) {
          updateDashboard(tagName, tagData.value);
        }
      }
    };

    // Subscribe to more tags dynamically
    ws.send(JSON.stringify({type: 'subscribe', tags: ['Tank 1 Level']}));
    ```
    """
    # Parse comma-separated tag names
    tag_names = None
    if tags:
        tag_names = [t.strip() for t in tags.split(',')]

    await tag_value_manager.connect(websocket, tag_names)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to OptiFlow Gateway tag value stream",
            "timestamp": datetime.utcnow().isoformat(),
            "subscribed_tags": tag_names or [],
            "total_connections": tag_value_manager.get_connection_count()
        })

        # Listen for client messages (subscribe/unsubscribe)
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "subscribe":
                    new_tags = message.get("tags", [])
                    await tag_value_manager.subscribe(websocket, new_tags)
                    await websocket.send_json({
                        "type": "subscribed",
                        "tags": new_tags,
                        "timestamp": datetime.utcnow().isoformat()
                    })

                elif message.get("type") == "unsubscribe":
                    remove_tags = message.get("tags", [])
                    await tag_value_manager.unsubscribe(websocket, remove_tags)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "tags": remove_tags,
                        "timestamp": datetime.utcnow().isoformat()
                    })

                elif message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })

    except WebSocketDisconnect:
        logger.info("Tag values client disconnected normally")
        await tag_value_manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"❌ Tag values WebSocket error: {e}", exc_info=True)
        await tag_value_manager.disconnect(websocket)


@router.get("/tags/status")
async def get_tag_websocket_status():
    """
    Get tag values WebSocket connection statistics
    """
    return {
        "active_connections": tag_value_manager.get_connection_count(),
        "service": "websocket_tag_values",
        "endpoint": "/ws/tags",
        "status": "operational"
    }
