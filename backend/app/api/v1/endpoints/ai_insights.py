"""
AI Insights API Endpoints

Endpoints for AI-powered process insights:
- Anomaly detection
- Automated insight generation
- Predictive analytics
- Model management
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import logging

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.tag import Tag
from app.services.ai_insights import get_ai_insights_service
from app.schemas.ai_insights import (
    AnomalyDetectionRequest,
    AnomalyDetectionResult,
    InsightGenerationRequest,
    InsightFeed,
    TagAnalysisResult,
    BaselineUpdateRequest,
    BaselineUpdateResponse,
    AIDashboardSummary,
    AIHealthScore,
    ModelListResponse,
    ModelInfo,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Insight Generation Endpoints
# ============================================================================

@router.post("/insights/generate", response_model=InsightFeed)
async def generate_insights(
    request: InsightGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate AI insights for specified tags

    Analyzes tag data and generates human-readable insights about:
    - Trends
    - Outliers
    - Level shifts
    - Baseline deviations
    """
    try:
        ai_service = get_ai_insights_service()

        # Get tags from database
        tags = db.query(Tag).filter(Tag.id.in_(request.tag_ids)).all()

        if not tags:
            raise HTTPException(status_code=404, detail="No tags found")

        tag_analyses = []

        # Analyze each tag
        for tag in tags:
            # Generate mock data for demonstration
            # TODO: Replace with actual InfluxDB query
            data = _generate_mock_tag_data(
                tag_id=str(tag.id),
                start=request.start,
                end=request.end,
                base_value=float(tag.last_value) if tag.last_value else 50.0
            )

            # Analyze
            analysis = ai_service.analyze_tag_data(
                tag_id=str(tag.id),
                tag_name=tag.name,
                data=data,
                generate_insights=True
            )

            tag_analyses.append(analysis)

        # Get top insights
        top_insights = ai_service.get_top_insights(
            tag_analyses,
            limit=request.limit,
            severity_filter=request.severity_filter
        )

        return InsightFeed(
            total_insights=len(top_insights),
            insights=top_insights,
            tags_analyzed=len(tags)
        )

    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/tag/{tag_id}", response_model=TagAnalysisResult)
async def get_tag_insights(
    tag_id: str,
    start: Optional[datetime] = Query(None, description="Start time (default: last 24h)"),
    end: Optional[datetime] = Query(None, description="End time (default: now)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed insights for a specific tag

    Returns comprehensive analysis including:
    - Statistics
    - Trends
    - Anomalies
    - Insights
    """
    try:
        # Get tag
        tag = db.query(Tag).filter(Tag.id == tag_id).first()

        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")

        # Default time range
        if not end:
            end = datetime.utcnow()
        if not start:
            start = end - timedelta(hours=24)

        # Get data
        data = _generate_mock_tag_data(
            tag_id=tag_id,
            start=start,
            end=end,
            base_value=float(tag.last_value) if tag.last_value else 50.0
        )

        # Analyze
        ai_service = get_ai_insights_service()
        analysis = ai_service.analyze_tag_data(
            tag_id=tag_id,
            tag_name=tag.name,
            data=data,
            generate_insights=True
        )

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tag insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Anomaly Detection Endpoints
# ============================================================================

@router.post("/anomalies/detect", response_model=AnomalyDetectionResult)
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Detect anomalies in tag data using Isolation Forest

    Performs multivariate anomaly detection across specified tags
    """
    try:
        ai_service = get_ai_insights_service()

        # Get tags
        tags = db.query(Tag).filter(Tag.id.in_(request.tag_ids)).all()

        if not tags:
            raise HTTPException(status_code=404, detail="No tags found")

        # Prepare data for multivariate analysis
        all_data = []

        for tag in tags:
            data = _generate_mock_tag_data(
                tag_id=str(tag.id),
                start=request.start,
                end=request.end,
                base_value=float(tag.last_value) if tag.last_value else 50.0
            )

            data[f'tag_{tag.id}'] = data['value']
            all_data.append(data)

        # Merge dataframes
        if len(all_data) > 0:
            merged_df = all_data[0]
            for df in all_data[1:]:
                merged_df = merged_df.merge(df, on='timestamp', how='outer', suffixes=('', '_drop'))

            # Get feature columns
            features = [col for col in merged_df.columns if col.startswith('tag_')]

            # Detect anomalies
            result = ai_service.detect_anomalies_multivariate(
                data=merged_df,
                features=features
            )

            return result
        else:
            return AnomalyDetectionResult(
                total_points=0,
                anomaly_count=0,
                anomaly_percentage=0.0,
                anomalies=[]
            )

    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Baseline Management Endpoints
# ============================================================================

@router.post("/baseline/update", response_model=BaselineUpdateResponse)
async def update_baseline(
    request: BaselineUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update baseline statistics for a tag

    Baseline is used to compare current values and detect deviations
    """
    try:
        # Get tag
        tag = db.query(Tag).filter(Tag.id == request.tag_id).first()

        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")

        # Get baseline data
        data = _generate_mock_tag_data(
            tag_id=request.tag_id,
            start=request.start,
            end=request.end,
            base_value=float(tag.last_value) if tag.last_value else 50.0
        )

        # Set baseline
        ai_service = get_ai_insights_service()
        ai_service.set_baseline(request.tag_id, data)

        # Get updated baseline
        baseline = ai_service.baseline_stats.get(request.tag_id)

        if baseline:
            return BaselineUpdateResponse(
                success=True,
                message=f"Baseline updated for tag {tag.name}",
                baseline={
                    "tag_id": request.tag_id,
                    **baseline
                }
            )
        else:
            return BaselineUpdateResponse(
                success=False,
                message="Failed to set baseline"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating baseline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Dashboard Endpoints
# ============================================================================

@router.get("/dashboard/summary", response_model=AIDashboardSummary)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI dashboard summary

    Provides overview of AI system health and recent insights
    """
    try:
        # Get all active tags
        tags = db.query(Tag).filter(Tag.is_active == True).limit(20).all()

        ai_service = get_ai_insights_service()
        tag_analyses = []

        # Quick analysis of recent data
        end = datetime.utcnow()
        start = end - timedelta(hours=1)

        for tag in tags[:10]:  # Limit to 10 for summary
            data = _generate_mock_tag_data(
                tag_id=str(tag.id),
                start=start,
                end=end,
                base_value=float(tag.last_value) if tag.last_value else 50.0
            )

            analysis = ai_service.analyze_tag_data(
                tag_id=str(tag.id),
                tag_name=tag.name,
                data=data,
                generate_insights=True
            )

            tag_analyses.append(analysis)

        # Get insights
        recent_insights = ai_service.get_top_insights(tag_analyses, limit=10)

        # Count by severity
        critical_count = len([i for i in recent_insights if i.get("severity") == "critical"])
        warning_count = len([i for i in recent_insights if i.get("severity") == "warning"])

        # Calculate health score (simple heuristic)
        base_score = 100.0
        score_penalty = (critical_count * 10) + (warning_count * 5)
        health_score_value = max(0, min(100, base_score - score_penalty))

        # Determine status
        if health_score_value >= 80:
            status = "healthy"
        elif health_score_value >= 50:
            status = "degraded"
        else:
            status = "critical"

        health_score = AIHealthScore(
            score=health_score_value,
            status=status,
            anomaly_count=0,  # TODO: Count from anomaly detection
            critical_insights=critical_count,
            warning_insights=warning_count
        )

        return AIDashboardSummary(
            health_score=health_score,
            recent_insights=recent_insights,
            anomalies_detected=0,
            tags_monitored=len(tags),
            models_active=0,  # TODO: Count active ML models
            last_analysis=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Model Management Endpoints (Placeholder for Phase 2)
# ============================================================================

@router.get("/models", response_model=ModelListResponse)
async def list_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all ML models

    Returns information about deployed ML models
    """
    # Placeholder - will be implemented in Phase 2
    return ModelListResponse(
        models=[],
        total=0
    )


# ============================================================================
# Helper Functions
# ============================================================================

def _generate_mock_tag_data(
    tag_id: str,
    start: datetime,
    end: datetime,
    base_value: float = 50.0,
    noise_level: float = 5.0,
    trend: float = 0.0,
    anomaly_probability: float = 0.05
) -> pd.DataFrame:
    """
    Generate mock time series data for testing

    TODO: Replace with actual InfluxDB query in production

    Args:
        tag_id: Tag ID
        start: Start datetime
        end: End datetime
        base_value: Base value for data
        noise_level: Standard deviation of noise
        trend: Trend coefficient
        anomaly_probability: Probability of injecting anomaly

    Returns:
        DataFrame with columns: timestamp, value
    """
    import numpy as np

    # Generate timestamps (1 minute intervals)
    timestamps = pd.date_range(start=start, end=end, freq='1min')

    # Generate values
    n_points = len(timestamps)
    values = []

    for i in range(n_points):
        # Base value with trend
        value = base_value + (trend * i)

        # Add noise
        value += np.random.normal(0, noise_level)

        # Occasionally inject anomaly
        if np.random.random() < anomaly_probability:
            value += np.random.choice([-1, 1]) * noise_level * 5

        values.append(value)

    return pd.DataFrame({
        'timestamp': timestamps,
        'value': values
    })
