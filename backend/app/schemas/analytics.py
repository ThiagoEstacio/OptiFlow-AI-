"""
Analytics Query Schemas

Pydantic models for advanced analytics queries supporting:
- Cross-tag comparisons
- Multi-dimensional aggregations
- Statistical functions
- Custom time windows
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from uuid import UUID


class QueryFilter(BaseModel):
    """
    Filter condition for analytics query

    Examples:
        - {"field": "quality", "operator": "eq", "value": "good"}
        - {"field": "value", "operator": "between", "value": [20, 80]}
        - {"field": "device_id", "operator": "in", "value": ["uuid1", "uuid2"]}
    """
    field: str = Field(..., description="Field to filter on")
    operator: Literal["eq", "ne", "gt", "lt", "gte", "lte", "in", "between"] = Field(
        ..., description="Comparison operator"
    )
    value: Any = Field(..., description="Value(s) to compare against")

    @field_validator('value')
    @classmethod
    def validate_value(cls, v, info):
        """Validate value based on operator"""
        operator = info.data.get('operator')
        if operator == 'between' and not isinstance(v, list):
            raise ValueError("'between' operator requires a list of two values")
        if operator == 'between' and len(v) != 2:
            raise ValueError("'between' operator requires exactly two values")
        if operator == 'in' and not isinstance(v, list):
            raise ValueError("'in' operator requires a list of values")
        return v


class QueryAggregation(BaseModel):
    """
    Aggregation function configuration

    Supported functions:
    - Basic: mean, median, mode, min, max, sum, count
    - Statistical: stddev, variance, percentile
    - Advanced: correlation, moving_average, rate_of_change
    - Outliers: outlier_detection
    """
    function: Literal[
        "mean", "median", "mode",
        "min", "max", "sum", "count",
        "stddev", "variance", "percentile",
        "correlation", "moving_average", "cumulative_sum",
        "rate_of_change", "outlier_detection"
    ] = Field(..., description="Aggregation function")

    field: str = Field(default="value", description="Field to aggregate")

    window: Optional[str] = Field(
        default="1m",
        description="Time window for aggregation (e.g., '1m', '5m', '1h', '1d')"
    )

    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Function-specific parameters"
    )

    @field_validator('params')
    @classmethod
    def validate_params(cls, v, info):
        """Validate params based on function"""
        function = info.data.get('function')

        if function == 'percentile':
            if not v or 'percentile' not in v:
                raise ValueError("percentile function requires 'percentile' parameter (0-100)")
            if not 0 <= v['percentile'] <= 100:
                raise ValueError("percentile must be between 0 and 100")

        if function == 'correlation':
            if not v or 'target_tag' not in v:
                raise ValueError("correlation function requires 'target_tag' parameter")

        if function == 'moving_average':
            if v and 'type' in v:
                if v['type'] not in ['simple', 'exponential', 'weighted']:
                    raise ValueError("moving_average type must be 'simple', 'exponential', or 'weighted'")

        if function == 'outlier_detection':
            if v and 'method' in v:
                if v['method'] not in ['zscore', 'iqr', 'isolation_forest']:
                    raise ValueError("outlier_detection method must be 'zscore', 'iqr', or 'isolation_forest'")

        return v


class AnalyticsQuery(BaseModel):
    """
    Advanced analytics query

    Example:
        {
            "tags": ["temp_sensor_01", "pressure_sensor_01"],
            "start": "2025-10-27T00:00:00Z",
            "end": "2025-10-28T00:00:00Z",
            "filters": [
                {"field": "quality", "operator": "eq", "value": "good"}
            ],
            "aggregations": [
                {
                    "function": "percentile",
                    "field": "value",
                    "window": "1h",
                    "params": {"percentile": 95}
                },
                {
                    "function": "correlation",
                    "field": "value",
                    "params": {"target_tag": "pressure_sensor_01"}
                }
            ],
            "group_by": ["device_id"],
            "limit": 1000
        }
    """
    tags: List[str] = Field(..., min_length=1, description="Tag IDs to query")

    start: datetime = Field(..., description="Start timestamp (ISO 8601)")
    end: datetime = Field(..., description="End timestamp (ISO 8601)")

    filters: Optional[List[QueryFilter]] = Field(
        default=[],
        description="Filter conditions"
    )

    aggregations: List[QueryAggregation] = Field(
        ..., min_length=1,
        description="Aggregation functions to apply"
    )

    group_by: Optional[List[str]] = Field(
        default=[],
        description="Fields to group by (e.g., 'device_id', 'site_id')"
    )

    limit: Optional[int] = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum number of results"
    )

    @field_validator('end')
    @classmethod
    def validate_time_range(cls, v, info):
        """Validate that end is after start"""
        start = info.data.get('start')
        if start and v <= start:
            raise ValueError("end must be after start")
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags_limit(cls, v):
        """Limit maximum number of tags to prevent performance issues"""
        if len(v) > 100:
            raise ValueError("Maximum 100 tags per query")
        return v


class TimeSeriesDataPoint(BaseModel):
    """Single data point in time series"""
    timestamp: datetime
    value: float
    quality: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AggregationResult(BaseModel):
    """Result of a single aggregation"""
    function: str
    field: str
    window: Optional[str] = None
    result: Any  # Can be float, dict, list depending on function
    metadata: Optional[Dict[str, Any]] = None


class QueryResult(BaseModel):
    """
    Result of analytics query

    Contains:
    - Raw time series data (if requested)
    - Aggregation results
    - Metadata (query time, rows, etc.)
    """
    query_id: Optional[str] = Field(default=None, description="Unique query identifier")

    data: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Raw time series data (if no aggregation or with raw=true)"
    )

    aggregations: List[AggregationResult] = Field(
        default=[],
        description="Results of aggregation functions"
    )

    metadata: Dict[str, Any] = Field(
        default={},
        description="Query execution metadata"
    )

    # Convenience fields
    total_rows: int = Field(default=0, description="Total number of data points")
    query_time_ms: float = Field(default=0, description="Query execution time in milliseconds")
    tags_analyzed: int = Field(default=0, description="Number of tags analyzed")


# Request/Response models for API

class AnalyticsQueryRequest(AnalyticsQuery):
    """Request model for analytics query endpoint"""
    include_raw_data: bool = Field(
        default=False,
        description="Include raw time series data in response (in addition to aggregations)"
    )


class AnalyticsQueryResponse(QueryResult):
    """Response model for analytics query endpoint"""
    pass


# Saved Query Templates

class SavedQuery(BaseModel):
    """Saved analytics query template"""
    id: Optional[UUID] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    query: AnalyticsQuery
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_public: bool = Field(default=False)
    tags_metadata: Optional[List[str]] = Field(default=[], description="Tags for categorization")


class SavedQueryCreate(BaseModel):
    """Create saved query"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    query: AnalyticsQuery
    is_public: bool = Field(default=False)
    tags_metadata: Optional[List[str]] = []


class SavedQueryUpdate(BaseModel):
    """Update saved query"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    query: Optional[AnalyticsQuery] = None
    is_public: Optional[bool] = None
    tags_metadata: Optional[List[str]] = None


class SavedQueryResponse(SavedQuery):
    """Saved query response"""
    id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
