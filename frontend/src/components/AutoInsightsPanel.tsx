/**
 * AutoInsightsPanel - Painel de Insights Automáticos
 *
 * Integra as 3 ferramentas principais do AI Agent:
 * 1. PCM - MTBF/MTTR (Manutenção)
 * 2. PCM Preditivo - Predição de Falhas
 * 3. Qualidade - CEP/SPC
 *
 * Refactored to use shared hooks and utilities
 */

import React, { useState, useCallback, useMemo } from 'react';
import { useAsyncData } from '../hooks/useAsyncData';
import { REFRESH_INTERVALS } from '../utils/constants';
import {
  Wrench,
  TrendingUp,
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Target,
  BarChart3,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Settings,
  Zap,
  ShieldCheck
} from 'lucide-react';
import {
  MTBFMTTRResult,
  FailurePrediction,
  SPCLimits,
  getMTBFMTTR,
  predictFailure,
  calculateSPCLimits,
  getRiskLevelColor,
  getRiskLevelIcon,
  getReliabilityColor,
  getStabilityColor,
  formatHours,
  formatPercent
} from '../api/insights';

// ========================================
// Types
// ========================================

interface Equipment {
  id: string;
  name: string;
  type?: string;
}

interface QualityTag {
  id: string;
  name: string;
  unit?: string;
  usl?: number;
  lsl?: number;
}

interface AutoInsightsPanelProps {
  equipments?: Equipment[];
  qualityTags?: QualityTag[];
  autoRefresh?: boolean;
  refreshInterval?: number; // seconds
  compact?: boolean;
  onInsightClick?: (type: string, data: any) => void;
}

// ========================================
// Sub-Components
// ========================================

const MTBFMTTRCard: React.FC<{
  data: MTBFMTTRResult | null;
  loading: boolean;
  error: string | null;
  compact?: boolean;
}> = ({ data, loading, error, compact }) => {
  const [expanded, setExpanded] = useState(!compact);

  if (loading) {
    return (
      <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 animate-pulse">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
        <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
          <AlertTriangle className="w-4 h-4" />
          <span className="text-sm font-medium">Erro ao carregar MTBF/MTTR</span>
        </div>
        <p className="text-xs text-red-500 dark:text-red-400 mt-1">{error}</p>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden ${
      data.reliability_classification === 'Crítico' ? 'ring-2 ring-red-500' : ''
    }`}>
      {/* Header */}
      <div
        className="p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${getReliabilityColor(data.reliability_classification)}`}>
              <Wrench className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">
                PCM - {data.equipment_id}
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                MTBF/MTTR • {data.duration}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {data.reliability_classification && (
              <span className={`px-2 py-1 rounded text-xs font-medium ${getReliabilityColor(data.reliability_classification)}`}>
                {data.reliability_classification}
              </span>
            )}
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {formatHours(data.mtbf_hours)}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">MTBF</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
              {formatHours(data.mttr_hours)}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">MTTR</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              {formatPercent(data.availability_percent)}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Disponibilidade</p>
          </div>
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 space-y-4">
          {/* Insights */}
          {data.insights && data.insights.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">Insights</p>
              <div className="space-y-1">
                {data.insights.map((insight, idx) => (
                  <p key={idx} className="text-sm text-gray-700 dark:text-gray-300">{insight}</p>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {data.recommendations && data.recommendations.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">Recomendações</p>
              <ul className="space-y-1">
                {data.recommendations.map((rec, idx) => (
                  <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2">
                    <span className="text-blue-500">•</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Failure History */}
          {data.failure_count > 0 && (
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                <AlertTriangle className="w-4 h-4" />
                <span>{data.failure_count} falhas no período</span>
              </div>
              <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                <Clock className="w-4 h-4" />
                <span>{data.total_downtime_hours.toFixed(1)}h de downtime</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const FailurePredictionCard: React.FC<{
  data: FailurePrediction | null;
  loading: boolean;
  error: string | null;
  compact?: boolean;
}> = ({ data, loading, error, compact }) => {
  const [expanded, setExpanded] = useState(!compact);

  if (loading) {
    return (
      <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 animate-pulse">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
        <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
          <AlertTriangle className="w-4 h-4" />
          <span className="text-sm font-medium">Erro na predição</span>
        </div>
        <p className="text-xs text-red-500 dark:text-red-400 mt-1">{error}</p>
      </div>
    );
  }

  if (!data) return null;

  const riskPercent = Math.round(data.failure_probability * 100);

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden ${
      data.overall_risk_level === 'critical' ? 'ring-2 ring-red-500' :
      data.overall_risk_level === 'high' ? 'ring-2 ring-orange-500' : ''
    }`}>
      {/* Header */}
      <div
        className="p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${getRiskLevelColor(data.overall_risk_level)}`}>
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">
                Predição - {data.equipment_id}
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Horizonte: {data.prediction_horizon}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`px-2 py-1 rounded text-xs font-medium flex items-center gap-1 ${getRiskLevelColor(data.overall_risk_level)}`}>
              <span>{getRiskLevelIcon(data.overall_risk_level)}</span>
              {data.overall_risk_level.toUpperCase()}
            </span>
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </div>

        {/* Risk Gauge */}
        <div className="mt-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-500 dark:text-gray-400">Probabilidade de Falha</span>
            <span className="text-sm font-bold">{riskPercent}%</span>
          </div>
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                riskPercent >= 70 ? 'bg-red-500' :
                riskPercent >= 50 ? 'bg-orange-500' :
                riskPercent >= 30 ? 'bg-yellow-500' :
                'bg-green-500'
              }`}
              style={{ width: `${riskPercent}%` }}
            />
          </div>
          <div className="flex items-center justify-between mt-1 text-xs text-gray-400">
            <span>Baixo</span>
            <span>Crítico</span>
          </div>
        </div>

        {/* Failure Window */}
        {data.predicted_failure_window && (
          <div className="mt-3 p-2 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
            <p className="text-xs text-red-600 dark:text-red-400 flex items-center gap-2">
              <Clock className="w-3 h-3" />
              Janela de falha: {data.predicted_failure_window.min_days}-{data.predicted_failure_window.max_days} dias
            </p>
          </div>
        )}
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 space-y-4">
          {/* Risk Factors */}
          {data.risk_factors.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">Fatores de Risco</p>
              <div className="space-y-2">
                {data.risk_factors.map((factor, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded">
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">{factor.tag_id}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{factor.primary_concern}</p>
                    </div>
                    <div className={`px-2 py-1 rounded text-xs font-bold ${
                      factor.risk_score >= 0.7 ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                      factor.risk_score >= 0.5 ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                      'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                    }`}>
                      {Math.round(factor.risk_score * 100)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {data.recommendations && data.recommendations.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">Ações Recomendadas</p>
              <ul className="space-y-1">
                {data.recommendations.map((rec, idx) => (
                  <li key={idx} className="text-sm text-gray-700 dark:text-gray-300">{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Confidence */}
          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
            <ShieldCheck className="w-4 h-4" />
            Confiança da predição: {Math.round(data.confidence * 100)}%
          </div>
        </div>
      )}
    </div>
  );
};

const SPCCard: React.FC<{
  data: SPCLimits | null;
  loading: boolean;
  error: string | null;
  compact?: boolean;
}> = ({ data, loading, error, compact }) => {
  const [expanded, setExpanded] = useState(!compact);

  if (loading) {
    return (
      <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 animate-pulse">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
        <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
          <AlertTriangle className="w-4 h-4" />
          <span className="text-sm font-medium">Erro no CEP</span>
        </div>
        <p className="text-xs text-red-500 dark:text-red-400 mt-1">{error}</p>
      </div>
    );
  }

  if (!data) return null;

  const stabilityAssessment = data.stability_assessment || {
    status: 'Desconhecido',
    out_of_control_count: 0,
    out_of_control_percentage: 0
  };
  const stability = stabilityAssessment.status || 'Desconhecido';
  const cpk = data.capability_indices?.cpk;

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden ${
      stability === 'Instável' ? 'ring-2 ring-red-500' : ''
    }`}>
      {/* Header */}
      <div
        className="p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${getStabilityColor(stability)}`}>
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">
                CEP - {data.tag_id}
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {data.chart_type} • {data.sample_size} amostras
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`px-2 py-1 rounded text-xs font-medium ${getStabilityColor(stability)}`}>
              {stability}
            </span>
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="text-center">
            <p className="text-lg font-bold text-gray-900 dark:text-white">
              {data.process_statistics?.mean?.toFixed(2) ?? 'N/A'}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Média</p>
          </div>
          <div className="text-center">
            <p className={`text-lg font-bold ${
              cpk && cpk >= 1.33 ? 'text-green-600 dark:text-green-400' :
              cpk && cpk >= 1.0 ? 'text-yellow-600 dark:text-yellow-400' :
              'text-red-600 dark:text-red-400'
            }`}>
              {cpk?.toFixed(2) || 'N/A'}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Cpk</p>
          </div>
          <div className="text-center">
            <p className={`text-lg font-bold ${
              stabilityAssessment.out_of_control_count === 0 ? 'text-green-600 dark:text-green-400' :
              'text-red-600 dark:text-red-400'
            }`}>
              {stabilityAssessment.out_of_control_count}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Fora de Controle</p>
          </div>
        </div>

        {/* Control Limits Preview */}
        {(data.control_limits?.x_bar_chart || data.control_limits?.individuals_chart) && (
          <div className="mt-3 p-2 bg-gray-50 dark:bg-gray-700/50 rounded text-xs">
            <div className="flex justify-between">
              <span className="text-red-600 dark:text-red-400">
                UCL: {(data.control_limits.x_bar_chart?.ucl || data.control_limits.individuals_chart?.ucl)?.toFixed(2)}
              </span>
              <span className="text-gray-600 dark:text-gray-400">
                CL: {(data.control_limits.x_bar_chart?.cl || data.control_limits.individuals_chart?.cl)?.toFixed(2)}
              </span>
              <span className="text-blue-600 dark:text-blue-400">
                LCL: {(data.control_limits.x_bar_chart?.lcl || data.control_limits.individuals_chart?.lcl)?.toFixed(2)}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 space-y-4">
          {/* Capability Indices */}
          {data.capability_indices && (
            <div>
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">Índices de Capabilidade</p>
              <div className="grid grid-cols-4 gap-2">
                <div className="p-2 bg-gray-50 dark:bg-gray-700/50 rounded text-center">
                  <p className="text-sm font-bold">{data.capability_indices.cp.toFixed(2)}</p>
                  <p className="text-xs text-gray-500">Cp</p>
                </div>
                <div className="p-2 bg-gray-50 dark:bg-gray-700/50 rounded text-center">
                  <p className="text-sm font-bold">{data.capability_indices.cpk.toFixed(2)}</p>
                  <p className="text-xs text-gray-500">Cpk</p>
                </div>
                <div className="p-2 bg-gray-50 dark:bg-gray-700/50 rounded text-center">
                  <p className="text-sm font-bold">{data.capability_indices.sigma_level.toFixed(1)}σ</p>
                  <p className="text-xs text-gray-500">Sigma</p>
                </div>
                <div className="p-2 bg-gray-50 dark:bg-gray-700/50 rounded text-center">
                  <p className="text-sm font-bold">{data.capability_indices.ppm_estimate.toFixed(0)}</p>
                  <p className="text-xs text-gray-500">PPM</p>
                </div>
              </div>
            </div>
          )}

          {/* Insights */}
          {data.insights && data.insights.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">Insights</p>
              <div className="space-y-1">
                {data.insights.map((insight, idx) => (
                  <p key={idx} className="text-sm text-gray-700 dark:text-gray-300">{insight}</p>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {data.recommendations && data.recommendations.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">Recomendações</p>
              <ul className="space-y-1">
                {data.recommendations.map((rec, idx) => (
                  <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2">
                    <span className="text-blue-500">•</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ========================================
// Main Component
// ========================================

export const AutoInsightsPanel: React.FC<AutoInsightsPanelProps> = ({
  equipments = [],
  qualityTags = [],
  autoRefresh = true,
  refreshInterval = 60,
  compact = false,
  onInsightClick
}) => {
  const [activeTab, setActiveTab] = useState<'pcm' | 'prediction' | 'quality'>('pcm');
  const [selectedEquipment, setSelectedEquipment] = useState<string>(equipments[0]?.id || '');
  const [selectedQualityTag, setSelectedQualityTag] = useState<string>(qualityTags[0]?.id || '');

  // Track if tabs have been activated (for lazy loading)
  const [tabsEnabled, setTabsEnabled] = useState({ pcm: true, prediction: false, quality: false });

  // Get spec limits for selected quality tag
  const selectedTag = useMemo(() =>
    qualityTags.find(t => t.id === selectedQualityTag),
    [qualityTags, selectedQualityTag]
  );

  // MTBF/MTTR data using shared hook
  const {
    data: mtbfData,
    loading: mtbfLoading,
    error: mtbfError,
    refresh: refreshMTBF,
    lastUpdated: mtbfLastUpdated,
  } = useAsyncData(
    () => getMTBFMTTR(selectedEquipment),
    {
      enabled: tabsEnabled.pcm && !!selectedEquipment,
      autoRefresh,
      refreshInterval: refreshInterval * 1000,
      deps: [selectedEquipment],
    }
  );

  // Failure Prediction data using shared hook
  const {
    data: predictionData,
    loading: predictionLoading,
    error: predictionError,
    refresh: refreshPrediction,
  } = useAsyncData(
    () => predictFailure(selectedEquipment),
    {
      enabled: tabsEnabled.prediction && !!selectedEquipment,
      autoRefresh,
      refreshInterval: refreshInterval * 1000,
      deps: [selectedEquipment],
    }
  );

  // SPC/CEP data using shared hook
  const {
    data: spcData,
    loading: spcLoading,
    error: spcError,
    refresh: refreshSPC,
  } = useAsyncData(
    () => calculateSPCLimits(selectedQualityTag, {
      specificationLimits: selectedTag?.usl && selectedTag?.lsl
        ? { usl: selectedTag.usl, lsl: selectedTag.lsl }
        : undefined
    }),
    {
      enabled: tabsEnabled.quality && !!selectedQualityTag,
      autoRefresh,
      refreshInterval: refreshInterval * 1000,
      deps: [selectedQualityTag, selectedTag?.usl, selectedTag?.lsl],
    }
  );

  // Consolidated loading and error states
  const loading = { mtbf: mtbfLoading, prediction: predictionLoading, spc: spcLoading };
  const errors = { mtbf: mtbfError, prediction: predictionError, spc: spcError };
  const lastUpdate = mtbfLastUpdated;

  // Refresh all data
  const refreshAll = useCallback(async () => {
    await Promise.all([
      tabsEnabled.pcm ? refreshMTBF() : Promise.resolve(),
      tabsEnabled.prediction ? refreshPrediction() : Promise.resolve(),
      tabsEnabled.quality ? refreshSPC() : Promise.resolve(),
    ]);
  }, [tabsEnabled, refreshMTBF, refreshPrediction, refreshSPC]);

  // Handle tab click - enable lazy loading for that tab
  const handleTabClick = (tabId: typeof activeTab) => {
    setActiveTab(tabId);

    // Enable the tab if not already enabled (triggers data fetch via useAsyncData)
    if (!tabsEnabled[tabId]) {
      setTabsEnabled(prev => ({ ...prev, [tabId]: true }));
    }
  };

  // For display purposes - track which tabs have been loaded
  const initialLoaded = tabsEnabled;

  const tabs = [
    { id: 'pcm', label: 'PCM', icon: Wrench, description: 'MTBF/MTTR' },
    { id: 'prediction', label: 'Preditivo', icon: TrendingUp, description: 'Predição de Falhas' },
    { id: 'quality', label: 'Qualidade', icon: Activity, description: 'CEP/SPC' },
  ];

  return (
    <div className="bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="font-bold text-gray-900 dark:text-white">Insights Automáticos</h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                PCO • PCM • Qualidade
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {lastUpdate && (
              <span className="text-xs text-gray-400">
                Atualizado: {lastUpdate.toLocaleTimeString('pt-BR')}
              </span>
            )}
            <button
              onClick={refreshAll}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title="Atualizar"
            >
              <RefreshCw className={`w-4 h-4 text-gray-500 ${loading.mtbf || loading.prediction || loading.spc ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mt-4">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => handleTabClick(tab.id as typeof activeTab)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
              {!initialLoaded[tab.id as keyof typeof initialLoaded] && (
                <span className="text-xs text-gray-400">(clique para carregar)</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Equipment/Tag Selector */}
        <div className="mb-4">
          {(activeTab === 'pcm' || activeTab === 'prediction') && (
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Equipamento:</label>
              <select
                value={selectedEquipment}
                onChange={(e) => setSelectedEquipment(e.target.value)}
                className="flex-1 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              >
                {equipments.length === 0 && (
                  <option value="">Nenhum equipamento</option>
                )}
                {equipments.map(eq => (
                  <option key={eq.id} value={eq.id}>{eq.name}</option>
                ))}
              </select>
            </div>
          )}

          {activeTab === 'quality' && (
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Tag de Qualidade:</label>
              <select
                value={selectedQualityTag}
                onChange={(e) => setSelectedQualityTag(e.target.value)}
                className="flex-1 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              >
                {qualityTags.length === 0 && (
                  <option value="">Nenhuma tag</option>
                )}
                {qualityTags.map(tag => (
                  <option key={tag.id} value={tag.id}>{tag.name} {tag.unit ? `(${tag.unit})` : ''}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Tab Content */}
        {activeTab === 'pcm' && (
          <MTBFMTTRCard
            data={mtbfData}
            loading={loading.mtbf}
            error={errors.mtbf}
            compact={compact}
          />
        )}

        {activeTab === 'prediction' && (
          <FailurePredictionCard
            data={predictionData}
            loading={loading.prediction}
            error={errors.prediction}
            compact={compact}
          />
        )}

        {activeTab === 'quality' && (
          <SPCCard
            data={spcData}
            loading={loading.spc}
            error={errors.spc}
            compact={compact}
          />
        )}
      </div>

      {/* Auto-refresh indicator */}
      {autoRefresh && (
        <div className="px-4 pb-3 flex items-center justify-center gap-2 text-xs text-gray-400">
          <span className="animate-pulse w-2 h-2 bg-green-500 rounded-full"></span>
          Atualização automática a cada {refreshInterval}s
        </div>
      )}
    </div>
  );
};

export default AutoInsightsPanel;
