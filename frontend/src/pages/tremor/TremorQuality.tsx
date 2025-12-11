/**
 * Alarm Analysis Dashboard - Análise de Alarmes
 * ==============================================
 *
 * Dashboard simplificado com funcionalidades reais:
 * - Pareto Analysis com dados reais de AlarmEvent
 * - Ishikawa (Fishbone) dinâmico via ML API
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Title,
  Text,
  Metric,
  Flex,
  Grid,
  Badge,
  Button,
  TabGroup,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Callout,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  TableHeaderCell,
  TextInput,
} from '@tremor/react';
import {
  BarChart3,
  AlertTriangle,
  Target,
  TrendingDown,
  RefreshCw,
  Download,
  Lightbulb,
  GitBranch,
  Users,
  Settings,
  Package,
  Ruler,
  Leaf,
  ClipboardList,
  Search,
  AlertCircle,
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import apiClient from '../../api/client';
import {
  ProfessionalBarChart,
} from '../../components/charts/ProfessionalCharts';
import { selectStylesSmall } from '../../components/common/StyledSelect';

// Types
interface ParetoItem {
  rank: number;
  alarm_type: string;
  category: string;
  count: number;
  percent: number;
  cumulative_percent: number;
  is_vital_few: boolean;
  estimated_cost: number;
  equipment_family?: string;
  severity?: string;
}

interface IshikawaCause {
  cause: string;
  probability: number;
  status: string;
  source?: string;
}

interface IshikawaCategory {
  name: string;
  icon: string;
  causes: IshikawaCause[];
  total_probability?: number;
}

// Helper functions
const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
  }).format(value);
};

const getCategoryIcon = (categoryId: string) => {
  const icons: Record<string, React.ReactNode> = {
    mao_de_obra: <Users className="w-5 h-5" />,
    maquina: <Settings className="w-5 h-5" />,
    material: <Package className="w-5 h-5" />,
    metodo: <ClipboardList className="w-5 h-5" />,
    medicao: <Ruler className="w-5 h-5" />,
    meio_ambiente: <Leaf className="w-5 h-5" />,
  };
  return icons[categoryId] || <AlertCircle className="w-5 h-5" />;
};

const getCategoryColor = (categoryId: string): string => {
  const colors: Record<string, string> = {
    mao_de_obra: 'blue',
    maquina: 'red',
    material: 'emerald',
    metodo: 'violet',
    medicao: 'amber',
    meio_ambiente: 'teal',
  };
  return colors[categoryId] || 'gray';
};

export const TremorQuality: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(0);
  const [timeRange, setTimeRange] = useState('7d');
  const [paretoData, setParetoData] = useState<ParetoItem[]>([]);
  const [paretoSummary, setParetoSummary] = useState<any>(null);
  const [ishikawaData, setIshikawaData] = useState<Record<string, IshikawaCategory>>({});
  const [ishikawaProblem, setIshikawaProblem] = useState('');
  const [ishikawaLoading, setIshikawaLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [error, setError] = useState<string | null>(null);

  // Fetch Pareto data from real AlarmEvent
  const fetchParetoData = useCallback(async () => {
    try {
      const response = await apiClient.get('/api/v1/quality/pareto/alarms', {
        params: { time_range: timeRange, limit: 10, include_actions: true },
      });

      if (response.data) {
        setParetoData(response.data.pareto || []);
        setParetoSummary(response.data.summary || null);
      }
    } catch (err) {
      console.error('Error fetching Pareto data:', err);
      // Set empty state instead of fake data
      setParetoData([]);
      setParetoSummary(null);
    }
  }, [timeRange]);

  // Fetch Ishikawa analysis from ML API
  const fetchIshikawaAnalysis = useCallback(async (problem?: string) => {
    setIshikawaLoading(true);
    try {
      // Try to get categories first
      const categoriesResponse = await apiClient.get('/api/v1/ml/ishikawa/categories');

      if (problem) {
        // Get dynamic analysis for specific problem
        const analysisResponse = await apiClient.post('/api/v1/ml/ishikawa/analyze', null, {
          params: { problem, hours: timeRange === '24h' ? 24 : timeRange === '7d' ? 168 : 720 }
        });

        if (analysisResponse.data?.categories) {
          setIshikawaData(analysisResponse.data.categories);
        }
      } else {
        // Use default categories structure
        const categories = categoriesResponse.data?.categories || [];
        const categoriesMap: Record<string, IshikawaCategory> = {};

        categories.forEach((cat: any) => {
          categoriesMap[cat.id] = {
            name: cat.name,
            icon: cat.icon,
            causes: cat.typical_causes?.map((cause: string) => ({
              cause,
              probability: 0,
              status: 'template',
            })) || [],
          };
        });

        setIshikawaData(categoriesMap);
      }
    } catch (err) {
      console.error('Error fetching Ishikawa data:', err);
      // Set default 6M structure
      setIshikawaData({
        mao_de_obra: { name: 'Mão de Obra', icon: '👤', causes: [] },
        maquina: { name: 'Máquina', icon: '⚙️', causes: [] },
        material: { name: 'Material', icon: '📦', causes: [] },
        metodo: { name: 'Método', icon: '📋', causes: [] },
        medicao: { name: 'Medição', icon: '📏', causes: [] },
        meio_ambiente: { name: 'Meio Ambiente', icon: '🌡️', causes: [] },
      });
    } finally {
      setIshikawaLoading(false);
    }
  }, [timeRange]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      await Promise.all([
        fetchParetoData(),
        fetchIshikawaAnalysis(),
      ]);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Erro ao carregar dados de análise');
    } finally {
      setLoading(false);
    }
  }, [fetchParetoData, fetchIshikawaAnalysis]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Handle Ishikawa problem search
  const handleIshikawaSearch = () => {
    if (ishikawaProblem.trim()) {
      fetchIshikawaAnalysis(ishikawaProblem);
    }
  };

  // Prepare Pareto chart data
  const paretoChartData = paretoData.map((p) => ({
    tipo: p.alarm_type.length > 20 ? p.alarm_type.substring(0, 20) + '...' : p.alarm_type,
    Quantidade: p.count,
    'Acumulado %': p.cumulative_percent,
  }));

  if (loading && !paretoData.length) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-700 font-medium">Carregando análises...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 bg-slate-50 min-h-screen -m-6 p-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-violet-900 via-purple-900 to-slate-900 rounded-xl p-6 text-white shadow-2xl">
        <Flex justifyContent="between" alignItems="start" className="flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-violet-500/20 rounded-lg">
                <BarChart3 className="w-8 h-8 text-violet-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Análise de Alarmes</h1>
                <p className="text-violet-300 text-sm">
                  Pareto • Causa Raiz • {format(lastUpdated, "dd/MM HH:mm", { locale: ptBR })}
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-2 text-sm font-medium border border-white/30 rounded-lg bg-white/10 text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-violet-400 cursor-pointer appearance-none backdrop-blur"
              style={{
                ...selectStylesSmall,
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='white'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
                minWidth: '130px'
              }}
            >
              <option value="24h" className="text-gray-900">24 horas</option>
              <option value="7d" className="text-gray-900">7 dias</option>
              <option value="30d" className="text-gray-900">30 dias</option>
            </select>
            <Button size="xs" variant="secondary" icon={RefreshCw} onClick={fetchData}>
              Atualizar
            </Button>
            <Button size="xs" variant="secondary" icon={Download}>
              Exportar
            </Button>
          </div>
        </Flex>

        {/* Quick Stats */}
        <div className="mt-6 grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white/10 rounded-xl p-4 backdrop-blur">
            <p className="text-violet-200 text-xs font-medium">Total de Alarmes</p>
            <p className="text-3xl font-bold mt-1 text-white">
              {paretoSummary?.total_alarms || 0}
            </p>
            <p className="text-violet-300 text-xs">no período</p>
          </div>

          <div className="bg-white/10 rounded-xl p-4 backdrop-blur">
            <p className="text-violet-200 text-xs font-medium">Vital Few (80/20)</p>
            <p className="text-3xl font-bold mt-1 text-red-400">
              {paretoSummary?.vital_few_count || 0}
            </p>
            <p className="text-violet-300 text-xs">tipos causam 80% problemas</p>
          </div>

          <div className="bg-white/10 rounded-xl p-4 backdrop-blur">
            <p className="text-violet-200 text-xs font-medium">Tipos de Alarme</p>
            <p className="text-3xl font-bold mt-1 text-amber-400">
              {paretoSummary?.total_types || paretoData.length}
            </p>
            <p className="text-violet-300 text-xs">identificados</p>
          </div>

          <div className="bg-white/10 rounded-xl p-4 backdrop-blur">
            <p className="text-violet-200 text-xs font-medium">Custo Estimado</p>
            <p className="text-2xl font-bold mt-1 text-emerald-400">
              {formatCurrency(paretoSummary?.total_estimated_cost || 0)}
            </p>
            <p className="text-violet-300 text-xs">impacto no período</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <TabGroup index={activeTab} onIndexChange={setActiveTab}>
        <TabList variant="solid" className="bg-white rounded-lg p-1">
          <Tab icon={BarChart3}>Pareto Analysis</Tab>
          <Tab icon={GitBranch}>Causa Raiz (Ishikawa)</Tab>
        </TabList>

        <TabPanels>
          {/* Pareto Tab */}
          <TabPanel>
            {paretoData.length > 0 ? (
              <>
                <Grid numItemsSm={1} numItemsLg={3} className="gap-6 mt-6">
                  {/* Pareto Summary */}
                  <Card className="bg-white">
                    <Title>Resumo Pareto</Title>
                    <Text>Análise 80/20 dos alarmes</Text>

                    <div className="mt-6 space-y-4">
                      <div className="p-4 bg-gradient-to-r from-red-50 to-amber-50 rounded-lg">
                        <Flex justifyContent="between">
                          <div>
                            <p className="text-gray-600 text-sm">Total de Alarmes</p>
                            <p className="text-3xl font-bold text-gray-900">{paretoSummary?.total_alarms || 0}</p>
                          </div>
                          <BarChart3 className="w-10 h-10 text-red-500" />
                        </Flex>
                      </div>

                      <div className="p-4 bg-gradient-to-r from-violet-50 to-blue-50 rounded-lg">
                        <Flex justifyContent="between">
                          <div>
                            <p className="text-gray-600 text-sm">Vital Few (80%)</p>
                            <p className="text-3xl font-bold text-violet-600">{paretoSummary?.vital_few_count || 0}</p>
                            <p className="text-xs text-gray-500">de {paretoSummary?.total_types || 0} tipos</p>
                          </div>
                          <Target className="w-10 h-10 text-violet-500" />
                        </Flex>
                      </div>

                      <div className="p-4 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-lg">
                        <Flex justifyContent="between">
                          <div>
                            <p className="text-gray-600 text-sm">Custo Estimado</p>
                            <p className="text-2xl font-bold text-emerald-600">{formatCurrency(paretoSummary?.total_estimated_cost || 0)}</p>
                          </div>
                          <TrendingDown className="w-10 h-10 text-emerald-500" />
                        </Flex>
                      </div>
                    </div>

                    {paretoSummary?.pareto_insight && (
                      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                        <Flex alignItems="start" className="gap-3">
                          <Lightbulb className="w-5 h-5 text-blue-600 mt-0.5" />
                          <div>
                            <p className="font-medium text-blue-900">Insight Pareto</p>
                            <p className="text-sm text-blue-700">{paretoSummary.pareto_insight}</p>
                          </div>
                        </Flex>
                      </div>
                    )}
                  </Card>

                  {/* Pareto Chart */}
                  <Card className="bg-white lg:col-span-2">
                    <Title>Gráfico de Pareto</Title>
                    <Text>Alarmes por frequência</Text>

                    <div className="mt-4" style={{ height: '350px' }}>
                      <ProfessionalBarChart
                        data={paretoChartData}
                        xAxisKey="tipo"
                        categories={['Quantidade']}
                        colors={['#ef4444']}
                        height={320}
                        showGrid={true}
                        showLegend={true}
                      />
                    </div>

                    {/* Legend */}
                    <div className="mt-4 flex items-center gap-4 justify-center">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-red-500 rounded" />
                        <span className="text-sm text-gray-600">Quantidade</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-red-200 rounded" />
                        <span className="text-sm text-gray-600">Vital Few (80%)</span>
                      </div>
                    </div>
                  </Card>
                </Grid>

                {/* Pareto Details Table */}
                <Card className="bg-white mt-6">
                  <Title>Detalhamento do Pareto</Title>
                  <Text>Ranking completo dos alarmes</Text>

                  <Table className="mt-4">
                    <TableHead>
                      <TableRow>
                        <TableHeaderCell>#</TableHeaderCell>
                        <TableHeaderCell>Tipo de Alarme</TableHeaderCell>
                        <TableHeaderCell>Categoria</TableHeaderCell>
                        <TableHeaderCell className="text-right">Qtd</TableHeaderCell>
                        <TableHeaderCell className="text-right">%</TableHeaderCell>
                        <TableHeaderCell className="text-right">Acum.</TableHeaderCell>
                        <TableHeaderCell className="text-right">Custo Est.</TableHeaderCell>
                        <TableHeaderCell>Status</TableHeaderCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {paretoData.map((item) => (
                        <TableRow key={item.rank} className={item.is_vital_few ? 'bg-red-50' : ''}>
                          <TableCell>
                            <Badge color={item.is_vital_few ? 'red' : 'gray'} size="sm">{item.rank}</Badge>
                          </TableCell>
                          <TableCell className="font-medium">{item.alarm_type}</TableCell>
                          <TableCell>
                            <Badge color="blue" size="sm">{item.category}</Badge>
                          </TableCell>
                          <TableCell className="text-right font-bold">{item.count}</TableCell>
                          <TableCell className="text-right">{item.percent.toFixed(1)}%</TableCell>
                          <TableCell className="text-right">
                            <span className={item.cumulative_percent <= 80 ? 'text-red-600 font-medium' : ''}>
                              {item.cumulative_percent.toFixed(1)}%
                            </span>
                          </TableCell>
                          <TableCell className="text-right text-emerald-600 font-medium">
                            {formatCurrency(item.estimated_cost)}
                          </TableCell>
                          <TableCell>
                            {item.is_vital_few ? (
                              <Badge color="red" size="sm">Vital Few</Badge>
                            ) : (
                              <Badge color="gray" size="sm">Trivial Many</Badge>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Card>
              </>
            ) : (
              <Card className="bg-white mt-6">
                <div className="text-center py-12">
                  <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <Title>Sem dados de alarmes</Title>
                  <Text className="mt-2">
                    Não há alarmes registrados no período selecionado para análise Pareto.
                  </Text>
                </div>
              </Card>
            )}
          </TabPanel>

          {/* Ishikawa Tab */}
          <TabPanel>
            <Card className="bg-white mt-6">
              <Flex justifyContent="between" alignItems="center" className="mb-6">
                <div>
                  <Title>Diagrama de Ishikawa (6M)</Title>
                  <Text>Análise de Causa Raiz - Método dos 6Ms</Text>
                </div>
                <div className="flex items-center gap-2">
                  <TextInput
                    placeholder="Descreva o problema a analisar..."
                    value={ishikawaProblem}
                    onChange={(e) => setIshikawaProblem(e.target.value)}
                    className="w-80"
                  />
                  <Button
                    icon={Search}
                    onClick={handleIshikawaSearch}
                    loading={ishikawaLoading}
                  >
                    Analisar
                  </Button>
                </div>
              </Flex>

              {ishikawaLoading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-violet-600 mx-auto mb-4"></div>
                  <Text>Analisando causas raiz...</Text>
                </div>
              ) : Object.keys(ishikawaData).length > 0 ? (
                <div>
                  {/* Main Effect Line */}
                  <div className="flex items-center justify-center mb-8">
                    <div className="flex-1 h-1 bg-gray-400"></div>
                    <div className="px-6 py-3 bg-red-600 text-white font-bold rounded-lg text-lg">
                      {ishikawaProblem || 'Problema: Análise de Alarmes'}
                    </div>
                  </div>

                  {/* 6M Categories */}
                  <Grid numItemsSm={2} numItemsLg={3} className="gap-6">
                    {Object.entries(ishikawaData).map(([categoryId, category]) => {
                      const color = getCategoryColor(categoryId);
                      return (
                        <Card
                          key={categoryId}
                          decoration="left"
                          decorationColor={color as any}
                          className={`bg-${color}-50`}
                        >
                          <Flex alignItems="center" className="gap-2 mb-3">
                            {getCategoryIcon(categoryId)}
                            <Title className={`text-${color}-900`}>{category.name}</Title>
                            {category.total_probability && category.total_probability > 0 && (
                              <Badge color={color as any} size="sm">
                                {(category.total_probability * 100).toFixed(0)}%
                              </Badge>
                            )}
                          </Flex>

                          {category.causes.length > 0 ? (
                            <div className="space-y-2">
                              {category.causes.slice(0, 4).map((cause, idx) => (
                                <div key={idx} className="flex items-center justify-between text-sm">
                                  <span className="text-gray-700">{cause.cause}</span>
                                  {cause.probability > 0 && (
                                    <Badge
                                      color={cause.probability > 0.3 ? 'red' : cause.probability > 0.15 ? 'amber' : 'gray'}
                                      size="sm"
                                    >
                                      {(cause.probability * 100).toFixed(0)}%
                                    </Badge>
                                  )}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <Text className="text-gray-500 text-sm italic">
                              Insira um problema para análise
                            </Text>
                          )}
                        </Card>
                      );
                    })}
                  </Grid>

                  {/* Instructions */}
                  <Callout
                    title="Como usar"
                    icon={Lightbulb}
                    color="blue"
                    className="mt-6"
                  >
                    Digite uma descrição do problema no campo acima (ex: "Alta taxa de alarmes de temperatura no ELEV01")
                    e clique em "Analisar" para gerar uma análise de causa raiz baseada nos dados operacionais.
                  </Callout>
                </div>
              ) : (
                <div className="text-center py-12">
                  <GitBranch className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <Title>Análise de Causa Raiz</Title>
                  <Text className="mt-2">
                    Descreva um problema no campo acima para gerar o diagrama de Ishikawa.
                  </Text>
                </div>
              )}
            </Card>
          </TabPanel>
        </TabPanels>
      </TabGroup>

      {/* Error Alert */}
      {error && (
        <Callout title="Erro ao carregar dados" icon={AlertTriangle} color="red" className="mt-6">
          {error}
        </Callout>
      )}
    </div>
  );
};

export default TremorQuality;
