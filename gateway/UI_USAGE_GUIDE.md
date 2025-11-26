# Gateway Configuration UI - Guia de Uso

## Visão Geral

A **Interface Web do Gateway OptiFlow** permite configurar e gerenciar adaptadores de protocolo industrial diretamente através do navegador, sem necessidade de editar arquivos JSON ou usar comandos curl.

![Gateway UI](docs/gateway-ui-screenshot.png)

---

## Acessando a Interface

### URL de Acesso

```
http://localhost:8080/
```

Ou diretamente:

```
http://localhost:8080/ui/index.html
```

### Em Produção (Edge Device)

Substitua `localhost` pelo IP do dispositivo edge:

```
http://192.168.1.100:8080/
```

---

## Funcionalidades Principais

### 1. Dashboard de Status

Ao abrir a UI, você verá um dashboard com:

- **Total de Adaptadores**: Quantidade de adaptadores configurados
- **Conectados**: Quantos estão conectados aos dispositivos
- **Rodando**: Quantos estão ativos coletando dados
- **Total de Tags**: Soma de todos os tags monitorados

Esses valores são atualizados automaticamente a cada 10 segundos.

---

### 2. Adicionar Novo Adaptador

#### Passo a Passo:

1. Clique no botão **"+ Adicionar Adaptador"** (verde)
2. Preencha o formulário:

   - **Nome do Adaptador**: Nome descritivo (ex: "PLC Silo 1")
   - **Protocolo**: Selecione o protocolo industrial
     - OPC UA
     - Modbus TCP/IP
     - MQTT
     - EtherNet/IP
     - Siemens S7
   - **Host**: IP ou hostname do dispositivo (ex: `192.168.1.10`)
   - **Porta**: Porta do protocolo (ex: `4840` para OPC UA)
   - **Taxa de Scan (ms)**: Intervalo de leitura em milissegundos (padrão: 1000)
   - **Timeout**: Tempo máximo de espera em segundos (padrão: 10.0)
   - **Habilitado**: Marque para iniciar automaticamente

3. Clique em **"Criar Adaptador"**
4. Aguarde a confirmação com o ID do adaptador criado

#### Exemplo - Adicionar OPC UA:

```
Nome: PLC Linha de Produção 1
Protocolo: OPC UA
Host: 192.168.1.50
Porta: 4840
Taxa de Scan: 1000ms
Timeout: 10.0s
Habilitado: ✓
```

---

### 3. Gerenciar Adaptadores Existentes

Cada adaptador é exibido em um **card** com informações completas:

#### Informações Exibidas:

- **Nome e ID** do adaptador
- **Status**: Badge verde (Conectado) ou vermelho (Desconectado)
- **Protocolo**: Tipo de protocolo usado
- **Endpoint**: IP:Porta do dispositivo
- **Taxa de Scan**: Intervalo de leitura
- **Quantidade de Tags**: Total de tags monitorados
- **Status de Execução**: Rodando ou Parado

#### Ações Disponíveis:

Cada card possui botões para:

1. **Iniciar/Parar**: Controla a execução do adaptador
   - Verde "Iniciar": Inicia coleta de dados
   - Vermelho "Parar": Para coleta de dados

2. **Testar**: Testa conexão com o dispositivo
   - Verifica se consegue conectar
   - Mostra quantos tags foram descobertos
   - Útil antes de ativar o adaptador

3. **Descobrir Tags**: Auto-descoberta de tags
   - Para **OPC UA**: Navega no namespace do servidor e encontra todas as variáveis
   - Exibe lista completa com nome, endereço e tipo
   - Os tags descobertos ficam disponíveis para monitoramento

4. **Excluir**: Remove o adaptador
   - Pede confirmação antes de excluir
   - Para automaticamente antes de remover

---

### 4. Descoberta Automática de Tags (OPC UA)

A funcionalidade de **descoberta automática** é especialmente poderosa para OPC UA:

#### Como Usar:

1. Certifique-se que o adaptador está **Conectado**
2. Clique em **"Descobrir Tags"**
3. Aguarde alguns segundos enquanto o sistema:
   - Conecta ao servidor OPC UA
   - Navega pelo namespace
   - Encontra todas as variáveis legíveis
4. Uma janela modal mostrará:
   - Quantidade de tags descobertos
   - Lista completa com:
     - **Nome**: Nome da variável
     - **Address**: NodeId no formato `ns=X;i=Y`
     - **Type**: Tipo de dados (double, boolean, int, etc.)

#### Exemplo de Resultado:

```
✅ 53 tags descobertos com sucesso!

running
Address: ns=2;i=7
Type: boolean

speed_mps
Address: ns=2;i=8
Type: double

temperature_celsius
Address: ns=2;i=9
Type: double

...
```

---

### 5. Testar Conexão

Antes de ativar um adaptador, é importante testar a conexão:

#### Procedimento:

1. Clique em **"Testar"** no card do adaptador
2. O sistema tentará:
   - Conectar ao dispositivo
   - Validar credenciais (se houver)
   - Descobrir tags disponíveis
3. Mostrará mensagem de sucesso ou erro

#### Mensagens Possíveis:

**Sucesso**:
```
✅ Conexão bem-sucedida!
Tags descobertos: 53
```

**Falha**:
```
❌ Falha na conexão: Connection timeout
```

---

### 6. Controlar Execução

#### Iniciar Adaptador:

1. Clique em **"Iniciar"** (botão verde)
2. O adaptador começará a:
   - Conectar ao dispositivo
   - Ler tags configurados
   - Publicar dados no Kafka
3. Status mudará para **"Rodando"**

#### Parar Adaptador:

1. Clique em **"Parar"** (botão vermelho)
2. O adaptador irá:
   - Parar leitura de tags
   - Desconectar do dispositivo
   - Manter configuração salva
3. Status mudará para **"Parado"**

---

### 7. Atualização Automática

A interface atualiza automaticamente:

- **A cada 10 segundos**: Recarrega lista de adaptadores
- **Valores em tempo real**: Status, contadores, conexões
- **Sem necessidade de refresh**: Dados sempre atualizados

Para forçar atualização manual, clique em **"Atualizar"**.

---

## Fluxo de Trabalho Típico

### Adicionar Novo PLC/Dispositivo

```
1. Clicar em "+ Adicionar Adaptador"
   ↓
2. Preencher dados do dispositivo
   ↓
3. Clicar em "Criar Adaptador"
   ↓
4. Testar conexão com botão "Testar"
   ↓
5. Descobrir tags automaticamente
   ↓
6. Verificar lista de tags descobertos
   ↓
7. Iniciar adaptador
   ↓
8. Monitorar status e contadores
```

---

## Protocolos Suportados

### OPC UA (Open Platform Communications)
- **Porta padrão**: 4840
- **Features**: Auto-descoberta de tags, navegação de namespace
- **Segurança**: None, Sign, SignAndEncrypt
- **Uso**: PLCs Siemens, Beckhoff, B&R, servidores SCADA

### Modbus TCP/IP
- **Porta padrão**: 502
- **Features**: Leitura de holding registers, coils, input registers
- **Configuração**: Slave ID, byte order
- **Uso**: PLCs Allen Bradley, Schneider, instrumentação

### MQTT (Message Queue Telemetry Transport)
- **Porta padrão**: 1883 (TCP), 8883 (TLS)
- **Features**: Subscribe a tópicos, QoS configurável
- **Autenticação**: Username/password opcional
- **Uso**: IoT devices, sensores wireless

### EtherNet/IP
- **Porta padrão**: 44818
- **Features**: Explicit messaging, I/O messaging
- **Uso**: PLCs Rockwell/Allen Bradley

### Siemens S7
- **Porta padrão**: 102
- **Features**: Leitura de DBs, marcadores, entradas/saídas
- **Uso**: PLCs Siemens S7-300, S7-400, S7-1200, S7-1500

---

## Troubleshooting

### Adaptador não conecta

**Problema**: Status mostra "Desconectado"

**Soluções**:
1. Verificar IP e porta estão corretos
2. Testar ping ao dispositivo: `ping 192.168.1.10`
3. Verificar firewall não está bloqueando porta
4. Clicar em "Testar" para diagnóstico detalhado
5. Verificar credenciais (se protocolo requer autenticação)

### Descoberta não encontra tags

**Problema**: "Descobrir Tags" retorna 0 tags

**Soluções**:
1. Verificar adaptador está conectado
2. Para OPC UA: Verificar namespace correto
3. Verificar dispositivo tem tags/variáveis configuradas
4. Checar permissões de leitura no dispositivo

### Interface não carrega

**Problema**: Erro ao acessar `http://localhost:8080/`

**Soluções**:
1. Verificar container Gateway está rodando: `docker ps | grep gateway`
2. Verificar porta 8080 está exposta: `docker port optiflow-gateway`
3. Verificar logs: `docker logs optiflow-gateway`
4. Reiniciar container: `docker compose restart gateway`

### Dados não aparecem no InfluxDB

**Problema**: Adaptador rodando mas dados não chegam no backend

**Soluções**:
1. Verificar Kafka está rodando: `docker ps | grep kafka`
2. Verificar tópico `raw_tags`: `docker exec kafka-1 kafka-console-consumer ...`
3. Verificar backend está consumindo: `docker logs optiflow-backend`
4. Verificar configuração Kafka no adaptador

---

## Configurações Avançadas

### Configuração via JSON (extra_config)

Para configurações específicas de protocolo, use o campo `extra_config`:

#### OPC UA:
```json
{
  "security_mode": "None",
  "security_policy": "None",
  "subscription_interval": 100,
  "username": "opcional",
  "password": "opcional"
}
```

#### Modbus:
```json
{
  "slave_id": 1,
  "byte_order": "big"
}
```

#### MQTT:
```json
{
  "client_id": "gateway-001",
  "username": "user",
  "password": "pass",
  "qos": 1,
  "topics": ["sensors/+/temperature"]
}
```

### Configuração de Kafka

Para cada adaptador, você pode customizar o destino Kafka:

```json
{
  "topic": "raw_tags_custom",
  "bootstrap_servers": "kafka-1:9092",
  "producer_config": {
    "acks": "all",
    "compression_type": "lz4"
  }
}
```

---

## API REST (Para Integração)

A UI utiliza a API REST do Gateway. Você pode usar os mesmos endpoints programaticamente:

### Listar Adaptadores
```bash
curl http://localhost:8080/api/adapters/
```

### Criar Adaptador
```bash
curl -X POST http://localhost:8080/api/adapters/ \
  -H "Content-Type: application/json" \
  -d '{
    "adapter_name": "PLC 1",
    "protocol_type": "opcua",
    "host": "192.168.1.10",
    "port": 4840,
    "enabled": true
  }'
```

### Descobrir Tags
```bash
curl -X POST http://localhost:8080/api/adapters/opcua-abc123/discover
```

Para documentação completa da API, acesse:
```
http://localhost:8080/docs
```

---

## Boas Práticas

### 1. Sempre Testar Antes de Ativar
- Use "Testar" para validar conectividade
- Verifique se encontra os tags esperados
- Só depois ative o adaptador

### 2. Use Taxas de Scan Apropriadas
- **Processo rápido** (< 1s): 100-500ms
- **Processo normal** (1-10s): 1000ms (padrão)
- **Processo lento** (> 10s): 5000-10000ms
- Não sobrecarregue PLCs antigos com scans muito rápidos

### 3. Organize Nomes
- Use nomes descritivos: "PLC Silo 1 - Temperatura"
- Evite apenas números: "Adapter 1"
- Inclua localização: "Linha 2 - Esteira Principal"

### 4. Monitore Status Regularmente
- Verifique contadores de erro
- Observe se adaptadores estão conectados
- Use auto-refresh para monitoramento passivo

### 5. Backup de Configurações
- Periodicamente exporte configurações via API
- Mantenha backup do arquivo `adapters_config.json`
- Documente IPs e portas dos dispositivos

---

## Segurança

### Considerações Importantes:

1. **Acesso à Interface**:
   - Atualmente sem autenticação (desenvolvimento)
   - Para produção: implementar firewall ou VPN
   - Restringir acesso à rede interna apenas

2. **Protocolos Industriais**:
   - Use security modes quando disponível (OPC UA)
   - Configure credenciais para protocolos que suportam
   - Isole rede industrial da rede corporativa

3. **Dados Sensíveis**:
   - Não exponha interface para internet pública
   - Use HTTPS/TLS em produção
   - Monitore logs de acesso

---

## Deployment em Produção

### Edge Device (Raspberry Pi, Industrial PC)

1. **Modificar docker-compose.yml**:
```yaml
gateway:
  ports:
    - "8080:8080"  # Apenas rede interna
  environment:
    - GATEWAY_CONFIG_PATH=/app/config/adapters_config.json
```

2. **Configurar Firewall**:
```bash
# Permitir apenas rede local
sudo ufw allow from 192.168.1.0/24 to any port 8080
```

3. **Criar Atalho no Desktop** (opcional):
```desktop
[Desktop Entry]
Name=OptiFlow Gateway Config
Exec=firefox http://localhost:8080/
Icon=network-server
Type=Application
```

### Acesso Remoto Seguro

Use túnel SSH para acesso remoto seguro:

```bash
# Do seu computador
ssh -L 8080:localhost:8080 user@edge-device-ip

# Depois acesse no navegador:
http://localhost:8080/
```

---

## Próximos Passos

Após configurar adaptadores:

1. **Verificar dados no Backend**:
   - Acessar dashboard principal: `http://localhost:3000`
   - Verificar tags no banco de dados
   - Conferir dashboards de produção

2. **Configurar Alertas**:
   - Definir limites de temperatura, pressão, etc.
   - Configurar notificações
   - Criar regras de qualidade

3. **Otimizar Coleta**:
   - Ajustar taxas de scan conforme necessidade
   - Remover tags não utilizados
   - Balancear carga entre múltiplos gateways

---

## Suporte

Para dúvidas ou problemas:

- **Logs do Gateway**: `docker logs optiflow-gateway`
- **API Docs**: http://localhost:8080/docs
- **Documentação Técnica**: `gateway/GATEWAY_API_DOCUMENTATION.md`

---

## Changelog

### v1.0.0 (2025-11-25)
- ✅ Interface web completa para configuração
- ✅ CRUD de adaptadores via UI
- ✅ Descoberta automática de tags (OPC UA)
- ✅ Teste de conexão integrado
- ✅ Dashboard de status em tempo real
- ✅ Auto-refresh a cada 10 segundos
- ✅ Suporte para 5 protocolos industriais
