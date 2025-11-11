#!/bin/bash
# Script para monitorar progresso do treinamento ML

echo "🔍 Checking ML Training Progress..."
echo ""

# Check if models exist
echo "📁 Model Files:"
docker compose exec backend ls -lh /app/models/ 2>/dev/null | grep -E "\.joblib|\.h5|\.json"

echo ""
echo "📊 Latest Model Timestamps:"
docker compose exec backend stat /app/models/isolation_forest.joblib 2>/dev/null | grep Modify || echo "  Isolation Forest: Not found"
docker compose exec backend stat /app/models/lstm_autoencoder.h5 2>/dev/null | grep Modify || echo "  LSTM: Not found yet (still training)"
docker compose exec backend stat /app/models/metrics.json 2>/dev/null | grep Modify || echo "  Metrics: Not found yet"

echo ""
echo "💾 Model Sizes:"
docker compose exec backend du -sh /app/models/*.joblib /app/models/*.h5 2>/dev/null || echo "  Checking..."

echo ""
echo "🔄 To check if training is still running, look for python processes in backend container"
echo "   Training LSTM takes 30-60 minutes with 50 epochs on CPU"
