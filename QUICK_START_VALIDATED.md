# OptiFlow Platform - Quick Start Guide (Validated)

**Última Atualização**: 2025-11-25
**Status**: ✅ Validado e Funcional

Este guia reflete o **estado real e funcional** do sistema após validação completa.

---

## 🚀 Start em 5 Minutos

### 1. Pré-requisitos
```bash
# Verificar instalações
docker --version          # >= 20.10
docker compose version    # >= 2.0
```

### 2. Iniciar Infraestrutura Base
```bash
cd /home/thiestacio/OptiFlow-AI-

# Iniciar serviços core
docker compose up -d zookeeper postgres redis influxdb rabbitmq

# Aguardar ~10 segundos para services ficarem healthy
sleep 10
```

### 3. Iniciar Kafka Cluster
```bash
# Iniciar brokers (requer zookeeper up)
docker compose up -d kafka-1 kafka-2 kafka-3

# Aguardar brokers ficarem prontos
sleep 10
```

### 4. Iniciar Gateway (Edge)
```bash
# Iniciar gateway com adaptador OPC UA
docker compose up -d gateway

# Verificar se está publicando no Kafka
docker logs -f gateway | grep "Published"
# Deve mostrar: ✅ Published XX messages to Kafka topic 'raw_tags'
```

### 5. Iniciar Backend + Consumer
```bash
# Iniciar backend FastAPI com consumer Kafka
docker compose up -d backend

# Aguardar startup completo
sleep 15

# Verificar saúde
curl http://localhost:8000/api/health
# Deve retornar: {"status":"healthy"}
```

### 6. Validar Pipeline Completo
```bash
# Executar script de validação
./scripts/validate_pipeline.sh

# Deve mostrar:
# ✅ ALL CHECKS PASSED
# Pipeline is healthy and operational!
```

---

## 📊 Acessar Interfaces

### Gateway UI (Configuração de Tags)
```
URL: http://localhost:8080/ui/tags.html
Funcionalidades:
  • Visualizar 53 tags descobertos do simulador OPC UA
  • Configurar scan rate (500ms - 60s)
  • Ver valores em tempo real com quality e timestamp
  • Criar/editar/deletar tags manualmente
```

### Backend API (Swagger)
```
URL: http://localhost:8000/docs
Endpoints Principais:
  • GET  /api/health                    - Health check
  • GET  /api/v1/tags                   - Listar tags
  • GET  /api/v1/analytics/...          - Dados analíticos
  • POST /api/v1/simulator/...          - Controle de simulador
```

### Kafka UI (Monitoramento)
```
URL: http://localhost:8090
Tópicos:
  • raw_tags         - Dados de tags do gateway
  • dlq_timeseries   - Dead letter queue

Grupos de Consumidores:
  • timeseries-writers - Consumer backend→InfluxDB
```

### InfluxDB UI (Banco de Dados)
```
URL: http://localhost:8086
Login: (verificar variáveis de ambiente)

Buckets:
  • timeseries      - Dados raw (30 dias)
  • downsampled_1m  - Médias 1 minuto (90 dias)
  • downsampled_1h  - Médias 1 hora (2 anos)
  • downsampled_1d  - Médias diárias (infinito)
```

---

## 🔍 Verificação Rápida

### Gateway está publicando?
```bash
docker logs gateway | grep "Published" | tail -5
```
**Esperado**: Mensagens como `✅ Published 53 messages to Kafka topic 'raw_tags'`

### Kafka tem mensagens?
```bash
docker exec optiflow-kafka-1 kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic raw_tags \
  --max-messages 3
```
**Esperado**: JSON com `tag_name`, `value`, `quality`, `timestamp`

### Consumer está processando?
```bash
docker exec optiflow-kafka-1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group timeseries-writers | grep raw_tags
```
**Esperado**: LAG < 100 mensagens

### InfluxDB tem dados?
```bash
docker exec optiflow-influxdb influx query \
  'from(bucket: "timeseries") |> range(start: -5m) |> limit(n: 5)'
```
**Esperado**: Registros com `tag_id`, `value`, `quality`

---

## 📁 Estrutura de Dados

### Fluxo de Mensagens
```
OPC UA Simulator (53 tags @ 100ms)
        ↓
Gateway (aiokafka producer)
        ↓
Kafka Topic: raw_tags
        ↓
Backend Consumer (group: timeseries-writers)
        ↓
InfluxDB Bucket: timeseries
```

### Formato de Mensagem (Kafka)
```json
{
  "tag_name": "speed_mps",
  "value": 2.617,
  "quality": "good",
  "timestamp": "2025-11-25T04:16:02.897453",
  "source": "opcua-simulator-001",
  "address": "ns=2;i=8"
}
```

### Esquema InfluxDB
```
Measurement: tag_data
Tags:
  - tag_id      (ex: "speed_mps")
  - quality     (ex: "good", "bad", "uncertain")
  - source      (ex: "opcua-simulator-001")
Fields:
  - value       (float/int/bool/string)
Timestamp:
  - Preservado do OPC UA SourceTimestamp
```

---

## ⚙️ Configuração

### Variáveis de Ambiente Críticas
```bash
# .env (root)
CONSUMER_ENABLED=true                    # ✅ OBRIGATÓRIO
CONSUMER_TOPIC=raw_tags                  # ✅ OBRIGATÓRIO
KAFKA_BOOTSTRAP_SERVERS=kafka-1:9092,kafka-2:9093,kafka-3:9096

# gateway/.env (se existir)
KAFKA_BOOTSTRAP_SERVERS=kafka:9092       # Usar service name
```

### Configuração do Gateway
```json
// gateway/config/adapters_config.json
{
  "adapters": [
    {
      "adapter_id": "opcua-simulator-001",
      "protocol": "opcua",
      "host": "simulator",
      "port": 4840,
      "enabled": true,
      "scan_rate_ms": 1000,
      "tags": []  // Vazio = auto-discover
    }
  ]
}
```

---

## 🛠️ Troubleshooting Comum

### Gateway não publica no Kafka
**Sintoma**: Logs mostram `⚠️ Kafka not available`

**Diagnóstico**:
```bash
docker exec optiflow-gateway pip list | grep aiokafka
```

**Fix**:
```bash
# Se não estiver instalado
docker exec optiflow-gateway pip install aiokafka==0.10.0
docker restart optiflow-gateway

# Ou rebuild a imagem
docker compose build gateway
docker compose up -d gateway
```

---

### Consumer não inicia
**Sintoma**: No logs de consumer, lag sempre crescendo

**Diagnóstico**:
```bash
docker logs optiflow-backend | grep -i "consumer\|kafka"
```

**Fix**:
```bash
# Verificar .env
grep CONSUMER_ENABLED .env
# Deve retornar: CONSUMER_ENABLED=true

# Se não existir, adicionar:
echo "CONSUMER_ENABLED=true" >> .env
docker restart optiflow-backend
```

---

### InfluxDB vazio
**Sintoma**: Query retorna sem dados

**Diagnóstico**:
```bash
# Verificar se bucket existe
docker exec optiflow-influxdb influx bucket list | grep timeseries

# Verificar lag do consumer
docker exec optiflow-kafka-1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group timeseries-writers
```

**Fix**:
```bash
# Se bucket não existe, criar:
docker exec optiflow-influxdb influx bucket create \
  -n timeseries \
  -o optiflow \
  --retention 720h

# Se consumer não está commitando, restart:
docker restart optiflow-backend
```

---

### Lag do Consumer Alto (>1000)
**Sintoma**: Consumer group mostra lag crescente

**Diagnóstico**:
```bash
docker logs optiflow-backend | grep -i "error.*influx\|write.*fail"
```

**Possíveis Causas**:
1. InfluxDB lento (muitos writes simultâneos)
2. Batch size pequeno
3. Circuit breaker aberto

**Fix**:
```bash
# Aumentar batch size (requer code change)
# backend/app/services/timeseries_consumer.py
# max_batch_size = 500

# Ou restart para resetar circuit breaker
docker restart optiflow-backend
```

---

## 📈 Métricas Esperadas

### Performance Normal
| Componente | Métrica | Valor Esperado |
|------------|---------|----------------|
| Gateway | Tags/segundo | ~53 |
| Gateway | Frequência publish | 1-2 segundos (batches) |
| Kafka | Lag máximo | <100 mensagens |
| Consumer | Throughput | 50-100 msgs/s |
| InfluxDB | Write latency | <100ms |
| E2E Latency | Gateway→InfluxDB | <5 segundos |

### Alertas Críticos
- ❌ Consumer lag >1000 mensagens
- ❌ Gateway down >60 segundos
- ❌ InfluxDB write errors >1%
- ❌ Kafka broker down

---

## 🔄 Rotinas de Manutenção

### Diário
```bash
# Verificar saúde do pipeline
./scripts/validate_pipeline.sh

# Verificar logs de erro
docker logs optiflow-gateway | grep -i error | tail -20
docker logs optiflow-backend | grep -i error | tail -20
```

### Semanal
```bash
# Limpar logs antigos
docker system prune -f

# Verificar uso de disco (InfluxDB)
docker exec optiflow-influxdb du -sh /var/lib/influxdb2/

# Verificar retenção de buckets
docker exec optiflow-influxdb influx bucket list
```

### Mensal
```bash
# Backup do InfluxDB
docker exec optiflow-influxdb influx backup /tmp/backup
docker cp optiflow-influxdb:/tmp/backup ./backups/influx-$(date +%Y%m%d)

# Backup do PostgreSQL
docker exec optiflow-postgres pg_dump -U optiflow optiflow > ./backups/postgres-$(date +%Y%m%d).sql

# Verificar e atualizar dependencies
docker compose pull
```

---

## 🎯 Próximos Passos

### Após Validar Pipeline

1. **Adicionar Segundo PLC**
   - Editar `gateway/config/adapters_config.json`
   - Adicionar novo adaptador OPC UA/Modbus/S7

2. **Configurar Downsampling**
   - Criar Continuous Queries no InfluxDB
   - Popular buckets `downsampled_1m`, `downsampled_1h`, `downsampled_1d`

3. **Implementar Cache Redis**
   - Cachear consultas frequentes
   - Reduzir 70-80% da carga no InfluxDB

4. **Monitoramento com Prometheus**
   - Expor métricas do consumer
   - Dashboards de lag, throughput, errors

5. **Alerting**
   - Configurar Alertmanager
   - Notificações Slack/Email para falhas

---

## 📚 Documentação Completa

- **[PIPELINE_VALIDATION_COMPLETE.md](PIPELINE_VALIDATION_COMPLETE.md)** - Validação end-to-end
- **[SESSION_SUMMARY.md](SESSION_SUMMARY.md)** - Resumo da última sessão
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Visão geral de arquitetura
- **[REALTIME_VALUES_SUMMARY.md](gateway/REALTIME_VALUES_SUMMARY.md)** - UI realtime
- **[scripts/validate_pipeline.sh](scripts/validate_pipeline.sh)** - Health check automatizado

---

## ⚡ Comandos Úteis

### Restart Completo
```bash
docker compose down
docker compose up -d zookeeper postgres redis influxdb
sleep 10
docker compose up -d kafka-1 kafka-2 kafka-3
sleep 10
docker compose up -d gateway backend
sleep 15
./scripts/validate_pipeline.sh
```

### Logs em Tempo Real
```bash
# Gateway
docker logs -f optiflow-gateway --tail 50

# Backend
docker logs -f optiflow-backend --tail 50 | grep -v "sqlalchemy"

# Todos os serviços
docker compose logs -f --tail 20
```

### Verificar Recursos
```bash
# Uso de CPU/Memória
docker stats

# Espaço em disco
docker system df

# Containers rodando
docker compose ps
```

---

## ✅ Checklist de Validação

Antes de considerar o sistema operacional:

- [ ] Gateway responde em http://localhost:8080/health
- [ ] Gateway publica mensagens no Kafka (verificar logs)
- [ ] Tópico `raw_tags` tem mensagens (kafka-console-consumer)
- [ ] Consumer group `timeseries-writers` está ativo
- [ ] Consumer lag <100 mensagens
- [ ] Backend responde em http://localhost:8000/api/health
- [ ] InfluxDB tem dados recentes (últimos 5 minutos)
- [ ] UI do gateway mostra tags com values atualizando
- [ ] Script `validate_pipeline.sh` passa todos os testes

---

**🎉 Parabéns! Você tem um pipeline industrial IoT funcional.**

Para dúvidas ou problemas, consulte:
1. Logs dos containers (`docker logs <container>`)
2. Script de validação (`./scripts/validate_pipeline.sh`)
3. Documentação completa em `PIPELINE_VALIDATION_COMPLETE.md`

---

*OptiFlow Platform - Industrial IoT Edge & Cloud*
*Quick Start Guide - Validated 2025-11-25*
