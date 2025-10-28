/**
 * GaugeChart Component
 *
 * Industrial-style gauge chart for displaying real-time KPIs
 * Using Plotly.js for high-quality visualization
 *
 * Use cases:
 * - Temperature, Pressure, Flow rate monitoring
 * - KPI indicators (OEE, Quality, Performance)
 * - Thresholds visualization (Normal, Warning, Critical)
 */

import React from 'react';
import Plot from 'react-plotly.js';

export interface GaugeThreshold {
  value: number;
  color: string;
  label: string;
}

export interface GaugeChartProps {
  value: number;
  min: number;
  max: number;
  unit?: string;
  title?: string;
  thresholds?: GaugeThreshold[];
  showDelta?: boolean;
  previousValue?: number;
  height?: number;
  width?: number | string;
}

export const GaugeChart: React.FC<GaugeChartProps> = ({
  value,
  min,
  max,
  unit = '',
  title = '',
  thresholds = [],
  showDelta = true,
  previousValue,
  height = 250,
  width = '100%',
}) => {
  // Default thresholds if none provided
  const defaultThresholds: GaugeThreshold[] = [
    { value: min, color: '#22c55e', label: 'Normal' },
    { value: (max - min) * 0.7 + min, color: '#eab308', label: 'Warning' },
    { value: (max - min) * 0.9 + min, color: '#ef4444', label: 'Critical' },
  ];

  const activeThresholds = thresholds.length > 0 ? thresholds : defaultThresholds;

  // Determine bar color based on current value
  const getBarColor = (): string => {
    for (let i = activeThresholds.length - 1; i >= 0; i--) {
      if (value >= activeThresholds[i].value) {
        return activeThresholds[i].color;
      }
    }
    return activeThresholds[0].color;
  };

  // Create steps for gauge background
  const steps = activeThresholds.map((threshold, index) => {
    const nextThreshold = activeThresholds[index + 1];
    return {
      range: [threshold.value, nextThreshold ? nextThreshold.value : max],
      color: threshold.color + '20', // Add opacity
    };
  });

  // Configure gauge data
  const data: Plotly.Data[] = [
    {
      type: 'indicator',
      mode: showDelta && previousValue !== undefined
        ? 'gauge+number+delta'
        : 'gauge+number',
      value: value,
      number: {
        suffix: unit ? ` ${unit}` : '',
        font: { size: 32, color: '#1f2937' },
      },
      delta: previousValue !== undefined ? {
        reference: previousValue,
        increasing: { color: '#22c55e' },
        decreasing: { color: '#ef4444' },
        font: { size: 16 },
      } : undefined,
      title: {
        text: title,
        font: { size: 18, color: '#374151' },
      },
      gauge: {
        axis: {
          range: [min, max],
          tickwidth: 1,
          tickcolor: '#9ca3af',
          tickfont: { size: 12, color: '#6b7280' },
        },
        bar: {
          color: getBarColor(),
          thickness: 0.75,
        },
        bgcolor: 'white',
        borderwidth: 2,
        bordercolor: '#e5e7eb',
        steps: steps,
        threshold: {
          line: { color: '#dc2626', width: 4 },
          thickness: 0.75,
          value: max * 0.95, // Show threshold line at 95%
        },
      },
    } as any,
  ];

  // Configure layout
  const layout: Partial<Plotly.Layout> = {
    height: height,
    width: typeof width === 'number' ? width : undefined,
    margin: { t: title ? 50 : 20, r: 25, l: 25, b: 25 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    font: { family: 'Inter, system-ui, sans-serif' },
  };

  // Configure options
  const config: Partial<Plotly.Config> = {
    displayModeBar: false,
    responsive: true,
  };

  return (
    <div className="gauge-chart-container">
      <Plot
        data={data}
        layout={layout}
        config={config}
        style={{ width: width === '100%' ? '100%' : width }}
        useResizeHandler={true}
      />

      {/* Legend */}
      {activeThresholds.length > 0 && (
        <div className="gauge-legend flex justify-center gap-4 mt-2 text-sm">
          {activeThresholds.map((threshold, index) => (
            <div key={index} className="flex items-center gap-1">
              <div
                className="w-3 h-3 rounded-sm"
                style={{ backgroundColor: threshold.color }}
              />
              <span className="text-gray-600">{threshold.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default GaugeChart;
