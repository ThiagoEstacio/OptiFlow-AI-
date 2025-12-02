/**
 * OEE Dashboard - Overall Equipment Effectiveness
 * ================================================
 *
 * Dashboard executivo profissional para análise de OEE industrial.
 * Layout otimizado para máximo uso do espaço com informações claras.
 */
import React, { useState, useCallback, useEffect, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
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
  Divider,
  SelectChangeEvent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Tabs,
  Tab,
  Collapse,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Badge,
  Snackbar,
  AlertTitle,
  Drawer,
  Switch,
  FormControlLabel,
  TextField,
  Menu,
  CircularProgress
} from '@mui/material';
import { Grid } from '../components/GridWrapper';
import {
  Speed,
  Refresh,
  Download,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  AccessTime,
  PrecisionManufacturing,
  Engineering,
  TrendingUp,
  TrendingDown,
  BarChart as BarChartIcon,
  Timer,
  Build,
  HighQuality,
  Settings,
  Close,
  Timeline,
  Report,
  ExpandMore,
  ExpandLess,
  PlayArrow,
  Stop,
  Pause,
  Construction,
  Inventory,
  Category,
  Assignment,
  Info,
  OpenInNew,
  NotificationsActive,
  NotificationsOff,
  Notifications,
  ArrowDownward,
  ArrowUpward,
  PictureAsPdf,
  TableChart,
  Print,
  Share
} from '@mui/icons-material';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Bar,
  Cell,
  ComposedChart,
  RadialBarChart,
  RadialBar,
  BarChart,
  Line
} from 'recharts';
import apiClient from '../api/client';
import { useAsyncData } from '../hooks/useAsyncData';
import { REFRESH_INTERVALS } from '../utils/constants';
import { LoadingState, ErrorState } from '../components/shared';
import { OEEPredictions } from '../components/OEEPredictions';

// Sprint 6: Cross-filtering integration
import { FilterBar, DrillDownBreadcrumb, useFilterStore, useURLFilters } from '../components/filters';

// Types
interface OEEOverview {
  status: string;
  generated_at: string;
  time_range: string;
  hours_in_period: number;
  summary: {
    oee: { value: number; target: number; status: string; world_class: number; gap_to_target: number };
    availability: { value: number; target: number; status: string };
    performance: { value: number; target: number; status: string };
    quality: { value: number; target: number; status: string };
  };
  losses: {
    equipment_failure_hours: number;
    setup_adjustments_hours: number;
    idling_minor_stops_hours: number;
    reduced_speed_hours: number;
    process_defects_hours: number;
    reduced_yield_hours: number;
    total_loss_hours: number;
  };
  equipment_count: number;
  insights: Array<{
    type: string;
    icon: string;
    title: string;
    description: string;
    recommendation: string;
  }>;
}

interface EquipmentData {
  status: string;
  time_range: string;
  hours_in_period: number;
  aggregated: {
    total_equipment: number;
    total_operating_hours: number;
    total_downtime_hours: number;
    total_production: number;
    total_defects: number;
    overall_defect_rate: number;
    equipment_above_target: number;
    equipment_critical: number;
  };
  equipment: Array<{
    id: string;
    name: string;
    area: string;
    type: string;
    oee: number;
    availability: number;
    performance: number;
    quality: number;
    status: string;
    hours_total: number;
    hours_planned_production: number;
    hours_operating: number;
    hours_planned_downtime: number;
    hours_unplanned_downtime: number;
    hours_idle: number;
    utilization_percent: number;
    total_pieces: number;
    good_pieces: number;
    defect_pieces: number;
    defect_rate: number;
    mtbf_hours: number;
    mttr_hours: number;
    num_failures: number;
    total_loss_hours: number;
  }>;
}

interface ShiftData {
  status: string;
  date: string;
  summary: {
    best_shift: string;
    best_oee: number;
    worst_shift: string;
    worst_oee: number;
    gap: number;
  };
  shifts: Array<{
    shift: string;
    start_time: string;
    end_time: string;
    oee: number;
    availability: number;
    performance: number;
    quality: number;
    status: string;
  }>;
}

// === SPRINT 2: Equipment Details for Drill-Down ===
interface EquipmentDetails {
  id: string;
  name: string;
  area: string;
  type: string;
  current_state: 'running' | 'stopped' | 'idle' | 'maintenance';
  oee: number;
  availability: number;
  performance: number;
  quality: number;
  metrics: {
    hours_total: number;
    hours_operating: number;
    hours_planned_downtime: number;
    hours_unplanned_downtime: number;
    hours_idle: number;
    total_pieces: number;
    good_pieces: number;
    defect_pieces: number;
    defect_rate: number;
    mtbf_hours: number;
    mttr_hours: number;
    num_failures: number;
  };
  downtime_events: Array<{
    id: string;
    start_time: string;
    end_time: string | null;
    duration_minutes: number;
    type: 'planned' | 'unplanned' | 'setup' | 'idle';
    category: string;
    reason: string;
    notes: string;
    classified: boolean;
    classified_by: string | null;
  }>;
  losses_breakdown: {
    equipment_failure: number;
    setup_adjustments: number;
    idling_stops: number;
    reduced_speed: number;
    process_defects: number;
    reduced_yield: number;
  };
  hourly_oee: Array<{
    hour: string;
    oee: number;
    availability: number;
    performance: number;
    quality: number;
  }>;
}

// Downtime classification options
const DOWNTIME_CATEGORIES = [
  { value: 'mechanical_failure', label: 'Falha Mecânica', icon: <Build /> },
  { value: 'electrical_failure', label: 'Falha Elétrica', icon: <Warning /> },
  { value: 'planned_maintenance', label: 'Manutenção Planejada', icon: <Construction /> },
  { value: 'setup_changeover', label: 'Setup / Troca', icon: <Settings /> },
  { value: 'material_shortage', label: 'Falta de Material', icon: <Inventory /> },
  { value: 'quality_issue', label: 'Problema de Qualidade', icon: <Category /> },
  { value: 'operator_break', label: 'Pausa Operador', icon: <Pause /> },
  { value: 'no_demand', label: 'Sem Demanda', icon: <Stop /> },
  { value: 'other', label: 'Outro', icon: <Info /> },
];

// === SPRINT 2: OEE Alert Types ===
interface OEEAlert {
  id: string;
  timestamp: Date;
  type: 'oee_drop' | 'availability_drop' | 'performance_drop' | 'quality_drop' | 'equipment_critical' | 'target_achieved';
  severity: 'critical' | 'warning' | 'info' | 'success';
  title: string;
  message: string;
  equipmentId?: string;
  equipmentName?: string;
  currentValue: number;
  previousValue?: number;
  threshold: number;
  acknowledged: boolean;
}

interface AlertConfig {
  enabled: boolean;
  oeeThreshold: number;
  availabilityThreshold: number;
  performanceThreshold: number;
  qualityThreshold: number;
  dropPercentageAlert: number; // Alert when OEE drops by this % from previous
  soundEnabled: boolean;
}

const DEFAULT_ALERT_CONFIG: AlertConfig = {
  enabled: true,
  oeeThreshold: 70,
  availabilityThreshold: 85,
  performanceThreshold: 80,
  qualityThreshold: 95,
  dropPercentageAlert: 5,
  soundEnabled: false
};

// Format helpers
const formatNumber = (value: number, decimals = 1) => {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
};

// Status helpers
const getStatusColor = (status: string, theme: any) => {
  switch (status) {
    case 'good': return theme.palette.success.main;
    case 'warning': return theme.palette.warning.main;
    case 'critical': return theme.palette.error.main;
    default: return theme.palette.grey[500];
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'good': return <CheckCircle sx={{ fontSize: 18, color: 'success.main' }} />;
    case 'warning': return <Warning sx={{ fontSize: 18, color: 'warning.main' }} />;
    case 'critical': return <ErrorIcon sx={{ fontSize: 18, color: 'error.main' }} />;
    default: return null;
  }
};

// Big OEE Gauge - Full width professional display
const BigOEEDisplay: React.FC<{
  oee: OEEOverview['summary']['oee'];
  availability: OEEOverview['summary']['availability'];
  performance: OEEOverview['summary']['performance'];
  quality: OEEOverview['summary']['quality'];
  equipmentCount: number;
  hoursInPeriod: number;
  totalLossHours: number;
}> = ({ oee, availability, performance, quality, equipmentCount, hoursInPeriod, totalLossHours }) => {
  const theme = useTheme();

  const getColor = (value: number, target: number) =>
    value >= target ? theme.palette.success.main :
    value >= target * 0.9 ? theme.palette.warning.main :
    theme.palette.error.main;

  const ComponentGauge = ({ value, target, label, icon }: { value: number; target: number; label: string; icon: React.ReactNode }) => {
    const color = getColor(value, target);
    const percentage = Math.min((value / 100) * 100, 100);

    return (
      <Box sx={{ textAlign: 'center', flex: 1 }}>
        <Stack direction="row" alignItems="center" justifyContent="center" spacing={0.5} mb={1}>
          <Box sx={{ color }}>{icon}</Box>
          <Typography variant="body2" fontWeight={600} color="text.secondary">
            {label}
          </Typography>
        </Stack>
        <Typography variant="h3" fontWeight={800} color={color} sx={{ lineHeight: 1 }}>
          {formatNumber(value, 1)}%
        </Typography>
        <Box sx={{ mt: 1, mx: 'auto', maxWidth: 150 }}>
          <LinearProgress
            variant="determinate"
            value={percentage}
            sx={{
              height: 8,
              borderRadius: 4,
              bgcolor: alpha(color, 0.15),
              '& .MuiLinearProgress-bar': {
                borderRadius: 4,
                bgcolor: color
              }
            }}
          />
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
          Meta: {target}% | Gap: {value >= target ? '+' : ''}{formatNumber(value - target, 1)}%
        </Typography>
      </Box>
    );
  };

  return (
    <Paper sx={{ p: 3, background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.03)} 0%, ${alpha(theme.palette.background.paper, 1)} 100%)` }}>
      <Grid container spacing={3} alignItems="center">
        {/* Main OEE Score */}
        <Grid item xs={12} md={3}>
          <Box sx={{ textAlign: 'center', position: 'relative' }}>
            <Box sx={{ position: 'relative', display: 'inline-block' }}>
              <Box sx={{
                width: 180,
                height: 180,
                borderRadius: '50%',
                background: `conic-gradient(
                  ${getColor(oee.value, oee.target)} ${oee.value * 3.6}deg,
                  ${alpha(theme.palette.grey[300], 0.3)} ${oee.value * 3.6}deg
                )`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mx: 'auto'
              }}>
                <Box sx={{
                  width: 140,
                  height: 140,
                  borderRadius: '50%',
                  bgcolor: 'background.paper',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexDirection: 'column',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
                }}>
                  <Typography variant="h2" fontWeight={900} color={getColor(oee.value, oee.target)} sx={{ lineHeight: 1 }}>
                    {formatNumber(oee.value, 1)}
                  </Typography>
                  <Typography variant="h6" color={getColor(oee.value, oee.target)} fontWeight={600}>
                    %
                  </Typography>
                </Box>
              </Box>
            </Box>
            <Typography variant="h6" fontWeight={700} color="text.primary" sx={{ mt: 2 }}>
              OEE GERAL
            </Typography>
            <Stack direction="row" spacing={1} justifyContent="center" mt={1}>
              <Chip
                size="small"
                label={`Meta: ${oee.target}%`}
                sx={{ fontSize: 11, fontWeight: 600 }}
              />
              <Chip
                size="small"
                label={`World Class: ${oee.world_class}%`}
                color="primary"
                variant="outlined"
                sx={{ fontSize: 11, fontWeight: 600 }}
              />
            </Stack>
          </Box>
        </Grid>

        {/* Component Gauges */}
        <Grid item xs={12} md={6}>
          <Stack direction="row" spacing={3} divider={<Divider orientation="vertical" flexItem />}>
            <ComponentGauge
              value={availability.value}
              target={availability.target}
              label="DISPONIBILIDADE"
              icon={<Timer sx={{ fontSize: 20 }} />}
            />
            <ComponentGauge
              value={performance.value}
              target={performance.target}
              label="PERFORMANCE"
              icon={<Speed sx={{ fontSize: 20 }} />}
            />
            <ComponentGauge
              value={quality.value}
              target={quality.target}
              label="QUALIDADE"
              icon={<HighQuality sx={{ fontSize: 20 }} />}
            />
          </Stack>
        </Grid>

        {/* Quick Stats */}
        <Grid item xs={12} md={3}>
          <Stack spacing={2}>
            <Paper sx={{ p: 2, bgcolor: alpha(theme.palette.info.main, 0.08), border: `1px solid ${alpha(theme.palette.info.main, 0.2)}` }}>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="caption" color="text.secondary">Equipamentos Monitorados</Typography>
                  <Typography variant="h4" fontWeight={800} color="info.main">{equipmentCount}</Typography>
                </Box>
                <PrecisionManufacturing sx={{ fontSize: 40, color: 'info.main', opacity: 0.5 }} />
              </Stack>
            </Paper>
            <Paper sx={{ p: 2, bgcolor: alpha(theme.palette.warning.main, 0.08), border: `1px solid ${alpha(theme.palette.warning.main, 0.2)}` }}>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="caption" color="text.secondary">Horas Perdidas</Typography>
                  <Typography variant="h4" fontWeight={800} color="warning.main">{formatNumber(totalLossHours, 1)}h</Typography>
                </Box>
                <AccessTime sx={{ fontSize: 40, color: 'warning.main', opacity: 0.5 }} />
              </Stack>
            </Paper>
            <Paper sx={{ p: 2, bgcolor: alpha(theme.palette.success.main, 0.08), border: `1px solid ${alpha(theme.palette.success.main, 0.2)}` }}>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="caption" color="text.secondary">Período de Análise</Typography>
                  <Typography variant="h4" fontWeight={800} color="success.main">{formatNumber(hoursInPeriod, 0)}h</Typography>
                </Box>
                <BarChartIcon sx={{ fontSize: 40, color: 'success.main', opacity: 0.5 }} />
              </Stack>
            </Paper>
          </Stack>
        </Grid>
      </Grid>
    </Paper>
  );
};

// 6 Big Losses Pareto Chart
const LossesPareto: React.FC<{ losses: OEEOverview['losses'] }> = ({ losses }) => {
  const theme = useTheme();

  const lossData = [
    { name: 'Falhas de Equipamento', shortName: 'Falhas Equip.', value: losses.equipment_failure_hours, category: 'Disponibilidade', color: '#e53935' },
    { name: 'Setup e Ajustes', shortName: 'Setup/Ajustes', value: losses.setup_adjustments_hours, category: 'Disponibilidade', color: '#ef5350' },
    { name: 'Paradas Menores', shortName: 'Paradas', value: losses.idling_minor_stops_hours, category: 'Performance', color: '#ff9800' },
    { name: 'Velocidade Reduzida', shortName: 'Veloc. Red.', value: losses.reduced_speed_hours, category: 'Performance', color: '#ffa726' },
    { name: 'Defeitos de Processo', shortName: 'Defeitos', value: losses.process_defects_hours, category: 'Qualidade', color: '#2196f3' },
    { name: 'Redução de Rendimento', shortName: 'Rend. Red.', value: losses.reduced_yield_hours, category: 'Qualidade', color: '#42a5f5' },
  ].sort((a, b) => b.value - a.value);

  const total = lossData.reduce((sum, d) => sum + d.value, 0);
  let cumulative = 0;
  const paretoData = lossData.map(d => {
    cumulative += d.value;
    return {
      ...d,
      percentage: total > 0 ? (d.value / total * 100) : 0,
      cumulative: total > 0 ? (cumulative / total * 100) : 0
    };
  });

  return (
    <Paper sx={{ p: 2.5, height: '100%' }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <Build sx={{ color: theme.palette.error.main, fontSize: 24 }} />
          <Typography variant="h6" fontWeight={700}>6 Grandes Perdas</Typography>
        </Stack>
        <Chip
          label={`Total: ${formatNumber(total, 1)} horas`}
          color="error"
          size="small"
          sx={{ fontWeight: 600 }}
        />
      </Stack>

      <Box sx={{ height: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={paretoData} margin={{ top: 10, right: 30, left: 0, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={alpha(theme.palette.divider, 0.5)} />
            <XAxis
              dataKey="shortName"
              tick={{ fontSize: 11, fontWeight: 500 }}
              angle={-35}
              textAnchor="end"
              height={70}
              interval={0}
            />
            <YAxis
              yAxisId="left"
              tick={{ fontSize: 11 }}
              label={{ value: 'Horas', angle: -90, position: 'insideLeft', fontSize: 12, fontWeight: 600 }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 11 }}
              domain={[0, 100]}
              label={{ value: '% Acumulado', angle: 90, position: 'insideRight', fontSize: 12, fontWeight: 600 }}
            />
            <RechartsTooltip
              contentStyle={{
                fontSize: 12,
                padding: '8px 12px',
                borderRadius: 8,
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
              }}
              formatter={(value: number, name: string) => [
                name === 'cumulative' ? `${formatNumber(value, 1)}%` : `${formatNumber(value, 2)} horas`,
                name === 'cumulative' ? 'Acumulado' : 'Perda'
              ]}
              labelFormatter={(label) => paretoData.find(d => d.shortName === label)?.name || label}
            />
            <Bar yAxisId="left" dataKey="value" name="value" radius={[4, 4, 0, 0]}>
              {paretoData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="cumulative"
              stroke={theme.palette.grey[800]}
              strokeWidth={3}
              dot={{ fill: theme.palette.grey[800], r: 5, strokeWidth: 2, stroke: '#fff' }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </Box>

      <Stack direction="row" spacing={2} mt={2} justifyContent="center">
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <Box sx={{ width: 12, height: 12, borderRadius: 1, bgcolor: '#e53935' }} />
          <Typography variant="caption" fontWeight={500}>Disponibilidade</Typography>
        </Stack>
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <Box sx={{ width: 12, height: 12, borderRadius: 1, bgcolor: '#ff9800' }} />
          <Typography variant="caption" fontWeight={500}>Performance</Typography>
        </Stack>
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <Box sx={{ width: 12, height: 12, borderRadius: 1, bgcolor: '#2196f3' }} />
          <Typography variant="caption" fontWeight={500}>Qualidade</Typography>
        </Stack>
      </Stack>
    </Paper>
  );
};

// Shift Comparison Chart
const ShiftChart: React.FC<{ shifts: ShiftData['shifts']; summary: ShiftData['summary'] }> = ({ shifts, summary }) => {
  const theme = useTheme();

  return (
    <Paper sx={{ p: 2.5, height: '100%' }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <AccessTime sx={{ color: theme.palette.info.main, fontSize: 24 }} />
          <Typography variant="h6" fontWeight={700}>Comparativo por Turno</Typography>
        </Stack>
        <Chip
          label={`Gap: ${formatNumber(summary.gap, 1)} pp`}
          color="warning"
          size="small"
          sx={{ fontWeight: 600 }}
        />
      </Stack>

      <Box sx={{ height: 200 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={shifts} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={alpha(theme.palette.divider, 0.5)} />
            <XAxis dataKey="shift" tick={{ fontSize: 12, fontWeight: 600 }} />
            <YAxis tick={{ fontSize: 11 }} domain={[0, 100]} />
            <RechartsTooltip
              contentStyle={{ fontSize: 12, borderRadius: 8 }}
              formatter={(value: number, name: string) => [`${formatNumber(value, 1)}%`, name]}
            />
            <Bar dataKey="oee" name="OEE" fill={theme.palette.primary.main} radius={[4, 4, 0, 0]} barSize={30} />
            <Bar dataKey="availability" name="Disp." fill={theme.palette.success.main} radius={[4, 4, 0, 0]} barSize={30} />
            <Bar dataKey="performance" name="Perf." fill={theme.palette.warning.main} radius={[4, 4, 0, 0]} barSize={30} />
            <Bar dataKey="quality" name="Qual." fill={theme.palette.info.main} radius={[4, 4, 0, 0]} barSize={30} />
          </BarChart>
        </ResponsiveContainer>
      </Box>

      <Divider sx={{ my: 2 }} />

      <Grid container spacing={2}>
        <Grid item xs={6}>
          <Paper sx={{ p: 1.5, bgcolor: alpha(theme.palette.success.main, 0.1), textAlign: 'center' }}>
            <TrendingUp sx={{ color: 'success.main', fontSize: 28 }} />
            <Typography variant="body2" fontWeight={700} color="success.main">
              {summary.best_shift}: {formatNumber(summary.best_oee, 1)}%
            </Typography>
            <Typography variant="caption" color="text.secondary">Melhor Turno</Typography>
          </Paper>
        </Grid>
        <Grid item xs={6}>
          <Paper sx={{ p: 1.5, bgcolor: alpha(theme.palette.error.main, 0.1), textAlign: 'center' }}>
            <TrendingDown sx={{ color: 'error.main', fontSize: 28 }} />
            <Typography variant="body2" fontWeight={700} color="error.main">
              {summary.worst_shift}: {formatNumber(summary.worst_oee, 1)}%
            </Typography>
            <Typography variant="caption" color="text.secondary">Necessita Atenção</Typography>
          </Paper>
        </Grid>
      </Grid>
    </Paper>
  );
};

// Equipment Performance Table
const EquipmentPerformanceTable: React.FC<{
  equipment: EquipmentData['equipment'];
  aggregated: EquipmentData['aggregated'];
  onEquipmentClick?: (equipment: EquipmentData['equipment'][0]) => void;
}> = ({ equipment, aggregated, onEquipmentClick }) => {
  const theme = useTheme();

  const ProgressCell = ({ value, max = 100, color }: { value: number; max?: number; color: string }) => (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 100 }}>
      <Box sx={{ flex: 1 }}>
        <LinearProgress
          variant="determinate"
          value={Math.min((value / max) * 100, 100)}
          sx={{
            height: 6,
            borderRadius: 3,
            bgcolor: alpha(color, 0.15),
            '& .MuiLinearProgress-bar': { borderRadius: 3, bgcolor: color }
          }}
        />
      </Box>
      <Typography variant="body2" fontWeight={600} sx={{ minWidth: 50, textAlign: 'right', fontSize: 13 }}>
        {formatNumber(value, 1)}%
      </Typography>
    </Box>
  );

  return (
    <Paper sx={{ p: 2.5 }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <PrecisionManufacturing sx={{ color: theme.palette.primary.main, fontSize: 24 }} />
          <Typography variant="h6" fontWeight={700}>Performance por Equipamento</Typography>
        </Stack>
        <Stack direction="row" spacing={1}>
          <Chip
            label={`${aggregated.equipment_above_target} acima da meta`}
            color="success"
            size="small"
            sx={{ fontWeight: 600 }}
          />
          <Chip
            label={`${aggregated.equipment_critical} críticos`}
            color="error"
            size="small"
            sx={{ fontWeight: 600 }}
          />
        </Stack>
      </Stack>

      <TableContainer sx={{ maxHeight: 400 }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 700, fontSize: 12, bgcolor: alpha(theme.palette.primary.main, 0.08) }}>
                Equipamento
              </TableCell>
              <TableCell sx={{ fontWeight: 700, fontSize: 12, bgcolor: alpha(theme.palette.primary.main, 0.08), minWidth: 150 }}>
                OEE
              </TableCell>
              <TableCell sx={{ fontWeight: 700, fontSize: 12, bgcolor: alpha(theme.palette.primary.main, 0.08), minWidth: 130 }}>
                Disponibilidade
              </TableCell>
              <TableCell sx={{ fontWeight: 700, fontSize: 12, bgcolor: alpha(theme.palette.primary.main, 0.08), minWidth: 130 }}>
                Performance
              </TableCell>
              <TableCell sx={{ fontWeight: 700, fontSize: 12, bgcolor: alpha(theme.palette.primary.main, 0.08), minWidth: 130 }}>
                Qualidade
              </TableCell>
              <TableCell align="center" sx={{ fontWeight: 700, fontSize: 12, bgcolor: alpha(theme.palette.primary.main, 0.08) }}>
                Hrs Operando
              </TableCell>
              <TableCell align="center" sx={{ fontWeight: 700, fontSize: 12, bgcolor: alpha(theme.palette.primary.main, 0.08) }}>
                Hrs Parado
              </TableCell>
              <TableCell align="center" sx={{ fontWeight: 700, fontSize: 12, bgcolor: alpha(theme.palette.primary.main, 0.08) }}>
                MTBF
              </TableCell>
              <TableCell align="center" sx={{ fontWeight: 700, fontSize: 12, bgcolor: alpha(theme.palette.primary.main, 0.08) }}>
                MTTR
              </TableCell>
              <TableCell align="center" sx={{ fontWeight: 700, fontSize: 12, bgcolor: alpha(theme.palette.primary.main, 0.08) }}>
                Falhas
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {equipment.map((eq) => {
              const oeeColor = eq.oee >= 85 ? theme.palette.success.main :
                              eq.oee >= 70 ? theme.palette.warning.main :
                              theme.palette.error.main;
              const availColor = eq.availability >= 95 ? theme.palette.success.main :
                                eq.availability >= 85 ? theme.palette.warning.main :
                                theme.palette.error.main;
              const perfColor = eq.performance >= 90 ? theme.palette.success.main :
                               eq.performance >= 80 ? theme.palette.warning.main :
                               theme.palette.error.main;
              const qualColor = eq.quality >= 99 ? theme.palette.success.main :
                               eq.quality >= 95 ? theme.palette.warning.main :
                               theme.palette.error.main;

              return (
                <TableRow
                  key={eq.id}
                  onClick={() => onEquipmentClick?.(eq)}
                  sx={{
                    cursor: onEquipmentClick ? 'pointer' : 'default',
                    '&:hover': {
                      bgcolor: alpha(theme.palette.primary.main, onEquipmentClick ? 0.08 : 0.04),
                      transform: onEquipmentClick ? 'scale(1.002)' : 'none',
                      boxShadow: onEquipmentClick ? `inset 4px 0 0 ${theme.palette.primary.main}` : 'none'
                    },
                    bgcolor: eq.status === 'critical' ? alpha(theme.palette.error.main, 0.04) : 'transparent',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <TableCell>
                    <Stack direction="row" alignItems="center" spacing={1}>
                      {getStatusIcon(eq.status)}
                      <Box sx={{ flex: 1 }}>
                        <Stack direction="row" alignItems="center" spacing={0.5}>
                          <Typography variant="body2" fontWeight={600} sx={{ fontSize: 13 }}>
                            {eq.name}
                          </Typography>
                          {onEquipmentClick && (
                            <OpenInNew sx={{ fontSize: 14, color: 'primary.main', opacity: 0.6 }} />
                          )}
                        </Stack>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: 11 }}>
                          {eq.area} | {eq.type}
                        </Typography>
                      </Box>
                    </Stack>
                  </TableCell>
                  <TableCell>
                    <ProgressCell value={eq.oee} color={oeeColor} />
                  </TableCell>
                  <TableCell>
                    <ProgressCell value={eq.availability} color={availColor} />
                  </TableCell>
                  <TableCell>
                    <ProgressCell value={eq.performance} color={perfColor} />
                  </TableCell>
                  <TableCell>
                    <ProgressCell value={eq.quality} color={qualColor} />
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="body2" fontWeight={600} color="success.main" sx={{ fontSize: 13 }}>
                      {formatNumber(eq.hours_operating, 1)}h
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="body2" fontWeight={600} color="error.main" sx={{ fontSize: 13 }}>
                      {formatNumber(eq.hours_unplanned_downtime, 1)}h
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="body2" sx={{ fontSize: 13 }}>
                      {formatNumber(eq.mtbf_hours, 1)}h
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="body2" sx={{ fontSize: 13 }}>
                      {formatNumber(eq.mttr_hours, 1)}h
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={eq.num_failures}
                      size="small"
                      color={eq.num_failures > 3 ? 'error' : eq.num_failures > 1 ? 'warning' : 'default'}
                      sx={{ fontWeight: 700, minWidth: 32 }}
                    />
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Summary row */}
      <Paper sx={{ mt: 2, p: 2, bgcolor: alpha(theme.palette.grey[100], 0.5) }}>
        <Grid container spacing={3}>
          <Grid item xs={3}>
            <Typography variant="caption" color="text.secondary">Total Horas Operando</Typography>
            <Typography variant="h5" fontWeight={700} color="success.main">
              {formatNumber(aggregated.total_operating_hours, 1)}h
            </Typography>
          </Grid>
          <Grid item xs={3}>
            <Typography variant="caption" color="text.secondary">Total Horas Parado</Typography>
            <Typography variant="h5" fontWeight={700} color="error.main">
              {formatNumber(aggregated.total_downtime_hours, 1)}h
            </Typography>
          </Grid>
          <Grid item xs={3}>
            <Typography variant="caption" color="text.secondary">Produção Total</Typography>
            <Typography variant="h5" fontWeight={700} color="primary.main">
              {aggregated.total_production.toLocaleString()}
            </Typography>
          </Grid>
          <Grid item xs={3}>
            <Typography variant="caption" color="text.secondary">Taxa de Defeitos</Typography>
            <Typography variant="h5" fontWeight={700} color={aggregated.overall_defect_rate > 1 ? 'error.main' : 'success.main'}>
              {formatNumber(aggregated.overall_defect_rate, 2)}%
            </Typography>
          </Grid>
        </Grid>
      </Paper>
    </Paper>
  );
};

// Insights Panel
const InsightsPanel: React.FC<{ insights: OEEOverview['insights'] }> = ({ insights }) => {
  const theme = useTheme();

  if (!insights || insights.length === 0) return null;

  return (
    <Paper sx={{ p: 2.5 }}>
      <Stack direction="row" alignItems="center" spacing={1} mb={2}>
        <Engineering sx={{ color: theme.palette.warning.main, fontSize: 24 }} />
        <Typography variant="h6" fontWeight={700}>Insights e Recomendações</Typography>
      </Stack>

      <Grid container spacing={2}>
        {insights.map((insight, index) => (
          <Grid item xs={12} md={4} key={index}>
            <Alert
              severity={insight.type === 'error' ? 'error' : insight.type === 'warning' ? 'warning' : 'info'}
              sx={{
                height: '100%',
                '& .MuiAlert-message': { width: '100%' },
                '& .MuiAlert-icon': { fontSize: 28 }
              }}
            >
              <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                {insight.icon} {insight.title}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                {insight.description}
              </Typography>
              {insight.recommendation && (
                <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  Recomendação: {insight.recommendation}
                </Typography>
              )}
            </Alert>
          </Grid>
        ))}
      </Grid>
    </Paper>
  );
};

// === SPRINT 2: OEE Alerts Drawer ===
interface AlertsDrawerProps {
  open: boolean;
  onClose: () => void;
  alerts: OEEAlert[];
  onAcknowledge: (alertId: string) => void;
  onClearAll: () => void;
  config: AlertConfig;
  onConfigChange: (config: AlertConfig) => void;
}

const AlertsDrawer: React.FC<AlertsDrawerProps> = ({
  open,
  onClose,
  alerts,
  onAcknowledge,
  onClearAll,
  config,
  onConfigChange
}) => {
  const theme = useTheme();
  const [showConfig, setShowConfig] = useState(false);

  const getSeverityColor = (severity: OEEAlert['severity']) => {
    switch (severity) {
      case 'critical': return theme.palette.error.main;
      case 'warning': return theme.palette.warning.main;
      case 'info': return theme.palette.info.main;
      case 'success': return theme.palette.success.main;
      default: return theme.palette.grey[500];
    }
  };

  const getSeverityIcon = (severity: OEEAlert['severity']) => {
    switch (severity) {
      case 'critical': return <ErrorIcon sx={{ color: 'error.main' }} />;
      case 'warning': return <Warning sx={{ color: 'warning.main' }} />;
      case 'info': return <Info sx={{ color: 'info.main' }} />;
      case 'success': return <CheckCircle sx={{ color: 'success.main' }} />;
      default: return <Notifications />;
    }
  };

  const unacknowledgedCount = alerts.filter(a => !a.acknowledged).length;

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: { width: { xs: '100%', sm: 420 } }
      }}
    >
      <Box sx={{
        p: 2,
        background: `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 100%)`,
        color: 'white'
      }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Stack direction="row" alignItems="center" spacing={1}>
            <NotificationsActive sx={{ fontSize: 28 }} />
            <Typography variant="h6" fontWeight={700}>
              Alertas OEE
            </Typography>
            {unacknowledgedCount > 0 && (
              <Chip
                label={unacknowledgedCount}
                size="small"
                sx={{ bgcolor: 'error.main', color: 'white', fontWeight: 700 }}
              />
            )}
          </Stack>
          <Stack direction="row" spacing={1}>
            <IconButton onClick={() => setShowConfig(!showConfig)} sx={{ color: 'white' }}>
              <Settings />
            </IconButton>
            <IconButton onClick={onClose} sx={{ color: 'white' }}>
              <Close />
            </IconButton>
          </Stack>
        </Stack>
      </Box>

      {/* Config Panel */}
      <Collapse in={showConfig}>
        <Paper sx={{ m: 2, p: 2, bgcolor: alpha(theme.palette.info.main, 0.05) }}>
          <Typography variant="subtitle2" fontWeight={700} gutterBottom>
            Configurar Alertas
          </Typography>
          <Stack spacing={2}>
            <FormControlLabel
              control={
                <Switch
                  checked={config.enabled}
                  onChange={(e) => onConfigChange({ ...config, enabled: e.target.checked })}
                />
              }
              label="Alertas Habilitados"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={config.soundEnabled}
                  onChange={(e) => onConfigChange({ ...config, soundEnabled: e.target.checked })}
                />
              }
              label="Som de Alerta"
            />
            <Divider />
            <Typography variant="caption" fontWeight={600}>Limiares de Alerta</Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  label="OEE Mínimo"
                  type="number"
                  size="small"
                  fullWidth
                  value={config.oeeThreshold}
                  onChange={(e) => onConfigChange({ ...config, oeeThreshold: Number(e.target.value) })}
                  InputProps={{ endAdornment: '%' }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  label="Queda Máxima"
                  type="number"
                  size="small"
                  fullWidth
                  value={config.dropPercentageAlert}
                  onChange={(e) => onConfigChange({ ...config, dropPercentageAlert: Number(e.target.value) })}
                  InputProps={{ endAdornment: '%' }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  label="Disponibilidade"
                  type="number"
                  size="small"
                  fullWidth
                  value={config.availabilityThreshold}
                  onChange={(e) => onConfigChange({ ...config, availabilityThreshold: Number(e.target.value) })}
                  InputProps={{ endAdornment: '%' }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  label="Performance"
                  type="number"
                  size="small"
                  fullWidth
                  value={config.performanceThreshold}
                  onChange={(e) => onConfigChange({ ...config, performanceThreshold: Number(e.target.value) })}
                  InputProps={{ endAdornment: '%' }}
                />
              </Grid>
            </Grid>
          </Stack>
        </Paper>
      </Collapse>

      {/* Alerts List */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {alerts.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <NotificationsOff sx={{ fontSize: 64, color: 'grey.300', mb: 2 }} />
            <Typography color="text.secondary">
              Nenhum alerta ativo
            </Typography>
          </Box>
        ) : (
          <Stack spacing={2}>
            {alerts.map((alert) => (
              <Paper
                key={alert.id}
                sx={{
                  p: 2,
                  borderLeft: `4px solid ${getSeverityColor(alert.severity)}`,
                  bgcolor: alert.acknowledged ? alpha(theme.palette.grey[100], 0.5) : alpha(getSeverityColor(alert.severity), 0.05),
                  opacity: alert.acknowledged ? 0.7 : 1,
                  transition: 'all 0.2s ease'
                }}
              >
                <Stack direction="row" spacing={1.5} alignItems="flex-start">
                  {getSeverityIcon(alert.severity)}
                  <Box sx={{ flex: 1 }}>
                    <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                      <Typography variant="subtitle2" fontWeight={700}>
                        {alert.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {alert.timestamp.toLocaleTimeString('pt-BR')}
                      </Typography>
                    </Stack>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                      {alert.message}
                    </Typography>
                    {alert.equipmentName && (
                      <Chip
                        size="small"
                        label={alert.equipmentName}
                        sx={{ mt: 1, bgcolor: alpha(theme.palette.primary.main, 0.1) }}
                      />
                    )}
                    <Stack direction="row" alignItems="center" spacing={1} sx={{ mt: 1 }}>
                      <Stack direction="row" alignItems="center" spacing={0.5}>
                        {alert.previousValue !== undefined && (
                          <>
                            <Typography variant="caption" color="text.secondary">
                              {formatNumber(alert.previousValue, 1)}%
                            </Typography>
                            <ArrowDownward sx={{ fontSize: 14, color: 'error.main' }} />
                          </>
                        )}
                        <Typography
                          variant="caption"
                          fontWeight={700}
                          sx={{ color: getSeverityColor(alert.severity) }}
                        >
                          {formatNumber(alert.currentValue, 1)}%
                        </Typography>
                      </Stack>
                      {!alert.acknowledged && (
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => onAcknowledge(alert.id)}
                          sx={{ ml: 'auto' }}
                        >
                          Reconhecer
                        </Button>
                      )}
                    </Stack>
                  </Box>
                </Stack>
              </Paper>
            ))}
          </Stack>
        )}
      </Box>

      {/* Footer Actions */}
      {alerts.length > 0 && (
        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Button
            fullWidth
            variant="outlined"
            color="error"
            onClick={onClearAll}
            startIcon={<Close />}
          >
            Limpar Todos os Alertas
          </Button>
        </Box>
      )}
    </Drawer>
  );
};

// === SPRINT 2: Equipment Drill-Down Modal ===
interface EquipmentDrillDownModalProps {
  open: boolean;
  onClose: () => void;
  equipment: EquipmentData['equipment'][0] | null;
  timeRange: string;
  onClassifyDowntime: (eventId: string, category: string, notes: string) => void;
}

const EquipmentDrillDownModal: React.FC<EquipmentDrillDownModalProps> = ({
  open,
  onClose,
  equipment,
  timeRange,
  onClassifyDowntime
}) => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [downtimeEvents, setDowntimeEvents] = useState<EquipmentDetails['downtime_events']>([]);
  const [hourlyOEE, setHourlyOEE] = useState<EquipmentDetails['hourly_oee']>([]);
  const [classifyingEvent, setClassifyingEvent] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [classificationNotes, setClassificationNotes] = useState('');
  const [loading, setLoading] = useState(false);

  // Simulated data for demo - in production this would come from API
  React.useEffect(() => {
    if (equipment && open) {
      setLoading(true);
      // Simulate API call
      setTimeout(() => {
        // Generate mock downtime events
        const mockDowntimeEvents: EquipmentDetails['downtime_events'] = [
          {
            id: '1',
            start_time: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
            end_time: new Date(Date.now() - 3.5 * 60 * 60 * 1000).toISOString(),
            duration_minutes: 30,
            type: 'unplanned',
            category: 'mechanical_failure',
            reason: 'Falha no motor principal',
            notes: 'Substituído rolamento danificado',
            classified: true,
            classified_by: 'João Silva'
          },
          {
            id: '2',
            start_time: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            end_time: new Date(Date.now() - 1.75 * 60 * 60 * 1000).toISOString(),
            duration_minutes: 15,
            type: 'setup',
            category: 'setup_changeover',
            reason: 'Troca de produto',
            notes: '',
            classified: true,
            classified_by: 'Maria Santos'
          },
          {
            id: '3',
            start_time: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
            end_time: null,
            duration_minutes: 45,
            type: 'unplanned',
            category: '',
            reason: 'Parada não identificada',
            notes: '',
            classified: false,
            classified_by: null
          }
        ];

        // Generate mock hourly OEE
        const mockHourlyOEE: EquipmentDetails['hourly_oee'] = [];
        for (let i = 23; i >= 0; i--) {
          const hour = new Date(Date.now() - i * 60 * 60 * 1000);
          const baseOEE = 75 + Math.random() * 20;
          mockHourlyOEE.push({
            hour: hour.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
            oee: baseOEE,
            availability: 85 + Math.random() * 12,
            performance: 80 + Math.random() * 15,
            quality: 95 + Math.random() * 4
          });
        }

        setDowntimeEvents(mockDowntimeEvents);
        setHourlyOEE(mockHourlyOEE);
        setLoading(false);
      }, 500);
    }
  }, [equipment, open]);

  const handleClassifySubmit = () => {
    if (classifyingEvent && selectedCategory) {
      onClassifyDowntime(classifyingEvent, selectedCategory, classificationNotes);
      // Update local state
      setDowntimeEvents(prev => prev.map(evt =>
        evt.id === classifyingEvent
          ? { ...evt, category: selectedCategory, notes: classificationNotes, classified: true, classified_by: 'Você' }
          : evt
      ));
      setClassifyingEvent(null);
      setSelectedCategory('');
      setClassificationNotes('');
    }
  };

  if (!equipment) return null;

  const getStateColor = (state: string) => {
    switch (state) {
      case 'running': return theme.palette.success.main;
      case 'stopped': return theme.palette.error.main;
      case 'idle': return theme.palette.warning.main;
      case 'maintenance': return theme.palette.info.main;
      default: return theme.palette.grey[500];
    }
  };

  const getStateLabel = (state: string) => {
    switch (state) {
      case 'running': return 'Em Operação';
      case 'stopped': return 'Parado';
      case 'idle': return 'Ocioso';
      case 'maintenance': return 'Manutenção';
      default: return state;
    }
  };

  const unclassifiedCount = downtimeEvents.filter(e => !e.classified).length;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { minHeight: '80vh' }
      }}
    >
      <DialogTitle sx={{
        background: `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 100%)`,
        color: 'white',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Stack direction="row" alignItems="center" spacing={2}>
          <PrecisionManufacturing sx={{ fontSize: 32 }} />
          <Box>
            <Typography variant="h5" fontWeight={700}>
              {equipment.name}
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              {equipment.area} | {equipment.type}
            </Typography>
          </Box>
          <Chip
            label={getStateLabel(equipment.status)}
            sx={{
              bgcolor: alpha(getStateColor(equipment.status), 0.2),
              color: 'white',
              fontWeight: 600,
              border: `1px solid ${alpha('#fff', 0.3)}`
            }}
          />
        </Stack>
        <IconButton onClick={onClose} sx={{ color: 'white' }}>
          <Close />
        </IconButton>
      </DialogTitle>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
          <Tab label="Visão Geral" icon={<BarChartIcon />} iconPosition="start" />
          <Tab
            label={
              <Badge badgeContent={unclassifiedCount} color="error">
                Eventos de Parada
              </Badge>
            }
            icon={<Timeline />}
            iconPosition="start"
          />
          <Tab label="Tendência OEE" icon={<TrendingUp />} iconPosition="start" />
          <Tab label="Perdas" icon={<Report />} iconPosition="start" />
        </Tabs>
      </Box>

      <DialogContent sx={{ bgcolor: alpha(theme.palette.grey[100], 0.5) }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <Typography>Carregando detalhes...</Typography>
          </Box>
        ) : (
          <>
            {/* Tab 0: Overview */}
            {activeTab === 0 && (
              <Grid container spacing={3} sx={{ mt: 0 }}>
                {/* OEE Components */}
                <Grid item xs={12}>
                  <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" fontWeight={700} gutterBottom>
                      Indicadores OEE
                    </Typography>
                    <Grid container spacing={3}>
                      {[
                        { label: 'OEE', value: equipment.oee, target: 85, color: theme.palette.primary.main },
                        { label: 'Disponibilidade', value: equipment.availability, target: 95, color: theme.palette.success.main },
                        { label: 'Performance', value: equipment.performance, target: 90, color: theme.palette.warning.main },
                        { label: 'Qualidade', value: equipment.quality, target: 99, color: theme.palette.info.main },
                      ].map((metric) => (
                        <Grid item xs={6} md={3} key={metric.label}>
                          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: alpha(metric.color, 0.08), border: `1px solid ${alpha(metric.color, 0.2)}` }}>
                            <Typography variant="body2" color="text.secondary" fontWeight={600}>
                              {metric.label}
                            </Typography>
                            <Typography variant="h3" fontWeight={800} sx={{ color: metric.value >= metric.target * 0.9 ? metric.color : theme.palette.error.main }}>
                              {formatNumber(metric.value, 1)}%
                            </Typography>
                            <LinearProgress
                              variant="determinate"
                              value={Math.min(metric.value, 100)}
                              sx={{
                                mt: 1,
                                height: 8,
                                borderRadius: 4,
                                bgcolor: alpha(metric.color, 0.15),
                                '& .MuiLinearProgress-bar': { borderRadius: 4, bgcolor: metric.value >= metric.target * 0.9 ? metric.color : theme.palette.error.main }
                              }}
                            />
                            <Typography variant="caption" color="text.secondary">
                              Meta: {metric.target}%
                            </Typography>
                          </Paper>
                        </Grid>
                      ))}
                    </Grid>
                  </Paper>
                </Grid>

                {/* Metrics */}
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 3, height: '100%' }}>
                    <Typography variant="h6" fontWeight={700} gutterBottom>
                      <Timer sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Tempo de Operação
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">Horas Operando</Typography>
                        <Typography variant="h5" fontWeight={700} color="success.main">{formatNumber(equipment.hours_operating, 1)}h</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">Parada Não Planejada</Typography>
                        <Typography variant="h5" fontWeight={700} color="error.main">{formatNumber(equipment.hours_unplanned_downtime, 1)}h</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">Parada Planejada</Typography>
                        <Typography variant="h5" fontWeight={700} color="info.main">{formatNumber(equipment.hours_planned_downtime || 0, 1)}h</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">Ocioso</Typography>
                        <Typography variant="h5" fontWeight={700} color="warning.main">{formatNumber(equipment.hours_idle, 1)}h</Typography>
                      </Grid>
                    </Grid>
                  </Paper>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 3, height: '100%' }}>
                    <Typography variant="h6" fontWeight={700} gutterBottom>
                      <Assignment sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Métricas de Manutenção
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">MTBF (Tempo Médio Entre Falhas)</Typography>
                        <Typography variant="h5" fontWeight={700}>{formatNumber(equipment.mtbf_hours, 1)}h</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">MTTR (Tempo Médio de Reparo)</Typography>
                        <Typography variant="h5" fontWeight={700}>{formatNumber(equipment.mttr_hours, 2)}h</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">Número de Falhas</Typography>
                        <Typography variant="h5" fontWeight={700} color={equipment.num_failures > 3 ? 'error.main' : 'text.primary'}>
                          {equipment.num_failures}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">Taxa de Defeitos</Typography>
                        <Typography variant="h5" fontWeight={700} color={equipment.defect_rate > 1 ? 'error.main' : 'success.main'}>
                          {formatNumber(equipment.defect_rate, 2)}%
                        </Typography>
                      </Grid>
                    </Grid>
                  </Paper>
                </Grid>
              </Grid>
            )}

            {/* Tab 1: Downtime Events */}
            {activeTab === 1 && (
              <Paper sx={{ p: 3, mt: 2 }}>
                <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6" fontWeight={700}>
                    <Timeline sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Eventos de Parada ({downtimeEvents.length})
                  </Typography>
                  {unclassifiedCount > 0 && (
                    <Alert severity="warning" sx={{ py: 0 }}>
                      {unclassifiedCount} evento(s) não classificado(s)
                    </Alert>
                  )}
                </Stack>

                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 700 }}>Início</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Fim</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Duração</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Tipo</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Categoria</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Motivo</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Ações</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {downtimeEvents.map((event) => (
                        <React.Fragment key={event.id}>
                          <TableRow sx={{
                            bgcolor: !event.classified ? alpha(theme.palette.warning.main, 0.08) : 'transparent',
                            '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.04) }
                          }}>
                            <TableCell>{new Date(event.start_time).toLocaleString('pt-BR')}</TableCell>
                            <TableCell>{event.end_time ? new Date(event.end_time).toLocaleString('pt-BR') : <Chip size="small" label="Em andamento" color="error" />}</TableCell>
                            <TableCell>
                              <Typography fontWeight={600}>
                                {event.duration_minutes >= 60
                                  ? `${Math.floor(event.duration_minutes / 60)}h ${event.duration_minutes % 60}min`
                                  : `${event.duration_minutes} min`}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip
                                size="small"
                                label={event.type === 'planned' ? 'Planejada' : event.type === 'setup' ? 'Setup' : event.type === 'idle' ? 'Ociosa' : 'Não Planejada'}
                                color={event.type === 'planned' ? 'info' : event.type === 'unplanned' ? 'error' : 'warning'}
                              />
                            </TableCell>
                            <TableCell>
                              {event.category
                                ? DOWNTIME_CATEGORIES.find(c => c.value === event.category)?.label || event.category
                                : <Typography color="text.secondary" fontStyle="italic">Não classificado</Typography>
                              }
                            </TableCell>
                            <TableCell>{event.reason}</TableCell>
                            <TableCell>
                              {event.classified ? (
                                <Chip size="small" icon={<CheckCircle />} label={`Por: ${event.classified_by}`} color="success" variant="outlined" />
                              ) : (
                                <Chip size="small" icon={<Warning />} label="Pendente" color="warning" />
                              )}
                            </TableCell>
                            <TableCell>
                              {!event.classified && (
                                <Button
                                  size="small"
                                  variant="contained"
                                  color="primary"
                                  onClick={() => setClassifyingEvent(classifyingEvent === event.id ? null : event.id)}
                                >
                                  Classificar
                                </Button>
                              )}
                            </TableCell>
                          </TableRow>
                          {/* Classification form */}
                          <TableRow>
                            <TableCell colSpan={8} sx={{ p: 0 }}>
                              <Collapse in={classifyingEvent === event.id}>
                                <Box sx={{ p: 2, bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
                                  <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                                    Classificar Parada
                                  </Typography>
                                  <Grid container spacing={2} alignItems="flex-end">
                                    <Grid item xs={12} md={4}>
                                      <FormControl fullWidth size="small">
                                        <Typography variant="caption" fontWeight={600} gutterBottom>Categoria</Typography>
                                        <Select
                                          value={selectedCategory}
                                          onChange={(e) => setSelectedCategory(e.target.value)}
                                          displayEmpty
                                        >
                                          <MenuItem value="" disabled>Selecione a categoria</MenuItem>
                                          {DOWNTIME_CATEGORIES.map((cat) => (
                                            <MenuItem key={cat.value} value={cat.value}>
                                              <Stack direction="row" alignItems="center" spacing={1}>
                                                {cat.icon}
                                                <span>{cat.label}</span>
                                              </Stack>
                                            </MenuItem>
                                          ))}
                                        </Select>
                                      </FormControl>
                                    </Grid>
                                    <Grid item xs={12} md={5}>
                                      <Typography variant="caption" fontWeight={600} gutterBottom>Observações</Typography>
                                      <input
                                        type="text"
                                        value={classificationNotes}
                                        onChange={(e) => setClassificationNotes(e.target.value)}
                                        placeholder="Adicione detalhes sobre a parada..."
                                        style={{
                                          width: '100%',
                                          padding: '8px 12px',
                                          borderRadius: '4px',
                                          border: `1px solid ${theme.palette.divider}`,
                                          fontSize: '14px'
                                        }}
                                      />
                                    </Grid>
                                    <Grid item xs={12} md={3}>
                                      <Stack direction="row" spacing={1}>
                                        <Button
                                          variant="contained"
                                          color="primary"
                                          onClick={handleClassifySubmit}
                                          disabled={!selectedCategory}
                                        >
                                          Salvar
                                        </Button>
                                        <Button
                                          variant="outlined"
                                          onClick={() => {
                                            setClassifyingEvent(null);
                                            setSelectedCategory('');
                                            setClassificationNotes('');
                                          }}
                                        >
                                          Cancelar
                                        </Button>
                                      </Stack>
                                    </Grid>
                                  </Grid>
                                </Box>
                              </Collapse>
                            </TableCell>
                          </TableRow>
                        </React.Fragment>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            )}

            {/* Tab 2: OEE Trend */}
            {activeTab === 2 && (
              <Paper sx={{ p: 3, mt: 2 }}>
                <Typography variant="h6" fontWeight={700} gutterBottom>
                  <TrendingUp sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Tendência de OEE (Últimas 24h)
                </Typography>
                <Box sx={{ height: 400 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={hourlyOEE} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={alpha(theme.palette.divider, 0.5)} />
                      <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                      <RechartsTooltip
                        contentStyle={{ fontSize: 12, borderRadius: 8 }}
                        formatter={(value: number, name: string) => [`${formatNumber(value, 1)}%`, name]}
                      />
                      <Bar dataKey="oee" name="OEE" fill={theme.palette.primary.main} radius={[4, 4, 0, 0]} barSize={12} />
                      <Line type="monotone" dataKey="availability" name="Disponibilidade" stroke={theme.palette.success.main} strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="performance" name="Performance" stroke={theme.palette.warning.main} strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="quality" name="Qualidade" stroke={theme.palette.info.main} strokeWidth={2} dot={false} />
                    </ComposedChart>
                  </ResponsiveContainer>
                </Box>
              </Paper>
            )}

            {/* Tab 3: Losses Breakdown */}
            {activeTab === 3 && (
              <Paper sx={{ p: 3, mt: 2 }}>
                <Typography variant="h6" fontWeight={700} gutterBottom>
                  <Report sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Detalhamento de Perdas
                </Typography>
                <Grid container spacing={2}>
                  {[
                    { label: 'Falhas de Equipamento', value: equipment.hours_unplanned_downtime * 0.4, color: '#e53935', category: 'Disponibilidade' },
                    { label: 'Setup e Ajustes', value: equipment.hours_unplanned_downtime * 0.2, color: '#ef5350', category: 'Disponibilidade' },
                    { label: 'Paradas Menores', value: equipment.hours_idle * 0.5, color: '#ff9800', category: 'Performance' },
                    { label: 'Velocidade Reduzida', value: equipment.hours_idle * 0.5, color: '#ffa726', category: 'Performance' },
                    { label: 'Defeitos de Processo', value: equipment.defect_pieces * 0.01, color: '#2196f3', category: 'Qualidade' },
                    { label: 'Redução de Rendimento', value: equipment.defect_pieces * 0.005, color: '#42a5f5', category: 'Qualidade' },
                  ].map((loss) => (
                    <Grid item xs={12} md={6} key={loss.label}>
                      <Paper sx={{ p: 2, bgcolor: alpha(loss.color, 0.08), border: `1px solid ${alpha(loss.color, 0.2)}` }}>
                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                          <Box>
                            <Typography variant="body2" fontWeight={600}>{loss.label}</Typography>
                            <Typography variant="caption" color="text.secondary">{loss.category}</Typography>
                          </Box>
                          <Typography variant="h5" fontWeight={700} sx={{ color: loss.color }}>
                            {formatNumber(loss.value, 2)}h
                          </Typography>
                        </Stack>
                        <LinearProgress
                          variant="determinate"
                          value={Math.min((loss.value / equipment.total_loss_hours) * 100, 100)}
                          sx={{
                            mt: 1,
                            height: 6,
                            borderRadius: 3,
                            bgcolor: alpha(loss.color, 0.15),
                            '& .MuiLinearProgress-bar': { borderRadius: 3, bgcolor: loss.color }
                          }}
                        />
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </Paper>
            )}
          </>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Button startIcon={<Download />} variant="outlined">
          Exportar Relatório
        </Button>
        <Button onClick={onClose} variant="contained">
          Fechar
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Main Component
export const OEEDashboard: React.FC = () => {
  const theme = useTheme();

  // === SPRINT 6: Global filter store integration ===
  const {
    timeRange: globalTimeRange,
    selectedEquipments: globalSelectedEquipments,
    selectedAreas: globalSelectedAreas,
    crossFilterEnabled,
    setTimeRangePreset,
    setEquipments,
    drillDown,
  } = useFilterStore();

  // URL sync
  useURLFilters({ enabled: true });

  // Map global time range to local format
  const timeRange = globalTimeRange.preset;

  // === SPRINT 2: Drill-down state ===
  const [selectedEquipment, setSelectedEquipment] = useState<EquipmentData['equipment'][0] | null>(null);
  const [drillDownOpen, setDrillDownOpen] = useState(false);

  // === SPRINT 2: Alerts state ===
  const [alerts, setAlerts] = useState<OEEAlert[]>([]);
  const [alertConfig, setAlertConfig] = useState<AlertConfig>(DEFAULT_ALERT_CONFIG);
  const [alertsDrawerOpen, setAlertsDrawerOpen] = useState(false);
  const [snackbarAlert, setSnackbarAlert] = useState<OEEAlert | null>(null);
  const [previousOEE, setPreviousOEE] = useState<number | null>(null);

  const handleEquipmentClick = (equipment: EquipmentData['equipment'][0]) => {
    setSelectedEquipment(equipment);
    setDrillDownOpen(true);

    // Sprint 6: Update global drill-down path
    drillDown('equipment', equipment.id, equipment.name);

    // Cross-filter: if enabled, filter to this equipment globally
    if (crossFilterEnabled) {
      setEquipments([equipment.id]);
    }
  };

  const handleCloseDrillDown = () => {
    setDrillDownOpen(false);
    setSelectedEquipment(null);
  };

  const handleClassifyDowntime = (eventId: string, category: string, notes: string) => {
    // In production, this would call the API
    console.log('Classifying downtime:', { eventId, category, notes });
    // apiClient.post(`/api/v1/oee/downtime/${eventId}/classify`, { category, notes });
  };

  // === SPRINT 2: Alert handlers ===
  const handleAcknowledgeAlert = (alertId: string) => {
    setAlerts(prev => prev.map(a =>
      a.id === alertId ? { ...a, acknowledged: true } : a
    ));
  };

  const handleClearAllAlerts = () => {
    setAlerts([]);
  };

  const addAlert = useCallback((alert: Omit<OEEAlert, 'id' | 'timestamp' | 'acknowledged'>) => {
    const newAlert: OEEAlert = {
      ...alert,
      id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      acknowledged: false
    };
    setAlerts(prev => [newAlert, ...prev].slice(0, 50)); // Keep last 50 alerts
    setSnackbarAlert(newAlert);
  }, []);

  // === SPRINT 2: Export state and handlers ===
  const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);

  const handleExportClick = (event: React.MouseEvent<HTMLElement>) => {
    setExportMenuAnchor(event.currentTarget);
  };

  const handleExportClose = () => {
    setExportMenuAnchor(null);
  };

  const handleExportPDF = async () => {
    handleExportClose();
    setIsExporting(true);
    try {
      const response = await apiClient.get(`/api/v1/oee/export/pdf?time_range=${timeRange}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `OEE_Report_${new Date().toISOString().split('T')[0]}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setExportSuccess('PDF');
    } catch (error) {
      console.error('Error exporting PDF:', error);
      // Fallback: Generate simple client-side report
      generateClientSidePDF();
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportExcel = async () => {
    handleExportClose();
    setIsExporting(true);
    try {
      const response = await apiClient.get(`/api/v1/oee/export/excel?time_range=${timeRange}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `OEE_Report_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setExportSuccess('Excel');
    } catch (error) {
      console.error('Error exporting Excel:', error);
      // Fallback: Generate CSV
      generateClientSideCSV();
    } finally {
      setIsExporting(false);
    }
  };

  const generateClientSidePDF = () => {
    // Fallback: Print current view
    window.print();
  };

  const generateClientSideCSV = () => {
    if (!oeeData || !equipmentData) return;

    const csvContent = [
      // Header
      'Relatório OEE - OptiFlow',
      `Período: ${timeRange}`,
      `Gerado em: ${new Date().toLocaleString('pt-BR')}`,
      '',
      // Summary
      'RESUMO OEE',
      `OEE Geral,${oeeData.summary.oee.value}%`,
      `Disponibilidade,${oeeData.summary.availability.value}%`,
      `Performance,${oeeData.summary.performance.value}%`,
      `Qualidade,${oeeData.summary.quality.value}%`,
      '',
      // Losses
      '6 GRANDES PERDAS (Horas)',
      `Falhas de Equipamento,${oeeData.losses.equipment_failure_hours}`,
      `Setup e Ajustes,${oeeData.losses.setup_adjustments_hours}`,
      `Paradas Menores,${oeeData.losses.idling_minor_stops_hours}`,
      `Velocidade Reduzida,${oeeData.losses.reduced_speed_hours}`,
      `Defeitos de Processo,${oeeData.losses.process_defects_hours}`,
      `Redução de Rendimento,${oeeData.losses.reduced_yield_hours}`,
      `Total,${oeeData.losses.total_loss_hours}`,
      '',
      // Equipment
      'EQUIPAMENTOS',
      'Nome,Área,OEE,Disponibilidade,Performance,Qualidade,Horas Operando,Horas Parado,MTBF,MTTR,Falhas',
      ...equipmentData.equipment.map(eq =>
        `${eq.name},${eq.area},${eq.oee}%,${eq.availability}%,${eq.performance}%,${eq.quality}%,${eq.hours_operating},${eq.hours_unplanned_downtime},${eq.mtbf_hours},${eq.mttr_hours},${eq.num_failures}`
      )
    ].join('\n');

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `OEE_Report_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    setExportSuccess('CSV');
  };

  const handlePrint = () => {
    handleExportClose();
    window.print();
  };

  // Fetch functions
  const fetchOEEOverview = useCallback(async () => {
    const response = await apiClient.get(`/api/v1/oee/overview?time_range=${timeRange}`);
    return response.data as OEEOverview;
  }, [timeRange]);

  const fetchEquipmentData = useCallback(async () => {
    const response = await apiClient.get(`/api/v1/oee/equipment?time_range=${timeRange}`);
    return response.data as EquipmentData;
  }, [timeRange]);

  const fetchShiftData = useCallback(async () => {
    const response = await apiClient.get('/api/v1/oee/shifts');
    return response.data as ShiftData;
  }, []);

  const { data: oeeData, loading, error, refresh: loadData, isRetrying } = useAsyncData(fetchOEEOverview, {
    autoRefresh: true,
    refreshInterval: REFRESH_INTERVALS.MEDIUM,
    deps: [timeRange],
    keepPreviousData: true,
  });

  const { data: equipmentData } = useAsyncData(fetchEquipmentData, {
    autoRefresh: true,
    refreshInterval: REFRESH_INTERVALS.MEDIUM,
    deps: [timeRange],
    keepPreviousData: true,
  });

  const { data: shiftData } = useAsyncData(fetchShiftData, {
    autoRefresh: true,
    refreshInterval: REFRESH_INTERVALS.SLOW,
    keepPreviousData: true,
  });

  const handleTimeRangeChange = (event: SelectChangeEvent) => {
    // Sprint 6: Update global filter store instead of local state
    const value = event.target.value as '1h' | '4h' | '8h' | '24h' | '7d' | '30d';
    setTimeRangePreset(value);
  };

  // === SPRINT 2: Monitor OEE changes and generate alerts ===
  useEffect(() => {
    if (!alertConfig.enabled || !oeeData) return;

    const currentOEE = oeeData.summary.oee.value;

    // Check for OEE drop from previous value
    if (previousOEE !== null && currentOEE < previousOEE) {
      const dropPercentage = previousOEE - currentOEE;
      if (dropPercentage >= alertConfig.dropPercentageAlert) {
        addAlert({
          type: 'oee_drop',
          severity: dropPercentage >= 10 ? 'critical' : 'warning',
          title: 'Queda de OEE Detectada',
          message: `OEE caiu ${formatNumber(dropPercentage, 1)} pontos percentuais`,
          currentValue: currentOEE,
          previousValue: previousOEE,
          threshold: alertConfig.dropPercentageAlert
        });
      }
    }

    // Check OEE below threshold
    if (currentOEE < alertConfig.oeeThreshold) {
      const existingAlert = alerts.find(a =>
        a.type === 'oee_drop' &&
        !a.acknowledged &&
        Math.abs(a.currentValue - currentOEE) < 1
      );
      if (!existingAlert) {
        addAlert({
          type: 'oee_drop',
          severity: currentOEE < alertConfig.oeeThreshold * 0.9 ? 'critical' : 'warning',
          title: 'OEE Abaixo do Limite',
          message: `OEE atual (${formatNumber(currentOEE, 1)}%) está abaixo do limite de ${alertConfig.oeeThreshold}%`,
          currentValue: currentOEE,
          threshold: alertConfig.oeeThreshold
        });
      }
    }

    // Check availability below threshold
    if (oeeData.summary.availability.value < alertConfig.availabilityThreshold) {
      const existingAlert = alerts.find(a =>
        a.type === 'availability_drop' &&
        !a.acknowledged &&
        Date.now() - a.timestamp.getTime() < 60000 // Don't repeat within 1 minute
      );
      if (!existingAlert) {
        addAlert({
          type: 'availability_drop',
          severity: 'warning',
          title: 'Disponibilidade Baixa',
          message: `Disponibilidade (${formatNumber(oeeData.summary.availability.value, 1)}%) abaixo do limite`,
          currentValue: oeeData.summary.availability.value,
          threshold: alertConfig.availabilityThreshold
        });
      }
    }

    // Check performance below threshold
    if (oeeData.summary.performance.value < alertConfig.performanceThreshold) {
      const existingAlert = alerts.find(a =>
        a.type === 'performance_drop' &&
        !a.acknowledged &&
        Date.now() - a.timestamp.getTime() < 60000
      );
      if (!existingAlert) {
        addAlert({
          type: 'performance_drop',
          severity: 'warning',
          title: 'Performance Baixa',
          message: `Performance (${formatNumber(oeeData.summary.performance.value, 1)}%) abaixo do limite`,
          currentValue: oeeData.summary.performance.value,
          threshold: alertConfig.performanceThreshold
        });
      }
    }

    // Update previous OEE for next comparison
    setPreviousOEE(currentOEE);
  }, [oeeData, alertConfig, addAlert, previousOEE, alerts]);

  // Check equipment critical status
  useEffect(() => {
    if (!alertConfig.enabled || !equipmentData) return;

    equipmentData.equipment.forEach(eq => {
      if (eq.status === 'critical') {
        const existingAlert = alerts.find(a =>
          a.type === 'equipment_critical' &&
          a.equipmentId === eq.id &&
          !a.acknowledged &&
          Date.now() - a.timestamp.getTime() < 300000 // Don't repeat within 5 minutes
        );
        if (!existingAlert) {
          addAlert({
            type: 'equipment_critical',
            severity: 'critical',
            title: 'Equipamento Crítico',
            message: `${eq.name} está em estado crítico com OEE de ${formatNumber(eq.oee, 1)}%`,
            equipmentId: eq.id,
            equipmentName: eq.name,
            currentValue: eq.oee,
            threshold: alertConfig.oeeThreshold
          });
        }
      }
    });
  }, [equipmentData, alertConfig, addAlert, alerts]);

  // Count unacknowledged alerts
  const unacknowledgedAlertCount = useMemo(() =>
    alerts.filter(a => !a.acknowledged).length,
    [alerts]
  );

  if (loading && !oeeData) {
    return (
      <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', pt: 4 }}>
        <LoadingState message="Carregando dados de OEE..." size="lg" />
      </Box>
    );
  }

  if (error && !oeeData) {
    return (
      <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', pt: 4 }}>
        <ErrorState message={error} onRetry={loadData} isRetrying={isRetrying} />
      </Box>
    );
  }

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh' }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 100%)`,
          color: 'white',
          borderRadius: 0,
          py: 2.5,
          px: 3
        }}
      >
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Stack direction="row" alignItems="center" spacing={2}>
            <Speed sx={{ fontSize: 40 }} />
            <Box>
              <Typography variant="h4" fontWeight={800}>
                OEE Dashboard
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Overall Equipment Effectiveness | Efetividade Global dos Equipamentos
              </Typography>
            </Box>
          </Stack>

          <Stack direction="row" spacing={2} alignItems="center">
            <Chip
              label={new Date().toLocaleString('pt-BR')}
              sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', fontWeight: 600 }}
            />
            <FormControl size="small" sx={{ minWidth: 120, bgcolor: 'rgba(255,255,255,0.15)', borderRadius: 1 }}>
              <Select
                value={timeRange}
                onChange={handleTimeRangeChange}
                sx={{ color: 'white', '& .MuiSvgIcon-root': { color: 'white' }, fontWeight: 600 }}
              >
                <MenuItem value="1h">1 hora</MenuItem>
                <MenuItem value="6h">6 horas</MenuItem>
                <MenuItem value="24h">24 horas</MenuItem>
                <MenuItem value="7d">7 dias</MenuItem>
                <MenuItem value="30d">30 dias</MenuItem>
              </Select>
            </FormControl>
            <Tooltip title="Atualizar dados">
              <IconButton sx={{ color: 'white' }} onClick={loadData}>
                <Refresh />
              </IconButton>
            </Tooltip>
            <Tooltip title="Alertas OEE">
              <IconButton sx={{ color: 'white' }} onClick={() => setAlertsDrawerOpen(true)}>
                <Badge badgeContent={unacknowledgedAlertCount} color="error">
                  {unacknowledgedAlertCount > 0 ? (
                    <NotificationsActive sx={{ animation: 'pulse 1s infinite' }} />
                  ) : (
                    <Notifications />
                  )}
                </Badge>
              </IconButton>
            </Tooltip>
            <Tooltip title="Exportar relatório">
              <IconButton
                sx={{ color: 'white' }}
                onClick={handleExportClick}
                disabled={isExporting}
              >
                {isExporting ? <CircularProgress size={24} color="inherit" /> : <Download />}
              </IconButton>
            </Tooltip>
          </Stack>

          {/* Export Menu */}
          <Menu
            anchorEl={exportMenuAnchor}
            open={Boolean(exportMenuAnchor)}
            onClose={handleExportClose}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
          >
            <MenuItem onClick={handleExportPDF}>
              <ListItemIcon>
                <PictureAsPdf fontSize="small" color="error" />
              </ListItemIcon>
              <ListItemText primary="Exportar PDF" secondary="Relatório completo em PDF" />
            </MenuItem>
            <MenuItem onClick={handleExportExcel}>
              <ListItemIcon>
                <TableChart fontSize="small" color="success" />
              </ListItemIcon>
              <ListItemText primary="Exportar Excel/CSV" secondary="Dados tabulares para análise" />
            </MenuItem>
            <Divider />
            <MenuItem onClick={handlePrint}>
              <ListItemIcon>
                <Print fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Imprimir" secondary="Imprimir visualização atual" />
            </MenuItem>
          </Menu>
        </Stack>
      </Paper>

      {/* Sprint 6: Global Filter Bar */}
      <Box sx={{ px: 3, pt: 2 }}>
        <FilterBar
          showEquipments={true}
          showAreas={true}
          showStatuses={true}
          compact={false}
        />
        <Box sx={{ mt: 1 }}>
          <DrillDownBreadcrumb />
        </Box>
      </Box>

      {/* Main Content */}
      <Box sx={{ p: 3 }}>
        {oeeData && (
          <Stack spacing={3}>
            {/* Row 1: Main OEE Display */}
            <BigOEEDisplay
              oee={oeeData.summary.oee}
              availability={oeeData.summary.availability}
              performance={oeeData.summary.performance}
              quality={oeeData.summary.quality}
              equipmentCount={oeeData.equipment_count}
              hoursInPeriod={oeeData.hours_in_period}
              totalLossHours={oeeData.losses.total_loss_hours}
            />

            {/* Row 2: Losses Pareto & Shift Comparison */}
            <Grid container spacing={3}>
              <Grid item xs={12} lg={7}>
                <LossesPareto losses={oeeData.losses} />
              </Grid>
              <Grid item xs={12} lg={5}>
                {shiftData && <ShiftChart shifts={shiftData.shifts} summary={shiftData.summary} />}
              </Grid>
            </Grid>

            {/* Row 3: Equipment Table */}
            {equipmentData && (
              <EquipmentPerformanceTable
                equipment={equipmentData.equipment}
                aggregated={equipmentData.aggregated}
                onEquipmentClick={handleEquipmentClick}
              />
            )}

            {/* Row 4: Insights */}
            <InsightsPanel insights={oeeData.insights} />

            {/* Row 5: ML Predictions - Sprint 3 */}
            <Divider sx={{ my: 1 }} />
            <OEEPredictions showSummary={true} />
          </Stack>
        )}
      </Box>

      {/* === SPRINT 2: Equipment Drill-Down Modal === */}
      <EquipmentDrillDownModal
        open={drillDownOpen}
        onClose={handleCloseDrillDown}
        equipment={selectedEquipment}
        timeRange={timeRange}
        onClassifyDowntime={handleClassifyDowntime}
      />

      {/* === SPRINT 2: Alerts Drawer === */}
      <AlertsDrawer
        open={alertsDrawerOpen}
        onClose={() => setAlertsDrawerOpen(false)}
        alerts={alerts}
        onAcknowledge={handleAcknowledgeAlert}
        onClearAll={handleClearAllAlerts}
        config={alertConfig}
        onConfigChange={setAlertConfig}
      />

      {/* === SPRINT 2: Snackbar Notification === */}
      <Snackbar
        open={!!snackbarAlert}
        autoHideDuration={6000}
        onClose={() => setSnackbarAlert(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        {snackbarAlert && (
          <Alert
            severity={snackbarAlert.severity === 'critical' ? 'error' : snackbarAlert.severity}
            variant="filled"
            onClose={() => setSnackbarAlert(null)}
            sx={{ width: '100%', minWidth: 300 }}
            action={
              <Button
                color="inherit"
                size="small"
                onClick={() => {
                  setAlertsDrawerOpen(true);
                  setSnackbarAlert(null);
                }}
              >
                Ver Todos
              </Button>
            }
          >
            <AlertTitle>{snackbarAlert.title}</AlertTitle>
            {snackbarAlert.message}
          </Alert>
        )}
      </Snackbar>

      {/* === SPRINT 2: Export Success Snackbar === */}
      <Snackbar
        open={!!exportSuccess}
        autoHideDuration={4000}
        onClose={() => setExportSuccess(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Alert
          severity="success"
          variant="filled"
          onClose={() => setExportSuccess(null)}
          sx={{ width: '100%' }}
        >
          Relatório {exportSuccess} exportado com sucesso!
        </Alert>
      </Snackbar>

      {/* CSS Animation for pulse */}
      <style>{`
        @keyframes pulse {
          0% { transform: scale(1); }
          50% { transform: scale(1.1); }
          100% { transform: scale(1); }
        }
        @media print {
          body * {
            visibility: hidden;
          }
          .MuiBox-root, .MuiBox-root * {
            visibility: visible;
          }
          .no-print {
            display: none !important;
          }
        }
      `}</style>
    </Box>
  );
};

export default OEEDashboard;
