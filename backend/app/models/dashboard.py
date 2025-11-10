"""
Dashboard models for customizable module-specific dashboards
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class DashboardModule(str, enum.Enum):
    """Dashboard module types following ISA-95 structure"""
    OPERATIONS = "operations"
    MAINTENANCE = "maintenance"
    ENGINEERING = "engineering"
    EXECUTIVE = "executive"


class WidgetType(str, enum.Enum):
    """Widget types available for dashboards"""
    # Common widgets
    KPI_CARD = "kpi_card"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    TABLE = "table"
    GAUGE = "gauge"
    MAP = "map"
    HEATMAP = "heatmap"

    # Operations widgets
    PROCESS_STATUS = "process_status"
    ACTIVE_ALARMS = "active_alarms"
    PROCESS_VARIABLES = "process_variables"
    RECENT_COMMANDS = "recent_commands"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    EQUIPMENT_STATUS = "equipment_status"
    EVENT_LOG = "event_log"

    # Maintenance widgets
    OPEN_WORK_ORDERS = "open_work_orders"
    MTBF_MTTR = "mtbf_mttr"
    UPCOMING_MAINTENANCE = "upcoming_maintenance"
    FAILURE_HISTORY = "failure_history"
    PREDICTIVE_INDICATORS = "predictive_indicators"
    PARTS_INVENTORY = "parts_inventory"
    MAINTENANCE_RESPONSE_TIME = "maintenance_response_time"

    # Engineering widgets
    OPTIMIZATION_RECOMMENDATIONS = "optimization_recommendations"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    ENERGY_CONSUMPTION = "energy_consumption"
    TREND_ANALYSIS = "trend_analysis"
    PROCESS_SIMULATIONS = "process_simulations"
    QUALITY_INDICATORS = "quality_indicators"
    CAPACITY_ANALYSIS = "capacity_analysis"

    # Executive widgets
    KPI_DASHBOARD = "kpi_dashboard"
    SYSTEM_HEALTH = "system_health"
    FINANCIAL_ANALYSIS = "financial_analysis"
    RISKS_OPPORTUNITIES = "risks_opportunities"
    MONTHLY_TRENDS = "monthly_trends"
    PERFORMANCE_COMPARISON = "performance_comparison"
    SUSTAINABILITY_INDICATORS = "sustainability_indicators"


class Dashboard(Base):
    """
    Dashboard model - Customizable dashboards per module
    """
    __tablename__ = "dashboards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Ownership
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Dashboard metadata
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    module = Column(SQLEnum(DashboardModule), nullable=False, index=True)

    # Sharing and permissions
    is_public = Column(Boolean, default=False, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False)

    # Layout configuration
    # Grid layout: {cols: 12, rowHeight: 80, breakpoints: {...}}
    layout_config = Column(JSONB, default=dict, nullable=False)

    # Dashboard-level filters
    # Example: {siteId: 1, dateRange: "last_7_days", assetType: "conveyor"}
    default_filters = Column(JSONB, default=dict, nullable=False)

    # Refresh settings
    refresh_interval = Column(Integer, default=30, nullable=False)  # seconds
    auto_refresh = Column(Boolean, default=True, nullable=False)

    # Display settings
    theme = Column(String(50), default="light", nullable=False)
    show_legend = Column(Boolean, default=True, nullable=False)
    show_grid = Column(Boolean, default=True, nullable=False)

    # Usage tracking
    view_count = Column(Integer, default=0, nullable=False)
    last_viewed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="dashboards")
    organization = relationship("Organization", back_populates="dashboards")
    widgets = relationship("Widget", back_populates="dashboard", cascade="all, delete-orphan", order_by="Widget.position")
    shared_with = relationship("DashboardShare", back_populates="dashboard", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Dashboard {self.name} ({self.module})>"


class Widget(Base):
    """
    Widget model - Individual components within a dashboard
    """
    __tablename__ = "widgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False, index=True)

    # Widget metadata
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(SQLEnum(WidgetType), nullable=False, index=True)

    # Grid position and size
    # Example: {x: 0, y: 0, w: 4, h: 2, minW: 2, minH: 1}
    position = Column(Integer, nullable=False, default=0)  # Order in dashboard
    grid_position = Column(JSONB, nullable=False)  # {x, y, w, h}

    # Widget configuration
    # Example: {dataSource: "simulator", metric: "energy", aggregation: "avg"}
    config = Column(JSONB, default=dict, nullable=False)

    # Data query configuration
    # Example: {endpoint: "/api/v1/simulator/status", params: {site_id: 1}}
    data_config = Column(JSONB, default=dict, nullable=False)

    # Display settings
    # Example: {showTitle: true, color: "primary", unit: "kWh"}
    display_config = Column(JSONB, default=dict, nullable=False)

    # Refresh settings (overrides dashboard default if set)
    refresh_interval = Column(Integer, nullable=True)  # seconds, null = use dashboard default

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    dashboard = relationship("Dashboard", back_populates="widgets")

    def __repr__(self):
        return f"<Widget {self.title} ({self.type})>"


class DashboardShare(Base):
    """
    Dashboard sharing model - Tracks which users have access to which dashboards
    """
    __tablename__ = "dashboard_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Permissions
    can_edit = Column(Boolean, default=False, nullable=False)
    can_delete = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    shared_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    dashboard = relationship("Dashboard", back_populates="shared_with")
    user = relationship("User", foreign_keys=[user_id], back_populates="shared_dashboards")
    shared_by_user = relationship("User", foreign_keys=[shared_by])

    def __repr__(self):
        return f"<DashboardShare dashboard={self.dashboard_id} user={self.user_id}>"


class DashboardTemplate(Base):
    """
    Dashboard template model - Pre-configured dashboard templates
    """
    __tablename__ = "dashboard_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Template metadata
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    module = Column(SQLEnum(DashboardModule), nullable=False, index=True)

    # Template configuration (full dashboard + widgets config)
    config = Column(JSONB, nullable=False)

    # Preview
    thumbnail_url = Column(String(500), nullable=True)

    # Visibility
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # System templates can't be deleted

    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<DashboardTemplate {self.name} ({self.module})>"
