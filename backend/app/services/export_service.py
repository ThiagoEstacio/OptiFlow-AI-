"""
Export Service

Service for exporting time-series data and annotations to various formats.

Supported formats:
- CSV (Comma Separated Values)
- JSON (JavaScript Object Notation)
- Excel (XLSX)
- Parquet (for big data workflows)

Use cases:
- Export trend data for external analysis
- Generate reports for compliance
- Data exchange with other systems
- Backup and archival
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from io import BytesIO, StringIO
import json
import csv

from loguru import logger

from app.services.timeseries_service import TagSeries, DataPoint
from app.models.annotation import Annotation


class ExportFormat:
    """Export format constants"""
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    PARQUET = "parquet"


class ExportService:
    """
    Service for exporting data to various formats.
    """

    def __init__(self):
        """Initialize export service"""
        logger.info("ExportService initialized")

    # ==================== CSV Export ====================

    async def export_tag_series_to_csv(
        self,
        tag_series: TagSeries,
        include_quality: bool = True,
        include_metadata: bool = False
    ) -> str:
        """
        Export single tag series to CSV format.

        Args:
            tag_series: TagSeries to export
            include_quality: Include quality column
            include_metadata: Include metadata column

        Returns:
            CSV string
        """
        logger.info(f"Exporting tag {tag_series.tag_id} to CSV ({len(tag_series.data_points)} points)")

        output = StringIO()
        writer = csv.writer(output)

        # Write header
        header = ["timestamp", "value"]
        if include_quality:
            header.append("quality")
        if include_metadata:
            header.append("metadata")
        writer.writerow(header)

        # Write data rows
        for dp in tag_series.data_points:
            row = [
                dp.timestamp.isoformat(),
                dp.value
            ]
            if include_quality:
                row.append(dp.quality or "Good")
            if include_metadata:
                metadata = getattr(dp, 'metadata', {})
                row.append(json.dumps(metadata) if metadata else "")
            writer.writerow(row)

        return output.getvalue()

    async def export_multiple_tags_to_csv(
        self,
        tag_series_list: List[TagSeries],
        format_type: str = "wide"
    ) -> str:
        """
        Export multiple tag series to CSV format.

        Args:
            tag_series_list: List of TagSeries to export
            format_type: "wide" (one column per tag) or "long" (one row per measurement)

        Returns:
            CSV string
        """
        logger.info(f"Exporting {len(tag_series_list)} tags to CSV (format: {format_type})")

        if format_type == "wide":
            return await self._export_wide_format(tag_series_list)
        else:
            return await self._export_long_format(tag_series_list)

    async def _export_wide_format(self, tag_series_list: List[TagSeries]) -> str:
        """Export in wide format (one column per tag)"""
        if not tag_series_list:
            return ""

        output = StringIO()
        writer = csv.writer(output)

        # Get all unique timestamps
        all_timestamps = set()
        for series in tag_series_list:
            for dp in series.data_points:
                all_timestamps.add(dp.timestamp)

        sorted_timestamps = sorted(all_timestamps)

        # Build header
        header = ["timestamp"]
        for series in tag_series_list:
            tag_name = series.tag_name or series.tag_id
            header.append(tag_name)
        writer.writerow(header)

        # Build data rows
        for timestamp in sorted_timestamps:
            row = [timestamp.isoformat()]

            for series in tag_series_list:
                # Find value for this timestamp
                value = ""
                for dp in series.data_points:
                    if dp.timestamp == timestamp:
                        value = str(dp.value)
                        break
                row.append(value)

            writer.writerow(row)

        return output.getvalue()

    async def _export_long_format(self, tag_series_list: List[TagSeries]) -> str:
        """Export in long format (one row per measurement)"""
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["timestamp", "tag_id", "tag_name", "value", "quality"])

        # Data rows
        for series in tag_series_list:
            tag_name = series.tag_name or series.tag_id
            for dp in series.data_points:
                writer.writerow([
                    dp.timestamp.isoformat(),
                    series.tag_id,
                    tag_name,
                    dp.value,
                    dp.quality or "Good"
                ])

        return output.getvalue()

    async def export_annotations_to_csv(
        self,
        annotations: List[Annotation]
    ) -> str:
        """
        Export annotations to CSV format.

        Args:
            annotations: List of annotations to export

        Returns:
            CSV string
        """
        logger.info(f"Exporting {len(annotations)} annotations to CSV")

        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "id",
            "type",
            "severity",
            "title",
            "content",
            "start_time",
            "end_time",
            "duration_seconds",
            "tag_id",
            "device_id",
            "site_id",
            "created_by",
            "created_by_name",
            "created_at",
            "is_public",
            "pinned"
        ])

        # Data rows
        for annotation in annotations:
            writer.writerow([
                str(annotation.id),
                annotation.annotation_type.value,
                annotation.severity.value,
                annotation.title,
                annotation.content or "",
                annotation.start_time.isoformat(),
                annotation.end_time.isoformat() if annotation.end_time else "",
                annotation.duration_seconds,
                str(annotation.tag_id) if annotation.tag_id else "",
                str(annotation.device_id) if annotation.device_id else "",
                str(annotation.site_id) if annotation.site_id else "",
                annotation.created_by,
                annotation.created_by_name or "",
                annotation.created_at.isoformat(),
                annotation.is_public,
                annotation.pinned
            ])

        return output.getvalue()

    # ==================== JSON Export ====================

    async def export_tag_series_to_json(
        self,
        tag_series: TagSeries,
        pretty: bool = False
    ) -> str:
        """
        Export single tag series to JSON format.

        Args:
            tag_series: TagSeries to export
            pretty: Pretty print JSON

        Returns:
            JSON string
        """
        logger.info(f"Exporting tag {tag_series.tag_id} to JSON ({len(tag_series.data_points)} points)")

        data = tag_series.to_dict()

        if pretty:
            return json.dumps(data, indent=2, default=str)
        else:
            return json.dumps(data, default=str)

    async def export_multiple_tags_to_json(
        self,
        tag_series_list: List[TagSeries],
        pretty: bool = False
    ) -> str:
        """
        Export multiple tag series to JSON format.

        Args:
            tag_series_list: List of TagSeries to export
            pretty: Pretty print JSON

        Returns:
            JSON string
        """
        logger.info(f"Exporting {len(tag_series_list)} tags to JSON")

        data = {
            "tags": [series.to_dict() for series in tag_series_list],
            "export_time": datetime.utcnow().isoformat(),
            "tag_count": len(tag_series_list),
            "total_data_points": sum(len(s.data_points) for s in tag_series_list)
        }

        if pretty:
            return json.dumps(data, indent=2, default=str)
        else:
            return json.dumps(data, default=str)

    async def export_annotations_to_json(
        self,
        annotations: List[Annotation],
        pretty: bool = False
    ) -> str:
        """
        Export annotations to JSON format.

        Args:
            annotations: List of annotations to export
            pretty: Pretty print JSON

        Returns:
            JSON string
        """
        logger.info(f"Exporting {len(annotations)} annotations to JSON")

        data = {
            "annotations": [annotation.to_dict() for annotation in annotations],
            "export_time": datetime.utcnow().isoformat(),
            "annotation_count": len(annotations)
        }

        if pretty:
            return json.dumps(data, indent=2, default=str)
        else:
            return json.dumps(data, default=str)

    # ==================== Combined Export ====================

    async def export_trend_with_annotations(
        self,
        tag_series: TagSeries,
        annotations: List[Annotation],
        format_type: str = "json",
        pretty: bool = False
    ) -> str:
        """
        Export trend data with associated annotations.

        Useful for exporting complete context of a time period.

        Args:
            tag_series: Tag data
            annotations: Associated annotations
            format_type: "json" or "csv"
            pretty: Pretty print (for JSON)

        Returns:
            Exported data string
        """
        logger.info(f"Exporting trend with {len(tag_series.data_points)} points and {len(annotations)} annotations")

        if format_type == "json":
            data = {
                "tag": tag_series.to_dict(),
                "annotations": [annotation.to_dict() for annotation in annotations],
                "export_time": datetime.utcnow().isoformat(),
                "data_point_count": len(tag_series.data_points),
                "annotation_count": len(annotations)
            }

            if pretty:
                return json.dumps(data, indent=2, default=str)
            else:
                return json.dumps(data, default=str)

        elif format_type == "csv":
            # For CSV, export data and annotations separately
            output = StringIO()
            writer = csv.writer(output)

            # Write tag data section
            writer.writerow(["# Tag Data"])
            writer.writerow(["timestamp", "value", "quality"])
            for dp in tag_series.data_points:
                writer.writerow([
                    dp.timestamp.isoformat(),
                    dp.value,
                    dp.quality or "Good"
                ])

            writer.writerow([])  # Empty row

            # Write annotations section
            writer.writerow(["# Annotations"])
            writer.writerow(["start_time", "end_time", "type", "severity", "title", "content"])
            for annotation in annotations:
                writer.writerow([
                    annotation.start_time.isoformat(),
                    annotation.end_time.isoformat() if annotation.end_time else "",
                    annotation.annotation_type.value,
                    annotation.severity.value,
                    annotation.title,
                    annotation.content or ""
                ])

            return output.getvalue()

        else:
            raise ValueError(f"Unsupported format: {format_type}")

    # ==================== Excel Export ====================

    async def export_to_excel(
        self,
        tag_series_list: List[TagSeries],
        annotations: Optional[List[Annotation]] = None
    ) -> BytesIO:
        """
        Export data to Excel format (XLSX).

        Creates separate sheets for:
        - Tag data (one sheet per tag or combined)
        - Annotations
        - Statistics

        Args:
            tag_series_list: List of tag series to export
            annotations: Optional list of annotations

        Returns:
            BytesIO buffer with Excel file
        """
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
        except ImportError:
            logger.error("openpyxl not installed - cannot export to Excel")
            raise ValueError("Excel export requires openpyxl package")

        logger.info(f"Exporting {len(tag_series_list)} tags to Excel")

        # Create workbook
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # Remove default sheet

        # Create tag data sheet (wide format)
        ws_data = wb.create_sheet("Tag Data")

        # Header row
        header = ["Timestamp"]
        for series in tag_series_list:
            header.append(series.tag_name or series.tag_id)
        ws_data.append(header)

        # Style header
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        for cell in ws_data[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        # Get all timestamps
        all_timestamps = set()
        for series in tag_series_list:
            for dp in series.data_points:
                all_timestamps.add(dp.timestamp)
        sorted_timestamps = sorted(all_timestamps)

        # Write data rows
        for timestamp in sorted_timestamps:
            row = [timestamp.isoformat()]
            for series in tag_series_list:
                value = ""
                for dp in series.data_points:
                    if dp.timestamp == timestamp:
                        value = dp.value
                        break
                row.append(value)
            ws_data.append(row)

        # Auto-size columns
        for column in ws_data.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws_data.column_dimensions[column_letter].width = adjusted_width

        # Create statistics sheet
        ws_stats = wb.create_sheet("Statistics")
        ws_stats.append(["Tag", "Min", "Max", "Average", "Count", "Range"])

        # Style header
        for cell in ws_stats[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        # Write statistics
        for series in tag_series_list:
            if series.statistics:
                ws_stats.append([
                    series.tag_name or series.tag_id,
                    series.statistics.get("min", ""),
                    series.statistics.get("max", ""),
                    series.statistics.get("avg", ""),
                    series.statistics.get("count", ""),
                    series.statistics.get("range", "")
                ])

        # Auto-size columns
        for column in ws_stats.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            ws_stats.column_dimensions[column_letter].width = adjusted_width

        # Create annotations sheet if provided
        if annotations:
            ws_annotations = wb.create_sheet("Annotations")
            ws_annotations.append([
                "Type", "Severity", "Title", "Start Time", "End Time",
                "Duration (s)", "Created By", "Created At"
            ])

            # Style header
            for cell in ws_annotations[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

            # Write annotations
            for annotation in annotations:
                ws_annotations.append([
                    annotation.annotation_type.value,
                    annotation.severity.value,
                    annotation.title,
                    annotation.start_time.isoformat(),
                    annotation.end_time.isoformat() if annotation.end_time else "",
                    annotation.duration_seconds,
                    annotation.created_by_name or annotation.created_by,
                    annotation.created_at.isoformat()
                ])

            # Auto-size columns
            for column in ws_annotations.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws_annotations.column_dimensions[column_letter].width = adjusted_width

        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        logger.info("Excel export completed")
        return output

    # ==================== Summary Export ====================

    async def export_summary_report(
        self,
        tag_series_list: List[TagSeries],
        annotations: List[Annotation],
        format_type: str = "json"
    ) -> str:
        """
        Export summary report with aggregated statistics.

        Args:
            tag_series_list: List of tag series
            annotations: List of annotations
            format_type: "json" or "csv"

        Returns:
            Exported report string
        """
        logger.info(f"Generating summary report for {len(tag_series_list)} tags")

        # Calculate aggregated statistics
        total_data_points = sum(len(s.data_points) for s in tag_series_list)

        tag_summaries = []
        for series in tag_series_list:
            summary = {
                "tag_id": series.tag_id,
                "tag_name": series.tag_name,
                "data_point_count": len(series.data_points),
                "statistics": series.statistics or {}
            }
            tag_summaries.append(summary)

        # Annotation summary
        annotation_by_type = {}
        annotation_by_severity = {}

        for annotation in annotations:
            type_key = annotation.annotation_type.value
            severity_key = annotation.severity.value

            annotation_by_type[type_key] = annotation_by_type.get(type_key, 0) + 1
            annotation_by_severity[severity_key] = annotation_by_severity.get(severity_key, 0) + 1

        report = {
            "export_time": datetime.utcnow().isoformat(),
            "tag_count": len(tag_series_list),
            "total_data_points": total_data_points,
            "annotation_count": len(annotations),
            "tags": tag_summaries,
            "annotations_by_type": annotation_by_type,
            "annotations_by_severity": annotation_by_severity
        }

        if format_type == "json":
            return json.dumps(report, indent=2, default=str)
        elif format_type == "csv":
            # CSV summary format
            output = StringIO()
            writer = csv.writer(output)

            writer.writerow(["# Export Summary"])
            writer.writerow(["Export Time", report["export_time"]])
            writer.writerow(["Tag Count", report["tag_count"]])
            writer.writerow(["Total Data Points", report["total_data_points"]])
            writer.writerow(["Annotation Count", report["annotation_count"]])
            writer.writerow([])

            writer.writerow(["# Tag Statistics"])
            writer.writerow(["Tag ID", "Tag Name", "Data Points", "Min", "Max", "Average"])
            for tag in tag_summaries:
                stats = tag["statistics"]
                writer.writerow([
                    tag["tag_id"],
                    tag["tag_name"] or "",
                    tag["data_point_count"],
                    stats.get("min", ""),
                    stats.get("max", ""),
                    stats.get("avg", "")
                ])

            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format_type}")


# Global export service instance
export_service = ExportService()
