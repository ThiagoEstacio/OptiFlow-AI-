"""
GBM Logistics Data API Endpoints

API endpoints for multi-source data import and insights:
- Excel/CSV file upload
- External API integration
- Manual data entry
- Data insights and analytics
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.data_import_service import DataImportService
from app.services.gbm_insights_service import GBMInsightsService

router = APIRouter()


# ==================== PYDANTIC MODELS ====================

class DataSourceCreate(BaseModel):
    """Data source creation model."""
    name: str = Field(..., description="Data source name")
    source_type: str = Field(..., description="Source type: api, manual, excel, csv")
    api_url: Optional[str] = Field(None, description="API URL if source_type is api")
    api_key: Optional[str] = Field(None, description="API key if required")
    auth_type: Optional[str] = Field("none", description="Auth type: bearer, basic, api_key, none")
    data_format: Optional[str] = Field("json", description="Data format: json, xml, csv, excel")
    field_mapping: Optional[Dict[str, str]] = Field(None, description="Field mapping from external to internal")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Custom validation rules")
    auto_sync: Optional[bool] = Field(False, description="Enable automatic synchronization")
    sync_interval_minutes: Optional[int] = Field(60, description="Sync interval in minutes")
    require_approval: Optional[bool] = Field(False, description="Require approval before import")
    notes: Optional[str] = Field(None, description="Additional notes")


class ManualEntryCreate(BaseModel):
    """Manual data entry model."""
    operation_type: str = Field(..., description="Operation type")
    operation_date: datetime = Field(..., description="Operation date and time")
    vehicle_id: Optional[str] = Field(None, description="Vehicle ID")
    vehicle_type: Optional[str] = Field(None, description="Vehicle type")
    product_type: str = Field(..., description="Product type")
    product_grade: Optional[str] = Field(None, description="Product grade")
    gross_weight_kg: Optional[float] = Field(None, description="Gross weight in kg")
    tare_weight_kg: Optional[float] = Field(None, description="Tare weight in kg")
    net_weight_kg: float = Field(..., description="Net weight in kg")
    moisture_percent: Optional[float] = Field(None, description="Moisture percentage")
    impurity_percent: Optional[float] = Field(None, description="Impurity percentage")
    origin: Optional[str] = Field(None, description="Origin location")
    destination: Optional[str] = Field(None, description="Destination location")
    loading_time_minutes: Optional[float] = Field(None, description="Loading time in minutes")
    waiting_time_minutes: Optional[float] = Field(None, description="Waiting time in minutes")
    notes: Optional[str] = Field(None, description="Additional notes")


class ImportApproval(BaseModel):
    """Import approval model."""
    approved: bool = Field(..., description="Approval decision")
    notes: Optional[str] = Field(None, description="Approval notes")


# ==================== DATA SOURCE MANAGEMENT ====================

@router.post("/data-sources/", response_model=Dict[str, Any])
async def create_data_source(
    site_id: int,
    data_source: DataSourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new data source configuration.

    Configures a new data source for importing GBM Logística data.
    """
    service = DataImportService(db)

    try:
        result = await service.create_data_source(
            site_id=site_id,
            user_id=current_user.id,
            **data_source.dict()
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/data-sources/{site_id}", response_model=List[Dict[str, Any]])
async def get_data_sources(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all data sources for a site.

    Returns list of configured data sources.
    """
    service = DataImportService(db)
    return await service.get_data_sources(site_id)


# ==================== FILE IMPORT ====================

@router.post("/import/excel/", response_model=Dict[str, Any])
async def import_excel_file(
    site_id: int = Form(...),
    data_source_id: int = Form(...),
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import data from Excel file.

    Upload and process Excel file with GBM Logística data.
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel format (.xlsx or .xls)")

    service = DataImportService(db)

    try:
        file_content = await file.read()
        result = await service.import_from_excel(
            site_id=site_id,
            data_source_id=data_source_id,
            file_content=file_content,
            file_name=file.filename,
            user_id=current_user.id,
            sheet_name=sheet_name
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import/csv/", response_model=Dict[str, Any])
async def import_csv_file(
    site_id: int = Form(...),
    data_source_id: int = Form(...),
    file: UploadFile = File(...),
    delimiter: str = Form(","),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import data from CSV file.

    Upload and process CSV file with GBM Logística data.
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format (.csv)")

    service = DataImportService(db)

    try:
        file_content = await file.read()
        result = await service.import_from_csv(
            site_id=site_id,
            data_source_id=data_source_id,
            file_content=file_content,
            file_name=file.filename,
            user_id=current_user.id,
            delimiter=delimiter
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== API INTEGRATION ====================

@router.post("/sync/{site_id}/{data_source_id}", response_model=Dict[str, Any])
async def sync_from_api(
    site_id: int,
    data_source_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sync data from external API.

    Trigger synchronization with external API (e.g., GBM Logística API).
    """
    service = DataImportService(db)

    try:
        result = await service.sync_from_api(
            site_id=site_id,
            data_source_id=data_source_id,
            user_id=current_user.id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== MANUAL ENTRY ====================

@router.post("/manual-entry/{site_id}/{data_source_id}", response_model=Dict[str, Any])
async def create_manual_entry(
    site_id: int,
    data_source_id: int,
    entry: ManualEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create manual data entry.

    Manually enter a single operational record.
    """
    service = DataImportService(db)

    try:
        result = await service.create_manual_entry(
            site_id=site_id,
            data_source_id=data_source_id,
            data=entry.dict(),
            user_id=current_user.id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== IMPORT MANAGEMENT ====================

@router.get("/imports/{site_id}", response_model=List[Dict[str, Any]])
async def get_import_history(
    site_id: int,
    limit: int = Query(50, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get import history for a site.

    Returns recent import operations with status and statistics.
    """
    service = DataImportService(db)
    return await service.get_import_history(site_id, limit)


@router.post("/imports/{import_id}/approve", response_model=Dict[str, Any])
async def approve_import(
    import_id: int,
    approval: ImportApproval,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve or reject a pending import.

    Used when data source requires manual approval.
    """
    # TODO: Implement approval logic
    return {
        "status": "approved" if approval.approved else "rejected",
        "import_id": import_id,
        "message": "Import approval processed"
    }


# ==================== INSIGHTS & ANALYTICS ====================

@router.get("/insights/{site_id}/overview", response_model=Dict[str, Any])
async def get_operational_overview(
    site_id: int,
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get operational overview and insights.

    Comprehensive analysis of GBM operational data with KPIs and insights.
    """
    service = GBMInsightsService(db)
    return await service.get_operational_overview(site_id, start_date, end_date)


@router.get("/insights/{site_id}/benchmarks", response_model=Dict[str, Any])
async def get_benchmarks(
    site_id: int,
    operation_type: Optional[str] = Query(None, description="Filter by operation type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get performance benchmarks.

    Compare site performance against industry standards.
    """
    service = GBMInsightsService(db)
    return await service.get_benchmarks(site_id, operation_type)


@router.get("/insights/{site_id}/predictions", response_model=Dict[str, Any])
async def predict_volume(
    site_id: int,
    days_ahead: int = Query(7, description="Number of days to predict", ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Predict operational volume.

    Time-series prediction of operational volume for upcoming days.
    """
    service = GBMInsightsService(db)
    return await service.predict_volume(site_id, days_ahead)


# ==================== DATA TEMPLATES ====================

@router.get("/templates/excel", response_model=Dict[str, Any])
async def get_excel_template(
    current_user: User = Depends(get_current_user)
):
    """
    Get Excel import template.

    Returns information about the expected Excel format for imports.
    """
    return {
        "template_version": "1.0",
        "description": "Excel template for GBM Logistics data import",
        "required_columns": [
            {"name": "operation_type", "type": "text", "description": "Type of operation (road_discharge, rail_discharge, ship_loading, receiving)"},
            {"name": "operation_date", "type": "datetime", "description": "Date and time of operation"},
            {"name": "net_weight_kg", "type": "number", "description": "Net weight in kilograms"}
        ],
        "optional_columns": [
            {"name": "external_id", "type": "text", "description": "External system ID"},
            {"name": "vehicle_id", "type": "text", "description": "Vehicle identifier"},
            {"name": "product_type", "type": "text", "description": "Product type (corn, soy, wheat, etc.)"},
            {"name": "gross_weight_kg", "type": "number", "description": "Gross weight in kg"},
            {"name": "tare_weight_kg", "type": "number", "description": "Tare weight in kg"},
            {"name": "moisture_percent", "type": "number", "description": "Moisture percentage"},
            {"name": "impurity_percent", "type": "number", "description": "Impurity percentage"},
            {"name": "loading_time_minutes", "type": "number", "description": "Loading time in minutes"},
            {"name": "waiting_time_minutes", "type": "number", "description": "Waiting time in minutes"},
            {"name": "origin", "type": "text", "description": "Origin location"},
            {"name": "destination", "type": "text", "description": "Destination location"}
        ],
        "example_data": [
            {
                "operation_type": "ship_loading",
                "operation_date": "2025-01-15 14:30:00",
                "net_weight_kg": 35000,
                "vehicle_id": "MV GRAIN CARRIER",
                "product_type": "soy",
                "loading_time_minutes": 120,
                "waiting_time_minutes": 45
            }
        ]
    }


@router.get("/templates/field-mappings", response_model=Dict[str, Any])
async def get_field_mapping_examples(
    current_user: User = Depends(get_current_user)
):
    """
    Get field mapping examples.

    Examples of field mappings from GBM format to OptiFlow format.
    """
    return {
        "gbm_logistics": {
            "description": "Standard GBM Logística field mapping",
            "mapping": {
                "Data": "operation_date",
                "Tipo": "operation_type",
                "Placa": "vehicle_id",
                "Produto": "product_type",
                "Peso Bruto": "gross_weight_kg",
                "Tara": "tare_weight_kg",
                "Peso Líquido": "net_weight_kg",
                "Umidade": "moisture_percent",
                "Impureza": "impurity_percent",
                "Origem": "origin",
                "Destino": "destination"
            }
        },
        "custom_api": {
            "description": "Custom API field mapping example",
            "mapping": {
                "date_time": "operation_date",
                "op_type": "operation_type",
                "truck_plate": "vehicle_id",
                "commodity": "product_type",
                "net_wt": "net_weight_kg"
            }
        }
    }
