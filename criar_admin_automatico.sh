#!/bin/bash
# Script para criar usuário admin automaticamente
# Executa o script Python no container do backend

echo "=========================================="
echo "CRIANDO USUÁRIO ADMINISTRADOR"
echo "=========================================="
echo ""

# Verificar se o backend está rodando
if ! docker compose ps backend | grep -q "Up"; then
    echo "❌ Container backend não está rodando!"
    echo ""
    echo "Iniciando backend..."
    docker compose up -d backend
    echo ""
    echo "Aguardando 15 segundos para o backend inicializar..."
    sleep 15
fi

echo "Executando script de criação de usuário..."
echo ""

# Executar script Python no container do backend
docker compose exec -T backend python3 /app/create_admin.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ SUCESSO!"
    echo "=========================================="
    echo ""
    echo "Agora você pode fazer login em:"
    echo "  http://localhost:3000"
    echo ""
    echo "Com as credenciais:"
    echo "  Email: admin@smartport.com"
    echo "  Senha: Admin@123456"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ ERRO"
    echo "=========================================="
    echo ""
    echo "Não foi possível criar o usuário."
    echo ""
    echo "Tente o método manual:"
    echo "  ./criar_usuario_admin.sh"
    echo ""
fi

exit $EXIT_CODE
