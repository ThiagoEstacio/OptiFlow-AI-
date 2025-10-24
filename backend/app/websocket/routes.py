"""
WebSocket routes
"""
from fastapi import APIRouter, WebSocket, Query
from typing import Optional

from app.websocket.handlers import handle_realtime_data, handle_dashboard, handle_smartport, handle_plc_streaming

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


@router.websocket("/smartport")
async def websocket_smartport(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """SmartPort real-time updates WebSocket endpoint"""
    await handle_smartport(websocket, token)


@router.websocket("/plc")
async def websocket_plc(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """PLC real-time streaming WebSocket endpoint"""
    await handle_plc_streaming(websocket, token)
