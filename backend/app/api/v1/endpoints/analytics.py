"""
Analytics API Endpoints

Advanced analytics and query endpoints:
- POST /query: Execute advanced analytics query
- GET /saved: List saved queries
- POST /saved: Create saved query
- GET /saved/{id}: Get saved query
- PUT /saved/{id}: Update saved query
- DELETE /saved/{id}: Delete saved query
- GET /anomalies: ML-based anomaly detection
- GET /model-info: ML model information
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from pydantic import BaseModel
import joblib
import numpy as np
import os
import logging

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsQueryRequest,
    AnalyticsQueryResponse,
    SavedQuery,
    SavedQueryCreate,
    SavedQueryUpdate,
    SavedQueryResponse,
)
from app.services.analytics import AnalyticsService
from app.services.cache_service import cached
from app.services.optimized_influxdb_service import optimized_influxdb_service
from slowapi import Limiter
from slowapi.util import get_remote_address

from influxdb_client import InfluxDBClient
import pandas as pd

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

# ========================================
# 📊 ML MODELS & CONFIG
# ========================================

MODEL_DIR = "/app/models"
ISOLATION_FOREST_PATH = os.path.join(MODEL_DIR, "isolation_forest_fast.joblib")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler_fast.joblib")

INFLUX_URL = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
INFLUX_TOKEN = os.getenv("INFLUXDB_TOKEN", "my-super-secret-influxdb-token")
INFLUX_ORG = os.getenv("INFLUXDB_ORG", "optiflow")
INFLUX_BUCKET = os.getenv("INFLUXDB_BUCKET", "timeseries")

TAG_NAME_MAPPING = {
    "Motor 01 - Corrente": "MOTOR_01_CURRENT",
    "Motor 01 - Velocidade": "MOTOR_01_SPEED",
    "Motor 01 - Vibração": "MOTOR_01_VIBRATION",
    "Temperatura - Área Produção": "TEMP_SENSOR_01",
    "Temperatura - Caldeira": "TEMP_SENSOR_02",
    "Pressão - Linha Principal": "PRESSURE_01",
    "Pressão - Caldeira": "PRESSURE_02",
    "Nível - Tanque Água": "LEVEL_TANK_01",
    "Consumo Energético Total": "POWER_CONSUMPTION",
    "Taxa de Produção": "PRODUCTION_RATE",
}

TAGS_ORDER = [
    "MOTOR_01_CURRENT", "MOTOR_01_SPEED", "MOTOR_01_VIBRATION",
    "TEMP_SENSOR_01", "TEMP_SENSOR_02", "PRESSURE_01", "PRESSURE_02",
    "LEVEL_TANK_01", "POWER_CONSUMPTION", "PRODUCTION_RATE",
]


# ========================================
# 📦 ML RESPONSE MODELS
# ========================================

class AnomalyPoint(BaseModel):
    timestamp: datetime
    tag_id: str
    value: float
    anomaly_score: float
    is_anomaly: bool
    anomaly_type: Optional[str] = None


class AnomalyDetectionResponse(BaseModel):
    total_points: int
    anomalies_detected: int
    anomaly_rate: float
    model_used: str
    time_range: dict
    anomalies: List[AnomalyPoint]


@router.post("/query", response_model=AnalyticsQueryResponse)
@limiter.limit("50/minute")  # Higher limit for analytics queries
async def execute_analytics_query(
    request: Request,
    query_request: AnalyticsQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute advanced analytics query

    Supports:
    - Cross-tag comparisons
    - Multi-dimensional aggregations
    - Statistical functions (percentile, stddev, correlation)
    - Custom time windows
    - Filters and grouping

    Example request:
    ```json
    {
        "tags": ["temp_sensor_01", "pressure_sensor_01"],
        "start": "2025-10-27T00:00:00Z",
        "end": "2025-10-28T00:00:00Z",
        "filters": [
            {"field": "quality", "operator": "eq", "value": "good"}
        ],
        "aggregations": [
            {
                "function": "percentile",
                "field": "value",
                "window": "1h",
                "params": {"percentile": 95}
            },
            {
                "function": "correlation",
                "field": "value",
                "params": {"target_tag": "pressure_sensor_01"}
            }
        ],
        "group_by": ["device_id"],
        "limit": 1000,
        "include_raw_data": false
    }
    ```

    Returns:
        QueryResult with aggregation results and optional raw data
    """
    # Initialize analytics service
    analytics_service = AnalyticsService(
        influxdb_client=None,  # TODO: Get from dependency
        bucket="smartport"
    )

    # Execute query
    result = await analytics_service.execute_query(
        query=query_request,
        include_raw=query_request.include_raw_data
    )

    return result


@router.get("/saved", response_model=List[SavedQueryResponse])
@limiter.limit("30/minute")
async def list_saved_queries(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List saved analytics queries

    Returns:
    - User's own saved queries
    - Public queries from other users
    """
    # TODO: Implement saved queries model and query
    # For now, return empty list
    return []


@router.post("/saved", response_model=SavedQueryResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_saved_query(
    request: Request,
    query_create: SavedQueryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Save analytics query template for reuse

    Allows users to:
    - Save complex queries
    - Share queries with team (if is_public=true)
    - Reuse common analytics patterns
    """
    # TODO: Implement saved queries model and creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Saved queries not yet implemented"
    )


@router.get("/saved/{query_id}", response_model=SavedQueryResponse)
@limiter.limit("30/minute")
async def get_saved_query(
    request: Request,
    query_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get saved query by ID
    """
    # TODO: Implement
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Saved query not found"
    )


@router.put("/saved/{query_id}", response_model=SavedQueryResponse)
@limiter.limit("20/minute")
async def update_saved_query(
    request: Request,
    query_id: UUID,
    query_update: SavedQueryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update saved query

    Only the query owner can update
    """
    # TODO: Implement
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Saved query not found"
    )


@router.delete("/saved/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_saved_query(
    request: Request,
    query_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete saved query

    Only the query owner can delete
    """
    # TODO: Implement
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Saved query not found"
    )


# Additional analytics endpoints

@router.get("/functions", response_model=dict)
@limiter.limit("10/minute")
async def get_available_functions(request: Request):
    """
    Get list of available aggregation functions with descriptions

    Returns documentation for all supported functions
    """
    return {
        "basic": {
            "mean": {
                "description": "Calculate average value",
                "params": [],
                "example": {"function": "mean", "field": "value", "window": "1h"}
            },
            "median": {
                "description": "Calculate median value",
                "params": [],
                "example": {"function": "median", "field": "value", "window": "1h"}
            },
            "mode": {
                "description": "Calculate most frequent value",
                "params": [],
                "example": {"function": "mode", "field": "value"}
            },
            "min": {
                "description": "Find minimum value",
                "params": [],
                "example": {"function": "min", "field": "value", "window": "1h"}
            },
            "max": {
                "description": "Find maximum value",
                "params": [],
                "example": {"function": "max", "field": "value", "window": "1h"}
            },
            "sum": {
                "description": "Calculate sum of values",
                "params": [],
                "example": {"function": "sum", "field": "value", "window": "1h"}
            },
            "count": {
                "description": "Count number of data points",
                "params": [],
                "example": {"function": "count", "field": "value", "window": "1h"}
            },
        },
        "statistical": {
            "stddev": {
                "description": "Calculate standard deviation",
                "params": [],
                "example": {"function": "stddev", "field": "value", "window": "1h"}
            },
            "variance": {
                "description": "Calculate variance",
                "params": [],
                "example": {"function": "variance", "field": "value"}
            },
            "percentile": {
                "description": "Calculate percentile (e.g., P95, P99)",
                "params": [
                    {"name": "percentile", "type": "int", "range": "0-100", "required": True}
                ],
                "example": {
                    "function": "percentile",
                    "field": "value",
                    "window": "1h",
                    "params": {"percentile": 95}
                }
            },
        },
        "advanced": {
            "correlation": {
                "description": "Calculate correlation between two tags",
                "params": [
                    {"name": "target_tag", "type": "string", "required": True}
                ],
                "example": {
                    "function": "correlation",
                    "field": "value",
                    "params": {"target_tag": "pressure_sensor_01"}
                }
            },
            "moving_average": {
                "description": "Calculate moving average (SMA, EMA, WMA)",
                "params": [
                    {"name": "type", "type": "string", "options": ["simple", "exponential", "weighted"]},
                    {"name": "window_size", "type": "int", "default": 10}
                ],
                "example": {
                    "function": "moving_average",
                    "field": "value",
                    "params": {"type": "exponential", "window_size": 20}
                }
            },
            "cumulative_sum": {
                "description": "Calculate cumulative sum over time",
                "params": [],
                "example": {"function": "cumulative_sum", "field": "value"}
            },
            "rate_of_change": {
                "description": "Calculate rate of change (percentage)",
                "params": [],
                "example": {"function": "rate_of_change", "field": "value"}
            },
            "outlier_detection": {
                "description": "Detect outliers using statistical methods",
                "params": [
                    {"name": "method", "type": "string", "options": ["zscore", "iqr", "isolation_forest"]},
                    {"name": "threshold", "type": "float", "default": 3.0, "description": "For Z-score method"},
                    {"name": "multiplier", "type": "float", "default": 1.5, "description": "For IQR method"}
                ],
                "example": {
                    "function": "outlier_detection",
                    "field": "value",
                    "params": {"method": "zscore", "threshold": 3.0}
                }
            },
        }
    }


@router.get("/examples", response_model=dict)
@limiter.limit("10/minute")
async def get_query_examples(request: Request):
    """
    Get example queries for common use cases

    Returns pre-built query examples that users can modify
    """
    return {
        "production_monitoring": {
            "name": "Production Monitoring (95th Percentile)",
            "description": "Monitor production metrics with P95 aggregation",
            "query": {
                "tags": ["production_rate", "quality_index"],
                "start": "2025-10-27T00:00:00Z",
                "end": "2025-10-28T00:00:00Z",
                "aggregations": [
                    {
                        "function": "percentile",
                        "field": "value",
                        "window": "1h",
                        "params": {"percentile": 95}
                    }
                ],
                "group_by": ["device_id"]
            }
        },
        "correlation_analysis": {
            "name": "Temperature-Pressure Correlation",
            "description": "Analyze correlation between temperature and pressure",
            "query": {
                "tags": ["temp_sensor_01", "pressure_sensor_01"],
                "start": "2025-10-27T00:00:00Z",
                "end": "2025-10-28T00:00:00Z",
                "aggregations": [
                    {"function": "mean", "field": "value", "window": "15m"}
                ]
            }
        }
    }


# ========================================
# 🤖 ML ANOMALY DETECTION ENDPOINTS
# ========================================

@router.get("/anomalies", response_model=AnomalyDetectionResponse)
@cached(ttl=180, key_prefix="analytics_anomalies")
async def detect_anomalies(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    tag_id: Optional[str] = Query(None, description="Filter by specific tag"),
    model_type: str = Query("isolation_forest", description="Model type"),
    limit: int = Query(1000, description="Max points", ge=1, le=100000)
):
    """Detect anomalies using ML models"""
    # Parse dates
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else datetime.utcnow()
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else end_dt - timedelta(days=7)
    
    # Load model
    if not os.path.exists(ISOLATION_FOREST_PATH):
        raise HTTPException(status_code=503, detail="Model not trained yet")
    
    model = joblib.load(ISOLATION_FOREST_PATH)
    scaler = joblib.load(SCALER_PATH)
    
    # Query usando OptimizedInfluxDB (auto-seleciona bucket baseado em time range)
    # Para ML, sempre usamos dados brutos para máxima precisão
    start_str = start_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_str = end_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Coletar dados de todos os tags necessários
    all_data = []
    for tag_name in TAGS_ORDER:
        try:
            # Usando OptimizedInfluxDB com auto-bucket selection
            data = await optimized_influxdb_service.query_tag_data(
                tag_name=tag_name,
                start_time=start_str,
                end_time=end_str,
                limit=limit
            )
            if data:
                all_data.extend(data)
        except Exception as e:
            logger.warning(f"Failed to query tag {tag_name}: {e}")
            continue
    
    if not all_data:
        return AnomalyDetectionResponse(
            total_points=0, anomalies_detected=0, anomaly_rate=0.0,
            model_used=model_type, time_range={"start": start_dt.isoformat(), "end": end_dt.isoformat()},
            anomalies=[]
        )
    
    # Converter para DataFrame
    df = pd.DataFrame(all_data)
    
    # Pivot para ter um tag por coluna
    df_pivot = df.pivot_table(
        index='timestamp', 
        columns='tag_name', 
        values='value',
        aggfunc='mean'
    ).reset_index()
    
    # Rename colunas usando mapping
    df_pivot = df_pivot.rename(columns=TAG_NAME_MAPPING)
    feature_cols = [col for col in TAGS_ORDER if col in df_pivot.columns]
    
    if len(df_pivot) > limit:
        df_pivot = df_pivot.sample(n=limit, random_state=42)
    
    X = df_pivot[feature_cols].fillna(0).values
    timestamps = df_pivot['timestamp'].values
    
    # Predict
    X_scaled = scaler.transform(X)
    predictions = model.predict(X_scaled)
    scores = model.score_samples(X_scaled)
    is_anomaly_arr = (predictions == -1)
    
    # Build response
    anomalies = []
    for i in range(len(df_pivot)):
        if is_anomaly_arr[i]:
            tag_val = tag_id if tag_id else feature_cols[0]
            
            # Handle NaN/Inf values
            raw_value = df_pivot[feature_cols[0]].iloc[i] if feature_cols else 0.0
            value = float(raw_value) if np.isfinite(raw_value) else 0.0
            
            score_val = float(-scores[i])
            if not np.isfinite(score_val):
                score_val = 0.0
            
            anomalies.append(AnomalyPoint(
                timestamp=pd.Timestamp(timestamps[i]).to_pydatetime(),
                tag_id=tag_val,
                value=value,
                anomaly_score=score_val,
                is_anomaly=True,
                anomaly_type="outlier"
            ))
    
    return AnomalyDetectionResponse(
        total_points=len(df),
        anomalies_detected=len(anomalies),
        anomaly_rate=len(anomalies) / len(df) if len(df) > 0 else 0.0,
        model_used=model_type,
        time_range={"start": start_dt.isoformat(), "end": end_dt.isoformat()},
        anomalies=anomalies[:500]
    )


@router.get("/model-info")
async def get_model_info():
    """Get ML model information"""
    if not os.path.exists(ISOLATION_FOREST_PATH):
        return {"status": "not_ready", "message": "Model not trained"}
    
    model = joblib.load(ISOLATION_FOREST_PATH)
    return {
        "model_type": "Isolation Forest",
        "n_estimators": model.n_estimators,
        "contamination": model.contamination,
        "features": TAGS_ORDER,
        "status": "ready"
    }

