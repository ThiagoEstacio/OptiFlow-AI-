/**
 * KPI Card Widget - Professional dashboard KPI display
 * Features:
 * - Primary value with unit
 * - Comparison value (previous period, target, etc)
 * - Trend indicator (up/down/neutral)
 * - Sparkline mini chart
 * - Color-coded status
 * - Configurable themes
 */

import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: number | string;
  unit?: string;
  previousValue?: number;
  target?: number;
  trend?: 'up' | 'down' | 'neutral';
  trendPercentage?: number;
  sparklineData?: number[];
  status?: 'good' | 'warning' | 'critical' | 'neutral';
  format?: 'number' | 'percentage' | 'currency';
  decimals?: number;
  icon?: React.ReactNode;
  theme?: 'default' | 'minimal' | 'modern' | 'industrial';
  size?: 'sm' | 'md' | 'lg';
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  unit = '',
  previousValue,
  target,
  trend,
  trendPercentage,
  sparklineData,
  status = 'neutral',
  format = 'number',
  decimals = 1,
  icon,
  theme = 'default',
  size = 'md',
}) => {
  // Format value based on type
  const formatValue = (val: number | string): string => {
    if (typeof val === 'string') return val;

    switch (format) {
      case 'percentage':
        return `${val.toFixed(decimals)}%`;
      case 'currency':
        return `$${val.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
      case 'number':
      default:
        return val.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
    }
  };

  // Calculate trend if not provided
  const calculatedTrend = trend || (previousValue !== undefined && typeof value === 'number'
    ? value > previousValue ? 'up' : value < previousValue ? 'down' : 'neutral'
    : 'neutral');

  // Calculate trend percentage if not provided
  const calculatedTrendPercentage = trendPercentage !== undefined ? trendPercentage :
    (previousValue !== undefined && typeof value === 'number' && previousValue !== 0
      ? ((value - previousValue) / previousValue) * 100
      : 0);

  // Status colors
  const statusColors = {
    good: 'border-green-500 bg-green-50',
    warning: 'border-yellow-500 bg-yellow-50',
    critical: 'border-red-500 bg-red-50',
    neutral: 'border-gray-300 bg-white',
  };

  const statusTextColors = {
    good: 'text-green-700',
    warning: 'text-yellow-700',
    critical: 'text-red-700',
    neutral: 'text-gray-700',
  };

  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600',
  };

  // Size classes
  const sizeClasses = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  const valueSizeClasses = {
    sm: 'text-2xl',
    md: 'text-3xl',
    lg: 'text-4xl',
  };

  // Render sparkline (simple SVG)
  const renderSparkline = () => {
    if (!sparklineData || sparklineData.length === 0) return null;

    const width = 100;
    const height = 30;
    const max = Math.max(...sparklineData);
    const min = Math.min(...sparklineData);
    const range = max - min || 1;

    const points = sparklineData.map((val, i) => {
      const x = (i / (sparklineData.length - 1)) * width;
      const y = height - ((val - min) / range) * height;
      return `${x},${y}`;
    }).join(' ');

    return (
      <svg className="w-24 h-8 ml-auto" viewBox={`0 0 ${width} ${height}`}>
        <polyline
          points={points}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className={trendColors[calculatedTrend]}
        />
      </svg>
    );
  };

  return (
    <div className={`
      border-l-4 rounded-lg shadow-sm hover:shadow-md transition-shadow
      ${statusColors[status]} ${sizeClasses[size]}
      h-full flex flex-col
    `}>
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <h3 className="text-sm font-medium text-gray-600 uppercase tracking-wide">
            {title}
          </h3>
        </div>
        {icon && (
          <div className={`ml-2 ${statusTextColors[status]}`}>
            {icon}
          </div>
        )}
      </div>

      {/* Main Value */}
      <div className="flex-1 flex items-center">
        <div className="flex-1">
          <div className={`font-bold ${valueSizeClasses[size]} ${statusTextColors[status]}`}>
            {formatValue(value)}
            {unit && <span className="text-lg ml-1 font-normal">{unit}</span>}
          </div>
        </div>
        {renderSparkline()}
      </div>

      {/* Footer - Trend & Comparison */}
      <div className="mt-3 flex items-center justify-between text-sm">
        {/* Trend indicator */}
        {calculatedTrendPercentage !== 0 && (
          <div className={`flex items-center font-medium ${trendColors[calculatedTrend]}`}>
            {calculatedTrend === 'up' && <TrendingUp className="w-4 h-4 mr-1" />}
            {calculatedTrend === 'down' && <TrendingDown className="w-4 h-4 mr-1" />}
            {calculatedTrend === 'neutral' && <Minus className="w-4 h-4 mr-1" />}
            <span>
              {Math.abs(calculatedTrendPercentage).toFixed(1)}%
            </span>
          </div>
        )}

        {/* Comparison or target */}
        {(previousValue !== undefined || target !== undefined) && (
          <div className="text-gray-500 text-xs">
            {previousValue !== undefined && (
              <span>vs prev: {formatValue(previousValue)}</span>
            )}
            {target !== undefined && (
              <span>target: {formatValue(target)}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
