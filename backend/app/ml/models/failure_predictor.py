"""
Failure Predictor - Predicts equipment failures using machine learning
"""
from typing import Dict, Any
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from app.ml.models.base_predictor import BasePredictor


class FailurePredictor(BasePredictor):
    """
    Predicts equipment failures based on sensor data and historical patterns
    """

    def __init__(self):
        super().__init__(model_name="FailurePredictor")
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )

    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> Dict[str, Any]:
        """
        Train the failure prediction model

        Args:
            X: Features (sensor data, operating conditions)
            y: Target (0 = normal, 1 = failure)

        Returns:
            Training metrics
        """
        self.model.fit(X, y)
        self.is_trained = True

        # Store feature importance
        self.metadata['feature_importance'] = dict(zip(
            X.columns,
            self.model.feature_importances_
        ))

        # Calculate training metrics
        y_pred = self.model.predict(X)
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, zero_division=0),
            'recall': recall_score(y, y_pred, zero_division=0),
            'f1_score': f1_score(y, y_pred, zero_division=0)
        }

        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict failure probability

        Args:
            X: Feature DataFrame

        Returns:
            Failure predictions (0 or 1)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")

        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict failure probabilities

        Args:
            X: Feature DataFrame

        Returns:
            Probability of failure for each sample
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")

        return self.model.predict_proba(X)[:, 1]  # Probability of failure class

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """
        Evaluate model on test data

        Args:
            X: Test features
            y: True labels

        Returns:
            Evaluation metrics
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")

        y_pred = self.model.predict(X)

        return {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, zero_division=0),
            'recall': recall_score(y, y_pred, zero_division=0),
            'f1_score': f1_score(y, y_pred, zero_division=0)
        }
