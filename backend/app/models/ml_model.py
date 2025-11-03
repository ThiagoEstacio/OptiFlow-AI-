"""
ML Model and Prediction models
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Float, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class ModelType(str, enum.Enum):
    """ML model types"""
    PREDICTIVE_MAINTENANCE = "predictive_maintenance"
    ANOMALY_DETECTION = "anomaly_detection"
    DEMAND_FORECAST = "demand_forecast"
    PROCESS_OPTIMIZATION = "process_optimization"
    CLASSIFICATION = "classification"
    REGRESSION = "regression"


class ModelStatus(str, enum.Enum):
    """Model status"""
    TRAINING = "training"
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"


class MLModel(Base):
    """
    ML Model - Trained machine learning models
    """
    __tablename__ = "ml_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    model_type = Column(SQLEnum(ModelType), nullable=False, index=True)
    status = Column(SQLEnum(ModelStatus), default=ModelStatus.TRAINING, nullable=False, index=True)

    # MLflow tracking
    mlflow_run_id = Column(String(255), nullable=True, index=True)
    mlflow_model_uri = Column(String(500), nullable=True)

    # Model version
    version = Column(String(50), nullable=False)

    # Algorithm info
    algorithm = Column(String(100), nullable=False)  # XGBoost, LightGBM, RandomForest, etc.

    # Performance metrics
    metrics = Column(JSONB, default=dict, nullable=False)
    # Example:
    # {
    #   "accuracy": 0.95,
    #   "precision": 0.93,
    #   "recall": 0.94,
    #   "f1_score": 0.935,
    #   "auc": 0.98
    # }

    # Training info
    training_start = Column(DateTime(timezone=True), nullable=True)
    training_end = Column(DateTime(timezone=True), nullable=True)
    training_samples = Column(Integer, nullable=True)

    # Features
    feature_names = Column(JSONB, default=list, nullable=False)
    feature_importance = Column(JSONB, default=dict, nullable=False)

    # Hyperparameters
    hyperparameters = Column(JSONB, default=dict, nullable=False)

    # Deployment info
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)

    # Retraining schedule
    retrain_frequency_days = Column(Integer, nullable=True)
    last_retrain = Column(DateTime(timezone=True), nullable=True)
    next_retrain = Column(DateTime(timezone=True), nullable=True)

    # Additional settings
    settings = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    predictions = relationship("Prediction", back_populates="model", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MLModel {self.name} v{self.version}>"


class Prediction(Base):
    """
    Prediction - Results from ML model inference
    """
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("ml_models.id", ondelete="CASCADE"), nullable=False, index=True)

    # Prediction target (e.g., device_id for predictive maintenance)
    target_type = Column(String(50), nullable=False, index=True)  # device, tag, site, etc.
    target_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Prediction results
    prediction_value = Column(Float, nullable=True)
    prediction_class = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=True)  # 0-1 or 0-100

    # Probability distribution (for classification)
    probabilities = Column(JSONB, default=dict, nullable=False)

    # Feature values used for prediction
    features = Column(JSONB, default=dict, nullable=False)

    # SHAP values for explainability
    shap_values = Column(JSONB, default=dict, nullable=False)

    # Time window
    prediction_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    prediction_horizon = Column(String(50), nullable=True)  # "24h", "7d", etc.

    # Outcome (for model monitoring)
    actual_value = Column(Float, nullable=True)
    actual_class = Column(String(100), nullable=True)
    outcome_timestamp = Column(DateTime(timezone=True), nullable=True)

    # Additional data
    prediction_metadata = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    model = relationship("MLModel", back_populates="predictions")

    def __repr__(self):
        return f"<Prediction {self.id} (confidence: {self.confidence})>"
