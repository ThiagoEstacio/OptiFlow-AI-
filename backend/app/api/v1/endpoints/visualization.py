"""
Visualization API Endpoints

Provides REST API for visualization components (Trend Viewer, Live Monitor, etc.)
Integrates with TimeSeries, Export, and Annotation services.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from io import BytesIO

from app.api.deps import get_db
from app.models.tag import Tag
from app.models.annotation import Annotation, AnnotationType, AnnotationSeverity
from app.services.timeseries_service import (
    timeseries_service,
    TimeSeriesQuery,
    AggregationFunction,
    TagSeries
)
from app.services.export_service import export_service, ExportFormat
from loguru import logger

router = APIRouter()


# ==================== Pydantic Schemas ====================

from pydantic import BaseModel, Field


class TrendQueryRequest(BaseModel):
    """Request schema for trend query"""
    tag_ids: List[UUID] = Field(..., min_items=1, max_items=20, description="Tag IDs to query")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    aggregation: Optional[AggregationFunction] = Field(None, description="Aggregation function")
    interval: Optional[str] = Field(None, description="Aggregation interval (e.g., '1m', '5m', '1h')")
    max_points: int = Field(1000, ge=10, le=10000, description="Maximum points per tag")
    include_annotations: bool = Field(True, description="Include annotations in response")
    annotation_types: Optional[List[AnnotationType]] = Field(None, description="Filter annotation types")

    class Config:
        schema_extra = {
            "example": {
                "tag_ids": ["123e4567-e89b-12d3-a456-426614174000"],
                "start_time": "2025-01-20T00:00:00Z",
                "end_time": "2025-01-20T23:59:59Z",
                "aggregation": "mean",
                "interval": "5m",
                "max_points": 1000,
                "include_annotations": True,
                "annotation_types": ["event", "alarm"]
            }
        }


class TrendResponse(BaseModel):
    """Response schema for trend query"""
    tags: List[dict] = Field(..., description="Tag series data")
    annotations: List[dict] = Field([], description="Associated annotations")
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")
    total_data_points: int = Field(..., description="Total data points returned")

    class Config:
        schema_extra = {
            "example": {
                "tags": [],
                "annotations": [],
                "query_time_ms": 125.5,
                "total_data_points": 1000
            }
        }


class LiveDataRequest(BaseModel):
    """Request schema for live data"""
    tag_ids: List[UUID] = Field(..., min_items=1, max_items=50, description="Tag IDs to monitor")
    duration_seconds: int = Field(300, ge=10, le=3600, description="Duration to look back")

    class Config:
        schema_extra = {
            "example": {
                "tag_ids": ["123e4567-e89b-12d3-a456-426614174000"],
                "duration_seconds": 300
            }
        }


class ExportRequest(BaseModel):
    """Request schema for export"""
    tag_ids: List[UUID] = Field(..., min_items=1, max_items=100, description="Tag IDs to export")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    format: str = Field("csv", description="Export format (csv, json, excel)")
    include_annotations: bool = Field(True, description="Include annotations")
    include_statistics: bool = Field(True, description="Include statistics")
    aggregation: Optional[AggregationFunction] = Field(None, description="Aggregation function")
    interval: Optional[str] = Field(None, description="Aggregation interval")

    class Config:
        schema_extra = {
            "example": {
                "tag_ids": ["123e4567-e89b-12d3-a456-426614174000"],
                "start_time": "2025-01-20T00:00:00Z",
                "end_time": "2025-01-20T23:59:59Z",
                "format": "csv",
                "include_annotations": True,
                "include_statistics": True
            }
        }


# ==================== Trend Viewer Endpoints ====================

@router.post("/trends", response_model=TrendResponse)
async def query_trends(
    request: TrendQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query historical trend data for multiple tags.

    This is the main endpoint for the Trend Viewer component.

    Features:
    - Multi-tag queries (up to 20 tags)
    - Time range filtering
    - Aggregation and downsampling
    - Automatic annotation retrieval
    - Query performance tracking
    """
    import time
    start_query_time = time.time()

    logger.info(f"Querying trends for {len(request.tag_ids)} tags from {request.start_time} to {request.end_time}")

    # Validate tags exist
    tags = db.query(Tag).filter(Tag.id.in_(request.tag_ids)).all()
    if len(tags) != len(request.tag_ids):
        found_ids = {tag.id for tag in tags}
        missing_ids = set(request.tag_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tags not found: {missing_ids}"
        )

    # Create tag_id to tag_name mapping
    tag_names = {str(tag.id): tag.name for tag in tags}

    # Query time series data
    query = TimeSeriesQuery(
        tag_ids=[str(tag_id) for tag_id in request.tag_ids],
        start_time=request.start_time,
        end_time=request.end_time,
        aggregation=request.aggregation,
        interval=request.interval,
        limit=request.max_points
    )

    tag_series_list = await timeseries_service.query_multiple_tags(query)

    # Add tag names to series
    for series in tag_series_list:
        series.tag_name = tag_names.get(series.tag_id, series.tag_id)

    # Query annotations if requested
    annotations = []
    if request.include_annotations:
        annotation_query = db.query(Annotation).filter(
            Annotation.tag_id.in_(request.tag_ids),
            Annotation.start_time >= request.start_time,
            Annotation.start_time <= request.end_time,
            Annotation.is_deleted == False
        )

        # Filter by annotation types if specified
        if request.annotation_types:
            annotation_query = annotation_query.filter(
                Annotation.annotation_type.in_(request.annotation_types)
            )

        annotations = annotation_query.order_by(Annotation.start_time).all()

    # Calculate query time
    query_time_ms = (time.time() - start_query_time) * 1000

    # Calculate total data points
    total_data_points = sum(len(series.data_points) for series in tag_series_list)

    logger.info(f"Trend query completed in {query_time_ms:.2f}ms - {total_data_points} data points, {len(annotations)} annotations")

    return TrendResponse(
        tags=[series.to_dict() for series in tag_series_list],
        annotations=[annotation.to_dict() for annotation in annotations],
        query_time_ms=query_time_ms,
        total_data_points=total_data_points
    )


@router.get("/trends/{tag_id}", response_model=TrendResponse)
async def query_single_tag_trend(
    tag_id: UUID,
    start_time: datetime = Query(..., description="Start time"),
    end_time: datetime = Query(..., description="End time"),
    aggregation: Optional[AggregationFunction] = Query(None, description="Aggregation function"),
    interval: Optional[str] = Query(None, description="Aggregation interval"),
    max_points: int = Query(1000, ge=10, le=10000, description="Maximum points"),
    include_annotations: bool = Query(True, description="Include annotations"),
    db: Session = Depends(get_db)
):
    """
    Query historical trend data for a single tag.

    Simplified endpoint for single-tag queries.
    """
    import time
    start_query_time = time.time()

    logger.info(f"Querying trend for tag {tag_id} from {start_time} to {end_time}")

    # Validate tag exists
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag {tag_id} not found"
        )

    # Query time series data
    tag_series = await timeseries_service.query_tag_data(
        tag_id=str(tag_id),
        start_time=start_time,
        end_time=end_time,
        aggregation=aggregation,
        interval=interval,
        limit=max_points
    )

    tag_series.tag_name = tag.name

    # Query annotations if requested
    annotations = []
    if include_annotations:
        annotations = db.query(Annotation).filter(
            Annotation.tag_id == tag_id,
            Annotation.start_time >= start_time,
            Annotation.start_time <= end_time,
            Annotation.is_deleted == False
        ).order_by(Annotation.start_time).all()

    # Calculate query time
    query_time_ms = (time.time() - start_query_time) * 1000

    logger.info(f"Trend query completed in {query_time_ms:.2f}ms - {len(tag_series.data_points)} data points, {len(annotations)} annotations")

    return TrendResponse(
        tags=[tag_series.to_dict()],
        annotations=[annotation.to_dict() for annotation in annotations],
        query_time_ms=query_time_ms,
        total_data_points=len(tag_series.data_points)
    )


# ==================== Live Monitor Endpoints ====================

@router.post("/live", response_model=TrendResponse)
async def query_live_data(
    request: LiveDataRequest,
    db: Session = Depends(get_db)
):
    """
    Query recent data for live monitoring.

    Returns data from the last N seconds for real-time visualization.
    Use in conjunction with WebSocket for live updates.
    """
    import time
    start_query_time = time.time()

    logger.info(f"Querying live data for {len(request.tag_ids)} tags (last {request.duration_seconds}s)")

    # Validate tags exist
    tags = db.query(Tag).filter(Tag.id.in_(request.tag_ids)).all()
    if len(tags) != len(request.tag_ids):
        found_ids = {tag.id for tag in tags}
        missing_ids = set(request.tag_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tags not found: {missing_ids}"
        )

    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(seconds=request.duration_seconds)

    # Create tag_id to tag_name mapping
    tag_names = {str(tag.id): tag.name for tag in tags}

    # Query time series data
    query = TimeSeriesQuery(
        tag_ids=[str(tag_id) for tag_id in request.tag_ids],
        start_time=start_time,
        end_time=end_time,
        limit=1000
    )

    tag_series_list = await timeseries_service.query_multiple_tags(query)

    # Add tag names to series
    for series in tag_series_list:
        series.tag_name = tag_names.get(series.tag_id, series.tag_id)

    # Calculate query time
    query_time_ms = (time.time() - start_query_time) * 1000

    # Calculate total data points
    total_data_points = sum(len(series.data_points) for series in tag_series_list)

    logger.info(f"Live data query completed in {query_time_ms:.2f}ms - {total_data_points} data points")

    return TrendResponse(
        tags=[series.to_dict() for series in tag_series_list],
        annotations=[],
        query_time_ms=query_time_ms,
        total_data_points=total_data_points
    )


@router.get("/live/latest", response_model=dict)
async def get_latest_values(
    tag_ids: List[UUID] = Query(..., description="Tag IDs"),
    db: Session = Depends(get_db)
):
    """
    Get the latest values for multiple tags.

    Returns the most recent value for each tag.
    Useful for dashboard displays and current value indicators.
    """
    logger.info(f"Getting latest values for {len(tag_ids)} tags")

    # Validate tags exist
    tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
    if not tags:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tags found"
        )

    # Get latest values
    latest_values = await timeseries_service.query_latest_values(
        tag_ids=[str(tag_id) for tag_id in tag_ids]
    )

    # Build response with tag names
    result = {}
    for tag in tags:
        tag_id_str = str(tag.id)
        if tag_id_str in latest_values:
            result[tag_id_str] = {
                "tag_id": tag_id_str,
                "tag_name": tag.name,
                "value": latest_values[tag_id_str].value,
                "timestamp": latest_values[tag_id_str].timestamp.isoformat(),
                "quality": latest_values[tag_id_str].quality,
                "unit": tag.unit
            }

    return {
        "latest_values": result,
        "count": len(result)
    }


# ==================== Export Endpoints ====================

@router.post("/export")
async def export_trend_data(
    request: ExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export trend data to various formats.

    Supports:
    - CSV (comma-separated values)
    - JSON (JavaScript Object Notation)
    - Excel (XLSX spreadsheet)

    Returns file download response.
    """
    logger.info(f"Exporting {len(request.tag_ids)} tags to {request.format}")

    # Validate tags exist
    tags = db.query(Tag).filter(Tag.id.in_(request.tag_ids)).all()
    if len(tags) != len(request.tag_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more tags not found"
        )

    # Create tag_id to tag_name mapping
    tag_names = {str(tag.id): tag.name for tag in tags}

    # Query time series data
    query = TimeSeriesQuery(
        tag_ids=[str(tag_id) for tag_id in request.tag_ids],
        start_time=request.start_time,
        end_time=request.end_time,
        aggregation=request.aggregation,
        interval=request.interval
    )

    tag_series_list = await timeseries_service.query_multiple_tags(query)

    # Add tag names to series
    for series in tag_series_list:
        series.tag_name = tag_names.get(series.tag_id, series.tag_id)

    # Query annotations if requested
    annotations = []
    if request.include_annotations:
        annotations = db.query(Annotation).filter(
            Annotation.tag_id.in_(request.tag_ids),
            Annotation.start_time >= request.start_time,
            Annotation.start_time <= request.end_time,
            Annotation.is_deleted == False
        ).all()

    # Generate export based on format
    if request.format == "csv":
        content = await export_service.export_multiple_tags_to_csv(tag_series_list, format_type="wide")
        media_type = "text/csv"
        filename = f"trend_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    elif request.format == "json":
        content = await export_service.export_multiple_tags_to_json(tag_series_list, pretty=True)
        media_type = "application/json"
        filename = f"trend_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    elif request.format == "excel":
        try:
            buffer = await export_service.export_to_excel(tag_series_list, annotations if request.include_annotations else None)
            filename = f"trend_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"

            return StreamingResponse(
                buffer,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format: {request.format}"
        )


@router.get("/export/summary")
async def export_summary_report(
    tag_ids: List[UUID] = Query(..., description="Tag IDs"),
    start_time: datetime = Query(..., description="Start time"),
    end_time: datetime = Query(..., description="End time"),
    format: str = Query("json", description="Export format (json or csv)"),
    db: Session = Depends(get_db)
):
    """
    Export summary report with statistics.

    Provides aggregated statistics without detailed data points.
    Useful for reports and dashboards.
    """
    logger.info(f"Generating summary report for {len(tag_ids)} tags")

    # Validate tags exist
    tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
    if not tags:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tags found"
        )

    # Create tag_id to tag_name mapping
    tag_names = {str(tag.id): tag.name for tag in tags}

    # Query time series data
    query = TimeSeriesQuery(
        tag_ids=[str(tag_id) for tag_id in tag_ids],
        start_time=start_time,
        end_time=end_time
    )

    tag_series_list = await timeseries_service.query_multiple_tags(query)

    # Add tag names to series
    for series in tag_series_list:
        series.tag_name = tag_names.get(series.tag_id, series.tag_id)

    # Query annotations
    annotations = db.query(Annotation).filter(
        Annotation.tag_id.in_(tag_ids),
        Annotation.start_time >= start_time,
        Annotation.start_time <= end_time,
        Annotation.is_deleted == False
    ).all()

    # Generate summary report
    content = await export_service.export_summary_report(
        tag_series_list,
        annotations,
        format_type=format
    )

    if format == "json":
        media_type = "application/json"
        filename = f"summary_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    else:
        media_type = "text/csv"
        filename = f"summary_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


# ==================== Statistics Endpoints ====================

@router.get("/statistics/{tag_id}")
async def get_tag_statistics(
    tag_id: UUID,
    start_time: datetime = Query(..., description="Start time"),
    end_time: datetime = Query(..., description="End time"),
    db: Session = Depends(get_db)
):
    """
    Get statistical analysis for a tag over a time range.

    Returns min, max, mean, median, stddev, etc.
    """
    logger.info(f"Calculating statistics for tag {tag_id}")

    # Validate tag exists
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag {tag_id} not found"
        )

    # Calculate statistics
    statistics = await timeseries_service.calculate_statistics(
        tag_id=str(tag_id),
        start_time=start_time,
        end_time=end_time
    )

    return {
        "tag_id": str(tag_id),
        "tag_name": tag.name,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "statistics": statistics
    }
