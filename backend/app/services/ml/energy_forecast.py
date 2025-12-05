"""
Energy Forecast Service - MELH-002
==================================

Implements LSTM model for predicting energy consumption.

Sprint 2-3 Task: MELH-002 - Previsão de Consumo de Energia

Replaces Math.random() with real ML predictions for:
- Next 24 hours hourly consumption forecast
- Monthly consumption projection
- Confidence intervals

Features:
- LSTM neural network for time series prediction
- Automatic model training and retraining
- Confidence calculation based on prediction horizon
- Model persistence with versioning
"""

import logging
import os
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

import numpy as np

# Optional imports for deep learning
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from sklearn.preprocessing import MinMaxScaler
    import joblib
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

logger = logging.getLogger(__name__)


class ForecastStatus(Enum):
    """Status of energy forecast"""
    SUCCESS = "success"
    NO_MODEL = "no_model"
    INSUFFICIENT_DATA = "insufficient_data"
    ERROR = "error"


@dataclass
class HourlyPrediction:
    """Single hour prediction"""
    hour: int
    timestamp: str
    predicted_kwh: float
    confidence: float
    lower_bound: float
    upper_bound: float


@dataclass
class EnergyForecast:
    """Complete energy forecast result"""
    status: ForecastStatus
    predictions: List[HourlyPrediction] = field(default_factory=list)
    daily_total_kwh: float = 0.0
    monthly_projection_kwh: float = 0.0
    mape: Optional[float] = None
    model_version: str = ""
    trained_at: str = ""
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "predictions": [
                {
                    "hour": p.hour,
                    "timestamp": p.timestamp,
                    "predicted_kwh": round(p.predicted_kwh, 2),
                    "confidence": round(p.confidence, 1),
                    "lower_bound": round(p.lower_bound, 2),
                    "upper_bound": round(p.upper_bound, 2)
                }
                for p in self.predictions
            ],
            "daily_total_kwh": round(self.daily_total_kwh, 2),
            "monthly_projection_kwh": round(self.monthly_projection_kwh, 2),
            "mape": round(self.mape, 2) if self.mape else None,
            "model_version": self.model_version,
            "trained_at": self.trained_at,
            "has_model": self.status != ForecastStatus.NO_MODEL,
            "message": self.message
        }


class EnergyForecastService:
    """
    Energy Forecast Service using LSTM.

    MELH-002: Predicts energy consumption using deep learning
    to replace the Math.random() fallback in the frontend.

    Key Features:
    1. LSTM network for sequence prediction
    2. 24-hour ahead forecasting
    3. Confidence intervals with decreasing confidence
    4. Monthly consumption projection
    """

    SEQUENCE_LENGTH = 24  # Use 24 hours of history
    FORECAST_HORIZON = 24  # Predict next 24 hours

    def __init__(self, model_path: str = "models/energy"):
        """
        Initialize Energy Forecast Service.

        Args:
            model_path: Directory to store trained models
        """
        self.model_path = Path(model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)

        self.model = None
        self.scaler = MinMaxScaler() if TF_AVAILABLE else None
        self.model_version = ""
        self.trained_at = ""
        self.last_mape = None

        # Statistics
        self._stats = {
            "total_predictions": 0,
            "trainings_completed": 0
        }

        if not TF_AVAILABLE:
            logger.warning("TensorFlow not available. Energy forecast using fallback.")
        else:
            # Configure TensorFlow for minimal memory usage
            tf.get_logger().setLevel('ERROR')
            gpus = tf.config.experimental.list_physical_devices('GPU')
            if gpus:
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)

        logger.info("⚡ EnergyForecastService initialized")
        logger.info(f"   Model path: {self.model_path}")
        logger.info(f"   Sequence length: {self.SEQUENCE_LENGTH}")
        logger.info(f"   Forecast horizon: {self.FORECAST_HORIZON}")

    def _build_model(self) -> 'Sequential':
        """Build LSTM model architecture."""
        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=(self.SEQUENCE_LENGTH, 1)),
            Dropout(0.2),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(self.FORECAST_HORIZON)
        ])

        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )

        return model

    async def train(
        self,
        historical_data: List[Dict[str, Any]],
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train LSTM model with historical consumption data.

        Args:
            historical_data: List of hourly consumption readings
            epochs: Training epochs (default 50)
            batch_size: Batch size (default 32)
            validation_split: Validation split (default 0.2)

        Returns:
            Training results including metrics
        """
        if not TF_AVAILABLE:
            return {
                "status": "error",
                "message": "TensorFlow not installed"
            }

        logger.info(f"🎯 Training energy forecast model")
        logger.info(f"   Samples: {len(historical_data)}")

        # Minimum data requirement
        min_samples = self.SEQUENCE_LENGTH * 10  # At least 10 sequences
        if len(historical_data) < min_samples:
            return {
                "status": "insufficient_data",
                "message": f"Need at least {min_samples} samples, got {len(historical_data)}",
                "samples_provided": len(historical_data),
                "samples_required": min_samples
            }

        try:
            # Extract consumption values
            consumption = np.array([
                float(d.get('consumption_kwh', d.get('kwh', d.get('value', 0))))
                for d in historical_data
            ]).reshape(-1, 1)

            # Scale data
            consumption_scaled = self.scaler.fit_transform(consumption)

            # Create sequences
            X, y = self._create_sequences(consumption_scaled)

            if len(X) < 10:
                return {
                    "status": "insufficient_data",
                    "message": f"Could only create {len(X)} sequences, need at least 10"
                }

            # Build and train model
            self.model = self._build_model()

            callbacks = [
                EarlyStopping(patience=10, restore_best_weights=True),
                ReduceLROnPlateau(factor=0.5, patience=5, min_lr=1e-6)
            ]

            history = self.model.fit(
                X, y,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=validation_split,
                callbacks=callbacks,
                verbose=0
            )

            # Calculate MAPE on validation set
            val_start = int(len(X) * (1 - validation_split))
            X_val = X[val_start:]
            y_val = y[val_start:]

            predictions = self.model.predict(X_val, verbose=0)
            mape = self._calculate_mape(y_val, predictions)

            # Save model
            self.model_version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            self.trained_at = datetime.now(timezone.utc).isoformat()
            self.last_mape = mape
            self._save_model()

            self._stats["trainings_completed"] += 1

            logger.info(f"✅ Model trained successfully")
            logger.info(f"   MAPE: {mape:.2f}%")
            logger.info(f"   Sequences used: {len(X)}")

            return {
                "status": "success",
                "samples_used": len(historical_data),
                "sequences_created": len(X),
                "epochs_run": len(history.history['loss']),
                "final_loss": float(history.history['loss'][-1]),
                "val_loss": float(history.history['val_loss'][-1]) if 'val_loss' in history.history else None,
                "mape": round(mape, 2),
                "model_version": self.model_version,
                "trained_at": self.trained_at
            }

        except Exception as e:
            logger.error(f"❌ Error training model: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def predict(
        self,
        recent_consumption: Optional[List[float]] = None
    ) -> EnergyForecast:
        """
        Generate 24-hour energy consumption forecast.

        Args:
            recent_consumption: Optional list of last 24 hours consumption.
                               If not provided, uses simulated data.

        Returns:
            EnergyForecast with hourly predictions
        """
        self._stats["total_predictions"] += 1

        # Check if model is available
        if self.model is None:
            loaded = self._load_model()
            if not loaded:
                # Return fallback predictions (NOT Math.random!)
                return self._generate_statistical_forecast(recent_consumption)

        if not TF_AVAILABLE:
            return self._generate_statistical_forecast(recent_consumption)

        try:
            # Get or generate input sequence
            if recent_consumption is None or len(recent_consumption) < self.SEQUENCE_LENGTH:
                recent_consumption = self._get_typical_daily_pattern()

            # Ensure correct length
            if len(recent_consumption) > self.SEQUENCE_LENGTH:
                recent_consumption = recent_consumption[-self.SEQUENCE_LENGTH:]
            elif len(recent_consumption) < self.SEQUENCE_LENGTH:
                # Pad with mean
                mean_val = np.mean(recent_consumption) if recent_consumption else 100.0
                padding = [mean_val] * (self.SEQUENCE_LENGTH - len(recent_consumption))
                recent_consumption = padding + list(recent_consumption)

            # Prepare input
            X = np.array(recent_consumption).reshape(-1, 1)
            X_scaled = self.scaler.transform(X)
            X_input = X_scaled.reshape(1, self.SEQUENCE_LENGTH, 1)

            # Predict
            predictions_scaled = self.model.predict(X_input, verbose=0)[0]

            # Inverse scale
            predictions = self.scaler.inverse_transform(
                predictions_scaled.reshape(-1, 1)
            ).flatten()

            # Generate hourly predictions with confidence intervals
            now = datetime.now(timezone.utc)
            hourly_predictions = []

            for i, pred in enumerate(predictions):
                # Confidence decreases with horizon
                base_confidence = 95.0
                decay = 1.5 * i  # Decrease ~1.5% per hour
                confidence = max(50.0, base_confidence - decay)

                # Calculate bounds based on historical variability
                std_factor = 0.1 * (1 + i * 0.05)  # Increase uncertainty
                lower = pred * (1 - std_factor)
                upper = pred * (1 + std_factor)

                hourly_predictions.append(HourlyPrediction(
                    hour=i,
                    timestamp=(now + timedelta(hours=i)).isoformat(),
                    predicted_kwh=float(pred),
                    confidence=confidence,
                    lower_bound=float(lower),
                    upper_bound=float(upper)
                ))

            # Calculate totals
            daily_total = sum(predictions)
            # Monthly projection: daily average * days in month
            monthly_projection = daily_total * 30

            return EnergyForecast(
                status=ForecastStatus.SUCCESS,
                predictions=hourly_predictions,
                daily_total_kwh=float(daily_total),
                monthly_projection_kwh=float(monthly_projection),
                mape=self.last_mape,
                model_version=self.model_version,
                trained_at=self.trained_at
            )

        except Exception as e:
            logger.error(f"❌ Prediction error: {e}")
            return EnergyForecast(
                status=ForecastStatus.ERROR,
                message=str(e)
            )

    def _create_sequences(
        self,
        data: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Create input/output sequences for training."""
        X, y = [], []

        for i in range(len(data) - self.SEQUENCE_LENGTH - self.FORECAST_HORIZON + 1):
            X.append(data[i:i + self.SEQUENCE_LENGTH])
            y.append(data[i + self.SEQUENCE_LENGTH:i + self.SEQUENCE_LENGTH + self.FORECAST_HORIZON].flatten())

        return np.array(X), np.array(y)

    def _calculate_mape(self, actual: np.ndarray, predicted: np.ndarray) -> float:
        """Calculate Mean Absolute Percentage Error."""
        # Avoid division by zero
        mask = actual != 0
        if not np.any(mask):
            return 0.0

        mape = np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100
        return float(mape)

    def _generate_statistical_forecast(
        self,
        recent_data: Optional[List[float]] = None
    ) -> EnergyForecast:
        """
        Generate forecast using statistical methods (fallback).

        This replaces Math.random() with actual statistical modeling:
        - Uses typical daily consumption pattern
        - Adds variability based on historical patterns
        - NOT random!
        """
        logger.info("Using statistical forecast (no LSTM model available)")

        # Get typical pattern
        pattern = self._get_typical_daily_pattern()

        # If we have recent data, adjust pattern to match
        if recent_data and len(recent_data) >= 6:
            recent_mean = np.mean(recent_data[-6:])
            pattern_mean = np.mean(pattern)
            if pattern_mean > 0:
                scale_factor = recent_mean / pattern_mean
                pattern = [p * scale_factor for p in pattern]

        # Generate predictions with confidence intervals
        now = datetime.now(timezone.utc)
        hourly_predictions = []

        for i, base_pred in enumerate(pattern):
            # Add deterministic variation based on hour
            hour_of_day = (now.hour + i) % 24

            # Confidence decreases with horizon
            confidence = max(60.0, 90.0 - i * 1.2)

            # Bounds based on typical variability
            std_factor = 0.15 * (1 + i * 0.03)
            lower = base_pred * (1 - std_factor)
            upper = base_pred * (1 + std_factor)

            hourly_predictions.append(HourlyPrediction(
                hour=i,
                timestamp=(now + timedelta(hours=i)).isoformat(),
                predicted_kwh=float(base_pred),
                confidence=confidence,
                lower_bound=float(lower),
                upper_bound=float(upper)
            ))

        daily_total = sum(pattern)
        monthly_projection = daily_total * 30

        return EnergyForecast(
            status=ForecastStatus.NO_MODEL,
            predictions=hourly_predictions,
            daily_total_kwh=float(daily_total),
            monthly_projection_kwh=float(monthly_projection),
            message="Using statistical forecast - train LSTM for better accuracy"
        )

    def _get_typical_daily_pattern(self) -> List[float]:
        """
        Return typical industrial energy consumption pattern.

        Based on typical industrial operations:
        - Lower consumption at night (22:00 - 06:00)
        - Ramp up in morning (06:00 - 08:00)
        - Peak during day shift (08:00 - 17:00)
        - Ramp down evening (17:00 - 22:00)
        """
        # Base consumption in kWh for a medium industrial facility
        base = 150.0

        # Hourly multipliers representing typical pattern
        pattern_multipliers = [
            0.6,   # 00:00 - Night shift (reduced)
            0.55,  # 01:00
            0.55,  # 02:00
            0.55,  # 03:00
            0.55,  # 04:00
            0.6,   # 05:00 - Start ramping up
            0.75,  # 06:00 - Morning shift starts
            0.9,   # 07:00
            1.0,   # 08:00 - Peak production
            1.05,  # 09:00
            1.1,   # 10:00
            1.05,  # 11:00
            0.95,  # 12:00 - Lunch break
            1.0,   # 13:00
            1.05,  # 14:00
            1.0,   # 15:00
            0.95,  # 16:00 - Start winding down
            0.85,  # 17:00 - Day shift ends
            0.75,  # 18:00
            0.7,   # 19:00
            0.65,  # 20:00
            0.6,   # 21:00
            0.55,  # 22:00
            0.55,  # 23:00
        ]

        # Generate 24-hour pattern
        now = datetime.now(timezone.utc)
        start_hour = now.hour

        pattern = []
        for i in range(24):
            hour = (start_hour + i) % 24
            multiplier = pattern_multipliers[hour]

            # Add small deterministic variation (NOT random!)
            # Based on day of year for seasonality
            day_factor = 1.0 + 0.05 * np.sin(now.timetuple().tm_yday / 365.0 * 2 * np.pi)

            consumption = base * multiplier * day_factor
            pattern.append(consumption)

        return pattern

    def _save_model(self):
        """Save model, scaler, and metadata."""
        if not TF_AVAILABLE or self.model is None:
            return

        try:
            model_file = self.model_path / f"energy_lstm_{self.model_version}.h5"
            scaler_file = self.model_path / f"energy_scaler_{self.model_version}.joblib"
            meta_file = self.model_path / "latest_model.txt"

            self.model.save(str(model_file))
            joblib.dump(self.scaler, scaler_file)

            # Save reference to latest model
            with open(meta_file, 'w') as f:
                f.write(self.model_version)

            logger.info(f"💾 Model saved: {model_file}")

        except Exception as e:
            logger.error(f"Error saving model: {e}")

    def _load_model(self) -> bool:
        """Load latest trained model."""
        if not TF_AVAILABLE:
            return False

        try:
            meta_file = self.model_path / "latest_model.txt"

            if not meta_file.exists():
                return False

            with open(meta_file, 'r') as f:
                version = f.read().strip()

            model_file = self.model_path / f"energy_lstm_{version}.h5"
            scaler_file = self.model_path / f"energy_scaler_{version}.joblib"

            if not model_file.exists() or not scaler_file.exists():
                return False

            self.model = load_model(str(model_file), compile=False)
            self.model.compile(optimizer='adam', loss='mse', metrics=['mae'])
            self.scaler = joblib.load(scaler_file)
            self.model_version = version

            logger.info(f"📂 Model loaded: {model_file}")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            "tensorflow_available": TF_AVAILABLE,
            "model_loaded": self.model is not None,
            "model_version": self.model_version,
            "trained_at": self.trained_at,
            "last_mape": self.last_mape,
            "sequence_length": self.SEQUENCE_LENGTH,
            "forecast_horizon": self.FORECAST_HORIZON,
            "statistics": self._stats
        }


# Global singleton
_energy_service: Optional[EnergyForecastService] = None


def get_energy_forecast_service() -> EnergyForecastService:
    """Get global energy forecast service instance."""
    global _energy_service
    if _energy_service is None:
        _energy_service = EnergyForecastService()
    return _energy_service
