#!/bin/bash

# System Health Overview - Verificar melhorias implementadas
# Verifica: DB Pool, InfluxDB, Cache, ML Model

set -e

echo "============================================================"
echo "🏥 OPTIFLOW AI - SYSTEM HEALTH OVERVIEW"
echo "============================================================"
echo "Data: $(date)"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Scores
TOTAL_SCORE=0
MAX_SCORE=0

print_score() {
    local component=$1
    local score=$2
    local max=$3
    local percentage=$((score * 100 / max))
    
    if [ $percentage -ge 80 ]; then
        color=$GREEN
        status="✅ EXCELENTE"
    elif [ $percentage -ge 60 ]; then
        color=$YELLOW
        status="⚠️  BOM"
    else
        color=$RED
        status="❌ PRECISA MELHORAR"
    fi
    
    echo -e "${color}${component}: ${score}/${max} (${percentage}%) ${status}${NC}"
    TOTAL_SCORE=$((TOTAL_SCORE + score))
    MAX_SCORE=$((MAX_SCORE + max))
}

echo "============================================================"
echo "📊 1. DATABASE POOL CONFIGURATION"
echo "============================================================"

# Check database pool
POOL_SIZE=$(docker compose exec -T backend python -c "
from app.core.config import settings
print(settings.DATABASE_POOL_SIZE)
" 2>/dev/null | tail -1)

MAX_OVERFLOW=$(docker compose exec -T backend python -c "
from app.core.config import settings
print(settings.DATABASE_MAX_OVERFLOW)
" 2>/dev/null | tail -1)

echo "Pool Size: $POOL_SIZE"
echo "Max Overflow: $MAX_OVERFLOW"
echo "Total Capacity: $((POOL_SIZE + MAX_OVERFLOW)) connections"

DB_SCORE=0
if [ "$POOL_SIZE" -ge 50 ]; then
    echo -e "${GREEN}✅ Pool size adequado (≥50)${NC}"
    DB_SCORE=$((DB_SCORE + 5))
else
    echo -e "${YELLOW}⚠️  Pool size pode ser melhorado${NC}"
    DB_SCORE=$((DB_SCORE + 2))
fi

if [ "$MAX_OVERFLOW" -ge 100 ]; then
    echo -e "${GREEN}✅ Overflow adequado (≥100)${NC}"
    DB_SCORE=$((DB_SCORE + 5))
else
    echo -e "${YELLOW}⚠️  Overflow pode ser melhorado${NC}"
    DB_SCORE=$((DB_SCORE + 2))
fi

print_score "Database Pool" $DB_SCORE 10
echo ""

echo "============================================================"
echo "📊 2. INFLUXDB DOWNSAMPLING"
echo "============================================================"

# Check InfluxDB buckets
BUCKETS=$(docker compose exec -T influxdb influx bucket list --json 2>/dev/null | jq -r '.[].name' | grep -E "downsampled|timeseries" || echo "")

if echo "$BUCKETS" | grep -q "downsampled_1m"; then
    echo -e "${GREEN}✅ Bucket downsampled_1m existe${NC}"
    INFLUX_SCORE=5
else
    echo -e "${RED}❌ Bucket downsampled_1m não encontrado${NC}"
    INFLUX_SCORE=0
fi

if echo "$BUCKETS" | grep -q "downsampled_1h"; then
    echo -e "${GREEN}✅ Bucket downsampled_1h existe${NC}"
    INFLUX_SCORE=$((INFLUX_SCORE + 5))
else
    echo -e "${RED}❌ Bucket downsampled_1h não encontrado${NC}"
fi

# Check tasks
TASKS=$(docker compose exec -T influxdb influx task list --json 2>/dev/null | jq -r '.[].name' | grep -E "downsample" || echo "")

if echo "$TASKS" | grep -q "downsample_1m"; then
    echo -e "${GREEN}✅ Task downsample_1m ativa${NC}"
    INFLUX_SCORE=$((INFLUX_SCORE + 3))
else
    echo -e "${YELLOW}⚠️  Task downsample_1m não encontrada${NC}"
fi

if echo "$TASKS" | grep -q "downsample_1h"; then
    echo -e "${GREEN}✅ Task downsample_1h ativa${NC}"
    INFLUX_SCORE=$((INFLUX_SCORE + 2))
else
    echo -e "${YELLOW}⚠️  Task downsample_1h não encontrada${NC}"
fi

print_score "InfluxDB Downsampling" $INFLUX_SCORE 15
echo ""

echo "============================================================"
echo "📊 3. CACHE SERVICE"
echo "============================================================"

# Check Redis
if docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✅ Redis respondendo${NC}"
    CACHE_SCORE=5
else
    echo -e "${RED}❌ Redis não está respondendo${NC}"
    CACHE_SCORE=0
fi

# Check cache service file
if [ -f "backend/app/services/cache_service.py" ]; then
    echo -e "${GREEN}✅ CacheService implementado${NC}"
    CACHE_SCORE=$((CACHE_SCORE + 5))
else
    echo -e "${RED}❌ CacheService não encontrado${NC}"
fi

# Check cache endpoint
if [ -f "backend/app/api/v1/endpoints/cache.py" ]; then
    echo -e "${GREEN}✅ Cache API endpoint criado${NC}"
    CACHE_SCORE=$((CACHE_SCORE + 3))
else
    echo -e "${YELLOW}⚠️  Cache API endpoint não encontrado${NC}"
fi

# Try to get cache stats
CACHE_STATS=$(curl -s http://localhost:8000/api/v1/cache/stats 2>/dev/null || echo "")
if echo "$CACHE_STATS" | grep -q "connected"; then
    echo -e "${GREEN}✅ Cache API respondendo${NC}"
    CACHE_SCORE=$((CACHE_SCORE + 2))
else
    echo -e "${YELLOW}⚠️  Cache API não configurada ainda${NC}"
fi

print_score "Cache Service" $CACHE_SCORE 15
echo ""

echo "============================================================"
echo "📊 4. ML FEATURE ENGINEERING"
echo "============================================================"

# Check feature engineering service
if [ -f "backend/app/services/ml_feature_engineering.py" ]; then
    echo -e "${GREEN}✅ FeatureEngineer implementado${NC}"
    ML_SCORE=5
    
    # Count features
    FEATURES=$(grep -E "def _add_|# ===" backend/app/services/ml_feature_engineering.py | wc -l || echo 0)
    if [ "$FEATURES" -ge 6 ]; then
        echo -e "${GREEN}✅ 6+ grupos de features implementados${NC}"
        ML_SCORE=$((ML_SCORE + 5))
    fi
else
    echo -e "${RED}❌ FeatureEngineer não encontrado${NC}"
    ML_SCORE=0
fi

# Check trained model
if [ -f "backend/models/isolation_forest_features.pkl" ] || docker compose exec -T backend test -f /app/models/isolation_forest_features.pkl 2>/dev/null; then
    echo -e "${GREEN}✅ Modelo treinado existe${NC}"
    ML_SCORE=$((ML_SCORE + 3))
    
    # Check metrics
    if [ -f "backend/models/metrics_features.json" ] || docker compose exec -T backend test -f /app/models/metrics_features.json 2>/dev/null; then
        echo -e "${GREEN}✅ Métricas salvas${NC}"
        ML_SCORE=$((ML_SCORE + 2))
        
        # Try to read F1-score
        F1_SCORE=$(docker compose exec -T backend cat /app/models/metrics_features.json 2>/dev/null | jq -r '.f1_score' 2>/dev/null || echo "0")
        if [ "$F1_SCORE" != "0" ] && [ "$F1_SCORE" != "null" ]; then
            echo -e "${GREEN}✅ F1-Score: $F1_SCORE${NC}"
            
            # Check if meets target
            if [ "$(echo "$F1_SCORE >= 0.25" | bc -l 2>/dev/null || echo 0)" -eq 1 ]; then
                echo -e "${GREEN}🎉 F1-Score atinge target (≥0.25)!${NC}"
                ML_SCORE=$((ML_SCORE + 5))
            else
                echo -e "${YELLOW}⚠️  F1-Score abaixo do target${NC}"
                ML_SCORE=$((ML_SCORE + 2))
            fi
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Modelo ainda não treinado${NC}"
fi

print_score "ML Feature Engineering" $ML_SCORE 20
echo ""

echo "============================================================"
echo "📊 5. OPTIMIZED SERVICES"
echo "============================================================"

OPT_SCORE=0

# Check OptimizedInfluxDBService
if [ -f "backend/app/services/optimized_influxdb_service.py" ]; then
    echo -e "${GREEN}✅ OptimizedInfluxDBService criado${NC}"
    OPT_SCORE=$((OPT_SCORE + 5))
else
    echo -e "${YELLOW}⚠️  OptimizedInfluxDBService não encontrado${NC}"
fi

# Check if integrated in main.py
if grep -q "optimized_influxdb_service" backend/app/main.py 2>/dev/null; then
    echo -e "${GREEN}✅ OptimizedInfluxDBService integrado${NC}"
    OPT_SCORE=$((OPT_SCORE + 3))
else
    echo -e "${YELLOW}⚠️  OptimizedInfluxDBService não integrado ainda${NC}"
fi

# Check cache decorator usage
CACHED_ENDPOINTS=$(grep -r "@cached" backend/app/api/v1/endpoints/*.py 2>/dev/null | wc -l || echo 0)
if [ "$CACHED_ENDPOINTS" -gt 0 ]; then
    echo -e "${GREEN}✅ $CACHED_ENDPOINTS endpoints usando @cached${NC}"
    OPT_SCORE=$((OPT_SCORE + 2))
else
    echo -e "${YELLOW}⚠️  Cache decorator não aplicado aos endpoints ainda${NC}"
fi

print_score "Optimized Services" $OPT_SCORE 10
echo ""

echo "============================================================"
echo "📊 6. SYSTEM RESOURCES"
echo "============================================================"

# Check containers
BACKEND_STATUS=$(docker compose ps backend --format json 2>/dev/null | jq -r '.[0].State' 2>/dev/null || echo "unknown")
POSTGRES_STATUS=$(docker compose ps postgres --format json 2>/dev/null | jq -r '.[0].State' 2>/dev/null || echo "unknown")
INFLUXDB_STATUS=$(docker compose ps influxdb --format json 2>/dev/null | jq -r '.[0].State' 2>/dev/null || echo "unknown")
REDIS_STATUS=$(docker compose ps redis --format json 2>/dev/null | jq -r '.[0].State' 2>/dev/null || echo "unknown")

SYS_SCORE=0
[ "$BACKEND_STATUS" = "running" ] && echo -e "${GREEN}✅ Backend running${NC}" && SYS_SCORE=$((SYS_SCORE + 3)) || echo -e "${RED}❌ Backend not running${NC}"
[ "$POSTGRES_STATUS" = "running" ] && echo -e "${GREEN}✅ PostgreSQL running${NC}" && SYS_SCORE=$((SYS_SCORE + 2)) || echo -e "${RED}❌ PostgreSQL not running${NC}"
[ "$INFLUXDB_STATUS" = "running" ] && echo -e "${GREEN}✅ InfluxDB running${NC}" && SYS_SCORE=$((SYS_SCORE + 3)) || echo -e "${RED}❌ InfluxDB not running${NC}"
[ "$REDIS_STATUS" = "running" ] && echo -e "${GREEN}✅ Redis running${NC}" && SYS_SCORE=$((SYS_SCORE + 2)) || echo -e "${RED}❌ Redis not running${NC}"

print_score "System Resources" $SYS_SCORE 10
echo ""

echo "============================================================"
echo "🎯 OVERALL HEALTH SCORE"
echo "============================================================"

PERCENTAGE=$((TOTAL_SCORE * 100 / MAX_SCORE))

echo "Total Score: $TOTAL_SCORE / $MAX_SCORE"
echo ""

if [ $PERCENTAGE -ge 90 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   🎉 SISTEMA EXCELENTE: ${PERCENTAGE}%         ║${NC}"
    echo -e "${GREEN}║   Todas melhorias implementadas!      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
elif [ $PERCENTAGE -ge 75 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✅ SISTEMA ÓTIMO: ${PERCENTAGE}%            ║${NC}"
    echo -e "${GREEN}║   Principais melhorias ativas         ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
elif [ $PERCENTAGE -ge 60 ]; then
    echo -e "${YELLOW}╔════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║   ⚠️  SISTEMA BOM: ${PERCENTAGE}%             ║${NC}"
    echo -e "${YELLOW}║   Algumas melhorias precisam integração║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════╝${NC}"
else
    echo -e "${RED}╔════════════════════════════════════════╗${NC}"
    echo -e "${RED}║   ❌ SISTEMA PRECISA MELHORAR: ${PERCENTAGE}%   ║${NC}"
    echo -e "${RED}║   Implementar melhorias restantes      ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════╝${NC}"
fi

echo ""
echo "============================================================"
echo "📋 RECOMENDAÇÕES"
echo "============================================================"

if [ $CACHE_SCORE -lt 10 ]; then
    echo "• Integrar @cached decorator nos endpoints principais"
fi

if [ $OPT_SCORE -lt 8 ]; then
    echo "• Integrar OptimizedInfluxDBService nos serviços"
fi

if [ $ML_SCORE -lt 15 ]; then
    echo "• Treinar modelo ML com feature engineering"
fi

if [ $TOTAL_SCORE -eq $MAX_SCORE ]; then
    echo -e "${GREEN}✨ Nenhuma recomendação - sistema perfeito!${NC}"
fi

echo ""
echo "Relatório gerado em: $(date)"
echo "============================================================"
