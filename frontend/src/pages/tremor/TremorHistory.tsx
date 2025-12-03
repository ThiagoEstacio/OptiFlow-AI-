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
  Select,
  SelectItem,
  Grid,
  Metric,
  Flex,
  Table,
  TableHead,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
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
    const response = await apiClient.get('/api/v1/timeseries/tags/active', {
      params: { lookback_hours: 24 }
    });

    const tags = response.data?.tags || [];

    return tags.map((tag: any) => {
      const name = tag.name || tag.id || 'Tag';
      const unit = tag.unit || '';
      const value = tag.last_value ?? 0;

      return {
        id: tag.id,
        name,
        unit,
        category: getTagCategory(name, unit),
        currentValue: value,
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
    const historyPromises = tagIds.map(tagId =>
      apiClient.get(`/api/v1/demo/tags/${tagId}/history`, {
        params: { minutes }
      }).catch(() => ({ data: { data: [], tag_name: tagId } }))
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
      const historyData = response.data?.data || [];

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

  // Filter tags by search
  const filteredTags = availableTags.filter(tag =>
    tag.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tag.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium"
                style={{
                  backgroundColor: `${CHART_COLORS[idx % CHART_COLORS.length]}20`,
                  borderLeft: `4px solid ${CHART_COLORS[idx % CHART_COLORS.length]}`,
                }}
              >
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: CHART_COLORS[idx % CHART_COLORS.length] }} />
                {tag.name}
                {tag.unit && <span className="text-gray-400">({tag.unit})</span>}
                <button
                  onClick={() => removeTag(tag.id)}
                  className="ml-1 hover:bg-gray-200 rounded-full p-0.5"
                >
                  <X className="w-3.5 h-3.5 text-gray-500" />
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Search Input */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <TextInput
            placeholder="Buscar tags por nome ou categoria..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Tags Grid by Category */}
        <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-lg p-3 bg-white">
          {Object.entries(tagsByCategory).map(([category, tags]) => (
            <div key={category} className="mb-4 last:mb-0">
              <Text className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                {category}
              </Text>
              <div className="flex flex-wrap gap-2">
                {tags.map(tag => {
                  const isSelected = selectedTags.some(t => t.id === tag.id);
                  const selectedIndex = selectedTags.findIndex(t => t.id === tag.id);
                  return (
                    <button
                      key={tag.id}
                      onClick={() => toggleTag(tag)}
                      disabled={!isSelected && selectedTags.length >= 8}
                      className={`
                        px-3 py-1.5 rounded-lg text-sm transition-all
                        ${isSelected
                          ? 'text-white shadow-md'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed'
                        }
                      `}
                      style={isSelected ? { backgroundColor: CHART_COLORS[selectedIndex % CHART_COLORS.length] } : {}}
                    >
                      {isSelected && <CheckCircle className="w-3.5 h-3.5 inline mr-1" />}
                      {tag.name}
                      {tag.unit && <span className="opacity-70 ml-1">({tag.unit})</span>}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        <Text className="text-xs text-gray-400 mt-2">
          {selectedTags.length}/8 tags selecionados • {availableTags.length} tags disponíveis
        </Text>
      </Card>

      {/* Time Range & Controls Card */}
      <Card>
        <Grid numItems={1} numItemsMd={3} className="gap-6">
          {/* Time Range Presets */}
          <div className="md:col-span-2">
            <Text className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4 text-gray-500" />
              Período
            </Text>
            <div className="flex flex-wrap gap-2">
              {TIME_RANGES.map(range => (
                <button
                  key={range.value}
                  onClick={() => setTimeRange(range.value)}
                  className={`
                    px-4 py-2 rounded-lg text-sm font-medium transition-all
                    ${timeRange === range.value
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
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
            <Text className="text-sm font-semibold mb-3 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-gray-500" />
              Tipo de Gráfico
            </Text>
            <div className="flex gap-2">
              <button
                onClick={() => setChartType('line')}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
                  ${chartType === 'line'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }
                `}
              >
                <LineChart className="w-4 h-4" />
                Linha
              </button>
              <button
                onClick={() => setChartType('area')}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
                  ${chartType === 'area'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }
                `}
              >
                <BarChart3 className="w-4 h-4" />
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

      {/* Data Table */}
      {historyData.length > 0 && (
        <Card>
          <Title>Dados Tabulares</Title>
          <Text className="text-gray-500 mb-4">
            Últimos {Math.min(historyData.length, 50)} registros
          </Text>
          <div className="overflow-x-auto">
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Timestamp</TableHeaderCell>
                  {selectedTags.map((tag, idx) => (
                    <TableHeaderCell key={tag.id}>
                      <Flex alignItems="center" className="gap-2">
                        <div
                          className="w-2 h-2 rounded-full"
                          style={{ backgroundColor: CHART_COLORS[idx % CHART_COLORS.length] }}
                        />
                        {tag.name}
                      </Flex>
                    </TableHeaderCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {historyData.slice(-50).reverse().map((point, idx) => (
                  <TableRow key={idx}>
                    <TableCell>
                      <Text className="text-sm">{point.time}</Text>
                    </TableCell>
                    {selectedTags.map(tag => (
                      <TableCell key={tag.id}>
                        <Text className="font-mono">
                          {typeof point[tag.name] === 'number'
                            ? (point[tag.name] as number).toFixed(2)
                            : '-'
                          }
                        </Text>
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </Card>
      )}
    </div>
  );
}
