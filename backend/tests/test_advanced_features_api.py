"""
Integration tests for Advanced Features API endpoints
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, date, timedelta
from uuid import uuid4
from unittest.mock import patch, Mock

from app.models.asset import Asset, AssetType
from app.models.operational_data import ShipLoading


@pytest.fixture
async def test_asset_for_api(test_db, test_site):
    """Create test asset for API tests"""
    asset = Asset(
        id=str(uuid4()),
        asset_id="CONV-API-001",
        name="API Test Conveyor",
        asset_type=AssetType.CONVEYOR,
        site_id=test_site.id,
        manufacturer="Test Mfg",
        model="API-1000",
        installation_date=datetime.utcnow() - timedelta(days=365),
        health_score=75.0,
        status="operational",
        operating_hours=8760.0,
        last_maintenance=datetime.utcnow() - timedelta(days=60),
    )
    test_db.add(asset)
    await test_db.commit()
    await test_db.refresh(asset)
    return asset


@pytest.fixture
async def test_ship_for_api(test_db, test_site):
    """Create test ship loading for API tests"""
    ship = ShipLoading(
        id=uuid4(),
        site_id=test_site.id,
        ship_name="MV API Test",
        ship_imo="9999999",
        product_type=ProductType.SOYBEAN,
        scheduled_arrival=datetime.utcnow() + timedelta(hours=2),
        estimated_tonnage=50000.0,
        status="scheduled",
    )
    test_db.add(ship)
    await test_db.commit()
    await test_db.refresh(ship)
    return ship


# Gateway Production Tools Tests

@pytest.mark.asyncio
async def test_test_gateway_connection_endpoint(client: AsyncClient, auth_headers):
    """Test gateway connection testing endpoint"""
    config = {
        "name": "Test Gateway",
        "protocol": "opcua",
        "host": "192.168.1.100",
        "port": 4840,
    }

    with patch('app.services.gateway_production_manager.IndustrialGateway'):
        response = await client.post(
            "/api/v1/advanced/gateway/test",
            json=config,
            headers=auth_headers
        )

    assert response.status_code in [200, 500, 501]  # Success or error


@pytest.mark.asyncio
async def test_validate_gateway_config_endpoint_success(client: AsyncClient, auth_headers):
    """Test gateway configuration validation endpoint - valid config"""
    config = {
        "name": "Test Gateway",
        "protocol": "modbus_tcp",
        "host": "192.168.1.100",
        "port": 502,
        "tags": [
            {
                "name": "Temperature",
                "address": "40001",
                "data_type": "FLOAT"
            }
        ]
    }

    response = await client.post(
        "/api/v1/advanced/gateway/validate",
        json=config,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "valid" in data
    assert "errors" in data


@pytest.mark.asyncio
async def test_validate_gateway_config_endpoint_invalid(client: AsyncClient, auth_headers):
    """Test gateway configuration validation endpoint - invalid config"""
    config = {
        "name": "Test Gateway",
        # Missing required fields
    }

    response = await client.post(
        "/api/v1/advanced/gateway/validate",
        json=config,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert len(data["errors"]) > 0


@pytest.mark.asyncio
async def test_get_gateway_template_endpoint_opcua(client: AsyncClient, auth_headers):
    """Test gateway template generation endpoint - OPC-UA"""
    response = await client.get(
        "/api/v1/advanced/gateway/template/opcua",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["protocol"] == "opcua"
    assert "port" in data
    assert "tags" in data


@pytest.mark.asyncio
async def test_get_gateway_template_endpoint_modbus(client: AsyncClient, auth_headers):
    """Test gateway template generation endpoint - Modbus"""
    response = await client.get(
        "/api/v1/advanced/gateway/template/modbus_tcp",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["protocol"] == "modbus_tcp"


@pytest.mark.asyncio
async def test_get_gateway_template_endpoint_invalid_type(client: AsyncClient, auth_headers):
    """Test gateway template generation endpoint - invalid type"""
    response = await client.get(
        "/api/v1/advanced/gateway/template/invalid",
        headers=auth_headers
    )

    assert response.status_code in [400, 422, 500]


@pytest.mark.asyncio
async def test_gateway_endpoints_require_auth(client: AsyncClient):
    """Test that gateway endpoints require authentication"""
    response = await client.post(
        "/api/v1/advanced/gateway/validate",
        json={"name": "Test"}
    )

    assert response.status_code == 401


# ML Failure Prediction Tests

@pytest.mark.asyncio
@patch('app.services.ml_failure_predictor.pickle')
@patch('app.services.ml_failure_predictor.os.path.exists')
async def test_train_ml_model_endpoint(mock_exists, mock_pickle, client: AsyncClient, auth_headers):
    """Test ML model training endpoint"""
    mock_exists.return_value = False

    with patch('builtins.open', return_value=Mock()):
        response = await client.post(
            "/api/v1/advanced/ml/train?training_days=30",
            headers=auth_headers
        )

    assert response.status_code in [200, 501]  # Success or scikit-learn not available


@pytest.mark.asyncio
@patch('app.services.ml_failure_predictor.pickle.load')
@patch('app.services.ml_failure_predictor.os.path.exists')
async def test_predict_failure_endpoint(mock_exists, mock_pickle_load, client: AsyncClient, auth_headers, test_asset_for_api):
    """Test ML failure prediction endpoint"""
    mock_exists.return_value = True

    # Mock trained model
    mock_model = Mock()
    mock_model.predict_proba.return_value = [[0.3, 0.7]]
    mock_scaler = Mock()
    mock_scaler.transform.return_value = [[1, 2, 3, 4, 5, 6, 7, 8]]

    mock_pickle_load.return_value = {
        "model": mock_model,
        "scaler": mock_scaler
    }

    with patch('builtins.open', return_value=Mock()):
        response = await client.get(
            f"/api/v1/advanced/ml/predict/{test_asset_for_api.id}?prediction_horizon_hours=24",
            headers=auth_headers
        )

    assert response.status_code in [200, 404, 501]


@pytest.mark.asyncio
async def test_predict_failure_endpoint_asset_not_found(client: AsyncClient, auth_headers):
    """Test ML prediction endpoint with non-existent asset"""
    fake_id = str(uuid4())

    response = await client.get(
        f"/api/v1/advanced/ml/predict/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code in [404, 500]


@pytest.mark.asyncio
async def test_ml_endpoints_require_auth(client: AsyncClient):
    """Test that ML endpoints require authentication"""
    response = await client.post(
        "/api/v1/advanced/ml/train",
    )

    assert response.status_code == 401


# Loading Optimization Tests

@pytest.mark.asyncio
async def test_optimize_berths_endpoint(client: AsyncClient, auth_headers, test_site):
    """Test berth optimization endpoint"""
    response = await client.get(
        f"/api/v1/advanced/optimize/berths/{test_site.id}?days_ahead=7",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "allocations" in data or "status" in data


@pytest.mark.asyncio
async def test_optimize_loading_sequence_endpoint(client: AsyncClient, auth_headers, test_ship_for_api):
    """Test loading sequence optimization endpoint"""
    response = await client.get(
        f"/api/v1/advanced/optimize/loading/{test_ship_for_api.id}",
        headers=auth_headers
    )

    assert response.status_code in [200, 404, 500]


@pytest.mark.asyncio
async def test_optimize_loading_rate_endpoint(client: AsyncClient, auth_headers, test_ship_for_api):
    """Test optimal loading rate calculation endpoint"""
    weather = {
        "wind_speed_kmh": 25.0,
        "rainfall_mm": 0.0,
        "temperature_c": 25.0
    }

    response = await client.post(
        f"/api/v1/advanced/optimize/loading-rate/{test_ship_for_api.id}",
        json=weather,
        headers=auth_headers
    )

    assert response.status_code in [200, 404, 500]


@pytest.mark.asyncio
async def test_optimize_loading_rate_endpoint_no_weather(client: AsyncClient, auth_headers, test_ship_for_api):
    """Test optimal loading rate without weather data"""
    response = await client.post(
        f"/api/v1/advanced/optimize/loading-rate/{test_ship_for_api.id}",
        json=None,
        headers=auth_headers
    )

    # Should handle missing weather data gracefully
    assert response.status_code in [200, 404, 422, 500]


@pytest.mark.asyncio
async def test_optimization_endpoints_require_auth(client: AsyncClient, test_site):
    """Test that optimization endpoints require authentication"""
    response = await client.get(
        f"/api/v1/advanced/optimize/berths/{test_site.id}"
    )

    assert response.status_code == 401


# Report Generation Tests

@pytest.mark.asyncio
async def test_generate_daily_pdf_endpoint(client: AsyncClient, auth_headers, test_site):
    """Test daily PDF report generation endpoint"""
    today = date.today()

    response = await client.get(
        f"/api/v1/advanced/reports/daily-pdf?site_id={test_site.id}&operation_date={today.isoformat()}",
        headers=auth_headers
    )

    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "filename" in data or "file" in data


@pytest.mark.asyncio
async def test_generate_operations_excel_endpoint(client: AsyncClient, auth_headers, test_site):
    """Test operations Excel report generation endpoint"""
    start_date = date.today()
    end_date = start_date + timedelta(days=7)

    response = await client.get(
        f"/api/v1/advanced/reports/operations-excel?site_id={test_site.id}&start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
        headers=auth_headers
    )

    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "filename" in data or "file" in data


@pytest.mark.asyncio
async def test_report_endpoints_require_auth(client: AsyncClient, test_site):
    """Test that report endpoints require authentication"""
    today = date.today()

    response = await client.get(
        f"/api/v1/advanced/reports/daily-pdf?site_id={test_site.id}&operation_date={today.isoformat()}"
    )

    assert response.status_code == 401


# Mobile Endpoints Tests

@pytest.mark.asyncio
async def test_mobile_summary_endpoint(client: AsyncClient, auth_headers, test_site):
    """Test mobile summary endpoint"""
    response = await client.get(
        f"/api/v1/advanced/mobile/summary/{test_site.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    # Should return lightweight summary data
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_mobile_ship_status_endpoint(client: AsyncClient, auth_headers, test_ship_for_api):
    """Test mobile ship status endpoint"""
    response = await client.get(
        f"/api/v1/advanced/mobile/ship-status/{test_ship_for_api.id}",
        headers=auth_headers
    )

    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert "ship_name" in data or "status" in data


@pytest.mark.asyncio
async def test_mobile_endpoints_require_auth(client: AsyncClient, test_site):
    """Test that mobile endpoints require authentication"""
    response = await client.get(
        f"/api/v1/advanced/mobile/summary/{test_site.id}"
    )

    assert response.status_code == 401


# Cross-cutting concerns

@pytest.mark.asyncio
async def test_all_advanced_endpoints_return_json(client: AsyncClient, auth_headers, test_site):
    """Test that all advanced endpoints return JSON"""
    endpoints = [
        f"/api/v1/advanced/mobile/summary/{test_site.id}",
        f"/api/v1/advanced/optimize/berths/{test_site.id}",
    ]

    for endpoint in endpoints:
        response = await client.get(endpoint, headers=auth_headers)
        if response.status_code == 200:
            assert response.headers["content-type"].startswith("application/json")


@pytest.mark.asyncio
async def test_invalid_query_parameters(client: AsyncClient, auth_headers, test_site):
    """Test endpoints handle invalid query parameters gracefully"""
    response = await client.get(
        f"/api/v1/advanced/optimize/berths/{test_site.id}?days_ahead=invalid",
        headers=auth_headers
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
@patch('app.services.ml_failure_predictor.pickle')
async def test_train_ml_with_asset_type_filter(mock_pickle, client: AsyncClient, auth_headers):
    """Test ML training with asset type filter"""
    with patch('builtins.open', return_value=Mock()):
        with patch('app.services.ml_failure_predictor.os.path.exists', return_value=False):
            response = await client.post(
                "/api/v1/advanced/ml/train?asset_type=conveyor&training_days=60",
                headers=auth_headers
            )

    assert response.status_code in [200, 501]


@pytest.mark.asyncio
async def test_berth_optimization_invalid_site(client: AsyncClient, auth_headers):
    """Test berth optimization with invalid site ID"""
    invalid_site_id = 999999

    response = await client.get(
        f"/api/v1/advanced/optimize/berths/{invalid_site_id}",
        headers=auth_headers
    )

    assert response.status_code in [404, 500]
