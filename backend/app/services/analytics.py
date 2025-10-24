"""
Advanced Analytics Service for Time Series Data
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from scipy import stats, signal
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Advanced analytics for time series data"""

    def __init__(self):
        self.scaler = StandardScaler()

    async def calculate_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistical metrics for time series data

        Returns:
            Dictionary with mean, median, std, min, max, percentiles, etc.
        """
        try:
            if not data:
                return {}

            df = pd.DataFrame(data)

            if 'value' not in df.columns:
                return {}

            values = df['value'].dropna()

            if len(values) == 0:
                return {}

            return {
                "count": len(values),
                "mean": float(values.mean()),
                "median": float(values.median()),
                "std": float(values.std()),
                "variance": float(values.var()),
                "min": float(values.min()),
                "max": float(values.max()),
                "range": float(values.max() - values.min()),
                "percentiles": {
                    "p25": float(values.quantile(0.25)),
                    "p50": float(values.quantile(0.50)),
                    "p75": float(values.quantile(0.75)),
                    "p90": float(values.quantile(0.90)),
                    "p95": float(values.quantile(0.95)),
                    "p99": float(values.quantile(0.99))
                },
                "skewness": float(values.skew()),
                "kurtosis": float(values.kurtosis())
            }

        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}

    async def detect_anomalies(
        self,
        data: List[Dict[str, Any]],
        method: str = "zscore",
        threshold: float = 3.0
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in time series data

        Methods:
        - zscore: Z-score based detection
        - iqr: Interquartile range method
        - mad: Median Absolute Deviation

        Returns:
            List of anomaly points with scores
        """
        try:
            if not data:
                return []

            df = pd.DataFrame(data)

            if 'value' not in df.columns:
                return []

            values = df['value'].values
            anomalies = []

            if method == "zscore":
                # Z-score method
                z_scores = np.abs(stats.zscore(values, nan_policy='omit'))
                anomaly_indices = np.where(z_scores > threshold)[0]

                for idx in anomaly_indices:
                    anomalies.append({
                        **data[idx],
                        "anomaly_score": float(z_scores[idx]),
                        "method": "zscore"
                    })

            elif method == "iqr":
                # IQR method
                q1 = np.percentile(values, 25)
                q3 = np.percentile(values, 75)
                iqr = q3 - q1
                lower_bound = q1 - threshold * iqr
                upper_bound = q3 + threshold * iqr

                for idx, value in enumerate(values):
                    if value < lower_bound or value > upper_bound:
                        deviation = min(abs(value - lower_bound), abs(value - upper_bound))
                        anomalies.append({
                            **data[idx],
                            "anomaly_score": float(deviation / iqr),
                            "method": "iqr"
                        })

            elif method == "mad":
                # Median Absolute Deviation method
                median = np.median(values)
                mad = np.median(np.abs(values - median))
                modified_z_scores = 0.6745 * (values - median) / mad

                anomaly_indices = np.where(np.abs(modified_z_scores) > threshold)[0]

                for idx in anomaly_indices:
                    anomalies.append({
                        **data[idx],
                        "anomaly_score": float(abs(modified_z_scores[idx])),
                        "method": "mad"
                    })

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    async def calculate_trends(
        self,
        data: List[Dict[str, Any]],
        window: int = 10
    ) -> Dict[str, Any]:
        """
        Calculate trend information using linear regression

        Returns:
            Trend slope, direction, and strength
        """
        try:
            if not data or len(data) < 2:
                return {}

            df = pd.DataFrame(data)

            if 'value' not in df.columns or 'timestamp' not in df.columns:
                return {}

            # Convert timestamp to numeric
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['time_numeric'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds()

            # Linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                df['time_numeric'].values,
                df['value'].values
            )

            # Determine trend direction
            if abs(slope) < std_err:
                direction = "stable"
            elif slope > 0:
                direction = "increasing"
            else:
                direction = "decreasing"

            # Calculate moving average
            df['moving_avg'] = df['value'].rolling(window=window, min_periods=1).mean()

            return {
                "slope": float(slope),
                "intercept": float(intercept),
                "r_squared": float(r_value ** 2),
                "p_value": float(p_value),
                "std_error": float(std_err),
                "direction": direction,
                "strength": float(abs(r_value)),
                "moving_average": df['moving_avg'].tolist()
            }

        except Exception as e:
            logger.error(f"Error calculating trends: {e}")
            return {}

    async def forecast_simple(
        self,
        data: List[Dict[str, Any]],
        periods: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Simple linear forecast for time series data

        Returns:
            List of forecasted points
        """
        try:
            if not data or len(data) < 2:
                return []

            df = pd.DataFrame(data)

            if 'value' not in df.columns or 'timestamp' not in df.columns:
                return []

            # Convert timestamp to numeric
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['time_numeric'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds()

            # Linear regression
            slope, intercept, _, _, _ = stats.linregress(
                df['time_numeric'].values,
                df['value'].values
            )

            # Generate forecasts
            last_time = df['timestamp'].max()
            time_diff = df['timestamp'].diff().median()

            forecasts = []
            for i in range(1, periods + 1):
                forecast_time = last_time + (time_diff * i)
                time_numeric = (forecast_time - df['timestamp'].min()).total_seconds()
                forecast_value = slope * time_numeric + intercept

                forecasts.append({
                    "timestamp": forecast_time.isoformat(),
                    "value": float(forecast_value),
                    "type": "forecast"
                })

            return forecasts

        except Exception as e:
            logger.error(f"Error forecasting: {e}")
            return []

    async def calculate_correlation(
        self,
        data1: List[Dict[str, Any]],
        data2: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate correlation between two time series

        Returns:
            Correlation coefficient and p-value
        """
        try:
            if not data1 or not data2:
                return {}

            df1 = pd.DataFrame(data1)
            df2 = pd.DataFrame(data2)

            if 'value' not in df1.columns or 'value' not in df2.columns:
                return {}

            # Align time series by timestamp if available
            if 'timestamp' in df1.columns and 'timestamp' in df2.columns:
                df1['timestamp'] = pd.to_datetime(df1['timestamp'])
                df2['timestamp'] = pd.to_datetime(df2['timestamp'])

                merged = pd.merge(df1, df2, on='timestamp', suffixes=('_1', '_2'))
                values1 = merged['value_1'].values
                values2 = merged['value_2'].values
            else:
                # Use as-is if no timestamp
                min_len = min(len(df1), len(df2))
                values1 = df1['value'].values[:min_len]
                values2 = df2['value'].values[:min_len]

            # Calculate Pearson correlation
            pearson_corr, pearson_p = stats.pearsonr(values1, values2)

            # Calculate Spearman correlation
            spearman_corr, spearman_p = stats.spearmanr(values1, values2)

            return {
                "pearson": {
                    "correlation": float(pearson_corr),
                    "p_value": float(pearson_p),
                    "significant": pearson_p < 0.05
                },
                "spearman": {
                    "correlation": float(spearman_corr),
                    "p_value": float(spearman_p),
                    "significant": spearman_p < 0.05
                },
                "sample_size": len(values1)
            }

        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return {}

    async def resample_data(
        self,
        data: List[Dict[str, Any]],
        interval: str,
        aggregation: str = "mean"
    ) -> List[Dict[str, Any]]:
        """
        Resample time series data to a different interval

        Intervals: '1min', '5min', '1h', '1d', etc.
        Aggregations: 'mean', 'sum', 'min', 'max', 'first', 'last'
        """
        try:
            if not data:
                return []

            df = pd.DataFrame(data)

            if 'value' not in df.columns or 'timestamp' not in df.columns:
                return []

            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)

            # Resample based on aggregation method
            if aggregation == "mean":
                resampled = df.resample(interval).mean()
            elif aggregation == "sum":
                resampled = df.resample(interval).sum()
            elif aggregation == "min":
                resampled = df.resample(interval).min()
            elif aggregation == "max":
                resampled = df.resample(interval).max()
            elif aggregation == "first":
                resampled = df.resample(interval).first()
            elif aggregation == "last":
                resampled = df.resample(interval).last()
            else:
                resampled = df.resample(interval).mean()

            # Convert back to list of dicts
            resampled.reset_index(inplace=True)
            result = resampled.to_dict('records')

            # Convert timestamps to ISO format
            for item in result:
                if 'timestamp' in item:
                    item['timestamp'] = item['timestamp'].isoformat()

            return result

        except Exception as e:
            logger.error(f"Error resampling data: {e}")
            return []

    async def calculate_fft(
        self,
        data: List[Dict[str, Any]],
        top_frequencies: int = 10
    ) -> Dict[str, Any]:
        """
        Calculate Fast Fourier Transform to detect periodicity

        Returns:
            Top frequencies and their magnitudes
        """
        try:
            if not data:
                return {}

            df = pd.DataFrame(data)

            if 'value' not in df.columns:
                return {}

            values = df['value'].values

            # Perform FFT
            fft_values = np.fft.fft(values)
            frequencies = np.fft.fftfreq(len(values))

            # Get magnitudes
            magnitudes = np.abs(fft_values)

            # Get top frequencies (excluding DC component)
            indices = np.argsort(magnitudes[1:len(magnitudes)//2])[-top_frequencies:][::-1] + 1

            top_freqs = []
            for idx in indices:
                top_freqs.append({
                    "frequency": float(frequencies[idx]),
                    "magnitude": float(magnitudes[idx]),
                    "period": float(1/abs(frequencies[idx])) if frequencies[idx] != 0 else None
                })

            return {
                "top_frequencies": top_freqs,
                "dominant_frequency": float(frequencies[indices[0]]),
                "dominant_period": float(1/abs(frequencies[indices[0]])) if frequencies[indices[0]] != 0 else None
            }

        except Exception as e:
            logger.error(f"Error calculating FFT: {e}")
            return {}


# Global analytics service instance
analytics_service = AnalyticsService()
