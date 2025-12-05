/**
 * Professional Real-time Overview - Executive Dashboard
 *
 * Overview page showing system health, adapter status, and key metrics.
 * For detailed tag list, use /realtime/tags
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Stack,
  Chip,
  Avatar,
  IconButton,
  Button,
  LinearProgress,
  useTheme
} from '@mui/material';
import { Grid } from '../components/GridWrapper';
import {
  Refresh,
  Circle,
  SignalCellularAlt,
  Memory,
  Hub,
  CheckCircle,
  Warning,
  ArrowForward,
  Speed,
  Thermostat,
  Water,
  ElectricBolt
} from '@mui/icons-material';
import { GaugeWidget } from '../components/professional/GaugeWidget';
import { ChartWidget } from '../components/professional/ChartWidget';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

// Gateway Edge API URL
const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8080';

interface ChartDataPoint {
  time: string;
  value: number;
}

interface RealtimeTagValue {
  value: number;
  quality: string;
  timestamp: string;
  address: string;
  adapter_id: string;
  protocol: string;
}

interface GatewayRealtimeAllResponse {
  count: number;
  adapters: number;
  tags: Record<string, RealtimeTagValue>;
  latency_ms?: number;
}

interface AdapterInfo {
  adapter_id: string;
  adapter_name: string;
  protocol_type: string;
  enabled: boolean;
  connected: boolean;
  running: boolean;
  tags_count: number;
  host: string;
  port: number;
}

interface SystemStats {
  totalTags: number;
  connectedAdapters: number;
  totalAdapters: number;
  goodQualityTags: number;
  latencyMs: number;
}

export const ProfessionalRealtime: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [adapters, setAdapters] = useState<AdapterInfo[]>([]);
  const [stats, setStats] = useState<SystemStats>({
    totalTags: 0,
    connectedAdapters: 0,
    totalAdapters: 0,
    goodQualityTags: 0,
    latencyMs: 0
  });
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Key metrics from real-time data
  const [metrics, setMetrics] = useState({
    flow: 0,
    temperature: 0,
    tankLevel: 0,
    power: 0
  });

  // Previous values for trend calculation
  const [prevValues, setPrevValues] = useState({
    flow: 0,
    temperature: 0,
    tankLevel: 0,
    power: 0
  });

  // Fetch all data from Gateway Edge
  const fetchData = useCallback(async () => {
    try {
      const [realtimeResponse, adaptersResponse] = await Promise.all([
        axios.get<GatewayRealtimeAllResponse>(`${GATEWAY_URL}/api/tags/realtime/all`),
        axios.get<AdapterInfo[]>(`${GATEWAY_URL}/api/adapters/`)
      ]);

      if (realtimeResponse.data?.tags) {
        setIsConnected(true);
        setLastUpdate(new Date());

        const realtimeTags = realtimeResponse.data.tags;
        const tagEntries = Object.entries(realtimeTags);

        // Calculate stats
        const goodQuality = tagEntries.filter(([_, t]) => t.quality === 'Good').length;

        setStats({
          totalTags: realtimeResponse.data.count,
          connectedAdapters: adaptersResponse.data.filter(a => a.connected).length,
          totalAdapters: adaptersResponse.data.length,
          goodQualityTags: goodQuality,
          latencyMs: realtimeResponse.data.latency_ms || 0
        });

        setAdapters(adaptersResponse.data);

        // Find key metrics by tag name (supports partial matching and virtual: prefix)
        const getTagValue = (name: string): number => {
          // Direct match first
          if (realtimeTags[name]) return Number(realtimeTags[name].value) || 0;

          // Try with virtual prefix patterns
          const virtualPatterns = [
            `virtual:OPC-UA:${name}`,
            `virtual:MODBUS:${name}`,
            `virtual:PROFINET:${name}`,
            `virtual:ETHERNET-IP:${name}`
          ];
          for (const pattern of virtualPatterns) {
            if (realtimeTags[pattern]) return Number(realtimeTags[pattern].value) || 0;
          }

          // Search by partial match (contains)
          const matchingKey = Object.keys(realtimeTags).find(key =>
            key.includes(name) || key.endsWith(name)
          );
          if (matchingKey) return Number(realtimeTags[matchingKey].value) || 0;

          return 0;
        };

        // Use real tags from Node-RED Grain Terminal Simulator
        // Flow from conveyors (CORR01, CORR02, CORR03)
        const conveyorFlow = getTagValue('CORR01_FLOW_TPH_PV') +
                            getTagValue('CORR02_FLOW_TPH_PV') +
                            getTagValue('CORR03_FLOW_TPH_PV');
        // Temperature from conveyor motors
        const avgTemp = (getTagValue('CORR01_MOTOR_TEMP_C_PV') +
                        getTagValue('CORR02_MOTOR_TEMP_C_PV') +
                        getTagValue('CORR03_MOTOR_TEMP_C_PV')) / 3;
        // Elevator flow as tank level proxy
        const elevatorFlow = getTagValue('ELV01_FLOW_TPH_PV');
        // Total power from all equipment
        const totalPower = getTagValue('CORR01_POWER_KW_PV') +
                          getTagValue('CORR02_POWER_KW_PV') +
                          getTagValue('CORR03_POWER_KW_PV') +
                          getTagValue('ELV01_POWER_KW_PV') +
                          getTagValue('SLD01_POWER_KW_PV');

        // Store previous values for trend
        setPrevValues({
          flow: metrics.flow,
          temperature: metrics.temperature,
          tankLevel: metrics.tankLevel,
          power: metrics.power
        });

        // Update metrics with real values from Grain Terminal Simulator
        setMetrics({
          flow: conveyorFlow,        // Total conveyor flow (ton/h)
          temperature: avgTemp,       // Average motor temperature (°C)
          tankLevel: elevatorFlow,    // Elevator throughput (ton/h)
          power: totalPower           // Total power consumption (kW)
        });

        // Update chart with total conveyor flow data
        const timestamp = new Date();
        setChartData(prev => {
          const newPoint = {
            time: timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
            value: conveyorFlow
          };
          const updated = [...prev, newPoint];
          return updated.slice(-20);
        });
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setIsConnected(false);
    }
  }, [metrics]);

  // Initial load and polling
  useEffect(() => {
    fetchData();
    intervalRef.current = setInterval(fetchData, 2000);
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const qualityPercentage = stats.totalTags > 0
    ? Math.round((stats.goodQualityTags / stats.totalTags) * 100)
    : 0;

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', pb: 4 }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
          color: 'white',
          borderRadius: 0,
          mb: 3
        }}
      >
        <Container maxWidth="xl">
          <Box sx={{ py: 4 }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Box>
                <Typography variant="h4" fontWeight={700} gutterBottom>
                  Real-time Overview
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.9 }}>
                  System health and key performance indicators
                </Typography>
              </Box>

              <Stack direction="row" spacing={2} alignItems="center">
                <Chip
                  icon={
                    <Circle
                      sx={{
                        animation: isConnected ? 'pulse 2s ease-in-out infinite' : 'none',
                        '@keyframes pulse': {
                          '0%, 100%': { opacity: 1 },
                          '50%': { opacity: 0.5 }
                        }
                      }}
                    />
                  }
                  label={isConnected ? 'Gateway Connected' : 'Disconnected'}
                  sx={{
                    bgcolor: isConnected ? 'rgba(76, 175, 80, 0.3)' : 'rgba(255, 87, 34, 0.3)',
                    color: 'white',
                    fontWeight: 600
                  }}
                />
                <IconButton onClick={fetchData} sx={{ color: 'white' }}>
                  <Refresh />
                </IconButton>
              </Stack>
            </Stack>
          </Box>
        </Container>
      </Paper>

      <Container maxWidth="xl">
        {/* System KPIs */}
        <Grid container spacing={3} mb={3}>
          <Grid xs={12} sm={6} md={3}>
            <Paper sx={{ p: 3, borderRadius: 2, height: '100%' }}>
              <Stack direction="row" alignItems="center" spacing={2} mb={2}>
                <Avatar sx={{ bgcolor: theme.palette.primary.light }}>
                  <Memory />
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight={700}>{stats.totalTags}</Typography>
                  <Typography variant="body2" color="text.secondary">Managed Tags</Typography>
                </Box>
              </Stack>
              <Button
                size="small"
                endIcon={<ArrowForward />}
                onClick={() => navigate('/realtime/tags')}
              >
                View All Tags
              </Button>
            </Paper>
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <Paper sx={{ p: 3, borderRadius: 2, height: '100%' }}>
              <Stack direction="row" alignItems="center" spacing={2} mb={2}>
                <Avatar sx={{ bgcolor: theme.palette.success.light }}>
                  <Hub />
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight={700}>
                    {stats.connectedAdapters}/{stats.totalAdapters}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">Adapters Online</Typography>
                </Box>
              </Stack>
              <LinearProgress
                variant="determinate"
                value={(stats.connectedAdapters / Math.max(stats.totalAdapters, 1)) * 100}
                color="success"
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Paper>
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <Paper sx={{ p: 3, borderRadius: 2, height: '100%' }}>
              <Stack direction="row" alignItems="center" spacing={2} mb={2}>
                <Avatar sx={{ bgcolor: qualityPercentage > 90 ? theme.palette.success.light : theme.palette.warning.light }}>
                  <CheckCircle />
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight={700}>{qualityPercentage}%</Typography>
                  <Typography variant="body2" color="text.secondary">Signal Quality</Typography>
                </Box>
              </Stack>
              <LinearProgress
                variant="determinate"
                value={qualityPercentage}
                color={qualityPercentage > 90 ? 'success' : 'warning'}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Paper>
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <Paper sx={{ p: 3, borderRadius: 2, height: '100%' }}>
              <Stack direction="row" alignItems="center" spacing={2} mb={2}>
                <Avatar sx={{ bgcolor: theme.palette.info.light }}>
                  <SignalCellularAlt />
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight={700}>
                    {stats.latencyMs.toFixed(1)}ms
                  </Typography>
                  <Typography variant="body2" color="text.secondary">Response Time</Typography>
                </Box>
              </Stack>
              <Typography variant="caption" color="text.secondary">
                Last update: {lastUpdate?.toLocaleTimeString() || 'N/A'}
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Adapters Status */}
        <Paper sx={{ p: 3, borderRadius: 2, mb: 3 }}>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Adapter Status
          </Typography>
          <Grid container spacing={2}>
            {adapters.map((adapter) => (
              <Grid key={adapter.adapter_id} xs={12} sm={6} md={4}>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 2,
                    borderColor: adapter.connected ? 'success.main' : 'error.main',
                    borderWidth: 2
                  }}
                >
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <Chip
                          size="small"
                          label={adapter.protocol_type.toUpperCase()}
                          color={adapter.protocol_type === 'modbus' ? 'primary' : 'secondary'}
                        />
                        {adapter.connected ? (
                          <CheckCircle fontSize="small" color="success" />
                        ) : (
                          <Warning fontSize="small" color="error" />
                        )}
                      </Stack>
                      <Typography variant="subtitle1" fontWeight={600} mt={1}>
                        {adapter.adapter_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {adapter.host}:{adapter.port}
                      </Typography>
                    </Box>
                    <Box textAlign="right">
                      <Typography variant="h5" fontWeight={700} color="primary">
                        {adapter.tags_count}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">tags</Typography>
                    </Box>
                  </Stack>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Paper>

        {/* Key Metrics - Gauges - Grain Terminal */}
        <Typography variant="h6" fontWeight={600} mb={2}>
          Grain Terminal - Process Metrics
        </Typography>
        <Grid container spacing={3} mb={3}>
          <Grid xs={12} sm={6} md={3}>
            <GaugeWidget
              title="Conveyor Flow"
              value={metrics.flow}
              min={0}
              max={1500}
              unit="ton/h"
              thresholds={{ low: 500, medium: 900, high: 1200 }}
              trend={metrics.flow > prevValues.flow ? 'up' : metrics.flow < prevValues.flow ? 'down' : 'neutral'}
              trendValue="CORR01+CORR02+CORR03"
              subtitle="Total belt throughput"
              size="medium"
            />
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <GaugeWidget
              title="Motor Temperature"
              value={metrics.temperature}
              min={0}
              max={100}
              unit="°C"
              thresholds={{ low: 40, medium: 60, high: 80 }}
              trend={metrics.temperature > prevValues.temperature ? 'up' : metrics.temperature < prevValues.temperature ? 'down' : 'neutral'}
              subtitle="Average conveyor motors"
              size="medium"
            />
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <GaugeWidget
              title="Elevator Flow"
              value={metrics.tankLevel}
              min={0}
              max={500}
              unit="ton/h"
              thresholds={{ low: 150, medium: 300, high: 400 }}
              trend={metrics.tankLevel > prevValues.tankLevel ? 'up' : metrics.tankLevel < prevValues.tankLevel ? 'down' : 'neutral'}
              subtitle="ELV01 throughput"
              size="medium"
            />
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <GaugeWidget
              title="Total Power"
              value={metrics.power}
              min={0}
              max={500}
              unit="kW"
              thresholds={{ low: 150, medium: 300, high: 400 }}
              trend={metrics.power > prevValues.power ? 'up' : metrics.power < prevValues.power ? 'down' : 'neutral'}
              trendValue="All equipment"
              subtitle="Plant consumption"
              size="medium"
            />
          </Grid>
        </Grid>

        {/* Live Chart */}
        <Grid container spacing={3}>
          <Grid xs={12}>
            <ChartWidget
              title="Conveyor Flow Trend"
              subtitle="Real-time data from Node-RED Grain Terminal Simulator"
              data={chartData}
              type="line"
              dataKey="value"
              xAxisKey="time"
              color="primary"
              height={300}
              trend={metrics.flow > prevValues.flow ? 'up' : metrics.flow < prevValues.flow ? 'down' : 'neutral'}
              trendValue={lastUpdate ? `Updated ${lastUpdate.toLocaleTimeString()}` : 'Loading...'}
              showGrid
            />
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};
