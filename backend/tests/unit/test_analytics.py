"""
Unit tests for Analytics Service
"""
import pytest
from datetime import datetime
from app.services.analytics import analytics_service


@pytest.mark.asyncio
async def test_calculate_statistics(sample_timeseries_data):
    """Test statistical calculations"""
    stats = await analytics_service.calculate_statistics(sample_timeseries_data)

    assert "mean" in stats
    assert "median" in stats
    assert "std" in stats
    assert "min" in stats
    assert "max" in stats
    assert "percentiles" in stats

    # Check values
    assert stats["count"] == 3
    assert stats["min"] == 41.8
    assert stats["max"] == 43.2


@pytest.mark.asyncio
async def test_calculate_statistics_empty():
    """Test statistics with empty data"""
    stats = await analytics_service.calculate_statistics([])
    assert stats == {}


@pytest.mark.asyncio
async def test_detect_anomalies_zscore(sample_timeseries_data):
    """Test anomaly detection using Z-score method"""
    # Add an anomaly
    data = sample_timeseries_data + [{
        "timestamp": "2024-01-01T00:15:00Z",
        "value": 100.0,  # Anomaly
        "quality": "good"
    }]

    anomalies = await analytics_service.detect_anomalies(
        data=data,
        method="zscore",
        threshold=2.0
    )

    assert len(anomalies) > 0
    assert anomalies[0]["anomaly_score"] > 2.0
    assert anomalies[0]["method"] == "zscore"


@pytest.mark.asyncio
async def test_detect_anomalies_iqr(sample_timeseries_data):
    """Test anomaly detection using IQR method"""
    # Add outliers
    data = sample_timeseries_data * 3  # More data points
    data.append({
        "timestamp": "2024-01-01T00:30:00Z",
        "value": 200.0,  # Outlier
        "quality": "good"
    })

    anomalies = await analytics_service.detect_anomalies(
        data=data,
        method="iqr",
        threshold=1.5
    )

    assert len(anomalies) > 0


@pytest.mark.asyncio
async def test_calculate_trends(sample_timeseries_data):
    """Test trend calculation"""
    trends = await analytics_service.calculate_trends(
        data=sample_timeseries_data,
        window=2
    )

    assert "slope" in trends
    assert "direction" in trends
    assert "strength" in trends
    assert "r_squared" in trends
    assert trends["direction"] in ["increasing", "decreasing", "stable"]


@pytest.mark.asyncio
async def test_forecast_simple(sample_timeseries_data):
    """Test simple forecasting"""
    forecasts = await analytics_service.forecast_simple(
        data=sample_timeseries_data,
        periods=5
    )

    assert len(forecasts) == 5
    assert all("timestamp" in f for f in forecasts)
    assert all("value" in f for f in forecasts)
    assert all(f["type"] == "forecast" for f in forecasts)


@pytest.mark.asyncio
async def test_calculate_correlation():
    """Test correlation calculation"""
    data1 = [{"value": i} for i in range(10)]
    data2 = [{"value": i * 2} for i in range(10)]

    correlation = await analytics_service.calculate_correlation(data1, data2)

    assert "pearson" in correlation
    assert "spearman" in correlation
    assert correlation["pearson"]["correlation"] > 0.9  # Strong positive correlation


@pytest.mark.asyncio
async def test_resample_data():
    """Test data resampling"""
    data = [
        {"timestamp": "2024-01-01T00:00:00Z", "value": 10},
        {"timestamp": "2024-01-01T00:01:00Z", "value": 20},
        {"timestamp": "2024-01-01T00:02:00Z", "value": 30},
        {"timestamp": "2024-01-01T00:03:00Z", "value": 40},
        {"timestamp": "2024-01-01T00:04:00Z", "value": 50},
    ]

    resampled = await analytics_service.resample_data(
        data=data,
        interval="2min",
        aggregation="mean"
    )

    assert len(resampled) > 0
    assert all("timestamp" in r for r in resampled)
    assert all("value" in r for r in resampled)


@pytest.mark.asyncio
async def test_calculate_fft(sample_timeseries_data):
    """Test FFT calculation"""
    # Need more data points for meaningful FFT
    data = sample_timeseries_data * 10

    fft_results = await analytics_service.calculate_fft(
        data=data,
        top_frequencies=5
    )

    assert "top_frequencies" in fft_results
    assert "dominant_frequency" in fft_results
    assert len(fft_results["top_frequencies"]) <= 5
