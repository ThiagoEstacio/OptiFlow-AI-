/**
 * Asset Framework Page - PI Asset Framework-like Interface
 * Hierarchical organization of industrial assets with templates and attributes
 *
 * Features:
 * - Tree view of asset hierarchy (Plant > Area > Equipment Group > Equipment > Component)
 * - Template management for reusable asset definitions
 * - Attribute viewing with real-time data from tags
 * - Search and filter capabilities
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
  Paper,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Tooltip,
  Stack,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Collapse,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Breadcrumbs,
  Link,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
  Factory as FactoryIcon,
  Domain as DomainIcon,
  Category as CategoryIcon,
  Settings as SettingsIcon,
  Memory as MemoryIcon,
  Search as SearchIcon,
  Build as BuildIcon,
  Save as SaveIcon,
  AccountTree as TreeIcon,
  Description as TemplateIcon,
  LocalOffer as TagIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import {
  gatewayEdgeApi,
  AssetElementHierarchy,
  AssetElement,
  AssetTemplate,
  AssetFrameworkStats,
  ElementType,
} from '../api/gatewayEdge';

// Icon mapping for element types
const elementTypeIcons: Record<ElementType, React.ReactNode> = {
  plant: <FactoryIcon />,
  area: <DomainIcon />,
  equipment_group: <CategoryIcon />,
  equipment: <SettingsIcon />,
  component: <MemoryIcon />,
};

const elementTypeLabels: Record<ElementType, string> = {
  plant: 'Planta',
  area: 'Área',
  equipment_group: 'Grupo de Equipamentos',
  equipment: 'Equipamento',
  component: 'Componente',
};

const elementTypeColors: Record<ElementType, string> = {
  plant: '#1976D2',
  area: '#388E3C',
  equipment_group: '#F57C00',
  equipment: '#7B1FA2',
  component: '#455A64',
};

// Tree Node Component
interface TreeNodeProps {
  node: AssetElementHierarchy;
  level: number;
  selectedId: string | null;
  expandedIds: Set<string>;
  onSelect: (node: AssetElementHierarchy) => void;
  onToggle: (id: string) => void;
}

const TreeNode: React.FC<TreeNodeProps> = ({
  node,
  level,
  selectedId,
  expandedIds,
  onSelect,
  onToggle
}) => {
  const isExpanded = expandedIds.has(node.id);
  const isSelected = selectedId === node.id;
  const hasChildren = node.children && node.children.length > 0;

  return (
    <>
      <ListItemButton
        sx={{
          pl: 2 + level * 2,
          backgroundColor: isSelected ? 'action.selected' : 'transparent',
          borderLeft: isSelected ? `3px solid ${elementTypeColors[node.type]}` : '3px solid transparent',
          '&:hover': {
            backgroundColor: 'action.hover',
          },
        }}
        onClick={() => onSelect(node)}
      >
        <ListItemIcon sx={{ minWidth: 32 }}>
          {hasChildren ? (
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onToggle(node.id);
              }}
            >
              {isExpanded ? <ExpandMoreIcon /> : <ChevronRightIcon />}
            </IconButton>
          ) : (
            <Box sx={{ width: 28 }} />
          )}
        </ListItemIcon>
        <ListItemIcon sx={{ minWidth: 32, color: node.color || elementTypeColors[node.type] }}>
          {elementTypeIcons[node.type]}
        </ListItemIcon>
        <ListItemText
          primary={node.name}
          secondary={`${elementTypeLabels[node.type]} • ${node.attributes_count} atributos`}
          primaryTypographyProps={{ fontWeight: isSelected ? 600 : 400 }}
        />
        {node.template_id && (
          <Chip
            size="small"
            label="Template"
            variant="outlined"
            sx={{ ml: 1 }}
          />
        )}
      </ListItemButton>
      {hasChildren && (
        <Collapse in={isExpanded} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            {node.children.map((child) => (
              <TreeNode
                key={child.id}
                node={child}
                level={level + 1}
                selectedId={selectedId}
                expandedIds={expandedIds}
                onSelect={onSelect}
                onToggle={onToggle}
              />
            ))}
          </List>
        </Collapse>
      )}
    </>
  );
};

export const AssetFrameworkPage: React.FC = () => {
  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [hierarchy, setHierarchy] = useState<AssetElementHierarchy[]>([]);
  const [stats, setStats] = useState<AssetFrameworkStats | null>(null);
  const [templates, setTemplates] = useState<AssetTemplate[]>([]);
  const [selectedElement, setSelectedElement] = useState<AssetElement | null>(null);
  const [selectedHierarchyNode, setSelectedHierarchyNode] = useState<AssetElementHierarchy | null>(null);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'hierarchy' | 'templates'>('hierarchy');

  // Dialog states
  const [buildDialogOpen, setBuildDialogOpen] = useState(false);
  const [buildLoading, setBuildLoading] = useState(false);

  // Load data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [hierarchyData, statsData, templatesData] = await Promise.all([
        gatewayEdgeApi.getAssetHierarchy(),
        gatewayEdgeApi.getAssetStats(),
        gatewayEdgeApi.listAssetTemplates(),
      ]);

      setHierarchy(hierarchyData);
      setStats(statsData);
      setTemplates(templatesData);

      // Auto-expand first level
      const firstLevelIds = new Set(hierarchyData.map(h => h.id));
      setExpandedIds(firstLevelIds);

    } catch (err: any) {
      setError(err.message || 'Falha ao carregar Asset Framework');
      console.error('Error loading asset framework:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Load element details when selected
  const loadElementDetails = async (elementId: string) => {
    try {
      const element = await gatewayEdgeApi.getAssetElement(elementId, true);
      setSelectedElement(element);
    } catch (err) {
      console.error('Error loading element details:', err);
    }
  };

  // Handle tree node selection
  const handleNodeSelect = (node: AssetElementHierarchy) => {
    setSelectedHierarchyNode(node);
    loadElementDetails(node.id);
  };

  // Handle tree node toggle
  const handleNodeToggle = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  // Build hierarchy from tags
  const handleBuildFromTags = async () => {
    try {
      setBuildLoading(true);
      const newStats = await gatewayEdgeApi.buildAssetHierarchyFromTags();
      setStats(newStats);
      await loadData();
      setSuccess(`Hierarquia construída: ${newStats.total_elements} elementos criados`);
      setBuildDialogOpen(false);
    } catch (err: any) {
      setError(err.message || 'Falha ao construir hierarquia');
    } finally {
      setBuildLoading(false);
    }
  };

  // Save configuration
  const handleSave = async () => {
    try {
      const saved = await gatewayEdgeApi.saveAssetConfiguration();
      if (saved) {
        setSuccess('Configuração salva com sucesso');
      } else {
        setError('Falha ao salvar configuração');
      }
    } catch (err: any) {
      setError(err.message || 'Falha ao salvar');
    }
  };

  // Get breadcrumb path
  const getBreadcrumbs = () => {
    if (!selectedElement) return [];
    const parts = selectedElement.path.split('/').filter(Boolean);
    return parts;
  };

  // Filter hierarchy based on search
  const filterHierarchy = (nodes: AssetElementHierarchy[], query: string): AssetElementHierarchy[] => {
    if (!query) return nodes;
    const lowerQuery = query.toLowerCase();

    return nodes.reduce<AssetElementHierarchy[]>((acc, node) => {
      const matches = node.name.toLowerCase().includes(lowerQuery) ||
                     node.path.toLowerCase().includes(lowerQuery);
      const filteredChildren = filterHierarchy(node.children || [], query);

      if (matches || filteredChildren.length > 0) {
        acc.push({
          ...node,
          children: filteredChildren,
        });
      }
      return acc;
    }, []);
  };

  const filteredHierarchy = filterHierarchy(hierarchy, searchQuery);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TreeIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            Asset Framework
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Organização hierárquica de ativos industriais (estilo PI Asset Framework)
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<BuildIcon />}
            onClick={() => setBuildDialogOpen(true)}
          >
            Construir de Tags
          </Button>
          <Button
            variant="outlined"
            startIcon={<SaveIcon />}
            onClick={handleSave}
          >
            Salvar
          </Button>
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={loadData}
          >
            Atualizar
          </Button>
        </Stack>
      </Box>

      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Stats Cards */}
      {stats && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={2}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="primary.main" fontWeight="bold">
                  {stats.total_elements}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Elementos
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="secondary.main" fontWeight="bold">
                  {stats.total_templates}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Templates
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="success.main" fontWeight="bold">
                  {stats.total_attributes}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Atributos
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="info.main" fontWeight="bold">
                  {stats.linked_attributes}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Vinculados a Tags
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" fontWeight="bold">
                  {stats.root_elements}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Elementos Raiz
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Stack direction="row" spacing={1} justifyContent="center" flexWrap="wrap">
                  {Object.entries(stats.elements_by_type || {}).map(([type, count]) => (
                    <Chip
                      key={type}
                      size="small"
                      label={`${count}`}
                      icon={elementTypeIcons[type as ElementType] as React.ReactElement}
                      sx={{ bgcolor: elementTypeColors[type as ElementType], color: 'white' }}
                    />
                  ))}
                </Stack>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Por Tipo
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Tabs */}
      <Box sx={{ mb: 2 }}>
        <Stack direction="row" spacing={1}>
          <Button
            variant={activeTab === 'hierarchy' ? 'contained' : 'outlined'}
            startIcon={<TreeIcon />}
            onClick={() => setActiveTab('hierarchy')}
          >
            Hierarquia
          </Button>
          <Button
            variant={activeTab === 'templates' ? 'contained' : 'outlined'}
            startIcon={<TemplateIcon />}
            onClick={() => setActiveTab('templates')}
          >
            Templates ({templates.length})
          </Button>
        </Stack>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : activeTab === 'hierarchy' ? (
        <Grid container spacing={3}>
          {/* Tree View */}
          <Grid item xs={12} md={5}>
            <Paper sx={{ height: 'calc(100vh - 400px)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Pesquisar elementos..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  InputProps={{
                    startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                  }}
                />
              </Box>
              <Box sx={{ flex: 1, overflow: 'auto' }}>
                {filteredHierarchy.length === 0 ? (
                  <Box sx={{ p: 4, textAlign: 'center' }}>
                    <Typography color="text.secondary">
                      {searchQuery ? 'Nenhum elemento encontrado' : 'Nenhum elemento cadastrado'}
                    </Typography>
                    <Button
                      variant="outlined"
                      startIcon={<BuildIcon />}
                      onClick={() => setBuildDialogOpen(true)}
                      sx={{ mt: 2 }}
                    >
                      Construir de Tags
                    </Button>
                  </Box>
                ) : (
                  <List dense>
                    {filteredHierarchy.map((node) => (
                      <TreeNode
                        key={node.id}
                        node={node}
                        level={0}
                        selectedId={selectedHierarchyNode?.id || null}
                        expandedIds={expandedIds}
                        onSelect={handleNodeSelect}
                        onToggle={handleNodeToggle}
                      />
                    ))}
                  </List>
                )}
              </Box>
            </Paper>
          </Grid>

          {/* Details Panel */}
          <Grid item xs={12} md={7}>
            <Paper sx={{ height: 'calc(100vh - 400px)', overflow: 'auto', p: 3 }}>
              {selectedElement ? (
                <>
                  {/* Breadcrumbs */}
                  <Breadcrumbs sx={{ mb: 2 }}>
                    {getBreadcrumbs().map((part, idx) => (
                      <Link
                        key={idx}
                        underline="hover"
                        color="inherit"
                        sx={{ cursor: 'pointer' }}
                      >
                        {part}
                      </Link>
                    ))}
                  </Breadcrumbs>

                  {/* Element Header */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                    <Box
                      sx={{
                        width: 48,
                        height: 48,
                        borderRadius: 2,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        bgcolor: selectedElement.color || elementTypeColors[selectedElement.element_type],
                        color: 'white',
                      }}
                    >
                      {elementTypeIcons[selectedElement.element_type]}
                    </Box>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h5" fontWeight="bold">
                        {selectedElement.name}
                      </Typography>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Chip
                          size="small"
                          label={elementTypeLabels[selectedElement.element_type]}
                          sx={{
                            bgcolor: selectedElement.color || elementTypeColors[selectedElement.element_type],
                            color: 'white',
                          }}
                        />
                        {selectedElement.template_id && (
                          <Chip size="small" label="Usa Template" variant="outlined" />
                        )}
                        <Typography variant="caption" color="text.secondary">
                          ID: {selectedElement.id}
                        </Typography>
                      </Stack>
                    </Box>
                  </Box>

                  {selectedElement.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                      {selectedElement.description}
                    </Typography>
                  )}

                  <Divider sx={{ my: 2 }} />

                  {/* Attributes Table */}
                  <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <TagIcon />
                    Atributos ({selectedElement.attributes?.length || 0})
                  </Typography>

                  {selectedElement.attributes && selectedElement.attributes.length > 0 ? (
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Nome</TableCell>
                            <TableCell>Tipo</TableCell>
                            <TableCell>Valor</TableCell>
                            <TableCell>Unidade</TableCell>
                            <TableCell>Qualidade</TableCell>
                            <TableCell>Tag ID</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {selectedElement.attributes.map((attr) => (
                            <TableRow key={attr.id} hover>
                              <TableCell>
                                <Typography fontWeight={500}>{attr.name}</Typography>
                                {attr.description && (
                                  <Typography variant="caption" color="text.secondary" display="block">
                                    {attr.description}
                                  </Typography>
                                )}
                              </TableCell>
                              <TableCell>
                                <Chip size="small" label={attr.attribute_type} variant="outlined" />
                              </TableCell>
                              <TableCell>
                                <Typography
                                  fontFamily="monospace"
                                  color={attr.current_quality === 'Good' ? 'success.main' : 'error.main'}
                                >
                                  {attr.current_value !== null && attr.current_value !== undefined
                                    ? typeof attr.current_value === 'number'
                                      ? attr.current_value.toFixed(2)
                                      : String(attr.current_value)
                                    : '-'}
                                </Typography>
                              </TableCell>
                              <TableCell>{attr.uom || '-'}</TableCell>
                              <TableCell>
                                <Chip
                                  size="small"
                                  label={attr.current_quality || 'Unknown'}
                                  color={attr.current_quality === 'Good' ? 'success' : 'default'}
                                />
                              </TableCell>
                              <TableCell>
                                <Typography variant="caption" fontFamily="monospace">
                                  {attr.tag_id || '-'}
                                </Typography>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  ) : (
                    <Typography color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                      Nenhum atributo configurado
                    </Typography>
                  )}

                  {/* Children count */}
                  {selectedElement.children && selectedElement.children.length > 0 && (
                    <>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="body2" color="text.secondary">
                        {selectedElement.children.length} elemento(s) filho(s)
                      </Typography>
                    </>
                  )}

                  {/* Metadata */}
                  {selectedElement.metadata && Object.keys(selectedElement.metadata).length > 0 && (
                    <>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="subtitle2" gutterBottom>
                        Metadata
                      </Typography>
                      <Typography variant="body2" component="pre" sx={{
                        bgcolor: 'grey.100',
                        p: 1,
                        borderRadius: 1,
                        overflow: 'auto',
                        fontSize: '0.75rem',
                      }}>
                        {JSON.stringify(selectedElement.metadata, null, 2)}
                      </Typography>
                    </>
                  )}
                </>
              ) : (
                <Box sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  color: 'text.secondary',
                }}>
                  <TreeIcon sx={{ fontSize: 64, mb: 2, opacity: 0.5 }} />
                  <Typography>
                    Selecione um elemento na árvore para ver detalhes
                  </Typography>
                </Box>
              )}
            </Paper>
          </Grid>
        </Grid>
      ) : (
        /* Templates Tab */
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">
              Templates de Elementos
            </Typography>
            <Button variant="contained" startIcon={<AddIcon />} disabled>
              Novo Template
            </Button>
          </Box>

          {templates.length === 0 ? (
            <Box sx={{ py: 4, textAlign: 'center' }}>
              <TemplateIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
              <Typography color="text.secondary">
                Nenhum template cadastrado
              </Typography>
            </Box>
          ) : (
            <Grid container spacing={2}>
              {templates.map((template) => (
                <Grid item xs={12} sm={6} md={4} key={template.id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Box
                          sx={{
                            width: 32,
                            height: 32,
                            borderRadius: 1,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            bgcolor: template.color || elementTypeColors[template.element_type],
                            color: 'white',
                          }}
                        >
                          {elementTypeIcons[template.element_type]}
                        </Box>
                        <Typography variant="subtitle1" fontWeight="bold">
                          {template.name}
                        </Typography>
                      </Box>
                      {template.description && (
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          {template.description}
                        </Typography>
                      )}
                      <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mt: 1 }}>
                        <Chip
                          size="small"
                          label={elementTypeLabels[template.element_type]}
                          variant="outlined"
                        />
                        <Chip
                          size="small"
                          label={`${template.attributes?.length || 0} atributos`}
                          variant="outlined"
                        />
                        {template.elements_count !== undefined && (
                          <Chip
                            size="small"
                            label={`${template.elements_count} em uso`}
                            color="primary"
                            variant="outlined"
                          />
                        )}
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Paper>
      )}

      {/* Build Dialog */}
      <Dialog open={buildDialogOpen} onClose={() => setBuildDialogOpen(false)}>
        <DialogTitle>Construir Hierarquia de Tags</DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            Esta ação irá analisar o arquivo <code>tags_config.json</code> e criar automaticamente
            uma hierarquia de ativos baseada nos caminhos (group_path) configurados.
          </Typography>
          <Alert severity="warning" sx={{ mb: 2 }}>
            A hierarquia existente será reconstruída. Certifique-se de salvar antes.
          </Alert>
          <Typography variant="body2" color="text.secondary">
            Os templates padrão (Motor, Medidor, Transformador, Shiploader) serão criados automaticamente.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBuildDialogOpen(false)}>
            Cancelar
          </Button>
          <Button
            variant="contained"
            onClick={handleBuildFromTags}
            disabled={buildLoading}
            startIcon={buildLoading ? <CircularProgress size={20} /> : <BuildIcon />}
          >
            {buildLoading ? 'Construindo...' : 'Construir'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AssetFrameworkPage;
