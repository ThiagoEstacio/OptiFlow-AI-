# OptiFlow AI - Quick Start: Production Hardening
## Transforme o Sistema em Enterprise-Grade em 5 Dias

> **Para implantação IMEDIATA em cliente: Siga apenas os passos CRÍTICOS**
> **Para implantação ROBUSTA: Complete todos os 5 dias**

---

## 🚨 DIA 0 - PRÉ-REQUISITOS (2 horas)

### Auditoria Inicial
```bash
# 1. Execute auditoria de prontidão
./scripts/production-readiness-audit.sh

# 2. Revise o score e prioridades
# Score < 75%? Siga o plano completo
# Score 75-90%? Foque nos itens CRÍTICOS
# Score > 90%? Revise apenas melhorias
```

### Backup Imediato (CRÍTICO!)
```bash
# Crie backup antes de qualquer mudança
./scripts/backup.sh
```

---

## 🔴 DIA 1 - CRÍTICO: Segurança & Backups (8 horas)

### Manhã: Remover Credenciais Hardcoded (3h)

**1. Criar arquivo .env de produção**
```bash
# .env.production (NÃO COMMITAR!)
cat > .env.production << 'EOF'
# Database
POSTGRES_PASSWORD=$(openssl rand -base64 32)
POSTGRES_USER=optiflow_prod

# InfluxDB
INFLUXDB_ADMIN_TOKEN=$(openssl rand -base64 32)

# Redis
REDIS_PASSWORD=$(openssl rand -base64 32)

# JWT
JWT_SECRET_KEY=$(openssl rand -base64 64)

# Admin
ADMIN_DEFAULT_PASSWORD=$(openssl rand -base64 16)
EOF
```

**2. Atualizar docker-compose.prod.yml**
```yaml
# Substituir todas senhas hardcoded por:
environment:
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  # ...etc
```

**3. Atualizar backend/app/core/config.py**
```python
# Adicionar validação
@validator('POSTGRES_PASSWORD')
def check_password_strength(cls, v):
    if len(v) < 16:
        raise ValueError('Password too weak for production')
    return v
```

### Tarde: Sistema de Backup Automático (5h)

**1. Criar script de backup robusto**
```bash
#!/bin/bash
# scripts/backup-production.sh

BACKUP_DIR="/backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# PostgreSQL
docker compose exec -T postgres pg_dumpall -U optiflow | gzip > "$BACKUP_DIR/postgres.sql.gz"

# InfluxDB
docker compose exec -T influxdb influx backup /tmp/backup
docker compose cp influxdb:/tmp/backup "$BACKUP_DIR/influxdb"

# Application data
tar -czf "$BACKUP_DIR/app-data.tar.gz" backend/ml_models/ monitoring/grafana/dashboards/

# Encrypt backup (IMPORTANTE!)
gpg --symmetric --cipher-algo AES256 "$BACKUP_DIR/postgres.sql.gz"
gpg --symmetric --cipher-algo AES256 "$BACKUP_DIR/influxdb.tar.gz"

# Upload to S3/Azure/GCP (escolha um)
# aws s3 cp "$BACKUP_DIR" s3://optiflow-backups/ --recursive
# az storage blob upload-batch -d optiflow-backups -s "$BACKUP_DIR"
# gsutil -m cp -r "$BACKUP_DIR" gs://optiflow-backups/

# Limpar backups antigos (manter 30 dias)
find /backups -type d -mtime +30 -exec rm -rf {} \;

echo "✅ Backup completed: $BACKUP_DIR"
```

**2. Configurar cron para backup automático**
```bash
# Editar crontab
crontab -e

# Adicionar (backup diário às 2am)
0 2 * * * /opt/optiflow/scripts/backup-production.sh >> /var/log/optiflow-backup.log 2>&1
```

**3. Testar restore**
```bash
# scripts/restore-from-backup.sh
BACKUP_DATE=$1  # Ex: 20251110-140530

# Restore PostgreSQL
gunzip < "/backups/$BACKUP_DATE/postgres.sql.gz" | docker compose exec -T postgres psql -U optiflow

# Restore InfluxDB
docker compose exec influxdb influx restore "/backups/$BACKUP_DATE/influxdb"

echo "✅ Restore completed from $BACKUP_DATE"
```

---

## 🟡 DIA 2 - IMPORTANTE: Alta Disponibilidade (8 horas)

### Manhã: Load Balancer + Múltiplas Instâncias Backend (4h)

**1. Criar nginx.prod.conf**
```nginx
upstream backend {
    least_conn;  # Load balancing por menor conexão
    server backend-1:8000 max_fails=3 fail_timeout=30s;
    server backend-2:8000 max_fails=3 fail_timeout=30s;
    server backend-3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    listen 443 ssl http2;
    
    server_name optiflow.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/optiflow.crt;
    ssl_certificate_key /etc/ssl/private/optiflow.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://backend/health;
    }
    
    # API
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

**2. Atualizar docker-compose.prod.yml**
```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - /etc/ssl:/etc/ssl:ro
    depends_on:
      - backend-1
      - backend-2
      - backend-3
  
  backend-1:
    <<: *backend-template
    container_name: optiflow-backend-1
    
  backend-2:
    <<: *backend-template
    container_name: optiflow-backend-2
    
  backend-3:
    <<: *backend-template
    container_name: optiflow-backend-3
```

### Tarde: Redis Sentinel + Database Replication (4h)

**1. Configurar Redis Sentinel**
```yaml
# docker-compose.prod.yml
  redis-master:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    
  redis-replica-1:
    image: redis:7-alpine
    command: redis-server --replicaof redis-master 6379 --requirepass ${REDIS_PASSWORD}
    
  redis-sentinel-1:
    image: redis:7-alpine
    command: redis-sentinel /etc/redis/sentinel.conf
    volumes:
      - ./redis-sentinel.conf:/etc/redis/sentinel.conf
```

**2. Configurar PostgreSQL Replication**
```yaml
# Usar Patroni ou Stolon para HA automático
  postgres-master:
    image: postgres:15-alpine
    environment:
      POSTGRES_REPLICATION_MODE: master
      
  postgres-replica:
    image: postgres:15-alpine
    environment:
      POSTGRES_REPLICATION_MODE: slave
      POSTGRES_MASTER_HOST: postgres-master
```

---

## 🟢 DIA 3 - MELHORIAS: Observabilidade Avançada (8 horas)

### Manhã: Alertas Críticos (4h)

**1. Configurar alertas no Prometheus**
```yaml
# monitoring/prometheus/alerts/critical.yml
groups:
  - name: critical_alerts
    interval: 30s
    rules:
      # Sistema
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "{{ $labels.instance }} has been down for more than 1 minute"
          
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          
      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.15
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Disk space is running low (< 15%)"
          
      # Backend
      - alert: HighErrorRate
        expr: rate(optiflow_http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected (> 5%)"
          
      - alert: SlowRequests
        expr: histogram_quantile(0.95, rate(optiflow_http_request_duration_seconds_bucket[5m])) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "95th percentile latency > 2s"
          
      # Database
      - alert: DatabaseConnectionPoolExhausted
        expr: optiflow_db_connections_active > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool is exhausted"
          
      # AI/ML
      - alert: AgentUnhealthy
        expr: optiflow_agent_status == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Autonomous agent is unhealthy"
          
      - alert: OllamaDown
        expr: optiflow_ollama_health == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Ollama service is down"
```

**2. Configurar Alertmanager**
```yaml
# monitoring/prometheus/alertmanager.yml
global:
  resolve_timeout: 5m
  
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'team-notifications'
  
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true
      
    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'team-notifications'
    email_configs:
      - to: 'team@yourdomain.com'
        from: 'alertmanager@yourdomain.com'
        smarthost: 'smtp.gmail.com:587'
        
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: YOUR_PAGERDUTY_KEY
        
  - name: 'slack'
    slack_configs:
      - api_url: YOUR_SLACK_WEBHOOK
        channel: '#optiflow-alerts'
```

### Tarde: Distributed Tracing (4h)

**1. Adicionar Jaeger**
```yaml
# docker-compose.prod.yml
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "6831:6831/udp"  # Agent
    environment:
      COLLECTOR_ZIPKIN_HOST_PORT: :9411
```

**2. Instrumentar backend com OpenTelemetry**
```python
# backend/app/core/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_tracing():
    resource = Resource.create({"service.name": "optiflow-backend"})
    tracer_provider = TracerProvider(resource=resource)
    
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
    )
    
    span_processor = BatchSpanProcessor(jaeger_exporter)
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)
    
    return trace.get_tracer(__name__)
```

---

## 🔵 DIA 4 - TESTES: Validação Completa (8 horas)

### Manhã: Testes de Carga (4h)

**1. Executar testes de stress**
```bash
# Teste de carga crescente
k6 run load-testing/scenarios/stress-test.js

# Teste de soak (longa duração)
k6 run load-testing/scenarios/soak-test.js

# Teste de spike (carga súbita)
k6 run load-testing/scenarios/spike-test.js
```

**2. Analisar resultados e otimizar**
- Identificar bottlenecks no Grafana
- Ajustar connection pools
- Otimizar queries lentas
- Aumentar recursos se necessário

### Tarde: Chaos Engineering (4h)

**1. Testar falhas de componentes**
```bash
# scripts/chaos/test-backend-failure.sh
echo "🔥 Testing backend failure..."
docker stop optiflow-backend-1
sleep 60
# Verificar se load balancer redistribuiu tráfego
curl -sf http://localhost/health || echo "❌ FAILED"
docker start optiflow-backend-1

# scripts/chaos/test-database-failure.sh
echo "🔥 Testing database failure..."
docker pause optiflow-postgres
sleep 30
# Verificar circuit breaker
curl -sf http://localhost/api/v1/tags || echo "✅ Circuit breaker working"
docker unpause optiflow-postgres

# scripts/chaos/test-network-partition.sh
echo "🔥 Testing network partition..."
docker network disconnect optiflow-network optiflow-backend-2
sleep 60
# Verificar que sistema continua operacional
docker network connect optiflow-network optiflow-backend-2
```

**2. Validar recuperação automática**
- Testar failover de database
- Testar Redis Sentinel failover
- Validar circuit breakers
- Verificar alertas foram disparados

---

## 🟣 DIA 5 - DEPLOYMENT: CI/CD & Go-Live (8 horas)

### Manhã: CI/CD Pipeline (4h)

**1. Criar GitHub Actions workflow**
```yaml
# .github/workflows/production-deploy.yml
name: Production Deployment

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run unit tests
        run: |
          cd backend
          pytest tests/ --cov=app --cov-report=xml
          
      - name: Check coverage
        run: |
          coverage report --fail-under=60
  
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          
  build:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker images
        run: |
          docker-compose -f docker-compose.prod.yml build
          
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker-compose -f docker-compose.prod.yml push
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to production
        run: |
          ssh ${{ secrets.PROD_HOST }} << 'EOF'
            cd /opt/optiflow
            git pull
            docker-compose -f docker-compose.prod.yml pull
            docker-compose -f docker-compose.prod.yml up -d
            ./scripts/smoke-test.sh
          EOF
```

### Tarde: Go-Live Checklist (4h)

**1. Pré-deployment checklist**
```bash
# Executar auditoria final
./scripts/production-readiness-audit.sh

# Verificar score >= 90%
# Se não, PARAR e corrigir itens críticos

# Backup completo
./scripts/backup-production.sh

# Testes de smoke
./scripts/smoke-test.sh

# Verificar alertas configurados
curl http://localhost:9090/api/v1/alerts

# Verificar dashboards
curl -u admin:admin http://localhost:3001/api/dashboards
```

**2. Deployment**
```bash
# Blue-green deployment
./scripts/deploy-blue-green.sh

# Monitorar métricas por 30 minutos
watch -n 5 'curl -s http://localhost:9090/api/v1/query?query=up | jq'

# Smoke tests em produção
./scripts/smoke-test.sh production

# Se tudo OK: commit blue to production
# Se problemas: rollback to green
```

**3. Pós-deployment**
```bash
# Verificar todos serviços healthy
docker-compose ps

# Verificar logs por erros
docker-compose logs --tail=100 | grep ERROR

# Verificar métricas
curl http://localhost:8000/metrics

# Verificar dashboards Grafana
open http://localhost:3001
```

---

## 📋 CHECKLIST FINAL - GO/NO-GO

### ✅ MUST-HAVE (Bloqueadores)
- [ ] Backups automáticos configurados e testados
- [ ] Restore testado e documentado
- [ ] Credenciais seguras (sem hardcode)
- [ ] SSL/TLS configurado
- [ ] Alertas críticos funcionando
- [ ] Load balancer com health checks
- [ ] Múltiplas instâncias backend
- [ ] Monitoramento completo (Prometheus + Grafana)
- [ ] Circuit breakers testados
- [ ] Score auditoria >= 75%

### 🎯 HIGHLY RECOMMENDED
- [ ] Database replication
- [ ] Redis Sentinel
- [ ] Distributed tracing
- [ ] Chaos tests executados
- [ ] CI/CD pipeline
- [ ] Runbooks documentados
- [ ] Score auditoria >= 85%

### 💪 NICE-TO-HAVE
- [ ] Kubernetes deployment
- [ ] Multi-tenancy
- [ ] Blue-green deployment
- [ ] Score auditoria >= 95%

---

## 🆘 CONTATOS DE EMERGÊNCIA

### Responsáveis
- **DevOps Lead:** [Nome] - [Telefone]
- **Backend Lead:** [Nome] - [Telefone]
- **DBA:** [Nome] - [Telefone]

### Escalation
1. Verificar alertas no Grafana
2. Verificar logs: `docker-compose logs --tail=1000`
3. Verificar circuit breakers
4. Se crítico: executar rollback

### Rollback Procedure
```bash
# 1. Parar versão nova
docker-compose down

# 2. Restaurar backup
./scripts/restore-from-backup.sh BACKUP_DATE

# 3. Subir versão anterior
git checkout PREVIOUS_TAG
docker-compose -f docker-compose.prod.yml up -d

# 4. Verificar sistema
./scripts/smoke-test.sh
```

---

## 📊 MÉTRICAS DE SUCESSO

### SLOs (Service Level Objectives)
- **Availability:** 99.9% uptime (43 min downtime/mês)
- **Latency:** P95 < 500ms, P99 < 1s
- **Error Rate:** < 0.1% das requests
- **Data Loss:** 0 (zero tolerance)

### KPIs
- Tempo de resposta médio < 200ms
- Throughput > 1000 req/s
- Uptime > 99.5%
- MTTR (Mean Time To Repair) < 15 min

---

## 🎉 SUCESSO!

Se você chegou aqui e completou todos os passos CRÍTICOS:

**🚀 SEU SISTEMA ESTÁ PRONTO PARA PRODUÇÃO!**

### Próximos Passos Pós-Implantação:
1. Monitorar métricas por 7 dias
2. Ajustar alertas baseado em false positives
3. Otimizar performance baseado em dados reais
4. Implementar features de NICE-TO-HAVE
5. Documentar lições aprendidas

### Manutenção Contínua:
- **Diária:** Verificar dashboards, alertas, logs
- **Semanal:** Revisar métricas de SLO, testar backups
- **Mensal:** Chaos engineering, security audit
- **Trimestral:** Capacity planning, performance tuning

---

**Dúvidas? Problemas?** 
Consulte RUNBOOK.md ou abra um incident ticket.

**Boa sorte! 🍀**
