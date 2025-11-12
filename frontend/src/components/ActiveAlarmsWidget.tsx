/**
 * Widget de Alarmes Ativos - Integrado com Agent
 *
 * Exibe alarmes ativos em tempo real usando a API do Agent
 */

import React, { useState, useEffect } from 'react';
import { AlertTriangle, AlertCircle, Clock, CheckCircle, RefreshCw } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Alarm {
  alarm_id: string;
  alarm_name: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  tag_id: string;
  trigger_value: number;
  trigger_timestamp: string;
  state: string;
  description: string;
  alarm_type: string;
}

interface ActiveAlarmsWidgetProps {
  maxAlarms?: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const ActiveAlarmsWidget: React.FC<ActiveAlarmsWidgetProps> = ({
  maxAlarms = 5,
  autoRefresh = true,
  refreshInterval = 30000, // 30 segundos
}) => {
  const [alarms, setAlarms] = useState<Alarm[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchActiveAlarms = async () => {
    try {
      setLoading(true);
      setError(null);

      // ✨ Chamar API do Agent para obter alarmes ativos
      const response = await fetch(
        `${API_BASE}/api/v1/agent/tools/test?tool_name=get_active_alarms`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            limit: maxAlarms,
          }),
        }
      );

      if (response.ok) {
        const result = await response.json();

        if (result.success && result.data.alarms) {
          setAlarms(result.data.alarms);
          console.log('✅ Alarmes ativos carregados:', result.data.total_alarms);
        } else {
          setError(result.error || 'Erro ao carregar alarmes');
        }
      } else {
        setError('Falha ao conectar com o servidor');
      }

      setLastUpdate(new Date());
    } catch (err) {
      console.error('❌ Erro ao buscar alarmes:', err);
      setError('Erro ao buscar alarmes ativos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActiveAlarms();

    if (autoRefresh) {
      const interval = setInterval(fetchActiveAlarms, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, maxAlarms]);

  const getSeverityColor = (severity: string) => {
    const colors = {
      critical: 'bg-red-100 text-red-800 border-red-300',
      high: 'bg-orange-100 text-orange-800 border-orange-300',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      low: 'bg-blue-100 text-blue-800 border-blue-300',
    };
    return colors[severity as keyof typeof colors] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const getSeverityIcon = (severity: string) => {
    if (severity === 'critical' || severity === 'high') {
      return <AlertTriangle className="w-4 h-4" />;
    }
    return <AlertCircle className="w-4 h-4" />;
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);

    if (minutes < 60) {
      return `${minutes}m atrás`;
    } else if (hours < 24) {
      return `${hours}h atrás`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-600" />
          <h3 className="text-lg font-semibold text-gray-900">Alarmes Ativos</h3>
          {!loading && (
            <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">
              {alarms.length}
            </span>
          )}
        </div>

        <button
          onClick={fetchActiveAlarms}
          disabled={loading}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="Atualizar"
        >
          <RefreshCw className={`w-4 h-4 text-gray-600 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-6 h-6 text-blue-600 animate-spin" />
          <span className="ml-2 text-gray-600">Carregando alarmes...</span>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
          <AlertCircle className="w-6 h-6 text-red-600 mx-auto mb-2" />
          <p className="text-sm text-red-800">{error}</p>
          <button
            onClick={fetchActiveAlarms}
            className="mt-2 text-sm text-red-600 hover:text-red-700 underline"
          >
            Tentar novamente
          </button>
        </div>
      )}

      {/* Alarms List */}
      {!loading && !error && alarms.length === 0 && (
        <div className="text-center py-8">
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-2" />
          <p className="text-gray-600 font-medium">Nenhum alarme ativo</p>
          <p className="text-sm text-gray-500 mt-1">Sistema operando normalmente</p>
        </div>
      )}

      {!loading && !error && alarms.length > 0 && (
        <div className="space-y-3">
          {alarms.map((alarm) => (
            <div
              key={alarm.alarm_id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start gap-3">
                {/* Severity Icon */}
                <div className={`p-2 rounded-lg border ${getSeverityColor(alarm.severity)}`}>
                  {getSeverityIcon(alarm.severity)}
                </div>

                {/* Alarm Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="font-semibold text-gray-900 text-sm">
                      {alarm.alarm_name}
                    </h4>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(alarm.severity)}`}>
                      {alarm.severity.toUpperCase()}
                    </span>
                  </div>

                  <p className="text-sm text-gray-600 mt-1">
                    {alarm.description}
                  </p>

                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      <span>{formatTimestamp(alarm.trigger_timestamp)}</span>
                    </div>

                    <div>
                      Valor: <span className="font-medium">{alarm.trigger_value.toFixed(2)}</span>
                    </div>

                    <div className="text-gray-400">
                      {alarm.alarm_type}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Footer - Last Update */}
      {!loading && (
        <div className="mt-4 pt-3 border-t border-gray-200 text-xs text-gray-500 text-center">
          Última atualização: {lastUpdate.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

export default ActiveAlarmsWidget;
