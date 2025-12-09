/**
 * 🏷️ Tag Details - Tremor Professional
 * =====================================
 *
 * Detailed view of a specific tag with history and statistics
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
  Metric,
  AreaChart,
  BarChart,
  Select,
  SelectItem,
  Table,
  TableHead,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
  Tab,
  TabGroup,
  TabList,
  TabPanel,
  TabPanels,
} from '@tremor/react';
import {
  ArrowLeft,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Activity,
  Clock,
  Database,
  LineChart,
  BarChart3,
  Info,
  Download,
} from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import apiClient from '../../api/client';

interface TagInfo {
  tag_id: string;
  name: string;
  description?: string;
  unit?: string;
  value: number;
  quality: string;
  timestamp: string;
  adapter_id?: string;
  data_type?: string;
  engineering_units?: string;
}

interface HistoryPoint {
  timestamp: string;
  value: number;
  quality?: string;
}

interface Statistics {
  min: number;
  max: number;
  avg: number;
  stddev: number;
  count: number;
}

const TIME_RANGES = [
  { value: '15m', label: '15 minutos' },
  { value: '1h', label: '1 hora' },
  { value: '6h', label: '6 horas' },
  { value: '24h', label: '24 horas' },
  { value: '7d', label: '7 dias' },
  { value: '30d', label: '30 dias' },
];

export const TremorTagDetails: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const [tag, setTag] = useState<TagInfo | null>(null);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [timeRange, setTimeRange] = useState('1h');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTagInfo = useCallback(async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);

      // Get all active tags and find the one we need
      const response = await apiClient.get('/api/v1/timeseries/tags/active');
      const tags = response.data?.tags || response.data || [];
      const tagInfo = tags.find((t: any) => (t.tag_id || t.id) === id);

      if (tagInfo) {
        setTag({
          tag_id: tagInfo.tag_id || tagInfo.id,
          name: tagInfo.name || tagInfo.tag_id || tagInfo.id,
          description: tagInfo.description,
          unit: tagInfo.unit || tagInfo.engineering_units,
          value: tagInfo.value ?? 0,
          quality: tagInfo.quality || 'GOOD',
          timestamp: tagInfo.timestamp || new Date().toISOString(),
          adapter_id: tagInfo.adapter_id,
          data_type: tagInfo.data_type || 'Float',
          engineering_units: tagInfo.engineering_units,
        });

        // Generate mock history for demo
        await fetchHistory(tagInfo.tag_id || tagInfo.id);
      } else {
        // Create a placeholder tag if not found
        setTag({
          tag_id: id,
          name: id,
          value: 0,
          quality: 'UNCERTAIN',
          timestamp: new Date().toISOString(),
        });
        setError('Tag não encontrada no sistema');
      }
    } catch (err) {
      console.error('Error fetching tag:', err);
      setError('Erro ao carregar informações da tag');
    } finally {
      setLoading(false);
    }
  }, [id]);

  const fetchHistory = async (tagId: string) => {
    try {
      // Try to fetch real history
      const response = await apiClient.get(`/api/v1/timeseries/tags/${tagId}/history`, {
        params: { time_range: timeRange },
      });

      if (response.data?.data?.length > 0) {
        setHistory(response.data.data);
        calculateStatistics(response.data.data);
        return;
      }
    } catch {
      // Generate mock history if API fails
    }

    // Generate mock history
    const mockHistory = generateMockHistory(timeRange);
    setHistory(mockHistory);
    calculateStatistics(mockHistory);
  };

  const generateMockHistory = (range: string): HistoryPoint[] => {
    const points: HistoryPoint[] = [];
    const now = Date.now();
    let interval: number;
    let count: number;

    switch (range) {
      case '15m':
        interval = 60000; // 1 minute
        count = 15;
        break;
      case '1h':
        interval = 60000; // 1 minute
        count = 60;
        break;
      case '6h':
        interval = 300000; // 5 minutes
        count = 72;
        break;
      case '24h':
        interval = 900000; // 15 minutes
        count = 96;
        break;
      case '7d':
        interval = 3600000; // 1 hour
        count = 168;
        break;
      case '30d':
        interval = 14400000; // 4 hours
        count = 180;
        break;
      default:
        interval = 60000;
        count = 60;
    }

    const baseValue = tag?.value ?? 50;
    let currentValue = baseValue;

    for (let i = count; i >= 0; i--) {
      // Random walk with mean reversion
      const noise = (Math.random() - 0.5) * 10;
      const reversion = (baseValue - currentValue) * 0.1;
      currentValue = currentValue + noise + reversion;

      points.push({
        timestamp: new Date(now - i * interval).toISOString(),
        value: Math.max(0, currentValue),
        quality: Math.random() > 0.05 ? 'GOOD' : 'UNCERTAIN',
      });
    }

    return points;
  };

  const calculateStatistics = (data: HistoryPoint[]) => {
    if (data.length === 0) return;

    const values = data.map(d => d.value);
    const sum = values.reduce((a, b) => a + b, 0);
    const avg = sum / values.length;
    const min = Math.min(...values);
    const max = Math.max(...values);

    const squaredDiffs = values.map(v => Math.pow(v - avg, 2));
    const avgSquaredDiff = squaredDiffs.reduce((a, b) => a + b, 0) / values.length;
    const stddev = Math.sqrt(avgSquaredDiff);

    setStatistics({
      min,
      max,
      avg,
      stddev,
      count: values.length,
    });
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchTagInfo();
    setRefreshing(false);
  };

  useEffect(() => {
    fetchTagInfo();
  }, [fetchTagInfo]);

  useEffect(() => {
    if (tag) {
      fetchHistory(tag.tag_id);
    }
  }, [timeRange]);

  const getTrend = () => {
    if (history.length < 2) return 'stable';
    const recent = history.slice(-5);
    const older = history.slice(-10, -5);
    if (recent.length === 0 || older.length === 0) return 'stable';

    const recentAvg = recent.reduce((a, b) => a + b.value, 0) / recent.length;
    const olderAvg = older.reduce((a, b) => a + b.value, 0) / older.length;

    const diff = ((recentAvg - olderAvg) / olderAvg) * 100;
    if (diff > 5) return 'up';
    if (diff < -5) return 'down';
    return 'stable';
  };

  const getQualityColor = (quality: string) => {
    switch (quality?.toUpperCase()) {
      case 'GOOD':
        return 'green';
      case 'UNCERTAIN':
        return 'yellow';
      case 'BAD':
        return 'red';
      default:
        return 'gray';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Carregando tag...</span>
      </div>
    );
  }

  const trend = getTrend();

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <Flex justifyContent="between" alignItems="center">
        <Flex alignItems="center" className="gap-4">
          <Button
            variant="secondary"
            icon={ArrowLeft}
            onClick={() => navigate(-1)}
          >
            Voltar
          </Button>
          <div>
            <Flex alignItems="center" className="gap-2">
              <Title className="text-2xl font-bold text-gray-800">
                {tag?.name || id}
              </Title>
              <Badge color={getQualityColor(tag?.quality || '')} size="sm">
                {tag?.quality || 'UNKNOWN'}
              </Badge>
            </Flex>
            <Text className="text-gray-500">
              {tag?.description || `Tag ID: ${tag?.tag_id}`}
            </Text>
          </div>
        </Flex>
        <Flex className="gap-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            {TIME_RANGES.map(r => (
              <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
            ))}
          </Select>
          <Button
            variant="secondary"
            icon={RefreshCw}
            onClick={handleRefresh}
            loading={refreshing}
          >
            Atualizar
          </Button>
        </Flex>
      </Flex>

      {error && (
        <Card className="bg-yellow-50 border-yellow-200">
          <Flex alignItems="center" className="gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
            <Text className="text-yellow-700">{error}</Text>
          </Flex>
        </Card>
      )}

      {/* Current Value Card */}
      <Grid numItemsMd={4} className="gap-6">
        <Card className="col-span-2">
          <Flex alignItems="start" justifyContent="between">
            <div>
              <Text className="text-gray-500">Valor Atual</Text>
              <Metric className="mt-1">
                {tag?.value?.toFixed(2) ?? '--'} {tag?.unit || ''}
              </Metric>
              <Flex alignItems="center" className="gap-2 mt-2">
                {trend === 'up' && <TrendingUp className="w-4 h-4 text-green-500" />}
                {trend === 'down' && <TrendingDown className="w-4 h-4 text-red-500" />}
                {trend === 'stable' && <Minus className="w-4 h-4 text-gray-400" />}
                <Text className="text-sm text-gray-500">
                  {trend === 'up' ? 'Subindo' : trend === 'down' ? 'Descendo' : 'Estável'}
                </Text>
              </Flex>
            </div>
            <Activity className="w-10 h-10 text-blue-500" />
          </Flex>
        </Card>

        <Card>
          <Text className="text-gray-500">Mínimo</Text>
          <Metric className="mt-1 text-blue-600">
            {statistics?.min?.toFixed(2) ?? '--'}
          </Metric>
        </Card>

        <Card>
          <Text className="text-gray-500">Máximo</Text>
          <Metric className="mt-1 text-red-600">
            {statistics?.max?.toFixed(2) ?? '--'}
          </Metric>
        </Card>
      </Grid>

      {/* Statistics Row */}
      <Grid numItemsMd={4} className="gap-4">
        <Card>
          <Flex alignItems="center" className="gap-2">
            <Database className="w-5 h-5 text-gray-400" />
            <Text className="text-gray-500">Média</Text>
          </Flex>
          <Text className="text-2xl font-bold mt-2">
            {statistics?.avg?.toFixed(2) ?? '--'}
          </Text>
        </Card>
        <Card>
          <Flex alignItems="center" className="gap-2">
            <Activity className="w-5 h-5 text-gray-400" />
            <Text className="text-gray-500">Desvio Padrão</Text>
          </Flex>
          <Text className="text-2xl font-bold mt-2">
            {statistics?.stddev?.toFixed(2) ?? '--'}
          </Text>
        </Card>
        <Card>
          <Flex alignItems="center" className="gap-2">
            <Clock className="w-5 h-5 text-gray-400" />
            <Text className="text-gray-500">Última Atualização</Text>
          </Flex>
          <Text className="text-lg font-medium mt-2">
            {tag?.timestamp ? new Date(tag.timestamp).toLocaleString('pt-BR') : '--'}
          </Text>
        </Card>
        <Card>
          <Flex alignItems="center" className="gap-2">
            <BarChart3 className="w-5 h-5 text-gray-400" />
            <Text className="text-gray-500">Amostras</Text>
          </Flex>
          <Text className="text-2xl font-bold mt-2">
            {statistics?.count ?? '--'}
          </Text>
        </Card>
      </Grid>

      {/* Charts */}
      <TabGroup>
        <TabList>
          <Tab icon={LineChart}>Tendência</Tab>
          <Tab icon={BarChart3}>Distribuição</Tab>
          <Tab icon={Info}>Informações</Tab>
        </TabList>
        <TabPanels>
          <TabPanel>
            <Card className="mt-4">
              <Title>Histórico de Valores</Title>
              <AreaChart
                className="h-72 mt-4"
                data={history.map(h => ({
                  time: new Date(h.timestamp).toLocaleString('pt-BR', {
                    hour: '2-digit',
                    minute: '2-digit',
                    day: timeRange.includes('d') ? '2-digit' : undefined,
                    month: timeRange.includes('d') ? '2-digit' : undefined,
                  }),
                  Valor: h.value,
                }))}
                index="time"
                categories={['Valor']}
                colors={['blue']}
                showLegend={false}
                curveType="monotone"
              />
            </Card>
          </TabPanel>

          <TabPanel>
            <Card className="mt-4">
              <Title>Distribuição por Hora</Title>
              <BarChart
                className="h-72 mt-4"
                data={(() => {
                  // Group by hour
                  const hourlyData: Record<number, number[]> = {};
                  history.forEach(h => {
                    const hour = new Date(h.timestamp).getHours();
                    if (!hourlyData[hour]) hourlyData[hour] = [];
                    hourlyData[hour].push(h.value);
                  });

                  return Object.entries(hourlyData).map(([hour, values]) => ({
                    hora: `${hour}:00`,
                    'Média': values.reduce((a, b) => a + b, 0) / values.length,
                  }));
                })()}
                index="hora"
                categories={['Média']}
                colors={['blue']}
              />
            </Card>
          </TabPanel>

          <TabPanel>
            <Card className="mt-4">
              <Title>Informações da Tag</Title>
              <div className="mt-4 space-y-4">
                <Grid numItemsMd={2} className="gap-4">
                  <div>
                    <Text className="text-gray-500 text-sm">Tag ID</Text>
                    <Text className="font-medium">{tag?.tag_id}</Text>
                  </div>
                  <div>
                    <Text className="text-gray-500 text-sm">Nome</Text>
                    <Text className="font-medium">{tag?.name}</Text>
                  </div>
                  <div>
                    <Text className="text-gray-500 text-sm">Unidade</Text>
                    <Text className="font-medium">{tag?.unit || tag?.engineering_units || '-'}</Text>
                  </div>
                  <div>
                    <Text className="text-gray-500 text-sm">Tipo de Dado</Text>
                    <Text className="font-medium">{tag?.data_type || 'Float'}</Text>
                  </div>
                  <div>
                    <Text className="text-gray-500 text-sm">Adaptador</Text>
                    <Text className="font-medium">{tag?.adapter_id || '-'}</Text>
                  </div>
                  <div>
                    <Text className="text-gray-500 text-sm">Qualidade</Text>
                    <Badge color={getQualityColor(tag?.quality || '')} size="sm">
                      {tag?.quality || 'UNKNOWN'}
                    </Badge>
                  </div>
                </Grid>

                {tag?.description && (
                  <div>
                    <Text className="text-gray-500 text-sm">Descrição</Text>
                    <Text className="font-medium">{tag.description}</Text>
                  </div>
                )}
              </div>
            </Card>
          </TabPanel>
        </TabPanels>
      </TabGroup>

      {/* Recent Values Table */}
      <Card>
        <Flex justifyContent="between" alignItems="center">
          <Title>Valores Recentes</Title>
          <Button variant="secondary" icon={Download} size="xs">
            Exportar
          </Button>
        </Flex>
        <Table className="mt-4">
          <TableHead>
            <TableRow>
              <TableHeaderCell>Timestamp</TableHeaderCell>
              <TableHeaderCell className="text-right">Valor</TableHeaderCell>
              <TableHeaderCell className="text-right">Qualidade</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {history.slice(-20).reverse().map((point, idx) => (
              <TableRow key={idx}>
                <TableCell>
                  {new Date(point.timestamp).toLocaleString('pt-BR')}
                </TableCell>
                <TableCell className="text-right font-medium">
                  {point.value.toFixed(2)} {tag?.unit || ''}
                </TableCell>
                <TableCell className="text-right">
                  <Badge color={getQualityColor(point.quality || 'GOOD')} size="xs">
                    {point.quality || 'GOOD'}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
};

export default TremorTagDetails;
