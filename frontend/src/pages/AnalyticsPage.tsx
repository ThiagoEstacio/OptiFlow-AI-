/**
 * Analytics Page
 *
 * Main page for advanced analytics with visual query builder
 * and interactive data visualization
 */

import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Download,
  RefreshCw,
  Lightbulb,
} from 'lucide-react';
import { QueryBuilder, AnalyticsQuery } from '../components/QueryBuilder';
import {
  MultiAxisChart,
  BarChart,
  HeatmapChart,
  ScatterPlot,
  GaugeChart,
  BoxPlot,
  WaterfallChart,
  RadarChart,
  SankeyDiagram,
  TreemapChart,
  GeoMap,
} from '../components/Visualizations';
import analyticsApi, {
  QueryResult,
  QueryExample,
  AggregationFunction,
} from '../services/analyticsApi';

/**
 * Main Analytics Page Component
 */
export const AnalyticsPage: React.FC = () => {
  // Query state
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Examples and functions
  const [examples, setExamples] = useState<QueryExample[]>([]);
  const [functions, setFunctions] = useState<AggregationFunction[]>([]);
  const [showExamples, setShowExamples] = useState(false);

  // Visualization selection
  const [selectedVisualization, setSelectedVisualization] = useState<string>('auto');

  // Load examples and functions on mount
  useEffect(() => {
    const loadMetadata = async () => {
      try {
        const [examplesData, functionsData] = await Promise.all([
          analyticsApi.getQueryExamples(),
          analyticsApi.getAvailableFunctions(),
        ]);
        setExamples(examplesData);
        setFunctions(functionsData);
      } catch (err) {
        console.error('Failed to load metadata:', err);
      }
    };

    loadMetadata();
  }, []);

  /**
   * Execute analytics query
   */
  const handleExecuteQuery = async (query: AnalyticsQuery) => {
    setLoading(true);
    setError(null);

    try {
      const result = await analyticsApi.executeQuery(query);
      setQueryResult(result);
    } catch (err: any) {
      setError(err.message || 'Failed to execute query');
      setQueryResult(null);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Load example query
   */
  const handleLoadExample = (example: QueryExample) => {
    // This would need to be implemented by passing the query back to QueryBuilder
    // For now, we'll just execute it directly
    handleExecuteQuery(example.query);
    setShowExamples(false);
  };

  /**
   * Export results to CSV
   */
  const handleExportResults = () => {
    if (!queryResult) return;

    // Convert results to CSV
    let csvContent = 'timestamp,tag_id,value\n';

    if (queryResult.raw_data) {
      queryResult.raw_data.forEach((row) => {
        csvContent += `${row.timestamp},${row.tag_id},${row.value}\n`;
      });
    } else {
      // Export aggregation results
      queryResult.aggregations.forEach((agg) => {
        agg.values.forEach((val) => {
          csvContent += `${val.timestamp},${val.tag_id || 'aggregated'},${val.value}\n`;
        });
      });
    }

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics-results-${Date.now()}.csv`;
    a.click();
  };

  /**
   * Render visualization based on query result
   */
  const renderVisualization = () => {
    if (!queryResult) return null;

    const { aggregations } = queryResult;
    if (aggregations.length === 0) return null;

    // Auto-select visualization based on aggregation type
    if (selectedVisualization === 'auto') {
      const firstAgg = aggregations[0];

      // Time series data -> Multi-axis chart
      if (
        firstAgg.values.length > 10 &&
        firstAgg.values.every((v) => v.timestamp)
      ) {
        const timestamps = firstAgg.values.map((v) => v.timestamp);
        const series = aggregations.map((agg) => ({
          name: `${agg.function}(${agg.field})`,
          data: agg.values.map((v) => v.value),
          yAxis: 'left' as const,
          unit: agg.field === 'value' ? 'units' : agg.field,
        }));

        return (
          <MultiAxisChart
            timestamps={timestamps}
            series={series}
            title="Query Results - Time Series"
            height={500}
          />
        );
      }

      // Few data points -> Bar chart
      if (firstAgg.values.length <= 10) {
        return (
          <BarChart
            categories={firstAgg.values.map(
              (v) => v.tag_id || v.timestamp.split('T')[0]
            )}
            series={aggregations.map((agg) => ({
              name: `${agg.function}(${agg.field})`,
              data: agg.values.map((v) => v.value),
            }))}
            title="Query Results - Comparison"
            height={500}
          />
        );
      }
    }

    // Manual visualization selection
    // ... (implement other visualization types)

    return null;
  };

  return (
    <div className="analytics-page min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <BarChart3 size={36} className="text-blue-600" />
                Advanced Analytics
              </h1>
              <p className="text-gray-600 mt-2">
                Build complex queries and visualize your industrial data with Power
                BI-style analytics
              </p>
            </div>

            <button
              onClick={() => setShowExamples(!showExamples)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Lightbulb size={18} />
              {showExamples ? 'Hide' : 'Show'} Examples
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mt-6">
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
              <div className="text-sm text-gray-600">Available Functions</div>
              <div className="text-2xl font-bold text-blue-600">
                {functions.length}
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
              <div className="text-sm text-gray-600">Example Queries</div>
              <div className="text-2xl font-bold text-green-600">
                {examples.length}
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
              <div className="text-sm text-gray-600">Query Status</div>
              <div className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                {loading ? (
                  <>
                    <RefreshCw size={20} className="animate-spin text-blue-600" />
                    <span className="text-base">Running...</span>
                  </>
                ) : queryResult ? (
                  <>
                    <CheckCircle size={20} className="text-green-600" />
                    <span className="text-base">Complete</span>
                  </>
                ) : (
                  <span className="text-base text-gray-400">Ready</span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Examples Panel */}
        {showExamples && examples.length > 0 && (
          <div className="mb-8 bg-white rounded-lg shadow-lg p-6 border border-purple-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Lightbulb size={20} className="text-purple-600" />
              Example Queries
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {examples.map((example, index) => (
                <div
                  key={index}
                  className="border border-gray-200 rounded-lg p-4 hover:border-purple-400 hover:shadow-md transition-all cursor-pointer"
                  onClick={() => handleLoadExample(example)}
                >
                  <div className="font-semibold text-gray-900 mb-1">
                    {example.name}
                  </div>
                  <div className="text-sm text-gray-600 mb-2">
                    {example.description}
                  </div>
                  <div className="text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded inline-block">
                    {example.use_case}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Query Builder */}
        <div className="mb-8">
          <QueryBuilder
            onExecute={handleExecuteQuery}
            onStreamData={(data) => setQueryResult(data)}
            loading={loading}
            enableStreaming={true}
          />
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-8 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-red-900">Query Error</div>
              <div className="text-sm text-red-700 mt-1">{error}</div>
            </div>
          </div>
        )}

        {/* Results Section */}
        {queryResult && (
          <div className="space-y-6">
            {/* Results Header */}
            <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <TrendingUp size={20} className="text-green-600" />
                    Query Results
                  </h3>
                  <div className="text-sm text-gray-600 mt-1">
                    Executed in {queryResult.execution_time_ms.toFixed(2)}ms •{' '}
                    {queryResult.metadata.total_records.toLocaleString()} records
                  </div>
                </div>

                <button
                  onClick={handleExportResults}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  <Download size={16} />
                  Export CSV
                </button>
              </div>

              {/* Aggregation Summary */}
              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
                {queryResult.aggregations.slice(0, 3).map((agg, index) => (
                  <div
                    key={index}
                    className="bg-gray-50 p-3 rounded border border-gray-200"
                  >
                    <div className="text-xs text-gray-600 uppercase">
                      {agg.function}({agg.field})
                    </div>
                    <div className="text-lg font-semibold text-gray-900 mt-1">
                      {agg.summary?.mean?.toFixed(2) || agg.values[0]?.value.toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {agg.values.length} data points
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Visualization */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  Visualization
                </h3>

                <select
                  value={selectedVisualization}
                  onChange={(e) => setSelectedVisualization(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="auto">Auto-Select</option>
                  <option value="timeseries">Time Series</option>
                  <option value="bar">Bar Chart</option>
                  <option value="scatter">Scatter Plot</option>
                  <option value="heatmap">Heatmap</option>
                  <option value="box">Box Plot</option>
                </select>
              </div>

              {renderVisualization()}
            </div>

            {/* Raw Data Table (if included) */}
            {queryResult.raw_data && queryResult.raw_data.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Raw Data (first 100 rows)
                </h3>

                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Timestamp
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Tag ID
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Value
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Quality
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {queryResult.raw_data.slice(0, 100).map((row, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm text-gray-900 font-mono">
                            {new Date(row.timestamp).toLocaleString()}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900 font-mono">
                            {row.tag_id}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900">
                            {row.value.toFixed(4)}
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <span
                              className={`px-2 py-1 rounded text-xs ${
                                row.quality === 'good'
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-yellow-100 text-yellow-800'
                              }`}
                            >
                              {row.quality}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!queryResult && !loading && !error && (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <BarChart3 size={64} className="text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Ready to Analyze
            </h3>
            <p className="text-gray-600 max-w-md mx-auto">
              Use the query builder above to create your first analytics query. Select
              tags, choose time range, add filters, and configure aggregations to get
              started.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalyticsPage;
