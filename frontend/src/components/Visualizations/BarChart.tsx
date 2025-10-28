/**
 * BarChart Component
 *
 * Versatile bar/column chart for categorical comparisons
 * Using Plotly.js
 *
 * Use cases:
 * - Production by shift/day/month
 * - Quality metrics by product
 * - Energy consumption by area
 * - Downtime by equipment
 * - Defects by type (Pareto-style)
 */

import React from 'react';
import Plot from 'react-plotly.js';

export interface BarDataSeries {
  name: string;
  values: number[];
  color?: string;
}

export interface BarChartProps {
  categories: string[];  // X-axis labels
  data: number[] | BarDataSeries[];  // Single series or multiple
  orientation?: 'vertical' | 'horizontal';
  stacked?: boolean;
  grouped?: boolean;
  showValues?: boolean;  // Show values on bars
  title?: string;
  xLabel?: string;
  yLabel?: string;
  height?: number;
  width?: number | string;
  colors?: string[];
  sortBars?: 'ascending' | 'descending' | 'none';
}

export const BarChart: React.FC<BarChartProps> = ({
  categories,
  data,
  orientation = 'vertical',
  stacked = false,
  grouped = false,
  showValues = false,
  title,
  xLabel,
  yLabel,
  height = 400,
  width = '100%',
  colors,
  sortBars = 'none',
}) => {
  // Default colors
  const defaultColors = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
    '#8b5cf6', '#ec4899', '#14b8a6', '#f97316',
  ];

  const finalColors = colors || defaultColors;

  // Normalize data to array of series
  const series: BarDataSeries[] = Array.isArray(data) && typeof data[0] === 'object'
    ? (data as BarDataSeries[])
    : [{
        name: 'Value',
        values: data as number[],
        color: finalColors[0],
      }];

  // Sort if requested
  let sortedCategories = [...categories];
  let sortedSeries = series.map(s => ({ ...s, values: [...s.values] }));

  if (sortBars !== 'none' && series.length === 1) {
    // Only sort for single series
    const combined = sortedCategories.map((cat, i) => ({
      category: cat,
      value: series[0].values[i],
    }));

    combined.sort((a, b) =>
      sortBars === 'ascending'
        ? a.value - b.value
        : b.value - a.value
    );

    sortedCategories = combined.map(c => c.category);
    sortedSeries[0].values = combined.map(c => c.value);
  }

  // Create traces
  const traces: Plotly.Data[] = sortedSeries.map((s, index) => ({
    type: 'bar',
    name: s.name,
    x: orientation === 'vertical' ? sortedCategories : s.values,
    y: orientation === 'vertical' ? s.values : sortedCategories,
    orientation: orientation === 'horizontal' ? 'h' : 'v',
    marker: {
      color: s.color || finalColors[index % finalColors.length],
      line: {
        color: 'white',
        width: 1,
      },
    },
    text: showValues ? s.values.map(v => v.toFixed(1)) : [],
    textposition: 'auto',
    textfont: {
      size: 11,
      color: '#1f2937',
    },
    hovertemplate: `<b>${s.name}</b><br>` +
      (orientation === 'vertical' ? '%{x}<br>' : '') +
      `Value: %{${orientation === 'vertical' ? 'y' : 'x'}:.2f}<extra></extra>`,
  }));

  const layout: Partial<Plotly.Layout> = {
    title: title ? {
      text: title,
      font: { size: 18, color: '#374151' },
    } : undefined,
    height: height,
    width: typeof width === 'number' ? width : undefined,
    margin: {
      t: title ? 60 : 40,
      r: 50,
      l: orientation === 'horizontal' ? 120 : 60,
      b: orientation === 'vertical' ? 80 : 60,
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(249, 250, 251, 1)',

    xaxis: {
      title: {
        text: xLabel || (orientation === 'vertical' ? 'Category' : 'Value'),
        font: { size: 14, color: '#374151' },
      },
      gridcolor: '#e5e7eb',
      zerolinecolor: '#9ca3af',
      tickfont: { size: 11, color: '#6b7280' },
      tickangle: orientation === 'vertical' ? -45 : 0,
    },

    yaxis: {
      title: {
        text: yLabel || (orientation === 'vertical' ? 'Value' : 'Category'),
        font: { size: 14, color: '#374151' },
      },
      gridcolor: orientation === 'vertical' ? '#e5e7eb' : 'rgba(0,0,0,0)',
      zerolinecolor: '#9ca3af',
      tickfont: { size: 11, color: '#6b7280' },
    },

    barmode: stacked ? 'stack' : grouped ? 'group' : 'group',
    bargap: 0.15,
    bargroupgap: 0.1,

    showlegend: series.length > 1,
    legend: {
      x: 1,
      y: 1,
      xanchor: 'right',
      yanchor: 'top',
      bgcolor: 'rgba(255, 255, 255, 0.8)',
      bordercolor: '#e5e7eb',
      borderwidth: 1,
    },

    font: { family: 'Inter, system-ui, sans-serif' },
  };

  const config: Partial<Plotly.Config> = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    responsive: true,
  };

  return (
    <div className="bar-chart-container">
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

export default BarChart;
