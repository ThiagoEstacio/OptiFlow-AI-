#!/bin/bash

# Script para iniciar o ambiente de desenvolvimento do OptiFlow
# Mantém os serviços rodando

echo "🚀 Iniciando OptiFlow Development Environment..."
echo ""

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Por favor, inicie o Docker primeiro."
    exit 1
fi

# Verificar se backend está rodando
echo "📊 Verificando backend..."
if ! docker ps | grep -q optiflow-backend; then
    echo "⚠️  Backend não está rodando. Iniciando..."
    sudo docker compose up -d backend
    sleep 5
else
    echo "✅ Backend rodando"
fi

# Verificar se frontend está rodando na porta 3002
echo "🎨 Verificando frontend..."
if ! lsof -ti:3002 > /dev/null 2>&1; then
    echo "⚠️  Frontend não está rodando. Iniciando na porta 3002..."
    cd frontend
    nohup npm run dev > ../frontend.log 2>&1 &
    echo $! > ../frontend.pid
    cd ..
    sleep 3
    echo "✅ Frontend iniciado em http://localhost:3002"
else
    echo "✅ Frontend rodando em http://localhost:3002"
fi

echo ""
echo "🎉 Ambiente de desenvolvimento pronto!"
echo ""
echo "📌 URLs:"
echo "   Frontend: http://localhost:3002"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "💡 Para parar o frontend: kill \$(cat frontend.pid)"
echo ""
