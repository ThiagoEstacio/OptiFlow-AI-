/**
 * Widget de Health Score AI/ML
 *
 * Exibe o status de saúde do sistema AI/ML em tempo real
 */

import React, { useState, useEffect } from 'react';
import { Brain, Activity, CheckCircle, AlertTriangle, XCircle, RefreshCw } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface AIHealthData {
  timestamp: string;
  status: 'healthy' | 'degraded' | 'error';
  components: {
    autonomous_agent: {
      available: boolean;
      status: string;
      insights_count: number;
    };
    ai_insights_service: {
      available: boolean;
      status: string;
    };
  };
  message?: string;
}

interface AIHealthWidgetProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const AIHealthWidget: React.FC<AIHealthWidgetProps> = ({
  autoRefresh = true,
  refreshInterval = 60000, // 60 segundos
}) => {
  const [healthData, setHealthData] = useState<AIHealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchHealth = async () => {
    try {
      setLoading(true);

      // ✨ Endpoint público de health
      const response = await fetch(`${API_BASE}/api/v1/ai/health/public`);

      if (response.ok) {
        const data = await response.json();
        setHealthData(data);
        console.log('✅ AI Health status:', data.status);
      } else {
        setHealthData({
          timestamp: new Date().toISOString(),
          status: 'error',
          components: {
            autonomous_agent: {
              available: false,
              status: 'unknown',
              insights_count: 0,
            },
            ai_insights_service: {
              available: false,
              status: 'unknown',
            },
          },
          message: 'Erro ao conectar com o servidor',
        });
      }

      setLastUpdate(new Date());
    } catch (error) {
      console.error('❌ Erro ao buscar AI health:', error);
      setHealthData({
        timestamp: new Date().toISOString(),
        status: 'error',
        components: {
          autonomous_agent: {
            available: false,
            status: 'error',
            insights_count: 0,
          },
          ai_insights_service: {
            available: false,
            status: 'error',
          },
        },
        message: 'Erro ao buscar status',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();

    if (autoRefresh) {
      const interval = setInterval(fetchHealth, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const getStatusColor = (status: string) => {
    const colors = {
      healthy: 'bg-green-100 text-green-800 border-green-300',
      degraded: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      error: 'bg-red-100 text-red-800 border-red-300',
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const getStatusIcon = (status: string) => {
    if (status === 'healthy') {
      return <CheckCircle className="w-6 h-6 text-green-600" />;
    } else if (status === 'degraded') {
      return <AlertTriangle className="w-6 h-6 text-yellow-600" />;
    } else {
      return <XCircle className="w-6 h-6 text-red-600" />;
    }
  };

  const getStatusText = (status: string) => {
    const texts = {
      healthy: 'Saudável',
      degraded: 'Degradado',
      error: 'Erro',
      running: 'Rodando',
      not_initialized: 'Não Inicializado',
      unknown: 'Desconhecido',
    };
    return texts[status as keyof typeof texts] || status;
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">AI/ML System Health</h3>
        </div>

        <button
          onClick={fetchHealth}
          disabled={loading}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="Atualizar"
        >
          <RefreshCw className={`w-4 h-4 text-gray-600 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Loading */}
      {loading && !healthData && (
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-6 h-6 text-blue-600 animate-spin" />
          <span className="ml-2 text-gray-600">Carregando status...</span>
        </div>
      )}

      {/* Health Status */}
      {healthData && (
        <div className="space-y-4">
          {/* Overall Status */}
          <div className={`p-4 rounded-lg border ${getStatusColor(healthData.status)}`}>
            <div className="flex items-center gap-3">
              {getStatusIcon(healthData.status)}
              <div className="flex-1">
                <div className="font-semibold text-sm">
                  Status Geral: {getStatusText(healthData.status).toUpperCase()}
                </div>
                {healthData.message && (
                  <div className="text-xs mt-1 opacity-75">
                    {healthData.message}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Components Status */}
          <div className="space-y-3">
            {/* Autonomous Agent */}
            <div className="border border-gray-200 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4 text-gray-600" />
                <h4 className="font-semibold text-sm text-gray-900">Autonomous Agent</h4>
              </div>

              <div className="space-y-1 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Status:</span>
                  <span
                    className={`px-2 py-1 rounded-full font-medium ${
                      healthData.components.autonomous_agent.available
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {getStatusText(healthData.components.autonomous_agent.status)}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Insights Gerados:</span>
                  <span className="font-medium text-gray-900">
                    {healthData.components.autonomous_agent.insights_count}
                  </span>
                </div>
              </div>
            </div>

            {/* AI Insights Service */}
            <div className="border border-gray-200 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <Brain className="w-4 h-4 text-gray-600" />
                <h4 className="font-semibold text-sm text-gray-900">AI Insights Service</h4>
              </div>

              <div className="space-y-1 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Status:</span>
                  <span
                    className={`px-2 py-1 rounded-full font-medium ${
                      healthData.components.ai_insights_service.available
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {getStatusText(healthData.components.ai_insights_service.status)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Footer - Last Update */}
          <div className="pt-3 border-t border-gray-200 text-xs text-gray-500 text-center">
            Última atualização: {lastUpdate.toLocaleTimeString()}
          </div>
        </div>
      )}
    </div>
  );
};

export default AIHealthWidget;
