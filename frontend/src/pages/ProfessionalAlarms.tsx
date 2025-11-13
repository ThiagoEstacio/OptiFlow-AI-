/**
 * Professional Alarms Page - Enterprise Alarm Management
 * Modern alarm monitoring and management with timeline view
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
  Tabs,
  Tab,
  Badge,
  alpha,
  useTheme
} from '@mui/material';
import Grid from '@mui/material/Unstable_Grid2';
import {
  Notifications,
  Error,
  Warning,
  Info,
  CheckCircle,
  NotificationsActive
} from '@mui/icons-material';
import { StatWidget } from '../components/professional/StatWidget';
import { TimelineWidget, TimelineEvent } from '../components/professional/TimelineWidget';
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
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export const ProfessionalAlarms: React.FC = () => {
  const theme = useTheme();
  const [currentTab, setCurrentTab] = useState(0);
  const [alarmStats, setAlarmStats] = useState({
    active: 12,
    critical: 3,
    warning: 6,
    info: 3,
    resolved: 48
  });

  // Sample alarm events
  const [activeAlarms, setActiveAlarms] = useState<TimelineEvent[]>([
    {
      id: '1',
      title: 'High Temperature Alert',
      description: 'Reactor temperature exceeded threshold (95°C)',
      timestamp: new Date(Date.now() - 5 * 60000),
      type: 'error',
      severity: 'critical',
      user: 'System',
      tags: ['temperature', 'reactor']
    },
    {
      id: '2',
      title: 'Low Pressure Warning',
      description: 'Main line pressure below optimal range',
      timestamp: new Date(Date.now() - 15 * 60000),
      type: 'warning',
      severity: 'high',
      user: 'System',
      tags: ['pressure', 'main-line']
    },
    {
      id: '3',
      title: 'Production Rate Deviation',
      description: 'Output rate 5% below target',
      timestamp: new Date(Date.now() - 30 * 60000),
      type: 'warning',
      severity: 'medium',
      user: 'System',
      tags: ['production', 'efficiency']
    },
    {
      id: '4',
      title: 'Sensor Communication Lost',
      description: 'Tag_003 stopped reporting data',
      timestamp: new Date(Date.now() - 45 * 60000),
      type: 'error',
      severity: 'high',
      user: 'System',
      tags: ['sensor', 'communication']
    },
    {
      id: '5',
      title: 'Maintenance Due',
      description: 'Scheduled maintenance in 2 hours',
      timestamp: new Date(Date.now() - 60 * 60000),
      type: 'info',
      severity: 'low',
      user: 'Maintenance Team',
      tags: ['maintenance', 'scheduled']
    }
  ]);

  const [historyAlarms, setHistoryAlarms] = useState<TimelineEvent[]>([
    {
      id: 'h1',
      title: 'Emergency Stop Resolved',
      description: 'System restarted successfully after emergency stop',
      timestamp: new Date(Date.now() - 2 * 3600000),
      type: 'success',
      user: 'Operator John',
      tags: ['emergency', 'resolved']
    },
    {
      id: 'h2',
      title: 'Vibration Alert Cleared',
      description: 'Motor vibration returned to normal levels',
      timestamp: new Date(Date.now() - 3 * 3600000),
      type: 'success',
      user: 'System',
      tags: ['vibration', 'motor']
    }
  ]);

  // Sample chart data
  const alarmTrendData = [
    { day: 'Mon', critical: 5, warning: 8, info: 3 },
    { day: 'Tue', critical: 3, warning: 6, info: 4 },
    { day: 'Wed', critical: 4, warning: 7, info: 2 },
    { day: 'Thu', critical: 2, warning: 5, info: 5 },
    { day: 'Fri', critical: 3, warning: 6, info: 3 },
    { day: 'Sat', critical: 1, warning: 3, info: 2 },
    { day: 'Sun', critical: 2, warning: 4, info: 1 }
  ];

  useEffect(() => {
    loadAlarms();
  }, []);

  const loadAlarms = async () => {
    try {
      const alarms = await apiClient.getActiveAlarms();
      // Process alarms...
    } catch (error) {
      console.error('Error loading alarms:', error);
    }
  };

  const handleAlarmClick = (event: TimelineEvent) => {
    console.log('Alarm clicked:', event);
    // Navigate to alarm details or open modal
  };

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', pb: 4 }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.error.main} 0%, ${theme.palette.error.dark} 100%)`,
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
                  Alarm Management Center
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.9 }}>
                  Real-time alarm monitoring and event tracking
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
                <NotificationsActive sx={{ fontSize: 32 }} />
              </Avatar>
            </Stack>

            {/* Status Chips */}
            <Stack direction="row" spacing={2} mt={3}>
              <Chip
                icon={<Error />}
                label={`${alarmStats.critical} Critical`}
                sx={{
                  bgcolor: 'rgba(255, 255, 255, 0.2)',
                  color: 'white',
                  fontWeight: 600,
                  backdropFilter: 'blur(10px)'
                }}
              />
              <Chip
                icon={<Warning />}
                label={`${alarmStats.warning} Warnings`}
                sx={{
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                  color: 'white',
                  backdropFilter: 'blur(10px)'
                }}
              />
              <Chip
                icon={<Info />}
                label={`${alarmStats.info} Info`}
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
        {/* Stats Grid */}
        <Grid container spacing={3} mb={3}>
          <Grid xs={12} sm={6} md={3}>
            <StatWidget
              title="Active Alarms"
              value={alarmStats.active}
              icon={<Notifications />}
              color="error"
              gradient
              subtitle={`${alarmStats.critical} critical`}
              footer="Requires attention"
              animate
            />
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <StatWidget
              title="Critical"
              value={alarmStats.critical}
              icon={<Error />}
              color="error"
              gradient
              subtitle="High priority"
              footer="Immediate action"
              animate
            />
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <StatWidget
              title="Warnings"
              value={alarmStats.warning}
              icon={<Warning />}
              color="warning"
              gradient
              subtitle="Medium priority"
              footer="Monitor closely"
            />
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <StatWidget
              title="Resolved Today"
              value={alarmStats.resolved}
              icon={<CheckCircle />}
              color="success"
              gradient
              subtitle="Successfully cleared"
              footer="95% resolution rate"
            />
          </Grid>
        </Grid>

        {/* Tabs */}
        <Paper sx={{ mb: 3 }}>
          <Tabs
            value={currentTab}
            onChange={(e, newValue) => setCurrentTab(newValue)}
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
            <Tab
              icon={
                <Badge badgeContent={alarmStats.active} color="error">
                  <Notifications />
                </Badge>
              }
              iconPosition="start"
              label="Active Alarms"
            />
            <Tab icon={<CheckCircle />} iconPosition="start" label="History" />
            <Tab icon={<Warning />} iconPosition="start" label="Analytics" />
          </Tabs>

          {/* Tab 0: Active Alarms */}
          <TabPanel value={currentTab} index={0}>
            <Grid container spacing={3}>
              <Grid xs={12} lg={8}>
                <TimelineWidget
                  title="Active Alarms"
                  events={activeAlarms}
                  maxEvents={20}
                  showTime
                  onEventClick={handleAlarmClick}
                />
              </Grid>

              <Grid xs={12} lg={4}>
                <Paper sx={{ p: 3, borderRadius: 2, height: '100%' }}>
                  <Typography variant="h6" fontWeight={600} mb={3}>
                    Alarm Summary
                  </Typography>

                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Most Common Type
                      </Typography>
                      <Typography variant="h6">Temperature Alerts</Typography>
                    </Box>

                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Average Resolution Time
                      </Typography>
                      <Typography variant="h6">15 minutes</Typography>
                    </Box>

                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Last Critical Alarm
                      </Typography>
                      <Typography variant="h6">5 minutes ago</Typography>
                    </Box>
                  </Stack>
                </Paper>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Tab 1: History */}
          <TabPanel value={currentTab} index={1}>
            <TimelineWidget
              title="Resolved Alarms"
              events={historyAlarms}
              maxEvents={50}
              showTime
              onEventClick={handleAlarmClick}
            />
          </TabPanel>

          {/* Tab 2: Analytics */}
          <TabPanel value={currentTab} index={2}>
            <ChartWidget
              title="Alarm Trends"
              subtitle="Weekly overview"
              data={alarmTrendData}
              type="bar"
              dataKey="critical"
              xAxisKey="day"
              color="error"
              height={350}
              trend="down"
              trendValue="-12%"
              showGrid
              showLegend
            />
          </TabPanel>
        </Paper>
      </Container>
    </Box>
  );
};
