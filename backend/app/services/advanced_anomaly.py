"""
Advanced Anomaly Detection Service

Advanced anomaly detection methods:
- LSTM Autoencoder for deep learning anomaly detection
- Multivariate anomaly detection
- Real-time streaming anomaly detection
- Anomaly severity scoring
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LSTMAutoencoderDetector:
    """
    LSTM Autoencoder Anomaly Detector

    Uses deep learning to detect anomalies in time series data
    """

    def __init__(
        self,
        sequence_length: int = 50,
        encoding_dim: int = 10,
        epochs: int = 50,
        batch_size: int = 32
    ):
        """
        Initialize LSTM Autoencoder

        Args:
            sequence_length: Length of input sequences
            encoding_dim: Dimension of encoded representation
            epochs: Number of training epochs
            batch_size: Batch size for training
        """
        self.sequence_length = sequence_length
        self.encoding_dim = encoding_dim
        self.epochs = epochs
        self.batch_size = batch_size
        self.model = None
        self.scaler = None
        self.threshold = None
        self.is_trained = False

    def _create_model(self, n_features: int):
        """Create LSTM autoencoder model"""
        try:
            from tensorflow.keras.models import Sequential, Model
            from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed, Input
            from tensorflow.keras.optimizers import Adam
        except ImportError:
            logger.error("TensorFlow not installed. Install with: pip install tensorflow")
            return None

        # Encoder
        model = Sequential([
            # Encoder
            LSTM(64, activation='relu', input_shape=(self.sequence_length, n_features), return_sequences=True),
            LSTM(32, activation='relu', return_sequences=False),
            Dense(self.encoding_dim, activation='relu'),

            # Decoder
            RepeatVector(self.sequence_length),
            LSTM(32, activation='relu', return_sequences=True),
            LSTM(64, activation='relu', return_sequences=True),
            TimeDistributed(Dense(n_features))
        ])

        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')

        return model

    def _create_sequences(self, data: np.ndarray) -> np.ndarray:
        """Create sequences for LSTM"""
        sequences = []

        for i in range(len(data) - self.sequence_length + 1):
            sequences.append(data[i:i + self.sequence_length])

        return np.array(sequences)

    def train(
        self,
        training_data: pd.DataFrame,
        features: List[str],
        contamination: float = 0.05
    ):
        """
        Train LSTM autoencoder

        Args:
            training_data: Historical data (should be normal/non-anomalous)
            features: Feature columns
            contamination: Expected proportion of anomalies (for threshold)
        """
        from sklearn.preprocessing import StandardScaler

        try:
            # Scale data
            self.scaler = StandardScaler()
            X = training_data[features].values
            X_scaled = self.scaler.fit_transform(X)

            # Create sequences
            X_seq = self._create_sequences(X_scaled)

            if len(X_seq) == 0:
                logger.error("Insufficient data for sequence creation")
                return

            # Create and train model
            n_features = len(features)
            self.model = self._create_model(n_features)

            if self.model is None:
                return

            logger.info(f"Training LSTM autoencoder with {len(X_seq)} sequences...")

            self.model.fit(
                X_seq, X_seq,
                epochs=self.epochs,
                batch_size=self.batch_size,
                validation_split=0.2,
                verbose=0
            )

            # Calculate reconstruction errors for threshold
            predictions = self.model.predict(X_seq, verbose=0)
            reconstruction_errors = np.mean(np.square(X_seq - predictions), axis=(1, 2))

            # Set threshold based on contamination rate
            self.threshold = np.percentile(reconstruction_errors, (1 - contamination) * 100)

            self.is_trained = True

            logger.info(f"LSTM autoencoder trained. Threshold: {self.threshold:.4f}")

        except Exception as e:
            logger.error(f"Error training LSTM autoencoder: {e}")

    def detect(
        self,
        data: pd.DataFrame,
        features: List[str]
    ) -> Dict[str, Any]:
        """
        Detect anomalies using trained autoencoder

        Args:
            data: Data to analyze
            features: Feature columns

        Returns:
            Anomaly detection results
        """
        if not self.is_trained or self.model is None:
            logger.warning("LSTM autoencoder not trained")
            return {
                "error": "Model not trained",
                "anomalies": []
            }

        try:
            # Scale data
            X = data[features].values
            X_scaled = self.scaler.transform(X)

            # Create sequences
            X_seq = self._create_sequences(X_scaled)

            if len(X_seq) == 0:
                return {
                    "total_points": 0,
                    "anomaly_count": 0,
                    "anomalies": []
                }

            # Predict and calculate reconstruction errors
            predictions = self.model.predict(X_seq, verbose=0)
            reconstruction_errors = np.mean(np.square(X_seq - predictions), axis=(1, 2))

            # Identify anomalies
            anomalies = []
            anomaly_indices = np.where(reconstruction_errors > self.threshold)[0]

            for idx in anomaly_indices:
                # Map back to original data index
                data_idx = idx + self.sequence_length - 1

                if data_idx < len(data):
                    anomaly_severity = "high" if reconstruction_errors[idx] > self.threshold * 2 else "medium"

                    anomalies.append({
                        "index": int(data_idx),
                        "timestamp": data.iloc[data_idx].get('timestamp', '').isoformat() if hasattr(data.iloc[data_idx].get('timestamp', ''), 'isoformat') else str(data.iloc[data_idx].get('timestamp', '')),
                        "reconstruction_error": float(reconstruction_errors[idx]),
                        "threshold": float(self.threshold),
                        "severity": anomaly_severity,
                        "features": {
                            feature: float(data.iloc[data_idx][feature])
                            for feature in features
                        }
                    })

            return {
                "total_points": len(X_seq),
                "anomaly_count": len(anomalies),
                "anomaly_percentage": (len(anomalies) / len(X_seq) * 100) if len(X_seq) > 0 else 0,
                "anomalies": anomalies[:100]  # Limit to 100
            }

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return {
                "error": str(e),
                "anomalies": []
            }


class AdvancedAnomalyService:
    """
    Advanced Anomaly Detection Service

    Orchestrates advanced anomaly detection methods
    """

    def __init__(self):
        self.lstm_detector = LSTMAutoencoderDetector()

    def detect_lstm(
        self,
        data: pd.DataFrame,
        features: List[str],
        train_first: bool = True
    ) -> Dict[str, Any]:
        """
        Detect anomalies using LSTM autoencoder

        Args:
            data: Data to analyze
            features: Feature columns
            train_first: Whether to train on this data first

        Returns:
            Anomaly detection results
        """
        if train_first:
            # Use first 80% for training
            train_size = int(len(data) * 0.8)
            train_data = data.iloc[:train_size]

            self.lstm_detector.train(train_data, features)

        # Detect on full data
        results = self.lstm_detector.detect(data, features)

        return results


# Singleton instance
_advanced_anomaly_service = None


def get_advanced_anomaly_service() -> AdvancedAnomalyService:
    """Get singleton instance of Advanced Anomaly Service"""
    global _advanced_anomaly_service

    if _advanced_anomaly_service is None:
        _advanced_anomaly_service = AdvancedAnomalyService()

    return _advanced_anomaly_service
