/**
 * Health Badge - Shows health status in asset tree
 * Small badge with color indicator and optional tooltip
 */

import React, { useState, useEffect } from 'react';
import { Activity, AlertCircle, AlertTriangle, CheckCircle, HelpCircle } from 'lucide-react';
import axios from 'axios';

interface HealthBadgeProps {
  assetId: string;
  showScore?: boolean;
  showTooltip?: boolean;
  size?: 'sm' | 'md';
}

interface HealthStatus {
  health_score: number;
  status: 'excellent' | 'good' | 'fair' | 'poor' | 'critical' | 'unknown';
  issues_count: number;
  warnings_count: number;
}

const STATUS_COLORS = {
  excellent: 'bg-green-500 text-white',
  good: 'bg-green-400 text-white',
  fair: 'bg-yellow-500 text-white',
  poor: 'bg-orange-500 text-white',
  critical: 'bg-red-500 text-white',
  unknown: 'bg-gray-400 text-white',
};

const STATUS_ICONS = {
  excellent: CheckCircle,
  good: CheckCircle,
  fair: Activity,
  poor: AlertTriangle,
  critical: AlertCircle,
  unknown: HelpCircle,
};

const STATUS_LABELS = {
  excellent: 'Excelente',
  good: 'Bom',
  fair: 'Regular',
  poor: 'Ruim',
  critical: 'Crítico',
  unknown: 'Desconhecido',
};

export const HealthBadge: React.FC<HealthBadgeProps> = ({
  assetId,
  showScore = true,
  showTooltip = true,
  size = 'sm',
}) => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [showTooltipState, setShowTooltipState] = useState(false);

  useEffect(() => {
    fetchHealth();
  }, [assetId]);

  const fetchHealth = async () => {
    setLoading(true);

    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/assets/${assetId}/health`
      );

      setHealth({
        health_score: response.data.health_score || 0,
        status: response.data.status || 'unknown',
        issues_count: response.data.issues_count || 0,
        warnings_count: response.data.warnings_count || 0,
      });
    } catch (error) {
      console.error('Error fetching health:', error);
      setHealth({
        health_score: 0,
        status: 'unknown',
        issues_count: 0,
        warnings_count: 0,
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading || !health) {
    return (
      <div className={`inline-flex items-center justify-center ${size === 'sm' ? 'w-6 h-6' : 'w-8 h-8'}`}>
        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-gray-400"></div>
      </div>
    );
  }

  const StatusIcon = STATUS_ICONS[health.status];
  const colorClass = STATUS_COLORS[health.status];
  const sizeClasses = size === 'sm' ? 'px-1.5 py-0.5 text-xs' : 'px-2 py-1 text-sm';
  const iconSize = size === 'sm' ? 'w-3 h-3' : 'w-4 h-4';

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => showTooltip && setShowTooltipState(true)}
      onMouseLeave={() => setShowTooltipState(false)}
    >
      {/* Badge */}
      <div
        className={`
          inline-flex items-center gap-1 rounded-full font-medium
          ${colorClass} ${sizeClasses}
        `}
      >
        <StatusIcon className={iconSize} />
        {showScore && <span>{health.health_score.toFixed(0)}</span>}
      </div>

      {/* Tooltip */}
      {showTooltip && showTooltipState && (
        <div className="absolute z-50 bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-48">
          <div className="bg-gray-900 dark:bg-gray-800 text-white text-xs rounded-lg p-3 shadow-xl">
            <div className="mb-2">
              <div className="font-semibold mb-1">Health Score</div>
              <div className="flex items-center justify-between">
                <span>{STATUS_LABELS[health.status]}</span>
                <span className="font-bold">{health.health_score.toFixed(1)}/100</span>
              </div>
            </div>

            {(health.issues_count > 0 || health.warnings_count > 0) && (
              <div className="pt-2 border-t border-gray-700 space-y-1">
                {health.issues_count > 0 && (
                  <div className="flex items-center justify-between text-red-400">
                    <span>Críticos:</span>
                    <span className="font-bold">{health.issues_count}</span>
                  </div>
                )}
                {health.warnings_count > 0 && (
                  <div className="flex items-center justify-between text-yellow-400">
                    <span>Avisos:</span>
                    <span className="font-bold">{health.warnings_count}</span>
                  </div>
                )}
              </div>
            )}

            {/* Arrow */}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
              <div className="border-4 border-transparent border-t-gray-900 dark:border-t-gray-800"></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HealthBadge;
