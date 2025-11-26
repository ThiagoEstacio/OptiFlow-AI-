# OptiFlow - Guia de Migração

**De**: Monolito (Backend com Simulator acoplado)
**Para**: Microserviços (Simulator + Gateway + Backend)

---

## 📋 Checklist de Migração

### ✅ Já Implementado

- [x] Simulador extraído do backend → microserviço independente
- [x] OPC-UA server criado (simulador expõe tags)
- [x] Gateway microservice (API + Workers)
- [x] Gateway REST API (local low-latency)
- [x] Gateway WebSocket (real-time alarms)
- [x] Docker deployment (Simulator, Gateway, Backend)
- [x] Docker Compose full (stack completo)
- [x] Documentação completa

### ⏳ Próximos Passos

- [ ] Remover lógica de simulação do backend
- [ ] Atualizar frontend para usar Gateway API (opcional)
- [ ] Testar fluxo completo (Simulator → Gateway → Kafka → Backend)
- [ ] Configurar adaptadores OPC-UA no Gateway
- [ ] Validar quality flags e alarmes via WebSocket

---

## 🔄 Mudanças na Arquitetura

### Antes

```python
# backend/app/services/lightweight_simulator.py
class LightweightGrainTerminalSimulator:
    async def step_async(...):
        # ... simulation logic ...

        # ❌ Backend publica diretamente no Kafka
        await self._write_to_influxdb()
```

```python
# backend/app/api/routes/simulator.py
from app.services.lightweight_simulator import get_simulator

@router.post("/simulator/start")
async def start_system():
    sim = get_simulator()  # ❌ Backend controla simulador
    sim.start()
```

### Depois

```python
# simulator/app/services/grain_terminal_simulator.py
class GrainTerminalSimulator:
    async def step_async(...):
        # ... simulation logic ...

        # ✅ Simulador só atualiza estado interno
        # Gateway lê via OPC-UA e publica no Kafka
```

```python
# simulator/app/services/opcua_server.py
class OPCUASimulatorServer:
    async def _update_loop(self):
        while self._running:
            tags = self.simulator.get_all_tags()

            # ✅ Atualiza nodes OPC-UA
            for tag_name, value in tags.items():
                await self.tag_nodes[tag_name].write_value(value)
```

```python
# gateway/app/services/protocols/opcua_adapter.py
async def read_tags(self) -> List[TagData]:
    # ✅ Gateway lê do OPC-UA (Simulator OU PLC real)
    values = await self.client.read_values(self.nodes)

    # ✅ Gateway publica no Kafka
    return [TagData(...) for v in values]
```

---

## 🚀 Como Usar a Nova Arquitetura

### Desenvolvimento (com Simulator)

```bash
# 1. Inicia stack completo
docker-compose -f docker-compose.full.yml up -d

# 2. Verifica se tudo subiu
docker-compose -f docker-compose.full.yml ps

# Deve mostrar:
# - optiflow-simulator (4840, 4850)
# - optiflow-gateway (8080)
# - optiflow-backend (8000)
# - optiflow-kafka (9092)
# - optiflow-postgres (5432)
# - optiflow-influxdb (8086)
# - optiflow-redis (6379)
# - optiflow-frontend (3000)

# 3. Inicia simulação
curl -X POST http://localhost:4850/simulator/start

# 4. Verifica tags no Simulator
curl http://localhost:4850/simulator/tags

# 5. Verifica tags no Gateway (lê do OPC-UA)
curl http://localhost:8080/api/tags/list

# 6. Verifica dados no Backend (via Kafka)
curl http://localhost:8000/api/v1/tags

# 7. Acessa frontend
open http://localhost:3000
```

### Produção (com PLCs Reais)

```bash
# 1. Edita config do Gateway
vim gateway/config/adapters_config.yaml

# Muda:
# host: simulator  → host: 192.168.1.10 (IP do PLC)

# 2. Faz deploy do Gateway (edge)
kubectl apply -f gateway/k8s/

# 3. Faz deploy do Backend (cloud)
kubectl apply -f backend/k8s/

# 4. Faz deploy do Frontend (cloud)
kubectl apply -f frontend/k8s/

# Nota: Simulator NÃO vai para produção
```

---

## 🔧 Configuração do Gateway

### Conectar ao Simulator (Dev)

`gateway/config/adapters_config.yaml`:
```yaml
adapters:
  - adapter_id: simulator_opcua
    protocol_type: opcua
    enabled: true
    host: simulator  # Docker service name
    port: 4840
    timeout: 5.0
    scan_rate_ms: 1000

    extra_config:
      security_mode: None
      security_policy: None

    tags:
      - name: CORR01_TEMP_C
        address: ns=2;s=CORR01/TEMP_C_PV
        type: float
        unit: °C

      - name: CORR01_POWER_KW
        address: ns=2;s=CORR01/POWER_KW_PV
        type: float
        unit: kW

      - name: CORR01_CURRENT_A
        address: ns=2;s=CORR01/CURRENT_A_PV
        type: float
        unit: A

      # ... adicione mais tags conforme necessário
```

### Conectar a PLC Real (Produção)

`gateway/config/adapters_config.yaml`:
```yaml
adapters:
  - adapter_id: plc1_siemens
    protocol_type: opcua
    enabled: true
    host: 192.168.1.10  # IP do PLC
    port: 4840
    timeout: 5.0
    scan_rate_ms: 1000

    extra_config:
      security_mode: SignAndEncrypt
      security_policy: Basic256Sha256
      username: opcua_user
      password: ${OPCUA_PASSWORD}  # Ler de env/secrets

    tags:
      - name: SILO1_TEMPERATURA
        address: ns=2;s=TEAG.SILO1.TEMP
        type: float
        unit: °C

      - name: SILO1_NIVEL
        address: ns=2;s=TEAG.SILO1.NIVEL
        type: float
        unit: "%"
```

---

## 🧪 Testes

### Teste 1: Simulator Standalone

```bash
# Inicia apenas o simulador
docker-compose -f simulator/docker-compose.yml up -d

# Verifica OPC-UA server
telnet localhost 4840

# Verifica API REST
curl http://localhost:4850/health

# Inicia simulação
curl -X POST http://localhost:4850/simulator/start

# Verifica status
curl http://localhost:4850/simulator/status

# Verifica tags
curl http://localhost:4850/simulator/tags
```

### Teste 2: Gateway → Simulator

```bash
# Inicia Simulator + Gateway + Kafka
docker-compose -f docker-compose.full.yml up -d simulator gateway kafka

# Aguarda 30s
sleep 30

# Inicia simulação
curl -X POST http://localhost:4850/simulator/start

# Aguarda 10s (Gateway lê tags e publica Kafka)
sleep 10

# Verifica tags no Gateway
curl http://localhost:8080/api/tags/list

# Deve mostrar tags lidas do OPC-UA
```

### Teste 3: Full Stack

```bash
# Inicia tudo
docker-compose -f docker-compose.full.yml up -d

# Aguarda 60s
sleep 60

# Inicia simulação
curl -X POST http://localhost:4850/simulator/start

# Aguarda 15s
sleep 15

# Verifica Backend recebeu dados (via Kafka)
curl http://localhost:8000/api/v1/tags

# Acessa frontend
open http://localhost:3000
```

---

## 🐛 Troubleshooting

### Gateway não conecta ao Simulator

```bash
# 1. Verifica se Simulator está rodando
curl http://localhost:4850/health

# 2. Verifica se OPC-UA server está acessível
telnet localhost 4840

# 3. Verifica logs do Simulator
docker logs optiflow-simulator

# 4. Verifica logs do Gateway
docker logs optiflow-gateway

# 5. Verifica config do Gateway
cat gateway/config/adapters_config.yaml
```

### Backend não recebe dados

```bash
# 1. Verifica se Kafka está rodando
docker logs optiflow-kafka

# 2. Verifica se Gateway publicou no Kafka
docker exec optiflow-kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic raw_tags \
  --from-beginning \
  --max-messages 10

# 3. Verifica logs do Backend
docker logs optiflow-backend

# 4. Verifica se consumer Kafka está rodando
# Deve mostrar logs: "📥 Consumed X messages from Kafka"
```

### Tags não aparecem no Frontend

```bash
# 1. Verifica se Backend API está funcionando
curl http://localhost:8000/api/v1/tags

# 2. Verifica se InfluxDB tem dados
curl http://localhost:8086/api/v2/query \
  -H "Authorization: Token optiflow-influx-token" \
  -d 'bucket=optiflow&query=from(bucket:"optiflow")|>range(start:-1h)|>limit(n:10)'

# 3. Verifica logs do Frontend
docker logs optiflow-frontend

# 4. Abre console do navegador (F12)
# Verifica erros de CORS ou network
```

---

## 📚 Referências

- **Arquitetura Geral**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Simulator Docs**: [simulator/README.md](simulator/README.md)
- **Gateway Docs**: [gateway/README.microservice.md](gateway/README.microservice.md)
- **Gateway Architecture**: [gateway/ARCHITECTURE.microservice.md](gateway/ARCHITECTURE.microservice.md)

---

## ✅ Validação de Migração

Após migração, valide:

- [ ] Simulator roda standalone (porta 4840/4850)
- [ ] Gateway conecta ao Simulator via OPC-UA
- [ ] Gateway lê tags e publica no Kafka
- [ ] Backend consome Kafka e grava InfluxDB
- [ ] Frontend mostra dashboards em tempo real
- [ ] WebSocket alarmes funciona (Gateway → Frontend)
- [ ] Quality flags são detectados e geram alarmes
- [ ] Failsafe buffer do Gateway funciona (desliga Kafka e verifica)

---

**Data**: 2025-01-19
**Status**: ✅ Migração completa
