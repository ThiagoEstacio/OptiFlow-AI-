/**
 * Health Trends & Analytics Page
 *
 * Comprehensive trend analysis, predictions, and insights for asset health
 */

import React, { useState, useEffect } from 'react';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  BarChart3,
  Calendar,
  RefreshCw,
  Download,
  CheckCircle,
  AlertTriangle,
} from 'lucide-react';
import { useAssets } from '../contexts/AssetContext';
import axios from 'axios';
import { MultiAxisChart } from '../components/Visualizations/MultiAxisChart';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface HealthTrendPoint {
  snapshot_time: string;
  health_score: number;
  health_status: string;
  issues_count: number;
  warnings_count: number;
  trend_direction?: string;
}

interface Statistics {
  period_days: number;
  data_points: number;
  mean_score: number;
  median_score: number;
  min_score: number;
  max_score: number;
  stddev: number;
  current_score: number;
  overall_trend: string;
  volatility: number;
}

interface Prediction {
  current_score: number;
  predicted_score: number;
  forecast_days: number;
  trend_slope: number;
  confidence: string;
  maintenance_needed: boolean;
  urgency: string;
  recommendation: string;
}

interface Anomaly {
  snapshot_time: string;
  health_score: number;
  deviation: number;
  type: string;
}

export const HealthTrendsPage: React.FC = () => {
  const { assets, selectedAsset, selectAsset } = useAssets();
  const selectedAssetId = selectedAsset?.id;

  // State
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<number>(7); // days
  const [trendData, setTrendData] = useState<HealthTrendPoint[]>([]);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);

  // Get selected asset or first asset with attributes
  const currentAssetId = selectedAssetId || assets.find(a => (a.attributes_count || 0) > 0)?.id;

  // Fetch all analytics data
  const fetchAnalytics = async () => {
    if (!currentAssetId) return;

    setLoading(true);
    setError(null);

    try {
      // Fetch trend data
      const trendResponse = await axios.get(
        `${API_BASE_URL}/assets/${currentAssetId}/health/trend`,
        { params: { limit: 200 } }
      );
      setTrendData(trendResponse.data.trend || []);

      // Fetch statistics
      const statsResponse = await axios.get(
        `${API_BASE_URL}/assets/${currentAssetId}/health/statistics`,
        { params: { days: period } }
      );
      setStatistics(statsResponse.data.statistics || null);

      // Fetch prediction
      const predictionResponse = await axios.get(
        `${API_BASE_URL}/assets/${currentAssetId}/health/predict`,
        { params: { days_history: period, forecast_days: 7 } }
      );
      setPrediction(predictionResponse.data.prediction || null);

      // Fetch anomalies
      const anomaliesResponse = await axios.get(
        `${API_BASE_URL}/assets/${currentAssetId}/health/anomalies`,
        { params: { days: period, sensitivity: 2.0 } }
      );
      setAnomalies(anomaliesResponse.data.anomalies || []);

    } catch (err: any) {
      console.error('Error fetching analytics:', err);
      setError(err.message || 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  // Fetch data on mount and when asset or period changes
  useEffect(() => {
    fetchAnalytics();
  }, [currentAssetId, period]);

  // Auto-refresh every 2 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      if (currentAssetId) {
        fetchAnalytics();
      }
    }, 120000);

    return () => clearInterval(interval);
  }, [currentAssetId, period]);

  // Get current asset
  const currentAsset = assets.find(a => a.id === currentAssetId);

  // Prepare chart data for MultiAxisChart
  const chartTimestamps = trendData.map(point => new Date(point.snapshot_time));
  const chartSeries = [
    {
      name: 'Health Score',
      data: trendData.map(point => point.health_score),
      yAxis: 'left' as const,
      unit: 'Score',
      color: '#3B82F6',
    },
    {
      name: 'Issues',
      data: trendData.map(point => point.issues_count),
      yAxis: 'right' as const,
      unit: 'Count',
      color: '#EF4444',
    },
    {
      name: 'Warnings',
      data: trendData.map(point => point.warnings_count),
      yAxis: 'right' as const,
      unit: 'Count',
      color: '#F59E0B',
    },
  ];

  // Trend icon
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />;
      case 'degrading':
        return <TrendingDown className="w-5 h-5 text-red-600 dark:text-red-400" />;
      default:
        return <Activity className="w-5 h-5 text-gray-600 dark:text-gray-400" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <BarChart3 className="w-8 h-8 text-blue-600 dark:text-blue-400" />
              Health Trends & Analytics
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Análise de tendências, previsões e insights preditivos
            </p>
          </div>

          <button
            onClick={fetchAnalytics}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </button>
        </div>
      </div>

      {/* Asset and Period Selector */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Asset Selector */}
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Asset
            </label>
            <select
              value={currentAssetId || ''}
              onChange={(e) => selectAsset(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="">Selecione um asset...</option>
              {assets
                .filter(a => (a.attributes_count || 0) > 0)
                .map(asset => (
                  <option key={asset.id} value={asset.id}>
                    {asset.name} ({asset.asset_type})
                  </option>
                ))}
            </select>
          </div>

          {/* Period Selector */}
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Período de Análise
            </label>
            <div className="flex gap-2">
              {[7, 30, 90].map(days => (
                <button
                  key={days}
                  onClick={() => setPeriod(days)}
                  className={`flex-1 px-4 py-2 rounded-lg border-2 transition-all ${
                    period === days
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-blue-400'
                  }`}
                >
                  <Calendar className="w-4 h-4 inline mr-1" />
                  {days} dias
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {loading && !trendData.length ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Carregando dados de tendência...</p>
        </div>
      ) : error ? (
        <div className="text-center py-12 text-red-600 dark:text-red-400">
          <AlertCircle className="w-12 h-12 mx-auto mb-4" />
          <p className="font-medium">Erro ao carregar dados</p>
          <p className="text-sm mt-2">{error}</p>
        </div>
      ) : !currentAssetId ? (
        <div className="text-center py-12 text-gray-600 dark:text-gray-400">
          <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p className="font-medium">Selecione um asset para análise</p>
        </div>
      ) : trendData.length === 0 ? (
        <div className="text-center py-12 text-gray-600 dark:text-gray-400">
          <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p className="font-medium">Sem dados históricos disponíveis</p>
          <p className="text-sm mt-2">O sistema começará a coletar dados automaticamente</p>
        </div>
      ) : (
        <>
          {/* Statistics Overview */}
          {statistics && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {/* Current Score */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Score Atual
                  </p>
                  {getTrendIcon(statistics.overall_trend)}
                </div>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {statistics.current_score.toFixed(1)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 capitalize">
                  Tendência: {statistics.overall_trend}
                </p>
              </div>

              {/* Mean Score */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Média ({period}d)
                  </p>
                  <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {statistics.mean_score.toFixed(1)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Mediana: {statistics.median_score.toFixed(1)}
                </p>
              </div>

              {/* Range */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Amplitude
                  </p>
                  <BarChart3 className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                </div>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {(statistics.max_score - statistics.min_score).toFixed(1)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {statistics.min_score.toFixed(1)} - {statistics.max_score.toFixed(1)}
                </p>
              </div>

              {/* Volatility */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Volatilidade
                  </p>
                  <Activity className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                </div>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {statistics.volatility.toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Desvio: ±{statistics.stddev.toFixed(1)}
                </p>
              </div>
            </div>
          )}

          {/* Trend Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Tendência de Health Score
            </h2>
            {chartTimestamps.length > 0 ? (
              <div style={{ height: '400px' }}>
                <MultiAxisChart
                  timestamps={chartTimestamps}
                  series={chartSeries}
                  height={400}
                  leftAxisTitle="Health Score"
                  rightAxisTitle="Count"
                  showLegend={true}
                  showGrid={true}
                />
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                Sem dados para exibir
              </p>
            )}
          </div>

          {/* Prediction and Anomalies */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Prediction */}
            {prediction && (
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Previsão de Manutenção
                </h2>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Score Previsto (7d):</span>
                    <span className="text-2xl font-bold text-gray-900 dark:text-white">
                      {prediction.predicted_score.toFixed(1)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Confiança:</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      prediction.confidence === 'high'
                        ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                        : prediction.confidence === 'medium'
                        ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
                        : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                    }`}>
                      {prediction.confidence.toUpperCase()}
                    </span>
                  </div>

                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    {prediction.maintenance_needed ? (
                      <div className={`flex items-start gap-3 p-4 rounded-lg ${
                        prediction.urgency === 'high'
                          ? 'bg-red-50 dark:bg-red-900/20'
                          : prediction.urgency === 'medium'
                          ? 'bg-orange-50 dark:bg-orange-900/20'
                          : 'bg-yellow-50 dark:bg-yellow-900/20'
                      }`}>
                        <AlertTriangle className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                          prediction.urgency === 'high'
                            ? 'text-red-600 dark:text-red-400'
                            : prediction.urgency === 'medium'
                            ? 'text-orange-600 dark:text-orange-400'
                            : 'text-yellow-600 dark:text-yellow-400'
                        }`} />
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            Manutenção Necessária ({prediction.urgency.toUpperCase()})
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {prediction.recommendation}
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-start gap-3 p-4 rounded-lg bg-green-50 dark:bg-green-900/20">
                        <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-green-600 dark:text-green-400" />
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            Operação Normal
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {prediction.recommendation}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Anomalies */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                Anomalias Detectadas
              </h2>

              {anomalies.length > 0 ? (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {anomalies.slice(0, 5).map((anomaly, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {new Date(anomaly.snapshot_time).toLocaleString('pt-BR')}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          anomaly.type === 'low'
                            ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                            : 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                        }`}>
                          {anomaly.type === 'low' ? 'Baixo' : 'Alto'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">
                          Score: {anomaly.health_score.toFixed(1)}
                        </span>
                        <span className="text-gray-600 dark:text-gray-400">
                          Desvio: {anomaly.deviation.toFixed(2)}σ
                        </span>
                      </div>
                    </div>
                  ))}
                  {anomalies.length > 5 && (
                    <p className="text-sm text-gray-500 dark:text-gray-400 text-center pt-2">
                      +{anomalies.length - 5} anomalias adicionais
                    </p>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <CheckCircle className="w-12 h-12 mx-auto mb-2 text-green-500 dark:text-green-400 opacity-50" />
                  <p className="text-gray-600 dark:text-gray-400">
                    Nenhuma anomalia detectada
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    Padrão de saúde estável
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Data Info */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>💡 Insights:</strong> Os dados são coletados automaticamente a cada 60 segundos.
              Análise baseada em {statistics?.data_points || 0} pontos de dados dos últimos {period} dias.
              Atualizações automáticas a cada 2 minutos.
            </p>
          </div>
        </>
      )}
    </div>
  );
};

export default HealthTrendsPage;
