"""
Data Quality Analytics Endpoints
Monitor and analyze data quality metrics
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.tag import Tag
from app.services.influxdb import InfluxDBService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize InfluxDB service
influxdb = InfluxDBService()


@router.get("/quality/summary")
async def get_data_quality_summary(
    site_id: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168, description="Time window in hours (1-168)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get data quality summary for all tags

    Returns percentage of good/bad/uncertain data points per tag
    """
    try:
        # Get tags from database
        query = select(Tag).where(Tag.is_active == True)
        if site_id:
            query = query.join(Tag.device).where(Device.site_id == site_id)

        result = await db.execute(query)
        tags = result.scalars().all()

        summary = []
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        for tag in tags:
            # Query quality metrics from InfluxDB
            quality_stats = await influxdb.get_quality_statistics(
                tag_id=str(tag.id),
                start_time=start_time,
                end_time=end_time
            )

            if quality_stats["total_points"] > 0:
                summary.append({
                    "tag_id": str(tag.id),
                    "tag_name": tag.name,
                    "device_name": tag.device.name if tag.device else None,
                    "total_points": quality_stats["total_points"],
                    "good_percentage": quality_stats["good_percentage"],
                    "bad_percentage": quality_stats["bad_percentage"],
                    "uncertain_percentage": quality_stats["uncertain_percentage"],
                    "last_quality": tag.last_quality,
                    "quality_status": _get_quality_status(quality_stats["good_percentage"])
                })

        # Sort by bad_percentage descending (worst quality first)
        summary.sort(key=lambda x: x["bad_percentage"], reverse=True)

        return {
            "time_window_hours": hours,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_tags": len(summary),
            "tags_with_issues": len([t for t in summary if t["quality_status"] != "excellent"]),
            "data": summary
        }

    except Exception as e:
        logger.error(f"Error getting data quality summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/tag/{tag_id}")
async def get_tag_quality_details(
    tag_id: str,
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed quality metrics for a specific tag
    """
    try:
        # Verify tag exists
        result = await db.execute(select(Tag).where(Tag.id == tag_id))
        tag = result.scalar_one_or_none()

        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # Get quality statistics
        stats = await influxdb.get_quality_statistics(
            tag_id=tag_id,
            start_time=start_time,
            end_time=end_time
        )

        # Get quality timeline (hourly breakdown)
        timeline = await influxdb.get_quality_timeline(
            tag_id=tag_id,
            start_time=start_time,
            end_time=end_time,
            interval="1h"
        )

        return {
            "tag_id": tag_id,
            "tag_name": tag.name,
            "time_window_hours": hours,
            "statistics": stats,
            "timeline": timeline,
            "current_quality": tag.last_quality,
            "recommendations": _generate_quality_recommendations(stats)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tag quality details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/alerts")
async def get_quality_alerts(
    threshold: float = Query(5.0, ge=0.1, le=50.0, description="Bad data threshold (%)"),
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get tags with quality issues exceeding threshold
    """
    try:
        result = await db.execute(select(Tag).where(Tag.is_active == True))
        tags = result.scalars().all()

        alerts = []
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        for tag in tags:
            stats = await influxdb.get_quality_statistics(
                tag_id=str(tag.id),
                start_time=start_time,
                end_time=end_time
            )

            if stats["bad_percentage"] > threshold:
                alerts.append({
                    "severity": _get_alert_severity(stats["bad_percentage"]),
                    "tag_id": str(tag.id),
                    "tag_name": tag.name,
                    "device_name": tag.device.name if tag.device else None,
                    "bad_percentage": stats["bad_percentage"],
                    "total_points": stats["total_points"],
                    "message": f"Tag has {stats['bad_percentage']:.1f}% bad data quality (threshold: {threshold}%)",
                    "recommended_action": _get_recommended_action(stats["bad_percentage"])
                })

        # Sort by severity and bad_percentage
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        alerts.sort(key=lambda x: (severity_order[x["severity"]], -x["bad_percentage"]))

        return {
            "threshold": threshold,
            "time_window_hours": hours,
            "total_alerts": len(alerts),
            "critical_count": len([a for a in alerts if a["severity"] == "critical"]),
            "high_count": len([a for a in alerts if a["severity"] == "high"]),
            "alerts": alerts
        }

    except Exception as e:
        logger.error(f"Error getting quality alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions

def _get_quality_status(good_percentage: float) -> str:
    """Determine quality status based on good data percentage"""
    if good_percentage >= 99:
        return "excellent"
    elif good_percentage >= 95:
        return "good"
    elif good_percentage >= 90:
        return "fair"
    elif good_percentage >= 80:
        return "poor"
    else:
        return "critical"


def _get_alert_severity(bad_percentage: float) -> str:
    """Determine alert severity based on bad data percentage"""
    if bad_percentage >= 20:
        return "critical"
    elif bad_percentage >= 10:
        return "high"
    elif bad_percentage >= 5:
        return "medium"
    else:
        return "low"


def _get_recommended_action(bad_percentage: float) -> str:
    """Get recommended action based on bad data percentage"""
    if bad_percentage >= 20:
        return "URGENT: Check PLC connection and sensor calibration immediately"
    elif bad_percentage >= 10:
        return "Investigate sensor health and wiring. Consider recalibration."
    elif bad_percentage >= 5:
        return "Monitor trend. May need preventive maintenance soon."
    else:
        return "Continue monitoring. Within acceptable range."


def _generate_quality_recommendations(stats: dict) -> List[str]:
    """Generate quality improvement recommendations"""
    recommendations = []

    if stats["bad_percentage"] > 10:
        recommendations.append("Check PLC connection stability")
        recommendations.append("Verify sensor calibration and wiring")
        recommendations.append("Review tag configuration (scan rate, deadband)")

    if stats["uncertain_percentage"] > 5:
        recommendations.append("Check for intermittent connection issues")
        recommendations.append("Review OPC-UA server health")

    if stats["good_percentage"] < 90:
        recommendations.append("Exclude this tag from ML training until quality improves")
        recommendations.append("Consider increasing scan rate if deadband is too aggressive")

    if not recommendations:
        recommendations.append("Data quality is excellent. No action needed.")

    return recommendations
