/**
 * Gateway Details Page - View and manage gateway configuration and tags
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  Alert,
  CircularProgress,
  Toolbar,
  Tooltip,
  Card,
  CardContent,
  Divider,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { gatewayConfigApi } from '../api/gatewayConfig';
import type { GatewayConfig, GatewayTag, GatewayTagCreate } from '../types/gateway';

export const GatewayDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [gateway, setGateway] = useState<GatewayConfig | null>(null);
  const [tags, setTags] = useState<GatewayTag[]>([]);
  const [tagValues, setTagValues] = useState<Record<number, any>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tag dialog state
  const [tagDialogOpen, setTagDialogOpen] = useState(false);
  const [editingTag, setEditingTag] = useState<GatewayTag | null>(null);
  const [deleteTagDialogOpen, setDeleteTagDialogOpen] = useState(false);
  const [tagToDelete, setTagToDelete] = useState<GatewayTag | null>(null);

  // Tag form state
  const [tagForm, setTagForm] = useState<Partial<GatewayTagCreate>>({
    tag_name: '',
    enabled: true,
    address_config: {},
    data_type: 'float',
    scale_factor: 1.0,
    offset: 0.0,
    unit: '',
    description: '',
  });

  // Load gateway and tags
  const loadGateway = async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);
      const gatewayData = await gatewayConfigApi.get(parseInt(id));
      setGateway(gatewayData);
      setTags(gatewayData.tags || []);

      // Load current values for tags
      loadTagValues(gatewayData.tags || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load gateway configuration');
    } finally {
      setLoading(false);
    }
  };

  // Load current values for all tags
  const loadTagValues = async (tagsToLoad: GatewayTag[]) => {
    if (tagsToLoad.length === 0) return;

    try {
      // Use WebSocket to get real-time values
      const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const wsUrl = BASE_URL.replace('http', 'ws') + '/ws/tags';

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        // Subscribe to all tags
        const tagIds = tagsToLoad.map(t => t.id);
        ws.send(JSON.stringify({
          action: 'subscribe',
          tag_ids: tagIds
        }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.tag_id && data.value !== undefined) {
            setTagValues(prev => ({
              ...prev,
              [data.tag_id]: {
                value: data.value,
                timestamp: data.timestamp,
                quality: data.quality
              }
            }));
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        // Fallback: try to get values from REST API
        loadTagValuesFromAPI(tagsToLoad);
      };

      // Clean up WebSocket on unmount
      return () => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      };
    } catch (err) {
      console.error('Failed to connect to WebSocket:', err);
      loadTagValuesFromAPI(tagsToLoad);
    }
  };

  // Fallback: Load tag values from REST API
  const loadTagValuesFromAPI = async (tagsToLoad: GatewayTag[]) => {
    const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('auth_token');

    for (const tag of tagsToLoad.slice(0, 10)) { // Load first 10 for performance
      try {
        const response = await fetch(`${BASE_URL}/api/v1/tags/${tag.id}/latest`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });

        if (response.ok) {
          const data = await response.json();
          setTagValues(prev => ({
            ...prev,
            [tag.id]: {
              value: data.value,
              timestamp: data.timestamp,
              quality: data.quality
            }
          }));
        }
      } catch (err) {
        console.error(`Failed to load value for tag ${tag.id}:`, err);
      }
    }
  };

  useEffect(() => {
    loadGateway();
  }, [id]);

  // Handle tag create/edit
  const handleOpenTagDialog = (tag?: GatewayTag) => {
    if (tag) {
      setEditingTag(tag);
      setTagForm({
        tag_name: tag.tag_name,
        enabled: tag.enabled,
        address_config: tag.address_config,
        data_type: tag.data_type,
        scale_factor: tag.scale_factor,
        offset: tag.offset,
        unit: tag.unit || '',
        description: tag.description || '',
      });
    } else {
      setEditingTag(null);
      setTagForm({
        tag_name: '',
        enabled: true,
        address_config: {},
        data_type: 'float',
        scale_factor: 1.0,
        offset: 0.0,
        unit: '',
        description: '',
      });
    }
    setTagDialogOpen(true);
  };

  const handleCloseTagDialog = () => {
    setTagDialogOpen(false);
    setEditingTag(null);
  };

  const handleSaveTag = async () => {
    if (!id || !tagForm.tag_name) return;

    try {
      setLoading(true);

      if (editingTag) {
        // Update existing tag
        await gatewayConfigApi.tags.update(
          parseInt(id),
          editingTag.id,
          tagForm
        );
      } else {
        // Create new tag
        await gatewayConfigApi.tags.create(parseInt(id), tagForm);
      }

      await loadGateway();
      handleCloseTagDialog();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save tag');
    } finally {
      setLoading(false);
    }
  };

  // Handle tag delete
  const handleOpenDeleteTagDialog = (tag: GatewayTag) => {
    setTagToDelete(tag);
    setDeleteTagDialogOpen(true);
  };

  const handleCloseDeleteTagDialog = () => {
    setDeleteTagDialogOpen(false);
    setTagToDelete(null);
  };

  const handleDeleteTag = async () => {
    if (!id || !tagToDelete) return;

    try {
      setLoading(true);
      await gatewayConfigApi.tags.delete(parseInt(id), tagToDelete.id);
      await loadGateway();
      handleCloseDeleteTagDialog();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete tag');
    } finally {
      setLoading(false);
    }
  };

  // Helper to format address config
  const formatAddressConfig = (config: Record<string, any>): string => {
    if (!config || Object.keys(config).length === 0) return '-';
    return Object.entries(config)
      .map(([key, value]) => `${key}: ${value}`)
      .join(', ');
  };

  if (loading && !gateway) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error && !gateway) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/gateways')} sx={{ mt: 2 }}>
          Back to Gateways
        </Button>
      </Box>
    );
  }

  if (!gateway) return null;

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" alignItems="center" mb={3}>
        <IconButton onClick={() => navigate('/gateways')} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4" flexGrow={1}>
          {gateway.name}
        </Typography>
        <Button
          startIcon={<RefreshIcon />}
          onClick={loadGateway}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Gateway Info Cards */}
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 3 }}>
        <Box sx={{ flex: '1 1 calc(50% - 12px)', minWidth: 300 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Configuration
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Box display="flex" flexDirection="column" gap={1}>
                <Box display="flex" justifyContent="space-between">
                  <Typography color="text.secondary">Protocol:</Typography>
                  <Typography fontWeight="medium">{gateway.gateway_type.toUpperCase()}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography color="text.secondary">Status:</Typography>
                  <Chip
                    label={gateway.enabled ? 'Enabled' : 'Disabled'}
                    color={gateway.enabled ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography color="text.secondary">Polling Interval:</Typography>
                  <Typography>{gateway.polling_interval_ms} ms</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography color="text.secondary">Max Retries:</Typography>
                  <Typography>{gateway.max_retries}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography color="text.secondary">Created:</Typography>
                  <Typography>{new Date(gateway.created_at).toLocaleString()}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: '1 1 calc(50% - 12px)', minWidth: 300 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Connection
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Box display="flex" flexDirection="column" gap={1}>
                {Object.entries(gateway.connection_config).map(([key, value]) => (
                  <Box key={key} display="flex" justifyContent="space-between">
                    <Typography color="text.secondary">{key}:</Typography>
                    <Typography fontWeight="medium" sx={{ wordBreak: 'break-all', maxWidth: '60%', textAlign: 'right' }}>
                      {String(value)}
                    </Typography>
                  </Box>
                ))}
              </Box>
              {gateway.description && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="body2" color="text.secondary">
                    {gateway.description}
                  </Typography>
                </>
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Tags Section */}
      <Paper sx={{ p: 2 }}>
        <Toolbar sx={{ px: { xs: 0 } }}>
          <Typography variant="h6" flexGrow={1}>
            Tags ({tags.length})
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenTagDialog()}
          >
            Add Tag
          </Button>
        </Toolbar>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Tag Name</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Valor Atual</TableCell>
                <TableCell>Address</TableCell>
                <TableCell>Data Type</TableCell>
                <TableCell>Scale/Offset</TableCell>
                <TableCell>Unit</TableCell>
                <TableCell>Description</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tags.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center">
                    <Typography color="text.secondary" py={3}>
                      No tags configured. Click "Add Tag" to create one.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                tags.map((tag) => {
                  const currentValue = tagValues[tag.id];
                  return (
                  <TableRow key={tag.id}>
                    <TableCell>
                      <Typography fontWeight="medium">{tag.tag_name}</Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={tag.enabled ? 'Enabled' : 'Disabled'}
                        color={tag.enabled ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {currentValue ? (
                        <Box>
                          <Typography variant="body2" fontWeight="medium" color="primary">
                            {typeof currentValue.value === 'number'
                              ? currentValue.value.toFixed(2)
                              : String(currentValue.value)}
                          </Typography>
                          {currentValue.timestamp && (
                            <Typography variant="caption" color="text.secondary">
                              {new Date(currentValue.timestamp).toLocaleTimeString()}
                            </Typography>
                          )}
                        </Box>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          ...
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {formatAddressConfig(tag.address_config)}
                      </Typography>
                    </TableCell>
                    <TableCell>{tag.data_type}</TableCell>
                    <TableCell>
                      {tag.scale_factor !== 1.0 || tag.offset !== 0.0 ? (
                        <Typography variant="body2">
                          ×{tag.scale_factor} + {tag.offset}
                        </Typography>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>{tag.unit || '-'}</TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary" noWrap sx={{ maxWidth: 200 }}>
                        {tag.description || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Edit">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenTagDialog(tag)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleOpenDeleteTagDialog(tag)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Tag Create/Edit Dialog */}
      <Dialog open={tagDialogOpen} onClose={handleCloseTagDialog} maxWidth="md" fullWidth>
        <DialogTitle>{editingTag ? 'Edit Tag' : 'Create New Tag'}</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} pt={1}>
            <TextField
              label="Tag Name"
              value={tagForm.tag_name}
              onChange={(e) => setTagForm({ ...tagForm, tag_name: e.target.value })}
              required
              fullWidth
            />

            <FormControlLabel
              control={
                <Switch
                  checked={tagForm.enabled}
                  onChange={(e) => setTagForm({ ...tagForm, enabled: e.target.checked })}
                />
              }
              label="Enabled"
            />

            <TextField
              label="Address Configuration (JSON)"
              value={JSON.stringify(tagForm.address_config || {}, null, 2)}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value);
                  setTagForm({ ...tagForm, address_config: parsed });
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              multiline
              rows={3}
              placeholder='{"node_id": "ns=2;s=Machine1.Temperature"}'
              helperText="Enter protocol-specific address configuration as JSON"
              fullWidth
            />

            <TextField
              label="Data Type"
              value={tagForm.data_type}
              onChange={(e) => setTagForm({ ...tagForm, data_type: e.target.value })}
              select
              SelectProps={{ native: true }}
              fullWidth
            >
              <option value="float">Float</option>
              <option value="int">Integer</option>
              <option value="bool">Boolean</option>
              <option value="string">String</option>
            </TextField>

            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 200 }}>
                <TextField
                  label="Scale Factor"
                  type="number"
                  value={tagForm.scale_factor}
                  onChange={(e) => setTagForm({ ...tagForm, scale_factor: parseFloat(e.target.value) })}
                  inputProps={{ step: 0.1 }}
                  fullWidth
                />
              </Box>
              <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 200 }}>
                <TextField
                  label="Offset"
                  type="number"
                  value={tagForm.offset}
                  onChange={(e) => setTagForm({ ...tagForm, offset: parseFloat(e.target.value) })}
                  inputProps={{ step: 0.1 }}
                  fullWidth
                />
              </Box>
            </Box>

            <TextField
              label="Unit"
              value={tagForm.unit}
              onChange={(e) => setTagForm({ ...tagForm, unit: e.target.value })}
              placeholder="°C, bar, RPM, etc."
              fullWidth
            />

            <TextField
              label="Description"
              value={tagForm.description}
              onChange={(e) => setTagForm({ ...tagForm, description: e.target.value })}
              multiline
              rows={2}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseTagDialog}>Cancel</Button>
          <Button
            onClick={handleSaveTag}
            variant="contained"
            disabled={!tagForm.tag_name}
          >
            {editingTag ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Tag Confirmation Dialog */}
      <Dialog open={deleteTagDialogOpen} onClose={handleCloseDeleteTagDialog}>
        <DialogTitle>Delete Tag</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the tag "{tagToDelete?.tag_name}"?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteTagDialog}>Cancel</Button>
          <Button onClick={handleDeleteTag} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
