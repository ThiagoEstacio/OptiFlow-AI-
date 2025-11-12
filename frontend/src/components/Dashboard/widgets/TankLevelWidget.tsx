import React from 'react';
import { useLiveTagData } from '../../../hooks/useLiveTagData';

interface Widget {
  id: string;
  title: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface TankLevelWidgetProps {
  widget: Widget;
}

const TankLevelWidget: React.FC<TankLevelWidgetProps> = ({ widget }) => {
  const tagId = widget.config?.tagId || widget.data_config?.tagId;
  
  const liveData = useLiveTagData({
    tagId,
    min: widget.config?.min || 0,
    max: widget.config?.max || 100,
  });

  if (liveData.loading) {
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
          <div className="text-5xl mb-2">⛽</div>
          <p className="text-sm">Drag a level tag</p>
        </div>
      </div>
    );
  }

  const min = widget.config?.min || 0;
  const max = widget.config?.max || 100;
  const numValue = typeof liveData.value === 'number' ? liveData.value : 0;
  const percentage = ((numValue - min) / (max - min)) * 100;
  const clampedPercentage = Math.max(0, Math.min(100, percentage));

  // Get color based on level
  const getLevelColor = () => {
    if (clampedPercentage < 20) return '#EF4444'; // Red - Low
    if (clampedPercentage < 40) return '#F59E0B'; // Orange - Low-Medium
    if (clampedPercentage < 80) return '#10B981'; // Green - Good
    if (clampedPercentage < 95) return '#3B82F6'; // Blue - High
    return '#EF4444'; // Red - Overflow risk
  };

  const getStatusText = () => {
    if (clampedPercentage < 20) return 'LOW';
    if (clampedPercentage < 40) return 'LOW-MED';
    if (clampedPercentage < 80) return 'NORMAL';
    if (clampedPercentage < 95) return 'HIGH';
    return 'CRITICAL';
  };

  return (
    <div className="h-full flex flex-col items-center justify-center p-6">
      {/* Title */}
      <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 text-center">
        {widget.config?.tagName || widget.title || 'Tank Level'}
      </div>

      {/* Tank Visual */}
      <div className="relative w-40 h-56 flex items-end justify-center">
        {/* Tank Container */}
        <svg className="w-full h-full" viewBox="0 0 100 140" xmlns="http://www.w3.org/2000/svg">
          {/* Tank body */}
          <rect
            x="20"
            y="20"
            width="60"
            height="100"
            rx="5"
            fill="none"
            stroke="#9CA3AF"
            strokeWidth="2"
          />
          
          {/* Liquid level */}
          <rect
            x="22"
            y={122 - clampedPercentage}
            width="56"
            height={clampedPercentage}
            rx="3"
            fill={getLevelColor()}
            opacity="0.8"
          >
            <animate
              attributeName="opacity"
              values="0.7;0.9;0.7"
              dur="2s"
              repeatCount="indefinite"
            />
          </rect>
          
          {/* Liquid surface wave effect */}
          <path
            d={`M 22 ${122 - clampedPercentage} Q 35 ${120 - clampedPercentage}, 50 ${122 - clampedPercentage} T 78 ${122 - clampedPercentage}`}
            fill={getLevelColor()}
            opacity="0.6"
          >
            <animate
              attributeName="d"
              values={`M 22 ${122 - clampedPercentage} Q 35 ${120 - clampedPercentage}, 50 ${122 - clampedPercentage} T 78 ${122 - clampedPercentage};
                      M 22 ${122 - clampedPercentage} Q 35 ${124 - clampedPercentage}, 50 ${122 - clampedPercentage} T 78 ${122 - clampedPercentage};
                      M 22 ${122 - clampedPercentage} Q 35 ${120 - clampedPercentage}, 50 ${122 - clampedPercentage} T 78 ${122 - clampedPercentage}`}
              dur="3s"
              repeatCount="indefinite"
            />
          </path>

          {/* Level indicators */}
          <line x1="15" y1="30" x2="20" y2="30" stroke="#6B7280" strokeWidth="1" />
          <line x1="15" y1="55" x2="20" y2="55" stroke="#6B7280" strokeWidth="1" />
          <line x1="15" y1="80" x2="20" y2="80" stroke="#6B7280" strokeWidth="1" />
          <line x1="15" y1="105" x2="20" y2="105" stroke="#6B7280" strokeWidth="1" />
          <line x1="15" y1="120" x2="20" y2="120" stroke="#6B7280" strokeWidth="1" />

          <line x1="80" y1="30" x2="85" y2="30" stroke="#6B7280" strokeWidth="1" />
          <line x1="80" y1="55" x2="85" y2="55" stroke="#6B7280" strokeWidth="1" />
          <line x1="80" y1="80" x2="85" y2="80" stroke="#6B7280" strokeWidth="1" />
          <line x1="80" y1="105" x2="85" y2="105" stroke="#6B7280" strokeWidth="1" />
          <line x1="80" y1="120" x2="85" y2="120" stroke="#6B7280" strokeWidth="1" />
        </svg>

        {/* Value overlay */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center bg-white/90 dark:bg-gray-800/90 rounded-lg p-2 shadow-lg">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {clampedPercentage.toFixed(0)}%
            </div>
            <div className="text-xs font-medium" style={{ color: getLevelColor() }}>
              {getStatusText()}
            </div>
          </div>
        </div>
      </div>

      {/* Details */}
      <div className="mt-4 text-center space-y-1">
        <div className="text-lg font-bold text-gray-900 dark:text-white">
          {numValue.toFixed(widget.config?.decimals || 1)} {widget.config?.unit || 'L'}
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          Range: {min} - {max} {widget.config?.unit || 'L'}
        </div>
        {liveData.timestamp && (
          <div className="text-xs text-gray-400">
            {new Date(liveData.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
};

export default TankLevelWidget;
