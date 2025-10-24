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
    timeseries,
    alarms,
    export,
    annotations,
    analytics,
    smartport_berths,
    smartport_vessels,
    smartport_operations,
    smartport_dashboard,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(sites.router, prefix="/sites", tags=["Sites"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])
api_router.include_router(tags.router, prefix="/tags", tags=["Tags"])
api_router.include_router(timeseries.router, prefix="/timeseries", tags=["Time Series"])
api_router.include_router(alarms.router, prefix="/alarms", tags=["Alarms"])
api_router.include_router(export.router, prefix="/export", tags=["Data Export"])
api_router.include_router(annotations.router, prefix="/annotations", tags=["Annotations & Collaboration"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Advanced Analytics"])

# SmartPort endpoints
api_router.include_router(smartport_berths.router, prefix="/smartport/berths", tags=["SmartPort - Berths"])
api_router.include_router(smartport_vessels.router, prefix="/smartport/vessels", tags=["SmartPort - Vessels"])
api_router.include_router(smartport_operations.router, prefix="/smartport/operations", tags=["SmartPort - Operations"])
api_router.include_router(smartport_dashboard.router, prefix="/smartport/dashboard", tags=["SmartPort - Dashboard"])
