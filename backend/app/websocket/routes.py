"""
WebSocket routes
"""
from fastapi import APIRouter, WebSocket, Query
from typing import Optional

from app.websocket.handlers import handle_realtime_data, handle_dashboard

router = APIRouter()


@router.websocket("/realtime")
async def websocket_realtime(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """Real-time data streaming WebSocket endpoint"""
    await handle_realtime_data(websocket, token)


@router.websocket("/dashboard/{dashboard_id}")
async def websocket_dashboard(
    websocket: WebSocket,
    dashboard_id: str,
    token: Optional[str] = Query(None)
):
    """Dashboard-specific WebSocket endpoint"""
    await handle_dashboard(websocket, dashboard_id, token)
