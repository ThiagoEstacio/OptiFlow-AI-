# Scripts Directory

Este diretório contém scripts utilitários para gerenciar e testar o OptiFlow AI Platform.

## 📊 Container Monitoring

### monitor-containers.sh
Script bash para verificar status de todos os containers do stack.

**Uso:**
```bash
./scripts/monitor-containers.sh
```

**Funcionalidades:**
- ✅ Status visual de todos os 20 containers
- 🏥 Health check de cada serviço
- 🌐 URLs de acesso rápido
- 📊 Sumário geral (Total/Running/Healthy/Unhealthy)
- 🎨 Output colorido e organizado por categoria

**Categorias monitoradas:**
- Core Application (backend, frontend, gateway)
- Infrastructure (postgres, redis, influxdb)
- Messaging (kafka, zookeeper, rabbitmq)
- Background Jobs (celery-worker, celery-beat)
- Monitoring (prometheus, grafana, exporters)
- Simulation & ML (opcua-server, mlflow)

---

### monitor-live.py
Monitor Python com atualização em tempo real e métricas de recursos.

**Uso básico (snapshot):**
```bash
python3 scripts/monitor-live.py
```

**Modo contínuo (atualiza a cada 5s):**
```bash
python3 scripts/monitor-live.py --continuous
```

**Funcionalidades:**
- 📈 Uso de CPU por container
- 💾 Consumo de memória
- 🌐 Tráfego de rede
- 🔄 Atualização automática em tempo real
- 🎨 Interface colorida com emojis
- ⌨️  Ctrl+C para sair

**Exemplo de output:**
```
🚀 Core Application
  ● healthy backend    CPU: 0.75%   MEM: 289.9MiB
  ● running frontend   CPU: 0.04%   MEM: 56MiB
  ● healthy gateway    CPU: 0.13%   MEM: 68.32MiB
```

---

## Scripts Disponíveis

### 1. `smartport_setup.py`

**Propósito**: Executa o setup inicial completo do SmartPort

**O que faz**:
- Cria usuário administrador
- Cria organização (Porto de Santos)
- Cria site SmartPort (Terminal T1)
- Cria dispositivo PLC (Portainer 01)
- Cria 6 tags de processo
- Cria alarme de temperatura
- Salva configuração em `smartport_config.json`

**Como usar**:
```bash
# Certifique-se que os serviços estão rodando
docker-compose up -d

# Execute o setup
python scripts/smartport_setup.py
```

**Saída**: Arquivo `smartport_config.json` com IDs de todos os recursos criados

---

### 2. `smartport_simulate.py`

**Propósito**: Simula dados realistas de um portainer em operação

**O que faz**:
- Simula ciclos completos de operação do portainer:
  - Carregar container
  - Levantar carga
  - Mover horizontalmente
  - Descer carga
  - Descarregar
  - Retornar à posição inicial
- Gera dados para todas as tags:
  - Temperatura do motor (°C)
  - Altura do spreader (m)
  - Posição X (m)
  - Peso da carga (kg)
  - Status operacional
  - Consumo de energia (kW)

**Como usar**:
```bash
# Execução padrão (60 minutos)
python scripts/smartport_simulate.py

# Teste rápido (5 minutos, 2 ciclos)
python scripts/smartport_simulate.py --quick

# Duração personalizada (ex: 30 minutos)
python scripts/smartport_simulate.py --duration 30

# Usar arquivo de configuração diferente
python scripts/smartport_simulate.py --config minha_config.json
```

**Parâmetros**:
- `--duration N`: Duração da simulação em minutos (padrão: 60)
- `--quick`: Executa teste rápido de 5 minutos
- `--config FILE`: Arquivo de configuração (padrão: smartport_config.json)

---

### 3. `smartport_verify.py`

**Propósito**: Verifica que todos os componentes do SmartPort estão funcionando

**O que verifica**:
- ✓ Containers Docker (11 serviços)
- ✓ Backend API (health, docs)
- ✓ Bancos de dados (PostgreSQL, InfluxDB, Redis)
- ✓ Interfaces web (Frontend, Grafana, MLflow, RabbitMQ)
- ✓ Dados do SmartPort (organização, site, device, tags)
- ✓ Dados de séries temporais

**Como usar**:
```bash
# Verificação completa
python scripts/smartport_verify.py

# Verificar apenas infraestrutura (sem dados)
python scripts/smartport_verify.py --no-data
```

**Saída**: Relatório detalhado de cada verificação com resumo final

---

## Fluxo de Trabalho Recomendado

### Setup Inicial

```bash
# 1. Subir serviços
docker-compose up -d

# 2. Aguardar inicialização (2-3 minutos)
docker-compose logs -f

# 3. Executar setup
python scripts/smartport_setup.py

# 4. Verificar instalação
python scripts/smartport_verify.py

# 5. Simular dados (teste rápido)
python scripts/smartport_simulate.py --quick

# 6. Verificar novamente (incluindo dados)
python scripts/smartport_verify.py
```

### Desenvolvimento Contínuo

```bash
# Simular dados enquanto desenvolve
python scripts/smartport_simulate.py --duration 120 &

# Acompanhar logs
docker-compose logs -f backend

# Verificar periodicamente
python scripts/smartport_verify.py
```

### Demonstração

```bash
# Setup rápido para demo
python scripts/smartport_setup.py && \
python scripts/smartport_simulate.py --quick && \
echo "Demo pronta! Acesse http://localhost:8000/docs"
```

---

## Arquivos Gerados

### `smartport_config.json`

Arquivo de configuração gerado por `smartport_setup.py`:

```json
{
  "base_url": "http://localhost:8000",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "resources": {
    "user": { "id": "...", "email": "admin@smartport.com" },
    "organization": { "id": "...", "name": "Porto de Santos" },
    "site": { "id": "...", "name": "Terminal T1 - Santos", "site_type": "smartport" },
    "device": { "id": "...", "name": "PLC Portainer 01" },
    "tags": [
      { "id": "...", "name": "PC01_Motor_Temperature" },
      { "id": "...", "name": "PC01_Spreader_Height" },
      ...
    ],
    "alarm": { "id": "...", "name": "Temperatura Motor Alta" }
  }
}
```

Este arquivo é usado pelos scripts de simulação e verificação.

---

## Requisitos

### Python 3.11+

```bash
python --version  # Deve ser 3.11 ou superior
```

### Dependências

```bash
pip install requests
```

### Docker & Docker Compose

```bash
docker --version
docker-compose --version
```

### Serviços Rodando

Todos os scripts assumem que os serviços estão rodando:

```bash
docker-compose up -d
```

---

## Troubleshooting

### Erro: "Arquivo de configuração não encontrado"

```bash
# Execute o setup primeiro
python scripts/smartport_setup.py
```

### Erro: "Não foi possível conectar ao backend"

```bash
# Verifique se o backend está rodando
docker-compose ps backend
docker-compose logs backend

# Reinicie se necessário
docker-compose restart backend
```

### Erro: "Token inválido" ou "401 Unauthorized"

```bash
# Refaça o setup para obter novo token
python scripts/smartport_setup.py
```

### Erro: "Falha ao criar recurso: 400"

Pode ser que o recurso já existe. Verifique:

```bash
# Listar recursos existentes
curl http://localhost:8000/api/v1/organizations/

# Se necessário, limpe o banco e refaça o setup
docker-compose down -v
docker-compose up -d
python scripts/smartport_setup.py
```

---

## Exemplos de Uso

### Exemplo 1: Setup Completo com Simulação

```bash
#!/bin/bash
# setup_and_simulate.sh

set -e  # Parar em caso de erro

echo "🚀 Iniciando SmartPort..."
docker-compose up -d

echo "⏳ Aguardando serviços..."
sleep 30

echo "🔧 Executando setup..."
python scripts/smartport_setup.py

echo "📊 Simulando dados (10 minutos)..."
python scripts/smartport_simulate.py --duration 10

echo "✅ Pronto! Acesse:"
echo "   Backend: http://localhost:8000/docs"
echo "   Frontend: http://localhost:5173"
echo "   Grafana: http://localhost:3000"
```

### Exemplo 2: Verificação Automatizada

```bash
#!/bin/bash
# health_check.sh

# Executar verificação e salvar resultado
python scripts/smartport_verify.py > verification_report.txt

# Verificar se passou
if [ $? -eq 0 ]; then
  echo "✅ Sistema OK"
  exit 0
else
  echo "❌ Sistema com problemas"
  cat verification_report.txt
  exit 1
fi
```

### Exemplo 3: Simulação Contínua em Background

```bash
# Iniciar simulação em background
nohup python scripts/smartport_simulate.py --duration 480 > simulation.log 2>&1 &

# Verificar progresso
tail -f simulation.log

# Parar simulação
pkill -f smartport_simulate.py
```

---

## Contribuindo

Ao adicionar novos scripts:

1. Documente o propósito e uso no cabeçalho do script
2. Adicione ao README.md
3. Inclua tratamento de erros
4. Forneça mensagens claras de status
5. Teste em ambiente limpo (docker-compose down -v)

---

**Última atualização**: 2025-10-24
**Versão**: 1.0.0
