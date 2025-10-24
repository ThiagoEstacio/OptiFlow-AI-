"""
Analytics and Reports schemas for SmartPort
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime, date
from uuid import UUID

from app.models.port.loading_operation import CommodityType

# Import schemas (avoid circular imports)
if TYPE_CHECKING:
    from app.schemas.port.loading_operation import CargoResponse, OperationEventResponse


# ===== KPI Schemas =====

class PortKPIResponse(BaseModel):
    """Port operational KPIs"""
    # Throughput
    total_throughput: float = Field(..., description="Total cargo handled (tons)")
    daily_average_throughput: float = Field(..., description="Daily average (tons/day)")
    monthly_throughput: float = Field(..., description="Monthly throughput (tons)")

    # Efficiency
    average_loading_rate: float = Field(..., description="Average loading rate (tons/hour)")
    average_efficiency: float = Field(..., description="Average operational efficiency (%)")
    average_berth_utilization: float = Field(..., description="Average berth utilization (%)")

    # Operations
    total_operations: int = Field(..., description="Total operations count")
    completed_operations: int = Field(..., description="Completed operations")
    active_operations: int = Field(..., description="Currently active operations")
    delayed_operations: int = Field(..., description="Delayed operations count")

    # Vessels
    total_vessels: int = Field(..., description="Total vessels")
    vessels_in_port: int = Field(..., description="Vessels currently in port")
    vessels_berthed: int = Field(..., description="Vessels at berth")
    vessels_waiting: int = Field(..., description="Vessels waiting")

    # Downtime
    total_downtime_hours: float = Field(..., description="Total downtime (hours)")
    average_downtime_per_operation: float = Field(..., description="Average downtime per operation (hours)")

    # Period
    period_start: datetime
    period_end: datetime


class PerformanceMetricsResponse(BaseModel):
    """General performance metrics"""
    # Operational performance
    operational_efficiency: float = Field(..., description="Overall efficiency (%)", ge=0, le=100)
    equipment_availability: float = Field(..., description="Equipment availability (%)", ge=0, le=100)
    berth_utilization: float = Field(..., description="Berth utilization (%)", ge=0, le=100)

    # Time metrics
    average_turnaround_time: float = Field(..., description="Average vessel turnaround time (hours)")
    average_waiting_time: float = Field(..., description="Average waiting time (hours)")
    average_berthing_time: float = Field(..., description="Average time at berth (hours)")

    # Throughput
    current_throughput_rate: Optional[float] = Field(None, description="Current throughput (tons/hour)")
    peak_throughput_rate: float = Field(..., description="Peak throughput achieved (tons/hour)")
    design_throughput_rate: Optional[float] = Field(None, description="Design throughput (tons/hour)")

    # Quality
    on_time_completion_rate: float = Field(..., description="On-time completion rate (%)", ge=0, le=100)
    safety_incidents: int = Field(..., description="Safety incidents count")

    # Period
    period_start: datetime
    period_end: datetime
    last_updated: datetime


class EquipmentPerformanceResponse(BaseModel):
    """Equipment-specific performance metrics"""
    equipment_id: UUID
    equipment_code: str
    equipment_name: str
    equipment_type: str

    # Status
    current_status: str
    health_score: Optional[float] = Field(None, ge=0, le=100, description="Health score (%)")
    failure_probability: Optional[float] = Field(None, ge=0, le=100, description="Failure probability (%)")

    # Performance
    utilization_rate: float = Field(..., description="Utilization rate (%)", ge=0, le=100)
    efficiency: float = Field(..., description="Efficiency (%)", ge=0, le=100)
    availability: float = Field(..., description="Availability (%)", ge=0, le=100)

    # Throughput
    total_throughput: float = Field(..., description="Total throughput (tons)")
    average_throughput_rate: float = Field(..., description="Average rate (tons/hour)")
    current_throughput_rate: Optional[float] = Field(None, description="Current rate (tons/hour)")

    # Time
    total_operating_hours: float = Field(..., description="Operating hours")
    total_downtime_hours: float = Field(..., description="Downtime hours")
    mtbf: Optional[float] = Field(None, description="Mean time between failures (hours)")
    mttr: Optional[float] = Field(None, description="Mean time to repair (hours)")

    # Maintenance
    last_maintenance_date: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None
    days_until_maintenance: Optional[int] = None

    # Period
    period_start: datetime
    period_end: datetime


class TrendDataPoint(BaseModel):
    """Single data point in a trend"""
    timestamp: datetime
    value: float
    label: Optional[str] = None


class TrendResponse(BaseModel):
    """Trend data response"""
    metric_name: str
    metric_unit: str
    data_points: List[TrendDataPoint]

    # Statistics
    min_value: float
    max_value: float
    average_value: float
    current_value: Optional[float] = None

    # Period
    period_start: datetime
    period_end: datetime


class MultipleTrendsResponse(BaseModel):
    """Multiple trends response"""
    trends: List[TrendResponse]
    period_start: datetime
    period_end: datetime


# ===== Commodity Analytics =====

class CommodityBreakdownResponse(BaseModel):
    """Breakdown by commodity"""
    commodity: CommodityType
    total_quantity: float = Field(..., description="Total quantity (tons)")
    total_operations: int = Field(..., description="Number of operations")
    average_rate: float = Field(..., description="Average loading rate (tons/hour)")
    percentage_of_total: float = Field(..., description="Percentage of total throughput", ge=0, le=100)


class CommodityAnalyticsResponse(BaseModel):
    """Commodity analytics"""
    total_commodities: int
    breakdown: List[CommodityBreakdownResponse]
    period_start: datetime
    period_end: datetime


# ===== Reports Schemas =====

class DailyReportResponse(BaseModel):
    """Daily operations report"""
    report_date: date
    site_id: UUID
    site_name: str

    # Summary
    total_throughput: float = Field(..., description="Total throughput (tons)")
    total_operations: int
    active_operations: int
    completed_operations: int

    # Vessels
    vessels_arrived: int
    vessels_departed: int
    vessels_in_port: int

    # Performance
    average_loading_rate: float
    average_efficiency: float
    total_downtime_hours: float

    # Commodity breakdown
    commodities: List[CommodityBreakdownResponse] = Field(default_factory=list)

    # Issues
    delays: int = Field(..., description="Number of delays")
    equipment_failures: int = Field(..., description="Equipment failures")
    weather_delays: int = Field(..., description="Weather-related delays")

    # Operations list
    operations: List[Dict[str, Any]] = Field(default_factory=list, description="List of operations")

    generated_at: datetime


class OperationReportResponse(BaseModel):
    """Single operation detailed report"""
    operation_id: UUID
    operation_number: str
    operation_type: str

    # Vessel & Berth
    vessel_name: str
    vessel_imo: str
    berth_name: str
    berth_code: str

    # Schedule
    planned_start: datetime
    planned_end: datetime
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]

    # Duration
    planned_duration_hours: float
    actual_duration_hours: Optional[float]
    variance_hours: Optional[float]

    # Quantity
    total_planned_quantity: float
    total_actual_quantity: float
    variance_quantity: float

    # Performance
    planned_rate: Optional[float]
    actual_rate: Optional[float]
    efficiency: Optional[float]

    # Downtime
    total_downtime_hours: float
    downtime_breakdown: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Breakdown of downtime by reason"
    )

    # Cargos
    cargos: List[CargoResponse] = Field(default_factory=list)

    # Events
    events: List[OperationEventResponse] = Field(default_factory=list)

    # Equipment used
    equipment_used: List[str] = Field(default_factory=list)
    equipment_performance: List[Dict[str, Any]] = Field(default_factory=list)

    # Delays
    is_delayed: bool
    delay_reason: Optional[str]
    delay_minutes: float

    # Weather
    weather_conditions: Optional[str]

    # Personnel
    shift_supervisor: Optional[str]

    # Notes
    notes: Optional[str]

    generated_at: datetime


class CustomReportRequest(BaseModel):
    """Request for custom report"""
    report_name: str = Field(..., min_length=1, max_length=255)
    report_type: str = Field(..., description="Type of report (summary, detailed, commodity, equipment)")

    # Filters
    site_id: Optional[UUID] = None
    from_date: datetime
    to_date: datetime
    vessel_ids: List[UUID] = Field(default_factory=list)
    berth_ids: List[UUID] = Field(default_factory=list)
    commodities: List[CommodityType] = Field(default_factory=list)
    equipment_ids: List[UUID] = Field(default_factory=list)

    # Options
    include_charts: bool = Field(default=True, description="Include charts in report")
    include_events: bool = Field(default=True, description="Include operation events")
    include_equipment_details: bool = Field(default=False, description="Include equipment performance")
    group_by: Optional[str] = Field(None, description="Group by: vessel, berth, commodity, day, week, month")


class CustomReportResponse(BaseModel):
    """Custom report response"""
    report_id: UUID
    report_name: str
    report_type: str

    # Period
    period_start: datetime
    period_end: datetime

    # Summary
    summary: Dict[str, Any] = Field(default_factory=dict)

    # Data sections
    kpis: Optional[PortKPIResponse] = None
    performance: Optional[PerformanceMetricsResponse] = None
    commodity_breakdown: Optional[CommodityAnalyticsResponse] = None
    operations: List[Dict[str, Any]] = Field(default_factory=list)
    equipment_performance: List[EquipmentPerformanceResponse] = Field(default_factory=list)
    trends: List[TrendResponse] = Field(default_factory=list)

    # Export URLs (will be generated)
    pdf_url: Optional[str] = None
    excel_url: Optional[str] = None
    csv_url: Optional[str] = None

    generated_at: datetime
    generated_by: Optional[str] = None


# ===== Query Parameters =====

class AnalyticsQueryParams(BaseModel):
    """Common query parameters for analytics"""
    site_id: Optional[UUID] = None
    from_date: datetime
    to_date: datetime
    granularity: Optional[str] = Field(default="hour", description="Data granularity: minute, hour, day, week, month")
    include_trends: bool = Field(default=False, description="Include trend data")


class TrendQueryParams(BaseModel):
    """Query parameters for trend data"""
    site_id: Optional[UUID] = None
    from_date: datetime
    to_date: datetime
    metrics: List[str] = Field(..., description="Metrics to fetch: throughput, efficiency, utilization, etc.")
    granularity: str = Field(default="hour", description="Data granularity: minute, hour, day")
    equipment_id: Optional[UUID] = Field(None, description="Filter by equipment")
    berth_id: Optional[UUID] = Field(None, description="Filter by berth")
