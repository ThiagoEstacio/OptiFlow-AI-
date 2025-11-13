/**
 * PieChart Component
 *
 * Pie/Donut chart for percentage distributions
 * Using Plotly.js
 *
 * Use cases:
 * - Energy consumption by area
 * - Production distribution by product
 * - Downtime by cause
 * - Quality defects by type
 * - Resource allocation
 */

import React from 'react';
import Plot from 'react-plotly.js';

export interface PieDataSlice {
  label: string;
  value: number;
  color?: string;
}

export interface PieChartProps {
  data: PieDataSlice[];
  title?: string;
  donut?: boolean;  // Show as donut chart
  donutHoleSize?: number;  // 0-1, default 0.4
  showPercentages?: boolean;
  showValues?: boolean;
  showLegend?: boolean;
  height?: number;
  width?: number | string;
  colors?: string[];
  pullSlice?: string;  // Label of slice to pull out (emphasize)
}

export const PieChart: React.FC<PieChartProps> = ({
  data,
  title,
  donut = false,
  donutHoleSize = 0.4,
  showPercentages = true,
  showValues = false,
  showLegend = true,
  height = 400,
  width = '100%',
  colors,
  pullSlice,
}) => {
  // Default colors
  const defaultColors = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
    '#8b5cf6', '#ec4899', '#14b8a6', '#f97316',
    '#06b6d4', '#84cc16', '#a855f7', '#f43f5e',
  ];

  const finalColors = colors || data.map((_, i) => defaultColors[i % defaultColors.length]);

  // Calculate total for percentages
  const total = data.reduce((sum, item) => sum + item.value, 0);

  // Create pull array (emphasize specific slice)
  const pull = data.map(item => item.label === pullSlice ? 0.1 : 0);

  // Create text labels
  const textInfo = [];
  if (showPercentages && showValues) {
    textInfo.push('label', 'value', 'percent');
  } else if (showPercentages) {
    textInfo.push('label', 'percent');
  } else if (showValues) {
    textInfo.push('label', 'value');
  } else {
    textInfo.push('label');
  }

  const trace: Plotly.Data = {
    type: 'pie',
    labels: data.map(d => d.label),
    values: data.map(d => d.value),
    marker: {
      colors: data.map((d, i) => d.color || finalColors[i]),
      line: {
        color: 'white',
        width: 2,
      },
    },
    hole: donut ? donutHoleSize : 0,
    pull: pull,
    textinfo: textInfo.join('+') as any,
    textposition: 'auto',
    textfont: {
      size: 12,
      color: 'white',
    },
    hovertemplate: '<b>%{label}</b><br>' +
      'Value: %{value:.2f}<br>' +
      'Percentage: %{percent}<extra></extra>',
  };

  const layout: Partial<Plotly.Layout> = {
    title: title ? {
      text: title,
      font: { size: 18, color: '#374151' },
    } : undefined,
    height: height,
    width: typeof width === 'number' ? width : undefined,
    margin: { t: title ? 60 : 40, r: 40, l: 40, b: 40 },
    paper_bgcolor: 'rgba(0,0,0,0)',

    showlegend: showLegend,
    legend: {
      orientation: 'v',
      x: 1.05,
      y: 0.5,
      xanchor: 'left',
      yanchor: 'middle',
      bgcolor: 'rgba(255, 255, 255, 0.8)',
      bordercolor: '#e5e7eb',
      borderwidth: 1,
      font: { size: 11, color: '#6b7280' },
    },

    font: { family: 'Inter, system-ui, sans-serif' },

    // Donut center text
    annotations: donut ? [{
      text: `Total<br><b>${total.toFixed(0)}</b>`,
      x: 0.5,
      y: 0.5,
      font: {
        size: 16,
        color: '#374151',
      },
      showarrow: false,
      xref: 'paper',
      yref: 'paper',
    }] : [],
  };

  const config: Partial<Plotly.Config> = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    responsive: true,
  };

  return (
    <div className="pie-chart-container">
      <Plot
        data={[trace]}
        layout={layout}
        config={config}
        style={{ width: width === '100%' ? '100%' : width }}
        useResizeHandler={true}
      />

      {/* Summary statistics */}
      <div className="pie-summary mt-4 grid grid-cols-2 gap-4 text-sm">
        <div className="stat-card bg-gray-50 p-3 rounded">
          <div className="text-gray-600">Total</div>
          <div className="text-xl font-semibold text-gray-900">{total.toFixed(2)}</div>
        </div>
        <div className="stat-card bg-gray-50 p-3 rounded">
          <div className="text-gray-600">Categories</div>
          <div className="text-xl font-semibold text-gray-900">{data.length}</div>
        </div>
      </div>
    </div>
  );
};

export default PieChart;
