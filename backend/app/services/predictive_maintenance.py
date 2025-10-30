"""
Predictive Maintenance Service

Predicts equipment failures and estimates Remaining Useful Life (RUL):
- Failure prediction using XGBoost/RandomForest
- RUL estimation
- Risk scoring
- Maintenance recommendations
- Feature engineering from sensor data
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Feature Engineering for Predictive Maintenance

    Extracts meaningful features from raw sensor data
    """

    @staticmethod
    def engineer_features(data: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer features from sensor data

        Expected columns: temperature, vibration, pressure, etc.

        Args:
            data: Raw sensor data

        Returns:
            DataFrame with engineered features
        """
        features = pd.DataFrame()

        # Statistical features for each sensor
        for col in data.columns:
            if col == 'timestamp':
                continue

            # Rolling window statistics (last hour)
            window = 60  # 60 minutes

            if len(data) >= window:
                features[f'{col}_mean'] = data[col].rolling(window=window, min_periods=1).mean()
                features[f'{col}_std'] = data[col].rolling(window=window, min_periods=1).std()
                features[f'{col}_max'] = data[col].rolling(window=window, min_periods=1).max()
                features[f'{col}_min'] = data[col].rolling(window=window, min_periods=1).min()
                features[f'{col}_range'] = features[f'{col}_max'] - features[f'{col}_min']

                # Rate of change
                features[f'{col}_roc'] = data[col].diff()
                features[f'{col}_roc_std'] = features[f'{col}_roc'].rolling(window=window, min_periods=1).std()
            else:
                # If not enough data, use basic stats
                features[f'{col}_mean'] = data[col].mean()
                features[f'{col}_std'] = data[col].std()
                features[f'{col}_max'] = data[col].max()
                features[f'{col}_min'] = data[col].min()

        # Operating time features
        if 'runtime_hours' in data.columns:
            features['runtime_hours'] = data['runtime_hours']
            features['runtime_squared'] = data['runtime_hours'] ** 2

        if 'cycles_count' in data.columns:
            features['cycles_count'] = data['cycles_count']

        # Fill NaN values
        features = features.fillna(0)

        return features


class RULEstimator:
    """
    Remaining Useful Life (RUL) Estimator

    Estimates how long equipment can operate before failure
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.model = None
        self.is_trained = False

    def train(
        self,
        training_data: pd.DataFrame,
        features: List[str],
        target: str = 'rul'
    ):
        """
        Train RUL estimation model

        Args:
            training_data: Historical data with RUL labels
            features: Feature columns
            target: Target column (RUL in hours/days)
        """
        from sklearn.ensemble import RandomForestRegressor

        X = training_data[features].values
        y = training_data[target].values

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train Random Forest regressor
        self.model = RandomForestRegressor(
            n_estimators=200,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )

        self.model.fit(X_scaled, y)
        self.is_trained = True

        logger.info(f"RUL model trained with {len(X)} samples")

    def estimate_rul(
        self,
        features: pd.DataFrame
    ) -> Tuple[float, float]:
        """
        Estimate RUL for current equipment state

        Args:
            features: Current feature values

        Returns:
            Tuple of (rul_hours, confidence)
        """
        if not self.is_trained:
            logger.warning("RUL model not trained")
            return 0.0, 0.0

        # Scale features
        X = features.values.reshape(1, -1)
        X_scaled = self.scaler.transform(X)

        # Predict RUL
        rul_prediction = self.model.predict(X_scaled)[0]

        # Estimate confidence from tree variance
        if hasattr(self.model, 'estimators_'):
            predictions = np.array([tree.predict(X_scaled)[0] for tree in self.model.estimators_])
            std = np.std(predictions)
            confidence = 1.0 / (1.0 + std)  # Higher confidence for lower variance
        else:
            confidence = 0.5

        return float(max(0, rul_prediction)), float(confidence)


class FailurePredictor:
    """
    Equipment Failure Predictor

    Predicts probability of failure in different time windows
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.model = None
        self.is_trained = False
        self.feature_names = []

    def train(
        self,
        training_data: pd.DataFrame,
        features: List[str],
        target: str = 'failure'
    ):
        """
        Train failure prediction model

        Args:
            training_data: Historical data with failure labels
            features: Feature columns
            target: Target column (0/1 for no failure/failure)
        """
        try:
            import xgboost as xgb
        except ImportError:
            logger.warning("XGBoost not installed, using RandomForest instead")
            from sklearn.ensemble import RandomForestClassifier
            use_xgboost = False
        else:
            use_xgboost = True

        self.feature_names = features
        X = training_data[features].values
        y = training_data[target].values

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train classifier
        if use_xgboost:
            self.model = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )
        else:
            from sklearn.ensemble import RandomForestClassifier
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )

        self.model.fit(X_scaled, y)
        self.is_trained = True

        logger.info(f"Failure prediction model trained with {len(X)} samples")

    def predict_failure(
        self,
        features: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Predict failure probability

        Args:
            features: Current feature values

        Returns:
            Dict with failure prediction
        """
        if not self.is_trained:
            logger.warning("Failure prediction model not trained")
            return {
                "failure_probability": 0.0,
                "risk_level": "unknown",
                "confidence": 0.0
            }

        # Scale features
        X = features.values.reshape(1, -1)
        X_scaled = self.scaler.transform(X)

        # Predict
        failure_prob = self.model.predict_proba(X_scaled)[0][1]  # Probability of failure
        prediction = self.model.predict(X_scaled)[0]

        # Determine risk level
        if failure_prob >= 0.7:
            risk_level = "high"
        elif failure_prob >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "failure_probability": float(failure_prob),
            "will_fail": bool(prediction == 1),
            "risk_level": risk_level,
            "confidence": float(max(failure_prob, 1 - failure_prob))
        }


class PredictiveMaintenanceService:
    """
    Main Predictive Maintenance Service

    Orchestrates all predictive maintenance capabilities
    """

    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.rul_estimator = RULEstimator()
        self.failure_predictor = FailurePredictor()

    def analyze_equipment(
        self,
        equipment_id: str,
        equipment_name: str,
        sensor_data: pd.DataFrame,
        include_rul: bool = True,
        include_failure_prediction: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive equipment health analysis

        Args:
            equipment_id: Equipment ID
            equipment_name: Equipment name
            sensor_data: Recent sensor data
            include_rul: Include RUL estimation
            include_failure_prediction: Include failure prediction

        Returns:
            Analysis results
        """
        if sensor_data.empty:
            return {
                "equipment_id": equipment_id,
                "equipment_name": equipment_name,
                "error": "No sensor data available"
            }

        results = {
            "equipment_id": equipment_id,
            "equipment_name": equipment_name,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "data_points": len(sensor_data)
        }

        # Engineer features
        try:
            features = self.feature_engineer.engineer_features(sensor_data)

            # Use latest features for prediction
            latest_features = features.iloc[-1:] if len(features) > 0 else features

            # RUL estimation
            if include_rul and self.rul_estimator.is_trained:
                rul_hours, rul_confidence = self.rul_estimator.estimate_rul(latest_features)

                results["remaining_useful_life"] = {
                    "hours": rul_hours,
                    "days": rul_hours / 24,
                    "confidence": rul_confidence,
                    "estimated_failure_date": (datetime.utcnow() + timedelta(hours=rul_hours)).isoformat()
                }

            # Failure prediction
            if include_failure_prediction and self.failure_predictor.is_trained:
                failure_prediction = self.failure_predictor.predict_failure(latest_features)
                results["failure_prediction"] = failure_prediction

            # Maintenance recommendations
            results["recommendations"] = self._generate_recommendations(results)

            # Health score (0-100)
            results["health_score"] = self._calculate_health_score(results)

        except Exception as e:
            logger.error(f"Error analyzing equipment: {e}")
            results["error"] = str(e)

        return results

    def _calculate_health_score(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate overall equipment health score (0-100)

        Args:
            analysis: Analysis results

        Returns:
            Health score
        """
        base_score = 100.0

        # Penalize based on failure probability
        if "failure_prediction" in analysis:
            failure_prob = analysis["failure_prediction"].get("failure_probability", 0)
            base_score -= failure_prob * 50  # Up to -50 points

        # Penalize based on low RUL
        if "remaining_useful_life" in analysis:
            rul_days = analysis["remaining_useful_life"].get("days", 365)

            if rul_days < 7:
                base_score -= 30
            elif rul_days < 30:
                base_score -= 20
            elif rul_days < 90:
                base_score -= 10

        return max(0, min(100, base_score))

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate maintenance recommendations

        Args:
            analysis: Analysis results

        Returns:
            List of recommendations
        """
        recommendations = []

        # Based on failure risk
        if "failure_prediction" in analysis:
            risk_level = analysis["failure_prediction"].get("risk_level", "low")

            if risk_level == "high":
                recommendations.append({
                    "priority": "urgent",
                    "action": "Schedule immediate inspection",
                    "reason": "High probability of failure detected"
                })
            elif risk_level == "medium":
                recommendations.append({
                    "priority": "high",
                    "action": "Schedule inspection within 48 hours",
                    "reason": "Moderate failure risk detected"
                })

        # Based on RUL
        if "remaining_useful_life" in analysis:
            rul_days = analysis["remaining_useful_life"].get("days", 365)

            if rul_days < 7:
                recommendations.append({
                    "priority": "urgent",
                    "action": "Plan equipment replacement or major maintenance",
                    "reason": f"Estimated failure in {rul_days:.1f} days"
                })
            elif rul_days < 30:
                recommendations.append({
                    "priority": "high",
                    "action": "Order spare parts and schedule maintenance window",
                    "reason": f"Estimated failure in {rul_days:.1f} days"
                })

        # Based on health score
        health_score = self._calculate_health_score(analysis)

        if health_score < 50:
            recommendations.append({
                "priority": "urgent",
                "action": "Comprehensive equipment diagnostics required",
                "reason": f"Poor health score: {health_score:.0f}/100"
            })

        return recommendations

    def batch_analyze(
        self,
        equipment_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple equipment in batch

        Args:
            equipment_list: List of equipment with sensor data

        Returns:
            List of analysis results
        """
        results = []

        for equipment in equipment_list:
            analysis = self.analyze_equipment(
                equipment_id=equipment["id"],
                equipment_name=equipment["name"],
                sensor_data=equipment["sensor_data"]
            )

            results.append(analysis)

        return results

    def get_maintenance_schedule(
        self,
        equipment_analyses: List[Dict[str, Any]],
        days_ahead: int = 30
    ) -> Dict[str, Any]:
        """
        Generate maintenance schedule based on analyses

        Args:
            equipment_analyses: List of equipment analyses
            days_ahead: Planning horizon in days

        Returns:
            Maintenance schedule
        """
        schedule = {
            "urgent": [],
            "high_priority": [],
            "medium_priority": [],
            "low_priority": []
        }

        for analysis in equipment_analyses:
            equipment_id = analysis.get("equipment_id")
            equipment_name = analysis.get("equipment_name")

            # Check RUL
            if "remaining_useful_life" in analysis:
                rul_days = analysis["remaining_useful_life"].get("days", 365)

                if rul_days < 7:
                    schedule["urgent"].append({
                        "equipment_id": equipment_id,
                        "equipment_name": equipment_name,
                        "rul_days": rul_days,
                        "health_score": analysis.get("health_score", 0)
                    })
                elif rul_days < 30:
                    schedule["high_priority"].append({
                        "equipment_id": equipment_id,
                        "equipment_name": equipment_name,
                        "rul_days": rul_days,
                        "health_score": analysis.get("health_score", 0)
                    })

            # Check failure risk
            if "failure_prediction" in analysis:
                risk_level = analysis["failure_prediction"].get("risk_level", "low")

                if risk_level == "high" and equipment_id not in [e["equipment_id"] for e in schedule["urgent"]]:
                    schedule["urgent"].append({
                        "equipment_id": equipment_id,
                        "equipment_name": equipment_name,
                        "risk_level": risk_level,
                        "health_score": analysis.get("health_score", 0)
                    })

        # Sort by priority
        for priority in schedule:
            schedule[priority] = sorted(
                schedule[priority],
                key=lambda x: x.get("health_score", 0)
            )

        return schedule


# Singleton instance
_predictive_maintenance_service = None


def get_predictive_maintenance_service() -> PredictiveMaintenanceService:
    """Get singleton instance of Predictive Maintenance Service"""
    global _predictive_maintenance_service

    if _predictive_maintenance_service is None:
        _predictive_maintenance_service = PredictiveMaintenanceService()

    return _predictive_maintenance_service
