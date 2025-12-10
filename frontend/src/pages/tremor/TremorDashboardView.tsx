/**
 * 📊 Dashboard View - Tremor Professional
 * ========================================
 *
 * View saved dashboards with responsive grid layout
 * Uses react-grid-layout for proper widget positioning
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Title,
  Text,
  Flex,
  Badge,
  Button,
} from '@tremor/react';
import {
  ArrowLeft,
  Pencil,
  RefreshCw,
  Clock,
  AlertTriangle,
  Maximize2,
  Minimize2,
} from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import apiClient from '../../api/client';
import WidgetRenderer from '../../components/Dashboard/WidgetRenderer';

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
  size?: string;
  config: {
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
    [key: string]: any;
  };
  layout?: WidgetLayout;
  data_config?: any;
  display_config?: any;
}

interface Dashboard {
  id: string;
  name: string;
  description: string;
  module: string;
  is_public: boolean;
  layout_config?: { widgets: Widget[] };
  widgets?: Widget[];
  view_count: number;
  updated_at: string;
}

const moduleColors: Record<string, string> = {
  operations: 'blue',
  maintenance: 'orange',
  quality: 'green',
  executive: 'purple',
  energy: 'yellow',
  analytics: 'cyan',
};

// Default layout for widgets without layout info
const getDefaultLayout = (index: number, type: string): WidgetLayout => {
  const defaultSizes: Record<string, { w: number; h: number }> = {
    gauge: { w: 3, h: 3 },
    tank_level: { w: 2, h: 4 },
    line_chart: { w: 4, h: 3 },
    area_chart: { w: 4, h: 3 },
    bar_chart: { w: 3, h: 3 },
    table: { w: 6, h: 4 },
    active_alarms: { w: 4, h: 4 },
    oee: { w: 3, h: 3 },
    equipment_health: { w: 3, h: 3 },
  };

  const size = defaultSizes[type] || { w: 3, h: 3 };

  return {
    x: (index % 4) * 3,
    y: Math.floor(index / 4) * 3,
    w: size.w,
    h: size.h,
    minW: 2,
    minH: 2,
  };
};

export const TremorDashboardView: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const fetchDashboard = useCallback(async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.get(`/api/v1/dashboards/${id}`);
      setDashboard(response.data);
    } catch (err: any) {
      console.error('Error fetching dashboard:', err);

      try {
        const listResponse = await apiClient.get('/api/v1/dashboards');
        const dashboards = listResponse.data || [];
        const found = dashboards.find((d: any) => d.id === id);
        if (found) {
          setDashboard({
            ...found,
            layout_config: { widgets: [] },
          });
        } else {
          setError('Dashboard não encontrado');
        }
      } catch {
        setError('Erro ao carregar dashboard');
      }
    } finally {
      setLoading(false);
    }
  }, [id]);

  const handleRefresh = () => {
    setLastRefresh(new Date());
    fetchDashboard();
  };

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setLastRefresh(new Date());
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // Fullscreen toggle
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  // Prepare widget for WidgetRenderer
  const prepareWidget = (widget: Widget) => {
    return {
      ...widget,
      config: {
        ...widget.config,
        tagId: widget.config.tagId || widget.config.tag_ids?.[0],
        tagName: widget.config.tagName || widget.config.tag_ids?.[0],
      },
      data_config: widget.data_config || {
        tagId: widget.config.tagId || widget.config.tag_ids?.[0],
      },
      display_config: widget.display_config || {},
    };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Carregando dashboard...</span>
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="p-6">
        <Card className="p-12 text-center">
          <AlertTriangle className="w-16 h-16 mx-auto text-yellow-500 mb-4" />
          <Title className="text-gray-600">{error || 'Dashboard não encontrado'}</Title>
          <Text className="text-gray-500 mt-2">
            O dashboard solicitado não existe ou você não tem permissão para acessá-lo.
          </Text>
          <Button
            icon={ArrowLeft}
            className="mt-4"
            onClick={() => navigate('/dashboards')}
          >
            Voltar para Lista
          </Button>
        </Card>
      </div>
    );
  }

  const widgets = dashboard.layout_config?.widgets || dashboard.widgets || [];

  // Get widget size class based on layout
  const getWidgetSizeClass = (widget: Widget, index: number) => {
    const layout = widget.layout || getDefaultLayout(index, widget.type);
    const w = layout.w || 3;
    const h = layout.h || 3;

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
    <div className={`${isFullscreen ? 'fixed inset-0 z-50 bg-gray-100' : ''} flex flex-col h-full`}>
      {/* Header */}
      <div className="bg-white border-b px-6 py-3 flex-shrink-0">
        <Flex justifyContent="between" alignItems="center">
          <Flex alignItems="center" className="gap-4">
            <Button
              variant="secondary"
              icon={ArrowLeft}
              onClick={() => navigate('/dashboards')}
            >
              Voltar
            </Button>
            <div>
              <Flex alignItems="center" className="gap-2">
                <Title className="text-xl font-bold text-gray-800">{dashboard.name}</Title>
                <Badge color={moduleColors[dashboard.module] || 'gray'} size="sm">
                  {dashboard.module}
                </Badge>
                {dashboard.is_public && (
                  <Badge color="green" size="sm">Público</Badge>
                )}
              </Flex>
              {dashboard.description && (
                <Text className="text-gray-500 text-sm">{dashboard.description}</Text>
              )}
            </div>
          </Flex>
          <Flex className="gap-2" alignItems="center">
            <Flex alignItems="center" className="gap-1 text-gray-500 text-sm mr-4">
              <Clock className="w-4 h-4" />
              <span>Atualizado: {lastRefresh.toLocaleTimeString('pt-BR')}</span>
            </Flex>
            <Button
              variant="secondary"
              icon={isFullscreen ? Minimize2 : Maximize2}
              onClick={toggleFullscreen}
            >
              {isFullscreen ? 'Sair' : 'Tela Cheia'}
            </Button>
            <Button
              variant="secondary"
              icon={RefreshCw}
              onClick={handleRefresh}
            >
              Atualizar
            </Button>
            <Button
              variant="secondary"
              icon={Pencil}
              onClick={() => navigate(`/dashboards/builder?id=${dashboard.id}`)}
            >
              Editar
            </Button>
          </Flex>
        </Flex>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4 bg-gray-100">
        {widgets.length === 0 ? (
          <Card className="p-12 text-center">
            <Title className="text-gray-500">Dashboard Vazio</Title>
            <Text className="text-gray-400 mt-2">
              Este dashboard ainda não possui widgets configurados.
            </Text>
            <Button
              icon={Pencil}
              className="mt-4 bg-blue-600 hover:bg-blue-700 text-white"
              onClick={() => navigate(`/dashboards/builder?id=${dashboard.id}`)}
            >
              Adicionar Widgets
            </Button>
          </Card>
        ) : (
          <div className="bg-white rounded-lg border p-4 min-h-[600px]">
            <div className="grid grid-cols-6 gap-4">
              {widgets.map((widget, index) => {
                const preparedWidget = prepareWidget(widget);
                const { colSpan, minHeight } = getWidgetSizeClass(widget, index);

                return (
                  <div
                    key={widget.id}
                    className={`${colSpan} bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden`}
                    style={{ minHeight }}
                  >
                    {/* Widget Header */}
                    <div
                      className="flex items-center justify-between px-3 py-2 bg-gray-50 border-b"
                      style={{ borderLeftColor: widget.config.color, borderLeftWidth: '3px' }}
                    >
                      <Text className="font-medium text-gray-700 truncate">
                        {widget.title}
                      </Text>
                      {widget.config.tag_ids && widget.config.tag_ids.length > 0 && (
                        <Badge color="blue" size="xs">
                          {widget.config.tag_ids.length} tag{widget.config.tag_ids.length > 1 ? 's' : ''}
                        </Badge>
                      )}
                    </div>

                    {/* Widget Content */}
                    <div className="h-[calc(100%-40px)] overflow-hidden">
                      <WidgetRenderer widget={preparedWidget} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TremorDashboardView;
