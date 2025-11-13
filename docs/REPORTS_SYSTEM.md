# 📊 Sistema de Relatórios - OptiFlow AI

## Visão Geral

Sistema completo de geração e exportação de relatórios profissionais com suporte a múltiplos formatos (PDF, Excel, CSV) e templates pré-configurados.

---

## 🎯 Funcionalidades

### ✅ Templates de Relatórios Disponíveis

1. **Relatório Operacional Diário**
   - Resumo completo das operações do dia
   - Formatos: PDF, Excel, CSV
   - Tempo estimado: 30s

2. **Relatório Operacional Semanal**
   - Análise consolidada da semana
   - Formatos: PDF, Excel
   - Tempo estimado: 1min

3. **Análise de Qualidade**
   - Métricas de qualidade, defeitos e tendências
   - Formatos: PDF, Excel
   - Tempo estimado: 45s

4. **Performance de Modelos ML**
   - Acurácia, previsões e insights dos modelos
   - Formatos: PDF, Excel
   - Tempo estimado: 30s

5. **Sumário Executivo**
   - Visão geral para tomada de decisão
   - Formato: PDF
   - Tempo estimado: 1min

6. **Histórico de Alarmes**
   - Alarmes acionados, duração e resolução
   - Formatos: PDF, Excel, CSV
   - Tempo estimado: 30s

7. **Performance de Equipamentos**
   - Eficiência, disponibilidade e manutenções
   - Formatos: PDF, Excel
   - Tempo estimado: 45s

8. **Consumo de Energia**
   - Análise detalhada de consumo e eficiência energética
   - Formatos: PDF, Excel
   - Tempo estimado: 40s

---

## 📁 Arquitetura

### Backend

```
/backend/app/
├── services/
│   ├── report_generator.py              # Gerador original (operacional)
│   └── advanced_report_generator.py     # Gerador avançado (todos os tipos)
├── api/v1/endpoints/
│   └── reports.py                       # Endpoints API
└── api/v1/
    └── api.py                          # Router registration
```

### Frontend

```
/frontend/src/
└── pages/
    └── ReportsDashboard.tsx            # Dashboard de relatórios
```

### Relatórios Gerados

```
/generated_reports/                      # Diretório de saída
├── operational_20251112.pdf
├── quality_20251101_20251112.xlsx
├── ml_performance_20251112_143022.pdf
└── alarms_20251105_20251112.csv
```

---

## 🔌 API Endpoints

### 1. Listar Templates

```http
GET /api/v1/reports/templates
```

**Response:**
```json
[
  {
    "id": "operational_daily",
    "name": "Relatório Operacional Diário",
    "description": "Resumo completo das operações do dia",
    "formats": ["pdf", "excel", "csv"],
    "parameters": ["date"],
    "estimated_time": "30s"
  }
]
```

### 2. Gerar Relatório

```http
POST /api/v1/reports/generate
```

**Request Body:**
```json
{
  "report_type": "operational_daily",
  "start_date": "2025-11-12",
  "end_date": "2025-11-12",
  "format": "pdf",
  "filters": {
    "severity": "HIGH"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Relatório gerado com sucesso",
  "report_id": "operational_20251112",
  "filename": "operational_20251112.pdf",
  "download_url": "/api/v1/reports/download/operational_20251112.pdf",
  "file_size_bytes": 245760
}
```

### 3. Download de Relatório

```http
GET /api/v1/reports/download/{filename}
```

**Response:** Arquivo binário (PDF/Excel/CSV)

### 4. Histórico de Relatórios

```http
GET /api/v1/reports/history?limit=20
```

**Response:**
```json
[
  {
    "report_id": "operational_20251112",
    "report_type": "operational",
    "created_at": "2025-11-12T14:30:22",
    "filename": "operational_20251112.pdf",
    "format": "pdf",
    "file_size_bytes": 245760
  }
]
```

### 5. Deletar Relatório

```http
DELETE /api/v1/reports/{filename}
```

**Response:**
```json
{
  "success": true,
  "message": "Relatório deletado com sucesso"
}
```

---

## 💻 Uso no Frontend

### Importar o Dashboard

```typescript
import { ReportsDashboard } from './pages/ReportsDashboard';

// No App.tsx ou router
<Route path="/reports" element={<ReportsDashboard />} />
```

### Fluxo de Uso

1. **Selecionar Template**: Usuário escolhe tipo de relatório
2. **Configurar Parâmetros**: Define formato, período e filtros
3. **Gerar Relatório**: Sistema processa e cria arquivo
4. **Download Automático**: Arquivo é baixado automaticamente
5. **Histórico**: Relatório fica disponível no histórico

---

## 🎨 Interface do Usuário

### Tela Principal

```
┌─────────────────────────────────────────────┐
│ 📊 Relatórios e Exportação                  │
│ Gere relatórios profissionais em PDF, Excel│
├─────────────────────────────────────────────┤
│                                             │
│ Templates de Relatórios                     │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│ │  Daily   │ │ Quality  │ │   ML     │    │
│ │Operations│ │ Analysis │ │Performance│    │
│ │ [Gerar]  │ │ [Gerar]  │ │ [Gerar]  │    │
│ └──────────┘ └──────────┘ └──────────┘    │
│                                             │
│ Histórico de Relatórios                     │
│ • operational_20251112.pdf    [📥] [🗑️]    │
│ • quality_report.xlsx         [📥] [🗑️]    │
│ • ml_performance.pdf          [📥] [🗑️]    │
└─────────────────────────────────────────────┘
```

### Dialog de Configuração

```
┌─────────────────────────────────────┐
│ Relatório Operacional Diário        │
├─────────────────────────────────────┤
│ Formato: [PDF ▼]                    │
│ Data Inicial: [2025-11-12]          │
│ Data Final: [2025-11-12]            │
│                                     │
│ ℹ️ Tempo estimado: 30s              │
│                                     │
│         [Cancelar] [Gerar e Baixar] │
└─────────────────────────────────────┘
```

---

## 🛠️ Dependências

### Backend

```bash
# PDF Generation
pip install reportlab

# Excel Generation
pip install openpyxl

# Já instaladas no projeto
```

### Frontend

```bash
# Material-UI (já instalado)
npm install @mui/material @mui/icons-material
```

---

## 📝 Exemplo de Uso

### 1. Gerar Relatório via API

```bash
# Gerar relatório operacional em PDF
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "operational_daily",
    "start_date": "2025-11-12",
    "format": "pdf"
  }'

# Response
{
  "success": true,
  "filename": "operational_20251112.pdf",
  "download_url": "/api/v1/reports/download/operational_20251112.pdf"
}
```

### 2. Download do Relatório

```bash
# Download direto
curl -O http://localhost:8000/api/v1/reports/download/operational_20251112.pdf

# Ou abrir no navegador
open http://localhost:8000/api/v1/reports/download/operational_20251112.pdf
```

### 3. Listar Histórico

```bash
curl http://localhost:8000/api/v1/reports/history?limit=10
```

---

## 🎯 Tipos de Relatórios Detalhados

### 1. Relatório Operacional

**Conteúdo:**
- Resumo de métricas operacionais
- Eficiência e disponibilidade
- Produção e consumo de energia
- Alarmes críticos

**Tabelas:**
- Métricas vs Metas
- Status de equipamentos
- KPIs principais

### 2. Análise de Qualidade

**Conteúdo:**
- Taxa de conformidade
- Taxa de defeitos
- Produtos inspecionados
- Tempo médio de detecção

**Gráficos:**
- Tendência de qualidade
- Distribuição de defeitos
- Pareto de causas

### 3. Performance ML

**Conteúdo:**
- Acurácia dos modelos
- Previsões realizadas
- Métricas de performance (R², MAPE, etc)

**Tabelas:**
- Comparação de modelos
- Histórico de treinamentos
- Experimentos A/B

### 4. Histórico de Alarmes

**Conteúdo:**
- Alarmes por severidade
- Duração média
- Taxa de resolução
- Top 10 alarmes

**Filtros:**
- Por severidade (CRITICAL, HIGH, MEDIUM, LOW)
- Por período
- Por equipamento

---

## 🚀 Próximos Passos

### Melhorias Planejadas

1. **Agendamento Automático**
   - Envio de relatórios por email
   - Geração automática diária/semanal
   - Webhooks para integração

2. **Customização Avançada**
   - Editor de templates
   - Logos e branding personalizados
   - Campos customizáveis

3. **Mais Formatos**
   - PowerPoint (PPTX)
   - HTML interativo
   - JSON para APIs

4. **Analytics**
   - Dashboard de uso de relatórios
   - Relatórios mais acessados
   - Métricas de download

---

## ✅ Checklist de Implementação

- [x] Backend: Serviço de geração de relatórios
- [x] Backend: Suporte a PDF (reportlab)
- [x] Backend: Suporte a Excel (openpyxl)
- [x] Backend: Suporte a CSV
- [x] Backend: 8 templates pré-configurados
- [x] Backend: Endpoints API completos
- [x] Backend: Router registrado
- [x] Frontend: Dashboard de relatórios
- [x] Frontend: Interface de configuração
- [x] Frontend: Download automático
- [x] Frontend: Histórico de relatórios
- [x] Documentação completa

---

## 🏆 Score de Completude

**100% IMPLEMENTADO** ✅

- ✅ Backend completo com 8 tipos de relatórios
- ✅ 3 formatos de exportação (PDF, Excel, CSV)
- ✅ API RESTful com 5 endpoints
- ✅ Frontend dashboard profissional
- ✅ UI/UX intuitiva com Material-UI
- ✅ Download e gestão de arquivos
- ✅ Documentação técnica completa

**Sistema pronto para produção!** 🚀
