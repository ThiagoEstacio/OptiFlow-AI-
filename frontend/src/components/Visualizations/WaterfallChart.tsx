/**
 * WaterfallChart Component
 *
 * Waterfall chart for analyzing sequential contributions (gains/losses)
 * Using Plotly.js
 *
 * Use cases:
 * - OEE loss analysis (Availability, Performance, Quality)
 * - Production efficiency breakdown
 * - Cost/profit analysis
 * - Energy loss cascade
 * - Process yield analysis
 */

import React from 'react';
import Plot from 'react-plotly.js';

export interface WaterfallItem {
  label: string;
  value: number;
  type: 'initial' | 'increase' | 'decrease' | 'total';
}

export interface WaterfallChartProps {
  data: WaterfallItem[];
  title?: string;
  xLabel?: string;
  yLabel?: string;
  height?: number;
  width?: number | string;
  increaseColor?: string;
  decreaseColor?: string;
  totalColor?: string;
  showConnectors?: boolean;
}

export const WaterfallChart: React.FC<WaterfallChartProps> = ({
  data,
  title,
  xLabel,
  yLabel = 'Value',
  height = 400,
  width = '100%',
  increaseColor = '#10b981',  // green
  decreaseColor = '#ef4444',  // red
  totalColor = '#3b82f6',     // blue
  showConnectors = true,
}) => {
  // Prepare data for Plotly waterfall
  const labels = data.map(item => item.label);
  const values = data.map(item => item.value);

  // Map measure types
  const measures = data.map(item => {
    if (item.type === 'initial' || item.type === 'total') return 'total';
    return 'relative';
  });

  // Determine colors based on increase/decrease
  const colors = data.map(item => {
    if (item.type === 'total' || item.type === 'initial') return totalColor;
    return item.value >= 0 ? increaseColor : decreaseColor;
  });

  const trace: Plotly.Data = {
    type: 'waterfall',
    name: 'Contribution Analysis',
    orientation: 'v',
    x: labels,
    y: values,
    measure: measures,
    text: values.map(v => v.toFixed(1)),
    textposition: 'outside',
    textfont: {
      size: 11,
      color: '#1f2937',
    },
    increasing: { marker: { color: increaseColor } },
    decreasing: { marker: { color: decreaseColor } },
    totals: { marker: { color: totalColor } },
    connector: showConnectors ? {
      line: {
        color: '#9ca3af',
        width: 2,
        dash: 'dot',
      },
    } : { visible: false },
    hovertemplate: '<b>%{x}</b><br>' +
      'Value: %{y:.2f}<br>' +
      '<extra></extra>',
  } as any;

  const layout: Partial<Plotly.Layout> = {
    title: title ? {
      text: title,
      font: { size: 18, color: '#374151' },
    } : undefined,
    height: height,
    width: typeof width === 'number' ? width : undefined,
    margin: { t: title ? 60 : 40, r: 50, l: 80, b: 100 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(249, 250, 251, 1)',

    xaxis: {
      title: {
        text: xLabel || 'Steps',
        font: { size: 14, color: '#374151' },
      },
      gridcolor: 'rgba(0,0,0,0)',
      tickfont: { size: 11, color: '#6b7280' },
      tickangle: -45,
    },

    yaxis: {
      title: {
        text: yLabel,
        font: { size: 14, color: '#374151' },
      },
      gridcolor: '#e5e7eb',
      zerolinecolor: '#9ca3af',
      tickfont: { size: 11, color: '#6b7280' },
    },

    showlegend: false,

    font: { family: 'Inter, system-ui, sans-serif' },
  };

  const config: Partial<Plotly.Config> = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    responsive: true,
  };

  // Calculate summary statistics
  const initial = data.find(item => item.type === 'initial')?.value || 0;
  const final = data.find(item => item.type === 'total')?.value || 0;
  const totalIncrease = data
    .filter(item => item.type === 'increase' && item.value > 0)
    .reduce((sum, item) => sum + item.value, 0);
  const totalDecrease = Math.abs(data
    .filter(item => item.type === 'decrease' || (item.type === 'increase' && item.value < 0))
    .reduce((sum, item) => sum + item.value, 0));
  const netChange = final - initial;

  return (
    <div className="waterfall-chart-container">
      <Plot
        data={[trace]}
        layout={layout}
        config={config}
        style={{ width: width === '100%' ? '100%' : width }}
        useResizeHandler={true}
      />

      {/* Summary cards */}
      <div className="waterfall-summary mt-4 grid grid-cols-4 gap-3 text-sm">
        <div className="stat-card bg-blue-50 p-3 rounded">
          <div className="text-gray-600 text-xs">Initial</div>
          <div className="text-lg font-semibold text-blue-900">{initial.toFixed(1)}</div>
        </div>

        <div className="stat-card bg-green-50 p-3 rounded">
          <div className="text-gray-600 text-xs">Total Gains</div>
          <div className="text-lg font-semibold text-green-900">+{totalIncrease.toFixed(1)}</div>
        </div>

        <div className="stat-card bg-red-50 p-3 rounded">
          <div className="text-gray-600 text-xs">Total Losses</div>
          <div className="text-lg font-semibold text-red-900">-{totalDecrease.toFixed(1)}</div>
        </div>

        <div className="stat-card bg-purple-50 p-3 rounded">
          <div className="text-gray-600 text-xs">Final</div>
          <div className="text-lg font-semibold text-purple-900">{final.toFixed(1)}</div>
        </div>
      </div>

      {/* Net change indicator */}
      <div className="net-change mt-3 text-center">
        <span className="text-gray-600 text-sm">Net Change: </span>
        <span className={`font-semibold ${netChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {netChange >= 0 ? '+' : ''}{netChange.toFixed(1)}
          {' '}({((netChange / initial) * 100).toFixed(1)}%)
        </span>
      </div>
    </div>
  );
};

export default WaterfallChart;
