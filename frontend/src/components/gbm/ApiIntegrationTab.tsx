import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  CircularProgress,
} from '@mui/material';
import { Sync as SyncIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import axios from 'axios';

interface ApiIntegrationTabProps {
  siteId: number;
  dataSources: any[];
  onSyncComplete: () => void;
}

const ApiIntegrationTab: React.FC<ApiIntegrationTabProps> = ({
  siteId,
  dataSources,
  onSyncComplete,
}) => {
  const [syncing, setSyncing] = useState<{ [key: number]: boolean }>({});
  const [syncResults, setSyncResults] = useState<{ [key: number]: any }>({});
  const [error, setError] = useState<string | null>(null);

  const handleSync = async (dataSourceId: number) => {
    setSyncing({ ...syncing, [dataSourceId]: true });
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/api/v1/gbm/sync/${siteId}/${dataSourceId}`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      setSyncResults({ ...syncResults, [dataSourceId]: response.data });
      onSyncComplete();
    } catch (err: any) {
      console.error('Sync error:', err);
      setError(err.response?.data?.detail || 'Sync failed');
    } finally {
      setSyncing({ ...syncing, [dataSourceId]: false });
    }
  };

  const apiDataSources = dataSources.filter((ds) => ds.source_type === 'api');

  if (apiDataSources.length === 0) {
    return (
      <Card>
        <CardContent>
          <Alert severity="info">
            No API data sources configured. Go to the "Data Sources" tab to create one.
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            API Integration
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Sync data from external APIs (GBM Logística, custom APIs, etc.)
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <List>
            {apiDataSources.map((ds) => (
              <ListItem key={ds.id} divider>
                <ListItemText
                  primary={ds.name}
                  secondary={
                    <Box>
                      <Typography variant="body2" component="span">
                        {ds.api_url}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        {ds.last_sync_at && (
                          <Chip
                            size="small"
                            label={`Last sync: ${new Date(ds.last_sync_at).toLocaleString()}`}
                            sx={{ mr: 1 }}
                          />
                        )}
                        {ds.last_sync_status && (
                          <Chip
                            size="small"
                            label={ds.last_sync_status}
                            color={ds.last_sync_status === 'success' ? 'success' : 'error'}
                          />
                        )}
                      </Box>
                      {syncResults[ds.id] && (
                        <Alert severity="success" sx={{ mt: 1 }}>
                          Imported {syncResults[ds.id].records_imported} records
                        </Alert>
                      )}
                    </Box>
                  }
                />
                <ListItemSecondaryAction>
                  <Button
                    variant="contained"
                    onClick={() => handleSync(ds.id)}
                    disabled={syncing[ds.id]}
                    startIcon={
                      syncing[ds.id] ? <CircularProgress size={20} /> : <SyncIcon />
                    }
                  >
                    {syncing[ds.id] ? 'Syncing...' : 'Sync Now'}
                  </Button>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ApiIntegrationTab;
