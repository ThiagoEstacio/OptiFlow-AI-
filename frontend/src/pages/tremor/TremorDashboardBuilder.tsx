/**
 * 🛠️ Dashboard Builder - Tremor Professional
 * ============================================
 *
 * Visual dashboard builder with drag-and-drop and resize support
 * Uses @dnd-kit for drag-and-drop functionality
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
  TabGroup,
  TabList,
  Tab,
  Callout,
  BadgeDelta,
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
  GripVertical,
  Maximize2,
  Plus,
  FolderPlus,
  MessageSquare,
  Info,
  Lightbulb,
  Clock,
  Play,
  Pause,
  RefreshCw,
} from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  rectSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
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
      { id: 'kpi_delta', name: 'KPI com Delta', icon: TrendingUp, description: 'KPI com variação %', defaultW: 2, defaultH: 2 },
      { id: 'stat', name: 'Estatística', icon: TrendingUp, description: 'Valor grande destacado', defaultW: 2, defaultH: 2 },
      { id: 'gauge', name: 'Gauge', icon: Gauge, description: 'Velocímetro circular', defaultW: 3, defaultH: 3 },
      { id: 'bar_gauge', name: 'Bar Gauge', icon: BarChart3, description: 'Barra de progresso', defaultW: 2, defaultH: 2 },
      { id: 'progress_ring', name: 'Anel de Progresso', icon: CircleDot, description: 'Progresso circular', defaultW: 2, defaultH: 2 },
    ],
  },
  {
    id: 'charts',
    name: 'Gráficos',
    icon: LineChart,
    widgets: [
      { id: 'line_chart', name: 'Linha', icon: LineChart, description: 'Tendência temporal', defaultW: 4, defaultH: 3 },
      { id: 'multi_line_chart', name: 'Multi-Linha', icon: LineChart, description: 'Múltiplas séries', defaultW: 4, defaultH: 3 },
      { id: 'area_chart', name: 'Área', icon: AreaChart, description: 'Área preenchida', defaultW: 4, defaultH: 3 },
      { id: 'bar_chart', name: 'Barras', icon: BarChart3, description: 'Comparação de valores', defaultW: 3, defaultH: 3 },
      { id: 'multi_bar_chart', name: 'Multi-Barras', icon: BarChart3, description: 'Barras comparativas', defaultW: 4, defaultH: 3 },
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
    name: 'Alertas & Info',
    icon: AlertTriangle,
    widgets: [
      { id: 'active_alarms', name: 'Alarmes Ativos', icon: AlertTriangle, description: 'Lista de alarmes', defaultW: 4, defaultH: 4 },
      { id: 'callout_info', name: 'Callout Info', icon: Info, description: 'Informação destacada', defaultW: 3, defaultH: 2 },
      { id: 'callout_warning', name: 'Callout Alerta', icon: AlertTriangle, description: 'Alerta importante', defaultW: 3, defaultH: 2 },
      { id: 'callout_insight', name: 'Insight', icon: Lightbulb, description: 'Dica ou recomendação', defaultW: 3, defaultH: 2 },
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
  // Delta/Trend config
  showDelta?: boolean;
  deltaType?: 'increase' | 'decrease' | 'unchanged';
  deltaValue?: number;
  // Callout config
  calloutTitle?: string;
  calloutMessage?: string;
  calloutType?: 'info' | 'warning' | 'error' | 'success';
  // Multi-series config
  seriesColors?: string[];
  // Interactive time range
  interactiveTimeRange?: boolean;
  // Auto refresh
  autoRefresh?: boolean;
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

interface DashboardTab {
  id: string;
  name: string;
  widgets: Widget[];
}

interface Dashboard {
  id?: string;
  name: string;
  description: string;
  module: string;
  is_public: boolean;
  widgets: Widget[];
  tabs?: DashboardTab[];
  useTabs?: boolean;
}

const moduleOptions = [
  { value: 'operations', label: 'Operações' },
  { value: 'maintenance', label: 'Manutenção' },
  { value: 'quality', label: 'Qualidade' },
  { value: 'executive', label: 'Executivo' },
  { value: 'energy', label: 'Energia' },
  { value: 'analytics', label: 'Analytics' },
];

// Resizable Widget Item Component with drag-to-resize
interface ResizableWidgetItemProps {
  widget: Widget;
  isSelected: boolean;
  isLocked: boolean;
  onSelect: () => void;
  onRemove: () => void;
  onResize: (widgetId: string, newW: number, newH: number) => void;
  getWidgetIcon: (type: string) => React.ReactNode;
  getWidgetSizeClass: (widget: Widget) => { colSpan: string; minHeight: string };
}

const ResizableWidgetItem: React.FC<ResizableWidgetItemProps> = ({
  widget,
  isSelected,
  isLocked,
  onSelect,
  onRemove,
  onResize,
  getWidgetIcon,
  getWidgetSizeClass,
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: widget.id, disabled: isLocked });

  const [isResizing, setIsResizing] = useState(false);
  const [resizeStart, setResizeStart] = useState({ x: 0, y: 0, w: 0, h: 0 });
  const widgetRef = React.useRef<HTMLDivElement>(null);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition: isResizing ? 'none' : transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 1000 : isResizing ? 999 : 1,
  };

  const { colSpan, minHeight } = getWidgetSizeClass(widget);
  const widgetInfo = ALL_WIDGETS.find(w => w.id === widget.type);

  // Handle resize start
  const handleResizeStart = (e: React.MouseEvent) => {
    if (isLocked) return;
    e.preventDefault();
    e.stopPropagation();
    setIsResizing(true);
    setResizeStart({
      x: e.clientX,
      y: e.clientY,
      w: widget.layout.w,
      h: widget.layout.h,
    });
  };

  // Handle resize move and end
  React.useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - resizeStart.x;
      const deltaY = e.clientY - resizeStart.y;

      // Calculate new size based on drag distance (80px per grid unit)
      const gridSize = 80;
      const newW = Math.max(1, Math.min(6, resizeStart.w + Math.round(deltaX / gridSize)));
      const newH = Math.max(2, Math.min(8, resizeStart.h + Math.round(deltaY / gridSize)));

      if (newW !== widget.layout.w || newH !== widget.layout.h) {
        onResize(widget.id, newW, newH);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, resizeStart, widget.id, widget.layout.w, widget.layout.h, onResize]);

  return (
    <div
      ref={(node) => {
        setNodeRef(node);
        (widgetRef as any).current = node;
      }}
      style={{ ...style, minHeight }}
      className={`${colSpan} bg-white rounded-lg border-2 overflow-hidden transition-all relative ${
        isSelected
          ? 'border-blue-500 shadow-lg'
          : 'border-gray-200 hover:border-gray-300'
      } ${isDragging ? 'shadow-2xl' : ''} ${isResizing ? 'ring-2 ring-blue-400' : ''}`}
    >
      {/* Widget Header - Drag Handle */}
      <div
        className={`flex items-center justify-between px-2 py-1.5 bg-gray-50 border-b ${
          !isLocked ? 'cursor-grab active:cursor-grabbing' : ''
        }`}
        onClick={onSelect}
        {...(!isLocked ? { ...attributes, ...listeners } : {})}
      >
        <Flex alignItems="center" className="gap-1.5 flex-1 min-w-0">
          {!isLocked && (
            <GripVertical className="w-3 h-3 text-gray-400 flex-shrink-0" />
          )}
          <div style={{ color: widget.config.color }} className="flex-shrink-0">
            {getWidgetIcon(widget.type)}
          </div>
          <Text className="text-xs font-medium text-gray-700 truncate">
            {widget.title}
          </Text>
        </Flex>
        <Flex className="gap-1 flex-shrink-0">
          {/* Size indicator */}
          <span className="text-[10px] text-gray-400 mr-1">
            {widget.layout.w}x{widget.layout.h}
          </span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onRemove();
            }}
            className="p-0.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded"
          >
            <X className="w-3 h-3" />
          </button>
        </Flex>
      </div>

      {/* Widget Content */}
      <div
        className="h-[calc(100%-32px)] overflow-hidden"
        onClick={onSelect}
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

      {/* Resize Handle - Bottom Right Corner */}
      {!isLocked && (
        <div
          onMouseDown={handleResizeStart}
          className={`absolute bottom-0 right-0 w-4 h-4 cursor-se-resize group ${
            isSelected ? 'opacity-100' : 'opacity-0 hover:opacity-100'
          }`}
          title="Arraste para redimensionar"
        >
          <svg
            className="w-4 h-4 text-gray-400 group-hover:text-blue-500"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M22 22H20V20H22V22ZM22 18H20V16H22V18ZM18 22H16V20H18V22ZM22 14H20V12H22V14ZM18 18H16V16H18V18ZM14 22H12V20H14V22ZM18 14H16V12H18V14ZM14 18H12V16H14V18ZM14 14H12V12H14V14Z" />
          </svg>
        </div>
      )}

      {/* Resize indicator during resize */}
      {isResizing && (
        <div className="absolute inset-0 bg-blue-500 bg-opacity-10 pointer-events-none flex items-center justify-center">
          <span className="bg-blue-600 text-white px-2 py-1 rounded text-sm font-medium">
            {widget.layout.w} x {widget.layout.h}
          </span>
        </div>
      )}
    </div>
  );
};

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
    useTabs: false,
    tabs: [{ id: 'tab_default', name: 'Principal', widgets: [] }],
  });
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedWidget, setSelectedWidget] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [tagSearchTerm, setTagSearchTerm] = useState('');
  const [showTagDropdown, setShowTagDropdown] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(['visualization', 'industrial', 'alerts'])
  );
  const [isLayoutLocked, setIsLayoutLocked] = useState(false);

  // Tab management
  const [activeTabIndex, setActiveTabIndex] = useState(0);
  const [editingTabName, setEditingTabName] = useState<string | null>(null);

  // Auto-refresh control
  const [isAutoRefreshPaused, setIsAutoRefreshPaused] = useState(false);
  const [globalRefreshInterval, setGlobalRefreshInterval] = useState(30);

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
      console.log('🏷️ Fetching tags from gateway proxy...');
      const response = await apiClient.get('/api/v1/gateway-config/proxy/tags');
      const tags = response.data || [];
      console.log(`🏷️ Received ${tags.length} tags from gateway`);
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
    // If tabs mode is on, add to current tab
    if (dashboard.useTabs) {
      addWidgetToTab(type);
      return;
    }

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

  // Tab management functions
  const addTab = () => {
    const newTab: DashboardTab = {
      id: `tab_${Date.now()}`,
      name: `Aba ${(dashboard.tabs?.length || 0) + 1}`,
      widgets: [],
    };
    setDashboard(prev => ({
      ...prev,
      tabs: [...(prev.tabs || []), newTab],
    }));
    setActiveTabIndex((dashboard.tabs?.length || 0));
    setHasChanges(true);
  };

  const removeTab = (tabId: string) => {
    if ((dashboard.tabs?.length || 0) <= 1) return; // Keep at least one tab
    const tabIndex = dashboard.tabs?.findIndex(t => t.id === tabId) || 0;
    setDashboard(prev => ({
      ...prev,
      tabs: prev.tabs?.filter(t => t.id !== tabId),
    }));
    if (activeTabIndex >= tabIndex && activeTabIndex > 0) {
      setActiveTabIndex(activeTabIndex - 1);
    }
    setHasChanges(true);
  };

  const renameTab = (tabId: string, newName: string) => {
    setDashboard(prev => ({
      ...prev,
      tabs: prev.tabs?.map(t => t.id === tabId ? { ...t, name: newName } : t),
    }));
    setEditingTabName(null);
    setHasChanges(true);
  };

  const toggleUseTabs = () => {
    setDashboard(prev => ({
      ...prev,
      useTabs: !prev.useTabs,
    }));
    setHasChanges(true);
  };

  // Auto-refresh toggle
  const toggleAutoRefresh = () => {
    setIsAutoRefreshPaused(prev => !prev);
  };

  // Add widget to current tab (when tabs mode is on)
  const addWidgetToTab = (type: string) => {
    const widgetType = ALL_WIDGETS.find(w => w.id === type);
    const currentTab = dashboard.tabs?.[activeTabIndex];
    if (!currentTab) return;

    const maxY = currentTab.widgets.reduce((max, w) => Math.max(max, w.layout.y + w.layout.h), 0);

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
      tabs: prev.tabs?.map((tab, idx) =>
        idx === activeTabIndex
          ? { ...tab, widgets: [...tab.widgets, newWidget] }
          : tab
      ),
    }));
    setSelectedWidget(newWidget.id);
    setHasChanges(true);
  };

  // Remove widget from tab
  const removeWidgetFromTab = (widgetId: string, tabIndex: number) => {
    setDashboard(prev => ({
      ...prev,
      tabs: prev.tabs?.map((tab, idx) =>
        idx === tabIndex
          ? { ...tab, widgets: tab.widgets.filter(w => w.id !== widgetId) }
          : tab
      ),
    }));
    if (selectedWidget === widgetId) {
      setSelectedWidget(null);
    }
    setHasChanges(true);
  };

  // Handle drag end in tab
  const handleDragEndInTab = (event: DragEndEvent, tabIndex: number) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setDashboard(prev => {
        const currentTab = prev.tabs?.[tabIndex];
        if (!currentTab) return prev;

        const oldIndex = currentTab.widgets.findIndex(w => w.id === active.id);
        const newIndex = currentTab.widgets.findIndex(w => w.id === over.id);

        return {
          ...prev,
          tabs: prev.tabs?.map((tab, idx) =>
            idx === tabIndex
              ? { ...tab, widgets: arrayMove(tab.widgets, oldIndex, newIndex) }
              : tab
          ),
        };
      });
      setHasChanges(true);
    }
  };

  // Handle widget resize in tab
  const handleWidgetResizeInTab = (widgetId: string, newW: number, newH: number, tabIndex: number) => {
    setDashboard(prev => ({
      ...prev,
      tabs: prev.tabs?.map((tab, idx) =>
        idx === tabIndex
          ? {
              ...tab,
              widgets: tab.widgets.map(w =>
                w.id === widgetId
                  ? { ...w, layout: { ...w.layout, w: newW, h: newH } }
                  : w
              ),
            }
          : tab
      ),
    }));
    setHasChanges(true);
  };

  // Update widget config in tab
  const updateWidgetConfigInTab = (widgetId: string, configUpdates: Partial<WidgetConfig>, tabIndex: number) => {
    setDashboard(prev => ({
      ...prev,
      tabs: prev.tabs?.map((tab, idx) =>
        idx === tabIndex
          ? {
              ...tab,
              widgets: tab.widgets.map(w =>
                w.id === widgetId
                  ? { ...w, config: { ...w.config, ...configUpdates } }
                  : w
              ),
            }
          : tab
      ),
    }));
    setHasChanges(true);
  };

  // Update widget in tab
  const updateWidgetInTab = (widgetId: string, updates: Partial<Widget>, tabIndex: number) => {
    setDashboard(prev => ({
      ...prev,
      tabs: prev.tabs?.map((tab, idx) =>
        idx === tabIndex
          ? {
              ...tab,
              widgets: tab.widgets.map(w =>
                w.id === widgetId ? { ...w, ...updates } : w
              ),
            }
          : tab
      ),
    }));
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

  // Find selected widget from either tabs or flat widgets
  const selectedWidgetData = dashboard.useTabs
    ? dashboard.tabs?.flatMap(t => t.widgets).find(w => w.id === selectedWidget)
    : dashboard.widgets.find(w => w.id === selectedWidget);

  // Get the tab index that contains the selected widget
  const getSelectedWidgetTabIndex = (): number => {
    if (!dashboard.useTabs || !selectedWidget) return -1;
    return dashboard.tabs?.findIndex(t => t.widgets.some(w => w.id === selectedWidget)) ?? -1;
  };

  // Smart update functions that work with both modes
  const smartUpdateWidget = (widgetId: string, updates: Partial<Widget>) => {
    if (dashboard.useTabs) {
      const tabIndex = getSelectedWidgetTabIndex();
      if (tabIndex >= 0) {
        updateWidgetInTab(widgetId, updates, tabIndex);
      }
    } else {
      updateWidget(widgetId, updates);
    }
  };

  const smartUpdateWidgetConfig = (widgetId: string, configUpdates: Partial<WidgetConfig>) => {
    if (dashboard.useTabs) {
      const tabIndex = getSelectedWidgetTabIndex();
      if (tabIndex >= 0) {
        updateWidgetConfigInTab(widgetId, configUpdates, tabIndex);
      }
    } else {
      updateWidgetConfig(widgetId, configUpdates);
    }
  };

  const smartRemoveWidget = (widgetId: string) => {
    if (dashboard.useTabs) {
      const tabIndex = getSelectedWidgetTabIndex();
      if (tabIndex >= 0) {
        removeWidgetFromTab(widgetId, tabIndex);
      }
    } else {
      removeWidget(widgetId);
    }
  };

  // DnD sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Handle drag end
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setDashboard((prev) => {
        const oldIndex = prev.widgets.findIndex((w) => w.id === active.id);
        const newIndex = prev.widgets.findIndex((w) => w.id === over.id);

        return {
          ...prev,
          widgets: arrayMove(prev.widgets, oldIndex, newIndex),
        };
      });
      setHasChanges(true);
    }
  };

  // Handle widget resize
  const handleWidgetResize = (widgetId: string, newW: number, newH: number) => {
    setDashboard(prev => ({
      ...prev,
      widgets: prev.widgets.map(w =>
        w.id === widgetId
          ? { ...w, layout: { ...w.layout, w: newW, h: newH } }
          : w
      ),
    }));
    setHasChanges(true);
  };

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
            {/* Tabs toggle */}
            <Button
              variant="secondary"
              icon={FolderPlus}
              onClick={toggleUseTabs}
              className={dashboard.useTabs ? 'bg-blue-100 border-blue-300' : ''}
            >
              {dashboard.useTabs ? 'Tabs: On' : 'Tabs: Off'}
            </Button>
            {/* Auto-refresh control */}
            <Button
              variant="secondary"
              icon={isAutoRefreshPaused ? Play : Pause}
              onClick={toggleAutoRefresh}
              className={isAutoRefreshPaused ? 'text-amber-600' : 'text-green-600'}
            >
              {isAutoRefreshPaused ? 'Pausado' : `${globalRefreshInterval}s`}
            </Button>
            <Button
              variant="secondary"
              icon={isLayoutLocked ? Lock : Unlock}
              onClick={() => setIsLayoutLocked(!isLayoutLocked)}
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

          {/* Widgets Grid - with Tab Support */}
          {dashboard.useTabs ? (
            // Tabbed Layout Mode
            <Card className="p-0 overflow-visible">
              {/* Tab Header with Management */}
              <div className="bg-gray-50 border-b px-4 py-2">
                <Flex justifyContent="between" alignItems="center">
                  <TabGroup index={activeTabIndex} onIndexChange={setActiveTabIndex}>
                    <TabList variant="solid" className="gap-1">
                      {dashboard.tabs?.map((tab, index) => (
                        <Tab
                          key={tab.id}
                          className={`group relative px-4 py-2 ${
                            activeTabIndex === index ? 'bg-white shadow-sm' : 'hover:bg-gray-100'
                          }`}
                        >
                          {editingTabName === tab.id ? (
                            <input
                              type="text"
                              defaultValue={tab.name}
                              autoFocus
                              onBlur={(e) => renameTab(tab.id, e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  renameTab(tab.id, e.currentTarget.value);
                                } else if (e.key === 'Escape') {
                                  setEditingTabName(null);
                                }
                              }}
                              onClick={(e) => e.stopPropagation()}
                              className="w-20 px-1 py-0 text-sm bg-transparent border-b border-blue-500 focus:outline-none"
                            />
                          ) : (
                            <span
                              onDoubleClick={(e) => {
                                e.stopPropagation();
                                setEditingTabName(tab.id);
                              }}
                              className="cursor-text"
                            >
                              {tab.name}
                            </span>
                          )}
                          {/* Tab badge showing widget count */}
                          <Badge size="xs" color="gray" className="ml-2">
                            {tab.widgets.length}
                          </Badge>
                          {/* Remove tab button */}
                          {(dashboard.tabs?.length || 0) > 1 && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                removeTab(tab.id);
                              }}
                              className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          )}
                        </Tab>
                      ))}
                    </TabList>
                  </TabGroup>
                  <Button
                    size="xs"
                    variant="secondary"
                    icon={Plus}
                    onClick={addTab}
                  >
                    Nova Aba
                  </Button>
                </Flex>
              </div>

              {/* Tab Content */}
              <div className="p-4 pb-8">
                {dashboard.tabs && dashboard.tabs[activeTabIndex] && (
                  dashboard.tabs[activeTabIndex].widgets.length === 0 ? (
                    <div className="p-12 text-center border-2 border-dashed rounded-lg bg-gray-50">
                      <LayoutDashboard className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                      <Title className="text-gray-500">Aba Vazia</Title>
                      <Text className="text-gray-400 mt-2">
                        Clique em um widget no painel lateral para adicionar a esta aba
                      </Text>
                    </div>
                  ) : (
                    <>
                      <DndContext
                        sensors={sensors}
                        collisionDetection={closestCenter}
                        onDragEnd={(event) => handleDragEndInTab(event, activeTabIndex)}
                      >
                        <SortableContext
                          items={dashboard.tabs[activeTabIndex].widgets.map(w => w.id)}
                          strategy={rectSortingStrategy}
                          disabled={isLayoutLocked}
                        >
                          <div className="grid grid-cols-6 gap-4 auto-rows-auto">
                            {dashboard.tabs[activeTabIndex].widgets.map((widget) => (
                              <ResizableWidgetItem
                                key={widget.id}
                                widget={widget}
                                isSelected={selectedWidget === widget.id}
                                isLocked={isLayoutLocked}
                                onSelect={() => setSelectedWidget(widget.id)}
                                onRemove={() => removeWidgetFromTab(widget.id, activeTabIndex)}
                                onResize={(id, w, h) => handleWidgetResizeInTab(id, w, h, activeTabIndex)}
                                getWidgetIcon={getWidgetIcon}
                                getWidgetSizeClass={getWidgetSizeClass}
                              />
                            ))}
                          </div>
                        </SortableContext>
                      </DndContext>
                      {/* Spacer to allow adding more widgets */}
                      <div className="h-40 mt-4 border-2 border-dashed border-gray-200 rounded-lg flex items-center justify-center text-gray-400 text-sm">
                        Adicione mais widgets do painel lateral
                      </div>
                    </>
                  )
                )}
              </div>
            </Card>
          ) : (
            // Standard Layout Mode (no tabs)
            dashboard.widgets.length === 0 ? (
              <Card className="p-12 text-center border-2 border-dashed bg-white">
                <LayoutDashboard className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                <Title className="text-gray-500">Dashboard Vazio</Title>
                <Text className="text-gray-400 mt-2">
                  Clique em um widget no painel lateral para adicionar
                </Text>
              </Card>
            ) : (
              <div className="bg-white rounded-lg border p-4 pb-20">
                <DndContext
                  sensors={sensors}
                  collisionDetection={closestCenter}
                  onDragEnd={handleDragEnd}
                >
                  <SortableContext
                    items={dashboard.widgets.map(w => w.id)}
                    strategy={rectSortingStrategy}
                    disabled={isLayoutLocked}
                  >
                    <div className="grid grid-cols-6 gap-4 auto-rows-auto">
                      {dashboard.widgets.map((widget) => (
                        <ResizableWidgetItem
                          key={widget.id}
                          widget={widget}
                          isSelected={selectedWidget === widget.id}
                          isLocked={isLayoutLocked}
                          onSelect={() => setSelectedWidget(widget.id)}
                          onRemove={() => removeWidget(widget.id)}
                          onResize={handleWidgetResize}
                          getWidgetIcon={getWidgetIcon}
                          getWidgetSizeClass={getWidgetSizeClass}
                        />
                      ))}
                    </div>
                  </SortableContext>
                </DndContext>
                {/* Spacer to allow adding more widgets */}
                <div className="h-40 mt-4 border-2 border-dashed border-gray-200 rounded-lg flex items-center justify-center text-gray-400 text-sm">
                  Adicione mais widgets do painel lateral
                </div>
              </div>
            )
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
                      onChange={(e) => smartUpdateWidget(selectedWidgetData.id, { title: e.target.value })}
                    />
                  </div>
                  <div>
                    <Text className="text-xs font-medium text-gray-600 mb-1">Cor</Text>
                    <div className="flex flex-wrap gap-1">
                      {COLOR_PRESETS.map((color) => (
                        <button
                          key={color.value}
                          onClick={() => smartUpdateWidgetConfig(selectedWidgetData.id, { color: color.value })}
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

              {/* Size Section */}
              <div>
                <Text className="text-xs font-semibold text-gray-500 uppercase mb-2">
                  <Flex alignItems="center" className="gap-1">
                    <Maximize2 className="w-3 h-3" />
                    Tamanho
                  </Flex>
                </Text>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Text className="text-xs font-medium text-gray-600 mb-1">Largura</Text>
                    <Select
                      value={String(selectedWidgetData.layout?.w || 3)}
                      onValueChange={(value) => {
                        smartUpdateWidget(selectedWidgetData.id, {
                          layout: { ...selectedWidgetData.layout, w: parseInt(value) }
                        });
                      }}
                    >
                      {[1, 2, 3, 4, 5, 6].map(size => (
                        <SelectItem key={size} value={String(size)}>
                          {size} col{size > 1 ? 's' : ''}
                        </SelectItem>
                      ))}
                    </Select>
                  </div>
                  <div>
                    <Text className="text-xs font-medium text-gray-600 mb-1">Altura</Text>
                    <Select
                      value={String(selectedWidgetData.layout?.h || 3)}
                      onValueChange={(value) => {
                        smartUpdateWidget(selectedWidgetData.id, {
                          layout: { ...selectedWidgetData.layout, h: parseInt(value) }
                        });
                      }}
                    >
                      {[2, 3, 4, 5, 6, 8].map(size => (
                        <SelectItem key={size} value={String(size)}>
                          {size} linha{size > 1 ? 's' : ''}
                        </SelectItem>
                      ))}
                    </Select>
                  </div>
                </div>
                <div className="mt-2 flex gap-1">
                  <button
                    onClick={() => smartUpdateWidget(selectedWidgetData.id, {
                      layout: { ...selectedWidgetData.layout, w: 2, h: 2 }
                    })}
                    className="flex-1 px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                  >
                    Pequeno
                  </button>
                  <button
                    onClick={() => smartUpdateWidget(selectedWidgetData.id, {
                      layout: { ...selectedWidgetData.layout, w: 3, h: 3 }
                    })}
                    className="flex-1 px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                  >
                    Médio
                  </button>
                  <button
                    onClick={() => smartUpdateWidget(selectedWidgetData.id, {
                      layout: { ...selectedWidgetData.layout, w: 6, h: 4 }
                    })}
                    className="flex-1 px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                  >
                    Grande
                  </button>
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
                      {['line_chart', 'area_chart', 'bar_chart', 'multi_line_chart', 'multi_bar_chart'].includes(selectedWidgetData.type) && (
                        <span className="text-gray-400 ml-1">(multi-série)</span>
                      )}
                    </Text>

                    {selectedWidgetData.config.tag_ids && selectedWidgetData.config.tag_ids.length > 0 && (
                      <div className="space-y-1 mb-2">
                        {selectedWidgetData.config.tag_ids.map((tagId, index) => {
                          const tagInfo = availableTags.find(t => t.tag_id === tagId);
                          const seriesColors = selectedWidgetData.config.seriesColors || [];
                          const tagColor = seriesColors[index] || COLOR_PRESETS[index % COLOR_PRESETS.length].value;
                          const isMultiSeries = ['line_chart', 'area_chart', 'bar_chart', 'multi_line_chart', 'multi_bar_chart'].includes(selectedWidgetData.type);

                          return (
                            <div
                              key={tagId}
                              className="flex items-center gap-2 p-1.5 bg-gray-50 rounded border"
                            >
                              {/* Color picker for multi-series */}
                              {isMultiSeries && (
                                <div className="relative group">
                                  <button
                                    className="w-4 h-4 rounded-full border border-gray-300"
                                    style={{ backgroundColor: tagColor }}
                                    title="Alterar cor da série"
                                  />
                                  <div className="absolute left-0 top-5 bg-white border rounded shadow-lg p-1 hidden group-hover:flex gap-1 z-50">
                                    {COLOR_PRESETS.map((color) => (
                                      <button
                                        key={color.value}
                                        onClick={() => {
                                          const newColors = [...seriesColors];
                                          newColors[index] = color.value;
                                          smartUpdateWidgetConfig(selectedWidgetData.id, { seriesColors: newColors });
                                        }}
                                        className="w-4 h-4 rounded-full border border-gray-200 hover:scale-125 transition-transform"
                                        style={{ backgroundColor: color.value }}
                                        title={color.name}
                                      />
                                    ))}
                                  </div>
                                </div>
                              )}
                              <span className="flex-1 text-xs text-gray-700 truncate">
                                {tagInfo?.name || tagId}
                              </span>
                              {tagInfo?.unit && (
                                <span className="text-xs text-gray-400">({tagInfo.unit})</span>
                              )}
                              <button
                                onClick={() => {
                                  const newTags = selectedWidgetData.config.tag_ids?.filter(t => t !== tagId) || [];
                                  const newColors = [...seriesColors];
                                  newColors.splice(index, 1);
                                  smartUpdateWidgetConfig(selectedWidgetData.id, {
                                    tag_ids: newTags,
                                    tagId: newTags[0] || undefined,
                                    tagName: newTags[0] ? availableTags.find(t => t.tag_id === newTags[0])?.name : undefined,
                                    seriesColors: newColors,
                                  });
                                }}
                                className="p-0.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </div>
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
                          <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded shadow-lg max-h-64 overflow-hidden flex flex-col">
                            <div className="px-2 py-1 bg-blue-50 border-b text-xs text-blue-700 font-medium">
                              {availableTags.length} tags disponíveis
                              {tagSearchTerm && ` (filtrando por "${tagSearchTerm}")`}
                            </div>
                            <div className="max-h-48 overflow-y-auto">
                              {availableTags
                                .filter(tag =>
                                  tag.name.toLowerCase().includes(tagSearchTerm.toLowerCase()) ||
                                  tag.tag_id.toLowerCase().includes(tagSearchTerm.toLowerCase())
                                )
                                .slice(0, 100)
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
                                        smartUpdateWidgetConfig(selectedWidgetData.id, {
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
                    <div className="mt-1 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-1">
                        <div className={`w-1.5 h-1.5 rounded-full ${
                          selectedWidgetData.config.tag_ids?.length ? 'bg-green-500' : 'bg-amber-500'
                        }`}></div>
                        <span className={selectedWidgetData.config.tag_ids?.length ? 'text-green-700' : 'text-amber-700'}>
                          {selectedWidgetData.config.tag_ids?.length ? 'Tags configuradas' : 'Selecione tags'}
                        </span>
                      </div>
                      <span className="text-gray-400">
                        {availableTags.length} disponíveis
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Text className="text-xs font-medium text-gray-600 mb-1">Unidade</Text>
                      <TextInput
                        placeholder="°C, bar..."
                        value={selectedWidgetData.config.unit || ''}
                        onChange={(e) => smartUpdateWidgetConfig(selectedWidgetData.id, { unit: e.target.value })}
                      />
                    </div>
                    <div>
                      <Text className="text-xs font-medium text-gray-600 mb-1">Decimais</Text>
                      <NumberInput
                        value={selectedWidgetData.config.decimals ?? 1}
                        onValueChange={(v) => smartUpdateWidgetConfig(selectedWidgetData.id, { decimals: v })}
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
                        onValueChange={(v) => smartUpdateWidgetConfig(selectedWidgetData.id, { min: v })}
                      />
                    </div>
                    <div>
                      <Text className="text-xs font-medium text-gray-600 mb-1">Máximo</Text>
                      <NumberInput
                        value={selectedWidgetData.config.max ?? 100}
                        onValueChange={(v) => smartUpdateWidgetConfig(selectedWidgetData.id, { max: v })}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Delta/Trend Indicator - for KPI widgets */}
              {['kpi_card', 'kpi_delta', 'stat'].includes(selectedWidgetData.type) && (
                <div>
                  <Text className="text-xs font-semibold text-gray-500 uppercase mb-2">
                    <Flex alignItems="center" className="gap-1">
                      <TrendingUp className="w-3 h-3" />
                      Indicador de Tendência
                    </Flex>
                  </Text>

                  {/* Enable delta */}
                  <label className="flex items-center gap-2 mb-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedWidgetData.config.showDelta ?? false}
                      onChange={(e) => smartUpdateWidgetConfig(selectedWidgetData.id, { showDelta: e.target.checked })}
                      className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <Text className="text-xs text-gray-600">
                      Mostrar variação percentual
                    </Text>
                  </label>

                  {selectedWidgetData.config.showDelta && (
                    <div className="space-y-2 pl-6">
                      {/* Delta type */}
                      <div>
                        <Text className="text-xs font-medium text-gray-600 mb-1">Tipo de variação</Text>
                        <div className="flex gap-1">
                          {[
                            { value: 'increase', label: '↑ Aumento', color: 'text-green-600' },
                            { value: 'decrease', label: '↓ Queda', color: 'text-red-600' },
                            { value: 'unchanged', label: '→ Estável', color: 'text-gray-600' },
                          ].map((type) => (
                            <button
                              key={type.value}
                              onClick={() => smartUpdateWidgetConfig(selectedWidgetData.id, { deltaType: type.value as 'increase' | 'decrease' | 'unchanged' })}
                              className={`flex-1 px-2 py-1 text-xs rounded border transition-colors ${
                                selectedWidgetData.config.deltaType === type.value
                                  ? 'bg-blue-50 border-blue-300 text-blue-700'
                                  : 'bg-white border-gray-200 hover:bg-gray-50'
                              } ${type.color}`}
                            >
                              {type.label}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Delta value */}
                      <div>
                        <Text className="text-xs font-medium text-gray-600 mb-1">Valor da variação (%)</Text>
                        <NumberInput
                          value={selectedWidgetData.config.deltaValue ?? 0}
                          onValueChange={(v) => smartUpdateWidgetConfig(selectedWidgetData.id, { deltaValue: v })}
                          min={-100}
                          max={1000}
                          step={0.1}
                        />
                      </div>

                      {/* Preview */}
                      <div className="mt-2 p-2 bg-gray-50 rounded border text-center">
                        <Text className="text-xs text-gray-500 mb-1">Preview</Text>
                        <BadgeDelta
                          deltaType={selectedWidgetData.config.deltaType || 'unchanged'}
                          size="sm"
                        >
                          {selectedWidgetData.config.deltaValue ?? 0}%
                        </BadgeDelta>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Callout Configuration - for callout widgets */}
              {['callout_info', 'callout_warning', 'callout_insight'].includes(selectedWidgetData.type) && (
                <div>
                  <Text className="text-xs font-semibold text-gray-500 uppercase mb-2">
                    <Flex alignItems="center" className="gap-1">
                      <MessageSquare className="w-3 h-3" />
                      Conteúdo do Callout
                    </Flex>
                  </Text>

                  {/* Callout title */}
                  <div className="mb-2">
                    <Text className="text-xs font-medium text-gray-600 mb-1">Título</Text>
                    <TextInput
                      placeholder="Título do callout"
                      value={selectedWidgetData.config.calloutTitle || ''}
                      onChange={(e) => smartUpdateWidgetConfig(selectedWidgetData.id, { calloutTitle: e.target.value })}
                    />
                  </div>

                  {/* Callout message */}
                  <div className="mb-2">
                    <Text className="text-xs font-medium text-gray-600 mb-1">Mensagem</Text>
                    <textarea
                      placeholder="Descrição ou mensagem do callout..."
                      value={selectedWidgetData.config.calloutMessage || ''}
                      onChange={(e) => smartUpdateWidgetConfig(selectedWidgetData.id, { calloutMessage: e.target.value })}
                      className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-h-[60px] resize-y"
                    />
                  </div>

                  {/* Callout type */}
                  <div>
                    <Text className="text-xs font-medium text-gray-600 mb-1">Tipo</Text>
                    <div className="grid grid-cols-2 gap-1">
                      {[
                        { value: 'info', label: 'ℹ️ Info', bgColor: 'bg-blue-50', borderColor: 'border-blue-300' },
                        { value: 'warning', label: '⚠️ Alerta', bgColor: 'bg-amber-50', borderColor: 'border-amber-300' },
                        { value: 'error', label: '❌ Erro', bgColor: 'bg-red-50', borderColor: 'border-red-300' },
                        { value: 'success', label: '✅ Sucesso', bgColor: 'bg-green-50', borderColor: 'border-green-300' },
                      ].map((type) => (
                        <button
                          key={type.value}
                          onClick={() => smartUpdateWidgetConfig(selectedWidgetData.id, { calloutType: type.value as 'info' | 'warning' | 'error' | 'success' })}
                          className={`px-2 py-1.5 text-xs rounded border transition-colors ${
                            selectedWidgetData.config.calloutType === type.value
                              ? `${type.bgColor} ${type.borderColor}`
                              : 'bg-white border-gray-200 hover:bg-gray-50'
                          }`}
                        >
                          {type.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Preview */}
                  <div className="mt-3">
                    <Text className="text-xs text-gray-500 mb-1">Preview</Text>
                    <Callout
                      title={selectedWidgetData.config.calloutTitle || 'Título do Callout'}
                      color={
                        selectedWidgetData.config.calloutType === 'warning' ? 'yellow' :
                        selectedWidgetData.config.calloutType === 'error' ? 'red' :
                        selectedWidgetData.config.calloutType === 'success' ? 'green' : 'blue'
                      }
                    >
                      {selectedWidgetData.config.calloutMessage || 'Mensagem do callout aparecerá aqui.'}
                    </Callout>
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
                      onValueChange={(v) => smartUpdateWidgetConfig(selectedWidgetData.id, { targetOEE: v })}
                      min={0}
                      max={100}
                    />
                  </div>
                </div>
              )}

              {/* Time Range - for charts */}
              {['line_chart', 'area_chart', 'bar_chart', 'multi_line_chart', 'multi_bar_chart'].includes(selectedWidgetData.type) && (
                <div>
                  <Text className="text-xs font-semibold text-gray-500 uppercase mb-2">
                    <Flex alignItems="center" className="gap-1">
                      <Clock className="w-3 h-3" />
                      Período
                    </Flex>
                  </Text>

                  {/* Quick time range buttons */}
                  <div className="flex flex-wrap gap-1 mb-2">
                    {[
                      { value: '1h', label: '1h' },
                      { value: '6h', label: '6h' },
                      { value: '24h', label: '24h' },
                      { value: '7d', label: '7d' },
                    ].map((tr) => (
                      <button
                        key={tr.value}
                        onClick={() => smartUpdateWidgetConfig(selectedWidgetData.id, { time_range: tr.value })}
                        className={`px-2 py-1 text-xs rounded transition-colors ${
                          selectedWidgetData.config.time_range === tr.value
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {tr.label}
                      </button>
                    ))}
                  </div>

                  {/* Full time range selector */}
                  <Select
                    value={selectedWidgetData.config.time_range || '1h'}
                    onValueChange={(v) => smartUpdateWidgetConfig(selectedWidgetData.id, { time_range: v })}
                  >
                    {TIME_RANGES.map(tr => (
                      <SelectItem key={tr.value} value={tr.value}>{tr.label}</SelectItem>
                    ))}
                  </Select>

                  {/* Interactive time range toggle */}
                  <label className="flex items-center gap-2 mt-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedWidgetData.config.interactiveTimeRange ?? false}
                      onChange={(e) => smartUpdateWidgetConfig(selectedWidgetData.id, { interactiveTimeRange: e.target.checked })}
                      className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <Text className="text-xs text-gray-600">
                      Mostrar botões de período no widget
                    </Text>
                  </label>
                </div>
              )}

              {/* Auto-refresh configuration */}
              <div>
                <Text className="text-xs font-semibold text-gray-500 uppercase mb-2">
                  <Flex alignItems="center" className="gap-1">
                    <RefreshCw className="w-3 h-3" />
                    Atualização Automática
                  </Flex>
                </Text>

                {/* Enable auto-refresh */}
                <label className="flex items-center gap-2 mb-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedWidgetData.config.autoRefresh ?? true}
                    onChange={(e) => smartUpdateWidgetConfig(selectedWidgetData.id, { autoRefresh: e.target.checked })}
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <Text className="text-xs text-gray-600">
                    Atualizar automaticamente
                  </Text>
                </label>

                {selectedWidgetData.config.autoRefresh !== false && (
                  <div>
                    <Text className="text-xs font-medium text-gray-600 mb-1">Intervalo (segundos)</Text>
                    <div className="flex gap-1">
                      {[10, 30, 60, 120].map((interval) => (
                        <button
                          key={interval}
                          onClick={() => smartUpdateWidgetConfig(selectedWidgetData.id, { refresh_interval: interval })}
                          className={`flex-1 px-2 py-1 text-xs rounded transition-colors ${
                            selectedWidgetData.config.refresh_interval === interval
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          {interval}s
                        </button>
                      ))}
                    </div>
                    <NumberInput
                      value={selectedWidgetData.config.refresh_interval ?? 30}
                      onValueChange={(v) => smartUpdateWidgetConfig(selectedWidgetData.id, { refresh_interval: v })}
                      min={5}
                      max={300}
                      className="mt-2"
                    />
                  </div>
                )}
              </div>

              {/* Delete Widget */}
              <Button
                variant="secondary"
                color="red"
                icon={Trash2}
                size="xs"
                className="w-full"
                onClick={() => smartRemoveWidget(selectedWidgetData.id)}
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
