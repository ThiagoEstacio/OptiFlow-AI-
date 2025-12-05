"""
Gateway Client Service
======================

Client for communicating with the Gateway Edge microservice.
Provides access to Asset Tree, adapters, tags, and real-time data.
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from functools import lru_cache
import os

logger = logging.getLogger(__name__)

# Gateway URL from environment or default
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://optiflow-gateway:8080")


class GatewayClient:
    """
    HTTP client for Gateway Edge API communication.

    Used by the AI Agent to access Asset Tree and real-time tag data.
    """

    def __init__(self, base_url: str = None):
        self.base_url = base_url or GATEWAY_URL
        self.timeout = 10.0

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        json: Dict = None
    ) -> Dict[str, Any]:
        """Make async HTTP request to Gateway"""
        url = f"{self.base_url}/api{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Gateway request failed: {method} {url} - {e}")
            return {"error": str(e), "success": False}
        except Exception as e:
            logger.error(f"Gateway request error: {e}")
            return {"error": str(e), "success": False}

    # ========================================
    # Asset Tree Methods
    # ========================================

    async def get_asset_hierarchy(self, root_id: str = None) -> Dict[str, Any]:
        """
        Get asset hierarchy tree.

        Args:
            root_id: Optional root element ID to get subtree

        Returns:
            Hierarchy tree structure
        """
        params = {}
        if root_id:
            params["root_id"] = root_id

        return await self._request("GET", "/assets/hierarchy", params=params)

    async def get_asset_element(
        self,
        element_id: str,
        include_children: bool = False
    ) -> Dict[str, Any]:
        """
        Get specific asset element details.

        Args:
            element_id: Element ID or path
            include_children: Include child elements

        Returns:
            Element details with attributes
        """
        # Check if it's a path (starts with /)
        if element_id.startswith('/'):
            endpoint = f"/assets/elements/by-path{element_id}"
            return await self._request("GET", endpoint)
        else:
            params = {"include_children": include_children}
            return await self._request("GET", f"/assets/elements/{element_id}", params=params)

    async def search_assets(
        self,
        query: str,
        element_type: str = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search for assets by name or path.

        Args:
            query: Search query
            element_type: Filter by type (plant, area, equipment_group, equipment, component)
            limit: Max results

        Returns:
            List of matching elements
        """
        params = {
            "search": query,
            "limit": limit
        }
        if element_type:
            params["element_type"] = element_type

        return await self._request("GET", "/assets/elements", params=params)

    async def get_asset_statistics(self) -> Dict[str, Any]:
        """
        Get asset tree statistics.

        Returns:
            Statistics about elements, attributes, templates
        """
        return await self._request("GET", "/assets/statistics")

    async def list_elements(
        self,
        element_type: str = None,
        parent_id: str = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        List elements with filters.

        Args:
            element_type: Filter by type
            parent_id: Filter by parent
            limit: Max results

        Returns:
            List of elements
        """
        params = {"limit": limit}
        if element_type:
            params["element_type"] = element_type
        if parent_id:
            params["parent_id"] = parent_id

        return await self._request("GET", "/assets/elements", params=params)

    # ========================================
    # Adapter & Tag Methods
    # ========================================

    async def get_adapters(self) -> Dict[str, Any]:
        """Get list of configured adapters"""
        return await self._request("GET", "/adapters")

    async def get_adapter_tags(self, adapter_id: str) -> Dict[str, Any]:
        """Get tags for specific adapter"""
        return await self._request("GET", f"/adapters/{adapter_id}/tags")

    async def get_realtime_values(self, tag_ids: List[str] = None) -> Dict[str, Any]:
        """
        Get real-time values for tags.

        Args:
            tag_ids: Optional list of specific tag IDs

        Returns:
            Real-time values for tags
        """
        params = {}
        if tag_ids:
            params["tags"] = ",".join(tag_ids)
        return await self._request("GET", "/realtime/values", params=params)

    async def get_available_tags(
        self,
        adapter_id: str = None,
        search: str = None
    ) -> Dict[str, Any]:
        """
        Get available tags from tags_config.json.

        Args:
            adapter_id: Filter by adapter
            search: Search by name

        Returns:
            List of available tags
        """
        params = {}
        if adapter_id:
            params["adapter_id"] = adapter_id
        if search:
            params["search"] = search

        return await self._request("GET", "/assets/available-tags", params=params)

    # ========================================
    # Health Check
    # ========================================

    async def health_check(self) -> bool:
        """Check if gateway is reachable"""
        try:
            result = await self._request("GET", "")
            return "error" not in result
        except Exception:
            return False


# Singleton instance
_gateway_client: Optional[GatewayClient] = None


def get_gateway_client() -> GatewayClient:
    """Get or create gateway client singleton"""
    global _gateway_client
    if _gateway_client is None:
        _gateway_client = GatewayClient()
    return _gateway_client
