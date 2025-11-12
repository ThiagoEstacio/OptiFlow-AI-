import React, { useState, useEffect } from 'react';
import { apiClient } from '../../../api/client';

interface Widget {
  id: string;
  title: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface ProcessStatusWidgetProps {
  widget: Widget;
}

const ProcessStatusWidget: React.FC<ProcessStatusWidgetProps> = ({ widget }) => {
  const [processes, setProcesses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      // Support multiple tags - each tag represents a process
      const tagIds = widget.config?.tagIds || widget.data_config?.tagIds || [];
      
      if (!tagIds || tagIds.length === 0) {
        setLoading(false);
        setError('No tags bound');
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Fetch current values for all process tags
        const promises = tagIds.map((tagId: string) =>
          apiClient.get('/api/v1/analytics/current', {
            params: { tag_ids: tagId },
          }).catch(() => ({ data: null }))
        );

        const responses = await Promise.all(promises);
        
        const formattedData = responses
          .map((response) => {
            if (response.data && response.data.length > 0) {
              const point = response.data[0];
              const value = typeof point.value === 'number' ? point.value : 0;
              
              // Determine status based on value (customize logic as needed)
              let status = 'idle';
              if (value > 50) status = 'running';
              else if (value < 0) status = 'error';
              
              return {
                name: point.tag_name || 'Process',
                status,
                efficiency: Math.max(0, Math.min(100, value)), // Clamp 0-100
                value: point.value,
                quality: point.quality,
              };
            }
            return null;
          })
          .filter(Boolean);

        if (formattedData.length > 0) {
          setProcesses(formattedData);
        } else {
          setError('No data available');
        }
      } catch (err: any) {
        console.error('Error fetching process status:', err);
        setError(err.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Refresh every 3 seconds
    const interval = setInterval(fetchData, 3000);
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
          <p className="text-xs text-gray-400 mt-2">Drag process tags here</p>
        </div>
      </div>
    );
  }

  if (processes.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <span className="text-gray-500 dark:text-gray-400">No processes configured</span>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-500';
      case 'idle': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="h-full p-4 space-y-3 overflow-auto">
      {processes.map((process, index) => (
        <div key={index} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${getStatusColor(process.status)} ${
                process.status === 'running' ? 'animate-pulse' : ''
              }`}></div>
              <span className="font-medium text-gray-900 dark:text-white">{process.name}</span>
            </div>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {process.efficiency}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all" 
              style={{ width: `${process.efficiency}%` }}
            ></div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ProcessStatusWidget;
