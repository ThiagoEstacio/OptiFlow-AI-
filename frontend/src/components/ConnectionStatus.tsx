/**
 * Connection Status Component
 * Shows real-time backend connection status
 */

import React from 'react';
import { useBackendHealth } from '../hooks/useBackendHealth';
import { Wifi, WifiOff, AlertTriangle, RefreshCw } from 'lucide-react';

interface ConnectionStatusProps {
  className?: string;
  showLatency?: boolean;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  className = '',
  showLatency = false,
}) => {
  const { status, latency, forceCheck, lastCheck } = useBackendHealth({
    checkInterval: 30000,
    failureThreshold: 3,
  });

  const getStatusConfig = () => {
    switch (status) {
      case 'online':
        return {
          icon: <Wifi className="w-4 h-4" />,
          text: 'Online',
          color: 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30',
          dot: 'bg-green-500',
          animate: true,
        };
      case 'degraded':
        return {
          icon: <AlertTriangle className="w-4 h-4" />,
          text: 'Degraded',
          color: 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/30',
          dot: 'bg-yellow-500',
          animate: true,
        };
      case 'offline':
        return {
          icon: <WifiOff className="w-4 h-4" />,
          text: 'Offline',
          color: 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/30',
          dot: 'bg-red-500',
          animate: false,
        };
      case 'checking':
      default:
        return {
          icon: <RefreshCw className="w-4 h-4 animate-spin" />,
          text: 'Checking',
          color: 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900/30',
          dot: 'bg-gray-500',
          animate: false,
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${config.color} ${className}`}
      title={`Last check: ${lastCheck ? lastCheck.toLocaleTimeString() : 'Never'}`}
    >
      <span className="relative flex h-2 w-2">
        {config.animate && (
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${config.dot} opacity-75`} />
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${config.dot}`} />
      </span>

      {config.icon}
      <span>{config.text}</span>

      {showLatency && latency !== null && (
        <span className="text-gray-500 dark:text-gray-400">
          {latency}ms
        </span>
      )}

      <button
        onClick={forceCheck}
        className="ml-1 p-0.5 hover:bg-black/10 dark:hover:bg-white/10 rounded transition-colors"
        title="Check connection"
      >
        <RefreshCw className="w-3 h-3" />
      </button>
    </div>
  );
};

export default ConnectionStatus;
