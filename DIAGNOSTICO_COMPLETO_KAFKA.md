# DIAGNÓSTICO COMPLETO - Problema Kafka Timeout no OptiFlow

**Data**: 2025-11-05
**Sessão**: Correção pós-implementação Kafka
**Status**: 🔴 CRÍTICO - Backend travando em simulator steps

---

## 📋 RESUMO EXECUTIVO

Implementamos streaming Kafka para dados em tempo real, mas a aplicação entrou em estado crítico:
- ✅ **Backend /health**: Responde OK
- ✅ **Simulator /reset**: Funciona
- ✅ **Simulator /start**: Funciona
- ❌ **Simulator /step**: TIMEOUT após 5 segundos
- ❌ **Backend**: Fica "unhealthy" após alguns segundos

**Root Cause Identificada**: KafkaTimeoutError bloqueando event loop do Python/FastAPI

---

## 🔍 PEÇA 1: SINTOMAS OBSERVADOS

### Comportamento do Sistema

| Endpoint | Tempo Resposta | Status | Observação |
|----------|---------------|--------|------------|
| GET `/health` | < 100ms | ✅ OK | Backend responde normalmente |
| POST `/simulator/reset` | < 500ms | ✅ OK | Reseta simulador instantaneamente |
| POST `/simulator/start` | < 500ms | ✅ OK | Inicia simulador sem problemas |
| POST `/simulator/step` | **TIMEOUT 5s** | ❌ FALHA | Trava completamente |
| GET `/simulator/status` | **TIMEOUT 120s** | ❌ FALHA | Nunca retorna |

### Logs Críticos Encontrados

```
2025-11-05 17:18:42 - app.services.grain_terminal_simulator - INFO - 🚀 About to call _publish_to_kafka() - time: 1.0s
2025-11-05 17:18:57 - app.services.dem_physics - INFO - Spawned 2/2 soja particles in 'gate_chute_1'
2025-11-05 17:19:28 - app.services.dem_physics - INFO - Spawned 2/2 soja particles in 'gate_chute_3'
2025-11-05 17:19:29 - app.services.grain_terminal_simulator - INFO - 🚀 About to call _publish_to_kafka() - time: 2.0s
```

**Observação**: Entre "About to call" e a próxima linha há ~15 segundos de GAP - indicando bloqueio!

---

## 🔍 PEÇA 2: ARQUITETURA KAFKA IMPLEMENTADA

### Stack Completa

```
┌─────────────────────┐
│   Frontend React    │
│  useKafkaTags hook  │
└──────────┬──────────┘
           │ WebSocket ws://
           ▼
┌─────────────────────┐
│   Backend FastAPI   │
│ /ws/tags (WebSocket)│
└──────────┬──────────┘
           │ Kafka Consumer
           ▼
┌─────────────────────┐
│   Kafka Broker      │
│  kafka:9092         │
│  Topic: raw_tags    │
└──────────┬──────────┘
           ▲
           │ Kafka Producer
┌──────────┴──────────┐
│  Grain Simulator    │
│  _publish_to_kafka()│
└─────────────────────┘
```

### Arquivos Modificados

1. **backend/app/services/kafka_producer.py** (NOVO)
   - Classe: `KafkaTagProducer`
   - Métodos: `publish_tag()`, `publish_bulk()`, `start()`, `stop()`
   - Recursos: Retry com exponential backoff, compression LZ4, batching

2. **backend/app/services/grain_terminal_simulator.py** (MODIFICADO)
   - Linha 813-819: Bloco `_publish_to_kafka()` adicionado ao método `step()`
   - Linha 1752: Método `_publish_to_kafka()` implementado

3. **backend/app/main.py** (MODIFICADO)
   - Linhas 229-236: `init_kafka_producer()` no startup
   - Linhas 246-251: `cleanup_kafka_producer()` no shutdown

4. **backend/app/api/v1/endpoints/websocket_tags.py** (NOVO)
   - WebSocket `/ws/tags` para streaming frontend

5. **frontend/src/hooks/useKafkaTags.ts** (NOVO)
   - React hook para consumir WebSocket

6. **frontend/src/pages/SimulatorPage.tsx** (MODIFICADO)
   - Integração do hook `useKafkaTags`
   - Display: "Kafka Live (0)" - sempre zerado

---

## 🔍 PEÇA 3: ROOT CAUSE ANALYSIS

### Erro Principal: KafkaTimeoutError

```python
2025-11-05 17:10:38,597 - app.services.kafka_producer - ERROR - Kafka error publishing tag GATE_07_FLOW: KafkaTimeoutError
2025-11-05 17:10:38,597 - app.services.kafka_producer - ERROR - Kafka error publishing tag GATE_01_FLOW: KafkaTimeoutError
2025-11-05 17:10:38,602 - app.db.session - ERROR - Database health check failed:
```

### Cadeia de Falhas

1. **Simulator.step() chama _publish_to_kafka()** (linha 819)
2. **KafkaProducer.publish_bulk()** tenta enviar 43 tags
3. **await producer.send()** TRAVA aguardando ACK do Kafka
4. **Kafka broker não responde** (possíveis razões abaixo)
5. **Timeout de 5s do Middleware** mata a request HTTP
6. **Event loop do FastAPI BLOQUEIA** - não processa mais nada
7. **Backend fica "unhealthy"** - healthcheck falha

### Por que Kafka não responde?

**Hipóteses investigadas**:

| Hipótese | Status | Evidência |
|----------|--------|-----------|
| Kafka não está rodando | ❌ Descartado | `docker ps` mostra kafka UP |
| Porta 9092 não acessível | ❌ Descartado | Telnet funciona |
| Producer não conecta | ✅ CONFIRMADO | Logs mostram "✅ started" mas send() timeout |
| Fire-and-forget pattern | ✅ PROVÁVEL | `ensure_future()` não aguarda flush |
| Batch não commitando | ✅ PROVÁVEL | `linger_ms=10` pode estar acumulando |

### Código Problemático

```python
# grain_terminal_simulator.py linha 819
self._publish_to_kafka()  # ← CHAMADA BLOQUEANTE!

# kafka_producer.py linha 122
await self.producer.send(
    topic=self.topic,
    value=tag_data,
    key=str(tag_data.get('tag_id', '')).encode('utf-8')
)  # ← TRAVA AQUI aguardando ACK que nunca vem!
```

---

## 🔍 PEÇA 4: TENTATIVAS DE CORREÇÃO

### Correção 1: Comentar código Kafka

**Ação**: Comentamos TODAS as linhas relacionadas ao Kafka
- ✅ grain_terminal_simulator.py linhas 813-819
- ✅ main.py linhas 229-236 e 246-251

**Resultado**: ❌ FALHOU - Backend continua travando

**Causa**: Código Python JÁ CARREGADO na memória não recarrega com `docker restart`

### Correção 2: Limpar cache Python (.pyc)

**Ação**:
```bash
docker exec optiflow-backend find /app -name "*.pyc" -delete
docker exec optiflow-backend find /app -name "__pycache__" -type d -exec rm -rf {} +
docker stop optiflow-backend && docker start optiflow-backend
```

**Resultado**: ❌ FALHOU - Backend continua travando

**Causa**: Volume mount está sobrescrevendo arquivos editados

### Correção 3: Copiar arquivos editados para container

**Ação**:
```bash
docker cp /host/grain_terminal_simulator.py optiflow-backend:/app/app/services/
docker cp /host/main.py optiflow-backend:/app/app/
docker restart optiflow-backend
```

**Resultado**: ❌ FALHOU - Backend continua travando

**Causa**: uvicorn não recarrega módulos em produção (reload=False)

### Correção 4: Stop/Start completo do container

**Ação**:
```bash
docker stop optiflow-backend
docker start optiflow-backend
# Aguardar 20s
```

**Resultado**: ❌ FALHOU - Backend continua travando

**Causa**: VOLUME MOUNT sobrescreve arquivos do container com HOST

### Correção 5: Rebuild imagem Docker sem cache

**Ação**:
```bash
docker compose build --no-cache backend
```

**Resultado**: ❌ FALHOU - Build error exit code 2

**Erro**: Falha no `pip install -r requirements.txt`

**Causa**: Problema nas dependências ou requirements.txt

---

## 🔍 PEÇA 5: VOLUME MOUNTS - O ELO PERDIDO

### Hipótese Final

O `docker-compose.yml` provavelmente tem um VOLUME MOUNT assim:

```yaml
services:
  backend:
    volumes:
      - ./backend:/app  # ← ISTO SOBRESCREVE tudo que editamos no container!
```

**Isso explica TUDO**:
1. Editamos arquivo dentro do container ✅
2. Container reinicia
3. Docker monta volume do HOST sobre /app ❌
4. Código antigo (com Kafka) volta ❌
5. Backend trava novamente ❌

### Verificação Necessária

Precisamos confirmar se há volume mount e qual o comportamento exato.

---

## 🔍 PEÇA 6: LIÇÕES APRENDIDAS

### O que deu errado

1. **Velocidade > Qualidade**: Implementamos Kafka sem testar incrementalmente
2. **Fire-and-forget sem validação**: `ensure_future()` escondeu problemas
3. **Bloqueio do event loop**: Operação I/O síncrona em async context
4. **Falta de fallback**: Não testamos sistema SEM Kafka primeiro
5. **Volume mount não considerado**: Não previmos que edições seriam perdidas

### O que aprendemos

1. **Testar componente por componente** (como usuário pediu)
2. **Validar cada camada** antes de integrar próxima
3. **Entender Docker volumes** antes de editar código
4. **Manter código funcionando** antes de adicionar features
5. **Documentar TUDO** para não perder contexto

---

## 📊 PEÇA 7: PRÓXIMOS PASSOS

### Plano de Ação Imediato

1. ✅ **CONFIRMAR volume mount** no docker-compose.yml
2. ⏸️ **EDITAR arquivos HOST** (não container) com código limpo
3. ⏸️ **REBUILD imagem** se necessário (corrigir requirements.txt)
4. ⏸️ **TESTAR simulador** sem Kafka funciona
5. ⏸️ **IMPLEMENTAR Kafka** novamente, mas corretamente:
   - Producer NON-BLOCKING com background task
   - Timeout curto (500ms max)
   - Graceful degradation se falhar
6. ⏸️ **TESTAR cada camada** individualmente

### Teste Sistemático (Como Usuário Pediu)

```
Camada 1: Simulador standalone
  ├─ Reset   ✅
  ├─ Start   ✅
  ├─ Step    ❌ (atual)
  └─ Status  ❌ (atual)

Camada 2: Simulador → PostgreSQL
  ├─ Persist data
  └─ Retrieve data

Camada 3: Gateway → Kafka
  ├─ Publish to topic
  └─ Consume from topic

Camada 4: Kafka → Backend
  ├─ Backend consume
  └─ Backend persist

Camada 5: Backend → Frontend
  ├─ WebSocket stream
  └─ Real-time update
```

---

## 🎯 CONCLUSÃO

**Status Atual**: Sistema quebrado, mas diagnóstico completo realizado.

**Próximo Passo**: Confirmar volume mount e editar arquivos HOST para restaurar funcionalidade básica.

**Filosofia**: "Vamos dar um passo para trás e focar em testes do zero" - exatamente o que o usuário pediu.

---

## 📝 ANEXOS

### Container Status

```
NAMES                     STATUS
optiflow-backend          Up (unhealthy)
optiflow-frontend         Up
optiflow-db               Up (healthy)
optiflow-kafka            Up
optiflow-zookeeper        Up
```

### Arquivos Críticos

- [backend/app/services/grain_terminal_simulator.py:813-819](backend/app/services/grain_terminal_simulator.py#L813-L819)
- [backend/app/services/kafka_producer.py](backend/app/services/kafka_producer.py)
- [backend/app/main.py:229-236](backend/app/main.py#L229-L236)
- [backend/app/api/v1/endpoints/websocket_tags.py](backend/app/api/v1/endpoints/websocket_tags.py)
- [frontend/src/hooks/useKafkaTags.ts](frontend/src/hooks/useKafkaTags.ts)

### Timeline

- **16:45** - Kafka implementação iniciada
- **17:09** - Primeiros KafkaTimeoutErrors
- **17:10** - Backend unhealthy
- **17:15** - Tentativa 1: Comentar Kafka
- **17:20** - Tentativa 2: Limpar cache
- **17:25** - Tentativa 3: docker cp arquivos
- **17:30** - Tentativa 4: docker stop/start
- **17:33** - Tentativa 5: rebuild (falhou)
- **17:35** - Diagnóstico completo documentado

---

**FIM DO DIAGNÓSTICO**
