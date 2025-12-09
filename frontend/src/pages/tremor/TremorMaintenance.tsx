/**
 * 🔧 Maintenance Dashboard (PCM) - MELH-005
 * ==========================================
 *
 * Central de Manutenção com 4 tabs:
 * - Saúde dos Ativos
 * - Indicadores KPI (MTBF/MTTR)
 * - Backlog e Planejamento
 * - Análise de Falhas
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Card,
  Title,
  Text,
  Metric,
  Flex,
  Grid,
  ProgressBar,
  Badge,
  BadgeDelta,
  TabGroup,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Table,
  TableHead,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
  Callout,
  Button,
} from '@tremor/react';
import {
  ProfessionalAreaChart,
  ProfessionalDonutChart,
  ProfessionalBarChart,
  ProfessionalMultiBarChart,
} from '../../components/charts/ProfessionalCharts';
import {
  Wrench,
  Clock,
  Activity,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Settings,
  RefreshCw,
  Download,
  Calendar,
  Package,
  FileText,
  Target,
  Gauge,
  Heart,
  Zap,
  Timer,
  XCircle,
} from 'lucide-react';
import { format } from 'date-fns';
import apiClient from '../../api/client';

// Tab routing mapping
const TAB_ROUTES: Record<string, number> = {
  '/maintenance': 0,           // Saúde dos Ativos
  '/maintenance/pcm': 0,       // Saúde dos Ativos
  '/maintenance/kpis': 1,      // Indicadores KPI
  '/maintenance/backlog': 2,   // Backlog
  '/maintenance/analysis': 3,  // Análise de Falhas
};

const ROUTE_BY_TAB: Record<number, string> = {
  0: '/maintenance',
  1: '/maintenance/kpis',
  2: '/maintenance/backlog',
  3: '/maintenance/analysis',
};

// Types
interface EquipmentHealth {
  equipment_id: string;
  equipment_name: string;
  health_score: number;
  mtbf_hours: number | null;
  mttr_hours: number | null;
  availability_percent: number;
  failure_count: number;
  status: 'healthy' | 'attention' | 'warning' | 'critical';
}

interface MaintenanceKPI {
  mtbf_hours: number | null;
  mttr_hours: number | null;
  availability_percent: number | null;
  reliability_24h_percent: number | null;
  total_downtime_hours: number;
}

interface WorkOrder {
  id: string;
  equipment_id: string;
  type: 'preventive' | 'corrective' | 'predictive';
  priority: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  due_date: string;
  status: 'pending' | 'in_progress' | 'completed';
}

interface FailureAnalysis {
  failure_type: string;
  count: number;
  total_hours: number;
  percentage: number;
}

interface MLPrediction {
  equipment_id: string;
  equipment_name: string;
  probability: number;
  predicted_issue: string;
  recommendation: string;
}

// Component
export default function TremorMaintenance() {
  const location = useLocation();
  const navigate = useNavigate();

  // Determine initial tab from URL
  const getInitialTab = () => {
    const path = location.pathname;
    return TAB_ROUTES[path] ?? 0;
  };

  // State
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState(getInitialTab);
  const [timeRange, setTimeRange] = useState('30d');

  // Update tab when URL changes
  useEffect(() => {
    const newTab = TAB_ROUTES[location.pathname];
    if (newTab !== undefined && newTab !== selectedTab) {
      setSelectedTab(newTab);
    }
  }, [location.pathname]);

  // Handle tab change - update URL
  const handleTabChange = (index: number) => {
    setSelectedTab(index);
    const newRoute = ROUTE_BY_TAB[index];
    if (newRoute && newRoute !== location.pathname) {
      navigate(newRoute, { replace: true });
    }
  };
  const [equipmentHealth, setEquipmentHealth] = useState<EquipmentHealth[]>([]);
  const [selectedEquipment, setSelectedEquipment] = useState<string | null>(null);
  const [kpis, setKpis] = useState<MaintenanceKPI | null>(null);
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [failureAnalysis, setFailureAnalysis] = useState<FailureAnalysis[]>([]);
  const [mlPredictions, setMLPredictions] = useState<MLPrediction[]>([]);
  const [mtbfTrend, setMtbfTrend] = useState<{ month: string; mtbf_hours: number }[]>([]);

  // Fetch data
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch equipment KPIs
      const kpisResponse = await apiClient.get('/api/v1/maintenance/kpis/all', {
        params: { days: timeRange === '30d' ? 30 : timeRange === '90d' ? 90 : 7 }
      });

      if (kpisResponse.data.success) {
        setEquipmentHealth(kpisResponse.data.equipment.map((eq: any) => ({
          equipment_id: eq.equipment_id,
          equipment_name: eq.equipment_name,
          health_score: eq.availability_percent,
          mtbf_hours: eq.mtbf_hours,
          mttr_hours: eq.mttr_hours,
          availability_percent: eq.availability_percent,
          failure_count: eq.failure_count,
          status: eq.status
        })));
      }

      // Fetch downtime analysis
      const downtimeResponse = await apiClient.get('/api/v1/maintenance/downtime/analysis', {
        params: { days: 30 }
      });

      if (downtimeResponse.data.success) {
        setFailureAnalysis(downtimeResponse.data.by_failure_type.map((f: any) => ({
          failure_type: f.failure_type,
          count: f.count,
          total_hours: f.hours,
          percentage: (f.hours / downtimeResponse.data.total_downtime_hours) * 100
        })));
      }

      // Set sample work orders (would come from OS system)
      setWorkOrders(generateSampleWorkOrders());

      // Set sample ML predictions
      setMLPredictions(generateSamplePredictions());

    } catch (error) {
      console.error('Error fetching maintenance data:', error);
      // Use fallback data
      setEquipmentHealth(generateFallbackEquipment());
      setFailureAnalysis(generateFallbackFailures());
      setWorkOrders(generateSampleWorkOrders());
      setMLPredictions(generateSamplePredictions());
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  // Fetch equipment-specific KPIs
  const fetchEquipmentKPIs = async (equipmentId: string) => {
    try {
      const response = await apiClient.get(`/api/v1/maintenance/kpis/${equipmentId}`, {
        params: { days: 90 }
      });

      if (response.data.success) {
        setKpis(response.data.kpis);

        // Fetch MTBF trend
        const trendResponse = await apiClient.get(`/maintenance/mtbf/trend/${equipmentId}`, {
          params: { months: 6 }
        });

        if (trendResponse.data.success) {
          setMtbfTrend(trendResponse.data.trend_data);
        }
      }
    } catch (error) {
      console.error('Error fetching equipment KPIs:', error);
      setKpis(generateFallbackKPIs());
      setMtbfTrend(generateFallbackTrend());
    }
  };

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (selectedEquipment) {
      fetchEquipmentKPIs(selectedEquipment);
    }
  }, [selectedEquipment]);

  // Get status color
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'healthy': return 'emerald';
      case 'attention': return 'yellow';
      case 'warning': return 'orange';
      case 'critical': return 'red';
      default: return 'gray';
    }
  };

  // Get priority color
  const getPriorityColor = (priority: string): string => {
    switch (priority) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      case 'low': return 'blue';
      default: return 'gray';
    }
  };

  // Get health icon
  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-5 w-5 text-emerald-500" />;
      case 'attention': return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'warning': return <AlertTriangle className="h-5 w-5 text-orange-500" />;
      case 'critical': return <XCircle className="h-5 w-5 text-red-500" />;
      default: return <Activity className="h-5 w-5 text-gray-500" />;
    }
  };

  return (
    <div className="p-6 bg-gray-50 dark:bg-gray-900 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <Flex justifyContent="between" alignItems="center">
          <div>
            <Title className="text-2xl font-bold flex items-center gap-2">
              <Wrench className="h-7 w-7 text-blue-600" />
              Central de Manutenção (PCM)
            </Title>
            <Text className="text-gray-500">
              Gestão de ativos, indicadores e planejamento de manutenção
            </Text>
          </div>
          <Flex className="gap-3 items-center">
            <div className="min-w-[180px]">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="w-full px-4 py-2.5 text-sm font-medium border border-gray-300 rounded-lg bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 cursor-pointer appearance-none"
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236b7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
                  backgroundRepeat: 'no-repeat',
                  backgroundPosition: 'right 10px center',
                  backgroundSize: '18px',
                  paddingRight: '40px'
                }}
              >
                <option value="7d">Últimos 7 dias</option>
                <option value="30d">Últimos 30 dias</option>
                <option value="90d">Últimos 90 dias</option>
              </select>
            </div>
            <Button
              icon={RefreshCw}
              variant="secondary"
              onClick={fetchData}
              loading={loading}
            >
              Atualizar
            </Button>
            <Button icon={Download} variant="secondary">
              Exportar
            </Button>
          </Flex>
        </Flex>
      </div>

      {/* Main Tabs */}
      <TabGroup index={selectedTab} onIndexChange={handleTabChange}>
        <TabList className="mb-6">
          <Tab icon={Heart}>Saúde dos Ativos</Tab>
          <Tab icon={Gauge}>Indicadores KPI</Tab>
          <Tab icon={Calendar}>Backlog</Tab>
          <Tab icon={Target}>Análise de Falhas</Tab>
        </TabList>

        <TabPanels>
          {/* Tab 1: Asset Health */}
          <TabPanel>
            <Grid numItemsMd={2} numItemsLg={4} className="gap-4 mb-6">
              {/* Summary Cards */}
              <Card decoration="top" decorationColor="emerald">
                <Flex alignItems="center" justifyContent="start" className="gap-2">
                  <CheckCircle className="h-5 w-5 text-emerald-500" />
                  <Text>Saudáveis</Text>
                </Flex>
                <Metric>{equipmentHealth.filter(e => e.status === 'healthy').length}</Metric>
                <Text className="text-emerald-600">Operação normal</Text>
              </Card>

              <Card decoration="top" decorationColor="yellow">
                <Flex alignItems="center" justifyContent="start" className="gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  <Text>Atenção</Text>
                </Flex>
                <Metric>{equipmentHealth.filter(e => e.status === 'attention').length}</Metric>
                <Text className="text-yellow-600">Monitorar</Text>
              </Card>

              <Card decoration="top" decorationColor="orange">
                <Flex alignItems="center" justifyContent="start" className="gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-500" />
                  <Text>Alerta</Text>
                </Flex>
                <Metric>{equipmentHealth.filter(e => e.status === 'warning').length}</Metric>
                <Text className="text-orange-600">Ação necessária</Text>
              </Card>

              <Card decoration="top" decorationColor="red">
                <Flex alignItems="center" justifyContent="start" className="gap-2">
                  <XCircle className="h-5 w-5 text-red-500" />
                  <Text>Crítico</Text>
                </Flex>
                <Metric>{equipmentHealth.filter(e => e.status === 'critical').length}</Metric>
                <Text className="text-red-600">Ação imediata</Text>
              </Card>
            </Grid>

            {/* Equipment Health Grid */}
            <Card>
              <Title>Saúde dos Equipamentos</Title>
              <Grid numItemsMd={2} numItemsLg={4} className="gap-4 mt-4">
                {equipmentHealth.map((equipment) => (
                  <Card
                    key={equipment.equipment_id}
                    className="cursor-pointer hover:shadow-lg transition-shadow"
                    onClick={() => setSelectedEquipment(equipment.equipment_id)}
                  >
                    <Flex alignItems="center" justifyContent="between">
                      <Text className="font-semibold truncate">{equipment.equipment_name}</Text>
                      {getHealthIcon(equipment.status)}
                    </Flex>
                    <Metric className="mt-2">{equipment.health_score?.toFixed(1)}%</Metric>
                    <ProgressBar
                      value={equipment.health_score || 0}
                      color={getStatusColor(equipment.status)}
                      className="mt-2"
                    />
                    <Grid numItems={2} className="mt-3 gap-2">
                      <div>
                        <Text className="text-xs text-gray-500">MTBF</Text>
                        <Text className="font-medium">
                          {equipment.mtbf_hours ? `${equipment.mtbf_hours.toFixed(0)}h` : 'N/A'}
                        </Text>
                      </div>
                      <div>
                        <Text className="text-xs text-gray-500">Falhas</Text>
                        <Text className="font-medium">{equipment.failure_count}</Text>
                      </div>
                    </Grid>
                  </Card>
                ))}
              </Grid>
            </Card>

            {/* ML Predictions */}
            <Card className="mt-6">
              <Flex justifyContent="between" alignItems="center">
                <Title>Previsões ML (Próximos 7 dias)</Title>
                <Badge color="purple" icon={Zap}>AI Powered</Badge>
              </Flex>
              <Table className="mt-4">
                <TableHead>
                  <TableRow>
                    <TableHeaderCell>Equipamento</TableHeaderCell>
                    <TableHeaderCell>Probabilidade</TableHeaderCell>
                    <TableHeaderCell>Problema Previsto</TableHeaderCell>
                    <TableHeaderCell>Recomendação</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {mlPredictions.map((prediction, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{prediction.equipment_name}</TableCell>
                      <TableCell>
                        <Badge color={prediction.probability > 70 ? 'red' : prediction.probability > 50 ? 'orange' : 'yellow'}>
                          {prediction.probability}%
                        </Badge>
                      </TableCell>
                      <TableCell>{prediction.predicted_issue}</TableCell>
                      <TableCell className="text-sm text-gray-600">{prediction.recommendation}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          </TabPanel>

          {/* Tab 2: KPI Indicators */}
          <TabPanel>
            {/* Equipment Selector - Separate from grid for z-index */}
            <Card className="mb-6 relative z-50">
              <Flex justifyContent="between" alignItems="start" className="flex-wrap gap-4">
                <div>
                  <Title>Indicadores de Manutenção</Title>
                  <Text className="text-gray-500">Selecione um equipamento para visualizar os KPIs</Text>
                </div>
                <div className="min-w-[300px]">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Equipamento
                  </label>
                  <select
                    value={selectedEquipment || ''}
                    onChange={(e) => setSelectedEquipment(e.target.value || null)}
                    className="w-full px-4 py-3 text-base border border-gray-300 rounded-lg bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 cursor-pointer appearance-none"
                    style={{
                      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236b7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
                      backgroundRepeat: 'no-repeat',
                      backgroundPosition: 'right 12px center',
                      backgroundSize: '20px',
                      paddingRight: '44px'
                    }}
                  >
                    <option value="">-- Escolha um equipamento --</option>
                    {equipmentHealth.map((eq) => (
                      <option key={eq.equipment_id} value={eq.equipment_id}>
                        {eq.equipment_name} - {eq.availability_percent?.toFixed(0)}% disponível
                      </option>
                    ))}
                  </select>
                </div>
              </Flex>
            </Card>

            <Grid numItemsMd={2} className="gap-6">
              {selectedEquipment && kpis ? (
                <>
                  {/* KPI Cards */}
                  <Card decoration="top" decorationColor="blue">
                    <Flex alignItems="center" className="gap-2">
                      <Timer className="h-5 w-5 text-blue-600" />
                      <Text>MTBF (Tempo Médio Entre Falhas)</Text>
                    </Flex>
                    <Metric>{kpis.mtbf_hours?.toFixed(1) || 'N/A'} horas</Metric>
                    <Text className="text-gray-500 mt-2">
                      Meta: 720h (30 dias)
                    </Text>
                    <ProgressBar
                      value={Math.min(100, ((kpis.mtbf_hours || 0) / 720) * 100)}
                      color="blue"
                      className="mt-2"
                    />
                  </Card>

                  <Card decoration="top" decorationColor="amber">
                    <Flex alignItems="center" className="gap-2">
                      <Wrench className="h-5 w-5 text-amber-600" />
                      <Text>MTTR (Tempo Médio de Reparo)</Text>
                    </Flex>
                    <Metric>{kpis.mttr_hours?.toFixed(1) || 'N/A'} horas</Metric>
                    <Text className="text-gray-500 mt-2">
                      Meta: &lt; 4h
                    </Text>
                    <ProgressBar
                      value={Math.max(0, 100 - ((kpis.mttr_hours || 0) / 4) * 100)}
                      color="amber"
                      className="mt-2"
                    />
                  </Card>

                  <Card decoration="top" decorationColor="emerald">
                    <Flex alignItems="center" className="gap-2">
                      <Activity className="h-5 w-5 text-emerald-600" />
                      <Text>Disponibilidade</Text>
                    </Flex>
                    <Metric>{kpis.availability_percent?.toFixed(1) || 'N/A'}%</Metric>
                    <Text className="text-gray-500 mt-2">
                      Meta: &gt; 95%
                    </Text>
                    <ProgressBar
                      value={kpis.availability_percent || 0}
                      color="emerald"
                      className="mt-2"
                    />
                  </Card>

                  <Card decoration="top" decorationColor="violet">
                    <Flex alignItems="center" className="gap-2">
                      <Target className="h-5 w-5 text-violet-600" />
                      <Text>Confiabilidade (24h)</Text>
                    </Flex>
                    <Metric>{kpis.reliability_24h_percent?.toFixed(1) || 'N/A'}%</Metric>
                    <Text className="text-gray-500 mt-2">
                      Probabilidade de operar sem falha nas próximas 24h
                    </Text>
                    <ProgressBar
                      value={kpis.reliability_24h_percent || 0}
                      color="violet"
                      className="mt-2"
                    />
                  </Card>

                  {/* MTBF Trend Chart */}
                  <Card className="col-span-2">
                    <Title>Tendência MTBF (Últimos 6 meses)</Title>
                    <ProfessionalAreaChart
                      data={mtbfTrend.map(d => ({
                        date: d.month,
                        MTBF: d.mtbf_hours || 0
                      }))}
                      index="date"
                      categories={['MTBF']}
                      colors={['blue']}
                      valueFormatter={(v) => `${v.toFixed(0)}h`}
                      className="h-72 mt-4"
                    />
                  </Card>
                </>
              ) : (
                <Card className="col-span-2">
                  <Callout title="Selecione um equipamento" color="blue" icon={Settings}>
                    Escolha um equipamento acima para visualizar seus indicadores de manutenção.
                  </Callout>
                </Card>
              )}
            </Grid>
          </TabPanel>

          {/* Tab 3: Backlog */}
          <TabPanel>
            <Grid numItemsMd={3} className="gap-4 mb-6">
              <Card decoration="top" decorationColor="blue">
                <Flex alignItems="center" className="gap-2">
                  <Calendar className="h-5 w-5 text-blue-600" />
                  <Text>Preventivas Pendentes</Text>
                </Flex>
                <Metric>{workOrders.filter(wo => wo.type === 'preventive' && wo.status === 'pending').length}</Metric>
              </Card>

              <Card decoration="top" decorationColor="red">
                <Flex alignItems="center" className="gap-2">
                  <Wrench className="h-5 w-5 text-red-600" />
                  <Text>Corretivas Abertas</Text>
                </Flex>
                <Metric>{workOrders.filter(wo => wo.type === 'corrective' && wo.status !== 'completed').length}</Metric>
              </Card>

              <Card decoration="top" decorationColor="purple">
                <Flex alignItems="center" className="gap-2">
                  <Zap className="h-5 w-5 text-purple-600" />
                  <Text>Preditivas Agendadas</Text>
                </Flex>
                <Metric>{workOrders.filter(wo => wo.type === 'predictive').length}</Metric>
              </Card>
            </Grid>

            <Card>
              <Flex justifyContent="between" alignItems="center">
                <Title>Ordens de Serviço</Title>
                <Button icon={FileText} variant="secondary">
                  Nova OS
                </Button>
              </Flex>
              <Table className="mt-4">
                <TableHead>
                  <TableRow>
                    <TableHeaderCell>ID</TableHeaderCell>
                    <TableHeaderCell>Equipamento</TableHeaderCell>
                    <TableHeaderCell>Tipo</TableHeaderCell>
                    <TableHeaderCell>Prioridade</TableHeaderCell>
                    <TableHeaderCell>Descrição</TableHeaderCell>
                    <TableHeaderCell>Prazo</TableHeaderCell>
                    <TableHeaderCell>Status</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {workOrders.map((wo) => (
                    <TableRow key={wo.id}>
                      <TableCell className="font-mono">{wo.id}</TableCell>
                      <TableCell>{wo.equipment_id}</TableCell>
                      <TableCell>
                        <Badge color={wo.type === 'corrective' ? 'red' : wo.type === 'predictive' ? 'purple' : 'blue'}>
                          {wo.type}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge color={getPriorityColor(wo.priority)}>
                          {wo.priority}
                        </Badge>
                      </TableCell>
                      <TableCell>{wo.description}</TableCell>
                      <TableCell>{wo.due_date}</TableCell>
                      <TableCell>
                        <Badge color={wo.status === 'completed' ? 'emerald' : wo.status === 'in_progress' ? 'yellow' : 'gray'}>
                          {wo.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          </TabPanel>

          {/* Tab 4: Failure Analysis */}
          <TabPanel>
            <Grid numItemsMd={2} className="gap-6">
              {/* Pareto Chart */}
              <Card>
                <Title>Pareto de Falhas por Tipo</Title>
                <Text className="text-gray-500 mb-2">Horas de parada e ocorrências por tipo de falha</Text>
                <ProfessionalMultiBarChart
                  data={failureAnalysis.map(f => ({
                    tipo: f.failure_type.length > 12 ? f.failure_type.substring(0, 12) + '...' : f.failure_type,
                    'Horas': f.total_hours,
                    'Qtd': f.count
                  }))}
                  xAxisKey="tipo"
                  bars={[
                    { dataKey: 'Horas', name: 'Horas de Parada', color: '#dc2626' },
                    { dataKey: 'Qtd', name: 'Ocorrências', color: '#2563eb' }
                  ]}
                  height={280}
                  showGrid={true}
                  showLegend={true}
                />
              </Card>

              {/* Cost Distribution */}
              <Card>
                <Title>Distribuição de Custos</Title>
                <ProfessionalDonutChart
                  data={[
                    { name: 'Corretiva', value: 45 },
                    { name: 'Preventiva', value: 35 },
                    { name: 'Preditiva', value: 20 },
                  ]}
                  index="name"
                  category="value"
                  colors={['red', 'blue', 'purple']}
                  valueFormatter={(v) => `${v}%`}
                  className="h-72 mt-4"
                />
              </Card>

              {/* Failure Details Table */}
              <Card className="col-span-2">
                <Title>Detalhamento de Falhas</Title>
                <Table className="mt-4">
                  <TableHead>
                    <TableRow>
                      <TableHeaderCell>Tipo de Falha</TableHeaderCell>
                      <TableHeaderCell>Ocorrências</TableHeaderCell>
                      <TableHeaderCell>Tempo Total (h)</TableHeaderCell>
                      <TableHeaderCell>% do Total</TableHeaderCell>
                      <TableHeaderCell>Tendência</TableHeaderCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {failureAnalysis.map((failure, idx) => (
                      <TableRow key={idx}>
                        <TableCell className="font-medium">{failure.failure_type}</TableCell>
                        <TableCell>{failure.count}</TableCell>
                        <TableCell>{failure.total_hours.toFixed(1)}</TableCell>
                        <TableCell>
                          <Flex className="gap-2">
                            <ProgressBar
                              value={failure.percentage}
                              color="red"
                              className="w-20"
                            />
                            <Text>{failure.percentage.toFixed(1)}%</Text>
                          </Flex>
                        </TableCell>
                        <TableCell>
                          <BadgeDelta deltaType={idx % 2 === 0 ? 'decrease' : 'increase'}>
                            {idx % 2 === 0 ? '-12%' : '+5%'}
                          </BadgeDelta>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Card>
            </Grid>
          </TabPanel>
        </TabPanels>
      </TabGroup>
    </div>
  );
}

// Fallback data generators
function generateFallbackEquipment(): EquipmentHealth[] {
  return [
    { equipment_id: 'ELEV01', equipment_name: 'Elevador 01', health_score: 95, mtbf_hours: 720, mttr_hours: 2.5, availability_percent: 95, failure_count: 1, status: 'healthy' },
    { equipment_id: 'CORR01', equipment_name: 'Correia 01', health_score: 72, mtbf_hours: 480, mttr_hours: 4.0, availability_percent: 72, failure_count: 3, status: 'attention' },
    { equipment_id: 'CORR02', equipment_name: 'Correia 02', health_score: 98, mtbf_hours: 890, mttr_hours: 1.5, availability_percent: 98, failure_count: 0, status: 'healthy' },
    { equipment_id: 'SILO01', equipment_name: 'Silo 01', health_score: 85, mtbf_hours: 600, mttr_hours: 3.0, availability_percent: 85, failure_count: 2, status: 'healthy' },
    { equipment_id: 'PUMP01', equipment_name: 'Bomba 01', health_score: 55, mtbf_hours: 240, mttr_hours: 5.0, availability_percent: 55, failure_count: 5, status: 'warning' },
    { equipment_id: 'CRUSH01', equipment_name: 'Britador 01', health_score: 45, mtbf_hours: 168, mttr_hours: 6.0, availability_percent: 45, failure_count: 8, status: 'critical' },
  ];
}

function generateFallbackKPIs(): MaintenanceKPI {
  return {
    mtbf_hours: 520,
    mttr_hours: 3.2,
    availability_percent: 89.5,
    reliability_24h_percent: 95.5,
    total_downtime_hours: 42
  };
}

function generateFallbackTrend(): { month: string; mtbf_hours: number }[] {
  return [
    { month: '2024-07', mtbf_hours: 450 },
    { month: '2024-08', mtbf_hours: 480 },
    { month: '2024-09', mtbf_hours: 510 },
    { month: '2024-10', mtbf_hours: 495 },
    { month: '2024-11', mtbf_hours: 530 },
    { month: '2024-12', mtbf_hours: 520 },
  ];
}

function generateFallbackFailures(): FailureAnalysis[] {
  return [
    { failure_type: 'Mecânica', count: 12, total_hours: 48, percentage: 45 },
    { failure_type: 'Elétrica', count: 8, total_hours: 24, percentage: 22 },
    { failure_type: 'Instrumentação', count: 5, total_hours: 15, percentage: 14 },
    { failure_type: 'Processo', count: 4, total_hours: 12, percentage: 11 },
    { failure_type: 'Operacional', count: 3, total_hours: 8, percentage: 8 },
  ];
}

function generateSampleWorkOrders(): WorkOrder[] {
  return [
    { id: 'OS-2024-1234', equipment_id: 'ELEV01', type: 'preventive', priority: 'medium', description: 'Troca de rolamento', due_date: '15/12/2024', status: 'pending' },
    { id: 'OS-2024-1235', equipment_id: 'CORR02', type: 'preventive', priority: 'low', description: 'Lubrificação geral', due_date: '18/12/2024', status: 'pending' },
    { id: 'OS-2024-1236', equipment_id: 'PUMP01', type: 'corrective', priority: 'high', description: 'Reparo de vazamento', due_date: '10/12/2024', status: 'in_progress' },
    { id: 'OS-2024-1237', equipment_id: 'CRUSH01', type: 'predictive', priority: 'critical', description: 'Substituição preventiva - vibração alta', due_date: '08/12/2024', status: 'pending' },
    { id: 'OS-2024-1238', equipment_id: 'SILO01', type: 'preventive', priority: 'low', description: 'Inspeção de sensores', due_date: '20/12/2024', status: 'pending' },
  ];
}

function generateSamplePredictions(): MLPrediction[] {
  return [
    { equipment_id: 'CORR01', equipment_name: 'Correia 01', probability: 78, predicted_issue: 'Vibração alta - falha de rolamento', recommendation: 'Programar troca de rolamento nos próximos 3 dias' },
    { equipment_id: 'SILO02', equipment_name: 'Silo 02', probability: 65, predicted_issue: 'Sensor de nível degradando', recommendation: 'Calibrar ou substituir sensor' },
    { equipment_id: 'PUMP01', equipment_name: 'Bomba 01', probability: 52, predicted_issue: 'Aumento de temperatura', recommendation: 'Verificar sistema de resfriamento' },
  ];
}
