"""
GraphQL Types (PDCA #27)

Type definitions for the GraphQL schema.
"""

from typing import Optional, List
from datetime import datetime
import strawberry


# ========================================
# User Types
# ========================================

@strawberry.enum
class UserRole(str):
    """User role enum."""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    SUPERUSER = "superuser"


@strawberry.type
class User:
    """User type."""
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


# ========================================
# Asset Types
# ========================================

@strawberry.enum
class AssetType(str):
    """Asset type enum."""
    CONVEYOR = "conveyor"
    CRANE = "crane"
    TRUCK = "truck"
    SHIP = "ship"
    LOADER = "loader"
    STACKER = "stacker"


@strawberry.enum
class AssetStatus(str):
    """Asset status enum."""
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


@strawberry.type
class Asset:
    """Asset type."""
    id: str
    name: str
    type: AssetType
    status: AssetStatus
    health: float
    location: Optional[str] = None
    last_maintenance: Optional[datetime] = None
    created_at: datetime


# ========================================
# Alarm Types
# ========================================

@strawberry.enum
class AlarmSeverity(str):
    """Alarm severity enum."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@strawberry.type
class Alarm:
    """Alarm type."""
    id: str
    message: str
    severity: AlarmSeverity
    asset_id: Optional[str] = None
    acknowledged: bool
    timestamp: datetime


# ========================================
# Dashboard Types
# ========================================

@strawberry.type
class MaintenanceMetrics:
    """Maintenance metrics."""
    average_health: float
    critical_assets: int
    critical_alarms: int
    high_alarms: int
    medium_alarms: int


@strawberry.type
class OperationsMetrics:
    """Operations metrics."""
    efficiency_score: float
    berth_utilization: float


@strawberry.type
class OverallHealthScore:
    """Overall health score."""
    score: float
    status: str
    color: str


@strawberry.type
class Dashboard360:
    """360° Dashboard data."""
    overall_health_score: OverallHealthScore
    maintenance: MaintenanceMetrics
    operations: OperationsMetrics


# ========================================
# ROI Types
# ========================================

@strawberry.type
class PredictiveMaintenanceROI:
    """Predictive maintenance ROI."""
    failures_prevented: int
    emergency_costs_avoided: float
    savings: float


@strawberry.type
class ROI:
    """ROI calculations."""
    total_savings: float
    annual_projection: float
    roi_percentage: float
    predictive_maintenance: PredictiveMaintenanceROI


# ========================================
# Site Types
# ========================================

@strawberry.type
class Site:
    """Site type."""
    id: str
    name: str
    location: str
    dashboard360: Dashboard360
    roi: ROI
    assets: List[Asset]
    alarms: List[Alarm]


# ========================================
# Gateway Types
# ========================================

@strawberry.type
class Gateway:
    """Gateway type."""
    id: str
    name: str
    status: str
    connected_tags: int
    protocol: str


# ========================================
# Data Quality Types
# ========================================

@strawberry.type
class DataQuality:
    """Data quality metrics."""
    overall_score: float
    last_check: datetime
    issues_count: int


# ========================================
# Input Types (for mutations)
# ========================================

@strawberry.input
class AssetFilter:
    """Filter for assets query."""
    type: Optional[AssetType] = None
    status: Optional[AssetStatus] = None
    min_health: Optional[float] = None
    limit: Optional[int] = 10


@strawberry.input
class AlarmFilter:
    """Filter for alarms query."""
    severity: Optional[AlarmSeverity] = None
    acknowledged: Optional[bool] = None
    limit: Optional[int] = 10


@strawberry.input
class UpdateAssetInput:
    """Input for updating an asset."""
    id: str
    status: Optional[AssetStatus] = None
    health: Optional[float] = None


@strawberry.input
class AcknowledgeAlarmInput:
    """Input for acknowledging an alarm."""
    id: str
    user_id: str
