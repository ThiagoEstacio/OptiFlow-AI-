"""
MELH-007: Spare Parts Recommendation API Endpoints

Provides REST endpoints for spare parts management:
- Recommend parts for failures
- Proactive ordering based on ML predictions
- Inventory status tracking
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


def get_spare_parts_service():
    """Get spare parts service instance"""
    try:
        from app.services.maintenance.spare_parts import get_spare_parts_service as get_service
        return get_service()
    except ImportError as e:
        logger.warning(f"Spare parts service not available: {e}")
        return None


@router.post("/recommend/{equipment_id}")
async def recommend_spare_parts(
    equipment_id: str,
    failure_type: str = Query(..., description="Type of failure (mechanical, electrical, instrumentation)"),
    include_optional: bool = Query(default=True, description="Include optional parts"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Recommend spare parts for equipment failure.

    MELH-007: Based on historical maintenance data, recommends parts
    likely needed for the specified failure type.

    Args:
        equipment_id: Equipment identifier
        failure_type: Type of failure
        include_optional: Include optional parts in recommendations

    Returns:
        Prioritized list of recommended spare parts with stock status
    """
    service = get_spare_parts_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Spare parts service not available"
        )

    try:
        logger.info(f"Recommending parts for {equipment_id}, failure: {failure_type}")

        recommendation = await service.recommend(
            equipment_id=equipment_id,
            failure_type=failure_type,
            include_optional=include_optional
        )

        result = service.to_dict(recommendation)
        result["success"] = True

        return result

    except Exception as e:
        logger.error(f"Error recommending parts: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate parts recommendation: {str(e)}"
        )


@router.post("/recommend/predicted/{equipment_id}")
async def recommend_for_predicted_failure(
    equipment_id: str,
    failure_type: str = Query(..., description="Predicted failure type"),
    prediction_confidence: float = Query(..., ge=0.0, le=1.0, description="ML prediction confidence"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Proactive parts recommendation for predicted failure.

    Uses ML prediction results to proactively suggest parts ordering
    before failure actually occurs.

    Args:
        equipment_id: Equipment identifier
        failure_type: ML-predicted failure type
        prediction_confidence: Confidence of the prediction (0-1)

    Returns:
        Proactive parts recommendation with ordering suggestions
    """
    service = get_spare_parts_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Spare parts service not available"
        )

    try:
        logger.info(f"Proactive recommendation for {equipment_id}, confidence: {prediction_confidence}")

        recommendation = await service.recommend_for_predicted_failure(
            equipment_id=equipment_id,
            predicted_failure_type=failure_type,
            prediction_confidence=prediction_confidence
        )

        result = service.to_dict(recommendation)
        result["success"] = True
        result["proactive"] = True
        result["prediction_confidence"] = prediction_confidence

        # Add urgency indicator
        if prediction_confidence > 0.8:
            result["urgency"] = "high"
            result["recommendation"] = "Order critical parts immediately"
        elif prediction_confidence > 0.6:
            result["urgency"] = "medium"
            result["recommendation"] = "Review stock levels and place orders if needed"
        else:
            result["urgency"] = "low"
            result["recommendation"] = "Monitor situation, no immediate action required"

        return result

    except Exception as e:
        logger.error(f"Error in proactive recommendation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate proactive recommendation: {str(e)}"
        )


@router.get("/inventory")
async def get_inventory_status(
    category: Optional[str] = Query(default=None, description="Filter by category"),
    status: Optional[str] = Query(default=None, description="Filter by status (ok, low, out)"),
    current_user: User = Depends(get_current_user)
):
    """
    Get current inventory status for spare parts.

    Returns stock levels, reorder points, and status for all tracked parts.
    """
    service = get_spare_parts_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Spare parts service not available"
        )

    try:
        inventory = await service.get_inventory_status()

        # Apply filters
        parts = inventory["parts"]
        if category:
            parts = [p for p in parts if p["category"] == category.lower()]
        if status:
            parts = [p for p in parts if p["status"] == status.lower()]

        inventory["parts"] = parts
        inventory["success"] = True

        return inventory

    except Exception as e:
        logger.error(f"Error getting inventory: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get inventory status: {str(e)}"
        )


@router.get("/inventory/alerts")
async def get_inventory_alerts(
    current_user: User = Depends(get_current_user)
):
    """
    Get inventory alerts for parts needing attention.

    Returns parts with low stock or out of stock status.
    """
    service = get_spare_parts_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Spare parts service not available"
        )

    try:
        inventory = await service.get_inventory_status()

        alerts = []
        for part in inventory["parts"]:
            if part["status"] == "out":
                alerts.append({
                    "code": part["code"],
                    "description": part["description"],
                    "severity": "critical",
                    "message": f"OUT OF STOCK - {part['description']}",
                    "action": f"Order immediately - Lead time: {part['lead_time_days']} days"
                })
            elif part["status"] == "low":
                alerts.append({
                    "code": part["code"],
                    "description": part["description"],
                    "severity": "warning",
                    "message": f"LOW STOCK ({part['current_stock']} units) - {part['description']}",
                    "action": f"Review and order - Lead time: {part['lead_time_days']} days"
                })

        return {
            "success": True,
            "alert_count": len(alerts),
            "critical_count": sum(1 for a in alerts if a["severity"] == "critical"),
            "warning_count": sum(1 for a in alerts if a["severity"] == "warning"),
            "alerts": alerts
        }

    except Exception as e:
        logger.error(f"Error getting inventory alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get inventory alerts: {str(e)}"
        )


@router.get("/catalog")
async def get_parts_catalog(
    category: Optional[str] = Query(default=None, description="Filter by category"),
    current_user: User = Depends(get_current_user)
):
    """
    Get spare parts catalog.

    Returns all available parts with specifications.
    """
    service = get_spare_parts_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Spare parts service not available"
        )

    catalog = []
    for code, info in service.PARTS_CATALOG.items():
        if category and info["category"] != category.lower():
            continue

        catalog.append({
            "code": code,
            "description": info["description"],
            "category": info["category"],
            "unit_cost": info["cost"],
            "lead_time_days": info["lead_time"]
        })

    # Group by category
    by_category = {}
    for part in catalog:
        cat = part["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(part)

    return {
        "success": True,
        "total_parts": len(catalog),
        "categories": list(by_category.keys()),
        "catalog": catalog,
        "by_category": by_category
    }


@router.get("/history/{equipment_id}")
async def get_parts_history(
    equipment_id: str,
    months: int = Query(default=12, ge=1, le=24, description="History period in months"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get parts usage history for equipment.

    Returns historical parts consumption to identify patterns.
    """
    # In production, this would query work order history
    # For now, return sample data

    return {
        "success": True,
        "equipment_id": equipment_id,
        "period_months": months,
        "parts_used": [
            {"code": "BRG001", "description": "Bearing 6205-2RS", "count": 3, "total_cost": 135.00},
            {"code": "SEAL001", "description": "Oil Seal 35x52x7", "count": 5, "total_cost": 60.00},
            {"code": "BELT001", "description": "V-Belt A68", "count": 2, "total_cost": 56.00}
        ],
        "total_parts_cost": 251.00,
        "most_replaced": "SEAL001",
        "recommendation": "Consider preventive seal replacement to reduce failures"
    }
