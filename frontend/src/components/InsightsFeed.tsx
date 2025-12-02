/**
 * InsightsFeed Component
 * Displays a feed of AI-generated insights with filtering
 */

import React, { useState, useEffect } from 'react';
import { Insight, getInsights, getInsightsSummary, InsightsSummary } from '../api/insights';
import { InsightCard } from './InsightCard';

interface InsightsFeedProps {
  compact?: boolean;
  limit?: number;
  autoRefresh?: boolean;
  refreshInterval?: number; // in seconds
  showFilters?: boolean;
}

export const InsightsFeed: React.FC<InsightsFeedProps> = ({
  compact = false,
  limit = 20,
  autoRefresh = true,
  refreshInterval = 60,
  showFilters = true
}) => {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [summary, setSummary] = useState<InsightsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<string | null>(null);

  const fetchInsights = async () => {
    try {
      // Only show loading spinner on initial load, not on refresh
      if (insights.length === 0) {
        setLoading(true);
      }
      setError(null);

      const response = await getInsights({
        category: selectedCategory || undefined,
        severity: selectedSeverity || undefined,
        limit
      });

      // Smart update: only update if insights actually changed
      // This prevents unnecessary re-renders and "flashing"
      const newInsightsJson = JSON.stringify(response.insights.map(i => i.id).sort());
      const currentInsightsJson = JSON.stringify(insights.map(i => i.id).sort());

      if (newInsightsJson !== currentInsightsJson) {
        // Merge new insights while preserving order
        // New insights appear at top with animation
        setInsights(response.insights);
      }

      // Also fetch summary
      const summaryData = await getInsightsSummary();
      setSummary(summaryData);

    } catch (err: any) {
      console.error('Error fetching insights:', err);
      setError(err.response?.data?.detail || 'Failed to load insights');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();

    if (autoRefresh) {
      const interval = setInterval(fetchInsights, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [selectedCategory, selectedSeverity, limit, autoRefresh, refreshInterval]);

  const handleDismiss = (insightId: string) => {
    // Optimistically remove from UI
    setInsights(prev => prev.filter(i => i.id !== insightId));
    // Could call API to persist dismissal
  };

  if (loading && insights.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Carregando insights...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
        <p className="font-semibold">Erro ao carregar insights</p>
        <p className="text-sm">{error}</p>
        <button
          onClick={fetchInsights}
          className="mt-2 text-sm underline hover:no-underline"
        >
          Tentar novamente
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary Stats */}
      {summary && !compact && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-xs text-blue-600 font-medium">Total de Insights</p>
            <p className="text-2xl font-bold text-blue-700">{summary.total_insights}</p>
          </div>

          {summary.by_severity.critical > 0 && (
            <div className="p-3 bg-red-50 rounded-lg border border-red-200">
              <p className="text-xs text-red-600 font-medium">Críticos</p>
              <p className="text-2xl font-bold text-red-700">{summary.by_severity.critical || 0}</p>
            </div>
          )}

          {summary.by_severity.high > 0 && (
            <div className="p-3 bg-orange-50 rounded-lg border border-orange-200">
              <p className="text-xs text-orange-600 font-medium">Alta Prioridade</p>
              <p className="text-2xl font-bold text-orange-700">{summary.by_severity.high || 0}</p>
            </div>
          )}

          {summary.by_category.anomaly > 0 && (
            <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
              <p className="text-xs text-yellow-600 font-medium">Anomalias</p>
              <p className="text-2xl font-bold text-yellow-700">{summary.by_category.anomaly || 0}</p>
            </div>
          )}
        </div>
      )}

      {/* Filters */}
      {showFilters && !compact && (
        <div className="flex flex-wrap gap-2 p-3 bg-gray-50 rounded-lg">
          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">Categoria:</label>
            <select
              value={selectedCategory || ''}
              onChange={(e) => setSelectedCategory(e.target.value || null)}
              className="px-3 py-1 text-sm border rounded focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todas</option>
              <option value="anomaly">🔍 Anomalias</option>
              <option value="optimization">⚡ Otimizações</option>
              <option value="alert">⚠️ Alertas</option>
              <option value="trend">📈 Tendências</option>
              <option value="prediction">🔮 Previsões</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">Severidade:</label>
            <select
              value={selectedSeverity || ''}
              onChange={(e) => setSelectedSeverity(e.target.value || null)}
              className="px-3 py-1 text-sm border rounded focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todas</option>
              <option value="critical">Crítico</option>
              <option value="high">Alto</option>
              <option value="medium">Médio</option>
              <option value="low">Baixo</option>
              <option value="info">Info</option>
            </select>
          </div>

          <button
            onClick={fetchInsights}
            className="ml-auto px-4 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center gap-2"
            title="Atualizar insights"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Atualizar
          </button>
        </div>
      )}

      {/* Insights List */}
      {insights.length === 0 ? (
        <div className="text-center p-8 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-gray-500 text-sm">
            {selectedCategory || selectedSeverity
              ? 'Nenhum insight encontrado com os filtros selecionados'
              : 'Nenhum insight disponível no momento'}
          </p>
          <p className="text-xs text-gray-400 mt-2">
            O Autonomous Agent gera insights a cada 60 segundos
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {insights.map(insight => (
            <InsightCard
              key={insight.id}
              insight={insight}
              onDismiss={handleDismiss}
              compact={compact}
            />
          ))}
        </div>
      )}

      {/* Auto-refresh indicator */}
      {autoRefresh && !compact && (
        <div className="text-center text-xs text-gray-400 py-2">
          <span className="inline-flex items-center gap-2">
            <span className="animate-pulse w-2 h-2 bg-green-500 rounded-full"></span>
            Auto-atualização ativa (a cada {refreshInterval}s)
          </span>
        </div>
      )}
    </div>
  );
};

export default InsightsFeed;
