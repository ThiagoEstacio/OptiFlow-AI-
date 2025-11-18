# 🔧 Melhorias Necessárias no OptiFlow AI Agent

**Data de Análise**: 18 de novembro de 2025  
**Status Atual**: ✅ Funcional | ⚠️ Precisa Melhorias

---

## 🎯 Resumo Executivo

O agente está **funcionando** mas possui **limitações críticas** que impedem uso completo:

### ❌ **Problemas Identificados:**
1. **Dados históricos inexistentes** (InfluxDB vazio)
2. **Fallback muito agressivo** (captura queries que deviam ir pro Qwen)
3. **Tags não mapeadas** (nomes incorretos)
4. **Ferramentas sem dados** (retornam vazio)
5. **Falta integração com dados reais** do simulador

### ✅ **O Que Funciona:**
- Qwen 2.5:7B instalado e operacional
- Tool-calling implementado
- Sistema híbrido funcional
- Respostas em português
- Análise de alarmes (usa PostgreSQL)

---

## 📊 Problemas Detalhados e Soluções

### **1. InfluxDB Vazio - Sem Dados Históricos** 🔴 CRÍTICO

#### Problema:
```bash
Teste: "Temperatura média nas últimas 24h"
Resultado: "Não há dados disponíveis"
Causa: InfluxDB não está sendo populado com dados do simulador
```

#### Impacto:
- ❌ `calculate_statistics` retorna vazio
- ❌ `get_historical_data` sem dados
- ❌ `detect_anomalies` não funciona
- ❌ `compare_tags` impossível
- ❌ 80% das capacidades matemáticas inutilizáveis

#### Solução:
```python
# 1. Verificar se gateway está enviando dados para InfluxDB
# Arquivo: gateway/app/services/data_writer.py

# 2. Popular InfluxDB com dados históricos
python scripts/populate_influxdb_historical.py --days 30

# 3. Verificar se simulador está rodando
docker compose ps opcua-simulator

# 4. Testar escrita manual
curl -X POST http://localhost:8000/api/v1/timeseries/write \
  -d '{
    "tag_id": "ELEV01_TEMP_C_PV",
    "value": 75.5,
    "timestamp": "2025-11-18T10:00:00Z"
  }'
```

**Prioridade**: 🔴 **ALTA** (sem isso, 80% das ferramentas não funcionam)

---

### **2. Fallback Muito Agressivo** 🟠 MÉDIO

#### Problema:
```python
Pergunta: "Quais tags de temperatura estão disponíveis?"
Esperado: Qwen chama search_tags("temperatura")
Atual: Fallback retorna mensagem genérica
```

#### Causa:
```python
# backend/app/api/routes/ai_agent.py (linha ~690)
simple_keywords = ['alarme', 'dispositivo', 'olá', 'tag', 'dados', 'sensor']
# 'tag' está na lista de fallback!
```

#### Impacto:
- ❌ Queries sobre tags caem no fallback
- ❌ Buscas e descoberta de dados não funcionam
- ❌ Qwen não é usado quando deveria

#### Solução:
```python
# Refinar classificação híbrida
simple_keywords = [
    'alarme', 'alarm', 'crítico', 'urgente',  # Apenas alarmes
    'olá', 'oi', 'hello', 'ajuda'              # Apenas saudações
]

# Adicionar categoria "discovery" que sempre usa Qwen
discovery_keywords = [
    'quais', 'qual', 'liste', 'mostre', 'busque', 'procure',
    'disponível', 'available', 'tags', 'sensores'
]

if any(word in message_lower for word in discovery_keywords):
    use_qwen = True
    use_fallback = False
```

**Prioridade**: 🟠 **MÉDIA** (afeta descoberta de dados)

---

### **3. Tags Não Mapeadas Corretamente** 🟡 BAIXO

#### Problema:
```python
Usuário: "Temperatura do ELEV01"
Qwen busca: "ELEV01_TEMP" ou "temp_ELEV01"
Real no sistema: "ELEV01_TEMP_C_PV"
```

#### Impacto:
- ❌ Buscas falham por nome incorreto
- ❌ Usuário precisa saber nome exato da tag
- ❌ Experiência ruim (deveria ser intuitivo)

#### Solução:
```python
# 1. Criar ferramenta de busca inteligente
@tool
async def smart_tag_search(equipment: str, parameter: str) -> List[str]:
    """
    Busca inteligente de tags por equipamento e parâmetro.
    
    Exemplo:
        equipment="ELEV01", parameter="temperatura"
        → Retorna: ["ELEV01_TEMP_C_PV", "ELEV01_TEMP_ALARM"]
    """
    # Busca fuzzy no banco
    query = f"%{equipment}%{parameter}%"
    tags = await db.query(Tag).filter(Tag.name.ilike(query)).all()
    return [tag.name for tag in tags]

# 2. Adicionar aliases/sinônimos
TAG_ALIASES = {
    "temperatura": ["TEMP", "TEMPERATURE"],
    "pressão": ["PRESS", "PRESSURE"],
    "velocidade": ["VEL", "SPEED", "RPM"],
    "corrente": ["CURRENT", "AMP"],
}

# 3. Melhorar search_tags com fuzzy matching
from fuzzywuzzy import fuzz
```

**Prioridade**: 🟡 **BAIXA** (workaround: usuário usa nome exato)

---

### **4. Falta de Contexto do Processo** 🟠 MÉDIO

#### Problema:
```python
Usuário: "Qual a eficiência do elevador 1?"
Qwen: Não sabe que equipamentos existem ou como calcular
```

#### Impacto:
- ❌ Perguntas amplas não funcionam
- ❌ Falta conhecimento do processo industrial
- ❌ Não sugere análises proativas

#### Solução:
```python
# 1. Adicionar ferramenta get_equipment_list
@tool
async def get_equipment_list(category: str = None) -> Dict[str, Any]:
    """
    Lista equipamentos disponíveis no sistema.
    
    Retorna:
        {
            "elevators": ["ELEV01", "ELEV02"],
            "silos": ["SILO01", "SILO02"],
            "conveyors": ["ARZ_CORR01", "ARZ_CORR02"],
            "total": 6
        }
    """

# 2. Adicionar contexto industrial ao system prompt
PROCESS_CONTEXT = """
## Equipamentos Disponíveis no Sistema:
- **Elevadores** (ELEV01, ELEV02): Transporte vertical de material
  - Tags principais: TEMP_C_PV, CURRENT_A_PV, SPEED_RPM
  - Alarmes críticos: Alta temperatura (>80°C), Sobrecorrente (>50A)
  
- **Silos** (SILO01, SILO02): Armazenamento de material
  - Tags principais: LEVEL_PCT, TEMP_C_PV, PRESSURE_BAR
  - Alarmes críticos: Nível alto (>95%), Nível baixo (<10%)
  
- **Correias** (ARZ_CORR01, ARZ_CORR02): Transporte horizontal
  - Tags principais: VELOCIDADE_PV, TEMPERATURA_PV
  - Alarmes: Parada, Baixa velocidade

## Processo Industrial:
Material → Correia → Elevador → Silo → Expedição
"""

# 3. Adicionar ferramenta de relacionamento
@tool
async def get_equipment_relationships(equipment_id: str) -> Dict:
    """Retorna equipamentos relacionados (upstream/downstream)"""
    return {
        "ELEV01": {
            "upstream": ["ARZ_CORR01"],
            "downstream": ["SILO01"],
            "affects": ["SILO01_LEVEL", "PRODUCTION_RATE"]
        }
    }
```

**Prioridade**: 🟠 **MÉDIA** (melhora muito UX)

---

### **5. Ferramentas Sem Validação de Dados** 🟡 BAIXO

#### Problema:
```python
calculate_statistics("tag_inexistente", "24h")
→ Retorna: {"mean": null, "max": null}
→ Qwen recebe dados vazios e não sabe interpretar
```

#### Impacto:
- ⚠️ Respostas confusas
- ⚠️ Falta tratamento de erro

#### Solução:
```python
# backend/app/services/agent_tools.py

async def _calculate_statistics(self, tag_id: str, duration: str = "1h"):
    """Calculate statistics with proper error handling"""
    
    # 1. Validar se tag existe
    tag = await self.data_service.get_tag_by_id(tag_id)
    if not tag:
        return {
            "error": f"Tag '{tag_id}' não encontrada no sistema",
            "suggestion": "Use search_tags() para encontrar tags disponíveis"
        }
    
    # 2. Buscar dados
    data = await self.data_service.calculate_statistics(tag_id, duration)
    
    # 3. Validar se há dados suficientes
    if not data or data.get("count", 0) < 10:
        return {
            "error": f"Dados insuficientes para '{tag_id}' no período {duration}",
            "available_count": data.get("count", 0),
            "required_count": 10,
            "suggestion": "Tente um período maior (7d, 30d)"
        }
    
    return data
```

**Prioridade**: 🟡 **BAIXA** (melhora mensagens de erro)

---

### **6. Falta de Memória de Conversação** 🔵 FUTURO

#### Problema:
```
Usuário: "Qual a temperatura do ELEV01?"
Agent: "75.2°C"
Usuário: "E nas últimas 24 horas?" ← Contexto perdido
Agent: Não sabe que se refere a ELEV01
```

#### Impacto:
- ⚠️ Conversas não fluem naturalmente
- ⚠️ Usuário precisa repetir contexto

#### Solução:
```python
# Adicionar session management
class ConversationSession:
    def __init__(self):
        self.messages: List[Dict] = []
        self.context: Dict = {
            "last_equipment": None,
            "last_tag": None,
            "last_timeframe": None
        }
    
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        self._extract_context(content)
    
    def _extract_context(self, message: str):
        # Extrair equipamento, tag, período da mensagem
        if "ELEV01" in message:
            self.context["last_equipment"] = "ELEV01"
        
        if match := re.search(r'(\d+)h', message):
            self.context["last_timeframe"] = f"{match.group(1)}h"
```

**Prioridade**: 🔵 **BAIXA** (nice to have)

---

### **7. Performance do Qwen** 🟡 BAIXO

#### Problema:
```
Tempo de resposta Qwen: 3-5 segundos
Tempo de resposta Fallback: 50ms
Diferença: 60-100x mais lento
```

#### Impacto:
- ⚠️ UX pode ser impactado em análises complexas
- ⚠️ Usuários podem achar lento

#### Solução:
```python
# 1. Reduzir num_predict para respostas mais curtas
"num_predict": 500  # Ao invés de 800

# 2. Implementar streaming
async def call_ollama_streaming(messages):
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{OLLAMA_BASE_URL}/api/chat",
            json={"model": MODEL_NAME, "messages": messages, "stream": True}
        ) as response:
            async for line in response.aiter_lines():
                chunk = json.loads(line)
                yield chunk["message"]["content"]

# 3. Adicionar indicador de carregamento
response.suggestions = ["⏳ Analisando dados..."]

# 4. Cache de respostas comuns
from functools import lru_cache
@lru_cache(maxsize=100)
def get_cached_response(message_hash):
    ...
```

**Prioridade**: 🟡 **BAIXA** (3-5s é aceitável para análise complexa)

---

### **8. Falta de Ferramentas Industriais Específicas** 🟠 MÉDIO

#### Problema:
Ferramentas genéricas não cobrem casos de uso industriais específicos.

#### Ferramentas Faltando:

```python
# 1. Análise de Vibração
@tool
async def analyze_vibration(equipment_id: str, duration: str = "24h"):
    """
    Analisa espectro de vibração para diagnóstico de falhas.
    Detecta: desbalanceamento, desalinhamento, rolamentos
    """

# 2. Análise de Energia
@tool
async def analyze_energy_consumption(equipment_id: str, shift: str = "current"):
    """
    Analisa consumo energético por turno.
    Calcula: kWh total, pico de demanda, fator de potência
    """

# 3. Predição de Falhas
@tool
async def predict_failure(equipment_id: str, model: str = "random_forest"):
    """
    Usa ML para prever probabilidade de falha nas próximas 48h.
    Retorna: probability, confidence, contributing_factors
    """

# 4. Comparação de Turnos
@tool
async def compare_shifts(date: str, metric: str = "oee"):
    """
    Compara performance entre turnos (manhã, tarde, noite).
    Métricas: OEE, disponibilidade, qualidade, performance
    """

# 5. Root Cause Analysis
@tool
async def root_cause_analysis(alarm_id: int):
    """
    Analisa causas raiz de um alarme usando dados históricos.
    Correlaciona: eventos anteriores, mudanças de processo
    """

# 6. Análise de Batelada
@tool
async def analyze_batch(batch_id: str):
    """
    Analisa performance de uma batelada específica.
    Compara com: média histórica, especificações, melhor batelada
    ```

**Prioridade**: 🟠 **MÉDIA** (aumenta valor agregado)

---

### **9. Falta de Integração com ML Models** 🔵 FUTURO

#### Problema:
```
Sistema tem modelos ML treinados mas agente não usa.
```

#### Solução:
```python
# Integrar com modelos existentes
@tool
async def get_ml_predictions(equipment_id: str):
    """Obter predições dos modelos ML ativos"""
    predictions = await ml_service.get_active_predictions(equipment_id)
    return {
        "anomaly_score": predictions.anomaly_score,
        "failure_probability": predictions.failure_prob,
        "remaining_useful_life": predictions.rul_hours
    }
```

**Prioridade**: 🔵 **BAIXA** (ML já existe, só falta conectar)

---

## 🎯 Plano de Ação Priorizado

### **🔴 PRIORIDADE ALTA** (Fazer AGORA)

1. **Popular InfluxDB com dados históricos**
   ```bash
   # Criar script de população
   python scripts/populate_influxdb_historical.py --days 30
   
   # Verificar se gateway está escrevendo dados
   docker compose logs gateway | grep "InfluxDB"
   
   # Testar escrita manual
   curl -X POST http://localhost:8000/api/v1/timeseries/write
   ```
   **Resultado**: 80% das ferramentas passam a funcionar

2. **Refinar classificação híbrida (fallback vs Qwen)**
   ```python
   # Remover 'tag', 'dados', 'sensor' de simple_keywords
   # Adicionar categoria 'discovery' que sempre usa Qwen
   ```
   **Resultado**: Qwen usado corretamente

### **🟠 PRIORIDADE MÉDIA** (Próxima Sprint)

3. **Adicionar contexto do processo industrial**
   ```python
   # Documentar equipamentos no system prompt
   # Criar ferramenta get_equipment_list()
   # Adicionar mapeamento de relacionamentos
   ```
   **Resultado**: Agente entende processo

4. **Criar ferramentas industriais específicas**
   ```python
   # analyze_vibration()
   # analyze_energy_consumption()
   # compare_shifts()
   ```
   **Resultado**: Valor agregado para PCM/PCO

5. **Melhorar validação de dados**
   ```python
   # Verificar se tag existe antes de buscar
   # Retornar erros descritivos
   # Sugerir alternativas
   ```
   **Resultado**: Mensagens de erro melhores

### **🟡 PRIORIDADE BAIXA** (Backlog)

6. **Implementar busca inteligente de tags**
   ```python
   # Fuzzy matching
   # Aliases/sinônimos
   # smart_tag_search()
   ```

7. **Otimizar performance do Qwen**
   ```python
   # Streaming
   # Cache de respostas
   # Reduzir num_predict
   ```

### **🔵 FUTURO** (Roadmap)

8. **Adicionar memória de conversação**
   ```python
   # Session management
   # Context tracking
   # Multi-turn dialogue
   ```

9. **Integrar com modelos ML**
   ```python
   # Conectar predições existentes
   # Usar anomaly detection
   # RUL (Remaining Useful Life)
   ```

---

## 📈 Métricas de Sucesso

### **Antes das Melhorias:**
- ❌ 80% das ferramentas sem dados
- ❌ Qwen capturado por fallback
- ⚠️ Tags difíceis de encontrar
- ⚠️ Falta contexto industrial

### **Depois das Melhorias (Esperado):**
- ✅ 100% das ferramentas funcionais
- ✅ Qwen usado quando apropriado
- ✅ Busca inteligente de tags
- ✅ Contexto industrial completo
- ✅ Ferramentas PCM/PCO específicas

---

## 🔧 Scripts de Implementação

### **Script 1: Popular InfluxDB**
```bash
#!/bin/bash
# scripts/populate_influxdb_quick.sh

# 1. Verificar se InfluxDB está rodando
docker compose ps influxdb

# 2. Popular últimos 30 dias
python scripts/populate_influxdb_historical.py \
  --start-date "2025-10-19" \
  --end-date "2025-11-18" \
  --interval 60  # 1 ponto por minuto

# 3. Verificar dados
curl -X POST http://localhost:8086/api/v2/query \
  -H "Authorization: Token $INFLUX_TOKEN" \
  -d '{
    "query": "from(bucket: \"optiflow\") |> range(start: -24h) |> count()"
  }'
```

### **Script 2: Testar Todas as Ferramentas**
```python
# scripts/test_all_agent_tools.py

async def test_all_tools():
    """Testa todas as 12 ferramentas do agente"""
    
    tests = [
        ("get_realtime_value", {"tag_id": "ELEV01_TEMP_C_PV"}),
        ("calculate_statistics", {"tag_id": "ELEV01_TEMP_C_PV", "duration": "24h"}),
        ("search_tags", {"query": "temperatura"}),
        ("get_active_alarms", {}),
        # ... outras ferramentas
    ]
    
    results = {}
    for tool_name, args in tests:
        result = await toolkit.execute_tool(tool_name, args)
        results[tool_name] = {
            "success": result.success,
            "has_data": bool(result.data),
            "error": result.error
        }
    
    print(json.dumps(results, indent=2))
```

---

## 📚 Documentação a Criar

1. **Guia de Tags** (`docs/TAG_NAMING_CONVENTION.md`)
   - Convenção de nomes
   - Mapeamento equipamento → tags
   - Aliases e sinônimos

2. **Guia de Ferramentas** (`docs/AGENT_TOOLS_GUIDE.md`)
   - Descrição detalhada de cada ferramenta
   - Exemplos de uso
   - Limitações conhecidas

3. **Guia do Processo Industrial** (`docs/INDUSTRIAL_PROCESS.md`)
   - Fluxograma do processo
   - Equipamentos e função
   - Relacionamentos

---

## 🎊 Conclusão

### **Estado Atual:**
✅ **Fundação sólida** - Qwen funcional, sistema híbrido implementado  
⚠️ **Falta dados** - InfluxDB vazio limita 80% das capacidades  
⚠️ **Falta contexto** - Agente não conhece processo industrial  

### **Próximos Passos:**
1. 🔴 Popular InfluxDB (1-2 horas)
2. 🔴 Refinar classificação híbrida (30 min)
3. 🟠 Adicionar contexto industrial (2 horas)
4. 🟠 Criar ferramentas específicas PCM/PCO (1 dia)

### **ROI Esperado:**
- **Curto prazo** (1 dia): Agente 100% funcional com dados reais
- **Médio prazo** (1 semana): Ferramentas industriais específicas
- **Longo prazo** (1 mês): Sistema completo com ML integrado

**O agente está 70% pronto. Com as melhorias priorizadas, chegará a 100%!** 🚀
