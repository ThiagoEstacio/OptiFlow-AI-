"""
SmartPort API endpoints
"""
from app.api.v1.endpoints.port import vessels, berths, loading, analytics

__all__ = ["vessels", "berths", "loading", "analytics"]
