"""
Data Export endpoints for CSV, JSON, and Excel formats
"""
from fastapi import APIRouter, Depends, Query, Body, HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from app.db.session import get_db
from app.services.export import export_service
from app.services.influxdb import influxdb_service

router = APIRouter()


@router.post("/csv", response_class=StreamingResponse)
async def export_csv(
    data: List[Dict[str, Any]] = Body(...),
    filename: str = Query("export.csv"),
    columns: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Export data to CSV format

    Args:
        data: List of dictionaries to export
        filename: Output filename
        columns: Optional list of columns to include (in order)

    Returns:
        CSV file as streaming response
    """
    try:
        csv_buffer = await export_service.export_to_csv(
            data=data,
            columns=columns
        )

        return StreamingResponse(
            iter([csv_buffer.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/json")
async def export_json(
    data: List[Dict[str, Any]] = Body(...),
    pretty: bool = Query(False),
    metadata: Optional[Dict[str, Any]] = Body(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Export data to JSON format

    Args:
        data: List of dictionaries to export
        pretty: Whether to format JSON with indentation
        metadata: Optional metadata to include

    Returns:
        JSON response
    """
    try:
        json_data = await export_service.export_to_json(
            data=data,
            pretty=pretty,
            metadata=metadata
        )

        return Response(
            content=json_data,
            media_type="application/json",
            headers={
                "Content-Disposition": "attachment; filename=export.json"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/excel", response_class=StreamingResponse)
async def export_excel(
    data: List[Dict[str, Any]] = Body(...),
    filename: str = Query("export.xlsx"),
    sheet_name: str = Query("Data"),
    columns: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Export data to Excel format (.xlsx)

    Args:
        data: List of dictionaries to export
        filename: Output filename
        sheet_name: Name of the Excel sheet
        columns: Optional list of columns to include (in order)

    Returns:
        Excel file as streaming response
    """
    try:
        excel_buffer = await export_service.export_to_excel(
            data=data,
            sheet_name=sheet_name,
            columns=columns
        )

        return StreamingResponse(
            iter([excel_buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/timeseries/csv", response_class=StreamingResponse)
async def export_timeseries_csv(
    tag_ids: List[str] = Query(...),
    start_time: datetime = Query(...),
    end_time: Optional[datetime] = Query(None),
    aggregation: Optional[str] = Query(None),
    interval: Optional[str] = Query(None),
    pivot: bool = Query(False),
    filename: str = Query("timeseries_export.csv"),
    db: AsyncSession = Depends(get_db)
):
    """
    Export time series data to CSV format

    Args:
        tag_ids: List of tag IDs to export
        start_time: Start time for data query
        end_time: End time for data query
        aggregation: Aggregation function (mean, sum, min, max)
        interval: Aggregation interval (e.g., "5m", "1h")
        pivot: Whether to pivot data (tags as columns)
        filename: Output filename

    Returns:
        CSV file with time series data
    """
    try:
        # Query time series data
        timeseries_data = influxdb_service.query_multiple_tags(
            tag_ids=tag_ids,
            start_time=start_time,
            end_time=end_time,
            aggregation=aggregation,
            interval=interval
        )

        # Convert to list format
        data_list = []
        if isinstance(timeseries_data, dict):
            for tag_id, points in timeseries_data.items():
                for point in points:
                    data_list.append({
                        "tag_id": tag_id,
                        **point
                    })
        else:
            data_list = timeseries_data

        # Export to CSV
        csv_buffer = await export_service.export_timeseries_to_csv(
            timeseries_data=data_list,
            pivot=pivot
        )

        return StreamingResponse(
            iter([csv_buffer.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/timeseries/excel", response_class=StreamingResponse)
async def export_timeseries_excel(
    tag_ids: List[str] = Query(...),
    start_time: datetime = Query(...),
    end_time: Optional[datetime] = Query(None),
    aggregation: Optional[str] = Query(None),
    interval: Optional[str] = Query(None),
    filename: str = Query("timeseries_export.xlsx"),
    sheet_name: str = Query("Time Series Data"),
    db: AsyncSession = Depends(get_db)
):
    """
    Export time series data to Excel format

    Args:
        tag_ids: List of tag IDs to export
        start_time: Start time for data query
        end_time: End time for data query
        aggregation: Aggregation function (mean, sum, min, max)
        interval: Aggregation interval (e.g., "5m", "1h")
        filename: Output filename
        sheet_name: Name of the Excel sheet

    Returns:
        Excel file with time series data
    """
    try:
        # Query time series data
        timeseries_data = influxdb_service.query_multiple_tags(
            tag_ids=tag_ids,
            start_time=start_time,
            end_time=end_time,
            aggregation=aggregation,
            interval=interval
        )

        # Convert to list format
        data_list = []
        if isinstance(timeseries_data, dict):
            for tag_id, points in timeseries_data.items():
                for point in points:
                    data_list.append({
                        "tag_id": tag_id,
                        **point
                    })
        else:
            data_list = timeseries_data

        # Export to Excel
        excel_buffer = await export_service.export_to_excel(
            data=data_list,
            sheet_name=sheet_name
        )

        return StreamingResponse(
            iter([excel_buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/template/excel", response_class=StreamingResponse)
async def export_with_template(
    data: List[Dict[str, Any]] = Body(...),
    template_config: Dict[str, Any] = Body(...),
    filename: str = Query("report.xlsx"),
    db: AsyncSession = Depends(get_db)
):
    """
    Export data using a custom Excel template

    Args:
        data: List of dictionaries to export
        template_config: Template configuration (title, columns, formatting)
        filename: Output filename

    Example template_config:
    {
        "sheet_name": "Monthly Report",
        "title": "Production Report - January 2024",
        "columns": ["timestamp", "device_id", "value", "quality"]
    }

    Returns:
        Excel file with custom formatting
    """
    try:
        excel_buffer = await export_service.export_with_template(
            data=data,
            template_config=template_config
        )

        return StreamingResponse(
            iter([excel_buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
