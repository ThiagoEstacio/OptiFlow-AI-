import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import axios from 'axios';

interface DataSourcesTabProps {
  siteId: number;
  dataSources: any[];
  onDataSourcesChange: () => void;
}

const DataSourcesTab: React.FC<DataSourcesTabProps> = ({
  siteId,
  dataSources,
  onDataSourcesChange,
}) => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState<any>({
    name: '',
    source_type: 'excel',
    api_url: '',
    auth_type: 'none',
    data_format: 'json',
    notes: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (field: string, value: any) => {
    setFormData({ ...formData, [field]: value });
  };

  const handleSubmit = async () => {
    if (!formData.name || !formData.source_type) {
      setError('Please fill in required fields');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      await axios.post(
        `${import.meta.env.VITE_API_URL}/api/v1/gbm/data-sources/`,
        { ...formData, site_id: siteId },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      setDialogOpen(false);
      setFormData({
        name: '',
        source_type: 'excel',
        api_url: '',
        auth_type: 'none',
        data_format: 'json',
        notes: '',
      });
      onDataSourcesChange();
    } catch (err: any) {
      console.error('Error creating data source:', err);
      setError(err.response?.data?.detail || 'Failed to create data source');
    } finally {
      setSaving(false);
    }
  };

  const getSourceTypeColor = (type: string) => {
    switch (type) {
      case 'api':
        return 'primary';
      case 'excel':
      case 'csv':
        return 'success';
      case 'manual':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Data Sources</Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setDialogOpen(true)}
            >
              Add Data Source
            </Button>
          </Box>

          <Typography variant="body2" color="text.secondary" paragraph>
            Configure data sources for importing GBM Logística and other operational data
          </Typography>

          {dataSources.length === 0 ? (
            <Alert severity="info">
              No data sources configured. Click "Add Data Source" to create one.
            </Alert>
          ) : (
            <List>
              {dataSources.map((ds) => (
                <ListItem key={ds.id} divider>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1}>
                        {ds.name}
                        <Chip
                          label={ds.source_type}
                          size="small"
                          color={getSourceTypeColor(ds.source_type)}
                        />
                        {ds.enabled ? (
                          <Chip label="Enabled" size="small" color="success" />
                        ) : (
                          <Chip label="Disabled" size="small" color="default" />
                        )}
                      </Box>
                    }
                    secondary={
                      <Box>
                        {ds.api_url && (
                          <Typography variant="body2">{ds.api_url}</Typography>
                        )}
                        {ds.notes && (
                          <Typography variant="body2" color="text.secondary">
                            {ds.notes}
                          </Typography>
                        )}
                        <Typography variant="caption" color="text.secondary">
                          Created: {new Date(ds.created_at).toLocaleDateString()}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add Data Source</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              fullWidth
              required
              label="Name"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              placeholder="GBM Logística Production"
            />

            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '250px' }}>
                <FormControl fullWidth required>
                  <InputLabel>Source Type</InputLabel>
                  <Select
                    value={formData.source_type}
                    onChange={(e) => handleChange('source_type', e.target.value)}
                    label="Source Type"
                  >
                    <MenuItem value="excel">Excel/CSV Upload</MenuItem>
                    <MenuItem value="api">API Integration</MenuItem>
                    <MenuItem value="manual">Manual Entry</MenuItem>
                  </Select>
                </FormControl>
              </Box>

              <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '250px' }}>
                <FormControl fullWidth>
                  <InputLabel>Data Format</InputLabel>
                  <Select
                    value={formData.data_format}
                    onChange={(e) => handleChange('data_format', e.target.value)}
                    label="Data Format"
                  >
                    <MenuItem value="json">JSON</MenuItem>
                    <MenuItem value="xml">XML</MenuItem>
                    <MenuItem value="csv">CSV</MenuItem>
                    <MenuItem value="excel">Excel</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            </Box>

            {formData.source_type === 'api' && (
              <>
                <TextField
                  fullWidth
                  label="API URL"
                  value={formData.api_url}
                  onChange={(e) => handleChange('api_url', e.target.value)}
                  placeholder="https://api.gbmlogistica.com.br/v1/operations"
                />

                <FormControl fullWidth>
                  <InputLabel>Auth Type</InputLabel>
                  <Select
                    value={formData.auth_type}
                    onChange={(e) => handleChange('auth_type', e.target.value)}
                    label="Auth Type"
                  >
                    <MenuItem value="none">None</MenuItem>
                    <MenuItem value="bearer">Bearer Token</MenuItem>
                    <MenuItem value="api_key">API Key</MenuItem>
                    <MenuItem value="basic">Basic Auth</MenuItem>
                  </Select>
                </FormControl>
              </>
            )}

            <TextField
              fullWidth
              multiline
              rows={3}
              label="Notes"
              value={formData.notes}
              onChange={(e) => handleChange('notes', e.target.value)}
              placeholder="Additional information about this data source"
            />

            {error && (
              <Alert severity="error">{error}</Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained" disabled={saving}>
            {saving ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DataSourcesTab;
