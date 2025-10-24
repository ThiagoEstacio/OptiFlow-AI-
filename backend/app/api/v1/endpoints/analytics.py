"""
Advanced Analytics endpoints for time series data
"""
from fastapi import APIRouter, Depends, Query, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from app.db.session import get_db
from app.services.analytics import analytics_service
from app.services.influxdb import influxdb_service

router = APIRouter()


@router.post("/statistics")
async def calculate_statistics(
    data: List[Dict[str, Any]] = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate statistical metrics for time series data

    Returns: mean, median, std, min, max, percentiles, skewness, kurtosis
    """
    try:
        stats = await analytics_service.calculate_statistics(data)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate statistics: {str(e)}")


@router.get("/timeseries/statistics")
async def get_timeseries_statistics(
    tag_ids: List[str] = Query(...),
    start_time: datetime = Query(...),
    end_time: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistical metrics for time series data from InfluxDB

    Query data and calculate statistics in one call
    """
    try:
        # Query time series data
        timeseries_data = influxdb_service.query_multiple_tags(
            tag_ids=tag_ids,
            start_time=start_time,
            end_time=end_time
        )

        # Calculate statistics for each tag
        results = {}
        if isinstance(timeseries_data, dict):
            for tag_id, points in timeseries_data.items():
                stats = await analytics_service.calculate_statistics(points)
                results[tag_id] = stats
        else:
            stats = await analytics_service.calculate_statistics(timeseries_data)
            results["combined"] = stats

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post("/anomalies")
async def detect_anomalies(
    data: List[Dict[str, Any]] = Body(...),
    method: str = Query("zscore", regex="^(zscore|iqr|mad)$"),
    threshold: float = Query(3.0, ge=0.0),
    db: AsyncSession = Depends(get_db)
):
    """
    Detect anomalies in time series data

    Methods:
    - zscore: Z-score based detection (default threshold: 3.0)
    - iqr: Interquartile range method (default threshold: 1.5)
    - mad: Median Absolute Deviation (default threshold: 3.5)

    Returns list of anomaly points with scores
    """
    try:
        anomalies = await analytics_service.detect_anomalies(
            data=data,
            method=method,
            threshold=threshold
        )

        return {
            "anomalies": anomalies,
            "count": len(anomalies),
            "method": method,
            "threshold": threshold
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect anomalies: {str(e)}")


@router.get("/timeseries/anomalies")
async def get_timeseries_anomalies(
    tag_id: str = Query(...),
    start_time: datetime = Query(...),
    end_time: Optional[datetime] = Query(None),
    method: str = Query("zscore", regex="^(zscore|iqr|mad)$"),
    threshold: float = Query(3.0, ge=0.0),
    db: AsyncSession = Depends(get_db)
):
    """
    Detect anomalies in time series data from InfluxDB
    """
    try:
        # Query time series data
        timeseries_data = influxdb_service.query_tag_data(
            tag_id=tag_id,
            start_time=start_time,
            end_time=end_time
        )

        # Detect anomalies
        anomalies = await analytics_service.detect_anomalies(
            data=timeseries_data,
            method=method,
            threshold=threshold
        )

        return {
            "tag_id": tag_id,
            "anomalies": anomalies,
            "count": len(anomalies),
            "method": method,
            "threshold": threshold,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat() if end_time else None
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect anomalies: {str(e)}")


@router.post("/trends")
async def calculate_trends(
    data: List[Dict[str, Any]] = Body(...),
    window: int = Query(10, ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate trend information using linear regression

    Returns: slope, direction, strength, moving average
    """
    try:
        trends = await analytics_service.calculate_trends(
            data=data,
            window=window
        )
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate trends: {str(e)}")


@router.get("/timeseries/trends")
async def get_timeseries_trends(
    tag_id: str = Query(...),
    start_time: datetime = Query(...),
    end_time: Optional[datetime] = Query(None),
    window: int = Query(10, ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate trends for time series data from InfluxDB
    """
    try:
        # Query time series data
        timeseries_data = influxdb_service.query_tag_data(
            tag_id=tag_id,
            start_time=start_time,
            end_time=end_time
        )

        # Calculate trends
        trends = await analytics_service.calculate_trends(
            data=timeseries_data,
            window=window
        )

        return {
            "tag_id": tag_id,
            "trends": trends,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat() if end_time else None
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate trends: {str(e)}")


@router.post("/forecast")
async def forecast_simple(
    data: List[Dict[str, Any]] = Body(...),
    periods: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Simple linear forecast for time series data

    Returns forecasted points for the specified number of periods
    """
    try:
        forecasts = await analytics_service.forecast_simple(
            data=data,
            periods=periods
        )

        return {
            "forecasts": forecasts,
            "periods": periods
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to forecast: {str(e)}")


@router.get("/timeseries/forecast")
async def get_timeseries_forecast(
    tag_id: str = Query(...),
    start_time: datetime = Query(...),
    end_time: Optional[datetime] = Query(None),
    periods: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate forecast for time series data from InfluxDB
    """
    try:
        # Query time series data
        timeseries_data = influxdb_service.query_tag_data(
            tag_id=tag_id,
            start_time=start_time,
            end_time=end_time
        )

        # Generate forecast
        forecasts = await analytics_service.forecast_simple(
            data=timeseries_data,
            periods=periods
        )

        return {
            "tag_id": tag_id,
            "historical_data": timeseries_data,
            "forecasts": forecasts,
            "periods": periods
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to forecast: {str(e)}")


@router.post("/correlation")
async def calculate_correlation(
    data1: List[Dict[str, Any]] = Body(...),
    data2: List[Dict[str, Any]] = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate correlation between two time series

    Returns Pearson and Spearman correlation coefficients
    """
    try:
        correlation = await analytics_service.calculate_correlation(
            data1=data1,
            data2=data2
        )
        return correlation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate correlation: {str(e)}")


@router.get("/timeseries/correlation")
async def get_timeseries_correlation(
    tag_id1: str = Query(...),
    tag_id2: str = Query(...),
    start_time: datetime = Query(...),
    end_time: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate correlation between two tags from InfluxDB
    """
    try:
        # Query time series data for both tags
        data1 = influxdb_service.query_tag_data(
            tag_id=tag_id1,
            start_time=start_time,
            end_time=end_time
        )

        data2 = influxdb_service.query_tag_data(
            tag_id=tag_id2,
            start_time=start_time,
            end_time=end_time
        )

        # Calculate correlation
        correlation = await analytics_service.calculate_correlation(
            data1=data1,
            data2=data2
        )

        return {
            "tag_id1": tag_id1,
            "tag_id2": tag_id2,
            "correlation": correlation,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat() if end_time else None
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate correlation: {str(e)}")


@router.post("/resample")
async def resample_data(
    data: List[Dict[str, Any]] = Body(...),
    interval: str = Query(..., regex="^[0-9]+(s|min|h|d)$"),
    aggregation: str = Query("mean", regex="^(mean|sum|min|max|first|last)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Resample time series data to a different interval

    Intervals: '1s', '5min', '1h', '1d', etc.
    Aggregations: 'mean', 'sum', 'min', 'max', 'first', 'last'
    """
    try:
        resampled = await analytics_service.resample_data(
            data=data,
            interval=interval,
            aggregation=aggregation
        )

        return {
            "data": resampled,
            "interval": interval,
            "aggregation": aggregation,
            "count": len(resampled)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resample data: {str(e)}")


@router.post("/fft")
async def calculate_fft(
    data: List[Dict[str, Any]] = Body(...),
    top_frequencies: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate Fast Fourier Transform to detect periodicity

    Returns top frequencies and their periods
    """
    try:
        fft_results = await analytics_service.calculate_fft(
            data=data,
            top_frequencies=top_frequencies
        )
        return fft_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate FFT: {str(e)}")


@router.get("/timeseries/fft")
async def get_timeseries_fft(
    tag_id: str = Query(...),
    start_time: datetime = Query(...),
    end_time: Optional[datetime] = Query(None),
    top_frequencies: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate FFT for time series data from InfluxDB
    """
    try:
        # Query time series data
        timeseries_data = influxdb_service.query_tag_data(
            tag_id=tag_id,
            start_time=start_time,
            end_time=end_time
        )

        # Calculate FFT
        fft_results = await analytics_service.calculate_fft(
            data=timeseries_data,
            top_frequencies=top_frequencies
        )

        return {
            "tag_id": tag_id,
            "fft": fft_results,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat() if end_time else None
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate FFT: {str(e)}")
