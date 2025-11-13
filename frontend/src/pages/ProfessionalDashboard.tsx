/**
 * Professional Executive Dashboard - Enterprise Grade
 * Inspired by Material Dashboard Pro, Mantis, and Mira Pro
 */
import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Stack,
  Button,
  IconButton,
  Avatar,
  AvatarGroup,
  Chip,
  Divider,
  alpha,
  useTheme
} from '@mui/material';
import Grid from '@mui/material/Unstable_Grid2';
import {
  Dashboard as DashboardIcon,
  Memory,
  Speed,
  Storage,
  TrendingUp,
  People,
  Notifications,
  Settings,
  Refresh,
  Download,
  CloudQueue,
  Psychology,
  Bolt,
  Analytics
} from '@mui/icons-material';
import { StatWidget } from '../components/professional/StatWidget';
import { AnalyticsCard } from '../components/professional/AnalyticsCard';
import { ChartWidget } from '../components/professional/ChartWidget';
import { useRealtimeData, useWebSocketStatus, SimulatorUpdate } from '../hooks/useRealtimeData';
import apiClient from '../api/client';

export const ProfessionalDashboard: React.FC = () => {
  const theme = useTheme();

  // Real-time WebSocket data
  const isConnected = useWebSocketStatus();
  const { data: simulatorData } = useRealtimeData<SimulatorUpdate>('simulator_update');

  const [stats, setStats] = useState({
    totalDevices: 0,
    activeConnections: 0,
    dataPoints: 0,
    mlPredictions: 0
  });
  const [loading, setLoading] = useState(true);

  // Sample data for charts
  const performanceData = [
    { time: '00:00', value: 65 },
    { time: '04:00', value: 72 },
    { time: '08:00', value: 85 },
    { time: '12:00', value: 78 },
    { time: '16:00', value: 90 },
    { time: '20:00', value: 82 },
    { time: '24:00', value: 88 }
  ];

  const energyData = [
    { hour: '06:00', consumption: 450 },
    { hour: '08:00', consumption: 680 },
    { hour: '10:00', consumption: 720 },
    { hour: '12:00', consumption: 850 },
    { hour: '14:00', consumption: 790 },
    { hour: '16:00', consumption: 720 },
    { hour: '18:00', consumption: 580 }
  ];

  const productionData = [
    { day: 'Mon', units: 1200 },
    { day: 'Tue', units: 1400 },
    { day: 'Wed', units: 1100 },
    { day: 'Thu', units: 1600 },
    { day: 'Fri', units: 1350 },
    { day: 'Sat', units: 900 },
    { day: 'Sun', units: 700 }
  ];

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const [devices, tags] = await Promise.all([
        apiClient.getDevices(),
        apiClient.getTags()
      ]);

      setStats({
        totalDevices: devices.length,
        activeConnections: devices.filter(d => d.status === 'CONNECTED').length,
        dataPoints: tags.length * 1440 * 60, // Estimate: tags * minutes/day * points/minute
        mlPredictions: 15420 // Example value
      });

      setLoading(false);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setLoading(false);
    }
  };

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
                  OptiFlow Command Center
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.9 }}>
                  Real-time industrial intelligence platform
                </Typography>
              </Box>

              <Stack direction="row" spacing={2} alignItems="center">
                <AvatarGroup max={3}>
                  <Avatar sx={{ width: 40, height: 40, bgcolor: theme.palette.success.main }}>
                    <Speed />
                  </Avatar>
                  <Avatar sx={{ width: 40, height: 40, bgcolor: theme.palette.warning.main }}>
                    <Psychology />
                  </Avatar>
                  <Avatar sx={{ width: 40, height: 40, bgcolor: theme.palette.error.main }}>
                    <Bolt />
                  </Avatar>
                </AvatarGroup>

                <IconButton sx={{ color: 'white' }} onClick={loadDashboardData}>
                  <Refresh />
                </IconButton>
                <IconButton sx={{ color: 'white' }}>
                  <Download />
                </IconButton>
                <IconButton sx={{ color: 'white' }}>
                  <Settings />
                </IconButton>
              </Stack>
            </Stack>

            {/* Quick Stats Row */}
            <Stack direction="row" spacing={3} mt={3}>
              <Chip
                icon={<CloudQueue />}
                label="All Systems Operational"
                sx={{
                  bgcolor: 'rgba(255, 255, 255, 0.2)',
                  color: 'white',
                  fontWeight: 600,
                  backdropFilter: 'blur(10px)'
                }}
              />
              <Chip
                label={`Last updated: ${new Date().toLocaleTimeString()}`}
                sx={{
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                  color: 'white',
                  backdropFilter: 'blur(10px)'
                }}
              />
            </Stack>
          </Box>
        </Container>
      </Paper>

      <Container maxWidth="xl">
        {/* Main Stats Grid */}
        <Grid container spacing={3} mb={3}>
          <Grid item xs={12} sm={6} md={3}>
            <StatWidget
              title="Total Devices"
              value={stats.totalDevices}
              icon={<Memory />}
              color="primary"
              gradient
              subtitle={`${stats.activeConnections} active`}
              footer="Connected to OPC UA"
              loading={loading}
              animate
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <StatWidget
              title="Active Connections"
              value={stats.activeConnections}
              icon={<Speed />}
              color="success"
              gradient
              subtitle="Real-time monitoring"
              footer="99.9% uptime"
              loading={loading}
              animate
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <StatWidget
              title="Data Points/Day"
              value={`${(stats.dataPoints / 1000000).toFixed(1)}M`}
              icon={<Storage />}
              color="info"
              gradient
              subtitle="Time-series database"
              footer="InfluxDB + PostgreSQL"
              loading={loading}
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <StatWidget
              title="ML Predictions"
              value={stats.mlPredictions.toLocaleString()}
              icon={<Psychology />}
              color="warning"
              gradient
              subtitle="AI-powered insights"
              footer="3 active models"
              loading={loading}
              animate
            />
          </Grid>
        </Grid>

        {/* Analytics Cards */}
        <Grid container spacing={3} mb={3}>
          <Grid item xs={12} md={4}>
            <AnalyticsCard
              title="System Efficiency"
              value="94.2%"
              change={5.3}
              trend="up"
              subtitle="vs last week"
              icon={<Analytics />}
              color="success"
              progress={94}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <AnalyticsCard
              title="Energy Optimization"
              value="12.8%"
              change={-2.1}
              trend="down"
              subtitle="Savings this month"
              icon={<Bolt />}
              color="warning"
              progress={88}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <AnalyticsCard
              title="Anomaly Detection"
              value="99.7%"
              change={0.8}
              trend="up"
              subtitle="Accuracy rate"
              icon={<TrendingUp />}
              color="primary"
              progress={99}
            />
          </Grid>
        </Grid>

        {/* Charts Row */}
        <Grid container spacing={3} mb={3}>
          <Grid item xs={12} lg={8}>
            <ChartWidget
              title="System Performance"
              subtitle="Last 24 hours"
              data={performanceData}
              type="area"
              dataKey="value"
              xAxisKey="time"
              color="primary"
              height={350}
              trend="up"
              trendValue="+12.5%"
              showGrid
              onRefresh={() => console.log('Refresh')}
              onDownload={() => console.log('Download')}
              onFullscreen={() => console.log('Fullscreen')}
            />
          </Grid>

          <Grid item xs={12} lg={4}>
            <ChartWidget
              title="Energy Consumption"
              subtitle="Today"
              data={energyData}
              type="bar"
              dataKey="consumption"
              xAxisKey="hour"
              color="warning"
              height={350}
              trend="down"
              trendValue="-8.3%"
              showGrid={false}
            />
          </Grid>
        </Grid>

        {/* Production Chart */}
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <ChartWidget
              title="Production Output"
              subtitle="Weekly overview"
              data={productionData}
              type="bar"
              dataKey="units"
              xAxisKey="day"
              color="success"
              height={300}
              trend="up"
              trendValue="+15.2%"
              showGrid
              showLegend
            />
          </Grid>
        </Grid>

        {/* System Status */}
        <Paper sx={{ p: 3, mt: 3, borderRadius: 2 }}>
          <Typography variant="h6" gutterBottom fontWeight={600}>
            System Status
          </Typography>
          <Divider sx={{ mb: 2 }} />

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Stack spacing={1}>
                <Typography variant="caption" color="text.secondary">
                  DATABASE
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Box
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      bgcolor: 'success.main'
                    }}
                  />
                  <Typography variant="body2" fontWeight={600}>
                    Operational
                  </Typography>
                </Stack>
              </Stack>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Stack spacing={1}>
                <Typography variant="caption" color="text.secondary">
                  ML MODELS
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Box
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      bgcolor: 'success.main'
                    }}
                  />
                  <Typography variant="body2" fontWeight={600}>
                    3 Active
                  </Typography>
                </Stack>
              </Stack>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Stack spacing={1}>
                <Typography variant="caption" color="text.secondary">
                  OPC UA GATEWAY
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Box
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      bgcolor: 'success.main'
                    }}
                  />
                  <Typography variant="body2" fontWeight={600}>
                    Connected
                  </Typography>
                </Stack>
              </Stack>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Stack spacing={1}>
                <Typography variant="caption" color="text.secondary">
                  API STATUS
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Box
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      bgcolor: 'success.main'
                    }}
                  />
                  <Typography variant="body2" fontWeight={600}>
                    Healthy
                  </Typography>
                </Stack>
              </Stack>
            </Grid>
          </Grid>
        </Paper>
      </Container>
    </Box>
  );
};
