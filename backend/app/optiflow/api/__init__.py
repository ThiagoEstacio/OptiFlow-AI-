"""
OptiFlow Core API Router
"""
from fastapi import APIRouter

from app.optiflow.api import devices, tags, timeseries, users, alarms

# Create OptiFlow router
optiflow_router = APIRouter()

# Include all OptiFlow endpoint routers
optiflow_router.include_router(users.router, prefix="/users", tags=["OptiFlow - Users"])
optiflow_router.include_router(devices.router, prefix="/devices", tags=["OptiFlow - Devices"])
optiflow_router.include_router(tags.router, prefix="/tags", tags=["OptiFlow - Tags"])
optiflow_router.include_router(timeseries.router, prefix="/timeseries", tags=["OptiFlow - TimeSeries"])
optiflow_router.include_router(alarms.router, prefix="/alarms", tags=["OptiFlow - Alarms"])

__all__ = ["optiflow_router"]
