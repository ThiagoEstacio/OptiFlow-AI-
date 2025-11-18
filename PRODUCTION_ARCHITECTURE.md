# OptiFlow AI - Arquitetura de Produção

## 🎯 Objetivo
Garantir operação **ininterrupta 24/7** com resiliência, observabilidade e recuperação automática.

---

## 1. Princípios de Design

### 1.1 Resiliência
- **Circuit Breakers**: Falhas isoladas não cascateiam
- **Timeouts**: Nenhuma operação infinita
- **Retries**: Tentativas com backoff exponencial
- **Fallbacks**: Sempre há um plano B
- **Graceful Degradation**: Sistema funciona parcialmente se componente falha

### 1.2 Observabilidade
- **Logs estruturados**: JSON com correlation_id
- **Métricas**: RED (Rate, Errors, Duration)
- **Traces**: Request end-to-end tracking
- **Alertas**: Proativos, não reativos

### 1.3 Deployment Seguro
- **Blue-Green**: Zero downtime
- **Rollback automático**: Detecta falhas e reverte
- **Health checks**: Readiness e liveness probes
- **Resource limits**: OOMKiller não surpreende

---

## 2. Arquitetura de Serviços

```
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer (Nginx)                   │
│                    Rate Limit: 1000 req/min                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   Backend 1      Backend 2      Backend 3
   (Active)       (Standby)      (Standby)
        │
        ├── Health: /health (readiness + liveness)
        ├── Metrics: /metrics (Prometheus)
        └── Graceful Shutdown: 30s grace period
        │
        ├─────► Ollama (GPU)
        │       └── Circuit Breaker: 3 falhas = 60s pause
        │       └── Timeout: 30s
        │       └── Fallback: Rule-based analysis
        │
        ├─────► InfluxDB
        │       └── Connection Pool: 10 conexões
        │       └── Timeout: 10s
        │       └── Query semaphore: max 10 concurrent
        │
        ├─────► PostgreSQL
        │       └── Connection Pool: 20 conexões
        │       └── Timeout: 5s
        │       └── Read replicas para analytics
        │
        └─────► Redis
                └── Connection Pool: 50 conexões
                └── TTL: L1(5min) L2(1h)
                └── Fallback: In-memory cache
```

---

## 3. Proteções Implementadas

### 3.1 Rate Limiting (Prioridade ALTA)

#### Global
```python
# Limite por IP
@limiter.limit("100/minute")

# Limite total do sistema
@limiter.limit("1000/minute")
```

#### Endpoint Chat (Mais Crítico)
```python
@router.post("/chat")
@limiter.limit("10/minute")  # Previne abuso de LLM
async def chat_endpoint(...):
    ...
```

#### InfluxDB Queries
```python
_influx_query_semaphore = asyncio.Semaphore(10)  # ✅ JÁ IMPLEMENTADO
_influx_query_timeout = 30  # ✅ JÁ IMPLEMENTADO
```

### 3.2 Circuit Breaker Pattern

```python
# backend/app/core/circuit_breaker.py
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.state = CircuitState.CLOSED
        self.opened_at = None
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.opened_at > timedelta(seconds=self.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = datetime.now()
```

**Uso:**
```python
# backend/app/services/ai_agent.py
ollama_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

async def call_ollama_with_breaker(...):
    try:
        return ollama_breaker.call(call_ollama, messages, max_iterations)
    except Exception:
        logger.warning("Ollama circuit breaker OPEN, using fallback")
        return await fallback_analysis(request)
```

### 3.3 Timeout e Retry Strategy

```python
# backend/app/core/retry.py
import asyncio
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1, max_delay=10):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(f"Retry {attempt+1}/{max_retries} after {delay}s: {e}")
                    await asyncio.sleep(delay)
        return wrapper
    return decorator
```

**Uso:**
```python
@retry_with_backoff(max_retries=3, base_delay=2)
async def query_influxdb(query: str):
    async with asyncio.timeout(10):  # Timeout 10s
        return await influx_client.query(query)
```

---

## 4. Docker Compose - Resource Limits

```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
  
  ollama:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 12G  # 8GB VRAM + 4GB system
        reservations:
          cpus: '2.0'
          memory: 8G
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  postgres:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U optiflow"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  influxdb:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8086/health"]
      interval: 10s
      timeout: 5s
      retries: 3
  
  redis:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
```

---

## 5. Health Checks Inteligentes

### 5.1 Readiness Probe (Pronto para receber tráfego?)

```python
# backend/app/api/routes/health.py
@router.get("/health/ready")
async def readiness_check():
    """Verifica se o serviço está pronto para processar requests"""
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "influxdb": await check_influxdb(),
        "ollama": await check_ollama(),
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

async def check_database():
    try:
        async with asyncio.timeout(2):
            await db.execute("SELECT 1")
            return True
    except Exception:
        return False

async def check_ollama():
    try:
        async with asyncio.timeout(5):
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
                return resp.status_code == 200
    except Exception:
        return False
```

### 5.2 Liveness Probe (Aplicação está viva?)

```python
@router.get("/health/live")
async def liveness_check():
    """Verifica se a aplicação não está travada"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
```

---

## 6. Graceful Shutdown

```python
# backend/app/main.py
import signal
import asyncio

shutdown_event = asyncio.Event()

async def shutdown_handler(signum, frame):
    """Processa shutdown gracefully"""
    logger.info(f"🛑 Received signal {signum}, starting graceful shutdown...")
    
    # 1. Parar de aceitar novos requests
    shutdown_event.set()
    
    # 2. Aguardar requests em andamento (max 30s)
    logger.info("⏳ Waiting for active requests to finish (max 30s)...")
    await asyncio.sleep(2)  # Pequeno delay para requests finalizarem
    
    # 3. Fechar conexões com DBs
    logger.info("📦 Closing database connections...")
    await db.disconnect()
    await redis_client.close()
    await influx_client.close()
    
    # 4. Parar simulator se ativo
    if simulator.running:
        logger.info("🔌 Stopping simulator...")
        simulator.stop()
    
    logger.info("✅ Graceful shutdown complete")

# Registrar handlers
signal.signal(signal.SIGTERM, lambda s, f: asyncio.create_task(shutdown_handler(s, f)))
signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(shutdown_handler(s, f)))

@app.on_event("shutdown")
async def on_shutdown():
    await shutdown_handler(signal.SIGTERM, None)
```

---

## 7. Monitoramento e Alertas

### 7.1 Prometheus Metrics

```python
# backend/app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Ollama metrics
ollama_requests_total = Counter('ollama_requests_total', 'Total Ollama requests')
ollama_failures_total = Counter('ollama_failures_total', 'Failed Ollama requests')
ollama_circuit_breaker_state = Gauge('ollama_circuit_breaker_state', 'Circuit breaker state (0=closed, 1=open)')

# InfluxDB metrics
influxdb_query_duration = Histogram('influxdb_query_duration_seconds', 'InfluxDB query duration')
influxdb_active_queries = Gauge('influxdb_active_queries', 'Active InfluxDB queries')

# System metrics
system_memory_usage = Gauge('system_memory_usage_bytes', 'System memory usage')
system_cpu_usage = Gauge('system_cpu_usage_percent', 'System CPU usage')
```

### 7.2 Alertmanager Rules

```yaml
# monitoring/prometheus/alerts/production.yml
groups:
  - name: production_alerts
    interval: 30s
    rules:
      # Backend alerts
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected ({{ $value }})"
          description: "Error rate > 5% for 2 minutes"
      
      - alert: SlowResponseTime
        expr: http_request_duration_seconds{quantile="0.95"} > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "95th percentile response time > 5s"
      
      - alert: OllamaCircuitBreakerOpen
        expr: ollama_circuit_breaker_state == 1
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Ollama circuit breaker is OPEN"
      
      # Resource alerts
      - alert: HighMemoryUsage
        expr: system_memory_usage_bytes / 4294967296 > 0.9  # 90% of 4GB
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Memory usage > 90%"
      
      - alert: HighCPUUsage
        expr: system_cpu_usage_percent > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CPU usage > 80% for 10 minutes"
      
      # Database alerts
      - alert: DatabaseConnectionPoolExhausted
        expr: database_connections_active / database_connections_max > 0.9
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool > 90% usage"
```

---

## 8. Backup e Disaster Recovery

### 8.1 Backup Automático

```bash
# scripts/backup-production.sh
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
S3_BUCKET="s3://optiflow-backups"

# 1. Backup PostgreSQL
echo "🗄️  Backing up PostgreSQL..."
docker exec optiflow-postgres pg_dump -U optiflow optiflow | \
  gzip > "${BACKUP_DIR}/postgres_${TIMESTAMP}.sql.gz"

# 2. Backup InfluxDB
echo "📊 Backing up InfluxDB..."
docker exec optiflow-influxdb influx backup \
  -bucket optiflow -path /tmp/influx_backup
docker cp optiflow-influxdb:/tmp/influx_backup \
  "${BACKUP_DIR}/influxdb_${TIMESTAMP}"

# 3. Backup Redis (se necessário)
echo "💾 Backing up Redis..."
docker exec optiflow-redis redis-cli SAVE
docker cp optiflow-redis:/data/dump.rdb \
  "${BACKUP_DIR}/redis_${TIMESTAMP}.rdb"

# 4. Upload para S3/MinIO
echo "☁️  Uploading to S3..."
aws s3 sync "${BACKUP_DIR}" "${S3_BUCKET}/$(date +%Y/%m/%d)/"

# 5. Limpeza (manter últimos 7 dias localmente)
echo "🧹 Cleaning old backups..."
find "${BACKUP_DIR}" -type f -mtime +7 -delete

echo "✅ Backup completed: ${TIMESTAMP}"
```

**Cron:**
```cron
# /etc/crontab
0 2 * * * root /opt/optiflow/scripts/backup-production.sh >> /var/log/optiflow-backup.log 2>&1
```

### 8.2 Restore Procedure

```bash
# scripts/restore-production.sh
#!/bin/bash
set -euo pipefail

BACKUP_DATE=$1  # Format: 20250118_020000

echo "⚠️  WARNING: This will restore data from ${BACKUP_DATE}"
read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted"
    exit 1
fi

# 1. Stop services
docker compose stop backend frontend

# 2. Restore PostgreSQL
echo "🗄️  Restoring PostgreSQL..."
gunzip -c "/backups/postgres_${BACKUP_DATE}.sql.gz" | \
  docker exec -i optiflow-postgres psql -U optiflow optiflow

# 3. Restore InfluxDB
echo "📊 Restoring InfluxDB..."
docker cp "/backups/influxdb_${BACKUP_DATE}" optiflow-influxdb:/tmp/restore
docker exec optiflow-influxdb influx restore \
  -bucket optiflow /tmp/restore

# 4. Restart services
docker compose up -d

echo "✅ Restore completed"
```

---

## 9. Deployment Strategy

### 9.1 Blue-Green Deployment

```bash
# scripts/deploy-blue-green.sh
#!/bin/bash
set -euo pipefail

NEW_VERSION=$1
CURRENT_COLOR=$(docker ps --filter name=backend --format "{{.Names}}" | grep -o 'blue\|green')
NEW_COLOR=$([ "$CURRENT_COLOR" == "blue" ] && echo "green" || echo "blue")

echo "🚀 Deploying version ${NEW_VERSION} to ${NEW_COLOR}"

# 1. Pull new image
docker pull optiflow/backend:${NEW_VERSION}

# 2. Start new color
docker compose -f docker-compose.${NEW_COLOR}.yml up -d

# 3. Wait for health check
echo "⏳ Waiting for health check..."
for i in {1..30}; do
    if curl -sf http://localhost:8001/health/ready; then
        echo "✅ New version is healthy"
        break
    fi
    sleep 2
done

# 4. Monitor error rate for 5 minutes
echo "📊 Monitoring error rate..."
sleep 300

ERROR_RATE=$(curl -s 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[5m])' | \
  jq -r '.data.result[0].value[1]')

if (( $(echo "$ERROR_RATE > 0.1" | bc -l) )); then
    echo "❌ High error rate detected: ${ERROR_RATE}"
    echo "🔄 Rolling back..."
    docker compose -f docker-compose.${NEW_COLOR}.yml down
    exit 1
fi

# 5. Switch traffic
echo "🔀 Switching traffic to ${NEW_COLOR}..."
# Update nginx/load balancer config
sed -i "s/backend:8000/backend-${NEW_COLOR}:8000/" /etc/nginx/sites-enabled/optiflow
nginx -s reload

# 6. Stop old version
echo "🛑 Stopping ${CURRENT_COLOR}..."
docker compose -f docker-compose.${CURRENT_COLOR}.yml down

echo "✅ Deployment completed successfully"
```

---

## 10. Logging Estruturado

```python
# backend/app/core/logging.py
import logging
import json
from datetime import datetime
from contextvars import ContextVar
from uuid import uuid4

# Context var para correlation ID
correlation_id: ContextVar[str] = ContextVar('correlation_id', default=None)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id.get(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        # Adicionar campos extras
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id
        if hasattr(record, "endpoint"):
            log_obj["endpoint"] = record.endpoint
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = record.duration_ms
        
        return json.dumps(log_obj)

# Middleware para correlation ID
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    cid = request.headers.get("X-Correlation-ID", str(uuid4()))
    correlation_id.set(cid)
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response
```

---

## 11. Variáveis de Ambiente - Produção

```bash
# .env.production
# NÃO VERSIONAR - usar secrets manager em produção

# App
ENV=production
DEBUG=false
LOG_LEVEL=INFO
ENABLE_SIMULATOR=false  # ⚠️ NUNCA EM PRODUÇÃO

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_IP=100
RATE_LIMIT_CHAT_ENDPOINT=10

# Timeouts
OLLAMA_TIMEOUT=30
INFLUXDB_TIMEOUT=10
POSTGRES_TIMEOUT=5

# Circuit Breakers
OLLAMA_CIRCUIT_BREAKER_THRESHOLD=3
OLLAMA_CIRCUIT_BREAKER_TIMEOUT=60

# Connection Pools
POSTGRES_POOL_SIZE=20
REDIS_POOL_SIZE=50
INFLUXDB_MAX_CONCURRENT=10

# Cache
CACHE_L1_TTL=300  # 5 minutes
CACHE_L2_TTL=3600  # 1 hour

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_PORT=9090
```

---

## 12. Checklist de Deploy

### Pré-Deploy
- [ ] Backup completo de Postgres e InfluxDB
- [ ] Health checks passando em staging
- [ ] Load tests executados (target: 1000 req/min)
- [ ] Rollback plan documentado
- [ ] Alertas configurados no Grafana

### Deploy
- [ ] Blue-green deployment executado
- [ ] Health checks passando no novo ambiente
- [ ] Smoke tests executados
- [ ] Monitoramento ativo por 15 minutos
- [ ] Error rate < 1%

### Pós-Deploy
- [ ] Logs sem erros críticos
- [ ] Métricas de performance dentro do esperado
- [ ] Backup da versão anterior mantido por 7 dias
- [ ] Documentação atualizada
- [ ] Post-mortem se houve incidentes

---

## 13. SLAs e SLOs

### Service Level Objectives (SLOs)
- **Availability**: 99.9% uptime (43 minutos downtime/mês)
- **Latency**: 
  - P50: < 500ms
  - P95: < 2s
  - P99: < 5s
- **Error Rate**: < 1% (99% de requests bem-sucedidos)
- **Recovery Time**: < 5 minutos para falhas automáticas

### Service Level Indicators (SLIs)
- **Uptime**: Medido por health check a cada 10s
- **Request Duration**: Histogram do Prometheus
- **Error Rate**: Contador de 5xx / total de requests
- **Saturation**: CPU, RAM, disk, network usage

---

## 14. Próximos Passos

### Curto Prazo (Esta Sprint)
1. ✅ Implementar circuit breakers
2. ✅ Adicionar resource limits
3. ✅ Implementar graceful shutdown
4. ✅ Configurar health checks robustos

### Médio Prazo (Próximo Mês)
1. Implementar blue-green deployment
2. Configurar Prometheus + Grafana completo
3. Automatizar backups
4. Implementar logging estruturado

### Longo Prazo (Próximo Trimestre)
1. Kubernetes migration (auto-scaling)
2. Multi-region deployment
3. Disaster recovery drills
4. Chaos engineering (Chaos Monkey)

---

**Documentado por**: Claude AI Assistant  
**Data**: 18 de Novembro de 2025  
**Versão**: 1.0.0
