#!/bin/bash
# =================================================================
# Script para iniciar servidor OPC-UA SEM CACHE Python
# =================================================================

echo "🧹 Limpando processos OPC-UA antigos..."
pkill -9 -f "run_opcua_server.py" 2>/dev/null
sleep 2

echo "🗑️  Tentando deletar cache Python..."
sudo rm -rf /home/thiestacio/OptiFlow-AI-/backend/app/services/__pycache__/ 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ Cache deletado"
else
    echo "⚠️  Não foi possível deletar cache (requer sudo)"
fi

echo "🚀 Iniciando servidor OPC-UA (SEM GERAR CACHE)..."
cd /home/thiestacio/OptiFlow-AI-

# PYTHONDONTWRITEBYTECODE=1 evita criar .pyc
# -B também evita .pyc
# -u força stdout unbuffered
export PYTHONDONTWRITEBYTECODE=1
/home/thiestacio/anaconda3/envs/optiflow/bin/python -B -u \
    backend/scripts/run_opcua_server.py \
    > opcua_nocache.log 2>&1 &

echo "PID: $!"
echo "Log: opcua_nocache.log"
echo ""
echo "⏳ Aguardando 8 segundos..."
sleep 8
echo ""
echo "📋 Verificando log..."
tail -20 opcua_nocache.log
echo ""
echo "🔍 Erros BadTypeMismatch:"
grep -c "BadTypeMismatch" opcua_nocache.log 2>/dev/null || echo "0"
echo ""
echo "✅ Servidor iniciado!"
