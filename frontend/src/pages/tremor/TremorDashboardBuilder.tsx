/**
 * 🛠️ Dashboard Builder - Tremor Professional
 * ============================================
 *
 * Visual dashboard builder with drag-and-drop widgets
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Title,
  Text,
  Flex,
  Grid,
  Badge,
  Button,
  TextInput,
  Select,
  SelectItem,
  NumberInput,
  Tab,
  TabGroup,
  TabList,
  TabPanel,
  TabPanels,
} from '@tremor/react';
import {
  LayoutDashboard,
  Save,
  ArrowLeft,
  Plus,
  Trash2,
  Settings,
  BarChart3,
  LineChart,
  PieChart,
  Gauge,
  Table,
  AlertTriangle,
  Activity,
  Thermometer,
  Zap,
  GripVertical,
  X,
  Check,
  Eye,
} from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import apiClient from '../../api/client';

// Widget types available
const WIDGET_TYPES = [
  { id: 'line_chart', name: 'Gráfico de Linha', icon: LineChart, description: 'Tendência temporal' },
  { id: 'bar_chart', name: 'Gráfico de Barras', icon: BarChart3, description: 'Comparação de valores' },
  { id: 'pie_chart', name: 'Gráfico de Pizza', icon: PieChart, description: 'Distribuição percentual' },
  { id: 'gauge', name: 'Gauge/Velocímetro', icon: Gauge, description: 'Valor atual com limites' },
  { id: 'kpi', name: 'KPI Card', icon: Activity, description: 'Indicador numérico' },
  { id: 'table', name: 'Tabela', icon: Table, description: 'Dados tabulares' },
  { id: 'alarm_list', name: 'Lista de Alarmes', icon: AlertTriangle, description: 'Alarmes ativos' },
];

// Widget sizes
const WIDGET_SIZES = [
  { id: 'small', name: 'Pequeno', cols: 1 },
  { id: 'medium', name: 'Médio', cols: 2 },
  { id: 'large', name: 'Grande', cols: 3 },
  { id: 'full', name: 'Largura Total', cols: 4 },
];

interface Tag {
  tag_id: string;
  name: string;
  unit?: string;
  description?: string;
}

interface Widget {
  id: string;
  type: string;
  title: string;
  size: string;
  config: {
    tag_ids?: string[];
    time_range?: string;
    refresh_interval?: number;
    show_legend?: boolean;
    min_value?: number;
    max_value?: number;
    thresholds?: { value: number; color: string }[];
  };
}

interface Dashboard {
  id?: string;
  name: string;
  description: string;
  module: string;
  is_public: boolean;
  layout: Widget[];
}

const moduleOptions = [
  { value: 'operations', label: 'Operações' },
  { value: 'maintenance', label: 'Manutenção' },
  { value: 'quality', label: 'Qualidade' },
  { value: 'executive', label: 'Executivo' },
  { value: 'energy', label: 'Energia' },
  { value: 'analytics', label: 'Analytics' },
];

export const TremorDashboardBuilder: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const dashboardId = searchParams.get('id');

  const [dashboard, setDashboard] = useState<Dashboard>({
    name: '',
    description: '',
    module: 'operations',
    is_public: false,
    layout: [],
  });
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedWidget, setSelectedWidget] = useState<string | null>(null);
  const [showAddWidget, setShowAddWidget] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [tagSearchTerm, setTagSearchTerm] = useState('');
  const [showTagDropdown, setShowTagDropdown] = useState(false);

  // Fetch dashboard if editing
  useEffect(() => {
    if (dashboardId) {
      fetchDashboard(dashboardId);
    }
    fetchTags();
  }, [dashboardId]);

  const fetchDashboard = async (id: string) => {
    try {
      setLoading(true);
      const response = await apiClient.get(`/api/v1/dashboards/${id}`);
      const data = response.data;
      setDashboard({
        id: data.id,
        name: data.name,
        description: data.description || '',
        module: data.module,
        is_public: data.is_public,
        layout: data.layout_config?.widgets || data.widgets || [],
      });
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      // Create new if not found
    } finally {
      setLoading(false);
    }
  };

  const fetchTags = async () => {
    try {
      const response = await apiClient.get('/api/v1/timeseries/tags/active');
      const tags = response.data?.tags || response.data || [];
      setAvailableTags(tags.map((t: any) => ({
        tag_id: t.tag_id || t.id,
        name: t.name || t.tag_id || t.id,
        unit: t.unit,
        description: t.description,
      })));
    } catch (error) {
      console.error('Error fetching tags:', error);
    }
  };

  const handleSave = async () => {
    if (!dashboard.name) {
      alert('Por favor, informe o nome do dashboard');
      return;
    }

    try {
      setSaving(true);
      const payload = {
        name: dashboard.name,
        description: dashboard.description,
        module: dashboard.module,
        is_public: dashboard.is_public,
        layout_config: { widgets: dashboard.layout },
      };

      if (dashboard.id) {
        await apiClient.put(`/api/v1/dashboards/${dashboard.id}`, payload);
      } else {
        const response = await apiClient.post('/api/v1/dashboards', payload);
        setDashboard(prev => ({ ...prev, id: response.data.id }));
      }
      setHasChanges(false);
      alert('Dashboard salvo com sucesso!');
    } catch (error) {
      console.error('Error saving dashboard:', error);
      alert('Erro ao salvar dashboard');
    } finally {
      setSaving(false);
    }
  };

  const addWidget = (type: string) => {
    const widgetType = WIDGET_TYPES.find(w => w.id === type);
    const newWidget: Widget = {
      id: `widget_${Date.now()}`,
      type,
      title: widgetType?.name || 'Novo Widget',
      size: 'medium',
      config: {
        tag_ids: [],
        time_range: '1h',
        refresh_interval: 30,
        show_legend: true,
      },
    };
    setDashboard(prev => ({
      ...prev,
      layout: [...prev.layout, newWidget],
    }));
    setSelectedWidget(newWidget.id);
    setShowAddWidget(false);
    setHasChanges(true);
  };

  const updateWidget = (widgetId: string, updates: Partial<Widget>) => {
    setDashboard(prev => ({
      ...prev,
      layout: prev.layout.map(w =>
        w.id === widgetId ? { ...w, ...updates } : w
      ),
    }));
    setHasChanges(true);
  };

  const removeWidget = (widgetId: string) => {
    setDashboard(prev => ({
      ...prev,
      layout: prev.layout.filter(w => w.id !== widgetId),
    }));
    if (selectedWidget === widgetId) {
      setSelectedWidget(null);
    }
    setHasChanges(true);
  };

  const getWidgetIcon = (type: string) => {
    const widget = WIDGET_TYPES.find(w => w.id === type);
    const Icon = widget?.icon || BarChart3;
    return <Icon className="w-5 h-5" />;
  };

  const selectedWidgetData = dashboard.layout.find(w => w.id === selectedWidget);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <Flex justifyContent="between" alignItems="center">
          <Flex className="gap-4" alignItems="center">
            <Button
              variant="secondary"
              icon={ArrowLeft}
              onClick={() => navigate('/dashboards')}
            >
              Voltar
            </Button>
            <div>
              <Title className="text-xl">
                {dashboard.id ? 'Editar Dashboard' : 'Novo Dashboard'}
              </Title>
              <Text className="text-gray-500">
                Arraste widgets para construir seu dashboard
              </Text>
            </div>
          </Flex>
          <Flex className="gap-2">
            {hasChanges && (
              <Badge color="yellow" size="sm">Alterações não salvas</Badge>
            )}
            <Button
              variant="secondary"
              icon={Eye}
              onClick={() => dashboard.id && navigate(`/dashboards/${dashboard.id}`)}
              disabled={!dashboard.id}
            >
              Visualizar
            </Button>
            <Button
              icon={Save}
              onClick={handleSave}
              loading={saving}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              Salvar
            </Button>
          </Flex>
        </Flex>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Widget Library */}
        <div className="w-64 bg-gray-50 border-r overflow-y-auto p-4">
          <Text className="font-semibold text-gray-700 mb-3">Adicionar Widget</Text>
          <div className="space-y-2">
            {WIDGET_TYPES.map((widget) => {
              const Icon = widget.icon;
              return (
                <button
                  key={widget.id}
                  onClick={() => addWidget(widget.id)}
                  className="w-full p-3 bg-white border rounded-lg hover:border-blue-500 hover:shadow-sm transition-all text-left group"
                >
                  <Flex alignItems="center" className="gap-3">
                    <div className="p-2 bg-blue-50 rounded-lg group-hover:bg-blue-100">
                      <Icon className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <Text className="font-medium text-gray-800">{widget.name}</Text>
                      <Text className="text-xs text-gray-500">{widget.description}</Text>
                    </div>
                  </Flex>
                </button>
              );
            })}
          </div>
        </div>

        {/* Center - Canvas */}
        <div className="flex-1 overflow-y-auto p-6 bg-gray-100">
          {/* Dashboard Info */}
          <Card className="mb-6">
            <Grid numItemsMd={3} className="gap-4">
              <div>
                <Text className="text-sm font-medium text-gray-700 mb-1">Nome do Dashboard</Text>
                <TextInput
                  placeholder="Ex: Monitoramento Operacional"
                  value={dashboard.name}
                  onChange={(e) => {
                    setDashboard(prev => ({ ...prev, name: e.target.value }));
                    setHasChanges(true);
                  }}
                />
              </div>
              <div>
                <Text className="text-sm font-medium text-gray-700 mb-1">Módulo</Text>
                <Select
                  value={dashboard.module}
                  onValueChange={(v) => {
                    setDashboard(prev => ({ ...prev, module: v }));
                    setHasChanges(true);
                  }}
                >
                  {moduleOptions.map(opt => (
                    <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                  ))}
                </Select>
              </div>
              <div>
                <Text className="text-sm font-medium text-gray-700 mb-1">Descrição</Text>
                <TextInput
                  placeholder="Descrição opcional"
                  value={dashboard.description}
                  onChange={(e) => {
                    setDashboard(prev => ({ ...prev, description: e.target.value }));
                    setHasChanges(true);
                  }}
                />
              </div>
            </Grid>
          </Card>

          {/* Widgets Grid */}
          {dashboard.layout.length === 0 ? (
            <Card className="p-12 text-center border-2 border-dashed">
              <LayoutDashboard className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <Title className="text-gray-500">Dashboard Vazio</Title>
              <Text className="text-gray-400 mt-2">
                Clique em um widget no painel lateral para adicionar
              </Text>
            </Card>
          ) : (
            <Grid numItemsMd={2} numItemsLg={4} className="gap-4">
              {dashboard.layout.map((widget) => {
                const colSpan = WIDGET_SIZES.find(s => s.id === widget.size)?.cols || 2;
                return (
                  <Card
                    key={widget.id}
                    className={`p-4 cursor-pointer transition-all ${
                      selectedWidget === widget.id
                        ? 'ring-2 ring-blue-500 shadow-lg'
                        : 'hover:shadow-md'
                    }`}
                    style={{ gridColumn: `span ${colSpan}` }}
                    onClick={() => setSelectedWidget(widget.id)}
                  >
                    <Flex justifyContent="between" alignItems="start">
                      <Flex alignItems="center" className="gap-2">
                        <div className="p-1.5 bg-gray-100 rounded">
                          {getWidgetIcon(widget.type)}
                        </div>
                        <div>
                          <Text className="font-medium">{widget.title}</Text>
                          <Text className="text-xs text-gray-500">
                            {WIDGET_TYPES.find(w => w.id === widget.type)?.name}
                          </Text>
                        </div>
                      </Flex>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeWidget(widget.id);
                        }}
                        className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </Flex>

                    {/* Widget Preview */}
                    <div className="mt-4 h-32 bg-gray-50 rounded-lg flex items-center justify-center">
                      {widget.config.tag_ids && widget.config.tag_ids.length > 0 ? (
                        <div className="text-center">
                          <Badge color="blue" size="sm">
                            {widget.config.tag_ids.length} tag(s)
                          </Badge>
                          <Text className="text-xs text-gray-400 mt-1">
                            {widget.config.time_range || '1h'}
                          </Text>
                        </div>
                      ) : (
                        <Text className="text-gray-400 text-sm">
                          Configure as tags
                        </Text>
                      )}
                    </div>
                  </Card>
                );
              })}
            </Grid>
          )}
        </div>

        {/* Right Panel - Widget Config */}
        {selectedWidgetData && (
          <div className="w-80 bg-white border-l overflow-y-auto p-4">
            <Flex justifyContent="between" alignItems="center" className="mb-4">
              <Text className="font-semibold text-gray-700">Configurar Widget</Text>
              <button
                onClick={() => setSelectedWidget(null)}
                className="p-1 text-gray-400 hover:text-gray-600"
              >
                <X className="w-4 h-4" />
              </button>
            </Flex>

            <div className="space-y-4">
              {/* Title */}
              <div>
                <Text className="text-sm font-medium text-gray-700 mb-1">Título</Text>
                <TextInput
                  value={selectedWidgetData.title}
                  onChange={(e) => updateWidget(selectedWidgetData.id, { title: e.target.value })}
                />
              </div>

              {/* Size */}
              <div>
                <Text className="text-sm font-medium text-gray-700 mb-1">Tamanho</Text>
                <Select
                  value={selectedWidgetData.size}
                  onValueChange={(v) => updateWidget(selectedWidgetData.id, { size: v })}
                >
                  {WIDGET_SIZES.map(size => (
                    <SelectItem key={size.id} value={size.id}>{size.name}</SelectItem>
                  ))}
                </Select>
              </div>

              {/* Tags Selection */}
              <div>
                <Text className="text-sm font-medium text-gray-700 mb-1">
                  Tags ({selectedWidgetData.config.tag_ids?.length || 0} selecionadas)
                </Text>

                {/* Selected tags as chips */}
                {selectedWidgetData.config.tag_ids && selectedWidgetData.config.tag_ids.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-2">
                    {selectedWidgetData.config.tag_ids.map((tagId) => {
                      const tagInfo = availableTags.find(t => t.tag_id === tagId);
                      return (
                        <span
                          key={tagId}
                          className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs"
                        >
                          {tagInfo?.name || tagId}
                          <button
                            onClick={() => {
                              const newTags = selectedWidgetData.config.tag_ids?.filter(t => t !== tagId) || [];
                              updateWidget(selectedWidgetData.id, {
                                config: { ...selectedWidgetData.config, tag_ids: newTags }
                              });
                            }}
                            className="hover:bg-blue-200 rounded p-0.5"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </span>
                      );
                    })}
                  </div>
                )}

                {/* Search dropdown */}
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Buscar tags..."
                    value={tagSearchTerm}
                    onChange={(e) => {
                      setTagSearchTerm(e.target.value);
                      setShowTagDropdown(true);
                    }}
                    onFocus={() => setShowTagDropdown(true)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />

                  {showTagDropdown && (
                    <>
                      <div
                        className="fixed inset-0 z-40"
                        onClick={() => setShowTagDropdown(false)}
                      />
                      <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                        {availableTags
                          .filter(tag =>
                            tag.name.toLowerCase().includes(tagSearchTerm.toLowerCase()) ||
                            tag.tag_id.toLowerCase().includes(tagSearchTerm.toLowerCase())
                          )
                          .slice(0, 30)
                          .map((tag) => {
                            const isSelected = selectedWidgetData.config.tag_ids?.includes(tag.tag_id);
                            return (
                              <button
                                key={tag.tag_id}
                                onClick={() => {
                                  const currentTags = selectedWidgetData.config.tag_ids || [];
                                  const newTags = isSelected
                                    ? currentTags.filter(t => t !== tag.tag_id)
                                    : [...currentTags, tag.tag_id];
                                  updateWidget(selectedWidgetData.id, {
                                    config: { ...selectedWidgetData.config, tag_ids: newTags }
                                  });
                                  setTagSearchTerm('');
                                }}
                                className={`w-full px-3 py-2 text-left text-sm flex items-center justify-between hover:bg-gray-50 border-b border-gray-100 last:border-0 ${
                                  isSelected ? 'bg-blue-50' : ''
                                }`}
                              >
                                <div className="flex items-center gap-2">
                                  {isSelected && <Check className="w-4 h-4 text-blue-600" />}
                                  <span className={isSelected ? 'font-medium text-blue-700' : 'text-gray-700'}>
                                    {tag.name}
                                  </span>
                                  {tag.unit && <span className="text-gray-400 text-xs">({tag.unit})</span>}
                                </div>
                              </button>
                            );
                          })}
                        {availableTags.filter(tag =>
                          tag.name.toLowerCase().includes(tagSearchTerm.toLowerCase()) ||
                          tag.tag_id.toLowerCase().includes(tagSearchTerm.toLowerCase())
                        ).length === 0 && (
                          <div className="p-3 text-sm text-gray-500 text-center">
                            Nenhuma tag encontrada
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Time Range */}
              <div>
                <Text className="text-sm font-medium text-gray-700 mb-1">Período</Text>
                <Select
                  value={selectedWidgetData.config.time_range || '1h'}
                  onValueChange={(v) => updateWidget(selectedWidgetData.id, {
                    config: { ...selectedWidgetData.config, time_range: v }
                  })}
                >
                  <SelectItem value="15m">15 minutos</SelectItem>
                  <SelectItem value="1h">1 hora</SelectItem>
                  <SelectItem value="6h">6 horas</SelectItem>
                  <SelectItem value="24h">24 horas</SelectItem>
                  <SelectItem value="7d">7 dias</SelectItem>
                  <SelectItem value="30d">30 dias</SelectItem>
                </Select>
              </div>

              {/* Refresh Interval */}
              <div>
                <Text className="text-sm font-medium text-gray-700 mb-1">Atualização (seg)</Text>
                <NumberInput
                  value={selectedWidgetData.config.refresh_interval || 30}
                  onValueChange={(v) => updateWidget(selectedWidgetData.id, {
                    config: { ...selectedWidgetData.config, refresh_interval: v }
                  })}
                  min={5}
                  max={300}
                />
              </div>

              {/* Delete Widget */}
              <Button
                variant="secondary"
                color="red"
                icon={Trash2}
                className="w-full mt-4"
                onClick={() => removeWidget(selectedWidgetData.id)}
              >
                Remover Widget
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TremorDashboardBuilder;
