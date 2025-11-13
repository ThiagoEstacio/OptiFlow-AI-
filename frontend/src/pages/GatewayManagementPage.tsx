/**
 * Gateway Management Page - KEPServerEX-like Interface
 * Manages industrial gateway configurations for OPC-UA, Modbus, S7, etc.
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
  Tooltip,
  Stack,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Search as SearchIcon,
  Download as DownloadIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { gatewayConfigApi } from '../api/gatewayConfig';
import type { GatewayConfigList, GatewayConfig, GatewayType } from '../types/gateway';

export const GatewayManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const [gateways, setGateways] = useState<GatewayConfigList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterEnabled, setFilterEnabled] = useState<boolean | null>(null);

  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [discoveryDialogOpen, setDiscoveryDialogOpen] = useState(false);
  const [selectedGateway, setSelectedGateway] = useState<GatewayConfigList | null>(null);

  // Discovery state
  const [discoveryLoading, setDiscoveryLoading] = useState(false);
  const [discoveryResult, setDiscoveryResult] = useState<any>(null);
  const [discoveryForm, setDiscoveryForm] = useState({
    gateway_name: '',
    endpoint: '',
    namespace_index: undefined as number | undefined,
    tag_filter: '',
    polling_interval_ms: 1000,
    description: '',
  });

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    gateway_type: 'opcua' as GatewayType,
    enabled: true,
    connection_config: {
      endpoint: '',
      security_mode: 'None',
      security_policy: 'None',
    },
    polling_interval_ms: 1000,
    description: '',
  });

  useEffect(() => {
    loadGateways();
  }, [filterType, filterEnabled]);

  const loadGateways = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: any = {};
      
      if (filterEnabled !== null) {
        params.enabled_only = filterEnabled;
      }
      
      if (filterType !== 'all') {
        params.gateway_type = filterType;
      }
      
      const data = await gatewayConfigApi.list(params);
      setGateways(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load gateways');
      console.error('Error loading gateways:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      await gatewayConfigApi.create(formData);
      setCreateDialogOpen(false);
      loadGateways();
      resetForm();
    } catch (err: any) {
      setError(err.message || 'Failed to create gateway');
    }
  };

  const handleEdit = async () => {
    if (!selectedGateway) return;
    
    try {
      await gatewayConfigApi.update(selectedGateway.id, formData);
      setEditDialogOpen(false);
      loadGateways();
      resetForm();
      setSelectedGateway(null);
    } catch (err: any) {
      setError(err.message || 'Failed to update gateway');
    }
  };

  const handleDelete = async () => {
    if (!selectedGateway) return;
    
    try {
      await gatewayConfigApi.delete(selectedGateway.id);
      setDeleteDialogOpen(false);
      loadGateways();
      setSelectedGateway(null);
    } catch (err: any) {
      setError(err.message || 'Failed to delete gateway');
    }
  };

  const handleToggleEnabled = async (gateway: GatewayConfigList) => {
    try {
      if (gateway.enabled) {
        await gatewayConfigApi.disable(gateway.id);
      } else {
        await gatewayConfigApi.enable(gateway.id);
      }
      loadGateways();
    } catch (err: any) {
      setError(err.message || 'Failed to toggle gateway status');
    }
  };

  const openEditDialog = async (gateway: GatewayConfigList) => {
    try {
      const fullGateway = await gatewayConfigApi.get(gateway.id);
      setFormData({
        name: fullGateway.name,
        gateway_type: fullGateway.gateway_type,
        enabled: fullGateway.enabled,
        connection_config: fullGateway.connection_config as any,
        polling_interval_ms: fullGateway.polling_interval_ms,
        description: fullGateway.description || '',
      });
      setSelectedGateway(gateway);
      setEditDialogOpen(true);
    } catch (err: any) {
      setError(err.message || 'Failed to load gateway details');
    }
  };

  const openDeleteDialog = (gateway: GatewayConfigList) => {
    setSelectedGateway(gateway);
    setDeleteDialogOpen(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      gateway_type: 'opcua',
      enabled: true,
      connection_config: {
        endpoint: '',
        security_mode: 'None',
        security_policy: 'None',
      },
      polling_interval_ms: 1000,
      description: '',
    });
  };

  // Discovery handlers
  const handleDiscoverTags = async () => {
    if (!discoveryForm.endpoint) {
      setError('Please enter an OPC-UA endpoint');
      return;
    }

    try {
      setDiscoveryLoading(true);
      setError(null);

      const result = await gatewayConfigApi.discoverOPCUA({
        endpoint: discoveryForm.endpoint,
        namespace_index: discoveryForm.namespace_index,
        tag_filter: discoveryForm.tag_filter || undefined,
      });

      setDiscoveryResult(result);

      if (!result.success) {
        setError(result.error || 'Discovery failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to discover tags');
    } finally {
      setDiscoveryLoading(false);
    }
  };

  const handleImportDiscovery = async () => {
    if (!discoveryForm.gateway_name || !discoveryForm.endpoint) {
      setError('Please enter gateway name and endpoint');
      return;
    }

    try {
      setLoading(true);
      await gatewayConfigApi.importOPCUA(discoveryForm);
      await loadGateways();
      setDiscoveryDialogOpen(false);
      resetDiscoveryForm();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import gateway');
    } finally {
      setLoading(false);
    }
  };

  const resetDiscoveryForm = () => {
    setDiscoveryForm({
      gateway_name: '',
      endpoint: '',
      namespace_index: undefined,
      tag_filter: '',
      polling_interval_ms: 1000,
      description: '',
    });
    setDiscoveryResult(null);
  };

  const filteredGateways = gateways.filter((gateway) =>
    gateway.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    gateway.gateway_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (gateway.description && gateway.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const getGatewayTypeColor = (type: GatewayType): "primary" | "success" | "warning" | "info" => {
    switch (type) {
      case 'opcua': return 'primary';
      case 'modbus_tcp': return 'success';
      case 'siemens_s7': return 'warning';
      case 'rockwell_eip': return 'info';
      default: return 'primary';
    }
  };

  const getGatewayTypeLabel = (type: GatewayType): string => {
    switch (type) {
      case 'opcua': return 'OPC-UA';
      case 'modbus_tcp': return 'Modbus TCP';
      case 'siemens_s7': return 'Siemens S7';
      case 'rockwell_eip': return 'Rockwell EtherNet/IP';
      default: return type;
    }
  };

  if (loading && gateways.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Gateway Management
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Configure and manage industrial protocol gateways (OPC-UA, Modbus, S7, EtherNet/IP)
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Toolbar */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
            <TextField
              size="small"
              placeholder="Search gateways..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
              sx={{ minWidth: 250 }}
            />
            
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Protocol</InputLabel>
              <Select
                value={filterType}
                label="Protocol"
                onChange={(e) => setFilterType(e.target.value)}
              >
                <MenuItem value="all">All Protocols</MenuItem>
                <MenuItem value="opcua">OPC-UA</MenuItem>
                <MenuItem value="modbus_tcp">Modbus TCP</MenuItem>
                <MenuItem value="siemens_s7">Siemens S7</MenuItem>
                <MenuItem value="rockwell_eip">Rockwell EIP</MenuItem>
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={filterEnabled === null ? 'all' : filterEnabled ? 'enabled' : 'disabled'}
                label="Status"
                onChange={(e) => {
                  const value = e.target.value;
                  setFilterEnabled(value === 'all' ? null : value === 'enabled');
                }}
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="enabled">Enabled</MenuItem>
                <MenuItem value="disabled">Disabled</MenuItem>
              </Select>
            </FormControl>

            <Box sx={{ flexGrow: 1 }} />

            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={() => setDiscoveryDialogOpen(true)}
              color="secondary"
            >
              OPC-UA Discovery
            </Button>

            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                resetForm();
                setCreateDialogOpen(true);
              }}
            >
              New Gateway
            </Button>

            <IconButton onClick={loadGateways} color="primary">
              <RefreshIcon />
            </IconButton>
          </Stack>
        </CardContent>
      </Card>

      {/* Gateway List */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Protocol</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="center">Tags</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredGateways.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 3 }}>
                    No gateways found. Click "New Gateway" to create one.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredGateways.map((gateway) => (
                <TableRow key={gateway.id} hover>
                  <TableCell>
                    <Typography
                      variant="body2"
                      fontWeight={500}
                      sx={{
                        color: 'primary.main',
                        cursor: 'pointer',
                        '&:hover': {
                          textDecoration: 'underline'
                        }
                      }}
                      onClick={() => navigate(`/gateways/${gateway.id}`)}
                    >
                      {gateway.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={getGatewayTypeLabel(gateway.gateway_type)}
                      color={getGatewayTypeColor(gateway.gateway_type)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      icon={gateway.enabled ? <CheckCircleIcon /> : <CancelIcon />}
                      label={gateway.enabled ? 'Enabled' : 'Disabled'}
                      color={gateway.enabled ? 'success' : 'default'}
                      size="small"
                      onClick={() => handleToggleEnabled(gateway)}
                      sx={{ cursor: 'pointer' }}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Chip label={gateway.tags_count} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary" noWrap sx={{ maxWidth: 200 }}>
                      {gateway.description || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {new Date(gateway.created_at).toLocaleDateString()}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => navigate(`/gateways/${gateway.id}`)}
                        color="primary"
                      >
                        <VisibilityIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit">
                      <IconButton
                        size="small"
                        onClick={() => openEditDialog(gateway)}
                        color="primary"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton
                        size="small"
                        onClick={() => openDeleteDialog(gateway)}
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create/Edit Dialog */}
      <Dialog
        open={createDialogOpen || editDialogOpen}
        onClose={() => {
          setCreateDialogOpen(false);
          setEditDialogOpen(false);
          resetForm();
        }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {createDialogOpen ? 'Create New Gateway' : 'Edit Gateway'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="Gateway Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              fullWidth
            />

            <FormControl fullWidth required>
              <InputLabel>Protocol Type</InputLabel>
              <Select
                value={formData.gateway_type}
                label="Protocol Type"
                onChange={(e) => setFormData({ ...formData, gateway_type: e.target.value as GatewayType })}
              >
                <MenuItem value="opcua">OPC-UA</MenuItem>
                <MenuItem value="modbus_tcp">Modbus TCP</MenuItem>
                <MenuItem value="siemens_s7">Siemens S7</MenuItem>
                <MenuItem value="rockwell_eip">Rockwell EtherNet/IP</MenuItem>
              </Select>
            </FormControl>

            {formData.gateway_type === 'opcua' && (
              <TextField
                label="OPC-UA Endpoint"
                value={formData.connection_config.endpoint}
                onChange={(e) => setFormData({
                  ...formData,
                  connection_config: { ...formData.connection_config, endpoint: e.target.value }
                })}
                placeholder="opc.tcp://localhost:4840"
                required
                fullWidth
              />
            )}

            <TextField
              label="Polling Interval (ms)"
              type="number"
              value={formData.polling_interval_ms}
              onChange={(e) => setFormData({ ...formData, polling_interval_ms: parseInt(e.target.value) })}
              required
              fullWidth
            />

            <TextField
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              multiline
              rows={3}
              fullWidth
            />

            <FormControlLabel
              control={
                <Switch
                  checked={formData.enabled}
                  onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                />
              }
              label="Enabled"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setCreateDialogOpen(false);
            setEditDialogOpen(false);
            resetForm();
          }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={createDialogOpen ? handleCreate : handleEdit}
          >
            {createDialogOpen ? 'Create' : 'Update'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete gateway "{selectedGateway?.name}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDelete}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* OPC-UA Discovery Dialog */}
      <Dialog
        open={discoveryDialogOpen}
        onClose={() => {
          setDiscoveryDialogOpen(false);
          resetDiscoveryForm();
        }}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>OPC-UA Tag Discovery & Import</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            {/* Step 1: Connection Details */}
            <Typography variant="h6">Step 1: Server Connection</Typography>
            <TextField
              label="OPC-UA Endpoint"
              value={discoveryForm.endpoint}
              onChange={(e) => setDiscoveryForm({ ...discoveryForm, endpoint: e.target.value })}
              placeholder="opc.tcp://localhost:4840"
              required
              fullWidth
            />

            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                <TextField
                  label="Namespace Index (optional)"
                  type="number"
                  value={discoveryForm.namespace_index || ''}
                  onChange={(e) => setDiscoveryForm({
                    ...discoveryForm,
                    namespace_index: e.target.value ? parseInt(e.target.value) : undefined
                  })}
                  fullWidth
                />
              </Box>
              <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                <TextField
                  label="Tag Filter (optional)"
                  value={discoveryForm.tag_filter}
                  onChange={(e) => setDiscoveryForm({ ...discoveryForm, tag_filter: e.target.value })}
                  placeholder="CORR, TEMP, etc."
                  fullWidth
                />
              </Box>
            </Box>

            <Button
              variant="contained"
              onClick={handleDiscoverTags}
              disabled={discoveryLoading || !discoveryForm.endpoint}
              startIcon={discoveryLoading ? <CircularProgress size={20} /> : <SearchIcon />}
            >
              {discoveryLoading ? 'Discovering...' : 'Discover Tags'}
            </Button>

            {/* Step 2: Discovery Results */}
            {discoveryResult && (
              <>
                <Typography variant="h6" sx={{ mt: 2 }}>
                  Step 2: Discovery Results
                </Typography>

                {discoveryResult.success ? (
                  <>
                    <Alert severity="success">
                      Successfully discovered {discoveryResult.tag_count} tags from {discoveryResult.endpoint}
                    </Alert>

                    {discoveryResult.namespaces && discoveryResult.namespaces.length > 0 && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Available Namespaces:
                        </Typography>
                        {discoveryResult.namespaces.map((ns: any) => (
                          <Chip
                            key={ns.index}
                            label={`${ns.index}: ${ns.uri}`}
                            size="small"
                            sx={{ mr: 1, mb: 1 }}
                          />
                        ))}
                      </Box>
                    )}

                    <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 300 }}>
                      <Table size="small" stickyHeader>
                        <TableHead>
                          <TableRow>
                            <TableCell>Tag Name</TableCell>
                            <TableCell>Display Name</TableCell>
                            <TableCell>Address</TableCell>
                            <TableCell>Data Type</TableCell>
                            <TableCell>Readable</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {discoveryResult.tags.slice(0, 50).map((tag: any, index: number) => (
                            <TableRow key={index}>
                              <TableCell>{tag.tag_name}</TableCell>
                              <TableCell>{tag.display_name}</TableCell>
                              <TableCell>
                                <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                                  {tag.address}
                                </Typography>
                              </TableCell>
                              <TableCell>{tag.data_type || '-'}</TableCell>
                              <TableCell>
                                {tag.readable ? (
                                  <CheckCircleIcon color="success" fontSize="small" />
                                ) : (
                                  <CancelIcon color="disabled" fontSize="small" />
                                )}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>

                    {discoveryResult.tags.length > 50 && (
                      <Typography variant="body2" color="text.secondary">
                        Showing 50 of {discoveryResult.tag_count} tags. All tags will be imported.
                      </Typography>
                    )}

                    {/* Step 3: Gateway Configuration */}
                    <Typography variant="h6" sx={{ mt: 2 }}>
                      Step 3: Gateway Configuration
                    </Typography>

                    <TextField
                      label="Gateway Name"
                      value={discoveryForm.gateway_name}
                      onChange={(e) => setDiscoveryForm({ ...discoveryForm, gateway_name: e.target.value })}
                      required
                      fullWidth
                    />

                    <TextField
                      label="Polling Interval (ms)"
                      type="number"
                      value={discoveryForm.polling_interval_ms}
                      onChange={(e) => setDiscoveryForm({
                        ...discoveryForm,
                        polling_interval_ms: parseInt(e.target.value)
                      })}
                      fullWidth
                    />

                    <TextField
                      label="Description (optional)"
                      value={discoveryForm.description}
                      onChange={(e) => setDiscoveryForm({ ...discoveryForm, description: e.target.value })}
                      multiline
                      rows={2}
                      fullWidth
                    />
                  </>
                ) : (
                  <Alert severity="error">
                    {discoveryResult.error || 'Discovery failed'}
                  </Alert>
                )}
              </>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setDiscoveryDialogOpen(false);
              resetDiscoveryForm();
            }}
          >
            Cancel
          </Button>
          {discoveryResult?.success && (
            <Button
              variant="contained"
              onClick={handleImportDiscovery}
              disabled={!discoveryForm.gateway_name || loading}
              startIcon={loading ? <CircularProgress size={20} /> : <DownloadIcon />}
            >
              {loading ? 'Importing...' : `Import Gateway with ${discoveryResult.tag_count} Tags`}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};
