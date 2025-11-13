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
import Grid from '@mui/material/Unstable_Grid2';
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
import { useRealtimeData, useWebSocketStatus } from '../hooks/useRealtimeData';
import apiClient from '../api/client';

interface TagData {
  id: string;
  name: string;
  value: number;
  unit: string;
  deviceType?: string;
  quality?: 'good' | 'uncertain' | 'bad';
}

export const ProfessionalRealtime: React.FC = () => {
  const theme = useTheme();
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [tags, setTags] = useState<TagData[]>([]);
  const [loading, setLoading] = useState(true);

  // WebSocket connection status
  const isConnected = useWebSocketStatus();

  // Real-time tag updates (when backend WebSocket is ready)
  const { data: realtimeUpdate } = useRealtimeData<TagData>('tag_update');

  // Sample real-time data for demonstration
  const [liveData, setLiveData] = useState({
    production_rate: { value: 1050, trend: 'up' as const },
    temperature: { value: 78.5, trend: 'neutral' as const },
    pressure: { value: 92.3, trend: 'down' as const },
    oee: { value: 85.2, trend: 'up' as const }
  });

  // Chart data for trends
  const [chartData, setChartData] = useState([
    { time: '10:00', value: 1000 },
    { time: '10:05', value: 1020 },
    { time: '10:10', value: 1040 },
    { time: '10:15', value: 1030 },
    { time: '10:20', value: 1050 }
  ]);

  useEffect(() => {
    loadTags();

    // Simulate real-time updates
    const interval = setInterval(() => {
      setLiveData(prev => ({
        production_rate: {
          value: prev.production_rate.value + (Math.random() - 0.5) * 20,
          trend: Math.random() > 0.5 ? 'up' : 'down'
        },
        temperature: {
          value: prev.temperature.value + (Math.random() - 0.5) * 2,
          trend: Math.random() > 0.5 ? 'up' : 'down'
        },
        pressure: {
          value: prev.pressure.value + (Math.random() - 0.5) * 5,
          trend: Math.random() > 0.5 ? 'up' : 'down'
        },
        oee: {
          value: Math.max(75, Math.min(95, prev.oee.value + (Math.random() - 0.5) * 3)),
          trend: Math.random() > 0.5 ? 'up' : 'down'
        }
      }));

      // Update chart data
      setChartData(prev => {
        const newData = [...prev.slice(1), {
          time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          value: 1000 + Math.random() * 100
        }];
        return newData;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const loadTags = async () => {
    try {
      const tagsData = await apiClient.getTags();
      setTags(tagsData.slice(0, 12)); // Show first 12 tags
      setLoading(false);
    } catch (error) {
      console.error('Error loading tags:', error);
      setLoading(false);
    }
  };

  // Update tag data when real-time update arrives
  useEffect(() => {
    if (realtimeUpdate) {
      setTags(prev =>
        prev.map(tag =>
          tag.id === realtimeUpdate.id ? { ...tag, ...realtimeUpdate } : tag
        )
      );
    }
  }, [realtimeUpdate]);

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
              title="Production Rate"
              value={liveData.production_rate.value}
              min={800}
              max={1200}
              unit="units/h"
              thresholds={{ low: 900, medium: 1000, high: 1100 }}
              trend={liveData.production_rate.trend}
              trendValue={`${((liveData.production_rate.value / 1000 - 1) * 100).toFixed(1)}%`}
              subtitle="Current output"
              size="medium"
            />
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <GaugeWidget
              title="Temperature"
              value={liveData.temperature.value}
              min={0}
              max={100}
              unit="°C"
              thresholds={{ low: 60, medium: 75, high: 85 }}
              trend={liveData.temperature.trend}
              subtitle="Reactor core"
              size="medium"
            />
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <GaugeWidget
              title="Pressure"
              value={liveData.pressure.value}
              min={0}
              max={120}
              unit="PSI"
              thresholds={{ low: 70, medium: 85, high: 100 }}
              trend={liveData.pressure.trend}
              subtitle="Main line"
              size="medium"
            />
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <GaugeWidget
              title="OEE"
              value={liveData.oee.value}
              min={0}
              max={100}
              unit="%"
              thresholds={{ low: 75, medium: 85, high: 95 }}
              trend={liveData.oee.trend}
              trendValue={`${(liveData.oee.value - 85).toFixed(1)}%`}
              subtitle="Overall efficiency"
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
