# SmartPort - Guia de Deploy para Produção

Este guia cobre o processo completo de deploy do SmartPort em ambiente de produção.

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Preparação do Servidor](#preparação-do-servidor)
3. [Configuração](#configuração)
4. [Deploy](#deploy)
5. [Verificação](#verificação)
6. [Backup e Restore](#backup-e-restore)
7. [Monitoramento](#monitoramento)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Pré-requisitos

### Hardware Mínimo Recomendado

- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disco**: 100 GB SSD
- **Rede**: 100 Mbps

### Hardware Recomendado para Produção

- **CPU**: 8+ cores
- **RAM**: 16+ GB
- **Disco**: 250+ GB SSD
- **Rede**: 1 Gbps

### Software Necessário

- Ubuntu 20.04+ ou Debian 11+
- Docker 20.10+
- Docker Compose 2.0+
- Git
- Nginx (para SSL)

---

## 🖥️ Preparação do Servidor

### 1. Atualizar Sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar Docker

```bash
# Instalar dependências
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Adicionar repositório Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Verificar instalação
docker --version
docker compose version
```

### 3. Instalar Docker Compose (standalone)

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

### 4. Configurar Firewall

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

---

## ⚙️ Configuração

### 1. Clonar Repositório

```bash
cd /opt
sudo git clone https://github.com/yourorg/smartport.git
cd smartport
sudo chown -R $USER:$USER .
```

### 2. Configurar Variáveis de Ambiente

```bash
# Copiar exemplo de configuração
cp .env.prod.example .env.prod

# Editar configurações
nano .env.prod
```

**IMPORTANTE**: Configure as seguintes variáveis:

```bash
# Segurança - GERE VALORES ÚNICOS!
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
GATEWAY_API_KEY=$(openssl rand -hex 32)

# Database - USE SENHAS FORTES!
POSTGRES_PASSWORD=$(openssl rand -base64 32)
INFLUX_PASSWORD=$(openssl rand -base64 32)
INFLUX_TOKEN=$(openssl rand -hex 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# CORS - SEU DOMÍNIO!
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Frontend
VITE_API_URL=https://api.yourdomain.com
```

### 3. Configurar SSL (Let's Encrypt)

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obter certificado
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Certificados estarão em:
# /etc/letsencrypt/live/yourdomain.com/
```

### 4. Configurar Nginx (Reverse Proxy)

Criar `/opt/smartport/nginx/nginx.prod.conf`:

```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:80;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com api.yourdomain.com;
    return 301 https://$host$request_uri;
}

# Frontend
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Backend API
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
    limit_req zone=api_limit burst=200 nodelay;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS headers (handled by backend)
        proxy_hide_header Access-Control-Allow-Origin;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 🚀 Deploy

### Deploy Automático (Recomendado)

```bash
cd /opt/smartport
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

O script irá:
1. Validar pré-requisitos
2. Criar backup do banco atual
3. Baixar/construir imagens Docker
4. Parar containers antigos
5. Iniciar novos containers
6. Executar migrações do banco
7. Verificar health checks
8. Exibir status

### Deploy Manual

```bash
# 1. Backup
./scripts/backup.sh

# 2. Build images
docker-compose -f docker-compose.prod.yml build

# 3. Start services
docker-compose -f docker-compose.prod.yml up -d

# 4. Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 5. Check status
docker-compose -f docker-compose.prod.yml ps
```

---

## ✅ Verificação

### 1. Verificar Containers

```bash
docker-compose -f docker-compose.prod.yml ps
```

Todos os serviços devem estar "Up" e "healthy".

### 2. Verificar Logs

```bash
# Todos os serviços
docker-compose -f docker-compose.prod.yml logs -f

# Serviço específico
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f gateway
```

### 3. Testar Endpoints

```bash
# Health check
curl https://api.yourdomain.com/health

# API docs
curl https://api.yourdomain.com/docs

# Frontend
curl https://yourdomain.com
```

### 4. Verificar Databases

```bash
# PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres psql -U smartport_prod -d smartport_prod -c "\dt"

# InfluxDB
docker-compose -f docker-compose.prod.yml exec influxdb influx ping

# Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli -a $REDIS_PASSWORD ping
```

---

## 💾 Backup e Restore

### Backup Manual

```bash
./scripts/backup.sh
```

Backups são salvos em `./backups/`:
- PostgreSQL: `./backups/postgres/`
- InfluxDB: `./backups/influxdb/`

### Backup Automático (Cron)

```bash
# Editar crontab
crontab -e

# Adicionar linha (backup diário às 2h da manhã)
0 2 * * * cd /opt/smartport && ./scripts/backup.sh >> /var/log/smartport-backup.log 2>&1
```

### Restore

```bash
# Interativo
./scripts/restore.sh

# Restore automático (latest)
./scripts/restore.sh --latest

# Restore específico
./scripts/restore.sh --postgres backups/postgres/smartport_postgres_20241028_120000.sql.gz
```

---

## 📊 Monitoramento

### Prometheus & Grafana

Acessar:
- Prometheus: `http://server-ip:9090`
- Grafana: `http://server-ip:3000` (admin/admin)

### Logs Centralizados

```bash
# View logs em tempo real
docker-compose -f docker-compose.prod.yml logs -f --tail=100

# Export logs
docker-compose -f docker-compose.prod.yml logs > smartport-logs.txt
```

### Alertas

Configure alertas no Grafana para:
- CPU > 80%
- Memória > 90%
- Disco > 85%
- Containers down
- Alta taxa de erros

---

## 🔧 Troubleshooting

### Container não inicia

```bash
# Ver logs
docker-compose -f docker-compose.prod.yml logs [service]

# Restart service
docker-compose -f docker-compose.prod.yml restart [service]
```

### Erro de conexão com banco

```bash
# Verificar se PostgreSQL está rodando
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Verificar variáveis de ambiente
docker-compose -f docker-compose.prod.yml exec backend env | grep DATABASE
```

### Performance lenta

```bash
# Ver uso de recursos
docker stats

# Ajustar workers do backend no docker-compose.prod.yml
# CMD ["uvicorn", "app.main:app", "--workers", "8"]
```

### Rollback

```bash
# Parar versão atual
docker-compose -f docker-compose.prod.yml down

# Restore backup
./scripts/restore.sh --latest

# Iniciar versão anterior
git checkout [previous-version]
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔄 Atualização

```bash
# 1. Pull latest code
git pull origin main

# 2. Deploy
./scripts/deploy.sh
```

---

## 📞 Suporte

- Documentação: https://docs.smartport.io
- Issues: https://github.com/yourorg/smartport/issues
- Email: support@smartport.io

---

## 📝 Checklist de Produção

- [ ] Servidor configurado com requisitos mínimos
- [ ] Docker e Docker Compose instalados
- [ ] Firewall configurado
- [ ] SSL/TLS configurado
- [ ] Variáveis de ambiente configuradas com senhas fortes
- [ ] Backup automático configurado
- [ ] Monitoramento ativo
- [ ] Alertas configurados
- [ ] Documentação de acesso disponível
- [ ] Plano de rollback testado
- [ ] Testes de carga executados
- [ ] Logs centralizados
- [ ] DNS configurado
- [ ] Rate limiting ativo
- [ ] CORS configurado corretamente

---

**Status**: Pronto para Produção ✅
**Versão**: 1.0.0
**Data**: Outubro 2024
