"""
AI Insights API Endpoints

Endpoints for AI-powered process insights:
- Anomaly detection
- Automated insight generation
- Predictive analytics
- Model management
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import logging

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.tag import Tag
from app.services.ai_insights import get_ai_insights_service
from app.services.influxdb import influxdb_service
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
    db: AsyncSession = Depends(get_db),
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
            # Query real data from InfluxDB
            try:
                influx_data = influxdb_service.query_tag_data(
                    tag_id=str(tag.id),
                    start_time=request.start,
                    end_time=request.end
                )
                
                # Convert to DataFrame format expected by AI service
                if influx_data:
                    data = pd.DataFrame(influx_data)
                    data['timestamp'] = pd.to_datetime(data['timestamp'])
                    data = data.set_index('timestamp')
                else:
                    # Fallback to mock if no data available
                    logger.warning(f"No InfluxDB data for tag {tag.id}, using mock data")
                    data = _generate_mock_tag_data(
                        tag_id=str(tag.id),
                        start=request.start,
                        end=request.end,
                        base_value=float(tag.last_value) if tag.last_value else 50.0
                    )
            except Exception as e:
                logger.error(f"Error querying InfluxDB for tag {tag.id}: {e}")
                # Fallback to mock data on error
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
    db: AsyncSession = Depends(get_db),
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

        # Get real data from InfluxDB
        try:
            influx_data = influxdb_service.query_tag_data(
                tag_id=tag_id,
                start_time=start,
                end_time=end
            )
            
            if influx_data:
                data = pd.DataFrame(influx_data)
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data = data.set_index('timestamp')
            else:
                logger.warning(f"No InfluxDB data for tag {tag_id}, using mock data")
                data = _generate_mock_tag_data(
                    tag_id=tag_id,
                    start=start,
                    end=end,
                    base_value=float(tag.last_value) if tag.last_value else 50.0
                )
        except Exception as e:
            logger.error(f"Error querying InfluxDB for tag {tag_id}: {e}")
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
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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
            # Query real data from InfluxDB
            try:
                influx_data = influxdb_service.query_tag_data(
                    tag_id=str(tag.id),
                    start_time=start,
                    end_time=end
                )
                
                # Convert to DataFrame format
                if influx_data:
                    data = pd.DataFrame(influx_data)
                    data['timestamp'] = pd.to_datetime(data['timestamp'])
                    data = data.set_index('timestamp')
                else:
                    # Fallback to mock if no data available
                    logger.warning(f"No InfluxDB data for tag {tag.id}, using mock data")
                    data = _generate_mock_tag_data(
                        tag_id=str(tag.id),
                        start=start,
                        end=end,
                        base_value=float(tag.last_value) if tag.last_value else 50.0
                    )
            except Exception as e:
                logger.error(f"Error querying InfluxDB for tag {tag.id}: {e}")
                # Fallback to mock data on error
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


@router.get("/dashboard/summary/public", response_model=AIDashboardSummary)
async def get_dashboard_summary_public(db: AsyncSession = Depends(get_db)):
    """
    Get AI dashboard summary (public endpoint for testing)
    
    Same as /dashboard/summary but without authentication
    """
    try:
        # Get all active tags using async syntax
        stmt = select(Tag).where(Tag.is_active == True).limit(20)
        result = await db.execute(stmt)
        tags = list(result.scalars().all())

        ai_service = get_ai_insights_service()
        tag_analyses = []

        # Quick analysis of recent data
        end = datetime.utcnow()
        start = end - timedelta(hours=1)

        for tag in tags[:10]:  # Limit to 10 for summary
            # Query real data from InfluxDB
            try:
                influx_data = influxdb_service.query_tag_data(
                    tag_id=str(tag.id),
                    start_time=start,
                    end_time=end
                )
                
                # Convert to DataFrame format
                if influx_data:
                    data = pd.DataFrame(influx_data)
                    data['timestamp'] = pd.to_datetime(data['timestamp'])
                    data = data.set_index('timestamp')
                    logger.info(f"✅ Using REAL data from InfluxDB for tag {tag.name}: {len(influx_data)} points")
                else:
                    # Fallback to mock if no data available
                    logger.warning(f"⚠️ No InfluxDB data for tag {tag.id}, using mock data")
                    data = _generate_mock_tag_data(
                        tag_id=str(tag.id),
                        start=start,
                        end=end,
                        base_value=float(tag.last_value) if tag.last_value else 50.0
                    )
            except Exception as e:
                logger.error(f"❌ Error querying InfluxDB for tag {tag.id}: {e}")
                # Fallback to mock data on error
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
            anomaly_count=0,
            critical_insights=critical_count,
            warning_insights=warning_count
        )

        return AIDashboardSummary(
            health_score=health_score,
            recent_insights=recent_insights,
            anomalies_detected=0,
            tags_monitored=len(tags),
            models_active=0,
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
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    is_active: Optional[bool] = Query(None, description="Filter by deployment status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all ML models

    Returns information about deployed ML models (Phase 2)
    """
    from app.services.model_manager import get_model_manager
    from app.models.ml_model import ModelType, ModelStatus

    try:
        model_manager = get_model_manager()

        # Convert string to enum if provided
        type_filter = ModelType(model_type) if model_type else None
        status_filter = ModelStatus(status) if status else None

        models = model_manager.list_models(
            db=db,
            model_type=type_filter,
            status=status_filter,
            is_active=is_active
        )

        # Convert to response format
        model_list = [
            ModelInfo(
                id=str(model.id),
                name=model.name,
                model_type=model.model_type.value,
                status=model.status.value,
                algorithm=model.algorithm,
                version=model.version,
                is_active=model.is_active,
                metrics=model.metrics,
                created_at=model.created_at.isoformat(),
                deployed_at=model.deployed_at.isoformat() if model.deployed_at else None
            )
            for model in models
        ]

        return ModelListResponse(
            models=model_list,
            total=len(model_list)
        )

    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Forecasting Endpoints (Phase 2)
# ============================================================================

@router.post("/forecast/generate")
async def generate_forecast(
    tag_id: str = Query(..., description="Tag ID to forecast"),
    periods: int = Query(24, description="Number of periods to forecast"),
    freq: str = Query("H", description="Frequency (H=hourly, D=daily)"),
    start: Optional[datetime] = Query(None, description="Start time for historical data"),
    end: Optional[datetime] = Query(None, description="End time for historical data"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate forecast for a tag using Prophet (Phase 2)

    Returns forecast with confidence intervals
    """
    from app.services.forecasting import get_forecasting_service
    from app.services.influx_connector import get_influx_connector

    try:
        # Get tag
        tag = db.query(Tag).filter(Tag.id == tag_id).first()

        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")

        # Default time range (last 7 days)
        if not end:
            end = datetime.utcnow()
        if not start:
            start = end - timedelta(days=7)

        # Get data from InfluxDB
        influx = get_influx_connector()
        data = influx.query_tag_data(tag_id=tag_id, start=start, end=end)

        if data.empty:
            raise HTTPException(status_code=400, detail="Insufficient historical data for forecasting")

        # Generate forecast
        forecasting_service = get_forecasting_service()
        forecast = forecasting_service.generate_forecast(
            tag_id=tag_id,
            tag_name=tag.name,
            data=data,
            forecast_type="prophet",
            periods=periods,
            freq=freq
        )

        return forecast

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Predictive Maintenance Endpoints (Phase 2)
# ============================================================================

@router.post("/predictive-maintenance/analyze")
async def analyze_equipment_health(
    equipment_id: str = Query(..., description="Equipment ID"),
    include_rul: bool = Query(True, description="Include RUL estimation"),
    include_failure_prediction: bool = Query(True, description="Include failure prediction"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze equipment health with predictive maintenance (Phase 2)

    Returns:
    - Remaining Useful Life (RUL) estimation
    - Failure probability
    - Health score
    - Maintenance recommendations
    """
    from app.services.predictive_maintenance import get_predictive_maintenance_service
    from app.services.influx_connector import get_influx_connector

    try:
        # Get equipment sensor data
        # Note: This assumes equipment has associated sensor tags
        # You may need to adjust based on your data model

        end = datetime.utcnow()
        start = end - timedelta(hours=24)

        # Get sensor data for equipment
        influx = get_influx_connector()

        # Mock sensor data for now - replace with actual equipment sensor query
        sensor_data = pd.DataFrame({
            'timestamp': pd.date_range(start=start, end=end, freq='1min'),
            'temperature': np.random.normal(75, 10, (end - start).seconds // 60 + 1),
            'vibration': np.random.normal(0.5, 0.1, (end - start).seconds // 60 + 1),
            'pressure': np.random.normal(100, 5, (end - start).seconds // 60 + 1)
        })

        # Analyze
        pm_service = get_predictive_maintenance_service()
        analysis = pm_service.analyze_equipment(
            equipment_id=equipment_id,
            equipment_name=f"Equipment {equipment_id}",
            sensor_data=sensor_data,
            include_rul=include_rul,
            include_failure_prediction=include_failure_prediction
        )

        return analysis

    except Exception as e:
        logger.error(f"Error analyzing equipment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Root Cause Analysis Endpoints (Phase 2)
# ============================================================================

@router.post("/root-cause/analyze")
async def analyze_root_cause(
    anomaly_tag_id: str = Query(..., description="Tag ID with anomaly"),
    anomaly_timestamp: datetime = Query(..., description="When anomaly occurred"),
    related_tag_ids: List[str] = Query(..., description="Related tags to analyze"),
    time_window_minutes: int = Query(60, description="Analysis time window"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform root cause analysis for an anomaly (Phase 2)

    Returns:
    - Correlated tags
    - Causal chains
    - Likely root causes
    - Recommendations
    """
    from app.services.root_cause_analysis import get_root_cause_analysis_service
    from app.services.influx_connector import get_influx_connector

    try:
        # Get anomaly tag
        anomaly_tag = db.query(Tag).filter(Tag.id == anomaly_tag_id).first()

        if not anomaly_tag:
            raise HTTPException(status_code=404, detail="Anomaly tag not found")

        # Get time window
        start_time = anomaly_timestamp - timedelta(minutes=time_window_minutes)
        end_time = anomaly_timestamp + timedelta(minutes=time_window_minutes // 2)

        # Get data for all tags
        influx = get_influx_connector()
        all_tag_ids = [anomaly_tag_id] + related_tag_ids

        # Query multivariate data
        multivariate_data = influx.query_multivariate(
            tag_ids=all_tag_ids,
            start=start_time,
            end=end_time
        )

        if multivariate_data.empty:
            raise HTTPException(status_code=400, detail="Insufficient data for root cause analysis")

        # Get tag metadata
        related_tags = db.query(Tag).filter(Tag.id.in_(related_tag_ids)).all()
        tag_metadata = {str(tag.id): tag.name for tag in related_tags}
        tag_metadata[anomaly_tag_id] = anomaly_tag.name

        # Perform root cause analysis
        rca_service = get_root_cause_analysis_service()
        analysis = rca_service.analyze_anomaly(
            anomaly_tag_id=anomaly_tag_id,
            anomaly_tag_name=anomaly_tag.name,
            anomaly_timestamp=anomaly_timestamp,
            all_tags_data=multivariate_data,
            tag_metadata=tag_metadata,
            time_window_minutes=time_window_minutes
        )

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing root cause analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Advanced Anomaly Detection Endpoints (Phase 2)
# ============================================================================

@router.post("/anomalies/detect-lstm")
async def detect_anomalies_lstm(
    tag_ids: List[str] = Query(..., description="Tag IDs to analyze"),
    start: datetime = Query(..., description="Start time"),
    end: datetime = Query(..., description="End time"),
    train_first: bool = Query(True, description="Train model on this data first"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Detect anomalies using LSTM Autoencoder (Phase 2)

    Deep learning-based anomaly detection
    """
    from app.services.advanced_anomaly import get_advanced_anomaly_service
    from app.services.influx_connector import get_influx_connector

    try:
        # Get data
        influx = get_influx_connector()
        multivariate_data = influx.query_multivariate(
            tag_ids=tag_ids,
            start=start,
            end=end
        )

        if multivariate_data.empty:
            raise HTTPException(status_code=400, detail="No data available")

        # Get feature columns
        features = [col for col in multivariate_data.columns if col.startswith('tag_')]

        if not features:
            raise HTTPException(status_code=400, detail="No valid features found")

        # Detect anomalies
        advanced_anomaly = get_advanced_anomaly_service()
        result = advanced_anomaly.detect_lstm(
            data=multivariate_data,
            features=features,
            train_first=train_first
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting anomalies with LSTM: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
