"""
Data Ingestion API Routes - Receive data from external sources

This module provides endpoints for:
- Node-RED data ingestion
- External SCADA systems
- Third-party sensors
- Industrial protocol converters

Security: API Key authentication required
"""

from fastapi import APIRouter, HTTPException, Header, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import time

from app.core.logger import logger

router = APIRouter()


# === MODELS ===

class DataPoint(BaseModel):
    """Single data point from external source"""
    tag_name: str
    value: Any
    timestamp: Optional[str] = None
    quality: Optional[str] = "Good"
    source: Optional[str] = None
    unit: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BatchIngestRequest(BaseModel):
    """Batch of data points to ingest"""
    data: List[DataPoint]
    source_id: Optional[str] = None
    source_type: Optional[str] = None  # nodered, scada, mqtt, etc.


class IngestResponse(BaseModel):
    """Response for data ingestion"""
    success: bool
    received: int
    processed: int
    errors: int
    latency_ms: float
    message: str


# === API KEY VALIDATION ===

# Simple API key for Node-RED integration
# In production, use a proper secrets management system
VALID_API_KEYS = {
    "nodered-optiflow-2024": "Node-RED Integration",
    "scada-optiflow-2024": "SCADA Integration",
    "external-optiflow-2024": "External Systems"
}


def validate_api_key(x_api_key: Optional[str] = Header(None)):
    """Validate API key from request header"""
    if not x_api_key:
        raise HTTPException(401, "Missing X-API-Key header")

    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(403, "Invalid API key")

    return VALID_API_KEYS[x_api_key]


# === INTERNAL DATA BUFFER ===

# Simple in-memory buffer for received data
# This data can be read by adapters or forwarded to Kafka
_data_buffer: Dict[str, Dict[str, Any]] = {}
_stats = {
    "total_received": 0,
    "total_processed": 0,
    "total_errors": 0,
    "last_ingest_time": None,
    "sources": {}
}


def get_data_buffer():
    """Get current data buffer (for other modules)"""
    return _data_buffer


def get_ingest_stats():
    """Get ingestion statistics"""
    return _stats


# === ENDPOINTS ===

@router.post("/ingest", response_model=IngestResponse)
async def ingest_data(
    request: BatchIngestRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Ingest data from external sources (Node-RED, SCADA, etc.)

    **Authentication**: Requires X-API-Key header

    **Request Body**:
    ```json
    {
      "data": [
        {
          "tag_name": "S7_Temperatura_Silo1",
          "value": 45.2,
          "timestamp": "2025-01-19T10:30:45.123Z",
          "quality": "Good",
          "source": "siemens-plc-001"
        }
      ],
      "source_id": "nodered-001",
      "source_type": "nodered"
    }
    ```

    **Response**:
    ```json
    {
      "success": true,
      "received": 5,
      "processed": 5,
      "errors": 0,
      "latency_ms": 2.5,
      "message": "Data ingested successfully"
    }
    ```
    """
    start_time = time.time()

    # Validate API key
    source_name = validate_api_key(x_api_key)

    received = len(request.data)
    processed = 0
    errors = 0

    logger.info(f"📥 Data ingest: {received} points from {source_name} ({request.source_type or 'unknown'})")

    for point in request.data:
        try:
            # Set timestamp if not provided
            if not point.timestamp:
                point.timestamp = datetime.utcnow().isoformat() + "Z"

            # Store in buffer
            _data_buffer[point.tag_name] = {
                "value": point.value,
                "timestamp": point.timestamp,
                "quality": point.quality or "Good",
                "source": point.source or request.source_id,
                "source_type": request.source_type,
                "unit": point.unit,
                "metadata": point.metadata,
                "received_at": datetime.utcnow().isoformat()
            }

            processed += 1

            # Log sample data (first 3 points)
            if processed <= 3:
                logger.debug(f"  📊 {point.tag_name}: {point.value} ({point.quality})")

        except Exception as e:
            errors += 1
            logger.error(f"  ❌ Error processing {point.tag_name}: {e}")

    # Update stats
    _stats["total_received"] += received
    _stats["total_processed"] += processed
    _stats["total_errors"] += errors
    _stats["last_ingest_time"] = datetime.utcnow().isoformat()

    source_key = request.source_id or request.source_type or "unknown"
    if source_key not in _stats["sources"]:
        _stats["sources"][source_key] = {"count": 0, "last_seen": None}
    _stats["sources"][source_key]["count"] += processed
    _stats["sources"][source_key]["last_seen"] = _stats["last_ingest_time"]

    # Try to forward to Kafka if available
    try:
        from app.services.kafka_producer import get_kafka_producer
        kafka_producer = get_kafka_producer()

        # Start the producer if not yet started
        if kafka_producer and not kafka_producer._started:
            logger.info("  🚀 Starting Kafka producer for external data...")
            await kafka_producer.start()

        if kafka_producer and kafka_producer._started:
            # Convert to Kafka format
            kafka_data = []
            for point in request.data:
                kafka_data.append({
                    "tag_name": point.tag_name,
                    "value": point.value,
                    "timestamp": point.timestamp,
                    "quality": point.quality or "good",
                    "source": f"external:{request.source_type or 'unknown'}",
                    "source_id": request.source_id or "unknown"
                })

            count = await kafka_producer.publish_bulk(kafka_data, validate_quality=True)
            if count > 0:
                logger.info(f"  ✅ Forwarded {count} points to Kafka")
            else:
                logger.warning(f"  ⚠️ Failed to forward data to Kafka")
    except Exception as e:
        logger.debug(f"  ℹ️ Kafka forwarding not available: {e}")

    latency_ms = (time.time() - start_time) * 1000

    return IngestResponse(
        success=errors == 0,
        received=received,
        processed=processed,
        errors=errors,
        latency_ms=round(latency_ms, 2),
        message=f"Data ingested from {source_name}" if errors == 0 else f"Ingested with {errors} errors"
    )


@router.post("/ingest/single")
async def ingest_single_point(
    tag_name: str,
    value: Any,
    quality: str = "Good",
    source: Optional[str] = None,
    x_api_key: Optional[str] = Header(None)
):
    """
    Ingest a single data point (simpler endpoint for basic integrations)

    **Query Parameters**:
    - tag_name: Name of the tag
    - value: Current value
    - quality: Data quality (default: Good)
    - source: Source identifier (optional)
    """
    # Validate API key
    source_name = validate_api_key(x_api_key)

    timestamp = datetime.utcnow().isoformat() + "Z"

    _data_buffer[tag_name] = {
        "value": value,
        "timestamp": timestamp,
        "quality": quality,
        "source": source or source_name,
        "received_at": timestamp
    }

    _stats["total_received"] += 1
    _stats["total_processed"] += 1
    _stats["last_ingest_time"] = timestamp

    return {
        "success": True,
        "tag_name": tag_name,
        "value": value,
        "timestamp": timestamp
    }


@router.get("/ingest/buffer")
async def get_buffer_status(
    x_api_key: Optional[str] = Header(None)
):
    """
    Get current data buffer status

    Returns all data currently in the ingestion buffer
    """
    # Validate API key
    validate_api_key(x_api_key)

    return {
        "count": len(_data_buffer),
        "data": _data_buffer,
        "stats": _stats
    }


@router.get("/ingest/stats")
async def get_ingestion_stats():
    """
    Get ingestion statistics (no auth required for monitoring)
    """
    return {
        "total_received": _stats["total_received"],
        "total_processed": _stats["total_processed"],
        "total_errors": _stats["total_errors"],
        "buffer_size": len(_data_buffer),
        "last_ingest_time": _stats["last_ingest_time"],
        "sources": _stats["sources"]
    }


@router.delete("/ingest/buffer")
async def clear_buffer(
    x_api_key: Optional[str] = Header(None)
):
    """
    Clear the data buffer
    """
    # Validate API key
    validate_api_key(x_api_key)

    _data_buffer.clear()

    return {
        "success": True,
        "message": "Buffer cleared"
    }


@router.get("/ingest/tag/{tag_name}")
async def get_tag_from_buffer(
    tag_name: str,
    x_api_key: Optional[str] = Header(None)
):
    """
    Get a specific tag value from the buffer
    """
    # Validate API key
    validate_api_key(x_api_key)

    if tag_name not in _data_buffer:
        raise HTTPException(404, f"Tag '{tag_name}' not found in buffer")

    return {
        "tag_name": tag_name,
        **_data_buffer[tag_name]
    }
