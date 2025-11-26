# OptiFlow - Guia Docker Compose (Desenvolvimento Local)

## 🎯 Visão Geral

Docker Compose é a ferramenta **recomendada para desenvolvimento local** do OptiFlow. Este guia mostra como usar de forma eficiente.

### Por que Docker Compose?

✅ **Simples e rápido** - `docker-compose up` e tudo funciona
✅ **Ambiente completo** - Todos os serviços em um comando
✅ **Isolamento** - Não polui sua máquina
✅ **Reproduzível** - Mesmo ambiente para toda equipe
✅ **Fácil debug** - Logs claros, restart individual de serviços

---

## 🚀 Quick Start (3 comandos)

```bash
# 1. Clone e entre no diretório (se ainda não fez)
cd /home/thiestacio/OptiFlow-AI-

# 2. Suba todos os serviços
docker-compose up -d

# 3. Verifique que está tudo rodando
docker-compose ps
```

**Pronto!** 🎉 Você tem:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Grafana: http://localhost:3001 (admin/admin)
- Prometheus: http://localhost:9090
- Kafka UI: http://localhost:8090
- MLflow: http://localhost:5000

---

## 📦 Arquitetura dos Serviços

```
┌─────────────────────────────────────────────────────────────────┐
│                    OPTIFLOW DOCKER COMPOSE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────── OT NETWORK ────────────────────────┐   │
│  │  (Isolada - sem acesso externo)                         │   │
│  │                                                          │   │
│  │  ┌──────────────┐                                       │   │
│  │  │ OPC UA Server│  :4840                                │   │
│  │  │ (Simulator)  │                                       │   │
│  │  └──────┬───────┘                                       │   │
│  │         │                                                │   │
│  │         │                                                │   │
│  │  ┌──────▼───────┐                                       │   │
│  │  │   Gateway    │  (ponte OT ↔ IT)                     │   │
│  │  │              │                                       │   │
│  └──┴──────────────┴───────────────────────────────────────┘   │
│         │                                                       │
│         │ Envia dados via Kafka                                │
│         ▼                                                       │
│  ┌───────────────────── IT NETWORK ────────────────────────┐   │
│  │  (Com acesso externo)                                   │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │ Message Brokers                                  │   │   │
│  │  │  • Kafka (3 brokers) :9092,:9093,:9096          │   │   │
│  │  │  • RabbitMQ         :5672, :15672 (UI)          │   │   │
│  │  │  • Zookeeper        :2181                        │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │ Databases                                        │   │   │
│  │  │  • PostgreSQL   :5432  (metadata, relacional)   │   │   │
│  │  │  • InfluxDB     :8086  (timeseries)             │   │   │
│  │  │  • Redis        :6379  (cache, pub/sub)         │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │ Backend Services                                 │   │   │
│  │  │  • Backend API       :8000                       │   │   │
│  │  │  • Celery Worker     (background tasks)          │   │   │
│  │  │  • Celery Beat       (scheduler)                 │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │ AI & ML                                          │   │   │
│  │  │  • Ollama      :11435  (LLM local - RTX 4060)   │   │   │
│  │  │  • MLflow      :5000   (model tracking)          │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │ Monitoring                                       │   │   │
│  │  │  • Prometheus  :9090   (metrics)                 │   │   │
│  │  │  • Grafana     :3001   (dashboards)              │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │ Frontend                                         │   │   │
│  │  │  • React App   :3000   (UI)                      │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │ Security                                         │   │   │
│  │  │  • Vault       :8200   (secrets management)      │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Comandos Essenciais

### Operações Básicas

```bash
# ══════════════════════════════════════════════════════════
# INICIAR SERVIÇOS
# ══════════════════════════════════════════════════════════

# Subir TUDO (modo background)
docker-compose up -d

# Subir TUDO e ver logs em tempo real
docker-compose up

# Subir apenas serviços específicos
docker-compose up -d postgres influxdb redis  # Apenas DBs
docker-compose up -d backend frontend         # Apenas app


# ══════════════════════════════════════════════════════════
# STATUS E LOGS
# ══════════════════════════════════════════════════════════

# Ver status de todos os serviços
docker-compose ps

# Ver logs de TODOS os serviços
docker-compose logs

# Ver logs de serviço específico
docker-compose logs backend
docker-compose logs gateway
docker-compose logs -f frontend  # -f = follow (tempo real)

# Ver últimas 50 linhas de logs
docker-compose logs --tail=50 backend

# Logs de múltiplos serviços
docker-compose logs backend gateway


# ══════════════════════════════════════════════════════════
# PARAR E REINICIAR
# ══════════════════════════════════════════════════════════

# Parar TODOS os serviços (mas manter volumes/dados)
docker-compose stop

# Parar serviço específico
docker-compose stop backend

# Reiniciar TODOS
docker-compose restart

# Reiniciar serviço específico
docker-compose restart backend

# Parar E REMOVER containers (dados persistem em volumes)
docker-compose down

# Parar, remover containers E VOLUMES (⚠️ APAGA DADOS!)
docker-compose down -v


# ══════════════════════════════════════════════════════════
# REBUILD (após mudar código)
# ══════════════════════════════════════════════════════════

# Rebuild de TODOS os serviços
docker-compose build

# Rebuild de serviço específico
docker-compose build backend

# Rebuild SEM cache (força instalação completa)
docker-compose build --no-cache backend

# Rebuild e reinicia
docker-compose up -d --build backend


# ══════════════════════════════════════════════════════════
# EXECUÇÃO DE COMANDOS
# ══════════════════════════════════════════════════════════

# Executar comando em container rodando
docker-compose exec backend bash                    # Shell interativo
docker-compose exec postgres psql -U optiflow       # PostgreSQL CLI
docker-compose exec redis redis-cli -a optiflow_redis_password

# Executar comando único
docker-compose exec backend python -m pytest        # Rodar testes
docker-compose exec backend alembic upgrade head    # Migração DB


# ══════════════════════════════════════════════════════════
# LIMPEZA
# ══════════════════════════════════════════════════════════

# Parar tudo e limpar
docker-compose down

# Limpar volumes órfãos
docker volume prune

# Limpar containers parados
docker container prune

# Limpar imagens não usadas
docker image prune
```

---

## 🔧 Fluxos de Trabalho Comuns

### 1. Primeira Vez Rodando o Projeto

```bash
# 1. Clonar repositório (se ainda não fez)
git clone <repo-url>
cd OptiFlow-AI-

# 2. Criar arquivo .env (se necessário)
cp .env.example .env

# 3. Baixar imagens e subir serviços
docker-compose up -d

# 4. Esperar health checks (30-60 segundos)
# Você pode acompanhar:
docker-compose logs -f

# 5. Verificar que está tudo UP
docker-compose ps

# 6. Acessar aplicação
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

### 2. Começar o Dia de Trabalho

```bash
# Subir tudo
docker-compose up -d

# Ver se está tudo rodando
docker-compose ps

# Ver logs do que você está trabalhando
docker-compose logs -f backend
```

### 3. Mudou Código do Backend

```bash
# Opção 1: Hot reload (se configurado)
# → O backend reinicia automaticamente

# Opção 2: Restart manual (mais rápido)
docker-compose restart backend

# Opção 3: Rebuild completo (se mudou dependências)
docker-compose up -d --build backend

# Ver logs
docker-compose logs -f backend
```

### 4. Mudou Código do Frontend

```bash
# Opção 1: Hot reload Vite (já configurado)
# → Mudanças aparecem automaticamente no browser

# Opção 2: Rebuild produção
docker-compose up -d --build frontend
```

### 5. Mudou Código do Gateway

```bash
# Restart
docker-compose restart gateway

# Ou rebuild
docker-compose up -d --build gateway

# Ver logs
docker-compose logs -f gateway
```

### 6. Testar com Dados Limpos

```bash
# ⚠️ ATENÇÃO: Isso APAGA TODOS OS DADOS!

# 1. Parar e remover volumes
docker-compose down -v

# 2. Subir novamente (cria volumes novos)
docker-compose up -d

# 3. Rodar migrações/seeds se necessário
docker-compose exec backend alembic upgrade head
```

### 7. Debug de Problemas

```bash
# Ver logs de TODOS os serviços
docker-compose logs

# Ver logs de serviço específico
docker-compose logs backend --tail=100

# Entrar no container para debug
docker-compose exec backend bash
# Dentro do container:
# - python  (shell Python)
# - ls -la  (ver arquivos)
# - env     (ver variáveis ambiente)
# - curl http://postgres:5432  (testar conexões)

# Ver uso de recursos
docker stats

# Inspecionar container
docker-compose exec backend ps aux    # Processos rodando
docker-compose exec backend df -h     # Disco
docker-compose exec backend free -m   # Memória
```

### 8. Terminar o Dia

```bash
# Opção 1: Deixar rodando (consome RAM)
# (não faz nada)

# Opção 2: Parar tudo (libera RAM, mantém dados)
docker-compose stop

# Opção 3: Parar e remover containers (libera mais recursos)
docker-compose down
```

---

## 🐛 Troubleshooting

### Problema: Serviço não sobe

```bash
# Ver logs detalhados
docker-compose logs backend

# Possíveis causas:
# 1. Dependência não subiu ainda
docker-compose ps  # Veja se postgres/redis estão UP

# 2. Porta já em uso
# Erro: "port is already allocated"
# Solução: Mude a porta no docker-compose.yml
# Exemplo: "8001:8000" ao invés de "8000:8000"

# 3. Build falhou
docker-compose build --no-cache backend

# 4. Problema de permissão
sudo chown -R $USER:$USER .
```

### Problema: Backend não conecta no banco

```bash
# 1. Verificar se postgres está rodando
docker-compose ps postgres

# 2. Ver logs do postgres
docker-compose logs postgres

# 3. Testar conexão manualmente
docker-compose exec backend bash
# Dentro do container:
nc -zv postgres 5432  # Deve retornar "succeeded"

# 4. Verificar variáveis de ambiente
docker-compose exec backend env | grep DATABASE_URL
```

### Problema: "Unhealthy" no docker-compose ps

```bash
# Ver por que falhou o health check
docker-compose logs <service-name>

# Exemplo: postgres unhealthy
docker-compose logs postgres

# Solução comum: Esperar mais tempo
# Health checks levam alguns segundos para passar

# Forçar restart
docker-compose restart postgres
```

### Problema: Performance lenta

```bash
# Ver uso de recursos
docker stats

# Possíveis soluções:

# 1. Limpar volumes não usados
docker volume prune

# 2. Limpar imagens antigas
docker image prune -a

# 3. Reiniciar Docker Desktop (se no Windows/Mac)

# 4. Aumentar recursos do Docker Desktop
# Settings → Resources → CPUs/Memory
```

### Problema: Gateway não se conecta ao OPC UA

```bash
# 1. Ver logs do gateway
docker-compose logs gateway

# 2. Ver logs do OPC UA simulator
docker-compose logs opcua-server

# 3. Verificar se estão na mesma rede
docker network inspect optiflow-ai-_ot-network

# 4. Testar conectividade
docker-compose exec gateway nc -zv opcua-server 4840
```

### Problema: Frontend não carrega

```bash
# 1. Ver logs
docker-compose logs frontend

# 2. Verificar build
docker-compose build frontend

# 3. Limpar cache do browser
# Ctrl+Shift+R (hard refresh)

# 4. Verificar VITE_API_URL
docker-compose exec frontend env | grep VITE
```

---

## ⚡ Otimizações para Dev

### 1. Criar Aliases (atalhos)

Adicione ao seu `~/.bashrc` ou `~/.zshrc`:

```bash
# OptiFlow aliases
alias dc='docker-compose'
alias dcup='docker-compose up -d'
alias dcdown='docker-compose down'
alias dcps='docker-compose ps'
alias dclogs='docker-compose logs -f'
alias dcrestart='docker-compose restart'

# Usar:
# dcup           # ao invés de docker-compose up -d
# dclogs backend # ao invés de docker-compose logs -f backend
```

### 2. Script de Desenvolvimento

Crie `dev.sh` na raiz do projeto:

```bash
#!/bin/bash
# Script de desenvolvimento rápido

case "$1" in
  start)
    echo "🚀 Subindo OptiFlow..."
    docker-compose up -d
    echo "✅ Serviços iniciados!"
    echo "📊 Frontend: http://localhost:3000"
    echo "🔧 Backend: http://localhost:8000/docs"
    echo "📈 Grafana: http://localhost:3001"
    ;;
  stop)
    echo "🛑 Parando OptiFlow..."
    docker-compose stop
    echo "✅ Serviços parados!"
    ;;
  restart)
    echo "🔄 Reiniciando OptiFlow..."
    docker-compose restart
    echo "✅ Serviços reiniciados!"
    ;;
  logs)
    docker-compose logs -f ${2:-backend}
    ;;
  clean)
    echo "🧹 Limpando OptiFlow..."
    docker-compose down -v
    docker volume prune -f
    echo "✅ Limpeza completa!"
    ;;
  *)
    echo "Uso: ./dev.sh {start|stop|restart|logs|clean}"
    ;;
esac
```

Usar:
```bash
chmod +x dev.sh
./dev.sh start
./dev.sh logs backend
./dev.sh clean
```

### 3. Apenas Infraestrutura (sem app)

Se quiser apenas bancos de dados:

```bash
# Subir apenas infra
docker-compose up -d postgres influxdb redis rabbitmq kafka-1

# Rodar app localmente (fora do Docker)
cd backend
python -m uvicorn app.main:app --reload
```

---

## 📊 Monitoramento

### Grafana

```bash
# Acessar: http://localhost:3001
# Login: admin / admin

# Dashboards disponíveis:
# - OptiFlow System Overview
# - OptiFlow Performance Metrics
# - OptiFlow ML Metrics
```

### Prometheus

```bash
# Acessar: http://localhost:9090

# Queries úteis:
# - up{job="optiflow-backend"}           # Backend está up?
# - rate(http_requests_total[5m])        # Requests/segundo
# - process_resident_memory_bytes        # Uso de memória
```

### Kafka UI

```bash
# Acessar: http://localhost:8090

# Ver:
# - Topics
# - Mensagens
# - Consumer groups
# - Brokers (3 brokers no cluster)
```

### cAdvisor (Container Stats)

```bash
# Acessar: http://localhost:8081

# Ver:
# - CPU usage por container
# - Memory usage
# - Network I/O
# - Disk I/O
```

---

## 🔒 Segurança

### Redes Isoladas (OT/IT)

O docker-compose já configura segurança com **2 redes isoladas**:

```yaml
networks:
  # OT Network: Gateway ↔ PLCs (ISOLADA, sem internet)
  ot-network:
    internal: true  # ← Sem acesso externo

  # IT Network: Backend ↔ Frontend ↔ Databases
  it-network:
```

**Por quê?**
- PLCs ficam isolados (segurança industrial ISA-99/IEC 62443)
- Gateway funciona como "diodo de dados" (one-way: OT → IT)
- Backend/Frontend não acessam diretamente PLCs

### Vault (Secrets Management)

```bash
# Acessar Vault
docker-compose exec vault vault status

# Login
docker-compose exec vault vault login
# Token: optiflow-dev-root-token

# Ver secrets
docker-compose exec vault vault kv list secret/
```

---

## 📦 Volumes e Dados

### Volumes Persistentes

```bash
# Ver todos os volumes
docker volume ls | grep optiflow

# Volumes criados:
# - postgres_data      (banco relacional)
# - influxdb_data      (timeseries)
# - redis_data         (cache)
# - rabbitmq_data      (message queue)
# - kafka_1_data       (streaming - broker 1)
# - kafka_2_data       (streaming - broker 2)
# - kafka_3_data       (streaming - broker 3)
# - backend_mlflow     (ML models)
# - gateway_data       (buffer local)
# - grafana_data       (dashboards)
# - prometheus_data    (métricas)

# Inspecionar volume
docker volume inspect optiflow-ai-_postgres_data

# Backup de volume
docker run --rm \
  -v optiflow-ai-_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore de volume
docker run --rm \
  -v optiflow-ai-_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

---

## 🚀 Performance

### Resource Limits

O docker-compose já define limits para evitar OOM:

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '4.0'
        memory: 4G
      reservations:
        cpus: '2.0'
        memory: 2G
```

### Ver Uso Atual

```bash
# Uso de recursos em tempo real
docker stats

# Ver apenas serviços OptiFlow
docker stats $(docker ps --filter name=optiflow -q)
```

### Otimizar

```bash
# 1. Limpar regularmente
docker system prune -a  # Remove tudo não usado

# 2. Usar menos brokers Kafka (dev)
# Comentar kafka-2 e kafka-3 no docker-compose.yml

# 3. Desabilitar serviços não usados
docker-compose up -d postgres redis backend frontend
# (não sobe Kafka, RabbitMQ, etc)
```

---

## 📚 Próximos Passos

Agora que você domina Docker Compose local, considere:

1. **CI/CD** - Automatizar testes em cada commit
2. **K3s/Staging** - Ambiente que simula produção
3. **Cloud Deploy** - Azure AKS quando tiver clientes

**Documentação relacionada**:
- [INFRASTRUCTURE_GUIDE.md](INFRASTRUCTURE_GUIDE.md) - Guia completo de infraestrutura
- [infrastructure/kubernetes/monitoring/README.md](infrastructure/kubernetes/monitoring/README.md) - Monitoramento avançado

---

**Dúvidas?** Veja os logs:
```bash
docker-compose logs -f
```

**Quer ajuda?** Compartilhe os logs do serviço com problema! 🚀
