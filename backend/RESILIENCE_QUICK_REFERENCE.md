# Fault Tolerance Quick Reference Card

## Configuration Values

```python
# Database Connection Pool
DATABASE_POOL_SIZE = 20           # Min connections
DATABASE_MAX_OVERFLOW = 40        # Additional connections
DATABASE_POOL_TIMEOUT = 30        # Seconds to wait for connection
DATABASE_POOL_RECYCLE = 3600      # Recycle after 1 hour
DATABASE_CONNECT_TIMEOUT = 10     # Connection timeout
DATABASE_COMMAND_TIMEOUT = 30     # Query timeout

# Request Timeout
REQUEST_TIMEOUT_SECONDS = 30      # Max request time

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5   # Failures to open circuit
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60   # Seconds before recovery attempt
```

## Quick Usage Examples

### 1. Basic Database Operation (Automatic Protection)
```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

@app.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    # Automatically protected with:
    # - 30s connection timeout
    # - 30s query timeout
    # - Automatic rollback on error
    # - Circuit breaker
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

### 2. Add Extra Protection with Decorator
```python
from app.db.utils import with_db_resilience

@with_db_resilience(timeout=15)  # Custom 15s timeout
async def complex_query(db: AsyncSession):
    # This operation has:
    # - 15s timeout (instead of default 30s)
    # - Circuit breaker protection
    # - Automatic error logging
    result = await db.execute(complex_query)
    return result.all()
```

### 3. Retry on Transient Failures
```python
from app.db.utils import execute_with_retry

result = await execute_with_retry(
    get_user_data,
    db, user_id,
    max_retries=3,
    base_delay=1.0
)
```

### 4. Safe Operation with Default Value
```python
from app.db.utils import safe_db_operation

# Returns [] if query fails, doesn't raise exception
users = await safe_db_operation(
    db,
    lambda db: db.query(User).all(),
    default_value=[]
)
```

### 5. Check Database Health
```python
from app.db.session import check_db_health

if await check_db_health():
    print("Database is healthy")
else:
    print("Database is unavailable")
```

## Error Responses

### 504 Gateway Timeout
Request exceeded 30 seconds:
```json
{
  "detail": "Request processing exceeded timeout of 30 seconds",
  "error": "gateway_timeout",
  "path": "/api/v1/users",
  "method": "GET"
}
```

### 503 Service Unavailable (Circuit Breaker Open)
```json
{
  "detail": "Circuit breaker is OPEN. Service unavailable for 60s.",
  "error": "service_unavailable",
  "circuit_breaker": "open",
  "message": "Service is temporarily unavailable. Please try again later."
}
```

### Health Check Response (Database Down)
```json
{
  "status": "healthy",
  "services": {
    "api": "healthy",
    "database": "degraded"
  },
  "warnings": [
    "Database connection degraded - some features may be limited"
  ]
}
```

## Middleware Order

```
HTTP Request
    ↓
TimeoutMiddleware (30s timeout)
    ↓
CircuitBreakerMiddleware (fail fast when degraded)
    ↓
Your API Endpoint
    ↓
get_db() dependency (connection pool + timeouts)
    ↓
PostgreSQL
```

## Circuit Breaker States

| State | Behavior | When |
|-------|----------|------|
| CLOSED | Normal operation | Default state |
| OPEN | Reject all requests (fail fast) | After 5 failures |
| HALF_OPEN | Allow test requests | After 60s recovery timeout |

**Transitions:**
- CLOSED → OPEN: After 5 consecutive failures
- OPEN → HALF_OPEN: After 60 seconds
- HALF_OPEN → CLOSED: After 2 successful requests
- HALF_OPEN → OPEN: If test request fails

## Testing Commands

```bash
# Test request timeout (should return 504 after 30s)
curl http://localhost:8000/api/v1/slow-endpoint

# Test circuit breaker (stop database first)
docker-compose stop postgres
for i in {1..6}; do curl http://localhost:8000/api/v1/users; done

# Test health check
curl http://localhost:8000/health

# Test with database down
docker-compose stop postgres && curl http://localhost:8000/health

# Check circuit breaker state
curl http://localhost:8000/api/v1/circuit-breaker/status
```

## Monitoring

### Key Metrics
- `db_connections_active` - Current active DB connections
- `http_request_duration_seconds` - Request latency
- `http_requests_total{status="504"}` - Timeout errors
- `http_requests_total{status="503"}` - Circuit breaker errors

### Prometheus Queries
```promql
# Request timeout rate
rate(http_requests_total{status="504"}[5m])

# Circuit breaker open events
changes(circuit_breaker_state{state="open"}[1h])

# Average request duration
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Database connection pool utilization
db_connections_active / 20 * 100  # Percentage
```

## Troubleshooting

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Many 504 errors | Slow queries or database | Optimize queries, increase timeout |
| 503 errors | Database down or too many failures | Check database health, review logs |
| Connection pool exhausted | Too many concurrent requests | Increase pool size or reduce load |
| Frequent circuit opening | Database instability | Investigate database issues |

## Best Practices

1. ✅ **Use get_db() dependency** - Automatic protection
2. ✅ **Add @with_db_resilience** for critical operations
3. ✅ **Implement caching** for frequently accessed data
4. ✅ **Use safe_db_operation** for non-critical data
5. ✅ **Monitor circuit breaker state** in production
6. ✅ **Set up alerts** for 504/503 errors
7. ✅ **Test failure scenarios** regularly
8. ✅ **Keep connection pool size** appropriate for load

## Don't Do This

❌ Don't bypass get_db() dependency
❌ Don't disable timeouts in production
❌ Don't ignore circuit breaker open state
❌ Don't set timeouts too high (>60s)
❌ Don't leak database connections
❌ Don't ignore health check warnings

## Documentation

- **Full Guide:** `backend/FAULT_TOLERANCE_GUIDE.md`
- **Implementation Summary:** `backend/FAULT_TOLERANCE_IMPLEMENTATION_SUMMARY.md`
- **This Quick Ref:** `backend/RESILIENCE_QUICK_REFERENCE.md`

---
**Last Updated:** 2025-11-05
**Version:** 1.0.0
