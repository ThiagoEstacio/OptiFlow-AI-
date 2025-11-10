import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, BarChart, Bar } from 'recharts';
import { apiClient } from '@/api/client';
import { Loader2, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Zap, DollarSign, Activity } from 'lucide-react';

interface MLInsights {
  generated_at: string;
  time_range: string;
  status: string;
  summary: {
    total_insights: number;
    total_alerts: number;
    severity: string;
    status: string;
    top_recommendations: string[];
  };
  insights: {
    energy_prediction: any;
    efficiency: any;
    reliability: any;
    anomalies: any;
    correlations: any;
    cost_optimization: any;
  };
}

export const MLInsightsDashboard: React.FC = () => {
  const [insights, setInsights] = useState<MLInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<'last_24h' | 'last_7_days' | 'last_30_days'>('last_7_days');

  const fetchInsights = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get('/api/v1/ml/insights/all', {
        params: { time_range: timeRange }
      });
      setInsights(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao carregar insights ML');
      console.error('Erro ao carregar insights:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
    // Atualizar a cada 5 minutos
    const interval = setInterval(fetchInsights, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [timeRange]);

  if (loading && !insights) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-gray-600">Carregando insights ML/DS...</p>
          <p className="text-sm text-gray-400 mt-2">Processando {timeRange === 'last_7_days' ? '7 dias' : timeRange === 'last_24h' ? '24 horas' : '30 dias'} de dados</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Alert className="border-red-500 bg-red-50">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <AlertDescription className="ml-2 text-red-700">
            {error}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!insights) {
    return null;
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">ML Insights Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Análise preditiva e insights de Machine Learning
          </p>
        </div>
        <div className="flex gap-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="last_24h">Últimas 24h</option>
            <option value="last_7_days">Últimos 7 dias</option>
            <option value="last_30_days">Últimos 30 dias</option>
          </select>
          <button
            onClick={fetchInsights}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Activity className="w-4 h-4" />}
            Atualizar
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SummaryCard
          title="Total de Insights"
          value={insights.summary.total_insights}
          icon={<TrendingUp className="w-6 h-6 text-blue-500" />}
          color="blue"
        />
        <SummaryCard
          title="Alertas Ativos"
          value={insights.summary.total_alerts}
          icon={<AlertTriangle className="w-6 h-6 text-orange-500" />}
          color="orange"
        />
        <div className={`p-4 rounded-lg border-2 ${getSeverityColor(insights.summary.severity)}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium opacity-80">Severidade</p>
              <p className="text-2xl font-bold capitalize mt-1">{insights.summary.severity}</p>
            </div>
            <CheckCircle className="w-6 h-6" />
          </div>
        </div>
        <div className="p-4 rounded-lg border-2 border-green-200 bg-green-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-700">Status Geral</p>
              <p className="text-2xl font-bold text-green-600 capitalize mt-1">{insights.summary.status}</p>
            </div>
            <CheckCircle className="w-6 h-6 text-green-500" />
          </div>
        </div>
      </div>

      {/* Energy Prediction */}
      {insights.insights.energy_prediction && insights.insights.energy_prediction.status === 'success' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-500" />
              Previsão de Energia (LSTM)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
              <MetricCard
                title="Consumo Atual"
                value={`${insights.insights.energy_prediction.current_consumption_kwh?.toFixed(1) || 0} kWh`}
                subtitle="Consumo energético"
              />
              <MetricCard
                title="R² Score"
                value={insights.insights.energy_prediction.r2_score?.toFixed(4) || 'N/A'}
                subtitle={`MAPE: ${insights.insights.energy_prediction.mape?.toFixed(2) || 0}%`}
              />
              <MetricCard
                title="Tendência"
                value={insights.insights.energy_prediction.trend || 'stable'}
                subtitle="Próximas 24h"
                icon={insights.insights.energy_prediction.trend === 'increasing' ?
                  <TrendingUp className="w-5 h-5 text-red-500" /> :
                  <TrendingDown className="w-5 h-5 text-green-500" />
                }
              />
            </div>

            {insights.insights.energy_prediction.predicted_24h && insights.insights.energy_prediction.predicted_24h.length > 0 && (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={insights.insights.energy_prediction.predicted_24h}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="hour"
                      label={{ value: 'Hora', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis
                      label={{ value: 'Consumo (kWh)', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="predicted_kwh"
                      stroke="#3B82F6"
                      strokeWidth={2}
                      name="Previsão (kWh)"
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Efficiency and Reliability */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Efficiency */}
        {insights.insights.efficiency && insights.insights.efficiency.status === 'success' && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-green-500" />
                Análise de Eficiência
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Eficiência Atual</span>
                  <span className="text-2xl font-bold">
                    {insights.insights.efficiency.current_efficiency_kwh_per_ton?.toFixed(2) || 0} kWh/ton
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Eficiência Média</span>
                  <span className="text-lg font-semibold text-gray-700">
                    {insights.insights.efficiency.mean_efficiency_kwh_per_ton?.toFixed(2) || 0} kWh/ton
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Status</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    insights.insights.efficiency.efficiency_status === 'good' ? 'bg-green-100 text-green-700' :
                    insights.insights.efficiency.efficiency_status === 'normal' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {insights.insights.efficiency.efficiency_status || 'unknown'}
                  </span>
                </div>
                <div className="pt-4 border-t">
                  <p className="text-sm text-gray-600 mb-2">Modelo</p>
                  <p className="font-medium">{insights.insights.efficiency.model_type || 'N/A'}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    R²: {insights.insights.efficiency.r2_score?.toFixed(4) || 'N/A'} |
                    MAPE: {insights.insights.efficiency.mape?.toFixed(2) || 0}%
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Reliability (MTBF/MTTR) */}
        {insights.insights.reliability && insights.insights.reliability.status === 'success' && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-blue-500" />
                Confiabilidade (MTBF/MTTR)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">MTBF Médio</span>
                  <span className="text-2xl font-bold text-blue-600">
                    {insights.insights.reliability.mtbf_mean?.toFixed(1) || 0}h
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">MTTR Médio</span>
                  <span className="text-lg font-semibold text-orange-600">
                    {insights.insights.reliability.mttr_mean?.toFixed(1) || 0}h
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Disponibilidade</span>
                  <span className="text-xl font-bold text-green-600">
                    {insights.insights.reliability.availability_percent?.toFixed(2) || 0}%
                  </span>
                </div>
                <div className="pt-4 border-t">
                  <p className="text-sm text-gray-600 mb-2">Equipamentos Críticos</p>
                  <p className="text-3xl font-bold text-red-600">
                    {insights.insights.reliability.critical_equipment?.length || 0}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Requerem atenção imediata</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Anomalies and Cost Optimization */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Anomalies */}
        {insights.insights.anomalies && insights.insights.anomalies.status === 'success' && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-500" />
                Detecção de Anomalias
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-center p-6 bg-orange-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Anomalias Detectadas (24h)</p>
                  <p className="text-5xl font-bold text-orange-600">
                    {insights.insights.anomalies.recent_anomalies || 0}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    de {insights.insights.anomalies.total_anomalies || 0} total
                  </p>
                </div>
                <div className="flex justify-between items-center pt-4 border-t">
                  <span className="text-sm text-gray-600">Taxa de Anomalia</span>
                  <span className="text-lg font-bold">
                    {((insights.insights.anomalies.anomaly_rate || 0) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Cost Optimization */}
        {insights.insights.cost_optimization && insights.insights.cost_optimization.status === 'success' && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-green-500" />
                Otimização de Custos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Custo Atual (Mensal)</span>
                  <span className="text-xl font-bold text-gray-700">
                    R$ {insights.insights.cost_optimization.current_cost_monthly?.toFixed(2).replace('.', ',') || '0,00'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Custo Otimizado</span>
                  <span className="text-xl font-bold text-blue-600">
                    R$ {insights.insights.cost_optimization.optimized_cost_monthly?.toFixed(2).replace('.', ',') || '0,00'}
                  </span>
                </div>
                <div className="p-4 bg-green-50 rounded-lg border-2 border-green-200">
                  <div className="text-center">
                    <p className="text-sm text-gray-600 mb-1">Economia Potencial (Mensal)</p>
                    <p className="text-3xl font-bold text-green-600">
                      R$ {insights.insights.cost_optimization.potential_savings_monthly?.toFixed(2).replace('.', ',') || '0,00'}
                    </p>
                    <p className="text-sm text-green-700 font-medium mt-1">
                      {insights.insights.cost_optimization.savings_percentage?.toFixed(1) || 0}% de economia
                    </p>
                  </div>
                </div>
                <div className="pt-2">
                  <p className="text-xs text-gray-600">Economia Anual Estimada</p>
                  <p className="text-2xl font-bold text-green-600">
                    R$ {insights.insights.cost_optimization.potential_savings_yearly?.toFixed(2).replace('.', ',') || '0,00'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Recommendations */}
      {insights.summary.top_recommendations && insights.summary.top_recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Principais Recomendações</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {insights.summary.top_recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm font-bold mt-0.5">
                    {idx + 1}
                  </div>
                  <span className="text-gray-700 flex-1">{rec}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Footer Info */}
      <div className="text-center text-sm text-gray-500 py-4">
        <p>Última atualização: {new Date(insights.generated_at).toLocaleString('pt-BR')}</p>
        <p className="mt-1">Período de análise: {
          timeRange === 'last_24h' ? 'Últimas 24 horas' :
          timeRange === 'last_7_days' ? 'Últimos 7 dias' :
          'Últimos 30 dias'
        }</p>
      </div>
    </div>
  );
};

// Component helpers
const SummaryCard: React.FC<{
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
}> = ({ title, value, icon, color }) => (
  <div className={`p-4 rounded-lg border-2 border-${color}-200 bg-${color}-50`}>
    <div className="flex items-center justify-between">
      <div>
        <p className={`text-sm font-medium text-${color}-700`}>{title}</p>
        <p className={`text-2xl font-bold text-${color}-600 mt-1`}>{value}</p>
      </div>
      {icon}
    </div>
  </div>
);

const MetricCard: React.FC<{
  title: string;
  value: string;
  subtitle?: string;
  icon?: React.ReactNode;
}> = ({ title, value, subtitle, icon }) => (
  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
    <div className="flex items-center justify-between mb-2">
      <p className="text-sm text-gray-600">{title}</p>
      {icon}
    </div>
    <p className="text-2xl font-bold text-gray-900">{value}</p>
    {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
  </div>
);

export default MLInsightsDashboard;
