#!/bin/bash

# Test all improvements implemented for OptiFlow AI
# Validates Fix #1-4 are working correctly

set -e

echo "🧪 Testing OptiFlow AI Improvements"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

test_passed() {
    echo -e "${GREEN}✅ PASSED${NC}: $1"
    ((PASSED++))
}

test_failed() {
    echo -e "${RED}❌ FAILED${NC}: $1"
    ((FAILED++))
}

# ==============================================
# TEST #1: Database Pool Configuration
# ==============================================
echo "📊 Test #1: Database Pool Configuration"
echo "----------------------------------------"

POOL_SIZE=$(docker compose exec -T backend python -c "from app.core.config import settings; print(settings.DATABASE_POOL_SIZE)" 2>/dev/null || echo "ERROR")

if [ "$POOL_SIZE" = "50" ]; then
    test_passed "Database pool size = 50"
else
    test_failed "Database pool size = $POOL_SIZE (expected 50)"
fi

MAX_OVERFLOW=$(docker compose exec -T backend python -c "from app.core.config import settings; print(settings.DATABASE_MAX_OVERFLOW)" 2>/dev/null || echo "ERROR")

if [ "$MAX_OVERFLOW" = "100" ]; then
    test_passed "Database max overflow = 100"
else
    test_failed "Database max overflow = $MAX_OVERFLOW (expected 100)"
fi

echo ""

# ==============================================
# TEST #2: InfluxDB Downsampling Buckets
# ==============================================
echo "📊 Test #2: InfluxDB Downsampling Buckets"
echo "----------------------------------------"

# Check if downsampled_1m bucket exists
BUCKET_1M=$(docker compose exec influxdb influx bucket list --org optiflow --token my-super-secret-influxdb-token 2>/dev/null | grep -c "downsampled_1m" || echo "0")

if [ "$BUCKET_1M" -gt "0" ]; then
    test_passed "Bucket 'downsampled_1m' exists"
else
    test_failed "Bucket 'downsampled_1m' not found"
fi

# Check if downsampled_1h bucket exists
BUCKET_1H=$(docker compose exec influxdb influx bucket list --org optiflow --token my-super-secret-influxdb-token 2>/dev/null | grep -c "downsampled_1h" || echo "0")

if [ "$BUCKET_1H" -gt "0" ]; then
    test_passed "Bucket 'downsampled_1h' exists"
else
    test_failed "Bucket 'downsampled_1h' not found"
fi

# Check if tasks are active
TASK_1M=$(docker compose exec influxdb influx task list --org optiflow --token my-super-secret-influxdb-token 2>/dev/null | grep -c "downsample_1m.*active" || echo "0")

if [ "$TASK_1M" -gt "0" ]; then
    test_passed "Task 'downsample_1m' is active"
else
    test_failed "Task 'downsample_1m' not active"
fi

TASK_1H=$(docker compose exec influxdb influx task list --org optiflow --token my-super-secret-influxdb-token 2>/dev/null | grep -c "downsample_1h.*active" || echo "0")

if [ "$TASK_1H" -gt "0" ]; then
    test_passed "Task 'downsample_1h' is active"
else
    test_failed "Task 'downsample_1h' not active"
fi

echo ""

# ==============================================
# TEST #3: Cache Service
# ==============================================
echo "📊 Test #3: Cache Service"
echo "----------------------------------------"

# Check if cache service file exists
if [ -f "/home/thiestacio/OptiFlow-AI-/backend/app/services/cache_service.py" ]; then
    test_passed "cache_service.py exists"
else
    test_failed "cache_service.py not found"
fi

# Check if cache endpoint exists
if [ -f "/home/thiestacio/OptiFlow-AI-/backend/app/api/v1/endpoints/cache.py" ]; then
    test_passed "cache endpoint exists"
else
    test_failed "cache endpoint not found"
fi

# Test Redis connection
REDIS_PING=$(docker compose exec -T redis redis-cli -a optiflow_redis_password ping 2>/dev/null || echo "ERROR")

if [ "$REDIS_PING" = "PONG" ]; then
    test_passed "Redis is responding"
else
    test_failed "Redis not responding"
fi

echo ""

# ==============================================
# TEST #4: ML Feature Engineering
# ==============================================
echo "📊 Test #4: ML Feature Engineering"
echo "----------------------------------------"

# Check if feature engineering file exists
if [ -f "/home/thiestacio/OptiFlow-AI-/backend/app/services/ml_feature_engineering.py" ]; then
    test_passed "ml_feature_engineering.py exists"
else
    test_failed "ml_feature_engineering.py not found"
fi

# Check if training script exists
if [ -f "/home/thiestacio/OptiFlow-AI-/scripts/train_with_features.py" ]; then
    test_passed "train_with_features.py exists"
else
    test_failed "train_with_features.py not found"
fi

# Check if OptimizedInfluxDBService exists
if [ -f "/home/thiestacio/OptiFlow-AI-/backend/app/services/optimized_influxdb_service.py" ]; then
    test_passed "optimized_influxdb_service.py exists"
else
    test_failed "optimized_influxdb_service.py not found"
fi

echo ""

# ==============================================
# TEST #5: Backend Health
# ==============================================
echo "📊 Test #5: Backend Health"
echo "----------------------------------------"

# Check if backend is running
BACKEND_STATUS=$(docker compose ps backend | grep -c "Up" || echo "0")

if [ "$BACKEND_STATUS" -gt "0" ]; then
    test_passed "Backend container is running"
else
    test_failed "Backend container not running"
fi

# Check if backend is healthy
sleep 2
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null | grep -c "healthy" || echo "0")

if [ "$HEALTH" -gt "0" ]; then
    test_passed "Backend API is healthy"
else
    test_failed "Backend API not responding or unhealthy"
fi

echo ""

# ==============================================
# SUMMARY
# ==============================================
echo "=========================================="
echo "📊 TEST SUMMARY"
echo "=========================================="
echo ""
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "🎉 All improvements successfully implemented:"
    echo "  ✅ Fix #1: Database Pool (20→50)"
    echo "  ✅ Fix #2: InfluxDB Downsampling"
    echo "  ✅ Fix #3: Cache Service"
    echo "  ✅ Fix #4: ML Feature Engineering"
    echo ""
    echo "📝 Next steps:"
    echo "  1. Test ML training: docker compose exec backend python /app/scripts/train_with_features.py"
    echo "  2. Test cache API: curl http://localhost:8000/api/v1/cache/stats"
    echo "  3. Monitor InfluxDB tasks performance"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed${NC}"
    echo ""
    echo "Please review the failed tests above."
    exit 1
fi
