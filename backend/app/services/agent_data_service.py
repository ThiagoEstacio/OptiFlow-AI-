"""
Agent Data Service - Provides data access tools for AI Agent
Allows the agent to query tags, values, and perform calculations
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
import statistics

from app.models.gateway_config import GatewayConfig, GatewayTag


class AgentDataService:
    """
    Service that provides data access methods for the AI agent.
    The agent can use these tools to answer questions about the system.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_tags(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for tags by name or description.

        Args:
            search_term: Term to search for in tag name or description
            limit: Maximum number of results

        Returns:
            List of matching tags with their info
        """
        try:
            search_pattern = f"%{search_term}%"
            query = select(GatewayTag).where(
                or_(
                    GatewayTag.tag_name.ilike(search_pattern),
                    GatewayTag.description.ilike(search_pattern)
                )
            ).where(
                GatewayTag.enabled == True
            ).limit(limit)

            result = await self.db.execute(query)
            tags = result.scalars().all()

            return [
                {
                    "id": tag.id,
                    "name": tag.tag_name,
                    "description": tag.description or "No description",
                    "unit": tag.unit or "",
                    "data_type": tag.data_type,
                    "gateway_id": tag.gateway_id
                }
                for tag in tags
            ]
        except Exception as e:
            print(f"Error searching tags: {e}")
            return []

    async def get_tag_by_name(self, tag_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific tag by exact name match.

        Args:
            tag_name: Exact tag name

        Returns:
            Tag info or None
        """
        try:
            query = select(GatewayTag).where(
                and_(
                    GatewayTag.tag_name == tag_name,
                    GatewayTag.enabled == True
                )
            )

            result = await self.db.execute(query)
            tag = result.scalar_one_or_none()

            if not tag:
                return None

            return {
                "id": tag.id,
                "name": tag.tag_name,
                "description": tag.description or "No description",
                "unit": tag.unit or "",
                "data_type": tag.data_type,
                "gateway_id": tag.gateway_id,
                "scale_factor": tag.scale_factor,
                "offset": tag.offset
            }
        except Exception as e:
            print(f"Error getting tag by name: {e}")
            return None

    async def list_tags_by_pattern(self, pattern: str = "", limit: int = 50) -> List[Dict[str, Any]]:
        """
        List tags matching a pattern (e.g., "CORR%" for all conveyor tags).

        Args:
            pattern: SQL LIKE pattern (use % as wildcard)
            limit: Maximum number of results

        Returns:
            List of tags
        """
        try:
            if pattern:
                query = select(GatewayTag).where(
                    and_(
                        GatewayTag.tag_name.like(pattern),
                        GatewayTag.enabled == True
                    )
                ).limit(limit)
            else:
                query = select(GatewayTag).where(
                    GatewayTag.enabled == True
                ).limit(limit)

            result = await self.db.execute(query)
            tags = result.scalars().all()

            return [
                {
                    "name": tag.tag_name,
                    "description": tag.description or "",
                    "unit": tag.unit or "",
                    "data_type": tag.data_type
                }
                for tag in tags
            ]
        except Exception as e:
            print(f"Error listing tags: {e}")
            return []

    async def get_tag_statistics(self, tag_names: List[str]) -> Dict[str, Any]:
        """
        Get statistics about a set of tags.

        Args:
            tag_names: List of tag names

        Returns:
            Statistics dictionary
        """
        try:
            query = select(GatewayTag).where(
                and_(
                    GatewayTag.tag_name.in_(tag_names),
                    GatewayTag.enabled == True
                )
            )

            result = await self.db.execute(query)
            tags = result.scalars().all()

            return {
                "total_tags": len(tags),
                "tags": [
                    {
                        "name": tag.tag_name,
                        "description": tag.description,
                        "unit": tag.unit,
                        "data_type": tag.data_type
                    }
                    for tag in tags
                ]
            }
        except Exception as e:
            print(f"Error getting tag statistics: {e}")
            return {"total_tags": 0, "tags": []}

    async def get_gateway_info(self, gateway_id: int = 1) -> Optional[Dict[str, Any]]:
        """
        Get information about a gateway.

        Args:
            gateway_id: Gateway ID

        Returns:
            Gateway information
        """
        try:
            query = select(GatewayConfig).where(GatewayConfig.id == gateway_id)
            result = await self.db.execute(query)
            gateway = result.scalar_one_or_none()

            if not gateway:
                return None

            # Count tags
            count_query = select(func.count(GatewayTag.id)).where(
                and_(
                    GatewayTag.gateway_id == gateway_id,
                    GatewayTag.enabled == True
                )
            )
            count_result = await self.db.execute(count_query)
            tag_count = count_result.scalar() or 0

            return {
                "id": gateway.id,
                "name": gateway.name,
                "description": gateway.description,
                "endpoint_url": gateway.endpoint_url,
                "is_active": gateway.is_active,
                "total_tags": tag_count
            }
        except Exception as e:
            print(f"Error getting gateway info: {e}")
            return None

    async def search_tags_by_category(self, category_keyword: str) -> List[Dict[str, Any]]:
        """
        Search tags by category keywords (e.g., "speed", "temperature", "pressure").

        Args:
            category_keyword: Keyword to search

        Returns:
            List of relevant tags
        """
        # Map common keywords to tag patterns
        keyword_map = {
            "velocidade": ["speed", "velocidade", "vel"],
            "speed": ["speed", "velocidade", "vel"],
            "temperatura": ["temp", "temperatura", "temperature"],
            "temperature": ["temp", "temperatura", "temperature"],
            "pressao": ["press", "pressao", "pressure"],
            "pressure": ["press", "pressao", "pressure"],
            "correia": ["corr", "belt", "conveyor"],
            "conveyor": ["corr", "belt", "conveyor"],
            "motor": ["motor", "engine"],
            "nivel": ["level", "nivel"],
            "level": ["level", "nivel"]
        }

        search_terms = keyword_map.get(category_keyword.lower(), [category_keyword.lower()])

        try:
            # Build OR condition for all search terms
            conditions = []
            for term in search_terms:
                pattern = f"%{term}%"
                conditions.append(GatewayTag.tag_name.ilike(pattern))
                conditions.append(GatewayTag.description.ilike(pattern))

            query = select(GatewayTag).where(
                and_(
                    or_(*conditions),
                    GatewayTag.enabled == True
                )
            ).limit(30)

            result = await self.db.execute(query)
            tags = result.scalars().all()

            return [
                {
                    "name": tag.tag_name,
                    "description": tag.description or "",
                    "unit": tag.unit or "",
                    "data_type": tag.data_type
                }
                for tag in tags
            ]
        except Exception as e:
            print(f"Error searching by category: {e}")
            return []
