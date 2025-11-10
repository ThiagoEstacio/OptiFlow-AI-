"""
Failure Generation System for OptiFlow Simulator

This package implements realistic equipment failure simulation based on:
- Health degradation (MTBF decreases with health)
- Operating time and cycles
- Environmental conditions (temperature, humidity, dust)
- Stress events (starts/stops, overloads)
"""

from .failure_generator import FailureGenerator
from .failure_models import (
    BeltFailureModel,
    BearingFailureModel,
    MotorFailureModel,
    SensorFailureModel
)
from .environmental_factors import EnvironmentalFactors

__all__ = [
    'FailureGenerator',
    'BeltFailureModel',
    'BearingFailureModel',
    'MotorFailureModel',
    'SensorFailureModel',
    'EnvironmentalFactors'
]
