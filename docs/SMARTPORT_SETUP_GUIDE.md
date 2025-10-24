# Guia Completo de Setup e Testes - SmartPort

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Instalação](#instalação)
4. [Configuração](#configuração)
5. [Inicialização dos Serviços](#inicialização-dos-serviços)
6. [Verificação do Sistema](#verificação-do-sistema)
7. [Testando o SmartPort](#testando-o-smartport)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

**SmartPort** é uma solução vertical da plataforma OptiFlow AI para monitoramento e otimização de operações portuárias. O sistema coleta dados de dispositivos IoT industriais em tempo real, realiza análise preditiva e fornece dashboards de visualização.

### Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE CAMPO                          │
│  Dispositivos Portuários (PLCs, Sensores, RTUs)            │
└─────────────────┬───────────────────────────────────────────┘
                  │ OPC UA, Modbus, MQTT, S7, Ethernet/IP
┌─────────────────▼───────────────────────────────────────────┐
│                    GATEWAY IoT                               │
│  Coleta e normalização de dados industriais                │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP/WebSocket
┌─────────────────▼───────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                     │
│  Lógica de negócio, autenticação, processamento            │
└─────────────────┬───────────────────────────────────────────┘
                  │
      ┌───────────┼──────────┬─────────────┐
      ▼           ▼          ▼             ▼
┌──────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐
│PostgreSQL│ │InfluxDB  │ │  Redis  │ │ RabbitMQ │
│(Metadata)│ │(Séries   │ │ (Cache) │ │ (Queue)  │
│          │ │Temporais)│ │         │ │          │
└──────────┘ └──────────┘ └─────────┘ └──────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                  FRONTEND (React)                            │
│  Dashboards, configuração, visualização                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Pré-requisitos

### Opção 1: Docker (Recomendado)

- **Docker**: v20.10 ou superior
- **Docker Compose**: v2.0 ou superior
- **RAM**: Mínimo 8GB (recomendado 16GB)
- **Disco**: 10GB livres

```bash
# Verificar instalação do Docker
docker --version
docker-compose --version
```

### Opção 2: Instalação Local

#### Sistema Operacional
- Linux (Ubuntu 20.04+), macOS (11+), ou Windows 10/11 com WSL2

#### Software Base
- **Python**: 3.11 ou superior
- **Node.js**: 18.x ou superior
- **npm**: 9.x ou superior

```bash
# Verificar versões
python --version  # ou python3 --version
node --version
npm --version
```

#### Bancos de Dados (para instalação local)
- **PostgreSQL**: 15+
- **InfluxDB**: 2.7+
- **Redis**: 7.0+
- **RabbitMQ**: 3.12+

---

## 📦 Instalação

### Passo 1: Clonar o Repositório

```bash
# Clone o repositório
git clone <repository-url>
cd OptiFlow-AI-

# Checkout para a branch do SmartPort
git checkout claude/smartport-setup-guide-011CUSkHf6CqBBawpjAtvGcX
```

### Passo 2: Instalação com Docker (Recomendado)

#### 2.1 Verificar Estrutura do Projeto

```bash
# Listar arquivos principais
ls -la
# Deve conter: docker-compose.yml, backend/, frontend/, gateway/, docs/
```

#### 2.2 Revisar Configuração do Docker Compose

```bash
# Visualizar serviços disponíveis
cat docker-compose.yml | grep "^  [a-z]"
```

**Serviços incluídos:**
1. `postgres` - Banco de dados relacional (porta 5432)
2. `influxdb` - Banco de séries temporais (porta 8086)
3. `redis` - Cache e sessões (porta 6379)
4. `rabbitmq` - Fila de mensagens (porta 5672, 15672)
5. `backend` - API FastAPI (porta 8000)
6. `celery-worker` - Worker de tarefas assíncronas
7. `celery-beat` - Scheduler de tarefas
8. `gateway` - Gateway de comunicação IoT (porta 8001)
9. `frontend` - Interface React (porta 5173)
10. `mlflow` - Rastreamento de modelos ML (porta 5000)
11. `grafana` - Dashboards de monitoramento (porta 3000)

#### 2.3 Iniciar Serviços

```bash
# Construir e iniciar todos os serviços
docker-compose up -d

# Acompanhar logs de todos os serviços
docker-compose logs -f

# Acompanhar logs de um serviço específico
docker-compose logs -f backend
docker-compose logs -f gateway
docker-compose logs -f frontend
```

#### 2.4 Aguardar Inicialização

```bash
# Verificar status dos containers (todos devem estar "Up")
docker-compose ps

# Aguardar até que todos os serviços estejam saudáveis
# Isso pode levar 2-3 minutos na primeira execução
```

### Passo 3: Instalação Local (Alternativa)

#### 3.1 Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Linux/macOS:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env  # Se existir, caso contrário criar .env
nano .env  # Editar configurações
```

**Exemplo de .env para Backend:**
```env
# Database
DATABASE_URL=postgresql+asyncpg://optiflow:optiflow_password@localhost:5432/optiflow

# InfluxDB
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=optiflow_admin_token
INFLUXDB_ORG=optiflow
INFLUXDB_BUCKET=timeseries

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

#### 3.2 Gateway

```bash
cd gateway

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS

# Instalar dependências
pip install -r requirements.txt

# Configurar ambiente
cp .env.example .env  # Se existir
```

#### 3.3 Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Configurar ambiente
cp .env.example .env  # Se existir
```

**Exemplo de .env para Frontend:**
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

#### 3.4 Iniciar Bancos de Dados

```bash
# PostgreSQL (se não estiver rodando)
sudo systemctl start postgresql
# ou via Docker:
docker run -d --name postgres \
  -e POSTGRES_USER=optiflow \
  -e POSTGRES_PASSWORD=optiflow_password \
  -e POSTGRES_DB=optiflow \
  -p 5432:5432 \
  postgres:15

# InfluxDB
docker run -d --name influxdb \
  -p 8086:8086 \
  -e DOCKER_INFLUXDB_INIT_MODE=setup \
  -e DOCKER_INFLUXDB_INIT_USERNAME=admin \
  -e DOCKER_INFLUXDB_INIT_PASSWORD=optiflow_password \
  -e DOCKER_INFLUXDB_INIT_ORG=optiflow \
  -e DOCKER_INFLUXDB_INIT_BUCKET=timeseries \
  -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=optiflow_admin_token \
  influxdb:2.7

# Redis
docker run -d --name redis -p 6379:6379 redis:7

# RabbitMQ
docker run -d --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=optiflow \
  -e RABBITMQ_DEFAULT_PASS=optiflow_password \
  rabbitmq:3.12-management
```

---

## ⚙️ Configuração

### 1. Configuração do Backend

#### 1.1 Criar Banco de Dados

```bash
# Acessar container do PostgreSQL (se usando Docker)
docker exec -it optiflow-ai--postgres-1 psql -U optiflow

# Ou localmente
psql -U optiflow -h localhost
```

```sql
-- Verificar banco de dados
\l

-- Conectar ao banco optiflow
\c optiflow

-- Listar tabelas (após migrations)
\dt
```

#### 1.2 Executar Migrations

```bash
# Dentro do diretório backend com ambiente virtual ativado
cd backend

# Se usando Alembic (verificar se existe pasta alembic/)
alembic upgrade head

# Verificar tabelas criadas
docker exec -it optiflow-ai--postgres-1 psql -U optiflow -d optiflow -c "\dt"
```

**Tabelas esperadas:**
- organizations
- sites
- devices
- tags
- users
- alarm_definitions
- alarm_events
- ml_models
- predictions

### 2. Configuração do InfluxDB

```bash
# Acessar interface web
open http://localhost:8086

# Credenciais padrão:
# Username: admin
# Password: optiflow_password
# Organization: optiflow
# Bucket: timeseries
```

#### 2.1 Criar Buckets Adicionais (via CLI)

```bash
# Entrar no container do InfluxDB
docker exec -it optiflow-ai--influxdb-1 /bin/bash

# Criar bucket de agregações
influx bucket create \
  --name aggregations \
  --org optiflow \
  --token optiflow_admin_token

# Criar bucket de downsampling
influx bucket create \
  --name downsampled \
  --org optiflow \
  --retention 2160h \
  --token optiflow_admin_token
```

### 3. Configuração do RabbitMQ

```bash
# Acessar interface web
open http://localhost:15672

# Credenciais:
# Username: optiflow
# Password: optiflow_password
```

**Verificar:**
- Exchanges criadas automaticamente pelo Celery
- Queues ativas
- Connections dos workers

---

## 🚀 Inicialização dos Serviços

### Opção A: Docker Compose

```bash
# Iniciar todos os serviços
docker-compose up -d

# Verificar logs
docker-compose logs -f

# Parar todos os serviços
docker-compose down

# Parar e remover volumes (CUIDADO: apaga dados!)
docker-compose down -v
```

### Opção B: Inicialização Local

#### Terminal 1: Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Saída esperada:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### Terminal 2: Celery Worker

```bash
cd backend
source venv/bin/activate
celery -A app.core.celery worker --loglevel=info
```

#### Terminal 3: Celery Beat

```bash
cd backend
source venv/bin/activate
celery -A app.core.celery beat --loglevel=info
```

#### Terminal 4: Gateway

```bash
cd gateway
source venv/bin/activate
python app/main.py
```

#### Terminal 5: Frontend

```bash
cd frontend
npm run dev
```

**Saída esperada:**
```
VITE v5.0.x ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: http://192.168.x.x:5173/
```

---

## ✅ Verificação do Sistema

### 1. Verificar Serviços Web

```bash
# Backend API (deve retornar JSON)
curl http://localhost:8000/api/v1/health

# Documentação Swagger
open http://localhost:8000/docs

# Documentação ReDoc
open http://localhost:8000/redoc

# Frontend
open http://localhost:5173

# MLflow
open http://localhost:5000

# Grafana
open http://localhost:3000
# Credenciais padrão: admin / admin
```

### 2. Verificar Bancos de Dados

#### PostgreSQL

```bash
# Via Docker
docker exec -it optiflow-ai--postgres-1 psql -U optiflow -d optiflow -c "SELECT version();"

# Contar tabelas
docker exec -it optiflow-ai--postgres-1 psql -U optiflow -d optiflow -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
```

#### InfluxDB

```bash
# Listar buckets
docker exec -it optiflow-ai--influxdb-1 \
  influx bucket list --token optiflow_admin_token --org optiflow
```

#### Redis

```bash
# Testar conexão
docker exec -it optiflow-ai--redis-1 redis-cli ping
# Resposta esperada: PONG

# Verificar info
docker exec -it optiflow-ai--redis-1 redis-cli info server
```

### 3. Verificar Logs

```bash
# Logs do Backend
docker-compose logs backend | tail -50

# Logs do Gateway
docker-compose logs gateway | tail -50

# Logs do Celery Worker
docker-compose logs celery-worker | tail -50

# Logs em tempo real de todos os serviços
docker-compose logs -f --tail=100
```

---

## 🧪 Testando o SmartPort

### 1. Criar Usuário Administrador

```bash
# Método 1: Via API (criar script Python)
cat > create_admin.py << 'EOF'
import requests

BASE_URL = "http://localhost:8000"

# Criar usuário admin
response = requests.post(
    f"{BASE_URL}/api/v1/auth/register",
    json={
        "email": "admin@smartport.com",
        "password": "Admin@123456",
        "full_name": "SmartPort Administrator",
        "is_superuser": True
    }
)

if response.status_code == 200:
    print("✓ Usuário admin criado com sucesso!")
    print(response.json())
else:
    print(f"✗ Erro: {response.status_code}")
    print(response.text)
EOF

python create_admin.py
```

### 2. Autenticar e Obter Token

```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@smartport.com&password=Admin@123456"

# Salvar resposta (deve conter access_token)
# Exemplo de resposta:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer"
# }
```

**Salvar token em variável:**
```bash
export TOKEN="seu_token_aqui"
```

### 3. Criar Organização

```bash
curl -X POST "http://localhost:8000/api/v1/organizations/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Porto de Santos",
    "description": "Terminal de containers - Santos/SP",
    "settings": {
      "timezone": "America/Sao_Paulo",
      "language": "pt-BR"
    }
  }'

# Salvar o organization_id retornado
export ORG_ID="<organization_id_retornado>"
```

### 4. Criar Site SmartPort

```bash
curl -X POST "http://localhost:8000/api/v1/sites/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Terminal T1 - Santos",
    "site_type": "smartport",
    "organization_id": "'$ORG_ID'",
    "description": "Terminal de containers automatizado",
    "address": "Av. Portuária, 1000",
    "city": "Santos",
    "state": "SP",
    "country": "Brasil",
    "postal_code": "11013-000",
    "latitude": -23.9618,
    "longitude": -46.3322,
    "timezone": "America/Sao_Paulo",
    "settings": {
      "operational_hours": "24/7",
      "max_capacity_teu": 10000,
      "berths": 4
    }
  }'

# Salvar o site_id retornado
export SITE_ID="<site_id_retornado>"
```

### 5. Criar Dispositivo (PLC Portainer Crane)

```bash
curl -X POST "http://localhost:8000/api/v1/devices/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PLC Portainer 01",
    "site_id": "'$SITE_ID'",
    "device_type": "PLC",
    "protocol": "opc_ua",
    "description": "Controlador do Portainer de Containers 01",
    "ip_address": "192.168.100.50",
    "port": 4840,
    "connection_config": {
      "endpoint": "opc.tcp://192.168.100.50:4840",
      "security_mode": "None",
      "security_policy": "None",
      "username": "",
      "password": ""
    },
    "scan_rate": 1000,
    "enabled": true,
    "settings": {
      "crane_id": "PC-01",
      "max_load_kg": 65000,
      "max_height_m": 40
    }
  }'

# Salvar o device_id retornado
export DEVICE_ID="<device_id_retornado>"
```

### 6. Criar Tags (Variáveis de Processo)

#### Tag 1: Temperatura do Motor

```bash
curl -X POST "http://localhost:8000/api/v1/tags/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PC01_Motor_Temperature",
    "device_id": "'$DEVICE_ID'",
    "description": "Temperatura do motor principal",
    "address": "ns=2;s=Crane.Motor.Temperature",
    "data_type": "float",
    "unit": "°C",
    "category": "maintenance",
    "scan_rate": 5000,
    "deadband": 0.5,
    "scaling_factor": 1.0,
    "scaling_offset": 0.0,
    "min_value": 0.0,
    "max_value": 150.0,
    "enabled": true
  }'
```

#### Tag 2: Posição do Spreader

```bash
curl -X POST "http://localhost:8000/api/v1/tags/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PC01_Spreader_Height",
    "device_id": "'$DEVICE_ID'",
    "description": "Altura atual do spreader",
    "address": "ns=2;s=Crane.Spreader.Height",
    "data_type": "float",
    "unit": "m",
    "category": "process",
    "scan_rate": 1000,
    "deadband": 0.1,
    "min_value": 0.0,
    "max_value": 40.0,
    "enabled": true
  }'
```

#### Tag 3: Status Operacional

```bash
curl -X POST "http://localhost:8000/api/v1/tags/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PC01_Operational_Status",
    "device_id": "'$DEVICE_ID'",
    "description": "Status operacional do portainer",
    "address": "ns=2;s=Crane.Status.Operational",
    "data_type": "integer",
    "category": "status",
    "scan_rate": 2000,
    "enabled": true,
    "settings": {
      "0": "Stopped",
      "1": "Running",
      "2": "Error",
      "3": "Maintenance"
    }
  }'

export TAG_ID="<tag_id_retornado>"
```

### 7. Escrever Dados de Séries Temporais

```bash
# Criar script para simular dados
cat > simulate_data.py << 'EOF'
import requests
import time
import random
from datetime import datetime

BASE_URL = "http://localhost:8000"
TOKEN = "seu_token_aqui"  # Substitua pelo token obtido

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# IDs (substitua pelos IDs criados anteriormente)
TAG_TEMPERATURE = "tag_id_temperatura"
TAG_HEIGHT = "tag_id_altura"
TAG_STATUS = "tag_id_status"

print("🚀 Iniciando simulação de dados SmartPort...")

for i in range(50):
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Temperatura (40-80°C com tendência)
    temp = 60 + random.uniform(-10, 10) + (i * 0.2)

    # Altura (0-40m)
    height = 20 + 15 * random.random()

    # Status (1=Running na maior parte do tempo)
    status = random.choices([1, 2], weights=[95, 5])[0]

    # Enviar temperatura
    requests.post(
        f"{BASE_URL}/api/v1/timeseries/write",
        headers=headers,
        json={
            "tag_id": TAG_TEMPERATURE,
            "value": round(temp, 2),
            "timestamp": timestamp
        }
    )

    # Enviar altura
    requests.post(
        f"{BASE_URL}/api/v1/timeseries/write",
        headers=headers,
        json={
            "tag_id": TAG_HEIGHT,
            "value": round(height, 2),
            "timestamp": timestamp
        }
    )

    # Enviar status
    requests.post(
        f"{BASE_URL}/api/v1/timeseries/write",
        headers=headers,
        json={
            "tag_id": TAG_STATUS,
            "value": status,
            "timestamp": timestamp
        }
    )

    print(f"✓ Amostra {i+1}/50: Temp={temp:.1f}°C, Altura={height:.1f}m, Status={status}")
    time.sleep(1)

print("✅ Simulação concluída!")
EOF

# Editar o script com seus IDs e token
nano simulate_data.py

# Executar simulação
python simulate_data.py
```

### 8. Consultar Dados de Séries Temporais

```bash
# Consultar últimos valores
curl -X GET "http://localhost:8000/api/v1/timeseries/tags/$TAG_ID/latest" \
  -H "Authorization: Bearer $TOKEN"

# Consultar histórico (últimas 24h)
curl -X GET "http://localhost:8000/api/v1/timeseries/tags/$TAG_ID/data?range=24h" \
  -H "Authorization: Bearer $TOKEN"

# Consultar estatísticas
curl -X GET "http://localhost:8000/api/v1/timeseries/tags/$TAG_ID/statistics?range=1h&aggregation=mean" \
  -H "Authorization: Bearer $TOKEN"
```

### 9. Criar Alarme

```bash
curl -X POST "http://localhost:8000/api/v1/alarms/definitions/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Temperatura Motor Alta",
    "tag_id": "'$TAG_ID'",
    "alarm_type": "high_limit",
    "severity": "high",
    "description": "Alarme quando temperatura do motor excede 85°C",
    "setpoint": 85.0,
    "deadband": 5.0,
    "delay": 10,
    "enabled": true,
    "notification_enabled": true,
    "notification_emails": ["operacao@smartport.com"],
    "message_template": "ATENÇÃO: Temperatura do motor PC-01 atingiu {value}°C (limite: {setpoint}°C)"
  }'
```

### 10. Listar Recursos Criados

```bash
# Listar organizações
curl -X GET "http://localhost:8000/api/v1/organizations/" \
  -H "Authorization: Bearer $TOKEN"

# Listar sites SmartPort
curl -X GET "http://localhost:8000/api/v1/sites/?site_type=smartport" \
  -H "Authorization: Bearer $TOKEN"

# Listar dispositivos de um site
curl -X GET "http://localhost:8000/api/v1/devices/?site_id=$SITE_ID" \
  -H "Authorization: Bearer $TOKEN"

# Listar tags de um dispositivo
curl -X GET "http://localhost:8000/api/v1/tags/?device_id=$DEVICE_ID" \
  -H "Authorization: Bearer $TOKEN"

# Listar alarmes ativos
curl -X GET "http://localhost:8000/api/v1/alarms/events/?active=true" \
  -H "Authorization: Bearer $TOKEN"
```

### 11. Testar Frontend

```bash
# Acessar frontend
open http://localhost:5173

# Fazer login com as credenciais criadas
# Email: admin@smartport.com
# Senha: Admin@123456
```

**Nota:** O frontend atual está em estado de "Coming Soon", então você verá uma página de placeholder. O desenvolvimento da UI será feito nas próximas fases.

### 12. Testar Gateway (Simulação)

```bash
# Verificar logs do Gateway
docker-compose logs gateway

# Testar endpoint de health do Gateway
curl http://localhost:8001/health

# Testar conexão simulada com dispositivo
curl -X POST "http://localhost:8001/api/devices/connect" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'$DEVICE_ID'",
    "protocol": "opc_ua",
    "endpoint": "opc.tcp://192.168.100.50:4840"
  }'
```

---

## 🔍 Monitoramento e Observabilidade

### 1. Grafana

```bash
# Acessar Grafana
open http://localhost:3000

# Login: admin / admin (alterar na primeira vez)
```

**Configurar Datasources:**
1. Configuration → Data Sources → Add data source
2. Adicionar PostgreSQL:
   - Host: postgres:5432
   - Database: optiflow
   - User: optiflow
   - Password: optiflow_password
3. Adicionar InfluxDB:
   - URL: http://influxdb:8086
   - Organization: optiflow
   - Token: optiflow_admin_token
   - Default Bucket: timeseries

### 2. MLflow

```bash
# Acessar MLflow
open http://localhost:5000

# Visualizar experimentos
# Verificar modelos registrados
```

### 3. RabbitMQ Management

```bash
# Acessar painel RabbitMQ
open http://localhost:15672

# Login: optiflow / optiflow_password
```

**Verificar:**
- Queues: celery (deve ter workers conectados)
- Connections: Número de workers conectados
- Channels: Canais ativos
- Message rates: Taxa de mensagens processadas

---

## 🐛 Troubleshooting

### Problema 1: Container não inicia

```bash
# Verificar logs do container
docker-compose logs <service-name>

# Verificar se a porta está em uso
sudo netstat -tulpn | grep <port>

# Exemplo: verificar porta 8000
sudo netstat -tulpn | grep 8000

# Matar processo na porta (se necessário)
sudo kill -9 <PID>
```

### Problema 2: Backend não conecta ao PostgreSQL

```bash
# Verificar se PostgreSQL está rodando
docker-compose ps postgres

# Testar conexão
docker exec -it optiflow-ai--postgres-1 psql -U optiflow -d optiflow -c "SELECT 1;"

# Verificar variáveis de ambiente do backend
docker exec optiflow-ai--backend-1 env | grep DATABASE_URL

# Recriar banco de dados
docker-compose down
docker volume rm optiflow-ai-_postgres_data
docker-compose up -d postgres
```

### Problema 3: InfluxDB não aceita escritas

```bash
# Verificar token
docker exec -it optiflow-ai--influxdb-1 \
  influx auth list --token optiflow_admin_token

# Verificar buckets
docker exec -it optiflow-ai--influxdb-1 \
  influx bucket list --token optiflow_admin_token --org optiflow

# Recriar bucket
docker exec -it optiflow-ai--influxdb-1 \
  influx bucket create --name timeseries --org optiflow --token optiflow_admin_token
```

### Problema 4: Frontend não carrega

```bash
# Verificar se o backend está acessível
curl http://localhost:8000/api/v1/health

# Verificar CORS no backend
# Editar backend/app/core/config.py
# Adicionar "http://localhost:5173" em BACKEND_CORS_ORIGINS

# Limpar cache do npm e reinstalar
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Problema 5: Celery Worker não processa tarefas

```bash
# Verificar se RabbitMQ está rodando
docker-compose ps rabbitmq

# Verificar conexão do Celery
docker-compose logs celery-worker | grep "Connected to amqp"

# Reiniciar worker
docker-compose restart celery-worker

# Verificar queues no RabbitMQ
curl -u optiflow:optiflow_password http://localhost:15672/api/queues
```

### Problema 6: Erro de permissão em volumes

```bash
# Linux: Ajustar permissões dos volumes
sudo chown -R $USER:$USER .

# Recriar volumes
docker-compose down -v
docker-compose up -d
```

### Problema 7: Memória insuficiente

```bash
# Verificar uso de memória
docker stats

# Aumentar memória disponível para Docker
# Docker Desktop: Settings → Resources → Memory (aumentar para 8GB+)

# Parar serviços não essenciais temporariamente
docker-compose stop grafana mlflow
```

### Problema 8: API retorna 401 Unauthorized

```bash
# Verificar se o token está correto
echo $TOKEN

# Gerar novo token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@smartport.com&password=Admin@123456"

# Verificar expiração do token (padrão: 30 minutos)
# Configurável em backend/app/core/config.py: ACCESS_TOKEN_EXPIRE_MINUTES
```

### Problema 9: Gateway não conecta aos dispositivos

```bash
# Verificar logs detalhados
docker-compose logs gateway -f

# Verificar conectividade de rede
docker exec optiflow-ai--gateway-1 ping <device-ip>

# Verificar se a porta do protocolo está acessível
# Para OPC UA (porta 4840):
docker exec optiflow-ai--gateway-1 nc -zv <device-ip> 4840
```

### Problema 10: Migrations falham

```bash
# Entrar no container do backend
docker exec -it optiflow-ai--backend-1 /bin/bash

# Verificar status das migrations
alembic current

# Verificar histórico
alembic history

# Reverter migration
alembic downgrade -1

# Recriar banco do zero
# CUIDADO: Isso apaga todos os dados!
docker-compose down
docker volume rm optiflow-ai-_postgres_data
docker-compose up -d postgres
# Aguardar PostgreSQL iniciar
sleep 10
docker-compose up -d backend
# As migrations devem rodar automaticamente
```

---

## 📊 Checklist de Verificação Completa

Use este checklist para validar que o SmartPort está funcionando corretamente:

- [ ] **Infraestrutura**
  - [ ] Docker e Docker Compose instalados
  - [ ] Todos os 11 containers rodando (`docker-compose ps`)
  - [ ] Sem erros críticos nos logs

- [ ] **Bancos de Dados**
  - [ ] PostgreSQL acessível e com tabelas criadas
  - [ ] InfluxDB acessível e com buckets criados
  - [ ] Redis respondendo a PING
  - [ ] RabbitMQ com workers conectados

- [ ] **Backend API**
  - [ ] Health check retorna 200 OK
  - [ ] Swagger UI acessível em /docs
  - [ ] Login funcional e retorna token JWT
  - [ ] CRUD de organizações, sites, devices, tags funcional

- [ ] **Gateway**
  - [ ] Serviço iniciado sem erros
  - [ ] Health check retorna 200 OK (se implementado)

- [ ] **Frontend**
  - [ ] Aplicação carrega em http://localhost:5173
  - [ ] Sem erros no console do navegador
  - [ ] Consegue fazer requests para o backend

- [ ] **Funcionalidades SmartPort**
  - [ ] Organização criada com sucesso
  - [ ] Site SmartPort criado (site_type='smartport')
  - [ ] Dispositivo (PLC) criado e configurado
  - [ ] Tags criadas e vinculadas ao dispositivo
  - [ ] Dados de séries temporais sendo escritos no InfluxDB
  - [ ] Consultas de dados retornando valores corretos
  - [ ] Alarmes criados e ativos

- [ ] **Monitoramento**
  - [ ] Grafana acessível e datasources configurados
  - [ ] MLflow acessível
  - [ ] RabbitMQ Management acessível

---

## 📚 Próximos Passos

Após concluir este guia, você pode:

1. **Desenvolver Frontend SmartPort**
   - Implementar dashboards de visualização
   - Criar componentes de configuração de dispositivos
   - Adicionar gráficos em tempo real

2. **Implementar Protocol Handlers**
   - Desenvolver handlers OPC UA, Modbus, MQTT
   - Testar comunicação real com PLCs
   - Implementar reconexão automática

3. **Criar Modelos de ML**
   - Desenvolver modelo de manutenção preditiva
   - Criar modelo de detecção de anomalias
   - Implementar otimização de operações

4. **Escrever Testes**
   - Testes unitários (pytest)
   - Testes de integração
   - Testes E2E (Playwright)

5. **Deploy em Produção**
   - Configurar CI/CD
   - Setup de ambiente Kubernetes
   - Configurar monitoramento (Prometheus + Grafana)

---

## 📞 Suporte

Para dúvidas ou problemas:

- **Documentação**: `/docs/` (READMEs, arquitetura, API)
- **Issues**: Abra uma issue no repositório
- **Logs**: Sempre verifique `docker-compose logs -f` primeiro

---

**Última atualização**: 2025-10-24
**Versão**: 1.0.0
**Branch**: `claude/smartport-setup-guide-011CUSkHf6CqBBawpjAtvGcX`
