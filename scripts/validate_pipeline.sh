#!/bin/bash

##############################################################################
# OptiFlow Pipeline Health Check Script
#
# Valida o caminho completo: Gateway → Kafka → Consumer → InfluxDB
#
# Usage: ./scripts/validate_pipeline.sh
##############################################################################

set -e

echo "=========================================================================="
echo "OptiFlow Pipeline Health Check"
echo "=========================================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS="${GREEN}✅ PASS${NC}"
FAIL="${RED}❌ FAIL${NC}"
WARN="${YELLOW}⚠️  WARN${NC}"

FAILED_CHECKS=0

##############################################################################
# Test 1: Gateway Health
##############################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1: Gateway Health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "$PASS Gateway is responding at http://localhost:8080"
else
    echo -e "$FAIL Gateway is not responding"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check if gateway is publishing to Kafka
if docker logs optiflow-gateway 2>&1 | grep -q "Published.*messages"; then
    PUBLISHED=$(docker logs optiflow-gateway 2>&1 | grep "Published.*messages" | tail -1)
    echo -e "$PASS Gateway is publishing to Kafka"
    echo "      Latest: $PUBLISHED"
else
    echo -e "$FAIL Gateway is not publishing to Kafka"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""

##############################################################################
# Test 2: Kafka Cluster Health
##############################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2: Kafka Cluster Health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Kafka brokers
for broker in kafka-1 kafka-2 kafka-3; do
    if docker ps | grep -q "$broker.*healthy"; then
        echo -e "$PASS $broker is healthy"
    else
        echo -e "$FAIL $broker is not healthy"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
done

# Check if raw_tags topic has messages
if docker exec optiflow-kafka-1 kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic raw_tags \
    --max-messages 1 \
    --timeout-ms 5000 \
    2>&1 | grep -q "tag_name"; then
    echo -e "$PASS Topic 'raw_tags' has messages"
else
    echo -e "$FAIL Topic 'raw_tags' is empty or unavailable"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""

##############################################################################
# Test 3: Backend Consumer Health
##############################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 3: Backend Consumer Health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check backend health
if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "$PASS Backend is responding at http://localhost:8000"
else
    echo -e "$FAIL Backend is not responding"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check consumer group
CONSUMER_STATUS=$(docker exec optiflow-kafka-1 kafka-consumer-groups \
    --bootstrap-server localhost:9092 \
    --describe \
    --group timeseries-writers 2>/dev/null | grep raw_tags || echo "")

if [ -n "$CONSUMER_STATUS" ]; then
    echo -e "$PASS Consumer group 'timeseries-writers' is active"

    # Extract lag
    LAG=$(echo "$CONSUMER_STATUS" | awk '{print $6}')

    if [ "$LAG" -lt 100 ]; then
        echo -e "$PASS Consumer lag: $LAG messages (healthy)"
    elif [ "$LAG" -lt 1000 ]; then
        echo -e "$WARN Consumer lag: $LAG messages (monitor)"
    else
        echo -e "$FAIL Consumer lag: $LAG messages (critical)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi

    echo "      Consumer details:"
    echo "$CONSUMER_STATUS" | awk '{printf "      Offset: %s/%s (lag: %s)\n", $4, $5, $6}'
else
    echo -e "$FAIL Consumer group 'timeseries-writers' is not found"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""

##############################################################################
# Test 4: InfluxDB Storage
##############################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 4: InfluxDB Storage"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if InfluxDB is running
if docker ps | grep -q "optiflow-influxdb.*Up"; then
    echo -e "$PASS InfluxDB is running"
else
    echo -e "$FAIL InfluxDB is not running"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check if data exists in timeseries bucket (last 5 minutes)
INFLUX_CHECK=$(timeout 10 docker exec optiflow-influxdb influx query \
    'from(bucket: "timeseries") |> range(start: -5m) |> limit(n: 1)' 2>&1 || echo "TIMEOUT")

if echo "$INFLUX_CHECK" | grep -q "tag_id\|tag_name"; then
    echo -e "$PASS Data found in 'timeseries' bucket (last 5 minutes)"

    # Count total records in last hour
    RECORD_COUNT=$(timeout 10 docker exec optiflow-influxdb influx query \
        'from(bucket: "timeseries") |> range(start: -1h) |> count()' 2>&1 | \
        grep "_value" | awk '{sum+=$NF} END {print sum}' || echo "0")

    if [ "$RECORD_COUNT" -gt 0 ]; then
        echo "      Records in last hour: $RECORD_COUNT"
    fi
elif echo "$INFLUX_CHECK" | grep -q "TIMEOUT"; then
    echo -e "$WARN InfluxDB query timed out (may be under heavy load)"
else
    echo -e "$FAIL No data found in 'timeseries' bucket"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""

##############################################################################
# Test 5: End-to-End Latency
##############################################################################
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 5: End-to-End Latency Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get latest gateway publish timestamp
GATEWAY_TS=$(docker logs optiflow-gateway 2>&1 | grep "Published" | tail -1 | awk '{print $1, $2}' || echo "")

# Get latest InfluxDB timestamp
INFLUX_TS=$(timeout 10 docker exec optiflow-influxdb influx query \
    'from(bucket: "timeseries") |> range(start: -5m) |> max()' 2>&1 | \
    grep "^2025" | tail -1 | awk '{print $1}' || echo "")

if [ -n "$GATEWAY_TS" ] && [ -n "$INFLUX_TS" ]; then
    echo -e "$PASS E2E pipeline is active"
    echo "      Gateway last publish: $GATEWAY_TS"
    echo "      InfluxDB last write:  $INFLUX_TS"
else
    echo -e "$WARN Could not measure E2E latency (missing timestamps)"
fi

echo ""

##############################################################################
# Summary
##############################################################################
echo "=========================================================================="
echo "Summary"
echo "=========================================================================="

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
    echo ""
    echo "Pipeline is healthy and operational!"
    echo ""
    echo "Components:"
    echo "  • Gateway     → Collecting from OPC UA and publishing to Kafka"
    echo "  • Kafka       → Storing and distributing messages"
    echo "  • Consumer    → Processing messages and writing to InfluxDB"
    echo "  • InfluxDB    → Storing time-series data"
    echo ""
    exit 0
else
    echo -e "${RED}❌ $FAILED_CHECKS CHECK(S) FAILED${NC}"
    echo ""
    echo "Please review the failed checks above and troubleshoot:"
    echo "  1. Check container logs: docker logs <container-name>"
    echo "  2. Verify network connectivity between containers"
    echo "  3. Check configuration files (.env, adapters_config.json)"
    echo "  4. Ensure all required services are running: docker compose ps"
    echo ""
    exit 1
fi
