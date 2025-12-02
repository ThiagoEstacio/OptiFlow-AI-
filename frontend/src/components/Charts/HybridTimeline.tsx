/**
 * 🔮 HybridTimeline - Historical + ML Prediction Visualization
 * =============================================================
 *
 * Combina dados históricos com previsões de Machine Learning em uma
 * única visualização temporal.
 *
 * Features:
 * - Dados históricos à esquerda do "NOW"
 * - Previsões ML à direita com cone de incerteza
 * - Marcadores de eventos (alarmes, anomalias)
 * - Zoom e pan interativos
 * - Indicador de confiança da previsão
 */

import React, { useMemo, useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Stack,
  Chip,
  IconButton,
  Tooltip,
  ToggleButton,
  ToggleButtonGroup,
  Slider,
  alpha,
  useTheme,
  Divider,
} from '@mui/material';
import {
  Timeline as TimelineIcon,
  TrendingUp,
  Warning,
  Refresh,
  ZoomIn,
  ZoomOut,
  FitScreen,
  Download,
  Info,
  Psychology,
  History,
  Update,
} from '@mui/icons-material';
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
  Legend,
  Brush,
  Scatter,
} from 'recharts';

// ========================================
// Types
// ========================================

export interface TimelineDataPoint {
  timestamp: Date | string;
  value: number;
  type: 'historical' | 'prediction';
  confidence?: number; // 0-1 for predictions
  upperBound?: number;
  lowerBound?: number;
}

export interface TimelineEvent {
  timestamp: Date | string;
  type: 'alarm' | 'anomaly' | 'maintenance' | 'change';
  severity?: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description?: string;
}

export interface HybridTimelineProps {
  title?: string;
  historicalData: TimelineDataPoint[];
  predictionData: TimelineDataPoint[];
  events?: TimelineEvent[];
  unit?: string;
  confidenceLevel?: number; // Default 0.95 (95%)
  showConfidenceBand?: boolean;
  showEvents?: boolean;
  showLegend?: boolean;
  showBrush?: boolean;
  height?: number;
  historicalColor?: string;
  predictionColor?: string;
  onPointClick?: (point: TimelineDataPoint) => void;
  onEventClick?: (event: TimelineEvent) => void;
}

// ========================================
// Constants
// ========================================

const EVENT_COLORS = {
  alarm: '#f44336',
  anomaly: '#ff9800',
  maintenance: '#2196f3',
  change: '#9c27b0',
};

const SEVERITY_OPACITY = {
  low: 0.4,
  medium: 0.6,
  high: 0.8,
  critical: 1,
};

// ========================================
// Helper Components
// ========================================

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
  unit?: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label, unit }) => {
  const theme = useTheme();

  if (!active || !payload || !payload.length) return null;

  const data = payload[0]?.payload;
  const isPrediction = data?.type === 'prediction';

  return (
    <Paper
      elevation={3}
      sx={{
        p: 1.5,
        bgcolor: alpha(theme.palette.background.paper, 0.95),
        border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
        maxWidth: 250,
      }}
    >
      <Typography variant="caption" color="text.secondary" display="block">
        {label}
      </Typography>

      <Stack direction="row" alignItems="center" spacing={1} mt={0.5}>
        {isPrediction ? (
          <Psychology fontSize="small" color="secondary" />
        ) : (
          <History fontSize="small" color="primary" />
        )}
        <Typography variant="body2" fontWeight={600}>
          {data?.value?.toFixed(2)} {unit}
        </Typography>
        <Chip
          size="small"
          label={isPrediction ? 'Previsão' : 'Histórico'}
          color={isPrediction ? 'secondary' : 'primary'}
          sx={{ height: 20, fontSize: '0.7rem' }}
        />
      </Stack>

      {isPrediction && data?.confidence && (
        <Typography variant="caption" color="text.secondary" display="block" mt={0.5}>
          Confiança: {(data.confidence * 100).toFixed(0)}%
        </Typography>
      )}

      {isPrediction && data?.upperBound && data?.lowerBound && (
        <Typography variant="caption" color="text.secondary" display="block">
          Intervalo: [{data.lowerBound.toFixed(2)} - {data.upperBound.toFixed(2)}]
        </Typography>
      )}
    </Paper>
  );
};

// Event marker component
const EventMarker: React.FC<{
  event: TimelineEvent;
  onClick?: () => void;
}> = ({ event, onClick }) => {
  const theme = useTheme();
  const color = EVENT_COLORS[event.type];
  const opacity = SEVERITY_OPACITY[event.severity || 'medium'];

  return (
    <Tooltip
      title={
        <Stack spacing={0.5}>
          <Typography variant="subtitle2">{event.title}</Typography>
          {event.description && (
            <Typography variant="caption">{event.description}</Typography>
          )}
          <Typography variant="caption" color="text.secondary">
            {new Date(event.timestamp).toLocaleString('pt-BR')}
          </Typography>
        </Stack>
      }
      arrow
    >
      <Box
        onClick={onClick}
        sx={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          bgcolor: color,
          opacity,
          cursor: 'pointer',
          '&:hover': {
            transform: 'scale(1.5)',
            boxShadow: `0 0 8px ${color}`,
          },
          transition: 'all 0.2s ease',
        }}
      />
    </Tooltip>
  );
};

// ========================================
// Main Component
// ========================================

export const HybridTimeline: React.FC<HybridTimelineProps> = ({
  title = 'Timeline Híbrida',
  historicalData,
  predictionData,
  events = [],
  unit = '',
  confidenceLevel = 0.95,
  showConfidenceBand = true,
  showEvents = true,
  showLegend = true,
  showBrush = true,
  height = 400,
  historicalColor = '#2196f3',
  predictionColor = '#9c27b0',
  onPointClick,
  onEventClick,
}) => {
  const theme = useTheme();
  const [zoomDomain, setZoomDomain] = useState<[number, number] | null>(null);
  const [showPrediction, setShowPrediction] = useState(true);
  const [showHistorical, setShowHistorical] = useState(true);

  // Combine and format data
  const chartData = useMemo(() => {
    const historical = historicalData.map((point) => ({
      timestamp: new Date(point.timestamp).getTime(),
      formattedTime: new Date(point.timestamp).toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }),
      historical: point.value,
      type: 'historical' as const,
    }));

    const predictions = predictionData.map((point) => ({
      timestamp: new Date(point.timestamp).getTime(),
      formattedTime: new Date(point.timestamp).toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }),
      prediction: point.value,
      upperBound: point.upperBound,
      lowerBound: point.lowerBound,
      confidence: point.confidence,
      type: 'prediction' as const,
    }));

    // Combine and sort by timestamp
    return [...historical, ...predictions].sort((a, b) => a.timestamp - b.timestamp);
  }, [historicalData, predictionData]);

  // Find the "NOW" point (last historical data point)
  const nowTimestamp = useMemo(() => {
    if (historicalData.length === 0) return Date.now();
    const lastHistorical = historicalData[historicalData.length - 1];
    return new Date(lastHistorical.timestamp).getTime();
  }, [historicalData]);

  // Calculate statistics
  const stats = useMemo(() => {
    const historicalValues = historicalData.map((d) => d.value);
    const predictionValues = predictionData.map((d) => d.value);

    return {
      historicalMin: Math.min(...historicalValues),
      historicalMax: Math.max(...historicalValues),
      historicalAvg: historicalValues.reduce((a, b) => a + b, 0) / historicalValues.length,
      predictionMin: Math.min(...predictionValues),
      predictionMax: Math.max(...predictionValues),
      predictionAvg: predictionValues.reduce((a, b) => a + b, 0) / predictionValues.length,
      avgConfidence: predictionData.reduce((a, d) => a + (d.confidence || 0), 0) / predictionData.length,
    };
  }, [historicalData, predictionData]);

  // Handlers
  const handleZoomIn = useCallback(() => {
    if (!zoomDomain) {
      const range = chartData[chartData.length - 1].timestamp - chartData[0].timestamp;
      const center = nowTimestamp;
      setZoomDomain([center - range / 4, center + range / 4]);
    } else {
      const range = zoomDomain[1] - zoomDomain[0];
      const center = (zoomDomain[0] + zoomDomain[1]) / 2;
      setZoomDomain([center - range / 4, center + range / 4]);
    }
  }, [zoomDomain, chartData, nowTimestamp]);

  const handleZoomOut = useCallback(() => {
    if (zoomDomain) {
      const range = zoomDomain[1] - zoomDomain[0];
      const center = (zoomDomain[0] + zoomDomain[1]) / 2;
      const newRange = range * 2;
      const minTs = chartData[0].timestamp;
      const maxTs = chartData[chartData.length - 1].timestamp;
      setZoomDomain([
        Math.max(minTs, center - newRange / 2),
        Math.min(maxTs, center + newRange / 2),
      ]);
    }
  }, [zoomDomain, chartData]);

  const handleResetZoom = useCallback(() => {
    setZoomDomain(null);
  }, []);

  return (
    <Paper
      elevation={2}
      sx={{
        p: 2,
        bgcolor: theme.palette.background.paper,
      }}
    >
      {/* Header */}
      <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <TimelineIcon color="primary" />
          <Typography variant="h6">{title}</Typography>
          <Chip
            size="small"
            icon={<Psychology />}
            label={`Confiança: ${(stats.avgConfidence * 100).toFixed(0)}%`}
            color="secondary"
            variant="outlined"
          />
        </Stack>

        <Stack direction="row" alignItems="center" spacing={1}>
          {/* Toggle buttons */}
          <ToggleButtonGroup size="small" value={[showHistorical && 'historical', showPrediction && 'prediction'].filter(Boolean)}>
            <ToggleButton
              value="historical"
              onClick={() => setShowHistorical(!showHistorical)}
            >
              <History fontSize="small" />
            </ToggleButton>
            <ToggleButton
              value="prediction"
              onClick={() => setShowPrediction(!showPrediction)}
            >
              <TrendingUp fontSize="small" />
            </ToggleButton>
          </ToggleButtonGroup>

          {/* Zoom controls */}
          <Divider orientation="vertical" flexItem />
          <Tooltip title="Zoom In">
            <IconButton size="small" onClick={handleZoomIn}>
              <ZoomIn />
            </IconButton>
          </Tooltip>
          <Tooltip title="Zoom Out">
            <IconButton size="small" onClick={handleZoomOut}>
              <ZoomOut />
            </IconButton>
          </Tooltip>
          <Tooltip title="Reset Zoom">
            <IconButton size="small" onClick={handleResetZoom}>
              <FitScreen />
            </IconButton>
          </Tooltip>
        </Stack>
      </Stack>

      {/* Stats summary */}
      <Stack direction="row" spacing={3} mb={2}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <Box sx={{ width: 12, height: 12, bgcolor: historicalColor, borderRadius: 0.5 }} />
          <Typography variant="caption" color="text.secondary">
            Histórico: Média {stats.historicalAvg.toFixed(2)} {unit}
          </Typography>
        </Stack>
        <Stack direction="row" alignItems="center" spacing={1}>
          <Box sx={{ width: 12, height: 12, bgcolor: predictionColor, borderRadius: 0.5 }} />
          <Typography variant="caption" color="text.secondary">
            Previsão: Média {stats.predictionAvg.toFixed(2)} {unit}
          </Typography>
        </Stack>
      </Stack>

      {/* Chart */}
      <Box sx={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={chartData}
            margin={{ top: 10, right: 30, left: 10, bottom: showBrush ? 40 : 10 }}
          >
            <defs>
              {/* Gradient for confidence band */}
              <linearGradient id="confidenceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={predictionColor} stopOpacity={0.3} />
                <stop offset="100%" stopColor={predictionColor} stopOpacity={0.05} />
              </linearGradient>
              {/* Pattern for prediction area */}
              <pattern id="predictionPattern" patternUnits="userSpaceOnUse" width="4" height="4">
                <path
                  d="M-1,1 l2,-2 M0,4 l4,-4 M3,5 l2,-2"
                  style={{ stroke: predictionColor, strokeWidth: 1, opacity: 0.3 }}
                />
              </pattern>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke={alpha(theme.palette.divider, 0.3)} />

            <XAxis
              dataKey="formattedTime"
              tick={{ fontSize: 11 }}
              stroke={theme.palette.text.secondary}
            />

            <YAxis
              tick={{ fontSize: 11 }}
              stroke={theme.palette.text.secondary}
              tickFormatter={(value) => `${value}${unit ? ` ${unit}` : ''}`}
            />

            <RechartsTooltip
              content={<CustomTooltip unit={unit} />}
              cursor={{ strokeDasharray: '3 3' }}
            />

            {/* NOW reference line */}
            <ReferenceLine
              x={new Date(nowTimestamp).toLocaleString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
              })}
              stroke={theme.palette.warning.main}
              strokeWidth={2}
              strokeDasharray="5 5"
              label={{
                value: 'AGORA',
                fill: theme.palette.warning.main,
                fontSize: 12,
                fontWeight: 'bold',
              }}
            />

            {/* Confidence band for predictions */}
            {showConfidenceBand && showPrediction && (
              <Area
                dataKey="upperBound"
                stroke="none"
                fill="url(#confidenceGradient)"
                fillOpacity={1}
                name="Intervalo Superior"
              />
            )}

            {/* Historical line */}
            {showHistorical && (
              <Line
                type="monotone"
                dataKey="historical"
                stroke={historicalColor}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6, fill: historicalColor }}
                name="Histórico"
              />
            )}

            {/* Prediction line */}
            {showPrediction && (
              <Line
                type="monotone"
                dataKey="prediction"
                stroke={predictionColor}
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                activeDot={{ r: 6, fill: predictionColor }}
                name="Previsão"
              />
            )}

            {/* Lower bound for confidence */}
            {showConfidenceBand && showPrediction && (
              <Line
                type="monotone"
                dataKey="lowerBound"
                stroke={predictionColor}
                strokeWidth={1}
                strokeDasharray="2 2"
                strokeOpacity={0.5}
                dot={false}
                name="Limite Inferior"
              />
            )}

            {showLegend && <Legend />}

            {showBrush && (
              <Brush
                dataKey="formattedTime"
                height={30}
                stroke={theme.palette.primary.main}
                fill={alpha(theme.palette.primary.main, 0.1)}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </Box>

      {/* Events timeline */}
      {showEvents && events.length > 0 && (
        <Box mt={2}>
          <Typography variant="subtitle2" color="text.secondary" mb={1}>
            Eventos ({events.length})
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {events.map((event, index) => (
              <Chip
                key={index}
                size="small"
                icon={<Warning />}
                label={event.title}
                onClick={() => onEventClick?.(event)}
                sx={{
                  bgcolor: alpha(EVENT_COLORS[event.type], 0.1),
                  color: EVENT_COLORS[event.type],
                  borderColor: EVENT_COLORS[event.type],
                }}
                variant="outlined"
              />
            ))}
          </Stack>
        </Box>
      )}

      {/* Info footer */}
      <Stack direction="row" alignItems="center" spacing={1} mt={2}>
        <Info fontSize="small" color="disabled" />
        <Typography variant="caption" color="text.secondary">
          Previsões baseadas em modelo ML com {(confidenceLevel * 100).toFixed(0)}% de intervalo de confiança.
          A área sombreada indica a incerteza da previsão.
        </Typography>
      </Stack>
    </Paper>
  );
};

export default HybridTimeline;
