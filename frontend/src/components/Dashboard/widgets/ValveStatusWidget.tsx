/**
 * Valve Status Widget - Industrial Valve Control Display
 * Shows valve position and status with visual indicator
 */
import React from 'react';
import { useLiveTagData } from '../../../hooks/useLiveTagData';

interface Widget {
  id: string;
  title: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface ValveStatusWidgetProps {
  widget: Widget;
}

const ValveStatusWidget: React.FC<ValveStatusWidgetProps> = ({ widget }) => {
  const tagId = widget.config?.tagId || widget.data_config?.tagId;

  const liveData = useLiveTagData({
    tagId,
    min: 0,
    max: 100,
  });

  const position = typeof liveData.value === 'number' ? liveData.value : 0;
  const showPercentage = widget.config?.showPercentage ?? true;
  const valveColor = widget.config?.color || '#3B82F6';

  const getStatusText = () => {
    if (position >= 95) return 'Aberta';
    if (position <= 5) return 'Fechada';
    return 'Modulando';
  };

  const getStatusColor = () => {
    if (position >= 95) return '#10B981';
    if (position <= 5) return '#EF4444';
    return '#F59E0B';
  };

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
        <p className="text-gray-500 dark:text-gray-400">Arraste uma tag aqui</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col items-center justify-center p-4">
      {/* Valve SVG */}
      <div className="relative w-24 h-32">
        <svg viewBox="0 0 100 140" className="w-full h-full">
          {/* Pipe left */}
          <rect x="0" y="55" width="25" height="20" fill="#6B7280" />
          {/* Pipe right */}
          <rect x="75" y="55" width="25" height="20" fill="#6B7280" />

          {/* Valve body */}
          <rect x="25" y="45" width="50" height="40" rx="4" fill="#374151" />

          {/* Valve opening indicator */}
          <rect
            x="30"
            y="50"
            width="40"
            height="30"
            rx="2"
            fill={valveColor}
            opacity={position / 100}
            className="transition-all duration-300"
          />

          {/* Valve stem */}
          <rect x="45" y="20" width="10" height="30" fill="#9CA3AF" />

          {/* Valve handle (wheel) */}
          <circle cx="50" cy="15" r="12" fill="none" stroke="#4B5563" strokeWidth="4" />
          <line x1="38" y1="15" x2="62" y2="15" stroke="#4B5563" strokeWidth="3" />
          <line x1="50" y1="3" x2="50" y2="27" stroke="#4B5563" strokeWidth="3" />

          {/* Handle rotation based on position */}
          <g transform={`rotate(${position * 1.8} 50 15)`}>
            <circle cx="50" cy="15" r="4" fill="#1F2937" />
          </g>

          {/* Flow arrows when open */}
          {position > 20 && (
            <>
              <path
                d="M 10 65 L 20 65 L 15 60 M 20 65 L 15 70"
                stroke="#10B981"
                strokeWidth="2"
                fill="none"
                opacity={position / 100}
                className="animate-pulse"
              />
              <path
                d="M 80 65 L 90 65 L 85 60 M 90 65 L 85 70"
                stroke="#10B981"
                strokeWidth="2"
                fill="none"
                opacity={position / 100}
                className="animate-pulse"
              />
            </>
          )}
        </svg>
      </div>

      {/* Status */}
      <div className="mt-3 text-center">
        <div
          className="text-lg font-bold"
          style={{ color: getStatusColor() }}
        >
          {getStatusText()}
        </div>
        {showPercentage && (
          <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            {position.toFixed(0)}%
          </div>
        )}
        <div className="text-xs text-gray-500 mt-1">
          {widget.config?.tagName || tagId}
        </div>
      </div>

      {/* Position bar */}
      <div className="w-full mt-3">
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full transition-all duration-300 rounded-full"
            style={{
              width: `${position}%`,
              backgroundColor: valveColor
            }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>Fechada</span>
          <span>Aberta</span>
        </div>
      </div>

      {/* Timestamp */}
      {liveData.timestamp && (
        <div className="text-xs text-gray-400 mt-2">
          {new Date(liveData.timestamp).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

export default ValveStatusWidget;
