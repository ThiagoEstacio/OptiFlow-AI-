/**
 * StreamControls Component
 *
 * Controls for real-time analytics streaming
 */

import React, { useState } from 'react';
import {
  Play,
  Pause,
  Square,
  Radio,
  RefreshCw,
  Wifi,
  WifiOff,
  AlertCircle,
  Clock,
} from 'lucide-react';
import { StreamStatus } from '../../hooks/useAnalyticsStream';

export interface StreamControlsProps {
  status: StreamStatus;
  refreshInterval: number;
  onRefreshIntervalChange: (interval: number) => void;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  disabled?: boolean;
}

/**
 * Stream Controls Component
 */
export const StreamControls: React.FC<StreamControlsProps> = ({
  status,
  refreshInterval,
  onRefreshIntervalChange,
  onStart,
  onPause,
  onResume,
  onStop,
  disabled = false,
}) => {
  const [showIntervalPicker, setShowIntervalPicker] = useState(false);

  const intervalOptions = [
    { label: '1s', value: 1 },
    { label: '2s', value: 2 },
    { label: '5s', value: 5 },
    { label: '10s', value: 10 },
    { label: '30s', value: 30 },
    { label: '1m', value: 60 },
    { label: '5m', value: 300 },
  ];

  const handleIntervalChange = (value: number) => {
    onRefreshIntervalChange(value);
    setShowIntervalPicker(false);
  };

  const formatLastUpdate = (lastUpdate: string | null) => {
    if (!lastUpdate) return 'Never';
    const date = new Date(lastUpdate);
    return date.toLocaleTimeString();
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between">
        {/* Status Indicator */}
        <div className="flex items-center gap-3">
          {/* Connection Status */}
          <div className="flex items-center gap-2">
            {status.connected ? (
              <Wifi size={18} className="text-green-600" />
            ) : (
              <WifiOff size={18} className="text-gray-400" />
            )}
            <span
              className={`text-sm font-medium ${
                status.connected ? 'text-green-700' : 'text-gray-500'
              }`}
            >
              {status.connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          {/* Streaming Indicator */}
          {status.streaming && (
            <div className="flex items-center gap-2">
              {status.paused ? (
                <Pause size={18} className="text-yellow-600" />
              ) : (
                <Radio size={18} className="text-red-600 animate-pulse" />
              )}
              <span
                className={`text-sm font-medium ${
                  status.paused ? 'text-yellow-700' : 'text-red-700'
                }`}
              >
                {status.paused ? 'Paused' : 'Live'}
              </span>
            </div>
          )}

          {/* Sequence Counter */}
          {status.streaming && (
            <div className="text-sm text-gray-600">
              #{status.sequence.toString().padStart(4, '0')}
            </div>
          )}

          {/* Last Update */}
          {status.lastUpdate && (
            <div className="flex items-center gap-1 text-sm text-gray-600">
              <Clock size={14} />
              {formatLastUpdate(status.lastUpdate)}
            </div>
          )}
        </div>

        {/* Control Buttons */}
        <div className="flex items-center gap-2">
          {/* Refresh Interval Picker */}
          <div className="relative">
            <button
              onClick={() => setShowIntervalPicker(!showIntervalPicker)}
              disabled={disabled || status.streaming}
              className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw size={14} />
              {refreshInterval}s
            </button>

            {showIntervalPicker && (
              <div className="absolute top-full mt-1 right-0 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                {intervalOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handleIntervalChange(option.value)}
                    className={`block w-full text-left px-4 py-2 text-sm hover:bg-gray-50 ${
                      refreshInterval === option.value
                        ? 'bg-blue-50 text-blue-700 font-medium'
                        : 'text-gray-700'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Play/Pause/Stop Buttons */}
          {!status.streaming ? (
            <button
              onClick={onStart}
              disabled={disabled || !status.connected}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Play size={16} />
              Start Stream
            </button>
          ) : (
            <>
              {!status.paused ? (
                <button
                  onClick={onPause}
                  disabled={disabled}
                  className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Pause size={16} />
                  Pause
                </button>
              ) : (
                <button
                  onClick={onResume}
                  disabled={disabled}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Play size={16} />
                  Resume
                </button>
              )}

              <button
                onClick={onStop}
                disabled={disabled}
                className="flex items-center gap-2 px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Square size={16} />
                Stop
              </button>
            </>
          )}
        </div>
      </div>

      {/* Error Display */}
      {status.error && (
        <div className="mt-3 flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle size={18} className="text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <div className="text-sm font-medium text-red-900">
              Connection Error
            </div>
            <div className="text-xs text-red-700 mt-1">{status.error}</div>
          </div>
        </div>
      )}

      {/* Info Banner */}
      {status.streaming && !status.paused && (
        <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="text-sm text-blue-900">
            <strong>Live streaming active</strong> - Data updates every{' '}
            {refreshInterval}s. Visualizations will update automatically.
          </div>
        </div>
      )}
    </div>
  );
};

export default StreamControls;
