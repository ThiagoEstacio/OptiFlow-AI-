"""
Asset Health Score Service
Calculates health scores for assets based on their attributes and thresholds

Health Score (0-100):
- 90-100: Excellent (Green)
- 70-89: Good (Light Green)
- 50-69: Fair (Yellow)
- 30-49: Poor (Orange)
- 0-29: Critical (Red)

Factors considered:
- Attribute values vs thresholds (warning/critical)
- Calculated attribute evaluations
- Tag data quality
- Historical trends (future)
"""

from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.asset import Asset, AssetAttribute
from app.models.tag import Tag
from app.services.asset_calculator import AssetAttributeCalculator, FormulaEvaluationError


class AssetHealthCalculator:
    """Calculate health scores for assets"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.calculator = AssetAttributeCalculator(db)

    async def calculate_asset_health(
        self,
        asset_id: str
    ) -> Dict:
        """
        Calculate comprehensive health score for an asset

        Args:
            asset_id: Asset UUID

        Returns:
            Dictionary with health score and details
        """
        # Get asset
        stmt = select(Asset).where(Asset.id == UUID(asset_id))
        result = await self.db.execute(stmt)
        asset = result.scalar_one_or_none()

        if not asset:
            return {
                "asset_id": asset_id,
                "health_score": None,
                "status": "unknown",
                "error": "Asset not found"
            }

        # Get all attributes
        attrs_stmt = select(AssetAttribute).where(AssetAttribute.asset_id == UUID(asset_id))
        attrs_result = await self.db.execute(attrs_stmt)
        attributes = attrs_result.scalars().all()

        if not attributes:
            return {
                "asset_id": asset_id,
                "asset_name": asset.name,
                "health_score": 100,  # No attributes = assume healthy
                "status": "excellent",
                "message": "No attributes defined - assuming healthy",
                "details": []
            }

        # Evaluate each attribute
        attribute_scores = []
        issues = []
        warnings = []

        for attr in attributes:
            attr_evaluation = await self._evaluate_attribute_health(attr)
            attribute_scores.append(attr_evaluation["score"])

            if attr_evaluation["status"] == "critical":
                issues.append(attr_evaluation["message"])
            elif attr_evaluation["status"] == "warning":
                warnings.append(attr_evaluation["message"])

        # Calculate overall health score
        if attribute_scores:
            overall_score = sum(attribute_scores) / len(attribute_scores)
        else:
            overall_score = 100

        # Determine status
        status = self._get_status_from_score(overall_score)

        return {
            "asset_id": asset_id,
            "asset_name": asset.name,
            "asset_type": asset.asset_type.value if hasattr(asset.asset_type, 'value') else asset.asset_type,
            "health_score": round(overall_score, 2),
            "status": status,
            "attributes_count": len(attributes),
            "issues_count": len(issues),
            "warnings_count": len(warnings),
            "issues": issues,
            "warnings": warnings,
            "timestamp": None,  # TODO: Add timestamp
        }

    async def _evaluate_attribute_health(
        self,
        attribute: AssetAttribute
    ) -> Dict:
        """
        Evaluate health of a single attribute

        Args:
            attribute: AssetAttribute model

        Returns:
            Dictionary with score (0-100) and status
        """
        # Get current value
        current_value = None
        value_error = None

        if attribute.attribute_type == 'tag_reference':
            if attribute.tag_id:
                stmt = select(Tag).where(Tag.id == attribute.tag_id)
                result = await self.db.execute(stmt)
                tag = result.scalar_one_or_none()

                if tag and tag.last_value is not None:
                    try:
                        current_value = float(tag.last_value)
                    except (ValueError, TypeError):
                        value_error = f"Tag value is not numeric: {tag.last_value}"
                else:
                    value_error = "Tag has no value"

        elif attribute.attribute_type == 'static':
            if attribute.static_value:
                try:
                    current_value = float(attribute.static_value)
                except (ValueError, TypeError):
                    value_error = f"Static value is not numeric: {attribute.static_value}"

        elif attribute.attribute_type == 'calculated':
            try:
                current_value = await self.calculator.evaluate_attribute(
                    asset_id=str(attribute.asset_id),
                    attribute_name=attribute.name
                )
            except FormulaEvaluationError as e:
                value_error = f"Formula evaluation failed: {str(e)}"

        # If no value, return poor score
        if current_value is None:
            return {
                "attribute_id": str(attribute.id),
                "attribute_name": attribute.name,
                "score": 50 if value_error else 100,  # 50 if error, 100 if just no data
                "status": "warning" if value_error else "ok",
                "message": value_error or f"No data for {attribute.name}",
                "current_value": None,
            }

        # Check against thresholds
        settings = attribute.settings or {}
        min_val = settings.get('min')
        max_val = settings.get('max')
        warning_threshold = settings.get('warning')
        critical_threshold = settings.get('critical')

        score = 100
        status = "ok"
        message = f"{attribute.name} is healthy"

        # Check critical threshold
        if critical_threshold is not None:
            if current_value >= critical_threshold:
                score = 20
                status = "critical"
                message = f"{attribute.name} is CRITICAL: {current_value} >= {critical_threshold} {attribute.unit or ''}"

        # Check warning threshold
        if warning_threshold is not None and status == "ok":
            if current_value >= warning_threshold:
                score = 60
                status = "warning"
                message = f"{attribute.name} is WARNING: {current_value} >= {warning_threshold} {attribute.unit or ''}"

        # Check min/max bounds
        if min_val is not None and current_value < min_val:
            score = min(score, 40)
            status = "critical"
            message = f"{attribute.name} below minimum: {current_value} < {min_val} {attribute.unit or ''}"

        if max_val is not None and current_value > max_val:
            score = min(score, 40)
            status = "critical"
            message = f"{attribute.name} above maximum: {current_value} > {max_val} {attribute.unit or ''}"

        return {
            "attribute_id": str(attribute.id),
            "attribute_name": attribute.name,
            "score": score,
            "status": status,
            "message": message,
            "current_value": current_value,
            "unit": attribute.unit,
        }

    def _get_status_from_score(self, score: float) -> str:
        """Convert numeric score to status string"""
        if score >= 90:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 50:
            return "fair"
        elif score >= 30:
            return "poor"
        else:
            return "critical"

    async def calculate_hierarchy_health(
        self,
        asset_id: str
    ) -> Dict:
        """
        Calculate health for an asset and all its descendants

        Args:
            asset_id: Root asset UUID

        Returns:
            Hierarchical health report
        """
        # Get asset
        stmt = select(Asset).where(Asset.id == UUID(asset_id))
        result = await self.db.execute(stmt)
        asset = result.scalar_one_or_none()

        if not asset:
            return {"error": "Asset not found"}

        # Calculate own health
        own_health = await self.calculate_asset_health(asset_id)

        # Get children
        children_health = []
        descendants = asset.get_descendants()

        for child in descendants:
            child_health = await self.calculate_asset_health(str(child.id))
            children_health.append(child_health)

        # Calculate rollup score (average of all)
        all_scores = [own_health["health_score"]]
        all_scores.extend([ch["health_score"] for ch in children_health if ch.get("health_score") is not None])

        rollup_score = sum(all_scores) / len(all_scores) if all_scores else 100

        return {
            "asset_id": asset_id,
            "asset_name": asset.name,
            "health_score": own_health["health_score"],
            "rollup_health_score": round(rollup_score, 2),
            "status": self._get_status_from_score(rollup_score),
            "children_count": len(descendants),
            "children_health": children_health,
            "issues_total": own_health["issues_count"] + sum(ch.get("issues_count", 0) for ch in children_health),
            "warnings_total": own_health["warnings_count"] + sum(ch.get("warnings_count", 0) for ch in children_health),
        }


# Convenience function
async def calculate_asset_health(
    db: AsyncSession,
    asset_id: str
) -> Dict:
    """
    Convenience function to calculate asset health

    Args:
        db: Database session
        asset_id: Asset UUID

    Returns:
        Health report dictionary
    """
    calculator = AssetHealthCalculator(db)
    return await calculator.calculate_asset_health(asset_id)
