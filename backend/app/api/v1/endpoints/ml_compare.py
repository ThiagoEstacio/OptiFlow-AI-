"""
ML Model Comparison Endpoint - A/B Testing
OptiFlow AI - Compare IF vs Ensemble models
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
import os
import logging

from app.services.cache_service import cached

logger = logging.getLogger(__name__)

router = APIRouter()

# Model paths
IF_MODEL_PATH = "/app/models/isolation_forest_optimized.pkl"
IF_SCALER_PATH = "/app/models/scaler_optimized.pkl"
ENSEMBLE_MODEL_PATH = "/app/models/ensemble_anomaly_detector.pkl"
ENSEMBLE_SCALER_PATH = "/app/models/ensemble_scaler.pkl"

# Load models on startup
try:
    if_model = joblib.load(IF_MODEL_PATH)
    if_scaler = joblib.load(IF_SCALER_PATH)
    logger.info("✅ IF model loaded")
except Exception as e:
    logger.warning(f"⚠️  IF model not available: {e}")
    if_model = None
    if_scaler = None

try:
    ensemble = joblib.load(ENSEMBLE_MODEL_PATH)
    ensemble_scaler = joblib.load(ENSEMBLE_SCALER_PATH)
    logger.info("✅ Ensemble model loaded")
except Exception as e:
    logger.warning(f"⚠️  Ensemble model not available: {e}")
    ensemble = None
    ensemble_scaler = None

# ============================================================================
# Response Models
# ============================================================================

class ModelPrediction(BaseModel):
    model_name: str
    anomalies_detected: int
    anomaly_percentage: float
    anomaly_indices: List[int]
    prediction_scores: List[float]
    execution_time_ms: float

class ComparisonResult(BaseModel):
    if_prediction: Optional[ModelPrediction]
    ensemble_prediction: Optional[ModelPrediction]
    agreement_rate: Optional[float]
    both_agree_anomalies: Optional[int]
    disagreement_indices: Optional[List[int]]
    recommendation: str
    
class ModelMetrics(BaseModel):
    model_name: str
    size_mb: float
    features_count: int
    available: bool
    path: str

# ============================================================================
# Endpoints
# ============================================================================

@router.post("/compare", response_model=ComparisonResult)
async def compare_models(
    data: List[List[float]],
    description: str = Query("Test data", description="Description of the test data")
):
    """
    Compare predictions from IF and Ensemble models
    
    **Parameters:**
    - data: List of samples, each sample is a list of feature values
    - description: Description of what this test represents
    
    **Returns:**
    - Predictions from both models
    - Agreement analysis
    - Recommendation on which model to use
    """
    
    if not data or len(data) == 0:
        raise HTTPException(status_code=400, detail="No data provided")
    
    # Convert to numpy array
    X = np.array(data)
    
    result = {
        "if_prediction": None,
        "ensemble_prediction": None,
        "agreement_rate": None,
        "both_agree_anomalies": None,
        "disagreement_indices": None,
        "recommendation": ""
    }
    
    # ============================================================================
    # IF Model Prediction
    # ============================================================================
    if if_model and if_scaler:
        try:
            start_time = datetime.now()
            
            # Scale data
            X_scaled = if_scaler.transform(X)
            
            # Predict
            predictions = if_model.predict(X_scaled)
            scores = if_model.score_samples(X_scaled)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Process results
            anomaly_mask = predictions == -1
            anomaly_indices = np.where(anomaly_mask)[0].tolist()
            
            result["if_prediction"] = ModelPrediction(
                model_name="Isolation Forest (Optimized)",
                anomalies_detected=int(anomaly_mask.sum()),
                anomaly_percentage=float(anomaly_mask.sum() / len(X) * 100),
                anomaly_indices=anomaly_indices,
                prediction_scores=scores.tolist(),
                execution_time_ms=execution_time
            )
            
            logger.info(f"✅ IF prediction: {anomaly_mask.sum()} anomalies in {execution_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"❌ IF prediction failed: {e}")
    
    # ============================================================================
    # Ensemble Model Prediction
    # ============================================================================
    if ensemble and ensemble_scaler:
        try:
            start_time = datetime.now()
            
            # Scale data
            X_scaled = ensemble_scaler.transform(X)
            
            # Predict with both models
            if_pred = ensemble['if_model'].predict(X_scaled)
            lof_pred = ensemble['lof_model'].predict(X_scaled)
            
            # Get scores
            if_scores = ensemble['if_model'].score_samples(X_scaled)
            lof_scores = ensemble['lof_model'].score_samples(X_scaled)
            
            # Ensemble voting
            if_binary = (if_pred == 1).astype(int)
            lof_binary = (lof_pred == 1).astype(int)
            ensemble_votes = (if_binary + lof_binary) / 2
            ensemble_pred = (ensemble_votes >= ensemble['voting_threshold']).astype(int)
            ensemble_pred = np.where(ensemble_pred == 1, 1, -1)
            
            # Combined scores
            combined_scores = (if_scores + lof_scores) / 2
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Process results
            anomaly_mask = ensemble_pred == -1
            anomaly_indices = np.where(anomaly_mask)[0].tolist()
            
            result["ensemble_prediction"] = ModelPrediction(
                model_name="Ensemble (IF + LOF)",
                anomalies_detected=int(anomaly_mask.sum()),
                anomaly_percentage=float(anomaly_mask.sum() / len(X) * 100),
                anomaly_indices=anomaly_indices,
                prediction_scores=combined_scores.tolist(),
                execution_time_ms=execution_time
            )
            
            logger.info(f"✅ Ensemble prediction: {anomaly_mask.sum()} anomalies in {execution_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"❌ Ensemble prediction failed: {e}")
    
    # ============================================================================
    # Agreement Analysis
    # ============================================================================
    if result["if_prediction"] and result["ensemble_prediction"]:
        if_anomalies = set(result["if_prediction"].anomaly_indices)
        ensemble_anomalies = set(result["ensemble_prediction"].anomaly_indices)
        
        # Agreement
        agreement = if_anomalies & ensemble_anomalies  # Intersection
        disagreement = if_anomalies ^ ensemble_anomalies  # Symmetric difference
        
        result["both_agree_anomalies"] = len(agreement)
        result["disagreement_indices"] = sorted(list(disagreement))
        
        # Agreement rate (what % of total detected anomalies they agree on)
        total_detections = len(if_anomalies | ensemble_anomalies)
        if total_detections > 0:
            result["agreement_rate"] = len(agreement) / total_detections * 100
        else:
            result["agreement_rate"] = 100.0  # No anomalies = perfect agreement
        
        # Recommendation
        if result["agreement_rate"] >= 80:
            result["recommendation"] = "HIGH CONFIDENCE: Both models strongly agree. Use either model."
        elif result["agreement_rate"] >= 50:
            result["recommendation"] = "MEDIUM CONFIDENCE: Models partially agree. Ensemble recommended for robustness."
        else:
            result["recommendation"] = "LOW CONFIDENCE: Models disagree significantly. Manual review recommended. Use Ensemble for more conservative detection."
        
        logger.info(f"📊 Agreement rate: {result['agreement_rate']:.1f}%")
    
    elif result["if_prediction"]:
        result["recommendation"] = "Only IF model available. Consider training Ensemble for more robust detection."
    elif result["ensemble_prediction"]:
        result["recommendation"] = "Only Ensemble model available. Good choice for robust anomaly detection."
    else:
        result["recommendation"] = "ERROR: No models available for prediction."
    
    return ComparisonResult(**result)


@router.get("/models/info", response_model=List[ModelMetrics])
@cached(ttl=3600, key_prefix="ml_models_info")
async def get_models_info():
    """
    Get information about available ML models
    
    **Returns:**
    - List of models with metadata (size, features, availability)
    """
    
    models_info = []
    
    # IF Model
    if_available = os.path.exists(IF_MODEL_PATH)
    if_size = os.path.getsize(IF_MODEL_PATH) / (1024 * 1024) if if_available else 0
    
    # Try to get feature count
    if_features = 0
    if if_model:
        try:
            if_features = if_model.n_features_in_
        except:
            if_features = 20  # Known from training
    
    models_info.append(ModelMetrics(
        model_name="Isolation Forest (Optimized)",
        size_mb=round(if_size, 2),
        features_count=if_features,
        available=if_available and if_model is not None,
        path=IF_MODEL_PATH
    ))
    
    # Ensemble Model
    ensemble_available = os.path.exists(ENSEMBLE_MODEL_PATH)
    ensemble_size = os.path.getsize(ENSEMBLE_MODEL_PATH) / (1024 * 1024) if ensemble_available else 0
    
    ensemble_features = 0
    if ensemble:
        try:
            ensemble_features = ensemble['if_model'].n_features_in_
        except:
            ensemble_features = 14  # Known from training
    
    models_info.append(ModelMetrics(
        model_name="Ensemble (IF + LOF)",
        size_mb=round(ensemble_size, 2),
        features_count=ensemble_features,
        available=ensemble_available and ensemble is not None,
        path=ENSEMBLE_MODEL_PATH
    ))
    
    return models_info


@router.post("/test/synthetic")
async def test_with_synthetic_data(
    n_samples: int = Query(100, description="Number of synthetic samples"),
    n_features: int = Query(14, description="Number of features (14 for Ensemble, 20 for IF)"),
    contamination: float = Query(0.05, description="Percentage of anomalies to inject")
):
    """
    Test models with synthetic data
    
    **Parameters:**
    - n_samples: Number of samples to generate
    - n_features: Number of features per sample
    - contamination: Percentage of anomalies (0.0 to 1.0)
    
    **Returns:**
    - Comparison result from both models
    """
    
    # Generate synthetic data
    np.random.seed(42)
    
    # Normal data
    X_normal = np.random.randn(int(n_samples * (1 - contamination)), n_features)
    
    # Anomalous data (outliers)
    X_anomaly = np.random.randn(int(n_samples * contamination), n_features) * 3 + 5
    
    # Combine
    X = np.vstack([X_normal, X_anomaly])
    
    # Shuffle
    indices = np.random.permutation(len(X))
    X = X[indices]
    
    # Convert to list for API
    data = X.tolist()
    
    # Call compare endpoint
    return await compare_models(data, description=f"Synthetic test data ({n_samples} samples, {contamination*100:.1f}% anomalies)")
