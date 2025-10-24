"""
Tests for Export Service

Tests data export to CSV, JSON, and Excel formats.
"""
import pytest
from datetime import datetime, timedelta
import json
from io import BytesIO

from app.services.export_service import ExportService, ExportFormat
from app.services.timeseries_service import DataPoint, TagSeries
from app.models.annotation import Annotation, AnnotationType, AnnotationSeverity


@pytest.fixture
def export_service():
    """Create export service instance"""
    return ExportService()


@pytest.fixture
def sample_tag_series():
    """Create sample tag series"""
    data_points = []
    start_time = datetime.now()

    for i in range(10):
        timestamp = start_time + timedelta(minutes=i)
        data_points.append(DataPoint(
            timestamp=timestamp,
            value=20.0 + i,
            quality="Good"
        ))

    return TagSeries(
        tag_id="tag1",
        tag_name="Temperature",
        data_points=data_points,
        statistics={"min": 20.0, "max": 29.0, "avg": 24.5, "count": 10}
    )


@pytest.fixture
def sample_annotations(db_session):
    """Create sample annotations"""
    annotations = []
    start_time = datetime.utcnow()

    for i in range(5):
        annotation = Annotation(
            annotation_type=AnnotationType.EVENT,
            severity=AnnotationSeverity.INFO,
            title=f"Event {i}",
            content=f"Content {i}",
            start_time=start_time + timedelta(hours=i),
            created_by="test_user"
        )
        annotations.append(annotation)
        db_session.add(annotation)

    db_session.commit()
    return annotations


class TestCSVExport:
    """Test CSV export functionality"""

    @pytest.mark.asyncio
    async def test_export_single_tag_csv(self, export_service, sample_tag_series):
        """Test exporting single tag to CSV"""
        result = await export_service.export_tag_series_to_csv(
            tag_series=sample_tag_series,
            include_quality=True
        )

        assert isinstance(result, str)
        assert "timestamp,value,quality" in result
        lines = result.strip().split("\n")
        assert len(lines) == 11  # Header + 10 data rows

    @pytest.mark.asyncio
    async def test_export_single_tag_csv_no_quality(self, export_service, sample_tag_series):
        """Test exporting single tag to CSV without quality"""
        result = await export_service.export_tag_series_to_csv(
            tag_series=sample_tag_series,
            include_quality=False
        )

        assert "timestamp,value" in result
        assert "quality" not in result.split("\n")[0]

    @pytest.mark.asyncio
    async def test_export_multiple_tags_csv_wide(self, export_service):
        """Test exporting multiple tags to CSV (wide format)"""
        series1 = TagSeries(
            tag_id="tag1",
            tag_name="Temperature",
            data_points=[
                DataPoint(datetime.now(), 20.0, "Good"),
                DataPoint(datetime.now() + timedelta(minutes=1), 21.0, "Good")
            ]
        )

        series2 = TagSeries(
            tag_id="tag2",
            tag_name="Pressure",
            data_points=[
                DataPoint(datetime.now(), 100.0, "Good"),
                DataPoint(datetime.now() + timedelta(minutes=1), 101.0, "Good")
            ]
        )

        result = await export_service.export_multiple_tags_to_csv(
            tag_series_list=[series1, series2],
            format_type="wide"
        )

        assert isinstance(result, str)
        lines = result.strip().split("\n")
        header = lines[0]
        assert "Temperature" in header
        assert "Pressure" in header

    @pytest.mark.asyncio
    async def test_export_multiple_tags_csv_long(self, export_service):
        """Test exporting multiple tags to CSV (long format)"""
        series1 = TagSeries(
            tag_id="tag1",
            tag_name="Temperature",
            data_points=[DataPoint(datetime.now(), 20.0, "Good")]
        )

        series2 = TagSeries(
            tag_id="tag2",
            tag_name="Pressure",
            data_points=[DataPoint(datetime.now(), 100.0, "Good")]
        )

        result = await export_service.export_multiple_tags_to_csv(
            tag_series_list=[series1, series2],
            format_type="long"
        )

        assert isinstance(result, str)
        assert "tag_id,tag_name,value" in result

    @pytest.mark.asyncio
    async def test_export_annotations_csv(self, export_service, sample_annotations):
        """Test exporting annotations to CSV"""
        result = await export_service.export_annotations_to_csv(
            annotations=sample_annotations
        )

        assert isinstance(result, str)
        assert "id,type,severity,title" in result
        lines = result.strip().split("\n")
        assert len(lines) == 6  # Header + 5 data rows

    @pytest.mark.asyncio
    async def test_export_empty_list_csv(self, export_service):
        """Test exporting empty list to CSV"""
        result = await export_service.export_multiple_tags_to_csv(
            tag_series_list=[],
            format_type="wide"
        )

        assert result == ""


class TestJSONExport:
    """Test JSON export functionality"""

    @pytest.mark.asyncio
    async def test_export_single_tag_json(self, export_service, sample_tag_series):
        """Test exporting single tag to JSON"""
        result = await export_service.export_tag_series_to_json(
            tag_series=sample_tag_series,
            pretty=False
        )

        assert isinstance(result, str)
        data = json.loads(result)
        assert data["tag_id"] == "tag1"
        assert data["tag_name"] == "Temperature"
        assert len(data["data_points"]) == 10

    @pytest.mark.asyncio
    async def test_export_single_tag_json_pretty(self, export_service, sample_tag_series):
        """Test exporting single tag to JSON with pretty print"""
        result = await export_service.export_tag_series_to_json(
            tag_series=sample_tag_series,
            pretty=True
        )

        assert isinstance(result, str)
        assert "\n" in result  # Pretty printed has newlines
        data = json.loads(result)
        assert data["tag_id"] == "tag1"

    @pytest.mark.asyncio
    async def test_export_multiple_tags_json(self, export_service):
        """Test exporting multiple tags to JSON"""
        series1 = TagSeries(
            tag_id="tag1",
            tag_name="Temperature",
            data_points=[DataPoint(datetime.now(), 20.0, "Good")]
        )

        series2 = TagSeries(
            tag_id="tag2",
            tag_name="Pressure",
            data_points=[DataPoint(datetime.now(), 100.0, "Good")]
        )

        result = await export_service.export_multiple_tags_to_json(
            tag_series_list=[series1, series2],
            pretty=True
        )

        data = json.loads(result)
        assert "tags" in data
        assert len(data["tags"]) == 2
        assert "export_time" in data
        assert data["tag_count"] == 2

    @pytest.mark.asyncio
    async def test_export_annotations_json(self, export_service, sample_annotations):
        """Test exporting annotations to JSON"""
        result = await export_service.export_annotations_to_json(
            annotations=sample_annotations,
            pretty=True
        )

        data = json.loads(result)
        assert "annotations" in data
        assert len(data["annotations"]) == 5
        assert "annotation_count" in data


class TestCombinedExport:
    """Test combined export of trends and annotations"""

    @pytest.mark.asyncio
    async def test_export_trend_with_annotations_json(
        self, export_service, sample_tag_series, sample_annotations
    ):
        """Test exporting trend with annotations to JSON"""
        result = await export_service.export_trend_with_annotations(
            tag_series=sample_tag_series,
            annotations=sample_annotations,
            format_type="json",
            pretty=True
        )

        data = json.loads(result)
        assert "tag" in data
        assert "annotations" in data
        assert data["data_point_count"] == 10
        assert data["annotation_count"] == 5

    @pytest.mark.asyncio
    async def test_export_trend_with_annotations_csv(
        self, export_service, sample_tag_series, sample_annotations
    ):
        """Test exporting trend with annotations to CSV"""
        result = await export_service.export_trend_with_annotations(
            tag_series=sample_tag_series,
            annotations=sample_annotations,
            format_type="csv"
        )

        assert isinstance(result, str)
        assert "# Tag Data" in result
        assert "# Annotations" in result

    @pytest.mark.asyncio
    async def test_export_trend_invalid_format(
        self, export_service, sample_tag_series, sample_annotations
    ):
        """Test exporting with invalid format"""
        with pytest.raises(ValueError):
            await export_service.export_trend_with_annotations(
                tag_series=sample_tag_series,
                annotations=sample_annotations,
                format_type="invalid_format"
            )


class TestExcelExport:
    """Test Excel export functionality"""

    @pytest.mark.asyncio
    async def test_export_to_excel(self, export_service):
        """Test exporting to Excel"""
        series1 = TagSeries(
            tag_id="tag1",
            tag_name="Temperature",
            data_points=[
                DataPoint(datetime.now(), 20.0, "Good"),
                DataPoint(datetime.now() + timedelta(minutes=1), 21.0, "Good")
            ],
            statistics={"min": 20.0, "max": 21.0, "avg": 20.5, "count": 2}
        )

        try:
            result = await export_service.export_to_excel(
                tag_series_list=[series1],
                annotations=None
            )

            assert isinstance(result, BytesIO)
            assert result.getvalue()  # Has content

        except ValueError as e:
            # openpyxl not installed
            assert "openpyxl" in str(e)
            pytest.skip("openpyxl not installed")

    @pytest.mark.asyncio
    async def test_export_to_excel_with_annotations(
        self, export_service, sample_annotations
    ):
        """Test exporting to Excel with annotations"""
        series1 = TagSeries(
            tag_id="tag1",
            tag_name="Temperature",
            data_points=[DataPoint(datetime.now(), 20.0, "Good")]
        )

        try:
            result = await export_service.export_to_excel(
                tag_series_list=[series1],
                annotations=sample_annotations
            )

            assert isinstance(result, BytesIO)

        except ValueError as e:
            assert "openpyxl" in str(e)
            pytest.skip("openpyxl not installed")


class TestSummaryReport:
    """Test summary report generation"""

    @pytest.mark.asyncio
    async def test_export_summary_report_json(
        self, export_service, sample_annotations
    ):
        """Test generating summary report in JSON"""
        series1 = TagSeries(
            tag_id="tag1",
            tag_name="Temperature",
            data_points=[DataPoint(datetime.now(), 20.0, "Good")],
            statistics={"min": 20.0, "max": 20.0, "avg": 20.0, "count": 1}
        )

        result = await export_service.export_summary_report(
            tag_series_list=[series1],
            annotations=sample_annotations,
            format_type="json"
        )

        data = json.loads(result)
        assert "export_time" in data
        assert "tag_count" in data
        assert "total_data_points" in data
        assert "annotation_count" in data
        assert "tags" in data
        assert "annotations_by_type" in data

    @pytest.mark.asyncio
    async def test_export_summary_report_csv(
        self, export_service, sample_annotations
    ):
        """Test generating summary report in CSV"""
        series1 = TagSeries(
            tag_id="tag1",
            tag_name="Temperature",
            data_points=[DataPoint(datetime.now(), 20.0, "Good")],
            statistics={"min": 20.0, "max": 20.0, "avg": 20.0, "count": 1}
        )

        result = await export_service.export_summary_report(
            tag_series_list=[series1],
            annotations=sample_annotations,
            format_type="csv"
        )

        assert isinstance(result, str)
        assert "# Export Summary" in result
        assert "# Tag Statistics" in result

    @pytest.mark.asyncio
    async def test_export_summary_invalid_format(
        self, export_service, sample_annotations
    ):
        """Test generating summary with invalid format"""
        series1 = TagSeries(
            tag_id="tag1",
            tag_name="Temperature",
            data_points=[]
        )

        with pytest.raises(ValueError):
            await export_service.export_summary_report(
                tag_series_list=[series1],
                annotations=sample_annotations,
                format_type="invalid"
            )


class TestExportFormats:
    """Test export format constants"""

    def test_export_format_constants(self):
        """Test export format constants"""
        assert ExportFormat.CSV == "csv"
        assert ExportFormat.JSON == "json"
        assert ExportFormat.EXCEL == "excel"
        assert ExportFormat.PARQUET == "parquet"
