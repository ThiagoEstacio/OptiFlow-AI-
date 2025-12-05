"""
Machine Learning Services Module
================================

Sprint 2-3: ML & Prediction

This module contains:
- MELH-001: Anomaly Detection (Isolation Forest)
- MELH-002: Energy Forecast (LSTM)
- MELH-003: Ishikawa Dynamic Analysis
- MELH-004: Cross-Equipment Correlation
"""

from .anomaly_detection import (
    AnomalyDetectionService,
    AnomalyPrediction,
    get_anomaly_service,
)

from .energy_forecast import (
    EnergyForecastService,
    EnergyForecast,
    get_energy_forecast_service,
)

from .ishikawa_analysis import (
    IshikawaAnalysisService,
    IshikawaDiagram,
    IshikawaCategory,
    RootCause,
    get_ishikawa_service,
)

from .cross_equipment_correlation import (
    CrossEquipmentCorrelationService,
    CorrelationMatrix,
    EquipmentCorrelation,
    CorrelationType,
    get_correlation_service,
)

__all__ = [
    # MELH-001: Anomaly Detection
    "AnomalyDetectionService",
    "AnomalyPrediction",
    "get_anomaly_service",
    # MELH-002: Energy Forecast
    "EnergyForecastService",
    "EnergyForecast",
    "get_energy_forecast_service",
    # MELH-003: Ishikawa Analysis
    "IshikawaAnalysisService",
    "IshikawaDiagram",
    "IshikawaCategory",
    "RootCause",
    "get_ishikawa_service",
    # MELH-004: Cross-Equipment Correlation
    "CrossEquipmentCorrelationService",
    "CorrelationMatrix",
    "EquipmentCorrelation",
    "CorrelationType",
    "get_correlation_service",
]
