/**
 * Quality Analytics Dashboard - Ferramentas de Qualidade Industrial
 * =================================================================
 *
 * Dashboard profissional com:
 * - SPC/CEP (Statistical Process Control)
 * - Control Charts (X-bar R, I-MR)
 * - Process Capability (Cp, Cpk, Pp, Ppk)
 * - Pareto Analysis com drill-down
 * - Ishikawa (Fishbone) visualization
 * - PDCA Cycle tracking
 * - 5W2H Action Plans
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
  BadgeDelta,
  Button,
  Select,
  SelectItem,
  TabGroup,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  ProgressBar,
  Callout,
  List,
  ListItem,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  TableHeaderCell,
} from '@tremor/react';
import {
  BarChart3,
  LineChart,
  Target,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Activity,
  Gauge,
  RefreshCw,
  Download,
  Filter,
  ChevronRight,
  AlertCircle,
  Lightbulb,
  ClipboardList,
  GitBranch,
  Settings,
  Wrench,
  Users,
  Package,
  Thermometer,
  Ruler,
  Leaf,
  Workflow,
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import apiClient from '../../api/client';
import {
  ProfessionalAreaChart,
  ProfessionalBarChart,
  ProfessionalLineChart,
} from '../../components/charts/ProfessionalCharts';

// Types
interface SPCData {
  summary: {
    total_samples: number;
    total_subgroups: number;
    grand_mean: number;
    sigma_estimated: number;
    percent_in_control: number;
    out_of_control_signals: number;
  };
  control_limits: {
    x_bar: { ucl: number; cl: number; lcl: number };
    r: { ucl: number; cl: number; lcl: number };
  };
  capability?: {
    cp: number;
    cpk: number;
    pp: number;
    ppk: number;
    status: string;
    six_sigma_level: number;
    ppm_out_of_spec: number;
    yield_percent: number;
  };
  chart_data: {
    x_bar_chart: {
      center_line: number;
      ucl: number;
      lcl: number;
      data: Array<{ subgroup: number; value: number; in_control: boolean }>;
    };
  };
  out_of_control_signals: Array<{
    rule: number;
    description: string;
    subgroup: number;
    severity: string;
    action: string;
  }>;
  recommendations: Array<{
    priority: string;
    type: string;
    title: string;
    description: string;
    action: string;
  }>;
}

interface ParetoItem {
  rank: number;
  alarm_type: string;
  category: string;
  count: number;
  percent: number;
  cumulative_percent: number;
  is_vital_few: boolean;
  estimated_cost: number;
  actions?: Array<{
    priority: string;
    action: string;
    estimated_time: string;
    responsible: string;
  }>;
}

interface PDCACycle {
  id: string;
  title: string;
  current_phase: string;
  progress_percent: number;
  owner: string;
  priority: string;
}

// Helper functions
const getCapabilityColor = (cpk: number): 'emerald' | 'amber' | 'red' | 'blue' => {
  if (cpk >= 1.33) return 'emerald';
  if (cpk >= 1.0) return 'amber';
  return 'red';
};

const getCapabilityStatus = (cpk: number): string => {
  if (cpk >= 1.67) return 'Excelente';
  if (cpk >= 1.33) return 'Bom';
  if (cpk >= 1.0) return 'Capaz';
  if (cpk >= 0.67) return 'Marginal';
  return 'Incapaz';
};

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
  }).format(value);
};

export const TremorQuality: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(0);
  const [timeRange, setTimeRange] = useState('24h');
  const [selectedTag, setSelectedTag] = useState('SILO01_UMIDADE');
  const [spcData, setSpcData] = useState<SPCData | null>(null);
  const [paretoData, setParetoData] = useState<ParetoItem[]>([]);
  const [paretoSummary, setParetoSummary] = useState<any>(null);
  const [pdcaCycles, setPdcaCycles] = useState<PDCACycle[]>([]);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [spcRes, paretoRes, pdcaRes] = await Promise.all([
        apiClient.get(`/api/v1/quality/spc/analysis`, {
          params: {
            tag_id: selectedTag,
            duration: timeRange,
            subgroup_size: 5,
            usl: 14,  // Example spec limits for moisture
            lsl: 10,
            target: 12,
          },
        }).catch(() => ({ data: null })),
        apiClient.get(`/api/v1/quality/pareto/alarms`, {
          params: { time_range: '7d', limit: 10, include_actions: true },
        }).catch(() => ({ data: null })),
        apiClient.get(`/api/v1/quality/pdca/cycles`).catch(() => ({ data: null })),
      ]);

      if (spcRes.data) {
        setSpcData(spcRes.data);
      }
      if (paretoRes.data) {
        setParetoData(paretoRes.data.pareto || []);
        setParetoSummary(paretoRes.data.summary);
      }
      if (pdcaRes.data) {
        setPdcaCycles(pdcaRes.data.cycles || []);
      }

      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching quality data:', err);
      setError('Erro ao carregar dados de qualidade');
    } finally {
      setLoading(false);
    }
  }, [selectedTag, timeRange]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Prepare chart data for SPC
  const xBarChartData = spcData?.chart_data?.x_bar_chart?.data?.map((d) => ({
    subgrupo: d.subgroup,
    Média: d.value,
    UCL: spcData.chart_data.x_bar_chart.ucl,
    LCL: spcData.chart_data.x_bar_chart.lcl,
    CL: spcData.chart_data.x_bar_chart.center_line,
  })) || [];

  // Prepare Pareto chart data
  const paretoChartData = paretoData.map((p) => ({
    tipo: p.alarm_type.length > 15 ? p.alarm_type.substring(0, 15) + '...' : p.alarm_type,
    Quantidade: p.count,
    'Acumulado %': p.cumulative_percent,
  }));

  if (loading && !spcData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-700 font-medium">Carregando análises de qualidade...</p>
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
                <Gauge className="w-8 h-8 text-violet-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Quality Analytics</h1>
                <p className="text-violet-300 text-sm">
                  SPC/CEP • Pareto • Ishikawa • PDCA • {format(lastUpdated, "dd/MM HH:mm", { locale: ptBR })}
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Select value={timeRange} onValueChange={setTimeRange} className="w-28">
              <SelectItem value="1h">1 hora</SelectItem>
              <SelectItem value="6h">6 horas</SelectItem>
              <SelectItem value="24h">24 horas</SelectItem>
              <SelectItem value="7d">7 dias</SelectItem>
              <SelectItem value="30d">30 dias</SelectItem>
            </Select>
            <Button size="xs" variant="secondary" icon={RefreshCw} onClick={fetchData}>
              Atualizar
            </Button>
            <Button size="xs" variant="secondary" icon={Download}>
              Exportar
            </Button>
          </div>
        </Flex>

        {/* Quick Stats */}
        <div className="mt-6 grid grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="bg-white/10 rounded-xl p-4 backdrop-blur">
            <p className="text-violet-200 text-xs font-medium">Cpk</p>
            <p className={`text-3xl font-bold mt-1 ${spcData?.capability?.cpk && spcData.capability.cpk >= 1.33 ? 'text-emerald-400' : 'text-amber-400'}`}>
              {spcData?.capability?.cpk?.toFixed(2) || '--'}
            </p>
            <Badge color={getCapabilityColor(spcData?.capability?.cpk || 0)} size="sm" className="mt-1">
              {getCapabilityStatus(spcData?.capability?.cpk || 0)}
            </Badge>
          </div>

          <div className="bg-white/10 rounded-xl p-4 backdrop-blur">
            <p className="text-violet-200 text-xs font-medium">% Em Controle</p>
            <p className={`text-3xl font-bold mt-1 ${(spcData?.summary?.percent_in_control || 0) >= 95 ? 'text-emerald-400' : 'text-amber-400'}`}>
              {spcData?.summary?.percent_in_control?.toFixed(1) || '--'}%
            </p>
            <p className="text-violet-300 text-xs">{spcData?.summary?.out_of_control_signals || 0} sinais OOC</p>
          </div>

          <div className="bg-white/10 rounded-xl p-4 backdrop-blur">
            <p className="text-violet-200 text-xs font-medium">Sigma Nível</p>
            <p className="text-3xl font-bold mt-1 text-blue-400">
              {spcData?.capability?.six_sigma_level?.toFixed(1) || '--'}σ
            </p>
            <p className="text-violet-300 text-xs">PPM: {spcData?.capability?.ppm_out_of_spec?.toFixed(0) || '--'}</p>
          </div>

          <div className="bg-white/10 rounded-xl p-4 backdrop-blur">
            <p className="text-violet-200 text-xs font-medium">Vital Few (80/20)</p>
            <p className="text-3xl font-bold mt-1 text-red-400">
              {paretoSummary?.vital_few_count || '--'}
            </p>
            <p className="text-violet-300 text-xs">tipos causam 80% problemas</p>
          </div>

          <div className="bg-white/10 rounded-xl p-4 backdrop-blur">
            <p className="text-violet-200 text-xs font-medium">Ciclos PDCA</p>
            <p className="text-3xl font-bold mt-1 text-emerald-400">
              {pdcaCycles.length}
            </p>
            <p className="text-violet-300 text-xs">{pdcaCycles.filter(c => c.current_phase === 'check').length} em verificação</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <TabGroup index={activeTab} onIndexChange={setActiveTab}>
        <TabList variant="solid" className="bg-white rounded-lg p-1">
          <Tab icon={LineChart}>SPC / Control Charts</Tab>
          <Tab icon={BarChart3}>Pareto Analysis</Tab>
          <Tab icon={GitBranch}>Ishikawa (6M)</Tab>
          <Tab icon={Workflow}>PDCA Cycles</Tab>
          <Tab icon={ClipboardList}>Action Plans</Tab>
        </TabList>

        <TabPanels>
          {/* SPC Tab */}
          <TabPanel>
            <Grid numItemsSm={1} numItemsLg={3} className="gap-6 mt-6">
              {/* Process Capability Card */}
              <Card className="bg-white">
                <Flex justifyContent="between" alignItems="start">
                  <div>
                    <Title>Capacidade do Processo</Title>
                    <Text>Índices de Capabilidade (Cp, Cpk, Pp, Ppk)</Text>
                  </div>
                  <Badge color={getCapabilityColor(spcData?.capability?.cpk || 0)} size="lg">
                    {getCapabilityStatus(spcData?.capability?.cpk || 0)}
                  </Badge>
                </Flex>

                <div className="mt-6 space-y-4">
                  <div>
                    <Flex justifyContent="between" className="mb-2">
                      <Text>Cp (Potencial)</Text>
                      <Text className="font-bold">{spcData?.capability?.cp?.toFixed(3) || '--'}</Text>
                    </Flex>
                    <ProgressBar value={Math.min((spcData?.capability?.cp || 0) / 2 * 100, 100)} color="blue" />
                  </div>

                  <div>
                    <Flex justifyContent="between" className="mb-2">
                      <Text>Cpk (Real)</Text>
                      <Text className="font-bold">{spcData?.capability?.cpk?.toFixed(3) || '--'}</Text>
                    </Flex>
                    <ProgressBar
                      value={Math.min((spcData?.capability?.cpk || 0) / 2 * 100, 100)}
                      color={getCapabilityColor(spcData?.capability?.cpk || 0)}
                    />
                  </div>

                  <div>
                    <Flex justifyContent="between" className="mb-2">
                      <Text>Ppk (Longo Prazo)</Text>
                      <Text className="font-bold">{spcData?.capability?.ppk?.toFixed(3) || '--'}</Text>
                    </Flex>
                    <ProgressBar value={Math.min((spcData?.capability?.ppk || 0) / 2 * 100, 100)} color="violet" />
                  </div>
                </div>

                <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-violet-50 rounded-lg">
                  <Grid numItemsSm={2} className="gap-4">
                    <div className="text-center">
                      <p className="text-gray-600 text-sm">Nível Sigma</p>
                      <p className="text-2xl font-bold text-blue-600">{spcData?.capability?.six_sigma_level?.toFixed(1) || '--'}σ</p>
                    </div>
                    <div className="text-center">
                      <p className="text-gray-600 text-sm">Yield</p>
                      <p className="text-2xl font-bold text-emerald-600">{spcData?.capability?.yield_percent?.toFixed(4) || '--'}%</p>
                    </div>
                  </Grid>
                </div>
              </Card>

              {/* X-bar Chart */}
              <Card className="bg-white lg:col-span-2">
                <Flex justifyContent="between" alignItems="start">
                  <div>
                    <Title>Carta de Controle X̄ (Médias)</Title>
                    <Text>Tag: {selectedTag} • {spcData?.summary?.total_subgroups || 0} subgrupos</Text>
                  </div>
                  <Select value={selectedTag} onValueChange={setSelectedTag} className="w-48">
                    <SelectItem value="SILO01_UMIDADE">Silo 01 - Umidade</SelectItem>
                    <SelectItem value="SILO02_UMIDADE">Silo 02 - Umidade</SelectItem>
                    <SelectItem value="TEMP_MOTOR_01">Temperatura Motor 01</SelectItem>
                    <SelectItem value="PRESSAO_HIDRAULICA">Pressão Hidráulica</SelectItem>
                  </Select>
                </Flex>

                <div className="mt-4" style={{ height: '300px' }}>
                  <ProfessionalLineChart
                    data={xBarChartData}
                    xAxisKey="subgrupo"
                    lines={[
                      { dataKey: 'Média', name: 'Média', color: '#3b82f6', strokeWidth: 2 },
                      { dataKey: 'UCL', name: 'UCL (+3σ)', color: '#ef4444', strokeWidth: 1 },
                      { dataKey: 'LCL', name: 'LCL (-3σ)', color: '#ef4444', strokeWidth: 1 },
                      { dataKey: 'CL', name: 'CL (Média)', color: '#6b7280', strokeWidth: 1 },
                    ]}
                    height={280}
                    showGrid={true}
                    showLegend={true}
                  />
                </div>

                <div className="mt-4 grid grid-cols-3 gap-4 text-center">
                  <div className="p-3 bg-red-50 rounded-lg">
                    <p className="text-red-600 font-bold text-lg">{spcData?.control_limits?.x_bar?.ucl?.toFixed(2) || '--'}</p>
                    <p className="text-red-600 text-xs">UCL (+3σ)</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-gray-800 font-bold text-lg">{spcData?.control_limits?.x_bar?.cl?.toFixed(2) || '--'}</p>
                    <p className="text-gray-600 text-xs">CL (Média)</p>
                  </div>
                  <div className="p-3 bg-red-50 rounded-lg">
                    <p className="text-red-600 font-bold text-lg">{spcData?.control_limits?.x_bar?.lcl?.toFixed(2) || '--'}</p>
                    <p className="text-red-600 text-xs">LCL (-3σ)</p>
                  </div>
                </div>
              </Card>
            </Grid>

            {/* Out of Control Signals and Recommendations */}
            <Grid numItemsSm={1} numItemsLg={2} className="gap-6 mt-6">
              <Card className="bg-white">
                <Flex justifyContent="between" alignItems="center" className="mb-4">
                  <div>
                    <Title>Sinais Fora de Controle</Title>
                    <Text>Regras de Nelson detectadas</Text>
                  </div>
                  <Badge color="red" size="lg">{spcData?.out_of_control_signals?.length || 0}</Badge>
                </Flex>

                {spcData?.out_of_control_signals && spcData.out_of_control_signals.length > 0 ? (
                  <div className="space-y-3">
                    {spcData.out_of_control_signals.map((signal, idx) => (
                      <div key={idx} className={`p-3 rounded-lg ${signal.severity === 'critical' ? 'bg-red-50 border border-red-200' : 'bg-amber-50 border border-amber-200'}`}>
                        <Flex justifyContent="between" alignItems="center">
                          <div className="flex items-center gap-2">
                            <AlertTriangle className={`w-4 h-4 ${signal.severity === 'critical' ? 'text-red-600' : 'text-amber-600'}`} />
                            <span className="font-medium text-gray-900">Regra {signal.rule}</span>
                          </div>
                          <Badge color={signal.severity === 'critical' ? 'red' : 'amber'} size="sm">
                            Subgrupo {signal.subgroup}
                          </Badge>
                        </Flex>
                        <p className="text-sm text-gray-600 mt-1">{signal.description}</p>
                        <p className="text-xs text-blue-600 mt-1">{signal.action}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <Callout title="Processo em Controle" icon={CheckCircle} color="emerald">
                    Nenhum sinal fora de controle detectado. O processo está estatisticamente estável.
                  </Callout>
                )}
              </Card>

              <Card className="bg-white">
                <Title>Recomendações SPC</Title>
                <Text>Ações baseadas na análise estatística</Text>

                <div className="mt-4 space-y-3">
                  {spcData?.recommendations?.map((rec, idx) => (
                    <Callout
                      key={idx}
                      title={rec.title}
                      icon={rec.priority === 'critical' ? AlertCircle : rec.priority === 'high' ? AlertTriangle : rec.priority === 'info' ? Lightbulb : CheckCircle}
                      color={rec.priority === 'critical' ? 'red' : rec.priority === 'high' ? 'amber' : rec.priority === 'info' ? 'blue' : 'emerald'}
                    >
                      <p className="text-sm">{rec.description}</p>
                      <p className="text-xs font-medium mt-1">{rec.action}</p>
                    </Callout>
                  ))}
                </div>
              </Card>
            </Grid>
          </TabPanel>

          {/* Pareto Tab */}
          <TabPanel>
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

                <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                  <Flex alignItems="start" className="gap-3">
                    <Lightbulb className="w-5 h-5 text-blue-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-blue-900">Insight Pareto</p>
                      <p className="text-sm text-blue-700">{paretoSummary?.pareto_insight || 'Focando nos poucos vitais para máximo impacto'}</p>
                    </div>
                  </Flex>
                </div>
              </Card>

              {/* Pareto Chart */}
              <Card className="bg-white lg:col-span-2">
                <Title>Gráfico de Pareto</Title>
                <Text>Alarmes por frequência com linha acumulada</Text>

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
                    <div className="w-8 h-0.5 bg-gray-800" />
                    <span className="text-sm text-gray-600">% Acumulado</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-0.5 bg-amber-500 border-dashed border-2" />
                    <span className="text-sm text-gray-600">Limite 80%</span>
                  </div>
                </div>
              </Card>
            </Grid>

            {/* Pareto Details Table */}
            <Card className="bg-white mt-6">
              <Title>Detalhamento do Pareto</Title>
              <Text>Ranking completo com ações recomendadas</Text>

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
          </TabPanel>

          {/* Ishikawa Tab */}
          <TabPanel>
            <Card className="bg-white mt-6">
              <Title>Diagrama de Ishikawa (6M)</Title>
              <Text>Análise de Causa e Efeito - Método dos 6Ms</Text>

              <div className="mt-8">
                {/* Ishikawa Visual */}
                <div className="relative">
                  {/* Main Effect Line */}
                  <div className="flex items-center justify-center mb-8">
                    <div className="flex-1 h-1 bg-gray-400"></div>
                    <div className="px-6 py-3 bg-red-600 text-white font-bold rounded-lg text-lg">
                      Problema: Alta Taxa de Alarmes
                    </div>
                  </div>

                  {/* 6M Categories */}
                  <Grid numItemsSm={2} numItemsLg={3} className="gap-6">
                    {/* Man */}
                    <Card decoration="left" decorationColor="blue" className="bg-blue-50">
                      <Flex alignItems="center" className="gap-2 mb-3">
                        <Users className="w-5 h-5 text-blue-600" />
                        <Title className="text-blue-900">Mão de Obra (Man)</Title>
                      </Flex>
                      <List>
                        <ListItem>
                          <span>Falta de treinamento específico</span>
                          <Badge color="amber" size="sm">30%</Badge>
                        </ListItem>
                        <ListItem>
                          <span>Rotatividade alta da equipe</span>
                          <Badge color="amber" size="sm">20%</Badge>
                        </ListItem>
                        <ListItem>
                          <span>Fadiga/Stress do operador</span>
                          <Badge color="gray" size="sm">15%</Badge>
                        </ListItem>
                      </List>
                    </Card>

                    {/* Machine */}
                    <Card decoration="left" decorationColor="red" className="bg-red-50">
                      <Flex alignItems="center" className="gap-2 mb-3">
                        <Settings className="w-5 h-5 text-red-600" />
                        <Title className="text-red-900">Máquina (Machine)</Title>
                      </Flex>
                      <List>
                        <ListItem>
                          <span>Desgaste de rolamentos</span>
                          <Badge color="red" size="sm">45%</Badge>
                        </ListItem>
                        <ListItem>
                          <span>Desalinhamento do eixo</span>
                          <Badge color="red" size="sm">35%</Badge>
                        </ListItem>
                        <ListItem>
                          <span>Lubrificação inadequada</span>
                          <Badge color="amber" size="sm">40%</Badge>
                        </ListItem>
                      </List>
                    </Card>

                    {/* Material */}
                    <Card decoration="left" decorationColor="emerald" className="bg-emerald-50">
                      <Flex alignItems="center" className="gap-2 mb-3">
                        <Package className="w-5 h-5 text-emerald-600" />
                        <Title className="text-emerald-900">Material</Title>
                      </Flex>
                      <List>
                        <ListItem>
                          <span>Contaminação do produto</span>
                          <Badge color="gray" size="sm">15%</Badge>
                        </ListItem>
                        <ListItem>
                          <span>Variação de granulometria</span>
                          <Badge color="amber" size="sm">20%</Badge>
                        </ListItem>
                        <ListItem>
                          <span>Umidade acima do especificado</span>
                          <Badge color="amber" size="sm">25%</Badge>
                        </ListItem>
                      </List>
                    </Card>

                    {/* Method */}
                    <Card decoration="left" decorationColor="violet" className="bg-violet-50">
                      <Flex alignItems="center" className="gap-2 mb-3">
                        <ClipboardList className="w-5 h-5 text-violet-600" />
                        <Title className="text-violet-900">Método (Method)</Title>
                      </Flex>
                      <List>
                        <ListItem>
                          <span>Procedimento desatualizado</span>
                          <Badge color="red" size="sm">35%</Badge>
                        </ListItem>
                        <ListItem>
                          <span>Falta de padronização</span>
                          <Badge color="amber" size="sm">25%</Badge>
                        </ListItem>
                        <ListItem>
                          <span>Sequência de partida incorreta</span>
                          <Badge color="amber" size="sm">30%</Badge>
                        </ListItem>
                      </List>
                    </Card>

                    {/* Measurement */}
                    <Card decoration="left" decorationColor="amber" className="bg-amber-50">
                      <Flex alignItems="center" className="gap-2 mb-3">
                        <Ruler className="w-5 h-5 text-amber-600" />
                        <Title className="text-amber-900">Medição (Measurement)</Title>
                      </Flex>
                      <List>
                        <ListItem>
                          <span>Sensor descalibrado</span>
                          <Badge color="red" size="sm">40%</Badge>
                        </ListItem>
                        <ListItem>
                          <span>Frequência de medição inadequada</span>
                          <Badge color="amber" size="sm">20%</Badge>
                        </ListItem>
                        <ListItem>
                          <span>Erro de leitura/interpretação</span>
                          <Badge color="gray" size="sm">15%</Badge>
                        </ListItem>
                      </List>
                    </Card>

                    {/* Environment */}
                    <Card decoration="left" decorationColor="teal" className="bg-teal-50">
                      <Flex alignItems="center" className="gap-2 mb-3">
                        <Leaf className="w-5 h-5 text-teal-600" />
                        <Title className="text-teal-900">Meio Ambiente</Title>
                      </Flex>
                      <List>
                        <ListItem>
                          <span>Temperatura ambiente elevada</span>
                          <Badge color="amber" size="sm">30%</Badge>
                        </ListItem>
                        <ListItem>
                          <span>Poeira/Contaminação do ar</span>
                          <Badge color="amber" size="sm">25%</Badge>
                        </ListItem>
                        <ListItem>
                          <span>Vibração de equipamentos vizinhos</span>
                          <Badge color="gray" size="sm">20%</Badge>
                        </ListItem>
                      </List>
                    </Card>
                  </Grid>
                </div>
              </div>
            </Card>
          </TabPanel>

          {/* PDCA Tab */}
          <TabPanel>
            <Grid numItemsSm={1} numItemsLg={4} className="gap-4 mt-6">
              {/* PDCA Phase Cards */}
              <Card className="bg-blue-50">
                <Flex alignItems="center" className="gap-2 mb-3">
                  <div className="p-2 bg-blue-600 rounded-full">
                    <Target className="w-4 h-4 text-white" />
                  </div>
                  <Title className="text-blue-900">PLAN</Title>
                </Flex>
                <Metric className="text-blue-600">{pdcaCycles.filter(c => c.current_phase === 'plan').length}</Metric>
                <Text>ciclos em planejamento</Text>
              </Card>

              <Card className="bg-amber-50">
                <Flex alignItems="center" className="gap-2 mb-3">
                  <div className="p-2 bg-amber-600 rounded-full">
                    <Wrench className="w-4 h-4 text-white" />
                  </div>
                  <Title className="text-amber-900">DO</Title>
                </Flex>
                <Metric className="text-amber-600">{pdcaCycles.filter(c => c.current_phase === 'do').length}</Metric>
                <Text>ciclos em execução</Text>
              </Card>

              <Card className="bg-violet-50">
                <Flex alignItems="center" className="gap-2 mb-3">
                  <div className="p-2 bg-violet-600 rounded-full">
                    <Activity className="w-4 h-4 text-white" />
                  </div>
                  <Title className="text-violet-900">CHECK</Title>
                </Flex>
                <Metric className="text-violet-600">{pdcaCycles.filter(c => c.current_phase === 'check').length}</Metric>
                <Text>ciclos em verificação</Text>
              </Card>

              <Card className="bg-emerald-50">
                <Flex alignItems="center" className="gap-2 mb-3">
                  <div className="p-2 bg-emerald-600 rounded-full">
                    <CheckCircle className="w-4 h-4 text-white" />
                  </div>
                  <Title className="text-emerald-900">ACT</Title>
                </Flex>
                <Metric className="text-emerald-600">{pdcaCycles.filter(c => c.current_phase === 'act').length}</Metric>
                <Text>ciclos em padronização</Text>
              </Card>
            </Grid>

            {/* PDCA Cycles List */}
            <Card className="bg-white mt-6">
              <Title>Ciclos PDCA Ativos</Title>
              <Text>Projetos de melhoria contínua em andamento</Text>

              <div className="mt-4 space-y-4">
                {pdcaCycles.map((cycle) => (
                  <div key={cycle.id} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <Flex justifyContent="between" alignItems="start" className="mb-3">
                      <div>
                        <p className="font-bold text-gray-900">{cycle.title}</p>
                        <p className="text-sm text-gray-600">{cycle.id} • {cycle.owner}</p>
                      </div>
                      <div className="text-right">
                        <Badge
                          color={
                            cycle.current_phase === 'plan' ? 'blue' :
                            cycle.current_phase === 'do' ? 'amber' :
                            cycle.current_phase === 'check' ? 'violet' : 'emerald'
                          }
                          size="lg"
                        >
                          {cycle.current_phase.toUpperCase()}
                        </Badge>
                        <Badge color={cycle.priority === 'high' ? 'red' : 'gray'} size="sm" className="ml-2">
                          {cycle.priority}
                        </Badge>
                      </div>
                    </Flex>
                    <Flex justifyContent="between" alignItems="center">
                      <ProgressBar value={cycle.progress_percent} color="blue" className="flex-1 mr-4" />
                      <span className="text-sm font-medium text-gray-700">{cycle.progress_percent}%</span>
                    </Flex>
                  </div>
                ))}
              </div>
            </Card>
          </TabPanel>

          {/* Action Plans Tab */}
          <TabPanel>
            <Card className="bg-white mt-6">
              <Flex justifyContent="between" alignItems="center" className="mb-4">
                <div>
                  <Title>Planos de Ação 5W2H</Title>
                  <Text>Ações estruturadas para eliminação de problemas</Text>
                </div>
                <Button icon={ClipboardList} variant="primary">
                  Novo Plano
                </Button>
              </Flex>

              <div className="overflow-x-auto">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableHeaderCell>O Quê</TableHeaderCell>
                      <TableHeaderCell>Por Quê</TableHeaderCell>
                      <TableHeaderCell>Onde</TableHeaderCell>
                      <TableHeaderCell>Quando</TableHeaderCell>
                      <TableHeaderCell>Quem</TableHeaderCell>
                      <TableHeaderCell>Como</TableHeaderCell>
                      <TableHeaderCell>Quanto</TableHeaderCell>
                      <TableHeaderCell>Status</TableHeaderCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell className="font-medium">Substituir rolamentos ELEV01</TableCell>
                      <TableCell>Eliminar vibração excessiva</TableCell>
                      <TableCell>Área de Elevadores</TableCell>
                      <TableCell>2025-01-15</TableCell>
                      <TableCell>Manutenção Mecânica</TableCell>
                      <TableCell>Troca preventiva + alinhamento</TableCell>
                      <TableCell>R$ 3.300</TableCell>
                      <TableCell><Badge color="amber">Em Andamento</Badge></TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Recalibrar sensores de temperatura</TableCell>
                      <TableCell>Reduzir alarmes falsos</TableCell>
                      <TableCell>Laboratório</TableCell>
                      <TableCell>2025-01-10</TableCell>
                      <TableCell>Instrumentação</TableCell>
                      <TableCell>Calibração + certificado</TableCell>
                      <TableCell>R$ 500</TableCell>
                      <TableCell><Badge color="blue">Planejado</Badge></TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Atualizar procedimento de partida</TableCell>
                      <TableCell>Padronizar operação</TableCell>
                      <TableCell>Engenharia</TableCell>
                      <TableCell>2025-01-20</TableCell>
                      <TableCell>Eng. Processos</TableCell>
                      <TableCell>Revisar + treinar + validar</TableCell>
                      <TableCell>R$ 0 (interno)</TableCell>
                      <TableCell><Badge color="emerald">Concluído</Badge></TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            </Card>
          </TabPanel>
        </TabPanels>
      </TabGroup>

      {/* Error Alert */}
      {error && (
        <Callout title="Erro ao carregar dados" icon={AlertCircle} color="red" className="mt-6">
          {error}
        </Callout>
      )}
    </div>
  );
};

export default TremorQuality;
