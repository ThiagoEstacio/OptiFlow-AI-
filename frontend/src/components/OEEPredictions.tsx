/**
 * OEE Predictions Component - Sprint 3
 * =====================================
 *
 * Displays ML-based OEE predictions with early warning system.
 *
 * Features:
 * - Hourly OEE predictions chart
 * - Drop warnings with severity indicators
 * - Root cause analysis
 * - Recommendations panel
 */

import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Alert,
  AlertTitle,
  IconButton,
  Tooltip,
  useTheme,
  alpha,
  Stack,
  Divider,
  LinearProgress,
  Collapse,
  Button,
  Badge,
  Card,
  CardContent,
  CardHeader,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import { Grid } from './GridWrapper';
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Warning,
  Error as ErrorIcon,
  CheckCircle,
  Info,
  Refresh,
  ExpandMore,
  ExpandLess,
  Speed,
  Timeline,
  Lightbulb,
  Build,
  Schedule,
  PriorityHigh,
  AutoGraph,
} from '@mui/icons-material';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  ReferenceLine,
  Line,
  ComposedChart,
} from 'recharts';
import apiClient from '../api/client';
import { useAsyncData } from '../hooks/useAsyncData';
import { REFRESH_INTERVALS } from '../utils/constants';
import { LoadingState, ErrorState } from './shared';

// Types
interface PredictionPoint {
  timestamp: string;
  predicted_oee: number;
  confidence_interval: {
    lower: number;
    upper: number;
  };
  confidence: 'high' | 'medium' | 'low' | 'uncertain';
  contributing_factors: Record<string, number>;
}

interface DropWarning {
  warning_id: string;
  equipment_id: string;
  equipment_name: string;
  current_oee: number;
  predicted_oee: number;
  predicted_drop: number;
  drop_risk: 'critical' | 'high' | 'medium' | 'low' | 'none';
  expected_time: string;
  hours_until_drop: number;
  root_causes: Array<{
    factor: string;
    impact: string;
    description: string;
    [key: string]: any;
  }>;
  recommendations: string[];
  confidence: string;
  created_at: string;
}

interface OEEForecast {
  equipment_id: string;
  equipment_name: string;
  current_oee: number;
  predictions: PredictionPoint[];
  drop_warnings: DropWarning[];
  trend: 'improving' | 'stable' | 'declining';
  trend_slope: number;
  model_accuracy: number;
  last_updated: string;
}

interface PredictionSummary {
  total_equipment: number;
  equipment_with_warnings: number;
  critical_warnings: number;
  high_warnings: number;
  medium_warnings: number;
  average_predicted_oee: number;
  worst_predicted_equipment: {
    equipment_id: string;
    equipment_name: string;
    predicted_oee: number;
  } | null;
  best_predicted_equipment: {
    equipment_id: string;
    equipment_name: string;
    predicted_oee: number;
  } | null;
  overall_trend: string;
  generated_at: string;
}

// Format helpers
const formatNumber = (value: number, decimals = 1) => {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

const formatTime = (isoString: string) => {
  const date = new Date(isoString);
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
};

const formatDateTime = (isoString: string) => {
  const date = new Date(isoString);
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// Risk color helpers
const getRiskColor = (risk: DropWarning['drop_risk'], theme: any) => {
  switch (risk) {
    case 'critical':
      return theme.palette.error.main;
    case 'high':
      return theme.palette.warning.dark;
    case 'medium':
      return theme.palette.warning.main;
    case 'low':
      return theme.palette.info.main;
    default:
      return theme.palette.grey[500];
  }
};

const getRiskLabel = (risk: DropWarning['drop_risk']) => {
  switch (risk) {
    case 'critical':
      return 'Crítico';
    case 'high':
      return 'Alto';
    case 'medium':
      return 'Médio';
    case 'low':
      return 'Baixo';
    default:
      return 'Normal';
  }
};

const getTrendIcon = (trend: OEEForecast['trend']) => {
  switch (trend) {
    case 'improving':
      return <TrendingUp sx={{ color: 'success.main' }} />;
    case 'declining':
      return <TrendingDown sx={{ color: 'error.main' }} />;
    default:
      return <TrendingFlat sx={{ color: 'grey.500' }} />;
  }
};

const getConfidenceColor = (confidence: string, theme: any) => {
  switch (confidence) {
    case 'high':
      return theme.palette.success.main;
    case 'medium':
      return theme.palette.warning.main;
    case 'low':
      return theme.palette.error.light;
    default:
      return theme.palette.grey[400];
  }
};

// Summary Card Component
const PredictionSummaryCard: React.FC<{ summary: PredictionSummary }> = ({ summary }) => {
  const theme = useTheme();

  return (
    <Paper sx={{ p: 2.5 }}>
      <Stack direction="row" alignItems="center" spacing={1} mb={2}>
        <AutoGraph sx={{ color: theme.palette.primary.main, fontSize: 24 }} />
        <Typography variant="h6" fontWeight={700}>
          Resumo de Predições
        </Typography>
        <Chip
          label={`${summary.total_equipment} equipamentos`}
          size="small"
          sx={{ fontWeight: 600 }}
        />
      </Stack>

      <Grid container spacing={2}>
        {/* Warning Stats */}
        <Grid item xs={12} md={4}>
          <Paper
            sx={{
              p: 2,
              bgcolor: alpha(theme.palette.warning.main, 0.08),
              border: `1px solid ${alpha(theme.palette.warning.main, 0.2)}`,
            }}
          >
            <Typography variant="caption" color="text.secondary">
              Equipamentos com Alertas
            </Typography>
            <Stack direction="row" alignItems="baseline" spacing={1}>
              <Typography variant="h4" fontWeight={800} color="warning.main">
                {summary.equipment_with_warnings}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                de {summary.total_equipment}
              </Typography>
            </Stack>
            <Stack direction="row" spacing={1} mt={1}>
              {summary.critical_warnings > 0 && (
                <Chip
                  size="small"
                  label={`${summary.critical_warnings} críticos`}
                  color="error"
                  sx={{ fontWeight: 600 }}
                />
              )}
              {summary.high_warnings > 0 && (
                <Chip
                  size="small"
                  label={`${summary.high_warnings} altos`}
                  color="warning"
                  sx={{ fontWeight: 600 }}
                />
              )}
            </Stack>
          </Paper>
        </Grid>

        {/* Average OEE */}
        <Grid item xs={12} md={4}>
          <Paper
            sx={{
              p: 2,
              bgcolor: alpha(theme.palette.primary.main, 0.08),
              border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
            }}
          >
            <Typography variant="caption" color="text.secondary">
              OEE Médio Previsto (8h)
            </Typography>
            <Typography
              variant="h4"
              fontWeight={800}
              color={summary.average_predicted_oee >= 80 ? 'success.main' : 'warning.main'}
            >
              {formatNumber(summary.average_predicted_oee, 1)}%
            </Typography>
            <Chip
              size="small"
              label={
                summary.overall_trend === 'declining'
                  ? 'Tendência de queda'
                  : summary.overall_trend === 'improving'
                  ? 'Tendência de alta'
                  : 'Estável'
              }
              icon={
                summary.overall_trend === 'declining' ? (
                  <TrendingDown />
                ) : summary.overall_trend === 'improving' ? (
                  <TrendingUp />
                ) : (
                  <TrendingFlat />
                )
              }
              sx={{ mt: 1 }}
            />
          </Paper>
        </Grid>

        {/* Best/Worst */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, bgcolor: alpha(theme.palette.grey[100], 0.5) }}>
            <Stack spacing={1}>
              {summary.worst_predicted_equipment && (
                <Box>
                  <Typography variant="caption" color="error.main" fontWeight={600}>
                    Pior Previsão
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {summary.worst_predicted_equipment.equipment_name}:{' '}
                    {formatNumber(summary.worst_predicted_equipment.predicted_oee, 1)}%
                  </Typography>
                </Box>
              )}
              {summary.best_predicted_equipment && (
                <Box>
                  <Typography variant="caption" color="success.main" fontWeight={600}>
                    Melhor Previsão
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {summary.best_predicted_equipment.equipment_name}:{' '}
                    {formatNumber(summary.best_predicted_equipment.predicted_oee, 1)}%
                  </Typography>
                </Box>
              )}
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Paper>
  );
};

// Prediction Chart Component
const PredictionChart: React.FC<{ forecast: OEEForecast }> = ({ forecast }) => {
  const theme = useTheme();

  const chartData = useMemo(() => {
    return forecast.predictions.map((p) => ({
      time: formatTime(p.timestamp),
      predicted: p.predicted_oee,
      lower: p.confidence_interval.lower,
      upper: p.confidence_interval.upper,
      confidence: p.confidence,
    }));
  }, [forecast.predictions]);

  // Add current OEE as first point
  const fullData = [
    {
      time: 'Agora',
      predicted: forecast.current_oee,
      lower: forecast.current_oee,
      upper: forecast.current_oee,
      confidence: 'high',
    },
    ...chartData,
  ];

  return (
    <Paper sx={{ p: 2.5, height: '100%' }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <Timeline sx={{ color: theme.palette.primary.main, fontSize: 24 }} />
          <Typography variant="h6" fontWeight={700}>
            Previsão de OEE - {forecast.equipment_name}
          </Typography>
        </Stack>
        <Stack direction="row" alignItems="center" spacing={1}>
          {getTrendIcon(forecast.trend)}
          <Typography variant="body2" color="text.secondary">
            {forecast.trend === 'improving'
              ? 'Melhorando'
              : forecast.trend === 'declining'
              ? 'Declinando'
              : 'Estável'}
          </Typography>
          <Chip
            size="small"
            label={`Precisão: ${formatNumber(forecast.model_accuracy * 100, 0)}%`}
            sx={{ fontWeight: 600 }}
          />
        </Stack>
      </Stack>

      <Box sx={{ height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={fullData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={theme.palette.primary.main} stopOpacity={0.3} />
                <stop offset="95%" stopColor={theme.palette.primary.main} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={alpha(theme.palette.divider, 0.5)} />
            <XAxis dataKey="time" tick={{ fontSize: 11 }} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
            <RechartsTooltip
              contentStyle={{
                fontSize: 12,
                borderRadius: 8,
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              }}
              formatter={(value: number, name: string) => [
                `${formatNumber(value, 1)}%`,
                name === 'predicted' ? 'OEE Previsto' : name === 'upper' ? 'Limite Superior' : 'Limite Inferior',
              ]}
            />
            <ReferenceLine y={85} stroke={theme.palette.success.main} strokeDasharray="5 5" label="Meta" />
            <ReferenceLine y={70} stroke={theme.palette.warning.main} strokeDasharray="5 5" label="Alerta" />
            <Area
              type="monotone"
              dataKey="upper"
              stackId="1"
              stroke="transparent"
              fill={alpha(theme.palette.primary.main, 0.1)}
            />
            <Area
              type="monotone"
              dataKey="lower"
              stackId="2"
              stroke="transparent"
              fill={theme.palette.background.paper}
            />
            <Line
              type="monotone"
              dataKey="predicted"
              stroke={theme.palette.primary.main}
              strokeWidth={3}
              dot={{ fill: theme.palette.primary.main, r: 5 }}
              activeDot={{ r: 8 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </Box>

      <Stack direction="row" spacing={2} mt={2} justifyContent="center">
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <Box sx={{ width: 16, height: 3, bgcolor: theme.palette.primary.main, borderRadius: 1 }} />
          <Typography variant="caption">OEE Previsto</Typography>
        </Stack>
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <Box
            sx={{
              width: 16,
              height: 10,
              bgcolor: alpha(theme.palette.primary.main, 0.2),
              borderRadius: 1,
            }}
          />
          <Typography variant="caption">Intervalo de Confiança</Typography>
        </Stack>
      </Stack>
    </Paper>
  );
};

// Drop Warning Card Component
const DropWarningCard: React.FC<{ warning: DropWarning }> = ({ warning }) => {
  const theme = useTheme();
  const [expanded, setExpanded] = useState(false);

  return (
    <Card
      sx={{
        borderLeft: `4px solid ${getRiskColor(warning.drop_risk, theme)}`,
        bgcolor: alpha(getRiskColor(warning.drop_risk, theme), 0.05),
      }}
    >
      <CardHeader
        avatar={
          <Avatar sx={{ bgcolor: getRiskColor(warning.drop_risk, theme) }}>
            {warning.drop_risk === 'critical' ? <PriorityHigh /> : <Warning />}
          </Avatar>
        }
        title={
          <Stack direction="row" alignItems="center" spacing={1}>
            <Typography fontWeight={700}>{warning.equipment_name}</Typography>
            <Chip
              size="small"
              label={getRiskLabel(warning.drop_risk)}
              sx={{
                bgcolor: getRiskColor(warning.drop_risk, theme),
                color: 'white',
                fontWeight: 600,
              }}
            />
          </Stack>
        }
        subheader={
          <Stack direction="row" spacing={2}>
            <Typography variant="body2" color="text.secondary">
              <Schedule sx={{ fontSize: 14, mr: 0.5, verticalAlign: 'middle' }} />
              Em {formatNumber(warning.hours_until_drop, 1)}h ({formatDateTime(warning.expected_time)})
            </Typography>
          </Stack>
        }
        action={
          <IconButton onClick={() => setExpanded(!expanded)}>
            {expanded ? <ExpandLess /> : <ExpandMore />}
          </IconButton>
        }
      />
      <CardContent sx={{ pt: 0 }}>
        <Grid container spacing={2}>
          <Grid item xs={4}>
            <Typography variant="caption" color="text.secondary">
              OEE Atual
            </Typography>
            <Typography variant="h5" fontWeight={700}>
              {formatNumber(warning.current_oee, 1)}%
            </Typography>
          </Grid>
          <Grid item xs={4}>
            <Typography variant="caption" color="text.secondary">
              OEE Previsto
            </Typography>
            <Typography variant="h5" fontWeight={700} color="error.main">
              {formatNumber(warning.predicted_oee, 1)}%
            </Typography>
          </Grid>
          <Grid item xs={4}>
            <Typography variant="caption" color="text.secondary">
              Queda Esperada
            </Typography>
            <Typography variant="h5" fontWeight={700} color="error.main">
              -{formatNumber(warning.predicted_drop, 1)}%
            </Typography>
          </Grid>
        </Grid>

        <Collapse in={expanded}>
          <Divider sx={{ my: 2 }} />

          {/* Root Causes */}
          <Typography variant="subtitle2" fontWeight={700} gutterBottom>
            <Build sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
            Causas Identificadas
          </Typography>
          <Stack spacing={1} mb={2}>
            {warning.root_causes.map((cause, idx) => (
              <Alert key={idx} severity="warning" sx={{ py: 0.5 }}>
                <Typography variant="body2">{cause.description}</Typography>
              </Alert>
            ))}
          </Stack>

          {/* Recommendations */}
          <Typography variant="subtitle2" fontWeight={700} gutterBottom>
            <Lightbulb sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
            Recomendações
          </Typography>
          <List dense>
            {warning.recommendations.map((rec, idx) => (
              <ListItem key={idx} sx={{ py: 0 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <CheckCircle sx={{ fontSize: 16, color: 'success.main' }} />
                </ListItemIcon>
                <ListItemText
                  primary={rec}
                  primaryTypographyProps={{ variant: 'body2' }}
                />
              </ListItem>
            ))}
          </List>
        </Collapse>
      </CardContent>
    </Card>
  );
};

// Main Component
interface OEEPredictionsProps {
  equipmentId?: string;
  showSummary?: boolean;
}

export const OEEPredictions: React.FC<OEEPredictionsProps> = ({
  equipmentId,
  showSummary = true,
}) => {
  const theme = useTheme();

  // Fetch forecast for single equipment or all
  const fetchForecast = useCallback(async () => {
    if (equipmentId) {
      const response = await apiClient.get(`/api/v1/oee/predictions/${equipmentId}`);
      return response.data as OEEForecast;
    } else {
      const response = await apiClient.get('/api/v1/oee/predictions/');
      return response.data as OEEForecast[];
    }
  }, [equipmentId]);

  const fetchSummary = useCallback(async () => {
    const response = await apiClient.get('/api/v1/oee/predictions/summary');
    return response.data as PredictionSummary;
  }, []);

  const {
    data: forecastData,
    loading: forecastLoading,
    error: forecastError,
    refresh: refreshForecast,
  } = useAsyncData(fetchForecast, {
    autoRefresh: true,
    refreshInterval: REFRESH_INTERVALS.SLOW,
    keepPreviousData: true,
  });

  const {
    data: summaryData,
    loading: summaryLoading,
  } = useAsyncData(fetchSummary, {
    autoRefresh: true,
    refreshInterval: REFRESH_INTERVALS.SLOW,
    keepPreviousData: true,
  });

  // Get forecasts as array
  const forecasts = useMemo(() => {
    if (!forecastData) return [];
    return Array.isArray(forecastData) ? forecastData : [forecastData];
  }, [forecastData]);

  // Get all warnings sorted by severity
  const allWarnings = useMemo(() => {
    const warnings: DropWarning[] = [];
    forecasts.forEach((f) => {
      warnings.push(...f.drop_warnings);
    });

    const riskOrder = ['critical', 'high', 'medium', 'low', 'none'];
    return warnings.sort((a, b) => {
      const riskDiff = riskOrder.indexOf(a.drop_risk) - riskOrder.indexOf(b.drop_risk);
      if (riskDiff !== 0) return riskDiff;
      return a.hours_until_drop - b.hours_until_drop;
    });
  }, [forecasts]);

  if (forecastLoading && !forecastData) {
    return <LoadingState message="Carregando predições de OEE..." size="lg" />;
  }

  if (forecastError && !forecastData) {
    return <ErrorState message={forecastError} onRetry={refreshForecast} />;
  }

  return (
    <Box>
      <Stack spacing={3}>
        {/* Header */}
        <Paper
          sx={{
            p: 2.5,
            background: `linear-gradient(135deg, ${alpha(theme.palette.info.main, 0.1)} 0%, ${alpha(
              theme.palette.primary.main,
              0.05
            )} 100%)`,
          }}
        >
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Stack direction="row" alignItems="center" spacing={2}>
              <AutoGraph sx={{ fontSize: 40, color: theme.palette.primary.main }} />
              <Box>
                <Typography variant="h5" fontWeight={800}>
                  Predições de OEE com ML
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Previsões para as próximas 8 horas com alertas antecipados
                </Typography>
              </Box>
            </Stack>

            <Stack direction="row" spacing={1} alignItems="center">
              {allWarnings.length > 0 && (
                <Badge badgeContent={allWarnings.length} color="error">
                  <Chip
                    icon={<Warning />}
                    label="Alertas Ativos"
                    color="warning"
                    sx={{ fontWeight: 600 }}
                  />
                </Badge>
              )}
              <Tooltip title="Atualizar predições">
                <IconButton onClick={refreshForecast}>
                  <Refresh />
                </IconButton>
              </Tooltip>
            </Stack>
          </Stack>
        </Paper>

        {/* Summary */}
        {showSummary && summaryData && <PredictionSummaryCard summary={summaryData} />}

        {/* Warnings */}
        {allWarnings.length > 0 && (
          <Box>
            <Typography variant="h6" fontWeight={700} gutterBottom>
              <Warning sx={{ mr: 1, verticalAlign: 'middle', color: 'warning.main' }} />
              Alertas de Queda de OEE ({allWarnings.length})
            </Typography>
            <Grid container spacing={2}>
              {allWarnings.slice(0, 4).map((warning) => (
                <Grid item xs={12} md={6} key={warning.warning_id}>
                  <DropWarningCard warning={warning} />
                </Grid>
              ))}
            </Grid>
          </Box>
        )}

        {/* Prediction Charts */}
        <Box>
          <Typography variant="h6" fontWeight={700} gutterBottom>
            <Timeline sx={{ mr: 1, verticalAlign: 'middle', color: 'primary.main' }} />
            Gráficos de Previsão
          </Typography>
          <Grid container spacing={3}>
            {forecasts.slice(0, 4).map((forecast) => (
              <Grid item xs={12} lg={6} key={forecast.equipment_id}>
                <PredictionChart forecast={forecast} />
              </Grid>
            ))}
          </Grid>
        </Box>
      </Stack>
    </Box>
  );
};

export default OEEPredictions;
