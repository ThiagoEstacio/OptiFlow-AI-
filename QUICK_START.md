# OptiFlow - Quick Start ⚡

## 🚀 Em 3 Comandos

```bash
# 1. Entre no diretório
cd /home/thiestacio/OptiFlow-AI-

# 2. Inicie tudo
./dev.sh start

# 3. Acesse
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000/docs
```

**Pronto!** 🎉

---

## 📋 Comandos Mais Usados

```bash
# Ver logs em tempo real
./dev.sh logs backend

# Reiniciar um serviço
./dev.sh restart backend

# Ver status
./dev.sh status

# Parar tudo
./dev.sh stop

# Help completo
./dev.sh help
```

---

## 🌐 Acesso aos Serviços

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | - |
| **Backend API** | http://localhost:8000/docs | - |
| **Grafana** | http://localhost:3001 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **Kafka UI** | http://localhost:8090 | - |
| **MLflow** | http://localhost:5000 | - |
| **RabbitMQ** | http://localhost:15672 | optiflow / optiflow_password |

---

## 🐛 Problemas?

### Serviço não sobe

```bash
# Ver logs
./dev.sh logs backend

# Rebuild
./dev.sh build backend
./dev.sh restart backend
```

### Porta já em uso

```bash
# Exemplo: se 8000 está em uso
# Edite docker-compose.yml:
ports:
  - "8001:8000"  # Ao invés de "8000:8000"
```

### Limpar tudo e começar do zero

```bash
./dev.sh clean
./dev.sh start
```

---

## 📚 Documentação Completa

- **[DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md)** - Guia completo Docker Compose
- **[INFRASTRUCTURE_GUIDE.md](INFRASTRUCTURE_GUIDE.md)** - Arquitetura completa
- **[monitoring/README.md](infrastructure/kubernetes/monitoring/README.md)** - Monitoramento

---

## 🔧 Desenvolvimento

### Mudou código do Backend?

```bash
# Opção 1: Restart rápido (hot reload já configurado)
./dev.sh restart backend

# Opção 2: Rebuild completo (mudou dependências)
./dev.sh build backend
./dev.sh restart backend
```

### Mudou código do Frontend?

Hot reload já configurado! Mudanças aparecem automaticamente.

### Mudou código do Gateway?

```bash
./dev.sh restart gateway
./dev.sh logs gateway
```

### Rodar migrações do banco

```bash
./dev.sh db migrate
```

### Rodar testes

```bash
./dev.sh test backend
```

### Entrar em um container

```bash
./dev.sh shell backend
# Dentro do container:
# python     (shell Python)
# ls -la     (ver arquivos)
# env        (ver variáveis)
```

---

## 📊 Monitoramento

### Grafana (Dashboards)

```
URL: http://localhost:3001
Login: admin / admin

Dashboards disponíveis:
- OptiFlow System Overview
- OptiFlow Performance Metrics
- OptiFlow ML Metrics
```

### Prometheus (Métricas)

```
URL: http://localhost:9090

Queries úteis:
- up{job="optiflow-backend"}
- rate(http_requests_total[5m])
- process_resident_memory_bytes
```

### Kafka UI

```
URL: http://localhost:8090

Ver:
- Topics criados
- Mensagens em tempo real
- Consumer groups
- 3 brokers rodando
```

---

## 🎯 Próximos Passos

Agora que está rodando:

1. **Explore o Backend API**
   - http://localhost:8000/docs
   - Teste os endpoints

2. **Configure Dashboards no Grafana**
   - http://localhost:3001
   - Explore métricas

3. **Veja Documentação Completa**
   - [DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md)

---

## 💡 Dicas

### Aliases úteis

Adicione ao `~/.bashrc`:

```bash
alias dc='docker-compose'
alias dcup='./dev.sh start'
alias dcdown='./dev.sh stop'
alias dclogs='./dev.sh logs'
```

### Apenas infraestrutura

Se quiser rodar app localmente (fora do Docker):

```bash
# Subir apenas DBs e message brokers
./dev.sh only-infra

# Em outro terminal
cd backend
python -m uvicorn app.main:app --reload
```

---

**Dúvidas?** Execute:
```bash
./dev.sh help
```

**Problemas?** Veja os logs:
```bash
./dev.sh logs
```

🚀 **Bom desenvolvimento!**
