# Gateway Configuration API Documentation

## Overview

The OptiFlow Gateway Configuration API provides REST endpoints for managing industrial protocol adapters on edge devices. This API allows you to:

- Configure and manage protocol adapters (OPC UA, Modbus, MQTT, etc.)
- Discover tags from connected devices
- Monitor adapter status and statistics
- Test connections
- Start/stop adapters dynamically

**Base URL**: `http://localhost:8080`

**API Documentation (Swagger)**: `http://localhost:8080/docs`

---

## Architecture

```
Edge Device Configuration UI
    ↓
    ↓ HTTP REST API
    ↓
Gateway API (port 8080)
    ↓
    ├─→ Protocol Manager
    │    └─→ Adapters (OPC UA, Modbus, MQTT)
    │         └─→ PLCs/Sensors
    └─→ Kafka Producer
         └─→ Topic: raw_tags
```

---

## Authentication

Currently, the API is **open** (no authentication). For production deployments, implement:
- API Keys
- JWT tokens
- OAuth 2.0

---

## Endpoints

### Health & Info

#### `GET /`
Get API information

**Response**:
```json
{
  "name": "OptiFlow Gateway API",
  "version": "1.0.0",
  "description": "Tag browsing and configuration API"
}
```

#### `GET /health`
Health check endpoint

**Response**:
```json
{
  "status": "healthy"
}
```

---

### Adapter Management

#### `GET /api/adapters/`
List all configured adapters

**Query Parameters**:
- `protocol` (optional): Filter by protocol type (opcua, modbus, mqtt)
- `enabled_only` (optional): Show only enabled adapters (default: false)

**Response**:
```json
[
  {
    "adapter_id": "opcua-simulator-001",
    "adapter_name": "OptiFlow Terminal Simulator",
    "protocol_type": "opcua",
    "enabled": true,
    "host": "opcua-server",
    "port": 4840,
    "connected": true,
    "running": true,
    "tags_count": 53,
    "scan_rate_ms": 1000,
    "timeout": 10.0,
    "retry_interval": 10.0,
    "extra_config": {
      "security_mode": "None",
      "security_policy": "None",
      "subscription_interval": 100
    },
    "kafka_config": null
  }
]
```

**Example**:
```bash
curl http://localhost:8080/api/adapters/

# Filter by protocol
curl "http://localhost:8080/api/adapters/?protocol=opcua"

# Only enabled adapters
curl "http://localhost:8080/api/adapters/?enabled_only=true"
```

---

#### `GET /api/adapters/{adapter_id}`
Get detailed information about a specific adapter

**Path Parameters**:
- `adapter_id`: Unique adapter identifier

**Response**: Same structure as list endpoint, but single object

**Example**:
```bash
curl http://localhost:8080/api/adapters/opcua-simulator-001
```

**Error Responses**:
- `404 Not Found`: Adapter not found

---

#### `POST /api/adapters/`
Create a new protocol adapter

**Request Body**:
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

**Response**:
```json
{
  "success": true,
  "adapter_id": "opcua-a1b2c3d4",
  "message": "Adapter 'opcua-a1b2c3d4' created successfully",
  "adapter": { /* adapter config */ }
}
```

**Example**:
```bash
curl -X POST http://localhost:8080/api/adapters/ \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

**Error Responses**:
- `500 Internal Server Error`: Failed to create adapter

---

#### `PUT /api/adapters/{adapter_id}`
Update an existing adapter configuration

**Path Parameters**:
- `adapter_id`: Adapter to update

**Request Body** (all fields optional):
```json
{
  "adapter_name": "Updated Name",
  "enabled": false,
  "host": "192.168.1.20",
  "scan_rate_ms": 2000
}
```

**Response**:
```json
{
  "success": true,
  "adapter_id": "opcua-simulator-001",
  "message": "Adapter 'opcua-simulator-001' updated successfully"
}
```

**Example**:
```bash
curl -X PUT http://localhost:8080/api/adapters/opcua-simulator-001 \
  -H "Content-Type: application/json" \
  -d '{"scan_rate_ms": 2000}'
```

**Note**: The adapter will be restarted with the new configuration

**Error Responses**:
- `404 Not Found`: Adapter not found

---

#### `DELETE /api/adapters/{adapter_id}`
Delete an adapter

**Path Parameters**:
- `adapter_id`: Adapter to delete

**Response**:
```json
{
  "success": true,
  "adapter_id": "opcua-simulator-001",
  "message": "Adapter 'opcua-simulator-001' deleted successfully"
}
```

**Example**:
```bash
curl -X DELETE http://localhost:8080/api/adapters/opcua-simulator-001
```

**Note**: The adapter will be stopped before deletion

**Error Responses**:
- `404 Not Found`: Adapter not found

---

### Adapter Control

#### `POST /api/adapters/{adapter_id}/start`
Start a stopped adapter

**Path Parameters**:
- `adapter_id`: Adapter to start

**Response**:
```json
{
  "success": true,
  "adapter_id": "opcua-simulator-001",
  "message": "Adapter 'opcua-simulator-001' started successfully",
  "connected": true
}
```

**Example**:
```bash
curl -X POST http://localhost:8080/api/adapters/opcua-simulator-001/start
```

---

#### `POST /api/adapters/{adapter_id}/stop`
Stop a running adapter

**Path Parameters**:
- `adapter_id`: Adapter to stop

**Response**:
```json
{
  "success": true,
  "adapter_id": "opcua-simulator-001",
  "message": "Adapter 'opcua-simulator-001' stopped successfully"
}
```

**Example**:
```bash
curl -X POST http://localhost:8080/api/adapters/opcua-simulator-001/stop
```

---

#### `POST /api/adapters/{adapter_id}/test`
Test adapter connection to device

**Path Parameters**:
- `adapter_id`: Adapter to test

**Response**:
```json
{
  "success": true,
  "adapter_id": "opcua-simulator-001",
  "connected": true,
  "message": "Connection successful! Found 53 tags.",
  "discovered_tags_count": 53
}
```

**Example**:
```bash
curl -X POST http://localhost:8080/api/adapters/opcua-simulator-001/test
```

---

#### `POST /api/adapters/{adapter_id}/discover`
Trigger tag discovery for an adapter

**Path Parameters**:
- `adapter_id`: Adapter to discover tags from

**Response**:
```json
{
  "success": true,
  "adapter_id": "opcua-simulator-001",
  "message": "Discovered 53 tags",
  "discovered_tags": [
    {
      "name": "running",
      "address": "ns=2;i=7",
      "type": "boolean"
    },
    {
      "name": "speed_mps",
      "address": "ns=2;i=8",
      "type": "double"
    }
  ],
  "count": 53
}
```

**Example**:
```bash
curl -X POST http://localhost:8080/api/adapters/opcua-simulator-001/discover
```

**Note**: This triggers auto-discovery. For OPC UA adapters, it browses the server namespace and finds all readable variables.

---

### Monitoring

#### `GET /api/adapters/{adapter_id}/statistics`
Get detailed statistics for an adapter

**Path Parameters**:
- `adapter_id`: Adapter to get statistics for

**Response**:
```json
{
  "adapter_id": "opcua-simulator-001",
  "adapter_name": "OptiFlow Terminal Simulator",
  "protocol": "opcua",
  "connected": true,
  "running": true,
  "statistics": {
    "read_count": 1250,
    "error_count": 0,
    "last_read_time": "2025-11-19T18:45:00Z"
  },
  "endpoint": "opcua-server:4840",
  "scan_rate_ms": 1000
}
```

**Example**:
```bash
curl http://localhost:8080/api/adapters/opcua-simulator-001/statistics
```

---

## Data Models

### AdapterConfig

```json
{
  "adapter_name": "string",
  "protocol_type": "opcua | modbus | mqtt | ethernet_ip | s7",
  "enabled": true,
  "host": "string (IP or hostname)",
  "port": 4840,
  "scan_rate_ms": 1000,
  "timeout": 10.0,
  "retry_interval": 10.0,
  "extra_config": {
    // Protocol-specific configuration
  },
  "tags": [
    {
      "name": "tag_name",
      "address": "protocol_specific_address",
      "type": "data_type"
    }
  ]
}
```

### Protocol Types

- **opcua**: OPC UA (Open Platform Communications Unified Architecture)
- **modbus**: Modbus TCP/IP
- **mqtt**: MQTT (Message Queuing Telemetry Transport)
- **ethernet_ip**: EtherNet/IP
- **s7**: Siemens S7

### Extra Config Examples

#### OPC UA
```json
{
  "security_mode": "None | Sign | SignAndEncrypt",
  "security_policy": "None | Basic256 | Basic256Sha256",
  "subscription_interval": 100
}
```

#### Modbus
```json
{
  "slave_id": 1,
  "byte_order": "big | little"
}
```

#### MQTT
```json
{
  "client_id": "gateway-001",
  "username": "optional",
  "password": "optional",
  "qos": 1
}
```

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service not available

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Examples

### Complete Workflow: Add New OPC UA Device

```bash
# 1. Create adapter
curl -X POST http://localhost:8080/api/adapters/ \
  -H "Content-Type: application/json" \
  -d '{
    "adapter_name": "Production Line PLC",
    "protocol_type": "opcua",
    "enabled": true,
    "host": "192.168.1.50",
    "port": 4840,
    "scan_rate_ms": 1000,
    "timeout": 10.0,
    "retry_interval": 10.0,
    "extra_config": {
      "security_mode": "None",
      "security_policy": "None"
    },
    "tags": []
  }'

# Response: {"success": true, "adapter_id": "opcua-xyz123", ...}

# 2. Test connection
curl -X POST http://localhost:8080/api/adapters/opcua-xyz123/test

# 3. Discover tags
curl -X POST http://localhost:8080/api/adapters/opcua-xyz123/discover

# 4. Check adapter status
curl http://localhost:8080/api/adapters/opcua-xyz123

# 5. Monitor statistics
curl http://localhost:8080/api/adapters/opcua-xyz123/statistics

# 6. Update configuration (if needed)
curl -X PUT http://localhost:8080/api/adapters/opcua-xyz123 \
  -H "Content-Type: application/json" \
  -d '{"scan_rate_ms": 500}'

# 7. Stop adapter (for maintenance)
curl -X POST http://localhost:8080/api/adapters/opcua-xyz123/stop

# 8. Restart adapter
curl -X POST http://localhost:8080/api/adapters/opcua-xyz123/start
```

---

## Integration with Frontend

### React/Vue Example

```javascript
// List all adapters
const response = await fetch('http://localhost:8080/api/adapters/');
const adapters = await response.json();

// Create new adapter
await fetch('http://localhost:8080/api/adapters/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    adapter_name: 'New PLC',
    protocol_type: 'opcua',
    host: '192.168.1.10',
    port: 4840,
    enabled: true,
    scan_rate_ms: 1000,
    timeout: 10.0,
    retry_interval: 10.0,
    extra_config: {},
    tags: []
  })
});

// Discover tags
const discovery = await fetch(
  'http://localhost:8080/api/adapters/opcua-xyz123/discover',
  { method: 'POST' }
);
const tags = await discovery.json();
```

---

## Best Practices

1. **Always test connection** before enabling an adapter
2. **Use discovery** to automatically find available tags
3. **Monitor statistics** to track adapter health
4. **Set appropriate scan rates** (don't overload devices)
5. **Use reasonable timeouts** (5-10 seconds recommended)
6. **Configure retry intervals** for automatic recovery
7. **Stop adapters** before configuration changes
8. **Back up configurations** before making changes

---

## Troubleshooting

### Adapter won't connect

1. Check host and port are correct
2. Verify network connectivity: `ping <host>`
3. Check firewall rules
4. Test connection: `POST /api/adapters/{id}/test`
5. Check adapter logs in Gateway container

### Discovery returns no tags

1. Verify adapter is connected
2. Check protocol-specific namespace settings (OPC UA)
3. Ensure device has readable tags/registers
4. Check device security settings

### Tags not updating

1. Check adapter statistics: `GET /api/adapters/{id}/statistics`
2. Verify scan_rate_ms is set correctly
3. Check Kafka connectivity
4. Verify tag addresses are valid

---

## Support

For issues and questions:
- GitHub: https://github.com/anthropics/optiflow-ai
- Documentation: `http://localhost:8080/docs` (Swagger UI)

---

## Version History

- **v1.0.0** (2025-11-19): Initial release
  - CRUD endpoints for adapters
  - Tag discovery
  - Connection testing
  - Statistics monitoring
