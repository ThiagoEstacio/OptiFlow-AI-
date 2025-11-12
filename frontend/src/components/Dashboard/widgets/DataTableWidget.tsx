import React, { useState, useEffect } from 'react';
import { apiClient } from '../../../api/client';

interface Widget {
  id: string;
  title: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface DataTableWidgetProps {
  widget: Widget;
}

const DataTableWidget: React.FC<DataTableWidgetProps> = ({ widget }) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      // Support multiple tags for table
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
                id: index + 1,
                tagName: point.tag_name || `Tag ${index + 1}`,
                value: typeof point.value === 'number' ? point.value : point.value,
                quality: point.quality || 'unknown',
                timestamp: point.timestamp,
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
        console.error('Error fetching table data:', err);
        setError(err.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Refresh every 2 seconds
    const interval = setInterval(fetchData, 2000);
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
          <p className="text-xs text-gray-400 mt-2">Drag tags here to display</p>
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
    <div className="h-full overflow-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800 sticky top-0">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Tag
            </th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Value
            </th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Quality
            </th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Time
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          {data.map((row) => (
            <tr key={row.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
              <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                {row.tagName}
              </td>
              <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                {typeof row.value === 'number' ? row.value.toFixed(2) : String(row.value)}
              </td>
              <td className="px-4 py-2 whitespace-nowrap">
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  row.quality === 'good' 
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                    : row.quality === 'bad'
                    ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                }`}>
                  {row.quality}
                </span>
              </td>
              <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400">
                {row.timestamp ? new Date(row.timestamp).toLocaleTimeString() : '--'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DataTableWidget;
