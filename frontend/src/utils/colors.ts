/**
 * Color Utilities
 * ================
 * Centralized color configurations for consistent UI styling
 */

import { SeverityLevel, HealthStatus, TrendDirection } from './constants';

// Severity color mappings (Tailwind CSS classes)
export const SEVERITY_COLORS = {
  critical: {
    bg: 'bg-red-100',
    bgDark: 'bg-red-500',
    text: 'text-red-800',
    textLight: 'text-red-100',
    border: 'border-red-300',
    ring: 'ring-red-500',
    gradient: 'from-red-500 to-red-600',
    hex: '#ef4444',
  },
  high: {
    bg: 'bg-orange-100',
    bgDark: 'bg-orange-500',
    text: 'text-orange-800',
    textLight: 'text-orange-100',
    border: 'border-orange-300',
    ring: 'ring-orange-500',
    gradient: 'from-orange-500 to-orange-600',
    hex: '#f97316',
  },
  medium: {
    bg: 'bg-yellow-100',
    bgDark: 'bg-yellow-500',
    text: 'text-yellow-800',
    textLight: 'text-yellow-100',
    border: 'border-yellow-300',
    ring: 'ring-yellow-500',
    gradient: 'from-yellow-500 to-yellow-600',
    hex: '#eab308',
  },
  low: {
    bg: 'bg-blue-100',
    bgDark: 'bg-blue-500',
    text: 'text-blue-800',
    textLight: 'text-blue-100',
    border: 'border-blue-300',
    ring: 'ring-blue-500',
    gradient: 'from-blue-500 to-blue-600',
    hex: '#3b82f6',
  },
  info: {
    bg: 'bg-gray-100',
    bgDark: 'bg-gray-500',
    text: 'text-gray-800',
    textLight: 'text-gray-100',
    border: 'border-gray-300',
    ring: 'ring-gray-500',
    gradient: 'from-gray-500 to-gray-600',
    hex: '#6b7280',
  },
} as const;

// Health/Status color mappings
export const HEALTH_COLORS = {
  healthy: {
    bg: 'bg-green-100',
    bgDark: 'bg-green-500',
    text: 'text-green-800',
    textLight: 'text-green-100',
    border: 'border-green-300',
    ring: 'ring-green-500',
    gradient: 'from-green-500 to-green-600',
    hex: '#22c55e',
    icon: 'CheckCircle',
    label: 'Saudável',
  },
  warning: {
    bg: 'bg-yellow-100',
    bgDark: 'bg-yellow-500',
    text: 'text-yellow-800',
    textLight: 'text-yellow-100',
    border: 'border-yellow-300',
    ring: 'ring-yellow-500',
    gradient: 'from-yellow-500 to-yellow-600',
    hex: '#eab308',
    icon: 'AlertTriangle',
    label: 'Atenção',
  },
  critical: {
    bg: 'bg-red-100',
    bgDark: 'bg-red-500',
    text: 'text-red-800',
    textLight: 'text-red-100',
    border: 'border-red-300',
    ring: 'ring-red-500',
    gradient: 'from-red-500 to-red-600',
    hex: '#ef4444',
    icon: 'XCircle',
    label: 'Crítico',
  },
  unknown: {
    bg: 'bg-gray-100',
    bgDark: 'bg-gray-500',
    text: 'text-gray-800',
    textLight: 'text-gray-100',
    border: 'border-gray-300',
    ring: 'ring-gray-500',
    gradient: 'from-gray-500 to-gray-600',
    hex: '#6b7280',
    icon: 'HelpCircle',
    label: 'Desconhecido',
  },
  degraded: {
    bg: 'bg-orange-100',
    bgDark: 'bg-orange-500',
    text: 'text-orange-800',
    textLight: 'text-orange-100',
    border: 'border-orange-300',
    ring: 'ring-orange-500',
    gradient: 'from-orange-500 to-orange-600',
    hex: '#f97316',
    icon: 'AlertCircle',
    label: 'Degradado',
  },
} as const;

// Trend color mappings
export const TREND_COLORS = {
  up: {
    text: 'text-green-600',
    bg: 'bg-green-100',
    hex: '#22c55e',
  },
  down: {
    text: 'text-red-600',
    bg: 'bg-red-100',
    hex: '#ef4444',
  },
  stable: {
    text: 'text-gray-600',
    bg: 'bg-gray-100',
    hex: '#6b7280',
  },
} as const;

// Chart color palette
export const CHART_COLORS = {
  primary: ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'],
  secondary: ['#93c5fd', '#c4b5fd', '#67e8f9', '#6ee7b7', '#fcd34d', '#fca5a5'],
  gradient: {
    blue: ['#3b82f6', '#1d4ed8'],
    purple: ['#8b5cf6', '#7c3aed'],
    green: ['#10b981', '#059669'],
    red: ['#ef4444', '#dc2626'],
    orange: ['#f97316', '#ea580c'],
  },
} as const;

// Helper functions
export function getSeverityColor(severity: SeverityLevel | string) {
  return SEVERITY_COLORS[severity as SeverityLevel] || SEVERITY_COLORS.info;
}

export function getHealthColor(status: HealthStatus | string) {
  return HEALTH_COLORS[status as HealthStatus] || HEALTH_COLORS.unknown;
}

export function getTrendColor(trend: TrendDirection | string) {
  return TREND_COLORS[trend as TrendDirection] || TREND_COLORS.stable;
}

// Generate badge classes for severity
export function getSeverityBadgeClasses(severity: SeverityLevel | string): string {
  const colors = getSeverityColor(severity);
  return `${colors.bg} ${colors.text} ${colors.border} border`;
}

// Generate badge classes for health status
export function getHealthBadgeClasses(status: HealthStatus | string): string {
  const colors = getHealthColor(status);
  return `${colors.bg} ${colors.text} ${colors.border} border`;
}
