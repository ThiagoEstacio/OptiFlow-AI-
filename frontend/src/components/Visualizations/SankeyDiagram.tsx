/**
 * SankeyDiagram Component
 *
 * Sankey diagram for flow visualization
 * Using Plotly.js
 *
 * Use cases:
 * - Energy flow analysis
 * - Material flow tracking
 * - Cost allocation
 * - Production workflow
 * - Waste stream analysis
 */

import React from 'react';
import Plot from 'react-plotly.js';

export interface SankeyLink {
  source: string | number;  // Source node name or index
  target: string | number;  // Target node name or index
  value: number;            // Flow value
  color?: string;           // Link color (optional)
}

export interface SankeyNode {
  label: string;
  color?: string;
}

export interface SankeyDiagramProps {
  nodes: SankeyNode[];
  links: SankeyLink[];
  title?: string;
  height?: number;
  width?: number | string;
  orientation?: 'horizontal' | 'vertical';
  showValues?: boolean;
}

export const SankeyDiagram: React.FC<SankeyDiagramProps> = ({
  nodes,
  links,
  title,
  height = 500,
  width = '100%',
  orientation = 'horizontal',
  showValues = true,
}) => {
  // Default node colors
  const defaultNodeColors = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
    '#8b5cf6', '#ec4899', '#14b8a6', '#f97316',
    '#06b6d4', '#84cc16', '#a855f7', '#f43f5e',
  ];

  // Default link color (semi-transparent based on source node)
  const defaultLinkColor = 'rgba(100, 116, 139, 0.3)';

  // Create node index map
  const nodeIndexMap = new Map(nodes.map((node, i) => [node.label, i]));

  // Convert links to use indices
  const linkIndices = links.map(link => ({
    source: typeof link.source === 'string' ? nodeIndexMap.get(link.source)! : link.source,
    target: typeof link.target === 'string' ? nodeIndexMap.get(link.target)! : link.target,
    value: link.value,
    color: link.color || defaultLinkColor,
  }));

  const trace: Plotly.Data = {
    type: 'sankey',
    orientation: orientation === 'vertical' ? 'v' : 'h',
    node: {
      pad: 15,
      thickness: 20,
      line: {
        color: 'white',
        width: 2,
      },
      label: nodes.map(n => n.label),
      color: nodes.map((n, i) => n.color || defaultNodeColors[i % defaultNodeColors.length]),
      hovertemplate: '<b>%{label}</b><br>Total Flow: %{value:.2f}<extra></extra>',
    },
    link: {
      source: linkIndices.map(l => l.source),
      target: linkIndices.map(l => l.target),
      value: linkIndices.map(l => l.value),
      color: linkIndices.map(l => l.color),
      hovertemplate: '%{source.label} → %{target.label}<br>Flow: %{value:.2f}<extra></extra>',
    },
    textfont: {
      size: 12,
      color: 'white',
    },
  } as any;

  const layout: Partial<Plotly.Layout> = {
    title: title ? {
      text: title,
      font: { size: 18, color: '#374151' },
    } : undefined,
    height: height,
    width: typeof width === 'number' ? width : undefined,
    margin: { t: title ? 60 : 40, r: 40, l: 40, b: 40 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    font: { family: 'Inter, system-ui, sans-serif', size: 11, color: '#374151' },
  };

  const config: Partial<Plotly.Config> = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    responsive: true,
  };

  // Calculate total flow
  const totalFlow = links.reduce((sum, link) => sum + link.value, 0);

  // Calculate efficiency (if applicable - compare input vs output)
  const inputNodes = Array.from(new Set(links.map(l => l.source)));
  const outputNodes = Array.from(new Set(links.map(l => l.target)));
  const pureInputNodes = inputNodes.filter(n => !outputNodes.includes(n));
  const pureOutputNodes = outputNodes.filter(n => !inputNodes.includes(n));

  const totalInput = links
    .filter(l => {
      const sourceLabel = typeof l.source === 'string' ? l.source : nodes[l.source].label;
      return pureInputNodes.some(n =>
        (typeof n === 'string' ? n : nodes[n as number].label) === sourceLabel
      );
    })
    .reduce((sum, link) => sum + link.value, 0);

  const totalOutput = links
    .filter(l => {
      const targetLabel = typeof l.target === 'string' ? l.target : nodes[l.target].label;
      return pureOutputNodes.some(n =>
        (typeof n === 'string' ? n : nodes[n as number].label) === targetLabel
      );
    })
    .reduce((sum, link) => sum + link.value, 0);

  const efficiency = totalInput > 0 ? (totalOutput / totalInput) * 100 : 0;

  return (
    <div className="sankey-diagram-container">
      <Plot
        data={[trace]}
        layout={layout}
        config={config}
        style={{ width: width === '100%' ? '100%' : width }}
        useResizeHandler={true}
      />

      {/* Flow summary */}
      <div className="sankey-summary mt-4 grid grid-cols-3 gap-4 text-sm">
        <div className="stat-card bg-blue-50 p-3 rounded">
          <div className="text-gray-600 text-xs">Total Flow</div>
          <div className="text-lg font-semibold text-blue-900">{totalFlow.toFixed(1)}</div>
        </div>

        {totalInput > 0 && (
          <div className="stat-card bg-green-50 p-3 rounded">
            <div className="text-gray-600 text-xs">Input</div>
            <div className="text-lg font-semibold text-green-900">{totalInput.toFixed(1)}</div>
          </div>
        )}

        {totalOutput > 0 && (
          <div className="stat-card bg-purple-50 p-3 rounded">
            <div className="text-gray-600 text-xs">Output</div>
            <div className="text-lg font-semibold text-purple-900">{totalOutput.toFixed(1)}</div>
          </div>
        )}

        {efficiency > 0 && efficiency < 100 && (
          <div className="stat-card bg-amber-50 p-3 rounded">
            <div className="text-gray-600 text-xs">Efficiency</div>
            <div className="text-lg font-semibold text-amber-900">{efficiency.toFixed(1)}%</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SankeyDiagram;
