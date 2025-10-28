/**
 * ScatterPlot Component
 *
 * Scatter plot for correlation analysis and relationship visualization
 * Using Plotly.js
 *
 * Use cases:
 * - Correlation analysis between two variables
 * - Quality vs. Process parameter analysis
 * - Predictive model visualization
 * - Clustering and pattern detection
 */

import React from 'react';
import Plot from 'react-plotly.js';

export interface ScatterDataPoint {
  x: number;
  y: number;
  label?: string;
  group?: string;
}

export interface ScatterPlotProps {
  data: ScatterDataPoint[] | number[];  // Array of points or just y values
  xData?: number[];  // If data is just y values, provide x values here
  xLabel?: string;
  yLabel?: string;
  title?: string;
  showTrendline?: boolean;
  showCorrelation?: boolean;
  groups?: string[];  // For multi-group scatter plots
  colorByGroup?: boolean;
  height?: number;
  width?: number | string;
  markerSize?: number;
  markerColor?: string;
}

export const ScatterPlot: React.FC<ScatterPlotProps> = ({
  data,
  xData,
  xLabel = 'X Axis',
  yLabel = 'Y Axis',
  title,
  showTrendline = false,
  showCorrelation = false,
  groups,
  colorByGroup = false,
  height = 400,
  width = '100%',
  markerSize = 8,
  markerColor = '#3b82f6',
}) => {
  // Normalize data to ScatterDataPoint[]
  const normalizedData: ScatterDataPoint[] = Array.isArray(data) && typeof data[0] === 'number'
    ? (data as number[]).map((y, i) => ({
        x: xData ? xData[i] : i,
        y: y,
      }))
    : (data as ScatterDataPoint[]);

  // Calculate correlation if requested
  const correlation = showCorrelation ? calculateCorrelation(normalizedData) : null;

  // Calculate trendline if requested
  const trendlineData = showTrendline ? calculateTrendline(normalizedData) : null;

  // Group data if needed
  const groupedData = colorByGroup && groups
    ? groupDataByProperty(normalizedData)
    : { 'All Data': normalizedData };

  // Create scatter traces
  const scatterTraces: Plotly.Data[] = Object.entries(groupedData).map(([groupName, points]) => ({
    type: 'scatter',
    mode: 'markers',
    name: groupName,
    x: points.map(p => p.x),
    y: points.map(p => p.y),
    text: points.map(p => p.label || ''),
    marker: {
      size: markerSize,
      color: colorByGroup ? undefined : markerColor,
      opacity: 0.7,
      line: {
        color: 'white',
        width: 1,
      },
    },
    hovertemplate: '<b>%{text}</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<extra></extra>',
  }));

  // Add trendline if calculated
  if (trendlineData) {
    scatterTraces.push({
      type: 'scatter',
      mode: 'lines',
      name: 'Trendline',
      x: trendlineData.x,
      y: trendlineData.y,
      line: {
        color: '#ef4444',
        width: 2,
        dash: 'dash',
      },
      hoverinfo: 'skip',
    });
  }

  const layout: Partial<Plotly.Layout> = {
    title: title ? {
      text: title,
      font: { size: 18, color: '#374151' },
    } : undefined,
    height: height,
    width: typeof width === 'number' ? width : undefined,
    margin: { t: title ? 60 : 40, r: 50, l: 60, b: 60 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(249, 250, 251, 1)',
    xaxis: {
      title: {
        text: xLabel,
        font: { size: 14, color: '#374151' },
      },
      gridcolor: '#e5e7eb',
      zerolinecolor: '#9ca3af',
      tickfont: { size: 11, color: '#6b7280' },
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
    showlegend: colorByGroup || showTrendline,
    legend: {
      x: 1,
      y: 1,
      xanchor: 'right',
      bgcolor: 'rgba(255, 255, 255, 0.8)',
      bordercolor: '#e5e7eb',
      borderwidth: 1,
    },
    font: { family: 'Inter, system-ui, sans-serif' },
    annotations: showCorrelation && correlation !== null ? [{
      text: `Correlation: ${correlation.toFixed(3)}`,
      xref: 'paper',
      yref: 'paper',
      x: 0.02,
      y: 0.98,
      xanchor: 'left',
      yanchor: 'top',
      showarrow: false,
      bgcolor: 'rgba(255, 255, 255, 0.9)',
      bordercolor: '#e5e7eb',
      borderwidth: 1,
      borderpad: 8,
      font: { size: 14, color: '#374151' },
    }] : [],
  };

  const config: Partial<Plotly.Config> = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    responsive: true,
  };

  return (
    <div className="scatter-plot-container">
      <Plot
        data={scatterTraces}
        layout={layout}
        config={config}
        style={{ width: width === '100%' ? '100%' : width }}
        useResizeHandler={true}
      />

      {/* Correlation indicator */}
      {showCorrelation && correlation !== null && (
        <div className="correlation-indicator mt-2 text-center text-sm text-gray-600">
          {correlation > 0.7 && (
            <span className="text-green-600 font-medium">Strong Positive Correlation</span>
          )}
          {correlation < -0.7 && (
            <span className="text-red-600 font-medium">Strong Negative Correlation</span>
          )}
          {correlation >= -0.3 && correlation <= 0.3 && (
            <span className="text-gray-500">Weak Correlation</span>
          )}
          {correlation > 0.3 && correlation <= 0.7 && (
            <span className="text-blue-600">Moderate Positive Correlation</span>
          )}
          {correlation < -0.3 && correlation >= -0.7 && (
            <span className="text-orange-600">Moderate Negative Correlation</span>
          )}
        </div>
      )}
    </div>
  );
};

// Helper functions

function calculateCorrelation(data: ScatterDataPoint[]): number {
  const n = data.length;
  if (n < 2) return 0;

  const xValues = data.map(p => p.x);
  const yValues = data.map(p => p.y);

  const sumX = xValues.reduce((a, b) => a + b, 0);
  const sumY = yValues.reduce((a, b) => a + b, 0);
  const sumXY = xValues.reduce((sum, x, i) => sum + x * yValues[i], 0);
  const sumX2 = xValues.reduce((sum, x) => sum + x * x, 0);
  const sumY2 = yValues.reduce((sum, y) => sum + y * y, 0);

  const numerator = n * sumXY - sumX * sumY;
  const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));

  if (denominator === 0) return 0;

  return numerator / denominator;
}

function calculateTrendline(data: ScatterDataPoint[]): { x: number[]; y: number[] } | null {
  const n = data.length;
  if (n < 2) return null;

  const xValues = data.map(p => p.x);
  const yValues = data.map(p => p.y);

  const sumX = xValues.reduce((a, b) => a + b, 0);
  const sumY = yValues.reduce((a, b) => a + b, 0);
  const sumXY = xValues.reduce((sum, x, i) => sum + x * yValues[i], 0);
  const sumX2 = xValues.reduce((sum, x) => sum + x * x, 0);

  // Calculate slope (m) and intercept (b) for y = mx + b
  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;

  // Generate trendline points
  const minX = Math.min(...xValues);
  const maxX = Math.max(...xValues);

  return {
    x: [minX, maxX],
    y: [slope * minX + intercept, slope * maxX + intercept],
  };
}

function groupDataByProperty(data: ScatterDataPoint[]): Record<string, ScatterDataPoint[]> {
  const grouped: Record<string, ScatterDataPoint[]> = {};

  data.forEach(point => {
    const group = point.group || 'Ungrouped';
    if (!grouped[group]) {
      grouped[group] = [];
    }
    grouped[group].push(point);
  });

  return grouped;
}

export default ScatterPlot;
