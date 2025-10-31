# SmartPort OPC UA Integration - Implementation Status

## Overview
Implementation of OPC UA server integration for SmartPort platform. The system connects to OPC UA servers (PLC simulators), browses available tags, and imports them for use in dashboards.

## Architecture
```
OPC UA Server (PLC Simulator)
    ↓
SmartPort Backend (/devices endpoint)
    ↓ Browse Tags
Auto-discover tags
    ↓ Import
Tags stored in PostgreSQL
    ↓
Available at /tags endpoint
    ↓
Dashboard Builder consumes tags
```

## ✅ Completed - Backend

### 1. OPC UA Client Service
**File**: `backend/app/services/opcua_client.py`
- Connect/disconnect from OPC UA servers
- Test connection and get server info
- Browse server nodes recursively to discover tags
- Read single and multiple tags
- Subscribe to tag changes for real-time monitoring
- Map OPC UA data types to system data types

### 2. Schemas
**Files**: `backend/app/schemas/device.py`, `backend/app/schemas/tag.py`
- Device schemas (create, update, response)
- Protocol-specific connection configurations (OPC UA, Modbus, MQTT)
- Tag schemas with full metadata
- Browse/import request/response schemas

### 3. Device Endpoints
**File**: `backend/app/api/v1/endpoints/devices.py`

Endpoints:
- `GET /api/v1/devices/` - List devices with filters
- `POST /api/v1/devices/` - Create new device
- `GET /api/v1/devices/{id}` - Get device details
- `PUT /api/v1/devices/{id}` - Update device
- `DELETE /api/v1/devices/{id}` - Delete device
- `POST /api/v1/devices/test-connection` - Test OPC UA connection
- `POST /api/v1/devices/browse-tags` - Browse/discover tags from OPC UA server
- `POST /api/v1/devices/import-tags` - Import discovered tags to database

### 4. Tag Endpoints
**File**: `backend/app/api/v1/endpoints/tags.py`

Endpoints:
- `GET /api/v1/tags/` - List tags with filters and search
- `GET /api/v1/tags/with-devices` - List tags with device info (for dashboard-builder)
- `POST /api/v1/tags/` - Create tag
- `GET /api/v1/tags/{id}` - Get tag details
- `PUT /api/v1/tags/{id}` - Update tag
- `DELETE /api/v1/tags/{id}` - Delete tag
- `GET /api/v1/tags/{id}/latest` - Get latest cached value (fast, from PostgreSQL)
- `GET /api/v1/tags/{id}/history` - Get historical values (from InfluxDB)

## ✅ Completed - Frontend (Partial)

### 1. TypeScript Types
**Files**: `frontend/src/types/device.ts`, `frontend/src/types/tag.ts`
- Complete type definitions for devices and tags
- Enums for protocols, status, data types, categories

### 2. API Client
**Files**: `frontend/src/api/client.ts`, `frontend/src/api/devices.ts`, `frontend/src/api/tags.ts`
- Axios-based API client with interceptors
- Type-safe device API methods
- Type-safe tag API methods

### 3. Devices Page (Started)
**File**: `frontend/src/pages/DevicesPage.tsx`
- List devices with pagination
- Add device button
- Refresh functionality

## 🚧 Pending - Frontend

### Components Needed:
1. **AddDeviceModal.tsx** - Modal for adding new OPC UA device
   - Connection form (endpoint, credentials)
   - Test connection button
   - Browse tags functionality
   - Select/import tags to system

2. **DeviceCard.tsx** - Card component for device list
   - Display device info, status, tag count
   - Actions: browse tags, view details, delete

3. **TagsPage.tsx** - Page for listing all tags
   - Filter by device, category, search
   - Display tag metadata, last value
   - Link to device

4. **App.tsx Update** - Add routing
   - React Router setup
   - Routes for /devices, /tags, /dashboard-builder

5. **DashboardBuilder Update** - Consume tags from /tags endpoint
   - Fetch available tags from API
   - Allow selecting tags for charts
   - Display tag values in real-time

## 📝 Usage Flow

### 1. Connect to OPC UA Server
```
1. User goes to /devices
2. Clicks "Add Device"
3. Selects protocol "OPC UA"
4. Enters endpoint: opc.tcp://localhost:4840
5. Clicks "Test Connection"
   → Backend connects to OPC UA server
   → Returns server info (success/error)
```

### 2. Browse and Import Tags
```
6. User clicks "Browse Tags"
   → Backend browses OPC UA server node tree
   → Returns list of discovered tags (name, type, address, current value)
7. User selects tags to import
8. Clicks "Import Selected Tags"
   → Tags saved to PostgreSQL database
   → Device total_tags count updated
```

### 3. View Tags
```
9. User goes to /tags
   → Displays all tags from all devices
   → Can filter by device, category, search
   → Shows tag metadata and last value
```

### 4. Use in Dashboard
```
10. User goes to /dashboard-builder
11. Selects tags from /tags endpoint
12. Creates charts/visualizations
13. Dashboard displays real-time tag values
```

## 🔧 Technical Details

### Database Models
- **Device**: Connection info, status, metadata
- **Tag**: Tag metadata, cached value, configuration
- **Time Series (InfluxDB)**: Historical tag values

### Data Collection (TODO)
- Celery task to poll OPC UA tags periodically
- Write values to InfluxDB
- Update PostgreSQL cache (last_value, last_timestamp)

### Real-time Updates (TODO)
- WebSocket connection for dashboard updates
- OPC UA subscriptions for change notifications

## 📦 Dependencies

### Backend
- `asyncua==1.0.6` - OPC UA client library
- `fastapi`, `sqlalchemy`, `influxdb-client`

### Frontend
- `react-router-dom` - Routing
- `axios` - HTTP client
- `@tanstack/react-query` - Data fetching
- `lucide-react` - Icons

## 🚀 Next Steps

1. Complete frontend components (AddDeviceModal, DeviceCard)
2. Complete TagsPage
3. Update App.tsx with routing
4. Update DashboardBuilder to use /tags endpoint
5. Implement Celery task for data collection
6. Test complete flow with OPC UA simulator

## 📚 Related Files

- Backend: `backend/app/api/v1/endpoints/{devices,tags}.py`
- Frontend: `frontend/src/pages/DevicesPage.tsx`
- Models: `backend/app/models/{device,tag}.py`
- Schemas: `backend/app/schemas/{device,tag}.py`
