import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

interface Widget {
  id: string;
  title: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface AreaChartWidgetProps {
  widget: Widget;
}

const AreaChartWidget: React.FC<AreaChartWidgetProps> = ({ widget }) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const tagId = widget.config?.tagId || widget.data_config?.tagId;
  const interval = widget.config?.interval || 3600; // Default 1 hour
  const refreshInterval = widget.config?.refreshInterval || 30000; // 30 seconds

  useEffect(() => {
    if (!tagId) {
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        const response = await axios.get('/api/v1/analytics/historical', {
          params: {
            tag_id: tagId,
            interval: interval,
          },
        });

        if (response.data && Array.isArray(response.data.data)) {
          const formattedData = response.data.data.map((point: any) => ({
            time: new Date(point.timestamp).toLocaleTimeString('en-US', {
              hour: '2-digit',
              minute: '2-digit',
            }),
            value: parseFloat(point.value),
            timestamp: point.timestamp,
          }));
          setData(formattedData);
        }
      } catch (error) {
        console.error('Error fetching historical data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const intervalId = setInterval(fetchData, refreshInterval);

    return () => clearInterval(intervalId);
  }, [tagId, interval, refreshInterval]);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!tagId) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-gray-400">
          <div className="text-5xl mb-2">📈</div>
          <p className="text-sm">Drag a tag for area chart</p>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-gray-500 dark:text-gray-400">No data available</p>
      </div>
    );
  }

  // Calculate min/max for Y-axis domain
  const values = data.map(d => d.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const padding = (maxValue - minValue) * 0.1;

  return (
    <div className="h-full flex flex-col p-4">
      {/* Title */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
          {widget.config?.tagName || widget.title || 'Area Chart'}
        </h3>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          Last {interval / 3600}h
        </span>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
            <XAxis
              dataKey="time"
              stroke="#9CA3AF"
              tick={{ fontSize: 12 }}
              tickLine={{ stroke: '#6B7280' }}
            />
            <YAxis
              stroke="#9CA3AF"
              tick={{ fontSize: 12 }}
              tickLine={{ stroke: '#6B7280' }}
              domain={[minValue - padding, maxValue + padding]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                border: 'none',
                borderRadius: '8px',
                color: '#fff',
              }}
              labelStyle={{ color: '#9CA3AF' }}
              formatter={(value: number) => [value.toFixed(2), 'Value']}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#3B82F6"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorValue)"
              animationDuration={800}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Stats */}
      <div className="flex items-center justify-around mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
        <div className="text-center">
          <div className="text-xs text-gray-500 dark:text-gray-400">Min</div>
          <div className="text-sm font-bold text-gray-900 dark:text-white">
            {minValue.toFixed(2)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 dark:text-gray-400">Avg</div>
          <div className="text-sm font-bold text-gray-900 dark:text-white">
            {(values.reduce((a, b) => a + b, 0) / values.length).toFixed(2)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 dark:text-gray-400">Max</div>
          <div className="text-sm font-bold text-gray-900 dark:text-white">
            {maxValue.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AreaChartWidget;
