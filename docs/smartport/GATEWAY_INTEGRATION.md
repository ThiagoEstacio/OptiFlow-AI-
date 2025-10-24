# SmartPort - API Gateway Integration Plan

## Current Architecture
```
Frontend (React) → Backend (FastAPI) → Database (PostgreSQL)
                                     → InfluxDB (time series)
```

## Recommended Architecture with Gateway
```
Frontend → API Gateway → SmartPort Backend → PostgreSQL
                      → WebSocket Gateway → InfluxDB
                      → Auth Service
                      → Rate Limiter
                      → Cache (Redis)
```

## 1. API Gateway Options

### Option A: Kong (Recommended for Production)
```yaml
# docker-compose.gateway.yml
version: '3.8'

services:
  kong-database:
    image: postgres:14
    environment:
      POSTGRES_DB: kong
      POSTGRES_USER: kong
      POSTGRES_PASSWORD: kong

  kong-migrations:
    image: kong:3.4
    command: kong migrations bootstrap
    depends_on:
      - kong-database

  kong:
    image: kong:3.4
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: kong-database
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_ADMIN_ERROR_LOG: /dev/stderr
      KONG_ADMIN_LISTEN: 0.0.0.0:8001
    ports:
      - "8000:8000"  # Proxy
      - "8001:8001"  # Admin API
    depends_on:
      - kong-migrations

  # SmartPort Backend
  smartport-api:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/smartport
    ports:
      - "8080:8000"
```

### Option B: Traefik (Recommended for Kubernetes)
```yaml
# traefik.yml
entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

providers:
  docker:
    exposedByDefault: false

api:
  dashboard: true
  insecure: true

# docker-compose.traefik.yml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"  # Dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  smartport-api:
    build: ./backend
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.smartport.rule=Host(`api.smartport.local`)"
      - "traefik.http.routers.smartport.entrypoints=websecure"
      - "traefik.http.services.smartport.loadbalancer.server.port=8000"
```

### Option C: Nginx (Simple, for small deployments)
```nginx
# nginx.conf
upstream smartport_backend {
    least_conn;
    server backend1:8000 max_fails=3 fail_timeout=30s;
    server backend2:8000 max_fails=3 fail_timeout=30s;
    server backend3:8000 max_fails=3 fail_timeout=30s;
}

upstream smartport_websocket {
    ip_hash;  # Sticky sessions for WebSocket
    server backend1:8000;
    server backend2:8000;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=ws_limit:10m rate=5r/s;

server {
    listen 80;
    server_name api.smartport.com;

    # API endpoints
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://smartport_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket
    location /ws/ {
        limit_req zone=ws_limit burst=5 nodelay;

        proxy_pass http://smartport_websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # WebSocket specific timeouts
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }

    # Health check
    location /health {
        access_log off;
        proxy_pass http://smartport_backend/api/v1/health;
    }
}
```

## 2. Features to Add

### A. Rate Limiting
```python
# backend/app/middleware/rate_limit.py
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# In main.py
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Usage in endpoints
@router.get("/berths")
@limiter.limit("100/minute")
async def list_berths(request: Request, ...):
    ...
```

### B. CORS Configuration (Production)
```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # CORS
    CORS_ORIGINS: list[str] = [
        "https://smartport.example.com",
        "https://app.smartport.example.com"
    ]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: list[str] = ["*"]

# main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)
```

### C. Health Check Endpoint
```python
# backend/app/api/v1/endpoints/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "smartport",
        "version": "1.0.0"
    }

@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check - includes DB connection"""
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "database": "disconnected",
            "error": str(e)
        }, 503

@router.get("/health/live")
async def liveness_check():
    """Liveness check - minimal"""
    return {"status": "alive"}
```

## 3. Security Enhancements

### API Key Authentication (for external integrations)
```python
# backend/app/core/security.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """Verify API key for external integrations"""
    if api_key not in settings.VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# Usage
@router.get("/external/berths")
async def external_berths(api_key: str = Depends(verify_api_key)):
    ...
```

## 4. Recommended Integration Pattern

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         API Gateway (Kong)          │
│  ┌──────────────────────────────┐   │
│  │ Rate Limiting (100 req/min)  │   │
│  │ Authentication (JWT)         │   │
│  │ CORS                         │   │
│  │ Request Logging              │   │
│  │ Response Caching (Redis)     │   │
│  └──────────────────────────────┘   │
└────┬────────────────────────────┬───┘
     │                            │
     ▼                            ▼
┌─────────────┐           ┌─────────────┐
│  Backend 1  │           │  Backend 2  │
│  (FastAPI)  │           │  (FastAPI)  │
└──────┬──────┘           └──────┬──────┘
       │                         │
       └────────┬────────────────┘
                ▼
       ┌────────────────┐
       │   PostgreSQL   │
       │   + InfluxDB   │
       └────────────────┘
```

## 5. Implementation Priority

1. **Week 1:** Health checks + Basic Nginx reverse proxy
2. **Week 2:** Rate limiting + CORS production config
3. **Week 3:** Kong/Traefik setup + Load balancing
4. **Week 4:** Monitoring + Metrics + Alerting

## 6. External Integration APIs

For partners/third-party systems:
```python
# Webhook for vessel arrival
POST /api/v1/webhooks/vessel-arrival
X-API-Key: external-system-key
{
  "vessel_imo": "IMO1234567",
  "eta": "2024-01-25T10:00:00Z"
}

# Query API for external systems
GET /api/v1/external/berths/availability
X-API-Key: external-system-key
?date=2024-01-25&vessel_loa=350
```
