/**
 * Dashboard Templates
 * Pre-configured dashboard templates for common use cases
 */

import type { Widget } from '../pages/DashboardBuilderPage';

export interface DashboardTemplate {
  id: string;
  name: string;
  description: string;
  category: 'industrial' | 'analytics' | 'monitoring' | 'custom';
  thumbnail?: string;
  widgets: Omit<Widget, 'id'>[];
}

export const dashboardTemplates: DashboardTemplate[] = [
  {
    id: 'motor-monitoring',
    name: 'Motor Health Monitoring',
    description: 'Complete motor health dashboard with KPIs, trends, and status indicators',
    category: 'industrial',
    widgets: [
      {
        type: 'kpi',
        position: { x: 20, y: 20 },
        size: { width: 280, height: 180 },
        config: {
          title: 'Motor Current',
          unit: 'A',
          size: 'md',
          decimals: 1,
          showTrend: true,
          format: 'number',
          max: 300,
          min: 0,
        },
      },
      {
        type: 'kpi',
        position: { x: 320, y: 20 },
        size: { width: 280, height: 180 },
        config: {
          title: 'Motor Temperature',
          unit: '°C',
          size: 'md',
          decimals: 1,
          showTrend: true,
          format: 'number',
          max: 120,
          min: 20,
        },
      },
      {
        type: 'status',
        position: { x: 620, y: 20 },
        size: { width: 250, height: 180 },
        config: {
          title: 'Motor Status',
          status: 'running',
          size: 'md',
        },
      },
      {
        type: 'timeseries',
        position: { x: 20, y: 220 },
        size: { width: 560, height: 300 },
        config: {
          title: 'Motor Current Trend',
          timeRange: '1h',
          color: '#3B82F6',
        },
      },
      {
        type: 'gauge',
        position: { x: 600, y: 220 },
        size: { width: 270, height: 270 },
        config: {
          title: 'Vibration',
          unit: 'mm/s',
          min: 0,
          max: 15,
        },
      },
      {
        type: 'sparkline',
        position: { x: 20, y: 540 },
        size: { width: 280, height: 160 },
        config: {
          title: 'Power Consumption',
          unit: 'kW',
          sparklineStyle: 'area',
          showTrend: true,
          showMinMax: true,
        },
      },
      {
        type: 'progress',
        position: { x: 320, y: 540 },
        size: { width: 280, height: 160 },
        config: {
          title: 'Load Factor',
          unit: '%',
          min: 0,
          max: 100,
          progressType: 'bar',
          thresholds: {
            warning: 75,
            critical: 90,
          },
        },
      },
    ],
  },
  {
    id: 'production-overview',
    name: 'Production Overview',
    description: 'High-level production KPIs and status overview',
    category: 'analytics',
    widgets: [
      {
        type: 'kpi',
        position: { x: 20, y: 20 },
        size: { width: 280, height: 180 },
        config: {
          title: 'Total Production',
          unit: 't',
          size: 'lg',
          decimals: 0,
          showTrend: true,
          format: 'number',
        },
      },
      {
        type: 'kpi',
        position: { x: 320, y: 20 },
        size: { width: 280, height: 180 },
        config: {
          title: 'Throughput Rate',
          unit: 't/h',
          size: 'lg',
          decimals: 1,
          showTrend: true,
          format: 'number',
        },
      },
      {
        type: 'kpi',
        position: { x: 620, y: 20 },
        size: { width: 280, height: 180 },
        config: {
          title: 'Overall Efficiency',
          unit: '%',
          size: 'lg',
          decimals: 1,
          showTrend: true,
          format: 'percentage',
        },
      },
      {
        type: 'pie',
        position: { x: 20, y: 220 },
        size: { width: 400, height: 300 },
        config: {
          title: 'Equipment Status Distribution',
        },
      },
      {
        type: 'bar',
        position: { x: 440, y: 220 },
        size: { width: 460, height: 300 },
        config: {
          title: 'Production by Equipment',
        },
      },
      {
        type: 'table',
        position: { x: 20, y: 540 },
        size: { width: 880, height: 250 },
        config: {
          title: 'Equipment Status',
          size: 'sm',
        },
      },
    ],
  },
  {
    id: 'vessel-loading',
    name: 'Vessel Loading Dashboard',
    description: 'Monitor vessel loading progress and equipment performance',
    category: 'industrial',
    widgets: [
      {
        type: 'progress',
        position: { x: 20, y: 20 },
        size: { width: 400, height: 250 },
        config: {
          title: 'Vessel Loading Progress',
          unit: 't',
          min: 0,
          max: 50000,
          progressType: 'circular',
          target: 50000,
        },
      },
      {
        type: 'kpi',
        position: { x: 440, y: 20 },
        size: { width: 280, height: 110 },
        config: {
          title: 'Loading Rate',
          unit: 't/h',
          size: 'md',
          decimals: 0,
          showTrend: true,
          format: 'number',
        },
      },
      {
        type: 'kpi',
        position: { x: 440, y: 150 },
        size: { width: 280, height: 110 },
        config: {
          title: 'Estimated Time',
          unit: 'h',
          size: 'md',
          decimals: 1,
          showTrend: false,
          format: 'number',
        },
      },
      {
        type: 'timeseries',
        position: { x: 20, y: 290 },
        size: { width: 700, height: 300 },
        config: {
          title: 'Loading Rate History',
          timeRange: '4h',
          color: '#10B981',
        },
      },
      {
        type: 'status',
        position: { x: 20, y: 610 },
        size: { width: 220, height: 140 },
        config: {
          title: 'Shiploader',
          status: 'running',
          size: 'md',
        },
      },
      {
        type: 'status',
        position: { x: 260, y: 610 },
        size: { width: 220, height: 140 },
        config: {
          title: 'Conveyor Belt',
          status: 'running',
          size: 'md',
        },
      },
      {
        type: 'status',
        position: { x: 500, y: 610 },
        size: { width: 220, height: 140 },
        config: {
          title: 'Bucket Elevator',
          status: 'running',
          size: 'md',
        },
      },
    ],
  },
  {
    id: 'quality-control',
    name: 'Quality Control',
    description: 'Monitor product quality metrics and alarms',
    category: 'monitoring',
    widgets: [
      {
        type: 'gauge',
        position: { x: 20, y: 20 },
        size: { width: 280, height: 280 },
        config: {
          title: 'Product Moisture',
          unit: '%',
          min: 0,
          max: 100,
        },
      },
      {
        type: 'gauge',
        position: { x: 320, y: 20 },
        size: { width: 280, height: 280 },
        config: {
          title: 'Product Temperature',
          unit: '°C',
          min: -10,
          max: 60,
        },
      },
      {
        type: 'table',
        position: { x: 20, y: 320 },
        size: { width: 580, height: 300 },
        config: {
          title: 'Quality Measurements',
          size: 'md',
        },
      },
      {
        type: 'timeseries',
        position: { x: 620, y: 20 },
        size: { width: 500, height: 600 },
        config: {
          title: 'Quality Trend (24h)',
          timeRange: '24h',
          color: '#F59E0B',
        },
      },
    ],
  },
  {
    id: 'blank',
    name: 'Blank Dashboard',
    description: 'Start with an empty canvas',
    category: 'custom',
    widgets: [],
  },
];

// Get template by ID
export const getTemplate = (id: string): DashboardTemplate | undefined => {
  return dashboardTemplates.find((t) => t.id === id);
};

// Get templates by category
export const getTemplatesByCategory = (
  category: DashboardTemplate['category']
): DashboardTemplate[] => {
  return dashboardTemplates.filter((t) => t.category === category);
};
