#!/bin/bash
# Script to create simulator tags via API
# Uses existing REST endpoints - no SQLAlchemy issues!

API_BASE="http://localhost:8000/api/v1"

echo "=== Creating Simulator Tags via API ==="
echo ""

# Function to create a tag
create_tag() {
    local name=$1
    local description=$2
    local data_type=$3
    local category=$4
    local unit=$5
    local min_value=$6
    local max_value=$7

    echo "Creating tag: $name..."

    curl -s -X POST "$API_BASE/tags/" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$name\",
            \"tag_address\": \"$name\",
            \"description\": \"$description\",
            \"data_type\": \"$data_type\",
            \"category\": \"$category\",
            \"unit\": \"$unit\",
            \"min_value\": $min_value,
            \"max_value\": $max_value,
            \"scale_factor\": 1.0,
            \"offset\": 0.0,
            \"enabled\": true,
            \"log_enabled\": true
        }" > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo "  ✓ Created: $name"
    else
        echo "  ℹ Already exists or error: $name"
    fi
}

# System tags
create_tag "SYSTEM_RUNNING_PV" "System running status" "float" "status" "" 0 1
create_tag "WAREHOUSE_LEVEL_PCT_PV" "Warehouse inventory level" "float" "process" "%" 0 100
create_tag "TOTAL_MASS_T_PV" "Total mass loaded" "float" "process" "t" 0 100000
create_tag "TOTAL_KWH_PV" "Total energy consumed" "float" "energy" "kWh" 0 1000000
create_tag "TEST_COUNTER_PV" "Test counter (0-10)" "integer" "status" "" 0 10

# Gate tags (4 gates, 2 tags each)
for gate_num in {1..4}; do
    gate_id=$(printf "%02d" $gate_num)
    create_tag "ARZ_GATES_GATE${gate_id}_POSICAO_PV" "Gate $gate_num position" "float" "setpoint" "%" 0 100
    create_tag "ARZ_GATES_GATE${gate_id}_VAZAO_TPH_PV" "Gate $gate_num flow rate" "float" "process" "t/h" 0 500
done

echo ""
echo "=== Summary ==="
echo "✅ Tags creation attempted via API"
echo "📊 Autonomous Agent will now monitor these tags"
echo "💡 Values come from InfluxDB (Kafka → InfluxDB Consumer)"
echo ""
echo "Note: Some tags may already exist (that's OK!)"
