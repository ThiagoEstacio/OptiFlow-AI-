# OptiFlow AI - Port Terminal System Specification

## 🎯 Vision

Transform OptiFlow AI into a **complete industrial platform** specifically designed for **port grain terminals**, combining reliable industrial connectivity, intelligent monitoring, AI-powered analytics, and operational data management.

---

## 📋 Core Requirements

### 1. Industrial Gateway (Reliable & Multi-Protocol)
- ✅ **OPC-UA** - Universal standard for industrial communication
- ✅ **Modbus TCP** - Widely used in grain terminals
- ✅ **Siemens S7** - PLC communication protocol
- ✅ **Rockwell EtherNet/IP** - Allen-Bradley PLCs
- ✅ **Reliability**: Offline buffering, auto-reconnect, redundancy
- ✅ **Monitoring**: Connection status, data quality, latency

### 2. System Health Monitoring
- ✅ **Application Health**: CPU, RAM, disk space usage
- ✅ **Container Monitoring**: Docker container status and resource usage
- ✅ **Database Health**: PostgreSQL and InfluxDB monitoring
- ✅ **Tag Statistics**: Stored tags count, data rate, storage usage
- ✅ **Alerts**: Automatic alerts when thresholds exceeded

### 3. AI Agent Enhancements
- ✅ **Auto-Dashboard Creation**: Generate dashboards based on asset types
- ✅ **Failure Analysis**: Root cause analysis (RCA) engine
- ✅ **Pareto Charts**: Identify most frequent failures
- ✅ **Engineering Tools**: Statistical analysis, trend detection

### 4. Operational Data Management
- ✅ **GBM API Integration**: Real-time port operations data
- ✅ **Manual Data Entry**: Trucks counted, ships loaded, tonnage
- ✅ **Data Validation**: Ensure operational data quality
- ✅ **Historical Tracking**: Complete operational history

### 5. Port Terminal Specific Features
- ✅ **Grain Loading Simulator** (already exists)
- ✅ **Shiploader Dashboard**: Real-time loading operations
- ✅ **Silo Monitoring**: Levels, temperature, moisture
- ✅ **Belt Conveyor Dashboard**: Speed, load, alarms
- ✅ **Weighbridge Integration**: Truck weighing data

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                           │
│  Web UI (React) - Dashboards, Analytics, Monitoring            │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                           │
│  FastAPI Backend - Business Logic, AI Agent, Analytics         │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                 │
│  PostgreSQL (relational) + InfluxDB (time-series)              │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                   GATEWAY LAYER (NEW)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ OPC-UA   │  │ Modbus   │  │ Siemens  │  │ Rockwell │       │
│  │ Gateway  │  │ TCP      │  │ S7       │  │ EIP      │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                  MONITORING LAYER (NEW)                         │
│  System Metrics | Docker Stats | DB Health | Tag Stats         │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                    PHYSICAL LAYER                               │
│  PLCs, Sensors, Actuators, Industrial Equipment                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Implementation Phases

### PHASE 1: Industrial Gateway (Week 1-2)
**Goal**: Reliable multi-protocol connectivity to industrial equipment

#### 1.1 Python Dependencies
```python
# requirements.txt additions
asyncua==1.0.0          # OPC-UA client
pymodbus==3.5.2         # Modbus TCP client
python-snap7==1.3       # Siemens S7 protocol
pycomm3==1.2.0          # Rockwell EtherNet/IP
asyncio-mqtt==0.16.1    # MQTT for internal communication
```

#### 1.2 Gateway Components
- `backend/app/gateways/base_gateway.py` - Abstract base class
- `backend/app/gateways/opcua_gateway.py` - OPC-UA implementation
- `backend/app/gateways/modbus_gateway.py` - Modbus TCP implementation
- `backend/app/gateways/siemens_gateway.py` - Siemens S7 implementation
- `backend/app/gateways/rockwell_gateway.py` - Rockwell EIP implementation
- `backend/app/gateways/gateway_manager.py` - Unified manager
- `backend/app/models/gateway_config.py` - Configuration model

#### 1.3 Key Features
- **Auto-Reconnect**: Exponential backoff retry logic
- **Offline Buffering**: Store data when connection lost
- **Health Monitoring**: Connection status, latency, error rates
- **Data Quality**: Validate data before storage
- **Logging**: Comprehensive logging for troubleshooting

#### 1.4 Configuration Example
```yaml
gateways:
  - type: opcua
    name: "Shiploader PLC"
    endpoint: "opc.tcp://192.168.1.100:4840"
    namespace: "urn:shiploader:server"
    polling_interval: 1000  # ms
    tags:
      - node_id: "ns=2;s=Belt.Speed"
        tag_name: "shiploader_belt_speed"
      - node_id: "ns=2;s=Load.Weight"
        tag_name: "shiploader_load_weight"

  - type: modbus
    name: "Weighbridge"
    host: "192.168.1.101"
    port: 502
    unit_id: 1
    polling_interval: 2000
    registers:
      - address: 0
        count: 2
        type: float32
        tag_name: "weighbridge_gross_weight"
```

---

### PHASE 2: System Health Monitoring (Week 2-3)
**Goal**: Comprehensive monitoring of application health and infrastructure

#### 2.1 Components
- `backend/app/monitoring/system_monitor.py` - System metrics
- `backend/app/monitoring/docker_monitor.py` - Container monitoring
- `backend/app/monitoring/database_monitor.py` - DB health checks
- `backend/app/monitoring/tag_monitor.py` - Tag statistics
- `backend/app/models/system_health.py` - Health data model

#### 2.2 Metrics Collected
**System Metrics**:
- CPU usage (% and per core)
- RAM usage (used, available, %)
- Disk space (used, free, %)
- Network I/O
- Process count

**Docker Metrics**:
- Container status (running/stopped/failed)
- Container CPU usage
- Container memory usage
- Container restart count
- Container uptime

**Database Metrics**:
- Connection pool status
- Query performance
- Database size
- Active connections
- Cache hit ratio

**Tag Metrics**:
- Total tags stored
- Data points per minute
- Storage size (InfluxDB)
- Stale tags (no recent data)
- Error rates

#### 2.3 Health API Endpoints
```python
GET /api/v1/monitoring/system       # System metrics
GET /api/v1/monitoring/containers   # Docker status
GET /api/v1/monitoring/databases    # DB health
GET /api/v1/monitoring/tags         # Tag statistics
GET /api/v1/monitoring/summary      # Overall health summary
```

#### 2.4 Alert Thresholds
```python
THRESHOLDS = {
    "cpu_percent": 85,        # Alert if CPU > 85%
    "ram_percent": 90,        # Alert if RAM > 90%
    "disk_percent": 85,       # Alert if disk > 85%
    "container_restarts": 3,  # Alert if > 3 restarts in 1 hour
    "db_connections": 80,     # Alert if > 80% pool used
    "stale_tags_percent": 20, # Alert if > 20% tags stale
}
```

---

### PHASE 3: Operational Data Management (Week 3-4)
**Goal**: Track manual operational data and integrate external APIs

#### 3.1 Operational Data Models
```python
# backend/app/models/operational_data.py

class TruckEntry(Base):
    """Manual truck entry log"""
    timestamp = Column(DateTime)
    truck_id = Column(String)
    gross_weight = Column(Float)
    tare_weight = Column(Float)
    net_weight = Column(Float)
    product_type = Column(String)  # Corn, soy, wheat
    origin = Column(String)

class ShipLoading(Base):
    """Ship loading operations"""
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    ship_name = Column(String)
    tonnage_loaded = Column(Float)
    product_type = Column(String)
    berth_number = Column(Integer)
    loading_rate = Column(Float)  # tons/hour

class DailyOperations(Base):
    """Daily summary"""
    date = Column(Date)
    trucks_received = Column(Integer)
    ships_loaded = Column(Integer)
    total_tonnage = Column(Float)
    operating_hours = Column(Float)
```

#### 3.2 GBM API Integration
```python
# backend/app/integrations/gbm_api.py

class GBMAPIClient:
    """Integration with GBM Port Operations API"""

    async def fetch_ship_schedule(self):
        """Fetch upcoming ships"""

    async def fetch_berth_status(self):
        """Get real-time berth availability"""

    async def sync_loading_data(self):
        """Sync loading operations"""
```

#### 3.3 Manual Entry UI
- Truck entry form
- Ship loading form
- Daily summary dashboard
- Historical data table

---

### PHASE 4: AI Agent Enhancements (Week 4-5)
**Goal**: Intelligent dashboard creation and failure analysis

#### 4.1 Auto-Dashboard Generator
```python
class AutoDashboardGenerator:
    """Automatically creates dashboards based on asset type"""

    async def generate_dashboard(self, asset_type: str):
        """
        Shiploader → Belt speed, load weight, alarms
        Silo → Level, temperature, moisture
        Conveyor → Speed, load, bearing temp
        Weighbridge → Gross, tare, net weight
        """
```

#### 4.2 Failure Analysis Engine
```python
class FailureAnalyzer:
    """Root cause analysis for equipment failures"""

    async def analyze_failure(self, asset_id: str, failure_time: datetime):
        """
        1. Identify failure event
        2. Collect data before/during/after
        3. Find correlations
        4. Suggest root cause
        5. Recommend actions
        """
```

#### 4.3 Pareto Chart Generator
```python
class ParetoAnalyzer:
    """Engineering tool for failure frequency analysis"""

    async def generate_pareto(self, asset_id: str, days: int):
        """
        1. Count failure types
        2. Sort by frequency
        3. Calculate cumulative %
        4. Identify 80/20 rule
        5. Generate chart
        """
```

---

### PHASE 5: Port Terminal Dashboards (Week 5-6)
**Goal**: Domain-specific dashboards for grain terminal operations

#### 5.1 Shiploader Dashboard
- Real-time belt speed
- Load weight (current & cumulative)
- Loading rate (tons/hour)
- Target tonnage vs actual
- Estimated completion time
- Alarm history

#### 5.2 Silo Dashboard
- Level gauges for all silos
- Temperature monitoring
- Moisture content
- Product type
- Capacity utilization
- Fill/empty trends

#### 5.3 Conveyor System Dashboard
- Belt speeds (all conveyors)
- Load sensors
- Bearing temperatures
- Motor currents
- Alarm states
- Flow diagram

#### 5.4 Operations Summary Dashboard
- Today's trucks received
- Ships loaded this week
- Total tonnage (daily/weekly/monthly)
- Loading efficiency
- Equipment availability
- Downtime analysis

---

## 🚀 Technology Stack

### Backend (Python)
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **asyncua** - OPC-UA client
- **pymodbus** - Modbus TCP
- **python-snap7** - Siemens S7
- **pycomm3** - Rockwell EtherNet/IP
- **psutil** - System monitoring
- **docker-py** - Container monitoring

### Frontend (React)
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Recharts** - Charting library
- **TanStack Query** - Data fetching
- **Tailwind CSS** - Styling

### Infrastructure
- **PostgreSQL** - Relational database
- **InfluxDB** - Time-series database
- **Docker** - Containerization
- **Nginx** - Reverse proxy

---

## 📊 Success Metrics

### Technical Metrics
- **Gateway Uptime**: > 99.5%
- **Data Loss**: < 0.1%
- **Latency**: < 100ms average
- **System CPU**: < 70% average
- **Database Response**: < 50ms

### Operational Metrics
- **Dashboard Load Time**: < 2 seconds
- **Real-time Updates**: < 1 second delay
- **Alert Response**: < 30 seconds
- **Report Generation**: < 5 seconds

### Business Metrics
- **Equipment Downtime**: Reduce by 30%
- **Loading Efficiency**: Improve by 15%
- **Data Accuracy**: > 99%
- **User Adoption**: > 80% of operators

---

## 🔒 Security & Compliance

### Network Security
- VPN access to industrial network
- Firewall rules for gateway communication
- TLS encryption for OPC-UA
- Read-only access to PLCs (no write commands)

### Data Security
- Encrypted database connections
- Role-based access control (RBAC)
- Audit logging for all changes
- Backup encryption

### Industrial Standards
- IEC 62443 - Industrial cybersecurity
- ISA-95 - Enterprise-control integration
- ISO 27001 - Information security

---

## 📅 Implementation Timeline

```
Week 1-2:  Gateway Development (OPC-UA, Modbus, Siemens, Rockwell)
Week 2-3:  System Monitoring (Docker, DB, System metrics)
Week 3-4:  Operational Data (Manual entry + GBM API)
Week 4-5:  AI Agent Enhancements (Auto-dashboards, RCA, Pareto)
Week 5-6:  Port Terminal Dashboards (Shiploader, Silo, Conveyor)
Week 6:    Testing, Documentation, Deployment
```

---

## 🎯 Priority Order

1. **OPC-UA + Modbus Gateway** (CRITICAL) - Most common in grain terminals
2. **System Health Monitoring** (HIGH) - Ensure reliability
3. **Shiploader Dashboard** (HIGH) - Primary operation
4. **Manual Operational Data** (MEDIUM) - Immediate value
5. **Siemens + Rockwell Gateway** (MEDIUM) - Extended compatibility
6. **AI Auto-Dashboards** (MEDIUM) - Productivity boost
7. **Failure Analysis + Pareto** (LOW) - Long-term improvement
8. **GBM API Integration** (LOW) - Nice to have

---

## 📝 Notes

- **Grain Loading Simulator**: Already exists in system - leverage for testing
- **Industrial Network**: Gateway must run on network with PLC access
- **Offline Operation**: All features must work during internet outage
- **Multilingual**: Portuguese primary, English secondary
- **Mobile**: Critical dashboards must work on tablets in field

---

**Document Version**: 1.0
**Created**: November 3, 2025
**Author**: Claude (Autonomous AI Assistant)
**Status**: 🚧 Implementation Ready
