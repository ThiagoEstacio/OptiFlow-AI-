/**
 * Tags Management Page - PI Asset Framework Style
 * Optimized interface with tabs for Tags, Formulas, and Advanced Features
 */
import React, { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import { fetchTags, createTag, updateTag, deleteTag } from '../store/slices/tagsSlice';
import { fetchDevices } from '../store/slices/devicesSlice';
import { Modal } from '../components/Modal/Modal';
import { ConfirmDialog } from '../components/Modal/ConfirmDialog';
import { TagForm } from '../components/Forms/TagForm';
import { Tag } from '../types';
import { showToast } from '../utils/toast';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  Tooltip,
  Tabs,
  Tab,
  Card,
  CardContent,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Stack,
  Switch
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Refresh as RefreshIcon,
  AccountTree as TreeIcon,
  CloudDownload as ArchiveIcon,
  Functions as FormulaIcon,
  Storage as DataIcon,
  Settings as SettingsIcon,
  TrendingUp as TrendingUpIcon,
  Code as CodeIcon,
  ContentCopy as ContentCopyIcon
} from '@mui/icons-material';
import { AssetTreeView } from '../components/ExtendedTags/AssetTreeView';
import { TagBulkImport } from '../components/ExtendedTags/TagBulkImport';

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
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export const TagsPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { items: tags, loading } = useAppSelector((state) => state.tags);
  const { items: devices } = useAppSelector((state) => state.devices);

  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isBulkImportOpen, setIsBulkImportOpen] = useState(false);
  const [isFormulaModalOpen, setIsFormulaModalOpen] = useState(false);
  const [isArchivingModalOpen, setIsArchivingModalOpen] = useState(false);
  const [selectedTag, setSelectedTag] = useState<Tag | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // View state
  const [activeTab, setActiveTab] = useState(0);
  const [showTreeView, setShowTreeView] = useState(false);

  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [filterDevice, setFilterDevice] = useState<string>('');
  const [filterDataType, setFilterDataType] = useState<string>('');
  const [filterEnabled, setFilterEnabled] = useState<string>('all');
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Formulas state (mock data for now)
  const [formulas, setFormulas] = useState<any[]>([
    { id: '1', name: 'Eficiência Total', expression: '(Produção / Tempo) * 100', unit: '%', tags: ['PROD_01', 'TIME_01'] },
    { id: '2', name: 'Consumo Específico', expression: 'Energia / Produção', unit: 'kWh/ton', tags: ['ENERGY_01', 'PROD_01'] }
  ]);

  useEffect(() => {
    dispatch(fetchTags({}));
    dispatch(fetchDevices({}));
  }, [dispatch]);

  const handleCreate = async (data: any) => {
    setIsSubmitting(true);
    try {
      await dispatch(createTag(data)).unwrap();
      showToast.success('Tag criado com sucesso!');
      setIsCreateModalOpen(false);
      dispatch(fetchTags({}));
    } catch (error: any) {
      showToast.error(error.message || 'Erro ao criar tag');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = async (data: any) => {
    if (!selectedTag) return;
    setIsSubmitting(true);
    try {
      await dispatch(updateTag({ id: selectedTag.id, data })).unwrap();
      showToast.success('Tag atualizado com sucesso!');
      setIsEditModalOpen(false);
      setSelectedTag(null);
      dispatch(fetchTags({}));
    } catch (error: any) {
      showToast.error(error.message || 'Erro ao atualizar tag');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedTag) return;
    setIsSubmitting(true);
    try {
      await dispatch(deleteTag(selectedTag.id)).unwrap();
      showToast.success('Tag excluído com sucesso!');
      setIsDeleteDialogOpen(false);
      setSelectedTag(null);
      dispatch(fetchTags({}));
    } catch (error: any) {
      showToast.error(error.message || 'Erro ao excluir tag');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openEditModal = (tag: Tag) => {
    setSelectedTag(tag);
    setIsEditModalOpen(true);
  };

  const openDeleteDialog = (tag: Tag) => {
    setSelectedTag(tag);
    setIsDeleteDialogOpen(true);
  };

  const getDeviceName = (deviceId: string) => {
    return devices.find((d) => d.id === deviceId)?.name || deviceId;
  };

  const handleBulkImport = async (importRequest: any) => {
    try {
      showToast.success(`Importando ${importRequest.tags.length} tags...`);
      setTimeout(() => {
        dispatch(fetchTags({}));
      }, 1000);
    } catch (error: any) {
      throw error;
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await dispatch(fetchTags({})).unwrap();
      setLastRefresh(new Date());
      showToast.success('Tags atualizados!');
    } catch (error) {
      showToast.error('Erro ao atualizar tags');
    } finally {
      setTimeout(() => setIsRefreshing(false), 500);
    }
  };

  const handleExportFiltered = () => {
    const filtered = filteredTags;
    if (filtered.length === 0) {
      showToast.error('Nenhum tag para exportar');
      return;
    }

    const csvHeaders = ['ID', 'Name', 'Device', 'Data Type', 'Unit', 'Last Value', 'Last Update', 'Enabled'];
    const csvRows = filtered.map(tag => [
      tag.id,
      tag.name,
      tag.device_id,
      tag.data_type,
      tag.unit || '',
      tag.last_value ?? 'N/A',
      tag.last_timestamp ? new Date(tag.last_timestamp).toISOString() : 'N/A',
      tag.enabled ? 'Yes' : 'No'
    ]);

    const csv = [csvHeaders, ...csvRows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tags_export_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showToast.success(`${filtered.length} tags exportados!`);
  };

  const handleCopyTagId = async (tagId: string) => {
    try {
      await navigator.clipboard.writeText(tagId);
      showToast.success('Tag ID copiado!');
    } catch (error) {
      console.error('Error copying tag ID:', error);
      showToast.error('Falha ao copiar Tag ID');
    }
  };

  const getTagsWithRecentData = () => {
    return tags.filter(tag => {
      if (!tag.last_timestamp) return false;
      const lastUpdate = new Date(tag.last_timestamp);
      const now = new Date();
      const diffMinutes = (now.getTime() - lastUpdate.getTime()) / (1000 * 60);
      return diffMinutes < 5; // Data from last 5 minutes
    }).length;
  };

  const handleDownloadTemplate = () => {
    const template = `name,address,device_id,data_type,unit,description,enabled,log_enabled
TEMP_01,ns=2;s=Temperature,${devices[0]?.id || ''},FLOAT,°C,Temperature sensor,true,true
PRESS_01,ns=2;s=Pressure,${devices[0]?.id || ''},FLOAT,bar,Pressure sensor,true,true`;

    const blob = new Blob([template], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'tags_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredTags = tags.filter((tag) => {
    const matchesSearch =
      tag.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tag.address.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (tag.description && tag.description.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesDevice = !filterDevice || tag.device_id === filterDevice;
    const matchesDataType = !filterDataType || tag.data_type === filterDataType;
    const matchesEnabled =
      filterEnabled === 'all' ||
      (filterEnabled === 'enabled' && tag.enabled) ||
      (filterEnabled === 'disabled' && !tag.enabled);

    return matchesSearch && matchesDevice && matchesDataType && matchesEnabled;
  });

  // Stats
  const stats = {
    total: tags.length,
    enabled: tags.filter((t) => t.enabled).length,
    disabled: tags.filter((t) => !t.enabled).length,
    logging: tags.filter((t) => t.log_enabled).length,
    formulas: formulas.length
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h4" fontWeight="bold" gutterBottom>
              Tags & Fórmulas PI AF
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Gerenciamento completo de tags, fórmulas calculadas e arquivamento histórico
            </Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            <Tooltip title={`Última atualização: ${lastRefresh.toLocaleTimeString()}`}>
              <IconButton 
                onClick={handleRefresh} 
                color="primary" 
                size="large"
                disabled={isRefreshing}
              >
                <RefreshIcon className={isRefreshing ? 'animate-spin' : ''} />
              </IconButton>
            </Tooltip>
            <Tooltip title="Exportar tags filtrados">
              <IconButton onClick={handleExportFiltered} color="primary" size="large">
                <DownloadIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Hierarquia de Assets">
              <IconButton onClick={() => setShowTreeView(!showTreeView)} color="primary" size="large">
                <TreeIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        </Box>

        {/* Stats Cards */}
        <Stack direction="row" spacing={2} sx={{ mb: 3, overflowX: 'auto' }}>
          <Card elevation={2} sx={{ minWidth: 200, flex: 1 }}>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <DataIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" fontWeight="bold">{stats.total}</Typography>
              <Typography variant="caption" color="text.secondary">Total Tags</Typography>
            </CardContent>
          </Card>
          <Card elevation={2} sx={{ minWidth: 200, flex: 1, bgcolor: '#e8f5e9' }}>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <TrendingUpIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h4" fontWeight="bold" color="success.main">{stats.enabled}</Typography>
              <Typography variant="caption" color="text.secondary">Ativos</Typography>
            </CardContent>
          </Card>
          <Card elevation={2} sx={{ minWidth: 200, flex: 1, bgcolor: '#e3f2fd' }}>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <TrendingUpIcon sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant="h4" fontWeight="bold" color="info.main">{getTagsWithRecentData()}</Typography>
              <Typography variant="caption" color="text.secondary">Com Dados Recentes</Typography>
            </CardContent>
          </Card>
          <Card elevation={2} sx={{ minWidth: 200, flex: 1, bgcolor: '#fff3e0' }}>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <SettingsIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
              <Typography variant="h4" fontWeight="bold" color="warning.main">{stats.disabled}</Typography>
              <Typography variant="caption" color="text.secondary">Inativos</Typography>
            </CardContent>
          </Card>
          <Card elevation={2} sx={{ minWidth: 200, flex: 1, bgcolor: '#f3e5f5' }}>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <ArchiveIcon sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
              <Typography variant="h4" fontWeight="bold" color="secondary.main">{stats.logging}</Typography>
              <Typography variant="caption" color="text.secondary">Com Histórico</Typography>
            </CardContent>
          </Card>
        </Stack>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, flexDirection: { xs: 'column', md: 'row' } }}>
        {/* Tree View Sidebar */}
        {showTreeView && (
          <Box sx={{ width: { xs: '100%', md: '25%' } }}>
            <Paper elevation={3} sx={{ height: '700px', overflow: 'hidden' }}>
              <AssetTreeView
                onAssetSelect={(asset) => console.log('Selected:', asset)}
                selectedAssetId={undefined}
              />
            </Paper>
          </Box>
        )}

        {/* Main Content */}
        <Box sx={{ flex: 1 }}>
          <Paper elevation={3}>
            {/* Tabs */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} variant="fullWidth">
                <Tab icon={<DataIcon />} label="Tags" iconPosition="start" />
                <Tab icon={<FormulaIcon />} label="Fórmulas" iconPosition="start" />
                <Tab icon={<SettingsIcon />} label="Configurações" iconPosition="start" />
              </Tabs>
            </Box>

            {/* Tab 0: Tags */}
            <TabPanel value={activeTab} index={0}>
              <Box sx={{ px: 2 }}>
                {/* Actions */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6">Gerenciamento de Tags</Typography>
                  <Stack direction="row" spacing={1}>
                    <Button
                      startIcon={<DownloadIcon />}
                      variant="outlined"
                      size="small"
                      onClick={handleDownloadTemplate}
                    >
                      Template
                    </Button>
                    <Button
                      startIcon={<UploadIcon />}
                      variant="outlined"
                      size="small"
                      onClick={() => setIsBulkImportOpen(true)}
                    >
                      Importar
                    </Button>
                    <Button
                      startIcon={<AddIcon />}
                      variant="contained"
                      size="small"
                      onClick={() => setIsCreateModalOpen(true)}
                    >
                      Novo Tag
                    </Button>
                  </Stack>
                </Box>

                {/* Filters */}
                <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                    <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 35%' } }}>
                      <TextField
                        fullWidth
                        size="small"
                        placeholder="Buscar..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                      />
                    </Box>
                    <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 15%' } }}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Dispositivo</InputLabel>
                        <Select value={filterDevice} label="Dispositivo" onChange={(e) => setFilterDevice(e.target.value)}>
                          <MenuItem value="">Todos</MenuItem>
                          {devices.map((device) => (
                            <MenuItem key={device.id} value={device.id}>{device.name}</MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Box>
                    <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 15%' } }}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Tipo</InputLabel>
                        <Select value={filterDataType} label="Tipo" onChange={(e) => setFilterDataType(e.target.value)}>
                          <MenuItem value="">Todos</MenuItem>
                          <MenuItem value="BOOL">Boolean</MenuItem>
                          <MenuItem value="INT">Integer</MenuItem>
                          <MenuItem value="FLOAT">Float</MenuItem>
                          <MenuItem value="DOUBLE">Double</MenuItem>
                          <MenuItem value="STRING">String</MenuItem>
                        </Select>
                      </FormControl>
                    </Box>
                    <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 15%' } }}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Status</InputLabel>
                        <Select value={filterEnabled} label="Status" onChange={(e) => setFilterEnabled(e.target.value)}>
                          <MenuItem value="all">Todos</MenuItem>
                          <MenuItem value="enabled">Ativos</MenuItem>
                          <MenuItem value="disabled">Inativos</MenuItem>
                        </Select>
                      </FormControl>
                    </Box>
                    <Box sx={{ flex: { xs: '1 1 100%', md: '0 1 auto' }, minWidth: 100 }}>
                      <Button
                        fullWidth
                        variant="text"
                        onClick={() => {
                          setSearchQuery('');
                          setFilterDevice('');
                          setFilterDataType('');
                          setFilterEnabled('all');
                        }}
                      >
                        Limpar
                      </Button>
                    </Box>
                  </Box>
                </Paper>

                {/* Tags Table */}
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: 'grey.100' }}>
                        <TableCell><strong>Nome</strong></TableCell>
                        <TableCell><strong>Endereço</strong></TableCell>
                        <TableCell><strong>Tipo</strong></TableCell>
                        <TableCell><strong>Último Valor</strong></TableCell>
                        <TableCell><strong>Unidade</strong></TableCell>
                        <TableCell><strong>Status</strong></TableCell>
                        <TableCell align="right"><strong>Ações</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {filteredTags.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                            <Typography variant="body2" color="text.secondary">
                              Nenhum tag encontrado
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ) : (
                        filteredTags.map((tag) => (
                          <TableRow key={tag.id} hover>
                            <TableCell>
                              <Typography variant="body2" fontWeight="medium">{tag.name}</Typography>
                              {tag.description && (
                                <Typography variant="caption" color="text.secondary">{tag.description}</Typography>
                              )}
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" fontFamily="monospace" fontSize="0.75rem">
                                {tag.address}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip label={tag.data_type} size="small" color="secondary" variant="outlined" />
                            </TableCell>
                            <TableCell>
                              {tag.last_value !== null && tag.last_value !== undefined ? (
                                <Box>
                                  <Typography variant="body2" fontWeight="medium" color="primary">
                                    {typeof tag.last_value === 'number' 
                                      ? tag.last_value.toFixed(2) 
                                      : tag.last_value}
                                  </Typography>
                                  {tag.last_timestamp && (
                                    <Typography variant="caption" color="text.secondary">
                                      {new Date(tag.last_timestamp).toLocaleTimeString()}
                                    </Typography>
                                  )}
                                </Box>
                              ) : (
                                <Typography variant="body2" color="text.secondary">-</Typography>
                              )}
                            </TableCell>
                            <TableCell>{tag.unit || '-'}</TableCell>
                            <TableCell>
                              <Stack direction="row" spacing={0.5}>
                                <Chip
                                  label={tag.enabled ? 'Ativo' : 'Inativo'}
                                  size="small"
                                  color={tag.enabled ? 'success' : 'default'}
                                />
                                {tag.log_enabled && (
                                  <Chip icon={<ArchiveIcon />} label="Log" size="small" color="info" variant="outlined" />
                                )}
                              </Stack>
                            </TableCell>
                            <TableCell align="right">
                              <Tooltip title="Copiar ID">
                                <IconButton size="small" onClick={() => handleCopyTagId(tag.id)}>
                                  <ContentCopyIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                              <IconButton size="small" color="primary" onClick={() => openEditModal(tag)}>
                                <EditIcon fontSize="small" />
                              </IconButton>
                              <IconButton size="small" color="error" onClick={() => openDeleteDialog(tag)}>
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>

                {filteredTags.length > 0 && (
                  <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', bgcolor: 'grey.50' }}>
                    <Typography variant="caption" color="text.secondary">
                      Mostrando {filteredTags.length} de {tags.length} tags
                    </Typography>
                  </Box>
                )}
              </Box>
            </TabPanel>

            {/* Tab 1: Formulas */}
            <TabPanel value={activeTab} index={1}>
              <Box sx={{ px: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6">Fórmulas Calculadas</Typography>
                  <Button
                    startIcon={<AddIcon />}
                    variant="contained"
                    size="small"
                    onClick={() => setIsFormulaModalOpen(true)}
                  >
                    Nova Fórmula
                  </Button>
                </Box>

                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                  {formulas.map((formula) => (
                    <Box key={formula.id} sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' } }}>
                      <Card variant="outlined">
                        <CardContent>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                            <Box>
                              <Typography variant="h6" gutterBottom>
                                {formula.name}
                              </Typography>
                              <Chip label={formula.unit} size="small" color="primary" variant="outlined" />
                            </Box>
                            <Stack direction="row" spacing={0.5}>
                              <IconButton size="small" color="primary">
                                <EditIcon fontSize="small" />
                              </IconButton>
                              <IconButton size="small" color="error">
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Stack>
                          </Box>

                          <Divider sx={{ my: 1 }} />

                          <Box sx={{ bgcolor: 'grey.100', p: 1.5, borderRadius: 1, mb: 2 }}>
                            <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                              Expressão:
                            </Typography>
                            <Typography variant="body2" fontFamily="monospace" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <CodeIcon fontSize="small" color="action" />
                              {formula.expression}
                            </Typography>
                          </Box>

                          <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                            Tags utilizadas:
                          </Typography>
                          <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                            {formula.tags.map((tag: string) => (
                              <Chip key={tag} label={tag} size="small" variant="outlined" />
                            ))}
                          </Stack>
                        </CardContent>
                      </Card>
                    </Box>
                  ))}
                </Box>

                {formulas.length === 0 && (
                  <Box sx={{ textAlign: 'center', py: 8 }}>
                    <FormulaIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                      Nenhuma fórmula configurada
                    </Typography>
                    <Typography variant="body2" color="text.secondary" mb={3}>
                      Crie fórmulas para calcular KPIs e métricas derivadas
                    </Typography>
                    <Button
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={() => setIsFormulaModalOpen(true)}
                    >
                      Criar Primeira Fórmula
                    </Button>
                  </Box>
                )}
              </Box>
            </TabPanel>

            {/* Tab 2: Settings */}
            <TabPanel value={activeTab} index={2}>
              <Box sx={{ px: 2 }}>
                <Typography variant="h6" gutterBottom>Configurações Avançadas</Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Configurações de arquivamento, sincronização e integrações
                </Typography>

                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                  <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' } }}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          Arquivamento Histórico
                        </Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          Configure políticas de retenção e compressão de dados históricos
                        </Typography>
                        <Button
                          variant="outlined"
                          size="small"
                          fullWidth
                          onClick={() => setIsArchivingModalOpen(true)}
                        >
                          Configurar Arquivamento
                        </Button>
                      </CardContent>
                    </Card>
                  </Box>

                  <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' } }}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          Tag Point Builder
                        </Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          Interface avançada para descoberta e cadastro de tags OPC UA
                        </Typography>
                        <Button
                          variant="outlined"
                          size="small"
                          fullWidth
                          onClick={() => {
                            window.location.href = '/settings/tag-configuration';
                          }}
                        >
                          Abrir Tag Builder
                        </Button>
                      </CardContent>
                    </Card>
                  </Box>

                  <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' } }}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          Exportação de Dados
                        </Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          Exporte configurações de tags em diversos formatos
                        </Typography>
                        <Button
                          variant="outlined"
                          size="small"
                          fullWidth
                          onClick={handleExportFiltered}
                        >
                          Exportar Configurações
                        </Button>
                      </CardContent>
                    </Card>
                  </Box>

                  <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' } }}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          Notificações & Alarmes
                        </Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          Configure alarmes baseados em valores de tags
                        </Typography>
                        <Button
                          variant="outlined"
                          size="small"
                          fullWidth
                          onClick={() => {
                            window.location.href = '/alarms';
                          }}
                        >
                          Gerenciar Alarmes
                        </Button>
                      </CardContent>
                    </Card>
                  </Box>
                </Box>
              </Box>
            </TabPanel>
          </Paper>
        </Box>
      </Box>

      {/* Modals */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => !isSubmitting && setIsCreateModalOpen(false)}
        title="Criar Novo Tag"
        size="lg"
      >
        <TagForm
          onSubmit={handleCreate}
          onCancel={() => setIsCreateModalOpen(false)}
          isLoading={isSubmitting}
        />
      </Modal>

      <Modal
        isOpen={isEditModalOpen}
        onClose={() => !isSubmitting && setIsEditModalOpen(false)}
        title="Editar Tag"
        size="lg"
      >
        {selectedTag && (
          <TagForm
            tag={selectedTag}
            onSubmit={handleEdit}
            onCancel={() => setIsEditModalOpen(false)}
            isLoading={isSubmitting}
          />
        )}
      </Modal>

      <ConfirmDialog
        isOpen={isDeleteDialogOpen}
        onClose={() => !isSubmitting && setIsDeleteDialogOpen(false)}
        onConfirm={handleDelete}
        title="Excluir Tag"
        message={`Tem certeza que deseja excluir "${selectedTag?.name}"? Esta ação não pode ser desfeita.`}
        confirmText="Excluir"
        cancelText="Cancelar"
        variant="danger"
        isLoading={isSubmitting}
      />

      <TagBulkImport
        open={isBulkImportOpen}
        onClose={() => setIsBulkImportOpen(false)}
        onImport={handleBulkImport}
        gatewayId={undefined}
      />

      {/* Formula Modal (TODO: Create component) */}
      <Modal
        isOpen={isFormulaModalOpen}
        onClose={() => setIsFormulaModalOpen(false)}
        title="Nova Fórmula"
        size="lg"
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Modal de criação de fórmulas será implementado aqui
          </Typography>
        </Box>
      </Modal>

      {/* Archiving Configuration Modal */}
      <Modal
        isOpen={isArchivingModalOpen}
        onClose={() => setIsArchivingModalOpen(false)}
        title="Configurar Arquivamento"
        size="lg"
      >
        <Box sx={{ p: 3 }}>
          <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
            Configurações de Arquivamento de Dados
          </Typography>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Archiving Mode */}
            <Box>
              <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
                Modo de Arquivamento
              </Typography>
              <Select fullWidth defaultValue="time-based" size="small">
                <MenuItem value="time-based">Baseado em Tempo</MenuItem>
                <MenuItem value="change-based">Baseado em Mudança</MenuItem>
                <MenuItem value="hybrid">Híbrido</MenuItem>
              </Select>
            </Box>

            {/* Retention Period */}
            <Box>
              <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
                Período de Retenção
              </Typography>
              <TextField
                fullWidth
                size="small"
                type="number"
                defaultValue={30}
                InputProps={{
                  endAdornment: <Typography variant="body2" sx={{ ml: 1 }}>dias</Typography>
                }}
              />
            </Box>

            {/* Compression */}
            <Box>
              <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
                Compressão
              </Typography>
              <Select fullWidth defaultValue="gzip" size="small">
                <MenuItem value="none">Sem Compressão</MenuItem>
                <MenuItem value="gzip">GZIP</MenuItem>
                <MenuItem value="lz4">LZ4</MenuItem>
              </Select>
            </Box>

            {/* Archiving Interval */}
            <Box>
              <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
                Intervalo de Arquivamento
              </Typography>
              <TextField
                fullWidth
                size="small"
                type="number"
                defaultValue={60}
                InputProps={{
                  endAdornment: <Typography variant="body2" sx={{ ml: 1 }}>segundos</Typography>
                }}
              />
            </Box>

            {/* Storage Location */}
            <Box>
              <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
                Local de Armazenamento
              </Typography>
              <TextField
                fullWidth
                size="small"
                defaultValue="/data/archive"
                placeholder="/path/to/archive"
              />
            </Box>

            {/* Enable/Disable */}
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                Habilitar Arquivamento Automático
              </Typography>
              <Switch defaultChecked />
            </Box>

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', gap: 2, mt: 2, justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                onClick={() => setIsArchivingModalOpen(false)}
              >
                Cancelar
              </Button>
              <Button
                variant="contained"
                onClick={() => {
                  showToast.success('Configurações de arquivamento salvas!');
                  setIsArchivingModalOpen(false);
                }}
              >
                Salvar Configurações
              </Button>
            </Box>
          </Box>
        </Box>
      </Modal>
    </Box>
  );
};
