/**
 * InsightCard Component
 * Displays a single AI-generated insight
 */

import React from 'react';
import {
  Insight,
  getSeverityColor,
  getCategoryIcon,
  getCategoryLabel,
  getSeverityLabel,
  formatTimestamp
} from '../api/insights';

interface InsightCardProps {
  insight: Insight;
  onDismiss?: (insightId: string) => void;
  compact?: boolean;
}

export const InsightCard: React.FC<InsightCardProps> = ({
  insight,
  onDismiss,
  compact = false
}) => {
  const severityClass = getSeverityColor(insight.severity);
  const categoryIcon = getCategoryIcon(insight.category);

  if (compact) {
    return (
      <div className={`p-3 rounded-lg border ${severityClass} mb-2`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">{categoryIcon}</span>
              <span className="font-semibold text-sm">{insight.title}</span>
            </div>
            <p className="text-xs opacity-80">{insight.description}</p>
            <span className="text-xs opacity-60 mt-1 block">
              {formatTimestamp(insight.timestamp)}
            </span>
          </div>
          {onDismiss && (
            <button
              onClick={() => onDismiss(insight.id)}
              className="ml-2 text-gray-400 hover:text-gray-600"
              title="Dismiss"
            >
              ✕
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={`p-4 rounded-lg border-2 ${severityClass} shadow-sm hover:shadow-md transition-shadow`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{categoryIcon}</span>
          <div>
            <h3 className="font-bold text-lg">{insight.title}</h3>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs font-medium px-2 py-1 rounded-full bg-white bg-opacity-50">
                {getCategoryLabel(insight.category)}
              </span>
              <span className="text-xs font-medium px-2 py-1 rounded-full bg-white bg-opacity-50">
                {getSeverityLabel(insight.severity)}
              </span>
            </div>
          </div>
        </div>
        {onDismiss && (
          <button
            onClick={() => onDismiss(insight.id)}
            className="text-gray-400 hover:text-gray-600 p-1"
            title="Dismiss insight"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Description */}
      <p className="text-sm mb-3">{insight.description}</p>

      {/* Metrics (if any) */}
      {insight.metrics && Object.keys(insight.metrics).length > 0 && (
        <div className="mb-3 p-2 bg-white bg-opacity-30 rounded">
          <p className="text-xs font-semibold mb-1">Métricas:</p>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(insight.metrics).map(([key, value]) => (
              <div key={key} className="text-xs">
                <span className="font-medium">{key}:</span>{' '}
                <span>{typeof value === 'number' ? value.toFixed(2) : String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {insight.recommendations && insight.recommendations.length > 0 && (
        <div className="mb-3">
          <p className="text-xs font-semibold mb-2">Recomendações:</p>
          <ul className="list-disc list-inside space-y-1">
            {insight.recommendations.map((rec, idx) => (
              <li key={idx} className="text-xs">{rec}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs opacity-70 pt-2 border-t border-current border-opacity-20">
        <span>{formatTimestamp(insight.timestamp)}</span>
        {insight.tags && insight.tags.length > 0 && (
          <span>{insight.tags.length} tag(s) relacionada(s)</span>
        )}
      </div>
    </div>
  );
};

export default InsightCard;
