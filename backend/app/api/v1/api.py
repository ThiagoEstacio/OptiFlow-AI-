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
    discovery,
    points,
    annotations,
    visualization,
    explorer,
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
api_router.include_router(discovery.router, prefix="/discovery", tags=["Discovery"])
api_router.include_router(points.router, prefix="/points", tags=["Point Builder"])
api_router.include_router(annotations.router, prefix="/annotations", tags=["Annotations"])
api_router.include_router(visualization.router, prefix="/visualization", tags=["Visualization"])
api_router.include_router(explorer.router, prefix="/explorer", tags=["Tag Explorer"])
