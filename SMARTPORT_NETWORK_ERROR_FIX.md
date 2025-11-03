# ✅ Servidor OPC-UA Está Rodando - Como Conectar no SmartPort

## Status Atual

✅ **Servidor OPC-UA RODANDO**
- Endpoint: `opc.tcp://0.0.0.0:4840/optiflow/terminal`
- Escutando em: `0.0.0.0:4840` (todas as interfaces de rede)
- 110 tags disponíveis
- UAExpert conecta com sucesso ✅

❌ **SmartPort não conecta** - Network Error

---

## 🔥 SOLUÇÃO - Teste AGORA Nesta Ordem

### **1. Onde está rodando o SmartPort?**

Execute isto para descobrir:

#### Se SmartPort está na MESMA máquina:

```bash
# Teste se localhost funciona
curl -v telnet://localhost:4840

# Se conectar, use no SmartPort:
opc.tcp://localhost:4840/optiflow/terminal
```

#### Se SmartPort está em OUTRA máquina ou Docker:

```bash
# Descubra o IP da máquina do servidor
hostname -I
# Retorna: 21.0.0.18

# Use no SmartPort:
opc.tcp://21.0.0.18:4840/optiflow/terminal
```

---

### **2. ENDPOINTS PARA TESTAR (na ordem)**

Teste cada um destes no SmartPort, NA ORDEM:

#### **Tentativa 1:** IP da máquina
```
opc.tcp://21.0.0.18:4840/optiflow/terminal
```

#### **Tentativa 2:** Localhost com IP
```
opc.tcp://127.0.0.1:4840/optiflow/terminal
```

#### **Tentativa 3:** Localhost nome
```
opc.tcp://localhost:4840/optiflow/terminal
```

#### **Tentativa 4:** Hostname
```bash
# Descobrir hostname
hostname
# Exemplo: optiflow-server

# Use:
opc.tcp://optiflow-server:4840/optiflow/terminal
```

---

### **3. Configuração EXATA no SmartPort**

```
┌─────────────────────────────────────────────┐
│ Add OPC-UA Device                           │
├─────────────────────────────────────────────┤
│ Device Name: Terminal Graneleiro            │
│                                             │
│ Connection Method: [Direct Endpoint ▼]      │
│                                             │
│ Server URL:                                 │
│ ┌──────────────────────────────────────────┐│
│ │opc.tcp://21.0.0.18:4840/optiflow/terminal││
│ └──────────────────────────────────────────┘│
│                                             │
│ Security:                                   │
│   Mode: [None ▼]                            │
│   Policy: [None ▼]                          │
│                                             │
│ Authentication: [Anonymous ▼]               │
│                                             │
│ [Test Connection]  [Save]                   │
└─────────────────────────────────────────────┘
```

---

## 🔧 Verificações de Rede

### Teste 1: Servidor está acessível?

```bash
# Da máquina onde o SmartPort está rodando, execute:

# Opção A: telnet
telnet 21.0.0.18 4840

# Opção B: nc (netcat)
nc -zv 21.0.0.18 4840

# Opção C: curl
curl telnet://21.0.0.18:4840

# DEVE retornar: "Connected" ou "succeeded"
```

**Se NÃO conectar**: Problema de rede/firewall

### Teste 2: Firewall bloqueando?

```bash
# Verificar firewall
sudo ufw status

# Se estiver ativo, liberar porta 4840
sudo ufw allow 4840/tcp

# Reiniciar firewall
sudo ufw reload
```

### Teste 3: SmartPort consegue fazer DNS/ping?

```bash
# Da máquina do SmartPort:
ping 21.0.0.18

# DEVE responder
```

---

## 🎯 Checklist de Debug

Execute isto e me envie os resultados:

```bash
# 1. Confirmar que servidor está rodando
lsof -i:4840
# DEVE mostrar processo Python escutando

# 2. Ver interfaces de rede
ip addr show | grep "inet "
# Anote todos os IPs

# 3. Testar conectividade local
nc -zv localhost 4840
nc -zv 127.0.0.1 4840
nc -zv 21.0.0.18 4840

# 4. Ver hostname
hostname

# 5. Ver rotas de rede
ip route
```

**Me envie a saída de cada comando!**

---

## 🔍 Diagnóstico: Por que "Network Error"?

### Cenário A: SmartPort em Docker/Container

**Problema**: `localhost` do container ≠ `localhost` do host

**Solução**:
```
# No SmartPort, use:
opc.tcp://host.docker.internal:4840/optiflow/terminal

# OU o IP da bridge do Docker:
opc.tcp://172.17.0.1:4840/optiflow/terminal

# OU o IP real da máquina:
opc.tcp://21.0.0.18:4840/optiflow/terminal
```

### Cenário B: SmartPort em Outra Máquina

**Problema**: Firewall ou roteamento

**Solução**:
```bash
# Na máquina do servidor OPC-UA:
sudo ufw allow from <IP_SMARTPORT> to any port 4840

# OU desabilitar firewall temporariamente para testar:
sudo ufw disable
```

### Cenário C: SmartPort Requer Discovery Endpoint

**Problema**: SmartPort não aceita endpoint direto

**Solução**: Use discovery URL:
```
Discovery URL: opc.tcp://21.0.0.18:4840

# Depois clique "Discover" e selecione:
opc.tcp://21.0.0.18:4840/optiflow/terminal
```

---

## 📊 Servidor OPC-UA - Status Detalhado

### Informações do Servidor

```
✅ Status: RUNNING
✅ Listening: 0.0.0.0:4840 (todas interfaces)
✅ Namespace: 2
✅ Tags: 110
✅ Security: None (Anonymous)
✅ UAExpert: CONECTA ✅
```

### Endpoints Disponíveis

```
opc.tcp://localhost:4840/optiflow/terminal
opc.tcp://127.0.0.1:4840/optiflow/terminal
opc.tcp://21.0.0.18:4840/optiflow/terminal
opc.tcp://<HOSTNAME>:4840/optiflow/terminal
```

**TODOS estes endpoints levam ao mesmo servidor!**

---

## 🚀 Próximos Passos

### 1. MANTER O SERVIDOR RODANDO

O servidor está rodando agora. Para mantê-lo:

```bash
# Em um terminal dedicado:
cd /home/user/OptiFlow-AI-/backend
python3 scripts/run_opcua_server.py

# Deixe esse terminal aberto!
```

### 2. TESTAR CADA ENDPOINT NO SMARTPORT

Tente na ordem:
1. `opc.tcp://21.0.0.18:4840/optiflow/terminal` ← **TESTE ESTE PRIMEIRO**
2. `opc.tcp://127.0.0.1:4840/optiflow/terminal`
3. `opc.tcp://localhost:4840/optiflow/terminal`

### 3. REPORTAR RESULTADO

Me diga:
- **Qual endpoint você testou?**
- **Qual erro EXATO aparece?**
- **SmartPort está rodando onde?** (mesma máquina, outra máquina, Docker?)

---

## 💡 DICA IMPORTANTE

**Copie o endpoint do UAExpert!**

1. No UAExpert, vá em **Session** → **Connection Settings**
2. **Copie** o endpoint que FUNCIONOU
3. **Cole** EXATO no SmartPort

Se UAExpert conecta com:
```
opc.tcp://192.168.1.100:4840/optiflow/terminal
```

Use ESSE MESMO no SmartPort!

---

## ⚠️ Nota sobre BadTypeMismatch

Você verá estes erros no log:
```
ERROR - Error updating nodes: BadTypeMismatch
```

**IGNORE POR ENQUANTO** - isso NÃO impede a conexão!

É um bug secundário já corrigido. Faça `git pull` depois para pegar a correção.

---

## ✅ Comando Rápido de Teste

Execute isto AGORA para testar tudo:

```bash
# 1. Verificar servidor rodando
lsof -i:4840 && echo "✅ Servidor rodando" || echo "❌ Servidor NÃO está rodando"

# 2. Testar conectividade local
nc -zv 21.0.0.18 4840 && echo "✅ Porta acessível" || echo "❌ Porta bloqueada"

# 3. Mostrar IPs disponíveis
echo "Use um destes IPs no SmartPort:"
hostname -I | tr ' ' '\n' | while read ip; do echo "  opc.tcp://$ip:4840/optiflow/terminal"; done
```

**Me envie a saída desse comando!** 📤

---

## 🆘 Ainda Não Funciona?

Se após testar TODOS os endpoints acima ainda der "network error", me envie:

1. **Print da tela do SmartPort** mostrando o erro
2. **Saída do comando acima**
3. **Onde o SmartPort está rodando?** (Docker? Outra máquina? VM?)
4. **Endpoint que FUNCIONOU no UAExpert** (copie exato)

Vou resolver! 🚀
