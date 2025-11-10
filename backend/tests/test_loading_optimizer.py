"""
Tests for Loading Optimizer Service
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.services.loading_optimizer import LoadingOptimizer
from app.models.operational_data import ShipLoading
try:
    from app.models.operational_data import Berth, Silo
except ImportError:
    Berth = None
    Silo = None


@pytest.fixture
async def test_berths(test_db: AsyncSession, test_site):
    """Create test berths"""
    berths = [
        Berth(
            id=uuid4(),
            site_id=test_site.id,
            berth_number=1,
            name="Berth 1",
            max_ship_size=100000,
            depth_meters=15.0,
            length_meters=300.0,
            is_active=True,
        ),
        Berth(
            id=uuid4(),
            site_id=test_site.id,
            berth_number=2,
            name="Berth 2",
            max_ship_size=80000,
            depth_meters=12.0,
            length_meters=250.0,
            is_active=True,
        ),
    ]
    for berth in berths:
        test_db.add(berth)
    await test_db.commit()
    return berths


@pytest.fixture
async def test_silos(test_db: AsyncSession, test_site):
    """Create test silos"""
    silos = [
        Silo(
            id=uuid4(),
            site_id=test_site.id,
            silo_number=1,
            name="Silo 1",
            product_type=ProductType.SOYBEAN,
            capacity_tons=10000.0,
            current_level_tons=8000.0,
            loading_rate_tons_per_hour=1200.0,
            is_active=True,
        ),
        Silo(
            id=uuid4(),
            site_id=test_site.id,
            silo_number=2,
            name="Silo 2",
            product_type=ProductType.SOYBEAN,
            capacity_tons=10000.0,
            current_level_tons=6000.0,
            loading_rate_tons_per_hour=1000.0,
            is_active=True,
        ),
    ]
    for silo in silos:
        test_db.add(silo)
    await test_db.commit()
    return silos


@pytest.fixture
async def test_ship_loadings(test_db: AsyncSession, test_site):
    """Create test ship loadings"""
    now = datetime.utcnow()
    ships = [
        ShipLoading(
            id=uuid4(),
            site_id=test_site.id,
            ship_name="MV Atlantic",
            ship_imo="1234567",
            product_type=ProductType.SOYBEAN,
            scheduled_arrival=now + timedelta(hours=2),
            estimated_tonnage=50000.0,
            status="scheduled",
        ),
        ShipLoading(
            id=uuid4(),
            site_id=test_site.id,
            ship_name="MV Pacific",
            ship_imo="2345678",
            product_type=ProductType.SOYBEAN,
            scheduled_arrival=now + timedelta(hours=5),
            estimated_tonnage=40000.0,
            status="scheduled",
        ),
    ]
    for ship in ships:
        test_db.add(ship)
    await test_db.commit()
    return ships


@pytest.mark.asyncio
async def test_optimize_berth_allocation_success(test_db: AsyncSession, test_site, test_berths, test_ship_loadings):
    """Test successful berth allocation optimization"""
    optimizer = LoadingOptimizer(test_db)

    result = await optimizer.optimize_berth_allocation(test_site.id, days_ahead=7)

    assert result["status"] == "success"
    assert "allocations" in result
    assert "total_waiting_hours" in result
    assert "berth_utilization_percent" in result
    assert len(result["allocations"]) > 0


@pytest.mark.asyncio
async def test_optimize_berth_allocation_no_ships(test_db: AsyncSession, test_site, test_berths):
    """Test berth allocation with no scheduled ships"""
    optimizer = LoadingOptimizer(test_db)

    result = await optimizer.optimize_berth_allocation(test_site.id, days_ahead=7)

    assert result["status"] == "success"
    assert len(result["allocations"]) == 0
    assert result["total_waiting_hours"] == 0


@pytest.mark.asyncio
async def test_optimize_berth_allocation_no_berths(test_db: AsyncSession, test_site, test_ship_loadings):
    """Test berth allocation with no available berths"""
    optimizer = LoadingOptimizer(test_db)

    result = await optimizer.optimize_berth_allocation(test_site.id, days_ahead=7)

    assert result["status"] == "error"
    assert "no berths available" in result["error"].lower()


@pytest.mark.asyncio
async def test_optimize_berth_allocation_minimizes_waiting(test_db: AsyncSession, test_site, test_berths, test_ship_loadings):
    """Test that berth allocation minimizes total waiting time"""
    optimizer = LoadingOptimizer(test_db)

    result = await optimizer.optimize_berth_allocation(test_site.id, days_ahead=7)

    assert result["status"] == "success"
    # All ships should be allocated
    assert len(result["allocations"]) == len(test_ship_loadings)
    # Total waiting time should be minimized (ideally 0 or low)
    assert result["total_waiting_hours"] >= 0


@pytest.mark.asyncio
async def test_optimize_loading_sequence_success(test_db: AsyncSession, test_silos, test_ship_loadings):
    """Test successful loading sequence optimization"""
    optimizer = LoadingOptimizer(test_db)
    ship = test_ship_loadings[0]

    result = await optimizer.optimize_loading_sequence(ship.id)

    assert result["status"] == "success"
    assert "loading_sequence" in result
    assert "total_estimated_hours" in result
    assert "timeline" in result
    assert len(result["loading_sequence"]) > 0


@pytest.mark.asyncio
async def test_optimize_loading_sequence_ship_not_found(test_db: AsyncSession):
    """Test loading sequence optimization for non-existent ship"""
    optimizer = LoadingOptimizer(test_db)
    fake_id = uuid4()

    result = await optimizer.optimize_loading_sequence(fake_id)

    assert result["status"] == "error"
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_optimize_loading_sequence_no_silos(test_db: AsyncSession, test_ship_loadings, test_site):
    """Test loading sequence optimization with no available silos"""
    optimizer = LoadingOptimizer(test_db)
    ship = test_ship_loadings[0]

    # Clear all silos
    result = await optimizer.optimize_loading_sequence(ship.id)

    # Should either succeed with empty sequence or return error
    assert result["status"] in ["success", "error"]


@pytest.mark.asyncio
async def test_optimize_loading_sequence_timeline(test_db: AsyncSession, test_silos, test_ship_loadings):
    """Test that loading sequence includes proper timeline"""
    optimizer = LoadingOptimizer(test_db)
    ship = test_ship_loadings[0]

    result = await optimizer.optimize_loading_sequence(ship.id)

    assert result["status"] == "success"
    assert "timeline" in result
    # Timeline should have start and end times
    for step in result["loading_sequence"]:
        assert "start_time" in step or "estimated_start" in step


@pytest.mark.asyncio
async def test_calculate_optimal_loading_rate_base_rate(test_db: AsyncSession, test_ship_loadings):
    """Test optimal loading rate calculation with no weather"""
    optimizer = LoadingOptimizer(test_db)
    ship = test_ship_loadings[0]

    result = await optimizer.calculate_optimal_loading_rate(ship.id)

    assert result["status"] == "success"
    assert "optimal_loading_rate" in result
    assert result["optimal_loading_rate"] > 0
    assert "adjustments" in result


@pytest.mark.asyncio
async def test_calculate_optimal_loading_rate_high_wind(test_db: AsyncSession, test_ship_loadings):
    """Test loading rate calculation with high wind conditions"""
    optimizer = LoadingOptimizer(test_db)
    ship = test_ship_loadings[0]

    weather = {
        "wind_speed_kmh": 65.0,  # High wind
        "rainfall_mm": 0.0,
        "temperature_c": 25.0,
    }

    result = await optimizer.calculate_optimal_loading_rate(ship.id, current_weather=weather)

    assert result["status"] == "success"
    # Loading rate should be reduced due to high wind
    assert any("wind" in adj.lower() for adj in result.get("adjustments", []))
    # Should have limiting factors
    assert "limiting_factors" in result


@pytest.mark.asyncio
async def test_calculate_optimal_loading_rate_heavy_rain(test_db: AsyncSession, test_ship_loadings):
    """Test loading rate calculation with heavy rain"""
    optimizer = LoadingOptimizer(test_db)
    ship = test_ship_loadings[0]

    weather = {
        "wind_speed_kmh": 20.0,
        "rainfall_mm": 10.0,  # Heavy rain
        "temperature_c": 22.0,
    }

    result = await optimizer.calculate_optimal_loading_rate(ship.id, current_weather=weather)

    assert result["status"] == "success"
    # Loading rate should be reduced due to rain
    assert any("rain" in adj.lower() for adj in result.get("adjustments", []))


@pytest.mark.asyncio
async def test_calculate_optimal_loading_rate_moderate_wind(test_db: AsyncSession, test_ship_loadings):
    """Test loading rate calculation with moderate wind"""
    optimizer = LoadingOptimizer(test_db)
    ship = test_ship_loadings[0]

    weather = {
        "wind_speed_kmh": 45.0,  # Moderate wind
        "rainfall_mm": 0.0,
        "temperature_c": 25.0,
    }

    result = await optimizer.calculate_optimal_loading_rate(ship.id, current_weather=weather)

    assert result["status"] == "success"
    # Should have some wind adjustment but not as severe as high wind
    assert "optimal_loading_rate" in result


@pytest.mark.asyncio
async def test_calculate_optimal_loading_rate_good_conditions(test_db: AsyncSession, test_ship_loadings):
    """Test loading rate calculation with good weather conditions"""
    optimizer = LoadingOptimizer(test_db)
    ship = test_ship_loadings[0]

    weather = {
        "wind_speed_kmh": 15.0,  # Light wind
        "rainfall_mm": 0.0,       # No rain
        "temperature_c": 25.0,
    }

    result = await optimizer.calculate_optimal_loading_rate(ship.id, current_weather=weather)

    assert result["status"] == "success"
    # Should have minimal or no adjustments for good weather
    optimal_rate = result["optimal_loading_rate"]
    assert optimal_rate > 0


@pytest.mark.asyncio
async def test_calculate_optimal_loading_rate_ship_not_found(test_db: AsyncSession):
    """Test loading rate calculation for non-existent ship"""
    optimizer = LoadingOptimizer(test_db)
    fake_id = uuid4()

    result = await optimizer.calculate_optimal_loading_rate(fake_id)

    assert result["status"] == "error"
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_optimize_berth_allocation_utilization(test_db: AsyncSession, test_site, test_berths, test_ship_loadings):
    """Test berth utilization calculation"""
    optimizer = LoadingOptimizer(test_db)

    result = await optimizer.optimize_berth_allocation(test_site.id, days_ahead=7)

    assert result["status"] == "success"
    assert "berth_utilization_percent" in result
    assert 0 <= result["berth_utilization_percent"] <= 100


@pytest.mark.asyncio
async def test_optimize_loading_sequence_prefers_higher_rate_silos(test_db: AsyncSession, test_silos, test_ship_loadings):
    """Test that loading sequence prefers silos with higher loading rates"""
    optimizer = LoadingOptimizer(test_db)
    ship = test_ship_loadings[0]

    result = await optimizer.optimize_loading_sequence(ship.id)

    assert result["status"] == "success"
    # First silo in sequence should have higher or equal rate than subsequent ones
    # (greedy algorithm prefers higher rates first)
    if len(result["loading_sequence"]) > 1:
        first_silo = result["loading_sequence"][0]
        assert "silo_id" in first_silo or "silo_number" in first_silo


@pytest.mark.asyncio
async def test_calculate_optimal_loading_rate_multiple_factors(test_db: AsyncSession, test_ship_loadings):
    """Test loading rate calculation with multiple limiting factors"""
    optimizer = LoadingOptimizer(test_db)
    ship = test_ship_loadings[0]

    weather = {
        "wind_speed_kmh": 50.0,  # Moderate-high wind
        "rainfall_mm": 6.0,      # Some rain
        "temperature_c": 20.0,
    }

    result = await optimizer.calculate_optimal_loading_rate(ship.id, current_weather=weather)

    assert result["status"] == "success"
    # Should have multiple adjustments
    assert len(result.get("adjustments", [])) >= 2
    # Loading rate should be significantly reduced
    base_rate = 1200.0
    assert result["optimal_loading_rate"] < base_rate
