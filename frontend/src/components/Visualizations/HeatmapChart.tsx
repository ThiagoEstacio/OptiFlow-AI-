/**
 * HeatmapChart Component
 *
 * Heatmap visualization for correlation analysis and performance matrices
 * Using Plotly.js
 *
 * Use cases:
 * - Performance analysis (hourly/daily patterns)
 * - Correlation matrices between sensors
 * - Quality heatmaps (production by shift/day)
 * - Resource utilization patterns
 */

import React from 'react';
import Plot from 'react-plotly.js';

export interface HeatmapChartProps {
  data: number[][];  // 2D matrix of values
  xLabels: string[];  // X-axis labels
  yLabels: string[];  // Y-axis labels
  title?: string;
  colorScale?: 'Viridis' | 'Jet' | 'Hot' | 'Cool' | 'Greens' | 'Blues' | 'RdBu' | 'Portland';
  showScale?: boolean;
  height?: number;
  width?: number | string;
  annotations?: boolean;  // Show values on cells
  reverseScale?: boolean;  // Reverse color scale (for "lower is better" metrics)
}

export const HeatmapChart: React.FC<HeatmapChartProps> = ({
  data,
  xLabels,
  yLabels,
  title,
  colorScale = 'Viridis',
  showScale = true,
  height = 400,
  width = '100%',
  annotations = false,
  reverseScale = false,
}) => {
  // Prepare annotations if enabled
  const cellAnnotations = annotations ? data.flatMap((row, i) =>
    row.map((value, j) => ({
      x: xLabels[j],
      y: yLabels[i],
      text: value.toFixed(2),
      font: {
        color: getContrastColor(value, data),
        size: 10,
      },
      showarrow: false,
    }))
  ) : [];

  // Calculate contrast color for text visibility
  function getContrastColor(value: number, matrix: number[][]): string {
    const flatValues = matrix.flat();
    const min = Math.min(...flatValues);
    const max = Math.max(...flatValues);
    const normalized = (value - min) / (max - min);

    // Use white text for dark colors, black for light colors
    return normalized > 0.5 ? 'white' : 'black';
  }

  const plotData: Plotly.Data[] = [
    {
      type: 'heatmap',
      z: reverseScale ? data.map(row => [...row].reverse()) : data,
      x: xLabels,
      y: yLabels,
      colorscale: colorScale,
      showscale: showScale,
      hovertemplate: '<b>%{y}</b><br>%{x}<br>Value: %{z:.2f}<extra></extra>',
      colorbar: {
        title: {
          text: 'Value',
          side: 'right',
        },
        thickness: 15,
        len: 0.7,
      },
    } as any,
  ];

  const layout: Partial<Plotly.Layout> = {
    title: title ? {
      text: title,
      font: { size: 18, color: '#374151' },
    } : undefined,
    height: height,
    width: typeof width === 'number' ? width : undefined,
    margin: { t: title ? 60 : 40, r: 50, l: 80, b: 80 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    xaxis: {
      title: '',
      tickangle: -45,
      side: 'bottom',
      tickfont: { size: 11, color: '#6b7280' },
      gridcolor: '#e5e7eb',
    },
    yaxis: {
      title: '',
      tickfont: { size: 11, color: '#6b7280' },
      gridcolor: '#e5e7eb',
    },
    annotations: cellAnnotations as any,
    font: { family: 'Inter, system-ui, sans-serif' },
  };

  const config: Partial<Plotly.Config> = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    responsive: true,
  };

  return (
    <div className="heatmap-chart-container">
      <Plot
        data={plotData}
        layout={layout}
        config={config}
        style={{ width: width === '100%' ? '100%' : width }}
        useResizeHandler={true}
      />
    </div>
  );
};

export default HeatmapChart;
