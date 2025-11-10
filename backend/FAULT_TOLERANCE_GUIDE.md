# Fault Tolerance & Resilience Guide

## Overview

The OptiFlow backend now includes comprehensive fault-tolerant mechanisms to prevent database timeout issues and improve system resilience. The application is designed to gracefully handle database connection issues, slow queries, and cascading failures.

## Implemented Mechanisms

### 1. Connection Pool Configuration

**File:** `backend/app/db/session.py`

**Features:**
- **Increased Pool Size:** 20 min connections (up from 10) for better concurrency
- **Overflow Handling:** 40 additional connections (up from 20) for burst traffic
- **Connection Timeout:** 30 seconds to acquire a connection from pool
- **Connection Recycling:** Connections recycled after 1 hour to prevent stale connections
- **Pre-ping:** Test connections before use to detect dead connections
- **Query Timeout:** 30 seconds maximum for query execution

**Configuration (in `backend/app/core/config.py`):**
```python
DATABASE_POOL_SIZE = 20              # Min connections to maintain
DATABASE_MAX_OVERFLOW = 40           # Additional connections allowed
DATABASE_POOL_TIMEOUT = 30           # Wait time for connection (seconds)
DATABASE_POOL_RECYCLE = 3600         # Recycle connections after 1 hour
DATABASE_POOL_PRE_PING = True        # Test connections before use
DATABASE_CONNECT_TIMEOUT = 10        # Connection timeout (seconds)
DATABASE_COMMAND_TIMEOUT = 30        # Query execution timeout (seconds)
```

### 2. Request Timeout Middleware

**File:** `backend/app/middleware/timeout.py`

**Features:**
- Prevents requests from hanging indefinitely
- Returns 504 Gateway Timeout after configurable timeout
- Skips health checks, metrics, and WebSocket connections
- Provides detailed error responses

**Configuration:**
```python
REQUEST_TIMEOUT_SECONDS = 30  # Maximum request processing time
```

**Behavior:**
- If a request exceeds 30 seconds, it's cancelled
- Client receives 504 Gateway Timeout with details
- Prevents resource exhaustion from long-running requests

### 3. Circuit Breaker Pattern

**File:** `backend/app/middleware/circuit_breaker.py`

**Features:**
- **Three States:**
  - **CLOSED:** Normal operation, all requests pass through
  - **OPEN:** Too many failures, reject requests immediately (fail fast)
  - **HALF_OPEN:** Testing recovery, allow limited requests

- **Automatic Recovery:** After timeout, circuit transitions to HALF_OPEN to test if service recovered

**Configuration:**
```python
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5   # Failures before opening circuit
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60   # Seconds before trying to recover
```

**Behavior:**
1. After 5 consecutive failures, circuit opens
2. For 60 seconds, requests fail fast (no database calls)
3. After 60 seconds, circuit goes to HALF_OPEN
4. If next 2 requests succeed, circuit closes
5. If request fails in HALF_OPEN, circuit reopens

### 4. Exponential Backoff Retry Logic

**File:** `backend/app/main.py` (startup) and `backend/app/db/session.py` (operations)

**Features:**
- Automatic retry with increasing delays
- Prevents thundering herd problem
- Configurable max retries and delays

**Startup Retry Schedule:**
- Attempt 1: Immediate
- Attempt 2: 2 seconds delay
- Attempt 3: 4 seconds delay
- Attempt 4: 8 seconds delay
- Attempt 5: 16 seconds delay (max 30s cap)

### 5. Database Session Resilience

**File:** `backend/app/db/session.py`

**Features:**
- Session acquisition timeout protection
- Commit timeout protection
- Automatic rollback on errors
- Guaranteed session cleanup
- Health check function for monitoring

**Key Functions:**

```python
# Get database session with timeout protection
async def get_db() -> AsyncSession:
    # Automatically handles timeouts and errors
    # Guaranteed cleanup in finally block

# Check database health
async def check_db_health() -> bool:
    # Returns True if database is accessible
    # Used by health check endpoint
```

### 6. Graceful Degradation

**File:** `backend/app/main.py` (health check endpoint)

**Features:**
- Application remains "healthy" even if database is down
- Health endpoint returns detailed service status
- Load balancers keep routing traffic
- Application can serve cached/static content

**Health Check Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "services": {
    "api": "healthy",
    "database": "degraded"
  },
  "warnings": [
    "Database connection degraded - some features may be limited"
  ]
}
```

### 7. Database Utility Functions

**File:** `backend/app/db/utils.py`

**Utilities Provided:**

```python
# Decorator for database operations with resilience
@with_db_resilience(timeout=10)
async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# Execute with automatic retry
result = await execute_with_retry(
    some_db_function,
    arg1, arg2,
    max_retries=3
)

# Safe operation with default value
result = await safe_db_operation(
    db,
    lambda db: db.query(User).all(),
    default_value=[]
)
```

## Architecture Diagram

```
┌─────────────────┐
│   HTTP Request  │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ Timeout Middleware  │ ← 30s request timeout
│  (504 if exceeded)  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│Circuit Breaker      │ ← Fail fast when degraded
│    Middleware       │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   API Endpoint      │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Database Session   │ ← Connection pool with timeouts
│  get_db() + timeout │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   PostgreSQL Pool   │ ← 20 min, 40 overflow
│ (with pre-ping)     │   1hr recycle, 30s timeout
└─────────────────────┘
```

## Error Handling Flow

1. **Request arrives** → Timeout middleware starts timer
2. **Acquire DB session** → 30s timeout, circuit breaker check
3. **Execute query** → 30s command timeout
4. **Commit transaction** → 30s timeout
5. **Return response** → Must complete within 30s total

**If any step fails:**
- Automatic rollback
- Circuit breaker tracks failure
- Retry with exponential backoff (where applicable)
- Return appropriate error response

## Monitoring

### Key Metrics to Monitor

1. **Database Connection Pool:**
   - Active connections (`db_connections_active`)
   - Pool checkout time
   - Connection failures

2. **Request Timeouts:**
   - 504 Gateway Timeout responses
   - Average request duration

3. **Circuit Breaker State:**
   - State transitions (CLOSED → OPEN → HALF_OPEN)
   - Failure count
   - Recovery attempts

4. **Health Check Status:**
   - API health: always "healthy" if running
   - Database health: "healthy" or "degraded"

### Prometheus Metrics

Available at `/metrics` endpoint:
- `http_request_duration_seconds` - Request latency
- `db_connections_active` - Active DB connections
- `db_query_duration_seconds` - Query execution time

## Best Practices

### 1. Use Database Utilities

```python
from app.db.utils import with_db_resilience

@with_db_resilience(timeout=15)
async def get_user_with_profile(db: AsyncSession, user_id: int):
    # This operation is protected by circuit breaker and timeout
    result = await db.execute(
        select(User).options(joinedload(User.profile))
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

### 2. Handle TimeoutError

```python
from fastapi import HTTPException

try:
    user = await get_user(db, user_id)
except TimeoutError:
    raise HTTPException(
        status_code=504,
        detail="Database operation timed out"
    )
```

### 3. Implement Graceful Degradation

```python
@app.get("/users/{user_id}")
async def get_user_endpoint(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        user = await get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except TimeoutError:
        # Return cached data if available
        cached_user = await get_from_cache(user_id)
        if cached_user:
            return {"user": cached_user, "source": "cache", "warning": "live data unavailable"}
        raise HTTPException(status_code=504, detail="Service temporarily unavailable")
```

### 4. Use Safe Operations for Non-Critical Data

```python
from app.db.utils import safe_db_operation

# Won't raise exception if query fails, returns empty list
recent_users = await safe_db_operation(
    db,
    lambda db: db.query(User).order_by(User.created_at.desc()).limit(10).all(),
    default_value=[]
)
```

## Configuration Tuning

### For High-Traffic Environments

```python
# Increase pool size
DATABASE_POOL_SIZE = 50
DATABASE_MAX_OVERFLOW = 100

# Reduce timeout for faster failure detection
REQUEST_TIMEOUT_SECONDS = 15
DATABASE_COMMAND_TIMEOUT = 15
```

### For Low-Latency Requirements

```python
# Tighter timeouts
REQUEST_TIMEOUT_SECONDS = 10
DATABASE_COMMAND_TIMEOUT = 10

# More aggressive circuit breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 3
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 30
```

### For Unstable Networks

```python
# More retries with longer delays
# (Configure in startup logic)
max_retries = 10
base_delay = 5
max_delay = 60
```

## Testing Fault Tolerance

### 1. Test Database Timeout

```bash
# Start application
python -m app.main

# Simulate slow query (in PostgreSQL)
SELECT pg_sleep(60);  -- Will timeout after 30s
```

### 2. Test Circuit Breaker

```bash
# Stop database
docker-compose stop postgres

# Make 5 requests - circuit opens
curl http://localhost:8000/api/v1/users

# Next requests fail fast (no database calls)
curl http://localhost:8000/api/v1/users
# Returns: {"detail": "Circuit breaker is OPEN..."}
```

### 3. Test Request Timeout

```bash
# Make request that takes > 30 seconds
# Should receive 504 Gateway Timeout
```

### 4. Test Health Check

```bash
# With database running
curl http://localhost:8000/health
# Returns: {"status": "healthy", "services": {"database": "healthy"}}

# With database stopped
curl http://localhost:8000/health
# Returns: {"status": "healthy", "services": {"database": "degraded"}}
```

## Troubleshooting

### Issue: Frequent Circuit Breaker Openings

**Cause:** Database connection issues or slow queries

**Solution:**
1. Check database performance and connections
2. Increase `CIRCUIT_BREAKER_FAILURE_THRESHOLD`
3. Optimize slow queries
4. Increase connection pool size

### Issue: Many 504 Gateway Timeout Errors

**Cause:** Requests taking longer than configured timeout

**Solution:**
1. Increase `REQUEST_TIMEOUT_SECONDS` (if appropriate)
2. Optimize slow endpoints
3. Add caching for expensive operations
4. Consider async processing for long operations

### Issue: Connection Pool Exhaustion

**Cause:** Too many concurrent requests, leaked connections

**Solution:**
1. Increase `DATABASE_POOL_SIZE` and `DATABASE_MAX_OVERFLOW`
2. Check for connection leaks (ensure `get_db()` is used properly)
3. Reduce `DATABASE_POOL_TIMEOUT` to fail faster
4. Monitor `db_connections_active` metric

### Issue: Startup Failures

**Cause:** Database not ready during startup

**Solution:**
- Retry logic already implemented with exponential backoff
- Ensure database is accessible
- Check network connectivity
- Verify DATABASE_URL configuration

## Summary

The OptiFlow backend now implements multiple layers of fault tolerance:

1. ✅ **Connection Pool** - Proper sizing, timeouts, recycling
2. ✅ **Request Timeout** - Prevents indefinite hangs
3. ✅ **Circuit Breaker** - Prevents cascading failures
4. ✅ **Exponential Backoff** - Smart retry logic
5. ✅ **Graceful Degradation** - Continue operating during issues
6. ✅ **Health Checks** - Monitor service status
7. ✅ **Utility Functions** - Easy-to-use resilience patterns

These mechanisms work together to ensure the application remains responsive and available even when the database is experiencing issues.
