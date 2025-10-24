# SmartPort - Database Optimization Guide

## Current Database Schema

```sql
-- IMPLEMENTED ✅
CREATE TABLE berths (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(20) NOT NULL UNIQUE,
    berth_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    max_loa FLOAT NOT NULL,
    max_beam FLOAT NOT NULL,
    max_draft FLOAT NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    current_vessel_id UUID REFERENCES vessels(id),
    occupation_start TIMESTAMP WITH TIME ZONE,
    estimated_departure TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_berths_name ON berths(name);
CREATE INDEX ix_berths_berth_type ON berths(berth_type);
CREATE INDEX ix_berths_status ON berths(status);

CREATE TABLE vessels (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    imo VARCHAR(20) NOT NULL UNIQUE,
    vessel_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    loa FLOAT NOT NULL,
    beam FLOAT NOT NULL,
    draft FLOAT NOT NULL,
    eta TIMESTAMP WITH TIME ZONE,
    ata TIMESTAMP WITH TIME ZONE,
    etd TIMESTAMP WITH TIME ZONE,
    atd TIMESTAMP WITH TIME ZONE,
    last_latitude FLOAT,
    last_longitude FLOAT,
    last_position_update TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_vessels_name ON vessels(name);
CREATE INDEX ix_vessels_imo ON vessels(imo);
CREATE INDEX ix_vessels_status ON vessels(status);
CREATE INDEX ix_vessels_eta ON vessels(eta);

CREATE TABLE port_operations (
    id UUID PRIMARY KEY,
    vessel_id UUID NOT NULL REFERENCES vessels(id),
    berth_id UUID NOT NULL REFERENCES berths(id),
    operation_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    containers_planned INTEGER,
    containers_completed INTEGER DEFAULT 0,
    tonnage_planned FLOAT,
    tonnage_completed FLOAT DEFAULT 0,
    scheduled_start TIMESTAMP WITH TIME ZONE NOT NULL,
    actual_start TIMESTAMP WITH TIME ZONE,
    estimated_end TIMESTAMP WITH TIME ZONE NOT NULL,
    actual_end TIMESTAMP WITH TIME ZONE,
    efficiency_percentage FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_port_operations_vessel_id ON port_operations(vessel_id);
CREATE INDEX ix_port_operations_berth_id ON port_operations(berth_id);
CREATE INDEX ix_port_operations_status ON port_operations(status);
CREATE INDEX ix_port_operations_scheduled_start ON port_operations(scheduled_start);
```

## Missing Optimizations ❌

### 1. Composite Indexes (MISSING)
```sql
-- Add composite indexes for common queries
CREATE INDEX idx_berths_status_type ON berths(status, berth_type) WHERE is_active = true;
CREATE INDEX idx_berths_available_capacity ON berths(status, max_loa, max_draft) WHERE status = 'available';

CREATE INDEX idx_vessels_status_eta ON vessels(status, eta) WHERE eta IS NOT NULL;
CREATE INDEX idx_vessels_type_status ON vessels(vessel_type, status);

CREATE INDEX idx_operations_status_scheduled ON port_operations(status, scheduled_start);
CREATE INDEX idx_operations_vessel_berth ON port_operations(vessel_id, berth_id);
CREATE INDEX idx_operations_active ON port_operations(status, actual_start) WHERE status IN ('in_progress', 'scheduled');
```

### 2. Partitioning (MISSING - for large scale)
```sql
-- Partition port_operations by month (for history)
CREATE TABLE port_operations (
    -- same columns as before
) PARTITION BY RANGE (scheduled_start);

-- Create partitions
CREATE TABLE port_operations_2024_01 PARTITION OF port_operations
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE port_operations_2024_02 PARTITION OF port_operations
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Automatic partition creation with pg_partman
CREATE EXTENSION IF NOT EXISTS pg_partman;
```

### 3. Full-Text Search (MISSING)
```sql
-- Add full-text search for vessel names
ALTER TABLE vessels ADD COLUMN search_vector tsvector;

CREATE INDEX idx_vessels_search ON vessels USING GIN(search_vector);

-- Update function
CREATE FUNCTION vessels_search_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.imo, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.flag, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER vessels_search_trigger
BEFORE INSERT OR UPDATE ON vessels
FOR EACH ROW EXECUTE FUNCTION vessels_search_update();

-- Usage
SELECT * FROM vessels WHERE search_vector @@ to_tsquery('maersk & container');
```

### 4. Materialized Views for KPIs (MISSING)
```sql
-- Pre-calculate expensive KPIs
CREATE MATERIALIZED VIEW port_kpis_hourly AS
SELECT
    date_trunc('hour', NOW()) as hour,
    COUNT(DISTINCT b.id) as total_berths,
    COUNT(DISTINCT b.id) FILTER (WHERE b.status = 'available') as available_berths,
    COUNT(DISTINCT b.id) FILTER (WHERE b.status = 'occupied') as occupied_berths,
    COUNT(DISTINCT v.id) as total_vessels,
    COUNT(DISTINCT v.id) FILTER (WHERE v.status IN ('berthed', 'loading', 'unloading')) as berthed_vessels,
    COUNT(DISTINCT po.id) FILTER (WHERE po.status = 'in_progress') as active_operations,
    AVG(EXTRACT(EPOCH FROM (po.actual_end - po.actual_start))/3600) as avg_operation_hours
FROM berths b
CROSS JOIN vessels v
CROSS JOIN port_operations po
WHERE b.is_active = true;

-- Create index
CREATE UNIQUE INDEX ON port_kpis_hourly(hour);

-- Refresh every hour (cron job or pg_cron)
CREATE EXTENSION IF NOT EXISTS pg_cron;
SELECT cron.schedule('refresh-kpis', '0 * * * *',
    'REFRESH MATERIALIZED VIEW CONCURRENTLY port_kpis_hourly');
```

### 5. Time Series Data (MISSING - use InfluxDB)
```python
# backend/app/services/influxdb_service.py
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class InfluxDBService:
    def __init__(self):
        self.client = InfluxDBClient(
            url="http://influxdb:8086",
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()

    async def write_vessel_position(self, vessel_id: str, lat: float, lon: float, speed: float):
        """Write vessel position to time series"""
        point = Point("vessel_position") \
            .tag("vessel_id", vessel_id) \
            .field("latitude", lat) \
            .field("longitude", lon) \
            .field("speed", speed) \
            .time(datetime.utcnow())

        self.write_api.write(bucket="smartport", record=point)

    async def write_operation_metrics(self, operation_id: str, containers: int, efficiency: float):
        """Write operation metrics"""
        point = Point("operation_metrics") \
            .tag("operation_id", operation_id) \
            .field("containers_completed", containers) \
            .field("efficiency", efficiency) \
            .time(datetime.utcnow())

        self.write_api.write(bucket="smartport", record=point)

    async def get_vessel_trajectory(self, vessel_id: str, hours: int = 24):
        """Get vessel trajectory for last N hours"""
        query = f'''
        from(bucket: "smartport")
            |> range(start: -{hours}h)
            |> filter(fn: (r) => r._measurement == "vessel_position")
            |> filter(fn: (r) => r.vessel_id == "{vessel_id}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''

        result = self.query_api.query(query=query)
        return [
            {
                "time": record.get_time(),
                "latitude": record["latitude"],
                "longitude": record["longitude"],
                "speed": record["speed"]
            }
            for table in result
            for record in table.records
        ]
```

### 6. Database Caching with Redis (MISSING)
```python
# backend/app/services/cache_service.py
import redis.asyncio as redis
import json
from typing import Optional, Any

class CacheService:
    def __init__(self):
        self.redis = redis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True
        )

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set cached value with TTL"""
        await self.redis.setex(key, ttl, json.dumps(value))

    async def delete(self, key: str):
        """Delete cached value"""
        await self.redis.delete(key)

    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

# Usage in endpoints
@router.get("/berths")
async def list_berths(cache: CacheService = Depends(get_cache)):
    cache_key = "berths:list:all"

    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Query database
    berths = await db.query(Berth).all()

    # Cache for 5 minutes
    await cache.set(cache_key, berths, ttl=300)

    return berths
```

### 7. Connection Pooling Optimization
```python
# backend/app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    # Connection pool settings
    pool_size=20,           # Number of connections to keep open
    max_overflow=10,        # Max connections beyond pool_size
    pool_timeout=30,        # Seconds to wait for connection
    pool_recycle=3600,      # Recycle connections after 1 hour
    pool_pre_ping=True,     # Verify connections before using
)

SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

### 8. Soft Delete Pattern (PARTIALLY IMPLEMENTED)
```python
# backend/app/models/base.py
from sqlalchemy import Column, Boolean, DateTime
from datetime import datetime

class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String(100), nullable=True)

    def soft_delete(self, user: str):
        """Mark as deleted"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = user

# Usage
class Berth(Base, SoftDeleteMixin):
    ...

# Query only non-deleted
query = select(Berth).where(Berth.is_deleted == False)
```

### 9. Audit Trail (MISSING)
```sql
-- Audit table for tracking changes
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(10) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_changed_at ON audit_log(changed_at);

-- Trigger function
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log(table_name, record_id, action, new_values, changed_by)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', row_to_json(NEW), current_user);
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log(table_name, record_id, action, old_values, new_values, changed_by)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', row_to_json(OLD), row_to_json(NEW), current_user);
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log(table_name, record_id, action, old_values, changed_by)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', row_to_json(OLD), current_user);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables
CREATE TRIGGER berths_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON berths
FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER vessels_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON vessels
FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
```

### 10. Backup Strategy (MISSING)
```bash
# backup_smartport.sh
#!/bin/bash

# PostgreSQL backup
pg_dump -h localhost -U postgres smartport | gzip > /backups/smartport_$(date +%Y%m%d_%H%M%S).sql.gz

# InfluxDB backup
influx backup /backups/influxdb_$(date +%Y%m%d) -t $INFLUX_TOKEN

# Retention: Keep last 30 days
find /backups -name "smartport_*.sql.gz" -mtime +30 -delete
find /backups -name "influxdb_*" -mtime +30 -delete

# Upload to S3
aws s3 sync /backups s3://smartport-backups/
```

## Implementation Priority

1. **Urgent (Week 1):**
   - Composite indexes
   - Connection pooling optimization
   - Redis caching

2. **Important (Week 2):**
   - InfluxDB integration for time series
   - Materialized views for KPIs
   - Full-text search

3. **Nice to have (Week 3-4):**
   - Table partitioning
   - Audit trail
   - Backup automation

## Performance Benchmarks

After optimization, target metrics:
- Berth list query: < 50ms
- KPI dashboard: < 100ms (with cache)
- Vessel search: < 30ms (with full-text)
- Operation create: < 200ms
- WebSocket message: < 10ms
