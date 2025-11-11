# OptiFlow AI - Guia Rápido de Operações

**Quick Reference** para operações diárias de produção.

---

## 🚀 Deploy Inicial

### 1. Gerar Credenciais de Produção
```bash
cd /home/thiestacio/OptiFlow-AI-
./scripts/generate-production-secrets.sh

# Backup do output (ÚNICA VEZ que credenciais são mostradas)
# Salvar em password manager
```

### 2. Personalizar Configurações
```bash
nano .env.production

# Atualizar:
# - SMTP credentials (ALERTMANAGER_SMTP_*)
# - Domínios (CORS_ORIGINS, VITE_API_URL)
# - AWS S3 (se usar backup cloud)
# - Slack/PagerDuty webhooks
```

### 3. Validar Configuração
```bash
# Verificar docker-compose
docker-compose -f docker-compose.prod.yml config

# Verificar se variáveis foram substituídas
docker-compose -f docker-compose.prod.yml config | grep -i "postgres_password"
# Deve mostrar senha real, não ${POSTGRES_PASSWORD}
```

### 4. Deploy
```bash
# Subir todos os serviços
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# Verificar status
docker-compose -f docker-compose.prod.yml ps

# Verificar logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 💾 Backup & Restore

### Backup Manual
```bash
# Executar backup
./scripts/backup-production.sh

# Verificar backup criado
ls -lh /backups/$(date +%Y%m%d_*)

# Verificar saúde do backup
./scripts/check-backup-health.sh
```

### Restore
```bash
# Listar backups disponíveis
ls -lh /backups/

# Executar restore interativo
./scripts/restore-from-backup.sh
# Selecione o backup
# Confirme com "YES"
```

### Configurar Backup Automático (Cron)
```bash
# Copiar configuração cron
sudo cp scripts/backup-cron /etc/cron.d/optiflow-backup
sudo chmod 644 /etc/cron.d/optiflow-backup

# Verificar cron configurado
sudo crontab -l | grep backup

# Testar manualmente
sudo -u root /home/thiestacio/OptiFlow-AI-/scripts/backup-production.sh
```

---

## 🔔 Alertas

### Ver Alertas Ativos
```bash
# Prometheus UI
# http://localhost:9090/alerts

# Alertmanager UI
# http://localhost:9093/#/alerts

# Via API
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | {name: .labels.alertname, state: .state}'
```

### Testar Alerta
```bash
# 1. Simular ServiceDown
docker-compose -f docker-compose.prod.yml stop backend
# Aguardar 1min, verificar notificação
docker-compose -f docker-compose.prod.yml start backend

# 2. Enviar alerta de teste
curl -X POST http://localhost:9093/api/v1/alerts -H "Content-Type: application/json" -d '[{
  "labels": {"alertname": "TestAlert", "severity": "warning"},
  "annotations": {"summary": "Test", "description": "Testing"}
}]'
```

### Silenciar Alerta (Manutenção)
```bash
# Via Alertmanager UI
# http://localhost:9093/#/silences
# Clicar em "New Silence"

# Via API
curl -X POST http://localhost:9093/api/v1/silences -H "Content-Type: application/json" -d '{
  "matchers": [{"name": "alertname", "value": "ServiceDown"}],
  "startsAt": "2024-01-15T10:00:00Z",
  "endsAt": "2024-01-15T12:00:00Z",
  "createdBy": "ops@optiflow.com",
  "comment": "Manutenção programada"
}'
```

---

## 🔍 Monitoramento

### Verificar Status dos Serviços
```bash
# Docker status
docker-compose -f docker-compose.prod.yml ps

# Health checks
curl http://localhost:8000/health        # Backend
curl http://localhost:8086/health        # InfluxDB
curl http://localhost:9090/-/healthy     # Prometheus
curl http://localhost:9093/-/healthy     # Alertmanager
curl http://localhost:3000/api/health    # Grafana

# Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

### Ver Métricas
```bash
# Prometheus UI
# http://localhost:9090/graph

# Grafana Dashboards
# http://localhost:3000
# Login: admin / (ver .env.production)

# Métricas específicas
curl 'http://localhost:9090/api/v1/query?query=up' | jq '.data.result'
curl 'http://localhost:9090/api/v1/query?query=optiflow_agent_health_status' | jq
```

### Logs
```bash
# Todos os serviços
docker-compose -f docker-compose.prod.yml logs -f

# Serviço específico
docker-compose -f docker-compose.prod.yml logs -f backend

# Últimas 100 linhas
docker-compose -f docker-compose.prod.yml logs --tail=100 backend

# Buscar por erro
docker-compose -f docker-compose.prod.yml logs backend | grep -i error
```

---

## 🔧 Troubleshooting

### Serviço Não Inicia
```bash
# Ver logs
docker logs smartport-backend-prod

# Ver recursos
docker stats smartport-backend-prod

# Reiniciar serviço
docker-compose -f docker-compose.prod.yml restart backend

# Rebuild e restart
docker-compose -f docker-compose.prod.yml up -d --build backend
```

### Banco de Dados Não Conecta
```bash
# Verificar PostgreSQL
docker exec smartport-postgres-prod pg_isready -U optiflow_prod

# Conectar ao PostgreSQL
docker exec -it smartport-postgres-prod psql -U optiflow_prod -d optiflow

# Verificar conexões ativas
docker exec smartport-postgres-prod psql -U optiflow_prod -d optiflow -c "SELECT count(*) FROM pg_stat_activity;"
```

### Alto Uso de Memória
```bash
# Ver uso de memória
docker stats --no-stream | sort -k4 -h

# Ver top processos no container
docker exec smartport-backend-prod top -b -n 1

# Limpar cache Redis
docker exec smartport-redis-prod redis-cli -a "${REDIS_PASSWORD}" FLUSHALL
```

### Disco Cheio
```bash
# Ver uso de disco
df -h

# Limpar logs antigos
find /var/lib/docker/containers -name "*.log" -mtime +7 -delete

# Limpar volumes não usados
docker system prune -a --volumes

# Limpar backups antigos
find /backups -type d -name "20*" -mtime +7 -exec rm -rf {} \;
```

---

## 🔄 Atualizações

### Atualizar Código (Backend/Frontend)
```bash
# Pull latest code
git pull origin main

# Rebuild e restart
docker-compose -f docker-compose.prod.yml up -d --build backend frontend

# Verificar logs
docker-compose -f docker-compose.prod.yml logs -f backend frontend
```

### Atualizar Configuração
```bash
# Editar configuração
nano .env.production

# Recarregar (sem rebuild)
docker-compose -f docker-compose.prod.yml up -d

# Verificar nova config aplicada
docker-compose -f docker-compose.prod.yml exec backend env | grep VARIABLE_NAME
```

### Atualizar Alertas
```bash
# Editar regras
nano monitoring/prometheus/alerts/critical.yml

# Validar sintaxe
docker exec prometheus promtool check rules /etc/prometheus/alerts/critical.yml

# Reload Prometheus (sem restart)
curl -X POST http://localhost:9090/-/reload

# Verificar regras carregadas
curl http://localhost:9090/api/v1/rules | jq '.data.groups[].name'
```

---

## 🔐 Segurança

### Rotacionar Credenciais
```bash
# 1. Gerar novas credenciais
./scripts/generate-production-secrets.sh

# 2. Atualizar .env.production
# (script já cria backup do antigo)

# 3. Restart serviços
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# 4. Verificar funcionamento
curl http://localhost:8000/health
```

### Verificar Logs de Segurança
```bash
# Failed login attempts
docker-compose -f docker-compose.prod.yml logs backend | grep -i "failed.*login"

# Acessos não autorizados
docker-compose -f docker-compose.prod.yml logs backend | grep -i "401\|403"

# Verificar alerta de segurança
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.component=="security")'
```

---

## 📊 Performance

### Métricas de Latência
```bash
# P95 latency backend
curl 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,sum(rate(http_request_duration_seconds_bucket[5m]))by(le))'

# Request rate
curl 'http://localhost:9090/api/v1/query?query=rate(http_requests_total[5m])'

# Error rate
curl 'http://localhost:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[5m])'
```

### Load Testing
```bash
# Instalar k6
wget https://github.com/grafana/k6/releases/download/v0.45.0/k6-v0.45.0-linux-amd64.tar.gz
tar -xzf k6-v0.45.0-linux-amd64.tar.gz

# Executar load test
cd load-testing
k6 run load-test.js

# Stress test
k6 run scenarios/stress-test.js
```

---

## 🧹 Manutenção

### Limpeza Semanal
```bash
#!/bin/bash
# Executar toda segunda-feira

# Limpar logs Docker antigos (>7 dias)
find /var/lib/docker/containers -name "*.log" -mtime +7 -delete

# Limpar backups antigos (>30 dias)
find /backups -type d -name "20*" -mtime +30 -exec rm -rf {} \;

# Limpar imagens Docker não usadas
docker image prune -a -f --filter "until=168h"

# Limpar volumes órfãos
docker volume prune -f

# Restart serviços (minimizar memory leaks)
docker-compose -f docker-compose.prod.yml restart
```

### Health Check Diário
```bash
#!/bin/bash
# Executar todo dia

# 1. Verificar backup
./scripts/check-backup-health.sh

# 2. Verificar alertas ativos
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'

# 3. Verificar disk space
df -h | grep -E "/$|/backups"

# 4. Verificar serviços
docker-compose -f docker-compose.prod.yml ps | grep -v "Up"

# 5. Verificar memória
free -h
```

---

## 📱 Comandos Mobile (SSH)

### Status Rápido
```bash
alias status='docker-compose -f docker-compose.prod.yml ps'
alias logs='docker-compose -f docker-compose.prod.yml logs -f --tail=50'
alias metrics='curl -s http://localhost:9090/api/v1/query?query=up | jq'
alias alerts='curl -s http://localhost:9090/api/v1/alerts | jq ".data.alerts[] | select(.state==\"firing\") | .labels.alertname"'
```

### Restart de Emergência
```bash
# Backend travado
docker-compose -f docker-compose.prod.yml restart backend

# Tudo travado
docker-compose -f docker-compose.prod.yml restart

# Last resort (downtime!)
docker-compose -f docker-compose.prod.yml down && \
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
```

---

## 📞 Escalation

### Nível 1: Auto-Resolução
- Restart serviço
- Limpar cache Redis
- Verificar logs

### Nível 2: Operador
- Restore de backup
- Rotacionar credenciais
- Executar runbook

### Nível 3: Tech Lead
- Código changes necessárias
- Scaling horizontal
- Arquitetura changes

### Nível 4: CTO/Vendor
- Infraestrutura cloud issues
- Critical security breach
- Data loss scenarios

---

## 📚 Referências Rápidas

### Documentação
- `PRODUCTION_READINESS.md` - Roadmap completo
- `QUICK_START_PRODUCTION.md` - Guia 5 dias
- `SECURITY_CREDENTIALS_DONE.md` - Credenciais
- `BACKUP_SYSTEM_DONE.md` - Backup/Restore
- `ALERTING_SYSTEM_DONE.md` - Alertas
- `CRITICAL_ITEMS_COMPLETED.md` - Resumo executivo

### URLs Importantes
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093
- Backend API: http://localhost:8000
- Frontend: http://localhost:80

### Arquivos Críticos
- `.env.production` - Credenciais (chmod 600)
- `/backups/` - Backups criptografados
- `monitoring/prometheus/alerts/critical.yml` - Regras de alerta
- `monitoring/prometheus/alertmanager.yml` - Routing de alertas

---

**Última Atualização**: $(date +%Y-%m-%d)  
**Versão**: 1.0  
**Status**: Production Ready ✅
