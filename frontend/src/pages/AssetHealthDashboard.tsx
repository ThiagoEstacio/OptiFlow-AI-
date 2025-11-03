/**
 * Asset Health Dashboard
 *
 * Comprehensive overview of asset health across the entire hierarchy
 * Displays health scores, status distribution, and problematic assets
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Filter,
  Search,
  Download,
  Eye,
  BarChart3,
} from 'lucide-react';
import { useAssets, AssetType } from '../contexts/AssetContext';
import axios from 'axios';
import { HealthBadge } from '../components/DashboardBuilder/HealthBadge';

// Health status type
type HealthStatus = 'excellent' | 'good' | 'fair' | 'poor' | 'critical' | 'unknown';

// Health data interface
interface AssetHealthData {
  asset_id: string;
  asset_name: string;
  asset_type: AssetType;
  health_score: number;
  status: HealthStatus;
  issues_count: number;
  warnings_count: number;
  attributes_count: number;
  last_updated?: string;
}

// Overview statistics interface
interface HealthOverview {
  total_assets: number;
  average_health_score: number;
  status_distribution: Record<HealthStatus, number>;
  critical_assets: number;
  poor_assets: number;
  assets_with_issues: number;
  assets_with_warnings: number;
}

// Status configuration
const STATUS_CONFIG = {
  excellent: {
    label: 'Excelente',
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-50 dark:bg-green-900/20',
    border: 'border-green-200 dark:border-green-800',
    icon: CheckCircle,
  },
  good: {
    label: 'Bom',
    color: 'text-green-500 dark:text-green-400',
    bg: 'bg-green-50 dark:bg-green-900/20',
    border: 'border-green-200 dark:border-green-800',
    icon: CheckCircle,
  },
  fair: {
    label: 'Regular',
    color: 'text-yellow-600 dark:text-yellow-400',
    bg: 'bg-yellow-50 dark:bg-yellow-900/20',
    border: 'border-yellow-200 dark:border-yellow-800',
    icon: Activity,
  },
  poor: {
    label: 'Ruim',
    color: 'text-orange-600 dark:text-orange-400',
    bg: 'bg-orange-50 dark:bg-orange-900/20',
    border: 'border-orange-200 dark:border-orange-800',
    icon: AlertTriangle,
  },
  critical: {
    label: 'Crítico',
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    icon: AlertCircle,
  },
  unknown: {
    label: 'Desconhecido',
    color: 'text-gray-600 dark:text-gray-400',
    bg: 'bg-gray-50 dark:bg-gray-900/20',
    border: 'border-gray-200 dark:border-gray-800',
    icon: Activity,
  },
};

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const AssetHealthDashboard: React.FC = () => {
  const { assets, fetchAssets, selectAsset } = useAssets();

  // State
  const [overview, setOverview] = useState<HealthOverview | null>(null);
  const [healthData, setHealthData] = useState<AssetHealthData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<HealthStatus | 'all'>('all');
  const [typeFilter, setTypeFilter] = useState<AssetType | 'all'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'score' | 'issues'>('score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  // Fetch health data
  const fetchHealthData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch overview
      const overviewResponse = await axios.get(`${API_BASE_URL}/assets/health/overview`);
      setOverview(overviewResponse.data);

      // Fetch health for all assets
      const healthPromises = assets
        .filter((asset) => asset.is_active && (asset.attributes_count || 0) > 0)
        .map(async (asset) => {
          try {
            const response = await axios.get(`${API_BASE_URL}/assets/${asset.id}/health`);
            return {
              asset_id: asset.id,
              asset_name: asset.name,
              asset_type: asset.asset_type,
              health_score: response.data.health_score,
              status: response.data.status,
              issues_count: response.data.issues_count,
              warnings_count: response.data.warnings_count,
              attributes_count: asset.attributes_count || 0,
              last_updated: response.data.timestamp,
            };
          } catch (err) {
            console.error(`Error fetching health for asset ${asset.id}:`, err);
            return null;
          }
        });

      const healthResults = await Promise.all(healthPromises);
      const validHealthData = healthResults.filter((data) => data !== null) as AssetHealthData[];
      setHealthData(validHealthData);
    } catch (err: any) {
      console.error('Error fetching health data:', err);
      setError(err.message || 'Failed to fetch health data');
    } finally {
      setLoading(false);
    }
  };

  // Load data on mount and when assets change
  useEffect(() => {
    if (assets.length > 0) {
      fetchHealthData();
    }
  }, [assets]);

  // Auto-refresh every 60 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (assets.length > 0) {
        fetchHealthData();
      }
    }, 60000);

    return () => clearInterval(interval);
  }, [assets]);

  // Filter and sort health data
  const filteredAndSortedData = useMemo(() => {
    let filtered = healthData;

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((data) => data.status === statusFilter);
    }

    // Type filter
    if (typeFilter !== 'all') {
      filtered = filtered.filter((data) => data.asset_type === typeFilter);
    }

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter((data) =>
        data.asset_name.toLowerCase().includes(term)
      );
    }

    // Sort
    const sorted = [...filtered].sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case 'name':
          comparison = a.asset_name.localeCompare(b.asset_name);
          break;
        case 'score':
          comparison = a.health_score - b.health_score;
          break;
        case 'issues':
          comparison = a.issues_count - b.issues_count;
          break;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return sorted;
  }, [healthData, statusFilter, typeFilter, searchTerm, sortBy, sortOrder]);

  // Calculate statistics from filtered data
  const filteredStats = useMemo(() => {
    if (filteredAndSortedData.length === 0) {
      return {
        avgScore: 0,
        totalIssues: 0,
        totalWarnings: 0,
        criticalCount: 0,
        poorCount: 0,
      };
    }

    const avgScore =
      filteredAndSortedData.reduce((sum, data) => sum + data.health_score, 0) /
      filteredAndSortedData.length;

    const totalIssues = filteredAndSortedData.reduce(
      (sum, data) => sum + data.issues_count,
      0
    );

    const totalWarnings = filteredAndSortedData.reduce(
      (sum, data) => sum + data.warnings_count,
      0
    );

    const criticalCount = filteredAndSortedData.filter(
      (data) => data.status === 'critical'
    ).length;

    const poorCount = filteredAndSortedData.filter(
      (data) => data.status === 'poor'
    ).length;

    return { avgScore, totalIssues, totalWarnings, criticalCount, poorCount };
  }, [filteredAndSortedData]);

  // Handle asset selection
  const handleSelectAsset = (assetId: string) => {
    selectAsset(assetId);
    // Could also navigate to asset details page
  };

  // Export to CSV
  const handleExport = () => {
    const csv = [
      ['Asset Name', 'Type', 'Health Score', 'Status', 'Issues', 'Warnings'],
      ...filteredAndSortedData.map((data) => [
        data.asset_name,
        data.asset_type,
        data.health_score.toFixed(1),
        STATUS_CONFIG[data.status].label,
        data.issues_count,
        data.warnings_count,
      ]),
    ]
      .map((row) => row.join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `asset-health-${new Date().toISOString()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <Activity className="w-8 h-8 text-blue-600 dark:text-blue-400" />
              Asset Health Dashboard
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Monitor de saúde em tempo real para todos os assets
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleExport}
              disabled={filteredAndSortedData.length === 0}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Exportar CSV
            </button>

            <button
              onClick={fetchHealthData}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Atualizar
            </button>
          </div>
        </div>
      </div>

      {/* Overview Statistics */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {/* Average Health Score */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Score Médio
              </p>
              <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {overview.average_health_score.toFixed(1)}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              de {overview.total_assets} assets
            </p>
          </div>

          {/* Critical Assets */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-red-200 dark:border-red-800">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Assets Críticos
              </p>
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
            </div>
            <p className="text-3xl font-bold text-red-600 dark:text-red-400">
              {overview.critical_assets}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              requerem atenção imediata
            </p>
          </div>

          {/* Assets with Issues */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-orange-200 dark:border-orange-800">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Com Problemas
              </p>
              <AlertTriangle className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            </div>
            <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
              {overview.assets_with_issues}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              assets com issues
            </p>
          </div>

          {/* Assets with Warnings */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-yellow-200 dark:border-yellow-800">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Com Avisos
              </p>
              <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
            </div>
            <p className="text-3xl font-bold text-yellow-600 dark:text-yellow-400">
              {overview.assets_with_warnings}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              assets com warnings
            </p>
          </div>
        </div>
      )}

      {/* Status Distribution */}
      {overview && (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Distribuição de Status
            </h2>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {(Object.keys(STATUS_CONFIG) as HealthStatus[]).map((status) => {
              const config = STATUS_CONFIG[status];
              const count = overview.status_distribution[status] || 0;
              const percentage =
                overview.total_assets > 0
                  ? ((count / overview.total_assets) * 100).toFixed(1)
                  : '0.0';
              const Icon = config.icon;

              return (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className={`
                    p-4 rounded-lg border-2 transition-all hover:shadow-md
                    ${statusFilter === status ? 'ring-2 ring-blue-500' : ''}
                    ${config.bg} ${config.border}
                  `}
                >
                  <div className="flex items-center justify-center mb-2">
                    <Icon className={`w-6 h-6 ${config.color}`} />
                  </div>
                  <p className={`text-2xl font-bold ${config.color}`}>{count}</p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    {config.label}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {percentage}%
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Filters and Search */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar assets..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as HealthStatus | 'all')}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="all">Todos os Status</option>
            {(Object.keys(STATUS_CONFIG) as HealthStatus[]).map((status) => (
              <option key={status} value={status}>
                {STATUS_CONFIG[status].label}
              </option>
            ))}
          </select>

          {/* Type Filter */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as AssetType | 'all')}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="all">Todos os Tipos</option>
            <option value="enterprise">Empresa</option>
            <option value="site">Site</option>
            <option value="area">Área</option>
            <option value="unit">Unidade</option>
            <option value="equipment">Equipamento</option>
            <option value="component">Componente</option>
          </select>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'name' | 'score' | 'issues')}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="score">Ordenar por Score</option>
            <option value="name">Ordenar por Nome</option>
            <option value="issues">Ordenar por Issues</option>
          </select>

          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            title={sortOrder === 'asc' ? 'Crescente' : 'Decrescente'}
          >
            {sortOrder === 'asc' ? (
              <TrendingUp className="w-5 h-5" />
            ) : (
              <TrendingDown className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Filtered Stats */}
        <div className="mt-4 flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
          <span>
            Exibindo {filteredAndSortedData.length} de {healthData.length} assets
          </span>
          {filteredAndSortedData.length > 0 && (
            <div className="flex items-center gap-4">
              <span>Média: {filteredStats.avgScore.toFixed(1)}</span>
              <span className="text-red-600 dark:text-red-400">
                {filteredStats.criticalCount} críticos
              </span>
              <span className="text-orange-600 dark:text-orange-400">
                {filteredStats.totalIssues} issues
              </span>
              <span className="text-yellow-600 dark:text-yellow-400">
                {filteredStats.totalWarnings} warnings
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Asset List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Assets
          </h2>
        </div>

        {loading && healthData.length === 0 ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Carregando dados de saúde...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12 text-red-600 dark:text-red-400">
            <AlertCircle className="w-12 h-12 mx-auto mb-4" />
            <p className="font-medium">Erro ao carregar dados</p>
            <p className="text-sm mt-2">{error}</p>
            <button
              onClick={fetchHealthData}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Tentar novamente
            </button>
          </div>
        ) : filteredAndSortedData.length === 0 ? (
          <div className="text-center py-12 text-gray-600 dark:text-gray-400">
            <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="font-medium">Nenhum asset encontrado</p>
            <p className="text-sm mt-2">Tente ajustar os filtros</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Asset
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Tipo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Health Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Issues
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Warnings
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Atributos
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {filteredAndSortedData.map((data) => {
                  const statusConfig = STATUS_CONFIG[data.status];
                  const StatusIcon = statusConfig.icon;

                  return (
                    <tr
                      key={data.asset_id}
                      className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="font-medium text-gray-900 dark:text-white">
                          {data.asset_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                          {data.asset_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 w-24">
                            <div
                              className={`h-2 rounded-full ${
                                data.health_score >= 70
                                  ? 'bg-green-500'
                                  : data.health_score >= 50
                                  ? 'bg-yellow-500'
                                  : data.health_score >= 30
                                  ? 'bg-orange-500'
                                  : 'bg-red-500'
                              }`}
                              style={{ width: `${data.health_score}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {data.health_score.toFixed(1)}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${statusConfig.bg} ${statusConfig.color}`}
                        >
                          <StatusIcon className="w-3 h-3" />
                          {statusConfig.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {data.issues_count > 0 ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300">
                            <AlertCircle className="w-3 h-3" />
                            {data.issues_count}
                          </span>
                        ) : (
                          <span className="text-gray-400 dark:text-gray-600">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {data.warnings_count > 0 ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300">
                            <AlertTriangle className="w-3 h-3" />
                            {data.warnings_count}
                          </span>
                        ) : (
                          <span className="text-gray-400 dark:text-gray-600">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {data.attributes_count}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => handleSelectAsset(data.asset_id)}
                          className="inline-flex items-center gap-1 px-3 py-1 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                          Ver
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Help Section */}
      <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
        <p className="text-sm text-blue-800 dark:text-blue-200">
          <strong>💡 Dica:</strong> Clique em um status na distribuição para filtrar rapidamente.
          Use os filtros para encontrar assets específicos que precisam de atenção.
        </p>
      </div>
    </div>
  );
};

export default AssetHealthDashboard;
