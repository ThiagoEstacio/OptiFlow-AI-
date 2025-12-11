"""
Anomaly Detection Service - MELH-001
====================================

Implements Isolation Forest model for detecting anomalous behavior
in equipment using vibration, temperature, current, and power data.

Sprint 2-3 Task: MELH-001 - Modelo de Detecção de Anomalias

Features:
- Isolation Forest algorithm for unsupervised anomaly detection
- Per-equipment model training
- Real-time prediction with confidence scores
- Automatic model persistence and loading
- Feature importance analysis
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

# Optional imports for ML
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class AnomalyStatus(Enum):
    """Status of anomaly detection"""
    NORMAL = "normal"
    ANOMALY = "anomaly"
    NO_MODEL = "no_model"
    INSUFFICIENT_DATA = "insufficient_data"
    ERROR = "error"


@dataclass
class AnomalyPrediction:
    """Result of anomaly prediction"""
    status: AnomalyStatus
    score: float = 0.0
    confidence: float = 0.0
    contributing_features: List[Dict[str, Any]] = field(default_factory=list)
    recommendation: str = ""
    equipment_id: str = ""
    timestamp: str = ""
    raw_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "score": self.score,
            "confidence": self.confidence,
            "contributing_features": self.contributing_features,
            "recommendation": self.recommendation,
            "equipment_id": self.equipment_id,
            "timestamp": self.timestamp,
            "raw_scores": self.raw_scores,
            "is_anomaly": self.status == AnomalyStatus.ANOMALY
        }


@dataclass
class ModelInfo:
    """Information about a trained model"""
    equipment_id: str
    trained_at: datetime
    samples_used: int
    contamination: float
    features: List[str]
    performance_metrics: Dict[str, float] = field(default_factory=dict)


class AnomalyDetectionService:
    """
    Anomaly Detection Service using Isolation Forest.

    MELH-001: Detects anomalous equipment behavior using
    multivariate sensor data analysis.

    Key Features:
    1. Trains Isolation Forest model per equipment
    2. Uses vibration, temperature, current, power, load as features
    3. Provides confidence scores and contributing features
    4. Automatic model persistence
    """

    # Default feature columns for anomaly detection
    FEATURE_COLUMNS = [
        'vibration_mms',
        'temperature_c',
        'current_a',
        'power_kw',
        'load_pct'
    ]

    def __init__(self, model_path: str = "models/anomaly"):
        """
        Initialize Anomaly Detection Service.

        Args:
            model_path: Directory to store trained models
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available. Anomaly detection disabled.")

        self.model_path = Path(model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)

        # Stores trained models and scalers per equipment
        self._models: Dict[str, IsolationForest] = {}
        self._scalers: Dict[str, StandardScaler] = {}
        self._model_info: Dict[str, ModelInfo] = {}

        # Statistics
        self._stats = {
            "total_predictions": 0,
            "anomalies_detected": 0,
            "models_trained": 0
        }

        # Feature statistics for contribution analysis
        self._feature_stats: Dict[str, Dict[str, Tuple[float, float]]] = {}

        logger.info("🔍 AnomalyDetectionService initialized")
        logger.info(f"   Model path: {self.model_path}")
        logger.info(f"   Features: {self.FEATURE_COLUMNS}")

    async def train_model(
        self,
        equipment_id: str,
        historical_data: List[Dict[str, Any]],
        contamination: float = 0.05,
        n_estimators: int = 100
    ) -> Dict[str, Any]:
        """
        Train anomaly detection model for a specific equipment.

        Args:
            equipment_id: Unique identifier for the equipment
            historical_data: List of sensor readings with feature values
            contamination: Expected proportion of anomalies (default 5%)
            n_estimators: Number of trees in the forest

        Returns:
            Training results and metrics
        """
        if not SKLEARN_AVAILABLE:
            return {
                "status": "error",
                "message": "scikit-learn not installed"
            }

        logger.info(f"🎯 Training anomaly model for equipment: {equipment_id}")
        logger.info(f"   Samples: {len(historical_data)}")
        logger.info(f"   Contamination: {contamination}")

        # Validate minimum samples
        min_samples = 100
        if len(historical_data) < min_samples:
            return {
                "status": "insufficient_data",
                "message": f"Need at least {min_samples} samples, got {len(historical_data)}",
                "samples_provided": len(historical_data),
                "samples_required": min_samples
            }

        try:
            # Extract features from historical data
            X, valid_count = self._extract_features(historical_data)

            if valid_count < min_samples:
                return {
                    "status": "insufficient_data",
                    "message": f"Only {valid_count} valid samples after feature extraction",
                    "valid_samples": valid_count,
                    "samples_required": min_samples
                }

            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Store feature statistics for contribution analysis
            self._feature_stats[equipment_id] = {
                feature: (float(np.mean(X[:, i])), float(np.std(X[:, i])))
                for i, feature in enumerate(self.FEATURE_COLUMNS)
            }

            # Train Isolation Forest
            model = IsolationForest(
                contamination=contamination,
                n_estimators=n_estimators,
                max_samples='auto',
                random_state=42,
                n_jobs=-1,
                bootstrap=True
            )
            model.fit(X_scaled)

            # Store in memory
            self._models[equipment_id] = model
            self._scalers[equipment_id] = scaler

            # Save to disk
            self._save_model(equipment_id, model, scaler)

            # Store model info
            self._model_info[equipment_id] = ModelInfo(
                equipment_id=equipment_id,
                trained_at=datetime.now(timezone.utc),
                samples_used=valid_count,
                contamination=contamination,
                features=self.FEATURE_COLUMNS.copy()
            )

            self._stats["models_trained"] += 1

            logger.info(f"✅ Model trained for {equipment_id}")
            logger.info(f"   Samples used: {valid_count}")

            return {
                "status": "success",
                "equipment_id": equipment_id,
                "samples_trained": valid_count,
                "contamination": contamination,
                "n_estimators": n_estimators,
                "features": self.FEATURE_COLUMNS,
                "model_file": f"{equipment_id}_model.joblib",
                "trained_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error training model for {equipment_id}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "equipment_id": equipment_id
            }

    async def predict(
        self,
        equipment_id: str,
        current_readings: Dict[str, float]
    ) -> AnomalyPrediction:
        """
        Predict if current readings are anomalous.

        Args:
            equipment_id: Equipment to analyze
            current_readings: Dict with feature values

        Returns:
            AnomalyPrediction with status, score, and recommendations
        """
        self._stats["total_predictions"] += 1
        timestamp = datetime.now(timezone.utc).isoformat()

        if not SKLEARN_AVAILABLE:
            return AnomalyPrediction(
                status=AnomalyStatus.ERROR,
                recommendation="ML libraries not available",
                equipment_id=equipment_id,
                timestamp=timestamp
            )

        # Get or load model
        model = self._models.get(equipment_id)
        scaler = self._scalers.get(equipment_id)

        if model is None:
            # Try to load from disk
            loaded = self._load_model(equipment_id)
            if not loaded:
                return AnomalyPrediction(
                    status=AnomalyStatus.NO_MODEL,
                    recommendation=f"No trained model for equipment '{equipment_id}'. Train model first.",
                    equipment_id=equipment_id,
                    timestamp=timestamp
                )
            model = self._models[equipment_id]
            scaler = self._scalers[equipment_id]

        try:
            # Prepare input features
            X = np.array([[
                current_readings.get('vibration_mms', 0),
                current_readings.get('temperature_c', current_readings.get('temp_c', 0)),
                current_readings.get('current_a', 0),
                current_readings.get('power_kw', 0),
                current_readings.get('load_pct', current_readings.get('load', 0))
            ]])

            # Scale
            X_scaled = scaler.transform(X)

            # Get decision score (higher = more normal, lower = more anomalous)
            score = model.decision_function(X_scaled)[0]

            # Predict (-1 = anomaly, 1 = normal)
            prediction = model.predict(X_scaled)[0]
            is_anomaly = prediction == -1

            # Calculate confidence (0-100)
            # Score typically ranges from -0.5 to 0.5
            confidence = min(abs(score) * 100, 99.0)

            # Identify contributing features
            contributing = self._identify_contributing_features(
                current_readings,
                equipment_id
            )

            # Generate recommendation
            recommendation = self._generate_recommendation(
                is_anomaly,
                score,
                contributing
            )

            status = AnomalyStatus.ANOMALY if is_anomaly else AnomalyStatus.NORMAL

            if is_anomaly:
                self._stats["anomalies_detected"] += 1
                logger.warning(
                    f"⚠️ ANOMALY detected for {equipment_id}: "
                    f"score={score:.3f}, confidence={confidence:.1f}%"
                )

            return AnomalyPrediction(
                status=status,
                score=float(score),
                confidence=round(confidence, 1),
                contributing_features=contributing,
                recommendation=recommendation,
                equipment_id=equipment_id,
                timestamp=timestamp,
                raw_scores={
                    "decision_score": float(score),
                    "prediction": int(prediction)
                }
            )

        except Exception as e:
            logger.error(f"❌ Error predicting anomaly for {equipment_id}: {e}")
            return AnomalyPrediction(
                status=AnomalyStatus.ERROR,
                recommendation=f"Prediction error: {str(e)}",
                equipment_id=equipment_id,
                timestamp=timestamp
            )

    def _extract_features(
        self,
        data: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, int]:
        """Extract feature matrix from list of readings."""
        features = []

        for record in data:
            try:
                row = [
                    float(record.get('vibration_mms', 0) or 0),
                    float(record.get('temperature_c', record.get('temp_c', 0)) or 0),
                    float(record.get('current_a', 0) or 0),
                    float(record.get('power_kw', 0) or 0),
                    float(record.get('load_pct', record.get('load', 0)) or 0)
                ]

                # Skip rows with all zeros
                if sum(row) > 0:
                    features.append(row)
            except (ValueError, TypeError):
                continue

        return np.array(features), len(features)

    def _identify_contributing_features(
        self,
        readings: Dict[str, float],
        equipment_id: str
    ) -> List[Dict[str, Any]]:
        """
        Identify which features are contributing to anomaly.

        Uses z-score comparison against historical statistics.
        """
        stats = self._feature_stats.get(equipment_id, {})
        if not stats:
            return []

        contributing = []

        feature_mapping = {
            'vibration_mms': ('vibration_mms', readings.get('vibration_mms', 0)),
            'temperature_c': ('temperature_c', readings.get('temperature_c', readings.get('temp_c', 0))),
            'current_a': ('current_a', readings.get('current_a', 0)),
            'power_kw': ('power_kw', readings.get('power_kw', 0)),
            'load_pct': ('load_pct', readings.get('load_pct', readings.get('load', 0)))
        }

        for feature, (name, value) in feature_mapping.items():
            if feature in stats:
                mean, std = stats[feature]
                if std > 0:
                    z_score = abs((value - mean) / std)

                    if z_score > 2.0:  # More than 2 std devs from mean
                        deviation = "high" if value > mean else "low"
                        contributing.append({
                            "feature": feature,
                            "current_value": value,
                            "expected_mean": round(mean, 2),
                            "z_score": round(z_score, 2),
                            "deviation": deviation,
                            "severity": "high" if z_score > 3 else "medium"
                        })

        # Sort by z-score (most anomalous first)
        return sorted(contributing, key=lambda x: x['z_score'], reverse=True)

    def _generate_recommendation(
        self,
        is_anomaly: bool,
        score: float,
        contributing: List[Dict[str, Any]]
    ) -> str:
        """Generate recommendation based on prediction."""
        if not is_anomaly:
            return "Equipment operating within normal parameters. Continue standard monitoring."

        if not contributing:
            return "Anomaly detected. Review all sensor readings for unusual patterns."

        # Build recommendation based on contributing features
        top_feature = contributing[0]
        feature_name = top_feature['feature']
        deviation = top_feature['deviation']

        recommendations = {
            'vibration_mms': {
                'high': "High vibration detected. Check bearings, alignment, and balance. Schedule vibration analysis.",
                'low': "Unusually low vibration. Verify sensor operation and equipment coupling."
            },
            'temperature_c': {
                'high': "High temperature detected. Check cooling system, lubrication, and load conditions.",
                'low': "Low temperature detected. Verify heating systems or ambient conditions."
            },
            'current_a': {
                'high': "High current draw. Check for mechanical binding, overload, or electrical issues.",
                'low': "Low current. Verify motor load and mechanical coupling."
            },
            'power_kw': {
                'high': "High power consumption. Review process load and equipment efficiency.",
                'low': "Low power. Check if equipment is operating at designed capacity."
            },
            'load_pct': {
                'high': "High load percentage. Monitor for overload conditions.",
                'low': "Low load. Verify process requirements and equipment utilization."
            }
        }

        base_rec = recommendations.get(feature_name, {}).get(
            deviation,
            f"{feature_name} is {deviation}. Investigate cause."
        )

        # Add urgency based on score
        if score < -0.3:
            return f"URGENT: {base_rec} Immediate inspection recommended."
        elif score < -0.1:
            return f"WARNING: {base_rec} Schedule inspection within 24 hours."
        else:
            return base_rec

    def _save_model(
        self,
        equipment_id: str,
        model: 'IsolationForest',
        scaler: 'StandardScaler'
    ):
        """Save model and scaler to disk."""
        try:
            model_file = self.model_path / f"{equipment_id}_model.joblib"
            scaler_file = self.model_path / f"{equipment_id}_scaler.joblib"
            stats_file = self.model_path / f"{equipment_id}_stats.joblib"

            joblib.dump(model, model_file)
            joblib.dump(scaler, scaler_file)

            if equipment_id in self._feature_stats:
                joblib.dump(self._feature_stats[equipment_id], stats_file)

            logger.info(f"💾 Model saved: {model_file}")

        except Exception as e:
            logger.error(f"Error saving model: {e}")

    def _load_model(self, equipment_id: str) -> bool:
        """Load model and scaler from disk."""
        try:
            model_file = self.model_path / f"{equipment_id}_model.joblib"
            scaler_file = self.model_path / f"{equipment_id}_scaler.joblib"
            stats_file = self.model_path / f"{equipment_id}_stats.joblib"

            if not model_file.exists() or not scaler_file.exists():
                return False

            self._models[equipment_id] = joblib.load(model_file)
            self._scalers[equipment_id] = joblib.load(scaler_file)

            if stats_file.exists():
                self._feature_stats[equipment_id] = joblib.load(stats_file)

            logger.info(f"📂 Model loaded: {model_file}")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def get_model_status(self, equipment_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of trained models."""
        if equipment_id:
            info = self._model_info.get(equipment_id)
            if info:
                return {
                    "equipment_id": equipment_id,
                    "trained": True,
                    "trained_at": info.trained_at.isoformat(),
                    "samples_used": info.samples_used,
                    "contamination": info.contamination,
                    "features": info.features
                }
            else:
                # Check if model exists on disk
                model_file = self.model_path / f"{equipment_id}_model.joblib"
                return {
                    "equipment_id": equipment_id,
                    "trained": model_file.exists(),
                    "loaded_in_memory": equipment_id in self._models
                }

        # Return all models - include both in-memory and disk models
        models_dict = {}

        # First, add models from _model_info (fully loaded with metadata)
        for eq_id, info in self._model_info.items():
            models_dict[eq_id] = {
                "trained_at": info.trained_at.isoformat(),
                "samples_used": info.samples_used,
                "in_memory": True
            }

        # Then, add models from disk that aren't in _model_info
        for model_file in self.model_path.glob("*_model.joblib"):
            eq_id = model_file.stem.replace("_model", "")
            # Skip test models
            if eq_id.startswith("TEST"):
                continue
            if eq_id not in models_dict:
                # Get file modification time as trained_at proxy
                mtime = datetime.fromtimestamp(model_file.stat().st_mtime)
                models_dict[eq_id] = {
                    "trained_at": mtime.isoformat(),
                    "samples_used": 0,  # Unknown - not in memory
                    "in_memory": eq_id in self._models
                }

        return {
            "total_models": len(self._models),
            "models_on_disk": len(list(self.model_path.glob("*_model.joblib"))),
            "models": models_dict,
            "statistics": self._stats
        }

    def reset_statistics(self):
        """Reset prediction statistics."""
        self._stats = {
            "total_predictions": 0,
            "anomalies_detected": 0,
            "models_trained": self._stats.get("models_trained", 0)
        }
        logger.info("🔄 Anomaly detection statistics reset")


# Global singleton
_anomaly_service: Optional[AnomalyDetectionService] = None


def get_anomaly_service() -> AnomalyDetectionService:
    """Get global anomaly detection service instance."""
    global _anomaly_service
    if _anomaly_service is None:
        _anomaly_service = AnomalyDetectionService()
    return _anomaly_service
