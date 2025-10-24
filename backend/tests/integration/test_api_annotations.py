"""
Integration tests for Annotations API
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime


def test_create_annotation(test_client: TestClient, sample_annotation_data):
    """Test creating an annotation"""
    response = test_client.post("/api/v1/annotations/", json=sample_annotation_data)

    assert response.status_code == 200
    data = response.json()

    assert data["title"] == sample_annotation_data["title"]
    assert data["type"] == sample_annotation_data["type"]
    assert "id" in data


def test_get_annotation(test_client: TestClient, sample_annotation_data):
    """Test getting an annotation by ID"""
    # Create annotation
    create_response = test_client.post("/api/v1/annotations/", json=sample_annotation_data)
    annotation_id = create_response.json()["id"]

    # Get annotation
    response = test_client.get(f"/api/v1/annotations/{annotation_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == annotation_id
    assert data["title"] == sample_annotation_data["title"]


def test_list_annotations(test_client: TestClient, sample_annotation_data):
    """Test listing annotations"""
    # Create multiple annotations
    for i in range(3):
        annotation_data = sample_annotation_data.copy()
        annotation_data["title"] = f"Test Annotation {i}"
        test_client.post("/api/v1/annotations/", json=annotation_data)

    # List annotations
    response = test_client.get("/api/v1/annotations/")

    assert response.status_code == 200
    data = response.json()

    assert "annotations" in data
    assert "total" in data
    assert data["total"] >= 3


def test_list_annotations_with_filters(test_client: TestClient, sample_annotation_data):
    """Test listing annotations with filters"""
    # Create annotations with different types
    annotation_data1 = sample_annotation_data.copy()
    annotation_data1["type"] = "comment"
    test_client.post("/api/v1/annotations/", json=annotation_data1)

    annotation_data2 = sample_annotation_data.copy()
    annotation_data2["type"] = "event"
    test_client.post("/api/v1/annotations/", json=annotation_data2)

    # Filter by type
    response = test_client.get("/api/v1/annotations/?type=comment")

    assert response.status_code == 200
    data = response.json()

    assert all(a["type"] == "comment" for a in data["annotations"])


def test_update_annotation(test_client: TestClient, sample_annotation_data):
    """Test updating an annotation"""
    # Create annotation
    create_response = test_client.post("/api/v1/annotations/", json=sample_annotation_data)
    annotation_id = create_response.json()["id"]

    # Update annotation
    update_data = {
        "title": "Updated Title",
        "priority": "high"
    }

    response = test_client.put(f"/api/v1/annotations/{annotation_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["priority"] == "high"


def test_delete_annotation(test_client: TestClient, sample_annotation_data):
    """Test deleting an annotation"""
    # Create annotation
    create_response = test_client.post("/api/v1/annotations/", json=sample_annotation_data)
    annotation_id = create_response.json()["id"]

    # Delete annotation
    response = test_client.delete(f"/api/v1/annotations/{annotation_id}")

    assert response.status_code == 200

    # Verify deletion
    get_response = test_client.get(f"/api/v1/annotations/{annotation_id}")
    assert get_response.status_code == 404


def test_add_comment_to_annotation(test_client: TestClient, sample_annotation_data):
    """Test adding a comment to an annotation"""
    # Create annotation
    create_response = test_client.post("/api/v1/annotations/", json=sample_annotation_data)
    annotation_id = create_response.json()["id"]

    # Add comment
    comment_data = {
        "comment": "This is a test comment"
    }

    response = test_client.post(
        f"/api/v1/annotations/{annotation_id}/comments",
        json=comment_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["comment"] == "This is a test comment"
    assert data["annotation_id"] == annotation_id


def test_list_comments(test_client: TestClient, sample_annotation_data):
    """Test listing comments for an annotation"""
    # Create annotation
    create_response = test_client.post("/api/v1/annotations/", json=sample_annotation_data)
    annotation_id = create_response.json()["id"]

    # Add multiple comments
    for i in range(3):
        comment_data = {"comment": f"Comment {i}"}
        test_client.post(
            f"/api/v1/annotations/{annotation_id}/comments",
            json=comment_data
        )

    # List comments
    response = test_client.get(f"/api/v1/annotations/{annotation_id}/comments")

    assert response.status_code == 200
    comments = response.json()
    assert len(comments) == 3


def test_threaded_comments(test_client: TestClient, sample_annotation_data):
    """Test threaded replies to comments"""
    # Create annotation
    create_response = test_client.post("/api/v1/annotations/", json=sample_annotation_data)
    annotation_id = create_response.json()["id"]

    # Add parent comment
    parent_comment = test_client.post(
        f"/api/v1/annotations/{annotation_id}/comments",
        json={"comment": "Parent comment"}
    ).json()

    # Add reply
    reply_data = {
        "comment": "Reply to parent",
        "parent_comment_id": parent_comment["id"]
    }

    response = test_client.post(
        f"/api/v1/annotations/{annotation_id}/comments",
        json=reply_data
    )

    assert response.status_code == 200

    # List comments and verify threading
    comments_response = test_client.get(f"/api/v1/annotations/{annotation_id}/comments")
    comments = comments_response.json()

    # Find parent comment
    parent = next(c for c in comments if c["id"] == parent_comment["id"])
    assert len(parent["replies"]) == 1
    assert parent["replies"][0]["comment"] == "Reply to parent"
