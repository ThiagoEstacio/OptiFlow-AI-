/**
 * 📊 IBCS Showcase Page - Demonstração de Componentes IBCS
 * =========================================================
 *
 * Página para demonstrar todos os componentes IBCS disponíveis.
 * Útil para vendas/demos e documentação interna.
 */

import React, { useState } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Divider,
  Tab,
  Tabs,
  Alert,
  useTheme,
} from '@mui/material';
import { Grid } from '../components/GridWrapper';
import {
  IBCSBarChart,
  IBCSLineChart,
  IBCSWaterfallChart,
  IBCSKPICard,
  IBCSKPIGrid,
  IBCSColors,
  type IBCSTimeSeriesPoint,
} from '../components/ibcs';

// ========================================
// Sample Data
// ========================================

const barChartData = [
  { label: 'Jan', actual: 85, plan: 80, previousYear: 78 },
  { label: 'Fev', actual: 82, plan: 82, previousYear: 75 },
  { label: 'Mar', actual: 88, plan: 85, previousYear: 80 },
  { label: 'Abr', actual: 79, plan: 85, previousYear: 82 },
  { label: 'Mai', actual: 91, plan: 88, previousYear: 85 },
  { label: 'Jun', actual: 87, plan: 90, previousYear: 83 },
];

const lineChartData: IBCSTimeSeriesPoint[] = [
  { timestamp: '2024-01-01', actual: 85, plan: 80, previousYear: 78 },
  { timestamp: '2024-02-01', actual: 82, plan: 82, previousYear: 75 },
  { timestamp: '2024-03-01', actual: 88, plan: 85, previousYear: 80 },
  { timestamp: '2024-04-01', actual: 79, plan: 85, previousYear: 82 },
  { timestamp: '2024-05-01', actual: 91, plan: 88, previousYear: 85 },
  { timestamp: '2024-06-01', actual: 87, plan: 90, previousYear: 83 },
  { timestamp: '2024-07-01', actual: 92, plan: 90, forecast: 93 },
  { timestamp: '2024-08-01', forecast: 94, forecastLower: 91, forecastUpper: 97 },
  { timestamp: '2024-09-01', forecast: 95, forecastLower: 91, forecastUpper: 99 },
];

const waterfallData = [
  { label: 'OEE Inicial', value: 75, type: 'start' as const },
  { label: 'Red. Downtime', value: 5, type: 'positive' as const, description: 'Manutenção preventiva' },
  { label: 'Otim. Setup', value: 3, type: 'positive' as const, description: 'SMED implementado' },
  { label: 'Qualidade', value: 2, type: 'positive' as const, description: 'Controle estatístico' },
  { label: 'Falta Material', value: -2, type: 'negative' as const, description: 'Atraso fornecedor' },
  { label: 'Falha Equip.', value: -3, type: 'negative' as const, description: 'Queima motor' },
  { label: 'OEE Final', value: 80, type: 'total' as const },
];

const kpiData = [
  {
    title: 'OEE',
    value: 85.2,
    unit: '%',
    target: 85,
    previousValue: 82.5,
    status: 'good' as const,
    trend: 'up' as const,
    sparklineData: [78, 80, 82, 79, 83, 85, 85.2],
    format: 'percent' as const,
  },
  {
    title: 'Disponibilidade',
    value: 92.1,
    unit: '%',
    target: 95,
    previousValue: 91.8,
    status: 'warning' as const,
    trend: 'up' as const,
    sparklineData: [90, 91, 89, 92, 91, 92, 92.1],
    format: 'percent' as const,
  },
  {
    title: 'Performance',
    value: 88.5,
    unit: '%',
    target: 90,
    previousValue: 89.2,
    status: 'warning' as const,
    trend: 'down' as const,
    sparklineData: [87, 88, 90, 89, 88, 89, 88.5],
    format: 'percent' as const,
  },
  {
    title: 'Qualidade',
    value: 99.2,
    unit: '%',
    target: 99,
    previousValue: 98.8,
    status: 'good' as const,
    trend: 'up' as const,
    sparklineData: [98.5, 98.8, 99.0, 98.9, 99.1, 99.0, 99.2],
    format: 'percent' as const,
  },
];

// ========================================
// Main Component
// ========================================

export const IBCSShowcasePage: React.FC = () => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', pb: 4 }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          background: `linear-gradient(135deg, ${IBCSColors.actual} 0%, ${IBCSColors.actualLight} 100%)`,
          color: 'white',
          py: 3,
          mb: 3,
          borderRadius: 0,
        }}
      >
        <Container maxWidth="xl">
          <Typography variant="h4" fontWeight={700} gutterBottom>
            📊 IBCS Showcase
          </Typography>
          <Typography variant="body1" sx={{ opacity: 0.9 }}>
            International Business Communication Standards - Componentes de Visualização Profissional
          </Typography>
        </Container>
      </Paper>

      <Container maxWidth="xl">
        {/* Intro */}
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>IBCS</strong> (International Business Communication Standards) são padrões
            internacionais para visualização de dados em relatórios gerenciais.
            Os componentes abaixo seguem as melhores práticas para comunicação clara e profissional.
          </Typography>
        </Alert>

        {/* Tabs */}
        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="KPI Cards" />
          <Tab label="Bar Chart" />
          <Tab label="Line Chart" />
          <Tab label="Waterfall Chart" />
        </Tabs>

        {/* KPI Cards */}
        {activeTab === 0 && (
          <Box>
            <Typography variant="h6" gutterBottom fontWeight={600}>
              KPI Cards - Indicadores de Performance
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Cards profissionais para exibição de KPIs com variação, tendência e meta.
            </Typography>

            <IBCSKPIGrid kpis={kpiData} columns={4} gap={3} />

            <Divider sx={{ my: 4 }} />

            <Typography variant="h6" gutterBottom fontWeight={600}>
              KPI Card Individual - Modo Compacto
            </Typography>
            <Grid container spacing={2}>
              {kpiData.map((kpi, idx) => (
                <Grid item xs={6} md={3} key={idx}>
                  <IBCSKPICard {...kpi} compact />
                </Grid>
              ))}
            </Grid>
          </Box>
        )}

        {/* Bar Chart */}
        {activeTab === 1 && (
          <Box>
            <Grid container spacing={3}>
              <Grid item xs={12} lg={6}>
                <Paper sx={{ p: 3 }}>
                  <IBCSBarChart
                    data={barChartData}
                    title="OEE por Mês"
                    subtitle="Comparativo Atual vs Plano vs Ano Anterior"
                    unit="%"
                    height={350}
                    showPlan
                    showPreviousYear
                    showVariance
                  />
                </Paper>
              </Grid>

              <Grid item xs={12} lg={6}>
                <Paper sx={{ p: 3 }}>
                  <IBCSBarChart
                    data={barChartData}
                    title="Performance Mensal"
                    subtitle="Apenas valores atuais"
                    unit="%"
                    height={350}
                    orientation="horizontal"
                    targetLine={85}
                    targetLabel="Meta: 85%"
                  />
                </Paper>
              </Grid>
            </Grid>

            <Alert severity="info" sx={{ mt: 3 }}>
              <Typography variant="body2">
                <strong>Padrões IBCS aplicados:</strong>
                <br />• Barras pretas sólidas para valores atuais (AC)
                <br />• Barras com contorno para ano anterior (PY)
                <br />• Barras hachuradas para plano/orçamento (PL)
                <br />• Linha de referência para metas
              </Typography>
            </Alert>
          </Box>
        )}

        {/* Line Chart */}
        {activeTab === 2 && (
          <Box>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Paper sx={{ p: 3 }}>
                  <IBCSLineChart
                    data={lineChartData}
                    title="Tendência de OEE"
                    subtitle="Histórico, Plano e Previsão"
                    unit="%"
                    height={400}
                    showPlan
                    showPreviousYear
                    showForecast
                    showTarget
                    targetValue={90}
                    targetLabel="Meta Anual"
                    areaFill
                  />
                </Paper>
              </Grid>

              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 3 }}>
                  <IBCSLineChart
                    data={lineChartData.slice(0, 6)}
                    title="Apenas Actual"
                    subtitle="Visualização simplificada"
                    unit="%"
                    height={300}
                    showDots
                  />
                </Paper>
              </Grid>

              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 3 }}>
                  <IBCSLineChart
                    data={lineChartData.slice(0, 6)}
                    title="Com Plano"
                    subtitle="Comparativo Actual vs Plan"
                    unit="%"
                    height={300}
                    showPlan
                    showTarget
                    targetValue={88}
                  />
                </Paper>
              </Grid>
            </Grid>
          </Box>
        )}

        {/* Waterfall Chart */}
        {activeTab === 3 && (
          <Box>
            <Paper sx={{ p: 3 }}>
              <IBCSWaterfallChart
                data={waterfallData}
                title="Análise de Variação de OEE"
                subtitle="Contribuições positivas e negativas para o resultado"
                unit="%"
                height={400}
              />
            </Paper>

            <Alert severity="info" sx={{ mt: 3 }}>
              <Typography variant="body2">
                <strong>Uso do Waterfall Chart:</strong>
                <br />• Ideal para explicar variações entre dois pontos
                <br />• Verde para contribuições positivas
                <br />• Vermelho para contribuições negativas
                <br />• Preto para valores base e totais
                <br />• Perfeito para apresentações executivas
              </Typography>
            </Alert>
          </Box>
        )}

        {/* Color Legend */}
        <Box sx={{ mt: 4, p: 3, bgcolor: 'grey.50', borderRadius: 2 }}>
          <Typography variant="h6" gutterBottom fontWeight={600}>
            Paleta de Cores IBCS
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6} md={2}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 24, height: 24, bgcolor: IBCSColors.actual, borderRadius: 1 }} />
                <Typography variant="body2">Actual (AC)</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={2}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 24, height: 24, bgcolor: IBCSColors.previousYear, borderRadius: 1 }} />
                <Typography variant="body2">Previous Year (PY)</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={2}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 24, height: 24, bgcolor: IBCSColors.plan, borderRadius: 1 }} />
                <Typography variant="body2">Plan (PL)</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={2}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 24, height: 24, bgcolor: IBCSColors.positive, borderRadius: 1 }} />
                <Typography variant="body2">Positivo</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={2}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 24, height: 24, bgcolor: IBCSColors.negative, borderRadius: 1 }} />
                <Typography variant="body2">Negativo</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={2}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 24, height: 24, bgcolor: IBCSColors.forecast, borderRadius: 1 }} />
                <Typography variant="body2">Forecast (FC)</Typography>
              </Box>
            </Grid>
          </Grid>
        </Box>
      </Container>
    </Box>
  );
};

export default IBCSShowcasePage;
