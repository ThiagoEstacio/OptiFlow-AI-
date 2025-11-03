# 🏭 Asset Framework - Análise de Lacunas (Gap Analysis)

**Comparação**: OptiFlow AI Dashboard Builder vs PI Vision Asset Framework
**Data**: 03 de Novembro de 2025
**Objetivo**: Identificar o que falta para atingir paridade com PI AF

---

## 📊 Status Atual vs PI Vision Asset Framework

### ✅ **O que JÁ TEMOS**

| Feature | Status | Implementação Atual |
|---------|--------|---------------------|
| Tags individuais | ✅ | `Tag` model com metadata completa |
| Drag & drop | ✅ | React DnD implementado |
| Categorias de tags | ✅ | Enum `TagCategory` (8 categorias) |
| Busca de tags | ✅ | Search box + filtro por categoria |
| Metadata de tags | ✅ | name, description, unit, limits |
| Device association | ✅ | `device_id` foreign key |
| Data types | ✅ | Boolean, Integer, Float, String, Double |

---

## ❌ **O que FALTA - Asset Framework Features**

### 1. **Hierarquia de Ativos (Asset Hierarchy)** 🔴 CRÍTICO

**PI Vision tem**:
```
Enterprise (Empresa)
└── Site (Planta)
    └── Area (Área de Processo)
        └── Unit (Unidade)
            └── Equipment (Equipamento)
                └── SubEquipment (Sub-equipamento)
                    └── Attributes (Atributos/Tags)
```

**Nós temos**:
```
Device (Dispositivo)
└── Tags (Tags planas, sem hierarquia)
```

**O que falta**:
- ❌ Modelo de Asset hierárquico
- ❌ Navegação em árvore (tree view)
- ❌ Drill-down entre níveis
- ❌ Parent-child relationships
- ❌ Breadcrumb navigation
- ❌ Expansão/colapso de níveis

---

### 2. **Templates de Ativos (Asset Templates)** 🔴 CRÍTICO

**PI Vision tem**:
```python
# Template: Pump (Bomba)
- Attributes:
  - Flow (vazão)
  - Pressure (pressão)
  - Temperature (temperatura)
  - Status (status)
  - Power (potência)
- Analyses:
  - Efficiency calculation
  - MTBF tracking
- Event Frames:
  - Startup event
  - Shutdown event
```

**Nós temos**:
- ❌ Sem templates reutilizáveis
- ❌ Sem herança de propriedades
- ❌ Sem análises vinculadas a templates
- ❌ Sem event frames

**O que falta**:
- ❌ `AssetTemplate` model
- ❌ Template library/catalog
- ❌ Instanciação de templates
- ❌ Attribute propagation
- ❌ Template inheritance

---

### 3. **Atributos de Ativos vs Tags Diretas** 🟡 IMPORTANTE

**PI Vision tem**:
```
Asset: Motor_01
├── Attribute: Speed (referencia → Tag: MOTOR_01_SPEED)
├── Attribute: Current (referencia → Tag: MOTOR_01_CURRENT)
├── Attribute: Temperature (referencia → Tag: MOTOR_01_TEMP)
└── Attribute: Efficiency (calculado → Formula: Power/Design_Power*100)
```

**Nós temos**:
- Tags diretas sem camada de abstração
- Sem atributos calculados
- Sem fórmulas

**O que falta**:
- ❌ `AssetAttribute` model
- ❌ Attribute → Tag reference mapping
- ❌ Calculated attributes (formulas)
- ❌ Static attributes (metadados)
- ❌ Unit of measure conversions

---

### 4. **Contexto de Navegação (Asset Context)** 🟡 IMPORTANTE

**PI Vision tem**:
```
Usuário seleciona: Enterprise > Planta A > Área de Moagem > Moinho 1

Dashboard se adapta automaticamente:
- Widgets mostram dados do Moinho 1
- Análises aplicadas ao Moinho 1
- Alarmes filtrados por Moinho 1
- Tendências específicas do Moinho 1
```

**Nós temos**:
- Dashboard estático
- Sem contexto de ativos
- Tags fixas por widget

**O que falta**:
- ❌ Asset context selector
- ❌ Context propagation aos widgets
- ❌ Dynamic tag binding baseado em contexto
- ❌ Context-aware filtering
- ❌ Multi-asset comparison

---

### 5. **Análises Baseadas em Templates (Analyses)** 🟡 IMPORTANTE

**PI Vision tem**:
```python
# Análise: Pump Efficiency
Template: Pump
Formula: (Flow * Pressure) / (Power * Constant) * 100
Trigger: On data change
Output: Efficiency (%)

# Aplicado automaticamente a todas as bombas
```

**Nós temos**:
- Cálculos ad-hoc via AI Assistant
- Sem análises reutilizáveis
- Sem event-driven calculations

**O que falta**:
- ❌ `Analysis` model
- ❌ Formula engine
- ❌ Scheduled analyses
- ❌ Event-triggered analyses
- ❌ Analysis library

---

### 6. **Event Frames** 🟠 MODERADO

**PI Vision tem**:
```python
# Event Frame: Batch Production Run
Start condition: Status == "Running"
End condition: Status == "Stopped"
Captures:
- Start time
- End time
- Duration
- Attributes (temperatura média, vazão total, etc)
- Quality metrics
```

**Nós temos**:
- Sem conceito de Event Frames
- Histórico contínuo apenas

**O que falta**:
- ❌ `EventFrame` model
- ❌ Start/end condition detection
- ❌ Attribute capture during event
- ❌ Event frame search/filtering
- ❌ Batch genealogy

---

### 7. **Notificações Baseadas em Ativos (Notifications)** 🟠 MODERADO

**PI Vision tem**:
```python
# Notification Rule
Asset: All Pumps (template-based)
Condition: Temperature > High_Limit
Action:
  - Send email
  - Create work order
  - Log to database
Subscribers: Maintenance team
```

**Nós temos**:
- Autonomous Agent gera insights
- Sem regras de notificação configuráveis por ativos

**O que falta**:
- ❌ Asset-based notification rules
- ❌ Template-based rules (aplicar a todos de um tipo)
- ❌ Email/SMS/Teams integrations
- ❌ Escalation policies
- ❌ Notification history

---

### 8. **Relacionamentos Entre Ativos** 🟠 MODERADO

**PI Vision tem**:
```
Motor_01 → feeds → Pump_01
Pump_01 → supplies → Tank_01
Tank_01 → connects → Line_01

# Permite rastreamento de fluxo de processo
```

**Nós temos**:
- Sem relacionamentos entre devices/assets

**O que falta**:
- ❌ Asset relationships model
- ❌ Process flow visualization
- ❌ Upstream/downstream navigation
- ❌ Impact analysis (se falhar, o que afeta?)

---

### 9. **Visualização Hierárquica no Dashboard Builder** 🔴 CRÍTICO

**PI Vision tem**:

```
┌─────────────────────────────────────────┐
│ [▼ Planta A]                            │
│   [▼ Área de Moagem]                    │
│     [▶ Moinho 1]                        │
│     [▼ Moinho 2]                        │
│       ├─ Speed                          │
│       ├─ Current                        │
│       ├─ Temperature                    │
│       └─ Status                         │
│   [▶ Área de Armazenamento]            │
│ [▶ Planta B]                            │
└─────────────────────────────────────────┘
```

**Nós temos**:
```
┌─────────────────────────────────────────┐
│ Buscar: [___________]                   │
│ Categoria: [Todas ▼]                    │
│                                         │
│ [TAG_01] Process  100RPM                │
│ [TAG_02] Energy   1.5A                  │
│ [TAG_03] Quality  75°C                  │
│ [TAG_04] Status   Running               │
│ ... (lista plana)                       │
└─────────────────────────────────────────┘
```

**O que falta**:
- ❌ Tree view component (React)
- ❌ Expandable/collapsible nodes
- ❌ Icons por tipo de asset
- ❌ Lazy loading de sub-árvores
- ❌ Context menu (right-click)
- ❌ Multi-select de ativos

---

### 10. **Unit of Measure (UOM) Management** 🟢 BAIXA PRIORIDADE

**PI Vision tem**:
- Conversão automática de unidades
- Database de UOMs
- UOM classes (Temperature, Pressure, Flow, etc)

**Nós temos**:
- Campo `unit` como string livre
- Sem conversões

**O que falta**:
- ❌ UOM database
- ❌ UOM conversions (°C ↔ °F)
- ❌ UOM validation

---

### 11. **Table Lookup (Tabelas de Referência)** 🟢 BAIXA PRIORIDADE

**PI Vision tem**:
```python
# Lookup Table: Motor Status Codes
0 → "Stopped"
1 → "Starting"
2 → "Running"
3 → "Stopping"
4 → "Fault"
```

**Nós temos**:
- Sem lookups automáticos

**O que falta**:
- ❌ Lookup table model
- ❌ Value mapping
- ❌ Reverse lookup

---

## 📋 Roadmap Sugerido para Asset Framework

### **Phase 1: Foundation (1-2 semanas)** 🔴 CRÍTICO

#### Backend Models
```python
# 1. Asset Model
class Asset(Base):
    id = UUID
    name = String
    description = Text
    parent_id = UUID (self-referential FK)
    template_id = UUID (FK to AssetTemplate)
    asset_type = Enum (Equipment, Area, Site, Enterprise)
    metadata = JSONB

    # Relationships
    parent = relationship("Asset", remote_side=[id])
    children = relationship("Asset", back_populates="parent")
    attributes = relationship("AssetAttribute")
    template = relationship("AssetTemplate")

# 2. AssetAttribute Model
class AssetAttribute(Base):
    id = UUID
    asset_id = UUID (FK)
    name = String
    attribute_type = Enum (TagReference, Static, Calculated)
    tag_id = UUID (FK, nullable=True)
    static_value = String (nullable=True)
    formula = String (nullable=True)
    unit = String

# 3. AssetTemplate Model
class AssetTemplate(Base):
    id = UUID
    name = String
    description = Text
    asset_type = Enum
    attribute_definitions = JSONB
```

#### Frontend Components
```typescript
// 1. AssetTreeView component
interface AssetTreeNode {
  id: string;
  name: string;
  type: 'enterprise' | 'site' | 'area' | 'equipment';
  children?: AssetTreeNode[];
  attributes?: AssetAttribute[];
}

// 2. AssetContextSelector component
// 3. AssetNavigationPanel component
```

#### API Endpoints
```
GET  /api/v1/assets                    # Lista hierárquica
GET  /api/v1/assets/{id}               # Detalhes do asset
GET  /api/v1/assets/{id}/children      # Filhos diretos
GET  /api/v1/assets/{id}/attributes    # Atributos do asset
POST /api/v1/assets                    # Criar asset
PUT  /api/v1/assets/{id}               # Atualizar
DELETE /api/v1/assets/{id}             # Deletar

GET  /api/v1/asset-templates           # Templates disponíveis
POST /api/v1/assets/from-template      # Criar de template
```

---

### **Phase 2: Navigation & Context (1 semana)** 🟡

1. **Asset Context Provider** (React Context)
   - Armazena asset selecionado
   - Propaga para todos os widgets
   - Permite drill-up/drill-down

2. **Tree Navigation Component**
   - Expandir/colapsar
   - Icons por tipo
   - Drag & drop de atributos
   - Busca na árvore

3. **Breadcrumb Navigation**
   ```
   Home > Planta A > Área de Moagem > Moinho 1
   ```

4. **Dynamic Widget Binding**
   - Widget configurado para mostrar "Current Asset Speed"
   - Automaticamente mostra speed do asset selecionado

---

### **Phase 3: Templates & Analyses (1-2 semanas)** 🟡

1. **Template Library UI**
   - Catalog de templates
   - Preview de template
   - Instanciar template

2. **Formula Engine**
   ```python
   class FormulaEngine:
       def evaluate(self, formula: str, context: dict) -> float:
           # Parse formula
           # Resolve attribute references
           # Calculate result
           pass
   ```

3. **Analysis Scheduler**
   - Event-triggered
   - Time-triggered
   - On-demand

---

### **Phase 4: Advanced Features (2-3 semanas)** 🟠

1. Event Frames
2. Notifications
3. Asset Relationships
4. Genealogy tracking
5. UOM management
6. Table lookups

---

## 💡 Implementação Mínima Viável (MVP)

**Para ter funcionalidade básica de Asset Framework em 1 semana:**

### Backend (3-4 dias)

```python
# models/asset.py
class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    asset_type = Column(Enum('enterprise', 'site', 'area', 'equipment'))
    parent_id = Column(UUID, ForeignKey('assets.id'))
    metadata = Column(JSONB, default=dict)

    # Self-referential relationship
    parent = relationship("Asset", remote_side=[id], back_populates="children")
    children = relationship("Asset", back_populates="parent")

class AssetAttribute(Base):
    __tablename__ = "asset_attributes"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID, ForeignKey('assets.id'))
    name = Column(String(255), nullable=False)
    tag_id = Column(UUID, ForeignKey('tags.id'), nullable=True)
    static_value = Column(String(500))
    unit = Column(String(50))

    asset = relationship("Asset", back_populates="attributes")
    tag = relationship("Tag")
```

```python
# api/v1/endpoints/assets.py
@router.get("/assets")
async def get_assets_tree():
    """Returns hierarchical asset tree"""
    pass

@router.get("/assets/{asset_id}/attributes")
async def get_asset_attributes(asset_id: UUID):
    """Returns attributes with resolved tag values"""
    pass

@router.post("/assets")
async def create_asset(asset: AssetCreate):
    """Create new asset"""
    pass
```

### Frontend (2-3 dias)

```typescript
// components/AssetTree.tsx
export const AssetTree: React.FC = () => {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>();

  return (
    <div className="asset-tree">
      {assets.map(asset => (
        <AssetNode
          key={asset.id}
          asset={asset}
          expanded={expandedNodes.has(asset.id)}
          onToggle={() => toggleNode(asset.id)}
        />
      ))}
    </div>
  );
};

// components/AssetNode.tsx
export const AssetNode: React.FC<{asset: Asset}> = ({ asset }) => {
  const [{ isDragging }, drag] = useDrag({
    type: 'ASSET_ATTRIBUTE',
    item: { assetId: asset.id, attribute: 'speed' }
  });

  return (
    <div ref={drag}>
      <TreeIcon type={asset.type} />
      <span>{asset.name}</span>
      {asset.children?.map(child => (
        <AssetNode key={child.id} asset={child} />
      ))}
    </div>
  );
};
```

---

## 🎯 Priorização de Features

### **Essencial (Fazer Primeiro)** 🔴

1. ✅ Modelo Asset hierárquico
2. ✅ AssetAttribute com referência a Tags
3. ✅ Tree view navigation
4. ✅ Asset context selector
5. ✅ Dynamic widget binding

**Impacto**: 80% da funcionalidade do PI AF

---

### **Importante (Fazer em Seguida)** 🟡

6. Asset Templates
7. Template instantiation
8. Calculated attributes
9. Formula engine básico
10. Breadcrumb navigation

**Impacto**: +15% da funcionalidade

---

### **Nice to Have (Futuro)** 🟢

11. Event Frames
12. Notifications
13. Asset Relationships
14. UOM conversions
15. Table lookups

**Impacto**: +5% da funcionalidade

---

## 📊 Comparativo Final

| Feature | PI Vision AF | OptiFlow Atual | OptiFlow com MVP |
|---------|-------------|----------------|------------------|
| **Hierarquia de Ativos** | ✅ | ❌ | ✅ |
| **Tree Navigation** | ✅ | ❌ | ✅ |
| **Asset Context** | ✅ | ❌ | ✅ |
| **Templates** | ✅ | ❌ | 🟡 Básico |
| **Atributos** | ✅ | ❌ | ✅ |
| **Calculated Attributes** | ✅ | ❌ | 🟡 Fórmulas simples |
| **Event Frames** | ✅ | ❌ | ❌ |
| **Notifications** | ✅ | 🟡 Via Agent | 🟡 Via Agent |
| **Relationships** | ✅ | ❌ | ❌ |
| **UOM Conversions** | ✅ | ❌ | ❌ |

**Legenda**:
- ✅ Completo
- 🟡 Parcial
- ❌ Não implementado

---

## 🚀 Próximos Passos

### **Opção A: Implementar MVP (1 semana)**

**Estimativa**: 40-60 horas de desenvolvimento

**Entregas**:
1. Backend: Models + APIs (20h)
2. Frontend: Components (20h)
3. Migration scripts (5h)
4. Tests (10h)
5. Documentation (5h)

**Resultado**: Asset Framework básico funcional

---

### **Opção B: Implementação Completa (1 mês)**

**Estimativa**: 160-200 horas de desenvolvimento

**Entregas**:
- Todas as features essenciais + importantes
- Templates completos
- Formula engine robusto
- UI polido
- Testes abrangentes
- Documentação completa

**Resultado**: Paridade com PI Vision AF

---

### **Opção C: Iterativo (3-4 sprints)**

**Sprint 1** (1 semana): MVP básico
**Sprint 2** (1 semana): Templates + Formulas
**Sprint 3** (1 semana): Polish + UX
**Sprint 4** (1 semana): Advanced features

**Resultado**: Implementação gradual com feedback contínuo

---

## 📝 Conclusão

**O que temos hoje**: Tags planas com boa funcionalidade básica

**O que precisamos**: Camada de abstração de Assets com hierarquia

**Diferença chave**: PI Vision separa **Assets** (conceito lógico) de **Tags** (dados físicos)

**Benefícios de implementar**:
1. ✅ Organização muito melhor para grandes plantas
2. ✅ Reutilização via templates
3. ✅ Contexto de navegação
4. ✅ Análises automatizadas
5. ✅ Escalabilidade para 1000+ equipamentos

**Recomendação**: Implementar MVP do Asset Framework (Opção A) como próximo passo prioritário.

---

**Desenvolvido por**: Claude (Anthropic)
**Data**: 03 de Novembro de 2025
**Status**: Análise completa - Aguardando decisão de implementação
