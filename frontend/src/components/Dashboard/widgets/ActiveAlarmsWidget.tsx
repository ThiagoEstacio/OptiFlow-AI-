import React, { useState, useEffect } from 'react';
import { apiClient } from '../../../api/client';

interface Widget {
  id: string;
  title: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface ActiveAlarmsWidgetProps {
  widget: Widget;
}

const ActiveAlarmsWidget: React.FC<ActiveAlarmsWidgetProps> = ({ widget }) => {
  const [alarms, setAlarms] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAlarms = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch active alarms from API
        const response = await apiClient.get('/api/v1/alarms/active', {
          params: {
            limit: 10, // Limit to recent 10
          },
        });

        if (response.data && Array.isArray(response.data)) {
          const formattedAlarms = response.data.map((alarm: any) => {
            const timeDiff = Date.now() - new Date(alarm.trigger_timestamp).getTime();
            const minutes = Math.floor(timeDiff / 60000);
            const hours = Math.floor(minutes / 60);
            
            let timeAgo = '';
            if (hours > 0) {
              timeAgo = `${hours} hour${hours > 1 ? 's' : ''} ago`;
            } else if (minutes > 0) {
              timeAgo = `${minutes} min ago`;
            } else {
              timeAgo = 'Just now';
            }

            return {
              id: alarm.id,
              message: alarm.message || `Alarm on ${alarm.tag_id}`,
              severity: alarm.severity || 'info',
              time: timeAgo,
              state: alarm.state,
            };
          });

          setAlarms(formattedAlarms);
        } else {
          setAlarms([]);
        }
      } catch (err: any) {
        console.error('Error fetching alarms:', err);
        setError(err.message || 'Failed to load alarms');
      } finally {
        setLoading(false);
      }
    };

    fetchAlarms();
    
    // Refresh every 5 seconds
    const interval = setInterval(fetchAlarms, 5000);
    return () => clearInterval(interval);
  }, []);

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
          <span className="text-red-600 dark:text-red-400">Error loading alarms</span>
          <p className="text-xs text-gray-500 mt-1">{error}</p>
        </div>
      </div>
    );
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'border-l-red-500 bg-red-50 dark:bg-red-900/20';
      case 'warning': return 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
      case 'info': return 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/20';
      default: return 'border-l-gray-500 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  return (
    <div className="h-full p-4 space-y-2 overflow-auto">
      {alarms.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-4xl mb-2">✅</div>
          <p className="text-gray-600 dark:text-gray-400">No active alarms</p>
        </div>
      ) : (
        alarms.map((alarm) => (
          <div 
            key={alarm.id} 
            className={`border-l-4 p-3 rounded ${getSeverityColor(alarm.severity)}`}
          >
            <div className="flex justify-between items-start">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {alarm.message}
              </p>
              <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap ml-2">
                {alarm.time}
              </span>
            </div>
          </div>
        ))
      )}
    </div>
  );
};

export default ActiveAlarmsWidget;
