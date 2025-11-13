"""
Model Management Service

Manages the lifecycle of ML models:
- Training
- Deployment
- Versioning
- Performance monitoring
- Retraining
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import mlflow
import mlflow.sklearn
import mlflow.xgboost
import mlflow.lightgbm
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, mean_squared_error,
    mean_absolute_error, r2_score
)
import logging
import joblib
import json
import uuid

from app.models.ml_model import MLModel, ModelType, ModelStatus, Prediction

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Model Management Service

    Handles all ML model operations:
    - Training new models
    - Deploying models
    - Managing model versions
    - Monitoring model performance
    """

    def __init__(self, mlflow_tracking_uri: str = None):
        """
        Initialize Model Manager

        Args:
            mlflow_tracking_uri: MLflow tracking server URI
        """
        if mlflow_tracking_uri:
            mlflow.set_tracking_uri(mlflow_tracking_uri)
        else:
            # Use local filesystem tracking
            mlflow.set_tracking_uri("file:///tmp/mlruns")

        self.experiment_name = "optiflow-ai-insights"

        # Create experiment if it doesn't exist
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                mlflow.create_experiment(self.experiment_name)
        except Exception as e:
            logger.warning(f"Could not setup MLflow experiment: {e}")

    def train_model(
        self,
        db: Session,
        model_name: str,
        model_type: ModelType,
        algorithm: str,
        training_data: pd.DataFrame,
        features: List[str],
        target: str,
        hyperparameters: Dict[str, Any] = None,
        validation_split: float = 0.2,
        description: str = None
    ) -> MLModel:
        """
        Train a new ML model

        Args:
            db: Database session
            model_name: Name of the model
            model_type: Type of model
            algorithm: Algorithm to use (xgboost, lightgbm, random_forest, etc.)
            training_data: Training data
            features: List of feature columns
            target: Target column
            hyperparameters: Model hyperparameters
            validation_split: Validation split ratio
            description: Model description

        Returns:
            MLModel instance
        """
        logger.info(f"Training model: {model_name} ({algorithm})")

        # Create model record
        model = MLModel(
            name=model_name,
            description=description,
            model_type=model_type,
            status=ModelStatus.TRAINING,
            algorithm=algorithm,
            version="1.0.0",
            feature_names=features,
            hyperparameters=hyperparameters or {},
            training_start=datetime.utcnow()
        )

        db.add(model)
        db.commit()
        db.refresh(model)

        try:
            # Prepare data
            X = training_data[features].values
            y = training_data[target].values

            # Split data
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=validation_split, random_state=42
            )

            # Start MLflow run
            with mlflow.start_run(run_name=model_name) as run:
                # Train model based on algorithm
                trained_model = self._train_algorithm(
                    algorithm=algorithm,
                    X_train=X_train,
                    y_train=y_train,
                    hyperparameters=hyperparameters or {}
                )

                # Make predictions
                y_pred_train = trained_model.predict(X_train)
                y_pred_val = trained_model.predict(X_val)

                # Calculate metrics
                if model_type in [ModelType.CLASSIFICATION, ModelType.PREDICTIVE_MAINTENANCE]:
                    metrics = self._calculate_classification_metrics(
                        y_train, y_pred_train, y_val, y_pred_val
                    )
                else:
                    metrics = self._calculate_regression_metrics(
                        y_train, y_pred_train, y_val, y_pred_val
                    )

                # Log parameters and metrics to MLflow
                mlflow.log_params(hyperparameters or {})
                mlflow.log_metrics(metrics)

                # Log model to MLflow
                if algorithm.startswith("xgboost"):
                    mlflow.xgboost.log_model(trained_model, "model")
                elif algorithm.startswith("lightgbm"):
                    mlflow.lightgbm.log_model(trained_model, "model")
                else:
                    mlflow.sklearn.log_model(trained_model, "model")

                # Get feature importance
                feature_importance = self._get_feature_importance(
                    trained_model, features
                )

                # Update model record
                model.mlflow_run_id = run.info.run_id
                model.mlflow_model_uri = f"runs:/{run.info.run_id}/model"
                model.metrics = metrics
                model.feature_importance = feature_importance
                model.training_samples = len(X_train)
                model.training_end = datetime.utcnow()
                model.status = ModelStatus.ACTIVE

                db.commit()
                db.refresh(model)

                logger.info(f"Model {model_name} trained successfully. Metrics: {metrics}")

                return model

        except Exception as e:
            logger.error(f"Error training model: {e}")
            model.status = ModelStatus.FAILED
            db.commit()
            raise

    def _train_algorithm(
        self,
        algorithm: str,
        X_train: np.ndarray,
        y_train: np.ndarray,
        hyperparameters: Dict[str, Any]
    ):
        """Train model based on algorithm"""

        if algorithm == "xgboost_classifier":
            import xgboost as xgb
            model = xgb.XGBClassifier(**hyperparameters)

        elif algorithm == "xgboost_regressor":
            import xgboost as xgb
            model = xgb.XGBRegressor(**hyperparameters)

        elif algorithm == "lightgbm_classifier":
            import lightgbm as lgb
            model = lgb.LGBMClassifier(**hyperparameters)

        elif algorithm == "lightgbm_regressor":
            import lightgbm as lgb
            model = lgb.LGBMRegressor(**hyperparameters)

        elif algorithm == "random_forest_classifier":
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(**hyperparameters)

        elif algorithm == "random_forest_regressor":
            from sklearn.ensemble import RandomForestRegressor
            model = RandomForestRegressor(**hyperparameters)

        elif algorithm == "gradient_boosting_classifier":
            from sklearn.ensemble import GradientBoostingClassifier
            model = GradientBoostingClassifier(**hyperparameters)

        elif algorithm == "gradient_boosting_regressor":
            from sklearn.ensemble import GradientBoostingRegressor
            model = GradientBoostingRegressor(**hyperparameters)

        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        # Fit model
        model.fit(X_train, y_train)

        return model

    def _calculate_classification_metrics(
        self,
        y_train: np.ndarray,
        y_pred_train: np.ndarray,
        y_val: np.ndarray,
        y_pred_val: np.ndarray
    ) -> Dict[str, float]:
        """Calculate classification metrics"""

        metrics = {
            "train_accuracy": float(accuracy_score(y_train, y_pred_train)),
            "val_accuracy": float(accuracy_score(y_val, y_pred_val)),
            "train_precision": float(precision_score(y_train, y_pred_train, average='weighted', zero_division=0)),
            "val_precision": float(precision_score(y_val, y_pred_val, average='weighted', zero_division=0)),
            "train_recall": float(recall_score(y_train, y_pred_train, average='weighted', zero_division=0)),
            "val_recall": float(recall_score(y_val, y_pred_val, average='weighted', zero_division=0)),
            "train_f1": float(f1_score(y_train, y_pred_train, average='weighted', zero_division=0)),
            "val_f1": float(f1_score(y_val, y_pred_val, average='weighted', zero_division=0))
        }

        # Try to calculate AUC if binary classification
        try:
            if len(np.unique(y_train)) == 2:
                metrics["train_auc"] = float(roc_auc_score(y_train, y_pred_train))
                metrics["val_auc"] = float(roc_auc_score(y_val, y_pred_val))
        except:
            pass

        return metrics

    def _calculate_regression_metrics(
        self,
        y_train: np.ndarray,
        y_pred_train: np.ndarray,
        y_val: np.ndarray,
        y_pred_val: np.ndarray
    ) -> Dict[str, float]:
        """Calculate regression metrics"""

        return {
            "train_mse": float(mean_squared_error(y_train, y_pred_train)),
            "val_mse": float(mean_squared_error(y_val, y_pred_val)),
            "train_rmse": float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
            "val_rmse": float(np.sqrt(mean_squared_error(y_val, y_pred_val))),
            "train_mae": float(mean_absolute_error(y_train, y_pred_train)),
            "val_mae": float(mean_absolute_error(y_val, y_pred_val)),
            "train_r2": float(r2_score(y_train, y_pred_train)),
            "val_r2": float(r2_score(y_val, y_pred_val))
        }

    def _get_feature_importance(
        self,
        model,
        feature_names: List[str]
    ) -> Dict[str, float]:
        """Extract feature importance from model"""

        try:
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                return {
                    name: float(importance)
                    for name, importance in zip(feature_names, importances)
                }
        except:
            pass

        return {}

    def deploy_model(
        self,
        db: Session,
        model_id: str
    ) -> MLModel:
        """
        Deploy a trained model

        Args:
            db: Database session
            model_id: Model ID

        Returns:
            Updated MLModel instance
        """
        model = db.query(MLModel).filter(MLModel.id == model_id).first()

        if not model:
            raise ValueError(f"Model {model_id} not found")

        if model.status != ModelStatus.ACTIVE:
            raise ValueError(f"Model {model_id} is not in ACTIVE status")

        # Deactivate other models of the same type
        db.query(MLModel).filter(
            MLModel.model_type == model.model_type,
            MLModel.id != model.id,
            MLModel.is_active == True
        ).update({
            "is_active": False
        })

        # Activate this model
        model.is_active = True
        model.deployed_at = datetime.utcnow()

        db.commit()
        db.refresh(model)

        logger.info(f"Model {model.name} deployed successfully")

        return model

    def predict(
        self,
        db: Session,
        model_id: str,
        features: Dict[str, float],
        target_type: str,
        target_id: str
    ) -> Prediction:
        """
        Make a prediction using a deployed model

        Args:
            db: Database session
            model_id: Model ID
            features: Feature values
            target_type: Type of target (device, tag, etc.)
            target_id: Target ID

        Returns:
            Prediction instance
        """
        model = db.query(MLModel).filter(
            MLModel.id == model_id,
            MLModel.is_active == True
        ).first()

        if not model:
            raise ValueError(f"Active model {model_id} not found")

        # Load model from MLflow
        loaded_model = mlflow.sklearn.load_model(model.mlflow_model_uri)

        # Prepare features
        feature_values = [features.get(name, 0.0) for name in model.feature_names]
        X = np.array([feature_values])

        # Make prediction
        prediction_value = loaded_model.predict(X)[0]

        # Get probability if classifier
        confidence = None
        probabilities = {}

        if hasattr(loaded_model, 'predict_proba'):
            proba = loaded_model.predict_proba(X)[0]
            confidence = float(np.max(proba))
            probabilities = {
                f"class_{i}": float(p)
                for i, p in enumerate(proba)
            }

        # Create prediction record
        prediction = Prediction(
            model_id=model.id,
            target_type=target_type,
            target_id=uuid.UUID(target_id),
            prediction_value=float(prediction_value) if not isinstance(prediction_value, str) else None,
            prediction_class=str(prediction_value) if isinstance(prediction_value, str) else None,
            confidence=confidence,
            probabilities=probabilities,
            features=features
        )

        db.add(prediction)
        db.commit()
        db.refresh(prediction)

        return prediction

    def list_models(
        self,
        db: Session,
        model_type: ModelType = None,
        status: ModelStatus = None,
        is_active: bool = None
    ) -> List[MLModel]:
        """
        List models with optional filters

        Args:
            db: Database session
            model_type: Filter by model type
            status: Filter by status
            is_active: Filter by deployment status

        Returns:
            List of MLModel instances
        """
        query = db.query(MLModel)

        if model_type:
            query = query.filter(MLModel.model_type == model_type)

        if status:
            query = query.filter(MLModel.status == status)

        if is_active is not None:
            query = query.filter(MLModel.is_active == is_active)

        return query.order_by(MLModel.created_at.desc()).all()

    def get_model_performance(
        self,
        db: Session,
        model_id: str,
        time_window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get model performance metrics over time

        Args:
            db: Database session
            model_id: Model ID
            time_window_days: Time window for analysis

        Returns:
            Performance metrics
        """
        model = db.query(MLModel).filter(MLModel.id == model_id).first()

        if not model:
            raise ValueError(f"Model {model_id} not found")

        # Get predictions from the time window
        cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)

        predictions = db.query(Prediction).filter(
            Prediction.model_id == model_id,
            Prediction.created_at >= cutoff_date
        ).all()

        # Calculate statistics
        total_predictions = len(predictions)
        predictions_with_outcome = [
            p for p in predictions
            if p.actual_value is not None or p.actual_class is not None
        ]

        performance = {
            "model_id": str(model.id),
            "model_name": model.name,
            "total_predictions": total_predictions,
            "predictions_with_outcome": len(predictions_with_outcome),
            "time_window_days": time_window_days,
            "training_metrics": model.metrics
        }

        # Calculate accuracy if we have outcomes
        if predictions_with_outcome:
            if model.model_type in [ModelType.CLASSIFICATION, ModelType.PREDICTIVE_MAINTENANCE]:
                y_true = [p.actual_class for p in predictions_with_outcome if p.actual_class]
                y_pred = [p.prediction_class for p in predictions_with_outcome if p.actual_class]

                if y_true and y_pred:
                    performance["production_accuracy"] = float(accuracy_score(y_true, y_pred))
            else:
                y_true = [p.actual_value for p in predictions_with_outcome if p.actual_value is not None]
                y_pred = [p.prediction_value for p in predictions_with_outcome if p.actual_value is not None]

                if y_true and y_pred:
                    performance["production_mse"] = float(mean_squared_error(y_true, y_pred))
                    performance["production_mae"] = float(mean_absolute_error(y_true, y_pred))
                    performance["production_r2"] = float(r2_score(y_true, y_pred))

        return performance


# Singleton instance
_model_manager = None


def get_model_manager(mlflow_tracking_uri: str = None) -> ModelManager:
    """Get singleton instance of Model Manager"""
    global _model_manager

    if _model_manager is None:
        _model_manager = ModelManager(mlflow_tracking_uri)

    return _model_manager
