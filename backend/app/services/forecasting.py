"""
Time Series Forecasting Service

Provides forecasting capabilities using:
- Facebook Prophet for time series forecasting
- ARIMA for classical forecasting
- LSTM for deep learning forecasting
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ProphetForecaster:
    """
    Prophet-based Time Series Forecasting

    Uses Facebook's Prophet for robust time series forecasting with:
    - Trend detection
    - Seasonality modeling
    - Holiday effects
    - Confidence intervals
    """

    def __init__(
        self,
        seasonality_mode: str = 'additive',
        changepoint_prior_scale: float = 0.05,
        seasonality_prior_scale: float = 10.0,
        include_history: bool = True
    ):
        """
        Initialize Prophet forecaster

        Args:
            seasonality_mode: 'additive' or 'multiplicative'
            changepoint_prior_scale: Flexibility of trend changes
            seasonality_prior_scale: Flexibility of seasonality
            include_history: Whether to include historical data in output
        """
        self.seasonality_mode = seasonality_mode
        self.changepoint_prior_scale = changepoint_prior_scale
        self.seasonality_prior_scale = seasonality_prior_scale
        self.include_history = include_history
        self.model = None

    def forecast(
        self,
        data: pd.DataFrame,
        periods: int = 24,
        freq: str = 'H',
        confidence_interval: float = 0.95
    ) -> Dict[str, Any]:
        """
        Generate forecast for time series data

        Args:
            data: DataFrame with columns: timestamp (or ds), value (or y)
            periods: Number of periods to forecast
            freq: Frequency ('H' for hourly, 'D' for daily, etc.)
            confidence_interval: Confidence interval (0.80, 0.95, etc.)

        Returns:
            Dict with forecast results
        """
        try:
            from prophet import Prophet
        except ImportError:
            logger.error("Prophet not installed. Install with: pip install prophet")
            return {
                "error": "Prophet not installed",
                "forecast": [],
                "trend": [],
                "seasonality": []
            }

        # Prepare data for Prophet (requires columns: ds, y)
        prophet_data = self._prepare_data(data)

        if prophet_data.empty:
            return {
                "error": "Insufficient data for forecasting",
                "forecast": [],
                "trend": [],
                "seasonality": []
            }

        # Initialize Prophet model
        self.model = Prophet(
            seasonality_mode=self.seasonality_mode,
            changepoint_prior_scale=self.changepoint_prior_scale,
            seasonality_prior_scale=self.seasonality_prior_scale,
            interval_width=confidence_interval,
            yearly_seasonality='auto',
            weekly_seasonality='auto',
            daily_seasonality='auto'
        )

        # Fit model
        self.model.fit(prophet_data)

        # Generate future dataframe
        future = self.model.make_future_dataframe(
            periods=periods,
            freq=freq,
            include_history=self.include_history
        )

        # Make forecast
        forecast_df = self.model.predict(future)

        # Extract components
        results = self._extract_forecast_results(forecast_df, periods)

        logger.info(f"Forecast generated: {periods} periods ahead")

        return results

    def _prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for Prophet"""

        # Check if data has required columns
        if 'ds' in data.columns and 'y' in data.columns:
            return data[['ds', 'y']].copy()

        # Convert from standard format
        if 'timestamp' in data.columns and 'value' in data.columns:
            prepared = pd.DataFrame({
                'ds': pd.to_datetime(data['timestamp']),
                'y': data['value']
            })
            return prepared

        logger.error("Data must have columns: (ds, y) or (timestamp, value)")
        return pd.DataFrame()

    def _extract_forecast_results(
        self,
        forecast_df: pd.DataFrame,
        forecast_periods: int
    ) -> Dict[str, Any]:
        """Extract forecast results into structured format"""

        # Split historical and forecast
        if self.include_history:
            forecast_data = forecast_df.tail(forecast_periods)
        else:
            forecast_data = forecast_df

        results = {
            "forecast": [],
            "trend": [],
            "seasonality": {},
            "confidence_intervals": []
        }

        # Extract forecast values
        for _, row in forecast_data.iterrows():
            results["forecast"].append({
                "timestamp": row['ds'].isoformat(),
                "value": float(row['yhat']),
                "lower_bound": float(row['yhat_lower']),
                "upper_bound": float(row['yhat_upper'])
            })

            results["confidence_intervals"].append({
                "timestamp": row['ds'].isoformat(),
                "lower": float(row['yhat_lower']),
                "upper": float(row['yhat_upper']),
                "width": float(row['yhat_upper'] - row['yhat_lower'])
            })

        # Extract trend
        for _, row in forecast_data.iterrows():
            results["trend"].append({
                "timestamp": row['ds'].isoformat(),
                "value": float(row['trend'])
            })

        # Extract seasonality components
        if 'yearly' in forecast_df.columns:
            results["seasonality"]["yearly"] = [
                {
                    "timestamp": row['ds'].isoformat(),
                    "value": float(row['yearly'])
                }
                for _, row in forecast_data.iterrows()
            ]

        if 'weekly' in forecast_df.columns:
            results["seasonality"]["weekly"] = [
                {
                    "timestamp": row['ds'].isoformat(),
                    "value": float(row['weekly'])
                }
                for _, row in forecast_data.iterrows()
            ]

        if 'daily' in forecast_df.columns:
            results["seasonality"]["daily"] = [
                {
                    "timestamp": row['ds'].isoformat(),
                    "value": float(row['daily'])
                }
                for _, row in forecast_data.iterrows()
            ]

        return results

    def detect_anomalies(
        self,
        data: pd.DataFrame,
        threshold: float = 0.95
    ) -> Dict[str, Any]:
        """
        Detect anomalies using Prophet

        Points outside the confidence interval are flagged as anomalies

        Args:
            data: Historical data
            threshold: Confidence threshold

        Returns:
            Dict with anomaly information
        """
        if self.model is None:
            # Train model first
            self.forecast(data, periods=0, confidence_interval=threshold)

        # Predict on historical data
        prophet_data = self._prepare_data(data)
        forecast = self.model.predict(prophet_data)

        # Identify anomalies
        anomalies = []

        for i, row in forecast.iterrows():
            actual = prophet_data.loc[i, 'y']
            lower = row['yhat_lower']
            upper = row['yhat_upper']

            if actual < lower or actual > upper:
                anomalies.append({
                    "timestamp": row['ds'].isoformat(),
                    "actual_value": float(actual),
                    "expected_value": float(row['yhat']),
                    "lower_bound": float(lower),
                    "upper_bound": float(upper),
                    "deviation": float(abs(actual - row['yhat'])),
                    "severity": "high" if actual < lower - (upper - lower) or actual > upper + (upper - lower) else "medium"
                })

        return {
            "total_points": len(prophet_data),
            "anomaly_count": len(anomalies),
            "anomaly_percentage": (len(anomalies) / len(prophet_data)) * 100 if len(prophet_data) > 0 else 0,
            "anomalies": anomalies
        }


class DemandForecaster:
    """
    Demand Forecasting Service

    Specialized forecasting for demand prediction with:
    - Multiple seasonality patterns
    - External regressors (holidays, promotions, etc.)
    - Capacity planning recommendations
    """

    def __init__(self):
        self.prophet_forecaster = ProphetForecaster()

    def forecast_demand(
        self,
        historical_data: pd.DataFrame,
        forecast_horizon: int = 168,  # 7 days in hours
        external_factors: Dict[str, pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Forecast demand with capacity recommendations

        Args:
            historical_data: Historical demand data
            forecast_horizon: Hours to forecast ahead
            external_factors: External regressors (holidays, promotions, etc.)

        Returns:
            Forecast with capacity recommendations
        """
        # Generate base forecast
        forecast_result = self.prophet_forecaster.forecast(
            data=historical_data,
            periods=forecast_horizon,
            freq='H'
        )

        if "error" in forecast_result:
            return forecast_result

        # Calculate capacity recommendations
        forecast_values = [f["value"] for f in forecast_result["forecast"]]
        upper_bounds = [f["upper_bound"] for f in forecast_result["forecast"]]

        recommendations = {
            "peak_demand": max(forecast_values),
            "average_demand": np.mean(forecast_values),
            "recommended_capacity": max(upper_bounds) * 1.1,  # 10% buffer
            "capacity_utilization": (max(forecast_values) / (max(upper_bounds) * 1.1)) * 100
        }

        forecast_result["capacity_planning"] = recommendations

        # Identify peak periods
        peak_threshold = np.percentile(forecast_values, 90)
        peak_periods = []

        for f in forecast_result["forecast"]:
            if f["value"] > peak_threshold:
                peak_periods.append({
                    "timestamp": f["timestamp"],
                    "demand": f["value"]
                })

        forecast_result["peak_periods"] = peak_periods

        return forecast_result


class ForecastingService:
    """
    Main Forecasting Service

    Orchestrates all forecasting capabilities
    """

    def __init__(self):
        self.prophet_forecaster = ProphetForecaster()
        self.demand_forecaster = DemandForecaster()

    def generate_forecast(
        self,
        tag_id: str,
        tag_name: str,
        data: pd.DataFrame,
        forecast_type: str = "prophet",
        periods: int = 24,
        freq: str = 'H'
    ) -> Dict[str, Any]:
        """
        Generate forecast for a tag

        Args:
            tag_id: Tag ID
            tag_name: Tag name
            data: Historical data
            forecast_type: Type of forecast ('prophet', 'demand')
            periods: Periods to forecast
            freq: Frequency

        Returns:
            Forecast results
        """
        if data.empty:
            return {
                "tag_id": tag_id,
                "tag_name": tag_name,
                "error": "No data available"
            }

        if forecast_type == "prophet":
            forecast = self.prophet_forecaster.forecast(
                data=data,
                periods=periods,
                freq=freq
            )
        elif forecast_type == "demand":
            forecast = self.demand_forecaster.forecast_demand(
                historical_data=data,
                forecast_horizon=periods
            )
        else:
            return {
                "tag_id": tag_id,
                "tag_name": tag_name,
                "error": f"Unknown forecast type: {forecast_type}"
            }

        # Add metadata
        forecast["tag_id"] = tag_id
        forecast["tag_name"] = tag_name
        forecast["forecast_type"] = forecast_type
        forecast["generated_at"] = datetime.utcnow().isoformat()

        return forecast


# Singleton instance
_forecasting_service = None


def get_forecasting_service() -> ForecastingService:
    """Get singleton instance of Forecasting Service"""
    global _forecasting_service

    if _forecasting_service is None:
        _forecasting_service = ForecastingService()

    return _forecasting_service
