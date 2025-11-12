import React from 'react';
import { useLiveTagData } from '../../../hooks/useLiveTagData';

interface Widget {
  id: string;
  title: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface StatWidgetProps {
  widget: Widget;
}

const StatWidget: React.FC<StatWidgetProps> = ({ widget }) => {
  const tagId = widget.config?.tagId || widget.data_config?.tagId;
  
  const liveData = useLiveTagData({
    tagId,
    min: widget.config?.min || 0,
    max: widget.config?.max || 100,
  });

  if (liveData.loading) {
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900">
        <div className="animate-pulse text-center">
          <div className="h-16 w-32 bg-gray-200 dark:bg-gray-700 rounded mb-2 mx-auto"></div>
        </div>
      </div>
    );
  }

  if (liveData.error) {
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20">
        <div className="text-center">
          <div className="text-4xl mb-2">⚠️</div>
          <span className="text-red-600 dark:text-red-400 text-sm">{liveData.error}</span>
        </div>
      </div>
    );
  }

  if (!tagId) {
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900">
        <div className="text-center text-gray-400">
          <div className="text-5xl mb-2">📊</div>
          <p className="text-sm">Drag a tag here</p>
        </div>
      </div>
    );
  }

  const numValue = typeof liveData.value === 'number' ? liveData.value : 0;
  const formattedValue = numValue.toFixed(widget.config?.decimals ?? 1);
  
  // Calculate color based on thresholds
  const getValueColor = () => {
    const thresholds = widget.config?.thresholds || [];
    for (const threshold of thresholds) {
      if (numValue >= threshold.value) {
        return threshold.color;
      }
    }
    return 'text-blue-600 dark:text-blue-400';
  };

  return (
    <div className="h-full flex flex-col justify-center items-center p-6 bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900">
      {/* Title */}
      {widget.config?.showTitle !== false && (
        <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2 text-center">
          {widget.config?.tagName || widget.title}
        </div>
      )}
      
      {/* Main Value */}
      <div className={`text-6xl font-bold ${getValueColor()} transition-all duration-300`}>
        {widget.config?.prefix}{formattedValue}{widget.config?.suffix || widget.config?.unit || ''}
      </div>
      
      {/* Sparkline placeholder (could add mini chart) */}
      {widget.config?.showSparkline && (
        <div className="mt-3 h-8 w-full max-w-xs">
          <svg className="w-full h-full" viewBox="0 0 100 20" preserveAspectRatio="none">
            <polyline
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              className="text-blue-500 opacity-50"
              points="0,15 20,12 40,8 60,10 80,6 100,9"
            />
          </svg>
        </div>
      )}
      
      {/* Footer Info */}
      <div className="mt-3 flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
        {liveData.quality && (
          <span className={`px-2 py-1 rounded ${
            liveData.quality === 'good' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 
            'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
          }`}>
            {liveData.quality}
          </span>
        )}
        {liveData.timestamp && (
          <span>{new Date(liveData.timestamp).toLocaleTimeString()}</span>
        )}
      </div>
    </div>
  );
};

export default StatWidget;
