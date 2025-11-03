import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { format } from 'date-fns';

interface Series {
  key: string;
  name: string;
  color: string;
}

interface MultiSeriesChartProps {
  data: any[];
  series: Series[];
  xAxisKey?: string;
  title?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  height?: number;
}

const COLORS = [
  '#3B82F6', // blue
  '#EF4444', // red
  '#10B981', // green
  '#F59E0B', // yellow
  '#8B5CF6', // purple
  '#EC4899', // pink
  '#06B6D4', // cyan
  '#F97316', // orange
];

export const MultiSeriesChart: React.FC<MultiSeriesChartProps> = ({
  data,
  series,
  xAxisKey = 'timestamp',
  title,
  showGrid = true,
  showLegend = true,
  height = 400,
}) => {
  const formatXAxis = (value: any) => {
    const date = new Date(value);
    return format(date, 'HH:mm:ss');
  };

  const formatTooltipLabel = (label: any) => {
    const date = new Date(label);
    return format(date, 'MMM d, yyyy HH:mm:ss');
  };

  return (
    <div className="w-full">
      {title && <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />}
          <XAxis
            dataKey={xAxisKey}
            tickFormatter={formatXAxis}
            stroke="#6B7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis stroke="#6B7280" style={{ fontSize: '12px' }} />
          <Tooltip
            labelFormatter={formatTooltipLabel}
            contentStyle={{
              backgroundColor: '#FFF',
              border: '1px solid #E5E7EB',
              borderRadius: '8px',
              padding: '12px',
            }}
          />
          {showLegend && <Legend />}
          {series.map((s, index) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color || COLORS[index % COLORS.length]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
