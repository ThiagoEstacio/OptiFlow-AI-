"""
External Data Models for GBM Logistics and Third-Party Integration

Models for importing and tracking data from external sources:
- GBM Logística data (road/rail discharge, ship loading, receiving)
- External API integrations
- Manual data entry
- Excel/CSV imports
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from typing import Dict, Any, Optional
from datetime import datetime


class DataSource(Base):
    """
    Data source configuration for external integrations.

    Tracks different data sources (GBM, custom APIs, manual entry, etc.)
    """
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)

    # Source identification
    name = Column(String(200), nullable=False, index=True)  # "GBM Logística", "Custom API", etc.
    source_type = Column(String(50), nullable=False, index=True)  # api, manual, excel, csv

    # API configuration (if applicable)
    api_url = Column(String(500))
    api_key_encrypted = Column(Text)  # Encrypted API key
    auth_type = Column(String(50))  # bearer, basic, api_key, none

    # Import configuration
    data_format = Column(String(50))  # json, xml, csv, excel
    field_mapping = Column(JSON)  # Map external fields to internal schema

    # Sync settings
    auto_sync = Column(Boolean, default=False)
    sync_interval_minutes = Column(Integer)  # How often to sync
    last_sync_at = Column(DateTime(timezone=True))
    last_sync_status = Column(String(50))  # success, failed, pending
    last_sync_error = Column(Text)

    # Validation rules
    validation_rules = Column(JSON)  # Custom validation rules
    require_approval = Column(Boolean, default=False)  # Require manual approval before import

    # Status
    enabled = Column(Boolean, default=True, index=True)
    notes = Column(Text)

    # Site reference
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    site = relationship("Site")

    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    created_by_user = relationship("User")

    # Relationships
    imports = relationship("DataImport", back_populates="data_source")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source_type": self.source_type,
            "api_url": self.api_url,
            "auth_type": self.auth_type,
            "data_format": self.data_format,
            "field_mapping": self.field_mapping,
            "auto_sync": self.auto_sync,
            "sync_interval_minutes": self.sync_interval_minutes,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "last_sync_status": self.last_sync_status,
            "enabled": self.enabled,
            "require_approval": self.require_approval,
            "notes": self.notes,
            "site_id": self.site_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DataImport(Base):
    """
    Data import log - tracks each import operation.

    Records all data imports from external sources for audit trail.
    """
    __tablename__ = "data_imports"

    id = Column(Integer, primary_key=True, index=True)

    # Source reference
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)
    data_source = relationship("DataSource", back_populates="imports")

    # Import details
    import_type = Column(String(50), nullable=False)  # api_sync, manual_entry, excel_upload, csv_upload
    file_name = Column(String(500))  # Original filename if upload
    file_size_bytes = Column(Integer)

    # Status
    status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed, approved, rejected

    # Results
    records_total = Column(Integer, default=0)
    records_imported = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    records_duplicate = Column(Integer, default=0)

    # Error tracking
    errors = Column(JSON)  # List of error messages
    warnings = Column(JSON)  # List of warnings

    # Approval workflow
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    approval_notes = Column(Text)

    # Processing times
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    processing_duration_seconds = Column(Float)

    # Raw data (for preview/audit)
    raw_data_sample = Column(JSON)  # First few records for preview

    # Site reference
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    site = relationship("Site")

    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    created_by_user = relationship("User", foreign_keys=[created_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])

    # Relationships
    gbm_records = relationship("GBMLogisticsData", back_populates="import_record")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "data_source_id": self.data_source_id,
            "import_type": self.import_type,
            "file_name": self.file_name,
            "file_size_bytes": self.file_size_bytes,
            "status": self.status,
            "records_total": self.records_total,
            "records_imported": self.records_imported,
            "records_failed": self.records_failed,
            "records_duplicate": self.records_duplicate,
            "errors": self.errors,
            "warnings": self.warnings,
            "requires_approval": self.requires_approval,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approval_notes": self.approval_notes,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "processing_duration_seconds": self.processing_duration_seconds,
            "raw_data_sample": self.raw_data_sample,
            "site_id": self.site_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class GBMLogisticsData(Base):
    """
    GBM Logística operational data.

    Stores data from GBM Logística system:
    - Road discharge (descarga rodoviária)
    - Rail discharge (descarga ferroviária)
    - Ship loading (embarque de navios)
    - Receiving operations (recebimento)
    """
    __tablename__ = "gbm_logistics_data"

    id = Column(Integer, primary_key=True, index=True)

    # Import tracking
    import_id = Column(Integer, ForeignKey("data_imports.id"), index=True)
    import_record = relationship("DataImport", back_populates="gbm_records")

    # Operation type
    operation_type = Column(String(50), nullable=False, index=True)
    # road_discharge, rail_discharge, ship_loading, receiving

    # External reference
    external_id = Column(String(200), index=True)  # GBM's internal ID
    external_reference = Column(String(200))  # GBM's reference number

    # Operation details
    operation_date = Column(DateTime(timezone=True), nullable=False, index=True)
    completion_date = Column(DateTime(timezone=True))

    # Vehicle/Transport identification
    vehicle_id = Column(String(100))  # Truck plate, train number, ship name
    vehicle_type = Column(String(50))  # truck, train, ship

    # Product information
    product_type = Column(String(100), index=True)  # corn, soy, wheat, sugar, etc.
    product_grade = Column(String(50))  # Quality grade

    # Quantities
    gross_weight_kg = Column(Float)
    tare_weight_kg = Column(Float)
    net_weight_kg = Column(Float, nullable=False)  # Main quantity metric

    # Quality parameters
    moisture_percent = Column(Float)
    impurity_percent = Column(Float)
    protein_percent = Column(Float)
    broken_percent = Column(Float)
    quality_approved = Column(Boolean)
    quality_notes = Column(Text)

    # Origin/Destination
    origin = Column(String(200))
    origin_city = Column(String(100))
    origin_state = Column(String(50))
    destination = Column(String(200))
    destination_country = Column(String(100))

    # Performance metrics
    loading_time_minutes = Column(Float)
    waiting_time_minutes = Column(Float)
    total_time_minutes = Column(Float)
    throughput_kg_per_hour = Column(Float)

    # Financial
    freight_value = Column(Float)  # R$
    storage_value = Column(Float)  # R$
    service_value = Column(Float)  # R$
    total_value = Column(Float)  # R$

    # Status
    status = Column(String(50), default="pending", index=True)
    # pending, in_progress, completed, cancelled

    # Equipment used
    berth_number = Column(Integer)
    shiploader_id = Column(String(50))
    conveyor_ids = Column(JSON)  # List of conveyor IDs used

    # Contract information
    contract_number = Column(String(100))
    buyer_company = Column(String(200))
    supplier_company = Column(String(200))

    # Operational notes
    weather_condition = Column(String(100))
    incidents = Column(Text)
    delays_description = Column(Text)
    notes = Column(Text)

    # Raw data from GBM (for full audit trail)
    raw_data = Column(JSON)

    # Validation
    validated = Column(Boolean, default=False, index=True)
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    validated_at = Column(DateTime(timezone=True))
    validation_notes = Column(Text)

    # Site reference
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    site = relationship("Site")

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    validated_by_user = relationship("User", foreign_keys=[validated_by])

    def to_dict(self) -> Dict[str, Any]:
        # Calculate efficiency metrics
        efficiency_score = None
        if self.total_time_minutes and self.total_time_minutes > 0:
            expected_time = self.net_weight_kg / 50000 * 60 if self.net_weight_kg else 0  # Assume 50t/h baseline
            efficiency_score = (expected_time / self.total_time_minutes * 100) if expected_time > 0 else None

        return {
            "id": self.id,
            "import_id": self.import_id,
            "operation_type": self.operation_type,
            "external_id": self.external_id,
            "external_reference": self.external_reference,
            "operation_date": self.operation_date.isoformat() if self.operation_date else None,
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "vehicle_id": self.vehicle_id,
            "vehicle_type": self.vehicle_type,
            "product_type": self.product_type,
            "product_grade": self.product_grade,
            "gross_weight_kg": self.gross_weight_kg,
            "tare_weight_kg": self.tare_weight_kg,
            "net_weight_kg": self.net_weight_kg,
            "moisture_percent": self.moisture_percent,
            "impurity_percent": self.impurity_percent,
            "protein_percent": self.protein_percent,
            "broken_percent": self.broken_percent,
            "quality_approved": self.quality_approved,
            "quality_notes": self.quality_notes,
            "origin": self.origin,
            "origin_city": self.origin_city,
            "origin_state": self.origin_state,
            "destination": self.destination,
            "destination_country": self.destination_country,
            "loading_time_minutes": self.loading_time_minutes,
            "waiting_time_minutes": self.waiting_time_minutes,
            "total_time_minutes": self.total_time_minutes,
            "throughput_kg_per_hour": self.throughput_kg_per_hour,
            "efficiency_score": round(efficiency_score, 2) if efficiency_score else None,
            "freight_value": self.freight_value,
            "storage_value": self.storage_value,
            "service_value": self.service_value,
            "total_value": self.total_value,
            "status": self.status,
            "berth_number": self.berth_number,
            "shiploader_id": self.shiploader_id,
            "conveyor_ids": self.conveyor_ids,
            "contract_number": self.contract_number,
            "buyer_company": self.buyer_company,
            "supplier_company": self.supplier_company,
            "weather_condition": self.weather_condition,
            "incidents": self.incidents,
            "delays_description": self.delays_description,
            "notes": self.notes,
            "validated": self.validated,
            "validated_by": self.validated_by,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "validation_notes": self.validation_notes,
            "site_id": self.site_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
