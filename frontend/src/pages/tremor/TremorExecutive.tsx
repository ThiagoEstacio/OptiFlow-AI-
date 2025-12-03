/**
 * 🎯 Executive Dashboard 360° with Tremor
 * =======================================
 *
 * Unified view of maintenance + operations with ROI Calculator and strategic insights.
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  Title,
  Text,
  Metric,
  Flex,
  Grid,
  Col,
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
  List,
  ListItem,
  Button,
  Select,
  SelectItem,
} from '@tremor/react';
import {
  ProfessionalAreaChart,
  ProfessionalDonutChart,
  ProfessionalLineChart,
} from '../../components/charts/ProfessionalCharts';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  DollarSign,
  Activity,
  Settings,
  Zap,
  Clock,
  Download,
  RefreshCw,
  Target,
  BarChart3,
  PieChart,
  Wrench,
  Shield,
} from 'lucide-react';
import { format } from 'date-fns';
import apiClient from '../../api/client';

// Mock data generator
const generateMockData = () => {
  return {
    overall_health_score: {
      score: 87,
      status: 'good',
      maintenance_component: 85,
      operations_component: 89,
    },
    maintenance: {
      mtbf_hours: 720,
      mttr_hours: 2.5,
      availability: 98.5,
      planned_maintenance_ratio: 0.85,
      pending_work_orders: 12,
      overdue_work_orders: 2,
    },
    operations: {
      oee: 87.3,
      availability: 95.2,
      performance: 92.1,
      quality: 99.5,
      production_target_achievement: 94.8,
      energy_efficiency: 0.92,
    },
    asset_health: [
      { name: 'Compressor Principal', health: 95, status: 'healthy', criticality: 'high' },
      { name: 'Bomba de Processo A', health: 88, status: 'healthy', criticality: 'high' },
      { name: 'Trocador de Calor', health: 72, status: 'warning', criticality: 'medium' },
      { name: 'Motor Elétrico #3', health: 65, status: 'warning', criticality: 'high' },
      { name: 'Esteira Transportadora', health: 45, status: 'critical', criticality: 'low' },
    ],
    critical_alerts: [
      { id: 1, severity: 'critical', message: 'Motor #3 - Vibração excessiva detectada', time: '10 min atrás' },
      { id: 2, severity: 'warning', message: 'Trocador de calor - Temperatura acima do normal', time: '25 min atrás' },
      { id: 3, severity: 'warning', message: 'Bomba A - Manutenção preventiva em 3 dias', time: '1h atrás' },
    ],
    roi_data: {
      total_savings: 285000,
      downtime_reduction_percent: 35,
      maintenance_cost_reduction: 42000,
      energy_savings: 18500,
      productivity_gain: 224500,
    },
    trends: Array.from({ length: 30 }, (_, i) => ({
      date: format(new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000), 'dd/MM'),
      oee: 82 + Math.random() * 10,
      availability: 93 + Math.random() * 5,
      mtbf: 680 + Math.random() * 80,
    })),
  };
};

export const TremorExecutive: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [periodDays, setPeriodDays] = useState('7');
  const [lastUpdated, setLastUpdated] = useState(new Date());

  useEffect(() => {
    // Simulate API call
    const fetchData = async () => {
      setLoading(true);
      try {
        // In production, this would be:
        // const response = await apiClient.get('/api/v1/executive/dashboard360');
        // setData(response.data);

        await new Promise(resolve => setTimeout(resolve, 500));
        setData(generateMockData());
        setLastUpdated(new Date());
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [periodDays]);

  const handleRefresh = () => {
    setData(generateMockData());
    setLastUpdated(new Date());
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const healthScore = data?.overall_health_score || {};
  const maintenance = data?.maintenance || {};
  const operations = data?.operations || {};
  const roiData = data?.roi_data || {};

  const healthColor = healthScore.score >= 80 ? 'emerald' : healthScore.score >= 60 ? 'amber' : 'red';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <Title>Executive Dashboard 360°</Title>
          <Text>Última atualização: {format(lastUpdated, 'dd/MM/yyyy HH:mm')}</Text>
        </div>
        <div className="flex items-center gap-3">
          <Select value={periodDays} onValueChange={setPeriodDays}>
            <SelectItem value="7">7 dias</SelectItem>
            <SelectItem value="30">30 dias</SelectItem>
            <SelectItem value="90">90 dias</SelectItem>
          </Select>
          <Button size="xs" variant="secondary" icon={RefreshCw} onClick={handleRefresh}>
            Atualizar
          </Button>
          <Button size="xs" variant="secondary" icon={Download}>
            Exportar PDF
          </Button>
        </div>
      </div>

      {/* Health Score Hero */}
      <Card decoration="top" decorationColor={healthColor} className="bg-gradient-to-r from-slate-50 to-white">
        <Flex justifyContent="between" alignItems="center">
          <div>
            <Text>Score Geral de Saúde</Text>
            <Metric className="text-5xl">{healthScore.score}%</Metric>
            <Badge color={healthColor} size="lg" className="mt-2">
              {healthScore.status === 'excellent' ? 'Excelente' :
               healthScore.status === 'good' ? 'Bom' :
               healthScore.status === 'warning' ? 'Atenção' : 'Crítico'}
            </Badge>
          </div>
          <div className="text-right space-y-2">
            <div>
              <Text>Manutenção</Text>
              <div className="flex items-center gap-2">
                <ProgressBar value={healthScore.maintenance_component} color="blue" className="w-32" />
                <Text className="font-medium">{healthScore.maintenance_component}%</Text>
              </div>
            </div>
            <div>
              <Text>Operações</Text>
              <div className="flex items-center gap-2">
                <ProgressBar value={healthScore.operations_component} color="emerald" className="w-32" />
                <Text className="font-medium">{healthScore.operations_component}%</Text>
              </div>
            </div>
          </div>
        </Flex>
      </Card>

      {/* Tabs */}
      <TabGroup>
        <TabList>
          <Tab icon={BarChart3}>Visão Geral</Tab>
          <Tab icon={DollarSign}>ROI & Financeiro</Tab>
          <Tab icon={Activity}>Operações</Tab>
          <Tab icon={Wrench}>Manutenção</Tab>
          <Tab icon={Target}>Insights</Tab>
        </TabList>

        <TabPanels>
          {/* Overview Tab */}
          <TabPanel>
            <div className="mt-6 space-y-6">
              {/* KPIs Row */}
              <Grid numItemsSm={2} numItemsLg={4} className="gap-6">
                <Card decoration="top" decorationColor="blue">
                  <Flex justifyContent="between" alignItems="center">
                    <div>
                      <Text>OEE Geral</Text>
                      <Metric>{operations.oee?.toFixed(1)}%</Metric>
                    </div>
                    <Activity className="w-10 h-10 text-blue-500" />
                  </Flex>
                  <Flex className="mt-4">
                    <Text>Meta: 85%</Text>
                    <BadgeDelta deltaType="increase">+2.3%</BadgeDelta>
                  </Flex>
                  <ProgressBar value={operations.oee} color="blue" className="mt-2" />
                </Card>

                <Card decoration="top" decorationColor="emerald">
                  <Flex justifyContent="between" alignItems="center">
                    <div>
                      <Text>Disponibilidade</Text>
                      <Metric>{maintenance.availability?.toFixed(1)}%</Metric>
                    </div>
                    <CheckCircle className="w-10 h-10 text-emerald-500" />
                  </Flex>
                  <Flex className="mt-4">
                    <Text>Meta: 98%</Text>
                    <BadgeDelta deltaType="increase">+0.5%</BadgeDelta>
                  </Flex>
                  <ProgressBar value={maintenance.availability} color="emerald" className="mt-2" />
                </Card>

                <Card decoration="top" decorationColor="amber">
                  <Flex justifyContent="between" alignItems="center">
                    <div>
                      <Text>MTBF</Text>
                      <Metric>{maintenance.mtbf_hours}h</Metric>
                    </div>
                    <Clock className="w-10 h-10 text-amber-500" />
                  </Flex>
                  <Flex className="mt-4">
                    <Text>MTTR: {maintenance.mttr_hours}h</Text>
                    <BadgeDelta deltaType="decrease">-15min</BadgeDelta>
                  </Flex>
                </Card>

                <Card decoration="top" decorationColor="violet">
                  <Flex justifyContent="between" alignItems="center">
                    <div>
                      <Text>Ordens Pendentes</Text>
                      <Metric>{maintenance.pending_work_orders}</Metric>
                    </div>
                    <Settings className="w-10 h-10 text-violet-500" />
                  </Flex>
                  <Flex className="mt-4">
                    <Text>Vencidas: {maintenance.overdue_work_orders}</Text>
                    <Badge color="red">{maintenance.overdue_work_orders}</Badge>
                  </Flex>
                </Card>
              </Grid>

              {/* Charts Row */}
              <Grid numItemsSm={1} numItemsLg={2} className="gap-6">
                {/* Trend Chart */}
                <Card>
                  <Title>Tendências - Últimos 30 dias</Title>
                  <div className="mt-4">
                    <ProfessionalLineChart
                      data={data?.trends || []}
                      xAxisKey="date"
                      lines={[
                        { dataKey: 'oee', name: 'OEE', color: '#3b82f6' },
                        { dataKey: 'availability', name: 'Disponibilidade', color: '#10b981' },
                      ]}
                      height={288}
                      showGrid={true}
                      showLegend={true}
                    />
                  </div>
                </Card>

                {/* Asset Health */}
                <Card>
                  <Title>Saúde dos Ativos Críticos</Title>
                  <div className="mt-4 space-y-4">
                    {data?.asset_health?.map((asset: any, index: number) => (
                      <div key={index}>
                        <Flex justifyContent="between" className="mb-1">
                          <div className="flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full ${
                              asset.status === 'healthy' ? 'bg-emerald-500' :
                              asset.status === 'warning' ? 'bg-amber-500' : 'bg-red-500'
                            }`} />
                            <Text>{asset.name}</Text>
                            <Badge size="xs" color={
                              asset.criticality === 'high' ? 'red' :
                              asset.criticality === 'medium' ? 'amber' : 'gray'
                            }>
                              {asset.criticality}
                            </Badge>
                          </div>
                          <Text className="font-medium">{asset.health}%</Text>
                        </Flex>
                        <ProgressBar
                          value={asset.health}
                          color={asset.status === 'healthy' ? 'emerald' :
                                 asset.status === 'warning' ? 'amber' : 'red'}
                        />
                      </div>
                    ))}
                  </div>
                </Card>
              </Grid>

              {/* Alerts */}
              <Card>
                <Title>Alertas Críticos</Title>
                <div className="mt-4 space-y-3">
                  {data?.critical_alerts?.map((alert: any) => (
                    <Callout
                      key={alert.id}
                      title={alert.message}
                      icon={alert.severity === 'critical' ? AlertTriangle : Shield}
                      color={alert.severity === 'critical' ? 'red' : 'amber'}
                    >
                      {alert.time}
                    </Callout>
                  ))}
                </div>
              </Card>
            </div>
          </TabPanel>

          {/* ROI Tab */}
          <TabPanel>
            <div className="mt-6 space-y-6">
              {/* ROI Summary */}
              <Card className="bg-gradient-to-r from-emerald-50 to-white">
                <Flex justifyContent="between" alignItems="center">
                  <div>
                    <Text>Economia Total no Período</Text>
                    <Metric className="text-emerald-600">
                      R$ {roiData.total_savings?.toLocaleString('pt-BR')}
                    </Metric>
                  </div>
                  <DollarSign className="w-16 h-16 text-emerald-500" />
                </Flex>
              </Card>

              <Grid numItemsSm={2} numItemsLg={4} className="gap-6">
                <Card>
                  <Text>Redução de Downtime</Text>
                  <Metric className="text-blue-600">{roiData.downtime_reduction_percent}%</Metric>
                  <Text className="mt-2 text-sm">vs período anterior</Text>
                </Card>
                <Card>
                  <Text>Economia em Manutenção</Text>
                  <Metric className="text-emerald-600">
                    R$ {roiData.maintenance_cost_reduction?.toLocaleString('pt-BR')}
                  </Metric>
                </Card>
                <Card>
                  <Text>Economia em Energia</Text>
                  <Metric className="text-amber-600">
                    R$ {roiData.energy_savings?.toLocaleString('pt-BR')}
                  </Metric>
                </Card>
                <Card>
                  <Text>Ganho de Produtividade</Text>
                  <Metric className="text-violet-600">
                    R$ {roiData.productivity_gain?.toLocaleString('pt-BR')}
                  </Metric>
                </Card>
              </Grid>

              {/* ROI Breakdown Chart */}
              <Card>
                <Title>Composição do ROI</Title>
                <div className="mt-6">
                  <ProfessionalDonutChart
                    data={[
                      { name: 'Produtividade', value: roiData.productivity_gain || 0 },
                      { name: 'Manutenção', value: roiData.maintenance_cost_reduction || 0 },
                      { name: 'Energia', value: roiData.energy_savings || 0 },
                    ]}
                    colors={['#8b5cf6', '#10b981', '#f59e0b']}
                    height={240}
                    showLegend={true}
                  />
                </div>
              </Card>
            </div>
          </TabPanel>

          {/* Operations Tab */}
          <TabPanel>
            <div className="mt-6 space-y-6">
              <Grid numItemsSm={2} numItemsLg={3} className="gap-6">
                <Card>
                  <Text>OEE</Text>
                  <Metric>{operations.oee?.toFixed(1)}%</Metric>
                  <ProgressBar value={operations.oee} color="blue" className="mt-4" />
                </Card>
                <Card>
                  <Text>Disponibilidade</Text>
                  <Metric>{operations.availability?.toFixed(1)}%</Metric>
                  <ProgressBar value={operations.availability} color="emerald" className="mt-4" />
                </Card>
                <Card>
                  <Text>Performance</Text>
                  <Metric>{operations.performance?.toFixed(1)}%</Metric>
                  <ProgressBar value={operations.performance} color="amber" className="mt-4" />
                </Card>
                <Card>
                  <Text>Qualidade</Text>
                  <Metric>{operations.quality?.toFixed(1)}%</Metric>
                  <ProgressBar value={operations.quality} color="violet" className="mt-4" />
                </Card>
                <Card>
                  <Text>Atingimento de Meta</Text>
                  <Metric>{operations.production_target_achievement?.toFixed(1)}%</Metric>
                  <ProgressBar value={operations.production_target_achievement} color="blue" className="mt-4" />
                </Card>
                <Card>
                  <Text>Eficiência Energética</Text>
                  <Metric>{(operations.energy_efficiency * 100)?.toFixed(1)}%</Metric>
                  <ProgressBar value={operations.energy_efficiency * 100} color="emerald" className="mt-4" />
                </Card>
              </Grid>

              <Card>
                <Title>Evolução OEE</Title>
                <div className="mt-4">
                  <ProfessionalLineChart
                    data={data?.trends || []}
                    xAxisKey="date"
                    lines={[
                      { dataKey: 'oee', name: 'OEE', color: '#3b82f6' },
                    ]}
                    height={288}
                    showGrid={true}
                    showLegend={false}
                  />
                </div>
              </Card>
            </div>
          </TabPanel>

          {/* Maintenance Tab */}
          <TabPanel>
            <div className="mt-6 space-y-6">
              <Grid numItemsSm={2} numItemsLg={4} className="gap-6">
                <Card>
                  <Text>MTBF</Text>
                  <Metric>{maintenance.mtbf_hours}h</Metric>
                  <Text className="mt-2 text-sm text-gray-500">Tempo médio entre falhas</Text>
                </Card>
                <Card>
                  <Text>MTTR</Text>
                  <Metric>{maintenance.mttr_hours}h</Metric>
                  <Text className="mt-2 text-sm text-gray-500">Tempo médio de reparo</Text>
                </Card>
                <Card>
                  <Text>Disponibilidade</Text>
                  <Metric>{maintenance.availability}%</Metric>
                  <ProgressBar value={maintenance.availability} color="emerald" className="mt-4" />
                </Card>
                <Card>
                  <Text>Manutenção Planejada</Text>
                  <Metric>{(maintenance.planned_maintenance_ratio * 100).toFixed(0)}%</Metric>
                  <ProgressBar value={maintenance.planned_maintenance_ratio * 100} color="blue" className="mt-4" />
                </Card>
              </Grid>

              <Card>
                <Title>Ordens de Serviço</Title>
                <Table className="mt-4">
                  <TableHead>
                    <TableRow>
                      <TableHeaderCell>Status</TableHeaderCell>
                      <TableHeaderCell>Quantidade</TableHeaderCell>
                      <TableHeaderCell>Prioridade</TableHeaderCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell>Pendentes</TableCell>
                      <TableCell>{maintenance.pending_work_orders}</TableCell>
                      <TableCell><Badge color="amber">Média</Badge></TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Vencidas</TableCell>
                      <TableCell>{maintenance.overdue_work_orders}</TableCell>
                      <TableCell><Badge color="red">Alta</Badge></TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </Card>
            </div>
          </TabPanel>

          {/* Insights Tab */}
          <TabPanel>
            <div className="mt-6 space-y-6">
              <Grid numItemsSm={1} numItemsLg={2} className="gap-6">
                <Card>
                  <Title>Oportunidades de Melhoria</Title>
                  <List className="mt-4">
                    <ListItem>
                      <Flex justifyContent="between">
                        <Text>Otimização de manutenção preventiva</Text>
                        <Badge color="emerald">R$ 15.000/mês</Badge>
                      </Flex>
                    </ListItem>
                    <ListItem>
                      <Flex justifyContent="between">
                        <Text>Redução de consumo energético</Text>
                        <Badge color="emerald">R$ 8.500/mês</Badge>
                      </Flex>
                    </ListItem>
                    <ListItem>
                      <Flex justifyContent="between">
                        <Text>Aumento de OEE em 3%</Text>
                        <Badge color="emerald">R$ 45.000/mês</Badge>
                      </Flex>
                    </ListItem>
                  </List>
                </Card>

                <Card>
                  <Title>Riscos Identificados</Title>
                  <List className="mt-4">
                    <ListItem>
                      <Flex justifyContent="between">
                        <Text>Motor #3 - Falha iminente</Text>
                        <Badge color="red">Crítico</Badge>
                      </Flex>
                    </ListItem>
                    <ListItem>
                      <Flex justifyContent="between">
                        <Text>Esteira - Desgaste avançado</Text>
                        <Badge color="amber">Médio</Badge>
                      </Flex>
                    </ListItem>
                    <ListItem>
                      <Flex justifyContent="between">
                        <Text>Trocador de calor - Eficiência reduzida</Text>
                        <Badge color="amber">Médio</Badge>
                      </Flex>
                    </ListItem>
                  </List>
                </Card>
              </Grid>

              <Callout title="Recomendação Principal" icon={Target} color="blue">
                Priorizar manutenção do Motor #3 nas próximas 48h para evitar parada não programada.
                Economia estimada: R$ 25.000 em custos de emergência.
              </Callout>
            </div>
          </TabPanel>
        </TabPanels>
      </TabGroup>
    </div>
  );
};

export default TremorExecutive;
