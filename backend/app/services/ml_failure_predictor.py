"""
ML Failure Prediction

Machine Learning model for predicting equipment failures.

Uses:
- Historical failure data
- Sensor readings
- Maintenance records
- Operating conditions

Predicts:
- Probability of failure in next N hours
- Estimated time to failure
- Recommended maintenance window
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import pickle
import os

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. ML predictions disabled.")

from app.models.asset import Asset
from app.models.alarm import Alarm

logger = logging.getLogger(__name__)


class MLFailurePredictor:
    """
    Machine Learning-based failure prediction.

    Features used:
    - Asset health score history
    - Alarm frequency and severity
    - Operating hours
    - Time since last maintenance
    - Environmental conditions
    """

    def __init__(self, db: AsyncSession):
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for ML predictions")

        self.db = db
        self.model_path = "ml_models/"
        self.scaler = StandardScaler()

        # Models
        self.failure_classifier = None  # Predicts if failure will occur
        self.time_to_failure_regressor = None  # Predicts when it will occur

        # Ensure model directory exists
        os.makedirs(self.model_path, exist_ok=True)

    async def train_model(
        self,
        asset_type: Optional[str] = None,
        training_days: int = 180
    ) -> Dict[str, Any]:
        """
        Train ML models using historical data.

        Args:
            asset_type: Train for specific asset type (optional)
            training_days: Days of history to use for training

        Returns:
            Training results and metrics
        """
        try:
            logger.info(f"Training ML model with {training_days} days of data")

            # Collect training data
            X_train, y_train = await self._collect_training_data(
                asset_type=asset_type,
                days=training_days
            )

            if len(X_train) < 50:
                return {
                    "status": "insufficient_data",
                    "message": "Need at least 50 training samples",
                    "samples_collected": len(X_train),
                }

            # Split data
            X_train_split, X_test, y_train_split, y_test = train_test_split(
                X_train, y_train, test_size=0.2, random_state=42
            )

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train_split)
            X_test_scaled = self.scaler.transform(X_test)

            # Train classifier (binary: will fail / won't fail)
            self.failure_classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.failure_classifier.fit(X_train_scaled, y_train_split)

            # Evaluate classifier
            train_score = self.failure_classifier.score(X_train_scaled, y_train_split)
            test_score = self.failure_classifier.score(X_test_scaled, y_test)

            # Save models
            model_name = f"failure_model_{asset_type or 'all'}_{datetime.now().strftime('%Y%m%d')}.pkl"
            self._save_model(model_name)

            logger.info(
                f"Model trained: {len(X_train)} samples, "
                f"train_score={train_score:.3f}, test_score={test_score:.3f}"
            )

            return {
                "status": "success",
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "train_accuracy": round(train_score, 3),
                "test_accuracy": round(test_score, 3),
                "model_file": model_name,
                "features_used": self._get_feature_names(),
                "trained_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise

    async def predict_failure(
        self,
        asset_id: str,
        prediction_horizon_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Predict if asset will fail in the next N hours.

        Args:
            asset_id: Asset to analyze
            prediction_horizon_hours: Prediction time window

        Returns:
            Prediction results with probability and recommendations
        """
        try:
            if not self.failure_classifier:
                # Try to load existing model
                loaded = self._load_latest_model()
                if not loaded:
                    return {
                        "status": "no_model",
                        "message": "No trained model available. Please train a model first.",
                    }

            # Get asset
            result = await self.db.execute(
                select(Asset).where(Asset.id == asset_id)
            )
            asset = result.scalar_one_or_none()

            if not asset:
                raise ValueError(f"Asset {asset_id} not found")

            # Extract features for prediction
            features = await self._extract_features(asset)

            # Scale features
            features_scaled = self.scaler.transform([features])

            # Make prediction
            failure_probability = self.failure_classifier.predict_proba(features_scaled)[0][1]
            will_fail = failure_probability > 0.5

            # Estimate time to failure if likely to fail
            estimated_hours_to_failure = None
            if will_fail:
                estimated_hours_to_failure = self._estimate_time_to_failure(
                    features,
                    prediction_horizon_hours
                )

            # Generate recommendations
            recommendations = self._generate_ml_recommendations(
                failure_probability,
                estimated_hours_to_failure,
                asset.asset_type
            )

            # Determine risk level
            if failure_probability < 0.3:
                risk_level = "low"
            elif failure_probability < 0.7:
                risk_level = "medium"
            else:
                risk_level = "high"

            return {
                "asset_id": asset_id,
                "asset_name": asset.name,
                "asset_type": asset.asset_type,
                "prediction_horizon_hours": prediction_horizon_hours,
                "failure_probability": round(failure_probability, 3),
                "will_fail": will_fail,
                "risk_level": risk_level,
                "estimated_hours_to_failure": estimated_hours_to_failure,
                "confidence": self._calculate_prediction_confidence(features),
                "recommendations": recommendations,
                "predicted_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error predicting failure: {e}")
            raise

    async def _collect_training_data(
        self,
        asset_type: Optional[str],
        days: int
    ) -> Tuple[List[List[float]], List[int]]:
        """Collect historical data for training."""
        X = []  # Features
        y = []  # Labels (1 = failure, 0 = no failure)

        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Query assets
            query = select(Asset)
            if asset_type:
                query = query.where(Asset.asset_type == asset_type)

            result = await self.db.execute(query)
            assets = result.scalars().all()

            # For each asset, create training samples
            for asset in assets:
                # Get historical alarms
                alarm_result = await self.db.execute(
                    select(Alarm).where(
                        and_(
                            Alarm.asset_id == asset.id,
                            Alarm.triggered_at >= start_date
                        )
                    ).order_by(Alarm.triggered_at)
                )
                alarms = alarm_result.scalars().all()

                # Create samples (simulate features for now)
                # In production, would use actual sensor data from InfluxDB
                for i in range(len(alarms)):
                    features = self._simulate_features_from_alarm(alarms[i], asset)
                    label = 1 if alarms[i].severity in ["critical", "high"] else 0

                    X.append(features)
                    y.append(label)

            return X, y

        except Exception as e:
            logger.error(f"Error collecting training data: {e}")
            return [], []

    def _simulate_features_from_alarm(
        self,
        alarm: Alarm,
        asset: Asset
    ) -> List[float]:
        """Simulate feature extraction (placeholder for production implementation)."""
        # In production, would extract from:
        # - InfluxDB sensor readings
        # - Asset health history
        # - Maintenance records

        return [
            float(asset.health_score or 50),  # Health score
            1.0 if alarm.severity == "critical" else 0.5,  # Severity
            0.8,  # Simulated operating hours ratio
            0.6,  # Simulated vibration level
            25.0,  # Simulated temperature
            60.0,  # Simulated load percentage
            7.0,  # Days since last maintenance (simulated)
            3.0,  # Alarm count last 24h (simulated)
        ]

    async def _extract_features(self, asset: Asset) -> List[float]:
        """Extract current features from asset for prediction."""
        # Get recent alarms
        start_date = datetime.utcnow() - timedelta(days=7)

        result = await self.db.execute(
            select(func.count(Alarm.id)).where(
                and_(
                    Alarm.asset_id == asset.id,
                    Alarm.triggered_at >= start_date
                )
            )
        )
        recent_alarm_count = result.scalar() or 0

        # Extract features (placeholder - in production would use real sensor data)
        features = [
            float(asset.health_score or 50),
            1.0 if recent_alarm_count > 5 else 0.5,
            0.8,  # Operating hours ratio
            0.6,  # Vibration level
            25.0,  # Temperature
            60.0,  # Load percentage
            7.0,  # Days since maintenance
            float(recent_alarm_count),
        ]

        return features

    def _estimate_time_to_failure(
        self,
        features: List[float],
        max_hours: int
    ) -> Optional[float]:
        """Estimate hours until failure."""
        # Simplified estimation based on health score
        health_score = features[0]

        if health_score > 70:
            return max_hours * 0.9
        elif health_score > 50:
            return max_hours * 0.5
        elif health_score > 30:
            return max_hours * 0.2
        else:
            return max_hours * 0.1

    def _calculate_prediction_confidence(self, features: List[float]) -> float:
        """Calculate confidence in prediction (0-100)."""
        # Confidence based on data quality and model certainty
        health_score = features[0]

        confidence = 60.0  # Base confidence

        # Adjust based on health score availability
        if health_score > 0:
            confidence += 20

        # Adjust based on recent data
        if features[-1] > 0:  # Has recent alarms
            confidence += 15

        return min(round(confidence, 1), 95.0)

    def _generate_ml_recommendations(
        self,
        failure_probability: float,
        estimated_hours: Optional[float],
        asset_type: Optional[str]
    ) -> List[str]:
        """Generate recommendations based on ML prediction."""
        recommendations = []

        if failure_probability > 0.7:
            recommendations.append("URGENT: Schedule immediate inspection")
            recommendations.append("Consider taking asset offline for preventive maintenance")
            if estimated_hours and estimated_hours < 12:
                recommendations.append(f"Estimated failure in ~{estimated_hours:.0f} hours")

        elif failure_probability > 0.5:
            recommendations.append("Schedule inspection within 24 hours")
            recommendations.append("Monitor asset closely for warning signs")
            recommendations.append("Prepare spare parts and maintenance crew")

        elif failure_probability > 0.3:
            recommendations.append("Increased monitoring recommended")
            recommendations.append("Review maintenance schedule")

        else:
            recommendations.append("Asset operating normally")
            recommendations.append("Continue standard monitoring")

        return recommendations

    def _get_feature_names(self) -> List[str]:
        """Get names of features used in the model."""
        return [
            "health_score",
            "alarm_severity",
            "operating_hours_ratio",
            "vibration_level",
            "temperature",
            "load_percentage",
            "days_since_maintenance",
            "recent_alarm_count",
        ]

    def _save_model(self, filename: str):
        """Save trained model to disk."""
        try:
            model_data = {
                'classifier': self.failure_classifier,
                'scaler': self.scaler,
                'feature_names': self._get_feature_names(),
                'trained_at': datetime.utcnow().isoformat(),
            }

            filepath = os.path.join(self.model_path, filename)
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)

            logger.info(f"Model saved to {filepath}")

        except Exception as e:
            logger.error(f"Error saving model: {e}")

    def _load_latest_model(self) -> bool:
        """Load the most recent trained model."""
        try:
            # Find latest model file
            model_files = [
                f for f in os.listdir(self.model_path)
                if f.startswith('failure_model_') and f.endswith('.pkl')
            ]

            if not model_files:
                logger.warning("No saved models found")
                return False

            latest_model = sorted(model_files)[-1]
            filepath = os.path.join(self.model_path, latest_model)

            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)

            self.failure_classifier = model_data['classifier']
            self.scaler = model_data['scaler']

            logger.info(f"Loaded model from {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
