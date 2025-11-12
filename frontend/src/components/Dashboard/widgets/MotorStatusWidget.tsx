import React from 'react';
import { useLiveTagData } from '../../../hooks/useLiveTagData';

interface Widget {
  id: string;
  title: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface MotorStatusWidgetProps {
  widget: Widget;
}

const MotorStatusWidget: React.FC<MotorStatusWidgetProps> = ({ widget }) => {
  const statusTagId = widget.config?.statusTagId || widget.data_config?.statusTagId;
  const speedTagId = widget.config?.speedTagId;
  const currentTagId = widget.config?.currentTagId;
  const tempTagId = widget.config?.tempTagId;
  
  const statusData = useLiveTagData({ tagId: statusTagId });
  const speedData = useLiveTagData({ tagId: speedTagId });
  const currentData = useLiveTagData({ tagId: currentTagId });
  const tempData = useLiveTagData({ tagId: tempTagId });

  if (statusData.loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!statusTagId) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-gray-400">
          <div className="text-5xl mb-2">⚙️</div>
          <p className="text-sm">Drag a motor status tag</p>
        </div>
      </div>
    );
  }

  // Determine motor status
  const statusValue = typeof statusData.value === 'number' ? statusData.value : 0;
  const isRunning = statusValue > 0.5;
  const isFaulted = statusValue < 0 || (tempData.value as number) > 80;

  const getStatus = () => {
    if (isFaulted) return { text: 'FAULT', color: 'text-red-600', bg: 'bg-red-100 dark:bg-red-900/30' };
    if (isRunning) return { text: 'RUNNING', color: 'text-green-600', bg: 'bg-green-100 dark:bg-green-900/30' };
    return { text: 'STOPPED', color: 'text-gray-600', bg: 'bg-gray-100 dark:bg-gray-700/30' };
  };

  const status = getStatus();
  const speed = typeof speedData.value === 'number' ? speedData.value : 0;
  const current = typeof currentData.value === 'number' ? currentData.value : 0;
  const temp = typeof tempData.value === 'number' ? tempData.value : 0;

  return (
    <div className="h-full flex flex-col p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
          {widget.config?.motorName || widget.title || 'Motor Status'}
        </h3>
        <span className={`text-xs font-bold px-2 py-1 rounded ${status.bg} ${status.color}`}>
          {status.text}
        </span>
      </div>

      {/* Motor Visual */}
      <div className="flex-1 flex items-center justify-center mb-4">
        <div className="relative">
          {/* Motor body */}
          <svg className="w-32 h-32" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            {/* Main body */}
            <rect
              x="30"
              y="35"
              width="40"
              height="30"
              rx="5"
              fill="#4B5563"
              stroke="#6B7280"
              strokeWidth="2"
            />
            
            {/* Shaft */}
            <rect
              x="70"
              y="47"
              width="15"
              height="6"
              fill="#6B7280"
            />
            
            {/* Rotor */}
            <circle
              cx="50"
              cy="50"
              r="15"
              fill="#374151"
              stroke="#6B7280"
              strokeWidth="2"
            >
              {isRunning && (
                <animateTransform
                  attributeName="transform"
                  type="rotate"
                  from="0 50 50"
                  to="360 50 50"
                  dur={`${2 / Math.max(speed / 1000, 0.5)}s`}
                  repeatCount="indefinite"
                />
              )}
            </circle>
            
            {/* Rotor blades */}
            <line x1="50" y1="35" x2="50" y2="65" stroke="#6B7280" strokeWidth="2">
              {isRunning && (
                <animateTransform
                  attributeName="transform"
                  type="rotate"
                  from="0 50 50"
                  to="360 50 50"
                  dur={`${2 / Math.max(speed / 1000, 0.5)}s`}
                  repeatCount="indefinite"
                />
              )}
            </line>
            <line x1="35" y1="50" x2="65" y2="50" stroke="#6B7280" strokeWidth="2">
              {isRunning && (
                <animateTransform
                  attributeName="transform"
                  type="rotate"
                  from="0 50 50"
                  to="360 50 50"
                  dur={`${2 / Math.max(speed / 1000, 0.5)}s`}
                  repeatCount="indefinite"
                />
              )}
            </line>

            {/* Status indicator light */}
            <circle
              cx="35"
              cy="40"
              r="3"
              fill={isFaulted ? '#EF4444' : isRunning ? '#10B981' : '#6B7280'}
            >
              {isRunning && !isFaulted && (
                <animate
                  attributeName="opacity"
                  values="1;0.5;1"
                  dur="1s"
                  repeatCount="indefinite"
                />
              )}
            </circle>
          </svg>

          {/* Center speed indicator */}
          {isRunning && speedTagId && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-xs font-bold text-white bg-gray-800/80 px-2 py-1 rounded">
                {speed.toFixed(0)} RPM
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-2">
        {speedTagId && (
          <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
            <div className="text-xs text-gray-500 dark:text-gray-400">Speed</div>
            <div className="text-sm font-bold text-gray-900 dark:text-white">
              {speed.toFixed(0)}
            </div>
            <div className="text-xs text-gray-500">RPM</div>
          </div>
        )}
        
        {currentTagId && (
          <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
            <div className="text-xs text-gray-500 dark:text-gray-400">Current</div>
            <div className="text-sm font-bold text-gray-900 dark:text-white">
              {current.toFixed(1)}
            </div>
            <div className="text-xs text-gray-500">A</div>
          </div>
        )}
        
        {tempTagId && (
          <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
            <div className="text-xs text-gray-500 dark:text-gray-400">Temp</div>
            <div className={`text-sm font-bold ${temp > 80 ? 'text-red-600' : temp > 60 ? 'text-yellow-600' : 'text-gray-900 dark:text-white'}`}>
              {temp.toFixed(0)}
            </div>
            <div className="text-xs text-gray-500">°C</div>
          </div>
        )}
      </div>

      {/* Timestamp */}
      {statusData.timestamp && (
        <div className="text-xs text-gray-400 text-center mt-2">
          {new Date(statusData.timestamp).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

export default MotorStatusWidget;
