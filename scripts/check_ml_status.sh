#!/bin/bash
# Quick status check do treinamento ML

echo "🔍 ML Training Status Check"
echo "================================"
echo ""

# Check Isolation Forest
if docker compose exec backend test -f /app/models/isolation_forest.joblib 2>/dev/null; then
    echo "✅ Isolation Forest: TRAINED"
    IF_TIME=$(docker compose exec backend stat -c %y /app/models/isolation_forest.joblib 2>/dev/null | cut -d'.' -f1)
    echo "   └─ Timestamp: $IF_TIME"
    IF_SIZE=$(docker compose exec backend stat -c %s /app/models/isolation_forest.joblib 2>/dev/null)
    echo "   └─ Size: $((IF_SIZE / 1024)) KB"
else
    echo "❌ Isolation Forest: NOT FOUND"
fi

echo ""

# Check LSTM
if docker compose exec backend test -f /app/models/lstm_autoencoder.h5 2>/dev/null; then
    echo "✅ LSTM Autoencoder: TRAINED"
    LSTM_TIME=$(docker compose exec backend stat -c %y /app/models/lstm_autoencoder.h5 2>/dev/null | cut -d'.' -f1)
    echo "   └─ Timestamp: $LSTM_TIME"
    LSTM_SIZE=$(docker compose exec backend stat -c %s /app/models/lstm_autoencoder.h5 2>/dev/null)
    echo "   └─ Size: $((LSTM_SIZE / 1024)) KB"
else
    echo "⏳ LSTM Autoencoder: TRAINING IN PROGRESS..."
fi

echo ""

# Check metrics
if docker compose exec backend test -f /app/models/metrics.json 2>/dev/null; then
    echo "📊 Training Metrics Available:"
    docker compose exec backend cat /app/models/metrics.json 2>/dev/null | jq -r '
        to_entries | .[] | 
        "   \(.key):\n      - F1: \(.value.f1_score // "N/A")\n      - Precision: \(.value.precision // "N/A")\n      - Recall: \(.value.recall // "N/A")"
    ' || echo "   Error reading metrics"
else
    echo "📊 Training Metrics: Not available yet"
fi

echo ""
echo "================================"

# Check if training process is running
if docker compose exec backend pgrep -f "train_anomaly_models.py" >/dev/null 2>&1; then
    echo "🔄 Training process: RUNNING"
    echo "   Estimated completion: 30-60 minutes from start"
else
    echo "⚠️  Training process: NOT DETECTED"
    echo "   (May have completed or need restart)"
fi

echo ""
