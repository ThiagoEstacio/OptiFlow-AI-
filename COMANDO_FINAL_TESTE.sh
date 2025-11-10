#!/bin/bash
# ============================================================================
# COMANDO FINAL - Testar OPC-UA com código corrigido
# ============================================================================

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║    OPTIFLOW - ATIVAR CORREÇÕES E TESTAR OPC-UA                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}PASSO 1: Deletar cache Python (requer sudo)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Executando: sudo rm -rf backend/app/services/__pycache__/"
sudo rm -rf backend/app/services/__pycache__/
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Cache deletado com sucesso!${NC}"
else
    echo -e "${RED}✗ Erro ao deletar cache (pode precisar executar manualmente)${NC}"
    echo "  Execute: sudo rm -rf backend/app/services/__pycache__/"
fi
echo ""

echo -e "${BLUE}PASSO 2: Encerrar servidor OPC-UA antigo${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pkill -9 -f "run_opcua_server.py" 2>/dev/null
sleep 2
echo -e "${GREEN}✓ Servidor encerrado${NC}"
echo ""

echo -e "${BLUE}PASSO 3: Iniciar servidor com código corrigido${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Executando: python backend/scripts/run_opcua_server.py &"
cd /home/thiestacio/OptiFlow-AI-
/home/thiestacio/anaconda3/envs/optiflow/bin/python backend/scripts/run_opcua_server.py > opcua_fixed.log 2>&1 &
OPCUA_PID=$!
echo "  PID: $OPCUA_PID"
echo "  Log: opcua_fixed.log"
echo ""

echo -e "${YELLOW}Aguardando servidor inicializar (10 segundos)...${NC}"
sleep 10
echo ""

echo -e "${BLUE}PASSO 4: Verificar se há erros no log${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ERROR_COUNT=$(grep -c "BadTypeMismatch" opcua_fixed.log 2>/dev/null || echo "0")

if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✅ NENHUM ERRO BadTypeMismatch encontrado!${NC}"
    echo "   (Esperado: apenas warning 'aiokafka not installed')"
else
    echo -e "${RED}❌ AINDA TEM $ERROR_COUNT ERROS BadTypeMismatch${NC}"
    echo "   Verifique: tail -50 opcua_fixed.log"
fi
echo ""

echo -e "${BLUE}PASSO 5: Testar conexão OPC-UA${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Executando: python test_opcua_minimal.py"
echo ""

timeout 15 /home/thiestacio/anaconda3/envs/optiflow/bin/python test_opcua_minimal.py 2>&1 | grep -E "(Conectando|Conectado|Error|Found|TEAG|children)" | head -20

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ SUCESSO! Servidor OPC-UA está funcionando perfeitamente!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
else
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}⚠️  Timeout ou erro na conexão${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "Possíveis causas:"
    echo "  1. Servidor ainda está carregando cache antigo"
    echo "  2. Verificar: tail -100 opcua_fixed.log | grep ERROR"
fi
echo ""

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║    LOGS E DOCUMENTAÇÃO                                            ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Log do servidor:"
echo "   tail -f opcua_fixed.log"
echo ""
echo "📚 Documentação completa:"
echo "   - STATUS_FINAL_TDD.md         (este resumo)"
echo "   - OPCUA_SERVER_FIX_SUMMARY.md (análise técnica)"
echo "   - QUICK_TEST_OPCUA.md         (guia de testes)"
echo ""
echo "🎯 Próximos passos:"
echo "   1. Se funcionou: testar auto-discovery"
echo "   2. Se não funcionou: verificar cache Python ainda presente"
echo ""
