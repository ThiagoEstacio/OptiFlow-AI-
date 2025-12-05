/**
 * Asset Tree Page - Industrial Asset Hierarchy (Tremor)
 * ==================================================================
 *
 * Hierarchical organization of industrial assets with templates and attributes.
 * Uses Tremor UI components for consistency with the rest of the application.
 *
 * Features:
 * - Tree view of asset hierarchy (Plant > Area > Equipment Group > Equipment > Component)
 * - Template management for reusable asset definitions
 * - Attribute viewing with real-time data from tags
 * - Search and filter capabilities
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Title,
  Text,
  Flex,
  Grid,
  Badge,
  TabGroup,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  TextInput,
  Button,
  Divider,
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
  Metric,
  ProgressBar,
  Callout,
} from '@tremor/react';
import {
  Factory,
  Building2,
  Boxes,
  Settings,
  Cpu,
  Search,
  RefreshCw,
  Save,
  Wrench,
  ChevronRight,
  ChevronDown,
  FileText,
  Tag,
  Network,
  AlertCircle,
  CheckCircle,
  XCircle,
  Plus,
  Trash2,
  Link,
} from 'lucide-react';
import {
  gatewayEdgeApi,
  AssetElementHierarchy,
  AssetElement,
  AssetTemplate,
  AssetFrameworkStats,
  ElementType,
} from '../../api/gatewayEdge';

// Icon mapping for element types
const elementTypeIcons: Record<ElementType, React.ReactNode> = {
  plant: <Factory className="w-5 h-5" />,
  area: <Building2 className="w-5 h-5" />,
  equipment_group: <Boxes className="w-5 h-5" />,
  equipment: <Settings className="w-5 h-5" />,
  component: <Cpu className="w-5 h-5" />,
};

const elementTypeLabels: Record<ElementType, string> = {
  plant: 'Planta',
  area: 'Área',
  equipment_group: 'Grupo',
  equipment: 'Equipamento',
  component: 'Componente',
};

const elementTypeColors: Record<ElementType, 'blue' | 'emerald' | 'orange' | 'violet' | 'slate'> = {
  plant: 'blue',
  area: 'emerald',
  equipment_group: 'orange',
  equipment: 'violet',
  component: 'slate',
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
    <div>
      <div
        className={`
          flex items-center gap-2 px-3 py-2 cursor-pointer rounded-lg transition-colors
          ${isSelected ? 'bg-blue-50 border-l-4 border-blue-500' : 'hover:bg-gray-50 border-l-4 border-transparent'}
        `}
        style={{ paddingLeft: `${12 + level * 20}px` }}
        onClick={() => onSelect(node)}
      >
        {/* Expand/Collapse */}
        <button
          className="p-0.5 hover:bg-gray-200 rounded"
          onClick={(e) => {
            e.stopPropagation();
            if (hasChildren) onToggle(node.id);
          }}
        >
          {hasChildren ? (
            isExpanded ? <ChevronDown className="w-4 h-4 text-gray-500" /> : <ChevronRight className="w-4 h-4 text-gray-500" />
          ) : (
            <span className="w-4" />
          )}
        </button>

        {/* Icon */}
        <span className={`text-${elementTypeColors[node.type]}-500`}>
          {elementTypeIcons[node.type]}
        </span>

        {/* Name */}
        <span className={`flex-1 text-sm ${isSelected ? 'font-semibold text-gray-900' : 'text-gray-700'}`}>
          {node.name}
        </span>

        {/* Badge */}
        <Badge size="xs" color={elementTypeColors[node.type]}>
          {node.attributes_count}
        </Badge>

        {node.template_id && (
          <Badge size="xs" color="gray">
            T
          </Badge>
        )}
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div>
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
        </div>
      )}
    </div>
  );
};

// Available tag type
interface AvailableTag {
  tag_id: string;
  tag_name: string;
  address: string;
  adapter_id: string;
  data_type: string;
  metadata?: {
    engineering_units?: string;
    description?: string;
  };
}

export const TremorAssetFramework: React.FC = () => {
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
  const [buildLoading, setBuildLoading] = useState(false);

  // Add Tag Modal State
  const [showAddTagModal, setShowAddTagModal] = useState(false);
  const [availableTags, setAvailableTags] = useState<AvailableTag[]>([]);
  const [availableAdapters, setAvailableAdapters] = useState<string[]>([]);
  const [tagSearchQuery, setTagSearchQuery] = useState('');
  const [selectedAdapter, setSelectedAdapter] = useState<string>('');
  const [addingTag, setAddingTag] = useState(false);

  // Create Element Modal State
  const [showCreateElementModal, setShowCreateElementModal] = useState(false);
  const [newElementName, setNewElementName] = useState('');
  const [newElementDescription, setNewElementDescription] = useState('');
  const [newElementType, setNewElementType] = useState<ElementType>('equipment');
  const [newElementParentId, setNewElementParentId] = useState<string>('');
  const [creatingElement, setCreatingElement] = useState(false);
  const [allElements, setAllElements] = useState<AssetElement[]>([]);

  // Load data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [hierarchyData, statsData, templatesData, elementsResponse] = await Promise.all([
        gatewayEdgeApi.getAssetHierarchy(),
        gatewayEdgeApi.getAssetStats(),
        gatewayEdgeApi.listAssetTemplates(),
        gatewayEdgeApi.listAssetElements({ limit: 500 }),
      ]);

      setHierarchy(hierarchyData);
      setStats(statsData);
      setTemplates(templatesData);
      setAllElements(elementsResponse.elements || []);

      // Auto-expand first level
      const firstLevelIds = new Set(hierarchyData.map(h => h.id));
      setExpandedIds(firstLevelIds);

    } catch (err: any) {
      setError(err.message || 'Falha ao carregar Asset Tree');
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
    console.log('[AssetFramework] Build from tags clicked');
    try {
      setBuildLoading(true);
      setError(null);
      setSuccess(null);
      console.log('[AssetFramework] Calling buildAssetHierarchyFromTags...');
      const newStats = await gatewayEdgeApi.buildAssetHierarchyFromTags();
      console.log('[AssetFramework] Build result:', newStats);

      // Reload data first
      await loadData();

      // Then set stats and success message (after loadData to prevent being cleared)
      setStats(newStats);
      const successMsg = `✅ Hierarquia construída com sucesso! ${newStats.total_elements} elementos, ${newStats.total_attributes} atributos vinculados.`;
      setSuccess(successMsg);

      // Show alert for better visibility
      alert(successMsg);
    } catch (err: any) {
      console.error('[AssetFramework] Build error:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Falha ao construir hierarquia';
      setError(errorMsg);
      alert(`❌ Erro: ${errorMsg}`);
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

  // Open create element modal
  const handleOpenCreateElementModal = () => {
    setShowCreateElementModal(true);
    setNewElementName('');
    setNewElementDescription('');
    setNewElementType('equipment');
    setNewElementParentId('');
  };

  // Create new element
  const handleCreateElement = async () => {
    if (!newElementName.trim()) {
      setError('Nome do elemento é obrigatório');
      return;
    }

    try {
      setCreatingElement(true);
      setError(null);

      const newElement = await gatewayEdgeApi.createAssetElement({
        name: newElementName.trim(),
        description: newElementDescription.trim() || `${newElementName} - Criado manualmente`,
        element_type: newElementType,
        parent_id: newElementParentId || undefined,
        attributes: [],
      });

      if (newElement) {
        setSuccess(`Elemento "${newElementName}" criado com sucesso!`);
        setShowCreateElementModal(false);
        await loadData();
      } else {
        setError('Falha ao criar elemento');
      }
    } catch (err: any) {
      console.error('Error creating element:', err);
      setError(err.response?.data?.detail || err.message || 'Falha ao criar elemento');
    } finally {
      setCreatingElement(false);
    }
  };

  // Delete element
  const handleDeleteElement = async (elementId: string) => {
    if (!confirm('Tem certeza que deseja excluir este elemento?')) return;

    try {
      await gatewayEdgeApi.deleteAssetElement(elementId);
      setSuccess('Elemento excluído com sucesso!');
      setSelectedElement(null);
      setSelectedHierarchyNode(null);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Falha ao excluir elemento');
    }
  };

  // Load available tags for modal
  const loadAvailableTags = async (adapter?: string, search?: string) => {
    try {
      const result = await gatewayEdgeApi.getAvailableTags(adapter, search);
      setAvailableTags(result.tags);
      setAvailableAdapters(result.adapters);
    } catch (err) {
      console.error('Failed to load available tags:', err);
    }
  };

  // Open add tag modal
  const handleOpenAddTagModal = () => {
    setShowAddTagModal(true);
    setTagSearchQuery('');
    setSelectedAdapter('');
    loadAvailableTags();
  };

  // Add tag to element
  const handleAddTag = async (tag: AvailableTag) => {
    if (!selectedElement) return;

    try {
      setAddingTag(true);
      const updated = await gatewayEdgeApi.addAttributeToElement(selectedElement.id, {
        name: tag.tag_name,
        description: `Tag vinculado: ${tag.address}`,
        data_type: tag.data_type,
        uom: tag.metadata?.engineering_units || '',
        tag_id: tag.tag_id,
        tag_address: tag.address,
      });

      if (updated) {
        setSelectedElement(updated);
        setSuccess(`Tag "${tag.tag_name}" adicionado ao elemento`);
        await loadData();
      }
    } catch (err: any) {
      setError(err.message || 'Falha ao adicionar tag');
    } finally {
      setAddingTag(false);
      setShowAddTagModal(false);
    }
  };

  // Remove attribute from element
  const handleRemoveAttribute = async (attributeId: string) => {
    if (!selectedElement) return;

    if (!confirm('Remover este atributo?')) return;

    try {
      const success = await gatewayEdgeApi.deleteAttribute(selectedElement.id, attributeId);
      if (success) {
        // Reload element details
        const updated = await gatewayEdgeApi.getAssetElement(selectedElement.id, true);
        if (updated) {
          setSelectedElement(updated);
        }
        setSuccess('Atributo removido');
        await loadData();
      }
    } catch (err: any) {
      setError(err.message || 'Falha ao remover atributo');
    }
  };

  // Filter available tags
  const filteredAvailableTags = availableTags.filter(tag => {
    const matchesSearch = !tagSearchQuery ||
      tag.tag_name.toLowerCase().includes(tagSearchQuery.toLowerCase()) ||
      tag.tag_id.toLowerCase().includes(tagSearchQuery.toLowerCase());
    const matchesAdapter = !selectedAdapter || tag.adapter_id === selectedAdapter;
    return matchesSearch && matchesAdapter;
  });

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

  // Get breadcrumb path
  const getBreadcrumbs = () => {
    if (!selectedElement) return [];
    return selectedElement.path.split('/').filter(Boolean);
  };

  // Quality icon helper
  const getQualityIcon = (quality: string | undefined) => {
    if (quality === 'Good') return <CheckCircle className="w-4 h-4 text-emerald-500" />;
    if (quality === 'Bad') return <XCircle className="w-4 h-4 text-red-500" />;
    return <AlertCircle className="w-4 h-4 text-amber-500" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <Flex alignItems="center" className="gap-2">
            <Network className="w-8 h-8 text-blue-600" />
            <Title>Asset Tree</Title>
          </Flex>
          <Text>Organização hierárquica de ativos industriais (organização hierárquica de ativos industriais)</Text>
        </div>
        <Flex className="gap-2">
          <Button
            variant="secondary"
            icon={Wrench}
            loading={buildLoading}
            onClick={handleBuildFromTags}
          >
            Construir de Tags
          </Button>
          <Button
            icon={Plus}
            onClick={handleOpenCreateElementModal}
          >
            Novo Elemento
          </Button>
          <Button variant="secondary" icon={Save} onClick={handleSave}>
            Salvar
          </Button>
          <Button variant="secondary" icon={RefreshCw} onClick={loadData}>
            Atualizar
          </Button>
        </Flex>
      </div>

      {/* Alerts */}
      {error && (
        <Callout title="Erro" icon={XCircle} color="rose">
          {error}
        </Callout>
      )}
      {success && (
        <Callout title="Sucesso" icon={CheckCircle} color="emerald">
          {success}
        </Callout>
      )}

      {/* Stats Cards */}
      {stats && (
        <Grid numItemsSm={2} numItemsMd={3} numItemsLg={6} className="gap-4">
          <Card decoration="top" decorationColor="blue">
            <Text>Elementos</Text>
            <Metric>{stats.total_elements}</Metric>
          </Card>
          <Card decoration="top" decorationColor="violet">
            <Text>Templates</Text>
            <Metric>{stats.total_templates}</Metric>
          </Card>
          <Card decoration="top" decorationColor="emerald">
            <Text>Atributos</Text>
            <Metric>{stats.total_attributes}</Metric>
          </Card>
          <Card decoration="top" decorationColor="cyan">
            <Text>Vinculados</Text>
            <Metric>{stats.linked_attributes}</Metric>
          </Card>
          <Card decoration="top" decorationColor="slate">
            <Text>Elementos Raiz</Text>
            <Metric>{stats.root_elements}</Metric>
          </Card>
          <Card>
            <Text>Por Tipo</Text>
            <Flex className="gap-1 mt-2 flex-wrap">
              {Object.entries(stats.elements_by_type || {}).map(([type, count]) => (
                <Badge key={type} color={elementTypeColors[type as ElementType]} size="sm">
                  {elementTypeLabels[type as ElementType]}: {count}
                </Badge>
              ))}
            </Flex>
          </Card>
        </Grid>
      )}

      {/* Main Content */}
      <TabGroup>
        <TabList>
          <Tab icon={Network}>Hierarquia</Tab>
          <Tab icon={FileText}>Templates ({templates.length})</Tab>
        </TabList>

        <TabPanels>
          {/* Hierarchy Tab */}
          <TabPanel>
            {loading ? (
              <Card className="mt-6">
                <Flex justifyContent="center" className="py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <Text className="ml-3">Carregando...</Text>
                </Flex>
              </Card>
            ) : (
              <Grid numItemsSm={1} numItemsLg={2} className="gap-6 mt-6">
                {/* Tree View */}
                <Card className="h-[600px] overflow-hidden flex flex-col">
                  <div className="mb-4">
                    <TextInput
                      icon={Search}
                      placeholder="Pesquisar elementos..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <div className="flex-1 overflow-auto">
                    {filteredHierarchy.length === 0 ? (
                      <div className="text-center py-12">
                        <Network className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                        <Text>{searchQuery ? 'Nenhum elemento encontrado' : 'Nenhum elemento cadastrado'}</Text>
                        <Button
                          variant="secondary"
                          icon={Wrench}
                          className="mt-4"
                          onClick={handleBuildFromTags}
                        >
                          Construir de Tags
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-0.5">
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
                      </div>
                    )}
                  </div>
                </Card>

                {/* Details Panel */}
                <Card className="h-[600px] overflow-auto">
                  {selectedElement ? (
                    <div>
                      {/* Breadcrumbs */}
                      <div className="flex items-center gap-1 text-sm text-gray-500 mb-4 flex-wrap">
                        {getBreadcrumbs().map((part, idx) => (
                          <React.Fragment key={idx}>
                            {idx > 0 && <ChevronRight className="w-3 h-3" />}
                            <span className="hover:text-blue-600 cursor-pointer">{part}</span>
                          </React.Fragment>
                        ))}
                      </div>

                      {/* Element Header */}
                      <Flex alignItems="start" className="gap-4 mb-6">
                        <div className={`
                          w-12 h-12 rounded-lg flex items-center justify-center
                          bg-${elementTypeColors[selectedElement.element_type]}-100
                          text-${elementTypeColors[selectedElement.element_type]}-600
                        `}>
                          {elementTypeIcons[selectedElement.element_type]}
                        </div>
                        <div className="flex-1">
                          <Title>{selectedElement.name}</Title>
                          <Flex className="gap-2 mt-1">
                            <Badge color={elementTypeColors[selectedElement.element_type]}>
                              {elementTypeLabels[selectedElement.element_type]}
                            </Badge>
                            {selectedElement.template_id && (
                              <Badge color="gray">Usa Template</Badge>
                            )}
                          </Flex>
                          <Text className="mt-1 text-xs text-gray-400">ID: {selectedElement.id}</Text>
                        </div>
                      </Flex>

                      {selectedElement.description && (
                        <Text className="mb-4">{selectedElement.description}</Text>
                      )}

                      <Divider />

                      {/* Attributes */}
                      <Flex alignItems="center" justifyContent="between" className="my-4">
                        <Flex alignItems="center" className="gap-2">
                          <Tag className="w-5 h-5 text-gray-500" />
                          <Title className="text-base">Atributos ({selectedElement.attributes?.length || 0})</Title>
                        </Flex>
                        <Button
                          size="xs"
                          variant="secondary"
                          icon={Plus}
                          onClick={handleOpenAddTagModal}
                        >
                          Adicionar Tag
                        </Button>
                      </Flex>

                      {selectedElement.attributes && selectedElement.attributes.length > 0 ? (
                        <Table>
                          <TableHead>
                            <TableRow>
                              <TableHeaderCell>Nome</TableHeaderCell>
                              <TableHeaderCell>Valor</TableHeaderCell>
                              <TableHeaderCell>Unid.</TableHeaderCell>
                              <TableHeaderCell>Qual.</TableHeaderCell>
                              <TableHeaderCell>Ações</TableHeaderCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {selectedElement.attributes.map((attr) => (
                              <TableRow key={attr.id}>
                                <TableCell>
                                  <Text className="font-medium">{attr.name}</Text>
                                  {attr.tag_id && (
                                    <Text className="text-xs text-gray-400">{attr.tag_id}</Text>
                                  )}
                                </TableCell>
                                <TableCell>
                                  <Text className="font-mono">
                                    {attr.current_value !== null && attr.current_value !== undefined
                                      ? typeof attr.current_value === 'number'
                                        ? attr.current_value.toFixed(2)
                                        : String(attr.current_value)
                                      : '-'}
                                  </Text>
                                </TableCell>
                                <TableCell>
                                  <Text>{attr.uom || '-'}</Text>
                                </TableCell>
                                <TableCell>
                                  {getQualityIcon(attr.current_quality)}
                                </TableCell>
                                <TableCell>
                                  <button
                                    className="p-1 hover:bg-red-100 rounded text-red-500"
                                    onClick={() => handleRemoveAttribute(attr.id)}
                                    title="Remover atributo"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      ) : (
                        <div className="text-center py-6">
                          <Link className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                          <Text className="text-gray-400">Nenhum atributo configurado</Text>
                          <Button
                            size="xs"
                            variant="secondary"
                            icon={Plus}
                            className="mt-2"
                            onClick={handleOpenAddTagModal}
                          >
                            Adicionar Tag
                          </Button>
                        </div>
                      )}

                      {/* Children count */}
                      {selectedElement.children && selectedElement.children.length > 0 && (
                        <>
                          <Divider className="my-4" />
                          <Text className="text-sm text-gray-500">
                            {selectedElement.children.length} elemento(s) filho(s)
                          </Text>
                        </>
                      )}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full text-gray-400">
                      <Network className="w-16 h-16 mb-4 opacity-50" />
                      <Text>Selecione um elemento na árvore para ver detalhes</Text>
                    </div>
                  )}
                </Card>
              </Grid>
            )}
          </TabPanel>

          {/* Templates Tab */}
          <TabPanel>
            <Card className="mt-6">
              <Flex justifyContent="between" alignItems="center" className="mb-6">
                <Title>Templates de Elementos</Title>
                <Button variant="secondary" icon={FileText} disabled>
                  Novo Template
                </Button>
              </Flex>

              {templates.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <Text>Nenhum template cadastrado</Text>
                </div>
              ) : (
                <Grid numItemsSm={1} numItemsMd={2} numItemsLg={3} className="gap-4">
                  {templates.map((template) => (
                    <Card key={template.id} className="border hover:border-blue-300 transition-colors">
                      <Flex alignItems="start" className="gap-3">
                        <div className={`
                          w-10 h-10 rounded-lg flex items-center justify-center
                          bg-${elementTypeColors[template.element_type]}-100
                          text-${elementTypeColors[template.element_type]}-600
                        `}>
                          {elementTypeIcons[template.element_type]}
                        </div>
                        <div className="flex-1">
                          <Text className="font-semibold">{template.name}</Text>
                          {template.description && (
                            <Text className="text-sm text-gray-500 mt-1">{template.description}</Text>
                          )}
                          <Flex className="gap-2 mt-2 flex-wrap">
                            <Badge size="xs" color={elementTypeColors[template.element_type]}>
                              {elementTypeLabels[template.element_type]}
                            </Badge>
                            <Badge size="xs" color="gray">
                              {template.attributes?.length || 0} atributos
                            </Badge>
                            {template.elements_count !== undefined && template.elements_count > 0 && (
                              <Badge size="xs" color="blue">
                                {template.elements_count} em uso
                              </Badge>
                            )}
                          </Flex>
                        </div>
                      </Flex>
                    </Card>
                  ))}
                </Grid>
              )}
            </Card>
          </TabPanel>
        </TabPanels>
      </TabGroup>

      {/* Add Tag Modal */}
      {showAddTagModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
            <Flex justifyContent="between" alignItems="center" className="mb-4">
              <Title>Selecionar Tag para Vincular</Title>
              <button
                className="p-1 hover:bg-gray-100 rounded"
                onClick={() => setShowAddTagModal(false)}
              >
                <XCircle className="w-5 h-5 text-gray-500" />
              </button>
            </Flex>

            {/* Filters */}
            <Flex className="gap-4 mb-4">
              <div className="flex-1">
                <TextInput
                  icon={Search}
                  placeholder="Pesquisar tags..."
                  value={tagSearchQuery}
                  onChange={(e) => setTagSearchQuery(e.target.value)}
                />
              </div>
              <select
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                value={selectedAdapter}
                onChange={(e) => setSelectedAdapter(e.target.value)}
              >
                <option value="">Todos Adaptadores</option>
                {availableAdapters.map((adapter) => (
                  <option key={adapter} value={adapter}>{adapter}</option>
                ))}
              </select>
            </Flex>

            {/* Tags List */}
            <div className="flex-1 overflow-auto border rounded-lg">
              {filteredAvailableTags.length === 0 ? (
                <div className="text-center py-8">
                  <Tag className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                  <Text className="text-gray-400">Nenhum tag encontrado</Text>
                </div>
              ) : (
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableHeaderCell>Nome</TableHeaderCell>
                      <TableHeaderCell>Endereço</TableHeaderCell>
                      <TableHeaderCell>Adaptador</TableHeaderCell>
                      <TableHeaderCell>Tipo</TableHeaderCell>
                      <TableHeaderCell>Ação</TableHeaderCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredAvailableTags.slice(0, 50).map((tag) => (
                      <TableRow key={tag.tag_id} className="hover:bg-gray-50">
                        <TableCell>
                          <Text className="font-medium">{tag.tag_name}</Text>
                          <Text className="text-xs text-gray-400">{tag.tag_id}</Text>
                        </TableCell>
                        <TableCell>
                          <Text className="text-xs font-mono">{tag.address}</Text>
                        </TableCell>
                        <TableCell>
                          <Badge size="xs" color="gray">{tag.adapter_id}</Badge>
                        </TableCell>
                        <TableCell>
                          <Text className="text-xs">{tag.data_type}</Text>
                        </TableCell>
                        <TableCell>
                          <Button
                            size="xs"
                            variant="secondary"
                            icon={Plus}
                            loading={addingTag}
                            onClick={() => handleAddTag(tag)}
                          >
                            Adicionar
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
              {filteredAvailableTags.length > 50 && (
                <Text className="text-center py-2 text-gray-400 text-sm">
                  Mostrando 50 de {filteredAvailableTags.length} tags. Refine sua busca.
                </Text>
              )}
            </div>

            {/* Footer */}
            <Flex justifyContent="end" className="mt-4">
              <Button variant="secondary" onClick={() => setShowAddTagModal(false)}>
                Fechar
              </Button>
            </Flex>
          </Card>
        </div>
      )}

      {/* Create Element Modal */}
      {showCreateElementModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-lg">
            <Flex justifyContent="between" alignItems="center" className="mb-4">
              <Title>Criar Novo Elemento</Title>
              <button
                className="p-1 hover:bg-gray-100 rounded"
                onClick={() => setShowCreateElementModal(false)}
              >
                <XCircle className="w-5 h-5 text-gray-500" />
              </button>
            </Flex>

            <div className="space-y-4">
              {/* Nome */}
              <div>
                <Text className="mb-1 font-medium">Nome *</Text>
                <TextInput
                  placeholder="Ex: Silo1, Motor2, Compressor3"
                  value={newElementName}
                  onChange={(e) => setNewElementName(e.target.value)}
                />
              </div>

              {/* Descrição */}
              <div>
                <Text className="mb-1 font-medium">Descrição</Text>
                <TextInput
                  placeholder="Descrição do elemento"
                  value={newElementDescription}
                  onChange={(e) => setNewElementDescription(e.target.value)}
                />
              </div>

              {/* Tipo */}
              <div>
                <Text className="mb-1 font-medium">Tipo *</Text>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  value={newElementType}
                  onChange={(e) => setNewElementType(e.target.value as ElementType)}
                >
                  <option value="plant">Planta</option>
                  <option value="area">Área</option>
                  <option value="equipment_group">Grupo de Equipamentos</option>
                  <option value="equipment">Equipamento</option>
                  <option value="component">Componente</option>
                </select>
              </div>

              {/* Elemento Pai */}
              <div>
                <Text className="mb-1 font-medium">Elemento Pai (opcional)</Text>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  value={newElementParentId}
                  onChange={(e) => setNewElementParentId(e.target.value)}
                >
                  <option value="">-- Raiz (sem pai) --</option>
                  {allElements.map((el) => (
                    <option key={el.id} value={el.id}>
                      {el.path || el.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Footer */}
            <Flex justifyContent="end" className="mt-6 gap-2">
              <Button variant="secondary" onClick={() => setShowCreateElementModal(false)}>
                Cancelar
              </Button>
              <Button
                loading={creatingElement}
                onClick={handleCreateElement}
              >
                Criar Elemento
              </Button>
            </Flex>
          </Card>
        </div>
      )}
    </div>
  );
};

export default TremorAssetFramework;
