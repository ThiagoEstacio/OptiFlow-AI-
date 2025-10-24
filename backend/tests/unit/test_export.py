"""
Unit tests for Export Service
"""
import pytest
import json
from app.services.export import export_service


@pytest.mark.asyncio
async def test_export_to_csv():
    """Test CSV export"""
    data = [
        {"name": "Item 1", "value": 100, "category": "A"},
        {"name": "Item 2", "value": 200, "category": "B"},
        {"name": "Item 3", "value": 300, "category": "A"}
    ]

    csv_buffer = await export_service.export_to_csv(data)
    csv_content = csv_buffer.getvalue()

    assert "name" in csv_content
    assert "value" in csv_content
    assert "Item 1" in csv_content
    assert "100" in csv_content


@pytest.mark.asyncio
async def test_export_to_csv_with_columns():
    """Test CSV export with specific columns"""
    data = [
        {"name": "Item 1", "value": 100, "category": "A"},
        {"name": "Item 2", "value": 200, "category": "B"}
    ]

    csv_buffer = await export_service.export_to_csv(
        data=data,
        columns=["name", "value"]
    )
    csv_content = csv_buffer.getvalue()

    assert "name" in csv_content
    assert "value" in csv_content
    assert "category" not in csv_content  # Excluded column


@pytest.mark.asyncio
async def test_export_to_json():
    """Test JSON export"""
    data = [
        {"name": "Item 1", "value": 100},
        {"name": "Item 2", "value": 200}
    ]

    json_str = await export_service.export_to_json(data)
    json_data = json.loads(json_str)

    assert "data" in json_data
    assert "count" in json_data
    assert "exported_at" in json_data
    assert json_data["count"] == 2
    assert len(json_data["data"]) == 2


@pytest.mark.asyncio
async def test_export_to_json_with_metadata():
    """Test JSON export with metadata"""
    data = [{"name": "Item 1", "value": 100}]
    metadata = {"source": "test", "version": "1.0"}

    json_str = await export_service.export_to_json(data, metadata=metadata)
    json_data = json.loads(json_str)

    assert "metadata" in json_data
    assert json_data["metadata"]["source"] == "test"


@pytest.mark.asyncio
async def test_export_to_excel():
    """Test Excel export"""
    data = [
        {"name": "Item 1", "value": 100, "category": "A"},
        {"name": "Item 2", "value": 200, "category": "B"}
    ]

    excel_buffer = await export_service.export_to_excel(
        data=data,
        sheet_name="Test Data"
    )

    assert excel_buffer.tell() > 0  # Buffer has content
    excel_buffer.seek(0)  # Reset to beginning


@pytest.mark.asyncio
async def test_export_to_excel_empty():
    """Test Excel export with empty data"""
    excel_buffer = await export_service.export_to_excel(
        data=[],
        sheet_name="Empty"
    )

    assert excel_buffer.tell() > 0  # Buffer should still have content (empty file)


@pytest.mark.asyncio
async def test_export_timeseries_to_csv():
    """Test time series CSV export"""
    data = [
        {"timestamp": "2024-01-01T00:00:00Z", "tag_id": "tag1", "value": 10},
        {"timestamp": "2024-01-01T00:01:00Z", "tag_id": "tag1", "value": 20},
        {"timestamp": "2024-01-01T00:00:00Z", "tag_id": "tag2", "value": 30}
    ]

    csv_buffer = await export_service.export_timeseries_to_csv(data)
    csv_content = csv_buffer.getvalue()

    assert "timestamp" in csv_content
    assert "value" in csv_content


@pytest.mark.asyncio
async def test_export_with_template():
    """Test Excel export with custom template"""
    data = [
        {"name": "Item 1", "value": 100},
        {"name": "Item 2", "value": 200}
    ]

    template_config = {
        "sheet_name": "Report",
        "title": "Monthly Report",
        "columns": ["name", "value"]
    }

    excel_buffer = await export_service.export_with_template(
        data=data,
        template_config=template_config
    )

    assert excel_buffer.tell() > 0
