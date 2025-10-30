"""
AI Insights Service

Provides intelligent insights from industrial process data:
- Anomaly detection (Isolation Forest)
- Automated insight generation
- Pattern recognition
- Predictive maintenance scoring
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Anomaly Detection using Isolation Forest

    Detects unusual behavior in process variables using unsupervised learning
    """

    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        """
        Initialize anomaly detector

        Args:
            contamination: Expected proportion of outliers (0.0 to 0.5)
            random_state: Random seed for reproducibility
        """
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100,
            max_samples='auto',
            max_features=1.0,
            bootstrap=False
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_names = []

    def fit(self, data: pd.DataFrame, features: List[str]) -> None:
        """
        Fit the anomaly detection model

        Args:
            data: DataFrame with process data
            features: List of feature column names to use
        """
        self.feature_names = features
        X = data[features].dropna()

        if len(X) < 10:
            logger.warning("Insufficient data for anomaly detection training")
            return

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Fit model
        self.model.fit(X_scaled)
        self.is_fitted = True

        logger.info(f"Anomaly detector fitted with {len(X)} samples and {len(features)} features")

    def predict(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict anomalies in new data

        Args:
            data: DataFrame with process data

        Returns:
            Tuple of (predictions, anomaly_scores)
            predictions: 1 for normal, -1 for anomaly
            anomaly_scores: Anomaly score (more negative = more anomalous)
        """
        if not self.is_fitted:
            logger.warning("Model not fitted yet")
            return np.array([]), np.array([])

        X = data[self.feature_names].dropna()

        if len(X) == 0:
            return np.array([]), np.array([])

        # Scale features
        X_scaled = self.scaler.transform(X)

        # Predict
        predictions = self.model.predict(X_scaled)
        scores = self.model.score_samples(X_scaled)

        return predictions, scores

    def get_anomaly_percentage(self, data: pd.DataFrame) -> float:
        """Calculate percentage of anomalous points"""
        predictions, _ = self.predict(data)

        if len(predictions) == 0:
            return 0.0

        anomaly_count = np.sum(predictions == -1)
        return (anomaly_count / len(predictions)) * 100


class InsightGenerator:
    """
    Automated Insight Generation

    Generates human-readable insights from process data
    """

    @staticmethod
    def detect_trend(values: np.ndarray, threshold: float = 0.1) -> Dict[str, Any]:
        """
        Detect trend in time series data

        Args:
            values: Array of values
            threshold: Minimum slope to consider as trend

        Returns:
            Dict with trend information
        """
        if len(values) < 2:
            return {"trend": "insufficient_data"}

        # Linear regression for trend
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)

        # Normalize slope by value range
        value_range = np.ptp(values)
        if value_range > 0:
            normalized_slope = slope / value_range
        else:
            normalized_slope = 0

        if abs(normalized_slope) < threshold:
            trend = "stable"
        elif normalized_slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"

        return {
            "trend": trend,
            "slope": float(slope),
            "normalized_slope": float(normalized_slope),
            "change_rate": float(normalized_slope * 100)  # Percentage
        }

    @staticmethod
    def detect_outliers_zscore(values: np.ndarray, threshold: float = 3.0) -> Dict[str, Any]:
        """
        Detect outliers using Z-score method

        Args:
            values: Array of values
            threshold: Z-score threshold

        Returns:
            Dict with outlier information
        """
        if len(values) < 3:
            return {"outlier_count": 0, "outlier_percentage": 0.0}

        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return {"outlier_count": 0, "outlier_percentage": 0.0}

        z_scores = np.abs((values - mean) / std)
        outliers = z_scores > threshold

        return {
            "outlier_count": int(np.sum(outliers)),
            "outlier_percentage": float(np.sum(outliers) / len(values) * 100),
            "max_zscore": float(np.max(z_scores))
        }

    @staticmethod
    def detect_level_shift(values: np.ndarray, window: int = 10) -> Dict[str, Any]:
        """
        Detect sudden level shifts in data

        Args:
            values: Array of values
            window: Window size for comparison

        Returns:
            Dict with level shift information
        """
        if len(values) < window * 2:
            return {"level_shift_detected": False}

        # Compare recent window with previous window
        recent_mean = np.mean(values[-window:])
        previous_mean = np.mean(values[-2*window:-window])

        if previous_mean == 0:
            return {"level_shift_detected": False}

        change_percent = ((recent_mean - previous_mean) / abs(previous_mean)) * 100

        # Threshold: 10% change
        level_shift = abs(change_percent) > 10

        return {
            "level_shift_detected": bool(level_shift),
            "change_percent": float(change_percent),
            "previous_mean": float(previous_mean),
            "recent_mean": float(recent_mean)
        }

    @staticmethod
    def compare_to_baseline(current_value: float, baseline_mean: float, baseline_std: float) -> Dict[str, Any]:
        """
        Compare current value to baseline statistics

        Args:
            current_value: Current value to compare
            baseline_mean: Baseline mean
            baseline_std: Baseline standard deviation

        Returns:
            Dict with comparison information
        """
        if baseline_std == 0:
            deviation = 0
            status = "normal"
        else:
            deviation = (current_value - baseline_mean) / baseline_std

            if abs(deviation) > 3:
                status = "critical"
            elif abs(deviation) > 2:
                status = "warning"
            else:
                status = "normal"

        percent_diff = 0 if baseline_mean == 0 else ((current_value - baseline_mean) / abs(baseline_mean)) * 100

        return {
            "status": status,
            "deviation": float(deviation),
            "percent_difference": float(percent_diff),
            "baseline_mean": float(baseline_mean),
            "baseline_std": float(baseline_std),
            "current_value": float(current_value)
        }

    @staticmethod
    def generate_insight_message(tag_name: str, insight_type: str, data: Dict[str, Any]) -> str:
        """
        Generate human-readable insight message

        Args:
            tag_name: Name of the tag
            insight_type: Type of insight
            data: Insight data

        Returns:
            Human-readable message
        """
        if insight_type == "trend":
            trend = data.get("trend", "unknown")
            change_rate = data.get("change_rate", 0)

            if trend == "increasing":
                return f"📈 {tag_name} is trending upward ({abs(change_rate):.1f}% increase over time)"
            elif trend == "decreasing":
                return f"📉 {tag_name} is trending downward ({abs(change_rate):.1f}% decrease over time)"
            else:
                return f"➡️ {tag_name} is stable"

        elif insight_type == "outlier":
            count = data.get("outlier_count", 0)
            percentage = data.get("outlier_percentage", 0)

            if count > 0:
                return f"⚠️ {tag_name} has {count} outlier(s) detected ({percentage:.1f}% of data)"
            else:
                return f"✅ {tag_name} has no outliers"

        elif insight_type == "level_shift":
            if data.get("level_shift_detected", False):
                change = data.get("change_percent", 0)
                direction = "increased" if change > 0 else "decreased"
                return f"🔄 {tag_name} {direction} by {abs(change):.1f}% - possible setpoint change or process shift"
            else:
                return f"➡️ {tag_name} operating at consistent level"

        elif insight_type == "baseline_comparison":
            status = data.get("status", "normal")
            percent_diff = data.get("percent_difference", 0)

            if status == "critical":
                return f"🚨 {tag_name} is {abs(percent_diff):.1f}% {'above' if percent_diff > 0 else 'below'} normal - CRITICAL"
            elif status == "warning":
                return f"⚠️ {tag_name} is {abs(percent_diff):.1f}% {'above' if percent_diff > 0 else 'below'} normal"
            else:
                return f"✅ {tag_name} is within normal range"

        elif insight_type == "anomaly":
            score = data.get("anomaly_score", 0)
            is_anomaly = data.get("is_anomaly", False)

            if is_anomaly:
                return f"🔴 {tag_name} shows anomalous behavior (score: {score:.2f})"
            else:
                return f"✅ {tag_name} operating normally"

        return f"ℹ️ {tag_name}: {insight_type}"


class AIInsightsService:
    """
    Main AI Insights Service

    Orchestrates all AI capabilities:
    - Anomaly detection
    - Insight generation
    - Pattern recognition
    """

    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        self.insight_generator = InsightGenerator()
        self.baseline_stats = {}  # Cache for baseline statistics

    def analyze_tag_data(
        self,
        tag_id: str,
        tag_name: str,
        data: pd.DataFrame,
        features: List[str] = None,
        generate_insights: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis of tag data

        Args:
            tag_id: Tag ID
            tag_name: Tag name
            data: DataFrame with columns: timestamp, value
            features: Additional features for multivariate analysis
            generate_insights: Whether to generate text insights

        Returns:
            Dict with analysis results
        """
        if data.empty:
            return {
                "tag_id": tag_id,
                "tag_name": tag_name,
                "error": "No data available"
            }

        results = {
            "tag_id": tag_id,
            "tag_name": tag_name,
            "data_points": len(data),
            "timestamp": datetime.utcnow().isoformat(),
            "insights": []
        }

        # Basic statistics
        values = data['value'].values
        results["statistics"] = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "median": float(np.median(values)),
            "current": float(values[-1]) if len(values) > 0 else None
        }

        # Trend detection
        trend_info = self.insight_generator.detect_trend(values)
        results["trend"] = trend_info

        if generate_insights:
            insight_msg = self.insight_generator.generate_insight_message(
                tag_name, "trend", trend_info
            )
            results["insights"].append({
                "type": "trend",
                "severity": "info",
                "message": insight_msg,
                "data": trend_info
            })

        # Outlier detection
        outlier_info = self.insight_generator.detect_outliers_zscore(values)
        results["outliers"] = outlier_info

        if generate_insights and outlier_info["outlier_count"] > 0:
            insight_msg = self.insight_generator.generate_insight_message(
                tag_name, "outlier", outlier_info
            )
            results["insights"].append({
                "type": "outlier",
                "severity": "warning" if outlier_info["outlier_percentage"] > 5 else "info",
                "message": insight_msg,
                "data": outlier_info
            })

        # Level shift detection
        level_shift_info = self.insight_generator.detect_level_shift(values)
        results["level_shift"] = level_shift_info

        if generate_insights and level_shift_info.get("level_shift_detected", False):
            insight_msg = self.insight_generator.generate_insight_message(
                tag_name, "level_shift", level_shift_info
            )
            results["insights"].append({
                "type": "level_shift",
                "severity": "warning",
                "message": insight_msg,
                "data": level_shift_info
            })

        # Baseline comparison (if baseline exists)
        if tag_id in self.baseline_stats:
            baseline = self.baseline_stats[tag_id]
            current_value = values[-1] if len(values) > 0 else 0

            comparison = self.insight_generator.compare_to_baseline(
                current_value,
                baseline["mean"],
                baseline["std"]
            )
            results["baseline_comparison"] = comparison

            if generate_insights and comparison["status"] != "normal":
                insight_msg = self.insight_generator.generate_insight_message(
                    tag_name, "baseline_comparison", comparison
                )
                results["insights"].append({
                    "type": "baseline_comparison",
                    "severity": comparison["status"],
                    "message": insight_msg,
                    "data": comparison
                })

        return results

    def detect_anomalies_multivariate(
        self,
        data: pd.DataFrame,
        features: List[str],
        tag_metadata: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Detect anomalies using multiple features

        Args:
            data: DataFrame with features
            features: List of feature columns
            tag_metadata: Dict mapping feature names to tag names

        Returns:
            Dict with anomaly detection results
        """
        # Fit model if not already fitted
        if not self.anomaly_detector.is_fitted:
            self.anomaly_detector.fit(data, features)

        # Predict
        predictions, scores = self.anomaly_detector.predict(data)

        if len(predictions) == 0:
            return {
                "error": "No predictions available",
                "anomaly_count": 0
            }

        # Find anomalies
        anomaly_indices = np.where(predictions == -1)[0]

        results = {
            "total_points": len(predictions),
            "anomaly_count": len(anomaly_indices),
            "anomaly_percentage": float(len(anomaly_indices) / len(predictions) * 100),
            "anomalies": []
        }

        # Get details of anomalies
        for idx in anomaly_indices[:100]:  # Limit to 100 most recent
            anomaly_data = {
                "index": int(idx),
                "score": float(scores[idx]),
                "features": {}
            }

            for feature in features:
                if feature in data.columns:
                    anomaly_data["features"][feature] = float(data[feature].iloc[idx])

            results["anomalies"].append(anomaly_data)

        # Sort by score (most anomalous first)
        results["anomalies"] = sorted(
            results["anomalies"],
            key=lambda x: x["score"]
        )

        return results

    def set_baseline(self, tag_id: str, data: pd.DataFrame) -> None:
        """
        Set baseline statistics for a tag

        Args:
            tag_id: Tag ID
            data: DataFrame with value column
        """
        if data.empty or 'value' not in data.columns:
            return

        values = data['value'].values

        self.baseline_stats[tag_id] = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "sample_count": len(values),
            "updated_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Baseline set for tag {tag_id} with {len(values)} samples")

    def get_top_insights(
        self,
        tag_analyses: List[Dict[str, Any]],
        limit: int = 10,
        severity_filter: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top insights from multiple tag analyses

        Args:
            tag_analyses: List of tag analysis results
            limit: Maximum number of insights to return
            severity_filter: Filter by severity (e.g., ['critical', 'warning'])

        Returns:
            List of top insights sorted by severity
        """
        all_insights = []

        for analysis in tag_analyses:
            if "insights" in analysis:
                for insight in analysis["insights"]:
                    insight["tag_id"] = analysis.get("tag_id")
                    insight["tag_name"] = analysis.get("tag_name")
                    all_insights.append(insight)

        # Filter by severity if specified
        if severity_filter:
            all_insights = [
                i for i in all_insights
                if i.get("severity") in severity_filter
            ]

        # Sort by severity priority
        severity_priority = {"critical": 0, "warning": 1, "info": 2}
        all_insights.sort(key=lambda x: severity_priority.get(x.get("severity", "info"), 2))

        return all_insights[:limit]


# Singleton instance
_ai_insights_service = None


def get_ai_insights_service() -> AIInsightsService:
    """Get singleton instance of AI Insights Service"""
    global _ai_insights_service

    if _ai_insights_service is None:
        _ai_insights_service = AIInsightsService()

    return _ai_insights_service
