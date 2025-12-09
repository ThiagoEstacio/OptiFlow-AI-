/**
 * 📊 TremorHistory - Professional Historical Data Visualization
 * =============================================================
 *
 * Multi-tag historical data viewer with:
 * - Multiple tag selection with colored chips
 * - Time range presets with toggle buttons
 * - Real-time data from InfluxDB via API
 * - Export functionality
 * - Interactive charts with zoom
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Title,
  Text,
  Badge,
  Button,
  Grid,
  Metric,
  Flex,
  TextInput,
} from '@tremor/react';
import {
  ProfessionalLineChart,
  ProfessionalAreaChart,
} from '../../components/charts/ProfessionalCharts';
import {
  Clock,
  Download,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  LineChart,
  Search,
  X,
  Play,
  CheckCircle,
} from 'lucide-react';
import apiClient from '../../api/client';

// Types
interface TagInfo {
  id: string;
  name: string;
  unit: string;
  category: string;
  currentValue: number;
}

interface HistoryDataPoint {
  time: string;
  [key: string]: string | number;
}

interface TagStatistics {
  tagId: string;
  tagName: string;
  unit: string;
  min: number;
  max: number;
  avg: number;
  current: number;
  trend: 'up' | 'down' | 'stable';
  changePercent: number;
}

// Time range presets
const TIME_RANGES = [
  { value: '15m', label: '15 min', hours: 0.25 },
  { value: '1h', label: '1 hora', hours: 1 },
  { value: '4h', label: '4 horas', hours: 4 },
  { value: '12h', label: '12 horas', hours: 12 },
  { value: '24h', label: '24 horas', hours: 24 },
  { value: '7d', label: '7 dias', hours: 168 },
  { value: '30d', label: '30 dias', hours: 720 },
];

// Chart colors palette - distinct colors for each tag
const CHART_COLORS = [
  '#3b82f6', // blue
  '#10b981', // emerald
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#06b6d4', // cyan
  '#ec4899', // pink
  '#84cc16', // lime
];

// Determine category from tag name/unit
const getTagCategory = (name: string, unit: string): string => {
  const lowerName = name.toLowerCase();
  if (lowerName.includes('temp') || unit.includes('°C')) return 'Temperatura';
  if (lowerName.includes('press') || unit.includes('bar')) return 'Pressão';
  if (lowerName.includes('vaz') || lowerName.includes('flow')) return 'Vazão';
  if (lowerName.includes('nível') || lowerName.includes('level')) return 'Nível';
  if (lowerName.includes('energ') || unit.includes('kW') || unit.includes('V')) return 'Energia';
  return 'Outro';
};

// Fetch available tags from API
const fetchAvailableTags = async (): Promise<TagInfo[]> => {
  try {
    // Try multiple endpoints for tag discovery
    let tags: any[] = [];

    // First try: /api/v1/tags (PostgreSQL)
    try {
      const response = await apiClient.get('/api/v1/tags', {
        params: { limit: 200 }
      });
      tags = response.data || [];
    } catch {
      // If fails, try demo/tags endpoint
      try {
        const demoResponse = await apiClient.get('/api/v1/demo/tags/realtime', {
          params: { limit: 200 }
        });
        tags = demoResponse.data?.tags || [];
      } catch {
        console.warn('Could not fetch tags from primary endpoints');
      }
    }

    return tags.map((tag: any) => {
      const name = tag.name || tag.tag_name || tag.id || 'Tag';
      const unit = tag.unit || tag.engineering_unit || '';
      const value = tag.current_value ?? tag.last_value ?? tag.value ?? 0;

      return {
        id: tag.id || tag.tag_id || name,
        name,
        unit,
        category: getTagCategory(name, unit),
        currentValue: typeof value === 'number' ? value : parseFloat(value) || 0,
      };
    });
  } catch (error) {
    console.error('Error fetching tags:', error);
    return [];
  }
};

// Fetch historical data for selected tags
const fetchHistoricalData = async (
  tagIds: string[],
  hours: number,
  availableTags: TagInfo[]
): Promise<{ data: HistoryDataPoint[]; statistics: TagStatistics[] }> => {
  try {
    if (tagIds.length === 0) {
      return { data: [], statistics: [] };
    }

    const minutes = hours * 60;

    // Fetch history for each selected tag in parallel
    // Uses /api/v1/tags/timeseries/{tag_name} endpoint connected to InfluxDB
    const historyPromises = tagIds.map(tagId =>
      apiClient.get(`/api/v1/tags/timeseries/${encodeURIComponent(tagId)}`, {
        params: { start_minutes_ago: minutes }
      }).catch(() => {
        // Fallback to demo endpoint
        return apiClient.get(`/api/v1/demo/tags/${tagId}/history`, {
          params: { minutes }
        }).catch(() => ({ data: { data: [], tag_name: tagId } }));
      })
    );

    const historyResponses = await Promise.all(historyPromises);

    // Build time-indexed data from all tag histories
    const timeMap = new Map<string, HistoryDataPoint>();
    const tagStats: Map<string, { values: number[]; name: string; unit: string }> = new Map();

    historyResponses.forEach((response, idx) => {
      const tagId = tagIds[idx];
      const tagInfo = availableTags.find(t => t.id === tagId);
      const tagName = tagInfo?.name || tagId;
      const tagUnit = tagInfo?.unit || '';
      // Support both /api/v1/tags/timeseries and /api/v1/demo/tags formats
      const historyData = response.data?.data || response.data?.history || [];

      tagStats.set(tagId, { values: [], name: tagName, unit: tagUnit });

      // Sample data to avoid too many points (max 500 per tag)
      const sampleRate = Math.max(1, Math.floor(historyData.length / 500));
      const sampledData = historyData.filter((_: any, i: number) => i % sampleRate === 0);

      sampledData.forEach((point: any) => {
        const timestamp = new Date(point.time);
        timestamp.setSeconds(0, 0);
        const timeKey = timestamp.toISOString();
        const displayTime = timestamp.toLocaleString('pt-BR', {
          day: '2-digit',
          month: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
        });

        if (!timeMap.has(timeKey)) {
          timeMap.set(timeKey, {
            time: displayTime,
            _ts: timestamp.getTime(), // store as number for sorting
          });
        }

        const entry = timeMap.get(timeKey)!;
        entry[tagName] = point.value;

        tagStats.get(tagId)!.values.push(point.value);
      });
    });

    // Sort by timestamp and remove _ts helper
    const sortedData = Array.from(timeMap.values())
      .sort((a, b) => (a._ts as number) - (b._ts as number))
      .map(({ _ts, ...rest }) => rest) as HistoryDataPoint[];

    // Calculate statistics for each tag
    const statistics: TagStatistics[] = [];
    tagStats.forEach((stats, tagId) => {
      const values = stats.values;
      if (values.length === 0) return;

      const min = Math.min(...values);
      const max = Math.max(...values);
      const avg = values.reduce((a, b) => a + b, 0) / values.length;
      const current = values[values.length - 1];
      const first = values[0];
      const changePercent = first !== 0 ? ((current - first) / first) * 100 : 0;

      statistics.push({
        tagId,
        tagName: stats.name,
        unit: stats.unit,
        min,
        max,
        avg,
        current,
        trend: changePercent > 1 ? 'up' : changePercent < -1 ? 'down' : 'stable',
        changePercent,
      });
    });

    return { data: sortedData, statistics };
  } catch (error) {
    console.error('Error fetching historical data:', error);
    return { data: [], statistics: [] };
  }
};

export default function TremorHistory() {
  // State
  const [availableTags, setAvailableTags] = useState<TagInfo[]>([]);
  const [selectedTags, setSelectedTags] = useState<TagInfo[]>([]);
  const [historyData, setHistoryData] = useState<HistoryDataPoint[]>([]);
  const [statistics, setStatistics] = useState<TagStatistics[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [timeRange, setTimeRange] = useState('1h');
  const [chartType, setChartType] = useState<'line' | 'area'>('line');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showDropdown, setShowDropdown] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Fetch available tags on mount
  useEffect(() => {
    const loadTags = async () => {
      setLoading(true);
      const tags = await fetchAvailableTags();

      // Sort tags by category priority
      const categoryPriority: Record<string, number> = {
        'Temperatura': 1,
        'Pressão': 2,
        'Vazão': 3,
        'Nível': 4,
        'Energia': 5,
        'Outro': 6,
      };

      const sortedTags = [...tags].sort((a, b) => {
        const priorityA = categoryPriority[a.category] || 99;
        const priorityB = categoryPriority[b.category] || 99;
        if (priorityA !== priorityB) return priorityA - priorityB;
        return a.name.localeCompare(b.name);
      });

      setAvailableTags(sortedTags);
      setLoading(false);
    };

    loadTags();
  }, []);

  // Load historical data
  const loadHistoricalData = useCallback(async () => {
    if (selectedTags.length === 0) {
      setHistoryData([]);
      setStatistics([]);
      return;
    }

    setLoadingHistory(true);
    const range = TIME_RANGES.find(r => r.value === timeRange);
    const hours = range?.hours || 1;

    const selectedTagIds = selectedTags.map(t => t.id);
    const { data, statistics: stats } = await fetchHistoricalData(
      selectedTagIds,
      hours,
      availableTags
    );

    setHistoryData(data);
    setStatistics(stats);
    setLastUpdated(new Date());
    setLoadingHistory(false);
  }, [selectedTags, timeRange, availableTags]);

  // Toggle tag selection
  const toggleTag = (tag: TagInfo) => {
    setSelectedTags(prev => {
      const isSelected = prev.some(t => t.id === tag.id);
      if (isSelected) {
        return prev.filter(t => t.id !== tag.id);
      } else if (prev.length < 8) {
        return [...prev, tag];
      }
      return prev;
    });
  };

  // Remove tag from selection
  const removeTag = (tagId: string) => {
    setSelectedTags(prev => prev.filter(t => t.id !== tagId));
  };

  // Get selected tag names for chart
  const selectedTagNames = selectedTags.map(t => t.name);

  // Build chart lines configuration
  const chartLines = selectedTags.map((tag, idx) => ({
    dataKey: tag.name,
    name: tag.name,
    color: CHART_COLORS[idx % CHART_COLORS.length],
  }));

  // Export data as CSV
  const exportCSV = () => {
    if (historyData.length === 0) return;

    const headers = ['Timestamp', ...selectedTagNames];
    const rows = historyData.map(point => {
      const row = [point.time];
      selectedTagNames.forEach(name => {
        row.push(String(point[name] ?? ''));
      });
      return row.join(',');
    });

    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `historico_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Filter tags by search and category
  const filteredTags = availableTags.filter(tag => {
    const matchesSearch = tag.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          tag.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || tag.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // Group tags by category
  const tagsByCategory = filteredTags.reduce((acc, tag) => {
    if (!acc[tag.category]) {
      acc[tag.category] = [];
    }
    acc[tag.category].push(tag);
    return acc;
  }, {} as Record<string, TagInfo[]>);

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <RefreshCw className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
          <Text className="mt-4 text-gray-600">Carregando tags disponíveis...</Text>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <Title className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BarChart3 className="h-8 w-8 text-blue-600" />
            Tendências Históricas
          </Title>
          <Text className="text-gray-500 mt-1">
            Visualize e analise dados históricos de tags industriais
          </Text>
        </div>
        {lastUpdated && (
          <Badge color="blue" className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Última consulta: {lastUpdated.toLocaleTimeString('pt-BR')}
          </Badge>
        )}
      </div>

      {/* Tag Selection Card */}
      <Card>
        <Title className="text-base font-semibold mb-4">Selecionar Tags</Title>

        {/* Selected Tags as Chips */}
        {selectedTags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {selectedTags.map((tag, idx) => (
              <span
                key={tag.id}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold text-white shadow-md"
                style={{
                  backgroundColor: CHART_COLORS[idx % CHART_COLORS.length],
                }}
              >
                <span className="w-2.5 h-2.5 rounded-full bg-white/30" />
                {tag.name}
                {tag.unit && <span className="text-white/80 ml-1">({tag.unit})</span>}
                <button
                  onClick={() => removeTag(tag.id)}
                  className="ml-1 hover:bg-white/20 rounded-full p-0.5 transition-colors"
                  type="button"
                >
                  <X className="w-4 h-4 text-white" />
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Compact Tag Selector with Dropdown */}
        <div className="relative">
          <div className="flex gap-3">
            {/* Category Filter */}
            <div className="w-48">
              <Text className="text-xs font-medium text-gray-600 mb-1">Categoria</Text>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">Todas as categorias</option>
                {Object.keys(tagsByCategory).map(cat => (
                  <option key={cat} value={cat}>{cat} ({tagsByCategory[cat]?.length || 0})</option>
                ))}
              </select>
            </div>

            {/* Search and Select */}
            <div className="flex-1">
              <Text className="text-xs font-medium text-gray-600 mb-1">Buscar e selecionar tag</Text>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Digite para buscar tags..."
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setShowDropdown(true);
                  }}
                  onFocus={() => setShowDropdown(true)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />

                {/* Dropdown */}
                {showDropdown && (
                  <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-64 overflow-y-auto">
                    {filteredTags.length === 0 ? (
                      <div className="p-3 text-sm text-gray-500 text-center">
                        Nenhuma tag encontrada
                      </div>
                    ) : (
                      filteredTags.slice(0, 50).map(tag => {
                        const isSelected = selectedTags.some(t => t.id === tag.id);
                        const isDisabled = !isSelected && selectedTags.length >= 8;
                        return (
                          <button
                            key={tag.id}
                            type="button"
                            onClick={() => {
                              toggleTag(tag);
                              setSearchTerm('');
                            }}
                            disabled={isDisabled}
                            className={`
                              w-full px-3 py-2 text-left text-sm flex items-center justify-between hover:bg-gray-50 border-b border-gray-100 last:border-0
                              ${isSelected ? 'bg-blue-50' : ''}
                              ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                            `}
                          >
                            <div className="flex items-center gap-2">
                              {isSelected && <CheckCircle className="w-4 h-4 text-blue-600" />}
                              <span className={isSelected ? 'font-medium text-blue-700' : 'text-gray-700'}>
                                {tag.name}
                              </span>
                              {tag.unit && <span className="text-gray-400 text-xs">({tag.unit})</span>}
                            </div>
                            <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded">
                              {tag.category}
                            </span>
                          </button>
                        );
                      })
                    )}
                    {filteredTags.length > 50 && (
                      <div className="p-2 text-xs text-gray-400 text-center bg-gray-50">
                        Mostrando 50 de {filteredTags.length} resultados. Refine sua busca.
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Click outside to close dropdown */}
          {showDropdown && (
            <div
              className="fixed inset-0 z-40"
              onClick={() => setShowDropdown(false)}
            />
          )}
        </div>

        <Text className="text-xs text-gray-400 mt-3">
          {selectedTags.length}/8 tags selecionadas • {availableTags.length} tags disponíveis
        </Text>
      </Card>

      {/* Time Range & Controls Card */}
      <Card>
        <Grid numItems={1} numItemsMd={3} className="gap-6">
          {/* Time Range Presets */}
          <div className="md:col-span-2">
            <Text className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
              <Clock className="w-5 h-5 text-blue-600" />
              Período
            </Text>
            <div className="flex flex-wrap gap-2">
              {TIME_RANGES.map(range => (
                <button
                  type="button"
                  key={range.value}
                  onClick={() => setTimeRange(range.value)}
                  className={`
                    px-4 py-2.5 rounded-lg text-sm font-semibold transition-all border-2 cursor-pointer
                    ${timeRange === range.value
                      ? 'bg-blue-600 text-white shadow-lg border-blue-600'
                      : 'bg-white text-gray-700 border-gray-200 hover:border-blue-400 hover:bg-blue-50 hover:shadow-sm'
                    }
                  `}
                >
                  {range.label}
                </button>
              ))}
            </div>
          </div>

          {/* Chart Type */}
          <div>
            <Text className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-600" />
              Tipo de Gráfico
            </Text>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => {
                  console.log('Setting chart type to line');
                  setChartType('line');
                }}
                className={`
                  flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all border-2 cursor-pointer
                  ${chartType === 'line'
                    ? 'bg-blue-600 text-white shadow-lg border-blue-600'
                    : 'bg-white text-gray-700 border-gray-200 hover:border-blue-400 hover:bg-blue-50 hover:shadow-sm'
                  }
                `}
              >
                <LineChart className="w-5 h-5" />
                Linha
              </button>
              <button
                type="button"
                onClick={() => {
                  console.log('Setting chart type to area');
                  setChartType('area');
                }}
                className={`
                  flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all border-2 cursor-pointer
                  ${chartType === 'area'
                    ? 'bg-blue-600 text-white shadow-lg border-blue-600'
                    : 'bg-white text-gray-700 border-gray-200 hover:border-blue-400 hover:bg-blue-50 hover:shadow-sm'
                  }
                `}
              >
                <BarChart3 className="w-5 h-5" />
                Área
              </button>
            </div>
          </div>
        </Grid>

        {/* Action Buttons */}
        <Flex className="mt-6 gap-3" justifyContent="start">
          <Button
            icon={loadingHistory ? RefreshCw : Play}
            loading={loadingHistory}
            onClick={loadHistoricalData}
            disabled={selectedTags.length === 0}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {loadingHistory ? 'Carregando...' : 'Carregar Dados'}
          </Button>
          <Button
            icon={Download}
            variant="secondary"
            onClick={exportCSV}
            disabled={historyData.length === 0}
          >
            Exportar CSV
          </Button>
        </Flex>
      </Card>

      {/* Statistics Cards - Only show when data is loaded */}
      {statistics.length > 0 && (
        <Grid numItems={2} numItemsSm={3} numItemsMd={4} numItemsLg={selectedTags.length <= 4 ? selectedTags.length : 4} className="gap-4">
          {statistics.map((stat, idx) => (
            <Card
              key={stat.tagId}
              className="relative overflow-hidden"
              style={{ borderTop: `4px solid ${CHART_COLORS[idx % CHART_COLORS.length]}` }}
            >
              <Flex alignItems="start" justifyContent="between">
                <Text className="text-xs text-gray-500 truncate" title={stat.tagName}>
                  {stat.tagName}
                </Text>
                {stat.trend === 'up' ? (
                  <TrendingUp className="w-4 h-4 text-emerald-500" />
                ) : stat.trend === 'down' ? (
                  <TrendingDown className="w-4 h-4 text-rose-500" />
                ) : (
                  <Activity className="w-4 h-4 text-gray-400" />
                )}
              </Flex>
              <Metric className="text-2xl mt-1">
                {stat.current.toFixed(2)}
                <span className="text-xs font-normal text-gray-400 ml-1">{stat.unit}</span>
              </Metric>
              <Flex className="mt-2 gap-3 text-xs text-gray-500">
                <span>Min: {stat.min.toFixed(1)}</span>
                <span>Max: {stat.max.toFixed(1)}</span>
                <span>Avg: {stat.avg.toFixed(1)}</span>
              </Flex>
              <Badge
                color={stat.changePercent > 0 ? 'emerald' : stat.changePercent < 0 ? 'rose' : 'gray'}
                size="xs"
                className="mt-2"
              >
                {stat.changePercent > 0 ? '+' : ''}{stat.changePercent.toFixed(1)}%
              </Badge>
            </Card>
          ))}
        </Grid>
      )}

      {/* Empty State - Before loading data */}
      {selectedTags.length === 0 && (
        <Card className="text-center py-16">
          <BarChart3 className="w-20 h-20 text-gray-200 mx-auto mb-4" />
          <Title className="text-gray-600">Selecione Tags para Visualizar</Title>
          <Text className="text-gray-400 mt-2 max-w-md mx-auto">
            Escolha até 8 tags na seção acima para visualizar seus dados históricos.
            Depois clique em "Carregar Dados" para buscar o histórico.
          </Text>
        </Card>
      )}

      {/* Empty State - Tags selected but no data loaded yet */}
      {selectedTags.length > 0 && historyData.length === 0 && !loadingHistory && (
        <Card className="text-center py-16">
          <Play className="w-20 h-20 text-gray-200 mx-auto mb-4" />
          <Title className="text-gray-600">Clique em "Carregar Dados"</Title>
          <Text className="text-gray-400 mt-2 max-w-md mx-auto">
            Você selecionou {selectedTags.length} tag(s). Escolha o período desejado e
            clique no botão "Carregar Dados" para visualizar o histórico.
          </Text>
        </Card>
      )}

      {/* Main Chart */}
      {historyData.length > 0 && (
        <Card>
          <Flex justifyContent="between" alignItems="start" className="mb-4">
            <div>
              <Title>Gráfico de Tendências</Title>
              <Text className="text-gray-500">
                {historyData.length} pontos de dados • {selectedTags.length} tag(s)
              </Text>
            </div>
          </Flex>

          {chartType === 'line' ? (
            <ProfessionalLineChart
              data={historyData}
              xAxisKey="time"
              lines={chartLines}
              height={450}
              showGrid={true}
              showLegend={true}
            />
          ) : (
            <div className="space-y-6">
              {chartLines.map((line, idx) => (
                <div key={line.dataKey}>
                  <Flex alignItems="center" className="mb-2">
                    <div
                      className="w-3 h-3 rounded-full mr-2"
                      style={{ backgroundColor: line.color }}
                    />
                    <Text className="font-medium">{line.name}</Text>
                  </Flex>
                  <ProfessionalAreaChart
                    data={historyData}
                    xAxisKey="time"
                    dataKey={line.dataKey}
                    color={line.color}
                    height={180}
                    showGrid={true}
                  />
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

    </div>
  );
}
