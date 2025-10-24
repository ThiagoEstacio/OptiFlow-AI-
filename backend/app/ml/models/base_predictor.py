"""
Base Predictor class for ML models
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np


class BasePredictor(ABC):
    """
    Base class for all ML predictors
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.is_trained = False
        self.metadata = {}

    @abstractmethod
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> Dict[str, Any]:
        """
        Train the model

        Args:
            X: Feature DataFrame
            y: Target Series
            **kwargs: Additional training parameters

        Returns:
            Training metrics dictionary
        """
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions

        Args:
            X: Feature DataFrame

        Returns:
            Predictions array
        """
        pass

    @abstractmethod
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """
        Evaluate model performance

        Args:
            X: Feature DataFrame
            y: True target values

        Returns:
            Evaluation metrics dictionary
        """
        pass

    def save_model(self, path: str):
        """Save model to disk"""
        import joblib
        if self.model is None:
            raise ValueError("No model to save. Train the model first.")
        joblib.dump({
            'model': self.model,
            'metadata': self.metadata
        }, path)

    def load_model(self, path: str):
        """Load model from disk"""
        import joblib
        data = joblib.load(path)
        self.model = data['model']
        self.metadata = data.get('metadata', {})
        self.is_trained = True
