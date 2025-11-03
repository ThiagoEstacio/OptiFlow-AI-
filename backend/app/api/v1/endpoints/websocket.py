"""
WebSocket endpoint for real-time tag values streaming
Connects directly to OPC UA server without database intermediary
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional, Set
import asyncio
import json
import logging
from datetime import datetime

from app.services.opcua_tag_reader import OPCUATagReader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class TagStreamManager:
    """Manages WebSocket connections for real-time tag streaming"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.opcua_reader: Optional[OPCUATagReader] = None
        self.streaming_task: Optional[asyncio.Task] = None
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
        """Start OPC UA streaming task"""
        if self.is_streaming:
            return
            
        self.is_streaming = True
        logger.info("🚀 Starting OPC UA streaming...")
        
        # Connect to OPC UA server
        opcua_endpoint = "opc.tcp://opcua-server:4840/optiflow/terminal"
        self.opcua_reader = OPCUATagReader(opcua_endpoint)
        
        if not await self.opcua_reader.connect():
            logger.error("❌ Failed to connect to OPC UA server")
            self.is_streaming = False
            return
        
        logger.info("✅ Connected to OPC UA server")
        
        # Start streaming task
        self.streaming_task = asyncio.create_task(self._stream_loop())
    
    def stop_streaming(self):
        """Stop OPC UA streaming task"""
        if not self.is_streaming:
            return
            
        self.is_streaming = False
        
        if self.streaming_task:
            self.streaming_task.cancel()
            self.streaming_task = None
        
        if self.opcua_reader:
            asyncio.create_task(self.opcua_reader.disconnect())
            self.opcua_reader = None
        
        logger.info("⏹️  Stopped OPC UA streaming")
    
    async def _stream_loop(self):
        """Main streaming loop - reads OPC UA and broadcasts to all clients"""
        # Key nodes to stream (you can expand this)
        monitored_nodes = [
            # Gates
            "ns=2;i=8",   # GATE01.POSICAO.PV
            "ns=2;i=10",  # GATE01.VAZAO.PV
            "ns=2;i=13",  # GATE02.POSICAO.PV
            "ns=2;i=15",  # GATE02.VAZAO.PV
            "ns=2;i=18",  # GATE03.POSICAO.PV
            "ns=2;i=20",  # GATE03.VAZAO.PV
            # Conveyor 1
            "ns=2;i=58",  # CORR01.LIGADO.FB
            "ns=2;i=60",  # CORR01.VELOCIDADE.PV
            "ns=2;i=61",  # CORR01.VAZAO.PV
            "ns=2;i=66",  # CORR01.TEMP_CORREIA.PV
            # KPIs
            "ns=2;i=130", # ENERGIA_TOTAL.TOT
            "ns=2;i=131", # PRODUCAO_TOTAL.TOT
            "ns=2;i=132", # EFICIENCIA_ENERGIA.PV
        ]
        
        try:
            while self.is_streaming:
                # Read values from OPC UA
                values = await self.opcua_reader.read_multiple_tags(monitored_nodes)
                
                # Prepare message
                message = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "values": {}
                }
                
                for node_id, data in values.items():
                    message["values"][node_id] = {
                        "value": data["value"],
                        "quality": data["quality"],
                        "timestamp": data["timestamp"].isoformat()
                    }
                
                # Broadcast to all connected clients
                await self.broadcast(json.dumps(message))
                
                # Wait before next update (1 second = 1Hz update rate)
                await asyncio.sleep(1.0)
                
        except asyncio.CancelledError:
            logger.info("Streaming task cancelled")
        except Exception as e:
            logger.error(f"Error in streaming loop: {e}")
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
stream_manager = TagStreamManager()


@router.websocket("/tags/stream")
async def websocket_tags_stream(
    websocket: WebSocket,
    device_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time tag values
    
    Connect: ws://localhost:8000/api/v1/ws/tags/stream
    
    Receives JSON messages every second:
    {
        "timestamp": "2025-10-31T10:30:45.123",
        "values": {
            "ns=2;i=8": {
                "value": "90.0",
                "quality": "Good",
                "timestamp": "2025-10-31T10:30:45.120"
            },
            ...
        }
    }
    """
    await stream_manager.connect(websocket)
    
    try:
        # Keep connection alive and handle client messages
        while True:
            data = await websocket.receive_text()
            
            # Handle client commands (e.g., subscribe to specific tags)
            try:
                command = json.loads(data)
                
                if command.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif command.get("type") == "subscribe":
                    # Future: implement selective tag subscription
                    pass
                    
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
                
    except WebSocketDisconnect:
        stream_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        stream_manager.disconnect(websocket)
