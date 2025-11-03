"""
API Router - Aggregates all endpoint routers
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    organizations,
    sites,
    users,
    devices,
    tags,
    tag_labels,
    timeseries,
    alarms,
    analytics,
    websocket_analytics,
    ai_insights,
    chat,
    assets,
    monitoring,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(sites.router, prefix="/sites", tags=["Sites"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])
api_router.include_router(tags.router, prefix="/tags", tags=["Tags"])
api_router.include_router(tag_labels.router, prefix="/tag-labels", tags=["Tag Labels"])
api_router.include_router(timeseries.router, prefix="/timeseries", tags=["Time Series"])
api_router.include_router(alarms.router, prefix="/alarms", tags=["Alarms"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(websocket_analytics.router, prefix="/analytics/ws", tags=["Analytics WebSocket"])
api_router.include_router(ai_insights.router, prefix="/ai", tags=["AI Insights"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat & AI Assistant"])
api_router.include_router(assets.router, prefix="/assets", tags=["Asset Framework"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["System Monitoring"])
