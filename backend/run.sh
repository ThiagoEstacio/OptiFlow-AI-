#!/bin/bash
# OptiFlow AI Backend - Script de Inicialização
# Uso: ./run.sh

set -e

echo "============================================================"
echo "🚀 OptiFlow AI Backend - Iniciando..."
echo "============================================================"

# Verificar se o ambiente conda está ativo
if [[ "$CONDA_DEFAULT_ENV" != "optiflow" ]]; then
    echo "⚙️  Ativando ambiente conda 'optiflow'..."
    source /home/thiestacio/anaconda3/bin/activate optiflow
fi

# Verificar Python version
echo "🐍 Python: $(python --version)"
echo "📦 Ambiente: $CONDA_DEFAULT_ENV"

# Navegar para o diretório backend
cd /home/thiestacio/OptiFlow-AI-/backend

# Verificar se as dependências estão instaladas
echo "📋 Verificando dependências..."
python -c "from app.main import app; print('✅ Dependências OK')" 2>&1 | grep "✅" || {
    echo "❌ Erro ao importar aplicação"
    exit 1
}

echo ""
echo "============================================================"
echo "✅ Iniciando servidor Uvicorn..."
echo "============================================================"
echo "📍 URL: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo "🔄 ReDoc: http://localhost:8000/redoc"
echo "============================================================"
echo ""

# Iniciar servidor
exec python app/main.py
