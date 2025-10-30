/**
 * Progress Widget - Professional progress/loading indicator
 * Features:
 * - Horizontal and circular/radial progress bars
 * - Color-coded by thresholds
 * - Target indicators
 * - Multiple visualization styles
 * - Animated updates
 */

import React from 'react';
import { Target, TrendingUp } from 'lucide-react';

interface ProgressWidgetProps {
  title: string;
  value: number;
  max?: number;
  min?: number;
  unit?: string;
  target?: number;
  thresholds?: {
    warning?: number;
    critical?: number;
  };
  type?: 'bar' | 'circular';
  size?: 'sm' | 'md' | 'lg';
  showPercentage?: boolean;
  showValue?: boolean;
  animated?: boolean;
  color?: string;
}

export const ProgressWidget: React.FC<ProgressWidgetProps> = ({
  title,
  value,
  max = 100,
  min = 0,
  unit = '',
  target,
  thresholds,
  type = 'bar',
  size = 'md',
  showPercentage = true,
  showValue = true,
  animated = true,
  color,
}) => {
  // Calculate percentage
  const range = max - min;
  const normalizedValue = Math.max(min, Math.min(max, value));
  const percentage = ((normalizedValue - min) / range) * 100;

  // Determine color based on thresholds
  const getColor = () => {
    if (color) return color;

    if (thresholds) {
      if (thresholds.critical !== undefined && value >= thresholds.critical) {
        return 'bg-red-500';
      }
      if (thresholds.warning !== undefined && value >= thresholds.warning) {
        return 'bg-yellow-500';
      }
    }

    return 'bg-blue-500';
  };

  const progressColor = getColor();

  // Size classes
  const sizeClasses = {
    sm: { height: 'h-2', text: 'text-sm', circle: 80 },
    md: { height: 'h-3', text: 'text-base', circle: 120 },
    lg: { height: 'h-4', text: 'text-lg', circle: 160 },
  };

  const classes = sizeClasses[size];

  if (type === 'circular') {
    const circleSize = classes.circle;
    const strokeWidth = circleSize * 0.08;
    const radius = (circleSize - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference;

    return (
      <div className="flex flex-col items-center justify-center h-full p-4">
        <div className="relative" style={{ width: circleSize, height: circleSize }}>
          {/* Background circle */}
          <svg className="transform -rotate-90" width={circleSize} height={circleSize}>
            <circle
              cx={circleSize / 2}
              cy={circleSize / 2}
              r={radius}
              stroke="currentColor"
              strokeWidth={strokeWidth}
              fill="none"
              className="text-gray-200"
            />
            {/* Progress circle */}
            <circle
              cx={circleSize / 2}
              cy={circleSize / 2}
              r={radius}
              stroke="currentColor"
              strokeWidth={strokeWidth}
              fill="none"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              className={progressColor.replace('bg-', 'text-')}
              style={{
                transition: animated ? 'stroke-dashoffset 0.5s ease' : 'none',
              }}
            />
          </svg>

          {/* Center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            {showPercentage && (
              <div className={`font-bold ${classes.text}`}>
                {percentage.toFixed(0)}%
              </div>
            )}
            {showValue && (
              <div className="text-xs text-gray-600 mt-1">
                {value.toFixed(1)} {unit}
              </div>
            )}
          </div>
        </div>

        {/* Title */}
        <div className="mt-3 text-center">
          <div className={`font-medium text-gray-700 ${classes.text}`}>
            {title}
          </div>
          {target !== undefined && (
            <div className="text-xs text-gray-500 mt-1 flex items-center justify-center">
              <Target className="w-3 h-3 mr-1" />
              Target: {target} {unit}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Bar type (horizontal)
  return (
    <div className="flex flex-col h-full p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h3 className={`font-semibold text-gray-700 ${classes.text}`}>
          {title}
        </h3>
        {showPercentage && (
          <span className={`font-bold ${progressColor.replace('bg-', 'text-')} ${classes.text}`}>
            {percentage.toFixed(0)}%
          </span>
        )}
      </div>

      {/* Progress bar */}
      <div className="relative flex-1 flex items-center">
        <div className={`w-full ${classes.height} bg-gray-200 rounded-full overflow-hidden`}>
          <div
            className={`h-full ${progressColor} rounded-full ${animated ? 'transition-all duration-500 ease-out' : ''}`}
            style={{ width: `${percentage}%` }}
          />
        </div>

        {/* Target indicator */}
        {target !== undefined && (
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-gray-700"
            style={{ left: `${((target - min) / range) * 100}%` }}
          >
            <div className="absolute -top-1 left-1/2 transform -translate-x-1/2">
              <Target className="w-3 h-3 text-gray-700" />
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-2 text-sm text-gray-600">
        {showValue && (
          <span>
            {value.toFixed(1)} {unit}
          </span>
        )}
        <span className="text-xs text-gray-500">
          {min} - {max} {unit}
        </span>
      </div>

      {/* Thresholds legend */}
      {thresholds && (
        <div className="mt-3 flex gap-3 text-xs">
          {thresholds.warning !== undefined && (
            <div className="flex items-center">
              <div className="w-3 h-3 bg-yellow-500 rounded mr-1" />
              <span className="text-gray-600">Warning: {thresholds.warning}</span>
            </div>
          )}
          {thresholds.critical !== undefined && (
            <div className="flex items-center">
              <div className="w-3 h-3 bg-red-500 rounded mr-1" />
              <span className="text-gray-600">Critical: {thresholds.critical}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
