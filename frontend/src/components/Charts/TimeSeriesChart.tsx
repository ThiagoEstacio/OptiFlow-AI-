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
  value: number;
  [key: string]: any;
}

interface TimeSeriesChartProps {
  data: DataPoint[];
  dataKey?: string;
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
    return [`${value}${unit ? ' ' + unit : ''}`, name];
  };

  const formatTooltipLabel = (label: any) => {
    const date = new Date(label);
    return format(date, 'MMM d, yyyy HH:mm:ss');
  };

  const ChartComponent = type === 'area' ? AreaChart : LineChart;
  const DataComponent = type === 'area' ? Area : Line;

  return (
    <div className="w-full">
      {title && <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>}
      <ResponsiveContainer width="100%" height={height}>
        <ChartComponent data={data}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />}
          <XAxis
            dataKey={xAxisKey}
            tickFormatter={formatXAxis}
            stroke="#6B7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis stroke="#6B7280" style={{ fontSize: '12px' }} />
          <Tooltip
            formatter={formatTooltip}
            labelFormatter={formatTooltipLabel}
            contentStyle={{
              backgroundColor: '#FFF',
              border: '1px solid #E5E7EB',
              borderRadius: '8px',
              padding: '12px',
            }}
          />
          {showLegend && <Legend />}
          <DataComponent
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            fill={type === 'area' ? color : undefined}
            fillOpacity={type === 'area' ? 0.3 : undefined}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6 }}
          />
        </ChartComponent>
      </ResponsiveContainer>
    </div>
  );
};
