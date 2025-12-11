/**
 * Central de Manutenção Preditiva - MELH-005
 * ===========================================
 *
 * Dashboard de Manutenção com 3 tabs:
 * - Saúde dos Ativos (visão geral de equipamentos)
 * - Indicadores KPI (MTBF/MTTR/Disponibilidade)
 * - Manutenção Preditiva (ML: detecção de anomalias)
 */
import { useState, useEffect, useCallback, useRef } from 'react';
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
} from '../../components/charts/ProfessionalCharts';
import {
  Wrench,
  Activity,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Download,
  Target,
  Gauge,
  Heart,
  Zap,
  Timer,
  XCircle,
  Brain,
  Thermometer,
  Waves,
  BatteryCharging,
  Cpu,
  PlayCircle,
  Clock,
} from 'lucide-react';
import apiClient from '../../api/client';

// Tab routing mapping
const TAB_ROUTES: Record<string, number> = {
  '/maintenance': 0,
  '/maintenance/pcm': 0,
  '/maintenance/kpis': 1,
  '/maintenance/predictive': 2,
};

const ROUTE_BY_TAB: Record<number, string> = {
  0: '/maintenance',
  1: '/maintenance/kpis',
  2: '/maintenance/predictive',
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

interface AnomalyPrediction {
  equipment_id: string;
  status: 'normal' | 'anomaly' | 'no_model' | 'error' | 'no_data';
  message?: string;
  score?: number;
  confidence?: number;
  is_anomaly?: boolean;
  contributing_features?: {
    feature: string;
    current_value: number;
    expected_mean: number;
    z_score: number;
    deviation: 'high' | 'low';
    severity: 'high' | 'medium';
  }[];
  recommendation?: string;
  timestamp?: string;
}

interface ModelStatus {
  available: boolean;
  total_models: number;
  models: Record<string, { trained_at: string; samples_used: number }>;
  statistics: {
    total_predictions: number;
    anomalies_detected: number;
    models_trained: number;
  };
}

// Component
export default function TremorMaintenance() {
  const location = useLocation();
  const navigate = useNavigate();

  const getInitialTab = () => {
    const path = location.pathname;
    return TAB_ROUTES[path] ?? 0;
  };

  // State
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState(getInitialTab);
  const [timeRange, setTimeRange] = useState('30d');
  const [equipmentHealth, setEquipmentHealth] = useState<EquipmentHealth[]>([]);
  const [selectedEquipment, setSelectedEquipment] = useState<string | null>(null);
  const [kpis, setKpis] = useState<MaintenanceKPI | null>(null);
  const [mtbfTrend, setMtbfTrend] = useState<{ month: string; mtbf_hours: number }[]>([]);

  // Predictive Maintenance State
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [anomalyPredictions, setAnomalyPredictions] = useState<Record<string, AnomalyPrediction>>({});
  const [predictiveLoading, setPredictiveLoading] = useState(false);
  const [trainingEquipment, setTrainingEquipment] = useState<string | null>(null);

  // Auto-prediction State
  const [autoRefreshInterval, setAutoRefreshInterval] = useState<number>(6); // hours
  const [lastPredictionTime, setLastPredictionTime] = useState<Date | null>(null);
  const [nextPredictionTime, setNextPredictionTime] = useState<Date | null>(null);
  const [isAutoRefreshEnabled, setIsAutoRefreshEnabled] = useState(true);
  const hasRunInitialPrediction = useRef(false);

  // Update tab when URL changes
  useEffect(() => {
    const newTab = TAB_ROUTES[location.pathname];
    if (newTab !== undefined && newTab !== selectedTab) {
      setSelectedTab(newTab);
    }
  }, [location.pathname, selectedTab]);

  // Handle tab change
  const handleTabChange = (index: number) => {
    setSelectedTab(index);
    const newRoute = ROUTE_BY_TAB[index];
    if (newRoute && newRoute !== location.pathname) {
      navigate(newRoute, { replace: true });
    }
  };

  // Fetch main data
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
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
    } catch (error) {
      console.error('Error fetching maintenance data:', error);
      setEquipmentHealth(generateFallbackEquipment());
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

        const trendResponse = await apiClient.get(`/api/v1/maintenance/mtbf/trend/${equipmentId}`, {
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

  // Fetch ML model status
  const fetchModelStatus = async () => {
    try {
      const response = await apiClient.get('/api/v1/ml/anomaly/status');
      setModelStatus(response.data);
    } catch (error) {
      console.error('Error fetching model status:', error);
      setModelStatus({
        available: true,
        total_models: 0,
        models: {},
        statistics: { total_predictions: 0, anomalies_detected: 0, models_trained: 0 }
      });
    }
  };

  // Train anomaly model for equipment
  const trainModel = async (equipmentId: string) => {
    setTrainingEquipment(equipmentId);
    try {
      const response = await apiClient.post(`/api/v1/ml/anomaly/train/${equipmentId}`, null, {
        params: { days: 30, contamination: 0.05 }
      });

      if (response.data.status === 'success') {
        await fetchModelStatus();
        await runPrediction(equipmentId);
      }
    } catch (error) {
      console.error('Error training model:', error);
    } finally {
      setTrainingEquipment(null);
    }
  };

  // Run anomaly prediction
  const runPrediction = async (equipmentId: string) => {
    try {
      const response = await apiClient.get(`/api/v1/ml/anomaly/predict/${equipmentId}`, {
        params: { use_live: true }
      });

      setAnomalyPredictions(prev => ({
        ...prev,
        [equipmentId]: response.data
      }));
    } catch (error) {
      console.error('Error running prediction:', error);
    }
  };

  // Refs to track state across effects without causing re-renders
  const equipmentHealthRef = useRef<EquipmentHealth[]>([]);
  const modelStatusRef = useRef<ModelStatus | null>(null);
  const autoRefreshIntervalRef = useRef(autoRefreshInterval);

  // Keep refs in sync with state
  useEffect(() => {
    equipmentHealthRef.current = equipmentHealth;
  }, [equipmentHealth]);

  useEffect(() => {
    modelStatusRef.current = modelStatus;
  }, [modelStatus]);

  useEffect(() => {
    autoRefreshIntervalRef.current = autoRefreshInterval;
  }, [autoRefreshInterval]);

  // Run predictions for all equipment with models (using refs to avoid dependency issues)
  const runAllPredictions = useCallback(async () => {
    const currentEquipment = equipmentHealthRef.current;
    const currentModelStatus = modelStatusRef.current;

    if (!currentEquipment.length || !currentModelStatus?.models) {
      console.log('[Auto-Prediction] No equipment or models available');
      return;
    }

    setPredictiveLoading(true);
    console.log('[Auto-Prediction] Starting predictions for', currentEquipment.length, 'equipment');

    try {
      for (const eq of currentEquipment) {
        if (currentModelStatus.models[eq.equipment_id]) {
          console.log('[Auto-Prediction] Running prediction for:', eq.equipment_id);
          await runPrediction(eq.equipment_id);
        }
      }
      // Update timestamps after successful run
      const now = new Date();
      setLastPredictionTime(now);
      const next = new Date(now.getTime() + autoRefreshIntervalRef.current * 60 * 60 * 1000);
      setNextPredictionTime(next);
      console.log('[Auto-Prediction] Completed successfully');
    } catch (error) {
      console.error('[Auto-Prediction] Error:', error);
    } finally {
      setPredictiveLoading(false);
    }
  }, []); // No dependencies - uses refs

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (selectedEquipment) {
      fetchEquipmentKPIs(selectedEquipment);
    }
  }, [selectedEquipment]);

  // Always load model status on mount (not just when tab is selected)
  useEffect(() => {
    fetchModelStatus();
  }, []);

  // Also refresh model status when tab is selected
  useEffect(() => {
    if (selectedTab === 2) {
      fetchModelStatus();
    }
  }, [selectedTab]);

  // Auto-run predictions when models and equipment are available
  useEffect(() => {
    if (modelStatus?.total_models && modelStatus.total_models > 0 && equipmentHealth.length > 0) {
      // Run predictions automatically on first load (only once)
      if (!hasRunInitialPrediction.current && !predictiveLoading) {
        hasRunInitialPrediction.current = true;
        console.log('[Auto-Prediction] Running initial predictions on page load...');
        // Small delay to ensure refs are updated
        setTimeout(() => {
          runAllPredictions();
        }, 100);
      }
    }
  }, [modelStatus, equipmentHealth.length, predictiveLoading, runAllPredictions]);

  // Auto-refresh predictions at configured interval
  useEffect(() => {
    if (!isAutoRefreshEnabled || selectedTab !== 2) return;

    const intervalMs = autoRefreshInterval * 60 * 60 * 1000; // Convert hours to ms

    const interval = setInterval(() => {
      if (modelStatus?.total_models && modelStatus.total_models > 0 && equipmentHealth.length > 0) {
        console.log(`[Auto-Prediction] Running scheduled predictions (interval: ${autoRefreshInterval}h)`);
        runAllPredictions();
      }
    }, intervalMs);

    // Set initial next prediction time
    if (!nextPredictionTime) {
      setNextPredictionTime(new Date(Date.now() + intervalMs));
    }

    return () => clearInterval(interval);
  }, [isAutoRefreshEnabled, autoRefreshInterval, selectedTab, modelStatus, equipmentHealth.length]);

  // Update countdown timer every minute
  useEffect(() => {
    if (!isAutoRefreshEnabled || !nextPredictionTime) return;

    const timer = setInterval(() => {
      // Force re-render to update countdown display
      setNextPredictionTime(prev => prev ? new Date(prev.getTime()) : null);
    }, 60000); // Update every minute

    return () => clearInterval(timer);
  }, [isAutoRefreshEnabled, nextPredictionTime]);

  // Helper functions
  const getStatusColor = (status: string): "emerald" | "yellow" | "orange" | "red" | "gray" => {
    switch (status) {
      case 'healthy': return 'emerald';
      case 'attention': return 'yellow';
      case 'warning': return 'orange';
      case 'critical': return 'red';
      default: return 'gray';
    }
  };

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-5 w-5 text-emerald-500" />;
      case 'attention': return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'warning': return <AlertTriangle className="h-5 w-5 text-orange-500" />;
      case 'critical': return <XCircle className="h-5 w-5 text-red-500" />;
      default: return <Activity className="h-5 w-5 text-gray-500" />;
    }
  };

  const getFeatureIcon = (feature: string) => {
    switch (feature) {
      case 'vibration_mms': return <Waves className="h-4 w-4" />;
      case 'temperature_c': return <Thermometer className="h-4 w-4" />;
      case 'current_a': return <BatteryCharging className="h-4 w-4" />;
      case 'power_kw': return <Zap className="h-4 w-4" />;
      case 'load_pct': return <Cpu className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  const getFeatureName = (feature: string) => {
    const names: Record<string, string> = {
      vibration_mms: 'Vibração (mm/s)',
      temperature_c: 'Temperatura (°C)',
      current_a: 'Corrente (A)',
      power_kw: 'Potência (kW)',
      load_pct: 'Carga (%)',
    };
    return names[feature] || feature;
  };

  return (
    <div className="p-6 bg-gray-50 dark:bg-gray-900 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <Flex justifyContent="between" alignItems="center">
          <div>
            <Title className="text-2xl font-bold flex items-center gap-2">
              <Wrench className="h-7 w-7 text-blue-600" />
              Central de Manutenção Preditiva
            </Title>
            <Text className="text-gray-500">
              Gestão de ativos, indicadores e manutenção preditiva com ML
            </Text>
          </div>
          <Flex className="gap-3 items-center">
            <div className="min-w-[180px]">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="w-full px-4 py-2.5 text-sm font-medium border border-gray-300 rounded-lg bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="7d">Últimos 7 dias</option>
                <option value="30d">Últimos 30 dias</option>
                <option value="90d">Últimos 90 dias</option>
              </select>
            </div>
            <Button icon={RefreshCw} variant="secondary" onClick={fetchData} loading={loading}>
              Atualizar
            </Button>
            <Button icon={Download} variant="secondary">Exportar</Button>
          </Flex>
        </Flex>
      </div>

      {/* Main Tabs */}
      <TabGroup index={selectedTab} onIndexChange={handleTabChange}>
        <TabList className="mb-6">
          <Tab icon={Heart}>Saúde dos Ativos</Tab>
          <Tab icon={Gauge}>Indicadores KPI</Tab>
          <Tab icon={Brain}>Manutenção Preditiva</Tab>
        </TabList>

        <TabPanels>
          {/* Tab 1: Asset Health */}
          <TabPanel>
            <Grid numItemsMd={2} numItemsLg={4} className="gap-4 mb-6">
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

            {/* Link to Predictive */}
            <Card className="mt-6" decoration="left" decorationColor="purple">
              <Flex justifyContent="between" alignItems="center">
                <Flex alignItems="center" className="gap-3">
                  <Brain className="h-6 w-6 text-purple-600" />
                  <div>
                    <Title>Manutenção Preditiva (ML)</Title>
                    <Text className="text-gray-500">Detecção de anomalias e previsão de falhas</Text>
                  </div>
                </Flex>
                <Button variant="secondary" onClick={() => handleTabChange(2)}>
                  Ver Previsões
                </Button>
              </Flex>
            </Card>
          </TabPanel>

          {/* Tab 2: KPI Indicators */}
          <TabPanel>
            <Card className="mb-6">
              <Flex justifyContent="between" alignItems="start" className="flex-wrap gap-4">
                <div>
                  <Title>Indicadores de Manutenção</Title>
                  <Text className="text-gray-500">Selecione um equipamento para visualizar os KPIs</Text>
                </div>
                <div className="min-w-[300px]">
                  <select
                    value={selectedEquipment || ''}
                    onChange={(e) => setSelectedEquipment(e.target.value || null)}
                    className="w-full px-4 py-3 text-base border border-gray-300 rounded-lg bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                  <Card decoration="top" decorationColor="blue">
                    <Flex alignItems="center" className="gap-2">
                      <Timer className="h-5 w-5 text-blue-600" />
                      <Text>MTBF (Tempo Médio Entre Falhas)</Text>
                    </Flex>
                    <Metric>{kpis.mtbf_hours?.toFixed(1) || 'N/A'} horas</Metric>
                    <Text className="text-gray-500 mt-2">Meta: 720h (30 dias)</Text>
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
                    <Text className="text-gray-500 mt-2">Meta: &lt; 4h</Text>
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
                    <Text className="text-gray-500 mt-2">Meta: &gt; 95%</Text>
                    <ProgressBar value={kpis.availability_percent || 0} color="emerald" className="mt-2" />
                  </Card>

                  <Card decoration="top" decorationColor="violet">
                    <Flex alignItems="center" className="gap-2">
                      <Target className="h-5 w-5 text-violet-600" />
                      <Text>Confiabilidade (24h)</Text>
                    </Flex>
                    <Metric>{kpis.reliability_24h_percent?.toFixed(1) || 'N/A'}%</Metric>
                    <Text className="text-gray-500 mt-2">Probabilidade de operar sem falha nas próximas 24h</Text>
                    <ProgressBar value={kpis.reliability_24h_percent || 0} color="violet" className="mt-2" />
                  </Card>

                  <Card className="col-span-2">
                    <Title>Tendência MTBF (Últimos 6 meses)</Title>
                    <ProfessionalAreaChart
                      data={mtbfTrend.map(d => ({ date: d.month, value: d.mtbf_hours || 0 }))}
                      xAxisKey="date"
                      dataKey="value"
                      color="#0077BB"
                      height={288}
                    />
                  </Card>
                </>
              ) : (
                <>
                  <Card decoration="top" decorationColor="blue" className="col-span-2">
                    <Title className="mb-4">Visão Geral - Todos os Equipamentos</Title>
                    <Grid numItemsMd={4} className="gap-4">
                      <div className="text-center p-4 bg-blue-50 rounded-lg">
                        <Text className="text-blue-600 font-medium">MTBF Médio</Text>
                        <Metric className="text-blue-700">
                          {equipmentHealth.length > 0
                            ? (equipmentHealth.reduce((sum, eq) => sum + (eq.mtbf_hours || 0), 0) / equipmentHealth.length).toFixed(0)
                            : 'N/A'} h
                        </Metric>
                      </div>
                      <div className="text-center p-4 bg-amber-50 rounded-lg">
                        <Text className="text-amber-600 font-medium">MTTR Médio</Text>
                        <Metric className="text-amber-700">
                          {equipmentHealth.length > 0
                            ? (equipmentHealth.reduce((sum, eq) => sum + (eq.mttr_hours || 0), 0) / equipmentHealth.length).toFixed(1)
                            : 'N/A'} h
                        </Metric>
                      </div>
                      <div className="text-center p-4 bg-emerald-50 rounded-lg">
                        <Text className="text-emerald-600 font-medium">Disponibilidade Média</Text>
                        <Metric className="text-emerald-700">
                          {equipmentHealth.length > 0
                            ? (equipmentHealth.reduce((sum, eq) => sum + (eq.availability_percent || 0), 0) / equipmentHealth.length).toFixed(1)
                            : 'N/A'}%
                        </Metric>
                      </div>
                      <div className="text-center p-4 bg-violet-50 rounded-lg">
                        <Text className="text-violet-600 font-medium">Score Saúde Médio</Text>
                        <Metric className="text-violet-700">
                          {equipmentHealth.length > 0
                            ? (equipmentHealth.reduce((sum, eq) => sum + (eq.health_score || 0), 0) / equipmentHealth.length).toFixed(0)
                            : 'N/A'}%
                        </Metric>
                      </div>
                    </Grid>
                  </Card>

                  <Card className="col-span-2">
                    <Title>KPIs por Equipamento</Title>
                    <Text className="text-gray-500 mb-4">Selecione um equipamento no dropdown acima</Text>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableHeaderCell>Equipamento</TableHeaderCell>
                          <TableHeaderCell className="text-right">MTBF (h)</TableHeaderCell>
                          <TableHeaderCell className="text-right">MTTR (h)</TableHeaderCell>
                          <TableHeaderCell className="text-right">Disponibilidade</TableHeaderCell>
                          <TableHeaderCell>Status</TableHeaderCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {equipmentHealth.map((eq) => (
                          <TableRow
                            key={eq.equipment_id}
                            className="cursor-pointer hover:bg-gray-50"
                            onClick={() => setSelectedEquipment(eq.equipment_id)}
                          >
                            <TableCell className="font-medium">{eq.equipment_name}</TableCell>
                            <TableCell className="text-right">{eq.mtbf_hours?.toFixed(0) || 'N/A'}</TableCell>
                            <TableCell className="text-right">{eq.mttr_hours?.toFixed(1) || 'N/A'}</TableCell>
                            <TableCell className="text-right">{eq.availability_percent?.toFixed(1) || 'N/A'}%</TableCell>
                            <TableCell>
                              <Badge color={getStatusColor(eq.status)}>
                                {eq.status === 'healthy' ? 'Saudável' :
                                 eq.status === 'attention' ? 'Atenção' :
                                 eq.status === 'warning' ? 'Alerta' : 'Crítico'}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </Card>
                </>
              )}
            </Grid>
          </TabPanel>

          {/* Tab 3: Predictive Maintenance (ML) */}
          <TabPanel>
            {/* ML Status Header */}
            <Grid numItemsMd={4} className="gap-4 mb-6">
              <Card decoration="top" decorationColor="purple">
                <Flex alignItems="center" className="gap-2">
                  <Brain className="h-5 w-5 text-purple-600" />
                  <Text>Modelos Treinados</Text>
                </Flex>
                <Metric>{modelStatus?.total_models || 0}</Metric>
                <Text className="text-gray-500">Isolation Forest</Text>
              </Card>

              <Card decoration="top" decorationColor="blue">
                <Flex alignItems="center" className="gap-2">
                  <Activity className="h-5 w-5 text-blue-600" />
                  <Text>Predições Realizadas</Text>
                </Flex>
                <Metric>{modelStatus?.statistics?.total_predictions || 0}</Metric>
              </Card>

              <Card decoration="top" decorationColor="red">
                <Flex alignItems="center" className="gap-2">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                  <Text>Anomalias Detectadas</Text>
                </Flex>
                <Metric>{modelStatus?.statistics?.anomalies_detected || 0}</Metric>
              </Card>

              <Card decoration="top" decorationColor="emerald">
                <Flex alignItems="center" className="gap-2">
                  <CheckCircle className="h-5 w-5 text-emerald-600" />
                  <Text>Taxa de Detecção</Text>
                </Flex>
                <Metric>
                  {modelStatus?.statistics?.total_predictions
                    ? ((modelStatus.statistics.anomalies_detected / modelStatus.statistics.total_predictions) * 100).toFixed(1)
                    : 0}%
                </Metric>
              </Card>
            </Grid>

            {/* Actions & Auto-Refresh Controls */}
            <Card className="mb-6">
              <Flex justifyContent="between" alignItems="start" className="flex-wrap gap-4">
                <div>
                  <Title>Detecção de Anomalias por Equipamento</Title>
                  <Text className="text-gray-500">
                    Algoritmo: Isolation Forest | Features: Vibração, Temperatura, Corrente, Potência, Carga
                  </Text>
                </div>

                <div className="flex flex-col gap-3">
                  {/* Auto-Refresh Controls */}
                  <Flex alignItems="center" className="gap-3">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={isAutoRefreshEnabled}
                        onChange={(e) => setIsAutoRefreshEnabled(e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <Text className="text-sm">Auto-refresh</Text>
                    </label>

                    <select
                      value={autoRefreshInterval}
                      onChange={(e) => setAutoRefreshInterval(Number(e.target.value))}
                      disabled={!isAutoRefreshEnabled}
                      className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
                    >
                      <option value={1}>1 hora</option>
                      <option value={6}>6 horas</option>
                      <option value={12}>12 horas</option>
                      <option value={24}>24 horas</option>
                    </select>
                  </Flex>

                  {/* Status Info */}
                  {isAutoRefreshEnabled && (
                    <div className="text-xs text-gray-500 space-y-1">
                      {lastPredictionTime && (
                        <div className="flex items-center gap-1">
                          <CheckCircle className="w-3 h-3 text-emerald-500" />
                          <span>Última: {lastPredictionTime.toLocaleString('pt-BR')}</span>
                        </div>
                      )}
                      {nextPredictionTime && (
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-blue-500" />
                          <span>Próxima: {nextPredictionTime.toLocaleString('pt-BR')}</span>
                        </div>
                      )}
                    </div>
                  )}

                  <Button
                    icon={PlayCircle}
                    onClick={runAllPredictions}
                    loading={predictiveLoading}
                    disabled={!modelStatus?.total_models}
                    size="sm"
                  >
                    Executar Agora
                  </Button>
                </div>
              </Flex>
            </Card>

            {/* Equipment Predictions */}
            <Grid numItemsMd={2} className="gap-4">
              {equipmentHealth.map((eq) => {
                const hasModel = modelStatus?.models?.[eq.equipment_id];
                const prediction = anomalyPredictions?.[eq.equipment_id];
                const isTraining = trainingEquipment === eq.equipment_id;
                const isLoadingPrediction = predictiveLoading && hasModel && !prediction;

                return (
                  <Card
                    key={eq.equipment_id}
                    className={`relative ${prediction?.is_anomaly ? 'border-l-4 border-red-500' : hasModel && prediction ? 'border-l-4 border-emerald-500' : ''}`}
                  >
                    {/* Header com Status da Predição */}
                    <Flex justifyContent="between" alignItems="start">
                      <div>
                        <Title className="flex items-center gap-2">
                          {prediction?.is_anomaly ? (
                            <AlertTriangle className="h-5 w-5 text-red-500" />
                          ) : hasModel && prediction ? (
                            <CheckCircle className="h-5 w-5 text-emerald-500" />
                          ) : (
                            getHealthIcon(eq.status)
                          )}
                          {eq.equipment_name}
                        </Title>
                        <Text className="text-gray-500">{eq.equipment_id}</Text>
                      </div>

                      {/* Badge de Status Principal */}
                      {prediction?.is_anomaly ? (
                        <Badge color="red" icon={AlertTriangle} size="lg">ANOMALIA</Badge>
                      ) : hasModel && prediction && prediction.status !== 'no_data' ? (
                        <Badge color="emerald" icon={CheckCircle} size="lg">NORMAL</Badge>
                      ) : hasModel ? (
                        <Badge color="blue" icon={Brain}>ML Ativo</Badge>
                      ) : (
                        <Badge color="gray">Sem Modelo</Badge>
                      )}
                    </Flex>

                    {/* Loading State */}
                    {isLoadingPrediction && (
                      <div className="mt-4 p-4 bg-blue-50 rounded-lg animate-pulse">
                        <Flex alignItems="center" className="gap-2">
                          <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />
                          <Text className="text-blue-700">Executando análise preditiva...</Text>
                        </Flex>
                      </div>
                    )}

                    {/* Model Training */}
                    {!hasModel && (
                      <Callout
                        className="mt-4"
                        title="Modelo não treinado"
                        icon={Brain}
                        color="yellow"
                      >
                        <Text>Treine o modelo com dados históricos para habilitar predições.</Text>
                        <Button
                          size="xs"
                          className="mt-2"
                          onClick={() => trainModel(eq.equipment_id)}
                          loading={isTraining}
                        >
                          Treinar Modelo (30 dias)
                        </Button>
                      </Callout>
                    )}

                    {/* Prediction Results - Exibição Direta */}
                    {hasModel && prediction && (
                      <div className="mt-4">
                        {/* No Data State */}
                        {prediction.status === 'no_data' ? (
                          <Callout color="amber" title="Sem Dados Live">
                            <Text>{prediction.message || 'Nenhum dado em tempo real disponível.'}</Text>
                          </Callout>
                        ) : (
                          <>
                            {/* Métricas em Destaque */}
                            <Grid numItems={2} className="gap-3 mb-4">
                              <div className={`p-3 rounded-lg ${prediction.is_anomaly ? 'bg-red-50' : 'bg-emerald-50'}`}>
                                <Text className="text-xs text-gray-500">Score de Anomalia</Text>
                                <Metric className={`text-lg ${prediction.is_anomaly ? 'text-red-600' : 'text-emerald-600'}`}>
                                  {prediction.score?.toFixed(3) ?? 'N/A'}
                                </Metric>
                              </div>
                              <div className={`p-3 rounded-lg ${prediction.is_anomaly ? 'bg-red-50' : 'bg-emerald-50'}`}>
                                <Text className="text-xs text-gray-500">Confiança</Text>
                                <Metric className={`text-lg ${prediction.is_anomaly ? 'text-red-600' : 'text-emerald-600'}`}>
                                  {prediction.confidence?.toFixed(1) ?? 0}%
                                </Metric>
                              </div>
                            </Grid>

                            {/* Contributing Features - Fatores de Risco */}
                            {prediction.contributing_features && prediction.contributing_features.length > 0 && (
                              <div className="mb-3">
                                <Text className="text-sm font-medium text-gray-700 mb-2">
                                  ⚠️ Fatores de Risco Detectados:
                                </Text>
                                {prediction.contributing_features.slice(0, 3).map((f, idx) => (
                                  <div key={idx} className="p-2 bg-red-50 rounded mb-1 border-l-2 border-red-400">
                                    <Flex justifyContent="between" alignItems="center">
                                      <Flex alignItems="center" className="gap-2">
                                        {getFeatureIcon(f.feature)}
                                        <Text className="text-sm font-medium">{getFeatureName(f.feature)}</Text>
                                      </Flex>
                                      <Badge color={f.severity === 'high' ? 'red' : 'orange'} size="xs">
                                        {f.severity === 'high' ? 'CRÍTICO' : 'ATENÇÃO'}
                                      </Badge>
                                    </Flex>
                                    <Text className="text-xs text-gray-600 mt-1">
                                      Valor: <strong>{f.current_value?.toFixed(1) ?? 'N/A'}</strong> |
                                      Normal: {f.expected_mean?.toFixed(1) ?? 'N/A'} |
                                      Desvio: {f.z_score?.toFixed(1) ?? 'N/A'}σ
                                    </Text>
                                  </div>
                                ))}
                              </div>
                            )}

                            {/* Recommendation */}
                            {prediction.recommendation && (
                              <div className={`p-3 rounded-lg ${prediction.is_anomaly ? 'bg-red-100 border border-red-200' : 'bg-emerald-100 border border-emerald-200'}`}>
                                <Text className={`text-sm font-medium ${prediction.is_anomaly ? 'text-red-800' : 'text-emerald-800'}`}>
                                  💡 {prediction.recommendation}
                                </Text>
                              </div>
                            )}
                          </>
                        )}

                        {/* Timestamp */}
                        {prediction.timestamp && (
                          <Text className="text-xs text-gray-400 mt-3 flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            Última análise: {new Date(prediction.timestamp).toLocaleString('pt-BR')}
                          </Text>
                        )}
                      </div>
                    )}

                    {/* Run prediction button if model exists but no prediction yet and not loading */}
                    {hasModel && !prediction && !isLoadingPrediction && (
                      <div className="mt-4">
                        <Button
                          size="xs"
                          variant="secondary"
                          icon={PlayCircle}
                          onClick={() => runPrediction(eq.equipment_id)}
                        >
                          Executar Predição
                        </Button>
                      </div>
                    )}
                  </Card>
                );
              })}
            </Grid>

            {/* Algorithm Info */}
            <Card className="mt-6" decoration="left" decorationColor="purple">
              <Flex alignItems="start" className="gap-4">
                <Brain className="h-8 w-8 text-purple-600 flex-shrink-0" />
                <div>
                  <Title>Sobre o Algoritmo de Detecção</Title>
                  <Text className="text-gray-600 mt-2">
                    <strong>Isolation Forest</strong> é um algoritmo de Machine Learning não supervisionado
                    especializado em detecção de anomalias. Ele funciona isolando observações anômalas
                    através de partições recursivas aleatórias.
                  </Text>
                  <Grid numItemsMd={3} className="gap-4 mt-4">
                    <div className="p-3 bg-purple-50 rounded-lg">
                      <Text className="font-medium text-purple-700">Features Analisadas</Text>
                      <Text className="text-sm text-gray-600">Vibração, Temperatura, Corrente, Potência, Carga</Text>
                    </div>
                    <div className="p-3 bg-purple-50 rounded-lg">
                      <Text className="font-medium text-purple-700">Contamination</Text>
                      <Text className="text-sm text-gray-600">5% (proporção esperada de anomalias)</Text>
                    </div>
                    <div className="p-3 bg-purple-50 rounded-lg">
                      <Text className="font-medium text-purple-700">Treinamento</Text>
                      <Text className="text-sm text-gray-600">30 dias de dados históricos por equipamento</Text>
                    </div>
                  </Grid>
                </div>
              </Flex>
            </Card>
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
