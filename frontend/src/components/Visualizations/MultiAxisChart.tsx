/**
 * MultiAxisChart Component
 *
 * Advanced trending chart with multiple Y-axes for different units
 * Using Plotly.js
 *
 * Use cases:
 * - Temperature (°C) + Pressure (bar) on same chart
 * - Production rate + Energy consumption
 * - Multiple process variables with different scales
 * - Correlation visualization over time
 */

import React from 'react';
import Plot from 'react-plotly.js';

export interface SeriesConfig {
  name: string;
  data: number[];
  yAxis: 'left' | 'right';
  unit: string;
  color?: string;
  lineStyle?: 'solid' | 'dash' | 'dot' | 'dashdot';
  lineWidth?: number;
  showMarkers?: boolean;
}

export interface MultiAxisChartProps {
  timestamps: string[] | Date[];  // X-axis values
  series: SeriesConfig[];
  title?: string;
  leftAxisTitle?: string;
  rightAxisTitle?: string;
  height?: number;
  width?: number | string;
  showLegend?: boolean;
  showGrid?: boolean;
  showCrosshair?: boolean;
}

export const MultiAxisChart: React.FC<MultiAxisChartProps> = ({
  timestamps,
  series,
  title,
  leftAxisTitle,
  rightAxisTitle,
  height = 400,
  width = '100%',
  showLegend = true,
  showGrid = true,
  showCrosshair = true,
}) => {
  // Default colors if not specified
  const defaultColors = [
    '#3b82f6', // blue
    '#ef4444', // red
    '#10b981', // green
    '#f59e0b', // amber
    '#8b5cf6', // purple
    '#ec4899', // pink
    '#14b8a6', // teal
    '#f97316', // orange
  ];

  // Map line styles to Plotly dash types
  const getDashType = (style?: string): string => {
    switch (style) {
      case 'dash': return 'dash';
      case 'dot': return 'dot';
      case 'dashdot': return 'dashdot';
      default: return 'solid';
    }
  };

  // Create traces for each series
  const traces: Plotly.Data[] = series.map((s, index) => ({
    type: 'scatter',
    mode: s.showMarkers ? 'lines+markers' : 'lines',
    name: `${s.name} (${s.unit})`,
    x: timestamps,
    y: s.data,
    yaxis: s.yAxis === 'right' ? 'y2' : 'y',
    line: {
      color: s.color || defaultColors[index % defaultColors.length],
      width: s.lineWidth || 2,
      dash: getDashType(s.lineStyle),
    },
    marker: s.showMarkers ? {
      size: 4,
      color: s.color || defaultColors[index % defaultColors.length],
    } : undefined,
    hovertemplate: `<b>${s.name}</b><br>` +
      '%{x}<br>' +
      `Value: %{y:.2f} ${s.unit}<extra></extra>`,
  }));

  // Determine axis titles from series if not provided
  const leftSeries = series.find(s => s.yAxis === 'left');
  const rightSeries = series.find(s => s.yAxis === 'right');

  const layout: Partial<Plotly.Layout> = {
    title: title ? {
      text: title,
      font: { size: 18, color: '#374151' },
    } : undefined,
    height: height,
    width: typeof width === 'number' ? width : undefined,
    margin: { t: title ? 60 : 40, r: rightSeries ? 80 : 50, l: 80, b: 60 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(249, 250, 251, 1)',

    // Left Y-axis
    yaxis: {
      title: {
        text: leftAxisTitle || (leftSeries ? `${leftSeries.name} (${leftSeries.unit})` : ''),
        font: { size: 14, color: '#374151' },
      },
      side: 'left',
      gridcolor: showGrid ? '#e5e7eb' : 'rgba(0,0,0,0)',
      zerolinecolor: '#9ca3af',
      tickfont: { size: 11, color: '#6b7280' },
    },

    // Right Y-axis (only if there are right-axis series)
    yaxis2: rightSeries ? {
      title: {
        text: rightAxisTitle || `${rightSeries.name} (${rightSeries.unit})`,
        font: { size: 14, color: '#374151' },
      },
      side: 'right',
      overlaying: 'y',
      gridcolor: 'rgba(0,0,0,0)',  // Don't show grid for right axis
      zerolinecolor: '#9ca3af',
      tickfont: { size: 11, color: '#6b7280' },
    } : undefined,

    // X-axis (time)
    xaxis: {
      title: {
        text: 'Time',
        font: { size: 14, color: '#374151' },
      },
      gridcolor: showGrid ? '#e5e7eb' : 'rgba(0,0,0,0)',
      zerolinecolor: '#9ca3af',
      tickfont: { size: 11, color: '#6b7280' },
      tickangle: -45,
    },

    showlegend: showLegend,
    legend: {
      x: 0,
      y: 1.15,
      xanchor: 'left',
      yanchor: 'top',
      orientation: 'h',
      bgcolor: 'rgba(255, 255, 255, 0.8)',
      bordercolor: '#e5e7eb',
      borderwidth: 1,
    },

    hovermode: showCrosshair ? 'x unified' : 'closest',

    font: { family: 'Inter, system-ui, sans-serif' },
  };

  const config: Partial<Plotly.Config> = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    responsive: true,
  };

  return (
    <div className="multi-axis-chart-container">
      <Plot
        data={traces}
        layout={layout}
        config={config}
        style={{ width: width === '100%' ? '100%' : width }}
        useResizeHandler={true}
      />
    </div>
  );
};

export default MultiAxisChart;
