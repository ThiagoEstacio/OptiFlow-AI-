/**
 * Health Score Widget
 * Displays asset health score with visual indicators
 */

import React, { useState, useEffect } from 'react';
import {
  Heart,
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  Activity,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import axios from 'axios';

interface HealthScoreWidgetProps {
  assetId?: string;
  title?: string;
  showDetails?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

interface HealthData {
  asset_id: string;
  asset_name: string;
  health_score: number;
  status: 'excellent' | 'good' | 'fair' | 'poor' | 'critical';
  attributes_count: number;
  issues_count: number;
  warnings_count: number;
  issues?: string[];
  warnings?: string[];
}

const STATUS_CONFIG = {
  excellent: {
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-50 dark:bg-green-900/20',
    border: 'border-green-500',
    icon: CheckCircle,
    label: 'Excelente',
  },
  good: {
    color: 'text-green-500 dark:text-green-400',
    bg: 'bg-green-50 dark:bg-green-900/20',
    border: 'border-green-400',
    icon: TrendingUp,
    label: 'Bom',
  },
  fair: {
    color: 'text-yellow-600 dark:text-yellow-400',
    bg: 'bg-yellow-50 dark:bg-yellow-900/20',
    border: 'border-yellow-500',
    icon: Activity,
    label: 'Regular',
  },
  poor: {
    color: 'text-orange-600 dark:text-orange-400',
    bg: 'bg-orange-50 dark:bg-orange-900/20',
    border: 'border-orange-500',
    icon: AlertTriangle,
    label: 'Ruim',
  },
  critical: {
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-500',
    icon: AlertCircle,
    label: 'Crítico',
  },
};

export const HealthScoreWidget: React.FC<HealthScoreWidgetProps> = ({
  assetId,
  title = 'Health Score',
  showDetails = true,
  size = 'md',
}) => {
  const [healthData, setHealthData] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (assetId) {
      fetchHealthScore();
      // Refresh every 30 seconds
      const interval = setInterval(fetchHealthScore, 30000);
      return () => clearInterval(interval);
    }
  }, [assetId]);

  const fetchHealthScore = async () => {
    if (!assetId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/assets/${assetId}/health`
      );
      setHealthData(response.data);
    } catch (err: any) {
      console.error('Error fetching health score:', err);
      setError(err.message || 'Failed to fetch health score');
    } finally {
      setLoading(false);
    }
  };

  if (!assetId) {
    return (
      <div className="flex items-center justify-center h-full p-4 text-gray-500 dark:text-gray-400">
        <div className="text-center">
          <Heart className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p className="text-sm">Selecione um asset para ver o Health Score</p>
        </div>
      </div>
    );
  }

  if (loading && !healthData) {
    return (
      <div className="flex items-center justify-center h-full p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full p-4 text-red-500">
        <div className="text-center">
          <AlertCircle className="w-8 h-8 mx-auto mb-2" />
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (!healthData) {
    return null;
  }

  const status = healthData.status;
  const config = STATUS_CONFIG[status];
  const StatusIcon = config.icon;
  const score = healthData.health_score;

  // Size configurations
  const sizeClasses = {
    sm: {
      container: 'p-3',
      score: 'text-3xl',
      icon: 'w-6 h-6',
      title: 'text-sm',
      details: 'text-xs',
    },
    md: {
      container: 'p-4',
      score: 'text-5xl',
      icon: 'w-8 h-8',
      title: 'text-base',
      details: 'text-sm',
    },
    lg: {
      container: 'p-6',
      score: 'text-7xl',
      icon: 'w-12 h-12',
      title: 'text-lg',
      details: 'text-base',
    },
  };

  const sizes = sizeClasses[size];

  return (
    <div className={`h-full ${config.bg} rounded-lg border-2 ${config.border} ${sizes.container}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className={`font-semibold ${sizes.title} text-gray-900 dark:text-white`}>
          {title}
        </h3>
        {loading && (
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
        )}
      </div>

      {/* Main Score */}
      <div className="flex items-center justify-center mb-4">
        <div className="text-center">
          <div className={`${sizes.score} font-bold ${config.color} leading-none`}>
            {score.toFixed(1)}
          </div>
          <div className={`text-gray-600 dark:text-gray-400 mt-1 ${sizes.details}`}>
            / 100
          </div>
        </div>
      </div>

      {/* Status Badge */}
      <div className="flex items-center justify-center mb-4">
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${config.bg} border ${config.border}`}>
          <StatusIcon className={`${sizes.icon} ${config.color}`} />
          <span className={`font-medium ${config.color} ${sizes.details}`}>
            {config.label}
          </span>
        </div>
      </div>

      {/* Details */}
      {showDetails && (
        <>
          {/* Asset Name */}
          <div className="text-center mb-3">
            <p className={`font-medium text-gray-700 dark:text-gray-300 ${sizes.details}`}>
              {healthData.asset_name}
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-2 mb-3">
            <div className="text-center">
              <div className={`text-gray-900 dark:text-white font-bold ${sizes.details}`}>
                {healthData.attributes_count}
              </div>
              <div className={`text-gray-500 dark:text-gray-400 text-xs`}>
                Atributos
              </div>
            </div>
            <div className="text-center">
              <div className={`text-orange-600 dark:text-orange-400 font-bold ${sizes.details}`}>
                {healthData.warnings_count}
              </div>
              <div className={`text-gray-500 dark:text-gray-400 text-xs`}>
                Avisos
              </div>
            </div>
            <div className="text-center">
              <div className={`text-red-600 dark:text-red-400 font-bold ${sizes.details}`}>
                {healthData.issues_count}
              </div>
              <div className={`text-gray-500 dark:text-gray-400 text-xs`}>
                Críticos
              </div>
            </div>
          </div>

          {/* Issues */}
          {healthData.issues && healthData.issues.length > 0 && (
            <div className="mt-3 p-2 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
              <p className="text-xs font-medium text-red-800 dark:text-red-200 mb-1">
                🚨 Problemas Críticos:
              </p>
              <ul className="space-y-1">
                {healthData.issues.slice(0, 3).map((issue, idx) => (
                  <li key={idx} className="text-xs text-red-700 dark:text-red-300">
                    • {issue}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Warnings */}
          {healthData.warnings && healthData.warnings.length > 0 && !healthData.issues?.length && (
            <div className="mt-3 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded border border-yellow-200 dark:border-yellow-800">
              <p className="text-xs font-medium text-yellow-800 dark:text-yellow-200 mb-1">
                ⚠️ Avisos:
              </p>
              <ul className="space-y-1">
                {healthData.warnings.slice(0, 3).map((warning, idx) => (
                  <li key={idx} className="text-xs text-yellow-700 dark:text-yellow-300">
                    • {warning}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      {/* Progress Bar */}
      <div className="mt-3 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ${
            status === 'excellent' || status === 'good'
              ? 'bg-green-500'
              : status === 'fair'
              ? 'bg-yellow-500'
              : status === 'poor'
              ? 'bg-orange-500'
              : 'bg-red-500'
          }`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
};

export default HealthScoreWidget;
