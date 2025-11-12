import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { apiClient } from '../../../api/client';

interface Widget {
  id: string;
  title: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface LineChartWidgetProps {
  widget: Widget;
}

const LineChartWidget: React.FC<LineChartWidgetProps> = ({ widget }) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHistoricalData = async () => {
      const tagId = widget.config?.tagId || widget.data_config?.tagId;
      
      if (!tagId) {
        setLoading(false);
        setError('No tag bound');
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Get historical data for the last hour
        const endTime = new Date();
        const startTime = new Date(endTime.getTime() - 60 * 60 * 1000); // 1 hour ago

        const response = await apiClient.get('/api/v1/analytics/historical', {
          params: {
            tag_ids: tagId,
            start_time: startTime.toISOString(),
            end_time: endTime.toISOString(),
            aggregation: 'raw', // or 'avg', '1m', '5m', etc.
          },
        });

        if (response.data && response.data.length > 0) {
          const formattedData = response.data.map((point: any) => ({
            time: new Date(point.timestamp).toLocaleTimeString('en-US', { 
              hour: '2-digit', 
              minute: '2-digit' 
            }),
            value: typeof point.value === 'number' ? point.value : 0,
            timestamp: point.timestamp,
          }));
          setData(formattedData);
        } else {
          setError('No data available');
        }
      } catch (err: any) {
        console.error('Error fetching historical data:', err);
        setError(err.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    fetchHistoricalData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchHistoricalData, 30000);
    return () => clearInterval(interval);
  }, [widget.config?.tagId, widget.data_config?.tagId]);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <span className="text-gray-500 dark:text-gray-400">{error}</span>
          <p className="text-xs text-gray-400 mt-2">Drag a tag here to see data</p>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <span className="text-gray-500 dark:text-gray-400">No data available</span>
      </div>
    );
  }

  return (
    <div className="h-full w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="time" stroke="#9CA3AF" />
          <YAxis stroke="#9CA3AF" />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1F2937', 
              border: 'none',
              borderRadius: '8px',
              color: '#FFF'
            }}
          />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke="#3B82F6" 
            strokeWidth={2}
            dot={{ fill: '#3B82F6', r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default LineChartWidget;
