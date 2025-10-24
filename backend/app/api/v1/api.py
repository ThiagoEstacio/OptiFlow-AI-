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
)

# SmartPort endpoints
from app.api.v1.endpoints.port import (
    vessels,
    berths,
    loading,
    analytics,
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

# SmartPort routers
api_router.include_router(vessels.router, prefix="/port/vessels", tags=["SmartPort - Vessels"])
api_router.include_router(berths.router, prefix="/port/berths", tags=["SmartPort - Berths"])
api_router.include_router(loading.router, prefix="/port/operations", tags=["SmartPort - Operations"])
api_router.include_router(analytics.router, prefix="/port/analytics", tags=["SmartPort - Analytics"])
