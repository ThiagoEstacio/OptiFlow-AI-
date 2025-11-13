# 📊 Dashboard Export - Exportação de Dashboards como Relatórios

## Visão Geral

Sistema completo para exportar dashboards como relatórios em PDF ou Excel, preservando todos os widgets e dados em tempo real.

---

## 🎯 Funcionalidades

### ✅ Exportação Disponível

- **PDF**: Relatório formatado profissionalmente com todos os widgets
- **Excel**: Planilha com dados tabulares de todos os widgets
- **Auto-download**: Download automático após geração
- **Metadados**: Inclui timestamp, usuário e informações do dashboard

### ✅ Tipos de Widgets Suportados

1. **Metric Widgets** - KPIs e métricas com valores e tendências
2. **Chart Widgets** - Gráficos convertidos em tabelas de dados
3. **Table Widgets** - Tabelas de dados com cabeçalhos
4. **Status Widgets** - Indicadores de status com cores

---

## 🚀 Como Usar

### 1. Importar o Componente

```typescript
import { DashboardExportButton } from '@/components/DashboardExportButton';
```

### 2. Adicionar ao Dashboard

```typescript
export const MyDashboard: React.FC = () => {
  // Função para extrair dados dos widgets do dashboard
  const getWidgetsData = () => {
    return [
      {
        title: "Eficiência Operacional",
        type: "metric",
        value: "95.2",
        unit: "%",
        trend: "+5.2%",
        target: "90"
      },
      {
        title: "Produção por Hora",
        type: "chart",
        chart_type: "line",
        data: [
          { hora: "08:00", producao: 120 },
          { hora: "09:00", producao: 135 },
          { hora: "10:00", producao: 142 }
        ]
      },
      {
        title: "Top 10 Produtos",
        type: "table",
        headers: ["Produto", "Quantidade", "Valor"],
        data: [
          { Produto: "A", Quantidade: 1500, Valor: "R$ 45,000" },
          { Produto: "B", Quantidade: 1200, Valor: "R$ 36,000" }
        ]
      },
      {
        title: "Status do Sistema",
        type: "status",
        status: "ok",
        message: "Todos os sistemas operacionais"
      }
    ];
  };

  return (
    <Box>
      {/* Dashboard Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="h4">Meu Dashboard</Typography>

        {/* Export Button */}
        <DashboardExportButton
          dashboardId="my-dashboard-001"
          dashboardName="Dashboard de Produção"
          getWidgetsData={getWidgetsData}
          variant="contained"
          size="medium"
        />
      </Stack>

      {/* Dashboard Widgets */}
      <Grid container spacing={3}>
        {/* Your widgets here */}
      </Grid>
    </Box>
  );
};
```

---

## 📋 Formato dos Dados de Widgets

### Metric Widget

```typescript
{
  title: "Nome do KPI",
  type: "metric",
  value: "123.45",      // Valor atual
  unit: "kWh",          // Unidade (opcional)
  trend: "+5.2%",       // Tendência (opcional)
  target: "100"         // Meta (opcional)
}
```

### Chart Widget

```typescript
{
  title: "Gráfico de Vendas",
  type: "chart",
  chart_type: "bar",    // bar, line, pie, etc
  description: "Vendas mensais",  // Opcional
  data: [
    { mes: "Jan", vendas: 1000 },
    { mes: "Fev", vendas: 1200 }
  ]
}
```

### Table Widget

```typescript
{
  title: "Lista de Itens",
  type: "table",
  headers: ["Coluna1", "Coluna2", "Coluna3"],
  data: [
    { Coluna1: "A", Coluna2: "B", Coluna3: "C" },
    // Ou array simples:
    ["A", "B", "C"]
  ]
}
```

### Status Widget

```typescript
{
  title: "Status da Operação",
  type: "status",
  status: "ok",         // ok, warning, error
  message: "Sistema funcionando normalmente"
}
```

---

## 🎨 Exemplo Completo - Dashboard Real

```typescript
import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Stack
} from '@mui/material';
import { DashboardExportButton } from '@/components/DashboardExportButton';

export const ProductionDashboard: React.FC = () => {
  // Estado com dados do dashboard
  const [metrics, setMetrics] = useState({
    efficiency: 95.2,
    availability: 98.5,
    quality: 97.8,
    oee: 91.5
  });

  const [productionData, setProductionData] = useState([
    { hour: "08:00", production: 120, quality: 98 },
    { hour: "09:00", production: 135, quality: 97 },
    { hour: "10:00", production: 142, quality: 99 }
  ]);

  const [topProducts, setTopProducts] = useState([
    { product: "Product A", quantity: 1500, revenue: 45000 },
    { product: "Product B", quantity: 1200, revenue: 36000 },
    { product: "Product C", quantity: 980, revenue: 29400 }
  ]);

  // Função para extrair dados dos widgets
  const getWidgetsData = () => {
    return [
      // Metric widgets
      {
        title: "Eficiência Operacional",
        type: "metric",
        value: metrics.efficiency.toFixed(1),
        unit: "%",
        trend: "+5.2%",
        target: "90"
      },
      {
        title: "Disponibilidade",
        type: "metric",
        value: metrics.availability.toFixed(1),
        unit: "%",
        trend: "+3.5%",
        target: "95"
      },
      {
        title: "Qualidade",
        type: "metric",
        value: metrics.quality.toFixed(1),
        unit: "%",
        trend: "+2.1%",
        target: "95"
      },
      {
        title: "OEE Global",
        type: "metric",
        value: metrics.oee.toFixed(1),
        unit: "%",
        trend: "+8.3%",
        target: "85"
      },

      // Chart widget
      {
        title: "Produção por Hora",
        type: "chart",
        chart_type: "line",
        description: "Produção e qualidade ao longo do dia",
        data: productionData
      },

      // Table widget
      {
        title: "Top 3 Produtos",
        type: "table",
        headers: ["Produto", "Quantidade", "Receita"],
        data: topProducts.map(p => ({
          "Produto": p.product,
          "Quantidade": p.quantity.toString(),
          "Receita": `R$ ${p.revenue.toLocaleString()}`
        }))
      },

      // Status widget
      {
        title: "Status Geral",
        type: "status",
        status: "ok",
        message: "Todos os sistemas operacionais"
      }
    ];
  };

  return (
    <Container maxWidth="xl">
      {/* Header com botão de exportação */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h4" fontWeight={700}>
              Dashboard de Produção
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Monitoramento em tempo real
            </Typography>
          </Box>

          <DashboardExportButton
            dashboardId="production-dashboard"
            dashboardName="Dashboard de Produção"
            getWidgetsData={getWidgetsData}
            variant="contained"
            size="large"
          />
        </Stack>
      </Paper>

      {/* Dashboard Content */}
      <Grid container spacing={3}>
        {/* Metric Cards */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Typography variant="h6">Eficiência</Typography>
              <Typography variant="h3">{metrics.efficiency}%</Typography>
              <Typography variant="caption" color="success.main">
                +5.2%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* More widgets... */}
      </Grid>
    </Container>
  );
};
```

---

## 🔌 API Endpoint

### POST /api/v1/reports/export-dashboard

**Request:**
```json
{
  "dashboard_id": "production-dashboard",
  "dashboard_name": "Dashboard de Produção",
  "format": "pdf",
  "widgets": [
    {
      "title": "Eficiência",
      "type": "metric",
      "value": "95.2",
      "unit": "%",
      "trend": "+5.2%"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Dashboard exportado com sucesso como PDF",
  "report_id": "dashboard_production-dashboard",
  "filename": "dashboard_production-dashboard_20251113_143022.pdf",
  "download_url": "/api/v1/reports/download/dashboard_production-dashboard_20251113_143022.pdf",
  "file_size_bytes": 15420
}
```

---

## 🎨 Props do Componente

### DashboardExportButton

| Prop | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| `dashboardId` | `string` | Sim | ID único do dashboard |
| `dashboardName` | `string` | Sim | Nome/título do dashboard |
| `getWidgetsData` | `() => any[]` | Sim | Função que retorna array de widgets |
| `variant` | `'text' \| 'outlined' \| 'contained'` | Não | Estilo do botão (default: 'outlined') |
| `size` | `'small' \| 'medium' \| 'large'` | Não | Tamanho do botão (default: 'medium') |

---

## 📝 Exemplos de Widget Data por Tipo

### 1. KPI Simples
```typescript
{
  title: "Total de Vendas",
  type: "metric",
  value: "R$ 125,430"
}
```

### 2. KPI com Tendência e Meta
```typescript
{
  title: "Temperatura Média",
  type: "metric",
  value: "68.5",
  unit: "°C",
  trend: "-2.3°C",
  target: "70"
}
```

### 3. Gráfico de Barras
```typescript
{
  title: "Vendas por Região",
  type: "chart",
  chart_type: "bar",
  data: [
    { regiao: "Norte", vendas: 1200 },
    { regiao: "Sul", vendas: 1500 },
    { regiao: "Leste", vendas: 980 }
  ]
}
```

### 4. Tabela Detalhada
```typescript
{
  title: "Alarmes Ativos",
  type: "table",
  headers: ["Equipamento", "Tipo", "Severidade", "Duração"],
  data: [
    {
      "Equipamento": "Máquina 1",
      "Tipo": "Temperatura Alta",
      "Severidade": "CRÍTICO",
      "Duração": "15 min"
    }
  ]
}
```

### 5. Indicador de Status
```typescript
{
  title: "Conexão OPC-UA",
  type: "status",
  status: "warning",
  message: "2 gateways com conexão intermitente"
}
```

---

## 🎯 Melhores Práticas

### 1. Performance
- Limite dados de tabelas a 50-100 linhas no export
- Para gráficos, exporte apenas dados agregados
- Use `useMemo` para a função `getWidgetsData` se for pesada

```typescript
const getWidgetsData = useMemo(() => {
  return () => {
    // Extract and format widget data
    return widgetsArray;
  };
}, [dependencies]);
```

### 2. Formatação de Dados
- Formate números antes de exportar
- Use unidades claras (%, kWh, R$, etc)
- Inclua contexto nos títulos dos widgets

### 3. Tratamento de Erros
- Valide que `getWidgetsData()` retorna array não-vazio
- Trate widgets sem dados gracefully
- Mostre mensagens de erro claras ao usuário

---

## ✅ Checklist de Implementação

- [x] Backend: Métodos de geração de relatórios de dashboard
- [x] Backend: Endpoint `/export-dashboard`
- [x] Backend: Suporte a PDF e Excel
- [x] Frontend: Componente `DashboardExportButton`
- [x] Frontend: Menu de seleção de formato
- [x] Frontend: Dialog de confirmação
- [x] Frontend: Auto-download após geração
- [x] Frontend: Feedback de sucesso/erro
- [x] Documentação: Guia completo de uso
- [x] Exemplos: Código de exemplo funcional

---

## 🏆 Sistema Pronto

**100% IMPLEMENTADO** ✅

O sistema de exportação de dashboards está completo e pronto para uso em qualquer dashboard da aplicação!

### Como Integrar em Novos Dashboards

1. Importe o componente `DashboardExportButton`
2. Crie uma função `getWidgetsData()` que retorna array de widgets
3. Adicione o botão ao header do dashboard
4. Teste exportando em PDF e Excel

**Tempo estimado de integração: 10-15 minutos por dashboard** ⚡
