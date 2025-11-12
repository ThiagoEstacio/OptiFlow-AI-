import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { apiClient } from '../../../api/client';

interface Widget {
  id: string;
  title: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface BarChartWidgetProps {
  widget: Widget;
}

const BarChartWidget: React.FC<BarChartWidgetProps> = ({ widget }) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      // Support multiple tags for bar chart
      const tagIds = widget.config?.tagIds || widget.data_config?.tagIds || [];
      
      if (!tagIds || tagIds.length === 0) {
        setLoading(false);
        setError('No tags bound');
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Fetch current values for all tags
        const promises = tagIds.map((tagId: string) =>
          apiClient.get('/api/v1/analytics/current', {
            params: { tag_ids: tagId },
          }).catch(() => ({ data: null }))
        );

        const responses = await Promise.all(promises);
        
        const formattedData = responses
          .map((response, index) => {
            if (response.data && response.data.length > 0) {
              const point = response.data[0];
              return {
                name: point.tag_name || `Tag ${index + 1}`,
                value: typeof point.value === 'number' ? point.value : 0,
              };
            }
            return null;
          })
          .filter(Boolean);

        if (formattedData.length > 0) {
          setData(formattedData);
        } else {
          setError('No data available');
        }
      } catch (err: any) {
        console.error('Error fetching bar chart data:', err);
        setError(err.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Refresh every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [widget.config?.tagIds, widget.data_config?.tagIds]);

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
          <p className="text-xs text-gray-400 mt-2">Drag tags here to compare</p>
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
        <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="name" stroke="#9CA3AF" />
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
          <Bar dataKey="value" fill="#3B82F6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default BarChartWidget;
