"""
Tests for ML Failure Predictor Service
"""
import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.services.ml_failure_predictor import MLFailurePredictor
from app.models.asset import Asset, AssetType


@pytest.fixture
async def test_asset(test_db: AsyncSession, test_site) -> Asset:
    """Create test asset for ML predictions"""
    asset = Asset(
        id=str(uuid4()),
        asset_id="CONV-001",
        name="Conveyor Belt 1",
        asset_type=AssetType.CONVEYOR,
        site_id=test_site.id,
        manufacturer="Test Manufacturer",
        model="TB-1000",
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


@pytest.mark.asyncio
async def test_extract_features(test_db: AsyncSession, test_asset):
    """Test feature extraction from asset"""
    predictor = MLFailurePredictor(test_db)

    features = predictor._extract_features(test_asset)

    assert len(features) == 8
    assert all(isinstance(f, (int, float)) for f in features)
    # Check health_score is first feature
    assert features[0] == test_asset.health_score


@pytest.mark.asyncio
async def test_extract_features_handles_none_values(test_db: AsyncSession, test_site):
    """Test feature extraction handles None values gracefully"""
    asset = Asset(
        id=str(uuid4()),
        asset_id="CONV-002",
        name="Conveyor Belt 2",
        asset_type=AssetType.CONVEYOR,
        site_id=test_site.id,
        health_score=None,  # None value
        status="operational",
    )
    test_db.add(asset)
    await test_db.commit()
    await test_db.refresh(asset)

    predictor = MLFailurePredictor(test_db)
    features = predictor._extract_features(asset)

    assert len(features) == 8
    assert all(isinstance(f, (int, float)) for f in features)


@pytest.mark.asyncio
async def test_calculate_risk_level(test_db: AsyncSession):
    """Test risk level calculation"""
    predictor = MLFailurePredictor(test_db)

    assert predictor._calculate_risk_level(0.95) == "critical"
    assert predictor._calculate_risk_level(0.75) == "high"
    assert predictor._calculate_risk_level(0.50) == "medium"
    assert predictor._calculate_risk_level(0.20) == "low"


@pytest.mark.asyncio
async def test_estimate_hours_to_failure(test_db: AsyncSession):
    """Test hours to failure estimation"""
    predictor = MLFailurePredictor(test_db)

    # High probability = fewer hours
    hours_high = predictor._estimate_hours_to_failure(0.90, 24)
    assert hours_high < 24

    # Low probability = more hours
    hours_low = predictor._estimate_hours_to_failure(0.10, 24)
    assert hours_low > 24


@pytest.mark.asyncio
async def test_generate_recommendations_critical(test_db: AsyncSession):
    """Test recommendations for critical risk"""
    predictor = MLFailurePredictor(test_db)

    recommendations = predictor._generate_recommendations("critical", 2.5)

    assert len(recommendations) > 0
    assert any("immediate" in rec.lower() for rec in recommendations)


@pytest.mark.asyncio
async def test_generate_recommendations_high(test_db: AsyncSession):
    """Test recommendations for high risk"""
    predictor = MLFailurePredictor(test_db)

    recommendations = predictor._generate_recommendations("high", 12.0)

    assert len(recommendations) > 0
    assert any("schedule" in rec.lower() or "within" in rec.lower() for rec in recommendations)


@pytest.mark.asyncio
async def test_generate_recommendations_low(test_db: AsyncSession):
    """Test recommendations for low risk"""
    predictor = MLFailurePredictor(test_db)

    recommendations = predictor._generate_recommendations("low", 100.0)

    assert len(recommendations) > 0
    assert any("continue" in rec.lower() or "normal" in rec.lower() for rec in recommendations)


@pytest.mark.asyncio
@patch('app.services.ml_failure_predictor.pickle')
@patch('app.services.ml_failure_predictor.os.path.exists')
async def test_train_model_creates_model_file(mock_exists, mock_pickle, test_db: AsyncSession):
    """Test that model training creates a model file"""
    mock_exists.return_value = False
    predictor = MLFailurePredictor(test_db)

    # Mock pickle.dump
    mock_file = Mock()
    with patch('builtins.open', return_value=mock_file):
        result = await predictor.train_model()

    assert result["status"] == "success"
    assert "train_accuracy" in result
    assert "test_accuracy" in result
    assert "model_file" in result


@pytest.mark.asyncio
@patch('app.services.ml_failure_predictor.pickle')
@patch('app.services.ml_failure_predictor.os.path.exists')
async def test_train_model_with_asset_type_filter(mock_exists, mock_pickle, test_db: AsyncSession):
    """Test model training with asset type filter"""
    mock_exists.return_value = False
    predictor = MLFailurePredictor(test_db)

    with patch('builtins.open', return_value=Mock()):
        result = await predictor.train_model(asset_type="conveyor")

    assert result["status"] == "success"
    assert result.get("asset_type") == "conveyor"


@pytest.mark.asyncio
@patch('app.services.ml_failure_predictor.pickle.load')
@patch('app.services.ml_failure_predictor.os.path.exists')
async def test_predict_failure_model_not_found(mock_exists, mock_pickle_load, test_db: AsyncSession, test_asset):
    """Test prediction when model file doesn't exist"""
    mock_exists.return_value = False
    predictor = MLFailurePredictor(test_db)

    result = await predictor.predict_failure(test_asset.id)

    assert result["status"] == "error"
    assert "not found" in result["error"].lower() or "not trained" in result["error"].lower()


@pytest.mark.asyncio
@patch('app.services.ml_failure_predictor.pickle.load')
@patch('app.services.ml_failure_predictor.os.path.exists')
async def test_predict_failure_success(mock_exists, mock_pickle_load, test_db: AsyncSession, test_asset):
    """Test successful failure prediction"""
    mock_exists.return_value = True

    # Mock trained model
    mock_model = Mock()
    mock_model.predict_proba.return_value = [[0.3, 0.7]]  # 70% failure probability
    mock_scaler = Mock()
    mock_scaler.transform.return_value = [[1, 2, 3, 4, 5, 6, 7, 8]]

    mock_pickle_load.return_value = {
        "model": mock_model,
        "scaler": mock_scaler
    }

    predictor = MLFailurePredictor(test_db)

    with patch('builtins.open', return_value=Mock()):
        result = await predictor.predict_failure(test_asset.id, prediction_horizon_hours=24)

    assert result["status"] == "success"
    assert "failure_probability" in result
    assert "will_fail" in result
    assert "risk_level" in result
    assert "estimated_hours_to_failure" in result
    assert "recommendations" in result
    assert result["failure_probability"] == 0.7
    assert result["will_fail"] is True


@pytest.mark.asyncio
@patch('app.services.ml_failure_predictor.pickle.load')
@patch('app.services.ml_failure_predictor.os.path.exists')
async def test_predict_failure_low_probability(mock_exists, mock_pickle_load, test_db: AsyncSession, test_asset):
    """Test prediction with low failure probability"""
    mock_exists.return_value = True

    # Mock trained model with low probability
    mock_model = Mock()
    mock_model.predict_proba.return_value = [[0.85, 0.15]]  # 15% failure probability
    mock_scaler = Mock()
    mock_scaler.transform.return_value = [[1, 2, 3, 4, 5, 6, 7, 8]]

    mock_pickle_load.return_value = {
        "model": mock_model,
        "scaler": mock_scaler
    }

    predictor = MLFailurePredictor(test_db)

    with patch('builtins.open', return_value=Mock()):
        result = await predictor.predict_failure(test_asset.id)

    assert result["failure_probability"] == 0.15
    assert result["will_fail"] is False
    assert result["risk_level"] == "low"


@pytest.mark.asyncio
async def test_predict_failure_asset_not_found(test_db: AsyncSession):
    """Test prediction for non-existent asset"""
    predictor = MLFailurePredictor(test_db)

    result = await predictor.predict_failure("NON-EXISTENT-ID")

    assert result["status"] == "error"
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
@patch('app.services.ml_failure_predictor.pickle')
@patch('app.services.ml_failure_predictor.os.path.exists')
async def test_train_model_different_training_days(mock_exists, mock_pickle, test_db: AsyncSession):
    """Test model training with different training day ranges"""
    mock_exists.return_value = False
    predictor = MLFailurePredictor(test_db)

    # Test with 30 days
    with patch('builtins.open', return_value=Mock()):
        result_30 = await predictor.train_model(training_days=30)
        assert result_30["status"] == "success"

    # Test with 365 days
    with patch('builtins.open', return_value=Mock()):
        result_365 = await predictor.train_model(training_days=365)
        assert result_365["status"] == "success"


@pytest.mark.asyncio
@patch('app.services.ml_failure_predictor.pickle.load')
@patch('app.services.ml_failure_predictor.os.path.exists')
async def test_predict_failure_critical_risk(mock_exists, mock_pickle_load, test_db: AsyncSession, test_asset):
    """Test prediction with critical risk level"""
    mock_exists.return_value = True

    # Mock trained model with very high probability
    mock_model = Mock()
    mock_model.predict_proba.return_value = [[0.05, 0.95]]  # 95% failure probability
    mock_scaler = Mock()
    mock_scaler.transform.return_value = [[1, 2, 3, 4, 5, 6, 7, 8]]

    mock_pickle_load.return_value = {
        "model": mock_model,
        "scaler": mock_scaler
    }

    predictor = MLFailurePredictor(test_db)

    with patch('builtins.open', return_value=Mock()):
        result = await predictor.predict_failure(test_asset.id)

    assert result["risk_level"] == "critical"
    assert result["will_fail"] is True
    assert len(result["recommendations"]) > 0


@pytest.mark.asyncio
@patch('app.services.ml_failure_predictor.pickle.load')
@patch('app.services.ml_failure_predictor.os.path.exists')
async def test_predict_failure_different_horizons(mock_exists, mock_pickle_load, test_db: AsyncSession, test_asset):
    """Test prediction with different time horizons"""
    mock_exists.return_value = True

    mock_model = Mock()
    mock_model.predict_proba.return_value = [[0.5, 0.5]]
    mock_scaler = Mock()
    mock_scaler.transform.return_value = [[1, 2, 3, 4, 5, 6, 7, 8]]

    mock_pickle_load.return_value = {
        "model": mock_model,
        "scaler": mock_scaler
    }

    predictor = MLFailurePredictor(test_db)

    with patch('builtins.open', return_value=Mock()):
        # Test 24 hour horizon
        result_24 = await predictor.predict_failure(test_asset.id, prediction_horizon_hours=24)
        assert "prediction_horizon_hours" in result_24

        # Test 168 hour (7 day) horizon
        result_168 = await predictor.predict_failure(test_asset.id, prediction_horizon_hours=168)
        assert "prediction_horizon_hours" in result_168
