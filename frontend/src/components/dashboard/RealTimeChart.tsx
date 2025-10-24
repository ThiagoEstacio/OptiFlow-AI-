/**
 * Real-time Line Chart Component
 */
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useTimeSeries } from '../../hooks/useTimeSeries';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../common/ErrorMessage';
import type { TimeSeriesPoint } from '../../types';

interface RealTimeChartProps {
  tagIds: string[];
  title: string;
  height?: number;
  maxDataPoints?: number;
  refreshInterval?: number;
  yAxisLabel?: string;
}

export const RealTimeChart: React.FC<RealTimeChartProps> = ({
  tagIds,
  title,
  height = 400,
  maxDataPoints = 50,
  yAxisLabel = 'Value',
}) => {
  const { tagData, subscribeToTag, connected } = useWebSocket();
  const { querySingleTag, loading, error } = useTimeSeries();
  const [chartData, setChartData] = useState<any[]>([]);
  const [colors] = useState(['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']);

  // Load initial historical data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const endTime = new Date();
        const startTime = new Date(endTime.getTime() - 3600000); // Last hour

        const results = await Promise.all(
          tagIds.map((tagId) => querySingleTag(tagId, startTime, endTime))
        );

        // Combine data from all tags
        const combinedData: Record<string, any> = {};

        results.forEach((result, index) => {
          const tagId = tagIds[index];
          result.data?.forEach((point: TimeSeriesPoint) => {
            const timestamp = new Date(point.timestamp).getTime();
            if (!combinedData[timestamp]) {
              combinedData[timestamp] = { timestamp };
            }
            combinedData[timestamp][`tag_${index}`] = point.value;
          });
        });

        const sortedData = Object.values(combinedData).sort(
          (a: any, b: any) => a.timestamp - b.timestamp
        );

        setChartData(sortedData.slice(-maxDataPoints));
      } catch (err) {
        console.error('Failed to load initial data:', err);
      }
    };

    loadInitialData();
  }, [tagIds, maxDataPoints]);

  // Subscribe to real-time updates
  useEffect(() => {
    if (connected) {
      tagIds.forEach((tagId) => subscribeToTag(tagId));
    }
  }, [tagIds, connected, subscribeToTag]);

  // Update chart with real-time data
  useEffect(() => {
    tagIds.forEach((tagId, index) => {
      const data = tagData[tagId];
      if (data) {
        setChartData((prev) => {
          const newPoint = {
            timestamp: new Date(data.timestamp).getTime(),
            [`tag_${index}`]: data.value,
          };

          const updated = [...prev, newPoint];
          return updated.slice(-maxDataPoints);
        });
      }
    });
  }, [tagData, tagIds, maxDataPoints]);

  if (loading && chartData.length === 0) {
    return <LoadingSpinner text="Loading chart data..." />;
  }

  if (error) {
    return <ErrorMessage message={error} />;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <div className="flex items-center space-x-2">
          <div
            className={`w-2 h-2 rounded-full ${
              connected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-sm text-gray-600">
            {connected ? 'Live' : 'Disconnected'}
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(value) => new Date(value).toLocaleTimeString()}
            stroke="#6b7280"
          />
          <YAxis label={{ value: yAxisLabel, angle: -90, position: 'insideLeft' }} stroke="#6b7280" />
          <Tooltip
            labelFormatter={(value) => new Date(value).toLocaleString()}
            contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb' }}
          />
          <Legend />
          {tagIds.map((tagId, index) => (
            <Line
              key={tagId}
              type="monotone"
              dataKey={`tag_${index}`}
              name={`Tag ${index + 1}`}
              stroke={colors[index % colors.length]}
              strokeWidth={2}
              dot={false}
              animationDuration={300}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
