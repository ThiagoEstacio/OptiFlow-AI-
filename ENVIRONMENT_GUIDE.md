# OptiFlow - Guia de Ambientes

## 📋 Visão Geral

OptiFlow suporta 3 ambientes:

| Ambiente | Uso | Ferramenta | Config |
|----------|-----|------------|--------|
| **Development** | Desenvolvimento local | Docker Compose | `.env` |
| **Staging** | Testes pré-produção | K3s | `.env.staging` |
| **Production** | Produção (clientes) | Azure AKS / AWS EKS | `.env.production` |

---

## 🛠️ Development (Local)

### Ferramenta: Docker Compose

**Para quê?**
- Desenvolvimento diário
- Testes locais
- Debug

**Configuração**: `.env`

```bash
# Usar arquivo .env existente
docker-compose up -d

# Ou especificar arquivo diferente
docker-compose --env-file .env.local up -d
```

### Características

✅ **Hot reload** - Mudanças no código refletem automaticamente
✅ **Logs fáceis** - `docker-compose logs -f backend`
✅ **Restart rápido** - `docker-compose restart backend`
✅ **1 réplica** de cada serviço (sem load balancing)
✅ **Dados locais** - PostgreSQL, InfluxDB, Redis em volumes Docker
✅ **Sem HTTPS** - HTTP puro (localhost)

###Variáveis Importantes

```bash
# .env (Development)
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# URLs locais
VITE_API_URL=http://localhost:8000
DATABASE_URL=postgresql+asyncpg://optiflow:optiflow_password@postgres:5432/optiflow

# Senhas simples (OK para dev)
POSTGRES_PASSWORD=optiflow_password
REDIS_PASSWORD=optiflow_redis_password
```

---

## 🧪 Staging (Pré-Produção)

### Ferramenta: K3s

**Para quê?**
- Simular produção
- Testes de integração
- Validação antes de deploy

**Configuração**: `.env.staging`

```bash
# Deploy no K3s
kubectl create namespace optiflow-staging

# Criar ConfigMap com .env.staging
kubectl create configmap optiflow-config \
  --from-env-file=.env.staging \
  -n optiflow-staging

# Deploy serviços
kubectl apply -f infrastructure/kubernetes/staging/ -n optiflow-staging
```

### Características

✅ **Kubernetes real** - Mesma infraestrutura que produção
✅ **Load balancing** - NGINX Ingress
✅ **2-3 réplicas** de cada serviço
✅ **Auto-scaling** - HPA (Horizontal Pod Autoscaler)
✅ **Monitoring** - Prometheus + Grafana
✅ **Dados isolados** - Banco staging separado

### Variáveis Importantes

```bash
# .env.staging
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

# URLs staging
VITE_API_URL=https://api-staging.optiflow.com
DATABASE_URL=postgresql+asyncpg://optiflow:STRONG_PASSWORD@postgres-staging:5432/optiflow_staging

# Senhas FORTES
POSTGRES_PASSWORD=<gerar-senha-forte>
REDIS_PASSWORD=<gerar-senha-forte>
JWT_SECRET_KEY=<gerar-chave-forte>

# Features para testar
FEATURE_ML_ENABLED=true
FEATURE_AI_AGENT_ENABLED=true
```

### Como gerar senhas fortes

```bash
# Gerar senha aleatória
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Exemplo de saída:
# 8zR3mK9vP2xL4qW7nT1yF6hB5jC0eD8aU4iO3pQ2sG1

# Usar no .env.staging:
POSTGRES_PASSWORD=8zR3mK9vP2xL4qW7nT1yF6hB5jC0eD8aU4iO3pQ2sG1
```

---

## 🚀 Production (Produção)

### Ferramenta: Azure AKS (recomendado) ou AWS EKS

**Para quê?**
- Clientes reais
- SLA 99.95%
- Alta disponibilidade

**Configuração**: `.env.production` + Vault/Secrets Manager

```bash
# NÃO usar .env em produção!
# Usar secrets management:

# Opção 1: Kubernetes Secrets
kubectl create secret generic optiflow-secrets \
  --from-literal=POSTGRES_PASSWORD=<senha-forte> \
  --from-literal=JWT_SECRET_KEY=<chave-forte> \
  -n optiflow-prod

# Opção 2: HashiCorp Vault
vault kv put secret/optiflow/prod \
  POSTGRES_PASSWORD=<senha-forte> \
  JWT_SECRET_KEY=<chave-forte>

# Opção 3: Azure Key Vault (recomendado Azure)
az keyvault secret set \
  --vault-name optiflow-vault \
  --name postgres-password \
  --value '<senha-forte>'
```

### Características

✅ **Cloud managed** - Azure AKS / AWS EKS
✅ **Load balancing** - Azure LB + NGINX Ingress (2 camadas)
✅ **5-10 réplicas** por serviço
✅ **Auto-scaling** - HPA + Cluster Autoscaler
✅ **HTTPS** - cert-manager + Let's Encrypt
✅ **Monitoring** - Prometheus + Grafana + AlertManager
✅ **Alerting** - PagerDuty + Slack
✅ **Backup automático** - Diário, retenção 30 dias
✅ **Multi-AZ** - Alta disponibilidade

### Variáveis Importantes

```bash
# .env.production (apenas referência, usar Vault!)
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# URLs produção
VITE_API_URL=https://api.optiflow.com
DATABASE_URL=postgresql+asyncpg://optiflow:${POSTGRES_PASSWORD}@postgres-prod:5432/optiflow

# Senhas gerenciadas por Vault
# POSTGRES_PASSWORD=<vault:secret/optiflow/prod#POSTGRES_PASSWORD>
# JWT_SECRET_KEY=<vault:secret/optiflow/prod#JWT_SECRET_KEY>

# Features todas habilitadas
FEATURE_ML_ENABLED=true
FEATURE_AI_AGENT_ENABLED=true
FEATURE_PREDICTIVE_MAINTENANCE=true
FEATURE_ADVANCED_ANALYTICS=true

# Monitoring
SENTRY_DSN=<sentry-dsn>
PROMETHEUS_URL=http://prometheus:9090

# Backup
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"  # 2 AM diário
BACKUP_S3_BUCKET=optiflow-prod-backups

# Auto-scaling
HPA_MIN_REPLICAS=5
HPA_MAX_REPLICAS=20
HPA_TARGET_CPU_UTILIZATION=70
```

---

## 🔐 Segurança por Ambiente

### Development (Local)

```bash
# ✅ OK para desenvolvimento
SECRET_KEY=dev-secret-key
POSTGRES_PASSWORD=optiflow_password

# ⚠️ NUNCA commitar .env no Git!
echo ".env" >> .gitignore
```

### Staging

```bash
# ✅ Senhas fortes
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
POSTGRES_PASSWORD=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# ✅ HTTPS obrigatório
INGRESS_TLS_ENABLED=true

# ✅ Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
```

### Production

```bash
# ✅ Secrets management (Vault/Key Vault)
# NÃO usar variáveis de ambiente diretas

# ✅ Checklist de segurança:
# - [ ] Senhas geradas com >= 32 caracteres
# - [ ] JWT secret >= 32 bytes
# - [ ] HTTPS com TLS 1.3
# - [ ] Network Policies (pod isolation)
# - [ ] RBAC configurado
# - [ ] Secrets rotacionados a cada 90 dias
# - [ ] Logs de auditoria habilitados
# - [ ] Rate limiting ativo
# - [ ] DDoS protection (CloudFlare)
# - [ ] Backup automático testado
# - [ ] Disaster recovery documentado
```

---

## 📊 Comparação de Ambientes

| Característica | Development | Staging | Production |
|---------------|-------------|---------|------------|
| **Ferramenta** | Docker Compose | K3s | Azure AKS |
| **Réplicas** | 1 | 2-3 | 5-10 |
| **Load Balancer** | ❌ Não | ✅ NGINX | ✅ Azure LB + NGINX |
| **Auto-scaling** | ❌ Não | ✅ HPA | ✅ HPA + Cluster AS |
| **HTTPS** | ❌ HTTP | ✅ TLS | ✅ TLS 1.3 |
| **Monitoring** | Básico | Completo | Completo + PagerDuty |
| **Backup** | ❌ Manual | ✅ Diário | ✅ Diário + Multi-region |
| **Custo/mês** | $0 (local) | ~$100 | ~$950 (10 plantas) |
| **SLA** | - | 99% | 99.95% |

---

## 🔄 Workflow de Deploy

```
┌──────────────────────────────────────────────────────────────┐
│  DESENVOLVIMENTO (Local)                                     │
├──────────────────────────────────────────────────────────────┤
│  • Desenvolve em Docker Compose                              │
│  • Testa localmente                                          │
│  • Commit & Push para Git                                    │
└────────────┬─────────────────────────────────────────────────┘
             │
             │ git push origin develop
             ▼
┌──────────────────────────────────────────────────────────────┐
│  CI/CD (GitHub Actions)                                      │
├──────────────────────────────────────────────────────────────┤
│  • Roda testes automatizados                                 │
│  • Build de imagens Docker                                   │
│  • Push para registry (Docker Hub / Azure CR)                │
└────────────┬─────────────────────────────────────────────────┘
             │
             │ Se testes passam
             ▼
┌──────────────────────────────────────────────────────────────┐
│  STAGING (K3s)                                               │
├──────────────────────────────────────────────────────────────┤
│  • Deploy automático (ArgoCD)                                │
│  • Testes de integração                                      │
│  • Validação de stakeholders                                 │
│  • Performance testing                                       │
└────────────┬─────────────────────────────────────────────────┘
             │
             │ Se aprovado
             │ (merge develop → main)
             ▼
┌──────────────────────────────────────────────────────────────┐
│  PRODUCTION (Azure AKS)                                      │
├──────────────────────────────────────────────────────────────┤
│  • Aprovação manual obrigatória                              │
│  • Deploy via ArgoCD (GitOps)                                │
│  • Rollout progressivo (Canary/Blue-Green)                   │
│  • Monitoramento 24/7                                        │
│  • Alertas automáticos                                       │
└──────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Mudança de Ambiente

### Development → Staging

```bash
# 1. Gerar senhas fortes
./scripts/generate-secrets.sh staging

# 2. Atualizar .env.staging
vim .env.staging

# 3. Deploy no K3s
kubectl create configmap optiflow-config \
  --from-env-file=.env.staging \
  -n optiflow-staging

kubectl apply -f infrastructure/kubernetes/staging/ \
  -n optiflow-staging

# 4. Verificar
kubectl get pods -n optiflow-staging
kubectl logs -f deployment/backend -n optiflow-staging
```

### Staging → Production

```bash
# 1. Criar secrets no Vault
vault kv put secret/optiflow/prod \
  POSTGRES_PASSWORD=$(python -c "import secrets; print(secrets.token_urlsafe(32))") \
  JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# 2. Deploy via ArgoCD (GitOps)
# Commit manifests para Git
git add infrastructure/kubernetes/production/
git commit -m "feat: Deploy v1.0.0 to production"
git push origin main

# 3. ArgoCD detecta mudanças e faz deploy automático
argocd app sync optiflow-prod

# 4. Verificar
kubectl get pods -n optiflow-prod
kubectl logs -f deployment/backend -n optiflow-prod

# 5. Monitorar
# Grafana: https://grafana.optiflow.com
# Prometheus: https://prometheus.optiflow.com
```

---

## 📝 Checklist de Deploy

### Antes de Staging

- [ ] Testes locais passando (pytest)
- [ ] Código revisado (code review)
- [ ] Migrations rodando sem erros
- [ ] .env.staging atualizado
- [ ] Senhas geradas e documentadas (secrets manager)
- [ ] Build de imagens Docker OK

### Antes de Production

- [ ] Staging testado e aprovado
- [ ] Performance testing OK (carga, stress)
- [ ] Security scan das imagens (Trivy/Snyk)
- [ ] Secrets no Vault/Key Vault
- [ ] Backup automático configurado
- [ ] Monitoring e alerting configurados
- [ ] Runbook de incidentes atualizado
- [ ] Aprovação de stakeholders
- [ ] Plano de rollback documentado
- [ ] Database migrations testadas em staging

---

## 🆘 Troubleshooting por Ambiente

### Development

```bash
# Serviço não sobe
docker-compose logs backend

# Limpar e recomeçar
docker-compose down -v
docker-compose up -d

# Ver recursos
docker stats
```

### Staging (K3s)

```bash
# Pod crashando
kubectl logs -n optiflow-staging deployment/backend
kubectl describe pod -n optiflow-staging backend-xxx

# Restart
kubectl rollout restart deployment/backend -n optiflow-staging

# Debug
kubectl exec -it -n optiflow-staging deployment/backend -- bash
```

### Production (Azure AKS)

```bash
# Alertas no PagerDuty
# 1. Ver Grafana
# 2. Verificar Prometheus alerts
# 3. Ver logs: kubectl logs

# Rollback
kubectl rollout undo deployment/backend -n optiflow-prod

# Scale manual (emergência)
kubectl scale deployment/backend --replicas=10 -n optiflow-prod
```

---

## 📚 Documentação Relacionada

- **[DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md)** - Guia completo Docker Compose (development)
- **[INFRASTRUCTURE_GUIDE.md](INFRASTRUCTURE_GUIDE.md)** - Arquitetura completa (todos ambientes)
- **[monitoring/README.md](infrastructure/kubernetes/monitoring/README.md)** - Monitoramento (staging/production)

---

**Próximo passo**: Comece com Development, depois configure Staging quando precisar testar antes de produção! 🚀
