/**
 * Health Trends Drawer Component
 *
 * Displays detailed health trends for a specific asset
 * Used in the Asset Health Hub drawer
 */

import React, { useState, useEffect } from 'react';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  RefreshCw,
  Calendar,
  CheckCircle,
  AlertTriangle,
  BarChart3,
} from 'lucide-react';
import { useAssets } from '../contexts/AssetContext';
import axios from 'axios';
import { MultiAxisChart } from './Visualizations/MultiAxisChart';

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

interface HealthTrendsDrawerProps {
  assetId: string;
}

export const HealthTrendsDrawer: React.FC<HealthTrendsDrawerProps> = ({ assetId }) => {
  const { assets } = useAssets();

  // State
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<number>(7);
  const [trendData, setTrendData] = useState<HealthTrendPoint[]>([]);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);

  const currentAsset = assets.find(a => a.id === assetId);

  // Fetch analytics data
  const fetchAnalytics = async () => {
    if (!assetId) return;

    setLoading(true);
    setError(null);

    try {
      const [trendRes, statsRes, predictionRes, anomaliesRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/assets/${assetId}/health/trend`, { params: { limit: 200 } }),
        axios.get(`${API_BASE_URL}/assets/${assetId}/health/statistics`, { params: { days: period } }),
        axios.get(`${API_BASE_URL}/assets/${assetId}/health/predict`, {
          params: { days_history: period, forecast_days: 7 }
        }),
        axios.get(`${API_BASE_URL}/assets/${assetId}/health/anomalies`, {
          params: { days: period, sensitivity: 2.0 }
        }),
      ]);

      setTrendData(trendRes.data.trend || []);
      setStatistics(statsRes.data.statistics || null);
      setPrediction(predictionRes.data.prediction || null);
      setAnomalies(anomaliesRes.data.anomalies || []);
    } catch (err: any) {
      console.error('Error fetching analytics:', err);
      setError(err.message || 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [assetId, period]);

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

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="w-4 h-4 text-green-600 dark:text-green-400" />;
      case 'degrading':
        return <TrendingDown className="w-4 h-4 text-red-600 dark:text-red-400" />;
      default:
        return <Activity className="w-4 h-4 text-gray-600 dark:text-gray-400" />;
    }
  };

  if (loading && !trendData.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Carregando análise...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center py-8 text-red-600 dark:text-red-400">
          <AlertCircle className="w-12 h-12 mx-auto mb-4" />
          <p className="font-medium">Erro ao carregar dados</p>
          <p className="text-sm mt-2">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Asset Info */}
      {currentAsset && (
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 dark:text-white">{currentAsset.name}</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 capitalize">{currentAsset.asset_type}</p>
        </div>
      )}

      {/* Period Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Período de Análise
        </label>
        <div className="flex gap-2">
          {[7, 30, 90].map(days => (
            <button
              key={days}
              onClick={() => setPeriod(days)}
              className={`flex-1 px-3 py-2 rounded-lg border-2 transition-all text-sm ${
                period === days
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-blue-400'
              }`}
            >
              <Calendar className="w-3 h-3 inline mr-1" />
              {days}d
            </button>
          ))}
        </div>
      </div>

      {/* Statistics Cards */}
      {statistics && (
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Score Atual</p>
              {getTrendIcon(statistics.overall_trend)}
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {statistics.current_score.toFixed(1)}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">
              {statistics.overall_trend}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Média</p>
              <Activity className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {statistics.mean_score.toFixed(1)}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              ±{statistics.stddev.toFixed(1)}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Amplitude</p>
              <BarChart3 className="w-4 h-4 text-purple-600 dark:text-purple-400" />
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {(statistics.max_score - statistics.min_score).toFixed(1)}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {statistics.min_score.toFixed(1)} - {statistics.max_score.toFixed(1)}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Volatilidade</p>
              <Activity className="w-4 h-4 text-orange-600 dark:text-orange-400" />
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {statistics.volatility.toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {statistics.data_points} pontos
            </p>
          </div>
        </div>
      )}

      {/* Trend Chart */}
      {chartTimestamps.length > 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
            Tendência de Health Score
          </h3>
          <div style={{ height: '250px' }}>
            <MultiAxisChart
              timestamps={chartTimestamps}
              series={chartSeries}
              height={250}
              leftAxisTitle="Health Score"
              rightAxisTitle="Count"
              showLegend={true}
              showGrid={true}
            />
          </div>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-8 border border-gray-200 dark:border-gray-700 text-center">
          <BarChart3 className="w-12 h-12 mx-auto mb-2 text-gray-400 opacity-50" />
          <p className="text-gray-600 dark:text-gray-400">Sem dados históricos</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Aguarde coleta automática
          </p>
        </div>
      )}

      {/* Prediction */}
      {prediction && (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Previsão (7 dias)
          </h3>

          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Score Previsto:</span>
              <span className="font-bold text-gray-900 dark:text-white">
                {prediction.predicted_score.toFixed(1)}
              </span>
            </div>

            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Confiança:</span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                prediction.confidence === 'high'
                  ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                  : prediction.confidence === 'medium'
                  ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
                  : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
              }`}>
                {prediction.confidence.toUpperCase()}
              </span>
            </div>

            {prediction.maintenance_needed ? (
              <div className={`p-3 rounded-lg text-sm ${
                prediction.urgency === 'high'
                  ? 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200'
                  : prediction.urgency === 'medium'
                  ? 'bg-orange-50 dark:bg-orange-900/20 text-orange-800 dark:text-orange-200'
                  : 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-200'
              }`}>
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium">Manutenção {prediction.urgency.toUpperCase()}</p>
                    <p className="text-xs mt-1">{prediction.recommendation}</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-3 rounded-lg text-sm bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200">
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium">Operação Normal</p>
                    <p className="text-xs mt-1">{prediction.recommendation}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Anomalies */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          Anomalias ({anomalies.length})
        </h3>

        {anomalies.length > 0 ? (
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {anomalies.slice(0, 3).map((anomaly, idx) => (
              <div
                key={idx}
                className="p-2 rounded bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-sm"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-gray-600 dark:text-gray-400">
                    {new Date(anomaly.snapshot_time).toLocaleDateString('pt-BR')}
                  </span>
                  <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                    anomaly.type === 'low'
                      ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                      : 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                  }`}>
                    {anomaly.type === 'low' ? 'Baixo' : 'Alto'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-600 dark:text-gray-400">
                    Score: {anomaly.health_score.toFixed(1)}
                  </span>
                  <span className="text-gray-600 dark:text-gray-400">
                    {anomaly.deviation.toFixed(2)}σ
                  </span>
                </div>
              </div>
            ))}
            {anomalies.length > 3 && (
              <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                +{anomalies.length - 3} anomalias
              </p>
            )}
          </div>
        ) : (
          <div className="text-center py-4">
            <CheckCircle className="w-8 h-8 mx-auto mb-1 text-green-500 opacity-50" />
            <p className="text-xs text-gray-600 dark:text-gray-400">Nenhuma anomalia</p>
          </div>
        )}
      </div>

      {/* Refresh Button */}
      <button
        onClick={fetchAnalytics}
        disabled={loading}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
      >
        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        Atualizar Dados
      </button>
    </div>
  );
};
