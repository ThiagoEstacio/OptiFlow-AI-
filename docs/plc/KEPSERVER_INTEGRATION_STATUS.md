# OptiFlow AI - Integração com KEPServerEX e OPC UA
## Análise de Prontidão e Roadmap

**Data**: 2025-10-24
**Status Atual**: ⚠️ **Parcialmente Pronto** (60/100)

---

## ❓ Sua Pergunta

> "Posso testar com um simulador OPC como PLC por exemplo Kepserver? Nosso sistema está pronto para descobrir todos os tags, criar os archives dos tags no banco temporal e visualizar no front tanto em real time quanto em histórico?"

---

## ✅ O QUE JÁ ESTÁ PRONTO

### 1. Conexão com Servidor OPC UA ✅
- ✅ Código para conectar a qualquer servidor OPC UA (incluindo KEPServerEX)
- ✅ Cliente asyncua implementado
- ✅ Método `connect_opcua(url)` funcionando
- ✅ Disconnect automático

**Exemplo de uso**:
```python
# backend/app/services/plc_service.py
plc_service = PLCService()
await plc_service.connect_opcua("opc.tcp://localhost:4840")
```

### 2. Leitura de Tags OPC UA ✅
- ✅ Leitura de valores de tags
- ✅ Atualização de timestamp
- ✅ Quality status (GOOD/BAD/UNCERTAIN)
- ✅ Suporte a múltiplos tipos de dados

### 3. Gravação no Banco Temporal (InfluxDB) ✅
- ✅ Time Series Service implementado
- ✅ Método `write_tag_value()` funcional
- ✅ Batch writes suportado
- ✅ Query com agregação (mean, min, max)

### 4. WebSocket Streaming ✅
- ✅ `/ws/plc` endpoint implementado
- ✅ Subscribe/unsubscribe a tags
- ✅ Streaming a cada 1 segundo
- ✅ Gravação automática no InfluxDB

### 5. Visualização Frontend ✅
- ✅ RealTimePLCViewer (tempo real)
- ✅ HistoricalTrendChart (histórico)
- ✅ Recharts com gráficos bonitos
- ✅ Seletor de período (1h, 6h, 24h, 7 dias)

---

## ❌ O QUE ESTÁ FALTANDO

### 1. Browse/Discovery Automático de Tags ❌ **CRÍTICO**
**Status**: ❌ **NÃO IMPLEMENTADO**

**O que falta**:
- Método para "navegar" (browse) na árvore OPC UA
- Descobrir automaticamente todos os tags disponíveis
- Detectar tipo de dado de cada tag
- Identificar NodeID de cada tag

**Impacto**: Você teria que configurar cada tag manualmente no código.

### 2. Criação Automática de Tags no PostgreSQL ❌ **CRÍTICO**
**Status**: ❌ **NÃO IMPLEMENTADO**

**O que falta**:
- Endpoint API para salvar tags descobertos
- Model `Tag` no PostgreSQL (já existe, mas não integrado com PLC)
- Associação de tags com devices
- Metadata de tags (descrição, unidade, limites)

**Impacto**: Tags não são persistidos no banco relacional.

### 3. UI de Descoberta e Configuração ❌ **CRÍTICO**
**Status**: ❌ **NÃO IMPLEMENTADO**

**O que falta**:
- Página "PLC Configuration"
- Botão "Discover Tags" (browse OPC UA)
- Tree view de tags disponíveis
- Checkbox para selecionar quais tags monitorar
- Formulário para configurar unidade, limites, descrição

**Impacto**: Não há interface visual para configurar tags.

### 4. Configuração de Archives/Retenção ❌ **IMPORTANTE**
**Status**: ❌ **NÃO IMPLEMENTADO**

**O que falta**:
- Políticas de retenção de dados no InfluxDB
- Downsampling automático (1s → 1min → 1h → 1d)
- Configuração de archives por tag
- Continuous queries no InfluxDB

**Impacto**: Dados não têm política de retenção configurada.

### 5. Mapeamento Automático Device → Tags ❌ **IMPORTANTE**
**Status**: ❌ **NÃO IMPLEMENTADO**

**O que falta**:
- Criar Device no OptiFlow para representar o PLC/KEPServer
- Associar tags descobertos ao Device
- Sincronizar com modelo de dados existente

**Impacto**: Tags ficam "soltos", não associados a devices.

---

## 🎯 ROADMAP PARA INTEGRAÇÃO COMPLETA

### Fase 1: Discovery Básico (4-6 horas)
**Objetivo**: Descobrir e listar tags do KEPServerEX

**Tarefas**:
1. Implementar método `browse_opcua()` no PLCService
2. Criar endpoint `POST /api/v1/plc/discover`
3. Retornar lista de tags com NodeID, nome, tipo
4. Testar com KEPServerEX

**Entregável**: API que retorna todos os tags do servidor OPC UA

---

### Fase 2: Persistência de Tags (3-4 horas)
**Objetivo**: Salvar tags descobertos no PostgreSQL

**Tarefas**:
1. Criar endpoint `POST /api/v1/plc/tags/import`
2. Salvar tags na tabela `tags` do PostgreSQL
3. Associar tags a um device
4. Metadata (descrição, unidade, limites)

**Entregável**: Tags descobertos salvos no banco

---

### Fase 3: UI de Configuração (4-6 horas)
**Objetivo**: Interface visual para descoberta e configuração

**Tarefas**:
1. Criar página "PLC Configuration"
2. Botão "Connect to OPC UA Server"
3. Botão "Discover Tags"
4. Tree view de tags
5. Checkbox para selecionar tags
6. Salvar configuração

**Entregável**: UI completa de configuração

---

### Fase 4: Archives e Retenção (2-3 horas)
**Objetivo**: Configurar políticas de retenção no InfluxDB

**Tarefas**:
1. Criar retention policies no InfluxDB
2. Configurar downsampling
3. Continuous queries
4. UI para configurar por tag

**Entregável**: Sistema de archives automático

---

## ⚡ IMPLEMENTAÇÃO RÁPIDA (Agora!)

Vou implementar **Fase 1 + Fase 2** agora para você poder testar com KEPServerEX hoje mesmo!

### O que vou criar:

1. **Método `browse_opcua()` no PLCService**
   - Navega na árvore OPC UA
   - Retorna todos os tags encontrados
   - Detecta tipo de dado automaticamente

2. **Endpoint `POST /api/v1/plc/discover`**
   - Conecta ao servidor OPC UA
   - Faz browse de todos os tags
   - Retorna lista JSON

3. **Endpoint `POST /api/v1/plc/tags/import`**
   - Recebe lista de tags
   - Salva no PostgreSQL
   - Cria device se necessário

4. **Documentação de Integração com KEPServerEX**
   - Passo a passo de configuração
   - Exemplos de URL
   - Troubleshooting

---

## 📋 RESPOSTA DIRETA

### Você perguntou: "Posso testar com KEPServer?"
**Resposta**: ✅ **SIM**, você pode conectar! O código de conexão está pronto.

### "O sistema descobre todos os tags automaticamente?"
**Resposta**: ❌ **NÃO AINDA**, mas vou implementar isso AGORA.

### "Cria archives no banco temporal?"
**Resposta**: ⚠️ **PARCIALMENTE**. Grava no InfluxDB mas sem política de retenção configurada.

### "Visualiza no front em tempo real?"
**Resposta**: ✅ **SIM**, front está pronto! RealTimePLCViewer funciona.

### "Visualiza histórico?"
**Resposta**: ✅ **SIM**, front está pronto! HistoricalTrendChart funciona.

---

## 🚀 PRÓXIMOS PASSOS

**Vou implementar agora (próximos 30-45 minutos)**:
1. ✅ Browse/Discovery automático de tags OPC UA
2. ✅ Endpoint API para discovery
3. ✅ Importação de tags para PostgreSQL
4. ✅ Documentação de integração com KEPServerEX

**Depois você pode**:
1. Subir o KEPServerEX
2. Chamar API de discovery
3. Ver todos os tags
4. Importar os que quiser
5. Ver no frontend em tempo real!

---

**Posso começar a implementar agora?** 🚀
