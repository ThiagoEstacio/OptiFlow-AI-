"""
SmartPort API Router
"""
from fastapi import APIRouter

from app.port.api import vessels, loading

# Create SmartPort router
smartport_router = APIRouter()

# Include all SmartPort endpoint routers
smartport_router.include_router(vessels.router, prefix="/vessels", tags=["SmartPort - Vessels"])
smartport_router.include_router(loading.router, prefix="/loading", tags=["SmartPort - Loading Operations"])

__all__ = ["smartport_router"]
