"""
OEE Prediction API Endpoints - Sprint 3
========================================

Endpoints for OEE prediction and early warning system.

Endpoints:
- GET /predictions/{equipment_id} - Get OEE predictions for equipment
- GET /predictions/all - Get predictions for all equipment
- GET /warnings - Get active drop warnings
- GET /warnings/critical - Get only critical warnings
- POST /predictions/refresh - Force refresh predictions
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from app.services.oee_prediction_service import (
    oee_prediction_service,
    OEEForecast,
    DropWarning,
    DropRisk
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/oee/predictions", tags=["OEE Predictions"])


# Pydantic models for API responses
class PredictionPoint(BaseModel):
    timestamp: str
    predicted_oee: float
    confidence_interval: Dict[str, float]
    confidence: str
    contributing_factors: Dict[str, float]


class DropWarningResponse(BaseModel):
    warning_id: str
    equipment_id: str
    equipment_name: str
    current_oee: float
    predicted_oee: float
    predicted_drop: float
    drop_risk: str
    expected_time: str
    hours_until_drop: float
    root_causes: List[Dict[str, Any]]
    recommendations: List[str]
    confidence: str
    created_at: str


class OEEForecastResponse(BaseModel):
    equipment_id: str
    equipment_name: str
    current_oee: float
    predictions: List[PredictionPoint]
    drop_warnings: List[DropWarningResponse]
    trend: str
    trend_slope: float
    model_accuracy: float
    last_updated: str


class PredictionSummary(BaseModel):
    total_equipment: int
    equipment_with_warnings: int
    critical_warnings: int
    high_warnings: int
    medium_warnings: int
    average_predicted_oee: float
    worst_predicted_equipment: Optional[Dict[str, Any]]
    best_predicted_equipment: Optional[Dict[str, Any]]
    overall_trend: str
    generated_at: str


@router.get(
    "/{equipment_id}",
    response_model=OEEForecastResponse,
    summary="Get OEE predictions for equipment",
    description="Returns OEE predictions for the next N hours with drop warnings"
)
async def get_equipment_predictions(
    equipment_id: str,
    equipment_name: Optional[str] = Query(None, description="Human-readable equipment name"),
    horizon_hours: int = Query(8, ge=1, le=24, description="Hours to predict ahead"),
    use_cache: bool = Query(True, description="Use cached predictions if available")
):
    """
    Get OEE predictions for a specific equipment.

    Returns:
    - Hourly OEE predictions for the specified horizon
    - Confidence intervals for each prediction
    - Drop warnings if significant drops are predicted
    - Root cause analysis and recommendations
    """
    try:
        forecast = await oee_prediction_service.predict_oee(
            equipment_id=equipment_id,
            equipment_name=equipment_name or equipment_id,
            horizon_hours=horizon_hours,
            use_cache=use_cache
        )

        return oee_prediction_service.to_dict(forecast)

    except Exception as e:
        logger.error(f"Error getting predictions for {equipment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/",
    response_model=List[OEEForecastResponse],
    summary="Get OEE predictions for all equipment",
    description="Returns predictions for multiple equipment in parallel"
)
async def get_all_predictions(
    equipment_ids: Optional[str] = Query(
        None,
        description="Comma-separated equipment IDs. If empty, uses demo equipment."
    ),
    horizon_hours: int = Query(8, ge=1, le=24)
):
    """
    Get OEE predictions for multiple equipment.

    If no equipment_ids provided, returns predictions for demo equipment.
    """
    try:
        # Parse equipment IDs or use demo
        if equipment_ids:
            ids = [id.strip() for id in equipment_ids.split(",")]
        else:
            # Demo equipment
            ids = [
                "PRENSA_01",
                "TORNO_CNC_02",
                "CENTRO_USI_03",
                "INJETORA_04",
                "FORNO_05"
            ]

        names = {
            "PRENSA_01": "Prensa Hidráulica 01",
            "TORNO_CNC_02": "Torno CNC 02",
            "CENTRO_USI_03": "Centro de Usinagem 03",
            "INJETORA_04": "Injetora Plástico 04",
            "FORNO_05": "Forno Industrial 05"
        }

        forecasts = await oee_prediction_service.predict_all_equipment(
            equipment_ids=ids,
            equipment_names=names
        )

        return [oee_prediction_service.to_dict(f) for f in forecasts]

    except Exception as e:
        logger.error(f"Error getting all predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/summary",
    response_model=PredictionSummary,
    summary="Get predictions summary",
    description="Returns aggregated summary of all predictions and warnings"
)
async def get_predictions_summary(
    equipment_ids: Optional[str] = Query(None)
):
    """
    Get aggregated summary of OEE predictions.

    Includes:
    - Count of equipment with warnings
    - Warning breakdown by severity
    - Best/worst performing equipment predictions
    - Overall trend
    """
    try:
        # Get all predictions
        if equipment_ids:
            ids = [id.strip() for id in equipment_ids.split(",")]
        else:
            ids = ["PRENSA_01", "TORNO_CNC_02", "CENTRO_USI_03", "INJETORA_04", "FORNO_05"]

        forecasts = await oee_prediction_service.predict_all_equipment(ids)

        # Calculate summary
        total = len(forecasts)
        with_warnings = sum(1 for f in forecasts if f.drop_warnings)

        critical = 0
        high = 0
        medium = 0

        for f in forecasts:
            for w in f.drop_warnings:
                if w.drop_risk == DropRisk.CRITICAL:
                    critical += 1
                elif w.drop_risk == DropRisk.HIGH:
                    high += 1
                elif w.drop_risk == DropRisk.MEDIUM:
                    medium += 1

        # Average predicted OEE (last prediction for each)
        avg_oee = sum(
            f.predictions[-1].predicted_oee
            for f in forecasts
            if f.predictions
        ) / max(1, len([f for f in forecasts if f.predictions]))

        # Find worst and best
        sorted_forecasts = sorted(
            forecasts,
            key=lambda f: f.predictions[-1].predicted_oee if f.predictions else 100
        )

        worst = None
        best = None

        if sorted_forecasts:
            worst_f = sorted_forecasts[0]
            worst = {
                "equipment_id": worst_f.equipment_id,
                "equipment_name": worst_f.equipment_name,
                "predicted_oee": worst_f.predictions[-1].predicted_oee if worst_f.predictions else None
            }

            best_f = sorted_forecasts[-1]
            best = {
                "equipment_id": best_f.equipment_id,
                "equipment_name": best_f.equipment_name,
                "predicted_oee": best_f.predictions[-1].predicted_oee if best_f.predictions else None
            }

        # Overall trend
        declining = sum(1 for f in forecasts if f.trend == "declining")
        improving = sum(1 for f in forecasts if f.trend == "improving")

        if declining > improving:
            overall_trend = "declining"
        elif improving > declining:
            overall_trend = "improving"
        else:
            overall_trend = "stable"

        return PredictionSummary(
            total_equipment=total,
            equipment_with_warnings=with_warnings,
            critical_warnings=critical,
            high_warnings=high,
            medium_warnings=medium,
            average_predicted_oee=round(avg_oee, 2),
            worst_predicted_equipment=worst,
            best_predicted_equipment=best,
            overall_trend=overall_trend,
            generated_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Error generating predictions summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/warnings/active",
    response_model=List[DropWarningResponse],
    summary="Get active drop warnings",
    description="Returns all active OEE drop warnings sorted by severity"
)
async def get_active_warnings(
    min_risk: str = Query(
        "medium",
        description="Minimum risk level: critical, high, medium, low"
    )
):
    """
    Get all active drop warnings across all equipment.

    Warnings are sorted by:
    1. Risk level (critical first)
    2. Time until drop (soonest first)
    """
    try:
        risk_map = {
            "critical": DropRisk.CRITICAL,
            "high": DropRisk.HIGH,
            "medium": DropRisk.MEDIUM,
            "low": DropRisk.LOW
        }

        min_risk_enum = risk_map.get(min_risk.lower(), DropRisk.MEDIUM)

        warnings = await oee_prediction_service.get_critical_warnings(min_risk_enum)

        return [
            DropWarningResponse(
                warning_id=w.warning_id,
                equipment_id=w.equipment_id,
                equipment_name=w.equipment_name,
                current_oee=round(w.current_oee, 2),
                predicted_oee=round(w.predicted_oee, 2),
                predicted_drop=round(w.predicted_drop, 2),
                drop_risk=w.drop_risk.value,
                expected_time=w.expected_time.isoformat(),
                hours_until_drop=round(w.hours_until_drop, 1),
                root_causes=w.root_causes,
                recommendations=w.recommendations,
                confidence=w.confidence.value,
                created_at=w.created_at.isoformat()
            )
            for w in warnings
        ]

    except Exception as e:
        logger.error(f"Error getting warnings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/warnings/critical",
    response_model=List[DropWarningResponse],
    summary="Get critical warnings only",
    description="Returns only critical and high severity warnings"
)
async def get_critical_warnings():
    """Get only critical and high severity warnings."""
    return await get_active_warnings(min_risk="high")


@router.post(
    "/refresh",
    summary="Force refresh predictions",
    description="Clears cache and regenerates all predictions"
)
async def refresh_predictions(
    background_tasks: BackgroundTasks,
    equipment_ids: Optional[str] = Query(None)
):
    """
    Force refresh of predictions.

    Clears the cache and triggers regeneration of predictions
    for specified equipment (or all if not specified).
    """
    try:
        # Clear cache
        oee_prediction_service._prediction_cache.clear()

        # Parse equipment IDs
        if equipment_ids:
            ids = [id.strip() for id in equipment_ids.split(",")]
        else:
            ids = ["PRENSA_01", "TORNO_CNC_02", "CENTRO_USI_03", "INJETORA_04", "FORNO_05"]

        # Trigger refresh in background
        async def refresh_task():
            await oee_prediction_service.predict_all_equipment(ids)

        background_tasks.add_task(refresh_task)

        return {
            "status": "refreshing",
            "equipment_count": len(ids),
            "message": "Predictions are being regenerated in the background"
        }

    except Exception as e:
        logger.error(f"Error refreshing predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    summary="Check prediction service health",
    description="Returns health status of the prediction service"
)
async def prediction_service_health():
    """Check health of the OEE prediction service."""
    try:
        # Check if service is responsive
        cache_size = len(oee_prediction_service._prediction_cache)
        model_count = len(oee_prediction_service.models)

        return {
            "status": "healthy",
            "tensorflow_available": oee_prediction_service.models is not None,
            "cached_predictions": cache_size,
            "trained_models": model_count,
            "lookback_hours": oee_prediction_service.lookback_hours,
            "prediction_horizon": oee_prediction_service.prediction_horizon,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
