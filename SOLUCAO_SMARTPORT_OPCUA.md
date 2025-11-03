# Solução: Conectar Simulador OPC-UA no SmartPort

## ⚠️ Problema Identificado

✅ **UAExpert conecta** - Servidor OPC-UA está funcionando
❌ **SmartPort não conecta** - Problema de configuração de endpoint

## 🔍 Causa Provável

O SmartPort pode estar:
1. **Rodando em container/Docker** - `localhost` do container ≠ `localhost` do host
2. **Rodando em outra máquina** - Precisa usar IP da rede
3. **Verificando Discovery Endpoint** incorretamente
4. **Usando configuração diferente** do UAExpert

## ✅ Solução 1: Usar IP da Máquina ao Invés de localhost

**IMPORTANTE**: Primeiro, corrija o endpoint (você digitou com erro):
- ❌ `opc.tcp://locallhost:4840/optiflow/termina` (3 L's, falta "l" no final)
- ✅ `opc.tcp://localhost:4840/optiflow/terminal`

### Opção A: Localhost (127.0.0.1)
```
opc.tcp://127.0.0.1:4840/optiflow/terminal
```

### Opção B: IP da Máquina (Recomendado)
```
opc.tcp://21.0.0.18:4840/optiflow/terminal
```

**Por quê?** Se o SmartPort estiver em container ou outra máquina, `localhost` não funciona!

---

## 🚀 Passo a Passo Completo para SmartPort

### Etapa 1: Garantir que o Servidor Está Acessível

```bash
# 1. Verificar se servidor está rodando
lsof -i:4840

# Se não estiver, inicie:
cd /home/user/OptiFlow-AI-/backend
python3 scripts/run_opcua_server.py

# 2. Testar conectividade da rede
nc -zv 21.0.0.18 4840

# Deve retornar: Connection to 21.0.0.18 4840 port [tcp/*] succeeded!
```

### Etapa 2: Configurar no SmartPort - MÉTODO CORRETO

#### Método 1: Via Discovery URL

1. No SmartPort, vá em **Devices** → **Add Device**
2. Tipo: **OPC UA**
3. Configuração:
   ```
   Nome: Terminal Graneleiro

   Discovery URL: opc.tcp://21.0.0.18:4840

   OU (se SmartPort está na mesma máquina):
   Discovery URL: opc.tcp://127.0.0.1:4840

   Security Mode: None
   Security Policy: None
   Message Mode: None
   Authentication: Anonymous
   ```

4. Clique em **Discover Endpoints**
5. Selecione da lista: `opc.tcp://21.0.0.18:4840/optiflow/terminal`
6. Save

#### Método 2: Endpoint Direto

Se o método acima não funcionar:

```
Server Endpoint: opc.tcp://21.0.0.18:4840/optiflow/terminal

Server URL: opc.tcp://21.0.0.18:4840/optiflow/terminal

Security: None / NoSecurity

User Authentication: Anonymous (sem usuário/senha)

Namespace URI: http://optiflow.com/terminal

Namespace Index: 2
```

#### Método 3: Via Form Específico do SmartPort

Alguns sistemas têm campos separados:

```
Protocol: OPC UA
Host: 21.0.0.18
Port: 4840
Path: /optiflow/terminal
Namespace: 2
```

---

## 🔧 Configurações Específicas do SmartPort

### Se houver campo "Application URI":
```
Application URI: urn:optiflow:terminal
```

### Se houver campo "Product URI":
```
Product URI: http://optiflow.com/terminal
```

### Se houver "Session Timeout":
```
Session Timeout: 60000 (60 segundos)
```

### Se houver "Request Timeout":
```
Request Timeout: 10000 (10 segundos)
```

---

## ⚙️ Solução 2: Restart do Servidor OPC-UA com Binding Correto

O servidor já está configurado para `0.0.0.0` (todas as interfaces), mas vamos garantir:

```bash
# Parar servidor atual
pkill -f opcua_server

# Aguardar
sleep 2

# Reiniciar
cd /home/user/OptiFlow-AI-/backend
python3 scripts/run_opcua_server.py
```

Verifique se aparece:
```
Listening on 0.0.0.0:4840  ← Deve estar em 0.0.0.0, não em 127.0.0.1
✅ OPC-UA Server is running
```

---

## 🧪 Teste de Conectividade

### Teste 1: Porta Aberta
```bash
# Da máquina onde está o SmartPort, execute:
telnet 21.0.0.18 4840

# Ou
nc -zv 21.0.0.18 4840

# Deve conectar com sucesso
```

### Teste 2: Discovery Endpoint
```bash
# Instalar cliente OPC-UA de linha de comando
pip3 install opcua-client

# Testar discovery
python3 -c "
from asyncua import Client
import asyncio

async def test():
    client = Client('opc.tcp://21.0.0.18:4840')
    await client.connect()
    print('✅ Conectado!')
    endpoints = await client.get_endpoints()
    for ep in endpoints:
        print(f'Endpoint: {ep.EndpointUrl}')
    await client.disconnect()

asyncio.run(test())
"
```

---

## 📋 Checklist de Troubleshooting

- [ ] Servidor OPC-UA está rodando (`lsof -i:4840`)
- [ ] Endpoint está correto: `opc.tcp://21.0.0.18:4840/optiflow/terminal`
- [ ] Porta 4840 acessível (`nc -zv 21.0.0.18 4840`)
- [ ] UAExpert consegue conectar ✅ (confirmado)
- [ ] Security Mode: **None** (não Basic256, não SignAndEncrypt)
- [ ] Authentication: **Anonymous** (sem usuário/senha)
- [ ] Namespace correto: **2** (não 0, não 1)

---

## 🐛 Erros Comuns no SmartPort

### Erro: "Failed to connect to discovery endpoint"
**Solução**: Use endpoint direto ao invés de discovery:
```
opc.tcp://21.0.0.18:4840/optiflow/terminal
```

### Erro: "Endpoint not found"
**Causa**: Endpoint digitado incorreto
**Solução**: Copie e cole EXATAMENTE:
```
opc.tcp://21.0.0.18:4840/optiflow/terminal
```

### Erro: "Security policy not supported"
**Causa**: SmartPort tentando usar segurança
**Solução**: Configure Security para **None/NoSecurity**

### Erro: "Bad_SecurityChecksFailed"
**Causa**: Tentativa de autenticação
**Solução**: Use **Anonymous** authentication

### Erro: "Connection timeout"
**Causa**: Firewall ou porta bloqueada
**Solução**:
```bash
# Verificar firewall
sudo ufw status

# Se estiver ativo, liberar porta 4840
sudo ufw allow 4840/tcp
```

---

## 🔍 Debug Avançado

### Capturar log do servidor OPC-UA:
```bash
cd /home/user/OptiFlow-AI-/backend
python3 scripts/run_opcua_server.py 2>&1 | tee opcua_debug.log
```

Quando você tentar conectar do SmartPort, o log mostrará:
```
INFO - New client connected from xxx.xxx.xxx.xxx
```

Se NÃO aparecer nada, o SmartPort não está sequer tentando conectar.

### Ver requisições na porta 4840:
```bash
# Em outro terminal
sudo tcpdump -i any port 4840 -A

# Tente conectar do SmartPort
# Você deve ver tráfego OPC-UA
```

---

## 📸 Configuração no SmartPort - Screenshots

Aqui está como deve ficar no SmartPort:

```
┌─────────────────────────────────────────────┐
│ Add OPC-UA Device                           │
├─────────────────────────────────────────────┤
│ Device Name: Terminal Graneleiro            │
│                                             │
│ Connection:                                 │
│ ┌──────────────────────────────────────────┐│
│ │ opc.tcp://21.0.0.18:4840/optiflow/terminal│
│ └──────────────────────────────────────────┘│
│                                             │
│ Security Mode: [None ▼]                     │
│                                             │
│ Authentication: [Anonymous ▼]               │
│                                             │
│ [Test Connection]  [Save]                   │
└─────────────────────────────────────────────┘
```

---

## 💡 Dica: Use o Mesmo Endpoint do UAExpert

No UAExpert, vá em **Connection** e copie o endpoint EXATO que funcionou.

**Cole ESSE MESMO endpoint no SmartPort!**

---

## 🔄 Alternativa: Usar Porta Diferente

Se a porta 4840 estiver com problemas:

```bash
# Iniciar servidor em porta diferente
cd /home/user/OptiFlow-AI-/backend
python3 scripts/run_opcua_server.py --endpoint opc.tcp://0.0.0.0:4841/optiflow/terminal
```

Então use no SmartPort:
```
opc.tcp://21.0.0.18:4841/optiflow/terminal
```

---

## ❓ Informações Necessárias

Para te ajudar melhor, me diga:

1. **Onde o SmartPort está rodando?**
   - [ ] Mesma máquina que o servidor OPC-UA
   - [ ] Outra máquina na rede
   - [ ] Container Docker
   - [ ] Cloud/VM

2. **Qual endpoint você está usando no SmartPort?**
   - Copie e cole EXATAMENTE como está configurado

3. **Qual erro aparece no SmartPort?**
   - Mensagem de erro completa

4. **No UAExpert, qual endpoint você usou que funcionou?**
   - Copie da barra de endereço do UAExpert

5. **O SmartPort tem opção de "Discovery URL" ou só "Endpoint URL"?**
   - Tire um print da tela de configuração se possível

---

## 📝 Quick Fix - Teste Rápido

Execute isto AGORA:

```bash
# 1. Parar servidor
pkill -f opcua

# 2. Reiniciar com log verbose
cd /home/user/OptiFlow-AI-/backend
python3 scripts/run_opcua_server.py 2>&1 | tee log.txt &

# 3. Verificar que está rodando
sleep 5
lsof -i:4840

# 4. No SmartPort, use ESTE endpoint:
```

**ENDPOINT PARA USAR NO SMARTPORT:**
```
opc.tcp://21.0.0.18:4840/optiflow/terminal
```

Se ainda não funcionar, execute:
```bash
# Ver últimas 50 linhas do log
tail -50 log.txt
```

E me envie o output! 📤
