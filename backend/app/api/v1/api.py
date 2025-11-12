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
    operations,
    ai_engineering,
    advanced_features,
    executive,
    gbm_data,
    historical_analysis,
    gateway_config,
    metrics,
    cache,
    ml_compare,
    dashboards,
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
api_router.include_router(operations.router, prefix="/operations", tags=["Port Operations"])
api_router.include_router(ai_engineering.router, prefix="/ai-engineering", tags=["AI Engineering Tools"])
api_router.include_router(advanced_features.router, prefix="/advanced", tags=["Advanced Features"])
api_router.include_router(executive.router, prefix="/executive", tags=["Executive Dashboard & ROI"])
api_router.include_router(gbm_data.router, prefix="/gbm", tags=["GBM Logistics Data Import & Insights"])
api_router.include_router(historical_analysis.router, prefix="/historical", tags=["Historical Analysis & Trends"])
api_router.include_router(gateway_config.router, prefix="/gateway-config", tags=["Gateway Configuration & OPC-UA Discovery"])
api_router.include_router(cache.router, prefix="/cache", tags=["Cache Management"])
api_router.include_router(ml_compare.router, prefix="/ml", tags=["ML Model Comparison & A/B Testing"])
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["Dashboards & Widgets"])
api_router.include_router(metrics.router, tags=["Monitoring"])  # No prefix - metrics at /api/v1/metrics
