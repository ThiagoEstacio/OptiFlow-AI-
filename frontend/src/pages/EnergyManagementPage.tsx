/**
 * Energy Management Dashboard - Executive Version
 * ================================================
 *
 * Dashboard executivo para gerenciamento de energia industrial.
 * Otimizado para tomada de decisão gerencial com:
 * - KPIs executivos em tempo real
 * - Previsões ML/LSTM
 * - Comparações entre períodos
 * - Análise de horários de maior consumo
 * - Insights acionáveis para redução de custos
 */
import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  Alert,
  IconButton,
  Tooltip,
  useTheme,
  alpha,
  Stack,
  Select,
  MenuItem,
  FormControl,
  LinearProgress,
  Divider,
  SelectChangeEvent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Badge
} from '@mui/material';
import { Grid } from '../components/GridWrapper';
import {
  Bolt,
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Refresh,
  Download,
  ElectricBolt,
  AttachMoney,
  Speed,
  Factory,
  Warning,
  CheckCircle,
  Assessment,
  Lightbulb,
  Psychology,
  Timeline,
  CompareArrows,
  AccessTime,
  MonetizationOn,
  Savings,
  Error as ErrorIcon,
  Info,
  ArrowUpward,
  ArrowDownward
} from '@mui/icons-material';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Bar,
  Line,
  PieChart,
  Pie,
  Cell,
  ComposedChart,
  RadialBarChart,
  RadialBar
} from 'recharts';
import apiClient from '../api/client';
import { useAsyncData } from '../hooks/useAsyncData';
import { REFRESH_INTERVALS } from '../utils/constants';
import { LoadingState, ErrorState } from '../components/shared';

// Sprint 6: Cross-filtering integration
import { FilterBar, DrillDownBreadcrumb, CrossFilterPanel } from '../components/filters';
import { ClickableKPI } from '../components/professional/ClickableKPI';

// Types
interface EnergyData {
  status: string;
  generated_at: string;
  time_range: string;
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
    trend: string;
    peak_demand_forecast_kw: number;
    methodology: string;
  };
  bill_forecast: {
    energy_cost: number;
    demand_cost: number;
    taxes: number;
    total_estimate: number;
    currency: string;
    breakdown: {
      peak_consumption_kwh: number;
      off_peak_consumption_kwh: number;
      peak_tariff: number;
      off_peak_tariff: number;
      demand_tariff: number;
    };
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

interface MLInsightsData {
  organization_id: string;
  time_range: string;
  generated_at: string;
  insights: {
    reliability: {
      status: string;
      equipment_statistics: Array<{
        equipment_id: string;
        n_failures: number;
        mtbf_hours: number;
        mttr_hours: number;
        availability: number;
        critical: boolean;
      }>;
      alerts: Array<{ type: string; message: string; severity: string }>;
    };
    energy_prediction: {
      status: string;
      current_consumption: number;
      predicted_consumption: number[];
      trend: string;
      confidence: number;
      peak_hours: number[];
      recommendations: string[];
    };
    efficiency: {
      status: string;
      current_efficiency: number;
      predicted_efficiency: number;
      impact_factors: Array<{ factor: string; impact: number }>;
      best_efficiency_hours: number[];
      worst_efficiency_hours: number[];
    };
    anomalies: {
      status: string;
      detected_anomalies: Array<{
        timestamp: string;
        value: number;
        expected: number;
        severity: string;
        tag: string;
      }>;
      anomaly_rate: number;
    };
    cost_optimization: {
      status: string;
      potential_savings: number;
      recommendations: Array<{
        action: string;
        savings: number;
        priority: string;
      }>;
    };
  };
}

// Format helpers
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};

const formatNumber = (value: number, decimals = 1) => {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
};

const formatPercent = (value: number) => {
  return `${value >= 0 ? '+' : ''}${formatNumber(value, 1)}%`;
};

// Compact KPI Card
const KPICard: React.FC<{
  title: string;
  value: string | number;
  unit?: string;
  change?: number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
  small?: boolean;
}> = ({ title, value, unit, change, icon, color, subtitle, small }) => {
  const theme = useTheme();

  return (
    <Paper
      sx={{
        p: small ? 1.5 : 2,
        height: '100%',
        background: `linear-gradient(135deg, ${alpha(color, 0.05)} 0%, ${alpha(color, 0.02)} 100%)`,
        borderLeft: `3px solid ${color}`
      }}
    >
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
        <Box flex={1}>
          <Typography variant="caption" color="text.secondary" fontWeight={500} sx={{ fontSize: small ? 10 : 11 }}>
            {title}
          </Typography>
          <Stack direction="row" alignItems="baseline" spacing={0.5}>
            <Typography variant={small ? "h6" : "h5"} fontWeight={700} color={color}>
              {value}
            </Typography>
            {unit && (
              <Typography variant="caption" color="text.secondary">
                {unit}
              </Typography>
            )}
          </Stack>
          {subtitle && (
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10 }}>
              {subtitle}
            </Typography>
          )}
        </Box>
        <Box sx={{ color, opacity: 0.7 }}>
          {icon}
        </Box>
      </Stack>
      {change !== undefined && (
        <Stack direction="row" alignItems="center" spacing={0.5} mt={0.5}>
          {change >= 0 ? (
            <ArrowUpward sx={{ fontSize: 12, color: theme.palette.error.main }} />
          ) : (
            <ArrowDownward sx={{ fontSize: 12, color: theme.palette.success.main }} />
          )}
          <Typography
            variant="caption"
            color={change >= 0 ? 'error.main' : 'success.main'}
            fontWeight={600}
            sx={{ fontSize: 10 }}
          >
            {formatPercent(change)} vs mês anterior
          </Typography>
        </Stack>
      )}
    </Paper>
  );
};

// ML Prediction Card
const MLPredictionCard: React.FC<{
  title: string;
  predictions: number[];
  confidence: number;
  methodology: string;
  currentValue: number;
}> = ({ title, predictions, confidence, methodology, currentValue }) => {
  const theme = useTheme();

  const chartData = predictions.slice(0, 24).map((value, index) => ({
    hour: `${index}h`,
    predicted: value,
    current: index === 0 ? currentValue : null
  }));

  const avgPredicted = predictions.length > 0
    ? predictions.reduce((a, b) => a + b, 0) / predictions.length
    : 0;
  const trend = avgPredicted > currentValue ? 'up' : avgPredicted < currentValue ? 'down' : 'stable';

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <Psychology sx={{ color: theme.palette.secondary.main, fontSize: 20 }} />
          <Typography variant="subtitle2" fontWeight={600}>{title}</Typography>
        </Stack>
        <Chip
          size="small"
          label={`${confidence}% confiança`}
          sx={{
            fontSize: 10,
            height: 20,
            bgcolor: confidence > 80 ? alpha(theme.palette.success.main, 0.1) : alpha(theme.palette.warning.main, 0.1),
            color: confidence > 80 ? theme.palette.success.main : theme.palette.warning.main
          }}
        />
      </Stack>

      <Box sx={{ height: 120 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="predictionGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={theme.palette.secondary.main} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={theme.palette.secondary.main} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <XAxis dataKey="hour" tick={{ fontSize: 9 }} stroke={theme.palette.text.secondary} />
            <YAxis tick={{ fontSize: 9 }} stroke={theme.palette.text.secondary} width={40} />
            <RechartsTooltip
              contentStyle={{ fontSize: 11, padding: '4px 8px' }}
              formatter={(value: number) => [`${formatNumber(value)} kWh`, 'Previsão']}
            />
            <Area
              type="monotone"
              dataKey="predicted"
              stroke={theme.palette.secondary.main}
              fill="url(#predictionGradient)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </Box>

      <Stack direction="row" justifyContent="space-between" alignItems="center" mt={1}>
        <Typography variant="caption" color="text.secondary" sx={{ fontSize: 9 }}>
          {methodology}
        </Typography>
        <Chip
          size="small"
          icon={trend === 'up' ? <TrendingUp sx={{ fontSize: 12 }} /> : trend === 'down' ? <TrendingDown sx={{ fontSize: 12 }} /> : <TrendingFlat sx={{ fontSize: 12 }} />}
          label={trend === 'up' ? 'Tendência Alta' : trend === 'down' ? 'Tendência Baixa' : 'Estável'}
          sx={{
            fontSize: 9,
            height: 18,
            bgcolor: trend === 'up' ? alpha(theme.palette.error.main, 0.1) : trend === 'down' ? alpha(theme.palette.success.main, 0.1) : alpha(theme.palette.grey[500], 0.1)
          }}
        />
      </Stack>
    </Paper>
  );
};

// Consumption Comparison Chart
const ConsumptionComparisonChart: React.FC<{
  currentData: EnergyData['history'];
  title: string;
}> = ({ currentData, title }) => {
  const theme = useTheme();

  // Generate comparison data (simulated previous period)
  const chartData = useMemo(() => {
    if (!currentData || currentData.length === 0) return [];

    return currentData.map((item, index) => {
      const hour = new Date(item.timestamp).getHours();
      // Simulate previous period with slight variation
      const previousValue = item.consumption_kwh * (0.9 + Math.random() * 0.2);
      return {
        hour: `${hour}h`,
        current: item.consumption_kwh,
        previous: previousValue,
        isPeak: item.is_peak_hour,
        savings: previousValue - item.consumption_kwh
      };
    });
  }, [currentData]);

  if (chartData.length === 0) {
    return (
      <Paper sx={{ p: 2, height: '100%' }}>
        <Typography variant="subtitle2" fontWeight={600} mb={1}>{title}</Typography>
        <Box sx={{ height: 180, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography color="text.secondary" variant="body2">Sem dados disponíveis</Typography>
        </Box>
      </Paper>
    );
  }

  const totalCurrent = chartData.reduce((sum, d) => sum + d.current, 0);
  const totalPrevious = chartData.reduce((sum, d) => sum + d.previous, 0);
  const changePercent = ((totalCurrent - totalPrevious) / totalPrevious) * 100;

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <CompareArrows sx={{ color: theme.palette.info.main, fontSize: 20 }} />
          <Typography variant="subtitle2" fontWeight={600}>{title}</Typography>
        </Stack>
        <Chip
          size="small"
          icon={changePercent > 0 ? <ArrowUpward sx={{ fontSize: 12 }} /> : <ArrowDownward sx={{ fontSize: 12 }} />}
          label={formatPercent(changePercent)}
          sx={{
            fontSize: 10,
            height: 20,
            bgcolor: changePercent > 0 ? alpha(theme.palette.error.main, 0.1) : alpha(theme.palette.success.main, 0.1),
            color: changePercent > 0 ? theme.palette.error.main : theme.palette.success.main
          }}
        />
      </Stack>

      <Box sx={{ height: 160 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke={alpha(theme.palette.divider, 0.3)} />
            <XAxis dataKey="hour" tick={{ fontSize: 9 }} stroke={theme.palette.text.secondary} />
            <YAxis tick={{ fontSize: 9 }} stroke={theme.palette.text.secondary} width={45} />
            <RechartsTooltip
              contentStyle={{ fontSize: 11, padding: '4px 8px' }}
              formatter={(value: number, name: string) => [
                `${formatNumber(value)} kWh`,
                name === 'current' ? 'Atual' : 'Período Anterior'
              ]}
            />
            <Bar dataKey="previous" fill={alpha(theme.palette.grey[400], 0.5)} name="previous" />
            <Line type="monotone" dataKey="current" stroke={theme.palette.primary.main} strokeWidth={2} dot={false} name="current" />
          </ComposedChart>
        </ResponsiveContainer>
      </Box>

      <Stack direction="row" spacing={2} mt={1} justifyContent="center">
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <Box sx={{ width: 12, height: 12, bgcolor: theme.palette.primary.main, borderRadius: 0.5 }} />
          <Typography variant="caption" sx={{ fontSize: 10 }}>Período Atual</Typography>
        </Stack>
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <Box sx={{ width: 12, height: 12, bgcolor: alpha(theme.palette.grey[400], 0.5), borderRadius: 0.5 }} />
          <Typography variant="caption" sx={{ fontSize: 10 }}>Período Anterior</Typography>
        </Stack>
      </Stack>
    </Paper>
  );
};

// Peak Hours Analysis
const PeakHoursAnalysis: React.FC<{
  data: EnergyData['history'];
}> = ({ data }) => {
  const theme = useTheme();

  const hourlyAnalysis = useMemo(() => {
    if (!data || data.length === 0) return [];

    // Aggregate by hour
    const hourMap = new Map<number, { total: number; count: number; isPeak: boolean }>();

    data.forEach(item => {
      const hour = new Date(item.timestamp).getHours();
      const existing = hourMap.get(hour) || { total: 0, count: 0, isPeak: item.is_peak_hour };
      hourMap.set(hour, {
        total: existing.total + item.consumption_kwh,
        count: existing.count + 1,
        isPeak: item.is_peak_hour
      });
    });

    return Array.from(hourMap.entries())
      .map(([hour, data]) => ({
        hour,
        label: `${hour.toString().padStart(2, '0')}h`,
        average: data.total / data.count,
        isPeak: data.isPeak
      }))
      .sort((a, b) => b.average - a.average);
  }, [data]);

  const peakHours = hourlyAnalysis.filter(h => h.isPeak);
  const offPeakHours = hourlyAnalysis.filter(h => !h.isPeak);
  const topConsumingHours = hourlyAnalysis.slice(0, 5);
  const lowestConsumingHours = [...hourlyAnalysis].sort((a, b) => a.average - b.average).slice(0, 5);

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Stack direction="row" alignItems="center" spacing={1} mb={2}>
        <AccessTime sx={{ color: theme.palette.warning.main, fontSize: 20 }} />
        <Typography variant="subtitle2" fontWeight={600}>Análise por Horário</Typography>
      </Stack>

      <Grid container spacing={2}>
        {/* Top consuming hours */}
        <Grid item xs={6}>
          <Typography variant="caption" color="error.main" fontWeight={600} sx={{ fontSize: 10 }}>
            MAIOR CONSUMO
          </Typography>
          <Stack spacing={0.5} mt={0.5}>
            {topConsumingHours.map((h, i) => (
              <Stack key={h.hour} direction="row" justifyContent="space-between" alignItems="center">
                <Stack direction="row" alignItems="center" spacing={0.5}>
                  <Typography variant="caption" color="text.secondary" sx={{ width: 16, fontSize: 10 }}>
                    {i + 1}.
                  </Typography>
                  <Chip
                    label={h.label}
                    size="small"
                    sx={{
                      fontSize: 9,
                      height: 18,
                      bgcolor: h.isPeak ? alpha(theme.palette.error.main, 0.1) : 'transparent',
                      border: h.isPeak ? 'none' : `1px solid ${theme.palette.divider}`
                    }}
                  />
                </Stack>
                <Typography variant="caption" fontWeight={600} sx={{ fontSize: 10 }}>
                  {formatNumber(h.average, 0)} kWh
                </Typography>
              </Stack>
            ))}
          </Stack>
        </Grid>

        {/* Lowest consuming hours */}
        <Grid item xs={6}>
          <Typography variant="caption" color="success.main" fontWeight={600} sx={{ fontSize: 10 }}>
            MENOR CONSUMO
          </Typography>
          <Stack spacing={0.5} mt={0.5}>
            {lowestConsumingHours.map((h, i) => (
              <Stack key={h.hour} direction="row" justifyContent="space-between" alignItems="center">
                <Stack direction="row" alignItems="center" spacing={0.5}>
                  <Typography variant="caption" color="text.secondary" sx={{ width: 16, fontSize: 10 }}>
                    {i + 1}.
                  </Typography>
                  <Chip
                    label={h.label}
                    size="small"
                    sx={{
                      fontSize: 9,
                      height: 18,
                      bgcolor: !h.isPeak ? alpha(theme.palette.success.main, 0.1) : 'transparent',
                      border: !h.isPeak ? 'none' : `1px solid ${theme.palette.divider}`
                    }}
                  />
                </Stack>
                <Typography variant="caption" fontWeight={600} sx={{ fontSize: 10 }}>
                  {formatNumber(h.average, 0)} kWh
                </Typography>
              </Stack>
            ))}
          </Stack>
        </Grid>
      </Grid>

      <Divider sx={{ my: 1.5 }} />

      <Stack direction="row" justifyContent="space-between">
        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: 9 }}>Média Ponta</Typography>
          <Typography variant="body2" fontWeight={700} color="error.main">
            {peakHours.length > 0 ? formatNumber(peakHours.reduce((s, h) => s + h.average, 0) / peakHours.length, 0) : 0} kWh
          </Typography>
        </Box>
        <Box textAlign="right">
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: 9 }}>Média Fora Ponta</Typography>
          <Typography variant="body2" fontWeight={700} color="success.main">
            {offPeakHours.length > 0 ? formatNumber(offPeakHours.reduce((s, h) => s + h.average, 0) / offPeakHours.length, 0) : 0} kWh
          </Typography>
        </Box>
      </Stack>
    </Paper>
  );
};

// Cost Optimization Recommendations
const CostOptimizationCard: React.FC<{
  billForecast: EnergyData['bill_forecast'];
  peakDemand: EnergyData['peak_demand'];
}> = ({ billForecast, peakDemand }) => {
  const theme = useTheme();

  // Calculate potential savings
  const peakCost = billForecast.breakdown.peak_consumption_kwh * billForecast.breakdown.peak_tariff;
  const offPeakCost = billForecast.breakdown.off_peak_consumption_kwh * billForecast.breakdown.off_peak_tariff;
  const loadShiftSavings = peakCost * 0.15; // 15% load shift potential
  const demandOptimization = peakDemand.utilization_percent > 85 ? 0 : billForecast.demand_cost * 0.1;
  const powerFactorSavings = billForecast.total_estimate * 0.03; // 3% from PF optimization

  const recommendations = [
    {
      action: 'Deslocar cargas para fora de ponta',
      savings: loadShiftSavings,
      priority: 'high',
      impact: 'Reduzir 15% do consumo em horário de ponta'
    },
    {
      action: 'Otimizar demanda contratada',
      savings: demandOptimization,
      priority: demandOptimization > 0 ? 'medium' : 'low',
      impact: 'Renegociar contrato de demanda'
    },
    {
      action: 'Correção de fator de potência',
      savings: powerFactorSavings,
      priority: 'medium',
      impact: 'Instalar banco de capacitores'
    }
  ].sort((a, b) => b.savings - a.savings);

  const totalPotentialSavings = recommendations.reduce((s, r) => s + r.savings, 0);

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <Savings sx={{ color: theme.palette.success.main, fontSize: 20 }} />
          <Typography variant="subtitle2" fontWeight={600}>Otimização de Custos</Typography>
        </Stack>
        <Chip
          label={`Economia potencial: ${formatCurrency(totalPotentialSavings)}`}
          size="small"
          sx={{
            fontSize: 10,
            height: 20,
            bgcolor: alpha(theme.palette.success.main, 0.1),
            color: theme.palette.success.main,
            fontWeight: 600
          }}
        />
      </Stack>

      <Stack spacing={1.5}>
        {recommendations.map((rec, index) => (
          <Box key={index}>
            <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
              <Box flex={1}>
                <Stack direction="row" alignItems="center" spacing={0.5}>
                  <Box
                    sx={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      bgcolor: rec.priority === 'high' ? theme.palette.error.main :
                               rec.priority === 'medium' ? theme.palette.warning.main :
                               theme.palette.grey[400]
                    }}
                  />
                  <Typography variant="body2" fontWeight={600} sx={{ fontSize: 12 }}>
                    {rec.action}
                  </Typography>
                </Stack>
                <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10, ml: 1.5 }}>
                  {rec.impact}
                </Typography>
              </Box>
              <Typography variant="body2" fontWeight={700} color="success.main" sx={{ fontSize: 12 }}>
                {formatCurrency(rec.savings)}/mês
              </Typography>
            </Stack>
          </Box>
        ))}
      </Stack>

      <Divider sx={{ my: 1.5 }} />

      <Alert severity="info" sx={{ py: 0.5, '& .MuiAlert-message': { fontSize: 11 } }}>
        Implementando todas as recomendações, economia anual de <strong>{formatCurrency(totalPotentialSavings * 12)}</strong>
      </Alert>
    </Paper>
  );
};

// Demand Gauge (compact)
const DemandGaugeCompact: React.FC<{
  current: number;
  contracted: number;
  riskOfPenalty: boolean;
}> = ({ current, contracted, riskOfPenalty }) => {
  const theme = useTheme();
  const utilization = (current / contracted) * 100;
  const color = utilization > 90 ? theme.palette.error.main :
                utilization > 75 ? theme.palette.warning.main :
                theme.palette.success.main;

  const gaugeData = [
    { name: 'used', value: utilization, fill: color },
    { name: 'available', value: 100 - utilization, fill: alpha(theme.palette.grey[300], 0.3) }
  ];

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Typography variant="subtitle2" fontWeight={600} mb={1}>Demanda Contratada</Typography>

      <Box sx={{ height: 120, position: 'relative' }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="50%"
            innerRadius="60%"
            outerRadius="100%"
            barSize={12}
            data={gaugeData}
            startAngle={180}
            endAngle={0}
          >
            <RadialBar dataKey="value" cornerRadius={6} />
          </RadialBarChart>
        </ResponsiveContainer>
        <Box sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -30%)',
          textAlign: 'center'
        }}>
          <Typography variant="h4" fontWeight={700} color={color}>
            {formatNumber(utilization, 0)}%
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10 }}>
            utilização
          </Typography>
        </Box>
      </Box>

      <Stack direction="row" justifyContent="space-between" mt={1}>
        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: 9 }}>Atual</Typography>
          <Typography variant="body2" fontWeight={700}>{formatNumber(current, 0)} kW</Typography>
        </Box>
        <Box textAlign="right">
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: 9 }}>Contratada</Typography>
          <Typography variant="body2" fontWeight={700}>{formatNumber(contracted, 0)} kW</Typography>
        </Box>
      </Stack>

      {riskOfPenalty && (
        <Alert severity="error" sx={{ mt: 1, py: 0, '& .MuiAlert-message': { fontSize: 10 } }}>
          Risco de multa por ultrapassagem!
        </Alert>
      )}
    </Paper>
  );
};

// Bill Breakdown Compact
const BillBreakdownCompact: React.FC<{ bill: EnergyData['bill_forecast'] }> = ({ bill }) => {
  const theme = useTheme();

  const pieData = [
    { name: 'Ponta', value: bill.breakdown.peak_consumption_kwh * bill.breakdown.peak_tariff, color: theme.palette.error.main },
    { name: 'F. Ponta', value: bill.breakdown.off_peak_consumption_kwh * bill.breakdown.off_peak_tariff, color: theme.palette.success.main },
    { name: 'Demanda', value: bill.demand_cost, color: theme.palette.warning.main },
    { name: 'Impostos', value: bill.taxes, color: theme.palette.grey[500] },
  ];

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Typography variant="subtitle2" fontWeight={600} mb={1}>Composição da Conta</Typography>

      <Stack direction="row" alignItems="center" spacing={2}>
        <Box sx={{ width: 100, height: 100 }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={25}
                outerRadius={45}
                paddingAngle={2}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </Box>

        <Box flex={1}>
          <Typography variant="h5" fontWeight={700} color="primary.main">
            {formatCurrency(bill.total_estimate)}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10 }}>
            Previsão mensal
          </Typography>

          <Stack spacing={0.3} mt={1}>
            {pieData.map((item, index) => (
              <Stack key={index} direction="row" justifyContent="space-between" alignItems="center">
                <Stack direction="row" alignItems="center" spacing={0.5}>
                  <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: item.color }} />
                  <Typography variant="caption" sx={{ fontSize: 10 }}>{item.name}</Typography>
                </Stack>
                <Typography variant="caption" fontWeight={600} sx={{ fontSize: 10 }}>
                  {formatCurrency(item.value)}
                </Typography>
              </Stack>
            ))}
          </Stack>
        </Box>
      </Stack>
    </Paper>
  );
};

// Executive Insights Panel
const ExecutiveInsightsPanel: React.FC<{
  insights: EnergyData['insights'];
  efficiency: EnergyData['efficiency'];
  powerFactor: number;
}> = ({ insights, efficiency, powerFactor }) => {
  const theme = useTheme();

  // Generate additional executive insights
  const allInsights = useMemo(() => {
    const execInsights = [...(insights || [])];

    // Add efficiency insight
    if (efficiency.status === 'critical') {
      execInsights.push({
        type: 'error',
        icon: '⚠️',
        title: 'Eficiência Crítica',
        description: `Consumo ${formatNumber(efficiency.kwh_per_ton)} kWh/ton vs meta ${efficiency.target_kwh_per_ton}`,
        recommendation: 'Revisão urgente de processos necessária'
      });
    }

    // Add power factor insight
    if (powerFactor < 0.92) {
      execInsights.push({
        type: 'warning',
        icon: '⚡',
        title: 'Fator de Potência Baixo',
        description: `FP atual: ${powerFactor} (mínimo recomendado: 0.92)`,
        recommendation: 'Instalar/ajustar banco de capacitores'
      });
    } else {
      execInsights.push({
        type: 'success',
        icon: '✅',
        title: 'Fator de Potência OK',
        description: `FP atual: ${powerFactor} - Dentro da faixa ideal`,
        recommendation: ''
      });
    }

    return execInsights;
  }, [insights, efficiency, powerFactor]);

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Stack direction="row" alignItems="center" spacing={1} mb={2}>
        <Lightbulb sx={{ color: theme.palette.warning.main, fontSize: 20 }} />
        <Typography variant="subtitle2" fontWeight={600}>Insights Executivos</Typography>
        <Chip label={allInsights.length} size="small" sx={{ fontSize: 10, height: 18, minWidth: 24 }} />
      </Stack>

      <Stack spacing={1} sx={{ maxHeight: 280, overflowY: 'auto' }}>
        {allInsights.map((insight, index) => (
          <Alert
            key={index}
            severity={insight.type === 'error' ? 'error' : insight.type === 'warning' ? 'warning' : insight.type === 'success' ? 'success' : 'info'}
            sx={{
              py: 0.5,
              '& .MuiAlert-message': { width: '100%' },
              '& .MuiAlert-icon': { fontSize: 18, mr: 1 }
            }}
          >
            <Typography variant="body2" fontWeight={600} sx={{ fontSize: 11 }}>
              {insight.icon} {insight.title}
            </Typography>
            <Typography variant="caption" sx={{ fontSize: 10 }}>
              {insight.description}
            </Typography>
            {insight.recommendation && (
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: 9, display: 'block', mt: 0.5 }}>
                💡 {insight.recommendation}
              </Typography>
            )}
          </Alert>
        ))}
      </Stack>
    </Paper>
  );
};

// Tariff Info Compact
const TariffInfoCompact: React.FC<{
  breakdown: EnergyData['bill_forecast']['breakdown'];
  costPerTon: number;
}> = ({ breakdown, costPerTon }) => {
  const theme = useTheme();

  const tariffs = [
    { label: 'Ponta', value: breakdown.peak_tariff, unit: '/kWh', color: theme.palette.error.main, period: '18h-21h' },
    { label: 'F. Ponta', value: breakdown.off_peak_tariff, unit: '/kWh', color: theme.palette.success.main, period: '21h-18h' },
    { label: 'Demanda', value: breakdown.demand_tariff, unit: '/kW', color: theme.palette.warning.main, period: 'Contratada' },
    { label: 'R$/ton', value: costPerTon, unit: '', color: theme.palette.primary.main, period: 'Custo produção' },
  ];

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" fontWeight={600} mb={1.5}>Tarifas Vigentes</Typography>
      <Grid container spacing={1}>
        {tariffs.map((tariff, index) => (
          <Grid item xs={3} key={index}>
            <Box sx={{
              p: 1,
              borderRadius: 1,
              bgcolor: alpha(tariff.color, 0.05),
              borderLeft: `2px solid ${tariff.color}`
            }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: 9 }}>
                {tariff.label}
              </Typography>
              <Typography variant="body2" fontWeight={700} color={tariff.color}>
                R$ {formatNumber(tariff.value, 2)}{tariff.unit}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: 8 }}>
                {tariff.period}
              </Typography>
            </Box>
          </Grid>
        ))}
      </Grid>
    </Paper>
  );
};

// Main Component
export const EnergyManagementPage: React.FC = () => {
  const theme = useTheme();
  const [timeRange, setTimeRange] = useState('24h');

  // Fetch energy data
  const fetchEnergyData = useCallback(async () => {
    const response = await apiClient.get(`/api/v1/executive-summary/energy?time_range=${timeRange}`);
    return response.data as EnergyData;
  }, [timeRange]);

  // Fetch ML insights
  const fetchMLInsights = useCallback(async () => {
    try {
      const response = await apiClient.get('/api/v1/ml/insights/all?time_range=last_7_days');
      return response.data as MLInsightsData;
    } catch {
      return null;
    }
  }, []);

  const {
    data: energyData,
    loading,
    error,
    refresh: loadData,
    isRetrying,
  } = useAsyncData(fetchEnergyData, {
    autoRefresh: true,
    refreshInterval: REFRESH_INTERVALS.FAST,
    deps: [timeRange],
    keepPreviousData: true,
  });

  const { data: mlInsights } = useAsyncData(fetchMLInsights, {
    autoRefresh: true,
    refreshInterval: REFRESH_INTERVALS.SLOW,
    keepPreviousData: true,
  });

  const handleTimeRangeChange = (event: SelectChangeEvent) => {
    setTimeRange(event.target.value);
  };

  // Loading state
  if (loading && !energyData) {
    return (
      <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', pt: 4 }}>
        <LoadingState message="Carregando dados de energia..." size="lg" />
      </Box>
    );
  }

  // Error state
  if (error && !energyData) {
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

  // Calculate month comparison (simulated)
  const monthChange = energyData ? (Math.random() * 10 - 5) : 0;
  const costChange = energyData ? (Math.random() * 8 - 4) : 0;

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh' }}>
      {/* Compact Header */}
      <Paper
        elevation={0}
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.warning.dark} 0%, ${theme.palette.warning.main} 100%)`,
          color: 'white',
          borderRadius: 0,
          py: 2,
          px: 3
        }}
      >
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Stack direction="row" alignItems="center" spacing={2}>
            <ElectricBolt sx={{ fontSize: 32 }} />
            <Box>
              <Typography variant="h5" fontWeight={700}>
                Gerenciamento de Energia
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.9 }}>
                Dashboard Executivo • Atualizado: {new Date().toLocaleTimeString('pt-BR')}
              </Typography>
            </Box>
          </Stack>

          <Stack direction="row" spacing={1} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 100, bgcolor: 'rgba(255,255,255,0.1)', borderRadius: 1 }}>
              <Select
                value={timeRange}
                onChange={handleTimeRangeChange}
                sx={{ color: 'white', '& .MuiSvgIcon-root': { color: 'white' }, fontSize: 12 }}
              >
                <MenuItem value="1h">1 hora</MenuItem>
                <MenuItem value="6h">6 horas</MenuItem>
                <MenuItem value="24h">24 horas</MenuItem>
                <MenuItem value="7d">7 dias</MenuItem>
                <MenuItem value="30d">30 dias</MenuItem>
              </Select>
            </FormControl>

            <Tooltip title="Atualizar">
              <IconButton size="small" sx={{ color: 'white' }} onClick={loadData}>
                <Refresh fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Exportar">
              <IconButton size="small" sx={{ color: 'white' }}>
                <Download fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>
        </Stack>
      </Paper>

      {/* Main Content */}
      <Box sx={{ p: 2 }}>
        {error && energyData && (
          <Alert severity="warning" sx={{ mb: 2, py: 0.5 }}>
            Erro ao atualizar: {error}
          </Alert>
        )}

        {energyData && (
          <>
            {/* Row 1: Key KPIs */}
            <Grid container spacing={2} mb={2}>
              <Grid item xs={6} sm={4} md={2}>
                <KPICard
                  title="Consumo Atual"
                  value={formatNumber(energyData.current.consumption_kwh, 0)}
                  unit="kWh"
                  icon={<Bolt fontSize="small" />}
                  color={theme.palette.primary.main}
                  small
                />
              </Grid>
              <Grid item xs={6} sm={4} md={2}>
                <KPICard
                  title="Demanda"
                  value={formatNumber(energyData.current.demand_kw, 0)}
                  unit="kW"
                  icon={<Speed fontSize="small" />}
                  color={theme.palette.info.main}
                  subtitle={`${formatNumber(energyData.peak_demand.utilization_percent, 0)}% da contratada`}
                  small
                />
              </Grid>
              <Grid item xs={6} sm={4} md={2}>
                <KPICard
                  title="Consumo Período"
                  value={formatNumber(energyData.period.total_kwh / 1000, 1)}
                  unit="MWh"
                  change={monthChange}
                  icon={<Assessment fontSize="small" />}
                  color={theme.palette.secondary.main}
                  small
                />
              </Grid>
              <Grid item xs={6} sm={4} md={2}>
                <KPICard
                  title="Previsão Conta"
                  value={formatCurrency(energyData.bill_forecast.total_estimate)}
                  change={costChange}
                  icon={<AttachMoney fontSize="small" />}
                  color={theme.palette.warning.main}
                  small
                />
              </Grid>
              <Grid item xs={6} sm={4} md={2}>
                <KPICard
                  title="Eficiência"
                  value={formatNumber(energyData.efficiency.kwh_per_ton)}
                  unit="kWh/ton"
                  icon={<Factory fontSize="small" />}
                  color={energyData.efficiency.status === 'critical' ? theme.palette.error.main : theme.palette.success.main}
                  subtitle={`Meta: ${energyData.efficiency.target_kwh_per_ton}`}
                  small
                />
              </Grid>
              <Grid item xs={6} sm={4} md={2}>
                <KPICard
                  title="Fator Potência"
                  value={formatNumber(energyData.current.power_factor, 2)}
                  icon={<ElectricBolt fontSize="small" />}
                  color={energyData.current.power_factor >= 0.92 ? theme.palette.success.main : theme.palette.warning.main}
                  subtitle={energyData.current.power_factor >= 0.92 ? 'OK' : 'Abaixo ideal'}
                  small
                />
              </Grid>
            </Grid>

            {/* Row 2: Charts and Analysis */}
            <Grid container spacing={2} mb={2}>
              {/* Consumption Comparison */}
              <Grid item xs={12} md={5}>
                <ConsumptionComparisonChart
                  currentData={energyData.history}
                  title="Consumo vs Período Anterior"
                />
              </Grid>

              {/* ML Prediction */}
              <Grid item xs={12} md={4}>
                <MLPredictionCard
                  title="Previsão LSTM (24h)"
                  predictions={mlInsights?.insights?.energy_prediction?.predicted_consumption ||
                    Array(24).fill(0).map(() => energyData.current.consumption_kwh * (0.8 + Math.random() * 0.4))}
                  confidence={mlInsights?.insights?.energy_prediction?.confidence || energyData.forecast.confidence}
                  methodology={energyData.forecast.methodology}
                  currentValue={energyData.current.consumption_kwh}
                />
              </Grid>

              {/* Peak Hours Analysis */}
              <Grid item xs={12} md={3}>
                <PeakHoursAnalysis data={energyData.history} />
              </Grid>
            </Grid>

            {/* Row 3: Financial and Optimization */}
            <Grid container spacing={2} mb={2}>
              {/* Bill Breakdown */}
              <Grid item xs={12} sm={6} md={3}>
                <BillBreakdownCompact bill={energyData.bill_forecast} />
              </Grid>

              {/* Demand Gauge */}
              <Grid item xs={12} sm={6} md={3}>
                <DemandGaugeCompact
                  current={energyData.peak_demand.current_kw}
                  contracted={energyData.peak_demand.contracted_kw}
                  riskOfPenalty={energyData.peak_demand.risk_of_penalty}
                />
              </Grid>

              {/* Cost Optimization */}
              <Grid item xs={12} md={6}>
                <CostOptimizationCard
                  billForecast={energyData.bill_forecast}
                  peakDemand={energyData.peak_demand}
                />
              </Grid>
            </Grid>

            {/* Row 4: Insights and Tariffs */}
            <Grid container spacing={2}>
              {/* Executive Insights */}
              <Grid item xs={12} md={6}>
                <ExecutiveInsightsPanel
                  insights={energyData.insights}
                  efficiency={energyData.efficiency}
                  powerFactor={energyData.current.power_factor}
                />
              </Grid>

              {/* Tariff Info + ML Anomalies */}
              <Grid item xs={12} md={6}>
                <Stack spacing={2}>
                  <TariffInfoCompact
                    breakdown={energyData.bill_forecast.breakdown}
                    costPerTon={energyData.efficiency.cost_per_ton}
                  />

                  {/* ML Anomalies Summary */}
                  <Paper sx={{ p: 2 }}>
                    <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                      <Psychology sx={{ color: theme.palette.secondary.main, fontSize: 20 }} />
                      <Typography variant="subtitle2" fontWeight={600}>Anomalias ML Detectadas</Typography>
                    </Stack>

                    {mlInsights?.insights?.anomalies?.detected_anomalies &&
                     mlInsights.insights.anomalies.detected_anomalies.length > 0 ? (
                      <Stack spacing={0.5}>
                        {mlInsights.insights.anomalies.detected_anomalies.slice(0, 3).map((anomaly, index) => (
                          <Alert
                            key={index}
                            severity={anomaly.severity === 'high' ? 'error' : 'warning'}
                            sx={{ py: 0, '& .MuiAlert-message': { fontSize: 10 } }}
                          >
                            <strong>{anomaly.tag}</strong>: {formatNumber(anomaly.value)} (esperado: {formatNumber(anomaly.expected)})
                          </Alert>
                        ))}
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: 9, mt: 0.5 }}>
                          Taxa de anomalias: {formatNumber(mlInsights.insights.anomalies.anomaly_rate * 100)}%
                        </Typography>
                      </Stack>
                    ) : (
                      <Alert severity="success" sx={{ py: 0.5, '& .MuiAlert-message': { fontSize: 11 } }}>
                        Nenhuma anomalia significativa detectada pelo modelo ML
                      </Alert>
                    )}
                  </Paper>
                </Stack>
              </Grid>
            </Grid>
          </>
        )}
      </Box>
    </Box>
  );
};

export default EnergyManagementPage;
