/**
 * Visualizations Component Library
 *
 * Advanced visualization components using Plotly.js
 * for industrial analytics and monitoring
 */

// Chart Components
export { GaugeChart, type GaugeChartProps, type GaugeThreshold } from './GaugeChart';
export { HeatmapChart, type HeatmapChartProps } from './HeatmapChart';
export { ScatterPlot, type ScatterPlotProps, type ScatterDataPoint } from './ScatterPlot';
export { MultiAxisChart, type MultiAxisChartProps, type SeriesConfig } from './MultiAxisChart';
export { BarChart, type BarChartProps, type BarDataSeries } from './BarChart';
export { PieChart, type PieChartProps, type PieDataSlice } from './PieChart';
export { BoxPlot, type BoxPlotProps, type BoxPlotDataset } from './BoxPlot';
export { WaterfallChart, type WaterfallChartProps, type WaterfallItem } from './WaterfallChart';
export { RadarChart, type RadarChartProps, type RadarDataSeries } from './RadarChart';
export { SankeyDiagram, type SankeyDiagramProps, type SankeyLink, type SankeyNode } from './SankeyDiagram';
export { TreemapChart, type TreemapChartProps, type TreemapItem } from './TreemapChart';
export { GeoMap, type GeoMapProps, type MapMarker } from './GeoMap';

// Re-export all for convenience
export * from './GaugeChart';
export * from './HeatmapChart';
export * from './ScatterPlot';
export * from './MultiAxisChart';
export * from './BarChart';
export * from './PieChart';
export * from './BoxPlot';
export * from './WaterfallChart';
export * from './RadarChart';
export * from './SankeyDiagram';
export * from './TreemapChart';
export * from './GeoMap';
