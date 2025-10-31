/**
 * Página de Insights de IA
 *
 * Dashboard de insights em tempo real com IA:
 * - Detecção de anomalias
 * - Feed automatizado de insights
 * - Scores de saúde do sistema
 * - Análises preditivas com ChatGPT
 */

import React, { useState, useEffect } from 'react';
import {
  Brain,
  Activity,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle,
  Clock,
  Zap,
  BarChart3,
  RefreshCw,
  Download,
  Settings,
  Info,
  MessageSquare,
  Sparkles,
} from 'lucide-react';

interface Insight {
  type: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  tag_id?: string;
  tag_name?: string;
  data?: any;
  ai_analysis?: string;  // Análise gerada pelo ChatGPT
}

interface HealthScore {
  score: number;
  status: 'healthy' | 'degraded' | 'critical';
  anomaly_count: number;
  critical_insights: number;
  warning_insights: number;
  last_updated: string;
}

interface DashboardSummary {
  health_score: HealthScore;
  recent_insights: Insight[];
  anomalies_detected: number;
  tags_monitored: number;
  models_active: number;
  last_analysis: string | null;
}

export const AIInsightsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [chatMessage, setChatMessage] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatResponse, setChatResponse] = useState('');

  // Fetch dashboard summary
  const fetchSummary = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/ai/dashboard/summary', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSummary(data);
      } else {
        console.error('Failed to fetch AI summary');
        // Set mock data for demo
        setSummary(getMockSummary());
      }
    } catch (error) {
      console.error('Error fetching AI summary:', error);
      // Set mock data for demo
      setSummary(getMockSummary());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchSummary();
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Filter insights by severity
  const filteredInsights = summary?.recent_insights.filter(insight => {
    if (selectedSeverity === 'all') return true;
    return insight.severity === selectedSeverity;
  }) || [];

  // Get severity icon and color
  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200">
            <AlertCircle className="w-3 h-3 mr-1" />
            Critical
          </span>
        );
      case 'warning':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200">
            <AlertCircle className="w-3 h-3 mr-1" />
            Warning
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
            <Info className="w-3 h-3 mr-1" />
            Info
          </span>
        );
    }
  };

  // Get health status color
  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 dark:text-green-400';
      case 'degraded':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'critical':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-600 dark:text-blue-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading AI Insights...</p>
        </div>
      </div>
    );
  }

  const healthScore = summary?.health_score;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg">
            <Brain className="w-8 h-8 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">AI Insights</h1>
            <p className="text-gray-600 dark:text-gray-400">Real-time process intelligence and anomaly detection</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              autoRefresh
                ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-200'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            <span className="text-sm">{autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}</span>
          </button>

          <button
            onClick={fetchSummary}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>

          <button className="flex items-center space-x-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Health Score Card */}
      {healthScore && (
        <div className="bg-gradient-to-br from-purple-500 to-blue-600 dark:from-purple-700 dark:to-blue-800 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold mb-2 flex items-center">
                <Activity className="w-5 h-5 mr-2" />
                System Health Score
              </h2>
              <div className="flex items-baseline space-x-2">
                <span className="text-5xl font-bold">{healthScore.score.toFixed(0)}</span>
                <span className="text-2xl">/100</span>
              </div>
              <p className="text-purple-100 dark:text-purple-200 mt-2 capitalize">
                Status: {healthScore.status}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 text-right">
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-3xl font-bold">{healthScore.critical_insights}</div>
                <div className="text-sm text-purple-100 dark:text-purple-200">Critical</div>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-3xl font-bold">{healthScore.warning_insights}</div>
                <div className="text-sm text-purple-100 dark:text-purple-200">Warnings</div>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-3xl font-bold">{summary?.tags_monitored || 0}</div>
                <div className="text-sm text-purple-100 dark:text-purple-200">Tags Monitored</div>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-3xl font-bold">{summary?.anomalies_detected || 0}</div>
                <div className="text-sm text-purple-100 dark:text-purple-200">Anomalies</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Active Models</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {summary?.models_active || 0}
              </p>
            </div>
            <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Brain className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Anomalies Detected</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {summary?.anomalies_detected || 0}
              </p>
            </div>
            <div className="p-3 bg-red-100 dark:bg-red-900 rounded-lg">
              <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Tags Analyzed</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {summary?.tags_monitored || 0}
              </p>
            </div>
            <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
              <BarChart3 className="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Last Analysis</p>
              <p className="text-sm font-medium text-gray-900 dark:text-white mt-1">
                {summary?.last_analysis ? new Date(summary.last_analysis).toLocaleTimeString() : 'N/A'}
              </p>
            </div>
            <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <Clock className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Insights Feed */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <Zap className="w-5 h-5 mr-2 text-yellow-500" />
              Recent Insights
            </h2>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setSelectedSeverity('all')}
                className={`px-3 py-1 rounded-md text-sm transition-colors ${
                  selectedSeverity === 'all'
                    ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setSelectedSeverity('critical')}
                className={`px-3 py-1 rounded-md text-sm transition-colors ${
                  selectedSeverity === 'critical'
                    ? 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                }`}
              >
                Critical
              </button>
              <button
                onClick={() => setSelectedSeverity('warning')}
                className={`px-3 py-1 rounded-md text-sm transition-colors ${
                  selectedSeverity === 'warning'
                    ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                }`}
              >
                Warnings
              </button>
            </div>
          </div>
        </div>

        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {filteredInsights.length > 0 ? (
            filteredInsights.map((insight, idx) => (
              <div key={idx} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      {getSeverityBadge(insight.severity)}
                      {insight.tag_name && (
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {insight.tag_name}
                        </span>
                      )}
                    </div>
                    <p className="text-gray-700 dark:text-gray-300">{insight.message}</p>
                  </div>
                  <button className="ml-4 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-sm">
                    View Details
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="px-6 py-12 text-center">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">
                {selectedSeverity === 'all'
                  ? 'No insights available'
                  : `No ${selectedSeverity} insights at this time`}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Coming Soon - Phase 2 */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800 dark:to-gray-700 rounded-lg border-2 border-dashed border-blue-300 dark:border-blue-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          🚀 Coming Soon - Phase 2
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-700 dark:text-gray-300">
          <div>
            <h4 className="font-semibold mb-1">Predictive Maintenance</h4>
            <p>Equipment failure prediction and RUL estimation</p>
          </div>
          <div>
            <h4 className="font-semibold mb-1">Process Optimization</h4>
            <p>AI-powered setpoint recommendations</p>
          </div>
          <div>
            <h4 className="font-semibold mb-1">Demand Forecasting</h4>
            <p>Production and energy demand predictions</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Mock data for demo
function getMockSummary(): DashboardSummary {
  return {
    health_score: {
      score: 87.5,
      status: 'healthy',
      anomaly_count: 2,
      critical_insights: 0,
      warning_insights: 3,
      last_updated: new Date().toISOString(),
    },
    recent_insights: [
      {
        type: 'trend',
        severity: 'warning',
        message: '📈 CONV1_MOTOR_CURRENT is trending upward (12.5% increase over time)',
        tag_name: 'CONV1_MOTOR_CURRENT',
      },
      {
        type: 'outlier',
        severity: 'warning',
        message: '⚠️ CONV1_MOTOR_TEMP has 3 outlier(s) detected (5.2% of data)',
        tag_name: 'CONV1_MOTOR_TEMP',
      },
      {
        type: 'baseline_comparison',
        severity: 'info',
        message: '✅ SHIP_FLOW_RATE is within normal range',
        tag_name: 'SHIP_FLOW_RATE',
      },
      {
        type: 'level_shift',
        severity: 'warning',
        message: '🔄 ELEV1_MOTOR_CURRENT increased by 15.3% - possible setpoint change or process shift',
        tag_name: 'ELEV1_MOTOR_CURRENT',
      },
      {
        type: 'trend',
        severity: 'info',
        message: '➡️ PRODUCT_MOISTURE is stable',
        tag_name: 'PRODUCT_MOISTURE',
      },
    ],
    anomalies_detected: 2,
    tags_monitored: 45,
    models_active: 0,
    last_analysis: new Date().toISOString(),
  };
}

export default AIInsightsPage;
