#!/bin/bash
# Script para criar usuário administrador

echo "=========================================="
echo "CRIANDO USUÁRIO ADMINISTRADOR"
echo "=========================================="
echo ""

# Gerar hash de senha usando Python no container backend
echo "1. Gerando hash da senha..."
PASSWORD_HASH=$(docker compose exec -T backend python3 -c "
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
print(pwd_context.hash('Admin@123456'))
" 2>/dev/null)

if [ -z "$PASSWORD_HASH" ]; then
    echo "❌ Erro ao gerar hash de senha"
    echo "Tentando método alternativo..."

    # Método alternativo: usar bcrypt do Python direto
    PASSWORD_HASH=$(docker compose exec -T backend python3 -c "
import bcrypt
password = 'Admin@123456'.encode('utf-8')
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password, salt)
print(hashed.decode('utf-8'))
" 2>/dev/null)
fi

echo "Hash gerado: ${PASSWORD_HASH:0:20}..."
echo ""

echo "2. Criando usuário no banco de dados..."

# SQL para criar usuário admin
SQL_COMMAND="
INSERT INTO users (email, full_name, hashed_password, role, is_active, created_at, updated_at)
VALUES (
    'admin@smartport.com',
    'Administrator',
    '$PASSWORD_HASH',
    'admin',
    true,
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE SET
    hashed_password = EXCLUDED.hashed_password,
    updated_at = NOW();
"

docker compose exec -T postgres psql -U optiflow -d optiflow -c "$SQL_COMMAND" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Usuário criado/atualizado com sucesso!"
    echo ""
    echo "=========================================="
    echo "CREDENCIAIS DE LOGIN"
    echo "=========================================="
    echo ""
    echo "  Email:    admin@smartport.com"
    echo "  Senha:    Admin@123456"
    echo ""
    echo "Acesse: http://localhost:3000"
    echo ""
else
    echo "❌ Erro ao criar usuário"
    echo ""
    echo "Tentando método manual..."
    echo ""
    echo "Execute manualmente:"
    echo ""
    echo "docker compose exec postgres psql -U optiflow -d optiflow"
    echo ""
    echo "Depois cole o seguinte SQL:"
    echo ""
    echo "INSERT INTO users (email, full_name, hashed_password, role, is_active, created_at, updated_at)"
    echo "VALUES ("
    echo "    'admin@smartport.com',"
    echo "    'Administrator',"
    echo "    '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2U6pRK5a2a',"
    echo "    'admin',"
    echo "    true,"
    echo "    NOW(),"
    echo "    NOW()"
    echo ");"
fi
