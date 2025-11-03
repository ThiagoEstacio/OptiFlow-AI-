# 🏭 OptiFlow Grain Terminal OPC-UA Server

Servidor OPC-UA real com simulador de processo integrado para Terminal Exportador de Grãos de 1500 t/h.

## 📋 Visão Geral

Este sistema combina:
- ✅ **Simulador de Processo Real** - Física completa de um terminal portuário
- ✅ **Servidor OPC-UA** - Protocolo industrial padrão IEC 62541
- ✅ **100+ Variáveis em Tempo Real** - Atualizadas a 1 Hz
- ✅ **Comandos Remotos** - Start/Stop/Emergency via OPC-UA
- ✅ **Setpoints Graváveis** - Controle de vazadores e shiploader
- ✅ **Alarmes e Eventos** - Notificações em tempo real

## 🚀 Início Rápido

### 1. Instalar Dependências

```bash
cd backend
pip install -r requirements.txt
```

O `requirements.txt` já inclui `asyncua==1.0.6`.

### 2. Iniciar o Servidor

```bash
python scripts/run_opcua_server.py
```

O servidor inicia em: `opc.tcp://localhost:4840/optiflow/terminal`

### 3. Conectar com Cliente OPC-UA

**Recomendado: UAExpert** (gratuito para Windows)
- Download: https://www.unified-automation.com/products/development-tools/uaexpert.html
- Configurar endpoint: `opc.tcp://localhost:4840/optiflow/terminal`
- Security: None (Anonymous)

**Alternativas:**
- Prosys OPC UA Browser
- Ignition (trial)
- KEPServerEX

## 📊 Estrutura de Tags (Address Space)

### Hierarquia OPC-UA

```
Root
└── TEAG (Terminal Exportador de Grãos)
    ├── SYSTEM
    │   └── RUNNING.PV
    ├── ARZ (Armazém)
    │   ├── INVENTARIO.PV
    │   ├── NIVEL.PV
    │   ├── GATES
    │   │   ├── GATE01
    │   │   │   ├── POSICAO.PV (Double, Read)
    │   │   │   ├── POSICAO.SP (Double, Read/Write)
    │   │   │   ├── VAZAO.PV (Double, Read)
    │   │   │   └── ENTUPIDO.AL (Boolean, Read)
    │   │   ├── GATE02
    │   │   └── ... GATE10
    │   ├── CORR01 (Correia 1)
    │   │   ├── LIGADO.FB
    │   │   ├── RPM.PV
    │   │   ├── VELOCIDADE.PV
    │   │   ├── VAZAO.PV
    │   │   ├── CARGA.PV
    │   │   ├── CORRENTE.PV
    │   │   ├── POTENCIA.PV
    │   │   ├── TEMP_MANCAL.PV
    │   │   ├── TEMP_CORREIA.PV
    │   │   ├── TEMP_TAMBOR.PV
    │   │   ├── SUBVELOCIDADE.WARN
    │   │   └── SUBVELOCIDADE.AL
    │   ├── CORR02 (Correia 2)
    │   └── CORR03 (Correia 3)
    ├── ELV (Elevador)
    │   └── ELV01
    │       ├── LIGADO.FB
    │       ├── VELOCIDADE.PV
    │       ├── VAZAO.PV
    │       ├── CORRENTE.PV
    │       ├── POTENCIA.PV
    │       ├── TEMP_MOTOR.PV
    │       ├── TEMP_REDUCAO.PV
    │       ├── ESCORREGAMENTO.AL
    │       └── CORREIA_FROUXA.AL
    ├── BAL (Balança)
    │   └── BAL01
    │       ├── LIGADO.FB
    │       ├── PESO.PV
    │       ├── PESO.SP
    │       ├── CICLOS.TOT
    │       ├── TOTAL.TOT
    │       ├── VAZAO.PV
    │       └── ESTADO.PV
    ├── SLD (Shiploader)
    │   └── SLD01
    │       ├── LIGADO.FB
    │       ├── VAZAO.SP (Read/Write)
    │       ├── VAZAO.PV
    │       ├── POTENCIA.PV
    │       └── POEIRA.PV
    ├── KPIs
    │   ├── ENERGIA_TOTAL.TOT
    │   ├── PRODUCAO_TOTAL.TOT
    │   ├── EFICIENCIA_ENERGIA.PV
    │   └── CUSTO_ENERGIA.TOT
    └── CONTROL
        ├── CMD_START() [Method]
        ├── CMD_STOP() [Method]
        └── CMD_EMERGENCY_STOP() [Method]
```

## 🎮 Controle Via OPC-UA

### Variáveis Graváveis (Setpoints)

#### 1. Controle de Vazadores (Gates)

```python
# Abrir GATE01 em 75%
client.write_value("TEAG.ARZ.GATES.GATE01.POSICAO.SP", 75.0)

# Fechar GATE05
client.write_value("TEAG.ARZ.GATES.GATE05.POSICAO.SP", 0.0)
```

#### 2. Setpoint do Shiploader

```python
# Definir vazão em 1200 t/h
client.write_value("TEAG.SLD.SLD01.VAZAO.SP", 1200.0)
```

### Métodos (Comandos)

#### 1. Iniciar Sistema

```python
client.call_method("TEAG.CONTROL.CMD_START")
```

#### 2. Parar Sistema

```python
client.call_method("TEAG.CONTROL.CMD_STOP")
```

#### 3. Parada de Emergência

```python
client.call_method("TEAG.CONTROL.CMD_EMERGENCY_STOP")
```

## 📈 Monitoramento em Tempo Real

### KPIs Disponíveis

| Tag | Descrição | Unidade |
|-----|-----------|---------|
| `TEAG.KPIs.ENERGIA_TOTAL.TOT` | Energia total consumida | kWh |
| `TEAG.KPIs.PRODUCAO_TOTAL.TOT` | Massa total produzida | t |
| `TEAG.KPIs.EFICIENCIA_ENERGIA.PV` | Eficiência energética | kWh/t |
| `TEAG.KPIs.CUSTO_ENERGIA.TOT` | Custo total de energia | R$ |

### Alarmes

Alarmes são publicados como variáveis booleanas com sufixo `.AL`:

- `TEAG.ARZ.CORR01.SUBVELOCIDADE.AL` - Subvelocidade na correia
- `TEAG.ELV.ELV01.ESCORREGAMENTO.AL` - Escorregamento no elevador
- `TEAG.ARZ.GATES.GATExx.ENTUPIDO.AL` - Vazador entupido

## 🔧 Configuração Avançada

### Endpoint Customizado

```bash
python scripts/run_opcua_server.py --endpoint opc.tcp://0.0.0.0:4841/optiflow/terminal
```

### Taxa de Atualização

Modificar em `opcua_server.py`:

```python
self.update_rate_hz = 2.0  # 2 Hz (padrão: 1 Hz)
```

### Segurança

Para produção, habilitar autenticação e criptografia:

```python
self.server.set_security_policy([
    ua.SecurityPolicyType.Basic256Sha256_Sign,
    ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt
])
```

## 🧪 Teste de Integração

### Exemplo Python (Cliente)

```python
from asyncua import Client
import asyncio

async def test_opcua():
    client = Client("opc.tcp://localhost:4840/optiflow/terminal")

    async with client:
        # Ler vazão do shiploader
        vazao = await client.read_value("TEAG.SLD.SLD01.VAZAO.PV")
        print(f"Vazão: {vazao} t/h")

        # Modificar setpoint
        await client.write_value("TEAG.SLD.SLD01.VAZAO.SP", 1300.0)

        # Iniciar sistema
        await client.call_method("TEAG.CONTROL.CMD_START")

asyncio.run(test_opcua())
```

### Exemplo C# (.NET)

```csharp
using Opc.Ua;
using Opc.Ua.Client;

var endpoint = "opc.tcp://localhost:4840/optiflow/terminal";
var session = Session.Create(...);

// Ler variável
var node = new NodeId("TEAG.SLD.SLD01.VAZAO.PV");
var value = session.ReadValue(node);
Console.WriteLine($"Vazão: {value.Value} t/h");

// Escrever setpoint
var spNode = new NodeId("TEAG.SLD.SLD01.VAZAO.SP");
session.WriteValue(spNode, new DataValue(1200.0));
```

## 📦 Integração com SCADA

### Ignition (Inductive Automation)

1. Adicionar Device OPC-UA
2. Endpoint: `opc.tcp://localhost:4840/optiflow/terminal`
3. Browse tags em `TEAG`
4. Criar tags no Tag Browser
5. Arrastar para telas

### Elipse E3/Power

1. Configurar driver OPC-UA
2. Adicionar servidor OPC-UA
3. Importar tags
4. Linkar com telas

### WinCC/Simatic

1. Configurar OPC-UA Client
2. Importar address space
3. Criar HMI com tags

## 🎯 Casos de Uso

### 1. Treinamento de Operadores

- Simular condições normais e anormais
- Testar procedimentos de emergência
- Praticar otimização de processo

### 2. Desenvolvimento SCADA

- Testar telas sem processo real
- Validar lógicas de controle
- Verificar alarmes e intertravamentos

### 3. Teste de Integrações

- Validar comunicação OPC-UA
- Testar MES/ERP integration
- Desenvolvimento de dashboards

### 4. Análise de Dados

- Coletar dados históricos
- Treinar modelos de ML
- Otimizar parâmetros de controle

## 🔍 Troubleshooting

### Erro: "Cannot connect to endpoint"

```bash
# Verificar se servidor está rodando
ps aux | grep opcua

# Verificar porta
netstat -an | grep 4840

# Testar localmente
telnet localhost 4840
```

### Erro: "Access Denied"

- Verificar modo de segurança (usar None para testes)
- Confirmar permissões de firewall

### Valores não atualizam

- Verificar taxa de update (1 Hz padrão)
- Confirmar que simulação está rodando
- Checar logs do servidor

## 📚 Documentação Adicional

- **OPC-UA Specification:** https://reference.opcfoundation.org/
- **AsyncUA Library:** https://github.com/FreeOpcUa/opcua-asyncio
- **UAExpert Manual:** https://documentation.unified-automation.com/

## 🤝 Suporte

Para questões técnicas:
- Email: support@optiflow.com
- GitHub Issues: [link]

---

**Desenvolvido com ❤️ pela equipe OptiFlow**

Sistema em conformidade com IEC 62541 (OPC-UA)
