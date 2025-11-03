"""
AI Insights Schemas

Pydantic models for AI insights API requests/responses
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID


# ============================================================================
# Request Schemas
# ============================================================================

class AnomalyDetectionRequest(BaseModel):
    """Request for anomaly detection"""
    tag_ids: List[str] = Field(..., description="List of tag IDs to analyze")
    start: datetime = Field(..., description="Start time")
    end: datetime = Field(..., description="End time")
    contamination: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="Expected proportion of outliers"
    )


class InsightGenerationRequest(BaseModel):
    """Request for insight generation"""
    tag_ids: List[str] = Field(..., description="List of tag IDs to analyze")
    start: datetime = Field(..., description="Start time")
    end: datetime = Field(..., description="End time")
    limit: int = Field(default=10, ge=1, le=100, description="Max insights to return")
    severity_filter: Optional[List[str]] = Field(
        default=None,
        description="Filter by severity: critical, warning, info"
    )


class BaselineUpdateRequest(BaseModel):
    """Request to update baseline for a tag"""
    tag_id: str = Field(..., description="Tag ID")
    start: datetime = Field(..., description="Baseline period start")
    end: datetime = Field(..., description="Baseline period end")


# ============================================================================
# Response Schemas
# ============================================================================

class StatisticsData(BaseModel):
    """Statistical data"""
    mean: float
    std: float
    min: float
    max: float
    median: float
    current: Optional[float] = None


class TrendData(BaseModel):
    """Trend analysis data"""
    trend: str = Field(..., description="Trend: increasing, decreasing, stable")
    slope: float
    normalized_slope: float
    change_rate: float = Field(..., description="Change rate as percentage")


class OutlierData(BaseModel):
    """Outlier detection data"""
    outlier_count: int
    outlier_percentage: float
    max_zscore: Optional[float] = None


class LevelShiftData(BaseModel):
    """Level shift detection data"""
    level_shift_detected: bool
    change_percent: Optional[float] = None
    previous_mean: Optional[float] = None
    recent_mean: Optional[float] = None


class BaselineComparisonData(BaseModel):
    """Baseline comparison data"""
    status: str = Field(..., description="Status: normal, warning, critical")
    deviation: float = Field(..., description="Standard deviations from baseline")
    percent_difference: float
    baseline_mean: float
    baseline_std: float
    current_value: float


class InsightItem(BaseModel):
    """Single insight item"""
    type: str = Field(..., description="Insight type")
    severity: str = Field(..., description="Severity: critical, warning, info")
    message: str = Field(..., description="Human-readable message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional data")
    tag_id: Optional[str] = None
    tag_name: Optional[str] = None


class TagAnalysisResult(BaseModel):
    """Analysis result for a single tag"""
    tag_id: str
    tag_name: str
    data_points: int
    timestamp: str = Field(..., description="Analysis timestamp")
    statistics: StatisticsData
    trend: TrendData
    outliers: OutlierData
    level_shift: LevelShiftData
    baseline_comparison: Optional[BaselineComparisonData] = None
    insights: List[InsightItem] = Field(default_factory=list)
    error: Optional[str] = None


class AnomalyPoint(BaseModel):
    """Single anomaly point"""
    index: int
    score: float = Field(..., description="Anomaly score (more negative = more anomalous)")
    features: Dict[str, float] = Field(default_factory=dict)
    timestamp: Optional[str] = None


class AnomalyDetectionResult(BaseModel):
    """Anomaly detection result"""
    total_points: int
    anomaly_count: int
    anomaly_percentage: float
    anomalies: List[AnomalyPoint] = Field(default_factory=list)
    error: Optional[str] = None


class InsightFeed(BaseModel):
    """Feed of insights"""
    total_insights: int
    insights: List[InsightItem]
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tags_analyzed: int


class BaselineInfo(BaseModel):
    """Baseline statistics info"""
    tag_id: str
    mean: float
    std: float
    min: float
    max: float
    sample_count: int
    updated_at: str


class BaselineUpdateResponse(BaseModel):
    """Response for baseline update"""
    success: bool
    message: str
    baseline: Optional[BaselineInfo] = None


# ============================================================================
# Dashboard Schemas
# ============================================================================

class AIHealthScore(BaseModel):
    """Overall AI health score for a system/device"""
    score: float = Field(..., ge=0, le=100, description="Health score 0-100")
    status: str = Field(..., description="Status: healthy, degraded, critical")
    anomaly_count: int = Field(default=0)
    critical_insights: int = Field(default=0)
    warning_insights: int = Field(default=0)
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AIDashboardSummary(BaseModel):
    """Summary for AI dashboard"""
    health_score: AIHealthScore
    recent_insights: List[InsightItem] = Field(default_factory=list)
    anomalies_detected: int = Field(default=0)
    tags_monitored: int = Field(default=0)
    models_active: int = Field(default=0)
    last_analysis: Optional[str] = None


# ============================================================================
# Predictive Maintenance Schemas (for Phase 2)
# ============================================================================

class PredictiveMaintenanceScore(BaseModel):
    """Predictive maintenance score for equipment"""
    device_id: str
    device_name: str
    health_score: float = Field(..., ge=0, le=100)
    rul_days: Optional[float] = Field(
        None,
        description="Remaining Useful Life in days"
    )
    failure_probability: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Probability of failure in next period"
    )
    maintenance_recommended: bool = Field(default=False)
    confidence: Optional[float] = Field(None, ge=0, le=1)
    contributing_factors: List[str] = Field(default_factory=list)
    predicted_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ProcessOptimizationSuggestion(BaseModel):
    """Process optimization suggestion"""
    suggestion_id: str
    title: str
    description: str
    potential_improvement: str = Field(
        ...,
        description="e.g., '15% energy reduction', '10% efficiency increase'"
    )
    confidence: float = Field(..., ge=0, le=1)
    parameters: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Suggested parameter changes"
    )
    impact_analysis: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ============================================================================
# Model Management Schemas
# ============================================================================

class ModelInfo(BaseModel):
    """ML Model information"""
    model_id: str
    name: str
    model_type: str
    status: str
    version: str
    accuracy: Optional[float] = None
    last_trained: Optional[str] = None
    is_active: bool = False


class ModelListResponse(BaseModel):
    """List of models"""
    models: List[ModelInfo]
    total: int


# ============================================================================
# Real-time Monitoring Schemas
# ============================================================================

class RealTimeInsight(BaseModel):
    """Real-time insight (for WebSocket)"""
    insight_id: str = Field(default_factory=lambda: str(UUID))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tag_id: str
    tag_name: str
    insight_type: str
    severity: str
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnomalyAlert(BaseModel):
    """Anomaly alert (for WebSocket)"""
    alert_id: str = Field(default_factory=lambda: str(UUID))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tag_id: str
    tag_name: str
    anomaly_score: float
    severity: str = Field(..., description="low, medium, high, critical")
    message: str
    features: Dict[str, float] = Field(default_factory=dict)
    recommended_action: Optional[str] = None
