/**
 * Tag Historical Trends - Industrial Process Variable Trending
 * Visualize historical tag data from InfluxDB with advanced charting
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Stack,
  Chip,
  Button,
  FormControl,
  Select,
  MenuItem,
  TextField,
  Autocomplete,
  ToggleButtonGroup,
  ToggleButton,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  alpha,
  useTheme,
  Tooltip as MuiTooltip
} from '@mui/material';
import { Grid } from '../components/GridWrapper';
import {
  Timeline,
  Refresh,
  Download,
  ShowChart,
  BarChart as BarChartIcon,
  StackedLineChart,
  AccessTime,
  CalendarMonth,
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Speed
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Brush,
  ComposedChart
} from 'recharts';
import apiClient from '../api/client';
import { gatewayEdgeApi } from '../api/gatewayEdge';

// Chart colors for multiple tags
const CHART_COLORS = [
  '#2196f3', '#4caf50', '#ff9800', '#e91e63',
  '#9c27b0', '#00bcd4', '#795548', '#607d8b'
];

// Time range presets
const TIME_RANGES = [
  { label: '15 min', value: 15, unit: 'minutes' },
  { label: '1 hora', value: 1, unit: 'hours' },
  { label: '4 horas', value: 4, unit: 'hours' },
  { label: '12 horas', value: 12, unit: 'hours' },
  { label: '24 horas', value: 24, unit: 'hours' },
  { label: '7 dias', value: 7, unit: 'days' },
  { label: '30 dias', value: 30, unit: 'days' },
];

// Aggregation options
const AGGREGATIONS = [
  { label: 'Nenhuma (Raw)', value: 'none' },
  { label: 'Média', value: 'mean' },
  { label: 'Mínimo', value: 'min' },
  { label: 'Máximo', value: 'max' },
  { label: 'Soma', value: 'sum' },
];

interface TagOption {
  id: string;
  name: string;
  unit?: string;
  deviceType?: string;
}

interface ChartDataPoint {
  timestamp: string;
  time: string;
  [key: string]: number | string;
}

interface TagStats {
  min: number;
  max: number;
  avg: number;
  current: number;
  trend: 'up' | 'down' | 'flat';
}

export const TagHistoricalTrends: React.FC = () => {
  const theme = useTheme();

  // State
  const [availableTags, setAvailableTags] = useState<TagOption[]>([]);
  const [selectedTags, setSelectedTags] = useState<TagOption[]>([]);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [tagStats, setTagStats] = useState<Record<string, TagStats>>({});
  const [loading, setLoading] = useState(false);
  const [loadingTags, setLoadingTags] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Time range
  const [timeRangePreset, setTimeRangePreset] = useState<number>(1);
  const [customStartTime, setCustomStartTime] = useState<Date | null>(null);
  const [customEndTime, setCustomEndTime] = useState<Date | null>(null);
  const [useCustomRange, setUseCustomRange] = useState(false);

  // Aggregation
  const [aggregation, setAggregation] = useState('none');
  const [interval, setInterval] = useState('1m');

  // Chart options
  const [chartType, setChartType] = useState<'line' | 'area' | 'step'>('line');
  const [showGrid, setShowGrid] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(false);

  // Load available tags on mount
  useEffect(() => {
    loadAvailableTags();
  }, []);

  const loadAvailableTags = async () => {
    try {
      setLoadingTags(true);
      let allTags: TagOption[] = [];

      // Try to get managed tags from Gateway Edge API
      try {
        const gatewayTags = await gatewayEdgeApi.listManagedTags();
        if (Array.isArray(gatewayTags) && gatewayTags.length > 0) {
          const tags = gatewayTags.map((t: any) => ({
            id: t.tag_id || t.id,
            name: t.tag_name || t.name,
            unit: t.metadata?.engineering_units || t.unit || '',
            deviceType: t.protocol_type || 'opcua'
          }));
          allTags = [...tags];
        }
      } catch {
        console.log('Gateway not available, trying active tags from InfluxDB...');
      }

      // Also get active tags from InfluxDB (includes auto-discovered tags)
      try {
        const response = await apiClient.get('/api/v1/timeseries/tags/active?lookback_hours=1');
        const activeTags = (response.data?.tags || []).map((t: any) => ({
          id: t.id,
          name: t.name,
          unit: t.unit || '',
          deviceType: t.source || 'influxdb'
        }));

        // Merge with existing tags, avoiding duplicates
        const existingIds = new Set(allTags.map(t => t.id));
        for (const tag of activeTags) {
          if (!existingIds.has(tag.id)) {
            allTags.push(tag);
            existingIds.add(tag.id);
          }
        }
      } catch (err) {
        console.log('Could not fetch active tags from InfluxDB:', err);
      }

      // Fallback to backend PostgreSQL API if still empty
      if (allTags.length === 0) {
        const response = await apiClient.getTags();
        const tags = (response as any[]).map((t: any) => ({
          id: t.id,
          name: t.name,
          unit: t.unit || '',
          deviceType: t.device_type || 'sensor'
        }));
        allTags = tags;
      }

      setAvailableTags(allTags);
    } catch (err: any) {
      console.error('Error loading tags:', err);
      setError('Erro ao carregar tags disponíveis');
    } finally {
      setLoadingTags(false);
    }
  };

  const loadHistoricalData = useCallback(async () => {
    if (selectedTags.length === 0) return;

    setLoading(true);
    setError(null);

    try {
      // Calculate time range
      let startTime: Date;
      let endTime: Date = new Date();

      if (useCustomRange && customStartTime && customEndTime) {
        startTime = customStartTime;
        endTime = customEndTime;
      } else {
        const preset = TIME_RANGES.find(r => r.value === timeRangePreset);
        if (preset) {
          const ms = preset.unit === 'minutes' ? preset.value * 60 * 1000 :
                     preset.unit === 'hours' ? preset.value * 60 * 60 * 1000 :
                     preset.value * 24 * 60 * 60 * 1000;
          startTime = new Date(endTime.getTime() - ms);
        } else {
          startTime = new Date(endTime.getTime() - 60 * 60 * 1000);
        }
      }

      // Query data for each selected tag
      const tagDataPromises = selectedTags.map(async (tag) => {
        try {
          const params: any = {
            start_time: startTime.toISOString(),
            end_time: endTime.toISOString()
          };

          if (aggregation !== 'none') {
            params.aggregation = aggregation;
            params.interval = interval;
          }

          const response = await apiClient.get(`/api/v1/timeseries/tags/${tag.id}`, { params });
          return { tag, data: response.data?.data || [] };
        } catch (e) {
          console.error(`Error fetching data for tag ${tag.name}:`, e);
          return { tag, data: [] };
        }
      });

      const results = await Promise.all(tagDataPromises);

      // Merge data into chart format
      const mergedData = mergeTagData(results);
      setChartData(mergedData);

      // Calculate statistics for each tag
      const stats: Record<string, TagStats> = {};
      results.forEach(({ tag, data }) => {
        if (data.length > 0) {
          const values = data.map((d: any) => d.value).filter((v: number) => v !== null);
          const min = Math.min(...values);
          const max = Math.max(...values);
          const avg = values.reduce((a: number, b: number) => a + b, 0) / values.length;
          const current = values[values.length - 1];
          const prev = values.length > 1 ? values[values.length - 2] : current;

          stats[tag.id] = {
            min,
            max,
            avg,
            current,
            trend: current > prev ? 'up' : current < prev ? 'down' : 'flat'
          };
        }
      });
      setTagStats(stats);

    } catch (err: any) {
      console.error('Error loading historical data:', err);
      setError('Erro ao carregar dados históricos');
    } finally {
      setLoading(false);
    }
  }, [selectedTags, timeRangePreset, customStartTime, customEndTime, useCustomRange, aggregation, interval]);

  // Auto-refresh effect
  useEffect(() => {
    let timerId: number | undefined;
    if (autoRefresh && selectedTags.length > 0) {
      timerId = window.setInterval(() => {
        loadHistoricalData();
      }, 10000);
    }
    return () => {
      if (timerId !== undefined) window.clearInterval(timerId);
    };
  }, [autoRefresh, selectedTags, loadHistoricalData]);

  // Merge data from multiple tags into single chart format
  const mergeTagData = (results: { tag: TagOption; data: any[] }[]): ChartDataPoint[] => {
    const timeMap = new Map<string, ChartDataPoint>();

    results.forEach(({ tag, data }) => {
      data.forEach((point: any) => {
        const timestamp = point.timestamp || point.time;
        if (!timestamp) return;

        const time = new Date(timestamp).toLocaleTimeString('pt-BR', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        });

        if (!timeMap.has(timestamp)) {
          timeMap.set(timestamp, { timestamp, time });
        }

        const existing = timeMap.get(timestamp)!;
        existing[tag.id] = point.value;
      });
    });

    return Array.from(timeMap.values()).sort((a, b) =>
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  };

  const handleTagSelect = (event: any, newValue: TagOption[]) => {
    setSelectedTags(newValue.slice(0, 8)); // Max 8 tags
  };

  const handleExportCSV = () => {
    if (chartData.length === 0) return;

    const headers = ['Timestamp', ...selectedTags.map(t => t.name)];
    const rows = chartData.map(point => [
      point.timestamp,
      ...selectedTags.map(t => point[t.id] || '')
    ]);

    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trends_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'flat') => {
    switch (trend) {
      case 'up': return <TrendingUp sx={{ color: 'success.main' }} />;
      case 'down': return <TrendingDown sx={{ color: 'error.main' }} />;
      default: return <TrendingFlat sx={{ color: 'text.secondary' }} />;
    }
  };

  return (
      <Container maxWidth="xl" sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 3 }}>
          <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 1 }}>
            <Timeline sx={{ fontSize: 32, color: 'primary.main' }} />
            <Typography variant="h4" fontWeight="bold">
              Tendências Históricas
            </Typography>
            <Chip
              label="InfluxDB"
              size="small"
              color="info"
              icon={<Speed sx={{ fontSize: 16 }} />}
            />
          </Stack>
          <Typography variant="body2" color="text.secondary">
            Visualize e analise dados históricos de tags industriais com gráficos interativos
          </Typography>
        </Box>

        {/* Tag Selection */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
            Selecionar Tags
          </Typography>

          <Autocomplete
            multiple
            options={availableTags}
            getOptionLabel={(option) => `${option.name}${option.unit ? ` (${option.unit})` : ''}`}
            value={selectedTags}
            onChange={handleTagSelect}
            loading={loadingTags}
            renderInput={(params) => (
              <TextField
                {...params}
                placeholder="Buscar e selecionar tags..."
                variant="outlined"
                size="small"
              />
            )}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => (
                <Chip
                  {...getTagProps({ index })}
                  key={option.id}
                  label={option.name}
                  size="small"
                  sx={{
                    bgcolor: alpha(CHART_COLORS[index % CHART_COLORS.length], 0.2),
                    borderLeft: `3px solid ${CHART_COLORS[index % CHART_COLORS.length]}`
                  }}
                />
              ))
            }
          />

          {selectedTags.length >= 8 && (
            <Alert severity="info" sx={{ mt: 1 }}>
              Máximo de 8 tags atingido
            </Alert>
          )}
        </Paper>

        {/* Time Range & Options */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            {/* Time Range Presets */}
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                <AccessTime sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                Período
              </Typography>
              <ToggleButtonGroup
                value={timeRangePreset}
                exclusive
                onChange={(e, v) => { if (v) { setTimeRangePreset(v); setUseCustomRange(false); } }}
                size="small"
                sx={{ flexWrap: 'wrap' }}
              >
                {TIME_RANGES.map((range) => (
                  <ToggleButton key={range.value} value={range.value}>
                    {range.label}
                  </ToggleButton>
                ))}
              </ToggleButtonGroup>
            </Grid>

            {/* Custom Range */}
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                <CalendarMonth sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                Período Customizado
              </Typography>
              <Stack direction="row" spacing={1}>
                <TextField
                  type="datetime-local"
                  label="Início"
                  size="small"
                  sx={{ width: 180 }}
                  InputLabelProps={{ shrink: true }}
                  value={customStartTime ? customStartTime.toISOString().slice(0, 16) : ''}
                  onChange={(e) => {
                    const date = e.target.value ? new Date(e.target.value) : null;
                    setCustomStartTime(date);
                    setUseCustomRange(true);
                  }}
                />
                <TextField
                  type="datetime-local"
                  label="Fim"
                  size="small"
                  sx={{ width: 180 }}
                  InputLabelProps={{ shrink: true }}
                  value={customEndTime ? customEndTime.toISOString().slice(0, 16) : ''}
                  onChange={(e) => {
                    const date = e.target.value ? new Date(e.target.value) : null;
                    setCustomEndTime(date);
                    setUseCustomRange(true);
                  }}
                />
              </Stack>
            </Grid>

            {/* Aggregation */}
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                Agregação
              </Typography>
              <Stack direction="row" spacing={1}>
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <Select
                    value={aggregation}
                    onChange={(e) => setAggregation(e.target.value)}
                  >
                    {AGGREGATIONS.map((agg) => (
                      <MenuItem key={agg.value} value={agg.value}>{agg.label}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControl size="small" sx={{ minWidth: 80 }}>
                  <Select
                    value={interval}
                    onChange={(e) => setInterval(e.target.value)}
                    disabled={aggregation === 'none'}
                  >
                    <MenuItem value="10s">10s</MenuItem>
                    <MenuItem value="30s">30s</MenuItem>
                    <MenuItem value="1m">1m</MenuItem>
                    <MenuItem value="5m">5m</MenuItem>
                    <MenuItem value="15m">15m</MenuItem>
                    <MenuItem value="1h">1h</MenuItem>
                  </Select>
                </FormControl>
              </Stack>
            </Grid>
          </Grid>

          {/* Action Buttons */}
          <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
            <Button
              variant="contained"
              startIcon={loading ? <CircularProgress size={16} /> : <Refresh />}
              onClick={loadHistoricalData}
              disabled={selectedTags.length === 0 || loading}
            >
              {loading ? 'Carregando...' : 'Carregar Dados'}
            </Button>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleExportCSV}
              disabled={chartData.length === 0}
            >
              Exportar CSV
            </Button>
            <ToggleButtonGroup
              value={chartType}
              exclusive
              onChange={(e, v) => v && setChartType(v)}
              size="small"
            >
              <ToggleButton value="line">
                <MuiTooltip title="Linha"><ShowChart /></MuiTooltip>
              </ToggleButton>
              <ToggleButton value="area">
                <MuiTooltip title="Área"><StackedLineChart /></MuiTooltip>
              </ToggleButton>
              <ToggleButton value="step">
                <MuiTooltip title="Degrau"><BarChartIcon /></MuiTooltip>
              </ToggleButton>
            </ToggleButtonGroup>
          </Stack>
        </Paper>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Statistics Cards */}
        {selectedTags.length > 0 && Object.keys(tagStats).length > 0 && (
          <Grid container spacing={2} sx={{ mb: 3 }}>
            {selectedTags.map((tag, index) => {
              const stats = tagStats[tag.id];
              if (!stats) return null;

              return (
                <Grid item xs={6} sm={4} md={3} lg={2} key={tag.id}>
                  <Card sx={{
                    borderTop: `3px solid ${CHART_COLORS[index % CHART_COLORS.length]}`,
                    height: '100%'
                  }}>
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Typography variant="caption" color="text.secondary" noWrap>
                          {tag.name}
                        </Typography>
                        {getTrendIcon(stats.trend)}
                      </Stack>
                      <Typography variant="h5" fontWeight="bold" sx={{ my: 0.5 }}>
                        {stats.current.toFixed(2)}
                        {tag.unit && <Typography component="span" variant="caption" sx={{ ml: 0.5 }}>{tag.unit}</Typography>}
                      </Typography>
                      <Stack direction="row" spacing={1}>
                        <Typography variant="caption" color="text.secondary">
                          Min: {stats.min.toFixed(1)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Max: {stats.max.toFixed(1)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Avg: {stats.avg.toFixed(1)}
                        </Typography>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        )}

        {/* Chart */}
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            Gráfico de Tendências
          </Typography>

          {selectedTags.length === 0 ? (
            <Box sx={{
              height: 400,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'text.secondary'
            }}>
              <Stack alignItems="center" spacing={1}>
                <Timeline sx={{ fontSize: 64, opacity: 0.3 }} />
                <Typography>Selecione tags para visualizar tendências</Typography>
              </Stack>
            </Box>
          ) : chartData.length === 0 && !loading ? (
            <Box sx={{
              height: 400,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'text.secondary'
            }}>
              <Stack alignItems="center" spacing={1}>
                <ShowChart sx={{ fontSize: 64, opacity: 0.3 }} />
                <Typography>Clique em "Carregar Dados" para visualizar o histórico</Typography>
              </Stack>
            </Box>
          ) : (
            <ResponsiveContainer width="100%" height={450}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={alpha(theme.palette.divider, 0.5)} />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 11 }}
                  interval="preserveStartEnd"
                />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: theme.palette.background.paper,
                    borderRadius: 8,
                    boxShadow: theme.shadows[3]
                  }}
                />
                <Legend />
                <Brush dataKey="time" height={30} stroke={theme.palette.primary.main} />

                {selectedTags.map((tag, index) => {
                  const color = CHART_COLORS[index % CHART_COLORS.length];

                  if (chartType === 'area') {
                    return (
                      <Area
                        key={tag.id}
                        type="monotone"
                        dataKey={tag.id}
                        name={tag.name}
                        stroke={color}
                        fill={alpha(color, 0.3)}
                        strokeWidth={2}
                        dot={false}
                      />
                    );
                  } else {
                    return (
                      <Line
                        key={tag.id}
                        type={chartType === 'step' ? 'stepAfter' : 'monotone'}
                        dataKey={tag.id}
                        name={tag.name}
                        stroke={color}
                        strokeWidth={2}
                        dot={false}
                        activeDot={{ r: 4 }}
                      />
                    );
                  }
                })}
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </Paper>
      </Container>
  );
};

export default TagHistoricalTrends;
