# SmartPort Device Simulators

Simuladores de dispositivos industriais para testar o Gateway SmartPort.

## Simuladores Disponíveis

### 1. Modbus TCP Device Simulator

Simula um dispositivo industrial com protocolo Modbus TCP, gerando dados dinâmicos de processo.

#### Dados Simulados

| Endereço | Tipo | Descrição | Range | Unidade |
|----------|------|-----------|-------|---------|
| 40001 | Holding Register | Temperatura | 20-100 | °C (×10) |
| 40011 | Holding Register | Pressão | 0-10 | bar (×10) |
| 40021 | Holding Register | Vazão | 0-1000 | L/min |
| 40031 | Holding Register | Nível | 0-100 | % |
| 40041 | Holding Register | Potência | 0-10000 | W |
| 40051 | Holding Register | Velocidade | 0-3000 | RPM |
| Coil 1 | Digital | Motor Running | 0/1 | - |
| Coil 2 | Digital | Válvula Aberta | 0/1 | - |
| Coil 3 | Digital | Alarme Ativo | 0/1 | - |
| Coil 4 | Digital | Emergency Stop | 0/1 | - |

#### Instalação

```bash
cd simulators
pip install -r requirements.txt
```

#### Uso

**Modo Básico:**
```bash
python modbus_device_simulator.py
```

**Com Parâmetros:**
```bash
python modbus_device_simulator.py --host 0.0.0.0 --port 502 --update-interval 1.0
```

**Opções:**
- `--host`: Endereço para bind (padrão: 0.0.0.0)
- `--port`: Porta para escutar (padrão: 502)
- `--update-interval`: Intervalo de atualização em segundos (padrão: 1.0)

**Nota:** Porta 502 requer privilégios de superusuário:
```bash
sudo python modbus_device_simulator.py
```

Ou use porta alternativa (≥1024):
```bash
python modbus_device_simulator.py --port 5020
```

## Testando com Gateway

### 1. Iniciar o Simulador

```bash
cd simulators
python modbus_device_simulator.py --port 5020
```

### 2. Configurar Device no SmartPort

Via API ou Frontend, criar device com:
```json
{
  "name": "Simulated PLC",
  "protocol": "modbus_tcp",
  "ip_address": "localhost",
  "port": 5020,
  "site_id": "your-site-id",
  "enabled": true,
  "scan_rate": 1000
}
```

### 3. Configurar Tags

Exemplo de tag para temperatura:
```json
{
  "name": "Temperature_Tank1",
  "address": "40001",
  "data_type": "FLOAT",
  "device_id": "device-id",
  "unit": "°C",
  "scale_factor": 0.1,
  "enabled": true,
  "log_enabled": true
}
```

### 4. Verificar Dados

Os dados começarão a aparecer no dashboard SmartPort automaticamente.

## Desenvolvimento de Novos Simuladores

Para criar novos simuladores para outros protocolos:

1. Copie `modbus_device_simulator.py` como template
2. Substitua a biblioteca de protocolo (pymodbus → outra)
3. Adapte a lógica de atualização de dados
4. Adicione ao requirements.txt

### Protocolos Suportados para Futuros Simuladores

- **OPC UA**: usando `asyncua`
- **MQTT**: usando `paho-mqtt`
- **Siemens S7**: usando `python-snap7`
- **Ethernet/IP**: usando `pycomm3`

## Docker

### Executar Simulador em Container

```bash
docker run -it --rm \
  -p 5020:502 \
  -v $(pwd):/app \
  python:3.11-slim \
  bash -c "pip install pymodbus && python /app/modbus_device_simulator.py --host 0.0.0.0 --port 502"
```

## Troubleshooting

### Erro: Permission denied (porta 502)

Solução 1: Use sudo
```bash
sudo python modbus_device_simulator.py
```

Solução 2: Use porta ≥1024
```bash
python modbus_device_simulator.py --port 5020
```

Solução 3: Configure capabilities no Linux
```bash
sudo setcap 'cap_net_bind_service=+ep' $(which python3)
```

### Erro: Address already in use

Outra aplicação está usando a porta. Mude a porta:
```bash
python modbus_device_simulator.py --port 5021
```

### Gateway não conecta

1. Verifique se o simulador está rodando
2. Verifique o IP/porta configurados no device
3. Verifique firewall (permitir porta do simulador)
4. Use `telnet localhost 5020` para testar conectividade

## Logs

O simulador imprime logs a cada 10 iterações mostrando os valores atuais:

```
2024-10-28 15:30:00 - __main__ - INFO - Simulated Data - Temp: 65.3°C, Pressure: 5.2 bar, Flow: 580 L/min, Level: 62%, Power: 5450 W, RPM: 1680, Motor: 1, Alarm: 0
```

## Performance

- Update interval recomendado: 1-5 segundos
- O simulador pode simular múltiplos tags simultaneamente
- Consumo de CPU: ~1-2%
- Memória: ~30MB

## Próximas Funcionalidades

- [ ] Simulador OPC UA
- [ ] Simulador MQTT
- [ ] Simulador Siemens S7
- [ ] Simulador Ethernet/IP
- [ ] Interface web para controle dos simuladores
- [ ] Cenários pré-configurados (startup, shutdown, alarm)
- [ ] Gravação/replay de dados reais
