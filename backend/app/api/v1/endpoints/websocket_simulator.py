"""
WebSocket endpoint for real-time simulator data streaming
Broadcasts simulator values to all connected clients
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import asyncio
import json
import logging
from datetime import datetime

from app.services.lightweight_simulator import get_simulator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class SimulatorStreamManager:
    """Manages WebSocket connections for real-time simulator streaming"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.streaming_task: asyncio.Task | None = None
        self.is_streaming = False

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"✅ New WebSocket connection. Total: {len(self.active_connections)}")

        # Start streaming if not already running
        if not self.is_streaming:
            await self.start_streaming()

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.discard(websocket)
        logger.info(f"❌ WebSocket disconnected. Remaining: {len(self.active_connections)}")

        # Stop streaming if no connections
        if len(self.active_connections) == 0 and self.is_streaming:
            self.stop_streaming()

    async def start_streaming(self):
        """Start simulator streaming task"""
        if self.is_streaming:
            return

        self.is_streaming = True
        logger.info("🚀 Starting simulator real-time streaming...")

        # Start streaming task
        self.streaming_task = asyncio.create_task(self._stream_loop())

    def stop_streaming(self):
        """Stop simulator streaming task"""
        if not self.is_streaming:
            return

        self.is_streaming = False

        if self.streaming_task:
            self.streaming_task.cancel()
            self.streaming_task = None

        logger.info("⏹️  Stopped simulator streaming")

    async def _stream_loop(self):
        """Main streaming loop - reads simulator and broadcasts to all clients"""
        try:
            while self.is_streaming:
                # Get simulator instance
                sim = get_simulator()

                # Get all current tag values
                all_tags = sim.get_all_tags()

                # Get system status
                status = sim.get_status()

                # Prepare message with both tags and status
                message = {
                    "type": "simulator_update",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "tags": all_tags,
                    "status": status
                }

                # Broadcast to all connected clients
                await self.broadcast(json.dumps(message))

                # Wait before next update (1 second = 1Hz update rate)
                await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            logger.info("Streaming task cancelled")
        except Exception as e:
            logger.error(f"Error in streaming loop: {e}", exc_info=True)
            self.is_streaming = False

    async def broadcast(self, message: str):
        """Send message to all connected clients"""
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(connection)

        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


# Global manager instance
simulator_stream_manager = SimulatorStreamManager()


@router.websocket("/simulator/stream")
async def websocket_simulator_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time simulator data

    Connect: ws://localhost:8000/api/v1/ws/simulator/stream

    Receives JSON messages every second:
    {
        "type": "simulator_update",
        "timestamp": "2025-11-13T10:30:45.123Z",
        "tags": {
            "TEST_COUNTER_PV": 5.0,
            "WAREHOUSE_LEVEL_PCT_PV": 72.3,
            "CORR01_POWER_KW_PV": 45.2,
            ...
        },
        "status": {
            "system": {...},
            "gates": [...],
            "belts": [...],
            "shiploader": {...}
        }
    }

    Client can send commands:
    - {"type": "ping"} -> Receives {"type": "pong"}
    - {"type": "get_tags"} -> Receives list of available tags
    """
    await simulator_stream_manager.connect(websocket)

    try:
        # Keep connection alive and handle client messages
        while True:
            data = await websocket.receive_text()

            # Handle client commands
            try:
                command = json.loads(data)

                if command.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat() + "Z"})

                elif command.get("type") == "get_tags":
                    sim = get_simulator()
                    all_tags = sim.get_all_tags()
                    await websocket.send_json({
                        "type": "tags_list",
                        "tags": list(all_tags.keys()),
                        "count": len(all_tags)
                    })

                elif command.get("type") == "get_status":
                    sim = get_simulator()
                    status = sim.get_status()
                    await websocket.send_json({
                        "type": "status",
                        "data": status
                    })

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        simulator_stream_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        simulator_stream_manager.disconnect(websocket)
