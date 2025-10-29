#!/bin/bash
# Script de Diagnóstico - Por que porta 3000 mostra Grafana?

echo "======================================================================"
echo "DIAGNÓSTICO DE PORTAS - SmartPort vs Grafana"
echo "======================================================================"
echo ""

echo "1. CONTAINERS EM EXECUÇÃO:"
echo "----------------------------------------------------------------------"
docker compose ps
echo ""

echo "2. MAPEAMENTO DE PORTAS NO DOCKER-COMPOSE.YML:"
echo "----------------------------------------------------------------------"
echo "=== FRONTEND ==="
grep -A 15 "# Frontend Web Application" docker-compose.yml | grep -E "(ports:|command:)" | head -5
echo ""
echo "=== GRAFANA ==="
grep -A 10 "# Grafana" docker-compose.yml | grep -E "ports:" | head -2
echo ""

echo "3. CONFIGURAÇÃO DE PORTA NO VITE:"
echo "----------------------------------------------------------------------"
grep -A 2 "server:" frontend/vite.config.ts | grep "port:"
echo ""

echo "4. PROCESSOS USANDO PORTA 3000:"
echo "----------------------------------------------------------------------"
sudo lsof -i :3000 || echo "Nenhum processo encontrado"
echo ""

echo "5. PROCESSOS USANDO PORTA 5173:"
echo "----------------------------------------------------------------------"
sudo lsof -i :5173 || echo "Nenhum processo encontrado"
echo ""

echo "6. PROCESSOS USANDO PORTA 3001:"
echo "----------------------------------------------------------------------"
sudo lsof -i :3001 || echo "Nenhum processo encontrado"
echo ""

echo "7. TESTE DE CONTEÚDO NAS PORTAS:"
echo "----------------------------------------------------------------------"
echo "=== Porta 3000 ==="
curl -s http://localhost:3000 | head -5 | grep -i -E "(grafana|react|smartport|html)" || echo "Porta 3000 não responde"
echo ""
echo "=== Porta 5173 ==="
curl -s http://localhost:5173 | head -5 | grep -i -E "(grafana|react|smartport|html)" || echo "Porta 5173 não responde"
echo ""
echo "=== Porta 3001 ==="
curl -s http://localhost:3001 | head -5 | grep -i -E "(grafana|react|smartport|html)" || echo "Porta 3001 não responde"
echo ""

echo "8. LOGS DO FRONTEND (últimas 10 linhas):"
echo "----------------------------------------------------------------------"
docker compose logs frontend --tail=10
echo ""

echo "9. LOGS DO GRAFANA (últimas 5 linhas):"
echo "----------------------------------------------------------------------"
docker compose logs grafana --tail=5
echo ""

echo "======================================================================"
echo "DIAGNÓSTICO COMPLETO - Cole toda esta saída para análise"
echo "======================================================================"
