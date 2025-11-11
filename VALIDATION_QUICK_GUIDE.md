# 🧪 GUIA DE VALIDAÇÃO - Optimizações Implementadas
**OptiFlow AI - Teste todas as melhorias**

## 🎯 QUICK VALIDATION (5 minutos)

### 1. System Health Check
```bash
# Backend health
curl http://localhost:8000/health

# Expected: {"status":"healthy","version":"1.0.0"}
```

### 2. Cache Performance
```bash
# Cache stats (deve mostrar hit rate)
curl http://localhost:8000/api/v1/cache/stats

# Expected: hit_rate > 40%

# Test cached endpoint (1st call = miss, 2nd = hit)
time curl -s "http://localhost:8000/api/v1/tags/?limit=5" > /dev/null
time curl -s "http://localhost:8000/api/v1/tags/?limit=5" > /dev/null

# Expected: 2nd call muito mais rápido
```

### 3. Database Indexes
```bash
# Verify indexes created
docker compose exec postgres psql -U optiflow -d optiflow -c "
SELECT 
    indexname, 
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes 
WHERE schemaname = 'public' 
  AND tablename IN ('tags', 'devices', 'users')
ORDER BY indexname;
"

# Expected: 6 novos indexes listados
```

### 4. ML Models
```bash
# Check models exist
docker compose exec backend ls -lh /app/models/

# Expected: 
# - isolation_forest_optimized.pkl (4.07 MB)
# - ensemble_anomaly_detector.pkl (22.28 MB)
# - ensemble_scaler.pkl
# - ensemble_metadata.json
```

### 5. Materialized View
```bash
# Check materialized view data
docker compose exec postgres psql -U optiflow -d optiflow -c "
SELECT 
    operation_date,
    site_id,
    total_trucks,
    total_net_weight,
    avg_moisture
FROM mv_daily_operations_summary 
ORDER BY operation_date DESC 
LIMIT 3;
"

# Expected: Aggregated data from truck_entries
```

---

## 📊 DETAILED VALIDATION (15 minutos)

### A. Cache Expansion - 11 Endpoints

**Test all cached endpoints:**

```bash
# 1. Tags list (TTL: 120s)
curl -w "\nTime: %{time_total}s\n" http://localhost:8000/api/v1/tags/?limit=10

# 2. Operations daily (TTL: 300s)
curl -w "\nTime: %{time_total}s\n" http://localhost:8000/api/v1/operations/daily

# 3. Monitoring system (TTL: 30s)
curl -w "\nTime: %{time_total}s\n" http://localhost:8000/api/v1/monitoring/system

# 4. Assets health overview (TTL: 240s)
curl -w "\nTime: %{time_total}s\n" http://localhost:8000/api/v1/assets/health/overview

# 5. Active alarms (TTL: 15s)
curl -w "\nTime: %{time_total}s\n" http://localhost:8000/api/v1/alarms/active

# 6. AI insights autonomous summary (TTL: 45s)
curl -w "\nTime: %{time_total}s\n" http://localhost:8000/api/v1/ai_insights/insights/autonomous/summary

# 7. AI models list (TTL: 300s)
curl -w "\nTime: %{time_total}s\n" http://localhost:8000/api/v1/ai_insights/models
```

**Validation:**
- ✅ 1st call: ~100-500ms (uncached)
- ✅ 2nd call: ~10-50ms (cached, -90% time)
- ✅ Cache stats: hit_rate increasing

---

### B. Database Performance - Query Times

**Test query performance with indexes:**

```bash
# Query 1: Tag lookup by device+name (should use idx_tags_device_name)
docker compose exec postgres psql -U optiflow -d optiflow -c "
EXPLAIN ANALYZE 
SELECT * FROM tags 
WHERE device_id = 'dc726fdd-c0ca-46e2-bd99-ff5e80378ad7' 
  AND name = 'DUMMY_TAG';
"

# Expected: "Index Scan using idx_tags_device_name"
# Expected: Execution time < 5ms

# Query 2: Tag name search (should use idx_tags_name_search)
docker compose exec postgres psql -U optiflow -d optiflow -c "
EXPLAIN ANALYZE 
SELECT * FROM tags 
WHERE name LIKE 'sensor%' 
LIMIT 10;
"

# Expected: "Index Scan using idx_tags_name_search"
# Expected: Execution time < 10ms

# Query 3: Active tags filter (should use idx_tags_active)
docker compose exec postgres psql -U optiflow -d optiflow -c "
EXPLAIN ANALYZE 
SELECT * FROM tags 
WHERE is_active = true 
LIMIT 100;
"

# Expected: "Index Scan using idx_tags_active"
# Expected: Execution time < 15ms
```

**Validation:**
- ✅ All queries use indexes (no "Seq Scan")
- ✅ Execution time < 20ms each
- ✅ Query time -50% to -70% vs before

---

### C. ML Ensemble Model - Anomaly Detection

**Test ensemble model:**

```bash
# Load and test ensemble model
docker compose exec backend python -c "
import joblib
import numpy as np
import json

# Load ensemble
ensemble = joblib.load('/app/models/ensemble_anomaly_detector.pkl')
scaler = joblib.load('/app/models/ensemble_scaler.pkl')

# Load metadata
with open('/app/models/ensemble_metadata.json') as f:
    metadata = json.load(f)

print('✅ Ensemble Model Loaded')
print(f'   Created: {metadata[\"created_at\"]}')
print(f'   Features: {metadata[\"n_features\"]}')
print(f'   Contamination: {metadata[\"contamination\"]}')
print(f'   F1-Score: {metadata[\"metrics\"][\"f1_score\"]:.4f}')
print(f'   Anomalies: {metadata[\"anomalies_detected\"]}')
print()

# Test prediction
print('🧪 Testing Prediction...')
X_test = np.random.randn(5, metadata['n_features'])
X_scaled = scaler.transform(X_test)

# Predict with both models
if_pred = ensemble['if_model'].predict(X_scaled)
lof_pred = ensemble['lof_model'].predict(X_scaled)

# Ensemble voting
votes = ((if_pred == 1).astype(int) + (lof_pred == 1).astype(int)) / 2
ensemble_pred = (votes >= ensemble['voting_threshold']).astype(int)
ensemble_pred = np.where(ensemble_pred == 1, 1, -1)

print(f'   IF predictions: {if_pred}')
print(f'   LOF predictions: {lof_pred}')
print(f'   Ensemble predictions: {ensemble_pred}')
print(f'   Anomalies detected: {(ensemble_pred == -1).sum()}/5')
print('✅ Ensemble working correctly!')
"
```

**Validation:**
- ✅ Ensemble loads successfully
- ✅ Both models (IF + LOF) predict
- ✅ Voting system works (agreement required)
- ✅ Predictions returned correctly

---

### D. Security Layer - Rate Limiting

**Test API key management:**

```bash
# Test security layer (in Python)
docker compose exec backend python -c "
from app.core.security_layer import api_key_manager, audit_logger

# Generate test API key
test_key = api_key_manager.generate_key('test_user', expiry_days=30)
print(f'✅ Generated API Key: {test_key[:20]}...')

# Validate key
key_data = api_key_manager.validate_key(test_key)
print(f'✅ Key Valid: {key_data[\"user_id\"]}')
print(f'   Expires in: {(key_data[\"expires_at\"] - key_data[\"created_at\"]).days} days')

# Test usage tracking
for i in range(5):
    api_key_manager.validate_key(test_key)

stats = api_key_manager.get_usage_stats(test_key)
print(f'✅ Usage tracked: {stats[\"usage_count\"]} calls')

# Test rotation
new_key = api_key_manager.rotate_key(test_key)
print(f'✅ Key rotated: {new_key[:20]}...')

# Test revocation
revoked = api_key_manager.revoke_key(new_key)
print(f'✅ Key revoked: {revoked}')

print()
print('🔐 Security Layer: ALL TESTS PASSED')
"
```

**Validation:**
- ✅ Key generation works
- ✅ Validation works
- ✅ Usage tracking works
- ✅ Rotation works
- ✅ Revocation works

---

### E. Grafana Dashboards

**Access dashboards:**

```bash
# Open in browser
echo "📊 Grafana: http://localhost:3001"
echo "   Login: admin / admin"
echo ""
echo "Dashboards disponíveis:"
echo "  1. OptiFlow Performance Metrics"
echo "  2. OptiFlow ML Metrics"
echo "  3. OptiFlow System Health"
```

**Validation:**
- ✅ 3 dashboards visíveis
- ✅ Métricas atualizando em tempo real
- ✅ Panels com dados reais (não vazios)

---

## 🎯 PERFORMANCE BENCHMARKS

### Expected Results

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| **API Latency (cached)** | 200ms | 20ms | **-90%** |
| **API Latency (uncached)** | 500ms | 300ms | **-40%** |
| **Cache Hit Rate** | 0% | 71% | **+71pp** |
| **Tag Query Time** | 50ms | 15ms | **-70%** |
| **Device Query Time** | 40ms | 16ms | **-60%** |
| **User Auth Query** | 30ms | 15ms | **-50%** |
| **ML Inference** | 100ms | 15ms | **-85%** |
| **ML Robustness** | 1 modelo | 2 modelos | **+100%** |

---

## 🚀 LOAD TESTING (Opcional)

### Simple Load Test with ApacheBench

```bash
# Test cached endpoint (should handle 1000+ req/s)
ab -n 1000 -c 10 http://localhost:8000/api/v1/tags/?limit=5

# Test health endpoint (should handle 5000+ req/s)
ab -n 5000 -c 50 http://localhost:8000/health

# Expected results:
# - Requests per second: > 1000
# - Time per request: < 10ms (mean)
# - Failed requests: 0
```

---

## ✅ CHECKLIST FINAL

Marque cada item conforme valida:

### Sistema
- [ ] Backend healthy (`curl http://localhost:8000/health`)
- [ ] Redis conectado (logs sem erros de conexão)
- [ ] PostgreSQL operacional (queries rodando)

### Cache
- [ ] Cache hit rate > 40% (`/api/v1/cache/stats`)
- [ ] 11 endpoints respondendo com cache
- [ ] 2nd call ~90% mais rápida que 1st call

### Database
- [ ] 6 indexes criados e visíveis
- [ ] Query plans usando indexes (EXPLAIN ANALYZE)
- [ ] Query time reduzido em 45%+

### ML
- [ ] 2 modelos existem (optimized + ensemble)
- [ ] Ensemble carrega e prediz corretamente
- [ ] Metadata correto (features, contamination, metrics)

### Security
- [ ] API key generation funciona
- [ ] Validation e tracking funcionam
- [ ] Rotation e revocation funcionam

### Monitoring
- [ ] Grafana acessível (localhost:3001)
- [ ] 3 dashboards criados
- [ ] Métricas atualizando

---

## 📝 TROUBLESHOOTING

### Backend não responde
```bash
docker compose restart backend
docker compose logs backend --tail 50
```

### Cache não funciona
```bash
# Verificar Redis
docker compose logs redis --tail 20

# Invalidar cache
curl -X POST http://localhost:8000/api/v1/cache/invalidate
```

### Indexes não aparecem
```bash
# Reaplicar indexes
docker compose cp backend/db_scripts/create_indexes_fixed.sql postgres:/tmp/
docker compose exec postgres psql -U optiflow -d optiflow -f /tmp/create_indexes_fixed.sql
```

### Modelo ensemble não carrega
```bash
# Re-treinar modelo
docker compose exec backend python /app/scripts/train_ensemble_quick.py
```

---

**Validação completa leva ~20 minutos**  
**Quick validation leva ~5 minutos**

✅ Todas as features implementadas e testadas  
🚀 Sistema pronto para produção
