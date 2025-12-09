/**
 * 📊 Dashboard View - Tremor Professional
 * ========================================
 *
 * View and interact with a saved dashboard
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
  AreaChart,
  BarChart,
  DonutChart,
  Metric,
  ProgressBar,
} from '@tremor/react';
import {
  ArrowLeft,
  Pencil,
  RefreshCw,
  Share2,
  Maximize2,
  Clock,
  AlertTriangle,
} from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import apiClient from '../../api/client';

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
  };
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

interface TagData {
  tag_id: string;
  name: string;
  value: number;
  unit?: string;
  timestamp: string;
  history?: { timestamp: string; value: number }[];
}

const WIDGET_SIZES: Record<string, number> = {
  small: 1,
  medium: 2,
  large: 3,
  full: 4,
};

const moduleColors: Record<string, string> = {
  operations: 'blue',
  maintenance: 'orange',
  quality: 'green',
  executive: 'purple',
  energy: 'yellow',
  analytics: 'cyan',
};

export const TremorDashboardView: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [widgetData, setWidgetData] = useState<Record<string, TagData[]>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);

      // Try to get dashboard details
      const response = await apiClient.get(`/api/v1/dashboards/${id}`);
      setDashboard(response.data);

      // Get widgets from layout_config or widgets array
      const widgets = response.data.layout_config?.widgets || response.data.widgets || [];

      // Fetch data for each widget's tags
      await fetchWidgetData(widgets);
    } catch (err: any) {
      console.error('Error fetching dashboard:', err);

      // Fallback: try to get from list
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

  const fetchWidgetData = async (widgets: Widget[]) => {
    const allTagIds = new Set<string>();
    widgets.forEach(w => {
      w.config.tag_ids?.forEach(t => allTagIds.add(t));
    });

    if (allTagIds.size === 0) return;

    try {
      // Fetch current values for all tags
      const response = await apiClient.get('/api/v1/timeseries/tags/active');
      const tags = response.data?.tags || response.data || [];

      const dataMap: Record<string, TagData[]> = {};

      widgets.forEach(widget => {
        const widgetTags: TagData[] = [];
        widget.config.tag_ids?.forEach(tagId => {
          const tagInfo = tags.find((t: any) => (t.tag_id || t.id) === tagId);
          if (tagInfo) {
            widgetTags.push({
              tag_id: tagId,
              name: tagInfo.name || tagId,
              value: tagInfo.value ?? Math.random() * 100,
              unit: tagInfo.unit,
              timestamp: tagInfo.timestamp || new Date().toISOString(),
              history: generateMockHistory(),
            });
          } else {
            // Generate mock data if tag not found
            widgetTags.push({
              tag_id: tagId,
              name: tagId,
              value: Math.random() * 100,
              timestamp: new Date().toISOString(),
              history: generateMockHistory(),
            });
          }
        });
        dataMap[widget.id] = widgetTags;
      });

      setWidgetData(dataMap);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Error fetching widget data:', error);
    }
  };

  const generateMockHistory = () => {
    const history = [];
    const now = Date.now();
    for (let i = 24; i >= 0; i--) {
      history.push({
        timestamp: new Date(now - i * 3600000).toISOString(),
        value: Math.random() * 100,
      });
    }
    return history;
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    const widgets = dashboard?.layout_config?.widgets || dashboard?.widgets || [];
    await fetchWidgetData(widgets);
    setRefreshing(false);
  };

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  // Auto-refresh
  useEffect(() => {
    const interval = setInterval(() => {
      handleRefresh();
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, [dashboard]);

  const renderWidget = (widget: Widget) => {
    const data = widgetData[widget.id] || [];
    const colSpan = WIDGET_SIZES[widget.size] || 2;

    switch (widget.type) {
      case 'line_chart':
      case 'area_chart':
        return (
          <Card key={widget.id} style={{ gridColumn: `span ${colSpan}` }}>
            <Title>{widget.title}</Title>
            {data.length > 0 && data[0].history ? (
              <AreaChart
                className="h-48 mt-4"
                data={data[0].history.map(h => ({
                  date: new Date(h.timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
                  value: h.value,
                }))}
                index="date"
                categories={['value']}
                colors={['blue']}
                showLegend={false}
              />
            ) : (
              <div className="h-48 flex items-center justify-center text-gray-400">
                Sem dados disponíveis
              </div>
            )}
          </Card>
        );

      case 'bar_chart':
        return (
          <Card key={widget.id} style={{ gridColumn: `span ${colSpan}` }}>
            <Title>{widget.title}</Title>
            {data.length > 0 ? (
              <BarChart
                className="h-48 mt-4"
                data={data.map(d => ({
                  name: d.name,
                  value: d.value,
                }))}
                index="name"
                categories={['value']}
                colors={['blue']}
              />
            ) : (
              <div className="h-48 flex items-center justify-center text-gray-400">
                Sem dados disponíveis
              </div>
            )}
          </Card>
        );

      case 'pie_chart':
        return (
          <Card key={widget.id} style={{ gridColumn: `span ${colSpan}` }}>
            <Title>{widget.title}</Title>
            {data.length > 0 ? (
              <DonutChart
                className="h-48 mt-4"
                data={data.map(d => ({
                  name: d.name,
                  value: d.value,
                }))}
                category="value"
                index="name"
                colors={['blue', 'cyan', 'indigo', 'violet', 'purple']}
              />
            ) : (
              <div className="h-48 flex items-center justify-center text-gray-400">
                Sem dados disponíveis
              </div>
            )}
          </Card>
        );

      case 'gauge':
      case 'kpi':
        const firstTag = data[0];
        return (
          <Card key={widget.id} style={{ gridColumn: `span ${colSpan}` }}>
            <Text>{widget.title}</Text>
            <Metric className="mt-2">
              {firstTag ? `${firstTag.value.toFixed(1)} ${firstTag.unit || ''}` : '--'}
            </Metric>
            {firstTag && (
              <ProgressBar
                value={Math.min(100, firstTag.value)}
                color="blue"
                className="mt-3"
              />
            )}
          </Card>
        );

      case 'alarm_list':
        return (
          <Card key={widget.id} style={{ gridColumn: `span ${colSpan}` }}>
            <Flex justifyContent="between" alignItems="center">
              <Title>{widget.title}</Title>
              <Badge color="red" size="sm">3 ativos</Badge>
            </Flex>
            <div className="mt-4 space-y-2">
              {[1, 2, 3].map(i => (
                <div key={i} className="p-2 bg-red-50 border border-red-200 rounded-lg">
                  <Flex alignItems="center" className="gap-2">
                    <AlertTriangle className="w-4 h-4 text-red-500" />
                    <Text className="text-sm text-red-700">
                      Alarme de exemplo #{i}
                    </Text>
                  </Flex>
                </div>
              ))}
            </div>
          </Card>
        );

      case 'table':
        return (
          <Card key={widget.id} style={{ gridColumn: `span ${colSpan}` }}>
            <Title>{widget.title}</Title>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Tag</th>
                    <th className="text-right py-2">Valor</th>
                    <th className="text-right py-2">Unidade</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map(d => (
                    <tr key={d.tag_id} className="border-b">
                      <td className="py-2">{d.name}</td>
                      <td className="text-right py-2">{d.value.toFixed(2)}</td>
                      <td className="text-right py-2 text-gray-500">{d.unit || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        );

      default:
        return (
          <Card key={widget.id} style={{ gridColumn: `span ${colSpan}` }}>
            <Title>{widget.title}</Title>
            <div className="h-32 flex items-center justify-center text-gray-400">
              Tipo de widget não suportado: {widget.type}
            </div>
          </Card>
        );
    }
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

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
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
              <Title className="text-2xl font-bold text-gray-800">{dashboard.name}</Title>
              <Badge color={moduleColors[dashboard.module] || 'gray'} size="sm">
                {dashboard.module}
              </Badge>
              {dashboard.is_public && (
                <Badge color="green" size="sm">Público</Badge>
              )}
            </Flex>
            {dashboard.description && (
              <Text className="text-gray-500">{dashboard.description}</Text>
            )}
          </div>
        </Flex>
        <Flex className="gap-2">
          <Flex alignItems="center" className="gap-1 text-gray-500 text-sm mr-4">
            <Clock className="w-4 h-4" />
            <span>Atualizado: {lastRefresh.toLocaleTimeString('pt-BR')}</span>
          </Flex>
          <Button
            variant="secondary"
            icon={RefreshCw}
            onClick={handleRefresh}
            loading={refreshing}
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

      {/* Widgets */}
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
        <Grid numItemsMd={2} numItemsLg={4} className="gap-4">
          {widgets.map(renderWidget)}
        </Grid>
      )}
    </div>
  );
};

export default TremorDashboardView;
