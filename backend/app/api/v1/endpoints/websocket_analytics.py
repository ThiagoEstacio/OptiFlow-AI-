"""
WebSocket Analytics Endpoints

Real-time streaming analytics with live data updates:
- WS /stream: Stream analytics query results in real-time
- Supports auto-refresh at configurable intervals
- Live data updates as new measurements arrive
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import asyncio
import json
from datetime import datetime, timedelta
import logging

from app.core.deps import get_db
from app.schemas.analytics import AnalyticsQueryRequest
from app.services.analytics import AnalyticsService

router = APIRouter()
logger = logging.getLogger(__name__)


class AnalyticsStreamManager:
    """Manages WebSocket connections for streaming analytics"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket connected: {client_id}")

    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket disconnected: {client_id}")

    async def send_data(self, client_id: str, data: dict):
        """Send data to specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Error sending data to {client_id}: {e}")
                self.disconnect(client_id)

    async def send_error(self, client_id: str, error: str):
        """Send error message to client"""
        await self.send_data(
            client_id, {"type": "error", "message": error, "timestamp": datetime.utcnow().isoformat()}
        )


# Global stream manager
stream_manager = AnalyticsStreamManager()


@router.websocket("/stream")
async def stream_analytics(
    websocket: WebSocket,
    token: str = Query(...),  # JWT token for authentication
):
    """
    WebSocket endpoint for streaming analytics data

    Protocol:
    1. Client connects with JWT token
    2. Client sends query configuration:
       {
         "query": { ... analytics query ... },
         "refresh_interval": 5,  // seconds
         "mode": "continuous" | "windowed"
       }
    3. Server streams results at refresh_interval
    4. Client can send control messages:
       - {"action": "pause"} - Pause streaming
       - {"action": "resume"} - Resume streaming
       - {"action": "stop"} - Stop and disconnect
       - {"action": "update_query", "query": {...}} - Update query

    Response format:
    {
      "type": "data" | "error" | "status",
      "data": { ... query result ... },
      "timestamp": "2024-01-01T00:00:00",
      "sequence": 123
    }
    """

    # Generate unique client ID
    client_id = f"client_{id(websocket)}"

    # TODO: Validate JWT token (for now, accept all connections)
    # In production, you should:
    # 1. Decode and validate the JWT token
    # 2. Get user from token
    # 3. Check user permissions

    await stream_manager.connect(websocket, client_id)

    # Stream state
    streaming = False
    paused = False
    query_config = None
    refresh_interval = 5  # default 5 seconds
    sequence = 0

    try:
        # Wait for initial query configuration
        await websocket.send_json({
            "type": "status",
            "message": "Connected. Send query configuration to start streaming.",
            "timestamp": datetime.utcnow().isoformat()
        })

        # Main message loop
        while True:
            # Check for incoming messages (with timeout)
            try:
                message = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=0.1 if streaming and not paused else None
                )

                action = message.get("action")

                if action == "start" or action == "update_query":
                    # Start or update streaming
                    query_config = message.get("query")
                    refresh_interval = message.get("refresh_interval", 5)
                    mode = message.get("mode", "continuous")

                    if not query_config:
                        await stream_manager.send_error(client_id, "Query configuration required")
                        continue

                    streaming = True
                    paused = False
                    sequence = 0

                    await websocket.send_json({
                        "type": "status",
                        "message": f"Streaming started (refresh every {refresh_interval}s)",
                        "timestamp": datetime.utcnow().isoformat()
                    })

                elif action == "pause":
                    paused = True
                    await websocket.send_json({
                        "type": "status",
                        "message": "Streaming paused",
                        "timestamp": datetime.utcnow().isoformat()
                    })

                elif action == "resume":
                    paused = False
                    await websocket.send_json({
                        "type": "status",
                        "message": "Streaming resumed",
                        "timestamp": datetime.utcnow().isoformat()
                    })

                elif action == "stop":
                    streaming = False
                    await websocket.send_json({
                        "type": "status",
                        "message": "Streaming stopped",
                        "timestamp": datetime.utcnow().isoformat()
                    })

                else:
                    await stream_manager.send_error(client_id, f"Unknown action: {action}")

            except asyncio.TimeoutError:
                # No message received, continue to data streaming
                pass

            # Execute query and send results if streaming is active
            if streaming and not paused and query_config:
                try:
                    # Create analytics service (need to get DB session)
                    # For WebSocket, we'll create a new session for each query
                    from app.db.session import AsyncSessionLocal

                    async with SessionLocal() as db:
                        analytics_service = AnalyticsService(db)

                        # Parse query
                        query_request = AnalyticsQueryRequest(**query_config)

                        # Execute query
                        result = await analytics_service.execute_query(query_request)

                        # Send result
                        sequence += 1
                        await websocket.send_json({
                            "type": "data",
                            "data": {
                                "query_id": result.query_id,
                                "executed_at": result.executed_at,
                                "execution_time_ms": result.execution_time_ms,
                                "tags": result.tags,
                                "aggregations": [
                                    {
                                        "function": agg.function,
                                        "field": agg.field,
                                        "window": agg.window,
                                        "values": [
                                            {
                                                "timestamp": v.timestamp,
                                                "value": v.value,
                                                "tag_id": v.tag_id
                                            }
                                            for v in agg.values
                                        ],
                                        "summary": agg.summary
                                    }
                                    for agg in result.aggregations
                                ],
                                "metadata": {
                                    "total_records": result.metadata.total_records,
                                    "time_range": {
                                        "start": result.metadata.time_range.start,
                                        "end": result.metadata.time_range.end
                                    }
                                }
                            },
                            "timestamp": datetime.utcnow().isoformat(),
                            "sequence": sequence
                        })

                    # Wait for refresh interval
                    await asyncio.sleep(refresh_interval)

                except Exception as e:
                    logger.error(f"Error executing streaming query: {e}")
                    await stream_manager.send_error(client_id, f"Query execution error: {str(e)}")
                    streaming = False

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        await stream_manager.send_error(client_id, f"Server error: {str(e)}")
    finally:
        stream_manager.disconnect(client_id)


@router.websocket("/stream-simple")
async def stream_analytics_simple(
    websocket: WebSocket,
    tag_ids: str = Query(...),  # Comma-separated tag IDs
    refresh_interval: int = Query(5),  # Seconds
    window: str = Query("1h"),  # Time window (e.g., "1h", "30m")
):
    """
    Simplified WebSocket endpoint for streaming recent tag values

    Parameters:
    - tag_ids: Comma-separated tag IDs (e.g., "tag1,tag2,tag3")
    - refresh_interval: Refresh interval in seconds (default: 5)
    - window: Time window for data (e.g., "1h", "30m", "1d")

    Streams the mean value for each tag over the specified window,
    updated at the refresh interval.

    Response format:
    {
      "timestamp": "2024-01-01T00:00:00",
      "values": {
        "tag1": 123.45,
        "tag2": 67.89
      }
    }
    """

    client_id = f"simple_client_{id(websocket)}"
    await stream_manager.connect(websocket, client_id)

    # Parse tag IDs
    tags = [tag.strip() for tag in tag_ids.split(",")]

    try:
        await websocket.send_json({
            "type": "status",
            "message": f"Streaming {len(tags)} tags every {refresh_interval}s",
            "tags": tags
        })

        while True:
            try:
                from app.db.session import AsyncSessionLocal

                async with SessionLocal() as db:
                    analytics_service = AnalyticsService(db)

                    # Build simple query for each tag
                    now = datetime.utcnow()

                    # Parse window
                    if window.endswith("h"):
                        hours = int(window[:-1])
                        start = now - timedelta(hours=hours)
                    elif window.endswith("m"):
                        minutes = int(window[:-1])
                        start = now - timedelta(minutes=minutes)
                    elif window.endswith("d"):
                        days = int(window[:-1])
                        start = now - timedelta(days=days)
                    else:
                        start = now - timedelta(hours=1)  # default 1 hour

                    # Simple query: mean for each tag
                    query = AnalyticsQueryRequest(
                        tags=tags,
                        start=start,
                        end=now,
                        aggregations=[
                            {
                                "function": "mean",
                                "field": "value",
                                "window": window
                            }
                        ],
                        limit=1000
                    )

                    result = await analytics_service.execute_query(query)

                    # Extract values
                    values = {}
                    if result.aggregations:
                        for agg in result.aggregations:
                            for val in agg.values:
                                if val.tag_id:
                                    values[val.tag_id] = val.value

                    # Send simplified response
                    await websocket.send_json({
                        "timestamp": datetime.utcnow().isoformat(),
                        "values": values
                    })

                # Wait for refresh interval
                await asyncio.sleep(refresh_interval)

            except Exception as e:
                logger.error(f"Error in simple streaming: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                await asyncio.sleep(refresh_interval)

    except WebSocketDisconnect:
        logger.info(f"Simple client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
    finally:
        stream_manager.disconnect(client_id)
