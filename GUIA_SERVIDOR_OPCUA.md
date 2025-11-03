# Guia Completo - Servidor OPC-UA do Simulador

## 📡 Servidor OPC-UA Implementado

✅ **Status**: O servidor OPC-UA está implementado e rodando em:
```
opc.tcp://localhost:4840/optiflow/terminal
```

## 🚀 Como Iniciar o Servidor OPC-UA

### Método 1: Script Standalone (Recomendado)

```bash
cd /home/user/OptiFlow-AI-/backend
python3 scripts/run_opcua_server.py
```

O servidor irá:
1. Criar 110 nós OPC-UA
2. Iniciar o simulador físico
3. Atualizar valores em tempo real (1 Hz)
4. Aceitar comandos via OPC-UA

### Método 2: Porta Personalizada

```bash
cd /home/user/OptiFlow-AI-/backend
python3 scripts/run_opcua_server.py --endpoint opc.tcp://0.0.0.0:4841/optiflow/terminal
```

## 🏷️ Tags Disponíveis (110+ tags)

### Comportas (Gates) - 10 unidades
```
TEAG.ARZ.GATES.GATE01.POSICAO.PV     # Posição atual (%)
TEAG.ARZ.GATES.GATE01.POSICAO.SP     # Setpoint (%) - ESCRITÁVEL
TEAG.ARZ.GATES.GATE01.VAZAO.PV       # Fluxo (t/h)
TEAG.ARZ.GATES.GATE01.ENTUPIDO.AL    # Alarme de entupimento
... GATE02 até GATE10
```

### Correias (Belts) - 3 unidades
```
TEAG.ARZ.CORR01.RPM.PV              # Rotação (RPM)
TEAG.ARZ.CORR01.VAZAO.PV            # Fluxo (t/h)
TEAG.ARZ.CORR01.CORRENTE.PV         # Corrente (A)
TEAG.ARZ.CORR01.POTENCIA.PV         # Potência (kW)
TEAG.ARZ.CORR01.TEMP_MANCAL.PV      # Temperatura mancal (°C)
TEAG.ARZ.CORR01.TEMP_CORREIA.PV     # Temperatura correia (°C)
TEAG.ARZ.CORR01.TEMP_TAMBOR.PV      # Temperatura tambor (°C)
TEAG.ARZ.CORR01.CARGA.PV            # Carga (%)
TEAG.ARZ.CORR01.SUBVELOCIDADE.AL    # Alarme de subvelocidade
TEAG.ARZ.CORR01.CHUTE.NIVEL.PV      # Nível do chute (%)
TEAG.ARZ.CORR01.CHUTE.ENTUPIDO.AL   # Alarme chute entupido
... CORR02, CORR03
```

### Elevador
```
TEAG.ELV.ELV01.VAZAO.PV             # Fluxo (t/h)
TEAG.ELV.ELV01.VELOCIDADE.PV        # Velocidade (m/s)
TEAG.ELV.ELV01.CORRENTE.PV          # Corrente (A)
TEAG.ELV.ELV01.POTENCIA.PV          # Potência (kW)
TEAG.ELV.ELV01.TEMP_MOTOR.PV        # Temperatura motor (°C)
TEAG.ELV.ELV01.TEMP_REDUTOR.PV      # Temperatura redutor (°C)
TEAG.ELV.ELV01.ESCORREGAMENTO.AL    # Alarme de escorregamento
```

### Balança
```
TEAG.BAL.BAL01.PESO.PV              # Peso atual (kg)
TEAG.BAL.BAL01.PESO.SP              # Peso alvo (kg)
TEAG.BAL.BAL01.CICLOS.TOT           # Total de ciclos
TEAG.BAL.BAL01.TOTAL.TOT            # Massa total (t)
TEAG.BAL.BAL01.VAZAO_MEDIA.PV       # Vazão média (t/h)
TEAG.BAL.BAL01.ESTADO               # Estado do ciclo
```

### Shiploader
```
TEAG.SLD.SLD01.VAZAO.PV             # Vazão atual (t/h)
TEAG.SLD.SLD01.VAZAO.SP             # Vazão setpoint (t/h) - ESCRITÁVEL
TEAG.SLD.SLD01.POTENCIA.PV          # Potência (kW)
TEAG.SLD.SLD01.NIVEL_POEIRA         # Nível de poeira
```

### KPIs
```
TEAG.KPIs.PRODUCAO_TOTAL.TOT        # Produção total (t)
TEAG.KPIs.ENERGIA_TOTAL.TOT         # Energia total (kWh)
TEAG.KPIs.EFICIENCIA.PV             # Eficiência (kWh/t)
TEAG.KPIs.CUSTO_TOTAL               # Custo total (R$)
TEAG.KPIs.DISPONIBILIDADE.PV        # Disponibilidade (%)
```

### Controle (Métodos)
```
TEAG.CONTROL.CMD_START()            # Iniciar sistema
TEAG.CONTROL.CMD_STOP()             # Parar sistema
TEAG.CONTROL.CMD_EMERGENCY_STOP()   # Parada de emergência
```

## 🔧 Configuração no SmartPort/OptiFlow

### Passo 1: Adicionar Device OPC-UA

1. Acesse o SmartPort
2. Vá em **Devices** → **Add Device**
3. Selecione tipo: **OPC-UA**
4. Configure:
   ```
   Nome: Terminal Graneleiro - Simulador
   Endpoint: opc.tcp://localhost:4840/optiflow/terminal
   Security: None (Anonymous)
   Namespace Index: 2
   ```

### Passo 2: Importar Tags

#### Opção A: Importação Manual
1. Browse no namespace `2`
2. Expanda: `TEAG` → `ARZ` | `ELV` | `BAL` | `SLD` | `KPIs`
3. Selecione os tags desejados
4. Clique em **Import Selected**

#### Opção B: Importação em Lote
Use o browse recursivo para importar toda a hierarquia

#### Opção C: Adicionar Tags Individuais
```
Exemplo:
Tag Name: CORR01_CORRENTE
OPC-UA Path: ns=2;s=TEAG.ARZ.CORR01.CORRENTE.PV
Data Type: Double
Access: Read
```

### Passo 3: Configurar Polling/Subscription

- **Modo**: Subscription (recomendado)
- **Publishing Interval**: 1000 ms (1s)
- **Sampling Interval**: 500 ms
- **Queue Size**: 10

## ⚠️ Solução de Problemas

### Erro: "Connection Refused"

**Causa**: Servidor OPC-UA não está rodando

**Solução**:
```bash
cd /home/user/OptiFlow-AI-/backend
python3 scripts/run_opcua_server.py
```

Verifique se aparece:
```
✅ Server Ready
Endpoint: opc.tcp://0.0.0.0:4840/optiflow/terminal
```

### Erro: "Address Already in Use (Port 4840)"

**Causa**: Já há um processo usando a porta 4840

**Solução**:
```bash
# Matar processo na porta 4840
fuser -k 4840/tcp

# Ou matar todos processos Python do OPC-UA
pkill -f opcua_server

# Aguardar 2 segundos
sleep 2

# Reiniciar
python3 scripts/run_opcua_server.py
```

### Erro: "BadTypeMismatch" nos logs

**Causa**: Tipo de dado incorreto (Int64 vs Double)

**Status**: ✅ **CORRIGIDO** - arquivo `opcua_server.py` linha 471

A correção converte `cycle_count` para float antes de escrever.

### Erro: "Endpoint not Found" ou "Security Policy Mismatch"

**Causa**: Configuração incorreta no cliente OPC-UA

**Solução**:
- Endpoint EXATO: `opc.tcp://localhost:4840/optiflow/terminal`
- Security Mode: `None`
- Security Policy: `None` ou `NoSecurity`
- User: `Anonymous` (sem usuário/senha)

### Erro: Tags aparecem mas valores não mudam

**Causa**: Simulador não está iniciado

**Solução**:
1. Via OPC-UA, execute o método: `TEAG.CONTROL.CMD_START()`
2. Ou via API REST: `curl -X POST http://localhost:8000/api/v1/simulator/start`

## 🧪 Testar Conexão com Cliente OPC-UA

### Usando UAExpert (Windows)

1. Download: https://www.unified-automation.com/downloads/opc-ua-clients.html
2. Abra UAExpert
3. **Add Server**:
   - URL: `opc.tcp://localhost:4840/optiflow/terminal`
   - Security: None
4. **Connect**
5. Browse → Namespace 2 → TEAG

### Usando Prosys OPC UA Browser

1. Download: https://www.prosysopc.com/products/opc-ua-browser/
2. Connection → Add Server
3. Endpoint: `opc.tcp://localhost:4840/optiflow/terminal`
4. Security Mode: None
5. Connect

### Usando Python (asyncua)

```python
import asyncio
from asyncua import Client

async def test_connection():
    client = Client("opc.tcp://localhost:4840/optiflow/terminal")

    try:
        await client.connect()
        print("✅ Conectado!")

        # Ler uma tag
        node = client.get_node("ns=2;s=TEAG.ARZ.CORR01.CORRENTE.PV")
        value = await node.read_value()
        print(f"CORR01 Corrente: {value} A")

        # Escrever um setpoint
        sp_node = client.get_node("ns=2;s=TEAG.SLD.SLD01.VAZAO.SP")
        await sp_node.write_value(1200.0)
        print(f"Shiploader SP ajustado para 1200 t/h")

    finally:
        await client.disconnect()

asyncio.run(test_connection())
```

## 📊 Monitoramento em Tempo Real

O servidor atualiza automaticamente todos os valores a cada **1 segundo (1 Hz)**.

Valores que mudam dinamicamente:
- ✅ Corrente e potência (aumentam com carga)
- ✅ Temperaturas (sobem com uso)
- ✅ Fluxos (variam com abertura das comportas)
- ✅ Nível do chute (acumula se houver sobrecarga)
- ✅ Peso da balança (ciclo de enchimento/descarga)
- ✅ KPIs (energia, produção, custo)

## 🔐 Segurança

**Configuração Atual**: Sem segurança (desenvolvimento)
- Security Mode: None
- User Authentication: Anonymous

**Para Produção**: Edite `opcua_server.py` linha 85:
```python
# Adicionar segurança
self.server.set_security_policy([
    ua.SecurityPolicyType.Basic256Sha256
])

# Adicionar autenticação
from asyncua.server.users import User, UserManager
user_manager = UserManager()
user_manager.add_user(User("admin", "password123"))
self.server.set_user_manager(user_manager)
```

## ✅ Checklist de Verificação

- [ ] Servidor OPC-UA rodando sem erros
- [ ] Endpoint acessível: `opc.tcp://localhost:4840/optiflow/terminal`
- [ ] Cliente OPC-UA consegue conectar
- [ ] Tags aparecem no browse (110+ tags)
- [ ] Valores estão mudando em tempo real
- [ ] Consegue escrever setpoints
- [ ] Métodos de controle funcionam

## 📝 Logs de Debug

Para ver logs detalhados:
```bash
cd /home/user/OptiFlow-AI-/backend
python3 scripts/run_opcua_server.py 2>&1 | tee opcua_server.log
```

Logs importantes:
```
INFO - OPC-UA Server initialized - Namespace index: 2
INFO - Created 110 OPC-UA nodes
INFO - ✅ Server Ready
INFO - Starting OPC-UA Server at opc.tcp://0.0.0.0:4840/optiflow/terminal
INFO - Listening on 0.0.0.0:4840
INFO - ✅ OPC-UA Server is running
```

Se aparecer:
```
ERROR - Error updating nodes: BadTypeMismatch
```
→ Execute `git pull` para pegar a correção mais recente

## 💡 Dicas

1. **Use Subscription ao invés de Polling** para melhor performance
2. **Publishing Interval de 1000ms** (1s) é ideal para este simulador
3. **Tags escritáveis** terminam com `.SP` (setpoint)
4. **Valores atuais** terminam com `.PV` (process value)
5. **Alarmes** terminam com `.AL`
6. **Totalizadores** terminam com `.TOT`
7. **Namespace 2** contém todas as tags do simulador
8. **Namespace 0** é padrão do OPC-UA (não usar)

## 🔄 Integração com API REST

O servidor OPC-UA e a API REST rodam simultaneamente!

```bash
# Terminal 1 - OPC-UA Server
python3 scripts/run_opcua_server.py

# Terminal 2 - REST API
python3 -m uvicorn simulator_standalone:app --host 0.0.0.0 --port 8000

# Terminal 3 - Frontend
cd frontend && npm run dev
```

Agora você tem **3 interfaces** para o mesmo simulador:
1. ✅ **OPC-UA** - Tags industriais (porta 4840)
2. ✅ **REST API** - Endpoints HTTP (porta 8000)
3. ✅ **Web UI** - Interface gráfica (porta 5173)

## 📞 Suporte

Se encontrar erro ao conectar no SmartPort:
1. Cole o erro exato aqui
2. Verifique se o servidor está rodando: `lsof -i:4840`
3. Teste conexão com cliente standalone (UAExpert/Prosys)
4. Verifique logs do servidor OPC-UA

Todos os problemas conhecidos foram corrigidos! ✅
