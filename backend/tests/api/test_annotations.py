"""
Tests for Annotation API Endpoints

Tests annotation CRUD operations, filtering, search, and statistics.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.annotation import Annotation, AnnotationType, AnnotationSeverity


class TestAnnotationModel:
    """Test Annotation model"""

    def test_annotation_creation(self, db_session):
        """Test creating an annotation"""
        annotation = Annotation(
            annotation_type=AnnotationType.EVENT,
            severity=AnnotationSeverity.WARNING,
            title="Test Event",
            content="Test content",
            start_time=datetime.utcnow(),
            created_by="test_user",
            created_by_name="Test User"
        )

        db_session.add(annotation)
        db_session.commit()

        assert annotation.id is not None
        assert annotation.annotation_type == AnnotationType.EVENT
        assert annotation.severity == AnnotationSeverity.WARNING
        assert annotation.title == "Test Event"

    def test_annotation_to_dict(self, db_session):
        """Test converting annotation to dictionary"""
        annotation = Annotation(
            annotation_type=AnnotationType.COMMENT,
            severity=AnnotationSeverity.INFO,
            title="Test Comment",
            start_time=datetime.utcnow(),
            created_by="test_user"
        )

        result = annotation.to_dict()

        assert "id" in result
        assert result["annotation_type"] == "comment"
        assert result["severity"] == "info"
        assert result["title"] == "Test Comment"

    def test_annotation_duration(self, db_session):
        """Test annotation duration calculation"""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)

        annotation = Annotation(
            annotation_type=AnnotationType.MAINTENANCE,
            severity=AnnotationSeverity.INFO,
            title="Maintenance",
            start_time=start_time,
            end_time=end_time,
            created_by="test_user"
        )

        assert annotation.duration_seconds == 7200  # 2 hours
        assert annotation.is_range is True

    def test_annotation_point_annotation(self, db_session):
        """Test point annotation (no end time)"""
        annotation = Annotation(
            annotation_type=AnnotationType.EVENT,
            severity=AnnotationSeverity.ERROR,
            title="Event",
            start_time=datetime.utcnow(),
            created_by="test_user"
        )

        assert annotation.duration_seconds == 0
        assert annotation.is_range is False


class TestAnnotationCRUD:
    """Test annotation CRUD operations"""

    @pytest.mark.asyncio
    async def test_create_annotation(self, client, sample_tag):
        """Test creating an annotation via API"""
        data = {
            "annotation_type": "event",
            "severity": "warning",
            "title": "Test Event",
            "content": "Test content",
            "start_time": datetime.utcnow().isoformat(),
            "tag_id": str(sample_tag.id),
            "created_by": "test_user",
            "created_by_name": "Test User"
        }

        response = client.post("/api/v1/annotations/", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["title"] == "Test Event"
        assert result["annotation_type"] == "event"

    @pytest.mark.asyncio
    async def test_create_annotation_without_tag(self, client):
        """Test creating annotation without tag association"""
        data = {
            "annotation_type": "comment",
            "severity": "info",
            "title": "General Comment",
            "start_time": datetime.utcnow().isoformat(),
            "created_by": "test_user"
        }

        response = client.post("/api/v1/annotations/", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["tag_id"] is None

    @pytest.mark.asyncio
    async def test_create_range_annotation(self, client, sample_tag):
        """Test creating range annotation"""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=1)

        data = {
            "annotation_type": "maintenance",
            "severity": "info",
            "title": "Scheduled Maintenance",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "tag_id": str(sample_tag.id),
            "created_by": "test_user"
        }

        response = client.post("/api/v1/annotations/", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["is_range"] is True
        assert result["duration_seconds"] == 3600

    @pytest.mark.asyncio
    async def test_get_annotation(self, client, sample_annotation):
        """Test getting annotation by ID"""
        response = client.get(f"/api/v1/annotations/{sample_annotation.id}")

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == str(sample_annotation.id)
        assert result["title"] == sample_annotation.title

    @pytest.mark.asyncio
    async def test_list_annotations(self, client, sample_annotations):
        """Test listing annotations with pagination"""
        response = client.get("/api/v1/annotations/?page=1&page_size=10")

        assert response.status_code == 200
        result = response.json()
        assert "total" in result
        assert "annotations" in result
        assert len(result["annotations"]) > 0

    @pytest.mark.asyncio
    async def test_update_annotation(self, client, sample_annotation):
        """Test updating annotation"""
        data = {
            "title": "Updated Title",
            "severity": "error"
        }

        response = client.put(
            f"/api/v1/annotations/{sample_annotation.id}",
            json=data
        )

        assert response.status_code == 200
        result = response.json()
        assert result["title"] == "Updated Title"
        assert result["severity"] == "error"

    @pytest.mark.asyncio
    async def test_toggle_pin_annotation(self, client, sample_annotation):
        """Test toggling pin status"""
        original_pinned = sample_annotation.pinned

        response = client.patch(
            f"/api/v1/annotations/{sample_annotation.id}/pin"
        )

        assert response.status_code == 200
        result = response.json()
        assert result["pinned"] != original_pinned

    @pytest.mark.asyncio
    async def test_delete_annotation_soft(self, client, sample_annotation):
        """Test soft deleting annotation"""
        response = client.delete(
            f"/api/v1/annotations/{sample_annotation.id}?soft_delete=true"
        )

        assert response.status_code == 204

        # Verify it's marked as deleted
        get_response = client.get(f"/api/v1/annotations/{sample_annotation.id}")
        result = get_response.json()
        assert result["is_deleted"] is True

    @pytest.mark.asyncio
    async def test_restore_annotation(self, client, db_session):
        """Test restoring soft-deleted annotation"""
        # Create and delete annotation
        annotation = Annotation(
            annotation_type=AnnotationType.COMMENT,
            severity=AnnotationSeverity.INFO,
            title="To be deleted",
            start_time=datetime.utcnow(),
            created_by="test_user",
            is_deleted=True
        )
        db_session.add(annotation)
        db_session.commit()

        # Restore it
        response = client.post(f"/api/v1/annotations/{annotation.id}/restore")

        assert response.status_code == 200
        result = response.json()
        assert result["is_deleted"] is False


class TestAnnotationFiltering:
    """Test annotation filtering and search"""

    @pytest.mark.asyncio
    async def test_filter_by_tag(self, client, sample_tag, sample_annotations):
        """Test filtering annotations by tag"""
        response = client.get(
            f"/api/v1/annotations/tag/{sample_tag.id}"
        )

        assert response.status_code == 200
        result = response.json()
        assert all(a["tag_id"] == str(sample_tag.id) for a in result["annotations"])

    @pytest.mark.asyncio
    async def test_filter_by_type(self, client, sample_annotations):
        """Test filtering by annotation type"""
        response = client.get(
            "/api/v1/annotations/?annotation_types=event&annotation_types=alarm"
        )

        assert response.status_code == 200
        result = response.json()
        assert all(
            a["annotation_type"] in ["event", "alarm"]
            for a in result["annotations"]
        )

    @pytest.mark.asyncio
    async def test_filter_by_severity(self, client, sample_annotations):
        """Test filtering by severity"""
        response = client.get(
            "/api/v1/annotations/?severities=warning&severities=error"
        )

        assert response.status_code == 200
        result = response.json()
        assert all(
            a["severity"] in ["warning", "error"]
            for a in result["annotations"]
        )

    @pytest.mark.asyncio
    async def test_filter_by_time_range(self, client, sample_annotations):
        """Test filtering by time range"""
        start_time = datetime.utcnow() - timedelta(days=1)
        end_time = datetime.utcnow()

        response = client.get(
            f"/api/v1/annotations/?start_time={start_time.isoformat()}&end_time={end_time.isoformat()}"
        )

        assert response.status_code == 200
        result = response.json()
        assert "annotations" in result

    @pytest.mark.asyncio
    async def test_filter_pinned_only(self, client, db_session):
        """Test filtering pinned annotations only"""
        # Create pinned annotation
        annotation = Annotation(
            annotation_type=AnnotationType.BOOKMARK,
            severity=AnnotationSeverity.INFO,
            title="Pinned",
            start_time=datetime.utcnow(),
            created_by="test_user",
            pinned=True
        )
        db_session.add(annotation)
        db_session.commit()

        response = client.get("/api/v1/annotations/?pinned_only=true")

        assert response.status_code == 200
        result = response.json()
        assert all(a["pinned"] for a in result["annotations"])

    @pytest.mark.asyncio
    async def test_search_annotations(self, client, sample_annotations):
        """Test searching annotations"""
        response = client.get("/api/v1/annotations/?search=test")

        assert response.status_code == 200
        result = response.json()
        assert "annotations" in result


class TestAnnotationStatistics:
    """Test annotation statistics"""

    @pytest.mark.asyncio
    async def test_get_statistics(self, client, sample_annotations):
        """Test getting annotation statistics"""
        response = client.get("/api/v1/annotations/statistics/summary")

        assert response.status_code == 200
        result = response.json()
        assert "total_annotations" in result
        assert "by_type" in result
        assert "by_severity" in result
        assert "recent_count_24h" in result
        assert "pinned_count" in result

    @pytest.mark.asyncio
    async def test_get_statistics_by_tag(self, client, sample_tag, sample_annotations):
        """Test getting statistics filtered by tag"""
        response = client.get(
            f"/api/v1/annotations/statistics/summary?tag_id={sample_tag.id}"
        )

        assert response.status_code == 200
        result = response.json()
        assert "total_annotations" in result


class TestAnnotationBulkOperations:
    """Test bulk operations"""

    @pytest.mark.asyncio
    async def test_bulk_create_annotations(self, client, sample_tag):
        """Test creating multiple annotations in bulk"""
        annotations = [
            {
                "annotation_type": "comment",
                "severity": "info",
                "title": f"Comment {i}",
                "start_time": datetime.utcnow().isoformat(),
                "tag_id": str(sample_tag.id),
                "created_by": "test_user"
            }
            for i in range(5)
        ]

        data = {"annotations": annotations}

        response = client.post("/api/v1/annotations/bulk", json=data)

        assert response.status_code == 201
        result = response.json()
        assert len(result) == 5


class TestAnnotationValidation:
    """Test annotation validation"""

    @pytest.mark.asyncio
    async def test_invalid_time_range(self, client):
        """Test creating annotation with invalid time range"""
        start_time = datetime.utcnow()
        end_time = start_time - timedelta(hours=1)  # End before start

        data = {
            "annotation_type": "event",
            "severity": "info",
            "title": "Invalid",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "created_by": "test_user"
        }

        response = client.post("/api/v1/annotations/", json=data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_invalid_color(self, client):
        """Test creating annotation with invalid color"""
        data = {
            "annotation_type": "event",
            "severity": "info",
            "title": "Test",
            "start_time": datetime.utcnow().isoformat(),
            "created_by": "test_user",
            "color": "invalid"  # Not a hex color
        }

        response = client.post("/api/v1/annotations/", json=data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client):
        """Test creating annotation without required fields"""
        data = {
            "annotation_type": "event"
            # Missing title, start_time, created_by
        }

        response = client.post("/api/v1/annotations/", json=data)

        assert response.status_code == 422  # Validation error


# ==================== Fixtures ====================

@pytest.fixture
def sample_annotation(db_session, sample_tag):
    """Create a sample annotation"""
    annotation = Annotation(
        annotation_type=AnnotationType.EVENT,
        severity=AnnotationSeverity.WARNING,
        title="Sample Event",
        content="Sample content",
        start_time=datetime.utcnow(),
        tag_id=sample_tag.id,
        created_by="test_user",
        created_by_name="Test User"
    )
    db_session.add(annotation)
    db_session.commit()
    return annotation


@pytest.fixture
def sample_annotations(db_session, sample_tag):
    """Create multiple sample annotations"""
    annotations = []
    for i in range(10):
        annotation = Annotation(
            annotation_type=AnnotationType.COMMENT if i % 2 == 0 else AnnotationType.EVENT,
            severity=AnnotationSeverity.INFO if i % 2 == 0 else AnnotationSeverity.WARNING,
            title=f"Annotation {i}",
            start_time=datetime.utcnow() - timedelta(hours=i),
            tag_id=sample_tag.id if i % 2 == 0 else None,
            created_by="test_user"
        )
        annotations.append(annotation)
        db_session.add(annotation)

    db_session.commit()
    return annotations
