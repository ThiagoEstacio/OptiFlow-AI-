import React, { useState, useEffect } from 'react';
import { useLiveTagData } from '../../../hooks/useLiveTagData';

interface Widget {
  id: string;
  title: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface GaugeWidgetProps {
  widget: Widget;
}

const GaugeWidget: React.FC<GaugeWidgetProps> = ({ widget }) => {
  // Get tagId from widget config
  const tagId = widget.config?.tagId || widget.data_config?.tagId;
  const min = widget.config?.min || 0;
  const max = widget.config?.max || 100;
  
  // Use live data hook if tagId is available
  const liveData = useLiveTagData({
    tagId,
    min,
    max,
  });

  // Calculate percentage value
  const numValue = typeof liveData.value === 'number' ? liveData.value : 0;
  const percentage = ((numValue - min) / (max - min)) * 100;
  const clampedPercentage = Math.max(0, Math.min(100, percentage));

  if (liveData.loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (liveData.error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <span className="text-red-600 dark:text-red-400">Error</span>
          <p className="text-xs text-gray-500 mt-1">{liveData.error}</p>
        </div>
      </div>
    );
  }

  if (!tagId) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-gray-500 dark:text-gray-400">Drag a tag here</p>
      </div>
    );
  }

  const rotation = (clampedPercentage / 100) * 180 - 90;
  
  const getColor = () => {
    if (clampedPercentage < 30) return '#EF4444';
    if (clampedPercentage < 70) return '#F59E0B';
    return '#10B981';
  };

  return (
    <div className="h-full flex flex-col items-center justify-center">
      <div className="relative w-48 h-24">
        {/* Gauge Background */}
        <svg className="w-full h-full" viewBox="0 0 200 100">
          {/* Background Arc */}
          <path
            d="M 20 90 A 80 80 0 0 1 180 90"
            fill="none"
            stroke="#E5E7EB"
            strokeWidth="20"
            strokeLinecap="round"
          />
          {/* Value Arc */}
          <path
            d="M 20 90 A 80 80 0 0 1 180 90"
            fill="none"
            stroke={getColor()}
            strokeWidth="20"
            strokeLinecap="round"
            strokeDasharray={`${(clampedPercentage / 100) * 251} 251`}
          />
          {/* Needle */}
          <line
            x1="100"
            y1="90"
            x2="100"
            y2="30"
            stroke={getColor()}
            strokeWidth="3"
            strokeLinecap="round"
            transform={`rotate(${rotation} 100 90)`}
          />
          <circle cx="100" cy="90" r="5" fill={getColor()} />
        </svg>
      </div>
      <div className="text-center mt-2">
        <span className="text-3xl font-bold text-gray-900 dark:text-white">
          {numValue.toFixed(widget.config?.decimals || 1)} {widget.config?.unit || ''}
        </span>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          {widget.config?.tagName || widget.display_config?.subtitle || 'Current Value'}
        </p>
        {liveData.timestamp && (
          <p className="text-xs text-gray-400 dark:text-gray-600 mt-1">
            {new Date(liveData.timestamp).toLocaleTimeString()}
          </p>
        )}
      </div>
    </div>
  );
};

export default GaugeWidget;
