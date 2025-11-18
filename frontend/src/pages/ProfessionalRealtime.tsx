/**
 * Professional Real-time Page - Live Industrial Data Monitoring
 * Real-time tag monitoring with WebSocket updates
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Stack,
  Chip,
  Avatar,
  IconButton,
  ToggleButtonGroup,
  ToggleButton,
  alpha,
  useTheme
} from '@mui/material';
import { Grid } from '../components/GridWrapper';
import {
  Speed,
  Refresh,
  ViewModule,
  ViewList,
  Circle,
  SignalCellularAlt
} from '@mui/icons-material';
import { GaugeWidget } from '../components/professional/GaugeWidget';
import { StatWidget } from '../components/professional/StatWidget';
import { ChartWidget } from '../components/professional/ChartWidget';
import { useRealtimeData, useWebSocketStatus, SimulatorUpdate } from '../hooks/useRealtimeData';
import apiClient from '../api/client';

interface TagData {
  id: string;
  name: string;
  value: number;
  unit: string;
  deviceType?: string;
  quality?: 'good' | 'uncertain' | 'bad';
}

interface ChartDataPoint {
  time: string;
  value: number;
}

export const ProfessionalRealtime: React.FC = () => {
  const theme = useTheme();
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [tags, setTags] = useState<TagData[]>([]);
  const [loading, setLoading] = useState(true);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);

  // WebSocket connection status
  const isConnected = useWebSocketStatus();

  // Real-time simulator updates from WebSocket
  const { data: simulatorData } = useRealtimeData<SimulatorUpdate>('simulator_update');

  // Previous values for trend calculation
  const [prevValues, setPrevValues] = useState({
    production_rate: 0,
    temperature: 0,
    pressure: 0,
    power: 0
  });

  // Load historical chart data on mount
  useEffect(() => {
    loadTags();
    loadHistoricalData();
  }, []);

  // Update chart data when simulator updates arrive
  useEffect(() => {
    if (simulatorData?.tags) {
      const flowValue = simulatorData.tags['SLD01_FLOW_TPH_PV'] || 0;
      const timestamp = new Date(simulatorData.timestamp);

      setChartData(prev => {
        const newPoint = {
          time: timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          value: flowValue
        };

        // Keep last 20 points (rolling window)
        const updated = [...prev, newPoint];
        return updated.slice(-20);
      });
    }
  }, [simulatorData]);

  const loadTags = async () => {
    try {
      const tagsData = await apiClient.getTags();
      setTags(tagsData.slice(0, 12) as any); // Show first 12 tags
      setLoading(false);
    } catch (error) {
      console.error('Error loading tags:', error);
      setLoading(false);
    }
  };

  const loadHistoricalData = async () => {
    try {
      const response = await apiClient.get(
        '/api/v1/tags/timeseries/SLD01_FLOW_TPH_PV?start_minutes_ago=5'
      );
      const result = response.data;
      if (result && result.data && result.data.length > 0) {
        const historicalPoints = result.data.map((point: any) => ({
          time: new Date(point.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
          }),
          value: point.value
        }));
        setChartData(historicalPoints.slice(-20)); // Keep last 20 points
      }
    } catch (error) {
      console.error('Error loading historical data:', error);
    }
  };

  // Update tags when simulator data arrives
  useEffect(() => {
    if (simulatorData?.tags && tags.length > 0) {
      setTags(prev =>
        prev.map(tag => {
          const tagValue = simulatorData.tags[tag.id];
          if (tagValue !== undefined) {
            return { ...tag, value: tagValue, quality: 'good' as const };
          }
          return tag;
        })
      );
    }
  }, [simulatorData]);

  // Track previous values for trend calculation
  useEffect(() => {
    if (simulatorData?.tags && simulatorData?.status) {
      setPrevValues({
        production_rate: simulatorData.tags['SLD01_FLOW_TPH_PV'] || 0,
        temperature: simulatorData.tags['CORR01_TEMP_C_PV'] || 0,
        pressure: simulatorData.status.system.warehouse_level_pct || 0,
        power: simulatorData.tags['SLD01_POWER_KW_PV'] || 0
      });
    }
  }, [simulatorData]);

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', pb: 4 }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.success.main} 0%, ${theme.palette.success.dark} 100%)`,
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
                  Real-time Monitoring
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.9 }}>
                  Live industrial data streaming and visualization
                </Typography>
              </Box>

              <Stack direction="row" spacing={2} alignItems="center">
                {/* Connection Status */}
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
                  label={isConnected ? 'Live' : 'Disconnected'}
                  sx={{
                    bgcolor: isConnected
                      ? 'rgba(76, 175, 80, 0.2)'
                      : 'rgba(255, 255, 255, 0.2)',
                    color: 'white',
                    fontWeight: 600,
                    backdropFilter: 'blur(10px)'
                  }}
                />

                <Avatar
                  sx={{
                    width: 64,
                    height: 64,
                    bgcolor: 'rgba(255, 255, 255, 0.2)',
                    backdropFilter: 'blur(10px)'
                  }}
                >
                  <SignalCellularAlt sx={{ fontSize: 32 }} />
                </Avatar>
              </Stack>
            </Stack>
          </Box>
        </Container>
      </Paper>

      <Container maxWidth="xl">
        {/* Controls */}
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6" fontWeight={600}>
            Live Metrics
          </Typography>

          <Stack direction="row" spacing={2}>
            <IconButton onClick={loadTags} color="primary">
              <Refresh />
            </IconButton>

            <ToggleButtonGroup
              value={viewMode}
              exclusive
              onChange={(e, newMode) => newMode && setViewMode(newMode)}
              size="small"
            >
              <ToggleButton value="grid">
                <ViewModule />
              </ToggleButton>
              <ToggleButton value="list">
                <ViewList />
              </ToggleButton>
            </ToggleButtonGroup>
          </Stack>
        </Stack>

        {/* Key Metrics - Gauges */}
        <Grid container spacing={3} mb={3}>
          <Grid xs={12} sm={6} md={3}>
            <GaugeWidget
              title="Shiploader Flow"
              value={simulatorData?.tags['SLD01_FLOW_TPH_PV'] || 0}
              min={0}
              max={2500}
              unit="t/h"
              thresholds={{ low: 1000, medium: 1500, high: 2000 }}
              trend={
                simulatorData?.tags['SLD01_FLOW_TPH_PV'] ?? 0 > prevValues.production_rate
                  ? 'up'
                  : simulatorData?.tags['SLD01_FLOW_TPH_PV'] ?? 0 < prevValues.production_rate
                  ? 'down'
                  : 'neutral'
              }
              trendValue={`${simulatorData?.tags['SLD01_SETPOINT_TPH_PV']?.toFixed(0) || 0} t/h target`}
              subtitle="Production rate"
              size="medium"
            />
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <GaugeWidget
              title="Belt Temperature"
              value={simulatorData?.tags['CORR01_TEMP_C_PV'] || 0}
              min={0}
              max={100}
              unit="°C"
              thresholds={{ low: 50, medium: 70, high: 85 }}
              trend={
                simulatorData?.tags['CORR01_TEMP_C_PV'] ?? 0 > prevValues.temperature
                  ? 'up'
                  : simulatorData?.tags['CORR01_TEMP_C_PV'] ?? 0 < prevValues.temperature
                  ? 'down'
                  : 'neutral'
              }
              subtitle="Conveyor CORR01"
              size="medium"
            />
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <GaugeWidget
              title="Warehouse Level"
              value={simulatorData?.status?.system?.warehouse_level_pct || 0}
              min={0}
              max={100}
              unit="%"
              thresholds={{ low: 30, medium: 60, high: 85 }}
              trend={
                simulatorData?.status?.system?.warehouse_level_pct ?? 0 > prevValues.pressure
                  ? 'up'
                  : simulatorData?.status?.system?.warehouse_level_pct ?? 0 < prevValues.pressure
                  ? 'down'
                  : 'neutral'
              }
              subtitle="Storage capacity"
              size="medium"
            />
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <GaugeWidget
              title="Total Power"
              value={simulatorData?.tags['SLD01_POWER_KW_PV'] || 0}
              min={0}
              max={500}
              unit="kW"
              thresholds={{ low: 200, medium: 350, high: 450 }}
              trend={
                simulatorData?.tags['SLD01_POWER_KW_PV'] ?? 0 > prevValues.power
                  ? 'up'
                  : simulatorData?.tags['SLD01_POWER_KW_PV'] ?? 0 < prevValues.power
                  ? 'down'
                  : 'neutral'
              }
              trendValue={`${simulatorData?.status?.system?.kWh_per_ton?.toFixed(2) || 0} kWh/t`}
              subtitle="Shiploader power"
              size="medium"
            />
          </Grid>
        </Grid>

        {/* Live Chart */}
        <Grid container spacing={3} mb={3}>
          <Grid xs={12}>
            <ChartWidget
              title="Production Rate Trend"
              subtitle="Last 5 minutes"
              data={chartData}
              type="line"
              dataKey="value"
              xAxisKey="time"
              color="success"
              height={300}
              trend="up"
              trendValue="+5.2%"
              showGrid
            />
          </Grid>
        </Grid>

        {/* Tag Grid */}
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h6" fontWeight={600} mb={3}>
            All Tags ({tags.length})
          </Typography>

          <Grid container spacing={2}>
            {tags.map((tag) => (
              <Grid key={tag.id} xs={12} sm={6} md={4} lg={3}>
                <StatWidget
                  title={tag.name}
                  value={tag.value?.toFixed(1) || '0.0'}
                  icon={<Speed />}
                  color="primary"
                  subtitle={tag.unit || ''}
                  footer={tag.deviceType || 'Sensor'}
                  loading={loading}
                />
              </Grid>
            ))}
          </Grid>
        </Paper>
      </Container>
    </Box>
  );
};
