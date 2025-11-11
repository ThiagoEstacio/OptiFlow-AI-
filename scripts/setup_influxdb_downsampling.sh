#!/bin/bash

# Setup InfluxDB Downsampling for OptiFlow AI
# This creates buckets and continuous queries (tasks) for data aggregation

set -e

echo "🔧 Setting up InfluxDB Downsampling..."

# InfluxDB connection settings
INFLUXDB_URL="http://localhost:8086"
INFLUXDB_TOKEN="my-super-secret-influxdb-token"
INFLUXDB_ORG="optiflow"

# Check if influx CLI is available
if ! command -v influx &> /dev/null; then
    echo "⚠️  influx CLI not found. Installing inside container..."
    docker compose exec influxdb sh -c "command -v influx" || {
        echo "❌ InfluxDB container not running"
        exit 1
    }
fi

echo "📦 Step 1: Creating downsampled buckets..."

# Create 1-minute downsampled bucket (30 days retention)
docker compose exec influxdb influx bucket create \
    --name downsampled_1m \
    --org optiflow \
    --retention 720h \
    --token "$INFLUXDB_TOKEN" \
    2>/dev/null || echo "  ℹ️  Bucket downsampled_1m already exists"

# Create 1-hour downsampled bucket (365 days retention)
docker compose exec influxdb influx bucket create \
    --name downsampled_1h \
    --org optiflow \
    --retention 8760h \
    --token "$INFLUXDB_TOKEN" \
    2>/dev/null || echo "  ℹ️  Bucket downsampled_1h already exists"

echo "✅ Buckets created successfully"

echo "⚙️  Step 2: Creating continuous query tasks..."

# Task 1: Downsample to 1 minute
cat > /tmp/downsample_1m.flux << 'EOF'
option task = {name: "downsample_1m", every: 1m, offset: 30s}

from(bucket: "timeseries")
  |> range(start: -2m)
  |> filter(fn: (r) => r._measurement == "sensor_data")
  |> aggregateWindow(
      every: 1m,
      fn: mean,
      createEmpty: false
    )
  |> set(key: "_measurement", value: "sensor_data")
  |> to(bucket: "downsampled_1m", org: "optiflow")
EOF

docker compose exec -T influxdb influx task create \
    --org optiflow \
    --token "$INFLUXDB_TOKEN" \
    < /tmp/downsample_1m.flux \
    2>/dev/null || echo "  ℹ️  Task downsample_1m already exists"

# Task 2: Downsample to 1 hour
cat > /tmp/downsample_1h.flux << 'EOF'
option task = {name: "downsample_1h", every: 1h, offset: 5m}

from(bucket: "downsampled_1m")
  |> range(start: -2h)
  |> filter(fn: (r) => r._measurement == "sensor_data")
  |> aggregateWindow(
      every: 1h,
      fn: mean,
      createEmpty: false
    )
  |> set(key: "_measurement", value: "sensor_data")
  |> to(bucket: "downsampled_1h", org: "optiflow")
EOF

docker compose exec -T influxdb influx task create \
    --org optiflow \
    --token "$INFLUXDB_TOKEN" \
    < /tmp/downsample_1h.flux \
    2>/dev/null || echo "  ℹ️  Task downsample_1h already exists"

echo "✅ Tasks created successfully"

echo "📊 Step 3: Verifying setup..."

# List buckets
echo ""
echo "Buckets:"
docker compose exec influxdb influx bucket list \
    --org optiflow \
    --token "$INFLUXDB_TOKEN" \
    | grep -E "(timeseries|downsampled)"

# List tasks
echo ""
echo "Tasks:"
docker compose exec influxdb influx task list \
    --org optiflow \
    --token "$INFLUXDB_TOKEN" \
    | grep -E "(downsample|ID)"

echo ""
echo "✅ InfluxDB Downsampling setup complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Update Python code to use new buckets"
echo "  2. Verify query performance improvement"
echo "  3. Monitor task execution"
echo ""
echo "🔍 To monitor tasks:"
echo "  docker compose exec influxdb influx task run list --task-id <TASK_ID>"
