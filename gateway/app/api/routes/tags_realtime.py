"""
Tags API Routes - Low-latency local access to tag data

Provides REST API endpoints for:
- Real-time tag values (< 50ms latency)
- Batch reading (multiple tags in parallel)
- Tag listing and search
- Historical data (if local buffer available)

This API is designed for:
- Local dashboards in the plant
- HMI systems
- Troubleshooting tools
- Edge applications

Latency targets:
- Cache hit (L1 memory): ~2-5ms
- PLC read (cache miss): ~20-50ms
- Much faster than cloud backend (~500ms)
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import time

from app.core.logger import logger

router = APIRouter()


# === DEPENDENCY INJECTION ===

def get_protocol_manager():
    """
    Get protocol manager from global state

    This is a dependency that will be injected into route handlers
    """
    from app.main_kafka import protocol_manager
    if protocol_manager is None:
        raise HTTPException(503, "Protocol manager not initialized")
    return protocol_manager


# === TAG ENDPOINTS ===

# IMPORTANT: Static routes must be defined BEFORE parameterized routes
# to avoid the {tag_name} pattern capturing "all", "batch", etc.

@router.get("/realtime/all")
async def get_all_realtime_values(
    adapter_id: Optional[str] = Query(None, description="Filter by adapter ID"),
    pm=Depends(get_protocol_manager)
):
    """
    Get ALL real-time tag values from cache

    This is the main endpoint for UI dashboards - returns all cached values
    from subscription-based adapters.

    **Query Parameters**:
    - `adapter_id`: Filter by specific adapter (optional)

    **Returns**:
    ```json
    {
      "count": 78,
      "adapters": 2,
      "tags": {
        "temp_c": {"value": 45.2, "quality": "Good", "timestamp": "...", "adapter_id": "opcua-001"},
        "power_kw": {"value": 12.5, "quality": "Good", ...}
      },
      "latency_ms": 1.2
    }
    ```
    """
    start_time = time.time()

    all_values = {}
    adapter_count = 0

    for adp in pm.adapters.values():
        # Apply adapter filter if specified
        if adapter_id and adp.adapter_id != adapter_id:
            continue

        if not adp.connected:
            continue

        adapter_count += 1

        # Get values from last_values cache
        if hasattr(adp, 'last_values') and adp.last_values:
            # Build a reverse map: address -> tag_name
            address_to_name = {}
            for tag in adp.config.tags:
                addr = tag.get('address')
                if addr:
                    address_to_name[addr] = tag.get('name', addr)

            for address, cached_value in adp.last_values.items():
                tag_name = address_to_name.get(address, address)
                all_values[tag_name] = {
                    "value": cached_value.get('value'),
                    "quality": cached_value.get('quality', 'Good'),
                    "timestamp": cached_value.get('timestamp'),
                    "address": address,
                    "adapter_id": adp.adapter_id,
                    "protocol": adp.config.protocol_type
                }

    latency_ms = (time.time() - start_time) * 1000

    return {
        "count": len(all_values),
        "adapters": adapter_count,
        "tags": all_values,
        "latency_ms": round(latency_ms, 2)
    }


@router.get("/realtime/discovered/{adapter_id}")
async def get_discovered_tags_realtime(
    adapter_id: str,
    pm=Depends(get_protocol_manager)
):
    """
    Get ALL discovered tags from an adapter with real-time values

    This endpoint discovers tags and reads their current values DIRECTLY
    from the PLC/OPC-UA server (not from subscription cache).
    Used by the Gateway UI to show all available tags.

    **Returns**:
    ```json
    {
      "adapter_id": "opcua-simulator-001",
      "count": 53,
      "connected": true,
      "tags": [
        {
          "name": "temp_c",
          "address": "ns=2;i=12",
          "current_value": 45.2,
          "quality": "good",
          "data_type": "double",
          "unit": null,
          "last_update": "2025-01-19T10:30:45.123Z"
        }
      ],
      "latency_ms": 125.4
    }
    ```
    """
    start_time = time.time()

    # Find the adapter
    adapter = pm.adapters.get(adapter_id)
    if not adapter:
        raise HTTPException(404, f"Adapter '{adapter_id}' not found")

    # Check if adapter is connected
    if not adapter.connected:
        return {
            "adapter_id": adapter_id,
            "count": 0,
            "connected": False,
            "tags": [],
            "message": "Adapter not connected",
            "latency_ms": round((time.time() - start_time) * 1000, 2)
        }

    tags_with_values = []

    try:
        # Trigger discovery if adapter supports it (to populate config.tags)
        if hasattr(adapter, '_discover_tags'):
            await adapter._discover_tags()

        # Use the new direct read method if available (OPC-UA adapter)
        if hasattr(adapter, 'read_all_discovered_tags'):
            logger.info(f"📖 Using direct read for adapter {adapter_id}")
            tags_with_values = await adapter.read_all_discovered_tags()
        else:
            # Fallback: use cached values from subscriptions
            logger.info(f"📋 Using cached values for adapter {adapter_id}")
            discovered_tags = adapter.config.tags if hasattr(adapter.config, 'tags') else []
            last_values = getattr(adapter, 'last_values', {})

            for tag in discovered_tags:
                tag_addr = tag.get('address', '')
                cached = last_values.get(tag_addr, {})

                tags_with_values.append({
                    "name": tag.get('name') or tag.get('tag_name', tag_addr),
                    "address": tag_addr,
                    "current_value": cached.get('value'),
                    "quality": cached.get('quality', 'unknown'),
                    "data_type": tag.get('type', tag.get('data_type', 'unknown')),
                    "unit": tag.get('unit'),
                    "last_update": cached.get('timestamp'),
                    "connected": cached.get('value') is not None
                })

    except Exception as e:
        logger.error(f"Error getting discovered tags for {adapter_id}: {e}", exc_info=True)
        # Return empty but don't fail

    latency_ms = (time.time() - start_time) * 1000

    return {
        "adapter_id": adapter_id,
        "count": len(tags_with_values),
        "connected": adapter.connected,
        "tags": tags_with_values,
        "latency_ms": round(latency_ms, 2)
    }


@router.get("/realtime/{tag_name}")
async def get_realtime_tag(
    tag_name: str,
    pm=Depends(get_protocol_manager)
):
    """
    Get real-time value of a single tag

    **Performance**:
    - Cache hit: ~2-5ms
    - PLC read: ~20-50ms

    **Returns**:
    ```json
    {
      "tag_name": "SILO1_TEMPERATURA",
      "value": 45.2,
      "quality": "good",
      "timestamp": "2025-01-19T10:30:45.123Z",
      "unit": "°C",
      "source": "cache",  // or "plc"
      "latency_ms": 3.2
    }
    ```

    **Errors**:
    - 404: Tag not found
    - 503: Gateway not ready
    """
    start_time = time.time()

    try:
        # Find which adapter has this tag
        adapter = None
        tag_config = None

        for adp in pm.adapters.values():
            for tag in adp.config.tags:
                if tag.get('name') == tag_name:
                    adapter = adp
                    tag_config = tag
                    break
            if adapter:
                break

        if not adapter:
            raise HTTPException(404, f"Tag '{tag_name}' not found in any adapter")

        # Check if adapter is connected
        if not adapter.connected:
            raise HTTPException(
                503,
                f"Adapter for tag '{tag_name}' is not connected to PLC"
            )

        # Read tag value from adapter's cache
        # For OPC UA with subscriptions, this gets the last received value
        # For other protocols, this triggers a read
        tag_data = None

        # Try to get from adapter's last_values cache (OPC UA subscription)
        if hasattr(adapter, 'last_values') and tag_config.get('address') in adapter.last_values:
            cached_value = adapter.last_values[tag_config.get('address')]
            tag_data = type('TagData', (), {
                'tag_name': tag_name,
                'value': cached_value.get('value'),
                'quality': cached_value.get('quality', 'Good'),
                'timestamp': cached_value.get('timestamp'),
                'address': tag_config.get('address')
            })()
        else:
            # Fallback: read directly from adapter
            tags_data = await adapter.read_tags()
            for td in tags_data:
                if td.tag_name == tag_name or td.address == tag_config.get('address'):
                    tag_data = td
                    break

        if not tag_data or tag_data.value is None:
            raise HTTPException(404, f"Tag '{tag_name}' returned no data")

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000

        return {
            "tag_name": tag_data.tag_name,
            "value": tag_data.value,
            "quality": tag_data.quality,
            "timestamp": tag_data.timestamp,
            "unit": tag_config.get('unit'),
            "address": tag_data.address,
            "source": "plc",  # TODO: indicate "cache" when caching is implemented
            "latency_ms": round(latency_ms, 2),
            "adapter_id": adapter.adapter_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading tag {tag_name}: {e}", exc_info=True)
        raise HTTPException(500, f"Internal error reading tag: {str(e)}")


@router.post("/realtime/batch")
async def get_realtime_batch(
    tag_names: List[str],
    pm=Depends(get_protocol_manager)
):
    """
    Get real-time values for multiple tags in parallel

    **Much more efficient than N individual requests!**

    **Request Body**:
    ```json
    {
      "tag_names": ["SILO1_TEMP", "SILO1_NIVEL", "SILO2_TEMP"]
    }
    ```

    **Returns**:
    ```json
    {
      "count": 3,
      "tags": [
        {"tag_name": "SILO1_TEMP", "value": 45.2, ...},
        {"tag_name": "SILO1_NIVEL", "value": 80.5, ...},
        {"tag_name": "SILO2_TEMP", "value": 42.1, ...}
      ],
      "latency_ms": 52.3
    }
    ```
    """
    start_time = time.time()

    try:
        results = []

        # Build a map of tag_name -> (adapter, tag_config)
        tag_to_adapter = {}
        for tag_name in tag_names:
            for adapter in pm.adapters.values():
                for tag in adapter.config.tags:
                    if tag.get('name') == tag_name:
                        tag_to_adapter[tag_name] = (adapter, tag)
                        break
                if tag_name in tag_to_adapter:
                    break

        # Get values from last_values cache (most reliable for subscription-based adapters)
        for tag_name, (adapter, tag_config) in tag_to_adapter.items():
            if not adapter.connected:
                continue

            address = tag_config.get('address')

            # Try last_values cache first (OPC UA subscriptions, etc.)
            if hasattr(adapter, 'last_values') and address in adapter.last_values:
                cached_value = adapter.last_values[address]
                results.append({
                    "tag_name": tag_name,
                    "value": cached_value.get('value'),
                    "quality": cached_value.get('quality', 'Good'),
                    "timestamp": cached_value.get('timestamp'),
                    "address": address,
                    "adapter_id": adapter.adapter_id
                })

        latency_ms = (time.time() - start_time) * 1000

        return {
            "count": len(results),
            "requested": len(tag_names),
            "tags": results,
            "latency_ms": round(latency_ms, 2)
        }

    except Exception as e:
        logger.error(f"Error reading batch tags: {e}", exc_info=True)
        raise HTTPException(500, f"Internal error: {str(e)}")


@router.get("/list")
async def list_tags(
    adapter_id: Optional[str] = Query(None, description="Filter by adapter ID"),
    protocol: Optional[str] = Query(None, description="Filter by protocol (opcua, modbus, mqtt)"),
    search: Optional[str] = Query(None, description="Search in tag names"),
    pm=Depends(get_protocol_manager)
):
    """
    List all configured tags

    **Query Parameters**:
    - `adapter_id`: Filter by specific adapter
    - `protocol`: Filter by protocol type (opcua, modbus, mqtt)
    - `search`: Search term for tag names (case-insensitive)

    **Returns**:
    ```json
    {
      "count": 150,
      "tags": [
        {
          "name": "SILO1_TEMPERATURA",
          "address": "ns=2;s=TEAG.SILO1.TEMP",
          "adapter_id": "plc1_opcua",
          "protocol": "opcua",
          "unit": "°C",
          "connected": true
        },
        ...
      ]
    }
    ```
    """
    all_tags = []

    for adapter in pm.adapters.values():
        # Apply adapter_id filter
        if adapter_id and adapter.adapter_id != adapter_id:
            continue

        # Apply protocol filter
        if protocol and adapter.config.protocol_type != protocol:
            continue

        for tag in adapter.config.tags:
            tag_name = tag.get('name', '')

            # Apply search filter
            if search and search.lower() not in tag_name.lower():
                continue

            all_tags.append({
                "name": tag_name,
                "address": tag.get('address'),
                "adapter_id": adapter.adapter_id,
                "protocol": adapter.config.protocol_type,
                "unit": tag.get('unit'),
                "data_type": tag.get('data_type') or tag.get('type') or 'variant',
                "connected": adapter.connected,
                "enabled": tag.get('enabled', True)
            })

    return {
        "count": len(all_tags),
        "tags": all_tags,
        "filters_applied": {
            "adapter_id": adapter_id,
            "protocol": protocol,
            "search": search
        }
    }


@router.get("/search/{search_term}")
async def search_tags(
    search_term: str,
    limit: int = Query(50, ge=1, le=500, description="Max results"),
    pm=Depends(get_protocol_manager)
):
    """
    Search tags by name (fuzzy match)

    **Example**: `/api/tags/search/temperatura?limit=10`

    Returns tags containing "temperatura" (case-insensitive)
    """
    results = []
    search_lower = search_term.lower()

    for adapter in pm.adapters.values():
        for tag in adapter.config.tags:
            tag_name = tag.get('name', '')

            if search_lower in tag_name.lower():
                results.append({
                    "name": tag_name,
                    "address": tag.get('address'),
                    "adapter_id": adapter.adapter_id,
                    "protocol": adapter.config.protocol_type,
                    "unit": tag.get('unit'),
                    "match_score": tag_name.lower().count(search_lower)  # Relevance
                })

                if len(results) >= limit:
                    break

        if len(results) >= limit:
            break

    # Sort by match score (most relevant first)
    results.sort(key=lambda x: x['match_score'], reverse=True)

    return {
        "search_term": search_term,
        "count": len(results),
        "limit": limit,
        "tags": results
    }


@router.get("/adapter/{adapter_id}/status")
async def get_adapter_status(
    adapter_id: str,
    pm=Depends(get_protocol_manager)
):
    """
    Get detailed status of a specific adapter

    **Useful for troubleshooting!**

    **Returns**:
    ```json
    {
      "adapter_id": "plc1_opcua",
      "protocol": "opcua",
      "connected": true,
      "endpoint": "opc.tcp://192.168.1.10:4840",
      "tags_configured": 150,
      "read_count": 5420,
      "error_count": 3,
      "last_read_time": "2025-01-19T10:30:45Z",
      "uptime_seconds": 3600
    }
    ```
    """
    adapter = pm.adapters.get(adapter_id)

    if not adapter:
        raise HTTPException(404, f"Adapter '{adapter_id}' not found")

    stats = adapter.get_statistics()

    return {
        "adapter_id": adapter_id,
        "protocol": adapter.config.protocol_type,
        "connected": adapter.connected,
        "running": adapter.running,
        "endpoint": f"{adapter.config.host}:{adapter.config.port}",
        "tags_configured": len(adapter.config.tags),
        "read_count": stats.get('read_count', 0),
        "error_count": stats.get('error_count', 0),
        "last_read_time": stats.get('last_read_time'),
        "scan_rate_ms": adapter.config.scan_rate_ms,
        "extra_config": adapter.config.extra_config
    }


@router.get("/managed")
async def list_managed_tags(
    adapter_id: Optional[str] = Query(None, description="Filter by adapter ID"),
    pm=Depends(get_protocol_manager)
):
    """
    List all MANAGED tags (tags saved/configured by user)

    These are tags that were explicitly saved via the Gateway UI,
    as opposed to discovered tags that are auto-detected but not yet saved.

    **Data Source**: tags_config.json

    **Query Parameters**:
    - `adapter_id`: Filter by specific adapter

    **Returns**:
    ```json
    {
      "count": 10,
      "source": "tags_config.json",
      "tags": [
        {
          "tag_id": "tag_abc123",
          "tag_name": "SILO1_TEMPERATURA",
          "address": "ns=2;s=TEAG.SILO1.TEMP",
          "adapter_id": "opcua-001",
          "data_type": "double",
          "enabled": true,
          "historian": {...},
          "scaling": {...},
          ...
        }
      ]
    }
    ```
    """
    import json
    from pathlib import Path

    # Load managed tags from config file
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "tags_config.json"

    managed_tags = []

    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                all_managed = config.get('tags', [])

                # Apply adapter filter
                for tag in all_managed:
                    if adapter_id and tag.get('adapter_id') != adapter_id:
                        continue
                    managed_tags.append(tag)
        else:
            logger.warning(f"Tags config file not found: {config_path}")

    except Exception as e:
        logger.error(f"Error loading managed tags: {e}")
        raise HTTPException(500, f"Error loading managed tags: {str(e)}")

    # Also get realtime values for managed tags
    for tag in managed_tags:
        tag_name = tag.get('tag_name')
        if tag_name:
            # Try to get current value from adapters
            for adapter in pm.adapters.values():
                if adapter.adapter_id != tag.get('adapter_id'):
                    continue

                address = tag.get('address')
                if hasattr(adapter, 'last_values') and address and address in adapter.last_values:
                    cached = adapter.last_values[address]
                    tag['current_value'] = cached.get('value')
                    tag['current_quality'] = cached.get('quality', 'Good')
                    tag['current_timestamp'] = cached.get('timestamp')
                    tag['connected'] = adapter.connected
                break

    return {
        "count": len(managed_tags),
        "source": "tags_config.json",
        "tags": managed_tags,
        "note": "These are user-saved tags. Use Gateway UI to add/remove tags."
    }


# === TAG CRUD OPERATIONS ===
# These endpoints manage tags_config.json (local Gateway configuration)

from pydantic import BaseModel
from typing import Optional as OptionalType
import uuid


class TagCreateRequest(BaseModel):
    """Request to create a new managed tag"""
    tag_name: str
    address: str
    data_type: str = "double"  # Will be auto-detected from PLC if available
    adapter_id: str
    enabled: bool = True
    read_only: bool = True
    metadata: Optional[Dict[str, Any]] = None
    historian: Optional[Dict[str, Any]] = None
    alarm: Optional[Dict[str, Any]] = None
    scaling: Optional[Dict[str, Any]] = None


class TagUpdateRequest(BaseModel):
    """Request to update a managed tag"""
    tag_name: OptionalType[str] = None
    enabled: OptionalType[bool] = None
    read_only: OptionalType[bool] = None
    metadata: OptionalType[Dict[str, Any]] = None
    historian: OptionalType[Dict[str, Any]] = None
    alarm: OptionalType[Any] = None  # Can be dict or null to remove
    scaling: OptionalType[Dict[str, Any]] = None
    deadband: OptionalType[float] = None
    remove_alarm: OptionalType[bool] = None  # Explicit flag to remove alarm


def _load_tags_config() -> Dict[str, Any]:
    """Load tags_config.json"""
    import json
    from pathlib import Path

    config_path = Path(__file__).parent.parent.parent.parent / "config" / "tags_config.json"

    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)

    # Return default structure
    return {
        "tags": [],
        "groups": [],
        "templates": [],
        "metadata": {
            "version": "1.0",
            "updated_at": datetime.now().isoformat()
        }
    }


def _save_tags_config(config: Dict[str, Any]):
    """Save tags_config.json"""
    import json
    from pathlib import Path

    config_path = Path(__file__).parent.parent.parent.parent / "config" / "tags_config.json"

    # Update metadata
    config["metadata"] = config.get("metadata", {})
    config["metadata"]["updated_at"] = datetime.now().isoformat()

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    logger.info(f"✅ Saved tags config to {config_path}")


@router.get("/export/csv")
async def export_tags_csv(
    pm=Depends(get_protocol_manager)
):
    """
    Export all managed tags as CSV
    """
    from fastapi.responses import Response

    config = _load_tags_config()
    tags = config.get("tags", [])

    # Build CSV
    csv_lines = ["tag_id,tag_name,address,data_type,adapter_id,enabled,engineering_units,description"]

    for tag in tags:
        csv_lines.append(",".join([
            tag.get("tag_id", ""),
            tag.get("tag_name", ""),
            tag.get("address", ""),
            tag.get("data_type", ""),
            tag.get("adapter_id", ""),
            str(tag.get("enabled", True)).lower(),
            tag.get("metadata", {}).get("engineering_units", ""),
            tag.get("metadata", {}).get("description", "").replace(",", ";")
        ]))

    csv_content = "\n".join(csv_lines)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tags_export.csv"}
    )


@router.get("/")
async def list_all_managed_tags(
    pm=Depends(get_protocol_manager)
):
    """
    List all managed tags (from tags_config.json)

    This endpoint returns an array of tags for UI compatibility.
    Use /managed for detailed response with metadata.
    """
    config = _load_tags_config()
    managed_tags = config.get("tags", [])

    # Enrich with realtime values
    for tag in managed_tags:
        adapter_id = tag.get("adapter_id")
        address = tag.get("address")

        for adapter in pm.adapters.values():
            if adapter.adapter_id == adapter_id:
                if hasattr(adapter, 'last_values') and address and address in adapter.last_values:
                    cached = adapter.last_values[address]
                    tag['current_value'] = cached.get('value')
                    tag['current_quality'] = cached.get('quality', 'Good')
                    tag['current_timestamp'] = cached.get('timestamp')
                    tag['connected'] = adapter.connected
                break

    return managed_tags


@router.post("/")
async def create_tag(
    request: TagCreateRequest,
    pm=Depends(get_protocol_manager)
):
    """
    Create a new managed tag

    The tag will be saved to tags_config.json and used by:
    - Alarm Evaluator (for alarm thresholds)
    - Historian (for data logging)
    - Gateway UI

    **Note**: data_type is auto-detected from PLC when possible
    """
    config = _load_tags_config()

    # Check if tag with same name already exists
    for existing_tag in config.get("tags", []):
        if existing_tag.get("tag_name") == request.tag_name:
            raise HTTPException(400, f"Tag with name '{request.tag_name}' already exists")

    # Try to auto-detect data_type from adapter if not specified
    detected_data_type = request.data_type

    for adapter in pm.adapters.values():
        if adapter.adapter_id == request.adapter_id:
            # Check last_values for this address
            if hasattr(adapter, 'last_values') and request.address in adapter.last_values:
                cached = adapter.last_values[request.address]
                value = cached.get('value')

                # Auto-detect type from value
                if isinstance(value, bool):
                    detected_data_type = "boolean"
                elif isinstance(value, int):
                    detected_data_type = "int32"
                elif isinstance(value, float):
                    detected_data_type = "double"
                elif isinstance(value, str):
                    detected_data_type = "string"

                logger.info(f"Auto-detected data_type for {request.tag_name}: {detected_data_type} (from value: {type(value).__name__})")
            break

    # Generate tag_id
    tag_id = f"tag_{uuid.uuid4().hex[:8]}"

    # Build tag object
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_tag = {
        "tag_id": tag_id,
        "tag_name": request.tag_name,
        "address": request.address,
        "data_type": detected_data_type,
        "protocol_type": "opcua",  # Default, could be detected from adapter
        "adapter_id": request.adapter_id,
        "enabled": request.enabled,
        "read_only": request.read_only,
        "quality": "Good",
        "scaling": request.scaling,
        "deadband": None,
        "historian": request.historian or {
            "enabled": True,
            "mode": "on_change",
            "interval_ms": 1000,
            "retention_days": None,
            "compress": True,
            "exception_deadband": None
        },
        "alarm": request.alarm,
        "advanced_alarms": [],
        "validation": None,
        "formula": None,
        "event_triggers": [],
        "actions": [],
        "metadata": request.metadata or {
            "description": "",
            "engineering_units": "",
            "asset_id": None,
            "asset_name": None,
            "location": None,
            "pid_tag": None,
            "custom_properties": {}
        },
        "group_path": None,
        "tags": [],
        "current_value": None,
        "current_value_timestamp": None,
        "last_good_value": None,
        "last_change_timestamp": None,
        "read_count": 0,
        "error_count": 0,
        "last_error": None,
        "created_at": now,
        "updated_at": now
    }

    # Add to config
    if "tags" not in config:
        config["tags"] = []

    config["tags"].append(new_tag)

    # Save
    _save_tags_config(config)

    logger.info(f"✅ Created tag: {request.tag_name} (id: {tag_id}, data_type: {detected_data_type})")

    return {
        "success": True,
        "tag_id": tag_id,
        "tag_name": request.tag_name,
        "data_type": detected_data_type,
        "message": f"Tag '{request.tag_name}' created successfully"
    }


@router.put("/{tag_id}")
async def update_tag(
    tag_id: str,
    request: TagUpdateRequest
):
    """
    Update a managed tag

    Only updates fields that are provided (partial update)
    """
    config = _load_tags_config()

    tag_found = False
    for tag in config.get("tags", []):
        if tag.get("tag_id") == tag_id:
            tag_found = True

            # Update provided fields
            if request.tag_name is not None:
                tag["tag_name"] = request.tag_name
            if request.enabled is not None:
                tag["enabled"] = request.enabled
            if request.read_only is not None:
                tag["read_only"] = request.read_only
            if request.metadata is not None:
                tag["metadata"] = {**tag.get("metadata", {}), **request.metadata}
            if request.historian is not None:
                tag["historian"] = {**tag.get("historian", {}), **request.historian}

            # Handle alarm - can be dict (update) or explicit None (remove)
            # Check if 'alarm' key was sent in the request body
            if 'alarm' in (request.model_dump(exclude_unset=True) if hasattr(request, 'model_dump') else request.dict(exclude_unset=True)):
                if request.alarm is None:
                    # Explicitly set to None means remove alarm
                    tag["alarm"] = None
                    logger.info(f"Removed alarm config from tag {tag_id}")
                else:
                    # Update alarm config
                    tag["alarm"] = request.alarm
                    logger.info(f"Updated alarm config for tag {tag_id}: {request.alarm}")

            if request.scaling is not None:
                tag["scaling"] = request.scaling
            if request.deadband is not None:
                tag["deadband"] = request.deadband

            tag["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break

    if not tag_found:
        raise HTTPException(404, f"Tag '{tag_id}' not found")

    _save_tags_config(config)

    logger.info(f"✅ Updated tag: {tag_id}")

    return {
        "success": True,
        "tag_id": tag_id,
        "message": f"Tag updated successfully"
    }


@router.delete("/{tag_id}")
async def delete_tag(tag_id: str):
    """
    Delete a managed tag
    """
    config = _load_tags_config()

    original_count = len(config.get("tags", []))
    config["tags"] = [t for t in config.get("tags", []) if t.get("tag_id") != tag_id]

    if len(config["tags"]) == original_count:
        raise HTTPException(404, f"Tag '{tag_id}' not found")

    _save_tags_config(config)

    logger.info(f"✅ Deleted tag: {tag_id}")

    return {
        "success": True,
        "tag_id": tag_id,
        "message": f"Tag deleted successfully"
    }


# IMPORTANT: This parameterized route MUST be at the END to avoid capturing
# routes like /export/csv, /list, /managed, etc.
@router.get("/{tag_id}")
async def get_tag_by_id(
    tag_id: str,
    pm=Depends(get_protocol_manager)
):
    """
    Get a specific managed tag by ID

    NOTE: This route is placed at the end to avoid capturing static routes.
    """
    # Skip if tag_id matches a static route name
    static_routes = {'export', 'list', 'managed', 'realtime', 'search', 'adapter'}
    if tag_id.split('/')[0] in static_routes:
        raise HTTPException(404, f"Invalid route: {tag_id}")

    config = _load_tags_config()

    for tag in config.get("tags", []):
        if tag.get("tag_id") == tag_id:
            # Add realtime value if available
            adapter_id = tag.get("adapter_id")
            address = tag.get("address")

            for adapter in pm.adapters.values():
                if adapter.adapter_id == adapter_id:
                    if hasattr(adapter, 'last_values') and address in adapter.last_values:
                        cached = adapter.last_values[address]
                        tag['current_value'] = cached.get('value')
                        tag['current_quality'] = cached.get('quality', 'Good')
                        tag['current_timestamp'] = cached.get('timestamp')
                    break

            return tag

    raise HTTPException(404, f"Tag '{tag_id}' not found")
