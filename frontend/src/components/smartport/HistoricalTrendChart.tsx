/**
 * HistoricalTrendChart Component
 *
 * Displays historical PLC tag data with trend visualization
 */
import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { usePLC } from '../../hooks/usePLC';
import { BarChart3, RefreshCw, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { HistoricalDataPoint, PLCStatistics } from '../../api/plc';

interface HistoricalTrendChartProps {
  tagName: string;
  title?: string;
  hours?: number;
  chartType?: 'line' | 'area';
  showStatistics?: boolean;
}

export const HistoricalTrendChart: React.FC<HistoricalTrendChartProps> = ({
  tagName,
  title,
  hours: initialHours = 24,
  chartType = 'line',
  showStatistics = true,
}) => {
  const { tags, getHistory, getStatistics } = usePLC();

  const [data, setData] = useState<HistoricalDataPoint[]>([]);
  const [statistics, setStatistics] = useState<PLCStatistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [hours, setHours] = useState(initialHours);

  const tag = tags.find((t) => t.name === tagName);

  // Fetch historical data
  const fetchData = async () => {
    setLoading(true);
    try {
      const [historyData, statsData] = await Promise.all([
        getHistory(tagName, hours),
        showStatistics ? getStatistics(tagName, hours) : Promise.resolve(null),
      ]);

      setData(historyData);
      setStatistics(statsData);
    } catch (error) {
      console.error('Error fetching historical data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (tagName) {
      fetchData();
    }
  }, [tagName, hours]);

  // Format data for chart
  const chartData = data.map((point) => ({
    ...point,
    time: new Date(point.time).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    timestamp: new Date(point.time).getTime(),
  }));

  // Calculate trend
  const getTrend = () => {
    if (data.length < 2) return 'stable';
    const firstValue = data[0].value;
    const lastValue = data[data.length - 1].value;
    const change = ((lastValue - firstValue) / firstValue) * 100;

    if (Math.abs(change) < 1) return 'stable';
    return change > 0 ? 'up' : 'down';
  };

  const trend = getTrend();

  const timeRanges = [
    { label: '1 Hour', value: 1 },
    { label: '6 Hours', value: 6 },
    { label: '24 Hours', value: 24 },
    { label: '7 Days', value: 168 },
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm">
      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <BarChart3 className="h-5 w-5 text-blue-600" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                {title || `Historical Trend - ${tagName}`}
              </h2>
              {tag && <p className="text-sm text-gray-500">{tag.description}</p>}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Time Range Selector */}
            <div className="flex items-center gap-2">
              {timeRanges.map((range) => (
                <button
                  key={range.value}
                  onClick={() => setHours(range.value)}
                  className={`px-3 py-1 text-sm rounded transition-colors ${
                    hours === range.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {range.label}
                </button>
              ))}
            </div>

            {/* Refresh Button */}
            <button
              onClick={fetchData}
              disabled={loading}
              className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      {showStatistics && statistics && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div className="text-center">
            <p className="text-xs text-gray-500 uppercase">Current</p>
            <p className="text-lg font-bold text-gray-900">
              {data.length > 0 ? data[data.length - 1].value.toFixed(2) : 'N/A'}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500 uppercase">Average</p>
            <p className="text-lg font-bold text-blue-600">{statistics.mean.toFixed(2)}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500 uppercase">Min</p>
            <p className="text-lg font-bold text-green-600">{statistics.min.toFixed(2)}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500 uppercase">Max</p>
            <p className="text-lg font-bold text-red-600">{statistics.max.toFixed(2)}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500 uppercase">Trend</p>
            <div className="flex items-center justify-center gap-1">
              {trend === 'up' && <TrendingUp className="h-4 w-4 text-green-600" />}
              {trend === 'down' && <TrendingDown className="h-4 w-4 text-red-600" />}
              {trend === 'stable' && <Minus className="h-4 w-4 text-gray-600" />}
              <span
                className={`text-sm font-semibold ${
                  trend === 'up'
                    ? 'text-green-600'
                    : trend === 'down'
                    ? 'text-red-600'
                    : 'text-gray-600'
                }`}
              >
                {trend}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="p-6">
        {loading ? (
          <div className="flex items-center justify-center h-80">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading chart data...</span>
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex items-center justify-center h-80 text-gray-500">
            <div className="text-center">
              <BarChart3 className="h-12 w-12 mx-auto mb-3 text-gray-400" />
              <p>No historical data available</p>
            </div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            {chartType === 'area' ? (
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                  }}
                  formatter={(value: number) => [
                    `${value.toFixed(2)} ${tag?.unit || ''}`,
                    'Value',
                  ]}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fill="url(#colorValue)"
                />
              </AreaChart>
            ) : (
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                  }}
                  formatter={(value: number) => [
                    `${value.toFixed(2)} ${tag?.unit || ''}`,
                    'Value',
                  ]}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', r: 3 }}
                  activeDot={{ r: 5 }}
                  name={tagName}
                />
                {statistics && (
                  <>
                    <Line
                      type="monotone"
                      dataKey={() => statistics.mean}
                      stroke="#10b981"
                      strokeWidth={1}
                      strokeDasharray="5 5"
                      dot={false}
                      name="Average"
                    />
                  </>
                )}
              </LineChart>
            )}
          </ResponsiveContainer>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-gray-200 px-6 py-3 bg-gray-50 rounded-b-lg">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <span>
            {data.length} data points over {hours} hour{hours !== 1 ? 's' : ''}
          </span>
          {tag?.unit && <span>Unit: {tag.unit}</span>}
        </div>
      </div>
    </div>
  );
};
