# OptiFlow AI Platform - Technical Deep Dive

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React/TypeScript)              │
│  Dashboard | Simulator | Executive | Analytics | Chat | AI     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                 ┌───────────┴───────────┐
                 │                       │
          ┌──────▼──────┐         ┌─────▼──────┐
          │  REST API   │         │ WebSocket  │
          │  (FastAPI)  │         │  Streaming │
          └──────┬──────┘         └─────┬──────┘
                 │                       │
      ┌──────────┴──────────────────────┴──────────┐
      │                                             │
      │          Backend Services (Python)          │
      │   43+ Specialized Microservice Modules      │
      │                                             │
      │  ┌─ Core: Simulator, AI, Analytics        │
      │  ├─ Data: InfluxDB, Kafka, PostgreSQL     │
      │  ├─ ML: Predictive, Anomaly, RCA          │
      │  └─ Integration: Gateway, OPC-UA, Modbus  │
      │                                             │
      └──────────────────┬─────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
     ┌────▼────┐    ┌───▼────┐   ┌────▼───┐
     │PostgreSQL    │InfluxDB│   │  Kafka │
     │ (Relations)  │(Timeseries) │(Streaming)
     └─────────┘    └────────┘   └────────┘
          │              │              │
     ┌────▼──────────────▼──────────────▼────┐
     │    Redis (Cache & Pub/Sub)             │
     └────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  External Integrations                          │
│  ├─ OpenAI (LLM)                               │
│  ├─ Ollama (Local LLM)                         │
│  ├─ OPC-UA Servers (Industrial Devices)        │
│  ├─ Modbus/MQTT/S7 (Protocols)                 │
│  └─ RabbitMQ (Alternative Queue)               │
└─────────────────────────────────────────────────┘
```

---

## 1. Service Layer Architecture

### 1.1 Core Processing Pipeline

```python
# Data Flow through Services

Input (Device/Simulator)
    ↓
[Tag Service] - Normalize & validate tags
    ↓
[Data Service] - Aggregate & structure data
    ↓
[Analytics Service] - Calculate KPIs & metrics
    ↓
[InfluxDB Service] - Persist time-series via Kafka
    ↓
[Kafka Producer] - Publish to real-time consumers
    ↓
Output (APIs, WebSockets, Reports)
```

### 1.2 Service Interdependencies

**Core Services (Must Have):**
- Database Session (SQLAlchemy)
- Logging Service
- Config Service

**Feature Services (Gracefully Degrade):**
- Kafka Producer/Consumer
- InfluxDB Service
- Autonomous Agent
- AI Service

**Support Services:**
- Asset Health Calculator
- Predictive Maintenance
- Root Cause Analysis
- Report Generator

### 1.3 Service Loading Order (from main.py)

1. **Initialization (Startup)**
   - Database connection with exponential backoff (5 attempts, max 30s)
   - Database health check
   - Autonomous Agent (disabled currently)
   - Kafka Producer initialization
   - Kafka Consumer initialization

2. **Shutdown (Cleanup)**
   - Kafka Consumer graceful stop
   - Kafka Producer cleanup
   - Database connection pool cleanup

---

## 2. Database Architecture

### 2.1 Schema Structure

**User Management:**
```
User
├─ organization_id → Organization
├─ roles
└─ permissions
```

**Asset Hierarchy:**
```
Asset (Tree Structure)
├─ parent_id → Asset (self-referential)
├─ asset_type: enterprise|site|area|unit|equipment|component
├─ children[] → Asset
└─ asset_metadata (JSONB)
```

**Device Management:**
```
Device
├─ site_id → Site
├─ device_type: opcua|modbus|mqtt|s7|ethernetip
├─ tags[] → Tag (1:M)
└─ status: operational|offline|warning|error
```

**Tag System:**
```
Tag
├─ device_id → Device
├─ name, unit, min_value, max_value
├─ tag_type: analog|digital|string
└─ quality: good|uncertain|bad
```

**Extended Tags (PI AF-style):**
```
GatewayTagExtended
├─ gateway_id
├─ tag_type: simple|calculated|attribute
├─ formula (if calculated)
├─ archive_enabled: bool
├─ archive_type: continuous|discrete|eventspecific
└─ formula_variables[] (JSONB)

TagFormula
├─ formula_string
├─ variables: [name, datatype, value]
└─ calculation_interval
```

**Time-Series Data:**
```
PostgreSQL (Historical):
  ├─ AssetHealth
  │  ├─ asset_id
  │  ├─ health_score (0-100)
  │  ├─ status: healthy|warning|critical
  │  └─ calculated_at

  └─ AssetHealthHistory
     ├─ asset_health_id
     ├─ previous_score
     └─ change_timestamp

InfluxDB (Real-time):
  └─ measurement: tag_data
     ├─ tags: tag_id, quality, device_id, site_id
     ├─ fields: value (float)
     └─ time: timestamp
```

### 2.2 Multi-Tenancy Model

```python
# All tables have organization context:
Organization (Root)
    ├─ Sites (One per location)
    │   ├─ Devices (Equipment at site)
    │   │   ├─ Tags (Process variables)
    │   │   └─ Assets (Hierarchy)
    │   └─ Users (Site access)
    ├─ Assets (Root of hierarchy)
    └─ Users (Organization users)
```

**Isolation:**
- All queries filtered by `organization_id`
- User role-based access control
- Data separation at database level

### 2.3 Key Relationships

**One-to-Many:**
- Organization → Sites (1:N)
- Site → Devices (1:N)
- Device → Tags (1:N)
- Asset → ChildAssets (1:N)
- User → Conversations (1:N)

**Many-to-Many:**
- User ↔ Organization (with roles)
- Device ↔ Tag (through Tag association)

---

## 3. Real-Time Data Flow Architecture

### 3.1 Event-Driven Pipeline

**Producer Side (Data Generation):**
```
┌─────────────────┐
│   Simulator     │  (Physics-based, 1000+ tags/sec)
│   Gateway       │  (Protocol adapters, polling-based)
└────────┬────────┘
         │
         ▼
    ┌─────────────────────┐
    │  Tag Service Layer  │
    ├─────────────────────┤
    │ - Normalize tags    │
    │ - Filter duplicates │
    │ - Quality check     │
    └────────┬────────────┘
             │
             ▼
    ┌─────────────────────┐
    │  Kafka Producer     │
    ├─────────────────────┤
    │ Topic: raw_tags     │
    │ Batching: 10ms      │
    │ Compression: LZ4    │
    │ Acks: leader only   │
    └────────┬────────────┘
```

**Consumer Side (Data Persistence):**
```
    ┌──────────────────────┐
    │  Kafka Consumer      │
    ├──────────────────────┤
    │ Group: timeseries... │
    │ Batch size: 100      │
    │ Auto commit: false   │
    └────────┬─────────────┘
             │
             ▼
    ┌──────────────────────────┐
    │  InfluxDB Service        │
    ├──────────────────────────┤
    │ - Batch writes (1000s)   │
    │ - Quality indicators     │
    │ - Context tags           │
    └────────┬─────────────────┘
             │
             ▼
    ┌──────────────────────────┐
    │  InfluxDB (Storage)      │
    │  - High compression      │
    │  - Fast queries          │
    │  - Retention policies    │
    └──────────────────────────┘
```

### 3.2 WebSocket Real-Time Streaming

**Two WebSocket Channels:**

1. **Analytics WebSocket** (`/ws/analytics`)
   - Subscriptions to specific metric streams
   - Update interval: 1-5 seconds
   - Authentication: JWT (TODO: implement)
   - Broadcast: One-to-many fan-out

2. **Tag WebSocket** (`/ws/tags`)
   - Subscription to Kafka topics
   - Real-time tag updates
   - Message compression
   - Backpressure handling

**Connection Management:**
```python
# Current Pattern:
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # Process subscription/command
            # Send updates in loop
    except WebSocketDisconnect:
        # Cleanup
```

### 3.3 Caching Strategy

**Current Implementation:**
- Redis for general caching
- No explicit time-series caching
- Session management

**Opportunities:**
- Cache InfluxDB query results (5-60 minute TTL)
- Cache asset health calculations
- Cache executive dashboard metrics

---

## 4. AI/ML Integration Architecture

### 4.1 Three-Tier LLM Strategy

```
┌─────────────────────────────────────┐
│     User Request (Chat)             │
└────────────┬────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────┐
    │   AIService.generate_response()  │
    └────────────┬────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
    ┌───────────┐   ┌──────────────┐
    │  Ollama   │   │   OpenAI API │
    │ (Fallback)    │  (Primary)   │
    └───────────┘   └──────────────┘
        
    Selection Logic:
    - If USE_OLLAMA=true → Try Ollama first
    - If Ollama fails → Fallback to OpenAI
    - If both fail → Return heuristic response
```

### 4.2 Machine Learning Pipeline

```
Raw Sensor Data
    ↓
┌─────────────────────────────────┐
│  Feature Engineering             │
│  ├─ Rolling statistics (1h)      │
│  ├─ Rate of change              │
│  ├─ Operating hours              │
│  └─ Cycles count                 │
└────────────┬────────────────────┘
             │
             ▼
    ┌─────────────────────────────────┐
    │  Model Selection                │
    │  ├─ RUL Estimation (RULEstimator)
    │  ├─ Failure Prediction (XGBoost) │
    │  ├─ Anomaly Detection (Isolation │
    │  │   Forest / Isolation Forest)  │
    │  └─ Root Cause Analysis (Corr)  │
    └────────────┬────────────────────┘
                 │
                 ▼
        ┌─────────────────────────┐
        │  Training Data          │
        │  ├─ Historical data     │
        │  ├─ Simulated failures  │
        │  └─ Real failures       │
        └─────────────────────────┘
                 │
                 ▼
    ┌─────────────────────────────────┐
    │  Model Registry                 │
    │  ├─ MLModel (database)          │
    │  ├─ Version tracking            │
    │  └─ Performance metrics         │
    └────────────┬────────────────────┘
                 │
                 ▼
        ┌─────────────────────────┐
        │  Inference              │
        │  ├─ Real-time scoring   │
        │  ├─ Batch predictions   │
        │  └─ Explainability (SHAP)
        └─────────────────────────┘
```

### 4.3 Autonomous Agent Loop (Currently Disabled)

```
while agent.is_running:
    ├─ Fetch latest sensor data (last hour)
    │  └─ Query from InfluxDB
    │
    ├─ Calculate metrics
    │  ├─ Asset health scores
    │  ├─ Anomaly detection
    │  ├─ RUL estimates
    │  └─ Alert generation
    │
    ├─ Analyze patterns
    │  ├─ Correlation analysis
    │  ├─ Trend detection
    │  └─ Root cause identification
    │
    ├─ Generate insights
    │  ├─ Anomalies found
    │  ├─ Optimization opportunities
    │  ├─ Maintenance recommendations
    │  └─ Risk assessments
    │
    ├─ Store insights
    │  └─ Database persistence
    │
    └─ Sleep for monitoring_interval (60s)
```

**Why It's Disabled:**
- Session management issue (nested sessions)
- Connection pool exhaustion after N cycles
- Needs architectural refactoring

---

## 5. Gateway & Protocol Architecture

### 5.1 Protocol Adapter Pattern

```
┌──────────────────────────────────┐
│  DeviceManager                   │
│  (Coordinates all devices)       │
└──────────┬───────────────────────┘
           │
    ┌──────┴──────┬─────────┬─────────┬──────────┐
    │             │         │         │          │
    ▼             ▼         ▼         ▼          ▼
 ┌──────┐    ┌────────┐  ┌─────┐  ┌──────┐  ┌──────┐
 │OPC-UA    │Modbus  │ │MQTT │ │S7   │ │EtherNet
 │Adapter   │Adapter │ │Adapter Adapter  /IP
 └──┬───┘    └───┬──┘  └──┬──┘  └──┬──┘  └───┬───┘
    │             │        │       │         │
    └─────────────┼────────┼───────┼─────────┘
                  │
                  ▼
        ┌──────────────────────┐
        │  Protocol Manager    │
        │  (Routing, Config)   │
        └──────────┬───────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
    ┌────────┐          ┌──────────┐
    │ Device │          │Industrial│
    │ Polling│          │Equipment │
    └────────┘          └──────────┘
        │
        ▼
    ┌──────────────┐
    │ Data Buffer  │ (Resilience)
    └──────┬───────┘
           │
           ▼
    ┌──────────────────┐
    │ Backend Client   │
    │ (Data Upload)    │
    └──────┬───────────┘
           │
           ▼
    ┌──────────────────────┐
    │ Backend API          │
    │ (Persistence)        │
    └──────────────────────┘
```

### 5.2 OPC-UA Discovery & Browsing

**Features:**
- Automatic node discovery
- Namespace browsing
- Data type detection
- Read/write capability detection

**Implementation:**
```python
# OPC-UA Adapter includes:
- Connection pooling
- Reconnection logic
- Node subscription management
- Historical data reading
```

### 5.3 Modbus Protocol Support

**Supported Features:**
- RTU (Serial) & TCP modes
- Read Coils, Inputs, Holdings
- Write Single/Multiple Coils
- Timeout handling
- CRC validation (RTU)

**Multi-Register Handling:**
- DWORD (2x 16-bit) ✓
- FLOAT (IEEE 754) ✓
- String types - TODO
- Other types - Not yet

### 5.4 Data Buffering & Resilience

```
Gateway Buffer Management:
─────────────────────────

Incoming Data
    │
    ▼
┌─────────────────────────┐
│ In-Memory Buffer        │
│ - FIFO queue            │
│ - Max size: configurable│
│ - TTL: configurable     │
└────────┬────────────────┘
         │
    ┌────┴────┐
    │          │
    ▼          ▼
[Backend OK] [Backend Down]
    │           │
    │ Upload    │ Store
    │ (sync)    │ (async)
    │           │
    └────┬──────┘
         │
         ▼
    Lost on restart
    (TODO: Persist to SQLite)
```

---

## 6. API Layer Architecture

### 6.1 Endpoint Organization (25+ Routes)

```
/api/v1/
├─ /auth              → Authentication (JWT)
├─ /users             → User management
├─ /organizations     → Organization CRUD
├─ /sites             → Site management
├─ /devices           → Device configuration
├─ /tags              → Tag CRUD
├─ /tag-labels        → Tag categorization
├─ /assets            → Asset hierarchy
├─ /alarms            → Alert management
├─ /timeseries        → Time-series queries
├─ /chat              → Conversational AI
├─ /analytics         → Analytics & queries
├─ /analytics/ws      → WebSocket streaming
├─ /ai                → AI insights & models
├─ /ai-engineering    → Model management
├─ /advanced          → Advanced features
├─ /executive         → Executive dashboard
├─ /gbm               → Grain terminal logistics
├─ /historical        → Historical analysis
├─ /operations        → Port operations
├─ /monitoring        → System health
├─ /extended-tags     → PI AF tags & formulas
├─ /gateway-config    → OPC-UA discovery
└─ /ws/tags          → Real-time tag streaming
```

### 6.2 Authentication & Authorization

**Current Implementation:**
```python
# JWT-based authentication
@app.get("/protected")
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    # Automatic JWT validation
    pass
```

**Features:**
- JWT token generation
- Token refresh
- Role-based access control (RBAC)
- Organization isolation

**Gaps:**
- WebSocket endpoints don't validate JWT
- Some admin endpoints may lack proper checks

### 6.3 Error Handling Pattern

```python
try:
    # Main logic
except SpecificException as e:
    # Log with context
    logger.error(f"Error: {e}", exc_info=True)
    # Return meaningful response
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    # Catch-all
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

**Middleware:**
- Rate limiting (slowapi)
- Request timeout (custom middleware)
- Circuit breaker (custom middleware)
- CORS handling

---

## 7. Monitoring & Observability

### 7.1 Prometheus Metrics

**Metric Categories:**

1. **HTTP Metrics**
   - Requests total (by method, endpoint, status)
   - Request duration (latency histogram)
   - Requests in progress (gauge)

2. **Database Metrics**
   - Connection pool status
   - Query count (by operation type)
   - Query duration

3. **Extended Tags Metrics (PI AF)**
   - Total tags by type & gateway
   - Archived tags count
   - Formula count & executions

4. **Gateway Metrics**
   - Tags per gateway
   - Connection status (1=connected, 0=disconnected)

5. **AI Agent Metrics**
   - Interaction count (by type, success)
   - Response latency

6. **Asset Metrics**
   - Total assets by type
   - Alarms total by priority

### 7.2 Health Checks

**Application Health Endpoint** (`/health`):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "api": "healthy",
    "database": "healthy" or "degraded"
  },
  "warnings": [...],  // Optional
  "db_error": "..."   // Optional error detail
}
```

**Graceful Degradation:**
- App returns 200 even if DB is down
- Some features gracefully disabled
- Load balancers keep routing traffic

### 7.3 Logging Strategy

**Levels:**
- DEBUG: Development, detailed trace
- INFO: Service startup/shutdown, key events
- WARNING: Graceful degradation, retries
- ERROR: Failures, exceptions with context
- CRITICAL: Application can't start

**Format:**
```
2024-11-05 10:30:45,123 - app.services.autonomous_agent - INFO - 🤖 Autonomous Agent started
```

---

## 8. Security Architecture

### 8.1 Authentication Flow

```
User Login
    │
    ▼
┌─────────────────┐
│ Verify Credentials
│ (hashed password)
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│ Generate JWT Token   │
│ - User ID            │
│ - Org ID             │
│ - Roles              │
│ - Expiry: 24h        │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Return to Client     │
│ (Store in localStorage)
└──────────────────────┘

Subsequent Requests:
    │
    ├─ Include JWT in Authorization header
    │
    ▼
┌──────────────────────────┐
│ Validate JWT             │
│ - Signature check        │
│ - Expiry check           │
│ - Role verification      │
└────────┬─────────────────┘
         │
         ▼
    Grant/Deny Access
```

### 8.2 Data Protection

**At Rest:**
- PostgreSQL: No built-in encryption (consider at-rest)
- InfluxDB: No built-in encryption (consider at-rest)
- Redis: Optional AUTH password

**In Transit:**
- HTTPS/TLS recommended
- JWT signed with secret key
- Kafka can use SSL/TLS

**Database:**
- Organization-level isolation
- User role-based filtering
- No plaintext sensitive data (passwords hashed)

### 8.3 Security Gaps

**Current Issues:**
1. WebSocket endpoints lack JWT validation
2. Some admin endpoints may not verify org access
3. No rate limiting on auth endpoints (should have)
4. Sensitive config in environment variables (best practice)

**Recommendations:**
1. Add JWT validation to all WebSocket endpoints
2. Implement audit logging for admin actions
3. Add rate limiting to auth endpoints
4. Use secrets manager (AWS Secrets, HashiCorp Vault)

---

## 9. Performance Optimization Opportunities

### 9.1 Database Query Optimization

**Current Issues:**
- Some time-series queries run on PostgreSQL (slow)
- No query result caching
- N+1 query problems possible

**Opportunities:**
- Migrate time-series queries to InfluxDB (10-100x faster)
- Implement Redis caching (results TTL: 5-60 min)
- Batch queries where possible
- Add database indexes on frequently queried fields

**Expected Impact:**
- Analytics page load: 5s → 1s
- Dashboard refresh: 2s → 500ms
- CPU usage: -30%

### 9.2 Real-Time Streaming Optimization

**Current:**
- WebSocket updates every 1-5 seconds
- No message compression
- All subscribers get all messages

**Improvements:**
- Add delta compression (only changes)
- Implement message filtering per subscriber
- Use binary protocol (protobuf) instead of JSON
- Redis pub/sub for multi-instance deployments

### 9.3 Simulator Physics Optimization

**Current:**
- CPU-bound calculations (DEM physics)
- Runs synchronously in request loop

**Improvements:**
- GPU acceleration (CuPy already in requirements)
- Offload to background task queue (Celery)
- Cache physics constants
- Vectorize numpy operations

**Expected Impact:**
- Simulator throughput: Current → 2-3x increase

### 9.4 Caching Strategy

```
Layer 1: Application Cache
  └─ Function-level caching (functools)
  └─ TTL: 5-30 seconds

Layer 2: Redis Cache
  ├─ Query results: 5-60 min TTL
  ├─ Asset health: 2-5 min TTL
  ├─ Executive dashboard: 5-15 min TTL
  └─ Session data: 24h TTL

Layer 3: Database-level
  ├─ Materialized views (PostgreSQL)
  ├─ InfluxDB retention policies
  └─ Database indexes
```

---

## 10. Scalability Architecture

### 10.1 Horizontal Scaling

**Currently:**
- Single backend instance
- Single simulator instance
- Shared databases

**For Scaling:**
```
Load Balancer (Nginx/AWS ALB)
    │
    ├─ Backend API Instance 1
    ├─ Backend API Instance 2
    ├─ Backend API Instance 3
    └─ Backend API Instance N
    
    All connect to:
    ├─ Shared PostgreSQL
    ├─ Shared InfluxDB
    ├─ Shared Redis
    └─ Shared Kafka

WebSocket Scaling:
    ├─ Redis pub/sub for fan-out
    ├─ Connection pooling
    └─ Sticky sessions (optional)
```

### 10.2 Data Volume Scaling

**Current Capacity:**
- Simulator: 1000-2000 tags/sec
- InfluxDB: Default retention (infinite)
- PostgreSQL: 5-10 years of operational data

**For Scaling:**
1. **InfluxDB:**
   - Enable downsampling (reduce 1s to 1min after 30 days)
   - Implement retention policies (1 year for raw data)
   - Shard data by time range
   - Consider InfluxDB Cloud

2. **PostgreSQL:**
   - Partition tables by date
   - Archive old data to separate schema
   - Implement read replicas
   - Consider managed service (AWS RDS, Google Cloud SQL)

3. **Event Streaming:**
   - Kafka partition strategy by device/site
   - Multiple consumer instances
   - Consider Kafka cloud (Confluent, AWS MSK)

### 10.3 Bottleneck Analysis

**CPU-Bound:**
- Simulator physics calculations
- ML feature engineering
- InfluxDB queries on large datasets

**I/O-Bound:**
- Database queries (PostgreSQL)
- Kafka writes/reads
- WebSocket message distribution

**Memory-Bound:**
- InfluxDB in-memory index
- Redis cache growth
- Kafka broker memory

---

## Conclusion

OptiFlow's architecture is **well-designed for IoT/Industrial applications** with:
- Clean separation of concerns (service layer)
- Event-driven real-time capabilities
- Comprehensive monitoring
- Multi-tenancy support
- Graceful degradation

**Main architectural improvements needed:**
1. Fix autonomous agent session management
2. Implement InfluxDB caching layer
3. Add WebSocket authentication
4. Plan for horizontal scaling strategy

**The platform is architecturally sound for production deployment** with the recommended fixes.
