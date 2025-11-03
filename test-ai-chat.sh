#!/bin/bash

echo "🧪 Testando integração com OpenAI..."
echo ""

# Testar endpoint demo do chat
echo "📤 Enviando mensagem de teste..."
echo ""

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/chat/chat/demo \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Olá! Você está funcionando? Me diga quais são suas capacidades.",
    "include_context": true
  }')

echo "📥 Resposta do AI Assistant:"
echo ""
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Verificar se houve erro
if echo "$RESPONSE" | grep -q "error\|Error\|500"; then
    echo "❌ Erro na resposta"
    exit 1
else
    echo "✅ AI Assistant respondeu com sucesso!"
    exit 0
fi
