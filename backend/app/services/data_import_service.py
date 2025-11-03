"""
Data Import Service

Multi-source data import service for:
- Excel/CSV file imports
- External API integration (GBM Logística, etc.)
- Manual data entry
- Data validation and transformation
"""

import pandas as pd
import openpyxl
from typing import Dict, Any, List, Optional, BinaryIO
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import asyncio
import httpx
import json
import io

from app.models.external_data import DataSource, DataImport, GBMLogisticsData
from app.models.operational_data import TruckEntry, ShipLoading
from app.core.logging import get_logger
from app.services.influxdb_service import influxdb_service

logger = get_logger(__name__)


class DataImportService:
    """
    Service for importing data from multiple sources.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== EXCEL/CSV IMPORT ====================

    async def import_from_excel(
        self,
        site_id: int,
        data_source_id: int,
        file_content: BinaryIO,
        file_name: str,
        user_id: int,
        sheet_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Import data from Excel file.

        Args:
            site_id: Site ID
            data_source_id: Data source configuration ID
            file_content: File binary content
            file_name: Original filename
            user_id: User performing the import
            sheet_name: Excel sheet name (optional, defaults to first sheet)

        Returns:
            Import result with statistics
        """
        # Create import record
        import_record = DataImport(
            data_source_id=data_source_id,
            import_type="excel_upload",
            file_name=file_name,
            status="processing",
            started_at=datetime.utcnow(),
            site_id=site_id,
            created_by=user_id
        )
        self.db.add(import_record)
        await self.db.commit()
        await self.db.refresh(import_record)

        try:
            # Read Excel file
            df = pd.read_excel(file_content, sheet_name=sheet_name or 0)

            # Get data source configuration
            data_source = await self.db.get(DataSource, data_source_id)
            if not data_source:
                raise ValueError(f"Data source {data_source_id} not found")

            # Apply field mapping
            if data_source.field_mapping:
                df = self._apply_field_mapping(df, data_source.field_mapping)

            # Validate data
            validation_result = await self._validate_dataframe(df, data_source)

            if validation_result["has_errors"] and data_source.require_approval:
                import_record.status = "pending"
                import_record.requires_approval = True
                import_record.errors = validation_result["errors"]
                import_record.warnings = validation_result["warnings"]
                import_record.raw_data_sample = df.head(10).to_dict(orient="records")
                await self.db.commit()

                return {
                    "status": "pending_approval",
                    "import_id": import_record.id,
                    "message": "Data validation found errors. Approval required.",
                    "errors": validation_result["errors"],
                    "warnings": validation_result["warnings"]
                }

            # Import records
            import_result = await self._import_dataframe_records(
                df,
                data_source,
                import_record.id,
                site_id
            )

            # Update import record
            import_record.status = "completed"
            import_record.records_total = import_result["total"]
            import_record.records_imported = import_result["imported"]
            import_record.records_failed = import_result["failed"]
            import_record.records_duplicate = import_result["duplicate"]
            import_record.completed_at = datetime.utcnow()
            import_record.processing_duration_seconds = (
                import_record.completed_at - import_record.started_at
            ).total_seconds()
            import_record.errors = import_result.get("errors", [])
            import_record.warnings = validation_result["warnings"]

            await self.db.commit()

            return {
                "status": "success",
                "import_id": import_record.id,
                "records_imported": import_result["imported"],
                "records_failed": import_result["failed"],
                "records_duplicate": import_result["duplicate"],
                "warnings": validation_result["warnings"]
            }

        except Exception as e:
            logger.error(f"Excel import failed: {str(e)}")
            import_record.status = "failed"
            import_record.errors = [{"error": str(e)}]
            import_record.completed_at = datetime.utcnow()
            await self.db.commit()

            return {
                "status": "error",
                "import_id": import_record.id,
                "message": str(e)
            }

    async def import_from_csv(
        self,
        site_id: int,
        data_source_id: int,
        file_content: BinaryIO,
        file_name: str,
        user_id: int,
        delimiter: str = ","
    ) -> Dict[str, Any]:
        """Import data from CSV file."""
        # Read CSV
        df = pd.read_csv(file_content, delimiter=delimiter)

        # Convert to Excel format and use Excel import logic
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        return await self.import_from_excel(
            site_id=site_id,
            data_source_id=data_source_id,
            file_content=excel_buffer,
            file_name=file_name.replace('.csv', '.xlsx'),
            user_id=user_id
        )

    def _apply_field_mapping(self, df: pd.DataFrame, field_mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Apply field mapping from external columns to internal schema.

        field_mapping example:
        {
            "Data": "operation_date",
            "Placa": "vehicle_id",
            "Peso Líquido": "net_weight_kg"
        }
        """
        # Rename columns based on mapping
        rename_dict = {k: v for k, v in field_mapping.items() if k in df.columns}
        df = df.rename(columns=rename_dict)
        return df

    async def _validate_dataframe(
        self,
        df: pd.DataFrame,
        data_source: DataSource
    ) -> Dict[str, Any]:
        """
        Validate dataframe data.

        Returns validation result with errors and warnings.
        """
        errors = []
        warnings = []

        # Check required columns
        required_columns = ["operation_type", "operation_date", "net_weight_kg"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            errors.append({
                "type": "missing_columns",
                "message": f"Missing required columns: {', '.join(missing_columns)}"
            })

        # Check for null values in required fields
        for col in required_columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    errors.append({
                        "type": "null_values",
                        "column": col,
                        "count": int(null_count),
                        "message": f"Column '{col}' has {null_count} null values"
                    })

        # Check date formats
        if "operation_date" in df.columns:
            try:
                pd.to_datetime(df["operation_date"])
            except Exception as e:
                errors.append({
                    "type": "invalid_date_format",
                    "column": "operation_date",
                    "message": "Invalid date format in operation_date column"
                })

        # Check numeric fields
        numeric_fields = ["net_weight_kg", "gross_weight_kg", "tare_weight_kg"]
        for field in numeric_fields:
            if field in df.columns:
                non_numeric = pd.to_numeric(df[field], errors='coerce').isnull().sum()
                if non_numeric > 0:
                    warnings.append({
                        "type": "non_numeric_values",
                        "column": field,
                        "count": int(non_numeric),
                        "message": f"Column '{field}' has {non_numeric} non-numeric values"
                    })

        # Apply custom validation rules if defined
        if data_source.validation_rules:
            custom_validation = self._apply_custom_validation(df, data_source.validation_rules)
            errors.extend(custom_validation.get("errors", []))
            warnings.extend(custom_validation.get("warnings", []))

        return {
            "has_errors": len(errors) > 0,
            "errors": errors,
            "warnings": warnings
        }

    def _apply_custom_validation(
        self,
        df: pd.DataFrame,
        validation_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply custom validation rules defined in data source config."""
        errors = []
        warnings = []

        # Example rules:
        # {
        #     "min_weight": 1000,
        #     "max_weight": 100000,
        #     "valid_products": ["corn", "soy", "wheat"]
        # }

        if "min_weight" in validation_rules and "net_weight_kg" in df.columns:
            min_weight = validation_rules["min_weight"]
            invalid_count = (df["net_weight_kg"] < min_weight).sum()
            if invalid_count > 0:
                warnings.append({
                    "type": "weight_below_minimum",
                    "count": int(invalid_count),
                    "message": f"{invalid_count} records have weight below {min_weight} kg"
                })

        if "max_weight" in validation_rules and "net_weight_kg" in df.columns:
            max_weight = validation_rules["max_weight"]
            invalid_count = (df["net_weight_kg"] > max_weight).sum()
            if invalid_count > 0:
                warnings.append({
                    "type": "weight_above_maximum",
                    "count": int(invalid_count),
                    "message": f"{invalid_count} records have weight above {max_weight} kg"
                })

        if "valid_products" in validation_rules and "product_type" in df.columns:
            valid_products = validation_rules["valid_products"]
            invalid_products = ~df["product_type"].isin(valid_products)
            invalid_count = invalid_products.sum()
            if invalid_count > 0:
                warnings.append({
                    "type": "invalid_product_type",
                    "count": int(invalid_count),
                    "message": f"{invalid_count} records have invalid product types"
                })

        return {"errors": errors, "warnings": warnings}

    async def _import_dataframe_records(
        self,
        df: pd.DataFrame,
        data_source: DataSource,
        import_id: int,
        site_id: int
    ) -> Dict[str, Any]:
        """
        Import dataframe records into GBMLogisticsData table.
        """
        imported = 0
        failed = 0
        duplicate = 0
        errors = []

        for idx, row in df.iterrows():
            try:
                # Check for duplicates (based on external_id if present)
                if "external_id" in row and pd.notna(row["external_id"]):
                    existing = await self.db.execute(
                        select(GBMLogisticsData).where(
                            GBMLogisticsData.external_id == str(row["external_id"]),
                            GBMLogisticsData.site_id == site_id
                        )
                    )
                    if existing.scalar_one_or_none():
                        duplicate += 1
                        continue

                # Create record
                record = GBMLogisticsData(
                    import_id=import_id,
                    operation_type=row.get("operation_type", "receiving"),
                    external_id=str(row.get("external_id", "")),
                    external_reference=str(row.get("external_reference", "")),
                    operation_date=pd.to_datetime(row["operation_date"]),
                    completion_date=pd.to_datetime(row["completion_date"]) if "completion_date" in row and pd.notna(row["completion_date"]) else None,
                    vehicle_id=str(row.get("vehicle_id", "")),
                    vehicle_type=str(row.get("vehicle_type", "")),
                    product_type=str(row.get("product_type", "")),
                    product_grade=str(row.get("product_grade", "")),
                    gross_weight_kg=float(row["gross_weight_kg"]) if "gross_weight_kg" in row and pd.notna(row["gross_weight_kg"]) else None,
                    tare_weight_kg=float(row["tare_weight_kg"]) if "tare_weight_kg" in row and pd.notna(row["tare_weight_kg"]) else None,
                    net_weight_kg=float(row["net_weight_kg"]),
                    moisture_percent=float(row["moisture_percent"]) if "moisture_percent" in row and pd.notna(row["moisture_percent"]) else None,
                    impurity_percent=float(row["impurity_percent"]) if "impurity_percent" in row and pd.notna(row["impurity_percent"]) else None,
                    protein_percent=float(row["protein_percent"]) if "protein_percent" in row and pd.notna(row["protein_percent"]) else None,
                    origin=str(row.get("origin", "")),
                    origin_city=str(row.get("origin_city", "")),
                    origin_state=str(row.get("origin_state", "")),
                    destination=str(row.get("destination", "")),
                    loading_time_minutes=float(row["loading_time_minutes"]) if "loading_time_minutes" in row and pd.notna(row["loading_time_minutes"]) else None,
                    waiting_time_minutes=float(row["waiting_time_minutes"]) if "waiting_time_minutes" in row and pd.notna(row["waiting_time_minutes"]) else None,
                    total_time_minutes=float(row["total_time_minutes"]) if "total_time_minutes" in row and pd.notna(row["total_time_minutes"]) else None,
                    freight_value=float(row["freight_value"]) if "freight_value" in row and pd.notna(row["freight_value"]) else None,
                    total_value=float(row["total_value"]) if "total_value" in row and pd.notna(row["total_value"]) else None,
                    status=str(row.get("status", "completed")),
                    berth_number=int(row["berth_number"]) if "berth_number" in row and pd.notna(row["berth_number"]) else None,
                    buyer_company=str(row.get("buyer_company", "")),
                    supplier_company=str(row.get("supplier_company", "")),
                    weather_condition=str(row.get("weather_condition", "")),
                    notes=str(row.get("notes", "")),
                    site_id=site_id,
                    validated=False
                )

                self.db.add(record)
                imported += 1

                # Commit in batches of 100
                if imported % 100 == 0:
                    await self.db.commit()

            except Exception as e:
                failed += 1
                errors.append({
                    "row": int(idx),
                    "error": str(e)
                })
                logger.error(f"Failed to import row {idx}: {str(e)}")

        # Final commit to PostgreSQL
        await self.db.commit()

        # Write to InfluxDB in batch (for time-series performance)
        try:
            influx_operations = []
            for idx, row in df.iterrows():
                if idx >= duplicate:  # Only write non-duplicate records
                    influx_operations.append({
                        "operation_date": pd.to_datetime(row["operation_date"]),
                        "operation_type": str(row.get("operation_type", "receiving")),
                        "product_type": str(row.get("product_type", "")),
                        "vehicle_type": str(row.get("vehicle_type", "")),
                        "status": str(row.get("status", "completed")),
                        "net_weight_kg": float(row["net_weight_kg"]) if pd.notna(row["net_weight_kg"]) else None,
                        "loading_time_minutes": float(row["loading_time_minutes"]) if "loading_time_minutes" in row and pd.notna(row["loading_time_minutes"]) else None,
                        "waiting_time_minutes": float(row["waiting_time_minutes"]) if "waiting_time_minutes" in row and pd.notna(row["waiting_time_minutes"]) else None,
                        "total_value": float(row["total_value"]) if "total_value" in row and pd.notna(row["total_value"]) else None,
                    })

            if influx_operations:
                influx_result = influxdb_service.write_gbm_operations_batch(site_id, influx_operations)
                logger.info(f"InfluxDB write: {influx_result['success']} success, {influx_result['failed']} failed")

        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {str(e)}")
            # Don't fail the import if InfluxDB write fails

        return {
            "total": len(df),
            "imported": imported,
            "failed": failed,
            "duplicate": duplicate,
            "errors": errors[:100]  # Limit to first 100 errors
        }

    # ==================== API INTEGRATION ====================

    async def sync_from_api(
        self,
        site_id: int,
        data_source_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Sync data from external API (e.g., GBM Logística API).

        Args:
            site_id: Site ID
            data_source_id: Data source configuration ID
            user_id: User triggering the sync

        Returns:
            Sync result with statistics
        """
        # Get data source configuration
        data_source = await self.db.get(DataSource, data_source_id)
        if not data_source or data_source.source_type != "api":
            raise ValueError("Invalid API data source")

        # Create import record
        import_record = DataImport(
            data_source_id=data_source_id,
            import_type="api_sync",
            status="processing",
            started_at=datetime.utcnow(),
            site_id=site_id,
            created_by=user_id
        )
        self.db.add(import_record)
        await self.db.commit()
        await self.db.refresh(import_record)

        try:
            # Fetch data from API
            api_data = await self._fetch_from_api(data_source)

            # Convert to DataFrame for processing
            df = pd.DataFrame(api_data)

            # Apply field mapping
            if data_source.field_mapping:
                df = self._apply_field_mapping(df, data_source.field_mapping)

            # Import records
            import_result = await self._import_dataframe_records(
                df,
                data_source,
                import_record.id,
                site_id
            )

            # Update import record and data source
            import_record.status = "completed"
            import_record.records_total = import_result["total"]
            import_record.records_imported = import_result["imported"]
            import_record.records_failed = import_result["failed"]
            import_record.records_duplicate = import_result["duplicate"]
            import_record.completed_at = datetime.utcnow()
            import_record.processing_duration_seconds = (
                import_record.completed_at - import_record.started_at
            ).total_seconds()

            data_source.last_sync_at = datetime.utcnow()
            data_source.last_sync_status = "success"

            await self.db.commit()

            return {
                "status": "success",
                "import_id": import_record.id,
                "records_imported": import_result["imported"],
                "records_failed": import_result["failed"],
                "records_duplicate": import_result["duplicate"]
            }

        except Exception as e:
            logger.error(f"API sync failed: {str(e)}")
            import_record.status = "failed"
            import_record.errors = [{"error": str(e)}]
            import_record.completed_at = datetime.utcnow()

            data_source.last_sync_at = datetime.utcnow()
            data_source.last_sync_status = "failed"
            data_source.last_sync_error = str(e)

            await self.db.commit()

            return {
                "status": "error",
                "import_id": import_record.id,
                "message": str(e)
            }

    async def _fetch_from_api(self, data_source: DataSource) -> List[Dict[str, Any]]:
        """
        Fetch data from external API.

        Supports different auth types: bearer, basic, api_key, none
        """
        if not data_source.api_url:
            raise ValueError("API URL not configured")

        # Prepare headers
        headers = {}
        if data_source.auth_type == "bearer":
            # Decrypt API key (simplified - should use proper encryption)
            api_key = data_source.api_key_encrypted
            headers["Authorization"] = f"Bearer {api_key}"
        elif data_source.auth_type == "api_key":
            api_key = data_source.api_key_encrypted
            headers["X-API-Key"] = api_key

        # Fetch data
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(data_source.api_url, headers=headers)
            response.raise_for_status()

            if data_source.data_format == "json":
                return response.json()
            elif data_source.data_format == "xml":
                # Parse XML (simplified)
                import xmltodict
                return xmltodict.parse(response.text)
            else:
                raise ValueError(f"Unsupported data format: {data_source.data_format}")

    # ==================== MANUAL DATA ENTRY ====================

    async def create_manual_entry(
        self,
        site_id: int,
        data_source_id: int,
        data: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """
        Create a manual data entry.

        Args:
            site_id: Site ID
            data_source_id: Data source ID
            data: Record data
            user_id: User creating the entry

        Returns:
            Created record
        """
        # Create import record for audit
        import_record = DataImport(
            data_source_id=data_source_id,
            import_type="manual_entry",
            status="completed",
            records_total=1,
            records_imported=1,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            site_id=site_id,
            created_by=user_id
        )
        self.db.add(import_record)
        await self.db.commit()
        await self.db.refresh(import_record)

        # Create GBM record
        record = GBMLogisticsData(
            import_id=import_record.id,
            site_id=site_id,
            validated=False,
            **data
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)

        return record.to_dict()

    # ==================== DATA SOURCE MANAGEMENT ====================

    async def create_data_source(
        self,
        site_id: int,
        name: str,
        source_type: str,
        user_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new data source configuration."""
        data_source = DataSource(
            site_id=site_id,
            name=name,
            source_type=source_type,
            created_by=user_id,
            **kwargs
        )
        self.db.add(data_source)
        await self.db.commit()
        await self.db.refresh(data_source)

        return data_source.to_dict()

    async def get_data_sources(self, site_id: int) -> List[Dict[str, Any]]:
        """Get all data sources for a site."""
        result = await self.db.execute(
            select(DataSource).where(DataSource.site_id == site_id)
        )
        data_sources = result.scalars().all()
        return [ds.to_dict() for ds in data_sources]

    async def get_import_history(
        self,
        site_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get import history for a site."""
        result = await self.db.execute(
            select(DataImport)
            .where(DataImport.site_id == site_id)
            .order_by(DataImport.created_at.desc())
            .limit(limit)
        )
        imports = result.scalars().all()
        return [imp.to_dict() for imp in imports]
