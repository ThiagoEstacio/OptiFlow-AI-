# 📊 Frontend OptiFlow AI - Visualização de Dados

## Status: ✅ OPERACIONAL

Data: 10 de novembro de 2025

---

## 🎯 Componentes do Frontend

### Dashboard Principal
**URL**: `http://localhost:3000`

O frontend OptiFlow AI está rodando com os seguintes componentes:

### 1. 📈 Tags Page (Visualização de Dados)
**Rota**: `/tags`

**Funcionalidades**:
- ✅ **Tree View de Assets** - Navegação hierárquica (Sites → Áreas → Unidades → Equipamentos)
- ✅ **Lista de Tags** - Tabela com todas as tags configuradas
- ✅ **Filtros Avançados** - Por asset, tipo, status
- ✅ **Visualização em Tempo Real** - WebSocket para updates
- ✅ **Gráficos de Tendência** - Histórico de valores
- ✅ **Alarmes** - Status e configuração

### 2. 🏭 Sites & Assets
**Rota**: `/sites`

**Funcionalidades**:
- Gerenciamento de organizações e sites
- Hierarquia de assets (área, unidade, equipamento)
- Configuração de tags por asset
- Status e estatísticas

### 3. 🔔 Alarmes
**Rota**: `/alarms`

**Funcionalidades**:
- Lista de alarmes ativos
- Histórico de alarmes
- Configuração de regras
- Notificações

### 4. 📊 Dashboards
**Rota**: `/dashboards`

**Funcionalidades**:
- Dashboards personalizados
- Widgets configuráveis
- Visualizações em tempo real
- KPIs e métricas

---

## 🚀 Como Acessar

### 1. Verificar se o Frontend está Rodando

```bash
# Verificar status
docker compose ps frontend

# Ver logs
docker compose logs -f frontend

# Acessar URL
# http://localhost:3000
```

### 2. Login

```bash
# Credenciais padrão (se configurado):
Email: admin@optiflow.local
Senha: (ver .env.production ou usar script de geração)

# Ou criar novo usuário via API:
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password",
    "full_name": "Your Name"
  }'
```

### 3. Navegar pelo Sistema

**Fluxo Recomendado**:
1. **Sites** → Criar organização e sites
2. **Assets** → Criar hierarquia (área → unidade → equipamento)
3. **Tags** → Configurar tags para coleta de dados
4. **Gateway** → Conectar dispositivos OPC UA/Modbus
5. **Dashboards** → Visualizar dados em tempo real

---

## 📱 Páginas Disponíveis

### Home Dashboard (`/`)
- Visão geral do sistema
- Métricas principais
- Status dos serviços
- Alertas recentes

### Tags (`/tags`)
**Principais Componentes**:
- **AssetTreeView** - Árvore de navegação de assets
- **TagList** - Lista de tags com filtros
- **TagDetailsPanel** - Detalhes e configuração de tag
- **TrendChart** - Gráfico de tendência histórica
- **AlarmStatus** - Status de alarmes por tag

### Alarms (`/alarms`)
- Alarmes ativos
- Histórico
- Configuração de regras
- Prioridades e ações

### Analytics (`/analytics`)
- Análises avançadas
- Relatórios
- Estatísticas
- Previsões (ML)

### Settings (`/settings`)
- Configurações do sistema
- Usuários e permissões
- Integrações
- Aparência

---

## 🔧 Funcionalidades Técnicas

### WebSocket (Tempo Real)
```typescript
// Conexão automática para updates em tempo real
const socket = io('http://localhost:8000', {
  path: '/ws/socket.io',
  transports: ['websocket']
});

// Eventos disponíveis:
// - 'tag_update' - Atualização de valor de tag
// - 'alarm_update' - Atualização de alarme
// - 'device_status' - Status de dispositivo
```

### API REST
```typescript
// Base URL
const API_URL = 'http://localhost:8000/api/v1';

// Endpoints principais:
// GET /tags - Lista todas as tags
// GET /tags/{id} - Detalhes de uma tag
// GET /tags/{id}/history - Histórico de valores
// GET /assets - Lista assets
// GET /alarms - Lista alarmes
// GET /analytics/trends - Análises de tendências
```

### State Management (Redux)
```typescript
// Stores disponíveis:
// - authSlice - Autenticação
// - tagsSlice - Gerenciamento de tags
// - assetsSlice - Gerenciamento de assets
// - alarmsSlice - Gerenciamento de alarmes
// - websocketSlice - Conexão WebSocket
```

---

## 🎨 Tecnologias Frontend

### Core
- **React 18.2** - Framework UI
- **TypeScript 5.0** - Type safety
- **Vite 5.0** - Build tool e dev server
- **React Router 6.30** - Roteamento

### UI Components
- **Material-UI (MUI) 7.3** - Design system
- **MUI X Tree View 8.16** - Tree navigation
- **Lucide React** - Ícones modernos
- **TailwindCSS 3.4** - Utility-first CSS

### Data Visualization
- **Recharts 2.15** - Gráficos e charts
- **Plotly.js 2.27** - Gráficos avançados
- **D3.js 7.8** - Visualizações customizadas
- **React Table 8.11** - Tabelas avançadas

### State & Data
- **Redux Toolkit 2.9** - State management
- **RTK Query** - Data fetching e cache
- **React Hook Form 7.65** - Formulários
- **Zod 3.22** - Validação de schemas

### Real-time
- **Socket.io Client 4.6** - WebSocket client
- **React Hot Toast 2.6** - Notificações

---

## 📊 Visualização de Dados em Tempo Real

### Gráficos Disponíveis

#### 1. Line Chart (Tendência)
```typescript
// Evolução temporal de valores
<LineChart data={tagHistory}>
  <Line dataKey="value" stroke="#2196f3" />
  <XAxis dataKey="timestamp" />
  <YAxis />
</LineChart>
```

#### 2. Area Chart (Preenchido)
```typescript
// Tendência com área preenchida
<AreaChart data={data}>
  <Area type="monotone" dataKey="value" fill="#4caf50" />
</AreaChart>
```

#### 3. Bar Chart (Comparação)
```typescript
// Comparação entre tags ou períodos
<BarChart data={comparison}>
  <Bar dataKey="tag1" fill="#2196f3" />
  <Bar dataKey="tag2" fill="#4caf50" />
</BarChart>
```

#### 4. Scatter Plot (Correlação)
```typescript
// Análise de correlação entre variáveis
<ScatterChart>
  <Scatter data={data} fill="#ff9800" />
</ScatterChart>
```

#### 5. Pie Chart (Distribuição)
```typescript
// Distribuição percentual
<PieChart>
  <Pie data={distribution} dataKey="value" />
</PieChart>
```

---

## 🔥 Features Avançadas

### 1. Real-time Updates
- WebSocket para updates < 100ms
- Otimização com debounce
- Reconexão automática

### 2. Filtros Avançados
- Por asset (tree view)
- Por tipo de tag
- Por range de valores
- Por timestamp

### 3. Exportação de Dados
```typescript
// Exportar para CSV
export const exportToCSV = (data: TagHistory[]) => {
  const csv = convertToCSV(data);
  downloadFile(csv, 'tag_history.csv');
};

// Exportar gráfico como imagem
export const exportChart = (chartRef: RefObject) => {
  html2canvas(chartRef.current).then(canvas => {
    canvas.toBlob(blob => {
      saveAs(blob, 'chart.png');
    });
  });
};
```

### 4. Histórico Configurável
- Últimas 24 horas
- Última semana
- Último mês
- Range customizado

### 5. Agregações
- Média
- Mínimo/Máximo
- Soma
- Contagem
- Desvio padrão

---

## 🐛 Troubleshooting

### Frontend não carrega

```bash
# 1. Verificar se está rodando
docker compose ps frontend

# 2. Ver logs de erro
docker compose logs frontend

# 3. Restart
docker compose restart frontend

# 4. Rebuild se necessário
docker compose up -d --build frontend
```

### Erro de CORS

```bash
# Verificar configuração no backend
# backend/app/core/config.py
CORS_ORIGINS = ["http://localhost:3000", "http://localhost"]

# Restart backend
docker compose restart backend
```

### WebSocket não conecta

```bash
# 1. Verificar se backend está rodando
curl http://localhost:8000/health

# 2. Verificar configuração WebSocket
# frontend/src/services/websocket.ts
const SOCKET_URL = 'http://localhost:8000';

# 3. Ver logs de conexão
docker compose logs backend | grep -i websocket
```

### Dados não aparecem

```bash
# 1. Verificar se há tags cadastradas
curl http://localhost:8000/api/v1/tags

# 2. Verificar se gateway está coletando
docker compose logs gateway

# 3. Verificar InfluxDB
curl http://localhost:8086/health
```

---

## 📈 Próximas Melhorias

### Dashboard Avançado
- [ ] Widgets drag-and-drop
- [ ] Templates de dashboard
- [ ] Compartilhamento de dashboards
- [ ] Modo full-screen

### Visualizações
- [ ] Heat maps
- [ ] Gauges analógicos
- [ ] Diagramas P&ID interativos
- [ ] Modelo 3D de planta

### Analytics
- [ ] Previsões com ML
- [ ] Detecção de anomalias visual
- [ ] Correlação automática
- [ ] Recomendações de otimização

### Mobile
- [ ] PWA (Progressive Web App)
- [ ] App nativo (React Native)
- [ ] Notificações push
- [ ] Modo offline

---

## 🔗 Links Úteis

### Desenvolvimento
- **Frontend Dev**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9090

### Documentação
- **React**: https://react.dev
- **MUI**: https://mui.com
- **Recharts**: https://recharts.org
- **Redux Toolkit**: https://redux-toolkit.js.org

### Design System
- **MUI Components**: https://mui.com/material-ui/all-components/
- **Icons**: https://mui.com/material-ui/material-icons/
- **Theming**: https://mui.com/material-ui/customization/theming/

---

## ✅ Checklist de Funcionalidades

### Visualização
- [x] Tree view de assets
- [x] Lista de tags com filtros
- [x] Gráficos de tendência (Recharts)
- [x] Tabelas responsivas
- [x] Cards de métricas
- [x] Status indicators

### Interação
- [x] Filtros dinâmicos
- [x] Busca em tempo real
- [x] Paginação
- [x] Ordenação de colunas
- [x] Seleção múltipla
- [x] Drag and drop (tree view)

### Real-time
- [x] WebSocket connection
- [x] Auto-updates de valores
- [x] Notificações de alarmes
- [x] Status de dispositivos
- [x] Reconexão automática

### UX
- [x] Tema claro/escuro
- [x] Responsivo (mobile/tablet/desktop)
- [x] Loading states
- [x] Error handling
- [x] Feedback visual
- [x] Tooltips informativos

---

**Status**: ✅ **OPERACIONAL**

O frontend OptiFlow AI está pronto para visualização de dados em tempo real. Acesse `http://localhost:3000` e navegue pelas páginas de Tags, Alarms e Dashboards para ver seus dados IIoT.

**Próximo Passo**: Criar dados de exemplo ou conectar dispositivos reais via Gateway!
