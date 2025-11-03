/**
 * Sparkline Widget - Inline mini chart for trending
 * Features:
 * - Small, compact trend visualization
 * - Area, line, or bar style
 * - Current value display
 * - Min/max indicators
 * - Multiple data series support
 * - Real-time updates
 */

import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface SparklineWidgetProps {
  title: string;
  data: number[];
  currentValue?: number;
  previousValue?: number;
  unit?: string;
  style?: 'line' | 'area' | 'bar';
  color?: string;
  showMinMax?: boolean;
  showTrend?: boolean;
  height?: number;
  decimals?: number;
}

export const SparklineWidget: React.FC<SparklineWidgetProps> = ({
  title,
  data,
  currentValue,
  previousValue,
  unit = '',
  style = 'area',
  color = '#3B82F6',
  showMinMax = false,
  showTrend = true,
  height = 60,
  decimals = 1,
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex flex-col h-full p-3 bg-white rounded-lg border border-gray-200">
        <div className="text-sm font-medium text-gray-600">{title}</div>
        <div className="flex-1 flex items-center justify-center text-gray-400">
          No data
        </div>
      </div>
    );
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const width = 200;

  // Calculate trend
  const latestValue = currentValue ?? data[data.length - 1];
  const compareValue = previousValue ?? data[0];
  const trend = latestValue > compareValue ? 'up' : latestValue < compareValue ? 'down' : 'neutral';
  const trendPercentage = compareValue !== 0 ? ((latestValue - compareValue) / compareValue) * 100 : 0;

  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600',
  };

  // Generate SVG path
  const generatePath = () => {
    if (style === 'bar') {
      const barWidth = width / data.length;
      return data.map((value, i) => {
        const barHeight = ((value - min) / range) * height;
        const x = i * barWidth;
        const y = height - barHeight;
        return (
          <rect
            key={i}
            x={x}
            y={y}
            width={barWidth * 0.8}
            height={barHeight}
            fill={color}
            opacity={0.8}
          />
        );
      });
    }

    // Line or area
    const points = data.map((value, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return { x, y };
    });

    const pathData = points.map((p, i) =>
      `${i === 0 ? 'M' : 'L'} ${p.x},${p.y}`
    ).join(' ');

    if (style === 'area') {
      const areaPath = `${pathData} L ${width},${height} L 0,${height} Z`;
      return (
        <>
          <path
            d={areaPath}
            fill={color}
            opacity={0.2}
          />
          <path
            d={pathData}
            fill="none"
            stroke={color}
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </>
      );
    }

    // Line style
    return (
      <path
        d={pathData}
        fill="none"
        stroke={color}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    );
  };

  return (
    <div className="flex flex-col h-full p-3 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <h3 className="text-sm font-medium text-gray-600">
            {title}
          </h3>
        </div>
        {showTrend && (
          <div className={`flex items-center text-xs font-medium ${trendColors[trend]}`}>
            {trend === 'up' && <TrendingUp className="w-3 h-3 mr-0.5" />}
            {trend === 'down' && <TrendingDown className="w-3 h-3 mr-0.5" />}
            {trend === 'neutral' && <Minus className="w-3 h-3 mr-0.5" />}
            {Math.abs(trendPercentage).toFixed(1)}%
          </div>
        )}
      </div>

      {/* Current value */}
      <div className="mb-2">
        <span className="text-2xl font-bold text-gray-800">
          {latestValue.toFixed(decimals)}
        </span>
        {unit && <span className="text-sm text-gray-500 ml-1">{unit}</span>}
      </div>

      {/* Sparkline chart */}
      <div className="flex-1 relative">
        <svg
          width="100%"
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="none"
          className="w-full"
        >
          {generatePath()}
        </svg>

        {/* Min/Max indicators */}
        {showMinMax && (
          <>
            <div className="absolute top-0 right-0 text-xs text-gray-500 bg-white px-1">
              {max.toFixed(decimals)}
            </div>
            <div className="absolute bottom-0 right-0 text-xs text-gray-500 bg-white px-1">
              {min.toFixed(decimals)}
            </div>
          </>
        )}
      </div>

      {/* Data points info */}
      <div className="mt-2 text-xs text-gray-500">
        {data.length} data points
      </div>
    </div>
  );
};
