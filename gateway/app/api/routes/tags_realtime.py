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
        # Group tags by adapter (for efficient batch reading)
        tags_by_adapter: Dict[Any, List[str]] = {}

        for tag_name in tag_names:
            found = False
            for adapter in pm.adapters.values():
                for tag in adapter.config.tags:
                    if tag.get('name') == tag_name:
                        if adapter not in tags_by_adapter:
                            tags_by_adapter[adapter] = []
                        tags_by_adapter[adapter].append(tag_name)
                        found = True
                        break
                if found:
                    break

        # Read from all adapters in parallel
        results = []
        read_tasks = []

        for adapter, adapter_tag_names in tags_by_adapter.items():
            if adapter.connected:
                read_tasks.append(adapter.read_tags())

        # Execute all reads in parallel
        if read_tasks:
            all_tags_data = await asyncio.gather(*read_tasks, return_exceptions=True)

            # Flatten results and filter requested tags
            for tags_data in all_tags_data:
                if isinstance(tags_data, Exception):
                    logger.error(f"Error reading tags: {tags_data}")
                    continue

                for tag_data in tags_data:
                    if tag_data.tag_name in tag_names:
                        results.append({
                            "tag_name": tag_data.tag_name,
                            "value": tag_data.value,
                            "quality": tag_data.quality,
                            "timestamp": tag_data.timestamp,
                            "address": tag_data.address
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
