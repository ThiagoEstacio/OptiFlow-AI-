/**
 * Status Indicator Widget - Industrial status display
 * Features:
 * - Multiple status states (running, stopped, warning, alarm, offline)
 * - Animated pulse for active states
 * - Text label and description
 * - Compact and expanded views
 * - Equipment/process status visualization
 */

import React from 'react';
import { Power, AlertTriangle, AlertCircle, CheckCircle, XCircle, Minus } from 'lucide-react';

interface StatusIndicatorProps {
  label: string;
  status: 'running' | 'stopped' | 'warning' | 'alarm' | 'offline' | 'idle' | 'maintenance';
  value?: number | string;
  unit?: string;
  description?: string;
  size?: 'sm' | 'md' | 'lg';
  layout?: 'horizontal' | 'vertical';
  showIcon?: boolean;
  animated?: boolean;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  label,
  status,
  value,
  unit,
  description,
  size = 'md',
  layout = 'horizontal',
  showIcon = true,
  animated = true,
}) => {
  const statusConfig = {
    running: {
      color: 'bg-green-500',
      textColor: 'text-green-700',
      borderColor: 'border-green-500',
      bgColor: 'bg-green-50',
      icon: CheckCircle,
      label: 'Running',
    },
    stopped: {
      color: 'bg-red-500',
      textColor: 'text-red-700',
      borderColor: 'border-red-500',
      bgColor: 'bg-red-50',
      icon: XCircle,
      label: 'Stopped',
    },
    warning: {
      color: 'bg-yellow-500',
      textColor: 'text-yellow-700',
      borderColor: 'border-yellow-500',
      bgColor: 'bg-yellow-50',
      icon: AlertTriangle,
      label: 'Warning',
    },
    alarm: {
      color: 'bg-red-600',
      textColor: 'text-red-800',
      borderColor: 'border-red-600',
      bgColor: 'bg-red-100',
      icon: AlertCircle,
      label: 'Alarm',
    },
    offline: {
      color: 'bg-gray-400',
      textColor: 'text-gray-600',
      borderColor: 'border-gray-400',
      bgColor: 'bg-gray-50',
      icon: Power,
      label: 'Offline',
    },
    idle: {
      color: 'bg-blue-400',
      textColor: 'text-blue-700',
      borderColor: 'border-blue-400',
      bgColor: 'bg-blue-50',
      icon: Minus,
      label: 'Idle',
    },
    maintenance: {
      color: 'bg-orange-500',
      textColor: 'text-orange-700',
      borderColor: 'border-orange-500',
      bgColor: 'bg-orange-50',
      icon: AlertTriangle,
      label: 'Maintenance',
    },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  const sizeClasses = {
    sm: {
      indicator: 'w-3 h-3',
      icon: 'w-4 h-4',
      text: 'text-sm',
      padding: 'p-2',
    },
    md: {
      indicator: 'w-4 h-4',
      icon: 'w-5 h-5',
      text: 'text-base',
      padding: 'p-3',
    },
    lg: {
      indicator: 'w-6 h-6',
      icon: 'w-6 h-6',
      text: 'text-lg',
      padding: 'p-4',
    },
  };

  const classes = sizeClasses[size];

  const shouldAnimate = animated && (status === 'running' || status === 'warning' || status === 'alarm');

  return (
    <div className={`
      rounded-lg border ${config.borderColor} ${config.bgColor}
      ${classes.padding} h-full
      ${layout === 'vertical' ? 'flex flex-col items-center text-center' : 'flex items-center'}
    `}>
      {/* Status Indicator Circle */}
      <div className="relative">
        <div className={`
          rounded-full ${config.color} ${classes.indicator}
          ${shouldAnimate ? 'animate-pulse' : ''}
        `} />
        {shouldAnimate && (
          <div className={`
            absolute inset-0 rounded-full ${config.color}
            animate-ping opacity-75
          `} />
        )}
      </div>

      {/* Content */}
      <div className={`
        flex-1
        ${layout === 'vertical' ? 'mt-3' : 'ml-3'}
      `}>
        {/* Label */}
        <div className={`font-semibold ${config.textColor} ${classes.text}`}>
          {label}
        </div>

        {/* Status Label */}
        <div className={`text-xs text-gray-500 mt-0.5`}>
          {config.label}
        </div>

        {/* Value */}
        {value !== undefined && (
          <div className={`font-medium ${config.textColor} mt-1`}>
            {value} {unit}
          </div>
        )}

        {/* Description */}
        {description && (
          <div className="text-xs text-gray-600 mt-1">
            {description}
          </div>
        )}
      </div>

      {/* Icon */}
      {showIcon && (
        <div className={`${config.textColor} ${layout === 'vertical' ? 'mt-2' : 'ml-2'}`}>
          <Icon className={classes.icon} />
        </div>
      )}
    </div>
  );
};
