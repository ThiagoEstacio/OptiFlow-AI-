# PDCA Frontend - Problemas de Integração Identificados e Corrigidos

**Data**: 2025-11-17
**Status**: 🔴 CRÍTICO - Múltiplos problemas de integração frontend-backend

---

## 🚨 PROBLEMAS CRÍTICOS IDENTIFICADOS

### 1. Chamadas API SEM AUTENTICAÇÃO

**Arquivos afetados** (usando `fetch()` hardcoded):
- `/src/pages/ProfessionalDashboard.tsx` - ✅ CORRIGIDO
- `/src/pages/ProfessionalAnalytics.tsx` - 🔴 PENDENTE
- `/src/pages/ProfessionalAlarms.tsx` - 🔴 PENDENTE
- `/src/pages/ReportsDashboard.tsx` - 🔴 PENDENTE
- `/src/pages/AdminPage.tsx` - 🔴 PENDENTE

**Problema**:
```typescript
// ❌ ERRADO - Sem token de autenticação
const response = await fetch('http://localhost:8000/api/v1/ml/models');

// ✅ CORRETO - Com autenticação via apiClient
const models = await apiClient.get('/api/v1/ml/models/');
```

**Impacto**:
- Endpoints retornam 401 Unauthorized
- Dados não carregam no dashboard
- Gráficos aparecem vazios

---

### 2. Dashboard Builder DESABILITADO

**Problema encontrado** (App.tsx linha 195):
```tsx
// ❌ REDIRECIONAVA para /dashboard
<Route path="dashboard-builder" element={<Navigate to="/dashboard" replace />} />
```

**Correção aplicada**:
```tsx
// ✅ AGORA redireciona para a rota correta
<Route path="dashboard-builder" element={<Navigate to="/dashboards/builder" replace />} />
```

**Novas rotas adicionadas**:
- `/dashboard/executive` - Executive Dashboard
- `/dashboards/builder` - Dashboard Builder Page
- `/dashboards/new` - Criar novo dashboard

---

### 3. URLs Hardcoded (localhost:8000)

**Problema**:
- URLs apontam diretamente para `http://localhost:8000`
- Não funciona em produção
- Não usa proxy do Vite

**Locais afetados**:
```typescript
// Em ProfessionalDashboard.tsx:
fetch('http://localhost:8000/api/v1/tags/timeseries/...')

// Em ProfessionalAnalytics.tsx:
fetch('http://localhost:8000/api/v1/...')

// Em ProfessionalAlarms.tsx:
fetch('http://localhost:8000/api/v1/...')
```

**Solução**: Usar `apiClient` que já configura a BASE_URL corretamente

---

### 4. WebSocket Conecta mas Dados Não Fluem

**Status atual** (App.tsx):
```typescript
// WebSocket conecta mas simulador pode não estar rodando
websocketService.connect('ws://localhost:8000/api/v1/ws/simulator/stream');
simulatorDataSync.start();
tagDataSimulator.start();
```

**Verificações necessárias**:
- [ ] Backend WebSocket endpoint disponível
- [ ] Simulador iniciado (`POST /api/v1/simulator/start`)
- [ ] InfluxDB com dados históricos
- [ ] Tags cadastradas no PostgreSQL

---

## ✅ CORREÇÕES APLICADAS

### 1. ProfessionalDashboard.tsx

**Mudança**: Substituído `fetch()` por `apiClient.get()`

```typescript
// ANTES (sem autenticação):
const response = await fetch('http://localhost:8000/api/v1/ml/models');
if (response.ok) {
  const models = await response.json();
}

// DEPOIS (com autenticação):
const models = await apiClient.get('/api/v1/ml/models/');
if (Array.isArray(models) && models.length > 0) {
  // process models
}
```

**Funções corrigidas**:
- `loadMLModels()` - Modelos de ML
- `loadPerformanceChart()` - Gráfico de performance (24h)
- `loadEnergyChart()` - Gráfico de energia (12h)
- `loadProductionChart()` - Gráfico de produção (7 dias)

### 2. App.tsx - Rotas do Dashboard Builder

**Adicionado**:
```tsx
<Route path="dashboard/executive" element={<ExecutiveDashboard />} />
<Route path="dashboards/builder" element={<DashboardBuilderPage />} />
<Route path="dashboards/new" element={<DashboardBuilder />} />
```

**Corrigido redirect**:
```tsx
<Route path="dashboard-builder" element={<Navigate to="/dashboards/builder" replace />} />
```

---

## 🔴 CORREÇÕES PENDENTES

### Alta Prioridade

1. **ProfessionalAnalytics.tsx** - Múltiplas chamadas fetch() sem auth
2. **ProfessionalAlarms.tsx** - Chamadas fetch() sem auth
3. **ReportsDashboard.tsx** - Chamadas fetch() sem auth
4. **AdminPage.tsx** - Chamadas fetch() sem auth

### Média Prioridade

5. **Verificar endpoints de Dashboards no backend** - Confirmar se `/api/v1/dashboards` funciona
6. **Testar WebSocket streaming** - Validar conexão real-time
7. **Populacar dados históricos** - InfluxDB pode estar vazio após restart

### Baixa Prioridade

8. **Remover imports não utilizados** - App.tsx tem imports desnecessários
9. **Configurar proxy Vite para produção** - Evitar URLs hardcoded

---

## 📋 CHECKLIST DE VALIDAÇÃO

### Autenticação
- [x] apiClient tem interceptor de autenticação
- [x] Token é incluído automaticamente nos headers
- [ ] Refresh token funciona quando expirado
- [ ] Login page redireciona corretamente

### Dashboard Principal
- [x] Rota `/dashboard` funciona
- [x] ProfessionalDashboard usa apiClient
- [ ] Gráficos carregam dados corretamente
- [ ] KPIs mostram valores reais

### Dashboard Builder
- [x] Rota `/dashboards/builder` existe
- [x] DashboardBuilderPage importado
- [x] API service usa apiClient
- [ ] Endpoint backend `/api/v1/dashboards` funciona
- [ ] Criação de dashboards funciona
- [ ] Drag-and-drop de widgets funciona

### Dados em Tempo Real
- [x] WebSocket service configurado
- [x] Simulador iniciado no useEffect
- [ ] Dados fluindo via WebSocket
- [ ] Tags atualizando em tempo real
- [ ] Gráficos refresham automaticamente

### Outros Módulos
- [ ] ProfessionalAnalytics carrega dados
- [ ] ProfessionalAlarms mostra alarmes
- [ ] ReportsDashboard gera relatórios
- [ ] Settings funciona corretamente

---

## 🚀 PRÓXIMOS PASSOS

### Imediato (Hoje)

1. **Corrigir ProfessionalAnalytics.tsx**
   ```bash
   # Substituir fetch() por apiClient.get()
   ```

2. **Corrigir ProfessionalAlarms.tsx**
   ```bash
   # Substituir fetch() por apiClient.get()
   ```

3. **Testar backend endpoint de dashboards**
   ```bash
   TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
     -d "username=admin@optiflow.com&password=admin" | jq -r '.access_token')

   curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/api/v1/dashboards/"
   ```

4. **Reiniciar simulador e popular dados**
   ```bash
   curl -X POST http://localhost:8000/api/v1/simulator/start
   # Executar steps para gerar dados
   ```

### Curto Prazo (Esta Semana)

5. **Rebuild do frontend com correções**
   ```bash
   cd frontend
   npm run build
   docker restart optiflow-frontend
   ```

6. **Testes end-to-end de cada página**
7. **Documentar URLs de API corretas**
8. **Configurar variáveis de ambiente para produção**

---

## 📊 MÉTRICAS DE SUCESSO

| Métrica | Antes | Depois | Meta |
|---------|-------|--------|------|
| Páginas com fetch() hardcoded | 5 | 1 | 0 |
| Rotas do Dashboard Builder | 0 | 3 | 3 ✅ |
| Endpoints com autenticação | 1/5 | 2/5 | 5/5 |
| Gráficos carregando dados | 0% | 25% | 100% |

---

## 🔧 SCRIPT DE CORREÇÃO AUTOMÁTICA

Para corrigir todas as chamadas fetch() hardcoded:

```bash
#!/bin/bash
# fix-frontend-api-calls.sh

FILES=(
  "src/pages/ProfessionalAnalytics.tsx"
  "src/pages/ProfessionalAlarms.tsx"
  "src/pages/ReportsDashboard.tsx"
  "src/pages/AdminPage.tsx"
)

for file in "${FILES[@]}"; do
  echo "Fixing $file..."

  # 1. Adicionar import do apiClient (se não existir)
  if ! grep -q "import apiClient" "$file"; then
    sed -i "1a import apiClient from '../api/client';" "$file"
  fi

  # 2. Substituir fetch patterns (manualmente para cada arquivo)
  # Este passo requer análise individual de cada arquivo
done
```

---

## 📝 CONCLUSÃO

O frontend tem **problemas críticos de integração** que impedem o funcionamento correto:

1. **5 páginas** fazem chamadas API sem autenticação
2. **Dashboard Builder** estava completamente desabilitado
3. **URLs hardcoded** não funcionam em produção
4. **Dados não fluem** porque backend pode estar parado

### Status Atual
- ✅ ProfessionalDashboard corrigido (principal)
- ✅ Dashboard Builder habilitado
- 🔴 4 páginas ainda precisam correção
- 🔴 Backend precisa restart com simulador ativo

### Prioridade
**CRÍTICA** - Sistema não funcional para produção até correções serem aplicadas.

---

**Atualizado**: 2025-11-17
**Próxima revisão**: Após aplicação de todas as correções pendentes
