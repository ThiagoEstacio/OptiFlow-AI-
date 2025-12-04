"""
Adapter Configuration API Routes
==================================

CRUD endpoints for managing protocol adapters in the Gateway.
Allows edge device configuration through REST API.

Features:
- List all adapters
- Get adapter details
- Create new adapter
- Update adapter configuration
- Delete adapter
- Start/stop adapter
- Test adapter connection
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json
from pathlib import Path

from app.core.logger import logger

router = APIRouter()


# === PYDANTIC MODELS ===

class AdapterConfigBase(BaseModel):
    """Base configuration for protocol adapter"""
    adapter_name: str = Field(..., description="Human-readable adapter name")
    protocol_type: str = Field(..., description="Protocol type: opcua, modbus, mqtt")
    enabled: bool = Field(True, description="Enable/disable adapter")
    host: str = Field(..., description="PLC/Device host address")
    port: int = Field(..., description="PLC/Device port")
    scan_rate_ms: int = Field(1000, description="Scan rate in milliseconds")
    timeout: float = Field(10.0, description="Connection timeout in seconds")
    retry_interval: float = Field(10.0, description="Retry interval in seconds")
    extra_config: Dict[str, Any] = Field(default_factory=dict, description="Protocol-specific configuration")
    tags: List[Dict[str, Any]] = Field(default_factory=list, description="Tag configurations")
    kafka_config: Optional[Dict[str, Any]] = Field(None, description="Kafka configuration")


class AdapterCreate(AdapterConfigBase):
    """Model for creating new adapter"""
    pass


class AdapterUpdate(BaseModel):
    """Model for updating existing adapter (all fields optional)"""
    adapter_name: Optional[str] = None
    protocol_type: Optional[str] = None
    enabled: Optional[bool] = None
    host: Optional[str] = None
    port: Optional[int] = None
    scan_rate_ms: Optional[int] = None
    timeout: Optional[float] = None
    retry_interval: Optional[float] = None
    extra_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[Dict[str, Any]]] = None
    kafka_config: Optional[Dict[str, Any]] = None


class AdapterResponse(BaseModel):
    """Response model for adapter"""
    adapter_id: str
    adapter_name: str
    protocol_type: str
    enabled: bool
    host: str
    port: int
    connected: bool
    running: bool
    tags_count: int
    scan_rate_ms: int
    timeout: float
    retry_interval: float
    extra_config: Dict[str, Any]
    kafka_config: Optional[Dict[str, Any]]


class AdapterTestResult(BaseModel):
    """Result of adapter connection test"""
    success: bool
    adapter_id: str
    connected: bool
    message: str
    discovered_tags_count: Optional[int] = None
    error: Optional[str] = None


# === DEPENDENCY INJECTION ===

def get_protocol_manager():
    """Get protocol manager from global state"""
    from app.main_kafka import protocol_manager
    if protocol_manager is None:
        raise HTTPException(503, "Protocol manager not initialized")
    return protocol_manager


def get_config_path():
    """Get config file path"""
    return "/app/config/adapters_config.json"


# === ADAPTER CRUD ENDPOINTS ===

@router.get("/", response_model=List[AdapterResponse])
async def list_adapters(
    protocol: Optional[str] = Query(None, description="Filter by protocol type"),
    enabled_only: bool = Query(False, description="Show only enabled adapters"),
    verify_connection: bool = Query(False, description="Verify actual connection with health check"),
    pm=Depends(get_protocol_manager)
):
    """
    List all configured adapters

    **Query Parameters**:
    - `protocol`: Filter by protocol type (opcua, modbus, mqtt)
    - `enabled_only`: Show only enabled adapters
    - `verify_connection`: Perform actual health check to verify connection status

    **Returns**: List of adapter configurations
    """
    adapters_list = []

    for adapter_id, adapter in pm.adapters.items():
        # Apply filters
        if protocol and adapter.config.protocol_type != protocol:
            continue

        if enabled_only and not adapter.config.enabled:
            continue

        # Get adapter_name from extra_config or use adapter_id
        adapter_name = adapter.config.extra_config.get('adapter_name', adapter_id)

        # Verify actual connection status if requested
        actual_connected = adapter.connected
        if verify_connection and adapter.connected:
            try:
                # Perform actual health check
                if hasattr(adapter, 'health_check'):
                    actual_connected = await adapter.health_check()
                    if not actual_connected:
                        logger.warning(f"⚠️  Adapter '{adapter_id}' reports connected but health check failed")
            except Exception as e:
                logger.error(f"❌ Health check error for '{adapter_id}': {e}")
                actual_connected = False

        # Get tags count - for virtual adapters, use filtered count from stats
        tags_count = len(adapter.config.tags)
        if hasattr(adapter, '_tags_filtered') and adapter._tags_filtered > 0:
            tags_count = adapter._tags_filtered

        adapters_list.append(AdapterResponse(
            adapter_id=adapter_id,
            adapter_name=adapter_name,
            protocol_type=adapter.config.protocol_type,
            enabled=adapter.config.enabled,
            host=adapter.config.host,
            port=adapter.config.port,
            connected=actual_connected,
            running=adapter.running,
            tags_count=tags_count,
            scan_rate_ms=adapter.config.scan_rate_ms,
            timeout=adapter.config.timeout,
            retry_interval=adapter.config.retry_interval,
            extra_config=adapter.config.extra_config,
            kafka_config=getattr(adapter.config, 'kafka_config', None)
        ))

    return adapters_list


@router.get("/{adapter_id}", response_model=AdapterResponse)
async def get_adapter(
    adapter_id: str,
    pm=Depends(get_protocol_manager)
):
    """
    Get detailed information about a specific adapter

    **Path Parameters**:
    - `adapter_id`: Unique adapter identifier

    **Returns**: Adapter configuration and status
    """
    adapter = pm.adapters.get(adapter_id)

    if not adapter:
        raise HTTPException(404, f"Adapter '{adapter_id}' not found")

    # Get adapter_name from extra_config or use adapter_id
    adapter_name = adapter.config.extra_config.get('adapter_name', adapter_id)

    # Get tags count - for virtual adapters, use filtered count from stats
    tags_count = len(adapter.config.tags)
    if hasattr(adapter, '_tags_filtered') and adapter._tags_filtered > 0:
        tags_count = adapter._tags_filtered

    return AdapterResponse(
        adapter_id=adapter_id,
        adapter_name=adapter_name,
        protocol_type=adapter.config.protocol_type,
        enabled=adapter.config.enabled,
        host=adapter.config.host,
        port=adapter.config.port,
        connected=adapter.connected,
        running=adapter.running,
        tags_count=tags_count,
        scan_rate_ms=adapter.config.scan_rate_ms,
        timeout=adapter.config.timeout,
        retry_interval=adapter.config.retry_interval,
        extra_config=adapter.config.extra_config,
        kafka_config=getattr(adapter.config, 'kafka_config', None)
    )


@router.post("/", status_code=201)
async def create_adapter(
    adapter_config: AdapterCreate,
    pm=Depends(get_protocol_manager),
    config_path: str = Depends(get_config_path)
):
    """
    Create a new protocol adapter

    **Request Body**: Adapter configuration (AdapterCreate model)

    **Returns**: Created adapter with generated ID

    **Example**:
    ```json
    {
      "adapter_name": "PLC Silo 1",
      "protocol_type": "opcua",
      "enabled": true,
      "host": "192.168.1.10",
      "port": 4840,
      "scan_rate_ms": 1000,
      "timeout": 10.0,
      "retry_interval": 10.0,
      "extra_config": {
        "security_mode": "None",
        "security_policy": "None"
      },
      "tags": []
    }
    ```
    """
    try:
        # Generate unique adapter ID
        import uuid
        adapter_id = f"{adapter_config.protocol_type}-{uuid.uuid4().hex[:8]}"

        # Load existing config
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r') as f:
                config_data = json.load(f)
        else:
            config_data = {"adapters": []}

        # Create adapter config dict
        new_adapter = {
            "adapter_id": adapter_id,
            "adapter_name": adapter_config.adapter_name,
            "protocol_type": adapter_config.protocol_type,
            "enabled": adapter_config.enabled,
            "host": adapter_config.host,
            "port": adapter_config.port,
            "scan_rate_ms": adapter_config.scan_rate_ms,
            "timeout": adapter_config.timeout,
            "retry_interval": adapter_config.retry_interval,
            "extra_config": adapter_config.extra_config,
            "tags": adapter_config.tags
        }

        if adapter_config.kafka_config:
            new_adapter["kafka_config"] = adapter_config.kafka_config

        # Add to config
        config_data["adapters"].append(new_adapter)

        # Save config
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"✅ Created adapter '{adapter_id}' - saved to config")

        # Reload configuration in protocol manager
        await pm.load_config()

        # Start adapter if enabled
        if adapter_config.enabled:
            adapter = pm.adapters.get(adapter_id)
            if adapter and not adapter.running:
                await adapter.start()
                logger.info(f"✅ Started adapter '{adapter_id}'")

        return {
            "success": True,
            "adapter_id": adapter_id,
            "message": f"Adapter '{adapter_id}' created successfully",
            "adapter": new_adapter
        }

    except Exception as e:
        logger.error(f"❌ Failed to create adapter: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to create adapter: {str(e)}")


@router.put("/{adapter_id}")
async def update_adapter(
    adapter_id: str,
    adapter_update: AdapterUpdate,
    pm=Depends(get_protocol_manager),
    config_path: str = Depends(get_config_path)
):
    """
    Update an existing adapter configuration

    **Path Parameters**:
    - `adapter_id`: Adapter to update

    **Request Body**: Fields to update (all optional)

    **Returns**: Updated adapter configuration
    """
    try:
        # Load current config
        config_file = Path(config_path)
        if not config_file.exists():
            raise HTTPException(404, "Configuration file not found")

        with open(config_file, 'r') as f:
            config_data = json.load(f)

        # Find adapter
        adapter_found = False
        for i, adapter in enumerate(config_data["adapters"]):
            if adapter["adapter_id"] == adapter_id:
                adapter_found = True

                # Update fields (only if provided)
                update_dict = adapter_update.dict(exclude_unset=True)
                for key, value in update_dict.items():
                    adapter[key] = value

                config_data["adapters"][i] = adapter
                break

        if not adapter_found:
            raise HTTPException(404, f"Adapter '{adapter_id}' not found")

        # Save config
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"✅ Updated adapter '{adapter_id}' - saved to config")

        # Reload configuration
        await pm.load_config()

        # Restart adapter if it was running
        adapter = pm.adapters.get(adapter_id)
        if adapter:
            if adapter.running:
                await adapter.stop()
                await adapter.start()
                logger.info(f"✅ Restarted adapter '{adapter_id}' with new config")

        return {
            "success": True,
            "adapter_id": adapter_id,
            "message": f"Adapter '{adapter_id}' updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update adapter: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to update adapter: {str(e)}")


@router.delete("/{adapter_id}")
async def delete_adapter(
    adapter_id: str,
    pm=Depends(get_protocol_manager),
    config_path: str = Depends(get_config_path)
):
    """
    Delete an adapter

    **Path Parameters**:
    - `adapter_id`: Adapter to delete

    **Returns**: Success message
    """
    try:
        # Stop adapter first
        adapter = pm.adapters.get(adapter_id)
        if adapter and adapter.running:
            await adapter.stop()
            logger.info(f"✅ Stopped adapter '{adapter_id}' before deletion")

        # Remove from protocol manager
        if adapter_id in pm.adapters:
            del pm.adapters[adapter_id]

        # Load config
        config_file = Path(config_path)
        if not config_file.exists():
            raise HTTPException(404, "Configuration file not found")

        with open(config_file, 'r') as f:
            config_data = json.load(f)

        # Remove adapter
        original_count = len(config_data["adapters"])
        config_data["adapters"] = [
            a for a in config_data["adapters"]
            if a["adapter_id"] != adapter_id
        ]

        if len(config_data["adapters"]) == original_count:
            raise HTTPException(404, f"Adapter '{adapter_id}' not found in config")

        # Save config
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"✅ Deleted adapter '{adapter_id}' from config")

        return {
            "success": True,
            "adapter_id": adapter_id,
            "message": f"Adapter '{adapter_id}' deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete adapter: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to delete adapter: {str(e)}")


# === ADAPTER CONTROL ENDPOINTS ===

@router.post("/{adapter_id}/start")
async def start_adapter(
    adapter_id: str,
    pm=Depends(get_protocol_manager)
):
    """
    Start a stopped adapter

    **Path Parameters**:
    - `adapter_id`: Adapter to start

    **Returns**: Success message
    """
    adapter = pm.adapters.get(adapter_id)

    if not adapter:
        raise HTTPException(404, f"Adapter '{adapter_id}' not found")

    if adapter.running:
        return {
            "success": True,
            "adapter_id": adapter_id,
            "message": f"Adapter '{adapter_id}' is already running"
        }

    try:
        await adapter.start()
        logger.info(f"✅ Started adapter '{adapter_id}'")

        return {
            "success": True,
            "adapter_id": adapter_id,
            "message": f"Adapter '{adapter_id}' started successfully",
            "connected": adapter.connected
        }

    except Exception as e:
        logger.error(f"❌ Failed to start adapter '{adapter_id}': {e}", exc_info=True)
        raise HTTPException(500, f"Failed to start adapter: {str(e)}")


@router.post("/{adapter_id}/stop")
async def stop_adapter(
    adapter_id: str,
    pm=Depends(get_protocol_manager)
):
    """
    Stop a running adapter

    **Path Parameters**:
    - `adapter_id`: Adapter to stop

    **Returns**: Success message
    """
    adapter = pm.adapters.get(adapter_id)

    if not adapter:
        raise HTTPException(404, f"Adapter '{adapter_id}' not found")

    if not adapter.running:
        return {
            "success": True,
            "adapter_id": adapter_id,
            "message": f"Adapter '{adapter_id}' is already stopped"
        }

    try:
        await adapter.stop()
        logger.info(f"✅ Stopped adapter '{adapter_id}'")

        return {
            "success": True,
            "adapter_id": adapter_id,
            "message": f"Adapter '{adapter_id}' stopped successfully"
        }

    except Exception as e:
        logger.error(f"❌ Failed to stop adapter '{adapter_id}': {e}", exc_info=True)
        raise HTTPException(500, f"Failed to stop adapter: {str(e)}")


@router.post("/{adapter_id}/test", response_model=AdapterTestResult)
async def test_adapter_connection(
    adapter_id: str,
    pm=Depends(get_protocol_manager)
):
    """
    Test adapter connection to PLC/device

    **Path Parameters**:
    - `adapter_id`: Adapter to test

    **Returns**: Connection test result with discovered tags count
    """
    adapter = pm.adapters.get(adapter_id)

    if not adapter:
        raise HTTPException(404, f"Adapter '{adapter_id}' not found")

    try:
        # Check if adapter is connected
        if not adapter.connected:
            # Try to connect
            was_running = adapter.running
            if not was_running:
                await adapter.start()

            # Wait a bit for connection
            import asyncio
            await asyncio.sleep(2)

        # Check connection status
        if adapter.connected:
            tags_count = len(adapter.config.tags)

            return AdapterTestResult(
                success=True,
                adapter_id=adapter_id,
                connected=True,
                message=f"Connection successful! Found {tags_count} tags.",
                discovered_tags_count=tags_count
            )
        else:
            return AdapterTestResult(
                success=False,
                adapter_id=adapter_id,
                connected=False,
                message="Failed to connect to device",
                error="Connection timeout or refused"
            )

    except Exception as e:
        logger.error(f"❌ Connection test failed for '{adapter_id}': {e}", exc_info=True)
        return AdapterTestResult(
            success=False,
            adapter_id=adapter_id,
            connected=False,
            message="Connection test failed",
            error=str(e)
        )


@router.get("/{adapter_id}/statistics")
async def get_adapter_statistics(
    adapter_id: str,
    pm=Depends(get_protocol_manager)
):
    """
    Get detailed statistics for an adapter

    **Path Parameters**:
    - `adapter_id`: Adapter to get statistics for

    **Returns**: Adapter statistics including read counts, errors, performance metrics
    """
    adapter = pm.adapters.get(adapter_id)

    if not adapter:
        raise HTTPException(404, f"Adapter '{adapter_id}' not found")

    stats = adapter.get_statistics()

    # Get adapter_name from extra_config or use adapter_id as fallback
    adapter_name = adapter.config.extra_config.get('adapter_name', adapter_id)

    return {
        "adapter_id": adapter_id,
        "adapter_name": adapter_name,
        "protocol": adapter.config.protocol_type,
        "connected": adapter.connected,
        "running": adapter.running,
        "statistics": stats,
        "endpoint": f"{adapter.config.host}:{adapter.config.port}",
        "scan_rate_ms": adapter.config.scan_rate_ms
    }


@router.get("/{adapter_id}/health")
async def health_check_adapter(
    adapter_id: str,
    pm=Depends(get_protocol_manager)
):
    """
    Perform real health check on adapter connection

    **IMPORTANT**: This endpoint performs an actual read from the device
    to verify the connection is truly working, not just reported as connected.

    **Path Parameters**:
    - `adapter_id`: Adapter to health check

    **Returns**: Actual health status with verification
    """
    adapter = pm.adapters.get(adapter_id)

    if not adapter:
        raise HTTPException(404, f"Adapter '{adapter_id}' not found")

    # Get adapter_name from extra_config or use adapter_id as fallback
    adapter_name = adapter.config.extra_config.get('adapter_name', adapter_id)

    result = {
        "adapter_id": adapter_id,
        "adapter_name": adapter_name,
        "protocol": adapter.config.protocol_type,
        "reported_connected": adapter.connected,
        "reported_running": adapter.running,
        "verified_connected": False,
        "can_read_data": False,
        "message": "",
        "tags_readable": 0,
        "tags_total": len(adapter.config.tags)
    }

    # Check if adapter reports connected
    if not adapter.connected:
        result["message"] = "Adapter reports disconnected"
        return result

    if not adapter.running:
        result["message"] = "Adapter is not running"
        return result

    # Perform actual health check
    try:
        if hasattr(adapter, 'health_check'):
            health_ok = await adapter.health_check()
            result["verified_connected"] = health_ok

            if not health_ok:
                result["message"] = "Health check failed - connection may be stale"
                # Update adapter status to reflect reality
                adapter.connected = False
                return result
        else:
            # No health check method - assume connected status is accurate
            result["verified_connected"] = adapter.connected

    except Exception as e:
        result["message"] = f"Health check error: {str(e)}"
        result["verified_connected"] = False
        adapter.connected = False
        return result

    # Try to actually read some data to verify we can communicate
    try:
        if hasattr(adapter, 'read_all_discovered_tags'):
            tags_data = await adapter.read_all_discovered_tags()
            readable_count = sum(1 for t in tags_data if t.get('connected', False))
            result["can_read_data"] = readable_count > 0
            result["tags_readable"] = readable_count
            result["message"] = f"Verified: {readable_count}/{len(tags_data)} tags readable"
        elif hasattr(adapter, 'read_tags'):
            tags_data = await adapter.read_tags()
            readable_count = sum(1 for t in tags_data if t.quality == 'good')
            result["can_read_data"] = readable_count > 0
            result["tags_readable"] = readable_count
            result["message"] = f"Verified: {readable_count}/{len(tags_data)} tags readable"
        else:
            result["can_read_data"] = result["verified_connected"]
            result["message"] = "Connection verified (no read method available)"

    except Exception as e:
        result["can_read_data"] = False
        result["message"] = f"Data read failed: {str(e)}"
        logger.error(f"❌ Data read verification failed for '{adapter_id}': {e}")

    return result


@router.get("/{adapter_id}/tags")
async def get_adapter_tags(
    adapter_id: str,
    pm=Depends(get_protocol_manager)
):
    """
    Get real-time tags from adapter

    **Path Parameters**:
    - `adapter_id`: Adapter to get tags from

    **Returns**: List of tags with current values

    **Note**: For virtual adapters, returns tags filtered from the Node-RED ingestion buffer.
    For regular adapters, returns the configured tags with their last known values.
    """
    adapter = pm.adapters.get(adapter_id)

    if not adapter:
        raise HTTPException(404, f"Adapter '{adapter_id}' not found")

    try:
        # For virtual adapters and any adapter with read_tags method
        if hasattr(adapter, 'read_tags'):
            tags = await adapter.read_tags()

            # Convert TagData objects to dict
            tags_list = []
            for tag in tags:
                if hasattr(tag, 'to_dict'):
                    tags_list.append(tag.to_dict())
                elif isinstance(tag, dict):
                    tags_list.append(tag)
                else:
                    # Fallback for other types
                    tags_list.append({
                        'tag_name': getattr(tag, 'tag_name', str(tag)),
                        'value': getattr(tag, 'value', None),
                        'quality': getattr(tag, 'quality', 'unknown'),
                        'timestamp': getattr(tag, 'timestamp', None),
                        'source': adapter_id
                    })

            return {
                "success": True,
                "adapter_id": adapter_id,
                "protocol": adapter.config.protocol_type,
                "tags_count": len(tags_list),
                "tags": tags_list
            }

        # For adapters that support read_all_discovered_tags
        if hasattr(adapter, 'read_all_discovered_tags'):
            tags = await adapter.read_all_discovered_tags()
            return {
                "success": True,
                "adapter_id": adapter_id,
                "protocol": adapter.config.protocol_type,
                "tags_count": len(tags),
                "tags": tags
            }

        # Fallback: return configured tags without values
        configured_tags = [
            {
                'tag_name': tag.get('name', tag.get('tag_name', '')),
                'address': tag.get('address', ''),
                'type': tag.get('type', 'unknown'),
                'value': None,
                'quality': 'unknown',
                'source': adapter_id
            }
            for tag in adapter.config.tags
        ]

        return {
            "success": True,
            "adapter_id": adapter_id,
            "protocol": adapter.config.protocol_type,
            "tags_count": len(configured_tags),
            "tags": configured_tags,
            "note": "Values not available - adapter does not support real-time reading"
        }

    except Exception as e:
        logger.error(f"❌ Failed to get tags for '{adapter_id}': {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get tags: {str(e)}")


@router.post("/{adapter_id}/discover")
async def discover_tags(
    adapter_id: str,
    pm=Depends(get_protocol_manager)
):
    """
    Trigger tag discovery for an adapter

    **Path Parameters**:
    - `adapter_id`: Adapter to discover tags from

    **Returns**: Discovered tags

    **Note**: This endpoint triggers the adapter's auto-discovery feature.
    For OPC UA adapters, it will browse the server namespace and find all readable variables.
    """
    adapter = pm.adapters.get(adapter_id)

    if not adapter:
        raise HTTPException(404, f"Adapter '{adapter_id}' not found")

    # Check if adapter supports discovery
    if not hasattr(adapter, '_discover_tags'):
        return {
            "success": False,
            "adapter_id": adapter_id,
            "message": f"Adapter protocol '{adapter.protocol_type}' does not support auto-discovery",
            "discovered_tags": []
        }

    try:
        # Trigger discovery
        await adapter._discover_tags()

        # Get discovered tags
        discovered_tags = [
            {
                "name": tag.get('name'),
                "address": tag.get('address'),
                "type": tag.get('type', 'unknown')
            }
            for tag in adapter.config.tags
        ]

        return {
            "success": True,
            "adapter_id": adapter_id,
            "message": f"Discovered {len(discovered_tags)} tags",
            "discovered_tags": discovered_tags,
            "count": len(discovered_tags)
        }

    except Exception as e:
        logger.error(f"❌ Tag discovery failed for '{adapter_id}': {e}", exc_info=True)
        raise HTTPException(500, f"Tag discovery failed: {str(e)}")
