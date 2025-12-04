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
    websocket_simulator,
    ai_insights,
    chat,
    assets,
    monitoring,
    operations,
    ai_engineering,
    advanced_features,
    executive,
    executive_summary,
    executive_report,
    gbm_data,
    historical_analysis,
    gateway_config,
    metrics,
    cache,
    ml_compare,
    ml_models,
    ml_drift,
    ml_insights,
    dashboards,
    dashboard_stats,
    oee,
    oee_prediction,
    opcua_tags,
    reports,
    data_quality,
    health,
    database_monitor,
    alarm_partitions,
    websocket_monitor,
    prometheus,
    rate_limits,
    demo,
    quality_analytics,
)
from app.api.routes import consumer_metrics

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
api_router.include_router(websocket_simulator.router, tags=["Real-time Simulator WebSocket"])
api_router.include_router(ai_insights.router, prefix="/ai", tags=["AI Insights"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat & AI Assistant"])
api_router.include_router(assets.router, prefix="/assets", tags=["Asset Framework"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["System Monitoring"])
api_router.include_router(operations.router, prefix="/operations", tags=["Port Operations"])
api_router.include_router(ai_engineering.router, prefix="/ai-engineering", tags=["AI Engineering Tools"])
api_router.include_router(advanced_features.router, prefix="/advanced", tags=["Advanced Features"])
api_router.include_router(executive.router, prefix="/executive", tags=["Executive Dashboard & ROI"])
api_router.include_router(executive_summary.router, prefix="/executive-summary", tags=["Executive Summary & KPIs"])
api_router.include_router(executive_report.router, prefix="/executive-report", tags=["Executive Report PDF Generation"])
api_router.include_router(gbm_data.router, prefix="/gbm", tags=["GBM Logistics Data Import & Insights"])
api_router.include_router(historical_analysis.router, prefix="/historical", tags=["Historical Analysis & Trends"])
api_router.include_router(gateway_config.router, prefix="/gateway-config", tags=["Gateway Configuration & OPC-UA Discovery"])
api_router.include_router(cache.router, prefix="/cache", tags=["Cache Management"])
api_router.include_router(ml_compare.router, prefix="/ml", tags=["ML Model Comparison & A/B Testing"])
api_router.include_router(ml_models.router, prefix="/ml/models", tags=["ML Model Training & Management"])
api_router.include_router(ml_drift.router, prefix="/ml/drift", tags=["ML Drift Detection & Monitoring"])
api_router.include_router(ml_insights.router, prefix="/ml", tags=["ML Insights & Analytics"])
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["Dashboards & Widgets"])
api_router.include_router(dashboard_stats.router, prefix="/dashboard", tags=["Dashboard Statistics"])
api_router.include_router(oee.router, prefix="/oee", tags=["OEE - Overall Equipment Effectiveness"])
api_router.include_router(oee_prediction.router, tags=["OEE Predictions & Early Warnings"])
api_router.include_router(opcua_tags.router, prefix="/opcua", tags=["OPC UA Tag Browser"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports & Export"])
api_router.include_router(data_quality.router, prefix="/data-quality", tags=["Data Quality Analytics"])
api_router.include_router(health.router, prefix="/health", tags=["Health Checks"])
api_router.include_router(database_monitor.router, prefix="/database", tags=["Database Monitoring & Circuit Breakers"])
api_router.include_router(alarm_partitions.router, prefix="/alarm-partitions", tags=["Alarm Partition Management"])
api_router.include_router(websocket_monitor.router, prefix="/websocket-monitor", tags=["WebSocket Connection Pool Monitoring"])
api_router.include_router(prometheus.router, prefix="/prometheus", tags=["Prometheus Metrics Export"])
api_router.include_router(rate_limits.router, prefix="/rate-limits", tags=["Rate Limiting & Throttling"])
api_router.include_router(demo.router, prefix="/demo", tags=["Demo & Development Helpers"])
api_router.include_router(quality_analytics.router, prefix="/quality", tags=["Quality Analytics - SPC, Pareto, Ishikawa, PDCA"])
api_router.include_router(metrics.router, tags=["Monitoring"])  # No prefix - metrics at /api/v1/metrics
api_router.include_router(consumer_metrics.router, tags=["Pipeline Metrics"])  # Pipeline health endpoints at /api/v1/metrics/
