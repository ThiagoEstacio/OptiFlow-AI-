# 🤖 OptiFlow AI Agent - Capacidades Completas

## 📊 Status Atual do Sistema

### ✅ Modo Atual: **FALLBACK MODE** (Especializado PCM/PCO)
- **Localização**: `backend/app/api/routes/ai_agent.py` (linha 641)
- **Razão**: Ollama desabilitado para velocidade de resposta
- **Funcionalidades Ativas**: Análise de alarmes especializada

### 🧠 Modo Completo: **TOOL-CALLING MODE** (Disponível mas desabilitado)
- **LLM**: Qwen2.5:7B (4.7 GB - já baixado ✅)
- **Status**: Pronto para ativação
- **Capacidades**: Todas as ferramentas matemáticas e lógicas

---

## 🔧 Ferramentas Disponíveis (Agent Tools)

### 1️⃣ **Valores em Tempo Real**

#### `get_realtime_value`
Obtém o valor atual de uma tag/sensor específica.

**Exemplo de uso:**
```
"Qual o valor atual da temperatura do ELEV01?"
"Me mostre a velocidade da correia ARZ_CORR01 agora"
```

**Retorna:**
```json
{
  "tag_id": "ELEV01_TEMP_C_PV",
  "value": 72.5,
  "timestamp": "2025-11-18T10:30:00Z",
  "unit": "°C",
  "quality": "good"
}
```

#### `get_multiple_realtime_values`
Obtém valores atuais de múltiplas tags simultaneamente.

**Exemplo de uso:**
```
"Me mostre temperatura e corrente de todos os elevadores"
"Valores atuais de ELEV01_TEMP, ELEV01_CURRENT, ELEV02_TEMP"
```

---

### 2️⃣ **Cálculos Estatísticos**

#### `calculate_statistics`
Calcula estatísticas (média, máximo, mínimo, desvio padrão) sobre período de tempo.

**Capacidades matemáticas:**
- ✅ **Média (Mean)**: Valor médio ao longo do tempo
- ✅ **Máximo (Max)**: Valor máximo registrado
- ✅ **Mínimo (Min)**: Valor mínimo registrado
- ✅ **Desvio Padrão (Stddev)**: Medida de variabilidade
- ✅ **Coeficiente de Variação**: `(stddev / mean) * 100`

**Períodos suportados:**
- `1h` - Última hora
- `6h` - Últimas 6 horas
- `12h` - Últimas 12 horas
- `24h` - Último dia
- `7d` - Última semana
- `30d` - Último mês

**Exemplo de uso:**
```
"Qual foi a temperatura média do ELEV01 nas últimas 24 horas?"
"Temperatura máxima e mínima do ELEV02 na última semana"
"Calcule média, desvio padrão e coeficiente de variação da velocidade"
```

**Retorna:**
```json
{
  "tag_id": "ELEV01_TEMP_C_PV",
  "duration": "24h",
  "statistics": {
    "mean": 72.3,
    "max": 85.2,
    "min": 65.1,
    "stddev": 4.8,
    "count": 1440
  },
  "coefficient_of_variation": 6.6
}
```

---

### 3️⃣ **Dados Históricos**

#### `get_historical_data`
Obtém série temporal completa de dados históricos.

**Agregações disponíveis:**
- `mean` - Média por intervalo
- `max` - Máximo por intervalo
- `min` - Mínimo por intervalo
- `sum` - Soma total
- `stddev` - Desvio padrão

**Exemplo de uso:**
```
"Me mostre a tendência de temperatura do ELEV01 nas últimas 6 horas"
"Histórico de velocidade da correia nas últimas 24h"
```

**Retorna:**
```json
{
  "tag_id": "ELEV01_TEMP_C_PV",
  "duration": "6h",
  "points": [
    {"timestamp": "2025-11-18T04:00:00Z", "value": 68.5},
    {"timestamp": "2025-11-18T05:00:00Z", "value": 70.2},
    {"timestamp": "2025-11-18T06:00:00Z", "value": 72.8},
    ...
  ]
}
```

---

### 4️⃣ **Operações Lógicas Avançadas**

#### `compare_tags`
Compara múltiplas tags para encontrar correlações e padrões.

**Capacidades:**
- ✅ Comparação de estatísticas entre variáveis
- ✅ Detecção de variabilidade (coeficiente de variação)
- ✅ Identificação de comportamentos (estável vs variável)
- ✅ Análise de até 10 tags simultaneamente

**Exemplo de uso:**
```
"Compare a temperatura do ELEV01 com ELEV02 nas últimas 12 horas"
"Qual elevador teve maior variação de temperatura ontem?"
```

**Retorna:**
```json
{
  "tags_compared": 2,
  "duration": "12h",
  "statistics": {
    "ELEV01_TEMP_C_PV": {
      "mean": 72.3,
      "stddev": 4.8,
      "coefficient_of_variation": 6.6
    },
    "ELEV02_TEMP_C_PV": {
      "mean": 75.1,
      "stddev": 8.2,
      "coefficient_of_variation": 10.9
    }
  },
  "insights": [
    "ELEV02_TEMP_C_PV: High variability (10.9% coefficient of variation)",
    "ELEV01_TEMP_C_PV: Very stable (6.6% coefficient of variation)"
  ]
}
```

#### `detect_anomalies`
Detecta anomalias usando métodos estatísticos (Z-score).

**Sensibilidades:**
- `low` - 3σ (99.7% confiança) - Apenas anomalias extremas
- `medium` - 2.5σ (98.8% confiança) - **Padrão**
- `high` - 2σ (95.4% confiança) - Mais sensível

**Exemplo de uso:**
```
"Detecte anomalias na temperatura do ELEV02 nas últimas 24 horas"
"Existe algum valor anormal na corrente elétrica?"
```

**Retorna:**
```json
{
  "tag_id": "ELEV02_TEMP_C_PV",
  "duration": "24h",
  "sensitivity": "medium",
  "statistics": {
    "mean": 72.3,
    "stddev": 4.8
  },
  "anomalies_detected": [
    {
      "timestamp": "2025-11-18T08:15:00Z",
      "value": 95.2,
      "z_score": 4.77,
      "deviation": 31.7
    }
  ],
  "anomaly_count": 1,
  "insight": "Detected 1 anomalies (values beyond 2.5 standard deviations)"
}
```

---

### 5️⃣ **Análise de Desempenho**

#### `calculate_oee`
Calcula Overall Equipment Effectiveness (OEE).

**Fórmula:**
```
OEE = Disponibilidade × Performance × Qualidade
```

**Exemplo de uso:**
```
"Calcule o OEE do elevador 1"
"Qual a eficiência global dos equipamentos?"
```

#### `analyze_alarm_patterns`
Analisa padrões de alarmes (flooding, chattering, frequência).

**Exemplo de uso:**
```
"Analise os padrões de alarmes nas últimas 24 horas"
"Quais alarmes são mais frequentes?"
```

---

### 6️⃣ **Busca e Metadados**

#### `search_tags`
Busca tags por nome ou descrição.

**Exemplo de uso:**
```
"Quais sensores de temperatura estão disponíveis?"
"Procure tags relacionadas a velocidade"
```

#### `get_tag_metadata`
Obtém informações detalhadas sobre uma tag.

**Retorna:**
```json
{
  "tag_id": "ELEV01_TEMP_C_PV",
  "name": "Elevador 01 - Temperatura",
  "description": "Sensor de temperatura do motor do elevador 1",
  "unit": "°C",
  "data_type": "float",
  "min_value": 0,
  "max_value": 150,
  "alarm_high": 80,
  "alarm_critical": 90,
  "category": "Temperature",
  "equipment": "ELEV01"
}
```

#### `get_all_tags`
Lista todas as tags disponíveis no sistema.

#### `get_active_alarms`
Lista alarmes ativos com filtro por severidade.

**Exemplo de uso:**
```
"Quais são os alarmes críticos ativos?"
"Me mostre todos os alarmes de alta prioridade"
```

---

## 🎯 Exemplos Práticos de Capacidades

### ✅ **1. Valores Atuais**
```
Usuário: "Qual o valor atual da temperatura do ELEV01?"
Agente: Executa get_realtime_value("ELEV01_TEMP_C_PV")
        Retorna: 72.5°C
```

### ✅ **2. Média (Operação Matemática)**
```
Usuário: "Qual foi a temperatura média do ELEV01 nas últimas 24 horas?"
Agente: Executa calculate_statistics("ELEV01_TEMP_C_PV", "24h")
        Retorna: Mean = 72.3°C, Max = 85.2°C, Min = 65.1°C
```

### ✅ **3. Comparação (Operação Lógica)**
```
Usuário: "Compare ELEV01 com ELEV02. Qual teve maior temperatura?"
Agente: Executa compare_tags(["ELEV01_TEMP_C_PV", "ELEV02_TEMP_C_PV"])
        Análise: ELEV02 maior (75.1°C vs 72.3°C)
```

### ✅ **4. Detecção Condicional (Lógica)**
```
Usuário: "Me avise se algum equipamento teve temperatura acima de 80°C"
Agente: Executa calculate_statistics para cada equipamento
        Lógica: IF max > 80 THEN alerta
        Retorna: "ELEV01 atingiu 85.2°C às 14:30"
```

### ✅ **5. Análise de Tendência (Matemática + Lógica)**
```
Usuário: "A temperatura está aumentando ou diminuindo?"
Agente: Executa get_historical_data("ELEV01_TEMP_C_PV", "6h")
        Calcula: Regressão linear / comparação temporal
        Retorna: "Tendência de aumento (+2.5°C nas últimas 6h)"
```

### ✅ **6. Detecção de Anomalias (Estatística)**
```
Usuário: "Detecte anomalias na temperatura"
Agente: Executa detect_anomalies("ELEV01_TEMP_C_PV", "24h", "medium")
        Calcula: Z-score para cada ponto
        Retorna: 1 anomalia detectada (95.2°C, z-score=4.77)
```

### ✅ **7. Correlação Multi-Variável (Matemática Avançada)**
```
Usuário: "Existe correlação entre temperatura e corrente elétrica?"
Agente: Executa compare_tags(["ELEV01_TEMP_C_PV", "ELEV01_CURRENT_A_PV"])
        Análise: Coeficiente de variação, comportamento temporal
        Retorna: "Alta correlação: quando temperatura sobe, corrente aumenta"
```

---

## 🚀 Como Ativar o Modo Tool-Calling (LLM Completo)

### **Método 1: Remover Forçamento de Fallback**

Editar `backend/app/api/routes/ai_agent.py` (linha ~641):

**ANTES:**
```python
    # Force fallback mode for now since Ollama takes too long to load
    logger.info("Using fallback chat mode (Ollama disabled)")
    return await chat_fallback_mode(request, data_service, toolkit, db)
```

**DEPOIS:**
```python
    # Try to use Ollama, fallback only if not available
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        logger.info("Ollama available, using tool-calling mode")
        # Continue with tool-calling mode...
    except Exception as e:
        logger.warning(f"Ollama not available, using fallback mode: {e}")
        return await chat_fallback_mode(request, data_service, toolkit, db)
```

### **Método 2: Variável de Ambiente**

Adicionar ao `docker-compose.yml`:
```yaml
backend:
  environment:
    - USE_OLLAMA=true  # ou false para forçar fallback
```

---

## 📋 Comparação: Modo Fallback vs Tool-Calling

| Capacidade | Fallback Mode | Tool-Calling Mode |
|-----------|---------------|-------------------|
| **Análise de Alarmes** | ✅ Especializado | ✅ + LLM |
| **Valores Atuais** | ❌ | ✅ `get_realtime_value` |
| **Estatísticas (média, max, min)** | ❌ | ✅ `calculate_statistics` |
| **Comparações** | ❌ | ✅ `compare_tags` |
| **Detecção de Anomalias** | ❌ | ✅ `detect_anomalies` |
| **Histórico/Tendências** | ❌ | ✅ `get_historical_data` |
| **Correlações** | ❌ | ✅ `compare_tags` |
| **OEE** | ❌ | ✅ `calculate_oee` |
| **Busca de Tags** | ❌ | ✅ `search_tags` |
| **Resposta Especializada PCM/PCO** | ✅ | ✅ |
| **Velocidade** | ⚡ Rápido | 🐢 Mais lento |
| **Precisão Técnica** | ✅ Alta | ✅ Muito Alta |

---

## 💡 Recomendações

### **Para Produção:**
1. **Usar Fallback Mode** se:
   - Velocidade é crítica
   - Apenas consultas de alarmes são necessárias
   - Recursos limitados (RAM/VRAM)

2. **Usar Tool-Calling Mode** se:
   - Análises matemáticas complexas são necessárias
   - Usuários fazem perguntas variadas sobre dados
   - Precisa de detecção de anomalias automática
   - Análise de tendências e correlações é importante

### **Configuração Híbrida:**
```python
# Usar fallback para alarmes, tool-calling para análises
if is_alarm_query(message):
    return await chat_fallback_mode(...)
else:
    return await chat_with_tools(...)
```

---

## 📊 Resumo das Capacidades

### ✅ **SIM - O modelo é capaz de:**

1. ✅ **Trazer valores atuais** das variáveis
   - `get_realtime_value` + `get_multiple_realtime_values`

2. ✅ **Executar operações matemáticas:**
   - Média (mean)
   - Máximo (max)
   - Mínimo (min)
   - Desvio padrão (stddev)
   - Coeficiente de variação
   - Soma (sum)
   - Agregações temporais

3. ✅ **Funções lógicas:**
   - Comparações (>, <, ==)
   - Detecção condicional (IF/THEN)
   - Análise de padrões
   - Correlações
   - Classificação (estável vs variável)
   - Detecção de anomalias (Z-score)

### ⚠️ **MAS - Atualmente desabilitado**
- Modo Tool-Calling está **comentado** no código
- Ollama pronto mas não ativado
- Fácil de reativar (remover 3 linhas de código)

---

## 🔧 Instruções para Ativação Rápida

```bash
# 1. Editar o arquivo
nano backend/app/api/routes/ai_agent.py

# 2. Procurar linha 641:
#    return await chat_fallback_mode(request, data_service, toolkit, db)

# 3. Comentar a linha (adicionar #)
#    # return await chat_fallback_mode(request, data_service, toolkit, db)

# 4. Descomentar código do Ollama (linhas 643-656)

# 5. Reiniciar backend
docker compose restart backend

# 6. Testar
curl -X POST http://localhost:8000/api/v1/agent/dashboard/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Qual foi a temperatura média do ELEV01 nas últimas 24 horas?"}'
```

---

## 📚 Documentação Adicional

- **Arquivo de Ferramentas**: `backend/app/services/agent_tools.py`
- **Rotas da API**: `backend/app/api/routes/ai_agent.py`
- **Modelo LLM**: Qwen2.5:7B (4.7 GB, instalado em `/home/thiestacio/.ollama`)
- **Container**: `optiflow-ollama` (porta 11434/11435)

---

**Data de criação**: 18 de novembro de 2025  
**Versão**: 1.0  
**Status do Sistema**: ✅ Totalmente funcional, modo tool-calling pronto para ativação
