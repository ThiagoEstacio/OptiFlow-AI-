/**
 * TreemapChart Component
 *
 * Treemap for hierarchical data visualization
 * Using Plotly.js
 *
 * Use cases:
 * - Production volume by product hierarchy
 * - Cost allocation by department/category
 * - Inventory distribution
 * - Energy consumption by area/equipment
 * - Defect distribution by category
 */

import React from 'react';
import Plot from 'react-plotly.js';

export interface TreemapItem {
  label: string;
  parent: string;  // Empty string for root items
  value: number;
  color?: string;
  category?: string;  // Optional category for grouping
}

export interface TreemapChartProps {
  data: TreemapItem[];
  title?: string;
  height?: number;
  width?: number | string;
  colorScale?: 'Viridis' | 'Blues' | 'Greens' | 'Reds' | 'Portland';
  showValues?: boolean;
  showPercentages?: boolean;
}

export const TreemapChart: React.FC<TreemapChartProps> = ({
  data,
  title,
  height = 500,
  width = '100%',
  colorScale = 'Viridis',
  showValues = true,
  showPercentages = false,
}) => {
  // Calculate total for percentages
  const total = data.reduce((sum, item) => sum + item.value, 0);

  // Prepare text labels
  const textInfo = [];
  if (showValues && showPercentages) {
    textInfo.push('label', 'value', 'percent parent');
  } else if (showValues) {
    textInfo.push('label', 'value');
  } else if (showPercentages) {
    textInfo.push('label', 'percent parent');
  } else {
    textInfo.push('label');
  }

  const trace: Plotly.Data = {
    type: 'treemap',
    labels: data.map(item => item.label),
    parents: data.map(item => item.parent),
    values: data.map(item => item.value),
    text: data.map(item => item.label),
    textinfo: textInfo.join('+'),
    textposition: 'middle center',
    textfont: {
      size: 12,
      color: 'white',
    },
    marker: {
      colorscale: colorScale,
      cmid: total / 2,
      colorbar: {
        title: 'Value',
        thickness: 15,
        len: 0.7,
      },
      line: {
        color: 'white',
        width: 2,
      },
    },
    hovertemplate: '<b>%{label}</b><br>' +
      'Value: %{value:.2f}<br>' +
      'Percentage: %{percentParent}<extra></extra>',
    pathbar: {
      visible: true,
      thickness: 20,
      textfont: {
        size: 11,
        color: '#374151',
      },
    },
  } as any;

  const layout: Partial<Plotly.Layout> = {
    title: title ? {
      text: title,
      font: { size: 18, color: '#374151' },
    } : undefined,
    height: height,
    width: typeof width === 'number' ? width : undefined,
    margin: { t: title ? 80 : 60, r: 40, l: 40, b: 40 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    font: { family: 'Inter, system-ui, sans-serif' },
  };

  const config: Partial<Plotly.Config> = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    responsive: true,
  };

  // Calculate hierarchy levels
  const rootItems = data.filter(item => !item.parent || item.parent === '');
  const childItems = data.filter(item => item.parent && item.parent !== '');

  return (
    <div className="treemap-chart-container">
      <Plot
        data={[trace]}
        layout={layout}
        config={config}
        style={{ width: width === '100%' ? '100%' : width }}
        useResizeHandler={true}
      />

      {/* Summary statistics */}
      <div className="treemap-summary mt-4 grid grid-cols-3 gap-4 text-sm">
        <div className="stat-card bg-blue-50 p-3 rounded">
          <div className="text-gray-600 text-xs">Total Value</div>
          <div className="text-lg font-semibold text-blue-900">{total.toFixed(1)}</div>
        </div>

        <div className="stat-card bg-green-50 p-3 rounded">
          <div className="text-gray-600 text-xs">Root Categories</div>
          <div className="text-lg font-semibold text-green-900">{rootItems.length}</div>
        </div>

        <div className="stat-card bg-purple-50 p-3 rounded">
          <div className="text-gray-600 text-xs">Sub-Categories</div>
          <div className="text-lg font-semibold text-purple-900">{childItems.length}</div>
        </div>
      </div>

      {/* Top contributors */}
      {rootItems.length > 0 && (
        <div className="top-contributors mt-4">
          <div className="text-sm font-medium text-gray-700 mb-2">Top Categories:</div>
          <div className="grid grid-cols-2 gap-2">
            {rootItems
              .sort((a, b) => b.value - a.value)
              .slice(0, 4)
              .map((item, index) => (
                <div key={index} className="flex justify-between items-center bg-gray-50 p-2 rounded text-xs">
                  <span className="font-medium text-gray-700">{item.label}</span>
                  <span className="text-gray-900 font-semibold">
                    {item.value.toFixed(1)} ({((item.value / total) * 100).toFixed(1)}%)
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TreemapChart;
