"""
Analytics Service

Service for executing advanced analytics queries on time-series data.
Supports:
- Complex InfluxDB Flux queries
- Statistical aggregations
- Cross-tag correlations
- Pandas-based post-processing
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time
from uuid import uuid4

from app.schemas.analytics import (
    AnalyticsQuery,
    QueryFilter,
    QueryAggregation,
    QueryResult,
    AggregationResult,
)


class AnalyticsQueryBuilder:
    """
    Builder for InfluxDB Flux queries

    Converts AnalyticsQuery schema to Flux query language
    """

    def __init__(self, bucket: str = "smartport"):
        self.bucket = bucket

    def build_flux_query(self, query: AnalyticsQuery) -> str:
        """
        Build Flux query from AnalyticsQuery

        Returns:
            Flux query string
        """
        # Start with basic range and bucket
        flux_parts = [
            f'from(bucket: "{self.bucket}")',
            f'|> range(start: {self._format_time(query.start)}, stop: {self._format_time(query.end)})',
        ]

        # Filter by tags (measurement filter)
        tag_filter = self._build_tag_filter(query.tags)
        if tag_filter:
            flux_parts.append(f'|> filter(fn: (r) => {tag_filter})')

        # Apply custom filters
        for filter_cond in query.filters:
            flux_filter = self._build_filter(filter_cond)
            if flux_filter:
                flux_parts.append(f'|> filter(fn: (r) => {flux_filter})')

        # Group by if specified
        if query.group_by:
            group_cols = ', '.join([f'"{col}"' for col in query.group_by])
            flux_parts.append(f'|> group(columns: [{group_cols}])')

        # Apply aggregations
        for agg in query.aggregations:
            agg_flux = self._build_aggregation(agg)
            if agg_flux:
                flux_parts.append(agg_flux)

        # Limit results
        if query.limit:
            flux_parts.append(f'|> limit(n: {query.limit})')

        return '\n  '.join(flux_parts)

    def _format_time(self, dt: datetime) -> str:
        """Format datetime for Flux"""
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    def _build_tag_filter(self, tags: List[str]) -> str:
        """Build filter for tag IDs"""
        if len(tags) == 1:
            return f'r["tag_id"] == "{tags[0]}"'
        else:
            tag_conditions = ' or '.join([f'r["tag_id"] == "{tag}"' for tag in tags])
            return f'({tag_conditions})'

    def _build_filter(self, filter_cond: QueryFilter) -> str:
        """Build Flux filter from QueryFilter"""
        field = filter_cond.field
        operator = filter_cond.operator
        value = filter_cond.value

        # Map operators to Flux
        if operator == "eq":
            return f'r["{field}"] == {self._format_value(value)}'
        elif operator == "ne":
            return f'r["{field}"] != {self._format_value(value)}'
        elif operator == "gt":
            return f'r["{field}"] > {self._format_value(value)}'
        elif operator == "lt":
            return f'r["{field}"] < {self._format_value(value)}'
        elif operator == "gte":
            return f'r["{field}"] >= {self._format_value(value)}'
        elif operator == "lte":
            return f'r["{field}"] <= {self._format_value(value)}'
        elif operator == "in":
            values = ', '.join([self._format_value(v) for v in value])
            return f'contains(value: r["{field}"], set: [{values}])'
        elif operator == "between":
            return f'r["{field}"] >= {self._format_value(value[0])} and r["{field}"] <= {self._format_value(value[1])}'

        return ""

    def _format_value(self, value: Any) -> str:
        """Format value for Flux"""
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return f'"{str(value)}"'

    def _build_aggregation(self, agg: QueryAggregation) -> str:
        """Build Flux aggregation"""
        function = agg.function
        field = agg.field
        window = agg.window or "1m"

        # Basic aggregations (Flux native)
        if function == "mean":
            return f'|> aggregateWindow(every: {window}, fn: mean, createEmpty: false)'
        elif function == "median":
            return f'|> aggregateWindow(every: {window}, fn: median, createEmpty: false)'
        elif function == "min":
            return f'|> aggregateWindow(every: {window}, fn: min, createEmpty: false)'
        elif function == "max":
            return f'|> aggregateWindow(every: {window}, fn: max, createEmpty: false)'
        elif function == "sum":
            return f'|> aggregateWindow(every: {window}, fn: sum, createEmpty: false)'
        elif function == "count":
            return f'|> aggregateWindow(every: {window}, fn: count, createEmpty: false)'
        elif function == "stddev":
            return f'|> aggregateWindow(every: {window}, fn: stddev, createEmpty: false)'

        # For advanced functions (correlation, percentile, etc), we'll process in pandas
        # Return empty string here, processing will happen in execute_query
        return ""


class AnalyticsService:
    """
    Service for executing analytics queries

    Handles:
    1. Query building (Flux)
    2. Query execution (InfluxDB)
    3. Post-processing (Pandas for advanced functions)
    4. Result formatting
    """

    def __init__(self, influxdb_client=None, bucket: str = "smartport"):
        self.influxdb_client = influxdb_client
        self.bucket = bucket
        self.query_builder = AnalyticsQueryBuilder(bucket)

    async def execute_query(self, query: AnalyticsQuery, include_raw: bool = False) -> QueryResult:
        """
        Execute analytics query

        Args:
            query: AnalyticsQuery object
            include_raw: Include raw data in response (in addition to aggregations)

        Returns:
            QueryResult with aggregation results and optional raw data
        """
        start_time = time.time()
        query_id = str(uuid4())

        # Build Flux query
        flux_query = self.query_builder.build_flux_query(query)

        # Execute query (placeholder - will integrate with actual InfluxDB)
        raw_data = await self._execute_flux_query(flux_query)

        # Convert to pandas for processing
        df = self._to_dataframe(raw_data)

        # Execute aggregations
        aggregation_results = []
        for agg in query.aggregations:
            result = self._execute_aggregation(df, agg, query.tags)
            aggregation_results.append(result)

        # Calculate query time
        query_time_ms = (time.time() - start_time) * 1000

        return QueryResult(
            query_id=query_id,
            data=raw_data if include_raw else None,
            aggregations=aggregation_results,
            metadata={
                "flux_query": flux_query,
                "start": query.start.isoformat(),
                "end": query.end.isoformat(),
            },
            total_rows=len(df) if df is not None else 0,
            query_time_ms=round(query_time_ms, 2),
            tags_analyzed=len(query.tags),
        )

    async def _execute_flux_query(self, flux_query: str) -> List[Dict[str, Any]]:
        """
        Execute Flux query against InfluxDB

        TODO: Integrate with actual InfluxDB client
        For now, returns mock data
        """
        # MOCK DATA - Replace with actual InfluxDB query
        # Example:
        # query_api = self.influxdb_client.query_api()
        # tables = query_api.query(flux_query)
        # return self._parse_flux_result(tables)

        # Return empty for now
        return []

    def _to_dataframe(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert query result to pandas DataFrame"""
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Convert timestamp to datetime if present
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        return df

    def _execute_aggregation(
        self,
        df: pd.DataFrame,
        agg: QueryAggregation,
        tags: List[str]
    ) -> AggregationResult:
        """
        Execute single aggregation function

        Handles advanced functions that can't be done in Flux:
        - Percentile
        - Correlation
        - Moving average
        - Outlier detection
        """
        function = agg.function
        field = agg.field
        params = agg.params or {}

        result_value = None
        metadata = {}

        if df.empty:
            return AggregationResult(
                function=function,
                field=field,
                window=agg.window,
                result=None,
                metadata={"error": "No data available"}
            )

        # Percentile
        if function == "percentile":
            percentile = params.get("percentile", 50)
            result_value = float(df[field].quantile(percentile / 100))
            metadata["percentile"] = percentile

        # Correlation
        elif function == "correlation":
            target_tag = params.get("target_tag")
            if target_tag and target_tag in tags:
                # Group by tag_id and calculate correlation
                pivot_df = df.pivot_table(
                    values=field,
                    index='timestamp',
                    columns='tag_id',
                    aggfunc='mean'
                )

                if len(pivot_df.columns) >= 2:
                    # Correlation between first tag and target
                    source_tag = [t for t in tags if t != target_tag][0]
                    if source_tag in pivot_df.columns and target_tag in pivot_df.columns:
                        corr = pivot_df[source_tag].corr(pivot_df[target_tag])
                        result_value = float(corr)
                        metadata["source_tag"] = source_tag
                        metadata["target_tag"] = target_tag
                else:
                    result_value = None
                    metadata["error"] = "Insufficient data for correlation"
            else:
                result_value = None
                metadata["error"] = "Target tag not found"

        # Moving Average
        elif function == "moving_average":
            ma_type = params.get("type", "simple")
            window_size = params.get("window_size", 10)

            if ma_type == "simple":
                result_series = df[field].rolling(window=window_size).mean()
            elif ma_type == "exponential":
                result_series = df[field].ewm(span=window_size).mean()
            elif ma_type == "weighted":
                weights = np.arange(1, window_size + 1)
                result_series = df[field].rolling(window=window_size).apply(
                    lambda x: np.sum(weights * x) / weights.sum(), raw=True
                )
            else:
                result_series = df[field].rolling(window=window_size).mean()

            # Return last N values
            result_value = result_series.dropna().tail(100).tolist()
            metadata["type"] = ma_type
            metadata["window_size"] = window_size

        # Cumulative Sum
        elif function == "cumulative_sum":
            result_series = df[field].cumsum()
            result_value = result_series.tail(100).tolist()

        # Rate of Change
        elif function == "rate_of_change":
            result_series = df[field].pct_change()
            result_value = float(result_series.mean())
            metadata["max_rate"] = float(result_series.max())
            metadata["min_rate"] = float(result_series.min())

        # Outlier Detection
        elif function == "outlier_detection":
            method = params.get("method", "zscore")

            if method == "zscore":
                z_scores = np.abs((df[field] - df[field].mean()) / df[field].std())
                threshold = params.get("threshold", 3)
                outliers = df[z_scores > threshold]

            elif method == "iqr":
                Q1 = df[field].quantile(0.25)
                Q3 = df[field].quantile(0.75)
                IQR = Q3 - Q1
                multiplier = params.get("multiplier", 1.5)
                outliers = df[(df[field] < Q1 - multiplier * IQR) | (df[field] > Q3 + multiplier * IQR)]

            else:  # isolation_forest would require scikit-learn
                outliers = pd.DataFrame()

            result_value = {
                "outlier_count": len(outliers),
                "outlier_percentage": round(len(outliers) / len(df) * 100, 2) if len(df) > 0 else 0,
                "outliers": outliers.head(100).to_dict('records') if not outliers.empty else []
            }
            metadata["method"] = method

        # Variance
        elif function == "variance":
            result_value = float(df[field].var())

        # Mode
        elif function == "mode":
            mode_values = df[field].mode()
            result_value = float(mode_values[0]) if not mode_values.empty else None

        # Basic aggregations (if not done in Flux)
        elif function == "mean":
            result_value = float(df[field].mean())
        elif function == "median":
            result_value = float(df[field].median())
        elif function == "min":
            result_value = float(df[field].min())
        elif function == "max":
            result_value = float(df[field].max())
        elif function == "sum":
            result_value = float(df[field].sum())
        elif function == "count":
            result_value = int(df[field].count())
        elif function == "stddev":
            result_value = float(df[field].std())

        return AggregationResult(
            function=function,
            field=field,
            window=agg.window,
            result=result_value,
            metadata=metadata
        )


# Convenience functions for common analytics patterns

def calculate_correlation_matrix(df: pd.DataFrame, tags: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Calculate correlation matrix between multiple tags

    Returns:
        Nested dict: {tag1: {tag2: correlation, tag3: correlation}, ...}
    """
    # Pivot data
    pivot_df = df.pivot_table(
        values='value',
        index='timestamp',
        columns='tag_id',
        aggfunc='mean'
    )

    # Calculate correlation matrix
    corr_matrix = pivot_df.corr()

    # Convert to nested dict
    result = {}
    for tag1 in tags:
        if tag1 in corr_matrix.columns:
            result[tag1] = {}
            for tag2 in tags:
                if tag2 in corr_matrix.columns:
                    result[tag1][tag2] = float(corr_matrix.loc[tag1, tag2])

    return result


def calculate_percentiles(df: pd.DataFrame, field: str = 'value', percentiles: List[int] = None) -> Dict[str, float]:
    """
    Calculate multiple percentiles

    Args:
        df: DataFrame with data
        field: Field to calculate percentiles on
        percentiles: List of percentiles (e.g., [50, 90, 95, 99])

    Returns:
        Dict mapping percentile to value
    """
    if percentiles is None:
        percentiles = [50, 90, 95, 99]

    result = {}
    for p in percentiles:
        result[f"P{p}"] = float(df[field].quantile(p / 100))

    return result


def detect_anomalies_zscore(df: pd.DataFrame, field: str = 'value', threshold: float = 3.0) -> pd.DataFrame:
    """
    Detect anomalies using Z-score method

    Args:
        df: DataFrame with data
        field: Field to check for anomalies
        threshold: Z-score threshold (default: 3.0)

    Returns:
        DataFrame with only anomalous rows
    """
    z_scores = np.abs((df[field] - df[field].mean()) / df[field].std())
    return df[z_scores > threshold]


def calculate_moving_average(
    df: pd.DataFrame,
    field: str = 'value',
    window: int = 10,
    ma_type: str = 'simple'
) -> pd.Series:
    """
    Calculate moving average

    Args:
        df: DataFrame with data
        field: Field to calculate MA on
        window: Window size
        ma_type: Type - 'simple', 'exponential', or 'weighted'

    Returns:
        Series with moving average values
    """
    if ma_type == 'simple':
        return df[field].rolling(window=window).mean()
    elif ma_type == 'exponential':
        return df[field].ewm(span=window).mean()
    elif ma_type == 'weighted':
        weights = np.arange(1, window + 1)
        return df[field].rolling(window=window).apply(
            lambda x: np.sum(weights * x) / weights.sum(), raw=True
        )
    else:
        return df[field].rolling(window=window).mean()
