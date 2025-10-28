/**
 * BoxPlot Component
 *
 * Box and whisker plot for statistical distribution analysis
 * Using Plotly.js
 *
 * Use cases:
 * - Quality metrics distribution (Cpk analysis)
 * - Process capability analysis
 * - Outlier detection
 * - Batch comparison
 * - Shift performance comparison
 */

import React from 'react';
import Plot from 'react-plotly.js';

export interface BoxPlotDataset {
  name: string;
  values: number[];
  color?: string;
}

export interface BoxPlotProps {
  data: BoxPlotDataset[] | number[];  // Multiple datasets or single
  title?: string;
  xLabel?: string;
  yLabel?: string;
  showMean?: boolean;
  showOutliers?: boolean;
  orientation?: 'vertical' | 'horizontal';
  height?: number;
  width?: number | string;
  colors?: string[];
}

export const BoxPlot: React.FC<BoxPlotProps> = ({
  data,
  title,
  xLabel,
  yLabel = 'Value',
  showMean = true,
  showOutliers = true,
  orientation = 'vertical',
  height = 400,
  width = '100%',
  colors,
}) => {
  // Default colors
  const defaultColors = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
    '#8b5cf6', '#ec4899', '#14b8a6', '#f97316',
  ];

  const finalColors = colors || defaultColors;

  // Normalize data to array of datasets
  const datasets: BoxPlotDataset[] = Array.isArray(data) && typeof data[0] === 'object'
    ? (data as BoxPlotDataset[])
    : [{
        name: 'Distribution',
        values: data as number[],
        color: finalColors[0],
      }];

  // Create box plot traces
  const traces: Plotly.Data[] = datasets.map((dataset, index) => ({
    type: 'box',
    name: dataset.name,
    y: orientation === 'vertical' ? dataset.values : undefined,
    x: orientation === 'horizontal' ? dataset.values : undefined,
    orientation: orientation === 'horizontal' ? 'h' : 'v',
    marker: {
      color: dataset.color || finalColors[index % finalColors.length],
      outliercolor: '#ef4444',
      line: {
        outliercolor: '#dc2626',
        outlierwidth: 2,
      },
    },
    boxmean: showMean ? 'sd' : false,  // Show mean and std deviation
    boxpoints: showOutliers ? 'outliers' : false,
    jitter: 0.3,
    pointpos: -1.8,
    line: {
      color: '#374151',
      width: 1,
    },
    fillcolor: dataset.color ? `${dataset.color}40` : `${finalColors[index % finalColors.length]}40`,
    hovertemplate: '<b>%{fullData.name}</b><br>' +
      'Max: %{upper}<br>' +
      'Q3: %{q3}<br>' +
      'Median: %{median}<br>' +
      'Q1: %{q1}<br>' +
      'Min: %{lower}<extra></extra>',
  }));

  const layout: Partial<Plotly.Layout> = {
    title: title ? {
      text: title,
      font: { size: 18, color: '#374151' },
    } : undefined,
    height: height,
    width: typeof width === 'number' ? width : undefined,
    margin: { t: title ? 60 : 40, r: 50, l: 80, b: 80 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(249, 250, 251, 1)',

    xaxis: {
      title: {
        text: xLabel || (orientation === 'vertical' ? 'Category' : yLabel),
        font: { size: 14, color: '#374151' },
      },
      gridcolor: orientation === 'horizontal' ? '#e5e7eb' : 'rgba(0,0,0,0)',
      zerolinecolor: '#9ca3af',
      tickfont: { size: 11, color: '#6b7280' },
    },

    yaxis: {
      title: {
        text: yLabel || (orientation === 'vertical' ? yLabel : 'Category'),
        font: { size: 14, color: '#374151' },
      },
      gridcolor: orientation === 'vertical' ? '#e5e7eb' : 'rgba(0,0,0,0)',
      zerolinecolor: '#9ca3af',
      tickfont: { size: 11, color: '#6b7280' },
    },

    showlegend: datasets.length > 1,
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

  // Calculate statistics for summary
  const calculateStats = (values: number[]) => {
    const sorted = [...values].sort((a, b) => a - b);
    const n = sorted.length;
    const mean = values.reduce((a, b) => a + b, 0) / n;
    const median = n % 2 === 0
      ? (sorted[n / 2 - 1] + sorted[n / 2]) / 2
      : sorted[Math.floor(n / 2)];
    const q1 = sorted[Math.floor(n * 0.25)];
    const q3 = sorted[Math.floor(n * 0.75)];
    const iqr = q3 - q1;

    return { mean, median, q1, q3, iqr, min: sorted[0], max: sorted[n - 1] };
  };

  return (
    <div className="box-plot-container">
      <Plot
        data={traces}
        layout={layout}
        config={config}
        style={{ width: width === '100%' ? '100%' : width }}
        useResizeHandler={true}
      />

      {/* Statistics summary */}
      {datasets.length === 1 && (
        <div className="statistics-summary mt-4 grid grid-cols-4 gap-2 text-sm">
          {(() => {
            const stats = calculateStats(datasets[0].values);
            return (
              <>
                <div className="stat bg-blue-50 p-2 rounded text-center">
                  <div className="text-gray-600 text-xs">Mean</div>
                  <div className="font-semibold text-blue-900">{stats.mean.toFixed(2)}</div>
                </div>
                <div className="stat bg-green-50 p-2 rounded text-center">
                  <div className="text-gray-600 text-xs">Median</div>
                  <div className="font-semibold text-green-900">{stats.median.toFixed(2)}</div>
                </div>
                <div className="stat bg-amber-50 p-2 rounded text-center">
                  <div className="text-gray-600 text-xs">IQR</div>
                  <div className="font-semibold text-amber-900">{stats.iqr.toFixed(2)}</div>
                </div>
                <div className="stat bg-purple-50 p-2 rounded text-center">
                  <div className="text-gray-600 text-xs">Range</div>
                  <div className="font-semibold text-purple-900">
                    {(stats.max - stats.min).toFixed(2)}
                  </div>
                </div>
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
};

export default BoxPlot;
