/**
 * Visualization Showcase Page
 *
 * Interactive showcase of all 12 Plotly visualization components
 * with sample data, code examples, and use cases
 */

import React, { useState } from 'react';
import {
  BarChart3,
  Code,
  Info,
  ExternalLink,
  ChevronRight,
  Grid3x3,
  List,
  Search,
  Filter,
} from 'lucide-react';

// Import all visualization components
import {
  GaugeChart,
  HeatmapChart,
  ScatterPlot,
  MultiAxisChart,
  BarChart,
  PieChart,
  BoxPlot,
  WaterfallChart,
  RadarChart,
  SankeyDiagram,
  TreemapChart,
  GeoMap,
} from '../components/Visualizations';

/**
 * Visualization metadata interface
 */
interface VisualizationDemo {
  id: string;
  name: string;
  description: string;
  category: 'basic' | 'statistical' | 'advanced' | 'geospatial';
  useCases: string[];
  component: React.ReactElement;
  code: string;
}

/**
 * Main Showcase Page Component
 */
export const VisualizationShowcase: React.FC = () => {
  // State
  const [selectedDemo, setSelectedDemo] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showCode, setShowCode] = useState<string | null>(null);

  // Sample data generators
  const generateTimestamps = (hours: number = 24, interval: number = 1) => {
    const now = Date.now();
    const timestamps: string[] = [];
    for (let i = hours; i >= 0; i -= interval) {
      timestamps.push(new Date(now - i * 60 * 60 * 1000).toISOString());
    }
    return timestamps;
  };

  const generateRandomData = (count: number, min: number = 0, max: number = 100) => {
    return Array.from({ length: count }, () => Math.random() * (max - min) + min);
  };

  // Visualization demos
  const demos: VisualizationDemo[] = [
    // 1. GaugeChart
    {
      id: 'gauge',
      name: 'Gauge Chart',
      description: 'Real-time KPI monitoring with threshold indicators',
      category: 'basic',
      useCases: ['Production rates', 'Temperature monitoring', 'Pressure levels', 'OEE display'],
      component: (
        <GaugeChart
          value={75.5}
          min={0}
          max={100}
          unit="%"
          thresholds={[
            { value: 60, color: '#ef4444', label: 'Low' },
            { value: 80, color: '#eab308', label: 'Medium' },
            { value: 100, color: '#22c55e', label: 'High' },
          ]}
          showDelta={true}
          previousValue={72.3}
          title="OEE (Overall Equipment Effectiveness)"
        />
      ),
      code: `<GaugeChart
  value={75.5}
  min={0}
  max={100}
  unit="%"
  thresholds={[
    { value: 60, color: '#ef4444', label: 'Low' },
    { value: 80, color: '#eab308', label: 'Medium' },
    { value: 100, color: '#22c55e', label: 'High' }
  ]}
  showDelta={true}
  previousValue={72.3}
  title="OEE"
/>`,
    },

    // 2. HeatmapChart
    {
      id: 'heatmap',
      name: 'Heatmap Chart',
      description: 'Correlation matrix and pattern analysis',
      category: 'statistical',
      useCases: ['Tag correlations', 'Time-based patterns', 'Equipment comparison', 'Quality analysis'],
      component: (
        <HeatmapChart
          data={[
            [0.95, 0.82, 0.45, 0.23, 0.67],
            [0.82, 1.0, 0.55, 0.34, 0.71],
            [0.45, 0.55, 0.89, 0.67, 0.44],
            [0.23, 0.34, 0.67, 0.92, 0.38],
            [0.67, 0.71, 0.44, 0.38, 0.88],
          ]}
          xLabels={['Temp', 'Pressure', 'Flow', 'Speed', 'Power']}
          yLabels={['Temp', 'Pressure', 'Flow', 'Speed', 'Power']}
          title="Sensor Correlation Matrix"
          colorScale="RdBu"
        />
      ),
      code: `<HeatmapChart
  data={correlationMatrix}
  xLabels={['Temp', 'Pressure', 'Flow', 'Speed', 'Power']}
  yLabels={['Temp', 'Pressure', 'Flow', 'Speed', 'Power']}
  title="Sensor Correlation Matrix"
  colorScale="RdYlGn"
/>`,
    },

    // 3. ScatterPlot
    {
      id: 'scatter',
      name: 'Scatter Plot',
      description: 'Relationship analysis with trendlines',
      category: 'statistical',
      useCases: ['Process optimization', 'Quality vs parameters', 'Efficiency analysis', 'Anomaly detection'],
      component: (
        <ScatterPlot
          data={generateRandomData(50, 50, 100).map((x, i) => ({
            x: x,
            y: generateRandomData(50, 60, 95)[i],
            group: i < 25 ? 'Process A' : 'Process B'
          }))}
          xLabel="Temperature (°C)"
          yLabel="Quality Index"
          title="Temperature vs Quality"
          showTrendline={true}
          colorByGroup={true}
        />
      ),
      code: `<ScatterPlot
  data={[
    { name: 'Process A', x: xData, y: yData, color: '#3b82f6' },
    { name: 'Process B', x: xData2, y: yData2, color: '#ef4444' }
  ]}
  xLabel="Temperature (°C)"
  yLabel="Quality Index"
  title="Temperature vs Quality"
  showTrendline={true}
/>`,
    },

    // 4. MultiAxisChart
    {
      id: 'multiaxis',
      name: 'Multi-Axis Chart',
      description: 'Time series with multiple Y-axes for different units',
      category: 'basic',
      useCases: ['Process trending', 'Multi-variable monitoring', 'Batch analysis', 'Energy consumption'],
      component: (
        <MultiAxisChart
          timestamps={generateTimestamps(24, 2)}
          series={[
            {
              name: 'Temperature',
              data: generateRandomData(13, 60, 85),
              yAxis: 'left',
              unit: '°C',
              color: '#ef4444',
            },
            {
              name: 'Pressure',
              data: generateRandomData(13, 2, 8),
              yAxis: 'right',
              unit: 'bar',
              color: '#3b82f6',
            },
            {
              name: 'Flow Rate',
              data: generateRandomData(13, 100, 200),
              yAxis: 'right',
              unit: 'L/min',
              color: '#22c55e',
              lineStyle: 'dash',
            },
          ]}
          title="Process Parameters - Last 24 Hours"
          height={400}
        />
      ),
      code: `<MultiAxisChart
  timestamps={timestamps}
  series={[
    { name: 'Temperature', data: tempData, yAxis: 'left', unit: '°C' },
    { name: 'Pressure', data: pressData, yAxis: 'right', unit: 'bar' }
  ]}
  title="Process Parameters"
  height={400}
/>`,
    },

    // 5. BarChart
    {
      id: 'bar',
      name: 'Bar Chart',
      description: 'Categorical comparisons and rankings',
      category: 'basic',
      useCases: ['Production by shift', 'Equipment comparison', 'Monthly targets', 'Quality by product'],
      component: (
        <BarChart
          categories={['Shift 1', 'Shift 2', 'Shift 3', 'Shift 4']}
          data={[
            { name: 'Target', values: [1000, 1000, 1000, 1000], color: '#94a3b8' },
            { name: 'Actual', values: [950, 1020, 890, 1050], color: '#3b82f6' },
            { name: 'Good Quality', values: [900, 980, 850, 1000], color: '#22c55e' },
          ]}
          title="Production by Shift"
          stacked={false}
          showValues={true}
          {...({} as any)}
        />
      ),
      code: `<BarChart
  categories={['Shift 1', 'Shift 2', 'Shift 3', 'Shift 4']}
  series={[
    { name: 'Target', data: [1000, 1000, 1000, 1000] },
    { name: 'Actual', data: [950, 1020, 890, 1050] }
  ]}
  title="Production by Shift"
  showValues={true}
/>`,
    },

    // 6. PieChart
    {
      id: 'pie',
      name: 'Pie Chart',
      description: 'Distribution and composition analysis',
      category: 'basic',
      useCases: ['Downtime causes', 'Energy distribution', 'Product mix', 'Quality defects'],
      component: (
        <PieChart
          data={[
            { label: 'Mechanical Failure', value: 35, color: '#ef4444' },
            { label: 'Changeover', value: 25, color: '#f59e0b' },
            { label: 'Material Shortage', value: 20, color: '#eab308' },
            { label: 'Quality Issues', value: 12, color: '#3b82f6' },
            { label: 'Other', value: 8, color: '#94a3b8' },
          ]}
          title="Downtime Root Causes (Last Month)"
          donut={true}
          showPercentages={true}
        />
      ),
      code: `<PieChart
  data={[
    { label: 'Mechanical Failure', value: 35 },
    { label: 'Changeover', value: 25 },
    { label: 'Material Shortage', value: 20 }
  ]}
  title="Downtime Root Causes"
  donut={true}
  showPercentages={true}
/>`,
    },

    // 7. BoxPlot
    {
      id: 'boxplot',
      name: 'Box Plot',
      description: 'Statistical distribution and outlier detection',
      category: 'statistical',
      useCases: ['Process variability', 'Quality control', 'Performance distribution', 'Outlier identification'],
      component: (
        <BoxPlot
          data={[
            { name: 'Line 1', values: generateRandomData(100, 80, 95) },
            { name: 'Line 2', values: generateRandomData(100, 75, 92) },
            { name: 'Line 3', values: generateRandomData(100, 82, 98) },
            { name: 'Line 4', values: generateRandomData(100, 78, 90) },
          ]}
          title="Quality Distribution by Production Line"
          yLabel="Quality Score"
          showOutliers={true}
        />
      ),
      code: `<BoxPlot
  data={[
    { name: 'Line 1', values: line1Data },
    { name: 'Line 2', values: line2Data },
    { name: 'Line 3', values: line3Data }
  ]}
  title="Quality Distribution by Line"
  showOutliers={true}
/>`,
    },

    // 8. WaterfallChart
    {
      id: 'waterfall',
      name: 'Waterfall Chart',
      description: 'Sequential gains and losses analysis',
      category: 'advanced',
      useCases: ['OEE loss analysis', 'Cost breakdown', 'Energy consumption', 'Process efficiency'],
      component: (
        <WaterfallChart
          data={[
            { label: 'Target', value: 1000, type: 'initial' },
            { label: 'Availability Loss', value: -120, type: 'decrease' },
            { label: 'Performance Loss', value: -80, type: 'decrease' },
            { label: 'Quality Loss', value: -50, type: 'decrease' },
            { label: 'Actual Output', value: 750, type: 'total' },
          ]}
          title="OEE Loss Waterfall Analysis"
          showConnectors={true}
          {...({} as any)}
        />
      ),
      code: `<WaterfallChart
  data={[
    { label: 'Target', value: 1000, type: 'initial' },
    { label: 'Availability Loss', value: -120, type: 'decrease' },
    { label: 'Actual Output', value: 750, type: 'total' }
  ]}
  title="OEE Loss Analysis"
  showConnectors={true}
/>`,
    },

    // 9. RadarChart
    {
      id: 'radar',
      name: 'Radar Chart',
      description: 'Multi-dimensional performance comparison',
      category: 'advanced',
      useCases: ['Equipment comparison', 'Shift performance', 'KPI dashboard', 'Benchmark analysis'],
      component: (
        <RadarChart
          categories={['Quality', 'Availability', 'Performance', 'Safety', 'Efficiency', 'Compliance']}
          data={[
            { name: 'Current Period', values: [85, 92, 78, 95, 88, 90], color: '#3b82f6' },
            { name: 'Previous Period', values: [80, 88, 82, 90, 85, 87], color: '#94a3b8' },
            { name: 'Target', values: [90, 95, 90, 100, 92, 95], color: '#22c55e' },
          ]}
          title="Performance Scorecard Comparison"
          fill={true}
          {...({} as any)}
        />
      ),
      code: `<RadarChart
  categories={['Quality', 'Availability', 'Performance', 'Safety']}
  series={[
    { name: 'Current', values: [85, 92, 78, 95] },
    { name: 'Target', values: [90, 95, 90, 100] }
  ]}
  title="Performance Scorecard"
  fill={true}
/>`,
    },

    // 10. SankeyDiagram
    {
      id: 'sankey',
      name: 'Sankey Diagram',
      description: 'Flow and energy transfer visualization',
      category: 'advanced',
      useCases: ['Energy flow', 'Material flow', 'Process flow', 'Cost allocation'],
      component: (
        <SankeyDiagram
          nodes={[
            { id: 'input', label: 'Raw Material' },
            { id: 'process1', label: 'Process A' },
            { id: 'process2', label: 'Process B' },
            { id: 'output1', label: 'Product 1' },
            { id: 'output2', label: 'Product 2' },
            { id: 'waste', label: 'Waste' },
          ] as any}
          flows={[
            { source: 'input', target: 'process1', value: 1000 },
            { source: 'process1', target: 'process2', value: 850 },
            { source: 'process1', target: 'waste', value: 150 },
            { source: 'process2', target: 'output1', value: 600 },
            { source: 'process2', target: 'output2', value: 200 },
            { source: 'process2', target: 'waste', value: 50 },
          ]}
          title="Production Flow Analysis"
          {...({} as any)}
        />
      ),
      code: `<SankeyDiagram
  nodes={[
    { id: 'input', label: 'Raw Material' },
    { id: 'process', label: 'Process' },
    { id: 'output', label: 'Product' }
  ]}
  flows={[
    { source: 'input', target: 'process', value: 1000 },
    { source: 'process', target: 'output', value: 850 }
  ]}
  title="Production Flow"
/>`,
    },

    // 11. TreemapChart
    {
      id: 'treemap',
      name: 'Treemap Chart',
      description: 'Hierarchical data visualization with proportional sizing',
      category: 'advanced',
      useCases: ['Cost breakdown', 'Production by category', 'Inventory distribution', 'Resource allocation'],
      component: (
        <TreemapChart
          data={[
            {
              category: 'Manufacturing',
              subcategories: [
                { name: 'Labor', value: 450000, color: '#3b82f6' },
                { name: 'Materials', value: 680000, color: '#2563eb' },
                { name: 'Overhead', value: 320000, color: '#1d4ed8' },
              ],
            },
            {
              category: 'Operations',
              subcategories: [
                { name: 'Maintenance', value: 280000, color: '#22c55e' },
                { name: 'Utilities', value: 190000, color: '#16a34a' },
                { name: 'Logistics', value: 240000, color: '#15803d' },
              ],
            },
            {
              category: 'Overhead',
              subcategories: [
                { name: 'Administration', value: 180000, color: '#f59e0b' },
                { name: 'IT', value: 120000, color: '#d97706' },
                { name: 'Facilities', value: 95000, color: '#b45309' },
              ],
            },
          ] as any}
          title="Annual Cost Breakdown"
          showValues={true}
          {...({} as any)}
        />
      ),
      code: `<TreemapChart
  data={[
    {
      category: 'Manufacturing',
      subcategories: [
        { name: 'Labor', value: 450000 },
        { name: 'Materials', value: 680000 }
      ]
    }
  ]}
  title="Cost Breakdown"
  showValues={true}
/>`,
    },

    // 12. GeoMap
    {
      id: 'geomap',
      name: 'Geographic Map',
      description: 'Site locations and status on interactive map',
      category: 'geospatial',
      useCases: ['Plant locations', 'Asset tracking', 'Regional performance', 'Supply chain'],
      component: (
        <GeoMap
          markers={[
            {
              lat: 40.7128,
              lon: -74.006,
              name: 'New York Plant',
              status: 'online',
              value: 95.2,
            },
            {
              lat: 34.0522,
              lon: -118.2437,
              name: 'Los Angeles Plant',
              status: 'warning',
              value: 78.5,
            },
            {
              lat: 41.8781,
              lon: -87.6298,
              name: 'Chicago Plant',
              status: 'online',
              value: 92.1,
            },
            {
              lat: 29.7604,
              lon: -95.3698,
              name: 'Houston Plant',
              status: 'offline',
              value: 0,
            },
            {
              lat: 33.749,
              lon: -84.388,
              name: 'Atlanta Plant',
              status: 'online',
              value: 88.7,
            },
          ]}
          title="Plant Network Status"
          center={{ lat: 39.8283, lon: -98.5795 }}
          zoom={4}
          unit="%"
          metric="Availability"
        />
      ),
      code: `<GeoMap
  markers={[
    { lat: 40.7128, lon: -74.006, name: 'NY Plant', status: 'online' },
    { lat: 34.0522, lon: -118.2437, name: 'LA Plant', status: 'warning' }
  ]}
  title="Plant Network Status"
  center={{ lat: 39.8, lon: -98.5 }}
  zoom={4}
/>`,
    },
  ];

  // Filter demos
  const filteredDemos = demos.filter((demo) => {
    const matchesSearch =
      demo.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      demo.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || demo.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // Categories for filter
  const categories = [
    { value: 'all', label: 'All Categories', count: demos.length },
    { value: 'basic', label: 'Basic', count: demos.filter((d) => d.category === 'basic').length },
    {
      value: 'statistical',
      label: 'Statistical',
      count: demos.filter((d) => d.category === 'statistical').length,
    },
    {
      value: 'advanced',
      label: 'Advanced',
      count: demos.filter((d) => d.category === 'advanced').length,
    },
    {
      value: 'geospatial',
      label: 'Geospatial',
      count: demos.filter((d) => d.category === 'geospatial').length,
    },
  ];

  return (
    <div className="visualization-showcase min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <BarChart3 size={36} className="text-blue-600" />
                Visualization Showcase
              </h1>
              <p className="text-gray-600 mt-2">
                Interactive gallery of all 12 Plotly visualization components with sample data and
                code examples
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-lg transition-colors ${
                  viewMode === 'grid'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Grid3x3 size={20} />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-lg transition-colors ${
                  viewMode === 'list'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                <List size={20} />
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
              <div className="text-sm text-gray-600">Total Components</div>
              <div className="text-2xl font-bold text-blue-600">12</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
              <div className="text-sm text-gray-600">Categories</div>
              <div className="text-2xl font-bold text-green-600">4</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
              <div className="text-sm text-gray-600">Use Cases</div>
              <div className="text-2xl font-bold text-purple-600">40+</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
              <div className="text-sm text-gray-600">Code Examples</div>
              <div className="text-2xl font-bold text-orange-600">12</div>
            </div>
          </div>
        </div>

        {/* Search and Filter */}
        <div className="mb-6 flex gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search size={20} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search visualizations..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Category Filter */}
          <div className="flex gap-2">
            {categories.map((cat) => (
              <button
                key={cat.value}
                onClick={() => setSelectedCategory(cat.value)}
                className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  selectedCategory === cat.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                {cat.label} ({cat.count})
              </button>
            ))}
          </div>
        </div>

        {/* Results count */}
        <div className="mb-4 text-sm text-gray-600">
          Showing {filteredDemos.length} of {demos.length} visualizations
        </div>

        {/* Visualization Grid/List */}
        <div
          className={
            viewMode === 'grid'
              ? 'grid grid-cols-1 md:grid-cols-2 gap-6'
              : 'flex flex-col gap-4'
          }
        >
          {filteredDemos.map((demo) => (
            <div
              key={demo.id}
              className="bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-shadow"
            >
              {/* Card Header */}
              <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{demo.name}</h3>
                    <p className="text-sm text-gray-600 mt-1">{demo.description}</p>
                  </div>
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      demo.category === 'basic'
                        ? 'bg-blue-100 text-blue-800'
                        : demo.category === 'statistical'
                        ? 'bg-green-100 text-green-800'
                        : demo.category === 'advanced'
                        ? 'bg-purple-100 text-purple-800'
                        : 'bg-orange-100 text-orange-800'
                    }`}
                  >
                    {demo.category}
                  </span>
                </div>
              </div>

              {/* Visualization */}
              <div className="p-4 bg-gray-50">{demo.component}</div>

              {/* Use Cases */}
              <div className="p-4 border-t border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  <Info size={16} className="text-gray-600" />
                  <span className="text-sm font-medium text-gray-900">Use Cases:</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {demo.useCases.map((useCase, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                    >
                      {useCase}
                    </span>
                  ))}
                </div>
              </div>

              {/* Code Example */}
              <div className="p-4 border-t border-gray-200">
                <button
                  onClick={() => setShowCode(showCode === demo.id ? null : demo.id)}
                  className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  <Code size={16} />
                  {showCode === demo.id ? 'Hide' : 'Show'} Code Example
                </button>

                {showCode === demo.id && (
                  <div className="mt-3 bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
                    <pre className="text-xs font-mono">{demo.code}</pre>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {filteredDemos.length === 0 && (
          <div className="text-center py-12">
            <Filter size={48} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No visualizations found</h3>
            <p className="text-gray-600">
              Try adjusting your search or filter criteria
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default VisualizationShowcase;
