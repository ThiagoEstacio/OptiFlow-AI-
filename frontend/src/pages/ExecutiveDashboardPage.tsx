/**
 * 📊 Dashboard Executivo - Visão Gerencial e de Diretoria
 * ========================================================
 *
 * Dashboard consolidado com:
 * - KPIs principais (OEE, Disponibilidade, Performance, Qualidade)
 * - Alertas críticos em tempo real
 * - Tendências de produção
 * - Insights de ML
 * - Resumo financeiro
 *
 * Refactored to use shared hooks and utilities
 */
import React, { useState, useMemo, useCallback } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
  LinearProgress,
  Divider,
  useTheme,
  alpha,
  Stack,
  Select,
  MenuItem,
  FormControl,
  SelectChangeEvent
} from '@mui/material';
import { Grid } from '../components/GridWrapper';
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Warning,
  CheckCircle,
  Error as ErrorIcon,
  Refresh,
  Speed,
  Timer,
  Build,
  VerifiedUser,
  AttachMoney,
  Factory,
  Bolt,
  Assessment,
  Notifications,
  Info,
  ElectricBolt,
  BarChart,
  Engineering,
  PictureAsPdf
} from '@mui/icons-material';
import {
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Legend,
  PieChart,
  Pie,
  Cell,
  Bar,
  ComposedChart
} from 'recharts';
import apiClient from '../api/client';
import { useAsyncData } from '../hooks/useAsyncData';
import { REFRESH_INTERVALS } from '../utils/constants';
import { LoadingState, ErrorState } from '../components/shared';

// Sprint 6: Cross-filtering integration
import { FilterBar, DrillDownBreadcrumb, useFilterStore, useURLFilters, CrossFilterPanel } from '../components/filters';
import { ClickableKPI } from '../components/professional/ClickableKPI';
import { QualityIndicator, StaleDataBanner } from '../components/industrial/QualityIndicator';
import type { KPIType } from '../stores/dashboardSelectionStore';

// Types
interface KPIData {
  value: number;
  target: number;
  trend: 'up' | 'down' | 'stable';
  status: 'good' | 'warning' | 'critical';
}

interface ExecutiveOverview {
  status: string;
  generated_at: string;
  time_range: string;
  kpis: {
    oee: KPIData;
    availability: KPIData;
    performance: KPIData;
    quality: KPIData;
  };
  alarms: {
    total_active: number;
    by_severity: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
    trend: string;
    mttr_hours: number;
  };
  critical_equipment: Array<{
    name: string;
    alarm_count: number;
    health_score: number;
    status: string;
    last_alarm: string;
  }>;
  production_trends: {
    production_rate: { current: number; previous: number; unit: string; change_percent: number; trend: string };
    energy_efficiency: { current: number; previous: number; unit: string; change_percent: number; trend: string };
    throughput: { current: number; previous: number; unit: string; change_percent: number; trend: string };
  };
  insights: Array<{
    type: string;
    icon: string;
    title: string;
    description: string;
    impact: string;
  }>;
  financial_summary: {
    estimated_savings_today: number;
    downtime_cost_avoided: number;
    efficiency_improvement: number;
    projected_monthly_savings: number;
  };
}

interface TrendData {
  metric: string;
  period: string;
  unit: string;
  data: Array<{
    timestamp: string;
    value: number;
    target: number;
  }>;
  summary: {
    current: number;
    average: number;
    min: number;
    max: number;
    trend: string;
  };
}

// Tipos para Energia
interface EnergyData {
  current: {
    consumption_kwh: number;
    demand_kw: number;
    power_factor: number;
    status: string;
  };
  period: {
    total_kwh: number;
    average_kwh_hour: number;
    peak_demand_kw: number;
    change_percent: number;
    trend: string;
  };
  forecast: {
    monthly_kwh: number;
    confidence: number;
    peak_demand_forecast_kw: number;
  };
  bill_forecast: {
    energy_cost: number;
    demand_cost: number;
    taxes: number;
    total_estimate: number;
  };
  efficiency: {
    kwh_per_ton: number;
    cost_per_ton: number;
    target_kwh_per_ton: number;
    status: string;
  };
  peak_demand: {
    current_kw: number;
    contracted_kw: number;
    utilization_percent: number;
    risk_of_penalty: boolean;
  };
  history: Array<{
    timestamp: string;
    consumption_kwh: number;
    is_peak_hour: boolean;
  }>;
  insights: Array<{
    type: string;
    icon: string;
    title: string;
    description: string;
    recommendation: string;
  }>;
}

// Tipos para Pareto
interface ParetoData {
  summary: {
    total_alarms: number;
    unique_types: number;
    total_estimated_cost: number;
    alarms_causing_80_percent: number;
    pareto_efficiency: string;
  };
  pareto: Array<{
    rank: number;
    alarm_type: string;
    count: number;
    percent: number;
    cumulative_percent: number;
    mttr_minutes: number;
    estimated_cost: number;
    is_80_percent: boolean;
  }>;
  top_equipment: Array<{
    equipment: string;
    alarm_count: number;
    percent_of_total: number;
    status: string;
  }>;
  mttr_stats: {
    average_minutes: number;
    min_minutes: number;
    max_minutes: number;
  };
  insights: Array<{
    type: string;
    icon: string;
    title: string;
    description: string;
    recommendation: string;
  }>;
}

// Tipos para Produção
interface ProductionData {
  current: {
    throughput_ton_hour: number;
    utilization_percent: number;
    cycle_time_minutes: number;
    status: string;
  };
  period: {
    total_tons: number;
    average_ton_hour: number;
    peak_ton_hour: number;
    change_percent: number;
    trend: string;
  };
  capacity: {
    nominal_ton_hour: number;
    utilization_percent: number;
    idle_time_percent: number;
    status: string;
  };
  target: {
    production_target_tons: number;
    achievement_percent: number;
    gap_tons: number;
    status: string;
  };
  efficiency: {
    overall_efficiency: number;
    time_efficiency: number;
    performance_efficiency: number;
  };
  insights: Array<{
    type: string;
    icon: string;
    title: string;
    description: string;
    recommendation: string;
  }>;
}

// Tipos para Manutenção Preditiva
interface MaintenanceData {
  summary: {
    total_equipment: number;
    at_risk_count: number;
    average_health_score: number;
    maintenance_scheduled_7d: number;
  };
  at_risk: Array<{
    equipment_id: string;
    equipment_name: string;
    failure_probability: number;
    health_score: number;
    days_to_potential_failure: number;
    recommended_action: string;
  }>;
  equipment_health: Array<{
    equipment_id: string;
    equipment_name: string;
    equipment_type: string;
    health_score: number;
    health_status: string;
    mtbf_hours: number;
    failure_probability_7d: number;
    recommended_action: string;
  }>;
  scheduled_maintenance: Array<{
    equipment_id: string;
    equipment_name: string;
    maintenance_type: string;
    scheduled_date: string;
    days_remaining: number;
    priority: string;
  }>;
  roi: {
    failures_prevented_month: number;
    monthly_savings: number;
    system_cost: number;
    net_benefit: number;
    roi_percent: number;
  };
  insights: Array<{
    type: string;
    icon: string;
    title: string;
    description: string;
    recommendation: string;
  }>;
}

// KPI Card Component
const KPICard: React.FC<{
  title: string;
  icon: React.ReactNode;
  kpi: KPIData;
  unit?: string;
  color: string;
}> = ({ title, icon, kpi, unit = '%', color }) => {
  const theme = useTheme();

  const getStatusColor = () => {
    switch (kpi.status) {
      case 'good': return theme.palette.success.main;
      case 'warning': return theme.palette.warning.main;
      case 'critical': return theme.palette.error.main;
      default: return theme.palette.grey[500];
    }
  };

  const getTrendIcon = () => {
    switch (kpi.trend) {
      case 'up': return <TrendingUp sx={{ color: theme.palette.success.main }} />;
      case 'down': return <TrendingDown sx={{ color: theme.palette.error.main }} />;
      default: return <TrendingFlat sx={{ color: theme.palette.grey[500] }} />;
    }
  };

  const progress = Math.min((kpi.value / kpi.target) * 100, 100);

  return (
    <Card
      sx={{
        height: '100%',
        background: `linear-gradient(135deg, ${alpha(color, 0.1)} 0%, ${alpha(color, 0.05)} 100%)`,
        border: `1px solid ${alpha(color, 0.2)}`,
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: `0 8px 24px ${alpha(color, 0.3)}`
        }
      }}
    >
      <CardContent>
        <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
          <Stack direction="row" alignItems="center" spacing={1}>
            <Box
              sx={{
                bgcolor: alpha(color, 0.2),
                borderRadius: 2,
                p: 1,
                display: 'flex',
                color: color
              }}
            >
              {icon}
            </Box>
            <Typography variant="subtitle2" color="text.secondary" fontWeight={600}>
              {title}
            </Typography>
          </Stack>
          {getTrendIcon()}
        </Stack>

        <Typography variant="h3" fontWeight={700} sx={{ color: getStatusColor(), mb: 1 }}>
          {kpi.value.toFixed(1)}{unit}
        </Typography>

        <Box sx={{ mb: 1 }}>
          <Stack direction="row" justifyContent="space-between" mb={0.5}>
            <Typography variant="caption" color="text.secondary">
              Progresso para meta
            </Typography>
            <Typography variant="caption" fontWeight={600}>
              Meta: {kpi.target}{unit}
            </Typography>
          </Stack>
          <LinearProgress
            variant="determinate"
            value={progress}
            sx={{
              height: 8,
              borderRadius: 4,
              bgcolor: alpha(getStatusColor(), 0.2),
              '& .MuiLinearProgress-bar': {
                bgcolor: getStatusColor(),
                borderRadius: 4
              }
            }}
          />
        </Box>

        <Chip
          size="small"
          label={kpi.status === 'good' ? 'Dentro da meta' : kpi.status === 'warning' ? 'Atenção' : 'Crítico'}
          sx={{
            bgcolor: alpha(getStatusColor(), 0.15),
            color: getStatusColor(),
            fontWeight: 600
          }}
        />
      </CardContent>
    </Card>
  );
};

// Alert Card Component
const AlertCard: React.FC<{
  alarms: ExecutiveOverview['alarms'];
}> = ({ alarms }) => {
  const theme = useTheme();

  const severityData = [
    { name: 'Crítico', value: alarms.by_severity.critical, color: theme.palette.error.main },
    { name: 'Alto', value: alarms.by_severity.high, color: theme.palette.warning.main },
    { name: 'Médio', value: alarms.by_severity.medium, color: theme.palette.info.main },
    { name: 'Baixo', value: alarms.by_severity.low, color: theme.palette.success.main }
  ];

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={1} mb={2}>
          <Notifications color="warning" />
          <Typography variant="h6" fontWeight={600}>
            Status de Alarmes
          </Typography>
        </Stack>

        <Stack direction="row" spacing={3} alignItems="center">
          <Box sx={{ width: 120, height: 120 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={severityData}
                  innerRadius={35}
                  outerRadius={50}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </Box>

          <Box flex={1}>
            <Typography variant="h4" fontWeight={700} color="warning.main">
              {alarms.total_active}
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={2}>
              Alarmes Ativos
            </Typography>

            <Stack spacing={0.5}>
              {severityData.map((item) => (
                <Stack key={item.name} direction="row" justifyContent="space-between" alignItems="center">
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: item.color }} />
                    <Typography variant="caption">{item.name}</Typography>
                  </Stack>
                  <Typography variant="caption" fontWeight={600}>{item.value}</Typography>
                </Stack>
              ))}
            </Stack>
          </Box>
        </Stack>

        <Divider sx={{ my: 2 }} />

        <Stack direction="row" justifyContent="space-between">
          <Box>
            <Typography variant="caption" color="text.secondary">MTTR Médio</Typography>
            <Typography variant="body1" fontWeight={600}>{alarms.mttr_hours}h</Typography>
          </Box>
          <Box textAlign="right">
            <Typography variant="caption" color="text.secondary">Tendência</Typography>
            <Stack direction="row" alignItems="center" justifyContent="flex-end">
              {alarms.trend === 'down' ? (
                <TrendingDown sx={{ color: 'success.main', fontSize: 16 }} />
              ) : (
                <TrendingUp sx={{ color: 'error.main', fontSize: 16 }} />
              )}
              <Typography variant="body1" fontWeight={600}>
                {alarms.trend === 'down' ? 'Reduzindo' : 'Aumentando'}
              </Typography>
            </Stack>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
};

// Insight Card Component
const InsightCard: React.FC<{
  insight: ExecutiveOverview['insights'][0];
}> = ({ insight }) => {
  const theme = useTheme();

  const getTypeColor = () => {
    switch (insight.type) {
      case 'success': return theme.palette.success.main;
      case 'warning': return theme.palette.warning.main;
      case 'critical': return theme.palette.error.main;
      default: return theme.palette.info.main;
    }
  };

  const getIcon = () => {
    switch (insight.type) {
      case 'success': return <CheckCircle />;
      case 'warning': return <Warning />;
      case 'critical': return <ErrorIcon />;
      default: return <Info />;
    }
  };

  return (
    <Paper
      sx={{
        p: 2,
        borderLeft: `4px solid ${getTypeColor()}`,
        bgcolor: alpha(getTypeColor(), 0.05),
        mb: 1
      }}
    >
      <Stack direction="row" spacing={2}>
        <Box sx={{ color: getTypeColor() }}>{getIcon()}</Box>
        <Box flex={1}>
          <Typography variant="subtitle2" fontWeight={600}>
            {insight.title}
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={0.5}>
            {insight.description}
          </Typography>
          <Typography variant="caption" sx={{ color: getTypeColor() }}>
            {insight.impact}
          </Typography>
        </Box>
      </Stack>
    </Paper>
  );
};

// Financial Summary Component
const FinancialSummary: React.FC<{
  financial: ExecutiveOverview['financial_summary'];
}> = ({ financial }) => {
  const theme = useTheme();

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  return (
    <Card sx={{ height: '100%', bgcolor: alpha(theme.palette.success.main, 0.05) }}>
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={1} mb={3}>
          <AttachMoney color="success" />
          <Typography variant="h6" fontWeight={600}>
            Resumo Financeiro
          </Typography>
        </Stack>

        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'background.paper' }}>
              <Typography variant="caption" color="text.secondary">
                Economia Hoje
              </Typography>
              <Typography variant="h5" fontWeight={700} color="success.main">
                {formatCurrency(financial.estimated_savings_today)}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'background.paper' }}>
              <Typography variant="caption" color="text.secondary">
                Custo Evitado
              </Typography>
              <Typography variant="h5" fontWeight={700} color="primary.main">
                {formatCurrency(financial.downtime_cost_avoided)}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'background.paper' }}>
              <Typography variant="caption" color="text.secondary">
                Melhoria Eficiência
              </Typography>
              <Typography variant="h5" fontWeight={700} color="info.main">
                +{financial.efficiency_improvement.toFixed(1)}%
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'background.paper' }}>
              <Typography variant="caption" color="text.secondary">
                Projeção Mensal
              </Typography>
              <Typography variant="h5" fontWeight={700} color="success.dark">
                {formatCurrency(financial.projected_monthly_savings)}
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

// Equipment Health Component
const EquipmentHealth: React.FC<{
  equipment: ExecutiveOverview['critical_equipment'];
}> = ({ equipment }) => {
  const theme = useTheme();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical': return theme.palette.error.main;
      case 'warning': return theme.palette.warning.main;
      default: return theme.palette.success.main;
    }
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={1} mb={2}>
          <Factory color="primary" />
          <Typography variant="h6" fontWeight={600}>
            Saúde dos Equipamentos
          </Typography>
        </Stack>

        <Stack spacing={1}>
          {equipment.map((eq, idx) => (
            <Paper
              key={idx}
              sx={{
                p: 1.5,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                bgcolor: alpha(getStatusColor(eq.status), 0.05),
                border: `1px solid ${alpha(getStatusColor(eq.status), 0.2)}`
              }}
            >
              <Stack direction="row" alignItems="center" spacing={2}>
                <Box
                  sx={{
                    width: 40,
                    height: 40,
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    bgcolor: alpha(getStatusColor(eq.status), 0.15)
                  }}
                >
                  <Build sx={{ color: getStatusColor(eq.status) }} />
                </Box>
                <Box>
                  <Typography variant="subtitle2" fontWeight={600}>
                    {eq.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {eq.alarm_count} alarmes • {eq.last_alarm}
                  </Typography>
                </Box>
              </Stack>

              <Box textAlign="right">
                <Typography variant="h6" fontWeight={700} sx={{ color: getStatusColor(eq.status) }}>
                  {eq.health_score}%
                </Typography>
                <Chip
                  size="small"
                  label={eq.status === 'critical' ? 'Crítico' : eq.status === 'warning' ? 'Atenção' : 'Normal'}
                  sx={{
                    bgcolor: alpha(getStatusColor(eq.status), 0.15),
                    color: getStatusColor(eq.status),
                    fontSize: '0.65rem',
                    height: 20
                  }}
                />
              </Box>
            </Paper>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
};

// Energy Section Component
const EnergySection: React.FC<{
  energy: EnergyData;
}> = ({ energy }) => {
  const theme = useTheme();

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatNumber = (value: number, decimals = 0) => {
    return new Intl.NumberFormat('pt-BR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(value);
  };

  return (
    <Card>
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={1} mb={3}>
          <ElectricBolt sx={{ color: theme.palette.warning.main }} />
          <Typography variant="h6" fontWeight={600}>
            Energia & Custos
          </Typography>
        </Stack>

        <Grid container spacing={3}>
          {/* Consumo Atual */}
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, bgcolor: alpha(theme.palette.warning.main, 0.05), height: '100%' }}>
              <Typography variant="caption" color="text.secondary">Consumo Atual</Typography>
              <Typography variant="h4" fontWeight={700} color="warning.main">
                {formatNumber(energy.current.consumption_kwh, 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">kWh</Typography>
              <Divider sx={{ my: 1.5 }} />
              <Stack spacing={0.5}>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption">Demanda</Typography>
                  <Typography variant="caption" fontWeight={600}>{formatNumber(energy.current.demand_kw, 0)} kW</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption">Fator Potência</Typography>
                  <Typography variant="caption" fontWeight={600}>{energy.current.power_factor}</Typography>
                </Stack>
              </Stack>
            </Paper>
          </Grid>

          {/* Forecast Mensal */}
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, bgcolor: alpha(theme.palette.info.main, 0.05), height: '100%' }}>
              <Typography variant="caption" color="text.secondary">Forecast Mensal</Typography>
              <Typography variant="h4" fontWeight={700} color="info.main">
                {formatNumber(energy.forecast.monthly_kwh / 1000, 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">MWh</Typography>
              <Divider sx={{ my: 1.5 }} />
              <Stack spacing={0.5}>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption">Confiança</Typography>
                  <Typography variant="caption" fontWeight={600}>{energy.forecast.confidence}%</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption">Pico Previsto</Typography>
                  <Typography variant="caption" fontWeight={600}>{formatNumber(energy.forecast.peak_demand_forecast_kw, 0)} kW</Typography>
                </Stack>
              </Stack>
            </Paper>
          </Grid>

          {/* Previsão Conta de Luz */}
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, bgcolor: alpha(theme.palette.error.main, 0.05), height: '100%' }}>
              <Typography variant="caption" color="text.secondary">Previsão Conta de Luz</Typography>
              <Typography variant="h4" fontWeight={700} color="error.main">
                {formatCurrency(energy.bill_forecast.total_estimate)}
              </Typography>
              <Typography variant="body2" color="text.secondary">estimado</Typography>
              <Divider sx={{ my: 1.5 }} />
              <Stack spacing={0.5}>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption">Energia</Typography>
                  <Typography variant="caption" fontWeight={600}>{formatCurrency(energy.bill_forecast.energy_cost)}</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption">Demanda</Typography>
                  <Typography variant="caption" fontWeight={600}>{formatCurrency(energy.bill_forecast.demand_cost)}</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption">Impostos</Typography>
                  <Typography variant="caption" fontWeight={600}>{formatCurrency(energy.bill_forecast.taxes)}</Typography>
                </Stack>
              </Stack>
            </Paper>
          </Grid>

          {/* Eficiência */}
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, bgcolor: alpha(theme.palette.success.main, 0.05), height: '100%' }}>
              <Typography variant="caption" color="text.secondary">Eficiência Energética</Typography>
              <Typography variant="h4" fontWeight={700} sx={{
                color: energy.efficiency.status === 'good' ? 'success.main' :
                       energy.efficiency.status === 'warning' ? 'warning.main' : 'error.main'
              }}>
                {energy.efficiency.kwh_per_ton.toFixed(2)}
              </Typography>
              <Typography variant="body2" color="text.secondary">kWh/ton</Typography>
              <Divider sx={{ my: 1.5 }} />
              <Stack spacing={0.5}>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption">Meta</Typography>
                  <Typography variant="caption" fontWeight={600}>{energy.efficiency.target_kwh_per_ton} kWh/ton</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption">Custo/ton</Typography>
                  <Typography variant="caption" fontWeight={600}>{formatCurrency(energy.efficiency.cost_per_ton)}</Typography>
                </Stack>
              </Stack>
            </Paper>
          </Grid>
        </Grid>

        {/* Pico de Demanda Alert */}
        {energy.peak_demand.risk_of_penalty && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            <strong>Atenção:</strong> Demanda atual ({formatNumber(energy.peak_demand.current_kw, 0)} kW) próxima do limite contratado ({formatNumber(energy.peak_demand.contracted_kw, 0)} kW).
            Risco de multa por ultrapassagem!
          </Alert>
        )}

        {/* Insights de Energia */}
        {energy.insights && energy.insights.length > 0 && (
          <Box mt={2}>
            <Typography variant="subtitle2" color="text.secondary" mb={1}>Insights</Typography>
            <Stack spacing={1}>
              {energy.insights.slice(0, 3).map((insight, idx) => (
                <Paper
                  key={idx}
                  sx={{
                    p: 1.5,
                    borderLeft: `3px solid ${
                      insight.type === 'success' ? theme.palette.success.main :
                      insight.type === 'warning' ? theme.palette.warning.main :
                      insight.type === 'critical' ? theme.palette.error.main : theme.palette.info.main
                    }`,
                    bgcolor: alpha(
                      insight.type === 'success' ? theme.palette.success.main :
                      insight.type === 'warning' ? theme.palette.warning.main :
                      insight.type === 'critical' ? theme.palette.error.main : theme.palette.info.main,
                      0.05
                    )
                  }}
                >
                  <Typography variant="body2" fontWeight={600}>{insight.title}</Typography>
                  <Typography variant="caption" color="text.secondary">{insight.recommendation}</Typography>
                </Paper>
              ))}
            </Stack>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

// Pareto Chart Component
const ParetoSection: React.FC<{
  pareto: ParetoData;
}> = ({ pareto }) => {
  const theme = useTheme();

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  // Preparar dados para o gráfico de Pareto
  const chartData = pareto.pareto.map(item => ({
    name: item.alarm_type.length > 15 ? item.alarm_type.substring(0, 15) + '...' : item.alarm_type,
    count: item.count,
    cumulative: item.cumulative_percent,
    is80: item.is_80_percent
  }));

  return (
    <Card>
      <CardContent>
        <Stack direction="row" alignItems="center" justifyContent="space-between" mb={3}>
          <Stack direction="row" alignItems="center" spacing={1}>
            <BarChart sx={{ color: theme.palette.primary.main }} />
            <Typography variant="h6" fontWeight={600}>
              Pareto de Alarmes
            </Typography>
          </Stack>
          <Chip
            label={pareto.summary.pareto_efficiency}
            size="small"
            color="primary"
            variant="outlined"
          />
        </Stack>

        <Grid container spacing={3}>
          {/* Gráfico de Pareto */}
          <Grid item xs={12} lg={8}>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer>
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 10 }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis
                    yAxisId="left"
                    orientation="left"
                    label={{ value: 'Quantidade', angle: -90, position: 'insideLeft', fontSize: 12 }}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    domain={[0, 100]}
                    label={{ value: '% Acumulado', angle: 90, position: 'insideRight', fontSize: 12 }}
                  />
                  <RechartsTooltip
                    contentStyle={{
                      backgroundColor: theme.palette.background.paper,
                      border: `1px solid ${theme.palette.divider}`
                    }}
                  />
                  <Bar
                    yAxisId="left"
                    dataKey="count"
                    fill={theme.palette.primary.main}
                    name="Ocorrências"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="cumulative"
                    stroke={theme.palette.error.main}
                    strokeWidth={2}
                    dot={{ fill: theme.palette.error.main }}
                    name="% Acumulado"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </Box>
          </Grid>

          {/* Resumo e Top Equipamentos */}
          <Grid item xs={12} lg={4}>
            {/* Resumo */}
            <Paper sx={{ p: 2, mb: 2, bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
              <Typography variant="subtitle2" fontWeight={600} mb={1}>Resumo</Typography>
              <Stack spacing={0.5}>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2">Total de Alarmes</Typography>
                  <Typography variant="body2" fontWeight={600}>{pareto.summary.total_alarms}</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2">Tipos Únicos</Typography>
                  <Typography variant="body2" fontWeight={600}>{pareto.summary.unique_types}</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2">Custo Estimado</Typography>
                  <Typography variant="body2" fontWeight={600} color="error.main">
                    {formatCurrency(pareto.summary.total_estimated_cost)}
                  </Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2">MTTR Médio</Typography>
                  <Typography variant="body2" fontWeight={600}>{pareto.mttr_stats.average_minutes} min</Typography>
                </Stack>
              </Stack>
            </Paper>

            {/* Top Equipamentos */}
            <Paper sx={{ p: 2, bgcolor: alpha(theme.palette.warning.main, 0.05) }}>
              <Typography variant="subtitle2" fontWeight={600} mb={1}>Top Equipamentos</Typography>
              <Stack spacing={1}>
                {pareto.top_equipment.slice(0, 4).map((equip, idx) => (
                  <Stack key={idx} direction="row" justifyContent="space-between" alignItems="center">
                    <Stack direction="row" alignItems="center" spacing={1}>
                      <Typography variant="body2" sx={{
                        color: equip.status === 'critical' ? 'error.main' :
                               equip.status === 'warning' ? 'warning.main' : 'text.primary'
                      }}>
                        {equip.equipment}
                      </Typography>
                    </Stack>
                    <Chip
                      size="small"
                      label={`${equip.alarm_count}`}
                      sx={{
                        bgcolor: equip.status === 'critical' ? alpha(theme.palette.error.main, 0.1) :
                                equip.status === 'warning' ? alpha(theme.palette.warning.main, 0.1) :
                                alpha(theme.palette.success.main, 0.1),
                        fontSize: '0.7rem'
                      }}
                    />
                  </Stack>
                ))}
              </Stack>
            </Paper>
          </Grid>
        </Grid>

        {/* Insights do Pareto */}
        {pareto.insights && pareto.insights.length > 0 && (
          <Box mt={2}>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {pareto.insights.slice(0, 2).map((insight, idx) => (
                <Chip
                  key={idx}
                  icon={insight.type === 'critical' ? <Warning /> : <Info />}
                  label={insight.title}
                  size="small"
                  color={insight.type === 'critical' ? 'error' : insight.type === 'warning' ? 'warning' : 'info'}
                  variant="outlined"
                  sx={{ mt: 1 }}
                />
              ))}
            </Stack>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

// Production Metrics Component
const ProductionSection: React.FC<{
  production: ProductionData;
}> = ({ production }) => {
  const theme = useTheme();

  const formatNumber = (value: number, decimals = 0) => {
    return new Intl.NumberFormat('pt-BR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(value);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return theme.palette.success.main;
      case 'warning': return theme.palette.warning.main;
      case 'critical': return theme.palette.error.main;
      default: return theme.palette.grey[500];
    }
  };

  return (
    <Card>
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={1} mb={3}>
          <Factory sx={{ color: theme.palette.primary.main }} />
          <Typography variant="h6" fontWeight={600}>
            Métricas de Produção
          </Typography>
        </Stack>

        <Grid container spacing={2}>
          {/* Throughput Atual */}
          <Grid item xs={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
              <Typography variant="caption" color="text.secondary">Throughput Atual</Typography>
              <Typography variant="h4" fontWeight={700} color="primary.main">
                {formatNumber(production.current.throughput_ton_hour, 1)}
              </Typography>
              <Typography variant="body2" color="text.secondary">ton/hora</Typography>
              <Chip
                size="small"
                label={production.current.status === 'good' ? 'Normal' : 'Atenção'}
                sx={{
                  mt: 1,
                  bgcolor: alpha(getStatusColor(production.current.status), 0.15),
                  color: getStatusColor(production.current.status)
                }}
              />
            </Paper>
          </Grid>

          {/* Produção Total */}
          <Grid item xs={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: alpha(theme.palette.success.main, 0.05) }}>
              <Typography variant="caption" color="text.secondary">Produção Total</Typography>
              <Typography variant="h4" fontWeight={700} color="success.main">
                {formatNumber(production.period.total_tons)}
              </Typography>
              <Typography variant="body2" color="text.secondary">toneladas</Typography>
              <Stack direction="row" justifyContent="center" alignItems="center" spacing={0.5} mt={1}>
                {production.period.trend === 'up' ? (
                  <TrendingUp sx={{ color: 'success.main', fontSize: 16 }} />
                ) : (
                  <TrendingDown sx={{ color: 'error.main', fontSize: 16 }} />
                )}
                <Typography variant="caption" sx={{
                  color: production.period.trend === 'up' ? 'success.main' : 'error.main'
                }}>
                  {production.period.change_percent > 0 ? '+' : ''}{production.period.change_percent.toFixed(1)}%
                </Typography>
              </Stack>
            </Paper>
          </Grid>

          {/* Utilização */}
          <Grid item xs={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: alpha(theme.palette.info.main, 0.05) }}>
              <Typography variant="caption" color="text.secondary">Utilização</Typography>
              <Typography variant="h4" fontWeight={700} color="info.main">
                {production.capacity.utilization_percent.toFixed(0)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">da capacidade</Typography>
              <LinearProgress
                variant="determinate"
                value={Math.min(production.capacity.utilization_percent, 100)}
                sx={{
                  mt: 1,
                  height: 6,
                  borderRadius: 3,
                  bgcolor: alpha(theme.palette.info.main, 0.2),
                  '& .MuiLinearProgress-bar': {
                    bgcolor: getStatusColor(production.capacity.status)
                  }
                }}
              />
            </Paper>
          </Grid>

          {/* Atingimento Meta */}
          <Grid item xs={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: alpha(getStatusColor(production.target.status), 0.05) }}>
              <Typography variant="caption" color="text.secondary">Meta</Typography>
              <Typography variant="h4" fontWeight={700} sx={{ color: getStatusColor(production.target.status) }}>
                {production.target.achievement_percent.toFixed(0)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">atingido</Typography>
              {production.target.gap_tons > 0 ? (
                <Typography variant="caption" color="error.main">
                  Gap: {formatNumber(production.target.gap_tons)} ton
                </Typography>
              ) : (
                <Typography variant="caption" color="success.main">
                  +{formatNumber(Math.abs(production.target.gap_tons))} ton
                </Typography>
              )}
            </Paper>
          </Grid>
        </Grid>

        {/* Eficiência */}
        <Box mt={2}>
          <Stack direction="row" spacing={2} justifyContent="center">
            <Chip
              label={`Eficiência Global: ${production.efficiency.overall_efficiency.toFixed(1)}%`}
              color="primary"
              variant="outlined"
            />
            <Chip
              label={`Tempo de Ciclo: ${production.current.cycle_time_minutes} min`}
              color="secondary"
              variant="outlined"
            />
            <Chip
              label={`Capacidade: ${production.capacity.nominal_ton_hour} ton/h`}
              color="default"
              variant="outlined"
            />
          </Stack>
        </Box>
      </CardContent>
    </Card>
  );
};

// Predictive Maintenance Component
const MaintenanceSection: React.FC<{
  maintenance: MaintenanceData;
}> = ({ maintenance }) => {
  const theme = useTheme();

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const getHealthColor = (score: number) => {
    if (score >= 80) return theme.palette.success.main;
    if (score >= 60) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  const getPriorityColor = (priority: string) => {
    return priority === 'high' ? theme.palette.error.main : theme.palette.warning.main;
  };

  return (
    <Card>
      <CardContent>
        <Stack direction="row" alignItems="center" justifyContent="space-between" mb={3}>
          <Stack direction="row" alignItems="center" spacing={1}>
            <Engineering sx={{ color: theme.palette.primary.main }} />
            <Typography variant="h6" fontWeight={600}>
              Manutenção Preditiva
            </Typography>
          </Stack>
          <Chip
            label={`ROI: ${maintenance.roi.roi_percent.toFixed(0)}%`}
            color="success"
            size="small"
          />
        </Stack>

        <Grid container spacing={3}>
          {/* Resumo */}
          <Grid item xs={12} md={3}>
            <Stack spacing={2}>
              {/* KPIs de Manutenção */}
              <Paper sx={{ p: 2, bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
                <Typography variant="subtitle2" fontWeight={600} mb={1}>Visão Geral</Typography>
                <Stack spacing={1}>
                  <Stack direction="row" justifyContent="space-between">
                    <Typography variant="body2">Equipamentos</Typography>
                    <Typography variant="body2" fontWeight={600}>{maintenance.summary.total_equipment}</Typography>
                  </Stack>
                  <Stack direction="row" justifyContent="space-between">
                    <Typography variant="body2">Em Risco</Typography>
                    <Typography variant="body2" fontWeight={600} color="error.main">
                      {maintenance.summary.at_risk_count}
                    </Typography>
                  </Stack>
                  <Stack direction="row" justifyContent="space-between">
                    <Typography variant="body2">Health Médio</Typography>
                    <Typography variant="body2" fontWeight={600} sx={{ color: getHealthColor(maintenance.summary.average_health_score) }}>
                      {maintenance.summary.average_health_score.toFixed(0)}%
                    </Typography>
                  </Stack>
                  <Stack direction="row" justifyContent="space-between">
                    <Typography variant="body2">Manutenções 7d</Typography>
                    <Typography variant="body2" fontWeight={600}>{maintenance.summary.maintenance_scheduled_7d}</Typography>
                  </Stack>
                </Stack>
              </Paper>

              {/* ROI */}
              <Paper sx={{ p: 2, bgcolor: alpha(theme.palette.success.main, 0.05) }}>
                <Typography variant="subtitle2" fontWeight={600} mb={1}>Retorno do Sistema</Typography>
                <Stack spacing={0.5}>
                  <Stack direction="row" justifyContent="space-between">
                    <Typography variant="caption">Falhas Evitadas</Typography>
                    <Typography variant="caption" fontWeight={600}>{maintenance.roi.failures_prevented_month}/mês</Typography>
                  </Stack>
                  <Stack direction="row" justifyContent="space-between">
                    <Typography variant="caption">Economia</Typography>
                    <Typography variant="caption" fontWeight={600} color="success.main">
                      {formatCurrency(maintenance.roi.monthly_savings)}
                    </Typography>
                  </Stack>
                  <Stack direction="row" justifyContent="space-between">
                    <Typography variant="caption">Benefício Líquido</Typography>
                    <Typography variant="caption" fontWeight={600} color="success.main">
                      {formatCurrency(maintenance.roi.net_benefit)}
                    </Typography>
                  </Stack>
                </Stack>
              </Paper>
            </Stack>
          </Grid>

          {/* Equipamentos em Risco */}
          <Grid item xs={12} md={5}>
            <Paper sx={{ p: 2, height: '100%' }}>
              <Stack direction="row" alignItems="center" spacing={1} mb={2}>
                <Warning color="error" sx={{ fontSize: 20 }} />
                <Typography variant="subtitle2" fontWeight={600}>Equipamentos em Risco</Typography>
              </Stack>
              <Stack spacing={1.5}>
                {maintenance.at_risk.length > 0 ? (
                  maintenance.at_risk.slice(0, 4).map((equip, idx) => (
                    <Paper
                      key={idx}
                      sx={{
                        p: 1.5,
                        bgcolor: alpha(theme.palette.error.main, 0.05),
                        border: `1px solid ${alpha(theme.palette.error.main, 0.2)}`
                      }}
                    >
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Box>
                          <Typography variant="body2" fontWeight={600}>{equip.equipment_name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {equip.recommended_action}
                          </Typography>
                        </Box>
                        <Stack alignItems="flex-end">
                          <Chip
                            size="small"
                            label={`${equip.failure_probability}% risco`}
                            sx={{
                              bgcolor: alpha(theme.palette.error.main, 0.15),
                              color: theme.palette.error.main,
                              fontSize: '0.65rem'
                            }}
                          />
                          <Typography variant="caption" color="text.secondary" mt={0.5}>
                            ~{equip.days_to_potential_failure}d para falha
                          </Typography>
                        </Stack>
                      </Stack>
                    </Paper>
                  ))
                ) : (
                  <Alert severity="success" sx={{ py: 0.5 }}>
                    Nenhum equipamento em risco crítico
                  </Alert>
                )}
              </Stack>
            </Paper>
          </Grid>

          {/* Próximas Manutenções */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, height: '100%' }}>
              <Stack direction="row" alignItems="center" spacing={1} mb={2}>
                <Timer color="primary" sx={{ fontSize: 20 }} />
                <Typography variant="subtitle2" fontWeight={600}>Manutenções Programadas</Typography>
              </Stack>
              <Stack spacing={1}>
                {maintenance.scheduled_maintenance.length > 0 ? (
                  maintenance.scheduled_maintenance.slice(0, 4).map((maint, idx) => (
                    <Stack
                      key={idx}
                      direction="row"
                      justifyContent="space-between"
                      alignItems="center"
                      sx={{
                        p: 1,
                        borderRadius: 1,
                        bgcolor: alpha(getPriorityColor(maint.priority), 0.05),
                        borderLeft: `3px solid ${getPriorityColor(maint.priority)}`
                      }}
                    >
                      <Box>
                        <Typography variant="body2" fontWeight={600}>{maint.equipment_name}</Typography>
                        <Typography variant="caption" color="text.secondary">{maint.maintenance_type}</Typography>
                      </Box>
                      <Stack alignItems="flex-end">
                        <Typography variant="caption" fontWeight={600}>
                          {maint.days_remaining}d
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(maint.scheduled_date).toLocaleDateString('pt-BR')}
                        </Typography>
                      </Stack>
                    </Stack>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Nenhuma manutenção programada
                  </Typography>
                )}
              </Stack>
            </Paper>
          </Grid>
        </Grid>

        {/* Health dos Equipamentos - Barra de Progresso */}
        <Box mt={2}>
          <Typography variant="subtitle2" fontWeight={600} mb={1}>Health dos Equipamentos</Typography>
          <Grid container spacing={1}>
            {maintenance.equipment_health.slice(0, 6).map((equip, idx) => (
              <Grid item xs={6} md={2} key={idx}>
                <Tooltip title={`${equip.equipment_type} - ${equip.recommended_action}`}>
                  <Paper sx={{ p: 1, textAlign: 'center' }}>
                    <Typography variant="caption" noWrap>{equip.equipment_name}</Typography>
                    <Box sx={{ position: 'relative', display: 'inline-flex', mt: 0.5 }}>
                      <CircularProgress
                        variant="determinate"
                        value={equip.health_score}
                        size={40}
                        sx={{ color: getHealthColor(equip.health_score) }}
                      />
                      <Box
                        sx={{
                          top: 0,
                          left: 0,
                          bottom: 0,
                          right: 0,
                          position: 'absolute',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <Typography variant="caption" fontWeight={600} sx={{ fontSize: '0.6rem' }}>
                          {equip.health_score}%
                        </Typography>
                      </Box>
                    </Box>
                  </Paper>
                </Tooltip>
              </Grid>
            ))}
          </Grid>
        </Box>
      </CardContent>
    </Card>
  );
};

// Main Component
export const ExecutiveDashboardPage: React.FC = () => {
  const theme = useTheme();
  const [selectedMetric, setSelectedMetric] = useState('oee');
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  // Sprint 6: Global filter store integration
  const {
    timeRange: globalTimeRange,
    selectedEquipments,
    setTimeRangePreset,
  } = useFilterStore();
  useURLFilters({ enabled: true });

  // Map global time range to API format
  const timeRange = globalTimeRange.preset;

  // Fetch all executive data using the shared hook
  const fetchExecutiveData = useCallback(async () => {
    const [overviewRes, trendsRes, energyRes, paretoRes, productionRes, maintenanceRes] = await Promise.all([
      apiClient.get(`/api/v1/executive-summary/overview?time_range=${timeRange}`),
      apiClient.get(`/api/v1/executive-summary/trends?metric=${selectedMetric}&period=${timeRange === '24h' ? '24h' : '7d'}`),
      apiClient.get(`/api/v1/executive-summary/energy?time_range=${timeRange}`),
      apiClient.get(`/api/v1/executive-summary/alarms/pareto?time_range=${timeRange}`),
      apiClient.get(`/api/v1/executive-summary/production?time_range=${timeRange}`),
      apiClient.get(`/api/v1/executive-summary/maintenance/predictive`)
    ]);

    return {
      overview: overviewRes.data as ExecutiveOverview,
      trendData: trendsRes.data as TrendData,
      energyData: energyRes.data as EnergyData,
      paretoData: paretoRes.data as ParetoData,
      productionData: productionRes.data as ProductionData,
      maintenanceData: maintenanceRes.data as MaintenanceData,
    };
  }, [timeRange, selectedMetric]);

  const {
    data: executiveData,
    loading,
    error,
    refresh: loadData,
    isRetrying,
  } = useAsyncData(fetchExecutiveData, {
    autoRefresh: true,
    refreshInterval: REFRESH_INTERVALS.ANALYTICS, // 60 seconds
    deps: [timeRange, selectedMetric],
    keepPreviousData: true,
  });

  // Extract data from the combined result
  const overview = executiveData?.overview ?? null;
  const trendData = executiveData?.trendData ?? null;
  const energyData = executiveData?.energyData ?? null;
  const paretoData = executiveData?.paretoData ?? null;
  const productionData = executiveData?.productionData ?? null;
  const maintenanceData = executiveData?.maintenanceData ?? null;

  // Função para exportar relatório PDF
  const handleExportPDF = useCallback(async () => {
    setExporting(true);
    setExportError(null);
    try {
      const response = await apiClient.get(`/api/v1/executive-report/generate?time_range=${timeRange}`, {
        responseType: 'blob'
      });

      // Criar link de download
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `relatorio_executivo_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Erro ao exportar relatório:', err);
      setExportError('Erro ao gerar relatório PDF');
    } finally {
      setExporting(false);
    }
  }, [timeRange]);

  const handleTimeRangeChange = (event: SelectChangeEvent) => {
    // Sprint 6: Use global filter store
    const value = event.target.value as '1h' | '4h' | '8h' | '24h' | '7d' | '30d';
    setTimeRangePreset(value);
  };

  // Loading state
  if (loading && !overview) {
    return (
      <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', pt: 4 }}>
        <LoadingState message="Carregando dados executivos..." size="lg" />
      </Box>
    );
  }

  // Error state (only show if no data at all)
  if (error && !overview) {
    return (
      <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', pt: 4 }}>
        <ErrorState
          message={error}
          onRetry={loadData}
          isRetrying={isRetrying}
        />
      </Box>
    );
  }

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', pb: 4 }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 100%)`,
          color: 'white',
          py: 3,
          mb: 3,
          borderRadius: 0
        }}
      >
        <Container maxWidth="xl">
          <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
            <Box>
              <Stack direction="row" alignItems="center" spacing={2} mb={1}>
                <Assessment sx={{ fontSize: 40 }} />
                <Typography variant="h4" fontWeight={700}>
                  Dashboard Executivo
                </Typography>
              </Stack>
              <Typography variant="body1" sx={{ opacity: 0.9 }}>
                Visão consolidada para gerência e diretoria
              </Typography>
              {overview && (
                <Typography variant="caption" sx={{ opacity: 0.7 }}>
                  Atualizado em: {new Date(overview.generated_at).toLocaleString('pt-BR')}
                </Typography>
              )}
            </Box>

            <Stack direction="row" spacing={2} alignItems="center">
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <Select
                  value={timeRange}
                  onChange={handleTimeRangeChange}
                  sx={{
                    bgcolor: 'rgba(255,255,255,0.1)',
                    color: 'white',
                    '& .MuiSelect-icon': { color: 'white' }
                  }}
                >
                  <MenuItem value="1h">Última hora</MenuItem>
                  <MenuItem value="6h">Últimas 6h</MenuItem>
                  <MenuItem value="24h">Últimas 24h</MenuItem>
                  <MenuItem value="7d">Últimos 7 dias</MenuItem>
                  <MenuItem value="30d">Últimos 30 dias</MenuItem>
                </Select>
              </FormControl>

              <Tooltip title="Atualizar">
                <IconButton
                  onClick={loadData}
                  sx={{
                    bgcolor: 'rgba(255,255,255,0.1)',
                    color: 'white',
                    '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' }
                  }}
                >
                  <Refresh />
                </IconButton>
              </Tooltip>

              <Tooltip title="Exportar Relatório PDF">
                <IconButton
                  onClick={handleExportPDF}
                  disabled={exporting || loading}
                  sx={{
                    bgcolor: 'rgba(255,255,255,0.1)',
                    color: 'white',
                    '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' },
                    '&.Mui-disabled': { color: 'rgba(255,255,255,0.3)' }
                  }}
                >
                  {exporting ? <CircularProgress size={24} color="inherit" /> : <PictureAsPdf />}
                </IconButton>
              </Tooltip>
            </Stack>
          </Stack>
        </Container>
      </Paper>

      {/* Sprint 6: Global Filter Bar with Cross-Filtering */}
      <Container maxWidth="xl" sx={{ mt: 2, mb: 2 }}>
        <FilterBar
          showEquipments={true}
          showAreas={true}
          showStatuses={false}
          compact={true}
        />
        <Box sx={{ mt: 1 }}>
          <DrillDownBreadcrumb />
        </Box>
        {/* Cross-Filter Panel - Shows active selections */}
        <CrossFilterPanel position="top" collapsible={true} />
      </Container>

      <Container maxWidth="xl">
        {exportError && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setExportError(null)}>
            {exportError}
          </Alert>
        )}
        {error && overview && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            Erro ao atualizar dados: {error}. Mostrando dados anteriores.
          </Alert>
        )}

        {overview && (
          <>
            {/* KPI Cards - Interactive with Cross-Filtering */}
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} lg={3}>
                <ClickableKPI
                  type="oee"
                  title="OEE"
                  value={overview.kpis.oee.value}
                  target={overview.kpis.oee.target}
                  trend={overview.kpis.oee.trend}
                  trendData={trendData?.data?.slice(-12).map(d => d.value) || []}
                  icon={<Speed />}
                  color="primary"
                  format="percent"
                  drillThroughPage="/oee-dashboard"
                  showSparkline={true}
                  showTarget={true}
                />
              </Grid>
              <Grid item xs={12} sm={6} lg={3}>
                <ClickableKPI
                  type="availability"
                  title="Disponibilidade"
                  value={overview.kpis.availability.value}
                  target={overview.kpis.availability.target}
                  trend={overview.kpis.availability.trend}
                  icon={<Timer />}
                  color="success"
                  format="percent"
                  drillThroughPage="/oee-dashboard"
                  showSparkline={false}
                  showTarget={true}
                />
              </Grid>
              <Grid item xs={12} sm={6} lg={3}>
                <ClickableKPI
                  type="performance"
                  title="Performance"
                  value={overview.kpis.performance.value}
                  target={overview.kpis.performance.target}
                  trend={overview.kpis.performance.trend}
                  icon={<Bolt />}
                  color="warning"
                  format="percent"
                  drillThroughPage="/oee-dashboard"
                  showSparkline={false}
                  showTarget={true}
                />
              </Grid>
              <Grid item xs={12} sm={6} lg={3}>
                <ClickableKPI
                  type="quality"
                  title="Qualidade"
                  value={overview.kpis.quality.value}
                  target={overview.kpis.quality.target}
                  trend={overview.kpis.quality.trend}
                  icon={<VerifiedUser />}
                  color="info"
                  format="percent"
                  drillThroughPage="/oee-dashboard"
                  showSparkline={false}
                  showTarget={true}
                />
              </Grid>
            </Grid>

            {/* Charts and Alerts Row */}
            <Grid container spacing={3} sx={{ mt: 1 }}>
              {/* OEE Trend Chart */}
              <Grid item xs={12} lg={8}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                      <Typography variant="h6" fontWeight={600}>
                        Tendência de {selectedMetric.toUpperCase()}
                      </Typography>
                      <FormControl size="small" sx={{ minWidth: 150 }}>
                        <Select
                          value={selectedMetric}
                          onChange={(e) => setSelectedMetric(e.target.value)}
                        >
                          <MenuItem value="oee">OEE</MenuItem>
                          <MenuItem value="availability">Disponibilidade</MenuItem>
                          <MenuItem value="performance">Performance</MenuItem>
                          <MenuItem value="quality">Qualidade</MenuItem>
                          <MenuItem value="production">Produção</MenuItem>
                        </Select>
                      </FormControl>
                    </Stack>

                    <Box sx={{ height: 300 }}>
                      <ResponsiveContainer>
                        <AreaChart data={trendData?.data || []}>
                          <defs>
                            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor={theme.palette.primary.main} stopOpacity={0.3} />
                              <stop offset="95%" stopColor={theme.palette.primary.main} stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke={alpha(theme.palette.divider, 0.5)} />
                          <XAxis
                            dataKey="timestamp"
                            tickFormatter={(val) => new Date(val).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}
                            stroke={theme.palette.text.secondary}
                            fontSize={12}
                          />
                          <YAxis
                            stroke={theme.palette.text.secondary}
                            fontSize={12}
                            domain={selectedMetric === 'production' ? ['auto', 'auto'] : [0, 100]}
                          />
                          <RechartsTooltip
                            contentStyle={{
                              backgroundColor: theme.palette.background.paper,
                              border: `1px solid ${theme.palette.divider}`,
                              borderRadius: 8
                            }}
                            formatter={(value: number) => [`${value.toFixed(1)}${trendData?.unit || '%'}`, selectedMetric.toUpperCase()]}
                            labelFormatter={(label) => new Date(label).toLocaleString('pt-BR')}
                          />
                          <Area
                            type="monotone"
                            dataKey="value"
                            stroke={theme.palette.primary.main}
                            strokeWidth={2}
                            fillOpacity={1}
                            fill="url(#colorValue)"
                          />
                          <Line
                            type="monotone"
                            dataKey="target"
                            stroke={theme.palette.success.main}
                            strokeDasharray="5 5"
                            strokeWidth={2}
                            dot={false}
                          />
                          <Legend />
                        </AreaChart>
                      </ResponsiveContainer>
                    </Box>

                    {trendData && (
                      <Stack direction="row" justifyContent="space-around" mt={2}>
                        <Box textAlign="center">
                          <Typography variant="caption" color="text.secondary">Atual</Typography>
                          <Typography variant="h6" fontWeight={600}>{trendData.summary.current}{trendData.unit}</Typography>
                        </Box>
                        <Box textAlign="center">
                          <Typography variant="caption" color="text.secondary">Média</Typography>
                          <Typography variant="h6" fontWeight={600}>{trendData.summary.average}{trendData.unit}</Typography>
                        </Box>
                        <Box textAlign="center">
                          <Typography variant="caption" color="text.secondary">Mín</Typography>
                          <Typography variant="h6" fontWeight={600}>{trendData.summary.min}{trendData.unit}</Typography>
                        </Box>
                        <Box textAlign="center">
                          <Typography variant="caption" color="text.secondary">Máx</Typography>
                          <Typography variant="h6" fontWeight={600}>{trendData.summary.max}{trendData.unit}</Typography>
                        </Box>
                      </Stack>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              {/* Alarms Status */}
              <Grid item xs={12} lg={4}>
                <AlertCard alarms={overview.alarms} />
              </Grid>
            </Grid>

            {/* Insights, Equipment and Financial Row */}
            <Grid container spacing={3} sx={{ mt: 1 }}>
              {/* Executive Insights */}
              <Grid item xs={12} md={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Stack direction="row" alignItems="center" spacing={1} mb={2}>
                      <Info color="info" />
                      <Typography variant="h6" fontWeight={600}>
                        Insights Executivos
                      </Typography>
                    </Stack>

                    {overview.insights.map((insight, idx) => (
                      <InsightCard key={idx} insight={insight} />
                    ))}
                  </CardContent>
                </Card>
              </Grid>

              {/* Equipment Health */}
              <Grid item xs={12} md={4}>
                <EquipmentHealth equipment={overview.critical_equipment} />
              </Grid>

              {/* Financial Summary */}
              <Grid item xs={12} md={4}>
                <FinancialSummary financial={overview.financial_summary} />
              </Grid>
            </Grid>

            {/* Production Trends */}
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" fontWeight={600} mb={3}>
                      Indicadores de Produção
                    </Typography>

                    <Grid container spacing={3}>
                      {Object.entries(overview.production_trends).map(([key, trend]) => (
                        <Grid item xs={12} md={4} key={key}>
                          <Paper
                            sx={{
                              p: 3,
                              textAlign: 'center',
                              bgcolor: alpha(theme.palette.primary.main, 0.05),
                              border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`
                            }}
                          >
                            <Typography variant="caption" color="text.secondary" textTransform="uppercase">
                              {key.replace('_', ' ')}
                            </Typography>
                            <Stack direction="row" justifyContent="center" alignItems="baseline" spacing={1} my={1}>
                              <Typography variant="h4" fontWeight={700}>
                                {trend.current.toLocaleString('pt-BR')}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {trend.unit}
                              </Typography>
                            </Stack>
                            <Stack direction="row" justifyContent="center" alignItems="center" spacing={0.5}>
                              {trend.trend === 'up' ? (
                                <TrendingUp sx={{ color: 'success.main', fontSize: 18 }} />
                              ) : (
                                <TrendingDown sx={{ color: 'error.main', fontSize: 18 }} />
                              )}
                              <Typography
                                variant="body2"
                                sx={{ color: trend.trend === 'up' ? 'success.main' : 'error.main' }}
                              >
                                {trend.change_percent > 0 ? '+' : ''}{trend.change_percent.toFixed(1)}%
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                vs período anterior
                              </Typography>
                            </Stack>
                          </Paper>
                        </Grid>
                      ))}
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* ============================================
                NOVAS SEÇÕES: ENERGIA, PARETO, PRODUÇÃO E MANUTENÇÃO
                ============================================ */}

            {/* Seção de Energia */}
            {energyData && (
              <Grid container spacing={3} sx={{ mt: 1 }}>
                <Grid item xs={12}>
                  <EnergySection energy={energyData} />
                </Grid>
              </Grid>
            )}

            {/* Seção de Pareto de Alarmes */}
            {paretoData && (
              <Grid container spacing={3} sx={{ mt: 1 }}>
                <Grid item xs={12}>
                  <ParetoSection pareto={paretoData} />
                </Grid>
              </Grid>
            )}

            {/* Seção de Métricas de Produção Detalhadas */}
            {productionData && (
              <Grid container spacing={3} sx={{ mt: 1 }}>
                <Grid item xs={12}>
                  <ProductionSection production={productionData} />
                </Grid>
              </Grid>
            )}

            {/* Seção de Manutenção Preditiva */}
            {maintenanceData && (
              <Grid container spacing={3} sx={{ mt: 1 }}>
                <Grid item xs={12}>
                  <MaintenanceSection maintenance={maintenanceData} />
                </Grid>
              </Grid>
            )}
          </>
        )}
      </Container>
    </Box>
  );
};

export default ExecutiveDashboardPage;
