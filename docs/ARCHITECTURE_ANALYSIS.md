# 🏗️ Análise Arquitetural - OptiFlow AI Platform

**Data:** 11 de Novembro de 2025  
**Analista:** Arquiteto de Software Sênior  
**Versão:** 1.0.0

---

## 📋 Executive Summary

OptiFlow AI é uma **plataforma IIoT (Industrial IoT) complexa** com capacidades avançadas de ML, integração multi-protocolo industrial, e agente autônomo baseado em LLM. A análise revela uma arquitetura sólida, mas com **oportunidades críticas de otimização** em performance, escalabilidade e manutenibilidade.

### Métricas do Codebase

- **Total de arquivos Python:** 303
- **Serviços implementados:** 70+
- **Microsserviços ativos:** 9 (Backend, InfluxDB, PostgreSQL, Redis, RabbitMQ, Kafka, Ollama, MLflow, Monitoring)
- **Protocolos industriais:** 5 (OPC UA, Modbus TCP/RTU, MQTT, S7, EtherNet/IP)
- **Endpoints API:** 100+ (estimativa)

---

## 🎯 Análise SWOT

### ✅ STRENGTHS (Forças)

#### 1. **Arquitetura Moderna e Escalável**
- ✅ **Async/Await nativo:** FastAPI + SQLAlchemy async
- ✅ **Event-Driven:** Kafka + RabbitMQ para desacoplamento
- ✅ **Time-Series otimizado:** InfluxDB para dados industriais
- ✅ **Cache distribuído:** Redis para performance
- ✅ **Multi-tenant:** Suporte a organizações e sites

#### 2. **Stack Tecnológico de Ponta**
- ✅ **Python 3.11+** com type hints modernos
- ✅ **FastAPI** com validação Pydantic 2.0
- ✅ **React 18.2 + TypeScript** no frontend
- ✅ **Docker Compose** para orquestração
- ✅ **Prometheus + Grafana** para observabilidade

#### 3. **Capacidades Industriais Avançadas**
- ✅ **5 protocolos industriais** implementados
- ✅ **Gateway edge** com buffer e edge AI
- ✅ **OPC UA Server** para integração bidirecional
- ✅ **Data streaming** com Kafka

#### 4. **AI/ML Integrado**
- ✅ **Agente Autônomo** com LLM (Ollama local)
- ✅ **Anomaly Detection** com Isolation Forest (F1=0.1032)
- ✅ **Predictive Maintenance** com ML
- ✅ **MLflow** para versionamento de modelos

#### 5. **Features Empresariais**
- ✅ **WebSocket real-time** com reconexão automática
- ✅ **Rate limiting** e circuit breakers
- ✅ **Health checks** completos
- ✅ **Geração de relatórios** (PDF/Excel)
- ✅ **Dashboard executivo** 360°

---

### ⚠️ WEAKNESSES (Fraquezas)

#### 1. **Complexidade Excessiva** 🔴 CRÍTICO
```
Problema: 70+ serviços em backend/app/services/
Impacto: 
  - Difícil manutenção
  - Onboarding lento de novos desenvolvedores
  - Testes complexos
  - Difícil rastrear dependências

Evidências:
  - autonomous_agent.py: 1,045 linhas
  - executive_dashboard.py: 682 linhas
  - data_import_service.py: 650+ linhas
  - Muitos serviços com responsabilidades sobrepostas
```

**Solução:**
1. Consolidar serviços relacionados em módulos coesos
2. Aplicar Domain-Driven Design (DDD)
3. Separar em bounded contexts claros

#### 2. **Performance do ML** 🔴 CRÍTICO
```
Problema: F1-Score atual = 0.1032 (muito baixo)
Impacto:
  - 27,061 falsos positivos
  - Perda de 62% das anomalias reais
  - Inviável para produção industrial

Causa Raiz:
  - Ausência de feature engineering
  - Sem ensemble methods
  - Sem hyperparameter tuning
  - Data pipeline não otimizado
```

**Solução:** Já documentada em `ML_OPTIMIZATION_STRATEGY.md`

#### 3. **Database Connection Pool** 🟡 MÉDIO
```python
# backend/app/core/config.py
DATABASE_POOL_SIZE: int = 20
DATABASE_MAX_OVERFLOW: int = 40
DATABASE_POOL_TIMEOUT: int = 30

Problema: Pool pequeno para alta concorrência
Impacto:
  - Timeouts sob carga
  - Degradação de performance com 50+ usuários
  - Gargalo em operações assíncronas

Recomendação:
  - POOL_SIZE: 50 (mín 2x cores)
  - MAX_OVERFLOW: 100
  - Implementar connection pooling no InfluxDB também
```

#### 4. **Ausência de Cache Strategy** 🟡 MÉDIO
```
Problema: Cache usado apenas pontualmente
Impacto:
  - Queries repetitivas ao PostgreSQL
  - InfluxDB sobrecarregado
  - Latência alta em dashboards

Missing:
  - Cache de tags (frequentemente acessadas)
  - Cache de aggregations
  - Cache de dashboard data
  - TTL strategies definidas
```

#### 5. **Monolitismo do Backend** 🟡 MÉDIO
```
Arquitetura atual:
  ┌─────────────────────────────┐
  │     Backend Monolito        │
  │  (70+ services em 1 app)    │
  │                             │
  │  - Gateway Manager          │
  │  - ML Services              │
  │  - Analytics                │
  │  - Reports                  │
  │  - AI Agent                 │
  │  - Asset Management         │
  └─────────────────────────────┘

Problema: Tudo acoplado em uma aplicação
Impacto:
  - Deploy all-or-nothing
  - Escala vertical apenas
  - Um bug pode derrubar tudo
  - Difícil escalar componentes individualmente
```

#### 6. **Falta de Testes** 🟠 ALTO
```bash
# Atual
backend/tests/
  ├── test_alarms.py
  ├── test_auth.py
  ├── test_devices.py
  ├── test_rate_limiting.py
  ├── test_sites.py
  └── test_tags.py

Missing:
  - Testes de integração (0%)
  - Testes de carga (0%)
  - Testes E2E (0%)
  - Coverage < 20% (estimativa)
  - Sem CI/CD pipeline
```

#### 7. **InfluxDB Queries Lentas** 🔴 CRÍTICO
```
Problema: Queries de 1.3M pontos levam 2+ minutos
Impacto:
  - ML training bloqueado
  - Dashboards lentos
  - Timeouts frequentes

Causa:
  - Sem aggregateWindow otimizado
  - Sem downsampling
  - Sem índices adequados
  - Range queries muito amplos
```

---

### 🚀 OPPORTUNITIES (Oportunidades)

#### 1. **Migração para Microsserviços** ⭐ ALTO IMPACTO
```
Proposta: Separar em 6 microsserviços independentes

┌──────────────────────────────────────────────────────────┐
│                    API Gateway (Kong/NGINX)              │
└─────────┬────────────┬────────────┬──────────┬───────────┘
          │            │            │          │
   ┌──────▼─────┐ ┌───▼────┐ ┌────▼─────┐ ┌──▼─────────┐
   │  Gateway   │ │   ML   │ │Analytics │ │  Reports   │
   │  Service   │ │Service │ │ Service  │ │  Service   │
   └──────┬─────┘ └───┬────┘ └────┬─────┘ └──┬─────────┘
          │            │           │           │
   ┌──────▼─────┐ ┌───▼────┐ ┌────▼─────┐    │
   │   Agent    │ │  Asset │ │   Core   │    │
   │  Service   │ │Service │ │  Service │────┘
   └────────────┘ └────────┘ └──────────┘

Benefícios:
  ✅ Escala independente por serviço
  ✅ Deploy granular (zero downtime)
  ✅ Tecnologias específicas por domínio
  ✅ Isolamento de falhas
  ✅ Times independentes

Custo: 3-4 sprints (120-160 horas)
```

#### 2. **Implementar CQRS Pattern** ⭐ ALTO IMPACTO
```
Current: Mesmo banco para leitura e escrita
Problem: Queries complexas afetam escritas

Proposta: CQRS + Event Sourcing

┌─────────────┐     Events      ┌──────────────┐
│   Command   │────────────────▶│  Event Store │
│    Side     │                 │   (Kafka)    │
└─────────────┘                 └───────┬──────┘
                                        │
                                ┌───────▼──────┐
                                │   Projector  │
                                └───────┬──────┘
                                        │
┌─────────────┐                 ┌───────▼──────┐
│    Query    │◀────────────────│  Read Model  │
│    Side     │                 │  (Postgres)  │
└─────────────┘                 └──────────────┘

Benefícios:
  ✅ Queries otimizadas (materialized views)
  ✅ Escritas não bloqueiam leituras
  ✅ Histórico completo (event sourcing)
  ✅ Replay de eventos para debug
  ✅ Analytics sem afetar operacional

Custo: 2-3 sprints (80-120 horas)
```

#### 3. **GraphQL para Dashboards** ⭐ MÉDIO IMPACTO
```
Current: REST com N+1 queries
Problem: Frontend faz múltiplas requisições

Proposta: GraphQL agregador

query DashboardData {
  site(id: 1) {
    tags(limit: 10) {
      id
      name
      currentValue
      alarms(status: ACTIVE) {
        count
      }
    }
    assets {
      health {
        score
        status
      }
    }
    kpis {
      production
      efficiency
      oee
    }
  }
}

Benefícios:
  ✅ 1 request ao invés de 10+
  ✅ Reduz latência em 70%
  ✅ Menos tráfego de rede
  ✅ Type-safe com TypeScript

Custo: 1-2 sprints (40-80 horas)
```

#### 4. **Streaming Analytics** ⭐ ALTO IMPACTO
```
Current: Batch processing via Celery
Problem: Latência de minutos para insights

Proposta: Real-time stream processing

┌─────────┐    Kafka     ┌──────────────┐
│ Gateway │─────────────▶│ Kafka Stream │
└─────────┘              │  Processing  │
                         │  (ksqlDB)    │
                         └──────┬───────┘
                                │
                   ┌────────────┼────────────┐
                   │            │            │
            ┌──────▼──────┐ ┌──▼─────┐ ┌───▼────┐
            │  Aggregator │ │ Anomaly│ │ Alerts │
            │   Windows   │ │Detector│ │ Trigger│
            └─────────────┘ └────────┘ └────────┘

Benefícios:
  ✅ Latência < 1 segundo
  ✅ Alertas em real-time
  ✅ Windowed aggregations
  ✅ Stateful processing

Custo: 2 sprints (80 horas)
```

#### 5. **Multi-Region Deployment** ⭐ MÉDIO IMPACTO
```
Current: Single region
Problem: Latência alta para sites globais

Proposta: Edge computing + Central cloud

┌───────────────────────────────────────┐
│         Central Cloud (AWS)           │
│  - PostgreSQL RDS (multi-AZ)          │
│  - S3 para analytics/reports          │
│  - SageMaker para ML training         │
└────────────┬──────────────────────────┘
             │ (Sync)
    ┌────────┼────────┐
    │                 │
┌───▼────┐      ┌────▼───┐
│ Edge 1 │      │ Edge 2 │  (AWS Outposts / Local)
│ Site A │      │ Site B │
│        │      │        │
│ - Gateway    │ - Gateway
│ - InfluxDB   │ - InfluxDB
│ - Redis      │ - Redis
│ - ML Inference│- ML Inference
└────────┘      └────────┘

Benefícios:
  ✅ Latência < 50ms local
  ✅ Offline capability
  ✅ Reduz custos de banda
  ✅ Compliance (dados locais)

Custo: 4-5 sprints (160-200 horas)
```

---

### 🚨 THREATS (Ameaças)

#### 1. **Débito Técnico Crescente** 🔴 CRÍTICO
```
Sintomas:
  - 70+ serviços sem refatoração
  - Duplicação de código
  - Falta de documentação atualizada
  - Testes insuficientes

Impacto Futuro:
  - Velocity de desenvolvimento cai 50%
  - Bugs aumentam exponencialmente
  - Onboarding de devs leva semanas
  - Manutenção cara

Mitigação:
  ✅ Tech Debt Sprint mensal (20% do tempo)
  ✅ Code review obrigatório
  ✅ Documentação como parte do DoD
  ✅ Refactoring incremental
```

#### 2. **Single Point of Failure** 🟠 ALTO
```
SPOFs Identificados:

1. PostgreSQL único
   - Sem replicação configurada
   - Backup manual
   - Recovery Time: horas

2. InfluxDB único
   - Sem clustering
   - Perda de dados em falha

3. Backend monolítico
   - Uma falha derruba tudo
   - Sem circuit breaker entre módulos

4. Ollama único
   - Agent fica indisponível
   - Sem fallback

Solução: Alta disponibilidade por componente
```

#### 3. **Segurança** 🟠 ALTO
```
Vulnerabilidades Potenciais:

1. Secrets em código
   - GATEWAY_API_KEY hardcoded
   - JWT_SECRET gerado dinamicamente
   
2. Sem rate limiting granular
   - RATE_LIMIT_PER_MINUTE: 100 (global)
   - Vulnerável a DDoS

3. Sem WAF
   - Exposto diretamente

4. Logs sem sanitização
   - Possível vazamento de PII

5. Docker sem user namespace
   - Containers rodam como root

Solução: Security hardening sprint
```

#### 4. **Escalabilidade Limitada** 🟡 MÉDIO
```
Gargalos:

1. PostgreSQL connection pool (20)
   - Max 60 conexões simultâneas
   - Bloqueia com 100+ usuários

2. InfluxDB single node
   - Limited write throughput
   - ~50k points/s (max)

3. Backend CPU-bound
   - ML inference síncrono
   - Report generation bloqueia workers

4. Redis single instance
   - Sem sharding
   - Memória limitada

Capacidade atual: ~100 usuários simultâneos
Alvo: 1000+ usuários

Gap: 10x de capacidade necessária
```

#### 5. **Dependência de Terceiros** 🟡 MÉDIO
```
Riscos:

1. Ollama (LLM local)
   - Model updates podem quebrar
   - Performance variável
   - Sem SLA

2. InfluxDB OSS
   - Sem suporte enterprise
   - Breaking changes entre versões

3. Multiple Python packages
   - 150+ dependências
   - Vulnerabilidades (CVEs)
   - Manutenção constante

Mitigação:
  - Lock versions (já feito)
  - Testes de regressão
  - Alternatives documentadas
```

---

## 📊 Análise de Performance

### Benchmarks Atuais (Estimados)

| Métrica | Atual | Ideal | Gap |
|---------|-------|-------|-----|
| **API Latency (p95)** | 500ms | < 200ms | 60% |
| **Dashboard Load Time** | 3-5s | < 2s | 50% |
| **ML Inference** | 200ms | < 50ms | 75% |
| **Query InfluxDB (1M points)** | 2+ min | < 10s | 92% |
| **WebSocket Reconnect** | 5-10s | < 1s | 80% |
| **Report Generation** | 10-30s | < 5s | 67% |

### Bottlenecks Identificados

#### 1. **Database Layer** 🔴
```python
# Current
async with get_db() as session:
    tags = await session.execute(
        select(Tag).options(joinedload(Tag.alarms))  # N+1 query
    )

# Otimizado
async with get_db() as session:
    tags = await session.execute(
        select(Tag)
        .options(
            selectinload(Tag.alarms),  # Batch load
            lazyload('*')  # Evita loads desnecessários
        )
        .execution_options(compiled_cache={})  # Cache SQL
    )
```

#### 2. **InfluxDB Queries** 🔴
```flux
# Current (SLOW - 2+ min)
from(bucket: "timeseries")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "tag_values")
  # Sem aggregation = 1.3M pontos

# Otimizado (FAST - < 10s)
from(bucket: "downsampled")  # Pre-aggregated bucket
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "tag_values_1m")
  |> aggregateWindow(every: 5m, fn: mean)
  # 8,640 pontos (30d * 24h * 60m / 5m)
```

#### 3. **ML Pipeline** 🔴
```python
# Current (BLOQUEANTE)
df = load_data_from_influxdb()  # 2+ minutos
features = engineer_features(df)  # Síncrono
model.fit(features)  # CPU-bound

# Otimizado (PARALELO)
async with aiofiles.open('cache.parquet') as f:
    df = await asyncio.to_thread(pd.read_parquet, f)

with ProcessPoolExecutor(max_workers=4) as pool:
    features = await loop.run_in_executor(
        pool, engineer_features, df
    )
```

---

## 🏗️ Recomendações Arquiteturais

### 🔥 PRIORIDADE CRÍTICA (0-3 meses)

#### 1. **Otimizar ML Pipeline** 
**Impacto:** Alto | **Esforço:** Médio (80h)
```
Actions:
  1. Implementar feature engineering (Sprint 1)
  2. Cache Parquet para training data (Sprint 1)
  3. Ensemble methods (Sprint 2)
  4. Hyperparameter tuning (Sprint 2)

Target:
  - F1-Score: 0.1032 → 0.42 (+307%)
  - Training time: 5-10min → 30-60s
```

#### 2. **Database Connection Pool**
**Impacto:** Alto | **Esforço:** Baixo (8h)
```python
# config.py
DATABASE_POOL_SIZE: int = 50  # 2x cores (current: 20)
DATABASE_MAX_OVERFLOW: int = 100  # (current: 40)
DATABASE_POOL_PRE_PING: bool = True
DATABASE_ECHO_POOL: bool = True  # Debug pool exhaustion

# Implementar pool monitoring
@app.middleware("http")
async def monitor_db_pool(request, call_next):
    pool = get_engine().pool
    metrics.db_pool_size.set(pool.size())
    metrics.db_pool_overflow.set(pool.overflow())
    return await call_next(request)
```

#### 3. **InfluxDB Downsampling**
**Impacto:** Alto | **Esforço:** Médio (24h)
```flux
# Criar continuous query para downsampling
option task = {name: "downsample_1m", every: 1m}

from(bucket: "timeseries")
  |> range(start: -2m)
  |> filter(fn: (r) => r._measurement == "tag_values")
  |> aggregateWindow(every: 1m, fn: mean)
  |> to(bucket: "downsampled", org: "optiflow")

# Criar para múltiplas resoluções
# - 1m (retention: 7 days)
# - 5m (retention: 30 days)
# - 1h (retention: 1 year)
```

#### 4. **Implementar Cache Strategy**
**Impacto:** Médio | **Esforço:** Médio (40h)
```python
# services/cache_service.py
class CacheService:
    def __init__(self):
        self.redis = Redis(decode_responses=True)
    
    async def get_tags_cached(
        self, 
        site_id: int, 
        ttl: int = 300  # 5min
    ) -> List[Tag]:
        cache_key = f"tags:site:{site_id}"
        
        # Try cache first
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Cache miss - fetch from DB
        async with get_db() as session:
            tags = await session.execute(
                select(Tag).where(Tag.site_id == site_id)
            )
            tags = tags.scalars().all()
        
        # Store in cache
        await self.redis.setex(
            cache_key, 
            ttl, 
            json.dumps([t.dict() for t in tags])
        )
        
        return tags
```

---

### ⚡ PRIORIDADE ALTA (3-6 meses)

#### 5. **Separar em Microsserviços**
**Impacto:** Muito Alto | **Esforço:** Alto (160h)

```
Fase 1: Extrair ML Service
  - Isolar modelo de ML
  - API independente
  - Deploy separado
  - Auto-scaling
  
Fase 2: Extrair Analytics Service
  - Queries InfluxDB
  - Aggregations
  - Dashboard data

Fase 3: Extrair Gateway Service
  - Protocolo handlers
  - Data ingestion
  - Edge computing ready
```

#### 6. **Implementar CQRS**
**Impacto:** Alto | **Esforço:** Alto (120h)

#### 7. **CI/CD Pipeline**
**Impacto:** Alto | **Esforço:** Médio (40h)
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          docker compose -f docker-compose.test.yml up --abort-on-container-exit
          
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build images
        run: docker compose build
      
      - name: Push to registry
        run: docker compose push
        
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to staging
        run: |
          ssh deploy@staging.optiflow.ai "cd /opt/optiflow && docker compose pull && docker compose up -d"
```

---

### 📈 PRIORIDADE MÉDIA (6-12 meses)

#### 8. **GraphQL Layer**
**Impacto:** Médio | **Esforço:** Médio (80h)

#### 9. **Streaming Analytics**
**Impacto:** Médio | **Esforço:** Alto (80h)

#### 10. **Multi-Region**
**Impacto:** Baixo | **Esforço:** Muito Alto (200h)

---

## 📏 Métricas de Sucesso

### Technical Metrics

| Métrica | Baseline | Target Q1 | Target Q2 | Target Q3 |
|---------|----------|-----------|-----------|-----------|
| **API p95 Latency** | 500ms | 300ms | 200ms | 150ms |
| **ML F1-Score** | 0.1032 | 0.28 | 0.35 | 0.42 |
| **Test Coverage** | 20% | 50% | 70% | 85% |
| **Uptime** | 95% | 99% | 99.5% | 99.9% |
| **MTTR** | 2h | 1h | 30min | 15min |
| **Deploy Frequency** | 1x/week | 2x/week | Daily | Multiple/day |

### Business Metrics

| Métrica | Baseline | Target |
|---------|----------|--------|
| **Time to Market (new feature)** | 2-3 weeks | 3-5 days |
| **Developer Onboarding** | 2-3 weeks | 2-3 days |
| **Bug Resolution Time** | 3-5 days | < 1 day |
| **Cost per Transaction** | $X | -30% |
| **User Satisfaction (NPS)** | ? | 70+ |

---

## 💰 Estimativa de Custos

### Refactoring Total

| Fase | Duração | Equipe | Custo |
|------|---------|--------|-------|
| **Otimizações Críticas** | 3 meses | 2 devs | $60k |
| **Microsserviços** | 6 meses | 3 devs | $180k |
| **CQRS + Event Sourcing** | 3 meses | 2 devs | $60k |
| **CI/CD + Tests** | 2 meses | 2 devs | $40k |
| **GraphQL** | 2 meses | 1 dev | $20k |
| **Streaming** | 2 meses | 2 devs | $40k |
| **Total** | **12 meses** | **~3 devs** | **$400k** |

### ROI Esperado

- **Performance:** 70% mais rápido → Melhor UX → +20% retenção
- **Escalabilidade:** 10x capacidade → Suporta 10x mais clientes
- **Manutenibilidade:** 50% menos bugs → -60% custo suporte
- **Time to Market:** 3x mais rápido → Vantagem competitiva

**Payback:** 12-18 meses

---

## 🎯 Roadmap Recomendado

### Q1 2026 (Jan-Mar)
- ✅ ML Pipeline optimization (F1: 0.42)
- ✅ Database pool optimization
- ✅ InfluxDB downsampling
- ✅ Cache strategy implementation
- ✅ Basic monitoring dashboard

### Q2 2026 (Apr-Jun)
- ✅ Extract ML Service
- ✅ CI/CD pipeline
- ✅ Test coverage 70%
- ✅ API performance optimization
- ✅ Security hardening

### Q3 2026 (Jul-Sep)
- ✅ Extract Analytics Service
- ✅ CQRS implementation
- ✅ GraphQL layer
- ✅ High availability setup

### Q4 2026 (Oct-Dec)
- ✅ Streaming analytics
- ✅ Extract Gateway Service
- ✅ Multi-region prep
- ✅ Performance optimization round 2

---

## 🔍 Conclusão

OptiFlow AI possui **fundamentos sólidos** mas precisa de **refatoração estratégica** para escalar. As principais recomendações são:

### Must-Have (3 meses)
1. ✅ **ML Optimization** → F1-Score production-ready
2. ✅ **Database Pool** → Suporta carga atual
3. ✅ **InfluxDB Downsampling** → Queries 10x+ mais rápidas
4. ✅ **Cache Strategy** → Reduz 60% das queries

### Should-Have (6 meses)
5. ✅ **Microsserviços** → Escala independente
6. ✅ **CI/CD** → Deploy confiável
7. ✅ **Tests** → 70%+ coverage

### Nice-to-Have (12 meses)
8. ✅ **CQRS** → Separation of concerns
9. ✅ **GraphQL** → Frontend performance
10. ✅ **Streaming** → Real-time analytics

**A execução gradual e priorizada dessas recomendações levará OptiFlow AI de um MVP robusto para uma plataforma enterprise-ready e escalável.**

---

**Próximo Passo:** Revisar este documento com stakeholders e priorizar iniciativas para Q1 2026.
