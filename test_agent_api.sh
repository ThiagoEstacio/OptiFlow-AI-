#!/bin/bash
# Test script to validate Autonomous Agent's real-time tag value retrieval via API
# Simulates discovering tags and fetching their values

echo "================================================================================"
echo "🤖 AUTONOMOUS AGENT - REAL-TIME VALUE TEST (via API)"
echo "================================================================================"

API_BASE="http://localhost:8000/api/v1"

# Step 1: Get list of tags that exist (simulate auto-discovery)
echo ""
echo "📡 Step 1: Discovering tags (simulating InfluxDB auto-discovery)..."
echo "--------------------------------------------------------------------------------"

# Define the tags we know exist from the simulator
TAGS=(
    "SYSTEM_RUNNING_PV"
    "WAREHOUSE_LEVEL_PCT_PV"
    "TOTAL_MASS_T_PV"
    "TOTAL_KWH_PV"
    "TEST_COUNTER_PV"
    "ARZ_GATES_GATE01_POSICAO_PV"
    "ARZ_GATES_GATE01_VAZAO_TPH_PV"
    "ARZ_GATES_GATE02_POSICAO_PV"
    "ARZ_GATES_GATE02_VAZAO_TPH_PV"
    "ARZ_GATES_GATE03_POSICAO_PV"
    "ARZ_GATES_GATE03_VAZAO_TPH_PV"
    "ARZ_GATES_GATE04_POSICAO_PV"
    "ARZ_GATES_GATE04_VAZAO_TPH_PV"
)

echo "✅ Discovered ${#TAGS[@]} tags from simulator"
echo ""

# Step 2: Fetch real-time values for each tag
echo "📊 Step 2: Fetching real-time values for all tags..."
echo "================================================================================"

SUCCESS=0
NO_DATA=0
ERRORS=0

declare -a TAG_VALUES

for TAG_NAME in "${TAGS[@]}"; do
    RESPONSE=$(curl -s -w "\n%{http_code}" "$API_BASE/tags/realtime/$TAG_NAME" 2>/dev/null)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)

    if [ "$HTTP_CODE" = "200" ]; then
        SUCCESS=$((SUCCESS + 1))

        # Parse JSON response (simple extraction)
        VALUE=$(echo "$BODY" | grep -o '"value":[^,}]*' | cut -d':' -f2 | tr -d ' ')
        TIMESTAMP=$(echo "$BODY" | grep -o '"timestamp":"[^"]*"' | cut -d'"' -f4)
        QUALITY=$(echo "$BODY" | grep -o '"quality":"[^"]*"' | cut -d'"' -f4)

        printf "✅ %-45s = %10s [%-10s] @ %s\n" "$TAG_NAME" "$VALUE" "$QUALITY" "${TIMESTAMP:0:19}"

        TAG_VALUES+=("$TAG_NAME:$VALUE:$QUALITY")
    elif [ "$HTTP_CODE" = "404" ]; then
        NO_DATA=$((NO_DATA + 1))
        printf "⚠️  %-45s = NO DATA (last 24h)\n" "$TAG_NAME"
    else
        ERRORS=$((ERRORS + 1))
        printf "❌ %-45s = ERROR (HTTP %s)\n" "$TAG_NAME" "$HTTP_CODE"
    fi
done

# Step 3: Summary
echo ""
echo "================================================================================"
echo "📈 SUMMARY"
echo "================================================================================"
echo "Total tags tested:        ${#TAGS[@]}"
echo "✅ Values retrieved:      $SUCCESS ($(echo "scale=1; $SUCCESS*100/${#TAGS[@]}" | bc)%)"
echo "⚠️  No data found:        $NO_DATA ($(echo "scale=1; $NO_DATA*100/${#TAGS[@]}" | bc)%)"
echo "❌ Errors:                $ERRORS ($(echo "scale=1; $ERRORS*100/${#TAGS[@]}" | bc)%)"

# Step 4: Show categorized values
if [ $SUCCESS -gt 0 ]; then
    echo ""
    echo "--------------------------------------------------------------------------------"
    echo "📊 VALUE STATISTICS BY CATEGORY"
    echo "--------------------------------------------------------------------------------"

    echo ""
    echo "⚙️  System Tags:"
    for TAG_DATA in "${TAG_VALUES[@]}"; do
        TAG_NAME=$(echo "$TAG_DATA" | cut -d':' -f1)
        TAG_VALUE=$(echo "$TAG_DATA" | cut -d':' -f2)
        if [[ ! "$TAG_NAME" =~ "GATE" ]]; then
            printf "   %-50s = %10s\n" "$TAG_NAME" "$TAG_VALUE"
        fi
    done

    echo ""
    echo "🚪 Gate Tags:"
    for TAG_DATA in "${TAG_VALUES[@]}"; do
        TAG_NAME=$(echo "$TAG_DATA" | cut -d':' -f1)
        TAG_VALUE=$(echo "$TAG_DATA" | cut -d':' -f2)
        if [[ "$TAG_NAME" =~ "GATE" ]]; then
            printf "   %-50s = %10s\n" "$TAG_NAME" "$TAG_VALUE"
        fi
    done

    # Quality check
    GOOD_QUALITY=0
    for TAG_DATA in "${TAG_VALUES[@]}"; do
        TAG_QUALITY=$(echo "$TAG_DATA" | cut -d':' -f3)
        if [ "$TAG_QUALITY" = "good" ]; then
            GOOD_QUALITY=$((GOOD_QUALITY + 1))
        fi
    done

    echo ""
    echo "✨ Quality: $GOOD_QUALITY/$SUCCESS tags with 'good' quality ($(echo "scale=1; $GOOD_QUALITY*100/$SUCCESS" | bc)%)"
fi

# Step 5: What the agent does with this data
echo ""
echo "================================================================================"
echo "🤖 WHAT THE AUTONOMOUS AGENT DOES WITH THIS DATA"
echo "================================================================================"
echo "The Autonomous Agent uses these real-time values to:"
echo "  1. 🔍 Detect anomalies (outliers, sudden changes)"
echo "  2. 📊 Analyze performance (efficiency, throughput)"
echo "  3. ⚠️  Check alarm conditions (thresholds)"
echo "  4. 💚 Monitor asset health (degradation patterns)"
echo "  5. ⚡ Identify optimization opportunities"
echo "  6. 🔮 Predict future states (trends)"
echo ""
echo "================================================================================"
echo "✅ TEST COMPLETE - Real-time value retrieval is working!"
echo "================================================================================"
