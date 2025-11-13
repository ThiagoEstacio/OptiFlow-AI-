"""
ML Drift Detection Service using Evidently AI

Monitors model performance and data drift to trigger automatic retraining
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pathlib import Path

# Evidently imports
try:
    from evidently import ColumnMapping
    from evidently.report import Report
    from evidently.metric_preset import DataDriftPreset, DataQualityPreset
    from evidently.metrics import DatasetDriftMetric, DatasetMissingValuesMetric
    EVIDENTLY_AVAILABLE = True
except ImportError:
    EVIDENTLY_AVAILABLE = False
    logging.warning("Evidently AI not available - drift detection disabled")

logger = logging.getLogger(__name__)


class MLDriftDetector:
    """
    Service for detecting data and model drift using Evidently AI

    Features:
    - Data drift detection (feature distribution changes)
    - Model performance drift (accuracy degradation)
    - Automatic retraining triggers
    - Drift reports and visualization
    """

    def __init__(
        self,
        drift_threshold: float = 0.5,
        performance_threshold: float = 0.1,
        reports_dir: str = "/tmp/drift_reports"
    ):
        """
        Initialize drift detector

        Args:
            drift_threshold: Threshold for data drift (0-1, higher = more drift required to trigger)
            performance_threshold: Max acceptable performance drop (e.g., 0.1 = 10% drop)
            reports_dir: Directory to save drift reports
        """
        self.drift_threshold = drift_threshold
        self.performance_threshold = performance_threshold
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        if not EVIDENTLY_AVAILABLE:
            logger.warning("Evidently AI not installed - drift detection will be limited")

    def detect_data_drift(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        target_column: Optional[str] = None,
        numerical_features: Optional[List[str]] = None,
        categorical_features: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect data drift between reference (training) and current (production) data

        Args:
            reference_data: Training dataset used to train the model
            current_data: Current production data
            target_column: Name of target column (if supervised learning)
            numerical_features: List of numerical feature names
            categorical_features: List of categorical feature names

        Returns:
            Dictionary with drift detection results:
            {
                "drift_detected": bool,
                "drift_score": float,
                "drifted_features": List[str],
                "drift_report_path": str,
                "recommendation": str
            }
        """
        if not EVIDENTLY_AVAILABLE:
            logger.warning("Evidently not available - skipping drift detection")
            return {
                "drift_detected": False,
                "drift_score": 0.0,
                "drifted_features": [],
                "drift_report_path": None,
                "recommendation": "Install Evidently AI for drift detection"
            }

        try:
            # Setup column mapping
            column_mapping = ColumnMapping()
            if target_column:
                column_mapping.target = target_column
            if numerical_features:
                column_mapping.numerical_features = numerical_features
            if categorical_features:
                column_mapping.categorical_features = categorical_features

            # Create drift report
            report = Report(metrics=[
                DataDriftPreset(),
                DataQualityPreset(),
                DatasetDriftMetric(),
                DatasetMissingValuesMetric()
            ])

            # Run report
            report.run(
                reference_data=reference_data,
                current_data=current_data,
                column_mapping=column_mapping
            )

            # Extract results
            result = report.as_dict()

            # Parse drift metrics
            dataset_drift = result['metrics'][2]['result']  # DatasetDriftMetric
            drift_detected = dataset_drift.get('dataset_drift', False)
            drift_score = dataset_drift.get('drift_share', 0.0)  # Share of drifted features

            # Get drifted features
            drifted_features = []
            if 'drift_by_columns' in dataset_drift:
                for feature, drift_info in dataset_drift['drift_by_columns'].items():
                    if drift_info.get('drift_detected', False):
                        drifted_features.append(feature)

            # Save report
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            report_path = self.reports_dir / f"drift_report_{timestamp}.html"
            report.save_html(str(report_path))

            logger.info(f"Drift detection completed: drift_detected={drift_detected}, score={drift_score:.2f}")

            # Generate recommendation
            if drift_detected and drift_score > self.drift_threshold:
                recommendation = f"RETRAINING REQUIRED - {drift_score:.1%} of features drifted (threshold: {self.drift_threshold:.1%})"
            elif drift_detected:
                recommendation = f"MONITORING - Drift detected but below threshold ({drift_score:.1%} < {self.drift_threshold:.1%})"
            else:
                recommendation = "NO ACTION - Data distribution stable"

            return {
                "drift_detected": drift_detected,
                "drift_score": drift_score,
                "drifted_features": drifted_features,
                "drift_report_path": str(report_path),
                "recommendation": recommendation,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error detecting data drift: {e}", exc_info=True)
            return {
                "drift_detected": False,
                "drift_score": 0.0,
                "drifted_features": [],
                "drift_report_path": None,
                "recommendation": f"Error: {str(e)}",
                "error": str(e)
            }

    def detect_performance_drift(
        self,
        model_name: str,
        recent_predictions: pd.DataFrame,
        baseline_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Detect model performance drift by comparing recent predictions to baseline

        Args:
            model_name: Name of the model being monitored
            recent_predictions: DataFrame with columns ['prediction', 'actual', 'timestamp']
            baseline_metrics: Baseline performance metrics (e.g., {'accuracy': 0.95, 'f1_score': 0.93})

        Returns:
            Dictionary with performance drift results:
            {
                "performance_drift_detected": bool,
                "current_metrics": Dict[str, float],
                "baseline_metrics": Dict[str, float],
                "metric_drops": Dict[str, float],
                "recommendation": str
            }
        """
        try:
            # Calculate current metrics
            if 'actual' not in recent_predictions.columns or 'prediction' not in recent_predictions.columns:
                logger.warning("Cannot calculate performance metrics - missing 'actual' or 'prediction' columns")
                return {
                    "performance_drift_detected": False,
                    "current_metrics": {},
                    "baseline_metrics": baseline_metrics,
                    "metric_drops": {},
                    "recommendation": "Insufficient data for performance monitoring"
                }

            # Filter out rows with missing actuals
            complete_data = recent_predictions.dropna(subset=['actual', 'prediction'])

            if len(complete_data) == 0:
                logger.warning("No complete prediction-actual pairs available")
                return {
                    "performance_drift_detected": False,
                    "current_metrics": {},
                    "baseline_metrics": baseline_metrics,
                    "metric_drops": {},
                    "recommendation": "Waiting for actual outcomes to be available"
                }

            # Calculate current metrics based on problem type
            current_metrics = {}

            # Detect if classification or regression
            is_classification = len(np.unique(complete_data['actual'])) < 10

            if is_classification:
                # Classification metrics
                from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

                y_true = complete_data['actual'].values
                y_pred = complete_data['prediction'].values

                current_metrics['accuracy'] = accuracy_score(y_true, y_pred)
                try:
                    current_metrics['precision'] = precision_score(y_true, y_pred, average='weighted', zero_division=0)
                    current_metrics['recall'] = recall_score(y_true, y_pred, average='weighted', zero_division=0)
                    current_metrics['f1_score'] = f1_score(y_true, y_pred, average='weighted', zero_division=0)
                except Exception as e:
                    logger.warning(f"Could not calculate some classification metrics: {e}")
            else:
                # Regression metrics
                from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

                y_true = complete_data['actual'].values
                y_pred = complete_data['prediction'].values

                current_metrics['mae'] = mean_absolute_error(y_true, y_pred)
                current_metrics['rmse'] = np.sqrt(mean_squared_error(y_true, y_pred))
                current_metrics['r2_score'] = r2_score(y_true, y_pred)

            # Compare to baseline
            metric_drops = {}
            performance_drift_detected = False

            for metric_name, baseline_value in baseline_metrics.items():
                if metric_name in current_metrics:
                    current_value = current_metrics[metric_name]

                    # For metrics where higher is better (accuracy, f1, r2)
                    if metric_name in ['accuracy', 'precision', 'recall', 'f1_score', 'r2_score']:
                        drop = baseline_value - current_value
                        metric_drops[metric_name] = drop

                        if drop > self.performance_threshold:
                            performance_drift_detected = True

                    # For metrics where lower is better (mae, rmse)
                    elif metric_name in ['mae', 'rmse']:
                        increase = current_value - baseline_value
                        metric_drops[metric_name] = increase

                        # Convert to percentage increase
                        pct_increase = increase / baseline_value if baseline_value > 0 else 0
                        if pct_increase > self.performance_threshold:
                            performance_drift_detected = True

            # Generate recommendation
            if performance_drift_detected:
                worst_metric = max(metric_drops.items(), key=lambda x: abs(x[1]))
                recommendation = f"RETRAINING REQUIRED - {worst_metric[0]} degraded by {abs(worst_metric[1]):.2%}"
            else:
                recommendation = "NO ACTION - Model performance within acceptable range"

            logger.info(f"Performance drift detection for {model_name}: drift_detected={performance_drift_detected}")

            return {
                "performance_drift_detected": performance_drift_detected,
                "current_metrics": current_metrics,
                "baseline_metrics": baseline_metrics,
                "metric_drops": metric_drops,
                "recommendation": recommendation,
                "samples_evaluated": len(complete_data),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error detecting performance drift: {e}", exc_info=True)
            return {
                "performance_drift_detected": False,
                "current_metrics": {},
                "baseline_metrics": baseline_metrics,
                "metric_drops": {},
                "recommendation": f"Error: {str(e)}",
                "error": str(e)
            }

    def should_retrain(
        self,
        data_drift_result: Dict[str, Any],
        performance_drift_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Determine if model should be retrained based on drift results

        Args:
            data_drift_result: Result from detect_data_drift()
            performance_drift_result: Result from detect_performance_drift() (optional)

        Returns:
            Dictionary with retraining decision:
            {
                "should_retrain": bool,
                "reason": str,
                "urgency": str ("high", "medium", "low"),
                "triggers": List[str]
            }
        """
        triggers = []
        urgency = "low"

        # Check data drift
        if data_drift_result.get('drift_detected'):
            drift_score = data_drift_result.get('drift_score', 0.0)

            if drift_score > self.drift_threshold:
                triggers.append(f"Data drift: {drift_score:.1%} of features drifted")
                urgency = "high" if drift_score > 0.7 else "medium"

        # Check performance drift
        if performance_drift_result and performance_drift_result.get('performance_drift_detected'):
            triggers.append("Model performance degradation detected")
            urgency = "high"

        # Decision
        should_retrain = len(triggers) > 0

        if should_retrain:
            reason = " AND ".join(triggers)
        else:
            reason = "No significant drift detected"

        return {
            "should_retrain": should_retrain,
            "reason": reason,
            "urgency": urgency,
            "triggers": triggers,
            "timestamp": datetime.utcnow().isoformat()
        }


# Singleton instance
_drift_detector: Optional[MLDriftDetector] = None


def get_drift_detector() -> MLDriftDetector:
    """Get or create global drift detector instance"""
    global _drift_detector

    if _drift_detector is None:
        _drift_detector = MLDriftDetector(
            drift_threshold=0.5,  # 50% of features must drift to trigger
            performance_threshold=0.1,  # 10% performance drop triggers retraining
            reports_dir="/tmp/drift_reports"
        )

    return _drift_detector
