"""
Tags Routes - Combined router for all tag-related endpoints

This module combines:
- tags_realtime: Real-time tag value access
- tags_advanced: Tag management (CRUD, templates, statistics)
- tags_automation: Formulas, alarms, events, actions
"""

from fastapi import APIRouter

# Import sub-routers
from app.api.routes.tags_realtime import router as realtime_router
from app.api.routes.tags_advanced import router as advanced_router
from app.api.routes.tags_automation import router as automation_router

# Main tags router
router = APIRouter()

# Include all tag-related routes
router.include_router(realtime_router, tags=["Tag Values"])
router.include_router(advanced_router, tags=["Tag Management"])
router.include_router(automation_router, tags=["Tag Automation"])
