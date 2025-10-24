"""
Data Export Service for CSV, JSON, and Excel formats
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import io
import csv
import json
import pandas as pd
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting data in various formats"""

    def __init__(self):
        pass

    async def export_to_csv(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        include_headers: bool = True
    ) -> io.StringIO:
        """
        Export data to CSV format

        Args:
            data: List of dictionaries containing the data
            columns: Optional list of column names (order matters)
            include_headers: Whether to include header row

        Returns:
            StringIO buffer containing CSV data
        """
        try:
            output = io.StringIO()

            if not data:
                return output

            # Determine columns
            if not columns:
                columns = list(data[0].keys())

            # Create CSV writer
            writer = csv.DictWriter(
                output,
                fieldnames=columns,
                extrasaction='ignore'
            )

            # Write headers
            if include_headers:
                writer.writeheader()

            # Write rows
            for row in data:
                # Convert UUID and datetime objects to strings
                cleaned_row = {}
                for key, value in row.items():
                    if isinstance(value, (UUID, datetime)):
                        cleaned_row[key] = str(value)
                    elif value is None:
                        cleaned_row[key] = ""
                    else:
                        cleaned_row[key] = value

                writer.writerow(cleaned_row)

            output.seek(0)
            return output

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise

    async def export_to_json(
        self,
        data: List[Dict[str, Any]],
        pretty: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export data to JSON format

        Args:
            data: List of dictionaries containing the data
            pretty: Whether to format JSON with indentation
            metadata: Optional metadata to include in export

        Returns:
            JSON string
        """
        try:
            # Convert UUID and datetime objects to strings
            cleaned_data = []
            for row in data:
                cleaned_row = {}
                for key, value in row.items():
                    if isinstance(value, UUID):
                        cleaned_row[key] = str(value)
                    elif isinstance(value, datetime):
                        cleaned_row[key] = value.isoformat()
                    else:
                        cleaned_row[key] = value
                cleaned_data.append(cleaned_row)

            # Create export object
            export_object = {
                "data": cleaned_data,
                "count": len(cleaned_data),
                "exported_at": datetime.utcnow().isoformat()
            }

            # Add metadata if provided
            if metadata:
                export_object["metadata"] = metadata

            # Convert to JSON
            if pretty:
                return json.dumps(export_object, indent=2, ensure_ascii=False)
            else:
                return json.dumps(export_object, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            raise

    async def export_to_excel(
        self,
        data: List[Dict[str, Any]],
        sheet_name: str = "Data",
        columns: Optional[List[str]] = None,
        include_index: bool = False,
        auto_adjust_columns: bool = True
    ) -> io.BytesIO:
        """
        Export data to Excel format (.xlsx)

        Args:
            data: List of dictionaries containing the data
            sheet_name: Name of the Excel sheet
            columns: Optional list of column names (order matters)
            include_index: Whether to include row index
            auto_adjust_columns: Whether to auto-adjust column widths

        Returns:
            BytesIO buffer containing Excel file
        """
        try:
            # Convert to DataFrame
            if not data:
                df = pd.DataFrame()
            else:
                df = pd.DataFrame(data)

                # Select and order columns if specified
                if columns:
                    # Only keep columns that exist in the data
                    available_columns = [col for col in columns if col in df.columns]
                    df = df[available_columns]

                # Convert UUID and datetime columns to strings
                for col in df.columns:
                    if df[col].dtype == 'object':
                        df[col] = df[col].apply(
                            lambda x: str(x) if isinstance(x, (UUID, datetime)) else x
                        )

            # Create Excel file in memory
            output = io.BytesIO()

            # Use ExcelWriter with xlsxwriter engine
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=include_index
                )

                # Auto-adjust column widths
                if auto_adjust_columns and not df.empty:
                    worksheet = writer.sheets[sheet_name]

                    for idx, col in enumerate(df.columns):
                        # Calculate column width based on column name and max value length
                        max_len = max(
                            len(str(col)),
                            df[col].astype(str).str.len().max() if not df[col].empty else 0
                        )
                        # Add some padding
                        column_width = min(max_len + 2, 50)
                        worksheet.set_column(idx, idx, column_width)

            output.seek(0)
            return output

        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            raise

    async def export_timeseries_to_csv(
        self,
        timeseries_data: List[Dict[str, Any]],
        pivot: bool = False
    ) -> io.StringIO:
        """
        Export time series data to CSV format with special formatting

        Args:
            timeseries_data: List of time series data points
            pivot: Whether to pivot data (tags as columns, time as rows)

        Returns:
            StringIO buffer containing CSV data
        """
        try:
            if not timeseries_data:
                return io.StringIO()

            if pivot:
                # Convert to DataFrame and pivot
                df = pd.DataFrame(timeseries_data)

                # Pivot table with timestamp as index and tag_id as columns
                if 'timestamp' in df.columns and 'tag_id' in df.columns and 'value' in df.columns:
                    pivot_df = df.pivot(
                        index='timestamp',
                        columns='tag_id',
                        values='value'
                    )

                    # Export to CSV
                    output = io.StringIO()
                    pivot_df.to_csv(output)
                    output.seek(0)
                    return output
                else:
                    # Fallback to regular export
                    return await self.export_to_csv(timeseries_data)
            else:
                return await self.export_to_csv(timeseries_data)

        except Exception as e:
            logger.error(f"Error exporting time series to CSV: {e}")
            raise

    async def export_with_template(
        self,
        data: List[Dict[str, Any]],
        template_config: Dict[str, Any]
    ) -> io.BytesIO:
        """
        Export data using a custom Excel template configuration

        Args:
            data: List of dictionaries containing the data
            template_config: Template configuration with formatting rules

        Returns:
            BytesIO buffer containing Excel file
        """
        try:
            df = pd.DataFrame(data)

            output = io.BytesIO()

            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                workbook = writer.book

                # Extract template settings
                sheet_name = template_config.get('sheet_name', 'Data')
                title = template_config.get('title', 'Export Report')
                columns = template_config.get('columns', list(df.columns))

                # Add worksheet
                worksheet = workbook.add_worksheet(sheet_name)
                writer.sheets[sheet_name] = worksheet

                # Define formats
                title_format = workbook.add_format({
                    'bold': True,
                    'font_size': 16,
                    'align': 'center',
                    'valign': 'vcenter'
                })

                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#4472C4',
                    'font_color': 'white',
                    'border': 1
                })

                # Write title
                worksheet.merge_range(0, 0, 0, len(columns) - 1, title, title_format)

                # Write metadata
                row = 2
                worksheet.write(row, 0, 'Generated:', workbook.add_format({'bold': True}))
                worksheet.write(row, 1, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'))

                # Write headers
                header_row = row + 2
                for col_idx, column in enumerate(columns):
                    worksheet.write(header_row, col_idx, column, header_format)

                # Write data
                for row_idx, row_data in enumerate(df[columns].values, start=header_row + 1):
                    for col_idx, value in enumerate(row_data):
                        if pd.isna(value):
                            worksheet.write(row_idx, col_idx, "")
                        else:
                            worksheet.write(row_idx, col_idx, str(value))

                # Auto-adjust column widths
                for idx, col in enumerate(columns):
                    max_len = max(
                        len(str(col)),
                        df[col].astype(str).str.len().max() if not df[col].empty else 0
                    )
                    worksheet.set_column(idx, idx, min(max_len + 2, 50))

            output.seek(0)
            return output

        except Exception as e:
            logger.error(f"Error exporting with template: {e}")
            raise


# Global export service instance
export_service = ExportService()
