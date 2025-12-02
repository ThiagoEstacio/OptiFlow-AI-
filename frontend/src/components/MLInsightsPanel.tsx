/**
 * MLInsightsPanel - Painel de Insights ML Consolidados
 *
 * Consome os 6 modelos ML treinados:
 * 1. Confiabilidade (MTBF/MTTR)
 * 2. Previsão de Energia (LSTM)
 * 3. Eficiência (Gradient Boosting)
 * 4. Detecção de Anomalias (Isolation Forest)
 * 5. Análise de Correlações
 * 6. Otimização de Custos
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Wrench,
  Zap,
  TrendingUp,
  AlertTriangle,
  Link2,
  DollarSign,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Clock,
  Target,
  Activity,
  BarChart3,
  Lightbulb,
  ShieldAlert,
  CheckCircle,
  XCircle,
  Info
} from 'lucide-react';
import { apiClient } from '../api/client';

// ========================================
// Types
// ========================================

interface MLInsightsResponse {
  organization_id: string;
  time_range: string;
  generated_at: string;
  insights: {
    reliability: ReliabilityInsight | null;
    energy_prediction: EnergyInsight | null;
    efficiency: EfficiencyInsight | null;
    anomalies: AnomaliesInsight | null;
    correlations: CorrelationsInsight | null;
    cost_optimization: CostInsight | null;
  };
  summary: {
    total_insights: number;
    total_alerts: number;
    severity: string;
    top_recommendations: string[];
    status: string;
  };
}

interface ReliabilityInsight {
  status: string;
  equipment_statistics?: Array<{
    equipment_id: string;
    n_failures: number;
    mtbf_hours: number | null;
    mttr_hours: number;
    availability: number | null;
    critical: boolean;
  }>;
  critical_equipment?: Array<any>;
  next_maintenances?: Array<{
    equipment_id: string;
    probability_failure_24h: number;
    probability_failure_48h: number;
    probability_failure_7d: number;
    recommended_action: string;
  }>;
  alerts?: string[];
  recommendations?: string[];
}

interface EnergyInsight {
  status: string;
  current_consumption_kwh?: number;
  predicted_24h?: Array<{
    hour_ahead: number;
    timestamp: string;
    predicted_consumption_kwh: number;
    confidence: number;
  }>;
  trend?: string;
  trend_slope_kwh_per_hour?: number;
  mean_consumption_kwh?: number;
  abnormal_consumption?: boolean;
  alerts?: string[];
  recommendations?: string[];
}

interface EfficiencyInsight {
  status: string;
  current_efficiency_kwh_per_ton?: number;
  mean_efficiency_kwh_per_ton?: number;
  efficiency_status?: string;
  low_efficiency_periods?: number;
  correlations?: Record<string, number>;
  worst_hours?: number[];
  best_hours?: number[];
  alerts?: string[];
  recommendations?: string[];
}

interface AnomaliesInsight {
  status: string;
  total_anomalies?: number;
  anomaly_rate?: number;
  recent_anomalies?: number;
  anomaly_patterns?: Record<string, number>;
  equipment_with_most_anomalies?: Record<string, number>;
  alerts?: string[];
  recommendations?: string[];
}

interface CorrelationsInsight {
  status: string;
  strong_correlations?: Array<{
    variable_1: string;
    variable_2: string;
    correlation: number;
    strength: string;
    direction: string;
  }>;
  n_strong_correlations?: number;
  insights?: string[];
  recommendations?: string[];
}

interface CostInsight {
  status: string;
  current_cost_monthly?: number;
  potential_savings_monthly?: number;
  potential_savings_yearly?: number;
  savings_percentage?: number;
  peak_hours?: Record<string, number>;
  optimization_strategy?: string;
  recommendations?: string[];
}

interface MLInsightsPanelProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
  timeRange?: 'last_24h' | 'last_7_days' | 'last_30_days';
}

// ========================================
// Helper Components
// ========================================

const InsightCard: React.FC<{
  title: string;
  icon: React.ReactNode;
  status: string;
  color: string;
  children: React.ReactNode;
  alerts?: string[];
  recommendations?: string[];
  expanded?: boolean;
  onToggle?: () => void;
}> = ({ title, icon, status, color, children, alerts = [], recommendations = [], expanded = true, onToggle }) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'insufficient_data':
        return <Info className="w-4 h-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg border ${alerts.length > 0 ? 'border-orange-300 dark:border-orange-700' : 'border-gray-200 dark:border-gray-700'} overflow-hidden`}>
      <div
        className="p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${color}`}>
              {icon}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">{title}</h3>
              <div className="flex items-center gap-2 mt-1">
                {getStatusIcon()}
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {status === 'success' ? 'Dados disponíveis' : status === 'insufficient_data' ? 'Dados insuficientes' : 'Erro'}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {alerts.length > 0 && (
              <span className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 rounded text-xs font-medium">
                {alerts.length} alerta{alerts.length > 1 ? 's' : ''}
              </span>
            )}
            {expanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
          </div>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 space-y-4">
          {/* Main Content */}
          {status === 'success' ? (
            children
          ) : (
            <div className="text-center py-4 text-gray-500 dark:text-gray-400">
              <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">
                {status === 'insufficient_data'
                  ? 'Dados insuficientes para análise. Aguarde mais dados serem coletados.'
                  : 'Erro ao processar análise ML.'}
              </p>
            </div>
          )}

          {/* Alerts */}
          {alerts.length > 0 && (
            <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
              <p className="text-xs font-semibold text-orange-700 dark:text-orange-400 mb-2 flex items-center gap-1">
                <ShieldAlert className="w-4 h-4" />
                Alertas
              </p>
              <ul className="space-y-1">
                {alerts.map((alert, idx) => (
                  <li key={idx} className="text-sm text-orange-600 dark:text-orange-300">{alert}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {recommendations.length > 0 && (
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <p className="text-xs font-semibold text-blue-700 dark:text-blue-400 mb-2 flex items-center gap-1">
                <Lightbulb className="w-4 h-4" />
                Recomendações
              </p>
              <ul className="space-y-1">
                {recommendations.map((rec, idx) => (
                  <li key={idx} className="text-sm text-blue-600 dark:text-blue-300">{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const StatBox: React.FC<{
  label: string;
  value: string | number;
  subValue?: string;
  color?: string;
}> = ({ label, value, subValue, color = 'text-gray-900 dark:text-white' }) => (
  <div className="text-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
    <p className={`text-xl font-bold ${color}`}>{value}</p>
    <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
    {subValue && <p className="text-xs text-gray-400 mt-1">{subValue}</p>}
  </div>
);

// ========================================
// Main Component
// ========================================

export const MLInsightsPanel: React.FC<MLInsightsPanelProps> = ({
  autoRefresh = false,
  refreshInterval = 300,
  timeRange = 'last_7_days'
}) => {
  const [data, setData] = useState<MLInsightsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({
    reliability: true,
    energy: true,
    efficiency: true,
    anomalies: true,
    correlations: false,
    cost: false
  });

  const fetchInsights = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.get(`/api/v1/ml/insights/all?time_range=${timeRange}`);
      setData(response.data);
      setLastUpdate(new Date());
    } catch (err: any) {
      console.error('Error fetching ML insights:', err);
      setError(err.response?.data?.detail || err.message || 'Erro ao carregar insights ML');
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchInsights();
  }, [fetchInsights]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchInsights, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, fetchInsights]);

  const toggleCard = (card: string) => {
    setExpandedCards(prev => ({ ...prev, [card]: !prev[card] }));
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  };

  if (error && !data) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-6 border border-red-200 dark:border-red-800">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 text-red-500" />
          <div>
            <h3 className="font-semibold text-red-700 dark:text-red-400">Erro ao carregar Insights ML</h3>
            <p className="text-sm text-red-600 dark:text-red-300 mt-1">{error}</p>
          </div>
        </div>
        <button
          onClick={fetchInsights}
          className="mt-4 px-4 py-2 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
        >
          Tentar novamente
        </button>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-600 rounded-lg">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="font-bold text-gray-900 dark:text-white">Insights ML/DS</h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                6 Modelos de Machine Learning
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {data?.summary && (
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  data.summary.severity === 'high' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                  data.summary.severity === 'medium' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                  'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                }`}>
                  {data.summary.total_alerts} alertas
                </span>
              </div>
            )}
            {lastUpdate && (
              <span className="text-xs text-gray-400 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {lastUpdate.toLocaleTimeString('pt-BR')}
              </span>
            )}
            <button
              onClick={fetchInsights}
              disabled={loading}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
              title="Atualizar"
            >
              <RefreshCw className={`w-4 h-4 text-gray-500 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        {data?.summary && (
          <div className="grid grid-cols-4 gap-3 mt-4">
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-center">
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{data.summary.total_insights}</p>
              <p className="text-xs text-blue-500 dark:text-blue-400">Insights Gerados</p>
            </div>
            <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg text-center">
              <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">{data.summary.total_alerts}</p>
              <p className="text-xs text-orange-500 dark:text-orange-400">Alertas</p>
            </div>
            <div className={`p-3 rounded-lg text-center ${
              data.summary.status === 'ok' ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20'
            }`}>
              <p className={`text-2xl font-bold ${
                data.summary.status === 'ok' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
              }`}>
                {data.summary.status === 'ok' ? 'OK' : 'ATENÇÃO'}
              </p>
              <p className={`text-xs ${
                data.summary.status === 'ok' ? 'text-green-500 dark:text-green-400' : 'text-red-500 dark:text-red-400'
              }`}>Status Geral</p>
            </div>
            <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg text-center">
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">6</p>
              <p className="text-xs text-purple-500 dark:text-purple-400">Modelos Ativos</p>
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {loading && !data ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
            <span className="ml-3 text-gray-500">Gerando insights ML...</span>
          </div>
        ) : data ? (
          <>
            {/* 1. Confiabilidade (MTBF/MTTR) */}
            <InsightCard
              title="Confiabilidade - MTBF/MTTR"
              icon={<Wrench className="w-5 h-5 text-white" />}
              status={data.insights.reliability?.status || 'error'}
              color="bg-blue-500"
              alerts={data.insights.reliability?.alerts || []}
              recommendations={data.insights.reliability?.recommendations || []}
              expanded={expandedCards.reliability}
              onToggle={() => toggleCard('reliability')}
            >
              {data.insights.reliability?.equipment_statistics && (
                <div className="space-y-3">
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Estatísticas por Equipamento ({data.insights.reliability.equipment_statistics.length})
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {data.insights.reliability.equipment_statistics.slice(0, 4).map((eq, idx) => (
                      <div key={idx} className={`p-3 rounded-lg border ${eq.critical ? 'border-red-300 bg-red-50 dark:border-red-700 dark:bg-red-900/20' : 'border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-700/50'}`}>
                        <p className="text-xs font-medium text-gray-600 dark:text-gray-400 truncate">{eq.equipment_id}</p>
                        <p className="text-lg font-bold text-gray-900 dark:text-white">
                          {eq.mtbf_hours?.toFixed(0) || 'N/A'}h
                        </p>
                        <p className="text-xs text-gray-500">MTBF</p>
                        {eq.critical && (
                          <span className="text-xs text-red-600 dark:text-red-400 font-medium">Crítico</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </InsightCard>

            {/* 2. Previsão de Energia */}
            <InsightCard
              title="Previsão de Energia - LSTM"
              icon={<Zap className="w-5 h-5 text-white" />}
              status={data.insights.energy_prediction?.status || 'error'}
              color="bg-yellow-500"
              alerts={data.insights.energy_prediction?.alerts || []}
              recommendations={data.insights.energy_prediction?.recommendations || []}
              expanded={expandedCards.energy}
              onToggle={() => toggleCard('energy')}
            >
              {data.insights.energy_prediction?.status === 'success' && (
                <div className="grid grid-cols-3 gap-3">
                  <StatBox
                    label="Consumo Atual"
                    value={`${data.insights.energy_prediction.current_consumption_kwh?.toFixed(0) || 0}`}
                    subValue="kWh"
                    color={data.insights.energy_prediction.abnormal_consumption ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white'}
                  />
                  <StatBox
                    label="Média"
                    value={`${data.insights.energy_prediction.mean_consumption_kwh?.toFixed(0) || 0}`}
                    subValue="kWh"
                  />
                  <StatBox
                    label="Tendência"
                    value={data.insights.energy_prediction.trend === 'increasing' ? '↑ Alta' : '↓ Baixa'}
                    subValue={`${data.insights.energy_prediction.trend_slope_kwh_per_hour?.toFixed(2) || 0} kWh/h`}
                    color={data.insights.energy_prediction.trend === 'increasing' ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}
                  />
                </div>
              )}
            </InsightCard>

            {/* 3. Eficiência */}
            <InsightCard
              title="Eficiência - Gradient Boosting"
              icon={<TrendingUp className="w-5 h-5 text-white" />}
              status={data.insights.efficiency?.status || 'error'}
              color="bg-green-500"
              alerts={data.insights.efficiency?.alerts || []}
              recommendations={data.insights.efficiency?.recommendations || []}
              expanded={expandedCards.efficiency}
              onToggle={() => toggleCard('efficiency')}
            >
              {data.insights.efficiency?.status === 'success' && (
                <div className="space-y-3">
                  <div className="grid grid-cols-3 gap-3">
                    <StatBox
                      label="Eficiência Atual"
                      value={`${data.insights.efficiency.current_efficiency_kwh_per_ton?.toFixed(2) || 0}`}
                      subValue="kWh/ton"
                      color={data.insights.efficiency.efficiency_status === 'poor' ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}
                    />
                    <StatBox
                      label="Média"
                      value={`${data.insights.efficiency.mean_efficiency_kwh_per_ton?.toFixed(2) || 0}`}
                      subValue="kWh/ton"
                    />
                    <StatBox
                      label="Períodos Baixos"
                      value={data.insights.efficiency.low_efficiency_periods || 0}
                      subValue="ocorrências"
                    />
                  </div>
                  {data.insights.efficiency.worst_hours && data.insights.efficiency.worst_hours.length > 0 && (
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Piores horários: {data.insights.efficiency.worst_hours.join('h, ')}h
                    </p>
                  )}
                </div>
              )}
            </InsightCard>

            {/* 4. Anomalias */}
            <InsightCard
              title="Detecção de Anomalias - Isolation Forest"
              icon={<AlertTriangle className="w-5 h-5 text-white" />}
              status={data.insights.anomalies?.status || 'error'}
              color="bg-red-500"
              alerts={data.insights.anomalies?.alerts || []}
              recommendations={data.insights.anomalies?.recommendations || []}
              expanded={expandedCards.anomalies}
              onToggle={() => toggleCard('anomalies')}
            >
              {data.insights.anomalies?.status === 'success' && (
                <div className="grid grid-cols-3 gap-3">
                  <StatBox
                    label="Total Anomalias"
                    value={data.insights.anomalies.total_anomalies || 0}
                    color={data.insights.anomalies.total_anomalies && data.insights.anomalies.total_anomalies > 10 ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white'}
                  />
                  <StatBox
                    label="Taxa"
                    value={`${((data.insights.anomalies.anomaly_rate || 0) * 100).toFixed(1)}%`}
                  />
                  <StatBox
                    label="Últimas 24h"
                    value={data.insights.anomalies.recent_anomalies || 0}
                    color={data.insights.anomalies.recent_anomalies && data.insights.anomalies.recent_anomalies > 0 ? 'text-orange-600 dark:text-orange-400' : 'text-green-600 dark:text-green-400'}
                  />
                </div>
              )}
            </InsightCard>

            {/* 5. Correlações */}
            <InsightCard
              title="Análise de Correlações"
              icon={<Link2 className="w-5 h-5 text-white" />}
              status={data.insights.correlations?.status || 'error'}
              color="bg-purple-500"
              alerts={[]}
              recommendations={data.insights.correlations?.recommendations || []}
              expanded={expandedCards.correlations}
              onToggle={() => toggleCard('correlations')}
            >
              {data.insights.correlations?.status === 'success' && data.insights.correlations.strong_correlations && (
                <div className="space-y-2">
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {data.insights.correlations.n_strong_correlations || 0} correlações fortes encontradas
                  </p>
                  {data.insights.correlations.strong_correlations.slice(0, 3).map((corr, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded">
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        {corr.variable_1} ↔ {corr.variable_2}
                      </span>
                      <span className={`text-sm font-bold ${
                        corr.direction === 'positive' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                      }`}>
                        r = {corr.correlation.toFixed(3)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </InsightCard>

            {/* 6. Otimização de Custos */}
            <InsightCard
              title="Otimização de Custos"
              icon={<DollarSign className="w-5 h-5 text-white" />}
              status={data.insights.cost_optimization?.status || 'error'}
              color="bg-emerald-500"
              alerts={[]}
              recommendations={data.insights.cost_optimization?.recommendations || []}
              expanded={expandedCards.cost}
              onToggle={() => toggleCard('cost')}
            >
              {data.insights.cost_optimization?.status === 'success' && (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <StatBox
                      label="Custo Mensal Atual"
                      value={formatCurrency(data.insights.cost_optimization.current_cost_monthly || 0)}
                    />
                    <StatBox
                      label="Economia Potencial"
                      value={formatCurrency(data.insights.cost_optimization.potential_savings_monthly || 0)}
                      subValue={`${data.insights.cost_optimization.savings_percentage?.toFixed(1)}%`}
                      color="text-green-600 dark:text-green-400"
                    />
                  </div>
                  {data.insights.cost_optimization.optimization_strategy && (
                    <div className="p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
                      <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 mb-1">Estratégia</p>
                      <p className="text-sm text-emerald-600 dark:text-emerald-300">
                        {data.insights.cost_optimization.optimization_strategy}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </InsightCard>

            {/* Top Recommendations */}
            {data.summary.top_recommendations && data.summary.top_recommendations.length > 0 && (
              <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <p className="text-sm font-semibold text-blue-700 dark:text-blue-400 mb-3 flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  Top Recomendações
                </p>
                <ul className="space-y-2">
                  {data.summary.top_recommendations.slice(0, 5).map((rec, idx) => (
                    <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2">
                      <span className="text-blue-500 font-bold">{idx + 1}.</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : null}
      </div>

      {/* Footer */}
      <div className="px-4 pb-3 flex items-center justify-between text-xs text-gray-400 border-t border-gray-200 dark:border-gray-700 pt-3">
        <span>Período: {timeRange === 'last_24h' ? 'Últimas 24h' : timeRange === 'last_7_days' ? 'Últimos 7 dias' : 'Últimos 30 dias'}</span>
        {autoRefresh && (
          <span className="flex items-center gap-1">
            <span className="animate-pulse w-2 h-2 bg-green-500 rounded-full"></span>
            Atualização automática a cada {refreshInterval}s
          </span>
        )}
      </div>
    </div>
  );
};

export default MLInsightsPanel;
