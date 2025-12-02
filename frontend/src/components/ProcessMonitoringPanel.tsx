/**
 * ProcessMonitoringPanel Component
 *
 * Real-time process monitoring with:
 * - Live tag values with status indicators
 * - Anomaly detection and alerts
 * - AI-powered diagnostics and recommendations
 * - KPI dashboard
 * - Equipment health overview
 */

import React, { useState, useCallback, useMemo } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  Minus,
  Bell,
  BellOff,
  RefreshCw,
  Zap,
  Thermometer,
  Gauge,
  Settings,
  ChevronRight,
  ChevronDown,
  Lightbulb,
  Bot,
  Clock,
  Filter
} from 'lucide-react';
import {
  useProcessHealth,
  type HealthStatus,
  type TrendDirection,
  type ProcessAlert,
  type TagHealth,
  type ProcessKPI,
  type AlertSeverity
} from '../hooks/useProcessHealth';

// ========================================
// Sub-components
// ========================================

interface StatusBadgeProps {
  status: HealthStatus;
  size?: 'sm' | 'md' | 'lg';
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const colors: Record<HealthStatus, string> = {
    healthy: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    critical: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    unknown: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
  };

  const icons: Record<HealthStatus, React.ReactNode> = {
    healthy: <CheckCircle className={size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} />,
    warning: <AlertTriangle className={size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} />,
    critical: <XCircle className={size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} />,
    unknown: <Minus className={size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} />
  };

  const labels: Record<HealthStatus, string> = {
    healthy: 'Normal',
    warning: 'Alerta',
    critical: 'Crítico',
    unknown: 'Desconhecido'
  };

  const sizeClasses = {
    sm: 'px-1.5 py-0.5 text-xs',
    md: 'px-2 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base'
  };

  return (
    <span className={`inline-flex items-center gap-1 rounded-full font-medium ${colors[status]} ${sizeClasses[size]}`}>
      {icons[status]}
      {labels[status]}
    </span>
  );
};

interface TrendIndicatorProps {
  direction: TrendDirection;
  percent: number;
}

const TrendIndicator: React.FC<TrendIndicatorProps> = ({ direction, percent }) => {
  const absPercent = Math.abs(percent);

  if (direction === 'stable' || absPercent < 1) {
    return (
      <span className="inline-flex items-center gap-1 text-gray-500 dark:text-gray-400 text-sm">
        <Minus className="w-4 h-4" />
        <span>Estável</span>
      </span>
    );
  }

  const isUp = direction === 'up';
  const color = absPercent > 10
    ? (isUp ? 'text-red-500' : 'text-blue-500')
    : 'text-gray-600 dark:text-gray-400';

  return (
    <span className={`inline-flex items-center gap-1 ${color} text-sm`}>
      {isUp ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
      <span>{isUp ? '+' : ''}{percent.toFixed(1)}%</span>
    </span>
  );
};

interface SeverityBadgeProps {
  severity: AlertSeverity;
}

const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity }) => {
  const colors: Record<AlertSeverity, string> = {
    info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    low: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    high: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
    critical: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
  };

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium uppercase ${colors[severity]}`}>
      {severity}
    </span>
  );
};

// ========================================
// Tag Card Component
// ========================================

interface TagCardProps {
  tag: TagHealth;
  onDiagnose?: (tagId: string) => void;
}

const TagCard: React.FC<TagCardProps> = ({ tag, onDiagnose }) => {
  const [expanded, setExpanded] = useState(false);

  const getIcon = () => {
    const name = tag.tagName.toLowerCase();
    if (name.includes('temp')) return <Thermometer className="w-5 h-5" />;
    if (name.includes('flow') || name.includes('vazao')) return <Activity className="w-5 h-5" />;
    if (name.includes('press')) return <Gauge className="w-5 h-5" />;
    return <Zap className="w-5 h-5" />;
  };

  const statusBorder: Record<HealthStatus, string> = {
    healthy: 'border-l-green-500',
    warning: 'border-l-yellow-500',
    critical: 'border-l-red-500',
    unknown: 'border-l-gray-400'
  };

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border-l-4 ${statusBorder[tag.status]} p-4 transition-all hover:shadow-md`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${
            tag.status === 'critical' ? 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' :
            tag.status === 'warning' ? 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' :
            'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
          }`}>
            {getIcon()}
          </div>
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white text-sm">
              {tag.tagName}
            </h4>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-2xl font-bold text-gray-900 dark:text-white">
                {tag.currentValue?.toFixed(2) ?? '---'}
              </span>
              {tag.unit && (
                <span className="text-gray-500 dark:text-gray-400 text-sm">{tag.unit}</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          <StatusBadge status={tag.status} size="sm" />
          <TrendIndicator direction={tag.trend} percent={tag.trendPercent} />
        </div>
      </div>

      {/* Limits indicator */}
      {tag.limits && tag.currentValue !== null && (
        <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
          <div className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            {/* Low/High zones */}
            {tag.limits.low !== undefined && tag.limits.high !== undefined && (
              <>
                <div
                  className="absolute h-full bg-yellow-200 dark:bg-yellow-900/50"
                  style={{
                    left: '0%',
                    width: `${((tag.limits.low - (tag.limits.lowLow || 0)) / ((tag.limits.highHigh || tag.limits.high * 1.5) - (tag.limits.lowLow || 0))) * 100}%`
                  }}
                />
                <div
                  className="absolute h-full bg-green-200 dark:bg-green-900/50"
                  style={{
                    left: `${((tag.limits.low - (tag.limits.lowLow || 0)) / ((tag.limits.highHigh || tag.limits.high * 1.5) - (tag.limits.lowLow || 0))) * 100}%`,
                    width: `${((tag.limits.high - tag.limits.low) / ((tag.limits.highHigh || tag.limits.high * 1.5) - (tag.limits.lowLow || 0))) * 100}%`
                  }}
                />
              </>
            )}
            {/* Current value marker */}
            <div
              className={`absolute w-1 h-full ${
                tag.status === 'critical' ? 'bg-red-600' :
                tag.status === 'warning' ? 'bg-yellow-600' : 'bg-green-600'
              }`}
              style={{
                left: `${Math.min(100, Math.max(0, ((tag.currentValue - (tag.limits.lowLow || 0)) / ((tag.limits.highHigh || tag.limits.high || 100) - (tag.limits.lowLow || 0))) * 100))}%`
              }}
            />
          </div>
          <div className="flex justify-between mt-1 text-xs text-gray-500 dark:text-gray-400">
            <span>{tag.limits.lowLow ?? tag.limits.low ?? 'Min'}</span>
            <span>{tag.limits.highHigh ?? tag.limits.high ?? 'Max'}</span>
          </div>
        </div>
      )}

      {/* Expandable details */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-3 flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline"
      >
        {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        {expanded ? 'Menos detalhes' : 'Mais detalhes'}
      </button>

      {expanded && (
        <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 space-y-2">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            <span className="font-medium">Última atualização:</span>{' '}
            {tag.lastUpdate?.toLocaleTimeString() ?? 'N/A'}
          </div>
          {tag.history.length > 0 && (
            <div className="flex gap-1 h-8">
              {tag.history.slice(-20).map((h, i) => {
                const min = Math.min(...tag.history.map(x => x.value));
                const max = Math.max(...tag.history.map(x => x.value));
                const range = max - min || 1;
                const height = ((h.value - min) / range) * 100;
                return (
                  <div
                    key={i}
                    className="flex-1 bg-blue-200 dark:bg-blue-800 rounded-t"
                    style={{ height: `${Math.max(5, height)}%`, marginTop: 'auto' }}
                    title={`${h.value.toFixed(2)} @ ${h.timestamp.toLocaleTimeString()}`}
                  />
                );
              })}
            </div>
          )}
          {onDiagnose && (
            <button
              onClick={() => onDiagnose(tag.tagId)}
              className="mt-2 flex items-center gap-2 px-3 py-1.5 text-sm bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-colors"
            >
              <Bot className="w-4 h-4" />
              Diagnóstico IA
            </button>
          )}
        </div>
      )}
    </div>
  );
};

// ========================================
// Alert Card Component
// ========================================

interface AlertCardProps {
  alert: ProcessAlert;
  onAcknowledge: (id: string) => void;
}

const AlertCard: React.FC<AlertCardProps> = ({ alert, onAcknowledge }) => {
  const [showRecommendations, setShowRecommendations] = useState(false);

  const typeIcons: Record<ProcessAlert['type'], React.ReactNode> = {
    anomaly: <Activity className="w-5 h-5" />,
    threshold: <AlertTriangle className="w-5 h-5" />,
    trend: <TrendingUp className="w-5 h-5" />,
    equipment: <Settings className="w-5 h-5" />,
    prediction: <Bot className="w-5 h-5" />
  };

  const severityColors: Record<AlertSeverity, string> = {
    info: 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/10',
    low: 'border-l-gray-400 bg-gray-50 dark:bg-gray-800',
    medium: 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-900/10',
    high: 'border-l-orange-500 bg-orange-50 dark:bg-orange-900/10',
    critical: 'border-l-red-500 bg-red-50 dark:bg-red-900/10'
  };

  return (
    <div className={`rounded-lg border-l-4 p-4 ${severityColors[alert.severity]} ${alert.acknowledged ? 'opacity-60' : ''}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${
            alert.severity === 'critical' ? 'bg-red-200 text-red-700 dark:bg-red-900/50 dark:text-red-300' :
            alert.severity === 'high' ? 'bg-orange-200 text-orange-700 dark:bg-orange-900/50 dark:text-orange-300' :
            'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
          }`}>
            {typeIcons[alert.type]}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-medium text-gray-900 dark:text-white">
                {alert.title}
              </h4>
              <SeverityBadge severity={alert.severity} />
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {alert.description}
            </p>
            <div className="flex items-center gap-2 mt-2 text-xs text-gray-500 dark:text-gray-400">
              <Clock className="w-3 h-3" />
              {alert.timestamp.toLocaleTimeString()}
              {alert.tagId && (
                <span className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">
                  {alert.tagId}
                </span>
              )}
            </div>
          </div>
        </div>

        {!alert.acknowledged && (
          <button
            onClick={() => onAcknowledge(alert.id)}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Reconhecer alerta"
          >
            <BellOff className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Recommendations */}
      {alert.recommendations.length > 0 && (
        <div className="mt-3">
          <button
            onClick={() => setShowRecommendations(!showRecommendations)}
            className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            <Lightbulb className="w-4 h-4" />
            {showRecommendations ? 'Ocultar recomendações' : `Ver ${alert.recommendations.length} recomendações`}
          </button>

          {showRecommendations && (
            <ul className="mt-2 space-y-1">
              {alert.recommendations.map((rec, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <ChevronRight className="w-4 h-4 mt-0.5 text-green-500" />
                  {rec}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};

// ========================================
// KPI Card Component
// ========================================

interface KPICardProps {
  kpi: ProcessKPI;
}

const KPICard: React.FC<KPICardProps> = ({ kpi }) => {
  const statusColors: Record<HealthStatus, string> = {
    healthy: 'text-green-600 dark:text-green-400',
    warning: 'text-yellow-600 dark:text-yellow-400',
    critical: 'text-red-600 dark:text-red-400',
    unknown: 'text-gray-500 dark:text-gray-400'
  };

  const progressPercent = kpi.target
    ? Math.min(100, (kpi.value / kpi.target) * 100)
    : kpi.max
      ? Math.min(100, (kpi.value / kpi.max) * 100)
      : 50;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-600 dark:text-gray-400">{kpi.name}</span>
        <StatusBadge status={kpi.status} size="sm" />
      </div>
      <div className="flex items-baseline gap-2">
        <span className={`text-3xl font-bold ${statusColors[kpi.status]}`}>
          {kpi.value.toFixed(kpi.unit ? 1 : 0)}
        </span>
        {kpi.unit && (
          <span className="text-gray-500 dark:text-gray-400">{kpi.unit}</span>
        )}
      </div>
      {(kpi.target || kpi.max) && (
        <div className="mt-2">
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                kpi.status === 'critical' ? 'bg-red-500' :
                kpi.status === 'warning' ? 'bg-yellow-500' : 'bg-green-500'
              }`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <div className="flex justify-between mt-1 text-xs text-gray-500 dark:text-gray-400">
            <span>{kpi.min ?? 0}</span>
            <span>Meta: {kpi.target ?? kpi.max}</span>
          </div>
        </div>
      )}
    </div>
  );
};

// ========================================
// Main Component
// ========================================

export interface ProcessMonitoringPanelProps {
  tagIds?: string[];
  equipmentIds?: string[];
  alertThresholds?: Record<string, { low?: number; high?: number; lowLow?: number; highHigh?: number }>;
  refreshInterval?: number;
  title?: string;
  showKPIs?: boolean;
  showAlerts?: boolean;
  compact?: boolean;
}

export const ProcessMonitoringPanel: React.FC<ProcessMonitoringPanelProps> = ({
  tagIds,
  equipmentIds,
  alertThresholds,
  refreshInterval = 2000,
  title = 'Monitoramento de Processo',
  showKPIs = true,
  showAlerts = true,
  compact = false
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'tags' | 'alerts'>('overview');
  const [filterSeverity, setFilterSeverity] = useState<AlertSeverity | 'all'>('all');
  const [diagnosticResult, setDiagnosticResult] = useState<{ tagId: string; result: string } | null>(null);
  const [isDiagnosing, setIsDiagnosing] = useState(false);

  const processHealth = useProcessHealth({
    tagIds,
    equipmentIds,
    refreshInterval,
    alertThresholds,
    enableAnomalyDetection: true
  });

  const handleDiagnose = useCallback(async (tagId: string) => {
    setIsDiagnosing(true);
    try {
      const result = await processHealth.getDiagnostic(tagId);
      setDiagnosticResult({ tagId, result });
    } finally {
      setIsDiagnosing(false);
    }
  }, [processHealth]);

  const filteredAlerts = useMemo(() => {
    if (filterSeverity === 'all') return processHealth.alerts;
    return processHealth.alerts.filter(a => a.severity === filterSeverity);
  }, [processHealth.alerts, filterSeverity]);

  const unacknowledgedCount = processHealth.alerts.filter(a => !a.acknowledged).length;
  const criticalCount = processHealth.alerts.filter(a => a.severity === 'critical' && !a.acknowledged).length;

  const statusBgColor: Record<HealthStatus, string> = {
    healthy: 'bg-green-500',
    warning: 'bg-yellow-500',
    critical: 'bg-red-500',
    unknown: 'bg-gray-400'
  };

  return (
    <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className={`w-3 h-3 rounded-full ${statusBgColor[processHealth.overallStatus]} ${
            processHealth.overallStatus === 'critical' ? 'animate-pulse' : ''
          }`} />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {title}
          </h2>
          <StatusBadge status={processHealth.overallStatus} />
        </div>

        <div className="flex items-center gap-3">
          {/* Connection status */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm ${
            processHealth.connectionStatus === 'connected'
              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
              : processHealth.connectionStatus === 'connecting'
                ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
          }`}>
            <div className={`w-2 h-2 rounded-full ${
              processHealth.connectionStatus === 'connected' ? 'bg-green-500' :
              processHealth.connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' : 'bg-red-500'
            }`} />
            {processHealth.connectionStatus === 'connected' ? 'Conectado' :
             processHealth.connectionStatus === 'connecting' ? 'Conectando...' : 'Desconectado'}
          </div>

          {/* Alerts badge - só exibe se showAlerts=true */}
          {showAlerts && unacknowledgedCount > 0 && (
            <div className="flex items-center gap-1 px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg">
              <Bell className="w-4 h-4" />
              <span className="text-sm font-medium">{unacknowledgedCount}</span>
            </div>
          )}

          {/* Refresh button */}
          <button
            onClick={processHealth.refresh}
            disabled={processHealth.isLoading}
            className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
            title="Atualizar"
          >
            <RefreshCw className={`w-5 h-5 ${processHealth.isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Error display */}
      {processHealth.error && (
        <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg">
          {processHealth.error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'overview'
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Visão Geral
        </button>
        <button
          onClick={() => setActiveTab('tags')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'tags'
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Tags ({Object.keys(processHealth.tags).length})
        </button>
        {/* Aba de Alertas - só exibe se showAlerts=true */}
        {showAlerts && (
          <button
            onClick={() => setActiveTab('alerts')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'alerts'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Alertas
            {criticalCount > 0 && (
              <span className="px-1.5 py-0.5 bg-red-500 text-white text-xs rounded-full">
                {criticalCount}
              </span>
            )}
          </button>
        )}
      </div>

      {/* Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* KPIs */}
          {showKPIs && processHealth.kpis.length > 0 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                KPIs do Processo
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {processHealth.kpis.map(kpi => (
                  <KPICard key={kpi.id} kpi={kpi} />
                ))}
              </div>
            </div>
          )}

          {/* Critical Tags */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Tags em Atenção
            </h3>
            {Object.values(processHealth.tags).filter(t => t.status !== 'healthy').length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.values(processHealth.tags)
                  .filter(t => t.status !== 'healthy')
                  .sort((a, b) => {
                    const order: Record<HealthStatus, number> = { critical: 0, warning: 1, unknown: 2, healthy: 3 };
                    return order[a.status] - order[b.status];
                  })
                  .slice(0, 6)
                  .map(tag => (
                    <TagCard key={tag.tagId} tag={tag} onDiagnose={handleDiagnose} />
                  ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <CheckCircle className="w-12 h-12 mx-auto mb-2 text-green-500" />
                <p>Todos os tags estão operando normalmente</p>
              </div>
            )}
          </div>

          {/* Recent Alerts */}
          {showAlerts && processHealth.alerts.filter(a => !a.acknowledged).length > 0 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Alertas Recentes
              </h3>
              <div className="space-y-3">
                {processHealth.alerts
                  .filter(a => !a.acknowledged)
                  .slice(0, 3)
                  .map(alert => (
                    <AlertCard
                      key={alert.id}
                      alert={alert}
                      onAcknowledge={processHealth.acknowledgeAlert}
                    />
                  ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'tags' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.values(processHealth.tags).map(tag => (
            <TagCard key={tag.tagId} tag={tag} onDiagnose={handleDiagnose} />
          ))}
          {Object.keys(processHealth.tags).length === 0 && (
            <div className="col-span-full text-center py-12 text-gray-500 dark:text-gray-400">
              <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>Nenhum tag configurado</p>
            </div>
          )}
        </div>
      )}

      {/* Conteúdo da aba de Alertas - só renderiza se showAlerts=true */}
      {showAlerts && activeTab === 'alerts' && (
        <div className="space-y-4">
          {/* Filter */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={filterSeverity}
                onChange={(e) => setFilterSeverity(e.target.value as AlertSeverity | 'all')}
                className="px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm"
              >
                <option value="all">Todas severidades</option>
                <option value="critical">Crítico</option>
                <option value="high">Alto</option>
                <option value="medium">Médio</option>
                <option value="low">Baixo</option>
                <option value="info">Info</option>
              </select>
            </div>

            <button
              onClick={processHealth.clearResolvedAlerts}
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
            >
              Limpar reconhecidos
            </button>
          </div>

          {/* Alert list */}
          <div className="space-y-3">
            {filteredAlerts.map(alert => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onAcknowledge={processHealth.acknowledgeAlert}
              />
            ))}
            {filteredAlerts.length === 0 && (
              <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                <Bell className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Nenhum alerta ativo</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Diagnostic Modal */}
      {diagnosticResult && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl max-w-lg w-full p-6 shadow-xl">
            <div className="flex items-center gap-3 mb-4">
              <Bot className="w-6 h-6 text-purple-500" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Diagnóstico IA - {diagnosticResult.tagId}
              </h3>
            </div>
            <div className="prose dark:prose-invert text-sm max-h-64 overflow-y-auto">
              {diagnosticResult.result}
            </div>
            <button
              onClick={() => setDiagnosticResult(null)}
              className="mt-4 w-full py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              Fechar
            </button>
          </div>
        </div>
      )}

      {/* Loading overlay for diagnostic */}
      {isDiagnosing && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-xl flex items-center gap-4">
            <RefreshCw className="w-6 h-6 animate-spin text-purple-500" />
            <span className="text-gray-900 dark:text-white">Analisando com IA...</span>
          </div>
        </div>
      )}

      {/* Last update */}
      {processHealth.lastUpdate && (
        <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400 text-right">
          Última atualização: {processHealth.lastUpdate.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

export default ProcessMonitoringPanel;
