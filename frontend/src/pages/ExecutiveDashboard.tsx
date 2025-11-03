/**
 * Executive Dashboard 360°
 *
 * Unified view of maintenance + operations with ROI Calculator and strategic insights.
 * This is the game-changer that demonstrates business value.
 */
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AttachMoney,
  Warning,
  CheckCircle,
  Refresh,
  Download,
  Info,
} from '@mui/icons-material';
import { format } from 'date-fns';

import OverallHealthScore from '../components/executive/OverallHealthScore';
import ROICalculator from '../components/executive/ROICalculator';
import MaintenanceKPIs from '../components/executive/MaintenanceKPIs';
import OperationalKPIs from '../components/executive/OperationalKPIs';
import AssetHealthSummary from '../components/executive/AssetHealthSummary';
import CriticalAlerts from '../components/executive/CriticalAlerts';
import CorrelationAnalysis from '../components/executive/CorrelationAnalysis';
import RisksOpportunities from '../components/executive/RisksOpportunities';
import ExecutiveHighlights from '../components/executive/ExecutiveHighlights';

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
      id={`dashboard-tabpanel-${index}`}
      aria-labelledby={`dashboard-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const ExecutiveDashboard: React.FC = () => {
  const { siteId } = useParams<{ siteId: string }>();
  const [tabValue, setTabValue] = useState(0);
  const [periodDays, setPeriodDays] = useState(7);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [roiData, setRoiData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      // Fetch dashboard 360° data
      const dashboardResponse = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/v1/executive/dashboard360/${siteId}`,
        { params: { period_days: periodDays }, headers }
      );

      // Fetch ROI data
      const roiResponse = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/v1/executive/roi/${siteId}`,
        { params: { period_days: periodDays }, headers }
      );

      setDashboardData(dashboardResponse.data);
      setRoiData(roiResponse.data);
      setLastUpdated(new Date());
    } catch (err: any) {
      console.error('Error fetching dashboard data:', err);
      setError(err.response?.data?.detail || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (siteId) {
      fetchDashboardData();
    }
  }, [siteId, periodDays]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handlePeriodChange = (days: number) => {
    setPeriodDays(days);
  };

  const handleDownloadReport = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/v1/executive/weekly-report/pdf/${siteId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob',
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `executive_report_${format(new Date(), 'yyyy-MM-dd')}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Error downloading report:', err);
    }
  };

  if (loading && !dashboardData) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="80vh"
      >
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error && !dashboardData) {
    return (
      <Box p={3}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      </Box>
    );
  }

  const overallHealth = dashboardData?.overall_health_score || {};
  const highlights = roiData?.highlights || [];

  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      {/* Header */}
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
        flexWrap="wrap"
        gap={2}
      >
        <Box>
          <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
            Executive Dashboard 360°
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Last updated: {format(lastUpdated, 'MMM dd, yyyy HH:mm')}
          </Typography>
        </Box>

        <Box display="flex" gap={1} alignItems="center">
          {/* Period selector */}
          <Box display="flex" gap={0.5}>
            {[7, 30, 90].map((days) => (
              <Chip
                key={days}
                label={`${days}d`}
                color={periodDays === days ? 'primary' : 'default'}
                onClick={() => handlePeriodChange(days)}
                size="small"
              />
            ))}
          </Box>

          <Tooltip title="Refresh data">
            <IconButton onClick={fetchDashboardData} size="small">
              <Refresh />
            </IconButton>
          </Tooltip>

          <Tooltip title="Download PDF Report">
            <IconButton onClick={handleDownloadReport} size="small" color="primary">
              <Download />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Executive Highlights */}
      <ExecutiveHighlights highlights={highlights} roiData={roiData} />

      {/* Overall Health Score - Hero Section */}
      <Card
        sx={{
          mb: 3,
          background: `linear-gradient(135deg, ${
            overallHealth.status === 'excellent'
              ? '#4caf50 0%, #388e3c 100%'
              : overallHealth.status === 'good'
              ? '#2196f3 0%, #1976d2 100%'
              : overallHealth.status === 'warning'
              ? '#ff9800 0%, #f57c00 100%'
              : '#f44336 0%, #d32f2f 100%'
          })`,
          color: 'white',
        }}
      >
        <CardContent>
          <OverallHealthScore
            score={overallHealth.score}
            status={overallHealth.status}
            maintenanceComponent={overallHealth.maintenance_component}
            operationsComponent={overallHealth.operations_component}
          />
        </CardContent>
      </Card>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={tabValue} onChange={handleTabChange} variant="scrollable">
          <Tab label="Overview" />
          <Tab label="ROI & Financial" />
          <Tab label="Operations" />
          <Tab label="Maintenance" />
          <Tab label="Insights" />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        {/* Overview Tab */}
        <Grid container spacing={3}>
          {/* KPIs Summary */}
          <Grid item xs={12} md={6}>
            <MaintenanceKPIs data={dashboardData?.maintenance} />
          </Grid>
          <Grid item xs={12} md={6}>
            <OperationalKPIs data={dashboardData?.operations} />
          </Grid>

          {/* Asset Health */}
          <Grid item xs={12}>
            <AssetHealthSummary data={dashboardData?.asset_health} />
          </Grid>

          {/* Critical Alerts */}
          <Grid item xs={12}>
            <CriticalAlerts alerts={dashboardData?.critical_alerts || []} />
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {/* ROI & Financial Tab */}
        <ROICalculator siteId={siteId || ''} periodDays={periodDays} roiData={roiData} />
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {/* Operations Tab */}
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <OperationalKPIs data={dashboardData?.operations} detailed />
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        {/* Maintenance Tab */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <MaintenanceKPIs data={dashboardData?.maintenance} detailed />
          </Grid>
          <Grid item xs={12} md={6}>
            <AssetHealthSummary data={dashboardData?.asset_health} detailed />
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={4}>
        {/* Insights Tab */}
        <Grid container spacing={3}>
          {/* Correlation Analysis */}
          <Grid item xs={12}>
            <CorrelationAnalysis correlations={dashboardData?.correlations || []} />
          </Grid>

          {/* Risks & Opportunities */}
          <Grid item xs={12}>
            <RisksOpportunities
              risks={dashboardData?.risks || []}
              opportunities={dashboardData?.opportunities || []}
            />
          </Grid>
        </Grid>
      </TabPanel>
    </Box>
  );
};

export default ExecutiveDashboard;
