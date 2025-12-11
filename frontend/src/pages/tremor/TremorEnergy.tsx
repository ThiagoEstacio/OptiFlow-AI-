/**
 * ⚡ Energy Management Dashboard with Tremor
 * ==========================================
 *
 * Executive energy monitoring with ML predictions and cost optimization.
 */
import React, { useState, useEffect } from 'react';
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
  Callout,
  Button,
  List,
  ListItem,
} from '@tremor/react';
import {
  ProfessionalAreaChart,
  ProfessionalDonutChart,
  ProfessionalLineChart,
} from '../../components/charts/ProfessionalCharts';
import {
  Zap,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  DollarSign,
  Clock,
  Gauge,
  Factory,
  RefreshCw,
  Download,
  Target,
  Brain,
  Lightbulb,
  Sun,
  Moon,
} from 'lucide-react';
import { format } from 'date-fns';
import apiClient from '../../api/client';
import { NoDataAvailable, NoMLPrediction } from '../../components/common/NoDataAvailable';
import { selectStyles } from '../../components/common/StyledSelect';

// Function to fetch real data from APIs
// Now properly maps to the new backend endpoint structure with real InfluxDB data
const fetchRealEnergyData = async (timeRange: string) => {
  // Fetch energy metrics from API (now returns real InfluxDB data when available)
  const energyResponse = await apiClient.get('/api/v1/executive-summary/energy', {
    params: { time_range: timeRange }
  }).catch(() => ({ data: null }));

  // Fetch ML insights for energy predictions
  const mlResponse = await apiClient.get('/api/v1/ml/insights/all', {
    params: { time_range: timeRange }
  }).catch(() => ({ data: null }));

  // Fetch energy tags for real-time values
  const tagsResponse = await apiClient.get('/api/v1/timeseries/tags/active', {
    params: { lookback_hours: timeRange === '1h' ? 1 : timeRange === '6h' ? 6 : 24 }
  }).catch(() => ({ data: { tags: [] } }));

  const energyData = energyResponse.data || {};
  // ML API returns { insights: { energy_prediction: {...}, ... } }
  const mlData = mlResponse.data?.insights || mlResponse.data || {};
  const tags = tagsResponse.data?.tags || [];

  // Check data source (influxdb = real data, simulated = fallback)
  const dataSource = energyData.data_source || 'unknown';
  const isRealData = dataSource === 'influxdb';

  // Find energy-related tags for additional real-time data
  const energyTags = tags.filter((t: any) =>
    t.name?.toLowerCase().includes('energ') ||
    t.name?.toLowerCase().includes('kwh') ||
    t.name?.toLowerCase().includes('pot') ||
    t.unit?.includes('kW') ||
    t.unit?.includes('kWh')
  );

  // Use API data directly (already structured from backend)
  const currentData = energyData.current || {};
  const periodData = energyData.period || {};
  const forecastData = energyData.forecast || {};
  const billData = energyData.bill_forecast || {};
  const efficiencyData = energyData.efficiency || {};
  const peakDemandData = energyData.peak_demand || {};

  // Override with real-time tag values if available
  const currentConsumption = energyTags.find((t: any) =>
    t.unit?.includes('kWh')
  )?.value || currentData.consumption_kwh || 0;

  const currentDemand = energyTags.find((t: any) =>
    t.name?.toLowerCase().includes('demanda') || t.unit === 'kW'
  )?.value || currentData.demand_kw || 0;

  // Build data from API responses
  return {
    current: {
      consumption_kwh: currentConsumption,
      demand_kw: currentDemand,
      power_factor: currentData.power_factor || 0.92,
      status: currentData.status || 'unknown',
    },
    period: {
      total_kwh: periodData.total_kwh || 0,
      average_kwh_hour: periodData.average_kwh_hour || 0,
      peak_demand_kw: periodData.peak_demand_kw || 0,
      change_percent: periodData.change_percent || 0,
    },
    forecast: {
      monthly_kwh: forecastData.monthly_kwh || 0,
      confidence: forecastData.confidence || (mlData.energy_prediction?.predicted_24h?.[0]?.confidence * 100) || 0,
      trend: mlData.energy_prediction?.trend || periodData.trend || forecastData.trend || 'unknown',
      peak_demand_forecast_kw: forecastData.peak_demand_forecast_kw || 0,
      methodology: forecastData.methodology || 'LSTM Neural Network',
      hasModel: !!(mlData.energy_prediction?.status === 'success' && mlData.energy_prediction?.predicted_24h?.length > 0),
    },
    bill_forecast: {
      energy_cost: billData.energy_cost || 0,
      demand_cost: billData.demand_cost || 0,
      taxes: billData.taxes || 0,
      total_estimate: billData.total_estimate || 0,
      breakdown: {
        peak_consumption_kwh: billData.breakdown?.peak_consumption_kwh || 0,
        off_peak_consumption_kwh: billData.breakdown?.off_peak_consumption_kwh || 0,
        peak_tariff: billData.breakdown?.peak_tariff || 0,
        off_peak_tariff: billData.breakdown?.off_peak_tariff || 0,
        demand_tariff: billData.breakdown?.demand_tariff || 0,
      },
    },
    efficiency: {
      kwh_per_ton: efficiencyData.kwh_per_ton || 0,
      cost_per_ton: efficiencyData.cost_per_ton || 0,
      target_kwh_per_ton: efficiencyData.target_kwh_per_ton || 0.40,
      status: efficiencyData.status || 'unknown',
    },
    peak_demand: {
      current_kw: peakDemandData.current_kw || currentDemand,
      contracted_kw: peakDemandData.contracted_kw || 2000,
      utilization_percent: peakDemandData.utilization_percent || 0,
      risk_of_penalty: peakDemandData.risk_of_penalty || false,
    },
    // History from API (real InfluxDB data when available)
    history: (energyData.history || []).map((h: any) => ({
      hour: h.timestamp ? new Date(h.timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : '',
      consumption: h.consumption_kwh || 0,
      timestamp: h.timestamp,
      is_peak_hour: h.is_peak_hour || false,
    })),
    // ML predictions from API - energy_prediction.predicted_24h array
    ml_predictions: mlData.energy_prediction?.predicted_24h?.map((p: any) => ({
      hour: p.timestamp ? new Date(p.timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : `+${p.hour_ahead}h`,
      predicted: p.predicted_consumption_kwh || 0,
      confidence: (p.confidence * 100) || 0,
    })) || [],
    // Insights from energy API or ML API
    insights: energyData.insights || [
      // Energy prediction insights
      ...(mlData.energy_prediction?.recommendations?.map((rec: string) => ({
        type: rec.includes('⚠️') ? 'warning' : 'info',
        title: 'Previsão de Energia',
        description: rec,
        recommendation: '',
      })) || []),
      // Efficiency insights
      ...(mlData.efficiency?.alerts?.map((alert: string) => ({
        type: 'warning',
        title: 'Eficiência Energética',
        description: alert,
        recommendation: '',
      })) || []),
      // Cost optimization insights
      ...(mlData.cost_optimization?.recommendations?.slice(0, 2).map((rec: string) => ({
        type: 'success',
        title: 'Otimização de Custos',
        description: rec,
        recommendation: '',
      })) || []),
    ].slice(0, 4),
    // Savings opportunities from ML API cost_optimization
    savings_opportunities: mlData.cost_optimization ? [
      {
        action: mlData.cost_optimization.optimization_strategy || 'Otimização de carga',
        savings: mlData.cost_optimization.potential_savings_monthly || 0,
        priority: 'high',
      },
      ...(mlData.cost_optimization.recommendations?.slice(0, 3).map((rec: string, idx: number) => ({
        action: rec,
        savings: (mlData.cost_optimization.potential_savings_monthly || 0) * (0.3 - idx * 0.1),
        priority: idx === 0 ? 'medium' : 'low',
      })) || []),
    ] : [],
    // Track data source and availability
    _meta: {
      dataSource: dataSource,
      isRealData: isRealData,
      hasEnergyData: !!energyResponse.data,
      hasMLData: !!mlResponse.data,
      hasTagsData: tags.length > 0,
      generatedAt: energyData.generated_at,
      lastUpdate: new Date().toISOString(),
    },
  };
};

// Format helpers
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

const formatNumber = (value: number, decimals = 1) => {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

export const TremorEnergy: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('24h');
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Try to fetch real data from APIs
        const realData = await fetchRealEnergyData(timeRange);
        setData(realData);
        setLastUpdated(new Date());
      } catch (err) {
        console.error('Error fetching energy data:', err);
        // CORR-001: Do NOT use fallback data - show error state instead
        setError('Não foi possível carregar dados de energia. Tente novamente.');
        // Keep existing data if available, otherwise set empty structure
        if (!data) {
          setData({
            current: { consumption_kwh: 0, demand_kw: 0, power_factor: 0, status: 'error' },
            period: { total_kwh: 0, average_kwh_hour: 0, peak_demand_kw: 0, change_percent: 0 },
            forecast: { monthly_kwh: 0, confidence: 0, trend: 'unknown', peak_demand_forecast_kw: 0, hasModel: false },
            bill_forecast: { energy_cost: 0, demand_cost: 0, taxes: 0, total_estimate: 0, breakdown: {} },
            efficiency: { kwh_per_ton: 0, cost_per_ton: 0, target_kwh_per_ton: 80, status: 'unknown' },
            peak_demand: { current_kw: 0, contracted_kw: 0, utilization_percent: 0, risk_of_penalty: false },
            history: [],
            ml_predictions: [],
            insights: [],
            savings_opportunities: [],
            _meta: { hasEnergyData: false, hasMLData: false, hasTagsData: false },
          });
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [timeRange]);

  const handleRefresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const realData = await fetchRealEnergyData(timeRange);
      setData(realData);
    } catch (err) {
      // CORR-001: Do NOT use fallback - show error
      setError('Erro ao atualizar dados.');
    } finally {
      setLoading(false);
    }
    setLastUpdated(new Date());
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
      </div>
    );
  }

  const current = data?.current || {};
  const period = data?.period || {};
  const bill = data?.bill_forecast || {};
  const peak = data?.peak_demand || {};
  const efficiency = data?.efficiency || {};

  const demandColor = peak.utilization_percent > 90 ? 'red' : peak.utilization_percent > 75 ? 'amber' : 'emerald';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <Zap className="w-8 h-8 text-amber-500" />
          <div>
            <Flex alignItems="center" className="gap-2">
              <Title>Gerenciamento de Energia</Title>
              {data?._meta?.isRealData ? (
                <Badge color="emerald" size="sm">Dados Reais (InfluxDB)</Badge>
              ) : (
                <Badge color="amber" size="sm">Dados Simulados</Badge>
              )}
            </Flex>
            <Text>Dashboard Executivo • Atualizado: {format(lastUpdated, 'HH:mm:ss')}</Text>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2.5 text-sm font-medium border border-gray-300 rounded-lg bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 cursor-pointer appearance-none"
            style={{ ...selectStyles, minWidth: '150px' }}
          >
            <option value="1h">1 hora</option>
            <option value="6h">6 horas</option>
            <option value="24h">24 horas</option>
            <option value="7d">7 dias</option>
            <option value="30d">30 dias</option>
          </select>
          <Button size="xs" variant="secondary" icon={RefreshCw} onClick={handleRefresh}>
            Atualizar
          </Button>
          <Button size="xs" variant="secondary" icon={Download}>
            Exportar
          </Button>
        </div>
      </div>

      {/* KPIs Row */}
      <Grid numItemsSm={2} numItemsLg={6} className="gap-4">
        <Card decoration="left" decorationColor="blue">
          <Text>Consumo Atual</Text>
          <Metric>{formatNumber(current.consumption_kwh, 0)}</Metric>
          <Text className="text-sm">kWh</Text>
        </Card>

        <Card decoration="left" decorationColor="violet">
          <Text>Demanda</Text>
          <Metric>{formatNumber(current.demand_kw, 0)}</Metric>
          <Text className="text-sm">kW ({peak.utilization_percent?.toFixed(0)}% contratada)</Text>
        </Card>

        <Card decoration="left" decorationColor="amber">
          <Text>Consumo Período</Text>
          <Metric>{formatNumber(period.total_kwh / 1000, 1)}</Metric>
          <Text className="text-sm">MWh</Text>
          <BadgeDelta deltaType={period.change_percent < 0 ? 'decrease' : 'increase'} className="mt-1">
            {period.change_percent?.toFixed(1)}%
          </BadgeDelta>
        </Card>

        <Card decoration="left" decorationColor="emerald">
          <Text>Previsão Conta</Text>
          <Metric>{formatCurrency(bill.total_estimate)}</Metric>
          <Text className="text-sm">Este mês</Text>
        </Card>

        <Card decoration="left" decorationColor={efficiency.status === 'warning' ? 'amber' : 'emerald'}>
          <Text>Eficiência</Text>
          <Metric>{formatNumber(efficiency.kwh_per_ton)}</Metric>
          <Text className="text-sm">kWh/ton (meta: {efficiency.target_kwh_per_ton})</Text>
        </Card>

        <Card decoration="left" decorationColor={current.power_factor >= 0.92 ? 'emerald' : 'amber'}>
          <Text>Fator de Potência</Text>
          <Metric>{current.power_factor?.toFixed(2)}</Metric>
          <Text className="text-sm">{current.power_factor >= 0.92 ? 'OK' : 'Abaixo ideal'}</Text>
        </Card>
      </Grid>

      {/* Tabs */}
      <TabGroup>
        <TabList>
          <Tab icon={Zap}>Consumo</Tab>
          <Tab icon={DollarSign}>Custos</Tab>
          <Tab icon={Brain}>Previsões ML</Tab>
          <Tab icon={Lightbulb}>Otimização</Tab>
        </TabList>

        <TabPanels>
          {/* Consumption Tab */}
          <TabPanel>
            <div className="mt-6 space-y-6">
              <Grid numItemsSm={1} numItemsLg={2} className="gap-6">
                {/* Consumption Chart */}
                <Card>
                  <Flex justifyContent="between" alignItems="center">
                    <Title>Consumo por Hora</Title>
                    <div className="flex items-center gap-4 text-sm">
                      <div className="flex items-center gap-1">
                        <Sun className="w-4 h-4 text-amber-500" />
                        <Text>Fora Ponta</Text>
                      </div>
                      <div className="flex items-center gap-1">
                        <Moon className="w-4 h-4 text-red-500" />
                        <Text>Ponta (17-21h)</Text>
                      </div>
                    </div>
                  </Flex>
                  <div className="mt-4">
                    <ProfessionalAreaChart
                      data={data?.history || []}
                      xAxisKey="hour"
                      dataKey="consumption"
                      color="#3b82f6"
                      height={288}
                      showGrid={true}
                    />
                  </div>
                </Card>

                {/* Demand Gauge */}
                <Card>
                  <Title>Demanda Contratada</Title>
                  <div className="mt-6 text-center">
                    <Metric className={`text-5xl ${demandColor === 'emerald' ? 'text-emerald-600' : demandColor === 'amber' ? 'text-amber-600' : 'text-red-600'}`}>
                      {peak.utilization_percent?.toFixed(0)}%
                    </Metric>
                    <Text className="mt-2">Utilização</Text>
                    <ProgressBar value={peak.utilization_percent} color={demandColor} className="mt-4" />
                    <Flex justifyContent="between" className="mt-4">
                      <div>
                        <Text className="text-sm">Atual</Text>
                        <Text className="font-bold">{formatNumber(peak.current_kw, 0)} kW</Text>
                      </div>
                      <div className="text-right">
                        <Text className="text-sm">Contratada</Text>
                        <Text className="font-bold">{formatNumber(peak.contracted_kw, 0)} kW</Text>
                      </div>
                    </Flex>
                    {peak.risk_of_penalty && (
                      <Callout title="Risco de Multa" color="red" className="mt-4">
                        Demanda próxima do limite contratado!
                      </Callout>
                    )}
                  </div>
                </Card>
              </Grid>

              {/* Insights */}
              <Card>
                <Title>Insights</Title>
                <div className="mt-4 space-y-3">
                  {data?.insights?.map((insight: any, index: number) => (
                    <Callout
                      key={index}
                      title={insight.title}
                      color={insight.type === 'warning' ? 'amber' : insight.type === 'success' ? 'emerald' : 'blue'}
                    >
                      {insight.description}
                      {insight.recommendation && <Text className="mt-1 text-sm font-medium">{insight.recommendation}</Text>}
                    </Callout>
                  ))}
                </div>
              </Card>
            </div>
          </TabPanel>

          {/* Costs Tab */}
          <TabPanel>
            <div className="mt-6 space-y-6">
              {/* Bill Summary */}
              <Card className="bg-gradient-to-r from-amber-50 to-white">
                <Flex justifyContent="between" alignItems="center">
                  <div>
                    <Text>Previsão de Conta</Text>
                    <Metric className="text-amber-600">{formatCurrency(bill.total_estimate)}</Metric>
                  </div>
                  <DollarSign className="w-16 h-16 text-amber-500" />
                </Flex>
              </Card>

              <Grid numItemsSm={1} numItemsLg={2} className="gap-6">
                {/* Bill Breakdown */}
                <Card>
                  <Title>Composição da Conta</Title>
                  <div className="mt-6">
                    <ProfessionalDonutChart
                      data={[
                        { name: 'Consumo Ponta', value: bill.breakdown?.peak_consumption_kwh * bill.breakdown?.peak_tariff || 0 },
                        { name: 'Consumo F. Ponta', value: bill.breakdown?.off_peak_consumption_kwh * bill.breakdown?.off_peak_tariff || 0 },
                        { name: 'Demanda', value: bill.demand_cost || 0 },
                        { name: 'Impostos', value: bill.taxes || 0 },
                      ]}
                      colors={['#ef4444', '#10b981', '#f59e0b', '#94a3b8']}
                      height={240}
                      showLegend={true}
                    />
                  </div>
                </Card>

                {/* Tariffs */}
                <Card>
                  <Title>Tarifas Vigentes</Title>
                  <div className="mt-4 space-y-4">
                    <div className="p-3 bg-red-50 rounded-lg border-l-4 border-red-500">
                      <Flex justifyContent="between">
                        <div>
                          <Text className="font-medium">Ponta (17h-21h)</Text>
                          <Text className="text-sm">Horário de maior tarifa</Text>
                        </div>
                        <Text className="text-xl font-bold text-red-600">
                          R$ {bill.breakdown?.peak_tariff?.toFixed(2)}/kWh
                        </Text>
                      </Flex>
                    </div>

                    <div className="p-3 bg-emerald-50 rounded-lg border-l-4 border-emerald-500">
                      <Flex justifyContent="between">
                        <div>
                          <Text className="font-medium">Fora Ponta</Text>
                          <Text className="text-sm">Demais horários</Text>
                        </div>
                        <Text className="text-xl font-bold text-emerald-600">
                          R$ {bill.breakdown?.off_peak_tariff?.toFixed(2)}/kWh
                        </Text>
                      </Flex>
                    </div>

                    <div className="p-3 bg-amber-50 rounded-lg border-l-4 border-amber-500">
                      <Flex justifyContent="between">
                        <div>
                          <Text className="font-medium">Demanda</Text>
                          <Text className="text-sm">Contratada</Text>
                        </div>
                        <Text className="text-xl font-bold text-amber-600">
                          R$ {bill.breakdown?.demand_tariff?.toFixed(2)}/kW
                        </Text>
                      </Flex>
                    </div>
                  </div>
                </Card>
              </Grid>
            </div>
          </TabPanel>

          {/* ML Predictions Tab */}
          <TabPanel>
            <div className="mt-6 space-y-6">
              {/* CORR-001: Check if ML model is available */}
              {data?.forecast?.hasModel && data?.ml_predictions?.length > 0 ? (
                <>
                  {/* Real vs Predicted Chart */}
                  <Card>
                    <Flex justifyContent="between" alignItems="center">
                      <div className="flex items-center gap-2">
                        <Brain className="w-5 h-5 text-violet-500" />
                        <Title>Real vs Previsto - Análise Comparativa</Title>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-1">
                          <div className="w-3 h-3 rounded-full bg-blue-500" />
                          <Text className="text-sm">Real</Text>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className="w-3 h-3 rounded-full bg-violet-500" />
                          <Text className="text-sm">Previsto</Text>
                        </div>
                        <Badge color="violet">Confiança: {data?.forecast?.confidence || 0}%</Badge>
                      </div>
                    </Flex>
                    <div className="mt-4">
                      {/* CORR-001: Only show chart if we have both history AND predictions */}
                      {data?.history?.length > 0 ? (
                        <ProfessionalLineChart
                          data={(data?.history || []).map((h: any, i: number) => ({
                            ...h,
                            real: h.consumption,
                            // CORR-001: Use prediction if available, otherwise null (no fake data)
                            predicted: data?.ml_predictions?.[i]?.predicted || null,
                          }))}
                          xAxisKey="hour"
                          lines={[
                            { dataKey: 'real', name: 'Consumo Real', color: '#3b82f6' },
                            { dataKey: 'predicted', name: 'Previsão ML', color: '#8b5cf6' },
                          ]}
                          height={320}
                          showGrid={true}
                          showLegend={true}
                        />
                      ) : (
                        <NoDataAvailable
                          variant="empty"
                          title="Sem Dados Históricos"
                          description="Não há dados históricos de consumo para o período selecionado."
                          showCard={false}
                          size="sm"
                        />
                      )}
                    </div>
                    {/* CORR-001: Only calculate MAPE if we have real predictions */}
                    {data?.history?.length > 0 && data?.ml_predictions?.length > 0 && (
                      <div className="mt-4 grid grid-cols-3 gap-4">
                        <div className="p-3 bg-blue-50 rounded-lg text-center">
                          <Text className="text-sm text-gray-600">Erro Médio (MAPE)</Text>
                          <Text className="text-xl font-bold text-blue-600">
                            {(() => {
                              const validPairs = (data?.history || []).filter((_: any, i: number) =>
                                data?.ml_predictions?.[i]?.predicted && data?.ml_predictions?.[i]?.predicted > 0
                              );
                              if (validPairs.length === 0) return 'N/A';
                              const mape = validPairs.reduce((sum: number, h: any, i: number) => {
                                const pred = data?.ml_predictions?.[i]?.predicted || 0;
                                if (h.consumption > 0 && pred > 0) {
                                  return sum + Math.abs((h.consumption - pred) / h.consumption);
                                }
                                return sum;
                              }, 0) / validPairs.length * 100;
                              return `${mape.toFixed(1)}%`;
                            })()}
                          </Text>
                        </div>
                        <div className="p-3 bg-emerald-50 rounded-lg text-center">
                          <Text className="text-sm text-gray-600">Precisão</Text>
                          <Text className="text-xl font-bold text-emerald-600">
                            {data?.forecast?.confidence ? `${data.forecast.confidence}%` : 'N/A'}
                          </Text>
                        </div>
                        <div className="p-3 bg-violet-50 rounded-lg text-center">
                          <Text className="text-sm text-gray-600">Modelo</Text>
                          <Text className="text-xl font-bold text-violet-600">LSTM</Text>
                        </div>
                      </div>
                    )}
                  </Card>

                  {/* Prediction Only Chart */}
                  <Card>
                    <Flex justifyContent="between" alignItems="center">
                      <div className="flex items-center gap-2">
                        <Brain className="w-5 h-5 text-violet-500" />
                        <Title>Previsão LSTM - Próximas 24h</Title>
                      </div>
                      <Badge color="violet">Confiança: {data?.forecast?.confidence || 0}%</Badge>
                    </Flex>
                    <div className="mt-4">
                      <ProfessionalLineChart
                        data={data?.ml_predictions || []}
                        xAxisKey="hour"
                        lines={[
                          { dataKey: 'predicted', name: 'Predição', color: '#8b5cf6' },
                        ]}
                        height={288}
                        showGrid={true}
                        showLegend={false}
                      />
                    </div>
                  </Card>

                  <Grid numItemsSm={2} numItemsLg={3} className="gap-6">
                    <Card>
                      <Text>Consumo Mensal Previsto</Text>
                      <Metric className="text-violet-600">
                        {data?.forecast?.monthly_kwh > 0 ? `${formatNumber(data.forecast.monthly_kwh / 1000000, 2)} GWh` : 'N/A'}
                      </Metric>
                      <Text className="mt-2 text-sm">Metodologia: LSTM Neural Network</Text>
                    </Card>

                    <Card>
                      <Text>Pico de Demanda Previsto</Text>
                      <Metric className="text-amber-600">
                        {data?.forecast?.peak_demand_forecast_kw > 0 ? `${formatNumber(data.forecast.peak_demand_forecast_kw, 0)} kW` : 'N/A'}
                      </Metric>
                      <Text className="mt-2 text-sm">Próximas 24 horas</Text>
                    </Card>

                    <Card>
                      <Text>Tendência</Text>
                      <Flex alignItems="center" className="mt-2">
                        {data?.forecast?.trend === 'up' ? (
                          <TrendingUp className="w-8 h-8 text-red-500" />
                        ) : data?.forecast?.trend === 'down' ? (
                          <TrendingDown className="w-8 h-8 text-emerald-500" />
                        ) : (
                          <Gauge className="w-8 h-8 text-blue-500" />
                        )}
                        <Metric className="ml-2">
                          {data?.forecast?.trend === 'up' ? 'Alta' :
                           data?.forecast?.trend === 'down' ? 'Baixa' :
                           data?.forecast?.trend === 'unknown' ? 'Indisponível' : 'Estável'}
                        </Metric>
                      </Flex>
                    </Card>
                  </Grid>
                </>
              ) : (
                /* CORR-001: Show NoMLPrediction when model is not trained */
                <NoMLPrediction equipmentName="Energia" />
              )}
            </div>
          </TabPanel>

          {/* Optimization Tab */}
          <TabPanel>
            <div className="mt-6 space-y-6">
              {/* Savings Summary */}
              <Card className="bg-gradient-to-r from-emerald-50 to-white">
                <Flex justifyContent="between" alignItems="center">
                  <div>
                    <Text>Economia Potencial Total</Text>
                    <Metric className="text-emerald-600">
                      {formatCurrency(data?.savings_opportunities?.reduce((s: number, o: any) => s + o.savings, 0) || 0)}
                    </Metric>
                    <Text className="mt-2 text-sm">Por mês</Text>
                  </div>
                  <Target className="w-16 h-16 text-emerald-500" />
                </Flex>
              </Card>

              <Card>
                <Title>Oportunidades de Otimização</Title>
                <div className="mt-4 space-y-4">
                  {data?.savings_opportunities?.map((opp: any, index: number) => (
                    <div key={index} className="p-4 border rounded-lg">
                      <Flex justifyContent="between" alignItems="start">
                        <div className="flex-1">
                          <Flex alignItems="center" className="gap-2">
                            <div className={`w-2 h-2 rounded-full ${
                              opp.priority === 'high' ? 'bg-red-500' :
                              opp.priority === 'medium' ? 'bg-amber-500' : 'bg-gray-400'
                            }`} />
                            <Text className="font-medium">{opp.action}</Text>
                          </Flex>
                          <Badge color={
                            opp.priority === 'high' ? 'red' :
                            opp.priority === 'medium' ? 'amber' : 'gray'
                          } className="mt-2">
                            {opp.priority === 'high' ? 'Alta Prioridade' :
                             opp.priority === 'medium' ? 'Média Prioridade' : 'Baixa Prioridade'}
                          </Badge>
                        </div>
                        <Text className="text-xl font-bold text-emerald-600">
                          {formatCurrency(opp.savings)}/mês
                        </Text>
                      </Flex>
                    </div>
                  ))}
                </div>
              </Card>

              <Callout title="Economia Anual Estimada" icon={DollarSign} color="emerald">
                Implementando todas as recomendações: <strong>
                  {formatCurrency((data?.savings_opportunities?.reduce((s: number, o: any) => s + o.savings, 0) || 0) * 12)}
                </strong> por ano
              </Callout>
            </div>
          </TabPanel>
        </TabPanels>
      </TabGroup>
    </div>
  );
};

export default TremorEnergy;
