"""
Advanced Features API Endpoints

Production-ready advanced features:
- Gateway testing and production tools
- ML failure prediction
- Loading operation optimization
- Report generation (PDF/Excel)
- Mobile-optimized endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from datetime import datetime, date
import logging

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.gateway_production_manager import GatewayProductionManager
from app.services.ml_failure_predictor import MLFailurePredictor
from app.services.loading_optimizer import LoadingOptimizer
from app.services.report_generator import ReportGenerator

router = APIRouter()
logger = logging.getLogger(__name__)


# Gateway Production Tools


@router.post("/gateway/test", response_model=Dict[str, Any])
async def test_gateway_connection(
    gateway_config: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Test gateway connection before deployment.

    Performs:
    - Connection test
    - Read performance test
    - Reliability test with reconnection
    """
    try:
        manager = GatewayProductionManager(db)
        result = await manager.test_gateway_connection(gateway_config)

        logger.info(f"Gateway test completed: {result.get('overall_status')}")

        return result

    except Exception as e:
        logger.error(f"Error testing gateway: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gateway/validate", response_model=Dict[str, Any])
async def validate_gateway_configuration(
    gateway_config: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Validate gateway configuration.

    Checks for:
    - Required fields
    - Valid data types
    - Tag configuration
    - Best practices
    """
    try:
        manager = GatewayProductionManager(db)
        result = await manager.validate_configuration(gateway_config)

        return result

    except Exception as e:
        logger.error(f"Error validating configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gateway/benchmark/{gateway_id}", response_model=Dict[str, Any])
async def benchmark_gateway(
    gateway_id: int,
    duration_seconds: int = Query(60, ge=10, le=300),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Benchmark gateway performance.

    Tests gateway under load for specified duration.
    """
    try:
        manager = GatewayProductionManager(db)
        result = await manager.benchmark_gateway(gateway_id, duration_seconds)

        return result

    except Exception as e:
        logger.error(f"Error benchmarking gateway: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gateway/template/{gateway_type}", response_model=Dict[str, Any])
async def get_production_config_template(
    gateway_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get production-ready configuration template.

    Returns template with best practices for production deployment.
    """
    try:
        manager = GatewayProductionManager(db)
        template = await manager.create_production_config_template(gateway_type)

        return template

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ML Failure Prediction


@router.post("/ml/train", response_model=Dict[str, Any])
async def train_ml_model(
    asset_type: Optional[str] = None,
    training_days: int = Query(180, ge=30, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Train ML failure prediction model.

    Uses historical data to train Random Forest classifier.
    """
    try:
        predictor = MLFailurePredictor(db)
        result = await predictor.train_model(asset_type, training_days)

        logger.info(f"ML model trained: {result.get('status')}")

        return result

    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error(f"Error training ML model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/predict/{asset_id}", response_model=Dict[str, Any])
async def predict_failure(
    asset_id: str,
    prediction_horizon_hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Predict equipment failure using ML.

    Returns:
    - Failure probability
    - Risk level
    - Estimated time to failure
    - Recommendations
    """
    try:
        predictor = MLFailurePredictor(db)
        result = await predictor.predict_failure(asset_id, prediction_horizon_hours)

        logger.info(f"ML prediction for {asset_id}: {result.get('risk_level')}")

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error(f"Error predicting failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Loading Optimization


@router.get("/optimize/berths/{site_id}", response_model=Dict[str, Any])
async def optimize_berth_allocation(
    site_id: int,
    days_ahead: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Optimize berth allocation for scheduled ships.

    Uses greedy algorithm to minimize total waiting time.
    """
    try:
        optimizer = LoadingOptimizer(db)
        result = await optimizer.optimize_berth_allocation(site_id, days_ahead)

        logger.info(f"Berth optimization complete: {result.get('ships_scheduled')} ships")

        return result

    except Exception as e:
        logger.error(f"Error optimizing berths: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/optimize/loading/{ship_loading_id}", response_model=Dict[str, Any])
async def optimize_loading_sequence(
    ship_loading_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Optimize loading sequence for a ship.

    Returns optimal:
    - Silo selection
    - Loading order
    - Timeline
    """
    try:
        optimizer = LoadingOptimizer(db)
        result = await optimizer.optimize_loading_sequence(ship_loading_id)

        logger.info(f"Loading sequence optimized for ship {ship_loading_id}")

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error optimizing loading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize/loading-rate/{ship_loading_id}", response_model=Dict[str, Any])
async def calculate_optimal_loading_rate(
    ship_loading_id: int,
    current_weather: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Calculate optimal loading rate based on conditions.

    Considers:
    - Weather (wind, rain)
    - Ship characteristics
    - Product type
    """
    try:
        optimizer = LoadingOptimizer(db)
        result = await optimizer.calculate_optimal_loading_rate(
            ship_loading_id,
            current_weather
        )

        logger.info(f"Optimal loading rate calculated: {result.get('optimal_loading_rate')} t/h")

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating loading rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Report Generation


@router.get("/reports/daily-pdf")
async def generate_daily_pdf(
    site_id: int,
    operation_date: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate PDF report for daily operations.

    Returns PDF file for download.
    """
    try:
        generator = ReportGenerator(db)
        filename = await generator.generate_daily_operations_pdf(site_id, operation_date)

        filepath = generator.get_report_path(filename)

        logger.info(f"Daily PDF generated: {filename}")

        return FileResponse(
            path=filepath,
            media_type='application/pdf',
            filename=filename
        )

    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/operations-excel")
async def generate_operations_excel(
    site_id: int,
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate Excel report for date range.

    Includes:
    - Summary sheet
    - Truck entries
    - Ship loadings
    """
    try:
        generator = ReportGenerator(db)
        filename = await generator.generate_daily_operations_excel(
            site_id,
            start_date,
            end_date
        )

        filepath = generator.get_report_path(filename)

        logger.info(f"Excel report generated: {filename}")

        return FileResponse(
            path=filepath,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=filename
        )

    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating Excel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mobile-Optimized Endpoints


@router.get("/mobile/summary/{site_id}", response_model=Dict[str, Any])
async def get_mobile_summary(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get mobile-optimized summary for field operators.

    Returns lightweight data optimized for mobile devices.
    """
    try:
        from sqlalchemy import select, and_, func
        from app.models.operational_data import TruckEntry, ShipLoading, DailyOperations
        from datetime import date

        today = date.today()

        # Get today's operations
        result = await db.execute(
            select(DailyOperations).where(
                and_(
                    DailyOperations.site_id == site_id,
                    DailyOperations.operation_date == today
                )
            )
        )
        daily_ops = result.scalar_one_or_none()

        # Get active ship loadings
        ship_result = await db.execute(
            select(ShipLoading).where(
                and_(
                    ShipLoading.site_id == site_id,
                    ShipLoading.status.in_(["loading", "berthing"])
                )
            ).limit(5)
        )
        active_ships = ship_result.scalars().all()

        # Get recent trucks (last hour)
        from datetime import datetime, timedelta
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        truck_result = await db.execute(
            select(func.count(TruckEntry.id)).where(
                and_(
                    TruckEntry.site_id == site_id,
                    TruckEntry.entry_time >= one_hour_ago
                )
            )
        )
        trucks_last_hour = truck_result.scalar() or 0

        return {
            "site_id": site_id,
            "timestamp": datetime.utcnow().isoformat(),
            "today": {
                "trucks_total": daily_ops.trucks_received if daily_ops else 0,
                "trucks_last_hour": trucks_last_hour,
                "tonnage_loaded": daily_ops.total_tonnage_loaded if daily_ops else 0,
                "ships_loading": daily_ops.ships_loading if daily_ops else 0,
            },
            "active_ships": [
                {
                    "id": ship.id,
                    "name": ship.ship_name,
                    "berth": ship.berth_number,
                    "progress": round((ship.loaded_tonnage / ship.target_tonnage) * 100, 1) if ship.target_tonnage > 0 else 0,
                    "status": ship.status,
                }
                for ship in active_ships
            ],
            "alerts": [],  # TODO: Fetch critical alerts
        }

    except Exception as e:
        logger.error(f"Error getting mobile summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mobile/ship-status/{ship_loading_id}", response_model=Dict[str, Any])
async def get_mobile_ship_status(
    ship_loading_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get mobile-optimized ship loading status.

    Lightweight data for mobile monitoring.
    """
    try:
        from sqlalchemy import select
        from app.models.operational_data import ShipLoading

        result = await db.execute(
            select(ShipLoading).where(ShipLoading.id == ship_loading_id)
        )
        ship = result.scalar_one_or_none()

        if not ship:
            raise HTTPException(status_code=404, detail="Ship loading not found")

        progress = 0
        if ship.target_tonnage > 0:
            progress = (ship.loaded_tonnage / ship.target_tonnage) * 100

        eta = None
        if ship.loading_rate_avg and ship.loading_rate_avg > 0:
            remaining = ship.target_tonnage - ship.loaded_tonnage
            hours_remaining = remaining / ship.loading_rate_avg
            eta = datetime.utcnow() + timedelta(hours=hours_remaining)

        return {
            "id": ship.id,
            "ship_name": ship.ship_name,
            "berth_number": ship.berth_number,
            "status": ship.status,
            "progress_percent": round(progress, 1),
            "loaded_tonnage": ship.loaded_tonnage,
            "target_tonnage": ship.target_tonnage,
            "remaining_tonnage": ship.target_tonnage - ship.loaded_tonnage,
            "loading_rate": ship.loading_rate_avg,
            "eta": eta.isoformat() if eta else None,
            "updated_at": ship.updated_at.isoformat() if ship.updated_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ship status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
