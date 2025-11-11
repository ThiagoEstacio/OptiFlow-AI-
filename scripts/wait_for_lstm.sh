#!/bin/bash
# Script para aguardar e notificar quando o treinamento LSTM completar

echo "⏳ Aguardando treinamento LSTM completar..."
echo ""
echo "Monitorando arquivo: /app/models/lstm_autoencoder.h5"
echo "Verificando a cada 2 minutos..."
echo ""

START_TIME=$(date +%s)
CHECK_COUNT=0

while true; do
    CHECK_COUNT=$((CHECK_COUNT + 1))
    ELAPSED=$(($(date +%s) - START_TIME))
    ELAPSED_MIN=$((ELAPSED / 60))
    
    echo "[$CHECK_COUNT] Verificação após ${ELAPSED_MIN} minutos..."
    
    # Verificar se modelo LSTM existe
    if docker compose exec backend test -f /app/models/lstm_autoencoder.h5 2>/dev/null; then
        echo ""
        echo "✅ =================================="
        echo "✅  LSTM TRAINING COMPLETE!"
        echo "✅ =================================="
        echo ""
        echo "📊 Modelos disponíveis:"
        docker compose exec backend ls -lh /app/models/*.{h5,joblib,json} 2>/dev/null | grep -E "\.h5|\.joblib|\.json"
        echo ""
        echo "📈 Verificando métricas..."
        docker compose exec backend cat /app/models/metrics.json 2>/dev/null | jq . || echo "  Métricas não disponíveis"
        echo ""
        echo "🎯 Próximos passos:"
        echo "  1. Testar modelo LSTM via API"
        echo "  2. Comparar performance: Isolation Forest vs LSTM"
        echo "  3. Criar frontend de visualização de anomalias"
        echo ""
        
        # Notificação sonora (se disponível)
        which paplay >/dev/null 2>&1 && paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null
        
        break
    fi
    
    # Verificar se processo ainda está rodando
    if docker compose exec backend pgrep -f "train_anomaly_models.py" >/dev/null 2>&1; then
        echo "  ✓ Processo de treinamento ainda rodando..."
    else
        echo "  ⚠️ Processo não encontrado. Verificando modelos..."
        docker compose exec backend ls -lh /app/models/ 2>/dev/null | tail -10
    fi
    
    echo ""
    
    # Aguardar 2 minutos
    sleep 120
done

echo "Script finalizado após ${ELAPSED_MIN} minutos de espera"
