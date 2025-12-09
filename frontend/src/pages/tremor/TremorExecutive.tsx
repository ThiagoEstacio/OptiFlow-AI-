/**
 * 🎯 Executive Dashboard - OptiFlow
 * ==================================
 *
 * Dashboard executivo simplificado para gerência e diretoria:
 * - KPIs de alto nível (OEE, Disponibilidade, Performance, Qualidade)
 * - Score de Saúde geral
 * - Resumo de Alarmes (apenas contagem)
 * - Resumo Financeiro
 * - Tendências de produção
 */
import React, { useState, useEffect, useCallback } from 'react';
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
  Callout,
  Button,
} from '@tremor/react';
import {
  ProfessionalAreaChart,
} from '../../components/charts/ProfessionalCharts';
import {
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  DollarSign,
  Activity,
  Clock,
  Download,
  RefreshCw,
  Target,
  AlertCircle,
  Gauge,
  Factory,
  Eye,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import apiClient from '../../api/client';
import { selectStylesSmall } from '../../components/common/StyledSelect';
import { useNavigate } from 'react-router-dom';

// Types
interface KPI {
  value: number;
  target: number;
  trend: 'up' | 'down' | 'stable';
  status: 'good' | 'warning' | 'critical';
}

interface ExecutiveSummary {
  kpis: {
    oee: KPI;
    availability: KPI;
    performance: KPI;
    quality: KPI;
  };
  alarms: {
    total_active: number;
    by_severity: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
    trend: string;
    mttr_hours: number;
  };
  production_trends: {
    production_rate: {
      current: number;
      previous: number;
      unit: string;
      change_percent: number;
      trend: string;
    };
    energy_efficiency: {
      current: number;
      previous: number;
      unit: string;
      change_percent: number;
      trend: string;
    };
    throughput: {
      current: number;
      previous: number;
      unit: string;
      change_percent: number;
      trend: string;
    };
  };
  financial_summary: {
    estimated_savings_today: number;
    downtime_cost_avoided: number;
    efficiency_improvement: number;
    projected_monthly_savings: number;
  };
}

interface EnergyData {
  current: {
    consumption_kwh: number;
    demand_kw: number;
    power_factor: number;
    status: string;
  };
  period: {
    total_kwh: number;
    average_kwh_hour: number;
    peak_demand_kw: number;
    change_percent: number;
    trend: string;
  };
  history: Array<{
    timestamp: string;
    consumption_kwh: number;
    is_peak_hour: boolean;
  }>;
}

interface DashboardStats {
  total_devices: number;
  active_devices: number;
  total_tags: number;
  active_alarms: number;
  data_points_today: number;
}

// Helper functions
const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

const formatNumber = (value: number, decimals = 1): string => {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

const getStatusColor = (status: string): 'emerald' | 'amber' | 'red' | 'blue' => {
  switch (status) {
    case 'good':
      return 'emerald';
    case 'warning':
      return 'amber';
    case 'critical':
      return 'red';
    default:
      return 'blue';
  }
};

const getDeltaType = (trend: string): 'increase' | 'decrease' | 'unchanged' => {
  if (trend === 'stable') return 'unchanged';
  return trend === 'up' ? 'increase' : 'decrease';
};

export const TremorExecutive: React.FC = () => {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<ExecutiveSummary | null>(null);
  const [energy, setEnergy] = useState<EnergyData | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('24h');
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [summaryRes, energyRes, statsRes] = await Promise.all([
        apiClient.get(`/api/v1/executive-summary/overview?time_range=${timeRange}`),
        apiClient.get(`/api/v1/executive-summary/energy?time_range=${timeRange}`),
        apiClient.get('/api/v1/dashboard/stats'),
      ]);

      setSummary(summaryRes.data);
      setEnergy(energyRes.data);
      setStats(statsRes.data);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching executive data:', err);
      setError('Erro ao carregar dados. Tentando novamente...');
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-700 font-medium">Carregando dashboard executivo...</p>
        </div>
      </div>
    );
  }

  const kpis = summary?.kpis;
  const alarms = summary?.alarms;
  const production = summary?.production_trends;
  const financial = summary?.financial_summary;

  // Calculate overall health score
  const healthScore = kpis
    ? Math.round((kpis.oee.value + kpis.availability.value + kpis.performance.value + kpis.quality.value) / 4)
    : 0;
  const healthStatus = healthScore >= 85 ? 'good' : healthScore >= 70 ? 'warning' : 'critical';

  // Prepare energy chart data
  const energyChartData = energy?.history?.map((item) => ({
    hora: format(new Date(item.timestamp), 'HH:mm'),
    consumo: item.consumption_kwh,
  })) || [];

  return (
    <div className="space-y-6 bg-slate-50 min-h-screen -m-6 p-6">
      {/* Hero Header */}
      <div className="bg-gradient-to-r from-slate-900 via-blue-900 to-slate-900 rounded-xl p-6 text-white shadow-2xl">
        <Flex justifyContent="between" alignItems="start" className="flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Eye className="w-8 h-8 text-blue-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Executive Dashboard</h1>
                <p className="text-blue-300 text-sm">
                  Visão Geral • {format(lastUpdated, "dd/MM HH:mm", { locale: ptBR })}
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-2 text-sm font-medium border border-white/30 rounded-lg bg-white/10 text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400 cursor-pointer appearance-none backdrop-blur"
              style={{
                ...selectStylesSmall,
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='white'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
                minWidth: '130px'
              }}
            >
              <option value="1h" className="text-gray-900">1 hora</option>
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

        {/* Health Score & Quick Stats */}
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-5 gap-4">
          {/* Main Health Score */}
          <div className="bg-white/10 rounded-xl p-5 backdrop-blur text-center">
            <p className="text-blue-200 text-sm font-medium mb-2">Score de Saúde</p>
            <div className="relative inline-flex items-center justify-center">
              <svg className="w-24 h-24 transform -rotate-90">
                <circle className="text-white/10" strokeWidth="8" stroke="currentColor" fill="transparent" r="44" cx="48" cy="48" />
                <circle
                  className={healthStatus === 'good' ? 'text-emerald-400' : healthStatus === 'warning' ? 'text-amber-400' : 'text-red-400'}
                  strokeWidth="8"
                  strokeDasharray={`${healthScore * 2.76} 276`}
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="transparent"
                  r="44"
                  cx="48"
                  cy="48"
                />
              </svg>
              <span className="absolute text-2xl font-bold">{healthScore}%</span>
            </div>
            <Badge color={getStatusColor(healthStatus)} size="lg" className="mt-2">
              {healthStatus === 'good' ? 'Saudável' : healthStatus === 'warning' ? 'Atenção' : 'Crítico'}
            </Badge>
          </div>

          {/* Quick Stats */}
          <div className="bg-white/10 rounded-xl p-4 backdrop-blur">
            <Flex justifyContent="between" alignItems="start">
              <div>
                <p className="text-blue-200 text-xs font-medium">Dispositivos Ativos</p>
                <p className="text-3xl font-bold mt-1">{stats?.active_devices || 0}</p>
                <p className="text-blue-300 text-xs">de {stats?.total_devices || 0} total</p>
              </div>
              <Factory className="w-8 h-8 text-blue-400" />
            </Flex>
          </div>

          <div className="bg-white/10 rounded-xl p-4 backdrop-blur">
            <Flex justifyContent="between" alignItems="start">
              <div>
                <p className="text-blue-200 text-xs font-medium">Tags Monitorados</p>
                <p className="text-3xl font-bold mt-1">{stats?.total_tags || 0}</p>
                <p className="text-blue-300 text-xs">{formatNumber(stats?.data_points_today || 0, 0)} pts/dia</p>
              </div>
              <Activity className="w-8 h-8 text-emerald-400" />
            </Flex>
          </div>

          <div
            className="bg-white/10 rounded-xl p-4 backdrop-blur cursor-pointer hover:bg-white/15 transition-colors"
            onClick={() => navigate('/alarms')}
          >
            <Flex justifyContent="between" alignItems="start">
              <div>
                <p className="text-blue-200 text-xs font-medium">Alarmes Ativos</p>
                <p className="text-3xl font-bold mt-1 text-red-400">{alarms?.total_active || 0}</p>
                <p className="text-red-300 text-xs">{alarms?.by_severity?.critical || 0} críticos</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-400" />
            </Flex>
          </div>

          <div className="bg-white/10 rounded-xl p-4 backdrop-blur">
            <Flex justifyContent="between" alignItems="start">
              <div>
                <p className="text-blue-200 text-xs font-medium">Economia Hoje</p>
                <p className="text-2xl font-bold mt-1 text-emerald-400">
                  {formatCurrency(financial?.estimated_savings_today || 0)}
                </p>
                <p className="text-emerald-300 text-xs">custos evitados</p>
              </div>
              <DollarSign className="w-8 h-8 text-emerald-400" />
            </Flex>
          </div>
        </div>
      </div>

      {/* KPIs Section */}
      <div>
        <div className="mb-4">
          <h2 className="text-xl font-bold text-gray-900">Indicadores-Chave de Performance</h2>
          <p className="text-gray-600 text-sm">Monitoramento dos principais indicadores operacionais</p>
        </div>
        <Grid numItemsSm={2} numItemsLg={4} className="gap-4">
          {/* OEE Card */}
          <Card decoration="top" decorationColor={getStatusColor(kpis?.oee.status || 'warning')} className="bg-white">
            <Flex justifyContent="between" alignItems="start">
              <div>
                <p className="text-gray-600 font-medium text-sm">OEE Geral</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{formatNumber(kpis?.oee.value || 0)}%</p>
              </div>
              <div className={`p-2 rounded-lg ${kpis?.oee.status === 'good' ? 'bg-emerald-100' : kpis?.oee.status === 'warning' ? 'bg-amber-100' : 'bg-red-100'}`}>
                <Gauge className={`w-6 h-6 ${kpis?.oee.status === 'good' ? 'text-emerald-600' : kpis?.oee.status === 'warning' ? 'text-amber-600' : 'text-red-600'}`} />
              </div>
            </Flex>
            <Flex justifyContent="between" alignItems="center" className="mt-4">
              <p className="text-xs text-gray-600">Meta: {kpis?.oee.target}%</p>
              <BadgeDelta deltaType={getDeltaType(kpis?.oee.trend || 'stable')}>
                {Math.abs((kpis?.oee.target || 0) - (kpis?.oee.value || 0)).toFixed(1)}%
              </BadgeDelta>
            </Flex>
            <ProgressBar value={kpis?.oee.value || 0} color={getStatusColor(kpis?.oee.status || 'warning')} className="mt-3" />
          </Card>

          {/* Availability Card */}
          <Card decoration="top" decorationColor={getStatusColor(kpis?.availability.status || 'warning')} className="bg-white">
            <Flex justifyContent="between" alignItems="start">
              <div>
                <p className="text-gray-600 font-medium text-sm">Disponibilidade</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{formatNumber(kpis?.availability.value || 0)}%</p>
              </div>
              <div className={`p-2 rounded-lg ${kpis?.availability.status === 'good' ? 'bg-emerald-100' : kpis?.availability.status === 'warning' ? 'bg-amber-100' : 'bg-red-100'}`}>
                <Clock className={`w-6 h-6 ${kpis?.availability.status === 'good' ? 'text-emerald-600' : kpis?.availability.status === 'warning' ? 'text-amber-600' : 'text-red-600'}`} />
              </div>
            </Flex>
            <Flex justifyContent="between" alignItems="center" className="mt-4">
              <p className="text-xs text-gray-600">Meta: {kpis?.availability.target}%</p>
              <BadgeDelta deltaType={getDeltaType(kpis?.availability.trend || 'stable')}>
                {Math.abs((kpis?.availability.target || 0) - (kpis?.availability.value || 0)).toFixed(1)}%
              </BadgeDelta>
            </Flex>
            <ProgressBar value={kpis?.availability.value || 0} color={getStatusColor(kpis?.availability.status || 'warning')} className="mt-3" />
          </Card>

          {/* Performance Card */}
          <Card decoration="top" decorationColor={getStatusColor(kpis?.performance.status || 'warning')} className="bg-white">
            <Flex justifyContent="between" alignItems="start">
              <div>
                <p className="text-gray-600 font-medium text-sm">Performance</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{formatNumber(kpis?.performance.value || 0)}%</p>
              </div>
              <div className={`p-2 rounded-lg ${kpis?.performance.status === 'good' ? 'bg-emerald-100' : kpis?.performance.status === 'warning' ? 'bg-amber-100' : 'bg-red-100'}`}>
                <TrendingUp className={`w-6 h-6 ${kpis?.performance.status === 'good' ? 'text-emerald-600' : kpis?.performance.status === 'warning' ? 'text-amber-600' : 'text-red-600'}`} />
              </div>
            </Flex>
            <Flex justifyContent="between" alignItems="center" className="mt-4">
              <p className="text-xs text-gray-600">Meta: {kpis?.performance.target}%</p>
              <BadgeDelta deltaType={getDeltaType(kpis?.performance.trend || 'stable')}>
                {Math.abs((kpis?.performance.target || 0) - (kpis?.performance.value || 0)).toFixed(1)}%
              </BadgeDelta>
            </Flex>
            <ProgressBar value={kpis?.performance.value || 0} color={getStatusColor(kpis?.performance.status || 'warning')} className="mt-3" />
          </Card>

          {/* Quality Card */}
          <Card decoration="top" decorationColor={getStatusColor(kpis?.quality.status || 'warning')} className="bg-white">
            <Flex justifyContent="between" alignItems="start">
              <div>
                <p className="text-gray-600 font-medium text-sm">Qualidade</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{formatNumber(kpis?.quality.value || 0)}%</p>
              </div>
              <div className={`p-2 rounded-lg ${kpis?.quality.status === 'good' ? 'bg-emerald-100' : kpis?.quality.status === 'warning' ? 'bg-amber-100' : 'bg-red-100'}`}>
                <CheckCircle className={`w-6 h-6 ${kpis?.quality.status === 'good' ? 'text-emerald-600' : kpis?.quality.status === 'warning' ? 'text-amber-600' : 'text-red-600'}`} />
              </div>
            </Flex>
            <Flex justifyContent="between" alignItems="center" className="mt-4">
              <p className="text-xs text-gray-600">Meta: {kpis?.quality.target}%</p>
              <BadgeDelta deltaType={getDeltaType(kpis?.quality.trend || 'stable')}>
                {Math.abs((kpis?.quality.target || 0) - (kpis?.quality.value || 0)).toFixed(1)}%
              </BadgeDelta>
            </Flex>
            <ProgressBar value={kpis?.quality.value || 0} color={getStatusColor(kpis?.quality.status || 'warning')} className="mt-3" />
          </Card>
        </Grid>
      </div>

      {/* Production Trends & Energy */}
      <Grid numItemsSm={1} numItemsLg={2} className="gap-6">
        {/* Production Trends */}
        <Card className="bg-white">
          <Flex justifyContent="between" alignItems="center" className="mb-4">
            <div>
              <h3 className="text-lg font-bold text-gray-900">Tendências de Produção</h3>
              <p className="text-gray-600 text-sm">Comparativo com período anterior</p>
            </div>
            <div className="p-2 bg-blue-100 rounded-lg">
              <Activity className="w-6 h-6 text-blue-600" />
            </div>
          </Flex>

          <div className="space-y-4">
            {/* Production Rate */}
            <div className="p-4 bg-slate-50 rounded-lg">
              <Flex justifyContent="between" alignItems="center">
                <div>
                  <p className="text-sm text-gray-600">Taxa de Produção</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatNumber(production?.production_rate.current || 0, 0)} {production?.production_rate.unit || 't/h'}
                  </p>
                </div>
                <div className="text-right">
                  <Flex alignItems="center" className={`gap-1 ${(production?.production_rate.change_percent || 0) >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                    {(production?.production_rate.change_percent || 0) >= 0 ? (
                      <ArrowUpRight className="w-5 h-5" />
                    ) : (
                      <ArrowDownRight className="w-5 h-5" />
                    )}
                    <span className="font-semibold">{Math.abs(production?.production_rate.change_percent || 0).toFixed(1)}%</span>
                  </Flex>
                  <p className="text-xs text-gray-500">vs. período anterior</p>
                </div>
              </Flex>
            </div>

            {/* Throughput */}
            <div className="p-4 bg-slate-50 rounded-lg">
              <Flex justifyContent="between" alignItems="center">
                <div>
                  <p className="text-sm text-gray-600">Throughput</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatNumber(production?.throughput.current || 0, 0)} {production?.throughput.unit || 'ton'}
                  </p>
                </div>
                <div className="text-right">
                  <Flex alignItems="center" className={`gap-1 ${(production?.throughput.change_percent || 0) >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                    {(production?.throughput.change_percent || 0) >= 0 ? (
                      <ArrowUpRight className="w-5 h-5" />
                    ) : (
                      <ArrowDownRight className="w-5 h-5" />
                    )}
                    <span className="font-semibold">{Math.abs(production?.throughput.change_percent || 0).toFixed(1)}%</span>
                  </Flex>
                  <p className="text-xs text-gray-500">vs. período anterior</p>
                </div>
              </Flex>
            </div>

            {/* Energy Efficiency */}
            <div className="p-4 bg-slate-50 rounded-lg">
              <Flex justifyContent="between" alignItems="center">
                <div>
                  <p className="text-sm text-gray-600">Eficiência Energética</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatNumber(production?.energy_efficiency.current || 0, 1)} {production?.energy_efficiency.unit || 'kWh/ton'}
                  </p>
                </div>
                <div className="text-right">
                  <Flex alignItems="center" className={`gap-1 ${(production?.energy_efficiency.change_percent || 0) <= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                    {(production?.energy_efficiency.change_percent || 0) <= 0 ? (
                      <ArrowDownRight className="w-5 h-5" />
                    ) : (
                      <ArrowUpRight className="w-5 h-5" />
                    )}
                    <span className="font-semibold">{Math.abs(production?.energy_efficiency.change_percent || 0).toFixed(1)}%</span>
                  </Flex>
                  <p className="text-xs text-gray-500">menor = melhor</p>
                </div>
              </Flex>
            </div>
          </div>
        </Card>

        {/* Energy Consumption Chart */}
        <Card className="bg-white">
          <Flex justifyContent="between" alignItems="center" className="mb-4">
            <div>
              <h3 className="text-lg font-bold text-gray-900">Consumo de Energia</h3>
              <p className="text-gray-600 text-sm">Histórico do período selecionado</p>
            </div>
            <div className="p-2 bg-yellow-100 rounded-lg">
              <Zap className="w-6 h-6 text-yellow-600" />
            </div>
          </Flex>

          {energyChartData.length > 0 ? (
            <>
              <ProfessionalAreaChart
                data={energyChartData}
                xAxisKey="hora"
                dataKey="consumo"
                color="#F59E0B"
                height={192}
              />
              <Grid numItemsSm={3} className="gap-4 mt-4">
                <div className="text-center p-3 bg-slate-50 rounded-lg">
                  <p className="text-xs text-gray-500">Consumo Total</p>
                  <p className="text-lg font-bold text-gray-900">{formatNumber(energy?.period.total_kwh || 0, 0)} kWh</p>
                </div>
                <div className="text-center p-3 bg-slate-50 rounded-lg">
                  <p className="text-xs text-gray-500">Média/Hora</p>
                  <p className="text-lg font-bold text-gray-900">{formatNumber(energy?.period.average_kwh_hour || 0, 0)} kWh</p>
                </div>
                <div className="text-center p-3 bg-slate-50 rounded-lg">
                  <p className="text-xs text-gray-500">Pico Demanda</p>
                  <p className="text-lg font-bold text-gray-900">{formatNumber(energy?.period.peak_demand_kw || 0, 0)} kW</p>
                </div>
              </Grid>
            </>
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-400">
              <p>Sem dados de energia disponíveis</p>
            </div>
          )}
        </Card>
      </Grid>

      {/* Financial Summary */}
      <Card className="bg-white">
        <Flex justifyContent="between" alignItems="center" className="mb-4">
          <div>
            <h3 className="text-lg font-bold text-gray-900">Resumo Financeiro</h3>
            <p className="text-gray-600 text-sm">Impacto econômico da operação otimizada</p>
          </div>
          <div className="p-2 bg-emerald-100 rounded-lg">
            <DollarSign className="w-6 h-6 text-emerald-600" />
          </div>
        </Flex>

        <Grid numItemsSm={2} numItemsLg={4} className="gap-4">
          <div className="text-center p-4 bg-emerald-50 rounded-xl">
            <DollarSign className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
            <p className="text-gray-600 text-sm">Economia Hoje</p>
            <p className="text-2xl font-bold text-emerald-600 mt-1">{formatCurrency(financial?.estimated_savings_today || 0)}</p>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-xl">
            <Clock className="w-8 h-8 text-blue-600 mx-auto mb-2" />
            <p className="text-gray-600 text-sm">Downtime Evitado</p>
            <p className="text-2xl font-bold text-blue-600 mt-1">{formatCurrency(financial?.downtime_cost_avoided || 0)}</p>
          </div>
          <div className="text-center p-4 bg-violet-50 rounded-xl">
            <TrendingUp className="w-8 h-8 text-violet-600 mx-auto mb-2" />
            <p className="text-gray-600 text-sm">Var. Eficiência</p>
            <p className={`text-2xl font-bold mt-1 ${(financial?.efficiency_improvement || 0) >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
              {(financial?.efficiency_improvement || 0) >= 0 ? '+' : ''}{formatNumber(financial?.efficiency_improvement || 0)}%
            </p>
          </div>
          <div className="text-center p-4 bg-amber-50 rounded-xl">
            <Target className="w-8 h-8 text-amber-600 mx-auto mb-2" />
            <p className="text-gray-600 text-sm">Projeção Mensal</p>
            <p className="text-2xl font-bold text-amber-600 mt-1">{formatCurrency(financial?.projected_monthly_savings || 0)}</p>
          </div>
        </Grid>
      </Card>

      {/* Quick Links */}
      <Card className="bg-gradient-to-r from-slate-100 to-blue-50">
        <Flex justifyContent="between" alignItems="center" className="flex-wrap gap-4">
          <div>
            <h3 className="text-lg font-bold text-gray-900">Análises Detalhadas</h3>
            <p className="text-gray-600 text-sm">Acesse relatórios e análises específicas</p>
          </div>
          <Flex className="gap-2 flex-wrap">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => navigate('/quality')}
            >
              Qualidade & Pareto
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => navigate('/maintenance')}
            >
              Manutenção
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => navigate('/analytics')}
            >
              Analytics & ML
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => navigate('/alarms')}
            >
              Alarmes
            </Button>
          </Flex>
        </Flex>
      </Card>

      {/* Error Alert */}
      {error && (
        <Callout title="Erro ao carregar dados" icon={AlertCircle} color="red">
          {error}
        </Callout>
      )}
    </div>
  );
};

export default TremorExecutive;
