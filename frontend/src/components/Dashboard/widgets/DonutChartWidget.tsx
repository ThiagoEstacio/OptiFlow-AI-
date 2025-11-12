import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { useLiveTagData } from '../../../hooks/useLiveTagData';

interface Widget {
  id: string;
  title: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface DonutChartWidgetProps {
  widget: Widget;
}

const DonutChartWidget: React.FC<DonutChartWidgetProps> = ({ widget }) => {
  const tagIds = widget.config?.tagIds || widget.data_config?.tagIds || [];
  
  // Get live data for all tags
  const tagData = tagIds.map((tagId: string, index: number) => {
    const data = useLiveTagData({ tagId });
    return {
      name: widget.config?.tagNames?.[index] || `Tag ${index + 1}`,
      value: typeof data.value === 'number' ? Math.abs(data.value) : 0,
      loading: data.loading,
    };
  });

  const loading = tagData.some(t => t.loading);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (tagIds.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-gray-400">
          <div className="text-5xl mb-2">🍩</div>
          <p className="text-sm">Drag tags for donut chart</p>
        </div>
      </div>
    );
  }

  const COLORS = [
    '#3B82F6', // blue
    '#10B981', // green
    '#F59E0B', // orange
    '#EF4444', // red
    '#8B5CF6', // purple
    '#EC4899', // pink
    '#14B8A6', // teal
    '#F97316', // orange-alt
  ];

  // Calculate total for percentages
  const total = tagData.reduce((sum, item) => sum + item.value, 0);

  // Format data for chart
  const chartData = tagData.map((item, index) => ({
    ...item,
    percentage: total > 0 ? (item.value / total) * 100 : 0,
    fill: COLORS[index % COLORS.length],
  }));

  const renderCustomLabel = (entry: any) => {
    return `${entry.percentage.toFixed(1)}%`;
  };

  return (
    <div className="h-full flex flex-col p-4">
      {/* Title */}
      <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
        {widget.title || 'Distribution'}
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-0 relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderCustomLabel}
              innerRadius="60%"
              outerRadius="80%"
              fill="#8884d8"
              dataKey="value"
              animationDuration={800}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                border: 'none',
                borderRadius: '8px',
                color: '#fff',
              }}
              formatter={(value: number) => [
                `${value.toFixed(2)} (${((value / total) * 100).toFixed(1)}%)`,
                'Value',
              ]}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              wrapperStyle={{
                fontSize: '12px',
              }}
            />
          </PieChart>
        </ResponsiveContainer>

        {/* Center label */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {total.toFixed(1)}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Total
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DonutChartWidget;
