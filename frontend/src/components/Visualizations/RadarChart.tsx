/**
 * RadarChart Component
 *
 * Spider/Radar chart for multi-dimensional comparisons
 * Using Plotly.js
 *
 * Use cases:
 * - OEE comparison (Availability, Performance, Quality)
 * - Equipment performance across multiple KPIs
 * - Shift comparison (productivity, quality, safety, etc.)
 * - Product quality dimensions
 * - Supplier scorecards
 */

import React from 'react';
import Plot from 'react-plotly.js';

export interface RadarDataSeries {
  name: string;
  values: number[];
  color?: string;
  fillOpacity?: number;
}

export interface RadarChartProps {
  categories: string[];  // Dimensions (e.g., ["Availability", "Performance", "Quality"])
  data: RadarDataSeries[];  // Multiple series to compare
  title?: string;
  height?: number;
  width?: number | string;
  fillArea?: boolean;
  showGrid?: boolean;
  maxValue?: number;  // Max value for radial axis (auto-calculated if not provided)
}

export const RadarChart: React.FC<RadarChartProps> = ({
  categories,
  data,
  title,
  height = 500,
  width = '100%',
  fillArea = true,
  showGrid = true,
  maxValue,
}) => {
  // Default colors
  const defaultColors = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
    '#8b5cf6', '#ec4899', '#14b8a6', '#f97316',
  ];

  // Auto-calculate max value if not provided
  const calculatedMaxValue = maxValue || Math.max(
    ...data.flatMap(series => series.values),
    100  // Minimum of 100
  );

  // Create traces for each series
  const traces: Plotly.Data[] = data.map((series, index) => ({
    type: 'scatterpolar',
    r: [...series.values, series.values[0]],  // Close the polygon
    theta: [...categories, categories[0]],
    fill: fillArea ? 'toself' : 'none',
    fillcolor: series.color
      ? `${series.color}${Math.round((series.fillOpacity || 0.3) * 255).toString(16).padStart(2, '0')}`
      : `${defaultColors[index % defaultColors.length]}4D`,
    name: series.name,
    line: {
      color: series.color || defaultColors[index % defaultColors.length],
      width: 2,
    },
    marker: {
      size: 6,
      color: series.color || defaultColors[index % defaultColors.length],
    },
    hovertemplate: '<b>%{fullData.name}</b><br>' +
      '%{theta}: %{r:.1f}<extra></extra>',
  }));

  const layout: Partial<Plotly.Layout> = {
    title: title ? {
      text: title,
      font: { size: 18, color: '#374151' },
    } : undefined,
    height: height,
    width: typeof width === 'number' ? width : undefined,
    margin: { t: title ? 80 : 60, r: 80, l: 80, b: 60 },
    paper_bgcolor: 'rgba(0,0,0,0)',

    polar: {
      radialaxis: {
        visible: true,
        range: [0, calculatedMaxValue],
        gridcolor: showGrid ? '#e5e7eb' : 'rgba(0,0,0,0)',
        tickfont: { size: 11, color: '#6b7280' },
      },
      angularaxis: {
        gridcolor: showGrid ? '#e5e7eb' : 'rgba(0,0,0,0)',
        linecolor: '#9ca3af',
        tickfont: { size: 12, color: '#374151' },
      },
      bgcolor: 'rgba(249, 250, 251, 1)',
    },

    showlegend: true,
    legend: {
      x: 1.1,
      y: 0.5,
      xanchor: 'left',
      yanchor: 'middle',
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

  // Calculate averages for each series
  const averages = data.map(series => ({
    name: series.name,
    average: series.values.reduce((a, b) => a + b, 0) / series.values.length,
    color: series.color || defaultColors[data.indexOf(series) % defaultColors.length],
  }));

  return (
    <div className="radar-chart-container">
      <Plot
        data={traces}
        layout={layout}
        config={config}
        style={{ width: width === '100%' ? '100%' : width }}
        useResizeHandler={true}
      />

      {/* Series averages */}
      <div className="radar-averages mt-4 flex justify-center gap-4">
        {averages.map((avg, index) => (
          <div
            key={index}
            className="average-card bg-gray-50 px-4 py-2 rounded border-l-4"
            style={{ borderColor: avg.color }}
          >
            <div className="text-xs text-gray-600">{avg.name} Average</div>
            <div className="text-lg font-semibold" style={{ color: avg.color }}>
              {avg.average.toFixed(1)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RadarChart;
