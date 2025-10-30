import React from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { format } from 'date-fns';

interface DataPoint {
  timestamp: string | Date;
  value?: number;
  [key: string]: any;
}

interface SeriesConfig {
  dataKey: string;
  label?: string;
  color?: string;
  yAxisId?: string;
  unit?: string;
}

interface TimeSeriesChartProps {
  data: DataPoint[];
  dataKey?: string;
  series?: SeriesConfig[]; // Multiple series support
  xAxisKey?: string;
  title?: string;
  type?: 'line' | 'area';
  color?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  height?: number;
  unit?: string;
}

export const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({
  data,
  dataKey = 'value',
  series,
  xAxisKey = 'timestamp',
  title,
  type = 'line',
  color = '#3B82F6',
  showGrid = true,
  showLegend = true,
  height = 400,
  unit = '',
}) => {
  const formatXAxis = (value: any) => {
    const date = new Date(value);
    return format(date, 'HH:mm:ss');
  };

  const formatTooltip = (value: any, name: string) => {
    // Find unit for this series
    const seriesConfig = series?.find(s => s.dataKey === name || s.label === name);
    const seriesUnit = seriesConfig?.unit || unit;
    return [`${value}${seriesUnit ? ' ' + seriesUnit : ''}`, seriesConfig?.label || name];
  };

  const formatTooltipLabel = (label: any) => {
    const date = new Date(label);
    return format(date, 'MMM d, yyyy HH:mm:ss');
  };

  // Default colors for multiple series
  const defaultColors = [
    '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
    '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16'
  ];

  // Check if we have multiple series or single dataKey
  const hasMultipleSeries = series && series.length > 0;

  // Group series by yAxisId to determine which need separate Y axes
  const yAxisIds = hasMultipleSeries
    ? Array.from(new Set(series.map(s => s.yAxisId || 'left')))
    : ['left'];

  const ChartComponent = type === 'area' ? AreaChart : LineChart;

  return (
    <div className="w-full h-full">
      {title && <h3 className="text-sm font-semibold text-gray-700 mb-2 px-2">{title}</h3>}
      <ResponsiveContainer width="100%" height={title ? height - 30 : height}>
        <ChartComponent data={data}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />}
          <XAxis
            dataKey={xAxisKey}
            tickFormatter={formatXAxis}
            stroke="#6B7280"
            style={{ fontSize: '11px' }}
          />
          
          {/* Render Y axes based on yAxisIds */}
          {yAxisIds.map((yAxisId, index) => (
            <YAxis
              key={yAxisId}
              yAxisId={yAxisId}
              orientation={index === 0 ? 'left' : 'right'}
              stroke="#6B7280"
              style={{ fontSize: '11px' }}
            />
          ))}
          
          <Tooltip
            formatter={formatTooltip}
            labelFormatter={formatTooltipLabel}
            contentStyle={{
              backgroundColor: '#FFF',
              border: '1px solid #E5E7EB',
              borderRadius: '8px',
              padding: '8px',
              fontSize: '12px',
            }}
          />
          {showLegend && <Legend wrapperStyle={{ fontSize: '12px' }} />}
          
          {/* Render multiple series or single series */}
          {hasMultipleSeries ? (
            series.map((s, index) => {
              const seriesColor = s.color || defaultColors[index % defaultColors.length];
              return type === 'area' ? (
                <Area
                  key={s.dataKey}
                  type="monotone"
                  dataKey={s.dataKey}
                  name={s.label || s.dataKey}
                  stroke={seriesColor}
                  fill={seriesColor}
                  fillOpacity={0.3}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                  yAxisId={s.yAxisId || 'left'}
                />
              ) : (
                <Line
                  key={s.dataKey}
                  type="monotone"
                  dataKey={s.dataKey}
                  name={s.label || s.dataKey}
                  stroke={seriesColor}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                  yAxisId={s.yAxisId || 'left'}
                />
              );
            })
          ) : (
            // Single series (backward compatibility)
            type === 'area' ? (
              <Area
                type="monotone"
                dataKey={dataKey}
                stroke={color}
                fill={color}
                fillOpacity={0.3}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6 }}
                yAxisId="left"
              />
            ) : (
              <Line
                type="monotone"
                dataKey={dataKey}
                stroke={color}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6 }}
                yAxisId="left"
              />
            )
          )}
        </ChartComponent>
      </ResponsiveContainer>
    </div>
  );
};
