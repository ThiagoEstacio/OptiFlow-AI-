# Protocol Adapters - Event-Driven Architecture

## Visão Geral

Sistema unificado de adapters de protocolos industriais para OptiFlow AI Platform.

Todos os adapters seguem a **arquitetura event-driven** onde:
1. Adapters leem dados de dispositivos/servidores industriais
2. Dados são publicados no Kafka (tópico `raw_tags`)
3. InfluxDB Consumer consome do Kafka e armazena no InfluxDB
4. Frontend consome dados em tempo real via InfluxDB

## Arquitetura

```
┌──────────────┐     ┌─────────┐     ┌────────────┐     ┌──────────┐
│  OPC UA PLC  │────▶│         │     │            │     │          │
└──────────────┘     │         │     │            │     │          │
                     │ Protocol│────▶│   Kafka    │────▶│ InfluxDB │
┌──────────────┐     │ Adapters│     │ raw_tags   │     │ Consumer │
│ Modbus PLC   │────▶│         │     │            │     │          │
└──────────────┘     │         │     │            │     │          │
                     │         │     │            │     │          │
┌──────────────┐     │         │     └────────────┘     └──────────┘
│ MQTT Broker  │────▶│         │                              │
└──────────────┘     └─────────┘                              │
                                                               ▼
                                                        ┌────────────┐
                                                        │  InfluxDB  │
                                                        │  Database  │
                                                        └────────────┘
```

## Protocolos Suportados

### 1. OPC UA (Unified Architecture)
- ✅ **Implementado**
- Baseado em `asyncua`
- Subscription-based (push model)
- Autenticação username/password
- Ideal para: SCADA, DCS, sistemas industriais modernos

### 2. Modbus TCP
- ✅ **Implementado**
- Baseado em `pymodbus`
- Polling-based
- Suporta FC01-04 (coils, discrete inputs, holding registers, input registers)
- Conversão automática de tipos (int16, uint16, int32, uint32, float32, float64)
- Ideal para: PLCs, controladores industriais

### 3. MQTT
- ✅ **Implementado**
- Baseado em `asyncio-mqtt`
- Subscription-based (push model)
- Suporte a wildcards (# e +)
- Parse automático de JSON
- QoS levels 0, 1, 2
- TLS/SSL support
- Ideal para: IoT, sensores, sistemas distribuídos

### 4. Ethernet/IP
- ⏳ **Planejado**
- Ideal para: Allen-Bradley PLCs, Rockwell Automation

### 5. Siemens S7
- ⏳ **Planejado**
- Ideal para: Siemens PLCs (S7-300, S7-400, S7-1200, S7-1500)

## Componentes

### BaseProtocolAdapter
Classe abstrata que define o comportamento padrão de todos os adapters:

- **Métodos abstratos** (devem ser implementados):
  - `connect()` - Conectar ao dispositivo
  - `disconnect()` - Desconectar
  - `read_tags()` - Ler valores das tags
  - `health_check()` - Verificar saúde da conexão

- **Funcionalidades automáticas**:
  - Scan loop (leitura periódica)
  - Publicação automática no Kafka
  - Retry logic com exponential backoff
  - Reconexão automática
  - Estatísticas (read_count, error_count)

### Protocol Manager
Gerenciador central que:
- Carrega configurações de arquivo JSON
- Inicia/para todos os adapters
- Monitora saúde dos adapters (health check a cada 30s)
- Restart automático em caso de falha
- API unificada para estatísticas

## Configuração

### Arquivo de Configuração

Veja [adapters_config.example.json](./adapters_config.example.json) para exemplo completo.

```json
{
  "adapters": [
    {
      "adapter_id": "plc1_modbus",
      "protocol_type": "modbus",
      "enabled": true,
      "host": "192.168.1.10",
      "port": 502,
      "scan_rate_ms": 1000,
      "tags": [
        {
          "name": "Temperature",
          "address": "40001",
          "type": "float32"
        }
      ],
      "extra_config": {
        "slave_id": 1
      }
    }
  ]
}
```

### Parâmetros Comuns

| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `adapter_id` | string | - | ID único do adapter |
| `protocol_type` | string | - | Tipo do protocolo (opcua, modbus, mqtt) |
| `enabled` | bool | true | Se o adapter está habilitado |
| `host` | string | localhost | Host do dispositivo/servidor |
| `port` | int | varia | Porta de conexão |
| `scan_rate_ms` | int | 1000 | Taxa de leitura em ms |
| `timeout` | float | 5.0 | Timeout de conexão |
| `retry_interval` | float | 10.0 | Intervalo entre retries |
| `max_retries` | int | 5 | Máximo de tentativas de reconexão |
| `tags` | array | [] | Lista de tags a monitorar |
| `extra_config` | object | {} | Configurações específicas do protocolo |

## Uso Programático

### Criar Adapter Manualmente

```python
from gateway.app.services.protocols.modbus_adapter import create_modbus_adapter

# Criar adapter Modbus
adapter = create_modbus_adapter(
    adapter_id="plc1",
    host="192.168.1.10",
    port=502,
    tags=[
        {"name": "Temp", "address": "40001", "type": "float32"}
    ],
    slave_id=1
)

# Iniciar adapter
await adapter.start()

# Parar adapter
await adapter.stop()
```

### Usar Protocol Manager

```python
from gateway.app.services.protocol_manager import get_protocol_manager

# Obter manager global
manager = get_protocol_manager()

# Carregar configuração
await manager.load_config("/path/to/config.json")

# Iniciar todos os adapters
await manager.start_all()

# Obter estatísticas
stats = manager.get_statistics()
print(f"Adapters ativos: {stats['running_adapters']}/{stats['total_adapters']}")

# Parar todos
await manager.stop_all()
```

## Integração com Main Application

No arquivo `gateway/app/main.py`:

```python
from app.services.protocol_manager import init_protocol_manager, cleanup_protocol_manager

# Startup
@app.on_event("startup")
async def startup_event():
    # Inicializar Kafka producer
    await init_kafka_producer()

    # Inicializar InfluxDB consumer
    await start_timeseries_consumer()

    # Inicializar Protocol Manager
    await init_protocol_manager("/path/to/adapters_config.json")

# Shutdown
@app.on_event("shutdown")
async def shutdown_event():
    await cleanup_protocol_manager()
    await stop_timeseries_consumer()
    await cleanup_kafka_producer()
```

## Monitoramento e Logs

### Logs
Cada adapter emite logs com emojis para fácil identificação:

- 🔧 Inicialização
- 🔌 Conexão/Desconexão
- ✅ Sucesso
- ⚠️  Avisos
- ❌ Erros
- 📤 Publicação Kafka
- 🏥 Health check

### Estatísticas

```python
# Por adapter
stats = adapter.get_stats()
# {
#   'adapter_id': 'plc1',
#   'protocol_type': 'modbus',
#   'connected': True,
#   'running': True,
#   'read_count': 1250,
#   'error_count': 2,
#   'last_read_time': '2025-01-15T10:30:00'
# }

# Todas as estatísticas
all_stats = manager.get_statistics()
# {
#   'total_adapters': 3,
#   'running_adapters': 3,
#   'connected_adapters': 2,
#   'adapters': {
#     'plc1': {...},
#     'opcua1': {...},
#     'mqtt1': {...}
#   }
# }
```

## Dependências

```bash
# OPC UA
pip install asyncua

# Modbus
pip install pymodbus

# MQTT
pip install asyncio-mqtt

# Kafka (já instalado)
pip install aiokafka
```

## Performance

| Protocolo | Taxa de Leitura | Latência | CPU | Memória |
|-----------|-----------------|----------|-----|---------|
| OPC UA | 100-1000 tags/s | 10-50ms | Baixo | ~50MB |
| Modbus | 50-200 tags/s | 50-100ms | Baixo | ~20MB |
| MQTT | 1000+ msgs/s | 5-20ms | Baixo | ~30MB |

## Troubleshooting

### Adapter não conecta

1. Verifique conectividade de rede: `ping <host>`
2. Verifique porta: `telnet <host> <port>`
3. Verifique logs: busque por ❌ ou ⚠️
4. Aumente timeout e max_retries

### Tags não aparecem no InfluxDB

1. Verifique se Kafka producer está rodando
2. Verifique se InfluxDB consumer está rodando
3. Verifique tópico Kafka: `docker exec kafka kafka-console-consumer --topic raw_tags --bootstrap-server localhost:9092`
4. Verifique logs do adapter para 📤

### Performance ruim

1. Reduza `scan_rate_ms` se necessário
2. Reduza número de tags monitoradas
3. Use subscription-based protocols (OPC UA, MQTT) em vez de polling (Modbus)
4. Otimize batch_size no InfluxDB consumer

## Roadmap

- [x] Base abstrata para adapters
- [x] OPC UA adapter
- [x] Modbus TCP adapter
- [x] MQTT adapter
- [x] Protocol Manager
- [ ] Ethernet/IP adapter
- [ ] Siemens S7 adapter
- [ ] Docker Compose integration
- [ ] Web UI para gerenciamento
- [ ] Alarmes e notificações
- [ ] Métricas Prometheus

## Contribuindo

Para adicionar um novo protocolo:

1. Crie `protocols/<protocol>_adapter.py`
2. Herde de `BaseProtocolAdapter`
3. Implemente métodos abstratos
4. Adicione factory function `create_<protocol>_adapter()`
5. Registre no `Protocol Manager._create_adapter_from_config()`
6. Adicione exemplos de configuração
7. Atualize documentação

## Licença

MIT License - Ver arquivo LICENSE para detalhes.
