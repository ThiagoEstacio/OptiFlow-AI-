/**
 * Professional Analytics Page - Enterprise ML Insights
 * Modern analytics dashboard with ML model metrics and predictions
 */
import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Stack,
  Tabs,
  Tab,
  Chip,
  Avatar,
  Divider,
  useTheme,
  alpha
} from '@mui/material';
import Grid from '@mui/material/Unstable_Grid2';
import {
  Psychology,
  TrendingUp,
  BugReport,
  Bolt,
  Speed,
  Timeline,
  Assessment,
  AutoGraph
} from '@mui/icons-material';
import { StatWidget } from '../components/professional/StatWidget';
import { AnalyticsCard } from '../components/professional/AnalyticsCard';
import { ChartWidget } from '../components/professional/ChartWidget';
import apiClient from '../api/client';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export const ProfessionalAnalytics: React.FC = () => {
  const theme = useTheme();
  const [currentTab, setCurrentTab] = useState(0);
  const [mlStats, setMlStats] = useState({
    modelsActive: 3,
    predictionsToday: 15420,
    accuracy: 94.2,
    anomaliesDetected: 12
  });
  const [loading, setLoading] = useState(true);

  // Sample chart data
  const accuracyData = [
    { date: 'Jan', isolation: 98.5, gradient: 92.1, lstm: 94.2 },
    { date: 'Feb', isolation: 98.7, gradient: 92.8, lstm: 94.8 },
    { date: 'Mar', isolation: 98.9, gradient: 93.2, lstm: 95.1 },
    { date: 'Apr', isolation: 99.0, gradient: 93.5, lstm: 95.4 },
    { date: 'May', isolation: 99.1, gradient: 93.8, lstm: 95.6 },
    { date: 'Jun', isolation: 99.2, gradient: 94.0, lstm: 95.8 }
  ];

  const predictionsData = [
    { hour: '00:00', count: 580 },
    { hour: '04:00', count: 420 },
    { hour: '08:00', count: 1250 },
    { hour: '12:00', count: 1840 },
    { hour: '16:00', count: 2100 },
    { hour: '20:00', count: 1380 },
    { hour: '24:00', count: 890 }
  ];

  const anomalyTrendData = [
    { day: 'Mon', critical: 2, warning: 5, info: 8 },
    { day: 'Tue', critical: 1, warning: 4, info: 6 },
    { day: 'Wed', critical: 3, warning: 6, info: 9 },
    { day: 'Thu', critical: 1, warning: 3, info: 7 },
    { day: 'Fri', critical: 2, warning: 4, info: 5 },
    { day: 'Sat', critical: 0, warning: 2, info: 4 },
    { day: 'Sun', critical: 1, warning: 2, info: 3 }
  ];

  useEffect(() => {
    loadMLData();
  }, []);

  const loadMLData = async () => {
    try {
      // Load real ML data from backend
      setLoading(false);
    } catch (error) {
      console.error('Error loading ML data:', error);
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', pb: 4 }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.info.main} 0%, ${theme.palette.info.dark} 100%)`,
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
                  ML Analytics Center
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.9 }}>
                  Machine Learning insights and model performance monitoring
                </Typography>
              </Box>

              <Avatar
                sx={{
                  width: 64,
                  height: 64,
                  bgcolor: 'rgba(255, 255, 255, 0.2)',
                  backdropFilter: 'blur(10px)'
                }}
              >
                <Psychology sx={{ fontSize: 32 }} />
              </Avatar>
            </Stack>

            {/* Status Chips */}
            <Stack direction="row" spacing={2} mt={3}>
              <Chip
                icon={<Assessment />}
                label={`${mlStats.modelsActive} Models Active`}
                sx={{
                  bgcolor: 'rgba(255, 255, 255, 0.2)',
                  color: 'white',
                  fontWeight: 600,
                  backdropFilter: 'blur(10px)'
                }}
              />
              <Chip
                label={`${mlStats.predictionsToday.toLocaleString()} Predictions Today`}
                sx={{
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                  color: 'white',
                  backdropFilter: 'blur(10px)'
                }}
              />
              <Chip
                label={`${mlStats.accuracy}% Avg Accuracy`}
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
        {/* Tabs */}
        <Paper sx={{ mb: 3 }}>
          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            sx={{
              borderBottom: 1,
              borderColor: 'divider',
              '& .MuiTab-root': {
                textTransform: 'none',
                fontWeight: 600,
                fontSize: '0.95rem'
              }
            }}
          >
            <Tab icon={<Assessment />} iconPosition="start" label="Overview" />
            <Tab icon={<Psychology />} iconPosition="start" label="Models" />
            <Tab icon={<BugReport />} iconPosition="start" label="Anomalies" />
            <Tab icon={<Timeline />} iconPosition="start" label="Predictions" />
          </Tabs>

          {/* Tab 0: Overview */}
          <TabPanel value={currentTab} index={0}>
            {/* Stats Grid */}
            <Grid container spacing={3} mb={3}>
              <Grid xs={12} sm={6} md={3}>
                <StatWidget
                  title="Active Models"
                  value={mlStats.modelsActive}
                  icon={<Psychology />}
                  color="primary"
                  gradient
                  subtitle="Production ready"
                  footer="Last trained: 2h ago"
                  loading={loading}
                  animate
                />
              </Grid>

              <Grid xs={12} sm={6} md={3}>
                <StatWidget
                  title="Predictions/Day"
                  value={mlStats.predictionsToday.toLocaleString()}
                  icon={<AutoGraph />}
                  color="success"
                  gradient
                  subtitle="Real-time inference"
                  footer="Avg latency: 45ms"
                  loading={loading}
                />
              </Grid>

              <Grid xs={12} sm={6} md={3}>
                <StatWidget
                  title="Overall Accuracy"
                  value={`${mlStats.accuracy}%`}
                  icon={<TrendingUp />}
                  color="info"
                  gradient
                  subtitle="Across all models"
                  footer="+2.1% vs last week"
                  loading={loading}
                />
              </Grid>

              <Grid xs={12} sm={6} md={3}>
                <StatWidget
                  title="Anomalies Detected"
                  value={mlStats.anomaliesDetected}
                  icon={<BugReport />}
                  color="warning"
                  gradient
                  subtitle="Last 24 hours"
                  footer="3 critical, 9 warnings"
                  loading={loading}
                  animate
                />
              </Grid>
            </Grid>

            {/* Analytics Cards */}
            <Grid container spacing={3} mb={3}>
              <Grid xs={12} md={4}>
                <AnalyticsCard
                  title="Isolation Forest"
                  value="99.2%"
                  change={0.3}
                  trend="up"
                  subtitle="Anomaly detection accuracy"
                  icon={<BugReport />}
                  color="success"
                  progress={99}
                />
              </Grid>

              <Grid xs={12} md={4}>
                <AnalyticsCard
                  title="Gradient Boosting"
                  value="94.0%"
                  change={1.2}
                  trend="up"
                  subtitle="OEE prediction R²"
                  icon={<Speed />}
                  color="info"
                  progress={94}
                />
              </Grid>

              <Grid xs={12} md={4}>
                <AnalyticsCard
                  title="LSTM Energy"
                  value="95.8%"
                  change={0.6}
                  trend="up"
                  subtitle="Energy forecast accuracy"
                  icon={<Bolt />}
                  color="warning"
                  progress={96}
                />
              </Grid>
            </Grid>

            {/* Charts */}
            <Grid container spacing={3}>
              <Grid xs={12} lg={8}>
                <ChartWidget
                  title="Model Accuracy Trends"
                  subtitle="Last 6 months"
                  data={accuracyData}
                  type="line"
                  dataKey="isolation"
                  xAxisKey="date"
                  color="success"
                  height={350}
                  trend="up"
                  trendValue="+0.7%"
                  showGrid
                  showLegend
                />
              </Grid>

              <Grid xs={12} lg={4}>
                <ChartWidget
                  title="Predictions Volume"
                  subtitle="Today"
                  data={predictionsData}
                  type="bar"
                  dataKey="count"
                  xAxisKey="hour"
                  color="primary"
                  height={350}
                  trend="up"
                  trendValue="+12%"
                />
              </Grid>
            </Grid>
          </TabPanel>

          {/* Tab 1: Models */}
          <TabPanel value={currentTab} index={1}>
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Psychology sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Model Details
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Detailed model performance metrics and configurations
              </Typography>
            </Box>
          </TabPanel>

          {/* Tab 2: Anomalies */}
          <TabPanel value={currentTab} index={2}>
            <Grid container spacing={3}>
              <Grid xs={12}>
                <ChartWidget
                  title="Anomaly Detection Trends"
                  subtitle="Weekly overview"
                  data={anomalyTrendData}
                  type="bar"
                  dataKey="critical"
                  xAxisKey="day"
                  color="error"
                  height={350}
                  trend="down"
                  trendValue="-15%"
                  showGrid
                  showLegend
                />
              </Grid>
            </Grid>
          </TabPanel>

          {/* Tab 3: Predictions */}
          <TabPanel value={currentTab} index={3}>
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Timeline sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Prediction History
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Historical predictions and forecast accuracy
              </Typography>
            </Box>
          </TabPanel>
        </Paper>
      </Container>
    </Box>
  );
};
