import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  TextField,
  MenuItem,
  Badge,
  Alert,
  Divider,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as SuccessIcon,
  Visibility as ViewIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import apiClient from '../api/client';

interface AlarmEvent {
  id: string;
  type: 'alarm' | 'event' | 'anomaly' | 'prediction';
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  description: string;
  tag_name?: string;
  value?: number;
  threshold?: number;
  timestamp: string;
  acknowledged: boolean;
  source: string;
}

const AlarmsEventsView: React.FC = () => {
  const [alarms, setAlarms] = useState<AlarmEvent[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [selectedAlarm, setSelectedAlarm] = useState<AlarmEvent | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Fetch alarms and events
  const fetchAlarms = async () => {
    try {
      // Fetch from autonomous agent insights
      const insightsResponse = await apiClient.get('/api/v1/demo/ai-agent/insights');

      // Fetch ML alerts
      const mlResponse = await apiClient.get('/api/v1/ml/insights/all', {
        params: { time_range: 'last_24h' },
      });

      // Combine and format alarms
      const agentAlarms: AlarmEvent[] = insightsResponse.data.map((insight: any) => ({
        id: insight.id || insight.insight_id,
        type: insight.category === 'anomaly' ? 'anomaly' : insight.category === 'prediction' ? 'prediction' : 'event',
        severity: insight.severity || 'medium',
        title: insight.title,
        description: insight.description,
        tag_name: insight.tags?.[0],
        timestamp: insight.timestamp,
        acknowledged: false,
        source: 'Autonomous Agent',
      }));

      // Add ML alarms
      const mlAlarms: AlarmEvent[] = [];
      if (mlResponse.data.insights) {
        const { energy_prediction, anomalies, reliability } = mlResponse.data.insights;

        // Energy alarms
        if (energy_prediction?.status === 'success' && energy_prediction.abnormal_consumption) {
          mlAlarms.push({
            id: `ml-energy-${Date.now()}`,
            type: 'prediction',
            severity: 'high',
            title: 'Abnormal Energy Consumption Detected',
            description: `Current consumption: ${energy_prediction.current_consumption_kwh?.toFixed(2)} kWh is above expected range`,
            timestamp: new Date().toISOString(),
            acknowledged: false,
            source: 'ML Energy Predictor',
          });
        }

        // Anomaly alarms
        if (anomalies?.status === 'success' && anomalies.recent_anomalies > 5) {
          mlAlarms.push({
            id: `ml-anomaly-${Date.now()}`,
            type: 'anomaly',
            severity: 'high',
            title: `${anomalies.recent_anomalies} Anomalies Detected`,
            description: `Multiple anomalies detected in the last 24 hours. Anomaly score: ${anomalies.anomaly_score?.toFixed(2)}`,
            timestamp: new Date().toISOString(),
            acknowledged: false,
            source: 'ML Anomaly Detector',
          });
        }

        // Reliability alarms
        if (reliability?.status === 'success' && reliability.critical_equipment?.length > 0) {
          reliability.critical_equipment.forEach((eq: any) => {
            mlAlarms.push({
              id: `ml-reliability-${eq.equipment_id}`,
              type: 'alarm',
              severity: 'critical',
              title: `Critical MTBF: ${eq.equipment_id}`,
              description: `MTBF: ${eq.mtbf_hours?.toFixed(1)}h is below threshold. Immediate maintenance required.`,
              tag_name: eq.equipment_id,
              timestamp: new Date().toISOString(),
              acknowledged: false,
              source: 'ML Reliability Analyzer',
            });
          });
        }
      }

      const allAlarms = [...agentAlarms, ...mlAlarms].sort(
        (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );

      setAlarms(allAlarms);
    } catch (error) {
      console.error('Error fetching alarms:', error);
    }
  };

  useEffect(() => {
    fetchAlarms();
    const interval = setInterval(fetchAlarms, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  // Filter alarms
  const filteredAlarms = alarms.filter((alarm) => {
    if (filter !== 'all' && alarm.type !== filter) return false;
    if (severityFilter !== 'all' && alarm.severity !== severityFilter) return false;
    return true;
  });

  // Statistics
  const stats = {
    total: alarms.length,
    critical: alarms.filter((a) => a.severity === 'critical').length,
    high: alarms.filter((a) => a.severity === 'high').length,
    medium: alarms.filter((a) => a.severity === 'medium').length,
    low: alarms.filter((a) => a.severity === 'low').length,
    unacknowledged: alarms.filter((a) => !a.acknowledged).length,
  };

  // Chart data
  const severityData = [
    { name: 'Critical', value: stats.critical, color: '#d32f2f' },
    { name: 'High', value: stats.high, color: '#f57c00' },
    { name: 'Medium', value: stats.medium, color: '#fbc02d' },
    { name: 'Low', value: stats.low, color: '#388e3c' },
  ];

  const typeData = [
    { name: 'Alarms', value: alarms.filter((a) => a.type === 'alarm').length },
    { name: 'Events', value: alarms.filter((a) => a.type === 'event').length },
    { name: 'Anomalies', value: alarms.filter((a) => a.type === 'anomaly').length },
    { name: 'Predictions', value: alarms.filter((a) => a.type === 'prediction').length },
  ];

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <ErrorIcon sx={{ color: 'error.main' }} />;
      case 'high':
        return <WarningIcon sx={{ color: 'warning.main' }} />;
      case 'medium':
        return <InfoIcon sx={{ color: 'info.main' }} />;
      case 'low':
      case 'info':
        return <SuccessIcon sx={{ color: 'success.main' }} />;
      default:
        return <InfoIcon />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
      case 'info':
        return 'success';
      default:
        return 'default';
    }
  };

  const handleViewDetails = (alarm: AlarmEvent) => {
    setSelectedAlarm(alarm);
    setDetailsOpen(true);
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 600 }}>
        Alarms & Events Dashboard
      </Typography>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" variant="body2">
                Total Active
              </Typography>
              <Typography variant="h4" sx={{ mt: 1 }}>
                <Badge badgeContent={stats.unacknowledged} color="error">
                  {stats.total}
                </Badge>
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ bgcolor: 'error.main', color: 'white' }}>
            <CardContent>
              <Typography variant="body2">Critical</Typography>
              <Typography variant="h4" sx={{ mt: 1 }}>
                {stats.critical}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ bgcolor: 'warning.main', color: 'white' }}>
            <CardContent>
              <Typography variant="body2">High</Typography>
              <Typography variant="h4" sx={{ mt: 1 }}>
                {stats.high}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ bgcolor: 'info.main', color: 'white' }}>
            <CardContent>
              <Typography variant="body2">Medium</Typography>
              <Typography variant="h4" sx={{ mt: 1 }}>
                {stats.medium}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card sx={{ bgcolor: 'success.main', color: 'white' }}>
            <CardContent>
              <Typography variant="body2">Low</Typography>
              <Typography variant="h4" sx={{ mt: 1 }}>
                {stats.low}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" variant="body2">
                Unacknowledged
              </Typography>
              <Typography variant="h4" sx={{ mt: 1, color: 'error.main' }}>
                {stats.unacknowledged}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Alarms by Severity
              </Typography>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={severityData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label
                  >
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Events by Type
              </Typography>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={typeData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#1976d2" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <FilterIcon />
            <TextField
              select
              size="small"
              label="Type"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              sx={{ minWidth: 150 }}
            >
              <MenuItem value="all">All Types</MenuItem>
              <MenuItem value="alarm">Alarms</MenuItem>
              <MenuItem value="event">Events</MenuItem>
              <MenuItem value="anomaly">Anomalies</MenuItem>
              <MenuItem value="prediction">Predictions</MenuItem>
            </TextField>
            <TextField
              select
              size="small"
              label="Severity"
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              sx={{ minWidth: 150 }}
            >
              <MenuItem value="all">All Severities</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="low">Low</MenuItem>
            </TextField>
            <Typography variant="body2" sx={{ ml: 'auto' }}>
              Showing {filteredAlarms.length} of {alarms.length} events
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Alarms Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Active Alarms & Events
          </Typography>
          <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Severity</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Title</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Source</TableCell>
                  <TableCell>Timestamp</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredAlarms.map((alarm) => (
                  <TableRow
                    key={alarm.id}
                    sx={{
                      bgcolor: alarm.acknowledged ? 'transparent' : 'action.hover',
                      '&:hover': { bgcolor: 'action.selected' },
                    }}
                  >
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getSeverityIcon(alarm.severity)}
                        <Chip
                          label={alarm.severity.toUpperCase()}
                          size="small"
                          color={getSeverityColor(alarm.severity) as any}
                        />
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip label={alarm.type} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {alarm.title}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {alarm.description.substring(0, 80)}...
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={alarm.source} size="small" />
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {new Date(alarm.timestamp).toLocaleString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {alarm.acknowledged ? (
                        <Chip label="Acknowledged" size="small" color="success" />
                      ) : (
                        <Chip label="Active" size="small" color="error" />
                      )}
                    </TableCell>
                    <TableCell>
                      <IconButton size="small" onClick={() => handleViewDetails(alarm)}>
                        <ViewIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Details Dialog */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Alarm Details</DialogTitle>
        <DialogContent>
          {selectedAlarm && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Alert severity={getSeverityColor(selectedAlarm.severity) as any}>
                    <Typography variant="h6">{selectedAlarm.title}</Typography>
                  </Alert>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Type
                  </Typography>
                  <Typography variant="body1">{selectedAlarm.type}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Severity
                  </Typography>
                  <Typography variant="body1">{selectedAlarm.severity}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Source
                  </Typography>
                  <Typography variant="body1">{selectedAlarm.source}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Timestamp
                  </Typography>
                  <Typography variant="body1">
                    {new Date(selectedAlarm.timestamp).toLocaleString()}
                  </Typography>
                </Grid>
                {selectedAlarm.tag_name && (
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">
                      Tag Name
                    </Typography>
                    <Typography variant="body1">{selectedAlarm.tag_name}</Typography>
                  </Grid>
                )}
                <Grid item xs={12}>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Description
                  </Typography>
                  <Typography variant="body1">{selectedAlarm.description}</Typography>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
          <Button variant="contained" color="primary">
            Acknowledge
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AlarmsEventsView;
