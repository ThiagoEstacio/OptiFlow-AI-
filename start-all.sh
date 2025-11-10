#!/bin/bash
# OptiFlow AI - Iniciar todos os containers via Docker Compose
# Uso: ./start-all.sh

set -e

echo "============================================================"
echo "🚀 OptiFlow AI Platform - Iniciando Aplicação Completa"
echo "============================================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar se Docker está rodando
echo -e "${BLUE}🔍 Verificando Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker não está rodando!${NC}"
    echo -e "${YELLOW}   Execute: sudo systemctl start docker${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker está rodando${NC}"

# Verificar se docker-compose está instalado
echo -e "${BLUE}🔍 Verificando Docker Compose...${NC}"
if ! command -v docker-compose > /dev/null 2>&1 && ! docker compose version > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker Compose não está instalado!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose disponível${NC}"

echo ""
echo "============================================================"
echo -e "${BLUE}🐳 Iniciando containers Docker...${NC}"
echo "============================================================"
echo ""

# Ir para diretório raiz do projeto
cd "$(dirname "$0")"

# Iniciar todos os containers
echo -e "${BLUE}📦 Subindo todos os serviços...${NC}"
docker compose up -d

echo ""
echo -e "${BLUE}⏳ Aguardando containers ficarem saudáveis...${NC}"
sleep 5

# Verificar status dos containers
echo ""
echo -e "${BLUE}📊 Status dos Containers:${NC}"
echo ""
docker compose ps

echo ""
echo "============================================================"
echo -e "${GREEN}🎉 OptiFlow AI Platform está rodando!${NC}"
echo "============================================================"
echo ""
echo -e "${BLUE}📍 URLs de Acesso:${NC}"
echo ""
echo -e "  ${GREEN}Frontend:${NC}"
echo "    🌐 http://localhost:3000"
echo ""
echo -e "  ${GREEN}Backend:${NC}"
echo "    📡 http://localhost:8000"
echo "    📚 http://localhost:8000/docs (Swagger)"
echo "    🔄 http://localhost:8000/redoc"
echo "    ❤️  http://localhost:8000/health"
echo ""
echo -e "  ${GREEN}Serviços de Infraestrutura:${NC}"
echo "    🗄️  PostgreSQL:    localhost:5432"
echo "    ⚡ Redis:         localhost:6379"
echo "    📊 InfluxDB:      localhost:8086"
echo "    🐰 RabbitMQ:      localhost:15672 (user: guest, pass: guest)"
echo "    📈 Grafana:       localhost:3001 (admin/admin)"
echo "    🧪 MLflow:        localhost:5000"
echo "    🏭 OPC UA Server: localhost:4840"
echo "    🔥 Prometheus:    localhost:9090"
echo "    🤖 Ollama:        localhost:11434"
echo ""
echo -e "${BLUE}📊 Logs em tempo real:${NC}"
echo "  Todos:    docker compose logs -f"
echo "  Backend:  docker compose logs -f backend"
echo "  Frontend: docker compose logs -f frontend"
echo ""
echo -e "${BLUE}🛑 Para parar:${NC}"
echo "  ./stop-all.sh"
echo "  ou"
echo "  docker compose down"
echo ""
echo "============================================================"
echo -e "${GREEN}✨ Pronto para usar!${NC}"
echo "============================================================"
