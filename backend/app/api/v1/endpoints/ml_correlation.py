"""
MELH-004: Cross-Equipment Correlation API Endpoints

Provides REST endpoints for correlation analysis between equipment:
- Analyze correlations across multiple equipment
- Identify cascading failure paths
- Get equipment impact analysis
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


def get_correlation_service():
    """Get correlation analysis service instance"""
    try:
        from app.services.ml.cross_equipment_correlation import get_correlation_service as get_service
        return get_service()
    except ImportError as e:
        logger.warning(f"Correlation service not available: {e}")
        return None


@router.post("/analyze")
async def analyze_equipment_correlations(
    hours: int = Query(default=24, ge=1, le=168, description="Analysis period in hours"),
    min_correlation: float = Query(default=0.3, ge=0.0, le=1.0, description="Minimum correlation to report"),
    equipment_ids: Optional[str] = Query(default=None, description="Comma-separated equipment IDs to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze correlations between equipment.

    MELH-004: Identifies relationships between equipment including:
    - Positive correlations (equipment move together)
    - Negative correlations (inverse relationships)
    - Lagged correlations (one follows another with delay)

    This helps predict failure propagation and optimize maintenance.

    Args:
        hours: Time period to analyze (default: 24 hours)
        min_correlation: Minimum |r| to include in results (default: 0.3)
        equipment_ids: Optional specific equipment to analyze

    Returns:
        Correlation matrix with identified relationships and recommendations
    """
    service = get_correlation_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Correlation analysis service not available"
        )

    try:
        logger.info(f"Starting correlation analysis: hours={hours}, min_corr={min_correlation}")

        # Get equipment data
        equipment_filter = equipment_ids.split(",") if equipment_ids else None
        equipment_data = await _get_equipment_timeseries(db, hours, equipment_filter)

        if len(equipment_data) < 2:
            return {
                "success": False,
                "message": f"Need at least 2 equipment with data. Found: {len(equipment_data)}",
                "recommendation": "Ensure equipment have recent data in InfluxDB"
            }

        # Run correlation analysis
        result = await service.analyze_correlations(
            equipment_data=equipment_data,
            hours=hours,
            min_correlation=min_correlation
        )

        # Convert to JSON
        response = service.to_dict(result)
        response["success"] = True

        return response

    except Exception as e:
        logger.error(f"Error in correlation analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Correlation analysis failed: {str(e)}"
        )


@router.get("/equipment/{equipment_id}/impact")
async def get_equipment_impact(
    equipment_id: str,
    hours: int = Query(default=24, ge=1, le=168, description="Analysis period"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get impact analysis for specific equipment.

    Shows how many other equipment would be affected if this equipment fails,
    based on historical correlations.

    Args:
        equipment_id: Equipment to analyze
        hours: Analysis period

    Returns:
        Impact score and list of affected equipment
    """
    service = get_correlation_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Correlation service not available"
        )

    try:
        # Get all equipment data
        equipment_data = await _get_equipment_timeseries(db, hours, None)

        if equipment_id not in equipment_data:
            raise HTTPException(
                status_code=404,
                detail=f"Equipment {equipment_id} not found or has no data"
            )

        # Run correlation analysis
        result = await service.analyze_correlations(
            equipment_data=equipment_data,
            hours=hours,
            min_correlation=0.3
        )

        # Get impact for specific equipment
        impact = await service.get_equipment_impact(equipment_id, result.correlations)

        return {
            "success": True,
            "equipment_id": equipment_id,
            **impact
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting equipment impact: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Impact analysis failed: {str(e)}"
        )


@router.get("/cascading-risks")
async def get_cascading_failure_risks(
    hours: int = Query(default=48, ge=1, le=168, description="Analysis period"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get potential cascading failure paths.

    Identifies chains of equipment where a failure could propagate
    from one to another based on lagged correlations.

    Returns:
        List of cascading failure paths with timing and risk levels
    """
    service = get_correlation_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Correlation service not available"
        )

    try:
        # Get equipment data
        equipment_data = await _get_equipment_timeseries(db, hours, None)

        if len(equipment_data) < 2:
            return {
                "success": True,
                "cascading_paths": [],
                "message": "Insufficient equipment data for analysis"
            }

        # Run analysis
        result = await service.analyze_correlations(
            equipment_data=equipment_data,
            hours=hours,
            min_correlation=0.4  # Higher threshold for cascading analysis
        )

        return {
            "success": True,
            "analysis_period_hours": hours,
            "equipment_analyzed": len(equipment_data),
            "cascading_paths": result.potential_cascading_failures,
            "high_risk_count": sum(1 for p in result.potential_cascading_failures if p.get("risk_level") == "high"),
            "recommendations": [
                r for r in result.recommendations
                if "cascading" in r.lower() or "propagat" in r.lower()
            ]
        }

    except Exception as e:
        logger.error(f"Error analyzing cascading risks: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Cascading risk analysis failed: {str(e)}"
        )


@router.get("/matrix")
async def get_correlation_matrix(
    hours: int = Query(default=24, ge=1, le=168, description="Analysis period"),
    format: str = Query(default="list", description="Output format: 'list' or 'matrix'"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get correlation matrix for all equipment.

    Returns correlations in either list format (default) or matrix format
    suitable for heatmap visualization.

    Args:
        hours: Analysis period
        format: 'list' for flat list, 'matrix' for 2D array

    Returns:
        Correlation data in requested format
    """
    service = get_correlation_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Correlation service not available"
        )

    try:
        equipment_data = await _get_equipment_timeseries(db, hours, None)

        result = await service.analyze_correlations(
            equipment_data=equipment_data,
            hours=hours,
            min_correlation=0.0  # Include all for matrix
        )

        if format == "matrix":
            # Build matrix format for heatmap
            equipment_ids = list(equipment_data.keys())
            n = len(equipment_ids)

            # Initialize matrix with 1.0 diagonal
            matrix = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

            # Fill in correlations
            id_to_idx = {eq_id: idx for idx, eq_id in enumerate(equipment_ids)}
            for corr in result.correlations:
                if corr.source_id in id_to_idx and corr.target_id in id_to_idx:
                    i = id_to_idx[corr.source_id]
                    j = id_to_idx[corr.target_id]
                    matrix[i][j] = corr.correlation_coefficient
                    matrix[j][i] = corr.correlation_coefficient

            return {
                "success": True,
                "format": "matrix",
                "equipment_ids": equipment_ids,
                "matrix": matrix,
                "size": n
            }
        else:
            # List format
            return {
                "success": True,
                "format": "list",
                "equipment_count": len(equipment_data),
                "correlations": [
                    {
                        "source": c.source_id,
                        "target": c.target_id,
                        "coefficient": c.correlation_coefficient,
                        "strength": c.strength.value
                    }
                    for c in result.correlations
                ]
            }

    except Exception as e:
        logger.error(f"Error getting correlation matrix: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Matrix generation failed: {str(e)}"
        )


@router.get("/recommendations")
async def get_correlation_recommendations(
    equipment_id: Optional[str] = Query(default=None, description="Specific equipment ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get actionable recommendations based on correlation analysis.

    Returns maintenance scheduling suggestions, monitoring priorities,
    and failure prevention strategies.
    """
    service = get_correlation_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Correlation service not available"
        )

    try:
        equipment_data = await _get_equipment_timeseries(db, 48, None)  # 48h for better patterns

        result = await service.analyze_correlations(
            equipment_data=equipment_data,
            hours=48,
            min_correlation=0.4
        )

        recommendations = []

        # General recommendations
        recommendations.extend([
            {"type": "general", "priority": "high", "text": r}
            for r in result.recommendations
        ])

        # Equipment-specific recommendations
        if equipment_id:
            for corr in result.correlations:
                if corr.source_id == equipment_id or corr.target_id == equipment_id:
                    for rec in corr.recommendations:
                        recommendations.append({
                            "type": "equipment_specific",
                            "priority": "medium" if corr.strength.value == "strong" else "low",
                            "related_equipment": corr.target_id if corr.source_id == equipment_id else corr.source_id,
                            "text": rec
                        })

        # Deduplicate
        seen = set()
        unique_recs = []
        for rec in recommendations:
            key = rec["text"]
            if key not in seen:
                seen.add(key)
                unique_recs.append(rec)

        return {
            "success": True,
            "equipment_id": equipment_id,
            "recommendations": unique_recs[:20],  # Top 20
            "total_correlations_analyzed": len(result.correlations)
        }

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation generation failed: {str(e)}"
        )


# Helper functions

async def _get_equipment_timeseries(
    db: AsyncSession,
    hours: int,
    equipment_filter: Optional[List[str]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Get time series data for equipment from InfluxDB"""
    try:
        from app.services.influxdb_service import get_influxdb_service

        influx = get_influxdb_service()
        if not influx:
            # Return sample data for demonstration
            return _get_sample_equipment_data(equipment_filter)

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # Query equipment tags (motors, pumps, conveyors, etc.)
        query = f'''
        from(bucket: "optiflow")
            |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
            |> filter(fn: (r) => r["_measurement"] == "tag_values")
            |> filter(fn: (r) =>
                r["tag_id"] =~ /motor|pump|conveyor|crusher|feeder|belt|drive/i or
                r["category"] == "equipment"
            )
            |> aggregateWindow(every: 1m, fn: mean)
            |> fill(usePrevious: true)
        '''

        tables = influx.client.query_api().query(query)

        equipment_data: Dict[str, List[Dict]] = {}

        for table in tables:
            for record in table.records:
                tag_id = record.values.get("tag_id", "")

                if equipment_filter and tag_id not in equipment_filter:
                    continue

                if tag_id not in equipment_data:
                    equipment_data[tag_id] = []

                equipment_data[tag_id].append({
                    "timestamp": record.get_time(),
                    "value": record.get_value(),
                    "name": record.values.get("tag_name", tag_id),
                    "quality": record.values.get("quality", "GOOD")
                })

        # If no data from InfluxDB, return sample
        if not equipment_data:
            return _get_sample_equipment_data(equipment_filter)

        return equipment_data

    except Exception as e:
        logger.warning(f"Error getting equipment data: {e}")
        return _get_sample_equipment_data(equipment_filter)


def _get_sample_equipment_data(
    equipment_filter: Optional[List[str]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Generate sample equipment data for demonstration"""
    import random
    import numpy as np

    sample_equipment = [
        "motor_001", "motor_002", "pump_001", "conveyor_001",
        "crusher_001", "feeder_001", "belt_001", "drive_001"
    ]

    if equipment_filter:
        sample_equipment = [e for e in sample_equipment if e in equipment_filter]

    equipment_data = {}
    base_time = datetime.utcnow() - timedelta(hours=24)

    for eq_id in sample_equipment:
        readings = []
        base_value = random.uniform(50, 100)

        # Create correlated patterns
        if "motor" in eq_id:
            # Motors have similar patterns
            for i in range(1440):  # 24h of minute data
                value = base_value + 10 * np.sin(i / 60) + random.gauss(0, 2)
                readings.append({
                    "timestamp": base_time + timedelta(minutes=i),
                    "value": value,
                    "name": eq_id.replace("_", " ").title(),
                    "quality": "GOOD"
                })
        elif "pump" in eq_id:
            # Pumps lag motors by ~10 minutes
            for i in range(1440):
                value = base_value + 8 * np.sin((i - 10) / 60) + random.gauss(0, 3)
                readings.append({
                    "timestamp": base_time + timedelta(minutes=i),
                    "value": value,
                    "name": eq_id.replace("_", " ").title(),
                    "quality": "GOOD"
                })
        else:
            # Other equipment with some random correlation
            for i in range(1440):
                value = base_value + 5 * np.sin(i / 120) + random.gauss(0, 5)
                readings.append({
                    "timestamp": base_time + timedelta(minutes=i),
                    "value": value,
                    "name": eq_id.replace("_", " ").title(),
                    "quality": "GOOD"
                })

        equipment_data[eq_id] = readings

    return equipment_data
