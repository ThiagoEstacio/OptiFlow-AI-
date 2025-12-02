/**
 * ProcessMonitoringPage
 *
 * Dedicated page for real-time process monitoring with:
 * - Full process overview
 * - Multiple monitoring sections by area
 * - AI-powered diagnostics
 * - Alert management
 * - Equipment health dashboard
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  Settings,
  Maximize2,
  Minimize2,
  Download,
  Filter,
  LayoutDashboard,
  Layers,
  Thermometer,
  Gauge,
  Zap,
  RefreshCw,
  Bot,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  Bell,
  ExternalLink
} from 'lucide-react';
import { ProcessMonitoringPanel } from '../components/ProcessMonitoringPanel';
import { useProcessHealth, type HealthStatus } from '../hooks/useProcessHealth';
import { MLInsightsPanel } from '../components/MLInsightsPanel';

// ========================================
// Process Area Configuration
// ========================================

interface ProcessArea {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  tagPatterns: string[];
  alertThresholds: Record<string, { low?: number; high?: number; lowLow?: number; highHigh?: number }>;
}

const processAreas: ProcessArea[] = [
  {
    id: 'reception',
    name: 'Recepção',
    description: 'Área de recebimento de grãos',
    icon: <Layers className="w-5 h-5" />,
    tagPatterns: ['GATE', 'MOEGA', 'BALANCA'],
    alertThresholds: {
      'GATE01_POS': { low: 5, high: 95 },
      'GATE02_POS': { low: 5, high: 95 },
      'MOEGA_NIVEL': { low: 10, high: 90, lowLow: 5, highHigh: 95 }
    }
  },
  {
    id: 'transport',
    name: 'Transporte',
    description: 'Correias transportadoras e elevadores',
    icon: <Activity className="w-5 h-5" />,
    tagPatterns: ['CORR', 'ELEV', 'TC', 'EL'],
    alertThresholds: {
      'CORR01_TEMP': { high: 70, highHigh: 85 },
      'CORR01_CORRENTE': { high: 150, highHigh: 180 },
      'ELEV01_TEMP': { high: 65, highHigh: 80 },
      'ELEV01_CORRENTE': { high: 200, highHigh: 250 }
    }
  },
  {
    id: 'storage',
    name: 'Armazenagem',
    description: 'Silos e armazéns',
    icon: <LayoutDashboard className="w-5 h-5" />,
    tagPatterns: ['SILO', 'ARM', 'NIVEL'],
    alertThresholds: {
      'SILO01_NIVEL': { low: 10, high: 90, lowLow: 5, highHigh: 95 },
      'SILO01_TEMP': { high: 35, highHigh: 40 },
      'SILO01_UMIDADE': { high: 14, highHigh: 16 }
    }
  },
  {
    id: 'shipment',
    name: 'Expedição',
    description: 'Carregamento de navios e caminhões',
    icon: <TrendingUp className="w-5 h-5" />,
    tagPatterns: ['SHIP', 'LOAD', 'EXPEDIC'],
    alertThresholds: {
      'SHIPLOADER_VAZAO': { low: 500, high: 2500 },
      'SHIPLOADER_CORRENTE': { high: 300, highHigh: 350 }
    }
  }
];

// ========================================
// Quick Stats Component
// ========================================

interface QuickStatsProps {
  processHealth: ReturnType<typeof useProcessHealth>;
}

const QuickStats: React.FC<QuickStatsProps> = ({ processHealth }) => {
  const tagCount = Object.keys(processHealth.tags).length;
  const healthyCount = Object.values(processHealth.tags).filter(t => t.status === 'healthy').length;
  const warningCount = Object.values(processHealth.tags).filter(t => t.status === 'warning').length;
  const criticalCount = Object.values(processHealth.tags).filter(t => t.status === 'critical').length;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
            <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Tags Monitorados</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{tagCount}</p>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
            <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Normal</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">{healthyCount}</p>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Em Alerta</p>
            <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{warningCount}</p>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
            <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Crítico</p>
            <p className="text-2xl font-bold text-red-600 dark:text-red-400">{criticalCount}</p>
          </div>
        </div>
      </div>

    </div>
  );
};

// ========================================
// Area Card Component
// ========================================

interface AreaCardProps {
  area: ProcessArea;
  isSelected: boolean;
  onClick: () => void;
  status: HealthStatus;
  tagCount: number;
}

const AreaCard: React.FC<AreaCardProps> = ({
  area,
  isSelected,
  onClick,
  status,
  tagCount
}) => {
  const statusColors: Record<HealthStatus, string> = {
    healthy: 'border-green-500 bg-green-50 dark:bg-green-900/10',
    warning: 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10',
    critical: 'border-red-500 bg-red-50 dark:bg-red-900/10',
    unknown: 'border-gray-400 bg-gray-50 dark:bg-gray-800'
  };

  const statusDot: Record<HealthStatus, string> = {
    healthy: 'bg-green-500',
    warning: 'bg-yellow-500',
    critical: 'bg-red-500 animate-pulse',
    unknown: 'bg-gray-400'
  };

  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
        isSelected
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-md'
          : `${statusColors[status]} hover:shadow-md`
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${
            isSelected
              ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400'
              : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
          }`}>
            {area.icon}
          </div>
          <div>
            <h3 className="font-medium text-gray-900 dark:text-white">
              {area.name}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {area.description}
            </p>
          </div>
        </div>
        <div className={`w-3 h-3 rounded-full ${statusDot[status]}`} />
      </div>

      <div className="flex items-center gap-4 mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
        <span className="text-sm text-gray-600 dark:text-gray-400">
          <span className="font-medium">{tagCount}</span> tags
        </span>
      </div>
    </button>
  );
};

// ========================================
// Main Page Component
// ========================================

export const ProcessMonitoringPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedArea, setSelectedArea] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'areas' | 'full' | 'ai'>('areas');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [refreshRate, setRefreshRate] = useState(2000);

  // Global process health for stats
  const globalHealth = useProcessHealth({
    refreshInterval: refreshRate,
    enableAnomalyDetection: true
  });

  // Navigate to alarms page
  const handleNavigateToAlarms = () => {
    navigate('/alarms');
  };

  // Calculate area status based on tags
  const getAreaStatus = (area: ProcessArea): { status: HealthStatus; tagCount: number; alertCount: number } => {
    const areaTags = Object.values(globalHealth.tags).filter(tag =>
      area.tagPatterns.some(pattern =>
        tag.tagId.toUpperCase().includes(pattern.toUpperCase())
      )
    );

    const areaAlerts = globalHealth.alerts.filter(alert =>
      alert.tagId && area.tagPatterns.some(pattern =>
        alert.tagId!.toUpperCase().includes(pattern.toUpperCase())
      )
    ).filter(a => !a.acknowledged);

    let status: HealthStatus = 'healthy';
    if (areaTags.some(t => t.status === 'critical')) status = 'critical';
    else if (areaTags.some(t => t.status === 'warning')) status = 'warning';
    else if (areaTags.length === 0) status = 'unknown';

    return {
      status,
      tagCount: areaTags.length,
      alertCount: areaAlerts.length
    };
  };

  // Toggle fullscreen
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  // Get selected area config
  const selectedAreaConfig = selectedArea
    ? processAreas.find(a => a.id === selectedArea)
    : null;

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`p-2 rounded-lg ${
                globalHealth.overallStatus === 'critical'
                  ? 'bg-red-100 dark:bg-red-900/30'
                  : globalHealth.overallStatus === 'warning'
                    ? 'bg-yellow-100 dark:bg-yellow-900/30'
                    : 'bg-green-100 dark:bg-green-900/30'
              }`}>
                <Activity className={`w-6 h-6 ${
                  globalHealth.overallStatus === 'critical'
                    ? 'text-red-600 dark:text-red-400'
                    : globalHealth.overallStatus === 'warning'
                      ? 'text-yellow-600 dark:text-yellow-400'
                      : 'text-green-600 dark:text-green-400'
                }`} />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  Monitoramento de Processo
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Supervisão em tempo real com detecção de anomalias
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* View mode toggle */}
              <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('areas')}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                    viewMode === 'areas'
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                      : 'text-gray-600 dark:text-gray-400'
                  }`}
                >
                  Áreas
                </button>
                <button
                  onClick={() => setViewMode('full')}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                    viewMode === 'full'
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                      : 'text-gray-600 dark:text-gray-400'
                  }`}
                >
                  Completo
                </button>
                <button
                  onClick={() => setViewMode('ai')}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors flex items-center gap-1 ${
                    viewMode === 'ai'
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                      : 'text-gray-600 dark:text-gray-400'
                  }`}
                >
                  <Bot className="w-4 h-4" />
                  IA
                </button>
              </div>

              {/* Refresh rate */}
              <select
                value={refreshRate}
                onChange={(e) => setRefreshRate(Number(e.target.value))}
                className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 border-0 rounded-lg text-sm"
              >
                <option value={1000}>1s</option>
                <option value={2000}>2s</option>
                <option value={5000}>5s</option>
                <option value={10000}>10s</option>
              </select>

              {/* Fullscreen */}
              <button
                onClick={toggleFullscreen}
                className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                title={isFullscreen ? 'Sair do modo tela cheia' : 'Modo tela cheia'}
              >
                {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
              </button>

              {/* Refresh */}
              <button
                onClick={globalHealth.refresh}
                disabled={globalHealth.isLoading}
                className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50"
                title="Atualizar"
              >
                <RefreshCw className={`w-5 h-5 ${globalHealth.isLoading ? 'animate-spin' : ''}`} />
              </button>

              {/* Connection status */}
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${
                globalHealth.connectionStatus === 'connected'
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                  : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  globalHealth.connectionStatus === 'connected'
                    ? 'bg-green-500'
                    : 'bg-red-500 animate-pulse'
                }`} />
                <span className="text-sm font-medium">
                  {globalHealth.connectionStatus === 'connected' ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Quick stats */}
        <div className="mb-6">
          <QuickStats processHealth={globalHealth} />
        </div>

        {viewMode === 'areas' && (
          <div className="grid grid-cols-12 gap-6">
            {/* Area selector */}
            <div className="col-span-12 lg:col-span-3">
              <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Áreas do Processo
                </h2>
                <div className="space-y-3">
                  {processAreas.map(area => {
                    const areaStats = getAreaStatus(area);
                    return (
                      <AreaCard
                        key={area.id}
                        area={area}
                        isSelected={selectedArea === area.id}
                        onClick={() => setSelectedArea(area.id === selectedArea ? null : area.id)}
                        status={areaStats.status}
                        tagCount={areaStats.tagCount}
                      />
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Area detail or overview */}
            <div className="col-span-12 lg:col-span-9">
              {selectedAreaConfig ? (
                <div className="space-y-4">
                  <ProcessMonitoringPanel
                    title={`Monitoramento - ${selectedAreaConfig.name}`}
                    alertThresholds={selectedAreaConfig.alertThresholds}
                    refreshInterval={refreshRate}
                    showKPIs={true}
                    showAlerts={false}
                  />
                  {/* Link para página de alarmes */}
                  <button
                    onClick={handleNavigateToAlarms}
                    className="w-full py-3 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md hover:ring-2 hover:ring-blue-500 transition-all flex items-center justify-center gap-2 text-blue-600 dark:text-blue-400 font-medium"
                  >
                    <Bell className="w-5 h-5" />
                    Ver Alarmes Ativos e Histórico
                    <ExternalLink className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
                  <div className="text-center py-12">
                    <LayoutDashboard className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                      Selecione uma área
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400">
                      Clique em uma área à esquerda para ver os detalhes do monitoramento
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {viewMode === 'full' && (
          <div className="space-y-4">
            <ProcessMonitoringPanel
              title="Visão Completa do Processo"
              refreshInterval={refreshRate}
              showKPIs={true}
              showAlerts={false}
            />
            {/* Link para página de alarmes */}
            <button
              onClick={handleNavigateToAlarms}
              className="w-full py-3 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md hover:ring-2 hover:ring-blue-500 transition-all flex items-center justify-center gap-2 text-blue-600 dark:text-blue-400 font-medium"
            >
              <Bell className="w-5 h-5" />
              Ver Alarmes Ativos e Histórico
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        )}

        {viewMode === 'ai' && (
          <div className="space-y-6">
            {/* ML Insights Panel - Consome os 6 modelos ML treinados */}
            <MLInsightsPanel
              timeRange="last_7_days"
              autoRefresh={false}
              refreshInterval={300}
            />

            {/* Process monitoring - uses Gateway API */}
            <ProcessMonitoringPanel
              title="Monitoramento em Tempo Real"
              refreshInterval={Math.max(refreshRate, 5000)}
              showKPIs={true}
              showAlerts={false}
            />

            {/* Link para página de alarmes */}
            <button
              onClick={handleNavigateToAlarms}
              className="w-full py-3 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md hover:ring-2 hover:ring-blue-500 transition-all flex items-center justify-center gap-2 text-blue-600 dark:text-blue-400 font-medium"
            >
              <Bell className="w-5 h-5" />
              Ver Alarmes Ativos e Histórico
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        )}
      </main>

      {/* Footer with last update */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-2 px-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Última atualização: {globalHealth.lastUpdate?.toLocaleTimeString() ?? 'Aguardando...'}
          </div>
          <div className="flex items-center gap-4">
            <span>Refresh: {refreshRate / 1000}s</span>
            <span>{Object.keys(globalHealth.tags).length} tags monitorados</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default ProcessMonitoringPage;
