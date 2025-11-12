import React, { useState, useEffect } from 'react';
import { useLiveTagData } from '../../../hooks/useLiveTagData';

interface Widget {
  id: string;
  title: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface KPICardProps {
  widget: Widget;
}

const KPICard: React.FC<KPICardProps> = ({ widget }) => {
  const [trend, setTrend] = useState<'up' | 'down' | 'neutral'>('neutral');
  const [previousValue, setPreviousValue] = useState<number | null>(null);

  // Get tagId from widget config
  const tagId = widget.config?.tagId || widget.data_config?.tagId;
  
  // Use live data hook if tagId is available
  const liveData = useLiveTagData({
    tagId,
    min: widget.config?.min || 0,
    max: widget.config?.max || 100,
  });

  // Calculate trend when value changes
  useEffect(() => {
    if (liveData.value !== null && typeof liveData.value === 'number') {
      if (previousValue !== null) {
        if (liveData.value > previousValue) {
          setTrend('up');
        } else if (liveData.value < previousValue) {
          setTrend('down');
        } else {
          setTrend('neutral');
        }
      }
      setPreviousValue(liveData.value);
    }
  }, [liveData.value, previousValue]);

  const getTrendIcon = () => {
    if (trend === 'up') return '↗️';
    if (trend === 'down') return '↘️';
    return '→';
  };

  const getTrendColor = () => {
    if (trend === 'up') return 'text-green-600 dark:text-green-400';
    if (trend === 'down') return 'text-red-600 dark:text-red-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  // Format value for display
  const displayValue = liveData.value !== null 
    ? (typeof liveData.value === 'number' 
        ? liveData.value.toFixed(widget.config?.decimals || 2)
        : String(liveData.value))
    : '--';

  return (
    <div className="h-full flex flex-col justify-center items-center p-4">
      {liveData.loading ? (
        <div className="animate-pulse">
          <div className="h-12 w-24 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
          <div className="h-4 w-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      ) : liveData.error ? (
        <div className="text-center">
          <span className="text-red-600 dark:text-red-400">Error</span>
          <p className="text-xs text-gray-500 mt-1">{liveData.error}</p>
        </div>
      ) : (
        <>
          <div className="flex items-baseline space-x-2">
            <span className="text-4xl font-bold text-gray-900 dark:text-white">
              {displayValue}
            </span>
            {tagId && (
              <span className={`text-2xl ${getTrendColor()}`}>
                {getTrendIcon()}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
            {widget.config?.tagName || widget.display_config?.subtitle || 'No tag bound'}
          </p>
          {widget.config?.unit && (
            <span className="text-xs text-gray-500 dark:text-gray-500 mt-1">
              {widget.config.unit}
            </span>
          )}
          {liveData.timestamp && (
            <span className="text-xs text-gray-400 dark:text-gray-600 mt-1">
              Updated: {new Date(liveData.timestamp).toLocaleTimeString()}
            </span>
          )}
        </>
      )}
    </div>
  );
};

export default KPICard;
