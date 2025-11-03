import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Tabs,
  Tab,
  Paper,
  Alert,
  CircularProgress,
} from '@mui/material';
import axios from 'axios';

// Import components
import ExcelImportTab from '../components/gbm/ExcelImportTab';
import ManualEntryTab from '../components/gbm/ManualEntryTab';
import ApiIntegrationTab from '../components/gbm/ApiIntegrationTab';
import ImportHistoryTab from '../components/gbm/ImportHistoryTab';
import DataSourcesTab from '../components/gbm/DataSourcesTab';

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
      id={`gbm-tabpanel-${index}`}
      aria-labelledby={`gbm-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const GBMDataImport: React.FC = () => {
  const { siteId } = useParams<{ siteId: string }>();
  const [tabValue, setTabValue] = useState(0);
  const [dataSources, setDataSources] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const fetchDataSources = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/v1/gbm/data-sources/${siteId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setDataSources(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching data sources:', err);
      setError(err.response?.data?.detail || 'Failed to load data sources');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDataSources();
  }, [siteId]);

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="60vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            GBM Logistics Data Import
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Import operational data from GBM Logística and other sources via Excel, API, or manual entry
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Tabs */}
        <Paper sx={{ mb: 3 }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label="📊 Excel/CSV Import" />
            <Tab label="✍️ Manual Entry" />
            <Tab label="🔗 API Integration" />
            <Tab label="📋 Import History" />
            <Tab label="⚙️ Data Sources" />
          </Tabs>
        </Paper>

        {/* Tab Panels */}
        <TabPanel value={tabValue} index={0}>
          <ExcelImportTab
            siteId={parseInt(siteId!)}
            dataSources={dataSources}
            onImportComplete={fetchDataSources}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <ManualEntryTab
            siteId={parseInt(siteId!)}
            dataSources={dataSources}
            onEntryComplete={fetchDataSources}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <ApiIntegrationTab
            siteId={parseInt(siteId!)}
            dataSources={dataSources}
            onSyncComplete={fetchDataSources}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <ImportHistoryTab siteId={parseInt(siteId!)} />
        </TabPanel>

        <TabPanel value={tabValue} index={4}>
          <DataSourcesTab
            siteId={parseInt(siteId!)}
            dataSources={dataSources}
            onDataSourcesChange={fetchDataSources}
          />
        </TabPanel>
      </Box>
    </Container>
  );
};

export default GBMDataImport;
