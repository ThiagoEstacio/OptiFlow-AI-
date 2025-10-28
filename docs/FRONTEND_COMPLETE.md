# Frontend SmartPort - Documentação Completa

## 📋 Visão Geral

O frontend do SmartPort foi completamente implementado com todas as funcionalidades essenciais para gerenciamento de sites industriais, dispositivos, tags e alarmes.

## ✅ Funcionalidades Implementadas

### 1. **Autenticação e Segurança**
- ✅ Login com JWT
- ✅ Logout funcional
- ✅ Proteção de rotas (PrivateRoute)
- ✅ Persistência de token
- ✅ Redirecionamento automático em 401

**Arquivos**: `src/pages/LoginPage.tsx`, `src/components/PrivateRoute.tsx`, `src/hooks/useAuth.ts`

### 2. **Dashboard**
- ✅ Estatísticas em tempo real (Sites, Devices, Data Points, Alarms)
- ✅ Recent Sites widget
- ✅ Active Alarms widget
- ✅ Device Status grid
- ✅ Quick Actions

**Arquivo**: `src/pages/Dashboard.tsx`

### 3. **Gerenciamento de Sites (CRUD Completo)**
- ✅ Listagem com tabela
- ✅ Busca e filtros
- ✅ Criar novo site (formulário completo)
- ✅ Editar site existente
- ✅ Deletar com confirmação
- ✅ Validação de formulários com react-hook-form
- ✅ Notificações toast de sucesso/erro

**Arquivos**:
- `src/pages/SitesPage.tsx`
- `src/components/Forms/SiteForm.tsx`

### 4. **Gerenciamento de Devices (CRUD Completo)**
- ✅ Grid visual de dispositivos
- ✅ Busca e filtros (nome, tipo, protocolo, IP)
- ✅ Criar novo device (formulário com configurações específicas por protocolo)
- ✅ Editar device existente
- ✅ Deletar com confirmação
- ✅ Suporte a todos os protocolos: OPC UA, Modbus TCP/RTU, MQTT, Ethernet/IP, Siemens S7
- ✅ Indicador visual de status (conectado/desconectado)

**Arquivos**:
- `src/pages/DevicesPage.tsx`
- `src/components/Forms/DeviceForm.tsx`

### 5. **Gerenciamento de Tags (CRUD Completo)**
- ✅ Tabela completa de tags
- ✅ Filtros avançados (device, data type)
- ✅ Busca por nome, address, descrição
- ✅ Criar nova tag (formulário com scaling e limits)
- ✅ Editar tag existente
- ✅ Deletar com confirmação
- ✅ Suporte a múltiplos data types (BOOL, INT, FLOAT, DOUBLE, STRING, etc)
- ✅ Configuração de scaling (scale factor, offset)
- ✅ Configuração de limites (min/max)
- ✅ Toggle de logging

**Arquivos**:
- `src/pages/TagsPage.tsx`
- `src/components/Forms/TagForm.tsx`

### 6. **Visualização de Tag Details**
- ✅ Página dedicada para cada tag
- ✅ Gráfico de série temporal (Recharts)
- ✅ Seletor de período (1h, 6h, 24h, 7d)
- ✅ Refresh manual
- ✅ Exibição de configurações (address, data type, unit)
- ✅ Exibição de scaling e limites
- ✅ Status da tag (enabled, logging)

**Arquivo**: `src/pages/TagDetailsPage.tsx`

### 7. **Gerenciamento de Alarms**
- ✅ Lista completa de alarmes
- ✅ Estatísticas (Active, Acknowledged, Resolved)
- ✅ Filtros por severidade (Critical, High, Medium, Low)
- ✅ Filtros por status (Active, Acknowledged, Resolved)
- ✅ Busca por mensagem ou tag
- ✅ Acknowledge de alarmes
- ✅ Indicadores visuais de severidade (ícones e cores)
- ✅ Formatação de datas

**Arquivo**: `src/pages/AlarmsPage.tsx`

### 8. **Componentes de Charts**
- ✅ TimeSeriesChart (Line e Area charts)
- ✅ MultiSeriesChart (múltiplas séries em um gráfico)
- ✅ Tooltip formatado
- ✅ Legend
- ✅ Grid customizável
- ✅ Formatação de eixos
- ✅ Suporte a unidades

**Arquivos**:
- `src/components/Charts/TimeSeriesChart.tsx`
- `src/components/Charts/MultiSeriesChart.tsx`

### 9. **Sistema de Notificações**
- ✅ Toast notifications (react-hot-toast)
- ✅ Mensagens de sucesso/erro
- ✅ Loading states
- ✅ Promise-based toasts
- ✅ Customização de duração e posição

**Arquivos**:
- `src/components/Toast/Toaster.tsx`
- `src/utils/toast.ts`

### 10. **Modais e Diálogos**
- ✅ Modal genérico reutilizável
- ✅ Tamanhos customizáveis (sm, md, lg, xl)
- ✅ ConfirmDialog para confirmações
- ✅ Variantes (danger, warning, info)
- ✅ Loading states
- ✅ Fechar com ESC
- ✅ Backdrop clicável

**Arquivos**:
- `src/components/Modal/Modal.tsx`
- `src/components/Modal/ConfirmDialog.tsx`

### 11. **WebSocket Real-Time**
- ✅ WebSocket service completo
- ✅ Auto-reconnect
- ✅ Message handlers por tipo
- ✅ React hook (useWebSocket)
- ✅ Suporte a múltiplos handlers

**Arquivos**:
- `src/services/websocket.ts`
- `src/hooks/useWebSocket.ts`

### 12. **Página de Settings**
- ✅ Informações do usuário
- ✅ Dark Mode toggle
- ✅ Sidebar collapse toggle
- ✅ Auto-refresh settings
- ✅ Interval de refresh
- ✅ Notificações enable/disable
- ✅ Sound alerts toggle

**Arquivo**: `src/pages/SettingsPage.tsx`

### 13. **Dark Mode**
- ✅ Toggle funcional
- ✅ Persistência de preferência
- ✅ Provider global
- ✅ Classes CSS aplicadas automaticamente

**Arquivo**: `src/components/DarkModeProvider.tsx`

### 14. **Redux Store Completo**
- ✅ authSlice - Autenticação
- ✅ sitesSlice - Sites CRUD
- ✅ devicesSlice - Devices CRUD
- ✅ tagsSlice - Tags CRUD + timeseries
- ✅ alarmsSlice - Alarms + acknowledge
- ✅ organizationsSlice - Organizações
- ✅ uiSlice - Estado da UI (sidebar, dark mode)

**Diretório**: `src/store/slices/`

### 15. **API Client**
- ✅ 50+ métodos de endpoints
- ✅ Interceptors para JWT
- ✅ Auto-retry
- ✅ Type-safe com TypeScript
- ✅ Endpoints para todos os recursos

**Arquivo**: `src/api/client.ts`

---

## 📊 Estatísticas do Código

| Componente | Arquivos | Linhas de Código |
|------------|----------|------------------|
| **Pages** | 8 | ~2.000 |
| **Forms** | 3 | ~900 |
| **Components** | 10+ | ~1.500 |
| **Redux Store** | 7 slices | ~1.500 |
| **API Client** | 1 | ~350 |
| **Charts** | 2 | ~300 |
| **Services** | 2 | ~200 |
| **Hooks** | 2 | ~100 |
| **Utils** | 1 | ~50 |
| **Types** | 1 | ~350 |
| **Total** | ~37 | **~7.250 linhas** |

---

## 🎨 Design e UX

### Componentes de UI
- **Tabelas**: Responsivas com hover states
- **Cards**: Grid layout responsivo
- **Formulários**: Validação em tempo real
- **Botões**: Estados de loading
- **Badges**: Cores semânticas (success, danger, warning, info)
- **Spinners**: Loading states consistentes
- **Icons**: SVG inline para performance

### Cores e Temas
- **Primary**: Blue (#3B82F6)
- **Success**: Green (#10B981)
- **Danger**: Red (#EF4444)
- **Warning**: Yellow/Orange (#F59E0B)
- **Info**: Blue (#3B82F6)

### Responsividade
- ✅ Mobile (< 640px)
- ✅ Tablet (640px - 1024px)
- ✅ Desktop (> 1024px)
- ✅ Grid adaptativo
- ✅ Sidebar colapsável

---

## 🔧 Tecnologias Utilizadas

| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| **React** | 18.2 | Framework UI |
| **TypeScript** | 5.0 | Type safety |
| **Redux Toolkit** | Latest | State management |
| **React Router** | 6.x | Routing |
| **Axios** | Latest | HTTP client |
| **React Hook Form** | Latest | Form management |
| **React Hot Toast** | Latest | Notifications |
| **Recharts** | Latest | Charts/Graphs |
| **date-fns** | Latest | Date formatting |
| **TailwindCSS** | 3.4 | Styling |
| **Vite** | 5.0 | Build tool |

---

## 📁 Estrutura de Arquivos

```
frontend/src/
├── api/
│   └── client.ts              # API client completo
├── components/
│   ├── Charts/
│   │   ├── TimeSeriesChart.tsx
│   │   └── MultiSeriesChart.tsx
│   ├── Forms/
│   │   ├── SiteForm.tsx
│   │   ├── DeviceForm.tsx
│   │   └── TagForm.tsx
│   ├── Layout/
│   │   ├── AppLayout.tsx
│   │   ├── Sidebar.tsx
│   │   └── TopBar.tsx
│   ├── Modal/
│   │   ├── Modal.tsx
│   │   └── ConfirmDialog.tsx
│   ├── Toast/
│   │   └── Toaster.tsx
│   ├── DarkModeProvider.tsx
│   └── PrivateRoute.tsx
├── hooks/
│   ├── useAuth.ts
│   └── useWebSocket.ts
├── pages/
│   ├── Dashboard.tsx
│   ├── SitesPage.tsx
│   ├── DevicesPage.tsx
│   ├── TagsPage.tsx
│   ├── TagDetailsPage.tsx
│   ├── AlarmsPage.tsx
│   ├── SettingsPage.tsx
│   └── LoginPage.tsx
├── services/
│   └── websocket.ts
├── store/
│   ├── index.ts
│   └── slices/
│       ├── authSlice.ts
│       ├── sitesSlice.ts
│       ├── devicesSlice.ts
│       ├── tagsSlice.ts
│       ├── alarmsSlice.ts
│       ├── organizationsSlice.ts
│       └── uiSlice.ts
├── types/
│   └── index.ts
├── utils/
│   └── toast.ts
├── App.tsx
└── main.tsx
```

---

## 🚀 Como Usar

### Desenvolvimento

```bash
# Instalar dependências
cd frontend
npm install

# Iniciar dev server
npm run dev

# Build para produção
npm run build

# Preview do build
npm run preview
```

### Configuração

1. **API URL**: Configure em `src/api/client.ts`
2. **WebSocket URL**: Configure ao usar `useWebSocket` hook
3. **Environment Variables**: Crie `.env` se necessário

---

## 🎯 Rotas Disponíveis

| Rota | Componente | Proteção | Descrição |
|------|------------|----------|-----------|
| `/login` | LoginPage | Public | Página de login |
| `/` | Dashboard | Private | Dashboard principal |
| `/sites` | SitesPage | Private | Gerenciamento de sites |
| `/devices` | DevicesPage | Private | Gerenciamento de devices |
| `/tags` | TagsPage | Private | Gerenciamento de tags |
| `/tags/:id` | TagDetailsPage | Private | Detalhes e gráfico de tag |
| `/alarms` | AlarmsPage | Private | Gerenciamento de alarmes |
| `/settings` | SettingsPage | Private | Configurações do usuário |

---

## 🔐 Autenticação Flow

1. Usuário faz login em `/login`
2. Backend retorna `access_token`
3. Token armazenado em `localStorage`
4. Token incluído em todas as requisições (header `Authorization: Bearer <token>`)
5. Rotas privadas verificam presença de token
6. Se 401, usuário é redirecionado para `/login`

---

## 📝 Próximos Passos (Opcionais)

### Melhorias Futuras
- [ ] Paginação server-side nas tabelas
- [ ] Export de dados (CSV, Excel)
- [ ] Filtros avançados salvos
- [ ] Dashboards customizáveis
- [ ] Relatórios gerados
- [ ] User Management page (criar/editar usuários)
- [ ] Multi-idioma (i18n)
- [ ] Testes unitários (Jest, React Testing Library)
- [ ] Testes E2E (Cypress, Playwright)

---

## 🐛 Debugging

### Redux DevTools
- Extensão do navegador instalada
- State inspector
- Action logger
- Time-travel debugging

### React DevTools
- Component tree inspector
- Props/state viewer
- Performance profiler

### Network Tab
- Verificar requests/responses
- Headers
- Status codes
- Payloads

---

## 📚 Documentação de Referência

- [React Docs](https://react.dev)
- [TypeScript Docs](https://www.typescriptlang.org/docs)
- [Redux Toolkit Docs](https://redux-toolkit.js.org)
- [React Router Docs](https://reactrouter.com)
- [React Hook Form Docs](https://react-hook-form.com)
- [Recharts Docs](https://recharts.org)
- [TailwindCSS Docs](https://tailwindcss.com)

---

## 📞 Suporte

Para questões técnicas ou bugs, contate a equipe de desenvolvimento.

---

**Frontend SmartPort v1.0 - 100% Completo** ✅
