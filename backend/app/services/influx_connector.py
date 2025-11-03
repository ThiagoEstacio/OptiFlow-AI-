"""
InfluxDB Connector Service

Provides integration with InfluxDB for time series data:
- Query historical data
- Real-time data streaming
- Batch data retrieval
- Aggregations and downsampling
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class InfluxDBConnector:
    """
    InfluxDB Connector

    Handles all interactions with InfluxDB time series database
    """

    def __init__(
        self,
        url: str = None,
        token: str = None,
        org: str = None,
        bucket: str = None
    ):
        """
        Initialize InfluxDB connector

        Args:
            url: InfluxDB URL
            token: Authentication token
            org: Organization name
            bucket: Default bucket name
        """
        self.url = url or "http://localhost:8086"
        self.token = token
        self.org = org or "optiflow"
        self.bucket = bucket or "industrial_data"
        self.client = None
        self.query_api = None
        self.write_api = None

        self._connect()

    def _connect(self):
        """Connect to InfluxDB"""
        try:
            from influxdb_client import InfluxDBClient
            from influxdb_client.client.write_api import SYNCHRONOUS

            if self.token:
                self.client = InfluxDBClient(
                    url=self.url,
                    token=self.token,
                    org=self.org
                )

                self.query_api = self.client.query_api()
                self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

                logger.info(f"Connected to InfluxDB at {self.url}")
            else:
                logger.warning("InfluxDB token not provided - using mock data mode")

        except ImportError:
            logger.warning("influxdb-client not installed. Install with: pip install influxdb-client")
        except Exception as e:
            logger.error(f"Error connecting to InfluxDB: {e}")

    def query_tag_data(
        self,
        tag_id: str,
        start: datetime,
        end: datetime,
        measurement: str = "tag_values",
        aggregation: str = None,
        window: str = None
    ) -> pd.DataFrame:
        """
        Query data for a specific tag

        Args:
            tag_id: Tag ID
            start: Start datetime
            end: End datetime
            measurement: InfluxDB measurement name
            aggregation: Aggregation function (mean, max, min, sum)
            window: Aggregation window (e.g., '5m', '1h')

        Returns:
            DataFrame with columns: timestamp, value
        """
        if not self.query_api:
            logger.warning("InfluxDB not connected - using mock data")
            return self._generate_mock_data(tag_id, start, end)

        try:
            # Build Flux query
            query = self._build_flux_query(
                measurement=measurement,
                tag_id=tag_id,
                start=start,
                end=end,
                aggregation=aggregation,
                window=window
            )

            # Execute query
            result = self.query_api.query_data_frame(query)

            if result.empty:
                logger.warning(f"No data found for tag {tag_id}")
                return pd.DataFrame(columns=['timestamp', 'value'])

            # Process result
            df = self._process_query_result(result)

            return df

        except Exception as e:
            logger.error(f"Error querying InfluxDB: {e}")
            # Fallback to mock data
            return self._generate_mock_data(tag_id, start, end)

    def query_multiple_tags(
        self,
        tag_ids: List[str],
        start: datetime,
        end: datetime,
        measurement: str = "tag_values"
    ) -> Dict[str, pd.DataFrame]:
        """
        Query data for multiple tags

        Args:
            tag_ids: List of tag IDs
            start: Start datetime
            end: End datetime
            measurement: InfluxDB measurement name

        Returns:
            Dict mapping tag_id to DataFrame
        """
        results = {}

        for tag_id in tag_ids:
            data = self.query_tag_data(
                tag_id=tag_id,
                start=start,
                end=end,
                measurement=measurement
            )

            results[tag_id] = data

        return results

    def query_multivariate(
        self,
        tag_ids: List[str],
        start: datetime,
        end: datetime,
        measurement: str = "tag_values"
    ) -> pd.DataFrame:
        """
        Query multiple tags and merge into single DataFrame

        Args:
            tag_ids: List of tag IDs
            start: Start datetime
            end: End datetime
            measurement: InfluxDB measurement name

        Returns:
            DataFrame with columns: timestamp, tag_1, tag_2, ...
        """
        tag_data = self.query_multiple_tags(tag_ids, start, end, measurement)

        if not tag_data:
            return pd.DataFrame()

        # Merge all DataFrames on timestamp
        merged_df = None

        for tag_id, df in tag_data.items():
            if df.empty:
                continue

            df = df.rename(columns={'value': f'tag_{tag_id}'})

            if merged_df is None:
                merged_df = df
            else:
                merged_df = merged_df.merge(df, on='timestamp', how='outer')

        if merged_df is None:
            return pd.DataFrame()

        # Sort by timestamp
        merged_df = merged_df.sort_values('timestamp').reset_index(drop=True)

        return merged_df

    def _build_flux_query(
        self,
        measurement: str,
        tag_id: str,
        start: datetime,
        end: datetime,
        aggregation: str = None,
        window: str = None
    ) -> str:
        """Build Flux query string"""

        # Convert datetime to RFC3339
        start_str = start.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_str = end.strftime('%Y-%m-%dT%H:%M:%SZ')

        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: {start_str}, stop: {end_str})
            |> filter(fn: (r) => r["_measurement"] == "{measurement}")
            |> filter(fn: (r) => r["tag_id"] == "{tag_id}")
            |> filter(fn: (r) => r["_field"] == "value")
        '''

        # Add aggregation if specified
        if aggregation and window:
            query += f'''
            |> aggregateWindow(every: {window}, fn: {aggregation}, createEmpty: false)
            '''

        query += '''
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> keep(columns: ["_time", "value"])
        '''

        return query

    def _process_query_result(self, result: pd.DataFrame) -> pd.DataFrame:
        """Process InfluxDB query result"""

        if '_time' in result.columns:
            result = result.rename(columns={'_time': 'timestamp'})

        if 'timestamp' in result.columns:
            result['timestamp'] = pd.to_datetime(result['timestamp'])

        # Keep only timestamp and value columns
        columns_to_keep = ['timestamp', 'value']
        available_columns = [col for col in columns_to_keep if col in result.columns]

        if available_columns:
            result = result[available_columns]

        return result.reset_index(drop=True)

    def _generate_mock_data(
        self,
        tag_id: str,
        start: datetime,
        end: datetime,
        base_value: float = 50.0,
        noise_level: float = 5.0
    ) -> pd.DataFrame:
        """
        Generate mock data when InfluxDB is unavailable

        Args:
            tag_id: Tag ID
            start: Start datetime
            end: End datetime
            base_value: Base value
            noise_level: Noise standard deviation

        Returns:
            DataFrame with mock data
        """
        # Generate timestamps (1 minute intervals)
        timestamps = pd.date_range(start=start, end=end, freq='1min')

        # Generate values with noise
        n_points = len(timestamps)
        values = base_value + np.random.normal(0, noise_level, n_points)

        # Add some trend
        trend = np.linspace(0, 5, n_points)
        values += trend

        # Add occasional anomalies
        anomaly_mask = np.random.random(n_points) < 0.05
        values[anomaly_mask] += np.random.choice([-1, 1], np.sum(anomaly_mask)) * noise_level * 5

        return pd.DataFrame({
            'timestamp': timestamps,
            'value': values
        })

    def write_data(
        self,
        measurement: str,
        tag_id: str,
        value: float,
        timestamp: datetime = None,
        tags: Dict[str, str] = None,
        fields: Dict[str, Any] = None
    ):
        """
        Write data point to InfluxDB

        Args:
            measurement: Measurement name
            tag_id: Tag ID
            value: Value to write
            timestamp: Timestamp (default: now)
            tags: Additional tags
            fields: Additional fields
        """
        if not self.write_api:
            logger.warning("InfluxDB not connected - skipping write")
            return

        try:
            from influxdb_client import Point

            point = Point(measurement)

            # Add tags
            point = point.tag("tag_id", tag_id)

            if tags:
                for key, val in tags.items():
                    point = point.tag(key, val)

            # Add fields
            point = point.field("value", value)

            if fields:
                for key, val in fields.items():
                    point = point.field(key, val)

            # Add timestamp
            if timestamp:
                point = point.time(timestamp)

            # Write
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)

        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")

    def write_batch(
        self,
        measurement: str,
        data: pd.DataFrame
    ):
        """
        Write batch of data to InfluxDB

        Args:
            measurement: Measurement name
            data: DataFrame with columns: tag_id, timestamp, value
        """
        if not self.write_api:
            logger.warning("InfluxDB not connected - skipping batch write")
            return

        try:
            from influxdb_client import Point

            points = []

            for _, row in data.iterrows():
                point = Point(measurement)
                point = point.tag("tag_id", row['tag_id'])
                point = point.field("value", row['value'])

                if 'timestamp' in row:
                    point = point.time(row['timestamp'])

                points.append(point)

            # Write all points
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)

            logger.info(f"Wrote {len(points)} points to InfluxDB")

        except Exception as e:
            logger.error(f"Error writing batch to InfluxDB: {e}")

    def get_tag_statistics(
        self,
        tag_id: str,
        start: datetime,
        end: datetime,
        measurement: str = "tag_values"
    ) -> Dict[str, float]:
        """
        Get statistical summary for a tag

        Args:
            tag_id: Tag ID
            start: Start datetime
            end: End datetime
            measurement: Measurement name

        Returns:
            Dict with statistics
        """
        data = self.query_tag_data(tag_id, start, end, measurement)

        if data.empty:
            return {}

        values = data['value'].values

        return {
            "count": int(len(values)),
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "median": float(np.median(values)),
            "p25": float(np.percentile(values, 25)),
            "p75": float(np.percentile(values, 75)),
            "p95": float(np.percentile(values, 95))
        }

    def close(self):
        """Close InfluxDB connection"""
        if self.client:
            self.client.close()
            logger.info("InfluxDB connection closed")


# Singleton instance
_influx_connector = None


def get_influx_connector(
    url: str = None,
    token: str = None,
    org: str = None,
    bucket: str = None
) -> InfluxDBConnector:
    """Get singleton instance of InfluxDB Connector"""
    global _influx_connector

    if _influx_connector is None:
        _influx_connector = InfluxDBConnector(url, token, org, bucket)

    return _influx_connector
