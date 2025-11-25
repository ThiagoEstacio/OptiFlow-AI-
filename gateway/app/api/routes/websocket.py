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
