# 🧪 Asset Framework - Guia de Validação e Testes

**Branch**: `claude/fix-autonomous-agent-sessions-011CUm8WUduocmLfq3bJpCxf`
**Data**: November 3, 2025
**Status**: Pronto para validação

---

## 📋 Checklist de Validação

### ✅ FASE 1: Setup e Configuração

#### 1.1 Database Migration
```bash
cd backend

# Verificar migrations pendentes
alembic current

# Executar migration
alembic upgrade head

# Verificar se tabelas foram criadas
# Deve mostrar: assets, asset_attributes, asset_templates
```

**Resultado esperado**:
- ✅ Migration executada sem erros
- ✅ 3 novas tabelas criadas (assets, asset_attributes, asset_templates)
- ✅ Enums criados (assettype, asset_attribute_type)

#### 1.2 Seed Dados de Exemplo
```bash
cd backend
python scripts/seed_assets.py
```

**Resultado esperado**:
```
🌱 Starting Asset Framework seed...
✅ Asset Framework seed completed successfully!

📊 Summary:
   - 1 Enterprise
   - 1 Site
   - 2 Areas
   - 4 Equipment
   - 4 Components
   - 5 Attributes

   Total Assets: 12 assets
```

---

### ✅ FASE 2: Backend API Testing

#### 2.1 Testar Asset Endpoints

**GET /api/v1/assets/** - List all assets
```bash
curl http://localhost:8000/api/v1/assets/ | jq
```
**Esperado**: Lista de 12 assets

**GET /api/v1/assets/tree** - Get asset tree
```bash
curl http://localhost:8000/api/v1/assets/tree | jq
```
**Esperado**: Estrutura hierárquica com Terminal → Planta → Áreas → Equipment

**POST /api/v1/assets/** - Create asset
```bash
curl -X POST http://localhost:8000/api/v1/assets/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Silo 03 Teste",
    "description": "Silo de teste",
    "asset_type": "equipment",
    "parent_id": null
  }'
```
**Esperado**: Asset criado com ID retornado

**GET /api/v1/assets/{id}** - Get specific asset
```bash
curl http://localhost:8000/api/v1/assets/{asset_id} | jq
```
**Esperado**: Detalhes do asset incluindo full_path, level, children_count

**PUT /api/v1/assets/{id}** - Update asset
```bash
curl -X PUT http://localhost:8000/api/v1/assets/{asset_id} \
  -H "Content-Type: application/json" \
  -d '{"name": "Silo 03 Atualizado"}'
```
**Esperado**: Asset atualizado

**DELETE /api/v1/assets/{id}** - Delete asset
```bash
curl -X DELETE http://localhost:8000/api/v1/assets/{asset_id}
```
**Esperado**: Asset deletado (204 No Content)

#### 2.2 Testar Attribute Endpoints

**GET /api/v1/assets/{id}/attributes** - List attributes
```bash
curl http://localhost:8000/api/v1/assets/{asset_id}/attributes | jq
```
**Esperado**: Lista de attributes do asset

**POST /api/v1/assets/{id}/attributes** - Create attribute
```bash
curl -X POST http://localhost:8000/api/v1/assets/{asset_id}/attributes \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "{asset_id}",
    "name": "Teste Atributo",
    "attribute_type": "static",
    "static_value": "100",
    "unit": "kg",
    "display_order": 0,
    "settings": {}
  }'
```
**Esperado**: Attribute criado

#### 2.3 Testar Calculated Attributes

**POST /api/v1/assets/evaluate-formula** - Test formula
```bash
curl -X POST "http://localhost:8000/api/v1/assets/evaluate-formula?formula=2%20%2B%202&asset_id={asset_id}"
```
**Esperado**: `{"formula": "2 + 2", "result": 4.0, "success": true}`

**Fórmula com tag()** (substituir TAG_NAME por tag real):
```bash
curl -X POST "http://localhost:8000/api/v1/assets/evaluate-formula?formula=tag('CORREIA_01_VELOCIDADE')%20*%202&asset_id={asset_id}"
```
**Esperado**: Valor calculado baseado no tag

**GET /api/v1/assets/{id}/calculate-all** - Calculate all attributes
```bash
curl http://localhost:8000/api/v1/assets/{asset_id}/calculate-all | jq
```
**Esperado**: Todos calculated attributes avaliados

#### 2.4 Testar Health Score

**GET /api/v1/assets/{id}/health** - Get asset health
```bash
curl http://localhost:8000/api/v1/assets/{asset_id}/health | jq
```
**Esperado**:
```json
{
  "asset_id": "...",
  "asset_name": "Correia 01",
  "health_score": 85.5,
  "status": "good",
  "attributes_count": 3,
  "issues_count": 0,
  "warnings_count": 1,
  "warnings": ["..."]
}
```

**GET /api/v1/assets/{id}/health/hierarchy** - Get hierarchy health
```bash
curl http://localhost:8000/api/v1/assets/{asset_id}/health/hierarchy | jq
```
**Esperado**: Health score + children health

**GET /api/v1/assets/health/overview** - Health overview
```bash
curl http://localhost:8000/api/v1/assets/health/overview | jq
```
**Esperado**: Overview de todos assets com estatísticas

---

### ✅ FASE 3: Frontend Testing

#### 3.1 Iniciar Aplicação
```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**Acessar**: http://localhost:5173

#### 3.2 Dashboard Builder - Asset Tree Panel

1. **Navegar para Dashboard Builder**
   - Ir para `/dashboard-builder`
   - ✅ Página carrega sem erros

2. **Alternar para modo Assets**
   - Clicar no botão "Tags/Assets" toggle
   - ✅ Painel muda de Tags para Assets
   - ✅ Árvore de assets aparece

3. **Visualizar Árvore**
   - ✅ Ver "Terminal Portuário" como raiz
   - ✅ Expandir para ver "Planta de Grãos"
   - ✅ Expandir áreas e ver equipamentos
   - ✅ Ícones corretos por tipo (Building, MapPin, Boxes, etc)
   - ✅ Badges mostrando children_count e attributes_count

4. **Busca e Filtros**
   - Buscar "Correia"
   - ✅ Árvore filtra mostrando apenas Correia 01
   - Filtrar por tipo "equipment"
   - ✅ Mostra apenas equipamentos
   - Toggle "Show Inactive"
   - ✅ Mostra/oculta assets inativos

5. **Seleção de Asset**
   - Clicar em "Correia 01"
   - ✅ Asset fica destacado (borda azul)
   - ✅ Painel inferior mostra detalhes
   - ✅ Lista de attributes aparece
   - ✅ Full path exibido

#### 3.3 CRUD de Assets via Modal

1. **Criar Asset**
   - Clicar no botão "+" no header
   - ✅ Modal "Criar Novo Asset" abre
   - Preencher:
     - Nome: "Correia 03 Teste"
     - Tipo: Equipment
     - Parent: Área de Recepção
     - Metadata: capacidade = "200 ton/h"
   - Clicar "Criar Asset"
   - ✅ Toast de sucesso aparece
   - ✅ Árvore atualiza automaticamente
   - ✅ Novo asset aparece na hierarquia

2. **Editar Asset**
   - Clicar no botão de editar (✏️) em um asset
   - ✅ Modal "Editar Asset" abre com dados preenchidos
   - Alterar nome
   - Clicar "Salvar Alterações"
   - ✅ Asset atualizado na árvore

3. **Deletar Asset**
   - Clicar no botão deletar (🗑️)
   - ✅ Confirmação aparece
   - Confirmar
   - ✅ Asset removido da árvore
   - ✅ Children também removidos (cascade)

#### 3.4 CRUD de Attributes via Modal

1. **Criar Attribute - Tag Reference**
   - Selecionar um asset
   - Clicar "+" na seção de atributos
   - ✅ Modal "Criar Novo Atributo" abre
   - Escolher tipo: "Referência a Tag"
   - Selecionar um tag
   - Configurar thresholds
   - Salvar
   - ✅ Attribute aparece na lista

2. **Criar Attribute - Static**
   - Tipo: "Valor Estático"
   - Valor: "1200"
   - Unit: "RPM"
   - Salvar
   - ✅ Attribute criado

3. **Criar Attribute - Calculated**
   - Tipo: "Calculado"
   - Fórmula: `tag('CORREIA_01_VELOCIDADE') * 100`
   - Salvar
   - ✅ Attribute criado
   - ✅ Fórmula validada

#### 3.5 Drag & Drop

1. **Arrastar Asset para Widget**
   - Criar um widget Gauge no canvas
   - Arrastar "Correia 01" da árvore
   - Soltar no widget
   - ✅ Widget vinculado ao asset
   - ✅ Dados aparecem no widget

---

### ✅ FASE 4: Casos de Uso Completos

#### Caso 1: Monitorar Correia Transportadora

**Objetivo**: Criar asset completo com attributes e monitoring

1. Criar asset "Correia 02"
2. Adicionar attributes:
   - Velocidade (tag_reference → CORREIA_02_VELOCIDADE)
   - Velocidade Nominal (static → 2.0 m/s)
   - Eficiência (calculated → `tag('CORREIA_02_VELOCIDADE') / attr('Velocidade Nominal') * 100`)
3. Configurar thresholds:
   - Warning: velocidade > 2.2 m/s
   - Critical: velocidade > 2.4 m/s
4. Ver health score
5. ✅ Health score reflete thresholds

#### Caso 2: Hierarquia Completa

**Objetivo**: Criar nova área com equipamentos

1. Criar "Área de Expedição" (parent: Planta)
2. Criar "Correia 04" (parent: Área de Expedição)
3. Criar "Motor 04" (parent: Correia 04, type: component)
4. Adicionar attributes em cada nível
5. Ver health hierarchy
6. ✅ Health rollup funciona

#### Caso 3: Fórmulas Complexas

**Objetivo**: Testar calculated attributes avançados

Fórmulas para testar:
```python
# Potência
"tag('VOLTAGE') * tag('CURRENT')"

# Média de 3 sensores
"(tag('TEMP_1') + tag('TEMP_2') + tag('TEMP_3')) / 3"

# Eficiência OEE
"(attr('Availability') * attr('Performance') * attr('Quality')) / 100"

# Distância
"sqrt(pow(tag('X'), 2) + pow(tag('Y'), 2))"

# Conditional
"max(0, tag('FLOW') - attr('Min Flow'))"
```

---

## 🐛 Bugs Conhecidos e Limitações

### Bugs para Verificar:

1. **Modal de Asset**:
   - [ ] Validação de circular reference ao mudar parent?
   - [ ] Metadata aceita caracteres especiais?

2. **Calculated Attributes**:
   - [ ] Circular reference detection funciona?
   - [ ] Error messages claros para fórmulas inválidas?

3. **Health Score**:
   - [ ] Performance com 100+ assets?
   - [ ] Cache de cálculos?

### Limitações Conhecidas:

1. **Calculated Attributes**:
   - Não suporta funções temporais (avg últimos 5min)
   - Não suporta comparações com histórico
   - Sem validação de sintaxe em tempo real

2. **Health Score**:
   - Não considera tendências históricas
   - Não há pesos diferentes por attribute
   - Sem ML para predição

3. **UI**:
   - Sem edição de attributes (apenas create)
   - Sem bulk operations
   - Sem undo/redo

---

## 📊 Métricas de Performance

### Targets:

- **Asset Tree Load**: < 500ms (até 100 assets)
- **Health Calculation**: < 1s por asset
- **Formula Evaluation**: < 100ms
- **Modal Open**: < 50ms

### Como Medir:

```javascript
// No browser console
console.time('Asset Tree Load');
// ... fetch asset tree ...
console.timeEnd('Asset Tree Load');
```

---

## ✅ Critérios de Aceitação

### Mínimo para Produção:

- [ ] Migration executa sem erros
- [ ] Seed cria 12 assets corretamente
- [ ] CRUD de assets funciona via UI
- [ ] CRUD de attributes funciona via UI
- [ ] Calculated attributes avaliam corretamente
- [ ] Health score calcula sem erros
- [ ] Drag & drop funciona
- [ ] Busca e filtros funcionam
- [ ] Sem erros no console do browser
- [ ] Sem erros nos logs do backend

### Ideal para Produção:

- [ ] Performance dentro dos targets
- [ ] Todos casos de uso completos funcionam
- [ ] Error handling gracioso
- [ ] Loading states apropriados
- [ ] Feedback visual claro
- [ ] Documentação atualizada

---

## 🎯 Próximos Passos Após Validação

Se todos testes passarem:
1. ✅ Partir para Frontend Health Score (Widgets)
2. ✅ Integrar com Autonomous Agent
3. ✅ Criar templates pré-definidos
4. ✅ Implementar import/export

Se houver problemas:
1. 🐛 Documentar bugs encontrados
2. 🔧 Priorizar e corrigir
3. ♻️ Re-testar
4. ✅ Continuar quando estável

---

## 📝 Relatório de Validação

**Data**: ___________
**Testador**: ___________
**Branch**: `claude/fix-autonomous-agent-sessions-011CUm8WUduocmLfq3bJpCxf`

### Resultados:

- [ ] PASS - Todos testes passaram
- [ ] PASS WITH ISSUES - Testes passaram mas com problemas menores
- [ ] FAIL - Problemas críticos encontrados

### Bugs Encontrados:

1. ___________
2. ___________
3. ___________

### Observações:

___________

---

**🎉 Boa sorte com os testes! Se tudo passar, podemos seguir para as próximas fases!**
