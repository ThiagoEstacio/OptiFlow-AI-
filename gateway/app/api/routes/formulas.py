"""
Formula Engine API - Local Formula Evaluation
==============================================

Gateway-only formula evaluation for calculated tags.
Provides low-latency local computation.

NOTE: Formula DEFINITIONS should be managed in Backend.
      This API only handles LOCAL EVALUATION.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import math

from app.core.logger import logger

router = APIRouter(prefix="/formulas", tags=["Formulas"])


# ==================== Models ====================

class FormulaTestRequest(BaseModel):
    """Test formula with sample values"""
    expression: str
    sample_values: Dict[str, Any]  # {"tag_name": value}


class FormulaTestResponse(BaseModel):
    """Formula test result"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    expression: str
    inputs: Dict[str, Any]


# ==================== Safe Evaluation Context ====================

SAFE_BUILTINS = {
    'abs': abs,
    'min': min,
    'max': max,
    'round': round,
    'sum': sum,
    'len': len,
    'int': int,
    'float': float,
    'bool': bool,
    'str': str,
}

SAFE_MATH = {
    'sqrt': math.sqrt,
    'log': math.log,
    'log10': math.log10,
    'exp': math.exp,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'asin': math.asin,
    'acos': math.acos,
    'atan': math.atan,
    'atan2': math.atan2,
    'pow': math.pow,
    'ceil': math.ceil,
    'floor': math.floor,
    'pi': math.pi,
    'e': math.e,
}


def safe_eval(expression: str, tag_values: Dict[str, Any]) -> Any:
    """
    Safely evaluate a formula expression.

    Allowed:
    - Math operations: +, -, *, /, **, %
    - Tag values: tags['TAG_NAME']
    - Math functions: math.sqrt(), math.log(), etc
    - Built-ins: abs(), min(), max(), round()

    Blocked:
    - import statements
    - __builtins__
    - file operations
    - exec/eval
    """
    safe_context = {
        '__builtins__': {},
        'tags': tag_values,
        'math': SAFE_MATH,
        **SAFE_BUILTINS,
    }

    return eval(expression, safe_context)


# ==================== Endpoints ====================

@router.post("/test", response_model=FormulaTestResponse)
async def test_formula(request: FormulaTestRequest):
    """
    Test formula expression with sample values.

    This endpoint allows testing formulas before deployment.

    **Example Request**:
    ```json
    {
      "expression": "tags['TEMP_C'] * 1.8 + 32",
      "sample_values": {"TEMP_C": 100}
    }
    ```

    **Example Response**:
    ```json
    {
      "success": true,
      "result": 212.0,
      "expression": "tags['TEMP_C'] * 1.8 + 32",
      "inputs": {"TEMP_C": 100}
    }
    ```

    **Supported Syntax**:
    - Tag access: `tags['TAG_NAME']`
    - Math: `+`, `-`, `*`, `/`, `**`, `%`
    - Functions: `abs()`, `min()`, `max()`, `round()`, `math.sqrt()`, etc
    """
    try:
        result = safe_eval(request.expression, request.sample_values)

        logger.debug(f"Formula test: {request.expression} = {result}")

        return FormulaTestResponse(
            success=True,
            result=result,
            expression=request.expression,
            inputs=request.sample_values
        )

    except Exception as e:
        logger.warning(f"Formula test failed: {request.expression} - {e}")

        return FormulaTestResponse(
            success=False,
            error=str(e),
            expression=request.expression,
            inputs=request.sample_values
        )


@router.get("/examples")
async def get_formula_examples():
    """
    Get formula syntax examples.

    Returns common formula patterns for reference.
    """
    return {
        "examples": [
            {
                "name": "Temperature Conversion (C to F)",
                "expression": "tags['TEMP_C'] * 1.8 + 32",
                "description": "Convert Celsius to Fahrenheit"
            },
            {
                "name": "Pressure Conversion (bar to psi)",
                "expression": "tags['PRESSURE_BAR'] * 14.5038",
                "description": "Convert bar to PSI"
            },
            {
                "name": "Flow Rate Average",
                "expression": "(tags['FLOW_1'] + tags['FLOW_2']) / 2",
                "description": "Average of two flow sensors"
            },
            {
                "name": "Power Calculation",
                "expression": "tags['VOLTAGE'] * tags['CURRENT'] * tags['POWER_FACTOR']",
                "description": "Calculate electrical power"
            },
            {
                "name": "Differential Pressure",
                "expression": "tags['PRESSURE_IN'] - tags['PRESSURE_OUT']",
                "description": "Calculate pressure drop"
            },
            {
                "name": "Percentage Calculation",
                "expression": "(tags['LEVEL'] / tags['MAX_LEVEL']) * 100",
                "description": "Calculate tank level percentage"
            },
            {
                "name": "Square Root (for flow)",
                "expression": "math.sqrt(tags['DP_SENSOR']) * 100",
                "description": "Square root for differential pressure flow"
            },
            {
                "name": "Conditional (clamping)",
                "expression": "max(0, min(100, tags['VALUE']))",
                "description": "Clamp value between 0 and 100"
            },
            {
                "name": "Running Average",
                "expression": "(tags['V1'] + tags['V2'] + tags['V3'] + tags['V4']) / 4",
                "description": "Average of 4 values"
            },
            {
                "name": "Efficiency Calculation",
                "expression": "(tags['OUTPUT'] / tags['INPUT']) * 100 if tags['INPUT'] > 0 else 0",
                "description": "Calculate efficiency percentage"
            }
        ],
        "available_functions": {
            "math": list(SAFE_MATH.keys()),
            "builtins": list(SAFE_BUILTINS.keys())
        },
        "syntax_notes": [
            "Access tags using: tags['TAG_NAME']",
            "Use standard Python math operators: +, -, *, /, **, %",
            "Math functions available via math namespace: math.sqrt(), math.sin(), etc",
            "Conditional expressions supported: x if condition else y"
        ]
    }


@router.get("/engine/status")
async def get_formula_engine_status():
    """
    Get formula engine status.

    Returns information about the local formula evaluation engine.
    """
    try:
        # Try to import formula engine
        from app.services.formula_engine import get_formula_engine
        engine = get_formula_engine()

        return {
            "status": "running",
            "registered_formulas": engine.formula_count if hasattr(engine, 'formula_count') else 0,
            "evaluations": engine.evaluation_count if hasattr(engine, 'evaluation_count') else 0,
            "errors": engine.error_count if hasattr(engine, 'error_count') else 0,
            "avg_eval_time_ms": engine.avg_eval_time_ms if hasattr(engine, 'avg_eval_time_ms') else 0,
            "note": "Formula definitions managed by Backend. Gateway handles local evaluation only."
        }

    except ImportError:
        return {
            "status": "not_initialized",
            "registered_formulas": 0,
            "evaluations": 0,
            "errors": 0,
            "avg_eval_time_ms": 0,
            "note": "Formula engine not loaded. Will initialize when formulas are synced from Backend."
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
