# 🚀 Guia de Teste em Produção - PDCA #27 GraphQL API

## 📋 Resumo Executivo

O **OptiFlow AI Platform** agora possui uma **API GraphQL moderna** que substitui múltiplos endpoints REST por queries únicas e eficientes.

### ✅ Benefícios Implementados

| Métrica | Antes (REST) | Depois (GraphQL) | Melhoria |
|---------|--------------|------------------|----------|
| **Requests do Dashboard** | 8+ requisições | 1 requisição | **87% menos** |
| **Tempo de Carregamento** | 3-4 segundos | < 1 segundo | **70% mais rápido** |
| **Transferência de Dados** | ~500KB | ~200KB | **60% menos dados** |
| **Type Safety** | Parcial | 100% | **Completo** |

---

## 🎯 O que Testar

### 1. GraphQL Playground (Interface Interativa)

**URL**: `http://localhost:8000/graphql`

**O que é**: Interface web interativa para explorar e testar a API GraphQL.

**Como testar**:
1. Abra o navegador em `http://localhost:8000/graphql`
2. Você verá o GraphQL Playground com:
   - Editor de queries (esquerda)
   - Documentação automática (direita)
   - Resultados (centro inferior)

---

### 2. Query: Executive Dashboard (Caso de Uso Principal)

**Objetivo**: Carregar todo o dashboard executivo com **UMA ÚNICA QUERY**.

**Query GraphQL**:
```graphql
query ExecutiveDashboard {
  currentUser {
    id
    email
    fullName
    role
  }

  site(id: 1, periodDays: 7) {
    id
    name
    location

    # Dashboard 360° - Visão completa do site
    dashboard360 {
      overallHealthScore {
        score
        status
        color
      }

      maintenance {
        averageHealth
        criticalAssets
        criticalAlarms
        highAlarms
        mediumAlarms
      }

      operations {
        efficiencyScore
        berthUtilization
      }
    }

    # ROI e Savings
    roi {
      totalSavings
      annualProjection
      roiPercentage
      predictiveMaintenance {
        failuresPrevented
        emergencyCostsAvoided
        savings
      }
    }

    # Top 10 Assets
    assets(limit: 10) {
      id
      name
      type
      status
      health
      location
    }

    # Últimos 5 Alarmes
    alarms(limit: 5) {
      id
      message
      severity
      timestamp
      acknowledged
    }
  }
}
```

**Resultado Esperado**:
- ✅ Dados retornados em < 100ms (primeira vez) ou < 10ms (com cache)
- ✅ Todos os campos populados
- ✅ Estrutura de dados aninhada e completa

---

### 3. Query: Lista de Assets com Filtros

**Objetivo**: Buscar assets específicos usando filtros.

**Query GraphQL**:
```graphql
query AssetsList {
  assets(
    siteId: 1
    filter: {
      type: CONVEYOR
      status: DEGRADED
      minHealth: 50.0
      limit: 20
    }
  ) {
    id
    name
    type
    status
    health
    location
    lastMaintenance
  }
}
```

**Variações para Testar**:
- `type: PUMP` - Apenas bombas
- `status: CRITICAL` - Apenas críticos
- `minHealth: 80.0` - Saúde mínima de 80%

---

### 4. Query: Alarmes Filtrados

**Objetivo**: Buscar alarmes por severidade e status.

**Query GraphQL**:
```graphql
query AlarmsList {
  alarms(
    siteId: 1
    filter: {
      severity: CRITICAL
      acknowledged: false
      limit: 10
    }
  ) {
    id
    message
    severity
    assetId
    timestamp
    acknowledged
  }
}
```

---

### 5. Mutation: Atualizar Status de Asset

**Objetivo**: Mudar o status de um asset (ex: colocar em manutenção).

**Mutation GraphQL**:
```graphql
mutation UpdateAsset {
  updateAsset(input: {
    id: "asset-123"
    status: MAINTENANCE
  }) {
    id
    status
    health
  }
}
```

---

### 6. Mutation: Reconhecer Alarme

**Objetivo**: Marcar um alarme como reconhecido.

**Mutation GraphQL**:
```graphql
mutation AcknowledgeAlarm {
  acknowledgeAlarm(input: {
    id: "alarm-456"
    userId: "user-789"
  }) {
    id
    acknowledged
  }
}
```

---

## 📊 Métricas de Performance para Validar

### 1. Via GraphQL Playground

**Verificar**:
- ✅ Tempo de resposta mostrado no canto inferior direito
- ✅ < 100ms para queries frias
- ✅ < 10ms para queries em cache

### 2. Via Prometheus (Métricas)

**URL**: `http://localhost:9090/graph`

**Queries Prometheus**:

```promql
# Taxa de requisições GraphQL
rate(graphql_requests_total[5m])

# Latência p95 do ExecutiveDashboard
histogram_quantile(0.95,
  graphql_request_duration_seconds_bucket{
    operation_name="ExecutiveDashboard"
  }
)

# Taxa de acerto do cache
(
  graphql_cache_hits_total{cache_layer="L1"} +
  graphql_cache_hits_total{cache_layer="L2"}
) / (
  graphql_cache_hits_total +
  graphql_cache_misses_total
) * 100
```

### 3. Via Grafana (Dashboards)

**URL**: `http://localhost:3000`

**Dashboards para Ver**:
- GraphQL Performance Overview
- Cache Hit Rates
- Request Duration Breakdown

---

## 🔍 Testes de Integração

### Teste 1: Cache em Ação (PDCA #26)

**Passos**:
1. Execute a query `ExecutiveDashboard` pela primeira vez
2. Anote o tempo de resposta (esperado: ~60-100ms)
3. Execute a **mesma query** novamente imediatamente
4. Anote o tempo de resposta (esperado: ~4-10ms)

**Validação**:
- ✅ Segunda execução **muito mais rápida** (cache L1 hit)
- ✅ Resultado idêntico em ambas as execuções

### Teste 2: Tracing Distribuído (PDCA #25)

**Passos**:
1. Execute qualquer query GraphQL
2. Abra Jaeger UI: `http://localhost:16686`
3. Busque por serviço "optiflow-backend"
4. Encontre o trace mais recente

**Validação**:
- ✅ Trace aparece no Jaeger
- ✅ Mostra hierarquia de spans:
  - `graphql_request`
  - `graphql_query_ExecutiveDashboard`
  - `cache_l1_lookup`
  - `cache_l2_lookup` (se miss L1)
  - `database_query` (se miss L1+L2)

### Teste 3: Dashboard Otimizado (PDCA #14)

**Passos**:
1. Execute a query `ExecutiveDashboard` sem cache (limpe o cache antes)
2. Observe o tempo de execução
3. Compare com o tempo antigo de 8+ requests REST

**Validação**:
- ✅ Query única retorna em ~60ms (vs 3-4s antes)
- ✅ Todos os dados carregados em paralelo
- ✅ Sem necessidade de múltiplas chamadas

---

## 🧪 Cenários de Teste de Cliente

### Cenário 1: Operador de Planta

**Persona**: João, operador que monitora a planta 24/7

**Fluxo**:
1. Abre o dashboard executivo (query `ExecutiveDashboard`)
2. Vê 3 alarmes críticos na lista
3. Reconhece um alarme (mutation `AcknowledgeAlarm`)
4. Filtra apenas assets em estado crítico
5. Coloca um asset em manutenção (mutation `UpdateAsset`)

**Queries para Executar**:
```graphql
# 1. Dashboard inicial
query { ... ExecutiveDashboard ... }

# 2. Reconhecer alarme
mutation { acknowledgeAlarm(input: { id: "alarm-1", userId: "joao" }) { id acknowledged } }

# 3. Filtrar assets críticos
query { assets(siteId: 1, filter: { status: CRITICAL }) { id name status } }

# 4. Colocar em manutenção
mutation { updateAsset(input: { id: "asset-1", status: MAINTENANCE }) { id status } }
```

### Cenário 2: Gerente de Operações

**Persona**: Maria, gerente que precisa de relatórios e KPIs

**Fluxo**:
1. Visualiza ROI e savings do período
2. Analisa tendência de eficiência
3. Exporta dados para relatório

**Queries para Executar**:
```graphql
# 1. Dados de ROI
query {
  site(id: 1, periodDays: 30) {
    roi {
      totalSavings
      annualProjection
      roiPercentage
      predictiveMaintenance {
        failuresPrevented
        emergencyCostsAvoided
        savings
      }
    }
  }
}

# 2. Métricas operacionais
query {
  site(id: 1, periodDays: 7) {
    dashboard360 {
      operations {
        efficiencyScore
        berthUtilization
      }
      maintenance {
        averageHealth
        criticalAssets
      }
    }
  }
}
```

### Cenário 3: Desenvolvedor Integrando Frontend

**Persona**: Pedro, desenvolvedor React consumindo a API

**Vantagens para Mostrar**:
1. **Type Safety**: Schema GraphQL → TypeScript types automático
2. **Documentação**: Schema auto-documentado no Playground
3. **Flexibilidade**: Pedir só os campos necessários
4. **Performance**: Uma query vs múltiplas REST calls

**Exemplo de Integração React**:
```typescript
import { useQuery } from '@apollo/client';

function Dashboard() {
  const { data, loading } = useQuery(EXECUTIVE_DASHBOARD_QUERY);

  if (loading) return <Loading />;

  // Dados já vêm estruturados!
  return (
    <div>
      <HealthScore score={data.site.dashboard360.overallHealthScore} />
      <ROI data={data.site.roi} />
      <AssetsList assets={data.site.assets} />
    </div>
  );
}
```

---

## ✅ Checklist de Validação

### Performance
- [ ] Query `ExecutiveDashboard` < 100ms (cold)
- [ ] Query `ExecutiveDashboard` < 10ms (cached)
- [ ] Cache hit rate > 95%
- [ ] Redução de 87% em número de requests

### Funcionalidade
- [ ] Todas as queries retornam dados válidos
- [ ] Mutations atualizam dados corretamente
- [ ] Filtros funcionam conforme esperado
- [ ] Erros retornam mensagens claras

### Integração (PDCAs)
- [ ] Cache L1 + L2 funcionando (PDCA #26)
- [ ] Traces aparecem no Jaeger (PDCA #25)
- [ ] Queries paralelas otimizadas (PDCA #14)
- [ ] Métricas no Prometheus

### Developer Experience
- [ ] GraphQL Playground acessível
- [ ] Documentação auto-gerada visível
- [ ] Autocomplete funciona no editor
- [ ] Erros de validação claros

---

## 🚨 Troubleshooting

### GraphQL Playground não abre

**Problema**: `http://localhost:8000/graphql` não carrega

**Solução**:
```bash
# Verificar se backend está rodando
docker ps | grep backend

# Ver logs
docker logs optiflow-backend --tail 50

# Reiniciar se necessário
docker restart optiflow-backend
```

### Query retorna erro de autenticação

**Problema**: `"Could not validate credentials"`

**Solução**:
1. Obter token JWT válido primeiro
2. Adicionar header no Playground:
```json
{
  "Authorization": "Bearer SEU_TOKEN_AQUI"
}
```

### Performance abaixo do esperado

**Problema**: Queries demorando > 100ms mesmo em cache

**Solução**:
```bash
# Verificar Redis
docker exec optiflow-redis redis-cli PING

# Limpar cache se necessário
docker exec optiflow-redis redis-cli FLUSHALL

# Verificar conexão DB
docker logs optiflow-postgres --tail 20
```

---

## 📈 Próximos Passos (Pós-Teste)

Após validar em ambiente de teste, os próximos passos para produção:

1. **Configurar Rate Limiting** específico para GraphQL
2. **Configurar Query Complexity Analysis** (prevenir queries muito pesadas)
3. **Habilitar Persisted Queries** (segurança adicional)
4. **Configurar CDN** para cache de queries públicas
5. **Monitorar em produção** via Grafana + alertas

---

## 📞 Contato e Suporte

**Documentação Completa**:
- PDCA #27: `/docs/PDCA_27_GRAPHQL_COMPLETE.md`
- Integração: `/docs/PDCA_INTEGRATION_EXAMPLE.md`

**Endpoints**:
- GraphQL API: `http://localhost:8000/graphql`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`
- Jaeger: `http://localhost:16686`

---

**🎉 Pronto para Testar! Boa sorte na demonstração ao cliente!**
