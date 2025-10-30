#!/bin/bash

# Script para iniciar e manter o Vite rodando
cd "$(dirname "$0")/frontend"

echo "🎨 Iniciando Vite Dev Server..."
echo "📍 URL: http://localhost:3002"
echo ""
echo "⚠️  Para parar: pressione Ctrl+C"
echo ""

# Loop infinito para reiniciar se cair
while true; do
    npm run dev
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 130 ]; then
        echo ""
        echo "👋 Vite parado pelo usuário (Ctrl+C)"
        exit 0
    fi
    
    echo ""
    echo "⚠️  Vite parou inesperadamente (código $EXIT_CODE)"
    echo "🔄 Reiniciando em 3 segundos..."
    sleep 3
done
