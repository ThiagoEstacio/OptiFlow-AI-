/**
 * 🛠️ Dashboard Builder - Tremor Professional
 * ============================================
 *
 * Visual dashboard builder with drag-and-drop and resize support
 * Uses react-grid-layout for responsive, customizable layouts
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  Title,
  Text,
  Flex,
  Badge,
  Button,
  TextInput,
  Select,
  SelectItem,
  NumberInput,
} from '@tremor/react';
import {
  LayoutDashboard,
  Save,
  ArrowLeft,
  Trash2,
  BarChart3,
  LineChart,
  PieChart,
  Gauge,
  Table,
  AlertTriangle,
  Activity,
  Zap,
  X,
  Check,
  Eye,
  ChevronDown,
  ChevronRight,
  Droplets,
  Settings,
  TrendingUp,
  Heart,
  Thermometer,
  Wind,
  AreaChart,
  CircleDot,
  Lock,
  Unlock,
} from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import apiClient from '../../api/client';
import WidgetRenderer from '../../components/Dashboard/WidgetRenderer';

// Widget categories with types
const WIDGET_CATEGORIES = [
  {
    id: 'visualization',
    name: 'Visualização',
    icon: BarChart3,
    widgets: [
      { id: 'kpi_card', name: 'KPI Card', icon: Activity, description: 'Indicador com tendência', defaultW: 2, defaultH: 2 },
      { id: 'stat', name: 'Estatística', icon: TrendingUp, description: 'Valor grande destacado', defaultW: 2, defaultH: 2 },
      { id: 'gauge', name: 'Gauge', icon: Gauge, description: 'Velocímetro circular', defaultW: 3, defaultH: 3 },
      { id: 'bar_gauge', name: 'Bar Gauge', icon: BarChart3, description: 'Barra de progresso', defaultW: 2, defaultH: 2 },
    ],
  },
  {
    id: 'charts',
    name: 'Gráficos',
    icon: LineChart,
    widgets: [
      { id: 'line_chart', name: 'Linha', icon: LineChart, description: 'Tendência temporal', defaultW: 4, defaultH: 3 },
      { id: 'area_chart', name: 'Área', icon: AreaChart, description: 'Área preenchida', defaultW: 4, defaultH: 3 },
      { id: 'bar_chart', name: 'Barras', icon: BarChart3, description: 'Comparação de valores', defaultW: 3, defaultH: 3 },
      { id: 'pie_chart', name: 'Pizza', icon: PieChart, description: 'Distribuição', defaultW: 3, defaultH: 3 },
      { id: 'donut_chart', name: 'Donut', icon: CircleDot, description: 'Anel percentual', defaultW: 3, defaultH: 3 },
    ],
  },
  {
    id: 'industrial',
    name: 'Industrial',
    icon: Settings,
    widgets: [
      { id: 'process_status', name: 'Status Processo', icon: Settings, description: 'Estado operacional', defaultW: 2, defaultH: 2 },
      { id: 'motor_status', name: 'Status Motor', icon: Zap, description: 'Motor com RPM', defaultW: 2, defaultH: 3 },
      { id: 'tank_level', name: 'Nível Tanque', icon: Droplets, description: 'Nível de líquido', defaultW: 2, defaultH: 4 },
      { id: 'valve_status', name: 'Status Válvula', icon: Wind, description: 'Posição da válvula', defaultW: 2, defaultH: 3 },
      { id: 'oee', name: 'OEE', icon: TrendingUp, description: 'Eficiência geral', defaultW: 3, defaultH: 3 },
      { id: 'equipment_health', name: 'Saúde Equipamento', icon: Heart, description: 'MTBF/MTTR', defaultW: 3, defaultH: 3 },
    ],
  },
  {
    id: 'alerts',
    name: 'Alarmes',
    icon: AlertTriangle,
    widgets: [
      { id: 'active_alarms', name: 'Alarmes Ativos', icon: AlertTriangle, description: 'Lista de alarmes', defaultW: 4, defaultH: 4 },
    ],
  },
  {
    id: 'data',
    name: 'Dados',
    icon: Table,
    widgets: [
      { id: 'table', name: 'Tabela', icon: Table, description: 'Dados tabulares', defaultW: 6, defaultH: 4 },
      { id: 'heatmap', name: 'Mapa de Calor', icon: Thermometer, description: 'Matriz colorida', defaultW: 4, defaultH: 4 },
    ],
  },
];

// Flatten all widgets for lookup
const ALL_WIDGETS = WIDGET_CATEGORIES.flatMap(cat => cat.widgets);

// Time range options
const TIME_RANGES = [
  { value: '5m', label: '5 minutos' },
  { value: '15m', label: '15 minutos' },
  { value: '30m', label: '30 minutos' },
  { value: '1h', label: '1 hora' },
  { value: '6h', label: '6 horas' },
  { value: '24h', label: '24 horas' },
  { value: '7d', label: '7 dias' },
  { value: '30d', label: '30 dias' },
];

// Color presets
const COLOR_PRESETS = [
  { name: 'Azul', value: '#3B82F6' },
  { name: 'Verde', value: '#10B981' },
  { name: 'Amarelo', value: '#F59E0B' },
  { name: 'Vermelho', value: '#EF4444' },
  { name: 'Roxo', value: '#8B5CF6' },
  { name: 'Ciano', value: '#06B6D4' },
  { name: 'Rosa', value: '#EC4899' },
  { name: 'Laranja', value: '#F97316' },
];

interface Tag {
  tag_id: string;
  name: string;
  unit?: string;
  description?: string;
}

interface WidgetConfig {
  tag_ids?: string[];
  tagId?: string;
  tagName?: string;
  time_range?: string;
  refresh_interval?: number;
  min?: number;
  max?: number;
  unit?: string;
  decimals?: number;
  color?: string;
  showLegend?: boolean;
  showGrid?: boolean;
  thresholds?: { warning?: number; critical?: number };
  targetOEE?: number;
  showComponents?: boolean;
  showPercentage?: boolean;
  tankShape?: string;
  maxAlarms?: number;
  showSeverity?: boolean;
}

interface WidgetLayout {
  x: number;
  y: number;
  w: number;
  h: number;
  minW?: number;
  minH?: number;
}

interface Widget {
  id: string;
  type: string;
  title: string;
  config: WidgetConfig;
  layout: WidgetLayout;
}

interface Dashboard {
  id?: string;
  name: string;
  description: string;
  module: string;
  is_public: boolean;
  widgets: Widget[];
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
    widgets: [],
  });
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedWidget, setSelectedWidget] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [tagSearchTerm, setTagSearchTerm] = useState('');
  const [showTagDropdown, setShowTagDropdown] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(['visualization', 'industrial'])
  );
  const [isLayoutLocked, setIsLayoutLocked] = useState(false);

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

      // Convert old format to new format if needed
      const widgets = data.layout_config?.widgets || data.widgets || [];
      const convertedWidgets = widgets.map((w: any, index: number) => ({
        id: w.id,
        type: w.type,
        title: w.title,
        config: w.config || {},
        layout: w.layout || {
          x: (index % 4) * 3,
          y: Math.floor(index / 4) * 3,
          w: 3,
          h: 3,
          minW: 2,
          minH: 2,
        },
      }));

      setDashboard({
        id: data.id,
        name: data.name,
        description: data.description || '',
        module: data.module,
        is_public: data.is_public,
        widgets: convertedWidgets,
      });
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTags = async () => {
    try {
      // Fetch all tags from Gateway via backend proxy (235+ tags)
      const response = await apiClient.get('/api/v1/gateway-config/proxy/tags');
      const tags = response.data || [];
      setAvailableTags(tags.map((t: any) => ({
        tag_id: t.tag_id || t.id,
        name: t.tag_name || t.name || t.tag_id,
        unit: t.metadata?.engineering_units || t.unit || '',
        description: t.metadata?.description || t.description || '',
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
        layout_config: { widgets: dashboard.widgets },
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
    const widgetType = ALL_WIDGETS.find(w => w.id === type);

    // Find the lowest available position
    const maxY = dashboard.widgets.reduce((max, w) => Math.max(max, w.layout.y + w.layout.h), 0);

    const newWidget: Widget = {
      id: `widget_${Date.now()}`,
      type,
      title: widgetType?.name || 'Novo Widget',
      config: {
        tag_ids: [],
        time_range: '1h',
        refresh_interval: 30,
        color: '#3B82F6',
        decimals: 1,
        min: 0,
        max: 100,
        showLegend: true,
        showGrid: true,
        targetOEE: 85,
        showComponents: true,
        showPercentage: true,
        tankShape: 'rectangle',
        maxAlarms: 5,
        showSeverity: true,
      },
      layout: {
        x: 0,
        y: maxY,
        w: widgetType?.defaultW || 3,
        h: widgetType?.defaultH || 3,
        minW: 2,
        minH: 2,
      },
    };

    setDashboard(prev => ({
      ...prev,
      widgets: [...prev.widgets, newWidget],
    }));
    setSelectedWidget(newWidget.id);
    setHasChanges(true);
  };

  const updateWidget = (widgetId: string, updates: Partial<Widget>) => {
    setDashboard(prev => ({
      ...prev,
      widgets: prev.widgets.map(w =>
        w.id === widgetId ? { ...w, ...updates } : w
      ),
    }));
    setHasChanges(true);
  };

  const updateWidgetConfig = (widgetId: string, configUpdates: Partial<WidgetConfig>) => {
    setDashboard(prev => ({
      ...prev,
      widgets: prev.widgets.map(w =>
        w.id === widgetId ? { ...w, config: { ...w.config, ...configUpdates } } : w
      ),
    }));
    setHasChanges(true);
  };

  const removeWidget = (widgetId: string) => {
    setDashboard(prev => ({
      ...prev,
      widgets: prev.widgets.filter(w => w.id !== widgetId),
    }));
    if (selectedWidget === widgetId) {
      setSelectedWidget(null);
    }
    setHasChanges(true);
  };


  const toggleCategory = (categoryId: string) => {
    setExpandedCategories(prev => {
      const next = new Set(prev);
      if (next.has(categoryId)) {
        next.delete(categoryId);
      } else {
        next.add(categoryId);
      }
      return next;
    });
  };

  const getWidgetIcon = (type: string) => {
    const widget = ALL_WIDGETS.find(w => w.id === type);
    const Icon = widget?.icon || BarChart3;
    return <Icon className="w-4 h-4" />;
  };

  const selectedWidgetData = dashboard.widgets.find(w => w.id === selectedWidget);

  // Get widget size class based on layout
  const getWidgetSizeClass = (widget: Widget) => {
    const w = widget.layout?.w || 3;
    const h = widget.layout?.h || 3;

    // Map grid columns to Tailwind classes
    const colSpanMap: Record<number, string> = {
      1: 'col-span-1',
      2: 'col-span-2',
      3: 'col-span-3',
      4: 'col-span-4',
      5: 'col-span-5',
      6: 'col-span-6',
    };

    const colSpan = colSpanMap[Math.min(w, 6)] || 'col-span-3';
    const minHeight = `${h * 80}px`;

    return { colSpan, minHeight };
  };

  return (
    <div className="h-full flex flex-col bg-gray-100">
      {/* Header */}
      <div className="bg-white border-b px-6 py-3 flex-shrink-0">
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
              <Text className="text-gray-500 text-sm">
                Arraste e redimensione os widgets livremente
              </Text>
            </div>
          </Flex>
          <Flex className="gap-2" alignItems="center">
            {hasChanges && (
              <Badge color="yellow" size="sm">Alterações não salvas</Badge>
            )}
            <Button
              variant="secondary"
              icon={isLayoutLocked ? Lock : Unlock}
              onClick={() => setIsLayoutLocked(!isLayoutLocked)}
              tooltip={isLayoutLocked ? 'Desbloquear layout' : 'Bloquear layout'}
            >
              {isLayoutLocked ? 'Bloqueado' : 'Livre'}
            </Button>
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
        <div className="w-64 bg-white border-r overflow-y-auto flex-shrink-0">
          <div className="p-3">
            <Text className="font-semibold text-gray-700 mb-2 text-sm">Biblioteca de Widgets</Text>
            <Text className="text-xs text-gray-500 mb-3">Clique para adicionar ao dashboard</Text>

            {WIDGET_CATEGORIES.map((category) => {
              const CategoryIcon = category.icon;
              const isExpanded = expandedCategories.has(category.id);

              return (
                <div key={category.id} className="mb-1">
                  <button
                    onClick={() => toggleCategory(category.id)}
                    className="w-full flex items-center justify-between p-2 rounded hover:bg-gray-100 transition-colors"
                  >
                    <Flex alignItems="center" className="gap-2">
                      <CategoryIcon className="w-4 h-4 text-gray-600" />
                      <Text className="font-medium text-gray-700 text-sm">{category.name}</Text>
                      <Badge size="xs" color="gray">{category.widgets.length}</Badge>
                    </Flex>
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-gray-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-400" />
                    )}
                  </button>

                  {isExpanded && (
                    <div className="ml-2 space-y-1 mt-1">
                      {category.widgets.map((widget) => {
                        const Icon = widget.icon;
                        return (
                          <button
                            key={widget.id}
                            onClick={() => addWidget(widget.id)}
                            className="w-full p-2 bg-gray-50 border rounded hover:border-blue-400 hover:bg-blue-50 transition-all text-left group"
                          >
                            <Flex alignItems="center" className="gap-2">
                              <div className="p-1 bg-white rounded group-hover:bg-blue-100 border">
                                <Icon className="w-3 h-3 text-blue-600" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <Text className="text-xs font-medium text-gray-700 truncate">
                                  {widget.name}
                                </Text>
                              </div>
                            </Flex>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Center - Canvas */}
        <div className="flex-1 overflow-auto p-4">
          {/* Dashboard Info */}
          <Card className="mb-4 p-3">
            <div className="grid grid-cols-3 gap-3">
              <div>
                <Text className="text-xs font-medium text-gray-600 mb-1">Nome do Dashboard</Text>
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
                <Text className="text-xs font-medium text-gray-600 mb-1">Módulo</Text>
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
                <Text className="text-xs font-medium text-gray-600 mb-1">Descrição</Text>
                <TextInput
                  placeholder="Descrição opcional"
                  value={dashboard.description}
                  onChange={(e) => {
                    setDashboard(prev => ({ ...prev, description: e.target.value }));
                    setHasChanges(true);
                  }}
                />
              </div>
            </div>
          </Card>

          {/* Widgets Grid */}
          {dashboard.widgets.length === 0 ? (
            <Card className="p-12 text-center border-2 border-dashed bg-white">
              <LayoutDashboard className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <Title className="text-gray-500">Dashboard Vazio</Title>
              <Text className="text-gray-400 mt-2">
                Clique em um widget no painel lateral para adicionar
              </Text>
            </Card>
          ) : (
            <div className="bg-white rounded-lg border p-4 min-h-[600px]">
              <div className="grid grid-cols-6 gap-4">
                {dashboard.widgets.map((widget) => {
                  const widgetInfo = ALL_WIDGETS.find(w => w.id === widget.type);
                  const isSelected = selectedWidget === widget.id;
                  const { colSpan, minHeight } = getWidgetSizeClass(widget);

                  return (
                    <div
                      key={widget.id}
                      className={`${colSpan} bg-white rounded-lg border-2 overflow-hidden transition-all ${
                        isSelected
                          ? 'border-blue-500 shadow-lg'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      style={{ minHeight }}
                    >
                      {/* Widget Header */}
                      <div
                        className="flex items-center justify-between px-2 py-1 bg-gray-50 border-b"
                        onClick={() => setSelectedWidget(widget.id)}
                      >
                        <Flex alignItems="center" className="gap-1 flex-1 min-w-0">
                          <div style={{ color: widget.config.color }} className="flex-shrink-0">
                            {getWidgetIcon(widget.type)}
                          </div>
                          <Text className="text-xs font-medium text-gray-700 truncate">
                            {widget.title}
                          </Text>
                        </Flex>
                        <Flex className="gap-1 flex-shrink-0">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              removeWidget(widget.id);
                            }}
                            className="p-0.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </Flex>
                      </div>

                      {/* Widget Content */}
                      <div
                        className="h-[calc(100%-28px)] overflow-hidden"
                        onClick={() => setSelectedWidget(widget.id)}
                      >
                        {widget.config.tag_ids && widget.config.tag_ids.length > 0 ? (
                          <WidgetRenderer
                            widget={{
                              ...widget,
                              config: {
                                ...widget.config,
                                tagId: widget.config.tagId || widget.config.tag_ids?.[0],
                                tagName: widget.config.tagName || widget.config.tag_ids?.[0],
                              },
                              data_config: {
                                tagId: widget.config.tagId || widget.config.tag_ids?.[0],
                              },
                              display_config: {},
                            }}
                            isEditMode={true}
                          />
                        ) : (
                          <div className="h-full flex items-center justify-center bg-gray-50">
                            <div className="text-center p-2">
                              <div style={{ color: widget.config.color }} className="mb-1">
                                {widgetInfo?.icon ? <widgetInfo.icon className="w-6 h-6 mx-auto opacity-50" /> : null}
                              </div>
                              <Text className="text-gray-400 text-xs">
                                Configure as tags
                              </Text>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - Widget Config */}
        {selectedWidgetData && (
          <div className="w-72 bg-white border-l overflow-y-auto flex-shrink-0">
            <div className="p-3 border-b bg-gray-50">
              <Flex justifyContent="between" alignItems="center">
                <Flex alignItems="center" className="gap-2">
                  <div
                    className="p-1 rounded"
                    style={{ backgroundColor: `${selectedWidgetData.config.color}20` }}
                  >
                    <div style={{ color: selectedWidgetData.config.color }}>
                      {getWidgetIcon(selectedWidgetData.type)}
                    </div>
                  </div>
                  <div>
                    <Text className="font-semibold text-gray-700 text-sm">Configurar Widget</Text>
                    <Text className="text-xs text-gray-500">
                      {ALL_WIDGETS.find(w => w.id === selectedWidgetData.type)?.name}
                    </Text>
                  </div>
                </Flex>
                <button
                  onClick={() => setSelectedWidget(null)}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded hover:bg-gray-100"
                >
                  <X className="w-4 h-4" />
                </button>
              </Flex>
            </div>

            <div className="p-3 space-y-4">
              {/* General Section */}
              <div>
                <Text className="text-xs font-semibold text-gray-500 uppercase mb-2">Geral</Text>
                <div className="space-y-2">
                  <div>
                    <Text className="text-xs font-medium text-gray-600 mb-1">Título</Text>
                    <TextInput
                      value={selectedWidgetData.title}
                      onChange={(e) => updateWidget(selectedWidgetData.id, { title: e.target.value })}
                    />
                  </div>
                  <div>
                    <Text className="text-xs font-medium text-gray-600 mb-1">Cor</Text>
                    <div className="flex flex-wrap gap-1">
                      {COLOR_PRESETS.map((color) => (
                        <button
                          key={color.value}
                          onClick={() => updateWidgetConfig(selectedWidgetData.id, { color: color.value })}
                          className={`w-6 h-6 rounded-full border-2 transition-transform hover:scale-110 ${
                            selectedWidgetData.config.color === color.value
                              ? 'border-gray-800 scale-110'
                              : 'border-gray-200'
                          }`}
                          style={{ backgroundColor: color.value }}
                          title={color.name}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Data Section */}
              <div>
                <Text className="text-xs font-semibold text-gray-500 uppercase mb-2">Dados</Text>
                <div className="space-y-2">
                  {/* Tags Selection */}
                  <div>
                    <Text className="text-xs font-medium text-gray-600 mb-1">
                      Tags ({selectedWidgetData.config.tag_ids?.length || 0})
                    </Text>

                    {selectedWidgetData.config.tag_ids && selectedWidgetData.config.tag_ids.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-2">
                        {selectedWidgetData.config.tag_ids.map((tagId) => {
                          const tagInfo = availableTags.find(t => t.tag_id === tagId);
                          return (
                            <span
                              key={tagId}
                              className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-xs"
                            >
                              {tagInfo?.name || tagId}
                              <button
                                onClick={() => {
                                  const newTags = selectedWidgetData.config.tag_ids?.filter(t => t !== tagId) || [];
                                  updateWidgetConfig(selectedWidgetData.id, {
                                    tag_ids: newTags,
                                    tagId: newTags[0] || undefined,
                                    tagName: newTags[0] ? availableTags.find(t => t.tag_id === newTags[0])?.name : undefined,
                                  });
                                }}
                                className="hover:bg-blue-200 rounded"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </span>
                          );
                        })}
                      </div>
                    )}

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
                        className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />

                      {showTagDropdown && (
                        <>
                          <div
                            className="fixed inset-0 z-40"
                            onClick={() => setShowTagDropdown(false)}
                          />
                          <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded shadow-lg max-h-48 overflow-hidden flex flex-col">
                            <div className="max-h-36 overflow-y-auto">
                              {availableTags
                                .filter(tag =>
                                  tag.name.toLowerCase().includes(tagSearchTerm.toLowerCase()) ||
                                  tag.tag_id.toLowerCase().includes(tagSearchTerm.toLowerCase())
                                )
                                .slice(0, 20)
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
                                        updateWidgetConfig(selectedWidgetData.id, {
                                          tag_ids: newTags,
                                          tagId: newTags[0] || undefined,
                                          tagName: newTags[0] ? availableTags.find(t => t.tag_id === newTags[0])?.name : undefined,
                                        });
                                        setTagSearchTerm('');
                                      }}
                                      className={`w-full px-2 py-1.5 text-left text-xs flex items-center gap-2 hover:bg-gray-50 border-b border-gray-100 ${
                                        isSelected ? 'bg-blue-50' : ''
                                      }`}
                                    >
                                      <div className={`w-3 h-3 rounded border flex items-center justify-center ${
                                        isSelected ? 'bg-blue-600 border-blue-600' : 'border-gray-300'
                                      }`}>
                                        {isSelected && <Check className="w-2 h-2 text-white" />}
                                      </div>
                                      <span className={isSelected ? 'font-medium text-blue-700' : 'text-gray-700'}>
                                        {tag.name}
                                      </span>
                                      {tag.unit && <span className="text-gray-400">({tag.unit})</span>}
                                    </button>
                                  );
                                })}
                            </div>
                            <div className="p-1.5 bg-gray-50 border-t">
                              <Button
                                size="xs"
                                icon={Check}
                                onClick={() => {
                                  setShowTagDropdown(false);
                                  setTagSearchTerm('');
                                }}
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                              >
                                Confirmar ({selectedWidgetData.config.tag_ids?.length || 0})
                              </Button>
                            </div>
                          </div>
                        </>
                      )}
                    </div>

                    {/* Status indicator */}
                    <div className="mt-1 flex items-center gap-1 text-xs">
                      <div className={`w-1.5 h-1.5 rounded-full ${
                        selectedWidgetData.config.tag_ids?.length ? 'bg-green-500' : 'bg-amber-500'
                      }`}></div>
                      <span className={selectedWidgetData.config.tag_ids?.length ? 'text-green-700' : 'text-amber-700'}>
                        {selectedWidgetData.config.tag_ids?.length ? 'Tags configuradas' : 'Selecione tags'}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Text className="text-xs font-medium text-gray-600 mb-1">Unidade</Text>
                      <TextInput
                        placeholder="°C, bar..."
                        value={selectedWidgetData.config.unit || ''}
                        onChange={(e) => updateWidgetConfig(selectedWidgetData.id, { unit: e.target.value })}
                      />
                    </div>
                    <div>
                      <Text className="text-xs font-medium text-gray-600 mb-1">Decimais</Text>
                      <NumberInput
                        value={selectedWidgetData.config.decimals ?? 1}
                        onValueChange={(v) => updateWidgetConfig(selectedWidgetData.id, { decimals: v })}
                        min={0}
                        max={5}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Limits - for gauge/tank */}
              {['gauge', 'bar_gauge', 'tank_level'].includes(selectedWidgetData.type) && (
                <div>
                  <Text className="text-xs font-semibold text-gray-500 uppercase mb-2">Limites</Text>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Text className="text-xs font-medium text-gray-600 mb-1">Mínimo</Text>
                      <NumberInput
                        value={selectedWidgetData.config.min ?? 0}
                        onValueChange={(v) => updateWidgetConfig(selectedWidgetData.id, { min: v })}
                      />
                    </div>
                    <div>
                      <Text className="text-xs font-medium text-gray-600 mb-1">Máximo</Text>
                      <NumberInput
                        value={selectedWidgetData.config.max ?? 100}
                        onValueChange={(v) => updateWidgetConfig(selectedWidgetData.id, { max: v })}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* OEE specific */}
              {selectedWidgetData.type === 'oee' && (
                <div>
                  <Text className="text-xs font-semibold text-gray-500 uppercase mb-2">OEE</Text>
                  <div>
                    <Text className="text-xs font-medium text-gray-600 mb-1">Meta OEE (%)</Text>
                    <NumberInput
                      value={selectedWidgetData.config.targetOEE ?? 85}
                      onValueChange={(v) => updateWidgetConfig(selectedWidgetData.id, { targetOEE: v })}
                      min={0}
                      max={100}
                    />
                  </div>
                </div>
              )}

              {/* Time Range - for charts */}
              {['line_chart', 'area_chart', 'bar_chart'].includes(selectedWidgetData.type) && (
                <div>
                  <Text className="text-xs font-semibold text-gray-500 uppercase mb-2">Período</Text>
                  <Select
                    value={selectedWidgetData.config.time_range || '1h'}
                    onValueChange={(v) => updateWidgetConfig(selectedWidgetData.id, { time_range: v })}
                  >
                    {TIME_RANGES.map(tr => (
                      <SelectItem key={tr.value} value={tr.value}>{tr.label}</SelectItem>
                    ))}
                  </Select>
                </div>
              )}

              {/* Delete Widget */}
              <Button
                variant="secondary"
                color="red"
                icon={Trash2}
                size="xs"
                className="w-full"
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
